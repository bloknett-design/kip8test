#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 416: browser-check — заявка «Я добавил в таблицу Список_И_и_ПЗ
# новый столбец E "сокращение"… применять на странице Табель учёта
# рабочего времени, в окне мероприятий и в мини окнах шахматки и
# фамилий работников».
# ПРОВЕРКИ (мок-сервер, порт 8917):
#   1) десктоп 1280 тёмная, edit, ЖИВОЙ лист с сокращениями:
#      тултип бейджа «И — Инстр. ОТ», окно «Мероприятия в этот день»,
#      окно «Мероприятия» (месяц), попап фамилии (заголовки групп —
#      сокращение + title-полное), карточка «Работники» (плоские
#      строки — сокращение), ПЕЧАТЬ табеля (список мероприятий —
#      сокращение; window.print замокан), форма «+ Инструктаж…» —
#      select по ПОЛНЫМ названиям (регресс 410-412), кэш-путь;
#   2) десктоп 1280 светлая, view, СТАРЫЙ сервер (без «сокращение»):
#      полные названия везде (деградация) + день-окно полные;
#   3) мобайл 375 светлая, edit: карточка — сокращения в плоских строках.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8917
TODAY = datetime.date.today()
Y = TODAY.year

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

def ru(iso):
    p = iso.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]

# канон Task 409/412 + СОКРАЩЕНИЯ (столбец E)
N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_OG = 'Повторный инструктаж по инструкции № 9-ОГЭ'
N_SAM = 'Периодическая проверка знаний на допуск к самостоятельной работе'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_VY = 'Периодическая проверка знаний по охране труда при выполнении работ на высоте'
S_OT = 'Инстр. ОТ'
S_OG = 'Инстр. 9-ОГЭ'
S_SAM = 'ПЗ самост.'
S_EL = 'ПЗ ЭБ до 1000 В'
S_VY = 'ПЗ высота'

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, TODAY.month, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, TODAY.month, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '', 'комментарий': ''},
]
INSTR_ALL = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': N_OT,
   'дата_начала': d(Y, TODAY.month, 15), 'дата_окончания': d(Y, TODAY.month, 15),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 102, 'таб_номер': '017', 'тип': 'проверка_знаний', 'тема': N_EL,
   'дата_начала': d(Y, TODAY.month, 20), 'дата_окончания': d(Y, TODAY.month, 20),
   'длительность_дней': 1, 'комментарий': ''},
]
EVENTS_ALL = []
TRAININGS = list(INSTR_ALL)  # годовой срез (обоих листов) для окон/печати
VACATIONS = []
PPE = []
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день'},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
  {'id': 2, 'name': 'Дневной 5/2', 'cycle': 7, 'description': '',
   'days': [{'day': 1, 'status': 'Д8'}, {'day': 2, 'status': 'Д8'},
            {'day': 3, 'status': 'Д8'}, {'day': 4, 'status': 'Д8'},
            {'day': 5, 'status': 'Д8'}, {'day': 6, 'status': ''},
            {'day': 7, 'status': ''}]},
]

