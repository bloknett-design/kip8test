#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 424: browser-check — заявка «проработать блок Мероприятия:
# в мероприятиях должны выбираться из списка обучение/прогул/
# примечание, и также вся информация должна архивироваться в архиве;
# создать листы в файле табель_КИП_ИОС и проверить функционал
# данного блока приложения на соответствие».
# Сервер: eventsInit (листы «Инструктажи»+«Мероприятия») — GAS-VM
# покрыт юнит-тестами test-task424.js; здесь — КЛИЕНТ блока.
# ПРОВЕРКИ (мок-сервер, порт 8926; eventsAll — записи 2024/2025/Y):
#   1) десктоп 1280 тёмная, edit:
#      • блок «Мероприятия · Y» + навигатор лет ‹ › (архив);
#      • записи года в блоке, инструктажи — в СВОЁМ блоке;
#      • «+ Мероприятие…» → форма: select «Тип» РОВНО
#        обучение/прогул/примечание (СООТВЕТСТВИЕ ЗАЯВКЕ),
#        работник предзаполнен;
#      • добавление ВСЕХ ТРЁХ типов → API addTraining с верным
#        типом, тост, запись в блоке;
#      • АРХИВ: ‹ → Y-1 (записи 2025), ‹‹ → Y-2 (2024, минимум,
#        стрелка погашена), ›› возврат;
#      • правка архивной записи 2024: форма «Правка мероприятия»,
#        тип записи в select;
#      • бейдж ОБ в ячейке сегодня + окно «Мероприятия · месяц»;
#      • сводная «Общая»: колонка «Мероприятия · Y» с числом;
#   2) десктоп 1280 светлая, view: записи видны, кнопок НЕТ;
#   3) мобайл 375 тёмная, edit: форма открывается, select доступен.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8926
TODAY = datetime.date.today()
Y = TODAY.year
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)
FUTURE = '%04d-%02d-%02d' % (TODAY.year, TODAY.month,
                             min(TODAY.day + 10, 28))
PAST_OT = '%04d-%02d-%02d' % (TODAY.year, TODAY.month,
                              max(TODAY.day - 20, 1))


def ru(iso):
    p = str(iso).split('-')
    return p[2] + '.' + p[1] + '.' + p[0]


U_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
T_OB = 'Охрана труда (ежегодный курс)'
T_ASU = 'Курс АСУ ТП (базовый)'
T_PRG = 'Прогул без уважительной причины'
T_OTS = 'Отстранение от работы'
T_SPRAV = 'Справка медосмотра'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '0872', 'ФИО': 'Тестов Б. Б.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': '', 'старт_цикла': '',
   'дата_приёма': '2025-01-10', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': 'III', 'комментарий': ''},
]

