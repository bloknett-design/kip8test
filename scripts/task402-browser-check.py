#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 402: browser-check — заявка «В разделе Табель учёта рабочего
# времени, в столбце работники, в ячейках с фамилиями работников,
# данные типа работника размести в третьей строчке снизу, не меняя
# при этом шрифта и высоты ячеек. В файле табель_КИП_ИОС я добавил
# новый столбец "группа_допуска", необходимо сделать чтобы данные
# из него также редактировались из приложения и отображались
# в приложении после данных "должность"».
# МОК: 3 активных работника (Иванов сменный смена 1 / группа IV,
# Петров дневной / группа пусто, Сидоров сменный смена 3 / группа
# III) + 1 архивный; записи текущего месяца.
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, КИП ИОС + workschedule.view:
#      ячейка — ТРИ строки (ФИО / «Слесарь КИПиА · IV» / «смена №1»);
#      строка типа — тем же шрифтом 10px/12px/тем же цветом, что
#      должность; высота ячеек — прежняя растяжка (равные, без
#      вертикального скролла); у Петрова (группа пуста) должность
#      без «·»; карточка: «Группа допуска» ПОСЛЕ «Должности»; 0 JS-ошибок;
#   2) десктоп 1280 светлая, Админ + workschedule.edit:
#      карточка → «Правка данных…» → шторка: селект «Группа допуска»
#      = IV, опции II/III/IV/V + «— не указана —»; выбор V →
#      «Сохранить» → серверу ушёл updateEmployee с группа_допуска=V;
#      сетка перерисовалась («Слесарь КИПиА · V»); страница
#      «Работники» → «Общая»: колонка «Группа допуска» после
#      «Должности» (Иванов V, Петров —); 0 JS-ошибок;
#   3) мобильный 375 светлая, view: ячейка — три строки;
#      горизонтальная прокрутка — строка типа скрыта (ws-narrow),
#      возврат — видна; 0 JS-ошибок.
# Порт 8902 (запуск: python3 -m http.server 8902 &).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8902
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '', 'комментарий': ''},
  {'таб_номер': '031', 'ФИО': 'Сидоров С. С.', 'тип': 'сменный', 'смена': 3,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 2),
   'дата_приёма': '2023-11-05', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр КИПиА', 'группа_допуска': 'III', 'комментарий': ''},
  {'таб_номер': '900', 'ФИО': 'Архивный А. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2020-05-06', 'дата_увольнения': '%04d-06-30' % Y,
   'в_архиве': 1, 'должность': 'Инженер КИПиА', 'группа_допуска': 'II',
   'комментарий': ''},
]
ENTRIES = [
  {'дата': d(Y, M, 3), 'таб_номер': '017', 'статус': 'Д'},
  {'дата': d(Y, M, 5), 'таб_номер': '023', 'статус': 'Д8'},
  {'дата': d(Y, M, 7), 'таб_номер': '031', 'статус': 'Н'},
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
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

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
        return {'ok': True, 'data': {'trainings': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': list(ENTRIES)}}
    if action == 'workSchedule.updateEmployee':
        API_CALLS.append(('updateEmployee', dict(body or {})))
        tab = str((body or {}).get('таб_номер', ''))
        for e in EMPLOYEES:
            if str(e['таб_номер']) == tab:
                for k in ('ФИО', 'тип', 'должность', 'группа_допуска', 'комментарий'):
                    if k in (body or {}):
                        e[k] = str(body[k])
                if 'смена' in (body or {}):
                    e['смена'] = body['смена']
                return {'ok': True, 'data': {'таб_номер': tab}}
        return {'ok': False, 'error': 'not_found_таб_номер'}
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
                      body='not found (t402-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t402-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

CELLS_JS = """(function(){
    var wrap = document.getElementById('wsGridWrap');
    var cells = wrap.querySelectorAll('tbody td.ws-emp-col');
    var out = [];
    for (var i = 0; i < cells.length; i++) {
        var td = cells[i];
        var name = td.querySelector('.ws-emp-name');
        var pos = td.querySelector('.ws-emp-pos');
        var tip = td.querySelector('.ws-emp-tip');
        var rec = { fio: name ? name.textContent : null,
                   pos: pos ? pos.textContent : null,
                   tip: tip ? tip.textContent : null,
                   h: td.getBoundingClientRect().height };
        if (pos) { var cp = getComputedStyle(pos);
            rec.posFont = cp.fontSize; rec.posLH = cp.lineHeight; rec.posColor = cp.color; }
        if (tip) { var ct = getComputedStyle(tip);
            rec.tipFont = ct.fontSize; rec.tipLH = ct.lineHeight; rec.tipColor = ct.color;
            rec.tipOverflow = tip.scrollWidth > tip.clientWidth + 1;
            rec.tipVisible = tip.getBoundingClientRect().height > 0; }
        out.push(rec);
    }
    return { cells: out,
             scrollSh: wrap.scrollHeight, scrollCh: wrap.clientHeight };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, view ==========
    print('=== Контекст 1: десктоп тёмная — три строки ячейки (view) ===')
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
    m = page.evaluate(CELLS_JS)
    cells = m['cells']
    check('B0: сетка отрисована (3 работника)', len(cells) == 3, len(cells))
    iv = next((c for c in cells if c['fio'] and 'Иванов' in c['fio']), None)
    pe = next((c for c in cells if c['fio'] and 'Петров' in c['fio']), None)
    si = next((c for c in cells if c['fio'] and 'Сидоров' in c['fio']), None)
    # 1) три строки: ФИО / должность·группа / тип
    check('B1: Иванов — должность с группой «Слесарь КИПиА · IV»',
          iv and iv['pos'] == 'Слесарь КИПиА · IV', iv and iv['pos'])
    check('B2: Иванов — тип ТРЕТЬЕЙ строкой «смена №1»',
          iv and iv['tip'] == 'смена №1', iv and iv['tip'])
    check('B3: Петров (группа пуста) — должность без «·»',
          pe and pe['pos'] == 'Инженер КИПиА', pe and pe['pos'])
    check('B4: Петров — третья строка «дневной»',
          pe and pe['tip'] == 'дневной', pe and pe['tip'])
    check('B5: Сидоров — «Электромонтёр КИПиА · III» / «смена №3»',
          si and si['pos'] == 'Электромонтёр КИПиА · III' and si['tip'] == 'смена №3',
          si and (si['pos'], si['tip']))
    # 2) шрифт строки типа = шрифт должности (заявка: «не меняя шрифта»)
    check('C1: шрифт .ws-emp-tip = шрифт .ws-emp-pos (10px)',
          iv and iv['tipFont'] == iv['posFont'] == '10px', iv and (iv['tipFont'], iv['posFont']))
    check('C2: интервал 12px и цвет — те же, что у должности',
          iv and iv['tipLH'] == iv['posLH'] == '12px' and iv['tipColor'] == iv['posColor'],
          iv and (iv['tipLH'], iv['posLH'], iv['tipColor'], iv['posColor']))
    # 3) высота ячеек — прежняя растяжка (равные, без скролла, влезает)
    hs = [c['h'] for c in cells]
    check('D1: высоты ячеек РАВНЫ (растяжка _fitGrid, не контент)',
          len(set(hs)) == 1, hs)
    check('D2: вертикального скролла нет (допуск 1px — Task 257)',
          m['scrollSh'] <= m['scrollCh'] + 1, (m['scrollSh'], m['scrollCh']))
    check('D3: три строки влезают в ячейку (высота ≥ 52px)',
          hs and hs[0] >= 52, hs)
    check('D4: строка типа не обрезана эллипсисом',
          all(not c.get('tipOverflow') for c in cells),
          [c.get('tipOverflow') for c in cells])
    # 4) карточка: «Группа допуска» после «Должности»
    page.click("td.ws-emp-col[data-tab='017']")
    page.wait_for_timeout(700)
    card = page.evaluate("(function(){var p=document.getElementById('wsEmpPopup');" +
                         "return p?p.innerHTML:'';})()")
    check('E1: карточка открылась', 'Иванов' in card)
    i_pos = card.find('ws-emp-k">Должность')
    i_grp = card.find('ws-emp-k">Группа допуска')
    i_hire = card.find('ws-emp-k">Дата приёма')
    check('E2: «Группа допуска» — ПОСЛЕ «Должности» (до «Даты приёма»)',
          i_pos != -1 and i_grp != -1 and i_hire != -1 and i_pos < i_grp < i_hire,
          (i_pos, i_grp, i_hire))
    check('E3: значение группы в карточке — IV',
          i_grp != -1 and 'IV' in card[i_grp:i_grp + 200])
    page.screenshot(path='task402-proof-grid-dark.png', full_page=False)
    check('F: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, edit ==========
    print('=== Контекст 2: десктоп светлая — правка группы (edit) ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'edit-light')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    # страница «Работники» → карточка Иванова → «Правка данных…»
    # (Task 385: правка — ТОЛЬКО со страницы «Работники»; попап шахматки
    # — только чтение)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    page.click('.ws-emp-editdata')
    page.wait_for_selector('#wsEmpSheet.active', timeout=4000)
    page.wait_for_timeout(600)
    grp = page.evaluate("""(function(){
        var s = document.getElementById('wsEmpAccessGroup');
        if (!s) return null;
        var opts = [];
        for (var i = 0; i < s.options.length; i++)
            opts.push([s.options[i].value, s.options[i].textContent]);
        return { value: s.value, options: opts,
                 label: (document.querySelector('label[for=\\"wsEmpAccessGroup\\"]')||{}).textContent };
    })()""")
    check('G1: селект «Группа допуска» в шторке (лейбл)', grp and grp['label'] == 'Группа допуска',
          grp and grp['label'])
    check('G2: текущее значение IV (префилл правки)', grp and grp['value'] == 'IV',
          grp and grp['value'])
    vals = [o[0] for o in grp['options']] if grp else []
    check('G3: опции — II/III/IV/V + «— не указана —»',
          '' in vals and all(v in vals for v in ('II', 'III', 'IV', 'V')), vals)
    page.screenshot(path='task402-proof-edit-form.png', full_page=False)
    # выбор V → Сохранить
    page.select_option('#wsEmpAccessGroup', 'V')
    page.click('#wsEmpSubmitBtn')
    page.wait_for_timeout(1500)
    upd = [c for c in API_CALLS if c[0] == 'updateEmployee']
    check('H1: серверу ушёл updateEmployee с группа_допуска = V',
          upd and upd[-1][1].get('группа_допуска') == 'V',
          upd[-1][1].get('группа_допуска') if upd else None)
    check('H2: в payload и должность (порядок полей сохранён)',
          upd and upd[-1][1].get('должность') == 'Слесарь КИПиА',
          upd[-1][1].get('должность') if upd else None)
    m2 = page.evaluate(CELLS_JS)
    iv2 = next((c for c in m2['cells'] if c['fio'] and 'Иванов' in c['fio']), None)
    check('H3: сетка перерисовалась — «Слесарь КИПиА · V»',
          iv2 and iv2['pos'] == 'Слесарь КИПиА · V', iv2 and iv2['pos'])
    # вкладка «Общая» страницы «Работники» (уже на ней после правки)
    page.click(".ws-wtabs button:has-text('Общая')")
    page.wait_for_timeout(900)
    gen = page.evaluate("""(function(){
        var t = document.querySelector('.ws-wgen-table');
        if (!t) return null;
        var ths = [].map.call(t.querySelectorAll('thead th'), function(th){return th.textContent;});
        var row = t.querySelector('tbody tr');
        return { ths: ths,
                 first: row ? [].map.call(row.querySelectorAll('td'), function(td){return td.textContent;}) : null };
    })()""")
    check('I1: сводная «Общая» — колонка «Группа допуска» после «Должности»',
          gen and gen['ths'].index('Должность') + 1 == gen['ths'].index('Группа допуска'),
          gen and gen['ths'])
    check('I2: строка Иванова — группа V после должности',
          gen and gen['first'] and gen['first'][gen['ths'].index('Группа допуска')] == 'V',
          gen and gen['first'])
    pe_cell = page.evaluate("""(function(){
        var t = document.querySelector('.ws-wgen-table');
        var rows = t.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            if (rows[i].textContent.indexOf('Петров') !== -1)
                return rows[i].querySelectorAll('td')[4].textContent;
        }
        return null;
    })()""")
    check('I3: Петров — «—» (группа не указана)', pe_cell == '—', pe_cell)
    page.screenshot(path='task402-proof-workers-general.png', full_page=False)
    check('J: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобильный 375, светлая, view ==========
    print('=== Контекст 3: мобильный 375 светлая — строка типа и сужение ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 375, 'height': 800},
                              is_mobile=True, has_touch=True)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    mm = page.evaluate(CELLS_JS)
    ivm = next((c for c in mm['cells'] if c['fio'] and 'Иванов' in c['fio']), None)
    check('K1: мобильная ячейка — три строки (тип «смена №1»)',
          ivm and ivm['tip'] == 'смена №1' and ivm['tipVisible'], ivm and ivm['tip'])
    check('K2: шрифт строки типа — 10px (как должность)',
          ivm and ivm['tipFont'] == '10px', ivm and ivm['tipFont'])
    # горизонтальная прокрутка → сужение скрывает строку типа
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 300;")
    page.wait_for_timeout(700)
    narrow = page.evaluate("""(function(){
        var t = document.querySelector('.ws-grid');
        var tip = t.querySelector('tbody td.ws-emp-col .ws-emp-tip');
        return { narrow: t.classList.contains('ws-narrow'),
                 tipDisp: tip ? getComputedStyle(tip).display : null };
    })()""")
    check('K3: прокрутка — класс ws-narrow, строка типа СКРЫТА',
          narrow['narrow'] and narrow['tipDisp'] == 'none', narrow)
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 0;")
    page.wait_for_timeout(700)
    back = page.evaluate("""(function(){
        var t = document.querySelector('.ws-grid');
        var tip = t.querySelector('tbody td.ws-emp-col .ws-emp-tip');
        return { narrow: t.classList.contains('ws-narrow'),
                 tipDisp: tip ? getComputedStyle(tip).display : null };
    })()""")
    check('K4: возврат прокрутки — строка типа видна',
          (not back['narrow']) and back['tipDisp'] == 'block', back)
    page.screenshot(path='task402-proof-mobile.png', full_page=False)
    check('L: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
