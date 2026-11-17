#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 554 browser-check: перенос ПРИМЕЧАНИЯ при отметке галочкой
# о выполнении (toggleTrainingDone → сервер setTrainingDone →
# автосоздание записей с новыми сроками — «список на следующий
# год/срок»). Заявка:
#   «Внеси дополнение, при отметке галочкой о выполнении и
#    автоматическом формировании списка на следующий год, примечания
#    так же должны переноситься.»
# Сценарий (май 2026; работник 017; записи инструктажей 2026):
#  A) галочка инструкции 101 (по рабочим инструкциям ОТ, примечание
#     «протокол № 12, ведёт Иванов А.А.», выполнение = 0) → сервер
#     (srvVer '554') автосоздал ОБЕ записи (общий +6 мес 15.09.2026,
#     9-ОГЭ +3 мес 15.06.2026) — примечание ПЕРЕНЕСЕНО в созданные
#     строки карточки; тост «новые сроки», БЕЗ «старой версии»;
#     галочка 101 стала зелёной (ws-done-on);
#  B) галочка ПЗ 102 → сервер srvVer '553' (старый Apps Script,
#     примечания не переносит) — тост С предупреждением «Сервер
#     Apps Script старой версии — замените WorkSchedule.gs»
#     (порог предупреждения поднят Task 554: < 554);
#  C) санитар: 0 JS-ошибок; скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8997
Y, M = 2026, 5
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task554')
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
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

NOTE_101 = 'протокол № 12, ведёт Иванов А.А.'


# Записи «Инструктажей» 2026 года (формат 'done' сервера):
#  101 — инструктаж ОТ с примечанием, выполнение = 0 (отмечается);
#  102 — ПЗ без примечания, выполнение = 0 (старый сервер);
def T(tid, tab, tip, tema, d, comment, done, late):
    return {'id': tid, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d, 'дата_окончания': d,
            'длительность_дней': 1, 'комментарий': comment,
            'дата_проведения': d, 'выполнение': done, 'просрочен': late}