INSTR_LIST = [
  {'название': U_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': 'Инстр. ОТ'},
]


def ev(i, tab, tip, tema, d1, d2=None, days=1):
    return {'id': i, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d1, 'дата_окончания': d2 or d1,
            'длительность_дней': days, 'комментарий': ''}


# лист «Мероприятия»: записи ВСЕХ лет (архив) — 2024/2025/Y
def fresh_events():
    return [
        ev(500, '0871', 'обучение', T_ASU, '%04d-05-15' % (Y - 2)),
        ev(501, '0871', 'прогул', T_PRG, '%04d-06-10' % (Y - 1)),
        ev(502, '0871', 'примечание', T_OTS, '%04d-08-20' % (Y - 1)),
        ev(503, '0871', 'обучение', T_OB, TODAY_ISO),
        ev(504, '0872', 'примечание', T_SPRAV, TODAY_ISO),
    ]


# лист «Инструктажи» (для разделения блоков)
def fresh_instr():
    return [{'id': 600, 'таб_номер': '0871', 'тип': 'инструктаж',
             'тема': U_OT, 'дата_начала': PAST_OT,
             'дата_окончания': PAST_OT, 'длительность_дней': 1,
             'комментарий': '', 'дата_проведения': PAST_OT,
             'выполнение': 0, 'просрочен': 1}]


EVENTS = fresh_events()
INSTR = fresh_instr()
ADD_CALLS = []
DEL_CALLS = []
NEXT_ID = [700]
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#A5D6A7', 'short': 'обучение'},
  {'code': 'ПР', 'name': 'Прогул', 'color': '#EF9A9A', 'short': 'прогул'},
  {'code': '*', 'name': 'Примечание', 'color': '#CE93D8', 'short': 'примечание'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#90CAF9', 'short': 'инстр.'},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
PASS = 0
FAIL = 0
ADMIN = True


def reset_data():
    global EVENTS, INSTR, ADD_CALLS, DEL_CALLS
    EVENTS = fresh_events()
    INSTR = fresh_instr()
    ADD_CALLS = []
    DEL_CALLS = []


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if ADMIN else 'КИП ИОС'}}
    if action == 'getMyAccess':
        if ADMIN:
            perms = {'calc.view': True, 'library.view': True,
                     'kipios.view': True, 'workschedule.view': True,
                     'workschedule.edit': True}
            role = 'Админ'
        else:
            perms = {'calc.view': True, 'library.view': True,
                     'kipios.view': True, 'workschedule.view': True,
                     'workschedule.edit': False,
                     'workschedule.view.min': False}
            role = 'КИП ИОС'
        return {'ok': True, 'data': {'role': role, 'found': True,
                'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        inc = bool(body and body.get('includeArchived'))
        emps = EMPLOYEES if inc else [e for e in EMPLOYEES
                                       if not e['в_архиве']]
        return {'ok': True, 'data': {'employees': emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        both = INSTR + EVENTS
        return {'ok': True, 'data': {
            'trainings': [dict(r) for r in both
                          if r['дата_начала'][:4] == str(Y)],
            'instrList': [dict(x) for x in INSTR_LIST],
            'instrAll': [dict(r) for r in INSTR],
            'eventsAll': [dict(r) for r in EVENTS]}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.addTraining':
        ADD_CALLS.append(dict(body or {}))
        tip = str((body or {}).get('тип') or '')
        rec = ev(NEXT_ID[0], str((body or {}).get('таб_номер') or ''),
                 tip, str((body or {}).get('тема') or ''),
                 str((body or {}).get('дата_начала') or TODAY_ISO),
                 str((body or {}).get('дата_окончания') or ''),
                 int((body or {}).get('длительность_данных') or 1))
        rec['длительность_дней'] = int(
            (body or {}).get('длительность_дней') or 1)
        if tip in ('обучение', 'прогул', 'примечание'):
            EVENTS.append(rec)      # маршрутизация: лист «Мероприятия»
        else:
            INSTR.append(rec)       # лист «Инструктажи»
        NEXT_ID[0] += 1
        return {'ok': True, 'data': {'id': rec['id']}}
    if action == 'workSchedule.deleteTraining':
        rid = (body or {}).get('id')
        DEL_CALLS.append(rid)
        for pool in (EVENTS, INSTR):
            for r in list(pool):
                if r['id'] == rid:
                    pool.remove(r)
        return {'ok': True, 'data': {'id': rid}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t424-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t424-%s)' % tag)
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


# HTML блока «Мероприятия» карточки (страница «Работники»)
EV_BLOCK_JS = """(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Мероприятия') !== -1) {
            return {head: h.textContent, html: cards[i].innerHTML,
                    btn: !!cards[i].querySelector('.ws-emp-addtr'),
                    acts: cards[i].querySelectorAll('.ws-popup-act').length};
        }
    }
    return null;
})"""


def ev_block(page):
    return page.evaluate('(' + EV_BLOCK_JS + ')()') or {}


def toast_text(page):
    return page.evaluate(
        "(function(){var m = document.getElementById('toastMessage');"
        " return m ? m.textContent : '';})()")


def form_state(page):
    return page.evaluate("""(function(){
    var sh = document.getElementById('wsTrSheet');
    var sel = document.getElementById('wsTrType');
    var grp = document.getElementById('wsTrTypeGroup');
    var opts = sel ? Array.prototype.map.call(sel.options,
        function(o){return o.value;}) : null;
    return {open: !!(sh && sh.classList.contains('active')),
            title: (document.getElementById('wsTrSheetTitle')||{}).textContent,
            isSelect: !!(sel && sel.tagName === 'SELECT'),
            options: opts,
            typeShown: !!(grp && grp.style.display !== 'none'),
            typeVal: sel ? sel.value : null,
            emp: (document.getElementById('wsTrEmp')||{}).textContent,
            tabNo: (document.getElementById('wsTrTabNo')||{}).value};
})()""")


def submit_event(page, tip, tema):
    page.select_option('#wsTrType', tip)
    page.fill('#wsTrTitle', tema)
    page.click('#wsTrSubmitBtn')
    page.wait_for_timeout(1800)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ===== Контекст 1: десктоп 1280, тёмная, edit =====
    print('=== Контекст 1: десктоп тёмная edit — блок «Мероприятия» ===')
    ADMIN = True
    reset_data()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'main')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') &&"
                        " document.title === 'КИПиА'"))

    open_workers_card(page)
    blk = ev_block(page)
    page.screenshot(path='task424-proof-card-initial.png', full_page=False)
    check('B1: блок «Мероприятия · %d» + навигатор ‹ › (архив)' % Y,
          ('Мероприятия · %d' % Y) in blk.get('head', '') and
          'ws-ynav' in blk.get('html', ''), blk.get('head', ''))
    check('B2: запись года в блоке: «%s» %s' % (T_OB, ru(TODAY_ISO)),
          T_OB in blk.get('html', '') and
          ru(TODAY_ISO) in blk.get('html', ''))
    check('B3: инструктажи — в СВОЁМ блоке (темы И нет в мероприятиях)',
          U_OT not in blk.get('html', ''))
    check('B4: кнопка «+ Мероприятие…» и действия строк (✎/✕)',
          blk.get('btn') and blk.get('acts', 0) >= 2, blk)

    # --- форма «Новое мероприятие»: СООТВЕТСТВИЕ ЗАЯВКЕ ---
    page.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page.wait_for_timeout(700)
    fs = form_state(page)
    page.screenshot(path='task424-proof-form.png', full_page=False)
    check('C1: форма открылась, заголовок «Новое мероприятие»',
          fs['open'] and fs['title'] == 'Новое мероприятие', fs)
    check('C2: ГЛАВНОЕ — тип ВЫБИРАЕТСЯ ИЗ СПИСКА: ровно '
          '[обучение, прогул, примечание]',
          fs['isSelect'] and fs['options'] == ['обучение', 'прогул',
                                               'примечание'], fs['options'])
    check('C3: поле «Тип» видимо, дефолт «обучение»',
          fs['typeShown'] and fs['typeVal'] == 'обучение', fs['typeVal'])
    check('C4: работник предзаполнен из карточки',
          fs['emp'] == 'Федосов А. В. · таб. №0871' and
          fs['tabNo'] == '0871', fs['emp'])

    # --- добавление всех ТРЁХ типов (маршрутизация по типу) ---
    submit_event(page, 'прогул', 'Прогул (тест добавления)')
    check('D1: API addTraining — тип=прогул, таб 0871',
          ADD_CALLS and ADD_CALLS[-1]['тип'] == 'прогул' and
          ADD_CALLS[-1]['таб_номер'] == '0871', ADD_CALLS[-1:])
    t1 = toast_text(page)
    check('D2: тост «Мероприятие добавлено»', 'добавлено' in t1.lower(), t1)
    page.evaluate("WorkSchedule.selectWorkersTab('0871')")
    page.wait_for_timeout(900)
    blk = ev_block(page)
    check('D3: запись «Прогул (тест добавления)» в блоке',
          'Прогул (тест добавления)' in blk.get('html', ''))

    page.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page.wait_for_timeout(600)
    submit_event(page, 'примечание', 'Примечание (тест добавления)')
    check('D4: тип=примечание ушёл верно',
          ADD_CALLS and ADD_CALLS[-1]['тип'] == 'примечание',
          ADD_CALLS[-1:])
    page.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page.wait_for_timeout(600)
    submit_event(page, 'обучение', 'Стажировка на стенде')
    check('D5: тип=обучение ушёл верно',
          ADD_CALLS and ADD_CALLS[-1]['тип'] == 'обучение',
          ADD_CALLS[-1:])

    # --- АРХИВ: стрелки лет ---
    page.evaluate("WorkSchedule.selectWorkersTab('0871')")
    page.wait_for_timeout(900)
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Предыдущий год']")
    page.wait_for_timeout(900)
    blk = ev_block(page)
    check('E1: ‹ → «Мероприятия · %d», записи 2025 в блоке' % (Y - 1),
          ('Мероприятия · %d' % (Y - 1)) in blk.get('head', '') and
          T_PRG in blk.get('html', '') and T_OTS in blk.get('html', ''),
          blk.get('head', ''))
    page.screenshot(path='task424-proof-archive-%d.png' % (Y - 1),
                    full_page=False)
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Предыдущий год']")
    page.wait_for_timeout(900)
    blk = ev_block(page)
    check('E2: ‹‹ → «Мероприятия · %d» (минимум), запись 2024' % (Y - 2),
          ('Мероприятия · %d' % (Y - 2)) in blk.get('head', '') and
          T_ASU in blk.get('html', ''), blk.get('head', ''))
    check('E3: на минимуме стрелка ‹ ПОГАШЕНА (ws-ynav-off)',
          'ws-ynav-off' in blk.get('html', ''))

    # --- правка архивной записи 2024 (регресс 417) ---
    page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Мероприятия') !== -1) {
            var rows = cards[i].querySelectorAll('.ws-popup-row');
            for (var r = 0; r < rows.length; r++) {
                if (rows[r].innerText.indexOf('%s') !== -1) {
                    var e = rows[r].querySelector('.ws-popup-act');
                    if (e) { e.click(); return 'clicked'; }
                }
            }
        }
    }
    return 'no-row';
})()""" % T_ASU)
    page.wait_for_timeout(700)
    fs = form_state(page)
    check('F1: правка архива — «Правка мероприятия», тип записи в select',
          fs['open'] and fs['title'] == 'Правка мероприятия' and
          fs['typeVal'] == 'обучение', fs)
    check('F2: тема записи в поле',
          page.evaluate(
              "document.getElementById('wsTrTitle').value") == T_ASU)
    page.click("#wsTrSheet button.flow-input-cancel")
    page.wait_for_timeout(500)

    # возврат в текущий год
    page.evaluate("WorkSchedule.selectWorkersTab('0871')")
    page.wait_for_timeout(900)
    for _ in range(2):
        page.click(".ws-wgrid2 .ws-wcard "
                   ".ws-ynav-btn[title='Следующий год']")
        page.wait_for_timeout(600)
    blk = ev_block(page)
    check('F3: ›› → возврат «Мероприятия · %d»' % Y,
          ('Мероприятия · %d' % Y) in blk.get('head', ''),
          blk.get('head', ''))

    # --- сетка: бейдж ОБ сегодня + окно месяца ---
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    badge = page.evaluate("""(function(){
    var badges = document.querySelectorAll('#wsGridWrap .ws-ev-badge');
    for (var i = 0; i < badges.length; i++) {
        if (badges[i].textContent === 'ОБ') {
            return {found: true,
                    title: badges[i].getAttribute('title') || ''};
        }
    }
    return {found: false};
})()""")
    check('G1: бейдж «ОБ» в ячейке сегодня, тултип с темой',
          badge['found'] and T_OB in badge['title'], badge)
    panel = page.evaluate(
        "(function(){var el = document.getElementById('wsEventsPanel');"
        " return el ? el.innerText : '';})()")
    check('G2: окно «Мероприятия · месяц» содержит тему',
          T_OB in panel, panel[:200])

    # --- сводная «Общая»: колонка «Мероприятия · Y» ---
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.evaluate("WorkSchedule.selectWorkersTab('general')")
    page.wait_for_timeout(900)
    gen = page.evaluate("""(function(){
    var t = document.querySelector('.ws-wgen-table');
    if (!t) return {head: '', row: ''};
    var head = t.rows[0].innerText;
    var row = '';
    for (var i = 1; i < t.rows.length; i++) {
        if (t.rows[i].innerText.indexOf('Федосов') !== -1)
            row = t.rows[i].innerText;
    }
    return {head: head, row: row};
})()""")
    n_year = len([r for r in EVENTS
                  if r['таб_номер'] == '0871' and
                  r['дата_начала'][:4] == str(Y)])
    check('H1: сводная — колонка «Мероприятия · %d»' % Y,
          ('Мероприятия · %d' % Y).upper() in
          gen.get('head', '').upper(), gen.get('head', ''))
    check('H2: строка Федосова несёт число мероприятий года (%d)' % n_year,
          str(n_year) in gen.get('row', ''), gen.get('row', ''))
    check('H3: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ===== Контекст 2: десктоп 1280, светлая, view =====
    print('=== Контекст 2: десктоп светлая view — только чтение ===')
    ADMIN = False
    reset_data()
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'view')
    page2.goto('http://127.0.0.1:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    check('I0: приложение загрузилось (view)',
          page2.evaluate("document.title === 'КИПиА'"))
    open_workers_card(page2)
    blk = ev_block(page2)
    page2.screenshot(path='task424-proof-view-light.png', full_page=False)
    check('I1: записи года видны зрителю',
          T_OB in blk.get('html', ''), blk.get('head', ''))
    check('I2: кнопки «+ Мероприятие…» НЕТ',
          not blk.get('btn'), blk)
    check('I3: действий ✎/✕ НЕТ', blk.get('acts', 99) == 0, blk)
    check('I4: JS-ошибок нет', not js_errors2, js_errors2[:3])
    ctx2.close()

    # ===== Контекст 3: мобайл 375, тёмная, edit =====
    print('=== Контекст 3: мобайл 375 тёмная edit ===')
    ADMIN = True
    reset_data()
    ctx3 = browser.new_context(viewport={'width': 375, 'height': 812})
    page3 = ctx3.new_page()
    js_errors3 = attach(page3, ctx3, 'dark', 'mob')
    page3.goto('http://127.0.0.1:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(2200)
    page3.click('#wsWorkersBtn')
    page3.wait_for_timeout(1500)
    page3.click(".ws-wtabs button:has-text('Федосов')")
    page3.wait_for_timeout(900)
    blk = ev_block(page3)
    check('J1: мобайл — блок «Мероприятия · %d» с записью' % Y,
          ('Мероприятия · %d' % Y) in blk.get('head', '') and
          T_OB in blk.get('html', ''), blk.get('head', ''))
    check('J2: кнопка «+ Мероприятие…» доступна', blk.get('btn'), blk)
    page3.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page3.wait_for_timeout(700)
    fs = form_state(page3)
    page3.screenshot(path='task424-proof-mobile.png', full_page=False)
    check('J3: форма на мобайле — select с тремя типами',
          fs['open'] and fs['options'] == ['обучение', 'прогул',
                                           'примечание'], fs['options'])
    w = page3.evaluate("""(function(){
    var sel = document.getElementById('wsTrType');
    var r = sel.getBoundingClientRect();
    return {w: Math.round(r.width), h: Math.round(r.height)};
})()""")
    check('J4: тап-зона select достаточна (>=40px высоты)',
          w['h'] >= 40, w)
    page3.click("#wsTrSheet button.flow-input-cancel")
    page3.wait_for_timeout(400)
    check('J5: JS-ошибок нет', not js_errors3, js_errors3[:3])
    ctx3.close()

    browser.close()

print('\n===== ИТОГ: %d passed, %d failed =====' % (PASS, FAIL))
if FAIL:
    raise SystemExit(1)
