#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 438: browser-check — заявка пользователя: «В разделе Табель
# учёта рабочего времени при выводе на печать список кодов должен
# отображаться в сокращённом виде, формат верхнего текста
# переделай на "График работы / Сентябрь 2026 г. · вид табеля:
# полный", нижний текст убери, колонку "Часы" убери, в колонке
# "Перераб." только дни. Так же сделай возможность сохранения в
# файл вместо html в PDF и Excel».
# КОНТЕКСТЫ (мок-сервер, порт 8937):
#   1) десктоп 1280 тёмная, Админ — ГРАФИК РАБОТЫ → «Печать»:
#      - диалог предпросмотра открывается; кнопки «Печать» /
#        «Сохранить PDF» / «Сохранить Excel» / «Отмена»; кнопки
#        «Сохранить в файл» (HTML) НЕТ;
#      - печатный лист #wsPrintSheet: заголовок «График работы» +
#        строка «месяц год · вид табеля: полный»; НЕТ нормы
#        (40-час), НЕТ «Распечатано», НЕТ сноски wsp-foot, НЕТ
#        колонки «Часы»; «Перераб.» — только дни (нет «N/M»);
#        коды — сокращённые («Д8 — день 8ч», не полное имя);
#      - iframe предпросмотра — те же проверки в standalone-доке;
#      - «Сохранить PDF» → загрузка График_работы_*.pdf: %PDF-1.4,
#        /DCTDecode, %%EOF, размер > 10 КБ;
#      - «Сохранить Excel» → загрузка График_работы_*.xlsx:
#        PK-zip, лист «Табель», шапка 2 строки, нет «Часы»,
#        «Перераб.», «Коды:» с сокращениями, заливки цветов;
#      - «Отмена» закрывает диалог; 0 JS-ошибок.
#   2) мобайл 375 светлая — диалог открывается, без переполнения,
#      0 JS-ошибок.
# + скриншот-пруфы (диалог + предпросмотр).
import datetime
import json
import threading
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8937
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
            # день в выходной — источник переработки (overDays ≥ 1)
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'д',
                        'переработка': 1, 'праздник': 0, 'источник': 'руч'})
        if day == 9:
            out.append({'дата': iso, 'таб_номер': '0871', 'статус': 'ОТ',
                        'переработка': 0, 'праздник': 0, 'источник': 'руч'})
    return out


ENTRIES = fresh_entries()

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task438'
os.makedirs(SHOTS, exist_ok=True)


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:200] + ']') if (extra and not ok) else ''))


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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t438-%s');" % tag +
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
                      body='not found (t438-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# --- проверки печатного листа (внутри страницы или iframe) ---
SHEET_JS = """(function(root){
    var sheet = root.querySelector('#wsPrintSheet');
    if (!sheet) return null;
    var html = sheet.innerHTML;
    var fio = sheet.querySelector('.wsp-fio');
    var overCells = Array.prototype.slice.call(
        sheet.querySelectorAll('td.wsp-tot-over'));
    var overVals = overCells.map(function(td){ return td.textContent; });
    var hasSlash = overVals.some(function(v){ return /\//.test(v); });
    var title = sheet.querySelector('.wsp-title');
    var sub = sheet.querySelector('.wsp-sub');
    return {
        title: title ? title.textContent : null,
        sub: sub ? sub.textContent : null,
        hasMeta: !!sheet.querySelector('.wsp-meta'),
        hasPrinted: html.indexOf('Распечатано') !== -1,
        hasNorm: html.indexOf('Норма (40-час') !== -1,
        hasFoot: !!sheet.querySelector('.wsp-foot'),
        hasHoursCol: html.indexOf('>Часы</th>') !== -1,
        hasDaysCol: html.indexOf('>Дни</th>') !== -1,
        overVals: overVals,
        hasSlash: hasSlash,
        fio: fio ? fio.textContent : null,
        legendShort: html.indexOf('Д8 — день 8ч') !== -1,
        legendFull: html.indexOf('плановая дневная 8-часовая смена') !== -1,
        hasMev: !!sheet.querySelector('.wsp-mev')
    };
})"""


