#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 381: browser-check — заявки пользователя:
#   1) «Фон итогов верни как был до белого»: ячейки значений итогов
#      (td.ws-tt-num) — computed backgroundColor ПРОЗРАЧНЫЙ (обе
#      темы); зебра чётных строк ВОССТАНОВЛЕНА (tr even: 0.09 тёмная /
#      0.07 светлая); «Часы»/«Переработка» — базовая палитра тем
#      (#4ac771/#e0a23c тёмная, #1d7a37/#a06a13 светлая); линии
#      шахматки Task 378 ЖИВЫ; нулей в ячейках НЕТ; панель итогов
#      светлой темы #e9e7de; шахматка Task 379 (#FFFFFF пустых ячеек)
#      не тронута.
#   2) «При прокрутке текста в свёрнутых окнах мероприятий и норм,
#      значки раскрытия должны оставаться на месте»: окно
#      мероприятий (5 строк) — rect значка ДО прокрутки = ПОСЛЕ
#      (программный scrollTop 120 и max, колесо мыши, возврат в 0);
#      окно норм — слушатель прикреплён (флаг _barExpPin). Раскрытие
#      Task 378/379 живо (высота = scrollHeight, маржа 95−H, бар
#      95px).
#   3) «Окно „Мероприятия“ — не каждая строка … „плашка“ … общий фон
#      всего пространства окна на уровне текста»: соседние строки
#      ОДНОГО срока СКЛЕЕНЫ (зазор ≤ 0.75px); строки до КРАЁВ окна
#      (ширина строки = clientWidth окна); от заголовка до первой
#      строки 3px; тинты Task 380 живы; стык прошедших/идущих есть.
# + 0 JS-ошибок; мобайл 375 (склейка + прикол + итоги). Порт 8990.
import calendar, datetime, json, re
from collections import Counter
from urllib.parse import unquote
from PIL import Image
from playwright.sync_api import sync_playwright

PORT = 8990
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
TODAY_ISO = '%04d-%02d-%02d' % (Y, M, TODAY.day)

