#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 526 browser-check: Геометрия — анимированные «живые» схемы
# (заявка: «…переделай пояснительные картинки, сделай их анимированными
# с отображением реальных расчётов фигур, и переделай их отображение
# немного больше и без погрешностей в отображении линий и прочего,
# отобрази их в рамках с непрозрачным фоном бежевого-бело-молочного
# цвета в светлой теме и на твой выбор в тёмной теме.»):
#  A) ДЕСКТОП тёмная: 6 страниц — рамка .geo-fig-frame видима,
#     НЕПРОЗРАЧНЫЙ фон #17222E rgb(23,34,46), ширина ~320 (>220
#     прежних), SVG отрендерен, подписи размеров фактическими
#     значениями, блок живого расчёта с теми же числами, что
#     calcGeo*; анимация: animation-name gf-draw/gf-res, к финалу
#     opacity 1; жидкость gh (gf-liquid); старых .geo-svg нет.
#  B) ДЕСКТОП светлая: фон #F7F2E6 rgb(247,242,230), подписи
#     размеров читаемы (терракота #B05537), все 6 скриншотов.
#  C) ВЗАИМОДЕЙСТВИЕ (gc): ввод 150 → мгновенная перестройка
#     (geo-static, «D = 150 мм», 176,7146 см²); «Рассчитать» →
#     анимация перезапускается (geo-static снят).
#  D) МОБАЙЛ 390×844: рамка не обрезана, жидкость на месте.
#  E) 0 JS-ошибок; скриншоты в download/kip8test-task526/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task526')
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t526');" +
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
    return {
        frame: true,
        visible: frame.offsetParent !== null,
        bg: cs.backgroundColor,
        w: frame.getBoundingClientRect().width,
        notClipped: frame.scrollWidth <= frame.clientWidth + 1,
        svgChildren: svg.childElementCount,
        texts: Array.from(svg.querySelectorAll('text')).map(t => t.textContent),
        resText: res.textContent,
        nResRows: res.querySelectorAll('.geo-fig-res-row').length,
        drawAnim: draw ? getComputedStyle(draw).animationName : '',
        drawDash: draw ? getComputedStyle(draw).strokeDasharray : '',
        resAnim: getComputedStyle(res).animationName,
        resOpacity: getComputedStyle(res).opacity,
        dimColor: dimtx ? getComputedStyle(dimtx).fill : '',
        liquid: !!svg.querySelector('.gf-liquid'),
        staticMode: frame.classList.contains('geo-static')
    };})()"""


def fig_state(page, key):
    return page.evaluate(STATE_JS.replace('%%KEY%%', key))


# (страница, ключ, ожидаемые подписи, ожидаемые результаты живого расчёта)
GEO_PAGES = [
    ('geo-circle', 'gc', ['D = 100 мм', 'R = 50 мм'],
     ['78,5398 см²', '314,16 мм']),
    ('geo-ring', 'gr', ['D = 100 мм', 'd = 80 мм'],
     ['28,2743 см²', '20 мм']),
    ('geo-cylinder', 'gcy', ['D = 2 м', 'H = 3 м'],
     ['9,4248 м³', '25,1327 м²']),
    ('geo-horiz', 'gh', ['L = 5 м', 'D = 2 м', 'h = 1,5 м'],
     ['12,637 м³', '15,708 м³', '80,4499 %']),
    ('geo-sphere', 'gs', ['D = 2 м'],
     ['4,1888 м³', '12,5664 м²']),
    ('geo-cone', 'gco', ['D = 2 м', 'H = 3 м', 'L = 3,1623 м'],
     ['3,1416 м³', '3,1623 м']),
]


def check_page(st, page_id, labels, results, bg_rgb, extra=''):
    check(page_id + ': рамка в DOM и видима', st.get('frame') and st.get('visible'))
    check(page_id + ': НЕПРОЗРАЧНЫЙ фон ' + bg_rgb, st.get('bg') == bg_rgb,
          st.get('bg'))
    check(page_id + ': ширина ~320px (больше прежних 220)',
          280 <= st.get('w', 0) <= 322, st.get('w'))
    check(page_id + ': не обрезана', st.get('notClipped') is True)
    check(page_id + ': SVG отрендерен (дети есть)', st.get('svgChildren', 0) >= 4,
          st.get('svgChildren'))
    for lb in labels:
        check(page_id + ': подпись «' + lb + '»',
              lb in ' | '.join(st.get('texts', [])))
    for rs in results:
        check(page_id + ': живой расчёт «' + rs + '»', rs in st.get('resText', ''),
              st.get('resText', '')[:120])
    check(page_id + ': строк расчёта = ' + str(len(results)),
          st.get('nResRows') == len(results), st.get('nResRows'))
    if extra:
        print(extra)


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
        for page_id, key, labels, results in GEO_PAGES:
            page.evaluate("navigateTo('" + page_id + "')")
            page.wait_for_timeout(450)          # рендер + анимация идёт
            st = fig_state(page, key)
            check_page(st, page_id, labels, results, 'rgb(23, 34, 46)')
            check(page_id + ': анимация контура (gf-draw)',
                  st.get('drawAnim') == 'gf-draw', st.get('drawAnim'))
            check(page_id + ': штрих-маска контура (460)',
                  st.get('drawDash') == '460px' or st.get('drawDash') == '460',
                  st.get('drawDash'))
            check(page_id + ': анимация блока расчёта (gf-res)',
                  st.get('resAnim') == 'gf-res', st.get('resAnim'))
            if key == 'gh':
                check('geo-horiz: жидкость нарисована (gf-liquid)',
                      st.get('liquid') is True)
            page.wait_for_timeout(2100)          # анимации завершились
            st2 = fig_state(page, key)
            check(page_id + ': анимация завершена (opacity 1)',
                  st2.get('resOpacity') == '1', st2.get('resOpacity'))
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
              'D = 150 мм' in ' | '.join(st.get('texts', [])), st.get('texts'))
        check('ввод → режим geo-static (без анимации)',
              st.get('staticMode') is True)
        check('ввод → живой расчёт 176,71 см²',
              '176,71 см²' in st.get('resText', ''), st.get('resText', '')[:120])
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
        for page_id, key, labels, results in GEO_PAGES:
            page2.evaluate("navigateTo('" + page_id + "')")
            page2.wait_for_timeout(450)
            st = fig_state(page2, key)
            check_page(st, page_id, labels, results, 'rgb(247, 242, 230)')
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
            check(page_id + ' (мобайл): живой расчёт на месте',
                  len(st.get('resText', '')) > 5)
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
