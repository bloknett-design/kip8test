#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 370: browser-check — заявка пользователя:
#   «внеси изменения сразу и в тестовый и в боевой проекты,
#    жёлто-оранжевые значения недоставленных вместо баннера,
#    измени цвет чуть ярче и ближе к желтому.»
# Проверка НОВОГО цвета + полный регресс поведения Task 367/368:
#   1. десктоп 1280 тёмная, Админ: баннера нет; зелёный/красный/
#      жёлто-оранжевый #ffc400; недельные/месячные — по ЗАКРЫТЫМ
#      календарным периодам (Task 368: данные накрывают закрытую
#      неделю/месяц — зелёный; закрытый период без данных — красный,
#      в т.ч. сокращения «Еженед.»/«Ежемес.»); приоритет pending
#      над красным; реальный offline-ввод → цвет появляется сам
#      (hook после _outboxAdd); флаш → снова зелёный.
#   2. светлая тема: жёлто-оранжевый #cc9900, красный #e8230a.
#   3. мобайл 375: то же, баннера нет.
# + 0 JS-ошибок; скриншот-пруфы.
import datetime
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8970
TODAY = datetime.date.today()
D3 = TODAY - datetime.timedelta(days=3)     # суточные: старше цикла → красный

# Task 368: красный недельных/месячных — по ЗАКРЫТЫМ календарным
# периодам; моки детерминированы и не зависят от дня запуска
# (урок: «данные 7 дней назад» ВСЕГДА накрывают закрытую неделю)
def monday_of(d):
    return d - datetime.timedelta(days=d.weekday())

MON = monday_of(TODAY)
W_START = MON - datetime.timedelta(days=7)    # закрытая неделя: пн
W_END = MON - datetime.timedelta(days=1)      # закрытая неделя: вс
W2_START = MON - datetime.timedelta(days=14)  # позапрошлая неделя
W2_END = MON - datetime.timedelta(days=8)

def prev_month_bounds(d):
    first = d.replace(day=1)
    last = first - datetime.timedelta(days=1)
    return last.replace(day=1), last

M_START, M_END = prev_month_bounds(TODAY)      # прошлый месяц
M2_START, M2_END = prev_month_bounds(M_START)  # позапрошлый месяц

# Цвета (тёмная тема)
GREEN = 'rgb(90, 184, 112)'      # #5ab870
RED = 'rgb(255, 92, 71)'         # #ff5c47 (Task 359)
AMBER = 'rgb(255, 196, 0)'       # #ffc400 (Task 370 pending — ярче/желтее)
# Светлая тема
RED_L = 'rgb(232, 35, 10)'       # #e8230a
AMBER_L = 'rgb(204, 153, 0)'     # #cc9900 (Task 370)

def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)

def meter(i, hoz, param, dprev, dcurr, prev, curr, period):
    return {'id': i, 'hoz': hoz, 'param': param, 'datePrev': mdy(dprev),
            'dateCurr': mdy(dcurr), 'prev': prev, 'curr': curr, 'unit': 'м³',
            'temp': None, 'gcal': None, 'period': period,
            'modRole': 'Админ', 'modName': 'mobile_test',
            'modDisplayName': 'mobile_test', 'modTimestamp': None}

MOCK_METERS = [
    meter(2,  'Хозрасчёт №2',  'Расход воды речной в корпус 114',
          D3, TODAY - datetime.timedelta(days=1), 383181.0, 383291.0, 'Ежедневно'),
    meter(4,  'Хозрасчёт №4',  'Расход воздуха технологического в корпус 114',
          TODAY - datetime.timedelta(days=4), D3, 655000.0, 679700.0, 'Ежедневно'),
    meter(12, 'Хозрасчёт №12', 'Расход воздуха технологического в корпус 116',
          D3, TODAY - datetime.timedelta(days=1), 109634.0, 110393.0, 'Ежедневно'),
    meter(3,  'Хозрасчёт №3',  'Расход воды пожарохозяйственной (ПХВ) в корпус 114',
          W_START, W_END, 381484.0, 381485.0, 'Еженедельно'),
    meter(9,  'Хозрасчёт №9',  'Расход азота в корпус 114',
          M_START, M_END, 8544.5, 8545.5, 'Ежемесячно'),
    meter(11, 'Хозрасчёт №11', 'Расход воды речной в корпус 116',
          W2_START, W2_END, 105240.0, 105241.0, 'Еженед.'),   # сокращение (Task 367)
    meter(5,  'Хозрасчёт №5',  'Расход пара в корпус 114',
          M2_START, M2_END, 1234.0, 1240.0, 'Ежемес.'),      # сокращение (Task 367)
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
                        'datePrev': mdy(D3), 'dateCurr': mdy(TODAY),
                        'temp': None, 'isEdit': False},
            'isEdit': False, 'ts': 1700000000000, 'state': 'pending'}

