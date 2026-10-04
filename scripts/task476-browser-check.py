#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 476 (этап 2 оптимизации): browser-check — IndexedDB-кэш
# серверных данных. Заявка (продолжение этапа 1): «ранее
# подгруженные данные должны сохраняться в памяти устройства для
# моментального доступа к ним» — для СЕРВЕРНЫХ данных (Apps Script).
#
# Сценарии (порт 8993, мок Apps Script как в task475):
#   A  онлайн: вход (Админ, быстрый путь), «График работы» грузится
#      с сервера → локальная копия пишется в ДВА слоя —
#      localStorage И KipDB (indexedDB kip8-cache-test-v1,
#      ключ kip8_ws_cache_v1, формат v1 с текущим видом);
#   B  имитация среза квоты localStorage: LS-копия УДАЛЕНА, Apps
#      Script недоступен (route.abort) → «График работы» всё равно
#      открывается МГНОВЕННО из KipDB-копии (сетка отрендерена,
#      экрана ошибки нет) — квота больше не режет копии;
#   C  «Плановые мероприятия»: отметки грузятся (мок planEvents.list
#      с отметкой «Работы на месяц», март) → пишутся в KipDB
#      (kip8_pe_marks_v1, годы); офлайн + LS-чистка → отметки
#      восстановлены (галочки pe-m-done на месте) — раздел переживает
#      офлайн ВПЕРВЫЕ;
#   D  logout: локальные копии серверных данных стёрты (LS-ключи
#      kip8_ws_cache_v1/kip8_cj_cache_v1/kip8_cj_cols_v1/
#      kip8_flow_cache_v1 + KipDB ПУСТ) — граница приватности;
#      настройки интерфейса не тронуты (тема жива);
#   E  storage.persist запрошен после входа (KipAuth._persistAsked),
#      storage.persisted() опрошен без JS-ошибок;
#   F  расходомеры: flowmeter.list → KipDB-копия kip8_flow_cache_v1
#      (рядом с localStorage-копией).
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8993
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task476')
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


def attach(page, ctx, theme='dark', tag='t476', apps_script_ok=True):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    state = {'apps_ok': apps_script_ok}

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if not state['apps_ok']:
            return route.abort()
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
        if action == 'heartbeat' or action == 'logout':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
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
                      body='not found (t476-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_devices_cache')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t476-%s');" % tag +
        "localStorage.setItem('kip8test:kip8_cached_role','Админ');" +
        "localStorage.setItem('kip8test:kip8_cached_email','user@test.local');" +
        "localStorage.setItem('kip8test:kip8_cached_user_id','1');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors, state


def goto_app(page):
    t0 = time.time()
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    return time.time() - t0


