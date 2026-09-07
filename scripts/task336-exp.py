# -*- coding: utf-8 -*-
# Task 336 experiment: проверка предлагаемых фиксов ДО правки файла:
#   1) прозрачная правая граница th.ws-emp-col → полосы шапки/строк
#      в одной плоскости (пиксельный замер);
#   2) узкая ширина по тексту (--ws-emp-nw/--ws-tt-emp-nw) + переход
#      0.35s — сетка + итоги (месяц/год);
#   3) десктоп-панель: padding-top:0 (:has) — уже проверено (A).
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
Y, M = datetime.date.today().year, datetime.date.today().month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
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
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'kip.view':True}}}
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

FIX_CSS = """
<style id="t336fix">
/* фикс 1: полоса шапки в одной плоскости с полосами строк */
.ws-grid thead th.ws-emp-col { border-right: 1px solid transparent; }
/* фикс 2: узкая ширина по тексту */
.ws-grid.ws-narrow thead th.ws-emp-col,
.ws-grid.ws-narrow tbody td.ws-emp-col {
    width: var(--ws-emp-nw, 52px); min-width: var(--ws-emp-nw, 52px);
}
.ws-tt-table.ws-narrow th.ws-tt-emp,
.ws-tt-table.ws-narrow td.ws-tt-emp { width: var(--ws-tt-emp-nw, 48px); }
.ws-grid thead th.ws-emp-col, .ws-grid tbody td.ws-emp-col {
    transition: width 0.35s cubic-bezier(0.4,0,0.2,1),
                min-width 0.35s cubic-bezier(0.4,0,0.2,1),
                padding 0.35s cubic-bezier(0.4,0,0.2,1);
}
.ws-tt-table th.ws-tt-emp, .ws-tt-table td.ws-tt-emp {
    transition: width 0.35s cubic-bezier(0.4,0,0.2,1);
}
</style>
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':375,'height':720}, device_scale_factor=3)
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
    page.evaluate("localStorage.setItem('kip8_session_token','exp-t336')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload(); page.wait_for_timeout(2500)

    page.evaluate("navigateTo('docs-ios')"); page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')"); page.wait_for_timeout(1600)

    # применяем фиксы
    page.evaluate("""(function(){
        document.head.insertAdjacentHTML('beforeend', %s);
        document.body.style.setProperty('--ws-emp-nw', '42px');
        document.body.style.setProperty('--ws-tt-emp-nw', '48px');
    })()""" % json.dumps(FIX_CSS))
    page.wait_for_timeout(100)

    # --- 1) пиксельный замер стыка после фикса ---
    box = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap .ws-grid thead th.ws-emp-col');
        var b = th.getBoundingClientRect();
        return {x: Math.max(0, b.right - 40), y: Math.max(0, b.bottom - 8), width: 80, height: 150};
    })()""")
    page.screenshot(path='scripts/task336-exp-head-fixed.png', clip=box)

    d = page.evaluate("""(function(){
        var tbl = document.querySelector('#wsGridWrap .ws-grid');
        var th = tbl.querySelector('thead th.ws-emp-col');
        var td = tbl.querySelector('tbody td.ws-emp-col');
        var day1 = tbl.querySelector('thead th.ws-day-col');
        var hb = th.getBoundingClientRect(), db = td.getBoundingClientRect(), d1b = day1.getBoundingClientRect();
        return { thRight: hb.right, tdRight: db.right, day1Left: d1b.left,
                 thBr: getComputedStyle(th).borderRightWidth,
                 day1Br: getComputedStyle(day1).borderLeftWidth };
    })()""")
    print('DIVIDER after fix:', json.dumps(d, ensure_ascii=False))

    # --- 2) сужение сетки: ширина колонки ~42 + переход ---
    n = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap.querySelector('.ws-grid');
        var th = tbl.querySelector('thead th.ws-emp-col');
        wrap.scrollLeft = 2; wrap.dispatchEvent(new Event('scroll'));
        var out = { narrow: tbl.classList.contains('ws-narrow') };
        var t0 = Date.now();
        var w0 = th.getBoundingClientRect().width;
        return { setup: out, w0: w0, thW: th.getBoundingClientRect().width };
    })()""")
    page.wait_for_timeout(500)  # дать переходу завершиться
    n2 = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap.querySelector('.ws-grid');
        var th = tbl.querySelector('thead th.ws-emp-col');
        return { thW: th.getBoundingClientRect().width,
                 head: tbl.querySelector('thead th.ws-emp-col .ws-emp-head-txt').textContent,
                 emp: tbl.querySelector('tbody td.ws-emp-col .ws-emp-full').textContent };
    })()""")
    print('GRID narrow:', json.dumps(n, ensure_ascii=False), '->', json.dumps(n2, ensure_ascii=False))
    page.screenshot(path='scripts/task336-exp-grid-narrow.png')
    page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        wrap.scrollLeft = 0; wrap.dispatchEvent(new Event('scroll'));
    })()""")
    page.wait_for_timeout(500)

    # --- 3) итоги: месяц ---
    page.click('#wsTotalsBtn'); page.wait_for_timeout(900)
    mt = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        var w0 = th.getBoundingClientRect().width;
        b.scrollLeft = 2; b.dispatchEvent(new Event('scroll'));
        return { w0: w0, narrow: t.classList.contains('ws-narrow') };
    })()""")
    page.wait_for_timeout(500)
    mt2 = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        return { thW: th.getBoundingClientRect().width,
                 head: th.querySelector('.ws-tt-emp-head').textContent,
                 name: t.querySelector('tbody .ws-tt-name').textContent,
                 tblW: t.getBoundingClientRect().width };
    })()""")
    print('TT month:', json.dumps(mt, ensure_ascii=False), '->', json.dumps(mt2, ensure_ascii=False))
    page.screenshot(path='scripts/task336-exp-tt-month.png')
    page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        b.scrollLeft = 0; b.dispatchEvent(new Event('scroll'));
    })()""")

    # --- 4) итоги: год ---
    page.click('#wsTtPageTabYear'); page.wait_for_timeout(900)
    yt = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        var w0 = th.getBoundingClientRect().width;
        b.scrollLeft = 2; b.dispatchEvent(new Event('scroll'));
        return { w0: w0, narrow: t.classList.contains('ws-narrow') };
    })()""")
    page.wait_for_timeout(500)
    yt2 = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var th = t.querySelector('thead th.ws-tt-emp');
        return { thW: th.getBoundingClientRect().width,
                 head: th.querySelector('.ws-tt-emp-head').textContent,
                 name: t.querySelector('tbody .ws-tt-name').textContent };
    })()""")
    print('TT year:', json.dumps(yt, ensure_ascii=False), '->', json.dumps(yt2, ensure_ascii=False))
    page.screenshot(path='scripts/task336-exp-tt-year.png')
    ctx.close(); browser.close()
print('DONE')
