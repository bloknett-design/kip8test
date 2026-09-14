#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 368: browser-check — заявка пользователя:
#   «В хозрасчётах №3 и №11, в форме ввода показаний должен выбираться
#    период из двух дат определяющих период, и значения по умолчанию
#    в форме должны стоять даты за предыдущую календарную неделю.
#    Также с хозрасчётом №9, только период месяц. Еженедельные: красный,
#    когда календарная неделя (пн–вс) прошла; зелёный — когда данные
#    этой недели введены; снова красный, когда текущая (новая) календарная
#    неделя (пн–вс) прошла, пока не введут за неё данные. Ежемесячные:
#    красный, когда календарный месяц данных прошёл; зелёный — когда
#    данные за этот месяц введены; снова красный, когда (новый) текущий
#    календарный месяц прошел, пока не введут данные за его период.»
# Контексты:
#   1. десктоп 1280 тёмная, Админ:
#      - цвета: №3 зелёный (данные = закрытая неделя), №11 красный
#        (неделя старее закрытой), №9 зелёный (данные = прошлый месяц),
#        №5 «Ежемес.» красный, суточные №2 зелёный / №4 красный;
#      - подписи-диапазоны «за ДД.ММ–ДД.ММ.ГГГГ г.» на карточках и
#        в детальной карточке + хронология (запись — диапазон);
#      - форма №3: «Период с … по …» = закрытая неделя; №9: прошлый
#        месяц; №2: одна дата «вчера», поля периода скрыты;
#      - реальный ввод №3 → payload datePrev/dateCurr = границы
#        закрытой недели; после сохранения карточка зелёная с диапазоном;
#      - инвертированные даты — hard-отказ (тост, outbox пуст, шит открыт);
#      - правка №3 (окно 1 ч) — поля предзаполнены датами записи.
#   2. светлая тема: цвета читаемы, диапазоны живы.
#   3. мобайл 375: форма с двумя датами, список жив.
# + 0 JS-ошибок; скриншот-пруфы.
import datetime
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8967
TODAY = datetime.date.today()

def monday_of(d):
    return d - datetime.timedelta(days=d.weekday())

MON = monday_of(TODAY)                 # пн текущей недели
W_START = MON - datetime.timedelta(days=7)   # закрытая неделя: пн
W_END = MON - datetime.timedelta(days=1)    # закрытая неделя: вс
W2_START = MON - datetime.timedelta(days=14)  # неделя ДО закрытой
W2_END = MON - datetime.timedelta(days=8)

def month_first(d):
    return d.replace(day=1)

def prev_month_bounds(d):
    first = month_first(d)
    last = first - datetime.timedelta(days=1)
    return month_first(last), last

M_START, M_END = prev_month_bounds(TODAY)            # прошлый месяц
M2_START, M2_END = prev_month_bounds(M_START)        # месяц до него

def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)

def iso(d):
    return '%d-%02d-%02d' % (d.year, d.month, d.day)

YESTERDAY = TODAY - datetime.timedelta(days=1)
D3 = TODAY - datetime.timedelta(days=3)

def meter(i, hoz, param, dprev, dcurr, prev, curr, period, mod_fresh=False):
    return {'id': i, 'hoz': hoz, 'param': param, 'datePrev': mdy(dprev),
            'dateCurr': mdy(dcurr), 'prev': prev, 'curr': curr, 'unit': 'м³',
            'temp': None, 'gcal': None, 'period': period,
            'modRole': 'Админ', 'modName': 'user@test.local',
            'modDisplayName': 'user@test.local',
            'modTimestamp': (datetime.datetime.now().isoformat() if mod_fresh else None)}

MOCK_METERS = [
    meter(2,  'Хозрасчёт №2',  'Расход воды речной в корпус 114',
          YESTERDAY, YESTERDAY, 383181.0, 383291.0, 'Ежедневно'),
    meter(4,  'Хозрасчёт №4',  'Расход воздуха технологического в корпус 114',
          D3, D3, 655000.0, 679700.0, 'Ежедневно'),
    meter(3,  'Хозрасчёт №3',  'Расход воды пожарохозяйственной (ПХВ) в корпус 114',
          W_START, W_END, 381484.0, 381485.0, 'Еженедельно', mod_fresh=True),
    meter(9,  'Хозрасчёт №9',  'Расход азота в корпус 114',
          M_START, M_END, 8544.5, 8545.5, 'Ежемесячно'),
    meter(11, 'Хозрасчёт №11', 'Расход воды речной в корпус 116',
          W2_START, W2_END, 105240.0, 105241.0, 'Еженед.'),
    meter(5,  'Хозрасчёт №5',  'Расход пара в корпус 114',
          M2_START, M2_END, 1234.0, 1240.0, 'Ежемес.'),
    meter(12, 'Хозрасчёт №12', 'Расход воздуха технологического в корпус 116',
          YESTERDAY, YESTERDAY, 109634.0, 110393.0, 'Ежедневно'),
]

