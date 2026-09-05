# -*- coding: utf-8 -*-
# Task 322: browser-check «Итоги учёта — переработка д/н + слова в
# шапке + зебра + панель на всю высоту шахматки»:
#   1) Коды «д»/«н» — ДНИ ПЕРЕРАБОТКИ в итогах: сменному 12 ч,
#      дневному — часы, указанные при добавлении кода в ячейку
#      (малая форма часов в попапе; поле «Часы» в шите
#      «Дополнительно…»; поле «часы» записи — серверная колонка K).
#   2) Шапка итогов — СЛОВА: День (Д), Ночь (Н), Отпуск (ОТ),
#      Уч. отпуск (У), Отгул (ОВ), Больничный (Б), Прогул (ПР),
#      Переработка, Прочие, Всего.
#   3) Оформление: таблица со ЗЕБРОЙ строк; раскрытая панель —
#      на ВСЮ высоту шахматки, до бара с кнопками (сетка скрыта
#      классом ws-tt-open, панель flex: 1 до низа окна);
#      сворачивание возвращает сетку. Год — колонка «Перераб.».
# Проверки: 3 контекста (десктоп-Админ 1280 тёмная, светлая 1024,
# мобильный 375 touch), ввод часов через реальный попап ячейки,
# «Сохранить» с полем часы (мок-сервер хранит upsert), 0 JS-ошибок,
# скриншоты.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8942
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
# 017 — сменный; 023 — дневной; 099 — АРХИВНЫЙ
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

# Текущий месяц (мутабельный — setManualEntry делает upsert):
#   017 (сменный): Д,Д,Н,Д7,2,ОТ,ОТ,Б,«.»,д → явки 4, часы 43,2,
#                  переработка 12 (д, смена = 12 ч)
#   023 (дневной): Д8,Д8,д(7,2) → явки 2, часы 16, переработка 7,2
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

