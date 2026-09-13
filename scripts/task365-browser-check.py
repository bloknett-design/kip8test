#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 365: browser-check — заявка пользователя (с поправкой):
#   1) «В разделе Расходомеры хозрасчётные, в Хозрасчёте №12 период
#      указан еженедельно, но фактически нужно ежедневно, в
#      соответствии с формой ввода данных» — сервер/кэш отдают
#      «Еженедельно» (как в таблице), приложение должно показать
#      «Ежедневно» (нормализация) и вести себя суточно;
#   2) «красным должно быть с шести утра новых суток от суток ввода
#      данных, пока не введут новые данные, а не ровно час» —
#      красный с 6:00 следующих суток ДЕРЖИТСЯ (6:30, 7:30, 12:00,
#      следующие дни), зелёный — только после ввода новых данных.
# Контексты:
#   1. десктоп 1280 тёмная, Админ: список (бейджи №12/№3, цвета),
#      таймлайн фиксированного времени (ввод даты патчится
#      subclass-Date → window.__fixed), деталь №12, форма ввода №2
#      (оптимистичный зелёный + после серверного load());
#   2. мобайл 375: список жив, бейдж №12, красный «пора вводить».
# + 0 JS-ошибок; скриншоты-пруфы.
import datetime
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8963
TODAY = datetime.date.today()
T1 = TODAY + datetime.timedelta(days=1)   # «завтра» — новые сутки
T2 = TODAY + datetime.timedelta(days=2)

def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)

def iso(d):
    return d.strftime('%Y-%m-%d')

def meter(i, hoz, param, dprev, dcurr, prev, curr, period):
    return {'id': i, 'hoz': hoz, 'param': param, 'datePrev': mdy(dprev),
            'dateCurr': mdy(dcurr), 'prev': prev, 'curr': curr, 'unit': 'м³',
            'temp': None, 'gcal': None, 'period': period,
            'modRole': 'Админ', 'modName': 'mobile_test',
            'modDisplayName': 'mobile_test', 'modTimestamp': None}

# #2 — введено сегодня за вчера (зелёный); #4 — за позавчера
# (красный); #12 — из таблицы «Еженедельно» + данные за вчера
# (нормализация → суточный ритм); #3 — настоящий недельный,
# данные сегодня (та же неделя → зелёный, бейдж не тронут).
MOCK_METERS = [
    meter(2,  'Хозрасчёт №2',  'Расход воды речной в корпус 114',
          TODAY - datetime.timedelta(days=2), TODAY - datetime.timedelta(days=1),
          383181.0, 383291.0, 'Ежедневно'),
    meter(4,  'Хозрасчёт №4',  'Расход воздуха технологического в корпус 114',
          TODAY - datetime.timedelta(days=3), TODAY - datetime.timedelta(days=2),
          655000.0, 679700.0, 'Ежедневно'),
    meter(12, 'Хозрасчёт №12', 'Расход воздуха технологического в корпус 116',
          TODAY - datetime.timedelta(days=2), TODAY - datetime.timedelta(days=1),
          109634.0, 110393.0, 'Еженедельно'),
    meter(3,  'Хозрасчёт №3',  'Расход воды пожарохозяйственной (ПХВ) в корпус 114',
          TODAY - datetime.timedelta(days=1), TODAY,
          0.0, 0.0, 'Еженедельно'),
]

STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': STATE['role']}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': STATE['role'], 'found': True,
                'permissions': {'flowmeter.view': True, 'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': json.loads(json.dumps(MOCK_METERS))}}
    if action == 'flowmeter.getValidationRules':
        return {'ok': True, 'data': {'rules': []}}
    if action == 'flowmeter.getRecentAllMeters':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.updateReading':
        pid = body.get('id') if body else None
        for m in MOCK_METERS:
            if m['id'] == pid:
                m['prev'] = body.get('prev', m['prev'])
                m['curr'] = body.get('curr', m['curr'])
                m['datePrev'] = body.get('datePrev', m['datePrev'])
                m['dateCurr'] = body.get('dateCurr', m['dateCurr'])
                if body.get('temp') is not None:
                    m['temp'] = body['temp']
                break
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

