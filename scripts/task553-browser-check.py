#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 553 browser-check: блок «Повторные инструктажи и
# периодическая проверка знаний» карточки работника (страница
# «Работники» раздела «Табель учёта рабочего времени») —
# отображение ПРИМЕЧАНИЯ записи (поле «комментарий» листа
# «Инструктажи», столбец H). Заявка:
#   «В разделе "Табель учёта рабочего времени / Работники" в блоке
#    инструктажей и проверки знаний, сделай отображения примечания
#    в инструктажах и проверках данных».
# Сценарий (май 2026; работники 017/023; записи инструктажей
# с примечаниями/без/пробельные):
#  A) карточка 017: строка инструктажа «тема · дата · «примечание»»
#     — примечание в конце строки, курсив .ws-tr-note, 13px в карте;
#  B) пустое и пробельное примечание — строка без «ёлочек»;
#  C) запись «вне списка» — примечание как в обычных строках;
#  D) карточка 023 — своё примечание (проверка знаний);
#  E) светлая тема — тот же вид;
#  F) 0 JS-ошибок; скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8996
Y, M = 2026, 5
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task553')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:240] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'дневной',
   'смена': None, 'шаблон_ротации': None, 'старт_цикла': None,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': '2026-05-01',
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

# Записи «Инструктажей» 2026 года (формат 'done' сервера):
#  101/103 — с примечанием; 102 — пустое; 104 — пробельное;
#  105 — архив 2025 (попадает только в instrAll);
#  201 — запись работника 023 с примечанием
def T(tid, tab, tip, tema, d, comment, done, late):
    return {'id': tid, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d, 'дата_окончания': d,
            'длительность_дней': 1, 'комментарий': comment,
            'дата_проведения': d, 'выполнение': done, 'просрочен': late}

TRAININGS = [
  T(101, '017', 'инструктаж',
    'Повторный инструктаж по рабочим инструкциям ОТ',
    '2026-03-15', 'протокол № 12, ведёт Иванов А.А.', 1, 0),
  T(102, '017', 'проверка_знаний',
    'Периодическая проверка знаний на допуск к самостоятельной работе',
    '2026-05-20', '', 0, 1),
  T(103, '017', 'инструктаж',
    'Внеплановый инструктаж после аварии на ХВО-2',
    '2026-09-02', 'по предписанию № 4-ОТ', 0, 1),
  T(104, '017', 'инструктаж',
    'Повторный инструктаж по инструкции № 9-ОГЭ',
    '2026-10-10', '   ', 0, 1),
  T(201, '023', 'проверка_знаний',
    'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В',
    '2026-02-10', 'комиссия в Ростехнадзоре, ticket РТН-8', 1, 0),
]
INSTR_ALL = TRAININGS + [
  T(105, '017', 'инструктаж',
    'Повторный инструктаж по рабочим инструкциям ОТ',
    '2025-09-15', 'архив: протокол № 9 за 2025', 1, 0),
]
ENTRIES = []


def E(day, tab, status, source):
    return {'дата': '2026-05-%02d' % day, 'таб_номер': tab,
            'статус': status, 'переработка': 0, 'праздник': 0,
            'источник': source, 'дата_обновления':
            '2026-11-01T08:00:00.000Z', 'замещает': None,
            'инструкция': None, 'комментарий': '', 'часы': None,
            'время_начала': None, 'время_окончания': None}


ENTRIES.append(E(12, '023', 'Д', 'авто'))
ENTRIES.append(E(13, '023', 'Н', 'авто'))
VACATIONS = []
PPE = []


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS,
                'instrList': [], 'instrAll': INSTR_ALL,
                'eventsAll': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': PPE}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Снимок блока инструктажей КАРТОЧКИ активной вкладки «Работники»:
# заголовок окна + строки записей (текст + примечания + стили)
INSTR_CARD = """(() => {
    const cards = Array.from(document.querySelectorAll('.ws-wcard'));
    const card = cards.find(c => {
        const h = c.querySelector('.ws-whead-t');
        return h && /Повторные инструктажи/.test(h.textContent || '');
    });
    if (!card) return null;
    const head = (card.querySelector('.ws-whead-t') || {})
        .textContent.trim();
    const rows = Array.from(
        card.querySelectorAll('.ws-popup-row.ws-popup-event')).map(r => {
        const note = r.querySelector('.ws-tr-note');
        const st = note ? getComputedStyle(note) : null;
        return { text: r.textContent.replace(/\\s+/g, ' ').trim(),
                 note: note ? note.textContent.trim() : null,
                 italic: st ? st.fontStyle : null,
                 size: st ? st.fontSize : null };
    });
    return { head: head, rows: rows,
             notes: card.querySelectorAll('.ws-tr-note').length };})()"""


def instr_card(page):
    return page.evaluate(INSTR_CARD)


