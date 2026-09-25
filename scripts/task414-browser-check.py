#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 414: browser-check — заявка «В блоке Повторные инструктажи и
# периодическая проверка знаний в картах работников должен быть
# список только добавленных записей, не нужно показывать все 5 групп».
# ПРОВЕРКИ (мок-сервер, порт 8915):
#   1) десктоп 1280 тёмная, edit: карточка Иванова — ПЛОСКИЙ список
#      записей года («тема · дата», ✎/✕), БЕЗ групп-заголовков,
#      «— не проводился», «след. срок», «вне списка:»; пункты канона
#      без записей НЕ показаны; прошлогодняя запись — только в прошлом
#      году (стрелки ‹год›); ПОПАП ячейки — групповой вид СОХРАНЁН
#      (регресс 407); форма «+ Инструктаж…» — регресс 411/412;
#      перезагрузка — кэш-путь;
#   2) десктоп 1280 светлая, view: плоский список БЕЗ ✎/✕ и кнопки
#      «+ Инструктаж…»; пустой работник — «нет инструктажей…»;
#   3) мобайл 375 светлая, edit: блок плоский, форма работает.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8915
TODAY = datetime.date.today()
Y = TODAY.year

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

def ru(iso):
    p = iso.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]

N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_OG = 'Повторный инструктаж по инструкции № 9-ОГЭ'
N_SAM = 'Периодическая проверка знаний на допуск к самостоятельной работе'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_VY = 'Периодическая проверка знаний по охране труда при выполнении работ на высоте'
N_OFF = 'Целевой инструктаж новичка'

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
# ЗАПИСИ: текущий год — 2 по канону + 1 «вне списка»; прошлый год — 1
INSTR_ALL = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': N_OT,
   'дата_начала': d(Y, 1, 15), 'дата_окончания': d(Y, 1, 15),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 102, 'таб_номер': '017', 'тип': 'проверка_знаний', 'тема': N_SAM,
   'дата_начала': d(Y, 3, 20), 'дата_окончания': d(Y, 3, 20),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 103, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': N_OFF,
   'дата_начала': d(Y, 4, 10), 'дата_окончания': d(Y, 4, 10),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 104, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': N_OT,
   'дата_начала': d(Y - 1, 6, 11), 'дата_окончания': d(Y - 1, 6, 11),
   'длительность_дней': 1, 'комментарий': ''},
]
EVENTS_ALL = [
  {'id': 201, 'таб_номер': '017', 'тип': 'обучение', 'тема': 'Курс АСУ ТП',
   'дата_начала': d(Y, 2, 5), 'дата_окончания': d(Y, 2, 7),
   'длительность_дней': 3, 'комментарий': ''},
]
# СЦЕНАРИЙ ПОЛЬЗОВАТЕЛЯ: живой лист ещё не создан (instrList пуст →
# канон Task 412); срезы года — пустые, все записи идут из instrAll
TRAININGS = []
INSTR_LIST = []
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
    if action == 'workSchedule.addTraining':
        API_CALLS.append(('addTraining', dict(body or {})))
        return {'ok': True, 'data': {'id': 100}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


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
                      body='not found (t414-%s)' % tag)
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t414-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors, console_msgs


FORM_STATE_JS = """(function(){
    var sel = document.getElementById('wsTrTitleSel');
    var inp = document.getElementById('wsTrTitle');
    var eg = document.getElementById('wsTrEndGroup');
    var sl = document.getElementById('wsTrStartLabel');
    var emp = document.getElementById('wsTrEmp');
    return {
      title: (document.getElementById('wsTrSheetTitle')||{}).textContent || '',
      empText: emp ? emp.textContent : null,
      selHidden: sel ? sel.hidden : null,
      inpHidden: inp ? inp.hidden : null,
      startLabel: sl ? sl.textContent : null,
      endVisible: eg ? (eg.offsetParent !== null) : null,
      opts: sel ? Array.prototype.map.call(sel.options, function(o){return o.value;}) : null,
      groups: sel ? Array.prototype.map.call(
          sel.querySelectorAll('optgroup'), function(g){return g.label;}) : null
    };
})()"""

