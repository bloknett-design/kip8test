#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 534 browser-check: LCD-информер Табеля — заявка:
# «Погода не работает "Источники не дали данных (прямой запрос:
#  Failed to fetch); сервер: meteoinfo:exception:У вас нет
#  разрешения на вызов функции "UrlFetchApp.fetch". Т; open-meteo:
#  exception:…". В календаре, кнопки с годом выравняй по левому
#  краю, надписи "Год" и "Месяц" убери, шрифт в кнопках месяца
#  сделай немного меньше чем в годе.»:
#  A) КАЛЕНДАРЬ: подписей «Год»/«Месяц» НЕТ (DOM и CSS); строки
#     года И месяца — ПО ЛЕВОМУ КРАЮ (justify-content: flex-start +
#     геометрия: левый край ‹ = левому краю сетки дней); шрифт
#     строки месяца мельче года (селект 12<13, стрелки 15<16,
#     «Сегодня» 12<13); навигация цела (‹ год, селект месяца,
#     декабрь→январь, «Сегодня»).
#  B) ПОГОДА — ДВА прямых канала: open-meteo ok → wttr.in НЕ звётся;
#     open-meteo сбой → wttr.in ok («wttr.in (напрямую из
#     браузера)», сервер НЕ звётся, экран −2°); оба сбой → сервер
#     («через Apps Script», −12°); оба сбой + сервер diag «нет
#     разрешения UrlFetchApp» → подсказка authorizeWeather() +
#     dnote с ОБЕИМИ каналами; «Обновить сейчас» переспрашивает.
#  C) 1024 светлая тема — попапы в пределах вьюпорта; 0 JS-ошибок.
import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task534')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# режимы погоды: прямые каналы + сервер (Apps Script)
OM_MODE = ['ok']            # ok | fail
WT_MODE = ['ok']            # ok | fail
WEATHER_MODE = ['ok']       # ok | empty | perm | unknown
OM_CALLS = []               # счётчик open-meteo
WT_CALLS = []               # счётчик wttr.in
SERVER_W_CALLS = []         # счётчик серверных getWeather


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


# --- Данные мока (как в task531/532/533) ---
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': '2026-10-01',
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
_T = _dt.date.today()
_ISO = lambda d: d.strftime('%Y-%m-%d')
TRAININGS = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': 'Охрана труда', 'дата_начала': _ISO(_T),
   'дата_окончания': _ISO(_T), 'длительность_дней': 1, 'комментарий': ''},
]
VACATIONS = [
  {'id': 1, 'таб_номер': '017', 'дата_начала': _ISO(_T - _dt.timedelta(days=3)),
   'дата_окончания': _ISO(_T + _dt.timedelta(days=11)),
   'часть': 1, 'комментарий': ''},
]
WEATHER_OK = {'temp': -12, 'phenomenon': 'Слабый снег', 'cloud': 8,
              'wind': 4, 'windDir': 'северо-западный', 'pressure': 759,
              'humidity': 86.2, 'obsLocal': '15 октября, 13:00',
              'source': 'meteoinfo.ru', 'fetched': '2026-10-15T13:10:00Z',
              'diag': 'meteoinfo:http_200'}
_PERM_MSG = ('meteoinfo:exception:У вас нет разрешения на вызов функции ' +
             '"UrlFetchApp.fetch". Т; open-meteo:exception:У вас нет ' +
             'разрешения на вызов функции "UrlFetchApp.fetch". Т.')
WEATHER_EMPTY = {'temp': None, 'phenomenon': None, 'cloud': None, 'wind': None,
                 'windDir': None, 'pressure': None, 'humidity': None,
                 'obsLocal': None, 'source': None,
                 'note': 'weather_unavailable',
                 'diag': 'meteoinfo:http_403; open-meteo:http_503',
                 'fetched': '2026-10-15T13:10:00Z'}
WEATHER_PERM = dict(WEATHER_EMPTY, diag=_PERM_MSG)