TRAININGS = [
  T(101, '017', 'инструктаж',
    'Повторный инструктаж по рабочим инструкциям ОТ',
    '2026-03-15', NOTE_101, 0, 0),
  T(102, '017', 'проверка_знаний',
    'Периодическая проверка знаний на допуск к самостоятельной работе',
    '2026-05-20', '', 0, 1),
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
                'instrList': [], 'instrAll': INSTR_ALL,
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
        if rid == 101 and val == 1:
            # НОВЫЙ сервер (Task 554): автосоздание несёт примечание
            return {'ok': True, 'data': {
                'id': 101, 'выполнение': 1, 'просрочен': 0,
                'srvVer': '554', 'autoNote': 'пункт=… дети=9-ОГЭ',
                'created': [
                    {'id': 1021, 'таб_номер': '017', 'тип': 'инструктаж',
                     'тема': 'Повторный инструктаж по инструкции № 9-ОГЭ',
                     'дата_начала': '2026-06-15', 'дата_окончания': '2026-06-15',
                     'длительность_дней': 1, 'комментарий': NOTE_101,
                     'дата_проведения': '2026-06-15', 'выполнение': 0,
                     'просрочен': 0},
                    {'id': 1022, 'таб_номер': '017', 'тип': 'инструктаж',
                     'тема': 'Повторный инструктаж по рабочим инструкциям ОТ',
                     'дата_начала': '2026-09-15', 'дата_окончания': '2026-09-15',
                     'длительность_дней': 1, 'комментарий': NOTE_101,
                     'дата_проведения': '2026-09-15', 'выполнение': 0,
                     'просрочен': 0}
                ],
                'updated': [], 'skipped': []}}
        if rid == 102 and val == 1:
            # СТАРЫЙ сервер (до Task 554): примечание не переносится
            return {'ok': True, 'data': {
                'id': 102, 'выполнение': 1, 'просрочен': 0,
                'srvVer': '553', 'autoNote': '',
                'created': [], 'updated': [], 'skipped': []}}
        return {'ok': True, 'data': {'id': rid,
                'выполнение': val, 'просрочен': 0}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Снимок блока инструктажей КАРТОЧКИ «Работники»: строки записей
INSTR_CARD = """(() => {
    const cards = Array.from(document.querySelectorAll('.ws-wcard'));
    const card = cards.find(c => {
        const h = c.querySelector('.ws-whead-t');
        return h && /Повторные инструктажи/.test(h.textContent || '');
    });
    if (!card) return null;
    const rows = Array.from(
        card.querySelectorAll('.ws-popup-row.ws-popup-event')).map(r => {
        const chk = r.querySelector('.ws-done-chk');
        const nt = r.querySelector('.ws-tr-note');
        return { text: r.textContent.replace(/\\s+/g, ' ').trim(),
                 note: nt ? nt.textContent.trim() : null,
                 chkOn: chk ? chk.classList.contains('ws-done-on') : null };
    });
    return { rows: rows,
             notes: card.querySelectorAll('.ws-tr-note').length };})()"""


def instr_card(page):
    return page.evaluate(INSTR_CARD)


def toast_hook(page):
    page.evaluate(
        "window.__toasts = [];" +
        "var _o = KipToast.show;" +
        "KipToast.show = function(t) {" +
        "  try { window.__toasts.push(String(t)); } catch (e) {}" +
        "  return _o.apply(KipToast, arguments); };")


def last_toast(page):
    t = page.evaluate("window.__toasts || []")
    return (t[-1] if t else '')


def click_done(page, date_marker):
    # клик по галочке строки с датой-маркером (например '15.03.2026');
    # возврат — ОБЪЕКТ (примитив true playwright порой отдаёт как None)
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t554');" +
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

        print('== A: галочка 101 — автосозданные записи несут примечание ==')
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(900)
        page.evaluate("WorkSchedule.selectWorkersTab('017')")
        page.wait_for_timeout(700)
        toast_hook(page)

        card = instr_card(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if '15.03.2026' in r['text']), None)
        check('A: до клика — строка 101 с примечанием',
              r101 and ' · «' + NOTE_101 + '»' in r101['text'],
              r101 and r101['text'])
        check('A: до клика — галочка 101 НЕ отмечена',
              r101 and r101['chkOn'] is False, r101 and r101['chkOn'])

        clicked = click_done(page, '15.03.2026')
        page.wait_for_timeout(1200)
        check('A: галочка строки 101 нажата',
              bool(clicked) and clicked.get('ok') is True,
              repr(clicked))

        toast = last_toast(page)
        check('A: тост «новые сроки» с датами созданных',
              'новые сроки' in toast and
              '15.06.2026' in toast and '15.09.2026' in toast, toast)
        check('A: srvVer 554 — предупреждения «старой версии» НЕТ',
              'старой версии' not in toast, toast)

        card = instr_card(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if '15.03.2026' in r['text']), None)
        check('A: после клика — галочка 101 ЗЕЛЁНАЯ (ws-done-on)',
              r101 and r101['chkOn'] is True, r101 and r101['chkOn'])
        r_oge = next((r for r in rows if '15.06.2026' in r['text']), None)
        check('A: созданная запись 9-ОГЭ 15.06.2026 — примечание ПЕРЕНЕСЕНО',
              r_oge and ' · «' + NOTE_101 + '»' in r_oge['text'] and
              '9-ОГЭ' in r_oge['text'], r_oge and r_oge['text'])
        r_ot = next((r for r in rows if '15.09.2026' in r['text']), None)
        check('A: созданный общий 15.09.2026 — примечание ПЕРЕНЕСЕНО',
              r_ot and ' · «' + NOTE_101 + '»' in r_ot['text'] and
              'рабочим инструкциям' in r_ot['text'],
              r_ot and r_ot['text'])
        check('A: примечание в .ws-tr-note созданных строк',
              r_oge and r_oge['note'] == '«' + NOTE_101 + '»',
              r_oge and r_oge['note'])
        # в карточке: 101 + созданные 2 (102 без примечания)
        check('A: в карточке РОВНО три примечания (101 + 2 созданные)',
              (card or {}).get('notes') == 3, card and card['notes'])
        shot(page, '01-workers-017-note-carry-dark.png')

        print('== B: старый сервер (srvVer 553) — предупреждение ==')
        click_done(page, '20.05.2026')
        page.wait_for_timeout(1000)
        toast = last_toast(page)
        check('B: тост содержит предупреждение «старой версии»',
              'старой версии' in toast, toast)
        check('B: подсказка «замените WorkSchedule.gs»',
              'замените WorkSchedule.gs' in toast, toast)
        shot(page, '02-toast-old-server.png')

        print('== C: санитар ==')
        check('C: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()
        server.shutdown()

    print('\nИТОГО: %d/%d (pass/total), FAIL=%d' %
          (PASS, PASS + FAIL, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
