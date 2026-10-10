#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 493: browser-check — заявка: «Кнопку "Табель учёта рабочего
# времени" установленную на главную страницу назови короче "Табель
# учёта".»
#   1. МОБАЙЛ 375 тёмная, ПОСЕВ пина work-schedule (localStorage
#      'kip8test:pinnedSubsections'): на главной закреплённая кнопка —
#      метка «Табель учёта» (БЕЗ «рабочего времени»), субметка прежняя,
#      золотистый docs-стиль; клик по кнопке → #page-work-schedule
#      активна, заголовок страницы — ПОЛНОЕ имя (не переименовывали).
#   2. СТРАНИЦА «Документация ИОС»: статическая кнопка
#      workScheduleMenuBtn — метка «Табель учёта», субметка прежняя.
#   3. САЙДБАР (DOM): пункт sidebarWorkScheduleBtn — полное имя.
#   4. ДЕСКТОП 1280: закреплённая кнопка на главной — «Табель учёта».
# + 0 JS-ошибок; скриншоты в download/kip8test-task493/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8981
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task493')
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
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:200] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=False)
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


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


def setup_routes(ctx):
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200,
                      content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action),
                                      ensure_ascii=False).encode('utf-8'))

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (browser-check t493)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Состояние закреплённой кнопки на главной
PIN_BTN_JS = r"""(() => {
    const items = [...document.querySelectorAll('#pinnedItemsContainer .pinned-item')];
    const out = {count: items.length, items: []};
    items.forEach(el => {
        const label = el.querySelector('.menu-btn-label');
        const sub = el.querySelector('.menu-btn-sublabel');
        const st = getComputedStyle(el);
        out.items.push({
            key: el.getAttribute('data-pinned-key'),
            label: label ? label.textContent.trim() : null,
            labelColor: label ? getComputedStyle(label).color : null,
            sub: sub ? sub.textContent.trim() : null,
            borderColor: st.borderColor,
            visible: st.display !== 'none' &&
                     el.getBoundingClientRect().width > 0
        });
    });
    return out;
})()"""

