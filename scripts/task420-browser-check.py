#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 420: browser-check — заявка «я сделал отметку о выполнении
# общего инструктажа, а создалась только одна новая запись о
# следующем общем инструктаже (должна появиться запись о 9-ОГЭ
# через три месяца».
# КОРЕНЬ: встроенная связь 9-ОГЭ → общий требовала ТОЧНОГО
# совпадения названий с эталоном; фактические названия листа
# пользователя отличаются → детей не находилось.
# ПРОВЕРКИ (мок-сервер, порт 8921; живой лист с именами
# пользователя БЕЗ столбца «в составе» — связь строит КЛИЕНТ):
#   1) десктоп 1280 тёмная, edit:
#      • «след. срок» 9-ОГЭ — от ПОСЛЕДНЕГО события (общий) = +3 мес
#        (клиентская связь по сигнатурам — Task 420);
#      • клик галочки общего → API setTrainingDone; ответ created:
#        9-ОГЭ +3 мес И общий +6 мес; покрытие старого 9-ОГЭ;
#      • НОВАЯ запись 9-ОГЭ в блоке карточки; общий +6 в пуле;
#      • клик галочки НОВОЙ записи 9-ОГЭ → created ПУСТОЙ (общий
#        +6 уже в окне — чередование 3/6, дублей нет);
#      • снятие отметки; ✎ жив (регресс 417); кэш-путь;
#      • ВТОРОЙ работник: отметка САМОСТОЯТЕЛЬНОГО 9-ОГЭ (общего
#        в окне нет) → created: ОБЩИЙ +3 мес (ЦИКЛ «по кругу»,
#        серверное правило 0) — запись в карточке и пуле;
#   2) десктоп 1280 светлая, view: состояния некликабельны;
#   3) мобайл 375 тёмная, edit: галочка >=22px, тап → API + UI.
import calendar
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8921
TODAY = datetime.date.today()
Y = TODAY.year


def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)


def add_months(dt, n):
    m = dt.month - 1 + n
    y = dt.year + m // 12
    m = m % 12 + 1
    dim = calendar.monthrange(y, m)[1]
    return datetime.date(y, m, min(dt.day, dim))


def ru(iso):
    p = iso.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]


# общий инструктаж — 10 дней назад (внутри текущего года)
past_dt = TODAY - datetime.timedelta(days=10)
if past_dt.year != Y:
    past_dt = datetime.date(Y, 1, 15)
PAST_OT = d(past_dt.year, past_dt.month, past_dt.day)
# старый самостоятельный 9-ОГЭ — 6 мес до общего (давно просрочен)
stale_dt = add_months(past_dt, -6)
STALE_OGE = d(stale_dt.year, stale_dt.month, stale_dt.day)
# новые сроки: +3 мес (9-ОГЭ) и +6 мес (общий) от даты общего
oge_next = add_months(past_dt, 3)
ot_next = add_months(past_dt, 6)
OGE_NEXT = d(oge_next.year, oge_next.month, oge_next.day)
OT_NEXT = d(ot_next.year, ot_next.month, ot_next.day)
# наивный срок старого 9-ОГЭ (без учёта родителя) — прошёл
stale_due = add_months(stale_dt, 3)
STALE_DUE = d(stale_due.year, stale_due.month, stale_due.day)
TODAY_ISO = d(TODAY.year, TODAY.month, TODAY.day)
future_dt = TODAY + datetime.timedelta(days=30)
FUTURE = d(future_dt.year, future_dt.month, future_dt.day)

# ВТОРОЙ работник — сценарий ЦИКЛА: самостоятельный 9-ОГЭ месяц
# назад, общего в окне НЕТ → отметка создаёт ОБЩИЙ +3 мес
solo_dt = add_months(TODAY, -1)
SOLO_OGE = d(solo_dt.year, solo_dt.month, solo_dt.day)
solo_next = add_months(solo_dt, 3)
SOLO_OT_NEXT = d(solo_next.year, solo_next.month, solo_next.day)

# ФАКТИЧЕСКИЕ названия пользователя (без «№», столбца «в составе» НЕТ)
U_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
U_OGE = 'Инструктаж по инструкции 9-ОГЭ'
N_EL = 'Периодическая проверка знаний до 1000 В'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '0872', 'ФИО': 'Тестов Б. Б.', 'тип': 'сменный', 'смена': 2,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2025-01-10', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 4 разряд', 'группа_допуска': 'III', 'комментарий': ''},
]

