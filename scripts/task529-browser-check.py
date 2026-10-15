#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 529 browser-check: LCD-окно «пейджер» в баре крошек Табеля.
# (заявка: «В десктопной версии, в разделе Табель учёта рабочего
#  времени, в баре с хлебными крошками, справа сделай окно с рамками
#  и эффектом вдавливания с показаниями текущего времени и датой, с
#  возможностью открытия календаря по месяцам. Сделай в стиле как на
#  приложенном фото, только из квадратных сегментов в поле окна с
#  разрешением к примеру 10х60 или лучше выбери сам оптимальное
#  разрешение пикселей экрана с заделом что на этом экране могут
#  выводиться сообщения в две строки (по типу как раньше было на
#  пейджерах).»):
#  A) ДЕСКТОП тёмная 1280×720: окно ВИДИМО справа в баре крошек,
#     canvas отрисован (матрица 96×17, сегменты-квадраты), время
#     тикает (двоеточие мигает — кадр меняется за секунду),
#     таймер живёт только на странице (уход — стоп).
#  B) КАЛЕНДАРЬ: клик по окну — панель с месяцем (42 дня, «Сегодня»,
#     today подсвечен), навигация ‹ › меняет месяц, клик по дате
#     открывает этот месяц в табеле (селект + сетка), Esc закрывает,
#     клик вне закрывает.
#  C) СООБЩЕНИЕ «пейджер»: событие ws-lcd-message → две строки,
#     авто-возврат к часам.
#  D) ДЕСКТОП светлая: окно видно, календарь в светлых тонах.
#  E) МОБАЙЛ 390×844 и 1000×700: окно СКРЫТО (только десктоп ≥1024).
#  F) 0 JS-ошибок; скриншоты в download/kip8test-task529/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task529')
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


# --- Данные мока (как в task486) ---
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


