#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 405: browser-check — заявка «В файле табель_КИП_ИОС
# необходимо таблицу инструктажи разделить на две таблицы. В текущей
# таблице оставить только информацию которая касается проведения
# инструктажей и проверки знаний, а остальные данные, обучение и
# примечание, нужно переместить в новую таблицу под названием
# "Мероприятия". Тоесть в личных картах работников блок мероприятия
# остаётся и в нём отображаются только данные из новой таблицы
# "Мероприятия", а данные из таблицы "Инструктажи" отображать в новом
# блоке под названием "Повторные инструктажи и периодическая проверка
# знаний" на текущий год».
# МОК: 5 активных работников (как Task 403/404); Иванов 017 —
# отпуск 20–26 текущего месяца, 2 СИЗ, 4 мероприятия СМЕШАННЫХ типов:
# инструктаж (10-е), обучение (18-е), проверка_знаний (12-е),
# примечание (22-е) — ровно 2 в «Мероприятия» и 2 в «Инструктажи».
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, view: попап ячейки Иванова — секции
#      «Мероприятия · год» (обучение+примечание) и «Повторные
#      инструктажи и периодическая проверка знаний · год»
#      (инструктаж+проверка знаний), БЕЗ СИЗ; окно мероприятий
#      тулбара живо; 0 JS-ошибок;
#   2) десктоп 1280 светлая, edit: страница «Работники» — ТРИ колонки,
#      колонка 3 — ДВА окна (Мероприятия + Повторные инструктажи);
#      кнопка «+ Мероприятие…» → шторка с типом «обучение» (префилл
#      Task 405); «+ Инструктаж…» → тип «инструктаж»; сводная
#      «Общая» — НОВАЯ колонка «Инструктажи · год» (2 у Иванова)
#      и «Мероприятия · год» (2); ✎/✕ в обоих блоках правой колонки;
#   3) мобайл 375 светлая, view: стек ПЯТЬ блоков — профиль →
#      отпуска → СИЗ → мероприятия → повторные инструктажи; 0 ошибок.
# Порт 8906 (запуск: python3 -m http.server 8906 &).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8906
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов И. И.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '', 'комментарий': ''},
  {'таб_номер': '031', 'ФИО': 'Сидоров С. С.', 'тип': 'сменный', 'смена': 3,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, M, 2),
   'дата_приёма': '2023-11-05', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр КИПиА 4 разряда', 'группа_допуска': 'III', 'комментарий': ''},
  {'таб_номер': '045', 'ФИО': 'Ахметзянов Равиль Галиевич', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2021-06-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'группа_допуска': 'II', 'комментарий': ''},
  {'таб_номер': '058', 'ФИО': 'Константинопольский Аркадий Николаевич', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, M, 7),
   'дата_приёма': '2022-04-11', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА 3 разряд', 'группа_допуска': 'III', 'комментарий': ''},
]
ENTRIES = [
  {'дата': d(Y, M, 3), 'таб_номер': '017', 'статус': 'Д'},
  {'дата': d(Y, M, 5), 'таб_номер': '023', 'статус': 'Д8'},
  {'дата': d(Y, M, 7), 'таб_номер': '031', 'статус': 'Н'},
]
# Task 405: СМЕШАННЫЕ типы — 2 «мероприятийных» (обучение/примечание)
# и 2 «инструктажных» (инструктаж/проверка_знаний); «Инструктаж»
# с заглавной — проверка толерантности нормализации типа
TRAININGS = [
  {'id': 1, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': 'Охрана труда', 'дата_начала': d(Y, M, 10), 'дата_окончания': d(Y, M, 10)},
  {'id': 2, 'таб_номер': '017', 'тип': 'обучение',
   'тема': 'Пожарная безопасность', 'дата_начала': d(Y, M, 18), 'дата_окончания': d(Y, M, 18)},
  {'id': 3, 'таб_номер': '017', 'тип': 'Проверка знаний',
   'тема': 'Экзамен', 'дата_начала': d(Y, M, 12), 'дата_окончания': d(Y, M, 12)},
  {'id': 4, 'таб_номер': '017', 'тип': 'примечание',
   'тема': 'Перенос по приказу', 'дата_начала': d(Y, M, 22), 'дата_окончания': d(Y, M, 22)},
]
VACATIONS = [
  {'id': 1, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(Y, M, 20), 'дата_окончания': d(Y, M, 26)},
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Костюм для защиты от растворов кислот и щелочей',
   'дата_выдачи': d(Y, 8, 17), 'срок_годности': '1 год',
   'дата_окончания': d(Y + 1, 8, 17), 'примечание': ''},
  {'id': 2, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(Y - 1, M, 22), 'срок_годности': '1 год',
   'дата_окончания': d(Y, M, 22), 'примечание': ''},
]
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день'},
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

