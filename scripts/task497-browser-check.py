#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 497: browser-check — баг-репорт: «В разделе хозрасчётных
# расходомеров, при первом после входа в приложение открытие
# страницы, появляется надпись "Нет избранных расходомеров…", но
# счётчик нижней кнопки избранного показывает количество
# добавленных. Поправь: если в избранном есть расходомеры, они
# сразу отображаются ДО подгрузки данных с сервера.»
#
# МЕТОДИКА: сервер (flowmeter.list) отвечает С ЗАДЕРЖКОЙ — маршрут
# перехватывается и НЕ выполняется («сервер думает»), assertions
# проходят в окне до ответа (deferred route.fulfill, проверено
# отдельно: страница жива, fetch ожидает), затем «сервер отвечает».
#
#   1. МОБАЙЛ 375 тёмная, авторизован, FlowFav {1,3} + КЭШ:
#      вкладка «Избранные» (Task 491); В ОКНЕ ДО ОТВЕТА: 2 карточки
#      .flow-card с КАЭШ-показаниями (111,11 / 333,33), НЕТ ни
#      «Нет избранных расходомеров», ни «Загрузка данных»; счётчик
#      #flowFavCount = 2; ПОСЛЕ ответа: карточки обновлены сервером
#      (999,99 / 888,88). Скриншоты до/после.
#   2. Кэша НЕТ + FlowFav: в окне до ответа — «Загрузка данных…»,
#      НЕ «Нет избранных…»; после ответа — 2 карточки.
#   3. БЕЗ избранного: вкладка «Все»; после ответа клик «Избранные»
#      → заглушка «Нет избранных расходомеров» (поведение как прежде).
# + 0 JS-ошибок в каждом сценарии.
import json
import os
import time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8985
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task497')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0
SERVER_DELAY_NOTE = 'flowmeter.list: отложенный fulfill (сервер «думает»)'


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:200] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=False)
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def mk(id_, hoz, curr, prev):
    return {'id': id_, 'hoz': hoz,
            'param': 'Расход пара в корпус %d' % id_,
            'datePrev': '10/1/2026', 'dateCurr': '10/5/2026',
            'prev': prev, 'curr': curr, 'unit': 'т',
            'temp': None, 'gcal': 60.46, 'period': 'Ежедневно',
            'modRole': 'Админ', 'modName': 'bc', 'modTimestamp': None}


# Кэш (старые показания) и сервер (свежие) — значения НЕ пересекаются
CACHE_METERS = [mk(1, 'Хозрасчёт №1', 111.11, 110.11),
                mk(2, 'Хозрасчёт №2', 222.22, 220.22),
                mk(3, 'Хозрасчёт №3', 333.33, 330.33),
                mk(4, 'Хозрасчёт №4', 444.44, 440.44)]
SERVER_METERS = [mk(1, 'Хозрасчёт №1', 999.99, 900.11),
                 mk(2, 'Хозрасчёт №2', 888.88, 880.22),
                 mk(3, 'Хозрасчёт №3', 777.77, 770.33),
                 mk(4, 'Хозрасчёт №4', 666.66, 660.44)]
FAV_JSON = json.dumps({'1': '2026-10-01T00:00:00.000Z',
                       '3': '2026-10-02T00:00:00.000Z'})
FAV_ORDER = json.dumps(['1', '3'])


def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'flowmeter.view': True,
                                'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


def setup_routes(ctx, pending):
    """flowmeter.list перехватывается и НЕ отвечается сразу —
    «сервер думает». Остальные экшены — мгновенный ok-ответ."""

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if action == 'flowmeter.list':
            pending.append(route)
            return
        route.fulfill(status=200,
                      content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action),
                                      ensure_ascii=False).encode('utf-8'))

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (browser-check t497)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


def release(pending, meters):
    """«Сервер ответил»: выполняем все отложенные маршруты."""
    body = json.dumps({'ok': True, 'data': {'meters': meters}},
                      ensure_ascii=False).encode('utf-8')
    for r in pending:
        try:
            r.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=body)
        except Exception as e:
            print('  (release: %s)' % e)
    pending.clear()


