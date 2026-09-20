#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 384: browser-check — заявка пользователя: «В Табеле учёта
# рабочего времени, в карточках сотрудников добавь функционал
# редактирования данных сотрудника, отпусков и мероприятий по
# отдельности, с возможностью добавления и удаления информации,
# по которой будет строиться шахматка табеля на месяц и на год».
# ДЕСКТОП 1280 (тёмная, Админ=workschedule.edit):
#   A   страница загрузилась; B график открыт;
#   C   карточка: «Правка данных…» (до «Уволить…»), ✎/✕ у отпусков,
#       «+ Отпуск…» жив (регресс), «+ Мероприятие…», ✎/✕ мероприятия
#       живы (регресс Task 309);
#   D   «Правка данных…»: шторка active, title «Правка сотрудника»,
#       кнопка «Сохранить», таб. № readOnly + значение, поля
#       префиллены, карточка закрыта (z 9401 > 201);
#   E   смена ФИО → Сохранить → updateEmployee(таб_№ из состояния,
#       новое ФИО), шторка закрыта, тост «Данные сотрудника
#       обновлены», сетка перерисована с новым ФИО;
#   F   ✕ отпуска → kipConfirm OK → deleteVacation(id), тост
#       «Период отпуска удалён»;
#   G   ✎ отпуска → шторка «Правка отпуска», «Сохранить», поля
#       записи (часть/даты/комментарий/сотрудник);
#   H   смена дат → Сохранить → updateVacation(id, даты, часть),
#       тост «Период отпуска обновлён»;
#   I   «+ Мероприятие…» → шторка мероприятия, сотрудник префиллен,
#       title «Новое мероприятие»;
#   J   «Сотрудник +» (шапка сетки): режим СОЗДАНИЯ — «Новый
#       сотрудник»/«Добавить», таб. № вводится (readOnly=false);
#   K   0 JS-ошибок.
# ДЕСКТОП 1280 (зритель workschedule.view — Task 340 регресс):
#   L   карточка открывается, НЕТ «Правка данных…»/«Уволить…»/
#       «+ Отпуск…»/«+ Мероприятие…»/✎/✕; M 0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ):
#   N   карточка открывается, «Правка данных…» кликабельна → шторка
#       в границах вьюпорта; O ✎ отпуска открывает правку; P 0 ошибок.
# Порт 8994.
import calendar, datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8994
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
                      body='not found (t384-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t384-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

CARD_JS = """(function(){
    var pp = document.getElementById('wsEmpPopup');
    if (!pp) return { open: false };
    var txt = pp.textContent;
    function q(sel){ return pp.querySelector(sel); }
    function qa(sel){ return pp.querySelectorAll(sel); }
    return {
        open: pp.classList.contains('active'),
        txt: txt,
        editData: q('.ws-emp-editdata'),
        dismiss: q('.ws-emp-dismiss'),
        addVac: q('.ws-emp-addvac'),
        addTr: q('.ws-emp-addtr'),
        vacActs: qa('.ws-emp-field .ws-popup-act:not(.ws-popup-act-del)').length,
        vacDels: qa('.ws-emp-field .ws-popup-act-del').length,
        trActs: qa('.ws-popup-event .ws-popup-act:not(.ws-popup-act-del)').length,
        trDels: qa('.ws-popup-event .ws-popup-act-del').length,
        iEdit: txt.indexOf('Правка данных…'),
        iDismiss: txt.indexOf('Уволить…'),
        iAddVac: txt.indexOf('+ Отпуск…'),
        iAddTr: txt.indexOf('+ Мероприятие…'),
        vacRows: qa('.ws-emp-field').length
    };
})()"""

EMP_SHEET_JS = """(function(){
    var sh = document.getElementById('wsEmpSheet');
    var ov = document.getElementById('wsEmpOverlay');
    var t = document.getElementById('wsEmpSheetTitle');
    var b = document.getElementById('wsEmpSubmitBtn');
    var pp = document.getElementById('wsEmpPopup');
    return {
        sheet: sh.classList.contains('active'),
        overlay: ov.classList.contains('active'),
        cardClosed: !pp.classList.contains('active'),
        title: t ? t.textContent : '',
        btn: b ? b.textContent : '',
        tabNo: document.getElementById('wsEmpTabNo').value,
        tabRo: document.getElementById('wsEmpTabNo').readOnly,
        fio: document.getElementById('wsEmpFio').value,
        type: document.getElementById('wsEmpType').value,
        shift: document.getElementById('wsEmpShift').value,
        start: document.getElementById('wsEmpStart').value,
        hire: document.getElementById('wsEmpHire').value,
        pos: document.getElementById('wsEmpPosition').value,
        comment: document.getElementById('wsEmpComment').value
    };
})()"""

