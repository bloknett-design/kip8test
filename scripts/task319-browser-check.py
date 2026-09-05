# -*- coding: utf-8 -*-
# Task 319: browser-check «График работы» — четыре правки:
#   1) тултип «Обновить» — НЕ прячется под верхним баром:
#      перенос в <body> (stacking) + позиция с учётом бара (под
#      кнопкой, если над ней места меньше низа бара);
#   2) ПЕРЕКРЕСТЬЕ — движение мыши по ячейкам шахматки выделяет
#      СТРОКУ и СТОЛБЕЦ, пересекающиеся в ячейке под курсором
#      (переходы между ячейками без снятия строки; уход на шапку/
#      ФИО/вне сетки — сброс; переживает перерисовку);
#   3) тёмная тема — цвет шахматки ДНЕЙ как в светлой (пустые
#      #eef0f2, выходные #f7d9e3, текст #141413, inline-цвета
#      справочника), вся площадь слегка притенена фильтром
#      brightness(0.88); шапка/ФИО остаются тёмными;
#   4) окно выбора кодов — название мельче (12px) и ПЕРЕНОСИТСЯ;
#      зрителю («График работы — просмотр») клик по ячейке
#      открывает окно «Мероприятия в этот день» (без окна кодов,
#      без тоста «нет прав»).
# Проверки: 4 контекста (десктоп-Админ тёмная, десктоп светлая,
# зритель, мобильный 375 touch), 0 JS-ошибок, скриншоты.
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404).
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
  {'code':'ОТ','name':'Отпуск основной оплачиваемый ежегодный — длинное название для проверки переноса строки в окне выбора кодов','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
] + [
  {'таб_номер':'%03d' % (30 + i),'ФИО':'Сотрудник %02d Тестовый' % (i + 1),'тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
  for i in range(10)
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]},
]
ENTRIES = [
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Целевой инструктаж','дата_начала':'%04d-%02d-10' % (Y, M),'дата_окончания':'%04d-%02d-10' % (Y, M),'длительность_дней':1},
  {'id':102,'таб_номер':'023','тип':'обучение','тема':'Охрана труда','дата_начала':'%04d-%02d-12' % (Y, M),'дата_окончания':'%04d-%02d-15' % (Y, M),'длительность_дней':4},
]
VACATIONS = []

STATE = {'role': 'Админ'}

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t319)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

def open_grid(page, theme=None):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t319')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)

# Центр ячейки: строка по таб.№ (порядок <tr> в tbody) + data-day
def cell_xy(page, tab, day):
    return page.evaluate("""(function(a){
        var tab = a[0], day = a[1];
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var i=0;i<trs.length;i++){
            var emp = trs[i].querySelector('td.ws-emp-col');
            if (emp && emp.getAttribute('data-tab') === tab) {
                var td = trs[i].querySelector('td.ws-cell[data-day=\"'+day+'\"]');
                if (td) { var r = td.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2, i]; }
            }
        }
        return null;
    })""", [tab, day])

def th_xy(page, day):
    return page.evaluate("""(function(day){
        var th = document.querySelector('#wsGridWrap th[data-day=\"'+day+'\"]');
        if (!th) return null;
        var r = th.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2];
    })""", day)

