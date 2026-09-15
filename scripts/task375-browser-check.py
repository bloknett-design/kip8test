#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 375: browser-check — заявки пользователя:
#   1) «В разделе Табель учёта рабочего времени в формате вывода на
#      печать, под графиком, столбец со списком кодов расположить
#      справа от столбца списка мероприятий на расстоянии 10px».
#   2) «В разделе хозрасчётных расходомеров, при внесении новых
#      данных, иногда они автоматически дублируются…» — анти-дубли:
#      кулдаун повторного «Сохранить», блок повтора того же значения
#      за ту же дату, свёртка дублей outbox при флаше.
# Контексты:
#   1. десктоп 1280 тёмная, Админ — РАСХОДОМЕРЫ:
#      - реальный ввод №2 → ровно ОДИН updateReading;
#      - двойной вызов submitInput подряд (двойной тап/Enter+клик) →
#        вторая отправка заблокирована кулдауном, prev НЕ сдвинут
#        дважды (payload.prev = предыдущее показание, не curr);
#      - повторный ввод ТОГО ЖЕ значения за ту же дату (первый час) →
#        отправки НЕТ, тост «уже введены за эту дату»;
#      - свёртка: outbox с парой «оригинал + двойной сдвиг» → флаш
#        отправляет ТОЛЬКО оригинал (prev исходный);
#      - правка в окне 1 ч (isEdit) НЕ блокируется.
#   2. десктоп 1280 тёмная, Админ — ПЕЧАТЬ ТАБЕЛЯ:
#      wsp-bottom: gap = 10px (computed), коды правее мероприятий
#      ровно на 10px (rect), оба столбика от общего верха, сноска
#      под обоими на всю ширину; регресс 360/362.
#   3. мобайл 375 — печать строится (gap 10px), ввод жив.
# + 0 JS-ошибок; скриншот-пруфы. Порт 8977.
import datetime
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8977
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DAYS = (datetime.date(Y, M + 1, 1) - datetime.timedelta(days=1)).day
YESTERDAY = TODAY - datetime.timedelta(days=1)
D3 = TODAY - datetime.timedelta(days=3)

WEEKENDS = [d for d in range(1, DAYS + 1)
            if datetime.date(Y, M, d).weekday() >= 5]
SAT1 = WEEKENDS[0]
WORK1 = SAT1 - 1 if SAT1 - 1 >= 1 else SAT1 + 2

def mdy(d):
    return '%d/%d/%d' % (d.month, d.day, d.year)

def iso(d):
    return '%d-%02d-%02d' % (d.year, d.month, d.day)

def meter(i, hoz, param, dprev, dcurr, prev, curr, period):
    return {'id': i, 'hoz': hoz, 'param': param, 'datePrev': mdy(dprev),
            'dateCurr': mdy(dcurr), 'prev': prev, 'curr': curr, 'unit': 'м³',
            'temp': None, 'gcal': None, 'period': period,
            'modRole': 'Админ', 'modName': 'user@test.local',
            'modDisplayName': 'user@test.local',
            'modTimestamp': datetime.datetime.now().isoformat()}

MOCK_METERS = [
    meter(2, 'Хозрасчёт №2', 'Расход воды речной в корпус 114',
          YESTERDAY, YESTERDAY, 383291.0, 383291.0, 'Ежедневно'),
    meter(4, 'Хозрасчёт №4', 'Расход воздуха технологического в корпус 114',
          D3, D3, 679700.0, 679700.0, 'Ежедневно'),
]

