#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 399: browser-check — заявка «если у пользователя нет доступа
# к просмотру информации мастеров в табеле учёта, то и в окне
# мероприятий не должно быть информации мастеров (мероприятия,
# отпуска, СИЗ)».
# «Нет доступа к информации мастеров» = уровень «min»
# (workschedule.view.min): в сетке мастера скрыты с Task 340
# (_viewEmployees/_isMasterKipia); Task 399 синхронизирует окно
# мероприятий — записи мастеров исключаются из ВСЕХ трёх секций.
# МОК: 3 работника — Галкин «Мастер КИПиА» (мастер) + Иванов/
# Петров (не мастера); у каждого: мероприятие, отпуск, СИЗ
# текущего месяца.
# КОНТЕКСТЫ (матрица getMyAccess):
#   1) десктоп 1280 тёмная, КИП ИОС + workschedule.view.min:
#      сетка БЕЗ мастера (2 строки — Task 340 санити); окно
#      мероприятий — НИ ФИО, ни темы, ни СИЗ мастера; записи
#      не-мастеров видны; счётчики «· 1»; режим выбранного дня
#      (клик по дате) — мастер скрыт и там; кнопка «Работники»
#      скрыта (Task 395/398 санити); 0 JS-ошибок;
#   2) десктоп 1280 тёмная, КИП ИОС + workschedule.view:
#      сетка С мастером (3 строки); окно ПОЛНОЕ — записи мастера
#      показаны, счётчики «· 2»;
#   3) десктоп 1280 тёмная, Админ (edit): окно ПОЛНОЕ (санити
#      регресса — редактору ничего не отфильтровано);
#   4) мобильный 375 светлая, КИП ИОС + min: чип «Мероприятия»
#      раскрывает окно — мастера нет, не-мастер есть.
# Порт 9006 (запуск: python3 -m http.server 9006 &).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9006
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
  # мастер — в сетке скрыт у min (Task 340), Task 399 — и в окне
  {'таб_номер': '044', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(7),
   'дата_приёма': '2007-03-06', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'комментарий': ''},
]
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
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
TRAININGS = [
  # мастера: 07-08 числа текущего месяца
  {'id': 41, 'таб_номер': '044', 'тип': 'инструктаж',
   'тема': 'Инструктаж мастера', 'дата_начала': d(7), 'дата_окончания': d(8)},
  # не-мастера: 09 число
  {'id': 42, 'таб_номер': '017', 'тип': 'обучение',
   'тема': 'Обучение слесаря', 'дата_начала': d(9), 'дата_окончания': d(9)},
]
VACATIONS = [
  {'id': 21, 'таб_номер': '044', 'часть': 1,
   'дата_начала': d(1), 'дата_окончания': d(14), 'комментарий': ''},
  {'id': 22, 'таб_номер': '023', 'часть': 1,
   'дата_начала': d(15), 'дата_окончания': d(20), 'комментарий': ''},
]
PPE = [
  {'id': 31, 'таб_номер': '044', 'наименование': 'Каска защитная',
   'дата_выдачи': d(1), 'срок_годности': 12, 'дата_окончания': d(12), 'ед': 'шт'},
  {'id': 32, 'таб_номер': '017', 'наименование': 'Перчатки',
   'дата_выдачи': d(1), 'срок_годности': 12, 'дата_окончания': d(5), 'ед': 'шт'},
]

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag, perms, role):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

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
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': role}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': role, 'found': True,
                        'permissions': perms}}, ensure_ascii=False))
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}))
        if action == 'workSchedule.getStatusCodes':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'codes': CODES}}, ensure_ascii=False))
        if action == 'workSchedule.listEmployees':
            inc = bool(body and body.get('includeArchived'))
            emps = EMPLOYEES if inc else [e for e in EMPLOYEES if not e['в_архиве']]
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'employees': emps}}, ensure_ascii=False))
        if action == 'workSchedule.getPatterns':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'patterns': PATTERNS}}, ensure_ascii=False))
        if action == 'workSchedule.listTrainings':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'trainings': TRAININGS}}, ensure_ascii=False))
        if action == 'workSchedule.listVacations':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'vacations': VACATIONS}}, ensure_ascii=False))
        if action == 'workSchedule.listPpe':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ppe': PPE}}, ensure_ascii=False))
        if action == 'workSchedule.listEntries':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'entries': []}}, ensure_ascii=False))
        if action == 'prodCalendar.getMonth':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                        'shortdays': 0, 'holidays': [], 'transfers': []}}))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t399-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t399-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

