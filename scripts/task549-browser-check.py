#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 549 browser-check: табель учёта — диалог «Очистить правки»
# с ВЫБОРОЧНЫМ удалением (заявка: «в диалоговом окне подтверждения
# удаления ручных правок сделай возможность удаления каждой правки
# по отдельности с кратким наименованием правок (пример краткого
# содержания — работник/дата правки/наименование правки)»):
#  A) кнопка «Очистить правки» видна редактору; сетка отражает
#     накладку: 023 05-е «В» (ручной выходной пользователя),
#     041 05-е «д» (сместившаяся подмена), 031 06-е «н»;
#  B) клик → НОВЫЙ диалог kipConfirmList: 3 строки-чекбокса
#     «РАБОТНИК · ДАТА · НАИМЕНОВАНИЕ» (Петров · 05.10.2026 ·
#     В — Выходной (вручную); Кузнецов · 05.10.2026 · д — день в
#     выходной; Сидоров · 06.10.2026 · н — ночь в выходной), серым
#     — тип (ручная запись на сервере / авто-подмена, материализо-
#     вана), счётчик «Выбрано: 3 из 3», тумблер «Снять все»,
#     danger-кнопка «Очистить правки»;
#  B2) галочка «н» 031 снята по одной → «Выбрано: 2 из 3», тумблер
#     «Выбрать все» → OK → _PENDING __delete ТОЛЬКО ×2 (05|023,
#     05|041); «н» 031 НЕ тронута (запись жива, метка реестра
#     ws_auto_dn_keys сохранена; у 05|041 метка снята), кнопка
#     «Сохранить (2)», тост «Очищено правок: 2»;
#  C) «Сохранить» → workSchedule.deleteEntry ×2 (точные payload)
#     → перезагрузка → план Task 456 расставляет «д» ЗАНОВО на
#     023 05-го; спрос 06-го ЗАКРЫТ живой «н» 031 → новых «н» НЕТ
#     → «Сохранить (1)»;
#  D) «Сохранить» → setManualEntry ×1 («д» 05|023) → финал: 023
#     05-е «д», 031 06-е «н» (выбранная к сохранению правка), 041
#     05-е ПУСТО, 017 05/06 «ОТ»; _PENDING пуст;
#  E) идемпотентность: повторный рендер — 0 новых правок;
#     0 JS-ошибок; скриншоты.
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
RU = lambda iso: iso[8:10] + '.' + iso[5:7] + '.' + iso[0:4]
MK = '%04d-%02d' % (Y, M)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task549')
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
  {'code': 'В', 'name': 'Выходной (вручную)', 'color': '#EEF0F2'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2'},
]
# Геометрия заявки (цикл 4: Д/Н/—/—):
#   017 старт 01-го: 05-е cyc1 «Д», 06-е cyc2 «Н» — ОТПУСК 05–06
#   023 старт 02-го: 05-е ВЫХОДНОЙ (кандидат «д»), 06-е cyc1 «Д»
#   031 старт 04-го: 05-е cyc2 «Н» (работает), 06-е ВЫХОДНОЙ (кандидат «н»)
#   041 старт 02-го: как 023 — запасной кандидат «д» 05-го
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': D(1),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'сменный',
   'смена': 2, 'шаблон_ротации': 1, 'старт_цикла': D(2),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '031', 'ФИО': 'Сидоров Сидор Сидорович', 'тип': 'сменный',
   'смена': 3, 'шаблон_ротации': 1, 'старт_цикла': D(4),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '041', 'ФИО': 'Кузнецов Кузьма Кузьмич', 'тип': 'сменный',
   'смена': 4, 'шаблон_ротации': 1, 'старт_цикла': D(2),
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
            'дата_обновления': '2026-10-25T08:00:00.000Z',
            'замещает': None, 'инструкция': None, 'комментарий': '',
            'часы': None, 'время_начала': None, 'время_окончания': None}

