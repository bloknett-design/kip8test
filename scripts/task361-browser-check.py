#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 361: browser-check — заявка пользователя (печатная форма
# графика работы): «в печати столбец с сотрудниками сделай уже,
# по ширине текста в нём, а в общем размер таблицы увеличь
# насколько это возможно, и размер шрифта всех строк над и под
# таблицей сделай больше (для более удобного чтения, потому что
# сейчас текст на печати очень маленький, и его неудобно читать).
# И сделай отображение на печати значков мероприятий в ячейках
# шахматки».
# Контексты:
#   1. десктоп 1280 тёмная, Админ (edit): печать с мероприятиями —
#      бейджи в ячейках: сплошной с цветом у сформированного дня
#      (07: Д + инструктаж), ВИРТУАЛЬНЫЙ у статус-мероприятия без
#      записи в «Инструктажах» (08: И), пунктирный план у пустой
#      ячейки (02: обучение 023); ширина колонки «Сотрудник» —
#      inline по тексту (не 50mm); дни шире (делят остаток);
#      шрифты над/под таблицей и в таблице крупнее; print-медиа:
#      computed-стили (title 18px, mev 11px, cell 10px, высота
#      7.2mm, точка 2.2mm);
#   2. мобайл 375 touch — печать строится, бейджи/ширины живы.
# + 0 JS-ошибок; скриншот-пруф печатного листа.
# Стаб window.print — function-evaluate (урок Task 341).
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8960
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

MONTHS_NOM = ['январь','февраль','март','апрель','май','июнь',
              'июль','август','сентябрь','октябрь','ноябрь','декабрь']
MONTH_NAME = MONTHS_NOM[M - 1]

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-01' % (Y, M if M > 1 else 12),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-07' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# записи месяца: Д/Н/«.»/ОТ + Д на 07 (бейдж И сплошной) +
# статус-мероприятие И на 08 (ВИРТУАЛЬНЫЙ бейдж, записи в
# «Инструктажах» на 08 нет)
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-10' % (Y, M),'таб_номер':'017','статус':'.','источник':'авто'},
  {'id':4,'дата':'%04d-%02d-15' % (Y, M),'таб_номер':'023','статус':'ОТ','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-07' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':6,'дата':'%04d-%02d-08' % (Y, M),'таб_номер':'017','статус':'И','источник':'авто'}
]

def trainings_default():
    prev_y, prev_m = (Y, M - 1) if M > 1 else (Y - 1, 12)
    next_y, next_m = (Y, M + 1) if M < 12 else (Y + 1, 1)
    return [
      {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по охране труда',
       'дата_начала':'%04d-%02d-07' % (Y, M),'дата_окончания':'','дата_проведения':''},
      {'id':2,'таб_номер':'023','тип':'обучение','тема':'Обучение по новому оборудованию',
       'дата_начала':'%04d-%02d-29' % (prev_y, prev_m),'дата_окончания':'%04d-%02d-02' % (Y, M),'дата_проведения':''}
    ]

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
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':trainings_default()}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok':True,'data':{'entries':ENTRIES}}
        return {'ok':True,'data':{'entries':[]}}
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t361)')
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

# стаб window.print — function-evaluate (урок Task 341)
STUB_PRINT = "() => { window.print = function(){ window.__printCalled = (window.__printCalled||0)+1; }; }"

# содержимое печатного листа (разметка/бейджи; геометрия — в
# print-эмуляции, на экране лист display:none и offsetWidth=0)
JS_SHEET = """(function(){
    var s = document.getElementById('wsPrintSheet');
    if (!s) return null;
    var empTh = s.querySelector('.wsp-emp');
    return { printCalled: window.__printCalled || 0,
             empStyle: empTh ? empTh.getAttribute('style') : null,
             solidBadges: s.querySelectorAll('.wsp-ev:not(.wsp-ev-plan)').length,
             planBadges: s.querySelectorAll('.wsp-ev-plan').length,
             wrapPos: s.querySelector('.wsp-ev-wrap') ? 'y' : 'n',
             lgCount: s.querySelectorAll('.wsp-legend .wsp-lg').length,
             html: s.innerHTML };
})"""

