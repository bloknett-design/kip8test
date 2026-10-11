#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 499: browser-check — заявка: «Подсказки диапазонов впиши
# непосредственно в поля ввода, бледным текстом, вместо предложения
# "Например: 55" и так далее. И проверь у 50М (Cu50) α = 0,00428 °C⁻¹
# диапазон по моему -180...200 °C.»
#   1. МОБАЙЛ 375 тёмная, 50М: плейсхолдер поля температуры =
#      «−180…200 °C» (НЕ «Например: 55»), поля значения =
#      «10,2642…92,8 Ом»; оба — бледный ::placeholder (0.4/0.45);
#      div-подсказок ts-calc-range в DOM нет.
#   2. Каталог: карточки 50М/100М (0,00428) — «НСХ: −180…200 °C»,
#      карточки α = 0,00426 — прежние «−50…200 °C».
#   3. Живой расчёт по ГОСТ 5.2.3: −180 → 10,2642; −50 → 39,2275;
#      −190 — вне НСХ (тост, поле пусто); инверсия 39,2275 → ≈−50.
#   4. 100П: «−200…850 °C» / «17,2444…395,16 Ом»; t=−100 → 59,6393
#      (инвариант Task 498 — формула А.2 жива).
#   5. ТХА (K): «−270…1372 °C» / «−6,4577…54,8864 мВ».
#   6. СВЕТЛАЯ тема: плейсхолдер бледный тёмный (не белый).
#   7. ДЕСКТОП 1280: заголовок 21px + крошки (инвариант 498) +
#      плейсхолдер 100М (0,00426) «78,7…185,2 Ом».
# + 0 JS-ошибок; скриншоты в download/kip8test-task499/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8987
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task499')
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
                      body='not found (browser-check t499)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Состояние полей ППР: плейсхолдеры + бледность + отсутствие div-подсказок
