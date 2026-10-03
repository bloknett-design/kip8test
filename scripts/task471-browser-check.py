#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 471: browser-check — «Плановые мероприятия»:
#   1) кнопка просмотра предыдущих годов СЛЕВА от «2026 год» —
#      активна только при наличии архива за предыдущие годы
#      (planEvents.years), клик → 2025, повторный клик → возврат;
#   2) месяцы шапки кликабельны — выбирают месяц правого окна
#      (подсветка pe-mo-sel);
#   3) динамичное правое окно: клик по ячейке «Работы на следующий
#      месяц» → интерфейс ввода работ на следующий месяц (Ноябрь
#      2026; декабрь → Январь 2027 — переход года); клик по ячейке
#      «Работы на месяц» → перечень работ месяца с отметкой
#      полного/частичного выполнения или невыполнения
#      (planWorks.setStatus); клик по «Мероприятия» (шапка) — снова
#      описание раздела;
#   4) мобайл: Task 464 жив, селектор месяца синхронен.
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
                        '..', 'download', 'kip8test-task471')

TODAY_ISO = date.today().isoformat()          # 2026-10-03 (запуск 03.10.2026)
CUR_MONTH = date.today().month                 # 10 — октябрь

# Мок-работы листа «Работы на месяц» (по году+месяцу запроса)
def works_for(year, month):
    if year == 2026 and month == 10:
        return [
            {'id': 101, 'год': 2026, 'месяц': 10,
             'работа': 'Проверка датчиков давления КИП',
             'статус': '', 'дата_статуса': ''},
            {'id': 102, 'год': 2026, 'месяц': 10,
             'работа': 'Ревизия импульсных линий',
             'статус': 'частично', 'дата_статуса': '2026-10-01'},
        ]
    if year == 2026 and month == 11:
        return [
            {'id': 201, 'год': 2026, 'месяц': 11,
             'работа': 'Плановая поверка манометров',
             'статус': '', 'дата_статуса': ''},
        ]
    if year == 2027 and month == 1:
        return [
            {'id': 301, 'год': 2027, 'месяц': 1,
             'работа': 'Подготовка к отопительному сезону',
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
        # Архив за 2025 есть — кнопка годов активна
        return {'ok': True, 'data': {'years': [2025], 'srvVer': '471'}}
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


def works_state(page):
    return page.evaluate("""(() => {
        const dv = document.getElementById('peDescView');
        const wv = document.getElementById('peWorksView');
        const btn = document.getElementById('pePrevYearBtn');
        const label = document.getElementById('peYearLabel');
        const selTh = document.querySelector('tr.pe-head-months th.pe-mo-sel');
        const items = wv ? [...wv.querySelectorAll('.pe-work-item')].map(it => ({
            id: it.getAttribute('data-id'),
            text: (it.querySelector('.pe-work-text') || {}).textContent || '',
            status: (it.querySelector('.pe-work-status') || {}).textContent || '',
            del: !!it.querySelector('.pe-work-del'),
            stBtns: [...it.querySelectorAll('.pe-work-st-btn')].map(b => ({
                st: b.getAttribute('data-st'),
                sel: b.classList.contains('st-sel')})),
            input: !!document.getElementById('peWorkInput'),
            addBtn: !!document.getElementById('peWorkAddBtn'),
        })) : [];
        return {descHidden: dv ? dv.hidden : null,
                worksHidden: wv ? wv.hidden : null,
                title: wv ? ((wv.querySelector('.pe-desc-title') || {}).textContent || '') : '',
                target: wv ? ((wv.querySelector('.pe-works-target') || {}).textContent || '') : '',
                hasInput: !!document.getElementById('peWorkInput'),
                hasAdd: !!document.getElementById('peWorkAddBtn'),
                yearBtnDisabled: btn ? btn.disabled : null,
                yearLabel: label ? label.textContent : '',
                selMonth: selTh ? selTh.textContent.trim() : '',
                items: items,
                docW: document.documentElement.scrollWidth,
                winW: window.innerWidth};})()""")


def click_name(page, text):
    page.evaluate("""(t) => {
        const tds = document.querySelectorAll('#peTable tbody td.pe-name');
        for (const td of tds) {
            if ((td.textContent || '').trim() === t) { td.click(); return true; }
        }
        return false;}""", text)


def click_month_th(page, index0):
    page.evaluate("""(i) => {
        const ths = document.querySelectorAll('tr.pe-head-months th');
        if (ths[i]) ths[i].click();}""", index0)


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t471');" +
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

        # ===== A: широкий 1600 — окно-описание, кнопка года, месяц
        print('== A: 1600px — описание, кнопка годов, выбранный месяц ==')
        open_section(page)
        page.wait_for_timeout(400)
        st = works_state(page)
        check('описание раздела видно (Task 469 жив)',
              st['descHidden'] is False and st['worksHidden'] is True, st)
        check('вид работ скрыт по умолчанию', st['worksHidden'] is True, st)
        check('подпись года «2026 год»', st['yearLabel'] == '2026 год', st['yearLabel'])
        check('кнопка предыдущего года АКТИВНА (архив 2025 есть)',
              st['yearBtnDisabled'] is False, st['yearBtnDisabled'])
        check('кнопка слева от подписи (в th.pe-th-year)',
              page.evaluate("""(() => {
                const th = document.querySelector('#peTable th.pe-th-year');
                const btn = document.getElementById('pePrevYearBtn');
                const lbl = document.getElementById('peYearLabel');
                if (!th || !btn || !lbl) return false;
                return th.contains(btn) && th.contains(lbl) &&
                       btn.getBoundingClientRect().right <= lbl.getBoundingClientRect().left;})()"""))
        lead = page.evaluate("""(() => {
            const d = document.getElementById('peDescView');
            return d ? (d.querySelector('.pe-desc-lead') || {}).textContent || '' : '';})()""")
        check('лид Task 469 в описании', 'Периодические работы' in lead, lead)
        check('выбранный месяц по умолчанию — текущий (%s)' %
              ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг',
               'Сен', 'Окт', 'Ноя', 'Дек'][CUR_MONTH - 1],
              st['selMonth'] != '', st['selMonth'])
        check('planEvents.years запрошен', len(calls('planEvents.years')) >= 1)
        shot(page, 'a-desktop-desc.png')

        # ===== B: год — переключение 2026 → 2025 → 2026
        print('== B: кнопка годов — 2026 → 2025 → 2026 ==')
        API_CALLS.clear()
        page.evaluate("document.getElementById('pePrevYearBtn').click()")
        page.wait_for_timeout(600)
        st = works_state(page)
        check('после клика: подпись «2025 год»', st['yearLabel'] == '2025 год',
              st['yearLabel'])
        check('отметки перезагружены за 2025 (planEvents.list year=2025)',
              any(c.get('year') == 2025 for c in calls('planEvents.list')),
              calls('planEvents.list'))
        check('кнопка активна (можно вернуться к текущему)',
              st['yearBtnDisabled'] is False, st['yearBtnDisabled'])
        page.evaluate("document.getElementById('pePrevYearBtn').click()")
        page.wait_for_timeout(600)
        st = works_state(page)
        check('повторный клик: возврат «2026 год» (младших нет)',
              st['yearLabel'] == '2026 год', st['yearLabel'])
        shot(page, 'b-year-switch.png')

        # ===== C: «Работы на следующий месяц» — интерфейс ввода
        print('== C: «Работы на следующий месяц» — ввод работ ==')
        API_CALLS.clear()
        click_name(page, 'Работы на следующий месяц')
        page.wait_for_timeout(700)
        st = works_state(page)
        check('описание скрыто, вид работ показан',
              st['descHidden'] is True and st['worksHidden'] is False, st)
        check('заголовок «Работы на следующий месяц»',
              st['title'] == 'Работы на следующий месяц', st['title'])
        exp_next = CUR_MONTH + 1 if CUR_MONTH < 12 else 1
        exp_year = 2026 if CUR_MONTH < 12 else 2027
        month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                       'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        check('цель — следующий месяц (%s %d)' %
              (month_names[exp_next - 1], exp_year),
              ('Месяц работ: %s %d' % (month_names[exp_next - 1], exp_year))
              in st['target'], st['target'])
        check('интерфейс ввода: поле + кнопка «Добавить»',
              st['hasInput'] and st['hasAdd'], st)
        check('работы месяца загружены (planWorks.list)',
              any(c.get('month') == exp_next and c.get('year') == exp_year
                  for c in calls('planWorks.list')), calls('planWorks.list'))
        check('мок-работа в перечне (Плановая поверка манометров)',
              any('поверка' in it['text'].lower() for it in st['items']),
              [it['text'] for it in st['items']])
        check('у работ есть «×» (удаление), НЕТ кнопок статуса',
              st['items'] and all(it['del'] for it in st['items']) and
              all(not it['stBtns'] for it in st['items']), st['items'])
        # Добавление работы
        page.fill('#peWorkInput', 'Продувка импульсных линий РО-1')
        page.click('#peWorkAddBtn')
        page.wait_for_timeout(700)
        st = works_state(page)
        added = calls('planWorks.add')
        check('запрос planWorks.add {year:%d, month:%d, работа}' %
              (exp_year, exp_next),
              len(added) == 1 and added[0].get('work') == 'Продувка импульсных линий РО-1'
              and added[0].get('year') == exp_year and added[0].get('month') == exp_next,
              added)
        check('новая работа в перечне после добавления',
              any('Продувка' in it['text'] for it in st['items']),
              [it['text'] for it in st['items']])
        check('поле ввода очищено', page.input_value('#peWorkInput') == '')
        # Удаление работы
        page.evaluate("""(() => {
            const it = document.querySelector('#peWorksView .pe-work-item');
            it.querySelector('.pe-work-del').click();})()""")
        page.wait_for_timeout(700)
        st = works_state(page)
        removed = calls('planWorks.remove')
        check('запрос planWorks.remove {id}', len(removed) == 1 and
              removed[0].get('id') is not None, removed)
        check('работа исчезла из перечня',
              not any('поверка' in it['text'].lower() for it in st['items']),
              [it['text'] for it in st['items']])
        shot(page, 'c-works-next.png')

        # ===== D: «Мероприятия» — снова описание раздела
        print('== D: «Мероприятия» (шапка) — снова описание ==')
        page.evaluate("""(() => {
            document.querySelector('#peTable th.pe-th-name').click();})()""")
        page.wait_for_timeout(400)
        st = works_state(page)
        check('описание вернулось, вид работ скрыт',
              st['descHidden'] is False and st['worksHidden'] is True, st)
        check('клик по обычному наименованию — окно не меняется',
              page.evaluate("""(() => {
                const wv = document.getElementById('peWorksView');
                document.querySelectorAll('#peTable tbody td.pe-name')[0].click();
                return wv.hidden;})()""") is True)

        # ===== E: «Работы на месяц» — перечень + отметка выполнения
        print('== E: «Работы на месяц» — перечень и статусы ==')
        API_CALLS.clear()
        click_name(page, 'Работы на месяц')
        page.wait_for_timeout(700)
        st = works_state(page)
        check('заголовок «Работы на месяц»', st['title'] == 'Работы на месяц',
              st['title'])
        check('цель — текущий месяц (%s 2026)' % month_names[CUR_MONTH - 1],
              ('Месяц работ: %s 2026' % month_names[CUR_MONTH - 1]) in st['target'],
              st['target'])
        check('две мок-работы октября в перечне', len(st['items']) == 2,
              [it['text'] for it in st['items']])
        check('у каждой работы 3 кнопки статуса (Выполнено/Частично/Не выполнено)',
              all([b['st'] for b in it['stBtns']] ==
                  ['выполнено', 'частично', 'не выполнено'] for it in st['items']),
              st['items'])
        check('форма ввода в виде перечня ОТСУТСТВУЕТ',
              not st['hasInput'] and not st['hasAdd'], st)
        pre = [it for it in st['items'] if 'Ревизия' in it['text']]
        check('предустановленный статус «частично» подсвечен',
              pre and any(b['sel'] for b in pre[0]['stBtns']) and
              'частично' in pre[0]['status'], pre)
        # Отметка «Выполнено» у первой работы
        page.evaluate("""(() => {
            const it = document.querySelector('#peWorksView .pe-work-item');
            it.querySelector('.pe-work-st-btn[data-st="выполнено"]').click();})()""")
        page.wait_for_timeout(700)
        st = works_state(page)
        sts = calls('planWorks.setStatus')
        check('запрос planWorks.setStatus {id, выполнено, дата сегодня}',
              len(sts) == 1 and sts[0].get('status') == 'выполнено' and
              sts[0].get('date') == TODAY_ISO and sts[0].get('id') is not None,
              sts)
        first = st['items'][0] if st['items'] else {}
        check('бейдж «Выполнено — ДД.ММ.ГГГГ» появился',
              'Выполнено' in first.get('status', '') and
              TODAY_ISO[8:10] + '.' + TODAY_ISO[5:7] in first.get('status', ''),
              first)
        check('кнопка «Выполнено» подсвечена (st-sel)',
              first.get('stBtns') and first['stBtns'][0]['sel'], first)
        shot(page, 'e-works-month.png')

        # ===== F: клик по месяцу шапки — месяц правого окна
        print('== F: месяцы шапки — выбор месяца правого окна ==')
        API_CALLS.clear()
        click_month_th(page, 10)  # «Ноя.» — ноябрь (индекс 10 с нуля)
        page.wait_for_timeout(500)
        st = works_state(page)
        check('подсветка переехала на «Ноя.»', st['selMonth'] == 'Ноя.', st['selMonth'])
        check('вид «Работы на месяц» перезагружен за ноябрь',
              ('Месяц работ: Ноябрь 2026') in st['target'], st['target'])
        check('planWorks.list за ноябрь (2026, 11)',
              any(c.get('year') == 2026 and c.get('month') == 11
                  for c in calls('planWorks.list')), calls('planWorks.list'))
        # Декабрь + «на следующий месяц» → Январь 2027 (переход года)
        click_name(page, 'Работы на следующий месяц')
        page.wait_for_timeout(700)
        click_month_th(page, 11)  # «Дек.»
        page.wait_for_timeout(700)
        st = works_state(page)
        check('декабрь + «следующий месяц» → Январь 2027 (переход года)',
              ('Месяц работ: Январь 2027') in st['target'], st['target'])
        check('работы января 2027 запрошены',
              any(c.get('year') == 2027 and c.get('month') == 1
                  for c in calls('planWorks.list')), calls('planWorks.list'))
        check('мобайл-селектор синхронен (Декабрь)',
              page.evaluate("document.getElementById('peMonthSel').value") == '12')
        shot(page, 'f-january-2027.png')

        # ===== G: узкий 1100 (< 1200) — колонка, вид под таблицей
        print('== G: 1100px — раскладка колонкой, клики живы ==')
        page.set_viewport_size({'width': 1100, 'height': 900})
        page.wait_for_timeout(500)
        g = page.evaluate("""(() => {
            const lay = document.querySelector('#page-plan-events .pe-layout');
            const card = lay.querySelector('.pe-card');
            const desc = lay.querySelector('.pe-desc-card');
            return {dir: getComputedStyle(lay).flexDirection,
                    cardTop: card.getBoundingClientRect().top,
                    descTop: desc.getBoundingClientRect().top};})()""")
        check('раскладка колонкой (описание/работы ПОД таблицей)',
              g['dir'] == 'column' and g['descTop'] > g['cardTop'], g)
        click_name(page, 'Работы на месяц')
        page.wait_for_timeout(600)
        st = works_state(page)
        check('вид работ кликабелен и на узком экране',
              st['worksHidden'] is False and 'Работы на месяц' == st['title'], st)
        check('нет горизонтального переполнения', st['docW'] <= st['winW'] + 1,
              (st['docW'], st['winW']))
        shot(page, 'g-1100-column.png')

        # ===== H: мобильный 375 — Task 464 жив + селектор месяца
        print('== H: 375px — мобайл (Task 464) + синхронный месяц ==')
        page.set_viewport_size({'width': 375, 'height': 800})
        page.wait_for_timeout(500)
        m = page.evaluate("""(() => {
            const rows = document.querySelectorAll('#peTable tbody tr.pe-row');
            let visible = 0, nameCells = 0;
            rows.forEach(tr => {
                const name = tr.querySelector('td.pe-name');
                if (name && getComputedStyle(name).display !== 'none'
                    && name.getBoundingClientRect().width > 0) nameCells++;
                tr.querySelectorAll('td.pe-m').forEach(td => {
                    if (getComputedStyle(td).display !== 'none'
                        && td.getBoundingClientRect().width > 0) visible++;
                });
            });
            const bar = document.querySelector('.pe-month-bar');
            const btn = document.getElementById('pePrevYearBtn');
            return {visible: visible, nameCells: nameCells,
                    barVisible: getComputedStyle(bar).display !== 'none',
                    btnVisible: btn.getBoundingClientRect().width > 0,
                    sel: document.getElementById('peMonthSel').value};})()""")
        check('Task 464: один месяц × 10 строк = 10 видимых ячеек',
              m['visible'] == 10 and m['nameCells'] == 10, m)
        check('полоса «Месяц» (селектор) видна', m['barVisible'], m)
        check('кнопка годов видна на мобайле', m['btnVisible'], m)
        check('мобайл-селектор на декабре (синхронен с шапкой)',
              m['sel'] == '12', m['sel'])
        page.select_option('#peMonthSel', '11')  # ноябрь
        page.wait_for_timeout(600)
        st = works_state(page)
        check('смена месяца селектором → цель «Ноябрь 2026» в окне работ',
              ('Месяц работ: Ноябрь 2026') in st['target'], st['target'])
        check('подсветка шапки переехала на «Ноя.»', st['selMonth'] == 'Ноя.',
              st['selMonth'])
        check('0 JS-ошибок во всех сценариях', not js_errors, js_errors[:3])
        shot(page, 'h-mobile-375.png')

        browser.close()
    server.shutdown()

    print()
    print('ИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
