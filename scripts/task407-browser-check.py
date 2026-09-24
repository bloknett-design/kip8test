#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 407: browser-check — заявка «блок Повторные инструктажи и
# периодическая проверка знаний формируется из двух таблиц:
# "Список_И_и_ПЗ" (шаблонный список) + "Инструктажи" (записи
# пользователя; связка по столбцу "название" = "тема" записи)».
# МОК: 5 работников; Иванов 017 — отпуск, 2 СИЗ, мероприятия:
#   инструктаж «Охрана труда» (10-е), обучение «Пожарная безопасность»
#   (18-е, тема = пункт шаблона, но тип обучение → в блоке МЕРОПРИЯТИЯ),
#   «Проверка знаний» «Экзамен» (12-е, вне шаблона), примечание (22-е),
#   инструктаж «Целевой инструктаж» (5-е, разовый пункт).
# ШАБЛОН «Список_И_и_ПЗ»: Охрана труда/инструктаж/6 мес;
#   Электробезопасность/проверка_знаний/12 мес (последняя запись —
#   400 дней назад → ПРОСРОЧЕНО); Пожарная безопасность/инструктаж/
#   6 мес (записей нет → «— не проводился»); Целевой/инструктаж/
#   разовый. instrAll: ЭБ прошлого года (017) + ОТ чужого работника
#   (023 — фильтр по работнику).
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, view: попап ячейки — группы шаблона,
#      «след. срок ✓»/«⚠ просрочено», «вне списка», пустой пункт
#      скрыт, СИЗ нет (регресс 403), «Мероприятия» живы (регресс 405);
#   2) десктоп 1280 светлая, edit: карточка — 3 колонки (регресс
#      406); блок инструктажей: 4 группы, «— не проводился»/
#      «— в этом году не проводился», ✎/✕, «+ Инструктаж…»;
#      datalist «Темы» по виду пункта; сводная (регресс 405);
#   3) мобайл 375 светлая, view: стек 5 блоков (регресс 406) +
#      element-скрин блока инструктажей.
# Порт 8908 (запуск одним вызовом: сервер + проверка).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8908
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

OT_DATE = d(Y, M, max(1, TODAY.day - 10))        # в текущем месяце/году
OT_DUE = add_months(OT_DATE, 6)                  # будущее → «след. срок ✓»
CI_DATE = d(Y, M, max(1, TODAY.day - 5))
EB_LAST = (TODAY - datetime.timedelta(days=400)).isoformat()
EB_DUE = add_months(EB_LAST, 12)                 # ~35 дней назад → просрочено
EX_DATE = d(Y, M, 12)

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
   'тема': 'Охрана труда', 'дата_начала': OT_DATE, 'дата_окончания': OT_DATE},
  {'id': 2, 'таб_номер': '017', 'тип': 'обучение',
   'тема': 'Пожарная безопасность', 'дата_начала': d(Y, M, 18), 'дата_окончания': d(Y, M, 18)},
  {'id': 3, 'таб_номер': '017', 'тип': 'Проверка знаний',
   'тема': 'Экзамен', 'дата_начала': EX_DATE, 'дата_окончания': EX_DATE},
  {'id': 4, 'таб_номер': '017', 'тип': 'примечание',
   'тема': 'Перенос по приказу', 'дата_начала': d(Y, M, 22), 'дата_окончания': d(Y, M, 22)},
  {'id': 5, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': 'Целевой инструктаж', 'дата_начала': CI_DATE, 'дата_окончания': CI_DATE},
]
INSTR_LIST = [
  {'название': 'Охрана труда', 'вид': 'инструктаж',
   'периодичность': 6, 'основание': 'не реже 1 раза в 6 месяцев'},
  {'название': 'Электробезопасность', 'вид': 'проверка_знаний',
   'периодичность': 12, 'основание': 'ежегодно'},
  {'название': 'Пожарная безопасность', 'вид': 'инструктаж',
   'периодичность': 6, 'основание': ''},
  {'название': 'Целевой инструктаж', 'вид': 'инструктаж',
   'периодичность': 0, 'основание': 'разовый'},
]
INSTR_ALL = [
  # ЭБ Иванова — 400 дней назад (прошлый год): +12 мес → просрочено
  {'id': 7, 'таб_номер': '017', 'тип': 'проверка_знаний',
   'тема': 'Электробезопасность', 'дата_начала': EB_LAST, 'дата_окончания': EB_LAST},
  # ОТ ДРУГОГО работника — не должен попасть в карточку Иванова
  {'id': 8, 'таб_номер': '023', 'тип': 'инструктаж',
   'тема': 'Охрана труда', 'дата_начала': d(Y, M, max(1, TODAY.day - 3)),
   'дата_окончания': d(Y, M, max(1, TODAY.day - 3))},
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
        # Task 407: trainings (год) + instrList (шаблон) + instrAll
        return {'ok': True, 'data': {'trainings': list(TRAININGS),
                                    'instrList': list(INSTR_LIST),
                                    'instrAll': list(INSTR_ALL)}}
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
                      body='not found (t407-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t407-%s');" % tag +
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

