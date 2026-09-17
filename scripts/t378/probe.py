#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 378 РАЗВЕДКА: скриншоты табеля с открытой шторкой «Итоги учёта»
# (обе темы) + с баром окон мероприятий/норм — чтобы понять контекст заявки.
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8983
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
TRAININGS = [
  {'id': 7, 'тема': 'Повторный инструктаж по охране труда', 'код': 'И',
   'дата_начала': '%04d-%02d-04' % (Y, M), 'дата_окончания': '%04d-%02d-05' % (Y, M),
   'таб_номер': '017', 'подразделение': ''},
  {'id': 8, 'тема': 'Пожарная безопасность', 'код': 'ОБ',
   'дата_начала': '%04d-%02d-10' % (Y, M), 'дата_окончания': '%04d-%02d-11' % (Y, M),
   'таб_номер': '018', 'подразделение': ''},
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

with sync_playwright() as p:
    browser = p.chromium.launch()
    for theme in ('light', 'dark'):
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
            route.fulfill(status=404, content_type='text/plain', body='not found (t378-probe)')
        ctx.route('**raw.githubusercontent.com/**', block_external)
        ctx.route('**calendar.legalic.ru/**', block_external)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t378');" +
            "localStorage.setItem('kip8test:app-theme','%s');" % theme)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        # открыть раздел «Табель учёта рабочего времени»
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1800)
        # открыть шторку «Итоги учёта»
        page.evaluate("document.getElementById('wsTotalsBtn').click()")
        page.wait_for_timeout(1200)
        page.screenshot(path='/tmp/t378-drawer-%s.png' % theme, full_page=False)
        print(theme, 'drawer:', 'errors=', js_errors[:2])
        # состояние: вычисленные стили ячеек таблицы итогов
        info = page.evaluate("""(function(){
            var t = document.querySelector('#wsTtBody .ws-tt-table');
            if (!t) return 'no table';
            var td = t.querySelector('tbody td.ws-tt-num');
            var tdEmp = t.querySelector('tbody td.ws-tt-emp');
            var tr = t.querySelector('tbody tr');
            return {
                cellBg: getComputedStyle(td).backgroundColor,
                cellBB: getComputedStyle(td).borderBottomColor,
                cellBR: getComputedStyle(td).borderRightColor,
                empBg: getComputedStyle(tdEmp).backgroundColor,
                empBB: getComputedStyle(tdEmp).borderBottomColor,
                rowH: tr.getBoundingClientRect().height,
                zeroTexts: Array.prototype.map.call(t.querySelectorAll('tbody td.ws-tt-num'), function(c){return c.textContent.trim();}).slice(0, 20)
            };
        })()""")
        print(theme, 'totals info:', json.dumps(info, ensure_ascii=False)[:600])
        ctx.close()
    browser.close()
print('DONE')
