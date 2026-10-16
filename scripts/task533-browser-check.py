#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 533 browser-check: LCD-информер Табеля — заявка:
# «Погода не отображается, может рассмотреть способ получения
#  данных погоды не через скрипт? Кнопку со значком шестерёнки
#  расположи внутри информера. В календаре поменяй местами
#  отображения и селекторы года и месяца (год сверху, месяц под
#  годом), и у месяца сделай как у года селект + стрелки.»:
#  A) ШЕСТЕРЁНКА ВНУТРИ информера: оверлей на ЭКРАНЕ (правый
#     верхний угол стекла, bbox внутри рамки и над канвасом),
#     transparent-фон, 20×20; клик — ТОЛЬКО настройки; клик по
#     ОКНУ — ТОЛЬКО календарь; независимые попапы.
#  B) КАЛЕНДАРЬ: ГОД — ПЕРВОЙ строкой, МЕСЯЦ — ПОД годом;
#     у месяца СЕЛЕКТ (12 опций, текущий выбран) + стрелки ‹ ›;
#     «Сегодня» в строке месяца; декабрь→январь переносит год
#     и синхронизирует ОБА селекта; селект месяца применяет месяц.
#  C) ЗАКРЫТИЕ: Esc и клик мимо закрывают оба попапа.
#  D) ПОГОДА НАПРЯМУЮ: мок open-meteo 200 → «Есть данные …
#     open-meteo.com (напрямую из браузера)», сервер Apps Script
#     НЕ зовётся; open-meteo сбой → резерв сервера («через Apps
#     Script»); open-meteo сбой + сервер empty → варнинг с diag;
#     open-meteo сбой + Unknown action → подсказка про развёрты-
#     вание + причина прямого сбоя; «Обновить сейчас» дёргает
#     open-meteo повторно; экран показывает температуру.
#  E) КИРИЛЛИЦА: день недели на экране; глифы FONT5.
#  F) 1024 светлая тема — в пределах вьюпорта; 0 JS-ошибок.
import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8998
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task533')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# режимы погоды: прямой канал (open-meteo) и сервер (Apps Script)
OM_MODE = ['ok']            # ok | fail
WEATHER_MODE = ['ok']       # ok | empty | unknown
OM_CALLS = []               # счётчик прямых запросов
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


# --- Данные мока (как в task531/532) ---
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
WEATHER_EMPTY = {'temp': None, 'phenomenon': None, 'cloud': None, 'wind': None,
                 'windDir': None, 'pressure': None, 'humidity': None,
                 'obsLocal': None, 'source': None,
                 'note': 'weather_unavailable',
                 'diag': 'meteoinfo:http_403; open-meteo:http_503',
                 'fetched': '2026-10-15T13:10:00Z'}

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
        if WEATHER_MODE[0] == 'unknown':
            return {'ok': False,
                    'error': 'Unknown action: workSchedule.getWeather'}
        return {'ok': True, 'data': WEATHER_OK}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# --- JS-побы ---

# геометрия шестерёнки: ВНУТРИ информера (оверлей на экране)
GEAR_JS = r"""(() => {
    const gear = document.getElementById('wsLcdGear');
    const wrap = document.getElementById('wsLcdWrap');
    const btn = document.getElementById('wsLcdClock');
    const cv = document.getElementById('wsLcdCanvas');
    if (!gear || !wrap || !btn || !cv) return {missing: true};
    const g = gear.getBoundingClientRect(), w = wrap.getBoundingClientRect(),
          b = btn.getBoundingClientRect(), c = cv.getBoundingClientRect();
    const cs = getComputedStyle(gear);
    return {
        visible: g.width > 0 && g.height > 0,
        // ВНУТРИ информера: шестерёнка целиком В РАМКЕ (не справа от неё)
        insideFrame: g.left >= b.left - 1 && g.right <= b.right + 1 &&
                     g.top >= b.top - 1 && g.bottom <= b.bottom + 1,
        // пересекает ЭКРАН (канвас) — оверлей на стекле
        overScreen: g.left < c.right && g.right > c.left &&
                    g.top < c.bottom && g.bottom > c.top,
        // правый ВЕРХНИЙ угол стекла
        topRightOfScreen: Math.abs(g.top - c.top) <= 5 &&
                          Math.abs(g.right - c.right) <= 8,
        size: [g.width, g.height],
        expanded: gear.getAttribute('aria-expanded'),
        bg: cs.backgroundColor,
        color: cs.color};})"""

