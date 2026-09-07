# -*- coding: utf-8 -*-
# Task 337: browser-check — заявка пользователя:
#   «установил роли "КИП ИОС дежурный" доступ "График работы — просмотр",
#    а показываются кнопки "Сформировать" и "Вид" и доступно редактирование».
# ФИКС: право записи — из серверной матрицы (workschedule.edit);
# зритель (edit=✗) — без «Сформировать», клик по ячейке — только окно
# мероприятий. Task 340 (адаптация): зритель — УРОВЕНЬ 'view':
# «Вид» видна (просмотр), сохранённый вид подхватывается; редактор
# (edit=✓) — всё живо; дежурный-редактор — замок.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной','color':'#EEF0F2'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
]

# STATE: роль + наличие workschedule.edit в матрице
STATE = {'role': 'КИП ИОС дежурный', 'ws_edit': False}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':STATE['role'],'found':True,
                'permissions':{'workschedule.view':True,
                               'workschedule.edit':STATE['ws_edit']}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def setup_ctx(browser, viewport, token, theme=None, role='КИП ИОС дежурный', ws_edit=False, dsf=1):
    STATE['role'] = role
    STATE['ws_edit'] = ws_edit
    ctx = browser.new_context(viewport=viewport, device_scale_factor=dsf)
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
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
                      body=json.dumps(mock_response(action, body), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t337)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    # сохранённый «сменный» вид (ловля регресса: зритель не должен
    # подхватывать чужой/старый сохранённый вид)
    page.evaluate("localStorage.setItem('kip8_ws_view_v1','shift')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

def goto_tab_mobile(page):
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1400)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========= Контекст 1: мобильный 375 — ЗРИТЕЛЬ «КИП ИОС дежурный» =========
    print('=== Контекст 1: мобильный 375, «КИП ИОС дежурный», матрица edit=✗ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t337-viewer',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=False, dsf=3)
    goto_tab_mobile(page)

    # --- 1) кнопки «Сформировать» и «Вид» скрыты ---
    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 genW: gen.offsetWidth, viewW: view.offsetWidth,
                 saveHidden: document.getElementById('wsSaveBtn').hidden };
    })()""")
    check('M1: «Сформировать» скрыта (hidden, ширина 0)',
          st['genHidden'] and st['genW'] == 0, st)
    check('M2: «Вид» ВИДНА уровню view (Task 340, ширина > 0)',
          (not st['viewHidden']) and st['viewW'] > 0, st)

    # --- 2) зритель — СОХРАНЁННЫЙ вид 'shift' (Task 340: зритель
    #     подхватывает сохранённый вид, как редактор; setup ставит shift) ---
    rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('M3: сохранённый вид shift применён — 1 строка (Task 340)',
          rows == 1, rows)
    locked = page.evaluate("""(function(){
        var b = document.getElementById('wsViewBtn');
        return { locked: b.classList.contains('ws-view-locked'),
                 aria: b.getAttribute('aria-label') };
    })()""")
    check('M4: замка НЕТ (роль не редактор — без приглушения)',
          not locked['locked'], locked)
    check('M5: aria «сейчас сменный» (Task 338)', 'сменный' in locked['aria'], locked)

    # --- 3) клик по ячейке — ТОЛЬКО окно мероприятий (окно кодов нет) ---
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pops = page.evaluate("""(function(){
        return { ev: document.getElementById('wsEventsPopup').classList.contains('active'),
                 cell: document.getElementById('wsCellPopup').classList.contains('active') };
    })()""")
    check('M6: клик по ячейке → окно «Мероприятия в этот день»', pops['ev'], pops)
    check('M7: окно выбора кодов НЕ открыто (правки нет)', not pops['cell'], pops)
    page.evaluate("WorkSchedule.closeCellPopup()")

    # --- 4) заголовок «Сотрудник +» без плюса-клика (не редактор) ---
    head = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap thead th.ws-emp-col');
        return { add: th.classList.contains('ws-emp-head-add') };
    })()""")
    check('M8: заголовок сотрудников НЕ кликабелен (без +)', not head['add'], head)

    # --- 5) «Вид» работает у зрителя (Task 340): shift → day ---
    page.evaluate("WorkSchedule.cycleView()")
    page.wait_for_timeout(300)
    vw = page.evaluate("WorkSchedule._view")
    check('M9: cycleView зрителя переключает вид (shift → day)',
          vw == 'day', vw)
    page.evaluate("WorkSchedule.cycleView()")   # day → full (2 строки)
    page.wait_for_timeout(300)

    check('M10: 0 JS-ошибок (зритель)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 2: мобильный — РЕДАКТОР «КИП ИОС» (edit=✓) =========
    print('=== Контекст 2: мобильный 375, «КИП ИОС», матрица edit=✓ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t337-editor',
                                     theme='dark', role='КИП ИОС', ws_edit=True, dsf=3)
    goto_tab_mobile(page)

    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 genW: gen.offsetWidth, viewW: view.offsetWidth };
    })()""")
    check('E1: «Сформировать» ВИДНА (hidden=false, ширина > 0)',
          (not st['genHidden']) and st['genW'] > 0, st)
    check('E2: «Вид» ВИДНА (hidden=false, ширина > 0)',
          (not st['viewHidden']) and st['viewW'] > 0, st)

    # переключение вида работает: полный → сменный (строк меньше)
    page.evaluate("WorkSchedule._view = 'full'; WorkSchedule._applyView({ rerender: true });")
    page.wait_for_timeout(400)
    before = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    page.evaluate("WorkSchedule.cycleView()")
    page.wait_for_timeout(500)
    after = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('E3: cycleView переключает вид (2 → 1 строка сменных)',
          before == 2 and after == 1, (before, after))

    # клик по ячейке — окно КОДОВ (правка доступна)
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pops = page.evaluate("document.getElementById('wsCellPopup').classList.contains('active')")
    check('E4: клик по ячейке → окно выбора кодов (редактор)', pops, pops)
    page.evaluate("WorkSchedule.closeCellPopup()")

    check('E5: 0 JS-ошибок (редактор)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 3: дежурный-РЕДАКТОР (edit=✓) — замок жив =========
    print('=== Контекст 3: мобильный 375, «КИП ИОС дежурный», матрица edit=✓ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t337-duty',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=True, dsf=3)
    goto_tab_mobile(page)

    st = page.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        return { viewHidden: view.hidden,
                 locked: view.classList.contains('ws-view-locked') };
    })()""")
    rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('D1: кнопка «Вид» видна + ЗАМОК (приглушена)',
          (not st['viewHidden']) and st['locked'], st)
    check('D2: вид заперт — только сменные (1 строка)', rows == 1, rows)
    check('D3: 0 JS-ошибок (дежурный-редактор)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 4: ДЕСКТОП 1280 — зритель, ряд 3 без кнопок =========
    print('=== Контекст 4: десктоп 1280, «КИП ИОС дежурный», edit=✗ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t337-desk',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=False)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        var row = document.getElementById('wsActionsRow');
        var rr = row.getBoundingClientRect();
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 genW: gen.offsetWidth, viewW: view.offsetWidth,
                 rowH: Math.round(rr.height * 10) / 10,
                 crossVisible: !document.getElementById('wsCrossBtn').hidden };
    })()""")
    check('K1: десктоп: «Сформировать» скрыта',
          st['genHidden'] and st['genW'] == 0, st)
    check('K2: десктоп: «Вид» ВИДНА уровню view (Task 340)',
          (not st['viewHidden']) and st['viewW'] > 0, st)
    check('K3: десктоп: ряд действий 3 держит высоту (~29.7px, сетка не прыгает)',
          26 <= st['rowH'] <= 33, st)
    check('K4: десктоп: подсветка осталась (фича просмотра)', st['crossVisible'], st)
    rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('K5: десктоп: сменный вид (1 строка, Task 338)', rows == 1, rows)
    check('K6: 0 JS-ошибок (десктоп-зритель)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print('──────────────────────────────')
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
