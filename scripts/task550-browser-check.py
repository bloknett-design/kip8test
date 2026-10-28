#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 550 browser-check: итоги учёта — столбец «Отпуск (ОТ)»
# считает «чистые» дни: нерабочие праздничные дни ст. 112 НЕ
# входят в число дней отпуска (ст. 120 ТК РФ). Заявка:
#   «В разделе Табель учёта рабочего времени при расчёте в итогах
#    учёта количества дней отпуска, официальные праздничные дни,
#    которые не учитываются в отпуске, не должны учитываться
#    в данном расчёте».
# Сценарий (май 2026, праздники ст. 112: 01.05 + 09.05; источник
# ProdCalendar — фолбэк на фиксированные даты, внешние календари
# закрыты 404):
#  A) 017 (дневной) — «ОТ» на ВСЕ 31 день мая; сетка показывает
#     «ОТ» и на праздниках (отпуск в календарных днях, записи
#     остаются — сервер не менялся);
#  B) итоги «Месяц» (доп. столбцы развёрнуты): «Отпуск (ОТ)»
#     у 017 = 29 (31 − 2 праздника); тултип столбца называет
#     ст. 120 ТК РФ;
#  C) 023 (сменный): «У» 01.05 + 04.05 → «Уч. отпуск (У)» = 2
#     (уч. отпуск в календарных днях — праздники входят);
#     «Б» 09.05 → «Больничный (Б)» = 1 (без вычета); «Д» 12-го +
#     «Н» 13-го → Явки 2 / Часы 24 / День 1 / Ночь 1 — прочие
#     счётчики не задеты;
#  D) 0 JS-ошибок; скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
Y, M = 2026, 5
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task550')
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
  {'code': 'У', 'name': 'Уч. отпуск', 'color': '#E1F5FE'},
  {'code': 'Б', 'name': 'Больничный', 'color': '#FFEBEE'},
  {'code': 'В', 'name': 'Выходной (вручную)', 'color': '#EEF0F2'},
]
# 017 — ДНЕВНОЙ в отпуске весь май (Task 456 план подмен работает
# только со сменными отпускниками — шума авто-«д»/«н» нет);
# 023 — сменный со сменами и неявками на праздниках
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


def E(day, tab, status, source):
    return {'дата': '2026-05-%02d' % day, 'таб_номер': tab,
            'статус': status, 'переработка': 0, 'праздник': 0,
            'источник': source, 'дата_обновления':
            '2026-10-25T08:00:00.000Z', 'замещает': None,
            'инструкция': None, 'комментарий': '', 'часы': None,
            'время_начала': None, 'время_окончания': None}


ENTRIES = []
for d in range(1, 32):
    ENTRIES.append(E(d, '017', 'ОТ', 'авто'))     # весь май в отпуске
ENTRIES.append(E(1, '023', 'У', 'руч'))           # 01.05 — праздник
ENTRIES.append(E(4, '023', 'У', 'руч'))           # 04.05 — рабочий день
ENTRIES.append(E(9, '023', 'Б', 'руч'))           # 09.05 — праздник
ENTRIES.append(E(12, '023', 'Д', 'авто'))
ENTRIES.append(E(13, '023', 'Н', 'авто'))
VACATIONS = [
    {'id': 1, 'таб_номер': '017', 'часть': 1,
     'дата_начала': '2026-05-01', 'дата_окончания': '2026-05-31',
     'дней': 31, 'комментарий': ''},
]
TRAININGS = []
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
        return {'ok': True, 'data': {'trainings': TRAININGS}}
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


CELL_TEXT = """((p) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + p.tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    const td = row.querySelector('td[data-day="' + p.day + '"]');
    return td ? td.textContent.trim() : null;})"""


def cell_text(page, tab, day):
    return page.evaluate(CELL_TEXT, {'tab': tab, 'day': day})


