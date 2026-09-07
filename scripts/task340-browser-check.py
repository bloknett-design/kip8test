# -*- coding: utf-8 -*-
# Task 340: browser-check — трёхуровневый доступ к «Графику работы»:
#   workschedule.view      — карточка по ФИО ОТКРЫВАЕТСЯ (read-only),
#                            «Вид»/«Итоги» видны, «Сформировать» скрыта;
#   workschedule.view.min  — карточки нет, «Итоги» скрыта, «Мастер
#                            КИПиА» скрыт в шахматке, «Вид» видна;
#   workschedule.edit      — полный доступ (окно кодов, карточка с
#                            правкой, «Сформировать»).
# Мок матрицы: getMyAccess отдаёт все три права по STATE.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8945
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
# 017 — сменный слесарь; 023 — ДНЕВНОЙ «Мастер КИПиА»; 031 — дневной инженер
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Мастер КИПиА','комментарий':''},
  {'таб_номер':'031','ФИО':'Сидоров Сидор Сидорович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2023-06-01','дата_увольнения':'','в_архиве':0,'должность':'Инженер','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'031','статус':'Д8','источник':'авто'}
]
TRAININGS = [
  {'id':7,'таб_номер':'017','тип':'инструктаж','тема':'Вводный','дата_начала':'%04d-%02d-02' % (Y, M),'дата_окончания':'%04d-%02d-02' % (Y, M)}
]

# STATE: роль + три права матрицы
STATE = {'role': 'КИП ИОС дежурный', 'ws_view': False, 'ws_edit': False, 'ws_min': False}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':STATE['role'],'found':True,
                'permissions':{'workschedule.view':STATE['ws_view'],
                               'workschedule.view.min':STATE['ws_min'],
                               'workschedule.edit':STATE['ws_edit']}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
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

def setup_ctx(browser, viewport, token, theme=None, role='КИП ИОС дежурный',
              ws_view=False, ws_edit=False, ws_min=False, dsf=1, saved_view=None):
    STATE['role'] = role
    STATE['ws_view'] = ws_view
    STATE['ws_edit'] = ws_edit
    STATE['ws_min'] = ws_min
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t340)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
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

