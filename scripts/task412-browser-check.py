#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 412: browser-check — заявка «Нет выпадающего списка в форме
# выбора инструктажа и проверки знания, просто пустое поле для
# ручного ввода, а должен быть список из таблицы Список_И_и_ПЗ».
# Причина: боевой Apps Script не отдаёт instrList. ПРОВЕРКИ (сервер
# в моке отдаёт instrList: [] — СЦЕНАРИЙ ПОЛЬЗОВАТЕЛЯ):
#   1) десктоп 1280 тёмная, edit: карточка — 5 ГРУПП канона (не
#      плоский список!), подписи «раз в 6 месяцев/3 месяца/год»,
#      «вне списка:», «— не проводился»; console.warn фолбэка;
#      «+ Инструктаж…» — select ВИДЕН (не свободный ввод), 5 пунктов
#      в 2 группах, подсказка «раз в год · Основание: инструкция
#      № 53-ОТ», submit → тип = вид пункта, однодневная запись
#      (регресс 411); «+ Мероприятие…» — тема свободный ввод, период
#      (регресс); правка «вне списка» — отдельный пункт (регресс
#      410); ПЕРЕЗАГРУЗКА (кэш) — 5 групп остаются;
#   2) десктоп 1280 светлая, view: 5 групп канона, нет кнопок;
#   3) мобайл 375 светлая, edit: стек 5 блоков, форма instr — select
#      из канона, submit.
# Порт 8913 (запуск одним вызовом: сервер + проверка).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8913
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
]
# СЦЕНАРИЙ ПОЛЬЗОВАТЕЛЯ: сервер НЕ отдаёт пункты «Список_И_и_ПЗ» —
# старый Apps Script / лист не создан / деплой прежней версии.
# Клиент (Task 412) подставляет встроенный эталон _INSTR_CANON.
INSTR_LIST = []
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