# ЖИВОЙ лист с сокращениями (столбец E)
INSTR_LIST_SHORT = [
  {'название': N_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': S_OT},
  {'название': N_OG, 'вид': 'инструктаж', 'периодичность': 3,
   'основание': '', 'сокращение': S_OG},
  {'название': N_SAM, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': S_SAM},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': S_EL},
  {'название': N_VY, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': 'инструкция № 53-ОТ', 'сокращение': S_VY},
]
# СТАРЫЙ сервер: поля «сокращение» нет вовсе
INSTR_LIST_OLD = [
  {'название': N_OT, 'вид': 'инструктаж', 'периодичность': 6, 'основание': ''},
  {'название': N_OG, 'вид': 'инструктаж', 'периодичность': 3, 'основание': ''},
  {'название': N_SAM, 'вид': 'проверка_знаний', 'периодичность': 12, 'основание': ''},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12, 'основание': ''},
  {'название': N_VY, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': 'инструкция № 53-ОТ'},
]

PASS = 0
FAIL = 0
ADMIN = False
LIVE = True   # False → старый сервер (без сокращений)


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  + ' if ok else '  X ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if ADMIN else 'КИП ИОС'}}
    if action == 'getMyAccess':
        if ADMIN:
            perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                     'workschedule.view': True, 'workschedule.edit': True}
            role = 'Админ'
        else:
            perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                     'workschedule.view': True, 'workschedule.edit': False,
                     'workschedule.view.min': False}
            role = 'КИП ИОС'
        return {'ok': True, 'data': {'role': role, 'found': True, 'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        inc = bool(body and body.get('includeArchived'))
        emps = EMPLOYEES if inc else [e for e in EMPLOYEES if not e['в_архиве']]
        return {'ok': True, 'data': {'employees': emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        lst = INSTR_LIST_SHORT if LIVE else INSTR_LIST_OLD
        return {'ok': True, 'data': {'trainings': list(TRAININGS),
                                    'instrList': list(lst),
                                    'instrAll': list(INSTR_ALL),
                                    'eventsAll': list(EVENTS_ALL)}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': list(VACATIONS)}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': list(PPE)}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.addTraining':
        return {'ok': True, 'data': {'id': 100}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, keep_cache=False):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    pre = ''
    if not keep_cache:
        pre += ("try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
                "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};")
    ctx.add_init_script(
        pre +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t416-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try: body = json.loads(pd_)
            except Exception: body = None
        resp = api_response(action, body)
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                              body=json.dumps(resp, ensure_ascii=False))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t416-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def open_workers_card(page, fio='Иванов И. И.'):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('%s')" % fio)
    page.wait_for_timeout(900)


def find_event_cell(page):
    """клик по ячейке с бейджем И; возвращает (дата, title бейджа, html)"""
    return page.evaluate("""(function(){
    var wrap = document.getElementById('wsGridWrap');
    var rows = wrap.querySelectorAll('tbody tr');
    for (var i = 0; i < rows.length; i++) {
        var emp = rows[i].querySelector('td.ws-emp-col[data-tab='017']')
    }
    return null;
})()""" if False else """(function(){
    var badges = document.querySelectorAll('#wsGridWrap .ws-ev-badge');
    for (var i = 0; i < badges.length; i++) {
        var t = badges[i].getAttribute('title') || '';
        if (t.indexOf('Инстр') !== -1 || t.indexOf('И —') !== -1) {
            var cell = badges[i].closest('td.ws-cell');
            var oc = cell ? (cell.getAttribute('onclick') || '') : '';
            var m = oc.match(/onCellClick\\(event, '([0-9-]+)'/);
            cell.click();
            return {date: m ? m[1] : '', title: t};
        }
    }
    return null;
})()""")


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit, живой лист ==========
    print('=== Контекст 1: десктоп тёмная edit — сокращения из столбца E ===')
    ADMIN = True
    LIVE = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'short-dark', keep_cache=True)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    # --- тултип бейджа шахматки (мини-окно) ---
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    ev = find_event_cell(page)
    check('B1: бейдж И в сетке найден и кликнут (%s)' % (ev or {}).get('date'),
          ev is not None)
    check('B2: ЗАЯВКА 416 — тултип бейджа «И — Инстр. ОТ»',
          (ev or {}).get('title') == 'И — ' + S_OT, (ev or {}).get('title'))
    page.wait_for_timeout(700)

    # --- окно «Мероприятия в этот день» (мини-окно шахматки) ---
    day_html = page.evaluate("(document.getElementById('wsEventsPopup')||{}).innerHTML || ''")
    day_text = page.evaluate("(document.getElementById('wsEventsPopup')||{}).innerText || ''")
    check('B3: окно дня — строка показывает сокращение',
          S_OT in day_text or S_OT in day_html, day_text[:120])
    check('B4: окно дня — полного названия НЕТ',
          N_OT not in day_text, day_text[:150])
    page.screenshot(path='task416-proof-day-window.png', full_page=False)
    page.evaluate("WorkSchedule.closeCellPopup && WorkSchedule.closeCellPopup()")
    page.wait_for_timeout(300)

    # --- окно «Мероприятия» (месяц) ---
    month_text = page.evaluate("(document.getElementById('wsEventsPanel')||{}).innerText || ''")
    check('C1: окно месяца — строки с сокращениями',
          (S_OT in month_text) and (S_EL in month_text), month_text[:200])
    check('C2: окно месяца — полных названий НЕТ',
          N_OT not in month_text and N_EL not in month_text, month_text[:200])

    # --- попап фамилии (мини-окно, групповой вид) ---
    page.click('.ws-grid tbody tr:first-child td.ws-emp-col')
    page.wait_for_timeout(900)
    emp_html = page.evaluate("(document.getElementById('wsEmpPopup')||{}).innerHTML || ''")
    emp_text = page.evaluate("(document.getElementById('wsEmpPopup')||{}).innerText || ''")
    check('D1: попап фамилии — заголовки групп с сокращениями',
          S_OT in emp_text and S_EL in emp_text, emp_text[:200])
    check('D2: попап фамилии — title-тултип несёт ПОЛНОЕ название',
          ('title="%s"' % N_OT) in emp_html and
          ('title="%s"' % N_EL) in emp_html,
          'title-атрибуты групп')
    page.screenshot(path='task416-proof-emp-popup.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmpPopup()")
    page.wait_for_timeout(300)

    # --- карточка «Работники» (плоские строки) ---
    open_workers_card(page)
    card = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1)
            return {text: cards[i].innerText, html: cards[i].innerHTML};
    }
    return {text: '', html: ''};
})()""")
    check('E1: карточка — плоские строки с сокращениями',
          (S_OT + ' · ') in card['text'] and (S_EL + ' · ') in card['text'],
          card['text'][:200])
    check('E2: карточка — полных названий НЕТ',
          N_OT not in card['text'] and N_EL not in card['text'], card['text'][:200])
    page.screenshot(path='task416-proof-card-flat.png', full_page=False)

    # --- форма «+ Инструктаж…» — select по ПОЛНЫМ названиям (регресс) ---
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate("""(function(){
    var sel = document.getElementById('wsTrTitleSel');
    return {opts: sel ? Array.prototype.map.call(sel.options, function(o){return o.value;}) : null};
})()""")
    check('F1: форма — select по ПОЛНЫМ названиям (регресс 410/412)',
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY], fs['opts'])
    page.evaluate("WorkSchedule.closeTrainingForm && WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # --- печать табеля (страница «Табель учёта рабочего времени») ---
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    page.evaluate("window.print = function(){ window.__printed = true; }")
    page.click('#wsPrintBtn')
    page.wait_for_timeout(1200)
    printed = page.evaluate("document.getElementById('wsPrintSheet') ? document.getElementById('wsPrintSheet').innerText : ''")
    check('G1: печать табеля — список мероприятий с сокращениями',
          (S_OT in printed) and (S_EL in printed), printed[-300:])
    check('G2: печать табеля — полных названий НЕТ',
          N_OT not in printed and N_EL not in printed, printed[-300:])
    check('G3: window.print вызван', page.evaluate("!!window.__printed"))
    page.screenshot(path='task416-proof-print.png', full_page=False)

    # --- перезагрузка: кэш-путь ---
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    month_text2 = page.evaluate("(document.getElementById('wsEventsPanel')||{}).innerText || ''")
    check('H1: после перезагрузки (кэш) — сокращения сохранены',
          S_OT in month_text2, month_text2[:150])
    check('H2: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view, СТАРЫЙ сервер ==========
    print('=== Контекст 2: десктоп светлая view — старый сервер (без E) ===')
    ADMIN = False
    LIVE = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'old-view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    month_text = page.evaluate("(document.getElementById('wsEventsPanel')||{}).innerText || ''")
    check('I1: старый сервер — ПОЛНЫЕ названия в окне месяца',
          N_OT in month_text and S_OT not in month_text, month_text[:200])
    ev = find_event_cell(page)
    check('I2: старый сервер — тултип бейджа с полным названием',
          ev is not None and ev['title'] == 'И — ' + N_OT,
          (ev or {}).get('title'))
    page.wait_for_timeout(700)
    day_text = page.evaluate("(document.getElementById('wsEventsPopup')||{}).innerText || ''")
    check('I3: старый сервер — окно дня с полным названием',
          N_OT in day_text, day_text[:150])
    page.screenshot(path='task416-proof-old-server.png', full_page=False)
    check('I4: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, edit ==========
    print('=== Контекст 3: мобайл 375 светлая edit ===')
    ADMIN = True
    LIVE = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'short-mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_workers_card(page)
    card = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1)
            return {text: cards[i].innerText};
    }
    return {text: ''};
})()""")
    check('J1: мобайл — плоские строки с сокращениями',
          (S_OT + ' · ') in card['text'], card['text'][:150])
    page.screenshot(path='task416-proof-card-mobile.png', full_page=False)
    check('J2: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
