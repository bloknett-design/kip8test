#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443: browser-check — заявка: «В таблице СИЗ создать новый
# столбец "дата_изготовления" справа от "дата_выдачи"; дата
# окончания = изготовление + срок (приоритет), иначе выдача + срок;
# дата выдачи в этом случае — только информация».
# КОНТЕКСТ (мок-сервер, порт 8945): десктоп 1280 тёмная, Админ:
#   A: приложение + график;
#   B: «Работники» → карточка: «изгот. 15.01.2025» в мета-строке
#      записи с датой изготовления (после «выдано …»), записи без
#      даты изготовления — без «изгот.», «не выдано»/«До износа»;
#   C: шторка «+ СИЗ…»: поле «Дата изготовления» (label, date),
#      порядок полей выдача → изготовление → срок, подсказка с
#      формулировкой приоритета, ЖИВАЯ авто-дата: mfg+срок при
#      наличии mfg (пометка «от даты изготовления»), от выдачи при
#      отсутствии, «До износа»;
#   D: добавление — addPpe payload с дата_изготовления, запись в
#      карточке с «изгот.» (мок мутабельный);
#   E: правка ✎ — префилл даты изготовления, hint приоритета,
#      очистка → updatePpe с дата_изготовления='';
#   F: мобайл 375 — шторка с полем в границах экрана;
#   G: 0 JS-ошибок; скриншоты в download/screenshots-task443/.
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8945
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#90CAF9', 'short': 'инструктаж'},
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
INSTR = [
    {'id': 600, 'таб_номер': '0871', 'тип': 'инструктаж',
     'тема': 'Повторный инструктаж по охране труда',
     'дата_начала': TODAY_ISO, 'дата_окончания': TODAY_ISO,
     'длительность_дней': 1, 'комментарий': '',
     'дата_проведения': TODAY_ISO, 'выполнение': 1, 'просрочен': 0},
]
INSTR_LIST = [
  {'название': 'Повторный инструктаж по охране труда', 'вид': 'инструктаж',
   'периодичность': 6, 'основание': '', 'сокращение': 'Инстр. ОТ'},
]

