#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 498: browser-check — заявка: «в разделе датчиков температур
# посмотри ещё раз пределы измерения … скорректируй неточности;
# укажи эти пределы в °C и в единицах измерения в полях ввода
# произвольного расчёта; в баре с названием страницы — только тип
# датчиков, например "50М (Cu50) α = 0,00428 °C⁻¹", шрифт крупнее».
#   1. МОБАЙЛ 375 тёмная, 50М: заголовок = «50М (Cu50) α = 0,00428
#      °C⁻¹» (без «— термометр сопротивления»), font-size > прежних
#      18px базовых / фиттер мог уменьшить — но ≥ 15px; подсказки
#      пределов: «−50…200 °C» и «39,3…92,8 Ом» (класс ts-calc-range,
#      видимы, 11px).
#   2. 100П: заголовок «100П (Pt100) α = 0,00391 °C⁻¹»; подсказка
#      «17,2444…395,16 Ом» — НОВАЯ формула (старая давала 18,29);
#      живой расчёт: −100 → 59,6393; 59,64 → −100.
#   3. ТХА (K): заголовок «ТХА (K)»; «−270…1372 °C» / «−6,4577…54,8864 мВ».
#   4. Каталог (граница): на карточках «НСХ: −50…200 °C» — прежние.
#   5. СВЕТЛАЯ тема: подсказки видимы и читаемы.
#   6. ДЕСКТОП 1280: заголовок 21px (базовый, без уменьшения).
# + 0 JS-ошибок; скриншоты в download/kip8test-task498/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8986
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task498')
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
                      body='not found (browser-check t498)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


TITLE_JS = r"""(() => {
    const t = document.getElementById('tempSensorViewTitle');
    const tr = document.getElementById('tempQueryTempRange');
    const vr = document.getElementById('tempQueryValRange');
    const cs = t ? getComputedStyle(t) : null;
    const csR = tr ? getComputedStyle(tr) : null;
    return {
        title: t ? t.textContent : null,
        fs: cs ? cs.fontSize : null,
        tr: tr ? tr.textContent : null,
        vr: vr ? vr.textContent : null,
        trVisible: tr ? (tr.offsetHeight > 0 && tr.offsetWidth > 0) : false,
        vrVisible: vr ? (vr.offsetHeight > 0 && vr.offsetWidth > 0) : false,
        trFs: csR ? csR.fontSize : null,
        trColor: csR ? csR.color : null,
        headerH: (document.querySelector('#page-temp-sensor-view .page-inline-header') || {}).offsetHeight
    };
})()"""


