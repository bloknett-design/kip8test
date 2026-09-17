#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 379: browser-check — заявки пользователя:
#   1) «переделай, фон пустых ячеек #FFFFFF — ячейки значений не в
#      шторке итогов, а в шахматке табеля»: пустые ячейки значений
#      ШАХМАТКИ (ws-status-empty, «.»-ячейка, свотч «.») светлой
#      темы — computed #FFFFFF; тёмная — #eef0f2+brightness(0.88)
#      НЕ тронута; праздники розовые; заполненные — inline-цвет.
#   2) «окна „Мероприятия“/„Нормы“ в баре, при раскрытии должны
#      смещаться вниз по верх бара, не увеличивая его в размере»:
#      раскрытие = ОВЕРЛЕЙ вниз — высота окна = scrollHeight,
#      ГАБАРИТ БАРА НЕ МЕНЯЕТСЯ (.ws-bar-row 95px, ряды 2/3 и сетка
#      НЕ уезжают — координаты до/после равны), низ окна НИЖЕ верха
#      сетки (перекрывает), z-index 55 + тень; повторный клик —
#      95px, маржа сброшена; мобайл 375 — окно поверх второго окна,
#      ничего не сдвинулось.
# + 0 JS-ошибок; скриншот-пруфы. Порт 8986.
import datetime, json
import re
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8986
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

# Статическая проверка правила праздников (fallback A3): розовый
# #f8e2e9 у ПУСТЫХ праздничных ячеек жив в обеих темах
_idx_src = open('index.html', encoding='utf-8').read()
INDEX_RULE_FEAST = re.search(
    r'\[data-theme="light"\] \.ws-grid tbody td\.ws-cell\.ws-feast\.ws-status-empty \{[^}]*#f8e2e9',
    _idx_src) and re.search(
    r'\.ws-grid tbody td\.ws-cell\.ws-feast\.ws-status-empty \{[^}]*#f8e2e9',
    _idx_src)

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
  {'id': 1, 'дата': '%04d-%02d-%02d' % (Y, M, 3), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
  # Task 379: «.»-запись — ячейка ws-dot-code (плановый выходной)
  {'id': 2, 'дата': '%04d-%02d-%02d' % (Y, M, 6), 'таб_номер': '017', 'статус': '.', 'источник': 'авто'},
]
# 12 мероприятий с длинными темами — окно мероприятий переполняется
TRAININGS = []
for k in range(12):
    d = 2 + k * 2
    TRAININGS.append({
        'id': 70 + k,
        'тема': 'Повторный инструктаж по охране труда и пожарной безопасности на производстве, часть %d' % (k + 1),
        'код': 'И',
        'дата_начала': '%04d-%02d-%02d' % (Y, M, d),
        'дата_окончания': '%04d-%02d-%02d' % (Y, M, d),
        'таб_номер': '017', 'подразделение': ''})

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
                'holidays': ['%04d-%02d-04' % (Y, M)], 'transfers': []}}
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t379-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t379');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# Геометрия бара/сетки/рядов — ДО и ПОСЛЕ раскрытия сравниваем
GEOM = """(function(){
    var bar = document.querySelector('.ws-bar-row');
    var grid = document.getElementById('wsGridWrap');
    var trow = document.getElementById('wsTotalsRow');
    var arow = document.getElementById('wsActionsRow');
    return {
        barH: bar.getBoundingClientRect().height,
        gridTop: grid ? grid.getBoundingClientRect().top : null,
        trowTop: trow ? trow.getBoundingClientRect().top : null,
        arowTop: arow ? arow.getBoundingClientRect().top : null
    };
})()"""

