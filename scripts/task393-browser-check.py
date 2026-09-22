#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 393: browser-check — заявка: «В картах работников нужно
# сделать шрифт текста больше, и разбить карты работников на
# четыре блока: профиль (Правка данных…/Уволить…), Отпуска,
# Мероприятия, СИЗ».
# МОК: 6 работников (как Task 392), СИЗ Иванову (костюм + очки),
# 2 отпуска Иванову (Часть 1/Часть 2), 1 мероприятие текущего
# месяца Иванову.
# ДЕСКТОП 1280 (тёмная, Админ): A загрузка; B табель; C «Работники»
#   → вкладка Иванова: C1 ЧЕТЫРЕ окна .ws-wcard; C2 состав блока 1
#   (ФИО/Режим/Должность/Дата приёма/Правка данных…/Уволить…);
#   C3 блок 2 «Отпуска · ГОД» (Часть 1/2, «+ Отпуск…»); C4 блок 3
#   «Мероприятия · МЕСЯЦ ГОД» («+ Мероприятие…»); C5 блок 4
#   «СИЗ · средства индивидуальной защиты» (записи, «+ СИЗ…»);
#   C6 изоляция блоков (секции не смешиваются); C7 ШРИФТЫ КРУПНЕЕ
#   (15px шапка / 14px поля-строки / 12px заголовки / 12.5px мета);
#   C8 зазор 12px между окнами; D попап карточки у сетки — прежний
#   компактный вид (12px) + одна панель; E «Общая» — без окон;
#   F 0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ): M1 4 окна в колонку; M2 шрифты;
#   M3 0 JS-ошибок.
# Порт 9006 (запуск: python3 -m http.server 9006 &).
import datetime, json
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
  {'code': 'Д7,2', 'name': 'День 7,2-час', 'color': '#FFF9C4', 'short': 'день 7,2ч'},
  {'code': 'Д',    'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день 12ч'},
  {'code': 'Н',    'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'д',    'name': 'День в вых.', 'color': '#FFD54F', 'short': 'день в выходной'},
  {'code': 'н',    'name': 'Ночь в вых.', 'color': '#78909C', 'short': 'ночь в выходной'},
  {'code': 'ОТ',   'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': 'У',    'name': 'Учебный отпуск', 'color': '#80CBC4', 'short': 'ученический'},
  {'code': 'ОВ',   'name': 'Отгул', 'color': '#C5E1A5', 'short': 'отгул'},
  {'code': 'Б',    'name': 'Больничный', 'color': '#F8BBD0', 'short': 'больничный'},
  {'code': 'ПР',   'name': 'Прогул', 'color': '#EF5350', 'short': 'прогул'},
  {'code': 'И',    'name': 'Инструктаж', 'color': '#B3E5FC', 'short': 'инструктаж'},
  {'code': 'ОБ',   'name': 'Обучение', 'color': '#D1C4E9', 'short': 'обучение'},
  {'code': 'ПЗ',   'name': 'Проверка знаний', 'color': '#FFCDD2', 'short': 'проверка знаний'},
  {'code': '*',    'name': 'Примечание', 'color': '#FFAB91', 'short': 'не плановый'},
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
   'дата_выдачи': '2026-08-17', 'срок_годности': '1 год',
   'дата_окончания': '2027-08-17', 'примечание': ''},
  {'id': 2, 'таб_номер': '017', 'работник': 'Иванов И. И.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'срок_годности': 'До износа',
   'дата_окончания': 'До износа', 'примечание': ''},
]
VACATIONS = [
  {'id': 11, 'таб_номер': '017', 'часть': 1,
   'дата_начала': '%d-06-01' % Y, 'дата_окончания': '%d-06-22' % Y,
   'комментарий': ''},
  {'id': 12, 'таб_номер': '017', 'часть': 2,
   'дата_начала': '%d-12-01' % Y, 'дата_окончания': '%d-12-21' % Y,
   'комментарий': ''},
]
TRAININGS = [
  {'id': 31, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Охрана труда',
   'дата_начала': d(5), 'дата_окончания': d(5)},
]

