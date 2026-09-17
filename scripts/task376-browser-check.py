#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 376: browser-check — заявка пользователя: «при вводе новых данных
# расходов, в последнем расходомере №12 введённые новые данные записались
# на сервер в hozraschet_meters, а в архиве на hozraschet_archive не
# записались, в чём может быть причина, проверь».
# Контекст (десктоп 1280 тёмная, Админ — РАСХОДОМЕРЫ):
#   A-B  загрузка, список отрисован.
#   C-E  ДЫРА №12 (главный сценарий): meters уже содержит показание,
#        архив ПУСТ — запись в outbox при флаше НЕ считается доставленной
#        и УХОДИТ повторно (раньше удалялась по meters-совпадению —
#        строка архива терялась навсегда).
#   F-G  подтверждение по архиву: строка архива на месте → повтор НЕ
#        отправляется (дубль не создаётся).
#   H-L  сервер вернул archive_write_failed (meters записан, архив нет):
#        интерактивный ввод → запись ОСТАЁТСЯ в outbox (pending-цвет),
#        тост честный; авто-ретрай через 15 c доставляет запись и
#        вычищает outbox (самовосстановление без потери строки архива).
#   M-N  регресс: обычный ввод работает; 0 JS-ошибок.
# Порт 8979.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8979
TODAY = datetime.date.today()
YESTERDAY = TODAY - datetime.timedelta(days=1)
D3 = TODAY - datetime.timedelta(days=3)

def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)

def meter(i, hoz, param, dprev, dcurr, prev, curr, period):
    return {'id': i, 'hoz': hoz, 'param': param, 'datePrev': mdy(dprev),
            'dateCurr': mdy(dcurr), 'prev': prev, 'curr': curr, 'unit': 'м³',
            'temp': None, 'gcal': None, 'period': period,
            'modRole': 'Админ', 'modName': 'user@test.local',
            'modDisplayName': 'user@test.local',
            'modTimestamp': datetime.datetime.now().isoformat()}

# meters №4 «уже записан на сервере» (сценарий дыры): curr/dateCurr
# совпадают с записью outbox ниже — как после старого бага №12
MOCK_METERS = [
    meter(2, 'Хозрасчёт №2', 'Расход воды речной в корпус 114',
          YESTERDAY, YESTERDAY, 383291.0, 383291.0, 'Ежедневно'),
    meter(4, 'Хозрасчёт №4', 'Расход воздуха технологического в корпус 114',
          YESTERDAY, YESTERDAY, 679700.0, 680000.0, 'Ежедневно'),
]

STATE = {
    'archive': [],          # строки hozraschet_archive (записи «сутки»)
    'update_fails': False,  # сервер: архив падает → archive_write_failed
}

CAPTURED = []

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': json.loads(json.dumps(MOCK_METERS))}}
    if action == 'flowmeter.getValidationRules':
        return {'ok': True, 'data': {'rules': []}}
    if action == 'flowmeter.getRecentAllMeters':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.archive':
        # ответ реального listArchive: записи новейшими первыми
        return {'ok': True, 'data': {'records': list(reversed(STATE['archive']))}}
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
        if STATE['update_fails']:
            # честный сервер Task 376: meters УЖЕ записан (выше), архив не удался
            return {'ok': False, 'error': 'archive_write_failed',
                    'message': 'Показания сохранены, но запись в архив временно '
                               'не удалась — она будет отправлена повторно автоматически'}
        # архивная строка дописана (дедуп сервера опущен — не нужен для чека)
        STATE['archive'].append({
            'meterId': pid, 'entryType': 'сутки',
            'dateCurr': body.get('dateCurr', ''), 'curr': body.get('curr', 0)})
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

