#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 425: browser-check — заявка «мне не нужно объединять
# инструктажи и мероприятия, инструктажи менять не нужно, а для
# мероприятий нужно создать свои отдельные страницы, так же нужно
# проверить что бы они не влияли друг на друга в приложении:
# новые инструктажи формируются автоматически в зависимости от
# предыдущих, а мероприятия каждый раз вносятся вручную и без
# автоматического продления».
# Сервер: eventsInit (ТОЛЬКО лист «Мероприятия», «Инструктажи» не
# трогает) + стоп-правило автосоздания для мероприятых типов —
# покрыты юнит-тестами test-task424/425.js; здесь — НЕЗАВИСИМОСТЬ
# БЛОКОВ В ПРИЛОЖЕНИИ на мок-сервере (порт 8927):
#   1) десктоп 1280 тёмная, edit:
#      • блоки карточки раздельны: «Мероприятия · Y» (записи
#        архивных лет по стрелкам) и «Повторные инструктажи»;
#      • добавление мероприятий (обучение/прогул) → API
#        addTraining с верным типом, записи в СВОЁМ блоке;
#        блок инструктажей НЕ изменился (строк/тем);
#      • ГЛАВНАЯ НЕЗАВИСИМОСТЬ: отметка общего инструктажа 601 →
#        автосозданы ОБЕ записи (9-ОГЭ +3 мес, общий +6 мес)
#        в блоке/пуле ИНСТРУКТАЖЕЙ; блок «Мероприятия» и пул
#        _EVENTS_ALL НЕ изменились (мероприятия без продления —
#        вручную);
#      • фиксация созданного 9-ОГЭ (регресс 421) — ничего не
#        создано, мероприятия не тронуты;
#   2) десктоп 1280 светлая, view: записи видны, кнопок/галочек
#      нет (только просмотр);
#   3) мобайл 375 тёмная, edit: блок мероприятий, форма с select
#      РОВНО обучение/прогул/примечание.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8927
TODAY = datetime.date.today()
Y = TODAY.year
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)
PAST_OT = '%04d-%02d-%02d' % (TODAY.year, TODAY.month,
                              max(TODAY.day - 20, 1))
PAST_OGE = '%04d-%02d-%02d' % (TODAY.year, TODAY.month,
                                max(TODAY.day - 25, 1))

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def add_months(iso, m):
    p = [int(x) for x in iso.split('-')]
    y = p[0] + (p[1] - 1 + m) // 12
    mo = (p[1] - 1 + m) % 12 + 1
    dim = DAYS_IN_MONTH[mo - 1]
    if mo == 2 and y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
        dim = 29
    return '%04d-%02d-%02d' % (y, mo, min(p[2], dim))


OGE_NEXT = add_months(PAST_OT, 3)   # 9-ОГЭ +3 мес (эталон 423)
OT_NEXT = add_months(PAST_OT, 6)    # общий +6 мес


def ru(iso):
    p = str(iso).split('-')
    return p[2] + '.' + p[1] + '.' + p[0]


U_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
U_OGE = 'Повторный инструктаж по инструкции № 9-ОГЭ'
T_OB = 'Охрана труда (ежегодный курс)'
T_STAZH = 'Стажировка на стенде КИПиА'
T_PRG = 'Прогул (тест независимости)'

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
  {'название': U_OGE, 'вид': 'инструктаж', 'периодичность': 3,
   'основание': '', 'сокращение': '9-ОГЭ', 'в составе': U_OT},
]


def ev(i, tab, tip, tema, d1, d2=None, days=1):
    return {'id': i, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d1, 'дата_окончания': d2 or d1,
            'длительность_дней': days, 'комментарий': ''}


