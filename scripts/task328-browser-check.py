# -*- coding: utf-8 -*-
# Task 328: browser-check — заявка пользователя:
#   • кнопка-ЗНАЧОК вкл/выкл ПЕРЕКРЁСТНОЙ подсветки строк и столбцов
#     в шахматке — СЛЕВА от «Сформировать»;
#   • размер всех кнопок бара немного МЕНЬШЕ;
#   • всплывающие подсказки УБРАНЫ: два окна бара (мероприятия,
#     время/праздники) + кнопки «Итоги учёта»/«Месяц»/«Год»/
#     «Отменить»;
#   • у «Сформировать» — подсказка ФОРМАТА «Обновить» (окно).
# Проверки (десктоп 1280 Админ): кнопка есть/слева/иконка/svg,
#   aria-pressed, тост, localStorage, ВЫКЛ — наведение НЕ
#   подсвечивает, ВКЛ — перекрестье работает (строка+столбец),
#   сохранение состояния после перезагрузки; высоты кнопок
#   (29-30px ряда) и шрифт 13/12px; НЕТ title у кнопок и окон;
#   окно #wsGenerateTip: hidden → hover показывает → уход
#   скрывает, содержимое, в <body>; мобайл 375: кнопка 32×32,
#   ряд не выпирает. 0 JS-ошибок.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8942
TODAY = datetime.date.today()
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
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','переработка':1,'источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-04' % (Y, M),'таб_номер':'017','статус':'д','источник':'руч'},
  {'id':4,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-05' % (Y, M),'таб_номер':'023','статус':'ОТ','источник':'авто'},
  {'id':6,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'023','статус':'И','источник':'авто'}
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
        return {'ok':True,'data':{'entries':ENTRIES}}
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t328)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_cross_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280px, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'browser-check-t328')

    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- кнопка-иконка перекрестья: место/иконка/состояние ----------
    s0 = page.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        var gen = document.getElementById('wsGenerateBtn');
        if (!cross || !gen) return null;
        var row = document.getElementById('wsActionsRow');
        var kids = row ? Array.prototype.slice.call(row.children).map(function(e){return e.id;}) : [];
        var cr = cross.getBoundingClientRect();
        var gr = gen.getBoundingClientRect();
        var svg = cross.querySelector('svg');
        return {
            inRow: row ? row.contains(cross) : false,
            order: kids,
            leftOfGen: cr.right <= gr.left + 1,
            pressed: cross.getAttribute('aria-pressed'),
            label: cross.getAttribute('aria-label'),
            title: cross.getAttribute('title'),
            hasSvg: !!svg,
            svgSize: svg ? Math.round(svg.getBoundingClientRect().width) + 'x' + Math.round(svg.getBoundingClientRect().height) : null,
            w: Math.round(cr.width), h: Math.round(cr.height),
            genVisible: !gen.hidden,
            genFont: getComputedStyle(gen).fontSize,
            genH: Math.round(gr.height)
        };
    })""")
    check('C: #wsCrossBtn есть, в ряду 3 ДЕЙСТВИЙ', s0 and s0['inRow'], s0)
    check('C2: СЛЕВА от «Сформировать» (заявка)', s0 and s0['leftOfGen'], s0)
    # Task 332: КНОПКА ВИДА wsViewBtn — САМАЯ ЛЕВАЯ (левее перекрестья);
    # Task 333: у кнопки вида ПОДПИСЬ «Вид» — перекрестье ВТОРОЕ слева
    check('C3: порядок ряда: вид → перекрестье → Сформировать',
          s0 and s0['order'][:2] == ['wsViewBtn', 'wsCrossBtn'], s0)
    check('C4: иконка svg ~16px, БЕЗ текста', s0 and s0['hasSvg'] and s0['svgSize'] == '16x16', s0)
    check('C5: aria-pressed=true (ВКЛ по умолчанию)', s0 and s0['pressed'] == 'true', s0)
    check('C6: aria-label для скринридеров', s0 and s0['label'] and 'перекрёстная' in s0['label'].lower(), s0)
    check('C7: НЕТ нативного title (заявка: без подсказок)', s0 and not s0['title'], s0)

    # ---------- размеры кнопок: немного меньше ----------
    s1 = page.evaluate("""(function(){
        function info(id){
            var el = document.getElementById(id);
            if (!el) return null;
            var r = el.getBoundingClientRect();
            var cs = getComputedStyle(el);
            return {h: Math.round(r.height), font: cs.fontSize, pad: cs.padding};
        }
        return {
            cross: info('wsCrossBtn'),
            gen: info('wsGenerateBtn'),
            refresh: info('wsRefreshBtn'),
            totals: info('wsTotalsBtn'),
            tabM: info('wsTtTabMonth'),
            monthSel: info('wsMonthSel'),
            svgRefresh: (function(){
                var s = document.querySelector('#wsRefreshBtn svg');
                if (!s) return null;
                return Math.round(s.getBoundingClientRect().width);
            })()
        };
    })""")
    check('D: кнопки ряда ~29-30px (высота ряда, меньше прежних 34px)',
          s1 and s1['gen'] and 28 <= s1['gen']['h'] <= 31, s1)
    check('D2: шрифт кнопок 13px (был 14px)',
          s1 and s1['gen']['font'] == '13px' and s1['refresh']['font'] == '13px' and s1['totals']['font'] == '13px', s1)
    check('D3: иконка «Обновить» 13px (была 14px)', s1 and s1['svgRefresh'] == 13, s1)
    check('D4: вкладка «Месяц» 12px (была 13px)',
          s1 and s1['tabM'] and s1['tabM']['font'] == '12px', s1)

    # ---------- ВЫКЛЮЧЕНИЕ перекрестья кнопкой ----------
    page.click('#wsCrossBtn')
    page.wait_for_timeout(400)
    s2 = page.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        var toast = document.getElementById('toastMessage');
        return {
            pressed: cross.getAttribute('aria-pressed'),
            ls: localStorage.getItem('kip8_ws_cross_v1'),
            toast: toast ? toast.textContent : ''
        };
    })""")
    check('E: клик — ВЫКЛЮЧЕНО (aria-pressed=false)', s2['pressed'] == 'false', s2)
    check('E2: выбор сохранён в localStorage ("0")', s2['ls'] == '0', s2)
    check('E3: тост «выключена»', 'выключена' in s2['toast'], s2)

    # наведение при ВЫКЛЮЧЕНОМ перекрестье — подсветки НЕТ
    page.hover('td.ws-cell[data-day="3"]')
    page.wait_for_timeout(300)
    s3 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        var anyRow = false;
        for (var i=0;i<rows.length;i++) if (rows[i].classList.contains('ws-hover-row')) anyRow = true;
        var anyCol = !!document.querySelector('#wsGridWrap .ws-hover-col');
        var anyCell = !!document.querySelector('#wsGridWrap td.ws-hover');
        return {anyRow: anyRow, anyCol: anyCol, anyCell: anyCell};
    })""")
    check('F: ВЫКЛ: наведение НЕ подсвечивает (строка/столбец чисты)',
          not s3['anyRow'] and not s3['anyCol'] and not s3['anyCell'], s3)

    # ---------- ВКЛЮЧЕНИЕ обратно — перекрестье работает ----------
    page.click('#wsCrossBtn')
    page.wait_for_timeout(400)
    s4 = page.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        return {pressed: cross.getAttribute('aria-pressed'),
                ls: localStorage.getItem('kip8_ws_cross_v1')};
    })""")
    check('G: клик — ВКЛЮЧЕНО (aria-pressed=true)', s4['pressed'] == 'true', s4)
    check('G2: localStorage "1"', s4['ls'] == '1', s4)

    page.hover('td.ws-cell[data-day="3"]')
    page.wait_for_timeout(300)
    s5 = page.evaluate("""(function(){
        var cells = document.querySelectorAll('td.ws-cell[data-day="3"]');
        if (!cells.length) return null;
        var tr = cells[0].closest('tr');
        var th = document.querySelector('th[data-day="3"]');
        return {
            rowOn: tr.classList.contains('ws-hover-row'),
            colOn: th ? th.classList.contains('ws-hover-col') : null,
            cellOn: cells[0].classList.contains('ws-hover')
        };
    })""")
    check('H: ВКЛ: перекрестье работает — строка+столбец+ячейка',
          s5 and s5['rowOn'] and s5['colOn'] and s5['cellOn'], s5)

    # уход курсора с ячеек — подсветка снята
    try:
        page.hover('#wsMonthSel', timeout=2000)
    except Exception:
        pass
    page.wait_for_timeout(250)
    s6 = page.evaluate("(function(){ return !!document.querySelector('#wsGridWrap tr.ws-hover-row'); })()")
    check('H2: уход с ячеек снимает подсветку', not s6, s6)

    # ---------- перезагрузка: состояние ВЫКЛ восстановилось ----------
    page.click('#wsCrossBtn')  # снова ВЫКЛ
    page.wait_for_timeout(250)
    page.reload()
    page.wait_for_timeout(2500)
    # после перезагрузки приложение на дашборде — вернуть модуль
    # графика (init модуля читает localStorage при инициализации)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    s7 = page.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        return {pressed: cross ? cross.getAttribute('aria-pressed') : null,
                ls: localStorage.getItem('kip8_ws_cross_v1')};
    })""")
    check('I: перезагрузка — сохранённое ВЫКЛ восстановлено', s7['pressed'] == 'false' and s7['ls'] == '0', s7)
    # вернуть ВКЛ для последующих проверок
    page.evaluate("WorkSchedule.toggleCross()")
    page.wait_for_timeout(200)

    # ---------- тултипы УБРАНЫ: кнопки без title ----------
    s8 = page.evaluate("""(function(){
        var ids = ['wsTotalsBtn','wsTtTabMonth','wsTtTabYear','wsCancelBtn','wsGenerateBtn'];
        var res = {};
        for (var i=0;i<ids.length;i++){
            var el = document.getElementById(ids[i]);
            res[ids[i]] = el ? (el.getAttribute('title') || '') : 'NO_EL';
        }
        return res;
    })""")
    check('J: кнопки БЕЗ нативного title (Итоги/Месяц/Год/Отменить/Сформировать)',
          all(v == '' for v in s8.values()), s8)

    # ---------- тултипы УБРАНЫ: два окна бара ----------
    s9 = page.evaluate("""(function(){
        var ev = document.getElementById('wsEventsPanel');
        var cal = document.getElementById('wsCalPanel');
        return {
            evTitles: ev ? (ev.innerHTML.match(/title=/g) || []).length : -1,
            calTitles: cal ? (cal.innerHTML.match(/title=/g) || []).length : -1,
            evShown: ev ? !ev.hidden : null,
            calShown: cal ? !cal.hidden : null
        };
    })""")
    check('K: окно мероприятий — БЕЗ title (заявка)', s9['evTitles'] == 0 and s9['evShown'], s9)
    check('K2: окно времени/праздников — БЕЗ title (заявка)', s9['calTitles'] == 0 and s9['calShown'], s9)

    # ---------- окно «Сформировать»: формат «Обновить» ----------
    s10 = page.evaluate("""(function(){
        var tip = document.getElementById('wsGenerateTip');
        if (!tip) return null;
        return {
            inBody: tip.parentNode === document.body,
            hidden0: tip.hidden,
            cls: tip.className,
            hasDate: !!tip.querySelector('.ws-rt-date'),
            hasDesc: !!tip.querySelector('.ws-rt-desc'),
            head: tip.querySelector('.ws-rt-date') ? tip.querySelector('.ws-rt-date').textContent : '',
            desc: tip.querySelector('.ws-rt-desc') ? tip.querySelector('.ws-rt-desc').textContent : ''
        };
    })""")
    check('L: #wsGenerateTip есть, формат ws-refresh-tip (как «Обновить»)',
          s10 and s10['cls'].find('ws-refresh-tip') != -1 and s10['hasDate'] and s10['hasDesc'], s10)
    check('L2: скрыто по умолчанию, перенесено в <body>',
          s10 and s10['hidden0'] and s10['inBody'], s10)
    check('L3: заголовок «Сформировать шахматку» + описание с диалогом',
          s10 and s10['head'] == 'Сформировать шахматку' and 'диалог' in s10['desc'], s10)

    # hover по «Сформировать» — окно появляется НАД кнопкой
    page.hover('#wsGenerateBtn')
    page.wait_for_timeout(300)
    s11 = page.evaluate("""(function(){
        var tip = document.getElementById('wsGenerateTip');
        var btn = document.getElementById('wsGenerateBtn');
        if (!tip || !btn) return null;
        var tr = tip.getBoundingClientRect();
        var br = btn.getBoundingClientRect();
        return {hidden: tip.hidden, top: Math.round(tr.top), btnTop: Math.round(br.top),
                bottom: Math.round(tr.bottom), left: Math.round(tr.left)};
    })""")
    check('M: hover «Сформировать» — окно ПОКАЗАЛОСЬ', s11 and not s11['hidden'], s11)
    check('M2: окно НАД кнопкой (низ окна выше верха кнопки)',
          s11 and s11['bottom'] <= s11['btnTop'] + 1, s11)
    # уход курсора — окно скрылось
    try:
        page.hover('#wsMonthSel', timeout=2000)
    except Exception:
        pass
    page.wait_for_timeout(250)
    s12 = page.evaluate("(function(){ return document.getElementById('wsGenerateTip').hidden; })")
    check('M3: уход курсора — окно СКРЫТО', s12 == True, s12)

    check('N: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375px, Админ =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':700}, 'browser-check-t328-m')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    s20 = page2.evaluate("""(function(){
        var cross = document.getElementById('wsCrossBtn');
        if (!cross) return null;
        var r = cross.getBoundingClientRect();
        var row = document.getElementById('wsActionsRow');
        var rr = row.getBoundingClientRect();
        return {w: Math.round(r.width), h: Math.round(r.height),
                pressed: cross.getAttribute('aria-pressed'),
                rowRight: rr.right <= 375, visible: r.width > 0};
    })""")
    check('O: мобайл — кнопка 32×32, видна, ВКЛ',
          s20 and s20['w'] == 32 and s20['h'] == 32 and s20['pressed'] == 'true' and s20['visible'], s20)
    check('O2: мобайл — ряд действий не выпирает за экран', s20 and s20['rowRight'], s20)
    # тумблер на мобайле тоже работает
    page2.evaluate("WorkSchedule.toggleCross()")
    page2.wait_for_timeout(200)
    s21 = page2.evaluate("(function(){ return document.getElementById('wsCrossBtn').getAttribute('aria-pressed'); })")
    check('O3: мобайл — переключение работает', s21 == 'false', s21)
    check('P: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