# СИЗ (Task 443): коробка противогаза — дата изготовления задана
# (окончание = изготовление + срок, дата выдачи — информационная);
# каска — БЕЗ даты изготовления (окончание = выдача + срок);
# очки — «До износа»
PPE_STATE = [
  {'id': 11, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд',
   'наименование': 'Фильтрующая коробка противогаза',
   'дата_выдачи': '2026-08-17', 'дата_изготовления': '2025-01-15',
   'срок_годности': '2 года', 'дата_окончания': '2027-01-15',
   'примечание': 'банка №2'},
  {'id': 12, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Каска защитная',
   'дата_выдачи': '2026-08-17', 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': '2028-08-17',
   'примечание': ''},
  {'id': 13, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
]
API_CALLS = []   # [{action, body}]


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
    """Task 443: ПРИОРИТЕТ даты изготовления; иначе дата выдачи."""
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


PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task443'
os.makedirs(SHOTS, exist_ok=True)


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


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
        return {'ok': True, 'data': {
            'trainings': [dict(r) for r in INSTR],
            'instrList': [dict(x) for x in INSTR_LIST],
            'instrAll': [dict(r) for r in INSTR], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': [dict(r) for r in PPE_STATE]}}
    if action == 'workSchedule.addPpe':
        # мок-сервер считает дату окончания с ПРИОРИТЕТОМ
        # изготовления (зеркало логики Task 443)
        new_id = max((int(r['id']) for r in PPE_STATE), default=0) + 1
        rec = {'id': new_id, 'таб_номер': body.get('таб_номер', ''),
               'работник': EMPLOYEES[0]['ФИО'],
               'должность': EMPLOYEES[0]['должность'],
               'наименование': body.get('наименование', ''),
               'дата_выдачи': body.get('дата_выдачи', ''),
               'дата_изготовления': body.get('дата_изготовления', ''),
               'срок_годности': body.get('срок_годности', ''),
               'дата_окончания': ppe_expiry(body),
               'примечание': body.get('примечание', '')}
        PPE_STATE.append(rec)
        return {'ok': True, 'data': {'id': new_id}}
    if action == 'workSchedule.updatePpe':
        uid = int(body.get('id', 0))
        for r in PPE_STATE:
            if int(r['id']) == uid:
                r.update({
                    'наименование': body.get('наименование', r['наименование']),
                    'дата_выдачи': body.get('дата_выдачи', ''),
                    'дата_изготовления': body.get('дата_изготовления', ''),
                    'срок_годности': body.get('срок_годности', ''),
                    'дата_окончания': ppe_expiry(body),
                    'примечание': body.get('примечание', ''),
                })
                break
        return {'ok': True, 'data': {'id': uid}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in ENTRIES]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def api_calls_of(action):
    return [c for c in API_CALLS if c['action'] == action]


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t443-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        # приложение шлёт POST с JSON-телом (как в 392)
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
                      body='not found (t443-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


CARD_PPE_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    var txt = body ? (body.textContent || '') : '';
    var items = body ? body.querySelectorAll('.ws-ppe-item') : [];
    var metas = [];
    for (var i = 0; i < items.length; i++) {
        var m = items[i].querySelector('.ws-ppe-meta');
        metas.push(m ? m.textContent : '');
    }
    return {
        sec: txt.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
        korobka: txt.indexOf('Фильтрующая коробка противогаза') !== -1,
        izgot: txt.indexOf('изгот. 15.01.2025') !== -1,
        meta0: metas[0] || '', meta1: metas[1] || '', meta2: metas[2] || '',
        n: items.length,
        cardTxt: txt.slice(0, 250)
    };
})"""

SHEET_FIELDS_JS = """(function(){
    var sheet = document.getElementById('wsPpeSheet');
    var issued = document.getElementById('wsPpeIssued');
    var mfg = document.getElementById('wsPpeManufactured');
    var term = document.getElementById('wsPpeTerm');
    var labels = sheet.querySelectorAll('label');
    var order = [];
    for (var i = 0; i < labels.length; i++) order.push(labels[i].textContent.trim());
    var hintEl = sheet.querySelector('.ws-vac-form-hint');
    var r = mfg ? mfg.getBoundingClientRect() : null;
    return {
        open: sheet.classList.contains('active'),
        mfgExists: !!mfg,
        mfgType: mfg ? mfg.type : '',
        mfgLabel: mfg ? (sheet.querySelector('label[for=\\"wsPpeManufactured\\"]') || {}).textContent : '',
        mfgVisible: !!(r && r.width > 0 && r.height > 0),
        order: order,
        issuedBeforeMfg: !!(issued && mfg && issued.compareDocumentPosition(mfg) & 4),
        mfgBeforeTerm: !!(mfg && term && mfg.compareDocumentPosition(term) & 4),
        hint: hintEl ? hintEl.textContent : ''
    };
})"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ =====
        print('=== Контекст: десктоп тёмная — карточка СИЗ + дата изготовления ===')
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

        # ---------- B: карточка работника — мета-строки СИЗ ----------
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(1000)
        page.click('button[title="Федосов А. В."]')
        page.wait_for_timeout(900)
        c = page.evaluate(CARD_PPE_JS)
        check('B1: секция СИЗ в карточке (3 записи)', c['sec'] and c['n'] == 3,
              (c['sec'], c['n'], c['cardTxt']))
        check('B2: коробка противогаза с «изгот. 15.01.2025» в мета-строке',
              c['izgot'] and c['korobka'], c['meta0'])
        check('B3: мета коробки: выдано → изгот. → срок → до (порядок заявки)',
              ('выдано 17.08.2026' in c['meta0'] and
               'изгот. 15.01.2025' in c['meta0'] and
               'срок 2 года' in c['meta0'] and
               'до 15.01.2027' in c['meta0'] and
               c['meta0'].index('выдано') < c['meta0'].index('изгот.') <
               c['meta0'].index('срок')), c['meta0'])
        check('B4: каска БЕЗ «изгот.» (окончание от даты выдачи)',
              'изгот.' not in c['meta1'] and 'до 17.08.2028' in c['meta1'],
              c['meta1'])
        check('B5: очки — «не выдано» + «До износа»',
              'не выдано' in c['meta2'] and 'До износа' in c['meta2'],
              c['meta2'])
        page.screenshot(path=SHOTS + '/01-card-ppe-izgot.png')

        # ---------- C: шторка «+ СИЗ…» — поле и приоритет ----------
        page.click('.ws-emp-addppe')
        page.wait_for_timeout(700)
        e = page.evaluate(SHEET_FIELDS_JS)
        check('C1: шторка открыта', e['open'], e)
        check('C2: поле «Дата изготовления» есть, type=date, видно',
              e['mfgExists'] and e['mfgType'] == 'date' and e['mfgVisible'],
              e)
        check('C3: подпись поля — «Дата изготовления»',
              e['mfgLabel'] == 'Дата изготовления', e['mfgLabel'])
        check('C4: порядок полей: Дата выдачи → Дата изготовления → Срок годности',
              e['issuedBeforeMfg'] and e['mfgBeforeTerm'], e['order'])
        check('C5: подсказка шторки — приоритет изготовления («от неё», «только информация»)',
              'от неё' in e['hint'] and 'только информация' in e['hint'] and
              'N767н' in e['hint'], e['hint'])

        # авто-дата: приоритет изготовления
        page.fill('#wsPpeName', 'Фильтрующая коробка противогаза (запасная)')
        page.fill('#wsPpeIssued', '2026-08-17')
        page.fill('#wsPpeManufactured', '2025-01-15')
        page.select_option('#wsPpeTerm', '2 года')
        page.wait_for_timeout(400)
        h1 = page.evaluate(
            "document.getElementById('wsPpeExpiryInfo').textContent")
        check('C6: ПРИОРИТЕТ: окончание = изготовление + срок → '
              '«15.01.2027 (от даты изготовления — заполнится автоматически)»',
              '15.01.2027' in h1 and 'от даты изготовления' in h1, h1)
        # изготовление убрано → от даты выдачи
        page.fill('#wsPpeManufactured', '')
        page.wait_for_timeout(400)
        h2 = page.evaluate(
            "document.getElementById('wsPpeExpiryInfo').textContent")
        check('C7: без изготовления → от выдачи: «17.08.2028 '
              '(заполнится автоматически)» без пометки приоритета',
              '17.08.2028' in h2 and 'от даты изготовления' not in h2, h2)
        # только изготовление (выдача пуста)
        page.fill('#wsPpeIssued', '')
        page.fill('#wsPpeManufactured', '2025-01-15')
        page.wait_for_timeout(400)
        h3 = page.evaluate(
            "document.getElementById('wsPpeExpiryInfo').textContent")
        check('C8: только изготовление (без выдачи) → считается от него',
              '15.01.2027' in h3 and 'от даты изготовления' in h3, h3)
        # «До износа»
        page.select_option('#wsPpeTerm', 'До износа')
        page.wait_for_timeout(400)
        h4 = page.evaluate(
            "document.getElementById('wsPpeExpiryInfo').textContent")
        check('C9: «До износа» → «Дата окончания срока годности: До износа»',
              h4 == 'Дата окончания срока годности: До износа', h4)
        page.select_option('#wsPpeTerm', '2 года')
        page.fill('#wsPpeIssued', '2026-08-17')
        page.wait_for_timeout(300)
        page.screenshot(path=SHOTS + '/02-ppe-sheet-priority.png')

        # ---------- D: добавление с датой изготовления ----------
        n_add = len(api_calls_of('workSchedule.addPpe'))
        page.click('#wsPpeSubmitBtn')
        page.wait_for_timeout(1600)
        adds = api_calls_of('workSchedule.addPpe')
        ok_payload = (len(adds) == n_add + 1 and
                      adds[-1]['body'].get('дата_изготовления') == '2025-01-15' and
                      adds[-1]['body'].get('дата_выдачи') == '2026-08-17' and
                      adds[-1]['body'].get('срок_годности') == '2 года' and
                      adds[-1]['body'].get('таб_номер') == '0871')
        check('D1: addPpe payload с датой изготовления (и выдача, и срок)',
              ok_payload, adds[-1]['body'] if adds else None)
        d = page.evaluate("""(function(){
            var body = document.getElementById('wsWorkersBody');
            var txt = body ? (body.textContent || '') : '';
            return {
                sheetOpen: document.getElementById('wsPpeSheet')
                    .classList.contains('active'),
                zapasn: txt.indexOf('(запасная)') !== -1,
                izgot: txt.indexOf('изгот. 15.01.2025') !== -1,
                till: txt.indexOf('до 15.01.2027') !== -1,
                items: body ? body.querySelectorAll('.ws-ppe-item').length : 0
            };
        })()""")
        check('D2: шторка закрыта, запись появилась в карточке (4 записи)',
              (not d['sheetOpen']) and d['zapasn'] and d['items'] == 4,
              (d['sheetOpen'], d['zapasn'], d['items']))
        check('D3: новая запись с «изгот. 15.01.2025» и «до 15.01.2027» '
              '(мок посчитал от изготовления)',
              d['izgot'] and d['till'], (d['izgot'], d['till']))

        # ---------- E: правка ✎ — префилл и сброс приоритета ----------
        page.locator('.ws-ppe-item .ws-popup-act[title="Редактировать запись СИЗ"]').first.click()
        page.wait_for_timeout(800)
        g = page.evaluate("""(function(){
            return {
                title: document.getElementById('wsPpeSheetTitle').textContent,
                submit: document.getElementById('wsPpeSubmitBtn').textContent,
                name: document.getElementById('wsPpeName').value,
                issued: document.getElementById('wsPpeIssued').value,
                mfg: document.getElementById('wsPpeManufactured').value,
                term: document.getElementById('wsPpeTerm').value,
                hint: document.getElementById('wsPpeExpiryInfo').textContent
            };
        })()""")
        check('E1: правка открыта («Правка СИЗ»/«Сохранить»), '
              'дата изготовления ПРЕФИЛЛЕна (15.01.2025)',
              g['title'] == 'Правка СИЗ' and g['submit'] == 'Сохранить' and
              g['mfg'] == '2025-01-15', g)
        check('E2: hint в правке сразу от изготовления',
              '15.01.2027' in g['hint'] and 'от даты изготовления' in g['hint'],
              g['hint'])
        page.fill('#wsPpeManufactured', '')
        page.wait_for_timeout(300)
        n_upd = len(api_calls_of('workSchedule.updatePpe'))
        page.click('#wsPpeSubmitBtn')
        page.wait_for_timeout(1600)
        upds = api_calls_of('workSchedule.updatePpe')
        ok_upd = (len(upds) == n_upd + 1 and
                  upds[-1]['body'].get('id') == 11 and
                  upds[-1]['body'].get('дата_изготовления') == '' and
                  upds[-1]['body'].get('дата_выдачи') == '2026-08-17')
        check('E3: updatePpe после очистки: дата_изготовления = \'\' '
              '(приоритет сброшен), id/выдача на месте',
              ok_upd, upds[-1]['body'] if upds else None)
        e3 = page.evaluate("""(function(){
            var body = document.getElementById('wsWorkersBody');
            var txt = body ? (body.textContent || '') : '';
            var items = body ? body.querySelectorAll('.ws-ppe-item') : [];
            var meta = '';
            for (var i = 0; i < items.length; i++) {
                var nm = items[i].querySelector('.ws-ppe-name');
                var nmTxt = nm ? nm.textContent : '';
                // ОРИГИНАЛЬНАЯ коробка (запасную добавили последней)
                if (nmTxt.indexOf('коробка') !== -1 &&
                    nmTxt.indexOf('запасная') === -1) {
                    var m = items[i].querySelector('.ws-ppe-meta');
                    meta = m ? m.textContent : '';
                    break;
                }
            }
            return { meta: meta, izgotCount:
                     (txt.match(/изгот\\./g) || []).length };
        })()""")
        check('E4: после обновления мок пересчитал: коробка без «изгот.», '
              'окончание от выдачи (17.08.2028), осталась одна «изгот.» (запасная)',
              'изгот.' not in e3['meta'] and 'до 17.08.2028' in e3['meta'] and
              e3['izgotCount'] == 1, (e3['meta'], e3['izgotCount']))
        page.screenshot(path=SHOTS + '/03-card-after-update.png')
        check('G1: 0 JS-ошибок (десктоп)', js_errors == [], js_errors[:3])
        ctx.close()

        # ===== мобильный 375 — шторка с полем =====
        print('=== Контекст: мобайл 375 — шторка СИЗ с датой изготовления ===')
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'dark', 'mobile')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2000)
        page2.click('#wsWorkersBtn')
        page2.wait_for_timeout(1000)
        page2.click('button[title="Федосов А. В."]')
        page2.wait_for_timeout(900)
        m1 = page2.evaluate("""(function(){
            var txt = document.getElementById('wsWorkersBody').textContent || '';
            return { sec: txt.indexOf('СИЗ · средства индивидуальной защиты') !== -1,
                     izgot: txt.indexOf('изгот. 15.01.2025') !== -1 };
        })()""")
        check('F1: мобайл — секция СИЗ жива с «изгот.» в записи',
              m1['sec'] and m1['izgot'], m1)
        page2.click('.ws-emp-addppe')
        page2.wait_for_timeout(700)
        m2r = page2.evaluate("""(function(){
            var sheet = document.getElementById('wsPpeSheet');
            var r = sheet.getBoundingClientRect();
            var ids = ['wsPpeIssued', 'wsPpeManufactured', 'wsPpeTerm'];
            var clipped = [];
            var widths = {};
            for (var i = 0; i < ids.length; i++) {
                var el = document.getElementById(ids[i]);
                if (!el) { clipped.push(ids[i] + ':нет'); continue; }
                var er = el.getBoundingClientRect();
                widths[ids[i]] = Math.round(er.width);
                if (er.right > 376 || er.left < -1)
                    clipped.push(ids[i] + ':' + Math.round(er.right));
            }
            var mfg = document.getElementById('wsPpeManufactured');
            var mr = mfg ? mfg.getBoundingClientRect() : null;
            return {
                open: sheet.classList.contains('active'),
                inView: r.left >= -1 && r.right <= 376 && r.width > 0,
                mfgExists: !!mfg,
                mfgInRow: !!(mr && mr.width > 40 && mr.height > 0),
                clipped: clipped,
                widths: widths
            };
        })()""")
        check('F2: мобайл — шторка открыта в границах экрана',
              m2r['open'] and m2r['inView'], m2r)
        check('F3: мобайл — поле «Дата изготовления» доступно',
              m2r['mfgExists'] and m2r['mfgInRow'], m2r)
        check('F3b: мобайл — НИ ОДНО из трёх полей дат не обрезано '
              '(ряд — столбик ≤480px)',
              m2r['clipped'] == [], (m2r['clipped'], m2r['widths']))
        page2.fill('#wsPpeManufactured', '2025-01-15')
        page2.select_option('#wsPpeTerm', '2 года')
        page2.wait_for_timeout(400)
        mh = page2.evaluate(
            "document.getElementById('wsPpeExpiryInfo').textContent")
        check('F4: мобайл — приоритет жив (15.01.2027 от изготовления)',
              '15.01.2027' in mh and 'от даты изготовления' in mh, mh)
        page2.screenshot(path=SHOTS + '/04-mobile-ppe-sheet.png')
        check('F5: 0 JS-ошибок (мобайл)', js_errors2 == [], js_errors2[:3])
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
