# -*- coding: utf-8 -*-
# Task 317: browser-check «График работы» — бар над шахматкой:
#   • строка «данные от …» УБРАНА из бара — живёт в ИНФОРМАЦИОННОМ
#     ОКНЕ, появляющемся при НАВЕДЕНИИ на кнопку «Обновить»
#     (и по фокусу; скрывается уходом курсора/кликом/прокруткой);
#   • все кнопки в ТРИ РЯДА — РОВНО в высоту окон справа (95px),
#     расстояние между рядами 3px;
#   • рамки бара — 5px, не изменяются.
# Проверки (десктоп 1280, Админ): структура колонки (3 ряда в
# .ws-toolbar-main, окна рядом), точная высота колонки == окон ==
# 95px (±0.6), ряды ≈ 29.67px, зазоры 3px, кнопки во всю высоту
# ряда без переполнения, штампа в баре нет; тултип: hover →
# показан над кнопкой с «данные от …», pointer-events none, уход
# курсора/клик → скрыт, фокус → показан; правка ячейки → ряд 2
# «Сохранить (1)»+«Отменить» ВНУТРИ колонки (не полная ширина),
# высоты/зазоры те же, сетка под баром НЕ прыгает; «Обновить» —
# тост; светлая тема тултипа; зритель — колонка не прыгает, ряд 1
# наверху; мобильный 375px — бар колонкой, кнопки 34px, зазоры
# 3px; 1024px — ряд 1 без переноса. 0 JS-ошибок.
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
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
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
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Целевой инструктаж','дата_начала':'%04d-%02d-10' % (Y, M),'дата_окончания':'%04d-%02d-10' % (Y, M),'длительность_дней':1},
  {'id':102,'таб_номер':'023','тип':'обучение','тема':'Охрана труда','дата_начала':'%04d-%02d-12' % (Y, M),'дата_окончания':'%04d-%02d-15' % (Y, M),'длительность_дней':4}
] + [
  {'id':110 + i,'таб_номер':'%03d' % (30 + i),'тип':'инструктаж','тема':'Повторный инструктаж №%d на рабочем месте' % (i + 1),'дата_начала':'%04d-%02d-%02d' % (Y, M, 2 + i),'дата_окончания':'%04d-%02d-%02d' % (Y, M, 2 + i),'длительность_дней':1}
  for i in range(8)
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

# Состояние бара: высоты/зазоры/рамки/тултип
BAR_JS = """(function(){
    function R(el){ var r = el.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height}; }
    var tb = document.querySelector('.ws-toolbar');
    var br = document.querySelector('.ws-bar-row');
    var main = document.querySelector('.ws-toolbar-main');
    var ev = document.getElementById('wsEventsPanel');
    var cal = document.getElementById('wsCalPanel');
    var rows = [];
    var kids = main ? main.children : [];
    for (var i=0;i<kids.length;i++){
        var r = kids[i].getBoundingClientRect();
        rows.push({id: kids[i].id, y: r.y, h: r.height, w: r.width,
                   hidden: kids[i].hidden,
                   disp: getComputedStyle(kids[i]).display});
    }
    var btns = main ? main.querySelectorAll('.ws-toolbar-row > *') : [];
    var bList = [];
    for (var i=0;i<btns.length;i++){
        var b = btns[i];
        bList.push({id: b.id, h: b.getBoundingClientRect().height,
                    of: b.scrollHeight > b.clientHeight + 1});
    }
    var tip = document.getElementById('wsRefreshTip');
    var grid = document.getElementById('wsGridWrap');
    var cs = getComputedStyle(tb);
    return {
        pad: cs.padding, padT: parseFloat(cs.paddingTop), padB: parseFloat(cs.paddingBottom),
        padL: parseFloat(cs.paddingLeft), padR: parseFloat(cs.paddingRight),
        tb: R(tb), br: br ? R(br) : null,
        main: main ? R(main) : null, ev: R(ev), cal: R(cal),
        rows: rows, btns: bList,
        stamp: !!document.getElementById('wsCacheStamp'),
        tipHidden: tip ? tip.hidden : null,
        tipPE: tip ? getComputedStyle(tip).pointerEvents : '',
        gridY: grid ? grid.getBoundingClientRect().y : null,
        colW: (br && br.children.length === 3) ?
              [br.children[0].getBoundingClientRect().width,
               br.children[1].getBoundingClientRect().width,
               br.children[2].getBoundingClientRect().width] : []
    };
})()"""

def bar_state(page):
    return page.evaluate(BAR_JS)

def click_cell(page, iso, tab):
    page.evaluate("""(function(a){
        var iso = a[0], tab = a[1];
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'"+iso+"'") !== -1 && oc.indexOf("'"+tab+"'") !== -1) {
                var r = tds[i].getBoundingClientRect();
                window.__cellXY = [r.left + r.width/2, r.top + r.height/2];
                return;
            }
        }
        window.__cellXY = [600, 300];
    })""", [iso, tab])
    xy = page.evaluate("window.__cellXY")
    page.mouse.click(xy[0], xy[1])

def select_popup_code(page, code):
    return page.evaluate("""(function(code){
        var cp = document.getElementById('wsCellPopup');
        if (!cp) return false;
        var rows = cp.querySelectorAll('.ws-popup-row');
        for (var i=0;i<rows.length;i++){
            var c = rows[i].querySelector('.ws-popup-code');
            if (c && c.textContent.trim() === code) { rows[i].click(); return true; }
        }
        return false;
    })""", code)

def close_popups(page):
    page.evaluate("(function(){ var c = document.querySelector('.ws-popup-closer.active'); if (c) c.click(); })()")
    page.wait_for_timeout(150)

def approx(a, b, eps):
    return a is not None and b is not None and abs(a - b) <= eps

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280px, Админ =================
    ctx = browser.new_context(viewport={'width':1280,'height':800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t317)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t317')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- рамки бара 5px + высота бара ----------
    s0 = bar_state(page)
    check('C: рамки бара — 5px со всех сторон (не изменяются)',
          s0['pad'] == '5px' and approx(s0['padT'],5,0.1) and approx(s0['padB'],5,0.1) and
          approx(s0['padL'],5,0.1) and approx(s0['padR'],5,0.1), s0['pad'])
    # 95 (окна) + 2×5 (рамки) + 1 (border-bottom) = 106
    check('C2: высота бара = окна 95 + рамки 2×5 + 1 (было ~145)',
          approx(s0['tb']['h'], 106, 1.5), s0['tb']['h'])

    # ---------- три равные части ----------
    check('D: три части бара равной ширины (кнопки | мероприятия | время)',
          len(s0['colW']) == 3 and max(s0['colW']) - min(s0['colW']) <= 8, s0['colW'])

    # ---------- колонка кнопок РОВНО в высоту окон ----------
    check('E: колонка кнопок = окна = 95px (ровно)',
          approx(s0['main']['h'], 95, 0.6) and approx(s0['ev']['h'], 95, 0.6) and
          approx(s0['cal']['h'], 95, 0.6),
          (s0['main'] and s0['main']['h'], s0['ev']['h'], s0['cal']['h']))

    # ---------- ряды: 2 скрыта (нет правок), 1 и 3 видны ----------
    vis = [r for r in s0['rows'] if not r['hidden']]
    hid = [r for r in s0['rows'] if r['hidden']]
    check('F: ряд 2 скрыт без правок; ряды 1 и 3 видны',
          [r['id'] for r in hid] == ['wsActionsRow'] and
          [r['id'] for r in vis][0] == 'wsSelectsRow' and
          [r['id'] for r in vis][-1] == 'wsGenerateRow',
          [(r['id'], r['hidden']) for r in s0['rows']])
    rowH = (95.0 - 6.0) / 3.0
    check('F2: высота каждого ряда = (95−6)/3 ≈ 29.67px',
          all(approx(r['h'], rowH, 0.6) for r in vis),
          [round(r['h'], 2) for r in vis])
    # зазор между ВИДИМЫМИ рядами = 3px (ряд 2 скрыт: 1 → 3)
    gap13 = vis[1]['y'] - (vis[0]['y'] + vis[0]['h'])
    check('F3: расстояние между рядами кнопок — 3px (через скрытый слот)',
          approx(gap13, 3, 0.6) or approx(gap13, 3 + rowH + 3, 0.6), gap13)
    # последний видимый ряд не выходит за колонку
    check('F4: ряд 3 — в пределах колонки (не ниже 95px)',
          vis[-1]['y'] + vis[-1]['h'] <= s0['main']['y'] + 95 + 0.6,
          (vis[-1]['y'] + vis[-1]['h']) - (s0['main']['y'] + 95))

    # ---------- кнопки во всю высоту ряда, без переполнения ----------
    check('G: кнопки/селекты ряда 1 — во всю высоту ряда (≈29.7px)',
          all(approx(b['h'], rowH, 1.0) for b in s0['btns']),
          [round(b['h'], 2) for b in s0['btns']])
    check('G2: переполнений кнопок нет (текст входит)',
          not any(b['of'] for b in s0['btns']),
          [b['id'] for b in s0['btns'] if b['of']])

    # ---------- штамп убран, тултип скрыт ----------
    check('H: штампа «данные от» в баре НЕТ; тултип скрыт по умолчанию',
          not s0['stamp'] and s0['tipHidden'] is True, (s0['stamp'], s0['tipHidden']))

    # ---------- тултип: НАВЕДЕНИЕ ----------
    page.hover('#wsRefreshBtn')
    page.wait_for_timeout(300)
    tip1 = page.evaluate("""(function(){
        var tip = document.getElementById('wsRefreshTip');
        var btn = document.getElementById('wsRefreshBtn');
        if (!tip || !btn) return null;
        var t = tip.getBoundingClientRect(), b = btn.getBoundingClientRect();
        return { hidden: tip.hidden, x: t.x, y: t.y, w: t.width, h: t.height,
                 btnY: b.y, btnBottom: b.bottom, btnX: b.x,
                 date: (tip.querySelector('.ws-rt-date')||{}).textContent || '',
                 desc: (tip.querySelector('.ws-rt-desc')||{}).textContent || '',
                 pe: getComputedStyle(tip).pointerEvents };
    })()""")
    check('I: наведение на «Обновить» — тултип ПОКАЗАН',
          tip1 and not tip1['hidden'], tip1)
    check('I2: тултип содержит «данные от ДД.ММ, ЧЧ:ММ» (данные загружены)',
          tip1 and tip1['date'].startswith('данные от ') and len(tip1['date']) >= 18,
          tip1 and tip1['date'])
    check('I3: описание кнопки — в тултипе (бывший title)',
          tip1 and 'Обновить данные графика' in tip1['desc'], tip1 and tip1['desc'][:40])
    above = tip1 and tip1['y'] + tip1['h'] <= tip1['btnY'] + 1.5
    below = tip1 and tip1['y'] >= tip1['btnBottom'] - 1.5
    check('I4: позиция — НАД кнопкой (или под, если сверху нет места)',
          above or below, tip1 and (tip1['y'], tip1['h'], tip1['btnY'], tip1['btnBottom']))
    check('I5: лево тултипа — по кнопке; клики проходят сквозь',
          tip1 and abs(tip1['x'] - tip1['btnX']) <= 2 and tip1['pe'] == 'none',
          tip1 and (tip1['x'], tip1['btnX'], tip1['pe']))
    page.screenshot(path='scripts/task317-proof-tooltip.png', full_page=False)

    # уход курсора — скрыт
    page.mouse.move(640, 300)
    page.wait_for_timeout(300)
    check('I6: уход курсора — тултип скрыт',
          page.evaluate("document.getElementById('wsRefreshTip').hidden"))

    # фокус с клавиатуры — показан; blur — скрыт
    page.evaluate("document.getElementById('wsRefreshBtn').focus()")
    page.wait_for_timeout(200)
    check('J: фокус с клавиатуры — тултип показан',
          not page.evaluate("document.getElementById('wsRefreshTip').hidden"))
    page.evaluate("document.getElementById('wsRefreshBtn').blur()")
    page.wait_for_timeout(200)
    check('J2: потеря фокуса — тултип скрыт',
          page.evaluate("document.getElementById('wsRefreshTip').hidden"))

    # прокрутка — скрыт (fixed-позиция устаревает): реальный скролл
    # окна мероприятий (вложенный overflow-y: auto, scroll-событие
    # ловится capture-фазой слушателя на document)
    page.evaluate("document.getElementById('wsRefreshBtn').focus()")
    page.wait_for_timeout(150)
    scrolled = page.evaluate("(function(){ var el = document.getElementById('wsEventsPanel'); el.scrollTop = 60; return el.scrollTop; })()")
    page.wait_for_timeout(250)
    check('J3: прокрутка (окно мероприятий) — тултип скрыт',
          scrolled > 0 and page.evaluate("document.getElementById('wsRefreshTip').hidden"),
          (scrolled, page.evaluate("document.getElementById('wsRefreshTip').hidden")))
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(200)

    # ---------- клик «Обновить»: тултип закрывается, тост ----------
    page.evaluate("""(function(){
        window.__toasts = [];
        var orig = KipToast.show;
        KipToast.show = function(m){ window.__toasts.push(String(m)); return orig.apply(this, arguments); };
        return true;
    })()""")
    page.hover('#wsRefreshBtn')
    page.wait_for_timeout(250)
    page.click('#wsRefreshBtn')
    page.wait_for_timeout(600)
    toasts = page.evaluate("window.__toasts || []")
    check('K: клик «Обновить» — тултип закрылся, тост «Данные графика обновлены»',
          page.evaluate("document.getElementById('wsRefreshTip').hidden") and
          any('обновлены' in t for t in toasts), toasts)

    # ---------- ПРАВКА: ряд 2 появляется ВНУТРИ колонки ----------
    gridY0 = s0['gridY']
    click_cell(page, TODAY_ISO, '017')
    ok_sel = select_popup_code(page, 'Н')
    close_popups(page)
    page.wait_for_timeout(600)
    check('L: код выбран в попапе (Н)', ok_sel)
    s1 = bar_state(page)
    vis1 = [r for r in s1['rows'] if not r['hidden']]
    check('L2: при правке — ТРИ ряда в колонке (1 → 2 → 3)',
          [r['id'] for r in vis1] == ['wsSelectsRow', 'wsActionsRow', 'wsGenerateRow'],
          [(r['id'], r['hidden']) for r in s1['rows']])
    check('L3: ряд 2 — ВНУТРИ колонки кнопок (не во всю ширину бара)',
          vis1[1]['w'] <= s1['main']['w'] + 1 and approx(vis1[1]['y'], vis1[0]['y'] + rowH + 3, 1.0),
          (vis1[1]['w'], s1['main']['w']))
    check('L4: высоты рядов те же ≈29.67, зазоры 3px',
          all(approx(r['h'], rowH, 0.6) for r in vis1) and
          approx(vis1[1]['y'] - (vis1[0]['y'] + vis1[0]['h']), 3, 0.6) and
          approx(vis1[2]['y'] - (vis1[1]['y'] + vis1[1]['h']), 3, 0.6),
          [(round(r['h'],2)) for r in vis1] +
          [round(vis1[1]['y'] - (vis1[0]['y'] + vis1[0]['h']),2),
           round(vis1[2]['y'] - (vis1[1]['y'] + vis1[1]['h']),2)])
    # точная сумма: низ ряда 3 == низ окон (95px)
    check('L5: три ряда + два зазора — РОВНО низ окон (последний ряд у низа колонки)',
          approx(vis1[2]['y'] + vis1[2]['h'], s1['main']['y'] + s1['main']['h'], 0.6),
          (vis1[2]['y'] + vis1[2]['h']) - (s1['main']['y'] + s1['main']['h']))
    check('L6: колонка/окна/бар НЕ изменились при появлении ряда 2',
          approx(s1['main']['h'], 95, 0.6) and approx(s1['tb']['h'], s0['tb']['h'], 0.6),
          (s1['main']['h'], s1['tb']['h']))
    # сетка под баром не прыгает
    check('L7: сетка под баром НЕ прыгает (ряд 2 не двигает макет)',
          approx(s1['gridY'], gridY0, 1.0), (s1['gridY'], gridY0))
    save_btn = page.evaluate("""(function(){
        var s = document.getElementById('wsSaveBtn'), c = document.getElementById('wsCancelBtn');
        return s && !s.hidden && s.textContent.trim() === 'Сохранить (1)' &&
               c && !c.hidden && c.textContent.trim() === 'Отменить';
    })()""")
    check('L8: «Сохранить (1)» + «Отменить» — в ряду 2', save_btn)
    page.screenshot(path='scripts/task317-proof-rows.png', full_page=False)

    # отмена правок — ряд 2 скрыт, сетка не прыгает
    page.evaluate("""(function(){
        var btns = document.querySelectorAll('.kip-dialog-ok');
        window.__okBtn = btns.length ? btns[btns.length-1] : null;
        return !!window.__okBtn;
    })()""")
    page.click('#wsCancelBtn')
    page.wait_for_timeout(400)
    page.evaluate("""(function(){
        var dlgs = document.querySelectorAll('.kip-dialog');
        var d = dlgs[dlgs.length-1];
        if (d) { var ok = d.querySelector('.kip-dialog-ok'); if (ok) ok.click(); }
        return !!d;
    })()""")
    page.wait_for_timeout(800)
    s2 = bar_state(page)
    check('M: «Отменить» — ряд 2 скрыт, сетка на месте (не прыгает)',
          [r['id'] for r in s2['rows'] if not r['hidden']] == ['wsSelectsRow', 'wsGenerateRow'] and
          approx(s2['gridY'], gridY0, 1.0), (s2['gridY'], gridY0))

    # ---------- светлая тема ----------
    page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(400)
    page.hover('#wsRefreshBtn')
    page.wait_for_timeout(300)
    light = page.evaluate("""(function(){
        var tip = document.getElementById('wsRefreshTip');
        var main = document.querySelector('.ws-toolbar-main');
        return { tipBg: tip && !tip.hidden ? getComputedStyle(tip).backgroundColor : '',
                 shown: tip ? !tip.hidden : false,
                 mainH: main ? main.getBoundingClientRect().height : 0 };
    })()""")
    check('N: светлая тема — тултип показан, фон #fbf8f0',
          light['shown'] and light['tipBg'] == 'rgb(251, 248, 240)', light)
    check('N2: светлая тема — колонка кнопок по-прежнему 95px',
          approx(light['mainH'], 95, 0.6), light['mainH'])
    page.screenshot(path='scripts/task317-proof-light.png', full_page=False)
    page.mouse.move(640, 300)
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    page.wait_for_timeout(200)
    check('N3: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: зритель (ИТР) =================
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    def handle2(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx2.route('**/exec?**', handle2)
    ctx2.route('**script.google.com/**', handle2)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t317-v')")
    page2.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    sv = bar_state(page2)
    visv = [r for r in sv['rows'] if not r['hidden']]
    check('O: зритель — ряды 2/3 скрыты, только ряд 1',
          [r['id'] for r in visv] == ['wsSelectsRow'],
          [(r['id'], r['hidden']) for r in sv['rows']])
    check('O2: зритель — колонка кнопок и окна РОВНО 95px (ряд не растянулся)',
          approx(sv['main']['h'], 95, 0.6) and approx(sv['ev']['h'], 95, 0.6),
          (sv['main'] and sv['main']['h'], sv['ev']['h']))
    check('O3: зритель — кнопка ряда 1 прежних габаритов (не 95px!)',
          all(approx(b['h'], rowH, 1.0) for b in sv['btns']),
          [round(b['h'], 2) for b in sv['btns']])
    page2.hover('#wsRefreshBtn')
    page2.wait_for_timeout(300)
    check('O4: зритель — тултип «данные от» работает и ему',
          not page2.evaluate("document.getElementById('wsRefreshTip').hidden"))
    check('O5: JS-ошибок нет (зритель)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    STATE['role'] = 'Админ'

    # ================= Контекст 3: мобильный 375px =================
    ctx3 = browser.new_context(viewport={'width':375,'height':812})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    def handle3(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx3.route('**/exec?**', handle3)
    ctx3.route('**script.google.com/**', handle3)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.evaluate("localStorage.setItem('kip8_session_token','browser-check-t317-m')")
    page3.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page3.reload()
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    sm = bar_state(page3)
    vism = [r for r in sm['rows'] if not r['hidden']]
    check('P: мобильный — бар колонкой, все ряды/окна вертикально',
          sm['main']['w'] > 0 and sm['rows'][0]['y'] < sm['ev']['y'] < sm['cal']['y'],
          [(r['id'], round(r['y'],1)) for r in sm['rows']])
    check('P2: мобильный — кнопки базовые 34px (не сжаты)',
          all(approx(b['h'], 34, 1.0) for b in sm['btns']),
          [round(b['h'], 2) for b in sm['btns']])
    gapm = vism[1]['y'] - (vism[0]['y'] + vism[0]['h']) if len(vism) > 1 else None
    check('P3: мобильный — зазор между рядами кнопок 3px',
          approx(gapm, 3, 0.6), gapm)
    check('P4: мобильный — рамки бара 5px', sm['pad'] == '5px', sm['pad'])
    page3.screenshot(path='scripts/task317-proof-mobile.png', full_page=False)
    check('P5: JS-ошибок нет (мобильный)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 4: 1024px — ряд 1 без переноса =================
    ctx4 = browser.new_context(viewport={'width':1024,'height':800})
    page4 = ctx4.new_page()
    js_errors4 = []
    page4.on('pageerror', lambda e: js_errors4.append(str(e)))
    def handle4(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx4.route('**/exec?**', handle4)
    ctx4.route('**script.google.com/**', handle4)
    ctx4.route('**raw.githubusercontent.com/**', block_external)
    ctx4.route('**calendar.legalic.ru/**', block_external)
    page4.goto('http://localhost:%d/index.html' % PORT)
    page4.evaluate("localStorage.setItem('kip8_session_token','browser-check-t317-w')")
    page4.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page4.reload()
    page4.wait_for_timeout(2500)
    page4.evaluate("navigateTo('work-schedule')")
    page4.wait_for_timeout(3000)
    sw = bar_state(page4)
    visw = [r for r in sw['rows'] if not r['hidden']]
    check('Q: 1024px — колонка кнопок ровно в высоту окон (95px)',
          approx(sw['main']['h'], 95, 0.6) and approx(sw['ev']['h'], 95, 0.6),
          (sw['main'] and sw['main']['h'], sw['ev']['h']))
    check('Q2: 1024px — ряд 1 ОДНОЙ строкой (без переноса), ряд в высоту ≈29.7',
          all(approx(r['h'], rowH, 0.6) for r in visw) and
          all(approx(b['h'], rowH, 1.0) for b in sw['btns']),
          [round(r['h'],2) for r in visw])
    check('Q3: 1024px — переполнений нет',
          not any(b['of'] for b in sw['btns']),
          [b['id'] for b in sw['btns'] if b['of']])
    check('Q4: JS-ошибок нет (1024px)', len(js_errors4) == 0, js_errors4[:3])
    ctx4.close()

    browser.close()

fails = [r for r in results if not r[1]]
print('\n===== Task 317 browser-check: %d/%d =====' % (len(results) - len(fails), len(results)))
if fails:
    for f in fails:
        print('FAIL: ' + f[0] + ' | ' + str(f[2]))
    sys.exit(1)
