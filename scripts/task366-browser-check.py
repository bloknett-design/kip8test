#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 366: browser-check — 2 заявки пользователя:
#   1) баннер недоставленных показаний: текст с НОМЕРАМИ расходомеров,
#      просто читаемый, БЕЗ иконки (было «⟳ Показаний ждут отправки:
#      N — уйдут на сервер…»);
#   2) дубль-заявка (архив) — серверная, покрыта VM-тестами; здесь
#      проверяем клиентскую часть потока: offline-ввод → запись
#      остаётся в outbox (баннер с номером) → сервер ожил → флаш
#      → баннер исчез.
# Контексты:
#   1. десктоп 1280 тёмная, Админ: баннер в 3 состояниях (1 запись /
#      2 расходомера / №2 ×2), реальный offline-ввод, живой флаш;
#   2. мобайл 375: баннер жив, переносится, список жив.
# + 0 JS-ошибок; скриншот-пруф.
import datetime
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8965
TODAY = datetime.date.today()
YESTERDAY = TODAY - datetime.timedelta(days=1)

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

MOCK_METERS = [
    meter(2,  'Хозрасчёт №2',  'Расход воды речной в корпус 114',
          TODAY - datetime.timedelta(days=2), YESTERDAY, 383181.0, 383291.0, 'Ежедневно'),
    meter(4,  'Хозрасчёт №4',  'Расход воздуха технологического в корпус 114',
          TODAY - datetime.timedelta(days=3), TODAY - datetime.timedelta(days=2),
          655000.0, 679700.0, 'Ежедневно'),
    meter(12, 'Хозрасчёт №12', 'Расход воздуха технологического в корпус 116',
          TODAY - datetime.timedelta(days=2), YESTERDAY, 109634.0, 110393.0, 'Ежедневно'),
    meter(3,  'Хозрасчёт №3',  'Расход воды пожарохозяйственной (ПХВ) в корпус 114',
          YESTERDAY, TODAY, 0.0, 0.0, 'Еженедельно'),
]

