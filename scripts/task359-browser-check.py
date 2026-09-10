#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 359: browser-check — красный «пора вводить» ЯРЧЕ + шрифт крупнее.
#
# Замечание пользователя: «Красный цвет показаний по периодам сделай
# ярче, а шрифт немного больше, чтобы он лучше привлекал внимание».
#
# Проверяем в реальном рендере карточек (мок-сервер, детерминированные
# даты: один расходомер «пора» (данные 3 дня назад), второй «свежий»
# (данные сегодня) — цвет/шрифт не зависят от реальных часов):
#   1. ТЁМНАЯ тема: due = #ff5c47 (rgb(255,92,71)), 18px, 800;
#      свежий = #5ab870 (rgb(90,184,112)), 16px, 700 (не тронут).
#   2. СВЕТЛАЯ тема: due = #e8230a (rgb(232,35,10)), 18px, 800.
#   3. 0 JS-ошибок; скриншоты-пруфы обеих тем.
#
# Правка показаний в окне 1 ч (сервер, .gs) проверяется VM-тестами
# test-task359.js — браузеру недоступен Apps Script.

import json
import datetime
from playwright.sync_api import sync_playwright

PORT = 8959
BASE = 'http://127.0.0.1:%d' % PORT

UA_DESKTOP = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36')

ROLE = 'КИП ИОС дежурный'
EMAIL = 'user@test.local'

TODAY = datetime.date(2026, 9, 10)          # фиксированная вселенная мока
STALE = TODAY - datetime.timedelta(days=3)  # «пора вводить» при любом часе


def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)


METERS = [
    {   # id=2 — данные 3 дня назад → КРАСНЫЙ «пора вводить»
        'id': 2, 'hoz': 'Хозрасчёт №2', 'param': 'Расход пара на ТЭЦ',
        'unit': 'т', 'period': 'Ежедневно',
        'prev': 90.0, 'curr': 91.0,
        'datePrev': mdy(STALE - datetime.timedelta(days=1)), 'dateCurr': mdy(STALE),
        'temp': 55.0, 'gcal': None,
        'modRole': ROLE, 'modName': 'user@test.local',
        'modDisplayName': 'Оператор', 'modTimestamp': '2026-09-07T08:00:00.000Z'
    },
    {   # id=3 — данные сегодня → зелёный (обычный)
        'id': 3, 'hoz': 'Хозрасчёт №3', 'param': 'Расход сетевой воды',
        'unit': 'м³', 'period': 'Ежедневно',
        'prev': 120.0, 'curr': 121.5,
        'datePrev': mdy(TODAY - datetime.timedelta(days=1)), 'dateCurr': mdy(TODAY),
        'temp': 61.0, 'gcal': None,
        'modRole': ROLE, 'modName': 'user@test.local',
        'modDisplayName': 'Оператор', 'modTimestamp': '2026-09-10T08:00:00.000Z'
    }
]

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((ok, name, detail))
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                           (' — ' + detail) if detail and not ok else ''))


def mock_response(action):
    if action == 'sendOTP':
        return {'ok': True, 'data': {'sent': True}}
    if action == 'verifyOTP':
        return {'ok': True, 'data': {'token': 't359-desk', 'role': ROLE,
                                     'userId': 7, 'email': EMAIL}}
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 7, 'email': EMAIL, 'role': ROLE}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': ROLE, 'found': True,
                                     'permissions': {'flowmeter.view': True,
                                                     'flowmeter.input': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': [dict(m) for m in METERS],
                                     'serverTime': '2026-09-10T08:00:00.000Z'}}
    if action == 'flowmeter.getRecentAllMeters':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.updateReading':
        return {'ok': True, 'data': {'id': 2}}
    return {'ok': False, 'error': 'Unknown action: ' + action}


def route_all(ctx):
    def handle(route, request):
        url = request.url
        action = 'unknown'
        for part in url.split('?')[1].split('&') if '?' in url else []:
            if part.startswith('action='):
                action = part.split('=')[1]
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (t359)')
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


def val_style(page, meter_id):
    """Вычисленный стиль .flow-summary-val карточки meter_id."""
    return page.evaluate(
        "(() => { const card = document.querySelector("
        "'.flow-card[data-flow-id=\\\"%s\\\"]');"
        "const el = card && card.querySelector('.flow-summary-val');"
        "if (!el) return null; const cs = getComputedStyle(el);"
        "return {color: cs.color, fontSize: cs.fontSize,"
        "fontWeight: cs.fontWeight, cls: el.className};})()" % meter_id)


def js_get_overdue(page, meter_id):
    return page.evaluate(
        "(() => { const m = (FlowmeterData._METERS || []).filter("
        "x => String(x.id) === '%s')[0];"
        "return m ? !!FlowmeterData._isOverdue(m, null) : null; })()" % meter_id)


def run_theme(browser, theme):
    print('=== Тема: %s ===' % theme)
    errors = []
    ctx = browser.new_context(user_agent=UA_DESKTOP,
                              viewport={'width': 1280, 'height': 900})
    route_all(ctx)
    page = ctx.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    # Тема ДО загрузки (префикс kip8test: — изоляция localStorage)
    page.add_init_script("try{localStorage.setItem('kip8test:app-theme','%s')}catch(e){}" % theme)
    page.goto(BASE + '/index.html')
    page.wait_for_timeout(1500)
    ui_login(page)
    open_flowmeter_section(page)

    attr = page.evaluate("document.documentElement.getAttribute('data-theme')")
    check('тема применена (%s)' % theme, attr == theme, 'фактически: %r' % attr)

    check('id=2 «пора вводить» (_isOverdue)', js_get_overdue(page, 2) is True)
    check('id=3 свежий (_isOverdue=false)', js_get_overdue(page, 3) is False)

    due = val_style(page, 2)
    fresh = val_style(page, 3)
    expected_due = ('rgb(255, 92, 71)' if theme == 'dark' else 'rgb(232, 35, 10)')
    check('id=2: класс flow-summary-val-due',
          due and 'flow-summary-val-due' in due['cls'], 'cls: %r' % (due or {}).get('cls'))
    check('id=2: цвет ЯРЧЕ (%s)' % expected_due,
          due and due['color'] == expected_due, 'фактически: %r' % (due or {}).get('color'))
    check('id=2: шрифт крупнее (18px)', due and due['fontSize'] == '18px',
          'фактически: %r' % (due or {}).get('fontSize'))
    check('id=2: жирнее (800)', due and due['fontWeight'] == '800',
          'фактически: %r' % (due or {}).get('fontWeight'))
    check('id=3: зелёный не тронут (16px/700/#5ab870)',
          fresh and fresh['fontSize'] == '16px' and fresh['fontWeight'] == '700'
          and fresh['color'] == 'rgb(90, 184, 112)',
          'фактически: %r' % fresh)

    page.screenshot(path='scripts/task359-proof-%s.png' % theme)
    check('тема %s: 0 JS-ошибок' % theme, len(errors) == 0, '; '.join(errors[:3]))
    ctx.close()


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

    with sync_playwright() as p:
        browser = p.chromium.launch()
        run_theme(browser, 'dark')
        run_theme(browser, 'light')
        browser.close()
    httpd.shutdown()

    fails = sum(1 for ok, _, _ in RESULTS if not ok)
    print('\nИТОГО: %d/%d проверок, ошибок %d' % (
        len(RESULTS) - fails, len(RESULTS), fails))
    if fails:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
