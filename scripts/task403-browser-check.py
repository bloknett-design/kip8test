#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 403: browser-check — заявка «На странице Табель учёта рабочего
# времени, в столбце с фамилиями в должности сократи слово разряд на
# "р.", и убери данные группы допуска, и в сплывающем окне при
# нажатии на ячейку с фамилией работника убери данные СИЗ. При
# редактировании комментария в картах работников, изменения не
# применяются, а повторяются данные из группы допуска. В Табель
# учёта рабочего времени / Работники, ширину ярлыков с фамилиями
# работников сделай по габаритам самого длинного текста, блок
# мероприятия перемести в верх между блоками профиля и СИЗ».
# МОК: 4 активных работника — Иванов «Слесарь КИПиА 5 разряд»/IV,
# Петров «Инженер КИПиА»/без группы, Сидоров «Электромонтёр КИПиА
# 4 разряда»/III, Ахметзянов Равиль Галиевич «Мастер КИПиА»/II
# (самый длинный ярлык — для замера ширины); СИЗ/мероприятия/
# отпуска Иванова — непустые.
# КОНТЕКСТЫ:
#   1) десктоп 1280 тёмная, view: ячейка — должность СОКРАЩЁННО
#      («Слесарь КИПиА 5 р.», «Электромонтёр КИПиА 4 р.»), БЕЗ
#      группы допуска; тип — третьей строкой; попап по клику на
#      ячейку — БЕЗ СИЗ (профиль/отпуска/мероприятия живы, «Группа
#      допуска» в профиле жива); 0 JS-ошибок;
#   2) десктоп 1280 светлая, edit: страница «Работники» — ярлыки
#      по самому длинному тексту (колонка > 236px фолбэка, все
#      ярлыки одной строкой); карточка: ЛЕВАЯ колонка профиль +
#      отпуска, ПРАВАЯ — мероприятия НАД СИЗ (между профилем и
#      СИЗ); правка комментария → updateEmployee с комментарием
#      (НЕ группой); сводная «Общая» — колонка «Группа допуска»
#      жива; 0 JS-ошибок;
#   3) мобайл 375 светлая, view: ячейка — «5 р.»; страница
#      «Работники» — ярлыки горизонтальной лентой; карточка — стек
#      профиль → отпуска → мероприятия → СИЗ; 0 JS-ошибок.
# Порт 8903 (запуск: python3 -m http.server 8903 &).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8903
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
  {'id': 2, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': '', 'срок_годности': 'До износа',
   'дата_окончания': 'До износа', 'примечание': ''},
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
    var cols = document.querySelectorAll('.ws-wgrid2 .ws-wcol');
    if (cols.length < 2) return null;
    function heads(col) {
        var hs = col.querySelectorAll('.ws-whead-t');
        var out = [];
        for (var i = 0; i < hs.length; i++) out.push(hs[i].textContent.trim());
        return out;
    }
    var l = cols[0].getBoundingClientRect();
    var r = cols[1].getBoundingClientRect();
    return { leftHeads: heads(cols[0]), rightHeads: heads(cols[1]),
             leftX: l.left, rightX: r.left,
             leftW: l.width, rightW: r.width,
             lprofY: (cols[0].querySelector('.ws-wcard')||{getBoundingClientRect:function(){return{top:0}}}).getBoundingClientRect().top,
             trY: (cols[1].querySelectorAll('.ws-wcard')[0]||{getBoundingClientRect:function(){return{top:0}}}).getBoundingClientRect().top,
             ppeY: (cols[1].querySelectorAll('.ws-wcard')[1]||{getBoundingClientRect:function(){return{top:0}}}).getBoundingClientRect().top };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, view ==========
    print('=== Контекст 1: десктоп тёмная — должность «р.», без группы; попап без СИЗ ===')
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
    page.screenshot(path='task403-proof-grid-dark.png', full_page=False)
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
    # 2) карточка Иванова: колонки и порядок блоков
    page.click(".ws-wtabs button:has-text('Иванов И. И.')")
    page.wait_for_timeout(900)
    c2 = page.evaluate(CARD_COLS_JS)
    check('F1: левая колонка — профиль + отпуска',
          c2 and c2['leftHeads'][0].find('Иванов') != -1 and
          c2['leftHeads'][1].startswith('Отпуска ·'), c2 and c2['leftHeads'])
    check('F2: правая колонка — МЕРОПРИЯТИЯ, затем СИЗ',
          c2 and len(c2['rightHeads']) == 2 and
          c2['rightHeads'][0].startswith('Мероприятия ·') and
          c2['rightHeads'][1].startswith('СИЗ ·'), c2 and c2['rightHeads'])
    check('F3: СИЗ — на странице (Костюм жив в блоке)',
          page.evaluate("!!document.querySelector('.ws-wgrid2') && " +
                        "document.querySelector('.ws-wtab-body').innerHTML.indexOf('Костюм') !== -1"))
    check('F4: мероприятия — НАД СИЗ (верх правой колонки)',
          c2 and c2['trY'] < c2['ppeY'], c2 and (c2['trY'], c2['ppeY']))
    check('F5: мероприятия — ПРАВЕЕ профиля (между профилем и СИЗ)',
          c2 and c2['rightX'] > c2['leftX'] and c2['trY'] <= c2['lprofY'] + 40,
          c2 and (c2['rightX'], c2['leftX'], c2['trY'], c2['lprofY']))
    check('F6: колонки РАВНЫЕ', c2 and abs(c2['leftW'] - c2['rightW']) < 2,
          c2 and (c2['leftW'], c2['rightW']))
    page.screenshot(path='task403-proof-workers-light.png', full_page=False)
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
    page.fill('#wsEmpComment', 'Проверка комментария 403')
    page.screenshot(path='task403-proof-comment-edit.png', full_page=False)
    page.click('#wsEmpSubmitBtn')
    page.wait_for_timeout(1500)
    upd = [c for c in API_CALLS if c[0] == 'updateEmployee']
    check('H1: серверу ушёл updateEmployee с комментарием',
          upd and upd[-1][1].get('комментарий') == 'Проверка комментария 403',
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
          'Проверка комментария 403' in body_html)
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
    check('K5: мобайл — стек блоков: профиль → отпуска → мероприятия → СИЗ',
          len(stack) == 4 and stack[0].find('Иванов') != -1 and
          stack[1].startswith('Отпуска') and stack[2].startswith('Мероприятия') and
          stack[3].startswith('СИЗ'), stack)
    page.screenshot(path='task403-proof-mobile.png', full_page=False)
    check('L: JS-ошибок нет', js_errors == [], js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
