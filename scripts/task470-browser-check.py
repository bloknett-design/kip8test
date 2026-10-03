#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 470: browser-check — таблица «Плановых мероприятий»:
#   1) «Ноя.» — точка в конце сокращения ноября в шапке месяцев;
#   2) в группу «В конце месяца» добавлено мероприятие «Работы
#      на следующий месяц» (последней строкой группы);
#   3) НОВАЯ группа «На текущий месяц» с мероприятием «Работы
#      на месяц» (внизу таблицы).
# Отметки Task 463 работают по наименованию из DOM — новые строки
# автоматически кликабельны: клик по ячейке новой строки открывает
# диалог «Отметка выполнения» с правильным наименованием.
# ПРОВЕРКИ (мок-сервер, порт 8999):
#   A: широкий 1600 — шапка месяцев (Ноя. с точкой, 12 колонок),
#      структура: 3 группы, 10 строк, порядок и вхождение новых;
#      иконки-крестики во ВСЕХ 120 ячейках (включая новые строки);
#      раскладка Task 468 жива; 0 переполнений;
#   B: клики по ячейкам НОВЫХ строк — диалог «Отметка выполнения»
#      с наименованиями «Работы на следующий месяц» / «Работы на
#      месяц» и месяцем «Ноябрь 2026», дата = сегодня; «Отмена»;
#      запросов planEvents.mark НЕ уходило;
#   C: узкий 1100 (< 1200) — колонка, таблица с новой группой;
#   D: мобильный 375 — Task 464 жив: один видимый месяц у ВСЕХ
#      10 строк (включая новые); 0 JS-ошибок во всех сценариях.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'download', 'kip8test-task470')


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'planEvents.list':
        return {'ok': True, 'data': {'marks': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


PASS = 0
FAIL = 0
MARK_CALLS = []


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:260] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def open_section(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('plan-events')")
    page.wait_for_timeout(1200)


# Структура таблицы: месяцы, группы, строки, иконки ячеек
def table_state(page):
    return page.evaluate("""(() => {
        const table = document.querySelector('#peTable');
        const months = [...table.querySelectorAll('tr.pe-head-months th')]
            .map(th => th.textContent.trim());
        const groups = [...table.querySelectorAll('tr.pe-group td')]
            .map(td => td.textContent.trim());
        const rows = [...table.querySelectorAll('tbody tr.pe-row')].map(tr => ({
            name: tr.querySelector('td.pe-name').textContent.trim(),
            cells: tr.querySelectorAll('td.pe-m').length,
            icons: [...tr.querySelectorAll('td.pe-m svg')].length,
            noEvents: [...tr.querySelectorAll('td.pe-m')]
                .filter(td => getComputedStyle(td).display !== 'none'
                    && td.getBoundingClientRect().width > 0).length}));
        const groupPos = [...table.querySelectorAll('tbody tr')].map(tr =>
            tr.classList.contains('pe-group')
                ? tr.querySelector('td').textContent.trim() : null);
        return {months: months, groups: groups, rows: rows, seq: groupPos,
                docW: document.documentElement.scrollWidth,
                winW: window.innerWidth};})()""")


def main():
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t470');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            url = request.url
            action = ''
            if 'action=' in url:
                action = unquote(url.split('action=')[1].split('&')[0])
            pd_ = request.post_data
            body = {}
            if pd_:
                try:
                    body = json.loads(pd_)
                except Exception:
                    body = {}
            if action == 'planEvents.mark':
                MARK_CALLS.append(body)
            resp = mock_response(action, body)
            return route.fulfill(status=200,
                                 content_type='application/json; charset=utf-8',
                                 body=json.dumps(resp, ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        # ===== A: широкий 1600 — шапка, структура, иконки
        print('== A: 1600px — «Ноя.», новые строки, структура таблицы ==')
        open_section(page)
        st = table_state(page)
        check('шапка: ровно 12 месяцев', len(st['months']) == 12, st['months'])
        check('ноябрь — «Ноя.» с точкой (11-я колонка)',
              len(st['months']) == 12 and st['months'][10] == 'Ноя.',
              st['months'])
        check('сокращения ноября без точки в шапке НЕТ',
              all(m != 'Ноя' for m in st['months']), st['months'])
        check('«Май» без точки (полное слово, не тронуто)',
              len(st['months']) == 12 and st['months'][4] == 'Май', st['months'])
        check('3 группы: В начале / В конце / На текущий месяц',
              st['groups'] == ['В начале месяца', 'В конце месяца',
                              'На текущий месяц'], st['groups'])
        check('ровно 10 строк мероприятий',
              len(st['rows']) == 10, len(st['rows']))
        check('9-я строка — «Работы на следующий месяц» (в группе «В конце месяца»)',
              len(st['rows']) == 10 and st['rows'][8]['name'] == 'Работы на следующий месяц',
              [r['name'] for r in st['rows']])
        check('10-я строка — «Работы на месяц» (группа «На текущий месяц»)',
              len(st['rows']) == 10 and st['rows'][9]['name'] == 'Работы на месяц',
              [r['name'] for r in st['rows']])
        check('порядок в DOM: …В конце месяца → Работы на следующий месяц → '
              'На текущий месяц → Работы на месяц',
              st['seq'].count('В начале месяца') == 1 and
              st['seq'].count('В конце месяца') == 1 and
              st['seq'].count('На текущий месяц') == 1 and
              st['seq'].index('В конце месяца') < st['seq'].index('На текущий месяц') and
              st['seq'][-1] is None and st['seq'][-2] == 'На текущий месяц' and
              st['seq'][st['seq'].index('В конце месяца') + 1] is None,
              st['seq'])
        check('новые строки: по 12 ячеек месяцев',
              len(st['rows']) == 10 and st['rows'][8]['cells'] == 12 and
              st['rows'][9]['cells'] == 12,
              [st['rows'][8], st['rows'][9]])
        check('иконки-крестики во ВСЕХ ячейках: 10 × 12 = 120 (Task 463 жив)',
              all(r['icons'] == 12 for r in st['rows']) and len(st['rows']) == 10,
              [(r['name'], r['icons']) for r in st['rows']])
        check('нет горизонтального переполнения страницы',
              st['docW'] <= st['winW'] + 1, st)
        g = page.evaluate("""(() => {
            const lay = document.querySelector('#page-plan-events .pe-layout');
            const card = lay.querySelector('.pe-card');
            const desc = lay.querySelector('.pe-desc-card');
            const table = lay.querySelector('.pe-table');
            const cr = card.getBoundingClientRect(), dr = desc.getBoundingClientRect();
            const tr = table.getBoundingClientRect();
            return {dir: getComputedStyle(lay).flexDirection,
                    cardL: +cr.left.toFixed(1), cardR: +cr.right.toFixed(1),
                    cardW: +cr.width.toFixed(1), tabW: +tr.width.toFixed(1),
                    descL: +dr.left.toFixed(1)};})()""")
        check('раскладка Task 468 жива: строка, карточка влево, окно справа',
              g['dir'] == 'row' and g['cardL'] < g['descL'] and g['descL'] >= g['cardR'] - 1, g)
        check('карточка обнимает таблицу (cardW - tabW <= 3)',
              g['cardW'] - g['tabW'] <= 3, g)
        shot(page, 'a-desktop-1600.png')

        # ===== B: клики по ячейкам НОВЫХ строк — диалог Task 463
        print('== B: клики по новым строкам — диалог «Отметка выполнения» ==')

        def dialog_probe(row_name, month_idx):
            # клик по ячейке month_idx (0-based) строки с наименованием row_name;
            # 'active' добавляется через requestAnimationFrame — даём кадру выпасть
            r = page.evaluate("""([rn, mi]) => {
                const tr = [...document.querySelectorAll('#peTable tbody tr.pe-row')]
                    .find(r => r.querySelector('td.pe-name').textContent.trim() === rn);
                if (!tr) return {open: false, err: 'строка не найдена: ' + rn};
                const td = tr.querySelectorAll('td.pe-m')[mi];
                td.click();
                return {open: true};}""", [row_name, month_idx])
            page.wait_for_timeout(300)
            return r

        def dialog_state():
            return page.evaluate("""(() => {
                const ov = document.getElementById('kipDialogOverlay');
                if (!ov || !ov.classList.contains('active')) return {open: false};
                const title = ov.querySelector('.kip-dialog-title');
                const msg = ov.querySelector('.kip-dialog-msg');
                const date = ov.querySelector('#peDialogDate');
                return {open: true,
                        title: title ? title.textContent.trim() : '',
                        msg: msg ? msg.textContent.trim() : '',
                        date: date ? date.value : ''};})()""")

        def dialog_cancel():
            page.evaluate("""(() => {
                const ov = document.getElementById('kipDialogOverlay');
                const b = ov.querySelector('.kip-dialog-cancel');
                if (b) b.click();})()""")
            page.wait_for_timeout(450)

        today = page.evaluate("""(() => {
            const d = new Date();
            const m = d.getMonth() + 1, dd = d.getDate();
            return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m +
                   '-' + (dd < 10 ? '0' : '') + dd;})()""")

        probe = dialog_probe('Работы на месяц', 10)   # ноябрь
        check('клик по ячейке ноября строки «Работы на месяц» принят', probe.get('open'), probe)
        ds = dialog_state()
        check('диалог «Отметка выполнения» открыт',
              ds.get('open') and ds.get('title') == 'Отметка выполнения', ds)
        check('сообщение: «Работы на месяц — Ноябрь 2026»',
              ds.get('msg') == 'Работы на месяц — Ноябрь 2026', ds.get('msg'))
        check('дата по умолчанию — сегодняшняя', ds.get('date') == today, ds)
        dialog_cancel()
        closed = page.evaluate("""(() => {
            const ov = document.getElementById('kipDialogOverlay');
            if (!ov) return true;
            return !ov.classList.contains('active') &&
                   !ov.querySelector('.pe-dialog');})()""")
        check('диалог закрыт («Отмена»)', closed)

        probe = dialog_probe('Работы на следующий месяц', 10)   # ноябрь
        check('клик по ячейке строки «Работы на следующий месяц» принят',
              probe.get('open'), probe)
        ds = dialog_state()
        check('диалог открыт: «Работы на следующий месяц — Ноябрь 2026»',
              ds.get('open') and
              ds.get('msg') == 'Работы на следующий месяц — Ноябрь 2026', ds)
        dialog_cancel()
        closed = page.evaluate("""(() => {
            const ov = document.getElementById('kipDialogOverlay');
            if (!ov) return true;
            return !ov.classList.contains('active') &&
                   !ov.querySelector('.pe-dialog');})()""")
        check('диалог закрыт («Отмена»)', closed)
        check('запросов planEvents.mark НЕ уходило (только отмена)',
              len(MARK_CALLS) == 0, MARK_CALLS)
        shot(page, 'b-dialog-not-opened.png')

        # ===== C: узкий вьюпорт 1100 (< 1200) — колонка
        print('== C: 1100px (< 1200) — раскладка в колонку, таблица цела ==')
        page.set_viewport_size({'width': 1100, 'height': 900})
        page.wait_for_timeout(500)
        st = table_state(page)
        check('таблица цела в колонке: 3 группы / 10 строк',
              st['groups'] == ['В начале месяца', 'В конце месяца',
                              'На текущий месяц'] and len(st['rows']) == 10,
              (st['groups'], len(st['rows'])))
        check('«Ноя.» на месте в колонке',
              len(st['months']) == 12 and st['months'][10] == 'Ноя.', st['months'])
        below = page.evaluate("""(() => {
            const lay = document.querySelector('#page-plan-events .pe-layout');
            const card = lay.querySelector('.pe-card');
            const desc = lay.querySelector('.pe-desc-card');
            return desc.getBoundingClientRect().top >=
                   card.getBoundingClientRect().bottom - 1;})()""")
        check('описание ПОД таблицей (Task 468 не тронут)', below)
        shot(page, 'c-narrow-1100.png')

        # ===== D: мобильный 375 — Task 464 жив, новые строки включены
        print('== D: 375px — мобильный вид (один месяц у 10 строк) ==')
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(600)
        m = page.evaluate("""(() => {
            const bar = document.querySelector('#page-plan-events .pe-month-bar');
            const table = document.querySelector('#peTable');
            const sel = document.getElementById('peMonthSel');
            const visMonths = [...table.querySelectorAll('td.pe-m')]
                .filter(td => getComputedStyle(td).display !== 'none'
                    && td.getBoundingClientRect().width > 0
                    && td.parentElement.getBoundingClientRect().width > 0).length;
            const lastRow = [...table.querySelectorAll('tbody tr.pe-row')]
                .pop().querySelector('td.pe-name').textContent.trim();
            return {barVisible: bar ? getComputedStyle(bar).display !== 'none' : false,
                    selOptions: sel ? sel.options.length : 0,
                    visMonths: visMonths, lastRow: lastRow,
                    nov: table.querySelector('tr.pe-head-months').children[10].textContent};})()""")
        check('полоса выбора месяца видна (Task 464)', m.get('barVisible'), m)
        check('селектор месяца заполнен (12 опций)', m.get('selOptions') == 12, m)
        check('видимые ячейки: 10 строк × 1 месяц = 10 (было 8)',
              m.get('visMonths') == 10, m)
        check('последняя строка на мобайле — «Работы на месяц»',
              m.get('lastRow') == 'Работы на месяц', m)
        check('«Ноя.» в шапке на мобайле', m.get('nov') == 'Ноя.', m)
        st = table_state(page)
        check('нет горизонтального переполнения страницы',
              st['docW'] <= st['winW'] + 1, (st['docW'], st['winW']))
        shot(page, 'd-mobile-375.png')

        # ===== светлая тема (визуальный артефакт)
        page.set_viewport_size({'width': 1600, 'height': 1000})
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(400)
        shot(page, 'e-light-1600.png')
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(200)

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d OK / %d FAIL' % (PASS, FAIL))
    if js_errors:
        print('JS-ОШИБКИ (%d):' % len(js_errors))
        for e in js_errors[:10]:
            print('  ! ' + e[:300])
    else:
        print('JS-ошибок нет (0)')
    raise SystemExit(1 if (FAIL or js_errors) else 0)


if __name__ == '__main__':
    main()
