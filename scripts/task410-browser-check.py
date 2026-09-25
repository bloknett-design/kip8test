#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 410: browser-check — заявка «в форме добавления инструктажа
# или проверки знаний (карточка работника, блок инструктажей и
# проверки знаний) старые выпадающие списки, в т.ч. обучение/прогул/
# примечание; нужно — выбор одного из инструктажей или проверок
# знаний из таблицы Список_И_и_ПЗ».
# ПРОВЕРКИ:
#   1) десктоп 1280 тёмная, edit: попап ячейки «+ Мероприятие…» —
#      форма мероприятия (тип обучение/прогул/примечание, дата
#      ячейки); карточка: «+ Инструктаж…» — заголовок «Новый
#      инструктаж / проверка знаний», БЕЗ поля «Тип», select ВСЕХ
#      5 пунктов эталона с группами «Инструктажи»/«Проверка знаний»,
#      подсказки, submit → тип из «вида» пункта, тосты
#      «Запись добавлена»; «+ Мероприятие…» — прежняя форма;
#      правка «вне списка» (instr-режим, тип записи сохраняется)
#      и правка мероприятия;
#   2) десктоп 1280 светлая, view: регресс блока инструктажей
#      (5 групп эталона), у зрителя НЕТ кнопок добавления;
#   3) мобайл 375 светлая, edit: «+ Инструктаж…» — форма instr
#      (тип скрыт, select 5 пунктов, submit) + element-скрин.
# Порт 8911 (запуск одним вызовом: сервер + проверка).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8911
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_OG = 'Повторный инструктаж по инструкции № 9-ОГЭ'
N_SAM = 'Периодическая проверка знаний на допуск к самостоятельной работе'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_VY = 'Периодическая проверка знаний по охране труда при выполнении работ на высоте'

