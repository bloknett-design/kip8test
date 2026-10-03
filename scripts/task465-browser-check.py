#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 465: browser-check — значки окон бара табеля (3px от краёв),
# значок печати списка мероприятий + диалог печати/сохранения
# (предпросмотр книжного A4, PDF/Excel), взаимное исключение
# диалогов, мобайл, пустой месяц, 0 JS-ошибок.
# Заявка: «В разделе Табель учёта рабочего времени, в окнах
# мероприятий и норм, значки "развернуть окно" сместить на
# расстояние от краёв окон на 3px сверху и справа. В окне
# мероприятий, справа от значка раскрытия окна сделай новый значок
# с иконкой принтера, форма кнопки квадратная и размером как кнопка
# раскрытия окна, при нажатии на эту кнопку должно появляться
# диалоговое окно печати и сохранения в форматах файлов, так же
# как в окне кнопки печати графика, с предпросмотром списка
# мероприятий, для дальнейшей печати или сохранения в файл списка
# мероприятий на текущий месяц.»
# КОНТЕКСТ (мок-сервер, порт 8999):
#   A: геометрия — оба окна: top/right gap = 3px; окно мероприятий:
#      ПАРА [раскрытие(28px)][печать(3px)], 22×22, зазор 3;
#      окно норм: ОДИН значок в 3px; паддинги плашек 52/26;
#   B: клик по печати → диалог wsEventsPrevModal: заголовок, подза-
#      головок «Мероприятия — месяц год г.», 4 кнопки + подсказка
#      «A4 · книжная», лист wsev-sheet, инжект-стиль, iframe с
#      таблицей и секцией СИЗ;
#   C: закрытие — Esc / «Отмена» / клик по затемнению: диалог и
#      инжект сняты;
#   D: скачивания — PDF (magic %PDF-, имя Мероприятия_Месяц_год),
#      Excel (magic PK);
#   E: взаимоисключение — печать графика закрывает список, список
#      закрывает график;
#   F: пустой месяц (ноябрь) — тост, диалога нет;
#   G: мобайл 375 — чип «Мероприятия», печать в 3px от угла;
#   H: уровень min — печать работает, записи мастеров скрыты.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'download', 'kip8test-task465')

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
  {'таб_номер': '031', 'ФИО': 'Мастер КипиА Тестовый', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА', 'комментарий': ''},
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
   'дата_начала': d(5), 'дата_окончания': d(9), 'таб_номер': '031', 'подразделение': ''},
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(-100), 'дата_окончания': d(4), 'состояние': ''},
  {'id': 2, 'таб_номер': '023', 'наименование': 'Перчатки диэлектрические',
   'дата_выдачи': d(-60), 'дата_окончания': 'До износа', 'состояние': ''},
]

