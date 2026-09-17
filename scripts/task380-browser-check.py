#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 380: browser-check — заявки пользователя:
#   1) «В окне „Мероприятия“ в баре, цвет фона в окне где расположен
#      текст мероприятий дата которых прошла, должен быть светлее, а
#      дата которых ещё не наступила или не прошла — фон в окне
#      темнее»: строки окна мероприятий — класс .ws-ep-past у
#      прошедших (окончание строго < сегодня), computed фоны:
#      тёмная — прошедшие rgba(255,255,255,0.12) светлее окна,
#      текущие/будущие rgba(0,0,0,0.45) темнее окна; светлая —
#      0.55/0.12; ЯРКОСТЬ (blend-расчёт поверх фона окна):
#      past > окно > upcoming в обеих темах; плашка строки
#      padding 2px 6px / margin 0 -6px; количество прошедших строк =
#      расчётному по тем же правилам.
#   2) «В мобильной версии, при нажатии с задержкой на ячейки шахматки
#      и с фамилиями и ячейки итогов учёта, не должен выделяться текст»:
#      мобайл 375 — computed user-select:none у .ws-grid (ячейки
#      значений, ФИО, шапка) и .ws-tt-table (шторка итогов);
#      функционально — программная Selection по содержимому ячеек
#      ПУСТА (выделить нечего); десктоп 1280 — user-select ячеек НЕ
#      none (выделение мышью живо как прежде).
# + 0 JS-ошибок; скриншот-пруфы (окно мероприятий раскрыто значком,
#   мобайл с открытой шторкой итогов). Порт 8988.
import calendar, datetime, json, re
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8988
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
TODAY_ISO = '%04d-%02d-%02d' % (Y, M, TODAY.day)

def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': '.', 'name': 'Плановый выходной день', 'color': '#EEF0F2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '018', 'ФИО': 'Сидоров Сидор Сидорович', 'тип': 'сменный', 'смена': 2,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
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
  {'id': 1, 'дата': d(-6), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
  {'id': 2, 'дата': d(-2), 'таб_номер': '018', 'статус': 'Д8', 'источник': 'авто'},
]
# Task 380: мероприятия ВОКРУГ «сегодня» — прошедшие (окончание
# строго раньше), идущее сегодня (накрывает), будущие; расчёт
# «прошедшее» в Python по ТОМУ ЖЕ правилу, что в _renderMonthEventsPanel
TRAININGS = [
  {'id': 80, 'тема': 'Повторный инструктаж по охране труда (давно прошедший)',
   'тип': 'инструктаж', 'дата_начала': d(-12), 'дата_окончания': d(-12),
   'таб_номер': '017', 'подразделение': ''},
  {'id': 81, 'тема': 'Обучение по новой редакции инструкций (прошедший диапазон)',
   'тип': 'обучение', 'дата_начала': d(-9), 'дата_окончания': d(-7),
   'таб_номер': '018', 'подразделение': ''},
  {'id': 82, 'тема': 'Целевой инструктаж (идёт сегодня)',
   'тип': 'инструктаж', 'дата_начала': d(-1), 'дата_окончания': d(1),
   'таб_номер': '023', 'подразделение': ''},
  {'id': 83, 'тема': 'Проверка знаний (будущее)',
   'тип': 'проверка_знаний', 'дата_начала': d(2), 'дата_окончания': d(3),
   'таб_номер': '017', 'подразделение': ''},
  {'id': 84, 'тема': 'Инструктаж по пожарной безопасности (далёкое будущее)',
   'тип': 'инструктаж', 'дата_начала': d(5), 'дата_окончания': d(9),
   'таб_номер': '018', 'подразделение': ''},
]
EXPECTED_PAST = sum(1 for t in TRAININGS
                    if (t['дата_окончания'] or t['дата_начала']) < TODAY_ISO)

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok': True, 'data': {'entries': ENTRIES}}
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

