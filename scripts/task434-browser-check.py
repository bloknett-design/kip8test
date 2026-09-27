#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 434: browser-check — заявка «Коды на печати сделать в две
# колонки под названием "Коды:". В картах работников, в блоке
# профиля, после знака группы указывать дату последней выполненной
# проверке знаний до 1000В, в формате "от дд.мм.гггг". Также в
# окнах мероприятий ячеек табеля, дату указывать в формате
# "дд.мм.гггг"».
# ПРОВЕРКИ (мок-сервер, порт 8934):
#   1) десктоп 1280 тёмная, edit:
#      • ПЕЧАТЬ (предпросмотр Task 430): заголовок «Коды:» —
#        отдельной строкой СВЕРХУ; сетка .wsp-legend-cols —
#        ДВЕ равные колонки на всю ширину листа; каждый код —
#        своя строка колонки (два X-кластера); длинное
#        наименование ПЗ переносится ВНУТРИ своей колонки
#        (высота записи > одной строки); мероприятия — выше кодов;
#        сноска — ниже;
#      • КАРТОЧКА: «Группа допуска» работника с выполненной
#        проверкой знаний до 1000 В — «IV от 15.03.2026»;
#        работник без выполненной проверки — только «III»;
#      • ОКНО «Мероприятия в этот день» (клик по ячейке с
#        бейджами): подстрока «дд.мм.гггг · ФИО» (не ISO);
#        заголовок окна кодов — дата дд.мм.гггг;
#   2) десктоп 1280 светлая, view (зритель): клик по ячейке —
#      ТОЛЬКО окно мероприятий, дата дд.мм.гггг.
import datetime
import json
import threading
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8934
TODAY = datetime.date.today()
Y = TODAY.year
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)


def ru(iso):
    p = str(iso).split('-')
    return p[2] + '.' + p[1] + '.' + p[0]


U_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
EX_1000 = ('Периодическая проверка знаний на допуск к проведению '
           'работ в электроустановках до 1000 В')
T_OB = 'Охрана труда (ежегодный курс)'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0872', 'ФИО': 'Тестов Б. Б.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': '', 'старт_цикла': '',
   'дата_приёма': '2025-01-10', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': 'III', 'комментарий': ''},
]

