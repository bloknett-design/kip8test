#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 398 ДИАГНОСТИКА-2: полный аудит скрытия кнопок тулбара Табеля —
# атрибут hidden против ФАКТИЧЕСКОЙ видимости (rect + computed display),
# роли КИП ИОС (min) и зритель (view); пруф-скриншоты.
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

def attach(page, ctx, tag, perms, role='КИП ИОС'):
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
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': role, 'found': True,
                        'permissions': perms}}, ensure_ascii=False))
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
                      body='not found (t398b-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.clear()}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t398b-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','dark');")
    return js_errors

BTN_IDS = ['wsRefreshBtn', 'wsPrintBtn', 'wsWorkersBtn', 'wsViewBtn',
           'wsTotalsBtn', 'wsCrossBtn', 'wsGenerateBtn', 'wsSaveBtn',
           'wsCancelBtn', 'wsTtTabMonth', 'wsTtTabYear', 'wsLegendBtn']

with sync_playwright() as p:
    browser = p.chromium.launch()
    for tag, perms in [('min', dict(BASE_PERMS, **{'workschedule.view.min': True})),
                       ('view', dict(BASE_PERMS, **{'workschedule.view': True}))]:
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        attach(page, ctx, tag, perms)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)
        print('\n=== уровень %s (КИП ИОС) ===' % tag)
        rows = page.evaluate("""(function(){
            var out = [];
            var ids = %s;
            for (var i = 0; i < ids.length; i++) {
                var b = document.getElementById(ids[i]);
                if (!b) continue;
                var r = b.getBoundingClientRect();
                var st = getComputedStyle(b);
                out.push({id: ids[i], txt: (b.textContent || '').trim().slice(0, 18),
                          hiddenAttr: b.hidden, disp: st.display,
                          w: Math.round(r.width), h: Math.round(r.height),
                          visibleRect: r.width > 1 && r.height > 1});
            }
            return out;
        })()""" % json.dumps(BTN_IDS))
        bad = 0
        for r in rows:
            flag = ''
            if r['hiddenAttr'] and r['visibleRect']:
                flag = '  ← БАГ: hidden=true, но ВИДИМА (%sx%s, display=%s)' % (r['w'], r['h'], r['disp'])
                bad += 1
            print('  %-14s %-18s hidden=%-5s rect=%sx%-3s%s' %
                  (r['id'], r['txt'][:18], r['hiddenAttr'], r['w'], r['h'], flag))
        print('  ИТОГО визуально-протекающих кнопок: %d' % bad)
        page.screenshot(path='task398-diag-%s.png' % tag, full_page=False)
        ctx.close()
    browser.close()
print('\nГОТОВО')