def open_sensor(page, key):
    page.evaluate("openTempSensor('%s')" % key)
    page.wait_for_timeout(600)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ============ 1. МОБАЙЛ 375, тёмная, 50М (Cu50) ============
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t498-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(600)

        # граница заявки: пределы на карточках каталога прежние
        card_range = page.evaluate(
            "(() => { const c = document.querySelector('.ts-card-range');"
            " return c ? c.textContent : null; })()")
        check('0: каталог — на карточке прежние «НСХ: −50…200 °C»',
              card_range == 'НСХ: −50…200 °C', card_range)

        open_sensor(page, 'cu50_1428')
        check('A: страница датчика активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensor-view').classList.contains('active')"))
        st = page.evaluate(TITLE_JS)
        check('B: заголовок — только тип: «50М (Cu50) α = 0,00428 °C⁻¹»',
              st['title'] == '50М (Cu50) α = 0,00428 °C⁻¹', st['title'])
        check('C: пояснение «— термометр сопротивления» убрано',
              st['title'] is not None and '— термометр' not in st['title'],
              st['title'])
        fs_px = float(str(st['fs']).replace('px', '')) if st['fs'] else 0
        check('D: шрифт заголовка крупнее (≥ 15px после фиттера; было ~13-14)',
              fs_px >= 15, st['fs'])
        check('E: подсказка °C: «−50…200 °C» (минус типографский)',
              st['tr'] == '−50…200 °C', st['tr'])
        check('F: подсказка Ом: «39,3…92,8 Ом»',
              st['vr'] == '39,3…92,8 Ом', st['vr'])
        check('G: обе подсказки видимы',
              st['trVisible'] and st['vrVisible'],
              (st['trVisible'], st['vrVisible']))
        check('H: подсказка — 11px (класс ts-calc-range)',
              st['trFs'] == '11px', st['trFs'])
        shot(page, 'a-mobile-dark-50m-title.png')

        # ---- 100П: новая формула (сверка с ГОСТ А.2) ----
        open_sensor(page, 'pt100_1391')
        st2 = page.evaluate(TITLE_JS)
        check('I: 100П заголовок «100П (Pt100) α = 0,00391 °C⁻¹»',
              st2['title'] == '100П (Pt100) α = 0,00391 °C⁻¹', st2['title'])
        check('J: 100П подсказка «−200…850 °C»',
              st2['tr'] == '−200…850 °C', st2['tr'])
        check('K: 100П подсказка «17,2444…395,16 Ом» — НОВАЯ формула '
              '(старая давала 18,29 при −200)',
              st2['vr'] == '17,2444…395,16 Ом', st2['vr'])
        # живой расчёт: −100 → 59,6393
        page.fill('#tempQueryTemp', '-100')
        page.wait_for_timeout(400)
        v = page.evaluate(
            "document.getElementById('tempQueryVal').value")
        check('L: живой расчёт: 100П t=−100 → 59,6393 Ом (А.2 ГОСТ)',
              v == '59,6393', v)
        # обратная задача: 59,64 → −100
        page.fill('#tempQueryVal', '59,64')
        page.wait_for_timeout(400)
        t = page.evaluate("document.getElementById('tempQueryTemp').value")
        tnum = float(t.replace(',', '.')) if t else None
        check('M: инверсия: 59,64 Ом → ≈ −100 °C',
              tnum is not None and abs(tnum + 100) < 0.05, t)
        shot(page, 'b-mobile-dark-100p.png')

        # ---- ТХА (K) ----
        open_sensor(page, 'tc_K')
        st3 = page.evaluate(TITLE_JS)
        check('N: ТП заголовок — только имя: «ТХА (K)»',
              st3['title'] == 'ТХА (K)', st3['title'])
        check('O: ТХА подсказка «−270…1372 °C»',
              st3['tr'] == '−270…1372 °C', st3['tr'])
        check('P: ТХА подсказка «−6,4577…54,8864 мВ»',
              st3['vr'] == '−6,4577…54,8864 мВ', st3['vr'])
        shot(page, 'c-mobile-dark-tc-k.png')
        ctx.close()

        # ============ 2. СВЕТЛАЯ тема, 50П (α = 0,00391) ============
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors += []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t498-b');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'pt50_1391')
        st4 = page.evaluate(TITLE_JS)
        check('Q: светлая: заголовок «50П (Pt50) α = 0,00391 °C⁻¹»',
              st4['title'] == '50П (Pt50) α = 0,00391 °C⁻¹', st4['title'])
        check('R: светлая: подсказки видимы и читаемы (тёмный текст)',
              st4['trVisible'] and st4['vrVisible'] and
              st4['trColor'] is not None and '255, 255, 255' not in st4['trColor'],
              (st4['tr'], st4['trColor']))
        shot(page, 'd-light-50p.png')
        ctx.close()

        # ============ 3. ДЕСКТОП 1280: базовый 21px ============
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t498-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu100_1426')
        st5 = page.evaluate(TITLE_JS)
        check('S: десктоп: заголовок 21px (базовый, без фиттера)',
              st5['fs'] == '21px', st5['fs'])
        check('T: десктоп: крошки заканчиваются на «100М (Cu100) α = 0,00426 °C⁻¹»',
              st5['title'] is not None and
              st5['title'].endswith('100М (Cu100) α = 0,00426 °C⁻¹'), st5['title'])
        check('U: десктоп: подсказки на месте (78,7…185,2 Ом — α=0,00426)',
              st5['vr'] == '78,7…185,2 Ом', st5['vr'])
        shot(page, 'e-desktop-1280-cu100.png')
        ctx.close()
        browser.close()

    print('—' * 60)
    print('ИТОГО: %d OK, %d FAIL' % (PASS, FAIL))
    print('JS-ошибок: %d' % len(js_errors))
    for e in js_errors[:5]:
        print('  JS: ' + e[:200])
    raise SystemExit(1 if (FAIL or js_errors) else 0)


if __name__ == '__main__':
    main()
