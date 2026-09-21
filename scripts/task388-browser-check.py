#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 388: browser-check — заявка (5 частей):
#   (1) миниатюры мероприятий ВСЕГДА сплошные с фоном ЦВЕТА КОДА:
#       «*» (примечание) на дополнительно установленном выходном дне —
#       КРАСНЫЙ фон (прежде — прозрачный пунктир);
#   (2) панель «Обозначения» в КРАТКОМ виде — краткие обозначения
#       кодов по порядку заявки («Д8 — день 8ч» … «* — не плановый»);
#   (3) итоги учёта в видах «только сменный»/«только дневной»;
#   (4) значок раскрытия окон «Мероприятия»/«Нормы» — правый ВЕРХНИЙ
#       угол, БЕЗ смещения при раскрытии;
#   (5) страница «Работники» — вкладки-ярлыки СТОЛБИКОМ СЛЕВА:
#       «Общая» (сводка всех) + работники ПО ФАМИЛЬНО ПО АЛФАВИТУ.
# ДЕСКТОП 1280 (тёмная, Админ):
#   A  загрузка; B табель;
#   C  «Обозначения» краткий вид: ~230px, краткие обозначения ВИДНЫ
#      («Д8 — день 8ч», «— день в выходной», «— не плановый»), полные
#      имена СКРЫТЫ, «Выходной» — строка со свотчем-пустышкой и «—
#      выходной», 16 строк, секции «Коды дней (Т-12/Т-13)»/«Коды
#      мероприятий»;
#   D  шеврон → разворот ~500px: краткие СКРЫТЫ, полные имена ВИДНЫ;
#      сворачивание → ~230px;
#   E  СЕТКА: «*» на ПУСТОМ дне (дополнительно установленный выходной)
#      — бейдж БЕЗ ws-ev-pending, фон #FFAB91 (цвет кода листа);
#      легаси-«.»-день — тоже сплошной;
#   F  вид «сменный»: кнопка «Итоги учёта» ВИДИМА, шторка ОТКРЫВАЕТСЯ,
#      строки — только сменные (Иванов/Сидорова, БЕЗ Петрова);
#   G  вид «дневной»: шторка ПЕРЕРИСОВАНА — только Петров;
#      возврат в полный — все трое;
#   H  окно «Мероприятия»: значок .ws-bar-exp в ПРАВОМ ВЕРХНЕМ углу;
#      клик — окно раскрылось (ws-bar-open), ВЕРХ значка НЕ СМЕСТИЛСЯ;
#   I  страница «Работники»: ярлыки СТОЛБИКОМ СЛЕВА (вертикально),
#      первый «Общая», порядок ПО ФАМИЛЬНО ПО АЛФАВИТУ; «Общая» —
#      сводная таблица (все трое); клик по ярлыку — карточка
#      («Правка данных…»); возврат на «Общую»;
#   J  0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ):
#   K  «Обозначения» — страница: полные имена, краткие СКРЫТЫ;
#   L  «Работники» — ярлыки ГОРИЗОНТАЛЬНОЙ лентой сверху;
#   M  «*»-бейдж сплошной и в мобильной сетке; N 0 JS-ошибок.
# Порт 8998 (запуск: python3 -m http.server 8998 &).
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

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
# «*» (примечание) на ПУСТОМ дне 8 (дополнительно установленный
# выходной — записи нет) + лента мероприятий для переполнения окна
TRAININGS = [
  {'id': 101, 'таб_номер': '017', 'тип': 'примечание', 'тема': 'принят на смену',
   'дата_начала': d(8), 'дата_окончания': d(8), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 102, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Повторный инструктаж по охране труда',
   'дата_начала': d(3), 'дата_окончания': d(3), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 103, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Целевой инструктаж перед работами',
   'дата_начала': d(5), 'дата_окончания': d(5), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 104, 'таб_номер': '017', 'тип': 'обучение', 'тема': 'Обучение по промбезопасности',
   'дата_начала': d(9), 'дата_окончания': d(9), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 105, 'таб_номер': '023', 'тип': 'инструктаж', 'тема': 'Повторный инструктаж',
   'дата_начала': d(4), 'дата_окончания': d(4), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 106, 'таб_номер': '023', 'тип': 'проверка_знаний', 'тема': 'Проверка знаний до 1000В',
   'дата_начала': d(11), 'дата_окончания': d(11), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 107, 'таб_номер': '045', 'тип': 'инструктаж', 'тема': 'Вводный инструктаж',
   'дата_начала': d(6), 'дата_окончания': d(6), 'длительность_дней': 1, 'комментарий': ''},
  {'id': 108, 'таб_номер': '045', 'тип': 'примечание', 'тема': 'допуск к работам',
   'дата_начала': d(12), 'дата_окончания': d(12), 'длительность_дней': 1, 'комментарий': ''},
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
# день 5 — смена Д (сформирован), день 6 — легаси-«.» (руч), день 8 —
# ПУСТОЙ (дополнительно установленный выходной) с «*»-мероприятием
ENTRIES = [
  {'id': 1, 'дата': d(5), 'таб_номер': '017', 'статус': 'Д',
   'источник': 'авто', 'переработка': 0, 'праздник': 0},
  {'id': 2, 'дата': d(6), 'таб_номер': '017', 'статус': '.',
   'источник': 'руч', 'переработка': 0, 'праздник': 0},
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
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body, viewer),
                                      ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t388-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t388-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# состояние панели «Обозначения» + строки кодов
LEGEND_JS = """(function(){
    var d = document.getElementById('wsLegendDrawer');
    var b = document.getElementById('wsLegendBtn');
    var body = document.getElementById('wsLegendBody');
    var rows = body ? body.querySelectorAll('.ws-lg-item') : [];
    var firstShort = body ? body.querySelector('.ws-lg-short') : null;
    var firstName = body ? body.querySelector('.ws-lg-name') : null;
    var r = d.getBoundingClientRect();
    var codes = [];
    for (var i = 0; i < rows.length; i++) {
        var c = rows[i].querySelector('.ws-lg-code');
        var sw = rows[i].querySelector('.ws-lg-swatch');
        var sh = rows[i].querySelector('.ws-lg-short');
        codes.push({
            code: c ? c.textContent : '',
            dotSw: sw ? sw.classList.contains('ws-lg-swatch-dot') : false,
            short: sh ? sh.textContent : ''
        });
    }
    return {
        pressed: b ? b.getAttribute('aria-pressed') : 'none',
        slot: Math.round(r.width),
        right: Math.round(r.right),
        nRows: rows.length,
        codes: codes,
        shortVisible: !!(firstShort && getComputedStyle(firstShort).display !== 'none'),
        shortTxt: firstShort ? firstShort.textContent : '',
        nameVisible: !!(firstName && getComputedStyle(firstName).display !== 'none'),
        bodyTxt: body ? body.textContent : ''
    };
})()"""

# бейдж мероприятия в ячейке дня месяца (td[data-day])
CELL_BADGE_JS = """(function(day){
    var cells = document.querySelectorAll('#wsGridWrap td.ws-cell[data-day="' + day + '"]');
    for (var i = 0; i < cells.length; i++) {
        var b = cells[i].querySelector('.ws-ev-badge');
        if (!b) continue;
        return {
            found: true,
            text: b.textContent,
            cls: b.className,
            bg: (b.getAttribute('style') || '')
        };
    }
    return { found: false };
})(%s)"""

# сетка: список строк-работников (ФИО колонка)
GRID_ROWS_JS = """(function(){
    var out = [];
    document.querySelectorAll('#wsGridWrap td.ws-emp-col').forEach(function(td) {
        out.push(td.textContent.trim());
    });
    return out;
})()"""

# строки таблицы итогов (шторка)
TT_ROWS_JS = """(function(){
    var body = document.getElementById('wsTtBody');
    if (!body) return [];
    var t = body.querySelector('.ws-tt-table tbody');
    if (!t) return [];
    var out = [];
    t.querySelectorAll('tr').forEach(function(tr) {
        var n = tr.querySelector('.ws-tt-name');
        out.push(n ? n.textContent.trim() : tr.textContent.trim().slice(0, 30));
    });
    return out;
})()"""

# вкладки страницы «Работники»
WORKERS_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    var layout = body ? body.querySelector('.ws-workers-layout') : null;
    var tabs = body ? body.querySelectorAll('.ws-wtab') : [];
    var tabRects = [];
    tabs.forEach(function(t) {
        var r = t.getBoundingClientRect();
        tabRects.push({ txt: t.textContent.trim(), top: Math.round(r.top),
                        left: Math.round(r.left), w: Math.round(r.width),
                        active: t.classList.contains('active') });
    });
    var gen = body ? body.querySelector('.ws-wgen-table') : null;
    var card = body ? body.querySelector('.ws-wcard') : null;
    var bodyTxt = body ? body.textContent : '';
    return {
        layout: !!layout,
        nTabs: tabs.length,
        tabs: tabRects,
        vertical: tabRects.length > 1 &&
            tabRects[1].top > tabRects[0].top + 10,
        horizontal: tabRects.length > 1 &&
            Math.abs(tabRects[1].top - tabRects[0].top) < 10 &&
            tabRects[1].left > tabRects[0].left,
        genTable: !!gen,
        genRows: gen ? gen.querySelectorAll('tbody tr').length : 0,
        card: !!card,
        editBtn: bodyTxt.indexOf('Правка данных…') !== -1,
        addBtn: !!document.getElementById('wsWorkersAddBtn'),
        addTxt: (function() { var b = document.getElementById('wsWorkersAddBtn');
                              return b ? b.textContent.trim() : ''; })(),
        count: bodyTxt.indexOf('3 ') !== -1,
        bodyTxt: bodyTxt.slice(0, 400)
    };
})()"""

# значок раскрытия окна бара
BAR_EXP_JS = """(function(id){
    var p = document.getElementById(id);
    if (!p) return { panel: false };
    var btn = p.querySelector('.ws-bar-exp');
    var pr = p.getBoundingClientRect();
    if (!btn) return { panel: true, btn: false, panelRect: { top: Math.round(pr.top),
                         bottom: Math.round(pr.bottom), h: Math.round(pr.height) },
                       open: p.classList.contains('ws-bar-open') };
    var br = btn.getBoundingClientRect();
    return { panel: true, btn: true,
             visible: getComputedStyle(btn).display !== 'none',
             top: Math.round(br.top), left: Math.round(br.left),
             panelTop: Math.round(pr.top), panelBottom: Math.round(pr.bottom),
             open: p.classList.contains('ws-bar-open') };
})(%s)"""


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

    # ---------- C: «Обозначения» — КРАТКИЙ вид с краткими обозначениями ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(700)
    lg = page.evaluate(LEGEND_JS)
    check('C1: шторка открыта (aria-pressed=true)', lg['pressed'] == 'true', lg['pressed'])
    check('C2: КРАТКИЙ вид — слот ~230px', 220 <= lg['slot'] <= 240, lg['slot'])
    check('C3: краткие обозначения ВИДНЫ', lg['shortVisible'])
    check('C4: полные наименования СКРЫТЫ', not lg['nameVisible'])
    check('C5: 16 строк-кодов', lg['nRows'] == 16, lg['nRows'])
    seq = [c['code'] for c in lg['codes']]
    check('C6: порядок заявки — Д8 первым, события в конце',
          seq[0] == 'Д8' and seq[15] == '*', seq[:5])
    body_txt = lg['bodyTxt']
    check('C7: «Д8 — день 8ч» (краткое обозначение)',
          '— день 8ч' in body_txt and '— день 7,2ч' in body_txt)
    check('C8: «д — день в выходной», «н — ночь в выходной»',
          '— день в выходной' in body_txt and '— ночь в выходной' in body_txt)
    check('C9: «ОТ — отпуск … Б — больничный»',
          '— отпуск' in body_txt and '— отгул' in body_txt and '— больничный' in body_txt)
    wykh = lg['codes'][10]
    check('C10: «Выходной» — свотч-пустышка + «— выходной»',
          wykh['dotSw'] and wykh['code'] == '' and '— выходной' in body_txt, wykh)
    check('C11: «ПР — прогул … * — не плановый»',
          '— прогул' in body_txt and '— инструктаж' in body_txt and
          '— обучение' in body_txt and '— проверка знаний' in body_txt and
          '— не плановый' in body_txt)
    check('C12: секции «Коды дней (Т-12/Т-13)» / «Коды мероприятий»',
          'Коды дней (Т-12/Т-13)' in body_txt and 'Коды мероприятий' in body_txt)
    page.screenshot(path='/tmp/t388-proof-legend-short.png', full_page=False)

    # ---------- D: разворот/сворачивание ----------
    page.click('#wsLgChv')
    page.wait_for_timeout(700)
    lgw = page.evaluate(LEGEND_JS)
    check('D1: разворот — слот ~500px', 490 <= lgw['slot'] <= 510, lgw['slot'])
    check('D2: полные имена ВИДНЫ, краткие СКРЫТЫ',
          lgw['nameVisible'] and not lgw['shortVisible'])
    check('D3: полное наименование Д8 (заявка Task 387 жива)',
          'на час короче' in lgw['bodyTxt'])
    page.click('#wsLgChv')
    page.wait_for_timeout(700)
    lgn = page.evaluate(LEGEND_JS)
    check('D4: свёрнута — ~230px, краткие видны',
          220 <= lgn['slot'] <= 240 and lgn['shortVisible'], lgn['slot'])
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)

    # ---------- E: СЕТКА — «*» на пустом дне: КРАСНЫЙ (цвет кода) фон ----------
    badge = page.evaluate(CELL_BADGE_JS % 8)
    check('E1: «*»-бейдж на дне 8 (пустой/выходной) найден', badge['found'], badge)
    check('E2: бейдж СПЛОШНОЙ (без ws-ev-pending)',
          badge['found'] and 'ws-ev-pending' not in badge.get('cls', ''),
          badge.get('cls'))
    check('E3: фон бейджа — ЦВЕТ КОДА «*» (#FFAB91, не прозрачный)',
          badge['found'] and 'background:#FFAB91' in badge.get('bg', ''), badge.get('bg'))
    check('E4: текст бейджа — «*»', badge['found'] and badge.get('text') == '*', badge.get('text'))
    badge6 = page.evaluate(CELL_BADGE_JS % 6)
    check('E5: легаси-«.»-день — тот же сплошной бейдж (если есть)',
          (not badge6['found']) or ('ws-ev-pending' not in badge6['cls']), badge6)

    # ---------- F: вид «сменный» — итоги доступны ----------
    page.click('#wsViewBtn')          # full → shift
    page.wait_for_timeout(1200)
    rows = page.evaluate(GRID_ROWS_JS)
    check('F1: сетка сменного вида — только сменные (Иванов, Сидорова)',
          any('Иванов' in r for r in rows) and any('Сидорова' in r for r in rows)
          and not any('Петров' in r for r in rows), rows)
    check('F2: кнопка «Итоги учёта» ВИДИМА в сменном виде',
          page.evaluate("!document.getElementById('wsTotalsBtn').hidden"))
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(1200)
    check('F3: шторка итогов ОТКРЫЛАСЬ в сменном виде',
          page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')"))
    ttRows = page.evaluate(TT_ROWS_JS)
    check('F4: строки итогов — только сменные',
          any('Иванов' in r for r in ttRows) and any('Сидорова' in r for r in ttRows)
          and not any('Петров' in r for r in ttRows), ttRows)
    page.screenshot(path='/tmp/t388-proof-totals-shift.png', full_page=False)

    # ---------- G: вид «дневной» — шторка перерисована ----------
    page.click('#wsViewBtn')          # shift → day (шторка остаётся)
    page.wait_for_timeout(1500)
    check('G1: шторка ОСТАЛАСЬ открытой при смене вида',
          page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')"))
    ttRows2 = page.evaluate(TT_ROWS_JS)
    check('G2: строки итогов дневного вида — только Петров',
          any('Петров' in r for r in ttRows2) and not any('Иванов' in r for r in ttRows2)
          and not any('Сидорова' in r for r in ttRows2), ttRows2)
    page.click('#wsViewBtn')          # day → full
    page.wait_for_timeout(1500)
    ttRows3 = page.evaluate(TT_ROWS_JS)
    check('G3: полный вид — все трое в итогах',
          any('Иванов' in r for r in ttRows3) and any('Петров' in r for r in ttRows3)
          and any('Сидорова' in r for r in ttRows3), ttRows3)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(700)

    # ---------- H: окна бара — значок в ПРАВОМ ВЕРХНЕМ углу ----------
    ev1 = page.evaluate(BAR_EXP_JS % "'wsEventsPanel'")
    check('H1: окно «Мероприятия» есть', ev1['panel'])
    check('H2: значок .ws-bar-exp есть и ВИДЕН (текст переполняет)',
          ev1['btn'] and ev1['visible'], ev1)
    if ev1['btn'] and ev1['visible']:
        check('H3: значок в ПРАВОМ ВЕРХНЕМ углу (top ≈ panelTop)',
              ev1['top'] - ev1['panelTop'] <= 12, (ev1['top'], ev1['panelTop']))
        top_before = ev1['top']
        page.click('#wsEventsPanel .ws-bar-exp')
        page.wait_for_timeout(500)
        ev2 = page.evaluate(BAR_EXP_JS % "'wsEventsPanel'")
        check('H4: клик — окно РАСКРЫТО (ws-bar-open)', ev2['open'])
        check('H5: ВЕРХ значка НЕ СМЕСТИЛСЯ при раскрытии',
              abs(ev2['top'] - top_before) <= 2, (top_before, ev2['top']))
        check('H6: окно выросло ВНИЗ (низ уехал)',
              ev2['panelBottom'] > ev1['panelBottom'], (ev1['panelBottom'], ev2['panelBottom']))
        page.screenshot(path='/tmp/t388-proof-bar-exp-top.png', full_page=False)
        page.click('#wsEventsPanel .ws-bar-exp')
        page.wait_for_timeout(500)
        ev3 = page.evaluate(BAR_EXP_JS % "'wsEventsPanel'")
        check('H7: сворачивание — верх значка на месте',
              abs(ev3['top'] - top_before) <= 2, (top_before, ev3['top']))
    cal1 = page.evaluate(BAR_EXP_JS % "'wsCalPanel'")
    check('H8: окно «Нормы» — значок в правом верхнем углу (если виден)',
          (not (cal1['btn'] and cal1['visible'])) or (cal1['top'] - cal1['panelTop'] <= 12),
          cal1)

    # ---------- I: страница «Работники» — вкладки-ярлыки ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    w = page.evaluate(WORKERS_JS)
    check('I1: раскладка вкладок есть', w['layout'])
    check('I2: ярлыков 4 (Общая + трое)', w['nTabs'] == 4, w['nTabs'])
    check('I3: первый ярлык — «Общая» (активен)',
          w['tabs'][0]['txt'] == 'Общая' and w['tabs'][0]['active'], w['tabs'][0])
    order = [t['txt'] for t in w['tabs']]
    check('I4: ПО ФАМИЛЬНО ПО АЛФАВИТУ: Иванов → Петров → Сидорова',
          order[1:4] == ['Иванов И. И.', 'Петров П. П.', 'Сидорова А. А.'], order)
    check('I5: ярлыки СТОЛБИКОМ (вертикально, слева)',
          w['vertical'] and w['tabs'][1]['left'] < 300, w['tabs'][:3])
    check('I6: «Общая» — сводная таблица (3 строки)', w['genTable'] and w['genRows'] == 3,
          (w['genTable'], w['genRows']))
    check('I7: счётчик «3 работника»', w['count'])
    check('I8: кнопка «Добавить работника» жива (регресс 386)',
          w['addBtn'] and w['addTxt'] == 'Добавить работника', w['addTxt'])
    page.screenshot(path='/tmp/t388-proof-workers-general.png', full_page=False)
    # клик по ярлыку Иванова
    page.evaluate("document.querySelectorAll('.ws-wtab')[1].click()")
    page.wait_for_timeout(500)
    w2 = page.evaluate(WORKERS_JS)
    check('I9: вкладка Иванова — полная карточка', w2['card'] and w2['editBtn'])
    check('I10: одна карточка (не все сразу)',
          page.evaluate("document.querySelectorAll('#wsWorkersBody .ws-wcard').length === 1"))
    check('I11: заголовок карточки — Иванов',
          'Иванов И. И.' in w2['bodyTxt'], w2['bodyTxt'][:80])
    page.screenshot(path='/tmp/t388-proof-workers-tab.png', full_page=False)
    # возврат на «Общую»
    page.evaluate("document.querySelector('.ws-wtab-general').click()")
    page.wait_for_timeout(500)
    w3 = page.evaluate(WORKERS_JS)
    check('I12: возврат на «Общую» — сводная таблица', w3['genTable'] and not w3['card'])

    check('J: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, светлая, Админ =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 700})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'mob')

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    check('K0: мобильный табель открыт',
          page2.evaluate("!!document.querySelector('#page-work-schedule .ws-grid')"))

    # ---------- K: «Обозначения» — страница с полными именами ----------
    page2.click('#wsLegendBtn')
    page2.wait_for_timeout(1000)
    check('K1: мобильная страница ws-legend открыта',
          page2.evaluate("document.getElementById('page-ws-legend').classList.contains('active')"))
    lgm = page2.evaluate("""(function(){
        var body = document.getElementById('wsLgPageBody');
        if (!body) return null;
        var sh = body.querySelector('.ws-lg-short');
        var nm = body.querySelector('.ws-lg-name');
        return {
            shortHidden: !sh || getComputedStyle(sh).display === 'none',
            nameVisible: !!nm && getComputedStyle(nm).display !== 'none',
            txt: body.textContent
        };
    })()""")
    check('K2: полные имена ВИДНЫ, краткие СКРЫТЫ (страница)',
          lgm['nameVisible'] and lgm['shortHidden'])
    check('K3: «на час короче» (полная формулировка)', 'на час короче' in lgm['txt'])
    check('K4: ВСЕ краткие обозначения на странице скрыты CSS',
          page2.evaluate("(function(){ var all = document.querySelectorAll('#wsLgPageBody .ws-lg-short'); " +
                         "if (!all.length) return false; " +
                         "for (var i = 0; i < all.length; i++) " +
                         "  if (getComputedStyle(all[i]).display !== 'none') return false; " +
                         "return true; })()"))
    page2.screenshot(path='/tmp/t388-proof-mobile-legend.png', full_page=False)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(800)
    page2.click('#wsWorkersBtn')
    page2.wait_for_timeout(1000)
    wm = page2.evaluate(WORKERS_JS)
    check('L1: мобильная страница «Работники» — вкладки есть', wm['layout'])
    check('L2: ярлыки ГОРИЗОНТАЛЬНОЙ лентой (в ряд сверху)',
          wm['horizontal'], wm['tabs'][:3])
    check('L3: первый — «Общая», порядок фамильный',
          wm['tabs'][0]['txt'] == 'Общая' and
          [t['txt'] for t in wm['tabs']][1:4] == ['Иванов И. И.', 'Петров П. П.', 'Сидорова А. А.'])
    page2.screenshot(path='/tmp/t388-proof-mobile-workers.png', full_page=False)

    # ---------- M: «*»-бейдж в мобильной сетке ----------
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1500)
    badgeM = page2.evaluate(CELL_BADGE_JS % 8)
    check('M1: «*»-бейдж сплошной и в мобильной сетке (#FFAB91)',
          badgeM['found'] and 'background:#FFAB91' in badgeM.get('bg', '')
          and 'ws-ev-pending' not in badgeM['cls'], badgeM)

    check('N: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
