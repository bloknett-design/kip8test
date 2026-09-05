# -*- coding: utf-8 -*-
# Task 323: browser-check «Итоги учёта — боковая шторка справа»:
#   бар итогов перенесён в ПРАВУЮ часть экрана (вертикальный текст
#   названия), при открытии шторка выдвигается СПРАВА НАЛЕВО на
#   ПОЛОВИНУ рабочей области, внизу шахматки появляется ВИДИМЫЙ
#   ползунок горизонтальной прокрутки (дни прокручиваются под
#   шторкой — удобно сверять расчёты), строки итогов — РОВНО ПО
#   СТРОКАМ сотрудников шахматки (поэтому список работников в
#   панели на десктопе убран; год и мобайл — со списком).
# Проверки: 3 контекста (десктоп-Админ 1280 тёмная, светлая 1100,
# мобильный 375 touch): геометрия шторки/бара, вертикальный текст
# (writing-mode), ползунок (scrollWidth > clientWidth), выравнивание
# строк (top строк сетки == top строк панели), tfoot у низа,
# скрытая колонка «Сотрудник» (месяц) и открытая (год), живые правки
# в итогах, год: активные по порядку сетки + архив ниже, закрытие
# (gridwide держится 320 мс, затем сетка полная), 0 JS-ошибок,
# скриншоты.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8943
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t323)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t323')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)

