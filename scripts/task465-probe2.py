#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 465: probe-2 — геометрия значков (3px от краёв), пара
# [раскрытие][печать], диалог печати списка: предпросмотр, кнопки,
# закрытие, инжект-стиль. Порт 8998.
import datetime
import json
import calendar
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]

def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
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
]
ENTRIES = [
  {'id': 1, 'дата': d(-6), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
]
TRAININGS = [
  {'id': 80, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-12), 'дата_окончания': d(-12), 'таб_номер': '017', 'подразделение': ''},
  {'id': 81, 'тема': 'Обучение по новой редакции инструкций', 'тип': 'обучение',
   'дата_начала': d(-9), 'дата_окончания': d(-7), 'таб_номер': '018', 'подразделение': ''},
  {'id': 82, 'тема': 'Целевой инструктаж при допуске к работам повышенной опасности',
   'тип': 'инструктаж', 'дата_начала': d(-1), 'дата_окончания': d(1),
   'таб_номер': '023', 'подразделение': ''},
  {'id': 83, 'тема': 'Проверка знаний в объёме должностных обязанностей',
   'тип': 'проверка_знаний', 'дата_начала': d(2), 'дата_окончания': d(3),
   'таб_номер': '017', 'подразделение': ''},
  {'id': 84, 'тема': 'Инструктаж по пожарной безопасности', 'тип': 'инструктаж',
   'дата_начала': d(5), 'дата_окончания': d(9), 'таб_номер': '018', 'подразделение': ''},
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(-100), 'дата_окончания': d(4), 'состояние': ''},
  {'id': 2, 'таб_номер': '023', 'наименование': 'Перчатки диэлектрические',
   'дата_выдачи': d(-60), 'дата_окончания': 'До износа', 'состояние': ''},
]

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
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': PPE}}
    if action == 'workSchedule.listEntries':
        if body and body.get('month') == M:
            return {'ok': True, 'data': {'entries': ENTRIES}}
        return {'ok': True, 'data': {'entries': []}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    import threading
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','probe-t465b');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            url = request.url
            action = ''
            if 'action=' in url:
                action = unquote(url.split('action=')[1].split('&')[0])
            pd_ = request.post_data
            body = {}
            if pd_:
                try:
                    body = json.loads(pd_)
                except Exception:
                    body = {}
            resp = mock_response(action, body)
            return route.fulfill(status=200,
                                 content_type='application/json; charset=utf-8',
                                 body=json.dumps(resp, ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1800)

        info = page.evaluate("""(() => {
            const out = {errors: []};
            for (const id of ['wsEventsPanel', 'wsCalPanel']) {
                const el = document.getElementById(id);
                if (!el) { out[id] = null; continue; }
                const btn = el.querySelector('.ws-bar-exp');
                const prn = el.querySelector('.ws-bar-print');
                const er = el.getBoundingClientRect();
                const br = btn ? btn.getBoundingClientRect() : null;
                const pr = prn ? prn.getBoundingClientRect() : null;
                out[id] = {
                    hidden: el.hidden,
                    hasBtn: !!btn, hasPrint: !!prn,
                    btnDisplay: btn ? getComputedStyle(btn).display : null,
                    prnDisplay: prn ? getComputedStyle(prn).display : null,
                    btnTop: br ? +(br.top - er.top).toFixed(2) : null,
                    btnRight: br ? +(er.right - br.right).toFixed(2) : null,
                    btnW: br ? +br.width.toFixed(1) : null,
                    prnTop: pr ? +(pr.top - er.top).toFixed(2) : null,
                    prnRight: pr ? +(er.right - pr.right).toFixed(2) : null,
                    prnW: pr ? +pr.width.toFixed(1) : null,
                    prnH: pr ? +pr.height.toFixed(1) : null,
                    gapBtnToPrn: (br && pr) ? +(br.right - pr.left).toFixed(2) : null,
                    capPad: getComputedStyle(el.querySelector('.ws-ep-cap, .ws-cp-cap') || el).paddingRight
                };
            }
            const cap = document.querySelector('#wsEventsPanel .ws-ep-cap');
            out.evCapPad = cap ? getComputedStyle(cap).paddingRight : null;
            const ncap = document.querySelector('#wsCalPanel .ws-cp-cap');
            out.calCapPad = ncap ? getComputedStyle(ncap).paddingRight : null;
            return out;})()""")
        print(json.dumps(info, ensure_ascii=False, indent=1))

        # клик по значку печати → диалог
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(1200)
        dlg = page.evaluate("""(() => {
            const ov = document.getElementById('wsEventsPrevModal');
            if (!ov) return {open: false};
            const t = ov.querySelector('.wspprev-title');
            const s = ov.querySelector('.wspprev-sub');
            const btns = [...ov.querySelectorAll('.wspprev-btn')].map(b => b.textContent.trim());
            const hint = ov.querySelector('.wspprev-hint');
            const sheet = document.getElementById('wsPrintSheet');
            return {open: true, title: t ? t.textContent : '',
                    sub: s ? s.textContent : '', btns: btns,
                    hint: hint ? hint.textContent : '',
                    sheetClass: sheet ? sheet.className : null,
                    sheetHasTable: sheet ? !!sheet.querySelector('table.wsev-table') : false,
                    sheetRows: sheet ? sheet.querySelectorAll('table.wsev-table tbody tr').length : 0,
                    injStyle: !!document.getElementById('wsEventsPrintStyle')};})()""")
        print('DIALOG:', json.dumps(dlg, ensure_ascii=False))

        # содержимое iframe
        frame_txt = page.evaluate("""(() => {
            const ov = document.getElementById('wsEventsPrevModal');
            const fr = ov ? ov.querySelector('.wspprev-frame') : null;
            if (!fr || !fr.contentDocument) return null;
            const d = fr.contentDocument;
            return {title: d.title,
                    rows: d.querySelectorAll('table.wsev-table tbody tr').length,
                    ppeCap: !!d.querySelector('.wsev-cap'),
                    bg: d.defaultView.getComputedStyle(d.documentElement).backgroundColor};})()""")
        print('IFRAME:', json.dumps(frame_txt, ensure_ascii=False))
        page.screenshot(path='/home/z/my-project/download/t465-probe-dialog.png')

        # закрыть по Esc
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        closed = page.evaluate("""(() => ({
            dialog: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        print('AFTER ESC:', json.dumps(closed))

        # повторное открытие: СИЗ-секция в листе/iframe + скачивания
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(900)
        with_ppe = page.evaluate("""(() => {
            const sheet = document.getElementById('wsPrintSheet');
            const ov = document.getElementById('wsEventsPrevModal');
            const fr = ov ? ov.querySelector('.wspprev-frame') : null;
            const d = fr && fr.contentDocument;
            return {sheetCap: sheet ? !!sheet.querySelector('.wsev-cap') : false,
                    sheetPpeRows: sheet ? sheet.querySelectorAll('table.wsev-table')[1].querySelectorAll('tbody tr').length : 0,
                    iframeCap: d ? !!d.querySelector('.wsev-cap') : false,
                    iframePpeRows: d && d.querySelectorAll('table.wsev-table')[1] ? d.querySelectorAll('table.wsev-table')[1].querySelectorAll('tbody tr').length : 0};})()""")
        print('WITH PPE:', json.dumps(with_ppe))

        # скачивание PDF
        with page.expect_download() as dl:
            page.click('#wsEventsPrevModal .wspprev-pdf')
        d1 = dl.value
        path1 = '/home/z/my-project/download/t465-probe-list.pdf'
        d1.save_as(path1)
        head1 = open(path1, 'rb').read(8)
        print('PDF:', d1.suggested_filename, 'magic:', head1[:5], 'size:', len(open(path1,'rb').read()))

        # скачивание XLSX
        with page.expect_download() as dl2:
            page.click('#wsEventsPrevModal .wspprev-xlsx')
        d2 = dl2.value
        path2 = '/home/z/my-project/download/t465-probe-list.xlsx'
        d2.save_as(path2)
        head2 = open(path2, 'rb').read(4)
        print('XLSX:', d2.suggested_filename, 'magic:', head2, 'size:', len(open(path2,'rb').read()))

        # взаимное исключение: открыть печать графика — список закрывается
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        page.click('#wsPrintBtn')
        page.wait_for_timeout(700)
        excl = page.evaluate("""(() => ({
            graph: !!document.getElementById('wsPrintPrevModal'),
            events: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        print('GRAPH OPEN:', json.dumps(excl))

        # и обратно: значок печати закрывает график (клик сквозь overlay
        # невозможен — закрываем Esc, потом сразу граф→список)
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        page.evaluate("WorkSchedule._openPrintPreview('<div>probe</div>', null)")
        page.wait_for_timeout(300)
        page.evaluate("WorkSchedule.printEventsList()")
        page.wait_for_timeout(700)
        excl2 = page.evaluate("""(() => ({
            graph: !!document.getElementById('wsPrintPrevModal'),
            events: !!document.getElementById('wsEventsPrevModal')}))()""")
        print('EVENTS REOPEN (graph was force-closed):', json.dumps(excl2))
        page.screenshot(path='/home/z/my-project/download/t465-probe-final.png')

        # скролл окна мероприятий — прикол обоих значков
        pinned = page.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            el.scrollTop = 40;
            el.dispatchEvent(new Event('scroll'));
            const b = el.querySelector('.ws-bar-exp').getBoundingClientRect();
            const p = el.querySelector('.ws-bar-print').getBoundingClientRect();
            const er = el.getBoundingClientRect();
            return {btnTop: +(b.top - er.top).toFixed(2),
                    prnTop: +(p.top - er.top).toFixed(2)};})()""")
        print('PINNED@scroll40:', json.dumps(pinned))
        print('JS errors:', js_errors)
        browser.close()
    server.shutdown()


if __name__ == '__main__':
    main()
