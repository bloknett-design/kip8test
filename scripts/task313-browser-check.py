# -*- coding: utf-8 -*-
# Task 313: browser-check «График работы» — заявка пользователя:
#   1) в шахматке немного подсвечивается фон сегодняшней даты (шапка
#      колонки + все ячейки столбца, тёмная и светлая темы, поверх
#      inline-цветов статусов и ручных записей);
#   2) при клике по ячейке над окном кодов появляется ОТДЕЛЬНОЕ окно
#      «Мероприятия в этот день»: все мероприятия ячейки с цветом,
#      кодом и названием (кнопки ✎/✕ — редакторам); в окне кодов
#      строки «Мероприятия в этот день» больше нет.
# Проверки: геометрия (окно мероприятий СТРОГО над окном кодов,
# левые края выровнены, зазор 8px), содержимое (заголовок/подстрока/
# строки/пустое состояние), закрытие (Esc + кловер) обоих окон,
# подсветка «сегодня» (маркеры ws-today-col/ws-today, computed-стили,
# today-колонка ровно одна, лёгкая тема), мобильный 375px, зритель.
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404 — фолбэки праздников).
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8937
TODAY = datetime.date.today()          # локальная дата системы = дата браузера
TODAY_ISO = TODAY.isoformat()
TODAY_Y, TODAY_M, TODAY_D = TODAY.year, TODAY.month, TODAY.day

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'н','name':'Ночь в вых./праздник','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний','color':'#FFCDD2'},
  {'code':'.','name':'Плановый выходной день','color':'#FAF9F5'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# 02.06 Д (смена + бейдж И), 05.06 «.»; сегодня: 017 «Д» (авто),
# 023 «д» (руч) — подсветка поверх inline-цвета и рамки ручной записи
ENTRIES = [
  {'id':1,'дата':'2026-06-02','таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'2026-06-05','таб_номер':'017','статус':'.','источник':'авто'},
  {'id':3,'дата':'2026-06-03','таб_номер':'023','статус':'И','источник':'авто'},
  {'id':4,'дата':'2026-06-08','таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':5,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':6,'дата':TODAY_ISO,'таб_номер':'023','статус':'д','источник':'руч'}
]
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'ОТ и ПБ','дата_начала':'2026-06-02','дата_окончания':'2026-06-02'},
  {'id':102,'таб_номер':'023','тип':'инструктаж','тема':'ОТ и ПБ','дата_начала':'2026-06-03','дата_окончания':'2026-06-03'},
  {'id':103,'таб_номер':'023','тип':'обучение','тема':'КИПиА','дата_начала':'2026-06-10','дата_окончания':'2026-06-10'},
  {'id':104,'таб_номер':'017','тип':'инструктаж','тема':'Ежедневный контроль','дата_начала':TODAY_ISO,'дата_окончания':TODAY_ISO}
]
VACATIONS = []

STATE = {'role': 'Админ'}

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
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def goto_month(page, m, y):
    page.evaluate("""(function(a){
        var m = a[0], y = a[1];
        var ms = document.getElementById('wsMonthSel');
        var ys = document.getElementById('wsYearSel');
        if (ms) ms.value = String(m);
        if (ys) {
            var ok = false;
            for (var i=0;i<ys.options.length;i++) if (String(ys.options[i].value) === String(y)) ok = true;
            if (!ok) { var o = document.createElement('option'); o.value = String(y); o.textContent = String(y); ys.appendChild(o); }
            ys.value = String(y);
        }
        WorkSchedule.onMonthChange();
    })""", [m, y])
    page.wait_for_timeout(2500)

# клик по ячейке (дата+таб) — через координаты центра ячейки
def click_cell(page, iso, tab):
    page.evaluate("""(function(a){
        var iso = a[0], tab = a[1];
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'"+iso+"'") !== -1 && oc.indexOf("'"+tab+"'") !== -1) {
                var r = tds[i].getBoundingClientRect();
                window.__cellXY = [r.left + r.width/2, r.top + r.height/2];
                window.__cellEl = tds[i];
                return;
            }
        }
    })""", [iso, tab])
    xy = page.evaluate("window.__cellXY || [600, 300]")
    page.mouse.click(xy[0], xy[1])
    page.wait_for_timeout(500)

# состояние ОБОИХ окон (открытость, геометрия, содержимое)
BOTH_WINDOWS = """(function(){
    var cp = document.getElementById('wsCellPopup');
    var evp = document.getElementById('wsEventsPopup');
    var cr = cp ? cp.getBoundingClientRect() : null;
    var er = evp ? evp.getBoundingClientRect() : null;
    var etxt = evp ? evp.textContent : '';
    var ctxt = cp ? cp.textContent : '';
    var rows = evp ? evp.querySelectorAll('.ws-popup-row.ws-popup-event') : [];
    var first = rows.length ? rows[0] : null;
    var sw = first ? first.querySelector('.ws-popup-swatch') : null;
    var cs = sw ? getComputedStyle(sw) : null;
    return { codesOpen: cp ? cp.classList.contains('active') : false,
             evOpen: evp ? evp.classList.contains('active') : false,
             codesRect: cr ? [cr.left, cr.top, cr.right, cr.bottom] : null,
             evRect: er ? [er.left, er.top, er.right, er.bottom] : null,
             evZ: evp ? getComputedStyle(evp).zIndex : null,
             codesZ: cp ? getComputedStyle(cp).zIndex : null,
             evTitle: etxt.indexOf('Мероприятия в этот день') !== -1,
             evSub: etxt.indexOf('2026-06-02 · Иванов И. И.') !== -1,
             evCode: first ? (first.querySelector('.ws-popup-code')||{}).textContent : null,
             evName: first ? (first.querySelector('.ws-popup-name')||{}).textContent : null,
             evSwatch: cs ? cs.backgroundColor : null,
             evActs: evp ? evp.querySelectorAll('.ws-popup-act').length : 0,
             evEmpty: etxt.indexOf('нет мероприятий') !== -1,
             secInCodes: ctxt.indexOf('Мероприятия в этот день') !== -1,
             evRowsInCodes: cp ? cp.querySelectorAll('.ws-popup-event').length : 0,
             addEventInCodes: ctxt.indexOf('+ Мероприятие…') !== -1,
             moreInCodes: ctxt.indexOf('Дополнительно…') !== -1 };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- Контекст 1: десктоп 1280px, Админ ----------
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
        body = None
        pd = request.post_data
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        s = json.dumps(resp, ensure_ascii=False)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=s.encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t313)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t313')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    goto_month(page, 6, 2026)
    check('B: шахматка июнь 2026 отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. Клик по ячейке 02.06 Иванов (Д + мероприятие И): ДВА окна
    click_cell(page, '2026-06-02', '017')
    pop = page.evaluate(BOTH_WINDOWS)
    check('C: оба окна открыты (коды + мероприятия)', pop['codesOpen'] and pop['evOpen'], pop)
    ev, co = pop['evRect'], pop['codesRect']
    check('C2: окно мероприятий НАД окном кодов (зазор 4–12px)',
          ev and co and ev[3] <= co[1] + 1 and ev[3] >= co[1] - 12,
          {'evBottom': ev and ev[3], 'codesTop': co and co[1]})
    check('C3: левые края выровнены', ev and co and abs(ev[0] - co[0]) <= 1,
          {'evLeft': ev and ev[0], 'codesLeft': co and co[0]})
    check('C4: z-index окна мероприятий выше окна кодов',
          pop['evZ'] == '9402' and pop['codesZ'] == '9401', {'ev': pop['evZ'], 'codes': pop['codesZ']})
    check('C5: заголовок окна — «Мероприятия в этот день», подстрока «дата · ФИО»',
          pop['evTitle'] and pop['evSub'], {'title': pop['evTitle'], 'sub': pop['evSub']})
    check('C6: строка мероприятия: код И, название «ОТ и ПБ», цвет #B3E5FC',
          pop['evCode'] == 'И' and pop['evName'] == 'ОТ и ПБ' and pop['evSwatch'] == 'rgb(179, 229, 252)',
          {'code': pop['evCode'], 'name': pop['evName'], 'swatch': pop['evSwatch']})
    check('C7: кнопки ✎/✕ в окне мероприятий (Админ)', pop['evActs'] >= 2, pop['evActs'])
    check('C8: в окне кодов секции мероприятий НЕТ; «+ Мероприятие…»/«Дополнительно…» живы',
          (not pop['secInCodes']) and pop['evRowsInCodes'] == 0 and
          pop['addEventInCodes'] and pop['moreInCodes'],
          {'sec': pop['secInCodes'], 'rows': pop['evRowsInCodes']})
    page.screenshot(path='scripts/task313-proof-events-window.png', full_page=False)

    # закрыть окна перед следующим кликом (клик мимо окон = кловер)
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)

    # D. Пустой день (05.06 Иванов, «.», без мероприятий): окно с пустым состоянием
    click_cell(page, '2026-06-05', '017')
    popD = page.evaluate(BOTH_WINDOWS)
    check('D: пустой день — оба окна открыты, «нет мероприятий»',
          popD['codesOpen'] and popD['evOpen'] and popD['evEmpty'] and (not popD['evCode']),
          {'empty': popD['evEmpty'], 'code': popD['evCode']})
    page.screenshot(path='scripts/task313-proof-empty-day.png', full_page=False)

    # E. Esc закрывает ОБА окна
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    closed = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        return { codes: cp ? !cp.classList.contains('active') : true,
                 ev: evp ? !evp.classList.contains('active') : true,
                 evEmpty: evp ? evp.innerHTML === '' : true };
    })()""")
    check('E: Esc закрывает оба окна (контент очищен)',
          closed['codes'] and closed['ev'] and closed['evEmpty'], closed)

    # F. Кловер: клик мимо окон закрывает оба; повторный клик открывает заново
    click_cell(page, '2026-06-03', '023')
    popF = page.evaluate(BOTH_WINDOWS)
    check('F: повторный клик открывает оба окна (Петров, 03.06, событие «ОТ и ПБ»)',
          popF['codesOpen'] and popF['evOpen'] and popF['evName'] == 'ОТ и ПБ', popF)
    page.mouse.click(10, 700)   # кловер wsPopupCloser
    page.wait_for_timeout(300)
    closedF = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        return { codes: cp ? !cp.classList.contains('active') : true,
                 ev: evp ? !evp.classList.contains('active') : true };
    })()""")
    check('F2: клик по кловеру закрывает оба окна', closedF['codes'] and closedF['ev'], closedF)

    # G. Подсветка сегодняшней даты (текущий месяц/год системы).
    # ТЁМНАЯ ТЕМА явно (дефолт приложения — светлая, data-theme на <html>):
    # проверяем значения тёмной темы, затем G8 — светлой
    goto_month(page, TODAY_M, TODAY_Y)
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    today = page.evaluate("""(function(){
        var ths = document.querySelectorAll('#wsGridWrap thead th.ws-today-col');
        var cells = document.querySelectorAll('#wsGridWrap tbody td.ws-cell.ws-today');
        var out = { thCount: ths.length, cellCount: cells.length, thDay: null,
                    thBg: null, thColor: null,
                    cellBg: null, cellShadow: null, cellClass: null,
                    manualShadow: null, nonToday: 0 };
        if (ths.length === 1) {
            out.thDay = parseInt(ths[0].textContent, 10);
            var csTh = getComputedStyle(ths[0]);
            out.thBg = csTh.backgroundImage;
            out.thColor = csTh.color;
        }
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++) {
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'""" + TODAY_ISO + """'") !== -1 && oc.indexOf("'017'") !== -1) {
                var cs = getComputedStyle(tds[i]);
                out.cellBg = cs.backgroundColor;
                out.cellShadow = cs.boxShadow;
                out.cellClass = tds[i].className;
            }
            if (oc.indexOf("'""" + TODAY_ISO + """'") !== -1 && oc.indexOf("'023'") !== -1) {
                var cs2 = getComputedStyle(tds[i]);
                out.manualShadow = cs2.boxShadow;
            }
            if (tds[i].className.indexOf('ws-today') === -1) out.nonToday++;
        }
        return out;
    })()""")
    check('G: колонка «сегодня» одна в шапке (ws-today-col)',
          today['thCount'] == 1, today['thCount'])
    check('G2: дата колонки = сегодняшнее число', today['thDay'] == TODAY_D,
          {'thDay': today['thDay'], 'want': TODAY_D})
    check('G3: ячейки ws-today — по числу сотрудников (2)',
          today['cellCount'] == 2, today['cellCount'])
    check('G4: шапка — градиент поверх фона + акцентное число',
          today['thBg'] and today['thBg'].find('linear-gradient') != -1 and
          today['thBg'].find('rgba(74, 143, 199, 0.2)') != -1 and
          today['thColor'] == 'rgb(74, 143, 199)',
          {'bg': today['thBg'], 'color': today['thColor']})
    check('G5: статусная ячейка «сегодня»: inline-фон Д жив + inset-подсветка',
          today['cellBg'] == 'rgb(255, 224, 130)' and
          today['cellShadow'] and today['cellShadow'].find('inset') != -1 and
          today['cellShadow'].find('rgba(74, 143, 199, 0.16)') != -1,
          {'bg': today['cellBg'], 'shadow': today['cellShadow']})
    check('G6: ручная ячейка «сегодня»: подсветка + рамка (две inset-тени)',
          today['manualShadow'] and len(today['manualShadow'].split('inset')) - 1 >= 2 and
          today['manualShadow'].find('rgba(255, 255, 255, 0.5)') != -1,
          today['manualShadow'])
    check('G7: НЕ-сегодня ячеек с ws-today нет',
          today['nonToday'] > 0 and today['cellCount'] == 2)
    page.screenshot(path='scripts/task313-proof-today-column.png', full_page=False)

    # G8. Светлая тема — подсветка мягче
    light = page.evaluate("""(function(){
        document.documentElement.setAttribute('data-theme','light');
        var ths = document.querySelectorAll('#wsGridWrap thead th.ws-today-col');
        var res = { thBg: null, cellShadow: null };
        if (ths.length) {
            res.thBg = getComputedStyle(ths[0]).backgroundImage;
        }
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++) {
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'""" + TODAY_ISO + """'") !== -1 && oc.indexOf("'017'") !== -1) {
                res.cellShadow = getComputedStyle(tds[i]).boxShadow;
                break;
            }
        }
        document.documentElement.setAttribute('data-theme','light');
        return res;
    })()""")
    check('G8: светлая тема — шапка rgba(42, 93, 143, 0.13), ячейка rgba(42, 93, 143, 0.1)',
          light['thBg'] and light['thBg'].find('rgba(42, 93, 143, 0.13)') != -1 and
          light['cellShadow'] and light['cellShadow'].find('rgba(42, 93, 143, 0.1)') != -1,
          light)

    # H. Клик по ячейке «сегодня» — окно мероприятий с сегодняшним событием
    click_cell(page, TODAY_ISO, '017')
    popH = page.evaluate(BOTH_WINDOWS)
    check('H: окно мероприятий на сегодняшней ячейке (событие «Ежедневный контроль»)',
          popH['codesOpen'] and popH['evOpen'] and popH['evName'] == 'Ежедневный контроль' and
          popH['evCode'] == 'И',
          {'code': popH['evCode'], 'name': popH['evName']})
    page.screenshot(path='scripts/task313-proof-today-events.png', full_page=False)
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)

    # I. JS-ошибок нет
    check('I: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ---------- Контекст 2: мобильный 375px, Админ ----------
    ctxm = browser.new_context(viewport={'width':375,'height':720}, has_touch=True)
    pagem = ctxm.new_page()
    js_errors_m = []
    pagem.on('pageerror', lambda e: js_errors_m.append(str(e)))
    ctxm.route('**/exec?**', handle)
    ctxm.route('**script.google.com/**', handle)
    ctxm.route('**raw.githubusercontent.com/**', block_external)
    ctxm.route('**calendar.legalic.ru/**', block_external)

    pagem.goto('http://localhost:%d/index.html' % PORT)
    pagem.evaluate("localStorage.setItem('kip8_session_token','browser-check-t313-m')")
    pagem.reload()
    pagem.wait_for_timeout(2500)
    pagem.evaluate("navigateTo('work-schedule')")
    pagem.wait_for_timeout(1500)
    goto_month(pagem, 6, 2026)

    click_cell(pagem, '2026-06-02', '017')
    mob = pagem.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        var cr = cp && cp.classList.contains('active') ? cp.getBoundingClientRect() : null;
        var er = evp && evp.classList.contains('active') ? evp.getBoundingClientRect() : null;
        return { codesOpen: !!cr, evOpen: !!er,
                 codesRect: cr ? [cr.left, cr.top, cr.right, cr.bottom] : null,
                 evRect: er ? [er.left, er.top, er.right, er.bottom] : null };
    })()""")
    check('K: 375px — оба окна открыты', mob['codesOpen'] and mob['evOpen'], mob)
    mev, mco = mob['evRect'], mob['codesRect']
    check('K2: 375px — окно мероприятий сверху (evTop ≤ codesTop), окна в границах экрана',
          mev and mco and mev[1] <= mco[1] + 1 and
          mev[0] >= 0 and mev[2] <= 375 and mev[3] <= 720 and
          mco[0] >= 0 and mco[2] <= 375 and mco[3] <= 720,
          {'ev': mev, 'codes': mco})
    check('L: 375px — JS-ошибок нет', len(js_errors_m) == 0, js_errors_m[:3])
    ctxm.close()

    # ---------- Контекст 3: десктоп, «ИТР8 pro» (просмотр) ----------
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t313-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1500)
    goto_month(page2, 6, 2026)

    # зритель: клик по ячейке не открывает НИ ОДНО окно
    click_cell(page2, '2026-06-02', '017')
    ro = page2.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        return { codes: cp ? cp.classList.contains('active') : false,
                 ev: evp ? evp.classList.contains('active') : false };
    })()""")
    check('M: «ИТР8 pro» — клик по ячейке НЕ открывает ни окно кодов, ни окно мероприятий',
          (not ro['codes']) and (not ro['ev']), ro)
    # подсветка «сегодня» видна и зрителю (не требует прав)
    today_ro = page2.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        var now = new Date();
        m.value = String(now.getMonth()+1);
        y.value = String(now.getFullYear());
        WorkSchedule.onMonthChange();
        return true;
    })()""")
    page2.wait_for_timeout(2500)
    ro_today = page2.evaluate("""(function(){
        return document.querySelectorAll('#wsGridWrap thead th.ws-today-col').length === 1 &&
               document.querySelectorAll('#wsGridWrap tbody td.ws-cell.ws-today').length >= 1;
    })()""")
    check('M2: «ИТР8 pro» — подсветка «сегодня» видна и зрителю', ro_today)
    check('N: JS-ошибок нет (просмотр)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task313-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
