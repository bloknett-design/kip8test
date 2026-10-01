#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 457: browser-check — заявка: «Сделай отображение этих
# кодов как ручные, в Итоги/Талоны/печать входит» (развитие
# Task 456: авто-«д»/«н» замещения отпуска).
# КОНТЕКСТ (мок-сервер, порт 8982): текущий месяц; 4 сменных:
# 0441 Отпускников (цикл 4 «Д Н В В», «ОТ» весь месяц),
# 0442 Белов / 0443 Чернов (цикл 8 «В В В Д Н В В В»),
# 0444 Дубов (цикл 8, старт +2 дня); записи B/C/D — плановые
# смены; ПЛЮС ручная запись «д» (источник «руч») у Дубова в
# первый планово-выходной день (эталон «как ручные» в DOM):
#   A: приложение + сетка, «ОТ» отпускника;
#   B (ЗАЯВКА-1 «как ручные»): DOM ↔ модель; у каждой авто-ячейки
#      ws-manual-dn + ws-source-manual, НЕТ ws-status-empty,
#      пунктирного outline НЕТ, ::before-рамка ЕСТЬ, фон/шрифт
#      совпадают с ручной «д» записью;
#   C: попап — новый текст «учитывается в Итогах/Талонах/печати»
#      (старого «в записи не сохранён» НЕТ), строка «д»/«н»
#      АКТИВНА (ws-popup-active), Esc закрывает;
#   D (ЗАЯВКА-2 «Итоги»): шторка «Итоги учёта» — Переработка
#      (дни) = авто-коды (+ручная «д» Дубова), Явки/Часы НЕ
#      тронуты, title-подсказка часов;
#   E (ЗАЯВКА-3 «Талоны»): дни явки и 12-часовые талоны выросли
#      на авто-коды, чипы итогов;
#   F (ЗАЯВКА-4 «печать»): предпросмотр печати — авто-коды
#      в сетке листа (фон справочника), «Перераб./дни» строки;
#   G: правка «Д» поверх авто по-прежнему снимает слой;
#   H/I/J: зритель (авто с рамкой ручных), мобайл 375 (страница
#      итогов ws-totals), 0 JS-ошибок ×3; скриншоты
#      download/kip8test-task457/.
import calendar
import datetime
import json
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8982
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
DIM = calendar.monthrange(NOWY, NOWM)[1]

TAB_A = '0441'   # Отпускников — цикл 4, отпуск весь месяц
TAB_B = '0442'   # Белов — цикл 8
TAB_C = '0443'   # Чернов — цикл 8
TAB_D = '0444'   # Дубов — цикл 8, старт +2 дня (иная фаза)

SHOTS = '/home/z/my-project/download/kip8test-task457'
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


def E(date, tab, st, src='авто'):
    return {'дата': date, 'таб_номер': tab, 'статус': st,
            'переработка': 0, 'праздник': 0, 'источник': src}


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


# записи месяца: A — «ОТ» весь отпуск, B/C/D — плановые смены,
# Дубов — ПЛЮС ручная «д» в первый планово-выходной день (эталон
# «как ручные»: ws-source-manual + ws-manual-dn, БЕЗ ws-auto-dn)
ENTRIES = []
MANUAL_DN = None      # (iso, tab) ручной «д» Дубова
for d in range(1, DIM + 1):
    dt = datetime.date(NOWY, NOWM, d)
    ENTRIES.append(E(dt.isoformat(), TAB_A, 'ОТ'))
    for emp in EMPLOYEES[1:]:
        st = planned(dt, emp)
        if st:
            ENTRIES.append(E(dt.isoformat(), emp['таб_номер'], st))
if MANUAL_DN is None:
    for d in range(1, DIM + 1):
        dt = datetime.date(NOWY, NOWM, d)
        if planned(dt, EMPLOYEES[3]) == '':
            MANUAL_DN = (dt.isoformat(), TAB_D)
            ENTRIES.append(E(dt.isoformat(), TAB_D, 'д', src='руч'))
            break

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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t457-%s');" % tag +
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
                      body='not found (t457-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# DOM-скан авто-ячеек (классы/стили) + план модели
