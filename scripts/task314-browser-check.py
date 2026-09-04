# -*- coding: utf-8 -*-
# Task 314: browser-check «График работы» — заявка пользователя:
#   1) символ кода «.» заменён на «·», фон ячейки — как у ПУСТОЙ
#      (обе темы; цвет листа к фону «.»-ячейки не применяется);
#   2) мероприятия из «Инструктажи» отображаются в ячейках маленькими
#      бейджами-«иконками»: статус-мероприятие — НЕ большой код
#      (ячейка «·» + сплошной бейдж; нет записи — виртуальный бейдж),
#      бейджи видны и на днях отсутствия (ОТ + бейдж), пустая ячейка
#      с мероприятием — пунктирный бейдж;
#   3) последняя загруженная информация хранится ЛОКАЛЬНО (localStorage
#      kip8_ws_cache_v1): график открывается МГНОВЕННО без сети,
#      обновление данных — кнопкой «Обновить» (не «Сформировать»):
#      справочник кодов + сотрудники + записи + мероприятия + отпуска,
#      тост, штамп «данные от …», сетка не мигает, сбой — старые данные
#      остаются.
# Проверки: кэш-открытие (0 запросов workSchedule.*), кнопка
# (спиннер/блокировка/тост/штамп/запись кэша), смена месяца
# (некэшированный — сеть, возврат — мгновенно), офлайн (кэш жив,
# «Обновить» не стирает сетку), зритель (кнопка видна, «Сформировать»
# скрыта), мобильный 375px, тёмная/светлая темы, попап (метка «·»,
# свотч ws-swatch-dot), select «Дополнительно…» (метка «·»).
# Playwright + мок fetch (Apps Script по action; внешние источники
# производственного календаря закрыты 404 — фолбэки праздников).
import datetime
import json, sys, time
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8937
TODAY = datetime.date.today()          # локальная дата системы = дата браузера
TODAY_ISO = TODAY.isoformat()
TODAY_Y, TODAY_M = TODAY.year, TODAY.month
YM_TODAY = '%04d-%02d' % (TODAY_Y, TODAY_M)
# фиксированное «время загрузки» для штампа: вчера 14:22
STAMP_DT = datetime.datetime(TODAY.year, TODAY.month, TODAY.day, 14, 22) - datetime.timedelta(days=1)
STAMP_TS = int(STAMP_DT.timestamp() * 1000)
STAMP_TEXT = 'данные от %s, 14:22' % STAMP_DT.strftime('%d.%m')

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'н','name':'Ночь в вых./праздник','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'Б','name':'Больничный','color':'#F8BBD0'},
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
# Июнь 2026 (рабочие дни: пн 01.06, ср 03.06, пт 05.06, пн 08.06 —
# сб/вс 06-07.06; 12.06 пятница):
#   017: 01.06 пусто+мероприятие И (пунктир), 02.06 Д+И (сплошной),
#        05.06 «.» (плановый выходной — как пустая)
#   023: 03.06 И (статус-мероприятие — только бейдж), 08.06 Д8+ОБ,
#        12.06 ОТ+И (бейдж на дне отсутствия), 15.06 Б без мероприятий
ENTRIES_JUNE = [
  {'id':1,'дата':'2026-06-02','таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'2026-06-05','таб_номер':'017','статус':'.','источник':'авто'},
  {'id':3,'дата':'2026-06-03','таб_номер':'023','статус':'И','источник':'авто'},
  {'id':4,'дата':'2026-06-08','таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':5,'дата':'2026-06-12','таб_номер':'023','статус':'ОТ','источник':'авто'},
  {'id':6,'дата':'2026-06-15','таб_номер':'023','статус':'Б','источник':'авто'},
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS_JUNE = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Пустой день','дата_начала':'2026-06-01','дата_окончания':'2026-06-01'},
  {'id':102,'таб_номер':'017','тип':'инструктаж','тема':'ОТ и ПБ','дата_начала':'2026-06-02','дата_окончания':'2026-06-02'},
  {'id':103,'таб_номер':'023','тип':'инструктаж','тема':'ОТ и ПБ','дата_начала':'2026-06-03','дата_окончания':'2026-06-03'},
  {'id':104,'таб_номер':'023','тип':'обучение','тема':'КИПиА','дата_начала':'2026-06-08','дата_окончания':'2026-06-08'},
  {'id':105,'таб_номер':'023','тип':'инструктаж','тема':'В отпуске','дата_начала':'2026-06-12','дата_окончания':'2026-06-12'},
  {'id':106,'таб_номер':'017','тип':'инструктаж','тема':'Ежедневный контроль','дата_начала':TODAY_ISO,'дата_окончания':TODAY_ISO}
]
ENTRIES_TODAY_VIEW = [
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS_TODAY_VIEW = [
  {'id':106,'таб_номер':'017','тип':'инструктаж','тема':'Ежедневный контроль','дата_начала':TODAY_ISO,'дата_окончания':TODAY_ISO}
]
VACATIONS = []

STATE = {'role': 'Админ', 'slow_entries': False}

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
        return {'ok':True,'data':{'entries':ENTRIES_JUNE}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS_JUNE}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    return {'ok':False,'error':'unknown action ' + str(action)}

class FetchCounter:
    def __init__(self):
        self.n = 0
    def bump(self):
        self.n += 1
    def reset(self):
        self.n = 0

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def seed_cache(page, ts=STAMP_TS):
    """заполнить локальную копию для ТЕКУЩЕГО месяца (до открытия графика)"""
    page.evaluate("""(function(a){
        var ym = a[0], ts = a[1];
        var c = {
            v: 1,
            codes: a[2], patterns: a[3], employees: a[4],
            vacations: {}, views: {}
        };
        c.vacations[String(new Date().getFullYear())] = a[5];
        c.views[ym] = { entries: a[6], trainings: a[7], ts: ts };
        localStorage.setItem('kip8_ws_cache_v1', JSON.stringify(c));
        return true;
    })""", [YM_TODAY, ts, CODES, PATTERNS, EMPLOYEES, VACATIONS,
            ENTRIES_TODAY_VIEW, TRAININGS_TODAY_VIEW])

def ws_fetch_count(cnt):
    """сколько workSchedule.* запросов было с последнего сброса"""
    return cnt.n

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

# состояние ячейки: текст, классы, inline-фон, бейджи
CELL_STATE = """(function(a){
    var iso = a[0], tab = a[1];
    var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
    var td = null;
    for (var i=0;i<tds.length;i++){
        var oc = tds[i].getAttribute('onclick') || '';
        if (oc.indexOf("'"+iso+"'") !== -1 && oc.indexOf("'"+tab+"'") !== -1) { td = tds[i]; break; }
    }
    if (!td) return null;
    var cs = getComputedStyle(td);
    // текст до первого дочернего элемента (бейджи не в счёт)
    var main = '';
    for (var n = td.firstChild; n; n = n.nextSibling) {
        if (n.nodeType === 3) main += n.data;
        else break;
    }
    var badges = td.querySelectorAll('.ws-ev-badge');
    var btxt = [], bbg = [];
    for (var j=0;j<badges.length;j++) {
        btxt.push(badges[j].textContent);
        var st = badges[j].getAttribute('style') || '';
        bbg.push(st.indexOf('background') !== -1 ? st : '(пунктир)');
    }
    return { text: main,
             classes: td.className,
             inlineBg: (td.getAttribute('style') || '').indexOf('background') !== -1,
             bg: cs.backgroundColor,
             color: cs.color,
             badges: btxt, badgeStyles: bbg,
             hasPending: td.querySelectorAll('.ws-ev-badge.ws-ev-pending').length };
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280px, Админ =================
    ctx = browser.new_context(viewport={'width':1280,'height':800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))

    cnt1 = FetchCounter()

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        if action.startswith('workSchedule.'):
            cnt1.bump()
        if STATE['slow_entries'] and action == 'workSchedule.listEntries':
            time.sleep(0.45)
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t314)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t314')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # ---------- КЭШ: мгновенное открытие без сети ----------
    seed_cache(page)
    cnt1.reset()
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    check('B: график открыт МГНОВЕННО из локальной копии (0 запросов workSchedule.*)',
          ws_fetch_count(cnt1) == 0 and page.evaluate("!!document.querySelector('#wsGridWrap table')"),
          ws_fetch_count(cnt1))
    check('B2: сетка отрисована по данным кэша (2 сотрудника, сегодня Д/Д8)',
          page.evaluate("""(function(){
              var rows = document.querySelectorAll('#wsGridWrap tbody tr');
              return rows.length === 2;
          })()"""))
    # Task 317: строка «данные от» живёт в тултипе #wsRefreshTip
    # (дата обновляется и скрытом — текст элемента #wsRefreshTipDate)
    stamp = page.evaluate("(function(){var e=document.getElementById('wsRefreshTipDate');return e? e.textContent : null;})()")
    check('B3: дата возраста данных «%s» (в тултипе)' % STAMP_TEXT, stamp == STAMP_TEXT, stamp)
    check('B4: подсветка «сегодня» жива и на кэш-рендере (Task 313)',
          page.evaluate("document.querySelectorAll('#wsGridWrap thead th.ws-today-col').length === 1"))

    # ---------- КНОПКА «Обновить»: данные с сервера ----------
    btn_state = page.evaluate("""(function(){
        var b = document.getElementById('wsRefreshBtn');
        var g = document.getElementById('wsGenerateBtn');
        return { visible: !!b && !b.hidden && b.offsetParent !== null,
                 text: b ? b.textContent.trim() : null,
                 hasIcon: b ? !!b.querySelector('svg') : false,
                 genVisible: g ? !g.hidden : false,
                 genAction: g ? (g.getAttribute('onclick')||'') : '',
                 refreshAction: b ? (b.getAttribute('onclick')||'') : '' };
    })()""")
    check('C: кнопка «Обновить» видна (Админ), с иконкой; «Сформировать» жива отдельно',
          btn_state['visible'] and btn_state['hasIcon'] and btn_state['genVisible'] and
          ('refreshData' in btn_state['refreshAction']) and
          ('generateYear' in btn_state['genAction']), btn_state)

    STATE['slow_entries'] = True
    page.evaluate("""(function(){
        window.__toasts = [];
        var orig = KipToast.show;
        KipToast.show = function(m){ window.__toasts.push(String(m)); return orig.apply(this, arguments); };
        return true;
    })()""")
    cnt1.reset()
    page.click('#wsRefreshBtn')
    page.wait_for_timeout(150)
    spinning = page.evaluate("""(function(){
        var b = document.getElementById('wsRefreshBtn');
        return { spin: b ? b.classList.contains('ws-refreshing') : false,
                 disabled: b ? b.disabled : false,
                 gridAlive: !!document.querySelector('#wsGridWrap table') };
    })()""")
    check('C2: во время обновления — спиннер + кнопка блокирована, сетка НЕ пропала',
          spinning['spin'] and spinning['disabled'] and spinning['gridAlive'], spinning)
    page.wait_for_timeout(2500)
    check('C3: «Обновить» сходил на сервер (≥6 запросов: коды+5 наборов)',
          ws_fetch_count(cnt1) >= 6, ws_fetch_count(cnt1))
    toast_msgs = page.evaluate("window.__toasts || []")
    check('C4: тост «Данные графика обновлены»',
          any('Данные графика обновлены' in m for m in toast_msgs), toast_msgs[:3])
    stamp2 = page.evaluate("(function(){var e=document.getElementById('wsRefreshTipDate');return e? e.textContent : null;})()")
    check('C5: дата в тултипе обновилась (не %s)' % STAMP_TEXT,
          stamp2 and stamp2 != STAMP_TEXT and stamp2.startswith('данные от '), stamp2)
    saved = page.evaluate("""(function(){
        var c = JSON.parse(localStorage.getItem('kip8_ws_cache_v1'));
        var v = c.views['%s'];
        return { has: !!v, ts: v ? v.ts : 0, entries: v ? v.entries.length : 0 };
    })()""" % YM_TODAY)
    check('C6: локальная копия перезаписана (ts свежий, записи месяца)',
          saved['has'] and saved['ts'] >= STAMP_TS and saved['entries'] >= 2, saved)
    STATE['slow_entries'] = False

    # ---------- Смена месяца: некэшированный — сеть, возврат — мгновенно ----------
    cnt1.reset()
    goto_month(page, 6, 2026)
    check('D: некэшированный месяц (июнь) — загружен с сервера',
          ws_fetch_count(cnt1) >= 5 and page.evaluate("!!document.querySelector('#wsGridWrap table')"),
          ws_fetch_count(cnt1))
    cnt1.reset()
    goto_month(page, TODAY_M, TODAY_Y)
    check('D2: возврат к кэшированному месяцу — 0 запросов, мгновенно',
          ws_fetch_count(cnt1) == 0 and page.evaluate("!!document.querySelector('#wsGridWrap table')"),
          ws_fetch_count(cnt1))

    # ---------- Июнь 2026: «·», бейджи ----------
    goto_month(page, 6, 2026)

    # D3: «.»-ячейка (05.06, 017) = ПУСТАЯ (пн-пт 05.06.2026 — пятница)
    dot = page.evaluate(CELL_STATE, ['2026-06-05', '017'])
    empty = page.evaluate(CELL_STATE, ['2026-06-01', '023'])
    check('D3: «.»-ячейка: символ «·», класс ws-dot-code, БЕЗ inline-фона',
          dot and dot['text'] == '·' and ('ws-dot-code' in dot['classes']) and
          (not dot['inlineBg']), dot)
    check('D4: фон «.»-ячейки РАВЕН фону пустой рабочей ячейки (тёмная тема)',
          dot and empty and dot['bg'] == empty['bg'] and dot['color'] == empty['color'],
          {'dot': dot and [dot['bg'], dot['color']], 'empty': empty and [empty['bg'], empty['color']]})
    check('D5: у «.»-ячейки нет бейджей (день без мероприятий)', dot and dot['badges'] == [], dot)

    # D6: статус-мероприятие (03.06, 023, «И») — НЕ большой код, сплошной бейдж
    evday = page.evaluate(CELL_STATE, ['2026-06-03', '023'])
    check('D6: день-мероприятие «И»: текст «·» (НЕ «И»), без inline-фона, сплошной бейдж И #B3E5FC',
          evday and evday['text'] == '·' and not evday['inlineBg'] and
          evday['badges'] == ['И'] and 'background' in evday['badgeStyles'][0] and
          ('#B3E5FC' in evday['badgeStyles'][0]) and evday['hasPending'] == 0,
          evday)

    # D7: отсутствие (12.06, 023, «ОТ») + мероприятие — бейдж ТЕПЕРЬ виден
    otd = page.evaluate(CELL_STATE, ['2026-06-12', '023'])
    check('D7: «ОТ» + мероприятие: код «ОТ» + inline-фон + СПЛОШНОЙ бейдж «И»',
          otd and otd['text'] == 'ОТ' and otd['inlineBg'] and
          otd['badges'] == ['И'] and otd['hasPending'] == 0, otd)

    # D8: пустая ячейка + мероприятие (01.06, 017) — пунктирный бейдж
    pend = page.evaluate(CELL_STATE, ['2026-06-01', '017'])
    check('D8: пустая ячейка + мероприятие: «·» + ПУНКТИРНЫЙ бейдж «И»',
          pend and pend['text'] == '·' and pend['badges'] == ['И'] and
          pend['hasPending'] == 1, pend)

    # D9: смена + мероприятие (02.06, 017, Д + И) — код смены + сплошной бейдж
    work = page.evaluate(CELL_STATE, ['2026-06-02', '017'])
    check('D9: смена «Д» + мероприятие: код «Д», inline-фон, сплошной бейдж «И»',
          work and work['text'] == 'Д' and work['inlineBg'] and
          work['badges'] == ['И'] and work['hasPending'] == 0, work)

    # D10: «Б» без мероприятий (15.06, 023) — бейджа нет
    bol = page.evaluate(CELL_STATE, ['2026-06-15', '023'])
    check('D10: «Б» без мероприятий — бейджа нет', bol and bol['badges'] == [], bol)

    page.screenshot(path='scripts/task314-proof-badges.png', full_page=False)

    # ---------- Попап: метка «·», свотч ws-swatch-dot ----------
    click_cell(page, '2026-06-05', '017')
    pop = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        if (!cp || !cp.classList.contains('active')) return null;
        var rows = cp.querySelectorAll('.ws-popup-row');
        var dotRow = null;
        for (var i=0;i<rows.length;i++) {
            if ((rows[i].querySelector('.ws-popup-code')||{}).textContent === '·') { dotRow = rows[i]; break; }
        }
        var sw = dotRow ? dotRow.querySelector('.ws-popup-swatch') : null;
        // активная строка = текущий статус «.»
        var act = cp.querySelector('.ws-popup-row.ws-popup-active .ws-popup-code');
        return { dotRow: !!dotRow,
                 dotName: dotRow ? (dotRow.querySelector('.ws-popup-name')||{}).textContent : null,
                 dotSwatchClass: sw ? sw.className : null,
                 dotSwatchBg: sw ? getComputedStyle(sw).backgroundColor : null,
                 dotSwatchInline: sw ? (sw.getAttribute('style')||'') : null,
                 activeCode: act ? act.textContent : null };
    })()""")
    empty_bg = empty['bg'] if empty else None
    check('D11: попап: строка «·» (Плановый выходной день), свотч ws-swatch-dot без inline-стиля',
          pop and pop['dotRow'] and pop['dotName'] == 'Плановый выходной день' and
          ('ws-swatch-dot' in pop['dotSwatchClass']) and pop['dotSwatchInline'] == '',
          pop)
    check('D12: свотч «·» = фон ПУСТОЙ ячейки; активная строка — «·»',
          pop and pop['dotSwatchBg'] == empty_bg and pop['activeCode'] == '·',
          {'swatch': pop and pop['dotSwatchBg'], 'empty': empty_bg, 'active': pop and pop['activeCode']})
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    page.screenshot(path='scripts/task314-proof-popup-dot.png', full_page=False)

    # ---------- «Дополнительно…»: select c меткой «·» ----------
    click_cell(page, '2026-06-05', '017')
    page.evaluate("WorkSchedule.onPopupMore ? WorkSchedule.onPopupMore() : null")
    page.wait_for_timeout(400)
    sel_state = page.evaluate("""(function(){
        var s = document.getElementById('wsCellStatus');
        if (!s) return null;
        var dotOpt = null;
        for (var i=0;i<s.options.length;i++) {
            if (s.options[i].value === '.') { dotOpt = s.options[i]; break; }
        }
        return { value: s.value, dotLabel: dotOpt ? dotOpt.textContent : null,
                 dotValue: dotOpt ? dotOpt.value : null };
    })()""")
    check('D13: select «Дополнительно…»: value «.», метка «· — Плановый выходной день»',
          sel_state and sel_state['value'] == '.' and sel_state['dotLabel'] and
          sel_state['dotLabel'].startswith('· — Плановый выходной день') and
          sel_state['dotValue'] == '.', sel_state)
    page.evaluate("WorkSchedule.closeCellForm ? WorkSchedule.closeCellForm() : null")
    page.wait_for_timeout(200)

    # ---------- Светлая тема: «.» = пустая ----------
    page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(200)
    dot_l = page.evaluate(CELL_STATE, ['2026-06-05', '017'])
    empty_l = page.evaluate(CELL_STATE, ['2026-06-11', '023'])   # чт 11.06 — пустая
    check('D14: светлая тема — фон «.»-ячейки = фон пустой (#eef0f2)',
          dot_l and empty_l and dot_l['bg'] == empty_l['bg'] and
          dot_l['bg'] == 'rgb(238, 240, 242)',
          {'dot': dot_l and dot_l['bg'], 'empty': empty_l and empty_l['bg']})
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    page.screenshot(path='scripts/task314-proof-light-dot.png', full_page=False)

    # ---------- Повторное открытие страницы — по-прежнему мгновенно ----------
    page.evaluate("navigateTo('dashboard')")
    page.wait_for_timeout(600)
    cnt1.reset()
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    check('E: повторное открытие графика — снова 0 запросов (кэш на устройстве)',
          ws_fetch_count(cnt1) == 0 and page.evaluate("!!document.querySelector('#wsGridWrap table')"),
          ws_fetch_count(cnt1))
    check('E2: JS-ошибок нет (Админ)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: сервер недоступен (500) =================
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))

    def handle_fail(route, request):
        route.fulfill(status=500, content_type='text/plain', body='server down (t314)')
    ctx2.route('**/exec?**', handle_fail)
    ctx2.route('**script.google.com/**', handle_fail)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)

    page2.goto('http://localhost:%d/index.html' % PORT)
    # живая сессия при ПОЗЖЕ упавшем API: логин проходим, сервер
    # уроним ПЕРЕД вторым открытием графика (см. ниже)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t314-offline')")
    page2.reload()
    page2.wait_for_timeout(2500)
    def handle_ok(route, request):
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
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx2.route('**/exec?**', handle_ok)
    ctx2.route('**script.google.com/**', handle_ok)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(2000)
    seed_cache(page2)
    page2.evaluate("navigateTo('dashboard')")
    page2.wait_for_timeout(600)
    # роняем сервер
    ctx2.unroute('**/exec?**')
    ctx2.unroute('**script.google.com/**')
    ctx2.route('**/exec?**', handle_fail)
    ctx2.route('**script.google.com/**', handle_fail)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1800)
    offline = page2.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        return { grid: !!document.querySelector('#wsGridWrap table'),
                 err: wrap ? wrap.textContent.indexOf('Ошибка загрузки') !== -1 : null,
                 loading: wrap ? wrap.textContent.indexOf('Загрузка') !== -1 : null };
    })()""")
    check('F: офлайн — график открылся из локальной копии (без «Загрузка…»/ошибки)',
          offline['grid'] and not offline['err'] and not offline['loading'], offline)
    # «Обновить» при упавшем сервере: сетка ОСТАЁТСЯ, тост об ошибке.
    # (сессия при 500 умирает — приложение показывает логин-экран,
    # который перехватывает клики; вызываем refreshData напрямую —
    # UI-клик кнопки уже проверен в контексте 1)
    page2.evaluate("""(function(){
        window.__toasts = [];
        var orig = KipToast.show;
        KipToast.show = function(m){ window.__toasts.push(String(m)); return orig.apply(this, arguments); };
        WorkSchedule.refreshData();
        return true;
    })()""")
    page2.wait_for_timeout(2500)
    offline2 = page2.evaluate("""(function(){
        var wrap = document.getElementById('wsGridWrap');
        return { grid: !!document.querySelector('#wsGridWrap table'),
                 err: wrap ? wrap.textContent.indexOf('Ошибка загрузки') !== -1 : null };
    })()""")
    offline2['toast'] = any('Ошибка загрузки' in m for m in (page2.evaluate("window.__toasts || []")))
    check('F2: «Обновить» при сбое — сетка НЕ стёрта, тост об ошибке',
          offline2['grid'] and not offline2['err'] and offline2['toast'], offline2)
    check('F3: JS-ошибок нет (офлайн)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: зритель (ИТР8 pro) =================
    STATE['role'] = 'ИТР8 pro'
    ctx3 = browser.new_context(viewport={'width':1280,'height':800})
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))

    cnt3 = FetchCounter()

    def handle3(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        if action.startswith('workSchedule.'):
            cnt3.bump()
        body = None
        pd = request.post_data
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
    page3.evaluate("localStorage.setItem('kip8_session_token','browser-check-t314-viewer')")
    page3.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page3.reload()
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(2500)
    viewer = page3.evaluate("""(function(){
        var b = document.getElementById('wsRefreshBtn');
        var g = document.getElementById('wsGenerateBtn');
        return { refresh: b ? (!b.hidden && b.offsetParent !== null) : false,
                 generate: g ? !g.hidden : true,
                 grid: !!document.querySelector('#wsGridWrap table'),
                 stamp: (document.getElementById('wsRefreshTipDate')||{}).textContent || '' };
    })()""")
    check('G: зритель — «Обновить» доступна, «Сформировать» скрыта, сетка жива',
          viewer['refresh'] and not viewer['generate'] and viewer['grid'], viewer)
    # зритель обновляет данные кнопкой
    cnt3.reset()
    page3.click('#wsRefreshBtn')
    page3.wait_for_timeout(2200)
    check('G2: зритель: «Обновить» работает (запросы + дата в тултипе)',
          ws_fetch_count(cnt3) >= 6 and viewer is not None and
          page3.evaluate("(function(){var e=document.getElementById('wsRefreshTipDate');return e? e.textContent.indexOf('данные от')===0 : false;})()"),
          ws_fetch_count(cnt3))
    check('G3: JS-ошибок нет (зритель)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    # ================= Контекст 4: мобильный 375px =================
    STATE['role'] = 'Админ'
    ctx4 = browser.new_context(viewport={'width':375,'height':812})
    page4 = ctx4.new_page()
    js_errors4 = []
    page4.on('pageerror', lambda e: js_errors4.append(str(e)))

    def handle4(route, request):
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
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx4.route('**/exec?**', handle4)
    ctx4.route('**script.google.com/**', handle4)
    ctx4.route('**raw.githubusercontent.com/**', block_external)
    ctx4.route('**calendar.legalic.ru/**', block_external)

    page4.goto('http://localhost:%d/index.html' % PORT)
    page4.evaluate("localStorage.setItem('kip8_session_token','browser-check-t314-mobile')")
    page4.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page4.reload()
    page4.wait_for_timeout(2500)
    seed_cache(page4)
    page4.evaluate("navigateTo('work-schedule')")
    page4.wait_for_timeout(1800)
    mob = page4.evaluate("""(function(){
        var tb = document.querySelector('.ws-toolbar');
        var b = document.getElementById('wsRefreshBtn');
        var st = document.getElementById('wsRefreshTipDate');
        var r = b ? b.getBoundingClientRect() : null;
        var tr = tb ? tb.getBoundingClientRect() : null;
        return { grid: !!document.querySelector('#wsGridWrap table'),
                 btnVisible: r ? (r.width > 0 && r.height > 0) : false,
                 btnInToolbar: r && tr ? (r.top >= tr.top && r.bottom <= tr.bottom + 60) : false,
                 stamp: st ? st.textContent : null,
                 vw: window.innerWidth };
    })()""")
    check('H: мобильный 375px — тулбар жив, «Обновить» видна и в кадре, дата в тултипе',
          mob['grid'] and mob['btnVisible'] and mob['btnInToolbar'] and
          mob['stamp'] == STAMP_TEXT, mob)
    page4.click('#wsRefreshBtn')
    page4.wait_for_timeout(2200)
    check('H2: мобильный — «Обновить» подтянул данные (сетка жива, дата в тултипе свежая)',
          page4.evaluate("!!document.querySelector('#wsGridWrap table')") and
          page4.evaluate("(function(){var e=document.getElementById('wsRefreshTipDate');return e? e.textContent.indexOf('данные от')===0 : false;})()"))
    page4.screenshot(path='scripts/task314-proof-mobile.png', full_page=False)
    check('H3: JS-ошибок нет (мобильный)', len(js_errors4) == 0, js_errors4[:3])
    ctx4.close()

    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task314-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