def sheet_info(page, dom='document'):
    root = 'document' if dom == 'document' else \
        "document.getElementById('wsPrintPrevModal')" \
        ".querySelector('.wspprev-frame').contentDocument"
    return page.evaluate(SHEET_JS + '(' + root + ')')


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

        # --- диалог предпросмотра ---
        page.click('#wsPrintBtn')
        page.wait_for_timeout(1200)
        check('B1: диалог предпросмотра открыт',
              page.evaluate("!!document.getElementById('wsPrintPrevModal')"))
        btns = page.evaluate("""(function(){
            var ov = document.getElementById('wsPrintPrevModal');
            if (!ov) return null;
            var f = ov.querySelector('.wspprev-foot');
            return {
                print: !!f.querySelector('.wspprev-print'),
                pdf: !!f.querySelector('.wspprev-pdf'),
                xlsx: !!f.querySelector('.wspprev-xlsx'),
                cancel: !!f.querySelector('.wspprev-cancel'),
                save: !!f.querySelector('.wspprev-save'),
                text: f.textContent
            };
        })()""")
        check('B2: кнопки Печать/PDF/Excel/Отмена',
              btns and btns['print'] and btns['pdf'] and btns['xlsx']
              and btns['cancel'], btns)
        check('B3: кнопки «Сохранить PDF» и «Сохранить Excel» с текстом',
              btns and 'Сохранить PDF' in btns['text']
              and 'Сохранить Excel' in btns['text'], btns and btns['text'])
        check('B4: кнопки «Сохранить в файл» (HTML) НЕТ',
              btns and not btns['save'] and 'Сохранить в файл' not in btns['text'])

        # --- печатный лист в основном документе ---
        si = sheet_info(page)
        check('C1: заголовок «График работы»', si and si['title'] == 'График работы', si)
        check('C2: подстрока «…г. · вид табеля: полный»',
              si and si['sub'] and 'вид табеля: полный' in si['sub'], si)
        check('C3: НЕТ нормы (wsp-meta/«Норма (40-час»)',
              si and not si['hasMeta'] and not si['hasNorm'], si)
        check('C4: НЕТ штампа «Распечатано»', si and not si['hasPrinted'], si)
        check('C5: НЕТ сноски wsp-foot', si and not si['hasFoot'], si)
        check('C6: НЕТ колонки «Часы»', si and not si['hasHoursCol'], si)
        check('C7: колонка «Дни» есть', si and si['hasDaysCol'], si)
        check('C8: «Перераб.» — только дни (без «N/M»)',
              si and not si['hasSlash'] and si['overVals'] and
              all(re.fullmatch(r'\d+|—', v.strip()) for v in si['overVals']),
              si and si['overVals'])
        check('C9: строка сотрудника в листе',
              si and si['fio'] == 'Федосов А. В.', si)
        check('C10: коды — сокращённые («Д8 — день 8ч»)',
              si and si['legendShort'] and not si['legendFull'], si)
        check('C11: секция мероприятий есть', si and si['hasMev'], si)

        # --- iframe предпросмотра (standalone-документ) ---
        page.wait_for_timeout(800)
        pif = page.evaluate("""(function(){
            var ov = document.getElementById('wsPrintPrevModal');
            if (!ov) return null;
            var f = ov.querySelector('.wspprev-frame');
            try {
                var d = f.contentDocument;
                var sheet = d && d.getElementById('wsPrintSheet');
                if (!sheet) return null;
                var html = sheet.innerHTML;
                return {
                    title: (sheet.querySelector('.wsp-title')||{})
                        .textContent,
                    hasPrinted: html.indexOf('Распечатано') !== -1,
                    hasFoot: !!sheet.querySelector('.wsp-foot'),
                    hasHoursCol: html.indexOf('>Часы</th>') !== -1,
                    legendShort: html.indexOf('Д8 — день 8ч') !== -1
                };
            } catch (e) { return 'err: ' + e; }
        })()""")
        check('D1: iframe — заголовок «График работы»',
              pif and pif['title'] == 'График работы', pif)
        check('D2: iframe — без «Распечатано»/сноски/«Часов»',
              pif and not pif['hasPrinted'] and not pif['hasFoot']
              and not pif['hasHoursCol'], pif)
        check('D3: iframe — коды сокращённые',
              pif and pif['legendShort'], pif)

        page.screenshot(path=SHOTS + '/01-dialog-preview.png')

        # --- сохранение PDF ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-pdf')
            dl = dl_info.value
            pdf_path = '/tmp/t438-graph.pdf'
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
            check('E4: PDF — размер разумный (> 10 КБ)',
                  len(raw) > 10240, len(raw))
            check('E5: PDF — MediaBox A4-альбомная',
                  b'MediaBox [0 0 842 595]' in raw)
        except Exception as e:
            check('E1..E5: сохранение PDF', False, str(e)[:200])

        # --- сохранение Excel ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-xlsx')
            dl = dl_info.value
            xlsx_path = '/tmp/t438-graph.xlsx'
            dl.save_as(xlsx_path)
            raw = open(xlsx_path, 'rb').read()
            check('F1: Excel скачан — имя', dl.suggested_filename.startswith(
                'График_работы_') and dl.suggested_filename.endswith('.xlsx'),
                dl.suggested_filename)
            check('F2: Excel — PK-zip контейнер',
                  raw[:2] == b'PK' and b'PK\x05\x06' in raw[-30:], raw[:10])
            import zipfile
            zf = zipfile.ZipFile(xlsx_path)
            names = zf.namelist()
            check('F3: Excel — части книги на месте',
                  'xl/worksheets/sheet1.xml' in names and
                  'xl/styles.xml' in names and 'xl/workbook.xml' in names,
                  names)
            sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
            check('F4: лист «Табель» в workbook',
                  '<sheet name="Табель"' in
                  zf.read('xl/workbook.xml').decode('utf-8'))
            check('F5: шапка «График работы» + вид табеля',
                  '>График работы<' in sheet_xml and
                  'вид табеля: полный' in sheet_xml, sheet_xml[:200])
            check('F6: НЕТ «Часы», есть «Дни»/«Перераб.»',
                  '>Часы<' not in sheet_xml and '>Дни<' in sheet_xml and
                  '>Перераб.<' in sheet_xml)
            check('F7: коды сокращённые + мероприятия',
                  'Д8 — день 8ч' in sheet_xml and
                  'Мероприятия ·' in sheet_xml and 'Коды:' in sheet_xml)
            styles_xml = zf.read('xl/styles.xml').decode('utf-8')
            check('F8: цветные заливки кодов (Д8/ОТ)',
                  'FFFFF9C4' in styles_xml and 'FFECEFF1' in styles_xml)
            check('F9: закрепление шапки (xSplit/ySplit)',
                  'xSplit="1"' in sheet_xml and 'ySplit="5"' in sheet_xml)
        except Exception as e:
            check('F1..F9: сохранение Excel', False, str(e)[:200])

        # --- отмена закрывает ---
        page.click('.wspprev-cancel')
        page.wait_for_timeout(400)
        check('G1: «Отмена» закрыла диалог',
              page.evaluate("!document.getElementById('wsPrintPrevModal')"))
        check('G2: 0 JS-ошибок (десктоп)', not js_errors, js_errors[:3])

        # ===== Контекст 2: мобайл 375 светлая =====
        print('=== Контекст 2: мобайл 375 светлая ===')
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'mob')
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        page2.click('#wsPrintBtn')
        page2.wait_for_timeout(1200)
        check('H1: мобайл — диалог открыт',
              page2.evaluate("!!document.getElementById('wsPrintPrevModal')"))
        check('H2: мобайл — кнопки PDF/Excel есть',
              page2.evaluate("(function(){var ov=document." +
              "getElementById('wsPrintPrevModal');var f=ov&&ov.querySelector" +
              "('.wspprev-foot');return !!(f&&f.querySelector('.wspprev-pdf')" +
              "&&f.querySelector('.wspprev-xlsx'));})()"))
        check('H3: мобайл — 0 JS-ошибок', not js_errors2, js_errors2[:3])
        page2.screenshot(path=SHOTS + '/02-mobile-dialog.png')

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
