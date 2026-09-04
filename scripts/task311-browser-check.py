# -*- coding: utf-8 -*-
# Task 311: browser-check «График работы» — заявка пользователя:
#   1) в карточке сотрудника убрать строки «Шаблон ротации»,
#      «Сотрудник» (строка-заголовок) и «Итого в году»;
#   2) убрать пояснительные окна при наведении на ячейки
#      сотрудников и шахматки (карточка — ТОЛЬКО по клику);
#   3) убрать кнопку «+ Сотрудник» — её функцию выполняет
#      заголовок «Сотрудник» в шапке над колонкой ФИО.
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404 — ProdCalendar работает на
# фолбэке фиксированных праздников ст. 112, тест детерминирован).
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8933

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
# Петров: 3 части = 45 кал., минус 01.05/09.05 = 43 чистых (> лимита 42 —
# раньше карточка краснела «Итого … ПРЕВЫШЕН»; Task 311 строку убрал).
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':1,'дата_начала':'2026-06-01','дата_окончания':'2026-06-14','комментарий':'лето'},
  {'id':2,'таб_номер':'023','часть':1,'дата_начала':'2026-05-01','дата_окончания':'2026-05-15','комментарий':''},
  {'id':3,'таб_номер':'023','часть':2,'дата_начала':'2026-07-01','дата_окончания':'2026-07-15','комментарий':''},
  {'id':4,'таб_номер':'023','часть':3,'дата_начала':'2026-09-01','дата_окончания':'2026-09-15','комментарий':''}
]

STATE = {'role': 'Админ'}

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
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def toast_text(page):
    return page.evaluate("(function(){var t=document.querySelector('#toast');return t? (t.textContent||'') : '';})()")

