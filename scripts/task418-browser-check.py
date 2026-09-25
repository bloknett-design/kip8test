#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 418: browser-check — заявка «В таблице "Инструктажи" я заменил
# название столбца "дата_начала" на "дата_проведения", столбца
# "дата_окончания" на "выполнение", столбца "длительность_дней" на
# "просрочен"...» (логика столбцов + отметка о выполнении из блока
# карточки работника).
# ПРОВЕРКИ (мок-сервер, порт 8919; instrAll несёт поля
# дата_проведения/выполнение/просрочен):
#   1) десктоп 1280 тёмная, edit:
#      • строки блока «Повторные инструктажи…» карточки: ГАЛОЧКА
#        отметки (пустая — нет, зелёная ✓ — выполнено), бейдж
#        «просрочен» (дата прошла, отметки нет), выполненная строка
#        приглушена;
#      • клик по галочке → API workSchedule.setTrainingDone
#        (выполнение 0↔1), UI обновляется: галочка/бейдж/строка;
#      • блок «Мероприятия» БЕЗ галочек (только инструктажи);
#      • правка ✎ жива (регресс 417); кэш-путь после перезагрузки;
#   2) десктоп 1280 светлая, view: галочка некликабельна (состояние
#      видно), бейдж «просрочен» виден, ✎/✕ нет;
#   3) мобайл 375 тёмная, edit: галочка кликабельна, разметка цела.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8919
TODAY = datetime.date.today()
Y = TODAY.year


def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)


# даты записей: прошедшая (внутри текущего года), будущая
past_dt = TODAY - datetime.timedelta(days=10)
if past_dt.year != Y:
    past_dt = datetime.date(Y, 1, 1)
future_dt = TODAY + datetime.timedelta(days=30)
PAST = d(past_dt.year, past_dt.month, past_dt.day)
FUTURE = d(future_dt.year, future_dt.month, future_dt.day)
TODAY_ISO = d(TODAY.year, TODAY.month, TODAY.day)

N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_PB = 'Повторный инструктаж по пожарной безопасности'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
]