API_CALLS = []
PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if ADMIN else 'КИП ИОС'}}
    if action == 'getMyAccess':
        if ADMIN:
            perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                     'workschedule.view': True, 'workschedule.edit': True}
            role = 'Админ'
        else:
            perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                     'workschedule.view': True, 'workschedule.edit': False,
                     'workschedule.view.min': False}
            role = 'КИП ИОС'
        return {'ok': True, 'data': {'role': role, 'found': True, 'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        inc = bool(body and body.get('includeArchived'))
        emps = EMPLOYEES if inc else [e for e in EMPLOYEES if not e['в_архиве']]
        return {'ok': True, 'data': {'employees': emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': list(TRAININGS)}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': list(VACATIONS)}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': list(PPE)}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': list(ENTRIES)}}
    if action == 'workSchedule.addTraining':
        API_CALLS.append(('addTraining', dict(body or {})))
        return {'ok': True, 'data': {'id': 100}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}

ADMIN = False

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
        resp = api_response(action, body)
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                              body=json.dumps(resp, ensure_ascii=False))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t405-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t405-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

CELLS_JS = """(function(){
    var wrap = document.getElementById('wsGridWrap');
    var cells = wrap.querySelectorAll('tbody td.ws-emp-col');
    var out = [];
    for (var i = 0; i < cells.length; i++) {
        var td = cells[i];
        var name = td.querySelector('.ws-emp-name');
        out.push({ fio: name ? name.textContent : null });
    }
    return out;
})()"""

CARD_COLS_JS = """(function(){
    var out = { cols: [], tops: [] };
    var cols = document.querySelectorAll('.ws-wgrid2 .ws-wcol');
    for (var ci = 0; ci < cols.length; ci++) {
        var cards = cols[ci].querySelectorAll('.ws-wcard');
        var heads = [];
        for (var hi = 0; hi < cards.length; hi++) {
            var t = cards[hi].querySelector('.ws-whead-t');
            heads.push(t ? t.textContent.trim() : '');
        }
        var c1 = cols[ci].querySelector('.ws-wcard');
        out.cols.push({ n: cards.length, heads: heads,
                        x: cols[ci].getBoundingClientRect().left,
                        w: cols[ci].getBoundingClientRect().width });
        out.tops.push(c1 ? c1.getBoundingClientRect().top : null);
    }
    return out;
})()"""

