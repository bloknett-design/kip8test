#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 401: browser-check — заявка «В десктопной версии приложения,
# в разделе Табель учёта рабочего времени, окно итогов учёта за год
# должно раскрываться полностью закрывая собой шахматку табеля,
# вплотную примыкая к правому краю столбца с фамилиями работников,
# и в шапке окна итогов учёта за год, под числами должно быть
# пояснение данных в ячейках "дней/часов", и три крайних правых
# столбца (дней, часов, перераб. (дни)) выделить фоном немного
# другого оттенка от остальных ячеек со столбцами месяцев, и
# разделить их вертикальной линией таблицы такой же как с левого
# края окна итогов учёта за год».
# МОК: 2 активных работника (Иванов сменный, Петров дневной) +
# 1 архивный (Архивный А.А.); записи месяцев 01/02/09.
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, КИП ИОС + workschedule.view:
#      «Итоги учёта» → «Год»: шторка на ВСЮ ширину правее ФИО
#      (левый край = правый край столбца ФИО, правый = правый край
#      рабочей области); шапка двухстрочная — подстрока
#      «дней/часов» (colspan 12); итоговые столбцы: фон другого
#      оттенка (th/td) + разделитель 2px #4a8fc7 слева от «Днев»;
#      полоса ФИО сетки скрыта, ползунок сетки погашен; таблица
#      100% ширины шторки; ресайз окна → пересчёт ширины;
#      0 JS-ошибок;
#   2) десктоп 1280 светлая — то же (цвета светлой темы #6e8ba4);
#   3) десктоп 1280 тёмная — РЕГРЕСС: «Год» → «Месяц»: шторка
#      сжимается по таблице месяца, класс снят, полоса ФИО и
#      ползунок сетки вернулись;
#   4) мобильный 375 светлая — СТРАНИЦА итогов, вкладка «Год»:
#      подстрока и итоговые классы рендерятся, шторки нет.
# Порт 8901 (запуск: python3 -m http.server 8901 &).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8901
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
  # архив — отдельным блоком в годовой таблице (свои строки)
  {'таб_номер': '900', 'ФИО': 'Архивный А. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2020-05-06', 'дата_увольнения': '%04d-06-30' % Y,
   'в_архиве': 1, 'должность': 'Инженер КИПиА', 'комментарий': ''},
]
# записи года: январь (1 день Иванову), февраль (2 дня архивному),
# сентябрь (Иванов 2 + Петров 1)
YEAR_ENTRIES = {
  1: [ {'дата': d(Y, 1, 15), 'таб_номер': '017', 'статус': 'Д'} ],
  2: [ {'дата': d(Y, 2, 3), 'таб_номер': '900', 'статус': 'Д'},
       {'дата': d(Y, 2, 4), 'таб_номер': '900', 'статус': 'Д'} ],
  9: [ {'дата': d(Y, 9, 1), 'таб_номер': '017', 'статус': 'Д'},
       {'дата': d(Y, 9, 2), 'таб_номер': '017', 'статус': 'Д'},
       {'дата': d(Y, 9, 5), 'таб_номер': '023', 'статус': 'Д8'} ],
}
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
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
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': 'КИП ИОС'}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'КИП ИОС', 'found': True,
                        'permissions': {'calc.view': True, 'library.view': True,
                            'kipios.view': True, 'secret.view': True, 'whatsnew.view': True,
                            'workschedule.view': True}}}, ensure_ascii=False))
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}))
        if action == 'workSchedule.getStatusCodes':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'codes': CODES}}, ensure_ascii=False))
        if action == 'workSchedule.listEmployees':
            inc = bool(body and body.get('includeArchived'))
            emps = EMPLOYEES if inc else [e for e in EMPLOYEES if not e['в_архиве']]
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'employees': emps}}, ensure_ascii=False))
        if action == 'workSchedule.getPatterns':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'patterns': PATTERNS}}, ensure_ascii=False))
        if action == 'workSchedule.listTrainings':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'trainings': []}}, ensure_ascii=False))
        if action == 'workSchedule.listVacations':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'vacations': []}}, ensure_ascii=False))
        if action == 'workSchedule.listPpe':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ppe': []}}, ensure_ascii=False))
        if action == 'workSchedule.listEntries':
            mm = int(body.get('month', M)) if body else M
            entries = YEAR_ENTRIES.get(mm, []) if mm in YEAR_ENTRIES else []
            if mm == M:
                entries = list(YEAR_ENTRIES.get(M, []))
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'entries': entries}}, ensure_ascii=False))
        if action == 'prodCalendar.getMonth':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                        'shortdays': 0, 'holidays': [], 'transfers': []}}))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t401-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t401-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# Сводная геометрия/стили годовой шторки (десктоп)