IDB_READ = """async (key) => {
    const db = await new Promise((res, rej) => {
        const r = indexedDB.open('kip8-cache-test-v1');
        r.onsuccess = () => res(r.result);
        r.onerror = () => rej(r.error);
    });
    return await new Promise((res) => {
        const t = db.transaction('kv', 'readonly');
        const g = t.objectStore('kv').get(key);
        g.onsuccess = () => res(g.result !== undefined ? g.result : null);
        g.onerror = () => res(null);
    });
}"""

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


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= A. Онлайн: WS пишет оба слоя =================
        print('A. Онлайн: «График работы» — копия в ДВА слоя (LS + KipDB)')
        ctxA = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageA = ctxA.new_page()
        errsA, stateA = attach(pageA, ctxA)
        tA = goto_app(pageA)
        pageA.wait_for_timeout(2500)
        check('A: приложение загружено (%.2f с)' % tA, tA < 8)
        check('A: роль Админ применена',
              pageA.evaluate("KipAuth._cachedRole") == 'Админ')
        check('A: storage.persist запрошен после входа',
              pageA.evaluate("KipAuth._persistAsked === true"))

        pageA.evaluate("navigateTo('work-schedule')")
        pageA.wait_for_timeout(3500)
        gridA = pageA.evaluate("""(() => {
            const w = document.getElementById('wsGridWrap');
            return {grid: !!(w && w.querySelector('.ws-grid')),
                    err: !!(w && w.querySelector('.admin-empty')),
                    cells: w ? w.querySelectorAll('td.ws-cell').length : 0};
        })()""")
        check('A: сетка графика отрендерена с сервера', gridA['grid'] and not gridA['err'], gridA)
        check('A: ячейки сетки есть', gridA['cells'] > 0, gridA['cells'])

        lsA = pageA.evaluate(
            "!!localStorage.getItem('kip8_ws_cache_v1')")
        idbA = pageA.evaluate(IDB_READ, 'kip8_ws_cache_v1')
        check('A: localStorage-копия табеля записана (Task 314 жив)', lsA)
        check('A: KipDB-копия табеля записана (Task 476)',
              idbA is not None and idbA.get('v') == 1 and 'views' in idbA)
        ym = '%d-%02d' % (time.localtime().tm_year, time.localtime().tm_mon)
        check('A: текущий вид %s в KipDB-копии' % ym,
              idbA is not None and isinstance(idbA.get('views'), dict)
              and ym in idbA['views'] and isinstance(idbA['views'][ym].get('entries'), list))
        check('A: KipDB: сотрудники в копии',
              idbA is not None and len(idbA.get('employees') or []) == 1)
        pageA.screenshot(path=os.path.join(SHOT_DIR, '01-ws-online-dual-cache.png'),
                        full_page=False)

        # -------- F. Расходомеры: KipDB-копия (параллельно онлайн) ----
        print('F. Онлайн: «Расходомеры» — KipDB-копия')
        pageA.evaluate("navigateTo('flowmeter-data')")
        pageA.wait_for_timeout(2500)
        idbF = pageA.evaluate(IDB_READ, 'kip8_flow_cache_v1')
        check('F: KipDB-копия расходомеров записана',
              idbF is not None and isinstance(idbF.get('meters'), list)
              and len(idbF['meters']) == 1)
        lsF = pageA.evaluate(
            "!!localStorage.getItem('kip8_flow_cache_v1')")
        check('F: localStorage-копия расходомеров тоже жива', lsF)

        # ================= B. LS срезан + сеть недоступна =================
        print('B. Квота localStorage «срезала» LS-копию + Apps Script недоступен')
        # ВАЖНО: ключи ЛОГИЧЕСКИЕ — на странице localStorage обёрнут
        # префиксом репозитория (kip8test:), обёртка сама добавит его.
        pageA.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
        stateA['apps_ok'] = False
        ctxA.set_offline(True)
        tB = goto_app(pageA)
        check('B: офлайн reload мгновенный (< 2.5 с): %.2f с' % tB, tB < 2.5)
        # bootstrap стартует на window load + 100 мс — ждём применения
        # роли (быстрый путь), иначе navigateTo гоняется с доступом
        pageA.wait_for_timeout(1800)
        pageA.evaluate("navigateTo('work-schedule')")
        pageA.wait_for_timeout(2500)
        gridB = pageA.evaluate("""(() => {
            const w = document.getElementById('wsGridWrap');
            const active = document.querySelector('.page-content.active');
            return {grid: !!(w && w.querySelector('.ws-grid')),
                    visible: !!(w && w.offsetParent !== null),
                    page: active ? active.id : null,
                    err: !!(w && w.querySelector('.admin-empty')),
                    load: !!(w && w.querySelector('.flow-loading'))};
        })()""")
        check('B: сетка поднята из KipDB (LS пуст, сети нет)',
              gridB['grid'] and gridB['visible'] and gridB['page'] == 'page-work-schedule', gridB)
        check('B: экрана ошибки нет', not gridB['err'], gridB)
        idbB = pageA.evaluate(IDB_READ, 'kip8_ws_cache_v1')
        check('B: KipDB-копия на месте (не стёрта)', idbB is not None and idbB.get('v') == 1)
        pageA.screenshot(path=os.path.join(SHOT_DIR, '02-ws-offline-from-kipdb.png'),
                        full_page=False)
        ctxA.set_offline(False)
        stateA['apps_ok'] = True

        # ================= C. PE отметки: копия + офлайн =================
        print('C. «Плановые мероприятия»: отметки — KipDB-копия, офлайн-восстановление')
        pageA.evaluate("navigateTo('plan-events')")
        pageA.wait_for_timeout(3000)
        marksOnline = pageA.evaluate(
            "document.querySelectorAll('td.pe-m-done').length")
        idbC = pageA.evaluate(IDB_READ, 'kip8_pe_marks_v1')
        check('C: отметка отрисована онлайн (март, «Работы на месяц»)', marksOnline > 0,
              marksOnline)
        check('C: KipDB-копия отметок записана',
              idbC is not None and idbC.get('v') == 1
              and isinstance(idbC.get('years'), dict)
              and '2026' in idbC['years']
              and len(idbC['years']['2026'].get('marks') or []) == 1)

        stateA['apps_ok'] = False
        ctxA.set_offline(True)
        tC = goto_app(pageA)
        pageA.wait_for_timeout(1500)
        pageA.evaluate("navigateTo('plan-events')")
        pageA.wait_for_timeout(2000)
        marksOff = pageA.evaluate(
            "document.querySelectorAll('td.pe-m-done').length")
        check('C: офлайн — отметки восстановлены из KipDB', marksOff > 0, marksOff)
        check('C: офлайн reload быстрый (%.2f с)' % tC, tC < 2.5)
        pageA.screenshot(path=os.path.join(SHOT_DIR, '03-pe-marks-offline.png'),
                        full_page=False)
        ctxA.set_offline(False)
        stateA['apps_ok'] = True

        # ================= D. Logout чистит копии =================
        print('D. Logout: чистка локальных копий серверных данных')
        pageA.wait_for_timeout(1000)
        beforeD = pageA.evaluate(IDB_KEYS)
        check('D: до logout — KipDB не пуст (%d ключей)' % len(beforeD), len(beforeD) >= 3,
              beforeD)
        pageA.evaluate("KipAuth.logout()")
        pageA.wait_for_timeout(1500)
        afterD = pageA.evaluate(IDB_KEYS)
        lsD = pageA.evaluate("""(() => ({
            ws: !!localStorage.getItem('kip8_ws_cache_v1'),
            cj: !!localStorage.getItem('kip8_cj_cache_v1'),
            cjCols: !!localStorage.getItem('kip8_cj_cols_v1'),
            fm: !!localStorage.getItem('kip8_flow_cache_v1'),
            theme: localStorage.getItem('app-theme'),
            role: localStorage.getItem('kip8_cached_role') || ''
        }))()""")
        check('D: KipDB ПОЛНОСТЬЮ очищен после logout', len(afterD) == 0, afterD)
        check('D: LS: копия табеля удалена', not lsD['ws'])
        check('D: LS: копии каб. журнала удалены', not lsD['cj'] and not lsD['cjCols'])
        check('D: LS: копия расходомеров удалена', not lsD['fm'])
        check('D: настройки интерфейса не тронуты (тема жива)', lsD['theme'] == 'dark')
        check('D: роль сброшена (гость)', lsD['role'] == '' or lsD['role'] is None or
              pageA.evaluate("KipAuth._cachedRole") == 'Общий доступ')
        pageA.screenshot(path=os.path.join(SHOT_DIR, '04-after-logout-guest.png'),
                        full_page=False)

        # ================= E. Итог: JS-ошибки =================
        print('E. JS-ошибки')
        check('E: 0 JS-ошибок за все сценарии', len(errsA) == 0, errsA[:5])

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
