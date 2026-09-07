# -*- coding: utf-8 -*-
# Task 334: browser-check — заявка пользователя:
#   • КНОПКА «ВИД» — без значков, просто текст «Вид»;
#   • КАРТОЧКА ПРИБОРА — блок картинка + «№ прибора» + «Место
#     установки» НЕ прокручивается по вертикали (sticky под шапкой
#     на мобильной странице / у верха скролл-зоны десктоп-панели);
#   • МОБИЛЬНЫЙ ТАБЕЛЬ: кнопка перекрёстной подсветки УБРАНА; окна
#     «Мероприятия»/«Нормы» ИЗНАЧАЛЬНО СКРЫТЫ (раскрытие чипами);
#     ИТОГИ УЧЁТА — отдельная страница «Итоги учёта» с многострелочным
#     шевроном (3 стрелки по пути дашборд → Документация ИОС → Табель
#     → Итоги) и таблицей с ФАМИЛИЯМИ; при горизонтальной прокрутке
#     шахматки и таблицы итогов колонка ФИО/фамилий сужается до
#     ПЕРВЫХ 4 БУКВ фамилии.
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
ARCHIVE = [
  {'таб_номер':'900','ФИО':'Архивный Аркадий Аркадьевич','тип':'сменный','смена':2,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2020-03-15','дата_увольнения':'2026-06-30','в_архиве':1,'должность':'Слесарь КИПиА','комментарий':''},
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
]
YEAR_ENTRY = lambda m: [
  {'id':100+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'017','статус':'Д8','источник':'авто'},
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'},
] if m <= 6 else []

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
        if body and body.get('includeArchived'):
            return {'ok':True,'data':{'employees':EMPLOYEES + ARCHIVE}}
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

def setup_ctx(browser, viewport, token, theme=None, role='Админ'):
    STATE['role'] = role
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t334)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

