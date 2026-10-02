#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 463: browser-check — ИНТЕРАКТИВНЫЕ отметки выполнения в
# разделе «Плановые мероприятия» + архив файла Мероприятия_КИП_ИОС.
# Заявка: «...отметки делает пользователь в таблице плана
# мероприятий путём нажатия на ячейку напротив мероприятия за
# выбранный месяц, при этом, после подтверждения данного действия,
# в ячейке вместо тусклого крестика появляется значок галочки
# зелёного цвета, и эта информация, с указанием наименования
# мероприятия и даты его выполнения, сохраняется в архив файла
# Мероприятия_КИП_ИОС.»
# КОНТЕКСТ (мок-сервер, порт 8995; STATEFUL — mark пишет в стор):
#   A: страница открыта, list вернул 2 отметки → 96 знаков: 94
#      тусклых крестика + 2 зелёные галочки (title с датой);
#      клик по ОТМЕЧЕННОЙ ячейке → тост «Уже отмечено…», mark
#      НЕ вызывался; клик по пустой → диалог (наименование +
#      месяц + дата=сегодня) → «Отмена» → mark НЕ вызван, ячейка
#      осталась крестиком;
#   B: подтверждение диалога → mark вызван с payload {token, year:
#      2026, month, event, date} → ячейка pe-m-done + зелёный
#      polyline + title «Выполнено …» + тост «Выполнение отмечено»;
#      повторное открытие страницы → отметка приходит с сервера
#      (stateful);
#   C: идемпотентность сервера — скрытая отметка (в list НЕ
#      отдавалась) → mark отвечает already:true → тост «Отметка
#      уже была сохранена», ячейка с галочкой;
#   D: ошибка сервера mark (sheet_not_found + message) → тост
#      «Не удалось отметить: …», ячейка ОСТАЛАСЬ крестиком;
#   E: «старый сервер» (Unknown action) → автозагрузка ТИХО
#      (нет тоста об ошибке, только console.warn), крестики;
#   F: кнопка «Обновить» (peRefreshBtn) → повторный list + тост
#      «Отметки обновлены» + анимация pe-refreshing;
#   G: 0 JS-ошибок во всех контекстах; скриншоты в
#      download/kip8test-task463/.
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8995

PASS = 0
FAIL = 0
SHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        '..', 'download', 'kip8test-task463')

