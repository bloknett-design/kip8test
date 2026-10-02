#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 461: browser-check — заявка: «В разделе Работники в форме
# добавления СИЗ, выпадающий список наименования СИЗ должен
# формироваться автоматически в зависимости от содержания столбца
# "наименование_СИЗ" расположенного на листе "СИЗ" файла
# табель_КИП_ИОС. То есть из всего списка наименования СИЗ в столбце
# "наименование_СИЗ", в выпадающем списке формы должны перечислятся
# все разные СИЗ, но естественно в одном наименовании, без
# повторения.»
# КОНТЕКСТ (мок-сервер, порт 8955): десктоп 1280 тёмная, Админ:
#   A: приложение + график;
#   B: «Работники» → карточка → «+ СИЗ…»: datalist #wsPpeNameList —
#      ДИНАМИЧЕСКИЙ: 9 записей листа с повторами (каска ×3 у двух
#      работников, перчатки в двух регистрах, ботинки с пробелами,
#      пустое имя) → РОВНО 5 уникальных наименований, по алфавиту,
#      без повторов; ввод «ка» — нативный дропдаун с подсказками;
#   C: правка ✎ — datalist тот же динамический, имя записи
#      префиллено и не затёрто;
#   D: добавление «Костюм для защиты от растворов кислот и
#      щелочей» → после loadGrid повторное открытие — 6 наименований,
#      новое НА СВОЁМ МЕСТЕ по алфавиту (после «Каска защитная»);
#   E: ПУСТОЙ лист «СИЗ» (listPpe → []) — datalist НЕ тронут:
#      статичный запасной набор из 8 позиций образца (Task 392);
#   F: мобайл 375 — шторка в границах, datalist динамический (5);
#   G: 0 JS-ошибок; скриншоты в download/kip8test-task461/.
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8955
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0872', 'ФИО': 'Галкин Д. Н.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': '', 'старт_цикла': '',
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'группа_допуска': 'IV',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]