TOTALS = """(() => {
    const body = document.getElementById('wsTtBody');
    if (!body) return null;
    const table = body.querySelector('.ws-tt-table');
    if (!table) return null;
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => ({
        text: th.textContent.trim(),
        title: th.getAttribute('title') || ''}));
    const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => ({
        tab: ((tr.querySelector('.ws-tt-tabno') || {}).textContent || '').trim(),
        cells: Array.from(tr.querySelectorAll('td')).slice(1)
                .map(td => td.textContent.trim())}));
    return {headers: headers, rows: rows};})()"""


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t550');" +
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

        # месяц → май 2026 (праздники 01.05 + 09.05)
        page.select_option('#wsMonthSel', str(M))
        page.select_option('#wsYearSel', str(Y))
        page.wait_for_timeout(2500)

        # ===== A: сетка — «ОТ» стоит и на праздниках =====
        print('== A: сетка — отпуск в календарных днях (запись на празднике) ==')
        check('A: 017 01.05 — «ОТ» (праздник остаётся днём табеля)',
              (cell_text(page, '017', '1') or '').startswith('ОТ'),
              cell_text(page, '017', '1'))
        check('A: 017 09.05 — «ОТ» (праздник остаётся днём табеля)',
              (cell_text(page, '017', '9') or '').startswith('ОТ'),
              cell_text(page, '017', '9'))
        check('A: 017 05.05 — «ОТ» (обычный день)',
              (cell_text(page, '017', '5') or '').startswith('ОТ'),
              cell_text(page, '017', '5'))
        check('A: 023 01.05 — «У» (+ бейдж плановой «Д» — Task 305)',
              (cell_text(page, '023', '1') or '').startswith('У'),
              cell_text(page, '023', '1'))
        check('A: 023 09.05 — «Б» (больничный на празднике)',
              (cell_text(page, '023', '9') or '').startswith('Б'),
              cell_text(page, '023', '9'))
        shot(page, '01-grid-may-ot.png')

        # ===== B: итоги «Месяц» — «Отпуск (ОТ)» без праздников =====
        print('== B: итоги учёта — «чистые» дни отпуска ==')
        page.click('#wsTotalsBtn')
        page.wait_for_timeout(900)
        page.click('#wsTtChv')     # «Ещё» — доп. столбцы
        page.wait_for_timeout(500)
        tt = page.evaluate(TOTALS)
        check('B: таблица итогов отрисована', tt and tt.get('rows'), tt)
        headers = [h['text'] for h in (tt or {}).get('headers') or []]
        check('B: доп. столбцы развёрнуты — «Отпуск (ОТ)» есть',
              'Отпуск (ОТ)' in headers, headers)
        hmeta = {h['text']: h['title'] for h in (tt or {}).get('headers') or []}
        check('B: тултип столбца «Отпуск (ОТ)» — ст. 120 ТК РФ',
              'ст. 120 ТК РФ' in hmeta.get('Отпуск (ОТ)', ''),
              hmeta.get('Отпуск (ОТ)'))
        check('B: тултип объясняет вычет праздников',
              'нерабочих праздничных дней' in hmeta.get('Отпуск (ОТ)', ''),
              hmeta.get('Отпуск (ОТ)'))
        rows = {r['tab']: r['cells'] for r in (tt or {}).get('rows') or []}
        # индекс колонки в строке: headers[0] — «Работник», cells —
        # данные ПОСЛЕ него (headers[1:] ↔ cells 1:1)
        idx = {name: i for i, name in enumerate(headers[1:])}

        def val(tab, col):
            r = rows.get(tab) or []
            i = idx.get(col, -1)
            return r[i] if 0 <= i < len(r) else None

        check('B: 017 «Отпуск (ОТ)» = 29 (31 − 01.05 − 09.05)',
              val('017', 'Отпуск (ОТ)') == '29', val('017', 'Отпуск (ОТ)'))
        check('B: 017 «Явки (дни)» пусто (0)',
              val('017', 'Явки (дни)') == '', val('017', 'Явки (дни)'))
        check('B: 017 «Уч. отпуск (У)» пусто',
              val('017', 'Уч. отпуск (У)') == '', val('017', 'Уч. отпуск (У)'))
        shot(page, '02-totals-ot-29.png')

        # ===== C: прочие счётчики — праздники не вычитаются =====
        print('== C: «У»/«Б»/явки — без вычета (как прежде) ==')
        check('C: 023 «Уч. отпуск (У)» = 2 (01.05+04.05 — праздник входит)',
              val('023', 'Уч. отпуск (У)') == '2', val('023', 'Уч. отпуск (У)'))
        check('C: 023 «Больничный (Б)» = 1 (09.05 — праздник входит)',
              val('023', 'Больничный (Б)') == '1', val('023', 'Больничный (Б)'))
        check('C: 023 «Отпуск (ОТ)» пусто',
              val('023', 'Отпуск (ОТ)') == '', val('023', 'Отпуск (ОТ)'))
        check('C: 023 «Явки (дни)» = 2 (Д+Н)',
              val('023', 'Явки (дни)') == '2', val('023', 'Явки (дни)'))
        check('C: 023 «Часы» = 24 (12+12)',
              val('023', 'Часы') == '24', val('023', 'Часы'))
        check('C: 023 «День (Д)» = 1', val('023', 'День (Д)') == '1',
              val('023', 'День (Д)'))
        check('C: 023 «Ночь (Н)» = 1', val('023', 'Ночь (Н)') == '1',
              val('023', 'Ночь (Н)'))
        shot(page, '03-totals-u-b-work.png')

        # ===== D: санитар =====
        print('== D: санитар ==')
        check('D: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()
        server.shutdown()

    print('\nИТОГО: %d/%d (pass/total), FAIL=%d' %
          (PASS, PASS + FAIL, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
