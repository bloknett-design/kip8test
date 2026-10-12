#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 504: browser-check — заявка:
#   «В разделе "Табель учёта рабочего времени", в окне мероприятий,
#    даты выполненных мероприятий сделай зелёным цветом, а просроченных
#    - красным.»
# Проверяется ОКНО «Мероприятия» бара (#wsEventsPanel,
# _renderMonthEventsPanel) — ДАТЫ строк (.ws-ep-date):
#   A) ДЕСКТОП 1280x720, тёмная: выполненный И → класс ws-ep-date-ok +
#      цвет #81c784; просроченный ПЗ (поле «просрочен») → ws-ep-date-bad +
#      #ef5350; И без полей с прошедшей датой → bad (фолбэк даты);
#      будущий ПЗ / ОБ — БЕЗ класса (обычный цвет); выполнение
#      ПРИОРИТЕТНЕЕ поля «просрочен» (1+1 → зелёная); фон строк
#      ws-ep-past жив (Task 380/389); СИЗ-дата — без класса;
#   B) ДЕСКТОП, светлая: ok → #2e7d32, bad → #c62828, обычная — #000;
#   C) МОБАЙЛ 375x812, тёмная: окно открывается чипом «Мероприятия»,
#      цвета дат на месте (RGB-проверка);
#   D) 0 JS-ошибок; скриншоты.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8985
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task504')
os.makedirs(SHOT_DIR, exist_ok=True)


def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)


TODAY_ISO = '%04d-%02d-%02d' % (Y, M, TODAY.day)
# ожидание для «И без полей»: фолбэк срабатывает iff дата < «сегодня»
# (на 1–4-е числа месяца d(-4) клампится к 1-му — тогда НЕ просрочен)
EXP_LATE_FALLBACK = 'ws-ep-date-bad' if d(-4) < TODAY_ISO else ''
# ожидание фона ws-ep-past: строки 100/101/102/104/105 (смещения
# -5/-3/-4/-2/-1) прошедшие iff смещение строго до 1-го (кламп)
EXP_PAST = sum(1 for n in (5, 3, 4, 2, 1) if TODAY.day > n)


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
          (('  [' + str(extra)[:300] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=True)
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
TRAININGS = [
  # 1: И ВЫПОЛНЕНО (дата в прошлом) → ЗЕЛЁНАЯ дата
  {'id': 100, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-5), 'дата_окончания': d(-5), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 1, 'просрочен': 0},
  # 2: ПЗ ПРОСРОЧЕНО (поле сервера) → КРАСНАЯ дата
  {'id': 101, 'тема': 'Проверка знаний до 1000В', 'тип': 'проверка_знаний',
   'дата_начала': d(-3), 'дата_окончания': d(-3), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 0, 'просрочен': 1},
  # 3: И БЕЗ полей, дата прошла → КРАСНАЯ (фолбэк дата_начала < сегодня)
  {'id': 102, 'тема': 'Инструктаж по пожарной безопасности', 'тип': 'инструктаж',
   'дата_начала': d(-4), 'дата_окончания': d(-4), 'таб_номер': '023',
   'подразделение': ''},
  # 4: ПЗ БУДУЩЕЕ (без отметки) → БЕЗ класса
  {'id': 103, 'тема': 'Проверка знаний КИПиА', 'тип': 'проверка_знаний',
   'дата_начала': d(5), 'дата_окончания': d(5), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 0, 'просрочен': 0},
  # 5: ОБ — не «Инструктажи» → БЕЗ класса при любых полях
  {'id': 104, 'тема': 'Обучение по новой редакции инструкций', 'тип': 'обучение',
   'дата_начала': d(-2), 'дата_окончания': d(-2), 'таб_номер': '023',
   'подразделение': '', 'выполнение': 1, 'просрочен': 1},
  # 6: ПЗ ВЫПОЛНЕНО + просрочен=1 → ЗЕЛЁНАЯ (выполнение приоритетнее)
  {'id': 105, 'тема': 'Проверка знаний по электробезопасности', 'тип': 'проверка_знаний',
   'дата_начала': d(-1), 'дата_окончания': d(-1), 'таб_номер': '023',
   'подразделение': '', 'выполнение': 1, 'просрочен': 1},
]
PPE = [
  # СИЗ с истекающим сроком в этом месяце → строка «до дд.мм» БЕЗ класса даты
  {'id': 200, 'таб_номер': '017', 'наименование': 'Перчатки диэлектрические',
   'дата_выдачи': d(-60), 'дата_окончания': d(10), 'срок': '', 'количество': 1},
]
MODE = {'level': 'edit'}


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        perms = {'workschedule.view': True, 'workschedule.edit': True}
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
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Состояние окна «Мероприятия»: строки с классом ДАТЫ + computed-цветом
PANEL_STATE_JS = r"""(() => {
    const p = document.getElementById('wsEventsPanel');
    if (!p) return {missing: true};
    const rows = [...p.querySelectorAll('.ws-ep-item')];
    return {hidden: p.hidden,
            cap: (p.querySelector('.ws-ep-cap') || {}).textContent || '',
            rows: rows.map(r => {
                const dt = r.querySelector('.ws-ep-date');
                return {
                    past: r.classList.contains('ws-ep-past'),
                    date: dt ? dt.textContent.trim() : '',
                    cls: dt ? dt.className.replace('ws-ep-date', '').trim() : '',
                    color: dt ? getComputedStyle(dt).color : '',
                    text: (r.querySelector('.ws-ep-text') || {}).textContent || ''
                };})};})"""


