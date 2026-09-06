# -*- coding: utf-8 -*-
# Task 331: browser-check «Итоги учёта» — заявка пользователя:
#   • при открытии шторки — НЕТ полосок вертикальной прокрутки ни в
#     шторке, ни в шахматке (нативные полосы скрыты во всех движках);
#   • шеврон — в ДВА РАЗА УЖЕ (11px) и ПРОЗРАЧНЕЕ;
#   • левый бордюрчик — ПОЛОСА 2px как разделитель сменных/дневных;
#   • полоска горизонтальной прокрутки шторки — ПОД нижним бордюром
#     (как под шахматкой), при неполном открытии — НЕТ полоски, вся
#     информация видна;
#   • высота шапки столбцов шторки = высоте шапки шахматки;
#   • «Явки (дни)» / «Переработка (дни)» (+ год «Перераб. (дни)»);
#   • текст шапки/значений — ПО ЦЕНТРУ;
#   • нижний бордюр шторки ВСЕГДА на уровне бордюра шахматки.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
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
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-04' % (Y, M),'таб_номер':'017','статус':'д','источник':'руч'},
  {'id':4,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'023','статус':'д','часы':7.2,'источник':'руч'}
]
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':300+m,'дата':'%04d-%02d-16' % (Y, m),'таб_номер':'017','статус':'д','источник':'руч'}
] if m == 3 else [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'}
]

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t331)')
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

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, Админ, тёмная =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t331-a', theme='dark')

    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(700)
    s = page.evaluate("""(function(){
        var gw = document.getElementById('wsGridWrap');
        var tb = document.getElementById('wsTtBody');
        var ghb = document.getElementById('wsGridHbar');
        var thb = document.getElementById('wsTtHbar');
        var grid = document.querySelector('#wsGridWrap table.ws-grid');
        var tt = document.querySelector('#wsTtBody table.ws-tt-table');
        var gfoot = document.getElementById('wsGridFoot');
        var tfoot = document.querySelector('#wsTotalsPanel .ws-tt-foot');
        var chv = document.getElementById('wsTtChv');
        var edge = document.querySelector('.ws-tt-edge');
        var ttHead = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var r = function(el){ return el ? el.getBoundingClientRect().toJSON() : null; };
        var ths = tt ? tt.querySelectorAll('thead th') : [];
        var heads = [];
        for (var i=1;i<ths.length;i++) heads.push(ths[i].textContent.trim());
        var td = tt ? tt.querySelector('tbody td.ws-tt-num') : null;
        var tds = tt ? tt.querySelectorAll('tbody tr td:nth-child(2)') : [];
        return {
          gw: {vbar: gw.offsetWidth - gw.clientWidth, hbar: gw.offsetHeight - gw.clientHeight,
               sw: gw.scrollWidth, cw: gw.clientWidth},
          tb: {vbar: tb.offsetWidth - tb.clientWidth, hbar: tb.offsetHeight - tb.clientHeight,
               sw: tb.scrollWidth, cw: tb.clientWidth},
          ghb: {on: ghb.classList.contains('on'), r: r(ghb)},
          thb: {on: thb.classList.contains('on'), r: r(thb)},
          gthead: r(grid ? grid.querySelector('thead') : null),
          tthead: r(tt ? tt.querySelector('thead') : null),
          ttHead: r(ttHead),
          headDisp: ttHead ? getComputedStyle(ttHead).display : null,
          gfoot: r(gfoot), tfoot: r(tfoot),
          gtr: r(grid ? grid.querySelector('tbody tr') : null),
          ttr: r(tt ? tt.querySelector('tbody tr') : null),
          chv: r(chv), chvBg: getComputedStyle(chv).backgroundColor,
          edge: r(edge), edgeBg: getComputedStyle(edge).backgroundColor,
          heads: heads,
          dw: document.getElementById('wsTotalsDrawer').getBoundingClientRect().width,
          thAlign: ths.length ? getComputedStyle(ths[1]).textAlign : null,
          thVA: ths.length ? getComputedStyle(ths[1]).verticalAlign : null,
          thH: ths.length ? getComputedStyle(ths[1]).height : null,
          tdAlign: tds.length ? getComputedStyle(tds[0]).textAlign : null,
          tdTxt: tds.length ? tds[0].textContent.trim() : null,
          gridTheadH: grid ? getComputedStyle(grid.querySelector('thead')).height : null
        };
    })""")

    # 1) НЕТ полосок вертикальной прокрутки (оба контейнера)
    check('C: НЕТ верт. полоски в ШТОРКЕ (native vbar=0)', s['tb']['vbar'] == 0, s['tb'])
    check('C2: НЕТ верт. полоски в ШАХМАТКЕ (native vbar=0)', s['gw']['vbar'] == 0, s['gw'])
    # 4) при неполном открытии — без полоски прокрутки, всё видно
    check('D: свёрнуто: вся таблица видна (sw=cw), НЕТ полоски (thb off)',
          s['tb']['sw'] <= s['tb']['cw'] + 1 and not s['thb']['on'], (s['tb'], s['thb']['on']))
    check('D2: ширина шторки = 44+42+80 = 166 (вся информация видна)',
          approx(s['dw'], 166, 3), s['dw'])
    # 5) шапки равны
    check('E: шапка столбцов шторки = шапке сетки (высоты 38/38 ±0.5, одна полоса)',
          approx(s['tthead']['height'], s['gthead']['height'], 0.5)
          and approx(s['tthead']['top'], s['gthead']['top'], 0.5), (s['tthead'], s['gthead']))
    check('E2: thead th height=38px', s['thH'] and approx(float(s['thH'].replace('px','')), 38, 0.6), s['thH'])
    check('E3: шапка шторки (strip) ПРЯЧЕТСЯ в месяце (display:none)',
          s['headDisp'] == 'none', s['headDisp'])
    check('E4: ПЕРВЫЕ строки на одном уровне',
          approx(s['ttr']['top'], s['gtr']['top'], 1.5), (s['ttr']['top'], s['gtr']['top']))
    # 8) бордюры на одном уровне
    check('F: нижний бордюр шторки = бордюру шахматки (±1px)',
          approx(s['tfoot']['bottom'], s['gfoot']['bottom'], 1), (s['tfoot'], s['gfoot']))
    check('F2: ЗОНЫ ползунков под бордюрами на одном уровне (12px)',
          approx(s['thb']['r']['top'], s['ghb']['r']['top'], 1)
          and approx(s['thb']['r']['height'], 12, 0.6)
          and approx(s['ghb']['r']['height'], 12, 0.6), (s['thb']['r'], s['ghb']['r']))
    # 2) шеврон
    check('G: шеврон ВДВОЕ УЖЕ (11px) и прозрачнее rgba(...,0.55)',
          approx(s['chv']['width'], 11, 0.6) and s['chvBg'].endswith('0.55)'), (s['chv']['width'], s['chvBg']))
    # 3) полоса левого края
    check('H: левый бордюрчик — ПОЛОСА 2px #4a8fc7 (как разделитель сетки)',
          approx(s['edge']['width'], 2, 0.4) and s['edgeBg'] == 'rgb(74, 143, 199)',
          (s['edge']['width'], s['edgeBg']))
    # 6) подписи в днях
    check('I: заголовки «Явки (дни)», «Часы», «Переработка (дни)»',
          s['heads'] == ['Явки (дни)', 'Часы', 'Переработка (дни)'], s['heads'])
    # 7) центр
    check('J: текст шапки по центру, vertical-align middle',
          s['thAlign'] == 'center' and s['thVA'] == 'middle', (s['thAlign'], s['thVA']))
    check('J2: ячейки значений по центру',
          s['tdAlign'] == 'center', s['tdAlign'])
    page.screenshot(path='task331-proof-month.png')

    # ---------- разворот шевроном: 550px, ползунка нет ----------
    page.click('#wsTtChv')
    page.wait_for_timeout(500)
    s2 = page.evaluate("""(function(){
        var tb = document.getElementById('wsTtBody');
        var thb = document.getElementById('wsTtHbar');
        var gfoot = document.getElementById('wsGridFoot');
        var tfoot = document.querySelector('#wsTotalsPanel .ws-tt-foot');
        return {dw: document.getElementById('wsTotalsDrawer').getBoundingClientRect().width,
                sw: tb.scrollWidth, cw: tb.clientWidth,
                on: thb.classList.contains('on'),
                gfb: gfoot.getBoundingClientRect().bottom,
                tfb: tfoot.getBoundingClientRect().bottom};
    })""")
    check('K: разворот: 11 столбцов (550px), прокрутки НЕТ (ползунок не появился)',
          approx(s2['dw'], 550, 4) and s2['sw'] <= s2['cw'] + 1 and not s2['on'], s2)
    check('K2: бордюры на одном уровне и в развёрнутом виде',
          approx(s2['tfb'], s2['gfb'], 1), (s2['tfb'], s2['gfb']))
    page.click('#wsTtChv')
    page.wait_for_timeout(400)

    # ---------- ГОД: шапка «Обновить», подпись (дни), ползунки по месту ----------
    page.evaluate("WorkSchedule.setTotalsTab('year')")
    page.wait_for_timeout(2500)
    s3 = page.evaluate("""(function(){
        var tb = document.getElementById('wsTtBody');
        var thb = document.getElementById('wsTtHbar');
        var tt = document.querySelector('#wsTtBody table.ws-tt-year');
        var grid = document.querySelector('#wsGridWrap table.ws-grid');
        var ttHead = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var ths = tt ? tt.querySelectorAll('thead th') : [];
        var over = ths.length ? ths[ths.length-1].textContent.trim() : null;
        return {ttHeadDisp: ttHead ? getComputedStyle(ttHead).display : null,
                ttHeadH: ttHead ? ttHead.getBoundingClientRect().height : null,
                tthead: tt ? tt.querySelector('thead').getBoundingClientRect().toJSON() : null,
                gthead: grid ? grid.querySelector('thead').getBoundingClientRect().toJSON() : null,
                over: over,
                sw: tb.scrollWidth, cw: tb.clientWidth,
                on: thb.classList.contains('on'),
                gfb: document.getElementById('wsGridFoot').getBoundingClientRect().bottom,
                tfb: document.querySelector('#wsTotalsPanel .ws-tt-foot').getBoundingClientRect().bottom};
    })""")
    # Task 332 (заявка): кнопки «Обновить» шапки больше нет; ⚠ скрыт —
    # шапка ПРЯЧЕТСЯ ЦЕЛИКОМ (Task 331), высота головной зоны года = 0
    check('L: ГОД: шапки шторки НЕТ (кнопка «Обновить» удалена, ⚠ скрыт)',
          s3['ttHeadDisp'] == 'none' and approx(s3['ttHeadH'], 0, 1.5), (s3['ttHeadDisp'], s3['ttHeadH']))
    check('L2: ГОД: годовая колонка «Перераб. (дни)»', s3['over'] == 'Перераб. (дни)', s3['over'])
    check('L3: ГОД: шапка сетки = голова(0)+thead(38) (строки ровно, Task 332: без «Обновить»)',
          approx(s3['gthead']['height'], s3['ttHeadH'] + s3['tthead']['height'], 1.5),
          (s3['gthead']['height'], s3['ttHeadH'], s3['tthead']['height']))
    check('L4: ГОД: бордюры на одном уровне',
          approx(s3['tfb'], s3['gfb'], 1), (s3['tfb'], s3['gfb']))
    page.screenshot(path='task331-proof-year.png')

    # месяц обратно + закрытие
    page.evaluate("WorkSchedule.setTotalsTab('month')")
    page.wait_for_timeout(400)
    page.evaluate("WorkSchedule.toggleTotals()")
    page.wait_for_timeout(600)
    s4 = page.evaluate("""(function(){
        return {gridwide: document.getElementById('page-work-schedule').classList.contains('ws-tt-gridwide'),
                panelHidden: document.getElementById('wsTotalsPanel').hidden,
                ghbOn: document.getElementById('wsGridHbar').classList.contains('on'),
                thbOn: document.getElementById('wsTtHbar').classList.contains('on')};
    })""")
    check('M: закрытие: классы сняты, ползунки погашены',
          (not s4['gridwide']) and s4['panelHidden'] and (not s4['ghbOn']) and (not s4['thbOn']), s4)
    check('N: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: узкий десктоп 1024 — ползунки ЖИВЫЕ =================
    STATE['role'] = 'Админ'
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':1024,'height':800}, 'browser-check-t331-b', theme='dark')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.evaluate("WorkSchedule.toggleTotals()")
    page2.wait_for_timeout(700)
    s5 = page2.evaluate("""(function(){
        var gw = document.getElementById('wsGridWrap');
        var ghb = document.getElementById('wsGridHbar');
        var thb = document.getElementById('wsTtHbar');
        var tb = document.getElementById('wsTtBody');
        return {gw: {sw: gw.scrollWidth, cw: gw.clientWidth, vbar: gw.offsetWidth - gw.clientWidth},
                ghbOn: ghb.classList.contains('on'),
                ghbR: ghb.getBoundingClientRect().toJSON(),
                thumb: ghb.querySelector('.ws-hbar-thumb').style.width,
                thbOn: thb.classList.contains('on'),
                tb: {sw: tb.scrollWidth, cw: tb.clientWidth, vbar: tb.offsetWidth - tb.clientWidth}};
    })""")
    check('O: 1024: сетка переполнена — КАСТОМНЫЙ ползунок шахматки ВИДЕН',
          s5['gw']['sw'] > s5['gw']['cw'] + 1 and s5['ghbOn'] and s5['thumb'], s5)
    check('O2: 1024: ползунок ПОД бордюром шахматки (зона 12px)',
          approx(s5['ghbR']['height'], 12, 0.6), s5['ghbR'])
    check('O3: 1024: НЕТ верт. полосок (обе зоны), свёрнутая шторка БЕЗ полоски',
          s5['gw']['vbar'] == 0 and s5['tb']['vbar'] == 0 and (not s5['thbOn']), s5)
    # ПЕРЕТАСКИВАНИЕ бегунка сетки
    tr = s5['ghbR']
    cx, cy = tr['left'] + 30, tr['top'] + tr['height'] / 2
    page2.mouse.move(cx, cy); page2.mouse.down()
    page2.mouse.move(cx + 150, cy, steps=10); page2.mouse.up()
    page2.wait_for_timeout(300)
    s6 = page2.evaluate("""(function(){
        var gw = document.getElementById('wsGridWrap');
        var t = document.getElementById('wsGridHbar').querySelector('.ws-hbar-thumb');
        return {sl: gw.scrollLeft, tl: t.style.left};
    })""")
    check('P: DRAG ползунка сетки: прокрутка по бегунку (scrollLeft>100)',
          s6['sl'] > 100 and float(s6['tl'].replace('px','0') or 0) >= 0, s6)
    # ГОД на 1024: ползунок ШТОРКИ включается + перетаскивание
    page2.evaluate("WorkSchedule.setTotalsTab('year')")
    page2.wait_for_timeout(2200)
    s7 = page2.evaluate("""(function(){
        var tb = document.getElementById('wsTtBody');
        var thb = document.getElementById('wsTtHbar');
        var t = thb.querySelector('.ws-hbar-thumb');
        return {sw: tb.scrollWidth, cw: tb.clientWidth, on: thb.classList.contains('on'),
                tw: t.style.width, r: thb.getBoundingClientRect().toJSON(),
                footB: document.querySelector('#wsTotalsPanel .ws-tt-foot').getBoundingClientRect().bottom};
    })""")
    # Task 332/333: годовая таблица УЖЕ без «Сотрудника» на десктопе и
    # влезает в ширину шторки (архива в этом моке нет) — ползунок НЕ
    # включён (заявка Task 331: «без переполнения зона ПУСТАЯ»), но зона
    # 12px ПОД бордюром зарезервирована всегда
    check('Q: ГОД@1024: таблица влезает — ползунок ПУСТ, зона 12px ПОД бордюром',
          (not s7['on']) and s7['sw'] <= s7['cw'] + 1
          and approx(s7['r']['height'], 12, 0.6)
          and s7['r']['top'] >= s7['footB'] - 1, s7)
    if s7['on']:
        t2 = s7['r']
        cx2, cy2 = t2['left'] + 40, t2['top'] + t2['height'] / 2
        page2.mouse.move(cx2, cy2); page2.mouse.down()
        page2.mouse.move(cx2 + 120, cy2, steps=10); page2.mouse.up()
        page2.wait_for_timeout(300)
        s8 = page2.evaluate("(function(){var tb=document.getElementById('wsTtBody'); return {sl: tb.scrollLeft};})")
        check('R: DRAG ползунка шторки: таблица года прокрутилась',
              s8['sl'] > 50, s8)
    else:
        check('R: DRAG ползунка шторки (пропущен: ползунок не включён)', True)
    page2.screenshot(path='task331-proof-1024-year.png')
    check('S: 0 JS-ошибок (1024)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 375 =================
    STATE['role'] = 'Админ'
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':375,'height':720}, 'browser-check-t331-c')
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.evaluate("WorkSchedule.toggleTotals()")
    page3.wait_for_timeout(700)
    s9 = page3.evaluate("""(function(){
        var drawer = document.getElementById('wsTotalsDrawer');
        var chv = document.getElementById('wsTtChv');
        var edge = document.querySelector('.ws-tt-edge');
        var thb = document.getElementById('wsTtHbar');
        var tb = document.getElementById('wsTtBody');
        return {pos: getComputedStyle(drawer).position, w: drawer.getBoundingClientRect().width,
                chvW: chv.getBoundingClientRect().width,
                edgeW: edge.getBoundingClientRect().width,
                thbOn: thb.classList.contains('on'),
                tb: {sw: tb.scrollWidth, cw: tb.clientWidth},
                footB: document.querySelector('#wsTotalsPanel .ws-tt-foot').getBoundingClientRect().bottom,
                hbarT: thb.getBoundingClientRect().top};
    })""")
    check('T: мобайл: fixed-оверлей, шеврон 11px, полоса 2px, БЕЗ полоски',
          s9['pos'] == 'fixed' and approx(s9['chvW'], 11, 0.6)
          and approx(s9['edgeW'], 2, 0.4) and (not s9['thbOn']), s9)
    # разворот на мобиле: ползунок шторки появляется под бордюром
    page3.click('#wsTtChv')
    page3.wait_for_timeout(400)
    s10 = page3.evaluate("""(function(){
        var thb = document.getElementById('wsTtHbar');
        var tb = document.getElementById('wsTtBody');
        return {on: thb.classList.contains('on'),
                sw: tb.scrollWidth, cw: tb.clientWidth,
                footB: document.querySelector('#wsTotalsPanel .ws-tt-foot').getBoundingClientRect().bottom,
                hbarT: thb.getBoundingClientRect().top};
    })""")
    check('U: мобайл развёрнуто: ползунок шторки ПОД бордюром (переполнение)',
          s10['on'] and s10['sw'] > s10['cw'] + 1
          and s10['hbarT'] >= s10['footB'] - 1, s10)
    page3.screenshot(path='task331-proof-mobile.png')
    check('V: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 4: светлая тема =================
    STATE['role'] = 'Админ'
    ctx4, page4, js_errors4 = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t331-d', theme='light')
    page4.evaluate("navigateTo('work-schedule')")
    page4.wait_for_timeout(3000)
    page4.evaluate("WorkSchedule.toggleTotals()")
    page4.wait_for_timeout(700)
    s11 = page4.evaluate("""(function(){
        var edge = document.querySelector('.ws-tt-edge');
        var chv = document.getElementById('wsTtChv');
        var ghb = document.getElementById('wsGridHbar');
        var thb = document.getElementById('wsTtHbar');
        var tfoot = document.querySelector('#wsTotalsPanel .ws-tt-foot');
        var gfoot = document.getElementById('wsGridFoot');
        return {light: document.documentElement.getAttribute('data-theme') === 'light',
                edgeBg: getComputedStyle(edge).backgroundColor,
                chvBg: getComputedStyle(chv).backgroundColor,
                gfb: gfoot.getBoundingClientRect().bottom,
                tfb: tfoot.getBoundingClientRect().bottom,
                thbOn: thb.classList.contains('on')};
    })""")
    check('W: светлая: полоса края #6e8ba4 (разделитель сетки)',
          s11['edgeBg'] == 'rgb(110, 139, 164)', s11['edgeBg'])
    check('W2: светлая: шеврон прозрачный 0.6, бордюры на одном уровне',
          s11['chvBg'].endswith('0.6)') and approx(s11['tfb'], s11['gfb'], 1), (s11['chvBg'], s11['tfb'], s11['gfb']))
    page4.screenshot(path='task331-proof-light.png')
    check('X: 0 JS-ошибок (светлая)', len(js_errors4) == 0, js_errors4[:3])
    ctx4.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
