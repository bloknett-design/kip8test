#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 374: browser-check — кнопка «Копировать» над таблицами значений
# в «Датчиках температуры» убрана:
#   1. десктоп 1280 тёмная: ТС (50М) → Рассчитать → таблица значений
#      есть, заголовок «Таблица значений (шаг X°C)» есть, кнопки
#      «Копировать» НЕТ, кнопок в результатах НЕТ вообще; значения
#      R(t) в таблице корректны.
#   2. ТП (ТХК L) → Рассчитать → то же для E(t).
#   3. Соседний раздел «Шкала-сигнал» — своя кнопка «Копировать»
#      ОСТАЛАСЬ (не тронута).
#   4. светлая тема: заголовок без кнопки читаем.
# + 0 JS-ошибок; скриншот-пруфы (desktop-tc/light).
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8975

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t374)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t374-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    # --- ТС (50М): расчёт → таблица без кнопки ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(800)
    check('B: страница «Датчики температуры» активна',
          page.evaluate("document.getElementById('page-temp-sensors').classList.contains('active')"))
    page.click("#tsRtdCards .ts-card:has-text('50М')")
    page.wait_for_timeout(600)
    check('C: страница датчика 50М открыта',
          page.evaluate("document.getElementById('page-temp-sensor-view').classList.contains('active')"))
    page.fill("#temp_sensor_min", "0")
    page.fill("#temp_sensor_max", "100")
    page.fill("#temp_sensor_step", "50")
    page.click("#page-temp-sensor-view button.converter-convert-btn:has-text('Рассчитать')")
    page.wait_for_timeout(700)
    res = page.evaluate("""(function(){
        var r = document.getElementById('tempSensorResults');
        return {
            visible: r.style.display !== 'none',
            table: !!document.getElementById('tempTableContainer'),
            title: r.textContent.indexOf('Таблица значений (шаг 50°C)') !== -1,
            copyBtnText: r.textContent.indexOf('Копировать') !== -1,
            nButtons: r.querySelectorAll('button').length,
            r50: r.textContent.indexOf('60,7') !== -1
        };
    })()""")
    check('D: ТС — результаты показаны', res['visible'])
    check('E: ТС — таблица значений есть', res['table'])
    check('F: ТС — заголовок «Таблица значений (шаг 50°C)» есть', res['title'])
    check('G: ТС — кнопки «Копировать» НЕТ', not res['copyBtnText'])
    check('H: ТС — кнопок в результатах 0 шт.', res['nButtons'] == 0, res['nButtons'])
    check('I: ТС — R(50) = 60,7 Ом в таблице', res['r50'])

    # --- ТП (ТХК L): расчёт → таблица без кнопки ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(600)
    page.click("#tsTcCards .ts-card:has-text('ТХК (L)')")
    page.wait_for_timeout(600)
    check('J: страница датчика ТХК (L) открыта',
          page.evaluate("document.getElementById('page-temp-sensor-view').classList.contains('active')"))
    page.fill("#temp_sensor_min", "0")
    page.fill("#temp_sensor_max", "100")
    page.fill("#temp_sensor_step", "50")
    page.click("#page-temp-sensor-view button.converter-convert-btn:has-text('Рассчитать')")
    page.wait_for_timeout(700)
    res2 = page.evaluate("""(function(){
        var r = document.getElementById('tempSensorResults');
        return {
            table: !!document.getElementById('tempTableContainer'),
            title: r.textContent.indexOf('Таблица значений (шаг 50°C)') !== -1,
            copyBtnText: r.textContent.indexOf('Копировать') !== -1,
            nButtons: r.querySelectorAll('button').length,
            e100: r.textContent.indexOf('6,8617') !== -1
        };
    })()""")
    check('K: ТП — таблица значений есть', res2['table'])
    check('L: ТП — заголовок таблицы есть', res2['title'])
    check('M: ТП — кнопки «Копировать» НЕТ', not res2['copyBtnText'])
    check('N: ТП — кнопок в результатах 0 шт.', res2['nButtons'] == 0, res2['nButtons'])
    check('O: ТП — E(100) ≈ 6,8617 мВ в таблице', res2['e100'])
    page.screenshot(path='scripts/task374-proof-desktop-tc.png', full_page=False)

    # --- Соседний раздел «Шкала-сигнал»: кнопка «Копировать» ОСТАЛАСЬ ---
    page.evaluate("navigateTo('scale-signal')")
    page.wait_for_timeout(700)
    scale_ok = page.evaluate("""(function(){
        var b = document.querySelector('#scaleResultsArea button.query-btn');
        return !!(b && b.textContent.indexOf('Копировать') !== -1 && b.getAttribute('onclick').indexOf('copyScaleTable') !== -1);
    })()""")
    check('P: «Шкала-сигнал» — своя кнопка «Копировать» на месте (не тронута)', scale_ok)
    check('Q: десктоп — 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема =================
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    page2.on('dialog', lambda d: d.accept())
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    ctx2.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t374-b');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('temp-sensors')")
    page2.wait_for_timeout(700)
    page2.click("#tsTcCards .ts-card:has-text('ТХА (K)')")
    page2.wait_for_timeout(600)
    page2.fill("#temp_sensor_min", "0")
    page2.fill("#temp_sensor_max", "100")
    page2.fill("#temp_sensor_step", "50")
    page2.click("#page-temp-sensor-view button.converter-convert-btn:has-text('Рассчитать')")
    page2.wait_for_timeout(700)
    res3 = page2.evaluate("""(function(){
        var r = document.getElementById('tempSensorResults');
        return {
            table: !!document.getElementById('tempTableContainer'),
            copyBtnText: r.textContent.indexOf('Копировать') !== -1,
            e100: r.textContent.indexOf('4,096') !== -1
        };
    })()""")
    check('R: светлая — таблица есть (ТХА K)', res3['table'])
    check('S: светлая — кнопки «Копировать» НЕТ', not res3['copyBtnText'])
    check('T: светлая — E(100) = 4,096 мВ (НИСТ)', res3['e100'])
    page2.screenshot(path='scripts/task374-proof-light.png', full_page=False)
    check('U: светлая — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('')
print('ИТОГО: %d passed, %d failed (из %d)' % (PASS, FAIL, PASS + FAIL))
sys.exit(0 if FAIL == 0 else 1)
