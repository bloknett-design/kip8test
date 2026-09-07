# -*- coding: utf-8 -*-
# Debug Task 341 v2: точный флоу browser-check context 1 + стеки вызовов
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8946
CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'.','name':'Плановый выходной','color':'#EEF0F2'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Мастер КИПиА','комментарий':''},
  {'таб_номер':'031','ФИО':'Сидоров Сидор Сидорович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2023-06-01','дата_увольнения':'','в_архиве':0,'должность':'Инженер','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'}]}
]
ENTRIES = [
  {'id':1,'дата':'2026-09-02','таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'2026-09-02','таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':3,'дата':'2026-09-02','таб_номер':'031','статус':'Д8','источник':'авто'}
]

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
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':[]}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
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
    page.evaluate("localStorage.setItem('kip8_session_token','dbg-t341-v2')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    # E1/E2 как в browser-check
    page.evaluate("""(function(){
        var b = document.getElementById('wsPrintBtn');
        return { hidden: b.hidden, w: b.offsetWidth, label: b.textContent.trim() };
    })()""")
    page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")

    # do_print с захватом стеков
    page.evaluate("""(function(){
        window.__printCalls = 0;
        window.__stacks = [];
        window.print = function(){
            window.__printCalls++;
            window.__stacks.push(new Error('who').stack);
        };
    })()""")
    page.evaluate("document.getElementById('wsPrintBtn').click()")
    page.wait_for_timeout(250)
    calls = page.evaluate("window.__printCalls")
    print('CALLS =', calls)
    st = page.evaluate("window.__stacks")
    for i, s in enumerate(st):
        print('--- стек', i+1, '---')
        print(s[:600])
    print('JS errors:', js_errors[:3])
    browser.close()