# Статическая кнопка на page-docs-ios + заголовок страницы + сайдбар
STATIC_JS = r"""(() => {
    const btn = document.getElementById('workScheduleMenuBtn');
    const out = {};
    if (btn) {
        const label = btn.querySelector('.menu-btn-label');
        const sub = btn.querySelector('.menu-btn-sublabel');
        out.btnLabel = label ? label.textContent.trim() : null;
        out.btnSub = sub ? sub.textContent.trim() : null;
        out.btnOnclick = btn.getAttribute('onclick');
    } else { out.btnLabel = 'NO-BTN'; }
    const hdr = document.querySelector('#page-work-schedule .page-inline-header-title');
    out.pageHeader = hdr ? hdr.textContent.trim() : null;
    const sb = document.getElementById('sidebarWorkScheduleBtn');
    out.sidebarText = sb ? sb.textContent.trim() : null;
    out.activePage = (document.querySelector('.page-content.active') || {}).id || null;
    return out;
})()"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors = []

        # ---------- 1. МОБАЙЛ 375 тёмная, посев пина work-schedule ----------
        print('== 1. МОБАЙЛ 375 (тёмная), пин work-schedule посеян ==')
        ctx = browser.new_context(
            viewport={'width': 375, 'height': 720},
            is_mobile=True, has_touch=True,
            color_scheme='dark', locale='ru-RU')
        setup_routes(ctx)
        # Посев ДО скриптов страницы: изоляция kip8test: ещё не активна —
        # пишем сразу в сырые ключи с префиксом (токен как в 492 + пин)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t493-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            "localStorage.setItem('kip8test:pinnedSubsections', "
            "JSON.stringify(['work-schedule']));")
        page = ctx.new_page()
        page.on('dialog', lambda d: d.accept())
        page.on('pageerror', lambda e: errors.append('m: ' + str(e)))
        # console-«errors» вида «Failed to load resource» — это сетевые 404
        # от намеренно заблокированных маршрутов (как в 492), не считаем
        page.on('console', lambda m: errors.append('m-c: ' + m.text)
                if (m.type == 'error' and
                    'Failed to load resource' not in m.text) else None)
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(2500)

        pin = page.evaluate(PIN_BTN_JS)
        check('закреплена ровно ОДНА кнопка', pin['count'] == 1, pin)
        ws = next((i for i in pin['items'] if i['key'] == 'work-schedule'), None)
        check('кнопка work-schedule закреплена', ws is not None, pin)
        if ws:
            check('метка на главной — «Табель учёта»',
                  ws['label'] == 'Табель учёта', ws['label'])
            check('«рабочего времени» на главной НЕТ',
                  'рабочего времени' not in (ws['label'] or ''))
            check('субметка прежняя — «Шахматка сменного и дневного персонала»',
                  ws['sub'] == 'Шахматка сменного и дневного персонала', ws['sub'])
            check('кнопка видима', ws['visible'])
            check('золотистый docs-стиль (рамка)',
                  '199, 150, 74' in (ws['borderColor'] or ''), ws['borderColor'])
        shot(page, 'a-mobile-dashboard-pin.png')

        # Клик по закреплённой кнопке → страница табеля, ПОЛНЫЙ заголовок
        if ws:
            page.click('#pinnedItemsContainer .pinned-item')
            page.wait_for_timeout(900)
            st = page.evaluate(STATIC_JS)
            check('клик → открылась #page-work-schedule',
                  st['activePage'] == 'page-work-schedule', st['activePage'])
            check('заголовок страницы — ПОЛНОЕ имя (не переименовывали)',
                  st['pageHeader'] == 'Табель учёта рабочего времени',
                  st['pageHeader'])
            shot(page, 'b-mobile-work-schedule-page.png')

        # ---------- 2. Страница «Документация ИОС» ----------
        print('== 2. «Документация ИОС»: статическая кнопка ==')
        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(600)
        st = page.evaluate(STATIC_JS)
        check('кнопка workScheduleMenuBtn на странице есть',
              st['btnLabel'] != 'NO-BTN', st)
        check('метка кнопки на docs-ios — «Табель учёта»',
              st['btnLabel'] == 'Табель учёта', st['btnLabel'])
        check('субметка прежняя',
              st['btnSub'] == 'Шахматка сменного и дневного персонала',
              st['btnSub'])
        check('onclick прежний — navigateTo(\'work-schedule\')',
              st['btnOnclick'] == "navigateTo('work-schedule')", st['btnOnclick'])
        shot(page, 'c-mobile-docs-ios-btn.png')

        # ---------- 3. Сайдбар (DOM, без открытия) ----------
        print('== 3. Сайдбар: пункт — полное имя ==')
        sb = page.evaluate(
            "(() => { const el = document.getElementById('sidebarWorkScheduleBtn');"
            " return el ? el.textContent.trim() : null; })()")
        check('пункт сайдбара — ПОЛНОЕ имя (не переименовывали)',
              sb == 'Табель учёта рабочего времени', sb)
        ctx.close()

        # ---------- 4. ДЕСКТОП 1280 ----------
        print('== 4. ДЕСКТОП 1280, пин посеян ==')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800},
                                   locale='ru-RU')
        setup_routes(ctx2)
        ctx2.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t493-d');" +
            "localStorage.setItem('kip8test:pinnedSubsections', "
            "JSON.stringify(['work-schedule']));")
        page2 = ctx2.new_page()
        page2.on('pageerror', lambda e: errors.append('d: ' + str(e)))
        page2.on('console', lambda m: errors.append('d-c: ' + m.text)
                if (m.type == 'error' and
                    'Failed to load resource' not in m.text) else None)
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        pin2 = page2.evaluate(PIN_BTN_JS)
        ws2 = next((i for i in pin2['items']
                    if i['key'] == 'work-schedule'), None)
        check('десктоп: кнопка work-schedule закреплена', ws2 is not None)
        if ws2:
            check('десктоп: метка — «Табель учёта»',
                  ws2['label'] == 'Табель учёта', ws2['label'])
            check('десктоп: кнопка видима', ws2['visible'])
        shot(page2, 'd-desktop-dashboard-pin.png')
        ctx2.close()

        browser.close()

        print('== ИТОГ: %d OK, %d FAIL ==' % (PASS, FAIL))
        if errors:
            print('JS-ОШИБКИ (%d):' % len(errors))
            for e in errors[:10]:
                print('  ! ' + e[:300])
        else:
            print('JS-ОШИБКИ: 0')
        return 0 if (FAIL == 0 and not errors) else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
