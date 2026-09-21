#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 385: browser-check — заявка (3 части): (1) кнопка «Легенда» в
# баре → справа выезжает окно со всеми сокращениями шахматки (по
# принципу итогов учёта); (2) «сотрудник» → «работник» (все
# склонения) в разделе Табель; (3) карточка в шахматке — read-only
# (кнопок правки нет НИ у кого), кнопка «Работники» в баре →
# страница полных карточек (правка/добавление отпусков, мероприятий,
# данных работника).
# ДЕСКТОП 1280 (тёмная, Админ):
#   A   страница загрузилась; B график открыт, шапка «Работник»;
#   C   ЛЕГЕНДА: кнопка в ряду 2 → шторка active, класс
#       ws-legend-open, заголовок «Сокращения в шахматке», секции
#       «Коды дней (Т-12/Т-13)»/«Коды мероприятий»/«Обозначения в
#       шахматке», строки кодов из справочника (Д/Н/ОТ/И) со
#       свотчами, aria-pressed=true;
#   D   закрытие повторным кликом (класс снят, aria-pressed=false);
#   E   взаимоисключение: легенда открыта → клик «Итоги учёта» →
#       легенда закрылась, итоги открыты;
#   F   КАРТОЧКА АДМИНА — read-only: попап с данными, НЕТ «Правка
#       данных…»/«Уволить…»/«+ Отпуск…»/«+ Мероприятие…»/✎/✕;
#   G   кнопка «Работники» в баре (ряд 1) → страница
#       #page-ws-workers active, заголовок «Работники», счётчик «2
#       работника», карточки .ws-wcard с кнопками правки;
#   H   «+» шапки страницы → шторка «Новый работник»/«Добавить»,
#       таб. № вводится;
#   I   «Правка данных…» из карточки страницы → updateEmployee
#       (таб. № из состояния) → тост «Данные работника обновлены» →
#       карточка с новым ФИО;
#   J   ✎ отпуска из карточки страницы → «Правка отпуска» →
#       updateVacation(id);
#   K   «+ Мероприятие…» → шторка, сотрудник префиллен;
#   L   заголовок «Работник +» шапки сетки → страница «Работники»;
#   M   0 JS-ошибок.
# ДЕСКТОП 1280 (зритель workschedule.view):
#   N   кнопка «Работники» СКРЫТА; шапка сетки без плюса; карточка
#       без кнопок; O кнопка «Легенда» видна, шторка открывается
#       (легенда — всем уровням); P 0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ):
#   Q   легенда — fixed-шторка в границах вьюпорта; R страница
#       «Работники»: карточки в границах; S 0 JS-ошибок.
# Порт 8996.
import calendar, datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8996
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
  {'id': 202, 'таб_номер': '017', 'часть': 2,
   'дата_начала': '%04d-%02d-03' % (Y, 8 if M < 8 else min(M + 1, 12)),
   'дата_окончания': '%04d-%02d-09' % (Y, 8 if M < 8 else min(M + 1, 12)),
   'дней': 7, 'комментарий': ''},
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
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
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
    if action == 'workSchedule.updateEmployee':
        API_CALLS.append(('updateEmployee', dict(body or {})))
        tab = str((body or {}).get('таб_номер', ''))
        for e in EMPLOYEES:
            if str(e['таб_номер']) == tab:
                for k in ('ФИО', 'тип', 'должность', 'комментарий'):
                    if k in (body or {}):
                        e[k] = str(body[k])
                if 'смена' in (body or {}):
                    e['смена'] = body['смена']
                return {'ok': True, 'data': {'таб_номер': tab}}
        return {'ok': False, 'error': 'not_found_таб_номер'}
    if action == 'workSchedule.updateVacation':
        API_CALLS.append(('updateVacation', dict(body or {})))
        vid = (body or {}).get('id')
        for v in VACATIONS:
            if v['id'] == vid:
                for k in ('часть', 'дата_начала', 'дата_окончания', 'комментарий'):
                    if k in (body or {}):
                        v[k] = body[k]
                return {'ok': True, 'data': {'id': vid, 'дней': 1}}
        return {'ok': False, 'error': 'not_found'}
    if action == 'workSchedule.deleteVacation':
        API_CALLS.append(('deleteVacation', dict(body or {})))
        vid = (body or {}).get('id')
        for i, v in enumerate(VACATIONS):
            if v['id'] == vid:
                VACATIONS.pop(i)
                return {'ok': True, 'data': {'id': vid}}
        return {'ok': False, 'error': 'not_found'}
    if action in ('workSchedule.addTraining', 'workSchedule.deleteTraining',
                  'workSchedule.addEmployee', 'workSchedule.dismissEmployee',
                  'workSchedule.setManualEntry', 'workSchedule.deleteEntry',
                  'workSchedule.generateMonth'):
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
                      body='not found (t385-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t385-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