MEASURE_JS = """(function(){
    var body = document.getElementById('wsWsBody');
    var drawer = document.getElementById('wsTotalsDrawer');
    var page = document.getElementById('page-work-schedule');
    var gridWrap = document.getElementById('wsGridWrap');
    var panel = document.getElementById('wsTotalsPanel');
    var empTh = gridWrap ? gridWrap.querySelector('.ws-grid thead th.ws-emp-col') : null;
    var table = panel ? panel.querySelector('.ws-tt-table.ws-tt-year') : null;
    var ttBody = document.getElementById('wsTtBody');
    var sub = panel ? panel.querySelector('th.ws-tt-sub') : null;
    var sumTh = panel ? panel.querySelector('thead th.ws-tt-sum-edge') : null;
    var hoursTh = panel ? panel.querySelector('thead th.ws-tt-sum:not(.ws-tt-sum-edge)') : null;
    var sumTd = panel ? panel.querySelector('tbody td.ws-tt-sum-edge') : null;
    var monthTh = panel ? panel.querySelector('thead tr:first-child th:not(.ws-tt-sub):not(.ws-tt-sum):not(.ws-tt-emp)') : null;
    var monthTd = panel ? panel.querySelector('tbody td.ws-tt-num:not(.ws-tt-sum):not(.ws-tt-emp)') : null;
    var thead = panel ? panel.querySelector('.ws-tt-table.ws-tt-year thead') : null;
    var cs = function(el, prop, pe) {
        if (!el) return null;
        return getComputedStyle(el, pe || null).getPropertyValue(prop);
    };
    var dR = drawer ? drawer.getBoundingClientRect() : {width: 0, left: 0, right: 0};
    var bR = body ? body.getBoundingClientRect() : {width: 0, right: 0};
    var eR = empTh ? empTh.getBoundingClientRect() : {width: 0, right: 0};
    var hbarThumb = document.querySelector('#wsGridHbar .ws-hbar-thumb');
    return {
        bodyW: bR.width, bodyR: bR.right,
        drawerW: dR.width, drawerL: dR.left, drawerR: dR.right,
        empW: eR.width, empR: eR.right,
        yearfull: !!(page && page.classList.contains('ws-tt-yearfull')),
        theadRows: thead ? thead.querySelectorAll('tr').length : 0,
        subText: sub ? sub.textContent : null,
        subColspan: sub ? sub.getAttribute('colspan') : null,
        subVis: sub ? sub.getBoundingClientRect().height > 0 : false,
        sumThBg: cs(sumTh, 'background-color'),
        hoursThBg: cs(hoursTh, 'background-color'),
        monthThBg: cs(monthTh, 'background-color'),
        sumTdBg: cs(sumTd, 'background-color'),
        monthTdBg: cs(monthTd, 'background-color'),
        edgeW: cs(sumTh, 'border-left-width'),
        edgeC: cs(sumTh, 'border-left-color'),
        edgeWtd: cs(sumTd, 'border-left-width'),
        empAfter: empTh ? cs(empTh, 'display', '::after') : null,
        hbarThumbDisp: hbarThumb ? cs(hbarThumb, 'display') : 'нет',
        tableW: table ? table.getBoundingClientRect().width : 0,
        ttBodyW: ttBody ? ttBody.clientWidth : 0,
        cells: table ? table.querySelectorAll('tbody td.ws-tt-num').length : 0
    };
})()"""