OT_DATE = d(Y, M, max(1, TODAY.day - 10))
OG_DATE = d(Y, M, max(1, TODAY.day - 25))

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '', 'комментарий': ''},
]
TRAININGS = [
  {'id': 1, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': N_OT, 'дата_начала': OT_DATE, 'дата_окончания': OT_DATE},
  {'id': 2, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': N_OG, 'дата_начала': OG_DATE, 'дата_окончания': OG_DATE},
  {'id': 3, 'таб_номер': '017', 'тип': 'проверка_знаний',
   'тема': 'Внеплановый по наряду №4', 'дата_начала': d(Y, M, 12),
   'дата_окончания': d(Y, M, 12)},
  {'id': 4, 'таб_номер': '017', 'тип': 'примечание',
   'тема': 'Перенос по приказу', 'дата_начала': d(Y, M, 22),
   'дата_окончания': d(Y, M, 22)},
]
INSTR_LIST = [
  {'название': N_OT, 'вид': 'инструктаж', 'периодичность': 6, 'основание': ''},
  {'название': N_OG, 'вид': 'инструктаж', 'периодичность': 3, 'основание': ''},
  {'название': N_SAM, 'вид': 'проверка_знаний', 'периодичность': 12, 'основание': ''},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12, 'основание': ''},
  {'название': N_VY, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': 'инструкция № 53-ОТ'},
]
INSTR_ALL = [
  {'id': 9, 'таб_номер': '017', 'тип': 'проверка_знаний',
   'тема': N_SAM, 'дата_начала': d(Y - 2, 3, 12), 'дата_окончания': d(Y - 2, 3, 12)},
]
EVENTS_ALL = [
  {'id': 30, 'таб_номер': '017', 'тип': 'обучение',
   'тема': 'Курс АСУ ТП', 'дата_начала': d(Y - 1, 5, 15), 'дата_окончания': d(Y - 1, 5, 15)},
]
ENTRIES = [
  {'дата': d(Y, M, 3), 'таб_номер': '017', 'статус': 'Д'},
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
  {'id': 2, 'name': 'Дневной 5/2', 'cycle': 7, 'description': '',
   'days': [{'day': 1, 'status': 'Д8'}, {'day': 2, 'status': 'Д8'},
            {'day': 3, 'status': 'Д8'}, {'day': 4, 'status': 'Д8'},
            {'day': 5, 'status': 'Д8'}, {'day': 6, 'status': ''},
            {'day': 7, 'status': ''}]},
]

API_CALLS = []
PASS = 0
FAIL = 0

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
        return {'ok': True, 'data': {'entries': list(ENTRIES)}}
    if action == 'workSchedule.addTraining':
        API_CALLS.append(('addTraining', dict(body or {})))
        return {'ok': True, 'data': {'id': 100}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}

ADMIN = False

def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())

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
                      body='not found (t410-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t410-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

FORM_STATE_JS = """(function(){
    var sel = document.getElementById('wsTrTitleSel');
    var inp = document.getElementById('wsTrTitle');
    var tg = document.getElementById('wsTrTypeGroup');
    var tb = document.getElementById('wsTrTabGroup');
    var lbl = document.getElementById('wsTrTitleLabel');
    var ty = document.getElementById('wsTrType');
    return {
      title: (document.getElementById('wsTrSheetTitle')||{}).textContent || '',
      selHidden: sel ? sel.hidden : null,
      inpHidden: inp ? inp.hidden : null,
      typeDisplay: tg ? tg.style.display : null,
      typeVisible: tg ? (tg.offsetParent !== null) : null,
      tabFlex: tb ? tb.style.flex : null,
      label: lbl ? lbl.textContent : null,
      typeOpts: ty ? Array.prototype.map.call(ty.options, function(o){return o.value;}) : null,
      typeVal: ty ? ty.value : null,
      opts: sel ? Array.prototype.map.call(sel.options, function(o){return o.value;}) : null,
      groups: sel ? Array.prototype.map.call(
          sel.querySelectorAll('optgroup'), function(g){return g.label;}) : null,
      optSel: sel ? Array.prototype.map.call(
          sel.querySelectorAll('optgroup option'), function(o){return o.value;}) : null
    };
})()"""

def hint_js():
    return ("(function(){var h=document.getElementById('wsTrItemHint');" +
            "return h && !h.hidden ? h.textContent : null;})()")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — формы instr/мероприятие/правка ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'form-dark')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)

    # ---- попап ячейки: «+ Мероприятие…» — событие, дата ячейки ----
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
            if (m) { cells[j].click(); return m[1]; }
        }
    }
    return null;
})()""")
    check('B1: ячейка дня кликнута (дата %s)' % cell_date, cell_date is not None)
    page.wait_for_timeout(600)
    ev_row = page.evaluate("""(function(){
    var pp = document.getElementById('wsCellPopup');
    if (!pp) return null;
    var rows = pp.querySelectorAll('.ws-popup-more');
    for (var i = 0; i < rows.length; i++) {
        if (rows[i].textContent.indexOf('+ Мероприятие…') !== -1) return true;
    }
    return false;
})()""")
    check('B2: попап ячейки — строка «+ Мероприятие…»', bool(ev_row))
    page.click("#wsCellPopup .ws-popup-more:has-text('+ Мероприятие…')")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('B3: заголовок «Новое мероприятие» (событие)',
          fs['title'] == 'Новое мероприятие', fs['title'])
    check('B4: тип — РОВНО обучение/прогул/примечание, дефолт «обучение»',
          fs['typeOpts'] == ['обучение', 'прогул', 'примечание'] and
          fs['typeVal'] == 'обучение', (fs['typeOpts'], fs['typeVal']))
    check('B5: поле «Тип» ВИДИМО (форма события)', fs['typeVisible'] is True)
    check('B6: дата начала = дата ячейки',
          page.evaluate("document.getElementById('wsTrStart').value") == cell_date,
          page.evaluate("document.getElementById('wsTrStart').value"))
    check('B7: свободный ввод темы (select скрыт)',
          fs['selHidden'] is True and fs['inpHidden'] is False)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # ---- карточка: «+ Инструктаж…» — instr-режим ----
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('C1: заголовок «Новый инструктаж / проверка знаний»',
          fs['title'] == 'Новый инструктаж / проверка знаний', fs['title'])
    check('C2: поле «Тип» СКРЫТО (старых списков нет)',
          fs['typeVisible'] is False and fs['typeDisplay'] == 'none',
          (fs['typeVisible'], fs['typeDisplay']))
    check('C3: «Таб. №» — во всю ширину', '1 1 100%' in (fs['tabFlex'] or ''), fs['tabFlex'])
    check('C4: ярлык «Инструктаж / проверка знаний»',
          fs['label'] == 'Инструктаж / проверка знаний', fs['label'])
    check('C5: select виден, свободный ввод скрыт',
          fs['selHidden'] is False and fs['inpHidden'] is True)
    check('C6: ВСЕ 5 пунктов эталона (+ пустой)',
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY], fs['opts'])
    check('C7: группы «Инструктажи» / «Проверка знаний»',
          fs['groups'] == ['Инструктажи', 'Проверка знаний'], fs['groups'])
    check('C8: в группе инструктажей — 2, в ПЗ — 3',
          fs['optSel'] == [N_OT, N_OG, N_SAM, N_EL, N_VY], fs['optSel'])
    # submit без выбора — валидация (API не зовётся)
    n_calls = len(API_CALLS)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(400)
    check('C9: пустой select → addTraining НЕ вызван',
          len(API_CALLS) == n_calls, len(API_CALLS) - n_calls)
    # выбор инструктажа → подсказка + submit → тип из вида пункта
    page.select_option('#wsTrTitleSel', N_OT)
    page.wait_for_timeout(400)
    h1 = page.evaluate(hint_js())
    check('C10: подсказка ОТ: «раз в 6 месяцев»', h1 == 'раз в 6 месяцев', h1)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(400)
    body_txt = page.evaluate("document.body.innerText")
    check('C11: тост «Запись добавлена»', 'Запись добавлена' in body_txt)
    page.wait_for_timeout(700)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('C12: submit ОТ → тип «инструктаж», тема из списка',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OT, sent[-1] if sent else None)
    # повторно: пункт ПЗ → подсказка с основанием + тип «проверка_знаний»
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    page.select_option('#wsTrTitleSel', N_VY)
    page.wait_for_timeout(400)
    h2 = page.evaluate(hint_js())
    check('C13: подсказка высоты: «раз в год · Основание: инструкция № 53-ОТ»',
          h2 == 'раз в год · Основание: инструкция № 53-ОТ', h2)
    page.screenshot(path='task410-proof-form-instr.png', full_page=False)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('C14: submit высоты → тип «проверка_знаний» (вид пункта)',
          bool(sent) and sent[-1].get('тип') == 'проверка_знаний' and
          sent[-1].get('тема') == N_VY, sent[-1] if sent else None)

    # ---- «+ Мероприятие…» — прежняя форма события ----
    page.click('.ws-wgrid2 .ws-emp-addtr')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('D1: заголовок «Новое мероприятие»', fs['title'] == 'Новое мероприятие', fs['title'])
    check('D2: тип — 3 опции события, дефолт «обучение»',
          fs['typeOpts'] == ['обучение', 'прогул', 'примечание'] and
          fs['typeVal'] == 'обучение', (fs['typeOpts'], fs['typeVal']))
    check('D3: ярлык «Тема», свободный ввод',
          fs['label'] == 'Тема' and fs['selHidden'] is True and fs['inpHidden'] is False)
    page.fill('#wsTrTitle', 'Курс по АСУ ТП (повтор)')
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(400)
    body_txt = page.evaluate("document.body.innerText")
    check('D4: тост «Мероприятие добавлено»', 'Мероприятие добавлено' in body_txt)
    page.wait_for_timeout(700)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('D5: submit → тип «обучение», свободная тема',
          bool(sent) and sent[-1].get('тип') == 'обучение' and
          sent[-1].get('тема') == 'Курс по АСУ ТП (повтор)',
          sent[-1] if sent else None)

    # ---- правка «вне списка» (ПЗ) — instr-режим, тип записи ----
    page.evaluate("WorkSchedule.editTraining(3)")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('E1: правка ПЗ — заголовок «Правка инструктажа / проверки знаний»',
          fs['title'] == 'Правка инструктажа / проверки знаний', fs['title'])
    check('E2: правка ПЗ — поле «Тип» скрыто (instr-режим)',
          fs['typeVisible'] is False and fs['typeDisplay'] == 'none')
    check('E3: тема «вне списка» выбрана',
          fs['opts'] is not None and 'Внеплановый по наряду №4' in fs['opts'] and
          page.evaluate("document.getElementById('wsTrTitleSel').value") ==
          'Внеплановый по наряду №4', fs['opts'])
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('E4: submit правки «вне списка» → тип записи СОХРАНЁН (проверка_знаний)',
          bool(sent) and sent[-1].get('тип') == 'проверка_знаний' and
          sent[-1].get('тема') == 'Внеплановый по наряду №4',
          sent[-1] if sent else None)

    # ---- правка мероприятия — форма события ----
    page.evaluate("WorkSchedule.editTraining(4)")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('E5: правка примечания — «Правка мероприятия», тип виден',
          fs['title'] == 'Правка мероприятия' and fs['typeVisible'] is True and
          fs['typeVal'] == 'примечание', (fs['title'], fs['typeVal']))
    check('E6: тема в свободном вводе',
          page.evaluate("document.getElementById('wsTrTitle').value") == 'Перенос по приказу')
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    check('F1: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view — регресс блока/кнопок ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'workers-view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    insb = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные инструктажи') !== -1) return cards[i].innerHTML;
    }
    return '';
})()""")
    check('G1: регресс — блок жив: 5 групп эталона',
          insb.count('ws-il-head') == 5, insb.count('ws-il-head'))
    check('G2: подписи «раз в год» в блоке живы', 'раз в год' in insb)
    btns = page.evaluate("""(function(){
    return { addins: document.querySelectorAll('.ws-wgrid2 .ws-emp-addins').length,
             addtr: document.querySelectorAll('.ws-wgrid2 .ws-emp-addtr').length };
})()""")
    check('G3: у зрителя НЕТ кнопок «+ Инструктаж…»/«+ Мероприятие…»',
          btns['addins'] == 0 and btns['addtr'] == 0, btns)
    page.screenshot(path='task410-proof-card-view.png', full_page=False)
    check('G4: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, edit ==========
    print('=== Контекст 3: мобайл 375 светлая edit — форма instr ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 800})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    stack = page.evaluate("""(function(){
        var hs = document.querySelectorAll('.ws-wgrid2 .ws-whead-t');
        var out = [];
        for (var i = 0; i < hs.length; i++) out.push(hs[i].textContent.trim());
        return out;
    })()""")
    check('H1: мобайл — стек ПЯТЬ блоков (регресс)',
          len(stack) == 5 and stack[3].startswith('Повторные инструктажи'), stack)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('H2: мобайл форма — заголовок instr, «Тип» скрыт',
          fs['title'] == 'Новый инструктаж / проверка знаний' and
          fs['typeVisible'] is False, (fs['title'], fs['typeVisible']))
    check('H3: select — 5 пунктов эталона с группами',
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'])
    page.select_option('#wsTrTitleSel', N_OG)
    page.wait_for_timeout(400)
    h3 = page.evaluate(hint_js())
    check('H4: подсказка ОГЭ: «раз в 3 месяца»', h3 == 'раз в 3 месяца', h3)
    page.screenshot(path='task410-proof-form-mobile.png', full_page=False)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('H5: submit с мобайла → тип «инструктаж», тема ОГЭ',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OG, sent[-1] if sent else None)
    check('H6: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
