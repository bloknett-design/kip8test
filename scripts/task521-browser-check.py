#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 521 browser-check: малая форма д/н Табеля — время вместо часов:
#  A) клик по ячейке дневного работника → код «д» → форма с полями
#     «Время начала/окончания работ» (type=time, префилл 07:30/15:30)
#     + янтарная строка «Переработка: 8 ч» (#wsDnCalc);
#  B) изменение времени окончания → строка ПЕРЕСЧИТЫВАЕТСЯ на лету
#     (15:12 → «Переработка: 7,2 ч»);
#  C) «Готово» → правка в _PENDING с АВТОРАСЧЁТОМ часов (7,2),
#     попап закрыт, поле «часы» — число;
#  D) работа через полночь: 20:00–04:00 → «8 ч (через полночь)»,
#     Готово → часы 8;
#  E) ошибки: одинаковое время → тост, форма остаётся, правки нет;
#  F) сменному код «д» — БЕЗ формы (сразу применяется);
#  G) старого поля #wsDnHours в DOM нет; 0 JS-ошибок; скриншоты.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8997
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
DAY = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 11)))
DAY2 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 12)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task521')
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


CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'д', 'name': 'День в вых./праздник', 'color': '#FFD54F'},
  {'code': 'н', 'name': 'Ночь в вых./праздник', 'color': '#78909C'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2'},
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
ENTRIES = []
TRAININGS = []
PPE = []


def mock_response(action, body):
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
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


CELL_SEL = """((p) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + p.tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    return row.querySelector('td[data-day="' + p.day + '"]');})"""


def click_cell(page, tab, day):
    # day — НОМЕР ДНЯ месяца (data-day="11", не ISO)
    box = page.evaluate(CELL_SEL, {'tab': tab, 'day': day})
    if not box:
        return False
    page.evaluate("""((p) => {
        const empCell = document.querySelector(
            'td.ws-emp-col[data-tab="' + p.tab + '"]');
        const td = empCell.closest('tr')
            .querySelector('td[data-day="' + p.day + '"]');
        td.dispatchEvent(new MouseEvent('click',
            {bubbles: true, cancelable: true}));})""",
        {'tab': tab, 'day': day})
    return True


def click_code_row(page, code):
    # строка кода в попапе: .ws-popup-row, где .ws-popup-code = code
    return page.evaluate("""((c) => {
        const rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (let i = 0; i < rows.length; i++) {
            const codeEl = rows[i].querySelector('.ws-popup-code');
            if (codeEl && codeEl.textContent.trim() === c) {
                rows[i].dispatchEvent(new MouseEvent('click',
                    {bubbles: true, cancelable: true}));
                return true;
            }
        }
        return false;})""", code)


def form_state(page):
    return page.evaluate("""(() => {
        const s = document.getElementById('wsDnStart');
        const e = document.getElementById('wsDnEnd');
        const c = document.getElementById('wsDnCalc');
        const old = document.getElementById('wsDnHours');
        return {start: s ? s.value : null,
                startType: s ? s.type : null,
                end: e ? e.value : null,
                calc: c ? c.textContent.trim() : null,
                oldField: !!old,
                form: !!document.querySelector('#wsCellPopup .ws-dn-form')};})""")


def pending(page):
    return page.evaluate("""(() => {
        const p = window.WorkSchedule && WorkSchedule._PENDING || {};
        const out = {};
        Object.keys(p).forEach(function(k) { out[k] = p[k]; });
        return out;})""")


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t521');" +
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
        page.wait_for_timeout(1500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        # ===== A: форма д у дневного =====
        print('== A: дневной + «д» — форма времени с префиллом ==')
        check('A: ячейка кликнута, попап кодов открыт',
              click_cell(page, '023', '11') and
              page.evaluate("""(() => !!document.querySelector(
                  '#wsCellPopup .ws-popup-row'))()"""))
        check('A: строка «д» кликнута', click_code_row(page, 'д'))
        page.wait_for_timeout(300)
        st = form_state(page)
        shot(page, 'a-form-prefill.png')
        check('A: поля времени в DOM (type=time)',
              st['form'] and st['startType'] == 'time', st)
        check('A: префилл 07:30/15:30 (дефолт 8 ч)',
              st['start'] == '07:30' and st['end'] == '15:30', st)
        check('A: строка расчёта «Переработка: 8 ч»',
              st['calc'] == 'Переработка: 8 ч', st)
        check('A: старого поля #wsDnHours нет', not st['oldField'])

        # ===== B: живой пересчёт =====
        print('== B: живой пересчёт строки ==')
        page.fill('#wsDnStart', '08:00')
        page.fill('#wsDnEnd', '15:12')
        page.wait_for_timeout(200)
        st = form_state(page)
        check('B: 08:00–15:12 → «Переработка: 7,2 ч»',
              st['calc'] == 'Переработка: 7,2 ч', st)
        shot(page, 'b-live-recalc.png')

        # ===== C: Готово → авторасчёт в _PENDING =====
        print('== C: применение с авторасчётом ==')
        page.click('#wsCellPopup .ws-dn-ok')
        page.wait_for_timeout(300)
        pend = pending(page)
        key = DAY + '|023'
        check('C: правка в _PENDING', key in pend, pend)
        if key in pend:
            check('C: код «д», часы 7,2 (авторасчёт из минут)',
                  pend[key]['статус'] == 'д' and
                  abs(pend[key]['часы'] - 7.2) < 1e-9, pend[key])
        check('C: попап закрыт (формы нет)',
              not page.evaluate("""(() => !!document.querySelector(
                  '#wsCellPopup .ws-dn-form'))()"""))

        # ===== D: через полночь =====
        print('== D: работа через полночь ==')
        click_cell(page, '023', '12')
        page.wait_for_timeout(200)
        click_code_row(page, 'д')
        page.wait_for_timeout(300)
        page.fill('#wsDnStart', '20:00')
        page.fill('#wsDnEnd', '04:00')
        page.wait_for_timeout(200)
        st = form_state(page)
        check('D: 20:00–04:00 → «8 ч (через полночь)»',
              st['calc'] == 'Переработка: 8 ч (через полночь)', st)
        shot(page, 'd-overnight.png')
        page.click('#wsCellPopup .ws-dn-ok')
        page.wait_for_timeout(300)
        pend = pending(page)
        key2 = DAY2 + '|023'
        check('D: часы 8 в _PENDING (полночь +24 ч)',
              key2 in pend and abs(pend[key2]['часы'] - 8) < 1e-9,
              pend.get(key2))

        # ===== E: одинаковое время — тост, правки нет =====
        print('== E: ошибка одинакового времени ==')
        pend_before = pending(page)
        click_cell(page, '023', '11')
        page.wait_for_timeout(200)
        click_code_row(page, 'д')
        page.wait_for_timeout(300)
        page.fill('#wsDnStart', '08:00')
        page.fill('#wsDnEnd', '08:00')
        page.wait_for_timeout(200)
        page.click('#wsCellPopup .ws-dn-ok')
        page.wait_for_timeout(400)
        toast = page.evaluate("""(() => {
            const t = document.getElementById('toast');
            const m = document.getElementById('toastMessage');
            return {show: !!(t && t.classList.contains('show')),
                    msg: m ? m.textContent : ''};})()""")
        check('E: тост про совпадение времени',
              toast['show'] and 'совпадает' in toast['msg'], toast)
        check('E: форма остаётся (правка не применена)',
              page.evaluate("""(() => !!document.querySelector(
                  '#wsCellPopup .ws-dn-form'))()"""))
        pend_after = pending(page)
        check('E: _PENDING не изменился', pend_before == pend_after)
        shot(page, 'e-error-toast.png')
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)

        # ===== F: сменному — без формы =====
        print('== F: сменный + «д» — сразу, без формы ==')
        click_cell(page, '017', '11')
        page.wait_for_timeout(200)
        check('F: строка «д» кликнута (сменный)',
              click_code_row(page, 'д'))
        page.wait_for_timeout(300)
        st = form_state(page)
        check('F: формы времени НЕТ (сменному — 12 ч без вопроса)',
              not st['form'], st)
        pend = pending(page)
        key3 = DAY + '|017'
        check('F: код применён сразу, часы null (12 в итогах по типу)',
              key3 in pend and pend[key3]['статус'] == 'д' and
              pend[key3]['часы'] is None, pend.get(key3))

        check('G: JS-ошибок нет (кроме 404-моков)', len(js_errors) == 0,
              js_errors[:5])

        browser.close()
        server.shutdown()

    print()
    print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


main()