def open_grid(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    # Task 486: тихое обновление (таймер 4 с) — дождаться стабильности
    page.wait_for_timeout(3500)


def setup_routes(ctx):
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


def seed_ls(theme):
    return ("try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t504');" +
            "localStorage.setItem('kip8test:app-theme','" + theme + "');")


def find_row(state, marker):
    for r in state.get('rows', []):
        if marker in r.get('text', ''):
            return r
    return None


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A: ДЕСКТОП 1280x720, edit, ТЁМНАЯ ==')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(seed_ls('dark'))
        setup_routes(ctx)
        open_grid(page)
        st = page.evaluate(PANEL_STATE_JS)
        check('окно «Мероприятия» отрисовано (не hidden)',
              not st.get('missing') and not st.get('hidden'), st)
        check('6 строк мероприятий + 1 СИЗ = 7 строк',
              len(st.get('rows', [])) == 7, [r['text'][:40] for r in st.get('rows', [])])

        r1 = find_row(st, 'Повторный инструктаж')
        check('И выполнено: класс ws-ep-date-ok',
              r1 and r1['cls'] == 'ws-ep-date-ok', r1)
        check('И выполнено: цвет #81c784 (rgb(129, 199, 132))',
              r1 and r1['color'] == 'rgb(129, 199, 132)', r1)

        r2 = find_row(st, 'Проверка знаний до 1000В')
        check('ПЗ просрочен (поле сервера): класс ws-ep-date-bad',
              r2 and r2['cls'] == 'ws-ep-date-bad', r2)
        check('ПЗ просрочен: цвет #ef5350 (rgb(239, 83, 80))',
              r2 and r2['color'] == 'rgb(239, 83, 80)', r2)

        r3 = find_row(st, 'пожарной безопасности')
        lbl3 = ('И без полей: фолбэк по дате → ' + EXP_LATE_FALLBACK)
        check(lbl3, r3 and r3['cls'] == EXP_LATE_FALLBACK, r3)

        r4 = find_row(st, 'Проверка знаний КИПиА')
        check('ПЗ будущее: БЕЗ класса (обычный цвет)',
              r4 and r4['cls'] == '' and r4['color'] == 'rgb(224, 224, 224)', r4)

        r5 = find_row(st, 'Обучение по новой')
        check('ОБ: БЕЗ класса при выполнение=1/просрочен=1 (гвард И/ПЗ)',
              r5 and r5['cls'] == '' and r5['color'] == 'rgb(224, 224, 224)', r5)

        r6 = find_row(st, 'электробезопасности')
        check('выполнение ПРИОРИТЕТНЕЕ просрочки: 1+1 → ЗЕЛЁНАЯ',
              r6 and r6['cls'] == 'ws-ep-date-ok' and
              r6['color'] == 'rgb(129, 199, 132)', r6)

        # фон строк: прошедшие даты → ws-ep-past (Task 380/389 жив)
        past_rows = [r for r in st.get('rows', []) if r['past']]
        check('фон ws-ep-past: расчётно %d прошедших строк' % EXP_PAST,
              len(past_rows) == EXP_PAST, [r['date'] for r in past_rows])

        # СИЗ-строка: дата «до …» БЕЗ класса
        rz = None
        for r in st.get('rows', []):
            if 'Перчатки' in r.get('text', ''):
                rz = r
                break
        check('СИЗ «до дд.мм»: дата БЕЗ ok/bad класса',
              rz and rz['cls'] == '' and rz['date'].startswith('до '), rz)

        check('заголовок окна жив (Мероприятия · месяц)',
              'Мероприятия' in st.get('cap', ''), st.get('cap'))
        shot(page, 'a-desktop-dark.png')
        # прицельный element-скриншот окна «Мероприятия» (для VLM):
        # окно скроллится с ограниченной высотой (Task 378) — для кадра
        # временно раскрываем высоту (только в тесте, затем возвращаем)
        try:
            page.evaluate("(() => { const el = document.getElementById('wsEventsPanel');" +
                " el.style.height = 'auto'; el.style.maxHeight = 'none'; " +
                " el.style.overflow = 'visible'; })()")
            page.locator('#wsEventsPanel').screenshot(
                path=os.path.join(SHOT_DIR, 't504-panel-dark.png'))
        except Exception as e:
            print('  (panel shot: %s)' % e)

        # ==============================================================
        print('== B: ДЕСКТОП 1280x720, edit, СВЕТЛАЯ ==')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 720})
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        ctx2.add_init_script(seed_ls('light'))
        setup_routes(ctx2)
        open_grid(page2)
        st2 = page2.evaluate(PANEL_STATE_JS)
        r1l = find_row(st2, 'Повторный инструктаж')
        check('светлая: выполнено → #2e7d32 (rgb(46, 125, 50))',
              r1l and r1l['cls'] == 'ws-ep-date-ok' and
              r1l['color'] == 'rgb(46, 125, 50)', r1l)
        r2l = find_row(st2, 'Проверка знаний до 1000В')
        check('светлая: просрочено → #c62828 (rgb(198, 40, 40))',
              r2l and r2l['cls'] == 'ws-ep-date-bad' and
              r2l['color'] == 'rgb(198, 40, 40)', r2l)
        r4l = find_row(st2, 'Проверка знаний КИПиА')
        check('светлая: обычная дата — ЧЁРНАЯ (Task 330 жив)',
              r4l and r4l['cls'] == '' and r4l['color'] == 'rgb(0, 0, 0)', r4l)
        shot(page2, 'b-desktop-light.png')
        try:
            page2.evaluate("(() => { const el = document.getElementById('wsEventsPanel');" +
                " el.style.height = 'auto'; el.style.maxHeight = 'none'; " +
                " el.style.overflow = 'visible'; })()")
            page2.locator('#wsEventsPanel').screenshot(
                path=os.path.join(SHOT_DIR, 't504-panel-light.png'))
        except Exception as e:
            print('  (panel shot: %s)' % e)

        # ==============================================================
        print('== C: МОБАЙЛ 375x812, edit, тёмная — чип «Мероприятия» ==')
        ctx3 = browser.new_context(
            viewport={'width': 375, 'height': 812},
            is_mobile=True, has_touch=True,
            user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Mobile Safari/537.36')
        page3 = ctx3.new_page()
        js_errors3 = []
        page3.on('pageerror', lambda e: js_errors3.append(str(e)))
        page3.on('dialog', lambda dg: dg.accept())
        ctx3.add_init_script(seed_ls('dark'))
        setup_routes(ctx3)
        open_grid(page3)
        st3 = page3.evaluate(PANEL_STATE_JS)
        check('мобайл: окно отрисовано (hidden=false после чипа не требуется — '
              'скрытие CSS-классом страницы, не hidden)',
              not st3.get('missing'), st3 if st3.get('missing') else '')
        # мобильные чипы: раскрыть окно «Мероприятия» (Task 334)
        chip = page3.query_selector('#wsChipEvents')
        if chip and chip.is_visible():
            chip.click()
            page3.wait_for_timeout(400)
        st3 = page3.evaluate(PANEL_STATE_JS)
        r1m = find_row(st3, 'Повторный инструктаж')
        check('мобайл: выполнено → зелёная дата', r1m and
              r1m['cls'] == 'ws-ep-date-ok' and
              r1m['color'] == 'rgb(129, 199, 132)', r1m)
        r2m = find_row(st3, 'Проверка знаний до 1000В')
        check('мобайл: просрочено → красная дата', r2m and
              r2m['cls'] == 'ws-ep-date-bad' and
              r2m['color'] == 'rgb(239, 83, 80)', r2m)
        shot(page3, 'c-mobile-dark.png')

        # ==============================================================
        check('0 JS-ошибок (десктоп тёмная)', len(js_errors) == 0, js_errors)
        check('0 JS-ошибок (десктоп светлая)', len(js_errors2) == 0, js_errors2)
        check('0 JS-ошибок (мобайл)', len(js_errors3) == 0, js_errors3)

        browser.close()

    print('\nИТОГ: %d passed, %d failed' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
