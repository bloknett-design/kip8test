#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 440: browser-check — заявка пользователя (3 части):
#   1) «Во всех трёх представлениях печати коды справа от
#      мероприятий на расстоянии друг от друга 10px»;
#   2) «В картах работников, в блоке Повторные инструктажи и
#      периодическая проверка знаний не активна кнопка просмотра
#      следующего года, если в таблице Инструктажи … есть записи
#      на следующий год…»;
#   3) «Проверь такой же функционал просмотра предыдущего или
#      следующего годов, при наличии записей в серверной таблице,
#      должен быть реализован в блоках Отпуска и Мероприятия».
# КОНТЕКСТЫ (мок-сервер, порт 8940):
#   1) десктоп 1280 тёмная, Админ — ГРАФИК РАБОТЫ → «Печать»:
#      - геометрия iframe: gap ряда wsp-bottom = 10px, расстояние
#        мероприятий→коды = 10px (±1px), коды справа;
#      - «Сохранить PDF» → График_работы_*.pdf (%PDF-1.4,
#        DCTDecode, 842×595, 1 стр., рендер-пруф);
#      - «Сохранить Excel» → .xlsx: «Коды:» s="8", код-строки
#        s="7", styles.xml indent="1" ×2, cellXfs 10, сетка s="9";
#      - регресс 439: ФИО+Тип в A, ширина A по тексту.
#   2) десктоп 1280 светлая, Админ — РАБОТНИКИ → карточка:
#      - инструктажи (fam 1): › АКТИВНА на Y (запись Y+1 —
#        баг-фикс), клик → год Y+1, запись видна; на Y+1 › погашена;
#      - мероприятия (fam 0): › активна (период до 15.01.Y+1),
#        клик → «Мероприятия · Y+1»;
#      - отпуска (fam 2, НОВОЕ): навигатор ‹год›; год Y + запись
#        Y; ‹/› активны; ‹ → архив (Y-1) с записью и днями;
#        › › → Y+1; границы погашены за пределами записей;
#      - пул: сервер получил listVacations по годам окна [Y-3..Y+3];
#      - независимость годов трёх блоков; 0 JS-ошибок.
#   3) мобайл 375 светлая — карточка: навигатор отпусков работает,
#      нет горизонтального переполнения; 0 JS-ошибок.
# + скриншот-пруфы в download/screenshots-task440/.
import datetime
import json
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8940
TODAY = datetime.date.today()
Y = TODAY.year
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)

def iso(y, m, d):
    return '%04d-%02d-%02d' % (y, m, d)

def fmt_ru(s):
    p = s.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
]

INSTR_LIST = [
  {'название': 'Повторный инструктаж по охране труда', 'вид': 'инструктаж',
   'периодичность': 6, 'основание': '', 'сокращение': 'Инстр. ОТ'},
]

