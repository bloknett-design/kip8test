#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 522 browser-check: Табель — окно ячейки «Мероприятия в этот
# день» с НОВОЙ секцией «Статус дня» для «д»/«н» ДНЕВНОГО персонала
# (справка по коду + «Время работы: N ч» из колонки K), заявка:
# «При нажатии или наведении курсора мыши на ячейку с кодом «д» для
# дневного персонала, должен появляться попап с информацией по этому
# коду и временем работы»:
#  A) ХОВЕР день-«д» (7,2 ч, БЕЗ мероприятий) → окно с секцией:
#     свотч + код + полное название + «Время работы: 7,2 ч» +
#     «нет мероприятий»;
#  B) ХОВЕР день-«д» (часы НЕ указаны) → «Время работы: не указано»;
#  C) ХОВЕР день-«д» + мероприятие → секция И строка события;
#  D) ХОВЕР сменный «д» (без мероприятий) → окно НЕ открывается;
#  E) ХОВЕР пустая ячейка → окно НЕ открывается (регресс Task 487);
#  F) mouseleave → окно закрывается (grace 350 мс);
#  G) КЛИК редактора → окно кодов + окно мероприятий сверху с секцией;
#  H) КЛИК зрителя (edit=false) → ТОЛЬКО окно мероприятий с секцией;
#  I) 0 JS-ошибок; скриншоты в download/kip8test-task522/.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
D1 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 11)))   # день-«д» 7,2 ч
D2 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 12)))   # день-«д» без часов
D3 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 13)))   # день-«д» + мероприятие
D4 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 14)))   # сменный «д»
D5 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 15)))   # пустая ячейка
DAY1, DAY2, DAY3, DAY4, DAY5 = 11, 12, 13, 14, 15
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task522')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0
VIEWER = False


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


DN_NAME = ('День, плановая продолжительность работы в выходные и '
           'нерабочие праздничные дни, для сменного персонала дневная '
           '12-часовая смена (с 7:30 до 19:30), для дневного персонала — '
           'с указанием продолжительности (в часах) в комментарии')