RED = 'rgb(255, 92, 71)'     # #ff5c47 (тёмная тема)
GREEN = 'rgb(90, 184, 112)'  # #5ab870

VAL_COLOR = """(function(){
    var el = document.querySelector('.flow-card[data-flow-id="%d"] .flow-summary-val');
    return el ? getComputedStyle(el).color : null;
})()"""

BADGE = """(function(){
    var el = document.querySelector('.flow-card[data-flow-id="%d"] .flow-card-period');
    return el ? el.textContent.trim() : null;
})()"""

# Патч даты: new Date() без аргументов и Date.now() возвращают
# window.__fixed (мс); конструктор с аргументами — настоящий.
# Таймеры/timeout приложения НЕ подменяются — реальные (после
# сохранения load() сработает сам).
DATE_PATCH = """(function(){
    if (window.__datePatched) return 'already';
    var RealDate = Date;
    window.Date = class extends RealDate {
        constructor(...a) {
            if (a.length === 0 && window.__fixed !== undefined) super(window.__fixed);
            else super(...a);
        }
        static now() {
            return window.__fixed !== undefined ? window.__fixed : RealDate.now();
        }
    };
    window.__datePatched = true;
    return 'patched';
})()"""

def set_fixed(page, d, hh, mm):
    ms = int(datetime.datetime(d.year, d.month, d.day, hh, mm).timestamp() * 1000)
    page.evaluate('window.__fixed = %d' % ms)
    page.evaluate('FlowmeterData.renderList()')

