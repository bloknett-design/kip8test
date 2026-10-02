#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 462: browser-check — доступ к «Плановым мероприятиям» по
# ОТДЕЛЬНОМУ праву plan.events в матрице KIP8_Access.
# Заявка: «...в файле KIP8_Access, в таблице matrix нужно добавить
# новый столбец для определения доступа к данному разделу».
# КОНТЕКСТ (мок-сервер, порт 8993):
#   A: «КИП ИОС», колонка plan.events ✓ (+kipios.view ✓) — кнопка на
#      «Документации ИОС» видна, сайдбар-пункт виден, страница
#      открывается, крошки на месте;
#   B: «КИП ИОС», колонка есть, план ✓ → всё скрыто: кнопка на хабе,
#      пункт сайдбара; прямой переход → экран «Нет доступа»; ХАБ
#      «Документация ИОС» при этом ЖИВ (право снято не ломает хаб);
#   C: «КИП8 pro» (flowmeter.view без КИП ИОС) + plan.events ✓ —
#      раздел виден и открывается;
#   D: ПЕРЕХОДНЫЙ период — матрица БЕЗ колонки plan.events (скрипт
#      RoleMatrixTask462Init не запущен): «КИП ИОС» видит раздел
#      (прежнее поведение Task 460 — никто не теряет доступ);
#   E: легаси — сервер без getMyAccess (Unknown action): «КИП ИОС»
#      видит раздел по легаси-карте;
#   F: «КИП8» (без КИП ИОС и расходомеров) + plan.events ✓ — право
#      САМОДОСТАТОЧНО: раздел виден, хаба «Документация ИОС» нет;
#   G: 0 JS-ошибок во всех контекстах; скриншоты в
#      download/kip8test-task462/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8993

PASS = 0
FAIL = 0
SHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        '..', 'download', 'kip8test-task462')


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def api_response(action, body, role, perms, no_matrix):
    if no_matrix and action == 'getMyAccess':
        # «старый сервер» без getMyAccess — клиент уходит в легаси-карту
        return {'ok': False, 'error': 'Unknown action'}
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': role}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': role, 'found': True,
                'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, role='КИП ИОС', perms=None, no_matrix=False):
    """Мок API + тема + токен. perms — права матрицы (dict)."""
    if perms is None:
        perms = {}
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t462-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        if body is None:
            body = {}
        resp = api_response(action, body, role, perms, no_matrix)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t462-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def sidebar_item(page):
    """Видимость пункта «Плановые мероприятия» в сайдбаре."""
    return page.evaluate("""(() => {
        const items = document.querySelectorAll('.sidebar-item');
        for (const it of items) {
            const oc = it.getAttribute('onclick') || '';
            if (oc.indexOf("navigateTo('plan-events')") !== -1) {
                return {vis: it.style.display !== 'none',
                        txt: it.innerText.trim()};
            }
        }
        return null;})()""")


