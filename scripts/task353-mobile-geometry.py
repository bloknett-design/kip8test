#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 353: точная проверка геометрии модалки на мобильном экране
# (VLM усомнился в обрезке снизу — меряем getBoundingClientRect).
import json
from playwright.sync_api import sync_playwright

PORT = 8949
BASE = 'http://127.0.0.1:%d' % PORT

UA_ANDROID = ('Mozilla/5.0 (Linux; Android 13; Pixel 7) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Mobile Safari/537.36')

STATE = {'users': [
    {'id': 1, 'email': 'admin@x.ru', 'role': 'Админ',
     'login_status': 'вход выполнен', 'last_login': '2026-09-08 08:00:00'},
    {'id': 3, 'email': 'u3@x.ru', 'role': 'Общий доступ',
     'login_status': 'вход не выполнен', 'last_login': None},
]}


def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'admin@x.ru', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                                     'permissions': {'admin.panel': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'adminListUsers':
        return {'ok': True, 'data': STATE['users']}
    if action == 'adminListSessions':
        return {'ok': True, 'data': []}
    return {'ok': False, 'error': 'Unknown action'}


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
        for vp in [{'width': 390, 'height': 780}, {'width': 360, 'height': 640},
                   {'width': 320, 'height': 568}]:
            ctx = browser.new_context(user_agent=UA_ANDROID, viewport=vp,
                                      is_mobile=True, has_touch=True)

            def handle(route, request):
                url = request.url
                action = 'unknown'
                for part in url.split('?')[1].split('&') if '?' in url else []:
                    if part.startswith('action='):
                        action = part.split('=')[1]
                route.fulfill(status=200, content_type='application/json; charset=utf-8',
                              body=json.dumps(mock_response(action),
                                              ensure_ascii=False).encode('utf-8'))
            ctx.route('**/exec?**', handle)
            ctx.route('**script.google.com/**', handle)
            ctx.route('**raw.githubusercontent.com/**',
                      lambda r: r.fulfill(status=404, body='nf'))
            ctx.route('**calendar.legalic.ru/**',
                      lambda r: r.fulfill(status=404, body='nf'))

            page = ctx.new_page()
            page.goto(BASE + '/index.html')
            page.evaluate("localStorage.setItem('kip8_session_token','adm-tok')")
            page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
            page.reload()
            page.wait_for_timeout(1800)
            page.evaluate("navigateTo('admin-users')")
            page.wait_for_timeout(1200)
            page.evaluate("""() => {
                const items = document.querySelectorAll('#adminUsersList .admin-item');
                for (const it of items) {
                    if (it.textContent.indexOf('u3@x.ru') !== -1) {
                        it.querySelector('.admin-delete-btn').click();
                    }
                }
            }""")
            page.wait_for_selector('#deleteUserOverlay.active', timeout=3000)
            geo = page.evaluate("""() => {
                const m = document.querySelector('.delete-user-modal');
                const r = m.getBoundingClientRect();
                const b = document.querySelector('#deleteUserBtn').getBoundingClientRect();
                return {top: r.top, bottom: r.bottom, left: r.left, right: r.right,
                        vh: window.innerHeight, vw: window.innerWidth,
                        btnBottom: b.bottom, scrollH: m.scrollHeight, clientH: m.clientHeight};
            }""")
            ok = (geo['top'] >= 0 and geo['bottom'] <= geo['vh'] and
                  geo['left'] >= 0 and geo['right'] <= geo['vw'] and
                  geo['btnBottom'] <= geo['vh'])
            print('%s: modal %dx%s top=%.0f bottom=%.0f btnBottom=%.0f vh=%d → %s' % (
                vp, geo['vw'], '%.0f' % geo['right'] if False else (geo['right'] - geo['left']),
                geo['top'], geo['bottom'], geo['btnBottom'], geo['vh'],
                'OK' if ok else 'OVERFLOW'))
            if not ok:
                page.screenshot(path='scripts/task353-proof-overflow-%dx%d.png' %
                                (vp['width'], vp['height']))
            ctx.close()
        browser.close()
    httpd.shutdown()


if __name__ == '__main__':
    main()
