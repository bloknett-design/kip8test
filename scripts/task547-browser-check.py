#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 547 browser-check: табель учёта — смена периода отпуска:
#  A) сетка рендерит ВОССТАНОВЛЕННЫЕ смены отпускника (сервер-фикс:
#     дни, освобождённые от отпуска, — Д/Н, не пустые; отпуск 11–12);
#  B) свип устаревших авто-«д»/«н» (реестр Task 458 в localStorage):
#     _PENDING получает __delete/__autoStale на обе подмены,
#     «Сохранить (2)» видим, ячейки подмен рендерятся ПУСТЫМИ;
#  C) «Сохранить» → workSchedule.deleteEntry ×2 (точные payload),
#     правки отправлены, после перезагрузки сетки ячейки пусты,
#     _PENDING пуст, кнопка «Сохранить» скрыта;
#  D) «Сформировать» (Текущий месяц) → тост со счётчиками Task 547:
#     «возвращено смен из отпусков 4», «снято замещений 1»;
#  E) идемпотентность свипа после сохранения (повторный рендер — 0
#     правок); 0 JS-ошибок; скриншоты.
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
D = lambda n: '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, n)))
MK = '%04d-%02d' % (Y, M)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task547')
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
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': D(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'сменный',
   'смена': 2, 'шаблон_ротации': 1, 'старт_цикла': D(3),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '031', 'ФИО': 'Сидоров Сидор Сидорович', 'тип': 'сменный',
   'смена': 3, 'шаблон_ротации': 1, 'старт_цикла': D(7),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

def E(day, tab, status, source):
    return {'дата': D(day), 'таб_номер': tab, 'статус': status,
            'переработка': 0, 'праздник': 0, 'источник': source,
            'дата_обновления': '2026-10-20T08:00:00.000Z',
            'замещает': None, 'инструкция': None, 'комментарий': '',
            'часы': None, 'время_начала': None, 'время_окончания': None}

# Серверное состояние ПОСЛЕ генерации с фиксом Task 547:
# отпуск 017 был 05–10 (подмены сохранены), сместился на 11–12 —
# смены 05/06/09/10 ВОССТАНОВЛЕНЫ сервером, устаревшие подмены
# 023 «д» 05-го и 031 «н» 09-го ещё стоят записями «руч»
ENTRIES = [
    E(1, '017', 'Д', 'авто'), E(2, '017', 'Н', 'авто'),
    E(5, '017', 'Д', 'авто'), E(6, '017', 'Н', 'авто'),
    E(9, '017', 'Д', 'авто'), E(10, '017', 'Н', 'авто'),
    E(11, '017', 'ОТ', 'авто'), E(12, '017', 'ОТ', 'авто'),
    E(13, '017', 'Д', 'авто'), E(14, '017', 'Н', 'авто'),
    E(3, '023', 'Д', 'авто'), E(4, '023', 'Н', 'авто'),
    E(7, '023', 'Д', 'авто'), E(8, '023', 'Н', 'авто'),
    E(11, '023', 'Д', 'авто'), E(12, '023', 'Н', 'авто'),
    E(5, '023', 'д', 'руч'),            # устаревшая подмена (замещает пусто)
    E(7, '031', 'Д', 'авто'), E(8, '031', 'Н', 'авто'),
    E(11, '031', 'Д', 'авто'), E(12, '031', 'Н', 'авто'),
    E(9, '031', 'н', 'руч'),            # устаревшая подмена (замещает пусто)
]
VACATIONS = [
    {'id': 1, 'таб_номер': '017', 'часть': 1,
     'дата_начала': D(11), 'дата_окончания': D(12),
     'дней': 2, 'комментарий': ''},
]
TRAININGS = []
PPE = []
API_CALLS = []
GEN_RESPONSE = {'ok': True, 'data': {
    'generated': 0, 'updated': 4, 'removed': 0,
    'vacationRestored': 4, 'substitutionsRemoved': 1,
    'vacationGenerated': 2, 'vacationUpdated': 0, 'vacationsFound': 1,
    'vacationError': None, 'vacationDays': 2, 'trainingDays': 0,
    'eventGenerated': 0, 'eventRestored': 0, 'eventRemoved': 0,
    'removedShift': 0, 'warnings': [], 'perEmployee': {},
    'monthStart': D(1), 'daysInMonth': DIM}}


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
    if action == 'workSchedule.deleteEntry':
        API_CALLS.append({'action': 'deleteEntry', 'date': body.get('date'),
                          'таб_номер': body.get('таб_номер')})
        # реалистично: сервер удаляет строку — перезагрузка сетки
        # после «Сохранить» покажет ячейки ПУСТЫМИ
        for i, e in enumerate(ENTRIES):
            if e['дата'] == body.get('date') and \
               e['таб_номер'] == body.get('таб_номер'):
                ENTRIES.pop(i)
                break
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.generateMonth':
        API_CALLS.append({'action': 'generateMonth',
                          'year': body.get('year'), 'month': body.get('month')})
        return GEN_RESPONSE
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

CELL_TEXT = """((p) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + p.tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    const td = row.querySelector('td[data-day="' + p.day + '"]');
    return td ? td.textContent.trim() : null;})"""


