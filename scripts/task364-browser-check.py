#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 364: browser-check — заявка пользователя: «Красные линии
# вокруг ГРУППЫ ячеек выходных сделай 2px и по меньше яркости.
# Коды под графиком на печати размести в столбик справа от
# столбика мероприятий».
# Контексты:
#   1. десктоп 1280 тёмная, Админ (edit): СЕТКА — рамка-группа
#      выходных 2px #e57373 (бока th/td, верх inset-тень, низ),
#      внутренняя грань Сб|Вс 1px, фон выходного == пустой ячейке;
#      праздник (подмена ProdCalendar) — розовый + дата, БЕЗ рамки.
#      ПЕЧАТЬ (полный вид, стаб window.print): в листе обёртка
#      wsp-bottom, мероприятия и коды — ДВА СТОЛБИКА одного ряда;
#      в print-медиа: display:flex/row, коды ПРАВЕЕ мероприятий
#      (rect), ширина кодов ≤ 44% ряда, сноска ПОД обёрткой на всю
#      ширину; регресс 362 — «ПЗ — Проверка знаний» в перечне.
#      Скриншот-пруфы сетки и печати.
#   2. мобайл 375 touch — рамка 2px жива, печать строится,
#      wsp-bottom в листе.
# + 0 JS-ошибок. Порт 8961.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8961
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DAYS = (datetime.date(Y, M + 1, 1) - datetime.timedelta(days=1)).day

WEEKENDS = [d for d in range(1, DAYS + 1)
            if datetime.date(Y, M, d).weekday() >= 5]
SAT1, SUN1 = WEEKENDS[0], WEEKENDS[0] + 1
WORK1 = SAT1 - 1 if SAT1 - 1 >= 1 else SAT1 + 2
WORK_EMPTY = SUN1 + 1
FEAST = next(d for d in range(12, 19)
             if datetime.date(Y, M, d).weekday() < 5)

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний','color':'#FFCDD2'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-01' % (Y, M if M > 1 else 12),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-07' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-%02d' % (Y, M, WORK1),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-%02d' % (Y, M, WORK1),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-%02d' % (Y, M, SAT1),'таб_номер':'017','статус':'д','источник':'авто'},
  {'id':4,'дата':'%04d-%02d-20' % (Y, M),'таб_номер':'023','статус':'ОТ','источник':'авто'}
]
def trainings_default():
    return [
      {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по охране труда',
       'дата_начала':'%04d-%02d-07' % (Y, M),'дата_окончания':'','дата_проведения':''},
      {'id':2,'таб_номер':'023','тип':'обучение','тема':'Обучение по новому оборудованию',
       'дата_начала':'%04d-%02d-02' % (Y, M),'дата_окончания':'','дата_проведения':''},
      {'id':3,'таб_номер':'023','тип':'проверка_знаний','тема':'Проверка знаний промбезопасности',
       'дата_начала':'%04d-%02d-15' % (Y, M),'дата_окончания':'%04d-%02d-16' % (Y, M),'дата_проведения':''}
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
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':trainings_default()}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok':True,'data':{'entries':ENTRIES}}
        return {'ok':True,'data':{'entries':[]}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def setup_ctx(browser, viewport, token, theme=None, saved_view=None):
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t364)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    if saved_view:
        page.evaluate("localStorage.setItem('kip8_ws_view_v1','%s')" % saved_view)
    else:
        page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

RED = 'rgb(229, 115, 115)'    # #e57373 (Task 364: менее яркая)
OLD_BRIGHT = 'rgb(229, 57, 53)'  # #e53935 (Task 363, заменена в рамке)
PINK = 'rgb(248, 226, 233)'   # #f8e2e9
EMPTY = 'rgb(238, 240, 242)'  # #eef0f2

def js_cell(tab, day):
    return """(function(){
    var emp = document.querySelector('#wsGridWrap td.ws-emp-col[data-tab="%s"]');
    var row = emp ? emp.closest('tr') : null;
    var td = row ? row.querySelector('td[data-day="%d"]') : null;
    if (!td) return null;
    var cs = getComputedStyle(td);
    var th = document.querySelector('#wsGridWrap th[data-day="%d"]');
    var thcs = th ? getComputedStyle(th) : null;
    return {
      tdCls: td.className,
      bg: cs.backgroundColor,
      blW: cs.borderLeftWidth, blC: cs.borderLeftColor,
      brW: cs.borderRightWidth, brC: cs.borderRightColor,
      bbW: cs.borderBottomWidth, bbC: cs.borderBottomColor,
      thCls: th ? th.className : null,
      thBg: thcs ? thcs.backgroundColor : null,
      thBLW: thcs ? thcs.borderLeftWidth : null,
      thBLC: thcs ? thcs.borderLeftColor : null,
      thBT: thcs ? thcs.borderTopWidth : null,
      thShadow: thcs ? thcs.boxShadow : null
    };
})""" % (tab, day, day)

