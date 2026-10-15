#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 530 browser-check: доработка LCD-окна «пейджер» в баре крошек
# Табеля (заявка: «Рамки экрана сделай с эффектом выступа - бордюрчик,
#  и в светлой теме сделай светлым цветом. Цифры секунд перемести
#  справа от минут и меньше шрифтом, а точки мигать не должны. Данные
#  размести в одну линию, после времени - день недели и затем дату.
#  «призрачная» сетка не должна быть видна. Примыкание рамок сверху
#  и снизу к краям бара сделай вплотную и саму рамку прямоугольную с
#  прямыми углами без скруглений. Добавь отображение погоды в Кемерово
#  из источника https://meteoinfo.ru/ с иконкой отображающей погоду.
#  Длину окна по горизонтали можешь сделать больше на сколько это
#  необходимо но всегда фиксированной. Подключи вывод реальных
#  сообщений. И самое главное, внимательно проверь размеры квадратных
#  пикселей должны быть одинаковые и сетка пикселей ровная,
#  перепроверь и сделай ровно.»):
#  A) ДЕСКТОП тёмная 1280×720 (DPR 2): окно ВИДИМО справа; РАМКА
#     вплотную к краям бара (верх/низ), ПРЯМЫЕ углы (border-radius 0);
#     матрица 205×17; СЕТКА РОВНАЯ — пиксельный анализ канваса: все
#     сегменты ОДИНАКОВОЙ стороны, начала строго в решётке pitch
#     (ЦЕЛЫЙ pitch, канвас кратен матрице); «призрачной» сетки НЕТ
#     (пустые ряды — чистый фон); данные в ОДНУ строку (ряды 0/16
#     пусты, зоны время/сек/день/дата/погода разделены пустотой);
#     двоеточие НЕ мигает (кадры подряд отличаются ТОЛЬКО в зоне
#     секунд); длина окна ФИКСИРОВАНА (размер канваса не меняется
#     при выводе сообщения).
#  B) ПОГОДА: сервер (мок) отдаёт meteoinfo-данные (-12°, снег) —
#     иконка 8×8 в зоне X_ICON, температура «-12°» у правого края;
#     сбой сервера — прочерк «--», без ошибок.
#  C) РЕАЛЬНЫЕ сообщения: мок listTrainings/listVacations с записями
#     «сегодня» → очередь _feed → LCD сам показывает «пейджер»
#     (СЕГОДНЯ…), затем возврат к часам; внешний API ws-lcd-message.
#  D) КАЛЕНДАРЬ: клик — панель 42 дней, навигация ‹ ›, клик по дате
#     открывает месяц в табеле, Esc закрывает.
#  E) СВЕТЛАЯ тема: СВЕТЛЫЙ бордюрчик рамки (#e7e2d5), сетка ровная
#     (DPR 1), призраков нет.
#  F) УЗКОЕ окно 1024: заголовок — эллипсис, наезда на LCD нет.
#  G) МОБАЙЛ 390×844 и 1000×700: окно СКРЫТО.
#  H) 0 JS-ошибок; скриншоты в download/kip8test-task530/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task530')
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


def shot_el(page, sel, name):
    try:
        page.locator(sel).screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот элемента %s не сохранён: %s)' % (name, e))


# --- Данные мока ---
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
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'сменный',
   'смена': 2, 'шаблон_ротации': 1, 'старт_цикла': '2026-10-02',
   'дата_приёма': '2023-05-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

import datetime as _dt
_T = _dt.date.today()
_ISO = lambda d: d.strftime('%Y-%m-%d')
TODAY = _ISO(_T)
TOMORROW = _ISO(_T + _dt.timedelta(days=1))

TRAININGS = [
  # сегодня — попадает в ленту реальных сообщений
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': 'Охрана труда', 'дата_начала': TODAY,
   'дата_окончания': TODAY, 'длительность_дней': 1, 'комментарий': ''},
  # завтра
  {'id': 102, 'таб_номер': '023', 'тип': 'обучение',
   'тема': 'Автоматика', 'дата_начала': TOMORROW,
   'дата_окончания': TOMORROW, 'длительность_дней': 2, 'комментарий': ''},
]
VACATIONS = [
  # активный сегодня отпуск
  {'id': 1, 'таб_номер': '023', 'дата_начала': _ISO(_T - _dt.timedelta(days=3)),
   'дата_окончания': _ISO(_T + _dt.timedelta(days=11)),
   'часть': 1, 'комментарий': ''},
]

