#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 389: browser-check — заявка (4 части):
#   (1) окно «Мероприятия»: общий фон за ПРОШЕДШИМИ мероприятиями —
#       «как раньше», общий фон окна (как выше за оглавлением):
#       .ws-ep-past → transparent (обе темы), текущие/будущие —
#       темнее окна как прежде;
#   (2) страница «Работники»: кнопка «Добавить работника» — с бара
#       (шапки страницы) на «Общую» вкладку (клик — шторка создания);
#   (3) «Общая» вкладка: «На текущий момент: N работника
#       (автоматический подсчёт).» + «По штату: 14, из которых
#       2 мастера, 5 сменных и 7 дневных.»;
#   (4) фон ярлыков и окон вкладок — НЕ прозрачный (сплошной),
#       ярлыки и окна — с левого края.
# ДЕСКТОП 1280 (тёмная, Админ):
#   A  загрузка; B табель;
#   C  окно «Мероприятия» (текущий месяц): ИНВАРИАНТ — строка с
#      ws-ep-past → computed фон rgba(0,0,0,0) (ПРОЗРАЧНЫЙ = общий
#      фон окна), строка без → rgba(0,0,0,0.45) (ТЕМНЕЕ окна);
#      фон самого окна = var(--bg-tertiary) (#0e1621) — «как выше
#      за оглавлением»;
#   D  ПРЕДЫДУЩИЙ месяц (детерминизм): все строки прошедшие —
#      ВСЕ прозрачные; возврат в текущий;
#   E  «Работники»: в шапке страницы кнопки НЕТ; «Общая» вкладка —
#      численность (автоподсчёт) + штат; кнопка ВНУТРИ «Общей»
#      (клик → шторка «Новый работник»); ярлыки/окна — СПЛОШНЫЕ
#      фоны (26,34,51)/(14,22,33); блок — с ЛЕВОГО КРАЯ;
#      вкладка работника — карточка (сплошная);
#   F  0 JS-ошибок.
# ДЕСКТОП 1280 (светлая, Админ): G — окно «Мероприятия»: прошлые
#      прозрачные, текущие rgba(0,0,0,0.12), окно #F0EEE6; прошлый
#      месяц — все прозрачные; H 0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ): I — «Работники»: лента ярлыков
#      сплошная (#E4E0D3), окно «Общей» #F0EEE6, численность+штат+
#      кнопка; J 0 JS-ошибок.
# Порт 8999 (запуск: python3 -m http.server 8999 &).
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
M_LEN = (datetime.date(Y + (M // 12), (M % 12) + 1, 1) - datetime.timedelta(days=1)).day
if M == 1:
    PM, PY = 12, Y - 1
else:
    PM, PY = M - 1, Y

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

def pd(day):
    return '%04d-%02d-%02d' % (PY, PM, day)

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
]
VACATIONS = [
  {'id': 201, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(1), 'дата_окончания': d(10),
   'дней': 10, 'комментарий': 'лето'},
]
# Мероприятия: текущий месяц — дни 1-2 (прошедшие, если сегодня > 2)
# и будущие (сегодня+3/+6, урезанные в длину месяца — всегда
# «идёт/будет»); ПРЕДЫДУЩИЙ месяц — дни 5 и 10 (ГАРАНТИРОВАННО
# прошедшие — детерминизм проверки D/G3)
TRAININGS = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Повторный инструктаж по охране труда (тек. месяц, день 1)',
   'дата_начала': d(1), 'дата_окончания': d(1), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 102, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Целевой инструктаж перед работами (тек. месяц, день 2)',
   'дата_начала': d(2), 'дата_окончания': d(2), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 103, 'таб_номер': '023', 'тип': 'обучение', 'тема': 'Обучение по промбезопасности (будущее)',
   'дата_начала': d(min(TODAY.day + 3, M_LEN)), 'дата_окончания': d(min(TODAY.day + 3, M_LEN)),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 104, 'таб_номер': '045', 'тип': 'проверка_знаний', 'тема': 'Проверка знаний до 1000В (будущее)',
   'дата_начала': d(min(TODAY.day + 6, M_LEN)), 'дата_окончания': d(min(TODAY.day + 6, M_LEN)),
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 105, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Инструктаж прошлого месяца (день 5)',
   'дата_начала': pd(5), 'дата_окончания': pd(5), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 106, 'таб_номер': '023', 'тип': 'инструктаж', 'тема': 'Инструктаж прошлого месяца (день 10)',
   'дата_начала': pd(10), 'дата_окончания': pd(10), 'длительность_дней': 1, 'комментарий': ''},
]
CODES = [
  {'code': 'Д8',   'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Д7,2', 'name': 'День 7,2-час (пятн./предпраздн.)', 'color': '#FFF9C4', 'short': 'день 7,2ч'},
  {'code': 'Д',    'name': 'День (12-час, 7:30–19:30)', 'color': '#FFE082', 'short': 'день 12ч'},
  {'code': 'Н',    'name': 'Ночь (12-час, 19:30–7:30)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'д',    'name': 'День в вых./праздник', 'color': '#FFD54F', 'short': 'день в выходной'},
  {'code': 'н',    'name': 'Ночь в вых./праздник', 'color': '#78909C', 'short': 'ночь в выходной'},
  {'code': 'ОТ',   'name': 'Отпуск ежегодный основной', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': 'У',    'name': 'Учебный отпуск', 'color': '#80CBC4', 'short': 'ученический'},
  {'code': 'ОВ',   'name': 'Отгул (оплачиваемый)', 'color': '#C5E1A5', 'short': 'отгул'},
  {'code': 'Б',    'name': 'Больничный', 'color': '#F8BBD0', 'short': 'больничный'},
  {'code': 'ПР',   'name': 'Прогул', 'color': '#EF5350', 'short': 'прогул'},
  {'code': 'И',    'name': 'Инструктаж', 'color': '#B3E5FC', 'short': 'инструктаж'},
  {'code': 'ОБ',   'name': 'Обучение', 'color': '#D1C4E9', 'short': 'обучение'},
  {'code': 'ПЗ',   'name': 'Проверка знаний', 'color': '#FFCDD2', 'short': 'проверка знаний'},
  {'code': '*',    'name': 'Примечание (с комментарием)', 'color': '#FFAB91', 'short': 'не плановый'},
  {'code': '',     'name': 'Выходной, плановый выходной день', 'color': '#EEF0F2', 'short': 'выходной'},
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
ENTRIES = [
  {'id': 1, 'дата': d(5), 'таб_номер': '017', 'статус': 'Д',
   'источник': 'авто', 'переработка': 0, 'праздник': 0},
]

API_CALLS = []

def mock_response(action, body, viewer=False):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if not viewer else 'КИП ИОС дежурный'}}
    if action == 'getMyAccess':
        perms = ({'workschedule.view': True, 'workschedule.edit': True}
                 if not viewer else
                 {'workschedule.view': True, 'workschedule.edit': False,
                  'workschedule.view.min': False})
        return {'ok': True, 'data': {'role': 'Админ' if not viewer else 'КИП ИОС дежурный',
                'found': True, 'permissions': perms}}
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
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': [v for v in VACATIONS]}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action in ('workSchedule.updateEmployee', 'workSchedule.updateVacation',
                  'workSchedule.deleteVacation', 'workSchedule.addTraining',
                  'workSchedule.deleteTraining', 'workSchedule.addEmployee',
                  'workSchedule.dismissEmployee', 'workSchedule.setManualEntry',
                  'workSchedule.deleteEntry', 'workSchedule.generateMonth'):
        API_CALLS.append((action, dict(body or {})))
        return {'ok': True, 'data': {'ok': True}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag, viewer=False):
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
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body, viewer),
                                      ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t389-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t389-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# строки окна «Мероприятия»: класс прошлого + computed-фон