CODES = [
  {'code': 'Д8', 'name': 'День, плановая дневная 8-часовая смена '
   '(с 7:30 до 16:30)', 'color': '#FFF9C4', 'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь, плановая ночная 12-часовая смена '
   '(с 19:30 до 7:30)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'д', 'name': 'День, плановая работа в выходные и праздники',
   'color': '#FFD54F', 'short': 'день в выходной'},
  {'code': 'ОТ', 'name': 'Отпуск, ежегодный основной оплачиваемый',
   'color': '#ECEFF1', 'short': 'отпуск'},
  {'code': '', 'name': 'Выходной, плановый выходной день',
   'color': '#EEF0F2', 'short': 'выходной'},
  {'code': 'И', 'name': 'Инструктаж, повторный по охране труда',
   'color': '#90CAF9', 'short': 'инструктаж'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]


def ev(i, tab, tip, tema, d1, d2=None, days=1, done=1):
    return {'id': i, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d1, 'дата_окончания': d2 or d1,
            'длительность_дней': days, 'комментарий': '',
            'дата_проведения': d1, 'выполнение': done,
            'просрочен': 0}


# записей СЛЕДУЮЩЕГО года — баг-кейс заявки (кнопка ›)
INSTR = [
    ev(600, '0871', 'инструктаж', 'Повторный инструктаж по охране труда',
       iso(Y - 2, 5, 10)),
    ev(601, '0871', 'инструктаж', 'Повторный инструктаж по охране труда',
       TODAY_ISO),
    ev(602, '0871', 'проверка_знаний', 'Периодическая проверка знаний '
       'по промбезопасности', iso(Y + 1, 4, 20)),
]
# мероприятия: запись Y-1 + ПЕРИОД ЧЕРЕЗ ГРАНИЦУ года (27.12 → 15.01.Y+1)
EVENTS = [
    ev(500, '0871', 'обучение', 'Обучение по промбезопасности',
       iso(Y - 1, 6, 15)),
    ev(501, '0871', 'обучение', 'Стажировка на РМП',
       iso(Y, 12, 27), iso(Y + 1, 1, 15), 20),
]

# отпуска ПО ГОДАМ (listVacations фильтрует по году запроса)
VAC_BY_YEAR = {
    Y - 1: [{'id': 1, 'таб_номер': '0871', 'часть': 1,
             'дата_начала': iso(Y - 1, 6, 2),
             'дата_окончания': iso(Y - 1, 6, 15), 'комментарий': ''}],
    Y:     [{'id': 2, 'таб_номер': '0871', 'часть': 2,
             'дата_начала': iso(Y, 7, 1),
             'дата_окончания': iso(Y, 7, 14), 'комментарий': ''}],
    Y + 1: [{'id': 4, 'таб_номер': '0871', 'часть': 3,
             'дата_начала': iso(Y + 1, 5, 5),
             'дата_окончания': iso(Y + 1, 5, 18), 'комментарий': ''}],
}
VAC_CALLS = []  # годы, запрошенные клиентом (пул _vacYearEnsure)


def fresh_entries():
    out = []
    dim = (datetime.date(TODAY.year, TODAY.month % 12 + 1, 1) -
           datetime.timedelta(days=1)).day
    for day in range(1, dim + 1):
        iso_ = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, day)
        if day <= 5:
            out.append({'дата': iso_, 'таб_номер': '0871', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
        if day == 6:
            out.append({'дата': iso_, 'таб_номер': '0871', 'статус': 'д',
                        'переработка': 1, 'праздник': 0, 'источник': 'руч'})
        if day == 9:
            out.append({'дата': iso_, 'таб_номер': '0871', 'статус': 'ОТ',
                        'переработка': 0, 'праздник': 0, 'источник': 'руч'})
    return out


ENTRIES = fresh_entries()

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task440'
os.makedirs(SHOTS, exist_ok=True)


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': True,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {
            'trainings': [dict(r) for r in INSTR + EVENTS
                          if r['дата_начала'][:4] == str(Y)],
            'instrList': [dict(x) for x in INSTR_LIST],
            'instrAll': [dict(r) for r in INSTR],
            'eventsAll': [dict(r) for r in EVENTS]}}
    if action == 'workSchedule.listVacations':
        yr = None
        if body:
            try:
                yr = int(body.get('year'))
            except Exception:
                yr = None
        VAC_CALLS.append(yr if yr is not None else 'None')
        vacs = [dict(v) for v in VAC_BY_YEAR.get(yr, [])]
        return {'ok': True, 'data': {'vacations': vacs}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in ENTRIES]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t440-%s');" % tag +
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
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t440-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# геометрия печатного листа в iframe предпросмотра
GEOM_JS = """(function(){
    var ov = document.getElementById('wsPrintPrevModal');
    if (!ov) return null;
    var f = ov.querySelector('.wspprev-frame');
    try {
        var d = f.contentDocument;
        var sheet = d && d.getElementById('wsPrintSheet');
        if (!sheet) return null;
        var bottom = sheet.querySelector('.wsp-bottom');
        var mev = sheet.querySelector('.wsp-mev');
        var leg = sheet.querySelector('.wsp-legend');
        if (!bottom || !mev || !leg) return {missing: true};
        var bs = d.defaultView.getComputedStyle(bottom);
        var mr = mev.getBoundingClientRect();
        var lr = leg.getBoundingClientRect();
        var sr = sheet.getBoundingClientRect();
        return {
            bottomDisplay: bs.display,
            bottomGap: bs.gap,
            mevRight: mr.right, legLeft: lr.left,
            mevTop: mr.top, legTop: lr.top,
            legLeftOff: leg.offsetLeft, mevLeftOff: mev.offsetLeft,
            mevW: mev.offsetWidth, legW: leg.offsetWidth,
            gapPx: lr.left - mr.right,
            sheetRight: sr.right, legRight: lr.right,
            legendTxt: leg.textContent.slice(0, 80),
            mevTxt: mev.querySelector('.wsp-mev-t').textContent
        };
    } catch (e) { return 'err: ' + e; }
})"""

