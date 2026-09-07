# -*- coding: utf-8 -*-
# Task 336: browser-check — заявка пользователя:
#   • десктоп: блок картинка+№+Место ВПЛОТУЮ к верхнему бару
#     (реальный рендер: :has-правило padding-top:0, маржа удалена);
#   • сужение ЕЩЁ ПЛАВНЕЕ (0.35s cubic-bezier) и ширина — ПО ШИРИНЕ
#     СОКРАЩЁННОГО ТЕКСТА (замер JS --ws-emp-nw/--ws-tt-emp-nw):
#     сетка + итоги (вкладки месяц и год);
#   • полоса шапки сетки — В ОДНОЙ ПЛОСКОСТИ с полосами строк
#     (прозрачная граница th; пиксельный замер 3×).
import datetime
import json, sys
from urllib.parse import unquote
from PIL import Image
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
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-04' % (Y, M),'таб_номер':'017','статус':'д','источник':'руч'},
  {'id':4,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
]
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'},
] if m <= 6 else []
DEVICES = [
  {'ID':'100','Наименование':'Термометр сопротивления ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1, трубопровод пара','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]

STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        admin = STATE['role'] == 'Админ'
        return {'ok':True,'data':{'role':STATE['role'],'found':True,'permissions':{'workschedule.view':True,'workschedule.edit':admin,'flowmeter.view':True,'kip.view':True,'kip.edit':admin}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok':True,'data':{'entries':ENTRIES}}
        return {'ok':True,'data':{'entries':YEAR_ENTRY(month or 1)}}
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def setup_ctx(browser, viewport, token, theme=None, role='Админ', dsf=1):
    STATE['role'] = role
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t336)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
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

def blue_columns(png_path, y_head, y_body):
    """колонки синих пикселей (74,143,199)±20 в строках y_head/y_body"""
    im = Image.open(png_path).convert('RGB')
    def cols(y):
        out = []
        run = None
        for x in range(im.size[0]):
            p = im.getpixel((x, y))
            isb = abs(p[0]-74) < 25 and abs(p[1]-143) < 25 and abs(p[2]-199) < 25
            if isb and run is None:
                run = x
            elif not isb and run is not None:
                out.append((run, x - 1))
                run = None
        if run is not None:
            out.append((run, im.size[0] - 1))
        return out
    return cols(y_head), cols(y_body)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: МОБИЛЬНЫЙ 375, Админ, тёмная =================
    print('=== Контекст 1: мобильный 375, Админ, тёмная ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t336-a', theme='dark', dsf=3)
    goto_tab_mobile(page)

    # --- 1) полоса шапки в ОДНОЙ ПЛОСКОСТИ с полосами строк (пиксели 3×) ---
    page.screenshot(path='scripts/task336-bc-seam.png', clip=page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap .ws-grid thead th.ws-emp-col');
        var b = th.getBoundingClientRect();
        return {x: Math.max(0, b.right - 40), y: Math.max(0, b.bottom - 10),
                width: 80, height: 130};
    })()"""))
    head_runs, body_runs = blue_columns('scripts/task336-bc-seam.png', 12, 90)
    check('M1: шапка — синяя полоса 2 CSS px (6@3×)',
          len(head_runs) == 1 and 4 <= (head_runs[0][1] - head_runs[0][0] + 1) <= 8,
          head_runs)
    check('M1b: строки — синяя полоса 2 CSS px',
          len(body_runs) >= 1 and 4 <= (body_runs[0][1] - body_runs[0][0] + 1) <= 8,
          body_runs)
    if head_runs and body_runs:
        same = head_runs[0] == body_runs[0]
        check('M1c: полосы шапки и строк В ОДНОЙ ПЛОСКОСТИ (совпадают)', same,
              (head_runs[0], body_runs[0]))

    # --- 2) замер переменных + сужение сетки ---
    vars_set = page.evaluate("""(function(){
        return { nw: document.body.style.getPropertyValue('--ws-emp-nw'),
                 tt: document.body.style.getPropertyValue('--ws-tt-emp-nw') };
    })()""")
    check('M2: --ws-emp-nw замерена (~40px: 30 текст + 8 + 2)',
          vars_set['nw'] and 34 <= float(vars_set['nw'].replace('px', '')) <= 52, vars_set)

    nar = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap.querySelector('.ws-grid');
        var th = tbl.querySelector('thead th.ws-emp-col');
        var headSpan = tbl.querySelector('thead th.ws-emp-col .ws-emp-head-txt');
        var empSpan = tbl.querySelector('tbody td.ws-emp-col .ws-emp-full');
        var out = { trans: getComputedStyle(th).transitionDuration,
                    tf: getComputedStyle(th).transitionTimingFunction };
        wrap.scrollLeft = 2;
        wrap.dispatchEvent(new Event('scroll'));
        out.narrow = tbl.classList.contains('ws-narrow');
        out.headNow = headSpan.textContent; out.empNow = empSpan.textContent;
        return out;
    })()""")
    page.wait_for_timeout(600)
    nar2 = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap.querySelector('.ws-grid');
        var th = tbl.querySelector('thead th.ws-emp-col');
        return { thW: th.getBoundingClientRect().width };
    })()""")
    check('M3: transition 0.35s + cubic-bezier (плавнее)',
          '0.35s' in nar['trans'] and 'cubic-bezier' in nar['tf'], (nar['trans'], nar['tf']))
    check('M3b: scrollLeft=2 → сужение + «Сотр» + «Иван»',
          nar['narrow'] is True and nar['headNow'] == 'Сотр' and nar['empNow'] == 'Иван',
          (nar['narrow'], nar['headNow'], nar['empNow']))
    check('M3c: ширина колонки ≈ ширина текста (~40px)',
          30 <= nar2['thW'] <= 56, nar2['thW'])
    back = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        wrap.scrollLeft = 0; wrap.dispatchEvent(new Event('scroll'));
        var tbl = wrap.querySelector('.ws-grid');
        return { narrow: tbl.classList.contains('ws-narrow'),
                 head: tbl.querySelector('thead th.ws-emp-col .ws-emp-head-txt').textContent };
    })()""")
    check('M3d: возврат к 0 → полное «Сотрудник»',
          back['narrow'] is False and back['head'] == 'Сотрудник', back)

    # --- 3) итоги: вкладка МЕСЯЦ — сужение ширины ---
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    tm = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        var out = { w0: th.getBoundingClientRect().width,
                    trans: getComputedStyle(th).transitionDuration,
                    tf: getComputedStyle(th).transitionTimingFunction,
                    nw: document.body.style.getPropertyValue('--ws-tt-emp-nw') };
        b.scrollLeft = 2; b.dispatchEvent(new Event('scroll'));
        out.narrow = t.classList.contains('ws-narrow');
        return out;
    })()""")
    page.wait_for_timeout(600)
    tm2 = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        return { thW: th.getBoundingClientRect().width,
                 head: th.querySelector('.ws-tt-emp-head').textContent,
                 name: t.querySelector('tbody .ws-tt-name').textContent };
    })()""")
    check('M4: месяц — переменная --ws-tt-emp-nw замерена (~48px)',
          tm['nw'] and 42 <= float(tm['nw'].replace('px', '')) <= 58, tm['nw'])
    check('M4b: месяц — transition 0.35s cubic-bezier',
          '0.35s' in tm['trans'] and 'cubic-bezier' in tm['tf'], (tm['trans'], tm['tf']))
    check('M4c: месяц — колонка СУЖАЕТСЯ (42% → ~48px)',
          tm['narrow'] is True and 34 <= tm2['thW'] <= 62 and tm2['thW'] < tm['w0'] * 0.5,
          (tm['w0'], tm2['thW']))
    check('M4d: месяц — шапка «Сотр», фамилия «Иван»',
          tm2['head'] == 'Сотр' and tm2['name'] == 'Иван', (tm2['head'], tm2['name']))
    page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        b.scrollLeft = 0; b.dispatchEvent(new Event('scroll'));
    })()""")
    page.wait_for_timeout(400)

    # --- 4) итоги: вкладка ГОД ---
    page.click('#wsTtPageTabYear')
    page.wait_for_timeout(900)
    ty = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        var out = { w0: th.getBoundingClientRect().width,
                    trans: getComputedStyle(th).transitionDuration };
        b.scrollLeft = 2; b.dispatchEvent(new Event('scroll'));
        out.narrow = t.classList.contains('ws-narrow');
        return out;
    })()""")
    page.wait_for_timeout(600)
    ty2 = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        return { thW: th.getBoundingClientRect().width,
                 head: th.querySelector('.ws-tt-emp-head').textContent,
                 name: t.querySelector('tbody .ws-tt-name').textContent };
    })()""")
    check('M5: год — колонка сужается (w0 → ~46px)',
          ty['narrow'] is True and 32 <= ty2['thW'] <= 62 and ty2['thW'] < ty['w0'] * 0.5,
          (ty['w0'], ty2['thW']))
    check('M5b: год — «Сотр» + «Иван» + 0.35s',
          ty2['head'] == 'Сотр' and ty2['name'] == 'Иван' and '0.35s' in ty['trans'],
          (ty2['head'], ty2['name'], ty['trans']))
    page.screenshot(path='scripts/task336-bc-tt-year.png')
    page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        b.scrollLeft = 0; b.dispatchEvent(new Event('scroll'));
    })()""")

    # --- 5) карточка прибора (мобайл, контроль Task 335/336) ---
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1400)
    page.evaluate("devOpenDetail('100')")
    page.wait_for_timeout(1100)
    mcard = page.evaluate("""(function(){
        var pg = document.getElementById('page-device-detail');
        var head = pg.querySelector('.page-inline-header');
        var top = pg.querySelector('.dev-detail-top');
        if (!head || !top) return {err:1};
        return { gap: top.getBoundingClientRect().top - head.getBoundingClientRect().bottom };
    })()""")
    check('M6: мобайл-карточка — блок вплотную к шапке (gap 0)',
          'gap' in mcard and abs(mcard['gap']) < 1.5, mcard)
    check('M7: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: ДЕСКТОП 1440, Админ, тёмная =================
    print('=== Контекст 2: десктоп 1440, Админ, тёмная ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1440,'height':900}, 'bcheck-t336-b', theme='dark')
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1500)
    page.evaluate("devOpenDetail('100')")
    page.wait_for_timeout(1100)

    dcard = page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        var bar = document.getElementById('detailBreadcrumbBar');
        var top = body ? body.querySelector('.dev-detail-top') : null;
        if (!bar || !top) return {err:1};
        var brb = bar.getBoundingClientRect().bottom;
        var out = { gap0: top.getBoundingClientRect().top - brb,
                    padTop: getComputedStyle(body).paddingTop };
        body.scrollTop = 600;
        out.gapSc = top.getBoundingClientRect().top - brb;
        body.scrollTop = 0;
        return out;
    })()""")
    check('D1: РЕАЛЬНЫЙ рендер — блок ВПЛОТУЮ к бару (gap 0, паддинг зоны 0)',
          'gap0' in dcard and abs(dcard['gap0']) < 1.5
          and dcard['padTop'] == '0px', dcard)
    check('D1b: при прокрутке — прилип к верху (gap 0)',
          'gapSc' in dcard and abs(dcard['gapSc']) < 1.5, dcard)
    page.screenshot(path='scripts/task336-bc-d-card.png')

    # прочая карточка панели (без dev-detail-top) — паддинг 16px сохранён
    dpad = page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        return { bodyHas: body ? body.innerHTML.indexOf('dev-detail-top') : -1 };
    })()""")
    check('D2: в панели — карточка прибора (:has матчит)',
          dpad['bodyHas'] != -1, dpad)

    check('D3: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()
    browser.close()

print('')
print('ИТОГО: %d ✓ / %d ✗' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
