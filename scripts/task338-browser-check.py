# -*- coding: utf-8 -*-
# Task 338: browser-check — заявка пользователя (продолжение Task 337):
#   «так же у роли "КИП ИОС дежурный" не должны быть видны кнопка
#    "Итоги учёта", шахматка дневного персонала, карточки сотрудников».
# ФИКС (Task 338, адаптировано Task 340 под трёхуровневую схему):
# зритель (workschedule.view без edit) — УРОВЕНЬ 'view': карточка ФИО
# открывается read-only (кнопок правки нет), «Вид»/«Итоги» видны в
# полном виде, клик по ячейке — окно мероприятий; редактор — как прежде;
# строгий уровень min — в task340-browser-check.py.
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

def setup_ctx(browser, viewport, token, theme=None, role='КИП ИОС дежурный', ws_edit=False, dsf=1, saved_view='day'):
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t338)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    # сохранённый вид: зрителю подсунут «дневной» (ловля регресса:
    # зритель НЕ подхватывает чужой вид — его вид «сменный»);
    # редактору — честное значение (какое задал вызов)
    if saved_view is None:
        page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    else:
        page.evaluate("localStorage.setItem('kip8_ws_view_v1','%s')" % saved_view)
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
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t338-viewer',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=False, dsf=3,
                                     saved_view=None)
    goto_tab_mobile(page)

    # --- 1) кнопки «Сформировать»/«Вид» скрыты (регресс Task 337) ---
    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 genW: gen.offsetWidth, viewW: view.offsetWidth };
    })()""")
    check('M1: «Сформировать» скрыта (регресс 337)',
          st['genHidden'] and st['genW'] == 0, st)
    check('M2: «Вид» ВИДНА уровню view (Task 340)',
          (not st['viewHidden']) and st['viewW'] > 0, st)

    # --- 2) «Итоги учёта» ВИДНА уровню view в полном виде (Task 340) ---
    st = page.evaluate("""(function(){
        var tb = document.getElementById('wsTotalsBtn');
        return { tbHidden: tb.hidden, tbW: tb.offsetWidth };
    })()""")
    check('M3: «Итоги учёта» ВИДНА уровню view (Task 340, полный вид)',
          (not st['tbHidden']) and st['tbW'] > 0, st)

    # --- 3) шахматка дневных скрыта: только сменные строки ---
    rows = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        var fios = [];
        trs.forEach(function(tr){
            var s = tr.querySelector('td.ws-emp-col .ws-emp-full');
            fios.push(s ? s.textContent : '');
        });
        return { n: trs.length, hasDay: fios.some(function(f){ return f.indexOf('Петров') !== -1; }),
                 hasShift: fios.some(function(f){ return f.indexOf('Иванов') !== -1; }) };
    })()""")
    check('M5: полный вид — все строки видны уровню view (Task 340)',
          rows['n'] == 2 and rows['hasShift'] and rows['hasDay'], rows)

    # --- 4) карточки сотрудников: клик по ФИО не открывает ---
    st = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        return { onclick: td.getAttribute('onclick'),
                 readonly: document.getElementById('page-work-schedule')
                     .classList.contains('ws-readonly') };
    })()""")
    check('M6: колонка ФИО с onclick (карточка уровням view, Task 340)',
          st['onclick'] is not None, st)
    check('M7: ws-readonly НЕТ (уровень view — карточки живы)', not st['readonly'], st)
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pop = page.evaluate("""(function(){
        var p = document.getElementById('wsEmpPopup');
        return { emp: p.classList.contains('active'),
                 closer: document.getElementById('wsEmpPopupCloser').classList.contains('active'),
                 html: p.innerHTML };
    })()""")
    check('M8: клик по ФИО — карточка ОТКРЫТА (Task 340)',
          pop['emp'] and pop['closer'], pop['emp'])
    # read-only: кнопок правки нет (классы кнопок)
    check('M8b: карточка READ-ONLY: нет «Уволить…»/«+ Отпуск…»/✎',
          (pop['html'].find('ws-emp-dismiss') == -1) and
          (pop['html'].find('ws-emp-addvac') == -1) and
          (pop['html'].find('ws-popup-act') == -1),
          {k: pop['html'].find(v) for k, v in {'d':'ws-emp-dismiss','v':'ws-emp-addvac','a':'ws-popup-act'}.items()})
    page.evaluate("WorkSchedule.closeEmpPopup()")

    # --- 5) клик по ячейке дня — окно мероприятий (регресс 337) ---
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pops = page.evaluate("""(function(){
        return { ev: document.getElementById('wsEventsPopup').classList.contains('active'),
                 cell: document.getElementById('wsCellPopup').classList.contains('active') };
    })()""")
    check('M10: клик по ячейке → окно «Мероприятия» (просмотр жив)',
          pops['ev'] and not pops['cell'], pops)
    page.evaluate("WorkSchedule.closeCellPopup()")

    # --- 6) «Обновить» и подсветка остались (фичи просмотра) ---
    st = page.evaluate("""(function(){
        var r = document.getElementById('wsRefreshBtn');
        var c = document.getElementById('wsCrossBtn');
        return { refresh: r && !r.hidden, cross: c && !c.hidden };
    })()""")
    check('M11: «Обновить» на месте (выбор года/месяца жив)', st['refresh'], st)
    check('M12: подсветка-перекрестье на месте', st['cross'], st)

    # --- 7) итоги ДОСТУПНЫ уровню view (Task 340, полный вид) ---
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        return { page: document.getElementById('page-ws-totals').classList.contains('active'),
                 ttPage: !!WorkSchedule._ttPage };
    })()""")
    check('M13: программный toggleTotals — мобильная страница итогов ОТКРЫТА',
          st['page'] and st['ttPage'], st)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(400)
    page.evaluate("navigateTo('ws-totals')")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        return { totals: document.getElementById('page-ws-totals').classList.contains('active'),
                 ttPage: !!WorkSchedule._ttPage };
    })()""")
    check('M14: прямой переход ws-totals — страница итогов открыта (view)',
          st['totals'] and st['ttPage'], st)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(400)

    check('M15: 0 JS-ошибок (зритель)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 2: мобильный 375 — РЕДАКТОР «КИП ИОС» (edit=✓) =========
    print('=== Контекст 2: мобильный 375, «КИП ИОС», матрица edit=✓ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t338-editor',
                                     theme='dark', role='КИП ИОС', ws_edit=True, dsf=3,
                                     saved_view=None)
    goto_tab_mobile(page)

    st = page.evaluate("""(function(){
        var tb = document.getElementById('wsTotalsBtn');
        return { tbHidden: tb.hidden, tbW: tb.offsetWidth };
    })()""")
    rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('E1: «Итоги учёта» ВИДНА редактору', (not st['tbHidden']) and st['tbW'] > 0, st)
    check('E2: полный вид — все строки (2)', rows == len(EMPLOYEES), rows)

    # карточка сотрудника открывается по клику ФИО
    st = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        return { onclick: td.getAttribute('onclick'),
                 readonly: document.getElementById('page-work-schedule')
                     .classList.contains('ws-readonly') };
    })()""")
    check('E3: колонка ФИО с onclick (карточка редактору)', st['onclick'] is not None, st)
    check('E4: режима ws-readonly нет', not st['readonly'], st)
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pop = page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')")
    check('E5: клик по ФИО — карточка ОТКРЫТА (редактор)', pop, pop)
    page.evaluate("WorkSchedule.closeEmpPopup()")

    # мобильная страница итогов открывается редактору
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        return { page: document.getElementById('page-ws-totals').classList.contains('active'),
                 ttPage: !!WorkSchedule._ttPage };
    })()""")
    check('E6: итоги-страница открылась редактору', st['page'] and st['ttPage'], st)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(400)
    check('E7: 0 JS-ошибок (редактор)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 3: ДЕСКТОП 1280 — зритель =========
    print('=== Контекст 3: десктоп 1280, «КИП ИОС дежурный», edit=✗ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t338-desk',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=False,
                                     saved_view=None)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    st = page.evaluate("""(function(){
        var tb = document.getElementById('wsTotalsBtn');
        return { tbHidden: tb.hidden, tbW: tb.offsetWidth };
    })()""")
    rows = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        var fios = [];
        trs.forEach(function(tr){
            var s = tr.querySelector('td.ws-emp-col .ws-emp-full');
            fios.push(s ? s.textContent : '');
        });
        return { n: trs.length, hasDay: fios.some(function(f){ return f.indexOf('Петров') !== -1; }) };
    })()""")
    check('K1: десктоп: «Итоги учёта» ВИДНА уровню view (Task 340)',
          (not st['tbHidden']) and st['tbW'] > 0, st)
    check('K2: десктоп: полный вид — все строки (2)', rows['n'] == 2 and rows['hasDay'], rows)

    # шторка итогов открывается уровню view (десктоп-путь)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        return { open: !!WorkSchedule._totalsOpen,
                 gridwide: p.classList.contains('ws-tt-gridwide') };
    })()""")
    check('K3: десктоп: шторка итогов открылась (view, Task 340)',
          st['open'] and st['gridwide'], st)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(500)

    # карточка по ФИО открывается (read-only)
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(300)
    pop = page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')")
    check('K4: десктоп: клик ФИО — карточка открылась (view, Task 340)', pop, pop)
    page.evaluate("WorkSchedule.closeEmpPopup()")

    # CSS-правила ws-readonly живы в стилях (hover-нейтрализация ФИО)
    st = page.evaluate("""(function(){
        var found = false, foundLight = false;
        for (var i = 0; i < document.styleSheets.length; i++) {
            var rules = null;
            try { rules = document.styleSheets[i].cssRules; } catch (e) { continue; }
            if (!rules) continue;
            for (var j = 0; j < rules.length; j++) {
                var sel = '';
                try { sel = rules[j].selectorText || ''; } catch (e) { continue; }
                if (sel.indexOf('ws-readonly') !== -1 && sel.indexOf('td.ws-emp-col:hover') !== -1) {
                    found = true;
                    if (sel.indexOf('light') !== -1) foundLight = true;
                }
            }
        }
        return { found: found, foundLight: foundLight };
    })()""")
    check('K5: CSS ws-readonly hover-правила в стилях (тёмная + светлая)',
          st['found'] and st['foundLight'], st)
    check('K6: 0 JS-ошибок (десктоп-зритель)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 4: ДЕСКТОП 1280 — редактор: шторка жива =========
    print('=== Контекст 4: десктоп 1280, «КИП ИОС», edit=✓ ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t338-deskedit',
                                     theme='dark', role='КИП ИОС', ws_edit=True, saved_view=None)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    st = page.evaluate("""(function(){
        var tb = document.getElementById('wsTotalsBtn');
        return { tbHidden: tb.hidden, tbW: tb.offsetWidth };
    })()""")
    check('R1: десктоп-редактор: «Итоги учёта» видна', (not st['tbHidden']) and st['tbW'] > 0, st)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        return { open: !!WorkSchedule._totalsOpen,
                 gridwide: p.classList.contains('ws-tt-gridwide') };
    })()""")
    check('R2: десктоп-редактор: шторка итогов открылась', st['open'] and st['gridwide'], st)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(500)

    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(300)
    pop = page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')")
    check('R3: десктоп-редактор: карточка по ФИО открылась', pop, pop)
    page.evaluate("WorkSchedule.closeEmpPopup()")
    check('R4: 0 JS-ошибок (десктоп-редактор)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 5: мобильный — дежурный-РЕДАКТОР (замок жив) =========
    print('=== Контекст 5: мобильный 375, «КИП ИОС дежурный», edit=✓ (замок) ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t338-duty',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=True, dsf=3)
    goto_tab_mobile(page)
    st = page.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        var tb = document.getElementById('wsTotalsBtn');
        return { viewHidden: view.hidden,
                 locked: view.classList.contains('ws-view-locked'),
                 tbHidden: tb.hidden };
    })()""")
    rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('D1: кнопка «Вид» видна + ЗАМОК (дежурный-редактор)',
          (not st['viewHidden']) and st['locked'], st)
    check('D2: вид заперт — сменный (1 строка), «Итоги» скрыта',
          rows == 1 and st['tbHidden'], (rows, st))
    check('D3: 0 JS-ошибок (дежурный-редактор)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

    # скриншоты-пруфы (зритель мобайл/десктоп)
    print('──────────────────────────────')
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