def js_inject_feast(day):
    return """(function(){
    var FEAST = %d;
    if (window.ProdCalendar && window.ProdCalendar.dayInfo) {
        window.ProdCalendar.dayInfo = function(y, m, d) {
            var dw = new Date(y, m - 1, d).getDay();
            var hol = (d === FEAST);
            return { off: dw === 0 || dw === 6 || hol, holiday: hol, short: false };
        };
    }
    if (window.WorkSchedule && window.WorkSchedule._renderGrid) {
        window.WorkSchedule._renderGrid();
    }
    return true;
})""" % day

STUB_PRINT = "() => { window.print = function(){ window.__printCalled = (window.__printCalled||0)+1; }; }"

# раскладка нижнего ряда печатного листа (print-медиа)
JS_BOTTOM_LAYOUT = """(function(){
    var s = document.getElementById('wsPrintSheet');
    if (!s) return null;
    var bottom = s.querySelector('.wsp-bottom');
    var mev = s.querySelector('.wsp-bottom .wsp-mev');
    var legend = s.querySelector('.wsp-bottom .wsp-legend');
    var foot = s.querySelector('.wsp-foot');
    if (!bottom || !mev || !legend || !foot) return null;
    var cb = getComputedStyle(bottom), cm = getComputedStyle(mev), cl = getComputedStyle(legend);
    var bm = bottom.getBoundingClientRect(), mm = mev.getBoundingClientRect(),
        lm = legend.getBoundingClientRect(), fm = foot.getBoundingClientRect();
    var lgs = legend.querySelectorAll('.wsp-lg');
    var lgTexts = [];
    for (var i = 0; i < lgs.length; i++) lgTexts.push(lgs[i].textContent);
    var mevs = mev.querySelectorAll('.wsp-mev-item');
    return {
      display: cb.display, dir: cb.flexDirection, gap: cb.columnGap,
      mevFlex: cm.flex, legendFlex: cl.flex, legendMax: cl.maxWidth,
      mevTop: mm.top, legendTop: lm.top,
      legendLeft: lm.left, mevRight: mm.right,
      mevW: mm.width, legendW: lm.width, bottomW: bm.width,
      mevBottom: mm.bottom, legendBottom: lm.bottom, footTop: fm.top,
      footW: fm.width,
      lg: lgTexts, mevCount: mevs.length,
      footText: foot.textContent.slice(0, 60)
    };
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t364-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: сетка открыта', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # --- рамка-группа: 2px #e57373 (заявка 1) ---
    sat = page.evaluate(js_cell('023', SAT1))
    work = page.evaluate(js_cell('023', WORK_EMPTY))
    check('C: фон выходного == пустой рабочий (регресс 363)',
          sat and work and sat['bg'] == work['bg'] == EMPTY, (sat or {}).get('bg'))
    check('D: бока группы: td сб — border-left 2px #e57373',
          sat and sat['blW'] == '2px' and sat['blC'] == RED, sat and (sat['blW'], sat['blC']))
    check('E: бока группы: th сб — border-left 2px #e57373',
          sat and sat['thBLW'] == '2px' and sat['thBLC'] == RED, sat and (sat['thBLW'], sat['thBLC']))
    sun = page.evaluate(js_cell('023', SUN1))
    check('F: вс — ws-wgrp-last, border-right 2px #e57373',
          sun and 'ws-wgrp-last' in sun['tdCls'] and sun['brW'] == '2px' and sun['brC'] == RED,
          sun and (sun['brW'], sun['brC']))
    check('G: ВНУТРЕННЯЯ грань сб|вс — тонкая 1px',
          sun and sun['blW'] == '1px', sun and (sun['blW'],))
    check('H: верх группы — inset-тень 2px #e57373, border-top шапки 0',
          sat and 'inset' in (sat['thShadow'] or '') and RED in (sat['thShadow'] or '') and
          OLD_BRIGHT not in (sat['thShadow'] or '') and sat['thBT'] == '0px',
          sat and (sat['thShadow'], sat['thBT']))
    last = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        var last = rows[rows.length - 1];
        var td = last.querySelector('td[data-day="%d"]');
        var tdWork = last.querySelector('td[data-day="%d"]');
        if (!td || !tdWork) return null;
        var cs = getComputedStyle(td), cw = getComputedStyle(tdWork);
        return { w: cs.borderBottomWidth, c: cs.borderBottomColor,
                 workW: cw.borderBottomWidth };
    })""" % (SAT1, WORK1))
    check('I: низ группы — 2px #e57373, рабочий — 1px',
          last and last['w'] == '2px' and last['c'] == RED and last['workW'] == '1px', last)
    sat017 = page.evaluate(js_cell('017', SAT1))
    check('J: статус «д» на выходном — inline-фон (регресс)',
          sat017 and sat017['bg'] == 'rgb(255, 213, 79)', (sat017 or {}).get('bg'))

    # --- праздник: подмена календаря (регресс 363) ---
    page.evaluate(js_inject_feast(FEAST))
    page.wait_for_timeout(300)
    feast = page.evaluate(js_cell('023', FEAST))
    check('K: праздник — ws-feast, БЕЗ рамки, розовый + дата розовая',
          feast and 'ws-feast' in feast['tdCls'] and 'ws-wgrp' not in feast['tdCls'] and
          feast['bg'] == PINK and feast['thBg'] == PINK, feast and (feast['bg'], feast['thBg']))
    page.screenshot(path='scripts/task364-proof-grid.png')

    # --- ПЕЧАТЬ: коды СПРАВА от мероприятий (заявка 2) ---
    page.evaluate(STUB_PRINT)
    page.click('#wsPrintBtn')
    page.wait_for_timeout(400)
    check('L: печать вызвана, лист построен',
          page.evaluate("(window.__printCalled||0) === 1 && !!document.querySelector('#wsPrintSheet .wsp-bottom')"))
    page.emulate_media(media='print')
    lay = page.evaluate(JS_BOTTOM_LAYOUT)
    check('M: wsp-bottom — display:flex, направление row',
          lay and lay['display'] == 'flex' and lay['dir'] == 'row', lay and (lay['display'], lay['dir']))
    check('N: коды ПРАВЕЕ мероприятий (столбик справа)',
          lay and lay['legendLeft'] >= lay['mevRight'] - 1,
          lay and (lay['mevRight'], lay['legendLeft']))
    check('O: оба столбика от общего верха (один ряд)',
          lay and abs(lay['mevTop'] - lay['legendTop']) < 3,
          lay and (lay['mevTop'], lay['legendTop']))
    check('P: ширина кодов ≤ 44% ряда (без растяжения)',
          lay and lay['legendW'] <= lay['bottomW'] * 0.44 + 2 and lay['legendW'] > 0,
          lay and (lay['legendW'], lay['bottomW']))
    check('Q: мероприятия занимают остальную ширину ряда',
          lay and lay['mevW'] > lay['bottomW'] * 0.5, lay and (lay['mevW'], lay['bottomW']))
    check('R: сноска ПОД обёрткой, на всю ширину листа',
          lay and lay['footTop'] >= max(lay['mevBottom'], lay['legendBottom']) - 1 and
          lay['footW'] >= lay['bottomW'] - 2, lay and (lay['footTop'], lay['footW']))
    check('S: регресс 362 — «ПЗ — Проверка знаний» в перечне кодов',
          lay and any('ПЗ — Проверка знаний' in t for t in lay['lg']), lay and lay['lg'])
    check('T: регресс 360 — 3 мероприятия в левом столбике',
          lay and lay['mevCount'] == 3, lay and lay['mevCount'])
    page.screenshot(path='scripts/task364-proof-print.png', full_page=True)
    page.emulate_media(media='screen')
    check('U: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, тёмная =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':760}, 'bc-t364-b', theme='dark')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    m = page2.evaluate(js_cell('023', SAT1))
    check('V: мобайл: рамка группы 2px #e57373 жива',
          m and m['blW'] == '2px' and m['blC'] == RED, m and (m['blW'], m['blC']))
    page2.evaluate(STUB_PRINT)
    page2.click('#wsPrintBtn')
    page2.wait_for_timeout(400)
    page2.emulate_media(media='print')
    lay2 = page2.evaluate(JS_BOTTOM_LAYOUT)
    check('W: мобайл: печать — wsp-bottom, flex-ряд, коды правее',
          lay2 and lay2['display'] == 'flex' and lay2['legendLeft'] >= lay2['mevRight'] - 1, lay2)
    page2.emulate_media(media='screen')
    check('X: мобайл: 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
