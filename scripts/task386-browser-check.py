#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 386: browser-check — заявка (3 части): (1) кнопка «Легенда» →
# «Обозначения»; шторка выезжает в СОКРАЩЁННОМ виде (коды без
# наименований, ~190px), значок-шеврон на левом крае разворачивает
# ШИРОКУЮ панель с подробными наименованиями (min(400px,45vw));
# на мобильном — переход на ОТДЕЛЬНУЮ страницу #page-ws-legend;
# (2) шапка столбца сетки — «Работники», ПРОСТО надпись (без
# функции кнопки — кнопка только в баре); (3) на странице
# «Работники» кнопка «+» → «Добавить работника».
# ДЕСКТОП 1280 (тёмная, Админ):
#   A   загрузка; B график: шапка «Работники»-надпись (без onclick),
#       кнопки «Работники»/«Обозначения» в баре;
#   C   ШТОРКА УЗКИЙ ВИД: открытие — слот ~190px, наименования
#       (.ws-lg-name) СКРЫТЫ, пояснения (.ws-lg-notesec) скрыты,
#       шеврон #wsLgChv виден, заголовок «Обозначения», коды/свотчи;
#   D   ШЕВРОН → ШИРОКИЙ ВИД: слот ~400px, наименования ВИДИМЫ,
#       пояснения видимы, aria-pressed=true, svg развёрнут;
#   E   обратное сворачивание → ~190px, имена скрыты;
#   F   закрытие кнопкой (за край, aria-pressed=false, шеврон hidden);
#   G   Esc закрывает; H взаимоисключение с «Итогами учёта»;
#   I   карточка шахматки read-only (регресс 385);
#   J   страница «Работники»: «Добавить работника» → «Новый
#       работник» (таб. № вводится); «Правка данных…» → префилл,
#       таб. № readonly;
#   K   клик по th шапки НЕ уводит со страницы табеля;
#   L   0 JS-ошибок.
# ДЕСКТОП 1280 (зритель workschedule.view):
#   N   «Работники» скрыта; шапка без класса кнопки; карточка без
#       правки; O «Обозначения» — шторка + разворот шевроном; P 0 ошибок.
# МОБАЙЛ 375 (светлая, Админ):
#   Q   «Обозначения» → СТРАНИЦА #page-ws-legend (шторка display:
#       none), наименования и пояснения ВИДИМЫ, шеврон «Назад»
#       возвращает на табель; R страница «Работники» в границах,
#       кнопка «Добавить работника»; S 0 JS-ошибок.
# Порт 8997 (запуск: python3 -m http.server 8997 &).
import calendar, datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8997
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': 'бригада А'},
  {'таб_номер': '023', 'ФИО': 'Пётр Петров', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
VACATIONS = [
  {'id': 201, 'таб_номер': '017', 'часть': 1,
   'дата_начала': '%04d-%02d-01' % (Y, M), 'дата_окончания': '%04d-%02d-10' % (Y, M),
   'дней': 10, 'комментарий': 'лето'},
]
TRAININGS = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Целевой инструктаж',
   'дата_начала': '%04d-%02d-10' % (Y, M), 'дата_окончания': '%04d-%02d-10' % (Y, M),
   'длительность_дней': 1, 'комментарий': ''},
]
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск ежегодный основной', 'color': '#ECEFF1'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#C8E6C9'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'},
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
ENTRIES = [
  {'id': 1, 'дата': '%04d-%02d-05' % (Y, M), 'таб_номер': '017', 'статус': 'Д',
   'источник': 'авто', 'переработка': 0, 'праздник': 0},
]

API_CALLS = []