CODES = [
  {'code': 'Д', 'name': 'День, плановая 12-часовая смена', 'color': '#FFE082'},
  {'code': 'д', 'name': DN_NAME, 'color': '#FFD54F'},
  {'code': 'н', 'name': 'Ночь в вых./праздник', 'color': '#78909C'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной',
   'смена': '', 'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
# записи месяца: колонка K «часы» — единственное «время» дневного
ENTRIES = [
  {'дата': D1, 'таб_номер': '023', 'статус': 'д', 'часы': 7.2,
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
  {'дата': D2, 'таб_номер': '023', 'статус': 'д', 'часы': None,
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
  {'дата': D3, 'таб_номер': '023', 'статус': 'д', 'часы': 8,
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
  {'дата': D4, 'таб_номер': '017', 'статус': 'д', 'часы': None,
   'переработка': 1, 'праздник': 0, 'источник': 'авто',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
]
TRAININGS = [
  {'id': 301, 'таб_номер': '023', 'тип': 'инструктаж',
   'дата_начала': D3, 'дата_окончания': D3,
   'тема': 'Повторный инструктаж по охране труда', 'выполнение': 1}
]


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': not VIEWER}}}
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


# пометить ячейку (таб. номер + день) для page.hover — СНИМАЯ
# предыдущие метки (иначе локатор находит СТАРУЮ ячейку)
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
    # увести мышь с окна/ячейки (шапка сетки) и переждать
    # grace-таймер 350 мс — окно закрывается ДО следующего сценария
    # (иначе открытый попап ПЕРЕКРЫВАЕТ соседнюю ячейку и page.hover
    # не может навестись на неё)
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
            codesWin: !!(codes && codes.classList.contains('active'))};})()""")


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

        # ================= РЕДАКТОР: ховер-сценарии =================
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t522');" +
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

        # ===== A: ховер день-«д» 7,2 ч, БЕЗ мероприятий =====
        print('== A: ховер день-«д» (7,2 ч, без мероприятий) ==')
        check('A: ячейка помечена', mark_cell(page, '023', DAY1))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('A: окно открылось ХОВЕРОМ (заявка: без мероприятий)',
              st['win'], st)
        check('A: секция «Статус дня» в окне',
              'ws-dn-info' in st['html'], st['html'][:200])
        check('A: код «д» в секции', 'ws-dn-info-code">д<' in st['html'])
        check('A: ПОЛНОЕ название кода (справка)',
              'плановая продолжительность работы в выходные' in st['html'])
        check('A: «Время работы: 7,2 ч» (колонка K)',
              'Время работы: 7,2 ч' in st['html'])
        check('A: «нет мероприятий» — прежнее поведение',
              'нет мероприятий' in st['html'])
        check('A: окно кодов НЕ открыто (ховер не клик)',
              not st['codesWin'])
        shot(page, 'a-hover-dn-info.png')
        close_hover_window(page)

        # ===== B: ховер день-«д» без часов =====
        print('== B: ховер день-«д» (часы не указаны) ==')
        check('B: ячейка помечена', mark_cell(page, '023', DAY2))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('B: окно открылось', st['win'])
        check('B: «Время работы: не указано»',
              'Время работы: не указано' in st['html'], st['html'][:200])
        shot(page, 'b-hover-dn-no-hours.png')
        close_hover_window(page)

        # ===== C: ховер день-«д» + мероприятие =====
        print('== C: ховер день-«д» + мероприятие ==')
        check('C: ячейка помечена', mark_cell(page, '023', DAY3))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('C: окно открылось', st['win'])
        check('C: секция «Статус дня» есть', 'ws-dn-info' in st['html'])
        check('C: «Время работы: 8 ч»', 'Время работы: 8 ч' in st['html'])
        check('C: мероприятие рядом',
              'Повторный инструктаж по охране труда' in st['html'])
        check('C: секция НАД мероприятием (порядок)',
              st['html'].find('ws-dn-info') < st['html'].find('Повторный'))
        shot(page, 'c-hover-dn-event.png')
        close_hover_window(page)

        # ===== D: ховер сменный «д» без мероприятий =====
        print('== D: ховер сменный «д» — тишина ==')
        check('D: ячейка помечена', mark_cell(page, '017', DAY4))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(400)
        st = events_popup_state(page)
        check('D: окно НЕ открылось (сменному часов нет)',
              not st['win'], st)

        # ===== E: ховер пустая ячейка =====
        print('== E: ховер пустая ячейка — тишина (регресс) ==')
        check('E: ячейка помечена', mark_cell(page, '023', DAY5))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(400)
        st = events_popup_state(page)
        check('E: окно НЕ открылось (прежний гейт жив)', not st['win'], st)

        # ===== F: mouseleave → окно закрылось =====
        print('== F: уход курсора закрывает окно ==')
        check('F: ячейка помечена', mark_cell(page, '023', DAY1))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        check('F: окно открылось', events_popup_state(page)['win'])
        # увести мышь на шапку страницы (вне ячейки и вне окна)
        page.hover('#wsGridWrap thead th')
        page.wait_for_timeout(700)  # grace 350 мс + запас
        check('F: окно закрылось после ухода',
              not events_popup_state(page)['win'])

        # ===== G: КЛИК редактора =====
        print('== G: клик редактора по день-«д» ==')
        click_cell(page, '023', DAY1)
        page.wait_for_timeout(400)
        st = events_popup_state(page)
        check('G: окно кодов открыто', st['codesWin'])
        check('G: окно мероприятий сверху открыто', st['win'])
        check('G: секция «Статус дня» в окне мероприятий',
              'ws-dn-info' in st['html'] and 'Время работы: 7,2 ч' in st['html'])
        shot(page, 'g-click-editor.png')
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)  # анти-дребезг 400 мс

        # ===== ЗРИТЕЛЬ: клик-сценарий =====
        global VIEWER
        VIEWER = True
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 720})
        page2 = ctx2.new_page()
        page2.on('pageerror', lambda e: js_errors.append('viewer: ' + str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        ctx2.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t522v');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        ctx2.route('**/exec?**', handle)
        ctx2.route('**script.google.com/**', handle)
        ctx2.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx2.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx2.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        open_grid(page2)

        print('== H: клик зрителя по день-«д» ==')
        click_cell(page2, '023', DAY1)
        page2.wait_for_timeout(400)
        st2 = events_popup_state(page2)
        check('H: окно мероприятий открыто', st2['win'])
        check('H: окно кодов зрителю НЕ показывается', not st2['codesWin'])
        check('H: секция «Статус дня» с временем',
              'ws-dn-info' in st2['html'] and 'Время работы: 7,2 ч' in st2['html'])
        shot(page2, 'h-click-viewer.png')

        print('== I: JS-ошибки ==')
        check('I: JS-ошибок нет', len(js_errors) == 0, js_errors[:5])

        browser.close()
        server.shutdown()

    print()
    print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


main()