POPUP_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    const set = document.getElementById('wsLcdSet');
    const wrap = document.getElementById('wsLcdWrap');
    if (!cal || !set || !wrap) return {missing: true};
    const c = cal.getBoundingClientRect(), s = set.getBoundingClientRect(),
          w = wrap.getBoundingClientRect();
    return {calHidden: cal.hidden, setHidden: set.hidden,
            calVis: getComputedStyle(cal).display,
            setVis: getComputedStyle(set).display,
            calLeft: c.left, calRight: c.right, calW: c.width,
            setLeft: s.left, setRight: s.right, setW: s.width,
            gap: c.left - s.right,
            sameTop: Math.abs(c.top - s.top) < 2,
            setAtRightEdge: Math.abs(s.right - w.right) < 2,
            insideViewport: s.left >= 0 && c.left >= 0};})"""

# календарь: ГОД СВЕРХУ, МЕСЯЦ ПОД ГОДОМ (Task 533)
CAL_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    if (!cal || cal.hidden) return {missing: true};
    const yearRow = cal.querySelector('.ws-lcd-cal-year');
    const monthRow = cal.querySelector('.ws-lcd-cal-month');
    const ysel = yearRow ? yearRow.querySelector('select') : null;
    const msel = monthRow ? monthRow.querySelector('select') : null;
    const todayBtn = monthRow ? monthRow.querySelector('.ws-lcd-cal-today') : null;
    const WsL = window.WsLcdClock;
    const yearFirst = (() => {
        if (!yearRow || !monthRow) return null;
        return Array.prototype.indexOf.call(cal.children, yearRow) <
               Array.prototype.indexOf.call(cal.children, monthRow); })();
    return {
        hasYearRow: !!yearRow, hasMonthRow: !!monthRow,
        yearFirst: yearFirst,
        yearSelValue: ysel ? ysel.value : null,
        monthSelValue: msel ? msel.value : null,
        monthOptCount: msel ? msel.options.length : 0,
        monthSelText: msel && msel.selectedIndex >= 0 ?
            msel.options[msel.selectedIndex].textContent : '',
        todayInMonthRow: !!todayBtn,
        calY: WsL ? WsL._calY : null, calM: WsL ? WsL._calM : null,
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

# шрифт: глифы (Ь≠Е, Ё, Ч, Д) + день недели на сетке
FONT_JS = r"""(() => {
    const WsL = window.WsLcdClock;
    if (!WsL) return {missing: true};
    const F = WsL.FONT5;
    const dayZone = (() => { let s = 0;
        for (let r = 4; r <= 12; r++) for (let c = 42; c <= 110; c++)
            s += (WsL._grid ? WsL._grid[r][c] : 0);
        return s; })();
    return {
        softNotE: JSON.stringify(F['Ь']) !== JSON.stringify(F['Е']),
        yo: !!F['Ё'] && F['Ё'][0] === 0b01010,
        ch: F['Ч'][3] === 0b11111,
        de: F['Д'][0] === 0b01110 && F['Д'][6] === 0b11011,
        dayZone: dayZone};})"""

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
                "localStorage.setItem('kip8test:kip8_session_token','bc-t533');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            # ПРЯМОЙ канал погоды: open-meteo.com (Task 533)
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
        print('== A: ШЕСТЕРЁНКА — ВНУТРИ информера, клик = ТОЛЬКО настройки ==')
        OM_MODE[0] = 'ok'
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

        g = page.evaluate(GEAR_JS)
        check('A: шестерёнка ВИДИМА', g.get('visible'), g)
        check('A: ВНУТРИ рамки информера (не справа от неё)',
              g.get('insideFrame'), g)
        check('A: оверлей НАД экраном (пересекает канвас)',
              g.get('overScreen'), g)
        check('A: правый ВЕРХНИЙ угол стекла', g.get('topRightOfScreen'), g)
        check('A: зона клика 20×20', all(v == 20 for v in (g.get('size') or [])), g)
        check('A: фон прозрачный («на стекле»)',
              (g.get('bg') or '').replace(' ', '') in
              ('rgba(0,0,0,0)', 'transparent'), g)
        check('A: aria-expanded=false (закрыто)', g.get('expanded') == 'false', g)
        shot(page, '00-lcd-gear-inside.png')

        # клик по ШЕСТЕРЁНКЕ → ТОЛЬКО настройки
        page.click('#wsLcdGear')
        page.wait_for_timeout(300)
        pp = page.evaluate(POPUP_JS)
        check('A: клик по шестерёнке — настройки ОТКРЫТЫ',
              pp.get('setHidden') is False and pp.get('setVis') != 'none', pp)
        check('A: клик по шестерёнке — КАЛЕНДАРЬ закрыт',
              pp.get('calHidden') is True, pp)
        check('A: настройки у ПРАВОГО края (под шестерёнкой)',
              pp.get('setAtRightEdge'), pp)
        g = page.evaluate(GEAR_JS)
        check('A: aria-expanded=true у шестерёнки', g.get('expanded') == 'true', g)
        shot(page, '01-gear-settings-only.png')

        # клик по ОКНУ → календарь открывается (независимые попапы)
        page.click('#wsLcdClock')
        page.wait_for_timeout(300)
        pp = page.evaluate(POPUP_JS)
        check('A: клик по ОКНУ — календарь ОТКРЫТ',
              pp.get('calHidden') is False, pp)
        check('A: оба попапа открыты одновременно (независимые)',
              pp.get('setHidden') is False, pp)
        check('A: при открытом календаре настройки СЛЕВА (gap > 0)',
              (pp.get('gap') or -1) > 0, pp)
        check('A: одна линия по верху', pp.get('sameTop'), pp)
        shot(page, '02-both-popups.png')

        # закрытие календаря НЕ закрывает настройки
        page.click('#wsLcdClock')
        page.wait_for_timeout(250)
        pp = page.evaluate(POPUP_JS)
        check('A: повторный клик по окну — календарь закрыт',
              pp.get('calHidden') is True, pp)
        check('A: настройки остаются ОТКРЫТЫМИ (независимость)',
              pp.get('setHidden') is False, pp)
        page.click('#wsLcdGear')
        page.wait_for_timeout(250)
        pp = page.evaluate(POPUP_JS)
        check('A: повторный клик по шестерёнке — настройки закрыты',
              pp.get('setHidden') is True, pp)

        # ==============================================================
        print('== B: КАЛЕНДАРЬ — ГОД СВЕРХУ, МЕСЯЦ ПОД ГОДОМ (селект+стрелки) ==')
        page.click('#wsLcdClock')
        page.wait_for_timeout(300)
        cy = page.evaluate(CAL_JS)
        check('B: строки года И месяца есть',
              cy.get('hasYearRow') and cy.get('hasMonthRow'), cy)
        check('B: ГОД — ПЕРВОЙ строкой (месяц ПОД ним)', cy.get('yearFirst'), cy)
        check('B: в селекте года ТЕКУЩИЙ год',
              cy.get('yearSelValue') == str(cy.get('curY')), cy)
        check('B: селект месяца — 12 опций',
              (cy.get('monthOptCount') or 0) == 12, cy)
        check('B: в селекте месяца ТЕКУЩИЙ месяц',
              cy.get('monthSelValue') == str(cy.get('curM')), cy)
        check('B: «Сегодня» — в строке месяца', cy.get('todayInMonthRow'), cy)
        shot(page, '03-calendar-year-month.png')

        # порядок nav-кнопок: год ПЕРВОЙ строкой → [‹год, ›год, ‹мес, ›мес]
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        check('B: 4 кнопки навигации (2 года + 2 месяца)', len(navs) == 4, len(navs))
        y0 = int(cy.get('yearSelValue'))
        navs[0].click()          # ‹ год (первая строка — год)
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL_JS)
        check('B: ‹ года — год уменьшился, календарь ОТКРЫТ',
              cy.get('calY') == y0 - 1 and cy.get('hasYearRow'), cy)
        check('B: селект года синхронизирован',
              cy.get('yearSelValue') == str(y0 - 1), cy)
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        navs[1].click()          # › год — обратно
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL_JS)
        check('B: › года — год вернулся', cy.get('calY') == y0, cy)

        # селект месяца: выбор марта
        page.select_option('#wsLcdCal .ws-lcd-cal-month select', '3')
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL_JS)
        check('B: выбор месяца из селекта применяется (Март)',
              cy.get('calM') == 3 and cy.get('monthSelValue') == '3' and
              cy.get('monthSelText') == 'Март', cy)

        # стрелки месяца: › с декабря → январь следующего года
        page.evaluate("window.WsLcdClock._calY=%d; window.WsLcdClock._calM=12;"
                      " window.WsLcdClock._renderCal()" % y0)
        page.wait_for_timeout(150)
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        navs[3].click()          # › месяц (вторая строка): декабрь → январь
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL_JS)
        check('B: декабрь→январь — год перенёсся',
              cy.get('calY') == y0 + 1 and cy.get('calM') == 1, cy)
        check('B: ОБА селекта синхронизированы',
              cy.get('yearSelValue') == str(y0 + 1) and
              cy.get('monthSelValue') == '1' and
              cy.get('monthSelText') == 'Январь', cy)

        # «Сегодня»
        page.click('#wsLcdCal .ws-lcd-cal-today')
        page.wait_for_timeout(250)
        cy = page.evaluate(CAL_JS)
        check('B: «Сегодня» — текущие месяц и год',
              cy.get('calY') == cy.get('curY') and
              cy.get('calM') == cy.get('curM'), cy)
        shot(page, '04-calendar-today.png')

        # ==============================================================
        print('== C: закрытие — Esc и клик мимо (оба попапа) ==')
        page.click('#wsLcdGear')
        page.wait_for_timeout(250)
        pp = page.evaluate(POPUP_JS)
        check('C: оба открыты', pp.get('calHidden') is False and
              pp.get('setHidden') is False, pp)
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)
        pp = page.evaluate(POPUP_JS)
        check('C: Esc закрыл ОБА', pp.get('calHidden') is True and
              pp.get('setHidden') is True, pp)
        page.click('#wsLcdClock')
        page.click('#wsLcdGear')
        page.wait_for_timeout(250)
        page.click('#page-work-schedule .ws-toolbar')
        page.wait_for_timeout(250)
        pp = page.evaluate(POPUP_JS)
        check('C: клик мимо закрыл ОБА', pp.get('calHidden') is True and
              pp.get('setHidden') is True, pp)

        # ==============================================================
        print('== D: ПОГОДА НАПРЯМУЮ из браузера (open-meteo, без Apps Script) ==')
        # D1: прямой успех — сервер Apps Script НЕ звался вовсе
        # (прямой запрос уже выполнен при СТАРТЕ страницы — до клика)
        srv_before = len(SERVER_W_CALLS)
        page.click('#wsLcdGear')
        page.wait_for_timeout(400)
        ws = page.evaluate(WSTAT_JS)
        check('D1: «Есть данные» с каналом «напрямую из браузера»',
              'Есть данные' in (ws.get('text') or '') and
              'open-meteo.com (напрямую из браузера)' in (ws.get('text') or ''), ws)
        check('D1: сервер Apps Script погоду НЕ запрашивал',
              len(SERVER_W_CALLS) == srv_before,
              (srv_before, len(SERVER_W_CALLS)))
        check('D1: прямой запрос был (при старте страницы)',
              len(OM_CALLS) > 0, len(OM_CALLS))
        sc = page.evaluate(SCREEN_JS)
        check('D1: экран показывает −2° (данные open-meteo)',
              sc.get('tempTxt') == '-2°', sc)
        check('D1: зона погоды на экране непуста (иконка+температура)',
              (sc.get('weatherZone') or 0) > 5, sc)
        shot(page, '05-weather-direct-ok.png')

        # D2: «Обновить сейчас» дёргает ПРЯМОЙ канал повторно
        om_before = len(OM_CALLS)
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(600)
        check('D2: «Обновить сейчас» вызвал open-meteo повторно',
              len(OM_CALLS) > om_before, (om_before, len(OM_CALLS)))

        # D3: прямой сбой → РЕЗЕРВ сервера (через Apps Script)
        OM_MODE[0] = 'fail'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(700)
        ws = page.evaluate(WSTAT_JS)
        check('D3: резерв — «через Apps Script» в статусе',
              'Есть данные' in (ws.get('text') or '') and
              '(через Apps Script)' in (ws.get('text') or ''), ws)
        sc = page.evaluate(SCREEN_JS)
        check('D3: экран показывает −12° (данные сервера)',
              sc.get('tempTxt') == '-12°', sc)
        shot(page, '06-weather-fallback-server.png')

        # D4: прямой сбой + сервер ответил БЕЗ данных → варнинг с diag
        WEATHER_MODE[0] = 'empty'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(700)
        ws = page.evaluate(WSTAT_JS)
        check('D4: temp:null — варнинг-стиль', 'warn' in (ws.get('cls') or ''), ws)
        check('D4: перечень попыток сервера виден',
              'meteoinfo:http_403' in (ws.get('text') or ''), ws)
        shot(page, '07-weather-empty-diag.png')

        # D5: прямой сбой + Unknown action → подсказка про развёртывание
        WEATHER_MODE[0] = 'unknown'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(700)
        ws = page.evaluate(WSTAT_JS)
        check('D5: прямой сбой упомянут',
              'Прямой запрос open-meteo не прошёл' in (ws.get('text') or ''), ws)
        check('D5: подсказка «обновите развёртывание»',
              'обновите' in (ws.get('text') or '').lower() and
              'Apps Script' in (ws.get('text') or ''), ws)
        shot(page, '08-weather-no-endpoint.png')
        OM_MODE[0] = 'ok'
        WEATHER_MODE[0] = 'ok'

        # ==============================================================
        print('== E: КИРИЛЛИЦА экрана (день недели) + глифы ==')
        f = page.evaluate(FONT_JS)
        check('E: Ь ≠ Е', f.get('softNotE'), f)
        check('E: Ё с двумя точками', f.get('yo'), f)
        check('E: Ч — полная перекладина', f.get('ch'), f)
        check('E: Д — арка + ножки', f.get('de'), f)
        check('E: день недели НА ЭКРАНЕ (зона непуста)',
              (f.get('dayZone') or 0) > 50, f)
        shot(page, '09-lcd-cyrillic.png')

        ctx.close()

        # ==============================================================
        print('== F: 1024 — в пределах вьюпорта (светлая тема) ==')
        ctx2 = make_ctx('light', 1024, 700, dpr=1.0)
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(1200)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        g2 = page2.evaluate(GEAR_JS)
        check('F: шестерёнка видна на 1024 (внутри информера)',
              g2.get('visible') and g2.get('insideFrame'), g2)
        cy2 = None
        page2.click('#wsLcdClock')
        page2.click('#wsLcdGear')
        page2.wait_for_timeout(300)
        pp2 = page2.evaluate(POPUP_JS)
        check('F: обе панели в пределах вьюпорта (1024)',
              pp2.get('insideViewport'), pp2)
        cy2 = page2.evaluate(CAL_JS)
        check('F: год сверху/месяц снизу и на 1024',
              cy2.get('yearFirst') and (cy2.get('monthOptCount') or 0) == 12, cy2)
        shot(page2, '10-light-1024-both.png')
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
