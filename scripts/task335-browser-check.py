# -*- coding: utf-8 -*-
# Task 335: browser-check — заявка пользователя (правки/баги Task 334):
#   • блок картинка+№+Место вплотную к верхнему бару (scrolled 40px);
#   • плавное сужение колонок фамилий (transition 0.22s, порог 0) +
#     шапка «Сотрудник +» → «Сотр»;
#   • мобильный горизонтальный скролл СРАЗУ (touch-action pan-x pan-y,
#     без предварительного pinch-zoom);
#   • мобильная страница итогов за месяц — ВСЕ столбцы;
#   • опечатка чипа «Мероприятия» → «Мероприятия»;
#   • десктоп: виды «сменные/дневные» НЕ растягивают шахматку до низа.
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
DEVICES = [
  {'ID':'100','Наименование':'Термометр сопротивления ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1, трубопровод пара','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]

STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        admin = STATE['role'] == 'Админ'
        return {'ok':True,'data':{'role':STATE['role'],'found':True,'permissions':{'workschedule.view':True,'workschedule.edit':admin,'flowmeter.view':True,'kip.view':True,'kip.edit':admin}}}
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
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t335)')
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

# дашборд → Документация ИОС → Табель
def goto_tab_mobile(page):
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1200)

RIGHT = 'Меропри' + 'ятия'
TYPO = 'Меропри' + 'вия'

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: МОБИЛЬНЫЙ 375, Админ, тёмная =================
    print('=== Контекст 1: мобильный 375, Админ, тёмная ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'browser-check-t335-a', theme='dark')
    goto_tab_mobile(page)

    # --- чип «Мероприятия» (опечатка исправлена) ---
    chip = page.evaluate("""(function(){
        var b = document.getElementById('wsChipEvents');
        return b ? b.textContent.trim() : null;
    })()""")
    check('M1: чип подписан «%s» (опечатки нет)' % RIGHT, chip == RIGHT, chip)
    check('M1b: опечатки «%s» нет в DOM' % TYPO, TYPO not in page.content())

    # --- мобильный скролл СРАЗУ: pinch-zoom-target переопределён ---
    page.wait_for_timeout(700)  # MutationObserver → assignPinchZoomTargets (300ms)
    ta = page.evaluate("""(function(){
        var t = document.querySelector('#wsGridWrap .ws-grid');
        if (!t) return null;
        return { pz: t.classList.contains('pinch-zoom-target'),
                 ta: getComputedStyle(t).touchAction };
    })()""")
    check('M2: таблица — pinch-zoom-target, touch-action: pan-x pan-y',
          ta and ta['pz'] is True and ta['ta'] == 'pan-x pan-y', ta)

    # --- плавность: transition на колонке ФИО ---
    tr = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap .ws-grid thead th.ws-emp-col');
        var td = document.querySelector('#wsGridWrap .ws-grid tbody td.ws-emp-col');
        return { th: th ? getComputedStyle(th).transitionDuration : null,
                 thProp: th ? getComputedStyle(th).transitionProperty : null,
                 td: td ? getComputedStyle(td).transitionDuration : null };
    })()""")
    check('M3: transition ширины колонки ФИО (0.22s)',
          tr and '0.22s' in tr['th'] and '0.22s' in tr['td']
          and 'width' in (tr['thProp'] or ''), tr)

    # --- сужение в начале прокрутки + «Сотр» ---
    # (программная установка scrollLeft + синхронный Event('scroll') —
    #  приём Task 334)
    nar = page.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        var tbl = wrap.querySelector('.ws-grid');
        var headSpan = tbl.querySelector('thead th.ws-emp-col .ws-emp-head-txt');
        var empSpan = tbl.querySelector('tbody td.ws-emp-col .ws-emp-full');
        var out = {};
        wrap.scrollLeft = 2;   // самое начало прокрутки
        wrap.dispatchEvent(new Event('scroll'));
        out.after2 = { narrow: tbl.classList.contains('ws-narrow'),
                       head: headSpan.textContent, emp: empSpan.textContent };
        wrap.scrollLeft = 80;
        wrap.dispatchEvent(new Event('scroll'));
        out.after80 = { head: headSpan.textContent };
        wrap.scrollLeft = 0;
        wrap.dispatchEvent(new Event('scroll'));
        out.back = { narrow: tbl.classList.contains('ws-narrow'),
                     head: headSpan.textContent, emp: empSpan.textContent };
        return out;
    })()""")
    check('M4: scrollLeft=2 → уже сужено, шапка «Сотр», ФИО «Иван»',
          nar['after2']['narrow'] is True and nar['after2']['head'] == 'Сотр'
          and nar['after2']['emp'] == 'Иван', nar['after2'])
    check('M4b: возврат к 0 → полное «Сотрудник» + ФИО',
          nar['back']['narrow'] is False and nar['back']['head'] == 'Сотрудник'
          and nar['back']['emp'] == 'Иванов Иван Иванович', nar['back'])

    # --- страница итогов: ВСЕ столбцы месяца ---
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    tt = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b ? b.querySelector('.ws-tt-table') : null;
        if (!t) return null;
        var ths = t.querySelectorAll('thead th');
        var names = [];
        for (var i = 0; i < ths.length; i++) names.push(ths[i].textContent.trim());
        var th = t.querySelector('thead th.ws-tt-emp');
        return { cols: names.length, names: names,
                 headSpan: th ? th.querySelector('.ws-tt-emp-head').textContent : null,
                 minW: t.style.minWidth, ta: getComputedStyle(t).touchAction,
                 empTransition: getComputedStyle(th).transitionDuration };
    })()""")
    check('M5: месяц на странице — ВСЕ 12 столбцов', tt and tt['cols'] == 12, tt)
    check('M5b: доп. столбцы в списке',
          tt and 'Отгул (ОВ)' in tt['names'] and 'Прочие' in tt['names'], tt['names'] if tt else tt)
    check('M5c: шапка span «Сотрудник», touch-action pan-x pan-y, transition 0.22s',
          tt and tt['headSpan'] == 'Сотрудник' and tt['ta'] == 'pan-x pan-y'
          and tt['empTransition'] == '0.22s', tt)

    # сужение на странице итогов: шапка → «Сотр»
    nar2 = page.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var t = b.querySelector('.ws-tt-table');
        var headSpan = t.querySelector('thead th.ws-tt-emp .ws-tt-emp-head');
        b.scrollLeft = 60;
        b.dispatchEvent(new Event('scroll'));
        var r = { narrow: t.classList.contains('ws-narrow'), head: headSpan.textContent };
        b.scrollLeft = 0;
        return r;
    })()""")
    check('M6: итоги-страница — сужение: шапка «Сотр»',
          nar2['narrow'] is True and nar2['head'] == 'Сотр', nar2)

    # --- карточка прибора: блок вплотную к бару при прокрутке ---
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(900)
    page.evaluate("devOpenDetail('100')")
    page.wait_for_timeout(600)
    # удлиняем страницу — иначе контент короче окна и .scrolled
    # не активируется (обработчик проверяет docHeight > winHeight)
    page.evaluate("""(function(){
        var f = document.createElement('div');
        f.style.height = '1400px';
        document.getElementById('deviceDetailContent').appendChild(f);
    })()""")
    gap0 = page.evaluate("""(function(){
        var pg = document.getElementById('page-device-detail');
        var head = pg.querySelector('.page-inline-header');
        var top = pg.querySelector('.dev-detail-top');
        window.scrollTo(0, 0);
        return top.getBoundingClientRect().top - head.getBoundingClientRect().bottom;
    })()""")
    page.evaluate("window.scrollTo(0, 400)")
    page.wait_for_timeout(400)
    card = page.evaluate("""(function(){
        var pg = document.getElementById('page-device-detail');
        var head = pg.querySelector('.page-inline-header');
        var top = pg.querySelector('.dev-detail-top');
        var r = { scrolled: pg.classList.contains('scrolled'),
                  headH: head.getBoundingClientRect().height,
                  gapScrolled: top.getBoundingClientRect().top - head.getBoundingClientRect().bottom,
                  stickyTop: getComputedStyle(top).top };
        window.scrollTo(0, 0);
        return r;
    })()""")
    check('M7: карточка — блок вплотную к бару ДО прокрутки', abs(gap0) < 1, gap0)
    check('M8: прокрутка — шапка сжата 40px, блок ПРИМЫКАЕТ (зазор 0)',
          card['scrolled'] is True and abs(card['headH'] - 40) < 1
          and abs(card['gapScrolled']) < 1, card)

    check('M9: 0 JS-ошибок (мобильный)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: ДЕСКТОП 1280, Админ, тёмная =================
    print('=== Контекст 2: десктоп 1280, Админ, тёмная ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t335-b', theme='dark')
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)

    # полный вид: шахматка заполняет окно до низа
    full = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var wrap = document.getElementById('wsGridWrap');
        var rows = wrap.querySelectorAll('tbody tr');
        return { cls: p.classList.contains('ws-view-filtered'),
                 wrapBottom: wrap.getBoundingClientRect().bottom,
                 winH: window.innerHeight,
                 rowH: rows.length ? rows[0].getBoundingClientRect().height : null,
                 rows: rows.length };
    })()""")
    check('D1: полный вид — класс НЕ стоит, таблица до низа окна',
          full['cls'] is False and full['wrapBottom'] > full['winH'] - 30, full)

    # вид «сменные» — шахматка по контенту
    page.click('#wsViewBtn')
    page.wait_for_timeout(700)
    shift = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var wrap = document.getElementById('wsGridWrap');
        var col = document.getElementById('wsGridCol');
        var rows = wrap.querySelectorAll('tbody tr');
        return { cls: p.classList.contains('ws-view-filtered'),
                 rows: rows.length,
                 wrapBottom: wrap.getBoundingClientRect().bottom,
                 winH: window.innerHeight,
                 rowH: rows.length ? rows[0].getBoundingClientRect().height : null,
                 colAlign: getComputedStyle(col).alignSelf,
                 wrapFlex: getComputedStyle(wrap).flexGrow };
    })()""")
    check('D2: вид «сменные» — класс ws-view-filtered, только сменные',
          shift['cls'] is True and shift['rows'] == 11, shift)
    check('D3: шахматка НЕ до низа (по контенту), строки НЕ растянуты',
          shift['wrapBottom'] < shift['winH'] - 60
          and shift['rowH'] <= full['rowH'] + 0.5, shift)
    check('D3b: колонка align-self: flex-start, wrap flex-grow 0',
          shift['colAlign'] == 'flex-start' and shift['wrapFlex'] == '0', shift)

    # вид «дневные» — 1 строка, тоже по контенту
    page.click('#wsViewBtn')
    page.wait_for_timeout(700)
    day = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var wrap = document.getElementById('wsGridWrap');
        var rows = wrap.querySelectorAll('tbody tr');
        return { cls: p.classList.contains('ws-view-filtered'),
                 rows: rows.length,
                 wrapBottom: wrap.getBoundingClientRect().bottom,
                 winH: window.innerHeight };
    })()""")
    check('D4: вид «дневные» — 1 строка, НЕ до низа',
          day['cls'] is True and day['rows'] == 1
          and day['wrapBottom'] < day['winH'] - 200, day)

    # возврат в полный — снова заполнение до низа
    page.click('#wsViewBtn')
    page.wait_for_timeout(700)
    back = page.evaluate("""(function(){
        var p = document.getElementById('page-work-schedule');
        var wrap = document.getElementById('wsGridWrap');
        var rows = wrap.querySelectorAll('tbody tr');
        return { cls: p.classList.contains('ws-view-filtered'),
                 rows: rows.length,
                 wrapBottom: wrap.getBoundingClientRect().bottom,
                 winH: window.innerHeight };
    })()""")
    check('D5: возврат в полный — класс снят, снова до низа',
          back['cls'] is False and back['rows'] == 12
          and back['wrapBottom'] > back['winH'] - 30, back)

    # десктоп: сужение НЕ включается при прокрутке шторки (год);
    # после D5 вид снова полный — «Итоги учёта» доступна
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(800)
    page.click('#wsTtTabYear')
    page.wait_for_timeout(1500)
    gate = page.evaluate("""(function(){
        var b = document.getElementById('wsTtBody');
        var t = b.querySelector('.ws-tt-table');
        var name = t ? t.querySelector('tbody .ws-tt-name') : null;
        b.scrollLeft = 120;
        var r = { narrow: t ? t.classList.contains('ws-narrow') : null,
                  fio: name ? name.textContent : null };
        b.scrollLeft = 0;
        return r;
    })()""")
    check('D6: десктоп — прокрутка шторки НЕ сужает (ФИО полные)',
          gate['narrow'] is False and gate['fio'] == 'Иванов Иван Иванович', gate)

    # десктоп-панель: блок карточки вплотную к бару (margin-top −16)
    page.evaluate("navigateTo('device-detail')")
    page.wait_for_timeout(500)
    panel = page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        if (!body) return null;
        body.innerHTML = '<div class="dev-detail-card">' +
            '<div class="dev-detail-top" id="t335Top" style="height:110px">TOP</div>' +
            '<div style="height:2500px">BODY</div></div>';
        var bodyR = body.getBoundingClientRect().top;
        var top = document.getElementById('t335Top');
        var gap0 = top.getBoundingClientRect().top - bodyR;
        body.scrollTop = 700;
        var gapSc = top.getBoundingClientRect().top - bodyR;
        var mt = getComputedStyle(top).marginTop;
        body.scrollTop = 0;
        return { gap0: gap0, gapSc: gapSc, mt: mt };
    })()""")
    check('D7: панель — блок вплотную (margin-top −16px, зазоры ≈ 0)',
          panel and panel['mt'] == '-16px' and abs(panel['gap0']) < 4
          and abs(panel['gapSc']) < 4, panel)

    check('D8: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print('')
print('ИТОГО: %d ✓ / %d ✗' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
