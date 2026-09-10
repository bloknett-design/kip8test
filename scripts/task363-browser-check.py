#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 363: browser-check — заявка пользователя (шахматка табеля):
# «В шахматке табеля фон выходных дней сделай таким же как в пустых
# ячейках. А на ячейках выходных дней сделай толстые красные
# разделительные линии вокруг по краям группы этих ячеек (не каждую
# ячейку), включая ячейки с датами. А нерабочие праздничные дни
# оставь светлым розовым фоном, только добавь такой же фон и на их
# ячейки с датами».
# Контексты:
#   1. десктоп 1280 тёмная, Админ (edit): сетка с Сб/Вс (календарь
#      заблокирован — фолбэк выходных по дням недели): фон пустой
#      ячейки выходного == фон пустой ячейки рабочего дня (rgb равны);
#      рамка-группа: th/td первого столбца группы — border-left
#      3px rgb(229,57,53), последнего — border-right 3px, верх —
#      inset-тень 3px на th (border-top шапки 0), низ — border-bottom
#      3px на последней строке; ВНУТРЕННЯЯ грань Сб|Вс — тонкая 1px
#      (не каждую ячейку); статусная ячейка на выходном сохраняет
#      inline-цвет; прежнего пыльно-красного #cc6e73 нет. Затем
#      ProdCalendar.dayInfo подменяется (праздник в середине месяца)
#      + _renderGrid(): th праздника — розовый rgb(248,226,233) и
#      такой же фон пустой ячейки, БЕЗ рамки группы; соседние группы
#      выходных живы. Скриншот-пруф сетки.
#   2. мобайл 375 touch — классы рамки и праздника живы (computed).
# + 0 JS-ошибок.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8960
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DAYS = (datetime.date(Y, M + 1, 1) - datetime.timedelta(days=1)).day

# выходные по дням недели (фолбэк без производственного календаря)
WEEKENDS = [d for d in range(1, DAYS + 1)
            if datetime.date(Y, M, d).weekday() >= 5]
SAT1, SUN1 = WEEKENDS[0], WEEKENDS[0] + 1
WORK1 = SAT1 - 1 if SAT1 - 1 >= 1 else SAT1 + 2      # рабочий день перед группой
WORK_EMPTY = SUN1 + 1                                 # пустой рабочий день (без записей)
# праздник: первый будний день 12..18 (не Сб/Вс)
FEAST = next(d for d in range(12, 19)
             if datetime.date(Y, M, d).weekday() < 5)

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-01' % (Y, M if M > 1 else 12),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-07' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# записи: рабочие дни у обоих; у 017 на субботу — «д» (inline-фон);
# ПРАЗДНИК (FEAST) пуст у обоих — розовый виден
def entries_default():
    es = []
    es.append({'id':1,'дата':'%04d-%02d-%02d' % (Y, M, WORK1),'таб_номер':'017','статус':'Д','источник':'авто'})
    es.append({'id':2,'дата':'%04d-%02d-%02d' % (Y, M, WORK1),'таб_номер':'023','статус':'Д8','источник':'авто'})
    es.append({'id':3,'дата':'%04d-%02d-%02d' % (Y, M, SAT1),'таб_номер':'017','статус':'д','источник':'авто'})
    return es

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
        return {'ok':True,'data':{'trainings':[]}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok':True,'data':{'entries':entries_default()}}
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
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t363)')
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

RED = 'rgb(229, 57, 53)'      # #e53935
PINK = 'rgb(248, 226, 233)'   # #f8e2e9
OLD_RED = 'rgb(204, 110, 115)'  # #cc6e73 (Task 255, удалён)
EMPTY = 'rgb(238, 240, 242)'  # #eef0f2 (Task 319: обе темы несут светлые цвета)

# геометрия/стили рамки по дню (ячейка строки с таб_номером)
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

