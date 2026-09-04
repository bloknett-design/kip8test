# -*- coding: utf-8 -*-
# Task 307: browser-check «График работы» — заявка пользователя:
#   1) Вкладка «Сотрудники» УДАЛЕНА из субнавигации модуля (осталось
#      Шахматка / Инструктажи / Отпуска = 3 кнопки × 3 полосы);
#      страница #page-work-schedule-employees удалена целиком;
#   2) Кнопка «+ Сотрудник» (добавление) ПЕРЕНЕСЕНА в бар над
#      шахматкой (ws-toolbar-main, рядом с селектами и «Сформировать»);
#      открывает прежний bottom-sheet #wsEmpSheet; после добавления
#      перезагружается ШАХМАТКА (loadGrid) — новая строка сотрудника;
#   3) Видимость кнопки — по _canEdit (как «Сформировать»):
#      Админ видит, «ИТР8 pro» (просмотр) — нет.
# Playwright + мок fetch (перехват POST к Apps Script по action).
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

WS_URL = 'https://script.google.com/macros/s/AKfycbyt2sjbJ8xT5UPKDlYj4q-CV-5pH_Yrv5COrg0PIpp92snpQULUNtJC__pMnQ0h6feNlA/exec'
PORT = 8927

CODES = [
  {'code':'Д','name':'День','color':'#FFE082'},
  {'code':'Д8','name':'День 8ч','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь','color':'#B0BEC5'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной','color':'#CFD8DC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА смена №1','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА дневной','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный 5-дневный','cycle':5,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''},{'day':5,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'дата':'2026-09-01','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-14','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
TRAININGS = [
  {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный по охране труда','дата_начала':'2026-09-10','дата_окончания':'2026-09-10','длительность_дней':1,'комментарий':''}
]
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':2,'дата_начала':'2026-09-05','дата_окончания':'2026-09-16','комментарий':''}
]

STATE = {'role': 'Админ', 'added': None, 'add_calls': [], 'emp_calls': 0}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        # Структура ответа как у серверного rmGetMyAccess: found + permissions
        # (для Админа оверлей пропускается по '*', для остальных — критично)
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
        STATE['emp_calls'] += 1
        emps = EMPLOYEES + ([STATE['added']] if STATE['added'] else [])
        return {'ok':True,'data':{'employees':emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.addEmployee':
        STATE['add_calls'].append(body or {})
        STATE['added'] = {'таб_номер':(body or {}).get('таб_номер','042'),
                          'ФИО':(body or {}).get('ФИО','Сидоров С. С.'),
                          'тип':(body or {}).get('тип','сменный'),
                          'смена':1,'шаблон_ротации':1,
                          'старт_цикла':'2026-09-10','дата_приёма':'','дата_увольнения':'',
                          'в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
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

    # ---------- Контекст 1: мобильный 375px, Админ ----------
    ctx = browser.new_context(viewport={'width':375,'height':720})
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

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t307')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась, дашборд активен',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # B. График работы + сентябрь 2026
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    page.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '9';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page.wait_for_timeout(2500)
    check('B: шахматка отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. Субнавигация: 3 кнопки, без «Сотрудники»
    sub = page.evaluate("""(function(){
        var s = document.querySelector('#page-work-schedule .ws-subnav');
        var btns = s ? s.querySelectorAll('.ws-subnav-btn') : [];
        var labels = [];
        for (var i=0;i<btns.length;i++) labels.push(btns[i].textContent.trim());
        return { count: btns.length, labels: labels,
                 active: s ? (s.querySelector('.ws-subnav-btn.active')||{}).textContent : null };
    })()""")
    check('C: субнавигация — 3 кнопки (Шахматка/Инструктажи/Отпуска), без «Сотрудники»',
          sub['count'] == 3 and sub['labels'] == ['Шахматка','Инструктажи','Отпуска'] and
          'Сотрудники' not in sub['labels'], sub)
    check('C2: активная кнопка — «Шахматка»', sub['active'] == 'Шахматка', sub)

    # D. Кнопка «+ Сотрудник» в тулбаре над шахматкой
    tb = page.evaluate("""(function(){
        var b = document.getElementById('wsEmpBtn');
        var g = document.getElementById('wsGenerateBtn');
        if (!b) return null;
        var inMain = !!b.closest('.ws-toolbar-main');
        var inPage = !!b.closest('#page-work-schedule');
        return { text: b.textContent.trim(), hidden: b.hidden, title: b.title,
                 inMain: inMain, inPage: inPage,
                 genHidden: g ? g.hidden : null,
                 before: g ? (b.compareDocumentPosition(g) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0 : null,
                 h: b.getBoundingClientRect().height };
    })()""")
    check('D: «+ Сотрудник» в тулбаре (ws-toolbar-main, страница work-schedule), видна Админу',
          tb and tb['text'] == '+ Сотрудник' and not tb['hidden'] and tb['inMain'] and tb['inPage'], tb)
    check('D2: стоит в ряду ДО «Сформировать»; высота 34px', 
          tb and tb['before'] and not tb['genHidden'] and abs(tb['h'] - 34) < 1.5, tb)
    check('D3: title = «Добавить сотрудника»', tb and tb['title'] == 'Добавить сотрудника', tb)

    # E. Клик «+ Сотрудник» → bottom-sheet формы
    page.click('#wsEmpBtn')
    page.wait_for_timeout(700)
    sheet = page.evaluate("""(function(){
        var sh = document.getElementById('wsEmpSheet');
        var ov = document.getElementById('wsEmpOverlay');
        var f = document.getElementById('wsEmpTabNo');
        return { active: sh ? sh.classList.contains('active') : false,
                 ovActive: ov ? ov.classList.contains('active') : false,
                 title: (document.querySelector('#wsEmpSheet .flow-input-sheet-title')||{}).textContent,
                 tab: f ? f.value : '?',
                 focus: document.activeElement ? document.activeElement.id : '' };
    })()""")
    check('E: клик открыл bottom-sheet «Новый сотрудник» (sheet+overlay active)',
          sheet['active'] and sheet['ovActive'] and sheet['title'] == 'Новый сотрудник', sheet)
    check('E2: поле «Таб. №» пусто и в фокусе', sheet['tab'] == '' and sheet['focus'] == 'wsEmpTabNo', sheet)
    page.screenshot(path='scripts/task307-proof-sheet.png', full_page=False)

    # F. Заполнить форму → «Добавить» → мок addEmployee + перезагрузка шахматки
    page.fill('#wsEmpTabNo', '042')
    page.fill('#wsEmpFio', 'Сидоров С. С.')
    page.select_option('#wsEmpType', 'сменный')
    page.select_option('#wsEmpShift', '1')
    page.select_option('#wsEmpPattern', '1')
    page.fill('#wsEmpPosition', 'Слесарь КИПиА')
    emp_calls_before = STATE['emp_calls']
    page.click('#wsEmpSheet .flow-input-submit')
    page.wait_for_timeout(2500)
    add = STATE['add_calls'][0] if STATE['add_calls'] else {}
    check('F: сервер получил workSchedule.addEmployee (таб 042 / ФИО Сидоров)',
          len(STATE['add_calls']) == 1 and add.get('таб_номер') == '042' and
          add.get('ФИО') == 'Сидоров С. С.', add)
    closed = page.evaluate("!document.getElementById('wsEmpSheet').classList.contains('active')")
    t = toast_text(page)
    check('F2: шторка закрыта, тост «Сотрудник добавлен»', closed and 'добавлен' in t, t[:120])
    check('F3: шахматка перезагружена — listEmployees снова запрошен',
          STATE['emp_calls'] > emp_calls_before, (emp_calls_before, STATE['emp_calls']))
    new_row = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            if (rows[r].textContent.indexOf('Сидоров') !== -1) return rows[r].textContent.slice(0,40);
        }
        return null;
    })()""")
    check('F4: НОВАЯ СТРОКА «Сидоров» в шахматке', new_row is not None, new_row)

    # G. Инструктажи: субнав 3 кнопки, страница жива
    page.evaluate("navigateTo('work-schedule-trainings')")
    page.wait_for_timeout(1200)
    tr = page.evaluate("""(function(){
        var s = document.querySelector('#page-work-schedule-trainings .ws-subnav');
        var btns = s ? s.querySelectorAll('.ws-subnav-btn') : [];
        var labels = [];
        for (var i=0;i<btns.length;i++) labels.push(btns[i].textContent.trim());
        var list = document.getElementById('wsTrainingsList');
        return { labels: labels, hasCard: list ? list.innerHTML.indexOf('Иванов') !== -1 : false };
    })()""")
    check('G: «Инструктажи» — субнав 3 кнопки, карточки живы',
          tr['labels'] == ['Шахматка','Инструктажи','Отпуска'] and tr['hasCard'], tr)

    # H. Отпуска: субнав 3 кнопки
    page.evaluate("navigateTo('work-schedule-vacations')")
    page.wait_for_timeout(1200)
    vac = page.evaluate("""(function(){
        var s = document.querySelector('#page-work-schedule-vacations .ws-subnav');
        var btns = s ? s.querySelectorAll('.ws-subnav-btn') : [];
        var labels = [];
        for (var i=0;i<btns.length;i++) labels.push(btns[i].textContent.trim());
        return labels;
    })()""")
    check('H: «Отпуска» — субнав 3 кнопки', vac == ['Шахматка','Инструктажи','Отпуска'], vac)

    # I. Прямая навигация на удалённую страницу — не падает
    page.evaluate("navigateTo('work-schedule-employees')")
    page.wait_for_timeout(600)
    gone = page.evaluate("""(function(){
        var el = document.getElementById('page-work-schedule-employees');
        var act = document.querySelector('.page-content.active');
        return { el: !!el, active: act ? act.id : '' };
    })()""")
    check('I: страницы work-schedule-employees НЕТ; navigateTo не падает',
          not gone['el'] and gone['active'] != 'page-work-schedule-employees', gone)

    # J. Мобильный тулбар без горизонтального переполнения
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1000)
    ovf = page.evaluate("""(function(){
        var de = document.documentElement;
        var main = document.querySelector('.ws-toolbar-main');
        return { scrollW: de.scrollWidth, clientW: de.clientWidth,
                 rowH: main ? Math.round(main.getBoundingClientRect().height) : 0,
                 wrapped: main ? (main.getBoundingClientRect().height > 44) : false };
    })()""")
    check('J: 375px — нет горизонтального скролла (ряд переносится, не вылезает)',
          ovf['scrollW'] <= ovf['clientW'] + 2, ovf)
    page.screenshot(path='scripts/task307-proof-mobile.png', full_page=False)

    # K. JS-ошибок нет (контекст 1)
    check('K: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ---------- Контекст 2: десктоп 1280px, «ИТР8 pro» (просмотр) ----------
    STATE['role'] = 'ИТР8 pro'
    STATE['added'] = None
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t307-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(2000)
    ro = page2.evaluate("""(function(){
        var b = document.getElementById('wsEmpBtn');
        var g = document.getElementById('wsGenerateBtn');
        var cal = document.getElementById('wsCalPanel');
        var main = document.querySelector('.ws-toolbar-main');
        return { empHidden: b ? b.hidden : null, genHidden: g ? g.hidden : null,
                 calAfterMain: (cal && main) ? (cal.getBoundingClientRect().left > main.getBoundingClientRect().right) : null,
                 calVisible: cal ? !cal.hidden : null,
                 noWrap: main ? getComputedStyle(main).flexWrap !== 'wrap' : null,
                 grid: !!document.querySelector('#wsGridWrap table') };
    })()""")
    check('L: десктоп 1280px — «ИТР8 pro» (просмотр): «+ Сотрудник» СКРЫТА, сетка жива',
          ro['empHidden'] is True and ro['grid'], ro)
    check('L2: «Сформировать» тоже скрыта (паритет видимости)', ro['genHidden'] is True, ro)
    check('L3: десктоп — ряд nowrap, окошко календаря справа от кнопок',
          ro['noWrap'] and ro['calVisible'] and ro['calAfterMain'], ro)
    check('M: JS-ошибок нет (десктоп, 0 pageerror)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task307-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
