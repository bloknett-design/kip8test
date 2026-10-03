#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 467: browser-check — ФИКС окна предпросмотра печати списка
# мероприятий: лист больше НЕ смещён вправо за границу окна.
# Заявка: «В окне предпросмотра печати списка мероприятий, лист со
# списком смещён вправо за границу окна предпросмотра.»
# ПРИЧИНА: iframe наследовал альбомные 1063px (.wspprev-frame
# Task 430), _eventsPrevFit масштабирует 794px + paper
# overflow:hidden → flex-центрированный лист уезжал вправо
# (сдвиг ~134px), правый край срезался.
# ФИКС: класс wsev-prev-frame → CSS width 794px (приём
# wst-prev-frame Task 449).
# ПРОВЕРКИ (мок-сервер, порт 8999):
#   A: широкий вьюпорт (1600) — k=1: iframe 794px, paper 794px,
#      лист в iframe: left ≈ 0 (БЫЛО ~134), right ≈ 794 (влезает),
#      визуальные края листа == краям paper (без выхода за границу);
#   B: узкий вьюпорт (800) — k<1: масштаб жив, paper == frame*k,
#      лист по-прежнему в границах;
#   C: содержимое листа (заголовок/таблица) + кнопки диалога;
#   D: Esc — диалог закрыт, инжект снят; 0 JS-ошибок.
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
                        '..', 'download', 'kip8test-task467')

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
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(-100), 'дата_окончания': d(4), 'состояние': ''},
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
          (('  [' + str(extra)[:260] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


# Геометрия диалога предпросмотра списка мероприятий: iframe
# (CSS width), paper, лист ВНУТРИ iframe (координаты viewport'а
# iframe) + визуальные края листа (paper.left + sheet*k)
def prev_geom(page):
    return page.evaluate("""(() => {
        const ov = document.getElementById('wsEventsPrevModal');
        if (!ov) return {open: false};
        const paper = ov.querySelector('.wspprev-paper');
        const frame = ov.querySelector('.wspprev-frame');
        if (!paper || !frame) return {open: true, noDom: true};
        const pr = paper.getBoundingClientRect();
        const fr = frame.getBoundingClientRect();
        const cs = getComputedStyle(frame);
        const doc = frame.contentDocument;
        const sheet = doc ? doc.getElementById('wsPrintSheet') : null;
        const sr = sheet ? sheet.getBoundingClientRect() : null;
        const vw = frame.clientWidth;
        // визуальные края листа: origin top-left, transform scale(k)
        // (инлайновый style — computed отдаёт matrix, не scale)
        const m = frame.style.transform || '';
        let k = 1;
        const km = /scale\\(([0-9.]+)\\)/.exec(m);
        if (km) k = parseFloat(km[1]);
        const visL = sheet ? pr.left + sr.left * k : null;
        const visR = sheet ? pr.left + sr.right * k : null;
        const title = doc ? doc.querySelector('.wsev-title') : null;
        const tables = doc ? doc.querySelectorAll('.wsev-table').length : 0;
        const rows = doc ? doc.querySelectorAll('.wsev-table tbody tr').length : 0;
        return {open: true,
                cssW: cs.width, clientW: vw,
                frameW: +fr.width.toFixed(1), paperW: +pr.width.toFixed(1),
                paperL: +pr.left.toFixed(1), paperR: +pr.right.toFixed(1),
                sheetL: sr ? +sr.left.toFixed(1) : null,
                sheetR: sr ? +sr.right.toFixed(1) : null,
                sheetW: sr ? +sr.width.toFixed(1) : null,
                visL: visL !== null ? +visL.toFixed(1) : null,
                visR: visR !== null ? +visR.toFixed(1) : null,
                k: k, hasSheet: !!sheet,
                title: title ? title.textContent.trim() : '',
                tables: tables, rows: rows};})()""")


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t467');" +
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

        print('== A: широкий вьюпорт (k=1) — лист в границах окна ==')
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(1200)
        g = prev_geom(page)
        check('диалог открыт, paper + frame на месте',
              g.get('open') and not g.get('noDom'), g)
        check('CSS iframe: 794px (фикс wsev-prev-frame)',
              g.get('cssW') == '794px', g)
        check('iframe viewport 794px (было 1063 — причина сдвига)',
              g.get('clientW') == 794, g)
        check('paper == frame (794px): mismatch <= 1.5',
              abs((g.get('paperW') or 0) - (g.get('frameW') or 9)) <= 1.5, g)
        check('лист в iframe: left ≈ 0 (БЫЛО ~134px справа-сдвиг)',
              g.get('sheetL') is not None and g.get('sheetL') <= 2, g)
        check('лист в iframe: right <= 794 (правый край НЕ срезан)',
              g.get('sheetR') is not None and g.get('sheetR') <= 795, g)
        check('лист занимает всю ширину viewport (~794)',
              g.get('sheetW') is not None and g.get('sheetW') >= 788, g)
        check('визуальный левый край листа == paper.left (±3)',
              g.get('visL') is not None and
              abs(g['visL'] - g['paperL']) <= 3, g)
        check('визуальный правый край листа <= paper.right + 2 (в границах)',
              g.get('visR') is not None and g['visR'] <= g['paperR'] + 2, g)
        shot(page, 'a-preview-wide.png')

        print('== B: содержимое листа + кнопки диалога ==')
        check('заголовок листа «Мероприятия»', g.get('title') == 'Мероприятия', g)
        check('таблицы листа есть (мероприятия + возможно СИЗ)',
              g.get('tables', 0) >= 1, g)
        check('строки мероприятий заполнены',
              g.get('rows', 0) >= 3, g)
        btns = page.evaluate("""(() => {
            const ov = document.getElementById('wsEventsPrevModal');
            return ov ? [...ov.querySelectorAll('.wspprev-btn')]
                       .map(b => b.textContent.trim()) : [];})()""")
        check('кнопки: Печать / Сохранить PDF / Сохранить Excel / Отмена',
              btns == ['Печать', 'Сохранить PDF', 'Сохранить Excel', 'Отмена'], btns)
        hint = page.evaluate("""(() => {
            const ov = document.getElementById('wsEventsPrevModal');
            const h = ov ? ov.querySelector('.wspprev-hint') : null;
            return h ? h.textContent.trim() : '';})()""")
        check('подсказка «A4 · книжная»', hint == 'A4 · книжная', hint)

        print('== C: узкий вьюпорт (800px, k<1) — масштаб жив, лист в границах ==')
        page.set_viewport_size({'width': 800, 'height': 700})
        page.wait_for_timeout(700)
        g2 = prev_geom(page)
        check('узкий: iframe CSS остаётся 794px',
              g2.get('cssW') == '794px', g2)
        check('узкий: масштаб применён (k<1, frame < 794)',
              g2.get('k') is not None and g2['k'] < 1 and g2['frameW'] < 794, g2)
        check('узкий: paper == frame*k (mismatch <= 2)',
              abs((g2.get('paperW') or 0) - (g2.get('frameW') or 9)) <= 2, g2)
        check('узкий: лист в iframe всё так же left ≈ 0',
              g2.get('sheetL') is not None and g2['sheetL'] <= 2, g2)
        check('узкий: визуальный правый край листа <= paper.right + 2',
              g2.get('visR') is not None and g2['visR'] <= g2['paperR'] + 2, g2)
        shot(page, 'c-preview-narrow.png')

        print('== D: закрытие диалога, чистота ==')
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        st = page.evaluate("""(() => ({
            dlg: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        check('Esc: диалог закрыт, инжект снят',
              (not st['dlg']) and (not st['inj']), st)
        check('0 JS-ошибок на странице', len(js_errors) == 0, js_errors)

        browser.close()
    server.shutdown()
    print('\nИТОГ Task 467 browser-check: %d OK / %d FAIL' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