# Архив №3: запись-период (Task 368) + старая точечная
ARCH_3 = [
    {'meterId': 3, 'prev': 381484.0, 'curr': 381485.0, 'consumption': 1.0,
     'datePrev': mdy(W_START), 'dateCurr': mdy(W_END), 'temp': None, 'gcal': None,
     'entryType': 'сутки', 'comment': '', 'anomaly': ''},
    {'meterId': 3, 'prev': 381470.0, 'curr': 381484.0, 'consumption': 14.0,
     'datePrev': mdy(W2_START), 'dateCurr': mdy(W2_END), 'temp': None, 'gcal': None,
     'entryType': 'сутки', 'comment': '', 'anomaly': ''},
]

STATE = {'role': 'Админ'}
CAPTURED = []

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
        pid = (body or {}).get('id')
        return {'ok': True, 'data': {'records': ARCH_3 if pid == 3 else []}}
    if action == 'flowmeter.updateReading':
        CAPTURED.append(body)
        pid = body.get('id') if body else None
        for m in MOCK_METERS:
            if m['id'] == pid:
                m['prev'] = body.get('prev', m['prev'])
                m['curr'] = body.get('curr', m['curr'])
                m['datePrev'] = body.get('datePrev', m['datePrev'])
                m['dateCurr'] = body.get('dateCurr', m['dateCurr'])
                m['modTimestamp'] = datetime.datetime.now().isoformat()
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

VAL_COLOR = """(function(id){
    var card = document.querySelector('.flow-card[data-flow-id="' + id + '"]');
    if (!card) return null;
    var v = card.querySelector('.flow-summary-val');
    return v ? getComputedStyle(v).color : null;
})"""

