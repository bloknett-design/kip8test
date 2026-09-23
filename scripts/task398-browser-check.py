#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 398: browser-check — заявка «Почему в роли КИП ИОС видна
# кнопка "Работники" в разделе Табель учёта рабочего времени, хотя
# доступа и перехода по ней нет?»
# ПРИЧИНА (воспроизведена зондом task398-diagnose*.py): CSS
# .ws-refresh-btn{display:inline-flex} перебивал UA-стиль
# [hidden]{display:none} — JS-гейт Task 395 ставил hidden=true,
# а кнопка оставалась на экране (107×30) и кликалась впустую.
# ФИКС: [hidden]{display:none!important} в начале <style>.
# МОК: 2 работника (сетка + карточки).
# КОНТЕКСТЫ (матрица getMyAccess):
#   1) десктоп 1280 тёмная, КИП ИОС + workschedule.view.min:
#      кнопка СКРЫТА (hidden=true И rect 0×0 — визуально!),
#      ряд 1 не пострадал (Обновить/Печать/Вид/Обозначения видны),
#      DOM-скан: 0 протечек [hidden] на странице табеля;
#   2) десктоп 1280 тёмная, КИП ИОС + workschedule.view:
#      кнопка ВИДНА, КЛИК → переход на страницу «Работники»
#      работает (страница активна, ярлыки вкладок есть);
#   3) десктоп 1280 тёмная, Админ (edit): кнопка видна, переход
#      работает, «Сформировать» видна (санити регресса);
#   4) мобильный 375 светлая, КИП ИОС + min: кнопка скрыта
#      (rect 0×0), клик по её месту НЕ открывает страницу.
# Порт 9006 (запуск: python3 -m http.server 9006 &).
import calendar
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9006
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

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag, perms, role):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

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
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t398-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

BASE_PERMS = {'calc.view': True, 'library.view': True, 'kipios.view': True,
              'secret.view': True, 'whatsnew.view': True}
MIN_PERMS = dict(BASE_PERMS, **{'workschedule.view.min': True})
VIEW_PERMS = dict(BASE_PERMS, **{'workschedule.view': True})
EDIT_PERMS = dict(BASE_PERMS, **{'workschedule.view': True,
                                 'workschedule.edit': True})

