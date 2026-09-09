#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 353: browser-check — UI удаления пользователя в админ-панели.
#
# Проверки (3 контекста, вход — токен в localStorage как в task346):
#   1. ADMIN DESKTOP: список пользователей → у каждой карточки кнопка
#      «Удалить»; СВОЯ строка (email текущего админа) — disabled;
#      чужая — клик → модалка с email → «Удалить» → запрос
#      adminDeleteUser с верным userId → тост → модалка закрыта →
#      список перезагружен (юзер исчез из мок-состояния).
#   2. ERROR-ПУТЬ: сервер отклоняет («Нельзя удалить последнего
#      админа») → текст ошибки В МОДАЛКЕ, кнопка снова активна,
#      модалка открыта, повторных запросов нет.
#   3. CANCEL-ПУТЬ: «Отмена» закрывает модалку, adminDeleteUser НЕ
#      вызывается.
#   + фильтр журнала содержит опцию ADMIN_DELETE_USER;
#   + мобильная модалка (390px) — скриншот;
#   + 0 JS-ошибок во всех контекстах; скриншоты-пруфы.
import datetime
import json
from playwright.sync_api import sync_playwright

PORT = 8948
BASE = 'http://127.0.0.1:%d' % PORT

UA_DESKTOP = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36')
UA_ANDROID = ('Mozilla/5.0 (Linux; Android 13; Pixel 7) '
              'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Mobile Safari/537.36')

ADMIN_EMAIL = 'admin@x.ru'

# Мок-состояние сервера
STATE = {
    'users': [
        {'id': 1, 'email': ADMIN_EMAIL, 'role': 'Админ',
         'login_status': 'вход выполнен', 'last_login': '2026-09-08 08:00:00'},
        {'id': 2, 'email': 'u2@x.ru', 'role': 'КИП ИОС',
         'login_status': 'вход выполнен', 'last_login': '2026-09-07 12:30:00'},
        {'id': 3, 'email': 'u3@x.ru', 'role': 'Общий доступ',
         'login_status': 'вход не выполнен', 'last_login': None},
    ],
    'delete_error': None,       # None → успех; строка → сервер отклоняет
    'counts': {},               # action → число вызовов
}

# Перехваченные запросы (payload по action)
REQUESTS = {}

RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((ok, name, detail))
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                           (' — ' + detail) if detail and not ok else ''))


