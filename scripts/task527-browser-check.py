#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 527 browser-check: Геометрия — подписи вне фигур + расчёт
# ВНУТРИ картинки под фигурой + рамка больше.
# (заявка: «…на некоторых геометрических фигурах линии и цифры
#  пересекаются и накладываются друг на друга, поправь, и расчётные
#  данные должны отображаться на картинке под геометрической фигурой,
#  поэтому блок с фигурой сделай немного больше.»):
#  A) ДЕСКТОП тёмная: 6 страниц — рамка ~350px (>320 Task 526),
#     НЕПРОЗРАЧНЫЙ фон #17222E, SVG отрендерен, подписи размеров —
#     ВНЕ фигур (D под кругом/сферой/кольцом, d над кольцом, L слева
#     от конуса, h-подпись вне выносных), данные расчёта — В КАРТИНКЕ
#     (SVG-тексты .gf-tx/.gf-val под разделителем .gf-sep),
#     анимация gf-draw/gf-resg играет и завершается; жидкость gh;
#     HTML-блока #xxFigRes НЕТ.
#  B) ДЕСКТОП светлая: фон #F7F2E6, подписи терракота #B05537,
#     все 6 скриншотов.
#  C) ВЗАИМОДЕЙСТВИЕ (gc): ввод 150 → мгновенная перестройка
#     (geo-static, «D = 150 мм», 176,71 см² В КАРТИНКЕ); «Рассчитать»
#     → анимация перезапущена.
#  D) МОБАЙЛ 390×844: рамка не обрезана, данные на месте.
#  E) 0 JS-ошибок; скриншоты в download/kip8test-task527/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task527')
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


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'library.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def handle(route, request):
    action = ''
    if 'action=' in request.url:
        action = unquote(request.url.split('action=')[1].split('&')[0])
    body = {}
    if request.post_data:
        try:
            body = json.loads(request.post_data)
        except Exception:
            body = {}
    return route.fulfill(status=200,
        content_type='application/json; charset=utf-8',
        body=json.dumps(mock_response(action, body)))


def setup_ctx(browser, theme, viewport):
    ctx = browser.new_context(viewport=viewport)
    page = ctx.new_page()
    page.on('dialog', lambda dg: dg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t527');" +
        "localStorage.setItem('kip8test:app-theme','" + theme + "');")
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
        status=404, content_type='text/plain', body='nf'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
        status=404, content_type='text/plain', body='nf'))
    ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
        status=404, content_type='text/plain', body='nf'))
    return ctx, page


STATE_JS = """(() => {
    const key = '%%KEY%%';
    const frame = document.getElementById(key + 'FigFrame');
    if (!frame) return {frame: false};
    const svg = document.getElementById(key + 'Fig');
    const res = document.getElementById(key + 'FigRes');
    const cs = getComputedStyle(frame);
    const draw = svg.querySelector('.gf-draw');
    const dimtx = svg.querySelector('.gf-dimtx');
    const zone = svg.querySelector('.gf-resg');
    const sep = svg.querySelector('.gf-sep');
    const zcs = zone ? getComputedStyle(zone) : null;
    // подписи размеров: {текст: {y, x, anchor}}
    const dims = {};
    svg.querySelectorAll('text.gf-dimtx').forEach(t => {
        dims[t.textContent] = {y: parseFloat(t.getAttribute('y') || '0'),
                               x: parseFloat(t.getAttribute('x') || '0'),
                               anchor: t.getAttribute('text-anchor') || 'start'};
    });
    // данные расчёта В КАРТИНКЕ: тексты .gf-tx и .gf-val
    const formulas = Array.from(svg.querySelectorAll('text.gf-tx')).map(t => t.textContent);
    const values = Array.from(svg.querySelectorAll('text.gf-val')).map(t => t.textContent);
    const valColor = svg.querySelector('text.gf-val')
        ? getComputedStyle(svg.querySelector('text.gf-val')).fill : '';
    return {
        frame: true,
        visible: frame.offsetParent !== null,
        bg: cs.backgroundColor,
        w: frame.getBoundingClientRect().width,
        svgH: svg.getBoundingClientRect().height,
        notClipped: frame.scrollWidth <= frame.clientWidth + 1,
        svgChildren: svg.childElementCount,
        resDivInDom: !!res,
        dims: dims,
        formulas: formulas,
        values: values,
        zoneAnim: zcs ? zcs.animationName : '',
        zoneOpacity: zcs ? zcs.opacity : '',
        hasSep: !!sep,
        drawAnim: draw ? getComputedStyle(draw).animationName : '',
        drawDash: draw ? getComputedStyle(draw).strokeDasharray : '',
        dimColor: dimtx ? getComputedStyle(dimtx).fill : '',
        liquid: !!svg.querySelector('.gf-liquid'),
        staticMode: frame.classList.contains('geo-static')
    };})()"""


def fig_state(page, key):
    return page.evaluate(STATE_JS.replace('%%KEY%%', key))