VAC_SHEET_JS = """(function(){
    var sh = document.getElementById('wsVacSheet');
    var t = document.getElementById('wsVacSheetTitle');
    var b = document.getElementById('wsVacSubmitBtn');
    var pp = document.getElementById('wsEmpPopup');
    return {
        sheet: sh.classList.contains('active'),
        cardClosed: !pp.classList.contains('active'),
        title: t ? t.textContent : '',
        btn: b ? b.textContent : '',
        tabNo: document.getElementById('wsVacTabNo').value,
        part: document.getElementById('wsVacPart').value,
        start: document.getElementById('wsVacStart').value,
        end: document.getElementById('wsVacEnd').value,
        comment: document.getElementById('wsVacComment').value,
        daysInfo: document.getElementById('wsVacDaysInfo').textContent,
        yearInfo: document.getElementById('wsVacYearInfo').textContent
    };
})()"""

TR_SHEET_JS = """(function(){
    var sh = document.getElementById('wsTrSheet');
    var t = document.getElementById('wsTrSheetTitle');
    var pp = document.getElementById('wsEmpPopup');
    return {
        sheet: sh.classList.contains('active'),
        cardClosed: !pp.classList.contains('active'),
        title: t ? t.textContent : '',
        tabNo: document.getElementById('wsTrTabNo').value
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
    check('B: график открыт, сетка отрисована',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length >= 2"))

    # ---------- C: карточка — все три блока правки ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    card = page.evaluate(CARD_JS)
    check('C1: карточка открылась', card['open'])
    check('C2: «Правка данных…» в профиле (ws-emp-editdata)',
          bool(card['editData']) and card['iEdit'] != -1)
    check('C3: «Правка данных…» ВЫШЕ «Уволить…»',
          card['iEdit'] != -1 and card['iDismiss'] != -1 and card['iEdit'] < card['iDismiss'])
    check('C4: ✎/✕ у периодов отпусков (2 периода)',
          card['vacActs'] == 2 and card['vacDels'] == 2, (card['vacActs'], card['vacDels']))
    check('C5: «+ Отпуск…» жив (регресс Task 312)',
          bool(card['addVac']) and card['iAddVac'] != -1)
    check('C6: «+ Мероприятие…» в блоке мероприятий (ws-emp-addtr)',
          bool(card['addTr']) and card['iAddTr'] != -1)
    check('C7: ✎/✕ мероприятия живы (регресс Task 309)',
          card['trActs'] >= 1 and card['trDels'] >= 1, (card['trActs'], card['trDels']))
    page.screenshot(path='scripts/task384-proof-card.png', full_page=False)

    # ---------- D: «Правка данных…» — шторка режима правки ----------
    page.click('#wsEmpPopup .ws-emp-editdata')
    page.wait_for_timeout(700)
    es = page.evaluate(EMP_SHEET_JS)
    check('D1: шторка+оверлей открыты, карточка закрыта',
          es['sheet'] and es['overlay'] and es['cardClosed'])
    check('D2: заголовок «Правка сотрудника», кнопка «Сохранить»',
          es['title'] == 'Правка сотрудника' and es['btn'] == 'Сохранить',
          (es['title'], es['btn']))
    check('D3: таб. № readOnly со значением 017 (PK)',
          es['tabRo'] and es['tabNo'] == '017')
    check('D4: поля префиллены (ФИО/тип/смена/старт/приём/должность/комментарий)',
          es['fio'] == 'Иванов Иван Иванович' and es['type'] == 'сменный' and
          es['shift'] == '1' and es['start'] == '%04d-%02d-01' % (Y, M) and
          es['hire'] == '2024-03-15' and es['pos'] == 'Слесарь КИПиА' and
          es['comment'] == 'бригада А', (es['fio'], es['type'], es['shift'], es['pos']))
    page.screenshot(path='scripts/task384-proof-emp-edit-sheet.png', full_page=False)

    # ---------- E: сохранить правку данных ----------
    page.fill('#wsEmpFio', 'Иванов Иван Иванович (ст.)')
    # должность — <select> (Task 318): временная опция правки уже выбрана,
    # явный выбор той же опции из подгруженного списка
    page.select_option('#wsEmpPosition', label='Слесарь КИПиА')
    page.click('#wsEmpSubmitBtn')
    page.wait_for_timeout(1800)
    upd = [c for c in API_CALLS if c[0] == 'updateEmployee']
    toast = page.evaluate("document.getElementById('toastMessage').textContent")
    check('E1: updateEmployee вызван (таб. № из состояния)',
          len(upd) == 1 and upd[0][1].get('таб_номер') == '017', upd)
    check('E2: payload — новое ФИО',
          len(upd) == 1 and upd[0][1].get('ФИО') == 'Иванов Иван Иванович (ст.)')
    check('E3: шторка закрыта после успеха',
          not page.evaluate("document.getElementById('wsEmpSheet').classList.contains('active')"))
    check('E4: тост «Данные сотрудника обновлены»',
          'Данные сотрудника обновлены' in toast, toast)
    grid_fio = page.evaluate("document.querySelector('#page-work-schedule .ws-grid').textContent")
    check('E5: сетка перерисована с новым ФИО',
          'Иванов Иван Иванович (ст.)' in grid_fio)

    # ---------- F: ✕ отпуска → подтверждение → deleteVacation ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-field .ws-popup-act-del >> nth=1')
    page.wait_for_timeout(500)
    check('F1: kipConfirm открыт',
          page.evaluate("!!document.querySelector('.kip-dialog')"))
    page.click('.kip-dialog-ok')
    page.wait_for_timeout(1800)
    dels = [c for c in API_CALLS if c[0] == 'deleteVacation']
    toast = page.evaluate("document.getElementById('toastMessage').textContent")
    check('F2: deleteVacation вызван с id=202 (второй период)',
          len(dels) == 1 and dels[0][1].get('id') == 202, dels)
    check('F3: тост «Период отпуска удалён»',
          'Период отпуска удалён' in toast, toast)

    # ---------- G: ✎ отпуска → шторка режима правки ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-field .ws-popup-act:not(.ws-popup-act-del)')
    page.wait_for_timeout(700)
    vs = page.evaluate(VAC_SHEET_JS)
    check('G1: шторка отпуска открыта, карточка закрыта',
          vs['sheet'] and vs['cardClosed'])
    check('G2: заголовок «Правка отпуска», кнопка «Сохранить»',
          vs['title'] == 'Правка отпуска' and vs['btn'] == 'Сохранить',
          (vs['title'], vs['btn']))
    check('G3: поля записи (сотрудник/часть/даты/комментарий)',
          vs['tabNo'] == '017' and vs['part'] == '1' and
          vs['start'] == '%04d-%02d-01' % (Y, M) and
          vs['end'] == '%04d-%02d-10' % (Y, M) and vs['comment'] == 'лето',
          (vs['tabNo'], vs['part'], vs['start'], vs['end'], vs['comment']))
    check('G4: строка лимита без своей строки (0 запланировано)',
          'запланировано 0 из 42' in vs['yearInfo'], vs['yearInfo'])
    page.screenshot(path='scripts/task384-proof-vac-edit-sheet.png', full_page=False)

    # ---------- H: сменить даты → updateVacation ----------
    page.fill('#wsVacStart', '%04d-%02d-05' % (Y, M))
    page.fill('#wsVacEnd', '%04d-%02d-15' % (Y, M))
    page.wait_for_timeout(300)
    upd_v = [c for c in API_CALLS if c[0] == 'updateVacation']
    check('H1: до сохранения updateVacation не вызван', len(upd_v) == 0)
    page.click('#wsVacSubmitBtn')
    page.wait_for_timeout(1800)
    upd_v = [c for c in API_CALLS if c[0] == 'updateVacation']
    toast = page.evaluate("document.getElementById('toastMessage').textContent")
    check('H2: updateVacation вызван (id=201, новые даты, часть 1)',
          len(upd_v) == 1 and upd_v[0][1].get('id') == 201 and
          upd_v[0][1].get('дата_начала') == '%04d-%02d-05' % (Y, M) and
          upd_v[0][1].get('дата_окончания') == '%04d-%02d-15' % (Y, M) and
          upd_v[0][1].get('часть') == 1, upd_v)
    check('H3: тост «Период отпуска обновлён»',
          'Период отпуска обновлён' in toast, toast)
    check('H4: шторка закрыта после успеха',
          not page.evaluate("document.getElementById('wsVacSheet').classList.contains('active')"))

    # ---------- I: «+ Мероприятие…» — префилл сотрудника ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-addtr')
    page.wait_for_timeout(700)
    trs = page.evaluate(TR_SHEET_JS)
    check('I1: шторка мероприятия открыта, карточка закрыта',
          trs['sheet'] and trs['cardClosed'])
    check('I2: title «Новое мероприятие», сотрудник 017 префиллен',
          trs['title'] == 'Новое мероприятие' and trs['tabNo'] == '017',
          (trs['title'], trs['tabNo']))
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(300)

    # ---------- J: «Сотрудник +» — режим создания ----------
    page.click('.ws-grid thead th.ws-emp-col.ws-emp-head-add')
    page.wait_for_timeout(700)
    js_add = page.evaluate(EMP_SHEET_JS)
    check('J1: режим СОЗДАНИЯ: «Новый сотрудник»/«Добавить»',
          js_add['title'] == 'Новый сотрудник' and js_add['btn'] == 'Добавить',
          (js_add['title'], js_add['btn']))
    check('J2: таб. № вводится (readOnly=false, поле пустое)',
          not js_add['tabRo'] and js_add['tabNo'] == '')
    page.evaluate("WorkSchedule.closeEmployeeForm()")
    page.wait_for_timeout(300)

    check('K: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 2: зритель (workschedule.view) ============
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'dark', 'viewer', viewer=True)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('td.ws-emp-col[data-tab="017"]')
    page2.wait_for_timeout(600)
    card2 = page2.evaluate(CARD_JS)
    check('L1: зритель: карточка ОТКРЫВАЕТСЯ (Task 340)', card2['open'])
    check('L2: НЕТ «Правка данных…»',
          not card2['editData'] and card2['iEdit'] == -1)
    check('L3: НЕТ ✎/✕ у отпусков и мероприятий',
          card2['vacActs'] == 0 and card2['vacDels'] == 0 and
          card2['trActs'] == 0 and card2['trDels'] == 0,
          (card2['vacActs'], card2['vacDels'], card2['trActs'], card2['trDels']))
    check('L4: НЕТ «+ Отпуск…»/«+ Мероприятие…»/«Уволить…» (регресс)',
          card2['iAddVac'] == -1 and card2['iAddTr'] == -1 and card2['iDismiss'] == -1)
    check('M: 0 JS-ошибок (зритель)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ============ Контекст 3: мобильный 375, светлая, Админ ============
    ctx3 = browser.new_context(viewport={'width': 375, 'height': 700},
                                has_touch=True, is_mobile=True)
    page3 = ctx3.new_page()
    js_errors3 = attach(page3, ctx3, 'light', 'mobile')

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.tap('td.ws-emp-col[data-tab="017"]')
    page3.wait_for_timeout(600)
    card3 = page.evaluate if False else page3.evaluate(CARD_JS)
    check('N1: мобайл: карточка открылась, «Правка данных…» видна',
          card3['open'] and card3['iEdit'] != -1)
    page3.tap('#wsEmpPopup .ws-emp-editdata')
    page3.wait_for_timeout(700)
    box = page3.evaluate("""(function(){
        var sh = document.getElementById('wsEmpSheet').getBoundingClientRect();
        return { left: sh.left, right: sh.right, top: sh.top,
                 active: document.getElementById('wsEmpSheet').classList.contains('active'),
                 vw: window.innerWidth, title: document.getElementById('wsEmpSheetTitle').textContent };
    })()""")
    check('N2: мобайл: шторка правки в границах вьюпорта',
          box['active'] and box['left'] >= 0 and box['right'] <= box['vw'] + 1,
          box)
    check('N3: мобайл: заголовок «Правка сотрудника»',
          box['title'] == 'Правка сотрудника', box['title'])
    page3.screenshot(path='scripts/task384-proof-mobile-sheet.png', full_page=False)
    page3.evaluate("WorkSchedule.closeEmployeeForm()")
    page3.wait_for_timeout(400)

    page3.tap('td.ws-emp-col[data-tab="017"]')
    page3.wait_for_timeout(600)
    page3.tap('#wsEmpPopup .ws-emp-field .ws-popup-act:not(.ws-popup-act-del)')
    page3.wait_for_timeout(700)
    mv = page3.evaluate("""(function(){
        var t = document.getElementById('wsVacSheetTitle');
        return { active: document.getElementById('wsVacSheet').classList.contains('active'),
                 title: t ? t.textContent : '',
                 start: document.getElementById('wsVacStart').value };
    })()""")
    check('O1: мобайл: ✎ отпуска открывает «Правка отпуска»',
          mv['active'] and mv['title'] == 'Правка отпуска' and
          mv['start'] == '%04d-%02d-05' % (Y, M),
          mv)
    check('P: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