def goto_june(page):
    page.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '6';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page.wait_for_timeout(2500)

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
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t311)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t311')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # B. График работы + ИЮНЬ 2026
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    goto_june(page)
    check('B: шахматка июнь 2026 отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. Кнопки тулбара: «+ Сотрудник» НЕТ, «+ Отпуск» жива
    tb = page.evaluate("""(function(){
        var empBtn = document.getElementById('wsEmpBtn');
        var vacBtn = document.getElementById('wsVacBtn');
        var genBtn = document.getElementById('wsGenerateBtn');
        return { empBtn: !!empBtn, vacBtn: !!vacBtn, genBtn: !!genBtn };
    })()""")
    check('C: кнопка «+ Сотрудник» (#wsEmpBtn) УДАЛЕНА; «+ Отпуск» и «Сформировать» живы',
          (not tb['empBtn']) and tb['vacBtn'] and tb['genBtn'], tb)

    # D. ЗАГОЛОВОК «Сотрудник» — кнопка добавления (редактору)
    head = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap thead th.ws-emp-col');
        if (!th) return null;
        var cs = getComputedStyle(th);
        var plus = th.querySelector('.ws-emp-head-plus');
        return { cls: th.className, onclick: th.getAttribute('onclick') || '',
                 cursor: cs.cursor, plus: !!plus,
                 plusText: plus ? plus.textContent : '' };
    })()""")
    check('D: шапка «Сотрудник» — класс ws-emp-head-add, onclick openEmployeeForm, курсор-палец, плюсик',
          head is not None and 'ws-emp-head-add' in head['cls'] and
          'openEmployeeForm' in head['onclick'] and head['cursor'] == 'pointer' and
          head['plus'] and head['plusText'] == '+', head)
    page.screenshot(path='scripts/task311-proof-head-add.png', full_page=False)

    # E. Клик по заголовку «Сотрудник» → шторка #wsEmpSheet открывается
    page.click('#wsGridWrap thead th.ws-emp-col')
    page.wait_for_timeout(700)
    sheet = page.evaluate("""(function(){
        var sh = document.getElementById('wsEmpSheet');
        return { open: sh ? sh.classList.contains('active') : false,
                 title: document.getElementById('wsEmpSheetTitle') ?
                        document.getElementById('wsEmpSheetTitle').textContent : '' };
    })()""")
    check('E: клик по заголовку открывает шторку добавления сотрудника', sheet['open'], sheet)
    # закрыть шторку (кнопка отмены/клик по оверлею)
    page.evaluate("""(function(){
        var ov = document.getElementById('wsEmpOverlay');
        if (ov) ov.click();
        else {
            var btns = document.querySelectorAll('#wsEmpSheet button');
            for (var i=0;i<btns.length;i++) if (btns[i].textContent.indexOf('Отмена')!==-1) { btns[i].click(); break; }
        }
    })()""")
    page.wait_for_timeout(500)
    closed = page.evaluate("!document.getElementById('wsEmpSheet').classList.contains('active')")
    check('E2: шторка закрылась (отмена)', closed)

    # F. НАВЕДЕНИЕ на ячейку ФИО — карточка НЕ открывается (Task 311)
    page.hover('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(900)
    hv = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        return { active: pp ? pp.classList.contains('active') : null,
                 empty: pp ? !pp.textContent : null };
    })()""")
    check('F: наведение на ячейку ФИО — карточка НЕ открывается',
          hv['active'] is False and hv['empty'] is True, hv)
    page.mouse.move(640, 400)
    page.wait_for_timeout(300)

    # G. НАВЕДЕНИЕ на ячейку шахматки — title-тултипов нет
    g7 = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        var titles = [];
        var ths = document.querySelectorAll('#wsGridWrap thead th');
        for (var i=0;i<tds.length;i++) {
            var t = tds[i].getAttribute('title');
            if (t) titles.push(t);
        }
        var thTitles = [];
        for (var j=0;j<ths.length;j++) {
            var t2 = ths[j].getAttribute('title');
            if (t2) thTitles.push(t2);
        }
        return { cellTitles: titles.length, headTitles: thTitles.length };
    })()""")
    check('G: ячейки и шапка шахматки — БЕЗ title-атрибутов (0/0)',
          g7['cellTitles'] == 0 and g7['headTitles'] == 0, g7)

    # G2. Наведение на ячейку дня отпуска (12.06, Иванов) — попап не открывается
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-06-12'") !== -1 && oc.indexOf("'017'") !== -1) {
                var r = tds[i].getBoundingClientRect();
                window.__cellXY = [r.left + r.width/2, r.top + r.height/2];
                return;
            }
        }
    })()""")
    xy = page.evaluate("window.__cellXY || [600, 300]")
    page.mouse.move(xy[0], xy[1])
    page.wait_for_timeout(900)
    hov = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var cp = document.getElementById('wsCellPopup');
        return { emp: pp ? pp.classList.contains('active') : null,
                 cell: cp ? cp.classList.contains('active') : null };
    })()""")
    check('G2: наведение на ячейку дня — ни карточки, ни статусного попапа',
          hov['emp'] is False and hov['cell'] is False, hov)
    page.mouse.move(640, 200)
    page.wait_for_timeout(200)

    # H. КЛИК по ячейке ФИО — карточка открывается (единственный триггер)
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    card = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var closer = document.getElementById('wsEmpPopupCloser');
        var txt = pp ? pp.textContent : '';
        return { active: pp ? pp.classList.contains('active') : false,
                 closerActive: closer ? closer.classList.contains('active') : false,
                 txt: txt };
    })()""")
    t = card['txt']
    check('H: клик по ячейке ФИО — карточка открылась, кловер активен',
          card['active'] and card['closerActive'])
    check('H2: строк «Шаблон ротации», секции «Сотрудник», «Итого в году»/«лимит 42» НЕТ',
          t.find('Шаблон ротации') == -1 and t.find('Сменный сутки/двое') == -1 and
          t.find('Дневной 5/2') == -1 and t.find('Итого в году') == -1 and
          t.find('лимит 42') == -1 and t.find('ПРЕВЫШЕН') == -1, t[:300])
    check('H3: поля профиля живы — Тип/Должность/Дата приёма; профиль сразу после шапки',
          t.find('Тип') != -1 and t.find('сменный, смена №1') != -1 and
          t.find('Должность') != -1 and t.find('Слесарь КИПиА') != -1 and
          t.find('15.03.2024') != -1, t[:300])
    check('H4: периоды отпусков живы с чистыми днями «13 дней (−1 праздн.)»',
          t.find('01.06.2026 — 14.06.2026') != -1 and t.find('13 дней') != -1 and
          t.find('(−1 праздн.)') != -1, t[:300])
    page.screenshot(path='scripts/task311-proof-card.png', full_page=False)
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    check('H5: Esc закрыл карточку',
          page.evaluate("!document.getElementById('wsEmpPopup').classList.contains('active')"))

    # I. Петров (43 дн. > 42) — итога в карточке НЕТ, но периоды показаны
    page.click('td.ws-emp-col[data-tab="023"]')
    page.wait_for_timeout(600)
    pet = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        return { active: pp ? pp.classList.contains('active') : false,
                 noTotal: txt.indexOf('Итого в году') === -1,
                 noOver: txt.indexOf('ПРЕВЫШЕН') === -1,
                 hasParts: txt.indexOf('Часть 1') !== -1 && txt.indexOf('Часть 2') !== -1,
                 has14: txt.indexOf('14 дней') !== -1 || txt.indexOf('15 дней') !== -1 };
    })()""")
    check('I: Петров (43>42) — итог/ПРЕВЫШЕНИЕ из карточки убраны, части периодов живы',
          pet['active'] and pet['noTotal'] and pet['noOver'] and pet['hasParts'] and pet['has14'], pet)
    page.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    page.wait_for_timeout(300)

    # J. JS-ошибок нет
    check('J: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
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
    pagem.evaluate("localStorage.setItem('kip8_session_token','browser-check-t311-m')")
    pagem.reload()
    pagem.wait_for_timeout(2500)
    pagem.evaluate("navigateTo('work-schedule')")
    pagem.wait_for_timeout(1500)
    goto_june(pagem)
    # тап по заголовку «Сотрудник» — шторка открывается
    pagem.tap('#wsGridWrap thead th.ws-emp-col')
    pagem.wait_for_timeout(700)
    mob = pagem.evaluate("""(function(){
        var sh = document.getElementById('wsEmpSheet');
        var pp = document.getElementById('wsEmpPopup');
        return { sheetOpen: sh ? sh.classList.contains('active') : false,
                 cardClosed: pp ? !pp.classList.contains('active') : true };
    })()""")
    check('K: 375px — тап по заголовку открывает шторку добавления',
          mob['sheetOpen'] and mob['cardClosed'], mob)
    pagem.evaluate("""(function(){
        var ov = document.getElementById('wsEmpOverlay');
        if (ov) ov.click();
    })()""")
    pagem.wait_for_timeout(500)
    # тап по ячейке ФИО — карточка
    pagem.tap('td.ws-emp-col[data-tab="017"]')
    pagem.wait_for_timeout(600)
    mob2 = pagem.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var r = pp.getBoundingClientRect();
        var txt = pp.textContent;
        return { active: pp.classList.contains('active'),
                 inView: r.left >= 0 && r.right <= window.innerWidth && r.top >= 0,
                 noTotal: txt.indexOf('Итого в году') === -1,
                 noPattern: txt.indexOf('Шаблон ротации') === -1,
                 hasNet: txt.indexOf('13 дней') !== -1 };
    })()""")
    check('K2: 375px — тап по ФИО: карточка в экране, без итога/шаблона, чистые дни живы',
          mob2['active'] and mob2['inView'] and mob2['noTotal'] and
          mob2['noPattern'] and mob2['hasNet'], mob2)
    ovf = pagem.evaluate("(function(){var de=document.documentElement;return {sw:de.scrollWidth,cw:de.clientWidth};})()")
    check('K3: 375px — нет горизонтального переполнения',
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
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t311-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1500)
    goto_june(page2)
    ro = page2.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap thead th.ws-emp-col');
        var plus = th ? th.querySelector('.ws-emp-head-plus') : null;
        var cs = th ? getComputedStyle(th) : null;
        return { cls: th ? th.className : '', onclick: th ? th.getAttribute('onclick') : 'x',
                 plus: !!plus, cursor: cs ? cs.cursor : '' };
    })()""")
    check('M: «ИТР8 pro» — заголовок «Сотрудник» БЕЗ класса/onclick/плюсика',
          'ws-emp-head-add' not in ro['cls'] and (ro['onclick'] is None or ro['onclick'] == '') and
          (not ro['plus']) and ro['cursor'] != 'pointer', ro)
    # клик по заголовку — шторка НЕ открывается (нет прав)
    page2.click('#wsGridWrap thead th.ws-emp-col')
    page2.wait_for_timeout(700)
    ro2 = page2.evaluate("""(function(){
        var sh = document.getElementById('wsEmpSheet');
        return { sheetOpen: sh ? sh.classList.contains('active') : false };
    })()""")
    check('M2: «ИТР8 pro» — клик по заголовку шторку НЕ открывает',
          ro2['sheetOpen'] is False, ro2)
    # клик по ячейке ФИО — карточка доступна для просмотра
    page2.click('td.ws-emp-col[data-tab="017"]')
    page2.wait_for_timeout(600)
    ro3 = page2.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        return { active: pp ? pp.classList.contains('active') : false,
                 hasNet: txt.indexOf('13 дней') !== -1,
                 noTotal: txt.indexOf('Итого в году') === -1,
                 noPattern: txt.indexOf('Шаблон ротации') === -1 };
    })()""")
    check('M3: «ИТР8 pro» — карточка по клику доступна (просмотр), без итога/шаблона',
          ro3['active'] and ro3['hasNet'] and ro3['noTotal'] and ro3['noPattern'], ro3)
    check('N: JS-ошибок нет (просмотр)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task311-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
