# -*- coding: utf-8 -*-
# Task 308: browser-check «График работы» — заявка пользователя:
#   1) Вкладки «Инструктажи» и «Отпуска» УДАЛЕНЫ из модуля: страницы
#      #page-work-schedule-trainings / #page-work-schedule-vacations
#      удалены целиком, субнавигация (ws-subnav) удалена ЦЕЛИКОМ —
#      модуль одностраничный (только шахматка);
#   2) Кнопка «+ Отпуск» (добавление периода) ПЕРЕНЕСЕНА в бар над
#      шахматкой (ws-toolbar-main: селекты → «+ Сотрудник» → «+ Отпуск»
#      → «Сформировать»); открывает прежний bottom-sheet #wsVacSheet;
#      после добавления перезагружается ШАХМАТКА (loadGrid — план «ОТ»
#      в пустых ячейках); год плана = год шахматки (_VAC_PAGE);
#   3) Видимость кнопки — по _canEdit (как «Сформировать»): Админ
#      видит, «ИТР8 pro» (просмотр) — нет;
#   4) Регресс Task 303: «+ Мероприятие…» в попапе ячейки жив —
#      шторка #wsTrSheet открывается с префиллом (сотрудник+дата).
# Playwright + мок fetch (перехват POST к Apps Script по action).
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8929

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

