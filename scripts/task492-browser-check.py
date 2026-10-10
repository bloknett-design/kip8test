#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 492: browser-check — заявка: (1) кнопки «Все/Избранные» датчиков
# температуры сместить ВНИЗ и оформить как в расходомерах; (2) оформление
# кнопок вернуть как прежде, но крупный шрифт оставить и сделать у всех;
# (3) featured-оформление (выступ) — у кнопок в избранном.
#   1. МОБАЙЛ 375 тёмная, БЕЗ избранного: нижний бар #tsBottomBar виден
#      (fixed/grid/2 кнопки/счётчики 17/0), верхние .ts-tabs скрыты,
#      отступ .ts-page 96px; сетка 2-в-ряд, пары живы; НЕТ feat-классов;
#      у ВСЕХ кнопок шрифт 17px (≤400px) и рамка 1px без тени/градиента;
#      клики по кнопкам нижнего бара (Избранные → пусто → Все); уход со
#      страницы — бар скрыт; клик по карточке открывает датчик.
#   2. ИЗБРАННОЕ: звезда на 50М → карточка СРАЗУ feat (2px/тень/градиент,
#      шрифт тот же 17px), счётчик бара = 1; reload → автотаб «Избранные»
#      (кнопка бара active), карточка feat; «Все» через кнопку бара —
#      feat только у избранного.
#   3. СВЕТЛАЯ тема мобайл: бар виден, кнопка светлой палитры; feat —
#      светлая рамка/градиент/мягкая тень.
#   4. ДЕСКТОП 1280: бар СКРЫТ, верхние .ts-tabs ВИДНЫ; feat-класс в DOM
#      (посев kip8_temp_fav_v1) без стилей (1px/17px/без тени).
# + 0 JS-ошибок; скриншоты в download/kip8test-task492/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8976
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task492')
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
          (('  [' + str(extra)[:200] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=False)
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'flowmeter.view': True,
                                'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


def setup_routes(ctx):
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200,
                      content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action),
                                      ensure_ascii=False).encode('utf-8'))

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (browser-check t492)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Состояние нижнего бара + верхних табов + карточек
BAR_JS = r"""(() => {
    const bar = document.getElementById('tsBottomBar');
    const top = document.querySelector('.ts-tabs');
    if (!bar) return {bar: false};
    const bst = getComputedStyle(bar);
    const btns = [...bar.querySelectorAll('.ts-tab')];
    const page = document.querySelector('.ts-page');
    return {
        bar: true,
        barDisplay: bst.display,
        barPosition: bst.position,
        barBottom: bst.bottom,
        barZ: bst.zIndex,
        barBorderTop: bst.borderTopWidth,
        topDisplay: top ? getComputedStyle(top).display : 'none-el',
        pagePadBottom: page ? getComputedStyle(page).paddingBottom : null,
        btnN: btns.length,
        btnActive: btns.map(b => b.classList.contains('active')),
        btnFont: btns.map(b => getComputedStyle(b).fontSize),
        btnHeight: btns.map(b => Math.round(b.getBoundingClientRect().height)),
        btnWidth: btns.map(b => Math.round(b.getBoundingClientRect().width)),
        allCount: (document.getElementById('tsAllCountMob')||{}).textContent,
        favCount: (document.getElementById('tsFavCountMob')||{}).textContent,
        barRect: (r => ({t: Math.round(r.top), h: Math.round(r.height)}))(bar.getBoundingClientRect())
    };
})()"""

GEO_JS = r"""(() => {
    const out = {rtd: [], tc: []};
    const vis = el => {
        if (!el) return null;
        const st = getComputedStyle(el);
        return st.display === 'none' ? null : el.textContent.trim();
    };
    const grab = (box, arr) => {
        [...box.querySelectorAll('.ts-card')].forEach(c => {
            const r = c.getBoundingClientRect();
            const st = getComputedStyle(c);
            const nameEl = c.querySelector('.ts-card-name-main') ||
                           c.querySelector('.ts-card-name');
            const nst = nameEl ? getComputedStyle(nameEl) : null;
            arr.push({
                key: (c.getAttribute('onclick') || '')
                    .replace(/openTempSensor\('|'\)/g, ''),
                feat: c.className.indexOf('ts-card-feat') !== -1,
                name: vis(c.querySelector('.ts-card-name-main')) ||
                      vis(c.querySelector('.ts-card-name')),
                alpha: vis(c.querySelector('.ts-card-alpha')),
                top: Math.round(r.top), left: Math.round(r.left),
                width: Math.round(r.width),
                borderWidth: st.borderWidth,
                boxShadow: st.boxShadow,
                bgImage: st.backgroundImage,
                nameFont: nst ? nst.fontSize : null
            });
        });
    };
    grab(document.getElementById('tsRtdCards'), out.rtd);
    grab(document.getElementById('tsTcCards'), out.tc);
    out.gridCols = getComputedStyle(
        document.getElementById('tsRtdCards')).gridTemplateColumns;
    return out;
})()"""


