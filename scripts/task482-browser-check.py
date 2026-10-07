#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 482: browser-check — ТРИ части заявки (раздел «Табель учёта
# рабочего времени»):
#  1) окна «Мероприятия»/«Нормы» бара: раскрытие КАПАЕТСЯ по низу
#     экрана (_barExpMaxH: vh − top − 10), длинный список листается
#     ВНУТРИ окна (колесо мыши на десктопе; СВАЙП по сенсору —
#     CDP Input.dispatchTouchEvent на мобильном 375×812);
#  2) бейджи И/ПЗ ячеек шахматки: рамка ЗЕЛЁНАЯ (выполнение=1 —
#     #43a047) / КРАСНАЯ (не отмечено + дата прошла — #ef5350);
#     будущая дата и ОБ — обычная тёмная рамка rgba(0,0,0,0.45);
#  3) галочка отметки выполнения в окне «Мероприятия в этот день»
#     (рядом с ✎/✕): клик → workSchedule.setTrainingDone (мок) →
#     тост + ПОПАП перерисовался + БЕЙДЖ сетки перекрасился;
#     зритель (min) — состояние некликабельно, без ✎/✕.
# КОНТЕКСТ: мок Apps Script (порт 8992), 34 записи «Инструктажи»
# (длинный список окна мероприятий), сид localStorage кэша года
# ProdCalendar с 24 особыми днями (длинный список окна норм),
# динамические даты вокруг «сегодня», 0 JS-ошибок, скриншоты.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8992
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task482')
os.makedirs(SHOT_DIR, exist_ok=True)


def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)


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
  {'code': 'И', 'name': 'Инструктаж', 'color': '#B3E5FC'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#D1C4E9'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'},
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
ENTRIES = [
  {'id': 1, 'дата': d(-6), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
]

# TRAININGS: ключевые записи состояний + длинный хвост для окна
TODAY_ISO = '%04d-%02d-%02d' % (Y, M, TODAY.day)
TRAININGS = [
  # id 100: И ВЫПОЛНЕНО (прошедшая дата) → ЗЕЛЁНАЯ рамка, галочка ON
  {'id': 100, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-5), 'дата_окончания': d(-5), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 1, 'просрочен': 0},
  # id 101: ПЗ НЕ выполнено, дата ПРОШЛА → КРАСНАЯ рамка, пустая галочка
  {'id': 101, 'тема': 'Проверка знаний до 1000В', 'тип': 'проверка_знаний',
   'дата_начала': d(-3), 'дата_окончания': d(-3), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 0, 'просрочен': 1},
  # id 102: И будущая дата → обычная рамка (не наступила)
  {'id': 102, 'тема': 'Целевой инструктаж при допуске', 'тип': 'инструктаж',
   'дата_начала': d(5), 'дата_окончания': d(5), 'таб_номер': '023',
   'подразделение': '', 'выполнение': 0, 'просрочен': 0},
  # id 103: ОБ (не «Инструктажи») → обычная рамка, БЕЗ галочки
  {'id': 103, 'тема': 'Обучение по новой редакции инструкций', 'тип': 'обучение',
   'дата_начала': d(-2), 'дата_окончания': d(-2), 'таб_номер': '023',
   'подразделение': ''},
]
# длинный хвост: 30 инструктажей Иванова по месяцу (окно мероприятий
# становится ДЛИННЕЕ экрана — кап + прокрутка)
for k in range(30):
    day = max(1, min(DIM, k + 1))
    iso = '%04d-%02d-%02d' % (Y, M, day)
    done = 1 if (iso < TODAY_ISO and k % 5 == 0) else 0
    late = 1 if (iso < TODAY_ISO and done == 0) else 0
    TRAININGS.append({
        'id': 200 + k, 'тема': 'Инструктаж по охране труда №%d (длинное '
        'название пункта для переноса строк окна мероприятий)' % (k + 1),
        'тип': 'инструктаж', 'дата_начала': iso, 'дата_окончания': iso,
        'таб_номер': '017', 'подразделение': '',
        'выполнение': done, 'просрочен': late})

PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(-100), 'дата_окончания': d(4), 'состояние': ''},
]