# computed-стили в print-медиа (шрифты/размеры — Заявка 361)
JS_PRINT_CSS = """(function(){
    var g = function(sel, prop){
        var el = document.querySelector(sel);
        return el ? getComputedStyle(el)[prop] : null;
    };
    var s = document.getElementById('wsPrintSheet');
    var ev = s.querySelector('.wsp-ev');
    var evPlan = s.querySelector('.wsp-ev-plan');
    var wrap = s.querySelector('.wsp-ev-wrap');
    var cell = s.querySelector('td.wsp-cell');
    var over = s.querySelector('.wsp-over');
    return {
      base: g('#wsPrintSheet', 'fontSize'),
      title: g('#wsPrintSheet .wsp-title', 'fontSize'),
      sub: g('#wsPrintSheet .wsp-sub', 'fontSize'),
      meta: g('#wsPrintSheet .wsp-meta', 'fontSize'),
      printed: g('#wsPrintSheet .wsp-printed', 'fontSize'),
      mev: g('#wsPrintSheet .wsp-mev', 'fontSize'),
      legend: g('#wsPrintSheet .wsp-legend', 'fontSize'),
      foot: g('#wsPrintSheet .wsp-foot', 'fontSize'),
      fio: g('#wsPrintSheet .wsp-fio', 'fontSize'),
      pos: g('#wsPrintSheet .wsp-pos', 'fontSize'),
      cellFont: g('#wsPrintSheet .wsp-cell', 'fontSize'),
      daySpan: g('#wsPrintSheet .wsp-day span', 'fontSize'),
      cellH: cell ? cell.getBoundingClientRect().height : null,
      overW: over ? over.getBoundingClientRect().width : null,
      evFont: ev ? getComputedStyle(ev).fontSize : null,
      evDisplay: ev ? getComputedStyle(ev).display : null,
      evBg: ev ? getComputedStyle(ev).backgroundColor : null,
      planStyle: evPlan ? getComputedStyle(evPlan).borderTopStyle : null,
      wrapPosition: wrap ? getComputedStyle(wrap).position : null,
      wrapBottom: wrap ? getComputedStyle(wrap).bottom : null
    };
})"""