MONTHS_RU = ['Январь','Февраль','Март','Апрель','Май','Июнь',
             'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

PASS = 0
FAIL = 0

def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag):
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
                        'role': 'Админ'}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'Админ', 'found': True,
                        'permissions': {'workschedule.view': True,
                                        'workschedule.edit': True}}}, ensure_ascii=False))
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
                      body='not found (t393-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t393-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'admin')

    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: табель открыт, сетка отрисована (6 работников)',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length === 6"))

    # ---------- C: «Работники» → вкладка Иванова: 4 блока-окна ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    c = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var tabBody = body ? body.querySelector('.ws-wtab-body') : null;
        var cards = tabBody ? tabBody.querySelectorAll(':scope > .ws-wcard') : [];
        var arr = [];
        for (var i = 0; i < cards.length; i++) arr.push(cards[i].textContent || '');
        var fs = function(sel, prop){
            var el = tabBody ? tabBody.querySelector(sel) : null;
            return el ? getComputedStyle(el)[prop] : null;
        };
        return {
            n: cards.length,
            b1: arr[0] || '', b2: arr[1] || '', b3: arr[2] || '', b4: arr[3] || '',
            gap: cards.length > 1 ? getComputedStyle(cards[0]).marginBottom : null,
            titleFs: fs('.ws-popup-title', 'fontSize'),
            fieldFs: fs('.ws-emp-field', 'fontSize'),
            secFs: fs('.ws-popup-sec', 'fontSize'),
            rowFs: fs('.ws-popup-row', 'fontSize'),
            ppeFs: fs('.ws-ppe-item', 'fontSize'),
            metaFs: fs('.ws-ppe-meta', 'fontSize')
        };
    })()""")
    check('C1: вкладка работника — ЧЕТЫРЕ блока-окна .ws-wcard', c['n'] == 4, c['n'])

    b1, b2, b3, b4 = c['b1'], c['b2'], c['b3'], c['b4']
    check('C2: блок 1 — профиль: ФИО · таб. №, режим, должность, приём, действия',
          ('Иванов И. И.' in b1 and 'таб. №017' in b1 and 'Режим работы' in b1 and
           'сменный' in b1 and 'Должность' in b1 and 'Слесарь КИПиА' in b1 and
           'Дата приёма' in b1 and 'Правка данных…' in b1 and 'Уволить…' in b1),
          b1[:200])
    check('C3: блок 2 — «Отпуска · %d»: Часть 1/Часть 2, «+ Отпуск…»' % Y,
          ('Отпуска · %d' % Y) in b2 and 'Часть 1' in b2 and 'Часть 2' in b2 and
          '+ Отпуск…' in b2, b2[:200])
    mlabel = 'Мероприятия · %s %d' % (MONTHS_RU[M - 1], Y)
    check('C4: блок 3 — «%s»: мероприятие, «+ Мероприятие…»' % mlabel,
          mlabel in b3 and 'Охрана труда' in b3 and '+ Мероприятие…' in b3, b3[:200])
    check('C5: блок 4 — «СИЗ · средства индивидуальной защиты»: записи, «+ СИЗ…»',
          'СИЗ · средства индивидуальной защиты' in b4 and
          'Костюм для защиты от растворов кислот и щелочей' in b4 and
          'выдано 17.08.2026' in b4 and 'срок 1 год' in b4 and 'до 17.08.2027' in b4 and
          'Очки закрытые' in b4 and '+ СИЗ…' in b4, b4[:200])
    check('C6: изоляция блоков — секции НЕ смешиваются',
          ('Отпуска ·' not in b1 and 'Мероприятия ·' not in b1 and 'СИЗ ·' not in b1 and
           'Мероприятия ·' not in b2 and 'СИЗ ·' not in b2 and 'СИЗ ·' not in b3 and
           'Правка данных…' not in b2 and 'Правка данных…' not in b3 and
           'Правка данных…' not in b4))
    check('C7: ШРИФТ КРУПНЕЕ — 15px шапка / 14px поля и строки / 12px заголовки',
          c['titleFs'] == '15px' and c['fieldFs'] == '14px' and
          c['secFs'] == '12px' and c['rowFs'] == '14px' and
          c['ppeFs'] == '14px' and c['metaFs'] == '12.5px',
          (c['titleFs'], c['fieldFs'], c['secFs'], c['rowFs'], c['ppeFs'], c['metaFs']))
    check('C8: зазор между окнами — 12px', c['gap'] == '12px', c['gap'])
    page.screenshot(path='task393-proof-workers.png', full_page=False)

    # ---------- D: попап карточки у сетки — прежний компактный вид ----------
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(700)
    dd = page.evaluate("""(function(){
        var pop = document.getElementById('wsEmpPopup');
        var active = pop && pop.classList.contains('active');
        var fs = active ? getComputedStyle(pop.querySelector('.ws-emp-field')).fontSize : null;
        var titleFs = active ? getComputedStyle(pop.querySelector('.ws-popup-title')).fontSize : null;
        var txt = active ? (pop.textContent || '') : '';
        return {active: active, fs: fs, titleFs: titleFs,
                siz: txt.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
                kostum: txt.indexOf('Костюм') !== -1};
    })()""")
    check('D1: попап карточки у сетки открывается', dd['active'])
    check('D2: попап — прежняя компактная типографика (12px поля, 11px шапка)',
          dd['fs'] == '12px' and dd['titleFs'] == '11px', (dd['fs'], dd['titleFs']))
    check('D3: попап — сплошной вид (все секции в одном окне, СИЗ на месте)',
          dd['siz'] and dd['kostum'])
    page.screenshot(path='task393-proof-grid-popup.png', full_page=False)

    # ---------- E: «Общая» вкладка — без окон карточек ----------
    page.evaluate("WorkSchedule.closeEmpPopup()")
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(800)
    # выбор работника живёт между перерисовками (Task 388) —
    # переключаемся на «Общую» явно, как делает пользователь
    page.click('button.ws-wtab-general')
    page.wait_for_timeout(500)
    e = page.evaluate("""(function(){
        var tabBody = document.querySelector('#wsWorkersBody .ws-wtab-body');
        return tabBody ? tabBody.querySelectorAll(':scope > .ws-wcard').length : -1;
    })()""")
    check('E: «Общая» вкладка — окон карточки нет (сводка)', e == 0, e)

    check('F: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобильный 375, светлая, Админ =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 720})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'mob')

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('#wsWorkersBtn')
    page2.wait_for_timeout(1000)
    page2.click('button[title="Иванов И. И."]')
    page2.wait_for_timeout(800)
    m = page2.evaluate("""(function(){
        var tabBody = document.querySelector('#wsWorkersBody .ws-wtab-body');
        var cards = tabBody ? tabBody.querySelectorAll(':scope > .ws-wcard') : [];
        var first = cards.length ? cards[0] : null;
        var fs = first ? getComputedStyle(first.querySelector('.ws-emp-field')).fontSize : null;
        var lastGap = cards.length > 1 ?
            getComputedStyle(cards[cards.length - 1]).marginBottom : null;
        var vw = window.innerWidth;
        var fit = true;
        for (var i = 0; i < cards.length; i++) {
            var r = cards[i].getBoundingClientRect();
            if (r.right > vw + 1 || r.left < -1) fit = false;
        }
        return {n: cards.length, fs: fs, lastGap: lastGap, fit: fit};
    })()""")
    check('M1: мобильный — 4 блока-окна в колонку, в границах экрана',
          m['n'] == 4 and m['fit'], (m['n'], m['fit']))
    check('M2: мобильный — шрифт полей 14px (крупнее прежнего)', m['fs'] == '14px', m['fs'])
    check('M3: мобильный — последний блок без нижнего зазора', m['lastGap'] == '0px', m['lastGap'])
    page2.screenshot(path='task393-proof-mobile.png', full_page=False)
    check('M4: 0 JS-ошибок (мобильный)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('Task 393 browser-check: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
