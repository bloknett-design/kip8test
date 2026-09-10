#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 360: browser-check — заявка пользователя (печатная форма
# графика работы): «под графиком вначале должен отображаться список
# мероприятий на текущий месяц в один столбик, а под списком, в
# один столбик перечень кодов с их наименованием только которые
# есть в этом месяце».
# Контексты:
#   1. десктоп 1280 тёмная, Админ (edit): печать с мероприятиями
#      месяца (одна запись в месяце, одна ПЕРЕСЕКАЮЩАЯ границу
#      29.08–02.09, одна ВНЕ месяца — НЕ печатается) и перечнем
#      кодов ТОЛЬКО месяца (использованные Д/Н/./ОТ печатаются,
#      НЕиспользуемые Д8/д — НЕТ); порядок секций: таблица →
#      мероприятия → коды → сноска; эмуляция print-медиа: приложение
#      скрыто, лист виден, .wsp-mev-item/.wsp-lg — display:block
#      (один столбик);
#   2. десктоп 1280 тёмная, БЕЗ мероприятий — «нет мероприятий в
#      этом месяце»;
#   3. мобайл 375 touch — печать строится, секции на месте.
# + 0 JS-ошибок; скриншоты-пруфы печатного листа.
# Стаб window.print — function-evaluate (урок Task 341: строковый
# evaluate с присваиванием window.print вызывает его при
# сериализации результата — фантомный вызов).
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
  {'code':'.','name':'Плановый выходной день','color':'#EEF0F2'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'%04d-%02d-01' % (Y, M if M > 1 else 12),'дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'%04d-%02d-07' % (Y, M),'дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# коды МЕСЯЦА: Д, Н, «.», ОТ (023); Д8 и д НЕ используются — их в
# перечне быть НЕ должно
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-03' % (Y, M),'таб_номер':'017','статус':'Н','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-10' % (Y, M),'таб_номер':'017','статус':'.','источник':'авто'},
  {'id':4,'дата':'%04d-%02d-15' % (Y, M),'таб_номер':'023','статус':'ОТ','источник':'авто'}
]

# мероприятия: в месяце, ПЕРЕСЕКАЮЩАЯ границу (предыдущий месяц),
# ВНЕ месяца (следующий) — НЕ печатается
def trainings_default():
    prev_y, prev_m = (Y, M - 1) if M > 1 else (Y - 1, 12)
    next_y, next_m = (Y, M + 1) if M < 12 else (Y + 1, 1)
    return [
      {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный инструктаж по охране труда',
       'дата_начала':'%04d-%02d-07' % (Y, M),'дата_окончания':'','дата_проведения':''},
      {'id':2,'таб_номер':'023','тип':'обучение','тема':'Обучение по новому оборудованию',
       'дата_начала':'%04d-%02d-29' % (prev_y, prev_m),'дата_окончания':'%04d-%02d-02' % (Y, M),'дата_проведения':''},
      {'id':3,'таб_номер':'017','тип':'проверка_знаний','тема':'Вне месяца — НЕ печатается',
       'дата_начала':'%04d-%02d-05' % (next_y, next_m),'дата_окончания':'','дата_проведения':''}
    ]

STATE = {'role': 'Админ', 'trainings': 'default'}

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
        trs = trainings_default() if STATE['trainings'] == 'default' else []
        return {'ok':True,'data':{'trainings':trs}}
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t360)')
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