INSTR_LIST = [
  {'название': U_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': 'Инстр. ОТ'},
  {'название': EX_1000, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': 'ПЗ ЭБ до 1000 В'},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5',
   'short': 'ночь'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#90CAF9', 'short': 'инстр.'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#A5D6A7',
   'short': 'обучение'},
  {'code': 'ПЗ',
   'name': 'Проверка знаний, по охране труда и промышленной '
           'безопасности, до 1000В, на допуск к самостоятельной работе',
   'color': '#FFCDD2', 'short': 'проверка знаний'},
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


# лист «Инструктажи»: записи ВСЕХ лет
def fresh_instr():
    return [
        # 0871: выполненная проверка знаний до 1000 В (март) —
        # дата для профиля
        ev(600, '0871', 'проверка_знаний', EX_1000,
           '%04d-03-15' % Y, done=1),
        # 0871: НЕвыполненная проверка до 1000 В (сегодня, для
        # бейджа ПЗ/печати) — датой профиля НЕ становится
        ev(601, '0871', 'проверка_знаний', EX_1000, TODAY_ISO),
        # 0872: проверка до 1000 В НЕ выполнена — профилю без даты
        ev(602, '0872', 'проверка_знаний', EX_1000,
           '%04d-02-10' % Y),
        # 0871: повторный инструктаж сегодня (бейдж И, печать)
        ev(603, '0871', 'инструктаж', U_OT, TODAY_ISO),
    ]


# лист «Мероприятия»: обучение сегодня (бейдж ОБ)
def fresh_events():
    return [ev(500, '0871', 'обучение', T_OB, TODAY_ISO)]


INSTR = fresh_instr()
EVENTS = fresh_events()


def fresh_entries():
    out = []
    dim = (datetime.date(TODAY.year, TODAY.month % 12 + 1, 1) -
           datetime.timedelta(days=1)).day
    for day in range(1, dim + 1):
        iso = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, day)
        if day <= 10:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
            out.append({'дата': iso, 'таб_номер': '0872', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
        elif day <= 12:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'Н',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
        elif day == 13:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'ОТ',
                        'переработка': 0, 'праздник': 0, 'источник': 'руч'})
    return out


ENTRIES = fresh_entries()

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
                     'workschedule.edit': True}
            role = 'Админ'
        else:
            perms = {'calc.view': True, 'library.view': True,
                     'kipios.view': True, 'workschedule.view': True,
                     'workschedule.edit': False,
                     'workschedule.view.min': False}
            role = 'КИП ИОС'
        return {'ok': True, 'data': {'role': role, 'found': True,
                'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
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
        both = INSTR + EVENTS
        return {'ok': True, 'data': {
            'trainings': [dict(r) for r in both
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t434-%s');" % tag +
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
                      body='not found (t434-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def open_workers_card(page, fio):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('%s')" % fio)
    page.wait_for_timeout(900)


def group_row(page, fio):
    open_workers_card(page, fio)
    return page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('ФИО') === -1 &&
            h.textContent.indexOf('Профиль') === -1) { /* любой блок */ }
        var rows = cards[i].querySelectorAll('.ws-emp-field');
        for (var r = 0; r < rows.length; r++) {
            var k = rows[r].querySelector('.ws-emp-k');
            if (k && k.textContent.indexOf('Группа допуска') !== -1) {
                var v = rows[r].querySelector('.ws-emp-v');
                return v ? v.textContent : '';
            }
        }
    }
    return '';
})""")


def click_cell(page, iso, tab):
    page.evaluate("""(function(a){
    var tds = document.querySelectorAll('td.ws-cell');
    for (var i = 0; i < tds.length; i++) {
        var oc = tds[i].getAttribute('onclick') || '';
        if (oc.indexOf(a.iso) !== -1 && oc.indexOf(a.tab) !== -1) {
            tds[i].click();
            return true;
        }
    }
    return false;
})""", {'iso': iso, 'tab': tab})


# геометрия кодов в iframe предпросмотра печати
LEGEND_JS = """(function(){
    var d = document;
    var out = {title: null, cols: null, items: []};
    var sheet = d.getElementById('wsPrintSheet');
    if (!sheet) return out;
    var t = sheet.querySelector('.wsp-legend-t');
    if (t) {
        var tr = t.getBoundingClientRect();
        out.title = {text: t.textContent.trim().slice(0, 30),
                     display: getComputedStyle(t).display,
                     top: Math.round(tr.top), bottom: Math.round(tr.bottom),
                     w: Math.round(tr.width)};
    }
    var c = sheet.querySelector('.wsp-legend-cols');
    if (c) {
        var cr = c.getBoundingClientRect();
        out.cols = {display: getComputedStyle(c).display,
                    tracks: getComputedStyle(c).gridTemplateColumns,
                    x: Math.round(cr.left), right: Math.round(cr.right),
                    w: Math.round(cr.width)};
    }
    var lgs = sheet.querySelectorAll('.wsp-lg');
    for (var i = 0; i < lgs.length; i++) {
        var r = lgs[i].getBoundingClientRect();
        out.items.push({x: Math.round(r.left), y: Math.round(r.top),
                        w: Math.round(r.width), h: Math.round(r.height),
                        text: lgs[i].textContent.trim().slice(0, 24)});
    }
    var mv = sheet.querySelector('.wsp-mev');
    var lg = sheet.querySelector('.wsp-legend');
    if (mv && lg) {
        out.mevBottom = Math.round(mv.getBoundingClientRect().bottom);
        out.legendTop = Math.round(lg.getBoundingClientRect().top);
    }
    var ft = sheet.querySelector('.wsp-foot');
    if (ft) {
        out.footTop = Math.round(ft.getBoundingClientRect().top);
        out.legendBottom = Math.round(lg.getBoundingClientRect().bottom);
    }
    return out;
})"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ===== Контекст 1: десктоп 1280, тёмная, edit =====
        print('=== Контекст 1: десктоп тёмная edit — печать/карточка/окна ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'edit')
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        check('I0: приложение загрузилось',
              page.evaluate("document.title === 'КИПиА'"))

        # --- ПЕЧАТЬ: предпросмотр, коды в две колонки ---
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2200)
        page.click('#wsPrintBtn')
        page.wait_for_timeout(1200)
        check('I1: диалог предпросмотра печати открыт',
              page.evaluate(
                  "!!document.getElementById('wsPrintPrevModal')"))
        frame_el = page.query_selector('.wspprev-frame')
        check('I2: iframe предпросмотра есть', frame_el is not None)
        frame = frame_el.content_frame()
        page.wait_for_timeout(600)
        g = frame.evaluate(LEGEND_JS)
        # заголовок «Коды:» — отдельной строкой СВЕРХУ сетки
        check('I3: заголовок «Коды:» есть и блочный',
              g.get('title') and
              g['title']['text'].startswith('Коды:') and
              g['title']['display'] == 'block', g.get('title'))
        first_item_y = min([it['y'] for it in g['items']]) if g['items'] else 0
        check('I4: заголовок — НАД кодами (своя строка)',
              g['title']['bottom'] <= first_item_y + 2,
              (g['title']['bottom'], first_item_y))
        # сетка — grid, ДВЕ равные колонки до конца листа
        check('I5: сетка кодов — display: grid',
              g.get('cols') and g['cols']['display'] == 'grid',
              g.get('cols'))
        tracks = [t for t in (g['cols']['tracks'] or '').split() if t]
        check('I6: РОВНО ДВЕ колонки (grid-template-columns)',
              len(tracks) == 2, tracks)
        if len(tracks) == 2:
            def px(t):
                return float(t.replace('px', '').replace('mm', ''))
            w1, w2 = px(tracks[0]), px(tracks[1])
            check('I7: колонки РАВНЫЕ (в пределах 3%)',
                  abs(w1 - w2) <= 0.03 * max(w1, w2), (w1, w2))
            check('I8: сетка растянута до конца листа (ширина >= 900px)',
                  g['cols']['w'] >= 900, g['cols']['w'])
        # каждый код — своя строка колонки: два X-кластера
        xs = sorted(set(it['x'] for it in g['items']))
        check('I9: кодов в легенде достаточно (>= 5)', len(g['items']) >= 5,
              len(g['items']))
        col_x = [it['x'] for it in g['items']]
        lefts = [x for x in col_x if x < g['cols']['x'] + g['cols']['w'] / 2]
        rights = [x for x in col_x if x >= g['cols']['x'] + g['cols']['w'] / 2]
        check('I10: записи в ДВУХ колонках (левая и правая)',
              len(lefts) >= 2 and len(rights) >= 2,
              (len(lefts), len(rights)))
        # в каждой колонке — по одной записи на строке
        same_line = 0
        for a in range(len(g['items'])):
            for b in range(a + 1, len(g['items'])):
                ia, ib = g['items'][a], g['items'][b]
                if abs(ia['y'] - ib['y']) < 3 and abs(ia['x'] - ib['x']) < 3:
                    same_line += 1
        check('I11: каждая запись — своя строка (нет наложений)',
              same_line == 0, same_line)
        # длинное наименование ПЗ переносится ВНУТРИ колонки
        # (базовая линия — САМАЯ НИЗКАЯ запись-однострочник: «Н»,
        # «ОТ»…; Д8/И с длинными каноническими именами — 2 строки)
        pz = [it for it in g['items'] if it['text'].startswith('ПЗ')]
        short_h = [it['h'] for it in g['items']
                   if not it['text'].startswith(('Д8', 'Д7', 'ПЗ', 'И', 'д', 'н'))]
        if pz and short_h:
            base = min(short_h)
            check('I12: длинное имя ПЗ переносится (2+ строки)',
                  pz[0]['h'] > base + 4, (pz[0]['h'], base))
            check('I13: запись ПЗ не шире своей колонки',
                  pz[0]['w'] <= (g['cols']['w'] / 2) + 12,
                  (pz[0]['w'], g['cols']['w']))
        # порядок секций: мероприятия → коды → сноска
        check('I14: мероприятия — ВЫШЕ кодов',
              g.get('mevBottom', 10 ** 9) <= g.get('legendTop', 0) + 2,
              (g.get('mevBottom'), g.get('legendTop')))
        check('I15: сноска — НИЖЕ кодов',
              g.get('legendBottom', 0) <= g.get('footTop', 10 ** 9) + 2,
              (g.get('legendBottom'), g.get('footTop')))
        page.screenshot(path='task434-proof-print-2cols.png', full_page=False)
        # закрываем предпросмотр — не мешает дальнейшим кликам
        page.evaluate("WorkSchedule._closePrintPreview()")
        page.wait_for_timeout(500)

        # --- КАРТОЧКА: группа + дата проверки знаний до 1000 В ---
        g1 = group_row(page, 'Федосов')
        check('I16: Федосов — «IV от 15.03.2026»',
              g1 == 'IV от 15.03.2026', g1)
        # скриншот карточки Федосова (до переключения на Тестова)
        page.screenshot(path='task434-proof-card-group-date.png',
                        full_page=False)
        g2 = group_row(page, 'Тестов')
        check('I17: Тестов — только «III» (проверка не выполнена)',
              g2 == 'III', g2)
        page.screenshot(path='task434-proof-card-no-date.png',
                        full_page=False)

        # --- ОКНА ЯЧЕЙКИ: дата дд.мм.гггг ---
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2200)
        click_cell(page, TODAY_ISO, '0871')
        page.wait_for_timeout(700)
        win = page.evaluate("""(function(){
    var ev = document.getElementById('wsEventsPopup');
    var cp = document.getElementById('wsCellPopup');
    return {evActive: ev.classList.contains('active'),
            evSub: (ev.querySelector('.ws-events-sub')||{}).textContent,
            evTitle: (ev.querySelector('.ws-popup-title')||{}).textContent,
            cpActive: cp.classList.contains('active'),
            cpTitle: (cp.querySelector('.ws-popup-title')||{}).textContent};
})""")
        today_ru = ru(TODAY_ISO)
        check('I18: окно «Мероприятия в этот день» активно',
              win['evActive'])
        check('I19: подстрока окна — дата ДД.ММ.ГГГГ · ФИО',
              win['evSub'] == '%s · Федосов А. В.' % today_ru, win['evSub'])
        check('I20: ISO-даты в окне мероприятий НЕТ',
              TODAY_ISO not in (win['evSub'] or '') +
              (win['evTitle'] or ''))
        check('I21: заголовок окна кодов — дата ДД.ММ.ГГГГ',
              win['cpTitle'] and win['cpTitle'].startswith(today_ru),
              win['cpTitle'])
        page.screenshot(path='task434-proof-cell-windows-date.png',
                        full_page=False)
        check('I22: JS-ошибок нет', not js_errors, js_errors[:3])
        ctx.close()

        # ===== Контекст 2: десктоп 1280, светлая, view =====
        print('=== Контекст 2: десктоп светлая view — окно зрителя ===')
        global ADMIN
        ADMIN = False
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'view')
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        check('J0: приложение загрузилось (view)',
              page2.evaluate("document.title === 'КИПиА'"))
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2200)
        click_cell(page2, TODAY_ISO, '0871')
        page2.wait_for_timeout(700)
        win2 = page2.evaluate("""(function(){
    var ev = document.getElementById('wsEventsPopup');
    var cp = document.getElementById('wsCellPopup');
    return {evActive: ev.classList.contains('active'),
            evSub: (ev.querySelector('.ws-events-sub')||{}).textContent,
            cpActive: cp.classList.contains('active')};
})""")
        check('J1: зритель — окно мероприятий активно',
              win2['evActive'])
        check('J2: подстрока — дата ДД.ММ.ГГГГ · ФИО',
              win2['evSub'] == '%s · Федосов А. В.' % ru(TODAY_ISO),
              win2['evSub'])
        check('J3: окно кодов зрителю НЕ показывается',
              not win2['cpActive'])
        page2.screenshot(path='task434-proof-viewer-window.png',
                         full_page=False)
        check('J4: JS-ошибок нет', not js_errors2, js_errors2[:3])
        ctx2.close()

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