# (страница, ключ, подписи, данные расчёта, правило позиции подписей)
# правила: кортежи (подпись, min_y, max_y) — допусимый диапазон Y
GEO_PAGES = [
    ('geo-circle', 'gc', ['D = 100 мм', 'R = 50 мм'],
     ['78,5398 см²', '314,16 мм'],
     [('D = 100 мм', 146, 190)]),          # под кругом (низ 140)
    ('geo-ring', 'gr', ['D = 100 мм', 'd = 80 мм'],
     ['28,2743 см²', '20 мм'],
     [('D = 100 мм', 150, 190),            # под кольцом (низ 144)
      ('d = 80 мм', 0, 27)]),              # над кольцом (верх 28)
    ('geo-cylinder', 'gcy', ['D = 2 м', 'H = 3 м'],
     ['9,4248 м³', '25,1327 м²'],
     []),
    ('geo-horiz', 'gh', ['L = 5 м', 'D = 2 м', 'h = 1,5 м'],
     ['12,637 м³', '15,708 м³', '80,4499 %'],
     [('h = 1,5 м', 0, 80)]),              # вне выносных 81..126 (сверху)
    ('geo-sphere', 'gs', ['D = 2 м'],
     ['4,1888 м³', '12,5664 м²'],
     [('D = 2 м', 148, 190)]),             # под сферой (низ 142)
    ('geo-cone', 'gco', ['D = 2 м', 'H = 3 м', 'L = 3,1623 м'],
     ['3,1416 м³', '3,1623 м'],
     [('L = 3,1623 м', 0, 190)]),          # любой Y — проверим X отдельно
]


