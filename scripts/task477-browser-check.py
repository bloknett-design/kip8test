#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 477 (этап 3 оптимизации): browser-check — фоновая
# предзагрузка всех данных приложения ПО ПРАВАМ РОЛИ. Заявка:
# «в принципе должны незаметно подгружаться все данные приложения
# (только из тех разделов и данных, к которым у пользователя есть
# доступ согласно его роли)».
#
# Сценарии (порт 8992, мок Apps Script как в task476):
#   A  Админ (быстрый путь входа): через ~35 с после входа ВСЕ
#      13 элементов очереди прогружены ФОНОМ (дашборд активен,
#      пользователь ничего не видел): 9 статических data/*.json
#      (счётчик fetch-обёртки) + 7 WS-экшенов + 2 CJ + 1 FM +
#      1 PE (счётчики мока); KipDB заполнен ВСЕМИ копиями ДО
#      первого открытия разделов (ws/cj×2/fm/pe); SW DATA-кэш
#      прогрет (devices.json и др.); _state(): done=13, fail=0;
#   B  logout: очередь остановлена (started=false, pending=0);
#   C  ГОСТЬ (без токена): предзагрузка не запускается вовсе —
#      0 запросов к data/*.json и 0 серверных экшенов;
#   D  роль «КИП8» (без КИП ИОС/расходомеров/табеля): очередь
#      только из phonebook.json + exam-tickets.json — devices.json
#      НЕ запрашивался (права роли);
#   E  saveData (мок navigator.connection): предзагрузка
#      отключена целиком — 0 запросов данных;
#   F  0 JS-ошибок во всех сценариях.
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8992
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task477')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def serve():
    os.chdir(REPO)

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

    httpd = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    httpd.serve_forever()


WS_CODES = [{'code': 'Д', 'name': 'День', 'color': '#FFE082'},
             {'code': '', 'name': 'Выходной', 'color': '#EEF0F2'}]
WS_EMP = [{'таб_номер': '001', 'ФИО': 'Иванов И. И.', 'тип': 'сменный'}]
PE_MARKS = [{'id': 1, 'год': 2026, 'месяц': 3, 'мероприятие': 'Работы на месяц',
             'дата_выполнения': '2026-03-25'}]


