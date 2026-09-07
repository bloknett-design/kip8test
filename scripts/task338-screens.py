# -*- coding: utf-8 -*-
# Task 338: скриншоты-пруфы (зритель мобайл/десктоп, редактор десктоп)
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

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
  {'id':2,'дата':'%04d-%02d-05' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
]
CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'}
]

STATE = {'role': 'КИП ИОС дежурный', 'ws_edit': False}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':STATE['role'],'found':True,
                'permissions':{'workschedule.view':True,'workschedule.edit':STATE['ws_edit']}}}
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

def setup_ctx(browser, viewport, token, role, ws_edit, dsf=1):
    STATE['role'] = role
    STATE['ws_edit'] = ws_edit
    ctx = browser.new_context(viewport=viewport, device_scale_factor=dsf)
    page = ctx.new_page()
    page.on('pageerror', lambda e: print('JS ERROR:', e))
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
    page.evaluate("localStorage.setItem('kip8_ws_view_v1','day')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page

with sync_playwright() as p:
    browser = p.chromium.launch()

    # 1: мобильный зритель
    ctx, page = setup_ctx(browser, {'width':375,'height':720}, 'proof338-mob', 'КИП ИОС дежурный', False, dsf=3)
    page.evaluate("navigateTo('docs-ios')"); page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')"); page.wait_for_timeout(1600)
    page.screenshot(path='scripts/task338-proof-mobile-viewer.png')
    ctx.close()

    # 2: десктоп зритель
    ctx, page = setup_ctx(browser, {'width':1280,'height':800}, 'proof338-deskview', 'КИП ИОС дежурный', False)
    page.evaluate("navigateTo('work-schedule')"); page.wait_for_timeout(1800)
    page.screenshot(path='scripts/task338-proof-desktop-viewer.png')
    ctx.close()

    # 3: десктоп редактор (для сравнения)
    ctx, page = setup_ctx(browser, {'width':1280,'height':800}, 'proof338-deskedit', 'КИП ИОС', True)
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    page.evaluate("navigateTo('work-schedule')"); page.wait_for_timeout(1800)
    page.screenshot(path='scripts/task338-proof-desktop-editor.png')
    ctx.close()

    browser.close()
print('screenshots done')
