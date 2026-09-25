#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 415: browser-check — заявка «В карте работника, в блоках,
# записи которые не помещяются в одну строчку должны переноситься
# на следующую строчку».
# ПРОВЕРКИ (мок-сервер, порт 8916):
#   1) десктоп 1280 тёмная, edit: карточка Иванова — записи
#      инструктажей/мероприятий с ДЛИННЫМИ темами ПЕРЕНОСЯТСЯ на
#      2+ строки (Range-rects по тексту), white-space: normal,
#      text-overflow: clip (не «…»), строка не вылезает за блок;
#      заголовок блока инструктажей тоже переносится; ФИО — normal;
#      СИЗ/отпуска — прежний перенос не сломан; ПОПАП карточки
#      (#wsEmpPopup) — секции и записи переносятся; ПОПАП ДНЯ
#      (#wsCellPopup) — регресс: прежний однострочный ellipsis;
#      перезагрузка — кэш-путь;
#   2) десктоп 1280 светлая, view: перенос записей, без ✎/✕;
#   3) мобайл 375 светлая, edit: перенос в узкой колонке.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8916
TODAY = datetime.date.today()
Y = TODAY.year

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

def ru(iso):
    p = iso.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]

# канон Task 412 — длинные названия пунктов (главный кейс заявки)
N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
# длинные данные остальных блоков карты
N_EV = ('Повышение квалификации по автоматизированным системам управления '
        'технологическими процессами и метрологическому обеспечению')
N_PPE = ('Костюм из изолирующего материала для защиты от растворов кислот '
         'и щелочей концентрации до 20 процентов')
N_VAC_C = ('согласовано с начальником участка ремонта и наладки средств '
           'КИПиА, отгулы за переработку февраля')
# запись «вне списка» (не по шаблону) — длинная тема: в попапе
# карточки она — строка .ws-popup-event с ПОЛНОЙ темой
N_OFF = ('Целевой инструктаж при допуске к работам повышенной '
         'опасности по наряду-допуску в электроустановках цеха')

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
  {'id': 101, 'таб_номер': '017', 'тип': 'проверка_знаний', 'тема': N_EL,
   'дата_начала': d(Y, 3, 20), 'дата_окончания': d(Y, 3, 20),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 102, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': N_OT,
   'дата_начала': d(Y, 1, 15), 'дата_окончания': d(Y, 1, 15),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 105, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': N_OFF,
   'дата_начала': d(Y, 4, 7), 'дата_окончания': d(Y, 4, 7),
   'длительность_дней': 1, 'комментарий': ''},
]
# событие — в ТЕКУЩЕМ месяце (для попапа дня), длинная тема
EVENTS_ALL = [
  {'id': 201, 'таб_номер': '017', 'тип': 'обучение', 'тема': N_EV,
   'дата_начала': d(Y, TODAY.month, 12), 'дата_окончания': d(Y, TODAY.month, 12),
   'длительность_дней': 1, 'комментарий': ''},
]
VACATIONS = [
  {'id': 301, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(Y, 5, 11), 'дата_окончания': d(Y, 5, 24),
   'комментарий': N_VAC_C},
]
PPE = [
  {'id': 401, 'таб_номер': '017', 'наименование': N_PPE,
   'дата_выдачи': d(Y, 2, 3), 'срок_годности': '12 мес.',
   'дата_окончания': d(Y + 1, 2, 3), 'примечание': ''},
]
# trainings — ОБЪЕДИНЁННЫЙ годовой срез (Инструктажи + Мероприятия,
# WorkSchedule.gs Task 405) — питает окно «Мероприятия в этот день»
TRAININGS = [dict(EVENTS_ALL[0])]
INSTR_LIST = []
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

API_CALLS = []
PASS = 0
FAIL = 0
ADMIN = False


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
        return {'ok': True, 'data': {'trainings': list(TRAININGS),
                                    'instrList': list(INSTR_LIST),
                                    'instrAll': list(INSTR_ALL),
                                    'eventsAll': list(EVENTS_ALL)}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': list(VACATIONS)}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': list(PPE)}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t415-%s');" % tag +
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
                      body='not found (t415-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# --- JS-хелперы: перенос = Range-rects >= 2 строк текста ---