# --- табель: справочники (как в task364) ---
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'д', 'name': 'День в вых./праздник', 'color': '#FFD54F'},
  {'code': 'ОТ', 'name': 'Отпуск ежегодный основной', 'color': '#ECEFF1'},
  {'code': '.', 'name': 'Плановый выходной день', 'color': '#EEF0F2'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#B3E5FC'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#D1C4E9'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'}
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M if M > 1 else 12),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''}
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
  {'id': 2, 'name': 'Дневной 5/2', 'cycle': 7, 'description': '',
   'days': [{'day': 1, 'status': 'Д8'}, {'day': 2, 'status': 'Д8'},
            {'day': 3, 'status': 'Д8'}, {'day': 4, 'status': 'Д8'},
            {'day': 5, 'status': 'Д8'}, {'day': 6, 'status': ''},
            {'day': 7, 'status': ''}]}
]
ENTRIES = [
  {'id': 1, 'дата': '%04d-%02d-%02d' % (Y, M, WORK1), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
  {'id': 2, 'дата': '%04d-%02d-%02d' % (Y, M, WORK1), 'таб_номер': '023', 'статус': 'Д8', 'источник': 'авто'},
  {'id': 3, 'дата': '%04d-%02d-%02d' % (Y, M, SAT1), 'таб_номер': '017', 'статус': 'д', 'источник': 'авто'},
  {'id': 4, 'дата': '%04d-%02d-20' % (Y, M), 'таб_номер': '023', 'статус': 'ОТ', 'источник': 'авто'}
]
TRAININGS = [
  {'id': 1, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Повторный инструктаж по охране труда',
   'дата_начала': '%04d-%02d-07' % (Y, M), 'дата_окончания': '', 'дата_проведения': ''},
  {'id': 2, 'таб_номер': '023', 'тип': 'обучение', 'тема': 'Обучение по новому оборудованию',
   'дата_начала': '%04d-%02d-02' % (Y, M), 'дата_окончания': '', 'дата_проведения': ''},
  {'id': 3, 'таб_номер': '023', 'тип': 'проверка_знаний', 'тема': 'Проверка знаний промбезопасности',
   'дата_начала': '%04d-%02d-15' % (Y, M), 'дата_окончания': '%04d-%02d-16' % (Y, M), 'дата_проведения': ''}
]

CAPTURED = []

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': json.loads(json.dumps(MOCK_METERS))}}
    if action == 'flowmeter.getValidationRules':
        return {'ok': True, 'data': {'rules': []}}
    if action == 'flowmeter.getRecentAllMeters':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.updateReading':
        CAPTURED.append(body)
        pid = body.get('id') if body else None
        for m in MOCK_METERS:
            if m['id'] == pid:
                m['prev'] = body.get('prev', m['prev'])
                m['curr'] = body.get('curr', m['curr'])
                m['datePrev'] = body.get('datePrev', m['datePrev'])
                m['dateCurr'] = body.get('dateCurr', m['dateCurr'])
                m['modTimestamp'] = datetime.datetime.now().isoformat()
                break
        return {'ok': True, 'data': {'id': pid}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listEntries':
        month = body.get('month') if body else None
        if month == M:
            return {'ok': True, 'data': {'entries': ENTRIES}}
        return {'ok': True, 'data': {'entries': []}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def setup_ctx(browser, viewport, token, theme='dark'):
    ctx = browser.new_context(viewport=viewport)
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())
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
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t375)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','%s');" % token +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    return ctx, page, js_errors

STUB_PRINT = "() => { window.print = function(){ window.__printCalled = (window.__printCalled||0)+1; }; }"

JS_BOTTOM_LAYOUT = """(function(){
    var s = document.getElementById('wsPrintSheet');
    if (!s) return null;
    var bottom = s.querySelector('.wsp-bottom');
    var mev = s.querySelector('.wsp-bottom .wsp-mev');
    var legend = s.querySelector('.wsp-bottom .wsp-legend');
    var foot = s.querySelector('.wsp-foot');
    if (!bottom || !mev || !legend || !foot) return null;
    var cb = getComputedStyle(bottom), cm = getComputedStyle(mev), cl = getComputedStyle(legend);
    var bm = bottom.getBoundingClientRect(), mm = mev.getBoundingClientRect(),
        lm = legend.getBoundingClientRect(), fm = foot.getBoundingClientRect();
    var lgs = legend.querySelectorAll('.wsp-lg');
    var lgTexts = [];
    for (var i = 0; i < lgs.length; i++) lgTexts.push(lgs[i].textContent);
    var mevs = mev.querySelectorAll('.wsp-mev-item');
    return {
      display: cb.display, dir: cb.flexDirection, gap: cb.columnGap,
      mevFlex: cm.flex, legendFlex: cl.flex, legendMax: cl.maxWidth,
      mevTop: mm.top, legendTop: lm.top,
      legendLeft: lm.left, mevRight: mm.right,
      mevW: mm.width, legendW: lm.width, bottomW: bm.width,
      mevBottom: mm.bottom, legendBottom: lm.bottom, footTop: fm.top,
      footW: fm.width,
      lg: lgTexts, mevCount: mevs.length
    };
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: расходомеры — анти-дубли =================
    ctx, page, js_errors = setup_ctx(browser, {'width': 1280, 'height': 800}, 'bc-t375-a')
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1500)
    check('B: список расходомеров отрисован',
          page.evaluate("document.querySelectorAll('.flow-card').length") >= 2)

    # --- реальный ввод №2: ровно ОДНА отправка ---
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383400,5')
    page.click('.flow-input-submit')
    page.wait_for_timeout(2000)
    c2 = [c for c in CAPTURED if c.get('id') == 2]
    check('C: ввод №2 — ровно ОДИН updateReading',
          len(c2) == 1, len(c2))
    check('D: payload №2 корректен (prev=383291, curr=383400.5, дата=вчера)',
          c2 and c2[0].get('prev') == 383291 and c2[0].get('curr') == 383400.5 and
          c2[0].get('dateCurr') == mdy(YESTERDAY),
          json.dumps(c2[0], ensure_ascii=False)[:160] if c2 else None)
    n_out = page.evaluate("FlowmeterData._outboxCount()")
    check('E: outbox пуст после доставки', n_out == 0, n_out)

    # --- двойной вызов submitInput (двойной тап / Enter+клик) ---
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383500')
    page.evaluate("FlowmeterData.submitInput(); FlowmeterData.submitInput();")
    page.wait_for_timeout(2000)
    c2 = [c for c in CAPTURED if c.get('id') == 2]
    check('F: двойной вызов — вторая отправка НЕ ушла (всего 2 для №2)',
          len(c2) == 2, len(c2))
    check('G: prev НЕ сдвинут дважды (payload.prev=383400.5, не 383500)',
          c2 and c2[1].get('prev') == 383400.5 and c2[1].get('curr') == 383500,
          json.dumps(c2[1], ensure_ascii=False)[:160] if len(c2) > 1 else None)
    check('H: outbox пуст (дубль не копится)', page.evaluate("FlowmeterData._outboxCount()") == 0)

    # --- повтор ТОГО ЖЕ значения за ту же дату (первый час) ---
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383500')
    page.click('.flow-input-submit')
    page.wait_for_timeout(800)
    c2 = [c for c in CAPTURED if c.get('id') == 2]
    check('I: повтор того же значения — отправки НЕТ (осталось 2)',
          len(c2) == 2, len(c2))
    toast = page.evaluate("(document.getElementById('toastMessage')||{}).textContent")
    check('J: тост «уже введены за эту дату»',
          bool(toast) and 'уже введены' in toast and 'Изменить показания' in toast, toast)
    check('K: outbox по-прежнему пуст', page.evaluate("FlowmeterData._outboxCount()") == 0)

    # --- свёртка: outbox с парой «оригинал + двойной сдвиг» ---
    page.evaluate("""(function(){
        FlowmeterData._outboxAdd({ cid: 't375-e1', kind: 'day', state: 'pending',
            payload: { id: 4, prev: 679700, curr: 680000, datePrev: '%s', dateCurr: '%s', temp: null, isEdit: false } });
        FlowmeterData._outboxAdd({ cid: 't375-e2', kind: 'day', state: 'pending',
            payload: { id: 4, prev: 680000, curr: 680000, datePrev: '%s', dateCurr: '%s', temp: null, isEdit: false } });
        return FlowmeterData._outboxCount();
    })""" % (mdy(D3), mdy(YESTERDAY), mdy(YESTERDAY), mdy(YESTERDAY)))
    page.wait_for_timeout(300)
    check('L: пара «оригинал + двойной сдвиг» засеяна (2 записи)',
          page.evaluate("FlowmeterData._outboxCount()") == 2)
    page.evaluate("FlowmeterData._flushOutbox('init')")
    page.wait_for_timeout(2000)
    c4 = [c for c in CAPTURED if c.get('id') == 4]
    check('M: свёртка — ушла ТОЛЬКО оригинальная запись',
          len(c4) == 1 and c4[0].get('prev') == 679700 and c4[0].get('curr') == 680000,
          [json.dumps(c, ensure_ascii=False)[:120] for c in c4])
    check('N: outbox пуст после флаша', page.evaluate("FlowmeterData._outboxCount()") == 0)

    # --- правка в окне 1 ч (isEdit) НЕ блокируется ---
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(true)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383501')
    page.click('.flow-input-submit')
    page.wait_for_timeout(2000)
    c2 = [c for c in CAPTURED if c.get('id') == 2]
    check('O: правка (isEdit) прошла — 3-я отправка для №2',
          len(c2) == 3 and c2[2].get('isEdit') is True and c2[2].get('curr') == 383501,
          json.dumps(c2[2], ensure_ascii=False)[:160] if len(c2) > 2 else None)
    check('P: 0 JS-ошибок (расходомеры)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: печать табеля — 10px =================
    ctx, page, js_errors = setup_ctx(browser, {'width': 1280, 'height': 800}, 'bc-t375-b')
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('Q: сетка табеля открылась', page.evaluate("!!document.querySelector('#wsGridWrap table')"))
    page.evaluate(STUB_PRINT)
    page.click('#wsPrintBtn')
    page.wait_for_timeout(400)
    check('R: печать вызвана, лист построен',
          page.evaluate("(window.__printCalled||0) === 1 && !!document.querySelector('#wsPrintSheet .wsp-bottom')"))
    page.emulate_media(media='print')
    lay = page.evaluate(JS_BOTTOM_LAYOUT)
    check('S: wsp-bottom — flex-ряд (регресс 364)',
          lay and lay['display'] == 'flex' and lay['dir'] == 'row',
          lay and (lay['display'], lay['dir']))
    check('T: зазор между столбиками = 10px (computed)',
          lay and lay['gap'] == '10px', lay and lay['gap'])
    dist = lay and (lay['legendLeft'] - lay['mevRight'])
    check('U: коды ПРАВЕЕ мероприятий ровно на 10px (rect)',
          dist is not None and abs(dist - 10) <= 1.5, dist)
    check('V: оба столбика от общего верха (один ряд)',
          lay and abs(lay['mevTop'] - lay['legendTop']) < 3,
          lay and (lay['mevTop'], lay['legendTop']))
    check('W: мероприятия тянутся на остаток ряда (регресс 364)',
          lay and lay['mevW'] > lay['bottomW'] * 0.5, lay and lay['mevW'])
    check('X: сноска ПОД обёрткой, на всю ширину листа',
          lay and lay['footTop'] >= max(lay['mevBottom'], lay['legendBottom']) - 1 and
          lay['footW'] >= lay['bottomW'] - 2, lay and (lay['footTop'], lay['footW']))
    check('Y: регресс 362 — «ПЗ — Проверка знаний» в перечне кодов',
          lay and any('ПЗ — Проверка знаний' in t for t in lay['lg']), lay and lay['lg'])
    check('Z: регресс 360 — 3 мероприятия в левом столбике',
          lay and lay['mevCount'] == 3, lay and lay['mevCount'])
    page.screenshot(path='scripts/task375-proof-print.png', full_page=True)
    page.emulate_media(media='screen')
    check('AA: 0 JS-ошибок (печать)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 3: мобайл 375 =================
    ctx, page, js_errors = setup_ctx(browser, {'width': 375, 'height': 760}, 'bc-t375-c')
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    page.evaluate(STUB_PRINT)
    page.click('#wsPrintBtn')
    page.wait_for_timeout(400)
    page.emulate_media(media='print')
    lay2 = page.evaluate(JS_BOTTOM_LAYOUT)
    check('AB: мобайл: печать — wsp-bottom, зазор 10px',
          lay2 and lay2['display'] == 'flex' and lay2['gap'] == '10px' and
          lay2['legendLeft'] >= lay2['mevRight'] - 1,
          lay2 and (lay2['gap'], lay2['legendLeft'] - lay2['mevRight']))
    page.emulate_media(media='screen')
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1200)
    page.evaluate("FlowmeterData.openDetail(2)")
    page.wait_for_timeout(500)
    page.evaluate("FlowmeterData.openInput(false)")
    page.wait_for_timeout(400)
    page.fill('#flowInputField', '383502')
    page.evaluate("FlowmeterData.submitInput(); FlowmeterData.submitInput();")
    page.wait_for_timeout(2000)
    c2m = [c for c in CAPTURED if c.get('id') == 2]
    check('AC: мобайл: двойной ввод — дубля нет (одна новая отправка)',
          len(c2m) == 4 and c2m[3].get('curr') == 383502, len(c2m))
    check('AD: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