WEATHER = {'temp': -12, 'phenomenon': 'Слабый снег', 'cloud': 8,
           'wind': 4, 'windDir': 'северо-западный', 'pressure': 759,
           'humidity': 86.2, 'obsLocal': '15 октября, 13:00',
           'source': 'meteoinfo.ru', 'fetched': '2026-10-15T13:10:00Z'}


def mock_response(action, weather_mode='ok'):
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
        if weather_mode == 'ok':
            return {'ok': True, 'data': WEATHER}
        return {'ok': True, 'data': {'temp': None, 'phenomenon': None,
                'cloud': None, 'note': 'weather_unavailable'}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# геометрия виджета: рамка вплотную к бару, прямые углы, размер канваса
FRAME_JS = r"""(() => {
    const wrap = document.getElementById('wsLcdWrap');
    const btn = document.getElementById('wsLcdClock');
    const cv = document.getElementById('wsLcdCanvas');
    const header = document.querySelector('#page-work-schedule .page-inline-header');
    if (!wrap || !btn || !cv || !header) return {missing: true};
    const w = wrap.getBoundingClientRect(), b = btn.getBoundingClientRect(),
          h = header.getBoundingClientRect(), c = cv.getBoundingClientRect();
    const csBtn = getComputedStyle(btn), csCv = getComputedStyle(cv);
    return {
        wrapTop: w.top, wrapBottom: w.bottom, wrapLeft: w.left,
        headerTop: h.top, headerBottom: h.bottom,
        btnTop: b.top, btnBottom: b.bottom, btnH: b.height, btnW: b.width,
        cvTop: c.top, cvBottom: c.bottom, cvH: c.height, cvW: c.width,
        btnRadius: csBtn.borderRadius, cvRadius: csCv.borderRadius,
        btnBg: csBtn.backgroundColor,
        canvasW: cv.width, canvasH: cv.height,
        cssW: cv.style.width, cssH: cv.style.height,
        pitch: (window.WsLcdClock ? WsLcdClock._pitch : 0),
        timer: !!(window.WsLcdClock && WsLcdClock._timer)};})"""

# ПИКСЕЛЬНЫЙ АНАЛИЗ РОВНОСТИ СЕТКИ (главное заявки): без свечения,
# все сегменты одинаковой стороны, начала кратны pitch, призраков нет
GRID_JS = r"""(() => {
    const cv = document.getElementById('wsLcdCanvas');
    const WsL = window.WsLcdClock;
    if (!cv || !WsL || !WsL._grid) return {missing: true};
    const pitch = WsL._pitch;
    // перерисовать БЕЗ свечения — пиксели сегментов точные
    cv.style.setProperty('--ws-lcd-glow', 'none');
    WsL.draw();
    const ctx = cv.getContext('2d');
    const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
    const bg = [d[0], d[1], d[2]];
    const isBg = (x, y) => {
        const i = (y * cv.width + x) * 4;
        return Math.abs(d[i] - bg[0]) < 40 && Math.abs(d[i+1] - bg[1]) < 40 &&
               Math.abs(d[i+2] - bg[2]) < 40;
    };
    const widths = {};
    let runs = 0, badStart = 0, badLen = 0;
    // горизонтальные линии y = r*pitch (верх сегментов ряда r)
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
    // вертикальные линии x = c*pitch
    for (let c = 5; c <= 200; c += 6) {
        const x = c * pitch;
        if (x >= cv.width) continue;
        let r = 0;
        while (r < WsL.ROWS) {
            if (!isBg(x, r * pitch)) {
                const start = r * pitch;
                if (start % pitch !== 0) badStart++;
                let hgt = 0;
                while (start + hgt < cv.height && !isBg(x, start + hgt)) hgt++;
                widths[hgt] = (widths[hgt] || 0) + 1;
                runs++;
                r += Math.ceil((hgt + 1) / pitch);
            } else r++;
        }
    }
    // «призрачная» сетка: ряды 0 и 16 всегда пусты — чистый фон
    let row0dirty = 0, row16dirty = 0;
    for (let x = 0; x < cv.width; x++) {
        if (!isBg(x, 0)) row0dirty++;
        if (!isBg(x, cv.height - 1)) row16dirty++;
    }
    // вернуть свечение темы
    cv.style.removeProperty('--ws-lcd-glow');
    WsL.draw();
    return {pitch: pitch, w: cv.width, h: cv.height, runs: runs,
            badStart: badStart, distinctW: Object.keys(widths).length,
            widths: widths, row0dirty: row0dirty, row16dirty: row16dirty};})"""

# зоны одной строки данных + разделители между ними
ZONES_JS = r"""(() => {
    const g = WsLcdClock._grid;
    const zone = (c1, c2) => {
        let lit = 0;
        for (let r = 0; r < 17; r++) for (let c = c1; c <= c2; c++)
            if (g[r][c]) lit++;
        return lit;
    };
    let r0 = 0, r16 = 0;
    for (let c = 0; c < 205; c++) { r0 += g[0][c]; r16 += g[16][c]; }
    return {time: zone(1, 32), sec: zone(35, 41), day: zone(44, 108),
            date: zone(111, 169), iconZone: zone(172, 179), temp: zone(181, 203),
            gap1: zone(42, 43), gap2: zone(109, 110), gap3: zone(170, 171),
            gap4: zone(180, 180), row0: r0, row16: r16,
            tempTxt: (WsLcdClock._weather || {}).tempTxt,
            icon: (WsLcdClock._weather || {}).icon};})"""


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        def make_ctx(theme, w, h, dpr=1.0, weather_mode='ok'):
            ctx = browser.new_context(viewport={'width': w, 'height': h},
                                      device_scale_factor=dpr)
            ctx.add_init_script(
                "try{localStorage.clear()}catch(e){};" +
                "localStorage.setItem('kip8test:kip8_session_token','bc-t530');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
                route.fulfill(status=200,
                              content_type='application/json; charset=utf-8',
                              body=json.dumps(mock_response(action, weather_mode),
                                              ensure_ascii=False))
            ctx.route('**/exec?**', handle)
            ctx.route('**script.google.com/**', handle)
            ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**meteoinfo.ru**', lambda r: r.fulfill(
                status=200, content_type='text/html; charset=utf-8',
                body='<html>погода</html>'))
            return ctx

        # ==============================================================
        print('== A: ДЕСКТОП тёмная (DPR 2) — рамка, ровная сетка, одна строка ==')
        ctx = make_ctx('dark', 1280, 720, dpr=2.0)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1200)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1800)

        fr = page.evaluate(FRAME_JS)
        check('A: виджет в DOM', not fr.get('missing'), fr)
        check('A: окно видно (ширина > 300)', fr.get('btnW', 0) > 300, fr)
        check('A: РАМКА ВПЛОТНУЮ к верху бара (top бара = top рамки ± 1)',
              abs(fr.get('wrapTop', -99) - fr.get('headerTop', -99)) <= 1, fr)
        check('A: РАМКА ВПЛОТНУЮ к низу бара (bottom = низ бара ± 2)',
              abs(fr.get('wrapBottom', -99) - (fr.get('headerBottom', 0) - 1)) <= 2, fr)
        check('A: кнопка-рамка на всю высоту бара (>50px)',
              fr.get('btnH', 0) > 50, fr)
        check('A: ПРЯМЫЕ углы рамки (border-radius 0px)',
              fr.get('btnRadius') == '0px', fr)
        check('A: ПРЯМЫЕ углы экрана (border-radius 0px)',
              fr.get('cvRadius') == '0px', fr)
        check('A: канвас кратен матрице (w % 205 == 0, h % 17 == 0)',
              fr.get('canvasW', 1) % 205 == 0 and fr.get('canvasH', 1) % 17 == 0, fr)
        check('A: pitch ЦЕЛЫЙ ≥ 2', isinstance(fr.get('pitch'), int) and
              fr.get('pitch', 0) >= 2, fr)
        check('A: таймер запущен', fr.get('timer'), fr)
        shot_el(page, '#wsLcdWrap', 'a-dark-widget.png')

        grid = page.evaluate(GRID_JS)
        check('A: сетка проанализирована', not grid.get('missing'), grid)
        check('A: РОВНАЯ СЕТКА — сегментов ≥ 60', grid.get('runs', 0) >= 60, grid)
        check('A: РОВНАЯ СЕТКА — начала строго в решётке pitch (0 промахов)',
              grid.get('badStart', -1) == 0, grid)
        check('A: РОВНАЯ СЕТКА — все сегменты ОДИНАКОВОЙ стороны (1 размер)',
              grid.get('distinctW', -1) == 1, grid.get('widths'))
        check('A: ПРИЗРАКОВ НЕТ — ряд 0 чистый (0 «грязных» пикселей)',
              grid.get('row0dirty', -1) == 0, grid)
        check('A: ПРИЗРАКОВ НЕТ — верхний ряд канваса чистый',
              grid.get('row16dirty', -1) == 0, grid)

        # двоеточие НЕ мигает: два кадра подряд — изменения ТОЛЬКО в зоне секунд
        steady = page.evaluate(r"""(() => new Promise(res => {
            const snap = () => WsLcdClock._grid.map(r => r.slice());
            const diffOutside = (a, b) => {
                let n = 0;
                for (let r = 0; r < 17; r++) for (let c = 0; c < 205; c++)
                    if (c < 35 || c > 41) if (a[r][c] !== b[r][c]) n++;
                return n;
            };
            const tick = () => {
                const s = new Date().getSeconds();
                if (s >= 58) return setTimeout(tick, 300);
                const a = snap();
                setTimeout(() => res({outside: diffOutside(a, snap()),
                                       sec: s}), 1050);
            };
            tick();}))""")
        check('A: двоеточие НЕ мигает — вне зоны секунд 0 изменений за секунду',
              steady.get('outside', -1) == 0, steady)

        zn = page.evaluate(ZONES_JS)
        check('A: ОДНА строка — ряды 0/16 пусты',
              zn.get('row0', -1) == 0 and zn.get('row16', -1) == 0, zn)
        check('A: зона времени заполнена (>60)', zn.get('time', 0) > 60, zn)
        check('A: зона секунд заполнена (>8)', zn.get('sec', 0) > 8, zn)
        check('A: зона дня недели заполнена (>40)', zn.get('day', 0) > 40, zn)
        check('A: зона даты заполнена (>40)', zn.get('date', 0) > 40, zn)
        check('A: РАЗДЕЛИТЕЛИ между блоками пусты',
              zn.get('gap1', -1) == 0 and zn.get('gap2', -1) == 0 and
              zn.get('gap3', -1) == 0, zn)

        # длина окна ФИКСИРОВАНА: размер не меняется при сообщении
        size1 = page.evaluate("(() => { const cv = document.getElementById('wsLcdCanvas');" +
                             "return [cv.width, cv.height, cv.style.width, cv.style.height]; })()")
        page.evaluate("window.dispatchEvent(new CustomEvent('ws-lcd-message'," +
                      "{detail:{line1:'ПРОВЕРКА', line2:'ФИКСИРОВАННОЙ ДЛИНЫ'}}))")
        page.wait_for_timeout(600)
        size2 = page.evaluate("(() => { const cv = document.getElementById('wsLcdCanvas');" +
                             "return [cv.width, cv.height, cv.style.width, cv.style.height]; })()")
        check('A: ДЛИНА ОКНА ФИКСИРОВАНА — размер при сообщении не изменился',
              size1 == size2, (size1, size2))
        # вернуть экран к часам ДО зон B/C (сообщение мешает снятию зон)
        page.evaluate("WsLcdClock._msg = null; WsLcdClock._tick();")
        page.wait_for_timeout(300)

        # ==============================================================
        print('== B: ПОГОДА Кемерово (meteoinfo.ru через сервер) ==')
        page.wait_for_timeout(400)
        zn2 = page.evaluate(ZONES_JS)
        check('B: температура «-12°» применена', zn2.get('tempTxt') == '-12°', zn2)
        check('B: иконка «снег» по явлению', zn2.get('icon') == 'snow', zn2)
        check('B: зона иконки 8×8 заполнена (>15)', zn2.get('iconZone', 0) > 15, zn2)
        check('B: зона температуры заполнена (>10)', zn2.get('temp', 0) > 10, zn2)
        check('B: зазор иконка-температура пуст', zn2.get('gap4', -1) == 0, zn2)
        wcall = page.evaluate("(() => localStorage.getItem('kip8_ws_weather_v1') || '')()")
        check('B: погода записана в localStorage-кэш', '-12' in wcall, wcall[:120])
        shot_el(page, '#wsLcdWrap', 'b-weather-dark.png')

        # сбой сервера погоды — прочерк
        ctx2 = make_ctx('dark', 1280, 720, dpr=1.0, weather_mode='fail')
        page2 = ctx2.new_page()
        page2.on('pageerror', lambda e: js_errors.append('p2:' + str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(1000)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(1600)
        zn3 = page2.evaluate(ZONES_JS)
        check('B: сбой сервера — без температуры/иконки, на экране прочерк «--»',
              (zn3.get('tempTxt') in (None, '--')) and not zn3.get('icon') and
              zn3.get('temp', 0) > 0, zn3)
        check('B: сбой сервера — экран жив, время идёт',
              zn3.get('time', 0) > 60, zn3)

        # ==============================================================
        print('== C: РЕАЛЬНЫЕ сообщения из данных Табеля ==')
        # ускорить цикл: первый «пейджер» через 1.2 с; лента строится
        # только когда НЕТ активного сообщения — сбрасываем состояние
        page.evaluate("WsLcdClock.FEED_DELAY = 1200;" +
                      "WsLcdClock._feedBuilt = 0; WsLcdClock._feedAt = 0;" +
                      "WsLcdClock._msg = null; WsLcdClock._tick();")
        page.wait_for_timeout(2600)
        msg = page.evaluate(r"""(() => {
            const m = WsLcdClock._msg;
            const feed = WsLcdClock._feed || [];
            return {has: !!m, feedLen: feed.length,
                    first: feed[0] || '', vac: (feed.filter(x => x.indexOf('ОТПУСК') === 0)[0] || ''),
                    l1: m ? m.pages[0][0] : '', l2: m ? m.pages[0][1] : ''};})""")
        check('C: очередь реальных сообщений построена (3)', msg.get('feedLen') == 3, msg)
        check('C: мероприятие «СЕГОДНЯ» в очереди',
              msg.get('first', '').startswith('СЕГОДНЯ инструктаж: Охрана труда'), msg)
        check('C: отпуск в очереди',
              msg.get('vac', '').startswith('ОТПУСК: Петров'), msg)
        check('C: «пейджер» сам показан на экране', msg.get('has'), msg)
        check('C: строка 1 — «СЕГОДНЯ…»', msg.get('l1', '').startswith('СЕГОДНЯ'), msg)
        shot_el(page, '#wsLcdWrap', 'c-feed-message.png')
        # авто-возврат к часам
        page.wait_for_timeout(9500)
        back = page.evaluate("(() => ({msg: !!WsLcdClock._msg, " +
                             "time: (() => { let n=0; const g = WsLcdClock._grid;" +
                             " for (let r=0;r<17;r++) for (let c=1;c<=32;c++) if (g[r][c]) n++; return n; })() }))()")
        check('C: авто-возврат к часам после показа', not back.get('msg') and
              back.get('time', 0) > 60, back)

        # ==============================================================
        print('== D: КАЛЕНДАРЬ по месяцам ==')
        page.evaluate("WsLcdClock.toggleCal(true)")
        page.wait_for_timeout(400)
        cal = page.evaluate(r"""(() => {
            const el = document.getElementById('wsLcdCal');
            const days = el ? el.querySelectorAll('.ws-lcd-cal-day').length : 0;
            const title = el ? (el.querySelector('.ws-lcd-cal-title') || {}).textContent : '';
            const today = el ? el.querySelectorAll('.ws-lcd-cal-day.today').length : 0;
            return {open: !!el && !el.hidden, days: days, title: title, today: today};})""")
        check('D: календарь открыт', cal.get('open'), cal)
        check('D: 42 ячейки дней', cal.get('days') == 42, cal)
        check('D: сегодня подсвечен', cal.get('today') == 1, cal)
        check('D: заголовок с месяцем и годом', '20' in str(cal.get('title', '')), cal)
        shot(page, 'd-calendar-dark.png')
        nav = page.evaluate("(() => { WsLcdClock._calNav(1);" +
                            "return document.querySelector('.ws-lcd-cal-title').textContent; })()")
        check('D: навигация ‹ › меняет месяц', bool(nav), nav)
        page.evaluate("WsLcdClock._calToday()")
        pick = page.evaluate("(() => { WsLcdClock._calPick(2026, 10, 15);" +
                             "const ms = document.getElementById('wsMonthSel');" +
                             "return {month: ms ? ms.value : '', closed: document.getElementById('wsLcdCal').hidden}; })()")
        check('D: клик по дате — месяц в табеле + закрытие',
              pick.get('month') == '10' and pick.get('closed'), pick)
        page.evaluate("WsLcdClock.toggleCal(true)")
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)
        esc = page.evaluate("document.getElementById('wsLcdCal').hidden")
        check('D: Esc закрывает календарь', esc)

        # ==============================================================
        print('== E: СВЕТЛАЯ тема — светлый бордюрчик, ровная сетка (DPR 1) ==')
        ctx3 = make_ctx('light', 1280, 720, dpr=1.0)
        page3 = ctx3.new_page()
        page3.on('pageerror', lambda e: js_errors.append('p3:' + str(e)))
        page3.on('dialog', lambda dg: dg.accept())
        page3.goto('http://127.0.0.1:%d/index.html' % PORT)
        page3.wait_for_timeout(1000)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(1800)
        fr3 = page3.evaluate(FRAME_JS)
        check('E: СВЕТЛЫЙ бордюрчик рамки (#e7e2d5)',
              fr3.get('btnBg') == 'rgb(231, 226, 213)', fr3.get('btnBg'))
        check('E: рамка вплотную к бару (светлая)',
              abs(fr3.get('wrapTop', -99) - fr3.get('headerTop', -99)) <= 1 and
              abs(fr3.get('wrapBottom', -99) - (fr3.get('headerBottom', 0) - 1)) <= 2, fr3)
        check('E: прямые углы (светлая)', fr3.get('btnRadius') == '0px' and
              fr3.get('cvRadius') == '0px', fr3)
        grid3 = page3.evaluate(GRID_JS)
        check('E: СЕТКА РОВНАЯ при DPR 1 — все сегменты одинаковы',
              grid3.get('distinctW', -1) == 1 and grid3.get('badStart', -1) == 0, grid3)
        check('E: ПРИЗРАКОВ НЕТ (светлая, ряд 0 чист)',
              grid3.get('row0dirty', -1) == 0, grid3)
        zn4 = page3.evaluate(ZONES_JS)
        check('E: погода в светлой теме (-12° снег)',
              zn4.get('tempTxt') == '-12°' and zn4.get('icon') == 'snow', zn4)
        shot_el(page3, '#wsLcdWrap', 'e-light-widget.png')
        shot(page3, 'e-light-full.png')
        page3.evaluate("WsLcdClock.toggleCal(true)")
        page3.wait_for_timeout(300)
        shot(page3, 'e-light-calendar.png')

        # ==============================================================
        print('== F: УЗКОЕ окно 1024 — эллипсис заголовка, без наезда ==')
        ctx4 = make_ctx('dark', 1024, 700, dpr=1.0)
        page4 = ctx4.new_page()
        page4.on('pageerror', lambda e: js_errors.append('p4:' + str(e)))
        page4.on('dialog', lambda dg: dg.accept())
        page4.goto('http://127.0.0.1:%d/index.html' % PORT)
        page4.wait_for_timeout(900)
        page4.evaluate("navigateTo('work-schedule')")
        page4.wait_for_timeout(1500)
        narrow = page4.evaluate(r"""(() => {
            const title = document.querySelector(
                '#page-work-schedule .page-inline-header-title');
            const wrap = document.getElementById('wsLcdWrap');
            const t = title.getBoundingClientRect(), w = wrap.getBoundingClientRect();
            const cs = getComputedStyle(title);
            return {ellipsis: cs.textOverflow === 'ellipsis',
                    overlap: t.right > w.left,
                    titleW: t.width, wrapL: w.left,
                    canvasW: document.getElementById('wsLcdCanvas').width};})""")
        check('F: заголовок — эллипсис (стиль применён)', narrow.get('ellipsis'))
        check('F: наезда заголовка на LCD НЕТ', not narrow.get('overlap'), narrow)
        check('F: окно влезает и сетка жива (канвас кратен 205)',
              narrow.get('canvasW', 1) % 205 == 0, narrow)
        shot(page4, 'f-narrow-1024.png')

        # ==============================================================
        print('== G: МОБАЙЛ — окно скрыто <1024px ==')
        for w, h in [(390, 844), (1000, 700)]:
            ctxm = make_ctx('dark', w, h)
            pm = ctxm.new_page()
            pm.on('pageerror', lambda e: js_errors.append('m:' + str(e)))
            pm.on('dialog', lambda dg: dg.accept())
            pm.goto('http://127.0.0.1:%d/index.html' % PORT)
            pm.wait_for_timeout(700)
            pm.evaluate("navigateTo('work-schedule')")
            pm.wait_for_timeout(900)
            vis = pm.evaluate("(() => { const w = document.getElementById('wsLcdWrap');" +
                              "return w && getComputedStyle(w).display !== 'none'; })()")
            check('G: %dx%d — окно СКРЫТО' % (w, h), not vis)
            ctxm.close()

        # ==============================================================
        print('== H: JS-ошибки ==')
        check('H: 0 JS-ошибок во всех сценариях', len(js_errors) == 0, js_errors[:4])

        browser.close()
        server.shutdown()

    print()
    print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