STATE = {'role': 'Админ', 'fail_update': False}

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
                break
        return {'ok': True, 'data': {'id': pid}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def outbox_seed(entries):
    return json.dumps(entries, ensure_ascii=False)

def entry(cid, mid, prev, curr):
    return {'cid': cid, 'kind': 'day',
            'payload': {'id': mid, 'prev': prev, 'curr': curr,
                        'datePrev': mdy(YESTERDAY), 'dateCurr': mdy(TODAY),
                        'temp': None, 'isEdit': False},
            'isEdit': False, 'ts': 1700000000000, 'state': 'pending'}

BANNER_TEXT = """(function(){
    var b = document.querySelector('.flow-outbox-banner');
    return b ? b.textContent.trim() : null;
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())   # beforeunload-предупреждение outbox

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if action == 'flowmeter.updateReading' and STATE['fail_update']:
            route.abort('connectionfailed')
            return
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t366)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t366-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1500)
    check('B: список отрисован (4 карточки), баннера НЕТ',
          page.evaluate("document.querySelectorAll('.flow-card').length") == 4 and
          page.evaluate("document.querySelector('.flow-outbox-banner') === null"))

    # --- состояние 1: одна запись ---
    page.evaluate("localStorage.setItem('kip8_flow_outbox_v1', %s)" % json.dumps(
        outbox_seed([entry('c1', 2, 383291.0, 383400.0)])))
    page.evaluate("FlowmeterData.renderList()")
    t = page.evaluate(BANNER_TEXT)
    check('C: одна запись — «Показание №2 не отправлено — отправится…»',
          t == 'Показание №2 не отправлено — отправится на сервер автоматически при восстановлении связи', t)
    check('D: иконки нет (нет .flow-outbox-ico и символа ⟳)',
          page.evaluate("document.querySelector('.flow-outbox-banner .flow-outbox-ico') === null") and
          '⟳' not in (t or ''))
    bg = page.evaluate("(function(){var b=document.querySelector('.flow-outbox-banner');return b?getComputedStyle(b).backgroundColor:null;})()")
    check('E: стиль баннера прежний (амбер Task 358)',
          bg is not None and '230, 150, 20' in bg, bg)

    # --- состояние 2: два расходомера ---
    page.evaluate("localStorage.setItem('kip8_flow_outbox_v1', %s)" % json.dumps(
        outbox_seed([entry('c1', 2, 383291.0, 383400.0), entry('c2', 4, 679700.0, 679800.0)])))
    page.evaluate("FlowmeterData.renderList()")
    t = page.evaluate(BANNER_TEXT)
    check('F: две записи — «Показания №2, №4 не отправлены — отправятся…»',
          t == 'Показания №2, №4 не отправлены — отправятся на сервер автоматически при восстановлении связи', t)

    # --- состояние 3: №2 ×2 + №4 ---
    page.evaluate("localStorage.setItem('kip8_flow_outbox_v1', %s)" % json.dumps(
        outbox_seed([entry('c1', 2, 383291.0, 383400.0), entry('c2', 4, 679700.0, 679800.0),
                     entry('c3', 2, 383400.0, 383520.0)])))
    page.evaluate("FlowmeterData.renderList()")
    t = page.evaluate(BANNER_TEXT)
    check('G: три записи — «№2 ×2, №4»',
          t == 'Показания №2 ×2, №4 не отправлены — отправятся на сервер автоматически при восстановлении связи', t)
    page.screenshot(path='scripts/task366-proof-desktop.png')

    # --- чистый outbox → баннера нет ---
    page.evaluate("localStorage.removeItem('kip8_flow_outbox_v1')")
    page.evaluate("FlowmeterData.renderList()")
    check('H: outbox пуст — баннера нет',
          page.evaluate("document.querySelector('.flow-outbox-banner') === null"))

    # --- реальный offline-ввод: сервер «умер» на updateReading ---
    STATE['fail_update'] = True
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '385,5')
    page.click('.flow-input-submit')
    page.wait_for_timeout(1500)
    st = page.evaluate("(FlowmeterData._outboxLoad()[0]||{}).state")
    check('I: offline-ввод — запись в outbox со state=retry', st == 'retry', st)
    page.evaluate("FlowmeterData.renderList()")
    t = page.evaluate(BANNER_TEXT)
    check('J: после возврата к списку — баннер с номером №2',
          t == 'Показание №2 не отправлено — отправится на сервер автоматически при восстановлении связи', t)

    # --- сервер ожил → флаш → баннер исчез ---
    STATE['fail_update'] = False
    page.evaluate("FlowmeterData._flushOutbox('test')")
    page.wait_for_timeout(1500)
    n = page.evaluate("FlowmeterData._outboxCount()")
    check('K: флаш доставил запись (outbox пуст)', n == 0, n)
    page.evaluate("FlowmeterData.renderList()")
    check('L: после доставки баннер исчез',
          page.evaluate("document.querySelector('.flow-outbox-banner') === null"))
    check('M: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, тёмная =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    page2.on('dialog', lambda d: d.accept())
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    ctx2.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t366-b');" +
        "localStorage.setItem('kip8test:app-theme','dark');" +
        "localStorage.setItem('kip8test:kip8_flow_outbox_v1', %s);" % json.dumps(
            outbox_seed([entry('c1', 2, 383291.0, 383400.0), entry('c2', 12, 110393.0, 110500.0)])))
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('flowmeter-data')")
    page2.wait_for_timeout(1500)
    check('N: мобайл — список жив (4 карточки)',
          page2.evaluate("document.querySelectorAll('.flow-card').length") == 4)
    t2 = page2.evaluate(BANNER_TEXT)
    check('O: мобайл — баннер «№2, №12» читаем',
          t2 == 'Показания №2, №12 не отправлены — отправятся на сервер автоматически при восстановлении связи', t2)
    h = page2.evaluate("(function(){var b=document.querySelector('.flow-outbox-banner');return b?b.getBoundingClientRect().height:0;})()")
    check('P: мобайл — баннер переносится (высота > 40px)', h > 40, h)
    page2.screenshot(path='scripts/task366-proof-mobile.png')
    check('Q: мобайл — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
