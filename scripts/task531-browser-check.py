#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 531 browser-check: доработка LCD-информера Табеля (заявка:
# «Экран с эффектом утопленного. Секунды смести вниз ровно по нижней
#  линии остального текста, а две точки выравни по середине между
#  часами и минутами. День недели выравни ровно между циферблатом
#  часов и датой. При нажатии на экран информера, сделай слева от
#  блока календаря блок с настройками информера (настройка
#  отображения, частота вывода информации и на своё усмотрение что
#  нибудь ещё полезное). Есть баг - при переключении месяцов в
#  календаре информера, календарь закрывается, и ещё при открытоых
#  шторках итогов учёта или обозначений на календарь накладывается
#  вертикальная полоса.»):
#  A) ДЕСКТОП тёмная 1280×720 (DPR 2): экран УТОПЛЕН (тень-колодец
#     inset 0 2px 3px), рамка-ВЫСТУП сохранена; ОБЩАЯ НИЖНЯЯ ЛИНИЯ
#     (ряд 12 у всех блоков, ряд 13 пуст); секунды 8..12; двоеточие
#     колонки 16..17 (симметричные зазоры); день недели ЦЕНТР зоны;
#     сетка РОВНАЯ (целый pitch, канвас кратен матрице, сегменты
#     одинаковые).
#  B) НАСТРОЙКИ: клик по экрану → календарь + панель #wsLcdSet СЛЕВА
#     (геометрия: правый край панели левее левого края календаря,
#     верх на одной линии); содержимое (отображение/частота/источники/
#     тест/сброс); живое применение (секунды/погода выкл → зоны пусты);
#     частота 30 сек → localStorage; «Тест сообщения» → «пейджер»;
#     «Сброс» → умолчания.
#  C) БАГ 1 (РЕГРЕССИЯ): реальный клик ‹ → календарь ОСТАЁТСЯ открыт
#     (composedPath); клик мимо → закрывается.
#  D) БАГ 2 (РЕГРЕССИЯ): шторка «Итоги учёта» открыта + календарь →
#     шапка z 20, elementFromPoint в центре календаря — ВНУТРИ
#     #wsLcdWrap (не бортик шторки); закрытие календаря → z обратно.
#     То же для «Обозначений».
#  E) СВЕТЛАЯ тема: утопленник светлый, панель настроек в светлой
#     теме, скриншот.
#  F) 1024: панель настроек + календарь не вылезают за левый край.
#  G) 0 JS-ошибок; скриншоты в download/kip8test-task531/.
import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task531')
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


# --- Данные мока (как в task530) ---
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
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
WEATHER = {'temp': -12, 'phenomenon': 'Слабый снег', 'cloud': 8,
           'wind': 4, 'windDir': 'северо-западный', 'pressure': 759,
           'humidity': 86.2, 'obsLocal': '15 октября, 13:00',
           'source': 'meteoinfo.ru', 'fetched': '2026-10-15T13:10:00Z'}


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
        return {'ok': True, 'data': WEATHER}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# --- JS-пробы ---
# эффект экрана/рамки + геометрия попапов
STYLE_JS = r"""(() => {
    const cv = document.getElementById('wsLcdCanvas');
    const btn = document.getElementById('wsLcdClock');
    if (!cv || !btn) return {missing: true};
    const csCv = getComputedStyle(cv), csBtn = getComputedStyle(btn);
    return {
        cvShadow: csCv.boxShadow, btnShadow: csBtn.boxShadow,
        cvRadius: csCv.borderRadius, btnRadius: csBtn.borderRadius};})"""

# компоновка по _grid: нижняя линия, секунды, двоеточие, день
LAYOUT_JS = r"""(() => {
    const WsL = window.WsLcdClock;
    if (!WsL || !WsL._grid) return {missing: true};
    const g = WsL._grid;
    const sum = (r, c1, c2) => { let s = 0;
        for (let c = c1; c <= c2; c++) s += g[r][c]; return s; };
    // колонки двоеточия: в ЯЧЕЙКЕ двоеточия (14..19) горят только 16..17
    const colonCols = [];
    for (let c = 14; c <= 19; c++) {
        for (let r = 4; r <= 12; r++) if (g[r][c]) { colonCols.push(c); break; }
    }
    // границы слова дня: первая/последняя колонка с сегментами в зоне 42..110
    let dayA = -1, dayB = -1;
    for (let c = 42; c <= 110; c++) {
        for (let r = 4; r <= 12; r++) if (g[r][c]) { if (dayA < 0) dayA = c; dayB = c; break; }
    }
    let row13 = 0;
    for (let c = 0; c < 205; c++) row13 += g[13][c];
    return {
        secBottom: sum(12, 35, 41), secTop: sum(8, 35, 41),
        secAbove: sum(7, 35, 41), secBelow: sum(13, 35, 41),
        timeBottom: sum(12, 1, 32), dateBottom: sum(12, 111, 170),
        iconBottom: sum(12, 172, 179), row13: row13,
        colonCols: colonCols.join(','),
        dayA: dayA, dayB: dayB,
        dayGapL: (dayA > 0 ? dayA - 42 : -1), dayGapR: (dayB > 0 ? 110 - dayB : -1)};})"""

