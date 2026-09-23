#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 395: browser-check — заявка (3 части):
#   (1) кнопка «Работники» НЕ отображается пользователям БЕЗ
#       доступа к разделу (null) и с ОГРАНИЧЕННЫМ просмотром (min)
#       по матрице; edit/view — видна (у view — read-only);
#   (2) фон блоков карточек НЕ сливается с общим фоном окна +
#       рамки ТОЛЩЕ (2px) и ЯРЧЕ, «выступающий вверх бордюрчик»
#       (светлая верхняя кромка + тень снизу);
#   (3) десктоп: ОТПУСКА — ПОД профилем, МЕРОПРИЯТИЯ — ПОД
#       отпусками (левая колонка .ws-wcol), СИЗ — ВЕРХНЯЯ ПРАВАЯ
#       часть экрана (правая колонка .ws-wcol-ppe).
# МОК: 6 работников (как Task 394), Иванову: отпуск + 3
# мероприятия года + 3 СИЗ.
# КОНТЕКСТЫ (матрица getMyAccess — permissions):
#   1) десктоп 1280 тёмная, edit (view+edit): раскладка + стили;
#   2) десктоп 1280 тёмная, view: кнопка ВИДНА, страница
#      read-only (без «Правка данных…»/«Уволить…»/«+ …»);
#   3) десктоп 1280 тёмная, min: кнопка СКРЫТА, прямой URL —
#      тело пустое;
#   4) десктоп 1280 тёмная, null (нет workschedule.*): кнопка
#      СКРЫТА, раздел табеля скрыт;
#   5) мобильный 375 светлая, edit: стек в колонку + стили
#      светлой темы.
# Порт 9006 (запуск: python3 -m http.server 9006 &).
import calendar
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 9006
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]

def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': 'бригада А'},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
  {'таб_номер': '045', 'ФИО': 'Сидорова А. А.', 'тип': 'сменный', 'смена': 2,
   'шаблон_ротации': 1, 'старт_цикла': d(2),
   'дата_приёма': '2023-06-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электрик КИПиА', 'комментарий': ''},
  {'таб_номер': '100', 'ФИО': 'Кузнецов К. К.', 'тип': 'сменный', 'смена': '',
   'шаблон_ротации': 1, 'старт_цикла': d(3),
   'дата_приёма': '2022-04-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'комментарий': ''},
  {'таб_номер': '101', 'ФИО': 'Васильев В. В.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(1),
   'дата_приёма': '2021-09-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА см.1', 'комментарий': ''},
  {'таб_номер': '102', 'ФИО': 'Николаева Н. Н.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(4),
   'дата_приёма': '2024-11-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
CODES = [
  {'code': 'Д8',   'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Д',    'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день 12ч'},
  {'code': 'Н',    'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'ОТ',   'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': 'И',    'name': 'Инструктаж', 'color': '#B3E5FC', 'short': 'инструктаж'},
  {'code': 'ОБ',   'name': 'Обучение', 'color': '#D1C4E9', 'short': 'обучение'},
  {'code': '',     'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
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
PPE_STATE = [
  {'id': 1, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА',
   'наименование': 'Костюм для защиты от растворов кислот и щелочей',
   'дата_выдачи': '%d-%02d-12' % (Y - 1, M), 'срок_годности': '1 год',
   'дата_окончания': d(12), 'примечание': ''},
  {'id': 2, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'срок_годности': 'До износа',
   'дата_окончания': 'До износа', 'примечание': ''},
  {'id': 3, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Ботинки',
   'дата_выдачи': '%d-%02d-05' % (Y - 2, M), 'срок_годности': '2 года',
   'дата_окончания': d(20), 'примечание': ''},
]
VACATIONS = [
  {'id': 11, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(10), 'дата_окончания': d(20), 'комментарий': ''},
]
TRAININGS = [
  {'id': 31, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Охрана труда',
   'дата_начала': d(5), 'дата_окончания': d(5)},
  {'id': 32, 'таб_номер': '017', 'тип': 'обучение', 'тема': 'Пожарная безопасность',
   'дата_начала': '%d-03-10' % Y, 'дата_окончания': '%d-03-10' % Y},
  {'id': 33, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Первая помощь',
   'дата_начала': '%d-06-15' % Y, 'дата_окончания': '%d-06-15' % Y},
]

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag, perms, role='Админ'):
    """perms — словарь прав матрицы (getMyAccess); role — имя роли
    (для null-контекста — БЕЗ '*' в легаси-карте, чтобы серверная
    матрица пересобирала список страниц: Админа _applyServerAccess
    не трогает — «Админ ('*') не трогаем»)."""
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
                body=json.dumps({'ok': True, 'data': {'trainings': TRAININGS}}, ensure_ascii=False))
        if action == 'workSchedule.listVacations':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'vacations': VACATIONS}}, ensure_ascii=False))
        if action == 'workSchedule.listPpe':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ppe': PPE_STATE}}, ensure_ascii=False))
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
                      body='not found (t395-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t395-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

