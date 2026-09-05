# -*- coding: utf-8 -*-
# Task 324: browser-check «Итоги учёта — кнопки в баре, шторка без
# ручки, одни строки оглавлений, ползунок в шторке»:
#   кнопки «Сформировать», «Сохранить (N)», «Отменить» — В НИЖНЕЙ
#   части бара В ОДИН РЯД; вертикальный бар-ручка справа УДАЛЁН —
#   вместо неё кнопка «Итоги учёта» в нижнем ряду; кнопки «Месяц» и
#   «Год» итогов — СПРАВА от кнопки «Итоги учёта»; пояснительный
#   текст шапки шторки УДАЛЁН; оглавления — ОДНИМИ СТРОКАМИ;
#   нижняя горизонтальная полоса прокрутки — В ШТОРКЕ итогов.
# Проверки: 3 контекста (десктоп-Админ 1280 тёмная, светлая 1100,
# мобильный 375 touch): нижний ряд кнопок (порядок/высоты/раздели-
# тель/скрытие прав), ручки нет (сетка полная ширины), открытие
# кнопкой (aria-pressed, пол-области), выравнивание строк итогов по
# строкам сетки, ОДНОСТРОЧНЫЕ оглавления (высота th), полоса
# прокрутки шторки (scrollWidth > clientWidth), живые правки,
# «Сохранить (N)» в нижнем ряду, вкладка «Год» из тулбара открывает
# шторку, ✕ закрывает (gridwide 320 мс), 0 JS-ошибок, скриншоты.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t324)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t324')")
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

    # ---------- РЯДЫ 2/3 кнопок тулбара (Task 325: итоги — ряд 2, действия — ряд 3) ----------
    rowinfo = page.evaluate("""(function(){
        var tot = document.getElementById('wsTotalsRow');
        var act = document.getElementById('wsActionsRow');
        var gen = document.getElementById('wsGenerateBtn');
        var save = document.getElementById('wsSaveBtn');
        var cancel = document.getElementById('wsCancelBtn');
        var btn = document.getElementById('wsTotalsBtn');
        var tm = document.getElementById('wsTtTabMonth');
        var ty = document.getElementById('wsTtTabYear');
        var tOrder = [], aOrder = [];
        for (var i=0;i<tot.children.length;i++) tOrder.push(tot.children[i].id);
        for (var j=0;j<act.children.length;j++) aOrder.push(act.children[j].id);
        var rt = tot.getBoundingClientRect();
        var ra = act.getBoundingClientRect();
        var sel = document.getElementById('wsSelectsRow').getBoundingClientRect();
        var tbm = btn.getBoundingClientRect();
        var tabm = tm.getBoundingClientRect();
        var main = document.querySelector('.ws-toolbar-main').getBoundingClientRect();
        return {tOrder: tOrder, aOrder: aOrder,
                genHidden: gen.hidden, saveHidden: save.hidden, cancelHidden: cancel.hidden,
                btnVisible: !btn.hidden, tmVisible: !tm.hidden, tyVisible: !ty.hidden,
                hasSep: !!document.querySelector('.ws-tb-sep'),
                totY: rt.y, totH: rt.height, actY: ra.y, actH: ra.height,
                selY: sel.y, selH: sel.height, mainH: main.height,
                btnX: tbm.x, tmX: tabm.x, tyX: ty.getBoundingClientRect().x,
                actBelow: ra.y > rt.y + rt.height - 2,
                noBar: !document.getElementById('wsTotalsBar'),
                noChev: !document.getElementById('wsTotalsChev'),
                noInfo: !document.getElementById('wsTtInfo')};
    })()""")
    check('B: ряд 2 = Итоги/Месяц/Год, ряд 3 = Сформировать/Сохранить/Отменить (Task 325)',
          rowinfo['tOrder'] == ['wsTotalsBtn','wsTtTabMonth','wsTtTabYear'] and
          rowinfo['aOrder'] == ['wsGenerateBtn','wsSaveBtn','wsCancelBtn'] and
          rowinfo['actBelow'], rowinfo)
    check('C: правки/права — Сформировать ВИДЕН, Сохранить/Отменить скрыты (правок нет)',
          (not rowinfo['genHidden']) and rowinfo['saveHidden'] and rowinfo['cancelHidden'], rowinfo)
    check('D: «Итоги учёта»/«Месяц»/«Год» — видны ВСЕМ, вкладки СПРАВА от кнопки',
          rowinfo['btnVisible'] and rowinfo['tmVisible'] and rowinfo['tyVisible'] and
          rowinfo['btnX'] < rowinfo['tmX'] < rowinfo['tyX'])
    check('E: разделитель .ws-tb-sep УДАЛЁН (Task 325: блоки в разных рядах)',
          not rowinfo['hasSep'])
    check('F/G: ТРИ ряда × calc((95−6)/3)≈29,7px — колонка = 95px (Task 325)',
          abs(rowinfo['totH'] - 29.67) < 1.5 and abs(rowinfo['actH'] - 29.67) < 1.5 and
          abs(rowinfo['selH'] - 29.67) < 1.5 and abs(rowinfo['mainH'] - 95) < 1.5, rowinfo)
    check('H: вертикальной ручки и инфо-строки НЕТ (DOM)',
          rowinfo['noBar'] and rowinfo['noChev'] and rowinfo['noInfo'])

    # ---------- свёрнутое состояние: ручки нет — сетка ПОЛНАЯ ширина ----------
    closed0 = page.evaluate("""(function(){
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        var wrap = document.getElementById('wsGridWrap').getBoundingClientRect();
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        return {bodyW: body.width, wrapW: wrap.width,
                drawerX: drawer.x, drawerR: drawer.right,
                panelHidden: document.getElementById('wsTotalsPanel').hidden,
                pressed: document.getElementById('wsTotalsBtn').getAttribute('aria-pressed')};
    })()""")
    check('I: свёрнуто — панель hidden, кнопка aria-pressed=false',
          closed0['panelHidden'] and closed0['pressed'] == 'false', closed0)
    check('J: свёрнуто — шторка ПОЛНОСТЬЮ за правым краем (ручки нет)',
          abs(closed0['wrapW'] - closed0['bodyW']) < 8 and
          closed0['drawerX'] >= closed0['bodyW'] - 5, closed0)
    full_w = closed0['wrapW']

    # ---------- раскрытие КНОПКОЙ «Итоги учёта» ----------
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(600)
    check('K: панель раскрылась КНОПКОЙ тулбара',
          not page.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    check('L: кнопка «нажата» (aria-pressed=true)',
          page.evaluate("document.getElementById('wsTotalsBtn').getAttribute('aria-pressed')") == 'true')
    check('M: классы ws-tt-open И ws-tt-gridwide на странице',
          page.evaluate("document.getElementById('page-work-schedule').className").find('ws-tt-open') != -1 and
          page.evaluate("document.getElementById('page-work-schedule').className").find('ws-tt-gridwide') != -1)
    layout = page.evaluate("""(function(){
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        var wrap = document.getElementById('wsGridWrap').getBoundingClientRect();
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var panel = document.getElementById('wsTotalsPanel').getBoundingClientRect();
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head').getBoundingClientRect();
        return {bodyW: body.width, wrapW: wrap.width, wrapH: wrap.height,
                drawerX: drawer.x, drawerW: drawer.width,
                panelX: panel.x, panelW: panel.width, panelH: panel.height,
                headH: head.height};
    })()""")
    check('N: шторка — ПРАВАЯ ПОЛОВИНА рабочей области',
          abs(layout['drawerW'] - layout['bodyW'] / 2) < 8 and
          abs(layout['drawerX'] - layout['bodyW'] / 2) < 8, layout)
    check('O: ШАХМАТКА ВИДИМА рядом с шторкой (итоги сверяем по сетке)',
          layout['wrapH'] > 300 and abs(layout['wrapW'] - layout['bodyW'] / 2) < 10, layout)
    check('P: шапка шторки компактная (✕ + ⚠ + Обновить, БЕЗ вкладок/инфо)',
          layout['headH'] < 46, layout)

    # ---------- шапка шторки: ⚠/Обновить, ✕ УДАЛЁН (Task 325) ----------
    headinfo = page.evaluate("""(function(){
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var x = document.getElementById('wsTtClose');
        var warn = document.getElementById('wsTtWarn');
        var refresh = document.getElementById('wsTtRefresh');
        var tabs = document.querySelectorAll('#wsTotalsPanel .ws-tt-tab');
        // видимый текст шапки (скрытый «Обновить» не в счёт)
        var vis = '';
        for (var i=0;i<head.childNodes.length;i++){
            var n = head.childNodes[i];
            if (n.nodeType === 3) vis += n.textContent;
            else if (!n.hidden) vis += n.textContent;
        }
        return {x: !!x, warn: !!warn, warnHidden: warn ? warn.hidden : null,
                warnText: warn ? warn.textContent : '',
                refresh: !!refresh, tabsInHead: tabs.length,
                headText: vis.replace(/\\s+/g, ' ').trim(),
                headEmpty: head.classList.contains('ws-tt-head-empty')};
    })()""")
    check('Q: в шапке — «Обновить»(год, скрыт); ✕/вкладок/⚠ нет; пустая → филлер (Task 325)',
          (not headinfo['x']) and headinfo['refresh'] and headinfo['tabsInHead'] == 0 and
          headinfo['warnHidden'] and headinfo['warnText'] == '' and
          headinfo['headEmpty'], headinfo)
    check('R: пояснительный текст «сентябрь · норма · правки» УДАЛЁН (заявка)',
          headinfo['headText'].find('норма') == -1 and
          headinfo['headText'].find('правки') == -1 and
          headinfo['headText'].find('г.') == -1 and
          len(headinfo['headText']) < 5, headinfo['headText'])

    # ---------- ОГЛАВЛЕНИЯ — ОДНИМИ СТРОКАМИ + ПОЛЗУНОК ШТОРКИ ----------
    headrows = page.evaluate("""(function(){
        var ths = document.querySelectorAll('#wsTtBody thead th');
        var maxH = 0, vals = [];
        for (var i=0;i<ths.length;i++){
            var h = ths[i].getBoundingClientRect().height;
            if (h > maxH) maxH = h;
            vals.push(ths[i].textContent);
        }
        var body = document.getElementById('wsTtBody');
        return {n: ths.length, maxH: maxH, vals: vals,
                sw: body.scrollWidth, cw: body.clientWidth,
                h1: ths.length > 1 ? ths[1].getBoundingClientRect().height : 0};
    })()""")
    check('S: оглавления ОДНИМИ СТРОКАМИ (высота th ≈ одной строке)',
          headrows['maxH'] < 26 and headrows['h1'] > 14, headrows)
    check('T: полная шапка словами на месте (День (Д)…Прочие…Всего)',
          'День (Д)' in headrows['vals'] and 'Больничный (Б)' in headrows['vals'] and
          'Переработка' in headrows['vals'] and 'Всего' in headrows['vals'], headrows['vals'])
    check('U: ШТОРКА — таблица ШИРЕ панели → ГОРИЗОНТАЛЬНАЯ ПРОКРУТКА (заявка)',
          headrows['sw'] > headrows['cw'] + 40, headrows)
    sbvis = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var r = body.getBoundingClientRect();
        var el = document.elementFromPoint(r.x + r.width / 2, r.bottom - 6);
        // на дне скролл-зоны — сама полоса/бегунок (или контент под ней)
        return {atBottom: !!el, sw: body.scrollWidth, cw: body.clientWidth,
                ovx: getComputedStyle(body).overflowX};
    })()""")
    check('V: ползунок ВНИЗУ шторки активен (overflow-x: auto, прокрутка есть)',
          sbvis['ovx'] == 'auto' and sbvis['sw'] > sbvis['cw'], sbvis)
    # прокрутка таблицы итогов ползунком шторки
    page.evaluate("document.getElementById('wsTtBody').scrollLeft = 120")
    scrolled = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        return {sl: body.scrollLeft, sw: body.scrollWidth};
    })()""")
    check('W: прокрутка шторки работает (scrollLeft > 0)',
          scrolled['sl'] > 50, scrolled)
    page.evaluate("document.getElementById('wsTtBody').scrollLeft = 0")

    # ---------- СТРОКИ ИТОГОВ — РОВНО ПО СТРОКАМ СОТРУДНИКОВ ----------
    align = page.evaluate("""(function(){
        var g = document.querySelectorAll('#wsGridWrap tbody tr');
        var t = document.querySelectorAll('#wsTtBody tbody tr');
        var gt = document.querySelector('#wsGridWrap thead');
        var pt = document.querySelector('#wsTtBody .ws-tt-table thead');
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var out = {g: [], t: []};
        for (var i=0;i<g.length;i++) out.g.push(g[i].getBoundingClientRect().top);
        for (var j=0;j<t.length;j++) out.t.push(t[j].getBoundingClientRect().top);
        out.gHeadH = gt.getBoundingClientRect().height;
        out.pHeadH = head.getBoundingClientRect().height + pt.getBoundingClientRect().height;
        return out;
    })()""")
    ok_align = True
    for i in range(min(len(align['g']), len(align['t']))):
        if abs(align['g'][i] - align['t'][i]) > 2.5:
            ok_align = False
    check('X: СТРОКИ ИТОГОВ ровно по строкам сотрудников (top совпадает)',
          ok_align and len(align['g']) == 2, align)
    check('Y: шапка сетки = шапка шторки + шапка таблицы (выравнивание)',
          abs(align['gHeadH'] - align['pHeadH']) <= 2.5,
          {'gridHead': align['gHeadH'], 'panelZone': align['pHeadH']})

    # месяц: колонка сотрудника скрыта; значения; tfoot; зебра
    empvis = page.evaluate("getComputedStyle(document.querySelector('#wsTtBody th.ws-tt-emp')).display")
    check('Z: колонка «Сотрудник» СКРЫТА на десктопе (месяц)', empvis == 'none', empvis)
    mh = page.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('Z2: tfoot «Итого» на месте',
          '</tbody><tfoot>' in mh and 'Итого по подразделению' in mh)
    row017 = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsTtBody tbody tr')[0].querySelectorAll('td');
        return [tds[1].textContent, tds[2].textContent, tds[10].textContent];
    })()""")
    check('Z3: Иванов — явки 4 / часы 43,2 / переработка 12',
          row017[0] == '4' and row017[1] == '43,2' and row017[2] == '12', row017)
    total = page.evaluate("""(function(){
        var tr = document.querySelector('#wsTtBody tfoot tr');
        var tds = tr.querySelectorAll('td');
        return {over: tds[10].textContent, hours: tds[2].textContent,
                bottom: tr.getBoundingClientRect().bottom,
                panelBottom: document.getElementById('wsTtBody').getBoundingClientRect().bottom};
    })()""")
    check('Z4: ИТОГО — переработка 19,2, часы 59,2; tfoot у низа панели',
          total['over'] == '19,2' and total['hours'] == '59,2' and
          abs(total['bottom'] - total['panelBottom']) < 8, total)

    # ---------- живая правка → «Сохранить (N)» В НИЖНЕМ РЯДУ ----------
    page.click('#wsGridWrap tbody tr:nth-child(1) td[data-day="11"]')
    page.wait_for_timeout(400)
    page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent === 'д') { rows[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(400)
    saveinfo = page.evaluate("""(function(){
        var save = document.getElementById('wsSaveBtn');
        var cancel = document.getElementById('wsCancelBtn');
        var tds = document.querySelectorAll('#wsTtBody tbody tr')[0].querySelectorAll('td');
        return {saveText: save.textContent, saveHidden: save.hidden,
                cancelHidden: cancel.hidden,
                inActionsRow: !!save.closest('#wsActionsRow'),
                over: tds[10].textContent};
    })()""")
    check('AA: правка ячейки — итоги ЖИВЬЁМ (д → переработка 24)',
          saveinfo['over'] == '24', saveinfo)
    check('AB: «Сохранить (1)» и «Отменить» появились В РЯДУ 3 (действия, Task 325)',
          saveinfo['saveText'] == 'Сохранить (1)' and not saveinfo['saveHidden'] and
          not saveinfo['cancelHidden'] and saveinfo['inActionsRow'], saveinfo)
    # ряд 3: все кнопки на ОДНОЙ высоте
    onerow2 = page.evaluate("""(function(){
        var kids = document.querySelectorAll('#wsActionsRow button');
        var top = null, ok = true;
        for (var i=0;i<kids.length;i++){
            if (kids[i].hidden) continue;
            var t = kids[i].getBoundingClientRect().top;
            if (top === null) top = t;
            else if (Math.abs(t - top) > 2) ok = false;
        }
        return ok;
    })()""")
    check('AC: с правками — кнопки ряда 3 ПО-ПРЕЖНЕМУ в одну строку', onerow2)
    page.evaluate("WorkSchedule._PENDING = {}; WorkSchedule._renderGrid();")
    page.wait_for_timeout(300)
    page.screenshot(path='task324-proof-desktop.png', full_page=False)

    # ---------- ГОД из тулбара: вкладка открывает ЗАКРЫТУЮ шторку ----------
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(500)
    check('AD: закрытие кнопкой — панель скрыта, кнопка отпущена',
          page.evaluate("document.getElementById('wsTotalsPanel').hidden") and
          page.evaluate("document.getElementById('wsTotalsBtn').getAttribute('aria-pressed')") == 'false')
    page.click('#wsTtTabYear')
    page.wait_for_timeout(1500)
    yearinfo = page.evaluate("""(function(){
        var th = document.querySelector('#wsTtBody th.ws-tt-emp');
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        var table = document.querySelector('#wsTtBody .ws-tt-table');
        var tabY = document.getElementById('wsTtTabYear');
        var iIv = -1, iSid = -1, iPet = -1;
        for (var i=0;i<trs.length;i++){
            var t = trs[i].textContent;
            if (t.indexOf('Иванов') !== -1) iIv = i;
            if (t.indexOf('Петров') !== -1) iPet = i;
            if (t.indexOf('Сидоров') !== -1) iSid = i;
        }
        return {open: !document.getElementById('wsTotalsPanel').hidden,
                emp: th ? getComputedStyle(th).display : null, n: trs.length,
                iIv: iIv, iPet: iPet, iSid: iSid,
                yearClass: table.className.indexOf('ws-tt-year') !== -1,
                tabActive: tabY.classList.contains('active'),
                refresh: !document.getElementById('wsTtRefresh').hidden,
                warnHidden: document.getElementById('wsTtWarn').hidden,
                bodyW: document.getElementById('wsTtBody').scrollWidth,
                bodyC: document.getElementById('wsTtBody').clientWidth};
    })()""")
    check('AE: клик «Год» в тулбаре ОТКРЫЛ закрытую шторку (годовой вид)',
          yearinfo['open'] and yearinfo['tabActive'] and yearinfo['refresh'], yearinfo)
    check('AF: год — колонка «Сотрудник» ВИДИНА, архив ниже активных, ⚠ скрыта',
          yearinfo['emp'] != 'none' and yearinfo['n'] == 3 and
          yearinfo['iIv'] < yearinfo['iSid'] and yearinfo['iPet'] < yearinfo['iSid'] and
          yearinfo['warnHidden'], yearinfo)
    check('AG: год — 12 колонок: таблица шире панели (ползунок шторки)',
          yearinfo['bodyW'] > yearinfo['bodyC'] + 40, yearinfo)
    page.screenshot(path='task324-proof-year.png', full_page=False)

    # ---------- закрытие КНОПКОЙ тулбара (Task 325: ✕ удалён) ----------
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(150)
    closed_now = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        return {panel: document.getElementById('wsTotalsPanel').hidden,
                open: p.classList.contains('ws-tt-open'),
                wide: p.classList.contains('ws-tt-gridwide'),
                pressed: document.getElementById('wsTotalsBtn').getAttribute('aria-pressed')};
    })()""")
    check('AH: кнопка закрыла — панель скрыта, gridwide ДЕРЖИТСЯ (анимация)',
          closed_now['panel'] and not closed_now['open'] and closed_now['wide'] and
          closed_now['pressed'] == 'false', closed_now)
    page.wait_for_timeout(500)
    closed_after = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var w = document.getElementById('wsGridWrap').getBoundingClientRect().width;
        return {wide: p.classList.contains('ws-tt-gridwide'), wrapW: w};
    })()""")
    check('AI: после анимации — gridwide снят, сетка ПОЛНАЯ ширина',
          not closed_after['wide'] and abs(closed_after['wrapW'] - full_w) < 8, closed_after)
    check('AJ: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая 1100 =================
    ctx2 = browser.new_context(viewport={'width':1100,'height':760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    check('AK: светлая — страница/сетка',
          page2.evaluate("document.documentElement.getAttribute('data-theme')") == 'light' and
          page2.evaluate("!!document.querySelector('#wsGridWrap table')"))
    page2.click('#wsTotalsBtn')
    page2.wait_for_timeout(600)
    lightgeom = page2.evaluate("""(function(){
        var body = document.getElementById('wsWsBody').getBoundingClientRect();
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var wrap = document.getElementById('wsGridWrap').getBoundingClientRect();
        var btn = document.getElementById('wsTotalsBtn');
        var tabs = document.getElementById('wsTtTabMonth');
        return {half: Math.abs(drawer.width - body.width / 2) < 8,
                wrapW: wrap.width, bodyW: body.width,
                btnBg: getComputedStyle(btn).backgroundColor,
                tabBg: getComputedStyle(tabs).backgroundColor,
                sw: document.getElementById('wsGridWrap').scrollWidth,
                cw: document.getElementById('wsGridWrap').clientWidth,
                ttSw: document.getElementById('wsTtBody').scrollWidth,
                ttCw: document.getElementById('wsTtBody').clientWidth};
    })()""")
    check('AL: светлая — шторка на пол-области, сетка рядом',
          lightgeom['half'] and lightgeom['wrapW'] < lightgeom['bodyW'] * 0.55, lightgeom)
    check('AM: светлая — кнопка/вкладки/ползунки живы',
          lightgeom['sw'] > lightgeom['cw'] + 50 and
          lightgeom['ttSw'] > lightgeom['ttCw'] + 40, lightgeom)
    vals2 = page2.evaluate("""(function(){
        var tr = document.querySelector('#wsTtBody tfoot tr');
        return tr ? tr.querySelectorAll('td')[10].textContent : null;
    })()""")
    check('AN: светлая — итоги считаются (переработка 19,2)',
          vals2 == '19,2', vals2)
    page2.screenshot(path='task324-proof-light.png', full_page=False)
    check('AO: JS-ошибок нет (светлая)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375 (touch) =================
    ctx3 = browser.new_context(viewport={'width':375,'height':720},
                               is_mobile=True, has_touch=True)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3, theme='dark')
    check('AP: мобильная — страница/сетка',
          page3.evaluate("!!document.querySelector('#wsGridWrap table')"))
    mobrow = page3.evaluate("""(function(){
        var btn = document.getElementById('wsTotalsBtn');
        var tm = document.getElementById('wsTtTabMonth');
        var r = btn.getBoundingClientRect();
        var rm = tm.getBoundingClientRect();
        var tot = !!document.getElementById('wsTotalsRow').offsetParent;
        var act = !!document.getElementById('wsActionsRow').offsetParent;
        return {btnW: r.width, btnH: r.height,
                tabW: rm.width, tabH: rm.height,
                totVisible: tot, actVisible: act,
                sepVisible: !!document.querySelector('.ws-tb-sep')};
    })()""")
    check('AQ: мобильный — ряды итогов/действий видны (тап-зона ≥34px)',
          mobrow['btnH'] >= 34 and mobrow['tabH'] >= 34 and
          mobrow['totVisible'] and mobrow['actVisible'] and
          not mobrow['sepVisible'], mobrow)
    # открытие шторки кнопкой; закрытие — ТАП МИМО (Task 325: ✕ удалён)
    page3.tap('#wsTotalsBtn')
    page3.wait_for_timeout(600)
    mobopen = page3.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        var body = document.getElementById('wsTtBody').getBoundingClientRect();
        var vw = window.innerWidth;
        return {open: !document.getElementById('wsTotalsPanel').hidden,
                dX: drawer.x, dW: drawer.width,
                x: !!document.getElementById('wsTtClose'),
                ttSw: document.getElementById('wsTtBody').scrollWidth,
                ttCw: document.getElementById('wsTtBody').clientWidth,
                empVis: getComputedStyle(document.querySelector('#wsTtBody th.ws-tt-emp')).display,
                bodyH: body.height};
    })()""")
    check('AR: мобильная шторка открылась (~86vw), ✕ НЕТ (Task 325)',
          mobopen['open'] and mobopen['dW'] < 560 and mobopen['dX'] < 375 - 300 and
          not mobopen['x'], mobopen)
    check('AS: мобильная — колонка «Сотрудник» ВИДИНА, прокрутка шторки есть',
          mobopen['empVis'] != 'none' and mobopen['ttSw'] > mobopen['ttCw'] + 40, mobopen)
    page3.screenshot(path='task324-proof-mobile.png', full_page=False)
    page3.touchscreen.tap(10, 300)
    page3.wait_for_timeout(500)
    mobclosed = page3.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer').getBoundingClientRect();
        return {panel: document.getElementById('wsTotalsPanel').hidden,
                dX: drawer.x};
    })()""")
    check('AT: мобильная — тап МИМО закрыл шторку (уехала за экран)',
          mobclosed['panel'] and mobclosed['dX'] > 370, mobclosed)
    check('AU: JS-ошибок нет (мобильный)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

fails = [r for r in results if not r[1]]
print('\n===== ИТОГ Task 324 browser-check: %d/%d PASS =====' %
      (len(results) - len(fails), len(results)))
if fails:
    for f in fails:
        print('FAIL: ' + f[0] + ' | ' + str(f[2]))
    raise SystemExit(1)