# ровная сетка (лёгкая версия пиксельного анализа 530)
GRID_JS = r"""(() => {
    const cv = document.getElementById('wsLcdCanvas');
    const WsL = window.WsLcdClock;
    if (!cv || !WsL || !WsL._grid) return {missing: true};
    const pitch = WsL._pitch;
    cv.style.setProperty('--ws-lcd-glow', 'none');
    WsL.draw();
    const ctx = cv.getContext('2d');
    const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
    const bg = [d[0], d[1], d[2]];
    const isBg = (x, y) => {
        const i = (y * cv.width + x) * 4;
        return Math.abs(d[i] - bg[0]) < 40 && Math.abs(d[i+1] - bg[1]) < 40 &&
               Math.abs(d[i+2] - bg[2]) < 40; };
    const widths = {};
    let runs = 0, badStart = 0;
    for (let r = 4; r <= 12; r++) {
        const y = r * pitch;
        if (y >= cv.height) continue;
        let c = 0;
        while (c < WsL.COLS) {
            if (!isBg(c * pitch, y)) {
                const start = c * pitch;
                if (start % pitch !== 0) badStart++;
                let w = 0;
                while (start + w < cv.width && !isBg(start + w, y)) w++;
                widths[w] = (widths[w] || 0) + 1;
                runs++;
                c += Math.ceil((w + 1) / pitch);
            } else c++;
        }
    }
    cv.style.removeProperty('--ws-lcd-glow');
    WsL.draw();
    return {pitch: pitch, w: cv.width, h: cv.height, runs: runs,
            badStart: badStart, distinctW: Object.keys(widths).length,
            widths: widths};})"""

