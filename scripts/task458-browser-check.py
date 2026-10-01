#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 458: browser-check — заявка: «Есть замечание, поверх
# авто-«д»/«н» не ставится в ручную код "Выходной, плановый
# выходной день". По сути авто-«д»/«н» должны функционировать в
# приложении и на сервере, в архивах полностью так же, как и
# ручные-«д»/«н»».
# КОНТЕКСТ (мок-сервер, порт 8984, STATEFUL): текущий месяц;
# 4 сменных: 0441 Отпускников (цикл 4 «Д Н В В», «ОТ» весь месяц),
# 0442 Белов / 0443 Чернов (цикл 8), 0444 Дубов (цикл 8, старт +2);
# записи B/C/D — плановые смены; ручная «д» Дубова (эталон);
# справочник — КАНОН Task 387/439 с пустым кодом «Выходной,
# плановый выходной день»; setManualEntry/deleteEntry — пишут в
# стор мока и логируются.
#   A: приложение + сетка, «ОТ» отпускника;
#   B (ЗАЯВКА «как ручные — записи»): материализация — правки
#      _PENDING (кнопка «Сохранить (N)»), DOM-маркеры ws-auto-dn
#      ↔ реестр _AUTO_DN_KEYS 1:1, вид ручных (ws-manual-dn +
#      ws-source-manual + ws-pending + inline-фон + ::before);
#   C (ЗАЯВКА-БАГ «в» поверх авто): попап (подсказка + активная
#      строка) → клик «Выходной, плановый выходной день» → ячейка
#      ПУСТАЯ белая, правка «.», авто-код снят, повторный рендер
#      НЕ возвращает;
#   D (Итоги): Переработка = материализованные д/н + 1 ручная;
#      Явки/Часы не тронуты;
#   E (Талоны): дни явки + 12ч талоны;
#   F (печать): коды в листе + «Перераб./дни»;
#   G (ЗАЯВКА «на сервере»): «Сохранить» → мок setManualEntry ×N
#      (д/н и «.»), записи стали серверными (без ws-pending),
#      кнопка скрыта; «в» поверх СОХРАНЁННОЙ авто → «.» upsert
#      (НЕ deleteEntry);
#   H (архивы/кросс-сессия): reload → реестр из localStorage,
#      «в» поверх сохранённой авто → «.» upsert;
#   I: зритель — сохранённые авто видны КАК РУЧНЫЕ (без маркера
#      реестра), «Сохранить» скрыта, материализации нет;
#   J: мобайл 375; 0 JS-ошибок ×3; скриншоты
#      download/kip8test-task458/.
import calendar
import datetime
import json
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8984
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
DIM = calendar.monthrange(NOWY, NOWM)[1]

TAB_A = '0441'   # Отпускников — цикл 4, отпуск весь месяц
TAB_B = '0442'   # Белов — цикл 8
TAB_C = '0443'   # Чернов — цикл 8
TAB_D = '0444'   # Дубов — цикл 8, старт +2 дня (иная фаза)

SHOTS = '/home/z/my-project/download/kip8test-task458'
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

# справочник КАНОН Task 387/439: «Выходной» — ПУСТОЙ код
CODES = [
  {'code': '', 'name': 'Выходной, плановый выходной день',
   'color': '#FFFFFF', 'short': 'выходной'},
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
            'переработка': 0, 'праздник': 0, 'источник': src,
            'замещает': '', 'комментарий': '', 'часы': None}


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
for d in range(1, DIM + 1):
    dt = datetime.date(NOWY, NOWM, d)
    if planned(dt, EMPLOYEES[3]) == '':
        MANUAL_DN = (dt.isoformat(), TAB_D)
        ENTRIES.append(E(dt.isoformat(), TAB_D, 'д', src='руч'))
        break

# STATEFUL стор мока: setManualEntry/deleteEntry пишут сюда
API_LOG = []          # [{action, date, tab, статус}]


def upsert_entry(date, tab, st):
    for e in ENTRIES:
        if e['дата'] == date and e['таб_номер'] == tab:
            e['статус'] = st
            e['источник'] = 'руч'
            return
    ENTRIES.append(E(date, tab, st, src='руч'))


