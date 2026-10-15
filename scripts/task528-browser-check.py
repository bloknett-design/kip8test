#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 528 browser-check: Геометрия — надписи НАД линиями, d кольца
# внутри отверстия, h над линией зеркала, ВСЕ результаты в блоке с
# фигурой, автопрокрутка к фигуре по «Рассчитать».
# (заявка: «На изображении фигур надписи должны быть как положено над
#  линиями (если мало места, то вынос линии нужно сделать больше), в
#  фигуре кольцо текст размера внутреннего диаметра можно разместить
#  внутри самой фигуры (там нет явного конфликта с линиями), в
#  горизонтальном цилиндре значения уровня жидкости так же можно
#  разместить над линией (сделать вынос линии немного дальше от
#  фигуры), и все результаты расчётов выводить в блоке с фигурами и
#  при нажатии на кнопку "Расчитать" автоматически смещать экран в
#  сторону фигуры.»):
#  A) ДЕСКТОП тёмная: 6 страниц — подписи размеров НАД размерными
#     линиями (реальная геометрия: bbox текста не пересекает линии
#     своей размерной группы), кольцо d — ВНУТРИ отверстия, гориз.
#     цилиндр h — НАД линией зеркала, ВСЕ результаты (3/2/4/5/3/4
#     строк) в картинке, строки не наезжают друг на друга
#     (getComputedTextLength), панелей #xx_results в DOM НЕТ.
#  B) ВЗАИМОДЕЙСТВИЕ: «Рассчитать» → экран смещается к фигуре
#     (frame в вьюпорте после клика при прокрученной вниз странице);
#     ввод → мгновенная перестройка; gh: h=1,9 → повернутая подпись
#     (fallback), h=0,2 → значение над линией зеркала.
#  C) ДЕСКТОП светлая: фон #F7F2E6, терракота #B05537, 6 скриншотов.
#  D) МОБАЙЛ 390×844: рамки не обрезаны, данные на месте, прокрутка
#     к фигуре работает.
#  E) 0 JS-ошибок; скриншоты в download/kip8test-task528/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task528')
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t528');" +
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
    const cs = getComputedStyle(frame);
    const zone = svg.querySelector('.gf-resg');
    const zcs = zone ? getComputedStyle(zone) : null;
    // подписи размеров: {текст: {y, x, anchor, rotated}}
    const dims = {};
    svg.querySelectorAll('text.gf-dimtx').forEach(t => {
        dims[t.textContent] = {y: parseFloat(t.getAttribute('y') || '0'),
                               x: parseFloat(t.getAttribute('x') || '0'),
                               anchor: t.getAttribute('text-anchor') || 'start',
                               rotated: (t.getAttribute('transform') || '').indexOf('rotate') !== -1};
    });
    // данные расчёта В КАРТИНКЕ
    const formulas = Array.from(svg.querySelectorAll('text.gf-tx')).map(t => t.textContent);
    const values = Array.from(svg.querySelectorAll('text.gf-val')).map(t => t.textContent);
    // Task 528: строки зоны расчёта не наезжают (реальная ширина текста)
    const rowClash = [];
    const txs = Array.from(svg.querySelectorAll('text.gf-tx'));
    const vals = Array.from(svg.querySelectorAll('text.gf-val'));
    for (let i = 0; i < txs.length; i++) {
        const fw = txs[i].getComputedTextLength();
        const vw = vals[i] ? vals[i].getComputedTextLength() : 0;
        // метки: [12 .. 12+fw]; значения: [228-vw .. 228]
        if (12 + fw > 228 - vw - 1) rowClash.push(txs[i].textContent);
    }
    // Task 528: подписи НЕ пересекают линии своей размерной группы
    // (реальная bbox-геометрия: текст и линия с перекрытием по X
    // обязаны быть разделены по Y)
    const crossings = [];
    svg.querySelectorAll('g.gf-dim').forEach(g => {
        const texts = Array.from(g.querySelectorAll('text.gf-dimtx'))
            .filter(t => !(t.getAttribute('transform') || '').includes('rotate'));
        const lines = Array.from(g.querySelectorAll('line.gf-dimln'));
        texts.forEach(t => {
            const bb = t.getBBox();
            lines.forEach(ln => {
                const lx1 = Math.min(+ln.getAttribute('x1'), +ln.getAttribute('x2'));
                const lx2 = Math.max(+ln.getAttribute('x1'), +ln.getAttribute('x2'));
                if (bb.x + bb.width < lx1 || bb.x > lx2) return;   // нет перекрытия по X
                const ly = +ln.getAttribute('y1');
                if (ly !== +ln.getAttribute('y2')) return;        // только горизонтальные
                if (bb.y < ly - 0.6 && bb.y + bb.height > ly + 0.6)
                    crossings.push(t.textContent + '×line y=' + ly);
            });
        });
    });
    const valColor = svg.querySelector('text.gf-val')
        ? getComputedStyle(svg.querySelector('text.gf-val')).fill : '';
    const dimColor = svg.querySelector('text.gf-dimtx')
        ? getComputedStyle(svg.querySelector('text.gf-dimtx')).fill : '';
    return {
        frame: true,
        visible: frame.offsetParent !== null,
        bg: cs.backgroundColor,
        w: frame.getBoundingClientRect().width,
        notClipped: frame.scrollWidth <= frame.clientWidth + 1,
        svgChildren: svg.childElementCount,
        svgViewBox: svg.getAttribute('viewBox'),
        resPanelInDom: !!document.getElementById(key + '_results'),
        dims: dims,
        formulas: formulas,
        values: values,
        rowClash: rowClash,
        crossings: crossings,
        hasSep: !!svg.querySelector('.gf-sep'),
        zoneAnim: zcs ? zcs.animationName : '',
        zoneOpacity: zcs ? zcs.opacity : '',
        dimColor: dimColor,
        valColor: valColor,
        liquid: !!svg.querySelector('.gf-liquid'),
        staticMode: frame.classList.contains('geo-static')
    };})()"""


def fig_state(page, key):
    return page.evaluate(STATE_JS.replace('%%KEY%%', key))


# (страница, ключ, подписи, [значения в картинке], число строк,
#  правила позиции: (подпись, min_y, max_y))
GEO_PAGES = [
    ('geo-circle', 'gc', ['D = 100 мм', 'R = 50 мм'],
     ['78,5398 см²', '314,16 мм', '50 мм'], 3,
     [('D = 100 мм', 141, 161)]),          # НАД линией 164, под кругом (низ 140)
    ('geo-ring', 'gr', ['D = 100 мм', 'd = 80 мм'],
     ['28,2743 см²', '20 мм'], 2,
     [('D = 100 мм', 145, 165),            # НАД линией 168 (под кольцом, низ 144)
      ('d = 80 мм', 60, 100)]),            # ВНУТРИ отверстия (центр 86)
    ('geo-cylinder', 'gcy', ['D = 2 м', 'H = 3 м'],
     ['9,4248 м³', '18,8496 м²', '25,1327 м²'], 4, []),
    ('geo-horiz', 'gh', ['L = 5 м', 'D = 2 м', 'h = 1,5 м'],
     ['12,637 м³', '15,708 м³', '80,4499 %', '2,5274 м²'], 5,
     [('h = 1,5 м', 60, 80)]),             # НАД линией зеркала (y=81)
    ('geo-sphere', 'gs', ['D = 2 м'],
     ['4,1888 м³', '12,5664 м²'], 3,
     [('D = 2 м', 143, 163)]),             # НАД линией 166 (под сферой, низ 142)
    ('geo-cone', 'gco', ['D = 2 м', 'H = 3 м', 'L = 3,1623 м'],
     ['3,1416 м³', '3,1416 м²', '3,1623 м', '9,9346 м²'], 4,
     [('D = 2 м', 150, 175)]),             # НАД линией 178.1 (под конусом)
]


def check_page(st, page_id, labels, results, nrows, bg_rgb, yrules):
    check(page_id + ': рамка в DOM и видима', st.get('frame') and st.get('visible'))
    check(page_id + ': НЕПРОЗРАЧНЫЙ фон ' + bg_rgb, st.get('bg') == bg_rgb,
          st.get('bg'))
    check(page_id + ': ширина ~350px', 330 <= st.get('w', 0) <= 352, st.get('w'))
    check(page_id + ': не обрезана', st.get('notClipped') is True)
    check(page_id + ': SVG отрендерен', st.get('svgChildren', 0) >= 4,
          st.get('svgChildren'))
    check(page_id + ': панели #xx_results НЕТ в DOM',
          st.get('resPanelInDom') is False)
    for lb in labels:
        check(page_id + ': подпись «' + lb + '»', lb in st.get('dims', {}),
              list(st.get('dims', {}).keys()))
    for rs in results:
        check(page_id + ': результат в картинке «' + rs + '»',
              rs in st.get('values', []), st.get('values'))
    check(page_id + ': ВСЕ результаты — %d строк' % nrows,
          len(st.get('values', [])) == nrows, st.get('values'))
    check(page_id + ': формулы те же (%d)' % nrows,
          len(st.get('formulas', [])) == nrows, st.get('formulas'))
    check(page_id + ': разделитель зоны расчёта (.gf-sep)',
          st.get('hasSep') is True)
    check(page_id + ': строки расчёта не наезжают (реальная ширина)',
          len(st.get('rowClash', [])) == 0, st.get('rowClash'))
    check(page_id + ': подписи НЕ пересекают линии размеров (bbox)',
          len(st.get('crossings', [])) == 0, st.get('crossings'))
    for lb, ylo, yhi in yrules:
        d = st.get('dims', {}).get(lb)
        check(page_id + ': «' + lb + '» y=' + ('%s' % d.get('y') if d else '?') +
              ' в [%d..%d]' % (ylo, yhi),
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

        print('A. Десктоп, тёмная тема (6 страниц, надписи НАД линиями):')
        for page_id, key, labels, results, nrows, yrules in GEO_PAGES:
            page.evaluate("navigateTo('" + page_id + "')")
            page.wait_for_timeout(450)
            st = fig_state(page, key)
            check_page(st, page_id, labels, results, nrows, 'rgb(23, 34, 46)', yrules)
            check(page_id + ': анимация зоны расчёта (gf-res)',
                  st.get('zoneAnim') == 'gf-res', st.get('zoneAnim'))
            if key == 'gh':
                check('geo-horiz: жидкость нарисована', st.get('liquid') is True)
                d = st.get('dims', {}).get('h = 1,5 м')
                check('geo-horiz: «h = 1,5 м» — НЕ повернута (над линией)',
                      d is not None and d.get('rotated') is False, d)
                check('geo-horiz: «h = 1,5 м» anchor end у правого края корпуса',
                      d is not None and d.get('anchor') == 'end', d)
                check('geo-horiz: viewBox 240×291 (5 строк)',
                      st.get('svgViewBox') == '0 0 240 291', st.get('svgViewBox'))
            if key == 'gco':
                d = st.get('dims', {}).get('L = 3,1623 м')
                check('geo-cone: «L» у ЛЕВОГО ребра (anchor end)',
                      d is not None and d.get('anchor') == 'end', d)
            page.wait_for_timeout(2100)
            st2 = fig_state(page, key)
            check(page_id + ': анимация завершена (opacity 1)',
                  st2.get('zoneOpacity') == '1', st2.get('zoneOpacity'))
            shot(page, 'desktop-dark-' + page_id + '.png')

        # кольцо: d внутри отверстия — реальная bbox-геометрия
        page.evaluate("navigateTo('geo-ring')")
        page.wait_for_timeout(2400)
        ring = page.evaluate("""(() => {
            const svg = document.getElementById('grFig');
            const t = Array.from(svg.querySelectorAll('text.gf-dimtx'))
                .find(x => x.textContent.indexOf('d = ') === 0);
            if (!t) return {found: false};
            const bb = t.getBBox();
            const cx = 120, cy = 86;
            const corners = [[bb.x, bb.y], [bb.x + bb.width, bb.y],
                             [bb.x, bb.y + bb.height],
                             [bb.x + bb.width, bb.y + bb.height]];
            const maxDist = Math.max.apply(null, corners.map(c =>
                Math.sqrt((c[0] - cx) * (c[0] - cx) + (c[1] - cy) * (c[1] - cy))));
            return {found: true, maxDist: maxDist, holeR: 46.4};
        })()""")
        check('кольцо: подпись d ВНУТРИ отверстия (bbox в круге R=46.4)',
              ring.get('found') and ring.get('maxDist', 999) <= 46.4, ring)

        # ---------- B: взаимодействие ----------
        print('B. Взаимодействие (тёмная):')
        # низкий вьюпорт 480×450 — страницы геометрии гарантированно
        # выше экрана: прокрутка к кнопке уводит фигуру из вида
        ctxs, pages = setup_ctx(browser, 'dark', {'width': 480, 'height': 450})
        pages.on('pageerror', lambda e: errors_all.append(str(e)))
        pages.goto('http://localhost:%d/index.html' % PORT)
        pages.wait_for_timeout(2200)

        # B1: круг — ввод + «Рассчитать» + автопрокрутка к фигуре
        pages.evaluate("navigateTo('geo-circle')")
        pages.wait_for_timeout(2200)
        pages.fill('#gc_diameter', '150')
        pages.wait_for_timeout(350)
        st = pages.evaluate("""(() => {
            const svg = document.getElementById('gcFig');
            const dims = {};
            svg.querySelectorAll('text.gf-dimtx').forEach(t =>
                dims[t.textContent] = 1);
            return {dims: Object.keys(dims),
                    static: document.getElementById('gcFigFrame')
                        .classList.contains('geo-static'),
                    vals: Array.from(svg.querySelectorAll('text.gf-val'))
                        .map(t => t.textContent)};
        })()""")
        check('ввод 150 → подпись «D = 150 мм» мгновенно',
              'D = 150 мм' in st.get('dims', []), st.get('dims'))
        check('ввод → режим geo-static', st.get('static') is True)
        check('ввод → 176,71 см² в картинке', '176,71 см²' in st.get('vals', []),
              st.get('vals'))
        # прокручиваем страницу ВНИЗ к кнопке, фигура уходит из вида
        pages.evaluate("document.querySelector('#page-geo-circle .scale-calc-btn')" +
                      ".scrollIntoView({block:'end'})")
        pages.wait_for_timeout(300)
        rect0 = pages.evaluate("""(() => {
            const r = document.getElementById('gcFigFrame').getBoundingClientRect();
            return {top: r.top, bottom: r.bottom, vh: window.innerHeight};
        })()""")
        check('до «Рассчитать»: фигура вне вьюпорта (прокрутили к кнопке)',
              rect0['top'] < -10 or rect0['bottom'] > rect0['vh'] + 10, rect0)
        pages.click('#page-geo-circle .scale-calc-btn')
        pages.wait_for_timeout(1300)          # плавная прокрутка + анимация
        st = pages.evaluate("""(() => {
            const f = document.getElementById('gcFigFrame');
            const svg = document.getElementById('gcFig');
            return {static: f.classList.contains('geo-static'),
                    vals: Array.from(svg.querySelectorAll('text.gf-val'))
                        .map(t => t.textContent)};
        })()""")
        check('«Рассчитать» → анимация перезапущена (geo-static снят)',
              st.get('static') is False)
        rect1 = pages.evaluate("""(() => {
            const r = document.getElementById('gcFigFrame').getBoundingClientRect();
            return {top: r.top, bottom: r.bottom, vh: window.innerHeight};
        })()""")
        check('«Рассчитать» → экран смещён К ФИГУРЕ (рамка в вьюпорте)',
              rect1['top'] >= -2 and rect1['bottom'] <= rect1['vh'] + 2, rect1)
        check('«Рассчитать» → панели #gc_results в DOM НЕТ',
              pages.evaluate("document.getElementById('gc_results')") is None)
        check('«Рассчитать» → ВСЕ результаты в картинке (3 строки)',
              len(st.get('vals', [])) == 3, st.get('vals'))
        pages.wait_for_timeout(1500)
        shot(pages, 'scroll-480-geo-circle-recalc150.png')

        # B2: гориз. цилиндр — h=1,9 (fallback повернутая) и h=0,2 (над линией)
        pages.evaluate("navigateTo('geo-horiz')")
        pages.wait_for_timeout(2200)
        pages.fill('#gh_level', '1,9')
        pages.wait_for_timeout(400)
        st = pages.evaluate("""(() => {
            const svg = document.getElementById('ghFig');
            const t = Array.from(svg.querySelectorAll('text.gf-dimtx'))
                .find(x => x.textContent.indexOf('h = ') === 0);
            return t ? {txt: t.textContent,
                        rotated: (t.getAttribute('transform') || '')
                            .indexOf('rotate') !== -1,
                        y: parseFloat(t.getAttribute('y') || '0')} : null;
        })()""")
        check('gh h=1,9 (места нет): повернутая подпись у линии (fallback)',
              st is not None and st.get('rotated') is True, st)
        pages.fill('#gh_level', '0,2')
        pages.wait_for_timeout(400)
        st = pages.evaluate("""(() => {
            const svg = document.getElementById('ghFig');
            const t = Array.from(svg.querySelectorAll('text.gf-dimtx'))
                .find(x => x.textContent.indexOf('h = ') === 0);
            return t ? {txt: t.textContent,
                        rotated: (t.getAttribute('transform') || '')
                            .indexOf('rotate') !== -1,
                        y: parseFloat(t.getAttribute('y') || '0')} : null;
        })()""")
        check('gh h=0,2: значение НАД линией зеркала (не повернуто)',
              st is not None and st.get('rotated') is False and
              100 <= st.get('y', 0) <= 120, st)
        pages.fill('#gh_level', '1,5')
        pages.wait_for_timeout(400)
        shot(pages, 'scroll-450-geo-horiz-levels.png')
        ctxs.close()

        # B3: «Рассчитать» на gh — прокрутка к фигуре (вьюпорт 480×700:
        # страница gh (~720) выше экрана, рамка 416 — помещается)
        ctxh, pageh = setup_ctx(browser, 'dark', {'width': 480, 'height': 700})
        pageh.on('pageerror', lambda e: errors_all.append(str(e)))
        pageh.goto('http://localhost:%d/index.html' % PORT)
        pageh.wait_for_timeout(2200)
        pageh.evaluate("navigateTo('geo-horiz')")
        pageh.wait_for_timeout(2300)
        pageh.evaluate("document.querySelector('#page-geo-horiz .scale-calc-btn')" +
                      ".scrollIntoView({block:'end'})")
        pageh.wait_for_timeout(300)
        rect0 = pageh.evaluate("""(() => {
            const r = document.getElementById('ghFigFrame').getBoundingClientRect();
            return {top: r.top, bottom: r.bottom, vh: window.innerHeight};
        })()""")
        check('gh до «Рассчитать»: фигура вне вьюпорта',
              rect0['top'] < -10 or rect0['bottom'] > rect0['vh'] + 10, rect0)
        pageh.click('#page-geo-horiz .scale-calc-btn')
        pageh.wait_for_timeout(1300)
        rect = pageh.evaluate("""(() => {
            const r = document.getElementById('ghFigFrame').getBoundingClientRect();
            return {top: r.top, bottom: r.bottom, vh: window.innerHeight};
        })()""")
        check('gh «Рассчитать» → экран к фигуре (рамка в вьюпорте)',
              rect['top'] >= -2 and rect['bottom'] <= rect['vh'] + 2, rect)
        st = pageh.evaluate("""(() => {
            const svg = document.getElementById('ghFig');
            return Array.from(svg.querySelectorAll('text.gf-val'))
                .map(t => t.textContent);
        })()""")
        check('gh «Рассчитать» → 5 строк результатов в картинке',
              len(st) == 5, st)
        check('gh «Рассчитать» → масса воды в картинке',
              any(v.endswith(' кг') for v in st), st)
        pageh.wait_for_timeout(1200)
        shot(pageh, 'scroll-480-geo-horiz-recalc.png')
        ctxh.close()

        # ---------- C: десктоп, светлая тема ----------
        ctx2, page2 = setup_ctx(browser, 'light', {'width': 1280, 'height': 720})
        page2.on('pageerror', lambda e: errors_all.append(str(e)))
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)

        print('C. Десктоп, светлая тема (бежево-бело-молочная бумага):')
        for page_id, key, labels, results, nrows, yrules in GEO_PAGES:
            page2.evaluate("navigateTo('" + page_id + "')")
            page2.wait_for_timeout(450)
            st = fig_state(page2, key)
            check_page(st, page_id, labels, results, nrows, 'rgb(247, 242, 230)', yrules)
            check(page_id + ': подписи читаемы (терракота #B05537)',
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
        for page_id, key, nrows in [('geo-horiz', 'gh', 5), ('geo-circle', 'gc', 3),
                                    ('geo-ring', 'gr', 2)]:
            page3.evaluate("navigateTo('" + page_id + "')")
            page3.wait_for_timeout(2500)
            st = fig_state(page3, key)
            check(page_id + ' (мобайл): рамка видима, не обрезана',
                  st.get('visible') and st.get('notClipped') is True,
                  {'w': st.get('w'), 'clip': st.get('notClipped')})
            check(page_id + ' (мобайл): ВСЕ результаты в картинке (%d)' % nrows,
                  len(st.get('values', [])) == nrows, st.get('values'))
            check(page_id + ' (мобайл): строки не наезжают',
                  len(st.get('rowClash', [])) == 0, st.get('rowClash'))
            if key == 'gh':
                check('geo-horiz (мобайл): жидкость есть', st.get('liquid') is True)
                d = st.get('dims', {}).get('h = 1,5 м')
                check('geo-horiz (мобайл): h НАД линией зеркала',
                      d is not None and d.get('rotated') is False, d)
            # «Рассчитать» → прокрутка к фигуре
            page3.evaluate("document.querySelector('#page-" + page_id +
                           " .scale-calc-btn').scrollIntoView({block:'end'})")
            page3.wait_for_timeout(300)
            page3.click('#page-' + page_id + ' .scale-calc-btn')
            page3.wait_for_timeout(1300)
            rect = page3.evaluate("""(() => {
                const r = document.getElementById('%sFigFrame').getBoundingClientRect();
                return {top: r.top, bottom: r.bottom, vh: window.innerHeight};
            })()""" % key)
            check(page_id + ' (мобайл): «Рассчитать» → экран к фигуре',
                  rect['top'] >= -2 and rect['bottom'] <= rect['vh'] + 2, rect)
            shot(page3, 'mobile-dark-' + page_id + '.png')
        ctx3.close()

        browser.close()

    print('E. JS-ошибки:')
    check('0 JS-ошибок во всех сценариях', len(errors_all) == 0, errors_all[:3])

    print('\nИТОГО: %d passed, %d failed' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
