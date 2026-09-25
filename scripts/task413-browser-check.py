#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 413: browser-check — заявка «При добавлении инструктажа или
# проверки знаний в форме ввода в приложении, они не добавляются,
# ещё я удалил таблицу Инструктажи в файле табель_КИП_ИОС… Где
# должны сохраняться записи? Что нужно сделать чтобы был их
# архив?».
# Причина: лист «Инструктажи» удалён → addTraining падал
# sheet_not_found. ПРОВЕРКИ (мок-сервер, порт 8914):
#   1) десктоп 1280 тёмная, edit, НОВЫЙ сервер (listTrainings ок,
#      все срезы пустые — лист удалён): сетка рендерится (не экран
#      ошибки), карточка — 5 групп канона «— не проводился»;
#      «+ Инструктаж…» — select канона (регресс 412), submit →
#      тост «Запись добавлена»; ОШИБОЧНЫЙ РЕЖИМ (старый Apps
#      Script): addTraining → sheet_not_found → тост «таблица
#      «Инструктажи» отсутствует в файле табель_КИП_ИОС»
#      (маппинг _apiErrText 413); «+ Мероприятие…» — регресс
#      (свободная тема, период); перезагрузка — кэш-путь;
#   2) десктоп 1280 светлая, view: старый сервер для listTrainings
#      (sheet_not_found) → экран ошибки с ПОНЯТНЫМ текстом (не
#      сырой код); затем нормальный режим — 5 групп, нет кнопок;
#   3) мобайл 375 светлая, edit: форма instr из канона, submit ok.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8914
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_OG = 'Повторный инструктаж по инструкции № 9-ОГЭ'
N_SAM = 'Периодическая проверка знаний на допуск к самостоятельной работе'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_VY = 'Периодическая проверка знаний по охране труда при выполнении работ на высоте'

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
# СЦЕНАРИЙ ПОЛЬЗОВАТЕЛЯ: таблица «Инструктажи» удалена из файла —
# все срезы записей пустые; НОВЫЙ сервер (Task 413) отвечает ok.
TRAININGS = []
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
# режимы мока: 'ok' — новый сервер (Task 413);
# 'sheet_not_found' — старый Apps Script (до обновления пользователем)
ADD_MODE = 'ok'
LIST_MODE = 'ok'


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
        # старый Apps Script: лист удалён → ошибка (до Task 413);
        # новый: ok с пустыми срезами
        if LIST_MODE == 'sheet_not_found':
            return {'ok': False, 'error': 'sheet_not_found: Инструктажи'}
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
        if ADD_MODE == 'sheet_not_found':
            return {'ok': False, 'error': 'sheet_not_found: Инструктажи'}
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
                      body='not found (t413-%s)' % tag)
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t413-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors, console_msgs


FORM_STATE_JS = """(function(){
    var sel = document.getElementById('wsTrTitleSel');
    var inp = document.getElementById('wsTrTitle');
    var tg = document.getElementById('wsTrTypeGroup');
    var lbl = document.getElementById('wsTrTitleLabel');
    var eg = document.getElementById('wsTrEndGroup');
    var sl = document.getElementById('wsTrStartLabel');
    var emp = document.getElementById('wsTrEmp');
    return {
      title: (document.getElementById('wsTrSheetTitle')||{}).textContent || '',
      empText: emp ? emp.textContent : null,
      selHidden: sel ? sel.hidden : null,
      inpHidden: inp ? inp.hidden : null,
      typeVisible: tg ? (tg.offsetParent !== null) : null,
      label: lbl ? lbl.textContent : null,
      startLabel: sl ? sl.textContent : null,
      endVisible: eg ? (eg.offsetParent !== null) : null,
      opts: sel ? Array.prototype.map.call(sel.options, function(o){return o.value;}) : null,
      groups: sel ? Array.prototype.map.call(
          sel.querySelectorAll('optgroup'), function(g){return g.label;}) : null,
      hint: (document.getElementById('wsTrItemHint')||{}).textContent || ''
    };
})()"""

CARD_GROUPS_JS = """(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные инструктажи') !== -1)
            return cards[i].innerHTML.split('ws-il-head').length - 1;
    }
    return 0;
})()"""

CARD_TEXT_JS = """(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные инструктажи') !== -1) return cards[i].innerText;
    }
    return '';
})()"""


