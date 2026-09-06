# -*- coding: utf-8 -*-
# Task 329: browser-check «Итоги учёта» — заявка пользователя:
#   • кнопка «Ещё» УБРАНА из шапки; на внутренней стороне левого края
#     шторки, ПО СЕРЕДИНЕ — кнопка-значок со стрелкой-ШЕВРОНОМ с тем же
#     функционалом (показать/скрыть доп. столбцы);
#   • по левому краю шторки — небольшой декоративный БОРТИК;
#   • шторка выдвигается РОВНО ПО РАЗМЕРУ СТОЛБЦОВ таблицы; столбцы
#     УЗКИЕ — по заголовкам в 2 строки;
#   • ПЕРЕРАБОТКА — в ДНЯХ (часы — в тултипе);
#   • ЗЕБРА колонки сотрудников шахматки — как строки шторки.
# Проверки (десктоп 1280 Админ): нет #wsTtMore; шеврон на краю
# (left 0, середина высоты, z, svg, rotate 180° в on); бортик 5px
# стальной; ширина шторки = сумма узких столбцов (≈142px свернуто /
# ≈486px развёрнуто), кап 60% (год), маржа 0 при открытии; значения
# переработки — дни, часы в тултипе; зебра ФИО чёт/нечёт; закрытие —
# парковка −ширина; мобайл 375 — fixed-оверлей, шеврон, дни;
# светлая тема — бортик/зебра/шеврон. 0 JS-ошибок.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8943
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
# Иванов (сменный): Д + Н → явки 2, часы 24; д → ПЕРЕРАБОТКА 1 ДЕНЬ (12 ч)
# Петров (дневной): Д8 → явки 1, часы 8; д (часы 7,2) → ПЕРЕРАБОТКА 1 ДЕНЬ (7,2 ч)
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-04' % (Y, M),'таб_номер':'017','статус':'д','источник':'руч'},
  {'id':4,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'023','статус':'д','часы':7.2,'источник':'руч'}
]
# Год: по месяцу Д8; в марце у Иванова «д» → годовая переработка 1 день
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':300+m,'дата':'%04d-%02d-16' % (Y, m),'таб_номер':'017','статус':'д','источник':'руч'}
] if m == 3 else [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
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

def setup_ctx(browser, viewport, token, theme=None):
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t329)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

