# -*- coding: utf-8 -*-
# Debug Task 341: кто вызывает window.print дважды?
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8946
CODES = [{'code':'Д','name':'День (12-час)','color':'#FFE082'}]
EMPLOYEES = [{'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'должность':'Слесарь КИПиА'}]
ENTRIES = [{'id':1,'дата':'2026-09-02','таб_номер':'017','статус':'Д','источник':'авто'}]

STATE = {'empty': False}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'u@t.local','role':'КИП ИОС'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'КИП ИОС','found':True,
                'permissions':{'workschedule.edit':True}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':([] if STATE['empty'] else EMPLOYEES)}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':[]}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':[]}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':[]}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':1280,'height':800})
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
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, body='x'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, body='x'))
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','dbg-t341')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    # 1) только установка стаба БЕЗ клика
    r = page.evaluate("""(function(){
        window.__pgCalls = 0; window.__printCalls = 0;
        var orig = WorkSchedule.printGrid;
        WorkSchedule.printGrid = function(){ window.__pgCalls++; return orig.apply(this, arguments); };
        window.print = function(){ window.__printCalls++; };
        return 'installed';
    })()""")
    page.wait_for_timeout(400)
    r = page.evaluate("({pg: window.__pgCalls, pr: window.__printCalls})")
    print('после установки стаба (без клика):', r)

    # 2) клик
    page.evaluate("document.getElementById('wsPrintBtn').click()")
    page.wait_for_timeout(400)
    r = page.evaluate("({pg: window.__pgCalls, pr: window.__printCalls})")
    print('после ОДНОГО клика:', r)

    # 3) стек вызова window.print
    page.evaluate("""(function(){
        window.__stacks = [];
        window.print = function(){ window.__stacks.push(new Error('who').stack); };
        document.getElementById('wsPrintBtn').click();
        return 'clicked2';
    })()""")
    page.wait_for_timeout(300)
    st = page.evaluate("window.__stacks")
    print('=== стеки window.print (%d):' % len(st))
    for s in st:
        print(s[:700])
        print('---')
    print('JS errors:', js_errors[:5])
    browser.close()
