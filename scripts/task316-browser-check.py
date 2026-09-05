# -*- coding: utf-8 -*-
# Task 316: browser-check «График работы» — наведение/КЛИК на дату
# в шапке шахматки выделяет ВЕСЬ столбец (шапка + ячейки, вид как у
# «сегодня» Task 313):
#   • мышь над датой — столбец подсвечен (снимается уходом курсора);
#   • клик по дате — день ВЫБРАН (держится до клика по другой
#     области / повторного клика / смены месяца), окно мероприятий
#     месяца фильтруется по дню (записи, НАКРЫВАЮЩИЕ дату);
#   • дата кликабельна (курсор-палец).
# Проверки: th[data-day] на всех днях + cursor:pointer; hover:
# ws-hover-col на th и ws-hover на ВСЕХ td столбца, снятие при уходе;
# клик: ws-sel-col/ws-sel (насыщеннее hover), окно «10.MM · 2»
# (только накрывающие записи, диапазоны живы), пустой день
# («нет мероприятий в этот день»), повторный клик — сброс, клик по
# другой области (окно времени) — сброс, переживание _renderGrid,
# смена месяца — сброс; светлая тема; зритель и мобильный 375px —
# выбор и фильтр работают. 0 JS-ошибок.
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
FIRST_DAY = TODAY.replace(day=1)
LAST_PREV = FIRST_DAY - datetime.timedelta(days=1)
CROSS_START = LAST_PREV - datetime.timedelta(days=1)

