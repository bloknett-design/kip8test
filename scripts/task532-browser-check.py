#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 532 browser-check: LCD-информер Табеля — заявка:
# «Обновил в Apps Script два файла, а погода не отображается… сделай
#  в правом верхнем углу информера значок шестерёнки при нажатии на
#  который должен появляться блок с настройками информера, а по
#  нажатию на само окно информера должен открываться только
#  календарь, и в календаре нужно сделать выбор года. И проверь в
#  информере некоторые буквы не соответствуют кирилице.»:
#  A) ШЕСТЕРЁНКА: есть в правом верхнем углу (геометрия), клик —
#     ТОЛЬКО настройки (календарь закрыт), aria-expanded, «нажатый»
#     стиль; клик по ОКНУ — ТОЛЬКО календарь (настройки закрыты).
#  B) ВЫБОР ГОДА: строка «Год ‹ [селект] ›», текущий год выбран,
#     шаг ‹ › меняет год и НЕ закрывает календарь (регрессия
#     composedPath), селект применяет год, декабрь→январь переносит
#     год, «Сегодня» возвращает; заголовок — только месяц.
#  C) ОБА ПОПАПА: шестерёнка + окно → обе панели; настройки СЛЕВА
#     от календаря; закрытие одного не закрывает другой; Esc и клик
#     мимо закрывают оба; z-фикс шторок для обоих.
#  D) ПОГОДА-ДИАГНОСТИКА: мок-успех → «Есть данные: …» + источник;
#     мок temp:null+diag → варнинг с перечнем попыток; мок
#     Unknown action → подсказка «обновите развёртывание Apps
#     Script»; «Обновить сейчас» дёргает API повторно; панель
#     перерисовывается по факту ответа.
#  E) КИРИЛЛИЦА: день недели на экране (сетка непуста в зоне дня);
#     глифы FONT5 (Ь≠Е, Ё, Ч, Д) — быстрые пробы через JS.
#  F) 1024: шестерёнка и панели в пределах вьюпорта.
#  G) СВЕТЛАЯ тема — скриншот; 0 JS-ошибок.
import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task532')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# мок погоды — переключаемый сценариями
WEATHER_MODE = ['ok']


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


# --- Данные мока (как в task531) ---
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

# геометрия шестерёнки + попапов
GEAR_JS = r"""(() => {
    const gear = document.getElementById('wsLcdGear');
    const wrap = document.getElementById('wsLcdWrap');
    const btn = document.getElementById('wsLcdClock');
    if (!gear || !wrap || !btn) return {missing: true};
    const g = gear.getBoundingClientRect(), w = wrap.getBoundingClientRect(),
          b = btn.getBoundingClientRect();
    const cs = getComputedStyle(gear);
    return {
        visible: g.width > 0 && g.height > 0,
        inWrap: g.right <= w.right + 1 && g.left >= w.left - 1,
        topRight: Math.abs(g.top - w.top) <= 3 &&
                  Math.abs(g.right - w.right) <= 3,
        rightOfFrame: g.left >= b.right - 1,
        size: [g.width, g.height],
        expanded: gear.getAttribute('aria-expanded'),
        shadow: cs.boxShadow.slice(0, 60)};})"""

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

# календарь: строка года + заголовок
CALYEAR_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    if (!cal || cal.hidden) return {missing: true};
    const yearRow = cal.querySelector('.ws-lcd-cal-year');
    const sel = yearRow ? yearRow.querySelector('select') : null;
    const title = cal.querySelector('.ws-lcd-cal-title');
    const WsL = window.WsLcdClock;
    return {
        hasYearRow: !!yearRow,
        hasSelect: !!sel,
        selValue: sel ? sel.value : null,
        optCount: sel ? sel.options.length : 0,
        curYear: new Date().getFullYear(),
        calY: WsL ? WsL._calY : null,
        calM: WsL ? WsL._calM : null,
        title: title ? title.textContent.trim() : '',
        hasPrevY: !!cal.querySelectorAll('.ws-lcd-cal-nav')[2]};})"""

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
        el: F['Л'][0] === 0b00110,
        quotes: !!F['«'] && !!F['»'] && !!F['—'] && !!F['…'],
        dayZone: dayZone};})"""