INSTR_BLOCK_JS = """(function(){
    // содержимое блоков правой колонки (colTr): мероприятия + инструктажи
    var col = document.querySelector('.ws-wgrid2 .ws-wcol-tr');
    if (!col) return null;
    var cards = col.querySelectorAll('.ws-wcard');
    var out = [];
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        var rows = cards[i].querySelectorAll('.ws-popup-event');
        var names = [];
        for (var r = 0; r < rows.length; r++) {
            var nm = rows[r].querySelector('.ws-popup-name');
            names.push(nm ? nm.textContent : '');
        }
        var btn = cards[i].querySelector('.ws-whead-a .ws-wbtn');
        out.push({ head: t ? t.textContent.trim() : '',
                   rows: names,
                   btn: btn ? btn.textContent.trim() : null,
                   btnCls: btn ? btn.className : null });
    }
    return out;
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, view ==========
    print('=== Контекст 1: десктоп тёмная — попап ячейки: разделение по типам ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'grid-dark')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    cells = page.evaluate(CELLS_JS)
    check('B0: сетка отрисована (5 работников)', len(cells) == 5, len(cells))
    # попап по клику на ячейку Иванова — разделение по типам
    page.click("td.ws-emp-col[data-tab='017']")
    page.wait_for_timeout(700)
    card = page.evaluate("(function(){var pp=document.getElementById('wsEmpPopup');" +
                         "return pp?pp.innerHTML:'';})()")
    check('C1: попап открылся (Иванов)', 'Иванов' in card)
    check('C2: секция «Мероприятия · %d» жива' % Y,
          ('Мероприятия · %d' % Y) in card)
    check('C3: НОВАЯ секция «Повторные инструктажи и периодическая проверка знаний · %d»' % Y,
          ('Повторные инструктажи и периодическая проверка знаний · %d' % Y) in card)
    # в «Мероприятиях» — только обучение/примечание
    iMer = card.find('Мероприятия · %d' % Y)
    iIns = card.find('Повторные инструктажи и периодическая проверка знаний')
    merPart = card[iMer:iIns] if (iMer != -1 and iIns > iMer) else card[iMer:]
    insPart = card[iIns:] if iIns != -1 else ''
    check('C4: «Мероприятия»: обучение (Пожарная безопасность)',
          'Пожарная безопасность' in merPart)
    check('C5: «Мероприятия»: примечание (Перенос по приказу)',
          'Перенос по приказу' in merPart)
    check('C6: «Мероприятия»: НЕТ инструктажа (Охрана труда)',
          'Охрана труда' not in merPart)
    check('C7: «Мероприятия»: НЕТ проверки знаний (Экзамен)',
          'Экзамен' not in merPart)
    check('C8: «Инструктажи»: инструктаж (Охрана труда)',
          'Охрана труда' in insPart)
    check('C9: «Инструктажи»: проверка знаний с ПРОБЕЛОМ (Экзамен)',
          'Экзамен' in insPart)
    check('C10: «Инструктажи»: НЕТ обучения (Пожарная безопасность)',
          'Пожарная безопасность' not in insPart)
    check('C11: «Инструктажи»: НЕТ примечания (Перенос по приказу)',
          'Перенос по приказу' not in insPart)
    check('C12: в попапе НЕТ секции СИЗ (регресс Task 403)',
          'СИЗ' not in card)
    page.screenshot(path='task405-proof-grid-dark.png', full_page=False)
    page.keyboard.press('Escape')
    page.wait_for_timeout(400)
    # окно мероприятий тулбара — живо (регресс)
    monthsNom = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    ev = page.evaluate("(function(){var e=document.getElementById('wsEventsPanel');" +
                       "return e?e.innerHTML:'';})()")
    check('D1: окно мероприятий живо (месяц)',
          ('Мероприятия · ' + monthsNom[M - 1] + ' ' + str(Y)) in ev, ev[:80])
    check('D2: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, edit ==========
    print('=== Контекст 2: десктоп светлая — карточка, префиллы типов, сводная ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'workers-light')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    # карточка Иванова: колонки
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    c2 = page.evaluate(CARD_COLS_JS)
    check('E1: ТРИ колонки', c2 and len(c2['cols']) == 3, c2 and len(c2['cols']))
    check('E2: колонка 1 — профиль + отпуска',
          c2 and len(c2['cols'][0]['heads']) == 2 and
          c2['cols'][0]['heads'][0].find('Иванов') != -1 and
          c2['cols'][0]['heads'][1].startswith('Отпуска ·'),
          c2 and c2['cols'][0]['heads'])
    check('E3: колонка 2 — СИЗ',
          c2 and len(c2['cols'][1]['heads']) == 1 and
          c2['cols'][1]['heads'][0].startswith('СИЗ ·'),
          c2 and c2['cols'][1]['heads'])
    check('E4: колонка 3 — ДВА окна: Мероприятия + Повторные инструктажи',
          c2 and len(c2['cols'][2]['heads']) == 2 and
          c2['cols'][2]['heads'][0].startswith('Мероприятия ·') and
          c2['cols'][2]['heads'][1].startswith('Повторные инструктажи'),
          c2 and c2['cols'][2]['heads'])
    check('E5: верхние блоки В ОДНУ ЛИНИЮ (tops, допуск 2px)',
          c2 and len(c2['tops']) == 3 and c2['tops'][0] is not None and
          abs(c2['tops'][0] - c2['tops'][1]) < 2 and
          abs(c2['tops'][1] - c2['tops'][2]) < 2, c2 and c2['tops'])
    # содержимое блоков правой колонки
    rc = page.evaluate(INSTR_BLOCK_JS)
    check('F1: блок «Мероприятия»: 2 записи (обучение+примечание)',
          rc and len(rc[0]['rows']) == 2, rc and rc[0]['rows'])
    check('F2: блок «Мероприятия»: кнопка «+ Мероприятие…»',
          rc and rc[0]['btn'] == '+ Мероприятие…', rc and rc[0]['btn'])
    check('F3: блок «Повторные инструктажи»: 2 записи (И+ПЗ)',
          rc and len(rc[1]['rows']) == 2, rc and rc[1]['rows'])
    check('F4: блок «Повторные инструктажи»: кнопка «+ Инструктаж…»',
          rc and rc[1]['btn'] == '+ Инструктаж…', rc and rc[1]['btn'])
    check('F5: кнопки блоков — классы ws-emp-addtr/addins',
          rc and 'ws-emp-addtr' in (rc[0]['btnCls'] or '') and
          'ws-emp-addins' in (rc[1]['btnCls'] or ''),
          rc and [rc[0]['btnCls'], rc[1]['btnCls']])
    # ✎/✕ в обоих блоках правой колонки
    acts = page.evaluate("""(function(){
        var col = document.querySelector('.ws-wgrid2 .ws-wcol-tr');
        var cards = col.querySelectorAll('.ws-wcard');
        var out = [];
        for (var i = 0; i < cards.length; i++) {
            out.push(cards[i].querySelectorAll('.ws-popup-act').length);
        }
        return out;
    })()""")
    check('F6: ✎/✕ в обоих блоках (по 2×записи = 4 на блок)',
          acts and acts[0] == 4 and acts[1] == 4, acts)
    page.screenshot(path='task405-proof-workers-light.png', full_page=False)
    # префилл типа: «+ Мероприятие…» → обучение
    page.click('.ws-wcol-tr .ws-wcard .ws-emp-addtr')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    tip1 = page.evaluate("document.getElementById('wsTrType').value")
    tab1 = page.evaluate("document.getElementById('wsTrTabNo').value")
    check('G1: «+ Мероприятие…» → тип по умолчанию «обучение»',
          tip1 == 'обучение', repr(tip1))
    check('G2: работник префиллом (017)', tab1 == '017', repr(tab1))
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(500)
    # префилл типа: «+ Инструктаж…» → инструктаж
    page.click('.ws-wcol-tr .ws-wcard .ws-emp-addins')
    page.wait_for_selector('#wsTrSheet.active', timeout=4000)
    page.wait_for_timeout(500)
    tip2 = page.evaluate("document.getElementById('wsTrType').value")
    check('G3: «+ Инструктаж…» → тип по умолчанию «инструктаж»',
          tip2 == 'инструктаж', repr(tip2))
    page.screenshot(path='task405-proof-instr-form.png', full_page=False)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)
    # сводная «Общая» — две колонки
    page.click(".ws-wtabs button:has-text('Общая')")
    page.wait_for_timeout(900)
    gen = page.evaluate("(function(){var t=document.querySelector('.ws-wgen-table');" +
                        "return t?t.innerHTML:'';})()")
    check('H1: сводная — колонка «Мероприятия · %d» жива' % Y,
          ('<th>Мероприятия · %d</th>' % Y) in gen)
    check('H2: сводная — НОВАЯ колонка «Инструктажи · %d»' % Y,
          ('<th>Инструктажи · %d</th>' % Y) in gen)
    check('H3: порядок: Мероприятия ЛЕВЕЕ Инструктажей',
          gen.find('<th>Мероприятия ·') < gen.find('<th>Инструктажи ·'))
    iIv = gen.find('Иванов И. И.')
    ivRow = gen[iIv:gen.find('</tr>', iIv)] if iIv != -1 else ''
    # пара последних ячеек строки = «мероприятия, инструктажи»
    check('H4: пара ячеек: <td>2</td><td>2</td> (мероприятия 2, инструктажи 2)',
          ivRow.rstrip().endswith('<td>2</td><td>2</td>'), ivRow[-60:])
    iPe = gen.find('Петров П. П.')
    peRow = gen[iPe:gen.find('</tr>', iPe)] if iPe != -1 else ''
    check('H6: Петров: прочерки в обеих колонках',
          peRow.rstrip().endswith('<td>—</td><td>—</td>'), peRow[-60:])
    check('I: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, view ==========
    print('=== Контекст 3: мобайл 375 светлая — стек ПЯТЬ блоков ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 375, 'height': 800})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    stack = page.evaluate("""(function(){
        var hs = document.querySelectorAll('.ws-wgrid2 .ws-whead-t');
        var out = [];
        for (var i = 0; i < hs.length; i++) out.push(hs[i].textContent.trim());
        return out;
    })()""")
    check('K1: мобайл — стек ПЯТЬ блоков: профиль → отпуска → СИЗ → '
          'мероприятия → повторные инструктажи',
          len(stack) == 5 and stack[0].find('Иванов') != -1 and
          stack[1].startswith('Отпуска') and stack[2].startswith('СИЗ') and
          stack[3].startswith('Мероприятия') and
          stack[4].startswith('Повторные инструктажи'), stack)
    page.screenshot(path='task405-proof-mobile.png', full_page=False)
    check('K2: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
