# -*- coding: utf-8 -*-
# Task 332: browser-check — заявка пользователя:
#   • ПОДСКАЗКА кнопки перекрёстной подсветки (информационное окно
#     #wsCrossTip, формат «Обновить»/«Сформировать»: заголовок +
#     описание + живое состояние);
#   • НОВАЯ кнопка переключения ВИДА ТАБЕЛЯ #wsViewBtn слева от
#     значка подсветки: 1 полный (все элементы), 2 сменный (нет
#     шахматки дневных и шторки), 3 дневной (нет шахматки сменных
#     и шторки) + своя подсказка #wsViewTip; роль «КИП ИОС
#     дежурный» — только вид 2 (сменный), кнопка заперта;
#   • шторка «Год»: кнопка «Обновить» УДАЛЕНА, столбца «Сотрудник»
#     НЕТ (строки года = строки сетки, без архива);
#   • РАЗДЕЛИТЕЛЬНАЯ ПОЛОСА между столбцом сотрудников и ячейками
#     шахматки — 2px #4a8fc7 / светлая #6e8ba4 (как разделитель
#     сменных/дневных и левая полоса шторки).
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
# архивный сотрудник — ТОЛЬКО в справочнике года (includeArchived),
# в таблице года его быть НЕ должно (Task 332)
ARCHIVE = [
  {'таб_номер':'900','ФИО':'Архивный Аркадий Аркадьевич','тип':'сменный','смена':2,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2020-03-15','дата_увольнения':'2026-06-30','в_архиве':1,'должность':'Слесарь КИПиА','комментарий':''}
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
  {'id':200+m,'дата':'%04d-%02d-15' % (Y, m),'таб_номер':'023','статус':'Д8','источник':'авто'}
] + ([{'id':300+m,'дата':'%04d-%02d-16' % (Y, m),'таб_номер':'017','статус':'д','источник':'руч'}] if m == 3 else [])

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
        # годовой справочник — с архивом; сетка/месяц — только активные
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t332)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

def grid_rows(page):
    return page.evaluate("document.querySelectorAll('#wsGridWrap table tbody tr').length")

