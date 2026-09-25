#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 409: browser-check — заявка «эталон раздела инструктажей и
# проверки знаний: ровно 5 пунктов (2 повторных инструктажа + 3
# периодические проверки знаний; п.5 основание = инструкция № 53-ОТ);
# больше никаких видов мероприятий в блоке и таблице; периодичность
# 12 мес → «раз в год»».
# МОК (эталон заявки 409): Иванов 017 — записи года: инструктаж
#   «Повторный инструктаж по рабочим инструкциям ОТ» (10 дн назад,
#   +6 мес актуально), инструктаж «Повторный инструктаж по
#   инструкции № 9-ОГЭ» (25 дн назад, +3 мес актуально), ПЗ
#   «Внеплановый по наряду №4» (12-е — вне списка), примечание
#   (22-е). instrAll: ПЗ «на допуск к самостоятельной работе»
#   400 дн назад (просрочено) + ПЗ «работы на высоте» Y-1-03-10
#   (просрочено в году табели; архивный снимок в Y-1) + чужой
#   инструктаж (023). eventsAll: Курс АСУ ТП Y-1-05-15 + примечание
#   Y-2-06-01 (min год навигации Y-2).
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, view: попап (5 пунктов эталона: группы/
#      подписи «раз в 6 месяцев/3 месяца/год», вне списка, сроки);
#      тултипы бейджей сетки;
#   2) десктоп 1280 светлая, edit: карточка (3 колонки — регресс
#      406); стрелки ‹год›: Y → Y-1 (архив: снимок «на конец Y-1») →
#      Y-2 (min, ‹ погашена) → возврат; ФОРМА: строгий select по
#      виду (2 И / 3 ПЗ) + подсказка «раз в год · Основание:
#      инструкция № 53-ОТ» + валидация + правка «вне списка»;
#      сводная (регресс 405);
#   3) мобайл 375 светлая, view: стек 5 блоков + element-скрин.
# Порт 8910 (запуск одним вызовом: сервер + проверка).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8910
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

def add_months(iso, months):
    import calendar
    p = [int(x) for x in iso.split('-')]
    y2 = p[0] + (p[1] - 1 + months) // 12
    m2 = (p[1] - 1 + months) % 12 + 1
    dim = calendar.monthrange(y2, m2)[1]
    return d(y2, m2, min(p[2], dim))

def fmt_ru(iso):
    p = iso.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]

N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_OG = 'Повторный инструктаж по инструкции № 9-ОГЭ'
N_SAM = 'Периодическая проверка знаний на допуск к самостоятельной работе'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
N_VY = 'Периодическая проверка знаний по охране труда при выполнении работ на высоте'

OT_DATE = d(Y, M, max(1, TODAY.day - 10))
OT_DUE = add_months(OT_DATE, 6)
OG_DATE = d(Y, M, max(1, TODAY.day - 25))
OG_DUE = add_months(OG_DATE, 3)
SAM_LAST = (TODAY - datetime.timedelta(days=400)).isoformat()
SAM_DUE = add_months(SAM_LAST, 12)
VY_DATE = d(Y - 1, 3, 10)
VY_DUE = add_months(VY_DATE, 12)   # снимок в архиве Y-1

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '', 'комментарий': ''},
  {'таб_номер': '031', 'ФИО': 'Сидоров С. С.', 'тип': 'сменный', 'смена': 3,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 2),
   'дата_приёма': '2023-11-05', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр КИПиА 4 разряда', 'группа_допуска': 'III', 'комментарий': ''},
  {'таб_номер': '045', 'ФИО': 'Ахметзянов Равиль Галиевич', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2021-06-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'группа_допуска': 'II', 'комментарий': ''},
  {'таб_номер': '058', 'ФИО': 'Константинопольский Аркадий Николаевич', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2022-04-11', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА 3 разряд', 'группа_допуска': 'III', 'комментарий': ''},
]
ENTRIES = [
  {'дата': d(Y, M, 3), 'таб_номер': '017', 'статус': 'Д'},
  {'дата': d(Y, M, 5), 'таб_номер': '023', 'статус': 'Д8'},
  {'дата': d(Y, M, 7), 'таб_номер': '031', 'статус': 'Н'},
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
# ЭТАЛОН ЗАЯВКИ 409 — ровно 5 пунктов, ничего больше
INSTR_LIST = [
  {'название': N_OT, 'вид': 'инструктаж', 'периодичность': 6, 'основание': ''},
  {'название': N_OG, 'вид': 'инструктаж', 'периодичность': 3, 'основание': ''},
  {'название': N_SAM, 'вид': 'проверка_знаний', 'периодичность': 12, 'основание': ''},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12, 'основание': ''},
  {'название': N_VY, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': 'инструкция № 53-ОТ'},
]
INSTR_ALL = [
  {'id': 7, 'таб_номер': '017', 'тип': 'проверка_знаний',
   'тема': N_SAM, 'дата_начала': SAM_LAST, 'дата_окончания': SAM_LAST},
  {'id': 8, 'таб_номер': '023', 'тип': 'инструктаж',
   'тема': N_OT, 'дата_начала': d(Y, M, max(1, TODAY.day - 3)),
   'дата_окончания': d(Y, M, max(1, TODAY.day - 3))},
  {'id': 9, 'таб_номер': '017', 'тип': 'проверка_знаний',
   'тема': N_VY, 'дата_начала': VY_DATE, 'дата_окончания': VY_DATE},
]
EVENTS_ALL = [
  {'id': 30, 'таб_номер': '017', 'тип': 'обучение',
   'тема': 'Курс АСУ ТП', 'дата_начала': d(Y - 1, 5, 15), 'дата_окончания': d(Y - 1, 5, 15)},
  {'id': 31, 'таб_номер': '017', 'тип': 'примечание',
   'тема': 'Приём на работу', 'дата_начала': d(Y - 2, 6, 1), 'дата_окончания': d(Y - 2, 6, 1)},
]
VACATIONS = [
  {'id': 1, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(Y, M, 20), 'дата_окончания': d(Y, M, 26)},
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Костюм для защиты от растворов кислот и щелочей',
   'дата_выдачи': d(Y, 8, 17), 'срок_годности': '1 год',
   'дата_окончания': d(Y + 1, 8, 17), 'примечание': ''},
  {'id': 2, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(Y - 1, M, 22), 'срок_годности': '1 год',
   'дата_окончания': d(Y, M, 22), 'примечание': ''},
]
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
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
                      body='not found (t409-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t409-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

