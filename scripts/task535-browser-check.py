#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 535 browser-check: LCD-информер Табеля — заявка:
# «В окне информера смести немного правее день недели и дату, чтобы
#  погода не примыкала слишком близко к дате, и буква "Я" в дне
#  недели написана без левой ножки, исправь. Выравни по высоте все
#  кнопки года и месяца в календаре, и в светлой теме стрелки в
#  кнопках и надпись Сегодня сделай поярче (сейчас бледные и плохо
#  видно).»
#  A) LCD-СЕТКА (window.WsLcdClock._grid): ПЯТНИЦА начинается на
#     кол. 60 (было 56 — смещена ПРАВЕЕ); дата 111..169 нетронута;
#     погода «-2°» (прямой open-meteo): иконка с 177 (НЕ 172), зазор
#     дата→иконка 170..176 ЧИСТ (7 колонок — не примыкает); «-12°»:
#     иконка 172 (кламп — регресса нет); «--»: прочерк у края.
#  B) КАЛЕНДАРЬ: селекты года/месяца и кнопки — ОДИНАКОВАЯ высота
#     (30px); светлая тема: стрелки/«Сегодня» — ТЁМНЫЙ контрастный
#     цвет rgb(20,20,19) (было бледное rgba(200,215,230,.9)).
#  C) 1024 светлая тема — попапы в пределах вьюпорта; 0 JS-ошибок.
#  D) VLM-скриншоты: строка LCD (ПЯТНИЦА с новой «Я»), календарь
#     тёмный/светлый.
import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task535')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

OM_CALLS = []
WT_CALLS = []
SERVER_W_CALLS = []


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


# --- Данные мока (как в task534) ---
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

# прямой ответ open-meteo: −1.6°C → «-2°» (3 глифа — динамическая иконка)
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
        return {'ok': True, 'data': WEATHER_OK}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# --- JS-побы ---

# LCD-сетка: колонки дня недели, даты и блока погоды
GRID_JS = r"""(() => {
    const WsL = window.WsLcdClock;
    if (!WsL || !WsL._grid) return {missing: true};
    const g = WsL._grid;
    const lit = (r, a, b) => { let n = 0;
        for (let c = a; c <= b; c++) n += (g[r][c] ? 1 : 0); return n; };
    const dayName = WsL._DAYS[(new Date().getDay() + 6) % 7];
    // первый горящий столбец дня недели (ряды 6..12, зона 42..110)
    let dayFirst = -1;
    for (let c = 42; c <= 110; c++)
        if (lit(6, c, c) || lit(9, c, c)) { dayFirst = c; break; }
    // первый горящий столбец блока погоды (ряды 5..12, зона 170..204)
    let wxFirst = -1, wxLast = -1;
    for (let c = 170; c <= 204; c++)
        for (let r = 5; r <= 12; r++)
            if (g[r][c]) { if (wxFirst < 0) wxFirst = c; wxLast = c; break; }
    const gapDateWeather = (function () {
        // дата кончается на 169 (X_DATE=111 + 59); зазор = 170..wxFirst-1
        let n = 0;
        if (wxFirst > 0)
            for (let r = 5; r <= 12; r++) n += lit(r, 170, wxFirst - 1);
        return n;
    })();
    return {dayName: dayName, dayFirst: dayFirst,
            date113: lit(6, 113, 113), date111empty: lit(6, 111, 111),
            wxFirst: wxFirst, wxLast: wxLast,
            gapDateWeather: gapDateWeather,
            tempTxt: WsL._weather ? WsL._weather.tempTxt : null,
            icon: WsL._weather ? WsL._weather.icon : null,
            cols: WsL.COLS, xIcon: WsL.X_ICON, xDay: WsL.X_DAY};})"""

