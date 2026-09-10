#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 358: browser-check — гарантированная доставка показаний
# расходомеров (outbox). Заявка: пользователь вводит показания, жмёт
# «Сохранить», быстро уходит к следующей карточке или закрывает
# приложение — введённое не доходит до сервера.
#
# Сценарии:
#   1. ОФЛАЙН-ВВОД (десктоп): сервер недоступен (route.abort на
#      getRecentAllMeters + updateReading) → «Сохранить» → тост
#      «Нет связи… будут отправлены автоматически», запись в outbox
#      (localStorage, префикс kip8test:), баннер «ждут отправки: 1».
#      Сеть возвращается (online-событие) → флаш: flowmeter.list
#      (дедуп) → updateReading доставлен → outbox пуст, тост
#      «отправлены: 1», баннера нет.
#   2. BEACON «ПОСЛЕДНЕГО ШАНСА» + ДЕДУП: офлайн-ввод → pagehide с
#      поднятой сетью → POST beacon на сервер (перехвачен), запись
#      ОСТАЛАСЬ в outbox (ответа нет) → «следующий запуск»: сервер
#      уже содержит показание (beacon дошёл) → перезагрузка → флаш
#      → запись снята ДЕДУПОМ, updateReading НЕ вызывался (архив
#      без дубля).
#   3. ПЕРЕ-ПОКАЗ АНОМАЛИИ: запись «awaiting-confirm» (пользователь
#      ушёл раньше решения) → следующий запуск → модалка аномалии
#      показана снова → «Всё равно сохранить» → доставка.
#   + 0 JS-ошибок во всех контекстах; скриншоты-пруфы.

import datetime
import json
from playwright.sync_api import sync_playwright

PORT = 8951
BASE = 'http://127.0.0.1:%d' % PORT

UA_DESKTOP = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36')

ROLE = 'КИП ИОС дежурный'
EMAIL = 'user@test.local'

# --- состояние мок-сервера ---
STATE = {
    'offline': False,        # abort на сетевые запросы расходомеров
    'meter': {               # текущее состояние meters-строки id=2
        'id': 2, 'hoz': 'Хозрасчёт №2', 'param': 'Расход пара на ТЭЦ',
        'unit': 'т', 'period': 'Ежедневно',
        'prev': 90.0, 'curr': 91.0,
        'datePrev': '9/7/2026', 'dateCurr': '9/8/2026',
        'temp': None, 'gcal': None,
        'modRole': ROLE, 'modName': 'other@plant.local',
        'modDisplayName': 'Прежний оператор',
        'modTimestamp': '2026-09-08T07:00:00.000Z'
    }
}

REQUESTS = []
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((ok, name, detail))
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                           (' — ' + detail) if detail and not ok else ''))