# подмена календаря: праздник FEAST + обычные Сб/Вс; перерисовка сетки
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

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t363-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: сетка открыта', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # --- фон выходного == фон пустой ячейки (заявка 1) ---
    sat = page.evaluate(js_cell('023', SAT1))
    work = page.evaluate(js_cell('023', WORK_EMPTY))
    check('C: пустая ячейка выходного — фон КАК у пустой ячейки рабочего',
          sat and work and sat['bg'] == work['bg'] == EMPTY, (sat or {}).get('bg'))
    check('D: розового фона у выходного НЕТ', sat and sat['bg'] != PINK, (sat or {}).get('bg'))

    # --- рамка-группа (заявка 2) ---
    check('E: суббота — ws-wgrp + ws-wgrp-first (th и td)',
          sat and 'ws-wgrp-first' in sat['tdCls'] and 'ws-wgrp-first' in (sat['thCls'] or ''),
          (sat or {}).get('tdCls'))
    check('F: бока группы: td сб — border-left 3px красный',
          sat and sat['blW'] == '3px' and sat['blC'] == RED, sat and (sat['blW'], sat['blC']))
    check('G: бока группы: th сб — border-left 3px красный',
          sat and sat['thBLW'] == '3px' and sat['thBLC'] == RED, sat and (sat['thBLW'], sat['thBLC']))
    sun = page.evaluate(js_cell('023', SUN1))
    check('H: воскресенье — ws-wgrp-last, border-right 3px',
          sun and 'ws-wgrp-last' in sun['tdCls'] and sun['brW'] == '3px' and sun['brC'] == RED,
          (sun or {}).get('brW'))
    check('I: ВНУТРЕННЯЯ грань сб|вс — тонкая 1px (не каждую ячейку)',
          sun and sun['blW'] == '1px', sun and (sun['blW'],))
    check('J: верх группы — inset-тень 3px на th, border-top шапки 0',
          sat and 'inset' in (sat['thShadow'] or '') and RED in (sat['thShadow'] or '') and sat['thBT'] == '0px',
          sat and (sat['thShadow'], sat['thBT']))
    # низ рамки — последняя строка
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
    check('K: низ группы — border-bottom 3px на последней строке, рабочий — 1px',
          last and last['w'] == '3px' and last['c'] == RED and last['workW'] == '1px', last)
    check('L: рабочий день у группы — БЕЗ своей красной границы (3px бьёт 1px)',
          work and work['brC'] != OLD_RED and work['blC'] != OLD_RED, work and (work['blC'], work['brC']))

    # --- статусная ячейка на выходном: inline-фон сохранён ---
    sat017 = page.evaluate(js_cell('017', SAT1))
    check('M: статус «д» на выходном — inline-фон справочника (#FFD54F)',
          sat017 and sat017['bg'] == 'rgb(255, 213, 79)', (sat017 or {}).get('bg'))

    # --- праздник: подмена календаря + перерисовка (заявка 3) ---
    page.evaluate(js_inject_feast(FEAST))
    page.wait_for_timeout(300)
    feast = page.evaluate(js_cell('023', FEAST))
    check('N: праздник — ws-feast, БЕЗ рамки группы',
          feast and 'ws-feast' in feast['tdCls'] and 'ws-feast' in (feast['thCls'] or '') and
          'ws-wgrp' not in feast['tdCls'], (feast or {}).get('tdCls'))
    check('O: пустая ячейка праздника — розовый фон #f8e2e9',
          feast and feast['bg'] == PINK, (feast or {}).get('bg'))
    check('P: ЯЧЕЙКА ДАТЫ праздника — ТА ЖЕ розовая заливка (заявка)',
          feast and feast['thBg'] == PINK, (feast or {}).get('thBg'))
    check('Q: соседние группы выходных живы (после перерисовки)',
          feast and page.evaluate(js_cell('023', SAT1))['blW'] == '3px')

    page.screenshot(path='scripts/task363-proof-grid.png')
    check('R: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, тёмная =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':760}, 'bc-t363-b', theme='dark')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.evaluate(js_inject_feast(FEAST))
    page2.wait_for_timeout(300)
    m = page2.evaluate(js_cell('023', SAT1))
    mf = page2.evaluate(js_cell('023', FEAST))
    check('S: мобайл: рамка группы жива (3px красный)',
          m and m['blW'] == '3px' and m['blC'] == RED, m and (m['blW'], m['blC']))
    check('T: мобайл: праздник розовый + дата розовая, без рамки',
          mf and mf['bg'] == PINK and mf['thBg'] == PINK and 'ws-wgrp' not in mf['tdCls'],
          mf and (mf['bg'], mf['thBg']))
    check('U: мобайл: 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
