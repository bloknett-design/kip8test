#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 356: browser-check — заявка пользователя (шахматка табеля):
# «пустые ячейки без кодов событий тоже должны быть без точек» —
# точка «·» по центру убрана и на РАБОЧИХ днях:
#   • пустая ячейка без записи — чистый центр;
#   • «.» (плановый выходной) — чистый центр (маркер ws-dot-code жив,
#     фон как у пустой);
#   • статус-мероприятие «И» — центр пуст, сплошной бейдж в углу;
#   • заполненные (коды смен, планы «ОТ», бейджи) — прежний вид;
#   • Task 355 жив: нерабочие без «·», розовый #f8e2e9, линии 1px
#     ярче (30% чёрного / стале-голубые), шапка с вертикалями.
# Контексты: десктоп 1280 тёмная/светлая, мобайл 390 тёмная.
# Праздник — сеяный кэш ProdCalendar (2026-09-08, вторник).
# + 0 JS-ошибок; скриншоты-пруфы.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8952
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

# день-праздник: вторник 2026-09-08 (сеем в кэш ProdCalendar)
HOLIDAY_DAY = 8
# субботы сентября 2026: 5, 12, 19, 26
SAT = 5
# рабочий день с записью «.» (четверг 10) и суббота с «.» (12)
DOT_WORKDAY = 10
DOT_SAT = 12
# пустой рабочий день (вторник 1) — теперь БЕЗ точки
EMPTY_WORKDAY = 1
# рабочий день со статус-мероприятием «И» (среда 2) — центр пуст,
# виртуальный бейдж «И» в углу
EVENT_DAY = 2

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной','color':'#EEF0F2'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'}
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
  # «.» на РАБОЧЕМ дне — центр ПУСТ (Task 356)
  {'id':3,'дата':'%04d-%02d-%02d' % (Y, M, DOT_WORKDAY),'таб_номер':'017','статус':'.','источник':'авто'},
  # «.» на СУББОТУ — центр пуст (Task 355)
  {'id':4,'дата':'%04d-%02d-%02d' % (Y, M, DOT_SAT),'таб_номер':'023','статус':'.','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':6,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'023','статус':'д','часы':7.2,'источник':'руч'},
  # статус-мероприятие «И» на рабочем дне — центр пуст + бейдж (Task 356)
  {'id':7,'дата':'%04d-%02d-%02d' % (Y, M, EVENT_DAY),'таб_номер':'023','статус':'И','источник':'авто'}
]
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'}
]

STATE = {'role': 'Админ'}

# кэш ProdCalendar: год 2026, регион 42 — праздник 8 сентября
def seed_pcal_js(page):
    # setItem принимает СТРОКУ: json.dumps дважды — JS-строковый литерал
    js_literal = json.dumps(json.dumps(pcal_seed()))
    page.evaluate("localStorage.setItem('ws_pcal_year2_%d_42', %s)" % (Y, js_literal))

def pcal_seed():
    return {
        'source': 'legalic',
        'fetchedAtMs': int(datetime.datetime.now().timestamp() * 1000),
        'region': 42, 'regionName': 'Кемеровская область - Кузбасс',
        'version': None,
        'norms': {'d40': 176, 'd36': 158.4, 'd24': 105.6, 'year': 1972.4},
        # ключ дня — ММДД БЕЗ дефиса (ProdCalendar._mmdd)
        'days': {'0908': {'off': True, 'holiday': True, 'title': 'Тестовый праздник (Task 355)'}}
    }

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
        month = body.get('month') if body else None
        if month == M:
            return {'ok':True,'data':{'entries':ENTRIES}}
        return {'ok':True,'data':{'entries':YEAR_ENTRY(month or 1)}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def setup_ctx(browser, viewport, token, theme=None, role='Админ'):
    STATE['role'] = role
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
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t356)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

JS_CELL = """(function(day){
    var td = document.querySelector('#wsGridWrap table tbody td.ws-cell[data-day="' + day + '"]');
    if (!td) return null;
    var cs = getComputedStyle(td);
    // центральный текст — только текстовые узлы ДО первого элемента (бейджи не в счёт)
    var main = '';
    for (var n = td.firstChild; n && n.nodeType === 3; n = n.nextSibling) main += n.nodeValue;
    return { text: main, all: td.textContent.trim(), weekend: td.classList.contains('ws-weekend'),
             empty: td.classList.contains('ws-status-empty'), dot: td.classList.contains('ws-dot-code'),
             badge: !!td.querySelector('.ws-ev-badge'), pending: !!td.querySelector('.ws-ev-pending'),
             bg: cs.backgroundColor, bl: cs.borderLeftColor, blw: cs.borderLeftWidth };
})"""