def delete_entry(date, tab):
    global ENTRIES
    ENTRIES = [e for e in ENTRIES
               if not (e['дата'] == date and e['таб_номер'] == tab)]


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
    if action == 'workSchedule.setManualEntry':
        upsert_entry(body.get('date'), str(body.get('таб_номер')),
                     body.get('статус'))
        API_LOG.append({'action': 'set', 'date': body.get('date'),
                        'tab': str(body.get('таб_номер')),
                        'статус': body.get('статус')})
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.deleteEntry':
        delete_entry(body.get('date'), str(body.get('таб_номер')))
        API_LOG.append({'action': 'del', 'date': body.get('date'),
                        'tab': str(body.get('таб_номер')), 'статус': ''})
        return {'ok': True, 'data': {'ok': True}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t458-%s');" % tag +
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
                      body='not found (t458-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# Снимок модели: реестр месяца, правки (д/н и «.»), DOM-маркеры,
# состояние кнопки «Сохранить»
MODEL_STATE_JS = (
    "(function(){var WS = window.WorkSchedule;"
    "var mk = WS._year + '-' + ((WS._month<10?'0':'') + WS._month);"
    "var reg = (WS._AUTO_DN_KEYS && WS._AUTO_DN_KEYS[mk]) || {};"
    "var pend = WS._PENDING || {};"
    "var pendDn = {}, pendDot = {}, pendSt = {};"
    "Object.keys(pend).forEach(function(k){"
    "var st = pend[k] ? pend[k]['статус'] : '';"
    "pendSt[k] = st;"
    "var t = k.split('|')[1];"
    "if (st==='д'||st==='н') pendDn[t]=(pendDn[t]||0)+1;"
    "if (st==='.') pendDot[t]=(pendDot[t]||0)+1;});"
    "var cells = {};"
    "document.querySelectorAll('td.ws-cell.ws-auto-dn').forEach("
    "function(td){var m=(td.getAttribute('onclick')||'')"
    ".match(/'([^']+)','([^']+)'/);"
    "if(m) cells[m[1]+'|'+m[2]] = (td.textContent||'').trim();});"
    "var btn = document.getElementById('wsSaveBtn');"
    "return {regKeys: Object.keys(reg), pendCount: Object.keys(pend).length,"
    " pendDn: pendDn, pendDot: pendDot, pendSt: pendSt, cells: cells,"
    " saveHidden: btn ? btn.hidden : null,"
    " saveText: btn ? btn.textContent : ''};})()")


def cell_props_js(iso, tab):
    """computed-стили ячейки: фон, outline, ::before-рамка"""
    return (
        "(function(){var td = document.querySelector("
        "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso, tab) +
        "if (!td) return null;"
        "var cs = getComputedStyle(td);"
        "var bf = getComputedStyle(td, '::before');"
        "return {cls: td.className, bg: cs.backgroundColor,"
        " os: cs.outlineStyle, ow: cs.outlineWidth,"
        " bfStyle: bf.borderStyle, bfWidth: bf.borderWidth};})()")


def cell_text_js(iso, tab):
    return (
        "(function(){var td = document.querySelector("
        "\"td.ws-cell[onclick*=\\'%s\\'][onclick*=\\'%s\\']\");" % (iso, tab) +
        "return td ? {text: (td.textContent||'').trim(),"
        " cls: td.className} : null;})()")


def pick_auto_keys(st, n):
    """первые n живых авто-ключей (сортировка по дате)"""
    keys = sorted([k for k in st['regKeys'] if k in st['cells']],
                  key=lambda k: (k.split('|')[0], k.split('|')[1]))
    return keys[:n]


def main():
    srv = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 светлая, Админ (edit) =====
        print('=== Контекст: десктоп светлая — материализация, '
              '«в» поверх авто, отчёты, сохранение ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'light', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        print('--- A: сетка открыта, материализация авто-«д»/«н» ---')
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
        st = page.evaluate(MODEL_STATE_JS)
        check('A4: ЗАЯВКА «записи»: план материализован в правки '
              '_PENDING (>= 3 авто-кодов)', st['pendCount'] >= 3,
              st['pendCount'])
        check('A5: кнопка «Сохранить (%d)» видна' % st['pendCount'],
              st['saveHidden'] is False and
              ('%d' % st['pendCount']) in (st['saveText'] or ''),
              st['saveText'])

        print('--- B (ЗАЯВКА «как ручные — записи»): DOM ↔ реестр ↔ правки ---')
        check('B1: реестр месяца не пуст', len(st['regKeys']) >= 3,
              st['regKeys'])
        dom_keys = set(st['cells'].keys())
        reg_keys = set(st['regKeys'])
        check('B2: DOM ws-auto-dn ↔ реестр _AUTO_DN_KEYS 1:1',
              dom_keys == reg_keys,
              'dom=%s reg=%s' % (len(dom_keys), len(reg_keys)))
        pend_dn_keys = set(k for k, v in st['pendSt'].items()
                           if v in ('д', 'н'))
        check('B3: правки д/н ↔ реестр 1:1 (материализация)',
              pend_dn_keys == reg_keys,
              'diff=%s' % list(pend_dn_keys ^ reg_keys)[:4])
        bad_txt = [k for k in st['cells']
                   if st['cells'].get(k) != st['pendSt'].get(k)]
        check('B4: текст DOM-ячейки == код правки («д»/«н»)',
              not bad_txt, bad_txt[:4])
        # вид ручной записи у первой авто-ячейки
        fk = pick_auto_keys(st, 1)
        if fk:
            fk = fk[0]
            iso_fk, tab_fk = fk.split('|')
            pr = page.evaluate(cell_props_js(iso_fk, tab_fk))
            check('B5: авто-ячейка: ws-manual-dn + ws-source-manual + '
                  'ws-pending + ws-auto-dn',
                  pr and 'ws-manual-dn' in pr['cls'] and
                  'ws-source-manual' in pr['cls'] and
                  'ws-pending' in pr['cls'] and 'ws-auto-dn' in pr['cls'],
                  pr and pr['cls'])
            check('B6: янтарный пунктир ws-pending (правка!) + ::before-рамка '
                  'ручных д/н',
                  pr and pr['os'] == 'dashed' and pr['ow'] == '2px' and
                  pr['bfStyle'] == 'solid' and
                  pr['bfWidth'] not in ('0px', ''), pr)
            mr = page.evaluate(cell_props_js(MANUAL_DN[0], MANUAL_DN[1]))
            check('B7: ручная «д» Дубова — эталон: БЕЗ ws-auto-dn/'
                  'ws-pending',
                  mr and 'ws-manual-dn' in mr['cls'] and
                  'ws-auto-dn' not in mr['cls'] and
                  'ws-pending' not in mr['cls'], mr and mr['cls'])
            check('B8: фон авто == фон ручной «д» (справочник)',
                  pr and mr and pr['bg'] == mr['bg'] or
                  (pr and page.evaluate(
                      "(function(){var meta = WorkSchedule._statusMeta('%s');"
                      "return !!meta && !!meta.color;})()" % st['cells'][fk])),
                  '%s / %s' % (pr and pr['bg'], mr and mr['bg']))
        page.screenshot(path=os.path.join(SHOTS, '01-desktop-grid.png'))

        print('--- C (ЗАЯВКА-БАГ): «Выходной» поверх авто-«д»/«н» ---')
        if fk:
            iso_c, tab_c = fk.split('|')
            code_c = st['cells'][fk]
            page.click('td.ws-cell[onclick*="%s"][onclick*="%s"]'
                       % (iso_c, tab_c))
            page.wait_for_timeout(600)
            auto_line = page.evaluate(
                "(function(){var e = document.querySelector("
                "'.ws-popup-auto');"
                "return e ? e.textContent.trim() : null;})()")
            check('C1: подсказка «Авто: «%s» … (замещение отпуска; правка — '
                  'как у ручной записи)»' % code_c,
                  auto_line and 'Авто' in auto_line and
                  code_c in auto_line and
                  'замещение отпуска' in auto_line and
                  'правка — как у ручной записи' in auto_line,
                  auto_line)
            active = page.evaluate(
                "(function(){var rows = document.querySelectorAll("
                "'.ws-popup-row');"
                "for (var i = 0; i < rows.length; i++) {"
                "var oc = rows[i].getAttribute('onclick') || '';"
                "if (oc.indexOf(\"onPopupStatus('%s')\") !== -1)" % code_c +
                " return rows[i].className;}"
                "return null;})()")
            check('C2: строка «%s» в попапе АКТИВНА (ws-popup-active)'
                  % code_c,
                  active and 'ws-popup-active' in active, active)
            page.screenshot(path=os.path.join(SHOTS, '02-popup.png'))
            # ВЫХОДНОЙ (пустой код) поверх авто — БАГ заявки
            page.click(
                ".ws-popup-row[onclick=\"WorkSchedule."
                "onPopupStatus('')\"]")
            page.wait_for_timeout(800)
            tc = page.evaluate(cell_text_js(iso_c, tab_c))
            check('C3: БАГ ЗАКРЫТ: код «в» поставлен — ячейка ПУСТАЯ '
                  'белая (ws-dot-code, без «%s»)' % code_c,
                  tc and tc['text'] == '' and
                  'ws-dot-code' in tc['cls'] and
                  code_c not in (tc['text'] or ''), tc)
            check('C4: авто-маркер снят (ws-auto-dn нет)',
                  tc and 'ws-auto-dn' not in tc['cls'], tc and tc['cls'])
            st2 = page.evaluate(MODEL_STATE_JS)
            check('C5: правка ячейки — «.» (надгробие, как авто-записи '
                  'Task 453)',
                  st2['pendSt'].get(fk) == '.', st2['pendSt'].get(fk))
            check('C6: ключ снят из реестра (повторной расстановки не '
                  'будет)', fk not in st2['regKeys'], fk)
            # повторный рендер не возвращает авто-код
            page.evaluate("(function(){WorkSchedule._renderGrid();})()")
            page.wait_for_timeout(600)
            tc2 = page.evaluate(cell_text_js(iso_c, tab_c))
            check('C7: повторный _renderGrid НЕ вернул авто-«%s»'
                  % code_c,
                  tc2 and tc2['text'] == '' and
                  'ws-dot-code' in tc2['cls'], tc2)
            page.screenshot(path=os.path.join(SHOTS, '03-vykhodnoy.png'))

        print('--- D (Итоги): переработка = материализованные д/н ---')
        st = page.evaluate(MODEL_STATE_JS)
        auto_b = st['pendDn'].get(TAB_B, 0)
        auto_c = st['pendDn'].get(TAB_C, 0)
        auto_d = st['pendDn'].get(TAB_D, 0)
        shifts_b = sum(1 for d in range(1, DIM + 1)
                       if planned(datetime.date(NOWY, NOWM, d),
                                  EMPLOYEES[1]) in ('Д', 'Н'))
        shifts_c = sum(1 for d in range(1, DIM + 1)
                       if planned(datetime.date(NOWY, NOWM, d),
                                  EMPLOYEES[2]) in ('Д', 'Н'))
        shifts_d = sum(1 for d in range(1, DIM + 1)
                       if planned(datetime.date(NOWY, NOWM, d),
                                  EMPLOYEES[3]) in ('Д', 'Н'))
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
        check('D1: шторка итогов: таблица с работниками', bool(tt), tt)
        check('D2: Белов: Переработка (дни) = %d материализованных'
              % auto_b,
              tt.get(TAB_B, {}).get('over') == str(auto_b),
              tt.get(TAB_B))
        check('D3: Белов: title «часов переработки: %s»'
              % str(12 * auto_b),
              ('часов переработки: %s' % (12 * auto_b))
              in tt.get(TAB_B, {}).get('overTitle', ''),
              tt.get(TAB_B, {}).get('overTitle'))
        check('D4: Дубов: Переработка = %d авто + 1 ручная «д»'
              % auto_d,
              tt.get(TAB_D, {}).get('over') == str(auto_d + 1),
              tt.get(TAB_D))
        check('D5: Белов: Явки = %d смен (д/н — не явка)'
              % shifts_b,
              tt.get(TAB_B, {}).get('work') == str(shifts_b),
              tt.get(TAB_B))
        check('D6: Белов: Часы = %s (не тронуты)' % str(12 * shifts_b),
              tt.get(TAB_B, {}).get('hours') == str(12 * shifts_b),
              tt.get(TAB_B))
        check('D7: надгробие «.» НЕ в переработке (Дубов/Белов без '
              'лишних дней)',
              tt.get(TAB_B, {}).get('over') == str(auto_b) and
              tt.get(TAB_D, {}).get('over') == str(auto_d + 1))
        page.screenshot(path=os.path.join(SHOTS, '04-totals.png'))
        page.click('#wsTotalsBtn')
        page.wait_for_timeout(600)

        print('--- E (Талоны): дни явки + 12-часовые талоны ---')
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
        exp_b_tal = shifts_b + auto_b
        exp_c_tal = shifts_c + auto_c
        exp_d_tal = shifts_d + auto_d + 1     # + ручная «д»
        check('E1: Белов: 12ч талонов = %d смен + %d авто = %s'
              % (shifts_b, auto_b, exp_b_tal),
              rs['b12'] == str(exp_b_tal), rs)
        check('E2: Дубов: 12ч = %d смен + %d авто + 1 ручная = %s'
              % (shifts_d, auto_d, exp_d_tal),
              rs['d12'] == str(exp_d_tal), rs)
        check('E3: Чернов: 12ч = %s' % exp_c_tal,
              rs['c12'] == str(exp_c_tal), rs)
        check('E4: «Дней явки» Белова = %s (д/н — день явки, Task 452)'
              % exp_b_tal,
              rs['days'].get('Белов Б. Б.') == str(exp_b_tal), rs['days'])
        check('E5: чип итого 12ч = %s'
              % (exp_b_tal + exp_c_tal + exp_d_tal),
              rs['t12chip'] == str(exp_b_tal + exp_c_tal + exp_d_tal),
              rs)
        page.screenshot(path=os.path.join(SHOTS, '05-talons.png'),
                        full_page=True)

        print('--- F (печать): материализованные коды в листе ---')
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
            stp = page.evaluate(MODEL_STATE_JS)
            pend_d = sum(1 for v in stp['pendSt'].values() if v == 'д')
            pend_n = sum(1 for v in stp['pendSt'].values() if v == 'н')
            dn_cells = sd.count('background:#FFD54F')
            exp_d_cells = pend_d + 1     # + ручная «д» Дубова
            check('F2: ячеек «д» (фон #FFD54F) = %d правок + 1 ручная'
                  % pend_d, dn_cells == exp_d_cells,
                  'found=%s expected=%s' % (dn_cells, exp_d_cells))
            check('F3: ячеек «н» (фон #78909C) = %d правок' % pend_n,
                  sd.count('background:#78909C') == pend_n,
                  'found=%s expected=%s'
                  % (sd.count('background:#78909C'), pend_n))
            m = re.search(re.escape('Белов Б. Б.') + r'.*?'
                          r'wsp-tot-over">(\d+)</td>', sd, re.S)
            check('F4: «Перераб./дни» Белова = %d' % auto_b,
                  m and m.group(1) == str(auto_b), m and m.group(1))
            page.screenshot(path=os.path.join(SHOTS, '06-print.png'))
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)

        print('--- G (ЗАЯВКА «на сервере»): Сохранить → записи сервера ---')
        stg = page.evaluate(MODEL_STATE_JS)
        n_before = stg['pendCount']
        n_dn = sum(stg['pendDn'].values())
        n_dot = sum(stg['pendDot'].values())
        check('G0: к сохранению %d правок (%d д/н + %d «.»)'
              % (n_before, n_dn, n_dot),
              n_before == n_dn + n_dot and n_dn >= 2 and n_dot == 1,
              stg['pendSt'])
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1200)
        page.click('#wsSaveBtn')
        page.wait_for_timeout(4000)
        stg2 = page.evaluate(MODEL_STATE_JS)
        sets = [x for x in API_LOG if x['action'] == 'set']
        check('G1: мок получил setManualEntry × %d (все правки — как '
              'ручные)' % n_before, len(sets) == n_before,
              '%s / ожидалось %s' % (len(sets), n_before))
        bad_st = [x for x in sets
                  if x['статус'] not in ('д', 'н', '.')]
        check('G2: статусы сохранённых — только д/н и «.»-надгробие',
              not bad_st, bad_st[:4])
        st_sets = [x for x in sets if x['статус'] in ('д', 'н')]
        check('G3: из них д/н = %d (материализация)' % n_dn,
              len(st_sets) == n_dn,
              '%s / %s' % (len(st_sets), n_dn))
        check('G4: _PENDING пуст (всё отправлено), кнопка «Сохранить» '
              'скрыта',
              stg2['pendCount'] == 0 and stg2['saveHidden'] is True,
              stg2)
        # записи стали серверными: ячейка авто без ws-pending, с маркером
        if st_sets:
            k0 = '%s|%s' % (st_sets[0]['date'], st_sets[0]['tab'])
            iso_g, tab_g = k0.split('|')
            tp = page.evaluate(cell_text_js(iso_g, tab_g))
            pr = page.evaluate(cell_props_js(iso_g, tab_g))
            check('G5: сохранённая авто-ячейка: серверная запись '
                  '(ws-manual-dn + ws-source-manual + ws-auto-dn, '
                  'БЕЗ ws-pending)',
                  tp and tp['text'] in ('д', 'н') and pr and
                  'ws-manual-dn' in pr['cls'] and
                  'ws-source-manual' in pr['cls'] and
                  'ws-auto-dn' in pr['cls'] and
                  'ws-pending' not in pr['cls'], pr and pr['cls'])
            page.screenshot(path=os.path.join(SHOTS, '07-saved.png'))
        # «в» поверх СОХРАНЁННОЙ авто-записи (реестр жив) — upsert «.»
        stg3 = page.evaluate(MODEL_STATE_JS)
        gk = pick_auto_keys(stg3, 2)
        check('G6: живых сохранённых авто-ключей >= 2 для сценариев '
              'G/H', len(gk) >= 2, gk)
        if len(gk) >= 2:
            iso_g2, tab_g2 = gk[1].split('|')
            del_before = len([x for x in API_LOG if x['action'] == 'del'])
            page.click('td.ws-cell[onclick*="%s"][onclick*="%s"]'
                       % (iso_g2, tab_g2))
            page.wait_for_timeout(600)
            page.click(
                ".ws-popup-row[onclick=\"WorkSchedule."
                "onPopupStatus('')\"]")
            page.wait_for_timeout(800)
            stg4 = page.evaluate(MODEL_STATE_JS)
            check('G7: «в» поверх СОХРАНЁННОЙ авто → правка «.» '
                  '(НЕ __delete)',
                  stg4['pendSt'].get(gk[1]) == '.',
                  stg4['pendSt'].get(gk[1]))
            page.evaluate("navigateTo('work-schedule')")
            page.wait_for_timeout(1000)
            n_before_g7 = len([x for x in API_LOG if x['action'] == 'set'])
            page.click('#wsSaveBtn')
            page.wait_for_timeout(3500)
            del_after = len([x for x in API_LOG if x['action'] == 'del'])
            g7_sets = [x for x in API_LOG if x['action'] == 'set'][n_before_g7:]
            tomb = [x for x in g7_sets
                    if x['date'] == gk[1].split('|')[0] and
                    x['статус'] == '.']
            check('G8: надгробие сохранено upsert-ом «.» '
                  '(setManualEntry), deleteEntry НЕ вызывался; доп. '
                  'правки — только д/н (повторное замещение смены '
                  'отпускника, заявка 456)',
                  len(tomb) == 1 and
                  del_after == del_before and
                  all(x['статус'] in ('д', 'н', '.') for x in g7_sets),
                  'sets=%s del=%s/%s' % (g7_sets, del_before, del_after))
            tp = page.evaluate(cell_text_js(iso_g2, tab_g2))
            check('G9: ячейка после «в» — пустая белая (надгробие)',
                  tp and tp['text'] == '' and 'ws-dot-code' in tp['cls'],
                  tp)
        check('G10: 0 JS-ошибок (десктоп)', not js_errors, js_errors[:4])

        # ===== reload: реестр из localStorage (кросс-сессия) =====
        print('--- H (архивы/кросс-сессия): reload → реестр жив ---')
        page.reload()
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        sth = page.evaluate(MODEL_STATE_JS)
        check('H1: после reload правок нет (записи на сервере)',
              sth['pendCount'] == 0 and sth['saveHidden'] is True, sth)
        check('H2: реестр восстановлен из localStorage '
              '(ws-auto-dn ячейки живы)',
              len(sth['cells']) >= 1 and
              set(sth['cells'].keys()) == set(sth['regKeys']),
              'dom=%s reg=%s' % (len(sth['cells']), len(sth['regKeys'])))
        hk = pick_auto_keys(sth, 1)
        if hk:
            iso_h, tab_h = hk[0].split('|')
            page.click('td.ws-cell[onclick*="%s"][onclick*="%s"]'
                       % (iso_h, tab_h))
            page.wait_for_timeout(600)
            page.click(
                ".ws-popup-row[onclick=\"WorkSchedule."
                "onPopupStatus('')\"]")
            page.wait_for_timeout(800)
            sth2 = page.evaluate(MODEL_STATE_JS)
            check('H3: «в» поверх сохранённой авто после reload → '
                  'правка «.» (реестр из localStorage)',
                  sth2['pendSt'].get(hk[0]) == '.',
                  sth2['pendSt'].get(hk[0]))
            page.evaluate("navigateTo('work-schedule')")
            page.wait_for_timeout(1000)
            page.click('#wsSaveBtn')
            page.wait_for_timeout(3500)
            last_h = [x for x in API_LOG if x['action'] == 'set'][-1]
            check('H4: сохранено «.» upsert-ом (setManualEntry)',
                  last_h['статус'] == '.' and
                  last_h['date'] == iso_h, last_h)
        ctx.close()

        # ===== зритель (view): сохранённые авто — как ручные =====
        print('=== Контекст: зритель — сохранённые авто как ручные ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'viewer', editor=False)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        stv = page2.evaluate(MODEL_STATE_JS)
        check('I1: зритель: сохранённые авто-«д»/«н» видны (записи '
              'сервера)',
              sum(stv['pendDn'].values()) == 0 and
              len(stv['cells']) == 0 and
              page2.evaluate(
                  "(function(){var n=0;"
                  "document.querySelectorAll("
                  "'td.ws-cell.ws-manual-dn.ws-source-manual')"
                  ".forEach(function(td){"
                  "var t=(td.textContent||'').trim();"
                  "if(t==='д'||t==='н') n++;});return n;})()") >= 1,
              stv)
        check('I2: зритель: материализации НЕТ (правок 0, кнопка '
              '«Сохранить» скрыта)',
              stv['pendCount'] == 0 and stv['saveHidden'] is True, stv)
        mr2 = page2.evaluate(cell_props_js(MANUAL_DN[0], MANUAL_DN[1]))
        check('I3: ручная «д» Дубова на месте (эталон)', bool(mr2))
        page2.screenshot(path=os.path.join(SHOTS, '08-viewer.png'))
        check('I4: 0 JS-ошибок (зритель)', not js_errors2, js_errors2[:4])
        ctx2.close()

        # ===== мобайл 375 =====
        print('=== Контекст: мобайл 375 — сетка + итоги ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'dark', 'mobile')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2500)
        check('J1: мобайл: сетка рендерится',
              page3.evaluate(
                  "(function(){return !!document.querySelector("
                  "'.ws-grid');})()"))
        dn_m = page3.evaluate(
            "(function(){var n=0;"
            "document.querySelectorAll('td.ws-cell')"
            ".forEach(function(td){"
            "var t=(td.textContent||'').trim();"
            "if(t==='д'||t==='н') n++;});return n;})()")
        check('J2: мобайл: авто-«д»/«н» записи видны (>= %d)' % 2,
              dn_m >= 2, dn_m)
        page3.screenshot(path=os.path.join(SHOTS, '09-mobile-grid.png'))
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
        # ожидание — по ФИНАЛЬНОМУ состоянию стора мока (повторные
        # замещения G8/H могли добавить/перенести коды)
        exp_b_final = sum(1 for e in ENTRIES
                          if e['таб_номер'] == TAB_B and
                          e['статус'] in ('д', 'н'))
        check('J3: мобайл-итоги: Переработка Белова = %d (по записям '
              'сервера)' % exp_b_final,
              tt3.get(TAB_B) == str(exp_b_final), tt3)
        page3.screenshot(path=os.path.join(SHOTS, '10-mobile-totals.png'),
                         full_page=True)
        check('J4: 0 JS-ошибок (мобайл)', not js_errors3, js_errors3[:4])
        ctx3.close()

        browser.close()

    print('\n═══════════════════════════════════════════')
    print('  Task 458 browser-check: %d passed, %d failed'
          % (PASS, FAIL))
    print('═══════════════════════════════════════════')
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
