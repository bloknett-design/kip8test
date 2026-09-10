#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 362: browser-check — заявка пользователя: «при печати
# сменного графика, мероприятия должны быть указанны только для
# сменных сотрудников, так же при печати графика дневного
# персонала. и не отобразилось наименование кода проверки знаний
# ПЗ, хотя он есть в мероприятиях у дневного сотрудника».
# Контексты:
#   1. десктоп 1280 тёмная, Админ (edit): печать в ТРЁХ видах —
#      полный (3 мероприятия, в перечне кодов И/ОБ/ПЗ), сменный
#      (только Иванов: И; ПЗ/ОБ дневного НЕТ), дневной (только
#      Петров: ОБ + ПЗ; в перечне кодов «ПЗ — Проверка знаний» —
#      БАГ заявки: код мероприятия без записи сетки не
#      объяснялся); строки таблицы = виду; print-медиа: лист виден;
#   2. мобайл 375 touch, вид сохранён 'day' (localStorage до
#      загрузки): печать сразу дневная, ПЗ в перечне.
# + 0 JS-ошибок; скриншот-пруф печатного листа дневного вида.
# Стаб window.print — function-evaluate (урок Task 341).
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8960
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний','color':'#FFCDD2'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-01' % (Y, M if M > 1 else 12),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-07' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# записи месяца: сменному Д/Н/«.»/статус-И (виртуальный бейдж 361),
# дневному Д8/ОТ; ПЗ в сетке НЕТ — баг заявки воспроизведён: код
# живёт только в «Инструктажах»
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-10' % (Y, M),'таб_номер':'017','статус':'.','источник':'авто'},
  {'id':4,'дата':'%04d-%02d-08' % (Y, M),'таб_номер':'017','статус':'И','источник':'авто'},
  {'id':5,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':6,'дата':'%04d-%02d-20' % (Y, M),'таб_номер':'023','статус':'ОТ','источник':'авто'}
]

def trainings_default():
    prev_y, prev_m = (Y, M - 1) if M > 1 else (Y - 1, 12)
    return [
      # Иванов (сменный): инструктаж 07 числа
      {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по охране труда',
       'дата_начала':'%04d-%02d-07' % (Y, M),'дата_окончания':'','дата_проведения':''},
      # Петров (дневной): обучение с прошлого месяца до 02 числа
      {'id':2,'таб_номер':'023','тип':'обучение','тема':'Обучение по новому оборудованию',
       'дата_начала':'%04d-%02d-29' % (prev_y, prev_m),'дата_окончания':'%04d-%02d-02' % (Y, M),'дата_проведения':''},
      # Петров (дневной): проверка знаний ПЗ 15–16 — записи сетки НЕТ
      {'id':3,'таб_номер':'023','тип':'проверка_знаний','тема':'Проверка знаний промбезопасности',
       'дата_начала':'%04d-%02d-15' % (Y, M),'дата_окончания':'%04d-%02d-16' % (Y, M),'дата_проведения':''}
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

def setup_ctx(browser, viewport, token, theme=None, role='Админ', saved_view=None):
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t362)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    # сохранённый вид: None — чистый «полный» (как в 361), иначе —
    # вид из localStorage ДО загрузки (как пользователь оставил)
    if saved_view:
        page.evaluate("localStorage.setItem('kip8_ws_view_v1','%s')" % saved_view)
    else:
        page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

# стаб window.print — function-evaluate (урок Task 341)
STUB_PRINT = "() => { window.print = function(){ window.__printCalled = (window.__printCalled||0)+1; }; }"

# содержимое печатного листа: список мероприятий, перечень кодов,
# строки таблицы (вид), счётчик печати
JS_SHEET = """(function(){
    var s = document.getElementById('wsPrintSheet');
    if (!s) return null;
    var items = s.querySelectorAll('.wsp-mev-item');
    var mev = [], i;
    for (i = 0; i < items.length; i++) mev.push(items[i].textContent);
    var lgs = s.querySelectorAll('.wsp-legend .wsp-lg');
    var lg = [];
    for (i = 0; i < lgs.length; i++) lg.push(lgs[i].textContent);
    var rows = s.querySelectorAll('tbody tr');
    var fios = [];
    for (i = 0; i < rows.length; i++) {
        var f = rows[i].querySelector('.wsp-fio');
        if (f) fios.push(f.textContent);
    }
    var sub = s.querySelector('.wsp-sub');
    return { printCalled: window.__printCalled || 0,
             mevCount: items.length,
             mev: mev,
             lg: lg,
             fios: fios,
             sub: sub ? sub.textContent : '',
             html: s.innerHTML };
})"""

def print_and_read(page):
    page.evaluate(STUB_PRINT)
    page.click('#wsPrintBtn')
    page.wait_for_timeout(400)
    return page.evaluate(JS_SHEET)

