#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 486: browser-check — ТИХОЕ обновление данных табеля при
# открытии приложения (заявка: «помимо ручного обновления»):
#  A) чистый профиль: открыли приложение (ДАШБОРД, раздел не
#     открывали) → через 4 с сам собой тихо обновился: 7 экшенов
#     workSchedule.* ушли, копия kip8_ws_cache_v1 (LS-слой,
#     префикс kip8test:) записана со свежими записями текущего
#     вида; ТОСТА НЕТ («тихое»); KipPreload.ws НЕ дублирует сеть
#     (ожидание 25 с — очередь дошла до ws-элемента и пропустила);
#  B) УСТАРЕВШАЯ копия в LS: открыли приложение → подождали →
#     открыли табель → сетка из СВЕЖИХ данных (тихое обновление
#     опередило открытие), штамп «данные от …» — сегодня;
#  C) табель открыт ДО тихого обновления: сетка из устаревшей
#     копии («ОТ») → обновление прилетело → сетка ТИХО
#     перерисовалась сама («Д»), без тоста и «Загрузка…»;
#  D) ручное «Обновить» работает как прежде: клик → тост
#     «Данные графика обновлены»;
#  E) троттлинг: повторный KipAuth._schedulePreload() (фоновая
#     проверка сессии) в течение 5 минут — сеть не дёргается.
# КОНТЕКСТ: мок Apps Script (порт 8998), 0 JS-ошибок, скриншоты.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
YM = '%04d-%02d' % (Y, M)
DAY5 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 5)))
DAY6 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 6)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task486')
os.makedirs(SHOT_DIR, exist_ok=True)

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
          (('  [' + str(extra)[:240] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


# --- Данные мока ---
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#B3E5FC'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной',
   'смена': '', 'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
# СВЕЖИЕ записи (сервер): 017 — день 5 «Д», день 6 «Н»; 023 — день 5 «Д»
ENTRIES_FRESH = [
  {'id': 11, 'дата': DAY5, 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
  {'id': 12, 'дата': DAY6, 'таб_номер': '017', 'статус': 'Н', 'источник': 'авто'},
  {'id': 13, 'дата': DAY5, 'таб_номер': '023', 'статус': 'Д', 'источник': 'руч'},
]
# УСТАРЕВШАЯ копия (сид LS): 017 — день 5 «ОТ» (давно устарело)
ENTRIES_STALE = [
  {'id': 1, 'дата': DAY5, 'таб_номер': '017', 'статус': 'ОТ', 'источник': 'авто'},
]
TRAININGS = []
PPE = []

# счётчики экшенов (сеть мока)
WS_CALLS = {}


def mock_response(action, body):
    WS_CALLS[action] = WS_CALLS.get(action, 0) + 1
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': True}}}
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
        if body and body.get('month') == M and body.get('year') == Y:
            return {'ok': True, 'data': {'entries': ENTRIES_FRESH}}
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# УСТАРЕВШАЯ копия Task 314 (формат v1) для сида LS (сценарии B/C)
def stale_cache_js():
    cache = {
        'v': 1, 'codes': CODES, 'patterns': PATTERNS,
        'employees': EMPLOYEES,
        'vacations': {str(Y): []},
        'ppe': PPE, 'instrList': [], 'instrAll': [], 'eventsAll': [],
        'views': {YM: {'entries': ENTRIES_STALE, 'trainings': [],
                       'ts': 1000}}
    }
    return ("try{localStorage.setItem('kip8test:kip8_ws_cache_v1', %s)}"
            "catch(e){};" % json.dumps(json.dumps(cache, ensure_ascii=False)))


def ws_count(action):
    return WS_CALLS.get(action, 0)


CELL_JS = r"""((p) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + p.tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    const td = row.querySelector('td[data-day="' + p.day + '"]');
    if (!td) return null;
    return {text: (td.textContent || '').trim(),
            day: p.day};})"""


CACHE_JS = r"""(() => {
    try {
        const raw = localStorage.getItem('kip8_ws_cache_v1');
        if (!raw) return null;
        const c = JSON.parse(raw);
        const v = c.views && c.views['%s'];
        return {v: c.v, hasView: !!v,
                entries: v ? v.entries.length : 0,
                ts: v ? v.ts : 0,
                employees: (c.employees || []).length};
    } catch (e) { return null; }})""" % YM


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A: чистый профиль — тихое обновление при открытии ==')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t486');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            action = ''
            if 'action=' in request.url:
                action = unquote(request.url.split('action=')[1].split('&')[0])
            body = {}
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except Exception:
                    body = {}
            return route.fulfill(status=200,
                content_type='application/json; charset=utf-8',
                body=json.dumps(mock_response(action, body), ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2000)
        # мы на ДАШБОРДЕ: раздел табеля НЕ открывали
        check('A: приложение открыто, табель не тронут',
              ws_count('getCurrentUser') >= 1, WS_CALLS)
        check('A: до таймера 4 с сеть табеля молчит',
              ws_count('workSchedule.listEntries') == 0, WS_CALLS)
        page.wait_for_timeout(5000)  # 4с таймер + выполнение
        check('A: ТИХОЕ обновление сработало — 7 экшенов ушли',
              ws_count('workSchedule.getStatusCodes') == 1 and
              ws_count('workSchedule.getPatterns') == 1 and
              ws_count('workSchedule.listEmployees') == 1 and
              ws_count('workSchedule.listTrainings') == 1 and
              ws_count('workSchedule.listVacations') == 1 and
              ws_count('workSchedule.listPpe') == 1 and
              ws_count('workSchedule.listEntries') == 1, WS_CALLS)
        cache = page.evaluate(CACHE_JS)
        check('A: копия в LS записана (формат v1, текущий вид)',
              cache and cache['v'] == 1 and cache['hasView'], cache)
        check('A: в копии СВЕЖИЕ записи (3) и сотрудники (2)',
              cache and cache['entries'] == 3 and cache['employees'] == 2, cache)
        check('A: штамп вида свежий (последние 60 с)',
              cache and cache['ts'] > (page.evaluate('Date.now()') - 60000),
              cache)
        toast_a = page.evaluate("""(() => {
            const t = document.getElementById('toast');
            const m = document.getElementById('toastMessage');
            return {show: !!(t && t.classList.contains('show')),
                    msg: m ? m.textContent : ''};})()""")
        check('A: ТОСТА НЕТ — обновление ТИХОЕ',
              not toast_a['show'] and 'обновлены' not in toast_a['msg'], toast_a)
        # KipPreload.ws НЕ дублирует сеть: очередь доходит до ws-элемента
        # (~9 json × ≥1.5 с пауз) и ПРОПУСКАЕТ его — свежая _silentTs
        page.wait_for_timeout(18000)
        check('A: KipPreload.ws НЕ дублирует сеть (пропуск по метке)',
              ws_count('workSchedule.listEntries') == 1, WS_CALLS)
        check('A: 0 JS-ошибок', len(js_errors) == 0, js_errors)
        shot(page, 'a-dashboard-silent-refresh.png')
        ctx.close()

        # ==============================================================
        print('== B: устаревшая копия — тихое обновление опережает ==')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors_b = []
        page.on('pageerror', lambda e: js_errors_b.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t486b');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            stale_cache_js())
        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2000)
        page.wait_for_timeout(5000)  # тихое обновление при открытии
        # теперь открываем раздел — сетка должна быть из СВЕЖИХ данных
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1800)
        rows = page.evaluate(
            "document.querySelectorAll('#wsGridWrap tbody tr').length")
        check('B: сетка отрисована (2 сотрудника)', rows == 2, rows)
        cell = page.evaluate(CELL_JS, {'day': 5, 'tab': '017'})
        check('B: ячейка дня 5 — СВЕЖИЙ код «Д» (не устаревший «ОТ»)',
              cell and 'Д' in cell['text'] and 'ОТ' not in cell['text'], cell)
        stamp = page.evaluate(
            "document.getElementById('wsRefreshTipDate') ? " +
            "document.getElementById('wsRefreshTipDate').textContent : ''")
        check('B: штамп «данные от …» — свежая дата (не пустой)',
              stamp and 'ещё нет' not in stamp, stamp)
        cache_b = page.evaluate(CACHE_JS)
        check('B: копия обновлена тихим обновлением (3 записи)',
              cache_b and cache_b['entries'] == 3, cache_b)
        toast_b = page.evaluate("""(() => {
            const t = document.getElementById('toast');
            const m = document.getElementById('toastMessage');
            return {show: !!(t && t.classList.contains('show')),
                    msg: m ? m.textContent : ''};})()""")
        check('B: тоста не было (тихое обновление без фанфар)',
              not toast_b['show'], toast_b)
        check('B: 0 JS-ошибок', len(js_errors_b) == 0, js_errors_b)
        shot(page, 'b-open-after-silent.png')
        ctx.close()

        # ==============================================================
        print('== C: табель открыт ДО тихого обновления — тихая перерисовка ==')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors_c = []
        page.on('pageerror', lambda e: js_errors_c.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t486c');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            stale_cache_js())
        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(1500)  # bootstrap (медленный путь) — до 4 с
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)  # сетка из УСТАРЕВШЕЙ копии
        cell_before = page.evaluate(CELL_JS, {'day': 5, 'tab': '017'})
        check('C: ДО обновления — устаревший «ОТ» из локальной копии',
              cell_before and 'ОТ' in cell_before['text'], cell_before)
        page.wait_for_timeout(6000)  # 4с таймер + тихое обновление
        cell_after = page.evaluate(CELL_JS, {'day': 5, 'tab': '017'})
        check('C: ПОСЛЕ — сетка ТИХО перерисовалась сама («Д»)',
              cell_after and 'Д' in cell_after['text'] and 'ОТ' not in cell_after['text'], cell_after)
        loading = page.evaluate("""(() => {
            const w = document.getElementById('wsGridWrap');
            return !!(w && w.innerHTML.indexOf('flow-loading') !== -1);})()""")
        check('C: «Загрузка…» НЕ мигала (сетка оставалась на экране)',
              not loading)
        toast_c = page.evaluate("""(() => {
            const t = document.getElementById('toast');
            const m = document.getElementById('toastMessage');
            return {show: !!(t && t.classList.contains('show')),
                    msg: m ? m.textContent : ''};})()""")
        check('C: тоста НЕ было (тихая перерисовка)',
              not toast_c['show'] and 'обновлены' not in toast_c['msg'], toast_c)
        stamp_c = page.evaluate(
            "document.getElementById('wsRefreshTipDate') ? " +
            "document.getElementById('wsRefreshTipDate').textContent : ''")
        check('C: штамп обновился на свежий', stamp_c and 'ещё нет' not in stamp_c,
              stamp_c)
        check('C: 0 JS-ошибок', len(js_errors_c) == 0, js_errors_c)
        shot(page, 'c-silent-rerender.png')
        # --- D: ручное «Обновить» работает как прежде (на этом же табе)
        print('== D: ручное «Обновить» — тост как прежде ==')
        before = ws_count('workSchedule.listEntries')
        page.click('#wsRefreshBtn')
        page.wait_for_timeout(1200)
        toast_d = page.evaluate("""(() => {
            const t = document.getElementById('toast');
            const m = document.getElementById('toastMessage');
            return {show: !!(t && t.classList.contains('show')),
                    msg: m ? m.textContent : ''};})()""")
        check('D: сеть дёргается вручную (listEntries +1)',
              ws_count('workSchedule.listEntries') == before + 1, WS_CALLS)
        check('D: тост «Данные графика обновлены» показан',
              toast_d['show'] and 'обновлены' in toast_d['msg'], toast_d)
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsRefreshBtn');
            return {disabled: b ? b.disabled : null,
                    spin: b ? b.classList.contains('ws-refreshing') : null};})()""")
        check('D: кнопка разблокирована после обновления',
              btn and not btn['disabled'] and not btn['spin'], btn)
        shot(page, 'd-manual-refresh-toast.png')
        # --- E: троттлинг — повторный _schedulePreload не дёргает сеть
        print('== E: троттлинг 5 минут ==')
        before_e = ws_count('workSchedule.listEntries')
        page.evaluate("KipAuth._schedulePreload()")
        page.wait_for_timeout(7000)
        check('E: повторный старт внутри окна — сеть НЕ дёргается',
              ws_count('workSchedule.listEntries') == before_e, WS_CALLS)
        check('E: 0 JS-ошибок (итог C+D+E)', len(js_errors_c) == 0, js_errors_c)
        ctx.close()

        browser.close()
    server.shutdown()

    print('\n===== ИТОГ Task 486 browser-check: %d/%d (fail %d) ====='
          % (PASS, PASS + FAIL, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
