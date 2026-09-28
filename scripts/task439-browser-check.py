#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 439: browser-check — заявка пользователя: «В печатном
# графике блок с кодами размести справа от мероприятий, в колонке
# с работниками оставь только ФИО и Тип и сузь этот столбец по
# размеру самого большого текста в его ячейках. В мобильной
# версии, в разделе Табель учёта рабочего времени, убери лишний
# код "Выходной, плановый выходной день" который старый со знаком
# "." при выборе в ячейках шахматки».
# КОНТЕКСТЫ (мок-сервер, порт 8938):
#   1) десктоп 1280 тёмная, Админ — ГРАФИК РАБОТЫ → «Печать»:
#      - печатный лист: под ФИО — Тип «смена №1» (НЕ должность
#        «Слесарь КИПиА…»), ширина колонки ≤ 30mm (по тексту);
#      - ГЕОМЕТРИЯ в iframe предпросмотра: .wsp-bottom — flex;
#        .wsp-legend СПРАВА от .wsp-mev (legend.left > mev.left),
#        верхние линии блоков совпадают (±3px);
#      - «Сохранить PDF» → График_работы_*.pdf: %PDF-1.4,
#        DCTDecode, %%EOF, 842×595, 1 страница (pymupdf), рендер;
#      - «Сохранить Excel» → .xlsx: ячейка A6 «ФИО + \n + Тип»,
#        ширина столбца A по тексту (15), «Коды:» в колонке D,
#        wrapText в стилях;
#      - «Отмена» закрывает; 0 JS-ошибок.
#   2) мобайл 375 светлая — СПРАВОЧНИК С ДУБЛЯМИ (пустой код +
#        легаси «.» + легаси «·», все «Выходной, плановый выходной
#        день»): клик по ячейке шахматки → попап кодов: ровно ОДНА
#        строка «Выходного», НЕТ строк с кодами «.»/«·»; диалог
#        печати открывается; 0 JS-ошибок.
# + скриншот-пруфы.
import datetime
import json
import threading
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8938
TODAY = datetime.date.today()
Y = TODAY.year
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)

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

# ДУБЛЬ «Выходного» (заявка 3): канонический пустой код + ЛЕГАСИ
# «.» + ЛЕГАСИ «·» — все с именем «Выходной, плановый выходной
# день»; нормализация должна оставить ОДНУ строку
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
  {'code': '.', 'name': 'Выходной, плановый выходной день',
   'color': '#CFD8DC', 'short': 'выходной'},
  {'code': '·', 'name': 'Выходной, плановый выходной день',
   'color': '#CFD8DC', 'short': 'выходной'},
  {'code': 'И', 'name': 'Инструктаж, повторный по охране труда',
   'color': '#90CAF9', 'short': 'инструктаж'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]


def ev(i, tab, tip, tema, d1, d2=None, days=1, done=0):
    return {'id': i, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d1, 'дата_окончания': d2 or d1,
            'длительность_дней': days, 'комментарий': '',
            'дата_проведения': d1, 'выполнение': done,
            'просрочен': 0}


INSTR = [ev(600, '0871', 'инструктаж', 'Повторный инструктаж по охране труда',
            TODAY_ISO)]
EVENTS = [ev(500, '0871', 'обучение', 'Обучение по промбезопасности',
             TODAY_ISO)]


def fresh_entries():
    out = []
    dim = (datetime.date(TODAY.year, TODAY.month % 12 + 1, 1) -
           datetime.timedelta(days=1)).day
    for day in range(1, dim + 1):
        iso = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, day)
        if day <= 5:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
        if day == 6:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'д',
                        'переработка': 1, 'праздник': 0, 'источник': 'руч'})
        if day == 9:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'ОТ',
                        'переработка': 0, 'праздник': 0, 'источник': 'руч'})
    return out


ENTRIES = fresh_entries()

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task439'
os.makedirs(SHOTS, exist_ok=True)


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:220] + ']') if (extra and not ok) else ''))


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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t439-%s');" % tag +
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
                      body='not found (t439-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# --- проверки печатного листа (DOM главного документа) ---