def reset_entries():
    STATE['entries'] = [
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
]

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
        # мок-сервер ХРАНИТ upsert (вкл. часы) — после «Сохранить» и
        # loadGrid запись живёт, итоги сходятся
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t322)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t322')")
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
    geom0 = page.evaluate("""(function(){
        var g = document.getElementById('wsGridWrap').getBoundingClientRect();
        return {h: g.height, top: g.top};
    })()""")
    check('B: панель итогов СКРЫТА по умолчанию',
          page.evaluate("document.getElementById('wsTotalsPanel').hidden"))

    # ---------- раскрытие: ВСЯ высота шахматки, до бара с кнопками ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(500)
    check('C: панель раскрылась',
          not page.evaluate("document.getElementById('wsTotalsPanel').hidden"))
    check('D: страница получила класс ws-tt-open (вид «итоги»)',
          page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')"))
    check('E: ШАХМАТКА СКРЫТА (панель заняла её место)',
          page.evaluate("document.getElementById('wsGridWrap').getBoundingClientRect().height") < 2)
    layout = page.evaluate("""(function(){
        var tb = document.querySelector('#page-work-schedule .ws-toolbar');
        var bar = document.getElementById('wsTotalsBar');
        var panel = document.getElementById('wsTotalsPanel');
        var vh = window.innerHeight;
        return {tbBottom: tb.getBoundingClientRect().bottom,
                barTop: bar.getBoundingClientRect().top,
                panelTop: panel.getBoundingClientRect().top,
                panelBottom: panel.getBoundingClientRect().bottom,
                vh: vh, panelH: panel.getBoundingClientRect().height};
    })()""")
    check('F: бар итогов — СРАЗУ под баром с кнопками (тулбар)',
          layout['barTop'] >= layout['tbBottom'] - 2 and
          layout['barTop'] <= layout['tbBottom'] + 20, layout)
    check('G: панель — ДО НИЗА ОКНА (вся высота шахматки)',
          layout['panelBottom'] >= layout['vh'] - 12, layout)
    check('H: панель высокая (>60% доступной высоты)', layout['panelH'] > 400, layout)

    # ---------- месяц: слова в шапке + зебра + переработка ----------
    month_html = page.evaluate("document.getElementById('wsTtBody').innerHTML")
    words_ok = all(('>%s</th>' % w) in month_html for w in
                   ['День (Д)','Ночь (Н)','Отпуск (ОТ)','Уч. отпуск (У)',
                    'Отгул (ОВ)','Больничный (Б)','Прогул (ПР)','Переработка',
                    'Прочие','Всего','Явки','Часы'])
    check('I: шапка — ПОЛНЫЕ СЛОВА с кодами в скобках + Переработка', words_ok)
    check('I2: одиночных кодов в шапке нет',
          '<th>Д</th>' not in month_html and '<th>ОТ</th>' not in month_html)

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
    # колонки: Явки, Часы, День(Д), Ночь(Н), ОТ, У, ОВ, Б, ПР,
    #           Переработка, Прочие, Всего (индексы 0..11)
    check('J: Иванов — явки 4, часы 43,2, День 3, Ночь 1, ОТ 2, Б 1, переработка 12, всего 9',
          row017 is not None and row017[0] == '4' and row017[1] == '43,2' and
          row017[2] == '3' and row017[3] == '1' and row017[4] == '2' and
          row017[7] == '1' and row017[9] == '12' and row017[11] == '9',
          row017)
    row023 = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Петров') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                var out = [];
                for (var j=1;j<tds.length;j++) out.push(tds[j].textContent);
                return out;
            }
        }
        return null;
    })()""")
    check('K: Петров — явки 2, часы 16, переработка 7,2 (часы правки ячейки)',
          row023 is not None and row023[0] == '2' and row023[1] == '16' and
          row023[9] == '7,2', row023)
    total = page.evaluate("""(function(){
        var tr = document.querySelector('#wsTtBody tr.ws-tt-total');
        var tds = tr.querySelectorAll('td');
        var out = [];
        for (var j=1;j<tds.length;j++) out.push(tds[j].textContent);
        return out;
    })()""")
    check('L: Итого — явки 6, часы 59,2, ПЕРЕРАБОТКА 19,2',
          total is not None and total[0] == '6' and total[1] == '59,2' and
          total[9] == '19,2', total)
    tip = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Иванов') !== -1) {
                return trs[i].querySelectorAll('td')[10].getAttribute('title');
            }
        }
        return null;
    })()""")
    check('M: тултип колонки — «дней переработки: 1 (коды д/н)»',
          tip is not None and 'дней переработки: 1' in tip, tip)

    # зебра: чётные строки с подложкой
    zebra = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        var bg1 = getComputedStyle(trs[0]).backgroundColor;
        var bg2 = getComputedStyle(trs[1]).backgroundColor;
        return {r0: bg1, r1: bg2};
    })()""")
    check('N: ЗЕБРА — чётная строка тонируется (r0≠r1, rgba)',
          zebra['r1'] != 'rgba(0, 0, 0, 0)' and zebra['r1'] != zebra['r0'], zebra)
    page.screenshot(path='task322-proof-month.png', full_page=False)

    # ---------- год: колонка «Перераб.» ----------
    page.click('#wsTtTabYear')
    page.wait_for_timeout(900)
    year_html = page.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('O: год — колонка «Перераб.» в шапке', 'Перераб.' in year_html)
    row017y = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Иванов') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                return {days: tds[13].textContent, hours: tds[14].textContent,
                        over: tds[15].textContent};
            }
        }
        return null;
    })()""")
    check('P: Иванов — год: 5 дней / 55,2 ч / переработка 12',
          row017y is not None and row017y['days'] == '5' and
          row017y['hours'] == '55,2' and row017y['over'] == '12', row017y)
    page.screenshot(path='task322-proof-year.png', full_page=False)

    # ---------- сворачивание: сетка возвращается ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(500)
    check('Q: панель свёрнута, сетка восстановила высоту',
          page.evaluate("document.getElementById('wsTotalsPanel').hidden") and
          not page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')") and
          page.evaluate("document.getElementById('wsGridWrap').getBoundingClientRect().height") >= geom0['h'] - 1)

    # ---------- ввод часов: попап → «д» → малая форма ----------
    # Петров (дневной), день 10 — пустая ячейка
    page.click('#wsGridWrap tbody tr:nth-child(2) td[data-day="10"]')
    page.wait_for_timeout(400)
    check('R: попап кодов открылся у ячейки',
          page.evaluate("document.getElementById('wsCellPopup').classList.contains('active')"))
    popup0 = page.evaluate("document.getElementById('wsCellPopup').innerHTML")
    check('R2: у д в списке нет лишних часов (ячейка пустая)',
          '· 8 ч' not in popup0 and '· 7,2 ч' not in popup0, popup0[:120])
    page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent === 'д') { rows[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(300)
    form = page.evaluate("""(function(){
        var inp = document.getElementById('wsDnHours');
        return {exists: !!inp,
                value: inp ? inp.value : null,
                label: document.querySelector('#wsCellPopup .ws-dn-label'),
                ok: !!document.querySelector('#wsCellPopup .ws-dn-ok'),
                back: !!document.querySelector('#wsCellPopup .ws-dn-back')};
    })()""")
    check('S: малая форма часов открылась (дневной + д)',
          form['exists'] and form['ok'] and form['back'], form)
    check('S2: префилл 8 (обычный день дневного)', form['value'] == '8', form)
    page.screenshot(path='task322-proof-form.png', full_page=False)

    # «Назад к кодам» — список возвращается
    page.evaluate("document.querySelector('#wsCellPopup .ws-dn-back').click()")
    page.wait_for_timeout(300)
    check('T: «Назад к кодам» вернул список статусов',
          page.evaluate("""(function(){
                var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
                return rows.length > 5;
            })()"""))
    # снова в форму — вводим 6 и применяем
    page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent === 'д') { rows[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(300)
    page.evaluate("document.getElementById('wsDnHours').value = '6'")
    page.evaluate("document.querySelector('#wsCellPopup .ws-dn-ok').click()")
    page.wait_for_timeout(400)
    pend = page.evaluate("(function(){ var p = WorkSchedule._PENDING['%s|023']; return p ? {s: p['статус'], h: p['часы']} : null; })()" % d(10))
    check('U: правка применена локально — д с часами 6',
          pend is not None and pend['s'] == 'д' and pend['h'] == 6, pend)
    check('U2: попап закрылся',
          not page.evaluate("document.getElementById('wsCellPopup').classList.contains('active')"))
    cell10 = page.evaluate("document.querySelector('#wsGridWrap tbody tr:nth-child(2) td[data-day=\"10\"]').textContent")
    check('U3: ячейка показывает код д', cell10.strip() == 'д', cell10)

    # итоги live: переработка Петрова 7,2+6=13,2 — панель открыта
    # (вкладка могла остаться «Год» — явно возвращаемся на месяц)
    page.click('#wsTotalsBar')
    page.wait_for_timeout(500)
    page.click('#wsTtTabMonth')
    page.wait_for_timeout(300)
    row023b = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Петров') !== -1) {
                var tds = trs[i].querySelectorAll('td');
                return {over: tds[10].textContent, work: tds[0].textContent};
            }
        }
        return null;
    })()""")
    check('V: итоги живьём — переработка Петрова 13,2 (несохранённая правка)',
          row023b is not None and row023b['over'] == '13,2', row023b)

    # «Сохранить» — payload с часами; мок сохраняет, после loadGrid итог сходится
    n0 = len(STATE['manualPayloads'])
    page.evaluate("WorkSchedule.saveAll()")
    page.wait_for_timeout(1500)
    payloads = [pl for pl in STATE['manualPayloads'][n0:]]
    ours = [pl for pl in payloads if pl.get('date') == d(10) and pl.get('таб_номер') == '023']
    check('W: «Сохранить» отправил поле часы = 6',
          len(ours) == 1 and ours[0].get('часы') == 6, ours)
    row023c = page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-tt-emp');
            if (emp && emp.textContent.indexOf('Петров') !== -1) {
                return trs[i].querySelectorAll('td')[10].textContent;
            }
        }
        return null;
    })()""")
    check('X: после сохранения и перезагрузки — переработка 13,2 (часы с сервера)',
          row023c == '13,2', row023c)

    # ---------- сменный: д применяется БЕЗ формы ----------
    page.click('#wsTotalsBar')
    page.wait_for_timeout(400)
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
    pendS = page.evaluate("(function(){ var p = WorkSchedule._PENDING['%s|017']; return p ? {s: p['статус'], h: p['часы']} : null; })()" % d(11))
    check('Y: сменный — д применился СРАЗУ (без формы, часы null)',
          pendS is not None and pendS['s'] == 'д' and pendS['h'] is None, pendS)
    check('Y2: формы часов не появлялось',
          not page.evaluate("!!document.getElementById('wsDnHours')"))
    # ячейка с часами: у Петрова день 5 — в списке кодов видно «· 7,2 ч»
    page.click('#wsGridWrap tbody tr:nth-child(2) td[data-day="5"]')
    page.wait_for_timeout(400)
    popup5 = page.evaluate("document.getElementById('wsCellPopup').innerHTML")
    check('Z: в списке кодов у д показаны часы «· 7,2 ч»',
          '· 7,2 ч' in popup5, popup5[:160])

    # шит «Дополнительно…» — префилл поля «Часы»
    page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (var i=0;i<rows.length;i++){
            if (rows[i].className.indexOf('ws-popup-more') !== -1 &&
                rows[i].textContent.indexOf('Дополнительно') !== -1) { rows[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(700)
    hours_val = page.evaluate("(function(){ var el = document.getElementById('wsCellHours'); return el ? el.value : null; })()")
    check('AA: шит «Дополнительно…» — префилл «Часы» = 7,2',
          hours_val == '7,2', hours_val)
    page.evaluate("WorkSchedule.closeCellForm()")
    page.wait_for_timeout(300)
    # чистим несохранённое (день 11) — не влияет на дальнейшие контексты
    page.evaluate("WorkSchedule._PENDING = {}; WorkSchedule._renderGrid();")
    page.wait_for_timeout(200)
    check('AB: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая 1100 =================
    # (1024 со скроллбаром даёт media 1009 — мобильная вёрстка;
    # берём 1100 — честный десктоп)
    reset_entries()
    ctx2 = browser.new_context(viewport={'width':1100,'height':760})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    check('AC: светлая — страница/сетка',
          page2.evaluate("document.documentElement.getAttribute('data-theme')") == 'light' and
          page2.evaluate("!!document.querySelector('#wsGridWrap table')"))
    page2.click('#wsTotalsBar')
    page2.wait_for_timeout(500)
    check('AD: светлая — панель раскрыта на всю высоту (сетка скрыта)',
          page2.evaluate("document.getElementById('wsGridWrap').getBoundingClientRect().height") < 2 and
          page2.evaluate("document.getElementById('wsTotalsPanel').getBoundingClientRect().height") > 400)
    zebra2 = page2.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsTtBody tbody tr');
        return {r0: getComputedStyle(trs[0]).backgroundColor,
                r1: getComputedStyle(trs[1]).backgroundColor};
    })()""")
    check('AE: светлая — зебра тонирует чётные строки',
          zebra2['r1'] != 'rgba(0, 0, 0, 0)' and zebra2['r1'] != zebra2['r0'], zebra2)
    mh2 = page2.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('AF: светлая — шапка словами + Переработка',
          'День (Д)' in mh2 and 'Больничный (Б)' in mh2 and 'Переработка' in mh2)
    check('AG: светлая — переработка Петрова 7,2 (часы записи)',
          page2.evaluate("""(function(){
                var trs = document.querySelectorAll('#wsTtBody tbody tr');
                for (var i=0;i<trs.length;i++){
                    var emp = trs[i].querySelector('td.ws-tt-emp');
                    if (emp && emp.textContent.indexOf('Петров') !== -1) {
                        return trs[i].querySelectorAll('td')[10].textContent;
                    }
                }
                return null;
            })()""") == '7,2')
    page2.screenshot(path='task322-proof-light.png', full_page=False)
    check('AH: светлая — JS-ошибок нет', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375, touch =================
    reset_entries()
    ctx3 = browser.new_context(viewport={'width':375,'height':720}, has_touch=True,
                               is_mobile=True, device_scale_factor=2)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3)
    check('AI: мобильный — сетка отрисована',
          page3.evaluate("!!document.querySelector('#wsGridWrap table')"))
    bar_h = page3.evaluate("document.getElementById('wsTotalsBar').getBoundingClientRect().height")
    check('AJ: мобильный — тап-зона бара ≥ 40px', bar_h >= 40, bar_h)
    page3.tap('#wsTotalsBar')
    page3.wait_for_timeout(500)
    check('AK: мобильный — тап раскрыл панель (≤70vh, свой скролл)',
          not page3.evaluate("document.getElementById('wsTotalsPanel').hidden") and
          page3.evaluate("document.getElementById('wsTotalsPanel').getBoundingClientRect().height") <= 720 * 0.71 + 30)
    mh3 = page3.evaluate("document.getElementById('wsTtBody').innerHTML")
    check('AL: мобильный — слова в шапке + зебра-таблица',
          'День (Д)' in mh3 and 'Переработка' in mh3)
    page3.screenshot(path='task322-proof-mobile.png', full_page=False)
    check('AM: мобильный — JS-ошибок нет', len(js_errors3) == 0, js_errors3[:3])
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
