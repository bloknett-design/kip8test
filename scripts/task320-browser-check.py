# -*- coding: utf-8 -*-
# Task 320: browser-check «График работы» — две правки:
#   1) «В выпадающем списке выбора года должно быть три года, до и
#      после текущего» — 7 пунктов (2023..2029 для 2026), было
#      −1…+2 (2025..2028);
#   2) «При добавлении нового сотрудника, не зависимо от времени
#      начала цикла, шахматка его рабочих дней должна строиться с
#      установленной даты, но с учётом выходных и праздничных
#      нерабочих дней (только для дневного, не касается сменного
#      персонала)» — клиентская часть: подсказка календарного
#      режима в шторке «Новый сотрудник» (тип «дневной» — текст
#      про пн–пт/Сб/Вс/праздники, «сменный» — скрыта); тост
#      «Сформировать» с новой строкой «убрано N лишних смен»
#      (removedShift ответа сервера); бейдж плановой смены —
#      паритет _plannedShiftAt (до старта цикла бейджа НЕТ —
#      сервер с Task 320 дни до старта не заполняет).
# Проверки: 3 контекста (десктоп-Админ тёмная, светлая, мобильный
# 375 touch), 0 JS-ошибок, скриншоты.
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404 — фолбэк, как офлайн).
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
  {'code':'ОТ','name':'Отпуск основной','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'}
]
# 017 — сменный, цикл 4 (Д/Н/—/—), старт 10.09: до старта план
# НЕ считается (бейджа нет), 15.09 = день цикла 2 → «Н»
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-10' % (Y, M),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-04' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
] + [
  {'таб_номер':'%03d' % (30 + i),'ФИО':'Сотрудник %02d Тестовый' % (i + 1),'тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-10' % (Y, M),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
  for i in range(8)
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]},
]
ENTRIES = [
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'}
]
TRAININGS = []
# отпуск 06–16 числа текущего месяца: 07 (до старта 10) — план без
# бейджа; 15 (день цикла 2) — план с бейджем «Н»
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':1,'дата_начала':'%04d-%02d-06' % (Y, M),'дата_окончания':'%04d-%02d-16' % (Y, M),'комментарий':''}
]

STATE = {'role': 'Админ', 'generateCalls': 0, 'generatePayloads': []}

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
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.generateMonth':
        STATE['generateCalls'] += 1
        STATE['generatePayloads'].append(body)
        # Task 320: removedShift в ответе — новая строка тоста
        return {'ok':True,'data':{'generated':5,'updated':2,'removed':1,
                                   'vacationDays':3,'removedShift':2,'warnings':[]}}
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
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t320)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t320')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)

