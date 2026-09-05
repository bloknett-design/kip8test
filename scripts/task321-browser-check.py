# -*- coding: utf-8 -*-
# Task 321: browser-check «Табель учёта рабочего времени» — три части:
#   1) Год в списке выбора — РОВНО три пункта (один до текущего,
#      текущий, один после); Task 320 делал ±3 (7 пунктов).
#   2) Раздел переименован: заголовок страницы, кнопка на
#      «Документация ИОС», крошки (PAGE_LABELS), пункт сайдбара.
#   3) ИТОГИ УЧЁТА под шахматкой: сворачиваемая панель (бар), не
#      мешает сетке (высота восстанавливается); вкладка «Месяц» —
#      явки/часы/Д/Н/неявки/прочие по сотрудникам + «Итого»,
#      формат «39,2» (запятая), живое обновление при несохранённых
#      правках; вкладка «Год» — 12 месяцев «явки/часы», годовые
#      суммы, архивный персонал с пометкой, «Обновить» перезагружает
#      (12 запросов listEntries), неполные данные предупреждаются.
# Проверки: 3 контекста (десктоп-Админ 1280 тёмная, светлая 1024,
# мобильный 375 touch), 0 JS-ошибок, скриншоты.
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404 — фолбэк, как офлайн).
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8941
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час, 7:30–19:30)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час (7:30–16:30)','color':'#FFF9C4'},
  {'code':'Д7,2','name':'День 7,2-час (пятн./предпраздн.)','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час, 19:30–7:30)','color':'#B0BEC5'},
  {'code':'ОТ','name':'Отпуск основной','color':'#ECEFF1'},
  {'code':'Б','name':'Больничный','color':'#F8BBD0'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'}
]
# 017 — сменный; 023 — дневной; 099 — АРХИВНЫЙ (уволен), виден
# только в годовых итогах (listEmployees includeArchived=true)
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
# Месяц: 017 — Д,Д,Н,Д7,2,ОТ,ОТ,Б,«.» (явки 4, часы 39,2);
# 023 — Д8,Д8 (явки 2, часы 16); 099 — ничего (архив)
ENTRIES = [
  {'дата':d(1),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'дата':d(2),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'дата':d(3),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'дата':d(4),'таб_номер':'017','статус':'Д7,2','источник':'авто'},
  {'дата':d(5),'таб_номер':'017','статус':'ОТ','источник':'авто'},
  {'дата':d(6),'таб_номер':'017','статус':'ОТ','источник':'авто'},
  {'дата':d(7),'таб_номер':'017','статус':'Б','источник':'авто'},
  {'дата':d(8),'таб_номер':'017','статус':'.','источник':'авто'},
  {'дата':d(1),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'дата':d(2),'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = []
VACATIONS = []

# Год: январь — 017 «Д»; май — 099 «Н» (архивный в годовых итогах);
# текущий месяц — те же ENTRIES
def entries_for(year, month):
    if month == M and year == Y:
        return ENTRIES
    if month == 1:
        return [{'дата':'%04d-01-05' % year,'таб_номер':'017','статус':'Д','источник':'авто'}]
    if month == 5:
        return [{'дата':'%04d-05-12' % year,'таб_номер':'099','статус':'Н','источник':'авто'}]
    return []

STATE = {'role':'Админ', 'entriesCalls':0, 'empCalls':0, 'empArchCalls':0,
         'failMonth': False}

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
        inc_arch = bool(body and body.get('includeArchived'))
        if inc_arch:
            STATE['empArchCalls'] += 1
            return {'ok':True,'data':{'employees':EMPLOYEES}}
        STATE['empCalls'] += 1
        return {'ok':True,'data':{'employees':[e for e in EMPLOYEES if not e['в_архиве']]}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        STATE['entriesCalls'] += 1
        year = int((body or {}).get('year', Y))
        month = int((body or {}).get('month', M))
        if STATE['failMonth'] and month == 3:
            return {'ok':False,'error':'net error (browser-check t321)'}
        return {'ok':True,'data':{'entries':entries_for(year, month)}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.generateMonth':
        return {'ok':True,'data':{'generated':5,'updated':2,'removed':1,
                                   'vacationDays':3,'removedShift':0,'warnings':[]}}
    if action == 'workSchedule.setManualEntry':
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t321)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t321')")
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
    check('A: страница загрузилась (тёмная тема)',
          page.evaluate("document.documentElement.getAttribute('data-theme')") == 'dark')
    check('B: график открыт, сетка отрисована (2 активных сотрудника)',
          page.evaluate("!!document.querySelector('#wsGridWrap table')") and
          page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length") == 2)

    # ---------- 1. Год: РОВНО три пункта ----------
    yr = page.evaluate("""(function(){
        var sel = document.getElementById('wsYearSel');
        var opts = sel.querySelectorAll('option');
        var vals = [];
        for (var i=0;i<opts.length;i++) vals.push(opts[i].value);
        return {n: opts.length, first: vals[0], last: vals[vals.length-1],
                sel: sel.value};
    })()""")
    check('C: год — РОВНО 3 пункта (Task 321: один до + текущий + один после)',
          yr['n'] == 3, yr)
    check('D: год — границы %d..%d' % (Y-1, Y+1),
          int(yr['first']) == Y-1 and int(yr['last']) == Y+1, yr)
    check('E: год — текущий %d выбран' % Y, int(yr['sel']) == Y, yr)
    check('F: год — пунктов ±3 (Task 320) больше нет', yr['n'] != 7, yr)

    # ---------- 2. Переименование раздела ----------
    title = page.evaluate("document.querySelector('#page-work-schedule .page-inline-header-title').textContent")
    check('G: заголовок страницы (крошки) — «Табель учёта рабочего времени»',
          'Табель учёта рабочего времени' in title, title)
    check('H: старое имя в заголовке отсутствует', 'График работы' not in title, title)
    sb = page.evaluate("document.querySelector('#sidebarWorkScheduleBtn span').textContent")
    check('I: пункт сайдбара — новое имя', 'Табель учёта рабочего времени' in sb, sb)
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(700)
    ml = page.evaluate("document.querySelector('#workScheduleMenuBtn .menu-btn-label').textContent")
    check('J: кнопка раздела на «Документация ИОС» — новое имя',
          'Табель учёта рабочего времени' in ml, ml)
    sub = page.evaluate("document.querySelector('#workScheduleMenuBtn .menu-btn-sublabel').textContent")
    check('K: субметка кнопки не изменилась',
          'Шахматка сменного и дневного персонала' in sub, sub)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1200)

    # ---------- 3. Итоги: бар под сеткой, панель скрыта ----------
    check('L: бар итогов существует и видим',
          page.evaluate("!!document.getElementById('wsTotalsBar') && !document.getElementById('wsTotalsBar').hidden"))
    check('M: панель итогов СКРЫТА по умолчанию (не мешает сетке)',
          page.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    geom0 = page.evaluate("""(function(){
        var g = document.getElementById('wsGridWrap').getBoundingClientRect();
        var b = document.getElementById('wsTotalsBar').getBoundingClientRect();
        return {gridH: g.height, gridBottom: g.bottom, barTop: b.top, barH: b.height};
    })()""")
    # Task 323: бар — ВЕРТИКАЛЬНАЯ ручка СПРАВА от сетки (высота = сетке)
    check('N: бар-ручка СПРАВА от сетки (вертикальный, во всю высоту)',
          abs(geom0['barH'] - geom0['gridH']) < 6 and geom0['barH'] > 200, geom0)

    # ---------- 4. Месяц: таблица итогов ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(500)
    check('O: панель раскрылась, вкладка «Месяц» активна',
          page.evaluate("!document.getElementById('wsTotalsPanel').hidden") and
          page.evaluate("document.getElementById('wsTtTabMonth').classList.contains('active')"))
    # Task 323: сетка ВИДИМА, сжалась по ШИРИНЕ (шторка заняла правую
    # половину), высота сохранена
    wnow = page.evaluate("(function(){ var w = document.getElementById('wsGridWrap').getBoundingClientRect(); var b = document.getElementById('wsWsBody').getBoundingClientRect(); return {w: w.width, h: w.height, bw: b.width}; })()")
    check('P: сетка сжалась по ШИРИНЕ до половины (шторка справа, Task 323)',
          wnow['w'] < wnow['bw'] * 0.55 and wnow['h'] > geom0['gridH'] * 0.9, wnow)
    month_html = page.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('Q: таблица месяца построена', 'ws-tt-table' in month_html and 'Иванов' in month_html, month_html[:200])
    row017 = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Иванов') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                var out = [];
                for (var j=1;j<tds.length;j++) out.push(tds[j].textContent);
                return out;
            }
        }
        return null;
    })()""")
    # out[0..10]: Явки, Часы, Д, Н, ОТ, У, ОВ, Б, ПР, Прочие, Всего
    # часы: Д12+Д12+Н12+Д7,2 = 43,2
    # Task 322: колонка «Переработка» (индекс 9) между ПР и Прочими;
    # переработка Иванова в этом моке 0 (кодов д/н нет)
    check('R: Иванов — явки 4, часы 43,2 (запятая), Д 3, Н 1, ОТ 2, Б 1, переработка 0, прочие 1, всего 8',
          row017 is not None and row017[:5] == ['4','43,2','3','1','2'] and
          row017[7] == '1' and row017[9] == '0' and row017[10] == '1' and row017[11] == '8',
          row017)
    total = page.evaluate("""(function(){
        var tr = document.querySelector('#wsTtBody tr.ws-tt-total');
        if (!tr) return null;
        var tds = tr.querySelectorAll('td');
        var out = [];
        for (var j=1;j<tds.length;j++) out.push(tds[j].textContent);
        return out;
    })()""")
    check('S: «Итого» — 6 явок, 59,2 ч (017 43,2 + 023 16)',
          total is not None and total[0] == '6' and total[1] == '59,2', total)
    info = page.evaluate("document.getElementById('wsTtInfo').textContent")
    check('T: инфо — месяц + норма календаря', 'раб. дн' in info and 'ч (40-час)' in info, info)

    # живое обновление: несохранённая правка меняет итоги сразу
    page.evaluate("""(function(){
        var day2 = '%s';
        WorkSchedule._PENDING[day2 + '|017'] = {'статус':'Б'};
        WorkSchedule._renderGrid();
    })()""" % d(2))
    page.wait_for_timeout(300)
    row017b = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Иванов') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                return [tds[1].textContent, tds[2].textContent, tds[8].textContent];
            }
        }
        return null;
    })()""")
    check('U: несохранённая правка — итоги обновились живьём (явки 3, часы 31,2, Б 2)',
          row017b is not None and row017b[0] == '3' and row017b[1] == '31,2' and row017b[2] == '2',
          row017b)
    info2 = page.evaluate("document.getElementById('wsTtInfo').textContent")
    check('V: инфо помечает несохранённые правки', 'несохранённые правки (1)' in info2, info2)
    page.evaluate("WorkSchedule._PENDING = {}; WorkSchedule._renderGrid();")
    page.wait_for_timeout(200)
    page.screenshot(path='task321-proof-month.png', full_page=False)

    # ---------- 5. Год: 12 месяцев, архив, «Обновить» ----------
    calls_before = STATE['entriesCalls']
    page.click('#wsTtTabYear')
    page.wait_for_timeout(900)
    check('W: вкладка «Год» активна, «Обновить» видна',
          page.evaluate("document.getElementById('wsTtTabYear').classList.contains('active')") and
          page.evaluate("!document.getElementById('wsTtRefresh').hidden"))
    check('X: загрузка года — 12 запросов listEntries',
          STATE['entriesCalls'] - calls_before == 12, STATE['entriesCalls'] - calls_before)
    year_html = page.evaluate("document.getElementById('wsTtBody').innerHTML")
    for abbr in ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']:
        if ('<th>%s</th>' % abbr) not in year_html:
            check('Y: 12 колонок месяцев (%s отсутствует)' % abbr, False, abbr)
            break
    else:
        check('Y: 12 колонок месяцев (янв..дек)', True)
    check('Z: формат «явки/часы» — 1/12 (январь Иванова)',
          '1/12' in year_html)
    check('Z2: архивный сотрудник в годовых итогах с пометкой',
          'Сидоров' in year_html and 'архив' in year_html)
    check('Z3: архивный НЕ в месячной таблице и НЕ в сетке',
          page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length") == 2)
    row099 = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Сидоров') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                return {may: tds[5].textContent, days: tds[13].textContent, hours: tds[14].textContent};
            }
        }
        return null;
    })()""")
    check('Z4: Сидоров — май 1/12, итог года 1 день / 12 часов',
          row099 is not None and row099['may'] == '1/12' and row099['days'] == '1' and row099['hours'] == '12',
          row099)
    row017y = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Иванов') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                return {days: tds[13].textContent, hours: tds[14].textContent};
            }
        }
        return null;
    })()""")
    check('Z5: Иванов — год: 5 дней / 55,2 ч (4 дн. 43,2 ч месяц + 1/12 январь)',
          row017y is not None and row017y['days'] == '5' and row017y['hours'] == '55,2',
          row017y)
    page.screenshot(path='task321-proof-year.png', full_page=False)

    # «Обновить» панели — перезагрузка года
    calls_before = STATE['entriesCalls']
    page.click('#wsTtRefresh')
    page.wait_for_timeout(900)
    check('AA: «Обновить» — ещё 12 запросов listEntries',
          STATE['entriesCalls'] - calls_before == 12, STATE['entriesCalls'] - calls_before)
    check('AB: годовая таблица перерисована после обновления',
          'ws-tt-table' in page.evaluate("document.getElementById('wsTtBody').innerHTML"))

    # неполные данные: март «падает» — предупреждение в инфо
    STATE['failMonth'] = True
    page.click('#wsTtRefresh')
    page.wait_for_timeout(900)
    info3 = page.evaluate("document.getElementById('wsTtInfo').textContent")
    check('AC: сбой месяца — предупреждение «не загружено месяцев»',
          'не загружено месяцев: 1' in info3, info3)
    STATE['failMonth'] = False

    # ---------- 6. Сворачивание: сетка возвращает высоту ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(500)
    check('AD: панель свёрнута, сетка восстановила высоту',
          page.evaluate("document.getElementById('wsTotalsPanel').hidden") and
          page.evaluate("document.getElementById('wsGridWrap').getBoundingClientRect().height") >= geom0['gridH'] - 1)
    check('AE: JS-ошибок нет', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая 1024 =================
    ctx2 = browser.new_context(viewport={'width':1024,'height':760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    check('AF: светлая тема — страница/сетка',
          page2.evaluate("document.documentElement.getAttribute('data-theme')") == 'light' and
          page2.evaluate("!!document.querySelector('#wsGridWrap table')"))
    yr2 = page2.evaluate("document.getElementById('wsYearSel').querySelectorAll('option').length")
    check('AG: светлая — год из 3 пунктов', yr2 == 3, yr2)
    page2.click('#wsTotalsBar')
    page2.wait_for_timeout(500)
    panel_bg = page2.evaluate("getComputedStyle(document.getElementById('wsTotalsPanel')).backgroundColor")
    check('AH: светлая — панель в светлых тонах (#e9e7de)',
          panel_bg == 'rgb(233, 231, 222)', panel_bg)
    check('AI: светлая — таблица месяца построена',
          'ws-tt-table' in page2.evaluate("document.getElementById('wsTtBody').innerHTML"))
    page2.screenshot(path='task321-proof-light.png', full_page=False)
    check('AJ: светлая — JS-ошибок нет', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375, touch =================
    ctx3 = browser.new_context(viewport={'width':375,'height':720}, has_touch=True,
                               is_mobile=True, device_scale_factor=2)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3)
    check('AK: мобильный — сетка отрисована',
          page3.evaluate("!!document.querySelector('#wsGridWrap table')"))
    bar_h = page3.evaluate("document.getElementById('wsTotalsBar').getBoundingClientRect().height")
    check('AL: мобильный — тап-зона бара ≥ 40px', bar_h >= 40, bar_h)
    page3.tap('#wsTotalsBar')
    page3.wait_for_timeout(500)
    check('AM: мобильный — тап раскрыл панель',
          not page3.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    check('AN: мобильный — скролл-контейнер сам #wsTtBody (Task 323)',
          page3.evaluate("(function(){ var b = document.getElementById('wsTtBody'); return getComputedStyle(b).overflow === 'auto' && !document.querySelector('#wsTtBody .ws-tt-scroll'); })()"))
    page3.screenshot(path='task321-proof-mobile.png', full_page=False)
    check('AO: мобильный — JS-ошибок нет', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

failed = [r for r in results if not r[1]]
print()
print('=' * 60)
print('ИТОГО: %d проверок, провалов: %d' % (len(results), len(failed)))
for name, ok, extra in failed:
    print('  FAIL: %s | %s' % (name, extra))
import sys
sys.exit(1 if failed else 0)
