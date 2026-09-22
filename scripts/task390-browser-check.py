#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 390: browser-check — заявка (5 частей, «Общая» вкладка
# «Работников»):
#   (1) «Сводка по всем работникам…» УБРАНА;
#   (2) «Работников по штату 14: 2 мастера; 7 дневных; 5 сменных.»
#       (константа) + ниже «Работников на текущий момент: (N)
#       мастера; (N) дневных; (N) сменных.» — АВТОПОДСЧЁТ ПО
#       КАТЕГОРИЯМ (мастера — должность «Мастер КИПиА», исключены
#       из сменных/дневных);
#   (3) шапка с надписями и кнопкой — ВЫДЕЛЕННЫЙ фон;
#   (4) ярлыки ПРИМЫКАЮТ к окну вкладок (щель справа убрана);
#   (5) тёмная тема: ярлыки светлее + тёплый тон (#4B4E46/
#       #575A50/#63665B) — не сливаются с фоном страницы.
# МОК: 6 работников — 2 «Мастер КИПиА» (типы сменный/дневной —
# доказательство исключения из категорий), 2 дневных, 2 сменных →
# «2 мастера; 2 дневных; 2 сменных».
# ДЕСКТОП 1280 (тёмная, Админ): A загрузка; B табель; C «Работники»:
#   C1 штат; C2 текущий; C3 старых НЕТ; C4 шапка выделена +
#   кнопка в шапке; C5 ярлыки тёплые светлые; C6 активный светлее;
#   C7 примыкание (щель 0); C8 hover; C9 шторка «Новый работник»;
#   C10 вкладка работника/возврат; C11 0 JS-ошибок.
# ДЕСКТОП 1280 (светлая, Админ): D1-D5 (ярлыки #E4E0D3, активный
#   #F0EEE6, шапка #E4E0D3, тексты, примыкание; 0 ошибок).
# МОБАЙЛ 375 (светлая, Админ): E лента ярлыков + тексты + кнопка;
#   F 0 JS-ошибок.
# Порт 9002 (запуск: python3 -m http.server 9002 &).
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9002
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
                      body='not found (t390-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t390-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# страница «Работники»: тексты/шапка/ярлыки/примыкание