# Состояние перекрестья: классы строки/столбца
def cross_state(page):
    return page.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        var rows = [];
        for (var i=0;i<trs.length;i++) rows.push(trs[i].classList.contains('ws-hover-row'));
        var th5 = document.querySelector('th[data-day=\"5\"]');
        var th7 = document.querySelector('th[data-day=\"7\"]');
        var col = function(day){
            var tds = document.querySelectorAll('td.ws-cell[data-day=\"'+day+'\"]');
            var on = 0;
            for (var i=0;i<tds.length;i++) if (tds[i].classList.contains('ws-hover')) on++;
            return {on: on, total: tds.length};
        };
        // ФИО-ячейка первой строки: box-shadow перекрестья
        var emp = trs.length ? trs[0].querySelector('td.ws-emp-col') : null;
        return {rows: rows,
                th5: th5 ? th5.classList.contains('ws-hover-col') : null,
                th7: th7 ? th7.classList.contains('ws-hover-col') : null,
                col5: col(5), col7: col(7),
                empShadow: emp ? getComputedStyle(emp).boxShadow : ''};
    })()""")

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

    # ---------- 1. Тултип «Обновить»: не под верхним баром ----------
    bar = page.evaluate("""(function(){
        var b = document.querySelector('.desktop-top-bar');
        if (!b) return null;
        var r = b.getBoundingClientRect();
        return {top:r.top, bottom:r.bottom, h:r.height, z:getComputedStyle(b).zIndex};
    })()""")
    check('C: верхний бар есть (sticky 56px, z70)', bar and abs(bar['h']-56)<1 and bar['z']=='70', bar)
    btn = page.evaluate("""(function(){
        var b = document.getElementById('wsRefreshBtn');
        var r = b.getBoundingClientRect();
        return {top:r.top, bottom:r.bottom, left:r.left};
    })()""")
    page.mouse.move(btn['left'] + 40, (btn['top'] + btn['bottom']) / 2)
    page.wait_for_timeout(250)
    tip = page.evaluate("""(function(){
        var t = document.getElementById('wsRefreshTip');
        if (!t) return null;
        var r = t.getBoundingClientRect();
        return {hidden: t.hidden, top: r.top, bottom: r.bottom, left: r.left, h: r.height,
                parent: t.parentNode === document.body ? 'body' : (t.parentNode.id || t.parentNode.tagName),
                z: getComputedStyle(t).zIndex, pe: getComputedStyle(t).pointerEvents,
                text: t.textContent.slice(0, 60)};
    })()""")
    check('D: тултип показан, ПЕРЕНЕСЁН в <body>', tip and not tip['hidden'] and tip['parent'] == 'body', tip)
    check('D2: тултип ПОД кнопкой — НИЖЕ верхнего бара (не прячется)',
          tip and tip['top'] >= bar['bottom'] - 1 and tip['top'] >= btn['bottom'] - 2,
          (tip and tip['top'], bar['bottom'], btn['bottom']))
    check('D3: z-index 9450 (в корне — выше бара z70), кликам не мешает',
          tip and tip['z'] == '9450' and tip['pe'] == 'none', (tip and tip['z'], tip and tip['pe']))
    check('D4: содержит «данные от» + описание',
          tip and ('данные от' in tip['text'] or 'ещ нет' in tip['text']), tip and tip['text'][:40])
    page.screenshot(path='scripts/task319-proof-tooltip.png')
    page.mouse.move(900, 700)
    page.wait_for_timeout(200)
    check('D5: уход курсора — тултип скрыт',
          page.evaluate("document.getElementById('wsRefreshTip').hidden"))

    # ---------- 2. ПЕРЕКРЕСТЬЕ ----------
    # ячейка (017, день 5): строка 0
    xy = cell_xy(page, '017', 5)
    page.mouse.move(xy[0], xy[1])
    page.wait_for_timeout(150)
    s = cross_state(page)
    check('E: перекрестье — СТРОКА 0 подсвечена (ws-hover-row)',
          s['rows'][0] == True and not any(s['rows'][1:]), s['rows'])
    check('E2: СТОЛБЕЦ 5 — th + ВСЕ ячейки (ws-hover-col/ws-hover)',
          s['th5'] == True and s['col5']['on'] == s['col5']['total'] and s['col5']['total'] > 0,
          (s['th5'], s['col5']))
    check('E3: столбец 7 НЕ подсвечен (только пересечение)',
          s['th7'] in (False, None) and s['col7']['on'] == 0, (s['th7'], s['col7']))
    check('E4: ФИО-ячейка строки — tint перекрестья',
          s['empShadow'] and s['empShadow'] != 'none', s['empShadow'][:60])
    inter = page.evaluate("""(function(){
        var td = document.querySelector('#wsGridWrap tbody tr td.ws-cell[data-day=\"5\"]');
        return td ? getComputedStyle(td).boxShadow : '';
    })()""")
    plain_row_cell = page.evaluate("""(function(){
        var tr = document.querySelectorAll('#wsGridWrap tbody tr')[0];
        var td = tr.querySelector('td.ws-cell[data-day=\"3\"]');
        return td ? getComputedStyle(td).boxShadow : '';
    })()""")
    check('E5: пересечение — насыщеннее остальной строки (0.24 vs 0.10)',
          'rgba(74, 143, 199, 0.24)' in inter and 'rgba(74, 143, 199, 0.1)' in plain_row_cell,
          (inter[:50], plain_row_cell[:50]))
    page.screenshot(path='scripts/task319-proof-crosshair.png')

    # соседняя ячейка ТОЙ ЖЕ строки (день 7): строка не снимается, столбец сменится
    xy7 = cell_xy(page, '017', 7)
    page.mouse.move(xy7[0], xy7[1])
    page.wait_for_timeout(150)
    s2 = cross_state(page)
    check('F: переход в той же строке — строка ОСТАЛАСЬ (без мигания)',
          s2['rows'][0] == True and not any(s2['rows'][1:]), s2['rows'])
    check('F2: столбец сменился (5 снят, 7 поставлен)',
          s2['th5'] == False and s2['th7'] == True and s2['col7']['on'] == s2['col7']['total'],
          (s2['th5'], s2['th7'], s2['col7']))

    # другая строка (023 — дневной, после сменных: индекс из cell_xy), день 5
    xy023 = cell_xy(page, '023', 5)
    r023 = xy023[2]
    page.mouse.move(xy023[0], xy023[1])
    page.wait_for_timeout(150)
    s3 = cross_state(page)
    check('G: смена строки — прежняя снята, новая поставлена',
          s3['rows'][r023] == True and s3['rows'][0] == False, (r023, s3['rows'][:3], s3['rows'][r023]))

    # уход на ШАПКУ (th дня 12): перекрестье снято, работает Task 316
    thxy = th_xy(page, 12)
    page.mouse.move(thxy[0], thxy[1])
    page.wait_for_timeout(150)
    s4 = cross_state(page)
    check('H: уход на шапку — строка/столбец перекрестья сняты',
          not any(s4['rows']) and s4['col5']['on'] == 0 and s4['col7']['on'] == 0, s4['rows'])
    th12 = page.evaluate("""(function(){
        var th = document.querySelector('th[data-day=\"12\"]');
        return th && th.classList.contains('ws-hover-col');
    })()""")
    check('H2: наведение th — свой столбец (Task 316 жив)', th12)

    # уход ИЗ сетки (тулбар): всё снято
    page.mouse.move(640, 150)
    page.wait_for_timeout(150)
    s5 = cross_state(page)
    check('I: уход из сетки — перекрестье снято полностью',
          not any(s5['rows']) and s5['col5']['on'] == 0, s5['rows'])

    # переживает перерисовку: hover ячейки → правка статуса → re-render
    xy = cell_xy(page, '017', 5)
    page.mouse.move(xy[0], xy[1])
    page.wait_for_timeout(150)
    page.mouse.click(xy[0], xy[1])   # открыть окно кодов
    page.wait_for_timeout(300)
    picked = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        if (!cp) return false;
        var rows = cp.querySelectorAll('.ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent.trim() === 'Н') { rows[i].click(); return true; }
        }
        return false;
    })()""")
    check('J: статус выбран в окне кодов (перерисовка)', picked)
    page.wait_for_timeout(400)
    s6 = cross_state(page)
    check('J2: перекрестье ПЕРЕЖИВАЕТ перерисовку (штамп из состояния)',
          s6['rows'][0] == True, s6['rows'][:3])
    # сетка в бары не прыгнула — закрыть окно, курсор в ТУЛБАР (не в сетку!)
    page.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page.wait_for_timeout(150)
    page.mouse.move(640, 148)
    page.wait_for_timeout(200)
    s7 = cross_state(page)
    check('J3: уход курсора после перерисовки — перекрестье снято',
          not any(s7['rows']), s7['rows'][:3])

    # ---------- 3. ТЁМНАЯ тема: цвета шахматки дней как в светлой ----------
    dark = page.evaluate("""(function(){
        function cs(el){ return el ? getComputedStyle(el) : null; }
        var empty = document.querySelector('#wsGridWrap td.ws-cell.ws-status-empty:not(.ws-weekend)');
        var weekend = document.querySelector('#wsGridWrap td.ws-cell.ws-weekend.ws-status-empty');
        var status = null;
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf('023') !== -1 && oc.indexOf('%s') !== -1) { status = tds[i]; break; }
        }
        var th = document.querySelector('#wsGridWrap thead th.ws-day-col');
        var emp = document.querySelector('#wsGridWrap tbody td.ws-emp-col');
        var pend = document.querySelector('#wsGridWrap .ws-ev-badge.ws-ev-pending');
        return {
            empty: empty ? {bg: cs(empty).backgroundColor, color: cs(empty).color, f: cs(empty).filter} : null,
            weekend: weekend ? {bg: cs(weekend).backgroundColor, f: cs(weekend).filter} : null,
            status: status ? {bg: cs(status).backgroundColor, color: cs(status).color, f: cs(status).filter} : null,
            th: th ? {bg: cs(th).backgroundColor} : null,
            emp: emp ? {bg: cs(emp).backgroundColor} : null,
            pend: pend ? {color: cs(pend).color, bc: cs(pend).borderColor} : null
        };
    })()""" % TODAY_ISO)
    check('K: пустая ячейка — #eef0f2 (как в светлой) + brightness(0.88)',
          dark['empty'] and dark['empty']['bg'] == 'rgb(238, 240, 242)' and
          dark['empty']['f'] == 'brightness(0.88)', dark['empty'])
    check('K2: текст кодов — #141413 (тёмный, как в светлой)',
          dark['status'] and dark['status']['color'] == 'rgb(20, 20, 19)', dark['status'])
    check('K3: статусная ячейка — inline-цвет справочника (Д8 #FFF9C4) + фильтр',
          dark['status'] and dark['status']['bg'] == 'rgb(255, 249, 196)' and
          dark['status']['f'] == 'brightness(0.88)', dark['status'])
    check('K4: пустая выходная — #f7d9e3 (не #6e4250)',
          dark['weekend'] and dark['weekend']['bg'] == 'rgb(247, 217, 227)', dark['weekend'])
    check('K5: шапка сетки — ТЁМНАЯ (заявка только про шахматку дней)',
          dark['th'] and dark['th']['bg'] == 'rgb(14, 22, 33)', dark['th'])
    check('K6: ФИО-колонка — тёмная',
          dark['emp'] and dark['emp']['bg'] == 'rgb(14, 22, 33)', dark['emp'])
    check('K7: «·»/пустые — вторичный тёмный',
          dark['empty'] and dark['empty']['color'] == 'rgba(20, 20, 19, 0.65)', dark['empty'])
    check('K8: пунктирный бейдж — тёмный текст/рамка',
          (not dark['pend']) or (dark['pend']['color'] == 'rgb(20, 20, 19)' and
                                 dark['pend']['bc'] == 'rgba(0, 0, 0, 0.55)'), dark['pend'])
    page.screenshot(path='scripts/task319-proof-dark.png')

    # ---------- 4. Окно кодов: название мельче + перенос ----------
    page.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page.wait_for_timeout(150)
    page.evaluate("WorkSchedule._cellHover(null)")
    xy = cell_xy(page, '017', 5)
    page.mouse.click(xy[0], xy[1])
    page.wait_for_timeout(300)
    names = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        if (!cp || !cp.classList.contains('active')) return null;
        var out = [];
        var rows = cp.querySelectorAll('.ws-popup-row');
        var longEl = null;
        for (var i=0;i<rows.length;i++){
            var n = rows[i].querySelector('.ws-popup-name');
            if (!n) continue;
            var cs = getComputedStyle(n);
            var rects = n.getClientRects();
            out.push({text: n.textContent.slice(0, 20), fs: cs.fontSize, ws: cs.whiteSpace,
                      ow: cs.overflowWrap, lines: rects.length, w: n.getBoundingClientRect().width});
            if (n.textContent.indexOf('Отпуск основной') !== -1) longEl = n;
        }
        var pw = cp.getBoundingClientRect().width;
        var longLines = 0;
        if (longEl) {
            var range = document.createRange();
            range.selectNodeContents(longEl);
            longLines = range.getClientRects().length;
        }
        var evp = document.getElementById('wsEventsPopup');
        var evName = evp ? evp.querySelector('.ws-popup-name') : null;
        return {names: out, popupW: pw, longLines: longLines,
                evFs: evName ? getComputedStyle(evName).fontSize : null,
                evWs: evName ? getComputedStyle(evName).whiteSpace : null,
                evActive: evp ? evp.classList.contains('active') : false};
    })()""")
    check('L: окно кодов открыто, названия — 12px (было 13px)',
          names and all(n['fs'] == '12px' for n in names['names']) and len(names['names']) >= 4,
          names and [(n['text'], n['fs']) for n in names['names'][:3]])
    check('L2: названия ПЕРЕНОСЯТСЯ (white-space normal, break-word)',
          names and all(n['ws'] == 'normal' and n['ow'] == 'break-word' for n in names['names']),
          names and names['names'][0])
    check('L3: ДЛИННОЕ название — несколько строк (Range-rects), окно ≤ 320px',
          names and names['longLines'] >= 2 and names['popupW'] <= 321,
          (names and names['longLines'], names and names['popupW']))
    page.screenshot(path='scripts/task319-proof-popup-name.png')
    # окно «Мероприятия в этот день» над окном кодов — прежний вид названия:
    # ячейка С мероприятием (017, день 10 «Целевой инструктаж»)
    page.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page.wait_for_timeout(200)
    xy10 = cell_xy(page, '017', 10)
    page.mouse.click(xy10[0], xy10[1])
    page.wait_for_timeout(300)
    evn = page.evaluate("""(function(){
        var evp = document.getElementById('wsEventsPopup');
        if (!evp || !evp.classList.contains('active')) return null;
        var n = evp.querySelector('.ws-popup-name');
        if (!n) return null;
        var cs = getComputedStyle(n);
        return {fs: cs.fontSize, ws: cs.whiteSpace, text: n.textContent.slice(0, 30)};
    })""")
    check('L4: окно «Мероприятия в этот день» — прежний вид (13px, nowrap)',
          evn and evn['fs'] == '13px' and evn['ws'] == 'nowrap' and 'Целевой' in evn['text'], evn)
    page.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page.wait_for_timeout(200)
    check('M: 0 JS-ошибок (контекст 1)', not js_errors, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема (санити) =================
    STATE['role'] = 'Админ'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    setup_routes(ctx2)
    open_grid(page2, theme='light')
    light = page.evaluate if False else page2.evaluate("""(function(){
        var empty = document.querySelector('#wsGridWrap td.ws-cell.ws-status-empty:not(.ws-weekend)');
        var weekend = document.querySelector('#wsGridWrap td.ws-cell.ws-weekend.ws-status-empty');
        var th = document.querySelector('#wsGridWrap thead th.ws-day-col');
        return {
            empty: empty ? {bg: getComputedStyle(empty).backgroundColor, f: getComputedStyle(empty).filter} : null,
            weekend: weekend ? {bg: getComputedStyle(weekend).backgroundColor} : null,
            th: th ? {bg: getComputedStyle(th).backgroundColor} : null
        };
    })()""")
    check('N: светлая — те же ЦВЕТА ячеек, БЕЗ фильтра',
          light['empty'] and light['empty']['bg'] == 'rgb(238, 240, 242)' and
          light['empty']['f'] == 'none' and
          light['weekend'] and light['weekend']['bg'] == 'rgb(247, 217, 227)', light)
    check('N2: светлая — шапка СВЕТЛАЯ (тема не перепутана)',
          light['th'] and light['th']['bg'] == 'rgba(240, 240, 240, 0.95)', light['th'])
    # перекрестье в светлой — тон мягче
    xy = cell_xy(page2, '017', 5)
    page2.mouse.move(xy[0], xy[1])
    page2.wait_for_timeout(150)
    cross_l = page2.evaluate("""(function(){
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        var td = trs[0].querySelector('td.ws-cell[data-day=\"3\"]');
        return {row: trs[0].classList.contains('ws-hover-row'),
                tint: td ? getComputedStyle(td).boxShadow : ''};
    })()""")
    check('O: перекрестье в светлой — строка + тон 0.06',
          cross_l['row'] and 'rgba(42, 93, 143, 0.06)' in cross_l['tint'], cross_l['tint'][:50])
    page2.screenshot(path='scripts/task319-proof-light.png')
    check('P: 0 JS-ошибок (контекст 2)', not js_errors2, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: ЗРИТЕЛЬ («График работы — просмотр») =================
    STATE['role'] = 'ИТР8 pro'
    ctx3 = browser.new_context(viewport={'width':1280,'height':800})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    setup_routes(ctx3)
    open_grid(page3)
    # ячейка с мероприятием (017, день 10 — «Целевой инструктаж»)
    xy = cell_xy(page3, '017', 10)
    page3.mouse.click(xy[0], xy[1])
    page3.wait_for_timeout(400)
    v = page3.evaluate("""(function(){
        var evp = document.getElementById('wsEventsPopup');
        var cp = document.getElementById('wsCellPopup');
        return {
            evActive: evp && evp.classList.contains('active'),
            evHtml: evp ? evp.innerHTML : '',
            cpActive: cp ? cp.classList.contains('active') : null,
            closer: !!(document.querySelector('.ws-popup-closer.active'))
        };
    })()""")
    check('Q: зритель — окно «Мероприятия в этот день» ОТКРЫТО',
          v['evActive'] and 'Мероприятия в этот день' in v['evHtml'] and
          'Целевой инструктаж' in v['evHtml'], v['evHtml'][:80])
    check('Q2: БЕЗ кнопок ✎/✕ (зритель — справка)',
          'editTraining' not in v['evHtml'] and 'deleteTraining' not in v['evHtml'])
    check('Q3: окно выбора кодов НЕ открыто (правка недоступна)',
          v['cpActive'] == False, v['cpActive'])
    check('Q4: кловер активен (клик мимо закроет)', v['closer'])
    page3.screenshot(path='scripts/task319-proof-viewer.png')
    # закрыть кловером, открыть ПУСТОЙ день
    page3.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page3.wait_for_timeout(200)
    xy17 = cell_xy(page3, '017', 17)
    page3.mouse.click(xy17[0], xy17[1])
    page3.wait_for_timeout(300)
    empty_ev = page3.evaluate("(function(){ var e = document.getElementById('wsEventsPopup'); return e && e.classList.contains('active') ? e.textContent : ''; })()")
    check('R: пустой день — «нет мероприятий» (окно тоже открыто)',
          'нет мероприятий' in empty_ev, empty_ev[:60])
    # зритель: перекрестье работает (все роли)
    page3.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page3.wait_for_timeout(200)
    xy = cell_xy(page3, '023', 5)
    ridx = xy[2]
    page3.mouse.move(xy[0], xy[1])
    page3.wait_for_timeout(150)
    vr = page3.evaluate("""(function(ri){
        var trs = document.querySelectorAll('#wsGridWrap tbody tr');
        return trs.length > ri && trs[ri].classList.contains('ws-hover-row');
    })""", ridx)
    check('S: зритель — перекрестье работает (все роли)', vr)
    check('T: 0 JS-ошибок (контекст 3)', not js_errors3, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 4: мобильный 375 touch =================
    STATE['role'] = 'Админ'
    ctx4 = browser.new_context(viewport={'width':375,'height':700}, has_touch=True, is_mobile=True)
    page4 = ctx4.new_page()
    js_errors4 = []
    page4.on('pageerror', lambda e: js_errors4.append(str(e)))
    setup_routes(ctx4)
    open_grid(page4, theme='dark')
    mob = page4.evaluate("""(function(){
        var bar = document.querySelector('.desktop-top-bar');
        var cells = document.querySelectorAll('#wsGridWrap td.ws-cell');
        var empty = document.querySelector('#wsGridWrap td.ws-cell.ws-status-empty:not(.ws-weekend)');
        return {barH: bar ? bar.getBoundingClientRect().height : 0,
                cells: cells.length,
                emptyBg: empty ? getComputedStyle(empty).backgroundColor : null};
    })()""")
    check('U: мобильный — сетка есть, бара нет, шахматка светлая в тёмной теме',
          mob['cells'] > 0 and mob['barH'] == 0 and mob['emptyBg'] == 'rgb(238, 240, 242)', mob)
    page4.screenshot(path='scripts/task319-proof-mobile.png')
    check('V: 0 JS-ошибок (контекст 4)', not js_errors4, js_errors4[:3])
    ctx4.close()

    browser.close()

fails = [r for r in results if not r[1]]
print()
print('ИТОГ: %d/%d passed, %d failed' % (len(results) - len(fails), len(results), len(fails)))
if fails:
    print('ПРОВАЛЕНЫ:')
    for n, _, e in fails:
        print('  ✗', n, '|', e)
sys.exit(1 if fails else 0)