# (flex-children блокифицируются, элементные rects не годятся —
#  считаем СТРОКИ текста через Range по содержимому)
WRAP_JS = """(function(a){
    var rootArg = a[0], sel = a[1], substr = a[2];
    var root = null;
    if (rootArg.charAt(0) === '#' || rootArg.charAt(0) === '.') {
        root = document.querySelector(rootArg);
    } else {
        // маркер-текст заголовка блока — ищем окно .ws-wcard карточки
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var c = 0; c < cards.length; c++) {
            var h = cards[c].querySelector('.ws-whead-t');
            if (h && h.textContent.indexOf(rootArg) !== -1) { root = cards[c]; break; }
        }
    }
    if (!root) return {err: 'no root ' + rootArg};
    var els = root.querySelectorAll(sel);
    for (var i = 0; i < els.length; i++) {
        if (substr && els[i].textContent.indexOf(substr) === -1) continue;
        var el = els[i];
        var cs = getComputedStyle(el);
        var rng = document.createRange();
        rng.selectNodeContents(el);
        var lines = rng.getClientRects().length;
        var r = el.getBoundingClientRect();
        return {whiteSpace: cs.whiteSpace, textOverflow: cs.textOverflow,
                overflow: cs.overflow, lines: lines,
                h: Math.round(r.height), w: Math.round(r.width),
                text: el.textContent.slice(0, 60)};
    }
    return {err: 'not found: ' + sel + ' / ' + substr};
})"""

ROWFIT_JS = """(function(a){
    var marker = a[0], substr = a[1];
    var root = null;
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var c = 0; c < cards.length; c++) {
        var h = cards[c].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf(marker) !== -1) { root = cards[c]; break; }
    }
    if (!root) return {err: 'no root'};
    var rows = root.querySelectorAll('.ws-popup-event');
    for (var i = 0; i < rows.length; i++) {
        if (rows[i].textContent.indexOf(substr) === -1) continue;
        return {scroll: rows[i].scrollWidth, client: rows[i].clientWidth};
    }
    return {err: 'row not found'};
})"""

BLOCK_JS = """(function(substr){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf(substr) !== -1) return true;
    }
    return false;
})"""