def mock_response(action, body, viewer=False):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if not viewer else 'КИП ИОС дежурный'}}
    if action == 'getMyAccess':
        perms = ({'workschedule.view': True, 'workschedule.edit': True}
                 if not viewer else
                 {'workschedule.view': True, 'workschedule.edit': False,
                  'workschedule.view.min': False})
        return {'ok': True, 'data': {'role': 'Админ' if not viewer else 'КИП ИОС дежурный',
                'found': True, 'permissions': perms}}
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
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': [v for v in VACATIONS]}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action in ('workSchedule.updateEmployee', 'workSchedule.updateVacation',
                  'workSchedule.deleteVacation', 'workSchedule.addTraining',
                  'workSchedule.deleteTraining', 'workSchedule.addEmployee',
                  'workSchedule.dismissEmployee', 'workSchedule.setManualEntry',
                  'workSchedule.deleteEntry', 'workSchedule.generateMonth'):
        API_CALLS.append((action, dict(body or {})))
        return {'ok': True, 'data': {'ok': True}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def attach(page, ctx, theme, tag, viewer=False):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body, viewer),
                                      ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t386-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t386-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# состояние шторки «Обозначения»: слот/вид/шеврон/видимость имён
LEGEND_JS = """(function(){
    var d = document.getElementById('wsLegendDrawer');
    var b = document.getElementById('wsLegendBtn');
    var chv = document.getElementById('wsLgChv');
    var body = document.getElementById('wsLegendBody');
    var first = body ? body.querySelector('.ws-lg-name') : null;
    var notesec = body ? body.querySelector('.ws-lg-notesec') : null;
    var r = d.getBoundingClientRect();
    var cr = chv ? chv.getBoundingClientRect() : {width: 0, height: 0};
    var sv = chv ? chv.querySelector('svg') : null;
    var svr = sv ? sv.getBoundingClientRect() : {width: 0};
    return {
        pressed: b ? b.getAttribute('aria-pressed') : 'x',
        slot: Math.round(r.width),
        right: Math.round(r.right),
        chvHidden: chv ? chv.hidden : true,
        chvW: Math.round(cr.width),
        chvPressed: chv ? chv.getAttribute('aria-pressed') : 'x',
        chvLabel: chv ? chv.getAttribute('aria-label') : '',
        svW: Math.round(svr.width),
        nameVisible: !!(first && first.offsetParent),
        nameTxt: first ? first.textContent : '',
        notesVisible: !!(notesec && notesec.offsetParent),
        swatches: body ? body.querySelectorAll('.ws-lg-swatch').length : 0,
        codes: body ? body.querySelectorAll('.ws-lg-code').length : 0
    };
})()"""

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
    check('B1: график открыт, сетка отрисована',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length >= 2"))
    head = page.evaluate("""(function(){
        var th = document.querySelector('.ws-grid thead th.ws-emp-col');
        return { txt: th.textContent, hasOnclick: !!th.getAttribute('onclick'),
                 cls: th.className };
    })()""")
    check('B2: шапка сетки — «Работники» (Task 386)', head['txt'] == 'Работники', head)
    check('B3: шапка — ПРОСТО надпись (без onclick/класса кнопки)',
          not head['hasOnclick'] and 'ws-emp-head-add' not in head['cls'], head)
    try:
        page.wait_for_selector('#wsWorkersBtn:not([hidden])', timeout=8000)
    except Exception:
        pass
    check('B4: кнопка «Работники» в баре видна (Админ)',
          page.evaluate("!document.getElementById('wsWorkersBtn').hidden"))
    check('B5: кнопка «Обозначения» в баре (текст переименован)',
          page.evaluate("var b=document.getElementById('wsLegendBtn');" +
                        "!!b && b.textContent === 'Обозначения'"))

    # ---------- C: шторка — УЗКИЙ вид (сокращённые обозначения) ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(700)
    lg = page.evaluate(LEGEND_JS)
    check('C1: шторка открыта (aria-pressed=true)', lg['pressed'] == 'true', lg['pressed'])
    check('C2: СОКРАЩЁННЫЙ вид — слот ~190px (не 400)',
          180 <= lg['slot'] <= 200, lg['slot'])
    check('C3: панель у правого края (выехала)', lg['right'] == 1280, lg['right'])
    check('C4: наименования кодов СКРЫТЫ (.ws-lg-name)', not lg['nameVisible'])
    check('C5: пояснения (.ws-lg-notesec) СКРЫТЫ', not lg['notesVisible'])
    check('C6: шеврон #wsLgChv виден на крае', not lg['chvHidden'] and lg['chvW'] > 0)
    check('C7: шеврон — aria-pressed=false (узкий)', lg['chvPressed'] == 'false')
    check('C8: заголовок шторки «Обозначения»',
          page.evaluate("document.querySelector('.ws-lg-head').textContent") == 'Обозначения')
    check('C9: коды из справочника (6) со свотчами',
          lg['codes'] == 6 and lg['swatches'] == 6, (lg['codes'], lg['swatches']))
    page.screenshot(path='/tmp/t386-proof-legend-narrow.png', full_page=False)

    # ---------- D: шеврон → ШИРОКИЙ вид (подробные наименования) ----------
    page.click('#wsLgChv')
    page.wait_for_timeout(700)
    lgw = page.evaluate(LEGEND_JS)
    check('D1: разворот — слот ~400px', 390 <= lgw['slot'] <= 410, lgw['slot'])
    check('D2: наименования ВИДИМЫ («День (12-час)»)',
          lgw['nameVisible'] and '12-час' in lgw['nameTxt'], lgw['nameTxt'])
    check('D3: пояснения (.ws-lg-notesec) ВИДИМЫ', lgw['notesVisible'])
    check('D4: шеврон aria-pressed=true', lgw['chvPressed'] == 'true')
    check('D5: aria-label «Только коды (свернуть)»',
          'Только коды' in lgw['chvLabel'], lgw['chvLabel'])
    check('D6: сетка сжата под широкую панель (панель в границах)',
          lgw['right'] == 1280 and lgw['slot'] >= 390)
    page.screenshot(path='/tmp/t386-proof-legend-wide.png', full_page=False)

    # ---------- E: сворачивание обратно ----------
    page.click('#wsLgChv')
    page.wait_for_timeout(700)
    lgn = page.evaluate(LEGEND_JS)
    check('E1: свёрнута — слот ~190px', 180 <= lgn['slot'] <= 200, lgn['slot'])
    check('E2: наименования снова скрыты', not lgn['nameVisible'])
    check('E3: шеврон aria-pressed=false', lgn['chvPressed'] == 'false')

    # ---------- F: закрытие повторным кликом кнопки ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(700)
    lgc = page.evaluate(LEGEND_JS)
    check('F1: закрыта (aria-pressed=false)', lgc['pressed'] == 'false')
    check('F2: шеврон скрыт (hidden)', lgc['chvHidden'])

    # ---------- G: Esc закрывает ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)
    lge = page.evaluate(LEGEND_JS)
    check('G1: Esc закрыл шторку', lge['pressed'] == 'false' and lge['chvHidden'])

    # ---------- H: взаимоисключение с итогами ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    lgh = page.evaluate(LEGEND_JS)
    tt_open = page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')")
    check('H1: открытие итогов закрыло «Обозначения»', lgh['pressed'] == 'false')
    check('H2: итоги открыты', tt_open)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(600)

    # ---------- I: карточка шахматки — read-only (регресс 385) ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    card = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        if (!pp) return { open: false };
        var txt = pp.textContent;
        return { open: pp.classList.contains('active'),
                 editData: txt.indexOf('Правка данных…'),
                 acts: pp.querySelectorAll('.ws-popup-act').length,
                 fio: txt.indexOf('Иванов') !== -1 };
    })()""")
    check('I1: карточка открылась, данные есть', card['open'] and card['fio'])
    check('I2: карточка read-only (кнопок правки нет)',
          card['editData'] == -1 and card['acts'] == 0)
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)

    # ---------- J: страница «Работники» — «Добавить работника» ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(700)
    wp = page.evaluate("""(function(){
        var pg = document.getElementById('page-ws-workers');
        var body = document.getElementById('wsWorkersBody');
        var btn = document.getElementById('wsWorkersAddBtn');
        var cards = body ? body.querySelectorAll('.ws-wcard') : [];
        return { active: pg.classList.contains('active'),
                 title: pg.querySelector('.page-inline-header-title').textContent,
                 count: body ? (body.querySelector('.ws-workers-count') || {}).textContent : '',
                 n: cards.length,
                 btnTxt: btn ? btn.textContent : '',
                 firstHasEdit: cards.length ? cards[0].textContent.indexOf('Правка данных…') !== -1 : false };
    })()""")
    check('J1: страница «Работники» активна', wp['active'])
    check('J2: счётчик/карточки', '2' in wp['count'] and wp['n'] == 2 and wp['firstHasEdit'])
    check('J3: кнопка — ТЕКСТ «Добавить работника» (не «+»)',
          wp['btnTxt'] == 'Добавить работника', wp['btnTxt'])
    page.screenshot(path='/tmp/t386-proof-workers-page.png', full_page=False)

    page.click('#wsWorkersAddBtn')
    page.wait_for_timeout(600)
    h_state = page.evaluate("""(function(){
        var t = document.getElementById('wsEmpSheetTitle');
        var b = document.getElementById('wsEmpSubmitBtn');
        var no = document.getElementById('wsEmpTabNo');
        return { active: document.getElementById('wsEmpSheet').classList.contains('active'),
                 title: t ? t.textContent : '', btn: b ? b.textContent : '',
                 ro: no ? no.readOnly : true };
    })()""")
    check('J4: «Добавить работника» → шторка «Новый работник»',
          h_state['active'] and h_state['title'] == 'Новый работник', h_state)
    check('J5: кнопка «Добавить», таб. № вводится',
          h_state['btn'] == 'Добавить' and h_state['ro'] is False)
    page.click('#wsEmpSheet .flow-input-cancel')
    page.wait_for_timeout(600)

    page.click('#wsWorkersBody .ws-wcard .ws-emp-editdata')
    page.wait_for_timeout(600)
    i_state = page.evaluate("""(function(){
        var t = document.getElementById('wsEmpSheetTitle');
        var no = document.getElementById('wsEmpTabNo');
        var fio = document.getElementById('wsEmpFio');
        return { active: document.getElementById('wsEmpSheet').classList.contains('active'),
                 title: t ? t.textContent : '',
                 tab: no ? no.value : '', ro: no ? no.readOnly : false,
                 fio: fio ? fio.value : '' };
    })()""")
    check('J6: «Правка данных…» → «Правка работника» (префилл, readonly PK)',
          i_state['active'] and i_state['title'] == 'Правка работника' and
          i_state['tab'] == '017' and i_state['ro'] is True and
          i_state['fio'] == 'Иванов Иван Иванович', i_state)
    page.click('#wsEmpSheet .flow-input-cancel')
    page.wait_for_timeout(600)

    # ---------- K: клик по th шапки НЕ уводит со страницы табеля ----------
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    page.click('.ws-grid thead th.ws-emp-col')
    page.wait_for_timeout(600)
    check('K1: клик по надписи «Работники» — остаёмся на табеле',
          page.evaluate("document.getElementById('page-work-schedule').classList.contains('active')"))
    check('L: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: зритель (workschedule.view) =================
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'dark', 'viewer', viewer=True)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    check('N1: зритель: кнопка «Работники» СКРЫТА',
          page2.evaluate("document.getElementById('wsWorkersBtn').hidden"))
    check('N2: зритель: шапка — надпись без класса кнопки',
          page2.evaluate("!document.querySelector('.ws-grid thead th.ws-emp-col.ws-emp-head-add')"))
    page2.click('#wsLegendBtn')
    page2.wait_for_timeout(700)
    lg2 = page2.evaluate(LEGEND_JS)
    check('N3: зритель: «Обозначения» — узкий вид открылся',
          lg2['pressed'] == 'true' and 180 <= lg2['slot'] <= 200, lg2['slot'])
    page2.click('#wsLgChv')
    page2.wait_for_timeout(700)
    lg2w = page2.evaluate(LEGEND_JS)
    check('N4: зритель: шеврон разворачивает (имена видимы)',
          390 <= lg2w['slot'] <= 410 and lg2w['nameVisible'])
    check('P: 0 JS-ошибок (зритель)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 375, светлая, Админ =================
    ctx3 = browser.new_context(viewport={'width': 375, 'height': 700})
    page3 = ctx3.new_page()
    js_errors3 = attach(page3, ctx3, 'light', 'mobile')

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.click('#wsLegendBtn')
    page3.wait_for_timeout(700)
    lm = page3.evaluate("""(function(){
        var d = document.getElementById('wsLegendDrawer');
        var pg = document.getElementById('page-ws-legend');
        var body = document.getElementById('wsLgPageBody');
        var first = body ? body.querySelector('.ws-lg-name') : null;
        var notesec = body ? body.querySelector('.ws-lg-notesec') : null;
        var title = pg.querySelector('.page-inline-header-title');
        var r = pg.getBoundingClientRect();
        return { pageActive: pg.classList.contains('active'),
                 title: title ? title.textContent : '',
                 drawerW: Math.round(d.getBoundingClientRect().width),
                 drawerDisplay: getComputedStyle(d).display,
                 nameVisible: !!(first && first.offsetParent),
                 nameTxt: first ? first.textContent : '',
                 notesVisible: !!(notesec && notesec.offsetParent),
                 codes: body ? body.querySelectorAll('.ws-lg-code').length : 0,
                 inView: r.left >= 0 && r.right <= 375 && r.top >= 0,
                 wsActive: document.getElementById('page-work-schedule').classList.contains('active') };
    })()""")
    check('Q1: мобайл: «Обозначения» → СТРАНИЦА #page-ws-legend (не шторка)',
          lm['pageActive'] and not lm['wsActive'])
    check('Q2: мобайл: шторка-десктоп погашена (display: none)',
          lm['drawerDisplay'] == 'none' and lm['drawerW'] == 0, lm['drawerDisplay'])
    check('Q3: мобайл: заголовок страницы «Обозначения»', lm['title'] == 'Обозначения', lm['title'])
    check('Q4: мобайл: наименования ВИДИМЫ на странице',
          lm['nameVisible'] and '12-час' in lm['nameTxt'], lm['nameTxt'])
    check('Q5: мобайл: пояснения видимы, коды на месте',
          lm['notesVisible'] and lm['codes'] == 6, lm['codes'])
    check('Q6: мобайл: страница в границах вьюпорта', lm['inView'])
    page3.screenshot(path='/tmp/t386-proof-mobile-legend-page.png', full_page=False)

    # шеврон «Назад» возвращает на табель
    page3.click('#page-ws-legend .page-inline-header-chevron')
    page3.wait_for_timeout(700)
    back = page3.evaluate("""(function(){
        return { legend: document.getElementById('page-ws-legend').classList.contains('active'),
                 ws: document.getElementById('page-work-schedule').classList.contains('active') };
    })()""")
    check('Q7: мобайл: шеврон «Назад» вернул на табель',
          not back['legend'] and back['ws'], back)

    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(1500)
    page3.click('#wsWorkersBtn')
    page3.wait_for_timeout(700)
    wm = page3.evaluate("""(function(){
        var pg = document.getElementById('page-ws-workers');
        var body = document.getElementById('wsWorkersBody');
        var btn = document.getElementById('wsWorkersAddBtn');
        var b = body.getBoundingClientRect();
        return { active: pg.classList.contains('active'),
                 n: body.querySelectorAll('.ws-wcard').length,
                 btnTxt: btn ? btn.textContent : '',
                 inView: b.left >= 0 && b.right <= 375 };
    })()""")
    check('R1: мобайл: страница «Работники» — карточки в границах',
          wm['active'] and wm['n'] == 2 and wm['inView'])
    check('R2: мобайл: кнопка «Добавить работника» (текст)',
          wm['btnTxt'] == 'Добавить работника', wm['btnTxt'])
    page3.screenshot(path='/tmp/t386-proof-mobile-workers.png', full_page=False)
    check('S: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
