#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 491: browser-check — заявка: (1) пары кнопок ТС 50М+50М и
# 100М+100М; (2) популярные кнопки 50М, 100М, ТХА (K), ТХК (L) —
# крупнее шрифт и рамка + эффект выступа; (3) есть избранное → при
# открытии страницы сразу вкладка «Избранное» (датчики температуры +
# расходомеры хозрасчётные).
#   1. МОБАЙЛ 375 тёмная: пары (50М+50М, 100М+100М, 50П+100П,
#      Pt100+Pt1000); featured computed-стили (border 2px, шрифт 19px,
#      box-shadow, градиент) у 4 ТС + ТХА (K)/ТХК (L); обычные — 1px/15px;
#      вкладка «Все» без избранного; звезда/клик живы.
#   2. АВТОТАБ датчиков: звезда → reload → «Избранные» активна + карточка
#      с feat-классом; возврат на страницу — снова «Избранные»;
#      удаление последнего → reload → «Все».
#   3. РАСХОДОМЕРЫ: FlowFav pre-seed → открытие раздела → вкладка
#      «Избранные» (все .flow-tab синхронны); пустой FlowFav → «Все».
#   4. СВЕТЛАЯ тема мобайл: featured-стили светлой палитры, скриншот.
#   5. ДЕСКТОП 1280: featured-класс в DOM, но стили НЕ применились
#      (1px/17px/без тени); порядок каталога 50М,50М,100М,100М.
# + 0 JS-ошибок; скриншоты в download/kip8test-task491/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8977
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task491')
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
                      body='not found (browser-check t491)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Геометрия + computed-стили карточек
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
                borderColor: st.borderColor,
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


