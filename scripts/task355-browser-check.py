#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 355: browser-check — заявка пользователя (шахматка табеля):
#   1. в нерабочих выходных/праздничных ячейках НЕТ точки «·» по центру
#      (рабочие дни/«.»-код/планы — прежний вид);
#   2. разделительные линии ячеек ТОНКИЕ (1px), но ЯРЧЕ: светлая —
#      30% чёрного, тёмная — 30% чёрного у дней (Task 319: дни светлые)
#      + стале-синяя 55% у ФИО; ШАПКА (дни месяца) — вертикальные
#      разделители 1px (стале-голубой 55% тёмная / 30% чёрного светлая),
#      верхняя рамка отключена (высота шапки не меняется);
#   3. розовый выходных/праздников ПАСТЕЛЬНЕЕ: #f7d9e3 → #f8e2e9
#      (обе темы).
# Контексты: десктоп 1280 тёмная, десктоп 1280 светлая, мобайл 390
# тёмная. Праздник — сеяный кэш ProdCalendar (2026-09-08, вторник).
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
# субботы сентября 2026: 5, 12, 19, 26 (первая — для основных проверок)
SAT = 5
# рабочий день с записью «.» (четверг 10) и суббота с «.» (12)
DOT_WORKDAY = 10
DOT_SAT = 12
# пустой рабочий день (вторник 1) — «·» остаётся
EMPTY_WORKDAY = 1

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
  # «.» на РАБОЧЕМ дне — «·» остаётся (регресс Task 314 не допущен)
  {'id':3,'дата':'%04d-%02d-%02d' % (Y, M, DOT_WORKDAY),'таб_номер':'017','статус':'.','источник':'авто'},
  # «.» на СУББОТУ — точка НЕ показывается (Task 355)
  {'id':4,'дата':'%04d-%02d-%02d' % (Y, M, DOT_SAT),'таб_номер':'023','статус':'.','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':6,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'023','статус':'д','часы':7.2,'источник':'руч'}
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t355)')
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
    return { text: td.textContent.trim(), weekend: td.classList.contains('ws-weekend'),
             empty: td.classList.contains('ws-status-empty'), dot: td.classList.contains('ws-dot-code'),
             bg: cs.backgroundColor, bl: cs.borderLeftColor, blw: cs.borderLeftWidth };
})"""

# ячейка из ВТОРОЙ строки (дневной Петров 023 — для «.»-записи на субботу)
JS_CELL_ROW2 = """(function(day){
    var td = document.querySelector('#wsGridWrap table tbody tr:nth-child(2) td.ws-cell[data-day="' + day + '"]');
    if (!td) return null;
    return { text: td.textContent.trim(), dot: td.classList.contains('ws-dot-code'),
             weekend: td.classList.contains('ws-weekend') };
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
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t355-a', theme='dark')
    seed_pcal_js(page)
    page.reload()
    page.wait_for_timeout(2000)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # диагностика сида праздника (Task 355)
    dbg = page.evaluate("""(function(){
        var di = ProdCalendar.dayInfo(%d, %d, %d);
        var raw = localStorage.getItem('ws_pcal_year2_%d_42');
        return { diOff: di.off, diHol: di.holiday, src: di.source, hasData: di.hasData,
                 rawLen: raw ? raw.length : 0, rawHead: raw ? raw.slice(0, 60) : null };
    })()""" % (Y, M, HOLIDAY_DAY, Y))
    print('  [diag] pcal day %d: %s' % (HOLIDAY_DAY, json.dumps(dbg, ensure_ascii=False)))

    # --- точка в нерабочих днях ---
    # день 5 (сб) — первая строка (Иванов, смена №1): ячейка пустая
    sat = page.evaluate(JS_CELL + '(%d)' % SAT)
    check('C: суббота (пустая) — точки «·» НЕТ', sat['text'] == '' and '·' not in (sat['text'] or ''), sat)
    check('C2: суббота — классы ws-weekend + ws-status-empty', sat['weekend'] and sat['empty'], sat)
    hol = page.evaluate(JS_CELL + '(%d)' % HOLIDAY_DAY)
    check('D: праздник (вт 08) — точки НЕТ, ws-weekend', hol['text'] == '' and hol['weekend'], hol)
    # день 12 (сб) — ВТОРАЯ строка (Петров): запись «.» — точка не показывается
    satdot = page.evaluate(JS_CELL_ROW2 + '(%d)' % DOT_SAT)
    check('E: суббота с кодом «.» — точки НЕТ, ws-dot-code жив', satdot['text'] == '' and satdot['dot'], satdot)
    workdot = page.evaluate(JS_CELL + '(%d)' % DOT_WORKDAY)
    check('F: рабочий день с «.» — «·» ОСТАЛСЯ', workdot['text'] == '·' and workdot['dot'], workdot)
    workempty = page.evaluate(JS_CELL + '(%d)' % EMPTY_WORKDAY)
    check('G: пустой рабочий день — «·» остался (не ws-weekend)',
          workempty['text'] == '·' and not workempty['weekend'], workempty)

    # --- розовый пастельнее ---
    check('H: розовый выходных = #f8e2e9 (rgb 248,226,233)', sat['bg'] == 'rgb(248, 226, 233)', sat['bg'])
    check('H2: розовый праздника — тот же', hol['bg'] == 'rgb(248, 226, 233)', hol['bg'])

    # --- линии ярче ---
    # воскресенье (день 6): левая граница — ОБЫЧНАЯ тёмная (суббота слева
    # тоже нерабочая → нет красного boundary-left; правая — красная
    # boundary-right, стык с понедельником — проверяется отдельно в M)
    sun = page.evaluate(JS_CELL + '(%d)' % 6)
    check('I: тело: граница дня 30% чёрного (тёмная, Task 319)', sun['bl'] == 'rgba(0, 0, 0, 0.3)', sun['bl'])
    check('I2: тело: толщина 1px (тонкие)', sun['blw'] == '1px', sun['blw'])
    emp = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
        return getComputedStyle(td).borderLeftColor;
    })()""")
    check('J: ФИО-колонка — стале-синяя 55%', emp == 'rgba(105, 130, 160, 0.55)', emp)
    head = page.evaluate(JS_HEAD + '(%d)' % 12)
    check('K: шапка: вертикальная граница 1px стале-голубая 55%',
          head['blw'] == '1px' and head['bl'] == 'rgba(140, 158, 188, 0.55)', head)
    check('K2: шапка: ВЕРХНЕЙ рамки нет (высота не меняется)', head['bt'] == '0px', head)
    head8 = page.evaluate(JS_HEAD + '(%d)' % HOLIDAY_DAY)
    check('L: шапка: праздник ws-feast/ws-holiday живы', head8['feast'] and head8['holiday'], head8)
    red = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-boundary-after');
        return td ? getComputedStyle(td).borderRightColor : null;
    })()""")
    check('M: красный стык Task 255 НЕ перекрашен (#cc6e73)', red == 'rgb(204, 110, 115)', red)
    stripe = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
        return getComputedStyle(td, '::after').backgroundColor;
    })()""")
    check('N: полоса ФИО ::after 2px #4a8fc7 жива (Task 333)', stripe == 'rgb(74, 143, 199)', stripe)
    grp = page.evaluate("""(function(){
        var tr = document.querySelector('#wsGridWrap table tbody tr.ws-group-first td');
        return tr ? getComputedStyle(tr).borderTopWidth + '/' + getComputedStyle(tr).borderTopColor : null;
    })()""")
    check('O: разделитель групп 2px #4a8fc7 жив (Task 259)', grp == '2px/rgb(74, 143, 199)', grp)
    page.screenshot(path='task355-proof-dark.png')
    check('P: 0 JS-ошибок (тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: десктоп 1280, светлая =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t355-b', theme='light')
    seed_pcal_js(page2)
    page2.reload()
    page2.wait_for_timeout(2000)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    sat2 = page2.evaluate(JS_CELL + '(%d)' % SAT)
    check('Q: светлая: суббота пустая — точки НЕТ, розовый #f8e2e9',
          sat2['text'] == '' and sat2['bg'] == 'rgb(248, 226, 233)', sat2)
    # воскресенье: левая граница обычная (суббота слева — тоже выходной)
    sun2 = page2.evaluate(JS_CELL + '(%d)' % 6)
    check('R: светлая: границы дней 30% чёрного, 1px',
          sun2['bl'] == 'rgba(0, 0, 0, 0.3)' and sun2['blw'] == '1px', sun2)
    head2 = page2.evaluate(JS_HEAD + '(%d)' % 12)
    check('S: светлая: шапка — вертикали 1px 30% чёрного, верха нет',
          head2['blw'] == '1px' and head2['bl'] == 'rgba(0, 0, 0, 0.3)' and head2['bt'] == '0px', head2)
    hol2 = page2.evaluate(JS_CELL + '(%d)' % HOLIDAY_DAY)
    check('T: светлая: праздник — точек нет, розовый', hol2['text'] == '' and hol2['bg'] == 'rgb(248, 226, 233)', hol2)
    workdot2 = page2.evaluate(JS_CELL + '(%d)' % DOT_WORKDAY)
    check('U: светлая: «.» на рабочем дне — «·» остался', workdot2['text'] == '·', workdot2)
    red2 = page2.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-cell.ws-boundary-after');
        return td ? getComputedStyle(td).borderRightColor : null;
    })()""")
    check('V: светлая: красный стык жив (#cc6e73)', red2 == 'rgb(204, 110, 115)', red2)
    page2.screenshot(path='task355-proof-light.png')
    check('W: 0 JS-ошибок (светлая)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 390, тёмная =================
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':390,'height':760}, 'bc-t355-c', theme='dark')
    seed_pcal_js(page3)
    page3.reload()
    page3.wait_for_timeout(2000)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    sat3 = page3.evaluate(JS_CELL + '(%d)' % SAT)
    check('X: мобайл: суббота — точки НЕТ, розовый', sat3['text'] == '' and sat3['bg'] == 'rgb(248, 226, 233)', sat3)
    page3.screenshot(path='task355-proof-mobile.png')
    check('Y: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
