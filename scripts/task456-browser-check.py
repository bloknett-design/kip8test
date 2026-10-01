#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 456: browser-check — заявка: авто-«д»/«н» в шахматке при
# отпуске сменного персонала («ОТ») — потенциальные смены «Д»/«Н»
# отпускника на выходных других сменных закрываются кодами «д»/«н»
# по правилам примыкания и очерёдности.
# КОНТЕКСТ (мок-сервер, порт 8980): октябрь-подобный ЛЮБОЙ текущий
# месяц; 4 сменных работника: 0441 Отпускников (цикл 4 «Д Н В В»,
# отпуск-записи «ОТ» весь месяц), 0442 Белов / 0443 Чернов (цикл 8
# «В В В Д Н В В В»), 0444 Дубов (тот же цикл 8, старт +2 дня —
# иная фаза); записи B/C/D — плановые смены (сформированный месяц):
#   A: приложение + сетка; у 0441 все дни «ОТ», авто-кодов в его
#      строке НЕТ;
#   B (ЗАЯВКА): DOM ↔ модель WorkSchedule._autoDnPlan(): каждая
#      ячейка плана — класс ws-auto-dn + текст «д»/«н» + inline-фон
#      справочника; ячеек ws-auto-dn вне плана НЕТ; ячейки с
#      записями («Д»/«Н» B/C/D) слой не трогает; есть «д» и «н»;
#   C: попап ячейки авто — строка «Авто: «д»… (замещение отпуска,
#      в записи не сохранён)», Esc закрывает; пустая ячейка без
#      авто — подсказки НЕТ;
#   D: правка поверх авто — «Д» из попапа: ws-pending + «Д»,
#      ws-auto-dn снят, _AUTO_DN ключа больше нет (пересчёт);
#   E: зритель (view) — авто-коды ВИДНЫ (слой просмотра);
#   F: мобайл 375 — авто-коды на месте;
#   G: 0 JS-ошибок ×3 контекста; скриншоты download/kip8test-task456/.
import calendar
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8980
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
DIM = calendar.monthrange(NOWY, NOWM)[1]
MD = lambda y, m, d: '%04d-%02d-%02d' % (y, m, d)

TAB_A = '0441'   # Отпускников — цикл 4, отпуск весь месяц
TAB_B = '0442'   # Белов — цикл 8
TAB_C = '0443'   # Чернов — цикл 8
TAB_D = '0444'   # Дубов — цикл 8, старт +2 дня (иная фаза)

SHOTS = '/home/z/my-project/download/kip8test-task456'
os.makedirs(SHOTS, exist_ok=True)

# шаблоны ротации (как лист «Дни_цикла»)
PAT_A = {'id': 1, 'name': 'День/ночь 12ч (Д Н В В)', 'cycle': 4,
         'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
                  {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]}
PAT_BC = {'id': 2, 'name': 'Смена 8 дней (В В В Д Н В В В)', 'cycle': 8,
          'days': [{'day': 1, 'status': ''}, {'day': 2, 'status': ''},
                   {'day': 3, 'status': ''}, {'day': 4, 'status': 'Д'},
                   {'day': 5, 'status': 'Н'}, {'day': 6, 'status': ''},
                   {'day': 7, 'status': ''}, {'day': 8, 'status': ''}]}
START_A = datetime.date(2024, 1, 1)
START_BC = datetime.date(2024, 1, 1)
START_D = datetime.date(2024, 1, 3)   # фаза цикла 8 сдвинута