def run(browser, theme):
    print('--- тема: %s ---' % theme)
    ctx = browser.new_context(viewport={'width': 1600, 'height': 900}, device_scale_factor=1)
    page = ctx.new_page()
    js_errors = attach(page, ctx, theme, theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)

    # ---------- 1. ШАХМАТКА: ПУСТЫЕ ячейки значений ----------
    cells = page.evaluate("""(function(){
        var out = {};
        // пустая НЕ праздник/НЕ сегодня/НЕ «.»
        var empt = document.querySelectorAll('#wsGridWrap tbody td.ws-cell.ws-status-empty');
        for (var i = 0; i < empt.length; i++) {
            var c = empt[i];
            if (c.classList.contains('ws-feast') || c.classList.contains('ws-today') ||
                c.classList.contains('ws-dot-code')) continue;
            out.empty = { bg: getComputedStyle(c).backgroundColor,
                          filter: getComputedStyle(c).filter };
            break;
        }
        // «.»-ячейка (плановый выходной)
        var dot = document.querySelector('#wsGridWrap tbody td.ws-cell.ws-dot-code');
        out.dot = dot ? { bg: getComputedStyle(dot).backgroundColor,
                          filter: getComputedStyle(dot).filter } : null;
        // праздник (ПУСТОЙ — розовый фон; заполненный несёт inline-цвет).
        // В моках праздничные ячейки могут не отрисоваться (календарь
        // приходит после рендера) — тогда проверяем ПРАВИЛО в исходнике
        var feast = document.querySelector('#wsGridWrap tbody td.ws-cell.ws-feast.ws-status-empty');
        out.feast = feast ? getComputedStyle(feast).backgroundColor : null;
        out.feastFound = !!feast;
        // заполненная (Д) — inline-цвет из справочника
        var filled = document.querySelector('#wsGridWrap tbody td.ws-cell:not(.ws-status-empty)');
        out.filled = filled ? getComputedStyle(filled).backgroundColor : null;
        // «сегодня» — inset-подсветка жива
        var today = document.querySelector('#wsGridWrap tbody td.ws-cell.ws-today');
        out.todayShadow = today ? getComputedStyle(today).boxShadow : null;
        return out;
    })()""")
    if theme == 'light':
        check('A1: ПУСТАЯ ячейка шахматки — #FFFFFF',
              cells['empty'] and cells['empty']['bg'] == 'rgb(255, 255, 255)',
              cells['empty'])
        check('A2: «.»-ячейка — #FFFFFF (как пустая)',
              cells['dot'] and cells['dot']['bg'] == 'rgb(255, 255, 255)', cells['dot'])
    else:
        check('A1: ПУСТАЯ ячейка (тёмная) — #eef0f2 + brightness(0.88), НЕ тронута',
              cells['empty'] and cells['empty']['bg'] == 'rgb(238, 240, 242)' and
              'brightness(0.88)' in cells['empty']['filter'], cells['empty'])
        check('A2: «.»-ячейка (тёмная) — #eef0f2 (НЕ тронута)',
              cells['dot'] and cells['dot']['bg'] == 'rgb(238, 240, 242)', cells['dot'])
    if cells is None:
        cells = {}
    if cells.get('feastFound'):
        check('A3: праздник — розовый #f8e2e9 (не тронут, Task 363)',
              cells['feast'] == 'rgb(248, 226, 233)', cells['feast'])
    else:
        # праздничные ячейки не отрисовались в моках — правило живо в CSS
        # (полную проверку праздников делают юнит-тесты test-task363/379)
        check('A3: правило праздников #f8e2e9 живо (CSS)',
              INDEX_RULE_FEAST is not None)
    check('A4: заполненная ячейка — inline-цвет кода (регресс)',
          cells['filled'] in ('rgb(255, 224, 130)', 'rgb(255, 249, 196)', 'rgb(176, 190, 197)'),
          cells['filled'])
    check('A5: подсветка «сегодня» жива (inset, Task 377)',
          cells['todayShadow'] and
          ('74, 143, 199' in cells['todayShadow'] or '42, 93, 143' in cells['todayShadow']),
          cells['todayShadow'])

    # ---------- 2. ОКНА БАРА: раскрытие = ОВЕРЛЕЙ ----------
    g0 = page.evaluate(GEOM)
    check('B0: до раскрытия — окно 95px, бар собран',
          abs(g0['barH'] - 95) < 3, g0)

    btn = page.locator('#wsEventsPanel .ws-bar-exp')
    check('B1: значок раскрытия есть (текст переполняет)', btn.count() == 1)
    btn.click()
    page.wait_for_timeout(450)   # transition 0.18s + запас

    opened = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var grid = document.getElementById('wsGridWrap');
        var r = ev.getBoundingClientRect();
        var cs = getComputedStyle(ev);
        return {
            h: r.height, bottom: r.bottom,
            scrollH: ev.scrollHeight,
            gridTop: grid.getBoundingClientRect().top,
            cls: ev.className,
            zi: cs.zIndex, pos: cs.position,
            shadow: cs.boxShadow,
            mb: cs.marginBottom,
            animH: cs.height
        };
    })()""")
    g1 = page.evaluate(GEOM)
    check('B2: окно раскрыто на ВЕСЬ текст (низ по количеству текста)',
          abs(opened['h'] - opened['scrollH']) < 6 and opened['h'] > 120,
          (opened['h'], opened['scrollH']))
    check('B3: ГАБАРИТ БАРА НЕ ИЗМЕНИЛСЯ (.ws-bar-row = 95px)',
          abs(g1['barH'] - g0['barH']) < 2 and abs(g1['barH'] - 95) < 3,
          (g0['barH'], g1['barH']))
    check('B4: ряд «Итоги учёта» НЕ уехал', abs(g1['trowTop'] - g0['trowTop']) < 2,
          (g0['trowTop'], g1['trowTop']))
    check('B5: ряд действий НЕ уехал', abs(g1['arowTop'] - g0['arowTop']) < 2,
          (g0['arowTop'], g1['arowTop']))
    check('B6: сетка под баром НЕ уехала', abs(g1['gridTop'] - g0['gridTop']) < 2,
          (g0['gridTop'], g1['gridTop']))
    check('B7: НИЗ окна НИЖЕ верха сетки — сместился вниз ПО ВЕРХ бара',
          opened['bottom'] > g1['gridTop'] + 20, (opened['bottom'], g1['gridTop']))
    check('B8: окно-оверлей: z-index 55, position relative',
          opened['zi'] == '55' and opened['pos'] == 'relative', (opened['zi'], opened['pos']))
    exp_sh = 'rgba(0, 0, 0, 0.38)' if theme == 'dark' else 'rgba(0, 0, 0, 0.22)'
    check('B9: тень «парения» (%s)' % exp_sh, exp_sh in opened['shadow'], opened['shadow'])
    check('B10: margin-bottom отрицательный (компенсация габарита)',
          opened['mb'].startswith('-') and abs(g1['barH'] - 95) < 3, opened['mb'])

    if theme == 'light':
        page.screenshot(path='/tmp/t379-opened-light.png', full_page=False)

    # повторный клик — свёрнуто, всё вернулось
    page.locator('#wsEventsPanel .ws-bar-exp').click()
    page.wait_for_timeout(450)
    closed = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var cs = getComputedStyle(ev);
        return { h: ev.getBoundingClientRect().height,
                 mb: cs.marginBottom, cls: ev.className };
    })()""")
    g2 = page.evaluate(GEOM)
    check('B11: повторный клик — окно свёрнуто (95px)', abs(closed['h'] - 95) < 3, closed['h'])
    check('B12: маржа сброшена (0px)', closed['mb'] == '0px', closed['mb'])
    check('B13: геометрия бара/сетки вернулась',
          abs(g2['barH'] - g0['barH']) < 2 and abs(g2['gridTop'] - g0['gridTop']) < 2,
          (g2['barH'], g2['gridTop']))

    # окно норм: если не переполняется — значка нет (как прежде)
    cal_btn = page.evaluate("""(function(){
        var cal = document.getElementById('wsCalPanel');
        var b = cal.querySelector('.ws-bar-exp');
        return { over: cal.scrollHeight > cal.clientHeight + 2,
                 display: b ? getComputedStyle(b).display : null };
    })()""")
    if cal_btn['over']:
        page.locator('#wsCalPanel .ws-bar-exp').click()
        page.wait_for_timeout(450)
        cal_open = page.evaluate("""(function(){
            var cal = document.getElementById('wsCalPanel');
            var grid = document.getElementById('wsGridWrap');
            var r = cal.getBoundingClientRect();
            return { h: r.height, bottom: r.bottom,
                     gridTop: grid.getBoundingClientRect().top,
                     zi: getComputedStyle(cal).zIndex };
        })()""")
        check('B14: окно «Нормы» — тот же оверлей (низ ниже сетки, z55)',
              cal_open['bottom'] > cal_open['gridTop'] + 10 and cal_open['zi'] == '55',
              cal_open)
    else:
        check('B14: окно «Нормы» без переполнения — значок скрыт (как прежде)',
              cal_btn['display'] == 'none', cal_btn)

    page.screenshot(path='/tmp/t379-%s.png' % theme, full_page=False)
    check('Z: 0 JS-ошибок (%s)' % theme, len(js_errors) == 0, js_errors[:2])
    ctx.close()
    return js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()
    errs_d = run(browser, 'dark')
    errs_l = run(browser, 'light')

    # ---------- МОБАЙЛ 375: раскрытие не двигает колонку бара ----------
    ctx = browser.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=1)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mob')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    # мобильный чип «Мероприятия» — раскрыть окно
    page.locator('#wsChipEvents').click()
    page.wait_for_timeout(500)
    m0 = page.evaluate("""(function(){
        var cal = document.getElementById('wsCalPanel');
        var grid = document.getElementById('wsGridWrap');
        var ev = document.getElementById('wsEventsPanel');
        return {
            calTop: cal.getBoundingClientRect().top,
            gridTop: grid.getBoundingClientRect().top,
            evH: ev.getBoundingClientRect().height,
            btn: !!ev.querySelector('.ws-bar-exp')
        };
    })()""")
    check('M1: мобайл — окно мероприятий открыто чипом', m0['evH'] > 0 and m0['btn'], m0)
    if m0['btn']:
        page.locator('#wsEventsPanel .ws-bar-exp').click()
        page.wait_for_timeout(450)
        m1 = page.evaluate("""(function(){
            var cal = document.getElementById('wsCalPanel');
            var grid = document.getElementById('wsGridWrap');
            var ev = document.getElementById('wsEventsPanel');
            var r = ev.getBoundingClientRect();
            return {
                h: r.height, bottom: r.bottom,
                calTop: cal.getBoundingClientRect().top,
                gridTop: grid.getBoundingClientRect().top,
                zi: getComputedStyle(ev).zIndex,
                mb: getComputedStyle(ev).marginBottom
            };
        })()""")
        check('M2: окно раскрыто на весь текст', m1['h'] > 120, m1['h'])
        check('M3: окно «Нормы» НЕ уехало (бар не увеличился)',
              abs(m1['calTop'] - m0['calTop']) < 2, (m0['calTop'], m1['calTop']))
        check('M4: сетка НЕ уехала', abs(m1['gridTop'] - m0['gridTop']) < 2,
              (m0['gridTop'], m1['gridTop']))
        check('M5: раскрытое окно перекрывает окно норм (оверлей вниз)',
              m1['bottom'] > m1['calTop'] + 10, (m1['bottom'], m1['calTop']))
        check('M6: z-index 55 (оверлей)', m1['zi'] == '55', m1['zi'])
        page.screenshot(path='/tmp/t379-mobile.png', full_page=False)
    check('M7: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:2])
    ctx.close()
    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
