#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 394: browser-check — заявка (3 части):
#   (1) десктоп: отпуска — СПРАВА от профиля, СИЗ — ПОД отпусками,
#       четыре блока — равномерно на весь экран (сетка 2×2);
#   (2) в карточках мероприятия — на ВЕСЬ ГОД;
#   (3) окно мероприятий месяца: ОТПУСКА (частично на два месяца —
#       в окнах ОБЕИХ месяцев) и СИЗ (срок истекает в месяце).
# МОК: 6 работников (как Task 393), Иванову: 2 отпуска (10–20 тек.
# месяца + ЧЕРЕЗ ГРАНИЦУ: последний день тек. месяца — 2-е число
# следующего), 3 мероприятия ГОДА (тек. месяц + март + июнь),
# 3 СИЗ (окончание 12-го тек. месяца / «До износа» / окончание
# 5-го следующего месяца).
# ДЕСКТОП 1280 (тёмная, Админ): A загрузка; B табель + окно
#   мероприятий (мероприятия/отпуска/СИЗ тек. месяца); C СЛЕДУЮЩИЙ
#   месяц (отпуск через границу и СИЗ следующего месяца видны —
#   «обоих месяцев»); D выбранный день (Task 316: накрывающий
#   отпуск + СИЗ ровно в день); E «Работники»: сетка 2×2 на весь
#   экран (отпуска справа профиля, СИЗ под отпусками, мероприятия
#   под профилем), блок 3 — «Мероприятия · ГОД» со всеми записями
#   года; F «Общая» — колонка «Мероприятия · ГОД»; G 0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ): M1 стек в колонку (без сетки);
#   M2 блок 3 — год; M3 чип «Мероприятия» — окно с секциями;
#   M4 0 JS-ошибок.
# Порт 9006 (запуск: python3 -m http.server 9006 &).
import calendar
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9006
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
NM, NY = (M + 1, Y) if M < 12 else (1, Y + 1)
NDIM = calendar.monthrange(NY, NM)[1]

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

def nd(day):
    return '%04d-%02d-%02d' % (NY, NM, day)

def dd(day):
    return '%02d.%02d' % (day, M)

def ndd(day):
    return '%02d.%02d' % (day, NM)

MONTHS_NOM = ['январь','февраль','март','апрель','май','июнь',
              'июль','август','сентябрь','октябрь','ноябрь','декабрь']