def run_flow(page, tab_no):
    page.evaluate("WorkSchedule.selectWorkersTab('%s')" % tab_no)
    page.wait_for_timeout(700)
    return instr_card(page)


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        # isolateLocalStorage (kip8test) — ключи с префиксом
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t553');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            action = ''
            if 'action=' in request.url:
                action = unquote(request.url.split('action=')[1].split('&')[0])
            body = {}
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except Exception:
                    body = {}
            return route.fulfill(status=200,
                content_type='application/json; charset=utf-8',
                body=json.dumps(mock_response(action, body), ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(1500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        page.select_option('#wsMonthSel', str(M))
        page.select_option('#wsYearSel', str(Y))
        page.wait_for_timeout(2000)

        # страница «Работники» — карточки (Task 417: попап удалён,
        # карточки — ЕДИНСТВЕННОЕ подробное вью работника)
        print('== A: карточка 017 — примечания строк инструктажей ==')
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(900)
        card = run_flow(page, '017')
        check('A: окно блока инструктажей отрисовано',
              card and 'Повторные инструктажи' in (card or {}).get('head', ''),
              (card or {}).get('head'))
        check('A: заголовок с годом шахматки (2026)',
              '2026' in (card or {}).get('head', ''), card and card['head'])

        rows = {r['text'][:34]: r for r in (card or {}).get('rows', [])}
        all_rows = (card or {}).get('rows', [])

        r101 = next((r for r in all_rows if 'рабочим инструкциям' in r['text']), None)
        check('A: строка инструктажа 15.03 с примечанием после даты',
              r101 and '15.03.2026' in r101['text'] and
              ' · «протокол № 12, ведёт Иванов А.А.»' in r101['text'] and
              r101['text'].index('15.03.2026') <
              r101['text'].index('протокол № 12'),
              r101 and r101['text'])
        check('A: примечание — элемент .ws-tr-note',
              r101 and r101['note'] == '«протокол № 12, ведёт Иванов А.А.»',
              r101 and r101['note'])
        check('A: примечание — курсив',
              r101 and r101['italic'] == 'italic', r101 and r101['italic'])
        check('A: размер в карте — 13px (мета-строка СИЗ, Task 444)',
              r101 and r101['size'] == '13px', r101 and r101['size'])

        r102 = next((r for r in all_rows
                     if 'к самостоятельной работе' in r['text']), None)
        check('B: пустое примечание — строка без «ёлочек»',
              r102 and '«' not in r102['text'], r102 and r102['text'])
        r104 = next((r for r in all_rows if '9-ОГЭ' in r['text']), None)
        check('B: пробельное примечание — тоже без «ёлочек»',
              r104 and '«' not in r104['text'], r104 and r104['text'])

        r103 = next((r for r in all_rows if 'Внеплановый' in r['text']), None)
        check('C: запись «вне списка» — примечание после даты',
              r103 and '02.09.2026' in r103['text'] and
              ' · «по предписанию № 4-ОТ»' in r103['text'],
              r103 and r103['text'])

        check('A: в карточке 017 РОВНО два примечания (101 + 103)',
              (card or {}).get('notes') == 2, card and card['notes'])
        shot(page, '01-workers-017-instr-note-dark.png')

        print('== D: карточка 023 — примечание проверки знаний ==')
        card23 = run_flow(page, '023')
        rows23 = (card23 or {}).get('rows', [])
        r201 = next((r for r in rows23 if 'электроустановках до 1000' in r['text']), None)
        check('D: примечание ПЗ 023 — после даты',
              r201 and '10.02.2026' in r201['text'] and
              ' · «комиссия в Ростехнадзоре, ticket РТН-8»' in r201['text'],
              r201 and r201['text'])
        check('D: в карточке 023 — одно примечание',
              (card23 or {}).get('notes') == 1, card23 and card23['notes'])
        shot(page, '02-workers-023-note-dark.png')

        print('== E: светлая тема — тот же вид ==')
        page.evaluate(
            "localStorage.setItem('kip8test:app-theme','light');" +
            "document.documentElement.setAttribute('data-theme','light')")
        page.wait_for_timeout(600)
        cardL = run_flow(page, '017')
        rowsL = (cardL or {}).get('rows', [])
        r101L = next((r for r in rowsL if 'рабочим инструкциям' in r['text']), None)
        check('E: светлая тема — примечание на месте',
              r101L and ' · «протокол № 12, ведёт Иванов А.А.»' in r101L['text'] and
              r101L['italic'] == 'italic',
              r101L and r101L['text'])
        shot(page, '03-workers-017-instr-note-light.png')

        print('== F: санитар ==')
        check('F: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()
        server.shutdown()

    print('\nИТОГО: %d/%d (pass/total), FAIL=%d' %
          (PASS, PASS + FAIL, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
