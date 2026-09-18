#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 382: browser-check — заявка пользователя: «В мобильной
# версии, на странице итогов учёта, в таблице вкладки месяц
# изначальную ширину столбца с фамилиями сотрудников сделай по
# ширине текста в ячейках как на вкладке год».
# МОБАЙЛ 375 (обе темы):
#   M1  переменная --ws-tt-emp-w установлена на body (Npx);
#   M2  ширина th.ws-tt-emp месяцa = переменной (±1.5px);
#   M3  ширина = «естественная» (№ таб. + 5 маржи + ФИО + 16
#       паддинги + 2 запас) ±2.5px — как авто-раскладка «Года»;
#   M4  ФИО НЕ обрезаны (правый край спана ≤ правого края ячейки);
#   M5  столбцы данных РАВНЫЕ (fixed-раскладка жива);
#   M6  вкладка «Год»: ширина её th.ws-tt-emp ≈ месяцу (±3px) —
#       «как на вкладке год»; возврат на «Месяц» — переменная и
#       ширина восстанавливаются (замер после перерисовки);
#   M7  сужение при прокрутке живо (ws-narrow → --ws-tt-emp-nw,
#       № таб. скрыт; возврат scrollLeft=0 → полная ширина);
#   M8  колонка УЖЕ доли 42% (стала заметно у́же прежнего);
#   M9  0 JS-ошибок.
# ДЕСКТОП 1280: колонка месяца скрыта (display:none — не тронуто),
#   переменная пишется и там (замер без CSS-эффекта), 0 JS-ошибок.
# Пиксельный пруф (светлая): вертикальная линия границы колонки
#   на ожидаемом x (th.right) в строке данных. Порт 8992.
import calendar, datetime, json, re
from urllib.parse import unquote
from PIL import Image
from playwright.sync_api import sync_playwright