def cell_text(page, tab, day):
    return page.evaluate(CELL_TEXT, {'tab': tab, 'day': day})


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
        # реестр авто-«д»/«н» Task 458: подмены 05|023 и 09|031 были
        # материализованы планом и СОХРАНЕНЫ прошлой сессией.
        # ВАЖНО: isolateLocalStorage ставит приложению префикс 'kip8test:'
        # — ключ реестра пишется С ПРЕФИКСОМ
        reg = json.dumps({MK: {D(5) + '|023': 1, D(9) + '|031': 1}},
                         ensure_ascii=False)
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:ws_auto_dn_keys')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t547');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            "localStorage.setItem('kip8test:ws_auto_dn_keys'," + json.dumps(reg) + ");")

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

        # ===== A: восстановленные смены отпускника в сетке =====
        print('== A: смены 017 восстановлены одним «Сформировать» ==')
        a5 = cell_text(page, '017', '5')
        a6 = cell_text(page, '017', '6')
        a9 = cell_text(page, '017', '9')
        a10 = cell_text(page, '017', '10')
        check('A: 05-е — «Д» (был «ОТ», стал пустым до фикса)', a5 == 'Д', a5)
        check('A: 06-е — «Н»', a6 == 'Н', a6)
        check('A: 09-е — «Д»', a9 == 'Д', a9)
        check('A: 10-е — «Н»', a10 == 'Н', a10)
        check('A: 11-е — «ОТ» (смещённый отпуск)', cell_text(page, '017', '11') == 'ОТ')
        check('A: 12-е — «ОТ»', cell_text(page, '017', '12') == 'ОТ')
        check('A: 13-е — «Д» (график жив)', cell_text(page, '017', '13') == 'Д')
        shot(page, '01-grid-restored-shifts.png')

        # ===== B: свип устаревших подмен =====
        print('== B: свип устаревших авто-«д»/«н» ==')
        pend = pending(page)
        k5, k9 = D(5) + '|023', D(9) + '|031'
        check('B: «д» 05|023 под __delete', pend.get(k5, {}).get('__delete') is True,
              pend)
        check('B: флаг свипа __autoStale',
              pend.get(k5, {}).get('__autoStale') is True, pend)
        check('B: «н» 09|031 под __delete', pend.get(k9, {}).get('__delete') is True,
              pend)
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsSaveBtn');
            return b ? {hidden: b.hidden, text: b.textContent.trim()} : null;})()""")
        check('B: кнопка «Сохранить (2)»', btn and not btn['hidden'] and
              btn['text'] == 'Сохранить (2)', btn)
        check('B: ячейка подмены 023 05-е рендерится ПУСТОЙ',
              cell_text(page, '023', '5') == '', cell_text(page, '023', '5'))
        check('B: ячейка подмены 031 09-е рендерится ПУСТОЙ',
              cell_text(page, '031', '9') == '', cell_text(page, '031', '9'))
        shot(page, '02-sweep-pending-save2.png')

        # ===== C: Сохранить → deleteEntry на сервер =====
        print('== C: «Сохранить» — удаление записей подмен ==')
        page.click('#wsSaveBtn')
        page.wait_for_timeout(2500)
        dels = [c for c in API_CALLS if c['action'] == 'deleteEntry']
        check('C: deleteEntry ×2', len(dels) == 2, API_CALLS)
        check('C: payload «д» 05|023',
              any(c['date'] == D(5) and c['таб_номер'] == '023' for c in dels), dels)
        check('C: payload «н» 09|031',
              any(c['date'] == D(9) and c['таб_номер'] == '031' for c in dels), dels)
        pend = pending(page)
        check('C: _PENDING пуст после сохранения', not pend, pend)
        check('C: ячейка 023 05-е пуста (сервер удалил)',
              cell_text(page, '023', '5') == '', cell_text(page, '023', '5'))
        check('C: ячейка 031 09-е пуста (сервер удалил)',
              cell_text(page, '031', '9') == '', cell_text(page, '031', '9'))
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsSaveBtn');
            return b ? {hidden: b.hidden, text: b.textContent.trim()} : null;})()""")
        check('C: кнопка «Сохранить» скрыта', btn and btn['hidden'], btn)
        shot(page, '03-after-save-deleted.png')

        # ===== D: идемпотентность свипа после сохранения =====
        print('== D: повторный рендер — свип молчит ==')
        page.evaluate("WorkSchedule._renderGrid()")
        page.wait_for_timeout(500)
        pend = pending(page)
        check('D: новых правок нет (идемпотентность)', not pend, pend)

        # ===== E: «Сформировать» — тост со счётчиками Task 547 =====
        print('== E: тост генерации со счётчиками ==')
        page.click('#wsGenerateBtn')
        page.wait_for_timeout(400)
        alt = page.evaluate("""(() => {
            const b = document.querySelector('.kip-dialog-alt');
            if (b) { b.click(); return b.textContent.trim(); }
            return null;})()""")
        check('E: диалог «Сформировать» открыт, выбран месяц', alt is not None, alt)
        page.wait_for_timeout(1500)
        t = toast_text(page)
        check('E: тост «возвращено смен из отпусков 4»',
              'возвращено смен из отпусков 4' in t, t)
        check('E: тост «снято замещений 1»', 'снято замещений 1' in t, t)
        shot(page, '04-generate-toast-counters.png')

        check('Z: 0 JS-ошибок', not js_errors, js_errors)

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
