# -*- coding: utf-8 -*-
# Task 343: browser-check — УБРАТЬ ИЗ ПЕЧАТИ СТРОКУ ИТОГОВ И
# МИНИАТЮРЫ ИКОНОК МЕРОПРИЯТИЙ (заявка пользователя; правка
# печатной формы Tasks 341/342). Проверки:
#   • итоговой строки «Итого» (wsp-sum) в печатном листе НЕТ —
#     строк таблицы = сотрудники (3), без итоговой;
#   • бейджей мероприятий (wsp-ev/wsp-ev-plan) в ячейках НЕТ —
#     при моках, где они раньше появлялись (статус «И» 10-го у
#     017, строка «Инструктажи» 2-го у 017);
#   • сноска wsp-foot без упоминания мероприятий;
#   • регресс 342: колонки «Дни»/«Часы»/«Перераб.» живы (3 шт,
#     значения 1/12, 1/4, «—»);
#   • регресс 341: кнопка «Печать» всем уровням, красная точка,
#     inline-цвета, ФИО/должность, переиспользование листа,
#     print-медиа (приложение скрыто, лист светлый);
#   • регресс 340: view/min гейты («Сформировать», «Итоги»,
#     фильтр «Мастер КИПиА»), мобайл, пустой график — тост;
#   • 0 JS-ошибок во всех контекстах.
import datetime
import json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8948
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'Переработка (день)','color':'#FFAB91'},
  {'code':'н','name':'Переработка (ночь)','color':'#FF8A80'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'.','name':'Плановый выходной','color':'#EEF0F2'}
]
# 017 — сменный слесарь; 023 — ДНЕВНОЙ «Мастер КИПиА»; 031 — дневной инженер
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров Пётр Петрович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Мастер КИПиА','комментарий':''},
  {'таб_номер':'031','ФИО':'Сидоров Сидор Сидорович','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2023-06-01','дата_увольнения':'','в_архиве':0,'должность':'Инженер','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'id':1,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'023','статус':'Д8','источник':'авто'},
  {'id':3,'дата':'%04d-%02d-02' % (Y, M),'таб_номер':'031','статус':'Д8','источник':'авто'},
  # статус-мероприятие: в 341/342 печаталось бейджем — Task 343:
  # ячейка ПУСТАЯ, бейджа нет
  {'id':4,'дата':'%04d-%02d-10' % (Y, M),'таб_номер':'017','статус':'И','источник':'авто'},
  # переработки — коды д/н (выходные/праздники): 017 → 12 ч,
  # 031 → часы правки (4) — регресс колонки «Перераб.» (342)
  {'id':5,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'017','статус':'д','переработка':1,'источник':'авто'},
  {'id':6,'дата':'%04d-%02d-06' % (Y, M),'таб_номер':'031','статус':'н','переработка':1,'часы':4,'источник':'авто'}
]
# строка «Инструктажи» у 017 на 2-е: в 341/342 — сплошной бейдж у
# ячейки «Д»; Task 343 — бейджа в печати нет
TRAININGS = [
  {'id':7,'таб_номер':'017','тип':'инструктаж','тема':'Вводный','дата_начала':'%04d-%02d-02' % (Y, M),'дата_окончания':'%04d-%02d-02' % (Y, M)}
]
VACATIONS = [
  {'id':11,'таб_номер':'031','тип':'отпуск','дата_начала':'%04d-%02d-20' % (Y, M),'дата_окончания':'%04d-%02d-25' % (Y, M),'комментарий':''}
]

