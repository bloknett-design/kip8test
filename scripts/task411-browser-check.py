#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 411: browser-check — заявка «скорректировать форму добавления
# инструктажа и проверки знаний в картах работников: выпадающий
# список с фамилиями не нужен (работник вычисляется из карточки);
# поле Инструктаж/проверка знаний — список из Список_И_и_ПЗ; поле
# даты одно — просто дата проведения (одним днём)».
# ПРОВЕРКИ:
#   1) десктоп 1280 тёмная, edit: попап ячейки «+ Мероприятие…» —
#      статичная строка работника, БЕЗ списка фамилий, период дат
#      (событие); карточка «+ Инструктаж…» — работник статично,
#      select 5 пунктов Список_И_и_ПЗ (регресс 410), ОДНА дата
#      «Дата проведения» (окончание/длительность скрыты), submit
#      пишет однодневную запись ДАЖЕ при мусоре в скрытых полях;
#      валидация «Укажите дату проведения»; «+ Мероприятие…» —
#      многодневный период сохраняется; правка И/ПЗ (одна дата) и
#      правка события ДРУГОГО работника (строка из записи);
#   2) десктоп 1280 светлая, view: регресс блока (5 групп),
#      у зрителя нет кнопок;
#   3) мобайл 375 светлая, edit: форма instr — статичный работник,
#      одна дата, submit.
# Порт 8912 (запуск одним вызовом: сервер + проверка).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8912
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
D2 = TODAY + datetime.timedelta(days=2)   # многодневное мероприятие

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_OG = 'Повторный инструктаж по инструкции № 9-ОГЭ'
N_SAM = 'Периодическая проверка знаний на допуск к самостоятельной работе'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_VY = 'Периодическая проверка знаний по охране труда при выполнении работ на высоте'