# содержимое блока b5 (попап или карточка): по селектору контейнера
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

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, view ==========
    print('=== Контекст 1: десктоп тёмная — попап ячейки: группы шаблона ===')
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
    page.click("td.ws-emp-col[data-tab='017']")
    page.wait_for_timeout(700)
    card = page.evaluate("(function(){var pp=document.getElementById('wsEmpPopup');" +
                         "return pp?pp.innerHTML:'';})()")
    check('C1: попап открылся (Иванов)', 'Иванов' in card)
    iIns = card.find('Повторные инструктажи')
    insPart = card[iIns:] if iIns != -1 else ''
    check('C2: секция «Повторные инструктажи … · %d»' % Y,
          ('Повторные инструктажи и периодическая проверка знаний · %d' % Y) in card)
    check('C3: группа «Охрана труда» + «раз в 6 месяцев»',
          'ws-il-name">Охрана труда<' in insPart and 'раз в 6 месяцев' in insPart)
    check('C4: запись года в группе (дата %s)' % fmt_ru(OT_DATE),
          ('ws-il-row' in insPart) and (fmt_ru(OT_DATE) in insPart))
    check('C5: «след. срок: %s ✓» (актуально)' % fmt_ru(OT_DUE),
          ('след. срок: ' + fmt_ru(OT_DUE) + ' ✓') in insPart)
    check('C6: «Электробезопасность» — «⚠ просрочено с %s»' % fmt_ru(EB_DUE),
          ('⚠ просрочено с ' + fmt_ru(EB_DUE)) in insPart)
    check('C7: попап компактный — БЕЗ «— в этом году не проводился» (группа ЭБ видна строкой просрочки)',
          '— в этом году не проводился' not in insPart and 'Электробезопасность' in insPart)
    check('C8: пустой пункт скрыт (Пожарной безопасности нет в попапе)',
          'Пожарная безопасность' not in insPart)
    check('C9: «вне списка:» + «Экзамен · %s»' % fmt_ru(EX_DATE),
          ('вне списка:' in insPart) and
          (('Экзамен · ' + fmt_ru(EX_DATE)) in insPart))
    iCi = insPart.find('Целевой инструктаж')
    segCi = insPart[iCi:insPart.find('ws-il-off', iCi)] if iCi != -1 else ''
    check('C10: «Целевой инструктаж» — запись, БЕЗ срока (разовый)',
          iCi != -1 and ('след. срок' not in segCi) and ('просрочено' not in segCi))
    check('C11: обучение «Пожарная безопасность» НЕ в инструктажах (тип важнее имени)',
          'Пожарная безопасность' not in insPart and
          'Пожарная безопасность' in card[:iIns])
    check('C12: в попапе НЕТ секции СИЗ (регресс Task 403)', 'СИЗ' not in card)
    check('C13: секция «Мероприятия · %d» жива (регресс 405)' % Y,
          ('Мероприятия · %d' % Y) in card and 'Перенос по приказу' in card)
    page.screenshot(path='task407-proof-grid-dark.png', full_page=False)
    page.keyboard.press('Escape')
    page.wait_for_timeout(400)
    check('D1: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, edit ==========
    print('=== Контекст 2: десктоп светлая — карточка: группы + datalist ===')
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
            var heads = [];
            var cards = cols[ci].querySelectorAll('.ws-wcard');
            for (var hi = 0; hi < cards.length; hi++) {
                var t = cards[hi].querySelector('.ws-whead-t');
                heads.push(t ? t.textContent.trim() : '');
            }
            out.push({ n: cards.length, heads: heads,
                       x: cols[ci].getBoundingClientRect().left });
        }
        return out;
    })()""")
    check('E0: карточка — 3 колонки (регресс 406)',
          cols and len(cols) == 3 and cols[0]['n'] == 3 and cols[1]['n'] == 1 and
          cols[2]['n'] == 1 and cols[1]['heads'][0].startswith('Повторные инструктажи') and
          cols[2]['heads'][0].startswith('СИЗ ·'),
          cols and [c['heads'] for c in cols])
    insb = page.evaluate(instr_html_js('.ws-wgrid2'))
    check('F1: блок b5 — ЧЕТЫРЕ группы шаблона (ws-il-head)',
          insb.count('ws-il-head') == 4, insb.count('ws-il-head'))
    check('F2: «Пожарная безопасность» — «— не проводился» (карточка)',
          '— не проводился' in insb and
          insb.find('Пожарная безопасность') < insb.find('— не проводился'))
    check('F3: «Электробезопасность» — просрочено + не в этом году',
          ('⚠ просрочено с ' + fmt_ru(EB_DUE)) in insb and
          '— в этом году не проводился' in insb)
    check('F4: «Охрана труда» — след. срок ✓',
          ('след. срок: ' + fmt_ru(OT_DUE) + ' ✓') in insb)
    check('F5: «вне списка:» + Экзамен', 'вне списка:' in insb and 'Экзамен' in insb)
    nRows = page.evaluate("""(function(){
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var i = 0; i < cards.length; i++) {
            var t = cards[i].querySelector('.ws-whead-t');
            if (t && t.textContent.indexOf('Повторные инструктажи') !== -1) {
                return { rows: cards[i].querySelectorAll('.ws-popup-event').length,
                         inGroups: cards[i].querySelectorAll('.ws-il-row').length,
                         acts: cards[i].querySelectorAll('.ws-popup-act').length,
                         btn: (cards[i].querySelector('.ws-whead-a .ws-wbtn') || {})
                              .textContent || '' };
            }
        }
        return null;
    })()""")
    check('G1: 3 годовые записи (2 в группах + 1 «вне списка»)',
          nRows and nRows['rows'] == 3 and nRows['inGroups'] == 2, nRows)
    check('G2: ✎/✕ — 6 кнопок (3 × 2)', nRows and nRows['acts'] == 6, nRows)
    check('G3: кнопка «+ Инструктаж…»', nRows and nRows['btn'] == '+ Инструктаж…', nRows)
    page.screenshot(path='task407-proof-workers-light.png', full_page=False)
    # datalist подсказок «Темы» (Task 407)
    page.click('.ws-wgrid2 .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    tip = page.evaluate("document.getElementById('wsTrType').value")
    check('H1: «+ Инструктаж…» → тип «инструктаж»', tip == 'инструктаж', repr(tip))
    opts = page.evaluate("""(function(){
        var dl = document.getElementById('wsTrTitleList');
        if (!dl) return null;
        var v = [];
        for (var i = 0; i < dl.options.length; i++) v.push(dl.options[i].value);
        return v;
    })()""")
    check('H2: datalist: 3 названия вида «инструктаж»',
          opts is not None and len(opts) == 3 and 'Охрана труда' in opts and
          'Пожарная безопасность' in opts and 'Целевой инструктаж' in opts,
          opts)
    check('H3: datalist: «Электробезопасность» (ПЗ) НЕ предложена',
          opts is not None and 'Электробезопасность' not in opts, opts)
    page.select_option('#wsTrType', 'проверка_знаний')
    page.wait_for_timeout(400)
    opts2 = page.evaluate("""(function(){
        var dl = document.getElementById('wsTrTitleList');
        var v = [];
        for (var i = 0; i < dl.options.length; i++) v.push(dl.options[i].value);
        return v;
    })()""")
    check('H4: смена типа на ПЗ → datalist: только «Электробезопасность»',
          opts2 == ['Электробезопасность'], opts2)
    page.select_option('#wsTrType', 'обучение')
    page.wait_for_timeout(400)
    opts3 = page.evaluate("""(function(){
        var dl = document.getElementById('wsTrTitleList');
        return dl ? dl.options.length : -1;
    })()""")
    check('H5: тип «обучение» → datalist пуст (свободная тема)',
          opts3 == 0, opts3)
    page.screenshot(path='task407-proof-instr-form.png', full_page=False)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    # сводная «Общая» — регресс 405/406
    page.click(".ws-wtabs button:has-text('Общая')")
    page.wait_for_timeout(900)
    gen = page.evaluate("(function(){var t=document.querySelector('.ws-wgen-table');" +
                        "return t?t.innerHTML:'';})()")
    check('I1: сводная — колонки «Мероприятия · %d» и «Инструктажи · %d»' % (Y, Y),
          ('<th>Мероприятия · %d</th>' % Y) in gen and
          ('<th>Инструктажи · %d</th>' % Y) in gen)
    iIv = gen.find('Иванов И. И.')
    ivRow = gen[iIv:gen.find('</tr>', iIv)] if iIv != -1 else ''
    check('I2: Иванов: 2 мероприятия / 3 инструктажа (плоский счёт)',
          ivRow.rstrip().endswith('<td>2</td><td>3</td>'), ivRow[-60:])
    check('J: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, view ==========
    print('=== Контекст 3: мобайл 375 светлая — стек + группы блока ===')
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
    insm = page.evaluate(instr_html_js('.ws-wgrid2'))
    check('K2: группы шаблона на мобайле (4 шапки + вне списка)',
          insm.count('ws-il-head') == 4 and 'вне списка:' in insm,
          insm.count('ws-il-head'))
    page.screenshot(path='task407-proof-mobile.png', full_page=False)
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
            path='task407-proof-instr-block-mobile.png')
        check('K3: element-скрин блока снят', True)
    else:
        check('K3: element-скрин блока снят', False, el)
    check('K4: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