CARD_JS = """(function(){
    var pp = document.getElementById('wsEmpPopup');
    if (!pp) return { open: false };
    var txt = pp.textContent;
    return {
        open: pp.classList.contains('active'),
        txt: txt,
        editData: txt.indexOf('Правка данных…'),
        dismiss: txt.indexOf('Уволить…'),
        addVac: txt.indexOf('+ Отпуск…'),
        addTr: txt.indexOf('+ Мероприятие…'),
        acts: pp.querySelectorAll('.ws-popup-act').length
    };
})()"""

LEGEND_JS = """(function(){
    var d = document.getElementById('wsLegendDrawer');
    var b = document.getElementById('wsLegendBtn');
    var page = document.getElementById('page-work-schedule');
    var body = document.getElementById('wsLegendBody');
    var txt = body ? body.textContent : '';
    return {
        open: page.classList.contains('ws-legend-open'),
        visible: d.getBoundingClientRect().width > 50,
        pressed: b ? b.getAttribute('aria-pressed') : 'x',
        txt: txt,
        iDays: txt.indexOf('Коды дней (Т-12/Т-13)'),
        iEv: txt.indexOf('Коды мероприятий'),
        iNote: txt.indexOf('Обозначения в шахматке'),
        hasD: txt.indexOf('День (12-час)') !== -1,
        hasN: txt.indexOf('Ночь (12-час)') !== -1,
        hasOT: txt.indexOf('Отпуск') !== -1,
        hasI: txt.indexOf('Инструктаж') !== -1,
        swatches: body ? body.querySelectorAll('.ws-lg-swatch').length : 0,
        rect: d.getBoundingClientRect()
    };
})()"""

