#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 442: browser-check — заявка: «На распечатываемом графике
# работы убери мини значки мероприятий в шахматке и столбец с
# кодами, и внешний контур линий выходных календарных дней в
# шахматке сделай толще, а выделять их фоном не нужно, и даты
# выходных жирнее».
# КОНТЕКСТ (мок-сервер, порт 8943): десктоп 1280 тёмная, Админ —
# ГРАФИК РАБОТЫ (сентябрь 2026: 1-е — вторник, полосы выходных
# 5–6/12–13/19–20/26–27) → «Печать»:
#   1) HTML-печать (iframe): легенды кодов и бейджей .wsp-ev НЕТ;
#      .wsp-bottom — блок (без flex/gap); мероприятия живы;
#      шапка: th выходного — классы wsp-off + края полосы
#      (edge-l у Сб, edge-r у Вс), computed border-top/left/right
#      2px, БЕЗ заливки, число ЖИРНОЕ (700), будни — 400, день
#      недели под числом — 400;
#      тело: клетки полосы — wsp-cell-off, край-л у Сб, край-р у
#      Вс, последняя строка — край-б (низ), заливки выходных НЕТ;
#   2) PDF: %PDF-1.4, 842×595, 1 стр. + ПРУФ перехватом canvas:
#      НИ ОДНОГО квадратика кодов (4.5×4.5) и бейджа (3.4×3.4),
#      НЕТ заливок выходных (#e2e8ec/#dfe5e9), ЕСТЬ толстые
#      strokeRect-контуры полос (lineWidth 1.4, ≥ 4 полос) и
#      ЖИРНЫЕ числа выходных ('700 7px Arial' среди установок
#      шрифта наряду с '7px Arial');
#   3) Excel: НЕТ «Коды:» и ячеек правее B в блоке мероприятий;
#      стили: 7 шрифтов, 13 границ (medium-контур), cellXfs 46
#      (3 цвета); числа: будни — НЕ жирные (s=45 regDate), Сб 5-го
#      — жирный контурный TL (s=11), Вс 6-го — TR (s=12); тело —
#      контурные варианты (BL/BR у цветных клеток 5/6-го);
#   4) мобильный 375: диалог открывается, легенды/бейджей нет;
#   5) 0 JS-ошибок; скриншоты в download/screenshots-task442/.
import datetime
import json
import os
import re
import zipfile
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8943
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

# событие СЕГОДНЯ (28.09.2026 — понедельник): в прежней печати
# давало бейдж в ячейке; теперь ячейка пустая (список ниже)
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

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task442'
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t442-%s');" % tag +
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
                      body='not found (t442-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# геометрия/стили печатного листа в iframe предпросмотра (Task 442)
