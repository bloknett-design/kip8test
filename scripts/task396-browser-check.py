#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 396: browser-check — заявка (3 части):
#   (1) ЗЕБРА строк в блоках карточек (чередующийся фон вторых
#       строк: профиль/отпуска/мероприятия/СИЗ; попап шахматки —
#       без зебры);
#   (2) КОМПАКТНЫЕ кнопки в ВЕРХНЕМ ПРАВОМ углу блоков:
#       «Правка данных…»/«Уволить…» — шапка профиля; «+ Отпуск…»/
#       «+ Мероприятие…»/«+ СИЗ…» — шапки своих блоков; контракты
#       onclick прежние; строк-действий внизу блоков больше нет;
#   (3) ОГЛАВЛЕНИЯ блоков — шрифт крупнее/ярче + ДРУГОЙ фон
#       (полоса .ws-whead на всю ширину окна: #1E2B42/#E4E0D3;
#       ФИО 16px/700, секции 13px/700, первичный цвет).
# МОК: 6 работников (как Task 395), Иванову: 3 отпуска + 4
# мероприятия года + 3 СИЗ (зебра видна во всех блоках).
# КОНТЕКСТЫ: 1) десктоп 1280 тёмная edit; 2) десктоп тёмная view
# (кнопок НЕТ, шапки/зебра ЕСТЬ); 3) мобильный 375 светлая edit.
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
  {'id': 12, 'таб_номер': '017', 'часть': 2,
   'дата_начала': '%d-08-03' % Y, 'дата_окончания': '%d-08-16' % Y, 'комментарий': ''},
  {'id': 13, 'таб_номер': '017', 'часть': 2,
   'дата_начала': '%d-11-02' % Y, 'дата_окончания': '%d-11-15' % Y, 'комментарий': 'зимняя'},
]
TRAININGS = [
  {'id': 31, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Охрана труда',
   'дата_начала': d(5), 'дата_окончания': d(5)},
  {'id': 32, 'таб_номер': '017', 'тип': 'обучение', 'тема': 'Пожарная безопасность',
   'дата_начала': '%d-03-10' % Y, 'дата_окончания': '%d-03-10' % Y},
  {'id': 33, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Первая помощь',
   'дата_начала': '%d-06-15' % Y, 'дата_окончания': '%d-06-15' % Y},
  {'id': 34, 'таб_номер': '017', 'тип': 'проверка знаний', 'тема': 'Экзамен',
   'дата_начала': '%d-12-05' % Y, 'дата_окончания': '%d-12-05' % Y},
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
                      body='not found (t396-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t396-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

EDIT_PERMS = {'workschedule.view': True, 'workschedule.edit': True}
VIEW_PERMS = {'workschedule.view': True}

# зебра: Chromium квантует альфу к 8 битам (0.045 → 0.043,
# 0.05 → 0.05/0.051) — сравниваем ТОЛЬКО префикс цвета с альфой
def alt_dark(bg):
    return bg is not None and bg.startswith('rgba(255, 255, 255, 0.04')
def alt_light(bg):
    return bg is not None and (bg.startswith('rgba(0, 0, 0, 0.05'))
def plain(bg):
    return bg == 'rgba(0, 0, 0, 0)'

# съём данных карточки (панели, шапки, кнопки, зебра, стили)
CARD_PROBE = """(function(){
    var body = document.getElementById('wsWorkersBody');
    var grid = body ? body.querySelector('.ws-wgrid2') : null;
    var cards = grid ? grid.querySelectorAll('.ws-wcard') : [];
    function rect(el) { var r = el.getBoundingClientRect();
        return {left: r.left, top: r.top, right: r.right,
                width: r.width, height: r.height}; }
    function cardInfo(card) {
        var head = card.querySelector(':scope > .ws-whead');
        var acts = head ? head.querySelector(':scope > .ws-whead-a') : null;
        var hs = head ? getComputedStyle(head) : null;
        var nameT = head ? head.querySelector('.ws-whead-name') : null;
        var secT = head ? head.querySelector('.ws-whead-t:not(.ws-whead-name)') : null;
        var ns = nameT ? getComputedStyle(nameT) : null;
        var ss = secT ? getComputedStyle(secT) : null;
        var btns = acts ? acts.querySelectorAll(':scope > .ws-wbtn') : [];
        var btnSt = btns.length ? getComputedStyle(btns[0]) : null;
        var danger = acts ? acts.querySelector('.ws-wbtn-danger') : null;
        var dSt = danger ? getComputedStyle(danger) : null;
        var fields = card.querySelectorAll(':scope > .ws-emp-field');
        var rows = card.querySelectorAll(':scope > .ws-popup-row');
        var ppes = card.querySelectorAll(':scope > .ws-ppe-item');
        function rowBg(list, idx) {
            return list[idx] ? getComputedStyle(list[idx]).backgroundColor : null;
        }
        return {
            hasHead: !!head,
            headBg: hs ? hs.backgroundColor : null,
            headML: hs ? hs.marginLeft : null,
            headBB: hs ? hs.borderBottomWidth : null,
            headR: head ? rect(head) : null,
            cardR: rect(card),
            nameFont: ns ? [ns.fontSize, ns.fontWeight, ns.color, ns.textTransform] : null,
            secFont: ss ? [ss.fontSize, ss.fontWeight, ss.color, ss.textTransform] : null,
            nBtns: btns.length,
            btn: btnSt ? [btnSt.height, btnSt.fontSize, btnSt.backgroundColor,
                          btnSt.color, btnSt.borderRadius] : null,
            btnR: btns.length ? rect(btns[btns.length - 1]) : null,
            dangerBg: dSt ? dSt.backgroundColor : null,
            legacyRows: card.querySelectorAll(':scope > .ws-popup-more').length,
            txt: card.textContent || '',
            fieldsN: fields.length,
            f1: rowBg(fields, 0), f2: rowBg(fields, 1),
            f3: rowBg(fields, 2), f4: rowBg(fields, 3),
            rowsN: rows.length,
            r1: rowBg(rows, 0), r2: rowBg(rows, 1),
            r3: rowBg(rows, 2), r4: rowBg(rows, 3),
            ppesN: ppes.length,
            p1: rowBg(ppes, 0), p2: rowBg(ppes, 1), p3: rowBg(ppes, 2),
            zebraRadius: fields.length > 1 ? getComputedStyle(fields[1]).borderRadius : null
        };
    }
    var out = {n: cards.length, cards: [], btnsTotal: 0, heads: 0};
    for (var i = 0; i < cards.length; i++) {
        var ci = cardInfo(cards[i]);
        out.cards.push(ci);
        out.btnsTotal += ci.nBtns;
        if (ci.hasHead) out.heads += 1;
    }
    return out;
})()"""

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
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    e = page.evaluate(CARD_PROBE)
    check('B1: 4 блока-окна, КАЖДЫЙ с шапкой .ws-whead',
          e['n'] == 4 and e['heads'] == 4, (e['n'], e['heads']))
    c = e['cards']
    check('B2: шапки — ДРУГОЙ фон #1E2B42 (не фон панели #243349)',
          all(ci['headBg'] == 'rgb(30, 43, 66)' for ci in c),
          [ci['headBg'] for ci in c])
    check('B3: полоса НА ВСЮ ШИРИНУ окна (margin -16px, ширина = окно − рамки)',
          c[0]['headML'] == '-16px' and
          abs(c[0]['headR']['width'] - (c[0]['cardR']['width'] - 4)) < 2 and
          abs(c[0]['headR']['left'] - (c[0]['cardR']['left'] + 2)) < 2,
          (c[0]['headML'], c[0]['headR'], c[0]['cardR']))
    check('B4: оглавление ФИО — 16px/700/первичный цвет/без капса',
          c[0]['nameFont'][0] == '16px' and c[0]['nameFont'][1] == '700' and
          c[0]['nameFont'][2] == 'rgb(224, 224, 224)' and
          c[0]['nameFont'][3] == 'none', c[0]['nameFont'])
    check('B5: оглавления секций — 13px/700/первичный/капс (было 12px/600/вторичный)',
          all(ci['secFont'] and ci['secFont'][0] == '13px' and ci['secFont'][1] == '700' and
              ci['secFont'][2] == 'rgb(224, 224, 224)' and ci['secFont'][3] == 'uppercase'
              for ci in c[1:]), [ci['secFont'] for ci in c[1:]])
    check('B6: нижняя линия шапки (разделитель с контентом)',
          all(ci['headBB'] and ci['headBB'] != '0px' for ci in c),
          [ci['headBB'] for ci in c])
    check('C1: 5 КОМПАКТНЫХ кнопок: 2 в профиле + «+ Отпуск…» + «+ Мероприятие…» + «+ СИЗ…»',
          e['btnsTotal'] == 5 and c[0]['nBtns'] == 2 and
          c[1]['nBtns'] == 1 and c[2]['nBtns'] == 1 and c[3]['nBtns'] == 1,
          (e['btnsTotal'], [ci['nBtns'] for ci in c]))
    check('C2: кнопка — 26px высота / 12px шрифт / акцент сайта / белый текст',
          c[0]['btn'] and c[0]['btn'][0] == '26px' and c[0]['btn'][1] == '12px' and
          c[0]['btn'][2] == 'rgb(74, 143, 199)' and c[0]['btn'][3] == 'rgb(255, 255, 255)',
          c[0]['btn'])
    check('C3: «Уволить…» — красная #ef5350',
          c[0]['dangerBg'] == 'rgb(239, 83, 80)', c[0]['dangerBg'])
    check('C4: кнопки — В ВЕРХНЕМ ПРАВОМ углу (правый край у рамки окна)',
          abs(c[0]['btnR']['right'] - (c[0]['cardR']['right'] - 16)) < 3 and
          c[0]['btnR']['top'] - c[0]['cardR']['top'] < 50,
          (c[0]['btnR'], c[0]['cardR']))
    check('C5: «Правка данных…»/«Уволить…» — в ШАПКЕ профиля (тексты живы)',
          'Правка данных…' in c[0]['txt'] and 'Уволить…' in c[0]['txt'] and
          c[0]['legacyRows'] == 0,
          (c[0]['txt'][:80], c[0]['legacyRows']))
    check('C6: строк-действий ВНИЗУ блоков больше НЕТ (легаси снят у панелей)',
          all(ci['legacyRows'] == 0 for ci in c),
          [ci['legacyRows'] for ci in c])
    check('C7: «+ Отпуск…»/«+ Мероприятие…»/«+ СИЗ…» — в шапках своих блоков',
          '+ Отпуск…' in c[1]['txt'] and '+ Мероприятие…' in c[2]['txt'] and
          '+ СИЗ…' in c[3]['txt'], None)
    # зебра: профиль 4 поля (Режим/Должность/Дата приёма/Комментарий) → 2-я и 4-я alt
    check('D1: ЗЕБРА профиля — строки 1/3 прозрачные, 2/4 с фоном 0.045',
          c[0]['fieldsN'] == 4 and plain(c[0]['f1']) and alt_dark(c[0]['f2']) and
          plain(c[0]['f3']) and alt_dark(c[0]['f4']),
          (c[0]['fieldsN'], c[0]['f1'], c[0]['f2'], c[0]['f3'], c[0]['f4']))
    # отпуска 3 периода → 2-я alt
    check('D2: ЗЕБРА отпусков — вторая строка с фоном',
          c[1]['fieldsN'] == 3 and plain(c[1]['f1']) and alt_dark(c[1]['f2']),
          (c[1]['fieldsN'], c[1]['f1'], c[1]['f2']))
    # мероприятия 4 строки → 2-я и 4-я alt
    check('D3: ЗЕБРА мероприятий — вторая И четвёртая строки',
          c[2]['rowsN'] == 4 and plain(c[2]['r1']) and alt_dark(c[2]['r2']) and
          plain(c[2]['r3']) and alt_dark(c[2]['r4']),
          (c[2]['rowsN'], c[2]['r1'], c[2]['r2'], c[2]['r3'], c[2]['r4']))
    # СИЗ 3 записи → 2-я alt
    check('D4: ЗЕБРА СИЗ — вторая запись с фоном',
          c[3]['ppesN'] == 3 and plain(c[3]['p1']) and alt_dark(c[3]['p2']),
          (c[3]['ppesN'], c[3]['p1'], c[3]['p2']))
    check('D5: полосы-«пилюли» — скругление 6px',
          c[0]['zebraRadius'] == '6px', c[0]['zebraRadius'])
    page.screenshot(path='task396-proof-workers-dark.png', full_page=False)
    # попап сетки — прежний вид (без зебры/шапок): карточка у колонки ФИО
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    pop = page.evaluate("""(function(){
        var html = window.WorkSchedule && window.WorkSchedule._renderEmpPopup
            ? window.WorkSchedule._renderEmpPopup('017') : null;
        return html ? {whead: html.indexOf('ws-whead') !== -1,
                       zebra: html.indexOf('ws-row-alt') !== -1,
                       btn: html.indexOf('ws-wbtn') !== -1,
                       title: html.indexOf('ws-popup-title') !== -1,
                       sec: html.indexOf('ws-popup-sec') !== -1} : null;
    })()""")
    check('E1: попап шахматки — прежний вид (title/sec, БЕЗ whead/зебры/кнопок)',
          pop and pop['title'] and pop['sec'] and not pop['whead'] and
          not pop['zebra'] and not pop['btn'], pop)
    check('E2: 0 JS-ошибок (контекст 1)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, тёмная, view ==========
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'viewer', VIEW_PERMS)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    e2 = page.evaluate(CARD_PROBE)
    check('F1: зритель — шапки-оглавления ЕСТЬ (4), кнопок НЕТ',
          e2['n'] == 4 and e2['heads'] == 4 and e2['btnsTotal'] == 0,
          (e2['n'], e2['heads'], e2['btnsTotal']))
    check('F2: зритель — ЗЕБРА видна (не правка)',
          alt_dark(e2['cards'][0]['f2']) and alt_dark(e2['cards'][2]['r2']),
          (e2['cards'][0]['f2'], e2['cards'][2]['r2']))
    check('F3: зритель — 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task396-proof-workers-view.png', full_page=False)
    ctx.close()

    # ========== Контекст 3: мобильный 375, светлая, edit ==========
    ctx = browser.new_context(viewport={'width': 375, 'height': 700})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mobile', EDIT_PERMS)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    e3 = page.evaluate(CARD_PROBE)
    c3 = e3['cards']
    check('G1: мобайл — 4 блока со шапками (стек)',
          e3['n'] == 4 and e3['heads'] == 4, (e3['n'], e3['heads']))
    check('G2: шапка светлая #E4E0D3 (не белая панель)',
          all(ci['headBg'] == 'rgb(228, 224, 211)' for ci in c3),
          [ci['headBg'] for ci in c3])
    check('G3: кнопка — оранжевый акцент светлой темы #C6613F',
          c3[0]['btn'] and c3[0]['btn'][2] == 'rgb(198, 97, 63)', c3[0]['btn'])
    check('G4: «Уволить…» — красная светлая #c62828',
          c3[0]['dangerBg'] == 'rgb(198, 40, 40)', c3[0]['dangerBg'])
    check('G5: ЗЕБРА светлой темы — тёмный тинт 0.05',
          alt_light(c3[0]['f2']) and alt_light(c3[2]['r2']),
          (c3[0]['f2'], c3[2]['r2']))
    check('G6: заголовок ФИО — первичный цвет светлой темы',
          c3[0]['nameFont'][2] == 'rgb(20, 20, 19)', c3[0]['nameFont'])
    # кнопки при узком экране: переносятся ниже заголовка, оставаясь ПРАВЕЕ
    wrapOk = page.evaluate("""(function(){
        var card = document.querySelectorAll('.ws-wcard')[0];
        var head = card.querySelector(':scope > .ws-whead');
        var t = head.querySelector('.ws-whead-t');
        var a = head.querySelector(':scope > .ws-whead-a');
        var wrap = (a.getBoundingClientRect().top - t.getBoundingClientRect().top) > 4;
        var rightOk = (head.getBoundingClientRect().right - a.getBoundingClientRect().right) < 40;
        return {wrap: wrap, rightOk: rightOk};
    })()""")
    check('G7: узкий экран — кнопки переносятся ниже заголовка и остаются справа',
          wrapOk['wrap'] and wrapOk['rightOk'], wrapOk)
    check('G8: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task396-proof-mobile-light.png', full_page=False)
    ctx.close()

    browser.close()

print('══════════════════════════════════════════')
print('Task 396 browser-check: %d/%d (PASS/FAIL)' % (PASS, PASS + FAIL))
print('══════════════════════════════════════════')
raise SystemExit(1 if FAIL else 0)
