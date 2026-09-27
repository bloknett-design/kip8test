#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 435 + 436: browser-check — заявка пользователя:
#   Task 435: «В картах работников, при переключении года в блоке
#   инструктажей, автоматически переключается год в блоке
#   мероприятий, и наоборот то же самое. Эти блоки не должны
#   влиять друг на друга».
#   Task 436: «В разделе расходомеров хозрасчётных, в полных
#   карточках расходомеров, график должен строится по логике -
#   все значения относительно между собой до 100%, но если есть
#   значения, которые больше в два раза и выше чем среднее
#   значение остальных, то все меньше него значения отображаются
#   относительно до 80%..., а большие значения отображаются от 80
#   до 100%».
# КОНТЕКСТЫ (мок-сервер, порт 8936):
#   1) десктоп 1280 тёмная, Админ — РАБОТНИКИ:
#      - оба блока на годe табеля (2026);
#      - ‹ в блоке инструктажей → год ТОЛЬКО инструктажей -1;
#      - ‹ снова → 2024 (мин инструктажей), запись 2024 видна;
#        блок мероприятий НЕ тронут (год и записи 2026);
#      - ‹ в блоке мероприятий → 2025, запись 2025 видна; блок
#        инструктажей остался на 2024 (запись 2024);
#      - записи блоков НЕ смешиваются (инструктажи в b5,
#        мероприятия в b3);
#      - клики навигаторов: b5 с третьим аргументом, b3 — прежний;
#      - зритель (view) — навигаторы живы и раздельны.
#   2) десктоп 1280 тёмная — РАСХОДОМЕРЫ (полная карточка №2):
#      - 12 суточных записей: [10..12 × 11, 300] (300 ≥ 2×
#        среднего остальных ~13.5) → две группы;
#      - высоты: большой бар ≈ 90% (одиночный — середина 80–100),
#        малые в [5..80], минимум малых = 5, максимум = 80;
#      - ни одного бара ниже 5% (пол Task 226);
#      - тултип — фактическое значение (300), не процент.
#   3) мобайл 375 светлая — расходомер: тот же график в полной
#      странице, без переполнения, 0 JS-ошибок.
# + скриншот-пруфы; 0 JS-ошибок во всех контекстах.
import datetime
import json
import threading
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8936
TODAY = datetime.date.today()
Y = TODAY.year
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)


def ru(iso):
    p = str(iso).split('-')
    return p[2] + '.' + p[1] + '.' + p[0]


U_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
U_OT_2024 = 'Повторный инструктаж по промышленной безопасности 2024'
T_OB = 'Охрана труда (ежегодный курс)'
T_STAZH_2025 = 'Стажировка на новом оборудовании 2025'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
]

INSTR_LIST = [
  {'название': U_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': 'Инстр. ОТ'},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#90CAF9', 'short': 'инстр.'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#A5D6A7', 'short': 'обучение'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]


def ev(i, tab, tip, tema, d1, d2=None, days=1, done=0):
    return {'id': i, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d1, 'дата_окончания': d2 or d1,
            'длительность_дней': days, 'комментарий': '',
            'дата_проведения': d1, 'выполнение': done,
            'просрочен': 0 if done else 1}


# лист «Инструктажи» (все годы): 2026 (тек.) + 2024 (мин)
INSTR = [
    ev(600, '0871', 'инструктаж', U_OT, TODAY_ISO),
    ev(601, '0871', 'инструктаж', U_OT_2024, '%04d-06-10' % (Y - 2), done=1),
]

# лист «Мероприятия» (все годы): 2026 (тек.) + 2025 (мин)
EVENTS = [
    ev(500, '0871', 'обучение', T_OB, TODAY_ISO),
    ev(501, '0871', 'обучение', T_STAZH_2025, '%04d-05-20' % (Y - 1)),
]


def fresh_entries():
    out = []
    dim = (datetime.date(TODAY.year, TODAY.month % 12 + 1, 1) -
           datetime.timedelta(days=1)).day
    for day in range(1, dim + 1):
        iso = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, day)
        if day <= 5:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
    return out


ENTRIES = fresh_entries()

# --- расходомеры: метры + архив с выбросом ---
def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)