WORKERS_JS = """(function(){
    var pg = document.getElementById('page-ws-workers');
    var body = document.getElementById('wsWorkersBody');
    var cards = body ? body.querySelectorAll('.ws-wcard') : [];
    var first = cards.length ? cards[0] : null;
    return {
        active: pg.classList.contains('active'),
        title: pg.querySelector('.page-inline-header-title').textContent,
        count: body ? (body.querySelector('.ws-workers-count') || {}).textContent : '',
        n: cards.length,
        firstHasEdit: first ? first.textContent.indexOf('Правка данных…') !== -1 : false,
        firstHasDismiss: first ? first.textContent.indexOf('Уволить…') !== -1 : false,
        firstHasAddVac: first ? first.textContent.indexOf('+ Отпуск…') !== -1 : false,
        firstHasAddTr: first ? first.textContent.indexOf('+ Мероприятие…') !== -1 : false,
        firstActs: first ? first.querySelectorAll('.ws-popup-act').length : 0,
        firstFio: first ? first.querySelector('.ws-popup-title').textContent : ''
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
    head_txt = page.evaluate("document.querySelector('.ws-emp-head-txt').textContent")
    check('B2: шапка сетки — «Работник» (переименование)', head_txt == 'Работник', head_txt)
    try:
        page.wait_for_selector('#wsWorkersBtn:not([hidden])', timeout=8000)
    except Exception:
        pass
    check('B3: кнопка «Работники» в баре видна (Админ)',
          page.evaluate("!document.getElementById('wsWorkersBtn').hidden"))
    check('B4: кнопка «Легенда» в баре видна',
          page.evaluate("!!document.getElementById('wsLegendBtn') && " +
                        "document.getElementById('wsLegendBtn').textContent === 'Легенда'"))

    # ---------- C: легенда ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(700)
    lg = page.evaluate(LEGEND_JS)
    check('C1: шторка открыта (класс ws-legend-open)', lg['open'])
    check('C2: панель видима (выехала)', lg['visible'])
    check('C3: aria-pressed=true', lg['pressed'] == 'true', lg['pressed'])
    check('C4: заголовок «Сокращения в шахматке»',
          page.evaluate("document.querySelector('.ws-lg-head').textContent") == 'Сокращения в шахматке')
    check('C5: секция «Коды дней (Т-12/Т-13)»', lg['iDays'] != -1)
    check('C6: секция «Коды мероприятий»', lg['iEv'] != -1)
    check('C7: секция «Обозначения в шахматке»', lg['iNote'] != -1)
    check('C8: коды из справочника (Д/Н/ОТ)', lg['hasD'] and lg['hasN'] and lg['hasOT'])
    check('C9: И — в секции мероприятий (после заголовка)', lg['iEv'] < lg['txt'].find('Инструктаж'))
    check('C10: свотчи цветов (≥6 кодов)', lg['swatches'] >= 6, lg['swatches'])
    check('C11: панель в границах экрана',
          lg['rect']['right'] <= 1280 and lg['rect']['left'] >= 300)

    # ---------- D: закрытие повторным кликом ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(700)
    lg2 = page.evaluate(LEGEND_JS)
    check('D1: класс ws-legend-open снят', not lg2['open'])
    check('D2: aria-pressed=false', lg2['pressed'] == 'false', lg2['pressed'])

    # ---------- E: взаимоисключение с итогами ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    lg3 = page.evaluate(LEGEND_JS)
    tt_open = page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')")
    check('E1: открытие итогов закрыло легенду', not lg3['open'])
    check('E2: итоги открыты', tt_open)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(600)
    tt_head = page.evaluate("(document.querySelector('#wsTtBody .ws-tt-emp-head') || {}).textContent")
    check('E3: итоги — шапка «Работник» (переименование)', tt_head == 'Работник', tt_head)

    # ---------- F: карточка АДМИНА — read-only ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    card = page.evaluate(CARD_JS)
    check('F1: карточка открылась', card['open'])
    check('F2: НЕТ «Правка данных…»', card['editData'] == -1)
    check('F3: НЕТ «Уволить…»', card['dismiss'] == -1)
    check('F4: НЕТ «+ Отпуск…»', card['addVac'] == -1)
    check('F5: НЕТ «+ Мероприятие…»', card['addTr'] == -1)
    check('F6: НЕТ ✎/✕ у отпусков/мероприятий', card['acts'] == 0, card['acts'])
    check('F7: данные в карточке (профиль/отпуск/мероприятие)',
          'Иванов' in card['txt'] and 'Отпуска' in card['txt'] and 'Мероприятия' in card['txt'])
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)

    # ---------- G: страница «Работники» ----------
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(700)
    wp = page.evaluate(WORKERS_JS)
    check('G1: страница активна', wp['active'])
    check('G2: заголовок «Работники» (крошки …/Табель/Работники)',
          wp['title'].endswith('Работники'), wp['title'])
    check('G3: счётчик «2 работника»', '2' in wp['count'] and 'работник' in wp['count'], wp['count'])
    check('G4: две карточки', wp['n'] == 2, wp['n'])
    check('G5: карточка с «Правка данных…»', wp['firstHasEdit'])
    check('G6: карточка с «Уволить…»', wp['firstHasDismiss'])
    check('G7: карточка с «+ Отпуск…»', wp['firstHasAddVac'])
    check('G8: карточка с «+ Мероприятие…»', wp['firstHasAddTr'])
    check('G9: ✎/✕ в карточке (отпуск+мероприятие ≥4)', wp['firstActs'] >= 4, wp['firstActs'])
    page.screenshot(path='/tmp/t385-proof-workers-page.png', full_page=False)

    # ---------- H: «+» шапки страницы → «Новый работник» ----------
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
    check('H1: шторка создания открыта', h_state['active'])
    check('H2: заголовок «Новый работник»', h_state['title'] == 'Новый работник', h_state['title'])
    check('H3: кнопка «Добавить», таб. № вводится',
          h_state['btn'] == 'Добавить' and h_state['ro'] is False)
    # Esc НЕ закрывает bottom-sheet — закрытие кнопкой «Отмена»
    page.click('#wsEmpSheet .flow-input-cancel')
    page.wait_for_timeout(600)

    # ---------- I: «Правка данных…» со страницы ----------
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
    check('I1: шторка правки открыта', i_state['active'])
    check('I2: «Правка работника»', i_state['title'] == 'Правка работника', i_state['title'])
    check('I3: таб. № 017 readonly (PK)', i_state['tab'] == '017' and i_state['ro'] is True)
    check('I4: ФИО префиллен', i_state['fio'] == 'Иванов Иван Иванович', i_state['fio'])
    page.fill('#wsEmpFio', 'Иванов Иван Иванович (ст.)')
    page.click('#wsEmpSubmitBtn')
    page.wait_for_timeout(1500)
    upd = [c for c in API_CALLS if c[0] == 'updateEmployee']
    check('I5: updateEmployee вызван (таб. № из состояния)',
          len(upd) == 1 and str(upd[0][1].get('таб_номер')) == '017', upd[:1])
    check('I6: payload — новое ФИО', upd and upd[0][1].get('ФИО') == 'Иванов Иван Иванович (ст.)')
    toast_i = page.evaluate("document.getElementById('toastMessage').textContent")
    check('I7: тост «Данные работника обновлены»', 'Данные работника обновлены' in toast_i, toast_i)
    wp2 = page.evaluate(WORKERS_JS)
    check('I8: страница перерисована с новым ФИО',
          '(ст.)' in wp2['firstFio'], wp2['firstFio'])

    # ---------- J: ✎ отпуска со страницы ----------
    page.click('#wsWorkersBody .ws-wcard .ws-emp-field .ws-popup-act:not(.ws-popup-act-del)')
    page.wait_for_timeout(700)
    j_state = page.evaluate("""(function(){
        var t = document.getElementById('wsVacSheetTitle');
        return { active: document.getElementById('wsVacSheet').classList.contains('active'),
                 title: t ? t.textContent : '',
                 start: document.getElementById('wsVacStart').value };
    })()""")
    check('J1: «Правка отпуска» открыта', j_state['active'])
    check('J2: заголовок «Правка отпуска»', j_state['title'] == 'Правка отпуска', j_state['title'])
    check('J3: даты префиллены', j_state['start'] == '%04d-%02d-01' % (Y, M), j_state['start'])
    page.fill('#wsVacEnd', '%04d-%02d-15' % (Y, M))
    page.click('#wsVacSubmitBtn')
    page.wait_for_timeout(1500)
    upd_v = [c for c in API_CALLS if c[0] == 'updateVacation']
    check('J4: updateVacation (id=201, новый конец)',
          len(upd_v) == 1 and upd_v[0][1].get('id') == 201 and
          upd_v[0][1].get('дата_окончания') == '%04d-%02d-15' % (Y, M), upd_v[:1])

    # ---------- K: «+ Мероприятие…» со страницы ----------
    page.click('#wsWorkersBody .ws-wcard .ws-emp-addtr')
    page.wait_for_timeout(700)
    k_state = page.evaluate("""(function(){
        var t = document.getElementById('wsTrSheetTitle');
        return { active: document.getElementById('wsTrSheet').classList.contains('active'),
                 title: t ? t.textContent : '',
                 tab: document.getElementById('wsTrTabNo').value };
    })()""")
    check('K1: шторка мероприятия открыта', k_state['active'])
    check('K2: title «Новое мероприятие»', k_state['title'] == 'Новое мероприятие')
    check('K3: сотрудник 017 префиллен', k_state['tab'] == '017', k_state['tab'])
    page.click('#wsTrSheet .flow-input-cancel')
    page.wait_for_timeout(600)

    # ---------- L: шапка «Работник +» → страница ----------
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    page.click('.ws-grid thead th.ws-emp-col.ws-emp-head-add')
    page.wait_for_timeout(700)
    wp3 = page.evaluate(WORKERS_JS)
    check('L1: клик шапки «Работник +» → страница «Работники»', wp3['active'])
    check('M: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
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
    check('N2: зритель: шапка сетки БЕЗ плюса/клика',
          page2.evaluate("!document.querySelector('.ws-grid thead th.ws-emp-col.ws-emp-head-add')"))
    page2.click('td.ws-emp-col[data-tab="017"]')
    page2.wait_for_timeout(600)
    card2 = page2.evaluate(CARD_JS)
    check('N3: зритель: карточка без кнопок (как прежде)',
          card2['open'] and card2['editData'] == -1 and card2['acts'] == 0)
    # легенда доступна ВСЕМ уровням
    page2.keyboard.press('Escape')
    page2.wait_for_timeout(300)
    page2.click('#wsLegendBtn')
    page2.wait_for_timeout(700)
    lg4 = page2.evaluate(LEGEND_JS)
    check('O1: зритель: кнопка «Легенда» работает', lg4['open'] and lg4['visible'])
    check('O2: зритель: контент легенды полный', lg4['iDays'] != -1 and lg4['hasD'])
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
        var r = d.getBoundingClientRect();
        return { open: document.getElementById('page-work-schedule').classList.contains('ws-legend-open'),
                 left: r.left, right: r.right, top: r.top, bottom: r.bottom };
    })()""")
    check('Q1: мобайл: легенда открыта (fixed-оверлей)', lm['open'])
    check('Q2: мобайл: шторка в границах вьюпорта',
          lm['left'] >= 0 and lm['right'] <= 375 and lm['top'] >= 0 and lm['bottom'] <= 700, lm)
    page3.screenshot(path='/tmp/t385-proof-mobile-legend.png', full_page=False)
    page3.click('#wsLegendBtn')
    page3.wait_for_timeout(600)

    page3.click('#wsWorkersBtn')
    page3.wait_for_timeout(700)
    wm = page3.evaluate(WORKERS_JS)
    check('R1: мобайл: страница «Работники» активна', wm['active'])
    check('R2: мобайл: карточки в границах (2 шт)',
          wm['n'] == 2 and page3.evaluate("(function(){var b=document.getElementById('wsWorkersBody').getBoundingClientRect();return b.left>=0&&b.right<=375;})()"))
    page3.screenshot(path='/tmp/t385-proof-mobile-workers.png', full_page=False)
    check('S: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