def mock_response(action):
    if action == 'sendOTP':
        return {'ok': True, 'data': {'sent': True}}
    if action == 'verifyOTP':
        return {'ok': True, 'data': {'token': 't358-desk', 'role': ROLE,
                                     'userId': 7, 'email': EMAIL}}
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 7, 'email': EMAIL, 'role': ROLE}}
    if action == 'getMyAccess':
        # матрица прав: flowmeter.view открывает раздел, flowmeter.input
        # — право ввода показаний (Task 296/295)
        return {'ok': True, 'data': {'role': ROLE, 'found': True,
                                     'permissions': {'flowmeter.view': True,
                                                     'flowmeter.input': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': [dict(STATE['meter'])],
                                     'serverTime': '2026-09-10T08:00:00.000Z'}}
    if action == 'flowmeter.getRecentAllMeters':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.updateReading':
        return {'ok': True, 'data': {'id': 2}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records': []}}
    return {'ok': False, 'error': 'Unknown action: ' + action}


def route_all(ctx):
    def handle(route, request):
        url = request.url
        action = 'unknown'
        for part in url.split('?')[1].split('&') if '?' in url else []:
            if part.startswith('action='):
                action = part.split('=')[1]
        try:
            payload = json.loads(request.post_data or '{}')
        except Exception:
            payload = {}
        if STATE['offline'] and action in ('flowmeter.getRecentAllMeters',
                                           'flowmeter.updateReading',
                                           'flowmeter.updatePeriodReading'):
            route.abort()
            return
        REQUESTS.append({'action': action, 'payload': payload,
                         'beacon': 'Beacon' in (request.headers or {}).get('sec-fetch-metadata-destination', '')})
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (t358)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


def ui_login(page, email=EMAIL, code='1'):
    page.evaluate("KipAuth._showLoginScreen()")
    page.wait_for_selector('#loginScreen', state='visible')
    page.fill('#authEmail', email)
    page.click('#authSendBtn')
    page.wait_for_selector('#authStep2.active', timeout=5000)
    for i in range(1, 7):
        page.fill('#otp%d' % i, code)
    page.click('#authVerifyBtn')
    page.wait_for_timeout(800)


def open_flowmeter_section(page):
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1200)


def outbox(page):
    raw = page.evaluate("localStorage.getItem('kip8_flow_outbox_v1')")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return None


def enter_reading(page, value):
    """Открыть карточку id=2 → «Ввести показания» → значение → Сохранить."""
    page.evaluate("FlowmeterData.openDetail(2, false)")
    page.wait_for_timeout(400)
    page.click('.flow-input-btn')
    page.wait_for_selector('#flowInputSheet.active, #flowInputSheet', timeout=4000)
    page.fill('#flowInputField', value)
    page.click('.flow-input-submit')
    page.wait_for_timeout(2500)   # 2 попытки fetch (retry 1 c) + откаты


def main():
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    import os
    os.chdir('/home/z/my-project/kip8test')

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass
    httpd = HTTPServer(('127.0.0.1', PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ======================================================
        print('=== 1. ОФЛАЙН-ВВОД → авто-флаш при online ===')
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_DESKTOP,
                                  viewport={'width': 1280, 'height': 800})
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(1500)
        ui_login(page)
        check('вход выполнен', page.evaluate("localStorage.getItem('kip8_session_token')") == 't358-desk')

        open_flowmeter_section(page)
        STATE['offline'] = True
        enter_reading(page, '95')
        # Промах сети ×2 (retry KipAuth) → catch → запись в outbox
        ent = outbox(page)
        check('офлайн: запись в outbox (не потеряна)', len(ent) == 1,
              'фактически: %r' % ent)
        if ent:
            check('офлайн: kind=day, состояние retry', ent[0]['kind'] == 'day' and ent[0]['state'] == 'retry',
                    'фактически: %r' % ent[0].get('state'))
            check('офлайн: payload содержит curr=95', ent[0]['payload'].get('curr') == 95)
        toast = page.evaluate("document.getElementById('toastMessage').textContent")
        check('офлайн: тост «будут отправлены автоматически»',
              'автоматически' in toast and 'сохранены' in toast, 'текст: %r' % toast[:100])
        page.screenshot(path='scripts/task358-proof-offline-toast.png')

        # Баннер: перерисовать список (как реальный возврат к списку)
        page.evaluate("FlowmeterData.renderList()")
        page.wait_for_timeout(300)
        banner = page.evaluate("document.querySelector('.flow-outbox-banner') ? document.querySelector('.flow-outbox-banner').textContent : ''")
        check('офлайн: баннер «ждут отправки: 1»', 'ждут отправки: 1' in banner, 'текст: %r' % banner[:100])
        page.screenshot(path='scripts/task358-proof-offline-banner.png')

        # Сеть вернулась → online → флаш
        upd_before = len([r for r in REQUESTS if r['action'] == 'flowmeter.updateReading'])
        STATE['offline'] = False
        page.evaluate("window.dispatchEvent(new Event('online'))")
        page.wait_for_timeout(2000)
        ent = outbox(page)
        check('online: outbox пуст после флаша', len(ent) == 0, 'фактически: %r' % ent)
        upd_after = [r for r in REQUESTS if r['action'] == 'flowmeter.updateReading']
        check('online: updateReading доставлен', len(upd_after) > upd_before,
              'до=%d после=%d' % (upd_before, len(upd_after)))
        if upd_after:
            check('online: payload корректен (curr=95)',
                  str(upd_after[-1]['payload'].get('curr')) == '95',
                  'payload: %r' % upd_after[-1]['payload'])
        toast = page.evaluate("document.getElementById('toastMessage').textContent")
        check('online: тост «отправлены: 1»', 'отправлены: 1' in toast, 'текст: %r' % toast[:100])
        page.evaluate("FlowmeterData.renderList()")
        page.wait_for_timeout(200)
        check('online: баннер исчез',
              page.evaluate("!document.querySelector('.flow-outbox-banner')"))
        page.screenshot(path='scripts/task358-proof-online-delivered.png')
        check('контекст 1: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

        # ======================================================
        print('=== 2. BEACON при закрытии + ДЕДУП следующего запуска ===')
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_DESKTOP,
                                  viewport={'width': 1280, 'height': 800})
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(1500)
        ui_login(page)
        open_flowmeter_section(page)

        STATE['offline'] = True
        enter_reading(page, '96')
        ent = outbox(page)
        check('офлайн №2: запись в outbox', len(ent) == 1 and ent[0]['payload'].get('curr') == 96,
              'фактически: %r' % ent)

        # Пользователь «закрывает приложение»: сеть уже поднята,
        # pagehide → sendBeacon последнего шанса
        STATE['offline'] = False
        beacons_before = len(REQUESTS)
        page.evaluate("window.dispatchEvent(new Event('pagehide'))")
        page.wait_for_timeout(1200)
        ent = outbox(page)
        check('beacon: запись ОСТАЛАСЬ в outbox (ответа нет, ждём сверки)',
              len(ent) == 1, 'фактически: %r' % ent)
        if ent:
            check('beacon: метка времени зафиксирована', bool(ent[0].get('beacon')))
        new_posts = REQUESTS[beacons_before:]
        upd_beacon = [r for r in new_posts if r['action'] == 'flowmeter.updateReading']
        check('beacon: POST на сервер «последнего шанса» отправлен', len(upd_beacon) >= 1,
              'перехвачено: %r' % [r['action'] for r in new_posts])
        if upd_beacon:
            check('beacon: payload содержит токен и curr=96',
                  upd_beacon[-1]['payload'].get('token') == 't358-desk' and
                  str(upd_beacon[-1]['payload'].get('curr')) == '96',
                  'payload: %r' % upd_beacon[-1]['payload'])

        # «Следующий запуск»: сервер УЖЕ содержит показание (beacon дошёл)
        STATE['meter'].update({'curr': 96.0, 'dateCurr': ent[0]['payload'].get('dateCurr', '9/9/2026')})
        upd_marker = len(REQUESTS)
        page.reload()
        page.wait_for_timeout(2000)
        open_flowmeter_section(page)
        page.wait_for_timeout(2000)
        ent = outbox(page)
        check('перезапуск: запись снята ДЕДУПОМ (beacon дошёл)', len(ent) == 0,
              'фактически: %r' % ent)
        upd_calls = [r for r in REQUESTS[upd_marker:] if r['action'] == 'flowmeter.updateReading']
        check('перезапуск: повторная отправка НЕ выполнялась (архив без дубля)',
              len(upd_calls) == 0, 'вызовы: %r' % [r['action'] for r in REQUESTS[upd_marker:]])
        check('контекст 2: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

        # ======================================================
        print('=== 3. ПЕРЕ-ПОКАЗ аномалии (быстрый уход с карточки) ===')
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_DESKTOP,
                                  viewport={'width': 1280, 'height': 800})
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(1500)
        ui_login(page)
        # Пользователь ввёл показания, валидация вернула soft-confirm,
        # он ушёл к следующей карточке раньше решения → запись «застряла»
        seed = [{
            'cid': 'fl-debug-seed', 'kind': 'day', 'ts': 1770000000000,
            'state': 'awaiting-confirm',
            'codes': ['JUMP_HIGH: расход 4.00 > max_cons ×3=1.50'],
            'isEdit': False,
            'payload': {'id': 2, 'prev': 91.0, 'curr': 95.0,
                        'datePrev': '9/8/2026', 'dateCurr': '9/9/2026',
                        'temp': None, 'isEdit': False}
        }]
        page.evaluate("s => localStorage.setItem('kip8_flow_outbox_v1', s)",
                      json.dumps(seed, ensure_ascii=False))
        open_flowmeter_section(page)
        page.wait_for_timeout(2500)   # флаш → пере-показ модалки
        modal = page.evaluate("!!document.getElementById('flowAnomalyModal')")
        check('перезапуск: модалка аномалии пере-показана', modal)
        page.screenshot(path='scripts/task358-proof-anomaly-reshow.png')
        if modal:
            # «Всё равно сохранить» → доставка
            btn = page.evaluate("""(function(){
                var m = document.getElementById('flowAnomalyModal');
                var btns = m.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.indexOf('сохранить') !== -1 ||
                        btns[i].textContent.indexOf('Сохранить') !== -1) return i;
                }
                return -1;
            })()""")
            check('модалка: кнопка подтверждения найдена', btn >= 0)
            if btn >= 0:
                page.evaluate("""(function(){
                    var m = document.getElementById('flowAnomalyModal');
                    m.querySelectorAll('button')[%d].click();
                })()""" % btn)
                page.wait_for_timeout(2000)
                ent = outbox(page)
                check('подтверждение: запись доставлена и убрана', len(ent) == 0,
                      'фактически: %r' % ent)
                upd = [r for r in REQUESTS if r['action'] == 'flowmeter.updateReading']
                check('подтверждение: updateReading ушёл на сервер', len(upd) >= 1)
        check('контекст 3: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

        browser.close()

    fails = sum(1 for ok, _, _ in RESULTS if not ok)
    print('=' * 60)
    print('ИТОГ: %d/%d проверок пройдено' % (len(RESULTS) - fails, len(RESULTS)))
    if fails:
        print('ПРОВАЛЕНО:')
        for ok, name, d in RESULTS:
            if not ok:
                print('  ✗ %s — %s' % (name, d))
    return fails


if __name__ == '__main__':
    import sys
    sys.exit(1 if main() else 0)
