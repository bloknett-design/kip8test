# -*- coding: utf-8 -*-
# Task 310: browser-check «График работы» — заявка пользователя:
#   1) у ячеек с ручными строчными «д»/«н» рамка 1px с ЗАКРУГЛЁННЫМИ
#      углами (Task 309 делал box-shadow 2px без скругления);
#   2) в карточке сотрудника НЕТ строки «Старт цикла»;
#   3) итог дней отпуска — «чистыми» днями за вычетом праздничных
#      нерабочих дней ст. 112 ТК РФ (ст. 120: праздники не включаются
#      в календарные дни отпуска); годовой лимит — 42 дня (хим.
#      производство: 28 осн. + 7 ст. 117 + 7 ст. 118 ТК РФ).
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404 — ProdCalendar работает на
# фолбэке фиксированных праздников ст. 112, тест детерминирован).
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8932

CODES = [
  {'code':'Д','name':'День','color':'#FFE082'},
  {'code':'Д8','name':'День 8ч','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'н','name':'Ночь в вых./праздник','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной','color':'#CFD8DC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':'ответственный за КИПиА цеха №2'},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = []
TRAININGS = []
# Иванов: 01.06–14.06 — 14 кал., минус 12.06 (День России) = 13 чистых.
# Петров: 3 части, суммарно 45 кал., минус 01.05 и 09.05 = 43 чистых
# → ПРЕВЫШЕНИЕ годового лимита 42 дн. (проверка красного итога).
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':1,'дата_начала':'2026-06-01','дата_окончания':'2026-06-14','комментарий':'лето'},
  {'id':2,'таб_номер':'023','часть':1,'дата_начала':'2026-05-01','дата_окончания':'2026-05-15','комментарий':''},
  {'id':3,'таб_номер':'023','часть':2,'дата_начала':'2026-07-01','дата_окончания':'2026-07-15','комментарий':''},
  {'id':4,'таб_номер':'023','часть':3,'дата_начала':'2026-09-01','дата_окончания':'2026-09-15','комментарий':''}
]

STATE = {'role': 'Админ', 'addvac_calls': []}

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
    if action == 'workSchedule.addVacation':
        STATE['addvac_calls'].append(body or {})
        return {'ok':True,'data':{'added':True}}
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def toast_text(page):
    return page.evaluate("(function(){var t=document.querySelector('#toast');return t? (t.textContent||'') : '';})()")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- Контекст 1: десктоп 1280px, Админ ----------
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
        s = json.dumps(resp, ensure_ascii=False)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=s.encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    # производственный календарь: внешние источники закрыты —
    # ProdCalendar перейдёт на фолбэк фиксированных праздников ст. 112
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t310)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t310')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # B. График работы + ИЮНЬ 2026 (месяц с праздником 12.06)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    page.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '6';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page.wait_for_timeout(2500)
    check('B: шахматка июнь 2026 отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. РУЧНАЯ «д» (суббота 13.06.2026, Петров — пустой день) →
    #    рамка ::before 1px с закруглёнными углами
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-06-13'") !== -1 && oc.indexOf("'023'") !== -1) { tds[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(700)
    page.evaluate("WorkSchedule.onPopupStatus('д')")
    page.wait_for_timeout(400)
    # Task 322: дневной персонал — сначала МАЛАЯ ФОРМА ЧАСОВ
    # (переработка по указанным часам); применяем 8 ч
    page.evaluate("(function(){ var i = document.getElementById('wsDnHours'); if (i) i.value = '8'; })()")
    page.evaluate("(function(){ var b = document.querySelector('#wsCellPopup .ws-dn-ok'); if (b) b.click(); })()")
    page.wait_for_timeout(900)
    frame = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-06-13'") !== -1 && oc.indexOf("'023'") !== -1) {
                var bf = getComputedStyle(tds[i], '::before');
                var cs = getComputedStyle(tds[i]);
                return { cls: tds[i].className, text: tds[i].textContent.trim(),
                         bfContent: bf.content, bfBorderTop: bf.borderTopWidth,
                         bfBorderStyle: bf.borderTopStyle,
                         bfRadius: bf.borderTopLeftRadius,
                         bfRadiusAll: [bf.borderTopRightRadius, bf.borderBottomRightRadius, bf.borderBottomLeftRadius],
                         bfPointer: bf.pointerEvents, shadow: cs.boxShadow };
            }
        }
        return null;
    })()""")
    check('C: ручная «д» — класс ws-manual-dn, ::before border 1px solid, все 4 угла radius 3px',
          frame is not None and 'ws-manual-dn' in frame['cls'] and
          frame['text'] == 'д' and frame['bfContent'] != 'none' and
          frame['bfBorderTop'] == '1px' and frame['bfBorderStyle'] == 'solid' and
          frame['bfRadius'] == '3px' and frame['bfRadiusAll'] == ['3px','3px','3px'] and
          frame['bfPointer'] == 'none', frame)
    # (в shadow ячейки остаётся тонкая 1.5px inset-тень ws-source-manual —
    # общий маркер ручных записей, живёт ПОД рамкой ::before — это норм)
    page.screenshot(path='scripts/task310-proof-frame.png', full_page=False)

    # C2. Соседняя пустая ячейка БЕЗ рамки (14.06, воскресенье)
    plain = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-06-14'") !== -1 && oc.indexOf("'023'") !== -1) {
                var bf = getComputedStyle(tds[i], '::before');
                return { cls: tds[i].className, content: bf.content,
                         border: bf.borderTopWidth, style: bf.borderTopStyle };
            }
        }
        return null;
    })()""")
    check('C2: пустая ячейка без рамки (::before отсутствует)',
          plain is not None and 'ws-manual-dn' not in plain['cls'] and
          plain['content'] == 'none', plain)

    # D. КАРТОЧКА ИВАНОВА (Task 311: открытие — ТОЛЬКО клик):
    #    нет «Старт цикла»; отпуск 01–14.06 = 13 дней за вычетом 12.06;
    #    итог года с лимитом 42 — УБРАН из карточки (Task 311)
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(500)
    iv = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        var total = pp ? (pp.querySelector('.ws-emp-total')||{}) : {};
        return { active: pp ? pp.classList.contains('active') : false,
                 noStartCycle: txt.indexOf('Старт цикла') === -1,
                 noStartVal: txt.indexOf('31.08.2026') === -1,
                 hasType: txt.indexOf('сменный, смена №1') !== -1,
                 hasPos: txt.indexOf('Слесарь КИПиА') !== -1,
                 hasHire: txt.indexOf('15.03.2024') !== -1,
                 hasPart: txt.indexOf('01.06.2026 — 14.06.2026') !== -1,
                 hasNet: txt.indexOf('13 дней') !== -1 && txt.indexOf('(−1 праздн.)') !== -1,
                 hasTotal: txt.indexOf('Итого в году: 13 дней') === -1,
                 hasHolNote: txt.indexOf('(вычтено праздников: 1)') === -1,
                 hasLimit: txt.indexOf('лимит 42') === -1,
                 noTotalNode: !pp.querySelector('.ws-emp-total'),
                 overClass: total.className || '',
                 overRed: (total.className || '').indexOf('ws-emp-overlimit') === -1 };
    })()""")
    check('D: карточка Иванова — «Старт цикла» НЕТ, поля профиля живы',
          iv['active'] and iv['noStartCycle'] and iv['noStartVal'] and
          iv['hasType'] and iv['hasPos'] and iv['hasHire'], iv)
    check('D2: отпуск 01–14.06 — «13 дней (−1 праздн.)»; итог «Итого … лимит 42» УБРАН (Task 311)',
          iv['hasPart'] and iv['hasNet'] and iv['hasTotal'] and
          iv['hasHolNote'] and iv['hasLimit'] and iv['noTotalNode'] and iv['overRed'], iv)
    page.screenshot(path='scripts/task310-proof-card-net.png', full_page=False)
    page.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    page.wait_for_timeout(300)

    # E. КАРТОЧКА ПЕТРОВА (Task 311: красный итог из карточки убран —
    #    лимит контролирует шторка «+ Отпуск», см. H ниже)
    page.click('td.ws-emp-col[data-tab="023"]')
    page.wait_for_timeout(500)
    pet = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        var total = pp ? (pp.querySelector('.ws-emp-total')||{}) : {};
        return { active: pp ? pp.classList.contains('active') : false,
                 hasOver: txt.indexOf('ПРЕВЫШЕН лимит 42 дн.') === -1,
                 hasTotal: txt.indexOf('Итого в году: 43 дн.') === -1,
                 noTotalNode: !pp.querySelector('.ws-emp-total'),
                 hasParts: txt.indexOf('Часть 1') !== -1 && txt.indexOf('Часть 2') !== -1,
                 overClass: (total.className || '').indexOf('ws-emp-overlimit') !== -1 };
    })()""")
    check('E: карточка Петрова — итог/ПРЕВЫШЕНИЕ убраны (Task 311), части периодов живы',
          pet['active'] and pet['hasOver'] and pet['hasTotal'] and pet['noTotalNode'] and
          pet['hasParts'] and not pet['overClass'], pet)
    page.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    page.wait_for_timeout(300)

    # F. (Task 311) Тултип плана отпуска в ячейке 12.06 — title УБРАН
    tip = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-06-12'") !== -1 && oc.indexOf("'017'") !== -1) {
                return { title: tds[i].getAttribute('title') || '',
                         cls: tds[i].className, text: tds[i].textContent.trim() };
            }
        }
        return null;
    })()""")
    check('F: Task 311 — тултип ячейки 12.06 убран; код «ОТ» плана в ячейке жив',
          tip is not None and tip['title'] == '' and 'ws-vac-plan' in tip['cls'] and
          tip['text'].find('ОТ') != -1, tip)

    # G. ШТОРКА «+ Отпуск»: Иванов 01.07–14.07 — строка периода,
    #    строка лимита года, добавление проходит.
    #    Task 312: вход в шторку — через строку «+ Отпуск…» в блоке
    #    отпусков КАРТОЧКИ сотрудника (кнопки в тулбаре больше нет);
    #    сотрудник уже префиллен (select_option — страховка)
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-addvac')
    page.wait_for_timeout(700)
    page.select_option('#wsVacTabNo', '017')
    page.fill('#wsVacStart', '2026-07-01')
    page.fill('#wsVacEnd', '2026-07-14')
    page.evaluate("WorkSchedule.onVacDatesChange()")
    page.wait_for_timeout(300)
    sheet = page.evaluate("""(function(){
        var days = document.getElementById('wsVacDaysInfo');
        var year = document.getElementById('wsVacYearInfo');
        var tab = document.getElementById('wsVacTabNo');
        return { open: document.getElementById('wsVacSheet').classList.contains('active'),
                 tab: tab ? tab.value : '',
                 days: days ? days.textContent : '',
                 year: year ? year.textContent : '',
                 yearCls: year ? year.className : '' };
    })()""")
    check('G: шторка открыта, Иванов: «14 кал. дн. (праздников нет)»',
          sheet['open'] and sheet['tab'] == '017' and
          sheet['days'].find('14 кал. дн.') != -1 and
          sheet['days'].find('праздников нет') != -1, sheet)
    check('G2: строка лимита «запланировано 13 из 42 … с этим периодом: 27»',
          sheet['year'].find('запланировано 13 из 42') != -1 and
          sheet['year'].find('с этим периодом: 27') != -1 and
          sheet['yearCls'].find('ws-vac-overlimit') == -1, sheet)
    page.click('#wsVacSheet .flow-input-submit')
    page.wait_for_timeout(2000)
    t1 = toast_text(page)
    add1 = STATE['addvac_calls'][0] if STATE['addvac_calls'] else {}
    check('G3: отпуск добавлен (addVacation вызван), тост «Отпуск добавлен»',
          len(STATE['addvac_calls']) == 1 and add1.get('таб_номер') == '017' and
          add1.get('дата_начала') == '2026-07-01' and 'Отпуск добавлен' in t1,
          (add1, t1[:100]))

    # H. БЛОКИРОВКА ПРЕВЫШЕНИЯ: Петров (уже 43) + 01.08–14.08 →
    #    красная строка «— ПРЕВЫШЕНИЕ», addVacation НЕ вызывается
    page.click('td.ws-emp-col[data-tab="023"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-addvac')
    page.wait_for_timeout(700)
    page.select_option('#wsVacTabNo', '023')
    page.fill('#wsVacStart', '2026-08-01')
    page.fill('#wsVacEnd', '2026-08-14')
    page.evaluate("WorkSchedule.onVacEmployeeChange()")
    page.evaluate("WorkSchedule.onVacDatesChange()")
    page.wait_for_timeout(300)
    over = page.evaluate("""(function(){
        var days = document.getElementById('wsVacDaysInfo');
        var year = document.getElementById('wsVacYearInfo');
        return { open: document.getElementById('wsVacSheet').classList.contains('active'),
                 days: days ? days.textContent : '',
                 year: year ? year.textContent : '',
                 yearCls: year ? year.className : '',
                 color: year ? getComputedStyle(year).color : '' };
    })()""")
    check('H: Петров — строка лимита красная «43 из 42 … 57 — ПРЕВЫШЕНИЕ»',
          over['open'] and over['year'].find('запланировано 43 из 42') != -1 and
          over['year'].find('с этим периодом: 57 — ПРЕВЫШЕНИЕ') != -1 and
          over['yearCls'].find('ws-vac-overlimit') != -1, over)
    page.click('#wsVacSheet .flow-input-submit')
    page.wait_for_timeout(1500)
    t2 = toast_text(page)
    check('H2: сабмит заблокирован — тост «Превышен годовой лимит», addVacation НЕ вызван',
          'Превышен годовой лимит' in t2 and 'всего 57' in t2 and
          len(STATE['addvac_calls']) == 1, t2[:140])
    page.screenshot(path='scripts/task310-proof-vac-limit.png', full_page=False)

    # I. JS-ошибок нет
    check('I: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ---------- Контекст 2: мобильный 375px, Админ ----------
    ctxm = browser.new_context(viewport={'width':375,'height':720}, has_touch=True)
    pagem = ctxm.new_page()
    js_errors_m = []
    pagem.on('pageerror', lambda e: js_errors_m.append(str(e)))
    ctxm.route('**/exec?**', handle)
    ctxm.route('**script.google.com/**', handle)
    ctxm.route('**raw.githubusercontent.com/**', block_external)
    ctxm.route('**calendar.legalic.ru/**', block_external)

    pagem.goto('http://localhost:%d/index.html' % PORT)
    pagem.evaluate("localStorage.setItem('kip8_session_token','browser-check-t310-m')")
    pagem.reload()
    pagem.wait_for_timeout(2500)
    pagem.evaluate("navigateTo('work-schedule')")
    pagem.wait_for_timeout(1500)
    pagem.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '6';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    pagem.wait_for_timeout(2500)
    pagem.click('td.ws-emp-col[data-tab="023"]')
    pagem.wait_for_timeout(600)
    mob = pagem.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var r = pp.getBoundingClientRect();
        var txt = pp.textContent;
        return { active: pp.classList.contains('active'),
                 inView: r.left >= 0 && r.right <= window.innerWidth && r.top >= 0,
                 over: txt.indexOf('ПРЕВЫШЕН лимит 42') === -1,
                 noStart: txt.indexOf('Старт цикла') === -1,
                 noTotal: txt.indexOf('Итого в году') === -1 };
    })()""")
    check('K: 375px — карточка в пределах экрана; «Старт цикла»/итог года НЕТ (Task 311)',
          mob['active'] and mob['inView'] and mob['over'] and mob['noStart'] and mob['noTotal'], mob)
    ovf = pagem.evaluate("(function(){var de=document.documentElement;return {sw:de.scrollWidth,cw:de.clientWidth};})()")
    check('K2: 375px — нет горизонтального переполнения',
          ovf['sw'] <= ovf['cw'] + 2, ovf)
    check('L: мобильный — JS-ошибок нет', len(js_errors_m) == 0, js_errors_m[:3])
    ctxm.close()

    # ---------- Контекст 3: десктоп, «ИТР8 pro» (просмотр) ----------
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t310-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1500)
    page2.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '6';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page2.wait_for_timeout(2500)
    page2.click('td.ws-emp-col[data-tab="017"]')
    page2.wait_for_timeout(600)
    ro = page2.evaluate("""(function(){
        var btn = document.getElementById('wsVacBtn');
        var pp = document.getElementById('wsEmpPopup');
        var addVac = pp ? pp.querySelector('.ws-emp-addvac') : null;
        return { btnGone: !btn,
                 noAddVac: !addVac };
    })()""")
    check('M: «ИТР8 pro» — «+ Отпуск» недоступна (Task 312: кнопки нет, строки в карточке нет)',
          ro['btnGone'] and ro['noAddVac'], ro)
    ro2 = page2.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        return { active: pp ? pp.classList.contains('active') : false,
                 hasNet: txt.indexOf('13 дней') !== -1,
                 hasLimit: txt.indexOf('лимит 42') === -1,
                 noStart: txt.indexOf('Старт цикла') === -1 };
    })()""")
    check('M2: «ИТР8 pro» — карточка по клику (Task 311): чистые дни видны, итога/лимита НЕТ',
          ro2['active'] and ro2['hasNet'] and ro2['hasLimit'] and ro2['noStart'], ro2)
    check('N: JS-ошибок нет (просмотр)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task310-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
