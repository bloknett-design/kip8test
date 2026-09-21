#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 387: browser-check — заявка: (1) панель «Обозначения» плавно
# разворачивается шире — до 500px — с подробными наименованиями
# кодов и секцией пояснений; (2) списки выбора кодов дней и
# мероприятий — правки в описании и последовательность по группам
# (16 кодов заявки); (3) пояснения: три удалены, «Рамка 2px…» →
# «Красная рамка… (пример - 24*)»; (4) «Выходной» — точка убрана:
# пустая ячейка белого цвета в списках И в шахматке.
# Мок справочника имитирует «СТАРЫЙ» лист (порядок Task 298,
# короткие имена, «.»-выходной) — нормализация должна показать
# НОВЫЙ порядок по группам и ПОЛНЫЕ наименования заявки.
# ДЕСКТОП 1280 (тёмная, Админ):
#   A   загрузка; B график + кнопка «Обозначения»;
#   C   шторка УЗКИЙ вид: ~190px, имена/пояснения скрыты, 16 кодов;
#   D   шеврон → ШИРОКИЙ вид: слот ~500px (было 400), имена ВИДИМЫ,
#       ПЕРВЫЙ код — Д8 (порядок по группам!), имя Д8 — полная
#       формулировка заявки («на час короче»), ОВ — «за ранее
#       отработанное время», «Выходной» — swatch-dot БЕЗ кода-«·»,
#       событийная секция начинается с ПР (после «Выходного»);
#   E   пояснения: удалённые отсутствуют, «Красная рамка…
#       (пример - 24*)» присутствует, бейдж/«сегодня» живы;
#   F   сворачивание → ~190px; G закрытие/Esc; H взаимоисключение;
#   I   ПОПАП ячейки: порядок Д8→…, «Выходной» — пустой код+имя,
#       легаси-«.»-ячейка подсвечивает строку «Выходного»;
#   J   select «Дополнительно…»: «— выходной —» первый, без «·»,
#       канонические наименования;
#   K   СЕТКА: «.»-ячейка — класс ws-dot-code, ПУСТОЙ центр (без
#       «·»), фон темы — «в шахматке должно отображаться так же»;
#   L   0 JS-ошибок.
# МОБАЙЛ 375 (светлая, Админ):
#   M   «Обозначения» → страница #page-ws-legend: имена/пояснения,
#       «Выходной»-строка, свотч БЕЛЫЙ (#FFFFFF, светлая тема),
#       шеврон «Назад»; N 0 JS-ошибок.
# Порт 8998 (запуск: python3 -m http.server 8998 &).
import datetime, json
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month

EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': 'бригада А'},
  {'таб_номер': '023', 'ФИО': 'Пётр Петров', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
VACATIONS = [
  {'id': 201, 'таб_номер': '017', 'часть': 1,
   'дата_начала': '%04d-%02d-01' % (Y, M), 'дата_окончания': '%04d-%02d-10' % (Y, M),
   'дней': 10, 'комментарий': 'лето'},
]
TRAININGS = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж', 'тема': 'Целевой инструктаж',
   'дата_начала': '%04d-%02d-10' % (Y, M), 'дата_окончания': '%04d-%02d-10' % (Y, M),
   'длительность_дней': 1, 'комментарий': ''},
]
# «СТАРЫЙ» лист: порядок строк Task 298 (Д раньше Д8), КОРОТКИЕ
# имена, «.»-код выходного — нормализация Task 387 обязана
# переставить по группам заявки и подставить ПОЛНЫЕ наименования
CODES = [
  {'code': 'Д',    'name': 'День (12-час, 7:30–19:30)', 'color': '#FFE082'},
  {'code': 'Д8',   'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4'},
  {'code': 'Д7,2', 'name': 'День 7,2-час (пятн./предпраздн.)', 'color': '#FFF9C4'},
  {'code': 'Н',    'name': 'Ночь (12-час, 19:30–7:30)', 'color': '#B0BEC5'},
  {'code': 'д',    'name': 'День в вых./праздник', 'color': '#FFD54F'},
  {'code': 'н',    'name': 'Ночь в вых./праздник', 'color': '#78909C'},
  {'code': 'ОТ',   'name': 'Отпуск ежегодный основной', 'color': '#ECEFF1'},
  {'code': 'У',    'name': 'Учебный отпуск', 'color': '#80CBC4'},
  {'code': 'ОВ',   'name': 'Отгул (оплачиваемый)', 'color': '#C5E1A5'},
  {'code': 'Б',    'name': 'Больничный', 'color': '#F8BBD0'},
  {'code': 'ПР',   'name': 'Прогул', 'color': '#EF5350'},
  {'code': 'И',    'name': 'Инструктаж', 'color': '#B3E5FC'},
  {'code': 'ОБ',   'name': 'Обучение', 'color': '#D1C4E9'},
  {'code': 'ПЗ',   'name': 'Проверка знаний', 'color': '#FFCDD2'},
  {'code': '*',    'name': 'Примечание (с комментарием)', 'color': '#FFAB91'},
  {'code': '.',    'name': 'Выходной, плановый выходной день', 'color': '#CFD8DC'}
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
# 2-я запись — легаси-«.» (плановый выходной, источник «руч»):
# ячейка обязана выглядеть ПУСТОЙ белой (класс ws-dot-code, без «·»)
ENTRIES = [
  {'id': 1, 'дата': '%04d-%02d-05' % (Y, M), 'таб_номер': '017', 'статус': 'Д',
   'источник': 'авто', 'переработка': 0, 'праздник': 0},
  {'id': 2, 'дата': '%04d-%02d-06' % (Y, M), 'таб_номер': '017', 'статус': '.',
   'источник': 'руч', 'переработка': 0, 'праздник': 0},
]

API_CALLS = []

def mock_response(action, body, viewer=False):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ' if not viewer else 'КИП ИОС дежурный'}}
    if action == 'getMyAccess':
        perms = ({'workschedule.view': True, 'workschedule.edit': True}
                 if not viewer else
                 {'workschedule.view': True, 'workschedule.edit': False,
                  'workschedule.view.min': False})
        return {'ok': True, 'data': {'role': 'Админ' if not viewer else 'КИП ИОС дежурный',
                'found': True, 'permissions': perms}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        inc = bool(body and body.get('includeArchived'))
        emps = EMPLOYEES if inc else [e for e in EMPLOYEES if not e['в_архиве']]
        return {'ok': True, 'data': {'employees': emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': [v for v in VACATIONS]}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action in ('workSchedule.updateEmployee', 'workSchedule.updateVacation',
                  'workSchedule.deleteVacation', 'workSchedule.addTraining',
                  'workSchedule.deleteTraining', 'workSchedule.addEmployee',
                  'workSchedule.dismissEmployee', 'workSchedule.setManualEntry',
                  'workSchedule.deleteEntry', 'workSchedule.generateMonth'):
        API_CALLS.append((action, dict(body or {})))
        return {'ok': True, 'data': {'ok': True}}
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

def attach(page, ctx, theme, tag, viewer=False):
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
                      body=json.dumps(mock_response(action, body, viewer),
                                      ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t387-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t387-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors

# состояние шторки «Обозначения» + нормализованный список кодов
LEGEND_JS = """(function(){
    var d = document.getElementById('wsLegendDrawer');
    var b = document.getElementById('wsLegendBtn');
    var chv = document.getElementById('wsLgChv');
    var body = document.getElementById('wsLegendBody');
    var rows = body ? body.querySelectorAll('.ws-lg-item') : [];
    var first = body ? body.querySelector('.ws-lg-name') : null;
    var notesec = body ? body.querySelector('.ws-lg-notesec') : null;
    var r = d.getBoundingClientRect();
    var codes = [];
    for (var i = 0; i < rows.length; i++) {
        var c = rows[i].querySelector('.ws-lg-code');
        var sw = rows[i].querySelector('.ws-lg-swatch');
        codes.push({
            code: c ? c.textContent : '',
            dotSw: !!(sw && sw.className.indexOf('ws-lg-swatch-dot') !== -1),
            bg: sw ? getComputedStyle(sw).backgroundColor : ''
        });
    }
    return {
        pressed: b ? b.getAttribute('aria-pressed') : 'x',
        slot: Math.round(r.width),
        right: Math.round(r.right),
        chvHidden: chv ? chv.hidden : true,
        chvPressed: chv ? chv.getAttribute('aria-pressed') : 'x',
        nameVisible: !!(first && first.offsetParent),
        nameTxt: first ? first.textContent : '',
        notesVisible: !!(notesec && notesec.offsetParent),
        notesTxt: notesec ? notesec.textContent : '',
        nRows: rows.length,
        codes: codes
    };
})()"""

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная, Админ =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'admin')

    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title === 'КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(3000)
    check('B1: график открыт, сетка отрисована',
          page.evaluate("!!document.querySelector('#page-work-schedule .ws-grid') && " +
                        "document.querySelectorAll('td.ws-emp-col[data-tab]').length >= 2"))
    check('B2: кнопка «Обозначения» в баре',
          page.evaluate("var b=document.getElementById('wsLegendBtn');" +
                        "!!b && b.textContent === 'Обозначения'"))

    # ---------- C: шторка — УЗКИЙ вид ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(700)
    lg = page.evaluate(LEGEND_JS)
    check('C1: шторка открыта (aria-pressed=true)', lg['pressed'] == 'true', lg['pressed'])
    check('C2: СОКРАЩЁННЫЙ вид — слот ~190px', 180 <= lg['slot'] <= 200, lg['slot'])
    check('C3: наименования кодов СКРЫТЫ', not lg['nameVisible'])
    check('C4: пояснения СКРЫТЫ', not lg['notesVisible'])
    check('C5: шеврон #wsLgChv виден', not lg['chvHidden'])
    check('C6: 16 строк-кодов (полный справочник)', lg['nRows'] == 16, lg['nRows'])

    # ---------- D: шеврон → ШИРОКИЙ вид (до 500px) ----------
    page.click('#wsLgChv')
    page.wait_for_timeout(700)
    lgw = page.evaluate(LEGEND_JS)
    check('D1: разворот — слот ~500px (было 400)',
          490 <= lgw['slot'] <= 510, lgw['slot'])
    check('D2: панель у правого края, наименования ВИДИМЫ',
          lgw['right'] == 1280 and lgw['nameVisible'])
    # ПОРЯДОК по группам: первый — Д8 (не «Д» листа!), затем Д7,2, Д, Н…
    seq = [c['code'] for c in lgw['codes']]
    check('D3: порядок по группам — Д8 первым (нормализация)',
          seq[0] == 'Д8' and seq[1] == 'Д7,2' and seq[2] == 'Д' and seq[3] == 'Н', seq[:5])
    check('D4: «Выходной» на 11-й позиции дня (после Б)',
          seq[10] == '' and seq[9] == 'Б', seq[8:12])
    check('D5: события после «Выходного»: ПР → И → ОБ → ПЗ → *',
          seq[11:16] == ['ПР', 'И', 'ОБ', 'ПЗ', '*'], seq[11:16])
    check('D6: имя Д8 — ПОЛНАЯ формулировка заявки («на час короче»)',
          'на час короче' in lgw['nameTxt'] and '8-часовая смена (с 7:30 до 16:30)' in lgw['nameTxt'],
          lgw['nameTxt'])
    check('D7: имя Д8 — НЕ листовое («День 8-час» заменено)',
          'День 8-час (' not in lgw['nameTxt'], lgw['nameTxt'])
    wykh = lgw['codes'][10]
    check('D8: «Выходной» — свотч ws-lg-swatch-dot, код ПУСТ (без «·»)',
          wykh['dotSw'] and wykh['code'] == '', wykh)
    body_txt = page.evaluate("document.getElementById('wsLegendBody').textContent")
    check('D9: имя «Выходного» — «Выходной, плановый выходной день»',
          'Выходной, плановый выходной день' in body_txt)
    check('D10: ОВ — «за ранее отработанное время, без содержания»',
          'за ранее отработанное время, без содержания' in body_txt)
    check('D11: точки «·» в шторке НЕТ',
          '·' not in body_txt)
    page.screenshot(path='/tmp/t387-proof-legend-wide-500.png', full_page=False)

    # ---------- E: пояснения (Task 387: −3, «красная рамка») ----------
    notes = lgw['notesTxt']
    check('E1: «Код мероприятия ставится в угол ячейки…» УДАЛЕНО',
          'Код мероприятия ставится' not in notes)
    check('E2: «В отпусках: 12 дней (−2 праздн.)…» УДАЛЕНО (ст. 120/125 ТК РФ)',
          'ст. 120 ТК РФ' not in notes and 'ст. 125 ТК РФ' not in notes and
          'вычтены праздники' not in notes)
    check('E3: «Зебра строк… перекрестье…» УДАЛЕНО',
          'Зебра строк' not in notes and 'перекрестье' not in notes)
    check('E4: «Красная рамка вокруг группы ячеек — выходные и праздники; «*» у числа (пример - 24*)…»',
          'Красная рамка вокруг группы ячеек' in notes and '(пример - 24*)' in notes)
    check('E5: «Рамка 2px» не осталось',
          'Рамка 2px' not in notes)
    check('E6: живые пояснения — бейдж смены и «сегодня»',
          'плановая смена по циклу' in notes and 'сегодняшняя дата' in notes)

    # ---------- F: сворачивание обратно ----------
    page.click('#wsLgChv')
    page.wait_for_timeout(700)
    lgn = page.evaluate(LEGEND_JS)
    check('F1: свёрнута — слот ~190px, имена скрыты',
          180 <= lgn['slot'] <= 200 and not lgn['nameVisible'], lgn['slot'])

    # ---------- G: закрытие/Esc ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)
    check('G1: закрыта повторным кликом', page.evaluate(LEGEND_JS)['pressed'] == 'false')
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)
    check('G2: Esc закрыл шторку', page.evaluate(LEGEND_JS)['pressed'] == 'false')

    # ---------- H: взаимоисключение с итогами ----------
    page.click('#wsLegendBtn')
    page.wait_for_timeout(600)
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(900)
    check('H1: открытие итогов закрыло «Обозначения»',
          page.evaluate(LEGEND_JS)['pressed'] == 'false' and
          page.evaluate("document.getElementById('page-work-schedule').classList.contains('ws-tt-open')"))
    page.click('#wsTotalsBtn')
    page.wait_for_timeout(600)

    # ---------- I: попап ячейки — «Выходной» без точки, порядок ----------
    # ячейка 6-го числа (легаси-«.», ручная): строка «Выходного» АКТИВНА
    dot_cell = 'tr:has(td.ws-emp-col[data-tab="017"]) td.ws-cell[data-day="6"]'
    page.click(dot_cell)
    page.wait_for_timeout(600)
    pop = page.evaluate("""(function(){
        var pp = document.getElementById('wsCellPopup');
        if (!pp) return { open: false };
        var rows = pp.querySelectorAll('.ws-popup-row');
        var codes = [];
        for (var i = 0; i < rows.length; i++) {
            var c = rows[i].querySelector('.ws-popup-code');
            var sw = rows[i].querySelector('.ws-popup-swatch');
            codes.push({
                code: c ? c.textContent : '',
                active: rows[i].className.indexOf('ws-popup-active') !== -1,
                dotSw: !!(sw && sw.className.indexOf('ws-swatch-dot') !== -1),
                name: (rows[i].querySelector('.ws-popup-name') || {}).textContent || ''
            });
        }
        return { open: pp.classList.contains('active'), codes: codes,
                 txt: pp.textContent };
    })()""")
    check('I1: попап открыт', pop['open'])
    pseq = [c['code'] for c in pop['codes'] if c['code'] or c['dotSw']]
    check('I2: порядок попапа — Д8 первым (после Б — «Выходной»)',
          pseq[0] == 'Д8' and pseq[10] == '' and pseq[9] == 'Б', pseq[:12])
    wykh_row = [c for c in pop['codes'] if c['dotSw']]
    check('I3: «Выходной» — свотч ws-swatch-dot, ПУСТОЙ код, имя',
          len(wykh_row) == 1 and wykh_row[0]['code'] == '' and
          'Выходной, плановый выходной день' in wykh_row[0]['name'], wykh_row)
    check('I4: легаси-«.» ячейка подсвечивает строку «Выходного»',
          wykh_row[0]['active'])
    check('I5: метки «·» в КОДАХ попапа НЕТ (разделитель «·» титула не в счёт)',
          all('·' not in c['code'] for c in pop['codes']))
    check('I6: имя Д8 — полная формулировка («на час короче»)',
          any('на час короче' in c['name'] for c in pop['codes']))
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)

    # ---------- J: select «Дополнительно…» ----------
    d5 = 'tr:has(td.ws-emp-col[data-tab="017"]) td.ws-cell[data-day="5"]'
    page.click(d5)
    page.wait_for_timeout(400)
    page.click("#wsCellPopup .ws-popup-row.ws-popup-more:last-child")
    page.wait_for_timeout(700)
    sel = page.evaluate("""(function(){
        var s = document.getElementById('wsCellStatus');
        if (!s) return { open: false };
        var opts = [];
        for (var i = 0; i < s.options.length; i++) {
            opts.push(s.options[i].value + '|' + s.options[i].textContent);
        }
        return { open: true, first: s.options[0] ? s.options[0].textContent : '',
                 empty: s.value === '', opts: opts };
    })()""")
    check('J1: шит «Дополнительно…» открыт, select заполнен', sel['open'])
    check('J2: первая опция — «— выходной —»', sel['first'] == '— выходной —', sel['first'])
    check('J3: опции «Выходного»-дубля НЕТ (одна пустая value)',
          len([o for o in sel['opts'] if o.split('|')[0] == '']) == 1)
    check('J4: опции без «·», канонические наименования',
          all('·' not in o for o in sel['opts']) and
          any('на час короче' in o for o in sel['opts']) and
          any('за ранее отработанное время' in o for o in sel['opts']))
    page.click('#wsCellSheet .flow-input-cancel')
    page.wait_for_timeout(500)

    # ---------- K: сетка — «.»-ячейка = ПУСТАЯ белая ----------
    grid = page.evaluate("""(function(){
        var td = document.querySelector('tr:has(td.ws-emp-col[data-tab="017"]) td.ws-cell[data-day="6"]');
        if (!td) return { found: false };
        return { found: true, dot: td.classList.contains('ws-dot-code'),
                 empty: td.classList.contains('ws-status-empty'),
                 txt: td.textContent.trim(), bg: getComputedStyle(td).backgroundColor };
    })()""")
    check('K1: «.»-ячейка найдена', grid['found'])
    check('K2: классы ws-dot-code + ws-status-empty (пустая ячейка)',
          grid['dot'] and grid['empty'], grid)
    check('K3: центр ПУСТ — точки «·» в ячейке НЕТ («в шахматке так же»)',
          grid['txt'] == '', repr(grid['txt']))
    # тёмная тема: фон ячеек-дней #eef0f2 с фильтром brightness(0.88)
    check('K4: фон — «пустая ячейка» (не цвет листа #CFD8DC)',
          grid['bg'] not in ('rgb(207, 216, 220)',), grid['bg'])
    page.screenshot(path='/tmp/t387-proof-grid-dot-cell.png', full_page=False)

    check('L: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: мобайл 375, светлая, Админ =================
    ctx2 = browser.new_context(viewport={'width': 375, 'height': 700})
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'mobile')

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(3000)
    page2.click('#wsLegendBtn')
    page2.wait_for_timeout(700)
    lm = page2.evaluate("""(function(){
        var d = document.getElementById('wsLegendDrawer');
        var pg = document.getElementById('page-ws-legend');
        var body = document.getElementById('wsLgPageBody');
        var rows = body ? body.querySelectorAll('.ws-lg-item') : [];
        var first = body ? body.querySelector('.ws-lg-name') : null;
        var notesec = body ? body.querySelector('.ws-lg-notesec') : null;
        var wykh = body ? body.querySelector('.ws-lg-swatch-dot') : null;
        var r = pg.getBoundingClientRect();
        var codes = [];
        for (var i = 0; i < rows.length; i++) {
            var c = rows[i].querySelector('.ws-lg-code');
            codes.push(c ? c.textContent : '');
        }
        return { pageActive: pg.classList.contains('active'),
                 title: pg.querySelector('.page-inline-header-title').textContent,
                 drawerDisplay: getComputedStyle(d).display,
                 nameVisible: !!(first && first.offsetParent),
                 nameTxt: first ? first.textContent : '',
                 notesVisible: !!(notesec && notesec.offsetParent),
                 notesTxt: notesec ? notesec.textContent : '',
                 nRows: rows.length, codes: codes,
                 wykhBg: wykh ? getComputedStyle(wykh).backgroundColor : '',
                 inView: r.left >= 0 && r.right <= 375 && r.top >= 0,
                 txt: body ? body.textContent : '' };
    })()""")
    check('M1: мобайл: «Обозначения» → СТРАНИЦА #page-ws-legend',
          lm['pageActive'] and lm['drawerDisplay'] == 'none')
    check('M2: наименования и пояснения ВИДИМЫ',
          lm['nameVisible'] and lm['notesVisible'])
    check('M3: 16 строк, порядок по группам (Д8 первый)',
          lm['nRows'] == 16 and lm['codes'][0] == 'Д8', (lm['nRows'], lm['codes'][:3]))
    check('M4: «Выходной» — ПУСТОЙ код, свотч БЕЛЫЙ (#FFFFFF светл. тема)',
          lm['codes'][10] == '' and lm['wykhBg'] == 'rgb(255, 255, 255)',
          (lm['codes'][10], lm['wykhBg']))
    check('M5: пояснение «(пример - 24*)», удалённых нет',
          '(пример - 24*)' in lm['notesTxt'] and 'ст. 120 ТК РФ' not in lm['notesTxt'] and
          'Зебра строк' not in lm['notesTxt'])
    check('M6: точки «·» на странице НЕТ', '·' not in lm['txt'])
    check('M7: страница в границах вьюпорта', lm['inView'])
    page2.screenshot(path='/tmp/t387-proof-mobile-legend.png', full_page=False)

    page2.click('#page-ws-legend .page-inline-header-chevron')
    page2.wait_for_timeout(700)
    back = page2.evaluate("""(function(){
        return { legend: document.getElementById('page-ws-legend').classList.contains('active'),
                 ws: document.getElementById('page-work-schedule').classList.contains('active') };
    })()""")
    check('M8: шеврон «Назад» вернул на табель', not back['legend'] and back['ws'], back)

    check('N: 0 JS-ошибок (мобайл)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    browser.close()

print()
print('Итого: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
