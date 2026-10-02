#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 460: browser-check — заявка: «Теперь необходимо создать новый
# раздел "Плановые мероприятия" в разделе Документация ИОС. На странице
# нового раздела необходимо разместить информацию в виде таблицы по
# образцу приложенному в файле» («Пример таблицы мероприятий.xlsx»).
# КОНТЕКСТ (мок-сервер, порт 8992):
#   A: десктоп 1280 тёмная, Админ — «Документация» → «Документация
#      ИОС»: ТРИ кнопки (Расходомеры / Табель / Плановые мероприятия);
#      закрепление (subsection-cell) на docs-ios;
#   B: ЗАЯВКА — клик «Плановые мероприятия»: страница, крошки «Главная /
#      Документация / Документация ИОС / Плановые мероприятия»;
#      таблица ПО ОБРАЗЦУ: «Мероприятия» rowspan 2 + «2026 год»
#      colspan 12, 12 месяцев («Фев.», БЕЗ опечатки «Феф.»), группы
#      «В начале месяца» (3) / «В конце месяца» (5), 8 мероприятий
#      в порядке образца, 96 ПУСТЫХ ячеек месяцев, сетка рамок,
#      зебра строк, шапка #1e293b;
#   C: сайдбар — пункт «Плановые мероприятия» в группе «Документация
#      ИОС», клик ведёт на страницу;
#   D: светлая тема — шапка #bfcad5, границы rgb(83, 96, 117);
#   E: мобайл 375 — горизонтальная прокрутка сетки (scrollWidth >
#      clientWidth), скролл до декабря, 0 JS-ошибок;
#   F: роли — «КИП8» (без ИОС): кнопка «Документация ИОС» скрыта;
#      «КИП8 pro» (flowmeter.view без КИП ИОС): «Плановые
#      мероприятия» ВИДИМЫ и открываются;
#   G: 0 JS-ошибок во всех контекстах; скриншоты в
#      download/kip8test-task460/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8992

MONTHS_SAMPLE = ['Янв.', 'Фев.', 'Мар.', 'Апр.', 'Май', 'Июн.',
                 'Июл.', 'Авг.', 'Сен.', 'Окт.', 'Ноя', 'Дек.']
GROUPS_SAMPLE = [
    ('В начале месяца', ['Проверка электроинструмента (приспособлений)',
                         'Проверка СИЗ в электроустановках',
                         'Проверка огнетушителей']),
    ('В конце месяца', ['График смен на следующий месяц',
                        'Отчёт по талонам',
                        'Выписка из ППР на следующий месяц',
                        'Журнал учёта электрооборудования',
                        'Отчёт по графику ППР']),
]
ALL_ACTS = GROUPS_SAMPLE[0][1] + GROUPS_SAMPLE[1][1]