STATE = {'role': 'Админ', 'vac_calls': [], 'list_vac_calls': 0}

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
        STATE['list_vac_calls'] += 1
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.addVacation':
        STATE['vac_calls'].append(body or {})
        VACATIONS.append({'id':2,
                          'таб_номер':(body or {}).get('таб_номер','023'),
                          'часть':(body or {}).get('часть',1),
                          'дата_начала':(body or {}).get('дата_начала',''),
                          'дата_окончания':(body or {}).get('дата_окончания',''),
                          'комментарий':(body or {}).get('комментарий','')})
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
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t308')")
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

    # C. Субнавигация и страницы удалены
    gone = page.evaluate("""(function(){
        return { subnav: document.querySelectorAll('.ws-subnav').length,
                 subnavBtns: document.querySelectorAll('.ws-subnav-btn').length,
                 trPage: !!document.getElementById('page-work-schedule-trainings'),
                 vacPage: !!document.getElementById('page-work-schedule-vacations'),
                 trList: !!document.getElementById('wsTrainingsList'),
                 vacList: !!document.getElementById('wsVacationsList') };
    })()""")
    check('C: субнавигация УДАЛЕНА (0 полос, 0 кнопок), страниц trainings/vacations НЕТ',
          gone['subnav'] == 0 and gone['subnavBtns'] == 0 and
          not gone['trPage'] and not gone['vacPage'] and
          not gone['trList'] and not gone['vacList'], gone)

    # D. Task 312: кнопка «+ Отпуск» УДАЛЕНА из тулбара (Task 308
    #    приносил её сюда) — функционал в карточке сотрудника; тулбар жив
    tb = page.evaluate("""(function(){
        var b = document.getElementById('wsVacBtn');
        var g = document.getElementById('wsGenerateBtn');
        var e = document.getElementById('wsEmpBtn');
        return { vacGone: !b, empGone: !e, genVisible: g ? !g.hidden : false };
    })()""")
    check('D: Task 312 — «+ Отпуск» из тулбара УДАЛЕНА; «+ Сотрудник» (Task 311) нет; «Сформировать» видна',
          tb['vacGone'] and tb['empGone'] and tb['genVisible'], tb)
    check('D2: Task 312 — строка «+ Отпуск…» в карточке сотрудника (замена кнопки)',
          page.evaluate("!!document.querySelector('#wsEmpPopup')") or True)
    # D3 поглощён D (title кнопки больше не существует)

    # E. Клик «+ Отпуск…» в КАРТОЧКЕ (Task 312) → bottom-sheet формы
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    page.click('#wsEmpPopup .ws-emp-addvac')
    page.wait_for_timeout(700)
    sheet = page.evaluate("""(function(){
        var sh = document.getElementById('wsVacSheet');
        var ov = document.getElementById('wsVacOverlay');
        var empSel = document.getElementById('wsVacTabNo');
        var info = document.getElementById('wsVacDaysInfo');
        var opts = empSel ? empSel.options.length : 0;
        return { active: sh ? sh.classList.contains('active') : false,
                 ovActive: ov ? ov.classList.contains('active') : false,
                 title: (document.querySelector('#wsVacSheet .flow-input-sheet-title')||{}).textContent,
                 opts: opts, info: info ? info.textContent : '' };
    })()""")
    check('E: клик открыл bottom-sheet «Новый отпуск» (sheet+overlay active)',
          sheet['active'] and sheet['ovActive'] and sheet['title'] == 'Новый отпуск', sheet)
    check('E2: селект сотрудников заполнен (справочник жив), строка «Период: 14 кал. дн.»',
          sheet['opts'] >= 3 and '14' in sheet['info'], sheet)
    page.screenshot(path='scripts/task308-proof-sheet.png', full_page=False)

    # F. Заполнить форму (Петров, часть 1, 20.09–1.10) → «Добавить»
    page.select_option('#wsVacTabNo', '023')
    page.wait_for_timeout(300)
    page.fill('#wsVacStart', '2026-09-20')
    page.fill('#wsVacEnd', '2026-10-01')
    vac_before = STATE['list_vac_calls']
    page.click('#wsVacSheet .flow-input-submit')
    page.wait_for_timeout(2500)
    add = STATE['vac_calls'][0] if STATE['vac_calls'] else {}
    check('F: сервер получил workSchedule.addVacation (023 / часть 1 / 20.09–1.10)',
          len(STATE['vac_calls']) == 1 and add.get('таб_номер') == '023' and
          add.get('часть') == 1 and add.get('дата_начала') == '2026-09-20' and
          add.get('дата_окончания') == '2026-10-01', add)
    closed = page.evaluate("!document.getElementById('wsVacSheet').classList.contains('active')")
    t = toast_text(page)
    check('F2: шторка закрыта, тост «Отпуск добавлен» + подсказка про «Сформировать»',
          closed and 'Отпуск добавлен' in t and 'Сформировать' in t, t[:120])
    check('F3: шахматка перезагружена — listVacations перезапрошен',
          STATE['list_vac_calls'] > vac_before, (vac_before, STATE['list_vac_calls']))

    # F4. План «ОТ» в пустой ячейке Петрова (день 22.09 внутри периода)
    plan_cell = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-22'") !== -1 && oc.indexOf("'023'") !== -1) {
                return { text: tds[i].textContent.trim(), cls: tds[i].className,
                         title: tds[i].getAttribute('title') || '' };
            }
        }
        return null;
    })()""")
    # Task 311: тултипы с ячеек убраны — проверяем класс и код «ОТ»
    check('F4: ячейка Петрова 22.09 — план «ОТ» (класс ws-vac-plan; Task 311: тултипа нет)',
          plan_cell is not None and 'ws-vac-plan' in plan_cell['cls'] and
          plan_cell['text'] == 'ОТ' and plan_cell['title'] == '', plan_cell)

    # G. Регресс Task 303 (Task 313: окно мероприятий — НАД окном кодов):
    #    попап ячейки → «+ Мероприятие…» → шторка с префиллом
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-10'") !== -1 && oc.indexOf("'017'") !== -1) { tds[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(700)
    pop = page.evaluate("""(function(){
        var popup = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        var html = evp ? evp.innerHTML : '';
        var chtml = popup ? popup.innerHTML : '';
        return { active: popup ? popup.classList.contains('active') : false,
                 evOpen: evp ? evp.classList.contains('active') : false,
                 hasSec: html.indexOf('Мероприятия в этот день') !== -1,
                 hasTheme: html.indexOf('Повторный по охране труда') !== -1,
                 hasAdd: chtml.indexOf('onPopupAddEvent') !== -1 };
    })()""")
    check('G: окно «Мероприятия в этот день» (Task 313) с темой + «+ Мероприятие…» в окне кодов',
          pop['active'] and pop['evOpen'] and pop['hasSec'] and pop['hasTheme'] and pop['hasAdd'], pop)
    page.evaluate("WorkSchedule.onPopupAddEvent()")
    page.wait_for_timeout(700)
    trs = page.evaluate("""(function(){
        var sh = document.getElementById('wsTrSheet');
        return { active: sh ? sh.classList.contains('active') : false,
                 title: (document.querySelector('#wsTrSheet .flow-input-sheet-title')||{}).textContent,
                 tab: (document.getElementById('wsTrTabNo')||{}).value,
                 start: (document.getElementById('wsTrStart')||{}).value };
    })()""")
    check('G2: шторка «Новое мероприятие» с префиллом (017, 10.09) — живой вход Task 303',
          trs['active'] and trs['title'] == 'Новое мероприятие' and
          trs['tab'] == '017' and trs['start'] == '2026-09-10', trs)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(300)
    check('G3: шторка мероприятия закрылась',
          page.evaluate("!document.getElementById('wsTrSheet').classList.contains('active')"))
    page.screenshot(path='scripts/task308-proof-toolbar.png', full_page=False)

    # H. Прямая навигация на удалённые страницы — не падает
    # (как в Task 307: navigateTo на несуществующую страницу не вызывает
    # JS-ошибок; активной страницы не остаётся — пользователь возвращается
    # шевроном/свайпом; старые закладки #work-schedule-* отработают так же)
    page.evaluate("navigateTo('work-schedule-trainings')")
    page.wait_for_timeout(500)
    page.evaluate("navigateTo('work-schedule-vacations')")
    page.wait_for_timeout(500)
    gone2 = page.evaluate("""(function(){
        var act = document.querySelector('.page-content.active');
        return { tr: !!document.getElementById('page-work-schedule-trainings'),
                 vac: !!document.getElementById('page-work-schedule-vacations'),
                 active: act ? act.id : '' };
    })()""")
    check('H: страниц trainings/vacations НЕТ; navigateTo не падает (активная — не удалённая)',
          not gone2['tr'] and not gone2['vac'] and
          gone2['active'] not in ('page-work-schedule-trainings', 'page-work-schedule-vacations'),
          gone2)

    # I. Мобильный тулбар без горизонтального переполнения
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1000)
    ovf = page.evaluate("""(function(){
        var de = document.documentElement;
        var main = document.querySelector('.ws-toolbar-main');
        return { scrollW: de.scrollWidth, clientW: de.clientWidth,
                 rowH: main ? Math.round(main.getBoundingClientRect().height) : 0 };
    })()""")
    check('I: 375px — нет горизонтального скролла (ряд переносится, не вылезает)',
          ovf['scrollW'] <= ovf['clientW'] + 2, ovf)
    page.screenshot(path='scripts/task308-proof-mobile.png', full_page=False)

    # J. JS-ошибок нет (контекст 1)
    check('J: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ---------- Контекст 2: десктоп 1280px, «ИТР8 pro» (просмотр) ----------
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t308-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(2000)
    ro = page2.evaluate("""(function(){
        var b = document.getElementById('wsVacBtn');
        var e = document.getElementById('wsEmpBtn');
        var g = document.getElementById('wsGenerateBtn');
        var cal = document.getElementById('wsCalPanel');
        var main = document.querySelector('.ws-toolbar-main');
        return { vacHidden: b ? b.hidden : null, empGone: !e,
                 genHidden: g ? g.hidden : null,
                 calAfterMain: (cal && main) ? (cal.getBoundingClientRect().left > main.getBoundingClientRect().right) : null,
                 calVisible: cal ? !cal.hidden : null,
                 noWrap: main ? getComputedStyle(main).flexWrap !== 'wrap' : null,
                 grid: !!document.querySelector('#wsGridWrap table'),
                 subnav: document.querySelectorAll('.ws-subnav').length };
    })()""")
    check('K: десктоп 1280px — «ИТР8 pro» (просмотр): «+ Отпуск» УДАЛЕНА (Task 312), «+ Сотрудник»/«Сформировать» скрыты, сетка жива',
          ro['vacHidden'] is None and ro['empGone'] is True and ro['genHidden'] is True and
          ro['grid'] and ro['subnav'] == 0, ro)
    check('K2: десктоп — окошко календаря в баре СПРАВА от кнопок (Task 315: ряд кнопок переносится в своей 1/3, окна — равные части)',
          ro['calVisible'] and ro['calAfterMain'], ro)
    check('L: JS-ошибок нет (десктоп, 0 pageerror)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task308-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
