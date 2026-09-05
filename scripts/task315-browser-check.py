# -*- coding: utf-8 -*-
# Task 315: browser-check «График работы» — заявка пользователя:
#   1) в баре над шахматкой — ВТОРОЕ окно с данными всех мероприятий
#      открытого месяца, МЕЖДУ кнопками и окном времени и праздников;
#      бар разделён на ТРИ РАВНЫЕ части (кнопки | мероприятия |
#      время и праздники); текст в окнах ПЕРЕНОСИТСЯ на строку ниже;
#   2) при вводе изменений (код в ячейке) помимо «Сохранить»
#      появляется «Отменить» (отмена ввода изменений);
#   3) «Сохранить» и «Отменить» — строкой 2 (под кнопками выбора
#      месяца и года), «Сформировать» — строкой 3 (ещё ниже).
# Проверки: три равные части (геометрия grid), окно мероприятий
# (заголовок+счётчик, строки: точка-цвет/диапазон дат/тема/ФИО,
# записи вне месяца не показаны, пересечение границы месяца),
# перенос текста (white-space: normal, высота многострочной записи),
# правка → строка 2 появляется (Сохранить (N) + Отменить), порядок
# строк 1/2/3 (геометрия), «Отменить» — kipConfirm(danger) → сброс
# правок + тост + строка скрыта, «Сохранить» — пакет на сервер,
# зритель (строки 2/3 скрыты, окно живо), мобильный 375px (бар
# колонкой), светлая тема окна. 0 JS-ошибок.
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404).
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8937
TODAY = datetime.date.today()
TODAY_ISO = TODAY.isoformat()
Y, M = TODAY.year, TODAY.month
FIRST_DAY = TODAY.replace(day=1)
LAST_PREV = FIRST_DAY - datetime.timedelta(days=1)   # конец прошлого месяца
CROSS_START = LAST_PREV - datetime.timedelta(days=1) # пересекает границу

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'}
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
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
# Мероприятия: однодневное, диапазон в месяце, ДЛИННАЯ тема (перенос),
# пересечение границы прошлого месяца, вне месяца (не показано)
DAY10 = '%04d-%02d-10' % (Y, M)
DAY12 = '%04d-%02d-12' % (Y, M)
DAY15 = '%04d-%02d-15' % (Y, M)
DAY20 = '%04d-%02d-20' % (Y, M)
NEXT5 = '%04d-%02d-05' % (Y + (1 if M == 12 else 0), (M % 12) + 1)
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Целевой инструктаж','дата_начала':DAY10,'дата_окончания':DAY10,'длительность_дней':1},
  {'id':102,'таб_номер':'023','тип':'обучение','тема':'Охрана труда','дата_начала':DAY12,'дата_окончания':DAY15,'длительность_дней':4},
  {'id':103,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по охране труда и промышленной безопасности на производственном объекте с аттестацией в комиссии предприятия и проверкой практических навыков','дата_начала':DAY20,'дата_окончания':DAY20,'длительность_днів':1,'длительность_дней':1},
  {'id':104,'таб_номер':'023','тип':'инструктаж','тема':'На стыке месяцев','дата_начала':CROSS_START.isoformat(),'дата_окончания':FIRST_DAY.isoformat(),'длительность_дней':3},
  {'id':105,'таб_номер':'017','тип':'обучение','тема':'Следующий месяц — НЕ показано','дата_начала':NEXT5,'дата_окончания':NEXT5,'длительность_дней':1}
]
VACATIONS = []

STATE = {'role': 'Админ'}
WRITE_COUNT = {'setManualEntry': 0, 'deleteEntry': 0}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        admin = STATE['role'] == 'Админ'
        perms = {'workschedule.view':True, 'workschedule.edit':admin,
                 'flowmeter.view':True, 'flowmeter.input':admin}
        if admin: perms['admin.panel'] = True
        return {'ok':True,'data':{'role':STATE['role'],'found':True,'permissions':perms}}
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
    if action == 'workSchedule.setManualEntry':
        WRITE_COUNT['setManualEntry'] += 1
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.deleteEntry':
        WRITE_COUNT['deleteEntry'] += 1
        return {'ok':True,'data':{'ok':True}}
    return {'ok':False,'error':'unknown action ' + str(action)}