PASS = 0
FAIL = 0
SHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        '..', 'download', 'kip8test-task460')


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def api_response(action, body, role, perms):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': role}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': role, 'found': True,
                'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, role='Админ', perms=None):
    """Мок API + тема + токен. perms=None → полный набор Админа."""
    if perms is None:
        perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                 'workschedule.view': True, 'workschedule.edit': True,
                 'flowmeter.view': True, 'whatsnew.view': True}
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t460-%s');" % tag +
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
        resp = api_response(action, body, role, perms)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t460-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== A/B/C: десктоп 1280, тёмная, Админ =====
        print('=== Контекст A: десктоп тёмная, Админ — «Документация ИОС» ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось (дашборд)',
              page.evaluate("!!document.querySelector('#page-dashboard.active')"))

        page.evaluate("navigateTo('docs')")
        page.wait_for_timeout(400)
        # Кнопка «Документация ИОС» на странице «Документация»
        docs_ios_btn = page.evaluate("""(() => {
            const btns = document.querySelectorAll('#page-docs .menu-btn');
            for (const b of btns) {
                if ((b.getAttribute('onclick')||'').indexOf('docs-ios') !== -1)
                    return {vis: b.style.display !== 'none',
                            txt: b.innerText.replace(/\\s+/g,' ').trim()};
            }
            return null;})()""")
        check('A2: кнопка «Документация ИОС» на странице «Документация»',
              docs_ios_btn and docs_ios_btn['vis'] and
              'Документация ИОС' in docs_ios_btn['txt'], docs_ios_btn)

        page.evaluate("navigateTo('docs-ios')")
        page.wait_for_timeout(400)
        hub = page.evaluate("""(() => {
            const res = {};
            const fl = document.getElementById('flowmeterMenuBtn');
            const ws = document.getElementById('workScheduleMenuBtn');
            const pe = document.getElementById('planEventsMenuBtn');
            res.fl = fl ? fl.style.display !== 'none' : null;
            res.ws = ws ? ws.style.display !== 'none' : null;
            res.pe = pe ? pe.style.display !== 'none' : null;
            res.peTxt = pe ? pe.innerText.replace(/\\s+/g,' ').trim() : '';
            // закрепление: обёртка subsection-cell (wrapSubsectionItems)
            res.wrap = !!document.querySelector(
                '.subsection-cell[data-subsection-key="plan-events"]');
            return res;})()""")
        check('A3: на «Документации ИОС» ТРИ видимые кнопки (расходомеры/табель/план)',
              hub['fl'] and hub['ws'] and hub['pe'], hub)
        check('A4: label/sublabel кнопки — «Плановые мероприятия»',
              hub['peTxt'].startswith('Плановые мероприятия') and
              'Периодические работы по месяцам года' in hub['peTxt'], hub['peTxt'])
        check('A5: кнопка обёрнута для закрепления на главной (subsection-cell)',
              hub['wrap'])

        print('=== Контекст B: ЗАЯВКА — страница «Плановые мероприятия» ===')
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(600)
        check('B1: страница активна',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))

        # крошки десктопа: Главная / Документация / Документация ИОС / Плановые мероприятия
        crumbs = page.evaluate("""(() => {
            const t = document.querySelector('#page-plan-events .page-inline-header-title');
            return t ? t.innerText.replace(/\\s+/g,' ').trim() : '';})()""")
        check('B2: крошки «Главная / Документация / Документация ИОС / Плановые мероприятия»',
              'Главная' in crumbs and 'Документация ИОС' in crumbs and
              'Плановые мероприятия' in crumbs, crumbs)

        tbl = page.evaluate("""(() => {
            const pageEl = document.getElementById('page-plan-events');
            const table = pageEl.querySelector('table.pe-table');
            if (!table) return null;
            const res = {};
            // шапка
            const ths = Array.from(table.querySelectorAll('thead th'))
                .map(th => th.textContent.trim());
            res.head = ths;
            res.nameRowspan = table.querySelector('th.pe-th-name').rowSpan;
            res.yearColspan = table.querySelector('th.pe-th-year').colSpan;
            // группы и строки
            res.groups = Array.from(table.querySelectorAll('tr.pe-group td'))
                .map(td => td.textContent.trim());
            res.acts = Array.from(table.querySelectorAll('td.pe-name'))
                .map(td => td.textContent.trim());
            res.emptyCnt = table.querySelectorAll('td.pe-m').length;
            res.emptyTexts = Array.from(table.querySelectorAll('td.pe-m'))
                .map(td => td.textContent.trim()).filter(t => t !== '').length;
            // рамки: у ячейки месяца есть граница
            const m = table.querySelector('td.pe-m');
            const cs = getComputedStyle(m);
            res.border = cs.borderTopWidth !== '0px' && cs.borderTopStyle !== 'none';
            // шапка: стальной фон
            const th = table.querySelector('thead th');
            res.thBg = getComputedStyle(th).backgroundColor;
            // зебра: фон чёт/нечёт строк отличается
            const rows = Array.from(table.querySelectorAll('tr.pe-row'));
            res.zebra = rows.length >= 2 &&
                getComputedStyle(rows[0].querySelector('td')).backgroundColor !==
                getComputedStyle(rows[1].querySelector('td')).backgroundColor;
            res.rowCnt = rows.length;
            // группа: жирная
            const g = table.querySelector('tr.pe-group td');
            res.groupBold = getComputedStyle(g).fontWeight;
            return res;})()""")
        check('B3: шапка «Мероприятия» + «2026 год» + 12 месяцев',
              tbl['head'][0] == 'Мероприятия' and tbl['head'][1] == '2026 год' and
              tbl['head'][2:] == MONTHS_SAMPLE, tbl['head'])
        check('B4: «Фев.» — опечатки образца «Фев.»/«Феф.» нет',
              tbl['head'][3] == 'Фев.' and 'Феф.' not in tbl['head'], tbl['head'][2:5])
        check('B5: «Мероприятия» rowspan 2, «2026 год» colspan 12 (merge образца)',
              tbl['nameRowspan'] == 2 and tbl['yearColspan'] == 12,
              (tbl['nameRowspan'], tbl['yearColspan']))
        check('B6: группы «В начале месяца» / «В конце месяца»',
              tbl['groups'] == [GROUPS_SAMPLE[0][0], GROUPS_SAMPLE[1][0]],
              tbl['groups'])
        check('B7: 8 мероприятий в порядке образца',
              tbl['acts'] == ALL_ACTS, tbl['acts'])
        check('B8: 96 ПУСТЫХ ячеек месяцев (без текста)',
              tbl['emptyCnt'] == 96 and tbl['emptyTexts'] == 0,
              (tbl['emptyCnt'], tbl['emptyTexts']))
        check('B9: сетка с рамками (границы ячеек)',
              tbl['border'], '')
        check('B10: шапка — стальной фон #1e293b (канон Task 330)',
              tbl['thBg'] == 'rgb(30, 41, 59)', tbl['thBg'])
        check('B11: зебра строк (чёт/нечёт отличаются)',
              tbl['zebra'] and tbl['rowCnt'] == 8)
        check('B12: группы — жирный текст',
              tbl['groupBold'] == '700' or tbl['groupBold'] == 'bold', tbl['groupBold'])
        shot(page, '01-desktop-dark.png')

        print('=== Контекст C: сайдбар ===')
        page.evaluate("toggleSidebar()")
        page.wait_for_timeout(400)
        side = page.evaluate("""(() => {
            const items = document.querySelectorAll('.sidebar-item');
            for (const it of items) {
                const oc = it.getAttribute('onclick') || '';
                if (oc.indexOf("navigateTo('plan-events')") !== -1) {
                    return {vis: it.style.display !== 'none',
                            txt: it.innerText.trim()};
                }
            }
            return null;})()""")
        check('C1: пункт «Плановые мероприятия» в сайдбаре (виден)',
              side and side['vis'] and side['txt'] == 'Плановые мероприятия', side)
        # клик по пункту сайдбара ведёт на страницу
        page.evaluate("""(() => {
            const items = document.querySelectorAll('.sidebar-item');
            for (const it of items) {
                const oc = it.getAttribute('onclick') || '';
                if (oc.indexOf("navigateTo('plan-events')") !== -1) { it.click(); return; }
            }})()""")
        page.wait_for_timeout(500)
        check('C2: клик пункта сайдбара открывает страницу',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        check('C3: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
        ctx.close()

        # ===== D: светлая тема =====
        print('=== Контекст D: светлая тема ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js2 = attach(page2, ctx2, 'light', 'light')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('plan-events')")
        page2.wait_for_timeout(600)
        light = page2.evaluate("""(() => {
            const table = document.querySelector('#page-plan-events table.pe-table');
            if (!table) return null;
            const th = table.querySelector('thead th');
            const td = table.querySelector('td.pe-m');
            return {thBg: getComputedStyle(th).backgroundColor,
                    thColor: getComputedStyle(th).color,
                    border: getComputedStyle(td).borderTopColor,
                    txt: getComputedStyle(table).color};})()""")
        check('D1: светлая тема — шапка #bfcad5, тёмный текст',
              light['thBg'] == 'rgb(191, 202, 213)' and light['thColor'] == 'rgb(51, 51, 51)',
              light)
        check('D2: границы светлой темы rgb(83, 96, 117)',
              light['border'] == 'rgb(83, 96, 117)', light['border'])
        shot(page2, '02-desktop-light.png')
        check('D3: 0 JS-ошибок (светлая)', len(js2) == 0, js2[:3])
        ctx2.close()

        # ===== E: мобайл 375 =====
        print('=== Контекст E: мобайл 375 ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720})
        page3 = ctx3.new_page()
        js3 = attach(page3, ctx3, 'dark', 'mob')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        # естественный путь: docs → docs-ios → план
        page3.evaluate("navigateTo('docs-ios')")
        page3.wait_for_timeout(400)
        tap = page3.evaluate("""(() => {
            const b = document.getElementById('planEventsMenuBtn');
            if (!b || b.style.display === 'none') return false;
            b.click(); return true;})()""")
        page3.wait_for_timeout(600)
        check('E1: мобайл — кнопка на «Документации ИОС» открывает страницу',
              tap and page3.evaluate("!!document.querySelector('#page-plan-events.active')"))
        mob = page3.evaluate("""(() => {
            const wrap = document.querySelector('#page-plan-events .pe-grid-wrap');
            if (!wrap) return null;
            return {sw: wrap.scrollWidth, cw: wrap.clientWidth,
                    overflow: getComputedStyle(wrap).overflowX};})()""")
        check('E2: сетка шире экрана — горизонтальная прокрутка',
              mob['sw'] > mob['cw'] and mob['overflow'] in ('auto', 'scroll'), mob)
        # скролл до правого края — декабрь виден, таблица не разъехалась
        page3.evaluate("""document.querySelector('#page-plan-events .pe-grid-wrap')
            .scrollLeft = 99999""")
        page3.wait_for_timeout(300)
        dec = page3.evaluate("""(() => {
            const ths = document.querySelectorAll(
                '#page-plan-events thead tr:last-child th');
            const last = ths[ths.length - 1];
            const r = last.getBoundingClientRect();
            return {txt: last.textContent.trim(), x: Math.round(r.right)};})()""")
        check('E3: скролл до декабря (последний месяц в вьюпорте)',
              dec['txt'] == 'Дек.' and dec['x'] <= 375, dec)
        check('E4: 0 JS-ошибок (мобайл)', len(js3) == 0, js3[:3])
        shot(page3, '03-mobile-375.png')
        ctx3.close()

        # ===== F: роли =====
        print('=== Контекст F: роли (КИП8 — нет ИОС; КИП8 pro — flowmeter без ИОС) ===')
        # КИП8: без КИП ИОС и расходомеров — кнопки «Документация ИОС» нет
        ctx4 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page4 = ctx4.new_page()
        attach(page4, ctx4, 'dark', 'k8', role='КИП8',
               perms={'calc.view': True, 'library.view': True, 'whatsnew.view': True})
        page4.goto('http://localhost:%d/index.html' % PORT)
        page4.wait_for_timeout(2500)
        page4.evaluate("navigateTo('docs')")
        page4.wait_for_timeout(400)
        hid = page4.evaluate("""(() => {
            const btns = document.querySelectorAll('#page-docs .menu-btn');
            for (const b of btns) {
                if ((b.getAttribute('onclick')||'').indexOf('docs-ios') !== -1)
                    return b.style.display === 'none';
            }
            return true;})()""")
        check('F1: «КИП8» — кнопка «Документация ИОС» скрыта (без доступа)',
              hid)
        ctx4.close()

        # КИП8 pro: flowmeter.view, без КИП ИОС — «Плановые мероприятия» ВИДИМЫ
        ctx5 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page5 = ctx5.new_page()
        js5 = attach(page5, ctx5, 'dark', 'k8pro', role='КИП8 pro',
                     perms={'calc.view': True, 'library.view': True,
                            'whatsnew.view': True, 'flowmeter.view': True})
        page5.goto('http://localhost:%d/index.html' % PORT)
        page5.wait_for_timeout(2500)
        page5.evaluate("navigateTo('docs-ios')")
        page5.wait_for_timeout(400)
        k8pro = page5.evaluate("""(() => {
            const pe = document.getElementById('planEventsMenuBtn');
            return {vis: pe && pe.style.display !== 'none'};})()""")
        check('F2: «КИП8 pro» — «Плановые мероприятия» ВИДИМЫ (страница идёт с хабом)',
              k8pro['vis'], k8pro)
        page5.evaluate("navigateTo('plan-events')")
        page5.wait_for_timeout(500)
        check('F3: «КИП8 pro» — страница открывается',
              page5.evaluate("!!document.querySelector('#page-plan-events.active')"))
        check('F4: 0 JS-ошибок (роли)', len(js5) == 0, js5[:3])
        ctx5.close()

        browser.close()

    print('-' * 60)
    print('ИТОГ Task 460 browser-check: %d passed / %d failed' % (PASS, FAIL))
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
    import threading
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