def D(day):
    return '%04d-%02d-%02d' % (Y, M, day)

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
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':7,'дата':TODAY_ISO,'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':8,'дата':TODAY_ISO,'таб_номер':'023','статус':'Д8','источник':'авто'}
]
# Мероприятия: ДВА в день 10 (фильтр по дню), диапазон 12–15,
# день 20, пересечение границы (накрывает только 1-е число),
# следующий месяц (не показан). День 17 — ПУСТОЙ.
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'Целевой инструктаж','дата_начала':D(10),'дата_окончания':D(10),'длительность_дней':1},
  {'id':106,'таб_номер':'023','тип':'инструктаж','тема':'Пожарная безопасность','дата_начала':D(10),'дата_окончания':D(10),'длительность_дней':1},
  {'id':102,'таб_номер':'023','тип':'обучение','тема':'Охрана труда','дата_начала':D(12),'дата_окончания':D(15),'длительность_дней':4},
  {'id':103,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж','дата_начала':D(20),'дата_окончания':D(20),'длительность_дней':1},
  {'id':104,'таб_номер':'023','тип':'инструктаж','тема':'На стыке месяцев','дата_начала':CROSS_START.isoformat(),'дата_окончания':FIRST_DAY.isoformat(),'длительность_дней':3},
  {'id':105,'таб_номер':'017','тип':'обучение','тема':'Следующий месяц — НЕ показано','дата_начала':'%04d-%02d-05' % (Y + (1 if M == 12 else 0), (M % 12) + 1),'дата_окончания':'%04d-%02d-05' % (Y + (1 if M == 12 else 0), (M % 12) + 1),'длительность_дней':1}
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

# Состояние столбца дня d: классы th + всех td
COL_JS = """(function(d){
    var th = document.querySelector('#wsGridWrap thead th[data-day="' + d + '"]');
    var tds = Array.prototype.slice.call(
        document.querySelectorAll('#wsGridWrap tbody td[data-day="' + d + '"]'));
    return { thHover: th ? th.classList.contains('ws-hover-col') : null,
             thSel: th ? th.classList.contains('ws-sel-col') : null,
             thToday: th ? th.classList.contains('ws-today-col') : false,
             thCursor: th ? getComputedStyle(th).cursor : '',
             thBg: th ? getComputedStyle(th).backgroundImage : '',
             tdN: tds.length,
             tdHover: tds.filter(function(t){ return t.classList.contains('ws-hover'); }).length,
             tdSel: tds.filter(function(t){ return t.classList.contains('ws-sel'); }).length,
             empN: document.querySelectorAll('#wsGridWrap tbody tr').length,
             anySelCol: document.querySelectorAll('#wsGridWrap .ws-sel-col, #wsGridWrap .ws-sel').length };
})"""

def col_state(page, d):
    return page.evaluate(COL_JS, d)

def ev_state(page):
    return page.evaluate("""(function(){
        var el = document.getElementById('wsEventsPanel');
        if (!el || el.hidden) return null;
        var cap = el.querySelector('.ws-ep-cap');
        var empty = el.querySelector('.ws-cp-empty');
        var items = el.querySelectorAll('.ws-ep-item');
        var rows = [];
        for (var i=0;i<items.length;i++){
            rows.push({
                date: (items[i].querySelector('.ws-ep-date')||{}).textContent || '',
                text: (items[i].querySelector('.ws-ep-text')||{}).textContent || ''
            });
        }
        return { cap: cap ? cap.textContent.trim() : '',
                 empty: empty ? empty.textContent.trim() : '',
                 n: items.length, rows: rows };
    })()""")

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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t316)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t316')")
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт, сетка отрисована', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # ---------- th[data-day] + курсор-палец ----------
    th10 = col_state(page, 10)
    check('C: th[data-day=10] есть, дата КЛИКАБЕЛЬНА (cursor: pointer)',
          th10 and th10['thCursor'] == 'pointer', th10 and th10['thCursor'])
    check('C2: td[data-day=10] — на ВСЕХ строках (2 сотрудника)',
          th10 and th10['tdN'] == th10['empN'] == 2, th10 and (th10['tdN'], th10['empN']))

    ev0 = ev_state(page)
    mm = '%02d' % M
    check('C3: до выбора — окно мероприятий всего месяца (5 записей)',
          ev0 and ev0['n'] == 5 and ('· 5' in ev0['cap']), ev0 and (ev0 and ev0['n'], ev0 and ev0['cap']))

    # ---------- НАВЕДЕНИЕ ----------
    page.hover('#wsGridWrap thead th[data-day="10"]')
    page.wait_for_timeout(250)
    hov = col_state(page, 10)
    check('D: наведение — ws-hover-col на th, ws-hover на ВСЕХ td столбца',
          hov['thHover'] and hov['tdHover'] == 2 and not hov['thSel'], hov)
    # уход курсора — подсветка снята
    page.hover('#wsCalPanel')
    page.wait_for_timeout(250)
    hov2 = col_state(page, 10)
    check('D2: уход курсора — подсветка столбца СНЯТА',
          not hov2['thHover'] and hov2['tdHover'] == 0, hov2)
    check('D3: hover не оставляет выбора (ws-sel нет)', hov2['tdSel'] == 0 and not hov2['thSel'], hov2)

    # ---------- КЛИК: выбор дня ----------
    page.click('#wsGridWrap thead th[data-day="10"]')
    page.wait_for_timeout(400)
    # курсор УВОДИМ с даты: клик оставляет мышь над th — hover-состояние
    # (мышь над датой) законно остаётся; проверяем ЧИСТЫЙ выбранный вид
    page.mouse.move(640, 60)
    page.wait_for_timeout(250)
    sel = col_state(page, 10)
    check('E: клик — ws-sel-col на th, ws-sel на ВСЕХ td, градиент жив',
          sel['thSel'] and sel['tdSel'] == 2 and not sel['thHover'] and sel['tdHover'] == 0 and
          sel['thBg'] != 'none' and ('74, 143, 199' in sel['thBg'] or '42, 93, 143' in sel['thBg']),
          sel)
    ev1 = ev_state(page)
    check('E2: окно отфильтровано по дню: «Мероприятия · 10.%s · 2»' % mm,
          ev1 and ev1['cap'] == 'Мероприятия · 10.%s · 2' % mm, ev1 and ev1['cap'])
    check('E3: показаны ТОЛЬКО накрывающие день записи',
          ev1 and ev1['n'] == 2 and
          any('Целевой инструктаж' in r['text'] for r in ev1['rows']) and
          any('Пожарная безопасность' in r['text'] for r in ev1['rows']),
          ev1 and [r['text'][:30] for r in ev1['rows']])
    check('E4: прочие записи месяца скрыты',
          ev1 and not any(('Охрана труда' in r['text'] or 'Повторный' in r['text'] or 'стыке' in r['text']) for r in ev1['rows']),
          ev1 and [r['text'][:30] for r in ev1['rows']])
    page.screenshot(path='scripts/task316-proof-selected.png', full_page=False)

    # ---------- выбор ПЕРЕЖИВАЕТ перерисовку сетки ----------
    page.evaluate("WorkSchedule._renderGrid()")
    page.wait_for_timeout(400)
    sel2 = col_state(page, 10)
    ev2 = ev_state(page)
    check('F: выбор ПЕРЕЖИВАЕТ _renderGrid (классы из состояния)',
          sel2['thSel'] and sel2['tdSel'] == 2 and ev2 and ev2['n'] == 2, (sel2, ev2 and ev2['cap']))

    # ---------- ПУСТОЙ день ----------
    page.click('#wsGridWrap thead th[data-day="17"]')
    page.wait_for_timeout(400)
    sel17 = col_state(page, 17)
    sel10 = col_state(page, 10)
    ev17 = ev_state(page)
    check('G: пустой день 17 — выбор ПЕРЕКЛЮЧИЛСЯ (10 погашен)',
          sel17['thSel'] and sel17['tdSel'] == 2 and not sel10['thSel'] and sel10['tdSel'] == 0,
          (sel17, sel10))
    check('G2: окно — «нет мероприятий в этот день», заголовок с днём',
          ev17 and ev17['n'] == 0 and ev17['empty'] == 'нет мероприятий в этот день' and
          ev17['cap'] == 'Мероприятия · 17.%s' % mm, ev17 and (ev17['cap'], ev17['empty']))

    # ---------- повторный клик — сброс ----------
    page.click('#wsGridWrap thead th[data-day="17"]')
    page.wait_for_timeout(400)
    sel17b = col_state(page, 17)
    ev17b = ev_state(page)
    check('H: повторный клик по дате — выбор СНЯТ (окно: весь месяц)',
          not sel17b['thSel'] and sel17b['tdSel'] == 0 and ev17b and ev17b['n'] == 5,
          (sel17b, ev17b and ev17b['cap']))

    # ---------- клик по ДРУГОЙ области — сброс ----------
    page.click('#wsGridWrap thead th[data-day="12"]')
    page.wait_for_timeout(400)
    ev12 = ev_state(page)
    check('I: клик по дате 12 — диапазон 12–15 накрывает день (1 запись)',
          ev12 and ev12['cap'] == 'Мероприятия · 12.%s · 1' % mm and
          any('Охрана труда' in r['text'] for r in ev12['rows']),
          ev12 and ev12['cap'])
    page.click('#wsCalPanel')
    page.wait_for_timeout(400)
    sel12b = col_state(page, 12)
    ev12b = ev_state(page)
    check('I2: клик по ДРУГОЙ области (окно времени) — выбор снят',
          not sel12b['thSel'] and sel12b['tdSel'] == 0 and ev12b and ev12b['n'] == 5,
          (sel12b, ev12b and ev12b['cap']))

    # ---------- светлая тема ----------
    page.click('#wsGridWrap thead th[data-day="10"]')
    page.wait_for_timeout(300)
    page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(400)
    light = col_state(page, 10)
    check('J: светлая тема — выбранный столбец подсвечен (тон 42,93,143)',
          light['thSel'] and '42, 93, 143' in light['thBg'], light['thBg'])
    page.screenshot(path='scripts/task316-proof-light.png', full_page=False)
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    page.wait_for_timeout(300)

    # ---------- смена месяца — сброс ----------
    page.click('#wsGridWrap thead th[data-day="10"]')
    page.wait_for_timeout(300)
    # курсор убираем с сетки ДО смены месяца: перерисовка под курсором
    # заново стреляет mouseenter (браузер пересчитывает hover-цепь) —
    # это законное повторное наведение, не должно мешать проверке сброса
    page.mouse.move(4, 4)
    page.wait_for_timeout(200)
    empty_m = (M % 12) + 2   # месяц ЧЕРЕЗ один: мероприятий нет точно
    page.select_option('#wsMonthSel', str(empty_m))
    page.wait_for_timeout(3000)
    after = page.evaluate("""(function(){
        return { anySel: document.querySelectorAll('#wsGridWrap .ws-sel-col, #wsGridWrap .ws-sel').length,
                 selDay: WorkSchedule._selDay, hoverDay: WorkSchedule._hoverDay };
    })()""")
    ev_next = ev_state(page)
    check('K: смена месяца — выбор дня СБРОШЕН (классов нет, _selDay null)',
          after['anySel'] == 0 and after['selDay'] is None, after)
    check('K2: окно мероприятий — полный вид ПУСТОГО месяца',
          ev_next and ev_next['n'] == 0 and 'нет мероприятий в этом месяце' in ev_next['empty'],
          ev_next and (ev_next['cap'], ev_next['empty']))
    # возврат в текущий месяц — окно снова с 5 записями
    page.select_option('#wsMonthSel', str(M))
    page.wait_for_timeout(3000)
    ev_back = ev_state(page)
    check('K3: возврат в месяц — окно месяца (5 записей), выбора нет',
          ev_back and ev_back['n'] == 5 and
          page.evaluate("document.querySelectorAll('#wsGridWrap .ws-sel-col, #wsGridWrap .ws-sel').length") == 0,
          ev_back and ev_back['cap'])
    check('K4: JS-ошибок нет (десктоп)', len(js_errors) == 0, js_errors[:3])
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
        resp = mock_response(action, None)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx2.route('**/exec?**', handle2)
    ctx2.route('**script.google.com/**', handle2)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t316-viewer')")
    page2.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    v0 = ev_state(page2)
    page2.hover('#wsGridWrap thead th[data-day="10"]')
    page2.wait_for_timeout(250)
    vh = col_state(page2, 10)
    page2.hover('#wsCalPanel')
    page2.wait_for_timeout(250)
    vh2 = col_state(page2, 10)
    check('L: зритель — наведение/уход работает (hover без выбора)',
          vh['thHover'] and vh2['tdHover'] == 0 and not vh2['thSel'], (vh, vh2))
    page2.click('#wsGridWrap thead th[data-day="10"]')
    page2.wait_for_timeout(400)
    vs = col_state(page2, 10)
    vv = ev_state(page2)
    check('L2: зритель — клик по дате: столбец выбран, окно отфильтровано (2)',
          vs['thSel'] and vs['tdSel'] == 2 and vv and vv['n'] == 2 and
          vv['cap'] == 'Мероприятия · 10.%s · 2' % mm, (vs, vv and vv['cap']))
    check('L3: JS-ошибок нет (зритель)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобильный 375px =================
    STATE['role'] = 'Админ'
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
        resp = mock_response(action, None)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx3.route('**/exec?**', handle3)
    ctx3.route('**script.google.com/**', handle3)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)

    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.evaluate("localStorage.setItem('kip8_session_token','browser-check-t316-mobile')")
    page3.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page3.reload()
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.click('#wsGridWrap thead th[data-day="10"]')
    page3.wait_for_timeout(500)
    ms = col_state(page3, 10)
    mv = ev_state(page3)
    check('M: мобильный — клик по дате: столбец выбран, окно отфильтровано',
          ms['thSel'] and ms['tdSel'] == 2 and mv and mv['n'] == 2 and
          mv['cap'] == 'Мероприятия · 10.%s · 2' % mm, (ms, mv and mv['cap']))
    page3.screenshot(path='scripts/task316-proof-mobile.png', full_page=False)
    check('M2: JS-ошибок нет (мобильный)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

fails = [r for r in results if not r[1]]
print('')
print('=' * 60)
print('ИТОГ: %d passed, %d failed, %d total' % (len(results) - len(fails), len(fails), len(results)))
if fails:
    print('ОШИБКИ:')
    for name, _, extra in fails:
        print('  FAIL: ' + name + ' | ' + str(extra))
    sys.exit(1)