# содержимое печатного листа
JS_SHEET = """(function(){
    var s = document.getElementById('wsPrintSheet');
    if (!s) return null;
    var iTable = s.innerHTML.indexOf('</tbody></table>');
    var iMev = s.innerHTML.indexOf('<div class="wsp-mev">');
    var iLegend = s.innerHTML.indexOf('<div class="wsp-legend">');
    var iFoot = s.innerHTML.indexOf('<div class="wsp-foot">');
    var mev = s.querySelector('.wsp-mev');
    return { html: s.innerHTML, iTable: iTable, iMev: iMev, iLegend: iLegend, iFoot: iFoot,
             mevText: mev ? mev.textContent : null,
             legendText: s.querySelector('.wsp-legend') ? s.querySelector('.wsp-legend').textContent : null,
             mevCount: s.querySelectorAll('.wsp-mev-item:not(.wsp-mev-none)').length,
             lgCount: s.querySelectorAll('.wsp-legend .wsp-lg').length,
             printCalled: window.__printCalled || 0 };
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t360-a', theme='dark')
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B: график открыт', page.evaluate("!!document.querySelector('#wsGridWrap table')"))

    # стаб печати + клик «Печать»
    page.evaluate(STUB_PRINT)
    page.click('#wsPrintBtn')
    page.wait_for_timeout(400)
    sheet = page.evaluate(JS_SHEET)
    check('C: лист построен, window.print вызван 1 раз', sheet and sheet['printCalled'] == 1, sheet)
    check('D: секция мероприятий есть, 2 записи (третья — вне месяца)',
          sheet['iMev'] != -1 and sheet['mevCount'] == 2, sheet)
    check('E: заголовок «Мероприятия · %s %d · 2»' % (MONTH_NAME, Y),
          ('Мероприятия · %s %d · 2' % (MONTH_NAME, Y)) in sheet['html'], sheet['mevText'])
    check('F: запись месяца — дата/код/тема/ФИО',
          ('07.%02d' % M) in sheet['mevText'] and 'И · Повторный инструктаж по охране труда · Иванов Иван Иванович' in sheet['mevText'], sheet['mevText'])
    check('G: запись вне месяца НЕ печатается',
          'Вне месяца' not in sheet['mevText'], sheet['mevText'])

    # диапазон через границу: 29.<prev>–02.<M>
    prev_m = M - 1 if M > 1 else 12
    range_txt = '29.%02d–02.%02d' % (prev_m, M)
    check('H: диапазон пересечения %s' % range_txt,
          range_txt in sheet['mevText'], sheet['mevText'])

    # перечень кодов: использованные есть, НЕиспользуемых НЕТ
    check('I: коды месяца: Д/Н/«.»/ОТ — с наименованиями',
          'Д — День (12-час)' in sheet['legendText'] and
          'Н — Ночь (12-час)' in sheet['legendText'] and
          '. — Плановый выходной день' in sheet['legendText'] and
          'ОТ — Отпуск ежегодный основной' in sheet['legendText'], sheet['legendText'])
    check('J: НЕиспользуемые коды Д8/д НЕ печатаются',
          'Д8' not in sheet['legendText'] and 'д — День в вых./праздник' not in sheet['legendText'], sheet['legendText'])
    check('K: 4 строки перечня (один столбик)', sheet['lgCount'] == 4, sheet)

    # порядок секций
    check('L: порядок: таблица → мероприятия → коды → сноска',
          sheet['iTable'] != -1 and sheet['iTable'] < sheet['iMev'] < sheet['iLegend'] < sheet['iFoot'], sheet)

    # эмуляция print-медиа: приложение скрыто, лист виден, ОДИН СТОЛБИК
    page.emulate_media(media='print')
    layout = page.evaluate("""(function(){
        var app = document.getElementById('mainApp');
        var s = document.getElementById('wsPrintSheet');
        var item = s.querySelector('.wsp-mev-item');
        var lg = s.querySelector('.wsp-legend .wsp-lg');
        return { appDisplay: app ? getComputedStyle(app).display : null,
                 sheetDisplay: getComputedStyle(s).display,
                 itemDisplay: item ? getComputedStyle(item).display : null,
                 lgDisplay: lg ? getComputedStyle(lg).display : null };
    })()""")
    check('M: print-медиа: приложение скрыто, лист виден',
          layout['appDisplay'] == 'none' and layout['sheetDisplay'] == 'block', layout)
    check('N: print-медиа: строка мероприятия display:block (один столбик)',
          layout['itemDisplay'] == 'block', layout)
    check('O: print-медиа: строка кода display:block (один столбик)',
          layout['lgDisplay'] == 'block', layout)
    page.screenshot(path='scripts/task360-proof-print.png')
    page.emulate_media(media='screen')
    back = page.evaluate("getComputedStyle(document.getElementById('wsPrintSheet')).display")
    check('P: экран: лист снова скрыт', back == 'none', back)
    check('Q: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 2: десктоп, тёмная, БЕЗ мероприятий ============
    STATE['trainings'] = 'empty'
    ctx2, page2, js_errors2 = setup_ctx(browser, {'width':1280,'height':800}, 'bc-t360-b', theme='dark')
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.evaluate(STUB_PRINT)
    page2.click('#wsPrintBtn')
    page2.wait_for_timeout(400)
    sheet2 = page2.evaluate(JS_SHEET)
    check('R: без мероприятий — заглушка «нет мероприятий в этом месяце»',
          sheet2 and 'нет мероприятий в этом месяце' in sheet2['mevText'], sheet2['mevText'] if sheet2 else None)
    check('S: без мероприятий — заголовок без счётчика, 0 записей',
          sheet2['mevCount'] == 0 and ('Мероприятия · %s %d' % (MONTH_NAME, Y)) in sheet2['html'], sheet2)
    check('T: перечень кодов при пустых мероприятиях жив (4 кода месяца)',
          sheet2['lgCount'] == 4, sheet2)
    check('U: 0 JS-ошибок (пустой месяц)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 375, тёмная =================
    STATE['trainings'] = 'default'
    ctx3, page3, js_errors3 = setup_ctx(browser, {'width':375,'height':760}, 'bc-t360-c', theme='dark')
    page3.evaluate("navigateTo('work-schedule')")
    page3.wait_for_timeout(3000)
    page3.evaluate(STUB_PRINT)
    page3.click('#wsPrintBtn')
    page3.wait_for_timeout(400)
    sheet3 = page3.evaluate(JS_SHEET)
    check('V: мобайл: печать строится, секции на месте',
          sheet3 and sheet3['iMev'] != -1 and sheet3['mevCount'] == 2 and sheet3['lgCount'] == 4, sheet3)
    check('W: 0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print()
print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
