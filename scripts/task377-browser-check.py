#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377: browser-check — заявки пользователя:
#   1) «В шахматке Табель учёта рабочего времени, выделение текущего
#      дня сделай посильнее» — заливки 0.30/0.22, шапка 0.40/0.26 +
#      полоса ::after 2px, составные правила: hover/select столбца
#      «сегодня» НЕ гасят подсветку (computed остаётся ≥ уровня).
#   2) «В светлой теме, разделительные полосы ячеек шахматки такого
#      же цвета, как в тёмной теме» — computed border-color:
#      дни rgb(10,15,23) / ФИО rgb(64,80,102) / шапка rgb(83,96,117);
#      пиксельное сравнение линий между темами (вертикаль + горизонталь);
#      красная рамка выходных ws-wgrp в светлой теме НЕ перекрашена.
# + 0 JS-ошибок; скриншот-пруфы обеих тем. Порт 8981.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from PIL import Image

PORT = 8981
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
   'должность': 'Слесарь КИПиА', 'комментарий': ''}
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
        return {'ok': True, 'data': {'trainings': []}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok': True, 'data': {'entries': ENTRIES}}
        return {'ok': True, 'data': {'entries': []}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

JS_STATE = """(function(){
    var grid = document.querySelector('#wsGridWrap table');
    if (!grid) return null;
    var thToday = grid.querySelector('thead th.ws-day-col.ws-today-col');
    var tdToday = grid.querySelector('tbody td.ws-cell.ws-today');
    var tdDay = grid.querySelector('tbody td.ws-cell[data-day="1"]');
    var thDay = grid.querySelector('thead th.ws-day-col[data-day="1"]');
    var tdEmp = grid.querySelector('tbody td.ws-emp-col');
    var rows = grid.querySelectorAll('tbody tr');
    var r0 = rows[0].getBoundingClientRect();
    var r1 = rows[1].getBoundingClientRect();
    var tdt = tdToday.getBoundingClientRect();
    var tdd = tdDay.getBoundingClientRect();
    var cs = getComputedStyle(tdToday);
    var csH = getComputedStyle(thToday);
    var csA = getComputedStyle(thToday, '::after');
    return {
        todayDay: thToday ? thToday.getAttribute('data-day') : null,
        shadow: cs.boxShadow,
        headerBg: csH.backgroundImage,
        headerWeight: csH.fontWeight,
        afterContent: csA.content, afterH: csA.height, afterPos: csA.position,
        afterBg: csA.backgroundColor, afterBottom: csA.bottom,
        dayBorder: getComputedStyle(tdDay).borderTopColor,
        empBorder: getComputedStyle(tdEmp).borderRightColor,
        headBorder: getComputedStyle(thDay).borderTopColor,
        wrap: (function(){ var w = document.getElementById('wsGridWrap');
            var r = w.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; })(),
        todayRect: {x: tdt.x, y: tdt.y, w: tdt.width, h: tdt.height},
        dayRect: {x: tdd.x, y: tdd.y, w: tdd.width, h: tdd.height},
        row0y: r0.y, row1y: r1.y
    };
})()"""

def run(browser, theme):
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=2)
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t377-check)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t377');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)

    st = page.evaluate(JS_STATE)
    print('=== %s (сегодня: %s) ===' % (theme, st['todayDay']))
    if theme == 'dark':
        check('A: заливка «сегодня» 0.30', 'rgba(74, 143, 199, 0.3)' in st['shadow'], st['shadow'])
        check('B: шапка градиент 0.40', 'rgba(74, 143, 199, 0.4)' in st['headerBg'], st['headerBg'])
        check('C: число жирное (700)', st['headerWeight'] == '700', st['headerWeight'])
    else:
        check('A: заливка «сегодня» 0.22', 'rgba(42, 93, 143, 0.22)' in st['shadow'], st['shadow'])
        check('B: шапка градиент 0.26', 'rgba(42, 93, 143, 0.26)' in st['headerBg'], st['headerBg'])
        check('C: число жирное (700)', st['headerWeight'] == '700', st['headerWeight'])
    check('D: полоса ::after жива (2px, absolute, внизу)',
          st['afterH'] == '2px' and st['afterPos'] == 'absolute' and st['afterBottom'] == '0px'
          and st['afterContent'] == '""',
          (st['afterContent'], st['afterH'], st['afterPos'], st['afterBottom']))
    if theme == 'dark':
        check('E: полоса — акцент тёмной', 'rgb(74, 143, 199)' in st['afterBg'], st['afterBg'])
    else:
        check('E: полоса — акцент светлой', 'rgb(42, 93, 143)' in st['afterBg'], st['afterBg'])

    # --- полосы: computed ---
    if theme == 'light':
        check('F: дни rgb(10,15,23)', st['dayBorder'] == 'rgb(10, 15, 23)', st['dayBorder'])
        check('G: ФИО rgb(64,80,102)', st['empBorder'] == 'rgb(64, 80, 102)', st['empBorder'])
        check('H: шапка rgb(83,96,117)', st['headBorder'] == 'rgb(83, 96, 117)', st['headBorder'])
        # красная рамка выходных не перекрашена
        red = page.evaluate("""(function(){
            var el = document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-wgrp-first');
            return el ? getComputedStyle(el).borderLeftColor : null;
        })()""")
        check('I: красная рамка выходных жива (ws-wgrp-first)',
              red == 'rgb(229, 115, 115)', red)
    else:
        check('F: тёмная дни rgba(0,0,0,0.3)', 'rgba(0, 0, 0, 0.3)' in st['dayBorder'], st['dayBorder'])
        check('G: тёмная ФИО rgba(105,130,160,0.55)', 'rgba(105, 130, 160, 0.55)' in st['empBorder'], st['empBorder'])
        check('H: тёмная шапка rgba(140,158,188,0.55)', 'rgba(140, 158, 188, 0.55)' in st['headBorder'], st['headBorder'])

    # --- составные правила: hover/select НЕ гасят «сегодня» ---
    day = st['todayDay']
    page.evaluate('WorkSchedule._dayHover(%s)' % day)
    sh = page.evaluate("(function(){var el=document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-today');return getComputedStyle(el).boxShadow;})()")
    if theme == 'dark':
        check('J: hover столбца «сегодня» не гасит (0.30)', 'rgba(74, 143, 199, 0.3)' in sh, sh)
    else:
        check('J: hover столбца «сегодня» не гасит (0.22)', 'rgba(42, 93, 143, 0.22)' in sh, sh)
    page.evaluate('WorkSchedule._dayHover(null)')
    page.evaluate('WorkSchedule._daySelect(%s)' % day)
    sh2 = page.evaluate("(function(){var el=document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-today');return getComputedStyle(el).boxShadow;})()")
    if theme == 'dark':
        check('K: select столбца «сегодня» → 0.34', 'rgba(74, 143, 199, 0.34)' in sh2, sh2)
    else:
        check('K: select столбца «сегодня» → 0.26', 'rgba(42, 93, 143, 0.26)' in sh2, sh2)
    hb = page.evaluate("(function(){var el=document.querySelector('#wsGridWrap table thead th.ws-day-col.ws-today-col');return getComputedStyle(el).backgroundImage;})()")
    if theme == 'dark':
        check('L: шапка при select — 0.44', 'rgba(74, 143, 199, 0.44)' in hb, hb)
    else:
        check('L: шапка при select — 0.30', 'rgba(42, 93, 143, 0.3)' in hb, hb)
    page.evaluate('WorkSchedule._daySelect(null)')

    # --- пиксели: линии между темами совпадают ---
    # полностраничный скриншот (страница не скроллена): css->device = *2;
    # clip НЕ используем — узкий clip «сжимал» замеры за пределами clip
    # в один краевой пиксель (урок этой проверки)
    page.screenshot(path='scripts/task377-proof-%s.png' % theme,
                    clip={'x': 0, 'y': st['wrap']['y'],
                          'width': 1280, 'height': min(st['wrap']['h'], 300)})
    page.screenshot(path='/tmp/t377-full-%s.png' % theme)
    img = Image.open('/tmp/t377-full-%s.png' % theme).convert('RGB')
    def px(cssx, cssy):
        ix = int(round(cssx * 2))
        iy = int(round(cssy * 2))
        ix = max(0, min(img.size[0]-1, ix)); iy = max(0, min(img.size[1]-1, iy))
        return img.getpixel((ix, iy))
    # тинт «сегодня» в пикселях: центр ячейки отличается от фона пустой
    tbg = px(st['todayRect']['x'] + st['todayRect']['w']/2,
             st['todayRect']['y'] + st['todayRect']['h']/2)
    nbg = px(st['dayRect']['x'] + st['dayRect']['w']/2,
             st['todayRect']['y'] + st['todayRect']['h']/2)
    tint_dist = sum(abs(a - b) for a, b in zip(tbg, nbg))
    check('P: тинт «сегодня» виден в пикселях (Δ≥20 от пустой ячейки)',
          tint_dist >= 20, (tbg, nbg, tint_dist))
    # вертикальная граница сегодня|завтра (правый край today td):
    # 1px-линия лежит со смещением до 0.5px — сканируем ±1px, берём
    # пиксель, наиболее отличный от фона ячейки
    bx = st['todayRect']['x'] + st['todayRect']['w']
    cy = st['todayRect']['y'] + st['todayRect']['h']/2
    bgc = px(st['todayRect']['x'] + st['todayRect']['w']/2, cy)
    best = None
    for dx in (-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1):
        c = px(bx + dx, cy)
        dist = sum(abs(a - b) for a, b in zip(c, bgc))
        if best is None or dist > best[0]:
            best = (dist, c)
    vline = best[1]
    # горизонтальная граница строка0|строка1 в столбце «сегодня»
    # (скан ±1px по вертикали, самый непохожий на фон)
    hy = st['row1y']
    cx = st['todayRect']['x'] + st['todayRect']['w']/2
    bgc2 = px(cx, cy)
    best2 = None
    for dy in (-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1):
        c = px(cx, hy + dy)
        dist = sum(abs(a - b) for a, b in zip(c, bgc2))
        if best2 is None or dist > best2[0]:
            best2 = (dist, c)
    hline = best2[1]
    print('  линии: верт=%s гориз=%s' % (vline, hline))
    lines = {'v': vline, 'h': hline}
    ctx.close()
    return lines, js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()
    dark_lines, dark_errs = run(browser, 'dark')
    light_lines, light_errs = run(browser, 'light')
    browser.close()

# --- сравнение линий между темами ---
def close(a, b, tol=6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))
check('M: ВЕРТ. линия одинакова в обеих темах (±6)',
      close(dark_lines['v'], light_lines['v']), (dark_lines['v'], light_lines['v']))
check('N: ГОРИЗ. линия одинакова в обеих темах (±6)',
      close(dark_lines['h'], light_lines['h']), (dark_lines['h'], light_lines['h']))
check('O: 0 JS-ошибок (обе темы)', len(dark_errs) == 0 and len(light_errs) == 0,
      (dark_errs[:2], light_errs[:2]))

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