def open_card(page, fio='Иванов И. И.'):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('%s')" % fio)
    page.wait_for_timeout(900)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — перенос записей в блоках ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'wrap-dark', keep_cache=True)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    open_card(page)
    check('A2: блок инструктажей в карточке найден',
          page.evaluate(BLOCK_JS, 'Повторные инструктажи'))

    w = page.evaluate(WRAP_JS, ['Повторные инструктажи',
                                '.ws-popup-event .ws-popup-name', N_EL])
    check('B1: ЗАЯВКА 415 — длинная тема записи переносится (2+ строки)',
          w.get('lines', 0) >= 2, w)
    check('B2: white-space: normal, text-overflow: clip (НЕ «…»)',
          w.get('whiteSpace') == 'normal' and w.get('textOverflow') == 'clip', w)
    fit = page.evaluate(ROWFIT_JS, ['Повторные инструктажи', N_EL])
    check('B3: строка не вылезает за блок по ширине',
          fit.get('scroll', 99999) <= fit.get('client', 0) + 1, fit)

    # мероприятия — длинная тема тоже переносится
    we = page.evaluate(WRAP_JS, ['Мероприятия',
                                '.ws-popup-event .ws-popup-name', N_EV])
    check('B4: мероприятия — длинная тема переносится', we.get('lines', 0) >= 2, we)

    # СИЗ и отпуска — прежний перенос не сломан
    wp = page.evaluate(WRAP_JS, ['СИЗ', '.ws-ppe-name', N_PPE])
    check('B5: СИЗ — наименование переносится (регресс 392)',
          wp.get('lines', 0) >= 2, wp)
    wv = page.evaluate(WRAP_JS, ['Отпуска', '.ws-emp-v', N_VAC_C])
    check('B6: отпуск — длинный комментарий переносится',
          wv.get('lines', 0) >= 2, wv)

    # заголовок блока инструктажей — перенос (теперь по умолчанию)
    wh = page.evaluate(WRAP_JS, ['.ws-wgrid2', '.ws-whead-t', 'Повторные инструктажи'])
    check('B7: заголовок блока инструктажей переносится',
          wh.get('lines', 0) >= 2 and wh.get('whiteSpace') == 'normal', wh)
    wn = page.evaluate(WRAP_JS, ['.ws-wgrid2', '.ws-whead-name', 'Иванов'])
    check('B8: ФИО · таб. № — white-space: normal',
          wn.get('whiteSpace') == 'normal', wn)
    page.screenshot(path='task415-proof-card-dark-wrap.png', full_page=False)

    # ---- ПОПАП карточки (#wsEmpPopup): секции + записи ----
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('.ws-grid tbody tr:first-child td.ws-emp-col')
    page.wait_for_timeout(900)
    c1 = page.evaluate(WRAP_JS, ['#wsEmpPopup', '.ws-popup-sec',
                                 'Повторные инструктажи'])
    check('C1: попап карточки — заголовок секции переносится (380px)',
          c1.get('lines', 0) >= 2 and c1.get('whiteSpace') == 'normal', c1)
    c2 = page.evaluate(WRAP_JS, ['#wsEmpPopup', '.ws-popup-event .ws-popup-name', N_OFF])
    check('C2: попап карточки — запись «вне списка» переносится, не «…»',
          c2.get('whiteSpace') == 'normal' and c2.get('textOverflow') == 'clip' and
          c2.get('lines', 0) >= 2, c2)
    c2b = page.evaluate(WRAP_JS, ['#wsEmpPopup', '.ws-il-name', N_EL])
    check('C2b: попап карточки — группа шаблона с длинным названием (регресс 407)',
          c2b.get('whiteSpace') == 'normal' and c2b.get('lines', 0) >= 2, c2b)
    c3 = page.evaluate(WRAP_JS, ['#wsEmpPopup', '.ws-popup-title', 'Иванов'])
    check('C3: попап карточки — ФИО переносится (normal)',
          c3.get('whiteSpace') == 'normal', c3)
    page.screenshot(path='task415-proof-popup-headers.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmpPopup()")
    page.wait_for_timeout(300)

    # ---- ПОПАП ДНЯ (#wsCellPopup): регресс — компактный ellipsis ----
    ev_date = d(Y, TODAY.month, 12)
    cell_date = page.evaluate("""(function(){
    var wrap = document.getElementById('wsGridWrap');
    var rows = wrap.querySelectorAll('tbody tr');
    for (var i = 0; i < rows.length; i++) {
        var emp = rows[i].querySelector('td.ws-emp-col[data-tab=\\'017\\']');
        if (!emp) continue;
        var cells = rows[i].querySelectorAll('td.ws-cell');
        for (var j = 0; j < cells.length; j++) {
            var oc = cells[j].getAttribute('onclick') || '';
            var m = oc.match(/onCellClick\\(event, '([0-9-]+)'/);
            if (m && m[1] === '%s') { cells[j].click(); return m[1]; }
        }
    }
    return null;
})()""" % ev_date)
    check('D1: ячейка дня события кликнута (%s)' % cell_date,
          cell_date == ev_date, cell_date)
    page.wait_for_timeout(700)
    dp = page.evaluate(WRAP_JS, ['#wsEventsPopup', '.ws-popup-name', N_EV])
    check('D2: регресс — окно «Мероприятия в этот день»: прежний однострочный ellipsis',
          dp.get('whiteSpace') == 'nowrap' and dp.get('textOverflow') == 'ellipsis',
          dp)
    page.evaluate("WorkSchedule.closeCellPopup && WorkSchedule.closeCellPopup()")
    page.wait_for_timeout(300)

    # ---- перезагрузка: кэш-путь ----
    page.reload()
    page.wait_for_timeout(2500)
    open_card(page)
    w2 = page.evaluate(WRAP_JS, ['Повторные инструктажи',
                                 '.ws-popup-event .ws-popup-name', N_EL])
    check('E1: после перезагрузки (кэш) — перенос сохранён',
          w2.get('lines', 0) >= 2, w2)
    check('E2: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view — перенос записей ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'wrap-view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_card(page)
    w = page.evaluate(WRAP_JS, ['Повторные инструктажи',
                                '.ws-popup-event .ws-popup-name', N_EL])
    check('F1: светлая тема — длинная тема переносится',
          w.get('lines', 0) >= 2 and w.get('textOverflow') == 'clip', w)
    check('F2: ✎/✕ НЕТ (не редактор)',
          page.evaluate("""(function(){
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var i = 0; i < cards.length; i++) {
            var h = cards[i].querySelector('.ws-whead-t');
            if (h && h.textContent.indexOf('Повторные инструктажи') !== -1)
                return cards[i].innerHTML.indexOf('editTraining(') === -1;
        }
        return false;
    })()"""))
    page.screenshot(path='task415-proof-card-light-view.png', full_page=False)
    check('F3: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, edit ==========
    print('=== Контекст 3: мобайл 375 светлая edit ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'wrap-mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_card(page)
    w = page.evaluate(WRAP_JS, ['Повторные инструктажи',
                                '.ws-popup-event .ws-popup-name', N_EL])
    check('G1: мобайл — перенос в узкой колонке (2+ строки)',
          w.get('lines', 0) >= 2 and w.get('textOverflow') == 'clip', w)
    page.screenshot(path='task415-proof-card-mobile.png', full_page=False)
    check('G2: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