# Накладка заявки: пользователь поставил 023 ручной выходной «В»
# на 05-е (ячейка кандидата занята) → план сместил подмену «д»
# на 041; «н» 031 на 06-м — на своём месте. Отпуск 017 05–06.
ENTRIES = [
    E(1, '017', 'Д', 'авто'), E(2, '017', 'Н', 'авто'),
    E(5, '017', 'ОТ', 'авто'), E(6, '017', 'ОТ', 'авто'),
    E(2, '023', 'Д', 'авто'), E(3, '023', 'Н', 'авто'),
    E(6, '023', 'Д', 'авто'),
    E(4, '031', 'Д', 'авто'), E(5, '031', 'Н', 'авто'),
    E(2, '041', 'Д', 'авто'), E(3, '041', 'Н', 'авто'),
    E(6, '041', 'Д', 'авто'),
    E(5, '023', 'В', 'руч'),            # ручной выходной — ЗАЯВКА
    E(5, '041', 'д', 'руч'),            # сместившаяся подмена (реестр)
    E(6, '031', 'н', 'руч'),            # подмена на месте (реестр)
]
VACATIONS = [
    {'id': 1, 'таб_номер': '017', 'часть': 1,
     'дата_начала': D(5), 'дата_окончания': D(6),
     'дней': 2, 'комментарий': ''},
]
TRAININGS = []
PPE = []
API_CALLS = []
GEN_RESPONSE = {'ok': True, 'data': {
    'generated': 0, 'updated': 0, 'removed': 0,
    'vacationRestored': 0, 'substitutionsRemoved': 0,
    'vacationGenerated': 0, 'vacationUpdated': 0, 'vacationsFound': 1,
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
        # реалистично: сервер удаляет строку
        for i, e in enumerate(ENTRIES):
            if e['дата'] == body.get('date') and \
               e['таб_номер'] == body.get('таб_номер'):
                ENTRIES.pop(i)
                break
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.setManualEntry':
        API_CALLS.append({'action': 'setManualEntry', 'date': body.get('date'),
                          'таб_номер': body.get('таб_номер'),
                          'статус': body.get('статус')})
        # реалистично: сервер создаёт/обновляет запись «руч»
        found = False
        for i, e in enumerate(ENTRIES):
            if e['дата'] == body.get('date') and \
               e['таб_номер'] == body.get('таб_номер'):
                ENTRIES[i]['статус'] = body.get('статус')
                ENTRIES[i]['источник'] = 'руч'
                found = True
                break
        if not found:
            ENTRIES.append(E(int(str(body.get('date')).split('-')[2]),
                             body.get('таб_номер'),
                             body.get('статус'), 'руч'))
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.generateMonth':
        API_CALLS.append({'action': 'generateMonth',
                          'year': body.get('year'), 'month': body.get('month')})
        return GEN_RESPONSE
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


def list_dialog(page):
    return page.evaluate("""(() => {
        const d = document.querySelector('.kip-dialog');
        if (!d) return null;
        const items = Array.from(d.querySelectorAll('.kip-dialog-item'))
            .map(function(l) {
                const cb = l.querySelector('input[type="checkbox"]');
                return {
                    id: cb ? cb.getAttribute('data-id') : null,
                    checked: cb ? cb.checked : null,
                    label: (l.querySelector('.kip-dialog-item-label') || {})
                            .textContent || '',
                    sub: (l.querySelector('.kip-dialog-item-sub') || {})
                          .textContent || ''};
            });
        const ok = d.querySelector('.kip-dialog-ok');
        return {
            title: (d.querySelector('.kip-dialog-title') || {}).textContent || '',
            msg: (d.querySelector('.kip-dialog-msg') || {}).textContent || '',
            items: items,
            count: (d.querySelector('.kip-dialog-count') || {}).textContent || '',
            selAll: (d.querySelector('.kip-dialog-selectall') || {})
                    .textContent || '',
            okText: ok ? ok.textContent.trim() : null,
            okDisabled: ok ? ok.disabled : null,
            danger: ok ? ok.className : null};})()""")


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
        # реестр авто-«д»/«н» Task 458: подмены 05|041 («д», сместилась
        # из-за ручного «В» 023) и 06|031 («н») материализованы и
        # СОХРАНЕНЫ прошлой сессией. ВАЖНО: isolateLocalStorage ставит
        # приложению префикс 'kip8test:' — ключ пишется С ПРЕФИКСОМ
        reg = json.dumps({MK: {D(5) + '|041': 1, D(6) + '|031': 1}},
                         ensure_ascii=False)
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:ws_auto_dn_keys')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t549');" +
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

        # ===== A: исходная накладка в сетке =====
        print('== A: накладка заявки — подмена смещена ручным «В» ==')
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsClearManualBtn');
            return b ? {hidden: b.hidden, text: b.textContent.trim()} : null;})()""")
        check('A: кнопка «Очистить правки» видна редактору',
              btn and not btn['hidden'] and btn['text'] == 'Очистить правки', btn)
        check('A: 023 05-е — ручной «В» (накладка)', cell_text(page, '023', '5') == 'В',
              cell_text(page, '023', '5'))
        check('A: 041 05-е — «д» (подмена сместилась сюда)',
              cell_text(page, '041', '5') == 'д', cell_text(page, '041', '5'))
        check('A: 031 06-е — «н» (подмена на месте)',
              cell_text(page, '031', '6') == 'н', cell_text(page, '031', '6'))
        check('A: 017 05-е — «ОТ» + бейдж плановой «Д» (отпускник, спрос жив)',
              (cell_text(page, '017', '5') or '').startswith('ОТ'),
              cell_text(page, '017', '5'))
        check('A: правок нет (стабильное состояние)', not pending(page))
        shot(page, '01-initial-misplaced.png')

        # ===== B: «Очистить правки» → диалог-список kipConfirmList =====
        print('== B: диалог-список — каждая правка отдельной строкой ==')
        page.click('#wsClearManualBtn')
        page.wait_for_timeout(600)
        dlg = list_dialog(page)
        check('B: диалог «Очистка ручных правок» открыт', dlg is not None, dlg)
        check('B: заголовок диалога', dlg and 'Очистка ручных правок' in dlg['title'], dlg)
        check('B: вводный текст «Отметьте правки к удалению»',
              dlg and 'Отметьте правки к удалению' in dlg['msg'], dlg)
        check('B: предупреждение про «авто»', dlg and 'не затрагиваются' in dlg['msg'], dlg)
        items = (dlg or {}).get('items') or []
        check('B: 3 строки — по одной на каждую правку', len(items) == 3, items)
        ids = [it['id'] for it in items]
        check('B: id строк = ключи ячеек (дата|таб)',
              ids == [D(5) + '|023', D(5) + '|041', D(6) + '|031'], ids)
        it23, it41, it31 = (items + [None, None, None])[:3]
        check('B: «В» 023 — работник/дата/наименование',
              it23 and 'Петров' in it23['label'] and RU(D(5)) in it23['label']
              and 'Выходной' in it23['label'] and 'В' in it23['label'],
              it23 and it23['label'])
        check('B: «д» 041 — краткое наименование из справочника',
              it41 and 'Кузнецов' in it41['label'] and RU(D(5)) in it41['label']
              and 'день в выходной' in it41['label'], it41 and it41['label'])
        check('B: «н» 031 — работник/дата/наименование',
              it31 and 'Сидоров' in it31['label'] and RU(D(6)) in it31['label']
              and 'ночь в выходной' in it31['label'], it31 and it31['label'])
        check('B: подпись «В» — ручная запись на сервере',
              it23 and 'ручная запись на сервере' in it23['sub'],
              it23 and it23['sub'])
        check('B: подписи «д»/«н» — авто-подмена, материализована',
              it41 and 'авто-подмена, материализована' in it41['sub'] and
              it31 and 'авто-подмена, материализована' in it31['sub'],
              [it41 and it41['sub'], it31 and it31['sub']])
        check('B: все отмечены по умолчанию',
              all(it['checked'] for it in items), items)
        check('B: счётчик «Выбрано: 3 из 3»',
              dlg and dlg['count'] == 'Выбрано: 3 из 3', dlg and dlg['count'])
        check('B: тумблер «Снять все» (все отмечены)',
              dlg and dlg['selAll'] == 'Снять все', dlg and dlg['selAll'])
        check('B: danger-кнопка «Очистить правки» активна',
              dlg and dlg['okText'] == 'Очистить правки' and
              'danger' in (dlg['danger'] or '') and not dlg['okDisabled'], dlg)
        shot(page, '02-list-dialog.png')

        # ===== B2: галочка «н» 031 снята по одной → OK =====
        print('== B2: выборочное удаление — «н» 031 остаётся ==')
        page.click('input[data-id="%s"]' % (D(6) + '|031'))
        page.wait_for_timeout(300)
        dlg = list_dialog(page)
        check('B2: счётчик «Выбрано: 2 из 3»',
              dlg and dlg['count'] == 'Выбрано: 2 из 3', dlg and dlg['count'])
        check('B2: тумблер сменился на «Выбрать все»',
              dlg and dlg['selAll'] == 'Выбрать все', dlg and dlg['selAll'])
        items = (dlg or {}).get('items') or []
        check('B2: галочка «н» 031 снята, остальные стоят',
              len(items) == 3 and items[0]['checked'] and items[1]['checked']
              and not items[2]['checked'], items)
        check('B2: OK активна при непустой выборке',
              dlg and not dlg['okDisabled'], dlg and dlg['okDisabled'])
        shot(page, '03-one-unchecked.png')
        page.click('.kip-dialog-ok')
        page.wait_for_timeout(600)

        pend = pending(page)
        k23, k41, k31 = D(5) + '|023', D(5) + '|041', D(6) + '|031'
        check('B2: ручной «В» 023 под __delete',
              pend.get(k23, {}).get('__delete') is True, pend)
        check('B2: сместившаяся «д» 041 под __delete',
              pend.get(k41, {}).get('__delete') is True, pend)
        check('B2: «н» 031 НЕ тронута — правки нет',
              pend.get(k31) is None, pend)
        check('B2: всего 2 правки (выборка!)', len(pend) == 2, pend)
        # ВАЖНО (урок Task 549): isolateLocalStorage ПОДМЕНЯЕТ
        # localStorage.getItem/setItem на префиксованные own-свойства
        # — literal-доступ из evaluate читал бы ДВОЙНОЙ префикс
        # ('kip8test:kip8test:…' → пусто; негативные ассеты Task 548
        # проходили тривиально). Читаем НАСТОЯЩЕЕ хранилище через
        # Storage.prototype (не затёрт own-свойством) + сверяем
        # память WorkSchedule._AUTO_DN_KEYS
        regRaw = page.evaluate("""(() => {
            try {
                return Storage.prototype.getItem.call(
                    localStorage, 'kip8test:ws_auto_dn_keys');
            } catch (e) { return null; }})()""")
        regMem = page.evaluate("""(() => {
            try { return JSON.stringify(
                (window.WorkSchedule || {})._AUTO_DN_KEYS || {}); }
            catch (e) { return '{}'; }})()""")
        regNow = json.loads(regRaw) if regRaw else {}
        regMemNow = json.loads(regMem) if regMem else {}
        check('B2: метка реестра 05|041 снята (в выборке)',
              not (regNow.get(MK) or {}).get(D(5) + '|041') and
              not (regMemNow.get(MK) or {}).get(D(5) + '|041'), [regNow, regMemNow])
        check('B2: метка реестра 06|031 СОХРАНЕНА (не в выборке)',
              (regNow.get(MK) or {}).get(D(6) + '|031') == 1 and
              (regMemNow.get(MK) or {}).get(D(6) + '|031') == 1, [regNow, regMemNow])
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsSaveBtn');
            return b ? {hidden: b.hidden, text: b.textContent.trim()} : null;})()""")
        check('B2: кнопка «Сохранить (2)»', btn and not btn['hidden'] and
              btn['text'] == 'Сохранить (2)', btn)
        t = toast_text(page)
        check('B2: тост «Очищено правок: 2»', 'Очищено правок: 2' in t, t)
        check('B2: ячейки под удалением рендерятся ПУСТЫМИ',
              cell_text(page, '023', '5') == '' and cell_text(page, '041', '5') == '')
        check('B2: «н» 031 06-е продолжает рендериться',
              cell_text(page, '031', '6') == 'н', cell_text(page, '031', '6'))
        shot(page, '04-selected-cleared.png')

        # ===== C: «Сохранить» → удаления → план расставляет заново =====
        print('== C: сохранение удалений → авто-расстановка заново ==')
        page.click('#wsSaveBtn')
        page.wait_for_timeout(2500)
        dels = [c for c in API_CALLS if c['action'] == 'deleteEntry']
        check('C: deleteEntry ×2 (только выборка)', len(dels) == 2, API_CALLS)
        check('C: payload «В» 05|023',
              any(c['date'] == D(5) and c['таб_номер'] == '023' for c in dels), dels)
        check('C: payload «д» 05|041',
              any(c['date'] == D(5) and c['таб_номер'] == '041' for c in dels), dels)
        check('C: «н» 06|031 НЕ удалялась',
              not any(c['date'] == D(6) and c['таб_номер'] == '031' for c in dels), dels)
        # план Task 456: «д» вернулась на 023; спрос 06-го закрыт живой «н»
        pend = pending(page)
        check('C: материализована «д» на 023 05-го',
              pend.get(k23, {}).get('статус') == 'д' and pend.get(k23, {}).get('__autoDn'), pend)
        check('C: новых «н» НЕТ — спрос 06-го закрыт сохранённой «н»',
              pend.get(k31) is None, pend)
        check('C: 041 05-го — правки НЕТ (подмена ушла)',
              pend.get(k41) is None, pend)
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsSaveBtn');
            return b ? {hidden: b.hidden, text: b.textContent.trim()} : null;})()""")
        check('C: кнопка «Сохранить (1)»', btn and not btn['hidden'] and
              btn['text'] == 'Сохранить (1)', btn)
        check('C: сетка — «д» на 023 05-го (вернулась!)',
              cell_text(page, '023', '5') == 'д', cell_text(page, '023', '5'))
        check('C: сетка — «н» на 031 06-е (выжила после выборки)',
              cell_text(page, '031', '6') == 'н')
        check('C: сетка — 041 05-го ПУСТО', cell_text(page, '041', '5') == '')
        shot(page, '05-auto-replanned.png')

        # ===== D: «Сохранить» материализации → финал =====
        print('== D: сохранение подмены — финал ==')
        page.click('#wsSaveBtn')
        page.wait_for_timeout(2500)
        sets = [c for c in API_CALLS if c['action'] == 'setManualEntry']
        check('D: setManualEntry ×1 (только «д»)', len(sets) == 1, API_CALLS)
        check('D: payload «д» 05|023',
              any(c['статус'] == 'д' and c['date'] == D(5) and c['таб_номер'] == '023'
                  for c in sets), sets)
        check('D: финал — 023 05-е «д»', cell_text(page, '023', '5') == 'д')
        check('D: финал — 031 06-е «н» (выборочно сохранена)',
              cell_text(page, '031', '6') == 'н')
        check('D: финал — 041 05-е ПУСТО', cell_text(page, '041', '5') == '')
        check('D: финал — 017 05/06 «ОТ» (слой авто не тронут)',
              (cell_text(page, '017', '5') or '').startswith('ОТ') and
              (cell_text(page, '017', '6') or '').startswith('ОТ'))
        pend = pending(page)
        check('D: _PENDING пуст', not pend, pend)
        btn = page.evaluate("""(() => {
            const b = document.getElementById('wsSaveBtn');
            return b ? {hidden: b.hidden} : null;})()""")
        check('D: кнопка «Сохранить» скрыта', btn and btn['hidden'], btn)
        shot(page, '06-final-selective.png')

        # ===== E: идемпотентность повторного рендера =====
        print('== E: повторный рендер — 0 новых правок ==')
        page.evaluate("WorkSchedule._renderGrid()")
        page.wait_for_timeout(500)
        pend = pending(page)
        check('E: новых правок нет', not pend, pend)

        check('Z: 0 JS-ошибок', not js_errors, js_errors)

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d OK, %d FAIL' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