MODE = {'level': 'edit'}   # edit | min


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        perms = {'workschedule.view': True}
        if MODE['level'] == 'edit':
            perms['workschedule.edit'] = True
        else:
            perms['workschedule.view.min'] = True
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': perms}}
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
          (('  [' + str(extra)[:220] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def geom(page, idp):
    return page.evaluate("""((id) => {
        const el = document.getElementById(id);
        if (!el) return null;
        const er = el.getBoundingClientRect();
        const btn = el.querySelector('.ws-bar-exp');
        const prn = el.querySelector('.ws-bar-print');
        const br = btn ? btn.getBoundingClientRect() : null;
        const pr = prn ? prn.getBoundingClientRect() : null;
        return {
            visible: !el.hidden && !!el.offsetParent,
            hasBtn: !!btn, hasPrint: !!prn,
            btnTop: br ? +(br.top - er.top).toFixed(2) : null,
            btnRight: br ? +(er.right - br.right).toFixed(2) : null,
            btnW: br ? +br.width.toFixed(1) : null,
            btnH: br ? +br.height.toFixed(1) : null,
            prnTop: pr ? +(pr.top - er.top).toFixed(2) : null,
            prnRight: pr ? +(er.right - pr.right).toFixed(2) : null,
            prnW: pr ? +pr.width.toFixed(1) : null,
            prnH: pr ? +pr.height.toFixed(1) : null,
            gap: (br && pr) ? +(pr.left - br.right).toFixed(2) : null,
            prnBefore: (br && pr) ? br.right < pr.left : null
        };})""", idp)


def dialog_state(page):
    return page.evaluate("""(() => {
        const ov = document.getElementById('wsEventsPrevModal');
        if (!ov) return {open: false};
        const t = ov.querySelector('.wspprev-title');
        const s = ov.querySelector('.wspprev-sub');
        const btns = [...ov.querySelectorAll('.wspprev-btn')].map(b => b.textContent.trim());
        const hint = ov.querySelector('.wspprev-hint');
        const fr = ov.querySelector('.wspprev-frame');
        const sheet = document.getElementById('wsPrintSheet');
        let ifr = null;
        try {
            const d = fr && fr.contentDocument;
            ifr = d ? {
                title: d.title,
                tables: d.querySelectorAll('table.wsev-table').length,
                rows: d.querySelectorAll('table.wsev-table tbody tr').length,
                ppeCap: !!d.querySelector('.wsev-cap')
            } : null;
        } catch (e) { ifr = 'xorigin'; }
        return {open: true,
                title: t ? t.textContent.trim() : '',
                sub: s ? s.textContent.trim() : '',
                btns: btns,
                hint: hint ? hint.textContent.trim() : '',
                sheetClass: sheet ? sheet.className : null,
                sheetTables: sheet ? sheet.querySelectorAll('table.wsev-table').length : 0,
                inj: !!document.getElementById('wsEventsPrintStyle'),
                iframe: ifr};})()""")


def toast_text(page):
    return page.evaluate("""(() => {
        const t = document.getElementById('toast');
        const m = document.getElementById('toastMessage');
        return {shown: !!(t && t.classList.contains('show')),
                text: m ? m.textContent : ''};})()""")


def main():
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t465');" +
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
        page.wait_for_timeout(1600)

        print('== A: геометрия значков ==')
        ev = geom(page, 'wsEventsPanel')
        cal = geom(page, 'wsCalPanel')
        check('окно мероприятий: пара значков (раскрытие + печать)',
              ev and ev['hasBtn'] and ev['hasPrint'], ev)
        check('печать СПРАВА от раскрытия (в углу)', ev and ev['prnBefore'] is True, ev)
        check('печать: 3px сверху и справа',
              ev and ev['prnTop'] == 3 and ev['prnRight'] == 3, ev)
        check('раскрытие: 3px сверху, 28px справа (сдвинуто влево)',
              ev and ev['btnTop'] == 3 and ev['btnRight'] == 28, ev)
        check('обе кнопки 22×22 (квадрат, размер раскрытия)',
              ev and ev['btnW'] == 22 and ev['btnH'] == 22 and
              ev['prnW'] == 22 and ev['prnH'] == 22, ev)
        check('зазор между значками 3px',
              ev and ev['gap'] == 3, ev)
        check('окно норм: ОДИН значок (печати нет)',
              cal and cal['hasBtn'] and not cal['hasPrint'], cal)
        check('окно норм: 3px сверху и справа',
              cal and cal['btnTop'] == 3 and cal['btnRight'] == 3, cal)
        caps = page.evaluate("""(() => {
            const a = document.querySelector('#wsEventsPanel .ws-ep-cap');
            const b = document.querySelector('#wsCalPanel .ws-cp-cap');
            return {ev: a ? getComputedStyle(a).paddingRight : null,
                    cal: b ? getComputedStyle(b).paddingRight : null};})()""")
        check('плашки-заголовки не прячутся: 52px/26px',
              caps['ev'] == '52px' and caps['cal'] == '26px', caps)
        shot(page, 'a-bar-icons.png')

        print('== B: диалог печати списка ==')
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(1100)
        st = dialog_state(page)
        check('диалог открыт (wsEventsPrevModal)', st['open'], st)
        check('заголовок «Предпросмотр печати»', st['title'] == 'Предпросмотр печати', st)
        check('подзаголовок «Мероприятия — месяц год г.»',
              st['sub'].startswith('Мероприятия — ') and 'г.' in st['sub'], st)
        check('кнопки: Печать / Сохранить PDF / Сохранить Excel / Отмена',
              st['btns'] == ['Печать', 'Сохранить PDF', 'Сохранить Excel', 'Отмена'], st)
        check('подсказка «A4 · книжная»', st['hint'] == 'A4 · книжная', st)
        check('лист #wsPrintSheet.wsev-sheet с таблицами', st['sheetClass'] == 'wsev-sheet' and st['sheetTables'] == 2, st)
        check('инжект-стиль книжной @page', st['inj'], st)
        check('iframe: standalone-документ с таблицей',
              st['iframe'] and st['iframe']['tables'] == 2, st['iframe'])
        check('iframe: строки списка (5 мероприятий + 1 СИЗ)',
              st['iframe'] and st['iframe']['rows'] == 6, st['iframe'])
        check('iframe: секция СИЗ', st['iframe'] and st['iframe']['ppeCap'], st['iframe'])
        shot(page, 'b-dialog.png')

        print('== C: закрытие ==')
        page.keyboard.press('Escape')
        page.wait_for_timeout(350)
        st2 = page.evaluate("""(() => ({
            dlg: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        check('Esc: диалог закрыт, инжект снят',
              (not st2['dlg']) and (not st2['inj']), st2)
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(700)
        page.click('#wsEventsPrevModal .wspprev-cancel', force=True)
        page.wait_for_timeout(350)
        st3 = page.evaluate("""(() => ({
            dlg: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        check('«Отмена»: закрыт + инжект снят', (not st3['dlg']) and (not st3['inj']), st3)
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(700)
        page.evaluate("""(() => {
            const ov = document.getElementById('wsEventsPrevModal');
            if (ov) ov.dispatchEvent(new MouseEvent('click', {bubbles: true}));})()""")
        page.wait_for_timeout(350)
        st4 = page.evaluate("""(() => ({
            dlg: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        check('клик по затемнению: диалог закрыт + инжект снят',
              (not st4['dlg']) and (not st4['inj']), st4)

        print('== D: скачивания PDF / Excel ==')
        page.evaluate("WorkSchedule.printEventsList()")
        page.wait_for_timeout(900)
        with page.expect_download() as dl1:
            page.click('#wsEventsPrevModal .wspprev-pdf', force=True)
        d1 = dl1.value
        p1 = os.path.join(SHOT_DIR, 'd-list.pdf')
        os.makedirs(SHOT_DIR, exist_ok=True)
        d1.save_as(p1)
        b1 = open(p1, 'rb').read()
        check('PDF: имя Мероприятия_Месяц_год.pdf',
              d1.suggested_filename.startswith('Мероприятия_') and
              d1.suggested_filename.endswith('.pdf'), d1.suggested_filename)
        check('PDF: magic %PDF-', b1[:5] == b'%PDF-', b1[:8])
        check('PDF: размер разумный (>10КБ)', len(b1) > 10000, len(b1))
        with page.expect_download() as dl2:
            page.click('#wsEventsPrevModal .wspprev-xlsx', force=True)
        d2 = dl2.value
        p2 = os.path.join(SHOT_DIR, 'd-list.xlsx')
        d2.save_as(p2)
        b2 = open(p2, 'rb').read()
        check('Excel: имя Мероприятия_Месяц_год.xlsx',
              d2.suggested_filename.startswith('Мероприятия_') and
              d2.suggested_filename.endswith('.xlsx'), d2.suggested_filename)
        check('Excel: magic PK (zip)', b2[:4] == b'PK\x03\x04', b2[:6])
        check('Excel: пакет книги (styles/sheet в архиве)',
              b'xl/styles.xml' in b2 and b'xl/worksheets/sheet1.xml' in b2)

        print('== E: взаимоисключение диалогов печати ==')
        page.keyboard.press('Escape')
        page.wait_for_timeout(350)
        page.click('#wsPrintBtn')
        page.wait_for_timeout(800)
        ex1 = page.evaluate("""(() => ({
            graph: !!document.getElementById('wsPrintPrevModal'),
            events: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        check('печать графика открыта, список закрыт + инжекта нет',
              ex1['graph'] and (not ex1['events']) and (not ex1['inj']), ex1)
        page.evaluate("WorkSchedule.printEventsList()")
        page.wait_for_timeout(800)
        ex2 = page.evaluate("""(() => ({
            graph: !!document.getElementById('wsPrintPrevModal'),
            events: !!document.getElementById('wsEventsPrevModal')}))()""")
        check('список мероприятий закрывает график',
              (not ex2['graph']) and ex2['events'], ex2)
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)

        print('== F: пустой месяц — тост, диалога нет ==')
        next_m = M + 1 if M < 12 else 1
        page.select_option('#wsMonthSel', str(next_m))
        page.wait_for_timeout(900)
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(800)
        stf = dialog_state(page)
        tf = toast_text(page)
        check('пустой месяц: диалог НЕ открыт', not stf['open'], stf)
        check('пустой месяц: тост «Нет мероприятий для печати»',
              'Нет мероприятий для печати' in tf['text'], tf)
        page.select_option('#wsMonthSel', str(M))
        page.wait_for_timeout(900)

        print('== G: мобайл 375 ==')
        page.set_viewport_size({'width': 375, 'height': 800})
        page.wait_for_timeout(600)
        page.click('#wsChipEvents')
        page.wait_for_timeout(700)
        evm = geom(page, 'wsEventsPanel')
        check('мобайл: окно мероприятий открыто чипом',
              evm and evm['visible'] and evm['hasPrint'], evm)
        check('мобайл: печать в 3px от угла', evm and evm['prnTop'] == 3 and evm['prnRight'] == 3, evm)
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(1000)
        stm = dialog_state(page)
        check('мобайл: диалог печати открывается', stm['open'], stm)
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        shot(page, 'g-mobile.png')
        page.set_viewport_size({'width': 1600, 'height': 1000})
        page.wait_for_timeout(500)

        print('== H: уровень min — мастера скрыты, печать работает ==')
        MODE['level'] = 'min'
        # кэш прав в localStorage переживает refreshData — перезагружаем
        # страницу с минимальными правами (view+min → уровень min)
        page.evaluate("""localStorage.setItem('kip8_my_access', JSON.stringify(
            {role: 'Админ', found: true,
             permissions: {'workschedule.view': true,
                           'workschedule.view.min': true}}))""")
        page.reload()
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)
        page.evaluate("WorkSchedule.printEventsList()")
        page.wait_for_timeout(900)
        sth = dialog_state(page)
        sheet_min = page.evaluate("""(() => {
            const s = document.getElementById('wsPrintSheet');
            return s ? s.querySelectorAll('table.wsev-table')[0]
                      .querySelectorAll('tbody tr').length : -1;})()""")
        # edit: 5 строк (мастер 031 в списке); min: 4 (мастер скрыт)
        check('min: диалог открыт', sth['open'], sth)
        check('min: запись мастера скрыта (4 вместо 5)', sheet_min == 4, sheet_min)
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        MODE['level'] = 'edit'

        print('== 0 JS-ошибок ==')
        check('JS-ошибок нет', not js_errors, js_errors[:3])

        browser.close()
    server.shutdown()
    print()
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    raise SystemExit(0 if FAIL == 0 else 1)


if __name__ == '__main__':
    main()
