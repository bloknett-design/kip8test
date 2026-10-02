#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 464: browser-check — правка/снятие отметок «Плановых
# мероприятий», кнопки диалога, ширина колонки по тексту,
# мобильная компактность (селектор месяца + один столбец).
# Заявка: «...Краткую инструкцию над таблицей убери. Ширину
# столбца с мероприятиями сделай по тексту в нём. В диалоговом
# окне подтверждения отметки, кнопку "Отмена" подкрась немного в
# красный, а кнопку "Отметить" переименуй в "Подтвердить". После
# выполнения отметки сделай возможность отредактировать дату и
# отменить выполнение отметки. В мобильной версии, для компактности,
# оставляй только столбец с мероприятиями и текущий месяц, с
# возможностью выбора месяца.»
# КОНТЕКСТ (мок-сервер, порт 8996; STATEFUL — update/unmark пишут
# в стор):
#   A: подсказки нет; селектор месяца скрыт на десктопе; колонка
#      мероприятий nowrap; клик по пустой → диалог с [Отмена
#      pe-cancel-red][Подтвердить]; Отмена → mark НЕ вызван;
#      Подтвердить → mark → зелёная галочка + тост;
#   B: клик по отмеченной → диалог «Изменение отметки» (дата
#      prefilled, три кнопки); Отмена → ничего; смена даты →
#      «Сохранить дату» → planEvents.update payload → title
#      обновился + тост «Дата отметки обновлена»;
#   C: «Удалить отметку» → planEvents.unmark (без date) → ячейка
#      крестик + тост «Отметка снята»; повторное открытие —
#      отметки нет (stateful);
#   D: ошибка сервера update (sheet_not_found) → тост, дата не
#      изменилась; not_found → тост с сообщением сервера; ошибка
#      unmark → тост, галочка осталась;
#   E: идемпотентность mark (already) — тост «Отметка уже была
#      сохранена» (скрытая отметка);
#   F: мобайл 375 светлая: селектор виден = текущий месяц; виден
#      ТОЛЬКО столбец текущего месяца (шапка+ячейки); выбор
#      «Декабрь» переключает столбец; отметка в декабре;
#      0 JS-ошибок;
#   G: кнопка «Обновить» — повторный list (smoke).
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8996

PASS = 0
FAIL = 0
SHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        '..', 'download', 'kip8test-task464')

# Мок-состояние «сервера» (stateful)
STATE = {
    'marks': [],      # видимые list-ом
    'hidden': [],     # только для already (контекст E)
    'next_id': 1,
    'log': [],
    'mode': 'normal',  # normal | error | unknown_action | not_found
}


def today_iso():
    return datetime.date.today().isoformat()


def mark_by_key(marks, year, month, event):
    for m in marks:
        if m['год'] == year and m['месяц'] == month and m['мероприятие'] == event:
            return m
    return None


