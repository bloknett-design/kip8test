#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 454: browser-check — заявка: «В отчёте талонов ширину
# колонки "Должность" сделай по ширине большего текста в ней,
# что бы текст был в одну строку, ширину колонки "Ф.И.О" сделай
# по ширине колонки "Должность", а колонку "Роспись о получении"
# сделай уже на величину увеличения колонок "Ф.И.О" и
# "Должность". Высоту строк с работниками оставь шириной в две
# строки текста в них, а текст выравни по вертикали по центру.»
# КОНТЕКСТ (мок-сервер, порт 8976):
#   A: десктоп 1280 тёмная, Админ: приложение + «Талоны»
#      (чипы 12ч=3 / 8ч=5);
#   B: ЗАЯВКА — предпросмотр печати: динамический colgroup
#      (инлайн-ширины c3/c4 ×3 сетки, c7 width:auto), ширина N =
#      ceil(max(тексты должностей 11pt, шапка 10.5pt)) + 10 (в
#      границах 87..188), c3 == c4 == N, «Роспись» = ОСТАТОК
#      сетки и меняется ровно на прирост c3+c4 (убыль старых
#      18.2%+20%), все должности В ОДНУ строку (Range rects),
#      строка данных = 2 строки текста (2.5em ≈ 36.7px +
#      паддинги), vertical-align middle, PDF = 1 страница;
#   C: СТРЕСС — длинная должность («Электромонтёр по ремонту и
#      обслуживанию электрооборудования»): N = КАП 188px, ячейка
#      ровно ДВЕ строки (без вылезания), прочие — одна, PDF = 1
#      страница;
#   D: ФОЛБЭК — canvas недоступен (getContext → null): НЕТ
#      инлайн-ширин, классы .wst-c3/.wst-c4/.wst-c7 (проценты
#      Excel, как до Task 454), форма не сломана;
#   E: зритель (view) — кнопка «Талоны» скрыта, прямой URL —
#      редирект;
#   F: мобайл 375 — страница + предпросмотр с тем же
#      динамическим colgroup;
#   G: 0 JS-ошибок ×5 контекстов; скриншоты в
#      download/kip8test-task454/.
import datetime
import json
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8976
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
D = lambda day: '%04d-%02d-%02d' % (NOWY, NOWM, day)

SHOTS = '/home/z/my-project/download/kip8test-task454'
os.makedirs(SHOTS, exist_ok=True)

# Работники (основной сценарий): Чирков — ДВЕ категории (t12=1,
# t8=3 — дубликат должности не влияет на замер); Федосов —
# сменный t12=2; Петров — t8=2; Яковлев — без записей (0/0,
# fallback «8 часовые», должность УЧИТЫВАЕТСЯ в замере)
EMPLOYEES = [
  {'таб_номер': '0231', 'ФИО': 'Чирков В. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2023-05-11',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': D(1), 'дата_приёма': '2024-03-15',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер по КИПиА', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0955', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2023-11-05',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр 4 разряда', 'группа_допуска': 'III',
   'комментарий': ''},
  {'таб_номер': '0377', 'ФИО': 'Яковлев Я. Я.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2025-01-20',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '',
   'комментарий': ''},
]
# Стресс: Гусев — должность, замер которой БОЛЬШЕ капа 178px,
# но при 188px ложится РОВНО на 2 строки; Данилов — ПАТОЛОГИЯ
# (57 знаков → 3 строки): height в td — МИНИМУМ, строка
# ВЫРАСТАЕТ, данные НЕ обрезаются (перелива нет)
GUSEV = {'таб_номер': '0456', 'ФИО': 'Гусев Г. Г.', 'тип': 'дневной',
         'смена': '', 'шаблон_ротации': 0, 'старт_цикла': '',
         'дата_приёма': '2024-06-01', 'дата_увольнения': '', 'в_архиве': 0,
         'должность': 'Электромонтёр по ремонту и обслуживанию',
         'группа_допуска': 'IV',
         'комментарий': ''}
DANILOV = {'таб_номер': '0457', 'ФИО': 'Данилов Д. Д.', 'тип': 'дневной',
           'смена': '', 'шаблон_ротации': 0, 'старт_цикла': '',
           'дата_приёма': '2024-06-01', 'дата_увольнения': '',
           'в_архиве': 0,
           'должность': 'Электромонтёр по ремонту и обслуживанию '
                        'электрооборудования', 'группа_допуска': 'IV',
           'комментарий': ''}