# ячейка из ВТОРОЙ строки (дневной Петров 023 — «И»-мероприятие и «.»-суббота)
JS_CELL_ROW2 = """(function(day){
    var td = document.querySelector('#wsGridWrap table tbody tr:nth-child(2) td.ws-cell[data-day="' + day + '"]');
    if (!td) return null;
    var cs = getComputedStyle(td);
    // центральный текст — только текстовые узлы ДО первого элемента
    var main = '';
    for (var n = td.firstChild; n && n.nodeType === 3; n = n.nextSibling) main += n.nodeValue;
    var badge = td.querySelector('.ws-ev-badge');
    return { text: main, dot: td.classList.contains('ws-dot-code'),
             weekend: td.classList.contains('ws-weekend'), badge: !!badge,
             badgeBg: badge ? getComputedStyle(badge).backgroundColor : null,
             badgeText: badge ? badge.textContent.trim() : null };
})"""

JS_HEAD = """(function(day){
    var th = document.querySelector('#wsGridWrap table thead th[data-day="' + day + '"]');
    if (!th) return null;
    var cs = getComputedStyle(th);
    return { feast: th.classList.contains('ws-feast'), holiday: th.classList.contains('ws-holiday'),
             bl: cs.borderLeftColor, blw: cs.borderLeftWidth, bt: cs.borderTopWidth };
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t356-a', theme='dark')
    seed_pcal_js(page)
    page.reload()
    page.wait_for_timeout(2000)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # --- Task 356: точка убрана в пустых ячейках РАБОЧИХ дней ---
    workempty = page.evaluate(JS_CELL + '(%d)' % EMPTY_WORKDAY)
    check('C: пустой рабочий день — точки «·» НЕТ (Task 356)',
          workempty['text'] == '' and '·' not in (workempty['text'] or ''), workempty)
    check('C2: пустой рабочий — ws-status-empty, НЕ ws-weekend',
          workempty['empty'] and not workempty['weekend'], workempty)
    workdot = page.evaluate(JS_CELL + '(%d)' % DOT_WORKDAY)
    check('D: рабочий день с «.» — точки НЕТ, ws-dot-code жив (Task 356)',
          workdot['text'] == '' and workdot['dot'], workdot)
    check('D2: «.»-ячейка — бейджа нет, фон как у пустой (rgb 238,240,242)',
          not workdot['badge'] and workdot['bg'] == workempty['bg'],
          {'dot': workdot['bg'], 'empty': workempty['bg']})
    # «И» на рабочем дне — вторая строка (Петров)
    ev = page.evaluate(JS_CELL_ROW2 + '(%d)' % EVENT_DAY)
    check('E: статус-мероприятие «И» — центр ПУСТ, бейдж есть (Task 356)',
          ev['text'] == '' and ev['badge'], ev)
    check('E2: бейдж «И» сплошной #B3E5FC (rgb 179,229,252)',
          ev['badgeText'] == 'И' and ev['badgeBg'] == 'rgb(179, 229, 252)', ev)
    # заполненные ячейки не задеты: Иванов (строка 1), день 2 — смена «Д»
    shift = page.evaluate(JS_CELL + '(%d)' % 2)
    check('F: смена Д — код по центру (заполненные не тронуты)',
          shift['text'].strip() == 'Д', shift)

    # --- Task 355 жив: нерабочие без точки, розовый, линии ---
    sat = page.evaluate(JS_CELL + '(%d)' % SAT)
    check('G: суббота (пустая) — точки «·» НЕТ (Task 355)', sat['text'] == '', sat)
    check('G2: суббота — ws-weekend + ws-status-empty', sat['weekend'] and sat['empty'], sat)
    hol = page.evaluate(JS_CELL + '(%d)' % HOLIDAY_DAY)
    check('H: праздник (вт 08) — точки НЕТ, ws-weekend', hol['text'] == '' and hol['weekend'], hol)
    satdot = page.evaluate(JS_CELL_ROW2 + '(%d)' % DOT_SAT)
    check('I: суббота с кодом «.» — точки НЕТ, ws-dot-code жив',
          satdot['text'] == '' and satdot['dot'], satdot)

    check('J: розовый выходных = #f8e2e9 (rgb 248,226,233)',
          sat['bg'] == 'rgb(248, 226, 233)', sat['bg'])
    sun = page.evaluate(JS_CELL + '(%d)' % 6)
    check('K: тело: граница дня 30% чёрного (Task 355/319)', sun['bl'] == 'rgba(0, 0, 0, 0.3)', sun['bl'])
    check('K2: тело: толщина 1px (тонкие)', sun['blw'] == '1px', sun['blw'])
    head = page.evaluate(JS_HEAD + '(%d)' % 12)
    check('L: шапка: вертикальная граница 1px стале-голубая 55%',
          head['blw'] == '1px' and head['bl'] == 'rgba(140, 158, 188, 0.55)', head)
    red = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-boundary-after');
        return td ? getComputedStyle(td).borderRightColor : null;
    })()""")
    check('M: красный стык Task 255 НЕ перекрашен (#cc6e73)', red == 'rgb(204, 110, 115)', red)
    page.screenshot(path='scripts/task356-proof-dark.png')
    check('N: 0 JS-ошибок (тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: десктоп 1280, светлая =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t356-b', theme='light')
    seed_pcal_js(page2)
    page2.reload()
    page2.wait_for_timeout(2000)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    we2 = page.evaluate if False else page2.evaluate(JS_CELL + '(%d)' % EMPTY_WORKDAY)
    check('O: светлая: пустой рабочий день — точки НЕТ', we2['text'] == '', we2)
    wd2 = page2.evaluate(JS_CELL + '(%d)' % DOT_WORKDAY)
    check('P: светлая: «.» на рабочем дне — точки НЕТ, ws-dot-code жив',
          wd2['text'] == '' and wd2['dot'], wd2)
    check('P2: светлая: «.»-ячейка фон = пустой (#eef0f2 → rgb 238,240,242)',
          wd2['bg'] == we2['bg'] == 'rgb(238, 240, 242)', {'dot': wd2['bg'], 'empty': we2['bg']})
    ev2 = page2.evaluate(JS_CELL_ROW2 + '(%d)' % EVENT_DAY)
    check('Q: светлая: «И» — центр ПУСТ, бейдж есть',
          ev2['text'] == '' and ev2['badge'], ev2)
    sat2 = page2.evaluate(JS_CELL + '(%d)' % SAT)
    check('R: светлая: суббота пустая — точки НЕТ, розовый #f8e2e9',
          sat2['text'] == '' and sat2['bg'] == 'rgb(248, 226, 233)', sat2)
    sun2 = page2.evaluate(JS_CELL + '(%d)' % 6)
    check('S: светлая: границы дней 30% чёрного, 1px',
          sun2['bl'] == 'rgba(0, 0, 0, 0.3)' and sun2['blw'] == '1px', sun2)
    red2 = page2.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-boundary-after');
        return td ? getComputedStyle(td).borderRightColor : null;
    })()""")
    check('T: светлая: красный стык жив (#cc6e73)', red2 == 'rgb(204, 110, 115)', red2)
    page2.screenshot(path='scripts/task356-proof-light.png')
    check('U: 0 JS-ошибок (светлая)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 390, тёмная =================
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':390,'height':760}, 'bc-t356-c', theme='dark')
    seed_pcal_js(page3)
    page3.reload()
    page3.wait_for_timeout(2000)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    we3 = page3.evaluate(JS_CELL + '(%d)' % EMPTY_WORKDAY)
    check('V: мобайл: пустой рабочий день — точки НЕТ', we3['text'] == '', we3)
    wd3 = page3.evaluate(JS_CELL + '(%d)' % DOT_WORKDAY)
    check('W: мобайл: «.» на рабочем дне — точки НЕТ', wd3['text'] == '' and wd3['dot'], wd3)
    sat3 = page3.evaluate(JS_CELL + '(%d)' % SAT)
    check('X: мобайл: суббота — точки НЕТ, розовый', sat3['text'] == '' and sat3['bg'] == 'rgb(248, 226, 233)', sat3)
    page3.screenshot(path='scripts/task356-proof-mobile.png')
    check('Y: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