MM = 96.0 / 25.4  # px в 1mm (96dpi)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t361-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    page.evaluate(STUB_PRINT)
    page.click('#wsPrintBtn')
    page.wait_for_timeout(400)
    sheet = page.evaluate(JS_SHEET)
    check('C: лист построен, window.print вызван 1 раз', sheet and sheet['printCalled'] == 1, sheet)

    # --- колонка «Сотрудник» по ширине текста ---
    emp_mm = None
    if sheet and sheet['empStyle']:
        try:
            emp_mm = float(sheet['empStyle'].split('width:')[1].split('mm')[0])
        except Exception:
            emp_mm = None
    check('D: у th «Сотрудник» inline ширина в mm', emp_mm is not None, sheet['empStyle'] if sheet else None)
    check('E: ширина по тексту — УЖЕ 50mm (кламп 24–48)', emp_mm is not None and 24 <= emp_mm < 50, emp_mm)

    # --- бейджи мероприятий в ячейках ---
    # 07: Д + инструктаж → сплошной И; 08: статус И без записи →
    # виртуальный сплошной; 02: обучение 023 в пустой ячейке → план
    check('H: бейджи в ячейках есть (сплошных ≥ 2)', sheet and sheet['solidBadges'] >= 2, sheet)
    check('I: пунктирный бейдж-план на пустой ячейке (02, 023)', sheet and sheet['planBadges'] >= 1, sheet)
    check('J: сплошной бейдж с цветом кода И (#B3E5FC)',
          sheet and 'background:#B3E5FC' in sheet['html'], None)

    # --- эмуляция print-медиа: computed-стили + геометрия ---
    page.emulate_media(media='print')
    css = page.evaluate(JS_PRINT_CSS)
    geom = page.evaluate("""(function(){
        var s = document.getElementById('wsPrintSheet');
        var empTh = s.querySelector('.wsp-emp');
        var days = s.querySelectorAll('.wsp-day');
        var first = days[0], last = days[days.length - 1];
        var table = s.querySelector('.wsp-grid');
        return { empW: empTh.offsetWidth,
                 dayFirst: first ? first.offsetWidth : null,
                 dayLast: last ? last.offsetWidth : null,
                 dayCount: days.length,
                 tableW: table.offsetWidth,
                 sheetW: s.offsetWidth };
    })()""")
    check('F: offsetWidth колонки ≈ inline ширине (мм→px)', geom['empW'] and abs(geom['empW'] - emp_mm * MM) < 4, (geom['empW'], emp_mm))
    # при 50mm-колонке день был бы ≈31px (вьюпорт 1280); с узкой
    # ФИО дни забирают остаток и РАВНЫ между собой (fixed-раскладка)
    check('G: дни равные и делят весь остаток ширины',
          geom['dayFirst'] and geom['dayFirst'] > 31.5 and abs(geom['dayFirst'] - geom['dayLast']) < 0.6,
          geom)
    check('G2: таблица занимает всю ширину листа',
          geom['tableW'] and abs(geom['tableW'] - geom['sheetW']) < 2, geom)
    check('K: print-медиа: базовый шрифт листа 11px', css['base'] == '11px', css['base'])
    check('L: шрифты НАД таблицей: title 18 / sub 14 / meta 12 / printed 11',
          css['title'] == '18px' and css['sub'] == '14px' and css['meta'] == '12px' and css['printed'] == '11px',
          (css['title'], css['sub'], css['meta'], css['printed']))
    check('M: шрифты ПОД таблицей: mev 11 / legend 11 / foot 10',
          css['mev'] == '11px' and css['legend'] == '11px' and css['foot'] == '10px',
          (css['mev'], css['legend'], css['foot']))
    check('N: шрифты В таблице: ФИО 10.5 / должность 8.5 / код 10 / ДН 7.5',
          css['fio'] == '10.5px' and css['pos'] == '8.5px' and css['cellFont'] == '10px' and css['daySpan'] == '7.5px',
          (css['fio'], css['pos'], css['cellFont'], css['daySpan']))
    check('O: высота ячейки 7.2mm (≈27.2px)', css['cellH'] and 26.5 < css['cellH'] < 30, css['cellH'])
    check('P: точка переработки 2.2mm (≈8.3px) — правила живы', css['overW'] is None or (css['overW'] and abs(css['overW'] - 2.2 * MM) < 1.5), css['overW'])
    check('Q: бейдж: inline-block 7.5px с цветом, план — dashed, wrap — absolute снизу',
          css['evDisplay'] == 'inline-block' and css['evFont'] == '7.5px' and
          css['planStyle'] == 'dashed' and css['wrapPosition'] == 'absolute' and css['wrapBottom'] not in (None, 'auto'),
          (css['evDisplay'], css['evFont'], css['planStyle'], css['wrapPosition'], css['wrapBottom']))

    # печать по-прежнему скрывает приложение, лист виден
    layout = page.evaluate("""(function(){
        var app = document.getElementById('mainApp');
        var s = document.getElementById('wsPrintSheet');
        return { appDisplay: app ? getComputedStyle(app).display : null,
                 sheetDisplay: getComputedStyle(s).display };
    })()""")
    check('R: print-медиа: приложение скрыто, лист виден',
          layout['appDisplay'] == 'none' and layout['sheetDisplay'] == 'block', layout)

    page.screenshot(path='scripts/task361-proof-print.png')
    page.emulate_media(media='screen')
    back = page.evaluate("getComputedStyle(document.getElementById('wsPrintSheet')).display")
    check('S: экран: лист снова скрыт', back == 'none', back)
    check('T: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, тёмная =================
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':760}, 'bc-t361-b', theme='dark')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.evaluate(STUB_PRINT)
    page2.click('#wsPrintBtn')
    page2.wait_for_timeout(400)
    sheet2 = page2.evaluate(JS_SHEET)
    emp2_mm = None
    if sheet2 and sheet2['empStyle']:
        try:
            emp2_mm = float(sheet2['empStyle'].split('width:')[1].split('mm')[0])
        except Exception:
            emp2_mm = None
    check('U: мобайл: лист построен, печать вызвана', sheet2 and sheet2['printCalled'] == 1, sheet2)
    check('V: мобайл: inline ширина «Сотрудника» в клампе', emp2_mm is not None and 24 <= emp2_mm <= 48, emp2_mm)
    check('W: мобайл: бейджи мероприятий в ячейках живы',
          sheet2 and sheet2['solidBadges'] >= 2 and sheet2['planBadges'] >= 1, sheet2)
    check('X: мобайл: 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