VAL_COLOR = """(function(id){
    var card = document.querySelector('.flow-card[data-flow-id="' + id + '"]');
    if (!card) return null;
    var v = card.querySelector('.flow-summary-val');
    return v ? getComputedStyle(v).color : null;
})"""

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t370)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t370-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1500)
    check('B: список отрисован (7 карточек), баннера НЕТ',
          page.evaluate("document.querySelectorAll('.flow-card').length") == 7 and
          page.evaluate("document.querySelector('.flow-outbox-banner') === null"))

    # --- цвета: зелёный / красный по закрытым периодам (Task 368) ---
    check('C: №2 (данные вчера) — ЗЕЛЁНЫЙ', page.evaluate(VAL_COLOR, 2) == GREEN,
          page.evaluate(VAL_COLOR, 2))
    check('D: №4 (данные 3 дня назад) — КРАСНЫЙ (суточные)',
          page.evaluate(VAL_COLOR, 4) == RED, page.evaluate(VAL_COLOR, 4))
    check('E: №3 недельный — данные за ЗАКРЫТУЮ неделю → ЗЕЛЁНЫЙ (Task 368: накрывает)',
          page.evaluate(VAL_COLOR, 3) == GREEN, page.evaluate(VAL_COLOR, 3))
    check('F: №9 месячный — данные за прошлый месяц → ЗЕЛЁНЫЙ (Task 368)',
          page.evaluate(VAL_COLOR, 9) == GREEN, page.evaluate(VAL_COLOR, 9))
    check('G: №11 «Еженед.» (сокращение) — данные позапрошлой неделей → КРАСНЫЙ',
          page.evaluate(VAL_COLOR, 11) == RED, page.evaluate(VAL_COLOR, 11))
    check('H: №5 «Ежемес.» (сокращение) — данные позапрошлым месяцем → КРАСНЫЙ',
          page.evaluate(VAL_COLOR, 5) == RED, page.evaluate(VAL_COLOR, 5))

    # --- жёлто-оранжевый НОВЫЙ цвет (Task 370): недоставленные показания ---
    page.evaluate("localStorage.setItem('kip8_flow_outbox_v1', %s)" % json.dumps(
        outbox_seed([entry('c1', 2, 383291.0, 383400.0)])))
    page.evaluate("FlowmeterData.renderList()")
    check('I: №2 с записью в outbox — ЖЁЛТО-ОРАНЖЕВЫЙ ЯРКИЙ #ffc400 (Task 370)',
          page.evaluate(VAL_COLOR, 2) == AMBER, page.evaluate(VAL_COLOR, 2))
    check('J: №12 без записи — ЗЕЛЁНЫЙ (соседи не тронуты)',
          page.evaluate(VAL_COLOR, 12) == GREEN, page.evaluate(VAL_COLOR, 12))

    # --- приоритет: pending НАД красным ---
    page.evaluate("localStorage.setItem('kip8_flow_outbox_v1', %s)" % json.dumps(
        outbox_seed([entry('c1', 2, 383291.0, 383400.0), entry('c2', 4, 679700.0, 679800.0)])))
    page.evaluate("FlowmeterData.renderList()")
    check('K: №4 красный + недоставленное — ЖЁЛТО-ОРАНЖЕВЫЙ (приоритет pending)',
          page.evaluate(VAL_COLOR, 4) == AMBER, page.evaluate(VAL_COLOR, 4))
    # пруф: полный палитры кадр — №2/№4 жёлто-оранжевые (pending),
    # №12/№3/№9 зелёные, №11/№5 красные (закрытые периоды)
    page.screenshot(path='scripts/task370-proof-desktop.png')
    page.evaluate("localStorage.setItem('kip8_flow_outbox_v1', %s)" % json.dumps(
        outbox_seed([entry('c1', 2, 383291.0, 383400.0)])))
    page.evaluate("FlowmeterData.renderList()")
    check('L: запись №4 удалена — снова КРАСНЫЙ',
          page.evaluate(VAL_COLOR, 4) == RED, page.evaluate(VAL_COLOR, 4))

    # --- очистка → снова зелёный ---
    page.evaluate("localStorage.removeItem('kip8_flow_outbox_v1')")
    page.evaluate("FlowmeterData.renderList()")
    check('M: outbox пуст — №2 снова ЗЕЛЁНЫЙ',
          page.evaluate(VAL_COLOR, 2) == GREEN, page.evaluate(VAL_COLOR, 2))

    # --- реальный offline-ввод: цвет появляется сам (hook Task 367) ---
    STATE['fail_update'] = True
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '385,5')
    page.click('.flow-input-submit')
    page.wait_for_timeout(1500)
    st = page.evaluate("(FlowmeterData._outboxLoad()[0]||{}).state")
    check('N: offline-ввод — запись в outbox со state=retry', st == 'retry', st)
    check('O: цвет появился БЕЗ ручного renderList (hook после _outboxAdd)',
          page.evaluate(VAL_COLOR, 2) == AMBER, page.evaluate(VAL_COLOR, 2))

    # --- сервер ожил → флаш → снова зелёный ---
    STATE['fail_update'] = False
    page.evaluate("FlowmeterData._flushOutbox('test')")
    page.wait_for_timeout(1500)
    n = page.evaluate("FlowmeterData._outboxCount()")
    check('P: флаш доставил запись (outbox пуст)', n == 0, n)
    check('Q: после доставки — №2 снова ЗЕЛЁНЫЙ (finish() → renderList)',
          page.evaluate(VAL_COLOR, 2) == GREEN, page.evaluate(VAL_COLOR, 2))
    check('R: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема — цвета читаемы =================
    # Сервер «мёртв» для updateReading: иначе init-флаш доставит записи
    # до первого рендера — значения уже вернутся зелёными
    STATE['fail_update'] = True
    ctx3 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    page3.on('dialog', lambda d: d.accept())
    ctx3.route('**/exec?**', handle)
    ctx3.route('**script.google.com/**', handle)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)
    ctx3.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t370-c');" +
        "localStorage.setItem('kip8test:app-theme','light');" +
        # init-script пишет в сырой localStorage ДО установки обёртки
        # изоляции — ключ нужен уже с префиксом kip8test:
        "localStorage.setItem('kip8test:kip8_flow_outbox_v1', %s);" % json.dumps(
            outbox_seed([entry('c1', 2, 383291.0, 383400.0)]), ensure_ascii=False))
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('flowmeter-data')")
    page3.wait_for_timeout(1500)
    check('S: светлая — жёлто-оранжевый золотистый #cc9900 (Task 370)',
          page3.evaluate(VAL_COLOR, 2) == AMBER_L, page3.evaluate(VAL_COLOR, 2))
    check('T: светлая — красный #e8230a (№4)',
          page3.evaluate(VAL_COLOR, 4) == RED_L, page3.evaluate(VAL_COLOR, 4))
    check('U: светлая — баннера нет',
          page3.evaluate("document.querySelector('.flow-outbox-banner') === null"))
    page3.screenshot(path='scripts/task370-proof-light.png')
    check('V: светлая — 0 JS-ошибок', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 3: мобайл 375, тёмная =================
    # fail_update остаётся True — записи переживают init-флаш
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t370-b');" +
        "localStorage.setItem('kip8test:app-theme','dark');" +
        # init-script пишет в сырой localStorage ДО установки обёртки
        # изоляции — ключ нужен уже с префиксом kip8test:
        "localStorage.setItem('kip8test:kip8_flow_outbox_v1', %s);" % json.dumps(
            outbox_seed([entry('c1', 2, 383291.0, 383400.0), entry('c2', 12, 110393.0, 110500.0)]), ensure_ascii=False))
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('flowmeter-data')")
    page2.wait_for_timeout(1500)
    check('W: мобайл — список жив (7 карточек), баннера нет',
          page2.evaluate("document.querySelectorAll('.flow-card').length") == 7 and
          page2.evaluate("document.querySelector('.flow-outbox-banner') === null"))
    check('X: мобайл — №2 жёлто-оранжевый #ffc400, №12 тоже (2 записи)',
          page2.evaluate(VAL_COLOR, 2) == AMBER and page2.evaluate(VAL_COLOR, 12) == AMBER)
    check('Y: мобайл — №11 недельный (позапрошлая неделя) красный жив',
          page2.evaluate(VAL_COLOR, 11) == RED)
    page2.screenshot(path='scripts/task370-proof-mobile.png')
    check('Z: мобайл — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
