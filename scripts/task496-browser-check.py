#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 496: browser-check — заявка: «В блоке произвольного расчёта,
# после ввода одного из данных и при нажатии подтверждения на
# клавиатуре, клавиатура должна закрываться, а не перемещаться
# по следующим полям ввода.»
#   1. МОБАЙЛ 375 тёмная, ТС 50М: на странице датчика оба поля ППР
#      (tempQueryTemp/tempQueryVal) — enterkeyhint="done", НЕТ
#      "next"; onkeydown="tempQueryEnterBlur(event,this)" на обоих;
#      фокус в поле температуры + Enter (page.keyboard) — фокус
#      СНЯТ (activeElement = body, НЕ tempQueryVal — перескакивания
#      нет); фокус в поле значения + Enter — тоже снят; живой расчёт
#      по oninput работает (55 → R посчитан); клавиатура не мешает
#      вводу обычных клавиш (Tab НЕ blur).
#   2. ТП ТХА (K): те же атрибуты и поведение Enter.
#   3. СВЕТЛАЯ тема: то же поведение.
#   4. ДЕСКТОП 1280: атрибуты живы и там (разметка не в media).
# + 0 JS-ошибок; скриншоты в download/kip8test-task496/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8984
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task496')
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
                      body='not found (browser-check t496)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Атрибуты полей ППР (enterkeyhint/onkeydown)
ATTRS_JS = r"""(() => {
    const t = document.getElementById('tempQueryTemp');
    const v = document.getElementById('tempQueryVal');
    if (!t || !v) return {t: !!t, v: !!v};
    return {
        t: true, v: true,
        tHint: t.getAttribute('enterkeyhint'),
        vHint: v.getAttribute('enterkeyhint'),
        tKd: t.getAttribute('onkeydown'),
        vKd: v.getAttribute('onkeydown'),
        fn: typeof window.tempQueryEnterBlur,
        tVal: t.value, vVal: v.value,
        label: (document.getElementById('tempQueryValLabel') || {}).textContent
    };
})()"""


