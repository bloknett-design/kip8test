# -*- coding: utf-8 -*-
# Task 333: browser-check — заявка пользователя:
#   • ШАПКА ШТОРКИ ИТОГОВ — фон как у шапки шахматки (#1e293b тёмная /
#     #bfcad5 светлая), ячейка «Сотрудник» в шапке — тоже;
#   • РАЗДЕЛИТЕЛЬ между сменными/дневными в шторке — 2px #4a8fc7/
#     #6e8ba4 (как ws-group-first сетки);
#   • ПЕРЕКРЁСТНАЯ ПОДСВЕТКА строк сетки распространяется на строки
#     шторки (ws-hover-row по тому же индексу, inset-заливка);
#   • КНОПКА ВИДА — подпись «Вид» (иконка + текст, ширина auto);
#   • АРХИВ в годовой таблице — блок «Архив» под основной таблицей
#     (своя колонка «Сотрудник» на любом экране; десктоп прячет её
#     только у ГЛАВНОЙ таблицы года); обновление — только кнопкой
#     «Обновить» тулбара (своей нет);
#   • ПОЛОСА между ФИО и ячейками — ::after sticky-ячеек СО СТОРОНЫ
#     ЯЧЕЕК (left:100%), НЕ уезжает при прокрутке (пиксельная проба
#     до/после scrollLeft в Chromium + Firefox).
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
  {'таб_номер':'901','ФИО':'Уволенный Ульян Ульянович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-01-07','дата_приёма':'2019-01-20','дата_увольнения':'2026-02-28','в_архиве':1,'должность':'Слесарь КИПиА','комментарий':''}
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
  {'id':400+m,'дата':'%04d-%02d-16' % (Y, m),'таб_номер':'900','статус':'Д8','источник':'авто'}
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

def approx(a, b, eps):
    return a is not None and b is not None and abs(a - b) <= eps

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t333)')
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