# клик стрелки ‹/› в КОНКРЕТНОМ блоке карточки (по тексту заголовка)
NAV_CLICK_JS = """(function(blockText, dir){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf(blockText) !== -1) {
            var btns = cards[i].querySelectorAll('.ws-ynav-btn');
            for (var b = 0; b < btns.length; b++) {
                var isNext = btns[b].textContent.indexOf('›') !== -1;
                if ((dir === 'next') === isNext) { btns[b].click(); return true; }
            }
            return 'no-btn';
        }
    }
    return 'no-block';
})"""

# состояние навигатора блока: год в заголовке + погашенность стрелок
NAV_STATE_JS = """(function(blockText){
    var cards = document.querySelectorAll('.ws-wgrid2 .ws-wcard');
    for (var i = 0; i < cards.length; i++) {
        var t = cards[i].querySelector('.ws-whead-t');
        if (t && t.textContent.indexOf(blockText) !== -1) {
            var off = cards[i].querySelectorAll('.ws-ynav-off');
            var btns = cards[i].querySelectorAll('.ws-ynav-btn:not(.ws-ynav-off)');
            return {
                title: t.textContent.replace(/\\s+/g, ' ').trim().slice(0, 90),
                offLeft: !!cards[i].querySelector('.ws-ynav-off:first-child, .ws-ynav-off'),
                offCount: off.length,
                offTitles: Array.prototype.map.call(off, function(x){
                    return x.textContent.trim(); }),
                liveCount: btns.length,
                html: cards[i].innerHTML.slice(0, 4000)
            };
        }
    }
    return null;
})"""


def nav_state(page, block):
    return page.evaluate(
        '(' + NAV_STATE_JS + ')(%s)' % json.dumps(block, ensure_ascii=False))