def attach(page, ctx, theme, tag, keep_cache=False):
    js_errors = []
    console_msgs = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    page.on('console', lambda msg: console_msgs.append(msg.text))

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
                      body='not found (t412-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    pre = ''
    if not keep_cache:
        pre += ("try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
                "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};")
    ctx.add_init_script(
        pre +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t412-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors, console_msgs

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
      tabSelect: tb ? !!tb.querySelector('select') : null,
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
          sel.querySelectorAll('optgroup'), function(g){return g.label;}) : null,
      hint: (document.getElementById('wsTrItemHint')||{}).textContent || ''
    };
})()"""

CARD_BLOCK_JS = """(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные инструктажи') !== -1) return cards[i].innerText;
    }
    return '';
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — сервер БЕЗ instrList, канон ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    # keep_cache=True: перезагрузка в конце проверит кэш-путь канона
    js_errors, console_msgs = attach(page, ctx, 'dark', 'canon-dark', keep_cache=True)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    card = page.evaluate(CARD_BLOCK_JS)
    check('B1: карточка — 5 ГРУПП канона (не плоский список)',
          card.count('Основание:') >= 0 and
          page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные инструктажи') !== -1)
            return cards[i].innerHTML.split('ws-il-head').length - 1;
    }
    return 0;
})()""") == 5)
    check('B2: подписи периодичности канона (6 мес / 3 мес / год)',
          'раз в 6 месяцев' in card and 'раз в 3 месяца' in card and
          'раз в год' in card,
          card[:200])
    check('B3: «вне списка:» — запись вне эталона показана',
          'вне списка' in card and 'Внеплановый по наряду №4' in card)
    check('B4: «— не проводился» в группах без записей',
          'не проводился' in card)
    check('B5: диагностика фолбэка — console.warn «[Список_И_и_ПЗ]»',
          any('[Список_И_и_ПЗ]' in m for m in console_msgs),
          console_msgs[:3])
    page.screenshot(path='task412-proof-card-groups.png', full_page=False)

    # ---- «+ Инструктаж…» — select ИЗ КАНОНА (заявка 412) ----
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('C1: заголовок «Новый инструктаж / проверка знаний»',
          fs['title'] == 'Новый инструктаж / проверка знаний', fs['title'])
    check('C2: ЗАЯВКА 412 — select ВИДЕН (не пустое поле ручного ввода)',
          fs['selHidden'] is False and fs['inpHidden'] is True,
          (fs['selHidden'], fs['inpHidden']))
    check('C3: работник карточки — статичная строка (регресс 411)',
          fs['empText'] == 'Иванов И. И. · таб. №017' and fs['tabSelect'] is False,
          (fs['empText'], fs['tabSelect']))
    check('C4: select — 5 ПУНКТОВ КАНОНА в 2 группах',
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'], fs['opts'])
    check('C5: «Тип» скрыт (регресс 410), ОДНА дата «Дата проведения» (регресс 411)',
          fs['typeVisible'] is False and fs['startLabel'] == 'Дата проведения' and
          fs['endVisible'] is False and fs['daysVisible'] is False,
          (fs['typeVisible'], fs['startLabel'], fs['endVisible']))
    page.select_option('#wsTrTitleSel', N_VY)
    page.wait_for_timeout(400)
    fs = page.evaluate(FORM_STATE_JS)
    check('C6: подсказка пункта «высота» из канона',
          fs['hint'] == 'раз в год · Основание: инструкция № 53-ОТ', fs['hint'])
    page.screenshot(path='task412-proof-form-canon.png', full_page=False)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('C7: submit → тип = «вид» пункта (проверка_знаний), однодневная',
          bool(sent) and sent[-1].get('тип') == 'проверка_знаний' and
          sent[-1].get('тема') == N_VY and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)
    check('C8: тост «Запись добавлена»',
          'Запись добавлена' in page.evaluate("document.body.innerText"))

    # ---- «+ Мероприятие…» — регресс события (тема свободная, период) ----
    page.click('.ws-wgrid2 .ws-emp-addtr')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('D1: «Новое мероприятие» — тема СВОБОДНЫЙ ввод, период дат',
          fs['title'] == 'Новое мероприятие' and
          fs['inpHidden'] is False and fs['selHidden'] is True and
          fs['startLabel'] == 'Дата начала' and fs['endVisible'] is True and
          fs['daysVisible'] is True,
          (fs['title'], fs['inpHidden'], fs['startLabel']))
    page.fill('#wsTrTitle', 'Курс по АСУ ТП')
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('D2: submit события — тип «обучение», тема свободная',
          bool(sent) and sent[-1].get('тип') == 'обучение' and
          sent[-1].get('тема') == 'Курс по АСУ ТП',
          sent[-1] if sent else None)

    # ---- правка «вне списка» (id 3) — отдельный пункт (регресс 410) ----
    page.evaluate("WorkSchedule.editTraining(3)")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('E1: правка «вне списка» — select с отдельным пунктом',
          fs['selHidden'] is False and
          'Внеплановый по наряду №4 (вне списка)' in
          page.evaluate("document.getElementById('wsTrTitleSel').innerHTML"),
          fs['selHidden'])
    check('E2: правка — одна дата «Дата проведения» (регресс 411)',
          fs['startLabel'] == 'Дата проведения' and fs['endVisible'] is False)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # ---- перезагрузка: кэш-путь канона (_restoreCachedView) ----
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    card2 = page.evaluate(CARD_BLOCK_JS)
    check('F1: после перезагрузки (кэш) — снова 5 групп канона',
          'раз в год' in card2 and 'раз в 6 месяцев' in card2 and
          'вне списка' in card2, card2[:200])
    check('G1: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view — группы канона у зрителя ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'light', 'canon-view')
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
    check('H1: зритель — 5 групп канона (групповой вид)',
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
    print('=== Контекст 3: мобайл 375 светлая edit — форма instr из канона ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 800})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'light', 'canon-mobile')
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
    check('I1: мобайл — стек ПЯТЬ блоков, И/ПЗ на месте',
          len(stack) == 5 and stack[3].startswith('Повторные инструктажи'), stack)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('I2: мобайл форма — select из КАНОНА (не свободный ввод)',
          fs['selHidden'] is False and fs['inpHidden'] is True and
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'],
          (fs['selHidden'], fs['opts']))
    check('I3: одна дата «Дата проведения», «Тип» скрыт',
          fs['startLabel'] == 'Дата проведения' and fs['typeVisible'] is False)
    page.screenshot(path='task412-proof-form-mobile.png', full_page=False)
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
