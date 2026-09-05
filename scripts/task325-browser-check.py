# -*- coding: utf-8 -*-
# Task 325: browser-check «Итоги учёта — ряды кнопок 2/3, шапка без ✕,
# колонки сотрудников по самому широкому тексту, вертикальные линии
# ячеек»: кнопки «Итоги учёта»/«Месяц»/«Год» — ВТОРОЙ строкой тулбара,
# «Сформировать»/«Сохранить (N)»/«Отменить» — ТРЕТЬЕЙ ПОД ними;
# ✕ из шапки шторки УДАЛЁН (закрытие — только кнопкой «Итоги учёта»,
# пустая шапка прячется); ширина колонки «Сотрудник» — ПО ТЕКСТУ В
# САМОМ ШИРОКОМ (шахматка: JS-замер --ws-emp-w; таблица итогов: без
# капа 220/150px); в таблице итогов — ТОНКИЕ ВЕРТИКАЛЬНЫЕ ЛИНИИ
# разделения ячеек (border-right, последняя колонка без линии).
# Проверки: 3 контекста (десктоп-Админ 1280 тёмная, светлая 1100,
# мобильный 375 touch): три ряда тулбара (порядок/высоты 29,67px/
# 95px), ✕ нет + пустая шапка скрыта (месяц) / показана (год —
# «Обновить»), открытие/закрытие кнопкой, колонка сотрудников без
# эллипсиса (шахматка и итоги), вертикальные линии вычисленным
# стилем, выравнивание строк итогов по строкам сетки, живые правки,
# 0 JS-ошибок, скриншоты.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8945
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час, 7:30–19:30)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час (7:30–16:30)','color':'#FFF9C4'},
  {'code':'Д7,2','name':'День 7,2-час (пятн./предпраздн.)','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час, 19:30–7:30)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'н','name':'Ночь в вых./праздник','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск основной','color':'#ECEFF1'},
  {'code':'Б','name':'Больничный','color':'#F8BBD0'},
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'}
]
# 017 — сменный; 023 — дневной; 099 — АРХИВНЫЙ (год)
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-01' % (Y, M),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-04' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'099','ФИО':'Сидоров Сидор Сидорович','тип':'сменный','смена':3,'шаблон_ротации':1,'старт_цикла':'%04d-02-01' % Y,'дата_приёма':'2020-05-04','дата_увольнения':'%04d-06-30' % Y,'в_архиве':1,'должность':'Слесарь КИПиА','комментарий':'уволен'}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
def d(day):
    return '%04d-%02d-%02d' % (Y, M, day)

# 017: Д,Д,Н,Д7,2,ОТ,ОТ,Б,«.»,д → явки 4, часы 43,2, переработка 12
# 023: Д8,Д8,д(7,2) → явки 2, часы 16, переработка 7,2
STATE = {'role':'Админ', 'entriesCalls':0, 'manualPayloads':[],
         'entries': [
  {'дата':d(1),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'дата':d(2),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'дата':d(3),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'дата':d(4),'таб_номер':'017','статус':'Д7,2','источник':'авто'},
  {'дата':d(5),'таб_номер':'017','статус':'ОТ','источник':'авто'},
  {'дата':d(6),'таб_номер':'017','статус':'ОТ','источник':'авто'},
  {'дата':d(7),'таб_номер':'017','статус':'Б','источник':'авто'},
  {'дата':d(8),'таб_номер':'017','статус':'.','источник':'авто'},
  {'дата':d(9),'таб_номер':'017','статус':'д','источник':'руч'},
  {'дата':d(1),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'дата':d(2),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'дата':d(5),'таб_номер':'023','статус':'д','источник':'руч','часы':7.2}
]}
TRAININGS = []
VACATIONS = []

