#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 441: browser-check — заявка: «Во всех трёх представлениях
# печати коды сделай в один столбец».
# КОНТЕКСТ (мок-сервер, порт 8941): десктоп 1280 тёмная, Админ —
# ГРАФИК РАБОТЫ → «Печать»:
#   1) HTML-печать (iframe): сетка .wsp-legend-cols — ОДНА колонка
#      (computed grid-template-columns = 1 трек, прежде 2);
#      все записи .wsp-lg — на ОДНОЙ вертикали (левые края равны
#      ±1px); регресс 440: коды справа от мероприятий, зазор 10px;
#   2) «Сохранить PDF»: %PDF-1.4, A4-альбом 842×595, 1 стр. +
#      ДЕТЕРМИНИРОВАННЫЙ ПРУФ перехватом canvas: квадратики кодов
#      (fillRect 4.5×4.5) — все на ОДНОЙ вертикали (разброс X = 0),
#      шаг по Y = 14pt (codeRowH); две колонки дали бы вторую
#      вертикаль через ~117pt;
#   3) «Сохранить Excel»: строки блока после «Коды:» — ячейки
#      ТОЛЬКО в A–D (правее D пусто), код-строки s="7" в D;
#   4) 0 JS-ошибок; скриншоты в download/screenshots-task441/.
import datetime
import json
import os
import re
import zipfile
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8941
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
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

# месячная легенда: Д8, д, ОТ (записи) + И (инструктаж сегодня);
# Н и «» (пустой) в этом месяце НЕ используются — в легенду не
# попадают (Task 360)
INSTR = [
    {'id': 600, 'таб_номер': '0871', 'тип': 'инструктаж',
     'тема': 'Повторный инструктаж по охране труда',
     'дата_начала': TODAY_ISO, 'дата_окончания': TODAY_ISO,
     'длительность_дней': 1, 'комментарий': '',
     'дата_проведения': TODAY_ISO, 'выполнение': 1, 'просрочен': 0},
]
INSTR_LIST = [
  {'название': 'Повторный инструктаж по охране труда', 'вид': 'инструктаж',
   'периодичность': 6, 'основание': '', 'сокращение': 'Инстр. ОТ'},
]
EXPECT_CODES = 4  # Д8, д, ОТ, И

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task441'
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


