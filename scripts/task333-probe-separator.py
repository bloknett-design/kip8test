# -*- coding: utf-8 -*-
# Task 333 probe: ВИЗУАЛЬНАЯ проверка разделительной полосы между
# колонкой ФИО и ячейками шахматки при ГОРИЗОНТАЛЬНОЙ прокрутке
# (gridwide, шторка открыта). Снимаем кропы границы ДО и ПОСЛЕ
# прокрутки в Chromium и Firefox.
import datetime, json, sys
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
  {'id':4,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        if body and body.get('includeArchived'):
            return {'ok':True,'data':{'employees':EMPLOYEES}}
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    return {'ok':True,'data':{'ok':True}}

def probe(browser, engine):
    ctx = browser.new_context(viewport={'width':1024,'height':768})
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
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, content_type='text/plain', body='nf'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, content_type='text/plain', body='nf'))
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','probe-t333')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    # открыть шторку (gridwide)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    info = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var emp = wrap.querySelector('table tbody td.ws-emp-col');
        var er = emp.getBoundingClientRect();
        return { scrollW: wrap.scrollWidth, clientW: wrap.clientWidth,
                 empRight: er.right, empTop: er.top, empH: er.height,
                 border: getComputedStyle(emp).borderRightWidth + ' ' + getComputedStyle(emp).borderRightStyle,
                 canScroll: wrap.scrollWidth > wrap.clientWidth };
    })""")
    print('[%s] grid: scrollW=%s clientW=%s canScroll=%s empRight=%.1f border=%s'
          % (engine, info['scrollW'], info['clientW'], info['canScroll'], info['empRight'], info['border']))
    def crop(tag):
        # кроп: x = empRight - 4 .. empRight + 40, y = тело сетки 60px
        x = max(0, info['empRight'] - 6)
        page.screenshot(path='probe-%s-%s.png' % (engine, tag),
                        clip={'x': x, 'y': info['empTop'], 'width': 60, 'height': 90})
    crop('before')
    if info['canScroll']:
        page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 300")
        page.wait_for_timeout(400)
        crop('after300')
        # измерить цвет полосы на границе ПОСЛЕ прокрутки по пикселям канваса
        px = page.evaluate("""(function(){
            var emp = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
            var er = emp.getBoundingClientRect();
            return { right: er.right, top: er.top, h: er.height };
        })()""")
        print('[%s] после прокрутки 300: sticky-колонка right=%.1f (была %.1f)'
              % (engine, px['right'], info['empRight']))
    else:
        print('[%s] НЕЧЕГО прокручивать (сетка влезла) — увеличу выборку' % engine)
    ctx.close()

with sync_playwright() as p:
    probe(p.chromium.launch(), 'chromium')
    try:
        probe(p.firefox.launch(), 'firefox')
    except Exception as e:
        print('firefox недоступен: %s' % e)
print('done')
