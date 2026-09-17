#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377 (разведка 3): скан профилей поперёк границ шахматки:
# вертикальная граница между двумя ПУСТЫМИ ячейками, горизонтальная между
# строками, в тёмной и светлой теме. dsf=2.
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
    // ищем две соседние ПУСТЫЕ ячейки (без inline-фона) в строке 0
    var row0 = grid.querySelectorAll('tbody tr')[0];
    var tds = row0.querySelectorAll('td.ws-cell');
    var pair = null;
    for (var i = 0; i < tds.length - 1; i++) {
        if (!tds[i].style.background && !tds[i+1].style.background) {
            pair = {a: rect(tds[i]), b: rect(tds[i+1]),
                    da: tds[i].getAttribute('data-day'), db: tds[i+1].getAttribute('data-day')};
            break;
        }
    }
    var row1 = grid.querySelectorAll('tbody tr')[1];
    var wrap = document.getElementById('wsGridWrap');
    return {wrap: rect(wrap), pair: pair,
            row1y: rect(row1).y, row0: rect(row0),
            tdAx: pair ? pair.a.x : null, tdAw: pair ? pair.a.w : null};
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t377-probe3)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','probe3');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    g = page.evaluate(JS_GEOM)
    wrap = g['wrap']
    clip = {'x': wrap['x'], 'y': wrap['y'], 'width': min(wrap['w'], 900), 'height': min(wrap['h'], 220)}
    page.screenshot(path='scripts/t377-probe3-%s.png' % theme, clip=clip)
    img = Image.open('scripts/t377-probe3-%s.png' % theme).convert('RGB')
    print('=== %s === (пара пустых: день %s|%s)' % (theme, g['pair']['da'], g['pair']['db']))
    # скан поперёк ВЕРТИКАЛЬНОЙ границы между двумя пустыми ячейками
    bx = g['pair']['b']['x']  # граница
    cy = g['pair']['b']['y'] + g['pair']['b']['h']/2
    print('ВЕРТ. граница (x=%.1f..%.1f, y=%.1f):' % (bx-3, bx+3, cy))
    for dx in [-3, -2, -1.75, -1.5, -1.25, -1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3]:
        ix = int(round((bx + dx - wrap['x']) * 2))
        iy = int(round((cy - wrap['y']) * 2))
        ix = max(0, min(img.size[0]-1, ix)); iy = max(0, min(img.size[1]-1, iy))
        print('  dx=%+.2f -> %s' % (dx, img.getpixel((ix, iy))))
    # скан поперёк ГОРИЗОНТАЛЬНОЙ границы row0|row1 на центре пустой ячейки
    hy = g['row1y']
    cx = g['pair']['a']['x'] + g['pair']['a']['w']/2
    print('ГОРИЗ. граница (y=%.1f..%.1f, x=%.1f):' % (hy-3, hy+3, cx))
    for dy in [-3, -2, -1.75, -1.5, -1.25, -1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3]:
        iy = int(round((hy + dy - wrap['y']) * 2))
        ix = int(round((cx - wrap['x']) * 2))
        iy = max(0, min(img.size[1]-1, iy)); ix = max(0, min(img.size[0]-1, ix))
        print('  dy=%+.2f -> %s' % (dy, img.getpixel((ix, iy))))
    ctx.close()

with sync_playwright() as p:
    browser = p.chromium.launch()
    run(browser, 'dark')
    run(browser, 'light')
    browser.close()
print('DONE')
