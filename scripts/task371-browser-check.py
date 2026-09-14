#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 371: browser-check — заявка пользователя:
#   «На странице Главная / Инженерные калькуляторы / КИП и А /
#    Датчики температуры, под блоком Таблица значений добавь блок
#    Расчёт произвольных значений, по примеру как в разделе
#    Шкала-сигнал.»
# Проверка:
#   1. десктоп 1280 тёмная: «Рассчитать» (ТС Cu50 по умолчанию) →
#      таблица значений + ПОД НЕЙ блок «Расчёт произвольных значений»;
#      живой двусторонний расчёт: 55 → 61,77 Ом; 92,8 → 200 °C;
#      Pt100: −50 → 80,3063; 138,5 → ≈100; ТП K: 400 → 16,3971 мВ,
#      −3,5531 → ≈−100; ТП B: 1000 → 4,8343 мВ; вне НСХ → тост
#      «вне диапазона НСХ» + очистка парного поля.
#   2. светлая тема: блок и поля читаемы, расчёт работает.
#   3. мобайл 375: панель не переполняется, расчёт работает.
# + 0 JS-ошибок; скриншот-пруфы.
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8972

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

def set_select(page, sel_id, value):
    # Нативные select скрыты кастомными дропдаунами приложения
    # (initCustomSelects) — Playwright select_option не проходит
    # actionability-чек. Устанавливаем value напрямую (перехваченный
    # сеттер синхронизирует кастомный UI) + событие change для логики.
    page.evaluate("""([id, val]) => {
        var s = document.getElementById(id);
        s.value = val;
        s.dispatchEvent(new Event('change', {bubbles: true}));
    }""", [sel_id, value])
    page.wait_for_timeout(250)

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t371)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t371-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(800)
    check('B: страница «Датчики температуры» активна',
          page.evaluate("document.getElementById('page-temp-sensors').classList.contains('active')"))

    # --- «Рассчитать» с дефолтной формой (ТС Cu50, 0..100, шаг 10) ---
    page.click('#page-temp-sensors .converter-convert-btn')
    page.wait_for_timeout(600)
    check('C: таблица значений отрисована',
          page.evaluate("document.getElementById('tempTableContainer') !== null"))
    check('D: под таблицей — блок «Расчёт произвольных значений»',
          page.evaluate("""(function(){
            var r = document.getElementById('tempSensorResults');
            var h = r ? r.innerHTML : '';
            var iTbl = h.indexOf('id="tempTableContainer"');
            var iPan = h.indexOf('id="tempCustomCalcPanel"');
            return iPan !== -1 && iTbl !== -1 && iTbl < iPan && h.indexOf('Расчёт произвольных значений') !== -1;
          })()"""))
    check('E: подписи полей ТС — «Температура (°C)» / «Сопротивление R(t), Ом»',
          page.evaluate("""(function(){
            var pan = document.getElementById('tempCustomCalcPanel');
            return pan && pan.textContent.indexOf('Температура (°C)') !== -1
                        && pan.textContent.indexOf('Сопротивление R(t), Ом') !== -1;
          })()"""))
    check('F: панель видима (высота > 0)',
          page.evaluate("document.getElementById('tempCustomCalcPanel').offsetHeight > 0"))

    # --- живой расчёт Cu50: t → R ---
    page.fill('#tempQueryTemp', '55')
    page.wait_for_timeout(150)
    check('G: Cu50 t=55 → R=61,77 Ом',
          page.evaluate("document.getElementById('tempQueryVal').value") == '61,77',
          page.evaluate("document.getElementById('tempQueryVal').value"))
    # --- живой расчёт Cu50: R → t ---
    page.fill('#tempQueryVal', '92,8')
    page.wait_for_timeout(150)
    check('H: Cu50 R=92,8 → t=200 °C (граница НСХ)',
          page.evaluate("document.getElementById('tempQueryTemp').value") == '200',
          page.evaluate("document.getElementById('tempQueryTemp').value"))
    # --- вне НСХ: t=250 для Cu ---
    page.fill('#tempQueryTemp', '250')
    page.wait_for_timeout(300)
    check('I: Cu50 t=250 вне НСХ → поле R очищено + тост',
          page.evaluate("document.getElementById('tempQueryVal').value") == '' and
          page.evaluate("""(function(){
            var t = document.getElementById('toast');
            var m = document.getElementById('toastMessage');
            return t && m && t.classList.contains('show') &&
                   m.textContent.indexOf('вне диапазона НСХ') !== -1 &&
                   m.textContent.indexOf('-50') !== -1;
          })()"""))
    page.wait_for_timeout(2500)  # ждём скрытия тоста

    # --- Pt100 (IEC): смена типа ТС + повторный «Рассчитать» ---
    set_select(page, 'temp_rtd_type', 'pt100_1385')
    page.click('#page-temp-sensors .converter-convert-btn')
    page.wait_for_timeout(600)
    page.fill('#tempQueryTemp', '-50')
    page.wait_for_timeout(150)
    check('J: Pt100 t=−50 → R=80,3063 Ом (член C ниже 0°C)',
          page.evaluate("document.getElementById('tempQueryVal').value") == '80,3063',
          page.evaluate("document.getElementById('tempQueryVal').value"))
    page.fill('#tempQueryVal', '138,5')
    page.wait_for_timeout(150)
    t_val = parse_ru(page.evaluate("document.getElementById('tempQueryTemp').value"))
    check('K: Pt100 R=138,5 → t≈100 °C',
          t_val is not None and abs(t_val - 100) < 0.05, t_val)

    # --- ТП (K): смена типа датчика ---
    set_select(page, 'temp_sensor_type', 'tc')
    page.click('#page-temp-sensors .converter-convert-btn')
    page.wait_for_timeout(600)
    check('L: подпись поля ТП — «Термо-ЭДС E(t), мВ»',
          page.evaluate("""(function(){
            var pan = document.getElementById('tempCustomCalcPanel');
            return pan && pan.textContent.indexOf('Термо-ЭДС E(t), мВ') !== -1;
          })()"""))
    page.fill('#tempQueryTemp', '400')
    page.wait_for_timeout(150)
    check('M: ТХА(K) t=400 → E=16,3971 мВ',
          page.evaluate("document.getElementById('tempQueryVal').value") == '16,3971',
          page.evaluate("document.getElementById('tempQueryVal').value"))
    page.fill('#tempQueryVal', '-3,5531')
    page.wait_for_timeout(150)
    t_val = parse_ru(page.evaluate("document.getElementById('tempQueryTemp').value"))
    check('N: ТХА(K) E=−3,5531 → t≈−100 °C',
          t_val is not None and abs(t_val + 100) < 0.02, t_val)

    # --- ТП (B): верхний диапазон ---
    set_select(page, 'temp_tc_type', 'B')
    page.click('#page-temp-sensors .converter-convert-btn')
    page.wait_for_timeout(600)
    page.fill('#tempQueryTemp', '1000')
    page.wait_for_timeout(150)
    check('O: ТПР(B) t=1000 → E=4,8343 мВ',
          page.evaluate("document.getElementById('tempQueryVal').value") == '4,8343',
          page.evaluate("document.getElementById('tempQueryVal').value"))

    # --- вне НСХ для ТП: t=1373 (макс K=1372; для B тоже вне) ---
    page.fill('#tempQueryTemp', '1821')
    page.wait_for_timeout(300)
    check('P: ТП(B) t=1821 вне НСХ → очистка + тост',
          page.evaluate("document.getElementById('tempQueryVal').value") == '' and
          page.evaluate("""(function(){
            var t = document.getElementById('toast');
            var m = document.getElementById('toastMessage');
            return t && m && t.classList.contains('show') &&
                   m.textContent.indexOf('Значение') === -1 &&
                   m.textContent.indexOf('Температура вне диапазона НСХ') !== -1;
          })()"""))
    page.wait_for_timeout(2500)

    # --- скриншот-пруф десктоп: K, t=400 → 16,3971 ---
    set_select(page, 'temp_tc_type', 'K')
    page.click('#page-temp-sensors .converter-convert-btn')
    page.wait_for_timeout(600)
    page.fill('#tempQueryTemp', '400')
    page.wait_for_timeout(300)
    page.evaluate("document.getElementById('tempCustomCalcPanel').scrollIntoView({block:'center'})")
    page.wait_for_timeout(400)
    page.screenshot(path='scripts/task371-proof-desktop.png')
    check('Q: десктоп-пруф снят (панель в кадре)', True)

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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t371-b');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('temp-sensors')")
    page2.wait_for_timeout(800)
    page2.click('#page-temp-sensors .converter-convert-btn')
    page2.wait_for_timeout(600)
    page2.fill('#tempQueryTemp', '55')
    page2.wait_for_timeout(150)
    check('R: светлая — Cu50 t=55 → 61,77 Ом',
          page2.evaluate("document.getElementById('tempQueryVal').value") == '61,77',
          page2.evaluate("document.getElementById('tempQueryVal').value"))
    lbl = page2.evaluate("""(function(){
        var pan = document.getElementById('tempCustomCalcPanel');
        var title = pan.querySelector('.converter-result-label-title');
        return title ? getComputedStyle(title).color : null;
    })()""")
    check('S: светлая — заголовок блока тёмный (не белый)',
          lbl is not None and lbl not in ('rgb(255, 255, 255)', 'rgba(255, 255, 255, 1)'), lbl)
    page2.evaluate("document.getElementById('tempCustomCalcPanel').scrollIntoView({block:'center'})")
    page2.wait_for_timeout(400)
    page2.screenshot(path='scripts/task371-proof-light.png')
    check('T: светлый пруф снят', True)
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t371-c');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('temp-sensors')")
    page3.wait_for_timeout(800)
    page3.click('#page-temp-sensors .converter-convert-btn')
    page3.wait_for_timeout(600)
    page3.fill('#tempQueryTemp', '55')
    page3.wait_for_timeout(150)
    check('U: мобайл — Cu50 t=55 → 61,77 Ом',
          page3.evaluate("document.getElementById('tempQueryVal').value") == '61,77',
          page3.evaluate("document.getElementById('tempQueryVal').value"))
    no_overflow = page3.evaluate("""(function(){
        var pan = document.getElementById('tempCustomCalcPanel');
        return pan && pan.scrollWidth <= window.innerWidth + 1;
    })()""")
    check('V: мобайл — панель не переполняет ширину', no_overflow)
    page3.evaluate("document.getElementById('tempCustomCalcPanel').scrollIntoView({block:'center'})")
    page3.wait_for_timeout(400)
    page3.screenshot(path='scripts/task371-proof-mobile.png')
    check('W: мобайл-пруф снят', True)
    ctx3.close()

    all_errors = js_errors + js_errors2 + js_errors3
    check('X: 0 JS-ошибок во всех контекстах', len(all_errors) == 0, all_errors[:5])

    browser.close()

print('\n════════ Итог Task 371 browser-check: %d ✓ / %d ✗ ════════' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
