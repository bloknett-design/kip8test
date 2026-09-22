#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 391: browser-check — заявка (3 части, «Общая» вкладка
# «Работников»):
#   (1) строки шапки — формат В СКОБКАХ: «Работников по штату 14
#       (2 мастера, 7 дневных, 5 сменных).» + ниже «Работников на
#       текущий момент (6) (2 мастера, 2 дневных, 2 сменных).»
#       (ведущее число = сумма категорий; запятые, не «;»);
#   (2) шрифт строк — БОЛЬШЕ и ЯРЧЕ: 14px / weight 600 / opacity
#       0.95 (было 12px / 0.75);
#   (3) кнопка «Добавить работника» — В СТИЛЕ САЙТА: тёмная тема
#       СИНИЙ #4a8fc7, светлая ОРАНЖЕВЫЙ #C6613F, текст белый,
#       hover — brightness(1.12).
# МОК: 6 работников — 2 «Мастер КИПиА» (типы сменный/дневной —
# доказательство исключения из категорий), 2 дневных, 2 сменных →
# «(6) (2 мастера, 2 дневных, 2 сменных)».
# ДЕСКТОП 1280 (тёмная, Админ): A загрузка; B табель; C «Работники»:
#   C1 штат; C2 текущий; C3 старых НЕТ; C4 порядок; C5 шрифт строк;
#   C6 кнопка СИНЯЯ с белым текстом; C7 hover-фильтр; C8 шторка
#   «Новый работник»; C9 инварианты Task 390 (шапка/примыкание);
#   C10 0 JS-ошибок.
# ДЕСКТОП 1280 (светлая, Админ): D1-D5 (тексты; кнопка ОРАНЖЕВАЯ
#   #C6613F с белым текстом; шапка #E4E0D3 жива; шрифт; 0 ошибок).
# МОБАЙЛ 375 (светлая, Админ): E лента ярлыков + тексты + кнопка;
#   F 0 JS-ошибок.
# Порт 9004 (запуск: python3 -m http.server 9004 &).
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9004
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