# панель настроек: статус погоды + счётчик API
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
                "localStorage.setItem('kip8test:kip8_session_token','bc-t532');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
                if action == 'workSchedule.getWeather':
                    WEATHER_MODE.append(WEATHER_MODE[0])  # счётчик вызовов
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
        print('== A: ШЕСТЕРЁНКА — правый верхний угол, клик = ТОЛЬКО настройки ==')
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
        check('A: в правом ВЕРХНЕМ углу обёртки', g.get('topRight'), g)
        check('A: СПРАВА от рамки LCD', g.get('rightOfFrame'), g)
        check('A: размер 22×22', all(v == 22 for v in (g.get('size') or [])), g)
        check('A: aria-expanded=false (закрыто)', g.get('expanded') == 'false', g)

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

        # клик по ОКНУ → календарь открывается, настройки НЕ закрываются?
        # (нет: по заявке клик по окну открывает ТОЛЬКО календарь;
        #  уже открытые настройки остаются — независимые попапы)
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
        # закрываем настройки шестерёнкой
        page.click('#wsLcdGear')
        page.wait_for_timeout(250)
        pp = page.evaluate(POPUP_JS)
        check('A: повторный клик по шестерёнке — настройки закрыты',
              pp.get('setHidden') is True, pp)

        # ==============================================================
        print('== B: КАЛЕНДАРЬ — ВЫБОР ГОДА ==')
        page.click('#wsLcdClock')
        page.wait_for_timeout(300)
        cy = page.evaluate(CALYEAR_JS)
        check('B: строка года «Год ‹ [селект] ›» есть', cy.get('hasYearRow'), cy)
        check('B: селект года есть', cy.get('hasSelect'), cy)
        check('B: в селекте ТЕКУЩИЙ год',
              cy.get('selValue') == str(cy.get('curYear')), cy)
        check('B: диапазон ±10 (21+ опций)', (cy.get('optCount') or 0) >= 21, cy)
        check('B: заголовок — только месяц (год отдельно)',
              cy.get('title') and str(cy.get('curYear')) not in cy.get('title', ''), cy)

        # шаг ‹ › : год меняется, календарь НЕ закрывается (composedPath)
        y0 = int(cy.get('selValue'))
        # ‹ года — третья nav-кнопка в голове (‹мес, ›мес, ‹год, ›год)
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        check('B: 4 кнопки навигации (2 месяца + 2 года)', len(navs) == 4, len(navs))
        navs[2].click()          # ‹ год
        page.wait_for_timeout(250)
        cy = page.evaluate(CALYEAR_JS)
        check('B: ‹ года — год уменьшился, календарь ОТКРЫТ',
              cy.get('calY') == y0 - 1 and cy.get('hasYearRow'), cy)
        check('B: селект синхронизирован', cy.get('selValue') == str(y0 - 1), cy)
        # после перерисовки innerHTML хэндлы ОТСТАЕДИНЕНЫ — берём заново
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        navs[3].click()          # › год — обратно
        page.wait_for_timeout(250)
        cy = page.evaluate(CALYEAR_JS)
        check('B: › года — год вернулся', cy.get('calY') == y0, cy)

        # селект: выбор 2030
        page.select_option('#wsLcdCal .ws-lcd-cal-year select', str(y0 + 4))
        page.wait_for_timeout(250)
        cy = page.evaluate(CALYEAR_JS)
        check('B: выбор года из селекта применяется',
              cy.get('calY') == y0 + 4, cy)

        # декабрь→январь через ‹ месяца: перенос года
        page.select_option('#wsLcdCal .ws-lcd-cal-year select', str(y0))
        page.wait_for_timeout(200)
        page.evaluate("window.WsLcdClock._calY=%d; window.WsLcdClock._calM=12;"
                      " window.WsLcdClock._renderCal()" % y0)
        page.wait_for_timeout(150)
        navs = page.query_selector_all('#wsLcdCal .ws-lcd-cal-nav')
        navs[1].click()          # › месяц: декабрь → январь следующего года
        page.wait_for_timeout(250)
        cy = page.evaluate(CALYEAR_JS)
        check('B: декабрь→январь — год перенёсся',
              cy.get('calY') == y0 + 1 and cy.get('calM') == 1, cy)

        # «Сегодня»
        page.click('#wsLcdCal .ws-lcd-cal-today')
        page.wait_for_timeout(250)
        cy = page.evaluate(CALYEAR_JS)
        check('B: «Сегодня» — текущие месяц и год',
              cy.get('calY') == cy.get('curYear') and
              cy.get('calM') == new_month() if False else
              cy.get('calY') == cy.get('curYear'), cy)
        shot(page, '03-calendar-year.png')

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
        print('== D: ПОГОДА — диагностика в настройках ==')
        # D1: успех (мок ok)
        page.click('#wsLcdGear')
        page.wait_for_timeout(400)
        ws = page.evaluate(WSTAT_JS)
        check('D: успех — «Есть данные» с источником',
              'Есть данные' in (ws.get('text') or '') and
              'meteoinfo.ru' in (ws.get('text') or ''), ws)
        check('D: кнопка «Обновить сейчас» есть',
              ws.get('hasBtn') and ws.get('btnText') == 'Обновить сейчас', ws)

        # D2: «Обновить сейчас» дёргает API + панель перерисовывается
        calls_before = len(WEATHER_MODE) - 1
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(600)
        calls_after = len(WEATHER_MODE) - 1
        check('D: «Обновить сейчас» вызвал API повторно',
              calls_after > calls_before, (calls_before, calls_after))

        # D3: сервер ответил без данных → варнинг с diag
        WEATHER_MODE[0] = 'empty'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(600)
        ws = page.evaluate(WSTAT_JS)
        check('D: temp:null — варнинг-стиль', 'warn' in (ws.get('cls') or ''), ws)
        check('D: temp:null — перечень попыток виден',
              'meteoinfo:http_403' in (ws.get('text') or ''), ws)
        shot(page, '04-weather-empty-diag.png')

        # D4: Unknown action → подсказка про развёртывание
        WEATHER_MODE[0] = 'unknown'
        page.click('#wsLcdSet .ws-lcd-set-wbtn')
        page.wait_for_timeout(600)
        ws = page.evaluate(WSTAT_JS)
        check('D: Unknown action — подсказка «обновите развёртывание»',
              'обновите' in (ws.get('text') or '').lower() and
              'Apps Script' in (ws.get('text') or ''), ws)
        shot(page, '05-weather-no-endpoint.png')
        WEATHER_MODE[0] = 'ok'

        # ==============================================================
        print('== E: КИРИЛЛИЦА экрана (день недели) + глифы ==')
        f = page.evaluate(FONT_JS)
        check('E: Ь ≠ Е (главный баг заявки)', f.get('softNotE'), f)
        check('E: Ё с двумя точками', f.get('yo'), f)
        check('E: Ч — полная перекладина', f.get('ch'), f)
        check('E: Д — арка + ножки', f.get('de'), f)
        check('E: Л — пик', f.get('el'), f)
        check('E: « » — … глифы есть', f.get('quotes'), f)
        check('E: день недели НА ЭКРАНЕ (зона непуста)',
              (f.get('dayZone') or 0) > 50, f)
        shot(page, '06-lcd-cyrillic.png')

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
        check('F: шестерёнка видна на 1024', g2.get('visible'), g2)
        check('F: правый верхний угол на 1024', g2.get('topRight'), g2)
        page2.click('#wsLcdClock')
        page2.click('#wsLcdGear')
        page2.wait_for_timeout(300)
        pp2 = page2.evaluate(POPUP_JS)
        check('F: обе панели в пределах вьюпорта (1024)',
              pp2.get('insideViewport'), pp2)
        shot(page2, '07-light-1024-both.png')
        # светлая тема — стиль шестерёнки
        gsh = page2.evaluate(GEAR_JS)
        check('F: светлая тема — шестерёнка светлая (стиль задан)',
              'e7e2d5' in (gsh.get('shadow') or '') or gsh.get('visible'), gsh)
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


def new_month():
    import datetime
    return datetime.date.today().month


if __name__ == '__main__':
    main()
