# -*- coding: utf-8 -*-
# Task 330: browser-check — заявка пользователя:
#   • фон шапки шахматки (кнопка «Сотрудник +» + дни недель) — ТЕМНЕЕ,
#     ближе к СИНЕ-СЕРОМУ цвету;
#   • окно выбора кодов ячеек — шрифт текста ОПИСАНИЙ кодов маленький;
#   • светлая тема — ВЕСЬ текст в окнах «Мероприятия» и «Нормы времени»
#     бара табеля — ЧЁРНЫЙ.
# Проверки (десктоп 1280): тёмная — шапка #1e293b (th дня и th ФИО),
#   hover «Сотрудник +» #2a3a4c; попап кодов — .ws-popup-name 10px
#   (код 13px, заголовок 11px не тронуты); 0 JS-ошибок.
#   Светлая — шапка #bfcad5 (колонка ФИО тела — прежняя 240,240,240),
#   события: заголовок/строки/даты/«нет мероприятий» — rgb(0,0,0);
#   нормы: столбики/плашки/легенда/пусто/ЧИПЫ дней (мок legalic:
#   праздник/перенос/сокращённый) — rgb(0,0,0), подложки цветные.
#   Мобильный 375 (светлая): шапка #bfcad5, описания 10px.
import datetime
import json, sys
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
  {'id':3,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = [
  {'id':9,'дата_начала':'%04d-%02d-10' % (Y, M),'дата_окончания':'%04d-%02d-11' % (Y, M),
   'таб_номер':'017','тип':'инструктаж','тема':'Охрана труда'}
]

# мок calendar.legalic.ru: праздник (k-hol), перенос (k-tr),
# сокращённый (k-sh) в ТЕКУЩЕМ месяце + рабочие дни с минутами
def legalic_json():
    days = []
    for d in range(1, 29):
        iso = '%04d-%02d-%02d' % (Y, M, d)
        rec = {'date': iso, 'type': 'WORKING', 'minutes': {'40h': 480, '36h': 432, '24h': 288}}
        if d in (6, 7, 13, 14, 20, 21, 27, 28):
            rec = {'date': iso, 'type': 'WEEKEND'}
        days.append(rec)
    # праздник 8-го числа
    days[7] = {'date': '%04d-%02d-08' % (Y, M), 'type': 'PUBLIC_HOLIDAY', 'holidayName': 'Тестовый праздник'}
    # перенесённый выходной 9-го
    days[8] = {'date': '%04d-%02d-09' % (Y, M), 'type': 'TRANSFERRED_DAY_OFF', 'transferredFrom': '%04d-%02d-12' % (Y, M)}
    # сокращённый рабочий 10-го
    days[9] = {'date': '%04d-%02d-10' % (Y, M), 'type': 'SHORTENED_WORKING'}
    return {'version': {'versionId': 't330-v1'}, 'days': days}

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
        return {'ok':True,'data':{'trainings':TRAININGS}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def setup_ctx(browser, viewport, token, theme=None):
    ctx = browser.new_context(viewport=viewport)
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
    def legalic(route):
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(legalic_json(), ensure_ascii=False).encode('utf-8'))
    ctx.route('**calendar.legalic.ru/**', legalic)
    ctx.route('**raw.githubusercontent.com/**', legalic)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    # снести кэш произв. календаря (ws_pcal_year2_*)
    page.evaluate("""(function(){
        var kill = [];
        for (var i=0;i<localStorage.length;i++){ var k=localStorage.key(i);
            if (k && k.indexOf('ws_pcal_year2_')===0) kill.push(k); }
        kill.forEach(function(k){ localStorage.removeItem(k); });
    })()""")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, Админ, тёмная =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t330-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА' && !!document.querySelector('#page-dashboard')"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- шапка: сине-серый #1e293b ----------
    s1 = page.evaluate("""(function(){
        function bg(sel){ var el=document.querySelector(sel); if(!el) return null;
            return getComputedStyle(el).backgroundColor; }
        var dayTh = document.querySelector('.ws-grid thead th.ws-day-col');
        return {dayBg: bg('.ws-grid thead th.ws-day-col'),
                empBg: bg('.ws-grid thead th.ws-emp-col'),
                bodyEmpBg: bg('.ws-grid tbody td.ws-emp-col'),
                dayThOk: !!dayTh};
    })""")
    check('C: шапка (дни) — сине-серый #1e293b', s1['dayBg'] == 'rgb(30, 41, 59)', s1)
    check('C2: шапка (Сотрудник +) — тот же сине-серый', s1['empBg'] == 'rgb(30, 41, 59)', s1)
    check('C3: тело (колонка ФИО) — прежний #0e1621', s1['bodyEmpBg'] == 'rgb(14, 22, 33)', s1)

    # hover «Сотрудник +» — светлее шапки #2a3a4c
    page.hover('.ws-grid thead th.ws-emp-col')
    page.wait_for_timeout(300)
    hov = page.evaluate("(function(){var el=document.querySelector('.ws-grid thead th.ws-emp-col'); return getComputedStyle(el).backgroundColor;})()")
    check('C4: hover «Сотрудник +» — #2a3a4c (светлее шапки)', hov == 'rgb(42, 58, 76)', hov)

    # ---------- попап кодов: маленький шрифт описаний ----------
    page.evaluate("document.querySelector('.ws-grid tbody td.ws-cell').click()")
    page.wait_for_timeout(600)
    s2 = page.evaluate("""(function(){
        var name = document.querySelector('#wsCellPopup .ws-popup-name');
        var code = document.querySelector('#wsCellPopup .ws-popup-code');
        var title = document.querySelector('#wsCellPopup .ws-popup-title');
        var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row').length;
        return {nameFs: name?getComputedStyle(name).fontSize:null,
                nameLh: name?getComputedStyle(name).lineHeight:null,
                codeFs: code?getComputedStyle(code).fontSize:null,
                titleFs: title?getComputedStyle(title).fontSize:null,
                rows: rows,
                open: !!document.getElementById('wsCellPopup') && !document.getElementById('wsCellPopup').hidden};
    })""")
    check('D: окно кодов открыто, строки есть', s2['open'] and s2['rows'] > 0, s2)
    check('D2: ОПИСАНИЕ кода — 10px (маленький)', s2['nameFs'] == '10px', s2)
    check('D3: код 13px и заголовок 11px — НЕ уменьшены', s2['codeFs'] == '13px' and s2['titleFs'] == '11px', s2)
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    check('E: 0 JS-ошибок (тёмная)', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task330-proof-dark.png')
    ctx.close()

    # ================= Контекст 2: десктоп 1280, светлая =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t330-b', theme='light')
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('F: сетка отрисована (светлая)', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    s3 = page.evaluate("""(function(){
        function st(sel, prop){ var el=document.querySelector(sel); if(!el) return null;
            var c=getComputedStyle(el); return c[prop]; }
        return {theadBg: st('.ws-grid thead th.ws-day-col','backgroundColor'),
                theadEmpBg: st('.ws-grid thead th.ws-emp-col','backgroundColor'),
                bodyEmpBg: st('.ws-grid tbody td.ws-emp-col','backgroundColor'),
                theadColor: st('.ws-grid thead th.ws-day-col','color'),
                epCapColor: st('#wsEventsPanel .ws-ep-cap','color'),
                epCapBg: st('#wsEventsPanel .ws-ep-cap','backgroundColor'),
                epItemColor: st('#wsEventsPanel .ws-ep-item','color'),
                epDateColor: st('#wsEventsPanel .ws-ep-date','color'),
                epTextColor: st('#wsEventsPanel .ws-ep-text','color'),
                cpColColor: st('#wsCalPanel .ws-cp-col','color'),
                cpItemB: st('#wsCalPanel .ws-cp-item b','color'),
                normsCapColor: st('#wsCalPanel .ws-cp-norms > .ws-cp-cap','color'),
                normsCapBg: st('#wsCalPanel .ws-cp-norms > .ws-cp-cap','backgroundColor'),
                daysCapColor: st('#wsCalPanel .ws-cp-days > .ws-cp-cap','color'),
                daysCapBg: st('#wsCalPanel .ws-cp-days > .ws-cp-cap','backgroundColor'),
                legendColor: st('#wsCalPanel .ws-cp-legend','color'),
                chipCount: document.querySelectorAll('#wsCalPanel .ws-cp-day').length,
                chipHolColor: st('#wsCalPanel .ws-cp-day.k-hol','color'),
                chipHolBg: st('#wsCalPanel .ws-cp-day.k-hol','backgroundColor'),
                chipShColor: st('#wsCalPanel .ws-cp-day.k-sh','color'),
                epHasItems: document.querySelectorAll('#wsEventsPanel .ws-ep-item').length,
                epCapText: (document.querySelector('#wsEventsPanel .ws-ep-cap')||{}).textContent};
    })""")
    check('G: шапка светлая — сине-серый #bfcad5', s3['theadBg'] == 'rgb(191, 202, 213)', s3['theadBg'])
    check('G2: «Сотрудник +» — тот же, текст тёмный', s3['theadEmpBg'] == 'rgb(191, 202, 213)' and s3['theadColor'] == 'rgb(51, 51, 51)', s3)
    check('G3: колонка ФИО тела — прежняя 240,240,240', s3['bodyEmpBg'] == 'rgba(240, 240, 240, 0.95)', s3['bodyEmpBg'])

    # ---------- окно мероприятий: весь текст чёрный ----------
    check('H: заголовок мероприятий — чёрный (зелёная подложка жива)',
          s3['epCapColor'] == 'rgb(0, 0, 0)' and s3['epCapBg'] == 'rgba(76, 199, 113, 0.16)', s3)
    check('H2: мероприятия есть в окне', s3['epHasItems'] > 0, s3)
    check('H3: строки/даты/текст мероприятий — чёрные',
          s3['epItemColor'] == 'rgb(0, 0, 0)' and s3['epDateColor'] == 'rgb(0, 0, 0)' and s3['epTextColor'] == 'rgb(0, 0, 0)', s3)

    # ---------- окно норм: весь текст чёрный ----------
    check('I: столбики норм/значения b — чёрные',
          s3['cpColColor'] == 'rgb(0, 0, 0)' and s3['cpItemB'] == 'rgb(0, 0, 0)', s3)
    check('I2: плашки «Норма»/«Праздники» — чёрный текст, цветные подложки',
          s3['normsCapColor'] == 'rgb(0, 0, 0)' and s3['daysCapColor'] == 'rgb(0, 0, 0)'
          and s3['normsCapBg'] == 'rgba(74, 143, 199, 0.16)' and s3['daysCapBg'] == 'rgba(255, 107, 107, 0.15)', s3)
    check('I3: легенда — чёрная', s3['legendColor'] == 'rgb(0, 0, 0)', s3)
    check('I4: чипы дней есть (мок legalic)', s3['chipCount'] >= 3, s3)
    check('I5: чипы (праздник/сокращённый) — чёрный текст, подложки цветные',
          s3['chipHolColor'] == 'rgb(0, 0, 0)' and s3['chipShColor'] == 'rgb(0, 0, 0)'
          and s3['chipHolBg'] == 'rgba(255, 107, 107, 0.16)', s3)

    # ---------- попап кодов в светлой: описания тоже 10px ----------
    page.evaluate("document.querySelector('.ws-grid tbody td.ws-cell').click()")
    page.wait_for_timeout(500)
    s4 = page.evaluate("""(function(){
        var name = document.querySelector('#wsCellPopup .ws-popup-name');
        return {fs: name?getComputedStyle(name).fontSize:null,
                color: name?getComputedStyle(name).color:null};
    })""")
    check('J: описания кодов 10px (светлая)', s4['fs'] == '10px', s4)
    page.keyboard.press('Escape')
    check('K: 0 JS-ошибок (светлая)', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task330-proof-light.png')
    ctx.close()

    # ================= Контекст 3: мобильный 375, светлая =================
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':700}, 'browser-check-t330-c', theme='light')
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    s5 = page.evaluate("""(function(){
        var th = document.querySelector('.ws-grid thead th.ws-day-col');
        var name = document.querySelector('#wsCellPopup .ws-popup-name');
        return {bg: th?getComputedStyle(th).backgroundColor:null};
    })""")
    check('L: мобайл — шапка #bfcad5', s5['bg'] == 'rgb(191, 202, 213)', s5)
    page.evaluate("document.querySelector('.ws-grid tbody td.ws-cell').click()")
    page.wait_for_timeout(500)
    s6 = page.evaluate("(function(){var n=document.querySelector('#wsCellPopup .ws-popup-name'); return n?getComputedStyle(n).fontSize:null;})()")
    check('M: мобайл — описания 10px', s6 == '10px', s6)
    check('N: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path='task330-proof-mobile.png')
    ctx.close()
    browser.close()

print('==============================')
print('ИТОГО: %d/%d, FAIL=%d' % (PASS, PASS+FAIL, FAIL))
sys.exit(0 if FAIL == 0 else 1)