# записи листа «Инструктажи» (формат done):
#   600 — старый самостоятельный 9-ОГЭ (6 мес назад), отметки нет
#   601 — общий инструктаж (10 дней назад), отметки нет
#   602 — будущая проверка знаний до 1000 В
#   610 — самостоятельный 9-ОГЭ второго работника (месяц назад)
INSTR_ALL = [
  {'id': 600, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': U_OGE,
   'дата_начала': STALE_OGE, 'дата_окончания': STALE_OGE, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': STALE_OGE, 'выполнение': 0, 'просрочен': 1},
  {'id': 601, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': U_OT,
   'дата_начала': PAST_OT, 'дата_окончания': PAST_OT, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': PAST_OT, 'выполнение': 0, 'просрочен': 1},
  {'id': 602, 'таб_номер': '0871', 'тип': 'проверка_знаний', 'тема': N_EL,
   'дата_начала': FUTURE, 'дата_окончания': FUTURE, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': FUTURE, 'выполнение': 0, 'просрочен': 0},
  {'id': 610, 'таб_номер': '0872', 'тип': 'инструктаж', 'тема': U_OGE,
   'дата_начала': SOLO_OGE, 'дата_окончания': SOLO_OGE, 'длительность_дней': 1,
   'комментарий': '', 'дата_проведения': SOLO_OGE, 'выполнение': 0, 'просрочен': 1},
]

# автосозданные (новый сервер): 9-ОГЭ +3 мес (604), общий +6 (605),
# и ЦИКЛ для второго работника: общий +3 от 9-ОГЭ (611)
CREATED_OGE = {'id': 604, 'таб_номер': '0871', 'тип': 'инструктаж',
               'тема': U_OGE, 'дата_начала': OGE_NEXT, 'дата_окончания': OGE_NEXT,
               'длительность_дней': 1, 'комментарий': '',
               'дата_проведения': OGE_NEXT, 'выполнение': 0, 'просрочен': 0}
CREATED_OT = {'id': 605, 'таб_номер': '0871', 'тип': 'инструктаж',
              'тема': U_OT, 'дата_начала': OT_NEXT, 'дата_окончания': OT_NEXT,
              'длительность_дней': 1, 'комментарий': '',
              'дата_проведения': OT_NEXT, 'выполнение': 0, 'просрочен': 0}
CREATED_CYCLE_OT = {'id': 611, 'таб_номер': '0872', 'тип': 'инструктаж',
                    'тема': U_OT, 'дата_начала': SOLO_OT_NEXT,
                    'дата_окончания': SOLO_OT_NEXT, 'длительность_днев': 1,
                    'длительность_дней': 1, 'комментарий': '',
                    'дата_проведения': SOLO_OT_NEXT, 'выполнение': 0,
                    'просрочен': 0}

EVENTS_ALL = []
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
# ЖИВОЙ список с именами пользователя; «в составе» НЕТ (Task 420:
# клиент строит связь сам — сигнатуры «9огэ»/«рабочиминструкциям»)
INSTR_LIST = [
  {'название': U_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': 'Инстр. ОТ'},
  {'название': U_OGE, 'вид': 'инструктаж', 'периодичность': 3,
   'основание': '', 'сокращение': '9-ОГЭ'},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': 'ПЗ до 1000 В'},
]

DONE_CALLS = []
AUTOCREATED = False    # 604/605 добавлены в мок-лист
CYCLE_CREATED = False  # 611 добавлен

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
    global AUTOCREATED, CYCLE_CREATED
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
        # свежие копии (урок Task 418)
        return {'ok': True, 'data': {'trainings': [dict(r) for r in INSTR_ALL],
                                    'instrList': [dict(x) for x in INSTR_LIST],
                                    'instrAll': [dict(r) for r in INSTR_ALL],
                                    'eventsAll': [dict(r) for r in EVENTS_ALL]}}
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
        rec = None
        for r in INSTR_ALL:
            if r['id'] == rid:
                rec = r
                break
        if not rec:
            return {'ok': False, 'error': 'not_found'}
        rec['выполнение'] = val
        rec['просрочен'] = 0 if val == 1 else (
            1 if rec['дата_начала'] < TODAY_ISO else 0)
        created = []
        updated = []
        # ЗАЯВКА 420: отметка ОБЩЕГО (601) → 9-ОГЭ +3 И общий +6
        # (нестрогая связь нашла ребёнка по именам пользователя) +
        # покрытие старого 9-ОГЭ
        if val == 1 and rid == 601:
            r600 = None
            for r in INSTR_ALL:
                if r['id'] == 600:
                    r600 = r
                    break
            if r600 and r600['выполнение'] == 0:
                r600['выполнение'] = 1
                r600['просрочен'] = 0
                updated.append({'id': 600, 'выполнение': 1, 'просрочен': 0})
            created = [dict(CREATED_OGE), dict(CREATED_OT)]
            if not AUTOCREATED:
                INSTR_ALL.append(dict(CREATED_OGE))
                INSTR_ALL.append(dict(CREATED_OT))
                AUTOCREATED = True
        # ЦИКЛ (Task 420): отметка НОВОЙ записи 9-ОГЭ (604) —
        # общий +6 (605) уже в окне → ничего (чередование, без дублей)
        if val == 1 and rid == 604:
            created = []
        # ЦИКЛ (Task 420): отметка САМОСТОЯТЕЛЬНОГО 9-ОГЭ второго
        # работника (610, общего в окне нет) → ОБЩИЙ +3 мес
        if val == 1 and rid == 610:
            created = [dict(CREATED_CYCLE_OT)]
            if not CYCLE_CREATED:
                INSTR_ALL.append(dict(CREATED_CYCLE_OT))
                CYCLE_CREATED = True
        return {'ok': True, 'data': {'id': rid,
                'выполнение': rec['выполнение'],
                'просрочен': rec['просрочен'],
                'created': created, 'updated': updated}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t420-%s');" % tag +
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
                      body='not found (t420-%s)' % tag)
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


# ВСЕ строки блока «Повторные инструктажи…» карточки по части темы
ROWS_STATE_JS = """(function(themePart){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var rows = cards[i].querySelectorAll('.ws-popup-row.ws-popup-event');
            var out = [];
            for (var r = 0; r < rows.length; r++) {
                if (rows[r].innerText.indexOf(themePart) !== -1) {
                    var chk = rows[r].querySelector('.ws-done-chk');
                    var late = rows[r].querySelector('.ws-late-tag');
                    out.push({
                        late: !!late,
                        chk: !!chk,
                        chkOn: !!(chk && chk.classList.contains('ws-done-on')),
                        chkRo: !!(chk && chk.classList.contains('ws-done-ro')),
                        chkTitle: chk ? (chk.getAttribute('title') || '') : '',
                        chkClickable: !!(chk && chk.getAttribute('onclick')),
                        rowDone: rows[r].classList.contains('ws-row-done'),
                        text: rows[r].innerText
                    });
                }
            }
            return out;
        }
    }
    return [];
})"""


def rows_state(page, theme_part):
    return page.evaluate('(' + ROWS_STATE_JS + ')("%s")' % theme_part)


def first_row(page, theme_part):
    rows = rows_state(page, theme_part)
    return rows[0] if rows else {}


def click_chk(page, theme_part, idx=0):
    return page.evaluate("""(function(themePart, idx){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var rows = cards[i].querySelectorAll('.ws-popup-row.ws-popup-event');
            var seen = 0;
            for (var r = 0; r < rows.length; r++) {
                if (rows[r].innerText.indexOf(themePart) !== -1) {
                    if (seen++ < idx) continue;
                    var chk = rows[r].querySelector('.ws-done-chk');
                    if (chk) { chk.click(); return 'clicked'; }
                    return 'no-chk';
                }
            }
            return 'no-row';
        }
    }
    return 'no-block';
})""" + '("%s", %d)' % (theme_part, idx))


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    print('=== Контекст 1: десктоп тёмная edit — заявка + цикл 9-ОГЭ ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'main')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    open_workers_card(page)
    page.screenshot(path='task420-proof-card-initial.png', full_page=False)

    # --- ЗАЯВКА: клиент построил связь по именам пользователя ---
    link_state = page.evaluate("""(function(){
    var l = WorkSchedule._INSTR_LIST || [];
    var og = null, ot = null;
    l.forEach(function(x){
        if (x.название.indexOf('9-ОГЭ') !== -1) og = x;
        if (x.название.indexOf('рабочим инструкциям') !== -1) ot = x;
    });
    return {link: og ? (og['в составе'] || '') : 'нет пункта',
            otName: ot ? ot.название : ''};
})()""")
    check('B0: ЗАЯВКА — клиент построил связь 9-ОГЭ → общий (без столбца)',
          link_state['link'] == U_OT, link_state)

    # «след. срок» 9-ОГЭ — от ПОСЛЕДНЕГО события (общий) = +3 мес
    sec = page.evaluate(
        "WorkSchedule._renderInstrSection([], '0871', false, false,"
        " WorkSchedule._INSTR_LIST, %d)" % Y)
    i_oge = sec.find('9-ОГЭ')
    seg = sec[i_oge:sec.find('ws-il-head', i_oge + 10)] if i_oge != -1 else ''
    check('B1: ЗАЯВКА — срок 9-ОГЭ от общего (+3 мес): «след. срок: %s»'
          % ru(OGE_NEXT), ('след. срок: ' + ru(OGE_NEXT)) in seg, seg[:400])
    check('B2: ЗАЯВКА — наивная просрочка от старой записи НЕ показана',
          ('просрочено с ' + ru(STALE_DUE)) not in seg and
          STALE_DUE not in seg, seg[:400])

    # --- исходное состояние строк ---
    r600 = first_row(page, '9-ОГЭ')
    check('B3: старый 9-ОГЭ — бейдж «просрочен» + пустая галочка',
          r600.get('late') and r600.get('chk') and not r600.get('chkOn'), r600)
    r601 = first_row(page, 'рабочим инструкциям ОТ')
    check('B4: общий инструктаж — бейдж «просрочен» + пустая галочка',
          r601.get('late') and r601.get('chk') and not r601.get('chkOn'), r601)

    # --- клик по галочке ОБЩЕГО: автосоздание сроков заявки ---
    n_calls = len(DONE_CALLS)
    click_chk(page, 'рабочим инструкциям ОТ')
    page.wait_for_timeout(1000)
    check('C1: ЗАЯВКА — API setTrainingDone вызван (601, 0→1)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 601, 'выполнение': 1}, DONE_CALLS[n_calls:])
    r601b = first_row(page, 'рабочим инструкциям ОТ')
    check('C2: общий отмечен — галочка зелёная, бейдж ушёл',
          r601b.get('chkOn') and not r601b.get('late'), r601b)
    r600b = rows_state(page, '9-ОГЭ')[0]
    check('C3: ЗАЯВКА — покрытие: старый 9-ОГЭ отмечен (зелёная, приглушен)',
          r600b.get('chkOn') and r600b.get('rowDone'), r600b)
    body_txt = page.evaluate('document.body.innerText')
    check('C4: ЗАЯВКА — тост «новые сроки» с датой 9-ОГЭ (%s)'
          % ru(OGE_NEXT),
          'новые сроки' in body_txt and ru(OGE_NEXT) in body_txt, body_txt[-200:])
    page.screenshot(path='task420-proof-marked-done.png', full_page=False)

    # --- НОВЫЕ записи: 9-ОГЭ (+3) в блоке карточки, общий (+6) в пуле ---
    oge_rows = rows_state(page, '9-ОГЭ')
    new_oge = None
    for r in oge_rows:
        if ru(OGE_NEXT) in r.get('text', ''):
            new_oge = r
    check('D1: ЗАЯВКА — НОВАЯ запись 9-ОГЭ (%s) появилась в блоке карточки'
          % ru(OGE_NEXT), bool(new_oge), oge_rows)
    check('D2: новая запись — пустая галочка, без «просрочен»',
          bool(new_oge) and new_oge.get('chk') and not new_oge.get('chkOn')
          and not new_oge.get('late'), new_oge)
    pools = page.evaluate("""(function(){
    var ids = {};
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){ ids[r.id] = r.дата_начала; });
    var otCount = 0;
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){
        if (r.тема && r.тема.indexOf('рабочим инструкциям ОТ') !== -1) otCount++; });
    return {inAll604: !!ids[604], inAll605: !!ids[605],
            d604: ids[604] || '', d605: ids[605] || '', otCount: otCount,
            has606: !!ids[606]};
})()""")
    check('D3: ЗАЯВКА — общий +6 мес (%s) в пуле _INSTR_ALL' % ru(OT_NEXT),
          pools['inAll605'] and pools['d605'] == OT_NEXT, pools)
    check('D4: 9-ОГЭ +3 мес в пуле _INSTR_ALL', pools['inAll604'] and
          pools['d604'] == OGE_NEXT, pools)
    check('D5: дублей общего нет (601 + 605, без 606)',
          pools['otCount'] == 2 and not pools['has606'], pools)

    # --- клик галочки НОВОЙ записи 9-ОГЭ: цикл закрыт общим +6 ---
    n_calls = len(DONE_CALLS)
    res_click = click_chk(page, '9-ОГЭ', idx=1)
    page.wait_for_timeout(900)
    check('E1: клик по галочке НОВОЙ записи 9-ОГЭ → API (604, 1)',
          res_click == 'clicked' and len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 604, 'выполнение': 1},
          (res_click, DONE_CALLS[n_calls:]))
    oge_rows2 = rows_state(page, '9-ОГЭ')
    new_oge2 = None
    for r in oge_rows2:
        if ru(OGE_NEXT) in r.get('text', ''):
            new_oge2 = r
    check('E2: новая запись отмечена — галочка зелёная',
          bool(new_oge2) and new_oge2.get('chkOn'), new_oge2)
    pools2 = page.evaluate("""(function(){
    var ot = 0, any606 = false;
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){
        if (r.тема && r.тема.indexOf('рабочим инструкциям ОТ') !== -1) ot++;
        if (r.id === 606) any606 = true; });
    return {otCount: ot, any606: any606};
})()""")
    check('E3: ЦИКЛ — общий +6 уже в окне: дублей НЕ появилось (created пуст)',
          pools2['otCount'] == 2 and not pools2['any606'], pools2)
    # снятие отметки новой записи
    click_chk(page, '9-ОГЭ', idx=1)
    page.wait_for_timeout(900)
    check('E4: снятие отметки новой записи → API (604, 0)',
          DONE_CALLS[-1] == {'id': 604, 'выполнение': 0}, DONE_CALLS[-2:])
    oge_rows3 = rows_state(page, '9-ОГЭ')
    new_oge3 = None
    for r in oge_rows3:
        if ru(OGE_NEXT) in r.get('text', ''):
            new_oge3 = r
    check('E5: после снятия — галочка пустая (запись осталась)',
          bool(new_oge3) and not new_oge3.get('chkOn'), new_oge3)

    # --- ВТОРОЙ РАБОТНИК: ЦИКЛ — отметка 9-ОГЭ без общего в окне ---
    page.click(".ws-wtabs button:has-text('Тестов Б. Б.')")
    page.wait_for_timeout(900)
    r610 = first_row(page, '9-ОГЭ')
    check('F1: ЦИКЛ — самостоятельный 9-ОГЭ Тестова: просрочен, без отметки',
          r610.get('late') and r610.get('chk') and not r610.get('chkOn'), r610)
    n_calls = len(DONE_CALLS)
    click_chk(page, '9-ОГЭ')
    page.wait_for_timeout(1000)
    check('F2: ЦИКЛ — клик → API (610, 1)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 610, 'выполнение': 1}, DONE_CALLS[n_calls:])
    body_txt2 = page.evaluate('document.body.innerText')
    check('F3: ЦИКЛ — тост «новые сроки» с датой общего (%s)'
          % ru(SOLO_OT_NEXT),
          'новые сроки' in body_txt2 and ru(SOLO_OT_NEXT) in body_txt2,
          body_txt2[-300:])
    ot_rows = rows_state(page, 'рабочим инструкциям ОТ')
    new_ot = None
    for r in ot_rows:
        if ru(SOLO_OT_NEXT) in r.get('text', ''):
            new_ot = r
    check('F4: ЦИКЛ — запись ОБЩИЙ +3 мес (%s) появилась в карточке Тестова'
          % ru(SOLO_OT_NEXT), bool(new_ot), ot_rows)
    check('F5: ЦИКЛ — новая запись общего без отметки и «просрочен»',
          bool(new_ot) and new_ot.get('chk') and not new_ot.get('chkOn')
          and not new_ot.get('late'), new_ot)
    pools3 = page.evaluate("""(function(){
    var r611 = null;
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){
        if (r.id === 611) r611 = r; });
    return r611 ? {tab: r611['таб_номер'], tema: r611.тема,
                   date: r611.дата_проведения || r611.дата_начала} : null;
})()""")
    check('F6: ЦИКЛ — запись 611 в пуле: общий для 0872 на %s'
          % ru(SOLO_OT_NEXT),
          pools3 and pools3['tab'] == '0872' and
          pools3['tema'] == U_OT and pools3['date'] == SOLO_OT_NEXT, pools3)
    page.screenshot(path='task420-proof-cycle-rule.png', full_page=False)

    # возврат к Федосову — ✎ жив (регресс 417)
    page.click(".ws-wtabs button:has-text('Федосов А. В.')")
    page.wait_for_timeout(900)
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
    check('G1: регресс — правка записи открывает форму',
          click_edit == 'clicked' and form['open'] and
          form['title'] == 'Правка инструктажа / проверки знаний',
          (click_edit, form))
    page.evaluate("WorkSchedule.closeTrainingForm && WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # --- кэш-путь: перезагрузка — состояние из данных ---
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Федосов А. В.')")
    page.wait_for_timeout(900)
    r601c = first_row(page, 'рабочим инструкциям ОТ')
    check('H1: кэш-путь — общий отмечен (зелёная)',
          r601c.get('chkOn') and not r601c.get('late'), r601c)
    r600c = rows_state(page, '9-ОГЭ')[0]
    check('H2: кэш-путь — покрытие старого 9-ОГЭ сохранено',
          r600c.get('chkOn') and r600c.get('rowDone'), r600c)
    oge_rows_c = rows_state(page, '9-ОГЭ')
    new_oge_c = [r for r in oge_rows_c if ru(OGE_NEXT) in r.get('text', '')]
    check('H3: кэш-путь — новая запись 9-ОГЭ на месте',
          len(new_oge_c) == 1 and not new_oge_c[0].get('chkOn'), oge_rows_c)
    link2 = page.evaluate("""(function(){
    var og = null;
    (WorkSchedule._INSTR_LIST||[]).forEach(function(x){
        if (x.название.indexOf('9-ОГЭ') !== -1) og = x; });
    return og ? (og['в составе'] || '') : '';
})()""")
    check('H4: кэш-путь — клиентская связь 9-ОГЭ построена снова',
          link2 == U_OT, link2)
    check('H5: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'view')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    open_workers_card(page)
    rv601 = first_row(page, 'рабочим инструкциям ОТ')
    check('I1: view — отмеченный общий: галочка-состояние НЕкликабельна',
          rv601.get('chkOn') and rv601.get('chkRo') and not rv601.get('chkClickable'), rv601)
    check('I2: view — подсказка «Выполнено»',
          rv601.get('chkTitle') == 'Выполнено', rv601.get('chkTitle'))
    rv600 = rows_state(page, '9-ОГЭ')[0]
    check('I3: view — покрытый 9-ОГЭ: состояние, бейджа нет',
          rv600.get('chkOn') and rv600.get('chkRo') and not rv600.get('late'), rv600)
    oge_rows_v = rows_state(page, '9-ОГЭ')
    new_oge_v = None
    for r in oge_rows_v:
        if ru(OGE_NEXT) in r.get('text', ''):
            new_oge_v = r
    check('I4: view — новая запись 9-ОГЭ БЕЗ галочки (не выполнена)',
          bool(new_oge_v) and not new_oge_v.get('chk') and
          not new_oge_v.get('chkOn') and not new_oge_v.get('late'), new_oge_v)
    n2 = len(DONE_CALLS)
    click_chk(page, 'рабочим инструкциям ОТ')
    page.wait_for_timeout(600)
    check('I5: view — клики по галочке API НЕ вызывают',
          len(DONE_CALLS) == n2, DONE_CALLS[n2:])
    page.screenshot(path='task420-proof-view-light.png', full_page=False)
    check('I6: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, тёмная, edit ==========
    print('=== Контекст 3: мобайл 375 тёмная edit ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mobile')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    open_workers_card(page)
    rm = first_row(page, 'до 1000 В')
    check('J1: мобайл — будущая ПЗ: пустая галочка, без «просрочен»',
          rm.get('chk') and not rm.get('chkOn') and not rm.get('late'), rm)
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
    check('J2: мобайл — галочка достаточного размера (>=22px)',
          size['w'] >= 22 and size['h'] >= 22, size)
    nm = len(DONE_CALLS)
    click_chk(page, 'до 1000 В')
    page.wait_for_timeout(2500)
    check('J3: мобайл — тап по галочке вызывает API (602, 1)',
          len(DONE_CALLS) == nm + 1 and
          DONE_CALLS[-1] == {'id': 602, 'выполнение': 1}, DONE_CALLS[nm:])
    rm2 = first_row(page, 'до 1000 В')
    check('J4: мобайл — галочка стала зелёной, бейджа нет',
          rm2.get('chkOn') and not rm2.get('late'), rm2)
    page.screenshot(path='task420-proof-mobile-toggle.png', full_page=False)
    check('J5: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
