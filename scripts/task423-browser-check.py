#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 423: browser-check — заявка «9-ОГЭ создалось через 6 месяцев
# а не через 3».
# ДИАГНОЗ: правило (2) создавало запись 9-ОГЭ на «дата общего +
# период из строки 9-ОГЭ живого листа», а там стоит «6» (скопировано
# с родителя «(6 месяцев)»); встроенная связь дефолтирует только
# ПУСТУЮ ячейку → 9-ОГЭ +6 вместо +3.
# ПРОВЕРКИ (мок-сервер, порт 8924; ЖИВОЙ ЛИСТ: у 9-ОГЭ
# периодичность 6 — как у родителя; мок setTrainingDone имитирует
# НОВЫЙ сервер Task 423 — обе записи, srvVer '423'):
#   1) десктоп 1280 тёмная, edit:
#      • «след. срок» 9-ОГЭ = дата общего + 3 мес (ГЛАВНЫЙ
#        КЛИЕНТСКИЙ ФИКС: до правки лист «6» уводил срок на +6);
#        бейдж группы — «раз в 3 месяца»;
#      • клик галочки общего 601 → тост «новые сроки: <9-ОГЭ +3>,
#        <общий +6>» — ОБЕ даты, дата 9-ОГЭ = +3 мес (ГЛАВНЫЙ
#        ФИКС СЕРВЕРА: до правки создавалось +6); покрытие старого
#        9-ОГЭ; новая запись в карточке/пуле; автоNote в консоли;
#        предупреждения о старой версии НЕТ (srvVer 423);
#      • отметка созданного 9-ОГЭ → только фиксация (регресс 421);
#      • ✎ жив (регресс 417); кэш-путь;
#   2) десктоп 1280 тёмная, edit, СЕРВЕР 422 (srvVer '422'):
#      тост с датами + «⚠ Сервер Apps Script старой версии…»;
#   3) десктоп 1280 светлая, view: состояния некликабельны;
#   4) мобайл 375 тёмная, edit: галочка >=22px, тап по ПЗ
#      (независимый) → тост «новые сроки» +12 мес.
import calendar
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8924
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


# Федосов: старый 9-ОГЭ 600 (6 мес назад); общий 601 (10 дней
# назад); будущая ПЗ 602. Тестов: самостоятельный 9-ОГЭ 610.
past_dt = TODAY - datetime.timedelta(days=10)
if past_dt.year != Y:
    past_dt = datetime.date(Y, 1, 15)
PAST_OT = d(past_dt.year, past_dt.month, past_dt.day)
stale_dt = add_months(past_dt, -6)
STALE_OGE = d(stale_dt.year, stale_dt.month, stale_dt.day)
oge_next = add_months(past_dt, 3)
OGE_NEXT = d(oge_next.year, oge_next.month, oge_next.day)
ot6 = add_months(past_dt, 6)
OT6_NEXT = d(ot6.year, ot6.month, ot6.day)
TODAY_ISO = d(TODAY.year, TODAY.month, TODAY.day)
future_dt = TODAY + datetime.timedelta(days=30)
FUTURE = d(future_dt.year, future_dt.month, future_dt.day)
pz_next = add_months(future_dt, 12)
PZ_NEXT = d(pz_next.year, pz_next.month, pz_next.day)
solo_dt = add_months(TODAY, -1)
SOLO_OGE = d(solo_dt.year, solo_dt.month, solo_dt.day)

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