MODE = {'level': 'edit'}


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
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
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.setTrainingDone':
        # мок с семантикой сервера: пишет «выполнение», пересчитывает
        # «просрочен» по дате записи
        tid = int((body or {}).get('id', 0))
        val = int((body or {}).get('выполнение', 0))
        rec = None
        for t in TRAININGS:
            if int(t['id']) == tid:
                rec = t
                break
        if rec:
            rec['выполнение'] = val
            rec['просрочен'] = 1 if (val != 1 and
                                     rec['дата_начала'] < TODAY_ISO) else 0
            return {'ok': True, 'data': {'id': tid, 'выполнение': val,
                    'просрочен': rec['просрочен'], 'created': [],
                    'updated': [], 'srvVer': 427}}
        return {'ok': False, 'error': 'запись не найдена'}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Сид кэша года ProdCalendar: 24 особых дня месяца → окно «Нормы»
# ДЛИННЕЕ экрана (кап при раскрытии)
def pcal_seed_js():
    days = {}
    for k in range(24):
        day = 1 + k
        if day > DIM:
            break
        mmdd = '%02d%02d' % (M, day)
        if k % 3 == 0:
            days[mmdd] = {'off': True, 'holiday': True, 'short': False,
                          'work': False, 'title': 'Праздник тестовый №%d' % (k + 1)}
        elif k % 3 == 1:
            days[mmdd] = {'off': True, 'holiday': False, 'short': False,
                          'work': False, 'title': 'Выходной, перенесённый с 0%d.0%d' % (day, M)}
        else:
            days[mmdd] = {'off': False, 'holiday': False, 'short': True,
                          'work': False, 'title': 'Сокращённый предпраздничный №%d' % (k + 1)}
    payload = json.dumps({'source': 'legalic', 'fetchedAtMs': 48 * 3600 * 1000,
                          'days': days}, ensure_ascii=False)
    return ("try{localStorage.setItem('kip8test:ws_pcal_year3_%d_42', %s)}catch(e){};"
            % (Y, json.dumps(payload)))


CELL_BADGES_JS = r"""(([tab, day]) => {
    const empCell = document.querySelector(
        'td.ws-emp-col[data-tab="' + tab + '"]');
    if (!empCell) return null;
    const row = empCell.closest('tr');
    if (!row) return null;
    const td = row.querySelector('td[data-day="' + day + '"]');
    if (!td) return null;
    const badges = [...td.querySelectorAll('.ws-ev-badge')].map(b => ({
        code: b.textContent.trim(),
        cls: b.className,
        border: getComputedStyle(b).borderColor,
        bg: getComputedStyle(b).backgroundColor
    }));
    return {day: day, badges: badges};})"""


POPUP_STATE_JS = r"""(() => {
    const evp = document.getElementById('wsEventsPopup');
    const rows = evp ? [...evp.querySelectorAll('.ws-popup-row.ws-popup-event')] : [];
    return {
        active: !!(evp && evp.classList.contains('active')),
        rows: rows.map(r => ({
            code: r.querySelector('.ws-popup-code') ?
                  r.querySelector('.ws-popup-code').textContent.trim() : '',
            chk: r.querySelector('.ws-done-chk') ?
                 r.querySelector('.ws-done-chk').className : null,
            chkTitle: r.querySelector('.ws-done-chk') ?
                      r.querySelector('.ws-done-chk').title : '',
            hasToggle: !!r.querySelector('[onclick*="toggleTrainingDone"]'),
            hasEdit: !!r.querySelector('[title="Редактировать"]'),
            hasDel: !!r.querySelector('[title="Удалить"]'),
            chkFirst: !!(r.querySelector('.ws-done-chk') &&
                        r.innerHTML.indexOf('ws-done-chk') <
                        r.innerHTML.indexOf('title="Редактировать"'))
        }))};})"""


def open_grid(page, theme='dark'):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)


