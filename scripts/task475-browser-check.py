#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 475 (этап 1 оптимизации): browser-check — моментальное
# открытие при любой связи + персистентный кэш данных + офлайн-ветка
# входа. Заявка: «моментальное открытие приложения при отсутствии
# или медленной связи, ранее подгруженные данные должны сохраняться
# в памяти устройства… загрузка должна быть фоновой (незаметной)».
#
# Сценарии (порт 8994, мок Apps Script как в task474):
#   A  онлайн-первая-загрузка: SW активен, кэш kipia-test-v699,
#      раздел «Приборы» рендерится, 0 JS-ошибок;
#   B  ПОЛНЫЙ ОФЛАЙН (context.set_offline): reload → приложение
#      открывается ИЗ КЭША SW мгновенно (< 2.5 с при любых
#      таймаутах сети), «Приборы» открываются из DATA-кэша/
#      precache без сети, 0 JS-ошибок; скриншот;
#   C  МЕДЛЕННАЯ СЕТЬ (route-задержка 4 с на каждый сетевой
#      запрос): reload → приложение открывается из кэша БЫСТРЕЕ
#      сетевой задержки (goto < 2.5 с при сети 4+ с) — сеть не
#      блокирует открытие; скриншот;
#   D  ОФЛАЙН-ВЕТКА ВХОДА: токен есть, кэша роли нет, Apps Script
#      недоступен (route.abort) → ГОСТЕВОЙ режим (не экран входа),
#      тост «Нет связи с сервером — открыт гостевой режим»,
#      автоповтор запущен (KipAuth._offlineRetryTimer); скриншот;
#      затем Apps Script «оживает» + событие online → повтор
#      выполняет вход (роль Админ, тост «Связь восстановлена»);
#   E  SWR-детекция изменения данных: модификация data/devices.json
#      на диске → повторное открытие раздела → мгновенно СТАРАЯ
#      копия из кэша + фоновая ревалидация ловит изменение →
#      DATA_REFRESHED → devLoaded сброшен (консоль-маркер Task 475)
#      → следующее открытие — СВЕЖИЕ данные с маркером.
import json
import os
import shutil
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8994
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task475')
os.makedirs(SHOT_DIR, exist_ok=True)
DEVICES_JSON = os.path.join(REPO, 'data', 'devices.json')

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


def attach(page, ctx, theme='dark', tag='t475', apps_script_ok=True, as_admin=True):
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
            role = 'Админ' if as_admin else 'Общий доступ'
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': role}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'Админ', 'found': True,
                        'permissions': {'calc.view': True, 'library.view': True,
                            'kipios.view': True, 'secret.view': True, 'whatsnew.view': True,
                            'charts.view': True, 'flowmeter.view': True,
                            'workschedule.view': True, 'workschedule.edit': True,
                            'admin.panel': True}}}, ensure_ascii=False))
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t475-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_devices_cache')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t475-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors, state