WORKERS_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    if (!body) return null;
    var txt = body.textContent || '';
    var tabs = body.querySelectorAll('.ws-wtab');
    var tabInfo = [];
    tabs.forEach(function(t) {
        tabInfo.push({ txt: t.textContent.trim(),
                       active: t.classList.contains('active'),
                       bg: getComputedStyle(t).backgroundColor });
    });
    var head = body.querySelector('.ws-wgen-head');
    var addBtn = document.getElementById('wsWorkersAddBtn');
    var wtabs = body.querySelector('.ws-wtabs');
    var win = body.querySelector('.ws-wtab-body > *');
    var gen = body.querySelector('.ws-wgen');
    var card = body.querySelector('.ws-wcard');
    return {
        staff: txt.indexOf('Работников по штату 14: 2 мастера; 7 дневных; 5 сменных.') !== -1,
        cur: txt.indexOf('Работников на текущий момент: 2 мастера; 2 дневных; 2 сменных.') !== -1,
        oldCur: txt.indexOf('На текущий момент:') !== -1,
        oldStaff: txt.indexOf('По штату: 14, из которых') !== -1,
        note: txt.indexOf('Сводка по всем работникам') !== -1,
        orderOk: txt.indexOf('Работников по штату') < txt.indexOf('Работников на текущий момент'),
        tabs: tabInfo,
        nTabs: tabs.length,
        head: head ? { bg: getComputedStyle(head).backgroundColor,
                       borderW: getComputedStyle(head).borderTopWidth,
                       radius: getComputedStyle(head).borderTopLeftRadius,
                       hasBtn: !!(addBtn && head.contains(addBtn)) } : null,
        addInBody: !!(addBtn && body.contains(addBtn)),
        addTxt: addBtn ? addBtn.textContent.trim() : '',
        gen: gen ? { bg: getComputedStyle(gen).backgroundColor } : null,
        card: card ? getComputedStyle(card).backgroundColor : null,
        gap: (wtabs && win) ? Math.round(win.getBoundingClientRect().left -
                                        wtabs.getBoundingClientRect().right) : null,
        tabsRow: wtabs ? getComputedStyle(wtabs).flexDirection : null,
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
    check('C1: «Работников по штату 14: 2 мастера; 7 дневных; 5 сменных.»',
          w['staff'], w['bodyTxt'][:200])
    check('C2: «Работников на текущий момент: 2 мастера; 2 дневных; 2 сменных.» (мастера исключены из типов)',
          w['cur'], w['bodyTxt'][:200])
    check('C3: старых формулировок и сноски НЕТ',
          not w['oldCur'] and not w['oldStaff'] and not w['note'],
          (w['oldCur'], w['oldStaff'], w['note']))
    check('C4: штат — ПЕРВОЙ строчкой, текущий — ниже',
          w['orderOk'], w['bodyTxt'][:200])
    check('C5: шапка ВЫДЕЛЕНА — фон #1E2B42 + рамка + радиус + кнопка в шапке',
          w['head'] and w['head']['bg'] == 'rgb(30, 43, 66)' and
          w['head']['borderW'] == '1px' and w['head']['hasBtn'],
          w['head'])
    inactive = [t for t in w['tabs'] if not t['active']]
    active = [t for t in w['tabs'] if t['active']]
    check('C6: ярлыки ТЁПЛЫЕ светлые #4B4E46 (НЕ фон страницы #1a2233)',
          inactive and all(t['bg'] == 'rgb(75, 78, 70)' for t in inactive),
          [t['bg'] for t in inactive][:2])
    check('C7: активный ярлык — самый светлый тёплый #63665B',
          active and all(t['bg'] == 'rgb(99, 102, 91)' for t in active),
          [t['bg'] for t in active][:2])
    check('C8: ПРИМЫКАНИЕ — ярлыки вплотную к окну вкладки (щель 0)',
          w['gap'] is not None and abs(w['gap']) <= 1, w['gap'])
    page.screenshot(path='/tmp/t390-proof-workers-dark.png', full_page=False)

    # hover по неактивному ярлыку — тёплый светлее
    page.hover('.ws-wtab:not(.active)')
    page.wait_for_timeout(300)
    hov = page.evaluate("(function(){ var t = document.querySelector('.ws-wtab:hover'); " +
                        "return t ? getComputedStyle(t).backgroundColor : null; })()")
    check('C9: hover ярлыка — тёплый #575A50 (светлее неактивного)', hov == 'rgb(87, 90, 80)', hov)

    # клик «Добавить работника» — шторка создания
    page.click('#wsWorkersAddBtn')
    page.wait_for_timeout(600)
    sheet_open = page.evaluate("(function(){ return {" +
        "open: document.getElementById('wsEmpSheet').classList.contains('active')," +
        "title: document.getElementById('wsEmpSheetTitle').textContent }; })()")
    check('C10: клик «Добавить работника» — шторка «Новый работник»',
          sheet_open['open'] and sheet_open['title'] == 'Новый работник', sheet_open)
    page.screenshot(path='/tmp/t390-proof-add-sheet.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmployeeForm()")
    page.wait_for_timeout(500)

    # вкладка работника — карточка + примыкание живо; возврат
    page.evaluate("document.querySelectorAll('.ws-wtab')[1].click()")
    page.wait_for_timeout(500)
    w2 = page.evaluate(WORKERS_JS)
    check('C11: вкладка работника — карточка, ПРИМЫКАНИЕ живо',
          w2['card'] == 'rgb(14, 22, 33)' and w2['gen'] is None and
          w2['gap'] is not None and abs(w2['gap']) <= 1,
          (w2['card'], w2['gap']))
    page.evaluate("document.querySelector('.ws-wtab-general').click()")
    page.wait_for_timeout(500)
    w3 = page.evaluate(WORKERS_JS)
    check('C12: возврат на «Общую» — панель с шапкой снова',
          w3['gen'] is not None and w3['head'] is not None and w3['card'] is None)

    check('C13: 0 JS-ошибок (десктоп тёмная)', len(js_errors) == 0, js_errors[:3])
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
    inactive_l = [t for t in wl['tabs'] if not t['active']]
    active_l = [t for t in wl['tabs'] if t['active']]
    check('D1: светлая — ярлыки #E4E0D3 (без изменений)',
          inactive_l and all(t['bg'] == 'rgb(228, 224, 211)' for t in inactive_l),
          [t['bg'] for t in inactive_l][:2])
    check('D2: светлая — активный #F0EEE6 (как окно вкладки)',
          active_l and all(t['bg'] == 'rgb(240, 238, 230)' for t in active_l),
          [t['bg'] for t in active_l][:2])
    check('D3: светлая — шапка ВЫДЕЛЕНА #E4E0D3',
          wl['head'] and wl['head']['bg'] == 'rgb(228, 224, 211)', wl['head'])
    check('D4: светлая — тексты + примыкание',
          wl['staff'] and wl['cur'] and not wl['note'] and
          wl['gap'] is not None and abs(wl['gap']) <= 1,
          (wl['staff'], wl['cur'], wl['gap']))
    page3.screenshot(path='/tmp/t390-proof-workers-light.png', full_page=False)
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
    check('E1: мобайл — ярлыки горизонтальной лентой, первый «Общая»',
          wm['tabsRow'] == 'row' and wm['nTabs'] == 7 and
          wm['tabs'][0]['txt'] == 'Общая' and wm['tabs'][0]['active'],
          (wm['tabsRow'], wm['nTabs']))
    inactive_m = [t for t in wm['tabs'] if not t['active']]
    check('E2: мобайл — ярлыки #E4E0D3 (светлая)',
          inactive_m and all(t['bg'] == 'rgb(228, 224, 211)' for t in inactive_m),
          [t['bg'] for t in inactive_m][:2])
    check('E3: мобайл — шапка #E4E0D3 + тексты + кнопка',
          wm['head'] and wm['head']['bg'] == 'rgb(228, 224, 211)' and
          wm['staff'] and wm['cur'] and wm['addInBody'] and wm['addTxt'] == 'Добавить работника',
          (wm['head'], wm['bodyTxt'][:150]))
    page2.screenshot(path='/tmp/t390-proof-mobile-workers.png', full_page=False)

    check('F: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
