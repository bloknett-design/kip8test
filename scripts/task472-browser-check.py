#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 472: browser-check — «Плановые мероприятия»:
#   1) поле ввода работ «на следующий месяц» — textarea с АВТОРОСТОМ
#      ВНИЗ под новые строки текста (длинный текст → поле растёт,
#      очистка → сжимается обратно; Enter — по-прежнему «Добавить»);
#   2) кликабельные ячейки (td.pe-m, месяцы шапки, «Мероприятия»,
#      строки работ) — вторая внутренняя рамка-бевел (имитация
#      выпуклости кнопки); некликабельные — без бевела;
#   3) фон таблицы и окна НЕПРОЗРАЧНЫЙ (обе темы); окно в светлой
#      теме — БЕЖЕВОЕ #f0eee6 (цвет фона бара) с ТОЛСТОЙ 3px
#      двухтонной рамкой-выступом + мягкая тень.
# ПРОВЕРКИ (мок-сервер, порт 8999): 0 JS-ошибок во всех сценариях.
import json
import os
import threading
from datetime import date
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'download', 'kip8test-task472')

TODAY_ISO = date.today().isoformat()
CUR_MONTH = date.today().month


# Мок-работы листа «Работы на месяц» (по году+месяцу запроса)
def works_for(year, month):
    if year == 2026 and month == CUR_MONTH + (1 if CUR_MONTH < 12 else 0):
        pass
    if year == 2026 and month == (CUR_MONTH + 1 if CUR_MONTH < 12 else 1):
        return [
            {'id': 201, 'год': year, 'месяц': month,
             'работа': 'Плановая поверка манометров',
             'статус': '', 'дата_статуса': ''},
        ]
    return []


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'planEvents.list':
        return {'ok': True, 'data': {'marks': [], 'srvVer': '471'}}
    if action == 'planEvents.years':
        return {'ok': True, 'data': {'years': [], 'srvVer': '471'}}
    if action == 'planWorks.list':
        y = body.get('year')
        m = body.get('month')
        return {'ok': True, 'data': {'works': works_for(y, m), 'srvVer': '471'}}
    if action == 'planWorks.add':
        w = {'id': 999, 'год': body.get('year'), 'месяц': body.get('month'),
             'работа': body.get('work'), 'статус': '', 'дата_статуса': ''}
        return {'ok': True, 'data': {'work': w}}
    if action == 'planWorks.remove':
        return {'ok': True, 'data': {'removed': True}}
    if action == 'planWorks.setStatus':
        w = {'id': body.get('id'), 'статус': body.get('status'),
             'дата_статуса': body.get('date') or TODAY_ISO}
        return {'ok': True, 'data': {'work': w}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


PASS = 0
FAIL = 0
API_CALLS = []


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


def calls(action):
    return [b for (a, b) in API_CALLS if a == action]


def set_theme(page, theme):
    page.evaluate("t => localStorage.setItem('app-theme', t)", theme)
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('plan-events')")
    page.wait_for_timeout(1200)


def click_name(page, text):
    page.evaluate("""(t) => {
        const tds = document.querySelectorAll('#peTable tbody td.pe-name');
        for (const td of tds) {
            if ((td.textContent || '').trim() === t) { td.click(); return true; }
        }
        return false;}""", text)


# Стилевое состояние раздела (фоны/рамки/бевелы) в текущей теме
def style_state(page):
    return page.evaluate("""(() => {
        const cs = (el) => el ? getComputedStyle(el) : null;
        const card = document.querySelector('#page-plan-events .pe-card');
        const win = document.querySelector('#page-plan-events .pe-desc-card');
        const tdM = document.querySelector('#peTable td.pe-m');
        const thMo = document.querySelector('#peTable tr.pe-head-months th');
        const thName = document.querySelector('#peTable th.pe-th-name');
        const nameClick = document.querySelector('#peTable td.pe-name.pe-name-click');
        const group = document.querySelector('#peTable td, #peTable tr.pe-group td');
        const grp = document.querySelector('#peTable tr.pe-group td');
        const c = cs(card), w = cs(win);
        return {
            cardBg: c ? c.backgroundColor : '',
            cardAlpha: c ? c.backgroundColor : '',
            winBg: w ? w.backgroundColor : '',
            winBorderW: w ? w.borderTopWidth : '',
            winBorderTop: w ? w.borderTopColor : '',
            winBorderBottom: w ? w.borderBottomColor : '',
            winShadow: w ? w.boxShadow : '',
            tdMShadow: cs(tdM) ? cs(tdM).boxShadow : '',
            thMoShadow: cs(thMo) ? cs(thMo).boxShadow : '',
            thNameShadow: cs(thName) ? cs(thName).boxShadow : '',
            nameClickShadow: cs(nameClick) ? cs(nameClick).boxShadow : '',
            groupShadow: cs(grp) ? cs(grp).boxShadow : '',
            docW: document.documentElement.scrollWidth,
            winW: window.innerWidth};})()""")


# Состояние поля ввода (авторост)
def input_state(page):
    return page.evaluate("""(() => {
        const ta = document.getElementById('peWorkInput');
        if (!ta) return null;
        const cs = getComputedStyle(ta);
        const btn = document.getElementById('peWorkAddBtn');
        const taR = ta.getBoundingClientRect();
        const btnR = btn ? btn.getBoundingClientRect() : null;
        return {tag: ta.tagName, rows: ta.getAttribute('rows'),
                h: ta.style.height || '(auto)',
                rectH: Math.round(taR.height),
                resize: cs.resize, overflow: cs.overflow,
                scrollH: ta.scrollHeight,
                minH: cs.minHeight,
                btnTopAligned: btnR ? Math.abs(btnR.top - taR.top) < 2 : false,
                btnH: btnR ? Math.round(btnR.height) : 0};})()""")


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t472');" +
            "localStorage.setItem('app-theme','light');")

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
            API_CALLS.append((action, dict(body)))
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

        # ===== A: светлая тема — бежевое окно + толстая рамка-выступ
        print('== A: 1600px СВЕТЛАЯ — бежевое окно, толстая рамка-выступ ==')
        open_section(page)
        page.wait_for_timeout(400)
        st = style_state(page)
        check('тема светлая (data-theme=light)',
              page.evaluate("document.documentElement.getAttribute('data-theme')")
              == 'light')
        check('окно БЕЖЕВОЕ #f0eee6 = rgb(240, 238, 230)',
              st['winBg'] == 'rgb(240, 238, 230)', st['winBg'])
        check('карточка таблицы непрозрачная #faf9f6',
              st['cardBg'] == 'rgb(250, 249, 246)', st['cardBg'])
        check('фон окна БЕЗ альфы (непрозрачный)',
              'rgba' not in st['winBg'] and 'rgba' not in st['cardBg'],
              (st['winBg'], st['cardBg']))
        check('толстая рамка окна 3px', st['winBorderW'] == '3px', st['winBorderW'])
        check('рамка-выступ: светлая грань сверху',
              st['winBorderTop'] == 'rgb(255, 253, 247)', st['winBorderTop'])
        check('рамка-выступ: тёмная грань снизу',
              st['winBorderBottom'] == 'rgb(200, 194, 175)',
              st['winBorderBottom'])
        check('мягкая тень под окном (выступ над страницей)',
              '2px 3px 6px' in st['winShadow'], st['winShadow'])
        check('цвет окна = цвет фона бара (240,238,230)',
              page.evaluate("""(() => {
                const header = document.querySelector('.app-header');
                const win = document.querySelector('.pe-desc-card');
                if (!header || !win) return false;
                const hb = getComputedStyle(header).backgroundColor;
                const wb = getComputedStyle(win).backgroundColor;
                return hb.indexOf('240, 238, 230') !== -1 &&
                       wb === 'rgb(240, 238, 230)';})()"""))
        shot(page, 'a-light-beige-window.png')

        # ===== B: светлая — бевел кликабельных ячеек
        print('== B: СВЕТЛАЯ — вторая рамка-бевел кликабельных ячеек ==')
        st = style_state(page)
        check('ячейка месяца td.pe-m — бевел (inset)',
              'inset' in st['tdMShadow'], st['tdMShadow'])
        check('месяц шапки th — бевел (inset)',
              'inset' in st['thMoShadow'], st['thMoShadow'])
        check('«Мероприятия» (шапка) — бевел (inset)',
              'inset' in st['thNameShadow'], st['thNameShadow'])
        check('строка работ pe-name-click — бевел (inset)',
              'inset' in st['nameClickShadow'], st['nameClickShadow'])
        check('бевел двухтонный (светлое + тёмное)',
              'rgba(255, 255, 255, 0.8)' in st['tdMShadow'] and
              'rgba(83, 96, 117, 0.42)' in st['tdMShadow'], st['tdMShadow'])
        check('строка-группа БЕЗ бевела (не кликабельна)',
              st['groupShadow'] == 'none', st['groupShadow'])
        shot(page, 'b-light-bevel.png')

        # ===== C: светлая — авторост поля ввода работ
        print('== C: СВЕТЛАЯ — textarea с авторостом вниз ==')
        click_name(page, 'Работы на следующий месяц')
        page.wait_for_timeout(700)
        inp = input_state(page)
        check('поле ввода — TEXTAREA rows=1',
              inp and inp['tag'] == 'TEXTAREA' and inp['rows'] == '1', inp)
        check('ресайз отключён, скроллбар скрыт',
              inp['resize'] == 'none' and inp['overflow'] == 'hidden',
              (inp['resize'], inp['overflow']))
        check('начальная высота — одна строка (~35px)',
              33 <= inp['rectH'] <= 40, inp['rectH'])
        h0 = inp['rectH']
        # Длинный текст — поле растёт вниз под новые строки
        page.fill('#peWorkInput',
                  'Ревизия запорной арматуры узла подготовки газа с полной '
                  'разборкой приводов, заменой уплотнений и последующей '
                  'опрессовкой системы импульсных линий, проверка '
                  'чувствительности датчиков давления и температуры, '
                  'калибровка вторичных приборов в шкафу КИП АБК №2 '
                  'с оформлением протоколов поверки')
        page.evaluate("document.getElementById('peWorkInput').dispatchEvent("
                      "new Event('input', {bubbles: true}))")
        page.wait_for_timeout(300)
        inp = input_state(page)
        check('длинный текст → поле выросло вниз (>= 2 строки)',
              inp['rectH'] >= h0 * 1.8, (h0, inp['rectH']))
        check('высота = контент + границы (без обрезки текста)',
              inp['rectH'] >= inp['scrollH'], (inp['rectH'], inp['scrollH']))
        h1 = inp['rectH']
        # Ещё длиннее — растёт дальше
        page.fill('#peWorkInput',
                  'Ревизия запорной арматуры узла подготовки газа с полной '
                  'разборкой приводов, заменой уплотнений и последующей '
                  'опрессовкой системы импульсных линий, проверка '
                  'чувствительности датчиков давления и температуры, '
                  'калибровка вторичных приборов в шкафу КИП АБК №2 '
                  'с оформлением протоколов поверки, продувка импульсных '
                  'линий расходомеров хозрасчёта, ревизия манометров '
                  'класса точности 1.5, замена термометров сопротивления '
                  'на котлах №1 и №2, проверка срабатывания защит и '
                  'блокировок по всем агрегатам')
        page.evaluate("document.getElementById('peWorkInput').dispatchEvent("
                      "new Event('input', {bubbles: true}))")
        page.wait_for_timeout(300)
        inp = input_state(page)
        check('ещё длиннее → поле выросло ещё', inp['rectH'] > h1, (h1, inp['rectH']))
        check('кнопка «Добавить» прижата к первой строке',
              inp['btnTopAligned'], inp)
        shot(page, 'c-light-grow.png')
        # Очистка — поле сжимается обратно
        page.fill('#peWorkInput', '')
        page.evaluate("document.getElementById('peWorkInput').dispatchEvent("
                      "new Event('input', {bubbles: true}))")
        page.wait_for_timeout(300)
        inp = input_state(page)
        check('очистка → поле сжалось обратно к одной строке',
              inp['rectH'] <= h0 + 2, (h0, inp['rectH']))
        # Enter — по-прежнему «Добавить»
        API_CALLS.clear()
        page.fill('#peWorkInput', 'Продувка импульсных линий РО-1')
        page.evaluate("document.getElementById('peWorkInput').dispatchEvent("
                      "new Event('input', {bubbles: true}))")
        page.press('#peWorkInput', 'Enter')
        page.wait_for_timeout(700)
        added = calls('planWorks.add')
        check('Enter добавляет работу (авторост не сломал)',
              len(added) == 1 and added[0].get('work') == 'Продувка импульсных линий РО-1',
              added)
        check('поле очищено после добавления',
              page.input_value('#peWorkInput') == '')

        # ===== D: тёмная тема — непрозрачные фоны + бевел
        print('== D: ТЁМНАЯ — непрозрачные фоны + бевел ==')
        set_theme(page, 'dark')
        st = style_state(page)
        check('тема тёмная (data-theme=dark)',
              page.evaluate("document.documentElement.getAttribute('data-theme')")
              == 'dark')
        check('карточка таблицы непрозрачная #17212e',
              st['cardBg'] == 'rgb(23, 33, 46)', st['cardBg'])
        check('окно непрозрачное #17212e',
              st['winBg'] == 'rgb(23, 33, 46)', st['winBg'])
        check('фоны БЕЗ альфы (тёмная тема)',
              'rgba' not in st['winBg'] and 'rgba' not in st['cardBg'],
              (st['winBg'], st['cardBg']))
        check('бевел ячейки месяца (тёмная тема)',
              'inset' in st['tdMShadow'], st['tdMShadow'])
        check('бевел месяца шапки (тёмная тема)',
              'inset' in st['thMoShadow'], st['thMoShadow'])
        shot(page, 'd-dark-opaque.png')

        # ===== E: тёмная — авторост в тёмной теме жив
        print('== E: ТЁМНАЯ — авторост поля жив ==')
        click_name(page, 'Работы на следующий месяц')
        page.wait_for_timeout(700)
        inp = input_state(page)
        h0 = inp['rectH']
        page.fill('#peWorkInput',
                  'Плановая поверка манометров с оформлением протоколов '
                  'и записью в журнал учёта средств измерений участка КИП ИОС')
        page.evaluate("document.getElementById('peWorkInput').dispatchEvent("
                      "new Event('input', {bubbles: true}))")
        page.wait_for_timeout(300)
        inp = input_state(page)
        check('авторост работает и в тёмной теме',
              inp['rectH'] > h0, (h0, inp['rectH']))
        shot(page, 'e-dark-grow.png')

        # ===== F: мобайл 375 светлая — Task 464 жив + авторост
        print('== F: 375px СВЕТЛАЯ — мобайл (Task 464) + авторост ==')
        page.set_viewport_size({'width': 375, 'height': 800})
        set_theme(page, 'light')
        m = page.evaluate("""(() => {
            const rows = document.querySelectorAll('#peTable tbody tr.pe-row');
            let visible = 0;
            rows.forEach(tr => tr.querySelectorAll('td.pe-m').forEach(td => {
                if (getComputedStyle(td).display !== 'none'
                    && td.getBoundingClientRect().width > 0) visible++;
            }));
            const bar = document.querySelector('.pe-month-bar');
            return {visible: visible,
                    barVisible: getComputedStyle(bar).display !== 'none'};})()""")
        check('Task 464: один месяц × 10 строк = 10 видимых ячеек',
              m['visible'] == 10, m['visible'])
        check('полоса «Месяц» (селектор) видна', m['barVisible'], m)
        check('окно бежевое на мобайле (под таблицей)',
              style_state(page)['winBg'] == 'rgb(240, 238, 230)')
        click_name(page, 'Работы на следующий месяц')
        page.wait_for_timeout(700)
        inp = input_state(page)
        h0 = inp['rectH']
        page.fill('#peWorkInput',
                  'Ревизия запорной арматуры узла подготовки газа с полной '
                  'разборкой приводов и заменой уплотнений')
        page.evaluate("document.getElementById('peWorkInput').dispatchEvent("
                      "new Event('input', {bubbles: true}))")
        page.wait_for_timeout(300)
        inp = input_state(page)
        check('авторост на мобайле (узкое поле растёт вниз)',
              inp['rectH'] >= h0 * 1.8, (h0, inp['rectH']))
        check('0 JS-ошибок во всех сценариях', not js_errors, js_errors[:3])
        shot(page, 'f-mobile-375.png')

        browser.close()
    server.shutdown()

    print()
    print('ИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