def goto_app(page):
    t0 = time.time()
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    return time.time() - t0


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= A. Онлайн-первая-загрузка =================
        print('A. Онлайн: первая загрузка + SW активен')
        ctxA = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageA = ctxA.new_page()
        errsA, _ = attach(pageA, ctxA)
        tA = goto_app(pageA)
        pageA.wait_for_timeout(3000)
        check('A: приложение загружено (быстро: %.2f с)' % tA, tA < 8)
        sw_state = pageA.evaluate("""async () => {
            const reg = await navigator.serviceWorker.ready;
            const keys = await caches.keys();
            const c = await caches.open('kipia-test-v699');
            const k = await c.keys();
            return {controlled: !!navigator.serviceWorker.controller,
                    caches: keys, entries: k.length};
        }""")
        check('A: SW контролирует страницу', sw_state['controlled'])
        check('A: кэш kipia-test-v699 создан', 'kipia-test-v699' in sw_state['caches'])
        check('A: precache наполнен (>= 20 записей)', sw_state['entries'] >= 20,
              sw_state['entries'])
        check('A: DATA-кэш kipia-data-test-v1 создан', 'kipia-data-test-v1' in sw_state['caches'])
        # Раздел «Приборы» онлайн — данные уходят в DATA-кэш
        pageA.evaluate("navigateTo('kip-ios')")
        pageA.wait_for_timeout(1200)
        pageA.evaluate("navigateTo('devices')")
        pageA.wait_for_timeout(2500)
        nA = pageA.evaluate("document.querySelectorAll('.dev-card, .device-card, #devList > *').length")
        check('A: раздел «Приборы» рендерится онлайн', (nA or 0) > 0, nA)
        dataA = pageA.evaluate("""async () => {
            const c = await caches.open('kipia-data-test-v1');
            const r = await c.match('/kip8test/data/devices.json') ||
                      await c.keys().then(async ks => {
                          for (const k of ks) if (String(k.url).indexOf('devices.json') !== -1)
                              return await c.match(k);
                          return null; });
            return r ? (await r.text()).length : 0;
        }""")
        check('A: devices.json сохранён в персистентный DATA-кэш', dataA > 100000, dataA)

        # ================= B. Полный офлайн =================
        print('B. ПОЛНЫЙ ОФЛАЙН: reload + раздел «Приборы»')
        ctxA.set_offline(True)
        tB = goto_app(pageA)
        check('B: офлайн reload — мгновенно (< 2.5 с): %.2f с' % tB, tB < 2.5)
        pageB_visible = pageA.evaluate("""(() => {
            const d = document.getElementById('page-dashboard');
            const ls = document.getElementById('loginScreen');
            return {dash: !!(d && d.classList.contains('active')),
                    login: !!(ls && ls.classList.contains('active'))};
        })()""")
        check('B: дашборд открыт, экрана входа нет',
              pageB_visible['dash'] and not pageB_visible['login'], pageB_visible)
        pageA.evaluate("navigateTo('kip-ios')")
        pageA.wait_for_timeout(800)
        pageA.evaluate("navigateTo('devices')")
        pageA.wait_for_timeout(2000)
        nB = pageA.evaluate("document.querySelectorAll('.dev-card, .device-card, #devList > *').length")
        check('B: «Приборы» открыты БЕЗ сети (из кэша устройства)', (nB or 0) > 0, nB)
        check('B: 0 JS-ошибок при офлайн-работе', len(errsA) == 0, errsA[:3])
        pageA.screenshot(path=os.path.join(SHOT_DIR, '01-offline-devices.png'))
        ctxA.set_offline(False)

        # ================= C. Медленная сеть =================
        print('C. МЕДЛЕННАЯ СЕТЬ (CDP: задержка 4 с, 50 Кбит/с на сетевые запросы)')
        # Эмуляция на уровне сети Chromium (не через route — Python-sleep
        # в синхронном route-обработчике блокирует соединение и портит
        # замер). SW отвечает из кэша ДО сети — открытие не ждёт сеть.
        cdp = ctxA.new_cdp_session(pageA)
        cdp.send('Network.enable')
        cdp.send('Network.emulateNetworkConditions', {
            'offline': False, 'latency': 4000,
            'downloadThroughput': 50 * 1024, 'uploadThroughput': 50 * 1024})
        tC = goto_app(pageA)
        check('C: открытие БЫСТРЕЕ сетевой задержки (< 2.5 с при сети 4+ с): %.2f с' % tC, tC < 2.5)
        pageA.wait_for_timeout(800)
        pageA.screenshot(path=os.path.join(SHOT_DIR, '02-slow-network-instant.png'))
        cdp.send('Network.emulateNetworkConditions', {
            'offline': False, 'latency': 0,
            'downloadThroughput': 10 * 1024 * 1024 * 1024,
            'uploadThroughput': 10 * 1024 * 1024 * 1024})
        check('C: 0 JS-ошибок при медленной сети', len(errsA) == 0, errsA[:3])
        ctxA.close()

        # ================= D. Офлайн-ветка входа =================
        print('D. ВХОД: токен есть, кэша роли нет, Apps Script недоступен')
        ctxD = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageD = ctxD.new_page()
        errsD, stateD = attach(pageD, ctxD, apps_script_ok=False, tag='t475d')
        # Токен есть (init_script), кэш роли УДАЛЁН — медленный путь bootstrap
        pageD.add_init_script("try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
                              "try{localStorage.removeItem('kip8_cached_role')}catch(e){};")
        tD = goto_app(pageD)
        pageD.wait_for_timeout(3500)
        stD = pageD.evaluate("""(() => {
            const ls = document.getElementById('loginScreen');
            const d = document.getElementById('page-dashboard');
            const toasts = Array.from(document.querySelectorAll('.toast, #toast, .app-toast, .show'))
                .map(el => el.textContent || '').join(' ');
            return {login: !!(ls && ls.classList.contains('active')),
                    dash: !!(d && d.classList.contains('active')),
                    role: (typeof KipAuth !== 'undefined' && KipAuth._cachedRole) || null,
                    retry: (typeof KipAuth !== 'undefined' && !!KipAuth._offlineRetryTimer),
                    toasts: toasts};
        })()""")
        check('D: ГОСТЕВОЙ режим (не экран входа-тупик)',
              (not stD['login']) and stD['dash'], stD)
        check('D: роль «Общий доступ»', stD['role'] == 'Общий доступ', stD['role'])
        check('D: автоповтор входа запущен (_offlineRetryTimer)', stD['retry'])
        check('D: тост поясняет гостевой режим',
              'гостевой режим' in stD['toasts'], stD['toasts'][:120])
        check('D: токен сохранён (вход догонится)', pageD.evaluate(
            "!!(localStorage.getItem('kip8test:kip8_session_token') || localStorage.getItem('kip8_session_token'))"))
        check('D: 0 JS-ошибок', len(errsD) == 0, errsD[:3])
        pageD.screenshot(path=os.path.join(SHOT_DIR, '03-guest-mode-offline.png'))

        # Сеть «ожила»: Apps Script отвечает, событие online → повтор входит
        print('D2. Возврат связи: автоповтор выполняет вход')
        stateD['apps_ok'] = True
        pageD.evaluate("window.dispatchEvent(new Event('online'))")
        pageD.wait_for_timeout(2500)
        stD2 = pageD.evaluate("""(() => {
            const toasts = Array.from(document.querySelectorAll('.toast, #toast, .app-toast, .show'))
                .map(el => el.textContent || '').join(' ');
            return {role: (typeof KipAuth !== 'undefined' && KipAuth._cachedRole) || null,
                    retryStopped: (typeof KipAuth !== 'undefined' && !KipAuth._offlineRetryTimer),
                    cached: localStorage.getItem('kip8test:kip8_cached_role') ||
                            localStorage.getItem('kip8_cached_role'),
                    toasts: toasts};
        })()""")
        check('D2: роль Админ применена после возврата связи', stD2['role'] == 'Админ', stD2['role'])
        check('D2: автоповтор остановлен', stD2['retryStopped'])
        check('D2: роль закэширована (следующий старт мгновенный)',
              stD2['cached'] == 'Админ', stD2['cached'])
        check('D2: тост «Связь восстановлена — выполнен вход»',
              'Связь восстановлена' in stD2['toasts'], stD2['toasts'][:120])
        pageD.screenshot(path=os.path.join(SHOT_DIR, '04-retry-recovered.png'))
        ctxD.close()

        # ================= E. SWR: детекция изменения данных =================
        print('E. SWR: изменение data/devices.json обнаруживается в фоне')
        ctxE = browser.new_context(viewport={'width': 1280, 'height': 900})
        pageE = ctxE.new_page()
        errsE, _ = attach(pageE, ctxE, tag='t475e')
        swr_logs = []
        pageE.on('console', lambda m: swr_logs.append(m.text)
                 if ('Task475' in m.text or 'SWR' in m.text) else None)
        goto_app(pageE)
        pageE.wait_for_timeout(2500)
        pageE.evaluate("navigateTo('kip-ios')")
        pageE.wait_for_timeout(800)
        pageE.evaluate("navigateTo('devices')")
        pageE.wait_for_timeout(2500)
        name_before = pageE.evaluate("(devData && devData.devices && devData.devices.length) || 0")
        check('E: исходные данные загружены (1291)', name_before == 1291, name_before)

        # Модифицируем файл на диске (+ маркерная запись)
        shutil.copy2(DEVICES_JSON, DEVICES_JSON + '.t475bak')
        try:
            with open(DEVICES_JSON, encoding='utf-8') as f:
                doc = json.load(f)
            doc['devices'].insert(0, {'ID': 'T475', 'Наименование': 'Маркер Task475',
                                      'Тип': 'SWR-тест', '№ прибора': 'T475',
                                      'Место установки': 'кэш'})
            with open(DEVICES_JSON, 'w', encoding='utf-8') as f:
                json.dump(doc, f, ensure_ascii=False)

            # Перезагрузка: App Shell + данные — из кэша устройства
            # мгновенно (сеть не ждём); фоновая ревалидация ловит изменение
            # (сублейбл главной уже тянет devices.json при загрузке).
            tE = goto_app(pageE)
            check('E: reload после изменения — мгновенный (< 2.5 с): %.2f с' % tE, tE < 2.5)
            pageE.wait_for_timeout(1500)
            pageE.evaluate("navigateTo('kip-ios')")
            pageE.wait_for_timeout(500)
            pageE.evaluate("navigateTo('devices')")
            pageE.wait_for_timeout(1000)
            # Ждём фоновую ревалидацию + DATA_REFRESHED + сброс/обновление
            swr_seen = False
            for _ in range(20):
                if any('Task475' in t for t in swr_logs):
                    swr_seen = True
                    break
                pageE.wait_for_timeout(500)
            check('E: DATA_REFRESHED получен (консоль Task475)', swr_seen, swr_logs[:3])
            # Следующее открытие — свежие данные с маркером
            pageE.evaluate("navigateTo('dashboard')")
            pageE.wait_for_timeout(400)
            pageE.evaluate("navigateTo('kip-ios')")
            pageE.wait_for_timeout(400)
            pageE.evaluate("navigateTo('devices')")
            pageE.wait_for_timeout(2000)
            n_fresh = pageE.evaluate("(devData && devData.devices && devData.devices.length) || 0")
            marker = pageE.evaluate(
                "(devData && devData.devices && devData.devices[0] && devData.devices[0].ID) || ''")
            check('E: следующее открытие — СВЕЖИЕ данные (1292 + маркер T475)',
                  n_fresh == 1292 and marker == 'T475', (n_fresh, marker))
            check('E: 0 JS-ошибок', len(errsE) == 0, errsE[:3])
            pageE.screenshot(path=os.path.join(SHOT_DIR, '05-swr-fresh-data.png'))
        finally:
            shutil.move(DEVICES_JSON + '.t475bak', DEVICES_JSON)
        ctxE.close()

        browser.close()

    print('\n════ Итог: %d passed, %d failed ════' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    threading.Thread(target=serve, daemon=True).start()
    time.sleep(0.5)
    main()