BASE_PERMS = {'calc.view': True, 'library.view': True, 'kipios.view': True,
              'secret.view': True, 'whatsnew.view': True}
MIN_PERMS = dict(BASE_PERMS, **{'workschedule.view.min': True})
VIEW_PERMS = dict(BASE_PERMS, **{'workschedule.view': True})
EDIT_PERMS = dict(BASE_PERMS, **{'workschedule.view': True,
                                 'workschedule.edit': True})

# окно мероприятий: сводка {мастер:bool, не-мастер:bool, счётчики}
# счётчики — из ОТДЕЛЬНЫХ плашек .ws-ep-cap: textContent всего окна
# склеивает «· 1» + «07.09» БЕЗ разделителя — regex по целому окну
# ловит «107»; плашка содержит только текст заголовка секции
PANEL_JS = """(function(){
    var el = document.getElementById('wsEventsPanel');
    var t = el ? el.textContent : '';
    var caps = el ? el.querySelectorAll('.ws-ep-cap') : [];
    var capN = function(idx) {
        var s = caps[idx] ? caps[idx].textContent : '';
        var m = s.match(/ · (\\d+)$/);
        return m ? m[1] : null;
    };
    return {
        hasPanel: !!el,
        masterFio: t.indexOf('Галкин') !== -1,
        masterTraining: t.indexOf('Инструктаж мастера') !== -1,
        masterPpe: t.indexOf('Каска') !== -1,
        nonTraining: t.indexOf('Обучение слесаря') !== -1,
        nonVac: t.indexOf('Отпуск · Петров П. П.') !== -1,
        nonPpe: t.indexOf('Перчатки') !== -1,
        capEv: capN(0),
        capVac: capN(1),
        capPpe: capN(2),
        emptyDay: t.indexOf('нет мероприятий в этот день') !== -1
    };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, КИП ИОС + min ==========
    print('=== Контекст 1: КИП ИОС, workschedule.view.min (сценарий заявки) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'min', MIN_PERMS, 'КИП ИОС')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    rows = page.evaluate("document.querySelectorAll('td.ws-emp-col[data-tab]').length")
    check('B: сетка — 2 строки (мастер скрыт у min, Task 340 санити)', rows == 2, rows)
    check('C: мастера нет в сетке',
          page.evaluate("document.querySelector('#wsGridWrap').textContent.indexOf('Галкин') === -1"))
    pnl = page.evaluate(PANEL_JS)
    check('D1: окно мероприятий отрисовано', pnl['hasPanel'])
    check('D2: ФИО мастера в окне НЕТ (Task 399)', not pnl['masterFio'], pnl)
    check('D3: мероприятие мастера в окне НЕТ', not pnl['masterTraining'])
    check('D4: отпуск мастера в окне НЕТ (мастер скрыт целиком)',
          not pnl['masterFio'] and not pnl['masterTraining'])
    check('D5: СИЗ мастера («Каска») в окне НЕТ', not pnl['masterPpe'])
    check('E1: мероприятие не-мастера ВИДНО', pnl['nonTraining'])
    check('E2: отпуск не-мастера ВИДНО', pnl['nonVac'])
    check('E3: СИЗ не-мастера («Перчатки») ВИДНО', pnl['nonPpe'])
    check('F1: счётчик мероприятий «· 1» (мастер не в счёте)',
          pnl['capEv'] == '1', pnl['capEv'])
    check('F2: счётчик отпусков «· 1»', pnl['capVac'] == '1', pnl['capVac'])
    check('F3: счётчик СИЗ «· 1»', pnl['capPpe'] == '1', pnl['capPpe'])
    page.screenshot(path='task399-proof-min.png', full_page=False)
    # режим выбранного дня: день 7 — только мастерское мероприятие
    page.evaluate("WorkSchedule._daySelect(7)")
    page.wait_for_timeout(400)
    pnl2 = page.evaluate(PANEL_JS)
    check('G1: день 7 (только мастерское) — окно ПУСТО от мастеров',
          not pnl2['masterFio'] and not pnl2['masterTraining'])
    check('G2: пустое состояние дня после фильтра', pnl2['emptyDay'])
    page.screenshot(path='task399-proof-min-day.png', full_page=False)
    # сброс выбора и день 9 — не-мастерское мероприятие видно
    page.evaluate("WorkSchedule._daySelect(7)")
    page.wait_for_timeout(300)
    page.evaluate("WorkSchedule._daySelect(9)")
    page.wait_for_timeout(400)
    pnl3 = page.evaluate(PANEL_JS)
    check('G3: день 9 — мероприятие не-мастера ВИДНО', pnl3['nonTraining'])
    check('G4: день 9 — мастера по-прежнему НЕТ', not pnl3['masterFio'])
    page.evaluate("WorkSchedule._daySelect(9)")
    page.wait_for_timeout(300)
    # санити прежних задач: «Работники» скрыта у min (Task 395/398)
    wbtn = page.evaluate(
        "(function(){var b=document.getElementById('wsWorkersBtn');"
        "var r=b.getBoundingClientRect();"
        "return {hidden:b.hidden, vis: r.width>1 && r.height>1};})()")
    check('H: «Работники» скрыта у min (Task 395/398 санити)',
          wbtn['hidden'] and not wbtn['vis'], wbtn)
    check('I: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, КИП ИОС + view ==========
    print('=== Контекст 2: КИП ИОС, workschedule.view (окно ПОЛНОЕ) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'view', VIEW_PERMS, 'КИП ИОС')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    rows = page.evaluate("document.querySelectorAll('td.ws-emp-col[data-tab]').length")
    check('J1: сетка — 3 строки (мастер виден у view)', rows == 3, rows)
    pnl = page.evaluate(PANEL_JS)
    check('J2: ФИО мастера в окне ЕСТЬ (view видит мастеров)', pnl['masterFio'])
    check('J3: мероприятие мастера показано', pnl['masterTraining'])
    check('J4: СИЗ мастера («Каска») показано', pnl['masterPpe'])
    check('J5: счётчики «· 2» (полные)',
          pnl['capEv'] == '2' and pnl['capVac'] == '2' and pnl['capPpe'] == '2',
          (pnl['capEv'], pnl['capVac'], pnl['capPpe']))
    page.screenshot(path='task399-proof-view.png', full_page=False)
    check('J6: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: десктоп 1280, Админ (edit) ==========
    print('=== Контекст 3: Админ, workschedule.edit (санити регресса) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'edit', EDIT_PERMS, 'Админ')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    pnl = page.evaluate(PANEL_JS)
    check('K1: редактор — окно ПОЛНОЕ (мастер показан)',
          pnl['masterFio'] and pnl['masterTraining'] and pnl['masterPpe'])
    check('K2: счётчик мероприятий «· 2»', pnl['capEv'] == '2', pnl['capEv'])
    check('K3: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 4: мобильный 375 светлая, КИП ИОС + min ==========
    print('=== Контекст 4: мобильный 375 светлая, КИП ИОС + min ===')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mobmin', MIN_PERMS, 'КИП ИОС')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    chip = page.evaluate(
        "(function(){var c=document.getElementById('wsChipEvents');"
        "var r=c.getBoundingClientRect();"
        "return {vis: r.width>1 && r.height>1};})()")
    check('L1: мобайл — чип «Мероприятия» виден', chip['vis'], chip)
    page.evaluate("WorkSchedule.toggleMobPanel('events')")
    page.wait_for_timeout(500)
    pnl = page.evaluate(PANEL_JS)
    check('L2: окно раскрыто — мастера НЕТ', not pnl['masterFio'] and not pnl['masterPpe'])
    check('L3: записи не-мастеров ВИДНЫ (мобайл)', pnl['nonTraining'] and pnl['nonPpe'])
    page.screenshot(path='task399-proof-mobile.png', full_page=False)
    check('L4: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