OT_DATE = d(Y, M, max(1, TODAY.day - 10))

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
  {'id': 3, 'таб_номер': '017', 'тип': 'проверка_знаний',
   'тема': 'Внеплановый по наряду №4', 'дата_начала': d(Y, M, 12),
   'дата_окончания': d(Y, M, 12)},
  # id 4 — ДРУГОЙ работник: правка покажет в строке Петрова
  {'id': 4, 'таб_номер': '023', 'тип': 'примечание',
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
INSTR_ALL = []
EVENTS_ALL = []
ENTRIES = []
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
                      body='not found (t411-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t411-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

FORM_STATE_JS = """(function(){
    var sel = document.getElementById('wsTrTitleSel');
    var inp = document.getElementById('wsTrTitle');
    var tg = document.getElementById('wsTrTypeGroup');
    var tb = document.getElementById('wsTrTabGroup');
    var lbl = document.getElementById('wsTrTitleLabel');
    var eg = document.getElementById('wsTrEndGroup');
    var dg = document.getElementById('wsTrDaysGroup');
    var sl = document.getElementById('wsTrStartLabel');
    var emp = document.getElementById('wsTrEmp');
    return {
      title: (document.getElementById('wsTrSheetTitle')||{}).textContent || '',
      empText: emp ? emp.textContent : null,
      empVisible: emp ? (emp.offsetParent !== null) : null,
      tabSelect: tb ? !!tb.querySelector('select') : null,
      workerLabel: tb ? ((tb.querySelector('.flow-input-label')||{}).textContent || '') : null,
      selHidden: sel ? sel.hidden : null,
      inpHidden: inp ? inp.hidden : null,
      typeDisplay: tg ? tg.style.display : null,
      typeVisible: tg ? (tg.offsetParent !== null) : null,
      label: lbl ? lbl.textContent : null,
      startLabel: sl ? sl.textContent : null,
      endDisplay: eg ? eg.style.display : null,
      endVisible: eg ? (eg.offsetParent !== null) : null,
      daysDisplay: dg ? dg.style.display : null,
      daysVisible: dg ? (dg.offsetParent !== null) : null,
      opts: sel ? Array.prototype.map.call(sel.options, function(o){return o.value;}) : null,
      groups: sel ? Array.prototype.map.call(
          sel.querySelectorAll('optgroup'), function(g){return g.label;}) : null
    };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — работник статично, одна дата ===')
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

    # ---- попап ячейки: «+ Мероприятие…» — событие, работник ячейки ----
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
    page.click("#wsCellPopup .ws-popup-more:has-text('+ Мероприятие…')")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('B2: заголовок «Новое мероприятие»', fs['title'] == 'Новое мероприятие', fs['title'])
    check('B3: работник ячейки — статичная строка «Иванов И. И. · таб. №017»',
          fs['empText'] == 'Иванов И. И. · таб. №017' and fs['empVisible'] is True,
          (fs['empText'], fs['empVisible']))
    check('B4: выпадающего списка фамилий НЕТ, подпись «Работник»',
          fs['tabSelect'] is False and fs['workerLabel'] == 'Работник',
          (fs['tabSelect'], fs['workerLabel']))
    check('B5: событие — период дат (начало/окончание/длительность видны)',
          fs['startLabel'] == 'Дата начала' and fs['endVisible'] is True and
          fs['daysVisible'] is True, (fs['startLabel'], fs['endVisible'], fs['daysVisible']))
    check('B6: дата начала = дата ячейки',
          page.evaluate("document.getElementById('wsTrStart').value") == cell_date)
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
    check('C2: работник карточки — статичная строка (без списка фамилий)',
          fs['empText'] == 'Иванов И. И. · таб. №017' and fs['tabSelect'] is False,
          (fs['empText'], fs['tabSelect']))
    check('C3: поле «Тип» СКРЫТО (регресс 410)',
          fs['typeVisible'] is False and fs['typeDisplay'] == 'none',
          (fs['typeVisible'], fs['typeDisplay']))
    check('C4: select 5 пунктов «Список_И_и_ПЗ» + группы (регресс 410)',
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'], fs['opts'])
    check('C5: ОДНА дата — «Дата проведения», окончание/длительность СКРЫТЫ',
          fs['startLabel'] == 'Дата проведения' and
          fs['endVisible'] is False and fs['daysVisible'] is False and
          fs['endDisplay'] == 'none' and fs['daysDisplay'] == 'none',
          (fs['startLabel'], fs['endVisible'], fs['daysVisible']))
    page.screenshot(path='task411-proof-form-instr.png', full_page=False)

    # валидация: пункт выбран, даты НЕТ → API не зовётся, тост
    page.select_option('#wsTrTitleSel', N_OT)
    page.wait_for_timeout(300)
    page.evaluate("document.getElementById('wsTrStart').value = ''")
    n_calls = len(API_CALLS)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(400)
    body_txt = page.evaluate("document.body.innerText")
    check('C6: без даты → тост «Укажите дату проведения», API не звался',
          len(API_CALLS) == n_calls and 'Укажите дату проведения' in body_txt,
          (len(API_CALLS) - n_calls))
    page.fill('#wsTrStart', d(Y, M, TODAY.day))

    # МУСОР в скрытых полях → однодневная запись
    page.evaluate("document.getElementById('wsTrEnd').value = '2099-12-31';" +
                 "document.getElementById('wsTrDays').value = '7';")
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('C7: submit → ОДНОДНЕВНАЯ запись (конец=начало, 1 день) при мусоре в скрытых полях',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OT and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)
    check('C8: тост «Запись добавлена»',
          'Запись добавлена' in page.evaluate("document.body.innerText"))

    # ---- «+ Мероприятие…» — многодневный период сохраняется ----
    page.click('.ws-wgrid2 .ws-emp-addtr')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('D1: «Новое мероприятие» — период дат виден',
          fs['title'] == 'Новое мероприятие' and
          fs['startLabel'] == 'Дата начала' and fs['endVisible'] is True and
          fs['daysVisible'] is True, (fs['title'], fs['startLabel']))
    page.fill('#wsTrTitle', 'Курс по АСУ ТП (3 дня)')
    page.fill('#wsTrEnd', d(D2.year, D2.month, D2.day))
    page.fill('#wsTrDays', '3')
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('D2: submit события → многодневный период СОХРАНЁН',
          bool(sent) and sent[-1].get('тип') == 'обучение' and
          sent[-1].get('тема') == 'Курс по АСУ ТП (3 дня)' and
          sent[-1].get('дата_окончания') == d(D2.year, D2.month, D2.day) and
          sent[-1].get('длительность_дней') == 3, sent[-1] if sent else None)

    # ---- правка И/ПЗ (id 1, ОТ) — одна дата ----
    page.evaluate("WorkSchedule.editTraining(1)")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('E1: правка И/ПЗ — заголовок + одна дата',
          fs['title'] == 'Правка инструктажа / проверки знаний' and
          fs['startLabel'] == 'Дата проведения' and fs['endVisible'] is False,
          (fs['title'], fs['startLabel'], fs['endVisible']))
    check('E2: правка — работник записи в статичной строке',
          fs['empText'] == 'Иванов И. И. · таб. №017', fs['empText'])
    check('E3: тема записи выбрана в select',
          page.evaluate("document.getElementById('wsTrTitleSel').value") == N_OT)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('E4: правка И/ПЗ → однодневная запись',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)

    # ---- правка события ДРУГОГО работника (id 4, Петров) ----
    page.evaluate("WorkSchedule.editTraining(4)")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('F1: правка события — заголовок + период дат',
          fs['title'] == 'Правка мероприятия' and fs['endVisible'] is True and
          fs['daysVisible'] is True, fs['title'])
    check('F2: работник ИЗ ЗАПИСИ — «Петров П. П. · таб. №023»',
          fs['empText'] == 'Петров П. П. · таб. №023', fs['empText'])
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    check('G1: JS-ошибок нет', js_errors == [], js_errors[:3])
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
    check('H1: регресс — блок жив: 5 групп эталона',
          insb.count('ws-il-head') == 5, insb.count('ws-il-head'))
    btns = page.evaluate("""(function(){
    return { addins: document.querySelectorAll('.ws-wgrid2 .ws-emp-addins').length,
             addtr: document.querySelectorAll('.ws-wgrid2 .ws-emp-addtr').length };
})()""")
    check('H2: у зрителя НЕТ кнопок добавления',
          btns['addins'] == 0 and btns['addtr'] == 0, btns)
    check('H3: JS-ошибок нет', js_errors == [], js_errors[:3])
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
    check('I1: мобайл — стек ПЯТЬ блоков (регресс)',
          len(stack) == 5 and stack[3].startswith('Повторные инструктажи'), stack)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('I2: мобайл форма — работник статично, одна дата, «Тип» скрыт',
          fs['empText'] == 'Иванов И. И. · таб. №017' and
          fs['tabSelect'] is False and fs['startLabel'] == 'Дата проведения' and
          fs['endVisible'] is False and fs['typeVisible'] is False,
          (fs['empText'], fs['startLabel'], fs['endVisible']))
    check('I3: select — 5 пунктов эталона с группами',
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'])
    page.screenshot(path='task411-proof-form-mobile.png', full_page=False)
    page.select_option('#wsTrTitleSel', N_OG)
    page.wait_for_timeout(400)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('I4: submit с мобайла → однодневная запись, тип «инструктаж»',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OG and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)
    check('I5: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