def entries_for(year, month):
    if month == M and year == Y:
        return [dict(e) for e in STATE['entries']]
    if month == 1:
        return [{'дата':'%04d-01-05' % year,'таб_номер':'017','статус':'Д','источник':'авто'}]
    if month == 5:
        return [{'дата':'%04d-05-12' % year,'таб_номер':'099','статус':'Н','источник':'авто'}]
    return []

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def mock_response(action, body):
    body = body or {}
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
        if body.get('includeArchived'):
            return {'ok':True,'data':{'employees':EMPLOYEES}}
        return {'ok':True,'data':{'employees':[e for e in EMPLOYEES if not e['в_архиве']]}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        STATE['entriesCalls'] += 1
        year = int(body.get('year', Y))
        month = int(body.get('month', M))
        return {'ok':True,'data':{'entries':entries_for(year, month)}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.generateMonth':
        return {'ok':True,'data':{'generated':5,'updated':2,'removed':1,
                                   'vacationDays':3,'removedShift':0,'warnings':[]}}
    if action == 'workSchedule.setManualEntry':
        STATE['manualPayloads'].append(body)
        date = body.get('date')
        tab = body.get('таб_номер')
        for e in STATE['entries']:
            if e['дата'] == date and e['таб_номер'] == tab:
                e['статус'] = body.get('статус')
                e['источник'] = 'руч'
                if 'часы' in body:
                    e['часы'] = body.get('часы')
                return {'ok':True,'data':{'ok':True}}
        rec = {'дата':date,'таб_номер':tab,'статус':body.get('статус'),
               'источник':'руч'}
        if 'часы' in body:
            rec['часы'] = body.get('часы')
        STATE['entries'].append(rec)
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.deleteEntry':
        return {'ok':True,'data':{'ok':True}}
    return {'ok':False,'error':'unknown action ' + str(action)}

def setup_routes(ctx):
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
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t325)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

# ================= Проверки Task 325 =================
def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t325')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, Админ, ТЁМНАЯ =================
    ctx = browser.new_context(viewport={'width':1280,'height':800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    setup_routes(ctx)
    open_grid(page, theme='dark')
    check('A: страница загрузилась, сетка отрисована (2 активных)',
          page.evaluate("!!document.querySelector('#wsGridWrap table')") and
          page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length") == 2)

    # ---------- ТРИ РЯДА тулбара (заявка Task 325) ----------
    rows = page.evaluate("""(function(){
        var sel = document.getElementById('wsSelectsRow').getBoundingClientRect();
        var tot = document.getElementById('wsTotalsRow').getBoundingClientRect();
        var act = document.getElementById('wsActionsRow').getBoundingClientRect();
        var main = document.querySelector('.ws-toolbar-main').getBoundingClientRect();
        var totOrder = [];
        var kids = document.getElementById('wsTotalsRow').children;
        for (var i=0;i<kids.length;i++) totOrder.push(kids[i].id);
        var actOrder = [];
        var kids2 = document.getElementById('wsActionsRow').children;
        for (var j=0;j<kids2.length;j++) actOrder.push(kids2[j].id);
        var btn = document.getElementById('wsTotalsBtn').getBoundingClientRect();
        var gen = document.getElementById('wsGenerateBtn');
        return {selH: sel.height, totH: tot.height, actH: act.height,
                mainH: main.height,
                totTop: tot.y, actTop: act.y, selBottom: sel.y + sel.height,
                totOrder: totOrder, actOrder: actOrder,
                genHidden: gen.hidden, btnW: btn.width};
    })()""")
    check('B: ТРИ ряда тулбара: селекты → Итоги учёта (ряд 2) → действия (ряд 3)',
          rows['totOrder'] == ['wsTotalsBtn','wsTtTabMonth','wsTtTabYear'] and
          rows['actOrder'] == ['wsGenerateBtn','wsSaveBtn','wsCancelBtn'] and
          abs(rows['totTop'] - rows['selBottom']) < 4 and
          abs(rows['actTop'] - (rows['totTop'] + rows['totH'])) < 4, rows)
    check('C: высоты рядов ~29,7px (95px/3), колонка — 95px',
          abs(rows['totH'] - 29.67) < 1.5 and abs(rows['actH'] - 29.67) < 1.5 and
          abs(rows['mainH'] - 95) < 1.5, rows)
    check('D: разделителя .ws-tb-sep НЕТ, «Сформировать» видна админу',
          rows['genHidden'] == False and
          page.evaluate("document.querySelector('.ws-tb-sep') === null"))

    # ---------- КОЛОНКА СОТРУДНИКОВ ШАХМАТКИ — ПО САМОМУ ШИРОКОМУ ----------
    emp = page.evaluate("""(function(){
        var page = document.getElementById('page-work-schedule');
        var cssVar = page.style.getPropertyValue('--ws-emp-w');
        var th = document.querySelector('.ws-grid thead th.ws-emp-col');
        var thW = th.getBoundingClientRect().width;
        var clipped = 0;
        var names = document.querySelectorAll('.ws-grid tbody .ws-emp-name');
        for (var i=0;i<names.length;i++) {
            if (names[i].scrollWidth > names[i].clientWidth + 1) clipped++;
        }
        var range = document.createRange();
        var maxW = 0;
        for (var j=0;j<names.length;j++) {
            range.selectNodeContents(names[j]);
            var w = range.getBoundingClientRect().width;
            if (w > maxW) maxW = w;
        }
        var cs = getComputedStyle(th);
        var pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
        return {cssVar: cssVar, thW: thW, clipped: clipped,
                maxName: maxW, pad: pad};
    })()""")
    check('E: --ws-emp-w ЗАМЕРЕНА, колонка = самый широкий текст + паддинги',
          emp['cssVar'] != '' and
          abs(emp['thW'] - (emp['maxName'] + emp['pad'] + 2)) < 3, emp)
    check('F: ФИО НЕ обрезаются эллипсисом (колонка по тексту)',
          emp['clipped'] == 0, emp)

    # ---------- ОТКРЫТИЕ ШТОРКИ кнопкой «Итоги учёта» ----------
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(600)
    opened = page.evaluate("""(function(){
        var panel = document.getElementById('wsTotalsPanel');
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var headRect = head.getBoundingClientRect();
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        var btn = document.getElementById('wsTotalsBtn');
        return {open: !panel.hidden,
                pressed: btn.getAttribute('aria-pressed'),
                headEmpty: head.classList.contains('ws-tt-head-empty'),
                headH: headRect.height,
                dW: drawer.width, bW: body.width,
                x: !!document.getElementById('wsTtClose')};
    })()""")
    check('G: шторка открыта кнопкой (aria-pressed), ✕ в шапке НЕТ',
          opened['open'] and opened['pressed'] == 'true' and
          opened['x'] == False)
    check('H: МЕСЯЦ — шапка шторки ПУСТА → СЖАТА до 16px-филлера',
          opened['headEmpty'] == True and
          opened['headH'] >= 14 and opened['headH'] <= 19, opened)
    check('I: шторка = половина рабочей области',
          abs(opened['dW'] - opened['bW'] / 2) < 4, opened)

    # ---------- ВЕРТИКАЛЬНЫЕ ЛИНИИ таблицы итогов ----------
    vlines = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsTtBody tbody tr td');
        var first = tds[0];
        var last = tds[tds.length - 1];
        var cf = getComputedStyle(first);
        var cl = getComputedStyle(last);
        var th = document.querySelector('#wsTtBody thead th');
        var cth = getComputedStyle(th);
        return {fw: parseFloat(cf.borderRightWidth), fs: cf.borderRightStyle,
                fc: cf.borderRightColor,
                lw: parseFloat(cl.borderRightWidth), ls: cl.borderRightStyle,
                thw: parseFloat(cth.borderRightWidth), ths: cth.borderRightStyle,
                bw: parseFloat(cf.borderBottomWidth)};
    })()""")
    check('J: ТОНКИЕ ВЕРТИКАЛЬНЫЕ ЛИНИИ ячеек (th и td, 1px solid)',
          vlines['fs'] == 'solid' and vlines['fw'] >= 1 and
          vlines['ths'] == 'solid' and vlines['thw'] >= 1 and
          vlines['bw'] >= 1, vlines)
    check('K: последняя колонка — БЕЗ линии (таблица не обводится справа)',
          vlines['ls'] == 'none' and vlines['lw'] == 0, vlines)

    # ---------- строки итогов — по строкам сетки ----------
    align = page.evaluate("""(function(){
        var gRows = document.querySelectorAll('#wsGridWrap tbody tr');
        var tRows = document.querySelectorAll('#wsTtBody tbody tr');
        var out = [];
        for (var i=0;i<Math.min(gRows.length,tRows.length);i++) {
            out.push(Math.abs(gRows[i].getBoundingClientRect().top -
                              tRows[i].getBoundingClientRect().top));
        }
        return {max: Math.max.apply(null, out), n: out.length};
    })()""")
    check('L: строки итогов — ровно по строкам сетки (без шапки шторки)',
          align['max'] < 2.5, align)

    # ---------- ГОД: шапка с «Обновить», колонка по тексту ----------
    page.click('#wsTtTabYear')
    page.wait_for_timeout(900)
    yearinfo = page.evaluate("""(function(){
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var ref = document.getElementById('wsTtRefresh');
        var headRect = head.getBoundingClientRect();
        var tds = document.querySelectorAll('#wsTtBody td.ws-tt-emp');
        if (!tds.length) return {err: 'нет строк'};
        var widths = [];
        var range = document.createRange();
        var maxW = 0;
        var maxTd = null;
        for (var i=0;i<tds.length;i++) {
            range.selectNodeContents(tds[i]);
            var w = range.getBoundingClientRect().width;
            widths.push(tds[i].getBoundingClientRect().width);
            if (w > maxW) { maxW = w; maxTd = tds[i]; }
        }
        var colW = widths[0];
        var allSame = widths.every(function(w){ return Math.abs(w - colW) < 1.5; });
        var cs = getComputedStyle(maxTd);
        var pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
        return {headHidden: head.hidden, headH: headRect.height,
                refHidden: ref.hidden, colW: colW, maxW: maxW,
                pad: pad, allSame: allSame, rows: tds.length,
                arch: !!document.querySelector('#wsTtBody .ws-tt-arch')};
    })()""")
    check('M: ГОД — шапка ПОКАЗАНА (кнопка «Обновить»), высота ≥ 28px',
          yearinfo.get('headHidden') == False and yearinfo.get('refHidden') == False and
          yearinfo.get('headH', 0) >= 28, yearinfo)
    check('N: ГОД — колонка «Сотрудник» ПО САМОМУ ШИРОКОМУ тексту',
          yearinfo.get('allSame') and
          abs(yearinfo.get('colW', 0) - (yearinfo.get('maxW', 0) + yearinfo.get('pad', 0))) < 4 and
          yearinfo.get('rows', 0) >= 3 and yearinfo.get('arch'), yearinfo)

    page.screenshot(path='task325-proof-year.png', full_page=False)

    # ---------- ЗАКРЫТИЕ только кнопкой ----------
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(500)
    closed = page.evaluate("""(function(){
        var panel = document.getElementById('wsTotalsPanel');
        var btn = document.getElementById('wsTotalsBtn');
        var cls = document.getElementById('page-work-schedule').className;
        return {panel: panel.hidden, pressed: btn.getAttribute('aria-pressed'), cls: cls};
    })()""")
    check('O: закрытие КНОПКОЙ (✕ нет) — панель скрыта, класс снят',
          closed['panel'] and closed['pressed'] == 'false' and
          ('ws-tt-open' not in closed['cls']), closed)

    # ---------- живая правка: «Сохранить (1)» в ряду 3 ----------
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(500)
    page.evaluate("WorkSchedule.setTotalsTab('month')")
    page.wait_for_timeout(400)
    cell = page.query_selector('#wsGridWrap tbody tr:first-child td.ws-cell:nth-child(3)')
    cell.click()
    page.wait_for_timeout(300)
    popup = page.evaluate("""(function(){
        var p = document.getElementById('wsCellPopup');
        return p && !p.hidden;
    })()""")
    check('P: попап ячейки открылся', popup)
    page.evaluate("WorkSchedule.onPopupStatus('ОТ')")
    page.wait_for_timeout(400)
    save = page.evaluate("""(function(){
        var btn = document.getElementById('wsSaveBtn');
        var act = document.getElementById('wsActionsRow').getBoundingClientRect();
        var br = btn.getBoundingClientRect();
        return {hidden: btn.hidden, text: btn.textContent,
                inRow: br.y >= act.y && (br.y + br.height) <= (act.y + act.height + 1)};
    })()""")
    check('Q: «Сохранить (1)» — в ряду 3 действий, текст со счётчиком',
          save['hidden'] == False and save['text'] == 'Сохранить (1)' and save['inRow'], save)
    page.screenshot(path='task325-proof-desktop.png', full_page=False)
    check('R: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая 1100 =================
    ctx2 = browser.new_context(viewport={'width':1100,'height':760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    light = page.evaluate if False else page2.evaluate
    ok2 = light("""(function(){
        var t = document.getElementById('wsTtBody');
        return !!document.querySelector('#wsGridWrap table');
    })()""")
    check('S: светлая — сетка отрисована', ok2)
    page2.click('#wsTotalsBtn')
    page2.wait_for_timeout(600)
    lv = light("""(function(){
        var td = document.querySelector('#wsTtBody tbody tr td');
        var cf = getComputedStyle(td);
        var head = document.querySelector('#wsTtBody thead th');
        return {rw: parseFloat(cf.borderRightWidth), rs: cf.borderRightStyle,
                rc: cf.borderRightColor,
                thb: getComputedStyle(head).backgroundColor};
    })()""")
    check('T: светлая — вертикальные линии тонкие/тёмные',
          lv['rs'] == 'solid' and lv['rw'] >= 1 and
          ('rgba(0, 0, 0' in lv['rc']), lv)
    emp2 = light("""(function(){
        var names = document.querySelectorAll('#wsGridWrap tbody .ws-emp-name');
        var clipped = 0;
        for (var i=0;i<names.length;i++) {
            if (names[i].scrollWidth > names[i].clientWidth + 1) clipped++;
        }
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        return {clipped: clipped,
                headEmpty: head.classList.contains('ws-tt-head-empty')};
    })()""")
    check('U: светлая — ФИО не обрезаны, шапка шторки сжата (месяц)',
          emp2['clipped'] == 0 and emp2['headEmpty'] == True, emp2)
    page2.screenshot(path='task325-proof-light.png', full_page=False)
    check('V: JS-ошибок нет (светлая)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375 touch =================
    ctx3 = browser.new_context(viewport={'width':375,'height':720},
                                has_touch=True, is_mobile=True)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3)
    mob = page3.evaluate("""(function(){
        var tot = document.getElementById('wsTotalsRow');
        var act = document.getElementById('wsActionsRow');
        var btn = document.getElementById('wsTotalsBtn').getBoundingClientRect();
        var gen = document.getElementById('wsGenerateBtn').getBoundingClientRect();
        return {totVisible: !!tot.offsetParent, actVisible: !!act.offsetParent,
                btnH: btn.height, genH: gen.height};
    })()""")
    check('W: мобильный — ряды итогов/действий видны, кнопки ≥ 28px',
          mob['totVisible'] and mob['actVisible'] and
          mob['btnH'] >= 28 and mob['genH'] >= 28, mob)
    page3.tap('#wsTotalsBtn')
    page3.wait_for_timeout(600)
    mopen = page3.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var tds = document.querySelectorAll('#wsTtBody td.ws-tt-emp');
        var range = document.createRange();
        var maxW = 0, maxTd = null;
        for (var i=0;i<tds.length;i++) {
            range.selectNodeContents(tds[i]);
            var w = range.getBoundingClientRect().width;
            if (w > maxW) { maxW = w; maxTd = tds[i]; }
        }
        var cs = getComputedStyle(maxTd);
        var pad = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
        var colW = tds.length ? tds[0].getBoundingClientRect().width : 0;
        return {open: !document.getElementById('wsTotalsPanel').hidden,
                dW: drawer.width, dX: drawer.x,
                headEmpty: head.classList.contains('ws-tt-head-empty'),
                x: !!document.getElementById('wsTtClose'),
                colW: colW, maxW: maxW, pad: pad,
                rows: tds.length};
    })()""")
    check('X: мобильная шторка открылась (~86vw), ✕ НЕТ, шапка сжата',
          mopen['open'] and mopen['dW'] < 560 and mopen['x'] == False and
          mopen['headEmpty'] == True, mopen)
    check('Y: мобильная — колонка «Сотрудник» ПО ТЕКСТУ (без капа 150px)',
          mopen['rows'] >= 2 and
          abs(mopen['colW'] - (mopen['maxW'] + mopen['pad'])) < 4 and
          mopen['colW'] != 150, mopen)
    page3.screenshot(path='task325-proof-mobile.png', full_page=False)
    # Task 325: ✕ удалён, шторка поверх тулбара — закрытие ТАПОМ МИМО
    # шторки (левая полоса экрана мимо fixed-оверлея; тап в окошко
    # производственного календаря — некликабельная зона)
    page3.touchscreen.tap(10, 300)
    page3.wait_for_timeout(600)
    mclosed = page3.evaluate("""(function(){
        return {panel: document.getElementById('wsTotalsPanel').hidden,
                pressed: document.getElementById('wsTotalsBtn').getAttribute('aria-pressed')};
    })()""")
    check('Z: мобильная — закрытие ТАПОМ МИМО шторки (✕ нет)',
          mclosed['panel'] and mclosed['pressed'] == 'false', mclosed)
    check('Z2: JS-ошибок нет (мобильный)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

fails = [r for r in results if not r[1]]
print('\n===== ИТОГ Task 325 browser-check: %d/%d PASS =====' %
      (len(results) - len(fails), len(results)))
if fails:
    for f in fails:
        print('FAIL: ' + f[0] + ' | ' + str(f[2]))
    raise SystemExit(1)
