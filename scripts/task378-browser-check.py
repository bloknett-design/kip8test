#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 378: browser-check — заявки пользователя:
#   1) итоги учёта: ячейки значений #FFFFFF (светлая) / #eef0f2+
#      brightness(0.88) (тёмная); нули → ПУСТЫЕ ячейки; линии =
#      шахматка (дни/шапка/ФИО); зебра удалена;
#   2) перекрестье: строка/столбец = яркость «сегодня» (0.30/0.22);
#      hover по ФИО → строка (без столбца); hover по ячейкам итогов →
#      строка сетки И итогов; выключенное перекрестье — нет подсветки;
#   3) окна бара: полосы прокрутки НЕТ (scrollbar-width none),
#      tabindex; значок .ws-bar-exp — виден при переполнении,
#      приглушён (0.45) → контрастен при hover/раскрытии; клик —
#      высота = scrollHeight (низ по количеству текста), повтор — 95px;
#      без переполнения — значок скрыт.
# + 0 JS-ошибок; мобайл 375 (чипы); скриншот-пруфы. Порт 8984.
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8984
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

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
            {'day': 7, 'status': ''}]}
]
ENTRIES = [
  {'id': 1, 'дата': '%04d-%02d-%02d' % (Y, M, 3), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
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

def alpha_of(shadow):
    # 'inset 0 0 0 999px rgba(74, 143, 199, 0.30)' → 0.30
    import re
    m = re.search(r'rgba\(\s*74,\s*143,\s*199,\s*([\d.]+)\s*\)', shadow or '')
    m2 = re.search(r'rgba\(\s*42,\s*93,\s*143,\s*([\d.]+)\s*\)', shadow or '')
    return float(m.group(1)) if m else (float(m2.group(1)) if m2 else None)

def run(browser, theme):
    print('--- тема: %s ---' % theme)
    ctx = browser.new_context(viewport={'width': 1600, 'height': 900}, device_scale_factor=1)
    page = ctx.new_page()
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t378-check)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t378');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)

    # ---------- 1. ИТОГИ УЧЁТА ----------
    page.evaluate("document.getElementById('wsTotalsBtn').click()")
    page.wait_for_timeout(1000)
    info = page.evaluate("""(function(){
        var t = document.querySelector('#wsTtBody .ws-tt-table');
        if (!t) return null;
        var td = t.querySelector('tbody td.ws-tt-num');
        var tdEmp = t.querySelector('tbody td.ws-tt-emp');
        var th = t.querySelector('thead th');
        var cs = getComputedStyle(td), ce = getComputedStyle(tdEmp), ch = getComputedStyle(th);
        var texts = Array.prototype.map.call(
            t.querySelectorAll('tbody td.ws-tt-num'), function(c){return c.textContent.trim();});
        return {
            cellBg: cs.backgroundColor, cellFilter: cs.filter, cellColor: cs.color,
            cellBB: cs.borderBottomColor, cellBR: cs.borderRightColor,
            empBB: ce.borderBottomColor, headBB: ch.borderBottomColor,
            texts: texts
        };
    })()""")
    if theme == 'light':
        check('A1: фон ячеек итогов — #FFFFFF (светлая)', info['cellBg'] == 'rgb(255, 255, 255)', info['cellBg'])
        check('A2: линии значений — rgb(10,15,23)', info['cellBB'] == 'rgb(10, 15, 23)', info['cellBB'])
        check('A3: шапка — rgb(83,96,117)', info['headBB'] == 'rgb(83, 96, 117)', info['headBB'])
        check('A4: «Сотрудник» — rgb(64,80,102)', info['empBB'] == 'rgb(64, 80, 102)', info['empBB'])
    else:
        check('A1: фон ячеек итогов — #eef0f2 (тёмная, как дни сетки)', info['cellBg'] == 'rgb(238, 240, 242)', info['cellBg'])
        check('A2: фильтр brightness(0.88)', 'brightness(0.88)' in info['cellFilter'], info['cellFilter'])
        check('A2b: текст тёмный #141413', info['cellColor'] == 'rgb(20, 20, 19)', info['cellColor'])
        check('A3: линии значений — rgba(0,0,0,0.30)', info['cellBB'] == 'rgba(0, 0, 0, 0.3)', info['cellBB'])
    zeros = [t for t in info['texts'] if t == '0']
    check('A5: НУЛЕЙ в ячейках итогов НЕТ (пусто)', len(zeros) == 0, info['texts'][:12])
    nonempty = [t for t in info['texts'] if t not in ('', '—')]
    check('A6: ненулевые значения остались (явки/часы)', len(nonempty) >= 2, nonempty[:6])
    empties = [t for t in info['texts'] if t == '']
    check('A7: есть ПУСТЫЕ ячейки (бывшие нули)', len(empties) >= 3, len(empties))

    # ---------- 2. ПЕРЕКРЕСТЬЕ ----------
    # 2.1 hover по ячейке дня → строка+столбец, яркость = «сегодня»
    day_cell = page.locator('#wsGridWrap tbody tr').nth(1).locator('td.ws-cell[data-day="5"]')
    day_cell.hover()
    page.wait_for_timeout(250)
    cross = page.evaluate("""(function(){
        var grid = document.querySelector('#wsGridWrap table');
        var tr = grid.querySelectorAll('tbody tr')[1];
        var tdHover = tr.querySelector('td.ws-cell.ws-hover');
        var tdRow = tr.querySelector('td.ws-cell');
        // ячейка ТОГО ЖЕ столбца в ДРУГОЙ строке — чистый тинт столбца
        // (без пересечения со строкой наведения)
        var other = grid.querySelectorAll('tbody tr')[0]
            .querySelector('td.ws-cell[data-day="5"]');
        var tdToday = grid.querySelector('tbody td.ws-cell.ws-today');
        var trCls = tr.className;
        var thHover = grid.querySelector('thead th.ws-hover-col');
        var thToday = grid.querySelector('thead th.ws-today-col');
        return {
            trCls: trCls,
            rowShadow: getComputedStyle(tdRow).boxShadow,
            colShadow: getComputedStyle(other).boxShadow,
            crossShadow: getComputedStyle(tdHover).boxShadow,
            todayShadow: tdToday ? getComputedStyle(tdToday).boxShadow : null,
            thHoverImg: thHover ? getComputedStyle(thHover).backgroundImage : null,
            thTodayImg: thToday ? getComputedStyle(thToday).backgroundImage : null
        };
    })()""")
    check('B1: строка под курсором — класс ws-hover-row', 'ws-hover-row' in cross['trCls'], cross['trCls'])
    a_row = alpha_of(cross['rowShadow'])
    a_today = alpha_of(cross['todayShadow'])
    check('B2: яркость строки = «сегодня» (%s)' % ('0.30' if theme == 'dark' else '0.22'),
          a_row is not None and a_today is not None and abs(a_row - a_today) < 0.011,
          (a_row, a_today))
    a_col = alpha_of(cross['colShadow'])
    check('B3: столбец наведения = «сегодня»', a_col is not None and abs(a_col - a_today) < 0.011,
          (a_col, a_today))
    a_cross = alpha_of(cross['crossShadow'])
    check('B3b: пересечение строки+столбца — насыщеннее (0.34/0.26)',
          a_cross is not None and abs(a_cross - a_today - 0.04) < 0.011, (a_cross, a_today))
    exp_head = '0.4' if theme == 'dark' else '0.26'
    check('B4: шапка hover-col = «сегодня» (%s)' % exp_head,
          cross['thHoverImg'] is not None and exp_head in cross['thHoverImg'] and
          cross['thTodayImg'] is not None and exp_head in cross['thTodayImg'],
          (cross['thHoverImg'], cross['thTodayImg']))

    # 2.2 hover по ФИО → ТОЛЬКО строка
    page.locator('#wsGridWrap tbody tr').nth(2).locator('td.ws-emp-col').hover()
    page.wait_for_timeout(250)
    emp_hov = page.evaluate("""(function(){
        var grid = document.querySelector('#wsGridWrap table');
        var tr = grid.querySelectorAll('tbody tr')[2];
        return {
            trCls: tr.className,
            anyHoverCol: !!grid.querySelector('thead th.ws-hover-col'),
            anyHoverCell: !!grid.querySelector('tbody td.ws-cell.ws-hover'),
            ttRowCls: (function(){
                var t = document.querySelector('#wsTtBody .ws-tt-table');
                if (!t) return '';
                var r = t.querySelectorAll('tbody tr')[2];
                return r ? r.className : '';
            })()
        };
    })()""")
    check('B5: hover по ФИО — строка подсвечена', 'ws-hover-row' in emp_hov['trCls'], emp_hov['trCls'])
    check('B6: столбец НЕ подсвечен (день не определён)',
          not emp_hov['anyHoverCol'] and not emp_hov['anyHoverCell'],
          (emp_hov['anyHoverCol'], emp_hov['anyHoverCell']))
    check('B7: строка ШТОРКИ итогов подсвечена синхронно',
          'ws-hover-row' in emp_hov['ttRowCls'], emp_hov['ttRowCls'])

    # 2.3 hover по ячейке итогов → строка сетки И итогов
    page.locator('#wsTtBody .ws-tt-table tbody tr').nth(1).locator('td.ws-tt-num').first.hover()
    page.wait_for_timeout(250)
    tt_hov = page.evaluate("""(function(){
        var grid = document.querySelector('#wsGridWrap table');
        var t = document.querySelector('#wsTtBody .ws-tt-table');
        return {
            gridRow: grid.querySelectorAll('tbody tr')[1].className,
            ttRow: t.querySelectorAll('tbody tr')[1].className,
            ttShadow: getComputedStyle(t.querySelectorAll('tbody tr')[1].querySelector('td')).boxShadow
        };
    })()""")
    check('B8: hover по ячейке ИТОГОВ — строка сетки подсвечена',
          'ws-hover-row' in tt_hov['gridRow'], tt_hov['gridRow'])
    check('B9: строка итогов подсвечена', 'ws-hover-row' in tt_hov['ttRow'], tt_hov['ttRow'])
    a_tt = alpha_of(tt_hov['ttShadow'])
    check('B10: яркость строки итогов = «сегодня»', a_tt is not None and abs(a_tt - a_today) < 0.011,
          (a_tt, a_today))

    # 2.4 перекрестье ВЫКЛЮЧЕНО — итоги/ФИО не подсвечивают
    page.evaluate("document.getElementById('wsCrossBtn').click()")
    page.wait_for_timeout(200)
    page.locator('#wsTtBody .ws-tt-table tbody tr').nth(1).locator('td.ws-tt-num').first.hover()
    page.locator('#wsGridWrap tbody tr').nth(0).locator('td.ws-emp-col').hover()
    page.wait_for_timeout(250)
    off = page.evaluate("""(function(){
        var grid = document.querySelector('#wsGridWrap table');
        var t = document.querySelector('#wsTtBody .ws-tt-table');
        return {
            g0: grid.querySelectorAll('tbody tr')[0].className,
            g1: grid.querySelectorAll('tbody tr')[1].className,
            t1: t.querySelectorAll('tbody tr')[1].className
        };
    })()""")
    check('B11: перекрестье ВЫКЛ — итоги/ФИО не подсвечивают',
          'ws-hover-row' not in off['g0'] and 'ws-hover-row' not in off['g1'] and
          'ws-hover-row' not in off['t1'], off)
    page.evaluate("document.getElementById('wsCrossBtn').click()")  # вернуть ВКЛ
    page.wait_for_timeout(200)

    # ---------- 3. ОКНА БАРА ----------
    panel = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var cal = document.getElementById('wsCalPanel');
        var cs = getComputedStyle(ev);
        var btn = ev.querySelector('.ws-bar-exp');
        return {
            evScroll: cs.scrollbarWidth,
            evTab: ev.getAttribute('tabindex'),
            calTab: cal.getAttribute('tabindex'),
            calScroll: getComputedStyle(cal).scrollbarWidth,
            btn: !!btn,
            btnDisplay: btn ? getComputedStyle(btn).display : null,
            btnOpacity: btn ? getComputedStyle(btn).opacity : null,
            evClientH: ev.clientHeight, evScrollH: ev.scrollHeight,
            evHeight: cs.height, evPos: cs.position
        };
    })()""")
    check('C1: полоса прокрутки окон СКРЫТА (scrollbar-width: none)',
          panel['evScroll'] == 'none' and panel['calScroll'] == 'none',
          (panel['evScroll'], panel['calScroll']))
    check('C2: окна фокусируемы (tabindex)', panel['evTab'] == '0' and panel['calTab'] == '0',
          (panel['evTab'], panel['calTab']))
    check('C3: окно мероприятий ПЕРЕПОЛНЕНО (12 длинных тем)',
          panel['evScrollH'] > panel['evClientH'] + 10, (panel['evScrollH'], panel['evClientH']))
    check('C4: значок раскрытия ЕСТЬ и ВИДЕН', panel['btn'] and panel['btnDisplay'] != 'none',
          (panel['btn'], panel['btnDisplay']))
    check('C5: значок НЕ активен — приглушён (0.45)',
          panel['btnOpacity'] is not None and abs(float(panel['btnOpacity']) - 0.45) < 0.01,
          panel['btnOpacity'])

    # hover по значку — контраст
    page.locator('#wsEventsPanel .ws-bar-exp').hover()
    page.wait_for_timeout(300)
    hov_op = page.evaluate("getComputedStyle(document.querySelector('#wsEventsPanel .ws-bar-exp')).opacity")
    check('C6: hover по значку — полная контрастность (1)', abs(float(hov_op) - 1.0) < 0.01, hov_op)

    # клик — раскрытие (низ уезжает вниз по количеству текста)
    page.locator('#wsEventsPanel .ws-bar-exp').click()
    page.wait_for_timeout(400)
    opened = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var btn = ev.querySelector('.ws-bar-exp');
        return {
            h: ev.getBoundingClientRect().height,
            scrollH: ev.scrollHeight,
            cls: ev.className,
            btnOn: btn.className,
            btnOp: getComputedStyle(btn).opacity,
            btnRot: getComputedStyle(btn.querySelector('svg')).transform
        };
    })()""")
    check('C7: клик — окно раскрыто (низ по количеству текста)',
          abs(opened['h'] - opened['scrollH']) < 6 and opened['h'] > 120,
          (opened['h'], opened['scrollH']))
    check('C8: ws-bar-open класс на окне', 'ws-bar-open' in opened['cls'], opened['cls'])
    check('C9: значок АКТИВЕН — контрастен (1)',
          'on' in opened['btnOn'] and abs(float(opened['btnOp']) - 1.0) < 0.01,
          (opened['btnOn'], opened['btnOp']))

    # повторный клик — свёрнуто до 95px
    page.locator('#wsEventsPanel .ws-bar-exp').click()
    page.wait_for_timeout(400)
    closed_h = page.evaluate(
        "document.getElementById('wsEventsPanel').getBoundingClientRect().height")
    check('C10: повторный клик — окно свёрнуто (95px)', abs(closed_h - 95) < 3, closed_h)

    # окно норм: значок есть? (нормы короткие — значок может отсутствовать)
    cal_btn = page.evaluate("""(function(){
        var cal = document.getElementById('wsCalPanel');
        var btn = cal.querySelector('.ws-bar-exp');
        var over = cal.scrollHeight > cal.clientHeight + 2;
        return { btn: !!btn, over: over,
                 display: btn ? getComputedStyle(btn).display : null };
    })()""")
    if cal_btn['over']:
        check('C11: окно норм переполнено — значок виден', cal_btn['btn'] and cal_btn['display'] != 'none', cal_btn)
    else:
        check('C11: окно норм без переполнения — значок скрыт',
              (not cal_btn['btn']) or cal_btn['display'] == 'none', cal_btn)

    # C12: после «сворачивания» переполнения (фильтр по дню) значок исчезает
    page.evaluate("WorkSchedule._daySelect(3)")
    page.wait_for_timeout(300)
    filt = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var btn = ev.querySelector('.ws-bar-exp');
        return { items: ev.querySelectorAll('.ws-ep-item').length,
                 over: ev.scrollHeight > ev.clientHeight + 2,
                 display: btn ? getComputedStyle(btn).display : null,
                 h: ev.getBoundingClientRect().height };
    })()""")
    check('C12: фильтр по дню — меньше записей', filt['items'] <= 3, filt['items'])
    if not filt['over']:
        check('C13: переполнения нет — значок скрыт, окно 95px',
              (filt['display'] == 'none') and abs(filt['h'] - 95) < 3, filt)
    else:
        check('C13: записи всё ещё переполняют — значок на месте', filt['display'] != 'none', filt)
    page.evaluate("WorkSchedule._daySelect(3)")  # сброс выбора

    page.screenshot(path='/tmp/t378-%s.png' % theme, full_page=False)
    check('Z: 0 JS-ошибок (%s)' % theme, len(js_errors) == 0, js_errors[:2])
    ctx.close()
    return js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()
    errs_d = run(browser, 'dark')
    errs_l = run(browser, 'light')

    # ---------- МОБАЙЛ 375: чипы + значок ----------
    ctx = browser.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=1)
    page = ctx.new_page()
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t378-mob)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t378');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    mob = page.evaluate("""(function(){
        var chip = document.getElementById('wsChipEvents');
        var ev = document.getElementById('wsEventsPanel');
        var r = chip.getBoundingClientRect();
        return { chipVisible: r.width > 0, evHidden: ev.hidden,
                 cs: getComputedStyle(ev).scrollbarWidth };
    })()""")
    check('M1: мобильный чип «Мероприятия» виден', mob['chipVisible'], mob)
    page.locator('#wsChipEvents').click()
    page.wait_for_timeout(500)
    mob2 = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var btn = ev.querySelector('.ws-bar-exp');
        return { visible: ev.getBoundingClientRect().height > 0,
                 btn: !!btn,
                 display: btn ? getComputedStyle(btn).display : null,
                 h: ev.getBoundingClientRect().height,
                 scrollH: ev.scrollHeight };
    })()""")
    check('M2: чип раскрыл окно — окно видимо', mob2['visible'], mob2)
    if mob2['scrollH'] > 97:
        check('M3: значок раскрытия работает и на мобиле',
              mob2['btn'] and mob2['display'] != 'none', mob2)
    page.screenshot(path='/tmp/t378-mobile.png', full_page=False)
    check('M4: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:2])
    ctx.close()
    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