def api_response(action, body):
    st = STATE
    st['log'].append({'action': action, 'body': body})
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'КИП ИОС'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'КИП ИОС', 'found': True,
                'permissions': {'kipios.view': True, 'plan.events': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'planEvents.list':
        if st['mode'] == 'unknown_action':
            return {'ok': False, 'error': 'Unknown action: planEvents.list'}
        return {'ok': True, 'data': {'marks': st['marks'], 'srvVer': '464'}}
    if action == 'planEvents.mark':
        if st['mode'] == 'unknown_action':
            return {'ok': False, 'error': 'Unknown action: planEvents.mark'}
        if st['mode'] == 'error':
            return {'ok': False, 'error': 'sheet_not_found',
                    'message': 'Лист «Архив» не найден — запустите planEventsDeploy()'}
        year = body.get('year')
        month = body.get('month')
        event = body.get('event')
        date = body.get('date')
        exist = mark_by_key(st['marks'], year, month, event) or \
                mark_by_key(st['hidden'], year, month, event)
        if exist:
            return {'ok': True, 'data': {'mark': exist, 'already': True}}
        m = {'id': st['next_id'], 'дата_выполнения': date,
             'мероприятие': event, 'год': year, 'месяц': month}
        st['next_id'] += 1
        st['marks'].append(m)
        return {'ok': True, 'data': {'mark': m, 'already': False}}
    if action == 'planEvents.update':
        if st['mode'] == 'unknown_action':
            return {'ok': False, 'error': 'Unknown action: planEvents.update'}
        if st['mode'] == 'error':
            return {'ok': False, 'error': 'sheet_not_found',
                    'message': 'Лист «Архив» не найден — запустите planEventsDeploy()'}
        if st['mode'] == 'not_found':
            return {'ok': False, 'error': 'not_found',
                    'message': 'Отметка не найдена — возможно, её уже сняли. Нажмите «Обновить» в шапке раздела'}
        year = body.get('year')
        month = body.get('month')
        event = body.get('event')
        date = body.get('date')
        exist = mark_by_key(st['marks'], year, month, event)
        if not exist:
            return {'ok': False, 'error': 'not_found',
                    'message': 'Отметка не найдена — возможно, её уже сняли. Нажмите «Обновить» в шапке раздела'}
        exist['дата_выполнения'] = date
        return {'ok': True, 'data': {'mark': exist}}
    if action == 'planEvents.unmark':
        if st['mode'] == 'unknown_action':
            return {'ok': False, 'error': 'Unknown action: planEvents.unmark'}
        if st['mode'] == 'error':
            return {'ok': False, 'error': 'sheet_not_found',
                    'message': 'Лист «Архив» не найден — запустите planEventsDeploy()'}
        year = body.get('year')
        month = body.get('month')
        event = body.get('event')
        exist = mark_by_key(st['marks'], year, month, event)
        if exist:
            st['marks'].remove(exist)
            return {'ok': True, 'data': {'removed': True}}
        return {'ok': True, 'data': {'removed': False}}
    return {'ok': True, 'data': {'ok': True}}


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def attach(page, ctx, theme, tag):
    """Мок API + тема + токен; возвращает список JS-ошибок."""
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t464-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

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
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t464-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def open_plan_events(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('plan-events')")
    page.wait_for_timeout(700)


def toast_text(page):
    return page.evaluate("""(() => {
        const t = document.getElementById('toast');
        const m = document.getElementById('toastMessage');
        return {shown: !!(t && t.classList.contains('show')),
                text: m ? m.textContent : ''};})()""")


def count_actions(action):
    return len([l for l in STATE['log'] if l['action'] == action])


def last_body(action):
    acts = [l['body'] for l in STATE['log'] if l['action'] == action]
    return acts[-1] if acts else None


def cell_by_event_month(page, event, month):
    """Состояние td.pe-m строки мероприятия по месяцу (1..12)."""
    return page.evaluate("""(([ev, mn]) => {
        const rows = document.querySelectorAll('#peTable tbody tr.pe-row');
        for (const tr of rows) {
            const nm = tr.querySelector('td.pe-name');
            if (!nm || nm.textContent.trim() !== ev) continue;
            const td = tr.querySelectorAll('td.pe-m')[mn - 1];
            if (!td) return null;
            return {'pe-m-done': td.classList.contains('pe-m-done'),
                    'pe-m-busy': td.classList.contains('pe-m-busy'),
                    'pe-mo-off': td.classList.contains('pe-mo-off'),
                    'visible': !!td.offsetParent,
                    hasCheck: !!td.querySelector('.pe-ic-check'),
                    hasCross: !!td.querySelector('.pe-ic-cross'),
                    'white-space': getComputedStyle(td.closest('tr').querySelector('.pe-name')).whiteSpace,
                    title: td.getAttribute('title') || ''};
        }
        return null;})""", [event, month])


def click_cell(page, event, month):
    page.evaluate("""(([ev, mn]) => {
        const rows = document.querySelectorAll('#peTable tbody tr.pe-row');
        for (const tr of rows) {
            const nm = tr.querySelector('td.pe-name');
            if (!nm || nm.textContent.trim() !== ev) continue;
            const td = tr.querySelectorAll('td.pe-m')[mn - 1];
            if (td) td.click();
        }})""", [event, month])


def dialog_state(page):
    return page.evaluate("""(() => {
        const ov = document.getElementById('kipDialogOverlay');
        const d = ov ? ov.querySelector('.pe-dialog') : null;
        if (!d) return null;
        const btns = [...d.querySelectorAll('.kip-dialog-btn')].map(b => ({
            text: b.textContent.trim(), cls: b.className}));
        return {title: (d.querySelector('.kip-dialog-title')||{}).textContent || '',
                msg: (d.querySelector('.kip-dialog-msg')||{}).textContent || '',
                date: (d.querySelector('#peDialogDate')||{}).value || '',
                btns: btns};})()""")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== A: десктоп — подсказки нет, диалог с новыми кнопками =====
        print('=== Контекст A: десктоп — кнопки диалога, ширина по тексту ===')
        STATE['marks'] = [
            {'id': 1, 'дата_выполнения': '2026-02-05', 'мероприятие': 'Проверка огнетушителей', 'год': 2026, 'месяц': 2},
        ]
        STATE['hidden'] = []
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsA = attach(page, ctx, 'dark', 'a')
        open_plan_events(page)
        check('A1: страница активна',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        check('A2: подсказки над таблицей НЕТ',
              page.evaluate("!document.getElementById('peHint')"))
        sel_hidden = page.evaluate("""(() => {
            const bar = document.querySelector('.pe-month-bar');
            return bar ? getComputedStyle(bar).display : 'нет элемента';})()""")
        check('A3: полоса выбора месяца СКРЫТА на десктопе',
              sel_hidden == 'none', sel_hidden)
        signs = page.evaluate("""(() => {
            const all = document.querySelectorAll('#peTable td.pe-m');
            const done = document.querySelectorAll('#peTable td.pe-m.pe-m-done');
            const ths = document.querySelectorAll('#peTable tr.pe-head-months th');
            const tagged = document.querySelectorAll('#peTable [class*="pe-mo-"]');
            return {total: all.length, done: done.length, th: ths.length,
                    tagged: tagged.length};})()""")
        check('A4: 96 ячеек + 1 отметка с сервера',
              signs['total'] == 96 and signs['done'] == 1, signs)
        check('A5: классы pe-mo-N расставлены (12 th + 96 td = 108)',
              signs['th'] == 12 and signs['tagged'] == 108, signs)
        c = cell_by_event_month(page, 'Проверка огнетушителей', 2)
        check('A6: колонка мероприятий БЕЗ переносов (по тексту, Task 464)',
              c and c.get('white-space') == 'nowrap', c and c.get('white-space'))
        # клик по пустой ячейке → диалог подтверждения с новыми кнопками
        n_mark = count_actions('planEvents.mark')
        click_cell(page, 'Проверка СИЗ в электроустановках', 3)
        page.wait_for_timeout(400)
        dlg = dialog_state(page)
        check('A7: диалог «Отметка выполнения» открыт',
              dlg and 'Отметка выполнения' in dlg['title'], dlg)
        check('A8: кнопки [Отмена (pe-cancel-red)] [Подтвердить]',
              dlg and len(dlg['btns']) == 2
              and dlg['btns'][0]['text'] == 'Отмена'
              and 'pe-cancel-red' in dlg['btns'][0]['cls']
              and dlg['btns'][1]['text'] == 'Подтвердить', dlg and dlg['btns'])
        check('A9: поле даты = СЕГОДНЯ',
              dlg and dlg['date'] == today_iso(), dlg and dlg['date'])
        shot(page, '01-confirm-dialog-new-buttons.png')
        page.click('#kipDialogOverlay .kip-dialog-cancel')
        page.wait_for_timeout(400)
        check('A10: «Отмена» закрыла диалог, mark НЕ вызван',
              not page.evaluate("!!document.querySelector('#kipDialogOverlay .pe-dialog')")
              and count_actions('planEvents.mark') == n_mark)
        # подтверждение → галочка
        click_cell(page, 'Проверка СИЗ в электроустановках', 3)
        page.wait_for_timeout(300)
        page.fill('#peDialogDate', '2026-03-11')
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        sent = last_body('planEvents.mark')
        check('A11: mark payload {year: 2026, month: 3, event, date}',
              sent and sent.get('year') == 2026 and sent.get('month') == 3
              and sent.get('event') == 'Проверка СИЗ в электроустановках'
              and sent.get('date') == '2026-03-11' and 'token' in sent, sent)
        cell = cell_by_event_month(page, 'Проверка СИЗ в электроустановках', 3)
        check('A12: ячейка pe-m-done + title «Выполнено 11.03.2026»',
              cell and cell.get('pe-m-done')
              and 'Выполнено 11.03.2026' in (cell.get('title') or ''), cell)
        t = toast_text(page)
        check('A13: тост «Выполнение отмечено»',
              t['shown'] and 'Выполнение отмечено' in t['text'], t)
        check('A14: 0 JS-ошибок', len(jsA) == 0, jsA[:3])
        ctx.close()

        # ===== B: клик по отмеченной → диалог правки (дата) =====
        print('=== Контекст B: отмеченная ячейка → правка даты ===')
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsB = attach(page, ctx, 'dark', 'b')
        open_plan_events(page)
        cell = cell_by_event_month(page, 'Проверка СИЗ в электроустановках', 3)
        check('B0: отметка из контекста A пришла с сервера (stateful)',
              cell and cell.get('pe-m-done')
              and 'Выполнено 11.03.2026' in (cell.get('title') or ''), cell)
        click_cell(page, 'Проверка СИЗ в электроустановках', 3)
        page.wait_for_timeout(400)
        dlg = dialog_state(page)
        check('B1: диалог «Изменение отметки»',
              dlg and 'Изменение отметки' in dlg['title'], dlg)
        check('B2: подпись с мероприятием, месяцем и датой (выполнено 11.03.2026)',
              dlg and 'Проверка СИЗ в электроустановках' in dlg['msg']
              and 'Март' in dlg['msg']
              and 'выполнено 11.03.2026' in dlg['msg'], dlg and dlg['msg'])
        check('B3: поле даты = дата отметки (prefill)',
              dlg and dlg['date'] == '2026-03-11', dlg and dlg['date'])
        check('B4: три кнопки [Отмена][Удалить отметку (pe-unmark-btn)][Сохранить дату]',
              dlg and len(dlg['btns']) == 3
              and dlg['btns'][0]['text'] == 'Отмена'
              and dlg['btns'][1]['text'] == 'Удалить отметку'
              and 'pe-unmark-btn' in dlg['btns'][1]['cls']
              and dlg['btns'][2]['text'] == 'Сохранить дату', dlg and dlg['btns'])
        shot(page, '02-edit-dialog-three-buttons.png')
        page.click('#kipDialogOverlay .kip-dialog-cancel')
        page.wait_for_timeout(400)
        check('B5: «Отмена» → ничего не отправлено',
              count_actions('planEvents.update') == 0
              and count_actions('planEvents.unmark') == 0)
        # правка даты
        click_cell(page, 'Проверка СИЗ в электроустановках', 3)
        page.wait_for_timeout(300)
        page.fill('#peDialogDate', '2026-03-20')
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        sent = last_body('planEvents.update')
        check('B6: update payload {year, month, event, date} + token',
              sent and sent.get('year') == 2026 and sent.get('month') == 3
              and sent.get('event') == 'Проверка СИЗ в электроустановках'
              and sent.get('date') == '2026-03-20' and 'token' in sent, sent)
        cell = cell_by_event_month(page, 'Проверка СИЗ в электроустановках', 3)
        check('B7: title обновился «Выполнено 20.03.2026»',
              cell and cell.get('pe-m-done')
              and 'Выполнено 20.03.2026' in (cell.get('title') or ''), cell)
        t = toast_text(page)
        check('B8: тост «Дата отметки обновлена»',
              t['shown'] and 'Дата отметки обновлена' in t['text'], t)
        check('B9: 0 JS-ошибок', len(jsB) == 0, jsB[:3])
        ctx.close()

        # ===== C: «Удалить отметку» → unmark =====
        print('=== Контекст C: снятие отметки ===')
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsC = attach(page, ctx, 'dark', 'c')
        open_plan_events(page)
        click_cell(page, 'Проверка СИЗ в электроустановках', 3)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .pe-unmark-btn')
        page.wait_for_timeout(700)
        sent = last_body('planEvents.unmark')
        check('C1: unmark payload {year, month, event} БЕЗ date + token',
              sent and sent.get('year') == 2026 and sent.get('month') == 3
              and sent.get('event') == 'Проверка СИЗ в электроустановках'
              and 'date' not in sent and 'token' in sent, sent)
        cell = cell_by_event_month(page, 'Проверка СИЗ в электроустановках', 3)
        check('C2: ячейка вернулась к крестику (без pe-m-done)',
              cell and not cell.get('pe-m-done') and cell.get('hasCross'), cell)
        t = toast_text(page)
        check('C3: тост «Отметка снята»',
              t['shown'] and 'Отметка снята' in t['text'], t)
        # повторное открытие — отметки нет (stateful)
        page.evaluate("navigateTo('dashboard')")
        page.wait_for_timeout(300)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(700)
        cell = cell_by_event_month(page, 'Проверка СИЗ в электроустановках', 3)
        check('C4: после повторного открытия отметки НЕТ (строка удалена)',
              cell and not cell.get('pe-m-done'), cell)
        check('C5: 0 JS-ошибок', len(jsC) == 0, jsC[:3])
        ctx.close()

        # ===== D: ошибки сервера update/unmark =====
        print('=== Контекст D: ошибки сервера при правке/снятии ===')
        STATE['marks'] = [
            {'id': 7, 'дата_выполнения': '2026-05-14', 'мероприятие': 'Отчёт по талонам', 'год': 2026, 'месяц': 5},
        ]
        STATE['log'] = []
        STATE['mode'] = 'error'
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsD = attach(page, ctx, 'dark', 'd')
        open_plan_events(page)
        click_cell(page, 'Отчёт по талонам', 5)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .kip-dialog-ok')   # Сохранить дату
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('D1: тост «Не удалось сохранить дату» с message сервера',
              t['shown'] and 'Не удалось сохранить дату' in t['text']
              and 'planEventsDeploy' in t['text'], t)
        cell = cell_by_event_month(page, 'Отчёт по талонам', 5)
        check('D2: дата не изменилась (title прежний 14.05.2026)',
              cell and 'Выполнено 14.05.2026' in (cell.get('title') or ''), cell)
        check('D3: busy снят', cell and not cell.get('pe-m-busy'), cell)
        click_cell(page, 'Отчёт по талонам', 5)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .pe-unmark-btn')
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('D4: тост «Не удалось снять отметку»',
              t['shown'] and 'Не удалось снять отметку' in t['text'], t)
        cell = cell_by_event_month(page, 'Отчёт по талонам', 5)
        check('D5: галочка осталась (данные не тронуты)',
              cell and cell.get('pe-m-done'), cell)
        check('D6: 0 JS-ошибок', len(jsD) == 0, jsD[:3])
        ctx.close()

        # not_found: отметку параллельно удалили
        STATE['mode'] = 'not_found'
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsD2 = attach(page, ctx, 'dark', 'd2')
        open_plan_events(page)
        click_cell(page, 'Отчёт по талонам', 5)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('D7: not_found → тост с подсказкой «Обновить»',
              t['shown'] and 'Не удалось сохранить дату' in t['text']
              and 'Обновить' in t['text'], t)
        check('D8: 0 JS-ошибок', len(jsD2) == 0, jsD2[:3])
        ctx.close()
        STATE['mode'] = 'normal'

        # ===== E: идемпотентность mark (already) — как в Task 463 =====
        print('=== Контекст E: already:true (скрытая отметка) ===')
        STATE['marks'] = []
        STATE['hidden'] = [
            {'id': 99, 'дата_выполнения': '2026-04-03', 'мероприятие': 'Отчёт по графику ППР', 'год': 2026, 'месяц': 4},
        ]
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsE = attach(page, ctx, 'dark', 'e')
        open_plan_events(page)
        click_cell(page, 'Отчёт по графику ППР', 4)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('E1: тост «Отметка уже была сохранена»',
              t['shown'] and 'уже была сохранена' in t['text'], t)
        cell = cell_by_event_month(page, 'Отчёт по графику ППР', 4)
        check('E2: галочка с датой сервера (03.04.2026)',
              cell and cell.get('pe-m-done')
              and 'Выполнено 03.04.2026' in (cell.get('title') or ''), cell)
        check('E3: 0 JS-ошибок', len(jsE) == 0, jsE[:3])
        ctx.close()

        # ===== F: мобайл 375 светлая — один месяц + селектор =====
        print('=== Контекст F: мобайл 375 — селектор месяца ===')
        STATE['marks'] = [
            {'id': 1, 'дата_выполнения': '2026-02-05', 'мероприятие': 'Проверка огнетушителей', 'год': 2026, 'месяц': 2},
        ]
        STATE['hidden'] = []
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 375, 'height': 812})
        page = ctx.new_page()
        jsF = attach(page, ctx, 'light', 'f')
        open_plan_events(page)
        cur_month = datetime.date.today().month
        sel = page.evaluate("""(() => {
            const s = document.getElementById('peMonthSel');
            const bar = document.querySelector('.pe-month-bar');
            return {exists: !!s, display: bar ? getComputedStyle(bar).display : '',
                    value: s ? s.value : '', options: s ? s.options.length : 0,
                    text: s && s.selectedOptions[0] ? s.selectedOptions[0].text : ''};})()""")
        check('F1: полоса выбора ВИДИМА на мобайле (flex)',
              sel['display'] == 'flex', sel)
        check('F2: селектор = ТЕКУЩИЙ месяц по умолчанию (%d)' % cur_month,
              sel['value'] == str(cur_month), sel)
        check('F3: 12 опций-месяцев в селекторе',
              sel['options'] == 12, sel)
        vis = page.evaluate("""((cur) => {
            const ths = [...document.querySelectorAll('#peTable tr.pe-head-months th')];
            const visTh = ths.filter(th => th.offsetParent).length;
            const cells = [...document.querySelectorAll('#peTable td.pe-m')];
            const visCell = cells.filter(td => td.offsetParent).length;
            const visCur = cells.filter(td => td.offsetParent && td.classList.contains('pe-mo-' + cur)).length;
            return {visTh: visTh, visCell: visCell, visCur: visCur};})""", cur_month)
        check('F4: видна шапка ТОЛЬКО одного месяца',
              vis['visTh'] == 1, vis)
        check('F5: видимы только 8 ячеек текущего месяца (8 мероприятий)',
              vis['visCell'] == 8 and vis['visCur'] == 8, vis)
        cell = cell_by_event_month(page, 'Проверка огнетушителей', 2)
        check('F6: февральская отметка скрыта (если текущий не февраль)',
              cur_month == 2 or not cell.get('visible'), cell)
        shot(page, '03-mobile-current-month.png')
        # выбор другого месяца
        page.select_option('#peMonthSel', '12')
        page.wait_for_timeout(400)
        vis12 = page.evaluate("""(() => {
            const cells = [...document.querySelectorAll('#peTable td.pe-m')];
            const visDec = cells.filter(td => td.offsetParent && td.classList.contains('pe-mo-12')).length;
            const visOther = cells.filter(td => td.offsetParent && !td.classList.contains('pe-mo-12')).length;
            const ths = [...document.querySelectorAll('#peTable tr.pe-head-months th')];
            const visThText = ths.filter(th => th.offsetParent).map(th => th.textContent).join(',');
            return {visDec: visDec, visOther: visOther, th: visThText};})()""")
        check('F7: после выбора «Декабрь» — видны 8 декабрьских ячеек',
              vis12['visDec'] == 8 and vis12['visOther'] == 0, vis12)
        check('F8: шапка показывает «Дек.»',
              'Дек.' in vis12['th'], vis12)
        # отметка в выбранном месяце
        click_cell(page, 'График смен на следующий месяц', 12)
        page.wait_for_timeout(400)
        dlg = dialog_state(page)
        check('F9: диалог отметки работает в выбранном месяце',
              dlg and 'Декабрь' in dlg['msg'], dlg and dlg['msg'])
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        cell = cell_by_event_month(page, 'График смен на следующий месяц', 12)
        check('F10: декабрьская отметка поставлена (галочка)',
              cell and cell.get('pe-m-done'), cell)
        shot(page, '04-mobile-december-marked.png')
        # возврат к текущему месяцу
        page.select_option('#peMonthSel', str(cur_month))
        page.wait_for_timeout(400)
        check('F11: возврат к текущему месяцу — ячейки снова видимы',
              page.evaluate("""((cur) => {
                const cells = [...document.querySelectorAll('#peTable td.pe-m')];
                return cells.filter(td => td.offsetParent && td.classList.contains('pe-mo-' + cur)).length === 8;})""", cur_month))
        fit = page.evaluate("""(() => {
            const wrap = document.querySelector('.pe-grid-wrap');
            const vis = [...document.querySelectorAll('#peTable td.pe-m')].filter(td => td.offsetParent);
            const last = vis[vis.length - 1];
            const tbl = document.getElementById('peTable').getBoundingClientRect();
            return {scroll: wrap.scrollWidth, client: wrap.clientWidth,
                    lastRight: Math.round(last.getBoundingClientRect().right),
                    tblRight: Math.round(tbl.right)};})()""")
        check('F12: таблица ВЛЕЗАЕТ без горизонтального скролла',
              fit['scroll'] <= fit['client'], fit)
        check('F12b: столбец месяца у правого края таблицы (нет пустого столбца)',
              fit['tblRight'] - fit['lastRight'] <= 20, fit)
        shot(page, '03-mobile-current-month.png')
        check('F13: 0 JS-ошибок', len(jsF) == 0, jsF[:3])
        ctx.close()

        # ===== G: кнопка «Обновить» (smoke) =====
        print('=== Контекст G: кнопка «Обновить» ===')
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsG = attach(page, ctx, 'dark', 'g')
        open_plan_events(page)
        n_list = count_actions('planEvents.list')
        check('G1: list вызван при открытии', n_list >= 1, n_list)
        page.click('#peRefreshBtn')
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('G2: повторный list + тост «Отметки обновлены»',
              count_actions('planEvents.list') == n_list + 1
              and t['shown'] and 'Отметки обновлены' in t['text'], t)
        shot(page, '05-desktop-no-hint-autowidth.png')
        check('G3: 0 JS-ошибок', len(jsG) == 0, jsG[:3])
        ctx.close()

        browser.close()

    print('-' * 60)
    print('ИТОГ Task 464 browser-check: %d passed / %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


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