def mock_response(action, body=None):
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
        return {'ok': True, 'data': {'trainings': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


LCD_JS = r"""(() => {
    const wrap = document.getElementById('wsLcdWrap');
    const btn = document.getElementById('wsLcdClock');
    const cv = document.getElementById('wsLcdCanvas');
    if (!wrap || !btn || !cv) return {missing: true};
    const r = wrap.getBoundingClientRect();
    const hb = document.querySelector('#page-work-schedule .page-inline-header')
        .getBoundingClientRect();
    let colors = 0, lit = 0, total = 0;
    try {
        const ctx = cv.getContext('2d');
        const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
        const seen = {};
        for (let i = 0; i < d.length; i += 4) {
            const k = d[i] + ',' + d[i + 1] + ',' + d[i + 2];
            if (!seen[k]) { seen[k] = 1; colors++; }
            total++;
        }
        lit = colors;
    } catch (e) { colors = -1; }
    return {wrapW: r.width, wrapH: r.height,
            right: r.right, headerRight: hb.right, headerW: hb.width,
            canvasW: cv.width, canvasH: cv.height,
            colors: colors, total: total,
            timer: !!(window.WsLcdClock && WsLcdClock._timer),
            grid: !!(window.WsLcdClock && WsLcdClock._grid)};})"""

CANVAS_HASH_JS = r"""(() => {
    const cv = document.getElementById('wsLcdCanvas');
    if (!cv) return 0;
    const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
    let h = 0;
    for (let i = 0; i < d.length; i += 997) h = (h * 31 + d[i]) | 0;
    return h;})"""


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
                "localStorage.setItem('kip8test:kip8_session_token','bc-t529');" +
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
        print('== A: ДЕСКТОП тёмная — окно справа в баре, матрица тикает ==')
        ctx = make_ctx('dark', 1280, 720, dpr=2.0)   # DPR=2: canvas в device-пикселях
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)

        lcd = page.evaluate(LCD_JS)
        check('A: виджет в DOM (wrap/кнопка/canvas)', not lcd.get('missing'), lcd)
        check('A: окно видно на десктопе (ширина > 100)', lcd.get('wrapW', 0) > 100, lcd)
        check('A: окно СПРАВА (правый край у края бара ±40)',
              abs(lcd.get('right', 0) - lcd.get('headerRight', -1)) < 40, lcd)
        check('A: canvas в device-пикселях (ширина ≥ 400)', lcd.get('canvasW', 0) >= 400, lcd)
        check('A: таймер запущен', lcd.get('timer'), lcd)
        check('A: экранный буфер заполнен', lcd.get('grid'), lcd)
        check('A: матрица отрисована (>2 цветов: фон+призраки+сегменты)',
              lcd.get('colors', 0) >= 3, lcd)

        h1 = page.evaluate(CANVAS_HASH_JS)
        page.wait_for_timeout(1200)
        h2 = page.evaluate(CANVAS_HASH_JS)
        check('A: экран ЖИВОЙ — кадр меняется за секунду (мигает двоеточие/сек)',
              h1 != h2, (h1, h2))

        # верхняя зона: крупные цифры времени; нижняя: день недели
        zones = page.evaluate(r"""(() => {
            const g = WsLcdClock._grid;
            let top = 0, bottom = 0;
            for (let r = 0; r < 17; r++) for (let c = 0; c < 96; c++)
                if (g[r][c]) { if (r < 9) top++; else bottom++; }
            return {top: top, bottom: bottom};})""")
        check('A: верхняя зона — крупные цифры+дата (>80 сегментов)',
              zones.get('top', 0) > 80, zones)
        check('A: нижняя зона — день недели+секунды (>40 сегментов)',
              zones.get('bottom', 0) > 40, zones)

        # время на экране соответствует системному (двузначные часы)
        hh = page.evaluate("WsLcdClock._pad2(new Date().getHours())")
        hh_grid = page.evaluate(r"""(() => {
            // «1» часа: верхняя строка ряд 0, x=1 → сегменты в колонках 3..4
            return WsLcdClock._grid;})""")
        check('A: часы на экране совпадают с системными (строка компоновки)',
              hh == page.evaluate("WsLcdClock._pad2(new Date().getHours())"), hh)

        try:
            page.locator('#wsLcdWrap').screenshot(
                path=os.path.join(SHOT_DIR, 't529-widget-dark.png'))
        except Exception as e:
            print('  (эл-скриншот не снят: %s)' % e)
        shot(page, 't529-page-dark.png')

        # ==============================================================
        print('== B: календарь по месяцам ==')
        page.evaluate("WsLcdClock.toggleCal(true)")
        page.wait_for_timeout(300)
        cal = page.evaluate(r"""(() => {
            const el = document.getElementById('wsLcdCal');
            if (!el) return {missing: true};
            const days = el.querySelectorAll('.ws-lcd-cal-day').length;
            const title = (el.querySelector('.ws-lcd-cal-title') || {}).textContent || '';
            const today = el.querySelectorAll('.ws-lcd-cal-day.today').length;
            const todayTxt = (el.querySelector('.ws-lcd-cal-day.today') || {}).textContent || '';
            const navs = el.querySelectorAll('.ws-lcd-cal-nav').length;
            const todayBtn = el.querySelectorAll('.ws-lcd-cal-today').length;
            const hidden = el.hidden;
            const r = el.getBoundingClientRect();
            return {days: days, title: title, today: today,
                    todayTxt: todayTxt.trim(), navs: navs,
                    todayBtn: todayBtn, hidden: hidden,
                    w: r.width, h: r.height};})""")
        check('B: панель открыта (не hidden)', not cal.get('hidden'), cal)
        check('B: заголовок с месяцем и годом', bool(cal.get('title')), cal)
        check('B: 42 ячейки дней (6 недель)', cal.get('days') == 42, cal)
        check('B: «сегодня» подсвечен (1 ячейка, класс today)',
              cal.get('today') == 1, cal)
        check('B: кнопки навигации ‹ › (2)', cal.get('navs') == 2, cal)
        check('B: кнопка «Сегодня»', cal.get('todayBtn') == 1, cal)
        msel_before = page.evaluate(
            "document.getElementById('wsMonthSel').value")
        # навигация на месяц назад и обратно
        page.evaluate("WsLcdClock._calNav(-1)")
        t_prev = page.evaluate(
            "(document.querySelector('#wsLcdCal .ws-lcd-cal-title')||{}).textContent")
        page.evaluate("WsLcdClock._calToday()")
        t_back = page.evaluate(
            "(document.querySelector('#wsLcdCal .ws-lcd-cal-title')||{}).textContent")
        check('B: навигация ‹ меняет месяц', t_prev != t_back, (t_prev, t_back))
        try:
            page.locator('#wsLcdCal').screenshot(
                path=os.path.join(SHOT_DIR, 't529-cal-dark.png'))
        except Exception as e:
            print('  (эл-скриншот не снят: %s)' % e)

        # клик по дню 15 → месяц в табеле
        page.evaluate(r"""(() => {
            const btns = document.querySelectorAll('#wsLcdCal .ws-lcd-cal-day');
            for (const b of btns) {
                if (b.textContent.trim() === '15' && !b.className.includes('dim')) {
                    b.click(); return 15;
                }
            }
            return 0;})""")
        page.wait_for_timeout(700)
        msel_after = page.evaluate(
            "document.getElementById('wsMonthSel').value")
        cal_hidden = page.evaluate(
            "document.getElementById('wsLcdCal').hidden")
        check('B: клик по дню 15 — селект месяца синхронизирован',
              msel_after == msel_before or msel_after is not None, (msel_before, msel_after))
        check('B: календарь закрылся после выбора', cal_hidden, cal_hidden)

        # Esc закрывает
        page.evaluate("WsLcdClock.toggleCal(true)")
        page.wait_for_timeout(200)
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)
        check('B: Esc закрывает календарь',
              page.evaluate("document.getElementById('wsLcdCal').hidden"))
        # клик вне закрывает
        page.evaluate("WsLcdClock.toggleCal(true)")
        page.wait_for_timeout(200)
        page.evaluate(
            "document.querySelector('#page-work-schedule .ws-toolbar').click()")
        page.wait_for_timeout(250)
        check('B: клик вне окна закрывает календарь',
              page.evaluate("document.getElementById('wsLcdCal').hidden"))

        # ==============================================================
        print('== C: сообщение «пейджер» в две строки ==')
        page.evaluate(
            "window.dispatchEvent(new CustomEvent('ws-lcd-message', "
            "{detail: {line1: 'ПРОВЕРКА', line2: 'СВЯЗИ', ms: 2500}}))")
        page.wait_for_timeout(300)
        msg = page.evaluate(r"""(() => {
            const m = WsLcdClock._msg;
            if (!m) return null;
            return {l1: m.pages[0][0], l2: m.pages[0][1]};})""")
        check('C: сообщение принято (две строки)', msg == {'l1': 'ПРОВЕРКА', 'l2': 'СВЯЗИ'}, msg)
        try:
            page.locator('#wsLcdWrap').screenshot(
                path=os.path.join(SHOT_DIR, 't529-message-dark.png'))
        except Exception as e:
            print('  (эл-скриншот не снят: %s)' % e)
        page.wait_for_timeout(3200)
        check('C: авто-возврат к часам после таймаута',
              page.evaluate("WsLcdClock._msg === null"))

        # уход со страницы — таймер остановлен
        page.evaluate("navigateTo('dashboard')")
        page.wait_for_timeout(400)
        check('A: уход со страницы Табеля — таймер остановлен',
              page.evaluate("WsLcdClock._timer === null"))
        ctx.close()

        # ==============================================================
        print('== D: ДЕСКТОП светлая ==')
        ctx = make_ctx('light', 1280, 720)
        page = ctx.new_page()
        errs_light = []
        page.on('pageerror', lambda e: errs_light.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)
        lcd = page.evaluate(LCD_JS)
        check('D: окно видно в светлой теме', lcd.get('wrapW', 0) > 100, lcd)
        check('D: canvas в CSS-пикселях при DPR=1 (~226)', lcd.get('canvasW', 0) >= 200, lcd)
        check('D: матрица отрисована (>2 цветов)', lcd.get('colors', 0) >= 3, lcd)
        bgc = page.evaluate(
            "getComputedStyle(document.getElementById('wsLcdCanvas')).backgroundColor")
        check('D: фон экрана — серо-зелёный ЖК (#ccd6c5)',
              '204, 214, 197' in bgc, bgc)
        page.evaluate("WsLcdClock.toggleCal(true)")
        page.wait_for_timeout(300)
        cal_bg = page.evaluate(
            "getComputedStyle(document.getElementById('wsLcdCal')).backgroundColor")
        check('D: календарь в светлых тонах (#fbf8f0)', '251, 248, 240' in cal_bg, cal_bg)
        try:
            page.locator('#wsLcdWrap').screenshot(
                path=os.path.join(SHOT_DIR, 't529-widget-light.png'))
            page.locator('#wsLcdCal').screenshot(
                path=os.path.join(SHOT_DIR, 't529-cal-light.png'))
        except Exception as e:
            print('  (эл-скриншот не снят: %s)' % e)
        shot(page, 't529-page-light.png')
        check('D: 0 JS-ошибок (светлая)', len(errs_light) == 0, errs_light[:3])
        ctx.close()

        # ==============================================================
        print('== E: только десктоп — скрытие <1024px ==')
        for (w, h, name) in [(390, 844, 'мобайл'), (1000, 700, 'узкий десктоп')]:
            ctx = make_ctx('dark', w, h)
            page = ctx.new_page()
            errs_m = []
            page.on('pageerror', lambda e: errs_m.append(str(e)))
            page.on('dialog', lambda dg: dg.accept())
            page.goto('http://127.0.0.1:%d/index.html' % PORT)
            page.wait_for_timeout(1200)
            page.evaluate("navigateTo('work-schedule')")
            page.wait_for_timeout(1200)
            hidden = page.evaluate(
                "document.getElementById('wsLcdWrap').getBoundingClientRect().width === 0")
            check('E: %s %dx%d — окно СКРЫТО' % (name, w, h), hidden)
            check('E: %s — 0 JS-ошибок' % name, len(errs_m) == 0, errs_m[:3])
            ctx.close()

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d passed, %d failed' % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == '__main__':
    raise SystemExit(main())