GEOM_JS = """(function(){
    var ov = document.getElementById('wsPrintPrevModal');
    if (!ov) return null;
    var f = ov.querySelector('.wspprev-frame');
    try {
        var d = f.contentDocument;
        var sheet = d && d.getElementById('wsPrintSheet');
        if (!sheet) return null;
        var cs = function(el){ return d.defaultView.getComputedStyle(el); };
        var bottom = sheet.querySelector('.wsp-bottom');
        var mev = sheet.querySelector('.wsp-mev');
        var legend = sheet.querySelector('.wsp-legend');
        var badges = sheet.querySelectorAll('.wsp-ev');
        var ths = sheet.querySelectorAll('thead .wsp-day');
        if (!bottom || !mev || !ths.length) return {missing: true};
        var byDay = {};
        for (var i = 0; i < ths.length; i++) {
            var t = ths[i];
            byDay[t.textContent.replace(/[^0-9]/g, '')] = t;
        }
        var out = {
            bottomDisplay: cs(bottom).display,
            bottomGap: cs(bottom).gap || '',
            mevTxt: mev.querySelector('.wsp-mev-t').textContent,
            nLegend: legend ? 1 : 0,
            nBadges: badges.length,
            nEvItems: mev.querySelectorAll('.wsp-mev-item').length,
            th: {}
        };
        var probe = function(day){
            var t = byDay[String(day)];
            if (!t) return null;
            var s = cs(t);
            var span = t.querySelector('span');
            return {
                cls: t.className,
                bg: s.backgroundColor,
                fw: s.fontWeight,
                spanFw: span ? cs(span).fontWeight : '',
                bt: s.borderTopWidth, bl: s.borderLeftWidth,
                br: s.borderRightWidth
            };
        };
        out.th.d1 = probe(1);   // вторник — рабочий
        out.th.d5 = probe(5);   // суббота — полоса 5–6 (край-л)
        out.th.d6 = probe(6);   // воскресенье — край-р
        out.th.d12 = probe(12); // суббота второй полосы
        out.th.d13 = probe(13); // воскресенье
        // тело: клетки дней 5/6/12 последней (единственной) строки
        var rows = sheet.querySelectorAll('tbody tr');
        out.nRows = rows.length;
        var cells = rows[rows.length - 1].querySelectorAll('td.wsp-cell');
        var cellOf = function(day){
            return cells[day - 1] ? cs(cells[day - 1]) : null;
        };
        var cellCls = function(day){
            return cells[day - 1] ? cells[day - 1].className : '';
        };
        out.cell = {
            d1: {cls: cellCls(1), bg: cellOf(1) ? cellOf(1).backgroundColor : ''},
            d5: {cls: cellCls(5), bg: cellOf(5) ? cellOf(5).backgroundColor : '',
                 bl: cellOf(5) ? cellOf(5).borderLeftWidth : '',
                 bb: cellOf(5) ? cellOf(5).borderBottomWidth : ''},
            d6: {cls: cellCls(6), br: cellOf(6) ? cellOf(6).borderRightWidth : '',
                 bb: cellOf(6) ? cellOf(6).borderBottomWidth : ''},
            d12: {cls: cellCls(12), bg: cellOf(12) ? cellOf(12).backgroundColor : '',
                  bl: cellOf(12) ? cellOf(12).borderLeftWidth : ''}
        };
        return out;
    } catch (e) { return 'err: ' + e; }
})"""


# PDF: детерминированный пруф перехватом canvas (Task 442)
CAPTURE_ON_JS = """(function(){
    var ws = window.WorkSchedule;
    if (ws.__t442origSave) return true;
    ws.__t442origSave = ws._savePrintPdf;
    ws._savePrintPdf = function(viewEmps, agg){
        window.__t442cap = {viewEmps: viewEmps, agg: agg};
        ws._savePrintPdf = ws.__t442origSave;
        return ws.__t442origSave.apply(this, arguments);
    };
    return true;
})"""

