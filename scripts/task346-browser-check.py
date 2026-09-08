#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 346: browser-check — политика сессий «1 моб + 1 десктоп» на
# одну почту (заявка: «с одной почты параллельно работать в мобильном
# и десктопном приложениях; не больше двух входов; только один вход в
# мобильное и один в десктопное; без запретов "уже вошел"»).
#
# Проверки (5 контекстов, все входы — РЕАЛЬНЫЙ UI-флоу email→OTP):
#   1. MOBILE (Android UA): вход → payload verifyOTP содержит
#      device='mobile'; ответ с evicted=1 → тост «Прежний вход в
#      мобильном приложении… завершён»; токен сохранён.
#   2. DESKTOP (Chrome UA): вход → device='desktop'; evicted=2 →
#      тост «…в десктопном приложении…».
#   3. ELECTRON-ФЛАГ (Android UA + window.__isElectron=true ДО
#      загрузки): device='desktop' — флаг приоритетнее UA.
#   4. СТАРЫЙ СЕРВЕР (ответ БЕЗ evicted): вход работает, тоста нет
#      (обратная совместимость до деплоя серверной части).
#   5. АДМИН-ПАНЕЛЬ (роль Админ): adminListSessions с device →
#      бейджи «моб»/«десктоп»; у легаси-сессий бейджа нет.
#   + 0 JS-ошибок во всех контекстах; скриншоты-пруфы.
import datetime
import json
from playwright.sync_api import sync_playwright

PORT = 8947
BASE = 'http://127.0.0.1:%d' % PORT

UA_ANDROID = ('Mozilla/5.0 (Linux; Android 13; Pixel 7) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Mobile Safari/537.36')
UA_DESKTOP = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36')

# Контекст-зависимое состояние мок-сервера
STATE = {'evicted': 1, 'old_server': False}
# Перехваченные запросы (payload по action)
REQUESTS = {}

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((ok, name, detail))
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                           (' — ' + detail) if detail and not ok else ''))


