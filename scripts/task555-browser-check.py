#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 555 browser-check: КРАТКОЕ НАИМЕНОВАНИЕ пункта
# «Список_И_и_ПЗ» в начале каждой строки записи блока «Повторные
# инструктажи и периодическая проверка знаний» КАРТОЧКИ работника
# (страница «Работники»). Заявка:
#   «в блоке со списком инструктажей и проверок знаний в карточках
#    работников, в начале каждого списка отображалось его краткое
#    наименование, указанное в таблице Список_И_и_ПЗ из файла
#    табель_КИП_ИОС. В начале краткое наименование более выраженным
#    шрифтом (инструктажи - синим цветом, проверки знаний - красным,
#    как цвет у их мини значков), а затем остальной текст более
#    мелким шрифтом. И шрифт не должен тускнеть при отметке
#    выполнения, а оставаться таким же нормально читаемым».
# Сценарий (май 2026; работник 017; записи 2026; Список_И_и_ПЗ — 4
# пункта: ОТ-РИ (сокр.), 9-ОГЭ (сокр.), ПЗ-1000В (сокр.), ПЗ-ПБ
# (ПУСТАЯ ячейка E)):
#  A) строка 101 (инструктаж ОТ-РИ): span.ws-tr-short В НАЧАЛЕ
#     .ws-popup-name, «ОТ-РИ», ЖИРНЫЙ 700, 14px, СИНИЙ
#     rgb(100,181,246) (тёмная тема); остальной текст .ws-tr-rest —
#     13px: полная тема · дата · «примечание» (Task 553/554 живы);
#  B) строка 102 (ПЗ): краткое «ПЗ-1000В» КРАСНЫМ rgb(239,83,80)
#     (.ws-tr-short-pz);
#  C) строка 103 (9-ОГЭ, ВЫПОЛНЕНА): текст НЕ тускнеет —
#     .ws-popup-name opacity 1, краткое — прежний синий, галочка
#     зелёная (ws-done-on);
#  D) строки 104 (пункт с ПУСТЫМ сокращением) и 105 («вне списка»)
#     — БЕЗ префикса, полная тема как прежде;
#  E) отметка галочкой 101 — текст не тускнеет (opacity 1, цвет
#     прежний), строка с полным текстом;
#  F) светлая тема — синий rgb(21,101,192), красный rgb(198,40,40),
#     остальной текст 13px;
#  G) санитар: 0 JS-ошибок; скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
Y, M = 2026, 5
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task555')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# Насыщенные оттенки цветов мини-значков (Task 555)
BLUE_DARK, BLUE_LIGHT = 'rgb(100, 181, 246)', 'rgb(21, 101, 192)'
RED_DARK, RED_LIGHT = 'rgb(239, 83, 80)', 'rgb(198, 40, 40)'


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
  {'code': 'И', 'name': 'Инструктаж (повторный)', 'color': '#B3E5FC'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'дневной',
   'смена': None, 'шаблон_ротации': None, 'старт_цикла': None,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

NOTE_101 = 'протокол № 12, ведёт Иванов А.А.'

# Таблица Список_И_и_ПЗ (формат listTrainings): столбец E
# «сокращение» — краткие названия пунктов (Task 416); у «ПЗ-ПБ»
# ячейка ПУСТАЯ (проверка деградации — строка без префикса)
INSTR_LIST = [
  {'название': 'Повторный инструктаж по рабочим инструкциям',
   'вид': 'инструктаж', 'периодичность': 6, 'основание': 'ПОТ',
   'сокращение': 'ОТ-РИ', 'в составе': ''},
  {'название': 'Повторный инструктаж по инструкции № 9-ОГЭ',
   'вид': 'инструктаж', 'периодичность': 3, 'основание': 'ЭБ',
   'сокращение': '9-ОГЭ',
   'в составе': 'Повторный инструктаж по рабочим инструкциям'},
  {'название': 'Периодическая проверка знаний в электроустановках до 1000 В',
   'вид': 'проверка_знаний', 'периодичность': 12, 'основание': 'ПТЭЭП',
   'сокращение': 'ПЗ-1000В', 'в составе': ''},
  {'название': 'Проверка знаний по промышленной безопасности',
   'вид': 'проверка_знаний', 'периодичность': 12, 'основание': 'РТН',
   'сокращение': '', 'в составе': ''},
]


# Записи «Инструктажей» 2026 года (формат 'done' сервера):
#  101 — инструктаж ОТ-РИ с примечанием, выполнение = 0 (отмечается);
#  102 — ПЗ-1000В без примечания, просрочена;
#  103 — 9-ОГЭ УЖЕ ВЫПОЛНЕНА (проверка «не тускнеет»);
#  104 — ПЗ пункта с ПУСТЫМ сокращением (строка без префикса);
#  105 — тема «вне списка» (нет пункта шаблона)
def T(tid, tab, tip, tema, d, comment, done, late):
    return {'id': tid, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d, 'дата_окончания': d,
            'длительность_дней': 1, 'комментарий': comment,
            'дата_проведения': d, 'выполнение': done, 'просрочен': late}


TRAININGS = [
  T(101, '017', 'инструктаж',
    'Повторный инструктаж по рабочим инструкциям',
    '2026-03-15', NOTE_101, 0, 0),
  T(102, '017', 'проверка_знаний',
    'Периодическая проверка знаний в электроустановках до 1000 В',
    '2026-05-20', '', 0, 1),
  T(103, '017', 'инструктаж',
    'Повторный инструктаж по инструкции № 9-ОГЭ',
    '2026-02-10', '', 1, 0),
  T(104, '017', 'проверка_знаний',
    'Проверка знаний по промышленной безопасности',
    '2026-04-05', 'по графику РТН', 0, 0),
  T(105, '017', 'инструктаж',
    'Аварийный внеплановый инструктаж',
    '2026-09-02', 'по предписанию № 4-ОТ', 0, 0),
]
INSTR_ALL = list(TRAININGS)
ENTRIES = []


def E(day, tab, status, source):
    return {'дата': '2026-05-%02d' % day, 'таб_номер': tab,
            'статус': status, 'переработка': 0, 'праздник': 0,
            'источник': source, 'дата_обновления':
            '2026-11-01T08:00:00.000Z', 'замещает': None,
            'инструкция': None, 'комментарий': '', 'часы': None,
            'время_начала': None, 'время_окончания': None}


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
                'instrList': INSTR_LIST, 'instrAll': INSTR_ALL,
                'eventsAll': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': PPE}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.setTrainingDone':
        rid = int(body.get('id', 0) or 0)
        val = int(body.get('выполнение', 0) or 0)
        # сервер Task 554 (srvVer 554): перенос примечаний жив;
        # для 555 достаточно отметить выполнение (без created)
        return {'ok': True, 'data': {'id': rid,
                'выполнение': val, 'просрочен': 0, 'srvVer': '554',
                'autoNote': '', 'created': [], 'updated': [],
                'skipped': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Снимок блока инструктажей КАРТОЧКИ «Работники»: строки записей с
# computed-стилями краткого наименования и остального текста
INSTR_CARD = """(() => {
    const cards = Array.from(document.querySelectorAll('.ws-wcard'));
    const card = cards.find(c => {
        const h = c.querySelector('.ws-whead-t');
        return h && /Повторные инструктажи/.test(h.textContent || '');
    });
    if (!card) return null;
    const rows = Array.from(
        card.querySelectorAll('.ws-popup-row.ws-popup-event')).map(r => {
        const name = r.querySelector('.ws-popup-name');
        const sh = r.querySelector('.ws-tr-short');
        const rest = r.querySelector('.ws-tr-rest');
        const chk = r.querySelector('.ws-done-chk');
        const nt = r.querySelector('.ws-tr-note');
        const shS = sh ? getComputedStyle(sh) : null;
        return { text: r.textContent.replace(/\\s+/g, ' ').trim(),
                 done: r.classList.contains('ws-row-done'),
                 nameOpacity: name ? getComputedStyle(name).opacity : null,
                 firstIsShort: !!(name && name.firstElementChild &&
                     name.firstElementChild.classList.contains('ws-tr-short')),
                 short: sh ? { text: sh.textContent.trim(),
                              pz: sh.classList.contains('ws-tr-short-pz'),
                              color: shS.color, weight: shS.fontWeight,
                              size: shS.fontSize } : null,
                 restSize: rest ? getComputedStyle(rest).fontSize : null,
                 note: nt ? nt.textContent.trim() : null,
                 chkOn: chk ? chk.classList.contains('ws-done-on') : null };
    });
    return { rows: rows,
             shorts: card.querySelectorAll('.ws-tr-short').length };})()"""


def instr_card(page):
    return page.evaluate(INSTR_CARD)


def run_flow(page):
    # страница «Работники» уже открыта (кнопка #wsWorkersBtn скрыта
    # на ней) — выбор работника перерисовывает карточку, как в
    # task553-browser-check.py
    page.evaluate("WorkSchedule.selectWorkersTab('017')")
    page.wait_for_timeout(700)
    return instr_card(page)


def click_done(page, date_marker):
    # клик по галочке строки с датой-маркером; возврат — ОБЪЕКТ
    # (примитив true playwright порой отдаёт как None — урок 554)
    return page.evaluate("""(() => {
        const rows = Array.from(
            document.querySelectorAll('.ws-wcard .ws-popup-row.ws-popup-event'));
        const row = rows.find(r =>
            (r.textContent || '').indexOf('%s') !== -1);
        if (!row) return { ok: false, why: 'row' };
        const chk = row.querySelector('.ws-done-chk');
        if (!chk) return { ok: false, why: 'chk' };
        chk.click();
        return { ok: true };})()""" % date_marker)


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t555');" +
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

        print('== A: строка 101 — краткое ОТ-РИ в начале, синим, жирным ==')
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(900)
        card = run_flow(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        check('A: краткое «ОТ-РИ» — ПЕРВЫМ элементом .ws-popup-name',
              r101 and r101['firstIsShort'] is True and
              r101['short'] and r101['short']['text'] == 'ОТ-РИ',
              r101 and r101['short'])
        check('A: краткое — ЖИРНЫМ 700 и 14px («более выраженным»)',
              r101 and r101['short']['weight'] == '700' and
              r101['short']['size'] == '14px',
              r101 and r101['short'])
        check('A: краткое инструктажа — СИНИМ (тёмная тема)',
              r101 and r101['short']['color'] == BLUE_DARK,
              r101 and r101['short']['color'])
        check('A: остальной текст — 13px (мельче)',
              r101 and r101['restSize'] == '13px', r101 and r101['restSize'])
        check('A: полная тема · дата · примечание — в остальном тексте',
              r101 and 'Повторный инструктаж по рабочим инструкциям' in
              r101['text'] and '15.03.2026' in r101['text'] and
              ' · «' + NOTE_101 + '»' in r101['text'],
              r101 and r101['text'])
        shot(page, '01-workers-017-short-dark.png')

        print('== B: строка 102 — краткое ПЗ-1000В КРАСНЫМ ==')
        r102 = next((r for r in rows if 'до 1000 В' in r['text']), None)
        check('B: краткое «ПЗ-1000В» с классом ws-tr-short-pz',
              r102 and r102['short'] and r102['short']['text'] == 'ПЗ-1000В'
              and r102['short']['pz'] is True, r102 and r102['short'])
        check('B: краткое проверки знаний — КРАСНЫМ (тёмная тема)',
              r102 and r102['short']['color'] == RED_DARK,
              r102 and r102['short']['color'])

        print('== C: выполненная строка 103 — текст НЕ тускнеет ==')
        r103 = next((r for r in rows if 'инструкции № 9-ОГЭ' in r['text']), None)
        check('C: строка 103 выполнена (ws-row-done + зелёная галочка)',
              r103 and r103['done'] is True and r103['chkOn'] is True,
              r103 and (r103['done'], r103['chkOn']))
        check('C: .ws-popup-name — opacity 1 (НЕ тускнеет)',
              r103 and r103['nameOpacity'] == '1', r103 and r103['nameOpacity'])
        check('C: краткое 9-ОГЭ — прежний СИНИЙ (не тускнеет)',
              r103 and r103['short'] and
              r103['short']['text'] == '9-ОГЭ' and
              r103['short']['color'] == BLUE_DARK,
              r103 and r103['short'])
        check('C: полный текст строки читаем',
              r103 and 'Повторный инструктаж по инструкции № 9-ОГЭ' in
              r103['text'] and '10.02.2026' in r103['text'],
              r103 and r103['text'])

        print('== D: без префикса — пустое сокращение и «вне списка» ==')
        r104 = next((r for r in rows if 'промышленной безопасности' in
                     r['text']), None)
        check('D: пункт с ПУСТЫМ сокращением — строка БЕЗ .ws-tr-short',
              r104 and r104['short'] is None and
              'Проверка знаний по промышленной безопасности' in r104['text'],
              r104 and r104['short'])
        r105 = next((r for r in rows if 'Аварийный' in r['text']), None)
        check('D: тема «вне списка» — строка БЕЗ .ws-tr-short',
              r105 and r105['short'] is None and
              ' · «по предписанию № 4-ОТ»' in r105['text'],
              r105 and r105['short'])
        check('D: в карточке РОВНО три кратких наименования (101/102/103)',
              (card or {}).get('shorts') == 3, card and card['shorts'])

        print('== E: отметка выполнения — текст не тускнеет ==')
        clicked = click_done(page, '15.03.2026')
        page.wait_for_timeout(1200)
        check('E: галочка строки 101 нажата',
              bool(clicked) and clicked.get('ok') is True, repr(clicked))
        card = instr_card(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        check('E: галочка 101 стала зелёной',
              r101 and r101['chkOn'] is True, r101 and r101['chkOn'])
        check('E: текст отмеченной строки — opacity 1 (НЕ тускнеет)',
              r101 and r101['nameOpacity'] == '1', r101 and r101['nameOpacity'])
        check('E: краткое отмеченной строки — прежний СИНИЙ',
              r101 and r101['short'] and
              r101['short']['color'] == BLUE_DARK,
              r101 and r101['short'])
        check('E: полный текст и примечание на месте',
              r101 and 'Повторный инструктаж по рабочим инструкциям' in
              r101['text'] and ' · «' + NOTE_101 + '»' in r101['text'],
              r101 and r101['text'])
        shot(page, '02-workers-017-short-after-done.png')

        print('== F: светлая тема — насыщенные синий/красный ==')
        page.evaluate(
            "localStorage.setItem('kip8test:app-theme','light');" +
            "document.documentElement.setAttribute('data-theme','light')")
        page.wait_for_timeout(600)
        card = run_flow(page)
        rows = (card or {}).get('rows', [])
        r101L = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        r102L = next((r for r in rows if 'до 1000 В' in r['text']), None)
        check('F: светлая тема — краткое инструктажа СИНИМ',
              r101L and r101L['short'] and
              r101L['short']['color'] == BLUE_LIGHT,
              r101L and r101L['short']['color'])
        check('F: светлая тема — краткое ПЗ КРАСНЫМ',
              r102L and r102L['short'] and
              r102L['short']['color'] == RED_LIGHT,
              r102L and r102L['short']['color'])
        check('F: остальной текст — по-прежнему 13px',
              r101L and r101L['restSize'] == '13px', r101L and r101L['restSize'])
        shot(page, '03-workers-017-short-light.png')

        print('== G: санитар ==')
        check('G: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()
        server.shutdown()

    print('\nИТОГО: %d/%d (pass/total), FAIL=%d' %
          (PASS, PASS + FAIL, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