# Мок-состояние «сервера» (stateful): marks — видимые list-ом,
# hidden — только для идемпотентности mark (контекст C)
STATE = {
    'marks': [],
    'hidden': [],
    'next_id': 1,
    'log': [],        # журнал действий мока
    'mode': 'normal', # normal | error | unknown_action
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
        return {'ok': True, 'data': {'marks': st['marks'], 'srvVer': '463'}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t463-%s');" % tag +
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
                      body='not found (t463-%s)' % tag)
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


def cell_by_event_month(page, event, month):
    """Состояние td.pe-m строки мероприятия по месяцу (1..12):
    {pe-m-done, pe-m-busy, hasCheck, hasCross, title} или None."""
    return page.evaluate("""(([ev, mn]) => {
        const rows = document.querySelectorAll('#peTable tbody tr.pe-row');
        for (const tr of rows) {
            const nm = tr.querySelector('td.pe-name');
            if (!nm || nm.textContent.trim() !== ev) continue;
            const td = tr.querySelectorAll('td.pe-m')[mn - 1];
            if (!td) return null;
            return {'pe-m-done': td.classList.contains('pe-m-done'),
                    'pe-m-busy': td.classList.contains('pe-m-busy'),
                    hasCheck: !!td.querySelector('.pe-ic-check'),
                    hasCross: !!td.querySelector('.pe-ic-cross'),
                    title: td.getAttribute('title') || ''};
        }
        return null;})""", [event, month])


def click_cell(page, event, month):
    """Клик по td.pe-m строки мероприятия по месяцу (1..12)."""
    page.evaluate("""(([ev, mn]) => {
        const rows = document.querySelectorAll('#peTable tbody tr.pe-row');
        for (const tr of rows) {
            const nm = tr.querySelector('td.pe-name');
            if (!nm || nm.textContent.trim() !== ev) continue;
            const td = tr.querySelectorAll('td.pe-m')[mn - 1];
            if (td) td.click();
        }})""", [event, month])


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== A: загрузка отметок + клики (отмеченная/пустая/отмена) =====
        print('=== Контекст A: 2 отметки с сервера; клики по ячейкам ===')
        STATE['marks'] = [
            {'id': 1, 'дата_выполнения': '2026-02-05', 'мероприятие': 'Проверка огнетушителей', 'год': 2026, 'месяц': 2},
            {'id': 2, 'дата_выполнения': '2026-05-21', 'мероприятие': 'Отчёт по талонам', 'год': 2026, 'месяц': 5},
        ]
        STATE['hidden'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsA = attach(page, ctx, 'dark', 'a')
        open_plan_events(page)
        check('A1: страница активна',
              page.evaluate("!!document.querySelector('#page-plan-events.active')"))
        signs = page.evaluate("""(() => {
            const all = document.querySelectorAll('#peTable td.pe-m');
            const cross = document.querySelectorAll('#peTable td.pe-m .pe-ic-cross');
            const done = document.querySelectorAll('#peTable td.pe-m.pe-m-done');
            const check = document.querySelectorAll('#peTable td.pe-m .pe-ic-check');
            return {total: all.length, cross: cross.length, done: done.length,
                    check: check.length};})()""")
        check('A2: 96 ячеек месяцев', signs['total'] == 96, signs)
        check('A3: 94 тусклых крестика + 2 галочки',
              signs['cross'] == 94 and signs['check'] == 2 and signs['done'] == 2,
              signs)
        titles = page.evaluate("""(() => {
            const out = [];
            document.querySelectorAll('#peTable td.pe-m.pe-m-done').forEach(td => {
                out.push(td.getAttribute('title') || '');});
            return out;})()""")
        check('A4: title отмеченных ячеек с датой dd.mm.yyyy',
              len(titles) == 2 and any('Выполнено 05.02.2026' in t for t in titles)
              and any('Выполнено 21.05.2026' in t for t in titles), titles)
        hint = page.evaluate("(() => { const h = document.getElementById('peHint'); return h ? h.textContent : ''; })()")
        check('A5: подсказка над таблицей', 'Нажмите на ячейку месяца' in hint, hint)
        btn = page.evaluate("(() => { const b = document.getElementById('peRefreshBtn'); return !!b; })()")
        check('A6: кнопка «Обновить» в шапке', btn)
        # клик по ОТМЕЧЕННОЙ ячейке → тост «Уже отмечено», mark НЕ шлётся
        n_mark_before = count_actions('planEvents.mark')
        click_cell(page, 'Проверка огнетушителей', 2)
        page.wait_for_timeout(400)
        t = toast_text(page)
        check('A7: клик по отмеченной → тост «Уже отмечено: выполнено 05.02.2026»',
              t['shown'] and 'Уже отмечено' in t['text'] and '05.02.2026' in t['text'], t)
        check('A8: mark при клике по отмеченной НЕ вызывался',
              count_actions('planEvents.mark') == n_mark_before)
        # клик по ПУСТОЙ ячейке → диалог; отмена
        click_cell(page, 'Проверка СИЗ в электроустановках', 3)
        page.wait_for_timeout(400)
        dlg = page.evaluate("""(() => {
            const ov = document.getElementById('kipDialogOverlay');
            const d = ov ? ov.querySelector('.pe-dialog') : null;
            if (!d) return null;
            return {title: (d.querySelector('.kip-dialog-title')||{}).textContent || '',
                    msg: (d.querySelector('.kip-dialog-msg')||{}).textContent || '',
                    date: (d.querySelector('#peDialogDate')||{}).value || '',
                    ok: !!d.querySelector('.kip-dialog-ok'),
                    cancel: !!d.querySelector('.kip-dialog-cancel')};})()""")
        check('A9: диалог открыт: заголовок «Отметка выполнения»',
              dlg and 'Отметка выполнения' in dlg['title'], dlg)
        check('A10: подпись «Проверка СИЗ в электроустановках — Март 2026»',
              dlg and 'Проверка СИЗ в электроустановках' in dlg['msg']
              and 'Март' in dlg['msg'] and '2026' in dlg['msg'], dlg and dlg['msg'])
        check('A11: поле даты = СЕГОДНЯ (локальная)',
              dlg and dlg['date'] == today_iso(), dlg and dlg['date'])
        page.click('#kipDialogOverlay .kip-dialog-cancel')
        page.wait_for_timeout(400)
        check('A12: «Отмена» закрыла диалог',
              not page.evaluate("!!document.querySelector('#kipDialogOverlay .pe-dialog')"))
        check('A13: mark после отмены НЕ вызван',
              count_actions('planEvents.mark') == n_mark_before)
        st = cell_by_event_month(page, 'Проверка СИЗ в электроустановках', 3)
        check('A14: ячейка после отмены — крестик (без pe-m-done)',
              st and not st.get('pe-m-done') and st.get('hasCross'), st)
        shot(page, '01-marks-loaded.png')
        ctx.close()

        # ===== B: подтверждение → mark → зелёная галочка =====
        print('=== Контекст B: подтверждение диалога — отметка сохраняется ===')
        STATE['marks'] = []
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsB = attach(page, ctx, 'dark', 'b')
        open_plan_events(page)
        click_cell(page, 'Проверка огнетушителей', 2)
        page.wait_for_timeout(300)
        page.fill('#peDialogDate', '2026-02-15')
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        marks_sent = [l['body'] for l in STATE['log'] if l['action'] == 'planEvents.mark']
        check('B1: mark вызван ОДИН раз', len(marks_sent) == 1, len(marks_sent))
        if marks_sent:
            b = marks_sent[0]
            check('B2: payload {year: 2026, month: 2, event, date}',
                  b.get('year') == 2026 and b.get('month') == 2
                  and b.get('event') == 'Проверка огнетушителей'
                  and b.get('date') == '2026-02-15' and 'token' in b, b)
        done_cell = cell_by_event_month(page, 'Проверка огнетушителей', 2)
        check('B3: ячейка стала pe-m-done с зелёной галочкой',
              done_cell and done_cell.get('pe-m-done') and done_cell.get('hasCheck'),
              done_cell)
        check('B4: title «Выполнено 15.02.2026»',
              done_cell and 'Выполнено 15.02.2026' in (done_cell.get('title') or ''),
              done_cell)
        t = toast_text(page)
        check('B5: тост «Выполнение отмечено»',
              t['shown'] and 'Выполнение отмечено' in t['text'], t)
        check('B6: busy-класс снят после ответа',
              not done_cell.get('pe-m-busy'), done_cell)
        # повторное открытие страницы — отметка приходит с сервера (stateful)
        page.evaluate("navigateTo('dashboard')")
        page.wait_for_timeout(300)
        page.evaluate("navigateTo('plan-events')")
        page.wait_for_timeout(700)
        done2 = cell_by_event_month(page, 'Проверка огнетушителей', 2)
        check('B7: после повторного открытия галочка приходит с сервера',
              done2 and done2.get('pe-m-done') and 'Выполнено 15.02.2026' in (done2.get('title') or ''),
              done2)
        shot(page, '02-marked-green-check.png')
        check('B8: 0 JS-ошибок', len(jsB) == 0, jsB[:3])
        ctx.close()

        # ===== C: идемпотентность сервера (already: true) =====
        print('=== Контекст C: сервер отвечает already:true (скрытая отметка) ===')
        STATE['marks'] = [
            {'id': 1, 'дата_выполнения': '2026-07-09', 'мероприятие': 'Выписка из ППР на следующий месяц', 'год': 2026, 'месяц': 7},
        ]
        STATE['hidden'] = [
            {'id': 99, 'дата_выполнения': '2026-04-03', 'мероприятие': 'Отчёт по графику ППР', 'год': 2026, 'месяц': 4},
        ]
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsC = attach(page, ctx, 'dark', 'c')
        open_plan_events(page)
        click_cell(page, 'Отчёт по графику ППР', 4)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        sent = [l['body'] for l in STATE['log'] if l['action'] == 'planEvents.mark']
        check('C1: mark отправлен (клиент не знал о скрытой отметке)',
              len(sent) == 1 and sent[0].get('event') == 'Отчёт по графику ППР', sent)
        t = toast_text(page)
        check('C2: тост «Отметка уже была сохранена»',
              t['shown'] and 'уже была сохранена' in t['text'], t)
        done_cell = cell_by_event_month(page, 'Отчёт по графику ППР', 4)
        check('C3: ячейка с галочкой (дата из ответа сервера 03.04.2026)',
              done_cell and done_cell.get('pe-m-done')
              and 'Выполнено 03.04.2026' in (done_cell.get('title') or ''), done_cell)
        check('C4: дубль в marks у клиента не создан (одна запись о событии)',
              len([m for m in STATE['marks'] + STATE['hidden']
                   if m['мероприятие'] == 'Отчёт по графику ППР']) == 1)
        check('C5: 0 JS-ошибок', len(jsC) == 0, jsC[:3])
        ctx.close()

        # ===== D: ошибка сервера при mark =====
        print('=== Контекст D: ошибка сервера — ячейка остаётся крестиком ===')
        STATE['marks'] = []
        STATE['hidden'] = []
        STATE['log'] = []
        STATE['mode'] = 'error'
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsD = attach(page, ctx, 'dark', 'd')
        open_plan_events(page)
        click_cell(page, 'Журнал учёта электрооборудования', 11)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('D1: тост «Не удалось отметить: …» с message сервера',
              t['shown'] and 'Не удалось отметить' in t['text']
              and 'planEventsDeploy' in t['text'], t)
        cell = cell_by_event_month(page, 'Журнал учёта электрооборудования', 11)
        check('D2: ячейка осталась КРЕСТИКОМ (без pe-m-done)',
              cell and not cell.get('pe-m-done') and cell.get('hasCross'), cell)
        check('D3: busy снят', cell and not cell.get('pe-m-busy'), cell)
        check('D4: 0 JS-ошибок', len(jsD) == 0, jsD[:3])
        ctx.close()
        STATE['mode'] = 'normal'

        # ===== E: «старый сервер» (Unknown action) — тихая деградация =====
        print('=== Контекст E: Unknown action — автозагрузка ТИХО ===')
        STATE['marks'] = []
        STATE['log'] = []
        STATE['mode'] = 'unknown_action'
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsE = attach(page, ctx, 'dark', 'e')
        open_plan_events(page)
        page.wait_for_timeout(1200)
        t = toast_text(page)
        check('E1: тоста об ошибке НЕТ (тихая автозагрузка)', not t['shown'], t)
        signs = page.evaluate("""(() => {
            const cross = document.querySelectorAll('#peTable td.pe-m .pe-ic-cross');
            return cross.length;})()""")
        check('E2: 96 крестиков (отметок нет)', signs == 96, signs)
        # клик → диалог → подтверждение → тост с ошибкой (явное действие)
        click_cell(page, 'Проверка электроинструмента (приспособлений)', 1)
        page.wait_for_timeout(300)
        page.click('#kipDialogOverlay .kip-dialog-ok')
        page.wait_for_timeout(700)
        t = toast_text(page)
        check('E3: явная отметка на старом сервере → тост «Не удалось отметить»',
              t['shown'] and 'Не удалось отметить' in t['text'], t)
        check('E4: 0 JS-ошибок', len(jsE) == 0, jsE[:3])
        ctx.close()
        STATE['mode'] = 'normal'

        # ===== F: кнопка «Обновить» =====
        print('=== Контекст F: кнопка «Обновить» — повторный list ===')
        STATE['marks'] = [
            {'id': 1, 'дата_выполнения': '2026-12-28', 'мероприятие': 'График смен на следующий месяц', 'год': 2026, 'месяц': 12},
        ]
        STATE['log'] = []
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        jsF = attach(page, ctx, 'dark', 'f')
        open_plan_events(page)
        n_list = count_actions('planEvents.list')
        check('F1: list вызван при открытии страницы', n_list >= 1, n_list)
        page.click('#peRefreshBtn')
        page.wait_for_timeout(700)
        check('F2: list вызван повторно', count_actions('planEvents.list') == n_list + 1)
        t = toast_text(page)
        check('F3: тост «Отметки обновлены»',
              t['shown'] and 'Отметки обновлены' in t['text'], t)
        done_cell = cell_by_event_month(page, 'График смен на следующий месяц', 12)
        check('F4: галочка декабря после обновления',
              done_cell and done_cell.get('pe-m-done'), done_cell)
        # мобильный вид + светлая тема — скриншот
        page2 = ctx.new_page()
        jsF2 = attach(page2, ctx, 'light', 'f2')
        page2.set_viewport_size({'width': 375, 'height': 812})
        open_plan_events(page2)
        check('F5: мобильный 375px: страница жива, таблица прокручивается',
              page2.evaluate("""(() => {
                const w = document.querySelector('#peTable').closest('.pe-grid-wrap');
                return !!(w && w.scrollWidth >= w.clientWidth);})()"""))
        done_cell = cell_by_event_month(page2, 'График смен на следующий месяц', 12)
        check('F6: галочка видна и в светлой теме (класс pe-m-done)',
              done_cell and done_cell.get('pe-m-done'), done_cell)
        shot(page2, '03-mobile-light.png')
        check('F7: 0 JS-ошибок', len(jsF) == 0 and len(jsF2) == 0,
              (jsF[:2], jsF2[:2]))
        ctx.close()

        browser.close()

    print('-' * 60)
    print('ИТОГ Task 463 browser-check: %d passed / %d failed' % (PASS, FAIL))
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
