#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 404: browser-check — заявка «В картах работников блок СИЗ
# размести слева от блока мероприятия. По итогу в верхней части
# должно быть три блока, слева на право, блок профиля (под ним блок
# отпуска), блок СИЗ и блок мероприятия, то есть нужно подогнать
# размеры блоков, что бы они поместились в одной линии. И кнопки
# "редактировать" в блоках отпуска и мероприятия выравнить
# разместить рядом с кнопками "удалить", по примеру как в блоке
# СИЗ. В разделе Табель учёта рабочего времени, в окне мероприятий
# убери информацию по отпускам».
# МОК: 5 активных работников (как в Task 403); Иванов — отпуск
# 20–26 текущего месяца, СИЗ «Каска» истекает в текущем месяце
# (для секции СИЗ окна), 2 мероприятия месяца.
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, view: ОКНО МЕРОПРИЯТИЙ тулбара — БЕЗ
#      секции «Отпуска» (при живом отпуске в данных), секции
#      «Мероприятия» и «СИЗ» живы; регресс ячейки «5 р.»; 0 ошибок;
#   2) десктоп 1280 светлая, edit: страница «Работники» — ТРИ
#      колонки (профиль+отпуска | СИЗ | мероприятия), верхние
#      блоки в одну линию, СИЗ ЛЕВЕЕ мероприятий; кнопки ✎/✕
#      отпусков/мероприятий — РЯДОМ у правого края (как СИЗ);
#      правка комментария → updateEmployee (регресс 403); 0 ошибок;
#   3) мобайл 375 светлая, view: карточка — стек профиль →
#      отпуска → СИЗ → мероприятия; 0 JS-ошибок.
# Порт 8905 (запуск: python3 -m http.server 8905 &).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8905
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
TRAININGS = [
  {'id': 1, 'таб_номер': '017', 'тип': 'Инструктаж по охране труда',
   'тема': 'Охрана труда', 'дата_начала': d(Y, M, 10), 'дата_окончания': d(Y, M, 10)},
  {'id': 2, 'таб_номер': '017', 'тип': 'Противоаварийная тренировка',
   'тема': 'Пожарная безопасность', 'дата_начала': d(Y, M, 18), 'дата_окончания': d(Y, M, 18)},
]
VACATIONS = [
  {'id': 1, 'таб_номер': '017', 'часть': 1,
   'дата_начала': d(Y, M, 20), 'дата_окончания': d(Y, M, 26)},
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Костюм для защиты от растворов кислот и щелочей',
   'дата_выдачи': d(Y, 8, 17), 'срок_годности': '1 год',
   'дата_окончания': d(Y + 1, 8, 17), 'примечание': ''},
  # Task 404: Каска истекает в текущем месяце — секция «СИЗ» окна
  # мероприятий должна показаться (проверка живости СИЗ)
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
    if action == 'workSchedule.updateEmployee':
        API_CALLS.append(('updateEmployee', dict(body or {})))
        tab = str((body or {}).get('таб_номер', ''))
        for e in EMPLOYEES:
            if str(e['таб_номер']) == tab:
                for k in ('ФИО', 'тип', 'должность', 'группа_допуска', 'комментарий'):
                    if k in (body or {}):
                        e[k] = str(body[k])
                if 'смена' in (body or {}):
                    e['смена'] = body['смена']
                return {'ok': True, 'data': {'таб_номер': tab}}
        return {'ok': False, 'error': 'not_found_таб_номер'}
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
                      body='not found (t403-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t403-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

CELLS_JS = """(function(){
    var wrap = document.getElementById('wsGridWrap');
    var cells = wrap.querySelectorAll('tbody td.ws-emp-col');
    var out = [];
    for (var i = 0; i < cells.length; i++) {
        var td = cells[i];
        var name = td.querySelector('.ws-emp-name');
        var pos = td.querySelector('.ws-emp-pos');
        var tip = td.querySelector('.ws-emp-tip');
        out.push({ fio: name ? name.textContent : null,
                   pos: pos ? pos.textContent : null,
                   tip: tip ? tip.textContent : null });
    }
    return out;
})()"""