def fresh_events():
    return [
        ev(500, '0871', 'обучение', T_OB, '%04d-05-15' % (Y - 2)),
        ev(501, '0871', 'прогул', 'Прогул 2025', '%04d-06-10' % (Y - 1)),
        ev(502, '0871', 'примечание', 'Отстранение', '%04d-08-20' % (Y - 1)),
        ev(503, '0871', 'обучение', 'Курс АСУ ТП (базовый)', TODAY_ISO),
        ev(504, '0872', 'примечание', 'Справка медосмотра', TODAY_ISO),
    ]


def fresh_instr():
    return [
        {'id': 600, 'таб_номер': '0871', 'тип': 'инструктаж',
         'тема': U_OGE, 'дата_начала': PAST_OGE,
         'дата_окончания': PAST_OGE, 'длительность_дней': 1,
         'комментарий': '', 'дата_проведения': PAST_OGE,
         'выполнение': 0, 'просрочен': 1},
        {'id': 601, 'таб_номер': '0871', 'тип': 'инструктаж',
         'тема': U_OT, 'дата_начала': PAST_OT,
         'дата_окончания': PAST_OT, 'длительность_дней': 1,
         'комментарий': '', 'дата_проведения': PAST_OT,
         'выполнение': 0, 'просрочен': 1},
    ]


EVENTS = fresh_events()
INSTR = fresh_instr()
ADD_CALLS = []
DONE_CALLS = []
NEXT_ID = [700]
AUTOCREATED = False
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
CONSOLE_MSGS = []


def check(name, ok, info=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ✓ %s' % name)
    else:
        FAIL += 1
        print('  ✗ %s  → %s' % (name, info))


def reset_data():
    global EVENTS, INSTR, AUTOCREATED
    EVENTS = fresh_events()
    INSTR = fresh_instr()
    ADD_CALLS.clear()
    DONE_CALLS.clear()
    AUTOCREATED = False


def api_response(action, body):
    global AUTOCREATED
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
                 str((body or {}).get('дата_окончания') or ''))
        rec['длительность_дней'] = int(
            (body or {}).get('длительность_дней') or 1)
        if tip in ('обучение', 'прогул', 'примечание'):
            EVENTS.append(rec)      # маршрутизация: лист «Мероприятия»
        else:
            INSTR.append(rec)       # лист «Инструктажи»
        NEXT_ID[0] += 1
        return {'ok': True, 'data': {'id': rec['id']}}
    if action == 'workSchedule.setTrainingDone':
        # моксервера Task 425: srvVer '425', автосоздание — ТОЛЬКО
        # для инструктажей (правила 421/423); мероприятия (если бы
        # id события пришёл) — фиксация без создания
        rid = (body or {}).get('id')
        val = 1 if (body or {}).get('выполнение') == 1 else 0
        DONE_CALLS.append({'id': rid, 'выполнение': val})
        rec = None
        for r in INSTR:
            if r['id'] == rid:
                rec = r
                break
        if rec is None:
            # id мероприятия (блок «Мероприятия» галочек не имеет —
            # сюда попасть можно только напрямую): фиксация без
            # автосоздания (стоп-правило Task 425)
            return {'ok': True, 'data': {'id': rid, 'выполнение': val,
                    'просрочен': 0, 'srvVer': '425',
                    'autoNote': 'Task 425: мероприятие — автосоздания '
                               'нет (вносится вручную, без продления)',
                    'created': [], 'updated': [], 'skipped': []}}
        rec['выполнение'] = val
        rec['просрочен'] = 0 if val == 1 else (
            1 if rec['дата_начала'] < TODAY_ISO else 0)
        created = []
        updated = []
        skipped = []
        note = ('пункт=' + rec['тема'] + ' родитель=- дети=' + U_OGE +
                ' [' + '9-ОГЭ' + ' → ' + ru(OGE_NEXT) + ']')
        # 601 — общий Федосова: ОБЕ записи (9-ОГЭ +3 эталона 423,
        # общий +6) + покрытие старого 9-ОГЭ 600
        if val == 1 and rid == 601:
            r600 = None
            for r in INSTR:
                if r['id'] == 600:
                    r600 = r
                    break
            if r600 and r600['выполнение'] == 0:
                r600['выполнение'] = 1
                r600['просрочен'] = 0
                updated.append({'id': 600, 'выполнение': 1, 'просрочен': 0})
            if not AUTOCREATED:
                c1 = {'id': 604, 'таб_номер': '0871', 'тип': 'инструктаж',
                      'тема': U_OGE, 'дата_начала': OGE_NEXT,
                      'дата_окончания': OGE_NEXT, 'длительность_дней': 1,
                      'комментарий': '', 'дата_проведения': OGE_NEXT,
                      'выполнение': 0, 'просрочен': 0}
                c2 = {'id': 605, 'таб_номер': '0871', 'тип': 'инструктаж',
                      'тема': U_OT, 'дата_начала': OT_NEXT,
                      'дата_окончания': OT_NEXT, 'длительность_дней': 1,
                      'комментарий': '', 'дата_проведения': OT_NEXT,
                      'выполнение': 0, 'просрочен': 0}
                created = [dict(c1), dict(c2)]
                INSTR.append(dict(c1))
                INSTR.append(dict(c2))
                AUTOCREATED = True
            else:
                created = []
        # созданный 9-ОГЭ 604 / любой зависимый — фиксация (421)
        if val == 1 and rid in (604, 600):
            created = []
            note = ('пункт=' + U_OGE + ' родитель=' + U_OT + ' дети=-' +
                    '; Task 421: зависимый пункт — автосоздания нет')
        return {'ok': True, 'data': {'id': rid,
                'выполнение': rec['выполнение'],
                'просрочен': rec['просрочен'],
                'srvVer': '425',
                'autoNote': note,
                'created': created, 'updated': updated,
                'skipped': skipped}}
    if action == 'workSchedule.deleteTraining':
        rid = (body or {}).get('id')
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
    page.on('console', lambda m: CONSOLE_MSGS.append(m.text))
    pre = ''
    if not keep_cache:
        pre += ("try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
                "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};")
    ctx.add_init_script(
        pre +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t425-%s');" % tag +
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
                      body='not found (t425-%s)' % tag)
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