def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': '.', 'name': 'Плановый выходной день', 'color': '#EEF0F2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '018', 'ФИО': 'Сидоров Сидор Сидорович', 'тип': 'сменный', 'смена': 2,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
  {'id': 2, 'name': 'Дневной 5/2', 'cycle': 7, 'description': '',
   'days': [{'day': 1, 'status': 'Д8'}, {'day': 2, 'status': 'Д8'},
            {'day': 3, 'status': 'Д8'}, {'day': 4, 'status': 'Д8'},
            {'day': 5, 'status': 'Д8'}, {'day': 6, 'status': ''},
            {'day': 7, 'status': ''}]},
]
ENTRIES = [
  {'id': 1, 'дата': d(-6), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
  {'id': 2, 'дата': d(-2), 'таб_номер': '018', 'статус': 'Д8', 'источник': 'авто'},
]
# Task 381: мероприятия ВОКРУГ «сегодня» (та же раскладка Task 380) —
# прошедшие подряд, затем идущее-сегодня и будущие подряд: видны
# ДВЕ сплошные зоны общего фона и СТЫК между ними
TRAININGS = [
  {'id': 80, 'тема': 'Повторный инструктаж по охране труда (давно прошедший)',
   'тип': 'инструктаж', 'дата_начала': d(-12), 'дата_окончания': d(-12),
   'таб_номер': '017', 'подразделение': ''},
  {'id': 81, 'тема': 'Обучение по новой редакции инструкций (прошедший диапазон)',
   'тип': 'обучение', 'дата_начала': d(-9), 'дата_окончания': d(-7),
   'таб_номер': '018', 'подразделение': ''},
  {'id': 82, 'тема': 'Целевой инструктаж (идёт сегодня)',
   'тип': 'инструктаж', 'дата_начала': d(-1), 'дата_окончания': d(1),
   'таб_номер': '023', 'подразделение': ''},
  {'id': 83, 'тема': 'Проверка знаний (будущее)',
   'тип': 'проверка_знаний', 'дата_начала': d(2), 'дата_окончания': d(3),
   'таб_номер': '017', 'подразделение': ''},
  {'id': 84, 'тема': 'Инструктаж по пожарной безопасности (далёкое будущее)',
   'тип': 'инструктаж', 'дата_начала': d(5), 'дата_окончания': d(9),
   'таб_номер': '018', 'подразделение': ''},
]
EXPECTED_PAST = sum(1 for t in TRAININGS
                    if (t['дата_окончания'] or t['дата_начала']) < TODAY_ISO)

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
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
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5

def parse_rgb(s):
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', s or '')
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def mode_color(img, x0, x1, y):
    c = Counter()
    for x in range(x0, x1, 5):
        c[img.getpixel((x, y))] += 1
    return c.most_common(1)[0][0]

def attach(page, ctx, theme, tag):
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
        route.fulfill(status=404, content_type='text/plain', body='not found (t381-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t381');" +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# Строки окна мероприятий: склейка + края + тинты
ROWS_JS = """(function(){
    var panel = document.getElementById('wsEventsPanel');
    var cap = panel.querySelector('.ws-cp-cap');
    var rows = Array.prototype.slice.call(
        panel.querySelectorAll('.ws-ep-item'));
    var pr = panel.getBoundingClientRect();
    var out = { rows: [], pastN: 0, upN: 0,
                panelW: panel.clientWidth,
                panelTop: pr.top,
                panelLeft: pr.left, panelRight: pr.right,
                panelBg: getComputedStyle(panel).backgroundColor };
    if (cap) out.capBottom = cap.getBoundingClientRect().bottom;
    rows.forEach(function(r){
        var rc = r.getBoundingClientRect();
        var cs = getComputedStyle(r);
        var o = { past: r.classList.contains('ws-ep-past'),
                  bg: cs.backgroundColor, pad: cs.padding, mar: cs.margin,
                  left: rc.left, right: rc.right, top: rc.top, bottom: rc.bottom,
                  width: rc.width,
                  txt: r.textContent.replace(/\\s+/g, ' ').slice(0, 24) };
        if (o.past) out.pastN++; else out.upN++;
        out.rows.push(o);
    });
    return out;
})()"""

# Итоги: прозрачные ячейки + зебра + цвета + линии + нули
# (десктоп — тело шторки #wsTtBody; мобайл — тело страницы
# итогов #wsTtPageBody: _ttBodyEl выбирает его в режиме _ttPage)
TT_JS = """(function(){
    var body = document.getElementById('wsTtBody');
    var t = body ? body.querySelector('.ws-tt-table') : null;
    if (!t) {
        body = document.getElementById('wsTtPageBody');
        t = body ? body.querySelector('.ws-tt-table') : null;
    }
    if (!t) return { err: 'NO TABLE' };
    var trs = t.querySelectorAll('tbody tr');
    var odd = trs[0], even = trs[1];
    var num = odd.querySelector('td.ws-tt-num');
    var hours = t.querySelector('td.ws-tt-hours');
    var over = t.querySelector('td.ws-tt-over');
    var panel = document.querySelector('.ws-totals-panel');
    return {
        nRows: trs.length,
        numBg: getComputedStyle(num).backgroundColor,
        oddBg: getComputedStyle(odd).backgroundColor,
        evenBg: getComputedStyle(even).backgroundColor,
        hoursC: hours ? getComputedStyle(hours).color : null,
        overC: over ? getComputedStyle(over).color : null,
        numBorder: getComputedStyle(num).borderBottomColor,
        panelBg: panel ? getComputedStyle(panel).backgroundColor : null,
        zeros: (body.innerHTML.match(/>0<\\/td>/g) || []).length
    };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= ДЕСКТОП: обе темы =================
    for theme in ('dark', 'light'):
        print('--- ДЕСКТОП 1280, тема %s ---' % theme)
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        js_errors = attach(page, ctx, theme, theme)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2000)

        # ---------- ЧАСТЬ 3: окно «Мероприятия» ----------
        r = page.evaluate(ROWS_JS)
        exp_past_bg = 'rgba(255, 255, 255, 0.12)' if theme == 'dark' else 'rgba(255, 255, 255, 0.55)'
        exp_up_bg = 'rgba(0, 0, 0, 0.45)' if theme == 'dark' else 'rgba(0, 0, 0, 0.12)'

        check('C1: строк ≥ 5, прошедших = %d (%s)' % (EXPECTED_PAST, theme),
              len(r['rows']) >= 5 and r['pastN'] == EXPECTED_PAST,
              (len(r['rows']), r['pastN']))
        past = [x for x in r['rows'] if x['past']]
        up = [x for x in r['rows'] if not x['past']]
        check('C2: тинты Task 380 живы (%s)' % theme,
              past and all(x['bg'] == exp_past_bg for x in past) and
              up and all(x['bg'] == exp_up_bg for x in up),
              [x['bg'] for x in r['rows'][:2]])

        # склейка соседних строк ОДНОГО срока: зазор ≤ 0.75px
        gaps = []
        for i in range(len(r['rows']) - 1):
            a, b = r['rows'][i], r['rows'][i + 1]
            if a['past'] == b['past']:
                gaps.append(abs(a['bottom'] - b['top']))
        check('C3: соседние строки одного срока СКЛЕЕНЫ (зазор ≤ 0.75px, %s)' % theme,
              len(gaps) >= 2 and max(gaps) <= 0.75, gaps)
        # стык прошедших/идущих существует (0 ≤ стык, ряды в порядке)
        if past and up:
            joint = past[-1]['bottom'] - up[0]['top']
            check('C4: СТЫК зон есть (прошедшие → идущие, %s)' % theme,
                  -0.75 <= joint <= 0.75, joint)

        # строки до КРАЁВ окна: ширина = clientWidth, края = границы окна
        wOk = all(abs(x['width'] - r['panelW']) <= 1.0 for x in r['rows'])
        lOk = all(abs(x['left'] - r['panelLeft'] - 1) <= 1.5 for x in r['rows'])
        rOk = all(abs(x['right'] - r['panelRight'] + 1) <= 1.5 for x in r['rows'])
        check('C5: строки до краёв окна (width=clientWidth, %s)' % theme,
              wOk and lOk and rOk,
              (r['rows'][0]['width'], r['panelW'], r['rows'][0]['left'], r['panelLeft']))

        # отступ первой строки от заголовка ≈ 5px (как прежде:
        # margin-bottom 2px заголовка + 3px; до Task 381 было 2px + gap 3px)
        if r.get('capBottom') is not None and r['rows']:
            dCap = r['rows'][0]['top'] - r['capBottom']
            check('C6: от заголовка до первой строки как прежде 5px (%s)' % theme,
                  4.0 <= dCap <= 6.0, dCap)

        # ---------- ЧАСТЬ 2: значок приколот при прокрутке ----------
        pin = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            var b = p.querySelector('.ws-bar-exp');
            if (!b) return { err: 'NO BTN' };
            var r0 = b.getBoundingClientRect().top;
            p.scrollTop = 120;
            return { r0: r0, btn: true, display: getComputedStyle(b).display,
                     hasPin: p._barExpPin === true };
        })()""")
        page.wait_for_timeout(150)
        r120 = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            var b = p.querySelector('.ws-bar-exp');
            return { top: b.getBoundingClientRect().top, st: p.scrollTop,
                     tr: b.style.transform };
        })()""")
        check('B1: программный скролл 120px — значок НА МЕСТЕ (%s)' % theme,
              'err' not in pin and abs(r120['top'] - pin['r0']) <= 1.0,
              (pin.get('r0'), r120['top'], r120['tr']))
        check('B2: transform = translateY(120px) (%s)' % theme,
              r120['tr'] == 'translateY(120px)', r120['tr'])
        check('B3: слушатель прикреплён 1 раз (флаг _barExpPin, %s)' % theme,
              pin.get('hasPin') is True, pin.get('hasPin'))

        # колесо мыши над окном — значок на месте
        box = page.locator('#wsEventsPanel').bounding_box()
        page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        page.mouse.wheel(0, 200)
        page.wait_for_timeout(150)
        rw = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            var b = p.querySelector('.ws-bar-exp');
            return { top: b.getBoundingClientRect().top, st: p.scrollTop };
        })()""")
        check('B4: колесо мыши +200 — значок НА МЕСТЕ (%s)' % theme,
              abs(rw['top'] - pin['r0']) <= 1.0, (pin.get('r0'), rw['top'], rw['st']))

        # прокрутка до конца и возврат в 0
        rmax = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            p.scrollTop = p.scrollHeight;
            var b = p.querySelector('.ws-bar-exp');
            return { top: b.getBoundingClientRect().top };
        })()""")
        page.wait_for_timeout(120)
        rmax2 = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            var b = p.querySelector('.ws-bar-exp');
            p.scrollTop = 0;
            return { top: b.getBoundingClientRect().top, st: 0,
                     tr: b.style.transform };
        })()""")
        page.wait_for_timeout(120)
        r0b = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            var b = p.querySelector('.ws-bar-exp');
            return { top: b.getBoundingClientRect().top, tr: b.style.transform };
        })()""")
        check('B5: у конца прокрутки значок НА МЕСТЕ (%s)' % theme,
              abs(rmax['top'] - pin['r0']) <= 1.0, (pin.get('r0'), rmax['top']))
        check('B6: возврат в 0 — значок НА МЕСТЕ, transform сброшен (%s)' % theme,
              abs(r0b['top'] - pin['r0']) <= 1.0 and r0b['tr'] in ('translateY(0px)', ''),
              (pin.get('r0'), r0b['top'], r0b['tr']))

        # окно норм: слушатель тоже прикреплён
        np = page.evaluate("""(function(){
            var p = document.getElementById('wsCalPanel');
            return { hasPin: p._barExpPin === true };
        })()""")
        check('B7: окно «Нормы» — слушатель прикреплён (%s)' % theme,
              np['hasPin'] is True, np)

        # раскрытие Task 378/379 живо (после прокруток!)
        page.locator('#wsEventsPanel .ws-bar-exp').click()
        page.wait_for_timeout(450)
        exp = page.evaluate("""(function(){
            var p = document.getElementById('wsEventsPanel');
            return { h: p.style.height, mb: p.style.marginBottom,
                     open: p.classList.contains('ws-bar-open'),
                     sh: p.scrollHeight, st: p.scrollTop };
        })()""")
        check('B8: раскрытие живо — высота = scrollHeight (%s)' % theme,
              exp['open'] and exp['h'] == str(exp['sh']) + 'px' and exp['st'] == 0,
              exp)
        check('B9: маржа бара 95−H — габарит бара не растёт (%s)' % theme,
              exp['mb'] == str(95 - exp['sh']) + 'px', exp['mb'])

        # ---------- ПИКСЕЛЬНЫЕ ПРУФЫ: окно мероприятий (РАСКРЫТО —
        # все строки в кадре; геометрия из ROWS_JS валидна: контент
        # не зависит от высоты окна, панель не двигалась) ----------
        # непрерывность зон: модальный цвет строки по горизонтали
        # (текст/точки отфильтрованы модой); стык одно-сроковых строк
        # = цвет зоны, НЕ фон окна; прошедшие СВЕТЛЕЕ идущих
        page.locator('#wsEventsPanel').screenshot(
            path='/tmp/t381-events-exp-%s.png' % theme)
        img = Image.open('/tmp/t381-events-exp-%s.png' % theme).convert('RGB')
        wP, hP = img.size
        winBg = parse_rgb(r['panelBg'])
        rowsG = r['rows']
        def pair_of(status):
            for i in range(len(rowsG) - 1):
                if rowsG[i]['past'] == status and rowsG[i + 1]['past'] == status:
                    return rowsG[i], rowsG[i + 1]
            return None, None
        def midY(rr):
            return int(round((rr['top'] + rr['bottom']) / 2 - r['panelTop']))
        def edgeY(rr):
            return int(round(rr['bottom'] - r['panelTop']))
        def col_at(y):
            if not (0 <= y < hP):
                return None
            return mode_color(img, 30, wP - 30, y)
        p1, p2 = pair_of(True)
        u1, u2 = pair_of(False)
        if p1 and u1:
            pm1, pm2 = col_at(midY(p1)), col_at(midY(p2))
            pe = col_at(edgeY(p1))
            um1, um2 = col_at(midY(u1)), col_at(midY(u2))
            ue = col_at(edgeY(u1))
            check('P1: непрерывность ПРОШЕДШИХ (стык = цвет, не фон окна; %s)' % theme,
                  pm1 and pm2 and pe and
                  dist(pm1, pm2) <= 10 and dist(pe, pm1) <= 14 and dist(pe, winBg) >= 15,
                  (pm1, pm2, pe, winBg))
            check('P2: непрерывность ИДУЩИХ-БУДУЩИХ (стык = цвет; %s)' % theme,
                  um1 and um2 and ue and
                  dist(um1, um2) <= 10 and dist(ue, um1) <= 14 and dist(ue, winBg) >= 15,
                  (um1, um2, ue, winBg))
            check('P3: прошедшие СВЕТЛЕЕ идущих (Δ≥20; %s)' % theme,
                  pm1 and um1 and dist(pm1, um1) >= 20, (pm1, um1))
            print('    пиксели %s: past %s→%s (стык %s), upcoming %s→%s (стык %s), окно %s' %
                  (theme, pm1, pm2, pe, um1, um2, ue, winBg))

        page.locator('#wsEventsPanel .ws-bar-exp').click()
        page.wait_for_timeout(450)

        # скриншот окна (свёрнуто, верх = светлее прошедшие, низ = темнее)
        page.locator('#wsEventsPanel').screenshot(
            path='/tmp/t381-events-%s.png' % theme)

        # ---------- ЧАСТЬ 1: итоги ----------
        page.locator('#wsTotalsBtn').click()
        page.wait_for_timeout(700)
        t = page.evaluate(TT_JS)
        exp_even = 'rgba(255, 255, 255, 0.09)' if theme == 'dark' else 'rgba(0, 0, 0, 0.07)'
        exp_hours = 'rgb(74, 199, 113)' if theme == 'dark' else 'rgb(29, 122, 55)'
        exp_over = 'rgb(224, 162, 60)' if theme == 'dark' else 'rgb(160, 106, 19)'
        exp_border = 'rgba(0, 0, 0, 0.3)' if theme == 'dark' else 'rgb(10, 15, 23)'
        check('A1: ячейки значений ПРОЗРАЧНЫЕ (%s)' % theme,
              'err' not in t and t['numBg'] == 'rgba(0, 0, 0, 0)', t.get('numBg'))
        check('A2: зебра чётных строк восстановлена (%s)' % theme,
              t.get('evenBg') == exp_even, t.get('evenBg'))
        check('A3: нечётные строки без фона (%s)' % theme,
              t.get('oddBg') == 'rgba(0, 0, 0, 0)', t.get('oddBg'))
        check('A4: «Часы» — базовая палитра темы (%s)' % theme,
              t.get('hoursC') == exp_hours, t.get('hoursC'))
        check('A5: «Переработка» — базовая палитра темы (%s)' % theme,
              t.get('overC') == exp_over, t.get('overC'))
        check('A6: линии шахматки Task 378 живы (%s)' % theme,
              t.get('numBorder') == exp_border, t.get('numBorder'))
        check('A7: нулей в ячейках итогов НЕТ (%s)' % theme,
              t.get('zeros') == 0, t.get('zeros'))
        if theme == 'light':
            check('A8: панель итогов светлой — #e9e7de (фон как до белого)',
                  t.get('panelBg') == 'rgb(233, 231, 222)', t.get('panelBg'))
            cell = page.evaluate("""(function(){
                var cells = document.querySelectorAll(
                    '.ws-grid tbody td.ws-cell');
                for (var i = 0; i < cells.length; i++) {
                    var s = getComputedStyle(cells[i]).backgroundColor;
                    if (s === 'rgb(255, 255, 255)') return true;
                }
                return false;
            })()""")
            check('A9: шахматка #FFFFFF (Task 379) не тронута', cell)
        # скриншот шторки итогов + геометрия строк для пиксельного пруфа
        ttGeo = page.evaluate("""(function(){
            var body = document.getElementById('wsTtBody');
            var t = body ? body.querySelector('.ws-tt-table') : null;
            if (!t) return { err: 'NO TABLE' };
            var trs = t.querySelectorAll('tbody tr');
            var out = { rows: [] };
            for (var i = 0; i < Math.min(3, trs.length); i++) {
                var rc = trs[i].getBoundingClientRect();
                out.rows.push({ top: rc.top, bottom: rc.bottom,
                                left: rc.left, right: rc.right });
            }
            var dr = document.querySelector('.ws-tt-drawer');
            var drc = dr.getBoundingClientRect();
            out.drTop = drc.top; out.drLeft = drc.left;
            return out;
        })()""")
        page.locator('.ws-tt-drawer').screenshot(
            path='/tmp/t381-totals-%s.png' % theme)

        # ---------- ПИКСЕЛЬНЫЙ ПРУФ: итоги без белого + зебра ----------
        if 'err' not in ttGeo and len(ttGeo['rows']) >= 2:
            imgT = Image.open('/tmp/t381-totals-%s.png' % theme).convert('RGB')
            r1, r2 = ttGeo['rows'][0], ttGeo['rows'][1]
            y1 = int(round((r1['top'] + r1['bottom']) / 2 - ttGeo['drTop']))
            y2 = int(round((r2['top'] + r2['bottom']) / 2 - ttGeo['drTop']))
            x0 = int(round(r1['left'] - ttGeo['drLeft'])) + 10
            x1 = int(round(r1['right'] - ttGeo['drLeft'])) - 10
            c1 = mode_color(imgT, x0, x1, y1)
            c2 = mode_color(imgT, x0, x1, y2)
            if theme == 'dark':
                exp_odd, exp_even = (14, 22, 33), (36, 43, 53)
            else:
                exp_odd, exp_even = (233, 231, 222), (217, 215, 206)
            check('P4: нечётная строка = фон панели (НЕ белый; %s)' % theme,
                  dist(c1, exp_odd) <= 8 and dist(c1, (255, 255, 255)) >= 20, c1)
            check('P5: чётная строка = зебра Task 322 (%s)' % theme,
                  dist(c2, exp_even) <= 9 and dist(c1, c2) >= 15, (c1, c2))
            print('    пиксели итогов %s: нечёт %s, чёт %s (ожид. %s / %s)' %
                  (theme, c1, c2, exp_odd, exp_even))
        check('Z: 0 JS-ошибок (%s)' % theme, len(js_errors) == 0, js_errors[:2])
        ctx.close()

    # ================= МОБАЙЛ 375 =================
    print('--- МОБАЙЛ 375 ---')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=2)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'mob')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2000)

    r = page.evaluate(ROWS_JS)
    gaps = []
    for i in range(len(r['rows']) - 1):
        a, b = r['rows'][i], r['rows'][i + 1]
        if a['past'] == b['past']:
            gaps.append(abs(a['bottom'] - b['top']))
    check('M1: строки мероприятий склеены (мобайл)',
          len(gaps) >= 2 and max(gaps) <= 0.75, gaps)
    check('M2: строки до краёв окна (мобайл)',
          all(abs(x['width'] - r['panelW']) <= 1.0 for x in r['rows']),
          (r['rows'][0]['width'], r['panelW']))

    pin = page.evaluate("""(function(){
        var p = document.getElementById('wsEventsPanel');
        var b = p.querySelector('.ws-bar-exp');
        if (!b) return { err: 'NO BTN' };
        return { r0: b.getBoundingClientRect().top };
    })()""")
    page.evaluate("document.getElementById('wsEventsPanel').scrollTop = 90")
    page.wait_for_timeout(150)
    r90 = page.evaluate("""(function(){
        var p = document.getElementById('wsEventsPanel');
        var b = p.querySelector('.ws-bar-exp');
        return { top: b.getBoundingClientRect().top, tr: b.style.transform };
    })()""")
    check('M3: прикол значка при прокрутке (мобайл)',
          'err' not in pin and abs(r90['top'] - pin['r0']) <= 1.5,
          (pin.get('r0'), r90['top']))

    page.locator('#wsTotalsBtn').click()
    page.wait_for_timeout(900)
    t = page.evaluate(TT_JS)
    check('M4: итоги — ячейки прозрачные, зебра есть (мобайл)',
          'err' not in t and t['numBg'] == 'rgba(0, 0, 0, 0)' and
          t['evenBg'] == 'rgba(0, 0, 0, 0.07)',
          (t.get('numBg'), t.get('evenBg')))
    page.screenshot(path='/tmp/t381-mobile.png', full_page=False)
    check('M5: 0 JS-ошибок (мобайл)', len(js_errors) == 0, js_errors[:2])
    ctx.close()
    browser.close()

print()
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
print('Сегодня: %s; ожидается прошедших строк: %d' % (TODAY_ISO, EXPECTED_PAST))
import sys
sys.exit(1 if FAIL else 0)
