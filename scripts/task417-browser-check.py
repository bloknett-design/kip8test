#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 417: browser-check — заявка «В блоках карт работников названия
# должны отображаться в полном виде. Попап по фамилии - убери полностью
# окно, теперь все подробные данные можно посмотреть в картах
# работников. Пытаюсь зайти в редактирование записи до 1000В у
# Федосова за 2025 год, не заходит и сообщение "Мероприятие не найдено
# — обновите график"…».
# ПРОВЕРКИ (мок-сервер, порт 8918; запись 2025 ТОЛЬКО в instrAll —
# сценарий бага, в годовом срезе trainings её нет):
#   1) десктоп 1280 тёмная, edit, живой лист с сокращениями:
#      клик по фамилии → попапа НЕТ (#wsEmpPopup отсутствует, ни одно
#      окно не active), td без onclick; карточка «Работники» — ПОЛНЫЕ
#      названия в блоках (сокращений нет), год ‹ 2025 → запись «до
#      1000 В», ✎ открывает «Правка инструктажа / проверки знаний»
#      с датой 2025-06-10 БЕЗ тоста «Мероприятие не найдено»; ✎
#      текущего года — прежний путь; регресс 416 — тултип бейджа и
#      окно дня с сокращением; кэш-путь после перезагрузки;
#   2) десктоп 1280 светлая, view: клик по фамилии — попапа нет,
#      карточка — полные названия, без ✎/✕;
#   3) мобайл 375 тёмная, edit: клик по фамилии — ничего, карточка —
#      полные названия, правка 2025 открывается.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8918
TODAY = datetime.date.today()
Y = TODAY.year

def d(y, m, day):
    return '%04d-%02d-%02d' % (y, m, day)

# названия канона + сокращения (живой лист «Список_И_и_ПЗ», столбец E)
N_OT = 'Повторный инструктаж по рабочим инструкциям ОТ'
N_EL = 'Периодическая проверка знаний на допуск к проведению работ в электроустановках до 1000 В'
S_OT = 'Инстр. ОТ'
S_EL = 'ПЗ ЭБ до 1000 В'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': d(Y, TODAY.month, 1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': d(Y, TODAY.month, 7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '', 'комментарий': ''},
]

# запись 2025 — ТОЛЬКО в архиве instrAll (сценарий заявки);
# запись текущего года — в обоих (срез + архив)
INSTR_ALL = [
  {'id': 501, 'таб_номер': '0871', 'тип': 'проверка_знаний', 'тема': N_EL,
   'дата_начала': '2025-06-10', 'дата_окончания': '2025-06-10',
   'длительность_дней': 1, 'комментарий': ''},
  {'id': 601, 'таб_номер': '0871', 'тип': 'инструктаж', 'тема': N_OT,
   'дата_начала': d(Y, TODAY.month, 15), 'дата_окончания': d(Y, TODAY.month, 15),
   'длительность_дней': 1, 'комментарий': ''},
]
TRAININGS = [dict(INSTR_ALL[1])]  # годовой срез сетки — записи 2025 в нём НЕТ
EVENTS_ALL = []
VACATIONS = []
PPE = []
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь'},
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082', 'short': 'день'},
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
INSTR_LIST = [
  {'название': N_OT, 'вид': 'инструктаж', 'периодичность': 6,
   'основание': '', 'сокращение': S_OT},
  {'название': N_EL, 'вид': 'проверка_знаний', 'периодичность': 12,
   'основание': '', 'сокращение': S_EL},
]

PASS = 0
FAIL = 0
ADMIN = True


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  + ' if ok else '  X ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if ADMIN else 'КИП ИОС'}}
    if action == 'getMyAccess':
        if ADMIN:
            perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                     'workschedule.view': True, 'workschedule.edit': True}
            role = 'Админ'
        else:
            perms = {'calc.view': True, 'library.view': True, 'kipios.view': True,
                     'workschedule.view': True, 'workschedule.edit': False,
                     'workschedule.view.min': False}
            role = 'КИП ИОС'
        return {'ok': True, 'data': {'role': role, 'found': True, 'permissions': perms}}
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
        return {'ok': True, 'data': {'trainings': list(TRAININGS),
                                    'instrList': list(INSTR_LIST),
                                    'instrAll': list(INSTR_ALL),
                                    'eventsAll': list(EVENTS_ALL)}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': list(VACATIONS)}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': list(PPE)}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.addTraining':
        return {'ok': True, 'data': {'id': 100}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, keep_cache=False):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    pre = ''
    if not keep_cache:
        pre += ("try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
                "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};")
    ctx.add_init_script(
        pre +
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t417-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

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
        resp = api_response(action, body)
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                              body=json.dumps(resp, ensure_ascii=False))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t417-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def open_workers_card(page, fio='Федосов А. В.'):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1500)
    page.click(".ws-wtabs button:has-text('%s')" % fio)
    page.wait_for_timeout(900)