# Шаги типичной мобильной навигации: дашборд → Документация ИОС →
# Табель (шахматка). pageHistory после них = [dashboard, docs-ios]
def goto_tab_mobile(page):
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1200)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: МОБИЛЬНЫЙ 375, Админ, тёмная =================
    print('=== Контекст 1: мобильный 375, Админ, тёмная ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'browser-check-t334-a', theme='dark')
    goto_tab_mobile(page)

    # --- кнопка «Вид» без значков ---
    vb = page.evaluate("""(function(){
        var b = document.getElementById('wsViewBtn');
        if (!b) return null;
        return { text: b.textContent.trim(), svgs: b.querySelectorAll('svg').length,
                 label: !!b.querySelector('.ws-view-label') };
    })()""")
    check('M1: кнопка «Вид» — текст «Вид», svg НЕТ', vb and vb['text'] == 'Вид' and vb['svgs'] == 0, vb)

    # --- кнопка подсветки скрыта ---
    cross = page.evaluate("""(function(){
        var b = document.getElementById('wsCrossBtn');
        if (!b) return null;
        return getComputedStyle(b).display;
    })()""")
    check('M2: кнопка перекрёстной подсветки СКРЫТА', cross == 'none', cross)

    # --- окна мероприятий/норм изначально скрыты, чипы видны ---
    panels = page.evaluate("""(function(){
        var e = document.getElementById('wsEventsPanel');
        var c = document.getElementById('wsCalPanel');
        var ch = document.getElementById('wsMobChips');
        return { ev: e ? getComputedStyle(e).display : 'no-el',
                 cal: c ? getComputedStyle(c).display : 'no-el',
                 chips: ch ? getComputedStyle(ch).display : 'no-el' };
    })()""")
    check('M3: окно «Мероприятия» изначально скрыто', panels['ev'] == 'none', panels)
    check('M4: окно «Нормы» изначально скрыто', panels['cal'] == 'none', panels)
    check('M5: ряд чипов виден', panels['chips'] == 'flex', panels)

    # --- чип раскрывает окно ---
    page.click('#wsChipEvents')
    page.wait_for_timeout(100)
    ev_open = page.evaluate("(function(){var e=document.getElementById('wsEventsPanel');return e?getComputedStyle(e).display:'?';})()")
    chip_pressed = page.evaluate("(function(){var c=document.getElementById('wsChipEvents');return c.getAttribute('aria-pressed');})()")
    check('M6: чип «Мероприятия» раскрыл окно', ev_open != 'none' and chip_pressed == 'true', (ev_open, chip_pressed))
    page.click('#wsChipEvents')
    page.wait_for_timeout(100)
    ev_closed = page.evaluate("(function(){var e=document.getElementById('wsEventsPanel');return e?getComputedStyle(e).display:'?';})()")
    check('M7: повторный чип свернул окно', ev_closed == 'none', ev_closed)
    # чип норм
    page.click('#wsChipNorms')
    page.wait_for_timeout(100)
    cal_open = page.evaluate("(function(){var c=document.getElementById('wsCalPanel');return c?getComputedStyle(c).display:'?';})()")
    check('M8: чип «Нормы» раскрыл окно', cal_open != 'none', cal_open)
    page.click('#wsChipNorms')

    # --- сужение ФИО сетки при горизонтальной прокрутке ---
    grid_state = page.evaluate("""(function(){
        var w = document.getElementById('wsGridWrap');
        if (!w) return null;
        w.scrollLeft = 120;
        w.dispatchEvent(new Event('scroll'));
        var t = w.querySelector('table.ws-grid');
        var sp = t ? t.querySelector('td.ws-emp-col .ws-emp-full') : null;
        return { narrow: t ? t.classList.contains('ws-narrow') : null,
                 txt: sp ? sp.textContent : null,
                 tabno: t ? getComputedStyle(t.querySelector('td.ws-emp-col .ws-tab-no')).display : null };
    })()""")
    check('M9: прокрутка сетки → ws-narrow', grid_state and grid_state['narrow'] is True, grid_state)
    check('M10: ФИО сужено до 4 букв («Иван»)', grid_state and grid_state['txt'] == 'Иван', grid_state)
    check('M11: таб. номер скрыт', grid_state and grid_state['tabno'] == 'none', grid_state)
    # возврат прокрутки → полное ФИО
    grid_back = page.evaluate("""(function(){
        var w = document.getElementById('wsGridWrap');
        w.scrollLeft = 0;
        w.dispatchEvent(new Event('scroll'));
        var t = w.querySelector('table.ws-grid');
        var sp = t ? t.querySelector('td.ws-emp-col .ws-emp-full') : null;
        return { narrow: t ? t.classList.contains('ws-narrow') : null,
                 txt: sp ? sp.textContent : null };
    })()""")
    check('M12: возврат прокрутки → полное ФИО', grid_back and grid_back['narrow'] is False and grid_back['txt'] == 'Иванов Иван Иванович', grid_back)

    # --- итоги учёта: страница с 3 шевронами и фамилиями ---
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(800)
    tp = page.evaluate("""(function(){
        var pg = document.getElementById('page-ws-totals');
        if (!pg || !pg.classList.contains('active')) return null;
        var title = pg.querySelector('.page-inline-header-title');
        var chv = pg.querySelector('.page-inline-header-chevron');
        return { active: true,
                 title: title ? title.textContent.trim() : '',
                 arrows: chv ? chv.querySelectorAll('svg').length : 0,
                 monthTab: !!document.getElementById('wsTtPageTabMonth'),
                 yearTab: !!document.getElementById('wsTtPageTabYear') };
    })()""")
    check('M13: итоги открылись СТРАНИЦЕЙ', tp and tp['active'] is True, tp)
    check('M14: заголовок «Итоги учёта»', tp and tp['title'] == 'Итоги учёта', tp)
    check('M15: в шапке ТРИ шеврона (глубина навигации)', tp and tp['arrows'] == 3, tp)
    check('M16: вкладки Месяц/Год на странице', tp and tp['monthTab'] and tp['yearTab'], tp)

    # шторка НЕ открылась на мобильном
    drawer = page.evaluate("(function(){var p=document.getElementById('page-work-schedule');return p?{open:p.classList.contains('ws-tt-open'),panelHidden:document.getElementById('wsTotalsPanel').hidden}:null;})()")
    check('M17: шторка НЕ открывалась (мобильный = страница)', drawer and drawer['open'] is False and drawer['panelHidden'] is True, drawer)

    # таблица с фамилиями
    tt = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b ? b.querySelector('table.ws-tt-table') : null;
        var emp = t ? t.querySelector('td.ws-tt-emp') : null;
        return { table: !!t,
                 empTxt: emp ? emp.textContent : '',
                 hasMonth: t ? t.textContent.indexOf('Явки') !== -1 : false };
    })()""")
    check('M18: таблица итогов на странице', tt and tt['table'], tt)
    check('M19: колонка сотрудника с ФАМИЛИЕЙ', tt and 'Иванов' in tt['empTxt'], tt)

    # вкладка «Год» на странице + сужение итогов при прокрутке
    page.click('#wsTtPageTabYear')
    page.wait_for_timeout(1500)
    yr = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b ? b.querySelector('table.ws-tt-year') : null;
        var wide = b ? b.scrollWidth > b.clientWidth : false;
        return { yearTable: !!t, arch: b ? b.textContent.indexOf('Архив') !== -1 : false,
                 overflow: wide };
    })()""")
    check('M20: вкладка «Год» — годовая таблица', yr and yr['yearTable'], yr)
    check('M21: год шире экрана (есть прокрутка)', yr and yr['overflow'], yr)
    yr_narrow = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        if (!b) return null;
        b.scrollLeft = 60;
        b.dispatchEvent(new Event('scroll'));
        var t = b.querySelector('table.ws-tt-table');
        var sp = t ? t.querySelector('td.ws-tt-emp .ws-tt-name') : null;
        return { narrow: t ? t.classList.contains('ws-narrow') : null,
                 txt: sp ? sp.textContent : null,
                 tabno: t ? getComputedStyle(t.querySelector('.ws-tt-tabno')).display : null };
    })()""")
    check('M22: прокрутка итогов → ws-narrow', yr_narrow and yr_narrow['narrow'] is True, yr_narrow)
    check('M23: фамилия итогов = 4 буквы', yr_narrow and yr_narrow['txt'] == 'Иван', yr_narrow)
    check('M24: таб. номер итогов скрыт', yr_narrow and yr_narrow['tabno'] == 'none', yr_narrow)
    yr_back = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        b.scrollLeft = 0;
        b.dispatchEvent(new Event('scroll'));
        var t = b.querySelector('table.ws-tt-table');
        var sp = t ? t.querySelector('td.ws-tt-emp .ws-tt-name') : null;
        return { narrow: t ? t.classList.contains('ws-narrow') : null,
                 txt: sp ? sp.textContent : null };
    })()""")
    check('M25: возврат → полная фамилия', yr_back and yr_back['narrow'] is False and 'Иванов' in (yr_back['txt'] or ''), yr_back)

    # шеврон страницы: одиночный тап = назад (на табель)
    page.click('#page-ws-totals .page-inline-header-chevron')
    page.wait_for_timeout(600)
    back = page.evaluate("""(function(){
        var ws = document.getElementById('page-work-schedule');
        var tt = document.getElementById('page-ws-totals');
        return { ws: ws.classList.contains('active'), tt: tt.classList.contains('active'),
                 flag: (typeof WorkSchedule !== 'undefined') ? WorkSchedule._ttPage : null };
    })()""")
    check('M26: шеврон вернул на табель, флаг снят', back['ws'] is True and back['tt'] is False and back['flag'] is False, back)

    # --- карточка прибора: sticky блок картинка+№+Место (мобильная страница) ---
    page.evaluate("""(function(){
        navigateTo('device-detail');
    })()""")
    page.wait_for_timeout(400)
    sticky = page.evaluate("""(function(){
        var content = document.getElementById('deviceDetailContent');
        if (!content) return null;
        content.innerHTML = '<div class="dev-detail-card">' +
            '<div class="dev-detail-top" id="t334Top" style="height:120px">TOP</div>' +
            '<div style="height:3000px">BODY</div></div>';
        window.scrollTo(0, 900);
        var top = document.getElementById('t334Top');
        var r = top.getBoundingClientRect();
        window.scrollTo(0, 0);
        return { top: r.top };
    })()""")
    check('M27: карточка прибора — блок №/Место ЛИПКИЙ (~56px под шапкой)',
          sticky and sticky['top'] is not None and abs(sticky['top'] - 56) < 4, sticky)

    check('M28: 0 JS-ошибок (мобильный)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: МОБИЛЬНЫЙ 375, светлая =================
    print('=== Контекст 2: мобильный 375, светлая ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'browser-check-t334-b', theme='light')
    goto_tab_mobile(page)
    light = page.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        var chips = document.getElementById('wsMobChips');
        var ev = document.getElementById('wsEventsPanel');
        var chip = document.querySelector('.ws-mob-chip');
        return { cross: cross ? getComputedStyle(cross).display : null,
                 chips: chips ? getComputedStyle(chips).display : null,
                 ev: ev ? getComputedStyle(ev).display : null,
                 chipBg: chip ? getComputedStyle(chip).backgroundColor : null };
    })()""")
    check('L1: светлая — подсветка скрыта', light['cross'] == 'none', light)
    check('L2: светлая — чипы видны, окно скрыто', light['chips'] == 'flex' and light['ev'] == 'none', light)
    # итоги — страница и в светлой теме
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(800)
    lt = page.evaluate("""(function(){
        var pg = document.getElementById('page-ws-totals');
        var b = document.getElementById('wsTtPageBody');
        return { active: pg.classList.contains('active'),
                 bodyBg: getComputedStyle(b).backgroundColor };
    })()""")
    check('L3: светлая — итоги страницей, фон тела #e9e7de', lt['active'] is True and lt['bodyBg'] == 'rgb(233, 231, 222)', lt)
    check('L4: 0 JS-ошибок (светлая)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 3: ДЕСКТОП 1280, Админ, тёмная =================
    print('=== Контекст 3: десктоп 1280, Админ, тёмная ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t334-c', theme='dark')
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)

    dt = page.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        var chips = document.getElementById('wsMobChips');
        var ev = document.getElementById('wsEventsPanel');
        var cal = document.getElementById('wsCalPanel');
        var vb = document.getElementById('wsViewBtn');
        return { cross: cross ? getComputedStyle(cross).display : null,
                 chips: chips ? getComputedStyle(chips).display : null,
                 ev: ev ? getComputedStyle(ev).display : null,
                 cal: cal ? getComputedStyle(cal).display : null,
                 viewSvgs: vb ? vb.querySelectorAll('svg').length : null,
                 viewText: vb ? vb.textContent.trim() : null };
    })()""")
    check('D1: десктоп — подсветка ВИДИМА', dt['cross'] != 'none', dt)
    check('D2: десктоп — окна-трети бара ВИДНЫ', dt['ev'] != 'none' and dt['cal'] != 'none', dt)
    check('D3: десктоп — чипы скрыты', dt['chips'] == 'none', dt)
    check('D4: десктоп — «Вид» без svg', dt['viewSvgs'] == 0 and dt['viewText'] == 'Вид', dt)

    # итоги — ШТОРКА (не страница) на десктопе
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(800)
    dd = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var tt = document.getElementById('page-ws-totals');
        return { open: p.classList.contains('ws-tt-open'),
                 panelHidden: document.getElementById('wsTotalsPanel').hidden,
                 ttActive: tt.classList.contains('active') };
    })()""")
    check('D5: десктоп — итоги ШТОРКОЙ (ws-tt-open)', dd['open'] is True and dd['panelHidden'] is False and dd['ttActive'] is False, dd)

    # карточка прибора — sticky в панели (синтетический блок)
    page.evaluate("navigateTo('device-detail')")
    page.wait_for_timeout(400)
    dsticky = page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        if (!body) return null;
        body.innerHTML = '<div class="dev-detail-card">' +
            '<div class="dev-detail-top" id="t334TopD" style="height:110px">TOP</div>' +
            '<div style="height:2500px">BODY</div></div>';
        body.scrollTop = 700;
        var r = document.getElementById('t334TopD').getBoundingClientRect();
        body.scrollTop = 0;
        return { top: r.top };
    })()""")
    check('D6: панель — блок №/Место ЛИПКИЙ у верха (≈0px)',
          dsticky and dsticky['top'] is not None and abs(dsticky['top']) < 4, dsticky)

    check('D7: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print('')
print('ИТОГО: %d ✓ / %d ✗' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