EV_ROWS_JS = """(function(){
    var p = document.getElementById('wsEventsPanel');
    if (!p) return { panel: false };
    var rows = p.querySelectorAll('.ws-ep-item');
    var out = [];
    rows.forEach(function(r) {
        out.push({ past: r.classList.contains('ws-ep-past'),
                   bg: getComputedStyle(r).backgroundColor,
                   txt: r.textContent.trim().slice(0, 50) });
    });
    return { panel: true, panelBg: getComputedStyle(p).backgroundColor,
             n: rows.length, rows: out };
})()"""

# страница «Работники»: ярлыки/окна/шапка/кнопка/левый край
WORKERS_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    if (!body) return null;
    var page = document.getElementById('page-ws-workers');
    var header = page ? page.querySelector('.page-inline-header') : null;
    var tabs = body.querySelectorAll('.ws-wtab');
    var tabInfo = [];
    tabs.forEach(function(t) {
        tabInfo.push({ txt: t.textContent.trim(),
                       active: t.classList.contains('active'),
                       bg: getComputedStyle(t).backgroundColor });
    });
    var gen = body.querySelector('.ws-wgen');
    var card = body.querySelector('.ws-wcard');
    var addBtn = document.getElementById('wsWorkersAddBtn');
    var layout = body.querySelector('.ws-workers-layout');
    var txt = body.textContent || '';
    return {
        headerBtn: header ? header.querySelector('.ws-workers-add') : 'no-header',
        headerBtns: header ? header.querySelectorAll('button').length : -1,
        tabs: tabInfo,
        nTabs: tabs.length,
        gen: gen ? { bg: getComputedStyle(gen).backgroundColor,
                     border: getComputedStyle(gen).borderTopWidth !== '0px' } : null,
        card: card ? getComputedStyle(card).backgroundColor : null,
        addInBody: !!(addBtn && body.contains(addBtn)),
        addTxt: addBtn ? addBtn.textContent.trim() : '',
        cur: txt.indexOf('На текущий момент: 3 работника (автоматический подсчёт).') !== -1,
        staff: txt.indexOf('По штату: 14, из которых 2 мастера, 5 сменных и 7 дневных.') !== -1,
        count: txt.indexOf('На текущий момент:') !== -1,
        layout: !!layout,
        bodyMarginLeft: getComputedStyle(body).marginLeft,
        bodyMarginRight: getComputedStyle(body).marginRight,
        leftGap: layout ? Math.round(layout.getBoundingClientRect().left -
                     page.getBoundingClientRect().left) : -1,
        bodyTxt: txt.slice(0, 300)
    };
})()"""

# смена месяца (детерминизм прошедших строк)
def switch_month(page, month, year):
    if year is not None:
        page.select_option('#wsYearSel', str(year))
        page.wait_for_timeout(400)
    page.select_option('#wsMonthSel', str(month))
    page.wait_for_timeout(1800)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'admin')

    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: табель открыт, сетка отрисована (3 работника)',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length === 3"))

    # ---------- C: окно «Мероприятия» — прошедшие = общий фон окна ----------
    ev = page.evaluate(EV_ROWS_JS)
    check('C1: окно «Мероприятия» есть, строки есть', ev['panel'] and ev['n'] >= 3,
          (ev.get('panel'), ev.get('n')))
    check('C2: фон ОКНА = var(--bg-tertiary) #0e1621 (как выше оглавления)',
          ev['panelBg'] == 'rgb(14, 22, 33)', ev['panelBg'])
    bad_past = [r for r in ev['rows'] if r['past'] and r['bg'] != 'rgba(0, 0, 0, 0)']
    check('C3: ПРОШЕДШИЕ строки — ПРОЗРАЧНЫЕ (rgba(0,0,0,0) = общий фон окна)',
          not bad_past, bad_past[:2])
    bad_cur = [r for r in ev['rows'] if not r['past'] and r['bg'] != 'rgba(0, 0, 0, 0.45)']
    check('C4: текущие/будущие — ТЕМНЕЕ окна (rgba(0,0,0,0.45)) как прежде',
          not bad_cur, bad_cur[:2])
    check('C5: есть хотя бы одна тёмная строка (идёт/будет)',
          any(not r['past'] for r in ev['rows']))
    n_past = sum(1 for r in ev['rows'] if r['past'])
    check('C6: прошедшие строки в текущем месяце есть (день 1-2 < сегодня)',
          n_past >= 1 or TODAY.day <= 2, n_past)
    page.screenshot(path='/tmp/t389-proof-events-dark.png', full_page=False)

    # ---------- D: ПРЕДЫДУЩИЙ месяц — ВСЕ строки прошедшие ----------
    switch_month(page, PM, PY if M == 1 else None)
    evp = page.evaluate(EV_ROWS_JS)
    check('D1: прошлый месяц — строки есть', evp['panel'] and evp['n'] == 2,
          evp.get('n'))
    check('D2: ВСЕ строки — класс ws-ep-past',
          evp['n'] > 0 and all(r['past'] for r in evp['rows']),
          [r['txt'] for r in evp['rows'] if not r['past']][:2])
    check('D3: ВСЕ строки ПРОЗРАЧНЫЕ (общий фон окна за прошедшими)',
          all(r['bg'] == 'rgba(0, 0, 0, 0)' for r in evp['rows']),
          [r['bg'] for r in evp['rows']][:3])
    check('D4: фон окна прежний (#0e1621)', evp['panelBg'] == 'rgb(14, 22, 33)',
          evp['panelBg'])
    page.screenshot(path='/tmp/t389-proof-events-prevmonth.png', full_page=False)
    switch_month(page, M, Y if M == 1 else None)
    check('D5: возврат в текущий месяц', page.evaluate(
        "parseInt(document.getElementById('wsMonthSel').value, 10)") == M)

    # ---------- E: страница «Работники» ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    w = page.evaluate(WORKERS_JS)
    check('E1: в ШАПКЕ страницы кнопки «Добавить работника» НЕТ',
          w['headerBtn'] is None and w['headerBtns'] == 0, (w['headerBtn'], w['headerBtns']))
    check('E2: «На текущий момент: 3 работника (автоматический подсчёт).»',
          w['cur'], w['bodyTxt'][:150])
    check('E3: «По штату: 14, из которых 2 мастера, 5 сменных и 7 дневных.»',
          w['staff'], w['bodyTxt'][:150])
    check('E4: кнопка «Добавить работника» — ВНУТРИ «Общей» вкладки',
          w['addInBody'] and w['addTxt'] == 'Добавить работника', (w['addInBody'], w['addTxt']))
    inactive = [t for t in w['tabs'] if not t['active']]
    active = [t for t in w['tabs'] if t['active']]
    check('E5: ярлыки: СПЛОШНОЙ фон неактивных #1a2233 (var(--bg-primary))',
          inactive and all(t['bg'] == 'rgb(26, 34, 51)' for t in inactive),
          [t['bg'] for t in inactive][:2])
    check('E6: активный ярлык — СПЛОШНОЙ #0e1621 (как окно вкладки)',
          active and all(t['bg'] == 'rgb(14, 22, 33)' for t in active),
          [t['bg'] for t in active][:2])
    check('E7: ОКНО «Общей» вкладки (.ws-wgen) — СПЛОШНОЙ #0e1621 + рамка',
          w['gen'] and w['gen']['bg'] == 'rgb(14, 22, 33)' and w['gen']['border'], w['gen'])
    check('E8: ни один ярлык/окно НЕ полупрозрачный (нет rgba)',
          all('rgba' not in t['bg'] for t in w['tabs']) and w['gen'] and 'rgba' not in w['gen']['bg'])
    check('E9: блок вкладок — с ЛЕВОГО КРАЯ (margin-left: 0, отступ от края страницы мал)',
          w['bodyMarginLeft'] == '0px' and w['bodyMarginRight'] == '0px' and w['leftGap'] <= 16,
          (w['bodyMarginLeft'], w['bodyMarginRight'], w['leftGap']))
    page.screenshot(path='/tmp/t389-proof-workers-general.png', full_page=False)

    # клик «Добавить работника» — шторка создания
    page.click('#wsWorkersAddBtn')
    page.wait_for_timeout(600)
    sheet_open = page.evaluate("(function(){ return {" +
        "open: document.getElementById('wsEmpSheet').classList.contains('active')," +
        "title: document.getElementById('wsEmpSheetTitle').textContent }; })()")
    check('E10: клик «Добавить работника» — шторка «Новый работник» открылась',
          sheet_open['open'] and sheet_open['title'] == 'Новый работник', sheet_open)
    page.screenshot(path='/tmp/t389-proof-add-sheet.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmployeeForm()")
    page.wait_for_timeout(500)
    check('E11: шторка закрылась', page.evaluate(
        "!document.getElementById('wsEmpSheet').classList.contains('active')"))

    # вкладка работника — карточка со сплошным фоном
    page.evaluate("document.querySelectorAll('.ws-wtab')[1].click()")
    page.wait_for_timeout(500)
    w2 = page.evaluate(WORKERS_JS)
    check('E12: вкладка работника — карточка .ws-wcard СПЛОШНАЯ (#0e1621)',
          w2['card'] == 'rgb(14, 22, 33)' and w2['gen'] is None, (w2['card'], w2['gen']))
    page.evaluate("document.querySelector('.ws-wtab-general').click()")
    page.wait_for_timeout(500)
    w3 = page.evaluate(WORKERS_JS)
    check('E13: возврат на «Общую» — панель .ws-wgen снова', w3['gen'] is not None and w3['card'] is None)

    check('F: 0 JS-ошибок (десктоп тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: десктоп 1280, СВЕТЛАЯ, Админ =================
    ctx3 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page3 = ctx3.new_page()
    js_errors3 = attach(page3, ctx3, 'light', 'light')

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    evl = page3.evaluate(EV_ROWS_JS)
    check('G1: светлая — фон окна #E9E7DE (своё правило светлой темы окна)',
          evl['panelBg'] == 'rgb(233, 231, 222)', evl['panelBg'])
    bad_past_l = [r for r in evl['rows'] if r['past'] and r['bg'] != 'rgba(0, 0, 0, 0)']
    check('G2: светлая — прошедшие ПРОЗРАЧНЫЕ', not bad_past_l, bad_past_l[:2])
    bad_cur_l = [r for r in evl['rows'] if not r['past'] and r['bg'] != 'rgba(0, 0, 0, 0.12)']
    check('G3: светлая — текущие/будущие rgba(0,0,0,0.12) как прежде',
          not bad_cur_l, bad_cur_l[:2])
    page3.screenshot(path='/tmp/t389-proof-events-light.png', full_page=False)
    switch_month(page3, PM, PY if M == 1 else None)
    evpl = page3.evaluate(EV_ROWS_JS)
    check('G4: светлая, прошлый месяц — ВСЕ прозрачные',
          evpl['n'] > 0 and all(r['past'] and r['bg'] == 'rgba(0, 0, 0, 0)'
                                for r in evpl['rows']),
          [r['bg'] for r in evpl['rows']][:3])
    switch_month(page3, M, Y if M == 1 else None)
    wl = None
    check('H: 0 JS-ошибок (десктоп светлая)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 3: мобайл 375, светлая, Админ =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 700})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'mob')

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('#wsWorkersBtn')
    page2.wait_for_timeout(1000)
    wm = page2.evaluate(WORKERS_JS)
    check('I1: мобильная «Работники» — ярлыки есть, первый «Общая»',
          wm['nTabs'] == 4 and wm['tabs'][0]['txt'] == 'Общая' and wm['tabs'][0]['active'],
          wm['tabs'][0] if wm else None)
    inactive_m = [t for t in wm['tabs'] if not t['active']]
    check('I2: мобильные ярлыки — СПЛОШНОЙ #E4E0D3 (светлая)',
          inactive_m and all(t['bg'] == 'rgb(228, 224, 211)' for t in inactive_m),
          [t['bg'] for t in inactive_m][:2])
    check('I3: ОКНО «Общей» вкладки — СПЛОШНОЙ #F0EEE6',
          wm['gen'] and wm['gen']['bg'] == 'rgb(240, 238, 230)', wm['gen'])
    check('I4: численность + штат + кнопка на «Общей» (мобайл)',
          wm['cur'] and wm['staff'] and wm['addInBody'],
          wm['bodyTxt'][:150] if wm else None)
    page2.screenshot(path='/tmp/t389-proof-mobile-workers.png', full_page=False)

    check('J: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