CARD_JS = """(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные инструктажи') !== -1)
            return {groups: cards[i].innerHTML.split('ws-il-head').length - 1,
                    text: cards[i].innerText,
                    html: cards[i].innerHTML};
    }
    return {groups: -1, text: '', html: ''};
})()"""


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
    print('=== Контекст 1: десктоп тёмная edit — карточка: только добавленные записи ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'dark', 'flat-dark', keep_cache=True)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    open_card(page)
    card = page.evaluate(CARD_JS)
    check('B1: ЗАЯВКА 414 — групп-заголовков в блоке НЕТ (не все 5 групп)',
          card['groups'] == 0, card['groups'])
    check('B2: записи года — плоскими строками «тема · дата»',
          (N_OT + ' · ' + ru(d(Y, 1, 15))) in card['text'] and
          (N_SAM + ' · ' + ru(d(Y, 3, 20))) in card['text'] and
          (N_OFF + ' · ' + ru(d(Y, 4, 10))) in card['text'],
          card['text'][:200])
    check('B3: НЕТ «— не проводился» / «след. срок» / «вне списка:» / «раз в »',
          all(s not in card['text'] for s in
              ['не проводился', 'след. срок', 'вне списка:', 'раз в ']),
          card['text'][:200])
    check('B4: пункты канона БЕЗ записей не показаны',
          all(s not in card['text'] for s in [N_OG, N_EL, N_VY]))
    check('B5: прошлогодняя запись в списке года НЕ видна',
          ru(d(Y - 1, 6, 11)) not in card['text'])
    check('B6: ✎/✕ у записей (редактору)',
          'WorkSchedule.editTraining(101)' in card['html'] and
          'WorkSchedule.deleteTraining(103)' in card['html'])
    check('B7: кнопка «+ Инструктаж…» в шапке блока',
          '+ Инструктаж…' in card['text'])
    page.screenshot(path='task414-proof-card-dark.png', full_page=False)

    # ---- год-навигация: прошлый год — архивная запись, без групп ----
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Предыдущий год']")
    page.wait_for_timeout(900)
    card2 = page.evaluate(CARD_JS)
    check('C1: ‹ прошлый год — прошлогодняя запись видна',
          (N_OT + ' · ' + ru(d(Y - 1, 6, 11))) in card2['text'],
          card2['text'][:200])
    check('C2: в прошлом году тоже НЕТ групп-заголовков',
          card2['groups'] == 0, card2['groups'])
    check('C3: записи текущего года не «уехали» в прошлый',
          ru(d(Y, 3, 20)) not in card2['text'])
    page.screenshot(path='task414-proof-card-year-prev.png', full_page=False)
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Следующий год']")
    page.wait_for_timeout(700)

    # ---- ПОПАП ячейки: групповой вид СОХРАНЁН (регресс 407) ----
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('.ws-grid tbody tr:first-child td.ws-emp-col')
    page.wait_for_timeout(900)
    popup_html = page.evaluate("(document.getElementById('wsEmpPopup')||{}).innerHTML || ''")
    popup_text = page.evaluate("(document.getElementById('wsEmpPopup')||{}).innerText || ''")
    check('D1: попап ячейки — групповой вид СОХРАНЁН (ws-il-head)',
          'ws-il-head' in popup_html)
    check('D2: попап — записи в группах видны',
          N_OT in popup_text and N_SAM in popup_text)
    check('D3: попап — «— не проводился» по-прежнему нет (компакт)',
          'не проводился' not in popup_text)
    page.screenshot(path='task414-proof-popup-groups.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmpPopup()")
    page.wait_for_timeout(300)

    # ---- форма «+ Инструктаж…» (регресс 411/412) ----
    open_card(page)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('E1: форма — select канона, 5 пунктов в 2 группах',
          fs['selHidden'] is False and fs['inpHidden'] is True and
          fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['groups'] == ['Инструктажи', 'Проверка знаний'],
          (fs['selHidden'], fs['opts']))
    check('E2: работник из карточки, «Дата проведения» (одна дата)',
          fs['empText'] == 'Иванов И. И. · таб. №017' and
          fs['startLabel'] == 'Дата проведения' and fs['endVisible'] is False,
          (fs['empText'], fs['startLabel']))
    page.select_option('#wsTrTitleSel', N_OT)
    page.wait_for_timeout(400)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('E3: submit → однодневная запись, тип «инструктаж»',
          bool(sent) and sent[-1].get('тип') == 'инструктаж' and
          sent[-1].get('тема') == N_OT and
          sent[-1].get('дата_окончания') == sent[-1].get('дата_начала') and
          sent[-1].get('длительность_дней') == 1, sent[-1] if sent else None)
    check('E4: тост «Запись добавлена»',
          'Запись добавлена' in page.evaluate("document.body.innerText"))

    # ---- перезагрузка: кэш-путь ----
    page.reload()
    page.wait_for_timeout(2500)
    open_card(page)
    card3 = page.evaluate(CARD_JS)
    check('F1: после перезагрузки (кэш) — плоский список сохранён',
          card3['groups'] == 0 and
          (N_SAM + ' · ' + ru(d(Y, 3, 20))) in card3['text'],
          card3['text'][:200])
    check('F2: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view — без правки ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'light', 'flat-view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_card(page)
    card = page.evaluate(CARD_JS)
    check('G1: плоский список записей (view)',
          card['groups'] == 0 and
          (N_OT + ' · ' + ru(d(Y, 1, 15))) in card['text'],
          card['text'][:200])
    check('G2: ✎/✕ НЕТ (не редактор)', 'editTraining(' not in card['html'])
    check('G3: кнопки «+ Инструктаж…» НЕТ', '+ Инструктаж…' not in card['text'])
    page.screenshot(path='task414-proof-card-light-view.png', full_page=False)
    open_card(page, 'Петров П. П.')
    cardp = page.evaluate(CARD_JS)
    check('G4: пустой работник — «нет инструктажей и проверок знаний за год»',
          'нет инструктажей и проверок знаний за год' in cardp['text'] and
          cardp['groups'] == 0, cardp['text'][:200])
    check('G5: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, edit ==========
    print('=== Контекст 3: мобайл 375 светлая edit ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors, console_msgs = attach(page, ctx, 'light', 'flat-mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_card(page)
    card = page.evaluate(CARD_JS)
    check('H1: мобайл — плоский список записей, без групп',
          card['groups'] == 0 and
          (N_OFF + ' · ' + ru(d(Y, 4, 10))) in card['text'],
          card['text'][:200])
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fs = page.evaluate(FORM_STATE_JS)
    check('H2: форма на мобайле — select канона + одна дата',
          fs['selHidden'] is False and fs['opts'] == ['', N_OT, N_OG, N_SAM, N_EL, N_VY] and
          fs['startLabel'] == 'Дата проведения', fs['startLabel'])
    page.select_option('#wsTrTitleSel', N_VY)
    page.wait_for_timeout(300)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(900)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('H3: submit с мобайла — ok',
          bool(sent) and sent[-1].get('тема') == N_VY and
          sent[-1].get('длительность_дней') == 1)
    page.screenshot(path='task414-proof-card-mobile.png', full_page=False)
    check('H4: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