# Сумма явных узких ширин (CSS/JS Task 329 → 331): свернуто 3 столбца,
# развёрнуто 11; Task 331 — расширены под «Явки (дни)»/«Переработка
# (дни)» в 2 строки (заявка: «вся информация видна, без полоски»)
W_WORK, W_HOURS, W_OVER = 44, 42, 80
W_EXTRA = [42, 64, 50, 52, 50, 38, 38, 50]   # ОВ, Б, ОТ, У, ПР, День, Ночь, Прочие
W_COLLAPSED = W_WORK + W_HOURS + W_OVER
W_EXPANDED = W_COLLAPSED + sum(W_EXTRA)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280px, Админ, тёмная тема =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t329-a', theme='dark')

    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- «Ещё» из шапки удалена; шеврон на левом краю ----------
    s0 = page.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        return {hasMore: !!document.getElementById('wsTtMore'),
                chv: !!document.getElementById('wsTtChv'),
                chvHidden: (function(){var b=document.getElementById('wsTtChv'); return b?b.hidden:null;})(),
                edge: !!drawer.querySelector('.ws-tt-edge'),
                chvInDrawer: (function(){var d=document.getElementById('wsTotalsDrawer'); return !!d.querySelector('#wsTtChv');})(),
                headMore: (function(){var h=document.querySelector('#wsTotalsPanel .ws-tt-head'); return h?h.innerHTML.indexOf('wsTtChv')!==-1:false;})(),
                open: document.getElementById('page-work-schedule').classList.contains('ws-tt-open'),
                dw: drawer.getBoundingClientRect().width,
                dr: drawer.getBoundingClientRect().right};
    })""")
    check('C: кнопки #wsTtMore НЕТ в DOM (заявка)', not s0['hasMore'], s0)
    check('C2: значок #wsTtChv в шторке, шапка его не содержит',
          s0['chv'] and s0['chvInDrawer'] and not s0['headMore'] and s0['chvHidden'], s0)
    check('C3: бортик .ws-tt-edge в шторке', s0['edge'], s0)

    # ---------- открытие ----------
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(600)
    s1 = page.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var body = document.getElementById('wsWsBody') || document.querySelector('.ws-body');
        var chv = document.getElementById('wsTtChv');
        var edge = drawer.querySelector('.ws-tt-edge');
        var chvR = chv.getBoundingClientRect();
        var dr = drawer.getBoundingClientRect();
        var edgeR = edge.getBoundingClientRect();
        var cs = getComputedStyle(chv);
        var bodyR = body.getBoundingClientRect();
        var table = document.querySelector('#wsTtBody table.ws-tt-table');
        return {open: document.getElementById('page-work-schedule').classList.contains('ws-tt-open'),
                chvHidden: chv.hidden, onCls: chv.classList.contains('on'),
                aria: chv.getAttribute('aria-pressed'),
                margin: drawer.style.marginRight, dw: dr.width, drR: dr.right, drH: dr.height,
                chvL: chvR.left - dr.left, chvMid: (chvR.top + chvR.height/2) - (dr.top + dr.height/2),
                chvW: chvR.width, chvH: chvR.height, chvZ: cs.zIndex,
                svg: !!chv.querySelector('svg'),
                edgeW: edgeR.width, edgeH: edgeR.height, edgeL: edgeR.left - dr.left,
                edgeBg: getComputedStyle(edge).backgroundColor,
                edgePe: getComputedStyle(edge).pointerEvents,
                bodyR: bodyR.right,
                tableW: table ? table.getBoundingClientRect().width : null,
                headH: (function(){var th = table ? table.querySelector('thead th.ws-tt-c-over') : null; return th ? th.getBoundingClientRect().height : null;})()};
    })""")
    check('D: шторка открыта, шеврон ВИДЕН (месяц)', s1['open'] and (not s1['chvHidden']), s1)
    check('D2: ширина шторки = сумма столбцов (≈%dpx)' % W_COLLAPSED,
          approx(s1['dw'], W_COLLAPSED, 4), s1['dw'])
    check('D3: таблица = ширина шторки (ровно по столбцам)',
          approx(s1['tableW'], s1['dw'], 2), (s1['tableW'], s1['dw']))
    check('D4: маржа 0 — правый край у границы области',
          s1['margin'] == '0px' and approx(s1['drR'], s1['bodyR'], 2), s1)
    check('D5: шеврон у левого края (left 0), z 6, svg',
          approx(s1['chvL'], 0, 1) and s1['chvZ'] == '6' and s1['svg'], s1)
    check('D6: шеврон по СЕРЕДИНЕ высоты края', approx(s1['chvMid'], 0, 2), s1['chvMid'])
    check('D7: ПОЛОСА левого края 2px во всю высоту, у края, #4a8fc7 (Task 331: как разделитель групп сетки), мышь не мешает',
          approx(s1['edgeW'], 2, 0.4) and approx(s1['edgeH'], s1['drH'], 1)
          and approx(s1['edgeL'], 0, 1) and s1['edgePe'] == 'none'
          and s1['edgeBg'] == 'rgb(74, 143, 199)', s1)

    # ---------- узкие столбцы + заголовки в 2 строки ----------
    s2 = page.evaluate("""(function(){
        var table = document.querySelector('#wsTtBody table.ws-tt-table');
        var ths = table.querySelectorAll('thead th');
        var heads = [], widths = [], contentH = [];
        for (var i=0;i<ths.length;i++){
            heads.push(ths[i].textContent.trim());
            if (i > 0) {
                widths.push(ths[i].getBoundingClientRect().width);
                var r = document.createRange();
                r.selectNodeContents(ths[i]);
                contentH.push(Math.round(r.getBoundingClientRect().height));
            }
        }
        return {heads: heads, widths: widths, contentH: contentH,
                layout: getComputedStyle(table).tableLayout,
                tw: getComputedStyle(table).width,
                hasVsego: heads.indexOf('Всего') !== -1,
                hasTfoot: !!table.querySelector('tfoot'),
                empDisp: getComputedStyle(table.querySelector('tbody td.ws-tt-emp')).display};
    })""")
    check('E: столбцы — Сотрудник, Явки (дни), Часы, Переработка (дни) (Task 331: подписи в днях)',
          s2['heads'] == ['Сотрудник','Явки (дни)','Часы','Переработка (дни)'], s2['heads'])
    check('E2: ширины УЗКИЕ по заголовкам (%d/%d/%d ±2 — Task 331)'
          % (W_WORK, W_HOURS, W_OVER),
          approx(s2['widths'][0], W_WORK, 2) and approx(s2['widths'][1], W_HOURS, 2)
          and approx(s2['widths'][2], W_OVER, 2), s2['widths'])
    check('E3: «Переработка» — в ДВЕ строки (контент вдвое выше однострочных)',
          s2['contentH'][2] >= s2['contentH'][1] * 1.6, s2['contentH'])
    check('E4: без «Всего» и tfoot; ФИО скрыт на десктопе',
          (not s2['hasVsego']) and (not s2['hasTfoot']) and s2['empDisp'] == 'none', s2)

    # ---------- ПЕРЕРАБОТКА В ДНЯХ ----------
    s3 = page.evaluate("""(function(){
        var table = document.querySelector('#wsTtBody table.ws-tt-table');
        var rows = table.querySelectorAll('tbody tr');
        function findRow(tab){
            for (var i=0;i<rows.length;i++){
                var td = rows[i].querySelector('td.ws-tt-emp');
                if (td && td.textContent.indexOf(tab) !== -1) return rows[i];
            }
            return null;
        }
        function row(r){
            var tds = r.querySelectorAll('td');
            var over = r.querySelector('td.ws-tt-over');
            var vals = [];
            for (var j=1;j<tds.length;j++) vals.push(tds[j].textContent.trim());
            return {vals: vals, overTxt: over.textContent.trim(), overTitle: over.getAttribute('title')};
        }
        return {ivan: row(findRow('017')), petr: row(findRow('023'))};
    })""")
    check('F: Иванов — Явки 2, Часы 24, ПЕРЕРАБОТКА 1 ДЕНЬ',
          s3['ivan']['vals'] == ['2','24','1'] and s3['ivan']['overTxt'] == '1', s3['ivan'])
    check('F2: Иванов — часы (12) в ТУЛТИПЕ, не в значении',
          s3['ivan']['overTitle'] == 'часов переработки: 12 (коды д/н)', s3['ivan']['overTitle'])
    check('F3: Петров — ПЕРЕРАБОТКА 1 ДЕНЬ, часы 7,2 в тултипе',
          s3['petr']['overTxt'] == '1' and s3['petr']['overTitle'] == 'часов переработки: 7,2 (коды д/н)', s3['petr'])

    # ---------- ЗЕБРА колонки сотрудников шахматки ----------
    s4 = page.evaluate("""(function(){
        var grid = document.querySelector('#wsGridWrap table.ws-grid');
        var rows = grid.querySelectorAll('tbody tr');
        var out = [];
        for (var i=0;i<4 && i<rows.length;i++){
            var td = rows[i].querySelector('td.ws-emp-col');
            var cs = getComputedStyle(td);
            out.push({i: i, img: cs.backgroundImage, bg: cs.backgroundColor});
        }
        return out;
    })""")
    check('G: зебра ФИО — чётные с градиентом 9%, нечётные без',
          'linear-gradient' in s4[1]['img'] and '0.09' in s4[1]['img']
          and s4[0]['img'] == 'none' and 'linear-gradient' in s4[3]['img'], s4)

    # ---------- шеврон: разворот доп. столбцов ----------
    page.click('#wsTtChv')
    page.wait_for_timeout(400)
    s5 = page.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var chv = document.getElementById('wsTtChv');
        var table = document.querySelector('#wsTtBody table.ws-tt-table');
        var ths = table.querySelectorAll('thead th');
        var heads = [];
        for (var i=1;i<ths.length;i++) heads.push(ths[i].textContent.trim());
        return {dw: drawer.getBoundingClientRect().width, tableW: table.getBoundingClientRect().width,
                on: chv.classList.contains('on'), aria: chv.getAttribute('aria-pressed'),
                heads: heads, hasMinW: table.style.minWidth};
    })""")
    check('H: шеврон ON (aria-pressed=true)', s5['on'] and s5['aria'] == 'true', s5)
    check('H2: шторка переширотилась на 11 столбцов (≈%dpx)' % W_EXPANDED,
          approx(s5['dw'], W_EXPANDED, 6) and approx(s5['tableW'], W_EXPANDED, 6), (s5['dw'], s5['tableW']))
    check('H3: доп. столбцы в порядке ЗАЯВКИ (Task 331: подписи в днях)',
          s5['heads'] == ['Явки (дни)','Часы','Переработка (дни)','Отгул (ОВ)','Больничный (Б)','Отпуск (ОТ)','Уч. отпуск (У)','Прогул (ПР)','День (Д)','Ночь (Н)','Прочие'], s5['heads'])
    check('H4: мин-ширины НЕТ (ширина = столбцы, не прокрутка)',
          not s5['hasMinW'], s5['hasMinW'])
    # обратно
    page.click('#wsTtChv')
    page.wait_for_timeout(400)
    s5b = page.evaluate("(function(){var d=document.getElementById('wsTotalsDrawer'); var c=document.getElementById('wsTtChv'); return {dw: d.getBoundingClientRect().width, on: c.classList.contains('on')};})()")
    check('H5: повторный клик — свернулись (≈%dpx), шеврон OFF' % W_COLLAPSED,
          approx(s5b['dw'], W_COLLAPSED, 4) and not s5b['on'], s5b)
    # пруф: открытая шторка (месяц, свёрнутые столбцы, шеврон, бортик)
    page.screenshot(path='task329-proof-desktop.png', full_page=False)

    # ---------- год: шеврон скрыт, ширина по таблице (кап 60%) ----------
    page.evaluate("WorkSchedule.setTotalsTab('year')")
    page.wait_for_timeout(2500)
    s6 = page.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var chv = document.getElementById('wsTtChv');
        var body = document.querySelector('.ws-body');
        var table = document.querySelector('#wsTtBody table.ws-tt-year');
        var ivan = table ? table.querySelector('tbody tr') : null;
        var over = ivan ? ivan.querySelector('td.ws-tt-over') : null;
        var cap = body.getBoundingClientRect().width * 0.6;
        return {chvHidden: chv.hidden, year: !!table,
                dw: drawer.getBoundingClientRect().width, cap: cap,
                tableW: table ? table.getBoundingClientRect().width : null,
                overTxt: over ? over.textContent.trim() : null,
                overTitle: over ? over.getAttribute('title') : null,
                scroll: document.getElementById('wsTtBody').scrollWidth > document.getElementById('wsTtBody').clientWidth};
    })""")
    check('I: «Год» — шеврон СКРЫТ, таблица годовая', s6['chvHidden'] and s6['year'], s6)
    check('I2: ширина = таблица (не выше капа 60%)',
          approx(s6['dw'], s6['tableW'], 2) and s6['dw'] <= s6['cap'] + 1, (s6['dw'], s6['tableW'], s6['cap']))
    check('I3: годовая ПЕРЕРАБОТКА — 2 ДНЯ (д в марте + текущий), часы в тултипе',
          s6['overTxt'] == '2' and 'часов переработки: 24' in (s6['overTitle'] or ''), s6)

    # ---------- закрытие: парковка −ширина, панель после анимации ----------
    page.evaluate("WorkSchedule.setTotalsTab('month')")
    page.wait_for_timeout(300)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(150)
    s7a = page.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var panel = document.getElementById('wsTotalsPanel');
        var w = drawer.getBoundingClientRect().width;
        return {panelHidden: panel.hidden, margin: drawer.style.marginRight, w: w,
                open: document.getElementById('page-work-schedule').classList.contains('ws-tt-open')};
    })""")
    check('J: закрытие — едет С КОНТЕНТОМ (панель видна), маржа = −ширина',
          (not s7a['panelHidden']) and s7a['margin'] == ('-%dpx' % round(s7a['w'])), s7a)
    page.wait_for_timeout(500)
    s7b = page.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var panel = document.getElementById('wsTotalsPanel');
        return {panelHidden: panel.hidden, margin: drawer.style.marginRight,
                open: document.getElementById('page-work-schedule').classList.contains('ws-tt-open'),
                gridwide: document.getElementById('page-work-schedule').classList.contains('ws-tt-gridwide')};
    })""")
    check('J2: после анимации панель спрятана, классы сняты', s7b['panelHidden'] and (not s7b['open']) and (not s7b['gridwide']), s7b)

    check('K: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375px, Админ =================
    STATE['role'] = 'Админ'
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':720}, 'browser-check-t329-b')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.evaluate("WorkSchedule.toggleTotals()")
    page2.wait_for_timeout(600)
    s8 = page2.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var chv = document.getElementById('wsTtChv');
        var dr = drawer.getBoundingClientRect();
        var table = document.querySelector('#wsTtBody table.ws-tt-table');
        var cs = getComputedStyle(drawer);
        var over = table ? table.querySelector('tbody td.ws-tt-over') : null;
        var emp = table ? table.querySelector('tbody td.ws-tt-emp') : null;
        return {pos: cs.position, transform: cs.transform,
                w: dr.width, vw: window.innerWidth,
                chvHidden: chv.hidden, chvL: chv.getBoundingClientRect().left - dr.left,
                chvMid: (function(){var r=chv.getBoundingClientRect(); return (r.top+r.height/2)-(dr.top+dr.height/2);})(),
                edgeW: drawer.querySelector('.ws-tt-edge').getBoundingClientRect().width,
                overTxt: over ? over.textContent.trim() : null,
                empW: emp ? emp.getBoundingClientRect().width / dr.width : null};
    })""")
    check('L: мобайл — fixed-оверлей ~86vw, шторка на месте',
          s8['pos'] == 'fixed' and s8['transform'] == 'none' and approx(s8['w'], 375*0.86, 4), s8)
    check('L2: шеврон виден (месяц), у левого края, по середине',
          (not s8['chvHidden']) and approx(s8['chvL'], 0, 1) and approx(s8['chvMid'], 0, 2), s8)
    check('L3: ПОЛОСА левого края 2px на мобиле (Task 331)', approx(s8['edgeW'], 2, 0.4), s8)
    check('L4: ПЕРЕРАБОТКА — день (мобайл)', s8['overTxt'] == '1', s8)
    check('L5: колонка ФИО в таблице (≈42%)', s8['empW'] and s8['empW'] > 0.35, s8['empW'])
    # «Ещё» на мобиле — прокрутка развёрнутых столбцов
    page2.click('#wsTtChv')
    page2.wait_for_timeout(300)
    s9 = page2.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var table = body.querySelector('table.ws-tt-table');
        return {minW: table.style.minWidth, scrollable: body.scrollWidth > body.clientWidth,
                ths: table.querySelectorAll('thead th').length};
    })""")
    check('L6: развёрнутые столбцы на мобиле — мин-ширина + прокрутка',
          s9['minW'] and s9['scrollable'] and s9['ths'] == 12, s9)
    page2.screenshot(path='task329-proof-mobile.png', full_page=False)
    check('M: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: светлая тема (десктоп) =================
    STATE['role'] = 'Админ'
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t329-c', theme='light')
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.evaluate("WorkSchedule.toggleTotals()")
    page3.wait_for_timeout(600)
    s10 = page3.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var edge = drawer.querySelector('.ws-tt-edge');
        var chv = document.getElementById('wsTtChv');
        var grid = document.querySelector('#wsGridWrap table.ws-grid');
        var even = grid.querySelectorAll('tbody tr')[1].querySelector('td.ws-emp-col');
        var odd = grid.querySelectorAll('tbody tr')[0].querySelector('td.ws-emp-col');
        var light = document.documentElement.getAttribute('data-theme') === 'light';
        return {light: light,
                edgeBg: getComputedStyle(edge).backgroundColor,
                chvBg: getComputedStyle(chv).backgroundColor, chvColor: getComputedStyle(chv).color,
                evenImg: getComputedStyle(even).backgroundImage,
                oddImg: getComputedStyle(odd).backgroundImage,
                dw: drawer.getBoundingClientRect().width};
    })""")
    check('N: светлая тема включена', s10['light'], s10)
    check('N2: полоса края светлой темы — #6e8ba4, как разделитель сетки (Task 331)',
          'rgb(110, 139, 164)' == s10['edgeBg'], s10['edgeBg'])
    check('N3: зебра ФИО — 7% в светлой теме',
          '0.07' in s10['evenImg'] and s10['oddImg'] == 'none', s10)
    check('N4: шеврон светлой темы ПРОЗРАЧНЫЙ (0.6, Task 331) + ширина та же',
          s10['chvBg'] not in ('', 'rgba(0, 0, 0, 0)') and s10['chvBg'].endswith('0.6)')
          and approx(s10['dw'], W_COLLAPSED, 4), s10)
    page3.screenshot(path='task329-proof-light.png', full_page=False)
    check('O: 0 JS-ошибок (светлая)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