GRID_STATE_JS = (
    "(function(){"
    "var plan = (typeof WorkSchedule !== 'undefined' && WorkSchedule._autoDnPlan)"
    " ? WorkSchedule._autoDnPlan() : null;"
    "var cells = {}, cls = {}, styles = {};"
    "document.querySelectorAll('td.ws-cell.ws-auto-dn').forEach(function(td){"
    "var m = (td.getAttribute('onclick')||'').match(/'([^']+)','([^']+)'/);"
    "if (!m) return;"
    "var k = m[1] + '|' + m[2];"
    "cells[k] = (td.textContent || '').trim();"
    "cls[k] = td.className;"
    "styles[k] = td.getAttribute('style') || '';});"
    "var pending = Object.keys((WorkSchedule._PENDING)||{}).length;"
    "return {plan: plan, cells: cells, cls: cls, styles: styles,"
    " pending: pending};})()")


def cell_props_js(iso, tab):
    """computed-стили ячейки: фон, шрифт, outline, ::before-рамка"""
    return (
        "(function(){var td = document.querySelector("
        "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso, tab) +
        "if (!td) return null;"
        "var cs = getComputedStyle(td);"
        "var bf = getComputedStyle(td, '::before');"
        "return {cls: td.className, bg: cs.backgroundColor,"
        " fw: cs.fontWeight, os: cs.outlineStyle, ow: cs.outlineWidth,"
        " bfStyle: bf.borderStyle, bfWidth: bf.borderWidth};})()")


def cell_bg_matches_code_js(iso, tab, code):
    """computed-фон ячейки == цвету справочника её кода (hex→rgb)"""
    return (
        "(function(){var td = document.querySelector("
        "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso, tab) +
        "if (!td) return null;"
        "var meta = WorkSchedule._statusMeta('%s') || {};" % code +
        "if (!meta.color) return null;"
        "var h = meta.color.replace('#', '');"
        "var exp = 'rgb(' + parseInt(h.substr(0,2),16) + ', ' +"
        " parseInt(h.substr(2,2),16) + ', ' +"
        " parseInt(h.substr(4,2),16) + ')';"
        "var cs = getComputedStyle(td);"
        "return {bg: cs.backgroundColor, exp: exp,"
        " ok: cs.backgroundColor === exp};})()")


