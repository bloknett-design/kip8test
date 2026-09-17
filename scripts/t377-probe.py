#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377 (разведка): замер ФАКТИЧЕСКИХ цветов разделительных полос шахматки
# табеля в тёмной и светлой теме + скриншоты обеих тем для сравнения глазами.
# Порт 8981. Ничего не правит — только читает.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8981
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск ежегодный основной', 'color': '#ECEFF1'},
  {'code': '.', 'name': 'Плановый выходной день', 'color': '#EEF0F2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
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
  {'id': 2, 'дата': '%04d-%02d-%02d' % (Y, M, 3), 'таб_номер': '023', 'статус': 'Д8', 'источник': 'авто'},
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

JS_MEASURE = """(function(){
    var out = {};
    var grid = document.querySelector('#wsGridWrap table');
    if (!grid) return null;
    var th = grid.querySelector('thead th.ws-day-col:not(.ws-emp-col)');
    var tdDay = grid.querySelector('tbody td.ws-cell[data-day]');
    var tdToday = grid.querySelector('tbody td.ws-cell.ws-today');
    var thToday = grid.querySelector('thead th.ws-day-col.ws-today-col');
    var tdEmp = grid.querySelector('tbody td.ws-emp-col');
    function cs(el){ return el ? getComputedStyle(el) : null; }
    var cth = cs(th), ctd = cs(tdDay), cemp = cs(tdEmp),
        ctToday = cs(tdToday), cthToday = cs(thToday);
    out.thBorder = cth ? [cth.borderTopColor, cth.borderRightColor, cth.borderBottomColor] : null;
    out.tdDayBorder = ctd ? [ctd.borderTopColor, ctd.borderRightColor, ctd.borderBottomColor] : null;
    out.tdEmpBorder = cemp ? [cemp.borderTopColor, cemp.borderRightColor] : null;
    out.tdTodayShadow = ctToday ? ctToday.boxShadow : null;
    out.thTodayBg = cthToday ? cthToday.backgroundImage : null;
    out.thTodayColor = cthToday ? cthToday.color : null;
    out.tdDayBg = ctd ? ctd.backgroundColor : null;
    out.tdDayFilter = ctd ? ctd.filter : null;
    //today column date
    out.todayDay = thToday ? thToday.getAttribute('data-day') : null;
    out.tdTodayBg = tdToday ? tdToday.backgroundColor : null;
    return out;
})()"""

def run(browser, theme):
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t377-probe)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','probe-t377');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    res = page.evaluate(JS_MEASURE)
    print('=== THEME: %s ===' % theme)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print('JS errors:', js_errors[:3])
    page.screenshot(path='scripts/t377-probe-%s.png' % theme, full_page=False)
    # прицельный кроп шахматки
    grid = page.query_selector('#wsGridWrap')
    if grid:
        grid.screenshot(path='scripts/t377-probe-grid-%s.png' % theme)
    ctx.close()
    return res

with sync_playwright() as p:
    browser = p.chromium.launch()
    dark = run(browser, 'dark')
    light = run(browser, 'light')
    browser.close()
print('DONE')
