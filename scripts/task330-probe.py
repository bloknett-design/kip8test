# -*- coding: utf-8 -*-
# Task 330 probe: замер ТЕКУЩИХ цветов/шрифтов до правок
import datetime, json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8960
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
  {'id':3,'дата':'%04d-%02d-04' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'}
]
STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        admin = STATE['role'] == 'Админ'
        return {'ok':True,'data':{'role':STATE['role'],'found':True,'permissions':{'workschedule.view':True,'workschedule.edit':admin,'flowmeter.view':True}}}
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
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':[]}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':[]}}
    if action == 'workSchedule.getProdCalendar':
        return {'ok':True,'data':{'calendar':{}}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for theme in ('dark','light'):
        ctx = browser.new_context(viewport={'width':1280,'height':800})
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
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
        page.goto('http://localhost:%d/index.html' % PORT)
        page.evaluate("localStorage.setItem('kip8_session_token','probe-t330')")
        page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
        page.reload()
        page.wait_for_timeout(2200)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        res = page.evaluate("""(function(){
          function cs(sel, prop){ var el=document.querySelector(sel); if(!el) return null;
            var c = getComputedStyle(el); return {bg: c.backgroundColor, bgImage: c.backgroundImage.slice(0,60), color: c.color, fs: c.fontSize, fw: c.fontWeight}; }
          var out = {};
          out.thead_th      = cs('.ws-grid thead th.ws-day-col:not(.ws-today-col)');
          out.thead_emp     = cs('.ws-grid thead th.ws-emp-col');
          out.tbody_emp     = cs('.ws-grid tbody td.ws-emp-col');
          out.tbody_cell    = cs('.ws-grid tbody td.ws-cell');
          out.toolbar       = cs('.ws-toolbar');
          out.events_panel  = cs('#wsEventsPanel');
          out.cal_panel     = cs('#wsCalPanel');
          // тексты окон бара
          function txt(sel){ var el=document.querySelector(sel); if(!el) return null; var c=getComputedStyle(el); return {color:c.color, fs:c.fontSize}; }
          out.ep_cap        = txt('#wsEventsPanel .ws-cp-cap');
          var epItems = document.querySelectorAll('#wsEventsPanel .ws-cp-empty');
          out.ep_empty      = epItems.length ? txt('#wsEventsPanel .ws-cp-empty') : null;
          out.cp_cap        = txt('#wsCalPanel .ws-cp-cap');
          out.cp_col        = txt('#wsCalPanel .ws-cp-col');
          out.cp_item       = txt('#wsCalPanel .ws-cp-item');
          out.cp_item_b     = txt('#wsCalPanel .ws-cp-item b');
          out.cp_legend     = txt('#wsCalPanel .ws-cp-legend');
          out.cp_day        = txt('#wsCalPanel .ws-cp-day');
          out.cp_empty      = txt('#wsCalPanel .ws-cp-empty');
          // попап кодов — открыть ячейку
          var cell = document.querySelector('.ws-grid tbody td.ws-cell');
          if (cell) { cell.click(); }
          return out;
        })""")
        page.wait_for_timeout(600)
        popup = page.evaluate("""(function(){
          function cs(sel, prop){ var el=document.querySelector(sel); if(!el) return null;
            var c = getComputedStyle(el); return {color: c.color, fs: c.fontSize, lh: c.lineHeight}; }
          var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
          return {name: cs('#wsCellPopup .ws-popup-name'), code: cs('#wsCellPopup .ws-popup-code'),
                  rowCount: rows.length, title: cs('#wsCellPopup .ws-popup-title')};
        })""")
        print('=== THEME %s ===' % theme)
        print('HEADER thead th:', res['thead_th'])
        print('HEADER thead emp:', res['thead_emp'])
        print('BODY emp col:', res['tbody_emp'])
        print('BODY cell:', res['tbody_cell'])
        print('TOOLBAR:', res['toolbar'])
        print('EVENTS panel:', res['events_panel'])
        print('CAL panel:', res['cal_panel'])
        print('ep_cap:', res['ep_cap'], 'ep_empty:', res['ep_empty'])
        print('cp_cap:', res['cp_cap'], 'cp_col:', res['cp_col'])
        print('cp_item:', res['cp_item'], 'cp_item_b:', res['cp_item_b'])
        print('cp_legend:', res['cp_legend'], 'cp_day:', res['cp_day'], 'cp_empty:', res['cp_empty'])
        print('POPUP name:', popup['name'], 'code:', popup['code'], 'title:', popup['title'], 'rows:', popup['rowCount'])
        print('JS errors:', errors)
        page.screenshot(path='scripts/task330-probe-%s.png' % theme, full_page=False)
        ctx.close()
    browser.close()
print('DONE')