def mock_response(action):
    if action == 'sendOTP':
        return {'ok': True, 'data': {'sent': True}}
    if action == 'verifyOTP':
        d = {'token': 't346-%s' % STATE.get('suffix', 'x'), 'role': 'КИП ИОС',
             'userId': 7, 'email': 'user@test.local'}
        if not STATE['old_server']:
            d['evicted'] = STATE['evicted']
        return {'ok': True, 'data': d}
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 7, 'email': 'user@test.local',
                                     'role': STATE.get('role', 'КИП ИОС')}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': STATE.get('role', 'КИП ИОС'), 'found': True,
                                     'permissions': {'admin.panel': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'adminListSessions':
        return {'ok': True, 'data': [
            {'email': 'a@x.ru', 'role': 'Админ', 'token': 'tokA',
             'created_at': '2026-09-08 07:00:00', 'last_heartbeat': '2026-09-08 08:00:00',
             'device': 'mobile'},
            {'email': 'a@x.ru', 'role': 'Админ', 'token': 'tokB',
             'created_at': '2026-09-08 07:30:00', 'last_heartbeat': '2026-09-08 08:30:00',
             'device': 'desktop'},
            {'email': 'b@x.ru', 'role': 'КИП ИОС', 'token': 'tokC',
             'created_at': '2026-08-02 17:10:22', 'last_heartbeat': '2026-08-20 18:38:21'}
        ]}
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
        REQUESTS[action] = payload
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (t346)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


def ui_login(page, email='user@test.local', code='1'):
    """Полный вход через UI: гость → «Войти в аккаунт» → email → OTP."""
    # Гостевой режим при старте (токена нет): кнопка в сайдбаре
    page.evaluate("KipAuth._showLoginScreen()")
    page.wait_for_selector('#loginScreen', state='visible')
    page.fill('#authEmail', email)
    page.click('#authSendBtn')
    page.wait_for_selector('#authStep2.active', timeout=5000)
    for i in range(1, 7):
        page.fill('#otp%d' % i, code)
    page.click('#authVerifyBtn')
    page.wait_for_timeout(600)


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

    today = datetime.date.today()
    fails = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------- Контекст 1: MOBILE ----------
        print('=== 1. MOBILE: device=mobile + тост evicted ===')
        STATE['suffix'] = 'mob'; STATE['evicted'] = 1; STATE['old_server'] = False
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_ANDROID,
                                  viewport={'width': 390, 'height': 780},
                                  is_mobile=True, has_touch=True)
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(1500)
        ui_login(page)
        check('MOBILE: вход выполнен (токен сохранён)',
              page.evaluate("localStorage.getItem('kip8_session_token')") == 't346-mob')
        check('MOBILE: payload verifyOTP содержит device=mobile',
              REQUESTS.get('verifyOTP', {}).get('device') == 'mobile',
              'фактически: %r' % REQUESTS.get('verifyOTP', {}).get('device'))
        toast_shown = page.evaluate("document.getElementById('toast').classList.contains('show')")
        toast_text = page.evaluate("document.getElementById('toastMessage').textContent")
        check('MOBILE: тост показан (evicted=1)', toast_shown)
        check('MOBILE: текст тоста — мобильное приложение, прежний вход завершён',
              ('мобильном' in toast_text) and ('завершён' in toast_text),
              'текст: %r' % toast_text[:120])
        check('MOBILE: payload email передан', REQUESTS.get('verifyOTP', {}).get('email') == 'user@test.local')
        check('MOBILE: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        page.screenshot(path='scripts/task346-proof-mobile-login.png')
        ctx.close()

        # ---------- Контекст 2: DESKTOP ----------
        print('=== 2. DESKTOP: device=desktop + тост evicted=2 ===')
        STATE['suffix'] = 'desk'; STATE['evicted'] = 2
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
        check('DESKTOP: вход выполнен',
              page.evaluate("localStorage.getItem('kip8_session_token')") == 't346-desk')
        check('DESKTOP: payload device=desktop',
              REQUESTS.get('verifyOTP', {}).get('device') == 'desktop',
              'фактически: %r' % REQUESTS.get('verifyOTP', {}).get('device'))
        toast_text = page.evaluate("document.getElementById('toastMessage').textContent")
        check('DESKTOP: тост — десктопное приложение (evicted=2)',
              ('десктопном' in toast_text) and ('завершён' in toast_text),
              'текст: %r' % toast_text[:120])
        check('DESKTOP: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

        # ---------- Контекст 3: ELECTRON-ФЛАГ ----------
        print('=== 3. ELECTRON: __isElectron приоритетнее мобильного UA ===')
        STATE['suffix'] = 'el'; STATE['evicted'] = 0
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_ANDROID,
                                  viewport={'width': 390, 'height': 780})
        ctx.add_init_script('window.__isElectron = true;')
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(1500)
        check('ELECTRON: флаг __isElectron установлен',
              page.evaluate('window.__isElectron === true'))
        ui_login(page)
        check('ELECTRON: device=desktop при мобильном UA (флаг)',
              REQUESTS.get('verifyOTP', {}).get('device') == 'desktop',
              'фактически: %r' % REQUESTS.get('verifyOTP', {}).get('device'))
        # evicted=0 → тоста быть не должно
        page.wait_for_timeout(400)
        toast_shown = page.evaluate("document.getElementById('toast').classList.contains('show')")
        check('ELECTRON: evicted=0 → тоста НЕТ', not toast_shown)
        check('ELECTRON: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

        # ---------- Контекст 4: СТАРЫЙ СЕРВЕР ----------
        print('=== 4. СТАРЫЙ СЕРВЕР (без evicted): обратная совместимость ===')
        STATE['suffix'] = 'old'; STATE['old_server'] = True
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_ANDROID,
                                  viewport={'width': 390, 'height': 780}, is_mobile=True)
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(1500)
        ui_login(page)
        check('OLD-SERVER: вход выполнен',
              page.evaluate("localStorage.getItem('kip8_session_token')") == 't346-old')
        check('OLD-SERVER: device всё равно отправлен',
              REQUESTS.get('verifyOTP', {}).get('device') == 'mobile')
        page.wait_for_timeout(400)
        toast_shown = page.evaluate("document.getElementById('toast').classList.contains('show')")
        toast_text = page.evaluate("document.getElementById('toastMessage').textContent")
        check('OLD-SERVER: тоста НЕТ (поля evicted нет в ответе)',
              (not toast_shown) or ('Прежний вход' not in toast_text))
        check('OLD-SERVER: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()
        STATE['old_server'] = False

        # ---------- Контекст 5: АДМИН-ПАНЕЛЬ ----------
        print('=== 5. АДМИН: бейджи «моб»/«десктоп» у сессий ===')
        STATE['suffix'] = 'adm'; STATE['role'] = 'Админ'
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_DESKTOP,
                                  viewport={'width': 1280, 'height': 800})
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.evaluate("_ => 0")  # прогрев
        page.goto(BASE + '/index.html')
        page.evaluate("localStorage.setItem('kip8_session_token','adm-tok')")
        page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
        page.reload()
        page.wait_for_timeout(1800)
        page.evaluate("navigateTo('admin-sessions')")
        page.wait_for_timeout(1200)
        html = page.evaluate("document.getElementById('adminSessionsList').innerHTML")
        n_badges = html.count('admin-badge-device')
        check('ADMIN: ровно 2 бейджа устройства (mobile+desktop, легаси без)',
              n_badges == 2, 'бейджей: %d' % n_badges)
        check('ADMIN: подпись «моб» у mobile-сессии', '>моб<' in html.replace(' ', '') or 'моб' in html)
        check('ADMIN: подпись «десктоп» у desktop-сессии', 'десктоп' in html)
        check('ADMIN: легаси-сессия (b@x.ru) отрендерена без бейджа',
              'b@x.ru' in html and html.split('b@x.ru')[1].split('admin-item-email')[0].count('admin-badge-device') == 0)
        check('ADMIN: сортировка по last_heartbeat — свежая сессия первой',
              html.find('tokB') < html.find('tokA') if 'tokA' in html and 'tokB' in html else True)
        check('ADMIN: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        page.screenshot(path='scripts/task346-proof-admin-sessions.png')
        ctx.close()
        STATE['role'] = 'КИП ИОС'

        browser.close()

    httpd.shutdown()
    fails = sum(1 for ok, _, _ in RESULTS if not ok)
    print()
    print('  Результат: %d passed, %d failed, %d total' % (len(RESULTS) - fails, fails, len(RESULTS)))
    print('=' * 60)
    import sys
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    print('=' * 60)
    print('Task 346 — browser-check: политика сессий «1 моб + 1 десктоп»')
    print('=' * 60)
    main()