EDIT_PERMS = {'workschedule.view': True, 'workschedule.edit': True}
VIEW_PERMS = {'workschedule.view': True}
MIN_PERMS = {'workschedule.view.min': True}
NULL_PERMS = {'calc.view': True}

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit ==========
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'admin', EDIT_PERMS)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B0: табель открыт, сетка отрисована (6 работников)',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length === 6"))
    check('B1: кнопка «Работники» ВИДНА (edit)',
          page.evaluate("var b=document.getElementById('wsWorkersBtn'); !!b && !b.hidden"))

    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    e = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var grid = body ? body.querySelector('.ws-wgrid2') : null;
        var colL = grid ? grid.querySelector(':scope > .ws-wcol:not(.ws-wcol-ppe)') : null;
        var colR = grid ? grid.querySelector(':scope > .ws-wcol-ppe') : null;
        var cardsL = colL ? colL.querySelectorAll(':scope > .ws-wcard') : [];
        var cardR = colR ? colR.querySelectorAll(':scope > .ws-wcard') : [];
        var cs = grid ? getComputedStyle(grid) : null;
        var rect = function(el) {
            var r = el.getBoundingClientRect();
            return {left: r.left, top: r.top, right: r.right,
                    width: r.width, height: r.height};
        };
        var st = cardR.length ? getComputedStyle(cardR[0]) : null;
        var pageBg = getComputedStyle(document.body).backgroundColor;
        return {
            cols: grid ? grid.querySelectorAll(':scope > .ws-wcol').length : 0,
            nL: cardsL.length, nR: cardR.length,
            display: cs ? cs.display : null, gap: cs ? cs.columnGap : null,
            align: cs ? cs.alignItems : null,
            rL: colL ? rect(colL) : null, rR: colR ? rect(colR) : null,
            c1: cardsL.length ? rect(cardsL[0]) : null,
            c2: cardsL.length > 1 ? rect(cardsL[1]) : null,
            c3: cardsL.length > 2 ? rect(cardsL[2]) : null,
            c4: cardR.length ? rect(cardR[0]) : null,
            txt1: cardsL.length ? (cardsL[0].textContent || '') : '',
            txt2: cardsL.length > 1 ? (cardsL[1].textContent || '') : '',
            txt3: cardsL.length > 2 ? (cardsL[2].textContent || '') : '',
            txt4: cardR.length ? (cardR[0].textContent || '') : '',
            bg: st ? st.backgroundColor : null,
            bw: st ? st.borderTopWidth : null,
            btop: st ? st.borderTopColor : null,
            bside: st ? st.borderLeftColor : null,
            shadow: st ? st.boxShadow : null,
            pageBg: pageBg
        };
    })()""")
    check('C1: ДВЕ колонки-обёртки .ws-wcol (лево 3 окна + право 1)',
          e['cols'] == 2 and e['nL'] == 3 and e['nR'] == 1,
          (e['cols'], e['nL'], e['nR']))
    check('C2: flex-раскладка, равные колонки, зазор 12px, правая НЕ тянется',
          e['display'] == 'flex' and e['align'] == 'flex-start' and
          e['gap'] == '12px' and
          abs(e['rL']['width'] - e['rR']['width']) < 4,
          (e['display'], e['align'], e['gap'], e['rL'], e['rR']))
    check('C3: ПРОФИЛЬ — верх левой колонки («Иванов И. И. · таб. №017»)',
          'Иванов И. И.' in e['txt1'] and 'таб. №017' in e['txt1'] and
          'Правка данных…' in e['txt1'], e['txt1'][:120])
    check('C4: ОТПУСКА — ПОД блоком профиля (левая колонка)',
          'Отпуска · %d' % Y in e['txt2'] and
          abs(e['c2']['left'] - e['c1']['left']) < 4 and
          e['c2']['top'] > e['c1']['top'] + 80,
          (e['c1'], e['c2']))
    check('C5: МЕРОПРИЯТИЯ — ПОД блоком отпуска (левая колонка)',
          'Мероприятия · %d' % Y in e['txt3'] and
          abs(e['c3']['left'] - e['c2']['left']) < 4 and
          e['c3']['top'] > e['c2']['top'] + 50,
          (e['c2'], e['c3']))
    check('C6: СИЗ — ВЕРХНЯЯ ПРАВАЯ часть экрана (правая колонка, верх)',
          'СИЗ · средства индивидуальной защиты' in e['txt4'] and
          'Костюм для защиты' in e['txt4'] and
          e['c4']['left'] > e['c1']['left'] + 100 and
          abs(e['c4']['top'] - e['c1']['top']) < 40,
          (e['c1'], e['c4']))
    # стили панелей: фон НЕ сливается с фоном окна
    check('D1: тёмная — фон панелей #243349 ≠ фон окна #1a2233',
          e['bg'] == 'rgb(36, 51, 73)' and e['pageBg'] != e['bg'],
          (e['bg'], e['pageBg']))
    check('D2: рамка ТОЛЩЕ — 2px',
          e['bw'] == '2px', e['bw'])
    def rgba(v):
        try:
            parts = v.replace('rgba(', '').replace('rgb(', '').rstrip(')').split(',')
            return [float(x.strip()) for x in parts]
        except Exception:
            return []
    btop, bside = rgba(e['btop'] or ''), rgba(e['bside'] or '')
    check('D3: «выступающий бордюрчик» — верхняя кромка ЯРЧЕ боков',
          len(btop) == 4 and len(bside) == 4 and btop[0] > bside[0] and
          btop[2] > bside[2],
          (e['btop'], e['bside']))
    check('D4: тень снизу — окно «приподнято»',
          '0px 3px' in (e['shadow'] or ''), e['shadow'])
    page.screenshot(path='task395-proof-workers-dark.png', full_page=False)

    # «Общая» — не задета (панель .ws-wgen без сетки)
    page.click('button.ws-wtab-general')
    page.wait_for_timeout(500)
    f = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        return {grid: !!body.querySelector('.ws-wgrid2'),
                gen: !!body.querySelector('.ws-wgen'),
                add: !!document.getElementById('wsWorkersAddBtn')};
    })()""")
    check('E1: «Общая» — панель .ws-wgen БЕЗ колонок, кнопка «Добавить» жива',
          not f['grid'] and f['gen'] and f['add'], f)
    check('F: 0 JS-ошибок (edit)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, тёмная, view ==========
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'dark', 'viewer', VIEW_PERMS)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    check('G1: view — кнопка «Работники» ВИДНА',
          page2.evaluate("var b=document.getElementById('wsWorkersBtn'); !!b && !b.hidden"))
    page2.click('#wsWorkersBtn')
    page2.wait_for_timeout(1000)
    check('G2: view — страница «Работники» ОТКРЫТА (вкладки)',
          page2.evaluate("!!document.querySelector('#wsWorkersBody .ws-workers-layout')"))
    page2.click('button[title="Иванов И. И."]')
    page2.wait_for_timeout(800)
    g = page2.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var txt = body ? (body.textContent || '') : '';
        return {txt: txt,
                noedit: txt.indexOf('Правка данных…') === -1,
                nodismiss: txt.indexOf('Уволить…') === -1,
                noaddvac: txt.indexOf('+ Отпуск…') === -1,
                noaddtr: txt.indexOf('+ Мероприятие…') === -1,
                noaddppe: txt.indexOf('+ СИЗ…') === -1};
    })()""")
    check('G3: view — карточка read-only (данные есть, правки НЕТ)',
          'Иванов И. И.' in g['txt'] and g['noedit'] and g['nodismiss'] and
          g['noaddvac'] and g['noaddtr'] and g['noaddppe'],
          (g['noedit'], g['nodismiss'], g['noaddvac'], g['noaddtr'], g['noaddppe']))
    page2.screenshot(path='task395-proof-workers-view.png', full_page=False)
    page2.click('button.ws-wtab-general')
    page2.wait_for_timeout(500)
    check('G4: view — «Общая» БЕЗ кнопки «Добавить работника»',
          page2.evaluate("!document.getElementById('wsWorkersAddBtn')"))
    check('G5: 0 JS-ошибок (view)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ========== Контекст 3: десктоп 1280, тёмная, min ==========
    ctx3 = browser.new_context(viewport={'width': 1280, 'height': 900})
    page3 = ctx3.new_page()
    js_errors3 = attach(page3, ctx3, 'dark', 'min', MIN_PERMS)

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    check('H1: min — табель открыт (сетка есть)',
          page3.evaluate("!!document.querySelector('#page-work-schedule .ws-grid')"))
    check('H2: min — кнопка «Работники» СКРЫТА',
          page3.evaluate("var b=document.getElementById('wsWorkersBtn'); !b || b.hidden"))
    page3.evaluate("navigateTo('ws-workers')")
    page3.wait_for_timeout(800)
    h = page3.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        return {txt: body ? (body.textContent || '').trim() : '(нет)',
                html: body ? (body.innerHTML || '').trim() : '(нет)'};
    })()""")
    check('H3: min — прямой URL: тело страницы ПУСТОЕ',
          h['html'] == '', h['txt'][:120])
    check('H4: 0 JS-ошибок (min)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ========== Контекст 4: десктоп 1280, тёмная, null ==========
    ctx4 = browser.new_context(viewport={'width': 1280, 'height': 900})
    page4 = ctx4.new_page()
    # роль БЕЗ '*' — «КИП8»: только так серверная матрица снимает
    # разделы (Админа _applyServerAccess не трогает)
    js_errors4 = attach(page4, ctx4, 'dark', 'norights', NULL_PERMS, role='КИП8')

    page4.goto('http://localhost:%d/index.html' % PORT)
    page4.wait_for_timeout(2500)
    # ждём серверную матрицу (getMyAccess): до её прихода navigateTo
    # ходит по легаси-карте (Админ — все разделы) и пустил бы в табель
    try:
        page4.wait_for_function(
            "function(){ try { return !!(KipAuth._serverAccess && " +
            "KipAuth._serverAccess.found); } catch (e) { return false; } }",
            timeout=9000)
    except Exception:
        pass
    page4.evaluate("navigateTo('work-schedule')")
    page4.wait_for_timeout(1500)
    i = page4.evaluate("""(function(){
        var b = document.getElementById('wsWorkersBtn');
        var noacc = !!document.getElementById('noAccessScreen');
        var vis = noacc ? (getComputedStyle(document.getElementById('noAccessScreen')).display !== 'none') : false;
        return {btn: !b || b.hidden, noaccess: vis};
    })()""")
    check('I1: null (нет доступа к разделу) — кнопка «Работники» СКРЫТА',
          i['btn'])
    check('I2: null — экран «нет доступа» к разделу табеля',
          i['noaccess'])
    check('I3: 0 JS-ошибок (null)', len(js_errors4) == 0, js_errors4[:3])
    ctx4.close()

    # ========== Контекст 5: мобильный 375, светлая, edit ==========
    ctx5 = browser.new_context(viewport={'width': 375, 'height': 720})
    page5 = ctx5.new_page()
    js_errors5 = attach(page5, ctx5, 'light', 'mob', EDIT_PERMS)

    page5.goto('http://localhost:%d/index.html' % PORT)
    page5.wait_for_timeout(2500)
    page5.evaluate("navigateTo('work-schedule')")
    page5.wait_for_timeout(3000)
    page5.click('#wsWorkersBtn')
    page5.wait_for_timeout(1000)
    page5.click('button[title="Иванов И. И."]')
    page5.wait_for_timeout(800)
    m = page5.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var grid = body ? body.querySelector('.ws-wgrid2') : null;
        var colL = grid ? grid.querySelector(':scope > .ws-wcol:not(.ws-wcol-ppe)') : null;
        var colR = grid ? grid.querySelector(':scope > .ws-wcol-ppe') : null;
        var cards = grid ? grid.querySelectorAll('.ws-wcard') : [];
        var cs = grid ? getComputedStyle(grid) : null;
        var tops = [], lefts = [], fit = true, vw = window.innerWidth;
        for (var i = 0; i < cards.length; i++) {
            var r = cards[i].getBoundingClientRect();
            tops.push(r.top); lefts.push(r.left);
            if (r.right > vw + 1 || r.left < -1) fit = false;
        }
        var st = cards.length ? getComputedStyle(cards[0]) : null;
        return {n: cards.length, display: cs ? cs.display : null,
                stack: tops.length === 4 && tops[0] < tops[1] && tops[1] < tops[2] && tops[2] < tops[3],
                sameLeft: lefts.length === 4 && Math.abs(lefts[0] - lefts[1]) < 4 && Math.abs(lefts[1] - lefts[2]) < 4,
                fit: fit,
                bg: st ? st.backgroundColor : null,
                btop: st ? st.borderTopColor : null,
                bside: st ? st.borderLeftColor : null,
                pageBg: getComputedStyle(document.body).backgroundColor};
    })()""")
    check('J1: мобильный — СТЕК в колонку (4 окна друг под другом)',
          m['n'] == 4 and m['display'] == 'block' and m['stack'] and
          m['sameLeft'] and m['fit'],
          (m['n'], m['display'], m['stack'], m['sameLeft'], m['fit']))
    check('J2: светлая — фон панелей БЕЛЫЙ ≠ кремовый фон окна',
          m['bg'] == 'rgb(255, 255, 255)' and m['pageBg'] != m['bg'],
          (m['bg'], m['pageBg']))
    def rgba2(v):
        try:
            parts = v.replace('rgba(', '').replace('rgb(', '').rstrip(')').split(',')
            return [float(x.strip()) for x in parts]
        except Exception:
            return []
    btop2, bside2 = rgba2(m['btop'] or ''), rgba2(m['bside'] or '')
    check('J3: светлая — верхняя кромка СВЕТЛЕЕ боков (блик)',
          len(btop2) == 4 and len(bside2) == 4 and btop2[0] > bside2[0] and
          btop2[1] > bside2[1],
          (m['btop'], m['bside']))
    page5.screenshot(path='task395-proof-mobile-light.png', full_page=False)
    check('J4: 0 JS-ошибок (мобильный)', len(js_errors5) == 0, js_errors5[:3])
    ctx5.close()

    browser.close()

print('=' * 60)
print('Task 395 browser-check: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