EMPLOYEES_STRESS = EMPLOYEES + [GUSEV, DANILOV]

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE0B2', 'short': 'день 12ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'д', 'name': 'Переработка день', 'color': '#FFCDD2',
   'short': 'перер. день'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
]

ENTRIES = []
# Чирков: 3×Д8 (t8=3) + 1×Д (t12=1) — ОДНА должность в ОБЕИХ группах
for i in (1, 2, 3):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0231', 'статус': 'Д8',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
ENTRIES.append({'дата': D(4), 'таб_номер': '0231', 'статус': 'Д',
                'переработка': 0, 'праздник': 0, 'источник': 'авто'})
# Федосов (сменный): 2×Н → t12=2
for i in (1, 2):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0871', 'статус': 'Н',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
# Петров: 2×Д8 → t8=2
for i in (5, 6):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0955', 'статус': 'Д8',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
# Стресс: Гусев и Данилов по 2×Д8 → t8=2 у каждого
ENTRIES_STRESS = ENTRIES + [
    {'дата': D(8), 'таб_номер': '0456', 'статус': 'Д8', 'переработка': 0,
     'праздник': 0, 'источник': 'авто'},
    {'дата': D(9), 'таб_номер': '0456', 'статус': 'Д8', 'переработка': 0,
     'праздник': 0, 'источник': 'авто'},
    {'дата': D(10), 'таб_номер': '0457', 'статус': 'Д8', 'переработка': 0,
     'праздник': 0, 'источник': 'авто'},
    {'дата': D(11), 'таб_номер': '0457', 'статус': 'Д8', 'переработка': 0,
     'праздник': 0, 'источник': 'авто'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

VARIANT = {'longpos': False}
PASS = 0
FAIL = 0


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def api_response(action, body, editor=True):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': editor,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        emps = EMPLOYEES_STRESS if VARIANT['longpos'] else EMPLOYEES
        return {'ok': True, 'data': {'employees': emps}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': [], 'instrList': [],
                'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        ents = ENTRIES_STRESS if VARIANT['longpos'] else ENTRIES
        return {'ok': True, 'data': {'entries': [dict(e) for e in ents]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, editor=True, longpos=False):
    VARIANT['longpos'] = longpos
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t454-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        if body is None:
            body = {}
        resp = api_response(action, body, editor=editor)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t454-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


TALONS_JS = """(function(){
    var body = document.getElementById('wsTalonsBody');
    if (!body) return null;
    var chips = {};
    body.querySelectorAll('.wst-chip').forEach(function(ch){
        var t = ch.textContent.replace(/\\s+/g,' ').trim();
        var m = t.match(/^([^:]+):\\s*(.+)$/);
        if (m) chips[m[1]] = m[2];
    });
    var rows = [];
    body.querySelectorAll('.wst-table tbody tr').forEach(function(tr){
        rows.push(tr.textContent.replace(/\\s+/g,' ').trim());
    });
    return {chips: chips, nrows: rows.length};
})"""

PREV_JS = """(function(){
    var ov = document.getElementById('wsTalonsPrevModal');
    if (!ov) return null;
    var fr = ov.querySelector('iframe');
    return {srcdoc: fr ? fr.srcdoc : ''};
})"""

# Замеры в СТАНДАРТНОЙ странице (srcdoc → _standalone.html)
MEASURE_JS = """(function(){
    var out = {};
    var table = document.querySelector('table.wst-rep-table');
    if (!table) return null;
    out.tableW = Math.round(table.getBoundingClientRect().width * 10) / 10;
    var cols = table.querySelectorAll('col');
    out.colClasses = [];
    out.colStyles = [];
    cols.forEach(function(c){
        out.colClasses.push(c.className);
        out.colStyles.push(c.getAttribute('style') || '');
    });
    // первая строка ДАННЫХ (после строки-заголовка группы)
    var trs = table.querySelectorAll('tbody tr');
    var dataRow = null;
    for (var i = 0; i < trs.length; i++) {
        if (trs[i].className.indexOf('wst-r-group') === -1) {
            dataRow = trs[i]; break;
        }
    }
    if (!dataRow) return out;
    var tds = dataRow.querySelectorAll('td');
    out.cellW = [];
    for (var j = 0; j < tds.length; j++) {
        out.cellW.push(Math.round(tds[j].getBoundingClientRect().width * 10) / 10);
    }
    var cs = getComputedStyle(tds[0]);
    out.vAlign = cs.verticalAlign;
    out.tdH = Math.round(tds[0].getBoundingClientRect().height * 10) / 10;
    out.lineH = parseFloat(cs.lineHeight) || 0;
    // ячейки должностей: число СТРОК текста (Range rects) + высоты
    out.pos = [];
    document.querySelectorAll('td.wst-r-pos').forEach(function(td){
        var range = document.createRange();
        range.selectNodeContents(td);
        var rects = range.getClientRects();
        var lines = 0;
        for (var k = 0; k < rects.length; k++) {
            if (rects[k].width > 1) lines++;
        }
        out.pos.push({t: td.textContent.trim(), lines: lines,
                      h: Math.round(td.getBoundingClientRect().height * 10) / 10,
                      sw: td.scrollWidth, cw: td.clientWidth});
    });
    // канвас-замер тех же текстов + шапки (тот же движок)
    var cv = document.createElement('canvas');
    var ctx = cv.getContext('2d');
    function maxW(font, arr) {
        ctx.font = font;
        var m = 0;
        arr.forEach(function(t){
            var w = ctx.measureText(t).width;
            if (w > m) m = w;
        });
        return Math.round(m * 10) / 10;
    }
    out.valW = maxW('11pt Times New Roman, Times, serif',
                    out.pos.map(function(p){ return p.t; }));
    out.headW = maxW('10.5pt Times New Roman, Times, serif', ['Должность']);
    return out;
})"""


def open_talons_preview(page):
    page.click('.wst-print-btn')
    page.wait_for_timeout(1500)
    return page.evaluate(PREV_JS)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== A+B: десктоп 1280 тёмная, Админ — ЗАЯВКА =====
        print('=== Контекст A/B: десктоп тёмная — динамическая сетка печати ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось, график открыт',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))
        btn = page.evaluate("(function(){var b = document.getElementById(" +
                            "'wsTalonsBtn'); return b ? " +
                            "{v: !b.hidden && b.offsetParent !== null," +
                            " t: b.textContent.trim()} : null;})()")
        check('A2: кнопка «Талоны» видна (edit)', bool(btn and btn['v']), btn)
        page.click('#wsTalonsBtn')
        page.wait_for_timeout(1500)
        g = page.evaluate(TALONS_JS)
        check('A3: страница «Талоны» отрендерена (4 работника)',
              bool(g and g['nrows'] == 4), g)
        if g:
            check('A4: чипы 12ч=3 (Чирков 1 + Федосов 2) / 8ч=5 '
                  '(Чирков 3 + Петров 2)',
                  g['chips'].get('12 ч. талонов') == '3' and
                  g['chips'].get('8 ч. талонов') == '5', g['chips'])
        page.screenshot(path=SHOTS + '/01-talons-page.png')

        prev = open_talons_preview(page)
        check('B1: предпросмотр открыт, srcdoc не пуст',
              bool(prev and prev['srcdoc']))
        sd = prev['srcdoc'] if prev else ''
        check('B2: маркеры формы на месте',
              all(s in sd for s in ['>ОТЧЕТ<', '>12 часовые<', '>8 часовые<',
                                    'Игушов Н.В.', 'Котельникова И.А.',
                                    'Фензель В.П.', '(ф.и.о.)']))
        widths = re.findall(r'style="width:(\d+)px"', sd)
        check('B3: инлайн-ширины c3/c4 во ВСЕХ ТРЁХ сетках (таблица + '
              'ИТОГО + подписи) = 6 шт.',
              len(widths) == 6, widths)
        check('B4: c7 «Роспись» = width:auto во всех трёх сетках (×3)',
              sd.count('style="width:auto"') == 3,
              sd.count('style="width:auto"'))
        check('B5: все 6 ширин ОДИНАКОВЫЕ — «Ф.И.О.» шириной «Должности»',
              len(set(widths)) == 1, widths)
        check('B6: ИТОГО по группам: 12ч=3, 8ч=5',
              re.search(r'ИТОГО: 12 часовые</td><td class="wst-t-val">3</td>',
                        sd) is not None and
              re.search(r'8 часовые</td><td class="wst-t-val">5</td>',
                        sd) is not None)
        n_px = int(widths[0]) if widths else 0

        # standalone → точные замеры геометрии (file:// — как в
        # Task 449–451; http-вариант Task 452 ловил 404: SHOTS
        # вне корня мок-сервера, PDF-пруф был пустышкой)
        with open(SHOTS + '/_standalone.html', 'w',
                  encoding='utf-8') as f:
            f.write(sd)
        pg = ctx.new_page()
        pg.goto('file://' + SHOTS + '/_standalone.html')
        pg.emulate_media(media='print')
        pg.wait_for_timeout(600)
        m = pg.evaluate(MEASURE_JS)
        check('B7: таблица замерена', bool(m and m.get('cellW')), m)
        if m and m.get('cellW'):
            check('B8: ширина N >= замера самого широкого текста должностей '
                  '(запас на паддинги) — текст в одну строку',
                  n_px >= m['valW'], (n_px, m['valW']))
            check('B9: N >= шапки «Должность» (10.5pt)',
                  n_px >= m['headW'], (n_px, m['headW']))
            check('B10: N в границах сетки (>= 12% = 87px, <= капа 188px)',
                  87 <= n_px <= 188, n_px)
            check('B11: порядок колонок c1..c7 сохранён',
                  m['colClasses'] == ['wst-c1', 'wst-c2', 'wst-c3', 'wst-c4',
                                      'wst-c5', 'wst-c6', 'wst-c7'],
                  m['colClasses'])
            check('B12: эффективные ширины: «Ф.И.О.» == «Должность» == N '
                  '(±2px)', abs(m['cellW'][2] - n_px) <= 2 and
                  abs(m['cellW'][3] - n_px) <= 2, (m['cellW'], n_px))
            rest = sum(m['cellW'][0:6]) - m['cellW'][2] - m['cellW'][3]
            check('B13: «Роспись» = ОСТАТОК сетки (±2px)',
                  abs(m['cellW'][6] - (m['tableW'] - sum(m['cellW'][0:6])))
                  <= 2, (m['cellW'], m['tableW']))
            # заявка: «Роспись» уже ровно НА ВЕЛИЧИНУ ПРИРОСТА c3+c4
            old_c3c4 = 0.382 * m['tableW']
            old_c7 = 0.222 * m['tableW']
            grow = 2 * n_px - old_c3c4
            delta_c7 = old_c7 - m['cellW'][6]
            check('B14: изменение «Росписи» == приросту c3+c4 (±3px, '
                  'геометрия заявки)', abs(grow - delta_c7) <= 3,
                  (round(grow, 1), round(delta_c7, 1)))
            check('B15: ВСЕ должности — В ОДНУ строку (Range rects = 1)',
                  all(p['lines'] == 1 for p in m['pos']),
                  [(p['t'], p['lines']) for p in m['pos']])
            check('B16: высота строки данных = ДВЕ строки текста '
                  '(2.5em ≈ 36.7px + паддинги, НЕ 6мм)',
                  m['tdH'] >= 2 * m['lineH'] and 36 <= m['tdH'] <= 45,
                  (m['tdH'], m['lineH']))
            check('B17: текст по вертикали ПО ЦЕНТРУ (vertical-align: middle)',
                  m['vAlign'] == 'middle', m['vAlign'])
            check('B18: должность Яковлева (0/0) тоже в замере — «Инженер '
                  'по КИП и А» в отчёте',
                  any(p['t'] == 'Инженер по КИП и А' for p in m['pos']),
                  [p['t'] for p in m['pos']])
            check('B19: Чирков в ОБОИХ группах — должность НЕ задвоена в '
                  'замере (5 строк данных: 1+1+2+1)',
                  len(m['pos']) == 5, len(m['pos']))
        pg.screenshot(path=SHOTS + '/03-standalone-print.png')
        pg.pdf(path=SHOTS + '/talons-a4.pdf', format='A4',
               margin={'top': '12mm', 'bottom': '12mm',
                       'left': '10mm', 'right': '10mm'})
        pg.close()
        try:
            import pypdf
            rd = pypdf.PdfReader(SHOTS + '/talons-a4.pdf')
            n_pages = len(rd.pages)
            pdf_text = rd.pages[0].extract_text() or ''
        except Exception as e:
            n_pages = 'pypdf error: %s' % e
            pdf_text = ''
        check('B20: PDF-эквивалент = РОВНО 1 страница A4 с РЕАЛЬНОЙ '
              'формой (гвардия от 404-пустышки)',
              n_pages == 1 and 'Наименование предприятия' in pdf_text
              and 'Чирков' in pdf_text and 'ОТЧЕТ' in pdf_text,
              (n_pages, pdf_text[:80]))
        page.screenshot(path=SHOTS + '/02-preview.png')
        page.click('.wspprev-cancel')
        page.wait_for_timeout(400)
        check('G1: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
        ctx.close()

        # ===== C: стресс — длинная должность (кап 188px) =====
        print('=== Контекст C: стресс — длинная должность, кап ширины ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js2 = attach(page2, ctx2, 'dark', 'stress', longpos=True)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        page2.click('#wsTalonsBtn')
        page2.wait_for_timeout(1500)
        prev2 = open_talons_preview(page2)
        sd2 = prev2['srcdoc'] if prev2 else ''
        check('C1: предпросмотр (стресс) открыт, Гусев И Данилов в отчёте',
              bool(sd2) and 'Электромонтёр по ремонту и обслуживанию' in sd2
              and 'электрооборудования' in sd2)
        w2 = re.findall(r'style="width:(\d+)px"', sd2)
        check('C2: замер длинной должности > капа → ширина = 188px (все 6)',
              len(w2) == 6 and set(w2) == {'188'}, w2)
        with open(SHOTS + '/_standalone-stress.html', 'w',
                  encoding='utf-8') as f:
            f.write(sd2)
        pg2 = ctx2.new_page()
        pg2.goto('file://' + SHOTS + '/_standalone-stress.html')
        pg2.emulate_media(media='print')
        pg2.wait_for_timeout(600)
        m2 = pg2.evaluate(MEASURE_JS)
        check('C3: стресс-замер получен', bool(m2 and m2.get('pos')), None)
        if m2 and m2.get('pos'):
            gu = [p for p in m2['pos'] if p['t'] ==
                  'Электромонтёр по ремонту и обслуживанию']
            da = [p for p in m2['pos'] if 'электрооборудования' in p['t']]
            check('C4: Гусев (39 зн., замер > капа) — РОВНО ДВЕ строки '
                  'внутри высоты 2.5em',
                  len(gu) == 1 and gu[0]['lines'] == 2, gu)
            check('C5: ни у кого нет горизонтального перелива '
                  '(scrollWidth <= clientWidth)',
                  all(p['sw'] <= p['cw'] + 1 for p in m2['pos']),
                  [(p['t'][:25], p['sw'], p['cw']) for p in m2['pos']])
            check('C6: высота строки Гусева (2 стр.) — ТА ЖЕ, что у '
                  '1-строчных (±1px, 2.5em хватает)',
                  gu and abs(gu[0]['h'] - m2['tdH']) <= 1,
                  (gu[0]['h'] if gu else None, m2['tdH']))
            check('C7: прочие должности — по-прежнему одна строка',
                  all(p['lines'] == 1 for p in m2['pos']
                      if p['t'] not in ('Электромонтёр по ремонту и '
                                        'обслуживанию',) and
                      'электрооборудования' not in p['t']),
                  [(p['t'][:25], p['lines']) for p in m2['pos']])
            check('C8: Данилов (57 зн., ПАТОЛОГИЯ) — 3 строки: строка '
                  'ВЫРОСЛА (height = минимум), данные НЕ обрезаны '
                  '(высота >= 3 строки текста)',
                  len(da) == 1 and da[0]['lines'] == 3 and
                  da[0]['h'] >= 3 * m2['lineH'] - 1, (da, m2['lineH']))
        pg2.pdf(path=SHOTS + '/talons-a4-stress.pdf', format='A4',
                margin={'top': '12mm', 'bottom': '12mm',
                        'left': '10mm', 'right': '10mm'})
        pg2.close()
        try:
            import pypdf
            rd2 = pypdf.PdfReader(SHOTS + '/talons-a4-stress.pdf')
            n_pages2 = len(rd2.pages)
            pdf_text2 = rd2.pages[0].extract_text() or ''
        except Exception as e:
            n_pages2 = 'pypdf error: %s' % e
            pdf_text2 = ''
        check('C9: стресс PDF = 1 страница A4 с реальной формой '
              '(Гусев + Данилов в тексте)',
              n_pages2 == 1 and 'Гусев' in pdf_text2 and
              'Данилов' in pdf_text2 and
              'ОТЧЕТ' in pdf_text2,
              (n_pages2, pdf_text2[:80]))
        page2.screenshot(path=SHOTS + '/04-stress-preview.png')
        page2.click('.wspprev-cancel')
        page2.wait_for_timeout(300)
        check('G2: 0 JS-ошибок (стресс)', len(js2) == 0, js2[:3])
        ctx2.close()

        # ===== D: фолбэк — canvas недоступен =====
        print('=== Контекст D: фолбэк — canvas getContext → null ===')
        ctx3 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page3 = ctx3.new_page()
        js3 = attach(page3, ctx3, 'light', 'fallback')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2500)
        page3.click('#wsTalonsBtn')
        page3.wait_for_timeout(1500)
        # отключаем canvas ЗАРАНЕЕ печати (замер невозможен)
        page3.evaluate("HTMLCanvasElement.prototype.getContext = " +
                       "function(){ return null; }")
        prev3 = open_talons_preview(page3)
        sd3 = prev3['srcdoc'] if prev3 else ''
        check('D1: предпросмотр (фолбэк) открыт', bool(sd3))
        check('D2: НЕТ инлайн-ширин — канвас недоступен',
              'style="width:' not in sd3,
              len(re.findall(r'style="width:\d+px"', sd3)))
        check('D3: колы с классами (проценты Excel, как до Task 454)',
              sd3.count('<col class="wst-c3">') == 3 and
              sd3.count('<col class="wst-c7">') == 3)
        check('D4: форма не сломана (маркеры + данные)',
              all(s in sd3 for s in ['>ОТЧЕТ<', '>12 часовые<',
                                     'Чирков В. А.', 'Слесарь по КИП и А']))
        page3.screenshot(path=SHOTS + '/05-fallback.png')
        page3.click('.wspprev-cancel')
        page3.wait_for_timeout(300)
        check('G3: 0 JS-ошибок (фолбэк)', len(js3) == 0, js3[:3])
        ctx3.close()

        # ===== E: зритель (view без edit) =====
        print('=== Контекст E: зритель — гейты ===')
        ctx4 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page4 = ctx4.new_page()
        js4 = attach(page4, ctx4, 'dark', 'viewer', editor=False)
        page4.goto('http://localhost:%d/index.html' % PORT)
        page4.wait_for_timeout(2500)
        page4.evaluate("navigateTo('work-schedule')")
        page4.wait_for_timeout(2000)
        btn4 = page4.evaluate("(function(){var b = document.getElementById(" +
                              "'wsTalonsBtn'); return !b ? null : " +
                              "(b.offsetParent !== null);})()")
        check('E1: зрителю кнопка «Талоны» СКРЫТА',
              btn4 is False or btn4 is None, btn4)
        page4.evaluate("navigateTo('ws-talons')")
        page4.wait_for_timeout(800)
        active = page4.evaluate("(function(){var p = document.getElementById(" +
                                "'page-ws-talons'); return p ? " +
                                "p.classList.contains('active') : false;})()")
        check('E2: прямой URL — редирект, страница не активна',
              active is False)
        check('G4: 0 JS-ошибок (зритель)', len(js4) == 0, js4[:3])
        ctx4.close()

        # ===== F: мобайл 375 =====
        print('=== Контекст F: мобайл 375 — печать с динамической сеткой ===')
        ctx5 = browser.new_context(viewport={'width': 375, 'height': 812})
        page5 = ctx5.new_page()
        js5 = attach(page5, ctx5, 'light', 'mobile')
        page5.goto('http://localhost:%d/index.html' % PORT)
        page5.wait_for_timeout(2500)
        page5.evaluate("navigateTo('work-schedule')")
        page5.wait_for_timeout(2000)
        page5.evaluate("WorkSchedule.openTalonsPage()")
        page5.wait_for_timeout(1200)
        g5 = page5.evaluate(TALONS_JS)
        check('F1: мобайл — страница «Талоны» отрендерена (чипы 3/5)',
              bool(g5 and g5['chips'].get('12 ч. талонов') == '3' and
              g5['chips'].get('8 ч. талонов') == '5'),
              g5['chips'] if g5 else None)
        prev5 = open_talons_preview(page5)
        sd5 = prev5['srcdoc'] if prev5 else ''
        w5 = re.findall(r'style="width:(\d+)px"', sd5)
        check('F2: мобайл — предпросмотр с той же динамической сеткой '
              '(6 инлайн-ширин, все равны десктопной)',
              len(w5) == 6 and n_px > 0 and set(w5) == {str(n_px)},
              (w5, n_px))
        page5.screenshot(path=SHOTS + '/06-mobile.png')
        check('G5: 0 JS-ошибок (мобайл)', len(js5) == 0, js5[:3])
        ctx5.close()

        browser.close()
    print('\n=== Итог: %d/%d (пас/фал) ===' % (PASS, PASS + FAIL))
    return 0 if FAIL == 0 else 1


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    import threading
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