# карточный блок по заголовку: голова/строки/HTML
BLOCK_JS = """(function(headPart){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf(headPart) !== -1) {
            return {head: h.textContent,
                    rows: cards[i].querySelectorAll('.ws-popup-row').length,
                    html: cards[i].innerHTML,
                    btn: !!cards[i].querySelector('.ws-emp-addtr'),
                    acts: cards[i].querySelectorAll('.ws-popup-act').length};
        }
    }
    return null;
})"""


def block(page, head_part):
    return page.evaluate('(' + BLOCK_JS + ')("%s")' % head_part) or {}


CLICK_CHK_JS = """(function(themePart, idx){
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
})"""


def click_chk(page, theme_part, idx=0):
    return page.evaluate('(' + CLICK_CHK_JS + ')("%s", %d)'
                         % (theme_part, idx))


def toast_text(page):
    return page.evaluate(
        "(function(){var m = document.getElementById('toastMessage');"
        " return m ? m.textContent : '';})()")


def form_state(page):
    return page.evaluate("""(function(){
    var sh = document.getElementById('wsTrSheet');
    var sel = document.getElementById('wsTrType');
    var grp = document.getElementById('wsTrTypeGroup');
    var rect = sel ? sel.getBoundingClientRect() : null;
    var opts = sel ? Array.prototype.map.call(sel.options,
        function(o){return o.value;}) : null;
    return {open: !!(sh && sh.classList.contains('active')),
            title: (document.getElementById('wsTrSheetTitle')||{}).textContent,
            isSelect: !!(sel && sel.tagName === 'SELECT'),
            options: opts,
            typeVal: sel ? sel.value : null,
            tapH: rect ? Math.round(rect.height) : 0,
            emp: (document.getElementById('wsTrEmp')||{}).textContent};
})""")


