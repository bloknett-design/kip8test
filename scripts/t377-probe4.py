#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377 (разведка 4, финальная): 3 сотрудника (2 сменных + 1 дневной):
# обычный 1px разделитель строк + групповой 2px (ws-group-first) + вертикаль.
# Обе темы. dsf=2. Порт 8981.
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
ENTRIES = []

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
        return {'ok': True, 'data': {'entries': []}}
    return {'ok': True, 'data': {'ok': True}}

JS_GEOM = """(function(){
    var grid = document.querySelector('#wsGridWrap table');
    if (!grid) return null;
    function rect(el){ var r = el.getBoundingClientRect();
        return {x: r.x, y: r.y, w: r.width, h: r.height}; }
    var rows = grid.querySelectorAll('tbody tr');
    var r0 = rect(rows[0]), r1 = rect(rows[1]), r2 = rect(rows[2]);
    var wrap = document.getElementById('wsGridWrap');
    // td дня 1 и 2 строки 0 (пустые)
    var tdA = rows[0].querySelector('td.ws-cell[data-day="1"]');
    var tdB = rows[0].querySelector('td.ws-cell[data-day="2"]');
    return {wrap: rect(wrap), r0: r0, r1: r1, r2: r2,
            tdA: rect(tdA), tdB: rect(tdB)};
})()"""

def run(browser, theme):
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=2)
    page = ctx.new_page()
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t377-probe4)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','probe4');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    g = page.evaluate(JS_GEOM)
    wrap = g['wrap']
    clip = {'x': wrap['x'], 'y': wrap['y'], 'width': min(wrap['w'], 900), 'height': min(wrap['h'], 300)}
    page.screenshot(path='scripts/t377-probe4-%s.png' % theme, clip=clip)
    img = Image.open('scripts/t377-probe4-%s.png' % theme).convert('RGB')
    def px(cssx, cssy):
        ix = int(round((cssx - wrap['x']) * 2))
        iy = int(round((cssy - wrap['y']) * 2))
        ix = max(0, min(img.size[0]-1, ix)); iy = max(0, min(img.size[1]-1, iy))
        return img.getpixel((ix, iy))
    print('=== %s === r0.h=%.1f r1.h=%.1f r2.h=%.1f' % (theme, g['r0']['h'], g['r1']['h'], g['r2']['h']))
    cx = g['tdA']['x'] + g['tdA']['w']/2
    # обычный разделитель r0|r1
    y01 = g['r1']['y']
    print('ОБЫЧНЫЙ разделитель r0|r1 (y=%.1f):' % y01)
    for dy in [-2,-1.5,-1,-0.5,0,0.5,1,1.5,2]:
        print('  dy=%+.1f -> %s' % (dy, px(cx, y01+dy)))
    # групповой разделитель r1|r2 (2px)
    y12 = g['r2']['y']
    print('ГРУППОВОЙ разделитель r1|r2 (y=%.1f):' % y12)
    for dy in [-2,-1.5,-1,-0.5,0,0.5,1,1.5,2]:
        print('  dy=%+.1f -> %s' % (dy, px(cx, y12+dy)))
    # вертикаль день1|день2
    bx = g['tdB']['x']
    cy = g['tdB']['y'] + g['tdB']['h']/2
    print('ВЕРТ. день1|день2 (x=%.1f):' % bx)
    for dx in [-1.5,-1,-0.5,0,0.5,1,1.5]:
        print('  dx=%+.1f -> %s' % (dx, px(bx+dx, cy)))
    ctx.close()

with sync_playwright() as p:
    browser = p.chromium.launch()
    run(browser, 'dark')
    run(browser, 'light')
    browser.close()
print('DONE')