NO_POPUP_JS = """(function(){
    return {
        empEl: !!document.getElementById('wsEmpPopup'),
        empCls: document.querySelectorAll('.ws-cell-popup.ws-emp-popup').length,
        activePopups: document.querySelectorAll('.ws-cell-popup.active').length,
        activeClosers: document.querySelectorAll('.ws-popup-closer.active').length
    };
})()"""


def click_surname(page, tab='0871'):
    page.click('td.ws-emp-col[data-tab="%s"]' % tab)
    page.wait_for_timeout(800)
    return page.evaluate(NO_POPUP_JS)


def instr_block(page):
    """блок «Повторные инструктажи…» открытой карточки"""
    return page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1)
            return {text: cards[i].innerText, html: cards[i].innerHTML,
                    head: h.textContent};
    }
    return {text: '', html: '', head: ''};
})()""")


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========== Контекст 1: десктоп 1280, тёмная, edit, живой лист ==========
    print('=== Контекст 1: десктоп тёмная edit — попапа нет, полные названия, правка 2025 ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'main', keep_cache=True)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A1: приложение загрузилось',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)

    # --- заявка: клик по фамилии больше ничего не открывает ---
    st = click_surname(page)
    check('B1: ЗАЯВКА — попап по фамилии удалён (#wsEmpPopup нет)',
          st['empEl'] is False and st['empCls'] == 0, st)
    check('B2: ни одно окно не открылось кликом по фамилии',
          st['activePopups'] == 0 and st['activeClosers'] == 0, st)
    no_onclick = page.evaluate(
        "(function(){var td=document.querySelector('td.ws-emp-col[data-tab=\"0871\"]');"
        "return td ? td.getAttribute('onclick') : 'no-td';})()")
    check('B3: td.ws-emp-col без атрибута onclick', no_onclick is None, no_onclick)
    nop = page.evaluate("(function(){try{WorkSchedule.closeEmpPopup();return 'ok';}"
                        "catch(e){return 'err:'+e.message;}})()")
    check('B4: closeEmpPopup — безопасный no-op', nop == 'ok', nop)
    page.screenshot(path='task417-proof-grid-click-no-popup.png', full_page=False)

    # --- карточка «Работники»: полные названия в блоках ---
    open_workers_card(page)
    blk = instr_block(page)
    check('C1: ЗАЯВКА — блок инструктажей: ПОЛНОЕ название текущего года',
          (N_OT + ' · ') in blk['text'], blk['text'][:180])
    check('C2: сокращений в блоке НЕТ',
          (S_OT + ' · ') not in blk['text'] and (S_EL + ' · ') not in blk['text'],
          blk['text'][:180])
    check('C3: ✎/✕ в строках живы (правка архивов)',
          'WorkSchedule.editTraining(' in blk['html'] and
          'WorkSchedule.deleteTraining(' in blk['html'])
    page.screenshot(path='task417-proof-card-full-name.png', full_page=False)

    # --- год ‹ 2025: архивная запись «до 1000 В», правка открывается ---
    page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var b = cards[i].querySelector('.ws-ynav-btn:not(.ws-ynav-off)');
            if (b) { b.click(); return 'clicked'; }
            return 'no-btn';
        }
    }
    return 'no-card';
})()""")
    page.wait_for_timeout(900)
    blk25 = instr_block(page)
    check('D1: год блока сменился на 2025', '2025' in blk25['head'], blk25['head'])
    check('D2: архивная запись 2025 «до 1000 В» — ПОЛНОЕ название',
          (N_EL + ' · ') in blk25['text'], blk25['text'][:200])
    check('D3: сокращения архива нет', (S_EL + ' · ') not in blk25['text'],
          blk25['text'][:200])
    page.screenshot(path='task417-proof-card-2025.png', full_page=False)

    # ✎ записи 2025 — форма правки (прежний баг: «Мероприятие не найдено»)
    page.click(".ws-wgrid2 .ws-wcard .ws-popup-act[title='Редактировать']")
    page.wait_for_timeout(900)
    form = page.evaluate("""(function(){
    var sh = document.getElementById('wsTrSheet');
    return {
        open: sh ? sh.classList.contains('active') : false,
        title: (document.getElementById('wsTrSheetTitle') || {}).textContent || '',
        tema: (document.getElementById('wsTrTitleSel') || {}).value || '',
        date: (document.getElementById('wsTrStart') || {}).value || '',
        toast404: document.body.innerText.indexOf('Мероприятие не найдено') !== -1
    };
})()""")
    check('E1: ЗАЯВКА — правка записи 2025 открывает форму', form['open'], form)
    check('E2: заголовок «Правка инструктажа / проверки знаний»',
          form['title'] == 'Правка инструктажа / проверки знаний', form['title'])
    check('E3: тема записи — «до 1000 В» (select)', form['tema'] == N_EL, form['tema'])
    check('E4: дата проведения — 2025-06-10', form['date'] == '2025-06-10', form['date'])
    check('E5: тоста «Мероприятие не найдено» НЕТ', form['toast404'] is False, form['toast404'])
    page.screenshot(path='task417-proof-edit-2025-form.png', full_page=False)
    page.evaluate("WorkSchedule.closeTrainingForm && WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(500)

    # назад в 2026 — правка текущего года (регресс 309/411);
    # в 2025 стрелка ‹ погашена (min-год записей) — активна только ›
    page.evaluate("""(function(){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var h = cards[i].querySelector('.ws-whead-t');
        if (h && h.textContent.indexOf('Повторные инструктажи') !== -1) {
            var b = cards[i].querySelectorAll('.ws-ynav-btn:not(.ws-ynav-off)');
            if (b.length >= 1) { b[0].click(); return 'clicked'; }
            return 'no-btn';
        }
    }
    return 'no-card';
})()""")
    page.wait_for_timeout(900)
    blk26 = instr_block(page)
    check('F1: возврат в %d — запись текущего года' % Y,
          (N_OT + ' · ') in blk26['text'], blk26['head'])
    page.click(".ws-wgrid2 .ws-wcard .ws-popup-act[title='Редактировать']")
    page.wait_for_timeout(900)
    form2 = page.evaluate("""(function(){
    var sh = document.getElementById('wsTrSheet');
    var d = (document.getElementById('wsTrStart') || {}).value || '';
    return {open: sh ? sh.classList.contains('active') : false, date: d};
})()""")
    cur_year = '%d' % Y
    check('F2: правка записи текущего года — прежний путь (регресс)',
          form2['open'] and form2['date'].find(cur_year) == 0, form2)
    page.evaluate("WorkSchedule.closeTrainingForm && WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # --- регресс 416: компактные показы с сокращениями ---
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    ev = page.evaluate("""(function(){
    var badges = document.querySelectorAll('#wsGridWrap .ws-ev-badge');
    for (var i = 0; i < badges.length; i++) {
        var t = badges[i].getAttribute('title') || '';
        if (t.indexOf('И —') !== -1 || t.indexOf('Инстр') !== -1) {
            var cell = badges[i].closest('td.ws-cell');
            cell.click();
            return {title: t};
        }
    }
    return null;
})()""")
    check('G1: регресс 416 — тултип бейджа «И — Инстр. ОТ»',
          (ev or {}).get('title') == 'И — ' + S_OT, (ev or {}).get('title'))
    page.wait_for_timeout(700)
    day_text = page.evaluate("(document.getElementById('wsEventsPopup')||{}).innerText || ''")
    check('G2: регресс 416 — окно дня: сокращение',
          S_OT in day_text and N_OT not in day_text, day_text[:150])
    page.screenshot(path='task417-proof-day-window-short.png', full_page=False)
    page.evaluate("WorkSchedule.closeCellPopup && WorkSchedule.closeCellPopup()")
    page.wait_for_timeout(300)

    # --- кэш-путь: перезагрузка ---
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)
    st2 = click_surname(page)
    check('H1: кэш-путь — попап по фамилии по-прежнему удалён',
          st2['empEl'] is False and st2['activePopups'] == 0, st2)
    check('H2: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 2: десктоп 1280, светлая, view ==========
    print('=== Контекст 2: десктоп светлая view ===')
    ADMIN = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'view')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    st3 = click_surname(page)
    check('I1: view — попап по фамилии не открывается',
          st3['empEl'] is False and st3['activePopups'] == 0, st3)
    open_workers_card(page)
    blkv = instr_block(page)
    check('I2: view — блок инструктажей: ПОЛНОЕ название',
          (N_OT + ' · ') in blkv['text'], blkv['text'][:160])
    check('I3: view — кнопок правки нет',
          'WorkSchedule.editTraining(' not in blkv['html'])
    page.screenshot(path='task417-proof-card-light-view.png', full_page=False)
    check('I4: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    # ========== Контекст 3: мобайл 375, тёмная, edit ==========
    print('=== Контекст 3: мобайл 375 тёмная edit ===')
    ADMIN = True
    ctx = browser.new_context(viewport={'width': 375, 'height': 667})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mobile')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    st4 = click_surname(page)
    check('J1: мобайл — тап по фамилии ничего не открывает',
          st4['empEl'] is False and st4['activePopups'] == 0, st4)
    open_workers_card(page)
    blkm = instr_block(page)
    check('J2: мобайл — блок инструктажей: ПОЛНОЕ название',
          (N_OT + ' · ') in blkm['text'], blkm['text'][:160])
    page.screenshot(path='task417-proof-card-mobile.png', full_page=False)
    check('J3: JS-ошибок нет', not js_errors, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
exit(0 if FAIL == 0 else 1)
