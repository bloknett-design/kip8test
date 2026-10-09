#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 490: browser-check — заявка «Датчики температуры» мобильная
# версия: кнопки-карточки по ДВЕ в строке, с одинаковой градуировкой
# рядом; на кнопках ТС только градуировка + температурный
# коэффициент, на кнопках ТП наименование с градуировкой; ТХА (K) и
# ТХК (L) вместе.
#   1. МОБАЙЛ 375 тёмная: сетка ДВЕ колонки; пары ТС в одной строке
#      с одинаковой α (50М+100М 0,00428; 50М+100М 0,00426; 50П+100П
#      0,00391; Pt100+Pt1000 0,00385); ТХА (K)+ТХК (L) в одной строке;
#      ТЖК (J)+ТМК (T), ТХКн (E)+ТНН (N), ТПП (R)+ТПП (S) парами;
#      ТПР (B) — во всю строку; на мобильном СКРЫТЫ: аналог в скобках,
#      R₀, материал ТП, диапазон НСХ (computed display none); ширина
#      кнопки ≈ половина строки; звезда/клик/страница датчика живы.
#   2. ДЕСКТОП 1280: полная карточка (аналог, R₀, НСХ видимы),
#      сетка auto-fill, порядок ТП K,L,J,T,E,N,R,S,B.
#   3. СВЕТЛАЯ тема мобайл: читаемость, скриншот.
# + 0 JS-ошибок; скриншоты в download/kip8test-task490/.
import json
import os
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8975
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task490')
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
          (('  [' + str(extra)[:220] + ']') if (extra and not ok) else ''))


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
                      body='not found (browser-check t490)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Геометрия и видимость карточек: пары строк, скрытые части
GEO_JS = r"""(() => {
    const out = {rtd: [], tc: []};
    const grab = (box, arr) => {
        const cards = [...box.querySelectorAll('.ts-card')];
        cards.forEach(c => {
            const r = c.getBoundingClientRect();
            const vis = el => {
                if (!el) return null;
                const st = getComputedStyle(el);
                return st.display === 'none' ? null
                    : el.textContent.trim();
            };
            arr.push({
                key: (c.getAttribute('onclick') || '')
                    .replace(/openTempSensor\('|'\)/g, '')
                    .replace('tc_', ''),
                // innerText УЧИТЫВАЕТ display:none (не как textContent)
                text: (c.innerText || '').replace(/[☆★›]/g, '').trim(),
                top: Math.round(r.top), left: Math.round(r.left),
                width: Math.round(r.width), height: Math.round(r.height),
                // имя ТС: видимый спан-градуировка (без аналога)
                name: vis(c.querySelector('.ts-card-name-main')) ||
                      vis(c.querySelector('.ts-card-name')),
                r0: vis(c.querySelector('.ts-card-r0')),
                alpha: vis(c.querySelector('.ts-card-alpha')),
                analog: vis(c.querySelector('.ts-card-name-analog')),
                meta: vis(c.querySelector('.ts-card-meta')),
                range: vis(c.querySelector('.ts-card-range')),
            });
        });
    };
    grab(document.getElementById('tsRtdCards'), out.rtd);
    grab(document.getElementById('tsTcCards'), out.tc);
    const g = getComputedStyle(document.getElementById('tsRtdCards'));
    out.gridCols = g.gridTemplateColumns;
    return out;
})()"""