# прямой ответ open-meteo (как OM_JSON в тестах): −1.6°C, код 3
OM_JSON = json.dumps({
    'latitude': 55.36, 'longitude': 86.02, 'timezone': 'Asia/Novokuznetsk',
    'current_units': {},
    'current': {
        'time': '2026-10-16T07:00', 'interval': 900,
        'temperature_2m': -1.6, 'relative_humidity_2m': 73,
        'surface_pressure': 1018.1, 'weather_code': 3,
        'wind_speed_10m': 2.55, 'wind_direction_10m': 271
    }
}, ensure_ascii=False)

# прямой ответ wttr.in (format=j1&lang=ru — реальный формат): −2°C
WTTR_JSON = json.dumps({
    'current_condition': [{
        'temp_C': '-2', 'FeelsLikeC': '-6', 'cloudcover': '100',
        'humidity': '83', 'observation_time': '01:51 AM',
        'pressure': '1035', 'weatherDesc': [{'value': 'Overcast '}],
        'lang_ru': [{'value': 'Пасмурно'}],
        'winddirDegree': '253', 'windspeedKmph': '11'
    }]
}, ensure_ascii=False)


def mock_response(action):
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
                'instrList': [], 'instrAll': TRAININGS, 'eventsAll': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    if action == 'workSchedule.getWeather':
        if WEATHER_MODE[0] == 'empty':
            return {'ok': True, 'data': WEATHER_EMPTY}
        if WEATHER_MODE[0] == 'perm':
            return {'ok': True, 'data': WEATHER_PERM}
        if WEATHER_MODE[0] == 'unknown':
            return {'ok': False,
                    'error': 'Unknown action: workSchedule.getWeather'}
        return {'ok': True, 'data': WEATHER_OK}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# --- JS-побы ---

