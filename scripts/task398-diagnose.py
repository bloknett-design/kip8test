#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 398 ДИАГНОСТИКА (зонд, не финальный тест): почему роли «КИП ИОС»
# видна кнопка «Работники» в разделе Табель, хотя доступа/перехода нет.
# Контексты (матрица getMyAccess для роли КИП ИОС):
#   1) found=true, workschedule.view.min=true   (ограниченный просмотр)
#   2) found=true, workschedule.view=true       (просмотр)
#   3) found=true, НЕТ workschedule.*           (нет доступа к разделу)
#   4) found=false                              (роли нет в матрице)
#   5) getMyAccess НЕ ОТВЕЧАЕТ (сеть/старый сервер) — легаси-карта
#   6) матрица ПРИХОДИТ ПОЗЖЕ навигации (гонка, без кэша)
#   7) СТАРЫЙ кэш kip8_my_access (view=true), живая матрица = min
# Для каждого: вход в раздел, видимость wsWorkersBtn, клик → результат.
import calendar
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9019
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
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
BASE_PERMS = {'calc.view': True, 'library.view': True, 'kipios.view': True,
              'secret.view': True, 'whatsnew.view': True}
MIN_PERMS = dict(BASE_PERMS, **{'workschedule.view.min': True})
VIEW_PERMS = dict(BASE_PERMS, **{'workschedule.view': True})
NO_PERMS = dict(BASE_PERMS)

def attach(page, ctx, tag, perms=None, found=True, role='КИП ИОС',
           delay_ms=0, fail_access=False, stale_cache=None):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': role}}, ensure_ascii=False))
        if action == 'getMyAccess':
            if fail_access:
                return route.fulfill(status=500, content_type='text/plain', body='boom')
            body = json.dumps({'ok': True, 'data': {'role': role, 'found': found,
                    'permissions': (perms if perms is not None else {})}}, ensure_ascii=False)
            if delay_ms:
                import time as _t
                _t.sleep(delay_ms / 1000.0)
            return route.fulfill(status=200, content_type='application/json; charset=utf-8', body=body)
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}))
        if action == 'workSchedule.getStatusCodes':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'codes': CODES}}, ensure_ascii=False))
        if action == 'workSchedule.listEmployees':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'employees': EMPLOYEES}}, ensure_ascii=False))
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
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'entries': []}}, ensure_ascii=False))
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
                      body='not found (t398-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    init = ("try{localStorage.clear()}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t398-%s');" % tag +
            "localStorage.setItem('kip8test:app-theme','dark');")
    if stale_cache is not None:
        init += ("localStorage.setItem('kip8_my_access', %s);"
                 % json.dumps(json.dumps(stale_cache)))
    ctx.add_init_script(init)
    return js_errors

def probe_state(p, name, **kw):
    print('\n=== %s ===' % name)
    ctx = p.chromium.launch().new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, name.replace(' ', '-').replace('(', '').replace(')', ''), **kw)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    entry = page.evaluate("""(function(){
        var b = document.getElementById('workScheduleMenuBtn');
        return {exists: !!b, display: b ? getComputedStyle(b).display : null};
    })()""")
    print('  вход в раздел (docs-ios кнопка): display=%s' % entry['display'])
    # пытаемся зайти в раздел напрямую (как пользователь по кнопке/URL)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1200)
    in_section = page.evaluate("(function(){var pg=document.getElementById('page-work-schedule');return pg && pg.classList.contains('active');})()")
    btn = page.evaluate("""(function(){
        var b = document.getElementById('wsWorkersBtn');
        if (!b) return {exists: false};
        var r = b.getBoundingClientRect();
        return {exists: true, hidden: b.hidden, display: getComputedStyle(b).display,
                w: r.width, h: r.height,
                level: (typeof WorkSchedule !== 'undefined') ? String(WorkSchedule._viewLevel) : 'WS?',
                canEdit: (typeof WorkSchedule !== 'undefined') ? !!WorkSchedule._canEdit : null,
                canAccessWs: (typeof KipAuth !== 'undefined') ? KipAuth.canAccess('ws-workers') : null};
    })()""")
    print('  в разделе: %s; кнопка «Работники»: hidden=%s display=%s %sx%s' %
          (in_section, btn.get('hidden'), btn.get('display'), btn.get('w'), btn.get('h')))
    print('  WorkSchedule._viewLevel=%s _canEdit=%s canAccess(ws-workers)=%s' %
          (btn.get('level'), btn.get('canEdit'), btn.get('canAccessWs')))
    if in_section and btn.get('exists'):
        page.evaluate("document.getElementById('wsWorkersBtn').scrollIntoView({block:'center'})")
        try:
            page.click('#wsWorkersBtn', timeout=1500)
        except Exception as e:
            print('  клик не удался: %s' % str(e).split('\n')[0][:100])
        page.wait_for_timeout(900)
        res = page.evaluate("""(function(){
            var pg = document.getElementById('page-ws-workers');
            var na = document.getElementById('noAccessScreen');
            return {workersActive: !!(pg && pg.classList.contains('active')),
                    noAccess: !!(na && na.style.display && na.style.display !== 'none')};
        })()""")
        print('  после клика: страница Работники активна=%s, экран «Нет доступа»=%s' %
              (res['workersActive'], res['noAccess']))
    if js_errors:
        print('  JS-ошибки: %s' % js_errors[:3])
    ctx.close()

with sync_playwright() as p:
    probe_state(p, '1. КИП ИОС + matrix min (workschedule.view.min=true)', perms=MIN_PERMS)
    probe_state(p, '2. КИП ИОС + matrix view (workschedule.view=true)', perms=VIEW_PERMS)
    probe_state(p, '3. КИП ИОС + matrix БЕЗ workschedule.*', perms=NO_PERMS)
    probe_state(p, '4. КИП ИОС + found=false (роли нет в матрице)', perms={}, found=False)
    probe_state(p, '5. КИП ИОС + getMyAccess 500 (легаси-карта)', fail_access=True)
    probe_state(p, '6. КИП ИОС + матрица приходит ПОЗЖЕ (гонка 3500мс)', perms=MIN_PERMS, delay_ms=3500)
    stale = {'role': 'КИП ИОС', 'found': True, 'permissions': dict(VIEW_PERMS)}
    probe_state(p, '7. КИП ИОС + старый кэш (view) + живая матрица min', perms=MIN_PERMS, stale_cache=stale)
print('\nЗОНД ЗАВЕРШЁН')
