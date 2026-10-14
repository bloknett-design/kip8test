#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 524 browser-check: наименования кодов «д»/«н» — хвост
# «в комментарии» убран. Заявка: «В описании кодов "д" и "н" убери в
# конце текст "в комментарии".» Мок листа «Коды_статусов» отдаёт
# ЛЕГАСИ-формулировки (как в живом листе Google Sheets до
# statusCodesReplace()) — приложение обязано показывать НОВЫЕ
# имена канона (нормализация Task 387):
#  A) ХОВЕР день-«д» (7,2 ч) → секция «Статус дня»: полное название
#     оканчивается «(в часах)», «в комментарии» НЕТ, время работы живо;
#  B) ХОВЕР день-«н» (пара 19:30–07:30, 12 ч) → новое название «н»,
#     «в комментарии» НЕТ, «19:30–07:30 · 12 ч (через полночь)»;
#  C) КЛИК редактора день-«д» → окно кодов: строка «д» — новое
#     название, «в комментарии» в окне НЕТ (ОВ в моке нет);
#  D) панель «Обозначения» → расшифровка «д»/«н» — новые названия,
#     «в комментарии» НЕТ; short «день/ночь в выходной» жив;
#  E) 0 JS-ошибок; скриншоты в download/kip8test-task524/.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8997
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
D1 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 11)))   # день-«д» 7,2 ч
D2 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 12)))   # день-«н» ночь
DAY1, DAY2 = 11, 12
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task524')
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
          (('  [' + str(extra)[:240] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


# ЛЕГАСИ-лист «Коды_статусов»: СТАРЫЕ формулировки «д»/«н» с хвостом
# «в комментарии» (как в живой таблице) — нормализация каноном обязана
# показать НОВЫЕ имена (Task 524). ОВ в мок НЕ включён: «в комментарии»
# в отрендеренном UI должно отсутствовать ЦЕЛИКОМ.
DN_OLD = ('День, плановая продолжительность работы в выходные и '
          'нерабочие праздничные дни, для сменного персонала дневная '
          '12-часовая смена (с 7:30 до 19:30), для дневного персонала — '
          'с указанием продолжительности (в часах) в комментарии')
NN_OLD = ('Ночь, плановая продолжительность работы в выходные и '
          'нерабочие праздничные дни, для сменного персонала ночная '
          '12-часовая смена (с 19:30 до 7:30), для дневного персонала — '
          'с указанием продолжительности (в часах) в комментарии')
CODES = [
  {'code': 'Д', 'name': 'День, плановая 12-часовая смена', 'color': '#FFE082'},
  {'code': 'д', 'name': DN_OLD, 'color': '#FFD54F'},
  {'code': 'н', 'name': NN_OLD, 'color': '#78909C'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
]
EMPLOYEES = [
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной',
   'смена': '', 'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 2, 'name': 'Дневной 5/2', 'cycle': 7, 'description': '',
   'days': [{'day': 1, 'status': 'Д8'}, {'day': 2, 'status': 'Д8'},
            {'day': 3, 'status': 'Д8'}, {'day': 4, 'status': 'Д8'},
            {'day': 5, 'status': 'Д7,2'}, {'day': 6, 'status': ''},
            {'day': 7, 'status': ''}]},
]
ENTRIES = [
  {'дата': D1, 'таб_номер': '023', 'статус': 'д', 'часы': 7.2,
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': '', 'время_начала': None, 'время_окончания': None},
  {'дата': D2, 'таб_номер': '023', 'статус': 'н', 'часы': 12,
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': '', 'время_начала': '19:30', 'время_окончания': '07:30'},
]
TRAININGS = []


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


MARK_JS = r"""(([t, dn]) => {
    document.querySelectorAll('[data-testid="hc"]')
        .forEach(c => c.removeAttribute('data-testid'));
    const emp = document.querySelector('td.ws-emp-col[data-tab="' + t + '"]');
    const td = emp.closest('tr').querySelector('td[data-day="' + dn + '"]');
    td.setAttribute('data-testid', 'hc');
    return !!td;})"""


def mark_cell(page, tab, day):
    return page.evaluate(MARK_JS, [tab, str(day)])


def close_hover_window(page):
    try:
        page.hover('#wsGridWrap thead th', timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(700)


def events_popup_state(page):
    return page.evaluate("""(() => {
        const w = document.getElementById('wsEventsPopup');
        const codes = document.getElementById('wsCellPopup');
        return {
            win: !!(w && w.classList.contains('active')),
            html: w ? w.innerHTML : '',
            codesWin: !!(codes && codes.classList.contains('active')),
            codesHtml: codes ? codes.innerHTML : ''};})()""")


def click_cell(page, tab, day):
    page.evaluate("""((p) => {
        const empCell = document.querySelector(
            'td.ws-emp-col[data-tab="' + p.tab + '"]');
        const td = empCell.closest('tr')
            .querySelector('td[data-day="' + p.day + '"]');
        td.dispatchEvent(new MouseEvent('click',
            {bubbles: true, cancelable: true}));})""",
        {'tab': tab, 'day': str(day)})


def open_grid(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    # Task 486: тихое обновление (~4 с от старта) перерисовывает
    # раздел — ждём ЗАВЕРШЕНИЯ, чтобы сетка была стабильна
    page.wait_for_timeout(2500)


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t524');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            action = ''
            if 'action=' in request.url:
                action = unquote(request.url.split('action=')[1].split('&')[0])
            body = {}
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except Exception:
                    body = {}
            return route.fulfill(status=200,
                content_type='application/json; charset=utf-8',
                body=json.dumps(mock_response(action, body), ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        open_grid(page)

        # ===== A: ховер день-«д» (7,2 ч) — секция «Статус дня» =====
        print('== A: ховер день-«д» (легаси-лист → новое название) ==')
        check('A: ячейка помечена', mark_cell(page, '023', DAY1))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('A: окно открылось ховером', st['win'], st)
        check('A: секция «Статус дня» в окне',
              'ws-dn-info' in st['html'], st['html'][:200])
        check('A: новое название «д» — окончание «(в часах)»',
              'с указанием продолжительности (в часах)' in st['html'])
        check('A: хвоста «в комментарии» в секции НЕТ',
              'в комментарии' not in st['html'])
        check('A: «Время работы: 7,2 ч» живо (Task 522)',
              'Время работы: 7,2 ч' in st['html'])
        shot(page, 'a-hover-dn-new-wording.png')
        close_hover_window(page)

        # ===== B: ховер день-«н» (пара 19:30–07:30, полночь) =====
        print('== B: ховер день-«н» (ночная пара, полночь) ==')
        check('B: ячейка помечена', mark_cell(page, '023', DAY2))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('B: окно открылось ховером', st['win'], st)
        check('B: код «н» в секции', 'ws-dn-info-code">н<' in st['html'])
        check('B: новое название «н» — ночная смена (с 19:30 до 7:30)',
              'для сменного персонала ночная 12-часовая смена (с 19:30 до 7:30)'
              in st['html'])
        check('B: хвоста «в комментарии» в секции НЕТ',
              'в комментарии' not in st['html'])
        check('B: «19:30–07:30 · 12 ч (через полночь)» живо (Task 523)',
              'Время работы: 19:30–07:30 · 12 ч (через полночь)'
              in st['html'])
        shot(page, 'b-hover-nn-new-wording.png')
        close_hover_window(page)

        # ===== C: клик редактора — окно кодов =====
        print('== C: клик редактора день-«д» — окно кодов ==')
        click_cell(page, '023', DAY1)
        page.wait_for_timeout(400)
        st = events_popup_state(page)
        check('C: окно кодов открыто', st['codesWin'], st)
        check('C: окно мероприятий открыто (секция сверху)',
              st['win'])
        check('C: строка «д» в окне кодов — новое название',
              ('с указанием продолжительности (в часах)'
               in st['codesHtml']))
        check('C: «в комментарии» в окне кодов НЕТ (ОВ в моке нет)',
              'в комментарии' not in st['codesHtml'])
        check('C: «в комментарии» в окне мероприятий НЕТ',
              'в комментарии' not in st['html'])
        shot(page, 'c-click-codes-window.png')
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        # ===== D: панель «Обозначения» (легенда, широкий вид) =====
        print('== D: панель «Обозначения» (широкий вид с полными названиями) ==')
        page.click('#wsLegendBtn')
        page.wait_for_timeout(400)
        # Task 387/388: широкий вид — шеврон #wsLgChv (toggleLegendWide):
        # .ws-lg-short скрыт, .ws-lg-name (полные названия) показан
        wide_before = page.evaluate(
            "() => !!document.getElementById('wsLegendDrawer')"
            ".classList.contains('ws-lg-wide')")
        if not wide_before:
            page.click('#wsLgChv')
            page.wait_for_timeout(500)
        lg = page.evaluate("""(() => {
            const btn = document.getElementById('wsLegendBtn');
            const d = document.getElementById('wsLegendDrawer');
            const b = document.getElementById('wsLegendBody');
            return {open: !!(btn && btn.getAttribute('aria-pressed') === 'true'
                             && d && d.style.marginRight === '0px'),
                    wide: !!(d && d.classList.contains('ws-lg-wide')),
                    html: b ? b.innerHTML : ''};})()""")
        check('D: панель открылась', lg['open'], lg)
        check('D: широкий вид (полные названия)', lg['wide'], lg)
        check('D: расшифровка «д» — новое название',
              ('с указанием продолжительности (в часах)'
               in lg['html']))
        check('D: расшифровка «н» — новое название (ночная смена)',
              'ночная 12-часовая смена (с 19:30 до 7:30)' in lg['html'])
        check('D: «в комментарии» в панели НЕТ',
              'в комментарии' not in lg['html'])
        check('D: short «день в выходной» жив',
              'день в выходной' in lg['html'])
        shot(page, 'd-legend-panel.png')
        page.click('#wsLegendBtn')
        page.wait_for_timeout(300)
        # ===== E: JS-ошибки =====
        print('== E: стабильность ==')
        check('E: 0 JS-ошибок', not js_errors, js_errors[:5])

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d/%d (pass/total)' % (PASS, PASS + FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