FIELDS_JS = r"""(() => {
    const t = document.getElementById('tempQueryTemp');
    const v = document.getElementById('tempQueryVal');
    const title = document.getElementById('tempSensorViewTitle');
    const phT = t ? getComputedStyle(t, '::placeholder') : null;
    const phV = v ? getComputedStyle(v, '::placeholder') : null;
    return {
        title: title ? title.textContent : null,
        fs: title ? getComputedStyle(title).fontSize : null,
        phT: t ? t.placeholder : null,
        phV: v ? v.placeholder : null,
        phTColor: phT ? phT.color : null,
        phVColor: phV ? phV.color : null,
        phTWeight: phT ? phT.fontWeight : null,
        divRanges: document.querySelectorAll('.ts-calc-range').length,
        valLabel: (document.getElementById('tempQueryValLabel') || {}).textContent
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t499-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(600)

        # каталог: диапазоны на карточках (0,00428 → −180…200; 1426 → −50…200)
        ranges = page.evaluate(
            "(() => { return Array.from(document.querySelectorAll('.ts-card-range'))"
            ".map(c => c.textContent); })()")
        check('0a: каталог: есть карточка «НСХ: −180…200 °C» (0,00428)',
              any(r == 'НСХ: −180…200 °C' for r in ranges), ranges[:6])
        check('0b: каталог: есть карточка «НСХ: −50…200 °C» (0,00426)',
              any(r == 'НСХ: −50…200 °C' for r in ranges), ranges[:6])

        open_sensor(page, 'cu50_1428')
        check('A: страница датчика активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensor-view').classList.contains('active')"))
        st = page.evaluate(FIELDS_JS)
        check('B: заголовок жив (инвариант 498): «50М (Cu50) α = 0,00428 °C⁻¹»',
              st['title'] == '50М (Cu50) α = 0,00428 °C⁻¹', st['title'])
        fs_px = float(str(st['fs']).replace('px', '')) if st['fs'] else 0
        check('C: шрифт заголовка ≥ 15px (после фиттера)',
              fs_px >= 15, st['fs'])
        check('D: плейсхолдер температуры = «−180…200 °C» (НЕ «Например: 55»)',
              st['phT'] == '−180…200 °C', st['phT'])
        check('E: плейсхолдер значения = «10,2642…92,8 Ом» (НЕ «Например: 61,8»)',
              st['phV'] == '10,2642…92,8 Ом', st['phV'])
        check('F: плейсхолдеры бледные (rgba 0.4, тёмная тема)',
              st['phTColor'] == 'rgba(255, 255, 255, 0.4)' and
              st['phVColor'] == 'rgba(255, 255, 255, 0.4)',
              (st['phTColor'], st['phVColor']))
        check('G: div-подсказок .ts-calc-range в DOM нет',
              st['divRanges'] == 0, st['divRanges'])
        shot(page, 'a-mobile-dark-50m.png')

        # живой расчёт по ГОСТ 5.2.3
        page.fill('#tempQueryTemp', '-180')
        page.wait_for_timeout(400)
        v = page.evaluate("document.getElementById('tempQueryVal').value")
        check('H: живой расчёт: 50М t=−180 → 10,2642 Ом (ГОСТ 5.2.3/А.3)',
              v == '10,2642', v)
        page.fill('#tempQueryTemp', '-50')
        page.wait_for_timeout(400)
        v = page.evaluate("document.getElementById('tempQueryVal').value")
        check('I: живой расчёт: 50М t=−50 → 39,2275 Ом (ГОСТ, не 39,3)',
              v == '39,2275', v)
        # инверсия: 39,2275 → −50
        page.fill('#tempQueryVal', '39,2275')
        page.wait_for_timeout(400)
        t = page.evaluate("document.getElementById('tempQueryTemp').value")
        tnum = float(t.replace(',', '.')) if t else None
        check('J: инверсия: 39,2275 Ом → ≈ −50 °C',
              tnum is not None and abs(tnum + 50) < 0.05, t)
        # вне диапазона: −190
        toast = ''
        page.evaluate("window.__t499toast = ''; const old = window.showToast;"
                      "window.showToast = function(m){ window.__t499toast = String(m);"
                      " if(old) old(m); };")
        page.fill('#tempQueryTemp', '-190')
        page.wait_for_timeout(400)
        toast = page.evaluate("window.__t499toast")
        v = page.evaluate("document.getElementById('tempQueryVal').value")
        check('K: t=−190 — вне НСХ: тост с «-180» + поле очищено',
              ('-180' in toast and v == ''), (toast, v))
        shot(page, 'b-mobile-dark-50m-calc.png')

        # ---- 100П: инвариант формулы А.2 (Task 498) + плейсхолдеры ----
        open_sensor(page, 'pt100_1391')
        st2 = page.evaluate(FIELDS_JS)
        check('L: 100П плейсхолдеры «−200…850 °C» / «17,2444…395,16 Ом»',
              st2['phT'] == '−200…850 °C' and st2['phV'] == '17,2444…395,16 Ом',
              (st2['phT'], st2['phV']))
        page.fill('#tempQueryTemp', '-100')
        page.wait_for_timeout(400)
        v = page.evaluate("document.getElementById('tempQueryVal').value")
        check('M: 100П t=−100 → 59,6393 Ом (А.2 ГОСТ, инвариант 498)',
              v == '59,6393', v)
        shot(page, 'c-mobile-dark-100p.png')

        # ---- ТХА (K): мВ ----
        open_sensor(page, 'tc_K')
        st3 = page.evaluate(FIELDS_JS)
        check('N: ТХА (K): «−270…1372 °C» / «−6,4577…54,8864 мВ»',
              st3['phT'] == '−270…1372 °C' and st3['phV'] == '−6,4577…54,8864 мВ',
              (st3['phT'], st3['phV']))
        check('O: подпись поля значения для ТП — Термо-ЭДС',
              st3['valLabel'] == 'Термо-ЭДС E(t), мВ', st3['valLabel'])
        shot(page, 'd-mobile-dark-tc-k.png')
        ctx.close()

        # ============ 2. СВЕТЛАЯ тема, 50М ============
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t499-b');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu50_1428')
        st4 = page.evaluate(FIELDS_JS)
        check('P: светлая: плейсхолдеры на месте (−180…200 °C)',
              st4['phT'] == '−180…200 °C', st4['phT'])
        check('Q: светлая: плейсхолдер бледный ТЁМНЫЙ (не белый)',
              st4['phTColor'] is not None and
              st4['phTColor'].startswith('rgba(20, 20, 19') and
              '255' not in st4['phTColor'],
              st4['phTColor'])
        shot(page, 'e-light-50m.png')
        ctx.close()

        # ============ 3. ДЕСКТОП 1280: инварианты 498 + плейсхолдер ============
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t499-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu100_1426')
        st5 = page.evaluate(FIELDS_JS)
        check('R: десктоп: заголовок 21px (базовый, без фиттера)',
              st5['fs'] == '21px', st5['fs'])
        check('S: десктоп: крошки заканчиваются на «100М (Cu100) α = 0,00426 °C⁻¹»',
              st5['title'] is not None and
              st5['title'].endswith('100М (Cu100) α = 0,00426 °C⁻¹'), st5['title'])
        check('T: десктоп: плейсхолдер 100М (0,00426) — «78,7…185,2 Ом»',
              st5['phV'] == '78,7…185,2 Ом', st5['phV'])
        check('U: десктоп: плейсхолдер температуры 1426 — «−50…200 °C»',
              st5['phT'] == '−50…200 °C', st5['phT'])
        shot(page, 'f-desktop-1280-cu100.png')
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