def btn_state(page, btn_id):
    return page.evaluate(
        "(function(){var b=document.getElementById(%r);if(!b)return{exists:false};"
        "var r=b.getBoundingClientRect();"
        "return {exists:true,hiddenAttr:b.hidden,w:r.width,h:r.height,"
        "visible:r.width>1&&r.height>1};})()" % btn_id)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, КИП ИОС + min ==========
    print('=== Контекст 1: КИП ИОС, workschedule.view.min (сценарий заявки) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'min', MIN_PERMS, 'КИП ИОС')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    entry = page.evaluate("var b=document.getElementById('workScheduleMenuBtn');b?getComputedStyle(b).display:null")
    check('B: вход в раздел табеля доступен (min даёт раздел)', entry == 'flex', entry)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    check('C: табель открыт, сетка отрисована (2 работника)',
          page.evaluate("!!document.querySelector('#page-work-schedule.active') && "
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length === 2"))
    w = btn_state(page, 'wsWorkersBtn')
    check('D1: кнопка «Работники» hidden=true (гейт Task 395 жив)',
          w['exists'] and w['hiddenAttr'] is True, w)
    check('D2: кнопка «Работники» ВИЗУАЛЬНО скрыта — rect 0×0 (фикс Task 398!)',
          w['exists'] and not w['visible'], w)
    click_res = page.evaluate("""(function(){
        var b = document.getElementById('wsWorkersBtn');
        var r = b.getBoundingClientRect();
        // клик в центр БЫВШЕГО места кнопки (ряд 1 тулбара)
        var x = r.left + (r.width > 0 ? r.width / 2 : 60);
        var y = r.top + (r.height > 0 ? r.height / 2 : 15);
        var hit = document.elementFromPoint(x, y);
        return {hitIsBtn: hit === b, hitTag: hit ? hit.tagName + '#' + (hit.id || '') +
                '.' + String(hit.className || '').split(' ')[0] : null};
    })()""")
    check('D3: клик по месту кнопки в неё НЕ попадает (нет «мёртвой» зоны)',
          not click_res['hitIsBtn'], click_res)
    page.evaluate("WorkSchedule.openWorkersPage()")
    page.wait_for_timeout(600)
    check('D4: программный вызов openWorkersPage НЕ ведёт на страницу (min)',
          not page.evaluate("var pg=document.getElementById('page-ws-workers');!!(pg&&pg.classList.contains('active'))"))
    others = {bid: btn_state(page, bid) for bid in
              ['wsRefreshBtn', 'wsPrintBtn', 'wsViewBtn', 'wsLegendBtn']}
    check('E1: «Обновить» видна (мин не задет фиксом)', others['wsRefreshBtn']['visible'])
    check('E2: «Печать» видна (фича просмотра для min)', others['wsPrintBtn']['visible'])
    check('E3: «Вид» видна (фича просмотра для min)', others['wsViewBtn']['visible'])
    check('E4: «Обозначения» видна', others['wsLegendBtn']['visible'])
    leaks = page.evaluate("""(function(){
        var out = [];
        var all = document.querySelectorAll('#page-work-schedule [hidden]');
        for (var i = 0; i < all.length; i++) {
            var r = all[i].getBoundingClientRect();
            if (r.width > 1 && r.height > 1) out.push(all[i].id || all[i].tagName);
        }
        return out;
    })()""")
    check('F: DOM-скан табеля: 0 визуально-протекающих [hidden]-элементов',
          leaks == [], leaks)
    page.screenshot(path='task398-proof-min.png', full_page=False)
    check('G: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, КИП ИОС + view ==========
    print('=== Контекст 2: КИП ИОС, workschedule.view (кнопка должна работать) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'view', VIEW_PERMS, 'КИП ИОС')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    w = btn_state(page, 'wsWorkersBtn')
    check('H1: кнопка «Работники» ВИДИМА уровню view (rect > 0)',
          w['exists'] and not w['hiddenAttr'] and w['visible'], w)
    page.screenshot(path='task398-proof-view-toolbar.png', full_page=False)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1200)
    wp = page.evaluate("""(function(){
        var pg = document.getElementById('page-ws-workers');
        return {active: !!(pg && pg.classList.contains('active')),
                tabs: document.querySelectorAll('#wsWorkersBody .ws-wtab').length};
    })()""")
    check('H2: КЛИК → переход на страницу «Работники» (страница активна)',
          wp['active'])
    check('H3: страница отрисована — ярлыки вкладок (Общая + 2 работника)',
          wp['tabs'] >= 3, wp)
    check('H4: у view НЕТ «Правка данных…» (карточки read-only — Task 395)',
          page.evaluate("var b=document.getElementById('wsWorkersBody');"
                        "!b || b.textContent.indexOf('Правка данных') === -1"))
    page.screenshot(path='task398-proof-view.png', full_page=False)
    check('H5: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: десктоп 1280, Админ (edit) ==========
    print('=== Контекст 3: Админ, workschedule.edit (санити регресса) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'edit', EDIT_PERMS, 'Админ')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    w = btn_state(page, 'wsWorkersBtn')
    g = btn_state(page, 'wsGenerateBtn')
    check('I1: кнопка «Работники» видна (edit)', w['exists'] and w['visible'], w)
    check('I2: «Сформировать» видна (edit) — фикс не сломал', g['exists'] and g['visible'], g)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1200)
    check('I3: переход на «Работники» работает',
          page.evaluate("var pg=document.getElementById('page-ws-workers');!!(pg&&pg.classList.contains('active'))"))
    # «Правка данных…» живёт в КАРТОЧКЕ работника (Task 396: кнопка в
    # шапке блока профиля) — сначала ярлык вкладки работника
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(900)
    check('I4: у edit в карточке работника ЕСТЬ «Правка данных…»',
          page.evaluate("var b=document.getElementById('wsWorkersBody');"
                        "!!b && b.textContent.indexOf('Правка данных') !== -1"))
    check('I5: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 4: мобильный 375, светлая, КИП ИОС + min ==========
    print('=== Контекст 4: мобильный 375, светлая, КИП ИОС + min ===')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mob-min', MIN_PERMS, 'КИП ИОС')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    w = btn_state(page, 'wsWorkersBtn')
    check('J1: мобильный min: кнопка «Работники» скрыта (rect 0×0)',
          w['exists'] and w['hiddenAttr'] and not w['visible'], w)
    # клик по бывшему месту кнопки (ряд 1) не должен ничего открывать
    page.evaluate("""(function(){
        var b = document.getElementById('wsWorkersBtn');
        var r = b.getBoundingClientRect();
        var x = r.left + 60, y = r.top + 15;
        var hit = document.elementFromPoint(x, y);
        if (hit && hit.click) hit.click();
    })()""")
    page.wait_for_timeout(700)
    check('J2: клик по месту кнопки НЕ открывает «Работники»',
          not page.evaluate("var pg=document.getElementById('page-ws-workers');!!(pg&&pg.classList.contains('active'))"))
    leaks = page.evaluate("(function(){var o=[];var a=document.querySelectorAll('#page-work-schedule [hidden]');for(var i=0;i<a.length;i++){var r=a[i].getBoundingClientRect();if(r.width>1&&r.height>1)o.push(a[i].id||a[i].tagName);}return o;})()")
    check('J3: мобильный DOM-скан: 0 протечек [hidden]', leaks == [], leaks)
    page.screenshot(path='task398-proof-mobile.png', full_page=False)
    check('J4: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print('\n════════════════════════════════════════')
print('Task 398 browser-check: %d passed, %d failed' % (PASS, FAIL))
print('════════════════════════════════════════')
raise SystemExit(1 if FAIL else 0)