def open_year(page):
    """Открыть итоги (месяц) → вкладку «Год»; ждём таблицу года."""
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(600)
    page.wait_for_selector('#wsTtTabYear:not([hidden])', timeout=4000)
    page.click('#wsTtTabYear')
    page.wait_for_selector('#wsTotalsPanel .ws-tt-table.ws-tt-year', timeout=8000)
    page.wait_for_timeout(700)   # рендер + _fitTtDrawer + анимация маржи

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, «Год» ==========
    print('=== Контекст 1: десктоп тёмная — «Год» на всю ширину ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'year-dark')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    open_year(page)
    m = page.evaluate(MEASURE_JS)
    # 1) полный режим и класс
    check('B1: класс ws-tt-yearfull на странице', m['yearfull'])
    # 2) шторка = рабочая область − колонка ФИО (вплотную к ФИО)
    check('B2: ширина шторки = рабочая область − ФИО (±4px)',
          abs(m['drawerW'] - (m['bodyW'] - m['empW'])) <= 4,
          (m['drawerW'], m['bodyW'], m['empW']))
    check('B3: левый край шторки = правый край столбца ФИО (±3px)',
          abs(m['drawerL'] - m['empR']) <= 3, (m['drawerL'], m['empR']))
    check('B4: правый край шторки = правый край рабочей области (±2px)',
          abs(m['drawerR'] - m['bodyR']) <= 2, (m['drawerR'], m['bodyR']))
    # 3) шахматка закрыта: дней сетки правее ФИО не видно
    vis_day = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var dR = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var days = wrap.querySelectorAll('tbody td[data-day]');
        var vis = 0;
        for (var i = 0; i < days.length; i++) {
            var r = days[i].getBoundingClientRect();
            if (r.left < dR.left && r.right > dR.left - 1) vis++;
        }
        return {total: days.length, vis: vis};
    })()""")
    check('B5: дни шахматки полностью закрыты шторкой',
          vis_day['total'] > 0 and vis_day['vis'] == 0, vis_day)
    # 4) шапка: подстрока «дней/часов»
    check('C1: шапка двухстрочная (2 tr в thead)', m['theadRows'] == 2, m['theadRows'])
    check('C2: подстрока «дней/часов» под месяцами (colspan=12)',
          m['subText'] == 'дней/часов' and m['subColspan'] == '12' and m['subVis'],
          (m['subText'], m['subColspan']))
    # 5) итоговые столбцы: фон другого оттенка
    check('D1: th «Дней» — фон ОТЛИЧАЕТСЯ от месяцев',
          m['sumThBg'] != m['monthThBg'], (m['sumThBg'], m['monthThBg']))
    check('D2: th «Часов» — тонировка та же, что у «Днев»',
          m['hoursThBg'] == m['sumThBg'], (m['hoursThBg'], m['sumThBg']))
    check('D3: td итоговых — фон тонирован (месяцы прозрачны)',
          m['sumTdBg'] != 'rgba(0, 0, 0, 0)' and m['monthTdBg'] == 'rgba(0, 0, 0, 0)',
          (m['sumTdBg'], m['monthTdBg']))
    # 6) разделитель 2px как .ws-tt-edge (#4a8fc7)
    check('E1: разделитель слева от «Днев» — 2px (th и td)',
          m['edgeW'] == '2px' and m['edgeWtd'] == '2px', (m['edgeW'], m['edgeWtd']))
    check('E2: цвет разделителя = .ws-tt-edge (rgb(74, 143, 199))',
          m['edgeC'] == 'rgb(74, 143, 199)', m['edgeC'])
    # 7) полоса ФИО скрыта, ползунок сетки погашен
    check('F1: полоса ФИО сетки (::after) скрыта', m['empAfter'] == 'none', m['empAfter'])
    check('F2: ползунок шахматки погашен', m['hbarThumbDisp'] == 'none', m['hbarThumbDisp'])
    # 8) таблица растянута на ширину шторки
    check('G1: таблица года = 100% ширины тела шторки (±3px)',
          abs(m['tableW'] - m['ttBodyW']) <= 3, (m['tableW'], m['ttBodyW']))
    check('G2: ячейки значений рендерятся (> 20)', m['cells'] > 20, m['cells'])
    page.screenshot(path='task401-proof-year-dark.png', full_page=False)
    # 9) ресайз окна — ширина пересчитывается
    page.set_viewport_size({'width': 1100, 'height': 900})
    page.wait_for_timeout(800)
    m2 = page.evaluate(MEASURE_JS)
    check('H1: ресайз 1100 — шторка переширотилась',
          abs(m2['drawerW'] - (m2['bodyW'] - m2['empW'])) <= 4,
          (m2['drawerW'], m2['bodyW'], m2['empW']))
    check('H2: класс полной ширины жив после ресайза', m2['yearfull'])
    page.screenshot(path='task401-proof-year-dark-1100.png', full_page=False)
    check('I: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, «Год» ==========
    print('=== Контекст 2: десктоп светлая — цвета светлой темы ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'year-light')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    open_year(page)
    m = page.evaluate(MEASURE_JS)
    check('J1: светлая — шторка на всю ширину (±4px)',
          abs(m['drawerW'] - (m['bodyW'] - m['empW'])) <= 4,
          (m['drawerW'], m['bodyW'], m['empW']))
    check('J2: подстрока «дней/часов» на месте',
          m['subText'] == 'дней/часов' and m['subVis'])
    check('J3: светлая — разделитель #6e8ba4 (rgb(110, 139, 164))',
          m['edgeC'] == 'rgb(110, 139, 164)', m['edgeC'])
    check('J4: светлая — th итоговых темнее месяцев',
          m['sumThBg'] != m['monthThBg'], (m['sumThBg'], m['monthThBg']))
    check('J5: светлая — td итоговых тонированы',
          m['sumTdBg'] != 'rgba(0, 0, 0, 0)' and m['monthTdBg'] == 'rgba(0, 0, 0, 0)',
          (m['sumTdBg'], m['monthTdBg']))
    page.screenshot(path='task401-proof-year-light.png', full_page=False)
    check('J6: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: десктоп 1280, тёмная — «Год» → «Месяц» ==========
    print('=== Контекст 3: регресс — возврат на «Месяц» ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'month-back')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    open_year(page)
    page.wait_for_selector('#wsTtTabMonth:not([hidden])', timeout=4000)
    page.click('#wsTtTabMonth')
    page.wait_for_selector('#wsTotalsPanel .ws-tt-table:not(.ws-tt-year)', timeout=6000)
    page.wait_for_timeout(700)
    m = page.evaluate(MEASURE_JS)
    check('K1: класс ws-tt-yearfull СНЯТ', not m['yearfull'])
    check('K2: шторка месяца СУЖЕНА (< полная ширина)',
          m['drawerW'] < m['bodyW'] - m['empW'] - 40, (m['drawerW'], m['bodyW'] - m['empW']))
    check('K3: полоса ФИО сетки ВЕРНУЛАСЬ', m['empAfter'] != 'none', m['empAfter'])
    page.screenshot(path='task401-proof-month-back.png', full_page=False)
    # повторное закрытие шторки — чистое состояние
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(500)
    closed = page.evaluate("(function(){var d=document.getElementById('wsTotalsDrawer');"
        "var p=document.getElementById('page-work-schedule');"
        "return {open: p.classList.contains('ws-tt-open'),"
        " yf: p.classList.contains('ws-tt-yearfull')};})()")
    check('K4: шторка закрылась (классы ws-tt-open сняты)',
          not closed['open'] and not closed['yf'], closed)
    check('K5: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 4: мобильный 375 светлая — страница итогов ==========
    print('=== Контекст 4: мобильный 375 светлая — страница итогов «Год» ===')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mob-year')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(600)
    page.wait_for_selector('#page-ws-totals.active', timeout=4000)
    page.click('#wsTtPageTabYear')
    page.wait_for_selector('#wsTtPageBody .ws-tt-table.ws-tt-year', timeout=8000)
    page.wait_for_timeout(600)
    mob = page.evaluate("""(function(){
        var pb = document.getElementById('wsTtPageBody');
        var sub = pb.querySelectorAll('th.ws-tt-sub');
        var sumTd = pb.querySelectorAll('td.ws-tt-sum');
        var sumEdge = pb.querySelectorAll('td.ws-tt-sum-edge');
        var arch = pb.querySelectorAll('.ws-tt-arch');
        var tabY = document.getElementById('wsTtPageTabYear');
        return { subs: sub.length, subText: sub.length ? sub[0].textContent : null,
                 colspan: sub.length ? sub[0].getAttribute('colspan') : null,
                 sumTds: sumTd.length, edges: sumEdge.length, arch: arch.length,
                 tabActive: tabY ? tabY.classList.contains('active') : false,
                 drawerW: (function(){var d=document.getElementById('wsTotalsDrawer');
                          var r=d.getBoundingClientRect(); return r.width;})() };
    })()""")
    check('L1: мобильная страница «Год» активна', mob['tabActive'])
    check('L2: подстрока «дней/часов» — в ОБОИХ таблицах (главная+архив)',
          mob['subs'] == 2 and mob['subText'] == 'дней/часов' and mob['colspan'] == '12',
          mob)
    check('L3: итоговые td — классы sum/sum-edge',
          mob['sumTds'] > 0 and mob['edges'] > 0, mob)
    check('L4: блок «Архив» рендерится (архивный работник)', mob['arch'] == 1, mob['arch'])
    check('L5: десктопной шторки на мобиле нет (width 0)', mob['drawerW'] == 0, mob['drawerW'])
    page.screenshot(path='task401-proof-mobile-year.png', full_page=False)
    check('L6: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