CARD_DATE = """(function(id){
    var card = document.querySelector('.flow-card[data-flow-id="' + id + '"]');
    if (!card) return null;
    var el = card.querySelector('.flow-summary-date-inline');
    return el ? el.textContent : null;
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t368)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t368-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1500)
    check('B: список отрисован (7 карточек)',
          page.evaluate("document.querySelectorAll('.flow-card').length") == 7)

    GREEN = 'rgb(90, 184, 112)'
    RED = 'rgb(255, 92, 71)'
    # --- цвета по ЗАКРЫТЫМ периодам (сегодня — после закрытия недели/месяца) ---
    check('C: №2 суточный (вчера) — ЗЕЛЁНЫЙ', page.evaluate(VAL_COLOR, 2) == GREEN,
          page.evaluate(VAL_COLOR, 2))
    check('D: №4 суточный (3 дня назад) — КРАСНЫЙ', page.evaluate(VAL_COLOR, 4) == RED,
          page.evaluate(VAL_COLOR, 4))
    check('E: №3 недельный (данные = закрытая неделя) — ЗЕЛЁНЫЙ',
          page.evaluate(VAL_COLOR, 3) == GREEN, page.evaluate(VAL_COLOR, 3))
    check('F: №11 недельный (данные неделей старее закрытой) — КРАСНЫЙ',
          page.evaluate(VAL_COLOR, 11) == RED, page.evaluate(VAL_COLOR, 11))
    check('G: №9 месячный (данные = прошлый месяц) — ЗЕЛЁНЫЙ',
          page.evaluate(VAL_COLOR, 9) == GREEN, page.evaluate(VAL_COLOR, 9))
    check('H: №5 «Ежемес.» (данные двумя месяцами старее) — КРАСНЫЙ',
          page.evaluate(VAL_COLOR, 5) == RED, page.evaluate(VAL_COLOR, 5))

    # --- подписи-диапазоны на карточках ---
    rng3 = 'за %02d.%02d–%02d.%02d.%d г.' % (W_START.day, W_START.month, W_END.day, W_END.month, W_END.year)
    rng9 = 'за %02d.%02d–%02d.%02d.%d г.' % (M_START.day, M_START.month, M_END.day, M_END.month, M_END.year)
    d2 = 'за %02d.%02d.%d г.' % (YESTERDAY.day, YESTERDAY.month, YESTERDAY.year)
    check('I: №3 подпись-диапазон «%s»' % rng3, page.evaluate(CARD_DATE, 3) == rng3,
          page.evaluate(CARD_DATE, 3))
    check('J: №9 подпись-диапазон «%s»' % rng9, page.evaluate(CARD_DATE, 9) == rng9,
          page.evaluate(CARD_DATE, 9))
    check('K: №2 суточная подпись «%s»' % d2, page.evaluate(CARD_DATE, 2) == d2,
          page.evaluate(CARD_DATE, 2))

    # --- детальная карточка №3: диапазон + хронология ---
    page.evaluate("FlowmeterData.openDetail(3)")
    page.wait_for_timeout(900)
    det = page.evaluate("(document.querySelector('.flow-detail-date-inline')||{}).textContent")
    check('L: детальная — «Последние показания %s»' % rng3, det == rng3, det)
    arch_td = page.evaluate("""(function(){
        var el = document.querySelector('#flowArchiveContainer td.flow-archive-date-range');
        return el ? el.textContent.trim() : null;
    })""")
    exp_arch = '%02d.%02d–%02d.%02d.%d' % (W_START.day, W_START.month, W_END.day, W_END.month, W_END.year)
    check('M: хронология №3 — запись-диапазон «%s» (без бейджа нед/мес)' % exp_arch,
          arch_td is not None and arch_td.startswith(exp_arch) and arch_td.find('нед') == -1,
          arch_td)

    # --- форма №3: период двух дат, дефолт = закрытая неделя ---
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    check('N: №3 подписи «Период с» / «по»',
          page.evaluate("(document.getElementById('flowInputDateLabel')||{}).textContent") == 'Период с' and
          page.evaluate("(document.getElementById('flowInputDateEndLabel')||{}).textContent") == 'по')
    check('O: №3 дефолты = закрытая неделя %s … %s' % (iso(W_START), iso(W_END)),
          page.evaluate("document.getElementById('flowInputDate').value") == iso(W_START) and
          page.evaluate("document.getElementById('flowInputDateEnd').value") == iso(W_END),
          page.evaluate("document.getElementById('flowInputDate').value") + ' … ' +
          page.evaluate("document.getElementById('flowInputDateEnd').value"))
    check('P: №3 поле «по» видно',
          page.evaluate("document.getElementById('flowInputDateEndGroup').style.display") == '')
    page.evaluate("FlowmeterData.closeInput()")

    # --- форма №9: период = прошлый месяц ---
    page.evaluate("FlowmeterData.openDetail(9)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    check('Q: №9 дефолты = прошлый месяц %s … %s' % (iso(M_START), iso(M_END)),
          page.evaluate("document.getElementById('flowInputDate').value") == iso(M_START) and
          page.evaluate("document.getElementById('flowInputDateEnd').value") == iso(M_END),
          page.evaluate("document.getElementById('flowInputDate').value") + ' … ' +
          page.evaluate("document.getElementById('flowInputDateEnd').value"))
    page.evaluate("FlowmeterData.closeInput()")

    # --- форма №2: суточная — одна дата, поля периода скрыты ---
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    check('R: №2 суточная — одна дата «вчера», «по» скрыто',
          page.evaluate("(document.getElementById('flowInputDateLabel')||{}).textContent") == 'Дата за предыдущие сутки' and
          page.evaluate("document.getElementById('flowInputDate').value") == iso(YESTERDAY) and
          page.evaluate("document.getElementById('flowInputDateEndGroup').style.display") == 'none')
    page.evaluate("FlowmeterData.closeInput()")

    # --- реальный ввод №11 (красный): период закрытой недели уходит на сервер ---
    page.evaluate("FlowmeterData.openDetail(11)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '105240,0')
    page.click('.flow-input-submit')
    page.wait_for_timeout(1800)
    cap = CAPTURED[-1] if CAPTURED else None
    check('S: №11 payload: datePrev/dateCurr = границы закрытой недели',
          cap is not None and cap.get('datePrev') == mdy(W_START) and cap.get('dateCurr') == mdy(W_END),
          json.dumps(cap, ensure_ascii=False)[:200] if cap else None)
    check('T: №11 после ввода — ЗЕЛЁНЫЙ (данные закрытой недели)',
          page.evaluate(VAL_COLOR, 11) == GREEN, page.evaluate(VAL_COLOR, 11))
    check('U: №11 подпись-диапазон на карточке', page.evaluate(CARD_DATE, 11) == rng3,
          page.evaluate(CARD_DATE, 11))
    n_out = page.evaluate("FlowmeterData._outboxCount()")
    check('V: outbox пуст (доставлено)', n_out == 0, n_out)

    # --- инвертированные даты: hard-отказ ---
    page.evaluate("FlowmeterData.openDetail(3)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.evaluate("document.getElementById('flowInputDate').value = '%s'" % iso(W_END))
    page.evaluate("document.getElementById('flowInputDateEnd').value = '%s'" % iso(W_START))
    page.fill('#flowInputField', '381500,0')
    page.click('.flow-input-submit')
    page.wait_for_timeout(900)
    check('W: инвертированные даты — запись НЕ ушла (outbox пуст)',
          page.evaluate("FlowmeterData._outboxCount()") == 0)
    check('X: тост «Дата конца периода раньше даты начала»',
          page.evaluate("(function(){var t=document.querySelector('.ki-toast,.toast,#toast');return t?t.textContent:'';})()").find('раньше даты начала') != -1 or
          page.evaluate("document.getElementById('flowInputSheet').classList.contains('active')"))
    page.evaluate("FlowmeterData.closeInput()")

    # --- правка №3 (окно 1 ч): предзаполнение датами записи ---
    page.evaluate("FlowmeterData.openDetail(3)")
    page.wait_for_timeout(400)
    page.evaluate("FlowmeterData.openInput(true)")
    page.wait_for_timeout(400)
    check('Y: правка №3 — поля = даты записи (%s … %s)' % (iso(W_START), iso(W_END)),
          page.evaluate("document.getElementById('flowInputDate').value") == iso(W_START) and
          page.evaluate("document.getElementById('flowInputDateEnd').value") == iso(W_END),
          page.evaluate("document.getElementById('flowInputDate').value") + ' … ' +
          page.evaluate("document.getElementById('flowInputDateEnd').value"))
    check('Z: правка — заголовок содержит «изменить»',
          page.evaluate("(document.getElementById('flowInputTitle')||{}).textContent").find('изменить') != -1)
    page.evaluate("FlowmeterData.closeInput()")
    page.screenshot(path='scripts/task368-proof-desktop.png')
    check('AA: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема =================
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t368-c');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('flowmeter-data')")
    page3.wait_for_timeout(1500)
    RED_L = 'rgb(232, 35, 10)'
    GREEN_L = 'rgb(90, 184, 112)'
    check('AB: светлая — №3 зелёный (диапазон жив)',
          page3.evaluate(VAL_COLOR, 3) == GREEN_L and page3.evaluate(CARD_DATE, 3) == rng3,
          page3.evaluate(VAL_COLOR, 3))
    check('AC: светлая — №5 «Ежемес.» красный читаем (№11 в контексте 1 уже ввели)',
          page3.evaluate(VAL_COLOR, 5) == RED_L, page3.evaluate(VAL_COLOR, 5))
    page3.screenshot(path='scripts/task368-proof-light.png')
    check('AD: светлая — 0 JS-ошибок', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 3: мобайл 375, тёмная =================
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t368-b');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('flowmeter-data')")
    page2.wait_for_timeout(1500)
    check('AE: мобайл — список жив (7 карточек)',
          page2.evaluate("document.querySelectorAll('.flow-card').length") == 7)
    check('AF: мобайл — №3 зелёный с диапазоном',
          page2.evaluate(VAL_COLOR, 3) == GREEN and page2.evaluate(CARD_DATE, 3) == rng3)
    page2.evaluate("FlowmeterData.openDetail(3)")
    page2.wait_for_timeout(600)
    page2.evaluate("FlowmeterData.openInput(false)")
    page2.wait_for_timeout(600)
    check('AG: мобайл — форма №3: оба поля дат на экране',
          page2.evaluate("document.getElementById('flowInputDate').value") == iso(W_START) and
          page2.evaluate("document.getElementById('flowInputDateEnd').value") == iso(W_END) and
          page2.evaluate("document.getElementById('flowInputDateEndGroup').style.display") == '')
    page2.evaluate("FlowmeterData.closeInput()")
    page2.screenshot(path='scripts/task368-proof-mobile.png')
    check('AH: мобайл — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