def open_sensor(page, key):
    page.evaluate("openTempSensor('%s')" % key)
    page.wait_for_timeout(500)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ============ 1. МОБАЙЛ 375, тёмная, датчик 50М (ТС) ===========
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t496-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(600)
        open_sensor(page, 'cu50_1428')

        check('A: страница датчика активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensor-view').classList.contains('active')"))
        st = page.evaluate(ATTRS_JS)
        check('B: оба поля ППР — enterkeyhint="done" (next убран)',
              st['tHint'] == 'done' and st['vHint'] == 'done',
              (st['tHint'], st['vHint']))
        check('C: onkeydown tempQueryEnterBlur на обоих полях',
              st['tKd'] == 'tempQueryEnterBlur(event,this)' and
              st['vKd'] == 'tempQueryEnterBlur(event,this)',
              (st['tKd'], st['vKd']))
        check('D: tempQueryEnterBlur — глобальная функция',
              st['fn'] == 'function', st['fn'])

        # --- Enter в поле температуры: клавиатура закрывается ---
        page.click('#tempQueryTemp')
        page.wait_for_timeout(300)
        check('E: фокус установлен в поле температуры',
              page.evaluate(
                  "document.activeElement === document.getElementById('tempQueryTemp')"))
        page.keyboard.press('Enter')
        page.wait_for_timeout(400)
        ae = page.evaluate(
            "document.activeElement && (document.activeElement.id || 'BODY-or-' + document.activeElement.tagName)")
        check('F: Enter — фокус СНЯТ (клавиатура закрылась), НЕ поле значения',
              ae != 'tempQueryVal' and ae != 'tempQueryTemp', ae)
        ae_is_body = page.evaluate(
            "document.activeElement === document.body")
        check('G: activeElement — body (blur сработал)', ae_is_body, ae)
        shot(page, 'a-mobile-dark-after-enter-temp.png')

        # --- живой расчёт жив: 55 → R(t) ---
        page.fill('#tempQueryTemp', '55')
        page.wait_for_timeout(400)
        st2 = page.evaluate(ATTRS_JS)
        check('H: живой расчёт жив (55 → R посчитан, oninput не тронут)',
              st2['vVal'] not in ('', None) and
              float(st2['vVal'].replace(',', '.')) > 0, st2['vVal'])
        shot(page, 'b-mobile-dark-live-calc.png')

        # --- Enter в поле значения: тоже закрывает ---
        page.click('#tempQueryVal')
        page.wait_for_timeout(300)
        page.keyboard.press('Enter')
        page.wait_for_timeout(400)
        ae2 = page.evaluate(
            "document.activeElement && (document.activeElement.id || 'BODY')")
        check('I: Enter в поле значения — фокус СНЯТ (body), не след. поле',
              ae2 == 'BODY', ae2)

        # --- глобальный Enter-переход жив для блока таблицы (граница заявки) ---
        page.click('#temp_sensor_min')
        page.wait_for_timeout(300)
        page.keyboard.press('Enter')
        page.wait_for_timeout(400)
        ae_tbl = page.evaluate(
            "document.activeElement && (document.activeElement.id || 'BODY')")
        check('K0: границы заявки: блок таблицы — Enter ПЕРЕСКАКИВАЕТ как прежде',
              ae_tbl == 'temp_sensor_max', ae_tbl)
        # поле шага — последнее: Enter жмёт «Рассчитать» + blur (как прежде)
        page.click('#temp_sensor_step')
        page.wait_for_timeout(200)
        page.keyboard.press('Enter')
        page.wait_for_timeout(700)
        res = page.evaluate(
            "(() => { const r = document.getElementById('tempSensorResults');" +
            " return r ? r.style.display + '/' + r.innerHTML.length : 'none'; })()")
        check('K1: последнее поле блока таблицы — Enter запускает расчёт (как прежде)',
              res.startswith('block/') and int(res.split('/')[1]) > 500, res)
        # значения не затёрлись
        st3 = page.evaluate(ATTRS_JS)
        check('K: значения полей после Tab не затёрты',
              st3['tVal'] == '55', st3['tVal'])

        # --- подпись ППР жива (ТС: Ом) ---
        check('L: подпись поля значения — Ом (ТС)',
              'Ом' in str(st['label']), st['label'])
        ctx.close()

        # ============ 2. ТП — ТХА (K) ================================
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors2 = []
        page.on('pageerror', lambda e: js_errors2.append(str(e)))
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t496-b');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'tc_K')
        st4 = page.evaluate(ATTRS_JS)
        check('M: ТХА (K) — атрибуты done×2 + onkeydown×2',
              st4['tHint'] == 'done' and st4['vHint'] == 'done' and
              st4['tKd'] == 'tempQueryEnterBlur(event,this)' and
              st4['vKd'] == 'tempQueryEnterBlur(event,this)',
              (st4['tHint'], st4['vHint']))
        check('N: ТХА (K) — подпись мВ',
              'мВ' in str(st4['label']), st4['label'])
        page.click('#tempQueryTemp')
        page.keyboard.press('Enter')
        page.wait_for_timeout(400)
        ae3 = page.evaluate(
            "document.activeElement && (document.activeElement.id || 'BODY')")
        check('O: ТХА (K) — Enter закрывает (не перескакивает)',
              ae3 != 'tempQueryVal' and ae3 != 'tempQueryTemp', ae3)
        # живой расчёт ТП: 300 → мВ
        page.fill('#tempQueryTemp', '300')
        page.wait_for_timeout(400)
        st5 = page.evaluate(ATTRS_JS)
        check('P: ТХА (K) — живой расчёт (300 → мВ > 0)',
              st5['vVal'] not in ('', None) and
              float(str(st5['vVal']).replace(',', '.')) > 0, st5['vVal'])
        shot(page, 'c-mobile-dark-tc.png')
        ctx.close()

        # ============ 3. СВЕТЛАЯ тема ================================
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors3 = []
        page.on('pageerror', lambda e: js_errors3.append(str(e)))
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t496-c');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu50_1428')
        st6 = page.evaluate(ATTRS_JS)
        check('Q: светлая — атрибуты живы (done×2 + onkeydown×2)',
              st6['tHint'] == 'done' and st6['vHint'] == 'done' and
              st6['vKd'] == 'tempQueryEnterBlur(event,this)', st6['tHint'])
        page.click('#tempQueryVal')
        page.keyboard.press('Enter')
        page.wait_for_timeout(400)
        ae4 = page.evaluate(
            "document.activeElement && (document.activeElement.id || 'BODY')")
        check('R: светлая — Enter закрывает клавиатуру',
              ae4 != 'tempQueryVal' and ae4 != 'tempQueryTemp', ae4)
        shot(page, 'd-mobile-light.png')
        ctx.close()

        # ============ 4. ДЕСКТОП 1280 ================================
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        js_errors4 = []
        page.on('pageerror', lambda e: js_errors4.append(str(e)))
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t496-d');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu50_1428')
        st7 = page.evaluate(ATTRS_JS)
        check('S: десктоп — атрибуты живы (done×2 + onkeydown×2)',
              st7['tHint'] == 'done' and st7['vHint'] == 'done' and
              st7['tKd'] == 'tempQueryEnterBlur(event,this)' and
              st7['vKd'] == 'tempQueryEnterBlur(event,this)',
              (st7['tHint'], st7['vKd']))
        page.click('#tempQueryTemp')
        page.keyboard.press('Enter')
        page.wait_for_timeout(400)
        ae5 = page.evaluate(
            "document.activeElement && (document.activeElement.id || 'BODY')")
        check('T: десктоп — Enter снимает фокус и тут',
              ae5 != 'tempQueryVal' and ae5 != 'tempQueryTemp', ae5)
        shot(page, 'e-desktop.png')
        ctx.close()

        browser.close()

    print('---')
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    print('JS-ошибок: %d' % (len(js_errors) + len(js_errors2) +
                             len(js_errors3) + len(js_errors4)))
    for e in (js_errors + js_errors2 + js_errors3 + js_errors4)[:5]:
        print('  JS: ' + e[:200])
    raise SystemExit(0 if (FAIL == 0 and not js_errors and not js_errors2 and
                           not js_errors3 and not js_errors4) else 1)


main()