# Бейдж плановой смены в ячейке (строка по таб.№ + день месяца)
def cell_badge(page, tab, day):
    return page.evaluate("""(function(a){
        var tab = a[0], day = a[1];
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-emp-col');
            if (emp && emp.getAttribute('data-tab') === tab) {
                var td = trs[i].querySelector('td.ws-cell[data-day=\"'+day+'\"]');
                if (td) {
                    var b = td.querySelector('.ws-ev-shift');
                    var plan = td.classList.contains('ws-vac-plan');
                    return {badge: b ? b.textContent : null, plan: plan};
                }
            }
        }
        return null;
    })""", [tab, day])

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
          page.evaluate("document.documentElement.getAttribute('data-theme')") == 'dark' and
          page.evaluate("document.title==='КИПиА'"))
    check('B: график открыт, сетка отрисована',
          page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- 1. Год: три года до и после текущего ----------
    yr = page.evaluate("""(function(){
        var sel = document.getElementById('wsYearSel');
        var opts = sel.querySelectorAll('option');
        var vals = [];
        for (var i=0;i<opts.length;i++) vals.push(opts[i].value);
        return {n: opts.length, first: vals[0], last: vals[vals.length-1],
                sel: sel.value};
    })()""")
    check('C: год — 7 пунктов (три до + текущий + три после)',
          yr['n'] == 7, yr)
    check('D: год — границы %d..%d' % (Y-3, Y+3),
          int(yr['first']) == Y-3 and int(yr['last']) == Y+3, yr)
    check('E: год — текущий выбран', int(yr['sel']) == Y, yr)
    check('F: год — прежних 4 пунктов нет (−1..+2)',
          yr['n'] != 4 and not (int(yr['first']) == Y-1 and int(yr['last']) == Y+2), yr)

    # ---------- 2. Подсказка календарного режима в шторке ----------
    add_head = page.evaluate("""(function(){
        var th = document.querySelector('th.ws-emp-head-add');
        if (!th) return null;
        var r = th.getBoundingClientRect();
        return [r.left+r.width/2, r.top+r.height/2];
    })()""")
    check('G: заголовок-кнопка «Сотрудник +» есть', add_head is not None)
    if add_head:
        page.mouse.click(add_head[0], add_head[1])
        page.wait_for_timeout(600)
        st = page.evaluate("""(function(){
            var sheet = document.getElementById('wsEmpSheet');
            var hint = document.getElementById('wsEmpCalHint');
            return {sheet: sheet.classList.contains('active'),
                    hintHidden: hint ? hint.hidden : null,
                    hintText: hint ? hint.textContent : ''};
        })()""")
        check('H: шторка «Новый сотрудник» открыта, подсказка скрыта (тип по умолчанию сменный)',
              st['sheet'] and st['hintHidden'] is True, st)
        page.select_select = None
        page.evaluate("""(function(){
            var sel = document.getElementById('wsEmpType');
            sel.value = 'дневной';
            sel.dispatchEvent(new Event('change'));
        })()""")
        page.wait_for_timeout(300)
        st2 = page.evaluate("""(function(){
            var hint = document.getElementById('wsEmpCalHint');
            var style = getComputedStyle(hint);
            return {hidden: hint.hidden, text: hint.textContent,
                    fs: style.fontSize, visible: style.display !== 'none'};
        })()""")
        check('I: тип «дневной» → подсказка видна, текст про пн–пт/Сб/Вс/праздники',
              st2['hidden'] is False and st2['visible'] and
              'пн–пт' in st2['text'] and 'праздничные нерабочие дни' in st2['text'] and
              'пустые выходные' in st2['text'], st2)
        check('J: подсказка компактная (12.5px)', st2['fs'] == '12.5px', st2)
        page.screenshot(path='scripts/task320-proof-hint.png')
        page.evaluate("""(function(){
            var sel = document.getElementById('wsEmpType');
            sel.value = 'сменный';
            sel.dispatchEvent(new Event('change'));
        })()""")
        page.wait_for_timeout(300)
        st3 = page.evaluate("""(function(){
            var hint = document.getElementById('wsEmpCalHint');
            return {hidden: hint.hidden};
        })()""")
        check('K: возврат на «сменный» → подсказка снова скрыта', st3['hidden'] is True, st3)
        page.evaluate("WorkSchedule.closeEmployeeForm()")
        page.wait_for_timeout(400)

    # ---------- 3. Бейдж плановой смены: до старта НЕТ, после — есть ----------
    b07 = cell_badge(page, '017', 7)    # 07-е: до старта (10-е) — план отпуска
    b15 = cell_badge(page, '017', 15)   # 15-е: день цикла 2 → «Н»
    check('L: 07-е (до старта цикла) — план отпуска БЕЗ бейджа (паритет Task 320)',
          b07 is not None and b07['plan'] and not b07['badge'], b07)
    check('M: 15-е (после старта, день цикла 2) — бейдж «Н» на плане отпуска',
          b15 is not None and b15['plan'] and b15['badge'] == 'Н', b15)
    b023 = cell_badge(page, '023', 15)  # дневной — бейджа нет (Task 306)
    check('N: дневной (023) — бейджа плановой смены нет',
          b023 is not None and not b023['badge'], b023)

    # ---------- 4. «Сформировать» → тост с «убрано N лишних смен» ----------
    gen_calls_before = STATE['generateCalls']
    page.evaluate("document.getElementById('wsGenerateBtn').click()")
    page.wait_for_timeout(500)
    dlg = page.evaluate("""(function(){
        var ov = document.getElementById('kipDialogOverlay');
        var alt = ov ? ov.querySelector('.kip-dialog-alt') : null;
        return {active: ov ? ov.classList.contains('active') : false,
                altText: alt ? alt.textContent : null};
    })()""")
    check('O: диалог подтверждения с кнопкой месяца', dlg['active'] and dlg['altText'] is not None, dlg)
    if dlg['active']:
        page.evaluate("document.querySelector('#kipDialogOverlay .kip-dialog-alt').click()")
        page.wait_for_timeout(1500)
        toast = page.evaluate("""(function(){
            var t = document.getElementById('toast');
            var m = document.getElementById('toastMessage');
            return {show: t.classList.contains('show'), text: m.textContent};
        })()""")
        check('P: тост генерации с новой строкой «убрано 2 лишних смен»',
              toast['show'] and 'убрано 2 лишних смен' in toast['text'] and
              'сформировано 5' in toast['text'], toast)
        check('Q: generateMonth вызван (месяц), payload с годом/месяцем',
              STATE['generateCalls'] == gen_calls_before + 1 and
              STATE['generatePayloads'][-1] and
              STATE['generatePayloads'][-1].get('year') == Y and
              STATE['generatePayloads'][-1].get('month') == M,
              STATE['generatePayloads'][-1:])
        page.screenshot(path='scripts/task320-proof-toast.png')

    # смена года — сетка перезагружается с новым годом (список жив)
    page.evaluate("""(function(){
        var sel = document.getElementById('wsYearSel');
        sel.value = String(%d);
        sel.dispatchEvent(new Event('change'));
    })()""" % (Y-3))
    page.wait_for_timeout(1500)
    check('R: выбор %d (нижняя граница списка) — год применился' % (Y-3),
          page.evaluate("document.getElementById('wsYearSel').value") == str(Y-3))
    page.screenshot(path='scripts/task320-proof-years.png')
    # назад к текущему году
    page.evaluate("""(function(){
        var sel = document.getElementById('wsYearSel');
        sel.value = String(%d);
        sel.dispatchEvent(new Event('change'));
    })()""" % Y)
    page.wait_for_timeout(1500)

    check('S: 0 JS-ошибок (контекст 1)', not js_errors, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема, 1024 =================
    ctx2 = browser.new_context(viewport={'width':1024,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    yr2 = page2.evaluate("""(function(){
        var sel = document.getElementById('wsYearSel');
        return {n: sel.querySelectorAll('option').length, sel: sel.value};
    })()""")
    check('T: светлая — год 7 пунктов, текущий выбран',
          yr2['n'] == 7 and int(yr2['sel']) == Y, yr2)
    page2.evaluate("""(function(){
        var th = document.querySelector('th.ws-emp-head-add');
        if (th) th.click();
    })()""")
    page2.wait_for_timeout(600)
    h2 = page2.evaluate("""(function(){
        var hint = document.getElementById('wsEmpCalHint');
        var sel = document.getElementById('wsEmpType');
        sel.value = 'дневной';
        sel.dispatchEvent(new Event('change'));
        var style = getComputedStyle(hint);
        return {hidden: hint.hidden, color: style.color, fs: style.fontSize};
    })()""")
    check('U: светлая — подсказка работает, цвет #777',
          h2['hidden'] is False and h2['color'] == 'rgb(119, 119, 119)' and
          h2['fs'] == '12.5px', h2)
    page2.screenshot(path='scripts/task320-proof-light.png')
    check('V: 0 JS-ошибок (контекст 2)', not js_errors2, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375 touch =================
    ctx3 = browser.new_context(viewport={'width':375,'height':700}, has_touch=True, is_mobile=True)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3, theme='dark')
    mob = page3.evaluate("""(function(){
        var sel = document.getElementById('wsYearSel');
        var cells = document.querySelectorAll('#wsGridWrap td.ws-cell');
        return {n: sel.querySelectorAll('option').length, cells: cells.length,
                first: sel.querySelector('option').value,
                last: sel.querySelectorAll('option')[6].value};
    })()""")
    check('W: мобильный — год 7 пунктов (%d..%d), сетка есть' % (Y-3, Y+3),
          mob['n'] == 7 and int(mob['first']) == Y-3 and int(mob['last']) == Y+3 and
          mob['cells'] > 0, mob)
    page3.screenshot(path='scripts/task320-proof-mobile.png')
    check('X: 0 JS-ошибок (контекст 3)', not js_errors3, js_errors3[:3])
    ctx3.close()

    browser.close()

fails = [r for r in results if not r[1]]
print()
print('ИТОГ: %d/%d passed, %d failed' % (len(results) - len(fails), len(results), len(fails)))
if fails:
    print('ПРОВАЛЕНЫ:')
    for n, _, e in fails:
        print('  ✗', n, '|', e)
sys.exit(1 if fails else 0)
