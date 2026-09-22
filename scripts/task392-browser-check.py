#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 392: browser-check — заявка (2 части):
#   (1) «Работников на текущий момент 6 (2 мастера, 2 дневных,
#       2 сменных).» — ведущее число БЕЗ СКОБОК (заявка: «12 без
#       скобок»); старого формата «(6) (» нет;
#   (2) раздел «СИЗ» — лист «СИЗ» табель_КИП_ИОС: секция в карточке
#       работника (записи с мета-строкой «выдано … · срок … ·
#       до …», ✎/✕, «+ СИЗ…»), шторка «Новое СИЗ»/«Правка СИЗ»
#       с АВТО-датой окончания (выдача + срок), добавление/правка/
#       удаление через сервер listPpe/addPpe/updatePpe/deletePpe.
# МОК: 6 работников (2 мастера, 2 дневных, 2 сменных); СИЗ:
#   Иванов (017): костюм (выдан 17.08.2026, 1 год, до 17.08.2027)
#   + очки закрытые (До износа); Петров (023): ботинки (1,5 года).
# ДЕСКТОП 1280 (тёмная, Админ): A загрузка; B табель; C «Работники»
#   (C1-C3 строка без скобок); D карточка Иванова (D1-D5 секция СИЗ);
#   E шторка (E1-E6: режимы/префилл/datalist/сроки/авто-дата);
#   F добавление (addPpe, тост, запись в карточке); G правка
#   (updatePpe с id); H удаление (kipConfirm → deletePpe);
#   I 0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ): M1-M3 секция СИЗ + шторка в границах;
#   N 0 JS-ошибок.
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

# СИЗ (лист «СИЗ» табель_КИП_ИОС): образец файла «Таблица СИЗ
# работникам КИП ИОС.xlsx» — Иванову выдан костюм (1 год) и очки
# (До износа); Петрову — ботинки (1,5 года)
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
  {'id': 3, 'таб_номер': '023', 'работник': 'Петров П. П.',
   'должность': 'Инженер КИПиА', 'наименование': 'Ботинки',
   'дата_выдачи': '2026-08-17', 'срок_годности': '1,5 года',
   'дата_окончания': '2028-02-17', 'примечание': ''},
]
API_CALLS = []   # [{action, body}] — addPpe/updatePpe/deletePpe

def ppe_add(rec):
    PPE_STATE.append(rec)

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
        API_CALLS.append({'action': action, 'body': body})
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
                body=json.dumps({'ok': True, 'data': {'trainings': []}}, ensure_ascii=False))
        if action == 'workSchedule.listVacations':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'vacations': []}}, ensure_ascii=False))
        if action == 'workSchedule.listPpe':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ppe': PPE_STATE}}, ensure_ascii=False))
        if action == 'workSchedule.listEntries':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'entries': []}}, ensure_ascii=False))
        if action == 'workSchedule.addPpe':
            new_id = max([r['id'] for r in PPE_STATE] + [0]) + 1
            ppe_add({'id': new_id, 'таб_номер': body.get('таб_номер', ''),
                     'работник': '', 'должность': '',
                     'наименование': body.get('наименование', ''),
                     'дата_выдачи': body.get('дата_выдачи', ''),
                     'срок_годности': body.get('срок_годности', ''),
                     'дата_окончания': '', 'примечание': body.get('примечание', '')})
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'id': new_id}}, ensure_ascii=False))
        if action == 'workSchedule.updatePpe':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'id': body.get('id')}}, ensure_ascii=False))
        if action == 'workSchedule.deletePpe':
            rid = body.get('id') if body else None
            PPE_STATE[:] = [r for r in PPE_STATE if r['id'] != rid]
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'id': rid}}, ensure_ascii=False))
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
                      body='not found (t392-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t392-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