def toast_text(page):
    return page.evaluate("(function(){ var t = document.querySelector('.toast, .kip-toast, #toastBox'); return t ? t.textContent : ''; })()")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, Админ, тёмная =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t332-a', theme='dark')

    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт', page.evaluate("!!document.querySelector('#wsGridWrap table')"))
    check('B2: полный вид по умолчанию — 12 строк (11 сменных + 1 дневной)', grid_rows(page) == 12, grid_rows(page))

    # ---- КНОПКА ВИДА: позиция/размер/иконки ----
    s1 = page.evaluate("""(function(){
        var row = document.getElementById('wsActionsRow');
        var view = document.getElementById('wsViewBtn');
        var cross = document.getElementById('wsCrossBtn');
        var gen = document.getElementById('wsGenerateBtn');
        if (!row || !view) return null;
        var r = view.getBoundingClientRect();
        var rc = cross.getBoundingClientRect();
        var icons = {
            full: document.getElementById('wsViewIconFull'),
            shift: document.getElementById('wsViewIconShift'),
            day: document.getElementById('wsViewIconDay')
        };
        var vis = {};
        for (var k in icons) vis[k] = icons[k] ? !icons[k].hidden : null;
        return { r: {x:r.x, y:r.y, w:r.width, h:r.height},
                 crossX: rc.x, genX: gen ? gen.getBoundingClientRect().x : -1,
                 locked: view.classList.contains('ws-view-locked'),
                 aria: view.getAttribute('aria-label'),
                 vis: vis, inRow: !!row.querySelector('#wsViewBtn'),
                 first: row.querySelector('button') === view,
                 title: view.getAttribute('title') };
    })""")
    check('C: #wsViewBtn в ряду 3, САМАЯ ЛЕВАЯ (левее подсветки)',
          s1['inRow'] and s1['first'] and s1['r']['x'] < s1['crossX'], s1)
    # десктоп: бар ≥1024 — кнопки во всю высоту ряда (~29,7px); Task 333:
    # у кнопки вида ПОДПИСЬ «Вид» — она ШИРЕ иконки-подсветки (34px),
    # высота — та же (ряд)
    s1c = page.evaluate("(function(){ var c=document.getElementById('wsCrossBtn').getBoundingClientRect(); var v=document.getElementById('wsViewBtn').getBoundingClientRect(); return {cw:c.width, ch:c.height, vw:v.width, vh:v.height}; })()")
    check('C2: кнопка вида — ШИРЕ значка (подпись «Вид»), высота ряда та же',
          s1c['vw'] > s1c['cw'] + 20 and approx(s1c['vh'], s1c['ch'], 1), s1c)
    check('C3: НЕТ нативного title (подсказка — информационное окно)', not s1['title'])
    check('C4: полный вид: видна иконка Full, Shift/Day скрыты',
          s1['vis']['full'] and not s1['vis']['shift'] and not s1['vis']['day'], s1['vis'])

    # ---- ПОДСКАЗКА кнопки ВИДА (информационное окно) ----
    page.hover('#wsViewBtn')
    page.wait_for_timeout(350)
    s2 = page.evaluate("""(function(){
        var tip = document.getElementById('wsViewTip');
        var btn = document.getElementById('wsViewBtn');
        var br = btn.getBoundingClientRect();
        var tr = tip.getBoundingClientRect();
        return { hidden: tip.hidden, inBody: tip.parentNode === document.body,
                 title: document.getElementById('wsViewTipTitle').textContent,
                 desc: document.getElementById('wsViewTipDesc').textContent,
                 pe: getComputedStyle(tip).pointerEvents,
                 above: tr.bottom <= br.top + 2, near: Math.abs(tr.left - br.left) < 40 };
    })()""")
    check('D: #wsViewTip показан при НАВЕДЕНИИ (в <body>, pointer-events none)',
          (not s2['hidden']) and s2['inBody'] and s2['pe'] == 'none', s2)
    check('D2: заголовок «Вид табеля: полный» + описание трёх видов',
          s2['title'] == 'Вид табеля: полный' and 'полный' in s2['desc'] and 'сменный' in s2['desc'] and 'дневной' in s2['desc'], s2)
    check('D3: окно НАД кнопкой, по горизонтали у кнопки', s2['above'] and s2['near'], s2)

    # ---- ПОДСКАЗКА значка ПОДСВЕТКИ ----
    page.hover('#wsCrossBtn')
    page.wait_for_timeout(350)
    s3 = page.evaluate("""(function(){
        var tip = document.getElementById('wsCrossTip');
        return { hidden: tip.hidden,
                 title: tip.querySelector('.ws-rt-date').textContent,
                 state: document.getElementById('wsCrossTipState').textContent,
                 desc: tip.querySelector('.ws-rt-desc').textContent };
    })()""")
    check('E: #wsCrossTip показан: заголовок + живое состояние «включена»',
          (not s3['hidden']) and s3['title'] == 'Перекрёстная подсветка строк и столбцов' and s3['state'] == 'включена', s3)
    # переключение — состояние в подсказке живое
    page.click('#wsCrossBtn')
    page.wait_for_timeout(200)
    s3b = page.evaluate("document.getElementById('wsCrossTipState').textContent")
    check('E2: после выключения подсказка обновилась («выключена»)', s3b == 'выключена', s3b)
    page.click('#wsCrossBtn')  # вернуть вкл
    page.wait_for_timeout(200)

    # ---- ПЕРЕКЛЮЧЕНИЕ ВИДА: сменный ----
    page.click('#wsViewBtn')
    page.wait_for_timeout(500)
    s4 = page.evaluate("""(function(){
        var icons = { shift: document.getElementById('wsViewIconShift') };
        return { rows: document.querySelectorAll('#wsGridWrap table tbody tr').length,
                 vis: !icons.shift.hidden,
                 totalsHidden: document.getElementById('wsTotalsBtn').hidden,
                 tabM: document.getElementById('wsTtTabMonth').hidden,
                 tabY: document.getElementById('wsTtTabYear').hidden,
                 aria: document.getElementById('wsViewBtn').getAttribute('aria-label'),
                 saved: localStorage.getItem('kip8_ws_view_v1'),
                 dayRows: (function(){ var n=0; var trs=document.querySelectorAll('#wsGridWrap table tbody tr td.ws-emp-col'); for (var i=0;i<trs.length;i++){ if (trs[i].textContent.indexOf('дневной') !== -1) n++; } return n; })() };
    })""")
    check('F: сменный вид — 11 строк, дневных НЕТ', s4['rows'] == 11 and s4['dayRows'] == 0, s4)
    check('F2: иконка Shift видна, «Итоги учёта» и вкладки скрыты',
          s4['vis'] and s4['totalsHidden'] and s4['tabM'] and s4['tabY'], s4)
    check('F3: aria-label «…сменный», выбор сохранён (kip8_ws_view_v1)',
          'сменный' in s4['aria'] and s4['saved'] == 'shift', s4)
    check('F4: шторка НЕ открывается программно из сменного вида (гейт)',
          page.evaluate("(function(){ WorkSchedule.toggleTotals(); return WorkSchedule._totalsOpen; })()") == False)
    check('F5: тост «Сменный вид» после клика', 'сменный' in (toast_text(page) or '').lower(), toast_text(page))
    page.screenshot(path='task332-proof-shift.png')

    # подсказка в сменном виде — заголовок сменный (мышь УВОДИМ:
    # повторный hover без ухода НЕ зажигает mouseenter заново)
    page.mouse.move(500, 500)
    page.wait_for_timeout(150)
    page.hover('#wsViewBtn')
    page.wait_for_timeout(300)
    s4b = page.evaluate("document.getElementById('wsViewTipTitle').textContent")
    check('F6: подсказка вида: «Вид табеля: сменный»', s4b == 'Вид табеля: сменный', s4b)
    page.mouse.move(500, 500)
    page.wait_for_timeout(150)

    # ---- ПЕРЕКЛЮЧЕНИЕ ВИДА: дневной ----
    page.click('#wsViewBtn')
    page.wait_for_timeout(500)
    s5 = page.evaluate("""(function(){
        return { rows: document.querySelectorAll('#wsGridWrap table tbody tr').length,
                 petrov: (function(){ var trs=document.querySelectorAll('#wsGridWrap table tbody tr td.ws-emp-col'); var n=0; for (var i=0;i<trs.length;i++){ if (trs[i].textContent.indexOf('Петров') !== -1) n++; } return n; })(),
                 shiftRows: (function(){ var trs=document.querySelectorAll('#wsGridWrap table tbody tr td.ws-emp-col'); var n=0; for (var i=0;i<trs.length;i++){ if (trs[i].textContent.indexOf('смена №') !== -1) n++; } return n; })(),
                 saved: localStorage.getItem('kip8_ws_view_v1') };
    })""")
    check('G: дневной вид — 1 строка (Петров), сменных НЕТ',
          s5['rows'] == 1 and s5['petrov'] == 1 and s5['shiftRows'] == 0, s5)
    check('G2: выбор сохранён (day)', s5['saved'] == 'day', s5['saved'])

    # ---- возврат в полный: шторка снова доступна ----
    page.click('#wsViewBtn')
    page.wait_for_timeout(500)
    check('H: полный вид — 12 строк, «Итоги учёта» доступна',
          grid_rows(page) == 12 and page.evaluate("!document.getElementById('wsTotalsBtn').hidden"))

    # ---- РАЗДЕЛИТЕЛЬНАЯ ПОЛОСА столбец ФИО | ячейки ----
    # Task 333: полоса — ПСЕВДОЭЛЕМЕНТ ::after sticky-ячеек (right: 0,
    # 2px, #4a8fc7) — БОРДЮР border-right 2px УДАЛЁН (в border-collapse
    # границы sticky-ячеек уезжали при прокрутке — пробы Chromium/Firefox)
    s6 = page.evaluate("""(function(){
        var th = document.querySelector('#wsGridWrap table thead th.ws-emp-col');
        var td = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
        var sep = document.querySelector('#wsGridWrap table tbody tr.ws-group-first td');
        var thA = getComputedStyle(th, '::after');
        var tdA = getComputedStyle(td, '::after');
        var cs = function(a){ return {w: a.width, pos: a.position, right: a.right,
                                      bg: a.backgroundColor, content: a.content}; };
        return { th: cs(thA), td: cs(tdA), thBorder: getComputedStyle(th).borderRightWidth,
                 groupTop: sep ? getComputedStyle(sep).borderTopColor : null };
    })""")
    check('I: полоса у столбца ФИО — ::after 2px absolute (шапка)',
          s6['th']['w'] == '2px' and s6['th']['pos'] == 'absolute' and s6['th']['content'] != 'none', s6['th'])
    check('I2: цвет полосы = #4a8fc7 (как разделитель сменных/дневных)',
          s6['td']['bg'] == 'rgb(74, 143, 199)' and s6['groupTop'] == 'rgb(74, 143, 199)', (s6['td'], s6['groupTop']))
    check('I3: полоса в теле — ::after 2px (бордюра-2px больше НЕТ)',
          s6['td']['w'] == '2px' and s6['thBorder'] != '2px', (s6['td'], s6['thBorder']))

    # полоса остаётся при горизонтальной прокрутке (sticky + ::after)
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 400")
    page.wait_for_timeout(200)
    s6b = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
        var r = td.getBoundingClientRect();
        var wrap = document.getElementById('wsGridWrap').getBoundingClientRect();
        var a = getComputedStyle(td, '::after');
        return { bg: a.backgroundColor, w: a.width,
                 inside: r.left >= wrap.left - 1 && r.right <= wrap.right + 2 };
    })""")
    check('I4: после прокрутки полоса на месте (::after sticky-ячейки)',
          s6b['bg'] == 'rgb(74, 143, 199)' and s6b['w'] == '2px' and s6b['inside'], s6b)
    page.evaluate("document.getElementById('wsGridWrap').scrollLeft = 0")

    # ---- ШТОРКА: ГОД — без «Обновить» и без столбца сотрудников ----
    page.evaluate("WorkSchedule.setTotalsTab('year')")
    page.wait_for_timeout(2500)
    s7 = page.evaluate("""(function(){
        var head = document.querySelector('#wsTotalsPanel .ws-tt-head');
        var refresh = document.getElementById('wsTtRefresh');
        var tt = document.querySelector('#wsTtBody table.ws-tt-year');
        var ths = tt ? tt.querySelectorAll('thead th') : [];
        var heads = [];
        for (var i=0;i<ths.length;i++) heads.push(ths[i].textContent.trim());
        var empTh = tt ? tt.querySelector('thead th.ws-tt-emp') : null;
        var arch = document.querySelector('#wsTtBody table.ws-tt-arch');
        var cap = document.querySelector('#wsTtBody .ws-tt-arch-cap');
        return { refreshInDom: !!refresh,
                 warnHidden: document.getElementById('wsTtWarn').hidden,
                 headHidden: head.hidden,
                 heads: heads,
                 empThDisp: empTh ? getComputedStyle(empTh).display : null,
                 rows: tt ? tt.querySelectorAll('tbody tr').length : 0,
                 arch: !!arch,
                 archRows: arch ? arch.querySelectorAll('tbody tr').length : 0,
                 archHas: arch ? arch.innerHTML.indexOf('Архивный') : -1,
                 capTxt: cap ? cap.textContent : null,
                 petrov: tt ? tt.innerHTML.indexOf('Петров') : -1 };
    })""")
    check('J: года: кнопки «Обновить» НЕТ в DOM', not s7['refreshInDom'])
    check('J2: года: шапка шторки спрятана (только ⚠, он скрыт)',
          s7['warnHidden'] and s7['headHidden'])
    # Task 333: колонка «Сотрудник» СНОВА в DOM главной таблицы (мобайл),
    # на ДЕСКТОПЕ скрыта CSS (.ws-tt-year:not(.ws-tt-arch)); архив — блоком
    check('J3: года: «Сотрудник» в DOM (мобайл), на десктопе СКРЫТ; месяцы следом',
          s7['heads'][0] == 'Сотрудник' and s7['heads'][1] == 'янв' and
          s7['empThDisp'] == 'none', (s7['heads'][:2], s7['empThDisp']))
    check('J4: года: строк главной = активным сетки (12), архив — БЛОКОМ ниже',
          s7['rows'] == 12 and s7['arch'] and s7['archRows'] == 1 and
          s7['archHas'] != -1 and s7['capTxt'] == 'Архив',
          (s7['rows'], s7['archRows'], s7['archHas'], s7['capTxt']))
    check('J5: года: годовые суммы (Дней/Часов/Перераб. (дни)) в конце',
          s7['heads'][-1] == 'Перераб. (дни)' and s7['heads'][-2] == 'Часов' and s7['heads'][-3] == 'Дней', s7['heads'][-3:])
    page.screenshot(path='task332-proof-year.png')

    # обновление года — кнопкой «Обновить» ТУЛБАРА (замена кнопки шапки)
    ts0 = page.evaluate("WorkSchedule._YEAR_DATA && WorkSchedule._YEAR_DATA.ts")
    page.click('#wsRefreshBtn')
    page.wait_for_timeout(3000)
    s8 = page.evaluate("""(function(){
        return { rows: document.querySelectorAll('#wsTtBody table.ws-tt-year tbody tr').length,
                 ts: WorkSchedule._YEAR_DATA ? WorkSchedule._YEAR_DATA.ts : null };
    })""")
    # Task 333: 12 активных + 1 архивная строка (блок «Архив», мок 900)
    check('K: «Обновить» тулбара перезагрузил год (кэш свежий, таблица жива)',
          s8['ts'] is not None and s8['ts'] >= ts0 and s8['rows'] == 13, (ts0, s8))
    page.screenshot(path='task332-proof-desktop.png')
    check('L: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: роль «КИП ИОС дежурный» =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t332-b', theme='dark', role='КИП ИОС дежурный')
    page2.evaluate("localStorage.setItem('kip8_ws_view_v1','day')")   # попытка подсунуть чужой вид
    page2.reload()
    page2.wait_for_timeout(2000)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    s9 = page2.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        return { rows: document.querySelectorAll('#wsGridWrap table tbody tr').length,
                 locked: view.classList.contains('ws-view-locked'),
                 aria: view.getAttribute('aria-label'),
                 view: WorkSchedule._view, lockedState: WorkSchedule._viewLocked,
                 totalsHidden: document.getElementById('wsTotalsBtn').hidden,
                 visShift: !document.getElementById('wsViewIconShift').hidden };
    })""")
    check('M: дежурный — вид ЗАПЕРТ на «сменный» (сохранённый day проигнорирован)',
          s9['view'] == 'shift' and s9['lockedState'] and s9['rows'] == 11, s9)
    check('M2: кнопка вида с классом ws-view-locked, иконка Shift',
          s9['locked'] and s9['visShift'], s9)
    check('M3: «Итоги учёта» скрыта (шторка недоступна)', s9['totalsHidden'])
    # клик не меняет вид
    page2.click('#wsViewBtn')
    page2.wait_for_timeout(400)
    s10 = page2.evaluate("(function(){ return { view: WorkSchedule._view, rows: document.querySelectorAll('#wsGridWrap table tbody tr').length, toast: (function(){ var t=document.querySelector('.toast, .kip-toast, #toastBox'); return t?t.textContent:''; })() }; })()")
    check('N: клик по запертой кнопке — вид НЕ меняется (сменный), тост-пояснение',
          s10['view'] == 'shift' and s10['rows'] == 11 and 'сменный' in s10['toast'], s10)
    # подсказка запертой кнопки (мышь УВОДИМ от кнопки перед hover)
    page2.mouse.move(500, 500)
    page2.wait_for_timeout(150)
    page2.hover('#wsViewBtn')
    page2.wait_for_timeout(300)
    s10b = page2.evaluate("(function(){ return { t: document.getElementById('wsViewTipTitle').textContent, d: document.getElementById('wsViewTipDesc').textContent, hidden: document.getElementById('wsViewTip').hidden }; })()")
    check('N2: подсказка дежурного: «сменный» + «доступен только сменный»',
          (not s10b['hidden']) and s10b['t'] == 'Вид табеля: сменный' and 'только сменный' in s10b['d'], s10b)
    page2.screenshot(path='task332-proof-duty.png')
    check('O: 0 JS-ошибок (дежурный)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: светлая тема =================
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t332-c', theme='light')
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    s11 = page3.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap table tbody td.ws-emp-col');
        var th = document.querySelector('#wsGridWrap table thead th.ws-emp-col');
        var sep = document.querySelector('#wsGridWrap table tbody tr.ws-group-first td');
        var tip = document.getElementById('wsCrossTip');
        // Task 333: полоса — ::after (НЕ border-right)
        return { light: document.documentElement.getAttribute('data-theme') === 'light',
                 td: getComputedStyle(td, '::after').backgroundColor, w: getComputedStyle(td, '::after').width,
                 th: getComputedStyle(th, '::after').backgroundColor, group: getComputedStyle(sep).borderTopColor,
                 tipBg: getComputedStyle(tip).backgroundColor,
                 tipDate: getComputedStyle(tip.querySelector('.ws-rt-date')).color };
    })""")
    check('P: светлая: полоса ::after #6e8ba4 (шапка и тело, = разделителю групп)',
          s11['td'] == 'rgb(110, 139, 164)' and s11['th'] == 'rgb(110, 139, 164)' and s11['group'] == 'rgb(110, 139, 164)' and s11['w'] == '2px', s11)
    page3.hover('#wsViewBtn')
    page3.wait_for_timeout(300)
    s11b = page3.evaluate("(function(){ var t=document.getElementById('wsViewTip'); return {hidden:t.hidden, col:getComputedStyle(t.querySelector('.ws-rt-date')).color}; })()")
    check('P2: светлая: подсказка вида показана, заголовок тёмный (#333)',
          (not s11b['hidden']) and s11b['col'] == 'rgb(51, 51, 51)', s11b)
    page3.screenshot(path='task332-proof-light.png')
    check('Q: 0 JS-ошибок (светлая)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 4: мобайл 375 =================
    ctx4, page4, js_errors4 = setup_ctx(browser, {'width':375,'height':700}, 'browser-check-t332-d', theme='dark')
    page4.evaluate("navigateTo('work-schedule')")
    page4.wait_for_timeout(3000)
    s12 = page4.evaluate("""(function(){
        var view = document.getElementById('wsViewBtn');
        var cross = document.getElementById('wsCrossBtn');
        var label = view ? view.querySelector('.ws-view-label') : null;
        return { rows: document.querySelectorAll('#wsGridWrap table tbody tr').length,
                 viewW: view.getBoundingClientRect().width,
                 crossW: cross.getBoundingClientRect().width,
                 label: label ? label.textContent : null,
                 aria: view.getAttribute('aria-label') };
    })""")
    # Task 333: подпись «Вид» — кнопка ШИРЕ иконки-подсветки (не 34px-квадрат)
    check('R: мобайл: кнопка вида с ПОДПИСЬЮ «Вид» (шире иконки)',
          s12['label'] == 'Вид' and s12['viewW'] > s12['crossW'] + 20, (s12['label'], s12['viewW'], s12['crossW']))
    page4.click('#wsViewBtn')
    page4.wait_for_timeout(500)
    s13 = page4.evaluate("""(function(){
        return { rows: document.querySelectorAll('#wsGridWrap table tbody tr').length,
                 totalsHidden: document.getElementById('wsTotalsBtn').hidden,
                 view: WorkSchedule._view };
    })""")
    check('R2: мобайл: сменный вид — 11 строк, «Итоги учёта» скрыта',
          s13['rows'] == 11 and s13['totalsHidden'] and s13['view'] == 'shift', s13)
    page4.screenshot(path='task332-proof-mobile.png')
    check('S: 0 JS-ошибок (мобайл)', len(js_errors4) == 0, js_errors4[:3])
    ctx4.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