TC_ORDER_JS = r"""(() => {
    const box = document.getElementById('tsTcCards');
    return [...box.querySelectorAll('.ts-card')].map(c =>
        (c.getAttribute('onclick') || '').replace(
            /openTempSensor\('tc_|'\)/g, ''));
})()"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= 1. МОБАЙЛ 375, тёмная =================
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t490-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(800)
        check('A: страница «Датчики температуры» активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensors').classList.contains('active')"))

        geo = page.evaluate(GEO_JS)
        check('B: мобайл — сетка ДВЕ колонки',
              len(geo['gridCols'].split()) == 2, geo['gridCols'])
        check('C: ТС-карточек 8', len(geo['rtd']) == 8, len(geo['rtd']))
        check('D: ТП-карточек 9', len(geo['tc']) == 9, len(geo['tc']))

        # --- пары ТС: одинаковая градуировка (α) в одной строке ---
        r = geo['rtd']
        pairs_ok = True
        for i in range(0, 8, 2):
            a, b = r[i], r[i + 1]
            same_row = abs(a['top'] - b['top']) < 5
            diff_col = abs(a['left'] - b['left']) > 50
            same_alpha = (a['alpha'] or '') == (b['alpha'] or '') and a['alpha']
            if not (same_row and diff_col and same_alpha):
                pairs_ok = False
        check('E: ТС — 4 строки по 2, у пары одинаковая α (одинаковая '
              'градуировка рядом)', pairs_ok,
              [(r[i]['key'], r[i + 1]['key'], r[i]['alpha']) for i in range(0, 8, 2)])
        check('F: пара 1: 50М + 100М, α = 0,00428',
              r[0]['name'] == '50М' and r[1]['name'] == '100М' and
              '0,00428' in (r[0]['alpha'] or ''),
              (r[0]['name'], r[1]['name'], r[0]['alpha']))
        check('G: пара 2: 50М + 100М, α = 0,00426',
              r[2]['name'] == '50М' and r[3]['name'] == '100М' and
              '0,00426' in (r[2]['alpha'] or ''),
              (r[2]['name'], r[3]['name'], r[2]['alpha']))
        check('H: пара 3: 50П + 100П, α = 0,00391 (ГОСТ)',
              r[4]['name'] == '50П' and r[5]['name'] == '100П' and
              '0,00391' in (r[4]['alpha'] or ''),
              (r[4]['name'], r[5]['name'], r[4]['alpha']))
        check('I: пара 4: Pt100 + Pt1000, α = 0,00385 (IEC)',
              r[6]['name'] == 'Pt100' and r[7]['name'] == 'Pt1000' and
              '0,00385' in (r[6]['alpha'] or ''),
              (r[6]['name'], r[7]['name'], r[6]['alpha']))

        # --- на кнопке ТС только градуировка + температурный коэф. ---
        check('J: ТС — R₀ скрыт на мобильном',
              all(c['r0'] is None for c in r),
              [c['r0'] for c in r])
        check('K: ТС — аналог (Cu50/Pt100/IEC) скрыт',
              all(c['analog'] is None for c in r),
              [c['analog'] for c in r])
        check('L: ТС — диапазон НСХ скрыт',
              all(c['range'] is None for c in r),
              [c['range'] for c in r])
        check('M: ТС — α (температурный коэффициент) виден на всех 8',
              all(c['alpha'] and c['alpha'].startswith('α') for c in r),
              [c['alpha'] for c in r])
        norm = lambda s: ''.join(str(s).split())
        check('N: ТС — текст кнопки = градуировка + α (без R₀/аналога)',
              all(norm(c['text']) == norm(c['name'] + c['alpha'])
                  for c in r),
              [(c['text'], c['name'], c['alpha']) for c in r[:2]])

        # --- ТП: ТХА (K)+ТХК (L) вместе; наименование + градуировка ---
        t = geo['tc']
        order = [c['key'] for c in t]
        check('O: порядок ТП K,L,J,T,E,N,R,S,B',
              order == ['K', 'L', 'J', 'T', 'E', 'N', 'R', 'S', 'B'], order)
        check('P: ТХА (K) и ТХК (L) — в одной строке (заявка)',
              abs(t[0]['top'] - t[1]['top']) < 5 and
              abs(t[0]['left'] - t[1]['left']) > 50,
              (t[0]['top'], t[1]['top'], t[0]['left'], t[1]['left']))
        check('Q: пары ТП в строках: (J,T), (E,N), (R,S)',
              all(abs(t[i]['top'] - t[i + 1]['top']) < 5 for i in (2, 4, 6)),
              [(t[i]['key'], t[i + 1]['key']) for i in (2, 4, 6)])
        check('R: ТП — кнопка = наименование (градуировка), материал скрыт',
              all(c['meta'] is None for c in t) and
              all('(' in (c['name'] or '') for c in t),
              [(c['name'], c['meta']) for c in t[:3]])
        check('S: ТП — диапазон НСХ скрыт',
              all(c['range'] is None for c in t),
              [c['range'] for c in t])
        check('T: ТП — текст кнопки без материала («хромель» и пр.)',
              all('хромель' not in c['text'] and 'константан' not in c['text']
                  and 'никросил' not in c['text'] and 'платинородий'
                  not in c['text'] for c in t),
              [c['text'] for c in t[:3]])
        b = t[8]
        half = t[0]['width']
        check('U: ТПР (B) — непарная, во всю строку',
              b['width'] > half * 1.6 and
              b['top'] > t[7]['top'],
              (b['width'], half, b['top'], t[7]['top']))
        check('V: кнопки ≈ половина строки (≥ 140px на 375)',
              all(140 <= c['width'] <= 190 for c in r + t[:8]),
              [c['width'] for c in r])
        shot(page, 'a-mobile-rtd-pairs.png')

        # --- живость: звезда, клик по кнопке, страница датчика ---
        try:
            page.click("#tsTcCards .ts-card:has-text('ТХК (L)') "
                       ".ts-card-fav-btn", timeout=4000)
            page.wait_for_timeout(400)
            check('W: звезда на компактной кнопке работает (★, счётчик 1)',
                  page.evaluate(
                      "document.getElementById('tsFavCount').textContent") == '1')
            page.click("#tsTcCards .ts-card:has-text('ТХК (L)')", timeout=4000)
            page.wait_for_timeout(700)
            # заголовок = «ТХК (L) — термопара» → проверка вхождением
            title_txt = page.evaluate(
                "document.getElementById('tempSensorViewTitle').textContent")
            check('X: клик по кнопке ТХК (L) — страница датчика открыта',
                  page.evaluate(
                      "document.getElementById('page-temp-sensor-view')"
                      ".classList.contains('active')") and
                  'ТХК (L)' in (title_txt or ''), title_txt)
            shot(page, 'b-mobile-sensor-view.png')
            page.evaluate("navigateTo('temp-sensors')")
            page.wait_for_timeout(600)
        except Exception as e:
            check('W/X: звезда и клик по кнопке', False, str(e))
        check('Y: мобайл — 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
        ctx.close()

        # ================= 2. ДЕСКТОП 1280, тёмная =================
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800})
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda d: d.accept())
        setup_routes(ctx2)
        ctx2.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t490-b');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('temp-sensors')")
        page2.wait_for_timeout(800)
        geo2 = page2.evaluate(GEO_JS)
        r2 = geo2['rtd']
        check('Z: десктоп — сетка НЕ две колонки (auto-fill ≥3)',
              len(geo2['gridCols'].split()) >= 3, geo2['gridCols'])
        check('AA: десктоп — R₀ виден («R₀ = 50 Ом»)',
              all(c['r0'] for c in r2), [c['r0'] for c in r2[:2]])
        check('AB: десктоп — аналог в скобках виден («(Cu50)»)',
              all(c['analog'] for c in r2), [c['analog'] for c in r2[:2]])
        check('AC: десктоп — диапазон НСХ виден',
              all(c['range'] and c['range'].startswith('НСХ') for c in r2),
              [c['range'] for c in r2[:2]])
        t2 = geo2['tc']
        check('AD: десктоп — материал ТП виден',
              all(c['meta'] for c in t2), [c['meta'] for c in t2[:2]])
        order2 = page2.evaluate(TC_ORDER_JS)
        check('AE: десктоп — порядок ТП K,L,J,T,E,N,R,S,B',
              order2 == ['K', 'L', 'J', 'T', 'E', 'N', 'R', 'S', 'B'],
              order2)
        shot(page2, 'c-desktop-full-cards.png')
        check('AF: десктоп — 0 JS-ошибок', len(js_errors2) == 0,
              js_errors2[:3])
        ctx2.close()

        # ================= 3. МОБАЙЛ 375, светлая =================
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720},
                                    is_mobile=True, has_touch=True)
        page3 = ctx3.new_page()
        js_errors3 = []
        page3.on('pageerror', lambda e: js_errors3.append(str(e)))
        page3.on('dialog', lambda d: d.accept())
        setup_routes(ctx3)
        ctx3.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t490-c');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('temp-sensors')")
        page3.wait_for_timeout(800)
        check('AG: светлая — имя кнопки читаемо (не белое на светлом)',
              page3.evaluate("""(function(){
            var n = document.querySelector('#tsRtdCards .ts-card .ts-card-name');
            return getComputedStyle(n).color.indexOf('255, 255, 255') === -1;
          })()"""))
        check('AH: светлая — α читаема',
              page3.evaluate("""(function(){
            var a = document.querySelector('#tsRtdCards .ts-card .ts-card-alpha');
            return a && getComputedStyle(a).color.indexOf('255, 255, 255') === -1;
          })()"""))
        shot(page3, 'd-mobile-light-pairs.png')
        check('AI: светлая — 0 JS-ошибок', len(js_errors3) == 0,
              js_errors3[:3])
        ctx3.close()

        browser.close()

    print('')
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