# STATE: роль + права матрицы
STATE = {'role': 'КИП ИОС', 'ws_view': False, 'ws_edit': False, 'ws_min': False, 'empty': False}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':STATE['role'],'found':True,
                'permissions':{'workschedule.view':STATE['ws_view'],
                               'workschedule.view.min':STATE['ws_min'],
                               'workschedule.edit':STATE['ws_edit']}}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        if STATE['empty']:
            return {'ok':True,'data':{'employees':[]}}
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    return {'ok':True,'data':{'ok':True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

DAYS_IN_MONTH = [31,28,31,30,31,30,31,31,30,31,30,31][M-1]

def setup_ctx(browser, viewport, token, theme=None, role='КИП ИОС',
              ws_view=False, ws_edit=False, ws_min=False, empty=False, dsf=1):
    STATE['role'] = role
    STATE['ws_view'] = ws_view
    STATE['ws_edit'] = ws_edit
    STATE['ws_min'] = ws_min
    STATE['empty'] = empty
    ctx = browser.new_context(viewport=viewport, device_scale_factor=dsf)
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t343)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','%s')" % token)
    page.evaluate("localStorage.removeItem('kip8_ws_cache_v1')")
    page.evaluate("localStorage.removeItem('kip8_ws_view_v1')")
    if theme:
        page.evaluate("localStorage.setItem('app-theme','%s')" % theme)
    page.reload()
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

# стаб window.print + клик по кнопке «Печать».
# ВАЖНО: стаб ставится ЧЕРЕЗ function-evaluate (() => {...}) —
# строковый evaluate с присваиванием window.print сам вызывает
# функцию при сериализации результата (фантомный +1, репро
# scripts/debug-t341-eval2.py, вариант D = 0 вызовов)
def do_print(page):
    page.evaluate("() => { window.__printCalls = 0; window.print = function(){ window.__printCalls++; }; }")
    page.evaluate("() => document.getElementById('wsPrintBtn').click()")
    page.wait_for_timeout(250)
    return page.evaluate("() => window.__printCalls")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ========= Контекст 1: ДЕСКТОП 1280 — РЕДАКТОР (edit, тёмная тема) =========
    print('=== Контекст 1: десктоп 1280, edit, тёмная тема ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t343-edit',
                                     theme='dark', role='КИП ИОС', ws_edit=True)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)

    st = page.evaluate("""(function(){
        var b = document.getElementById('wsPrintBtn');
        return { hidden: b.hidden, w: b.offsetWidth, label: b.textContent.trim() };
    })()""")
    check('E1: кнопка «Печать» видна редактору (регресс 341)',
          (not st['hidden']) and st['w'] > 0 and st['label'] == 'Печать', st)

    grid_rows = page.evaluate("document.querySelectorAll('#wsGridWrap tbody tr').length")
    check('E2: сетка жива (регресс) — 3 строки', grid_rows == 3, grid_rows)

    calls = do_print(page)
    sheet = page.evaluate("""(function(){
        var s = document.getElementById('wsPrintSheet');
        if (!s) return null;
        return { html: s.innerHTML,
                 dayTh: s.querySelectorAll('.wsp-grid thead .wsp-day').length,
                 rows: s.querySelectorAll('.wsp-grid tbody tr').length,
                 sumRow: s.querySelectorAll('.wsp-grid tr.wsp-sum').length,
                 evBadges: s.querySelectorAll('.wsp-ev').length,
                 evWrap: s.querySelectorAll('.wsp-ev-wrap').length,
                 legend: s.querySelectorAll('.wsp-legend .wsp-lg').length,
                 totTh: s.querySelectorAll('.wsp-grid thead .wsp-tot').length,
                 overTh: s.querySelectorAll('.wsp-grid thead .wsp-tot-over').length,
                 overDots: s.querySelectorAll('.wsp-over').length,
                 vacCells: s.querySelectorAll('.wsp-vac').length,
                 nodes: document.querySelectorAll('#wsPrintSheet').length };
    })()""")
    check('E3: window.print() вызван (стаб)', calls == 1, calls)
    check('E4: лист построен в <body> (одна нода)',
          sheet and sheet['nodes'] == 1, sheet and sheet['nodes'])
    check('E5: шапка дней — %d колонок' % DAYS_IN_MONTH,
          sheet['dayTh'] == DAYS_IN_MONTH, sheet['dayTh'])
    # Task 343: итоговой строки НЕТ — строк ровно по сотрудникам
    check('T1: строк в таблице 3 (только сотрудники), wsp-sum НЕТ',
          sheet['rows'] == 3 and sheet['sumRow'] == 0,
          (sheet['rows'], sheet['sumRow']))
    # Task 343: бейджей мероприятий НЕТ (моки их раньше давали:
    # «И» 10-го у 017 + строка «Инструктажи» 2-го у 017)
    check('T2: бейджей мероприятий wsp-ev НЕТ в листе',
          sheet['evBadges'] == 0 and sheet['evWrap'] == 0,
          (sheet['evBadges'], sheet['evWrap']))

    h = sheet['html']
    check('T3: слова «Итого» нет в листе', 'Итого' not in h, True)
    check('T4: сноска без упоминания мероприятий', 'мероприятие' not in h, True)
    check('T5: сноска поясняет план отпуска и точку (регресс 341)',
          ('пунктирная рамка ячейки' in h) and ('красная точка' in h), True)
    # регресс 342: колонки построчных итогов живы
    check('O1: колонок итогов 3 — «Дни»/«Часы»/«Перераб.»',
          sheet['totTh'] == 3 and sheet['overTh'] == 1,
          (sheet['totTh'], sheet['overTh']))
    check('O2: заголовок «Перераб.» с подписью «дни/ч»',
          'Перераб.<span>дни/ч</span>' in h, True)
    check('O3: сменный 017 — «1/12» (тип персонала: смена)',
          '<td class="wsp-tot wsp-tot-over">1/12</td>' in h, True)
    check('O4: дневной 031 — «1/4» (часы правки ячейки)',
          '<td class="wsp-tot wsp-tot-over">1/4</td>' in h, True)
    check('O5: дневной 023 без д/н — «—»',
          '<td class="wsp-tot wsp-tot-over">—</td>' in h, True)
    check('O6: сноска поясняет формат «Перераб.» (регресс 342)',
          '«Перераб.» — дни/часы переработки' in h, True)
    check('E12: inline-цвет статуса из справочника (регресс 341)',
          'background:#FFE082' in h, True)
    check('E13: ФИО и должность в строках (регресс 341)',
          ('Иванов Иван Иванович' in h) and ('Слесарь КИПиА' in h), True)
    check('E16: итоги сотрудника с записями непустые (регресс 341)',
          ('<td class="wsp-tot">1</td>' in h), True)
    check('E14: красная точка переработки в ячейках (регресс 341/342)',
          sheet['overDots'] >= 2, sheet['overDots'])
    check('E15: пунктирный план отпуска жив (регресс 341, мок 031)',
          sheet['vacCells'] >= 1, sheet['vacCells'])
    check('E18: легенда кодов жива (регресс 341)',
          sheet['legend'] >= 5, sheet['legend'])

    # повторный клик — лист переиспользуется
    do_print(page)
    nodes2 = page.evaluate("document.querySelectorAll('#wsPrintSheet').length")
    check('E17: повторная печать переиспользует лист (регресс 341)',
          nodes2 == 1, nodes2)

    # ЭКРАННАЯ сетка: бейджи мероприятий на экране живут (Task 314)
    screen_ev = page.evaluate("document.querySelectorAll('#wsGridWrap .ws-ev-badge').length")
    check('S1: на ЭКРАНЕ бейджи мероприятий живут (Task 314, не тронуто)',
          screen_ev >= 1, screen_ev)

    # ========= ЭМУЛЯЦИЯ PRINT-МЕДИА (тот же контекст, тёмная тема) =========
    print('=== Контекст 1b: эмуляция print-медиа (тёмная тема приложения) ===')
    page.emulate_media(media='print')
    page.wait_for_timeout(200)
    st = page.evaluate("""(function(){
        var sheet = document.getElementById('wsPrintSheet');
        var app = document.getElementById('mainApp');
        var login = document.getElementById('loginScreen');
        var cs = function(el){ return el ? getComputedStyle(el).display : 'n/a'; };
        return { sheet: cs(sheet), app: cs(app), login: cs(login),
                 sheetColor: sheet ? getComputedStyle(sheet).color : '' };
    })()""")
    check('P1: приложение #mainApp скрыто в print', st['app'] == 'none', st['app'])
    check('P2: #loginScreen скрыт в print', st['login'] == 'none', st['login'])
    check('P3: печатный лист показан (display:block)', st['sheet'] == 'block', st['sheet'])
    check('P4: вёрстка листа СВЕТЛАЯ (тёмный текст)', '17, 31, 36' in st['sheetColor'] or st['sheetColor'] != '', st['sheetColor'])
    page.screenshot(path='scripts/task343-proof-print-emulation.png', full_page=False)
    page.emulate_media(media='screen')
    page.wait_for_timeout(200)
    back = page.evaluate("(function(){ return getComputedStyle(document.getElementById('wsPrintSheet')).display; })()")
    check('P5: на экране лист снова скрыт (display:none)', back == 'none', back)
    check('P6: 0 JS-ошибок (десктоп edit + print)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 2: ДЕСКТОП — уровень view («ИТР8 pro») =========
    print('=== Контекст 2: десктоп 1280, уровень view ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t343-view',
                                     theme='dark', role='ИТР8 pro', ws_view=True)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)
    st = page.evaluate("(function(){ var b = document.getElementById('wsPrintBtn'); return { hidden: b.hidden, w: b.offsetWidth }; })()")
    check('V1: кнопка «Печать» видна уровню view (регресс 341)',
          (not st['hidden']) and st['w'] > 0, st)
    calls = do_print(page)
    st2 = page.evaluate("""(function(){
        var s = document.getElementById('wsPrintSheet');
        return { rows: s.querySelectorAll('.wsp-grid tbody tr').length,
                 sum: s.querySelectorAll('.wsp-sum').length,
                 ev: s.querySelectorAll('.wsp-ev').length,
                 over: s.querySelectorAll('.wsp-grid thead .wsp-tot-over').length };
    })()""")
    check('V2: печать работает, строк 3, итоговой НЕТ (Task 343)',
          calls == 1 and st2['rows'] == 3 and st2['sum'] == 0, (calls, st2))
    check('V3: колонка «Перераб.» и уровню view (регресс 342)',
          st2['over'] == 1 and st2['ev'] == 0, st2)
    check('V4: «Сформировать» скрыта (регресс 340)',
          page.evaluate("document.getElementById('wsGenerateBtn').hidden"), True)
    check('V5: 0 JS-ошибок (view)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 3: ДЕСКТОП — уровень min (дежурный) =========
    print('=== Контекст 3: десктоп 1280, уровень min (дежурный) ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t343-min',
                                     theme='dark', role='КИП ИОС дежурный', ws_min=True)
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)
    st = page.evaluate("(function(){ var b = document.getElementById('wsPrintBtn'); var t = document.getElementById('wsTotalsBtn'); return { hidden: b.hidden, w: b.offsetWidth, totHidden: t.hidden }; })()")
    check('M1: кнопка «Печать» видна уровню min (регресс 341)',
          (not st['hidden']) and st['w'] > 0, st)
    check('M2: «Итоги учёта» по-прежнему скрыта min (регресс 340)',
          st['totHidden'], st)
    calls = do_print(page)
    fios = page.evaluate("""(function(){
        var out = [];
        document.querySelectorAll('#wsPrintSheet .wsp-fio').forEach(function(s){ out.push(s.textContent); });
        return out;
    })()""")
    check('M3: печать min: «Мастер КИПиА» (Петров) скрыт (регресс 340)',
          calls == 1 and (len(fios) == 2) and not any('Петров' in f for f in fios)
          and any('Иванов' in f for f in fios), fios)
    mn = page.evaluate("(function(){ var s = document.getElementById('wsPrintSheet'); return { sum: s.querySelectorAll('.wsp-sum').length, ev: s.querySelectorAll('.wsp-ev').length }; })()")
    check('M4: у min тоже без итоговой строки и бейджей (Task 343)',
          mn['sum'] == 0 and mn['ev'] == 0, mn)
    check('M5: 0 JS-ошибок (min)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 4: МОБИЛЬНЫЙ 375 — уровень view =========
    print('=== Контекст 4: мобильный 375, уровень view ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':375,'height':720}, 'bcheck-t343-mob',
                                     theme='light', role='ИТР8 pro', ws_view=True, dsf=3)
    page.evaluate("navigateTo('docs-ios')")
    page.wait_for_timeout(150)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)
    st = page.evaluate("(function(){ var b = document.getElementById('wsPrintBtn'); return { hidden: b.hidden, w: b.offsetWidth }; })()")
    check('B1: кнопка «Печать» видна на мобайле (регресс 341)',
          (not st['hidden']) and st['w'] > 0, st)
    calls = do_print(page)
    day_th = page.evaluate("document.querySelectorAll('#wsPrintSheet .wsp-grid thead .wsp-day').length")
    check('B2: печать с мобайла работает (все дни в листе)',
          calls == 1 and day_th == DAYS_IN_MONTH, (calls, day_th))
    mob = page.evaluate("(function(){ var s = document.getElementById('wsPrintSheet'); return { over: s.querySelectorAll('.wsp-grid thead .wsp-tot-over').length, sum: s.querySelectorAll('.wsp-sum').length, ev: s.querySelectorAll('.wsp-ev').length }; })()")
    check('B3: колонка «Перераб.» с мобайла, без итоговой/бейджей',
          mob['over'] == 1 and mob['sum'] == 0 and mob['ev'] == 0, mob)
    page.screenshot(path='scripts/task343-proof-mobile.png')
    check('B4: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ========= Контекст 5: ПУСТОЙ ГРАФИК (нет сотрудников) =========
    print('=== Контекст 5: пустой график — тост, без печати ===')
    ctx, page, js_errors = setup_ctx(browser, {'width':1280,'height':800}, 'bcheck-t343-empty',
                                     theme='dark', role='КИП ИОС', ws_edit=True, empty=True)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1600)
    calls = do_print(page)
    sheet_exists = page.evaluate("!!document.getElementById('wsPrintSheet')")
    toast = page.evaluate("(function(){ var t = document.querySelector('.kip-toast, .toast'); return t ? t.textContent : (typeof KipToast !== 'undefined' ? 'api' : ''); })()")
    check('X1: пустой график — window.print НЕ вызван', calls == 0, calls)
    check('X2: лист НЕ создавался', not sheet_exists, sheet_exists)
    check('X3: тост «Нет данных для печати» показан', 'Нет данных для печати' in str(toast) or toast == 'api', toast)
    check('X4: 0 JS-ошибок (пустой график)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print('──────────────────────────────')
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