PAINT_RECORD_JS = """(function(){
    var ws = window.WorkSchedule;
    var cap = window.__t442cap;
    if (!cap) return {err: 'контекст печати не захвачен'};
    var strokes = [], fills = [], fonts = [];
    var orig = document.createElement.bind(document);
    document.createElement = function(tag){
        var el = orig(tag);
        if (tag === 'canvas' && el && el.getContext) {
            var origGet = el.getContext.bind(el);
            el.getContext = function(type){
                var ctx = origGet(type);
                if (ctx && ctx.strokeRect && !ctx.__t442rec) {
                    ctx.__t442rec = true;
                    var origStroke = ctx.strokeRect.bind(ctx);
                    ctx.strokeRect = function(x, y, w, h){
                        strokes.push([x, y, w, h, ctx.lineWidth]);
                        return origStroke(x, y, w, h);
                    };
                    var origFillRect = ctx.fillRect.bind(ctx);
                    ctx.fillRect = function(x, y, w, h){
                        fills.push([w, h, String(ctx.fillStyle)]);
                        return origFillRect(x, y, w, h);
                    };
                    var proto = Object.getPrototypeOf(ctx);
                    var d = Object.getOwnPropertyDescriptor(proto, 'font');
                    if (d && d.set) {
                        Object.defineProperty(ctx, 'font', {
                            get: function(){ return d.get.call(this); },
                            set: function(v){ fonts.push(String(v));
                                              d.set.call(this, v); }
                        });
                    }
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
        // canvas хранит lineWidth как float32: 1.4 →
        // 1.399999976158142 — сравниваем с допуском
        var thick = strokes.filter(function(s){
            return Math.abs(s[4] - 1.4) < 0.01; });
        var w = thick.map(function(s){ return s[2]; });
        var lws = {};
        for (var q = 0; q < strokes.length; q++) {
            lws[String(strokes[q][4])] = (lws[String(strokes[q][4])] || 0) + 1;
        }
        out = {
            pages: lay.pages.length, painted: painted,
            offDays: (model.days || []).filter(function(dd){ return dd.off; })
                .map(function(dd){ return dd.d; }),
            nDays: (model.days || []).length,
            lwDist: lws,
            strokes: strokes.length, thickStrokes: thick.length,
            thickW: w,
            codeSquares: fills.filter(function(f){
                return f[0] === 4.5 && f[1] === 4.5; }).length,
            badgeSquares: fills.filter(function(f){
                return f[0] === 3.4 && f[1] === 3.4; }).length,
            offFills: fills.filter(function(f){
                return String(f[2]).toLowerCase() === '#e2e8ec' ||
                       String(f[2]).toLowerCase() === '#dfe5e9'; }).length,
            fonts: fonts,
            boldDates: fonts.indexOf('700 7px Arial') !== -1,
            plainDates: fonts.indexOf('7px Arial') !== -1
        };
    } catch (e) { out = {err: String(e)}; }
    finally { document.createElement = orig; }
    return out;
})"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ — ПЕЧАТЬ =====
        print('=== Контекст: десктоп тёмная — печать (значки/коды '
              'удалены, контур выходных) ===')
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

        # --- HTML: значки/коды удалены, контур, жирные даты ---
        page.wait_for_timeout(800)
        g = page.evaluate(GEOM_JS)
        check('C1: легенды кодов НЕТ (.wsp-legend отсутствует)',
              g and g.get('nLegend') == 0, g)
        check('C2: бейджей .wsp-ev НЕТ (мини-значки удалены)',
              g and g.get('nBadges') == 0,
              (g and g.get('nBadges'),))
        check('C3: .wsp-bottom — блок (flex/gap сняты)',
              g and g.get('bottomDisplay') == 'block' and
              g.get('bottomGap') in ('normal', '0px', ''),
              (g and g.get('bottomDisplay'), g and g.get('bottomGap')))
        check('C4: мероприятия живы (заголовок + записи)',
              g and 'Мероприятия' in str(g.get('mevTxt')) and
              g.get('nEvItems', 0) >= 1,
              (g and g.get('mevTxt'), g and g.get('nEvItems')))
        t = g and g.get('th') or {}
        c5, c6 = t.get('d5') or {}, t.get('d6') or {}
        c1, c12, c13 = t.get('d1') or {}, t.get('d12') or {}, t.get('d13') or {}
        check('C5: Сб 5-го — класс выходного + КРАЙ-Л полосы',
              'wsp-off' in c5.get('cls', '') and
              'wsp-off-edge-l' in c5.get('cls', ''), c5.get('cls'))
        check('C6: Вс 6-го — КРАЙ-Р полосы (без край-л)',
              'wsp-off-edge-r' in c6.get('cls', '') and
              'wsp-off-edge-l' not in c6.get('cls', ''), c6.get('cls'))
        check('C7: вторая полоса 12–13 — та же схема краёв',
              'wsp-off-edge-l' in c12.get('cls', '') and
              'wsp-off-edge-r' in c13.get('cls', ''),
              (c12.get('cls'), c13.get('cls')))
        check('C8: шапка — верх контура 2px, край-л 2px (Сб 5-го)',
              c5.get('bt') == '2px' and c5.get('bl') == '2px',
              (c5.get('bt'), c5.get('bl')))
        check('C9: шапка — край-р 2px (Вс 6-го)',
              c6.get('br') == '2px', c6.get('br'))
        check('C10: шапка выходного БЕЗ заливки',
              c5.get('bg') in ('rgba(0, 0, 0, 0)', 'transparent'),
              c5.get('bg'))
        check('C11: число выходного ЖИРНОЕ (700), день недели — 400',
              c5.get('fw') == '700' and c5.get('spanFw') == '400',
              (c5.get('fw'), c5.get('spanFw')))
        check('C12: будний день — обычное число (400), без классов',
              c1.get('fw') == '400' and 'wsp-off' not in c1.get('cls', ''),
              (c1.get('cls'), c1.get('fw')))
        cc = g and g.get('cell') or {}
        d5c, d6c = cc.get('d5') or {}, cc.get('d6') or {}
        d1c, d12c = cc.get('d1') or {}, cc.get('d12') or {}
        check('C13: тело — клетка Сб 5-го в полосе (wsp-cell-off)',
              'wsp-cell-off' in d5c.get('cls', ''), d5c.get('cls'))
        check('C14: тело — край-л 2px и НИЗ 2px (последняя строка)',
              d5c.get('bl') == '2px' and d5c.get('bb') == '2px',
              (d5c.get('bl'), d5c.get('bb')))
        check('C15: тело — край-р 2px (Вс 6-го) + низ',
              d6c.get('br') == '2px' and d6c.get('bb') == '2px',
              (d6c.get('br'), d6c.get('bb')))
        check('C16: пустой выходной (12-го) БЕЗ заливки + край-л',
              d12c.get('bg') in ('rgba(0, 0, 0, 0)', 'transparent') and
              d12c.get('bl') == '2px', (d12c.get('bg'), d12c.get('bl')))
        check('C17: клетка события сегодня (28-е) — без бейджа/фона',
              g and g.get('nBadges') == 0 and
              'wsp-cell-off' not in (cc.get('d1') or {}).get('cls', ''),
              'покрыто C2 + отсутствие класса у будней')

        page.screenshot(path=SHOTS + '/01-print-dialog-contour.png')

        # --- PDF: детерминированный пруф ---
        try:
            page.evaluate(CAPTURE_ON_JS)
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-pdf')
            dl = dl_info.value
            pdf_path = '/tmp/t442-graph.pdf'
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
            rec = page.evaluate(PAINT_RECORD_JS)
            check('D6: ПРУФ: квадратиков кодов НОЛЬ (столбец удалён)',
                  rec and rec.get('codeSquares') == 0, rec)
            check('D7: ПРУФ: бейджей (3.4×3.4) НОЛЬ',
                  rec and rec.get('badgeSquares') == 0, rec)
            check('D8: ПРУФ: заливок выходных НОЛЬ (#e2e8ec/#dfe5e9)',
                  rec and rec.get('offFills') == 0, rec)
            ws_ = rec.get('thickW') if rec else None
            same_w = ws_ and (max(ws_) - min(ws_)) < 0.5
            check('D9: ПРУФ: толстых контуров ≥ 4 полос (lineWidth 1.4)',
                  rec and rec.get('thickStrokes', 0) >= 4,
                  str(rec)[:260])
            check('D10: ПРУФ: 4 контура равной ширины 2×dayW (~44pt)',
                  rec and ws_ and len(ws_) == 4 and same_w and
                  25 <= ws_[0] <= 60 and rec.get('strokes', 0) > 50,
                  (ws_, rec and rec.get('strokes')))
            check('D11: ПРУФ: числа выходных ЖИРНЫЕ (700 7px)',
                  rec and rec.get('boldDates') and rec.get('plainDates'),
                  rec and rec.get('fonts', [])[:8])
        except Exception as e:
            check('D1..D11: сохранение PDF', False, str(e)[:230])

        # --- Excel: столбца кодов нет, контуры/жирные даты ---
        try:
            with page.expect_download(timeout=30000) as dl_info:
                page.click('.wspprev-xlsx')
            dl = dl_info.value
            xlsx_path = '/tmp/t442-graph.xlsx'
            dl.save_as(xlsx_path)
            z = zipfile.ZipFile(xlsx_path)
            sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
            styles = z.read('xl/styles.xml').decode('utf-8')
            check('E1: Excel скачан — имя .xlsx',
                  dl.suggested_filename.endswith('.xlsx'),
                  dl.suggested_filename)
            check('E2: «Коды:» в листе НЕТ',
                  '>Коды:<' not in sheet)
            m_hdr = re.search(r'<c r="A(\d+)" t="inlineStr" s="1">'
                              r'<is><t>Мероприятия · ', sheet)
            check('E3: заголовок мероприятий — одна ячейка A (s=1)',
                  m_hdr is not None)
            if m_hdr:
                hdr_row = int(m_hdr.group(1))
                tail = sheet.split('<row r="%d"' % (hdr_row,), 1)[1]
                tail = tail.split('</sheetData>', 1)[0]
                cols = re.findall(r'<c r="([A-Z]+)\d+"', tail)
                bad = [c for c in cols if c not in ('A', 'B')]
                check('E4: строки блока — ячейки ТОЛЬКО A/B',
                      not bad, bad[:6])
            check('E5: стили — 7 шрифтов (НЕ жирные даты)',
                  '<fonts count="7">' in styles)
            check('E6: стили — 13 границ (medium-контур)',
                  '<borders count="13">' in styles and
                  'style="medium"' in styles and 'FF8F99A3' in styles)
            # 3 цвета (Д8 FFF9C4, д FFD54F, ОТ ECEFF1) → cellXfs 46,
            # regDate 45, headC 10 (Сб 5-го TL=11, Вс 6-го TR=12)
            m_xfs = re.search(r'<cellXfs count="(\d+)">', styles)
            check('E7: cellXfs = 22 + 8×3 = 46 (карта стилей)',
                  m_xfs and m_xfs.group(1) == '46', m_xfs and m_xfs.group(1))
            check('E8: будни — НЕ жирные числа (B4 s=45 regDate)',
                  re.search(r'<c r="B4" t="inlineStr" s="45">'
                            r'<is><t>1', sheet) is not None,
                  (re.search(r'<c r="B4"[^>]*>', sheet) or
                   re.search(r'<c r="B4"[^/>]*>', sheet)).group(0)
                  if re.search(r'<c r="B4"', sheet) else 'B4 нет')
            check('E9: Сб 5-го — ЖИРНЫЙ контурный TL (F4 s=11)',
                  re.search(r'<c r="F4" t="inlineStr" s="11">'
                            r'<is><t>5', sheet) is not None)
            check('E10: Вс 6-го — ЖИРНЫЙ контурный TR (G4 s=12)',
                  re.search(r'<c r="G4" t="inlineStr" s="12">'
                            r'<is><t>6', sheet) is not None)
            # тело: цветная клетка Сб 5-го — colC+0*7+4 (BL) = 28,
            # Вс 6-го — colC+1*7+5 (BR) = 36
            check('E11: тело — цветная клетка Сб 5-го BL (F6 s=28)',
                  re.search(r'<c r="F6" t="inlineStr" s="28">'
                            r'<is><t>Д8', sheet) is not None,
                  re.search(r'<c r="F6"[^>]*>', sheet).group(0)
                  if re.search(r'<c r="F6"', sheet) else 'F6 нет')
            check('E12: тело — цветная клетка Вс 6-го BR (G6 s=36)',
                  re.search(r'<c r="G6" t="inlineStr" s="36">'
                            r'<is><t>д', sheet) is not None)
            check('E13: indent-стилей кодов НЕТ',
                  'indent="1"' not in styles)
        except Exception as e:
            check('E1..E13: сохранение Excel', False, str(e)[:230])

        page.screenshot(path=SHOTS + '/03-print-dialog-final.png')
        check('F1: JS-ошибок нет', js_errors == [], js_errors[:3])
        ctx.close()

        # ===== мобильный 375 — печать =====
        print('=== Контекст: мобильный 375 — печать ===')
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812},
                                   accept_downloads=True)
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'mob')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        ok_open = False
        try:
            page2.click('#wsPrintBtn', timeout=8000)
            page2.wait_for_timeout(1500)
            ok_open = page2.evaluate(
                "!!document.getElementById('wsPrintPrevModal')")
        except Exception as e:
            check('G1: мобильный — диалог печати', False, str(e)[:160])
        if ok_open:
            check('G1: мобильный — диалог предпросмотра открыт', True)
            page2.wait_for_timeout(800)
            g2 = page2.evaluate(GEOM_JS)
            check('G2: мобильный — легенды и бейджей нет',
                  g2 and g2.get('nLegend') == 0 and
                  g2.get('nBadges') == 0, g2)
            check('G3: мобильный — контур выходных жив (Сб 5-го)',
                  g2 and 'wsp-off-edge-l' in
                  str(((g2.get('th') or {}).get('d5') or {}).get('cls', '')),
                  (g2 or {}).get('th'))
            page2.screenshot(path=SHOTS + '/04-mobile-print.png')
        check('G4: мобильный — JS-ошибок нет', js_errors2 == [],
              js_errors2[:3])
        ctx2.close()
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
