# -*- coding: utf-8 -*-
# Task 327: browser-check «Итоги учёта» — заявка пользователя:
#   • строка общего количества УБРАНА (нет tfoot «Итого»);
#   • основные столбцы: Явки, Часы, Переработка (порядок);
#   • дополнительные СКРЫТЫЕ столбцы: Отгул, Больничный, Отпуск,
#     Уч. отпуск, Прогул, День, Ночь, Прочие — кнопка «Ещё»;
#   • столбец «Всего» убран;
#   • столбцы РАВНОЙ ширины; заголовки в 2 строки при надобности;
#   • внизу шторки — БОРДЮРЧИК как у шахматки (5px стальной);
#   • «Месяц»/«Год» ПОЯВЛЯЮТСЯ при открытии шторки.
# Проверки (десктоп 1280 Админ): вкладки скрыты → появились,
# порядок столбцов, равная ширина ±1px, НЕТ Всего/tfoot/Итого,
# «Ещё» → 12 столбцов в порядке заявки + прокрутка, зебра,
# бордюрчик = .ws-grid-foot цвет в цвет у низа, строки итогов
# по строкам сетки, «Год» без Итого, закрытие → вкладки скрыты;
# мобайл 375: шторка 86vw, столбцы, «Ещё». 0 JS-ошибок.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8941
TODAY = datetime.date.today()
TODAY_ISO = TODAY.isoformat()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'.','name':'Плановый выходной','color':'#EEF0F2'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
] + [
  {'таб_номер':'%03d' % (30+i),'ФИО':'Сотрудник %02d Тестовый' % (i+1),'тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
  for i in range(10)
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# Иванов: Д(переработка) + Н + д(ручная) → явки 3, часы 36, перераб 24 (12+12)
# Петров: Д8 + ОТ + И → явки 1, часы 8, перераб 0, отгул 0... отпуск 1, прочие 1
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','переработка':1,'источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-04' % (Y, M),'таб_номер':'017','статус':'д','источник':'руч'},
  {'id':4,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-05' % (Y, M),'таб_номер':'023','статус':'ОТ','источник':'авто'},
  {'id':6,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'023','статус':'И','источник':'авто'}
]
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = []
VACATIONS = []

STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        admin = STATE['role'] == 'Админ'
        return {'ok':True,'data':{'role':STATE['role'],'found':True,'permissions':{'workschedule.view':True,'workschedule.edit':admin,'flowmeter.view':True}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok':True,'data':{'entries':ENTRIES}}
        return {'ok':True,'data':{'entries':YEAR_ENTRY(month or 1)}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def approx(a, b, eps):
    return a is not None and b is not None and abs(a - b) <= eps

def setup_ctx(browser, viewport, token):
    ctx = browser.new_context(viewport=viewport)
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t327)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280px, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t327')

    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- вкладки «Месяц»/«Год» скрыты до открытия ----------
    s0 = page.evaluate("""(function(){
        var m = document.getElementById('wsTtTabMonth');
        var y = document.getElementById('wsTtTabYear');
        return {mHidden: m ? m.hidden : null, yHidden: y ? y.hidden : null,
                mDisp: m ? getComputedStyle(m).display : null};
    })""")
    check('C: «Месяц»/«Год» СКРЫТЫ до открытия шторки (заявка)',
          s0['mHidden'] and s0['yHidden'] and s0['mDisp'] == 'none', s0)

    # ---------- открытие: вкладки появляются ----------
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(500)
    s1 = page.evaluate("""(function(){
        var m = document.getElementById('wsTtTabMonth');
        var y = document.getElementById('wsTtTabYear');
        var chv = document.getElementById('wsTtChv');
        return {mHidden: m ? m.hidden : null, yHidden: y ? y.hidden : null,
                mDisp: m ? getComputedStyle(m).display : null,
                chvHidden: chv ? chv.hidden : null,
                open: document.getElementById('page-work-schedule').classList.contains('ws-tt-open')};
    })""")
    check('D: шторка открыта, «Месяц»/«Год» ПОЯВИЛИСЬ (заявка)',
          s1['open'] and (not s1['mHidden']) and (not s1['yHidden']) and s1['mDisp'] != 'none', s1)
    check('D2: шеврон доп. столбцов виден (месяц; Task 329: функционал «Ещё» на краю)',
          (not s1['chvHidden']), s1)

    # ---------- таблица: столбцы/порядок/равная ширина ----------
    s2 = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var table = body.querySelector('table.ws-tt-table');
        if (!table) return null;
        var ths = table.querySelectorAll('thead th');
        var heads = [];
        var widths = [];
        for (var i=0;i<ths.length;i++){
            heads.push(ths[i].textContent.trim());
            if (i > 0) widths.push(ths[i].getBoundingClientRect().width);
        }
        var txt = body.textContent;
        var rows = table.querySelectorAll('tbody tr');
        // значения первой строки (Иванов)
        var tds = rows[0] ? rows[0].querySelectorAll('td') : [];
        var vals = [];
        for (var j=1;j<tds.length;j++) vals.push(tds[j].textContent.trim());
        var cs = getComputedStyle(table);
        var th0 = getComputedStyle(ths[1]);
        return {heads: heads, widths: widths, layout: cs.tableLayout,
                thWS: th0.whiteSpace, thWrap: th0.overflowWrap, thAlign: th0.textAlign,
                hasTotal: txt.indexOf('Итого') !== -1, hasVsego: heads.indexOf('Всего') !== -1,
                hasTfoot: !!table.querySelector('tfoot'),
                rowCount: rows.length, ivanov: vals,
                empDisp: getComputedStyle(table.querySelector('tbody td.ws-tt-emp')).display};
    })""")
    check('E: столбцы — Сотрудник, Явки (дни), Часы, Переработка (дни) (ПОРЯДОК — заявка; Task 331: подписи в днях)',
          s2['heads'] == ['Сотрудник','Явки (дни)','Часы','Переработка (дни)'], s2['heads'])
    check('E2: НЕТ «Всего», НЕТ tfoot, НЕТ «Итого» (заявка)',
          (not s2['hasVsego']) and (not s2['hasTfoot']) and (not s2['hasTotal']))
    w = s2['widths']
    # Task 329 → 331 (актуализация): столбцы УЗКИЕ по заголовкам
    # (44/42/80 — расширены под «Явки (дни)»/«Переработка (дни)» в 2
    # строки, заявка: «вся информация видна, без полоски прокрутки»)
    check('E3: столбцы данных УЗКИЕ по заголовкам (Task 329/331: 44/42/80)',
          len(w) == 3 and approx(w[0], 44, 2) and approx(w[1], 42, 2) and approx(w[2], 80, 2), w)
    check('E4: table-layout fixed + перенос заголовков + центр',
          s2['layout'] == 'fixed' and s2['thWS'] == 'normal' and
          s2['thWrap'] in ('break-word','anywhere') and s2['thAlign'] == 'center',
          (s2['layout'], s2['thWS'], s2['thWrap'], s2['thAlign']))
    # Task 322 semantics (действующая): д/н — ДНИ ПЕРЕРАБОТКИ, не явки:
    # Иванов: Д+Н = 2 явки/24 ч; д (сменный) = +1 ДЕНЬ переработки
    # (Task 329: переработка в ДНЯХ, не часах)
    check('E5: Иванов — явки 2 (Д+Н), часы 24, переработка 1 ДЕНЬ (Task 329)',
          s2['ivanov'] == ['2','24','1'], s2['ivanov'])
    check('E6: 12 строк сотрудников (без итоговой)', s2['rowCount'] == 12, s2['rowCount'])

    # ---------- «Ещё»: скрытые доп. столбцы ----------
    page.evaluate("WorkSchedule.toggleTotalsExtra()")
    page.wait_for_timeout(300)
    s3 = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var table = body.querySelector('table.ws-tt-table');
        var ths = table.querySelectorAll('thead th');
        var heads = [];
        for (var i=0;i<ths.length;i++) heads.push(ths[i].textContent.trim());
        var chv = document.getElementById('wsTtChv');
        var drawer = document.getElementById('wsTotalsDrawer');
        var w = table.getBoundingClientRect().width;
        var rows = table.querySelectorAll('tbody tr');
        var tds = rows[rows.length - 1] ? rows[rows.length - 1].querySelectorAll('td') : [];
        var pv = [];
        for (var j=1;j<tds.length;j++) pv.push(tds[j].textContent.trim());
        var tds0 = rows[0].querySelectorAll('td');
        var iv = [];
        for (var j=1;j<tds0.length;j++) iv.push(tds0[j].textContent.trim());
        return {heads: heads,
                chvOn: chv.classList.contains('on'),
                chvAria: chv.getAttribute('aria-pressed'),
                tableW: w, drawerW: drawer.getBoundingClientRect().width,
                petrov: pv, ivanov: iv};
    })""")
    expected = ['Сотрудник','Явки (дни)','Часы','Переработка (дни)','Отгул (ОВ)','Больничный (Б)',
                'Отпуск (ОТ)','Уч. отпуск (У)','Прогул (ПР)','День (Д)','Ночь (Н)','Прочие']
    check('F: «Ещё» — 8 доп. столбцов в ПОРЯДКЕ ЗАЯВКИ (заявка; Task 331: подписи в днях)',
          s3['heads'] == expected, s3['heads'])
    check('F2: шеврон ON + aria-pressed (Task 329)',
          s3['chvOn'] and s3['chvAria'] == 'true')
    # Task 329 → 331 (актуализация): шторка ПЕРЕШИРИВАЕТСЯ по столбцам
    # (~550px на десктопе — без прокрутки при капе 60%; 44/42/80)
    check('F3: шторка переширотилась по 11 столбцам (Task 329/331)',
          approx(s3['drawerW'], 44+42+80+42+64+50+52+50+38+38+50, 6), s3['drawerW'])
    # Иванов (Task 322/329): явки 2, часы 24, перераб 1 ДЕНЬ, день 1 (Д), ночь 1 (Н)
    check('F4: Иванов доп. — День 1, Ночь 1 (д — только переработка)',
          s3['ivanov'] == ['2','24','1','0','0','0','0','0','1','1','0'], s3['ivanov'])
    # Петров — ПОСЛЕДНЯЯ строка (сменные выше): явки 1 (Д8), часы 8,
    # отпуск 1 (ОТ), день 1, прочие 1 (И)
    check('F5: Петров доп. — Отпуск 1, День 1, Прочие 1',
          s3['petrov'] == ['1','8','0','0','0','1','0','0','1','0','1'], s3['petrov'])
    page.evaluate("WorkSchedule.toggleTotalsExtra()")
    page.wait_for_timeout(200)

    # ---------- бордюрчик ----------
    s4 = page.evaluate("""(function(){
        var panel = document.getElementById('wsTotalsPanel');
        var foot = panel.querySelector('.ws-tt-foot');
        if (!foot) return null;
        var fr = foot.getBoundingClientRect();
        var pr = panel.getBoundingClientRect();
        var cs = getComputedStyle(foot);
        var gridFoot = document.querySelector('.ws-grid-foot');
        var gcs = gridFoot ? getComputedStyle(gridFoot) : null;
        var gfr = gridFoot ? gridFoot.getBoundingClientRect() : { bottom: -999 };
        var hbar = document.getElementById('wsTtHbar');
        // зебра (фон — на TR, td прозрачны)
        var rows = document.querySelectorAll('#wsTtBody tbody tr');
        var b1 = getComputedStyle(rows[0]).backgroundColor;
        var b2 = getComputedStyle(rows[1]).backgroundColor;
        // строки итогов по строкам сетки
        var gRows = document.querySelectorAll('#wsGridWrap tbody tr');
        var t1 = rows[0].getBoundingClientRect().top;
        var g1 = gRows[0] ? gRows[0].getBoundingClientRect().top : null;
        return {h: fr.height, atBottom: Math.abs(fr.bottom - gfr.bottom) <= 1.5,
                bg: cs.backgroundColor, bt: cs.borderTopColor, bb: cs.borderBottomColor,
                gridBg: gcs ? gcs.backgroundColor : null,
                gridBt: gcs ? gcs.borderTopColor : null,
                hbarBelow: hbar ? (hbar.getBoundingClientRect().top >= fr.bottom - 1.5) : false,
                hbarH: hbar ? hbar.getBoundingClientRect().height : 0,
                zebra: b1 !== b2,
                rowTop: t1, gridTop: g1, rowDelta: g1 !== null ? Math.abs(t1 - g1) : null};
    })""")
    check('G: БОРДЮРЧИК внизу шторки — 5px, ТОТ ЖЕ стальной bevel (заявка; Task 331: уровень = бордюру сетки, ниже — зона ползунка 12px)',
          approx(s4['h'], 5, 0.6) and s4['atBottom'] and
          s4['bg'] == s4['gridBg'] and s4['bt'] == s4['gridBt'] and
          s4['hbarBelow'] and s4['hbarH'] > 0,
          (s4['h'], s4['bg'], s4['gridBg'], s4['bt'], s4['gridBt'], s4['hbarBelow'], s4['hbarH']))
    check('G2: зебра строк сохранена', s4['zebra'])
    check('G3: строки итогов — по строкам сетки (±3px)',
          s4['rowDelta'] is not None and s4['rowDelta'] <= 3, s4['rowDelta'])

    # ---------- «Год» ----------
    page.evaluate("WorkSchedule.setTotalsTab('year')")
    page.wait_for_timeout(1800)
    s5 = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var table = body.querySelector('table.ws-tt-table');
        var chv = document.getElementById('wsTtChv');
        var txt = body.textContent;
        var rows = table ? table.querySelectorAll('tbody tr') : [];
        // годовые суммы Иванова (месяц 36 + 11×12 = 168)
        var tds = rows[0] ? rows[0].querySelectorAll('td') : [];
        var last3 = [];
        for (var j = tds.length - 3; j < tds.length; j++) last3.push(tds[j].textContent.trim());
        return {hasTfoot: table ? !!table.querySelector('tfoot') : null,
                hasItogo: txt.indexOf('Итого') !== -1,
                chvHidden: chv ? chv.hidden : null,
                yearCls: table ? table.classList.contains('ws-tt-year') : null,
                last3: last3, rowCount: rows.length};
    })""")
    check('H: «Год» — НЕТ итоговой строки (заявка)',
          (not s5['hasTfoot']) and (not s5['hasItogo']))
    check('H2: «Год» — шеврон доп. столбцов скрыт', s5['chvHidden'])
    # Иванов год: явки 2 (месяц) + 11 (по Д в каждом) = 13; часы 24+132=156;
    # переработка 1 ДЕНЬ (единственный д — в текущем месяце; Task 329)
    check('H3: «Год» — таблица года (12 колонок), суммы 13/156/1 (дни)',
          s5['yearCls'] and s5['rowCount'] == 12 and s5['last3'][0] == '13' and
          s5['last3'][1] == '156' and s5['last3'][2] == '1', (s5['last3'], s5['rowCount']))

    # ---------- закрытие: вкладки убираются ----------
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(450)
    s6 = page.evaluate("""(function(){
        var m = document.getElementById('wsTtTabMonth');
        return {mHidden: m ? m.hidden : null,
                open: document.getElementById('page-work-schedule').classList.contains('ws-tt-open')};
    })""")
    check('I: закрытие — «Месяц»/«Год» убраны (заявка)',
          (not s6['open']) and s6['mHidden'], s6)

    check('J: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобильный 375px =================
    STATE['role'] = 'Админ'
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':812}, 'browser-check-t327-m')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.evaluate("WorkSchedule.toggleTotals()")
    page2.wait_for_timeout(500)
    s7 = page2.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var table = body.querySelector('table.ws-tt-table');
        var ths = table.querySelectorAll('thead th');
        var heads = [];
        for (var i=0;i<ths.length;i++) heads.push(ths[i].textContent.trim());
        var emp = table.querySelector('tbody td.ws-tt-emp');
        var chv = document.getElementById('wsTtChv');
        var drawer = document.getElementById('wsTotalsDrawer');
        var r = drawer.getBoundingClientRect();
        return {heads: heads, empW: emp ? emp.getBoundingClientRect().width : null,
                empVisible: emp ? getComputedStyle(emp).display !== 'none' : null,
                chvHidden: chv.hidden, drawerW: r.width};
    })""")
    check('K: мобайл — шторка ~86vw', approx(s7['drawerW'], 322.5, 30), s7['drawerW'])
    check('K2: мобайл — колонка ФИО видна, основные столбцы (Task 331: подписи в днях)',
          s7['empVisible'] and s7['heads'] == ['Сотрудник','Явки (дни)','Часы','Переработка (дни)'], s7['heads'])
    check('K3: мобайл — шеврон доп. столбцов доступен (Task 329)', not s7['chvHidden'])
    page2.evaluate("WorkSchedule.toggleTotalsExtra()")
    page2.wait_for_timeout(300)
    s8 = page2.evaluate("(function(){var t=document.querySelector('#wsTtBody table'); var ths=t.querySelectorAll('thead th'); var b=document.getElementById('wsTtBody'); return {cols: ths.length, scrollable: b.scrollWidth > b.clientWidth + 2};})()")
    check('K4: мобайл шеврон — 12 столбцов + прокрутка (мин-ширина)',
          s8['cols'] == 12 and s8['scrollable'], s8)
    page2.evaluate("WorkSchedule.toggleTotals()")
    page2.wait_for_timeout(450)
    check('K5: мобайл — закрытие (вкладки убраны)',
          page2.evaluate("(function(){var m=document.getElementById('wsTtTabMonth'); return m.hidden;})()"))
    check('K6: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('ИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