def has(lst, sub):
    return any(sub in t for t in lst)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t362-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт (полный вид, 2 строки)', page.evaluate("(function(){var r=document.querySelectorAll('#wsGridWrap tbody tr');return r.length===2;})()"))

    # --- полный вид: все 3 мероприятия, перечень объясняет И/ОБ/ПЗ ---
    sh = print_and_read(page)
    check('C: полный вид — лист построен, печать 1 раз', sh and sh['printCalled'] == 1, sh)
    check('D: полный вид — 3 мероприятия (И+ОБ+ПЗ)', sh and sh['mevCount'] == 3, sh['mev'] if sh else None)
    check('E: полный вид — Иванов и Петров в списке',
          sh and has(sh['mev'], 'Иванов') and has(sh['mev'], 'Петров'), sh['mev'] if sh else None)
    check('F: полный вид — «ПЗ — Проверка знаний» в перечне кодов',
          sh and has(sh['lg'], 'ПЗ — Проверка знаний'), sh['lg'] if sh else None)
    check('G: полный вид — строки обоих сотрудников', sh and len(sh['fios']) == 2, sh['fios'] if sh else None)

    # --- сменный вид: мероприятия только сменного ---
    page.click('#wsViewBtn')
    page.wait_for_timeout(600)
    sh = print_and_read(page)
    check('H: сменный вид — 1 строка (Иванов)', sh and sh['fios'] == ['Иванов Иван Иванович'], sh['fios'] if sh else None)
    check('I: сменный вид — 1 мероприятие (инструктаж Иванова)',
          sh and sh['mevCount'] == 1 and has(sh['mev'], 'Повторный инструктаж') and has(sh['mev'], 'Иванов'),
          sh['mev'] if sh else None)
    check('J: сменный вид — ПЗ/ОБ дневного НЕ печатаются',
          sh and not has(sh['mev'], 'Петров') and not has(sh['mev'], 'Проверка знаний') and not has(sh['mev'], 'Обучение'),
          sh['mev'] if sh else None)
    check('K: сменный вид — код И в перечне, ПЗ/ОБ нет',
          sh and has(sh['lg'], 'И — Инструктаж') and not has(sh['lg'], 'ПЗ —') and not has(sh['lg'], 'ОБ —'),
          sh['lg'] if sh else None)

    # --- дневной вид: мероприятия только дневного + БАГ ПЗ ---
    page.click('#wsViewBtn')
    page.wait_for_timeout(600)
    sh = print_and_read(page)
    check('L: дневной вид — 1 строка (Петров)', sh and sh['fios'] == ['Петров Пётр Петрович'], sh['fios'] if sh else None)
    check('M: дневной вид — 2 мероприятия (ОБ + ПЗ Петрова)',
          sh and sh['mevCount'] == 2 and has(sh['mev'], 'Обучение') and has(sh['mev'], 'Проверка знаний'),
          sh['mev'] if sh else None)
    check('N: дневной вид — инструктаж Иванова НЕ печатается',
          sh and not has(sh['mev'], 'Повторный инструктаж') and not has(sh['mev'], 'Иванов'),
          sh['mev'] if sh else None)
    check('O: дневной вид — «ПЗ — Проверка знаний» в перечне (баг заявки)',
          sh and has(sh['lg'], 'ПЗ — Проверка знаний'), sh['lg'] if sh else None)
    check('P: дневной вид — код И сменного НЕ в перечне',
          sh and not has(sh['lg'], 'И — Инструктаж'), sh['lg'] if sh else None)
    check('Q: дневной вид — коды сетки Д8/ОТ + мероприятие ОБ в перечне',
          sh and has(sh['lg'], 'Д8 — День 8-час') and has(sh['lg'], 'ОТ — Отпуск') and has(sh['lg'], 'ОБ — Обучение'),
          sh['lg'] if sh else None)
    check('R: шапка листа помечает вид', sh and 'вид табеля: дневной' in sh['sub'], sh['sub'] if sh else None)

    # --- эмуляция print-медиа: лист виден, скриншот-пруф ---
    page.emulate_media(media='print')
    layout = page.evaluate("""(function(){
        var app = document.getElementById('mainApp');
        var s = document.getElementById('wsPrintSheet');
        return { appDisplay: app ? getComputedStyle(app).display : null,
                 sheetDisplay: getComputedStyle(s).display };
    })()""")
    check('S: print-медиа: приложение скрыто, лист виден',
          layout['appDisplay'] == 'none' and layout['sheetDisplay'] == 'block', layout)
    page.screenshot(path='scripts/task362-proof-print.png')
    page.emulate_media(media='screen')
    check('T: 0 JS-ошибок (десктоп, 3 печати)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 2: мобайл 375, сохранённый вид 'day' ============
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':375,'height':760}, 'bc-t362-b', theme='dark', saved_view='day')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    sh2 = print_and_read(page2)
    check('U: мобайл: печать построена (дневной вид из localStorage)',
          sh2 and sh2['printCalled'] == 1 and sh2['fios'] == ['Петров Пётр Петрович'], sh2)
    check('V: мобайл: только дневные мероприятия + ПЗ в перечне',
          sh2 and sh2['mevCount'] == 2 and has(sh2['lg'], 'ПЗ — Проверка знаний'), sh2['lg'] if sh2 else None)
    check('W: мобайл: 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