def open_card(page):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — лист «Инструктажи» удалён (новый сервер) ===')
    ADMIN = True
    ADD_MODE = 'ok'
    LIST_MODE = 'ok'
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    # keep_cache=True: перезагрузка в конце проверит кэш-путь
    js_errors, console_msgs = attach(page, ctx, 'dark', 'empty-dark', keep_cache=True)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    check('A2: ЗАЯВКА 413 — сетка рендерится (listTrainings пустой НЕ валит загрузку)',
          page.evaluate("(function(){var w=document.querySelector('#wsWrap')||document.querySelector('.ws-page')||document.body;return (w.innerText||'').indexOf('Ошибка загрузки')===-1;})()"))
    check('A3: экрана ошибки sheet_not_found нет',
          'sheet_not_found' not in page.evaluate("document.body.innerText"))
    page.screenshot(path='task413-proof-grid-ok.png', full_page=False)

    # ---- карточка: 5 групп канона, «— не проводился» ----
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    card = page.evaluate(CARD_TEXT_JS)
    check('B1: карточка — 5 групп канона (архив записей пуст — каркас жив)',
          page.evaluate(CARD_GROUPS_JS) == 5)
    check('B2: «— не проводился» в группах (записей нет)',
          'не проводился' in card, card[:150])

    # ---- «+ Инструктаж…»: select канона + submit ok ----
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('C1: форма — select канона, 5 пунктов в 2 группах (регресс 412)',
          fs['selHidden'] is False and fs['inpHidden'] is True and
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'],
          (fs['selHidden'], fs['opts']))
    check('C2: работник из карточки, одна дата «Дата проведения» (регресс 411)',
          fs['empText'] == 'Иванов И. И. · таб. №017' and
          fs['startLabel'] == 'Дата проведения' and fs['endVisible'] is False,
          (fs['empText'], fs['startLabel']))
    page.select_option('#wsTrTitleSel', N_OT)
    page.wait_for_timeout(400)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('C3: submit → однодневная запись, тип «инструктаж»',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OT and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)
    check('C4: тост «Запись добавлена»',
          'Запись добавлена' in page.evaluate("document.body.innerText"))

    # ---- ОШИБОЧНЫЙ ПУТЬ: старый Apps Script (addTraining → sheet_not_found) ----
    ADD_MODE = 'sheet_not_found'
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    page.select_option('#wsTrTitleSel', N_SAM)
    page.wait_for_timeout(300)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    body_txt = page.evaluate("document.body.innerText")
    check('D1: ЗАЯВКА 413 — тост с ПОНЯТНЫМ текстом (не «sheet_not_found: Инструктажи»)',
          'табель_КИП_ИОС' in body_txt and 'отсутствует в' in body_txt and
          'Инструктажи' in body_txt, body_txt[:200])
    check('D2: текст ведёт к действию — «обновите WorkSchedule.gs»',
          'WorkSchedule.gs' in body_txt and 'создана автоматически' in body_txt,
          body_txt[:200])
    check('D3: сырого кода ошибки нет',
          'sheet_not_found: Инструктажи' not in body_txt)
    page.screenshot(path='task413-proof-toast-friendly.png', full_page=False)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    ADD_MODE = 'ok'

    # ---- «+ Мероприятие…» — регресс события ----
    page.click('.ws-wgrid2 .ws-emp-addtr')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('E1: «Новое мероприятие» — тема свободная, период дат (регресс)',
          fs['title'] == 'Новое мероприятие' and
          fs['inpHidden'] is False and fs['selHidden'] is True and
          fs['startLabel'] == 'Дата начала' and fs['endVisible'] is True,
          (fs['title'], fs['inpHidden'], fs['startLabel']))
    page.fill('#wsTrTitle', 'Курс по АСУ ТП')
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('E2: submit события — тип «обучение», тема свободная',
          bool(sent) and sent[-1].get('тип') == 'обучение' and
          sent[-1].get('тема') == 'Курс по АСУ ТП',
          sent[-1] if sent else None)

    # ---- перезагрузка: кэш-путь (пустые срезы в кэше не ломают вид) ----
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    check('F1: после перезагрузки (кэш) — сетка жива, 5 групп канона',
          page.evaluate(CARD_GROUPS_JS) == 5)
    check('G1: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view — старый сервер (listTrainings ошибка) ===')
    ADMIN = False
    LIST_MODE = 'sheet_not_found'
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'light', 'oldserver-view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    body_txt = page.evaluate("document.body.innerText")
    # старый сервер: loadGrid падает — экран/тост с понятным текстом (413)
    check('H1: экран ошибки — ПОНЯТНЫЙ текст «таблица «Инструктажи» отсутствует…»',
          'табель_КИП_ИОС' in body_txt and 'Инструктажи' in body_txt,
          body_txt[:200])
    check('H2: сырой код «sheet_not_found: Инструктажи» НЕ показан',
          'sheet_not_found: Инструктажи' not in body_txt)
    page.screenshot(path='task413-proof-old-server-error.png', full_page=False)
    check('H3: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, edit ==========
    print('=== Контекст 3: мобайл 375 светлая edit — форма из канона, submit ok ===')
    ADMIN = True
    LIST_MODE = 'ok'
    ADD_MODE = 'ok'
    ctx = browser.new_context(viewport={'width': 375, 'height': 800})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'light', 'empty-mobile')
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
    check('I1: мобайл — стек 5 блоков, И/ПЗ на месте',
          len(stack) == 5 and stack[3].startswith('Повторные инструктажи'), stack)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('I2: мобайл форма — select канона, одна дата',
          fs['selHidden'] is False and fs['inpHidden'] is True and
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['startLabel'] == 'Дата проведения',
          (fs['selHidden'], fs['opts']))
    page.screenshot(path='task413-proof-form-mobile.png', full_page=False)
    page.select_option('#wsTrTitleSel', N_OG)
    page.wait_for_timeout(400)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('I3: submit с мобайла → однодневная запись, тип «инструктаж»',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OG and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)
    check('I4: тост «Запись добавлена»',
          'Запись добавлена' in page.evaluate("document.body.innerText"))
    check('I5: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