def meter(i, hoz, param, dprev, dcurr, prev, curr, period):
    return {'id': i, 'hoz': hoz, 'param': param, 'datePrev': mdy(dprev),
            'dateCurr': mdy(dcurr), 'prev': prev, 'curr': curr, 'unit': 'м³',
            'temp': None, 'gcal': None, 'period': period,
            'modRole': 'Админ', 'modName': 'user@test.local',
            'modDisplayName': 'user@test.local',
            'modTimestamp': datetime.datetime.now().isoformat()}


METERS = [
    meter(2, 'Хозрасчёт №2', 'Расход воды речной в корпус 114',
          TODAY - datetime.timedelta(days=1), TODAY, 383291.0, 383291.0,
          'Ежедневно'),
]

# архив №2: 12 суточных записей, НОВЕЙШИЕ ПЕРВЫЕ; последняя (новейшая)
# consumption = 300 — выброс ≥ 2 × среднего остальных (~13.5)
def build_archive():
    cons = [11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12, 300]
    # cons[0] — старейшая ... cons[11] — новейшая; записи строятся от
    # старых к новым, потом reversed (новейшие первые — как сервер)
    recs = []
    prev = 380000.0
    for i, c in enumerate(cons):
        d = TODAY - datetime.timedelta(days=(len(cons) - 1 - i))
        recs.append({
            'meterId': 2, 'hoz': 'Хозрасчёт №2', 'prev': prev,
            'curr': prev + c, 'consumption': c,
            'datePrev': mdy(d - datetime.timedelta(days=1)), 'dateCurr': mdy(d),
            'daysBetween': 1, 'unit': 'м³', 'temp': None, 'gcal': None,
            'period': 'Ежедневно', 'modRole': 'Админ',
            'modName': 'user@test.local',
            'timestamp': datetime.datetime.now().isoformat(),
            'comment': '', 'anomaly': '', 'entryType': 'сутки'})
        prev += c
    recs.reverse()
    return recs


ARCHIVE_2 = build_archive()

