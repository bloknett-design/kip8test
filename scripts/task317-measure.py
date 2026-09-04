# -*- coding: utf-8 -*-
# Task 317: измерение ТЕКУЩЕГО бара (до правок) — ширины трёх частей,
# потребная ширина ряда кнопок, высоты. Для выбора компоновки.
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8937
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
]
ENTRIES = [{'id':7,'дата':TODAY.isoformat(),'таб_номер':'017','статус':'Д','источник':'авто'}]
TRAININGS = [{'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Целевой инструктаж','дата_начала':'%04d-%02d-10' % (Y, M),'дата_окончания':'%04d-%02d-10' % (Y, M),'длительность_дней':1}]
VACATIONS = []

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'flowmeter.input':True,'admin.panel':True}}}
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
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    return {'ok':False,'error':'unknown action ' + str(action)}

MEASURE = """(function(){
    function R(sel){ var el = document.querySelector(sel); if (!el) return null;
        var r = el.getBoundingClientRect();
        var cs = getComputedStyle(el);
        return {w: r.width, h: r.height, x: r.x, pad: cs.padding, disp: cs.display}; }
    var kids = [];
    var tm = document.querySelector('.ws-toolbar-main');
    if (tm) for (var i=0;i<tm.children.length;i++){
        var c = tm.children[i]; var r = c.getBoundingClientRect();
        kids.push({tag: c.tagName, id: c.id, cls: c.className, w: r.width, h: r.height});
    }
    return { toolbar: R('.ws-toolbar'), barRow: R('.ws-bar-row'),
             main: R('.ws-toolbar-main'), ev: R('#wsEventsPanel'), cal: R('#wsCalPanel'),
             act: R('#wsActionsRow'), gen: R('#wsGenerateRow'),
             save: R('#wsSaveBtn'), genBtn: R('#wsGenerateBtn'),
             mainKids: kids,
             barRowDisplay: getComputedStyle(document.querySelector('.ws-bar-row')).display };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    for W in (1280, 1024):
        ctx = browser.new_context(viewport={'width': W, 'height': 800})
        page = ctx.new_page()
        def handle(route, request):
            url = request.url
            action = ''
            if 'action=' in url:
                action = url.split('action=')[1].split('&')[0]
                action = unquote(action)
            pd = request.post_data
            body = None
            if pd:
                try: body = json.loads(pd)
                except Exception: body = None
            resp = mock_response(action, body)
            route.fulfill(status=200, content_type='application/json; charset=utf-8',
                          body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, body='x'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, body='x'))
        page.goto('http://localhost:%d/index.html' % PORT)
        page.evaluate("localStorage.setItem('kip8_session_token','t317m')")
        page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
        page.reload()
        page.wait_for_timeout(2000)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        m = page.evaluate(MEASURE)
        print('=== viewport %d ===' % W)
        print(json.dumps(m, ensure_ascii=False, indent=1))
        # потребная ширина ряда 1: сумма детей + гэпы
        need = 0
        gap = 8
        for k in m['mainKids']:
            if k['tag'] in ('SELECT', 'BUTTON'):
                need += k['w'] + gap
        print('ряд1 потребная ширина ~', round(need - gap, 1), 'px; доступно 1/3 =', round(m['main']['w'], 1))
        ctx.close()
    browser.close()
