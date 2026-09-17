#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377 (разведка 2): точечные замеры perceived-цветов границ шахматки:
# сэмплируем пиксели НА границах ячеек (top edge td, right edge td,
# низ шапки, границы ФИО) в обеих темах. Порт 8981.
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
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
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

JS_GEOM = """(function(){
    var grid = document.querySelector('#wsGridWrap table');
    if (!grid) return null;
    var out = {};
    function rect(el){ var r = el.getBoundingClientRect();
        return {x: r.x, y: r.y, w: r.width, h: r.height}; }
    // два соседних рабочих дня (не выходные, не сегодня): 2 и 3
    var td2 = grid.querySelector('tbody td.ws-cell[data-day="2"]');
    var td3 = grid.querySelector('tbody td.ws-cell[data-day="3"]');
    var th2 = grid.querySelector('thead th[data-day="2"]');
    var th3 = grid.querySelector('thead th[data-day="3"]');
    var emp = grid.querySelector('tbody td.ws-emp-col');
    var row0 = grid.querySelectorAll('tbody tr')[0];
    var row1 = grid.querySelectorAll('tbody tr')[1];
    var wrap = document.getElementById('wsGridWrap');
    out.wrap = rect(wrap);
    out.scrollY = wrap.scrollTop;
    out.td2 = rect(td2); out.td3 = rect(td3);
    out.th2 = rect(th2); out.th3 = rect(th3);
    out.emp = rect(emp);
    out.row0 = rect(row0); out.row1 = rect(row1);
    out.bgc2 = getComputedStyle(td2).backgroundColor;
    out.bgc3 = getComputedStyle(td3).backgroundColor;
    return out;
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t377-probe2)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','probe2');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    g = page.evaluate(JS_GEOM)
    print('=== %s ===' % theme)
    print('td2 bg=%s td3 bg=%s' % (g['bgc2'], g['bgc3']))
    # скриншот области сетки в device pixel (dsf=2)
    wrap = g['wrap']
    clip = {'x': wrap['x'], 'y': wrap['y'], 'width': min(wrap['w'], 900), 'height': min(wrap['h'], 200)}
    page.screenshot(path='scripts/t377-probe2-%s.png' % theme, clip=clip)
    from PIL import Image
    img = Image.open('scripts/t377-probe2-%s.png' % theme).convert('RGB')
    def px(cssx, cssy):
        # перевод css->скрин: скрин начинается в wrap.x,wrap.y; dsf=2
        ix = int((cssx - wrap['x']) * 2)
        iy = int((cssy - wrap['y']) * 2)
        ix = max(0, min(img.size[0]-1, ix))
        iy = max(0, min(img.size[1]-1, iy))
        return img.getpixel((ix, iy))
    def show(label, cssx, cssy):
        print('%-42s (%6.1f,%6.1f) -> rgb%s' % (label, cssx, cssy, px(cssx, cssy)))
    # вертикальная граница между днём 2 и 3 (тело): x = td3.left, y = центр td3
    cy3 = g['td3']['y'] + g['td3']['h']/2
    show('BODY: вертикаль день2|день3 (на границе)', g['td3']['x'], cy3)
    show('BODY: вертикаль день2|день3 (1px левее)', g['td3']['x']-1.5, cy3)
    show('BODY: вертикаль день2|день3 (центр дня 2)', g['td2']['x']+g['td2']['w']/2, cy3)
    # горизонтальная граница строка0|строка1 (тело): y = row1.top, x = центр дня 2
    cx2 = g['td2']['x'] + g['td2']['w']/2
    show('BODY: горизонталь строка0|строка1 (на границе)', cx2, g['row1']['y'])
    show('BODY: горизонталь строка0|строка1 (1px выше)', cx2, g['row1']['y']-1.5)
    # шапка: вертикаль между th2|th3
    chy = g['th3']['y'] + g['th3']['h']/2
    show('HEAD: вертикаль день2|день3 (на границе)', g['th3']['x'], chy)
    show('HEAD: вертикаль день2|день3 (центр дня 2)', g['th2']['x']+g['th2']['w']/2, chy)
    # низ шапки
    show('HEAD: низ шапки (на границе)', cx2, g['th2']['y']+g['th2']['h'])
    # ФИО правая граница
    show('BODY: ФИО правая граница', g['emp']['x']+g['emp']['w'], cy3)
    ctx.close()

with sync_playwright() as p:
    browser = p.chromium.launch()
    run(browser, 'dark')
    run(browser, 'light')
    browser.close()
print('DONE')