def submit_event(page, tip, tema):
    page.select_option('#wsTrType', tip)
    page.fill('#wsTrTitle', tema)
    page.click('#wsTrSubmitBtn')
    page.wait_for_timeout(1800)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ===== Контекст 1: десктоп 1280, тёмная, edit =====
    print('=== Контекст 1: десктоп тёмная edit — независимость блоков ===')
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
    page.screenshot(path='task425-proof-card-initial.png', full_page=False)
    evb = block(page, 'Мероприятия')
    inb = block(page, 'Повторные инструктажи')
    check('B1: блок «Мероприятия · %d» с записью года' % Y,
          ('Мероприятия · %d' % Y) in evb.get('head', '') and
          'Курс АСУ ТП' in evb.get('html', ''), evb.get('head', ''))
    check('B2: блок «Повторные инструктажи…» — общий 601 с пустой галочкой',
          'Повторные инструктажи' in (inb.get('head', '') or
                                      block(page, 'Повторные').get('head', '')) and
          'рабочим инструкциям ОТ' in (inb.get('html', '') or ''),
          inb.get('head', ''))
    check('B3: блоки раздельны — темы инструктажей НЕ в мероприятиях',
          U_OT not in evb.get('html', ''))
    ev_rows_0 = evb.get('rows', 0)
    check('B4: в блоке мероприятий %d строк, кнопка «+ Мероприятие…»'
          % ev_rows_0, ev_rows_0 >= 1 and evb.get('btn'), evb)

    # --- добавление мероприятия: обучение → ТОЛЬКО свой блок ---
    page.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page.wait_for_timeout(700)
    fs = form_state(page)
    check('C1: форма «Новое мероприятие», select РОВНО '
          '[обучение, прогул, примечание]',
          fs['open'] and fs['title'] == 'Новое мероприятие' and
          fs['options'] == ['обучение', 'прогул', 'примечание'], fs)
    submit_event(page, 'обучение', T_STAZH)
    check('C2: API addTraining — тип=обучение',
          ADD_CALLS and ADD_CALLS[-1]['тип'] == 'обучение' and
          ADD_CALLS[-1]['таб_номер'] == '0871', ADD_CALLS[-1:])
    tt = toast_text(page)
    check('C3: тост «Мероприятие добавлено»', 'добавлено' in tt.lower(), tt)
    page.evaluate("WorkSchedule.selectWorkersTab('0871')")
    page.wait_for_timeout(900)
    evb1 = block(page, 'Мероприятия')
    inb1 = block(page, 'Повторные инструктажи')
    check('C4: запись «%s» появилась в СВОЁМ блоке (+1 строка)'
          % T_STAZH,
          T_STAZH in evb1.get('html', '') and
          evb1.get('rows', 0) == ev_rows_0 + 1,
          (ev_rows_0, evb1.get('rows')))
    check('C5: НЕЗАВИСИМОСТЬ: блок инструктажей НЕ изменился '
          '(строк столько же, темы мероприятий НЕ там)',
          inb1.get('rows', 0) == inb.get('rows', 0) and
          T_STAZH not in inb1.get('html', ''),
          (inb.get('rows'), inb1.get('rows')))
    ev_rows_1 = evb1.get('rows', 0)

    # --- ГЛАВНАЯ НЕЗАВИСИМОСТЬ: отметка общего — мероприятия не тронуты ---
    n_calls = len(DONE_CALLS)
    n_logs = len(CONSOLE_MSGS)
    click_chk(page, 'рабочим инструкциям ОТ')
    page.wait_for_timeout(1400)
    check('D1: API setTrainingDone вызван (601, 0→1)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 601, 'выполнение': 1}, DONE_CALLS[n_calls:])
    tt = toast_text(page)
    check('D2: автосоздание ИНСТРУКТАЖЕЙ живо — тост «новые сроки: '
          '%s, %s» (ОБЕ записи)' % (ru(OGE_NEXT), ru(OT_NEXT)),
          'новые сроки' in tt and ru(OGE_NEXT) in tt and
          ru(OT_NEXT) in tt, tt)
    check('D3: srvVer 425 — предупреждения о старой версии НЕТ',
          'старой версии' not in tt, tt)
    page.screenshot(path='task425-proof-instr-marked.png', full_page=False)

    evb2 = block(page, 'Мероприятия')
    inb2 = block(page, 'Повторные инструктажи')
    check('D4: ГЛАВНАЯ НЕЗАВИСИМОСТЬ — блок «Мероприятия» НЕ изменился '
          '(строк по-прежнему %d, новых сроков там НЕТ)'
          % ev_rows_1,
          evb2.get('rows', 0) == ev_rows_1 and
          ru(OGE_NEXT) not in evb2.get('html', '') and
          ru(OT_NEXT) not in evb2.get('html', ''),
          (ev_rows_1, evb2.get('rows')))
    check('D5: созданные записи — в блоке ИНСТРУКТАЖЕЙ (9-ОГЭ %s)'
          % ru(OGE_NEXT),
          ru(OGE_NEXT) in inb2.get('html', '') and
          inb2.get('rows', 0) > inb1.get('rows', 0),
          (inb1.get('rows'), inb2.get('rows')))

    pools = page.evaluate("""(function(){
    var ids = {};
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){ ids[r.id] = r.дата_начала; });
    var evIds = {};
    (WorkSchedule._EVENTS_ALL||[]).forEach(function(r){ evIds[r.id] = true; });
    return {inAll604: !!ids[604], d604: ids[604] || '',
            inAll605: !!ids[605], d605: ids[605] || '',
            instrTotal: (WorkSchedule._INSTR_ALL||[]).length,
            evTotal: (WorkSchedule._EVENTS_ALL||[]).length,
            evHas604: !!evIds[604], evHas605: !!evIds[605],
            evTotalNow: (WorkSchedule._EVENTS_ALL||[]).length};
})()""")
    check('D6: пул _INSTR_ALL: 9-ОГЭ 604 (%s) и общий 605 (%s)'
          % (OGE_NEXT, OT_NEXT),
          pools['inAll604'] and pools['d604'] == OGE_NEXT and
          pools['inAll605'] and pools['d605'] == OT_NEXT, pools)
    check('D7: ГЛАВНАЯ — пул _EVENTS_ALL НЕ тронут автосозданием '
          '(604/605 НЕ мероприятия, %d записей — 5 исходных + стажировка)'
          % len(EVENTS),
          not pools['evHas604'] and not pools['evHas605'] and
          pools['evTotal'] == len(EVENTS), pools)

    logged = [m for m in CONSOLE_MSGS[n_logs:]
              if '[инструктажи] автосоздание:' in m]
    check('D8: autoNote автосоздания — в консоли (F12)', len(logged) >= 1,
          CONSOLE_MSGS[n_logs:][:5])

    # --- второе мероприятие: прогул → тоже только свой блок ---
    page.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page.wait_for_timeout(700)
    submit_event(page, 'прогул', T_PRG)
    check('E1: API addTraining — тип=прогул',
          ADD_CALLS and ADD_CALLS[-1]['тип'] == 'прогул', ADD_CALLS[-1:])
    page.evaluate("WorkSchedule.selectWorkersTab('0871')")
    page.wait_for_timeout(900)
    evb3 = block(page, 'Мероприятия')
    inb3 = block(page, 'Повторные инструктажи')
    page.screenshot(path='task425-proof-events-added.png', full_page=False)
    check('E2: прогул в блоке мероприятий (+1), инструктажи НЕ тронуты',
          T_PRG in evb3.get('html', '') and
          evb3.get('rows', 0) == ev_rows_1 + 1 and
          inb3.get('rows', 0) == inb2.get('rows', 0),
          (ev_rows_1, evb3.get('rows'), inb2.get('rows'), inb3.get('rows')))

    # --- фиксация созданного 9-ОГЭ (регресс 421): ничего не создаётся ---
    n_calls = len(DONE_CALLS)
    res_click = click_chk(page, '9-ОГЭ', idx=1)
    page.wait_for_timeout(1000)
    tt2 = toast_text(page)
    pools2 = page.evaluate(
        "(function(){return {i: (WorkSchedule._INSTR_ALL||[]).length,"
        " e: (WorkSchedule._EVENTS_ALL||[]).length};})()")
    check('F1: клик НОВОЙ 9-ОГЭ 604 → API (фиксация, регресс 421)',
          res_click == 'clicked' and len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 604, 'выполнение': 1},
          (res_click, DONE_CALLS[n_calls:]))
    check('F2: тост РОВНО «Отмечено выполнение» — ничего не создано',
          tt2 == 'Отмечено выполнение', tt2)
    check('F3: пулы не выросли от фиксации (инструктажи %d; '
          'мероприятия %d = +прогул из E, без новых)'
          % (pools['instrTotal'], pools['evTotal'] + 1),
          pools2['i'] == pools['instrTotal'] and
          pools2['e'] == pools['evTotal'] + 1, (pools, pools2))

    check('G1: 0 JS-ошибок', not js_errors, js_errors[:5])
    ctx.close()

    # ===== Контекст 2: десктоп 1280, светлая, view =====
    print('=== Контекст 2: десктоп светлая view — только просмотр ===')
    ADMIN = False
    reset_data()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'view')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_workers_card(page)
    page.screenshot(path='task425-proof-view-light.png', full_page=False)
    evb = block(page, 'Мероприятия')
    inb = block(page, 'Повторные инструктажи')
    check('H1: записи мероприятий видны (view)',
          'Курс АСУ ТП' in evb.get('html', ''), evb.get('head', ''))
    check('H2: кнопок «+»/✎/✕ НЕТ в обоих блоках',
          not evb.get('btn') and evb.get('acts', 0) == 0 and
          not inb.get('btn'), (evb.get('btn'), evb.get('acts'),
                               inb.get('btn')))
    no_click = page.evaluate(
        "(function(){var cards = document.querySelectorAll("
        "'.ws-wgrid2 .ws-wcard'); for (var i = 0; i < cards.length;"
        " i++) { var h = cards[i].querySelector('.ws-whead-t');"
        " if (h && h.textContent.indexOf('Повторные') !== -1) {"
        " var ch = cards[i].querySelectorAll('.ws-done-chk');"
        " var clickable = 0; ch.forEach(function(c){"
        " if (c.getAttribute('onclick')) clickable++; });"
        " return {total: ch.length, clickable: clickable}; } }"
        " return null;})()")
    check('H3: галочки инструктажей НЕ кликабельны (view)',
          no_click and no_click['clickable'] == 0, no_click)
    check('H4: 0 JS-ошибок', not js_errors, js_errors[:5])
    ctx.close()

    # ===== Контекст 3: мобайл 375, тёмная, edit =====
    print('=== Контекст 3: мобайл 375 тёмная edit ===')
    ADMIN = True
    reset_data()
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mob')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Федосов А. В.')")
    page.wait_for_timeout(900)
    evb = block(page, 'Мероприятия')
    check('I1: блок мероприятий на мобайле с записью года',
          ('Мероприятия · %d' % Y) in evb.get('head', '') and
          'Курс АСУ ТП' in evb.get('html', ''), evb.get('head', ''))
    page.click(".ws-wgrid2 .ws-wcard .ws-emp-addtr")
    page.wait_for_timeout(700)
    fs = form_state(page)
    page.screenshot(path='task425-proof-mobile.png', full_page=False)
    check('I2: форма открывается, select РОВНО три типа, тап-зона %dpx'
          % fs.get('tapH', 0),
          fs['open'] and fs['options'] == ['обучение', 'прогул',
                                           'примечание'] and
          fs.get('tapH', 0) >= 40, fs)
    check('I3: 0 JS-ошибок', not js_errors, js_errors[:5])
    ctx.close()

    browser.close()

print('')
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