# записи листа «Инструктажи» в НОВОМ формате заявки (Task 418):
#   601 — прошедшая дата, отметки нет → просрочен 1
#   602 — будущая дата, отметки нет → просрочен 0
#   603 — прошедшая дата с отметкой → просрочен 0
INSTR_ALL = [
  {'id': 601, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': N_OT,
   'дата_начала': PAST, 'дата_окончания': PAST, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': PAST, 'выполнение': 0, 'просрочен': 1},
  {'id': 602, 'таб_номер': '0871', 'тип': 'проверка_знаний', 'тема': N_EL,
   'дата_начала': FUTURE, 'дата_окончания': FUTURE, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': FUTURE, 'выполнение': 0, 'просрочен': 0},
  {'id': 603, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': N_PB,
   'дата_начала': PAST, 'дата_окончания': PAST, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': PAST, 'выполнение': 1, 'просрочен': 0},
]
TRAININGS = [dict(r) for r in INSTR_ALL]   # годовой срез сетки
EVENTS_ALL = [
  {'id': 700, 'таб_номер': '0871', 'тип': 'обучение', 'тема': 'Курс АСУ ТП',
   'дата_начала': PAST, 'дата_окончания': PAST, 'длительность_дней': 1,
   'комментарий': ''},
]
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
]
INSTR_LIST = [
  {'название': N_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': 'Инстр. ОТ'},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': 'ПЗ ЭБ до 1000 В'},
]

DONE_CALLS = []

PASS = 0
FAIL = 0
ADMIN = True


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
        # свежие копии при каждом ответе: TRAININGS-снапшот на импорте
        # разошёлся бы с setTrainingDone (клиентский _TRAININGS держал
        # бы старые флаги — переключение уходило «не туда»)
        return {'ok': True, 'data': {'trainings': [dict(r) for r in INSTR_ALL],
                                    'instrList': list(INSTR_LIST),
                                    'instrAll': [dict(r) for r in INSTR_ALL],
                                    'eventsAll': list(EVENTS_ALL)}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': list(VACATIONS)}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': list(PPE)}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.addTraining':
        return {'ok': True, 'data': {'id': 100}}
    if action == 'workSchedule.setTrainingDone':
        rid = (body or {}).get('id')
        val = 1 if (body or {}).get('выполнение') == 1 else 0
        DONE_CALLS.append({'id': rid, 'выполнение': val})
        for r in INSTR_ALL:
            if r['id'] == rid:
                r['выполнение'] = val
                r['просрочен'] = 0 if val == 1 else (
                    1 if r['дата_начала'] < TODAY_ISO else 0)
                return {'ok': True, 'data': {'id': rid,
                        'выполнение': r['выполнение'],
                        'просрочен': r['просрочен']}}
        return {'ok': False, 'error': 'not_found'}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t418-%s');" % tag +
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
                      body='not found (t418-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def open_workers_card(page, fio='Федосов А. В.'):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('%s')" % fio)
    page.wait_for_timeout(900)


# состояние строки блока «Повторные инструктажи…» по части темы
ROW_STATE_JS = """(function(themePart){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var rows = cards[i].querySelectorAll('.ws-popup-row.ws-popup-event');
            for (var r = 0; r < rows.length; r++) {
                if (rows[r].innerText.indexOf(themePart) !== -1) {
                    var chk = rows[r].querySelector('.ws-done-chk');
                    var late = rows[r].querySelector('.ws-late-tag');
                    return {
                        found: true,
                        late: !!late,
                        lateText: late ? late.innerText : '',
                        chk: !!chk,
                        chkOn: !!(chk && chk.classList.contains('ws-done-on')),
                        chkRo: !!(chk && chk.classList.contains('ws-done-ro')),
                        chkTitle: chk ? (chk.getAttribute('title') || '') : '',
                        chkClickable: !!(chk && chk.getAttribute('onclick')),
                        rowDone: rows[r].classList.contains('ws-row-done'),
                        text: rows[r].innerText
                    };
                }
            }
            return {found: false};
        }
    }
    return {found: false, noBlock: true};
})"""


def row_state(page, theme_part):
    return page.evaluate('(' + ROW_STATE_JS + ')("%s")' % theme_part)


# клик по галочке строки с заданной темой
CLICK_CHK_JS = """(function(themePart){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var rows = cards[i].querySelectorAll('.ws-popup-row.ws-popup-event');
            for (var r = 0; r < rows.length; r++) {
                if (rows[r].innerText.indexOf(themePart) !== -1) {
                    var chk = rows[r].querySelector('.ws-done-chk');
                    if (chk) { chk.click(); return 'clicked'; }
                    return 'no-chk';
                }
            }
            return 'no-row';
        }
    }
    return 'no-block';
})"""


def click_chk(page, theme_part):
    return page.evaluate('(' + CLICK_CHK_JS + ')("%s")' % theme_part)


def events_block_no_chk(page):
    return page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Мероприятия') !== -1 &&
            h.textContent.indexOf('Повторные') === -1) {
            return {chks: cards[i].querySelectorAll('.ws-done-chk').length,
                    rows: cards[i].querySelectorAll('.ws-popup-row.ws-popup-event').length};
        }
    }
    return {chks: -1, rows: -1};
})()""")


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — галочки, «просрочен», setTrainingDone ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'main')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    open_workers_card(page)
    page.screenshot(path='task418-proof-card-initial.png', full_page=False)

    # --- строки блока: состояние отметки и просрочки ---
    r1 = row_state(page, N_OT)
    check('B1: ЗАЯВКА — прошлая без отметки: галочка ПУСТАЯ',
          r1.get('found') and r1.get('chk') and not r1.get('chkOn'), r1)
    check('B2: ЗАЯВКА — бейдж «просрочен» на строке',
          r1.get('late') and
          r1.get('lateText', '').strip().lower() == 'просрочен', r1)
    check('B3: подсказка «Отметить выполнение»',
          r1.get('chkTitle') == 'Отметить выполнение', r1.get('chkTitle'))
    r2 = row_state(page, N_EL)
    check('B4: будущая дата — бейджа «просрочен» НЕТ',
          r2.get('found') and not r2.get('late'), r2)
    check('B5: будущая дата — галочка пустая', r2.get('chk') and not r2.get('chkOn'), r2)
    r3 = row_state(page, N_PB)
    check('B6: выполненная запись — галочка ЗЕЛЁНАЯ (ws-done-on)',
          r3.get('found') and r3.get('chkOn'), r3)
    check('B7: выполненная запись — строки приглушена (ws-row-done)',
          r3.get('rowDone'), r3)
    check('B8: выполненная запись — бейджа «просрочен» нет',
          not r3.get('late'), r3)
    check('B9: подсказка выполненной — «Снять отметку…»',
          r3.get('chkTitle') == 'Снять отметку о выполнении', r3.get('chkTitle'))

    # --- блок «Мероприятия» — без галочек ---
    ev = events_block_no_chk(page)
    check('C1: блок «Мероприятия» — записей с галочками НЕТ',
          ev['rows'] >= 1 and ev['chks'] == 0, ev)

    # --- клик по галочке: отметка о выполнении ---
    n_calls = len(DONE_CALLS)
    click_chk(page, N_OT)
    page.wait_for_timeout(900)
    check('D1: ЗАЯВКА — API setTrainingDone вызван (0→1)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 601, 'выполнение': 1},
          DONE_CALLS[n_calls:])
    r1b = row_state(page, N_OT)
    check('D2: галочка стала зелёной', r1b.get('chkOn'), r1b)
    check('D3: бейдж «просрочен» исчез', not r1b.get('late'), r1b)
    check('D4: строка приглушена (ws-row-done)', r1b.get('rowDone'), r1b)
    check('D5: тост «Отмечено выполнение»',
          'Отмечено выполнение' in page.evaluate('document.body.innerText'))
    page.screenshot(path='task418-proof-marked-done.png', full_page=False)

    # --- клик по зелёной галочке: снятие отметки ---
    click_chk(page, N_PB)
    page.wait_for_timeout(900)
    check('E1: снятие — API (1→0)',
          DONE_CALLS[-1] == {'id': 603, 'выполнение': 0}, DONE_CALLS[-2:])
    r3b = row_state(page, N_PB)
    check('E2: галочка пустая', not r3b.get('chkOn'), r3b)
    check('E3: просроченность ВЕРНУЛАСЬ (дата прошла)',
          r3b.get('late') and
          r3b.get('lateText', '').strip().lower() == 'просрочен', r3b)
    check('E4: строка не приглушена', not r3b.get('rowDone'), r3b)

    # --- правка ✎ жива (регресс 417; ✎ в блоке ИНСТРУКТАЖЕЙ —
    # блок «Мероприятия» стоит раньше в DOM и перехватил бы клик) ---
    click_edit = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var a = cards[i].querySelector('.ws-popup-act[title="Редактировать"]');
            if (a) { a.click(); return 'clicked'; }
            return 'no-act';
        }
    }
    return 'no-block';
})()""")
    page.wait_for_timeout(900)
    form = page.evaluate("""(function(){
    var sh = document.getElementById('wsTrSheet');
    return {open: sh ? sh.classList.contains('active') : false,
            title: (document.getElementById('wsTrSheetTitle') || {}).textContent || ''};
})()""")
    check('F1: регресс — правка записи открывает форму',
          click_edit == 'clicked' and form['open'] and
          form['title'] == 'Правка инструктажа / проверки знаний',
          (click_edit, form))
    page.evaluate("WorkSchedule.closeTrainingForm && WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # --- кэш-путь: перезагрузка — состояние отметок из данных ---
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Федосов А. В.')")
    page.wait_for_timeout(900)
    r1c = row_state(page, N_OT)
    check('G1: кэш-путь — отметка 601 сохранена (зелёная)',
          r1c.get('chkOn') and not r1c.get('late'), r1c)
    r3c = row_state(page, N_PB)
    check('G2: кэш-путь — снятая отметка 603: пустая + «просрочен»',
          not r3c.get('chkOn') and r3c.get('late') and
          r3c.get('lateText', '').strip().lower() == 'просрочен', r3c)
    check('G3: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    open_workers_card(page)
    rv1 = row_state(page, N_OT)
    check('H1: view — выполненная запись: галочка-состояние НЕкликабельна',
          rv1.get('chkOn') and rv1.get('chkRo') and not rv1.get('chkClickable'), rv1)
    check('H2: view — подсказка «Выполнено»',
          rv1.get('chkTitle') == 'Выполнено', rv1.get('chkTitle'))
    rv3 = row_state(page, N_PB)
    check('H3: view — снятая отметка + прошедшая дата: бейдж «просрочен» виден',
          rv3.get('late') and not rv3.get('chkClickable'), rv3)
    rv2 = row_state(page, N_EL)
    check('H4: view — будущая запись БЕЗ галочки (не выполнена)',
          not rv2.get('chk') and not rv2.get('chkOn'), rv2)
    # тап по некликабельной галочке не вызывает API
    n2 = len(DONE_CALLS)
    click_chk(page, N_OT)
    page.wait_for_timeout(600)
    check('H5: view — клики по галочке API НЕ вызывают',
          len(DONE_CALLS) == n2, DONE_CALLS[n2:])
    page.screenshot(path='task418-proof-view-light.png', full_page=False)
    check('H6: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, тёмная, edit ==========
    print('=== Контекст 3: мобайл 375 тёмная edit ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    open_workers_card(page)
    rm = row_state(page, N_PB)
    check('I1: мобайл — строка с «просрочен» и пустой галочкой',
          rm.get('late') and rm.get('chk') and not rm.get('chkOn'), rm)
    size = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var chk = cards[i].querySelector('.ws-done-chk');
            if (!chk) return {w: 0, h: 0};
            var r = chk.getBoundingClientRect();
            return {w: Math.round(r.width), h: Math.round(r.height)};
        }
    }
    return {w: -1, h: -1};
})()""")
    check('I2: мобайл — галочка достаточного размера (>=22px)',
          size['w'] >= 22 and size['h'] >= 22, size)
    nm = len(DONE_CALLS)
    click_chk(page, N_PB)
    page.wait_for_timeout(2500)
    check('I3: мобайл — тап по галочке вызывает API',
          len(DONE_CALLS) == nm + 1 and DONE_CALLS[-1]['id'] == 603, DONE_CALLS[nm:])
    diag = page.evaluate("""(function(){
    return {toast: document.body.innerText.slice(-300),
            workersActive: (function(){var pg = document.getElementById('page-ws-workers');
                return pg ? pg.classList.contains('active') : null;})(),
            pools: (function(){var o=[];(WorkSchedule._TRAININGS||[]).forEach(function(r){
                    o.push({p:'T', id:r.id, d:r.выполнение, l:r.просрочен});});
                (WorkSchedule._INSTR_ALL||[]).forEach(function(r){
                    o.push({p:'A', id:r.id, d:r.выполнение, l:r.просрочен});});
                return o;})()};
})()""")
    print('    [diag]', diag)
    rm2 = row_state(page, N_PB)
    check('I4: мобайл — галочка стала зелёной, бейдж ушёл',
          rm2.get('chkOn') and not rm2.get('late'), rm2)
    page.screenshot(path='task418-proof-mobile-toggle.png', full_page=False)
    check('I5: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