def attach(page, ctx, theme, tag):
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
                      body=json.dumps(mock_response(action, body), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (t380-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t380');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# Строки окна мероприятий: классы + computed фоны + плашка
ROWS_JS = """(function(){
    var panel = document.getElementById('wsEventsPanel');
    var rows = Array.prototype.slice.call(
        panel.querySelectorAll('.ws-ep-item'));
    function parseC(c){
        var m = c.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
        if (!m) return null;
        return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3]),
                m[4] === undefined ? 1 : parseFloat(m[4])];
    }
    function blend(fg, bg){
        var a = fg[3];
        return [fg[0]*a + bg[0]*(1-a), fg[1]*a + bg[1]*(1-a), fg[2]*a + bg[2]*(1-a)];
    }
    function lum(c){ return c[0]*0.299 + c[1]*0.587 + c[2]*0.114; }
    var winBg = parseC(getComputedStyle(panel).backgroundColor);
    var out = { winBg: getComputedStyle(panel).backgroundColor,
                rows: [], pastN: 0, upN: 0 };
    rows.forEach(function(r){
        var cs = getComputedStyle(r);
        var bg = parseC(cs.backgroundColor);
        var eff = blend(bg, winBg);
        var o = { past: r.classList.contains('ws-ep-past'),
                  bg: cs.backgroundColor,
                  pad: cs.padding, mar: cs.margin,
                  txt: r.textContent.replace(/\\s+/g, ' ').slice(0, 30),
                  effLum: lum(eff), winLum: lum(winBg) };
        if (o.past) out.pastN++; else out.upN++;
        out.rows.push(o);
    });
    return out;
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= ДЕСКТОП: мероприятия + user-select =================
    for theme in ('dark', 'light'):
        print('--- ДЕСКТОП 1280, тема %s ---' % theme)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        js_errors = attach(page, ctx, theme, theme)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2000)

        r = page.evaluate(ROWS_JS)
        exp_past_bg = 'rgba(255, 255, 255, 0.12)' if theme == 'dark' else 'rgba(255, 255, 255, 0.55)'
        exp_up_bg = 'rgba(0, 0, 0, 0.45)' if theme == 'dark' else 'rgba(0, 0, 0, 0.12)'

        check('A1: строк мероприятий ≥ 5 (%s)' % theme, len(r['rows']) >= 5, len(r['rows']))
        check('A2: прошедших строк = %d (расчёт по правилу «окончание < сегодня»)' % EXPECTED_PAST,
              r['pastN'] == EXPECTED_PAST, (r['pastN'], EXPECTED_PAST))
        past = [x for x in r['rows'] if x['past']]
        up = [x for x in r['rows'] if not x['past']]
        check('A3: фон ПРОШЕДШИХ = %s (%s)' % (exp_past_bg, theme),
              past and all(x['bg'] == exp_past_bg for x in past),
              [x['bg'] for x in past[:2]])
        check('A4: фон ТЕКУЩИХ/БУДУЩИХ = %s (%s)' % (exp_up_bg, theme),
              up and all(x['bg'] == exp_up_bg for x in up),
              [x['bg'] for x in up[:2]])
        check('A5: ЯРКОСТЬ: прошедшие СВЕТЛЕЕ окна, будущие ТЕМНЕЕ (%s)' % theme,
              past and up and
              all(x['effLum'] > x['winLum'] for x in past) and
              all(x['effLum'] < x['winLum'] for x in up),
              [(round(x['effLum'], 1), round(x['winLum'], 1)) for x in r['rows'][:3]])
        check('A6: плашка строки padding 2px 6px / margin 0 -6px (%s)' % theme,
              past and past[0]['pad'] == '2px 6px' and past[0]['mar'] == '0px -6px',
              (past[0]['pad'] if past else None, past[0]['mar'] if past else None))

        # раскрыть окно значком (Task 378/379) — скриншот ВСЕХ строк
        exp_btn = page.query_selector('#wsEventsPanel .ws-bar-exp')
        if exp_btn:
            page.locator('#wsEventsPanel .ws-bar-exp').click()
            page.wait_for_timeout(450)
        page.locator('#wsEventsPanel').screenshot(path='/tmp/t380-events-%s.png' % theme)

        # десктоп: выделение живо (user-select НЕ none)
        us = page.evaluate("""(function(){
            var emp = document.querySelector('.ws-grid tbody td.ws-emp-col');
            var cell = document.querySelector('.ws-grid tbody td.ws-cell');
            var w = document.querySelector('#wsEventsPanel .ws-ep-item');
            return { emp: getComputedStyle(emp).userSelect,
                     cell: cell ? getComputedStyle(cell).userSelect : null,
                     evRow: w ? getComputedStyle(w).userSelect : null };
        })()""")
        check('A7: десктоп — ячейки ФИО/значений/строки окна БЕЗ user-select (%s)' % theme,
              us['emp'] != 'none' and us['cell'] != 'none' and us['evRow'] != 'none', us)

        # шторка итогов на десктопе — выделение живо
        page.locator('#wsTotalsBtn').click()
        page.wait_for_timeout(700)
        us2 = page.evaluate("""(function(){
            var t = document.querySelector('.ws-tt-table');
            var td = t ? t.querySelector('tbody td') : null;
            return { table: t ? getComputedStyle(t).userSelect : null,
                     td: td ? getComputedStyle(td).userSelect : null };
        })()""")
        check('A8: десктоп — итоги учёта выделяются как прежде (%s)' % theme,
              us2['table'] != 'none' and us2['td'] != 'none', us2)
        check('Z: 0 JS-ошибок (%s)' % theme, len(js_errors) == 0, js_errors[:2])
        ctx.close()

    # ================= МОБАЙЛ 375: запрет выделения =================
    print('--- МОБАЙЛ 375 ---')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=2)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mob')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)

    m1 = page.evaluate("""(function(){
        var grid = document.querySelector('.ws-grid');
        var emp = document.querySelector('.ws-grid tbody td.ws-emp-col');
        var cell = document.querySelector('.ws-grid tbody td.ws-cell');
        var th = document.querySelector('.ws-grid thead th');
        return { grid: getComputedStyle(grid).userSelect,
                 emp: getComputedStyle(emp).userSelect,
                 cell: cell ? getComputedStyle(cell).userSelect : null,
                 th: getComputedStyle(th).userSelect,
                 gridWk: getComputedStyle(grid).webkitUserSelect };
    })()""")
    check('M1: шахматка user-select:none (мобайл)', m1['grid'] == 'none', m1)
    check('M2: ячейка ФИО user-select:none', m1['emp'] == 'none', m1['emp'])
    check('M3: ячейка значений user-select:none', m1['cell'] == 'none', m1['cell'])
    check('M4: шапка сетки user-select:none', m1['th'] == 'none', m1['th'])

    # функционально: программное выделение содержимого ячеек ПУСТО
    m2 = page.evaluate("""(function(){
        function trySel(el){
            var sel = window.getSelection();
            sel.removeAllRanges();
            var r = document.createRange();
            r.selectNodeContents(el);
            sel.addRange(r);
            var o = { txt: sel.toString(), collapsed: sel.isCollapsed };
            sel.removeAllRanges();
            return o;
        }
        var emp = document.querySelector('.ws-grid tbody td.ws-emp-col');
        var cell = document.querySelector('.ws-grid tbody td.ws-cell');
        return { emp: trySel(emp), cell: cell ? trySel(cell) : null };
    })()""")
    check('M5: выделение ФИО ПУСТО (текста не взять)',
          m2['emp']['txt'] == '' or m2['emp']['collapsed'], m2['emp'])
    check('M6: выделение ячейки значений ПУСТО',
          not m2['cell'] or m2['cell']['txt'] == '' or m2['cell']['collapsed'], m2['cell'])

    # шторка итогов: открыть и проверить
    page.locator('#wsTotalsBtn').click()
    page.wait_for_timeout(900)
    m3 = page.evaluate("""(function(){
        var t = document.querySelector('.ws-tt-table');
        if (!t) return { table: 'NO TABLE' };
        var emp = t.querySelector('tbody td.ws-tt-emp');
        var num = t.querySelector('tbody td.ws-tt-num');
        function trySel(el){
            var sel = window.getSelection();
            sel.removeAllRanges();
            var r = document.createRange();
            r.selectNodeContents(el);
            sel.addRange(r);
            var o = { txt: sel.toString(), collapsed: sel.isCollapsed };
            sel.removeAllRanges();
            return o;
        }
        return { table: getComputedStyle(t).userSelect,
                 emp: emp ? getComputedStyle(emp).userSelect : null,
                 num: num ? getComputedStyle(num).userSelect : null,
                 empSel: emp ? trySel(emp) : null,
                 numSel: num ? trySel(num) : null };
    })()""")
    check('M7: таблица итогов user-select:none', m3['table'] == 'none', m3['table'])
    check('M8: ячейка ФИО итогов user-select:none', m3['emp'] == 'none', m3['emp'])
    check('M9: ячейка значений итогов user-select:none', m3['num'] == 'none', m3['num'])
    check('M10: выделение ФИО итогов ПУСТО',
          not m3['empSel'] or m3['empSel']['txt'] == '' or m3['empSel']['collapsed'], m3['empSel'])
    check('M11: выделение значений итогов ПУСТО',
          not m3['numSel'] or m3['numSel']['txt'] == '' or m3['numSel']['collapsed'], m3['numSel'])

    page.screenshot(path='/tmp/t380-mobile.png', full_page=False)
    check('M12: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:2])
    ctx.close()
    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
print('Сегодня: %s; ожидается прошедших строк: %d' % (TODAY_ISO, EXPECTED_PAST))
import sys
sys.exit(1 if FAIL else 0)
