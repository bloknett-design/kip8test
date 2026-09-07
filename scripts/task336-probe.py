# -*- coding: utf-8 -*-
# Task 336 probe: диагностика 3 пунктов заявки ДО правок:
#   1) зазор блок картинка+№+Место ↔ верхний бар (мобайл + десктоп);
#   2) сужение фамилий: ширины в .ws-narrow vs фактическая ширина текста
#      «Сотр»/«Иван» (сетка + итоги месяц/год), переходы;
#   3) вертикальная полоса-разделитель в шапке сетки: x-координаты
#      ::after у th.ws-emp-col vs td.ws-emp-col (+ левая граница
#      первого th дня) — в одной ли плоскости.
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
Y, M = datetime.date.today().year, datetime.date.today().month

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
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
]
DEVICES = [
  {'ID':'100','Наименование':'Термометр сопротивления ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1, трубопровод пара','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'kip.view':True,'kip.edit':True}}}
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
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
    return {'ok':True,'data':{'ok':True}}

def setup_ctx(browser, viewport, token, theme='dark'):
    ctx = browser.new_context(viewport=viewport)
    page = ctx.new_page()
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
        route.fulfill(status=404, content_type='text/plain', body='not found (probe t336)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================== МОБАЙЛ 375: карточка + сетка ==================
    print('=== МОБАЙЛ 375 (тёмная) ===')
    ctx, page = setup_ctx(browser, {'width':375,'height':720}, 'probe-t336-m')

    # карточка прибора — зазор до верхнего бара
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1500)
    page.evaluate("devOpenDetail('100')")
    page.wait_for_timeout(1200)
    m_card = page.evaluate("""(function(){
        var pg = document.getElementById('page-device-detail');
        var head = pg ? pg.querySelector('.page-inline-header') : null;
        var top = pg ? pg.querySelector('.dev-detail-top') : null;
        if (!head || !top) return {err:'no els'};
        var hb = head.getBoundingClientRect(), tb = top.getBoundingClientRect();
        return { headerBottom: hb.bottom, topBlockTop: tb.top,
                 gap: tb.top - hb.bottom,
                 scrolled: pg.classList.contains('scrolled') };
    })()""")
    print('M-CARD:', json.dumps(m_card, ensure_ascii=False))

    # сетка — полосы-разделители и сужение
    page.evaluate("navigateTo('docs-ios')"); page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')"); page.wait_for_timeout(1600)
    m_grid = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap ? wrap.querySelector('.ws-grid') : null;
        if (!tbl) return {err:'no grid'};
        var th = tbl.querySelector('thead th.ws-emp-col');
        var td = tbl.querySelector('tbody td.ws-emp-col');
        var day1 = tbl.querySelector('thead th.ws-day-col');
        var hb = th.getBoundingClientRect(), db = td.getBoundingClientRect(), d1b = day1.getBoundingClientRect();
        var st = getComputedStyle(th, '::after');
        function r(el){ var b = el.getBoundingClientRect();
            return {left:b.left, right:b.right, width:b.width}; }
        // тексты для замера ширины
        var headSpan = th.querySelector('.ws-emp-head-txt');
        var empSpan = td.querySelector('.ws-emp-full');
        function txtW(el, s){ var old = el.textContent; el.textContent = s;
            var w = el.getBoundingClientRect().width; el.textContent = old; return w; }
        var headS4W = headSpan ? txtW(headSpan, 'Сотр') : null;
        var empS4W = empSpan ? txtW(empSpan, 'Иван') : null;
        // сужение
        wrap.scrollLeft = 2; wrap.dispatchEvent(new Event('scroll'));
        var thN = th.getBoundingClientRect().width, tdN = td.getBoundingClientRect().width;
        var csTh = getComputedStyle(th), csTd = getComputedStyle(td);
        var thD = getComputedStyle(th, '::after');
        var out = {
            divider: { thRight: hb.right, tdRight: db.right, day1Left: d1b.left,
                       thTdDelta: hb.right - db.right,
                       afterW: st.width, afterRight: st.right,
                       tdBorderStyle: getComputedStyle(td).borderRightWidth + ' ' + getComputedStyle(td).borderRightStyle,
                       thBorderStyle: getComputedStyle(th).borderRightWidth + ' ' + getComputedStyle(th).borderRightStyle },
            textW: { headSotр: headS4W, empIvan: empS4W },
            narrow: { thW: thN, tdW: tdN,
                      thMin: csTh.minWidth, tdMin: csTd.minWidth,
                      thPad: csTh.padding, tdPad: csTd.padding,
                      thTrans: csTh.transitionDuration + ' / ' + csTh.transitionTimingFunction,
                      tdTrans: csTd.transitionDuration },
            afterN: { w: thD.width, right: thD.right }
        };
        wrap.scrollLeft = 0; wrap.dispatchEvent(new Event('scroll'));
        return out;
    })()""")
    print('M-GRID:', json.dumps(m_grid, ensure_ascii=False, indent=1))

    # страница итогов: месяц + год — сужение и ширины
    page.click('#wsTotalsBtn'); page.wait_for_timeout(900)
    m_tt = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b ? b.querySelector('.ws-tt-table') : null;
        if (!t) return {err:'no table'};
        var th = t.querySelector('thead th.ws-tt-emp');
        var td = t.querySelector('tbody td.ws-tt-emp');
        var name = t.querySelector('tbody .ws-tt-name');
        var headSpan = th ? th.querySelector('.ws-tt-emp-head') : null;
        function txtW(el, s){ if(!el) return null; var old = el.textContent; el.textContent = s;
            var w = el.getBoundingClientRect().width; el.textContent = old; return w; }
        var w0 = th.getBoundingClientRect().width;
        b.scrollLeft = 2; b.dispatchEvent(new Event('scroll'));
        var out = {
            cols: t.querySelectorAll('thead th').length,
            w0: w0,
            wNarrow: th.getBoundingClientRect().width,
            narrow: t.classList.contains('ws-narrow'),
            trans: th ? getComputedStyle(th).transitionDuration + ' / ' + getComputedStyle(th).transitionTimingFunction : null,
            textW: { headSotr: txtW(headSpan, 'Сотр'), nameIvan: txtW(name, 'Иван') },
            nameTxt: name ? name.textContent : null
        };
        b.scrollLeft = 0; b.dispatchEvent(new Event('scroll'));
        return out;
    })()""")
    print('M-TT-MONTH:', json.dumps(m_tt, ensure_ascii=False, indent=1))

    # вкладка «Год»
    page.click('[data-tt-tab="year"]'); page.wait_for_timeout(900)
    m_tt_y = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b ? b.querySelector('.ws-tt-table') : null;
        if (!t) return {err:'no table'};
        var th = t.querySelector('thead th.ws-tt-emp');
        var td = t.querySelector('tbody td.ws-tt-emp');
        var name = t.querySelector('tbody .ws-tt-name');
        var headSpan = th ? th.querySelector('.ws-tt-emp-head') : null;
        function txtW(el, s){ if(!el) return null; var old = el.textContent; el.textContent = s;
            var w = el.getBoundingClientRect().width; el.textContent = old; return w; }
        var w0 = th ? th.getBoundingClientRect().width : null;
        if (th) { b.scrollLeft = 2; b.dispatchEvent(new Event('scroll')); }
        var out = {
            hasEmpCol: !!th, w0: w0,
            wNarrow: th ? th.getBoundingClientRect().width : null,
            narrow: t.classList.contains('ws-narrow'),
            trans: th ? getComputedStyle(th).transitionDuration + ' / ' + getComputedStyle(th).transitionTimingFunction : null,
            textW: { headSotr: txtW(headSpan, 'Сотр'), nameIvan: txtW(name, 'Иван') },
            nameTxt: name ? name.textContent : null,
            tableClass: t.className
        };
        b.scrollLeft = 0; b.dispatchEvent(new Event('scroll'));
        return out;
    })()""")
    print('M-TT-YEAR:', json.dumps(m_tt_y, ensure_ascii=False, indent=1))

    page.screenshot(path='scripts/task336-probe-mobile.png')
    ctx.close()

    # ================== ДЕСКТОП 1440: панель карточки ==================
    print('=== ДЕСКТОП 1440 (тёмная) ===')
    ctx, page = setup_ctx(browser, {'width':1440,'height':900}, 'probe-t336-d')

    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1500)
    page.evaluate("devOpenDetail('100')")
    page.wait_for_timeout(1200)
    d_card = page.evaluate("""(function(){
        var panel = document.getElementById('detailPanel');
        var body = document.getElementById('detailPanelBody');
        var bar = document.getElementById('detailBreadcrumbBar');
        var top = body ? body.querySelector('.dev-detail-top') : null;
        if (!body || !top) return {err:'no els', bodyHas: !!body};
        var pb = panel.getBoundingClientRect(), bb = body.getBoundingClientRect(), tb = top.getBoundingClientRect(), brb = bar.getBoundingClientRect();
        var st = getComputedStyle(top);
        var res = {
            panelTop: pb.top, barBottom: brb.bottom, bodyTop: bb.top, topBlockTop: tb.top,
            gapBarToTop: tb.top - brb.bottom,
            gapBodyTopToTop: tb.top - bb.top,
            marginTop: st.marginTop, paddingTop: getComputedStyle(body).paddingTop,
            bodyScrollTop: body.scrollTop
        };
        body.scrollTop = 400;
        res.gapScrolled = top.getBoundingClientRect().top - brb.bottom;
        body.scrollTop = 0;
        return res;
    })()""")
    print('D-CARD:', json.dumps(d_card, ensure_ascii=False, indent=1))
    page.screenshot(path='scripts/task336-probe-desktop.png')

    # сетка десктоп — плоскость полос (если доступна)
    ctx.close()
    browser.close()
print('DONE')
