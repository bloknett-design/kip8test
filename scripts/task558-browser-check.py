#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 558 browser-check: шахматка — мероприятия И/ОБ/ПЗ в ячейках
# НЕ влияют на логику определения подменных дней (заявка):
#  A) сетка рендерится: план отпуска 017 («О»), смены 023/031
#     записями, бейджи мероприятий И/ОБ/ПР в ячейках;
#  B) СОСЕД-МЕРОПРИЯТИЕ: запись «И» у 023 в дне 6 НЕ блокирует
#     примыкание — подмена «д» 023 в дне 5 стоит (правка _PENDING,
#     рамка ws-manual-dn, маркер ws-auto-dn, реестр localStorage);
#  C) МЕРОПРИЯТИЕ В ДНЕ ПОДМЕНЫ: запись «ОБ» у 031 в дне 3 —
#     кандидат, подмена «д» ПОВЕРХ записи (правка со статусом «д»,
#     материализация поверх серверной записи-мероприятия);
#  D) ПР-БЛОКЕР (прогул — отсутствие, НЕ мероприятие): запись «ПР»
#     у 031 в дне 11 — ячейка занята, подмены в дне 11 НЕТ ни у
#     кого (023 — рабочая «Д»): pending без ключа, ячейка «ПР»;
#  E) тост «Авто: N кодов „д“/„н“ (замещение отпуска)»,
#     кнопка «Сохранить (N)»; 0 JS-ошибок; скриншоты.
#
# Данные (текущий месяц, старты циклов с 1-го числа):
#   017 отпускник, цикл 2 «Д В» (потенциальные смены «Д» — нечётные);
#   023 кандидат,  цикл 4 «В В Д Д» (выходные 1,2,5,6,9,10,…);
#   031 кандидат,  цикл 4 «Д Д В В» (выходные 3,4,7,8,11,12,…);
#   отпуск 017 — весь месяц ПЛАНОМ листа «Отпуска» (записей нет);
#   записи: смены 023/031 («Д», авто), И 6|023, ОБ 3|031, ПР 11|031.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8995
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
D = lambda n: '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, n)))
MK = '%04d-%02d' % (Y, M)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task558')
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
  {'code': 'И', 'name': 'Инструктаж', 'color': '#B3E5FC'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#D1C4E9'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'},
  {'code': 'ПР', 'name': 'Прогул', 'color': '#EF5350'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': D(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'сменный',
   'смена': 2, 'шаблон_ротации': 2, 'старт_цикла': D(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '031', 'ФИО': 'Сидоров Сидор Сидорович', 'тип': 'сменный',
   'смена': 3, 'шаблон_ротации': 3, 'старт_цикла': D(1),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Отпускник Д/В', 'cycle': 2, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': ''}]},
  {'id': 2, 'name': 'Кандидат В В Д Д', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': ''}, {'day': 2, 'status': ''},
            {'day': 3, 'status': 'Д'}, {'day': 4, 'status': 'Д'}]},
  {'id': 3, 'name': 'Кандидат Д Д В В', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Д'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]


def E(day, tab, status, source):
    return {'дата': D(day), 'таб_номер': tab, 'статус': status,
            'переработка': 0, 'праздник': 0, 'источник': source,
            'дата_обновления': '2026-10-20T08:00:00.000Z',
            'замещает': None, 'инструкция': None, 'комментарий': '',
            'часы': None, 'время_начала': None, 'время_окончания': None}


# Сформированный месяц: смены 023/031 записями «Д» (авто) в рабочих
# днях по циклу; мероприятия: И 6|023 (сосед дня подмены 5),
# ОБ 3|031 (в самом дне подмены 3), ПР 11|031 (прогул — блокер)
ENTRIES = []
for d in range(1, DIM + 1):
    if (d - 1) % 4 in (2, 3):        # 023: В В Д Д → рабочие 3,4,7,8,…
        ENTRIES.append(E(d, '023', 'Д', 'авто'))
    if (d - 1) % 4 in (0, 1):        # 031: Д Д В В → рабочие 1,2,5,6,…
        ENTRIES.append(E(d, '031', 'Д', 'авто'))
ENTRIES.append(E(6, '023', 'И', 'авто'))    # сосед дня подмены 5
ENTRIES.append(E(3, '031', 'ОБ', 'авто'))   # день подмены 3
ENTRIES.append(E(11, '031', 'ПР', 'авто'))  # прогул — блокер дня 11
VACATIONS = [
    {'id': 1, 'таб_номер': '017', 'часть': 1,
     'дата_начала': D(1), 'дата_окончания': D(DIM),
     'дней': DIM, 'комментарий': ''},
]
TRAININGS = []
PPE = []
API_CALLS = []


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
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


CELL_TEXT = """((p) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + p.tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    const td = row.querySelector('td[data-day="' + p.day + '"]');
    return td ? td.textContent.trim() : null;})"""

CELL_INFO = """((p) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + p.tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    const td = row.querySelector('td[data-day="' + p.day + '"]');
    if (!td) return null;
    return {
        text: td.textContent.trim(),
        manualDn: td.classList.contains('ws-manual-dn'),
        autoDn: td.classList.contains('ws-auto-dn'),
        hasEvents: td.classList.contains('ws-has-events'),
        vacPlan: td.classList.contains('ws-vac-plan'),
        badge: (function() {
            const b = td.querySelector('.ws-ev-badge');
            return b ? b.textContent.trim() : '';
        })()
    };})"""


def cell_text(page, tab, day):
    return page.evaluate(CELL_TEXT, {'tab': tab, 'day': day})


def cell_info(page, tab, day):
    return page.evaluate(CELL_INFO, {'tab': tab, 'day': day})


def pending(page):
    return page.evaluate("""(() => {
        const p = window.WorkSchedule && WorkSchedule._PENDING || {};
        const out = {};
        Object.keys(p).forEach(function(k) { out[k] = p[k]; });
        return out;})()""")


def toast_text(page):
    return page.evaluate("""(() => {
        const m = document.getElementById('toastMessage');
        return m ? m.textContent.trim() : '';})()""")


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
        # чистый localStorage (кэш/права/реестр Task 458), тёмная тема;
        # ВАЖНО: isolateLocalStorage ставит префикс 'kip8test:' —
        # ключ реестра пишется С ПРЕФИКСОМ
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:ws_auto_dn_keys')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t558');" +
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

        # ===== A: сетка и бейджи мероприятий =====
        print('== A: сетка рендерится, план отпуска, бейджи ==')
        check('A: смена 023 д.4 — «Д» (запись)', cell_text(page, '023', '4') == 'Д')
        check('A: смена 031 д.2 — «Д» (запись)', cell_text(page, '031', '2') == 'Д')
        # план отпуска 017: «ОТ» + бейдж плановой смены «Д» (Task 305 —
        # отпуск в приоритете, смена рядом), ws-vac-plan — пунктир
        i17 = cell_info(page, '017', '3')
        check('A: план отпуска 017 д.3 — «ОТ» + бейдж смены «Д»',
              i17 and i17['text'] in ('ОТ', 'ОТД') and i17['vacPlan'], i17)
        i6 = cell_info(page, '023', '6')
        check('A: И 6|023 — бейдж мероприятия в ячейке',
              i6 and i6['badge'] == 'И' and i6['hasEvents'], i6)
        i11 = cell_info(page, '031', '11')
        check('A: ПР 11|031 — бейдж прогулa в ячейке',
              i11 and i11['badge'] == 'ПР' and i11['hasEvents'], i11)
        shot(page, '01-grid-events-badges.png')

        # ===== B: сосед-мероприятие НЕ блокирует подмену =====
        print('== B: «И» соседом — подмена «д» 023 в дне 5 ==')
        i5 = cell_info(page, '023', '5')
        check('B: д.5 023 — «д» (подмена при соседе-«И»)',
              i5 and i5['text'] == 'д', i5)
        check('B: рамка ws-manual-dn (правка как ручной ввод)',
              i5 and i5['manualDn'], i5)
        check('B: маркер ws-auto-dn (реестр слоя)',
              i5 and i5['autoDn'], i5)
        pend = pending(page)
        k5 = D(5) + '|023'
        check('B: правка _PENDING д.5|023 со статусом «д»',
              pend.get(k5, {}).get('статус') == 'д', pend)
        check('B: флаг __autoDn материализации',
              pend.get(k5, {}).get('__autoDn') is True, pend)
        shot(page, '02-subst-with-event-neighbor.png')

        # ===== C: подмена ПОВЕРХ записи-мероприятия =====
        print('== C: «д» 031 в дне 3 поверх записи «ОБ» ==')
        i3 = cell_info(page, '031', '3')
        check('C: д.3 031 — «д» (подмена поверх мероприятия)',
              i3 and i3['text'] == 'д', i3)
        check('C: рамка ws-manual-dn', i3 and i3['manualDn'], i3)
        k3 = D(3) + '|031'
        check('C: правка _PENDING д.3|031 со статусом «д»',
              pend.get(k3, {}).get('статус') == 'д', pend)
        check('C: флаг __autoDn', pend.get(k3, {}).get('__autoDn') is True, pend)
        shot(page, '03-subst-over-event-cell.png')

        # ===== D: ПР-блокер — подмены в дне 11 НЕТ =====
        print('== D: прогул 11|031 — ячейка занята, подмены нет ==')
        pend = pending(page)
        k11 = D(11) + '|031'
        k11023 = D(11) + '|023'
        check('D: правки на д.11|031 НЕТ (прогул занимает ячейку)',
              k11 not in pend, pend)
        check('D: правки на д.11|023 НЕТ (рабочая смена)',
              k11023 not in pend, pend)
        check('D: ячейка 11|031 — бейдж «ПР» (не перезаписана)',
              i11 and i11['badge'] == 'ПР', i11)
        check('D: ячейка 11|023 — «Д» (смена, не кандидат)',
              cell_text(page, '023', '11') == 'Д', cell_text(page, '023', '11'))
        shot(page, '04-pr-blocker-no-subst.png')

        # ===== E: тост, кнопка, реестр, 0 ошибок =====
        print('== E: тост/кнопка/реестр ==')
        t = toast_text(page)
        check('E: тост «Авто: … кодов «д»/«н» (замещение отпуска)»',
              ('Авто:' in t and '«д»/«н»' in t and 'замещение отпуска' in t), t)
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsSaveBtn');
            return b ? {hidden: b.hidden, text: b.textContent.trim()} : null;})()""")
        check('E: кнопка «Сохранить (N)» видима, N ≥ 4',
              btn and not btn['hidden'] and
              btn['text'].startswith('Сохранить (') and
              int(btn['text'].rstrip(')').split('(')[1]) >= 4, btn)
        # изолированный localStorage префиксует ЛЮБОЙ ключ — реестр
        # живёт под 'kip8test:ws_auto_dn_keys' (обращение из evaluate
        # без префикса), пробуем оба варианта
        reg = page.evaluate("""(() => {
            const keys = ['ws_auto_dn_keys', 'kip8test:ws_auto_dn_keys'];
            for (const k of keys) {
                try {
                    const v = JSON.parse(localStorage.getItem(k) || '{}');
                    if (v && Object.keys(v).length) return v;
                } catch (e) {}
            }
            return {};})()""")
        mreg = (reg or {}).get(MK, {})
        check('E: реестр содержит д.5|023', mreg.get(k5) == 1, reg)
        check('E: реестр содержит д.3|031', mreg.get(k3) == 1, reg)
        check('E: реестр НЕ содержит д.11|031', mreg.get(k11) is None, reg)
        shot(page, '05-toast-registry.png')

        check('Z: 0 JS-ошибок', not js_errors, js_errors)

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