def main():
    srv = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 светлая, Админ (edit) =====
        print('=== Контекст: десктоп светлая — авто-«д»/«н» '
              'как ручные + Итоги/Талоны/печать ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'light', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        print('--- A: сетка открыта, месяц текущий ---')
        check('A1: приложение загрузилось, шахматка открыта',
              page.evaluate(
                  "(function(){return !!document.querySelector("
                  "'.ws-grid');})()"))
        msel = page.evaluate(
            "(function(){var s=document.getElementById('wsMonthSel');"
            "return s?parseInt(s.value,10):null;})()")
        check('A2: сетка на текущем месяце (%d)' % NOWM, msel == NOWM, msel)
        check('A3: у отпускника 0441 дни «ОТ» (записи пришли)',
              page.evaluate(
                  "(function(){var n=0;"
                  "document.querySelectorAll('td.ws-cell').forEach(function(td){"
                  "var oc = td.getAttribute('onclick')||'';"
                  "if (oc.indexOf(\"'%s'\") !== -1 && " % TAB_A +
                  "td.textContent.indexOf('ОТ') !== -1) n++;});"
                  "return n;})()") >= 20)

        print('--- B (ЗАЯВКА «как ручные»): авто-ячейки = вид ручных «д»/«н» ---')
        st = page.evaluate(GRID_STATE_JS)
        plan = st['plan']
        check('B1: план слоя не пуст', plan and len(plan) >= 1, plan)
        if plan:
            dom_keys = set(st['cells'].keys())
            plan_keys = set(plan.keys())
            check('B2: DOM ↔ модель: ключи 1:1',
                  dom_keys == plan_keys and
                  all(st['cells'].get(k) == plan[k] for k in plan),
                  'dom=%s plan=%s' % (len(dom_keys), len(plan_keys)))
            bad_cls = [k for k in plan
                       if 'ws-manual-dn' not in (st['cls'].get(k) or '')
                       or 'ws-source-manual' not in (st['cls'].get(k) or '')]
            check('B3: у каждой авто-ячейки рамка ws-manual-dn + метка '
                  'ws-source-manual', not bad_cls, bad_cls[:4])
            bad_empty = [k for k in plan
                         if 'ws-status-empty' in (st['cls'].get(k) or '')]
            check('B4: авто-ячейки НЕ «пустые» (без ws-status-empty)',
                  not bad_empty, bad_empty[:4])
            no_bg = [k for k in plan
                     if 'background' not in (st['styles'].get(k) or '')]
            check('B5: inline-фон справочника у всех авто-ячеек',
                  not no_bg, no_bg[:4])
            # computed-стили: пунктира НЕТ, ::before-рамка ЕСТЬ
            fk = sorted(plan.keys())[0]
            iso_fk, tab_fk = fk.split('|')
            pr = page.evaluate(cell_props_js(iso_fk, tab_fk))
            bgm = page.evaluate(cell_bg_matches_code_js(iso_fk, tab_fk,
                                                         plan[fk]))
            check('B6: пунктирный outline СНЯТ (outline-style: none)',
                  pr and pr['os'] == 'none', pr)
            check('B7: ::before-рамка ручных д/н — ЕСТЬ (solid)',
                  pr and pr['bfStyle'] == 'solid' and
                  pr['bfWidth'] not in ('0px', ''), pr)
            # ручная «д» Дубова — эталон; полное сравнение стилей
            mr = page.evaluate(cell_props_js(MANUAL_DN[0], MANUAL_DN[1]))
            check('B8: ручная «д» Дубова в DOM (источник «руч»: '
                  'ws-manual-dn, БЕЗ ws-auto-dn/ws-pending)',
                  mr and 'ws-manual-dn' in mr['cls'] and
                  'ws-source-manual' in mr['cls'] and
                  'ws-auto-dn' not in mr['cls'] and
                  'ws-pending' not in mr['cls'], mr)
            check('B9: фон авто == цвету справочника её кода'
                  ' (как у ручной записи)',
                  bgm and bgm['ok'], bgm)
            # если в плане есть «д» — прямое сравнение с ручной «д»
            if plan[fk] == 'д':
                check('B9a: фон авто-«д» == фон ручной «д» Дубова',
                      pr and mr and pr['bg'] == mr['bg'],
                      'auto=%s manual=%s' % (pr and pr['bg'],
                                             mr and mr['bg']))
            check('B10: шрифт авто == шрифт ручной «д»',
                  pr and mr and pr['fw'] == mr['fw'])
            page.screenshot(path=os.path.join(SHOTS, '01-desktop-grid.png'))

        print('--- C: попап авто-кода — подсказка + АКТИВНАЯ строка ---')
        if plan:
            fk = sorted(plan.keys())[0]
            iso_d, tab_d = fk.split('|')
            code = plan[fk]
            page.click('td.ws-cell[onclick*="%s"][onclick*="%s"]'
                       % (iso_d, tab_d))
            page.wait_for_timeout(600)
            auto_line = page.evaluate(
                "(function(){var e = document.querySelector('.ws-popup-auto');"
                "return e ? e.textContent.trim() : null;})()")
            check('C1: подсказка «Авто: «%s»… (замещение отпуска, '
                  'учитывается в Итогах/Талонах/печати)»' % code,
                  auto_line and 'Авто' in auto_line and
                  code in auto_line and
                  'замещение отпуска' in auto_line and
                  'учитывается в Итогах/Талонах/печати' in auto_line,
                  auto_line)
            check('C2: старого текста «в записи не сохранён» НЕТ',
                  auto_line and 'в записи не сохранён' not in auto_line)
            active = page.evaluate(
                "(function(){var rows = document.querySelectorAll("
                "'.ws-popup-row');"
                "for (var i = 0; i < rows.length; i++) {"
                "var oc = rows[i].getAttribute('onclick') || '';"
                "if (oc.indexOf(\"onPopupStatus('%s')\") !== -1)" % code +
                " return rows[i].className;}"
                "return null;})()")
            check('C3: строка «%s» в попапе АКТИВНА (ws-popup-active)'
                  % code,
                  active and 'ws-popup-active' in active, active)
            page.screenshot(path=os.path.join(SHOTS, '02-popup-active.png'))
            page.keyboard.press('Escape')
            page.wait_for_timeout(400)
            check('C4: Esc закрыл попап',
                  not page.evaluate(
                      "(function(){return !!document.querySelector("
                      "'.ws-popup-auto');})()"))

        print('--- D (ЗАЯВКА «Итоги»): переработка авто-«д»/«н» ---')
        auto_cnt = {}
        for k in (plan or {}):
            t = k.split('|')[1]
            auto_cnt[t] = auto_cnt.get(t, 0) + 1
        page.click('#wsTotalsBtn')
        page.wait_for_timeout(900)
        tt = page.evaluate(
            "(function(){var out = {};"
            "document.querySelectorAll('#wsTtBody tbody tr').forEach("
            "function(tr){var f = tr.querySelector('.ws-tt-tabno');"
            "if (!f) return;"
            "var tds = tr.querySelectorAll('td.ws-tt-num');"
            "var ov = tds.length >= 3 ? tds[2] : null;"
            "out[f.textContent.trim()] = {"
            "work: tds.length ? tds[0].textContent.trim() : '',"
            "hours: tds.length >= 2 ? tds[1].textContent.trim() : '',"
            "over: ov ? ov.textContent.trim() : '',"
            "overTitle: ov ? (ov.getAttribute('title') || '') : ''};});"
            "return out;})()")
        exp_b_over = auto_cnt.get(TAB_B, 0)
        exp_d_over = auto_cnt.get(TAB_D, 0) + 1     # + ручная «д»
        shifts_b = sum(1 for d in range(1, DIM + 1)
                       if planned(datetime.date(NOWY, NOWM, d),
                                  EMPLOYEES[1]) in ('Д', 'Н'))
        shifts_d = sum(1 for d in range(1, DIM + 1)
                       if planned(datetime.date(NOWY, NOWM, d),
                                  EMPLOYEES[3]) in ('Д', 'Н'))
        check('D1: шторка итогов: таблица с работниками', bool(tt), tt)
        check('D2: Белов: Переработка (дни) = %d авто-кодов'
              % exp_b_over,
              tt.get(TAB_B, {}).get('over') == str(exp_b_over),
              tt.get(TAB_B))
        check('D3: Белов: title-подсказка «часов переработки: %s»'
              % str(12 * exp_b_over),
              ('часов переработки: %s' % (12 * exp_b_over))
              in tt.get(TAB_B, {}).get('overTitle', ''),
              tt.get(TAB_B, {}).get('overTitle'))
        check('D4: Дубов: Переработка (дни) = %d авто + 1 ручная «д»'
              % auto_cnt.get(TAB_D, 0),
              tt.get(TAB_D, {}).get('over') == str(exp_d_over),
              tt.get(TAB_D))
        check('D5: Белов: Явки = %d смен (авто в явки НЕ входит)'
              % shifts_b,
              tt.get(TAB_B, {}).get('work') == str(shifts_b),
              tt.get(TAB_B))
        check('D6: Белов: Часы = %s (не тронуты авто)'
              % str(12 * shifts_b),
              tt.get(TAB_B, {}).get('hours') == str(12 * shifts_b),
              tt.get(TAB_B))
        page.screenshot(path=os.path.join(SHOTS, '03-totals-drawer.png'))
        page.click('#wsTotalsBtn')     # закрыть шторку
        page.wait_for_timeout(600)

        print('--- E (ЗАЯВКА «Талоны»): дни явки + 12-часовые талоны ---')
        page.click('#wsTalonsBtn')
        page.wait_for_timeout(900)
        rs = page.evaluate(
            "(function(){function val(tab,cat){var i=document.querySelector("
            "'input.wst-count[data-tab=\"'+tab+'\"][data-cat=\"'+cat+'\"]');"
            "return i?i.value:null;}"
            "var days={};document.querySelectorAll('.wst-table tbody tr')"
            ".forEach(function(tr){var f=tr.querySelector('.wst-fio');"
            "var d=tr.querySelector('.wst-c-days');"
            "if(f&&d)days[f.textContent.trim()]=d.textContent.trim();});"
            "function chip(id){var e=document.getElementById(id);"
            "return e?e.textContent:null;}"
            "return {b12:val('" + TAB_B + "','t12'),"
            "d12:val('" + TAB_D + "','t12'),"
            "c12:val('" + TAB_C + "','t12'),"
            "days:days,t12chip:chip('wstTotalT12Chip')};})()")
        exp_b_tal = shifts_b + auto_cnt.get(TAB_B, 0)
        exp_c_tal = shifts_c = sum(
            1 for d in range(1, DIM + 1)
            if planned(datetime.date(NOWY, NOWM, d), EMPLOYEES[2])
            in ('Д', 'Н')) + auto_cnt.get(TAB_C, 0)
        exp_d_tal = shifts_d + auto_cnt.get(TAB_D, 0) + 1   # + ручная «д»
        exp_total = exp_b_tal + exp_c_tal + exp_d_tal
        check('E1: Белов: 12ч талонов = %d смен + %d авто = %s'
              % (shifts_b, auto_cnt.get(TAB_B, 0), exp_b_tal),
              rs['b12'] == str(exp_b_tal), rs)
        check('E2: Дубов: 12ч = %d смен + %d авто + 1 ручная = %s'
              % (shifts_d, auto_cnt.get(TAB_D, 0), exp_d_tal),
              rs['d12'] == str(exp_d_tal), rs)
        check('E3: Чернов: 12ч = %s' % exp_c_tal,
              rs['c12'] == str(exp_c_tal), rs)
        check('E4: «Дней явки» Белова = %s (переработка — в явках, '
              'Task 452)' % exp_b_tal,
              rs['days'].get('Белов Б. Б.') == str(exp_b_tal),
              rs['days'])
        check('E5: чип итого 12ч = %s' % exp_total,
              rs['t12chip'] == str(exp_total), rs)
        page.screenshot(path=os.path.join(SHOTS, '04-talons.png'),
                        full_page=True)

        print('--- F (ЗАЯВКА «печать»): авто-коды в печатном листе ---')
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)
        page.click('#wsPrintBtn')
        page.wait_for_timeout(1800)
        prev = page.evaluate(
            "(function(){var m=document.getElementById("
            "'wsPrintPrevModal');if(!m) return null;"
            "var f=m.querySelector('iframe.wspprev-frame');"
            "return {srcdoc:f?f.srcdoc:''};})()")
        check('F1: предпросмотр печати открыт', bool(prev))
        if prev:
            sd = prev['srcdoc']
            # авто-«д» + ручная «д» Дубова: ячейки с фоном справочника
            dn_cells = sd.count('background:#FFD54F')
            exp_dn = sum(1 for k in (plan or {})
                         if plan[k] == 'д') + 1    # + ручная «д»
            check('F2: ячеек «д» (фон #FFD54F) = %d авто + 1 ручная'
                  % (exp_dn - 1), dn_cells == exp_dn,
                  'found=%s expected=%s' % (dn_cells, exp_dn))
            m = re.search(re.escape('Белов Б. Б.') + r'.*?'
                          r'wsp-tot-over">(\d+)</td>', sd, re.S)
            check('F3: «Перераб./дни» Белова = %d' % exp_b_over,
                  m and m.group(1) == str(exp_b_over),
                  m and m.group(1))
            check('F4: коды «н» (фон #78909C) в листе есть',
                  'background:#78909C' in sd or
                  auto_cnt.get(TAB_B, 0) + auto_cnt.get(TAB_C, 0) +
                  auto_cnt.get(TAB_D, 0) ==
                  sum(1 for k in (plan or {}) if plan[k] == 'д'))
            page.screenshot(path=os.path.join(SHOTS, '05-print-preview.png'))
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        check('F5: Esc закрыл предпросмотр',
              not page.evaluate(
                  "(function(){return !!document.getElementById("
                  "'wsPrintPrevModal');})()"))

        print('--- G: правка «Д» поверх авто — слой по-прежнему уступает ---')
        if plan:
            fk = sorted(plan.keys())[0]
            iso_d, tab_d = fk.split('|')
            page.click('td.ws-cell[onclick*="%s"][onclick*="%s"]'
                       % (iso_d, tab_d))
            page.wait_for_timeout(600)
            page.click("div.ws-popup-row[onclick=\"WorkSchedule."
                       "onPopupStatus('Д')\"]")
            page.wait_for_timeout(700)
            st2 = page.evaluate(GRID_STATE_JS)
            cell2 = page.evaluate(
                "(function(){var td = document.querySelector("
                "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso_d, tab_d) +
                "if (!td) return null;"
                "return {text: td.textContent.trim(),"
                "auto: td.classList.contains('ws-auto-dn'),"
                "pending: td.classList.contains('ws-pending')};})()")
            check('G1: ячейка — ручная «Д» (pending), авто снят',
                  cell2 and cell2['text'] == 'Д' and cell2['pending'] and
                  not cell2['auto'], cell2)
            check('G2: ключа ячейки в _AUTO_DN больше нет',
                  fk not in (st2['plan'] or {}))
            page.screenshot(path=os.path.join(
                SHOTS, '06-manual-over-auto.png'))

        check('H1: 0 JS-ошибок (десктоп)', not js_errors, js_errors[:4])
        ctx.close()

        # ===== зритель (view) =====
        print('=== Контекст: зритель — авто-коды видны как ручные ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'viewer', editor=False)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        st3 = page2.evaluate(GRID_STATE_JS)
        check('I1: зритель: авто-ячейки в DOM есть',
              len(st3['cells']) >= 1, len(st3['cells']))
        check('I2: зритель: у авто-ячеек рамка ручных ws-manual-dn',
              st3['cells'] and all(
                  'ws-manual-dn' in (st3['cls'].get(k) or '')
                  for k in st3['cells']),
              [k for k in st3['cells']
               if 'ws-manual-dn' not in (st3['cls'].get(k) or '')][:3])
        page2.screenshot(path=os.path.join(SHOTS, '07-viewer.png'))
        check('I3: 0 JS-ошибок (зритель)', not js_errors2, js_errors2[:4])
        ctx2.close()

        # ===== мобайл 375 =====
        print('=== Контекст: мобайл 375 — авто-коды + страница итогов ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'dark', 'mobile')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2500)
        st4 = page3.evaluate(GRID_STATE_JS)
        check('J1: мобайл: авто-ячейки в DOM есть',
              len(st4['cells']) >= 1, len(st4['cells']))
        page3.screenshot(path=os.path.join(SHOTS, '08-mobile-grid.png'))
        # мобильная страница итогов (ws-totals): все столбцы
        page3.evaluate("navigateTo('ws-totals')")
        page3.wait_for_timeout(1200)
        tt3 = page3.evaluate(
            "(function(){var out = {};"
            "document.querySelectorAll('.ws-tt-table tbody tr').forEach("
            "function(tr){var f = tr.querySelector('.ws-tt-tabno');"
            "if (!f) return;"
            "var tds = tr.querySelectorAll('td.ws-tt-num');"
            "out[f.textContent.trim()] = tds.length >= 3 ?"
            " tds[2].textContent.trim() : '';});"
            "return out;})()")
        check('J2: мобайл-итоги: Переработка Белова = %d' % exp_b_over,
              tt3.get(TAB_B) == str(exp_b_over), tt3)
        page3.screenshot(path=os.path.join(SHOTS, '09-mobile-totals.png'),
                         full_page=True)
        check('J3: 0 JS-ошибок (мобайл)', not js_errors3, js_errors3[:4])
        ctx3.close()

        browser.close()

    print('\n═══════════════════════════════════════════')
    print('  Task 457 browser-check: %d passed, %d failed'
          % (PASS, FAIL))
    print('═══════════════════════════════════════════')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