TABS_JS = """(function(){
    var tabs = document.querySelector('.ws-wtabs');
    if (!tabs) return null;
    var items = tabs.querySelectorAll('.ws-wtab');
    var w = tabs.getBoundingClientRect().width;
    var maxScroll = 0, noWrap = true, i;
    for (i = 0; i < items.length; i++) {
        var it = items[i];
        if (it.scrollWidth > it.clientWidth + 1) noWrap = false;
        if (it.scrollWidth > maxScroll) maxScroll = it.scrollWidth;
    }
    var cs = window.getComputedStyle(tabs);
    return { w: w, n: items.length, noWrap: noWrap, maxScroll: maxScroll,
             display: cs.display, dir: cs.flexDirection };
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
    function actPair(container) {
        if (!container) return null;
        var acts = container.querySelectorAll('.ws-popup-act');
        if (acts.length < 2) return null;
        var a = acts[0].getBoundingClientRect();
        var b = acts[1].getBoundingClientRect();
        var row = container.getBoundingClientRect();
        return { gap: b.left - a.right, rightGap: row.right - b.right };
    }
    var vacRow = null;
    var fields = document.querySelectorAll('.ws-wgrid2 .ws-wcol:first-child .ws-emp-field');
    for (var i = 0; i < fields.length; i++) {
        if (fields[i].querySelector('.ws-popup-act')) { vacRow = fields[i]; break; }
    }
    out.vac = actPair(vacRow);
    out.tr = actPair(document.querySelector('.ws-wgrid2 .ws-wcol-tr .ws-popup-row.ws-popup-event'));
    out.ppe = actPair(document.querySelector('.ws-wgrid2 .ws-wcol-ppe .ws-ppe-item'));
    return out;
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, view ==========
    print('=== Контекст 1: десктоп тёмная — окно мероприятий без отпусков; регресс ячейки ===')
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
    iv = next((c for c in cells if c['fio'] and 'Иванов' in c['fio']), None)
    pe = next((c for c in cells if c['fio'] and 'Петров' in c['fio']), None)
    si = next((c for c in cells if c['fio'] and 'Сидоров' in c['fio']), None)
    # 1) «разряд» → «р.», группа НЕ показана
    check('B1: Иванов — «Слесарь КИПиА 5 р.» (сокращение, БЕЗ группы IV)',
          iv and iv['pos'] == 'Слесарь КИПиА 5 р.', iv and iv['pos'])
    check('B2: Иванов — тип третьей строкой «смена №1»',
          iv and iv['tip'] == 'смена №1', iv and iv['tip'])
    check('B3: Петров — «Инженер КИПиА» (без «разряда» и группы)',
          pe and pe['pos'] == 'Инженер КИПиА', pe and pe['pos'])
    check('B4: Сидоров — «Электромонтёр КИПиА 4 р.» (склонение)',
          si and si['pos'] == 'Электромонтёр КИПиА 4 р.', si and si['pos'])
    check('B5: групп допуска в столбце ФИО НЕТ (ни IV, ни III)',
          iv and si and 'IV' not in (iv['pos'] or '') + (si['pos'] or '')
          and 'III' not in (si['pos'] or ''),
          (iv and iv['pos'], si and si['pos']))
    # 2) ОКНО МЕРОПРИЯТИЙ тулбара — БЕЗ отпусков (Task 404): в моке
    #    отпуск Иванова 20–26 текущего месяца (до 404 секция была бы)
    monthsNom = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    ev = page.evaluate("(function(){var e=document.getElementById('wsEventsPanel');" +
                       "return e?e.innerHTML:'';})()")
    check('B6: окно мероприятий живо (секция «Мероприятия»)',
          ('Мероприятия · ' + monthsNom[M - 1] + ' ' + str(Y)) in ev, ev[:80])
    check('B7: НЕТ секции «Отпуска» (при живом отпуске в данных)',
          'Отпуска · ' not in ev and 'Отпуск · ' not in ev, ev[:200])
    check('B8: НЕТ точек отпусков (класс удалён)',
          'ws-ep-dot-vac' not in ev and 'ws-ep-cap-vac' not in ev)
    check('B9: секция «СИЗ» жива (Каска истекает в месяце)',
          ('СИЗ · ' + monthsNom[M - 1] + ' ' + str(Y)) in ev and 'Каска' in ev)
    check('B10: записи мероприятий живы (Охрана труда)', 'Охрана труда' in ev)
    # 2) попап по клику на ячейку — БЕЗ СИЗ
    page.click("td.ws-emp-col[data-tab='017']")
    page.wait_for_timeout(700)
    card = page.evaluate("(function(){var p=document.getElementById('wsEmpPopup');" +
                         "return p?p.innerHTML:'';})()")
    check('C1: попап открылся', 'Иванов' in card)
    check('C2: в попапе НЕТ секции СИЗ', 'СИЗ' not in card)
    check('C3: в попапе НЕТ записей СИЗ (Костюм/Каска)',
          'Костюм' not in card and 'Каска' not in card)
    check('C4: секции отпусков/мероприятий живы',
          'Отпуска · %d' % Y in card and 'Мероприятия · %d' % Y in card)
    check('C5: строка «Группа допуска» профиля жива (IV)',
          'ws-emp-k">Группа допуска' in card and 'IV' in card)
    check('C6: мероприятия в попапе — записи Иванова (Охрана труда)',
          'Охрана труда' in card)
    page.screenshot(path='task404-proof-grid-dark.png', full_page=False)
    page.keyboard.press('Escape')
    page.wait_for_timeout(400)
    check('D: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, edit ==========
    print('=== Контекст 2: десктоп светлая — ярлыки, колонки, правка комментария ===')
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
    # 1) ярлыки — по самому длинному тексту
    t = page.evaluate(TABS_JS)
    check('E1: колонка ярлыков на месте (6 ярлыков)', t and t['n'] == 6, t and t['n'])
    check('E2: ширина — по длинной фамилии (> 236px фолбэка)',
          t and t['w'] > 236, t and round(t['w']))
    check('E3: все ярлыки ОДНОЙ строкой (без переноса)',
          t and t['noWrap'], t and t['noWrap'])
    check('E4: самый длинный ярлык влезает (w ≥ его scrollWidth)',
          t and t['w'] >= t['maxScroll'] - 1, t and (round(t['w']), t['maxScroll']))
    # 2) карточка Иванова: ТРИ колонки (Task 404)
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    c2 = page.evaluate(CARD_COLS_JS)
    check('F0: ТРИ колонки', c2 and len(c2['cols']) == 3,
          c2 and len(c2['cols']))
    check('F1: колонка 1 — профиль + отпуска',
          c2 and len(c2['cols'][0]['heads']) == 2 and
          c2['cols'][0]['heads'][0].find('Иванов') != -1 and
          c2['cols'][0]['heads'][1].startswith('Отпуска ·'),
          c2 and c2['cols'][0]['heads'])
    check('F2: колонка 2 — СИЗ; колонка 3 — МЕРОПРИЯТИЯ',
          c2 and len(c2['cols'][1]['heads']) == 1 and
          c2['cols'][1]['heads'][0].startswith('СИЗ ·') and
          len(c2['cols'][2]['heads']) == 1 and
          c2['cols'][2]['heads'][0].startswith('Мероприятия ·'),
          c2 and [c2['cols'][1]['heads'], c2['cols'][2]['heads']])
    check('F3: верхние блоки В ОДНУ ЛИНИЮ (tops равны, допуск 2px)',
          c2 and len(c2['tops']) == 3 and c2['tops'][0] is not None and
          abs(c2['tops'][0] - c2['tops'][1]) < 2 and
          abs(c2['tops'][1] - c2['tops'][2]) < 2, c2 and c2['tops'])
    check('F4: порядок слева направо: профиль | СИЗ | мероприятия',
          c2 and c2['cols'][0]['x'] < c2['cols'][1]['x'] < c2['cols'][2]['x'],
          c2 and [round(c['x']) for c in c2['cols']])
    check('F5: колонки РАВНЫЕ (подогнаны под одну линию)',
          c2 and abs(c2['cols'][0]['w'] - c2['cols'][1]['w']) < 2 and
          abs(c2['cols'][1]['w'] - c2['cols'][2]['w']) < 2,
          c2 and [round(c['w']) for c in c2['cols']])
    check('F6: СИЗ — на странице (Костюм жив в блоке)',
          page.evaluate("!!document.querySelector('.ws-wgrid2') && " +
                        "document.querySelector('.ws-wtab-body').innerHTML.indexOf('Костюм') !== -1"))
    # кнопки ✎/✕ — РЯДОМ у правого края (как в СИЗ)
    check('F7: отпуск — ✎ и ✕ РЯДОМ (зазор ≤ 12px)',
          c2 and c2['vac'] and c2['vac']['gap'] <= 12,
          c2 and c2['vac'])
    check('F8: отпуск — кнопки прижаты вправо (≤ 22px)',
          c2 and c2['vac'] and c2['vac']['rightGap'] <= 22,
          c2 and c2['vac'])
    check('F9: мероприятие — ✎ и ✕ РЯДОМ (зазор ≤ 12px)',
          c2 and c2['tr'] and c2['tr']['gap'] <= 12,
          c2 and c2['tr'])
    check('F10: СИЗ (образец) — ✎ и ✕ рядом',
          c2 and c2['ppe'] and c2['ppe']['gap'] <= 12,
          c2 and c2['ppe'])
    page.screenshot(path='task404-proof-workers-light.png', full_page=False)
    # 3) правка комментария — не группы!
    page.click('.ws-emp-editdata')
    page.wait_for_selector('#wsEmpSheet.active', timeout=4000)
    page.wait_for_timeout(600)
    cmt0 = page.evaluate("document.getElementById('wsEmpComment').value")
    grp0 = page.evaluate("document.getElementById('wsEmpAccessGroup').value")
    check('G1: шторка правки — комментарий пуст (префилл)',
          cmt0 == '', repr(cmt0))
    check('G2: шторка правки — группа IV (префилл, не комментарий)',
          grp0 == 'IV', repr(grp0))
    page.fill('#wsEmpComment', 'Проверка комментария 404')
    page.screenshot(path='task404-proof-comment-edit.png', full_page=False)
    page.click('#wsEmpSubmitBtn')
    page.wait_for_timeout(1500)
    upd = [c for c in API_CALLS if c[0] == 'updateEmployee']
    check('H1: серверу ушёл updateEmployee с комментарием',
          upd and upd[-1][1].get('комментарий') == 'Проверка комментария 404',
          upd[-1][1].get('комментарий') if upd else None)
    check('H2: в payload группа = IV (НЕ комментарий — баг фиксен)',
          upd and upd[-1][1].get('группа_допуска') == 'IV',
          upd[-1][1].get('группа_допуска') if upd else None)
    check('H3: в payload должность сохранена',
          upd and upd[-1][1].get('должность') == 'Слесарь КИПиА 5 разряд',
          upd[-1][1].get('должность') if upd else None)
    # карточка перерисовалась: комментарий в профиле, группа отдельно
    body_html = page.evaluate("document.getElementById('wsWorkersBody').innerHTML")
    check('H4: в карточке комментарий отображается (НЕ группа повтором)',
          'Проверка комментария 404' in body_html)
    check('H5: «Группа допуска» в карточке — строка профиля жива (IV)',
          'Группа допуска' in body_html)
    # 4) сводная «Общая» — колонка группы жива
    page.click(".ws-wtabs button:has-text('Общая')")
    page.wait_for_timeout(900)
    gen = page.evaluate("(function(){var t=document.querySelector('.ws-wgen-table');" +
                        "return t?t.innerHTML:'';})()")
    check('I1: сводная «Общая» — колонка «Группа допуска» жива',
          'Группа допуска' in gen)
    check('I2: сводная — должности ПОЛНЫЕ (с «разряд»)',
          'Слесарь КИПиА 5 разряд' in gen)
    check('J: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, светлая, view ==========
    print('=== Контекст 3: мобайл 375 светлая — лента ярлыков, стек карточки ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 375, 'height': 800})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    cells = page.evaluate(CELLS_JS)
    iv = next((c for c in cells if c['fio'] and 'Иванов' in c['fio']), None)
    check('K1: мобайл — ячейка Иванова «Слесарь КИПиА 5 р.»',
          iv and iv['pos'] == 'Слесарь КИПиА 5 р.', iv and iv['pos'])
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    tm = page.evaluate(TABS_JS)
    check('K2: мобайл — ярлыки ГОРИЗОНТАЛЬНОЙ лентой',
          tm and tm['display'] == 'flex' and tm['dir'] == 'row',
          tm and (tm['display'], tm['dir']))
    check('K3: лента на всю ширину (width ≥ 340)',
          tm and tm['w'] >= 340, tm and round(tm['w']))
    page.evaluate("document.querySelector('.ws-wtabs').scrollLeft = 400")
    check('K4: лента скроллится вправо (длинные фамилии)',
          page.evaluate("document.querySelector('.ws-wtabs').scrollLeft > 0"))
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    stack = page.evaluate("""(function(){
        var hs = document.querySelectorAll('.ws-wgrid2 .ws-whead-t');
        var out = [];
        for (var i = 0; i < hs.length; i++) out.push(hs[i].textContent.trim());
        return out;
    })()""")
    check('K5: мобайл — стек блоков: профиль → отпуска → СИЗ → мероприятия',
          len(stack) == 4 and stack[0].find('Иванов') != -1 and
          stack[1].startswith('Отпуска') and stack[2].startswith('СИЗ') and
          stack[3].startswith('Мероприятия'), stack)
    page.screenshot(path='task404-proof-mobile.png', full_page=False)
    check('L: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