# 6 работников: мастера с РАЗНЫМИ типами (в категории
# сменных/дневных НЕ попадают), 2 дневных, 2 сменных
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
        return {'ok': True, 'data': {'trainings': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
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
                      body='not found (t391-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t391-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# страница «Работники»: тексты/шрифт/кнопка/инварианты Task 390
WORKERS_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    if (!body) return null;
    var txt = body.textContent || '';
    var staff = body.querySelector('.ws-wgen-staff');
    var count = body.querySelector('.ws-workers-count');
    var head = body.querySelector('.ws-wgen-head');
    var addBtn = document.getElementById('wsWorkersAddBtn');
    var wtabs = body.querySelector('.ws-wtabs');
    var win = body.querySelector('.ws-wtab-body > *');
    function cs(el, prop) { return el ? getComputedStyle(el)[prop] : null; }
    return {
        staff: txt.indexOf('Работников по штату 14 (2 мастера, 7 дневных, 5 сменных).') !== -1,
        cur: txt.indexOf('Работников на текущий момент (6) (2 мастера, 2 дневных, 2 сменных).') !== -1,
        oldColon: txt.indexOf('Работников по штату 14:') !== -1 ||
                  txt.indexOf('Работников на текущий момент:') !== -1,
        oldSemi: txt.indexOf('2 мастера; 7 дневных') !== -1 ||
                 txt.indexOf('2 мастера; 2 дневных') !== -1,
        orderOk: txt.indexOf('Работников по штату') < txt.indexOf('Работников на текущий момент'),
        staffFont: staff ? { size: cs(staff,'fontSize'), weight: cs(staff,'fontWeight'),
                             op: cs(staff,'opacity') } : null,
        countFont: count ? { size: cs(count,'fontSize'), weight: cs(count,'fontWeight'),
                             op: cs(count,'opacity') } : null,
        head: head ? { bg: cs(head,'backgroundColor'), hasBtn: !!(addBtn && head.contains(addBtn)) } : null,
        btn: addBtn ? { bg: cs(addBtn,'backgroundColor'), color: cs(addBtn,'color'),
                        border: cs(addBtn,'borderTopColor'), txt: addBtn.textContent.trim(),
                        inBody: !!body.contains(addBtn) } : null,
        gap: (wtabs && win) ? Math.round(win.getBoundingClientRect().left -
                                        wtabs.getBoundingClientRect().right) : null,
        bodyTxt: txt.slice(0, 260)
    };
})()"""

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
    check('B: табель открыт, сетка отрисована (6 работников)',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length === 6"))

    # ---------- C: страница «Работники» — «Общая» вкладка ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    w = page.evaluate(WORKERS_JS)
    check('C1: «Работников по штату 14 (2 мастера, 7 дневных, 5 сменных).»',
          w['staff'], w['bodyTxt'][:200])
    check('C2: «Работников на текущий момент (6) (2 мастера, 2 дневных, 2 сменных).» — итог = сумма',
          w['cur'], w['bodyTxt'][:200])
    check('C3: старых формулировок НЕТ (двоеточия и «;»)',
          not w['oldColon'] and not w['oldSemi'],
          (w['oldColon'], w['oldSemi']))
    check('C4: штат — ПЕРВОЙ строчкой, текущий — ниже',
          w['orderOk'], w['bodyTxt'][:200])
    check('C5: шрифт строк — 14px / 600 / 0.95 (БОЛЬШЕ и ЯРЧЕ, было 12px/0.75)',
          w['staffFont'] and w['staffFont']['size'] == '14px' and
          w['staffFont']['weight'] == '600' and w['staffFont']['op'] == '0.95' and
          w['countFont'] and w['countFont']['size'] == '14px' and
          w['countFont']['weight'] == '600' and w['countFont']['op'] == '0.95',
          (w['staffFont'], w['countFont']))
    check('C6: кнопка — СИНЯЯ #4a8fc7 (var(--accent-blue), тёмная тема) с БЕЛЫМ текстом',
          w['btn'] and w['btn']['bg'] == 'rgb(74, 143, 199)' and
          w['btn']['color'] == 'rgb(255, 255, 255)' and
          w['btn']['txt'] == 'Добавить работника' and w['btn']['inBody'],
          w['btn'])
    page.hover('#wsWorkersAddBtn')
    page.wait_for_timeout(300)
    hov = page.evaluate("(function(){ var b = document.getElementById('wsWorkersAddBtn');" +
                        "return b ? getComputedStyle(b).filter : null; })()")
    check('C7: hover кнопки — фильтр brightness(1.12)',
          hov == 'brightness(1.12)', hov)
    page.screenshot(path='/tmp/t391-proof-workers-dark.png', full_page=False)

    # клик «Добавить работника» — шторка создания
    page.click('#wsWorkersAddBtn')
    page.wait_for_timeout(600)
    sheet_open = page.evaluate("(function(){ return {" +
        "open: document.getElementById('wsEmpSheet').classList.contains('active')," +
        "title: document.getElementById('wsEmpSheetTitle').textContent }; })()")
    check('C8: клик «Добавить работника» — шторка «Новый работник»',
          sheet_open['open'] and sheet_open['title'] == 'Новый работник', sheet_open)
    page.screenshot(path='/tmp/t391-proof-add-sheet.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmployeeForm()")
    page.wait_for_timeout(500)

    # инварианты Task 390: выделенная шапка + примыкание ярлыков
    check('C9: инварианты Task 390 — шапка #1E2B42 с кнопкой + примыкание (щель 0)',
          w['head'] and w['head']['bg'] == 'rgb(30, 43, 66)' and
          w['head']['hasBtn'] and w['gap'] is not None and abs(w['gap']) <= 1,
          (w['head'], w['gap']))

    check('C10: 0 JS-ошибок (десктоп тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: десктоп 1280, СВЕТЛАЯ, Админ =================
    ctx3 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page3 = ctx3.new_page()
    js_errors3 = attach(page3, ctx3, 'light', 'light')

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.click('#wsWorkersBtn')
    page3.wait_for_timeout(1000)
    wl = page3.evaluate(WORKERS_JS)
    check('D1: светлая — тексты в новом формате',
          wl['staff'] and wl['cur'] and not wl['oldColon'] and not wl['oldSemi'],
          wl['bodyTxt'][:200])
    check('D2: светлая — кнопка ОРАНЖЕВАЯ #C6613F (var(--accent-blue) светлой темы), текст белый',
          wl['btn'] and wl['btn']['bg'] == 'rgb(198, 97, 63)' and
          wl['btn']['color'] == 'rgb(255, 255, 255)',
          wl['btn'])
    check('D3: светлая — шапка #E4E0D3 (инвариант Task 390)',
          wl['head'] and wl['head']['bg'] == 'rgb(228, 224, 211)', wl['head'])
    check('D4: светлая — шрифт строк 14px / 600 / 0.95',
          wl['staffFont'] and wl['staffFont']['size'] == '14px' and
          wl['staffFont']['weight'] == '600' and wl['staffFont']['op'] == '0.95',
          wl['staffFont'])
    page3.screenshot(path='/tmp/t391-proof-workers-light.png', full_page=False)
    check('D5: 0 JS-ошибок (десктоп светлая)', len(js_errors3) == 0, js_errors3[:3])
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
    tabs_row = page2.evaluate("(function(){ var t = document.querySelector('.ws-wtabs');" +
                              "return t ? getComputedStyle(t).flexDirection : null; })()")
    check('E1: мобайл — ярлыки горизонтальной лентой; тексты нового формата',
          tabs_row == 'row' and wm['staff'] and wm['cur'],
          (tabs_row, wm['bodyTxt'][:150]))
    check('E2: мобайл — кнопка ОРАНЖЕВАЯ #C6613F в шапке, текст белый',
          wm['btn'] and wm['btn']['bg'] == 'rgb(198, 97, 63)' and
          wm['btn']['color'] == 'rgb(255, 255, 255)' and wm['btn']['inBody'],
          wm['btn'])
    page2.screenshot(path='/tmp/t391-proof-mobile-workers.png', full_page=False)

    check('F: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