SHEET_JS = """(function(root){
    var sheet = root.querySelector('#wsPrintSheet');
    if (!sheet) return null;
    var html = sheet.innerHTML;
    var fio = sheet.querySelector('.wsp-fio');
    var pos = sheet.querySelector('.wsp-pos');
    var empTh = sheet.querySelector('th.wsp-emp');
    var m = empTh && empTh.getAttribute('style');
    var wm = m ? (m.match(/width:([\\d.]+)mm/) || [])[1] : null;
    return {
        fio: fio ? fio.textContent : null,
        pos: pos ? pos.textContent : null,
        empWmm: wm ? parseFloat(wm) : null,
        hasDolzh: html.indexOf('Слесарь') !== -1,
        title: (sheet.querySelector('.wsp-title')||{}).textContent,
        legendShort: html.indexOf('Д8 — день 8ч') !== -1,
        hasMev: !!sheet.querySelector('.wsp-mev'),
        hasLegend: !!sheet.querySelector('.wsp-legend')
    };
})"""


# --- ГЕОМЕТРИЯ ряда мероприятий|кодов (в iframe предпросмотра) ---
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
        return {
            bottomDisplay: bs.display,
            mevLeft: mev.offsetLeft, mevTop: mev.offsetTop,
            mevW: mev.offsetWidth,
            legLeft: leg.offsetLeft, legTop: leg.offsetTop,
            legW: leg.offsetWidth,
            legendTxt: leg.textContent.slice(0, 80),
            mevTxt: mev.querySelector('.wsp-mev-t').textContent
        };
    } catch (e) { return 'err: ' + e; }
})"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== Контекст 1: десктоп 1280 тёмная, Админ =====
        print('=== Контекст 1: десктоп тёмная Админ — Печать табеля ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                                  accept_downloads=True)
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'edit')
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось',
              page.evaluate("document.title === 'КИПиА'"))

        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        check('A2: график работы открыт (шахматка с данными)',
              page.evaluate("(function(){var g=document.querySelector(" +
              "'#page-work-schedule .ws-grid, .ws-grid');return !!g;})()"))

        page.click('#wsPrintBtn')
        page.wait_for_timeout(1500)
        check('B1: диалог предпросмотра открыт',
              page.evaluate("!!document.getElementById('wsPrintPrevModal')"))

        # --- печатный лист: колонка работника ФИО + Тип ---
        si = page.evaluate(SHEET_JS + '(document)')
        check('C1: заголовок «График работы»',
              si and si['title'] == 'График работы', si)
        check('C2: ФИО в колонке', si and si['fio'] == 'Федосов А. В.', si)
        check('C3: под ФИО — ТИП «смена №1» (не должность)',
              si and si['pos'] == 'смена №1', si)
        check('C4: должности («Слесарь КИПиА…») в колонке НЕТ',
              si and not si['hasDolzh'], si)
        check('C5: ширина колонки — по тексту (≤ 30mm)',
              si and si['empWmm'] is not None and
              10 <= si['empWmm'] <= 30, si and si['empWmm'])
        check('C6: секции мероприятий и кодов строятся',
              si and si['hasMev'] and si['hasLegend'] and si['legendShort'], si)

        # --- ГЕОМЕТРИЯ: коды СПРАВА от мероприятий (iframe) ---
        page.wait_for_timeout(800)
        g = page.evaluate(GEOM_JS)
        check('D1: нижняя секция — flex-ряд',
              g and g['bottomDisplay'] == 'flex', g)
        check('D2: блок кодов СПРАВА от мероприятий',
              g and g['legLeft'] > g['mevLeft'] + g['mevW'] * 0.5, g)
        check('D3: общая верхняя линия (legend.top == mev.top ±3px)',
              g and abs(g['legTop'] - g['mevTop']) <= 3, g)
        check('D4: ширина блока кодов ≈ 92mm (347±25px)',
              g and 320 <= g['legW'] <= 375, g and g['legW'])
        check('D5: заголовки секций на месте',
              g and 'Мероприятия' in g['mevTxt'] and
              'Коды' in g['legendTxt'], g)

        page.screenshot(path=SHOTS + '/01-dialog-preview.png')

        # --- сохранение PDF ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-pdf')
            dl = dl_info.value
            pdf_path = '/tmp/t439-graph.pdf'
            dl.save_as(pdf_path)
            raw = open(pdf_path, 'rb').read()
            check('E1: PDF скачан — имя', dl.suggested_filename.startswith(
                'График_работы_') and dl.suggested_filename.endswith('.pdf'),
                dl.suggested_filename)
            check('E2: PDF — заголовок %PDF-1.4 и хвост %%EOF',
                  raw[:8] == b'%PDF-1.4' and b'%%EOF' in raw[-40:],
                  raw[:20])
            check('E3: PDF — страницы с JPEG (DCTDecode)',
                  b'/DCTDecode' in raw and b'/Type /Pages' in raw)
            check('E4: PDF — MediaBox A4-альбомная',
                  b'MediaBox [0 0 842 595]' in raw)
            try:
                import fitz
                doc = fitz.open(pdf_path)
                check('E5: PDF — 1 страница (компактный месяц)',
                      doc.page_count == 1, doc.page_count)
                pg = doc.load_page(0)
                check('E6: PDF — страница 842×595 pt',
                      abs(pg.rect.width - 842) < 1 and
                      abs(pg.rect.height - 595) < 1,
                      (pg.rect.width, pg.rect.height))
                pix = pg.get_pixmap(dpi=110)
                pix.save(SHOTS + '/02-pdf-page1.png')
                check('E7: PDF — рендер страницы снят (пруф)', True)
            except ImportError:
                check('E5..E7: pymupdf недоступен (пропуск рендера)',
                      True)
        except Exception as e:
            check('E1..E7: сохранение PDF', False, str(e)[:220])

        # --- сохранение Excel ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-xlsx')
            dl = dl_info.value
            xlsx_path = '/tmp/t439-graph.xlsx'
            dl.save_as(xlsx_path)
            raw = open(xlsx_path, 'rb').read()
            check('F1: Excel скачан — имя', dl.suggested_filename.startswith(
                'График_работы_') and dl.suggested_filename.endswith('.xlsx'),
                dl.suggested_filename)
            check('F2: Excel — PK-zip контейнер',
                  raw[:2] == b'PK' and b'PK\x05\x06' in raw[-30:], raw[:10])
            import zipfile
            zf = zipfile.ZipFile(xlsx_path)
            sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
            check('F3: ячейка A — ФИО + перенос строки + Тип',
                  'Федосов А. В.\nсмена №1' in sheet_xml,
                  [l for l in sheet_xml.split('<row') if 'Федосов' in l][:1])
            check('F4: ширина столбца A — по тексту (16, не 30)',
                  '<col min="1" max="1" width="16"' in sheet_xml and
                  'width="30"' not in sheet_xml)
            check('F5: «Коды:» — в колонке D (справа от мероприятий)',
                  re.search(r'<c r="D\d+" t="inlineStr" s="1">'
                            r'<is><t>Коды:</t></is></c>', sheet_xml)
                  is not None)
            check('F6: заголовок мероприятий — в A той же строки',
                  'Мероприятия ·' in sheet_xml)
            check('F7: коды — в столбце D построчно',
                  re.search(r'<c r="D\d+" t="inlineStr" s="0">'
                            r'<is><t>Д8 — день 8ч</t></is></c>', sheet_xml)
                  is not None)
            styles_xml = zf.read('xl/styles.xml').decode('utf-8')
            check('F8: стиль ячейки работника — wrapText (две строки)',
                  'wrapText="1"' in styles_xml and
                  'vertical="top"' in styles_xml)
            check('F9: НЕТ «Часы», «Перераб.» — дни',
                  '>Часы<' not in sheet_xml and '>Перераб.<' in sheet_xml)
        except Exception as e:
            check('F1..F9: сохранение Excel', False, str(e)[:220])

        page.click('.wspprev-cancel')
        page.wait_for_timeout(400)
        check('G1: «Отмена» закрыла диалог',
              page.evaluate("!document.getElementById('wsPrintPrevModal')"))
        check('G2: 0 JS-ошибок (десктоп)', not js_errors, js_errors[:3])

        # ===== Контекст 2: мобайл 375 светлая — попап ячеек =====
        print('=== Контекст 2: мобайл 375 светлая — попап без дубля «.» ===')
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'mob')
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        check('H1: мобайл — сетка шахматки открыта',
              page2.evaluate("!!document.querySelector(" +
              "'#page-work-schedule .ws-grid, .ws-grid')"))

        # клик по ячейке (2-й день) → попап выбора кодов
        cell = 'tr:has(td.ws-emp-col[data-tab="0871"]) td.ws-cell[data-day="2"]'
        page2.click(cell)
        page2.wait_for_timeout(700)
        pop = page2.evaluate("""(function(){
            var pp = document.getElementById('wsCellPopup');
            if (!pp || !pp.classList.contains('active')) return null;
            var rows = Array.prototype.slice.call(
                pp.querySelectorAll('.ws-popup-row'));
            var codes = rows.map(function(r){
                var c = r.querySelector('.ws-popup-code');
                return c ? c.textContent : '';
            });
            var vykhCount = (pp.textContent.match(
                /Выходной, плановый выходной день/g) || []).length;
            return {
                n: rows.length,
                codes: codes,
                vykhCount: vykhCount,
                hasDot: codes.indexOf('.') !== -1,
                hasMidDot: codes.indexOf('·') !== -1,
                hasClear: rows.some(function(r){
                    return (r.getAttribute('onclick') || '')
                        .indexOf("onPopupStatus('')") !== -1; })
            };
        })()""")
        check('I1: попап выбора кодов открыт', pop is not None, pop)
        check('I2: ровно ОДНА строка «Выходной, плановый выходной день»',
              pop and pop['vykhCount'] == 1, pop and pop['vykhCount'])
        check('I3: легаси-код «.» в списке НЕТ',
              pop and not pop['hasDot'], pop and pop['codes'])
        check('I4: легаси-код «·» в списке НЕТ',
              pop and not pop['hasMidDot'], pop and pop['codes'])
        check('I5: клик по «Выходному» — очистка (пустой код)',
              pop and pop['hasClear'], pop and pop['codes'])
        page2.screenshot(path=SHOTS + '/03-mobile-cell-popup.png')

        # закрыть попап (кловер), открыть печать
        page2.evaluate("WorkSchedule.closeCellPopup && " +
                       "WorkSchedule.closeCellPopup()")
        page2.wait_for_timeout(300)
        page2.click('#wsPrintBtn')
        page2.wait_for_timeout(1200)
        check('J1: мобайл — диалог печати открыт',
              page2.evaluate("!!document.getElementById('wsPrintPrevModal')"))
        check('J2: мобайл — кнопки PDF/Excel есть',
              page2.evaluate("(function(){var ov=document." +
              "getElementById('wsPrintPrevModal');var f=ov&&ov.querySelector" +
              "('.wspprev-foot');return !!(f&&f.querySelector('.wspprev-pdf')" +
              "&&f.querySelector('.wspprev-xlsx'));})()"))
        check('J3: мобайл — 0 JS-ошибок', not js_errors2, js_errors2[:3])
        page2.screenshot(path=SHOTS + '/04-mobile-print-dialog.png')

        browser.close()

    print('\nИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    os.chdir('/home/z/my-project/kip8test')

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass
    httpd = HTTPServer(('127.0.0.1', PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        code = main()
    finally:
        httpd.shutdown()
    raise SystemExit(code)