def fresh_entries():
    out = []
    dim = (datetime.date(TODAY.year, TODAY.month % 12 + 1, 1) -
           datetime.timedelta(days=1)).day
    for day in range(1, dim + 1):
        iso_ = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, day)
        if day <= 5:
            out.append({'дата': iso_, 'таб_номер': '0871', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
    return out


ENTRIES = fresh_entries()
INSTR = []
INSTR_LIST = []

# Лист «СИЗ» с ПОВТОРАМИ (заявка): каска у ТРЁХ записей двух
# работников, перчатки в двух написаниях (регистр), ботинки с
# пробелами, очки/противогаз по одному, пустое наименование.
# Уникальных — РОВНО 5: Ботинки, Каска защитная, Очки закрытые,
# Перчатки нитриловые, Противогаз (по алфавиту ru).
PPE_STATE = [
  {'id': 11, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Каска защитная',
   'дата_выдачи': '2026-08-17', 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': '2028-08-17',
   'примечание': ''},
  {'id': 12, 'таб_номер': '0872', 'работник': 'Галкин Д. Н.',
   'должность': 'Мастер КИПиА', 'наименование': 'Каска защитная',
   'дата_выдачи': '2026-06-01', 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': '2028-06-01',
   'примечание': ''},
  {'id': 13, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Каска защитная',
   'дата_выдачи': '2025-03-10', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': 'старая, списана'},
  {'id': 14, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Перчатки нитриловые',
   'дата_выдачи': '2026-09-01', 'дата_изготовления': '',
   'срок_годности': '1 год', 'дата_окончания': '2027-09-01',
   'примечание': ''},
  {'id': 15, 'таб_номер': '0872', 'работник': 'Галкин Д. Н.',
   'должность': 'Мастер КИПиА', 'наименование': 'перчатки нитриловые',
   'дата_выдачи': '2026-09-05', 'дата_изготовления': '',
   'срок_годности': '1 год', 'дата_окончания': '2027-09-05',
   'примечание': ''},
  {'id': 16, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': '  Ботинки  ',
   'дата_выдачи': '2026-02-11', 'дата_изготовления': '',
   'срок_годности': '1 год', 'дата_окончания': '2027-02-11',
   'примечание': ''},
  {'id': 17, 'таб_номер': '0872', 'работник': 'Галкин Д. Н.',
   'должность': 'Мастер КИПиА', 'наименование': 'Очки закрытые',
   'дата_выдачи': '2026-04-14', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
  {'id': 18, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Противогаз',
   'дата_выдачи': '2026-01-20', 'дата_изготовления': '2025-01-15',
   'срок_годности': '3 года', 'дата_окончания': '2028-01-15',
   'примечание': ''},
  {'id': 19, 'таб_номер': '0872', 'работник': 'Галкин Д. Н.',
   'должность': 'Мастер КИПиА', 'наименование': '',
   'дата_выдачи': '', 'дата_изготовления': '',
   'срок_годности': '', 'дата_окончания': '', 'примечание': ''},
]

# режим листа «СИЗ»: 'data' (9 записей) / 'empty' (запасной набор)
PPE_MODE = 'data'

API_CALLS = []

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/kip8test-task461'
os.makedirs(SHOTS, exist_ok=True)

EXPECTED_DYNAMIC = ['Ботинки', 'Каска защитная', 'Очки закрытые',
                    'Перчатки нитриловые', 'Противогаз']
EXPECTED_STATIC = ['Костюм для защиты от растворов кислот и щелочей',
                   'Ботинки', 'Белье нательное', 'Куртка утеплённая',
                   'Каска защитная', 'Подшлемник', 'Противогаз',
                   'Очки закрытые']


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def term_months(term):
    s = str(term or '').strip().lower().replace(',', '.')
    if not s:
        return None
    if 'до износа' in s:
        return -1
    import re as _re
    m = _re.match(r'^(\d+(?:\.\d+)?)\s*(мес|год|л)', s)
    if not m:
        return None
    n = float(m.group(1))
    if m.group(2) == 'мес':
        return int(round(n))
    return int(round(n * 12))


def ppe_expiry(body):
    months = term_months(body.get('срок_годности'))
    if months == -1:
        return 'До износа'
    if not months:
        return ''
    base = str(body.get('дата_изготовления') or '') or \
           str(body.get('дата_выдачи') or '')
    if not base:
        return ''
    try:
        y, m, d = (int(x) for x in base.split('-'))
    except ValueError:
        return ''
    mo = m - 1 + months
    last = (datetime.date(y + mo // 12, mo % 12 + 1, 1) -
            datetime.timedelta(days=1)).day
    if d > last:
        d = last
    return '%04d-%02d-%02d' % (y + mo // 12, mo % 12 + 1, d)


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': True,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': [], 'instrList': [],
                                     'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        # режим листа: 'empty' → пустой лист (запасной набор datalist)
        ppe = [] if PPE_MODE == 'empty' else [dict(r) for r in PPE_STATE]
        return {'ok': True, 'data': {'ppe': ppe}}
    if action == 'workSchedule.addPpe':
        new_id = max((int(r['id']) for r in PPE_STATE), default=0) + 1
        emp = next((e for e in EMPLOYEES
                    if e['таб_номер'] == body.get('таб_номер')), EMPLOYEES[0])
        rec = {'id': new_id, 'таб_номер': body.get('таб_номер', ''),
               'работник': emp['ФИО'], 'должность': emp['должность'],
               'наименование': body.get('наименование', ''),
               'дата_выдачи': body.get('дата_выдачи', ''),
               'дата_изготовления': body.get('дата_изготовления', ''),
               'срок_годности': body.get('срок_годности', ''),
               'дата_окончания': ppe_expiry(body),
               'примечание': body.get('примечание', '')}
        PPE_STATE.append(rec)
        return {'ok': True, 'data': {'id': new_id}}
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
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t461-%s');" % tag +
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
        if body is None:
            body = {}
        if action.startswith('workSchedule.'):
            API_CALLS.append({'action': action, 'body': body})
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t461-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


DATALIST_JS = """(function(){
    var sheet = document.getElementById('wsPpeSheet');
    var dl = document.getElementById('wsPpeNameList');
    var opts = dl ? dl.querySelectorAll('option') : [];
    var vals = [];
    for (var i = 0; i < opts.length; i++)
        vals.push(opts[i].value !== undefined ? opts[i].value
                                               : (opts[i].getAttribute('value') || ''));
    return {
        open: sheet.classList.contains('active'),
        vals: vals,
        input: document.getElementById('wsPpeName').value
    };
})"""


def open_workers_card(page):
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(900)
    page.click('button[title="Федосов А. В."]')
    page.wait_for_timeout(900)


def main():
    global PPE_MODE
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ =====
        print('=== Контекст: десктоп тёмная — динамический datalist СИЗ ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось, график открыт',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))

        # ---------- B: «+ СИЗ…» — динамический datalist ----------
        open_workers_card(page)
        page.click('.ws-emp-addppe')
        page.wait_for_timeout(700)
        b = page.evaluate(DATALIST_JS)
        check('B1: шторка «Новое СИЗ» открыта', b['open'])
        check('B2: datalist ДИНАМИЧЕСКИЙ: 9 записей с повторами → '
              'РОВНО 5 уникальных наименований',
              len(b['vals']) == 5, b['vals'])
        check('B3: все разные СИЗ, БЕЗ повторения (заявка)',
              b['vals'] == EXPECTED_DYNAMIC,
              b['vals'])
        kas = b['vals'].count('Каска защитная')
        per = sum(1 for v in b['vals'] if v.lower() == 'перчатки нитриловые')
        check('B4: каска ×3 записи → одна строка; перчатки в 2 регистрах → одна',
              kas == 1 and per == 1, (kas, per, b['vals']))
        check('B5: пробелы обрезаны («  Ботинки  » → «Ботинки»), '
              'пустое имя не попало',
              'Ботинки' in b['vals'] and
              all(v == v.strip() and v for v in b['vals']), b['vals'])
        check('B6: сортировка по алфавиту',
              b['vals'] == sorted(b['vals'],
                                  key=lambda x: x.lower()), b['vals'])
        page.screenshot(path=SHOTS + '/01-ppe-form.png')

        # нативный дропдаун: ввод «ка» — Chromium покажет подсказки
        page.fill('#wsPpeName', 'ка')
        page.wait_for_timeout(600)
        page.screenshot(path=SHOTS + '/02-datalist-dropdown.png')
        check('B7: ввод «ка» — в datalist есть подходящие «Каска защитная»',
              any('Каска' in v for v in b['vals']), b['vals'])

        # ---------- C: правка ✎ — datalist тот же ----------
        page.click('#wsPpeSheet button.flow-input-cancel')
        page.wait_for_timeout(500)
        page.locator('.ws-ppe-item .ws-popup-act'
                     '[title="Редактировать запись СИЗ"]').first.click()
        page.wait_for_timeout(800)
        c = page.evaluate(DATALIST_JS)
        check('C1: правка открыта, datalist тоже динамический (5)',
              c['open'] and len(c['vals']) == 5, c['vals'])
        check('C2: имя записи префиллено и НЕ затёрто подсказками',
              c['input'] == 'Каска защитная', c['input'])
        page.screenshot(path=SHOTS + '/03-edit-datalist.png')
        page.click('#wsPpeSheet button.flow-input-cancel')
        page.wait_for_timeout(500)

        # ---------- D: добавление нового имени → datalist обновится ----------
        page.click('.ws-emp-addppe')
        page.wait_for_timeout(700)
        page.fill('#wsPpeName', 'Костюм для защиты от растворов кислот и щелочей')
        page.select_option('#wsPpeTerm', '1 год')
        page.click('#wsPpeSubmitBtn')
        page.wait_for_timeout(1800)
        d0 = page.evaluate("""(function(){
            var body = document.getElementById('wsWorkersBody');
            var txt = body ? (body.textContent || '') : '';
            return { kostyum: txt.indexOf('Костюм для защиты') !== -1,
                     addppe: !!document.querySelector('.ws-emp-addppe') };
        })()""")
        check('D1: запись добавлена, карточка жива (после loadGrid)',
              d0['kostyum'] and d0['addppe'], d0)
        page.click('.ws-emp-addppe')
        page.wait_for_timeout(700)
        d = page.evaluate(DATALIST_JS)
        exp = sorted(EXPECTED_DYNAMIC + ['Костюм для защиты от растворов кислот'
                                         ' и щелочей'],
                     key=lambda x: x.lower())
        check('D2: после добавления — 6 уникальных наименований '
              '(listPpe перечитан)',
              d['open'] and len(d['vals']) == 6, d['vals'])
        check('D3: новое наименование в списке, порядок алфавитный',
              d['vals'] == exp, (d['vals'], exp))
        page.screenshot(path=SHOTS + '/04-after-add-reopen.png')
        check('G1: 0 JS-ошибок (десктоп)', js_errors == [], js_errors[:3])
        ctx.close()

        # ===== E: ПУСТОЙ лист «СИЗ» — запасной статичный набор =====
        print('=== Контекст: пустой лист «СИЗ» — запасной набор datalist ===')
        PPE_MODE = 'empty'
        ctx3 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'dark', 'empty')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2200)
        open_workers_card(page3)
        page3.click('.ws-emp-addppe')
        page3.wait_for_timeout(700)
        e = page3.evaluate(DATALIST_JS)
        check('E1: пустой лист — шторка открыта, datalist НЕ тронут: '
              'статичный запасной набор из 8 позиций образца',
              e['open'] and e['vals'] == EXPECTED_STATIC, e['vals'])
        check('E2: «нет выданных СИЗ» в карточке (лист пуст)',
              page3.evaluate("(function(){var t = document.getElementById(" +
              "'wsWorkersBody').textContent || ''; return t.indexOf(" +
              "'нет выданных СИЗ') !== -1;})()"))
        page3.screenshot(path=SHOTS + '/05-fallback-static.png')
        check('G2: 0 JS-ошибок (пустой лист)', js_errors3 == [], js_errors3[:3])
        ctx3.close()

        # ===== F: мобайл 375 — шторка + динамический datalist =====
        print('=== Контекст: мобайл 375 — динамический datalist ===')
        PPE_MODE = 'data'
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'dark', 'mobile')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2200)
        open_workers_card(page2)
        page2.click('.ws-emp-addppe')
        page2.wait_for_timeout(700)
        m = page2.evaluate("""(function(){
            var sheet = document.getElementById('wsPpeSheet');
            var r = sheet.getBoundingClientRect();
            var dl = document.getElementById('wsPpeNameList');
            var opts = dl ? dl.querySelectorAll('option') : [];
            var vals = [];
            for (var i = 0; i < opts.length; i++) vals.push(opts[i].value);
            return { open: sheet.classList.contains('active'),
                     inView: r.left >= -1 && r.right <= 376 && r.width > 0,
                     vals: vals };
        })()""")
        # ожидание — из ТЕКУЩЕГО состояния мока (после добавления
        # «Костюма…» в шаге D лист уже содержит 6 уникальных имён);
        # дедупликация как в приложении: первое встреченное написание
        first_seen = {}
        for r in PPE_STATE:
            n = str(r['наименование']).strip()
            if n and n.lower() not in first_seen:
                first_seen[n.lower()] = n
        expected_now = sorted(first_seen.values(), key=lambda x: x.lower())
        check('F1: мобайл — шторка открыта в границах экрана',
              m['open'] and m['inView'], m)
        check('F2: мобайл — datalist динамический (%d наименований)'
              % len(expected_now),
              m['vals'] == expected_now, (m['vals'], expected_now))
        page2.screenshot(path=SHOTS + '/06-mobile-form.png')
        check('G3: 0 JS-ошибок (мобайл)', js_errors2 == [], js_errors2[:3])
        ctx2.close()
        browser.close()

    print('\n===== ИТОГ: %d OK / %d FAIL =====' % (PASS, FAIL))
    return 1 if FAIL else 0


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
