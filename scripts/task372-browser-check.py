#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 372: browser-check — переделка раздела «Датчики температуры»:
#   1. десктоп 1280 тёмная: страница выбора = КАРТОЧКИ (8 ТС + 8 ТП,
#      группы «Термометры сопротивления»/«Термопары»); клик карточки
#      50М (Cu50) → страница датчика (диапазон/шаг/чип/справка БЕЗ
#      информации о термопарах); «Рассчитать» → таблица + панель
#      «Расчёт произвольных значений» (Task 371) под ней; живой
#      двусторонний расчёт; вне НСХ → тост; клик ТХА (K) → справка
#      БЕЗ информации о термометрах, подпись «Термо-ЭДС E(t), мВ»;
#      ТПР (B) → 1000 → 4,8343 мВ; смена датчика сбрасывает
#      результаты; прямой hash без выбора → редирект на список.
#   2. светлая тема: карточки и страница датчика читаемы, расчёт жив.
#   3. мобайл 375: карточки в 2 колонки без переполнения, расчёт жив.
# + 0 JS-ошибок; скриншот-пруфы.
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8973

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'flowmeter.view': True, 'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def parse_ru(s):
    s = str(s).replace('\u00a0', '').replace(',', '.')
    try: return float(s)
    except Exception: return None

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t372)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t372-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    # --- страница выбора = карточки ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(800)
    check('B: страница «Датчики температуры» активна',
          page.evaluate("document.getElementById('page-temp-sensors').classList.contains('active')"))
    check('C: карточек ТС = 8',
          page.evaluate("document.querySelectorAll('#tsRtdCards .ts-card').length") == 8,
          page.evaluate("document.querySelectorAll('#tsRtdCards .ts-card').length"))
    check('D: карточек ТП = 8',
          page.evaluate("document.querySelectorAll('#tsTcCards .ts-card').length") == 8,
          page.evaluate("document.querySelectorAll('#tsTcCards .ts-card').length"))
    check('E: группы «Термометры сопротивления» и «Термопары»',
          page.evaluate("""(function(){
            var t = document.querySelector('#page-temp-sensors .ts-page').textContent;
            return t.indexOf('Термометры сопротивления') !== -1 && t.indexOf('Термопары') !== -1
                && t.indexOf('ГОСТ 6651-2009') !== -1 && t.indexOf('ГОСТ Р 8.585-2001') !== -1;
          })()"""))
    check('F: на странице выбора НЕТ кнопки «Рассчитать» (это список карточек)',
          page.evaluate("document.querySelector('#page-temp-sensors .converter-convert-btn') === null"))

    # --- клик карточки 50М (Cu50) → страница датчика ---
    page.click("#tsRtdCards .ts-card:first-child")
    page.wait_for_timeout(600)
    check('G: перешли на страницу датчика',
          page.evaluate("document.getElementById('page-temp-sensor-view').classList.contains('active')"))
    check('H: заголовок-крошки заканчиваются именем «50М (Cu50)»',
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent").strip().endswith('50М (Cu50)'),
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent"))
    check('I: чип датчика (имя + R₀)',
          page.evaluate("""(function(){
            var c = document.getElementById('tempSensorViewChip').textContent;
            return c.indexOf('50М (Cu50)') !== -1 && c.indexOf('R₀ = 50 Ом') !== -1;
          })()"""))
    check('J: дефолты формы 0 / 100 / 10',
          page.evaluate("document.getElementById('temp_sensor_min').value") == '0' and
          page.evaluate("document.getElementById('temp_sensor_max').value") == '100' and
          page.evaluate("document.getElementById('temp_sensor_step').value") == '10')
    check('K: справка ТС БЕЗ информации о термопарах',
          page.evaluate("""(function(){
            var h = document.getElementById('tempSensorInfoBody').textContent;
            return h.indexOf('Термопреобразователь сопротивления') !== -1
                && h.indexOf('ГОСТ 6651-2009') !== -1
                && h.indexOf('Термопара') === -1
                && h.indexOf('ГОСТ Р 8.585-2001') === -1
                && h.indexOf('термо-ЭДС') === -1;
          })()"""))

    # --- «Рассчитать» (Cu50, 0..100, шаг 10) ---
    page.click('#page-temp-sensor-view .converter-convert-btn')
    page.wait_for_timeout(600)
    check('L: таблица значений отрисована (R(50)=60,7)',
          page.evaluate("""(function(){
            var t = document.getElementById('tempTableContainer');
            return t !== null && t.textContent.indexOf('60,7') !== -1;
          })()"""))
    check('M: под таблицей — блок «Расчёт произвольных значений» (Task 371 жив)',
          page.evaluate("""(function(){
            var r = document.getElementById('tempSensorResults');
            var h = r ? r.innerHTML : '';
            var iTbl = h.indexOf('id="tempTableContainer"');
            var iPan = h.indexOf('id="tempCustomCalcPanel"');
            return iPan !== -1 && iTbl !== -1 && iTbl < iPan &&
                   h.indexOf('Сопротивление R(t), Ом') !== -1;
          })()"""))

    # --- живой расчёт Cu50 ---
    page.fill('#tempQueryTemp', '55')
    page.wait_for_timeout(150)
    check('N: Cu50 t=55 → R=61,77 Ом',
          page.evaluate("document.getElementById('tempQueryVal').value") == '61,77',
          page.evaluate("document.getElementById('tempQueryVal').value"))
    page.fill('#tempQueryVal', '92,8')
    page.wait_for_timeout(150)
    check('O: Cu50 R=92,8 → t=200 °C (граница НСХ)',
          page.evaluate("document.getElementById('tempQueryTemp').value") == '200',
          page.evaluate("document.getElementById('tempQueryTemp').value"))
    page.fill('#tempQueryTemp', '250')
    page.wait_for_timeout(300)
    check('P: Cu50 t=250 вне НСХ → очистка + тост',
          page.evaluate("document.getElementById('tempQueryVal').value") == '' and
          page.evaluate("""(function(){
            var t = document.getElementById('toast');
            var m = document.getElementById('toastMessage');
            return t && m && t.classList.contains('show') &&
                   m.textContent.indexOf('вне диапазона НСХ') !== -1;
          })()"""))
    page.wait_for_timeout(2500)

    # --- клик карточки ТХА (K) → справка БЕЗ информации о термометрах ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(600)
    page.click("#tsTcCards .ts-card:first-child")
    page.wait_for_timeout(600)
    check('Q: заголовок-крошки заканчиваются «ТХА (K)»',
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent").strip().endswith('ТХА (K)'),
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent"))
    check('R: справка ТП БЕЗ информации о термометрах',
          page.evaluate("""(function(){
            var h = document.getElementById('tempSensorInfoBody').textContent;
            return h.indexOf('термо-ЭДС') !== -1 && h.indexOf('ГОСТ Р 8.585-2001') !== -1
                && h.indexOf('Термопреобразователь') === -1
                && h.indexOf('ГОСТ 6651-2009') === -1
                && h.indexOf('IEC 60751') === -1
                && h.indexOf('хромель-алюмель') !== -1;
          })()"""))
    check('S: смена датчика сбросила результаты прошлой страницы',
          page.evaluate("""(function(){
            var r = document.getElementById('tempSensorResults');
            return r.style.display === 'none' && r.innerHTML === '';
          })()"""))

    page.click('#page-temp-sensor-view .converter-convert-btn')
    page.wait_for_timeout(600)
    check('T: подпись поля ТП — «Термо-ЭДС E(t), мВ»',
          page.evaluate("""(function(){
            var pan = document.getElementById('tempCustomCalcPanel');
            return pan && pan.textContent.indexOf('Термо-ЭДС E(t), мВ') !== -1
                        && pan.textContent.indexOf('Сопротивление') === -1;
          })()"""))
    page.fill('#tempQueryTemp', '400')
    page.wait_for_timeout(150)
    check('U: ТХА(K) t=400 → E=16,3971 мВ',
          page.evaluate("document.getElementById('tempQueryVal').value") == '16,3971',
          page.evaluate("document.getElementById('tempQueryVal').value"))
    page.fill('#tempQueryVal', '-3,5531')
    page.wait_for_timeout(150)
    t_val = parse_ru(page.evaluate("document.getElementById('tempQueryTemp').value"))
    check('V: ТХА(K) E=−3,5531 → t≈−100 °C',
          t_val is not None and abs(t_val + 100) < 0.02, t_val)

    # --- ТПР (B): карточка №8 в группе ТП ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(600)
    page.click("#tsTcCards .ts-card:nth-child(8)")
    page.wait_for_timeout(600)
    check('W: выбрана ТПР (B) — крошки заканчиваются именем',
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent").strip().endswith('ТПР (B)'),
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent"))
    page.click('#page-temp-sensor-view .converter-convert-btn')
    page.wait_for_timeout(600)
    page.fill('#tempQueryTemp', '1000')
    page.wait_for_timeout(150)
    check('X: ТПР(B) t=1000 → E=4,8343 мВ',
          page.evaluate("document.getElementById('tempQueryVal').value") == '4,8343',
          page.evaluate("document.getElementById('tempQueryVal').value"))
    page.fill('#tempQueryTemp', '1821')
    page.wait_for_timeout(300)
    check('Y: ТП(B) t=1821 вне НСХ → очистка + тост',
          page.evaluate("document.getElementById('tempQueryVal').value") == '' and
          page.evaluate("""(function(){
            var t = document.getElementById('toast');
            var m = document.getElementById('toastMessage');
            return t && m && t.classList.contains('show') &&
                   m.textContent.indexOf('Температура вне диапазона НСХ') !== -1;
          })()"""))
    page.wait_for_timeout(2500)

    # --- редирект: temp-sensor-view без выбранного датчика → список ---
    page.evaluate("tempSensorKey = null; navigateTo('temp-sensor-view')")
    page.wait_for_timeout(600)
    check('Z: hash temp-sensor-view без выбора → редирект на список карточек',
          page.evaluate("document.getElementById('page-temp-sensors').classList.contains('active')"))

    # --- десктоп-пруф: страница K с расчётом ---
    page.click("#tsTcCards .ts-card:first-child")
    page.wait_for_timeout(500)
    page.click('#page-temp-sensor-view .converter-convert-btn')
    page.wait_for_timeout(600)
    page.fill('#tempQueryTemp', '400')
    page.wait_for_timeout(300)
    page.evaluate("document.getElementById('tempCustomCalcPanel').scrollIntoView({block:'center'})")
    page.wait_for_timeout(400)
    page.screenshot(path='scripts/task372-proof-desktop.png')
    check('AA: десктоп-пруф снят', True)
    ctx.close()

    # ================= Контекст 2: светлая тема =================
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    def handle2(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx2.route('**/exec?**', handle2)
    ctx2.route('**script.google.com/**', handle2)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    ctx2.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t372-b');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('temp-sensors')")
    page2.wait_for_timeout(800)
    # светлая: карточки читаемы (имя тёмное, не белое)
    name_color = page2.evaluate("""(function(){
        var el = document.querySelector('#tsRtdCards .ts-card-name');
        return el ? getComputedStyle(el).color : null;
    })()""")
    check('AB: светлая — имя карточки тёмное (не белое)',
          name_color is not None and name_color not in ('rgb(255, 255, 255)', 'rgba(255, 255, 255, 1)'), name_color)
    page2.screenshot(path='scripts/task372-proof-light.png')
    check('AC: светлый пруф-карточки снят', True)
    # Pt100 (IEC): 7-я карточка ТС
    page2.click("#tsRtdCards .ts-card:nth-child(7)")
    page2.wait_for_timeout(600)
    page2.click('#page-temp-sensor-view .converter-convert-btn')
    page2.wait_for_timeout(600)
    page2.fill('#tempQueryTemp', '55')
    page2.wait_for_timeout(150)
    check('AD: светлая — Pt100 t=55 → 121,32 Ом',
          page2.evaluate("document.getElementById('tempQueryVal').value") == '121,32',
          page2.evaluate("document.getElementById('tempQueryVal').value"))
    ctx2.close()

    # ================= Контекст 3: мобайл 375 =================
    ctx3 = browser.new_context(viewport={'width': 375, 'height': 812})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    def handle3(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx3.route('**/exec?**', handle3)
    ctx3.route('**script.google.com/**', handle3)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)
    ctx3.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t372-c');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('temp-sensors')")
    page3.wait_for_timeout(800)
    no_overflow = page3.evaluate("""(function(){
        var grid = document.getElementById('tsRtdCards');
        return grid && grid.scrollWidth <= window.innerWidth + 1;
    })()""")
    check('AE: мобайл — сетка карточек не переполняет ширину', no_overflow)
    page3.screenshot(path='scripts/task372-proof-mobile.png')
    check('AF: мобайл-пруф карточек снят', True)
    page3.click("#tsTcCards .ts-card:first-child")
    page3.wait_for_timeout(600)
    check('AG0: мобайл — заголовок без крошек: «ТХА (K) — термопара»',
          page3.evaluate("document.getElementById('tempSensorViewTitle').textContent") == 'ТХА (K) — термопара',
          page3.evaluate("document.getElementById('tempSensorViewTitle').textContent"))
    page3.click('#page-temp-sensor-view .converter-convert-btn')
    page3.wait_for_timeout(600)
    page3.fill('#tempQueryTemp', '400')
    page3.wait_for_timeout(150)
    check('AG: мобайл — ТХА(K) t=400 → 16,3971 мВ',
          page3.evaluate("document.getElementById('tempQueryVal').value") == '16,3971',
          page3.evaluate("document.getElementById('tempQueryVal').value"))
    no_overflow2 = page3.evaluate("""(function(){
        var pan = document.getElementById('tempCustomCalcPanel');
        return pan && pan.scrollWidth <= window.innerWidth + 1;
    })()""")
    check('AH: мобайл — панель расчёта не переполняет ширину', no_overflow2)
    ctx3.close()

    all_errors = js_errors + js_errors2 + js_errors3
    check('AI: 0 JS-ошибок во всех контекстах', len(all_errors) == 0, all_errors[:5])

    browser.close()

print('\n════════ Итог Task 372 browser-check: %d ✓ / %d ✗ ════════' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