EMPLOYEES = [
  {'таб_номер': TAB_A, 'ФИО': 'Отпускников О. О.', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': START_A.isoformat(),
   'дата_приёма': '2023-05-11', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': TAB_B, 'ФИО': 'Белов Б. Б.', 'тип': 'сменный',
   'смена': 2, 'шаблон_ротации': 2, 'старт_цикла': START_BC.isoformat(),
   'дата_приёма': '2022-02-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр 4 разряда', 'группа_допуска': 'III',
   'комментарий': ''},
  {'таб_номер': TAB_C, 'ФИО': 'Чернов Ч. Ч.', 'тип': 'сменный',
   'смена': 3, 'шаблон_ротации': 2, 'старт_цикла': START_BC.isoformat(),
   'дата_приёма': '2021-08-16', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Приборист 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': TAB_D, 'ФИО': 'Дубов Д. Д.', 'тип': 'сменный',
   'смена': 4, 'шаблон_ротации': 2, 'старт_цикла': START_D.isoformat(),
   'дата_приёма': '2024-03-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электрогазосварщик 4 разряда', 'группа_допуска': 'III',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'Д', 'name': 'День (12-час, 7:30–19:30)', 'color': '#FFE082',
   'short': 'день 12ч'},
  {'code': 'Н', 'name': 'Ночь (12-час, 19:30–7:30)', 'color': '#B0BEC5',
   'short': 'ночь 12ч'},
  {'code': 'д', 'name': 'День в выходной/праздник (12ч, 7:30–19:30)',
   'color': '#FFD54F', 'short': 'день в выходной'},
  {'code': 'н', 'name': 'Ночь в выходной/праздник (12ч, 19:30–7:30)',
   'color': '#78909C', 'short': 'ночь в выходной'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
]


def E(date, tab, st):
    return {'дата': date, 'таб_номер': tab, 'статус': st,
            'переработка': 0, 'праздник': 0, 'источник': 'авто'}


def planned(date, emp):
    """плановая смена работника по циклу (формула _plannedShiftAt)"""
    if emp['шаблон_ротации'] == 1:
        pat, start = PAT_A, START_A
    else:
        pat, start = PAT_BC, (START_D if emp['таб_номер'] == TAB_D
                              else START_BC)
    delta = (date - start).days
    if delta < 0:
        return ''
    doc = delta % pat['cycle'] + 1
    for d in pat['days']:
        if d['day'] == doc:
            return d['status']
    return ''


# записи месяца: A — «ОТ» весь отпуск, B/C/D — плановые смены
ENTRIES = []
for d in range(1, DIM + 1):
    dt = datetime.date(NOWY, NOWM, d)
    ENTRIES.append(E(dt.isoformat(), TAB_A, 'ОТ'))
    for emp in EMPLOYEES[1:]:
        st = planned(dt, emp)
        if st:
            ENTRIES.append(E(dt.isoformat(), emp['таб_номер'], st))

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
          (('  [' + str(extra)[:250] + ']') if (extra and not ok) else ''))


def api_response(action, body, editor=True):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': editor,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': [PAT_A, PAT_BC]}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': [], 'instrList': [],
                'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in ENTRIES]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length).decode('utf-8', 'replace') \
            if length else ''
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {}
        action = ''
        if 'action=' in self.path:
            action = unquote(self.path.split('action=')[1].split('&')[0])
        resp = api_response(action, body)
        out = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type',
                         'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def attach(page, ctx, theme, tag, editor=True):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t456-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        if body is None:
            body = {}
        resp = api_response(action, body, editor=editor)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t456-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# DOM-скан авто-ячеек + план модели: ключ «ISO|таб», текст, стиль
GRID_STATE_JS = (
    "(function(){"
    "var plan = (typeof WorkSchedule !== 'undefined' && WorkSchedule._autoDnPlan)"
    " ? WorkSchedule._autoDnPlan() : null;"
    "var cells = {}, styles = {}, rows = {};"
    "document.querySelectorAll('td.ws-cell.ws-auto-dn').forEach(function(td){"
    "var m = (td.getAttribute('onclick')||'').match(/'([^']+)','([^']+)'/);"
    "if (!m) return;"
    "var k = m[1] + '|' + m[2];"
    "cells[k] = (td.textContent || '').trim();"
    "styles[k] = td.getAttribute('style') || '';"
    "rows[k] = m[2];});"
    "var pending = Object.keys((WorkSchedule._PENDING)||{}).length;"
    "return {plan: plan, cells: cells, styles: styles, rows: rows,"
    " pending: pending};})()")