# геометрия попапов (календарь + настройки) и взаимное положение
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
            calLeft: c.left, calRight: c.right, calTop: c.top, calW: c.width,
            setLeft: s.left, setRight: s.right, setTop: s.top, setW: s.width,
            gap: c.left - s.right,
            sameTop: Math.abs(c.top - s.top) < 2,
            insideViewport: s.left >= 0};})"""

# z-фикс шторок: z-index шапки + elementFromPoint в центре календаря
ZFIX_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    const header = document.querySelector(
        '#page-work-schedule .page-inline-header');
    if (!cal || !header) return {missing: true};
    const c = cal.getBoundingClientRect();
    const cx = c.left + c.width / 2, cy = c.top + Math.min(c.height / 2, 120);
    const el = document.elementFromPoint(cx, cy);
    return {
        z: getComputedStyle(header).zIndex,
        hitWrap: !!(el && el.closest && el.closest('#wsLcdWrap')),
        hitTag: el ? (el.tagName + '.' + (el.className || '')).slice(0, 60) : ''};})"""


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
                "localStorage.setItem('kip8test:kip8_session_token','bc-t531');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
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
        print('== A: ДЕСКТОП тёмная (DPR 2) — утопленник, нижняя линия, центрирование ==')
        ctx = make_ctx('dark', 1280, 720, dpr=2.0)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1200)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        st = page.evaluate(STYLE_JS)
        check('A: экран УТОПЛЕН — тень-колодец 0px 2px 3px inset',
              '0px 2px 3px 0px inset' in (st.get('cvShadow') or ''), st)
        check('A: экран — прямые углы', st.get('cvRadius') == '0px', st)
        check('A: рамка-ВЫСТУП сохранена — блик 0px 1px 0px inset',
              '0px 1px 0px 0px inset' in (st.get('btnShadow') or ''), st)

        lay = page.evaluate(LAYOUT_JS)
        check('A: НИЖНЯЯ ЛИНИЯ ЕДИНА (ряд 12): секунды', lay.get('secBottom', 0) > 0, lay)
        check('A: НИЖНЯЯ ЛИНИЯ: время', lay.get('timeBottom', 0) > 0, lay)
        check('A: НИЖНЯЯ ЛИНИЯ: дата', lay.get('dateBottom', 0) > 0, lay)
        check('A: НИЖНЯЯ ЛИНИЯ: иконка погоды', lay.get('iconBottom', 0) > 0, lay)
        check('A: ниже нижней линии (ряд 13) ПУСТО', lay.get('row13', 1) == 0, lay)
        check('A: секунды ВНИЗУ — верх на ряду 8', lay.get('secTop', 0) > 0, lay)
        check('A: над секундами (ряд 7) пусто', lay.get('secAbove', 1) == 0, lay)
        check('A: ДВОЕТОЧИЕ — колонки 16,17 (центр)',
              lay.get('colonCols') == '16,17', lay)
        check('A: ДЕНЬ по центру зоны — зазоры равны',
              lay.get('dayGapL', -1) >= 0 and
              abs(lay.get('dayGapL', -1) - lay.get('dayGapR', -1)) <= 1, lay)

        gr = page.evaluate(GRID_JS)
        check('A: сетка РОВНАЯ — pitch целый', gr.get('pitch', 0) >= 2, gr)
        check('A: канвас кратен матрице (205/17 × pitch)',
              gr.get('w', 0) == 205 * gr.get('pitch', 0) and
              gr.get('h', 0) == 17 * gr.get('pitch', 0), gr)
        check('A: все сегменты ОДИНАКОВОЙ стороны (одна ширина)',
              gr.get('distinctW', 9) == 1, gr)
        check('A: начала сегментов в решётке pitch', gr.get('badStart', 9) == 0, gr)
        shot(page, '01-dark-clock.png')

        # ==============================================================
        print('== B: НАСТРОЙКИ — панель слева от календаря, живое применение ==')
        page.click('#wsLcdClock')
        page.wait_for_timeout(400)
        pp = page.evaluate(POPUP_JS)
        check('B: календарь ОТКРЫТ', pp.get('calHidden') is False and
              pp.get('calVis') != 'none', pp)
        check('B: панель настроек ОТКРЫТА', pp.get('setHidden') is False and
              pp.get('setVis') != 'none', pp)
        check('B: панель СЛЕВА от календаря (правый край < левый край календаря)',
              pp.get('setRight', 1) < pp.get('calLeft', 0) and
              pp.get('gap', -1) >= 0, pp)
        check('B: панель и календарь на ОДНОЙ линии сверху',
              pp.get('sameTop') is True, pp)
        check('B: панель в пределах экрана', pp.get('insideViewport') is True, pp)
        check('B: ширина панели ~252px', 240 <= pp.get('setW', 0) <= 265, pp)
        shot(page, '02-dark-popup.png')

        html_set = page.evaluate(
            "document.getElementById('wsLcdSet').innerHTML")
        for t in ['Настройки информера', 'Секунды', 'День недели',
                  'Погода Кемерово', 'Частота', 'Инструктажи и мероприятия',
                  'Отпуска', 'Обновление', 'Тест сообщения', 'Сброс']:
            check('B: пункт «%s»' % t, t in html_set)

        # живое применение: секунды выкл → зона пуста
        page.click("#wsLcdSet input[onchange*=\"'sec'\"]")
        page.wait_for_timeout(300)
        z = page.evaluate(
            "(() => { const g = window.WsLcdClock._grid; let s = 0;"
            " for (let r = 0; r < 17; r++) for (let c = 35; c <= 43; c++)"
            " s += g[r][c]; return s; })()")
        check('B: секунды ВЫКЛ — зона секунд пуста', z == 0, z)
        # погода выкл → правая часть пуста
        page.click("#wsLcdSet input[onchange*=\"'weather'\"]")
        page.wait_for_timeout(300)
        z = page.evaluate(
            "(() => { const g = window.WsLcdClock._grid; let s = 0;"
            " for (let r = 0; r < 17; r++) for (let c = 171; c < 205; c++)"
            " s += g[r][c]; return s; })()")
        check('B: погода ВЫКЛ — иконки/температуры нет', z == 0, z)
        # частота 30 сек → localStorage
        page.select_option("#wsLcdSet select", '30')
        page.wait_for_timeout(300)
        saved = page.evaluate(
            "localStorage.getItem('kip8_ws_lcd_set_v1') || ''")
        check('B: частота 30 сек записана в localStorage',
              '"feedInt":30' in saved, saved)
        # день выкл → зона дня пуста
        page.click("#wsLcdSet input[onchange*=\"'day'\"]")
        page.wait_for_timeout(300)
        z = page.evaluate(
            "(() => { const g = window.WsLcdClock._grid; let s = 0;"
            " for (let r = 0; r < 17; r++) for (let c = 44; c <= 110; c++)"
            " s += g[r][c]; return s; })()")
        check('B: день ВЫКЛ — зона дня пуста', z == 0, z)
        shot(page, '03-dark-settings-off.png')
        # Сброс → умолчания
        page.click("#wsLcdSet button:has-text('Сброс')")
        page.wait_for_timeout(300)
        z = page.evaluate(
            "(() => { const g = window.WsLcdClock._grid; let s = 0;"
            " for (let r = 0; r < 17; r++) for (let c = 35; c <= 43; c++)"
            " s += g[r][c]; return s; })()")
        check('B: СБРОС — секунды снова на экране', z > 0, z)
        saved = page.evaluate(
            "localStorage.getItem('kip8_ws_lcd_set_v1')")
        check('B: СБРОС — хранилище очищено', saved is None, saved)
        # Тест сообщения → «пейджер»
        page.click("#wsLcdSet button:has-text('Тест сообщения')")
        page.wait_for_timeout(300)
        msg = page.evaluate(
            "(window.WsLcdClock._msg && window.WsLcdClock._msg.pages[0][0]) || ''")
        check('B: ТЕСТ сообщения — «пейджер» показывает ТЕСТ',
              str(msg).find('ТЕСТ') == 0, msg)
        page.wait_for_timeout(6500)     # тест гаснет (6 c)
        shot(page, '04-dark-testmsg.png')

        # ==============================================================
        print('== C: БАГ 1 — переключение месяцев НЕ закрывает календарь ==')
        title0 = page.evaluate(
            "document.querySelector('.ws-lcd-cal-title').textContent")
        page.click('.ws-lcd-cal-nav[aria-label="Предыдущий месяц"]')
        page.wait_for_timeout(350)
        st1 = page.evaluate(
            "({hidden: document.getElementById('wsLcdCal').hidden,"
            "  vis: getComputedStyle(document.getElementById('wsLcdCal')).display,"
            "  title: document.querySelector('.ws-lcd-cal-title').textContent,"
            "  open: window.WsLcdClock._calOpen})")
        check('C: клик ‹ — календарь ОТКРЫТ (баг 1 исправлен)',
              st1.get('hidden') is False and st1.get('vis') != 'none' and
              st1.get('open') is True, st1)
        check('C: месяц сменился', st1.get('title') != title0,
              (title0, st1.get('title')))
        page.click('.ws-lcd-cal-nav[aria-label="Следующий месяц"]')
        page.wait_for_timeout(350)
        st2 = page.evaluate("window.WsLcdClock._calOpen")
        check('C: клик › — календарь ПО-ПРЕЖНЕМУ открыт', st2 is True, st2)
        # «Сегодня» тоже не закрывает
        page.click('.ws-lcd-cal-today')
        page.wait_for_timeout(350)
        st3 = page.evaluate("window.WsLcdClock._calOpen")
        check('C: «Сегодня» — календарь открыт', st3 is True, st3)
        shot(page, '05-dark-cal-nav.png')   # снят при ОТКРЫТОМ календаре
        # клик мимо — закрывает
        page.click('#page-work-schedule .page-inline-header-title')
        page.wait_for_timeout(300)
        st4 = page.evaluate("window.WsLcdClock._calOpen")
        check('C: клик мимо — календарь ЗАКРЫЛСЯ', st4 is False, st4)

        # ==============================================================
        print('== D: БАГ 2 — шторки итогов/обозначений НЕ накрывают календарь ==')
        # базовый z шапки (попап закрыт)
        z0 = page.evaluate(
            "getComputedStyle(document.querySelector("
            "'#page-work-schedule .page-inline-header')).zIndex")
        # открыть «Итоги учёта» + календарь
        page.click('#wsTotalsBtn')
        page.wait_for_timeout(700)
        page.click('#wsLcdClock')
        page.wait_for_timeout(400)
        zf = page.evaluate(ZFIX_JS)
        check('D: шапка поднята z 20 при открытом попапе',
              zf.get('z') == '20', zf)
        check('D: клик в центр календаря попадает ВНУТРЬ попапа (не в бортик)',
              zf.get('hitWrap') is True, zf)
        shot(page, '06-dark-totals-drawer.png')
        # закрыть календарь → z обратно
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        z2 = page.evaluate(
            "getComputedStyle(document.querySelector("
            "'#page-work-schedule .page-inline-header')).zIndex")
        check('D: календарь закрыт — z шапки вернулся (5)', z2 == '5', z2)
        page.click('#wsTotalsBtn')       # закрыть шторку
        page.wait_for_timeout(600)

        # «Обозначения»
        page.click('#wsLegendBtn')
        page.wait_for_timeout(700)
        page.click('#wsLcdClock')
        page.wait_for_timeout(400)
        zf2 = page.evaluate(ZFIX_JS)
        check('D: ОБОЗНАЧЕНИЯ открыты — шапка z 20', zf2.get('z') == '20', zf2)
        check('D: ОБОЗНАЧЕНИЯ — календарь поверх (клик внутри попапа)',
              zf2.get('hitWrap') is True, zf2)
        shot(page, '07-dark-legend-drawer.png')
        # кроп зоны пересечения: правый край календаря + левый край шторки
        # (шеврон .ws-lg-chv сидит на левом краю шторки — проверяем, что
        # он НЕ рисуется ПОВЕРХ дней календаря)
        try:
            cb = page.locator('#wsLcdCal').bounding_box()
            if cb:
                clip = {'x': max(0, cb['x'] + cb['width'] - 90),
                        'y': cb['y'],
                        'width': min(130, 1280 - max(0, cb['x'] + cb['width'] - 90)),
                        'height': min(cb['height'], 300)}
                page.screenshot(path=os.path.join(
                    SHOT_DIR, '07b-legend-crop.png'), clip=clip)
        except Exception as e:
            print('  (кроп 07b не снят: %s)' % e)
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)
        page.click('#wsLegendBtn')
        page.wait_for_timeout(500)

        check('A/B/C/D: 0 JS-ошибок', len(js_errors) == 0, js_errors[:4])
        ctx.close()

        # ==============================================================
        print('== E: СВЕТЛАЯ тема — утопленник, панель, скриншот ==')
        ctx2 = make_ctx('light', 1280, 720, dpr=1.0)
        page2 = ctx2.new_page()
        errs2 = []
        page2.on('pageerror', lambda e: errs2.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(1200)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        st2 = page2.evaluate(STYLE_JS)
        check('E: экран утоплен в светлой теме (0px 2px 3px inset)',
              '0px 2px 3px 0px inset' in (st2.get('cvShadow') or ''), st2)
        page2.click('#wsLcdClock')
        page2.wait_for_timeout(400)
        pp2 = page2.evaluate(POPUP_JS)
        check('E: панель настроек в светлой теме открыта',
              pp2.get('setHidden') is False and pp2.get('setVis') != 'none', pp2)
        bg2 = page2.evaluate(
            "getComputedStyle(document.getElementById('wsLcdSet')).backgroundColor")
        check('E: панель светлый фон (rgb 251 248 240)',
              '251' in (bg2 or '') and '248' in (bg2 or '') and '240' in (bg2 or ''), bg2)
        shot(page2, '08-light-popup.png')
        page2.keyboard.press('Escape')
        check('E: 0 JS-ошибок (светлая)', len(errs2) == 0, errs2[:4])
        ctx2.close()

        # ==============================================================
        print('== F: 1024 — панель + календарь в пределах экрана ==')
        ctx3 = make_ctx('dark', 1024, 720, dpr=1.0)
        page3 = ctx3.new_page()
        page3.on('dialog', lambda dg: dg.accept())
        page3.goto('http://127.0.0.1:%d/index.html' % PORT)
        page3.wait_for_timeout(1200)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2500)
        page3.click('#wsLcdClock')
        page3.wait_for_timeout(400)
        pp3 = page3.evaluate(POPUP_JS)
        check('F: 1024 — панель не вылезает за левый край',
              pp3.get('insideViewport') is True, pp3)
        check('F: 1024 — календарь в пределах экрана',
              pp3.get('calRight', 9999) <= 1024, pp3)
        shot(page3, '09-1024-popup.png')
        ctx3.close()

    print()
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