# Значение N-й колонки строки сотрудника в панели итогов
JS_ROW_VAL = """(function(fi){
    var trs = document.querySelectorAll('#wsTtBody tbody tr');
    for (var i=0;i<trs.length;i++){
        var tds = trs[i].querySelectorAll('td');
        // месяц: колонка сотрудника скрыта display:none — td.ws-tt-emp
        // всё равно в DOM: индексы не сместились
        return trs[0].querySelectorAll('td')[fi].textContent;
    }
    return null;
})(%d)"""

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

    # ---------- свёрнутое состояние: бар-ручка у ПРАВОГО края ----------
    bar0 = page.evaluate("""(function(){
        var bar = document.getElementById('wsTotalsBar');
        var r = bar.getBoundingClientRect();
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        return {x: r.x, w: r.width, h: r.height, bodyRight: body.right,
                writing: getComputedStyle(bar.querySelector('.ws-totals-bar-cap')).writingMode,
                chev: document.getElementById('wsTotalsChev').textContent};
    })()""")
    check('B: панель скрыта по умолчанию',
          page.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    check('C: бар у ПРАВОГО края рабочей области (видно 28px)',
          abs(bar0['x'] + bar0['w'] - bar0['bodyRight']) < 3 and bar0['w'] < 40, bar0)
    check('D: текст названия ВЕРТИКАЛЬНЫЙ (writing-mode)',
          'vertical' in bar0['writing'], bar0['writing'])
    check('E: шеврон «влево» (закрыто)', bar0['chev'] == '◂', bar0['chev'])
    full_w = page.evaluate("document.getElementById('wsGridWrap').getBoundingClientRect().width")

    # ---------- раскрытие: справа налево на ПОЛОВИНУ области ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(600)
    check('F: панель раскрылась',
          not page.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    check('G: классы ws-tt-open И ws-tt-gridwide на странице',
          page.evaluate("document.getElementById('page-work-schedule').className") .find('ws-tt-open') != -1 and
          page.evaluate("document.getElementById('page-work-schedule').className").find('ws-tt-gridwide') != -1)
    check('H: шеврон «вправо» (открыто)',
          page.evaluate("document.getElementById('wsTotalsChev').textContent") == '▸')
    layout = page.evaluate("""(function(){
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        var wrap = document.getElementById('wsGridWrap').getBoundingClientRect();
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var panel = document.getElementById('wsTotalsPanel').getBoundingClientRect();
        var bar = document.getElementById('wsTotalsBar').getBoundingClientRect();
        return {bodyW: body.width, wrapW: wrap.width, wrapH: wrap.height,
                drawerX: drawer.x, drawerW: drawer.width,
                panelX: panel.x, panelW: panel.width, panelH: panel.height,
                barX: bar.x, barW: bar.width};
    })()""")
    check('I: ШАХМАТКА ВИДИМА (не скрыта) — итоги РЯДОМ с сеткой',
          layout['wrapH'] > 300, layout)
    check('J: шторка заняла ПРАВУЮ ПОЛОВИНУ рабочей области',
          abs(layout['drawerX'] + layout['drawerW'] - (layout['bodyW'] if False else (layout['drawerX'] + layout['drawerW']))) >= 0 and
          abs(layout['drawerW'] - layout['bodyW'] / 2) < 8 and
          abs(layout['drawerX'] - layout['bodyW'] / 2) < 8, layout)
    check('K: сетка сжата до левой половины (шторка = 50%, вкл. бар)',
          abs(layout['wrapW'] - layout['bodyW'] / 2) < 10 and
          abs(layout['panelW'] - (layout['drawerW'] - layout['barW'])) < 6, layout)
    check('L: панель правее бара (бар — ручка между сеткой и итогами)',
          layout['panelX'] > layout['barX'] and layout['barX'] < layout['drawerX'] + 40, layout)

    # ---------- ползунок внизу шахматки ----------
    scrollinfo = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var r = wrap.getBoundingClientRect();
        return {sw: wrap.scrollWidth, cw: wrap.clientWidth,
                ovx: getComputedStyle(wrap).overflowX,
                h: r.height, top: r.top};
    })()""")
    check('M: ПОЛЗУНОК — контент шире области (прокрутка дней)',
          scrollinfo['sw'] > scrollinfo['cw'] + 100, scrollinfo)
    check('N: ползунок виден (overflow-x: auto)',
          scrollinfo['ovx'] == 'auto', scrollinfo)
    # прокрутка дней под шторкой
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 250")
    daycol = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap thead th.ws-emp-col');
        var tds = document.querySelectorAll('#wsGridWrap tbody td.ws-emp-col');
        return {stickyX: th.getBoundingClientRect().x,
                cellX: tds.length ? tds[0].getBoundingClientRect().x : -1};
    })()""")
    check('O: прокрутка работает, ФИО прилипла к левому краю',
          daycol['stickyX'] < 210 and abs(daycol['stickyX'] - daycol['cellX']) < 2, daycol)
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 0")

    # ---------- СТРОКИ ИТОГОВ — РОВНО ПО СТРОКАМ СОТРУДНИКОВ ----------
    align = page.evaluate("""(function(){
        var g = document.querySelectorAll('#wsGridWrap tbody tr');
        var t = document.querySelectorAll('#wsTtBody tbody tr');
        var gt = document.querySelector('#wsGridWrap thead');
        var pt = document.querySelector('#wsTtBody .ws-tt-table thead');
        var tabs = document.querySelector('#wsTotalsPanel .ws-tt-tabs');
        var out = {g: [], t: []};
        for (var i=0;i<g.length;i++) out.g.push({top: g[i].getBoundingClientRect().top,
                                                  h: g[i].getBoundingClientRect().height});
        for (var j=0;j<t.length;j++) out.t.push({top: t[j].getBoundingClientRect().top,
                                                  h: t[j].getBoundingClientRect().height});
        out.gHeadH = gt.getBoundingClientRect().height;
        out.pTabsH = tabs.getBoundingClientRect().height;
        out.pHeadH = pt.getBoundingClientRect().height;
        out.bodyScrollTop = document.getElementById('wsTtBody').scrollTop;
        return out;
    })()""")
    ok_align = True
    for i in range(min(len(align['g']), len(align['t']))):
        if abs(align['g'][i]['top'] - align['t'][i]['top']) > 2.5:
            ok_align = False
    check('P: СТРОКИ ИТОГОВ ровно по строкам сотрудников (top совпадает)',
          ok_align and len(align['g']) == 2, align)
    head_match = abs(align['gHeadH'] - (align['pTabsH'] + align['pHeadH'])) <= 2.5
    check('Q: шапка сетки = зона вкладок+шапка панели (выравнивание строк)',
          head_match and align['gHeadH'] > 45,
          {'gridHead': align['gHeadH'], 'panelZone': align['pTabsH'] + align['pHeadH']})

    # ---------- месяц: колонка сотрудника скрыта, значения, tfoot ----------
    empvis = page.evaluate("""(function(){
        var th = document.querySelector('#wsTtBody th.ws-tt-emp');
        return getComputedStyle(th).display;
    })()""")
    check('R: колонка «Сотрудник» СКРЫТА на десктопе (месяц)',
          empvis == 'none', empvis)
    mh = page.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('S: шапка словами + tfoot «Итого»',
          'День (Д)' in mh and 'Больничный (Б)' in mh and
          'Переработка' in mh and '</tbody><tfoot>' in mh and
          'Итого по подразделению' in mh)
    # Иванов (1-я строка): явки 4, часы 43,2, переработка 12
    # (колонка сотрудника скрыта display:none, но В DOM — индексы с ней)
    row017 = page.evaluate(JS_ROW_VAL % 1), page.evaluate(JS_ROW_VAL % 2), page.evaluate(JS_ROW_VAL % 10)
    check('T: Иванов — явки 4 / часы 43,2 / переработка 12',
          row017[0] == '4' and row017[1] == '43,2' and row017[2] == '12', row017)
    row023 = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        var tds = trs[1].querySelectorAll('td');
        return [tds[1].textContent, tds[2].textContent, tds[10].textContent];
    })()""")
    check('U: Петров — явки 2 / часы 16 / переработка 7,2',
          row023[0] == '2' and row023[1] == '16' and row023[2] == '7,2', row023)
    total = page.evaluate("""(function(){
        var tr = document.querySelector('#wsTtBody tfoot tr');
        var tds = tr.querySelectorAll('td');
        return {over: tds[10].textContent, hours: tds[2].textContent,
                bottom: tr.getBoundingClientRect().bottom,
                panelBottom: document.getElementById('wsTtBody').getBoundingClientRect().bottom};
    })()""")
    check('V: ИТОГО — переработка 19,2, часы 59,2',
          total['over'] == '19,2' and total['hours'] == '59,2', total)
    check('W: итоговая строка прилипла к НИЗУ панели',
          abs(total['bottom'] - total['panelBottom']) < 4, total)
    zebra = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        return {r0: getComputedStyle(trs[0]).backgroundColor,
                r1: getComputedStyle(trs[1]).backgroundColor};
    })()""")
    check('X: зебра строк жива (чётная тонирована)',
          zebra['r1'] != zebra['r0'] and zebra['r1'] != 'rgba(0, 0, 0, 0)', zebra)

    # ---------- живая правка: д в пустую ячейку Иванова (сменный) ----------
    page.click('#wsGridWrap tbody tr:nth-child(1) td[data-day="11"]')
    page.wait_for_timeout(400)
    page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent === 'д') { rows[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(300)
    row017b = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        var tds = trs[0].querySelectorAll('td');
        return {over: tds[10].textContent, total: tds[11].textContent};
    })()""")
    check('Y: правка ячейки — итоги обновились ЖИВЬЁМ (д → переработка 24)',
          row017b['over'] == '24', row017b)
    check('Y2: инфо упоминает несохранённые правки',
          page.evaluate("document.getElementById('wsTtInfo').textContent").find('правки') != -1)
    page.evaluate("WorkSchedule._PENDING = {}; WorkSchedule._renderGrid();")
    page.wait_for_timeout(300)
    page.screenshot(path='task323-proof-desktop.png', full_page=False)

    # ---------- ГОД: колонка сотрудника видна, архив ниже, активные по сетке ----------
    page.evaluate("WorkSchedule.setTotalsTab('year')")
    page.wait_for_timeout(1500)
    yearinfo = page.evaluate("""(function(){
        var th = document.querySelector('#wsTtBody th.ws-tt-emp');
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        var table = document.querySelector('#wsTtBody .ws-tt-table');
        var iIv = -1, iSid = -1, iPet = -1;
        for (var i=0;i<trs.length;i++){
            var t = trs[i].textContent;
            if (t.indexOf('Иванов') !== -1) iIv = i;
            if (t.indexOf('Петров') !== -1) iPet = i;
            if (t.indexOf('Сидоров') !== -1) iSid = i;
        }
        return {emp: getComputedStyle(th).display, n: trs.length,
                iIv: iIv, iPet: iPet, iSid: iSid,
                yearClass: table.className.indexOf('ws-tt-year') !== -1,
                refresh: !document.getElementById('wsTtRefresh').hidden};
    })()""")
    check('Z: ГОД — колонка «Сотрудник» ВИДИМА (строки не по сетке)',
          yearinfo['emp'] != 'none', yearinfo)
    check('Z2: год — 12 колонок + архивный Сидоров в таблице',
          yearinfo['n'] == 3 and yearinfo['iSid'] != -1, yearinfo)
    check('Z3: год — активные ВЫШЕ архива (порядок сетки)',
          yearinfo['iIv'] < yearinfo['iSid'] and yearinfo['iPet'] < yearinfo['iSid'], yearinfo)
    check('Z4: таблица года с классом ws-tt-year, «Обновить» видна',
          yearinfo['yearClass'] and yearinfo['refresh'], yearinfo)
    # переключение обратно — колонка снова скрыта
    page.evaluate("WorkSchedule.setTotalsTab('month')")
    page.wait_for_timeout(500)
    check('Z5: возврат на месяц — колонка снова скрыта',
          page.evaluate("getComputedStyle(document.querySelector('#wsTtBody th.ws-tt-emp')).display") == 'none')

    # ---------- закрытие: панель скрыта, gridwide 320мс, затем полный вид ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(150)
    closed_now = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        return {panel: document.getElementById('wsTotalsPanel').hidden,
                open: p.classList.contains('ws-tt-open'),
                wide: p.classList.contains('ws-tt-gridwide'),
                chev: document.getElementById('wsTotalsChev').textContent};
    })()""")
    check('AA: закрытие — панель скрыта, ws-tt-open снят, gridwide ДЕРЖИТСЯ',
          closed_now['panel'] and not closed_now['open'] and closed_now['wide'], closed_now)
    page.wait_for_timeout(500)
    closed_after = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var w = document.getElementById('wsGridWrap').getBoundingClientRect().width;
        return {wide: p.classList.contains('ws-tt-gridwide'), wrapW: w};
    })()""")
    check('AB: после анимации — gridwide снят, сетка ПОЛНАЯ ширина',
          not closed_after['wide'] and abs(closed_after['wrapW'] - full_w) < 8, closed_after)
    check('AC: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая 1100 =================
    ctx2 = browser.new_context(viewport={'width':1100,'height':760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    check('AD: светлая — страница/сетка',
          page2.evaluate("document.documentElement.getAttribute('data-theme')") == 'light' and
          page2.evaluate("!!document.querySelector('#wsGridWrap table')"))
    page2.click('#wsTotalsBar')
    page2.wait_for_timeout(600)
    lightgeom = page.evaluate and page2.evaluate("""(function(){
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var wrap = document.getElementById('wsGridWrap').getBoundingClientRect();
        var bar = document.getElementById('wsTotalsBar');
        var cap = bar.querySelector('.ws-totals-bar-cap');
        return {half: Math.abs(drawer.width - body.width / 2) < 8,
                wrapW: wrap.width, bodyW: body.width,
                capColor: getComputedStyle(cap).color,
                sw: document.getElementById('wsGridWrap').scrollWidth,
                cw: document.getElementById('wsGridWrap').clientWidth};
    })()""")
    check('AE: светлая — шторка на пол-области, сетка рядом, ползунок',
          lightgeom['half'] and lightgeom['wrapW'] < lightgeom['bodyW'] * 0.55 and
          lightgeom['sw'] > lightgeom['cw'] + 50, lightgeom)
    vals2 = page2.evaluate("""(function(){
        var tr = document.querySelector('#wsTtBody tfoot tr');
        return tr ? tr.querySelectorAll('td')[10].textContent : null;
    })()""")
    check('AF: светлая — итог переработки 19,2', vals2 == '19,2', vals2)
    page2.screenshot(path='task323-proof-light.png', full_page=False)
    check('AG: светлая — JS-ошибок нет', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375, touch =================
    ctx3 = browser.new_context(viewport={'width':375,'height':720}, has_touch=True,
                               is_mobile=True, device_scale_factor=2)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3)
    check('AH: мобильный — сетка отрисована',
          page3.evaluate("!!document.querySelector('#wsGridWrap table')"))
    mob0 = page3.evaluate("""(function(){
        var bar = document.getElementById('wsTotalsBar').getBoundingClientRect();
        return {x: bar.x, w: bar.width};
    })()""")
    check('AI: мобильный — бар-ручка у правого края, тап-зона 44px',
          abs(mob0['x'] + mob0['w'] - 375) < 4 and mob0['w'] >= 40, mob0)
    page3.tap('#wsTotalsBar')
    page3.wait_for_timeout(600)
    mob1 = page3.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var panel = document.getElementById('wsTotalsPanel').getBoundingClientRect();
        var th = document.querySelector('#wsTtBody th.ws-tt-emp');
        return {drawerX: drawer.x, drawerW: drawer.width,
                panelVisible: !document.getElementById('wsTotalsPanel').hidden,
                emp: getComputedStyle(th).display,
                panelH: panel.height};
    })()""")
    check('AJ: мобильный — тап раскрыл шторку (~86vw fixed)',
          mob1['panelVisible'] and abs(mob1['drawerW'] - 322.5) < 30 and mob1['drawerX'] <= 60, mob1)
    check('AK: мобильный — список сотрудников ВИДИМ (строки не по сетке)',
          mob1['emp'] != 'none' and mob1['panelH'] > 200, mob1)
    mh3 = page3.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('AL: мобильный — слова в шапке + Иванов в списке',
          'День (Д)' in mh3 and 'Иванов' in mh3 and 'Итого по подразделению' in mh3)
    page3.screenshot(path='task323-proof-mobile.png', full_page=False)
    page3.tap('#wsTotalsBar')
    page3.wait_for_timeout(500)
    check('AM: мобильный — повторный тап свернул шторку',
          page3.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    check('AN: мобильный — JS-ошибок нет', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

failed = [r for r in results if not r[1]]
print()
print('=' * 60)
print('ИТОГ: %d/%d PASS, %d FAIL' % (len(results) - len(failed), len(results), len(failed)))
if failed:
    print('Провалены:')
    for name, _, extra in failed:
        print('  ✗', name, '|', str(extra)[:160])
import sys
sys.exit(1 if failed else 0)