PORT = 8992
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
  # САМАЯ ДЛИННАЯ ФИО — задаёт ширину колонки (max замера);
  # реалистичная длина — разница с прежней долей 42% заметна
  {'таб_номер': '018', 'ФИО': 'Сергеев Андрей Викторович', 'тип': 'сменный', 'смена': 2,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Пётр Петров', 'тип': 'дневной', 'смена': '',
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t382-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t382');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# Месячная таблица страницы итогов: ширины колонки/натурального
# текста/столбцов данных + переменные body
MONTH_JS = """(function(){
    var body = document.getElementById('wsTtPageBody');
    var t = body ? body.querySelector('.ws-tt-table') : null;
    if (!t) return { err: 'NO TABLE' };
    var th = t.querySelector('thead th.ws-tt-emp');
    var tds = t.querySelectorAll('tbody td.ws-tt-emp');
    var maxNat = 0, clipped = 0;
    for (var i = 0; i < tds.length; i++) {
        var tno = tds[i].querySelector('.ws-tt-tabno');
        var nm = tds[i].querySelector('.ws-tt-name');
        var w = (tno ? tno.getBoundingClientRect().width + 5 : 0)
              + (nm ? nm.getBoundingClientRect().width : 0);
        if (w > maxNat) maxNat = w;
        // ФИО не обрезано: правый край спана внутри ячейки
        if (nm && tds[i].getBoundingClientRect) {
            var nr = nm.getBoundingClientRect().right;
            var tr = tds[i].getBoundingClientRect().right - 8;
            if (nr > tr + 0.5) clipped++;
        }
    }
    var head = t.querySelector('.ws-tt-emp-head');
    var hw = head ? head.getBoundingClientRect().width : 0;
    var dths = t.querySelectorAll('thead th');
    var dw = [];
    for (var k = 1; k < Math.min(4, dths.length); k++) {
        dw.push(dths[k].getBoundingClientRect().width);
    }
    return {
        thW: th.getBoundingClientRect().width,
        thDisplay: getComputedStyle(th).display,
        varW: document.body.style.getPropertyValue('--ws-tt-emp-w'),
        varNw: document.body.style.getPropertyValue('--ws-tt-emp-nw'),
        maxNat: maxNat, headW: hw,
        clipped: clipped,
        dataW: dw,
        narrow: t.classList.contains('ws-narrow'),
        tableW: t.getBoundingClientRect().width,
        tabnoD: tds.length ? getComputedStyle(
            tds[0].querySelector('.ws-tt-tabno')).display : null,
        nRows: tds.length,
        bodyScrollW: body.scrollWidth, bodyClientW: body.clientWidth
    };
})()"""

# Годовая таблица страницы итогов: ширина её колонки «Сотрудник»
YEAR_JS = """(function(){
    var body = document.getElementById('wsTtPageBody');
    var t = body ? body.querySelector('.ws-tt-table.ws-tt-year') : null;
    if (!t) return { err: 'NO YEAR TABLE' };
    var th = t.querySelector('thead th.ws-tt-emp');
    return { thW: th.getBoundingClientRect().width };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= МОБАЙЛ 375: обе темы =================
    for theme in ('dark', 'light'):
        print('--- МОБАЙЛ 375, тема %s ---' % theme)
        ctx = browser.new_context(viewport={'width': 375, 'height': 812},
                                  device_scale_factor=2)
        page = ctx.new_page()
        js_errors = attach(page, ctx, theme, 'mob-%s' % theme)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2000)
        page.locator('#wsTotalsBtn').click()
        page.wait_for_timeout(900)

        r = page.evaluate(MONTH_JS)
        if 'err' in r:
            check('M0: месячная таблица отрисована (%s)' % theme, False, r)
        else:
            var_px = float(r['varW'].replace('px', '')) if r['varW'] else 0.0
            check('M1: --ws-tt-emp-w установлена (%s)' % theme,
                  bool(r['varW']) and var_px > 60, r['varW'])
            check('M2: ширина th = переменной ±1.5px (%s)' % theme,
                  abs(r['thW'] - var_px) <= 1.5, (r['thW'], var_px))
            check('M3: ширина = натуральный текст + 18 ±2.5px (%s)' % theme,
                  abs(r['thW'] - (r['maxNat'] + 18)) <= 2.5,
                  (r['thW'], r['maxNat']))
            check('M4: ФИО НЕ обрезаны (0 клиппинга; %s)' % theme,
                  r['clipped'] == 0, r['clipped'])
            check('M5: столбцы данных РАВНЫЕ ±1px (%s)' % theme,
                  len(r['dataW']) >= 2 and
                  abs(r['dataW'][0] - r['dataW'][1]) <= 1.0, r['dataW'])
            check('M8: колонка у́же прежних 42%%×0.85 (%s)' % theme,
                  r['thW'] < 0.42 * r['tableW'] * 0.85,
                  (r['thW'], r['tableW'], 0.42 * r['tableW']))
            print('    ширина колонки %.1fpx = переменная %s; натуральный '
                  'текст %.1fpx; таблица %.0fpx (%s)' %
                  (r['thW'], r['varW'], r['maxNat'], r['tableW'], theme))

            # ---------- вкладка «Год» ----------
            page.locator('#wsTtPageTabYear').click()
            page.wait_for_timeout(1600)
            y = page.evaluate(YEAR_JS)
            check('M6a: год — ширина колонки ≈ месячной ±3px (%s)' % theme,
                  'err' not in y and abs(y['thW'] - var_px) <= 3.0,
                  (y.get('thW'), var_px))
            # возврат на «Месяц» — переменная и ширина восстановлены
            page.locator('#wsTtPageTabMonth').click()
            page.wait_for_timeout(900)
            r2 = page.evaluate(MONTH_JS)
            var2 = float(r2['varW'].replace('px', '')) if r2['varW'] else 0.0
            check('M6b: возврат на месяц — переменная та же (%s)' % theme,
                  abs(var2 - var_px) <= 0.5, (r2.get('varW'), r['varW']))
            check('M6c: возврат — ширина снова = переменной (%s)' % theme,
                  abs(r2['thW'] - var2) <= 1.5, (r2.get('thW'), var2))

            # ---------- сужение при прокрутке живо ----------
            page.evaluate(
                "document.getElementById('wsTtPageBody').scrollLeft = 250")
            page.wait_for_timeout(700)
            r3 = page.evaluate(MONTH_JS)
            varnw = float(r['varNw'].replace('px', '')) if r['varNw'] else 0.0
            check('M7a: ws-narrow включён, ширина = --ws-tt-emp-nw (%s)' % theme,
                  r3['narrow'] and abs(r3['thW'] - varnw) <= 2.0,
                  (r3.get('narrow'), r3.get('thW'), r['varNw']))
            check('M7b: № таб. скрыт при сужении (%s)' % theme,
                  r3['tabnoD'] == 'none', r3.get('tabnoD'))
            page.evaluate(
                "document.getElementById('wsTtPageBody').scrollLeft = 0")
            page.wait_for_timeout(700)
            r4 = page.evaluate(MONTH_JS)
            check('M7c: возврат scrollLeft=0 — полная ширина (%s)' % theme,
                  not r4['narrow'] and abs(r4['thW'] - var_px) <= 1.5,
                  (r4.get('narrow'), r4.get('thW')))

            # ---------- пиксельный пруф (граница колонки) ----------
            if theme == 'light':
                geo = page.evaluate("""(function(){
                    var body = document.getElementById('wsTtPageBody');
                    var t = body.querySelector('.ws-tt-table');
                    var th = t.querySelector('thead th.ws-tt-emp');
                    var tr = t.querySelector('tbody tr');
                    var thr = th.getBoundingClientRect();
                    var trr = tr.getBoundingClientRect();
                    return { x: thr.right, rowY: (trr.top + trr.bottom) / 2 };
                })()""")
                page.screenshot(path='/tmp/t382-mobile-light.png', full_page=False)
                img = Image.open('/tmp/t382-mobile-light.png').convert('RGB')
                # device_scale_factor=2 → координаты ×2; scrollLeft=0
                # (возврат M7c) — таблица от левого края видна
                x2 = int(round(geo['x'] * 2))
                y2 = int(round(geo['rowY'] * 2))
                # граница td.ws-tt-emp светлой темы — стальная
                # rgb(64,80,102) (Task 378) на фоне панели (233,231,222)
                found = None
                for dx in range(-4, 5):
                    for dy in range(-4, 5):
                        try:
                            c = img.getpixel((x2 + dx, y2 + dy))
                            dc = ((c[0]-64)**2 + (c[1]-80)**2 + (c[2]-102)**2) ** 0.5
                            db = ((c[0]-233)**2 + (c[1]-231)**2 + (c[2]-222)**2) ** 0.5
                            if dc <= 30 and db > 40:
                                found = c
                        except Exception:
                            pass
                check('P1: вертикальная линия границы колонки на x=th.right '
                      '(светлая, rgb≈(64,80,102))', found is not None, found)

        check('M9: 0 JS-ошибок (%s)' % theme, len(js_errors) == 0, js_errors[:2])
        ctx.close()

    # ================= ДЕСКТОП 1280 (санити) =================
    for theme in ('dark', 'light'):
        print('--- ДЕСКТОП 1280, тема %s ---' % theme)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        js_errors = attach(page, ctx, theme, 'desk-%s' % theme)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2000)
        page.locator('#wsTotalsBtn').click()
        page.wait_for_timeout(900)
        d = page.evaluate("""(function(){
            var t = document.querySelector('#wsTtBody .ws-tt-table');
            if (!t) return { err: 'NO TABLE' };
            var th = t.querySelector('thead th.ws-tt-emp');
            return {
                empD: th ? getComputedStyle(th).display : null,
                varW: document.body.style.getPropertyValue('--ws-tt-emp-w')
            };
        })()""")
        check('D1: десктоп — колонка месяца СКРЫТА (%s)' % theme,
              'err' not in d and d['empD'] == 'none', d.get('empD'))
        check('D2: переменная пишется и на десктопе (без CSS-эффекта; %s)'
              % theme, 'err' not in d and bool(d['varW']), d.get('varW'))
        check('D3: 0 JS-ошибок (%s)' % theme, len(js_errors) == 0, js_errors[:2])
        ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
print('Сегодня: %s' % TODAY_ISO)