def main():
    srv = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 светлая, Админ (edit) =====
        print('=== Контекст: десктоп светлая — авто-«д»/«н» замещения '
              'отпуска ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'light', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        print('--- A: сетка открыта, месяц текущий ---')
        check('A1: приложение загрузилось, шахматка открыта',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))
        msel = page.evaluate("(function(){var s=document.getElementById(" +
                             "'wsMonthSel');return s?parseInt(s.value,10):"
                             "null;})()")
        check('A2: сетка на текущем месяце (%d)' % NOWM, msel == NOWM, msel)
        check('A3: у отпускника 0441 дни «ОТ» (записи пришли)',
              page.evaluate(
                  "(function(){var n=0;"
                  "document.querySelectorAll('td.ws-cell').forEach(function(td){"
                  "var oc = td.getAttribute('onclick')||'';"
                  "if (oc.indexOf(\"'%s'\") !== -1 && " % TAB_A +
                  "td.textContent.indexOf('ОТ') !== -1) n++;});"
                  "return n;})()") >= 20,
              'записи «ОТ» отпускника в DOM (у смен — бейдж смены рядом)')

        print('--- B (ЗАЯВКА): авто-«д»/«н» — DOM ↔ модель _autoDnPlan ---')
        st = page.evaluate(GRID_STATE_JS)
        plan = st['plan']
        check('B1: план модели не пуст (сценарий с отпускником сработал)',
              plan and len(plan) >= 1, plan)
        if plan:
            check('B2: DOM-ячеек ws-auto-dn ровно столько, сколько в плане',
                  len(st['cells']) == len(plan),
                  'dom=%s plan=%s' % (len(st['cells']), len(plan)))
            dom_keys = set(st['cells'].keys())
            plan_keys = set(plan.keys())
            check('B3: ключи DOM == ключи плана (нет лишних/потерянных)',
                  dom_keys == plan_keys,
                  'только DOM: %s; только план: %s' %
                  (sorted(dom_keys - plan_keys)[:5],
                   sorted(plan_keys - dom_keys)[:5]))
            mism = [k for k in plan if st['cells'].get(k) != plan[k]]
            check('B4: текст каждой ячейки = код плана («д»/«н»)',
                  not mism, mism[:5])
            no_bg = [k for k in st['styles']
                     if 'background' not in st['styles'][k]]
            check('B5: у всех авто-ячеек inline-фон справочника',
                  not no_bg, no_bg[:5])
            in_a = [k for k in plan if k.endswith('|' + TAB_A)]
            check('B6: у отпускника авто-кодов НЕТ (сам в отпуске)',
                  not in_a, in_a[:3])
            vals = list(plan.values())
            check('B7: есть коды «д» и «н» (обе смены отпускника)',
                  'д' in vals and 'н' in vals,
                  {v: vals.count(v) for v in set(vals)})
            # ячейки с записями B/C/D («Д»/«Н») слой не трогает:
            # все ключи плана — только пустые выходные дни кандидатов
            overlap = [k for k in plan
                       if k.split('|')[1] == TAB_A]
            check('B8: записи кандидатов не перекрываются (в плане только их выходные)',
                  not overlap, overlap[:3])

        # день с рабочей записью «Д» у Белова — авто нет, код на месте
        b_workday = None
        for d in range(1, DIM + 1):
            dt = datetime.date(NOWY, NOWM, d)
            if planned(dt, EMPLOYEES[1]) == 'Д':
                b_workday = dt
                break
        if b_workday:
            iso = b_workday.isoformat()
            cell = page.evaluate(
                "(function(){var td = document.querySelector("
                "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso, TAB_B) +
                "if (!td) return null;"
                "return {text: td.textContent.trim(),"
                "auto: td.classList.contains('ws-auto-dn')};})()")
            check('B9: рабочая запись «Д» Белова %s — код без авто' % iso,
                  cell and cell['text'] == 'Д' and not cell['auto'], cell)

        page.screenshot(path=os.path.join(SHOTS, '01-desktop-grid.png'))

        print('--- C: попап ячейки авто-кода — подсказка «замещение отпуска» ---')
        if plan:
            first_key = sorted(plan.keys())[0]
            iso_d, tab_d = first_key.split('|')
            page.click("td.ws-cell[onclick*=\"%s\"][onclick*=\"%s\"]"
                       % (iso_d, tab_d))
            page.wait_for_timeout(600)
            auto_line = page.evaluate(
                "(function(){var e = document.querySelector('.ws-popup-auto');"
                "return e ? e.textContent.trim() : null;})()")
            check('C1: строка «Авто: «%s»… (замещение отпуска…)»'
                  % plan[first_key],
                  auto_line and 'Авто' in auto_line and
                  plan[first_key] in auto_line and
                  'замещение отпуска' in auto_line and
                  'в записи не сохранён' in auto_line, auto_line)
            page.screenshot(path=os.path.join(SHOTS, '02-popup-auto.png'))
            page.keyboard.press('Escape')
            page.wait_for_timeout(400)
            check('C2: Esc закрыл попап',
                  not page.evaluate(
                      "(function(){return !!document.querySelector("
                      "'.ws-popup-auto');})()"))
            # пустая ячейка без авто — подсказки нет
            n_empty = page.evaluate(
                "(function(){return document.querySelectorAll("
                "'td.ws-cell.ws-status-empty:not(.ws-auto-dn):not("
                ".ws-vac-plan)').length;})()")
            if n_empty:
                page.click('td.ws-cell.ws-status-empty:not(.ws-auto-dn):not('
                           '.ws-vac-plan)')
                page.wait_for_timeout(500)
                check('C3: у пустой ячейки БЕЗ авто подсказки нет',
                      not page.evaluate(
                          "(function(){return !!document.querySelector("
                          "'.ws-popup-auto');})()"))
                page.keyboard.press('Escape')
                page.wait_for_timeout(300)

            print('--- D: правка поверх авто-кода — слой уступает записи ---')
            page.click("td.ws-cell[onclick*=\"%s\"][onclick*=\"%s\"]"
                       % (iso_d, tab_d))
            page.wait_for_timeout(600)
            page.click("div.ws-popup-row[onclick=\"WorkSchedule.onPopupStatus("
                       "'Д')\"]")
            page.wait_for_timeout(700)
            st2 = page.evaluate(GRID_STATE_JS)
            cell2 = page.evaluate(
                "(function(){var td = document.querySelector("
                "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso_d, tab_d) +
                "if (!td) return null;"
                "return {text: td.textContent.trim(),"
                "auto: td.classList.contains('ws-auto-dn'),"
                "pending: td.classList.contains('ws-pending')};})()")
            check('D1: ячейка %s/%s — ручная «Д» (pending), авто снят'
                  % (iso_d, tab_d),
                  cell2 and cell2['text'] == 'Д' and cell2['pending'] and
                  not cell2['auto'], cell2)
            check('D2: план пересчитан — ключа ячейки в _AUTO_DN больше нет',
                  first_key not in (st2['plan'] or {}))
            check('D3: правка в буфере _PENDING',
                  st2['pending'] >= 1, st2['pending'])
            page.screenshot(path=os.path.join(SHOTS, '03-after-manual-edit.png'))

        check('G1: 0 JS-ошибок (десктоп)', not js_errors, js_errors[:4])
        ctx.close()

        # ===== зритель (view) =====
        print('=== Контекст: зритель — авто-коды видны ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'viewer', editor=False)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        st3 = page2.evaluate(GRID_STATE_JS)
        check('E1: зритель: авто-ячейки в DOM есть',
              len(st3['cells']) >= 1, len(st3['cells']))
        check('E2: зритель: план модели совпадает с DOM',
              set(st3['cells'].keys()) == set((st3['plan'] or {}).keys()))
        page2.screenshot(path=os.path.join(SHOTS, '04-viewer.png'))
        check('G2: 0 JS-ошибок (зритель)', not js_errors2, js_errors2[:4])
        ctx2.close()

        # ===== мобайл 375 =====
        print('=== Контекст: мобайл 375 — авто-коды на месте ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'dark', 'mobile')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2500)
        st4 = page3.evaluate(GRID_STATE_JS)
        check('F1: мобайл: авто-ячейки в DOM есть',
              len(st4['cells']) >= 1, len(st4['cells']))
        page3.screenshot(path=os.path.join(SHOTS, '05-mobile.png'))
        check('G3: 0 JS-ошибок (мобайл)', not js_errors3, js_errors3[:4])
        ctx3.close()

        browser.close()

    print('\n═══════════════════════════════════════════')
    print('  Task 456 browser-check: %d passed, %d failed'
          % (PASS, FAIL))
    print('═══════════════════════════════════════════')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