def attach(page, ctx, theme='dark', tag='t477', with_token=True, save_data=False):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    state = {'apps_ok': True, 'actions': {}}

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if not state['apps_ok']:
            return route.abort()
        state['actions'][action] = state['actions'].get(action, 0) + 1
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': 'Админ'}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'Админ', 'found': True,
                        'permissions': {'calc.view': True, 'library.view': True,
                            'kipios.view': True, 'secret.view': True, 'whatsnew.view': True,
                            'charts.view': True, 'flowmeter.view': True,
                            'workschedule.view': True, 'workschedule.edit': True,
                            'plan.events': True}}}, ensure_ascii=False))
        if action == 'workSchedule.getStatusCodes':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'codes': WS_CODES}}, ensure_ascii=False))
        if action == 'workSchedule.getPatterns':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'patterns': []}}, ensure_ascii=False))
        if action == 'workSchedule.listEmployees':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'employees': WS_EMP}}, ensure_ascii=False))
        if action == 'workSchedule.listEntries':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'entries': [
                    {'дата': '2026-10-01', 'таб_номер': '001', 'статус': 'Д'}]}},
                    ensure_ascii=False))
        if action == 'workSchedule.listTrainings':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'trainings': [], 'instrList': [],
                    'instrAll': [], 'eventsAll': []}}, ensure_ascii=False))
        if action == 'workSchedule.listVacations':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'vacations': []}}, ensure_ascii=False))
        if action == 'workSchedule.listPpe':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ppe': []}}, ensure_ascii=False))
        if action == 'cableJournal.getColumns':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'columns': [
                    {'id': 'name', 'label': 'Название'}], 'canEdit': True}},
                    ensure_ascii=False))
        if action == 'cableJournal.list':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'rows': [], 'total': 0}},
                    ensure_ascii=False))
        if action == 'flowmeter.list':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'meters': [
                    {'id': 1, 'hoz': 'Хозрасчёт №1', 'param': 'Расход пара в корпус 114',
                     'datePrev': '10/1/2026', 'dateCurr': '10/2/2026',
                     'prev': 100.0, 'curr': 101.5, 'unit': 'т', 'temp': None,
                     'gcal': 60.46, 'period': 'Ежедневно', 'modRole': 'Админ',
                     'modName': 'mobile_test', 'modTimestamp': None}]}},
                    ensure_ascii=False))
        if action == 'planEvents.list':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'marks': PE_MARKS}}, ensure_ascii=False))
        if action == 'planEvents.years':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'years': []}}, ensure_ascii=False))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t477-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    init = (
        # счётчик fetch-обёртки: все сетевые запросы страницы
        "window.__reqs = [];" +
        "(function(){const _f = window.fetch;" +
        " window.fetch = function(u) { try { window.__reqs.push(String(u).split('?')[0]); }" +
        " catch(e){} return _f.apply(this, arguments); };})();"
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_cj_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_cj_cols_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_flow_cache_v1')}catch(e){};"
    )
    if with_token:
        init += ("localStorage.setItem('kip8test:kip8_session_token','bc-t477-%s');" % tag +
                 "localStorage.setItem('kip8test:kip8_cached_role','Админ');" +
                 "localStorage.setItem('kip8test:kip8_cached_email','user@test.local');" +
                 "localStorage.setItem('kip8test:kip8_cached_user_id','1');")
    else:
        init += "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};"
    if save_data:
        init += "try{Object.defineProperty(navigator,'connection'," \
                "{value:{saveData:true,effectiveType:'4g'},configurable:true});}catch(e){};"
    init += "localStorage.setItem('kip8test:app-theme','%s');" % theme
    ctx.add_init_script(init)
    return js_errors, state


def goto_app(page):
    t0 = time.time()
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    return time.time() - t0


IDB_KEYS = """async () => {
    const db = await new Promise((res, rej) => {
        const r = indexedDB.open('kip8-cache-test-v1');
        r.onsuccess = () => res(r.result);
        r.onerror = () => rej(r.error);
    });
    return await new Promise((res) => {
        const t = db.transaction('kv', 'readonly');
        const g = t.objectStore('kv').getAllKeys();
        g.onsuccess = () => res(g.result || []);
        g.onerror = () => res([]);
    });
}"""