def click_cell(page, iso, tab):
    page.evaluate("""(function(a){
        var iso = a[0], tab = a[1];
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'"+iso+"'") !== -1 && oc.indexOf("'"+tab+"'") !== -1) {
                var r = tds[i].getBoundingClientRect();
                window.__cellXY = [r.left + r.width/2, r.top + r.height/2];
                return;
            }
        }
        window.__cellXY = [600, 300];
    })""", [iso, tab])
    xy = page.evaluate("window.__cellXY")
    page.mouse.click(xy[0], xy[1])
    page.wait_for_timeout(600)

def select_popup_code(page, code):
    """выбрать код в попапе ячейки (строка с .ws-popup-code == code)"""
    return page.evaluate("""(function(code){
        var cp = document.getElementById('wsCellPopup');
        if (!cp) return false;
        var rows = cp.querySelectorAll('.ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent.trim() === code) { rows[i].click(); return true; }
        }
        return false;
    })""", code)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280px, Админ =================
    ctx = browser.new_context(viewport={'width':1280,'height':800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        body = None
        pd = request.post_data
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t315)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t315')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- ТРИ РАВНЫЕ ЧАСТИ ----------
    geo = page.evaluate("""(function(){
        var bar = document.querySelector('.ws-bar-row');
        var main = document.querySelector('.ws-toolbar-main');
        var ev = document.getElementById('wsEventsPanel');
        var cal = document.getElementById('wsCalPanel');
        if (!bar || !main || !ev || !cal) return null;
        var bs = getComputedStyle(bar);
        return { display: bs.display,
                 cols: bs.gridTemplateColumns,
                 main: main.offsetWidth, ev: ev.offsetWidth, cal: cal.offsetWidth,
                 mainTop: main.getBoundingClientRect().top,
                 evTop: ev.getBoundingClientRect().top,
                 calTop: cal.getBoundingClientRect().top,
                 calRight: cal.getBoundingClientRect().right,
                 evHidden: ev.hidden, calHidden: cal.hidden };
    })()""")
    check('C: строка 1 бара — grid', geo and geo['display'] == 'grid', geo)
    widths = sorted([geo['main'], geo['ev'], geo['cal']])
    check('C2: ТРИ РАВНЫЕ части (разброс ширин ≤ 8px)',
          geo and (widths[2] - widths[0]) <= 8, widths)
    ncols = len([c for c in (geo['cols'] or '').split(' ') if c.strip()])
    check('C3: grid-template-columns — три колонки', ncols == 3, geo['cols'])
    # окно мероприятий — МЕЖДУ кнопками и окном времени и праздников
    check('C4: порядок: кнопки → мероприятия → время/праздники',
          geo['mainTop'] <= geo['evTop'] and geo['evTop'] <= geo['calTop'] and
          geo and geo['main'] > 0 and geo['ev'] > 0 and geo['cal'] > 0)

    # ---------- ОКНО МЕРОПРИЯТИЙ ----------
    ev = page.evaluate("""(function(){
        var el = document.getElementById('wsEventsPanel');
        if (!el || el.hidden) return null;
        var cap = el.querySelector('.ws-ep-cap');
        var items = el.querySelectorAll('.ws-ep-item');
        var out = { cap: cap ? cap.textContent.trim() : '',
                    n: items.length, rows: [], longH: 0, shortH: 0 };
        for (var i=0;i<items.length;i++){
            var d = items[i].querySelector('.ws-ep-date');
            var t = items[i].querySelector('.ws-ep-text');
            var dot = items[i].querySelector('.ws-ep-dot');
            out.rows.push({ date: d ? d.textContent : '',
                            text: t ? t.textContent.trim() : '',
                            dotBg: dot ? (dot.getAttribute('style')||'') : '' });
            if (t && t.textContent.length > 80) out.longH = items[i].clientHeight;
            else if (out.shortH === 0) out.shortH = items[i].clientHeight;
        }
        var cs = getComputedStyle(el.querySelector('.ws-ep-item') || el);
        out.whiteSpace = cs.whiteSpace;
        var day = el.querySelector('.ws-cp-day');
        out.calDaySpace = day ? getComputedStyle(day).whiteSpace : '(нет чипов)';
        return out;
    })()""")
    check('D: окно мероприятий показано, заголовок с месяцем/годом',
          ev and ('Мероприятия ·' in ev['cap']) and (str(Y) in ev['cap']), ev and ev['cap'])
    # 4 записи месяца (вне месяца — не показано)
    check('D2: счётчик и строки = 4 (запись след. месяца НЕ показана)',
          ev and ev['n'] == 4 and ('· 4' in ev['cap']), (ev and ev['n'], ev and ev['cap']))
    dates = [r['date'] for r in (ev['rows'] if ev else [])]
    check('D3: диапазоны дат: «10.MM», «12–15.MM», «MM–1 пересечение»',
          any(d.startswith('10.') for d in dates) and
          any(d.startswith('12–15.') for d in dates) and
          any(d.endswith('.' + ('%02d' % M)) and '–' in d and not d.startswith(('10.','12–15.')) for d in dates),
          dates)
    check('D4: строки с темой и ФИО',
          ev and any('Целевой инструктаж' in r['text'] and 'Иванов' in r['text'] for r in ev['rows']) and
          any('Охрана труда' in r['text'] and 'Петров' in r['text'] for r in ev['rows']),
          ev and [r['text'][:40] for r in ev['rows']])
    check('D5: цвет точки — из «Коды_статусов» (#B3E5FC у И)',
          ev and any('#B3E5FC' in r['dotBg'] for r in ev['rows']),
          ev and [r['dotBg'] for r in ev['rows']][:2])

    # ---------- ПЕРЕНОС ТЕКСТА ----------
    check('E: строка мероприятия переносится (white-space: normal)',
          ev and ev['whiteSpace'] == 'normal', ev and ev['whiteSpace'])
    check('E2: длинная тема — высота в НЕСКОЛЬКО строк (> 1.5× короткой)',
          ev and ev['longH'] > ev['shortH'] * 1.5 and ev['longH'] >= 30,
          (ev and ev['shortH'], ev and ev['longH']))
    page.screenshot(path='scripts/task315-proof-desktop.png', full_page=False)

    # ---------- СТРОКИ 2/3: до правок ----------
    st0 = page.evaluate("""(function(){
        var act = document.getElementById('wsActionsRow');
        var tot = document.getElementById('wsTotalsRow');
        var s = document.getElementById('wsSaveBtn');
        var c = document.getElementById('wsCancelBtn');
        var g = document.getElementById('wsGenerateBtn');
        return { actHidden: act ? act.hidden : true,
                 totHidden: tot ? tot.hidden : true,
                 saveHidden: s ? s.hidden : true,
                 cancelHidden: c ? c.hidden : true,
                 gHidden: g ? g.hidden : true };
    })()""")
    check('F: ряды 2/3 ВСЕГДА на виду (Task 324/325); «Сформировать» — Админу, без правок Сохранить/Отменить скрыты',
          not st0['actHidden'] and not st0['totHidden'] and not st0['gHidden'] and
          st0['saveHidden'] and st0['cancelHidden'], st0)

    # ---------- ПРАВКА: строка 2 появляется ----------
    click_cell(page, TODAY_ISO, '017')
    ok_sel = select_popup_code(page, 'Н')
    page.wait_for_timeout(600)
    st1 = page.evaluate("""(function(){
        var act = document.getElementById('wsActionsRow');
        var tot = document.getElementById('wsTotalsRow');
        var s = document.getElementById('wsSaveBtn');
        var c = document.getElementById('wsCancelBtn');
        var g = document.getElementById('wsGenerateBtn');
        var cal = document.getElementById('wsCalPanel');
        var main = document.querySelector('.ws-toolbar-main');
        if (!act || !s || !c || !g || !tot || !cal || !main) return null;
        var ra = act.getBoundingClientRect(), rt = tot.getBoundingClientRect();
        var rg = g.getBoundingClientRect();
        var rm = main.getBoundingClientRect();
        return { actHidden: act.hidden, saveHidden: s.hidden, cancelHidden: c.hidden,
                 saveText: s.textContent.trim(), cancelText: c.textContent.trim(),
                 rowInCol: ra.top >= rm.top - 2 && ra.bottom <= rm.bottom + 2,
                 rowNotFullBar: ra.width <= rm.width + 1,
                 actBelowTot: ra.top >= rt.bottom - 2,
                 genBeforeSave: rg.left <= s.getBoundingClientRect().left,
                 saveVisible: s.offsetParent !== null, cancelVisible: c.offsetParent !== null };
    })()""")
    check('G: код выбран в попапе (Н)', ok_sel)
    check('G2: при правке появляются «Сохранить (1)» + «Отменить» (ряд 3 действий)',
          st1 and not st1['actHidden'] and not st1['saveHidden'] and not st1['cancelHidden'] and
          st1['saveText'] == 'Сохранить (1)' and st1['cancelText'] == 'Отменить' and
          st1['saveVisible'] and st1['cancelVisible'], st1)
    check('G3: ряд 3 — ВНУТРИ колонки кнопок (не полная ширина бара)',
          st1 and st1['rowInCol'] and st1['rowNotFullBar'], st1)
    check('G4: ряд 3 — ПОД рядом 2 итогов; «Сформировать» — первая в ряду (Task 325)',
          st1 and st1['actBelowTot'] and st1['genBeforeSave'], st1)
    page.screenshot(path='scripts/task315-proof-actions.png', full_page=False)

    # ---------- «Отменить»: kipConfirm → сброс ----------
    page.evaluate("""(function(){
        window.__toasts = [];
        var orig = KipToast.show;
        KipToast.show = function(m){ window.__toasts.push(String(m)); return orig.apply(this, arguments); };
        return true;
    })()""")
    page.click('#wsCancelBtn')
    page.wait_for_timeout(400)
    dlg = page.evaluate("""(function(){
        var d = document.querySelector('.kip-dialog');
        if (!d) return null;
        var ok = d.querySelector('.kip-dialog-ok');
        return { title: (d.querySelector('.kip-dialog-title')||{}).textContent || '',
                 msg: (d.querySelector('.kip-dialog-msg')||{}).textContent || '',
                 okText: ok ? ok.textContent.trim() : '',
                 danger: ok ? ok.className.indexOf('danger') !== -1 : false };
    })()""")
    check('H: «Отменить» — подтверждение kipConfirm (danger, «Отменить правки»)',
          dlg and dlg['title'] == 'Отмена изменений' and dlg['danger'] and
          dlg['okText'] == 'Отменить правки' and 'несохранённые правки' in dlg['msg'], dlg)
    page.click('.kip-dialog-ok')
    page.wait_for_timeout(800)
    st2 = page.evaluate("""(function(){
        var r2 = document.getElementById('wsActionsRow');
        var s = document.getElementById('wsSaveBtn');
        var c = document.getElementById('wsCancelBtn');
        // ячейка сегодня/017: серверная запись «Д» — правка отменена
        var cell = null;
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'""" + TODAY_ISO + """'") !== -1 && oc.indexOf("'017'") !== -1) { cell = tds[i]; break; }
        }
        return { r2hidden: r2 ? r2.hidden : true,
                 saveHidden: s ? s.hidden : true,
                 cancelHidden: c ? c.hidden : true,
                 pending: Object.keys(WorkSchedule._PENDING).length,
                 cellText: cell ? cell.textContent.trim() : '' };
    })()""")
    toasts = page.evaluate("window.__toasts || []")
    check('H2: после отмены — _PENDING пуст, кнопки скрыты (ряд 3 на виду)',
          st2['pending'] == 0 and not st2['r2hidden'] and st2['saveHidden'] and st2['cancelHidden'], st2)
    check('H3: тост «Изменения отменены (1)»',
          any('Изменения отменены (1)' in t for t in toasts), toasts[:3])
    check('H4: ячейка вернулась к серверной записи (Д)',
          st2['cellText'].strip().startswith('Д'), st2['cellText'])

    # ---------- «Сохранить»: прежний пакетный путь ----------
    click_cell(page, TODAY_ISO, '017')
    select_popup_code(page, 'Н')
    page.wait_for_timeout(600)
    page.click('#wsSaveBtn')
    page.wait_for_timeout(2500)
    st3 = page.evaluate("""(function(){
        var r2 = document.getElementById('wsActionsRow');
        return { r2hidden: r2 ? r2.hidden : true,
                 writes: %d };
    })()""" % WRITE_COUNT['setManualEntry'])
    toasts2 = page.evaluate("window.__toasts || []")
    check('I: «Сохранить» — пакет на сервер (setManualEntry), кнопки скрыты (ряд на виду)',
          st3['writes'] >= 1 and not st3['r2hidden'], st3)
    check('I2: тост «Сохранено записей: 1»',
          any('Сохранено записей: 1' in t for t in toasts2), toasts2[:3])

    # ---------- Светлая тема ----------
    page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(400)
    light = page.evaluate("""(function(){
        var el = document.getElementById('wsEventsPanel');
        var cal = document.getElementById('wsCalPanel');
        return { evBg: el ? getComputedStyle(el).backgroundColor : '',
                 calBg: cal ? getComputedStyle(cal).backgroundColor : '' };
    })()""")
    check('J: светлая тема — окно мероприятий #e9e7de (как календарь)',
          light['evBg'] == 'rgb(233, 231, 222)' and light['calBg'] == 'rgb(233, 231, 222)', light)
    page.screenshot(path='scripts/task315-proof-light.png', full_page=False)
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    check('J2: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: зритель (ИТР) =================
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    def handle2(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        resp = mock_response(action, None)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx2.route('**/exec?**', handle2)
    ctx2.route('**script.google.com/**', handle2)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t315-viewer')")
    page2.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    viewer = page2.evaluate("""(function(){
        var r2 = document.getElementById('wsActionsRow');
        var r3 = document.getElementById('wsGenerateRow');
        var g = document.getElementById('wsGenerateBtn');
        var ev = document.getElementById('wsEventsPanel');
        return { r2hidden: r2 ? r2.hidden : true,
                 r3hidden: r3 ? r3.hidden : true,
                 gHidden: g ? g.hidden : true,
                 grid: !!document.querySelector('#wsGridWrap table'),
                 evShown: ev ? (!ev.hidden && ev.querySelectorAll('.ws-ep-item').length > 0) : false,
                 evCap: ev ? (ev.querySelector('.ws-ep-cap')||{}).textContent : '' };
    })()""")
    check('K: зритель — «Сформировать» скрыта (ряды на виду: итоги видны всем), сетка жива',
          (not viewer['r2hidden']) and viewer['gHidden'] and viewer['grid'], viewer)
    check('K2: зритель видит окно мероприятий месяца',
          viewer['evShown'] and 'Мероприятия ·' in viewer['evCap'], viewer['evCap'])
    check('K3: JS-ошибок нет (зритель)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375px =================
    STATE['role'] = 'Админ'
    ctx3 = browser.new_context(viewport={'width':375,'height':812})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    def handle3(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        resp = mock_response(action, None)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx3.route('**/exec?**', handle3)
    ctx3.route('**script.google.com/**', handle3)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.evaluate("localStorage.setItem('kip8_session_token','browser-check-t315-mobile')")
    page3.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page3.reload()
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    mob = page3.evaluate("""(function(){
        var bar = document.querySelector('.ws-bar-row');
        var main = document.querySelector('.ws-toolbar-main');
        var ev = document.getElementById('wsEventsPanel');
        var act = document.getElementById('wsActionsRow');
        if (!bar || !main || !ev || !act) return null;
        var bs = getComputedStyle(bar);
        var rm = main.getBoundingClientRect(), re = ev.getBoundingClientRect(), rg = act.getBoundingClientRect();
        return { display: bs.display,
                 evBelowMain: re.top > rm.bottom - 2,
                 evWidth: ev.offsetWidth, barWidth: bar.offsetWidth,
                 evInViewport: ev.offsetParent !== null,
                 genInViewport: act.offsetParent !== null,
                 genAboveEv: rg.bottom <= re.top + 2 };
    })()""")
    check('L: мобильный — бар КОЛОНКОЙ (окно мероприятий под кнопками)',
          mob and mob['display'] == 'flex' and mob['evBelowMain'], mob)
    check('L2: окно мероприятий — во всю ширину бара, в кадре',
          mob and abs(mob['evWidth'] - mob['barWidth']) <= 4 and mob['evInViewport'],
          (mob and mob['evWidth'], mob and mob['barWidth']))
    check('L3: ряд 3 действий — в кнопочном блоке НАД окнами, в кадре',
          mob and mob['genAboveEv'] and mob['genInViewport'], mob)
    page3.screenshot(path='scripts/task315-proof-mobile.png', full_page=False)
    check('L4: JS-ошибок нет (мобильный)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

fails = [r for r in results if not r[1]]
print('')
print('=' * 60)
print('ИТОГ: %d passed, %d failed, %d total' % (len(results) - len(fails), len(fails), len(results)))
if fails:
    print('ОШИБКИ:')
    for name, _, extra in fails:
        print('  FAIL: ' + name + ' | ' + str(extra))
    sys.exit(1)