def setup_ctx(browser, viewport, token, theme='dark'):
    ctx = browser.new_context(viewport=viewport)
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t376)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','%s');" % token +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ============ Контекст 1: расходомеры — дыра №12 ============
    ctx, page, js_errors = setup_ctx(browser, {'width': 1280, 'height': 800}, 'bc-t376-a')
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1500)
    check('B: список расходомеров отрисован',
          page.evaluate("document.querySelectorAll('.flow-card').length") >= 2)

    # --- ДЫРА №12: meters записан, архива НЕТ → повторная доставка ---
    page.evaluate("""(function(){
        FlowmeterData._outboxAdd({ cid: 't376-hole', kind: 'day', state: 'retry',
            payload: { id: 4, prev: 679700, curr: 680000, datePrev: '%s',
                       dateCurr: '%s', temp: null, isEdit: false } });
        return FlowmeterData._outboxCount();
    })""" % (mdy(YESTERDAY), mdy(YESTERDAY)))
    page.wait_for_timeout(300)
    check('C: запись «дыры» засеяна (meters совпадает, архив пуст)',
          page.evaluate("FlowmeterData._outboxCount()") == 1)
    page.evaluate("FlowmeterData._flushOutbox('init')")
    page.wait_for_timeout(2500)
    c4 = [c for c in CAPTURED if c.get('id') == 4]
    check('D: ДЫРА ЗАКРЫТА — запись доставлена повторно (updateReading вызван)',
          len(c4) == 1 and c4[0].get('prev') == 679700 and c4[0].get('curr') == 680000,
          [json.dumps(c, ensure_ascii=False)[:120] for c in c4])
    check('E: outbox пуст после доставки, строка архива создана',
          page.evaluate("FlowmeterData._outboxCount()") == 0 and len(STATE['archive']) == 1,
          (page.evaluate("FlowmeterData._outboxCount()"), len(STATE['archive'])))

    # --- подтверждение по архиву: строка ЕСТЬ → повтор НЕ уходит ---
    page.evaluate("""(function(){
        FlowmeterData._outboxAdd({ cid: 't376-arch', kind: 'day', state: 'retry',
            payload: { id: 4, prev: 679700, curr: 680000, datePrev: '%s',
                       dateCurr: '%s', temp: null, isEdit: false } });
        return FlowmeterData._outboxCount();
    })""" % (mdy(YESTERDAY), mdy(YESTERDAY)))
    page.wait_for_timeout(300)
    page.evaluate("FlowmeterData._flushOutbox('init')")
    page.wait_for_timeout(2500)
    c4b = [c for c in CAPTURED if c.get('id') == 4]
    check('F: строка архива на месте → дубль НЕ отправляется (всего 1 для №4)',
          len(c4b) == 1, len(c4b))
    check('G: outbox вычищен дедупом по архиву',
          page.evaluate("FlowmeterData._outboxCount()") == 0)

    # --- сервер вернул archive_write_failed: интерактивный ввод №2 ---
    STATE['update_fails'] = True
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383400')
    page.click('.flow-input-submit')
    page.wait_for_timeout(2500)
    c2 = [c for c in CAPTURED if c.get('id') == 2]
    check('H: ввод ушёл на сервер (meters записан, архив «упал»)',
          len(c2) == 1 and c2[0].get('curr') == 383400,
          json.dumps(c2[0], ensure_ascii=False)[:140] if c2 else None)
    n_out = page.evaluate("FlowmeterData._outboxCount()")
    st = page.evaluate("(FlowmeterData._outboxLoad()[0]||{}).state")
    check('I: запись ОСТАЛАСЬ в outbox (ждёт повтора), state=retry',
          n_out == 1 and st == 'retry', (n_out, st))
    toast = page.evaluate("(document.getElementById('toastMessage')||{}).textContent")
    check('J: честный тост «запись в архив не удалась — отправим повторно»',
          bool(toast) and 'запись в архив не удалась' in toast and 'повторно' in toast, toast)
    pend = page.evaluate("document.querySelectorAll('.flow-summary-val-pending').length")
    check('K: значение карточки — pending-цвет (жёлто-оранжевый, Task 367/370)',
          pend >= 1, pend)

    # --- авто-ретрай через 15 c доставляет запись (самовосстановление) ---
    STATE['update_fails'] = False
    page.wait_for_timeout(16000)
    c2b = [c for c in CAPTURED if c.get('id') == 2]
    check('L: авто-ретрай доставил запись (2-я отправка для №2)',
          len(c2b) == 2 and c2b[1].get('curr') == 383400, len(c2b))
    check('M: outbox пуст, строка архива №2 создана',
          page.evaluate("FlowmeterData._outboxCount()") == 0 and
          any(r.get('meterId') == 2 for r in STATE['archive']),
          len(STATE['archive']))

    # --- регресс: обычный ввод работает ---
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383500')
    page.click('.flow-input-submit')
    page.wait_for_timeout(2000)
    c2c = [c for c in CAPTURED if c.get('id') == 2]
    check('N: регресс — обычный ввод работает (3-я отправка, prev=383400)',
          len(c2c) == 3 and c2c[2].get('prev') == 383400 and c2c[2].get('curr') == 383500,
          len(c2c))
    check('O: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='scripts/task376-proof-flow.png', full_page=True)
    ctx.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