DATA_REQS = """() => (window.__reqs || []).filter(u =>
    u.indexOf('/data/') !== -1 || u.indexOf('data/') === 0)"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= A. Админ: полная фоновая предзагрузка =================
        print('A. Админ: фоновая предзагрузка всех данных по роли (~35 с, незаметно)')
        ctxA = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageA = ctxA.new_page()
        errsA, stateA = attach(pageA, ctxA)
        tA = goto_app(pageA)
        check('A: приложение загружено (%.2f с)' % tA, tA < 8)
        pageA.wait_for_timeout(2500)
        check('A: дашборд активен (пользователь на месте)',
              pageA.evaluate("document.getElementById('page-dashboard').classList.contains('active')"))

        # ждём завершения очереди: 4 с задержка старта + 13 × ~2 с
        deadline = time.time() + 50
        st = {}
        while time.time() < deadline:
            st = pageA.evaluate("KipPreload._state()")
            if not st['active'] and st['pending'] == 0 and st['done'] + st['fail'] >= 13:
                break
            pageA.wait_for_timeout(2000)
        check('A: очередь завершилась: done=%d fail=%d pending=%d' %
              (st.get('done', -1), st.get('fail', -1), st.get('pending', -1)),
              st.get('pending') == 0 and st.get('done') == 13 and st.get('fail') == 0, st)

        dataReqs = pageA.evaluate(DATA_REQS)
        for f in ['devices', 'lockouts', 'valves', 'regulators', 'projects',
                  'cables', 'phonebook', 'exam-tickets', 'flowmeters']:
            check('A: %s.json предзагружен фоном' % f,
                  ('data/%s.json' % f) in dataReqs, dataReqs)
        a = stateA['actions']
        for act in ['workSchedule.getStatusCodes', 'workSchedule.getPatterns',
                    'workSchedule.listEmployees', 'workSchedule.listTrainings',
                    'workSchedule.listVacations', 'workSchedule.listPpe',
                    'workSchedule.listEntries', 'cableJournal.getColumns',
                    'cableJournal.list', 'flowmeter.list', 'planEvents.list']:
            check('A: экшен %s вызван предзагрузкой' % act, a.get(act, 0) >= 1,
                  a.get(act, 0))

        keys = pageA.evaluate(IDB_KEYS)
        for k in ['kip8_ws_cache_v1', 'kip8_cj_cache_v1', 'kip8_cj_cols_v1',
                  'kip8_flow_cache_v1', 'kip8_pe_marks_v1']:
            check('A: KipDB-копия %s готова ДО открытия раздела' % k, k in keys, keys)
        swData = pageA.evaluate("""async () => {
            const names = await caches.keys();
            const dcache = names.indexOf('kipia-data-test-v1') !== -1
                ? await caches.open('kipia-data-test-v1') : null;
            if (!dcache) return [];
            const ks = await dcache.keys();
            return ks.map(k => String(new URL(k.url).pathname));
        }""")
        check('A: SW DATA-кэш прогрет предзагрузкой (devices.json там)',
              any(u.endswith('/data/devices.json') for u in swData) if swData else False,
              [u for u in swData if 'devices' in u][:3])
        check('A: пользователь НЕ уходил с дашборда',
              pageA.evaluate("document.getElementById('page-dashboard').classList.contains('active')"))
        pageA.screenshot(path=os.path.join(SHOT_DIR, '01-admin-preload-done.png'),
                        full_page=False)

        # ================= B. logout: очередь остановлена =================
        print('B. logout: остановка очереди предзагрузки')
        pageA.evaluate("KipAuth.logout()")
        pageA.wait_for_timeout(800)
        stB = pageA.evaluate("KipPreload._state()")
        check('B: started=false после logout', stB['started'] is False, stB)
        check('B: pending=0 (очередь сброшена)', stB['pending'] == 0, stB)

        # ================= C. Гость: предзагрузки нет =================
        print('C. ГОСТЬ (без токена): предзагрузка не запускается')
        ctxC = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageC = ctxC.new_page()
        errsC, stateC = attach(pageC, ctxC, with_token=False)
        tC = goto_app(pageC)
        pageC.wait_for_timeout(10000)
        stC = pageC.evaluate("KipPreload._state()")
        dataReqsC = pageC.evaluate(DATA_REQS)
        # exam-tickets.json тянет ЛЕГАСИ pre-cache билетов (Task 242,
        # работает для всех с 2 с задержки — НЕ KipPreload)
        dataReqsC = [u for u in dataReqsC if u != 'data/exam-tickets.json']
        check('C: _state: предзагрузка не стартовала (pending=0)', stC['pending'] == 0, stC)
        check('C: 0 запросов к data/*.json за 10 с (кроме легаси-битов)',
              len(dataReqsC) == 0, dataReqsC)
        check('C: 0 серверных экшенов разделов',
              all(v == 0 for k, v in stateC['actions'].items()
                  if k not in ('getCurrentUser', 'getMyAccess', 'heartbeat')),
              stateC['actions'])
        pageC.screenshot(path=os.path.join(SHOT_DIR, '02-guest-no-preload.png'),
                        full_page=False)
        ctxC.close()

        # ================= D. Роль «КИП8»: только свои данные =================
        print('D. Роль «КИП8» (без КИП ИОС/табеля/расходомеров): очередь по правам')
        ctxD = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageD = ctxD.new_page()
        errsD, stateD = attach(pageD, ctxD, tag='t477d')
        # базовые маршруты уже навешаны attach-ом; переопределяем ПОВЕРХ
        # (Playwright: последний зарегистрированный маршрут приоритетнее)
        def kip8_handle(route, request):
            url = request.url
            action = ''
            if 'action=' in url:
                action = unquote(url.split('action=')[1].split('&')[0])
            if action == 'getCurrentUser':
                return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                    body=json.dumps({'ok': True, 'data': {'userId': 2,
                        'email': 'kip8@test.local', 'role': 'КИП8'}}, ensure_ascii=False))
            if action == 'getMyAccess':
                return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                    body=json.dumps({'ok': True, 'data': {'role': 'КИП8', 'found': True,
                            'permissions': {'calc.view': True, 'library.view': True,
                                'secret.view': True, 'whatsnew.view': True}}},
                            ensure_ascii=False))
            if action == 'heartbeat' or action == 'logout':
                return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                    body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                                 body=json.dumps({'ok': True, 'data': {'ok': True}},
                                                 ensure_ascii=False))
        ctxD.route('**/exec?**', kip8_handle, times=1000)
        ctxD.route('**script.google.com/**', kip8_handle, times=1000)
        # роль в LS-кэше — КИП8 (быстрый путь)
        pageD.add_init_script(
            "localStorage.setItem('kip8test:kip8_cached_role','КИП8');")
        tD = goto_app(pageD)
        pageD.wait_for_timeout(4000 + 12000)
        stD = pageD.evaluate("KipPreload._state()")
        dataReqsD = pageD.evaluate(DATA_REQS)
        check('D: очередь завершилась по правам роли КИП8 (done=%d)' % stD.get('done', -1),
              stD.get('pending') == 0 and stD.get('done') == 2, stD)
        check('D: phonebook.json предзагружен (секретное — право есть)',
              ('data/phonebook.json') in dataReqsD, dataReqsD)
        check('D: exam-tickets.json предзагружен (библиотека — право есть)',
              ('data/exam-tickets.json') in dataReqsD, dataReqsD)
        check('D: devices.json НЕ запрашивался (нет права КИП ИОС)',
              ('data/devices.json') not in dataReqsD, dataReqsD)
        check('D: серверные экшены разделов НЕ вызывались (нет прав)',
              stateD['actions'].get('workSchedule.listEntries', 0) == 0 and
              stateD['actions'].get('flowmeter.list', 0) == 0, stateD['actions'])
        pageD.screenshot(path=os.path.join(SHOT_DIR, '03-kip8-role-preload.png'),
                        full_page=False)
        ctxD.close()

        # ================= E. saveData: очередь отключена =================
        print('E. Data Saver: предзагрузка отключается целиком')
        ctxE = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageE = ctxE.new_page()
        errsE, stateE = attach(pageE, ctxE, tag='t477e', save_data=True)
        tE = goto_app(pageE)
        pageE.wait_for_timeout(10000)
        stE = pageE.evaluate("KipPreload._state()")
        dataReqsE = pageE.evaluate(DATA_REQS)
        # exam-tickets — легаси pre-cache (Task 242), не KipPreload
        dataReqsE = [u for u in dataReqsE if u != 'data/exam-tickets.json']
        check('E: очередь НЕ запущена при saveData (pending=0)', stE['pending'] == 0, stE)
        check('E: 0 запросов к data/*.json за 10 с (кроме легаси-битов)',
              len(dataReqsE) == 0, dataReqsE)
        pageE.screenshot(path=os.path.join(SHOT_DIR, '04-savedata-off.png'),
                        full_page=False)
        ctxE.close()

        # ================= F. Итог =================
        print('F. JS-ошибки')
        all_errs = errsA + errsC + errsD + errsE
        check('F: 0 JS-ошибок за все сценарии', len(all_errs) == 0, all_errs[:5])

        browser.close()

    print('\n═════════════════════════════════════════════════════')
    print('  Итог: %d passed, %d failed' % (PASS, FAIL))
    print('═════════════════════════════════════════════════════')
    return 1 if FAIL else 0


if __name__ == '__main__':
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    time.sleep(0.5)
    code = main()
    raise SystemExit(code)
