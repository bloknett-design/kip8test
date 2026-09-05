# -*- coding: utf-8 -*-
# Task 318: browser-check «График работы» — карточка/форма сотрудника:
#   • hover поля «Сотрудник +» — СПЛОШНОЙ цвет (как ячейки ФИО),
#     НЕ прозрачный (sticky-заголовок больше не «просвечивает»);
#   • «Должность» в шторке нового сотрудника — ВЫПАДАЮЩИЙ список
#     из таблицы «Сотрудники» (listEmployees includeArchived:
#     активные + архив, уникальные, по алфавиту);
#   • карточка: строка «Режим работы» (было «Тип»), строка
#     «Уволить…» (красная, редакторам) → шторка увольнения
#     (карточка закрывается — z 9401 > 201);
#   • увольнение: kipConfirm (danger) → dismissEmployee
#     {таб_номер, дата_увольнения} → сетка перегружена, строка
#     ушла из шахматки (в мок-таблице в_архиве=1 — «архив»).
# Контексты: десктоп 1280 Админ / светлая тема / зритель «ИТР8 pro»
# (без «Уволить…», заголовок не кликается) / мобильный 375 (тап).
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

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'}
]

def make_employees():
    # активные: 017 (Слесарь), 023 (Электрик — вторая должность),
    # 30+i (Слесарь — дубликат должности);
    # АРХИВ (в_архиве=1): 098 Мастер КИПиА, 099 Инженер КИПиА —
    # их должности должны попасть в select «Должность»
    return [
      {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
      {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Электрик','комментарий':''}
    ] + [
      {'таб_номер':'%03d' % (30 + i),'ФИО':'Сотрудник %02d Тестовый' % (i + 1),'тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
      for i in range(10)
    ] + [
      {'таб_номер':'099','ФИО':'Сидоров Сидор Сидорович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-01-05','дата_приёма':'2020-02-01','дата_увольнения':'2026-06-30','в_архиве':1,'должность':'Инженер КИПиА','комментарий':'уволен ранее'},
      {'таб_номер':'098','ФИО':'Кузнецов Кузьма Кузьмич','тип':'сменный','смена':2,'шаблон_ротации':1,'старт_цикла':'2026-01-05','дата_приёма':'2019-04-11','дата_увольнения':'2025-12-31','в_архиве':1,'должность':'Мастер КИПиА','комментарий':''}
    ]

# МУТИРУЕМЫЙ стенд: dismissEmployee ставит в_архиве=1 + дату
EMPLOYEES = make_employees()
API_CALLS = []       # журнал вызовов dismissEmployee / listEmployees
LIST_BODIES = []     # тела запросов listEmployees (includeArchived)

PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Целевой инструктаж','дата_начала':'%04d-%02d-10' % (Y, M),'дата_окончания':'%04d-%02d-10' % (Y, M),'длительность_дней':1},
  {'id':102,'таб_номер':'023','тип':'обучение','тема':'Охрана труда','дата_начала':'%04d-%02d-12' % (Y, M),'дата_окончания':'%04d-%02d-15' % (Y, M),'длительность_дней':4}
]
VACATIONS = []

STATE = {'role': 'Админ'}

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
        LIST_BODIES.append(body)
        include_archived = bool(body and body.get('includeArchived'))
        emps = [e for e in EMPLOYEES if include_archived or not e['в_архиве']]
        return {'ok':True,'data':{'employees':emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.dismissEmployee':
        API_CALLS.append(body)
        tab = str((body or {}).get('таб_номер', ''))
        for e in EMPLOYEES:
            if str(e['таб_номер']) == tab:
                e['в_архиве'] = 1
                e['дата_увольнения'] = str((body or {}).get('дата_увольнения', ''))
                return {'ok':True,'data':{'таб_номер':tab,'в_архиве':1}}
        return {'ok':False,'error':'not_found_таб_номер'}
    if action == 'workSchedule.setManualEntry':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.deleteEntry':
        return {'ok':True,'data':{'ok':True}}
    return {'ok':False,'error':'unknown action ' + str(action)}

def approx(a, b, eps):
    return a is not None and b is not None and abs(a - b) <= eps

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t318)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t318')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    check('A2: тёмная тема применена (app-theme=dark)',
          page.evaluate("document.documentElement.getAttribute('data-theme')==='dark'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована',
          page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- hover «Сотрудник +»: СПЛОШНОЙ цвет ----------
    head_js = """(function(){
        var th = document.querySelector('th.ws-emp-col.ws-emp-head-add');
        if (!th) return null;
        return { bg: getComputedStyle(th).backgroundColor,
                 color: getComputedStyle(th).color,
                 clickable: getComputedStyle(th).cursor };
    })()"""
    h0 = page.evaluate(head_js)
    check('C: заголовок «Сотрудник +» есть (клик-кнопка, курсор-палец)',
          h0 is not None and h0['clickable'] == 'pointer', h0)
    check('C2: фон ДО наведения — база шапки #0e1621',
          h0 and h0['bg'] == 'rgb(14, 22, 33)', h0 and h0['bg'])

    page.hover('th.ws-emp-head-add')
    page.wait_for_timeout(250)
    h1 = page.evaluate(head_js)
    check('D: hover — фон СПЛОШНОЙ #15202f (как ячейки ФИО под ней)',
          h1 and h1['bg'] == 'rgb(21, 32, 47)', h1 and h1['bg'])
    check('D2: фон НЕ прозрачный (rgb без альфы, не rgba)',
          h1 and h1['bg'].startswith('rgb(') and not h1['bg'].startswith('rgba'), h1 and h1['bg'])
    page.screenshot(path='scripts/task318-proof-hover.png', full_page=False)

    # уход курсора — фон возвращается
    page.mouse.move(640, 300)
    page.wait_for_timeout(250)
    h2 = page.evaluate(head_js)
    check('D3: уход курсора — фон вернулся к базе (цвет меняется только при hover)',
          h2 and h2['bg'] == 'rgb(14, 22, 33)', h2 and h2['bg'])

    # ---------- светлая тема ----------
    page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(200)
    page.hover('th.ws-emp-head-add')
    page.wait_for_timeout(250)
    hl = page.evaluate(head_js)
    check('E: светлая — hover СПЛОШНОЙ #e2e8ef',
          hl and hl['bg'] == 'rgb(226, 232, 239)', hl and hl['bg'])
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    page.wait_for_timeout(200)

    # ---------- шторка нового сотрудника: «Должность» — select ----------
    page.click('th.ws-emp-head-add')
    page.wait_for_timeout(700)
    pos = page.evaluate("""(function(){
        var sel = document.getElementById('wsEmpPosition');
        if (!sel) return null;
        var opts = [];
        for (var i=0;i<sel.options.length;i++) opts.push(sel.options[i].text);
        return { tag: sel.tagName, opts: opts, val: sel.value,
                 sheet: document.getElementById('wsEmpSheet').classList.contains('active') };
    })()""")
    check('F: шторка «Новый сотрудник» открылась кликом по заголовку',
          pos and pos['sheet'])
    check('F2: «Должность» — SELECT (не input)',
          pos and pos['tag'] == 'SELECT', pos and pos['tag'])
    # активные: Слесарь КИПиА, Электрик; архив: Инженер КИПиА, Мастер КИПиА
    expected = ['— выберите —', 'Инженер КИПиА', 'Мастер КИПиА', 'Слесарь КИПиА', 'Электрик']
    check('F3: варианты — ВСЯ таблица «Сотрудники» (активные+архив), уникальные, по алфавиту',
          pos and pos['opts'] == expected, pos and pos['opts'])
    check('F4: по умолчанию ничего не выбрано («— выберите —»)',
          pos and pos['val'] == '')
    # запрос к листу был с includeArchived
    inc = [b for b in LIST_BODIES if b and b.get('includeArchived')]
    check('F5: список запрошен с includeArchived (лист — источник вариантов)',
          len(inc) >= 1, [b for b in LIST_BODIES])
    page.screenshot(path='scripts/task318-proof-position-select.png', full_page=False)
    page.evaluate("WorkSchedule.closeEmployeeForm()")
    page.wait_for_timeout(300)

    # ---------- карточка: «Режим работы» + «Уволить…» ----------
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    card = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        var dis = pp ? pp.querySelector('.ws-emp-dismiss') : null;
        var k = null;
        if (dis) { var cs = getComputedStyle(dis); k = { color: cs.color, cursor: cs.cursor }; }
        // подпись строки профиля (не «Тип»)
        var ks = pp ? pp.querySelectorAll('.ws-emp-k') : [];
        var labels = [];
        for (var i=0;i<ks.length;i++) labels.push(ks[i].textContent.trim());
        var iVac = txt.indexOf('Отпуска · ');
        var iDis = txt.indexOf('Уволить…');
        return { open: pp ? pp.classList.contains('active') : false,
                 labels: labels, hasType: labels.indexOf('Тип') !== -1,
                 dis: !!dis, disCls: dis ? dis.className : '',
                 disStyle: k, iVac: iVac, iDis: iDis };
    })()""")
    check('G: карточка открылась; строка называется «Режим работы» (не «Тип»)',
          card['open'] and 'Режим работы' in card['labels'] and not card['hasType'],
          card['labels'])
    check('G2: «Режим работы» показывает тип со сменой',
          page.evaluate("(function(){ var pp=document.getElementById('wsEmpPopup'); return pp.textContent.indexOf('сменный, смена №1')!==-1; })()"))
    check('G3: строка «Уволить…» — в профиле, ДО блока отпусков',
          card['dis'] and card['iDis'] != -1 and card['iVac'] != -1 and card['iDis'] < card['iVac'],
          (card['dis'], card['iDis'], card['iVac']))
    check('G4: «Уволить…» — красная строка-действие (ws-emp-dismiss)',
          'ws-popup-row' in card['disCls'] and 'ws-popup-more' in card['disCls'] and
          'ws-emp-dismiss' in card['disCls'] and card['disStyle']['color'] == 'rgb(239, 83, 80)',
          (card['disCls'], card['disStyle']))
    page.screenshot(path='scripts/task318-proof-card.png', full_page=False)

    # ---------- «Уволить…»: шторка (карточка закрыта — z 9401 > 201) ----------
    page.click('#wsEmpPopup .ws-emp-dismiss')
    page.wait_for_timeout(700)
    dis1 = page.evaluate("""(function(){
        var sh = document.getElementById('wsDismissSheet');
        var ov = document.getElementById('wsDismissOverlay');
        var pp = document.getElementById('wsEmpPopup');
        var emp = document.getElementById('wsDismissEmp');
        var dt = document.getElementById('wsDismissDate');
        var info = document.querySelector('#wsDismissSheet .ws-dismiss-info');
        var btn = document.querySelector('#wsDismissSheet .ws-dismiss-submit');
        var cs = btn ? getComputedStyle(btn) : null;
        return { sheet: sh ? sh.classList.contains('active') : false,
                 overlay: ov ? ov.classList.contains('active') : false,
                 cardClosed: pp ? !pp.classList.contains('active') : true,
                 emp: emp ? emp.textContent : '',
                 date: dt ? dt.value : null,
                 info: info ? info.textContent : '',
                 btnBg: cs ? cs.backgroundColor : null,
                 title: (document.querySelector('#wsDismissSheet .flow-input-sheet-title')||{}).textContent || '' };
    })()""")
    check('H: «Уволить…» — карточка закрылась, шторка увольнения открылась',
          dis1['sheet'] and dis1['overlay'] and dis1['cardClosed'])
    check('H2: ФИО · таб. № в шторке (контекст сохранён)',
          dis1['emp'] == 'Иванов Иван Иванович · таб. №017', dis1['emp'])
    check('H3: дата увольнения — сегодня по умолчанию',
          dis1['date'] == TODAY_ISO, dis1['date'])
    check('H4: пояснение — строка остаётся в архиве справочника',
          dis1['info'].find('архиве') != -1 and dis1['title'] == 'Увольнение сотрудника',
          (dis1['title'], dis1['info']))
    check('H5: кнопка «Уволить» — красная (#e53935)',
          dis1['btnBg'] == 'rgb(229, 57, 53)', dis1['btnBg'])
    page.screenshot(path='scripts/task318-proof-dismiss-sheet.png', full_page=False)

    # ---------- отмена подтверждения: сотрудник на месте ----------
    page.click('#wsDismissSheet .ws-dismiss-submit')
    page.wait_for_timeout(400)
    dlg = page.evaluate("""(function(){
        var ov = document.getElementById('kipDialogOverlay');
        if (!ov || !ov.classList.contains('active')) return null;
        var ok = ov.querySelector('.kip-dialog-ok');
        var cancel = ov.querySelector('.kip-dialog-cancel');
        return { msg: (ov.querySelector('.kip-dialog-msg')||{}).textContent || '',
                 danger: ok ? ok.className.indexOf('danger') !== -1 : false,
                 okTxt: ok ? ok.textContent : '', cancelTxt: cancel ? cancel.textContent : '' };
    })()""")
    check('I: подтверждение kipConfirm — «Уволить Иванова…», danger, архив',
          dlg is not None and 'Уволить Иванов Иван Иванович?' in dlg['msg'] and
          dlg['danger'] and 'архиве' in dlg['msg'], dlg)
    # Отмена — сотрудник остаётся, сервер не звался
    page.click('#kipDialogOverlay .kip-dialog-cancel')
    page.wait_for_timeout(500)
    n_calls_cancel = len([c for c in API_CALLS if c and c.get('таб_номер') == '017'])
    still = page.evaluate("!!document.querySelector('td.ws-emp-col[data-tab=\\'017\\']')")
    check('I2: отмена подтверждения — API не зовётся, строка в шахматке',
          n_calls_cancel == 0 and still, (n_calls_cancel, still))
    check('I3: шторка осталась открытой (можно передумать дату)',
          page.evaluate("document.getElementById('wsDismissSheet').classList.contains('active')"))
    # «Отмена» шторки
    page.evaluate("WorkSchedule.closeDismissForm()")
    page.wait_for_timeout(300)
    check('I4: «Отмена» шторки — закрыта',
          not page.evaluate("document.getElementById('wsDismissSheet').classList.contains('active')"))

    # ---------- увольнение по-настоящему ----------
    rows_before = page.evaluate("document.querySelectorAll('#wsGridWrap td.ws-emp-col').length")
    page.evaluate("window.__toasts = []; var orig = KipToast.show; KipToast.show = function(m){ window.__toasts.push(String(m)); return orig.apply(this, arguments); };")
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-dismiss')
    page.wait_for_timeout(600)
    page.fill('#wsDismissDate', '2026-09-05')
    page.click('#wsDismissSheet .ws-dismiss-submit')
    page.wait_for_timeout(400)
    page.click('#kipDialogOverlay .kip-dialog-ok')
    page.wait_for_timeout(2500)

    api017 = [c for c in API_CALLS if c and c.get('таб_номер') == '017']
    check('J: API dismissEmployee вызван с датой 05.09.2026',
          len(api017) == 1 and api017[0].get('дата_увольнения') == '2026-09-05', api017)
    check('J2: шторка и карточка закрыты',
          not page.evaluate("document.getElementById('wsDismissSheet').classList.contains('active')") and
          not page.evaluate("document.getElementById('wsEmpPopup').classList.contains('active')"))
    toasts = page.evaluate("window.__toasts || []")
    check('J3: тост «Сотрудник уволен и убран из графика»',
          any('уволен' in t for t in toasts), toasts)
    row_gone = page.evaluate("!!document.querySelector('td.ws-emp-col[data-tab=\\'017\\']')")
    rows_after = page.evaluate("document.querySelectorAll('#wsGridWrap td.ws-emp-col').length")
    check('J4: строка Иванова УШЛА из шахматки (уволен → архив листа)',
          not row_gone and rows_after == rows_before - 1,
          (row_gone, rows_before, rows_after))
    check('J5: прочие сотрудники на месте (Петров 023)',
          page.evaluate("!!document.querySelector('td.ws-emp-col[data-tab=\\'023\\']')"))
    # мок-таблица: 017 в архиве с датой
    e017 = [e for e in EMPLOYEES if e['таб_номер'] == '017'][0]
    check('J6: в таблице «Сотрудники» строка ОСТАЛАСЬ (в_архиве=1, дата записана)',
          e017['в_архиве'] == 1 and e017['дата_увольнения'] == '2026-09-05', e017)
    page.screenshot(path='scripts/task318-proof-dismissed.png', full_page=False)

    # после увольнения select «Должность» всё ещё знает его должность (архив)
    LIST_BODIES.clear()
    page.click('th.ws-emp-head-add')
    page.wait_for_timeout(800)
    pos2 = page.evaluate("(function(){ var s=document.getElementById('wsEmpPosition'); var o=[]; for (var i=0;i<s.options.length;i++) o.push(s.options[i].text); return o; })()")
    check('K: после увольнения варианты списка НЕ поте­ряли его должность (архив жив)',
          pos2 == expected, pos2)
    page.evaluate("WorkSchedule.closeEmployeeForm()")
    page.wait_for_timeout(300)

    check('L: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: зритель (ИТР8 pro) =================
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
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx2.route('**/exec?**', handle2)
    ctx2.route('**script.google.com/**', handle2)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t318-v')")
    page2.evaluate("localStorage.setItem('app-theme','dark')")
    page2.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)

    head2 = page2.evaluate("""(function(){
        var th = document.querySelector('th.ws-emp-col');
        return { add: th ? th.className.indexOf('ws-emp-head-add') !== -1 : null,
                 cursor: th ? getComputedStyle(th).cursor : null,
                 bg: th ? getComputedStyle(th).backgroundColor : null };
    })()""")
    check('M: зритель — заголовок «Сотрудник» БЕЗ кнопки (не кликается)',
          head2['add'] is False and head2['cursor'] != 'pointer', head2)
    page2.click('th.ws-emp-col')
    page2.wait_for_timeout(500)
    check('M2: зритель — клик по заголовку шторку НЕ открывает',
          not page2.evaluate("document.getElementById('wsEmpSheet').classList.contains('active')"))

    page2.click('td.ws-emp-col[data-tab="023"]')
    page2.wait_for_timeout(600)
    card2 = page2.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        var ks = pp ? pp.querySelectorAll('.ws-emp-k') : [];
        var labels = [];
        for (var i=0;i<ks.length;i++) labels.push(ks[i].textContent.trim());
        return { open: pp ? pp.classList.contains('active') : false,
                 labels: labels,
                 dis: !!pp.querySelector('.ws-emp-dismiss'),
                 vac: !!pp.querySelector('.ws-emp-addvac') };
    })()""")
    check('N: зритель — карточка открылась, «Режим работы» виден',
          card2['open'] and 'Режим работы' in card2['labels'], card2['labels'])
    check('N2: зритель — строки «Уволить…» НЕТ (только редакторам)',
          not card2['dis'])
    check('N3: зритель — «+ Отпуск…» тоже нет (право записи)',
          not card2['vac'])
    page2.evaluate("WorkSchedule.closeEmpPopup()")
    page2.wait_for_timeout(300)
    check('N4: JS-ошибок нет (зритель)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    STATE['role'] = 'Админ'

    # ================= Контекст 3: мобильный 375px (touch) =================
    ctx3 = browser.new_context(viewport={'width':375,'height':812}, has_touch=True)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    def handle3(route, request):
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
    ctx3.route('**/exec?**', handle3)
    ctx3.route('**script.google.com/**', handle3)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.evaluate("localStorage.setItem('kip8_session_token','browser-check-t318-m')")
    page3.evaluate("localStorage.setItem('app-theme','dark')")
    page3.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page3.reload()
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)

    hm = page3.evaluate("""(function(){
        var th = document.querySelector('th.ws-emp-col.ws-emp-head-add');
        if (!th) return null;
        var r = th.getBoundingClientRect();
        return { w: r.width, h: r.height, cursor: getComputedStyle(th).cursor };
    })()""")
    check('O: мобайл — заголовок-кнопка «Сотрудник +» жив (курсор-палец)',
          hm is not None and hm['cursor'] == 'pointer' and hm['w'] >= 100, hm)
    page3.tap('td.ws-emp-col[data-tab="023"]')
    page3.wait_for_timeout(600)
    dis_m = page3.evaluate("(function(){ var pp=document.getElementById('wsEmpPopup'); return { open: pp.classList.contains('active'), dis: !!pp.querySelector('.ws-emp-dismiss') }; })()")
    check('P: мобайл — тап по ФИО → карточка, «Уволить…» есть',
          dis_m['open'] and dis_m['dis'], dis_m)
    page3.tap('#wsEmpPopup .ws-emp-dismiss')
    page3.wait_for_timeout(700)
    dism = page3.evaluate("""(function(){
        var sh = document.getElementById('wsDismissSheet');
        var r = sh.getBoundingClientRect();
        return { open: sh.classList.contains('active'), w: r.width,
                 emp: document.getElementById('wsDismissEmp').textContent,
                 date: document.getElementById('wsDismissDate').value };
    })()""")
    check('P2: мобайл — шторка увольнения во всю ширину, ФИО и дата живы',
          dism['open'] and dism['w'] >= 340 and
          'Петров' in dism['emp'] and dism['date'] == TODAY_ISO, dism)
    page3.screenshot(path='scripts/task318-proof-mobile.png', full_page=False)
    page3.evaluate("WorkSchedule.closeDismissForm()")
    page3.wait_for_timeout(300)
    check('P3: JS-ошибок нет (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

passed = sum(1 for r in results if r[1])
failed = sum(1 for r in results if not r[1])
print('\n===== ИТОГ Task 318 browser-check: %d/%d (pass/total) =====' % (passed, len(results)))
if failed:
    print('ПРОВАЛЕНЫ:')
    for r in results:
        if not r[1]:
            print('  FAIL ' + r[0] + ' | ' + str(r[2])[:300])
sys.exit(1 if failed else 0)