CELLS_JS = """(function(){
    var wrap = document.getElementById('wsGridWrap');
    var cells = wrap.querySelectorAll('tbody td.ws-emp-col');
    var out = [];
    for (var i = 0; i < cells.length; i++) {
        var td = cells[i];
        var name = td.querySelector('.ws-emp-name');
        out.push({ fio: name ? name.textContent : null });
    }
    return out;
})()"""

def instr_html_js(selector):
    return """(function(){
    var root = document.querySelector('%s');
    if (!root) return '';
    var heads = root.querySelectorAll('.ws-whead-t, .ws-popup-sec');
    for (var i = 0; i < heads.length; i++) {
        if (heads[i].textContent.indexOf('Повторные инструктажи') !== -1) {
            return heads[i].parentElement.parentElement.innerHTML;
        }
    }
    return '';
})()""" % selector

def block_title_js(block_text):
    return """(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf(%s) !== -1) return t.innerHTML;
    }
    return '';
})()""" % json.dumps(block_text)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, view ==========
    print('=== Контекст 1: десктоп тёмная — попап по эталону + тултипы ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'grid-dark')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    cells = page.evaluate(CELLS_JS)
    check('B0: сетка отрисована (5 работников)', len(cells) == 5, len(cells))
    badges = page.evaluate("""(function(){
    var bs = document.querySelectorAll('.ws-ev-badge');
    var out = [];
    for (var i = 0; i < bs.length; i++) out.push(bs[i].getAttribute('title') || '');
    return out;
})()""")
    joined = ' | '.join(badges)
    check('B1: бейджи в сетке есть', len(badges) > 0, len(badges))
    check('B2: тултип «И — Повторный инструктаж по рабочим инструкциям ОТ»',
          ('И — ' + N_OT) in joined, joined[:200])
    check('B3: тултип «И — Повторный инструктаж по инструкции № 9-ОГЭ»',
          ('И — ' + N_OG) in joined, joined[:200])
    check('B4: тултип «ПЗ — Внеплановый по наряду №4»',
          'ПЗ — Внеплановый по наряду №4' in joined, joined[:200])
    check('B5: тултип «* — Перенос по приказу»',
          '* — Перенос по приказу' in joined, joined[:200])
    page.click("td.ws-emp-col[data-tab='017']")
    page.wait_for_timeout(700)
    card = page.evaluate("(function(){var pp=document.getElementById('wsEmpPopup');" +
                         "return pp?pp.innerHTML:'';})()")
    check('C1: попап открылся; группы шаблона живы',
          'Иванов' in card and 'ws-il-head' in card)
    check('C2: эталон: 4 группы в попапе (пустой «до 1000 В» скрыт)',
          card.count('ws-il-head') == 4, card.count('ws-il-head'))
    check('C3: подписи: «раз в 6 месяцев» и «раз в 3 месяца»',
          'раз в 6 месяцев' in card and 'раз в 3 месяца' in card)
    check('C4: подпись «раз в год» ×2 (самост./высота)',
          card.count('раз в год') == 2, card.count('раз в год'))
    check('C5: старого формата «раз в 12 месяцев» НЕТ',
          'раз в 12 месяцев' not in card)
    check('C6: вне списка: «Внеплановый по наряду №4»',
          'вне списка:' in card and 'Внеплановый по наряду №4' in card)
    check('C7: след. срок ОТ актуален (%s)' % fmt_ru(OT_DUE),
          ('след. срок: ' + fmt_ru(OT_DUE) + ' ✓') in card)
    check('C8: след. срок ОГЭ актуален (%s)' % fmt_ru(OG_DUE),
          ('след. срок: ' + fmt_ru(OG_DUE) + ' ✓') in card)
    check('C9: просрочено самостоятельной (%s)' % fmt_ru(SAM_DUE),
          ('⚠ просрочено с ' + fmt_ru(SAM_DUE)) in card)
    check('C10: просрочено высоты (%s)' % fmt_ru(VY_DUE),
          ('⚠ просрочено с ' + fmt_ru(VY_DUE)) in card)
    check('C11: попап — БЕЗ навигатора года', 'ws-ynav' not in card)
    page.screenshot(path='task409-proof-grid-dark.png', full_page=False)
    page.keyboard.press('Escape')
    page.wait_for_timeout(400)
    check('D1: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, edit ==========
    print('=== Контекст 2: десктоп светлая — архивы + форма по эталону ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'workers-light')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    cols = page.evaluate("""(function(){
        var cols = document.querySelectorAll('.ws-wgrid2 .ws-wcol');
        var out = [];
        for (var ci = 0; ci < cols.length; ci++) {
            var cards = cols[ci].querySelectorAll('.ws-wcard');
            out.push(cards.length);
        }
        return out;
    })()""")
    check('E0: карточка — 3 колонки 3/1/1 (регресс 406)',
          cols == [3, 1, 1], cols)
    insb = page.evaluate(instr_html_js('.ws-wgrid2'))
    check('E1: блок года табели — РОВНО 5 групп эталона',
          insb.count('ws-il-head') == 5, insb.count('ws-il-head'))
    check('E2: «— не проводился» у пункта «до 1000 В» (записей нет)',
          ('ws-il-name">' + N_EL + '<') in insb and '— не проводился' in insb)
    check('E3: «— за %d год не проводился» у высоты (запись %d)' % (Y, Y - 1),
          ('— за ' + str(Y) + ' год не проводился') in insb)
    evT = page.evaluate(block_title_js('Мероприятия'))
    check('E4: «Мероприятия · %d» + навигатор ‹ ›' % Y,
          ('Мероприятия · %d' % Y) in evT and 'ws-ynav' in evT, evT[:120])
    insT = page.evaluate(block_title_js('Повторные инструктажи'))
    check('E5: «Повторные инструктажи… · %d» + навигатор' % Y,
          ('повторные инструктажи и периодическая проверка знаний · %d' % Y)
          .upper() in insT.upper() and 'ws-ynav' in insT, insT[:160])
    page.screenshot(path='task409-proof-card-light.png', full_page=False)
    # ---- стрелка ‹ : Y → Y-1 (архив) ----
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Предыдущий год']")
    page.wait_for_timeout(900)
    insT25 = page.evaluate(block_title_js('Повторные инструктажи'))
    check('F1: после ‹ — «Повторные инструктажи… · %d»' % (Y - 1),
          ('повторные инструктажи и периодическая проверка знаний · %d' % (Y - 1))
          .upper() in insT25.upper(), insT25[:160])
    insb25 = page.evaluate(instr_html_js('.ws-wgrid2'))
    check('F2: архив %d: запись высоты %s в группе' % (Y - 1, fmt_ru(VY_DATE)),
          fmt_ru(VY_DATE) in insb25 and ('ws-il-name">' + N_VY + '<') in insb25)
    check('F3: архив %d: нейтральный «след. срок (на конец %d): %s»'
          % (Y - 1, Y - 1, fmt_ru(VY_DUE)),
          ('след. срок (на конец %d): %s' % (Y - 1, fmt_ru(VY_DUE))) in insb25)
    check('F4: архив %d: БЕЗ ⚠ просрочено' % (Y - 1),
          'просрочено' not in insb25)
    evT25 = page.evaluate(block_title_js('Мероприятия'))
    check('F5: «Мероприятия · %d» после ‹' % (Y - 1),
          ('Мероприятия · %d' % (Y - 1)) in evT25, evT25[:120])
    evb25 = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Мероприятия') !== -1) return cards[i].innerHTML;
    }
    return '';
})()""")
    check('F6: архив мероприятий %d: «Курс АСУ ТП» %s' % (Y - 1, fmt_ru(d(Y - 1, 5, 15))),
          'Курс АСУ ТП' in evb25 and fmt_ru(d(Y - 1, 5, 15)) in evb25)
    page.screenshot(path='task409-proof-archive-%d.png' % (Y - 1), full_page=False)
    # ---- стрелка ‹‹ : Y-1 → Y-2 (минимум) ----
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Предыдущий год']")
    page.wait_for_timeout(900)
    nav24 = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Мероприятия') !== -1) return t.innerHTML;
    }
    return '';
})()""")
    check('G1: «Мероприятия · %d» (минимум по записям)' % (Y - 2),
          ('Мероприятия · %d' % (Y - 2)) in nav24, nav24[:120])
    check('G2: на минимуме ‹ ПОГАШЕНА (ws-ynav-off)',
          'ws-ynav-off' in nav24, nav24[:160])
    evb24 = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Мероприятия') !== -1) return cards[i].innerHTML;
    }
    return '';
})()""")
    check('G3: архив мероприятий %d: примечание «Приём на работу»' % (Y - 2),
          'Приём на работу' in evb24)
    # ---- возврат ›› к году табеля ----
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Следующий год']")
    page.wait_for_timeout(500)
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Следующий год']")
    page.wait_for_timeout(900)
    insT26 = page.evaluate(block_title_js('Повторные инструктажи'))
    check('H1: возврат ›› — «Повторные инструктажи… · %d»' % Y,
          ('повторные инструктажи и периодическая проверка знаний · %d' % Y)
          .upper() in insT26.upper(), insT26[:160])
    # ---- ФОРМА: строгий select по эталону + подсказка ----
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    fstate = page.evaluate("""(function(){
    var sel = document.getElementById('wsTrTitleSel');
    var inp = document.getElementById('wsTrTitle');
    return { selHidden: sel ? sel.hidden : null,
             inpHidden: inp ? inp.hidden : null,
             opts: sel ? Array.prototype.map.call(sel.options,
                 function(o){return o.value;}) : null };
})()""")
    check('I1: «+ Инструктаж…» — select виден, ввод скрыт',
          fstate['selHidden'] is False and fstate['inpHidden'] is True, fstate)
    check('I2: пункты вида «инструктаж» — РОВНО 2 (+ пустой)',
          fstate['opts'] == ['', N_OT, N_OG], fstate['opts'])
    # submit без выбора — валидация (API не зовётся)
    n_calls = len(API_CALLS)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(400)
    check('I3: пустой select → addTraining НЕ вызван',
          len(API_CALLS) == n_calls, len(API_CALLS) - n_calls)
    # выбор пункта → подсказка «раз в 6 месяцев» (без основания)
    page.select_option('#wsTrTitleSel', N_OT)
    page.wait_for_timeout(400)
    hint_txt = page.evaluate("(function(){var h=document.getElementById('wsTrItemHint');" +
                             "return h && !h.hidden ? h.textContent : null;})()")
    check('I4: подсказка пункта ОТ: «раз в 6 месяцев»',
          hint_txt == 'раз в 6 месяцев', hint_txt)
    page.fill('#wsTrStart', OT_DATE)
    page.fill('#wsTrEnd', OT_DATE)
    page.evaluate("WorkSchedule.submitTrainingForm()")
    page.wait_for_timeout(700)
    sent = [b for a, b in API_CALLS if a == 'addTraining']
    check('I5: submit — тема из select',
          bool(sent) and sent[-1].get('тема') == N_OT,
          sent[-1] if sent else None)
    # смена типа → ПЗ пункты (3 проверки знаний)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_timeout(500)
    page.select_option('#wsTrType', 'проверка_знаний')
    page.wait_for_timeout(400)
    opts2 = page.evaluate("""(function(){
    var sel = document.getElementById('wsTrTitleSel');
    return sel && !sel.hidden ? Array.prototype.map.call(sel.options,
        function(o){return o.value;}) : null;
})()""")
    check('I6: тип ПЗ → РОВНО 3 пункта вида (проверки знаний)',
          opts2 == ['', N_SAM, N_EL, N_VY], opts2)
    # выбор высоты → подсказка «раз в год · Основание: инструкция № 53-ОТ»
    page.select_option('#wsTrTitleSel', N_VY)
    page.wait_for_timeout(400)
    hint2 = page.evaluate("(function(){var h=document.getElementById('wsTrItemHint');" +
                          "return h && !h.hidden ? h.textContent : null;})()")
    check('I7: подсказка высоты: «раз в год · Основание: инструкция № 53-ОТ»',
          hint2 == 'раз в год · Основание: инструкция № 53-ОТ', hint2)
    page.screenshot(path='task409-proof-form-pz-hint.png', full_page=False)
    page.select_option('#wsTrType', 'обучение')
    page.wait_for_timeout(400)
    fstate3 = page.evaluate("""(function(){
    var sel = document.getElementById('wsTrTitleSel');
    var inp = document.getElementById('wsTrTitle');
    return { selHidden: sel ? sel.hidden : null, inpHidden: inp ? inp.hidden : null };
})()""")
    check('I8: тип «обучение» — свободный текстовый ввод',
          fstate3['selHidden'] is True and fstate3['inpHidden'] is False, fstate3)
    # правка записи «вне списка» (Внеплановый по наряду №4)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    page.evaluate("WorkSchedule.editTraining(3)")
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    edit_state = page.evaluate("""(function(){
    var sel = document.getElementById('wsTrTitleSel');
    if (!sel || sel.hidden) return null;
    return { value: sel.value,
             opts: Array.prototype.map.call(sel.options, function(o){return o.textContent;}) };
})()""")
    check('I9: правка «вне списка» — select с пунктом «(вне списка)»',
          edit_state is not None and edit_state['value'] == 'Внеплановый по наряду №4' and
          any('вне списка' in t for t in edit_state['opts']), edit_state)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    # сводная «Общая» — регресс 405/406
    page.click(".ws-wtabs button:has-text('Общая')")
    page.wait_for_timeout(900)
    gen = page.evaluate("(function(){var t=document.querySelector('.ws-wgen-table');" +
                        "return t?t.innerHTML:'';})()")
    check('J1: сводная — колонки «Мероприятия · %d» и «Инструктажи · %d»' % (Y, Y),
          ('<th>Мероприятия · %d</th>' % Y) in gen and
          ('<th>Инструктажи · %d</th>' % Y) in gen)
    check('J2: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, view ==========
    print('=== Контекст 3: мобайл 375 светлая — стек + навигатор ===')
    ADMIN = False
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
    check('K1: мобайл — стек ПЯТЬ блоков (регресс 406)',
          len(stack) == 5 and stack[0].find('Иванов') != -1 and
          stack[1].startswith('Отпуска') and stack[2].startswith('Мероприятия') and
          stack[3].startswith('Повторные инструктажи') and
          stack[4].startswith('СИЗ'), stack)
    insM = page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf('Повторные') !== -1) return cards[i].innerHTML;
    }
    return '';
})()""")
    check('K2: мобайл блок И-и-ПЗ: 5 групп + подпись «раз в год»',
          insM.count('ws-il-head') == 5 and 'раз в год' in insM,
          (insM.count('ws-il-head'), 'раз в год' in insM))
    check('K3: навигатор года на мобайле (стрелки кликабельны)',
          'ws-ynav' in insM and 'Предыдущий год' in insM)
    page.click(".ws-wgrid2 .ws-wcard .ws-ynav-btn[title='Предыдущий год']")
    page.wait_for_timeout(900)
    stack2 = page.evaluate("""(function(){
        var hs = document.querySelectorAll('.ws-wgrid2 .ws-whead-t');
        var out = [];
        for (var i = 0; i < hs.length; i++) out.push(hs[i].textContent.trim());
        return out;
    })()""")
    check('K4: мобайл ‹ — архив %d (оба блока сменили год)' % (Y - 1),
          any(t.startswith('Мероприятия · %d' % (Y - 1)) for t in stack2) and
          any(t.startswith('Повторные инструктажи') and
              str(Y - 1) in t for t in stack2), stack2)
    page.screenshot(path='task409-proof-mobile.png', full_page=False)
    el = page.evaluate("""(function(){
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var i = 0; i < cards.length; i++) {
            var t = cards[i].querySelector('.ws-whead-t');
            if (t && t.textContent.indexOf('Повторные инструктажи') !== -1) return i;
        }
        return -1;
    })()""")
    if el is not None and el >= 0:
        page.locator('.ws-wgrid2 .ws-wcard').nth(el).screenshot(
            path='task409-proof-instr-block-mobile.png')
        check('K5: element-скрин блока снят', True)
    else:
        check('K5: element-скрин блока снят', False, el)
    check('K6: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