def api_response(action):
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
            'trainings': [dict(r) for r in INSTR],
            'instrList': [dict(x) for x in INSTR_LIST],
            'instrAll': [dict(r) for r in INSTR], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t441-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        resp = api_response(action)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t441-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# геометрия печатного листа в iframe предпросмотра (Task 441)
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
        var cols = sheet.querySelector('.wsp-legend-cols');
        if (!bottom || !mev || !leg || !cols) return {missing: true};
        var bs = d.defaultView.getComputedStyle(bottom);
        var cs = d.defaultView.getComputedStyle(cols);
        var mr = mev.getBoundingClientRect();
        var lr = leg.getBoundingClientRect();
        var lgs = cols.querySelectorAll('.wsp-lg');
        var lefts = [], texts = [];
        for (var i = 0; i < lgs.length; i++) {
            lefts.push(lgs[i].getBoundingClientRect().left);
            texts.push(lgs[i].textContent.replace(/\\s+/g, ' ').trim());
        }
        return {
            bottomDisplay: bs.display,
            bottomGap: bs.gap,
            gridCols: cs.gridTemplateColumns,
            tracks: cs.gridTemplateColumns.split(' ').length,
            colGap: cs.columnGap,
            nCodes: lgs.length,
            leftsMin: lefts.length ? Math.min.apply(null, lefts) : null,
            leftsMax: lefts.length ? Math.max.apply(null, lefts) : null,
            leftsSpread: lefts.length
                ? Math.max.apply(null, lefts) - Math.min.apply(null, lefts)
                : null,
            codeTexts: texts,
            mevRight: mr.right, legLeft: lr.left,
            mevTop: mr.top, legTop: lr.top,
            gapPx: lr.left - mr.right,
            legendTxt: leg.textContent.slice(0, 80),
            mevTxt: mev.querySelector('.wsp-mev-t').textContent
        };
    } catch (e) { return 'err: ' + e; }
})"""


# ===== PDF: детерминированный пруф одноколоночности =====
# перехват canvas: квадратики легенды — fillRect(x, y, 4.5, 4.5)
# (уникальный размер: ячейки сетки dayW×rowH, бейджи 3.4, фон
# 842×595). Запись координат при РЕАЛЬНОМ вызове генератора.
CAPTURE_ON_JS = """(function(){
    var ws = window.WorkSchedule;
    if (ws.__t441origSave) return true;
    ws.__t441origSave = ws._savePrintPdf;
    ws._savePrintPdf = function(viewEmps, agg){
        window.__t441cap = {viewEmps: viewEmps, agg: agg};
        ws._savePrintPdf = ws.__t441origSave;
        return ws.__t441origSave.apply(this, arguments);
    };
    return true;
})"""

PAINT_RECORD_JS = """(function(){
    var ws = window.WorkSchedule;
    var cap = window.__t441cap;
    if (!cap) return {err: 'контекст печати не захвачен'};
    var rects = [];
    var orig = document.createElement.bind(document);
    document.createElement = function(tag){
        var el = orig(tag);
        if (tag === 'canvas' && el && el.getContext) {
            var origGet = el.getContext.bind(el);
            el.getContext = function(type){
                var ctx = origGet(type);
                if (ctx && ctx.fillRect && !ctx.__t441rec) {
                    ctx.__t441rec = true;
                    var origFillRect = ctx.fillRect.bind(ctx);
                    ctx.fillRect = function(x, y, w, h){
                        if (w === 4.5 && h === 4.5) {
                            rects.push([x, y, String(ctx.fillStyle)]);
                        }
                        return origFillRect(x, y, w, h);
                    };
                }
                return ctx;
            };
        }
        return el;
    };
    var out;
    try {
        var model = ws._printModel(cap.viewEmps, cap.agg);
        var lay = ws._printPdfLayout(model);
        var painted = 0;
        for (var p = 0; p < lay.pages.length; p++) {
            if (ws._printPdfPaintPage(lay, model, p)) painted++;
        }
        var xs = rects.map(function(r){ return r[0]; });
        var ys = rects.map(function(r){ return r[1]; })
            .sort(function(a, b){ return a - b; });
        var steps = [];
        for (var i = 1; i < ys.length; i++) steps.push(ys[i] - ys[i-1]);
        out = {
            pages: lay.pages.length, painted: painted,
            nCodes: (model.codes || []).length,
            squares: rects.length,
            xSpread: xs.length ? Math.max.apply(null, xs) -
                     Math.min.apply(null, xs) : null,
            ySteps: steps,
            colors: rects.map(function(r){ return r[2]; })
        };
    } catch (e) { out = {err: String(e)}; }
    finally { document.createElement = orig; }
    return out;
})"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ — ПЕЧАТЬ =====
        print('=== Контекст: десктоп тёмная — печать (коды одним '
              'столбцом) ===')
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

        # --- HTML: сетка кодов — ОДНА колонка ---
        page.wait_for_timeout(800)
        g = page.evaluate(GEOM_JS)
        check('C1: секция — flex-ряд (регресс 439/440)',
              g and g['bottomDisplay'] == 'flex', g)
        check('C2: зазор мероприятий↔коды = 10px (регресс 440)',
              g and g['bottomGap'] == '10px' and
              abs(g['gapPx'] - 10.0) <= 1.0,
              (g and g['bottomGap'], g and g['gapPx']))
        check('C3: сетка .wsp-legend-cols — ОДИН трек (прежде 2)',
              g and g['tracks'] == 1, (g and g['gridCols'],
                                       g and g['tracks']))
        check('C4: computed grid-template-columns = один трек',
              g and (' ' not in str(g['gridCols']).strip()) or
              g and str(g['gridCols']).count('fr') == 1,
              g and g['gridCols'])
        check('C5: все записи .wsp-lg на ОДНОЙ вертикали (±1px)',
              g and g['leftsSpread'] is not None and
              g['leftsSpread'] <= 1.0, g and g['leftsSpread'])
        check('C6: записей в легенде — %d (Д8, д, ОТ, И)'
              % EXPECT_CODES,
              g and g['nCodes'] == EXPECT_CODES,
              (g and g['nCodes'], g and g['codeTexts']))
        check('C7: тексты кодов — сокращённые (Task 438) и код месяца',
              g and g['codeTexts'] and
              all(('— ' in t) for t in g['codeTexts']) and
              any(t.startswith('Д8') for t in g['codeTexts']),
              g and g['codeTexts'])
        check('C8: заголовки секций на месте',
              g and 'Мероприятия' in g['mevTxt'] and
              'Коды' in g['legendTxt'], g)
        check('C9: коды СПРАВА от мероприятий (регресс 439)',
              g and g['legLeft'] > g['mevRight'] - 1, g)

        page.screenshot(path=SHOTS + '/01-print-dialog-onecol.png')

        # --- PDF: один столбец (детерминированный пруф) ---
        try:
            # захват контекста печати при РЕАЛЬНОМ клике кнопки
            page.evaluate(CAPTURE_ON_JS)
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-pdf')
            dl = dl_info.value
            pdf_path = '/tmp/t441-graph.pdf'
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
                pg.get_pixmap(dpi=150).save(SHOTS + '/02-pdf-page1.png')
                check('D5b: рендер снят (визуальный пруф)', True)
            except ImportError:
                check('D4..D5b: pymupdf недоступен (пропуск)', True)
            # перехват отрисовки: координаты квадратиков кодов
            rec = page.evaluate(PAINT_RECORD_JS)
            check('D6: ПРУФ: квадратиков = числу кодов (%d)'
                  % EXPECT_CODES,
                  rec and rec.get('squares') == EXPECT_CODES and
                  rec.get('squares') == rec.get('nCodes'),
                  rec)
            check('D7: ПРУФ: все квадратики на ОДНОЙ вертикали '
                  '(разброс X = 0pt)',
                  rec and rec.get('xSpread') == 0, rec)
            check('D8: ПРУФ: шаг по Y = 14pt (codeRowH, столбец '
                  'сплошной)',
                  rec and rec.get('ySteps') and
                  all(abs(s - 14) < 0.01 for s in rec['ySteps']),
                  rec and rec.get('ySteps'))
        except Exception as e:
            check('D1..D8: сохранение PDF', False, str(e)[:230])

        # --- Excel: коды — только столбец D ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-xlsx')
            dl = dl_info.value
            xlsx_path = '/tmp/t441-graph.xlsx'
            dl.save_as(xlsx_path)
            z = zipfile.ZipFile(xlsx_path)
            sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
            check('E1: Excel скачан — имя .xlsx',
                  dl.suggested_filename.endswith('.xlsx'),
                  dl.suggested_filename)
            m_hdr = re.search(r'<c r="D(\d+)" t="inlineStr" s="8">'
                              r'<is><t>Коды:</t></is></c>', sheet)
            check('E2: «Коды:» — колонка D (стиль 8, регресс 440)',
                  m_hdr is not None)
            if m_hdr:
                hdr_row = int(m_hdr.group(1))
                tail = sheet.split('<row r="%d"' % (hdr_row,), 1)[1]
                tail = tail.split('</sheetData>', 1)[0]
                # все ячейки строк блока — только A–D
                cols = re.findall(r'<c r="([A-Z]+)\d+"', tail)
                bad = [c for c in cols if c not in ('A', 'B', 'C', 'D')]
                check('E3: строки блока — ячейки ТОЛЬКО в A–D '
                      '(правее D пусто)', not bad, bad[:6])
                d7 = re.findall(r'<c r="D\d+" t="inlineStr" s="7">'
                                r'<is><t>', tail)
                check('E4: код-строк в D — ровно %d (строка на код)'
                      % EXPECT_CODES, len(d7) == EXPECT_CODES, len(d7))
                # мероприятия — в A/B тех же строк (регресс 439)
                check('E5: мероприятий — A/B на тех же строках',
                      re.search(r'<c r="A%d" t="inlineStr" s="5">'
                                r'<is><t>\d\d\.\d\d</t></is></c>'
                                % (hdr_row + 1,), sheet) is not None or
                      re.search(r'<c r="A%d" t="inlineStr"'
                                % (hdr_row + 1,), sheet) is not None,
                      'строка под шапкой блока не найдена')
        except Exception as e:
            check('E1..E5: сохранение Excel', False, str(e)[:230])

        page.screenshot(path=SHOTS + '/03-print-dialog-final.png')
        check('F1: JS-ошибок нет', js_errors == [], js_errors[:3])
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