def flow_state(page):
    return page.evaluate(r"""(() => {
        const btns = document.querySelectorAll('.flow-tab[data-flow-tab]');
        let allOn = true, favOn = true, n = 0;
        btns.forEach(b => {
            n++;
            const on = b.classList.contains('active');
            if (b.getAttribute('data-flow-tab') === 'fav') { if (!on) favOn = false; }
            else { if (!on) allOn = false; }
        });
        const list = document.getElementById('flowList');
        const txt = list ? list.textContent : '';
        return {
            n, allOn, favOn,
            cards: document.querySelectorAll('#flowList .flow-card').length,
            favCount: (document.getElementById('flowFavCount') || {}).textContent,
            noFavStub: txt.indexOf('Нет избранных расходомеров') !== -1,
            loading: txt.indexOf('Загрузка данных') !== -1,
            hasCacheVals: txt.indexOf('111,11') !== -1 || txt.indexOf('333,33') !== -1,
            hasServerVals: txt.indexOf('999,99') !== -1 || txt.indexOf('777,77') !== -1
        };
    })()""")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ============ 1. ГЛАВНЫЙ СЦЕНАРИЙ: кэш + избранное ================
        pending1 = []
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx, pending1)
        seed = ("localStorage.setItem('kip8test:kip8_session_token'," +
                "'bc-t497-a');" +
                "localStorage.setItem('kip8test:app-theme','dark');" +
                "localStorage.setItem('kip8test:kip8_flow_fav_v1'," +
                "'" + FAV_JSON + "');" +
                "localStorage.setItem('kip8test:kip8_flow_fav_order_v1'," +
                "'" + FAV_ORDER + "');" +
                "localStorage.setItem('kip8test:kip8_flow_cache_v1'," +
                "'" + json.dumps({'meters': CACHE_METERS,
                                  'ts': int(time.time() * 1000)},
                                 ensure_ascii=False) + "');")
        ctx.add_init_script(seed)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('flowmeter-data')")
        page.wait_for_timeout(1000)  # окно «сервер думает» (fetch в полёте)

        st = flow_state(page)
        check('A: вкладка «Избранные» активна (Task 491 жив)',
              st['favOn'] and not st['allOn'] and st['n'] >= 2, st)
        check('B: ДО ответа сервера — 2 карточки избранного ИЗ КЭША',
              st['cards'] == 2, st)
        check('C: ДО ответа — НЕТ заглушки «Нет избранных расходомеров»',
              not st['noFavStub'], st)
        check('D: ДО ответа — НЕТ «Загрузка данных» (кэш отрисован)',
              not st['loading'], st)
        check('E: счётчик нижнего бара #flowFavCount = 2',
              (st['favCount'] or '').strip() == '2', st)
        check('F: показания карточек — КАЭШОВЫЕ (111,11 / 333,33)',
              st['hasCacheVals'] and not st['hasServerVals'], st)
        shot(page, 'a-fav-instant-cache.png')

        release(pending1, SERVER_METERS)
        page.wait_for_timeout(1800)
        st2 = flow_state(page)
        check('G: ПОСЛЕ ответа — карточек по-прежнему 2',
              st2['cards'] == 2, st2)
        check('H: ПОСЛЕ ответа — показания СЕРВЕРНЫЕ (999,99 / 777,77)',
              st2['hasServerVals'] and not st2['hasCacheVals'], st2)
        check('I: ПОСЛЕ ответа — нет «Загрузки» и заглушек',
              not st2['loading'] and not st2['noFavStub'], st2)
        shot(page, 'b-fav-server-refreshed.png')
        check('J: сценарий 1 — 0 JS-ошибок', len(js_errors) == 0,
              js_errors[:3])
        ctx.close()

        # ============ 2. Кэша НЕТ, избранное есть =========================
        pending2 = []
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda d: d.accept())
        setup_routes(ctx2, pending2)
        ctx2.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token'," +
            "'bc-t497-b');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            "localStorage.setItem('kip8test:kip8_flow_fav_v1'," +
            "'" + FAV_JSON + "');" +
            "localStorage.setItem('kip8test:kip8_flow_fav_order_v1'," +
            "'" + FAV_ORDER + "');")
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('flowmeter-data')")
        page2.wait_for_timeout(1000)

        stn = flow_state(page2)
        check('K: без кэша, ДО ответа — «Загрузка данных…»',
              stn['loading'], stn)
        check('L: без кэша, ДО ответа — НЕТ «Нет избранных расходомеров»',
              not stn['noFavStub'], stn)
        shot(page2, 'c-no-cache-loading.png')
        release(pending2, SERVER_METERS)
        page2.wait_for_timeout(1800)
        stn2 = flow_state(page2)
        check('M: без кэша, ПОСЛЕ ответа — 2 карточки избранного',
              stn2['cards'] == 2 and not stn2['loading'], stn2)
        check('N: сценарий 2 — 0 JS-ошибок', len(js_errors2) == 0,
              js_errors2[:3])
        ctx2.close()

        # ============ 3. БЕЗ избранного (заглушка как прежде) =============
        pending3 = []
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page3 = ctx3.new_page()
        js_errors3 = []
        page3.on('pageerror', lambda e: js_errors3.append(str(e)))
        page3.on('dialog', lambda d: d.accept())
        setup_routes(ctx3, pending3)
        ctx3.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token'," +
            "'bc-t497-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('flowmeter-data')")
        page3.wait_for_timeout(1000)
        stf = flow_state(page3)
        check('O: без избранного — вкладка «Все» (Task 491)',
              stf['allOn'] and not stf['favOn'], stf)
        release(pending3, SERVER_METERS)
        page3.wait_for_timeout(1800)
        stf2 = flow_state(page3)
        check('P: без избранного, ПОСЛЕ ответа — все 4 карточки',
              stf2['cards'] == 4, stf2)
        # переключение на «Избранные» — заглушка как прежде
        # (клик в ВИДИМЫЙ таб нижнего бара: первый .flow-tab в DOM —
        # скрытые десктопные табы #flowDesktopTabs)
        page3.click("#flowBottomBar .flow-tab[data-flow-tab='fav']",
                    timeout=4000)
        page3.wait_for_timeout(600)
        stf3 = flow_state(page3)
        check('Q: «Избранные» без избранного — заглушка «Нет избранных» '
              '(как прежде)', stf3['noFavStub'] and stf3['cards'] == 0, stf3)
        shot(page3, 'd-no-fav-empty-stub.png')
        check('R: сценарий 3 — 0 JS-ошибок', len(js_errors3) == 0,
              js_errors3[:3])
        ctx3.close()

        browser.close()

    print('')
    print('ИТОГ: %d passed, %d failed (%s)' % (PASS, FAIL, SERVER_DELAY_NOTE))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