def ts_tab_state(page):
    return page.evaluate(r"""(() => {
        const btns = document.querySelectorAll('.ts-tab[data-ts-tab]');
        const out = {};
        btns.forEach(b => {
            out[b.getAttribute('data-ts-tab')] =
                b.classList.contains('active') + '/' +
                b.getAttribute('aria-selected');
        });
        return out;
    })()""")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ============ 1. МОБАЙЛ 375, тёмная, БЕЗ избранного =============
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t492-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(800)
        check('A: страница «Датчики температуры» активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensors').classList.contains('active')"))

        st = ts_tab_state(page)
        check('B: без избранного — вкладка «Все» активна (синхронно)',
              st.get('all', '').startswith('true') and
              st.get('fav', '').startswith('false'), st)

        bar = page.evaluate(BAR_JS)
        check('C: нижний бар ВИДЕН — display grid, fixed, bottom 0',
              bar['bar'] and bar['barDisplay'] == 'grid' and
              bar['barPosition'] == 'fixed' and bar['barBottom'] == '0px',
              bar)
        check('D: верхние .ts-tabs на мобильном СКРЫТЫ',
              bar['topDisplay'] == 'none', bar['topDisplay'])
        check('E: 2 кнопки, активна «Все», счётчики 17/0',
              bar['btnN'] == 2 and bar['btnActive'][0] and
              not bar['btnActive'][1] and bar['allCount'] == '17' and
              bar['favCount'] == '0',
              (bar['btnN'], bar['btnActive'], bar['allCount'],
               bar['favCount']))
        check('F: кнопки равной ширины (~1/2 экрана), высота ≥48px',
              abs(bar['btnWidth'][0] - bar['btnWidth'][1]) <= 2 and
              all(h >= 48 for h in bar['btnHeight']),
              (bar['btnWidth'], bar['btnHeight']))
        check('G: шрифт кнопок 15px на 375px (≤400px), z-index 80',
              all(f == '15px' for f in bar['btnFont']) and
              bar['barZ'] == '80', (bar['btnFont'], bar['barZ']))
        check('H: бар прижат к низу окна, отступ .ts-page 96px',
              bar['barRect']['t'] + bar['barRect']['h'] >= 715 and
              bar['pagePadBottom'] == '96px',
              (bar['barRect'], bar['pagePadBottom']))

        geo = page.evaluate(GEO_JS)
        r = geo['rtd']
        t = geo['tc']
        check('I: сетка ДВЕ колонки', len(geo['gridCols'].split()) == 2,
              geo['gridCols'])
        check('J: 8 ТС + 9 ТП', len(r) == 8 and len(t) == 9,
              (len(r), len(t)))

        def pair_row(i, j):
            a, b = r[i], r[j]
            return abs(a['top'] - b['top']) < 5 and \
                abs(a['left'] - b['left']) > 50
        check('K: пары живы — 50М+50М, 100М+100М, 50П+100П, Pt100+Pt1000',
              pair_row(0, 1) and pair_row(2, 3) and pair_row(4, 5) and
              pair_row(6, 7) and r[0]['name'] == '50М' and
              r[2]['name'] == '100М' and r[4]['name'] == '50П' and
              r[6]['name'] == 'Pt100',
              [(c['name'], c['alpha']) for c in r])

        check('L: БЕЗ избранного — 0 feat-классов (популярные обычные)',
              not any(c['feat'] for c in r + t),
              [(c['name'], c['feat']) for c in r[:4]])
        check('M: у ВСЕХ кнопок шрифт 17px (единый, бывший featured)',
              all(c['nameFont'] == '17px' for c in r + t),
              [(c['name'], c['nameFont']) for c in r[:4]])
        check('N: у ВСЕХ кнопок рамка 1px, без тени/градиента',
              all(c['borderWidth'] == '1px' and
                  c['boxShadow'] == 'none' and
                  c['bgImage'] == 'none' for c in r + t),
              [(c['name'], c['borderWidth'], c['boxShadow'][:20])
               for c in r[:4]])

        # клики по кнопкам НИЖНЕГО БАРА: Избранные → пусто → Все
        page.click("#tsBottomBar .ts-tab[data-ts-tab='fav']", timeout=4000)
        page.wait_for_timeout(500)
        check('O: клик «Избранные» в баре — пустой блок, «Избранные» active',
              page.evaluate(
                  "document.querySelector('#tsBottomBar .ts-tab[data-ts-tab=\\'fav\\']').classList.contains('active')") and
              page.evaluate(
                  "document.getElementById('tsRtdCards').textContent.indexOf('Нет избранных датчиков') !== -1"))
        shot(page, 'a-mobile-empty-fav.png')
        page.click("#tsBottomBar .ts-tab[data-ts-tab='all']", timeout=4000)
        page.wait_for_timeout(500)
        check('P: клик «Все» в баре — карточки вернулись',
              page.evaluate(
                  "document.querySelectorAll('#tsRtdCards .ts-card').length") == 8)

        # клик по карточке — страница датчика
        page.click("#tsRtdCards .ts-card:has-text('50М')", timeout=4000)
        page.wait_for_timeout(700)
        title_txt = page.evaluate(
            "document.getElementById('tempSensorViewTitle').textContent")
        check('Q: клик по кнопке 50М — страница датчика открыта',
              '50М' in title_txt and 'термометр' in title_txt, title_txt)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(500)

        # уход со страницы — бар скрыт
        page.evaluate("navigateTo('calc-kipa')")
        page.wait_for_timeout(500)
        bar_hidden = page.evaluate(
            "getComputedStyle(document.getElementById('tsBottomBar')).display")
        check('R: уход со страницы — нижний бар СКРЫТ', bar_hidden == 'none',
              bar_hidden)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(500)

        # ============ 2. ИЗБРАННОЕ на мобайле (тот же контекст) =========
        page.click("#tsRtdCards .ts-card:has-text('50М') .ts-card-fav-btn",
                   timeout=4000)
        page.wait_for_timeout(400)
        # ПОДВОДНЫЙ КАМЕНЬ: page.click оставляет мышь над карточкой →
        # :hover (.ts-card:hover { background: var(--active-bg) },
        # специфичность (0,2,0) > .ts-card-feat (0,1,0)) перекрывает
        # градиент выступа; отводим мышь, чтобы считать «покой» карточки
        page.mouse.move(10, 10)
        page.wait_for_timeout(200)
        fav_now = page.evaluate(r"""(() => {
            // :has-text — селектор Playwright, в querySelector нельзя;
            // ищем карточку по onclick-ключу первой 50М (cu50_1428)
            const c = document.querySelector(
                "#tsRtdCards .ts-card[onclick*='cu50_1428']");
            if (!c) return null;
            const st = getComputedStyle(c);
            const nameEl = c.querySelector('.ts-card-name-main') ||
                           c.querySelector('.ts-card-name');
            return {feat: c.className.indexOf('ts-card-feat') !== -1,
                    bw: st.borderWidth, sh: st.boxShadow,
                    bg: st.backgroundImage,
                    bgFull: st.background,
                    fs: nameEl ? getComputedStyle(nameEl).fontSize : null,
                    favCount: document.getElementById('tsFavCountMob').textContent};
        })()""")
        check('S: звезда на 50М → карточка СРАЗУ feat (2px/тень/градиент)',
              fav_now and fav_now['feat'] and fav_now['bw'] == '2px' and
              fav_now['sh'] != 'none' and
              ('linear-gradient' in fav_now['bg'] or
               'linear-gradient' in fav_now['bgFull']),
              fav_now and (fav_now['bg'], fav_now['bgFull'][:80]))
        check('T: feat-шрифт = общему (17px), счётчик бара = 1',
              fav_now and fav_now['fs'] == '17px' and
              fav_now['favCount'] == '1', fav_now)

        geo2 = page.evaluate(GEO_JS)
        r2 = geo2['rtd']
        feats = [c for c in r2 if c['feat']]
        plains = [c for c in r2 if not c['feat']]
        check('U: feat ровно 1 (избранная 50М), остальные обычные',
              len(feats) == 1 and len(plains) == 7 and
              feats[0]['name'] == '50М' and all(
                  c['borderWidth'] == '1px' and c['boxShadow'] == 'none'
                  for c in plains),
              [(c['name'], c['feat']) for c in r2])
        shot(page, 'b-mobile-fav-feat.png')

        page.reload()
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(800)
        st2 = ts_tab_state(page)
        check('V: РЕЛОАД + избранное → автотаб «Избранные» (кнопка бара active)',
              st2.get('fav', '').startswith('true') and
              st2.get('all', '').startswith('false'), st2)
        fav_cards = page.evaluate(
            "document.querySelectorAll('#tsRtdCards .ts-card').length")
        check('W: в «Избранных» — 1 карточка 50М с feat-классом',
              fav_cards == 1 and page.evaluate(
                  "document.querySelector('#tsRtdCards .ts-card')" +
                  ".className.indexOf('ts-card-feat') !== -1"),
              fav_cards)
        bar2 = page.evaluate(BAR_JS)
        check('X: счётчики бара после релоада: 17/1, «Избранные» active',
              bar2['allCount'] == '17' and bar2['favCount'] == '1' and
              bar2['btnActive'][1] and not bar2['btnActive'][0],
              (bar2['allCount'], bar2['favCount'], bar2['btnActive']))

        page.click("#tsBottomBar .ts-tab[data-ts-tab='all']", timeout=4000)
        page.wait_for_timeout(500)
        geo3 = page.evaluate(GEO_JS)
        check('Y: «Все» через кнопку бара — 8 ТС, feat только у 50М',
              len(geo3['rtd']) == 8 and
              sum(1 for c in geo3['rtd'] if c['feat']) == 1,
              [(c['name'], c['feat']) for c in geo3['rtd']])
        check('Z: 0 JS-ошибок (мобайл тёмная)', len(js_errors) == 0,
              js_errors[:3])
        ctx.close()

        # ================= 3. СВЕТЛАЯ тема мобайл =======================
        ctx4 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page4 = ctx4.new_page()
        js_errors4 = []
        page4.on('pageerror', lambda e: js_errors4.append(str(e)))
        page4.on('dialog', lambda d: d.accept())
        setup_routes(ctx4)
        ctx4.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t492-b');" +
            "localStorage.setItem('kip8test:app-theme','light');" +
            "localStorage.setItem('kip8test:kip8_temp_fav_v1'," +
            "'{\\\"cu50_1428\\\":\\\"2026-10-01T00:00:00.000Z\\\"}');")
        page4.goto('http://localhost:%d/index.html' % PORT)
        page4.wait_for_timeout(2500)
        page4.evaluate("navigateTo('temp-sensors')")
        page4.wait_for_timeout(800)
        light = page4.evaluate(r"""(() => {
            const barBtn = document.querySelector(
                "#tsBottomBar .ts-tab[data-ts-tab='all']");
            const c = document.querySelector(
                '#tsRtdCards .ts-card.ts-card-feat');
            const out = {btnColor: barBtn ? getComputedStyle(barBtn).color
                                          : null};
            if (c) {
                const st = getComputedStyle(c);
                out.borderColor = st.borderColor;
                out.bgImage = st.backgroundImage;
                out.boxShadow = st.boxShadow;
            }
            out.favActive = !!(document.querySelector(
                "#tsBottomBar .ts-tab[data-ts-tab='fav']").classList
                .contains('active'));
            return out;
        })()""")
        check('AA: светлая — автотаб «Избранные», кнопка светлой палитры',
              light['favActive'] and light['btnColor'] and
              light['btnColor'].startswith('rgba(43, 111, 163'), light)
        check('AB: светлая — feat-бордер светлой палитры + градиент/тень',
              light.get('borderColor', '').startswith('rgba(43, 111, 163') and
              'linear-gradient' in light.get('bgImage', '') and
              light.get('boxShadow', 'none') != 'none',
              (light.get('borderColor'), light.get('boxShadow', '')[:40]))
        shot(page4, 'c-mobile-light-fav-feat.png')
        check('AC: светлая — 0 JS-ошибок', len(js_errors4) == 0,
              js_errors4[:3])
        ctx4.close()

        # ================= 4. ДЕСКТОП 1280 ==============================
        ctx5 = browser.new_context(viewport={'width': 1280, 'height': 800})
        page5 = ctx5.new_page()
        js_errors5 = []
        page5.on('pageerror', lambda e: js_errors5.append(str(e)))
        page5.on('dialog', lambda d: d.accept())
        setup_routes(ctx5)
        ctx5.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t492-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            "localStorage.setItem('kip8test:kip8_temp_fav_v1'," +
            "'{\\\"cu50_1428\\\":\\\"2026-10-01T00:00:00.000Z\\\"}');")
        page5.goto('http://localhost:%d/index.html' % PORT)
        page5.wait_for_timeout(2500)
        page5.evaluate("navigateTo('temp-sensors')")
        page5.wait_for_timeout(800)
        desk = page5.evaluate(r"""(() => {
            const bar = document.getElementById('tsBottomBar');
            const top = document.querySelector('.ts-tabs');
            const cards = [...document.querySelectorAll('#tsRtdCards .ts-card')];
            const out = [];
            cards.forEach(c => {
                const nameEl = c.querySelector('.ts-card-name-main') ||
                               c.querySelector('.ts-card-name');
                out.push({
                    name: nameEl ? nameEl.textContent.trim() : '',
                    feat: c.className.indexOf('ts-card-feat') !== -1,
                    bw: getComputedStyle(c).borderWidth,
                    fs: nameEl ? getComputedStyle(nameEl).fontSize : null,
                    sh: getComputedStyle(c).boxShadow,
                    bg: getComputedStyle(c).backgroundImage
                });
            });
            return {
                barDisplay: bar ? getComputedStyle(bar).display : 'none-el',
                topDisplay: top ? getComputedStyle(top).display : 'none-el',
                cards: out,
                topBtnActive: !!(document.querySelector(
                    ".ts-tabs .ts-tab[data-ts-tab='fav']").classList
                    .contains('active'))
            };
        })()""")
        check('AD: десктоп — нижний бар СКРЫТ, верхние .ts-tabs ВИДНЫ',
              desk['barDisplay'] == 'none' and desk['topDisplay'] == 'flex',
              (desk['barDisplay'], desk['topDisplay']))
        check('AE: десктоп — автотаб «Избранные» и ВЕРХНЕЙ вкладкой',
              desk['topBtnActive'], desk['topBtnActive'])
        check('AF: десктоп — feat-класс в DOM, но рамка 1px (стили mobile)',
              any(c['feat'] for c in desk['cards']) and
              all(c['bw'] == '1px' for c in desk['cards']),
              [(c['name'], c['feat'], c['bw'])
               for c in desk['cards'][:4]])
        # посев избранного → автотаб «Избранные» (проверено AE/AF выше);
        # для шрифта и ПОРЯДКА каталога переключаемся на «Все»
        page5.evaluate("setTempSensorsTab('all')")
        page5.wait_for_timeout(400)
        desk_all = page5.evaluate(r"""(() => {
            const cards = [...document.querySelectorAll('#tsRtdCards .ts-card')];
            return cards.map(c => {
                const nameEl = c.querySelector('.ts-card-name-main') ||
                               c.querySelector('.ts-card-name');
                return {
                    name: nameEl ? nameEl.textContent.trim() : '',
                    feat: c.className.indexOf('ts-card-feat') !== -1,
                    fs: nameEl ? getComputedStyle(nameEl).fontSize : null,
                    sh: getComputedStyle(c).boxShadow,
                    bg: getComputedStyle(c).backgroundImage
                };
            });
        })()""")
        check('AG: десктоп — шрифт 17px (база), без тени/градиента',
              len(desk_all) == 8 and
              all(c['fs'] == '17px' and c['sh'] == 'none' and
                  c['bg'] == 'none' for c in desk_all),
              [(c['name'], c['fs']) for c in desk_all[:4]])
        check('AH: десктоп — порядок ТС 50М, 50М, 100М, 100М, …',
              [c['name'] for c in desk_all[:4]] ==
              ['50М', '50М', '100М', '100М'],
              [c['name'] for c in desk_all])
        shot(page5, 'd-desktop-top-tabs.png')
        check('AI: десктоп — 0 JS-ошибок', len(js_errors5) == 0,
              js_errors5[:3])
        ctx5.close()

        browser.close()

    print('')
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