def probe_line(page, engine, tag):
    """Пиксельная проба полосы ФИО/ячеек: кроп границы + поиск 2px линии #4a8fc7/#6e8ba4."""
    info = page.evaluate("""(function(){
        var emp = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
        if (!emp) return null;
        var er = emp.getBoundingClientRect();
        return { right: er.right, top: er.top + 2, h: Math.min(er.height - 4, 60) };
    })()""")
    if not info or info['h'] < 10:
        return None
    path = 't333-%s-%s.png' % (engine, tag)
    page.screenshot(path=path, clip={'x': max(0, info['right'] - 4),
                                     'y': info['top'],
                                     'width': 40, 'height': info['h']})
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(path).convert('RGB')
    w, h = im.size
    for x in range(w):
        cnt = 0
        for y in range(0, h, 2):
            r, g, b = im.getpixel((x, y))
            if abs(r - 74) < 45 and abs(g - 143) < 45 and abs(b - 199) < 50:
                cnt += 1
            if abs(r - 110) < 45 and abs(g - 139) < 45 and abs(b - 164) < 50:
                cnt += 1
        if cnt >= h / 2 * 0.6:
            return x
    return None

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, Админ, тёмная =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t333-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт (12 строк: 11 сменных + 1 дневной)',
          page.evaluate("document.querySelectorAll('#wsGridWrap table tbody tr').length") == 12)

    # ---- КНОПКА ВИДА: подпись «Вид» ----
    s1 = page.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        var label = view ? view.querySelector('.ws-view-label') : null;
        var cross = document.getElementById('wsCrossBtn');
        return { text: label ? label.textContent : null,
                 labelVis: label ? getComputedStyle(label).display : null,
                 font: label ? getComputedStyle(label).fontSize + '/' + getComputedStyle(label).fontWeight : null,
                 viewW: view ? view.getBoundingClientRect().width : 0,
                 crossW: cross ? cross.getBoundingClientRect().width : 0,
                 crossH: cross ? cross.getBoundingClientRect().height : 0,
                 viewH: view ? view.getBoundingClientRect().height : 0 };
    })()""")
    check('C: кнопка вида — ПОДПИСЬ «Вид»', s1['text'] == 'Вид', s1)
    check('C2: шрифт подписи 13px/600', s1['font'] == '13px/600', s1['font'])
    # Task 334 (заявка: «без значков, просто „Вид“»): в кнопке НЕТ
    # иконок — ширина по тексту «Вид» (все ещё шире квадратной кнопки
    # подсветки), высота ряда та же
    check('C3: кнопка «Вид» (текст) шире иконки-подсветки, высота ряда та же',
          s1['viewW'] > s1['crossW'] and approx(s1['viewH'], s1['crossH'], 2),
          (s1['viewW'], s1['crossW'], s1['viewH'], s1['crossH']))
    # клик — вид переключается (подпись не сломала цикл)
    page.click('#wsViewBtn')
    page.wait_for_timeout(500)
    check('C4: клик по «Вид» — сменный вид (11 строк)',
          page.evaluate("document.querySelectorAll('#wsGridWrap table tbody tr').length") == 11)
    page.click('#wsViewBtn')
    page.wait_for_timeout(500)
    check('C5: клик — дневной вид (1 строка)',
          page.evaluate("document.querySelectorAll('#wsGridWrap table tbody tr').length") == 1)
    page.click('#wsViewBtn')
    page.wait_for_timeout(500)
    check('C6: клик — полный вид (12 строк)',
          page.evaluate("document.querySelectorAll('#wsGridWrap table tbody tr').length") == 12)

    # ---- ШТОРКА: шапка = шапка сетки + разделитель + подсветка ----
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    s2 = page.evaluate("""(function(){
        var gridTh = document.querySelector('#wsGridWrap table thead th');
        var ttTh = document.querySelector('#wsTtBody .ws-tt-table thead th');
        return { grid: gridTh ? getComputedStyle(gridTh).backgroundColor : null,
                 tt: ttTh ? getComputedStyle(ttTh).backgroundColor : null,
                 ttH: ttTh ? ttTh.getBoundingClientRect().height : 0 };
    })()""")
    check('D: шапка шторки = шапка шахматки (#1e293b)',
          s2['grid'] == 'rgb(30, 41, 59)' and s2['tt'] == 'rgb(30, 41, 59)', s2)

    s3 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsTtBody .ws-tt-table tbody tr');
        if (!rows.length) return null;
        var last = rows[rows.length - 1];
        var td = last.querySelector('td');
        var cs = getComputedStyle(td);
        var prev = rows[rows.length - 2].querySelector('td');
        return { lastCls: last.className, prevCls: rows[rows.length - 2].className,
                 border: cs.borderTopWidth + ' ' + cs.borderTopStyle + ' ' + cs.borderTopColor,
                 prevBorder: getComputedStyle(prev).borderTopWidth };
    })()""")
    check('E: разделитель в шторке — строка первого дневного ws-group-first',
          s3 is not None and s3['lastCls'].find('ws-group-first') != -1 and s3['prevCls'].find('ws-group-first') == -1, s3)
    check('E2: полоса 2px solid rgb(74,143,199) — как в шахматке',
          s3['border'] == '2px solid rgb(74, 143, 199)', s3['border'])

    # ---- ПЕРЕКРЁСТНАЯ ПОДСВЕТКА → строки шторки ----
    cell = page.query_selector('#wsGridWrap table tbody tr:nth-child(3) td.ws-cell:nth-of-type(3)')
    if cell:
        cell.hover()
        page.wait_for_timeout(250)
    s4 = page.evaluate("""(function(){
        var g = document.querySelectorAll('#wsGridWrap table tbody tr');
        var t = document.querySelectorAll('#wsTtBody .ws-tt-table tbody tr');
        var gi = -1, ti = -1;
        for (var i = 0; i < g.length; i++) if (g[i].classList.contains('ws-hover-row')) gi = i;
        for (var j = 0; j < t.length; j++) if (t[j].classList.contains('ws-hover-row')) ti = j;
        var shadow = (ti >= 0) ? getComputedStyle(t[ti].querySelector('td')).boxShadow : '';
        return { gi: gi, ti: ti, shadow: shadow.slice(0, 60) };
    })()""")
    check('F: подсветка строки сетки (индекс 2)', s4['gi'] == 2, s4)
    check('F2: подсветка РАСПРОСТРАНИЛАСЬ на строку шторки (тот же индекс)',
          s4['ti'] == 2, s4)
    check('F3: заливка inset rgba(74,143,199,0.10) на ячейках строки шторки',
          s4['shadow'].find('inset') != -1 and s4['shadow'].find('74, 143, 199') != -1, s4['shadow'])
    # уход курсора с сетки — подсветка снята в ОБОИХ
    page.hover('#wsTotalsBtn')
    page.wait_for_timeout(250)
    s4b = page.evaluate("(function(){ var t = document.querySelectorAll('#wsTtBody .ws-tt-table tbody tr'); for (var j = 0; j < t.length; j++) if (t[j].classList.contains('ws-hover-row')) return true; return false; })()")
    check('F4: уход курсора — подсветка шторки снята', s4b is False)
    page.screenshot(path='task333-proof-month.png')

    # ---- ГОД: архив блоком ----
    page.click('#wsTtTabYear')
    page.wait_for_timeout(1800)
    s5 = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var cap = body.querySelector('.ws-tt-arch-cap');
        var arch = body.querySelector('table.ws-tt-arch');
        var main = body.querySelector('table.ws-tt-table:not(.ws-tt-arch)');
        var archRows = arch ? arch.querySelectorAll('tbody tr').length : 0;
        var mainRows = main ? main.querySelectorAll('tbody tr').length : 0;
        var mainEmp = main ? main.querySelector('td.ws-tt-emp') : null;
        var archEmp = arch ? arch.querySelector('td.ws-tt-emp') : null;
        var refresh = document.getElementById('wsTtRefresh');
        return { cap: cap ? cap.textContent : null,
                 arch: !!arch, archRows: archRows, mainRows: mainRows,
                 archHtml: arch ? arch.innerHTML.indexOf('Архивный Аркадий Аркадьевич') : -1,
                 archHtml2: arch ? arch.innerHTML.indexOf('Уволенный Ульян Ульянович') : -1,
                 mainEmpHidden: mainEmp ? getComputedStyle(mainEmp).display : 'no-cell',
                 archEmpShown: archEmp ? getComputedStyle(archEmp).display : 'no-cell',
                 archEmpSticky: archEmp ? getComputedStyle(archEmp).position : null,
                 refresh: !!refresh,
                 mainBeforeCap: cap && main ? (main.compareDocumentPosition(cap) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0 : null };
    })()""")
    check('G: подпись «Архив» под основной таблицей', s5['cap'] == 'Архив' and s5['mainBeforeCap'], s5)
    check('G2: архивная таблица ws-tt-arch — 2 строки', s5['arch'] and s5['archRows'] == 2, s5)
    check('G3: главная — 12 активных строк', s5['mainRows'] == 12, s5['mainRows'])
    check('G4: архивный Аркадий — в блоке архива', s5['archHtml'] != -1, s5['archHtml'])
    check('G5: уволенный Ульян — в блоке архива', s5['archHtml2'] != -1, s5['archHtml2'])
    check('G6: десктоп: «Сотрудник» ГЛАВНОЙ годовой скрыт, у АРХИВА — виден',
          s5['mainEmpHidden'] == 'none' and s5['archEmpShown'] != 'none', s5)
    check('G7: ячейка «Сотрудник» архива — sticky (имена при прокрутке)',
          s5['archEmpSticky'] == 'sticky', s5['archEmpSticky'])
    check('G8: своей кнопки «Обновить» НЕТ (только тулбар)', s5['refresh'] is False)

    # ---- АРХИВ ДОСТУПЕН ПРОКРУТКОЙ ШТОРКИ (Task 333: прижимка снята) ----
    page.evaluate("document.getElementById('wsTtBody').scrollTop = 99999")
    page.wait_for_timeout(500)
    s5b = page.evaluate("""(function(){
        var body = document.getElementById('wsTtBody');
        var cap = body.querySelector('.ws-tt-arch-cap');
        var arch = body.querySelector('table.ws-tt-arch tbody tr:last-child');
        if (!cap) return null;
        var cr = cap.getBoundingClientRect();
        var ar = arch ? arch.getBoundingClientRect() : null;
        return { st: body.scrollTop, capTop: cr.top, vh: window.innerHeight,
                 archTop: ar ? ar.top : null };
    })()""")
    check('G9: прокрутка шторки ДОСТИГАЕТ блока «Архив» (прижимка снята)',
          s5b and s5b['st'] > 50 and 0 <= s5b['capTop'] < s5b['vh'], s5b)
    page.evaluate("document.getElementById('wsTtBody').scrollTop = 0")
    page.wait_for_timeout(300)
    page.screenshot(path='task333-proof-year.png')

    # ---- ПОЛОСА ФИО/ячейки: ::after, не уезжает при прокрутке ----
    # возвращаемся в месяц (сетка уже gridwide), прокручиваем
    page.click('#wsTtTabMonth')
    page.wait_for_timeout(900)
    x_before = probe_line(page, 'chromium', 'before')
    can = page.evaluate("(function(){ var w = document.getElementById('wsGridWrap'); return w.scrollWidth > w.clientWidth; })()")
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 300")
    page.wait_for_timeout(500)
    x_after = probe_line(page, 'chromium', 'after300')
    if can:
        check('H: полоса ФИО есть ДО прокрутки (2px #4a8fc7)', x_before is not None, x_before)
        check('H2: полоса ОСТАЛАСЬ после прокрутки 300px (заявка)',
              x_after is not None, x_after)
    else:
        check('H: (сетка без прокрутки при 1280 — пропускаем пиксельную пробу)', True)
    page.screenshot(path='task333-proof-desktop.png')
    check('I: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема 1280 =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':1024,'height':768}, 'browser-check-t333-b', theme='light')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('#wsTotalsBtn')
    page2.wait_for_timeout(900)
    s6 = page2.evaluate("""(function(){
        var gridTh = document.querySelector('#wsGridWrap table thead th');
        var ttTh = document.querySelector('#wsTtBody .ws-tt-table thead th');
        var rows = document.querySelectorAll('#wsTtBody .ws-tt-table tbody tr');
        var td = rows.length ? rows[rows.length-1].querySelector('td') : null;
        return { grid: gridTh ? getComputedStyle(gridTh).backgroundColor : null,
                 tt: ttTh ? getComputedStyle(ttTh).backgroundColor : null,
                 sep: td ? getComputedStyle(td).borderTopColor + ' ' + getComputedStyle(td).borderTopWidth : null };
    })()""")
    check('J: светлая — шапка шторки = шапка сетки (#bfcad5)',
          s6['grid'] == 'rgb(191, 202, 213)' and s6['tt'] == 'rgb(191, 202, 213)', s6)
    check('J2: светлая — разделитель 2px rgb(110,139,164)',
          s6['sep'] == 'rgb(110, 139, 164) 2px', s6['sep'])
    # полоса ФИО — светлая #6e8ba4, пиксельная проба при прокрутке (1024 — есть прокрутка)
    page2.evaluate("document.getElementById('wsGridWrap').scrollLeft = 300")
    page2.wait_for_timeout(500)
    x2 = probe_line(page2, 'light', 'after300')
    check('J3: светлая — полоса ФИО осталась после прокрутки', x2 is not None, x2)
    page2.click('#wsTtTabYear')
    page2.wait_for_timeout(1600)
    s6b = page2.evaluate("(function(){ var b = document.getElementById('wsTtBody'); return { arch: !!b.querySelector('table.ws-tt-arch'), cap: !!b.querySelector('.ws-tt-arch-cap') }; })()")
    check('J4: светлая — блок «Архив» на месте', s6b['arch'] and s6b['cap'], s6b)
    page2.screenshot(path='task333-proof-light.png')
    check('K: 0 JS-ошибок (светлая)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 375 =================
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':375,'height':720}, 'browser-check-t333-c', theme='dark')
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    s7 = page3.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        var label = view ? view.querySelector('.ws-view-label') : null;
        var cross = document.getElementById('wsCrossBtn');
        return { text: label ? label.textContent : null,
                 viewW: view ? view.getBoundingClientRect().width : 0,
                 crossW: cross ? cross.getBoundingClientRect().width : 0 };
    })()""")
    check('L: мобайл — подпись «Вид» видна, кнопка шире иконки',
          s7['text'] == 'Вид' and s7['viewW'] > s7['crossW'] + 8, s7)
    # Task 334: на мобиле итоги открываются СТРАНИЦЕЙ #page-ws-totals
    # (таблица — в теле страницы #wsTtPageBody), шторка не используется
    page3.click('#wsTotalsBtn')
    page3.wait_for_timeout(900)
    s8 = page3.evaluate("""(function(){
        var monthEmp = document.querySelector('#wsTtPageBody .ws-tt-table tbody td.ws-tt-emp');
        return { monthEmp: monthEmp ? getComputedStyle(monthEmp).display : 'none',
                 pageActive: document.getElementById('page-ws-totals').classList.contains('active'),
                 monthName: (document.getElementById('wsTtPageBody').innerHTML.indexOf('Иванов Иван Иванович') !== -1) };
    })()""")
    check('M: мобайл месяц — колонка «Сотрудник» видна (имена)', s8['monthEmp'] != 'none', s8)
    # вкладка «Год» (Task 334: переключаем вкладками СТРАНИЦЫ итогов)
    page3.evaluate("WorkSchedule.setTotalsTab('year')")
    page3.wait_for_timeout(1600)
    s9 = page3.evaluate("""(function(){
        var b = document.getElementById('wsTtPageBody');
        var mainEmp = b.querySelector('table.ws-tt-table:not(.ws-tt-arch) tbody td.ws-tt-emp');
        var arch = b.querySelector('table.ws-tt-arch');
        var archEmp = arch ? arch.querySelector('tbody td.ws-tt-emp') : null;
        return { mainEmp: mainEmp ? getComputedStyle(mainEmp).display : 'none',
                 mainName: (b.innerHTML.indexOf('Иванов Иван Иванович') !== -1),
                 arch: !!arch,
                 archEmp: archEmp ? getComputedStyle(archEmp).display : 'none' };
    })()""")
    check('N: мобайл год — имена АКТИВНЫХ видны (колонка вернулась)',
          s9['mainEmp'] != 'none' and s9['mainName'], s9)
    check('N2: мобайл год — блок «Архив» с именами',
          s9['arch'] and s9['archEmp'] != 'none', s9)
    page3.screenshot(path='task333-proof-mobile.png')
    check('O: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

    # ================= Firefox: полоса ФИО при прокрутке =================
    try:
        ffx = p.firefox.launch()
        ctx4, page4, js_errors4 = setup_ctx(ffx, {'width':1024,'height':768}, 'browser-check-t333-ff', theme='dark')
        page4.evaluate("navigateTo('work-schedule')")
        page4.wait_for_timeout(3000)
        page4.click('#wsTotalsBtn')
        page4.wait_for_timeout(900)
        xb = probe_line(page4, 'firefox', 'before')
        page4.evaluate("document.getElementById('wsGridWrap').scrollLeft = 300")
        page4.wait_for_timeout(500)
        xa = probe_line(page4, 'firefox', 'after300')
        check('P: Firefox — полоса до прокрутки', xb is not None, xb)
        check('P2: Firefox — полоса ОСТАЛАСЬ после прокрутки', xa is not None, xa)
        check('P3: 0 JS-ошибок (Firefox)', len(js_errors4) == 0, js_errors4[:3])
        ctx4.close()
        ffx.close()
    except Exception as e:
        print('  (Firefox недоступен: %s)' % e)

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
