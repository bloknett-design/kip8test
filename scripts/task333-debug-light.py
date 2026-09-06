# -*- coding: utf-8 -*-
# Отладка: почему пиксельная проба полосы ФИО падает в светлой теме (1024).
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from PIL import Image

PORT = 8944
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':[]}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for theme in ('light', 'dark'):
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
        page.goto('http://localhost:%d/index.html' % PORT)
        page.evaluate("localStorage.setItem('kip8_session_token','debug-t333')")
        page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
        page.reload()
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(3000)
        page.click('#wsTotalsBtn')
        page.wait_for_timeout(900)
        info = page.evaluate("""(function(){
            var emp = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
            var er = emp.getBoundingClientRect();
            var after = getComputedStyle(emp, '::after');
            return { right: er.right, top: er.top, w: er.width, h: er.height,
                     afterContent: after.content, afterPos: after.position,
                     afterLeft: after.left, afterW: after.width, afterBg: after.backgroundColor };
        })()""")
        print('[%s] emp-col: right=%.1f h=%.1f ::after content=%s pos=%s left=%s w=%s bg=%s'
              % (theme, info['right'], info['h'], info['afterContent'], info['afterPos'],
                 info['afterLeft'], info['afterW'], info['afterBg']))
        page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 300")
        page.wait_for_timeout(500)
        path = 'debug-%s-boundary.png' % theme
        page.screenshot(path=path, clip={'x': max(0, info['right'] - 8), 'y': info['top'] + 1,
                                         'width': 48, 'height': 40})
        im = Image.open(path).convert('RGB')
        w, h = im.size
        # печатаем цвета столбцов (средняя строка)
        y = h // 2
        cols = []
        for x in range(w):
            r, g, b = im.getpixel((x, y))
            cols.append('#%02x%02x%02x' % (r, g, b))
        print('[%s] пиксели строки y=%d (x=%d..%d): %s' % (theme, y, 0, w - 1, ' '.join(cols)))
        ctx.close()
    browser.close()