def api_calls_of(action):
    return [c for c in API_CALLS if c['action'] == action]

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
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

    # ---------- C: «Работники» — строка текущего момента БЕЗ СКОБОК ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    w = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var txt = body ? (body.textContent || '') : '';
        return {
            staff: txt.indexOf('Работников по штату 14 (2 мастера, 7 дневных, 5 сменных).') !== -1,
            cur: txt.indexOf('Работников на текущий момент 6 (2 мастера, 2 дневных, 2 сменных).') !== -1,
            oldParens: txt.indexOf('Работников на текущий момент (6)') !== -1,
            bodyTxt: txt.slice(0, 200)
        };
    })()""")
    check('C1: «Работников по штату 14 (2 мастера, 7 дневных, 5 сменных).»',
          w['staff'], w['bodyTxt'])
    check('C2: «Работников на текущий момент 6 (2 мастера, 2 дневных, 2 сменных).» — 6 БЕЗ СКОБОК',
          w['cur'], w['bodyTxt'])
    check('C3: старого формата «(6) (…» НЕТ', not w['oldParens'])

    # ---------- D: карточка Иванова — секция СИЗ ----------
    page.click('button[title="Иванов И. И."]')
    page.wait_for_timeout(800)
    c = page.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var txt = body ? (body.textContent || '') : '';
        var items = body ? body.querySelectorAll('.ws-ppe-item') : [];
        var acts = body ? body.querySelectorAll('.ws-ppe-item .ws-popup-act') : [];
        var add = body ? body.querySelector('.ws-emp-addppe') : null;
        return {
            sec: txt.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
            kostum: txt.indexOf('Костюм для защиты от растворов кислот и щелочей') !== -1,
            issued: txt.indexOf('выдано 17.08.2026') !== -1,
            term: txt.indexOf('срок 1 год') !== -1,
            till: txt.indexOf('до 17.08.2027') !== -1,
            ochki: txt.indexOf('Очки закрытые') !== -1,
            doIznosa: txt.indexOf('срок До износа') !== -1,
            botinki: txt.indexOf('Ботинки') === -1,
            n: items.length, acts: acts.length,
            addTxt: add ? add.textContent.trim() : null,
            cardTxt: txt.slice(0, 300)
        };
    })()""")
    check('D1: секция «СИЗ · средства индивидуальной защиты» в карточке', c['sec'],
          c['cardTxt'])
    check('D2: запись «Костюм…» с мета-строкой (выдано 17.08.2026 · срок 1 год · до 17.08.2027)',
          c['kostum'] and c['issued'] and c['term'] and c['till'],
          c['cardTxt'])
    check('D3: «Очки закрытые» — срок «До износа»; чужих записей (ботинки) нет',
          c['ochki'] and c['doIznosa'] and c['botinki'], c['cardTxt'])
    check('D4: 2 записи, 4 кнопки ✎/✕', c['n'] == 2 and c['acts'] == 4,
          (c['n'], c['acts']))
    check('D5: строка «+ СИЗ…» у редактора', c['addTxt'] == '+ СИЗ…', c['addTxt'])
    page.screenshot(path='/tmp/t392-proof-card-siz.png', full_page=False)

    # ---------- E: шторка «Новое СИЗ» ----------
    page.click('.ws-emp-addppe')
    page.wait_for_timeout(700)
    e = page.evaluate("""(function(){
        var dl = document.getElementById('wsPpeNameList');
        var dlN = dl ? dl.querySelectorAll('option').length : 0;
        var term = document.getElementById('wsPpeTerm');
        var termN = term ? term.querySelectorAll('option').length : 0;
        return {
            open: document.getElementById('wsPpeSheet').classList.contains('active'),
            title: document.getElementById('wsPpeSheetTitle').textContent,
            submit: document.getElementById('wsPpeSubmitBtn').textContent,
            tabNo: document.getElementById('wsPpeTabNo').value,
            dlN: dlN, termN: termN,
            hint: document.getElementById('wsPpeExpiryInfo').textContent
        };
    })()""")
    check('E1: шторка открыта, заголовок «Новое СИЗ», кнопка «Добавить»',
          e['open'] and e['title'] == 'Новое СИЗ' and e['submit'] == 'Добавить', e)
    check('E2: работник карточки ПРЕФИЛЛЕН (017)', e['tabNo'] == '017', e['tabNo'])
    check('E3: datalist — 8 стандартных позиций', e['dlN'] == 8, e['dlN'])
    check('E4: select срока — 7 опций (—/6 мес./1 год/1,5/2/3/До износа)',
          e['termN'] == 7, e['termN'])
    # авто-дата окончания: выдача 17.08.2026 + 1 год → 17.08.2027
    page.fill('#wsPpeName', 'Каска защитная')
    page.fill('#wsPpeIssued', '2026-08-17')
    page.select_option('#wsPpeTerm', '1 год')
    page.wait_for_timeout(300)
    hint = page.evaluate("document.getElementById('wsPpeExpiryInfo').textContent")
    check('E5: авто-дата окончания «17.08.2027 (заполнится автоматически)»',
          '17.08.2027' in hint and 'автоматически' in hint, hint)
    page.select_option('#wsPpeTerm', 'До износа')
    page.wait_for_timeout(300)
    hint2 = page.evaluate("document.getElementById('wsPpeExpiryInfo').textContent")
    check('E6: «До износа» → «Дата окончания срока годности: До износа»',
          'До износа' in hint2, hint2)
    page.screenshot(path='/tmp/t392-proof-ppe-sheet.png', full_page=False)

    # ---------- F: добавление СИЗ ----------
    page.select_option('#wsPpeTerm', '2 года')
    page.fill('#wsPpeComment', 'До износа')
    n_add_before = len(api_calls_of('workSchedule.addPpe'))
    page.click('#wsPpeSubmitBtn')
    page.wait_for_timeout(1500)
    adds = api_calls_of('workSchedule.addPpe')
    check('F1: addPpe вызван с payload (наименование/дата/срок/примечание)',
          len(adds) == n_add_before + 1 and
          adds[-1]['body'].get('наименование') == 'Каска защитная' and
          adds[-1]['body'].get('дата_выдачи') == '2026-08-17' and
          adds[-1]['body'].get('срок_годности') == '2 года' and
          adds[-1]['body'].get('примечание') == 'До износа' and
          adds[-1]['body'].get('таб_номер') == '017',
          adds[-1]['body'] if adds else None)
    f = page.evaluate("""(function(){
        return {
            sheetOpen: document.getElementById('wsPpeSheet').classList.contains('active'),
            kaska: (document.getElementById('wsWorkersBody').textContent || '')
                .indexOf('Каска защитная') !== -1,
            items: document.querySelectorAll('#wsWorkersBody .ws-ppe-item').length
        };
    })()""")
    check('F2: шторка закрыта, запись «Каска защитная» в карточке (3 записи)',
          not f['sheetOpen'] and f['kaska'] and f['items'] == 3, f)

    # ---------- G: правка записи (✎) ----------
    page.locator('.ws-ppe-item .ws-popup-act[title="Редактировать запись СИЗ"]').first.click()
    page.wait_for_timeout(700)
    g = page.evaluate("""(function(){
        return {
            title: document.getElementById('wsPpeSheetTitle').textContent,
            submit: document.getElementById('wsPpeSubmitBtn').textContent,
            name: document.getElementById('wsPpeName').value,
            issued: document.getElementById('wsPpeIssued').value,
            term: document.getElementById('wsPpeTerm').value,
            comment: document.getElementById('wsPpeComment').value
        };
    })()""")
    check('G1: режим ПРАВКИ — «Правка СИЗ»/«Сохранить», поля префиллены',
          g['title'] == 'Правка СИЗ' and g['submit'] == 'Сохранить' and
          'Костюм' in g['name'] and g['issued'] == '2026-08-17' and
          g['term'] == '1 год', g)
    page.fill('#wsPpeComment', 'правка комментария')
    page.click('#wsPpeSubmitBtn')
    page.wait_for_timeout(1500)
    upd = api_calls_of('workSchedule.updatePpe')
    check('G2: updatePpe с id=1 и новым примечанием',
          len(upd) >= 1 and upd[-1]['body'].get('id') == 1 and
          upd[-1]['body'].get('примечание') == 'правка комментария',
          upd[-1]['body'] if upd else None)

    # ---------- H: удаление записи (✕ → kipConfirm) ----------
    n_del_before = len(api_calls_of('workSchedule.deletePpe'))
    page.locator('.ws-ppe-item .ws-popup-act-del[title="Удалить запись СИЗ"]').first.click()
    page.wait_for_timeout(500)
    check('H1: kipConfirm открыт',
          page.evaluate("!!document.querySelector('.kip-dialog')"))
    page.screenshot(path='/tmp/t392-proof-confirm.png', full_page=False)
    page.click('.kip-dialog-ok')
    page.wait_for_timeout(1500)
    dels = api_calls_of('workSchedule.deletePpe')
    h = page.evaluate("""(function(){
        return {
            items: document.querySelectorAll('#wsWorkersBody .ws-ppe-item').length,
            kostum: (document.getElementById('wsWorkersBody').textContent || '')
                .indexOf('Костюм') === -1
        };
    })()""")
    check('H2: deletePpe вызван с id=1',
          len(dels) == n_del_before + 1 and dels[-1]['body'].get('id') == 1,
          dels[-1]['body'] if dels else None)
    check('H3: запись исчезла из карточки (осталось 2)', h['items'] == 2, h)

    check('I: 0 JS-ошибок (десктоп тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, светлая, Админ =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 700})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'mob')

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('#wsWorkersBtn')
    page2.wait_for_timeout(1000)
    m = page2.evaluate("""(function(){
        var txt = document.getElementById('wsWorkersBody').textContent || '';
        return { cur: txt.indexOf('Работников на текущий момент 6 (2 мастера, 2 дневных, 2 сменных).') !== -1 };
    })()""")
    check('M1: мобайл — строка текущего момента без скобок вокруг 6', m['cur'])
    page2.click('button[title="Иванов И. И."]')
    page2.wait_for_timeout(800)
    # (десктоп-контекст выше удалил «Костюм» из МОКА — здесь живёт
    # «Очки закрытые» и добавленная «Каска защитная»)
    m2 = page2.evaluate("""(function(){
        var body = document.getElementById('wsWorkersBody');
        var txt = body ? (body.textContent || '') : '';
        return { sec: txt.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
                 ochki: txt.indexOf('Очки закрытые') !== -1,
                 items: body ? body.querySelectorAll('.ws-ppe-item').length : 0 };
    })()""")
    check('M2: мобайл — секция СИЗ в карточке с записями',
          m2['sec'] and m2['ochki'] and m2['items'] >= 1, m2)
    page2.click('.ws-emp-addppe')
    page2.wait_for_timeout(700)
    m3 = page2.evaluate("""(function(){
        var sheet = document.getElementById('wsPpeSheet');
        var r = sheet.getBoundingClientRect();
        return { open: sheet.classList.contains('active'),
                 inView: r.left >= 0 && r.right <= 375 && r.width > 0 };
    })()""")
    check('M3: мобайл — шторка «Новое СИЗ» в границах экрана',
          m3['open'] and m3['inView'], m3)
    page2.screenshot(path='/tmp/t392-proof-mobile-sheet.png', full_page=False)
    check('N: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print('=' * 60)
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
