# -*- coding: utf-8 -*-
# Task 336 probe-2: вкладка «Год» страницы итогов + зум-скриншот стыка
# шапки шахматки («Сотрудник +» | первый день) в тёмной и светлой теме.
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
Y, M = datetime.date.today().year, datetime.date.today().month

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
]
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'},
] if m <= 6 else []

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'kip.view':True,'kip.edit':True}}}
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
    return {'ok':True,'data':{'ok':True}}

def setup_ctx(browser, viewport, token, theme='dark'):
    ctx = browser.new_context(viewport=viewport, device_scale_factor=3)
    page = ctx.new_page()
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
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, body='x'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, body='x'))
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page

def tab_mobile(page):
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

with sync_playwright() as p:
    browser = p.chromium.launch()

    for theme in ('dark', 'light'):
        print('=== МОБАЙЛ 375 (%s) ===' % theme)
        ctx, page = setup_ctx(browser, {'width':375,'height':720}, 'probe-t336-m2-' + theme, theme)
        tab_mobile(page)

        # зум-скриншот стыка шапки: «Сотрудник +» | первый день
        box = page.evaluate("""(function(){
            var th = document.querySelector('#wsGridWrap .ws-grid thead th.ws-emp-col');
            var b = th.getBoundingClientRect();
            return {x: Math.max(0, b.right - 40), y: Math.max(0, b.bottom - 8), width: 80, height: 150};
        })()""")
        page.screenshot(path='scripts/task336-probe-head-%s.png' % theme, clip=box)

        # вкладка «Год» страницы итогов
        page.click('#wsTotalsBtn'); page.wait_for_timeout(900)
        page.click('#wsTtPageTabYear'); page.wait_for_timeout(900)
        y_tt = page.evaluate("""(function(){
            var b = document.getElementById('wsTtPageBody');
            var t = b ? b.querySelector('.ws-tt-table') : null;
            if (!t) return {err:'no table'};
            var th = t.querySelector('thead th.ws-tt-emp');
            var name = t.querySelector('tbody .ws-tt-name');
            var headSpan = th ? th.querySelector('.ws-tt-emp-head') : null;
            function txtW(el, s){ if(!el) return null; var old = el.textContent; el.textContent = s;
                var w = el.getBoundingClientRect().width; el.textContent = old; return w; }
            var w0 = th ? th.getBoundingClientRect().width : null;
            if (th) { b.scrollLeft = 2; b.dispatchEvent(new Event('scroll')); }
            var out = {
                hasEmpCol: !!th, w0: w0,
                wNarrow: th ? th.getBoundingClientRect().width : null,
                narrow: t.classList.contains('ws-narrow'),
                trans: th ? getComputedStyle(th).transitionDuration + ' / ' + getComputedStyle(th).transitionTimingFunction : null,
                minW: th ? getComputedStyle(th).minWidth : null,
                textW: { headSotr: txtW(headSpan, 'Сотр'), nameIvan: txtW(name, 'Иван') },
                nameTxt: name ? name.textContent : null,
                tableClass: t.className,
                yearHeadHtml: th ? th.innerHTML : null
            };
            b.scrollLeft = 0; b.dispatchEvent(new Event('scroll'));
            return out;
        })()""")
        print('M-TT-YEAR:', json.dumps(y_tt, ensure_ascii=False, indent=1))
        ctx.close()

    # ДЕСКТОП 1440: стык шапки сетки
    print('=== ДЕСКТОП 1440 (dark) ===')
    ctx, page = setup_ctx(browser, {'width':1440,'height':900}, 'probe-t336-d2', 'dark')
    page.evaluate("navigateTo('docs-ios')"); page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')"); page.wait_for_timeout(1800)
    d_grid = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap ? wrap.querySelector('.ws-grid') : null;
        if (!tbl) return {err:'no grid'};
        var th = tbl.querySelector('thead th.ws-emp-col');
        var td = tbl.querySelector('tbody td.ws-emp-col');
        var day1 = tbl.querySelector('thead th.ws-day-col');
        var hb = th.getBoundingClientRect(), db = td.getBoundingClientRect(), d1b = day1.getBoundingClientRect();
        return { thRight: hb.right, tdRight: db.right, day1Left: d1b.left,
                 thW: hb.width, tdW: db.width,
                 tdBorderR: getComputedStyle(td).borderRightWidth,
                 thBorderR: getComputedStyle(th).borderRightWidth };
    })()""")
    print('D-GRID:', json.dumps(d_grid, ensure_ascii=False))
    box = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap .ws-grid thead th.ws-emp-col');
        var b = th.getBoundingClientRect();
        return {x: Math.max(0, b.right - 40), y: Math.max(0, b.bottom - 8), width: 80, height: 150};
    })()""")
    page.screenshot(path='scripts/task336-probe-head-desktop.png', clip=box)
    ctx.close()
    browser.close()
print('DONE')