CUR_M = MONTHS_NOM[M - 1]
NEXT_M = MONTHS_NOM[NM - 1]

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': 'бригада А'},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
  {'таб_номер': '045', 'ФИО': 'Сидорова А. А.', 'тип': 'сменный', 'смена': 2,
   'шаблон_ротации': 1, 'старт_цикла': d(2),
   'дата_приёма': '2023-06-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электрик КИПиА', 'комментарий': ''},
  {'таб_номер': '100', 'ФИО': 'Кузнецов К. К.', 'тип': 'сменный', 'смена': '',
   'шаблон_ротации': 1, 'старт_цикла': d(3),
   'дата_приёма': '2022-04-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'комментарий': ''},
  {'таб_номер': '101', 'ФИО': 'Васильев В. В.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(1),
   'дата_приёма': '2021-09-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА см.1', 'комментарий': ''},
  {'таб_номер': '102', 'ФИО': 'Николаева Н. Н.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(4),
   'дата_приёма': '2024-11-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
CODES = [
  {'code': 'Д8',   'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Д7,2', 'name': 'День 7,2-час', 'color': '#FFF9C4', 'short': 'день 7,2ч'},
  {'code': 'Д',    'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день 12ч'},
  {'code': 'Н',    'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'д',    'name': 'День в вых.', 'color': '#FFD54F', 'short': 'день в выходной'},
  {'code': 'н',    'name': 'Ночь в вых.', 'color': '#78909C', 'short': 'ночь в выходной'},
  {'code': 'ОТ',   'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': 'У',    'name': 'Учебный отпуск', 'color': '#80CBC4', 'short': 'ученический'},
  {'code': 'ОВ',   'name': 'Отгул', 'color': '#C5E1A5', 'short': 'отгул'},
  {'code': 'Б',    'name': 'Больничный', 'color': '#F8BBD0', 'short': 'больничный'},
  {'code': 'ПР',   'name': 'Прогул', 'color': '#EF5350', 'short': 'прогул'},
  {'code': 'И',    'name': 'Инструктаж', 'color': '#B3E5FC', 'short': 'инструктаж'},
  {'code': 'ОБ',   'name': 'Обучение', 'color': '#D1C4E9', 'short': 'обучение'},
  {'code': 'ПЗ',   'name': 'Проверка знаний', 'color': '#FFCDD2', 'short': 'проверка знаний'},
  {'code': '*',    'name': 'Примечание', 'color': '#FFAB91', 'short': 'не плановый'},
  {'code': '',     'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
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
# СИЗ Иванову: окончание 12-го ТЕКУЩЕГО месяца (секция СИЗ в окне
# мероприятий текущего месяца), «До износа» (без даты — скрыто),
# ботинки — окончание 5-го СЛЕДУЮЩЕГО месяца (секция в следующем)
PPE_STATE = [
  {'id': 1, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА',
   'наименование': 'Костюм для защиты от растворов кислот и щелочей',
   'дата_выдачи': '%d-%02d-12' % (Y - 1, M), 'срок_годности': '1 год',
   'дата_окончания': d(12), 'примечание': ''},
  {'id': 2, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'срок_годности': 'До износа',
   'дата_окончания': 'До износа', 'примечание': ''},
  {'id': 3, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Ботинки',
   'дата_выдачи': '%04d-%02d-05' % (NY - 2, NM), 'срок_годности': '2 года',
   'дата_окончания': nd(5), 'примечание': ''},
]
# 2 отпуска Иванову: целиком в месяце + ЧЕРЕЗ ГРАНИЦУ (последний
# день текущего — 2-е число следующего: виден в окнах ОБЕИХ месяцев)
VACATIONS = [
  {'id': 11, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(10), 'дата_окончания': d(20), 'комментарий': ''},
  {'id': 12, 'таб_номер': '017', 'часть': 2,
   'дата_начала': d(DIM - 1), 'дата_окончания': nd(2), 'комментарий': ''},
]
# 3 мероприятия ГОДА (тек. месяц + март + июнь) — карточка показывает
# мероприятия за весь год
TRAININGS = [
  {'id': 31, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Охрана труда',
   'дата_начала': d(5), 'дата_окончания': d(5)},
  {'id': 32, 'таб_номер': '017', 'тип': 'обучение', 'тема': 'Пожарная безопасность',
   'дата_начала': '%d-03-10' % Y, 'дата_окончания': '%d-03-10' % Y},
  {'id': 33, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Первая помощь',
   'дата_начала': '%d-06-15' % Y, 'дата_окончания': '%d-06-15' % Y},
]

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag):
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
                        'role': 'Админ'}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'Админ', 'found': True,
                        'permissions': {'workschedule.view': True,
                                        'workschedule.edit': True}}}, ensure_ascii=False))
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
                body=json.dumps({'ok': True, 'data': {'ppe': PPE_STATE}}, ensure_ascii=False))
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
                      body='not found (t394-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t394-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'admin')

    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B0: табель открыт, сетка отрисована (6 работников)',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length === 6"))

    # ---------- B: окно мероприятий текущего месяца (3 секции) ----------
    ev = page.evaluate("document.getElementById('wsEventsPanel').textContent || ''")
    check('B1: «Мероприятия · %s %d · 1» + запись месяца' % (CUR_M, Y),
          ('Мероприятия · %s %d · 1' % (CUR_M, Y)) in ev and 'Охрана труда' in ev, ev[:160])
    check('B2: «Отпуска · %s %d · 2» — оба отпуска (в месяце + через границу)' % (CUR_M, Y),
          ('Отпуска · %s %d · 2' % (CUR_M, Y)) in ev and
          ('%d–%d.%02d' % (10, 20, M)) in ev and
          ('%02d.%02d–%s' % (DIM - 1, M, ndd(2))) in ev and
          ('Отпуск · Иванов И. И.' in ev), ev[:300])
    check('B3: «СИЗ · %s %d · 1» — костюм (до %s), «До износа»/ботинки скрыты' % (CUR_M, Y, dd(12)),
          ('СИЗ · %s %d · 1' % (CUR_M, Y)) in ev and
          ('до %s' % dd(12)) in ev and
          'Костюм для защиты от растворов кислот и щелочей' in ev and
          'Очки закрытые' not in ev and 'Ботинки' not in ev, ev[:300])
    page.screenshot(path='task394-proof-events.png', full_page=False)

    # ---------- C: СЛЕДУЮЩИЙ месяц — «обоих месяцев» ----------
    if M == 12:
        page.select_option('#wsYearSel', str(NY))
    page.select_option('#wsMonthSel', str(NM))
    page.wait_for_timeout(2500)
    ev2 = page.evaluate("document.getElementById('wsEventsPanel').textContent || ''")
    check('C1: «Отпуска · %s %d · 1» — ЧЕРЕЗ ГРАНИЦУ виден и в следующем месяце' % (NEXT_M, NY),
          ('Отпуска · %s %d · 1' % (NEXT_M, NY)) in ev2 and
          ('%02d.%02d–%s' % (DIM - 1, M, ndd(2))) in ev2 and
          'Отпуск · Иванов И. И.' in ev2 and
          ('%d–%d.%02d' % (10, 20, M)) not in ev2, ev2[:300])
    check('C2: «СИЗ · %s %d · 1» — ботинки (до %s), костюм скрыт' % (NEXT_M, NY, ndd(5)),
          ('СИЗ · %s %d · 1' % (NEXT_M, NY)) in ev2 and
          ('до %s' % ndd(5)) in ev2 and 'Ботинки' in ev2 and
          'Костюм' not in ev2, ev2[:300])
    check('C3: мероприятий в следующем месяце нет — «нет мероприятий в этом месяце»',
          'нет мероприятий в этом месяце' in ev2 and 'Охрана труда' not in ev2, ev2[:200])

    # ---------- D: выбранный день (Task 316) — отпуска/СИЗ по дню ----------
    if M == 12:
        page.select_option('#wsYearSel', str(Y))
    page.select_option('#wsMonthSel', str(M))
    page.wait_for_timeout(2500)
    page.evaluate("WorkSchedule._daySelect(12)")
    page.wait_for_timeout(400)
    ev3 = page.evaluate("document.getElementById('wsEventsPanel').textContent || ''")
    check('D1: день 12 — «Мероприятия · %s» без накрывающих записей' % dd(12),
          ('Мероприятия · %s' % dd(12)) in ev3 and 'нет мероприятий в этот день' in ev3, ev3[:200])
    check('D2: день 12 — «Отпуска · %s · 1» (отпуск 10–20 накрывает)' % dd(12),
          ('Отпуска · %s · 1' % dd(12)) in ev3 and 'Отпуск · Иванов И. И.' in ev3, ev3[:200])
    check('D3: день 12 — «СИЗ · %s · 1» (окончание ровно в день)' % dd(12),
          ('СИЗ · %s · 1' % dd(12)) in ev3 and 'Костюм' in ev3, ev3[:200])
    page.evaluate("WorkSchedule._daySelect(null)")
    page.wait_for_timeout(400)

    # ---------- E: «Работники» — сетка 2×2 на весь экран + ГОД ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    e = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var grid = body ? body.querySelector('.ws-wgrid2') : null;
        var cards = grid ? grid.querySelectorAll(':scope > .ws-wcard') : [];
        var cs = grid ? getComputedStyle(grid) : null;
        var r = [], rect;
        for (var i = 0; i < cards.length; i++) {
            rect = cards[i].getBoundingClientRect();
            r.push({left: rect.left, top: rect.top, right: rect.right,
                    width: rect.width, height: rect.height});
        }
        var gr = grid ? grid.getBoundingClientRect() : null;
        return {
            n: cards.length,
            display: cs ? cs.display : null,
            cols: cs ? cs.gridTemplateColumns : null,
            rowGap: cs ? cs.rowGap : null,
            rects: r,
            gridW: gr ? gr.width : 0,
            b3: cards.length > 2 ? (cards[2].textContent || '') : '',
            vw: window.innerWidth
        };
    })()""")
    check('E1: обёртка .ws-wgrid2 — СЕТКА (display: grid, 2 равные колонки)',
          e['display'] == 'grid' and e['n'] == 4, (e['display'], e['n']))
    cols = [float(c.replace('px', '')) for c in (e['cols'] or '').split() if c]
    check('E2: колонки РАВНЫЕ (1fr 1fr) — на весь экран',
          len(cols) == 2 and abs(cols[0] - cols[1]) < 3 and e['gridW'] >= 900,
          (e['cols'], e['gridW']))
    check('E3: зазор сетки — 12px', e['rowGap'] == '12px', e['rowGap'])
    r1, r2, r3, r4 = e['rects'][0], e['rects'][1], e['rects'][2], e['rects'][3]
    check('E4: ОТПУСКА — СПРАВА от профиля (ряд 1)',
          r2['left'] > r1['left'] + 100 and abs(r2['top'] - r1['top']) < 4,
          (r1, r2))
    check('E5: СИЗ — ПОД отпусками (ряд 2, правая колонка)',
          abs(r4['left'] - r2['left']) < 4 and r4['top'] > r2['top'] + 100,
          (r2, r4))
    check('E6: МЕРОПРИЯТИЯ — под профилем (ряд 2, левая колонка)',
          abs(r3['left'] - r1['left']) < 4 and r3['top'] > r1['top'] + 100,
          (r1, r3))
    check('E7: блок 3 — «Мероприятия · %d»: записи ВСЕГО ГОДА' % Y,
          ('Мероприятия · %d' % Y) in e['b3'] and 'Охрана труда' in e['b3'] and
          'Пожарная безопасность' in e['b3'] and 'Первая помощь' in e['b3'] and
          '+ Мероприятие…' in e['b3'], e['b3'][:260])
    page.screenshot(path='task394-proof-workers.png', full_page=False)

    # ---------- F: «Общая» — колонка «Мероприятия · ГОД», без сетки ----------
    page.click('button.ws-wtab-general')
    page.wait_for_timeout(500)
    f = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var rows = body.querySelectorAll('.ws-wgen-table tbody tr');
        var row = '';
        for (var i = 0; i < rows.length; i++) {
            if ((rows[i].textContent || '').indexOf('Иванов И. И.') !== -1) {
                row = rows[i].textContent || '';
            }
        }
        return {
            grid: !!body.querySelector('.ws-wgrid2'),
            head: (body.querySelector('.ws-wgen-table thead') || {}).textContent || '',
            row: row
        };
    })()""")
    check('F1: «Общая» — БЕЗ сетки карточки, колонка «Мероприятия · %d»' % Y,
          not f['grid'] and ('Мероприятия · %d' % Y) in f['head'], f['head'][:200])
    check('F2: сводка — годовой счётчик мероприятий Иванова (3)',
          'Иванов И. И.' in f['row'] and '3' in f['row'], f['row'][:200])

    check('G: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобильный 375, светлая, Админ =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 720})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'mob')

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('#wsWorkersBtn')
    page2.wait_for_timeout(1000)
    page2.click('button[title="Иванов И. И."]')
    page2.wait_for_timeout(800)
    m = page2.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var grid = body ? body.querySelector('.ws-wgrid2') : null;
        var cards = grid ? grid.querySelectorAll(':scope > .ws-wcard') : [];
        var cs = grid ? getComputedStyle(grid) : null;
        var tops = [], fit = true, vw = window.innerWidth;
        for (var i = 0; i < cards.length; i++) {
            var r = cards[i].getBoundingClientRect();
            tops.push(r.top);
            if (r.right > vw + 1 || r.left < -1) fit = false;
        }
        return {n: cards.length, display: cs ? cs.display : null,
                stack: tops.length === 4 && tops[0] < tops[1] && tops[1] < tops[2] && tops[2] < tops[3],
                fit: fit,
                b3: cards.length > 2 ? (cards[2].textContent || '') : ''};
    })()""")
    check('M1: мобильный — СТЕК в колонку (display: block), в границах экрана',
          m['n'] == 4 and m['display'] == 'block' and m['stack'] and m['fit'],
          (m['n'], m['display'], m['stack'], m['fit']))
    check('M2: мобильный — блок 3 «Мероприятия · %d» (год)' % Y,
          ('Мероприятия · %d' % Y) in m['b3'] and 'Первая помощь' in m['b3'],
          m['b3'][:160])
    # чип «Мероприятия» — окно с секциями отпусков/СИЗ
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(2500)
    page2.click('#wsChipEvents')
    page2.wait_for_timeout(500)
    me = page2.evaluate("""(function(){
        var el = document.getElementById('wsEventsPanel');
        var st = el ? getComputedStyle(el) : null;
        return {txt: el ? (el.textContent || '') : '',
                visible: st ? (st.display !== 'none' && !el.hidden) : false};
    })()""")
    check('M3: чип «Мероприятия» — окно с секциями (отпуска + СИЗ)',
          me['visible'] and ('Отпуска · %s %d' % (CUR_M, Y)) in me['txt'] and
          ('СИЗ · %s %d' % (CUR_M, Y)) in me['txt'], me['txt'][:220])
    page2.screenshot(path='task394-proof-mobile.png', full_page=False)
    check('M4: 0 JS-ошибок (мобильный)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('Task 394 browser-check: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