def main():
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A/B/C: ДЕСКТОП 1280x650, edit, тёмная ==')
        # НИЗКИЙ вьюпорт: кап срабатывает уже на окне мероприятий
        ctx = browser.new_context(viewport={'width': 1280, 'height': 650})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t482');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            pcal_seed_js())

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

        open_grid(page)

        # ---- A: окно «Мероприятия»: раскрытие КАПАЕТСЯ по экрану ----
        print('== A: кап раскрытия окна «Мероприятия» ==')
        st = page.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            const btn = el.querySelector('.ws-bar-exp');
            return {hidden: el.hidden, top: r.top, h: r.height,
                    sh: el.scrollHeight, hasBtn: !!btn,
                    vh: window.innerHeight};})()""")
        check('окно мероприятий отрисовано, список длинный',
              st and (not st['hidden']) and st['sh'] > 650, st)
        check('в свёрнутом виде — компактная высота 95px',
              st and abs(st['h'] - 95) < 2, st)
        check('значок раскрытия виден (текст не влезает)',
              st and st['hasBtn'], st)

        page.click('#wsEventsPanel .ws-bar-exp')
        page.wait_for_timeout(400)
        st2 = page.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            const r = el.getBoundingClientRect();
            const btn = el.querySelector('.ws-bar-exp');
            const br = btn ? btn.getBoundingClientRect() : null;
            const cs = getComputedStyle(el);
            return {open: el.classList.contains('ws-bar-open'),
                    h: r.height, top: r.top, bottom: r.bottom,
                    sh: el.scrollHeight, ch: el.clientHeight,
                    mb: el.style.marginBottom,
                    overflowY: cs.overflowY,
                    vh: window.innerHeight,
                    btnTop: br ? br.top : null};})()""")
        cap = st2['vh'] - st2['top'] - 10
        check('окно раскрыто (класс ws-bar-open)', st2['open'])
        check('высота КАПНУТА до низа экрана (h = vh − top − 10)',
              abs(st2['h'] - cap) < 3, {'h': st2['h'], 'cap': cap})
        check('низ окна НЕ ниже вьюпорта',
              st2['bottom'] <= st2['vh'] + 1, st2)
        check('габарит бара прежний: height + margin = 95px (маржа ОТРИЦАТЕЛЬНАЯ)',
              abs(st2['h'] + float(str(st2['mb']).replace('px', '')) - 95) < 1,
              st2)
        check('текст длиннее окна — прокрутка внутри',
              st2['sh'] > st2['ch'], st2)
        check('overflow-y: auto (колесо/свайп/стрелки)',
              st2['overflowY'] == 'auto', st2)

        # колесо мыши — прокрутка ВНУТРИ окна
        box = page.evaluate("""(() => {
            const r = document.getElementById('wsEventsPanel')
                .getBoundingClientRect();
            return {x: r.left + r.width / 2, y: r.top + 80};})()""")
        page.mouse.move(box['x'], box['y'])
        page.mouse.wheel(0, 300)
        page.wait_for_timeout(250)
        st3 = page.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            const btn = el.querySelector('.ws-bar-exp');
            const prn = el.querySelector('.ws-bar-print');
            const er = el.getBoundingClientRect();
            return {scrollTop: el.scrollTop,
                    btnTop: btn ? btn.getBoundingClientRect().top : null,
                    erTop: er.top,
                    prnTop: prn ? prn.getBoundingClientRect().top : null};})()""")
        check('КОЛЕСО МЫШКИ прокручивает раскрытый список',
              st3['scrollTop'] > 50, st3)
        check('значки остаются в верхнем углу при прокрутке (translateY)',
              st3['btnTop'] is not None and
              abs(st3['btnTop'] - st3['erTop'] - 3) < 4, st3)
        shot(page, 'a-events-expanded-capped.png')

        # сворачивание — прежнее
        page.click('#wsEventsPanel .ws-bar-exp')
        page.wait_for_timeout(350)
        st4 = page.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            return {open: el.classList.contains('ws-bar-open'),
                    h: el.getBoundingClientRect().height,
                    mb: el.style.marginBottom,
                    st: el.scrollTop};})()""")
        check('повторный клик — окно свёрнуто (95px, сброс маржи)',
              (not st4['open']) and abs(st4['h'] - 95) < 2 and st4['mb'] == '',
              st4)

        # ---- A2: окно «Нормы» — тот же кап (24 особых дня) ----
        print('== A2: кап раскрытия окна «Нормы» ==')
        stn = page.evaluate("""(() => {
            const el = document.getElementById('wsCalPanel');
            if (!el) return null;
            const btn = el.querySelector('.ws-bar-exp');
            return {hidden: el.hidden, sh: el.scrollHeight,
                    hasBtn: !!btn,
                    chips: el.querySelectorAll('.ws-cp-day').length};})()""")
        check('окно норм: длинный список особых дней (сид календаря)',
              stn and stn['sh'] > 400 and stn['chips'] >= 20, stn)
        if stn and stn['hasBtn']:
            page.click('#wsCalPanel .ws-bar-exp')
            page.wait_for_timeout(400)
            stn2 = page.evaluate("""(() => {
                const el = document.getElementById('wsCalPanel');
                const r = el.getBoundingClientRect();
                return {open: el.classList.contains('ws-bar-open'),
                        h: r.height, top: r.top, bottom: r.bottom,
                        sh: el.scrollHeight, ch: el.clientHeight,
                        vh: window.innerHeight};})()""")
            capn = stn2['vh'] - stn2['top'] - 10
            check('окно норм раскрыто КАПНУТО по экрану',
                  stn2['open'] and abs(stn2['h'] - capn) < 3,
                  {'h': stn2['h'], 'cap': capn})
            check('окно норм: низ не ниже вьюпорта',
                  stn2['bottom'] <= stn2['vh'] + 1, stn2)
            check('окно норм: прокрутка внутри',
                  stn2['sh'] > stn2['ch'], stn2)
            boxn = page.evaluate("""(() => {
                const r = document.getElementById('wsCalPanel')
                    .getBoundingClientRect();
                return {x: r.left + r.width / 2, y: r.top + 60};})()""")
            page.mouse.move(boxn['x'], boxn['y'])
            page.mouse.wheel(0, 250)
            page.wait_for_timeout(250)
            stn3 = page.evaluate("""(() => ({
                st: document.getElementById('wsCalPanel').scrollTop}))()""")
            check('окно норм: колесо прокручивает список',
                  stn3['st'] > 10, stn3)
            shot(page, 'a2-norms-expanded-capped.png')
            page.click('#wsCalPanel .ws-bar-exp')
            page.wait_for_timeout(300)
        else:
            check('окно норм: значок раскрытия есть', False, stn)

        # ---- B: рамки бейджей И/ПЗ в ячейках ----
        print('== B: рамки бейджей И/ПЗ в ячейках ==')
        day100 = int(d(-5).split('-')[2])
        day101 = int(d(-3).split('-')[2])
        day102 = int(d(5).split('-')[2])
        day103 = int(d(-2).split('-')[2])
        b1 = page.evaluate(CELL_BADGES_JS, ['017', day100])
        b2 = page.evaluate(CELL_BADGES_JS, ['017', day101])
        b3 = page.evaluate(CELL_BADGES_JS, ['023', day102])
        b4 = page.evaluate(CELL_BADGES_JS, ['023', day103])
        check('ячейка Иванова (И выполнено): бейдж И с классом ws-ev-done',
              b1 and any('ws-ev-done' in x['cls'] for x in b1['badges']), b1)
        check('рамка бейджа И ЗЕЛЁНАЯ #43a047',
              b1 and any(x['border'] == 'rgb(67, 160, 71)'
                         for x in b1['badges']), b1)
        check('ячейка Иванова (ПЗ просрочено): бейдж ПЗ с классом ws-ev-late',
              b2 and any('ws-ev-late' in x['cls']
                         for x in b2['badges'] if x['code'] == 'ПЗ'), b2)
        check('рамка бейджа ПЗ КРАСНАЯ #ef5350',
              b2 and any(x['border'] == 'rgb(239, 83, 80)'
                         for x in b2['badges'] if x['code'] == 'ПЗ'), b2)
        check('ячейка Петрова (И будущая): обычная рамка rgba(0,0,0,0.45)',
              b3 and any(x['border'] == 'rgba(0, 0, 0, 0.45)'
                         for x in b3['badges'] if x['code'] == 'И'), b3)
        check('бейдж ОБ: обычная рамка (не окрашивается)',
              b4 and any(x['border'] == 'rgba(0, 0, 0, 0.45)'
                         for x in b4['badges'] if x['code'] == 'ОБ'), b4)
        # долгие записи: зелёные/красные по дате (хвост)
        tall = page.evaluate("""(() => {
            let green = 0, red = 0, plain = 0;
            document.querySelectorAll(
                'td.ws-cell .ws-ev-badge').forEach(b => {
                if (b.classList.contains('ws-ev-done')) green++;
                else if (b.classList.contains('ws-ev-late')) red++;
                else plain++;
            });
            return {green: green, red: red, plain: plain};})()""")
        check('в сетке есть все три вида рамок (зел/красн/обычн)',
              tall['green'] >= 3 and tall['red'] >= 5 and tall['plain'] >= 24,
              tall)
        shot(page, 'b-grid-badges.png')

        # ---- C: попап ячейки — галочка отметки ----
        print('== C: попап «Мероприятия в этот день» — галочка ==')

        def cell_click(tab, day):
            page.evaluate("""(([tab, day]) => {
                const emp = document.querySelector(
                    'td.ws-emp-col[data-tab="' + tab + '"]');
                const td = emp.closest('tr')
                    .querySelector('td[data-day="' + day + '"]');
                td.click();})""", [tab, day])

        # C1: ячейка с И (выполнено) — зелёная галочка
        cell_click('017', day100)
        page.wait_for_timeout(350)
        ps1 = page.evaluate(POPUP_STATE_JS)
        check('попап открыт у ячейки', ps1['active'])
        r_instr = [r for r in ps1['rows'] if r['code'] == 'И']
        check('строка И: галочка ВКЛ (ws-done-on) + клик toggle',
              r_instr and r_instr[0]['chk'] and
              'ws-done-on' in r_instr[0]['chk'] and r_instr[0]['hasToggle'], ps1)
        check('строка И: галочка РЯДОМ с ✎/✕ (порядок в разметке)',
              r_instr and r_instr[0]['hasEdit'] and r_instr[0]['hasDel'] and
              r_instr[0]['chkFirst'], ps1)
        check('тултип галочки: «Снять отметку о выполнении»',
              r_instr and r_instr[0]['chkTitle'] == 'Снять отметку о выполнении',
              ps1)
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)

        # C2: ячейка с ПЗ (не выполнено) — пустая галочка, КЛИК по ней
        cell_click('017', day101)
        page.wait_for_timeout(350)
        ps2 = page.evaluate(POPUP_STATE_JS)
        r_pz = [r for r in ps2['rows'] if r['code'] == 'ПЗ']
        check('строка ПЗ: ПУСТАЯ галочка + клик toggle + ✎/✕',
              r_pz and r_pz[0]['chk'] and 'ws-done-on' not in r_pz[0]['chk']
              and r_pz[0]['hasToggle'] and r_pz[0]['hasEdit'], ps2)
        shot(page, 'c1-popup-before-toggle.png')

        # клик по галочке → сервер-мок → мгновенное обновление
        page.evaluate("""(() => {
            const evp = document.getElementById('wsEventsPopup');
            const row = [...evp.querySelectorAll('.ws-popup-event')]
                .find(r => r.querySelector('.ws-popup-code') &&
                           r.querySelector('.ws-popup-code').textContent
                               .trim() === 'ПЗ');
            row.querySelector('.ws-done-chk').click();})()""")
        page.wait_for_timeout(700)
        ps3 = page.evaluate(POPUP_STATE_JS)
        r_pz2 = [r for r in ps3['rows'] if r['code'] == 'ПЗ']
        check('после клика: галочка ПЗ стала ЗЕЛЁНОЙ (попап перерисован)',
              r_pz2 and 'ws-done-on' in (r_pz2[0]['chk'] or ''), ps3)
        b2_after = page.evaluate(CELL_BADGES_JS, ['017', day101])
        check('БЕЙДЖ ПЗ в сетке перекрасился в ЗЕЛЁНЫЙ без перезагрузки',
              b2_after and any(x['border'] == 'rgb(67, 160, 71)'
                               for x in b2_after['badges']
                               if x['code'] == 'ПЗ'), b2_after)
        toast = page.evaluate("""(() => {
            const t = document.getElementById('toast');
            const m = document.getElementById('toastMessage');
            return {shown: !!(t && t.classList.contains('show')),
                    text: m ? m.textContent.trim() : ''};})()""")
        check('тост «Отмечено выполнение»', toast['text'].startswith(
            'Отмечено выполнение'), toast)
        shot(page, 'c2-popup-after-toggle.png')

        # C3: снятие отметки — бейдж обратно КРАСНЫЙ (дата прошла)
        page.evaluate("""(() => {
            const evp = document.getElementById('wsEventsPopup');
            const row = [...evp.querySelectorAll('.ws-popup-event')]
                .find(r => r.querySelector('.ws-popup-code') &&
                           r.querySelector('.ws-popup-code').textContent
                               .trim() === 'ПЗ');
            row.querySelector('.ws-done-chk').click();})()""")
        page.wait_for_timeout(700)
        b2_back = page.evaluate(CELL_BADGES_JS, ['017', day101])
        check('снятие отметки: бейдж ПЗ снова КРАСНЫЙ (просрочен)',
              b2_back and any(x['border'] == 'rgb(239, 83, 80)'
                              for x in b2_back['badges']
                              if x['code'] == 'ПЗ'), b2_back)
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)

        # C4: ОБ — без галочки
        cell_click('023', day103)
        page.wait_for_timeout(350)
        ps4 = page.evaluate(POPUP_STATE_JS)
        r_ob = [r for r in ps4['rows'] if r['code'] == 'ОБ']
        check('строка ОБ: галочки НЕТ (семейство «Мероприятия»)',
              r_ob and r_ob[0]['chk'] is None and not r_ob[0]['hasToggle'], ps4)
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)

        check('JS-ошибок нет (десктоп, edit)', not js_errors, js_errors[:4])
        ctx.close()

        # ==============================================================
        print('== D: ЗРИТЕЛЬ (min): состояние без правки ==')
        MODE['level'] = 'min'
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 700})
        page2 = ctx2.new_page()
        js2 = []
        page2.on('pageerror', lambda e: js2.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        ctx2.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t482v');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            pcal_seed_js())

        def handle2(route, request):
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

        ctx2.route('**/exec?**', handle2)
        ctx2.route('**script.google.com/**', handle2)
        ctx2.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx2.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx2.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        open_grid(page2)
        bv = page2.evaluate(CELL_BADGES_JS, ['017', day100])
        check('зритель: бейдж И в ячейке — ЗЕЛЁНАЯ рамка (состояние видно)',
              bv and any(x['border'] == 'rgb(67, 160, 71)'
                         for x in bv['badges']), bv)
        page2.evaluate("""(([tab, day]) => {
            const emp = document.querySelector(
                'td.ws-emp-col[data-tab="' + tab + '"]');
            const td = emp.closest('tr')
                .querySelector('td[data-day="' + day + '"]');
            td.click();})""", ['017', day100])
        page2.wait_for_timeout(400)
        psv = page2.evaluate(POPUP_STATE_JS)
        rv = [r for r in psv['rows'] if r['code'] == 'И']
        check('зритель: галочка СОСТОЯНИЕ (ws-done-on ws-done-ro), БЕЗ клика',
              rv and rv[0]['chk'] and 'ws-done-ro' in rv[0]['chk']
              and not rv[0]['hasToggle'], psv)
        check('зритель: ✎/✕ у записей НЕТ (как прежде)',
              rv and not rv[0]['hasEdit'] and not rv[0]['hasDel'], psv)
        shot(page2, 'd-viewer-popup.png')
        check('JS-ошибок нет (зритель)', not js2, js2[:4])
        ctx2.close()
        MODE['level'] = 'edit'

        # ==============================================================
        print('== E: МОБИЛ 375x812, тёмная, свайп по сенсору ==')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 812},
                                   has_touch=True, is_mobile=True)
        page3 = ctx3.new_page()
        js3 = []
        page3.on('pageerror', lambda e: js3.append(str(e)))
        page3.on('dialog', lambda dg: dg.accept())
        ctx3.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t482m');" +
            "localStorage.setItem('kip8test:app-theme','dark');" +
            pcal_seed_js())

        def handle3(route, request):
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

        ctx3.route('**/exec?**', handle3)
        ctx3.route('**script.google.com/**', handle3)
        ctx3.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx3.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx3.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        open_grid(page3)
        # чип «Мероприятия» → окно показывается
        chip = page3.evaluate("""(() => {
            const c = document.getElementById('wsChipEvents');
            const el = document.getElementById('wsEventsPanel');
            return {chip: !!c,
                    visible: el ? el.offsetParent !== null : null};})()""")
        # Task 334: на мобильном окно скрыто CSS-медиа (класс
        # ws-mob-events-on на странице отсутствует) — проверяем
        # ВИЗУАЛЬНУЮ видимость (offsetParent), не атрибут hidden
        check('мобайл: чип «Мероприятия» есть, окно скрыто (CSS)',
              chip['chip'] and chip['visible'] is False, chip)
        page3.click('#wsChipEvents')
        page3.wait_for_timeout(400)
        stmob = page3.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            const r = el.getBoundingClientRect();
            const btn = el.querySelector('.ws-bar-exp');
            return {visible: el.offsetParent !== null, sh: el.scrollHeight,
                    h: r.height, top: r.top, hasBtn: !!btn,
                    vh: window.innerHeight};})()""")
        check('мобайл: окно открыто чипом, список длинный',
              stmob['visible'] and stmob['sh'] > 500, stmob)
        if stmob['hasBtn']:
            page3.evaluate("""(() => {
                document.getElementById('wsEventsPanel')
                    .querySelector('.ws-bar-exp').click();})()""")
            page3.wait_for_timeout(450)
            stmob2 = page3.evaluate("""(() => {
                const el = document.getElementById('wsEventsPanel');
                const r = el.getBoundingClientRect();
                return {open: el.classList.contains('ws-bar-open'),
                        h: r.height, top: r.top, bottom: r.bottom,
                        sh: el.scrollHeight, ch: el.clientHeight,
                        vh: window.innerHeight};})()""")
            capm = stmob2['vh'] - stmob2['top'] - 10
            check('мобайл: раскрытие КАПНУТО по экрану',
                  stmob2['open'] and abs(stmob2['h'] - capm) < 3,
                  {'h': stmob2['h'], 'cap': capm})
            check('мобайл: низ окна не ниже экрана',
                  stmob2['bottom'] <= stmob2['vh'] + 1, stmob2)

            # СВАЙП по сенсору: CDP Input.dispatchTouchEvent (настоящий
            # тач-ввод → нативная прокрутка overflow-контейнера)
            cdp = ctx3.new_cdp_session(page3)
            cx = 187
            cdp.send('Input.dispatchTouchEvent', {
                'type': 'touchStart',
                'touchPoints': [{'x': cx, 'y': 420}]})
            for yy in (390, 350, 310, 270, 230, 190):
                cdp.send('Input.dispatchTouchEvent', {
                    'type': 'touchMove',
                    'touchPoints': [{'x': cx, 'y': yy}]})
            cdp.send('Input.dispatchTouchEvent', {
                'type': 'touchEnd', 'touchPoints': []})
            page3.wait_for_timeout(400)
            stmob3 = page3.evaluate(
                "document.getElementById('wsEventsPanel').scrollTop")
            check('мобайл: СВАЙП по сенсору прокручивает список',
                  stmob3 > 40, stmob3)
            shot(page3, 'e-mobile-swipe.png')
        else:
            check('мобайл: значок раскрытия есть', False, stmob)

        # мобайл: попап ячейки с галочкой
        page3.evaluate("""(([tab, day]) => {
            const emp = document.querySelector(
                'td.ws-emp-col[data-tab="' + tab + '"]');
            const td = emp.closest('tr')
                .querySelector('td[data-day="' + day + '"]');
            td.click();})""", ['017', day100])
        page3.wait_for_timeout(450)
        psm = page3.evaluate(POPUP_STATE_JS)
        rm = [r for r in psm['rows'] if r['code'] == 'И']
        check('мобайл: галочка отметки в попапе ячейки',
              rm and rm[0]['chk'] and 'ws-done-on' in rm[0]['chk']
              and rm[0]['hasToggle'], psm)
        shot(page3, 'e-mobile-popup.png')
        check('JS-ошибок нет (мобайл)', not js3, js3[:4])
        ctx3.close()

        browser.close()

    print()
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