# ЖИВОЙ ЛИСТ заявки: у 9-ОГЭ периодичность 6 — скопирована с
# родителя («9-ОГЭ включён в Повторный инструктаж … (6 месяцев)»);
# столбца «в составе» нет — связь строит клиент (Task 420)
INSTR_LIST = [
  {'название': U_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': 'Инстр. ОТ'},
  {'название': U_OGE, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': '9-ОГЭ'},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': 'ПЗ до 1000 В'},
]

# автосоздаваемые записи (мок НОВОГО сервера Task 423): ОБЕ —
# 9-ОГЭ РОВНО +3 мес (значение листа «6» не сдвигает срок) и
# общий +6 мес
CREATED_OGE = {'id': 604, 'таб_номер': '0871', 'тип': 'инструктаж',
               'тема': U_OGE, 'дата_начала': OGE_NEXT, 'дата_окончания': OGE_NEXT,
               'длительность_дней': 1, 'комментарий': '',
               'дата_проведения': OGE_NEXT, 'выполнение': 0, 'просрочен': 0}
CREATED_OT = {'id': 605, 'таб_номер': '0871', 'тип': 'инструктаж',
              'тема': U_OT, 'дата_начала': OT6_NEXT,
              'дата_окончания': OT6_NEXT, 'длительность_дней': 1,
              'комментарий': '', 'дата_проведения': OT6_NEXT,
              'выполнение': 0, 'просрочен': 0}
CREATED_PZ = {'id': 607, 'таб_номер': '0871', 'тип': 'проверка_знаний',
              'тема': N_EL, 'дата_начала': PZ_NEXT, 'дата_окончания': PZ_NEXT,
              'длительность_дней': 1, 'комментарий': '',
              'дата_проведения': PZ_NEXT, 'выполнение': 0, 'просрочен': 0}

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

DONE_CALLS = []
CONSOLE_MSGS = []
AUTOCREATED = False
PZ_CREATED = False
OLD422 = False   # имитация Apps Script Task 422 (srvVer '422' —
                 # период 9-ОГЭ ещё по значению листа)
PASS = 0
FAIL = 0
ADMIN = True


def fresh_instr_all():
    """Снимок листа «Инструктажи» (формат done): 0871 — старый 9-ОГЭ
    600 (6 мес назад), общий 601 (10 дней назад), будущая ПЗ 602;
    0872 — самостоятельный 9-ОГЭ 610 (месяц назад)"""
    base = [
      {'id': 600, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': U_OGE,
       'дата_начала': STALE_OGE, 'дата_окончания': STALE_OGE,
       'длительность_дней': 1, 'комментарий': '',
       'дата_проведения': STALE_OGE, 'выполнение': 0, 'просрочен': 1},
      {'id': 601, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': U_OT,
       'дата_начала': PAST_OT, 'дата_окончания': PAST_OT,
       'длительность_дней': 1, 'комментарий': '',
       'дата_проведения': PAST_OT, 'выполнение': 0, 'просрочен': 1},
      {'id': 602, 'таб_номер': '0871', 'тип': 'проверка_знаний', 'тема': N_EL,
       'дата_начала': FUTURE, 'дата_окончания': FUTURE, 'длительность_дней': 1,
       'комментарий': '', 'дата_проведения': FUTURE, 'выполнение': 0,
       'просрочен': 0},
      {'id': 610, 'таб_номер': '0872', 'тип': 'инструктаж', 'тема': U_OGE,
       'дата_начала': SOLO_OGE, 'дата_окончания': SOLO_OGE,
       'длительность_дней': 1, 'комментарий': '',
       'дата_проведения': SOLO_OGE, 'выполнение': 0, 'просрочен': 1},
    ]
    return [dict(r) for r in base]


INSTR_ALL = fresh_instr_all()


def reset_data():
    global INSTR_ALL, AUTOCREATED, PZ_CREATED, DONE_CALLS
    INSTR_ALL = fresh_instr_all()
    AUTOCREATED = False
    PZ_CREATED = False
    DONE_CALLS = []


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def api_response(action, body):
    global AUTOCREATED, PZ_CREATED
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
        return {'ok': True, 'data': {'role': role, 'found': True,
                'permissions': perms}}
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
        return {'ok': True, 'data': {
            'trainings': [dict(r) for r in INSTR_ALL
                          if r['дата_начала'][:4] == str(Y)],
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
        skipped = []
        note = ('пункт=' + rec['тема'] + ' родитель=- дети=' + U_OGE +
                ' [' + '9-ОГЭ' + ' → ' + ru(OGE_NEXT) + ']')
        # 601 — общий Федосова: ГЛАВНЫЙ ФИКС Task 423 — 9-ОГЭ +3 мес
        # (значение листа «6» не сдвигает) и общий +6 мес; покрытие
        # старого 9-ОГЭ 600
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
        # 604 — созданный 9-ОГЭ: зависимый, только фиксация (421)
        if val == 1 and rid == 604:
            created = []
            note = ('пункт=' + U_OGE + ' родитель=' + U_OT + ' дети=-' +
                    '; Task 421: зависимый пункт — автосоздания нет')
        # 610 — самостоятельный 9-ОГЭ Тестова: фиксация (регресс 421)
        if val == 1 and rid == 610:
            created = []
            note = ('пункт=' + U_OGE + ' родитель=' + U_OT + ' дети=-' +
                    '; Task 421: зависимый пункт — автосоздания нет')
        # 602 — ПЗ: независимый пункт, свой срок +12 мес (правило 1)
        if val == 1 and rid == 602:
            created = [dict(CREATED_PZ)]
            note = 'пункт=' + N_EL + ' родитель=- дети=-'
            if not PZ_CREATED:
                INSTR_ALL.append(dict(CREATED_PZ))
                PZ_CREATED = True
        # сервер Task 422: srvVer есть, но период 9-ОГЭ ещё по
        # значению листа — клиент обязан предупредить (< 423)
        srv = '422' if OLD422 else '423'
        return {'ok': True, 'data': {'id': rid,
                'выполнение': rec['выполнение'],
                'просрочен': rec['просрочен'],
                'srvVer': srv,
                'autoNote': note,
                'created': created, 'updated': updated,
                'skipped': skipped}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, keep_cache=False):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    page.on('console', lambda msg: CONSOLE_MSGS.append(msg.text))
    pre = ''
    if not keep_cache:
        pre += ("try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
                "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};")
    ctx.add_init_script(
        pre +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t423-%s');" % tag +
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
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t423-%s)' % tag)
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


def toast_text(page):
    return page.evaluate(
        "(function(){var m = document.getElementById('toastMessage');"
        " return m ? m.textContent : '';})()")


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ===== Контекст 1: десктоп 1280, тёмная, edit — сервер 423 =====
    print('=== Контекст 1: десктоп тёмная edit — сервер 423, лист «6» у 9-ОГЭ ===')
    ADMIN = True
    OLD422 = False
    reset_data()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'main')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    open_workers_card(page)
    page.screenshot(path='task423-proof-card-initial.png', full_page=False)

    link_state = page.evaluate("""(function(){
    var l = WorkSchedule._INSTR_LIST || [];
    var og = null;
    l.forEach(function(x){
        if (x.название.indexOf('9-ОГЭ') !== -1) og = x;
    });
    return {link: og ? (og['в составе'] || '') : 'нет пункта',
            per: og ? og.периодичность : 0};
})()""")
    check('B0: регресс 420 — клиент построил связь 9-ОГЭ → общий',
          link_state['link'] == U_OT, link_state)
    check('B1: ГЛАВНЫЙ КЛИЕНТСКИЙ ФИКС — период 9-ОГЭ = 3 (лист несёт «6»)',
          link_state['per'] == 3, link_state)

    # «след. срок» 9-ОГЭ = общий + 3 мес (не +6 от листа):
    # рендер секции (как Task 420) — заголовок группы + срок
    sec = page.evaluate(
        "WorkSchedule._renderInstrSection([], '0871', false, false,"
        " WorkSchedule._INSTR_LIST, %d)" % Y)
    i_oge = sec.find('9-ОГЭ')
    seg_oge = sec[i_oge:sec.find('ws-il-head', i_oge + 10)] \
        if i_oge != -1 else ''
    check('B2: «след. срок» 9-ОГЭ = общий + 3 мес (%s)' % ru(OGE_NEXT),
          ('след. срок: ' + ru(OGE_NEXT)) in seg_oge, seg_oge[:400])
    check('B3: срок НЕ уехал на +6 (%s)' % ru(OT6_NEXT),
          ('след. срок: ' + ru(OT6_NEXT)) not in seg_oge, seg_oge[:400])
    check('B4: бейдж группы — «раз в 3 месяца» (лист «6» не показан)',
          'раз в 3 месяца' in seg_oge and
          '6 месяцев' not in seg_oge, seg_oge[:200])

    r601 = first_row(page, 'рабочим инструкциям ОТ')
    check('C1: общий 601 — просрочен, пустая галочка',
          r601.get('late') and r601.get('chk') and not r601.get('chkOn'), r601)

    # --- ГЛАВНЫЙ ФИКС СЕРВЕРА: клик общего → ОБЕ записи, 9-ОГЭ +3 ---
    n_calls = len(DONE_CALLS)
    n_logs = len(CONSOLE_MSGS)
    click_chk(page, 'рабочим инструкциям ОТ')
    page.wait_for_timeout(1200)
    check('D1: API setTrainingDone вызван (601, 0→1)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 601, 'выполнение': 1}, DONE_CALLS[n_calls:])
    tt = toast_text(page)
    check('D2: ГЛАВНЫЙ ФИКС — 9-ОГЭ +3 мес (%s) в «новых сроках»'
          % ru(OGE_NEXT),
          'новые сроки' in tt and ru(OGE_NEXT) in tt, tt)
    check('D3: общий +6 (%s) — тоже в тосте (ОБЕ записи)' % ru(OT6_NEXT),
          ru(OT6_NEXT) in tt, tt)
    check('D4: srvVer 423 — предупреждения о старой версии НЕТ',
          'старой версии' not in tt, tt)
    page.screenshot(path='task423-proof-main-fix-toast.png', full_page=False)

    # console: autoNote залогирован
    logged = [m for m in CONSOLE_MSGS[n_logs:]
              if '[инструктажи] автосоздание:' in m]
    check('D5: autoNote — в консоли (F12): «[инструктажи] автосоздание:»',
          len(logged) >= 1, CONSOLE_MSGS[n_logs:][:5])

    r600b = rows_state(page, '9-ОГЭ')[0]
    check('D6: покрытие: старый 9-ОГЭ отмечен (зелёная, приглушен)',
          r600b.get('chkOn') and r600b.get('rowDone'), r600b)

    oge_rows = rows_state(page, '9-ОГЭ')
    new_oge = None
    for r in oge_rows:
        if ru(OGE_NEXT) in r.get('text', ''):
            new_oge = r
    check('E1: НОВАЯ запись 9-ОГЭ (%s) в блоке карточки — срок +3 мес'
          % ru(OGE_NEXT), bool(new_oge), len(oge_rows))
    check('E2: новая запись — пустая галочка, без «просрочен»',
          bool(new_oge) and new_oge.get('chk') and
          not new_oge.get('chkOn') and not new_oge.get('late'), new_oge)
    pools = page.evaluate("""(function(){
    var ids = {};
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){ ids[r.id] = r.дата_начала; });
    var ot0871 = 0;
    (WorkSchedule._INSTR_ALL||[]).forEach(function(r){
        if (r['таб_номер'] === '0871' &&
            r.тема.indexOf('рабочим инструкциям ОТ') !== -1) ot0871++; });
    return {inAll604: !!ids[604], d604: ids[604] || '',
            inAll605: !!ids[605], d605: ids[605] || '',
            ot0871: ot0871, total: (WorkSchedule._INSTR_ALL||[]).length};
})()""")
    check('E3: 9-ОГЭ +3 в пуле _INSTR_ALL (id 604, %s)' % OGE_NEXT,
          pools['inAll604'] and pools['d604'] == OGE_NEXT, pools)
    check('E4: общий +6 в пуле (id 605, %s)' % OT6_NEXT,
          pools['inAll605'] and pools['d605'] == OT6_NEXT, pools)
    check('E5: дублей общего у Федосова нет (601 + 605)',
          pools['ot0871'] == 2, pools)

    # --- регресс 421: клик НОВОЙ записи 9-ОГЭ — фиксация ---
    n_calls = len(DONE_CALLS)
    res_click = click_chk(page, '9-ОГЭ', idx=1)
    page.wait_for_timeout(1000)
    check('F1: клик галочки НОВОЙ 9-ОГЭ → API (604, 1)',
          res_click == 'clicked' and len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 604, 'выполнение': 1},
          (res_click, DONE_CALLS[n_calls:]))
    tt2 = toast_text(page)
    check('F2: регресс 421 — тост РОВНО «Отмечено выполнение»'
          ' (без «новые сроки», без предупреждений)',
          tt2 == 'Отмечено выполнение', tt2)
    pools2 = page.evaluate(
        "(function(){return {total: (WorkSchedule._INSTR_ALL||[]).length};})()")
    check('F3: зависимый 9-ОГЭ ничего не создал (пул не вырос)',
          pools2['total'] == pools['total'], (pools, pools2))

    # --- Тестов: самостоятельный 9-ОГЭ — фиксация (регресс 421) ---
    page.click(".ws-wtabs button:has-text('Тестов Б. Б.')")
    page.wait_for_timeout(900)
    n_calls = len(DONE_CALLS)
    click_chk(page, '9-ОГЭ')
    page.wait_for_timeout(1000)
    check('G1: клик самостоятельного 9-ОГЭ 610 → API (фиксация)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 610, 'выполнение': 1}, DONE_CALLS[n_calls:])
    tt3 = toast_text(page)
    check('G2: тост «Отмечено выполнение» (9-ОГЭ зависимый)',
          tt3 == 'Отмечено выполнение', tt3)

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
    check('H1: регресс 417 — правка открывает форму',
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
    check('I1: кэш-путь — общий отмечен (зелёная)',
          r601c.get('chkOn') and not r601c.get('late'), r601c)
    oge_rows_c = rows_state(page, '9-ОГЭ')
    new_oge_c = [r for r in oge_rows_c if ru(OGE_NEXT) in r.get('text', '')]
    check('I2: кэш-путь — запись 9-ОГЭ +3 мес на месте',
          len(new_oge_c) == 1, len(oge_rows_c))
    check('I3: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ===== Контекст 2: СЕРВЕР 422 (srvVer '422' — период из листа) =====
    print('=== Контекст 2: десктоп тёмная edit — СЕРВЕР 422 ===')
    ADMIN = True
    OLD422 = True
    reset_data()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'old422')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_workers_card(page)
    n_calls = len(DONE_CALLS)
    click_chk(page, 'рабочим инструкциям ОТ')
    page.wait_for_timeout(1200)
    check('K1: клик → API (сервер 422 тоже отвечает)',
          len(DONE_CALLS) == n_calls + 1 and
          DONE_CALLS[-1] == {'id': 601, 'выполнение': 1}, DONE_CALLS[n_calls:])
    tt4 = toast_text(page)
    check('K2: ГЛАВНЫЙ ФИКС КЛИЕНТА — srvVer 422 < 423: предупреждение',
          tt4.startswith('Отмечено выполнение') and
          'старой версии' in tt4, tt4)
    check('K3: предупреждение объясняет, что делать',
          'WorkSchedule.gs' in tt4 and 'версию развёртывания' in tt4, tt4)
    page.screenshot(path='task423-proof-old422-server-toast.png', full_page=False)
    check('K4: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ===== Контекст 3: десктоп 1280, светлая, view =====
    print('=== Контекст 3: десктоп светлая view ===')
    ADMIN = False
    OLD422 = False
    reset_data()
    # view-состояние: у Тестова 9-ОГЭ 610 выполнен
    for r in INSTR_ALL:
        if r['id'] == 610:
            r['выполнение'] = 1
            r['просрочен'] = 0
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'view')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_workers_card(page)
    rv601 = first_row(page, 'рабочим инструкциям ОТ')
    check('L1: view — невыполненный общий: галочки НЕТ (ws-done-ro —'
          ' только для выполненных, Task 418), некликабельно',
          not rv601.get('chk') and not rv601.get('chkOn') and
          not rv601.get('chkClickable'), rv601)
    page.click(".ws-wtabs button:has-text('Тестов Б. Б.')")
    page.wait_for_timeout(900)
    rv610 = first_row(page, '9-ОГЭ')
    check('L2: view — 9-ОГЭ Тестова: «Выполнено», некликабельно',
          rv610.get('chkOn') and rv610.get('chkRo') and
          not rv610.get('chkClickable') and not rv610.get('late'), rv610)
    n2 = len(DONE_CALLS)
    click_chk(page, '9-ОГЭ')
    page.wait_for_timeout(600)
    check('L3: view — клики API НЕ вызывают',
          len(DONE_CALLS) == n2, DONE_CALLS[n2:])
    page.screenshot(path='task423-proof-view-light.png', full_page=False)
    check('L4: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ===== Контекст 4: мобайл 375, тёмная, edit =====
    print('=== Контекст 4: мобайл 375 тёмная edit ===')
    ADMIN = True
    reset_data()
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mobile')
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    open_workers_card(page)
    rm = first_row(page, 'до 1000 В')
    check('M1: мобайл — будущая ПЗ: пустая галочка, без «просрочен»',
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
    check('M2: мобайл — галочка достаточного размера (>=22px)',
          size['w'] >= 22 and size['h'] >= 22, size)
    nm = len(DONE_CALLS)
    click_chk(page, 'до 1000 В')
    page.wait_for_timeout(2500)
    check('M3: тап по галочке → API (602, 1)',
          len(DONE_CALLS) == nm + 1 and
          DONE_CALLS[-1] == {'id': 602, 'выполнение': 1}, DONE_CALLS[nm:])
    tt5 = toast_text(page)
    check('M4: ПЗ (независимый) — тост «новые сроки» +12 мес (%s)'
          % ru(PZ_NEXT), 'новые сроки' in tt5 and ru(PZ_NEXT) in tt5, tt5)
    check('M5: предупреждения о старой версии нет (srvVer 423)',
          'старой версии' not in tt5, tt5)
    page.screenshot(path='task423-proof-mobile-toggle.png', full_page=False)
    check('M6: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