def grid_fios(page):
    return page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        var fios = [];
        trs.forEach(function(tr){
            var s = tr.querySelector('td.ws-emp-col .ws-emp-full');
            fios.push(s ? s.textContent : '');
        });
        return { n: trs.length,
                 master: fios.some(function(f){ return f.indexOf('Петров') !== -1; }),
                 others: fios.filter(function(f){ return f.indexOf('Иванов') !== -1 || f.indexOf('Сидоров') !== -1; }).length };
    })()""")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========= Контекст 1: мобильный 375 — УРОВЕНЬ view («ИТР8 pro») =========
    print('=== Контекст 1: мобильный 375, уровень view (workschedule.view) ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t340-view',
                                     theme='dark', role='ИТР8 pro', ws_view=True, dsf=3)
    goto_tab_mobile(page)

    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        var tb = document.getElementById('wsTotalsBtn');
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 viewW: view.offsetWidth, tbHidden: tb.hidden, tbW: tb.offsetWidth };
    })()""")
    check('V1: «Сформировать» скрыта, «Вид» ВИДНА (Task 340)',
          st['genHidden'] and (not st['viewHidden']) and st['viewW'] > 0, st)
    check('V2: «Итоги учёта» ВИДНА уровню view (полный вид)',
          (not st['tbHidden']) and st['tbW'] > 0, st)

    rows = grid_fios(page)
    check('V3: полный вид — все 3 строки, «Мастер КИПиА» виден',
          rows['n'] == 3 and rows['master'] and rows['others'] == 2, rows)

    st = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        return { onclick: td.getAttribute('onclick'),
                 readonly: document.getElementById('page-work-schedule')
                     .classList.contains('ws-readonly'),
                 level: WorkSchedule._viewLevel };
    })()""")
    check('V4: ФИО с onclick (карточка уровням view), ws-readonly НЕТ',
          (st['onclick'] is not None) and (not st['readonly']) and st['level'] == 'view', st)

    # карточка открывается и READ-ONLY (без «Уволить…»/«+ Отпуск…»/✎)
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pop = page.evaluate("""(function(){
        var p = document.getElementById('wsEmpPopup');
        return { active: p.classList.contains('active'),
                 html: p.innerHTML };
    })()""")
    check('V5: клик по ФИО — карточка ОТКРЫТА (view)', pop['active'], pop['active'])
    # read-only: нет КНОПОК правки (классы кнопок: ws-emp-dismiss /
    # ws-emp-addvac / ws-popup-act); секция «Отпуска» (данные) остаётся
    check('V6: карточка READ-ONLY: нет «Уволить…»/«+ Отпуск…»/✎ (кнопок правки)',
          (pop['html'].find('ws-emp-dismiss') == -1) and (pop['html'].find('ws-emp-addvac') == -1)
          and (pop['html'].find('ws-popup-act') == -1),
          {k: pop['html'].find(v) for k, v in {'dismiss':'ws-emp-dismiss','addvac':'ws-emp-addvac','act':'ws-popup-act'}.items()})
    check('V6b: секции данных живы (профиль/отпуска/мероприятия)',
          (pop['html'].find('ws-emp-field') != -1) and (pop['html'].find('Отпуска') != -1),
          len(pop['html']))
    page.evaluate("WorkSchedule.closeEmpPopup()")

    # клик по ячейке дня — окно мероприятий, НЕ окно кодов
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pops = page.evaluate("""(function(){
        return { ev: document.getElementById('wsEventsPopup').classList.contains('active'),
                 cell: document.getElementById('wsCellPopup').classList.contains('active') };
    })()""")
    check('V7: клик по ячейке → окно «Мероприятия», окна кодов НЕТ',
          pops['ev'] and (not pops['cell']), pops)
    page.evaluate("WorkSchedule.closeCellPopup()")

    # мобильная страница итогов доступна уровню view
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        return { page: document.getElementById('page-ws-totals').classList.contains('active'),
                 ttPage: !!WorkSchedule._ttPage };
    })()""")
    check('V8: мобильная страница итогов открылась (view)', st['page'] and st['ttPage'], st)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(400)
    page.screenshot(path='scripts/task340-proof-mobile-view.png')
    check('V9: 0 JS-ошибок (view)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 2: мобильный 375 — УРОВЕНЬ min («КИП ИОС дежурный») =========
    print('=== Контекст 2: мобильный 375, уровень min (workschedule.view.min) ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t340-min',
                                     theme='dark', role='КИП ИОС дежурный', ws_min=True, dsf=3)
    goto_tab_mobile(page)

    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        var tb = document.getElementById('wsTotalsBtn');
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 viewW: view.offsetWidth, tbHidden: tb.hidden, tbW: tb.offsetWidth,
                 level: WorkSchedule._viewLevel };
    })()""")
    check('M1: «Сформировать» и «Итоги» скрыты, «Вид» ВИДНА',
          st['genHidden'] and st['tbHidden'] and st['tbW'] == 0
          and (not st['viewHidden']) and st['viewW'] > 0, st)
    check('M2: уровень доступа — «min»', st['level'] == 'min', st)

    rows = grid_fios(page)
    check('M3: «Мастер КИПиА» скрыт (2 строки, Петрова нет)',
          rows['n'] == 2 and (not rows['master']) and rows['others'] == 2, rows)

    st = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap tbody tr td.ws-emp-col');
        var withClick = 0;
        tds.forEach(function(td){ if (td.getAttribute('onclick')) withClick++; });
        return { withClick: withClick,
                 readonly: document.getElementById('page-work-schedule')
                     .classList.contains('ws-readonly') };
    })()""")
    check('M4: ФИО без onclick, страница ws-readonly',
          st['withClick'] == 0 and st['readonly'], st)

    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pop = page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')")
    page.evaluate("WorkSchedule._openEmpPopup(null, '017')")
    page.wait_for_timeout(200)
    pop2 = page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')")
    check('M5: карточки НЕТ (клик и программно)', (not pop) and (not pop2), (pop, pop2))

    # окно мероприятий живо (просмотр)
    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pops = page.evaluate("""(function(){
        return { ev: document.getElementById('wsEventsPopup').classList.contains('active'),
                 cell: document.getElementById('wsCellPopup').classList.contains('active') };
    })()""")
    check('M6: клик по ячейке → окно «Мероприятия» (окна кодов нет)',
          pops['ev'] and (not pops['cell']), pops)
    page.evaluate("WorkSchedule.closeCellPopup()")

    # итоги недоступны: программно и прямым переходом
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(500)
    st = page.evaluate("""(function(){
        return { page: document.getElementById('page-ws-totals').classList.contains('active'),
                 open: WorkSchedule._totalsOpen, ttPage: !!WorkSchedule._ttPage };
    })()""")
    check('M7: программный toggleTotals — ни страницы, ни шторки',
          (not st['page']) and (not st['open']) and (not st['ttPage']), st)
    page.evaluate("navigateTo('ws-totals')")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        return { totals: document.getElementById('page-ws-totals').classList.contains('active'),
                 ws: document.getElementById('page-work-schedule').classList.contains('active'),
                 ttPage: !!WorkSchedule._ttPage };
    })()""")
    check('M8: прямой переход ws-totals → редирект на табель',
          (not st['totals']) and st['ws'] and (not st['ttPage']), st)

    # «Вид» работает у min: переключение full → shift (Мастер не важен там)
    page.evaluate("WorkSchedule.cycleView()")
    page.wait_for_timeout(400)
    st = page.evaluate("""(function(){
        return { view: WorkSchedule._view,
                 saved: localStorage.getItem('kip8_ws_view_v1') };
    })()""")
    check('M9: «Вид» переключает (full → shift), сохраняется',
          st['view'] == 'shift' and st['saved'] == 'shift', st)
    page.evaluate("WorkSchedule.cycleView()")  # → day
    page.evaluate("WorkSchedule.cycleView()")  # → full обратно
    page.wait_for_timeout(300)

    page.screenshot(path='scripts/task340-proof-mobile-min.png')
    check('M10: 0 JS-ошибок (min)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 3: мобильный 375 — РЕДАКТОР («КИП ИОС», edit) =========
    print('=== Контекст 3: мобильный 375, уровень edit (workschedule.edit) ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t340-edit',
                                     theme='dark', role='КИП ИОС', ws_edit=True, dsf=3)
    goto_tab_mobile(page)

    st = page.evaluate("""(function(){
        var gen = document.getElementById('wsGenerateBtn');
        var view = document.getElementById('wsViewBtn');
        var tb = document.getElementById('wsTotalsBtn');
        return { genHidden: gen.hidden, viewHidden: view.hidden,
                 tbHidden: tb.hidden, level: WorkSchedule._viewLevel };
    })()""")
    check('E1: редактор — «Сформировать»/«Вид»/«Итоги» видны',
          (not st['genHidden']) and (not st['viewHidden']) and (not st['tbHidden'])
          and st['level'] == 'edit', st)
    rows = grid_fios(page)
    check('E2: все 3 строки (Мастер виден)', rows['n'] == 3 and rows['master'], rows)

    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pop = page.evaluate("""(function(){
        var p = document.getElementById('wsEmpPopup');
        return { active: p.classList.contains('active'), html: p.innerHTML };
    })()""")
    check('E3: карточка открылась С правкой («Уволить…»/«+ Отпуск…»)',
          pop['active'] and (pop['html'].find('Уволить') != -1)
          and (pop['html'].find('+ Отпуск') != -1), pop['active'])
    page.evaluate("WorkSchedule.closeEmpPopup()")

    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(400)
    pops = page.evaluate("""(function(){
        return { ev: document.getElementById('wsEventsPopup').classList.contains('active'),
                 cell: document.getElementById('wsCellPopup').classList.contains('active') };
    })()""")
    check('E4: клик по ячейке → окно КОДОВ (+мероприятия над ним)',
          pops['ev'] and pops['cell'], pops)
    page.evaluate("WorkSchedule.closeCellPopup()")
    check('E5: 0 JS-ошибок (edit)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 4: ДЕСКТОП 1280 — уровень min =========
    print('=== Контекст 4: десктоп 1280, уровень min ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t340-deskmin',
                                     theme='dark', role='КИП ИОС дежурный', ws_min=True)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    st = page.evaluate("""(function(){
        var tb = document.getElementById('wsTotalsBtn');
        var view = document.getElementById('wsViewBtn');
        return { tbHidden: tb.hidden, viewHidden: view.hidden };
    })()""")
    rows = grid_fios(page)
    check('K1: десктоп min: «Итоги» скрыта, «Вид» видна',
          st['tbHidden'] and (not st['viewHidden']), st)
    check('K2: десктоп min: «Мастер КИПиА» скрыт (2 строки)',
          rows['n'] == 2 and (not rows['master']), rows)

    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(600)
    st = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        return { open: !!WorkSchedule._totalsOpen,
                 gridwide: p.classList.contains('ws-tt-gridwide') };
    })()""")
    check('K3: десктоп min: шторка итогов не открылась',
          (not st['open']) and (not st['gridwide']), st)

    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(300)
    pop = page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')")
    check('K4: десктоп min: карточки нет', not pop, pop)

    # подсветка-перекрестье и «Обновить» живы (фичи просмотра)
    st = page.evaluate("""(function(){
        var r = document.getElementById('wsRefreshBtn');
        var c = document.getElementById('wsCrossBtn');
        return { refresh: r && !r.hidden, cross: c && !c.hidden };
    })()""")
    check('K5: «Обновить»/перекрестье на месте (фичи просмотра)',
          st['refresh'] and st['cross'], st)
    page.screenshot(path='scripts/task340-proof-desktop-min.png')
    check('K6: 0 JS-ошибок (десктоп min)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 5: ДЕСКТОП 1280 — уровень view =========
    print('=== Контекст 5: десктоп 1280, уровень view ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t340-deskview',
                                     theme='dark', role='ИТР8 pro', ws_view=True)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    st = page.evaluate("""(function(){
        var tb = document.getElementById('wsTotalsBtn');
        return { tbHidden: tb.hidden, tbW: tb.offsetWidth };
    })()""")
    check('G1: десктоп view: «Итоги» видна', (not st['tbHidden']) and st['tbW'] > 0, st)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    st = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        return { open: !!WorkSchedule._totalsOpen,
                 gridwide: p.classList.contains('ws-tt-gridwide') };
    })()""")
    check('G2: десктоп view: шторка итогов открылась', st['open'] and st['gridwide'], st)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(500)

    page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-emp-col');
        td.dispatchEvent(new MouseEvent('click', {bubbles:true}));
    })()""")
    page.wait_for_timeout(300)
    pop = page.evaluate("""(function(){
        var p = document.getElementById('wsEmpPopup');
        return { active: p.classList.contains('active'), html: p.innerHTML };
    })()""")
    check('G3: десктоп view: карточка открылась и read-only',
          pop['active'] and (pop['html'].find('Уволить') == -1), pop['active'])
    page.evaluate("WorkSchedule.closeEmpPopup()")
    page.screenshot(path='scripts/task340-proof-desktop-view.png')
    check('G4: 0 JS-ошибок (десктоп view)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 6: мобильный — дежурный-РЕДАКТОР (замок жив) =========
    print('=== Контекст 6: мобильный 375, «КИП ИОС дежурный», edit=✓ (замок) ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t340-duty',
                                     theme='dark', role='КИП ИОС дежурный', ws_edit=True, dsf=3)
    goto_tab_mobile(page)
    st = page.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        var tb = document.getElementById('wsTotalsBtn');
        return { viewHidden: view.hidden,
                 locked: view.classList.contains('ws-view-locked'),
                 tbHidden: tb.hidden, level: WorkSchedule._viewLevel };
    })()""")
    rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('D1: «Вид» видна + ЗАМОК (дежурный-редактор, регресс 332)',
          (not st['viewHidden']) and st['locked'] and st['level'] == 'edit', st)
    check('D2: вид заперт — сменный (1 строка), «Итоги» скрыта',
          rows == 1 and st['tbHidden'], (rows, st))
    check('D3: 0 JS-ошибок (дежурный-редактор)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print('──────────────────────────────')
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