def check_page(st, page_id, labels, results, bg_rgb, yrules):
    check(page_id + ': рамка в DOM и видима', st.get('frame') and st.get('visible'))
    check(page_id + ': НЕПРОЗРАЧНЫЙ фон ' + bg_rgb, st.get('bg') == bg_rgb,
          st.get('bg'))
    check(page_id + ': ширина ~350px (немного больше 320)',
          330 <= st.get('w', 0) <= 352, st.get('w'))
    check(page_id + ': не обрезана', st.get('notClipped') is True)
    check(page_id + ': SVG отрендерен (дети есть)', st.get('svgChildren', 0) >= 4,
          st.get('svgChildren'))
    check(page_id + ': HTML-блока #xxFigRes НЕТ в DOM',
          st.get('resDivInDom') is False)
    for lb in labels:
        check(page_id + ': подпись «' + lb + '»',
              lb in st.get('dims', {}), list(st.get('dims', {}).keys()))
    for rs in results:
        check(page_id + ': данные В КАРТИНКЕ «' + rs + '»',
              rs in st.get('values', []), st.get('values'))
    check(page_id + ': строк данных в картинке = ' + str(len(results)),
          len(st.get('values', [])) == len(results), st.get('values'))
    check(page_id + ': разделитель зоны расчёта (.gf-sep)',
          st.get('hasSep') is True)
    for lb, ylo, yhi in yrules:
        d = st.get('dims', {}).get(lb)
        check(page_id + ': «' + lb + '» вне фигуры (y=' +
              ('%s' % d.get('y') if d else '?') + ')',
              d is not None and ylo <= d.get('y', -1) <= yhi, d)


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors_all = []

        # ---------- A: десктоп, тёмная тема ----------
        ctx, page = setup_ctx(browser, 'dark', {'width': 1280, 'height': 720})
        page.on('pageerror', lambda e: errors_all.append(str(e)))
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)

        print('A. Десктоп, тёмная тема (6 страниц геометрии):')
        for page_id, key, labels, results, yrules in GEO_PAGES:
            page.evaluate("navigateTo('" + page_id + "')")
            page.wait_for_timeout(450)          # рендер + анимация идёт
            st = fig_state(page, key)
            check_page(st, page_id, labels, results, 'rgb(23, 34, 46)', yrules)
            check(page_id + ': анимация контура (gf-draw)',
                  st.get('drawAnim') == 'gf-draw', st.get('drawAnim'))
            check(page_id + ': штрих-маска контура (460)',
                  st.get('drawDash') == '460px' or st.get('drawDash') == '460',
                  st.get('drawDash'))
            check(page_id + ': анимация зоны расчёта в картинке (gf-res)',
                  st.get('zoneAnim') == 'gf-res', st.get('zoneAnim'))
            if key == 'gh':
                check('geo-horiz: жидкость нарисована (gf-liquid)',
                      st.get('liquid') is True)
                check('geo-horiz: картинка выше (viewBox 257)',
                      st.get('svgH', 0) > 330, st.get('svgH'))
            if key == 'gco':
                d = st.get('dims', {}).get('L = 3,1623 м')
                check('geo-cone: «L» у ЛЕВОГО ребра (anchor end, x=' +
                      ('%s' % d.get('x') if d else '?') + ')',
                      d is not None and d.get('anchor') == 'end' and d.get('x', 999) < 100, d)
            page.wait_for_timeout(2100)          # анимации завершились
            st2 = fig_state(page, key)
            check(page_id + ': анимация завершена (opacity 1)',
                  st2.get('zoneOpacity') == '1', st2.get('zoneOpacity'))
            shot(page, 'desktop-dark-' + page_id + '.png')
        check('старых статичных картинок нет (.geo-svg-container)',
              page.evaluate("document.querySelector('.geo-svg-container')") is None)

        # ---------- C: взаимодействие (круг) ----------
        print('C. Взаимодействие (geo-circle, тёмная):')
        page.evaluate("navigateTo('geo-circle')")
        page.wait_for_timeout(2200)
        page.fill('#gc_diameter', '150')
        page.wait_for_timeout(350)              # мгновенная перестройка
        st = fig_state(page, 'gc')
        check('ввод 150 → подпись «D = 150 мм» мгновенно',
              'D = 150 мм' in st.get('dims', {}), list(st.get('dims', {}).keys()))
        check('ввод → режим geo-static (без анимации)',
              st.get('staticMode') is True)
        check('ввод → живой расчёт 176,71 см² В КАРТИНКЕ',
              '176,71 см²' in st.get('values', []), st.get('values'))
        page.click('#page-geo-circle .scale-calc-btn')
        page.wait_for_timeout(350)
        st = fig_state(page, 'gc')
        check('«Рассчитать» → анимация перезапущена (geo-static снят)',
              st.get('staticMode') is False)
        check('«Рассчитать» → gf-draw играет',
              st.get('drawAnim') == 'gf-draw', st.get('drawAnim'))
        check('«Рассчитать» → панель «Результат» открылась',
              page.evaluate(
                  "document.getElementById('gc_results').style.display") != 'none')
        page.wait_for_timeout(1800)
        shot(page, 'desktop-dark-geo-circle-recalc150.png')
        ctx.close()

        # ---------- B: десктоп, светлая тема ----------
        ctx2, page2 = setup_ctx(browser, 'light', {'width': 1280, 'height': 720})
        page2.on('pageerror', lambda e: errors_all.append(str(e)))
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)

        print('B. Десктоп, светлая тема (бежево-бело-молочная бумага):')
        for page_id, key, labels, results, yrules in GEO_PAGES:
            page2.evaluate("navigateTo('" + page_id + "')")
            page2.wait_for_timeout(450)
            st = fig_state(page2, key)
            check_page(st, page_id, labels, results, 'rgb(247, 242, 230)', yrules)
            check(page_id + ': подписи размеров читаемы (терракота #B05537)',
                  st.get('dimColor') == 'rgb(176, 85, 55)', st.get('dimColor'))
            page2.wait_for_timeout(2100)
            shot(page2, 'desktop-light-' + page_id + '.png')
        ctx2.close()

        # ---------- D: мобайл 390×844 ----------
        ctx3, page3 = setup_ctx(browser, 'dark', {'width': 390, 'height': 844})
        page3.on('pageerror', lambda e: errors_all.append(str(e)))
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)

        print('D. Мобайл 390×844, тёмная тема:')
        for page_id, key in [('geo-horiz', 'gh'), ('geo-circle', 'gc')]:
            page3.evaluate("navigateTo('" + page_id + "')")
            page3.wait_for_timeout(2500)
            st = fig_state(page3, key)
            check(page_id + ' (мобайл): рамка видима, не обрезана',
                  st.get('visible') and st.get('notClipped') is True,
                  {'w': st.get('w'), 'clip': st.get('notClipped')})
            check(page_id + ' (мобайл): данные расчёта В КАРТИНКЕ',
                  len(st.get('values', [])) > 0, st.get('values'))
            if key == 'gh':
                check('geo-horiz (мобайл): жидкость есть',
                      st.get('liquid') is True)
            shot(page3, 'mobile-dark-' + page_id + '.png')
        ctx3.close()

        ctx4, page4 = setup_ctx(browser, 'light', {'width': 390, 'height': 844})
        page4.on('pageerror', lambda e: errors_all.append(str(e)))
        page4.goto('http://localhost:%d/index.html' % PORT)
        page4.wait_for_timeout(2500)
        page4.evaluate("navigateTo('geo-horiz')")
        page4.wait_for_timeout(2500)
        st4 = fig_state(page4, 'gh')
        print('D2. Мобайл, светлая:')
        check('geo-horiz (мобайл, светлая): бежевая бумага',
              st4.get('bg') == 'rgb(247, 242, 230)', st4.get('bg'))
        check('geo-horiz (мобайл, светлая): не обрезана',
              st4.get('notClipped') is True)
        shot(page4, 'mobile-light-geo-horiz.png')
        ctx4.close()

        browser.close()

    print('E. JS-ошибки:')
    check('0 JS-ошибок во всех сценариях', len(errors_all) == 0, errors_all[:3])

    print('\nИТОГО: %d passed, %d failed' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