# календарь: высоты контролов + цвета светлой темы
CAL535_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    if (!cal || cal.hidden) return {missing: true};
    const yearRow = cal.querySelector('.ws-lcd-cal-year');
    const monthRow = cal.querySelector('.ws-lcd-cal-month');
    const ysel = yearRow ? yearRow.querySelector('select') : null;
    const msel = monthRow ? monthRow.querySelector('select') : null;
    const ynavs = yearRow ? yearRow.querySelectorAll('.ws-lcd-cal-nav') : [];
    const mnavs = monthRow ? monthRow.querySelectorAll('.ws-lcd-cal-nav') : [];
    const todayBtn = monthRow ? monthRow.querySelector('.ws-lcd-cal-today') : null;
    const h = el => el ? Math.round(el.getBoundingClientRect().height * 10) / 10 : null;
    const col = el => el ? getComputedStyle(el).color : null;
    const bg = el => el ? getComputedStyle(el).backgroundColor : null;
    const ynav = ynavs.length ? ynavs[0] : null;
    const mnav = mnavs.length ? mnavs[0] : null;
    return {
        yselH: h(ysel), mselH: h(msel), ynavH: h(ynav), mnavH: h(mnav),
        todayH: h(todayBtn),
        ynavColor: col(ynav), mnavColor: col(mnav), todayColor: col(todayBtn),
        todayBg: bg(todayBtn),
        monthOptCount: msel ? msel.options.length : 0};})"""

# попапы: видимость/геометрия
POPUP_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    const set = document.getElementById('wsLcdSet');
    if (!cal || !set) return {missing: true};
    const c = cal.getBoundingClientRect(), s = set.getBoundingClientRect();
    return {calHidden: cal.hidden, setHidden: set.hidden,
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
                "localStorage.setItem('kip8test:kip8_session_token','bc-t535');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            def om_handle(route):
                OM_CALLS.append(1)
                route.fulfill(status=200,
                              content_type='application/json; charset=utf-8',
                              body=OM_JSON)
            ctx.route('**api.open-meteo.com/**', om_handle)

            def wt_handle(route):
                WT_CALLS.append(1)
                route.fulfill(status=200,
                              content_type='text/plain; charset=utf-8',
                              body=WTTR_JSON)
            ctx.route('**wttr.in/**', wt_handle)

            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
                if action == 'workSchedule.getWeather':
                    SERVER_W_CALLS.append(1)
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
        print('== A: LCD-СЕТКА — день недели ПРАВЕЕ, погода не примыкает ==')
        ctx = make_ctx('dark', 1280, 720, dpr=2.0)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1200)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        gr = page.evaluate(GRID_JS)
        today = _dt.date.today().weekday()   # 0=Пн
        day0 = {0: 43, 1: 61, 2: 66, 3: 60, 4: 60, 5: 63, 6: 50}[today]
        check('A: день недели (%s) смещён ПРАВЕЕ (первый столбец ≥ %d)'
              % (gr.get('dayName'), day0),
              (gr.get('dayFirst') or -1) >= day0, gr)
        check('A: X_DAY=52 (зона сдвинута правее — константа)',
              gr.get('xDay') == 52, gr)
        check('A: дата «16.10.2026» на X_DATE=111 нетронута',
              gr.get('date113') == 1 and gr.get('date111empty') == 0, gr)

        # погода: прямой open-meteo −1.6 → «-2°» (3 глифа)
        check('A: погода пришла прямым каналом («-2°», иконка)',
              gr.get('tempTxt') == '-2°' and gr.get('icon'), gr)
        check('A: блок погоды начинается с 177 (НЕ 172) — прижат к правому краю',
              gr.get('wxFirst') == 177, gr)
        check('A: зазор дата→погода (170..176) ЧИСТ — не примыкает',
              gr.get('gapDateWeather') == 0, gr)
        check('A: блок погоды до правого края (203)',
              gr.get('wxLast') == 203, gr)
        check('A: сервер Apps Script НЕ звался (прямой канал)',
              len(SERVER_W_CALLS) == 0, SERVER_W_CALLS)

        # фото строки LCD (ПЯТНИЦА с новой «Я») — элемент-скриншот канваса
        try:
            lcd = page.locator('#wsLcdClock')
            lcd.screenshot(path=os.path.join(SHOT_DIR, '01-lcd-row.png'))
            check('A: скриншот строки LCD сохранён', True)
        except Exception as e:
            check('A: скриншот строки LCD сохранён', False, str(e))

        # «-12°»: иконка клампится на 172 — регресса нет
        page.evaluate(
            "window.WsLcdClock._applyWeather({temp:-12,"
            "phenomenon:'Слабый снег',cloud:8})")
        page.wait_for_timeout(200)
        gr12 = page.evaluate(GRID_JS)
        check('A: «-12°»: иконка на 172 (кламп) — как раньше',
              gr12.get('wxFirst') == 172, gr12)
        check('A: «-12°»: зазор дата→иконка = 2 колонки (170..171 чисты)',
              (gr12.get('wxFirst') or 0) == 172 and
              all(not page.evaluate(
                  "window.WsLcdClock._grid[%d][%d]" % (r, c))
                  for r in (5, 8, 12) for c in (170, 171)), gr12)

        # «--»: прочерк у правого края
        page.evaluate("window.WsLcdClock._weather = null;" +
                      "window.WsLcdClock._lastSec = -1;" +
                      "window.WsLcdClock._tick()")
        page.wait_for_timeout(200)
        grdd = page.evaluate(GRID_JS)
        check('A: «--» (нет данных): блок = прочерк (светятся 194..196 и 200..202)',
              grdd.get('wxFirst') == 194 and grdd.get('wxLast') == 202, grdd)

        # восстановим «-2°» для скриншотов
        page.evaluate(
            "window.WsLcdClock._applyWeather({temp:-1.6,"
            "phenomenon:'Пасмурно',cloud:10})")

        # ==============================================================
        print('== B: КАЛЕНДАРЬ — высоты кнопок ровные (30px) ==')
        page.click('#wsLcdClock')
        page.wait_for_timeout(300)
        cy = page.evaluate(CAL535_JS)
        hs = [cy.get('yselH'), cy.get('mselH'), cy.get('ynavH'),
              cy.get('mnavH'), cy.get('todayH')]
        check('B: все высоты сняты (5 контролов)',
              all(h is not None for h in hs), cy)
        hmin, hmax = min(hs), max(hs)
        check('B: высоты РОВНЫЕ (разброс ≤ 1px): %s' % hs,
              hmax - hmin <= 1.0, cy)
        check('B: высота ≈ 30px (кнопки и селекты)',
              29 <= hmin and hmax <= 31, cy)
        check('B: тёмная тема — стрелки светлые (rgba(200,215,230,.9))',
              str(cy.get('ynavColor')).startswith('rgba(200, 215, 230'), cy)
        shot(page, '02-calendar-dark.png')
        page.keyboard.press('Escape')

        # ==============================================================
        print('== C: СВЕТЛАЯ ТЕМА — яркие стрелки/«Сегодня», 1024 ==')
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
        page2.wait_for_timeout(300)
        cy2 = page2.evaluate(CAL535_JS)
        check('C: светлая тема — стрелки ТЁМНЫЕ rgb(20,20,19) (#141413)',
              cy2.get('ynavColor') == 'rgb(20, 20, 19)' and
              cy2.get('mnavColor') == 'rgb(20, 20, 19)', cy2)
        check('C: светлая тема — «Сегодня» ТЁМНАЯ (rgb(20,20,19))',
              cy2.get('todayColor') == 'rgb(20, 20, 19)', cy2)
        check('C: светлая тема — подложка «Сегодня» белая',
              cy2.get('todayBg') == 'rgb(255, 255, 255)', cy2)
        hs2 = [cy2.get('yselH'), cy2.get('mselH'), cy2.get('ynavH'),
               cy2.get('mnavH'), cy2.get('todayH')]
        check('C: высоты ровные и в светлой теме (разброс ≤ 1px)',
              max(hs2) - min(hs2) <= 1.0, cy2)
        shot(page2, '03-calendar-light.png')
        pop = page2.evaluate(POPUP_JS)
        check('C: календарь в пределах вьюпорта 1024',
              pop.get('insideViewport'), pop)
        shot(page2, '04-light-1024.png')
        check('C: 0 JS-ошибок (светлая)', len(js_errors2) == 0, js_errors2)

        check('A/B: 0 JS-ошибок (тёмная)', len(js_errors) == 0, js_errors)

        browser.close()

    print('\nИТОГО: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