def cache_seed():
    return json.dumps({'meters': MOCK_METERS, 'ts': 1}, ensure_ascii=False)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t365)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    # localStorage ДО загрузки (init-script): токен, тёмная тема,
    # кэш расходомеров с «Еженедельно» у №12 (как из реального кэша)
    # kip8test изолирует localStorage префиксом «kip8test:» (шим
    # isolateLocalStorage внутри index.html). Init-script выполняется
    # ДО установки шима, поэтому пишем РОВНО те сырые ключи, которые
    # шим будет читать: 'kip8test:' + ключ приложения.
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t365-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');" +
        "localStorage.setItem('kip8test:kip8_flow_cache_v1', JSON.stringify(%s));" % cache_seed())
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    # патч даты → «сегодня 12:00», открытие раздела
    page.evaluate(DATE_PATCH)
    page.evaluate('window.__fixed = %d' % int(datetime.datetime(TODAY.year, TODAY.month, TODAY.day, 12, 0).timestamp() * 1000))
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(2000)

    check('B: список отрисован (4 карточки)',
          page.evaluate("document.querySelectorAll('.flow-card').length") == 4,
          page.evaluate("document.querySelectorAll('.flow-card').length"))
    check('C: №12 — бейдж «Ежедневно» (нормализация из «Еженедельно»)',
          page.evaluate(BADGE % 12) == 'Ежедневно', page.evaluate(BADGE % 12))
    check('D: №3 — бейдж «Еженедельно» (настоящий недельный не тронут)',
          page.evaluate(BADGE % 3) == 'Еженедельно', page.evaluate(BADGE % 3))
    check('E: №2 зелёный (введено сегодня за вчера)',
          page.evaluate(VAL_COLOR % 2) == GREEN, page.evaluate(VAL_COLOR % 2))
    check('F: №4 красный (за вчера данных нет)',
          page.evaluate(VAL_COLOR % 4) == RED, page.evaluate(VAL_COLOR % 4))
    check('G: №12 зелёный (суточная логика: вчера есть)',
          page.evaluate(VAL_COLOR % 12) == GREEN, page.evaluate(VAL_COLOR % 12))
    page.screenshot(path='scripts/task365-proof-desktop.png')

    # --- таймлайн: новые сутки (завтра) ---
    set_fixed(page, T1, 6, 30)
    check('H: завтра 6:30 — №2 КРАСНЫЙ (старт: 6:00 новых суток)',
          page.evaluate(VAL_COLOR % 2) == RED, page.evaluate(VAL_COLOR % 2))
    check('I: завтра 6:30 — №12 КРАСНЫЙ (суточный ритм нормализованного №12; недельный держал бы зелёным до понедельника)',
          page.evaluate(VAL_COLOR % 12) == RED, page.evaluate(VAL_COLOR % 12))
    check('J: завтра 6:30 — №4 всё ещё красный',
          page.evaluate(VAL_COLOR % 4) == RED, page.evaluate(VAL_COLOR % 4))

    set_fixed(page, T1, 7, 30)
    check('K: завтра 7:30 — №2 всё ЕЩЁ КРАСНЫЙ (поправка: НЕ ровно час)',
          page.evaluate(VAL_COLOR % 2) == RED, page.evaluate(VAL_COLOR % 2))
    check('L: завтра 7:30 — №12 всё ещё красный',
          page.evaluate(VAL_COLOR % 12) == RED, page.evaluate(VAL_COLOR % 12))

    set_fixed(page, T1, 12, 0)
    check('M: завтра 12:00 — №2 красный держится',
          page.evaluate(VAL_COLOR % 2) == RED, page.evaluate(VAL_COLOR % 2))

    set_fixed(page, T2, 9, 0)
    check('N: послезавтра 9:00 — №2 красный днями (пока нет данных)',
          page.evaluate(VAL_COLOR % 2) == RED, page.evaluate(VAL_COLOR % 2))

    # --- деталь №12: бейдж периода в карточке ---
    set_fixed(page, T1, 12, 10)
    page.evaluate("FlowmeterData.openDetail(12)")
    page.wait_for_timeout(600)
    check('O: деталь №12 — период «Ежедневно»',
          page.evaluate("(function(){var e=document.querySelector('.flow-detail-period');return e?e.textContent.trim():null;})()") == 'Ежедневно',
          page.evaluate("(function(){var e=document.querySelector('.flow-detail-period');return e?e.textContent.trim():null;})()"))

    # --- ввод новых данных по №2 (завтра 12:30) → сразу зелёный ---
    set_fixed(page, T1, 12, 30)
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    date_val = page.evaluate("document.getElementById('flowInputDate').value")
    check('P: форма — дата по умолчанию «вчера» (сегодня относительно фиксированного «завтра»)',
          date_val == iso(TODAY), date_val)
    page.fill('#flowInputField', '205,5')
    page.screenshot(path='scripts/task365-proof-form.png')
    page.click('.flow-input-submit')
    page.wait_for_timeout(250)
    check('Q: сразу после «Сохранить» — №2 ЗЕЛЁНЫЙ (оптимистично)',
          page.evaluate(VAL_COLOR % 2) == GREEN, page.evaluate(VAL_COLOR % 2))
    page.wait_for_timeout(1500)
    check('R: после серверного load() — №2 остаётся ЗЕЛЁНЫМ (новые данные)',
          page.evaluate(VAL_COLOR % 2) == GREEN, page.evaluate(VAL_COLOR % 2))
    check('S: №12 без новых данных — по-прежнему красный',
          page.evaluate(VAL_COLOR % 12) == RED, page.evaluate(VAL_COLOR % 12))
    check('T: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, тёмная =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    ctx2.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t365-b');" +
        "localStorage.setItem('kip8test:app-theme','dark');" +
        "localStorage.setItem('kip8test:kip8_flow_cache_v1', JSON.stringify(%s));" % cache_seed())
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate(DATE_PATCH)
    page2.evaluate('window.__fixed = %d' % int(datetime.datetime(TODAY.year, TODAY.month, TODAY.day, 12, 0).timestamp() * 1000))
    page2.evaluate("navigateTo('flowmeter-data')")
    page2.wait_for_timeout(2000)
    check('U: мобайл — список жив (4 карточки)',
          page2.evaluate("document.querySelectorAll('.flow-card').length") == 4)
    check('V: мобайл — №12 «Ежедневно»',
          page2.evaluate(BADGE % 12) == 'Ежедневно', page2.evaluate(BADGE % 12))
    check('W: мобайл — №4 красный, №2 зелёный',
          page2.evaluate(VAL_COLOR % 4) == RED and page2.evaluate(VAL_COLOR % 2) == GREEN,
          (page2.evaluate(VAL_COLOR % 4), page2.evaluate(VAL_COLOR % 2)))
    check('X: мобайл — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