def flow_tab_state(page):
    return page.evaluate(r"""(() => {
        const btns = document.querySelectorAll('.flow-tab[data-flow-tab]');
        const out = {all: [], fav: []};
        btns.forEach(b => {
            (b.getAttribute('data-flow-tab') === 'fav' ? out.fav : out.all)
                .push(b.classList.contains('active'));
        });
        return {allOn: out.all.every(x => x), favOn: out.fav.every(x => x),
                n: btns.length};
    })()""")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= 1. МОБАЙЛ 375, тёмная, БЕЗ избранного =========
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t491-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(800)
        check('A: страница «Датчики температуры» активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensors').classList.contains('active')"))

        st = ts_tab_state(page)
        check('B: без избранного — вкладка «Все» активна',
              st.get('all', '').startswith('true') and
              st.get('fav', '').startswith('false'), st)

        geo = page.evaluate(GEO_JS)
        r = geo['rtd']
        t = geo['tc']
        check('C: сетка ДВЕ колонки', len(geo['gridCols'].split()) == 2,
              geo['gridCols'])
        check('D: 8 ТС + 9 ТП', len(r) == 8 and len(t) == 9,
              (len(r), len(t)))

        def pair_row(i, j):
            a, b = r[i], r[j]
            return abs(a['top'] - b['top']) < 5 and \
                abs(a['left'] - b['left']) > 50
        check('E: строка 1 — 50М + 50М (одна строка, разные α)',
              pair_row(0, 1) and r[0]['name'] == '50М' and
              r[1]['name'] == '50М' and
              '0,00428' in (r[0]['alpha'] or '') and
              '0,00426' in (r[1]['alpha'] or ''),
              [(r[i]['name'], r[i]['alpha']) for i in (0, 1)])
        check('F: строка 2 — 100М + 100М (одна строка, разные α)',
              pair_row(2, 3) and r[2]['name'] == '100М' and
              r[3]['name'] == '100М' and
              '0,00428' in (r[2]['alpha'] or '') and
              '0,00426' in (r[3]['alpha'] or ''),
              [(r[i]['name'], r[i]['alpha']) for i in (2, 3)])
        check('G: строки 3/4 — 50П+100П, Pt100+Pt1000 (пары 490 живы)',
              pair_row(4, 5) and pair_row(6, 7) and
              r[4]['name'] == '50П' and r[5]['name'] == '100П' and
              r[6]['name'] == 'Pt100' and r[7]['name'] == 'Pt1000',
              [(r[i]['name'], r[i]['alpha']) for i in (4, 5, 6, 7)])

        # featured computed-стили
        feats = [c for c in r if c['feat']]
        plains = [c for c in r if not c['feat']]
        check('H: ТС feat-класс ровно на 4 Cu-кнопках (обе 50М, обе 100М)',
              len(feats) == 4 and
              all(c['name'] in ('50М', '100М') for c in feats) and
              all(c['name'] in ('50П', '100П', 'Pt100', 'Pt1000')
                  for c in plains),
              [c['name'] for c in r])
        check('I: feat ТС — рамка 2px (у обычных 1px)',
              all(c['borderWidth'] == '2px' for c in feats) and
              all(c['borderWidth'] == '1px' for c in plains),
              [(c['name'], c['borderWidth']) for c in r])
        # при 375px действует блок ≤400px: feat 17px, обычные 14px
        # (значения ≤1023px — 19/15 — проверены литералами в test-task491)
        check('J: feat ТС — шрифт имени 17px на 375px (у обычных 14px)',
              all(c['nameFont'] == '17px' for c in feats) and
              all(c['nameFont'] == '14px' for c in plains),
              [(c['name'], c['nameFont']) for c in r])
        check('K: feat ТС — эффект выступа (тень + градиент)',
              all(c['boxShadow'] != 'none' and
                  'linear-gradient' in c['bgImage'] for c in feats),
              [(c['name'], c['boxShadow'][:40], c['bgImage'][:30])
               for c in feats])
        check('L: обычные ТС — без тени и градиента',
              all(c['boxShadow'] == 'none' for c in plains),
              [(c['name'], c['boxShadow']) for c in plains])

        tc_feats = [c for c in t if c['feat']]
        tc_plain_j = [c for c in t if c['key'] == 'tc_J']
        check('M: ТП feat на ТХА (K) и ТХК (L) только',
              len(tc_feats) == 2 and
              {c['key'] for c in tc_feats} == {'tc_K', 'tc_L'},
              [c['key'] for c in t])
        # на 375px: feat 17px (блок ≤400px), ТЖК (J) — 14px
        check('N: feat ТП — 2px/17px/тень; ТЖК (J) — 1px/14px/без тени',
              all(c['borderWidth'] == '2px' and c['nameFont'] == '17px' and
                  c['boxShadow'] != 'none' for c in tc_feats) and
              all(c['borderWidth'] == '1px' and c['nameFont'] == '14px' and
                  c['boxShadow'] == 'none' for c in tc_plain_j),
              [(c['key'], c['borderWidth'], c['nameFont']) for c in tc_feats])

        # живость: клик по 50М → страница датчика
        page.click("#tsRtdCards .ts-card:has-text('50М')", timeout=4000)
        page.wait_for_timeout(700)
        title_txt = page.evaluate(
            "document.getElementById('tempSensorViewTitle').textContent")
        check('O: клик по кнопке 50М — страница датчика открыта',
              '50М' in title_txt and 'термометр' in title_txt, title_txt)
        shot(page, 'a-mobile-feat-pairs.png')
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(500)

        # ================= 2. АВТОТАБ «Избранное» (датчики) ==============
        page.click("#tsRtdCards .ts-card:has-text('50М') .ts-card-fav-btn",
                   timeout=4000)
        page.wait_for_timeout(400)
        check('P: звезда работает — счётчик «Избранные» = 1',
              page.evaluate(
                  "document.getElementById('tsFavCount').textContent") == '1')

        page.reload()
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(800)
        st = ts_tab_state(page)
        check('Q: РЕЛОАД + избранное есть → вкладка «Избранные» АКТИВНА',
              st.get('fav', '').startswith('true') and
              st.get('all', '').startswith('false'), st)
        fav_cards = page.evaluate(
            "document.querySelectorAll('#tsRtdCards .ts-card').length")
        check('R: в «Избранных» — 1 карточка 50М с feat-классом',
              fav_cards == 1 and page.evaluate(
                  "document.querySelector('#tsRtdCards .ts-card')" +
                  ".className.indexOf('ts-card-feat') !== -1"),
              fav_cards)
        shot(page, 'b-mobile-fav-autotab.png')

        # ручное переключение на «Все» → уход → возврат → снова «Избранные»
        page.evaluate("setTempSensorsTab('all')")
        page.wait_for_timeout(300)
        page.evaluate("navigateTo('calc-kipa')")
        page.wait_for_timeout(400)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(600)
        st = ts_tab_state(page)
        check('S: возврат на страницу (был на «Все») — снова «Избранные»',
              st.get('fav', '').startswith('true'), st)

        # удаление последнего избранного → reload → «Все»
        page.click("#tsRtdCards .ts-card .ts-card-fav-btn", timeout=4000)
        page.wait_for_timeout(400)
        page.reload()
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(800)
        st = ts_tab_state(page)
        check('T: избранное удалено → вкладка «Все» (сброс при пустом)',
              st.get('all', '').startswith('true') and
              st.get('fav', '').startswith('false'), st)
        check('U: 0 JS-ошибок (мобайл тёмная + автотаб)', len(js_errors) == 0,
              js_errors[:3])
        ctx.close()

        # ================= 3. РАСХОДОМЕРЫ хозрасчётные ===================
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda d: d.accept())
        setup_routes(ctx2)
        seed = ("localStorage.setItem('kip8test:kip8_session_token'," +
                "'bc-t491-b');" +
                "localStorage.setItem('kip8test:kip8_flow_fav_v1'," +
                "'{\"1\":\"2026-10-01T00:00:00.000Z\"," +
                "\"3\":\"2026-10-02T00:00:00.000Z\"}');" +
                "localStorage.setItem('kip8test:kip8_flow_fav_order_v1'," +
                "'[\"1\",\"3\"]');")
        ctx2.add_init_script(seed)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('flowmeter-data')")
        page2.wait_for_timeout(1500)
        ftab = flow_tab_state(page2)
        check('V: расходомеры с FlowFav → вкладка «Избранные» АКТИВНА '
              '(все .flow-tab синхронны)',
              ftab['favOn'] and not ftab['allOn'] and ftab['n'] >= 2, ftab)
        shot(page2, 'c-flow-autotab-fav.png')

        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page3 = ctx3.new_page()
        js_errors3 = []
        page3.on('pageerror', lambda e: js_errors3.append(str(e)))
        page3.on('dialog', lambda d: d.accept())
        setup_routes(ctx3)
        ctx3.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token'," +
            "'bc-t491-c');")
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('flowmeter-data')")
        page3.wait_for_timeout(1500)
        ftab3 = flow_tab_state(page3)
        check('W: расходомеры БЕЗ избранного → вкладка «Все»',
              ftab3['allOn'] and not ftab3['favOn'], ftab3)
        check('X: расходомеры — 0 JS-ошибок',
              len(js_errors2) == 0 and len(js_errors3) == 0,
              (js_errors2[:2], js_errors3[:2]))
        ctx2.close()
        ctx3.close()

        # ================= 4. СВЕТЛАЯ тема мобайл =======================
        ctx4 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page4 = ctx4.new_page()
        js_errors4 = []
        page4.on('pageerror', lambda e: js_errors4.append(str(e)))
        page4.on('dialog', lambda d: d.accept())
        setup_routes(ctx4)
        ctx4.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t491-d');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page4.goto('http://localhost:%d/index.html' % PORT)
        page4.wait_for_timeout(2500)
        page4.evaluate("navigateTo('temp-sensors')")
        page4.wait_for_timeout(800)
        light = page4.evaluate(r"""(() => {
            const c = document.querySelector(
                '#tsRtdCards .ts-card.ts-card-feat');
            if (!c) return null;
            const st = getComputedStyle(c);
            return {borderColor: st.borderColor,
                    bgImage: st.backgroundImage,
                    boxShadow: st.boxShadow};
        })()""")
        check('Y: светлая — feat-бордер светлой палитры',
              light and '43, 111, 163' in light['borderColor'] and
              light['borderColor'].startswith('rgba(43, 111, 163'),
              light and light['borderColor'])
        check('Z: светлая — градиент и мягкая тень выступа',
              light and 'linear-gradient' in light['bgImage'] and
              light['boxShadow'] != 'none',
              light and (light['bgImage'][:40], light['boxShadow'][:40]))
        shot(page4, 'd-mobile-light-feat.png')
        check('AA: светлая — 0 JS-ошибок', len(js_errors4) == 0,
              js_errors4[:3])
        ctx4.close()

        # ================= 5. ДЕСКТОП 1280 ==============================
        ctx5 = browser.new_context(viewport={'width': 1280, 'height': 800})
        page5 = ctx5.new_page()
        js_errors5 = []
        page5.on('pageerror', lambda e: js_errors5.append(str(e)))
        page5.on('dialog', lambda d: d.accept())
        setup_routes(ctx5)
        ctx5.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t491-e');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page5.goto('http://localhost:%d/index.html' % PORT)
        page5.wait_for_timeout(2500)
        page5.evaluate("navigateTo('temp-sensors')")
        page5.wait_for_timeout(800)
        desk = page5.evaluate(r"""(() => {
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
            return out;
        })()""")
        check('AB: десктоп — feat-класс в DOM, но рамка 1px (стили только '
              'мобильные)',
              any(c['feat'] for c in desk) and
              all(c['bw'] == '1px' for c in desk),
              [(c['name'], c['feat'], c['bw']) for c in desk[:4]])
        check('AC: десктоп — шрифт имени 17px (база), без тени/градиента',
              all(c['fs'] == '17px' and c['sh'] == 'none' and
                  c['bg'] == 'none' for c in desk),
              [(c['name'], c['fs'], c['sh'][:20]) for c in desk[:4]])
        check('AD: десктоп — порядок ТС 50М, 50М, 100М, 100М, …',
              [c['name'] for c in desk[:4]] == ['50М', '50М', '100М', '100М'],
              [c['name'] for c in desk])
        shot(page5, 'e-desktop-no-feat.png')
        check('AE: десктоп — 0 JS-ошибок', len(js_errors5) == 0,
              js_errors5[:3])
        ctx5.close()

        browser.close()

    print('')
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