def hub_button(page):
    """Видимость кнопки «Плановые мероприятия» на «Документации ИОС»."""
    return page.evaluate("""(() => {
        const b = document.getElementById('planEventsMenuBtn');
        return b ? b.style.display !== 'none' : null;})()""")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== A: колонка есть, галка ✓ =====
        print('=== Контекст A: «КИП ИОС», plan.events ✓ — раздел доступен ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsA = attach(page, ctx, 'dark', 'a', role='КИП ИОС',
                     perms={'kipios.view': True, 'plan.events': True})
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        check('A1: кнопка «Плановые мероприятия» на хабе ВИДНА',
              hub_button(page) is True)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(500)
        check('A2: страница открывается',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        crumbs = page.evaluate("""(() => {
            const t = document.querySelector('#page-plan-events .page-inline-header-title');
            return t ? t.innerText.replace(/\\s+/g, ' ').trim() : '';})()""")
        check('A3: крошки «... Документация ИОС / Плановые мероприятия»',
              'Документация ИОС' in crumbs and 'Плановые мероприятия' in crumbs, crumbs)
        side = sidebar_item(page)
        check('A4: пункт сайдбара виден', side and side['vis'], side)
        shot(page, '01-access-granted.png')
        check('A5: 0 JS-ошибок', len(jsA) == 0, jsA[:3])
        ctx.close()

        # ===== B: колонка есть, галка ✗ — ГЛАВНЫЙ сценарий =====
        print('=== Контекст B: «КИП ИОС», plan.events ✗ — раздел СКРЫТ ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsB = attach(page, ctx, 'dark', 'b', role='КИП ИОС',
                     perms={'kipios.view': True, 'plan.events': False})
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        check('B1: кнопка «Плановые мероприятия» на хабе СКРЫТА',
              hub_button(page) is False)
        docsios = page.evaluate("!!document.querySelector('#page-docs-ios.active')")
        check('B2: хаб «Документация ИОС» сам ОТКРЫТ (право снято не ломает хаб)',
              docsios)
        # другие кнопки хаба живы (Расходомеры/Табель не тронуты — видны по
        # своим правам; у КИП ИОС расходомеров нет, Табель есть)
        side = sidebar_item(page)
        check('B3: пункт сайдбара «Плановые мероприятия» СКРЫТ',
              side and not side['vis'], side)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(500)
        noacc = page.evaluate("""(() => {
            const el = document.getElementById('noAccessScreen');
            const pageEl = document.getElementById('page-plan-events');
            return {no: el && el.style.display !== 'none',
                    act: pageEl && pageEl.classList.contains('active')};})()""")
        check('B4: прямой переход → экран «Нет доступа», страница НЕ активна',
              noacc['no'] and not noacc['act'], noacc)
        shot(page, '02-access-denied.png')
        check('B5: 0 JS-ошибок', len(jsB) == 0, jsB[:3])
        ctx.close()

        # ===== C: КИП8 pro + plan.events ✓ =====
        print('=== Контекст C: «КИП8 pro» (flowmeter без КИП ИОС) + plan.events ✓ ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsC = attach(page, ctx, 'dark', 'c', role='КИП8 pro',
                     perms={'calc.view': True, 'library.view': True,
                            'whatsnew.view': True, 'flowmeter.view': True,
                            'plan.events': True})
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        check('C1: кнопка на хабе ВИДНА', hub_button(page) is True)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(500)
        check('C2: страница открывается',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        check('C3: 0 JS-ошибок', len(jsC) == 0, jsC[:3])
        ctx.close()

        # ===== D: ПЕРЕХОДНЫЙ период — колонки в матрице ещё нет =====
        print('=== Контекст D: матрица БЕЗ колонки plan.events (скрипт не запущен) ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsD = attach(page, ctx, 'dark', 'd', role='КИП ИОС',
                     perms={'kipios.view': True})  # ключа plan.events НЕТ
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        check('D1: раздел ВИДЕН (переходный фоллбек Task 460)',
              hub_button(page) is True)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(500)
        check('D2: страница открывается',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        # и КИП8 pro без колонки — тоже виден (за расходомерами)
        ctx.close()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsD2 = attach(page, ctx, 'dark', 'd2', role='КИП8 pro',
                      perms={'flowmeter.view': True})  # ключа plan.events НЕТ
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        check('D3: «КИП8 pro» без колонки — раздел ВИДЕН (за docs-ios)',
              hub_button(page) is True)
        check('D4: 0 JS-ошибок', len(jsD) == 0 and len(jsD2) == 0,
              (jsD[:2], jsD2[:2]))
        ctx.close()

        # ===== E: легаси — сервер без getMyAccess =====
        print('=== Контекст E: getMyAccess недоступен → легаси-карта ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsE = attach(page, ctx, 'dark', 'e', role='КИП ИОС',
                     perms={'kipios.view': True}, no_matrix=True)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        check('E1: раздел ВИДЕН по легаси-карте (КИП ИОС)',
              hub_button(page) is True)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(500)
        check('E2: страница открывается',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        check('E3: 0 JS-ошибок', len(jsE) == 0, jsE[:3])
        ctx.close()

        # ===== F: право самодостаточно (роль без КИП ИОС/расходомеров) =====
        print('=== Контекст F: «КИП8» + plan.events ✓ — право самодостаточно ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsF = attach(page, ctx, 'dark', 'f', role='КИП8',
                     perms={'calc.view': True, 'library.view': True,
                            'whatsnew.view': True, 'plan.events': True})
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('docs')")
        page.wait_for_timeout(400)
        hub_hidden = page.evaluate("""(() => {
            const btns = document.querySelectorAll('#page-docs .menu-btn');
            for (const b of btns) {
                if ((b.getAttribute('onclick')||'').indexOf('docs-ios') !== -1)
                    return b.style.display === 'none';
            }
            return true;})()""")
        check('F1: хаба «Документация ИОС» НЕТ (права нет)',
              hub_hidden)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(500)
        check('F2: раздел ОТКРЫВАЕТСЯ по праву plan.events (самодостаточно)',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        side = sidebar_item(page)
        check('F3: пункт сайдбара виден', side and side['vis'], side)
        shot(page, '03-standalone-permission.png')
        check('F4: 0 JS-ошибок', len(jsF) == 0, jsF[:3])
        ctx.close()

        browser.close()

    print('-' * 60)
    print('ИТОГ Task 462 browser-check: %d passed / %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