def nav_click(page, block, direction):
    return page.evaluate(
        '(function(b, d){ return (' + NAV_CLICK_JS + ')(b, d); })(%s, %s)' %
        (json.dumps(block, ensure_ascii=False), json.dumps(direction)))


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== Контекст 1: десктоп 1280 тёмная, Админ — ПЕЧАТЬ =====
        print('=== Контекст 1: десктоп тёмная — печать (зазор 10px) ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                                  accept_downloads=True)
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'print')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        check('A1: график работы открыт (шахматка с данными)',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))

        page.click('#wsPrintBtn')
        page.wait_for_timeout(1500)
        check('B1: диалог предпросмотра открыт',
              page.evaluate("!!document.getElementById('wsPrintPrevModal')"))

        # --- геометрия: зазор ровно 10px (HTML-представление) ---
        page.wait_for_timeout(800)
        g = page.evaluate(GEOM_JS)
        check('C1: нижняя секция — flex-ряд',
              g and g['bottomDisplay'] == 'flex', g)
        check('C2: CSS gap ряда = 10px (прежде 6mm)',
              g and g['bottomGap'] == '10px', g and g['bottomGap'])
        check('C3: блок кодов СПРАВА от мероприятий',
              g and g['legLeftOff'] > g['mevLeftOff'] + g['mevW'] * 0.5, g)
        gap_px = g['gapPx'] if g else None
        check('C4: РАССТОЯНИЕ мероприятий→коды = 10px (±1px)',
              g and abs(gap_px - 10.0) <= 1.0, gap_px)
        check('C5: общая верхняя линия (±3px)',
              g and abs(g['legTop'] - g['mevTop']) <= 3, g)
        check('C6: заголовки секций на месте',
              g and 'Мероприятия' in g['mevTxt'] and
              'Коды' in g['legendTxt'], g)
        check('C7: коды следуют ЗА ТЕКСТОМ (не прижаты к правому '
              'краю листа): за кодами ≥ 60px пусто',
              g and (g['sheetRight'] - g['legRight']) >= 60,
              g and (g['sheetRight'] - g['legRight']))

        page.screenshot(path=SHOTS + '/01-print-dialog-gap10px.png')

        # --- PDF (10px = 7.5pt в раскладке) ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-pdf')
            dl = dl_info.value
            pdf_path = '/tmp/t440-graph.pdf'
            dl.save_as(pdf_path)
            raw = open(pdf_path, 'rb').read()
            check('D1: PDF скачан — имя',
                  dl.suggested_filename.startswith('График_работы_') and
                  dl.suggested_filename.endswith('.pdf'),
                  dl.suggested_filename)
            check('D2: PDF — %PDF-1.4 + %%EOF + DCTDecode',
                  raw[:8] == b'%PDF-1.4' and b'%%EOF' in raw[-40:] and
                  b'/DCTDecode' in raw, raw[:16])
            check('D3: PDF — MediaBox A4-альбомная',
                  b'MediaBox [0 0 842 595]' in raw)
            try:
                import fitz
                doc = fitz.open(pdf_path)
                check('D4: PDF — 1 страница', doc.page_count == 1,
                      doc.page_count)
                pg = doc.load_page(0)
                check('D5: PDF — страница 842×595 pt',
                      abs(pg.rect.width - 842) < 1 and
                      abs(pg.rect.height - 595) < 1,
                      (pg.rect.width, pg.rect.height))
                pg.get_pixmap(dpi=110).save(SHOTS + '/02-pdf-page1.png')
                check('D6: PDF — рендер снят (пруф зазора)', True)
            except ImportError:
                check('D4..D6: pymupdf недоступен (пропуск)', True)
        except Exception as e:
            check('D1..D6: сохранение PDF', False, str(e)[:230])

        # --- Excel: indent-стили кодов (зазор ~7px) ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-xlsx')
            dl = dl_info.value
            xlsx_path = '/tmp/t440-graph.xlsx'
            dl.save_as(xlsx_path)
            import zipfile
            z = zipfile.ZipFile(xlsx_path)
            sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
            styles = z.read('xl/styles.xml').decode('utf-8')
            check('E1: Excel скачан — имя .xlsx',
                  dl.suggested_filename.endswith('.xlsx'),
                  dl.suggested_filename)
            check('E2: «Коды:» — колонка D со стилем 8 (шапка + indent)',
                  re.search(r'<c r="D\d+" t="inlineStr" s="8">'
                            r'<is><t>Коды:</t></is></c>', sheet) is not None)
            check('E3: строка кода — стиль 7 (indent, зазор ~7px)',
                  re.search(r'<c r="D\d+" t="inlineStr" s="7">', sheet)
                  is not None, sheet[sheet.find('Мероприятия · '):
                                    sheet.find('Мероприятия · ') + 400])
            check('E4: styles.xml — indent="1" ровно ДВА (код + шапка)',
                  styles.count('indent="1"') == 2,
                  styles.count('indent="1"'))
            # cellXfs = 9 базовых + число уникальных цветов заливок
            # (базовые fills: none + gray125 + синяя шапка = 3)
            fills = styles.count('<fill>')
            colors_n = fills - 3
            m_cnt = re.search(r'<cellXfs count="(\d+)">', styles)
            check('E5: cellXfs count = 9 базовых + %d цветов = %d'
                  % (colors_n, 9 + colors_n),
                  m_cnt and int(m_cnt.group(1)) == 9 + colors_n,
                  (m_cnt and m_cnt.group(1), colors_n))
            check('E6: цветная ячейка сетки — s="9" (база сдвинута)',
                  re.search(r'<c r="B\d+" t="inlineStr" s="9">', sheet)
                  is not None or re.search(r's="9">', sheet) is not None,
                  'нет s=9')
            # регресс 439: ФИО + Тип и ширина по тексту
            check('E7: регресс 439 — ФИО + Тип в ячейке A',
                  re.search(r'Федосов А\. В\.\nсмена №1', sheet) is not None)
            check('E8: регресс 439 — ширина A по тексту',
                  '<col min="1" max="1" width="15"' in sheet or
                  re.search(r'<col min="1" max="1" width="1[4-9]"', sheet)
                  is not None)
        except Exception as e:
            check('E1..E8: сохранение Excel', False, str(e)[:230])

        page.click('.wspprev-close, .wspprev-cancel'
                   ) if page.evaluate(
            "!!document.querySelector('.wspprev-close, .wspprev-cancel')"
        ) else page.keyboard.press('Escape')
        page.wait_for_timeout(600)
        check('F1: JS-ошибок нет (контекст печати)', js_errors == [],
              js_errors[:3])
        ctx.close()

        # ===== Контекст 2: десктоп 1280 светлая — РАБОТНИКИ =====
        print('=== Контекст 2: десктоп светлая — карточка (годы блоков) ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'light', 'workers')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(1200)
        page.click(".ws-wtabs button:has-text('Федосов')")
        page.wait_for_timeout(1500)

        # --- инструктажи (fam 1): баг-кейс › при записи Y+1 ---
        ins = nav_state(page, 'Повторные инструктажи')
        check('G1: блок «Повторные инструктажи… · %d»' % Y,
              ins and ('Повторные инструктажи и периодическая проверка '
                       'знаний · %d' % Y) in ins['title'], ins and ins['title'])
        check('G2: БАГ-ФИКС: › АКТИВНА на %d (запись %d есть)'
              % (Y, Y + 1),
              ins and ins['offTitles'].count('›') == 0, ins)
        check('G3: ‹ АКТИВНА (записи %d есть)' % (Y - 2),
              ins and ins['offTitles'].count('‹') == 0, ins)
        page.screenshot(path=SHOTS + '/03-card-years-start.png')
        r = nav_click(page, 'Повторные инструктажи', 'next')
        page.wait_for_timeout(1000)
        ins2 = nav_state(page, 'Повторные инструктажи')
        check('G4: клик › → «Повторные инструктажи… · %d»' % (Y + 1),
              ins2 and ('· %d' % (Y + 1)) in ins2['title'],
              ins2 and ins2['title'])
        check('G5: запись %d («проверка знаний по промбезопасности») видна'
              % (Y + 1),
              ins2 and 'промбезопасности' in ins2['html'], ins2 and
              ins2['html'][:200])
        check('G6: на %d › ПОГАШЕНА (записей %d нет), ‹ активна'
              % (Y + 1, Y + 2),
              ins2 and ins2['offTitles'].count('›') == 1 and
              ins2['offTitles'].count('‹') == 0, ins2 and ins2['offTitles'])

        # --- отпуска (fam 2): НОВАЯ навигация ---
        vac = nav_state(page, 'Отпуска')
        check('H1: блок «Отпуска · %d» + навигатор ‹год› (НОВОЕ)' % Y,
              vac and ('Отпуска · %d' % Y) in vac['title'] and
              vac['liveCount'] + vac['offCount'] == 2, vac and vac['title'])
        check('H2: запись года %d видна (01.07.–14.07.)' % Y,
              vac and ('01.07.%d' % Y) in vac['html'] and
              ('14.07.%d' % Y) in vac['html'], vac and vac['html'][:200])
        check('H3: ‹ АКТИВНА (запись %d) и › АКТИВНА (запись %d)'
              % (Y - 1, Y + 1),
              vac and vac['offCount'] == 0, vac and vac['offTitles'])
        r = nav_click(page, 'Отпуска', 'prev')
        page.wait_for_timeout(1200)
        vac2 = nav_state(page, 'Отпуска')
        check('H4: клик ‹ → «Отпуска · %d» (архивный год)' % (Y - 1),
              vac2 and ('Отпуска · %d' % (Y - 1)) in vac2['title'],
              vac2 and vac2['title'])
        check('H5: архивная запись %d видна (02.06.–15.06.) с днями'
              % (Y - 1),
              vac2 and ('02.06.%d' % (Y - 1)) in vac2['html'] and
              ('15.06.%d' % (Y - 1)) in vac2['html'] and
              'дн' in vac2['html'], vac2 and vac2['html'][:300])
        check('H6: на %d ‹ ПОГАШЕНА (раньше записей нет)' % (Y - 1),
              vac2 and vac2['offTitles'].count('‹') == 1,
              vac2 and vac2['offTitles'])
        page.screenshot(path=SHOTS + '/04-card-vacations-archive.png')
        r = nav_click(page, 'Отпуска', 'next')
        page.wait_for_timeout(1000)
        r = nav_click(page, 'Отпуска', 'next')
        page.wait_for_timeout(1200)
        vac3 = nav_state(page, 'Отпуска')
        check('H7: › › → «Отпуска · %d», запись 05.05.–18.05. видна'
              % (Y + 1),
              vac3 and ('Отпуска · %d' % (Y + 1)) in vac3['title'] and
              ('05.05.%d' % (Y + 1)) in vac3['html'],
              vac3 and vac3['title'])
        check('H8: на %d › ПОГАШЕНА (записей дальше нет)' % (Y + 1),
              vac3 and vac3['offTitles'].count('›') == 1,
              vac3 and vac3['offTitles'])

        # --- мероприятия (fam 0): › по периоду до 15.01.Y+1 ---
        mev = nav_state(page, 'Мероприятия')
        check('I1: «Мероприятия · %d», › АКТИВНА (период до 15.01.%d)'
              % (Y, Y + 1),
              mev and ('Мероприятия · %d' % Y) in mev['title'] and
              mev['offTitles'].count('›') == 0, mev and mev['offTitles'])
        r = nav_click(page, 'Мероприятия', 'next')
        page.wait_for_timeout(1000)
        mev2 = nav_state(page, 'Мероприятия')
        check('I2: клик › → «Мероприятия · %d»' % (Y + 1),
              mev2 and ('Мероприятия · %d' % (Y + 1)) in mev2['title'],
              mev2 and mev2['title'])
        check('I3: запись «Стажировка на РМП» в году %d видна' % (Y + 1),
              mev2 and 'Стажировка на РМП' in mev2['html'],
              mev2 and mev2['html'][:200])

        # --- независимость годов трёх блоков ---
        ins3 = nav_state(page, 'Повторные инструктажи')
        vac4 = nav_state(page, 'Отпуска')
        check('J1: блоки НЕ влияют друг на друга: инструктажи %d, '
              'отпуска %d, мероприятия %d'
              % (Y + 1, Y + 1, Y + 1),
              ins3 and ('· %d' % (Y + 1)) in ins3['title'] and
              vac4 and ('Отпуска · %d' % (Y + 1)) in vac4['title'] and
              mev2 and ('Мероприятия · %d' % (Y + 1)) in mev2['title'],
              (ins3 and ins3['title'], vac4 and vac4['title']))

        # --- пул: listVacations по годам окна [Y-3 .. Y+3] ---
        page.wait_for_timeout(800)
        vac_years = sorted(set([c for c in VAC_CALLS if c != 'None']))
        want = [Y - 3, Y - 2, Y - 1, Y, Y + 1, Y + 2, Y + 3]
        check('K1: сервер получил listVacations по годам окна ±3 %s'
              % want,
              all(w in vac_years for w in want), vac_years)
        n_next = VAC_CALLS.count(Y + 2)
        check('K2: годы окна запрошены ПО ОДНОМУ разу (Y+2: %d)' % n_next,
              n_next == 1, VAC_CALLS)
        check('L1: JS-ошибок нет (контекст карточки)', js_errors == [],
              js_errors[:3])
        ctx.close()

        # ===== Контекст 3: мобайл 375 светлая — карточка =====
        print('=== Контекст 3: мобайл 375 — карточка (отпуска ‹год›) ===')
        ctx = browser.new_context(viewport={'width': 375, 'height': 812})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'light', 'mobile')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(1200)
        page.click(".ws-wtabs button:has-text('Федосов')")
        page.wait_for_timeout(1500)
        vacm = nav_state(page, 'Отпуска')
        check('M1: мобайл: «Отпуска · %d» + навигатор' % Y,
              vacm and ('Отпуска · %d' % Y) in vacm['title'] and
              vacm['liveCount'] + vacm['offCount'] == 2,
              vacm and vacm['title'])
        r = nav_click(page, 'Отпуска', 'prev')
        page.wait_for_timeout(1200)
        vacm2 = nav_state(page, 'Отпуска')
        check('M2: мобайл: ‹ → «Отпуска · %d» с записью' % (Y - 1),
              vacm2 and ('Отпуска · %d' % (Y - 1)) in vacm2['title'] and
              ('02.06.%d' % (Y - 1)) in vacm2['html'],
              vacm2 and vacm2['title'])
        page.screenshot(path=SHOTS + '/05-mobile-card-vacations.png')
        check('M3: мобайл: нет горизонтального переполнения',
              page.evaluate(
                  'document.documentElement.scrollWidth <= 375 + 1'),
              page.evaluate('document.documentElement.scrollWidth'))
        check('M4: JS-ошибок нет (мобайл)', js_errors == [], js_errors[:3])
        ctx.close()

        browser.close()

    print('\n===== ИТОГ: %d OK / %d FAIL =====' % (PASS, FAIL))
    return 1 if FAIL else 0


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    import webbrowser
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