def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': ADMIN_EMAIL,
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                                     'permissions': {'admin.panel': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'adminListUsers':
        return {'ok': True, 'data': STATE['users']}
    if action == 'adminListSessions':
        return {'ok': True, 'data': [
            {'email': ADMIN_EMAIL, 'role': 'Админ', 'token': 'tokAdm',
             'created_at': '2026-09-08 07:00:00',
             'last_heartbeat': '2026-09-09 08:00:00', 'device': 'desktop'},
            {'email': 'u2@x.ru', 'role': 'КИП ИОС', 'token': 'tokU2',
             'created_at': '2026-09-08 07:30:00',
             'last_heartbeat': '2026-09-08 08:30:00', 'device': 'mobile'},
        ]}
    if action == 'adminDeleteUser':
        if STATE['delete_error']:
            return {'ok': False, 'error': STATE['delete_error']}
        # Успех: убираем юзера из мок-состояния (реализм перезагрузки)
        uid = REQUESTS.get('adminDeleteUser', {}).get('userId')
        STATE['users'] = [u for u in STATE['users'] if u['id'] != uid]
        return {'ok': True, 'data': {'ok': True, 'deleted': True,
                                     'sessionsRemoved': 2, 'otpsRemoved': 1}}
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
        STATE['counts'][action] = STATE['counts'].get(action, 0) + 1
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (t353)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


def admin_open_users(page):
    """Открыть админ-панель → Пользователи (токен уже в localStorage)."""
    page.evaluate("navigateTo('admin-users')")
    page.wait_for_timeout(1200)


def click_delete_for(page, email):
    """Клик «Удалить» в карточке с указанным email. Возвращает найдено ли."""
    return page.evaluate("""(email) => {
        const items = document.querySelectorAll('#adminUsersList .admin-item');
        for (const it of items) {
            if (it.textContent.indexOf(email) !== -1) {
                const b = it.querySelector('.admin-delete-btn');
                if (b) { b.click(); return true; }
            }
        }
        return false;
    }""", email)


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

        # ---------- Контекст 1: ADMIN DESKTOP — happy path ----------
        print('=== 1. ADMIN: кнопки, модалка, удаление, перезагрузка ===')
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_DESKTOP,
                                  viewport={'width': 1280, 'height': 800})
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.evaluate("localStorage.setItem('kip8_session_token','adm-tok')")
        page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
        page.reload()
        page.wait_for_timeout(1800)
        admin_open_users(page)

        html = page.evaluate("document.getElementById('adminUsersList').innerHTML")
        n_del = html.count('admin-delete-btn')
        check('ADMIN: у всех 3 карточек есть кнопка «Удалить»', n_del == 3,
              'кнопок: %d' % n_del)

        self_disabled = page.evaluate("""(email) => {
            const items = document.querySelectorAll('#adminUsersList .admin-item');
            for (const it of items) {
                if (it.textContent.indexOf(email) !== -1) {
                    const b = it.querySelector('.admin-delete-btn');
                    return b ? b.disabled : null;
                }
            }
            return null;
        }""", ADMIN_EMAIL)
        check('ADMIN: своя строка — кнопка disabled', self_disabled is True,
              'disabled: %r' % self_disabled)

        others_enabled = page.evaluate("""(email) => {
            let ok = 0, bad = 0;
            const items = document.querySelectorAll('#adminUsersList .admin-item');
            for (const it of items) {
                if (it.textContent.indexOf(email) !== -1) continue;
                const b = it.querySelector('.admin-delete-btn');
                if (b && !b.disabled) ok++; else bad++;
            }
            return {ok: ok, bad: bad};
        }""", ADMIN_EMAIL)
        check('ADMIN: чужие строки — кнопки активны',
              others_enabled['ok'] == 2 and others_enabled['bad'] == 0,
              str(others_enabled))

        page.screenshot(path='scripts/task353-proof-admin-users.png')

        # Открыть модалку на u2@x.ru
        found = click_delete_for(page, 'u2@x.ru')
        page.wait_for_selector('#deleteUserOverlay.active', timeout=3000)
        check('ADMIN: модалка открылась (клик по кнопке карточки)', found)
        modal_email = page.evaluate("document.getElementById('deleteUserEmail').textContent")
        check('ADMIN: email цели в модалке', modal_email == 'u2@x.ru',
              'фактически: %r' % modal_email)
        warn = page.evaluate(
            "document.querySelector('#deleteUserOverlay .delete-user-warn').textContent")
        check('ADMIN: предупреждение о безвозвратности',
              ('безвозвратно' in warn) and ('сессии' in warn))
        page.screenshot(path='scripts/task353-proof-delete-modal.png')

        # Подтвердить
        del_calls = STATE['counts'].get('adminDeleteUser', 0)
        list_calls = STATE['counts'].get('adminListUsers', 0)
        page.click('#deleteUserBtn')
        page.wait_for_timeout(1000)
        check('ADMIN: adminDeleteUser вызван ровно 1 раз',
              STATE['counts'].get('adminDeleteUser', 0) == del_calls + 1)
        payload = REQUESTS.get('adminDeleteUser', {})
        check('ADMIN: payload userId=2', payload.get('userId') == 2,
              'фактически: %r' % payload.get('userId'))
        check('ADMIN: токен передан', bool(payload.get('token')))
        modal_active = page.evaluate(
            "document.getElementById('deleteUserOverlay').classList.contains('active')")
        check('ADMIN: модалка закрыта после успеха', not modal_active)
        toast_text = page.evaluate("document.getElementById('toastMessage').textContent")
        check('ADMIN: тост с email и сессиями',
              ('u2@x.ru' in toast_text) and ('2' in toast_text),
              'текст: %r' % toast_text[:120])
        check('ADMIN: список пользователей перезагружен',
              STATE['counts'].get('adminListUsers', 0) > list_calls)
        u2_gone = page.evaluate(
            "document.getElementById('adminUsersList').textContent.indexOf('u2@x.ru') === -1")
        check('ADMIN: удалённый юзер исчез из списка', u2_gone)
        check('ADMIN: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

        # ---------- Контекст 2: ERROR-ПУТЬ ----------
        print('=== 2. ADMIN: ошибка сервера — текст в модалке ===')
        STATE['delete_error'] = 'Нельзя удалить последнего админа'
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_DESKTOP,
                                  viewport={'width': 1280, 'height': 800})
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.evaluate("localStorage.setItem('kip8_session_token','adm-tok')")
        page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
        page.reload()
        page.wait_for_timeout(1800)
        admin_open_users(page)

        click_delete_for(page, 'u3@x.ru')
        page.wait_for_selector('#deleteUserOverlay.active', timeout=3000)
        del_before = STATE['counts'].get('adminDeleteUser', 0)
        page.click('#deleteUserBtn')
        page.wait_for_timeout(1000)
        err_text = page.evaluate("document.getElementById('deleteUserError').textContent")
        check('ERROR: текст ошибки в модалке',
              err_text == 'Нельзя удалить последнего админа',
              'фактически: %r' % err_text)
        btn_state = page.evaluate("""() => {
            const b = document.getElementById('deleteUserBtn');
            return {disabled: b.disabled, label: b.textContent};
        }""")
        check('ERROR: кнопка снова активна с надписью «Удалить»',
              (not btn_state['disabled']) and btn_state['label'] == 'Удалить',
              str(btn_state))
        still_active = page.evaluate(
            "document.getElementById('deleteUserOverlay').classList.contains('active')")
        check('ERROR: модалка осталась открыта (юзер читает ошибку)', still_active)
        check('ERROR: повторных запросов НЕ было',
              STATE['counts'].get('adminDeleteUser', 0) == del_before + 1)
        page.screenshot(path='scripts/task353-proof-error.png')
        check('ERROR: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))

        # ---------- Контекст 3: CANCEL + фильтр журнала ----------
        print('=== 3. ADMIN: Отмена и фильтр журнала ===')
        del_calls = STATE['counts'].get('adminDeleteUser', 0)
        click_delete_for(page, 'u3@x.ru')  # снова открываем модалку
        page.wait_for_selector('#deleteUserOverlay.active', timeout=3000)
        page.click('#deleteUserOverlay .delete-user-cancel')
        page.wait_for_timeout(500)
        closed = page.evaluate(
            "document.getElementById('deleteUserOverlay').classList.contains('active')")
        check('CANCEL: модалка закрыта по «Отмена»', not closed)
        check('CANCEL: adminDeleteUser НЕ вызывался',
              STATE['counts'].get('adminDeleteUser', 0) == del_calls)

        # Крестик тоже закрывает
        click_delete_for(page, 'u3@x.ru')
        page.wait_for_selector('#deleteUserOverlay.active', timeout=3000)
        page.click('#deleteUserOverlay .delete-user-close')
        page.wait_for_timeout(500)
        closed = page.evaluate(
            "document.getElementById('deleteUserOverlay').classList.contains('active')")
        check('CANCEL: модалка закрыта по крестику', not closed)
        check('CANCEL: adminDeleteUser по-прежнему НЕ вызывался',
              STATE['counts'].get('adminDeleteUser', 0) == del_calls)

        # Фильтр журнала
        has_opt = page.evaluate("""() => {
            const sel = document.getElementById('adminLogFilter');
            if (!sel) return false;
            for (const o of sel.options) {
                if (o.value === 'ADMIN_DELETE_USER') return true;
            }
            return false;
        }""")
        check('FILTER: опция ADMIN_DELETE_USER в журнале событий', has_opt)
        ctx.close()
        STATE['delete_error'] = None

        # ---------- Контекст 4: MOBILE ----------
        print('=== 4. MOBILE: модалка удаления на узком экране ===')
        REQUESTS.clear()
        errors = []
        ctx = browser.new_context(user_agent=UA_ANDROID,
                                  viewport={'width': 390, 'height': 780},
                                  is_mobile=True, has_touch=True)
        route_all(ctx)
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '/index.html')
        page.evaluate("localStorage.setItem('kip8_session_token','adm-tok')")
        page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
        page.reload()
        page.wait_for_timeout(1800)
        admin_open_users(page)
        click_delete_for(page, 'u3@x.ru')
        page.wait_for_selector('#deleteUserOverlay.active', timeout=3000)
        fits = page.evaluate("""() => {
            const m = document.querySelector('.delete-user-modal');
            const r = m.getBoundingClientRect();
            return r.left >= 0 && r.right <= window.innerWidth &&
                   r.width > 200 && r.width < 400;
        }""")
        check('MOBILE: модалка вписывается в экран (390px)', fits)
        page.screenshot(path='scripts/task353-proof-mobile-modal.png')
        check('MOBILE: 0 JS-ошибок', len(errors) == 0, '; '.join(errors[:3]))
        ctx.close()

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
    print('Task 353 — browser-check: UI удаления пользователя в админ-панели')
    print('=' * 60)
    main()