# календарь Task 534: подписей нет, левый край, шрифты, навигация
CAL534_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    if (!cal || cal.hidden) return {missing: true};
    const yearRow = cal.querySelector('.ws-lcd-cal-year');
    const monthRow = cal.querySelector('.ws-lcd-cal-month');
    const ysel = yearRow ? yearRow.querySelector('select') : null;
    const msel = monthRow ? monthRow.querySelector('select') : null;
    const ynav = yearRow ? yearRow.querySelector('.ws-lcd-cal-nav') : null;
    const mnav = monthRow ? monthRow.querySelector('.ws-lcd-cal-nav') : null;
    const todayBtn = monthRow ? monthRow.querySelector('.ws-lcd-cal-today') : null;
    const grid = cal.querySelector('.ws-lcd-cal-grid');
    const px = el => el ? parseFloat(getComputedStyle(el).fontSize) : null;
    const gr = grid ? grid.getBoundingClientRect() : null;
    const yb = yearRow ? yearRow.querySelector('button') : null;
    const mb = monthRow ? monthRow.querySelector('button') : null;
    return {
        labels: cal.querySelectorAll(
            '.ws-lcd-cal-yearlbl, .ws-lcd-cal-monthlbl').length,
        yearJustify: yearRow ? getComputedStyle(yearRow).justifyContent : null,
        monthJustify: monthRow ? getComputedStyle(monthRow).justifyContent : null,
        yearSelFont: px(ysel), monthSelFont: px(msel),
        yearNavFont: px(ynav), monthNavFont: px(mnav),
        todayFont: px(todayBtn),
        // геометрия: левый край ‹ строки == левому краю сетки дней
        yearLeftAtGrid: !!(yb && gr &&
            Math.abs(yb.getBoundingClientRect().left - gr.left) <= 2),
        monthLeftAtGrid: !!(mb && gr &&
            Math.abs(mb.getBoundingClientRect().left - gr.left) <= 2),
        todayInMonthRow: !!todayBtn,
        monthOptCount: msel ? msel.options.length : 0,
        calY: window.WsLcdClock ? window.WsLcdClock._calY : null,
        calM: window.WsLcdClock ? window.WsLcdClock._calM : null,
        curY: new Date().getFullYear(),
        curM: new Date().getMonth() + 1};})"""

# экран: температура + зона погоды непуста
SCREEN_JS = r"""(() => {
    const WsL = window.WsLcdClock;
    if (!WsL) return {missing: true};
    const w = WsL._weather;
    let wx = 0;
    for (let r = 4; r <= 13; r++) for (let c = 170; c <= 204; c++)
        wx += (WsL._grid ? WsL._grid[r][c] : 0);
    return {tempTxt: w ? w.tempTxt : null, icon: w ? w.icon : null,
            weatherZone: wx,
            diag: WsL._weatherDiag ? {
                ok: WsL._weatherDiag.ok, via: WsL._weatherDiag.via,
                source: WsL._weatherDiag.source} : null};})"""

# панель настроек: статус погоды
WSTAT_JS = r"""(() => {
    const set = document.getElementById('wsLcdSet');
    if (!set || set.hidden) return {missing: true};
    const st = set.querySelector('.ws-lcd-set-wstat');
    const btn = set.querySelector('.ws-lcd-set-wbtn');
    return {text: st ? st.textContent.trim() : '',
            cls: st ? st.className : '',
            hasBtn: !!btn,
            btnText: btn ? btn.textContent.trim() : ''};})"""

# попапы: видимость/геометрия
POPUP_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    const set = document.getElementById('wsLcdSet');
    if (!cal || !set) return {missing: true};
    const c = cal.getBoundingClientRect(), s = set.getBoundingClientRect();
    return {calHidden: cal.hidden, setHidden: set.hidden,
            calVis: getComputedStyle(cal).display,
            setVis: getComputedStyle(set).display,
            gap: c.left - s.right,
            insideViewport: s.left >= 0 && c.left >= 0 && c.right <= innerWidth};})"""


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        def make_ctx(theme, w, h, dpr=1.0):
            ctx = browser.new_context(viewport={'width': w, 'height': h},
                                      device_scale_factor=dpr)
            ctx.add_init_script(
                "try{localStorage.clear()}catch(e){};" +
                "localStorage.setItem('kip8test:kip8_session_token','bc-t534');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            # прямой канал 1: open-meteo.com (Task 533)
            def om_handle(route):
                OM_CALLS.append(1)
                if OM_MODE[0] == 'fail':
                    route.fulfill(status=503, content_type='text/plain',
                                  body='om down')
                else:
                    route.fulfill(status=200,
                                  content_type='application/json; charset=utf-8',
                                  body=OM_JSON)
            ctx.route('**api.open-meteo.com/**', om_handle)

            # прямой канал 2: wttr.in (Task 534)
            def wt_handle(route):
                WT_CALLS.append(1)
                if WT_MODE[0] == 'fail':
                    route.fulfill(status=502, content_type='text/plain',
                                  body='wttr down')
                else:
                    route.fulfill(status=200,
                                  content_type='text/plain; charset=utf-8',
                                  body=WTTR_JSON)
            ctx.route('**wttr.in/**', wt_handle)

            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
                if action == 'workSchedule.getWeather':
                    SERVER_W_CALLS.append(1)   # счётчик серверных вызовов
                route.fulfill(status=200,
                              content_type='application/json; charset=utf-8',
                              body=json.dumps(mock_response(action),
                                              ensure_ascii=False))
            ctx.route('**/exec?**', handle)
            ctx.route('**script.google.com/**', handle)
            ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            return ctx

        # ==============================================================
        print('== A: КАЛЕНДАРЬ — без подписей, по левому краю, шрифт месяца мельче ==')
        OM_MODE[0] = 'ok'
        WT_MODE[0] = 'ok'
        WEATHER_MODE[0] = 'ok'
        ctx = make_ctx('dark', 1280, 720, dpr=2.0)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1200)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        page.click('#wsLcdClock')             # открыть календарь
        page.wait_for_timeout(300)
        cy = page.evaluate(CAL534_JS)
        check('A: подписей «Год»/«Месяц» в DOM НЕТ',
              (cy.get('labels') or 0) == 0, cy)
        check('A: строка года — justify-content: flex-start',
              cy.get('yearJustify') == 'flex-start', cy)
        check('A: строка месяца — justify-content: flex-start',
              cy.get('monthJustify') == 'flex-start', cy)
        check('A: геометрия — ‹ года у ЛЕВОГО края сетки дней',
              cy.get('yearLeftAtGrid'), cy)
        check('A: геометрия — ‹ месяца у ЛЕВОГО края сетки дней',
              cy.get('monthLeftAtGrid'), cy)
        check('A: селект месяца 12px < селекта года 13px',
              (cy.get('monthSelFont') or 0) == 12 and
              (cy.get('yearSelFont') or 0) == 13, cy)
        check('A: стрелки месяца 15px < стрелок года 16px',
              (cy.get('monthNavFont') or 0) == 15 and
              (cy.get('yearNavFont') or 0) == 16, cy)
        check('A: «Сегодня» в строке месяца — 12px',
              (cy.get('todayFont') or 0) == 12 and cy.get('todayInMonthRow'), cy)
        shot(page, '01-calendar-left-no-labels.png')

        # навигация цела: ‹ год
        y0 = int(cy.get('curY'))
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        check('A: 4 кнопки навигации (2 года + 2 месяца)', len(navs) == 4,
              len(navs))
        navs[0].click()          # ‹ год
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL534_JS)
        check('A: ‹ года уменьшил год (календарь жив)',
              cy.get('calY') == y0 - 1, cy)

        # селект месяца применяет месяц
        page.select_option('#wsLcdCal .ws-lcd-cal-month select', '3')
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL534_JS)
        check('A: селект месяца — Март применён', cy.get('calM') == 3, cy)

        # декабрь → январь переносит год
        page.evaluate("window.WsLcdClock._calY=%d; window.WsLcdClock._calM=12;"
                      " window.WsLcdClock._renderCal()" % y0)
        page.wait_for_timeout(150)
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        navs[3].click()          # › месяц: декабрь → январь
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL534_JS)
        check('A: декабрь→январь — год перенёсся',
              cy.get('calY') == y0 + 1 and cy.get('calM') == 1, cy)

        # «Сегодня»
        page.click('#wsLcdCal .ws-lcd-cal-today')
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL534_JS)
        check('A: «Сегодня» — текущие месяц и год',
              cy.get('calY') == cy.get('curY') and cy.get('calM') == cy.get('curM'),
              cy)
        shot(page, '02-calendar-today.png')

        # ==============================================================
        print('== B: ПОГОДА — два прямых канала (open-meteo → wttr.in → сервер) ==')
        # B1: успех open-meteo — wttr.in и сервер НЕ зовутся
        srv_before = len(SERVER_W_CALLS)
        page.click('#wsLcdGear')
        page.wait_for_timeout(400)
        ws = page.evaluate(WSTAT_JS)
        check('B1: «Есть данные» — канал open-meteo «напрямую из браузера»',
              'Есть данные' in (ws.get('text') or '') and
              'open-meteo.com (напрямую из браузера)' in (ws.get('text') or ''), ws)
        check('B1: wttr.in НЕ звался (успех первым каналом)',
              len(WT_CALLS) == 0, len(WT_CALLS))
        check('B1: сервер Apps Script погоду НЕ запрашивал',
              len(SERVER_W_CALLS) == srv_before,
              (srv_before, len(SERVER_W_CALLS)))
        sc = page.evaluate(SCREEN_JS)
        check('B1: экран показывает −2° (данные open-meteo)',
              sc.get('tempTxt') == '-2°', sc)
        shot(page, '03-weather-om-direct.png')

        # B2: open-meteo сбой → wttr.in успех (сервер НЕ звётся)
        OM_MODE[0] = 'fail'
        om_before, wt_before = len(OM_CALLS), len(WT_CALLS)
        page.click('#wsLcdSet .ws-lcd-set-wbtn')     # «Обновить сейчас»
        page.wait_for_timeout(700)
        check('B2: open-meteo пробован (сбой)',
              len(OM_CALLS) > om_before, (om_before, len(OM_CALLS)))
        check('B2: wttr.in подключился вторым',
              len(WT_CALLS) > wt_before, (wt_before, len(WT_CALLS)))
        ws = page.evaluate(WSTAT_JS)
        check('B2: статус — «wttr.in (напрямую из браузера)»',
              'Есть данные' in (ws.get('text') or '') and
              'wttr.in (напрямую из браузера)' in (ws.get('text') or ''), ws)
        check('B2: сервер Apps Script НЕ звался (заявка: без скрипта)',
              len(SERVER_W_CALLS) == srv_before, len(SERVER_W_CALLS))
        sc = page.evaluate(SCREEN_JS)
        check('B2: экран показывает −2° (данные wttr.in)',
              sc.get('tempTxt') == '-2°', sc)
        check('B2: зона погоды на экране непуста',
              (sc.get('weatherZone') or 0) > 5, sc)
        shot(page, '04-weather-wttr-fallback.png')

        # B3: оба прямых сбой → сервер («через Apps Script»)
        WT_MODE[0] = 'fail'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(700)
        ws = page.evaluate(WSTAT_JS)
        check('B3: резерв — «через Apps Script» в статусе',
              'Есть данные' in (ws.get('text') or '') and
              '(через Apps Script)' in (ws.get('text') or ''), ws)
        sc = page.evaluate(SCREEN_JS)
        check('B3: экран показывает −12° (данные сервера)',
              sc.get('tempTxt') == '-12°', sc)
        shot(page, '05-weather-server-fallback.png')

        # B4: оба сбой + сервер diag «нет разрешения UrlFetchApp»
        # (сценарий из заявки) → подсказка authorizeWeather + dnote
        WEATHER_MODE[0] = 'perm'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(700)
        ws = page.evaluate(WSTAT_JS)
        txt = ws.get('text') or ''
        check('B4: варнинг-стиль', 'warn' in (ws.get('cls') or ''), ws)
        check('B4: dnote с ОБЕИМИ каналами',
              '(прямой запрос: open-meteo: http_503; wttr.in: http_502)' in txt,
              txt[:200])
        check('B4: подсказка authorizeWeather() (нет разрешения)',
              'authorizeWeather()' in txt, txt[:200])
        check('B4: подсказка про новую версию развёртывания',
              'новую' in txt and 'версию развёртывания' in txt, txt[:200])
        shot(page, '06-weather-perm-hint.png')

        # B5: восстановление — «Обновить сейчас» снова open-meteo
        OM_MODE[0] = 'ok'
        WT_MODE[0] = 'ok'
        WEATHER_MODE[0] = 'ok'
        om_before = len(OM_CALLS)
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(700)
        check('B5: «Обновить сейчас» дёргает open-meteo повторно',
              len(OM_CALLS) > om_before, (om_before, len(OM_CALLS)))
        ws = page.evaluate(WSTAT_JS)
        check('B5: статус снова «Есть данные» (open-meteo)',
              'Есть данные' in (ws.get('text') or '') and
              'open-meteo.com (напрямую из браузера)' in (ws.get('text') or ''), ws)
        ctx.close()

        # ==============================================================
        print('== C: 1024 светлая тема — попапы в пределах, 0 JS-ошибок ==')
        ctx2 = make_ctx('light', 1024, 700, dpr=1.0)
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(1200)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        page2.click('#wsLcdClock')
        page2.click('#wsLcdGear')
        page2.wait_for_timeout(300)
        pp2 = page2.evaluate(POPUP_JS)
        check('C: обе панели в пределах вьюпорта (1024)',
              pp2.get('insideViewport'), pp2)
        cy2 = page2.evaluate(CAL534_JS)
        check('C: подписей нет и на 1024 (светлая)',
              (cy2.get('labels') or 0) == 0, cy2)
        check('C: левый край строк головы и на 1024',
              cy2.get('yearLeftAtGrid') and cy2.get('monthLeftAtGrid'), cy2)
        ws2 = page2.evaluate(WSTAT_JS)
        check('C: погода есть и в светлой теме',
              'Есть данные' in (ws2.get('text') or ''), (ws2.get('text') or '')[:120])
        shot(page2, '07-light-1024-both.png')
        ctx2.close()

        # ==============================================================
        print()
        print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
        if js_errors:
            print('JS-ОШИБКИ (первый контекст): %s' % js_errors[:3])
        if js_errors2:
            print('JS-ОШИБКИ (второй контекст): %s' % js_errors2[:3])
        if FAIL or js_errors or js_errors2:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