PASS = 0
FAIL = 0
ADMIN = True


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if ADMIN else 'КИП ИОС'}}
    if action == 'getMyAccess':
        if ADMIN:
            perms = {'calc.view': True, 'library.view': True,
                     'kipios.view': True, 'workschedule.view': True,
                     'workschedule.edit': True, 'flowmeter.view': True}
            role = 'Админ'
        else:
            perms = {'calc.view': True, 'library.view': True,
                     'kipios.view': True, 'workschedule.view': True,
                     'workschedule.edit': False,
                     'workschedule.view.min': False, 'flowmeter.view': True}
            role = 'КИП ИОС'
        return {'ok': True, 'data': {'role': role, 'found': True,
                'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': json.loads(json.dumps(METERS))}}
    if action == 'flowmeter.getValidationRules':
        return {'ok': True, 'data': {'rules': []}}
    if action == 'flowmeter.getRecentAllMeters':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records':
                json.loads(json.dumps(ARCHIVE_2))}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        inc = bool(body and body.get('includeArchived'))
        emps = EMPLOYEES if inc else [e for e in EMPLOYEES
                                       if not e['в_архиве']]
        return {'ok': True, 'data': {'employees': emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {
            'trainings': [dict(r) for r in INSTR + EVENTS
                          if r['дата_начала'][:4] == str(Y)],
            'instrList': [dict(x) for x in INSTR_LIST],
            'instrAll': [dict(r) for r in INSTR],
            'eventsAll': [dict(r) for r in EVENTS]}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in ENTRIES]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t435-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t435-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# --- JS-хелперы: карточка «Работники» ---
BLOCK_JS = """(function(title){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf(title) !== -1) return cards[i];
    }
    return null;
})"""


def block_year(page, title):
    return page.evaluate("""(function(title){
    var card = (function(){
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var i = 0; i < cards.length; i++) {
            var h = cards[i].querySelector('.ws-whead-t');
            if (h && h.textContent.indexOf(title) !== -1) return cards[i];
        }
        return null;
    })(title);
    if (!card) return null;
    var h = card.querySelector('.ws-whead-t');
    var m = h.textContent.match(/(\\d{4})/);
    return {year: m ? parseInt(m[1], 10) : null,
            text: h.textContent.trim().split('\\n')[0].slice(0, 80),
            body: card.textContent};
})""", title)


def block_nav_click(page, title, direction):
    return page.evaluate("""(function(a){
    var card = (function(){
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var i = 0; i < cards.length; i++) {
            var h = cards[i].querySelector('.ws-whead-t');
            if (h && h.textContent.indexOf(a.title) !== -1) return cards[i];
        }
        return null;
    })(a);
    if (!card) return 'no-card';
    var btns = card.querySelectorAll('.ws-ynav-btn');
    if (!btns.length) return 'no-nav';
    var el = (a.dir === 'back') ? btns[0] : btns[btns.length - 1];
    if (!el || el.classList.contains('ws-ynav-off')) return 'off';
    el.click();
    return 'ok';
})""", {'title': title, 'dir': direction})


def block_nav_attrs(page, title):
    return page.evaluate("""(function(title){
    var card = (function(){
        var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
        for (var i = 0; i < cards.length; i++) {
            var h = cards[i].querySelector('.ws-whead-t');
            if (h && h.textContent.indexOf(title) !== -1) return cards[i];
        }
        return null;
    })(title);
    if (!card) return [];
    var out = [];
    var btns = card.querySelectorAll('.ws-ynav-btn');
    for (var i = 0; i < btns.length; i++) {
        out.push(btns[i].getAttribute('onclick') || '');
    }
    return out;
})""", title)


# --- JS-хелперы: график расходомера ---
CHART_JS = """(function(){
    var area = document.querySelector('.flow-archive-chart-area');
    if (!area) return null;
    var zone = area.querySelector('.flow-archive-vbar-bar-zone');
    var out = {bars: [], tips: [], zoneH: zone ? zone.getBoundingClientRect().height : 0};
    var cols = area.querySelectorAll('.flow-archive-vbar-col');
    for (var i = 0; i < cols.length; i++) {
        var bar = cols[i].querySelector('.flow-archive-vbar');
        var tip = cols[i].querySelector('.flow-archive-vbar-tip');
        if (bar) {
            var st = bar.getAttribute('style') || '';
            var m = st.match(/height:([\\d.]+)%/);
            var r = bar.getBoundingClientRect();
            out.bars.push({pct: m ? parseFloat(m[1]) : null,
                           px: Math.round(r.height)});
        }
        if (tip) out.tips.push(tip.textContent.trim());
    }
    return out;
})"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== Контекст 1: десктоп 1280 тёмная, Админ =====
        print('=== Контекст 1: десктоп тёмная Админ — Работники ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'edit')
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось',
              page.evaluate("document.title === 'КИПиА'"))

        # --- Task 435: раздельные годы блоков ---
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2200)
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(1500)
        page.click(".ws-wtabs button:has-text('Федосов')")
        page.wait_for_timeout(1000)

        b3y = block_year(page, 'Мероприятия ·')
        b5y = block_year(page, 'Повторные инструктажи')
        check('B1: оба блока — год табеля %d' % Y,
              b3y['year'] == Y and b5y['year'] == Y,
              (b3y['text'], b5y['text']))

        # ‹ в блоке ИНСТРУКТАЖЕЙ → только он меняется
        r = block_nav_click(page, 'Повторные инструктажи', 'back')
        page.wait_for_timeout(700)
        b3y = block_year(page, 'Мероприятия ·')
        b5y = block_year(page, 'Повторные инструктажи')
        check('B2: клик ‹ в инструктажах — год инструктажей %d' % (Y - 1),
              b5y['year'] == Y - 1, b5y['text'])
        check('B3: год мероприятий НЕ тронут (%d)' % Y,
              b3y['year'] == Y, b3y['text'])

        # ‹ снова → минимум инструктажей (%d), запись 2024 видна
        r = block_nav_click(page, 'Повторные инструктажи', 'back')
        page.wait_for_timeout(700)
        b3y = block_year(page, 'Мероприятия ·')
        b5y = block_year(page, 'Повторные инструктажи')
        check('B4: год инструктажей %d (мин)' % (Y - 2),
              b5y['year'] == Y - 2, b5y['text'])
        check('B5: запись инструктажа %d показана' % (Y - 2),
              'промышленной безопасности 2024' in b5y['body'])
        check('B6: год мероприятий по-прежнему %d' % Y,
              b3y['year'] == Y, b3y['text'])
        page.screenshot(path='task435-proof-instr-2024-events-%d.png' % Y,
                        full_page=False)

        # ‹ в блоке МЕРОПРИЯТИЙ → только он меняется
        r = block_nav_click(page, 'Мероприятия ·', 'back')
        page.wait_for_timeout(700)
        b3y = block_year(page, 'Мероприятия ·')
        b5y = block_year(page, 'Повторные инструктажи')
        check('B7: клик ‹ в мероприятиях — год мероприятий %d' % (Y - 1),
              b3y['year'] == Y - 1, b3y['text'])
        check('B8: запись мероприятия %d показана' % (Y - 1),
              'Стажировка на новом оборудовании 2025' in b3y['body'])
        check('B9: блок инструктажей остался на %d (запись 2024)' % (Y - 2),
              b5y['year'] == Y - 2 and
              'промышленной безопасности 2024' in b5y['body'])
        page.screenshot(path='task435-proof-events-%d-instr-%d.png'
                             % (Y - 1, Y - 2), full_page=False)

        # записи не смешиваются
        check('B10: в блоке мероприятий НЕТ записей инструктажей',
              'промышленной безопасности 2024' not in b3y['body'])
        check('B11: в блоке инструктажей НЕТ записей мероприятий',
              'Стажировка на новом' not in b5y['body'])

        # сигнатуры кликов: b3 без третьего аргумента, b5 — с ним
        # (год блока мероприятий = минимум → жива стрелка ›, её клик
        # и проверяем на прежнюю сигнатуру)
        n3 = block_nav_attrs(page, 'Мероприятия ·')
        n5 = block_nav_attrs(page, 'Повторные инструктажи')
        check('B12: клики мероприятий — прежняя сигнатура (без третьего аргумента)',
              any("', 1)" in a for a in n3) and
              not any("', 1, 1)" in a for a in n3) and
              not any("', -1, 1)" in a for a in n3), n3)
        check('B13: клики инструктажей — с третьим аргументом 1',
              any("', -1, 1)" in a for a in n5) or
              any("', 1, 1)" in a for a in n5), n5)

        # › в мероприятиях → возврат к году табеля
        block_nav_click(page, 'Мероприятия ·', 'fwd')
        page.wait_for_timeout(700)
        b3y = block_year(page, 'Мероприятия ·')
        b5y = block_year(page, 'Повторные инструктажи')
        check('B14: › в мероприятиях — год %d, инструктажи не тронуты'
              % Y, b3y['year'] == Y and b5y['year'] == Y - 2,
              (b3y['text'], b5y['text']))
        check('B15: JS-ошибок нет', not js_errors, js_errors[:3])
        ctx.close()

        # ===== Контекст 1b: зритель (view) =====
        print('=== Контекст 1b: десктоп светлая view — навигаторы живы ===')
        global ADMIN
        ADMIN = False
        ctxv = browser.new_context(viewport={'width': 1280, 'height': 900})
        pagev = ctxv.new_page()
        js_errorsv = attach(pagev, ctxv, 'light', 'view')
        pagev.goto('http://127.0.0.1:%d/index.html' % PORT)
        pagev.wait_for_timeout(2500)
        pagev.evaluate("navigateTo('work-schedule')")
        pagev.wait_for_timeout(2200)
        pagev.click('#wsWorkersBtn')
        pagev.wait_for_timeout(1500)
        pagev.click(".ws-wtabs button:has-text('Федосов')")
        pagev.wait_for_timeout(1000)
        rv = block_nav_click(pagev, 'Повторные инструктажи', 'back')
        pagev.wait_for_timeout(700)
        b3yv = block_year(pagev, 'Мероприятия ·')
        b5yv = block_year(pagev, 'Повторные инструктажи')
        check('C1: зритель — год инструктажей сменился (%d)' % (Y - 1),
              b5yv['year'] == Y - 1, b5yv['text'])
        check('C2: зритель — год мероприятий НЕ тронут',
              b3yv['year'] == Y, b3y['text'])
        check('C3: JS-ошибок нет (view)', not js_errorsv, js_errorsv[:3])
        ctxv.close()

        # ===== Контекст 2: десктоп 1280 тёмная — РАСХОДОМЕРЫ =====
        print('=== Контекст 2: десктоп тёмная — график расходомера ===')
        ADMIN = True
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'dark', 'flow')
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('flowmeter-data')")
        page2.wait_for_timeout(1800)
        check('D1: список расходомеров открыт',
              page2.evaluate(
                  "!!document.querySelector('.flow-card, #flowList')"))
        page2.evaluate("FlowmeterData.openDetail(2)")
        page2.wait_for_timeout(1500)
        check('D2: детальная карточка (панель) открыта',
              page2.evaluate(
                  "!!document.querySelector('.flow-archive-chart')"))
        ch = page2.evaluate(CHART_JS)
        check('D3: баров ровно 12', ch and len(ch['bars']) == 12,
              len(ch['bars']) if ch else 'нет графика')
        pcts = [b['pct'] for b in ch['bars']] if ch else []
        # последний бар — новейшая запись = выброс 300
        big = pcts[-1] if pcts else None
        smalls = pcts[:-1] if pcts else []
        check('D4: большой бар (300) ≈ 90% (одиночный — середина 80–100)',
              big is not None and 89 <= big <= 91, big)
        check('D5: малые бары в полосе [5..80]',
              all(5 <= p <= 80 for p in smalls), smalls)
        check('D6: минимальный малый = 5% (пол Task 226)',
              smalls and abs(min(smalls) - 5) < 0.2, min(smalls) if smalls else None)
        check('D7: максимальный малый = 80% (граница полос)',
              smalls and abs(max(smalls) - 80) < 0.2, max(smalls) if smalls else None)
        check('D8: НИ ОДНОГО бара ниже 5%',
              all(p >= 5 for p in pcts), pcts)
        check('D9: тултипы — фактические значения (300 есть, 90% нет)',
              ch and '300' in ' '.join(ch['tips']) and
              not any('90' == t.replace(',', '.')
                      for t in ch['tips']), ch['tips'][:4] if ch else None)
        page2.screenshot(path='task436-proof-flow-chart-outlier.png',
                        full_page=False)
        check('D10: JS-ошибок нет', not js_errors2, js_errors2[:3])
        ctx2.close()

        # ===== Контекст 3: мобайл 375 светлая — расходомер =====
        print('=== Контекст 3: мобайл 375 — полная страница расходомера ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 720})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'light', 'mob')
        page3.goto('http://127.0.0.1:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('flowmeter-data')")
        page3.wait_for_timeout(1800)
        page3.evaluate("FlowmeterData.openDetail(2)")
        page3.wait_for_timeout(1500)
        ch3 = page3.evaluate(CHART_JS)
        pcts3 = [b['pct'] for b in ch3['bars']] if ch3 else []
        check('E1: мобайл — график построен (12 баров)',
              len(pcts3) == 12, len(pcts3))
        check('E2: мобайл — большой ≈ 90%, малые ≤ 80%',
              pcts3 and 89 <= pcts3[-1] <= 91 and
              all(p <= 80 for p in pcts3[:-1]), pcts3)
        check('E3: мобайл — горизонтального переполнения нет',
              page3.evaluate(
                  'document.documentElement.scrollWidth <= 376'))
        page3.screenshot(path='task436-proof-flow-chart-mobile.png',
                         full_page=False)
        check('E4: JS-ошибок нет (мобайл)', not js_errors3, js_errors3[:3])
        ctx3.close()

        browser.close()

    print('\n===== ИТОГ: %d passed, %d failed =====' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    os.chdir('/home/z/my-project/kip8test')

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass
    httpd = HTTPServer(('127.0.0.1', PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        main()
    finally:
        httpd.shutdown()
