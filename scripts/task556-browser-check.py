#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 556 browser-check: доводка вида строк блока «Повторные
# инструктажи и периодическая проверка знаний» КАРТОЧКИ работника
# (страница «Работники», колонка .ws-wcol-instr) ПОСЛЕ Task 555.
# Заявка:
#   «В блоке со списком инструктажей и проверок знаний в карточках
#    работников, справа от текста краткого наименования сделай
#    отступ (пробел) от остального текста. Шрифт дат сделай по
#    ярче. И в целом поле для текста сделай по шире, а кнопки и
#    значки слева и справа смести ближе к краям блока.»
# Сценарий (май 2026; работник 017; записи 2026; Список_И_и_ПЗ — 4
# пункта: ОТ-РИ (сокр.), 9-ОГЭ (сокр.), ПЗ-1000В (сокр.), ПЗ-ПБ
# (ПУСТАЯ ячейка E)):
#  A) строка 101 (инструктаж ОТ-РИ): отступ после краткого —
#     margin-right 6px (.ws-tr-short) и ВИДИМЫЙ зазор (rect) до
#     .ws-tr-rest; ДАТА — span.ws-tr-date ЯРЧЕ: цвет --text-primary
#     rgb(224,224,224) (тёмная тема) и вес 600, размер 13px;
#     геометрия строки колонки: padding-left 6px / padding-right
#     4px / gap 4px; свотч — у ЛЕВОГО края строки (rect: лево
#     свотча ≈ 6px от левого края), колонка галочка/✎/✕ — у
#     ПРАВОГО (право колонки ≈ 4px); поле .ws-popup-name —
#     растянуто (имя начинается после кода + 4px, правый край —
#     у колонки кнопок);
#  B) строка 102 (ПЗ): та же геометрия; дата 20.05.2026 яркая;
#  C) выполненная строка 103: отступ/дата/геометрия живы,
#     текст НЕ тускнеет (opacity 1 — Task 555);
#  D) строки 104 (пункт с ПУСТЫМ сокращением) и 105 («вне
#     списка») — БЕЗ префикса, но дата — ТА ЖЕ яркая (.ws-tr-date);
#  E) отметка галочкой 101 — отступ/дата/геометрия живы после
#     перерисовки, текст не тускнеет;
#  F) светлая тема — дата rgb(20,20,19), отступ 6px, поля
#     6px/4px, gap 4px;
#  G) санитар: 0 JS-ошибок; скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
Y, M = 2026, 5
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task556')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# Дата ЯРЧЕ: --text-primary (Task 556) тёмная #e0e0e0, светлая
# #141413 — против приглушённого --text-secondary строки
DATE_DARK, DATE_LIGHT = 'rgb(224, 224, 224)', 'rgb(20, 20, 19)'


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
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': 'И', 'name': 'Инструктаж (повторный)', 'color': '#B3E5FC'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'дневной',
   'смена': None, 'шаблон_ротации': None, 'старт_цикла': None,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

NOTE_101 = 'протокол № 12, ведёт Иванов А.А.'

# Таблица Список_И_и_ПЗ (формат listTrainings): столбец E
# «сокращение» — краткие названия пунктов (Task 416); у «ПЗ-ПБ»
# ячейка ПУСТАЯ (проверка деградации — строка без префикса)
INSTR_LIST = [
  {'название': 'Повторный инструктаж по рабочим инструкциям',
   'вид': 'инструктаж', 'периодичность': 6, 'основание': 'ПОТ',
   'сокращение': 'ОТ-РИ', 'в составе': ''},
  {'название': 'Повторный инструктаж по инструкции № 9-ОГЭ',
   'вид': 'инструктаж', 'периодичность': 3, 'основание': 'ЭБ',
   'сокращение': '9-ОГЭ',
   'в составе': 'Повторный инструктаж по рабочим инструкциям'},
  {'название': 'Периодическая проверка знаний в электроустановках до 1000 В',
   'вид': 'проверка_знаний', 'периодичность': 12, 'основание': 'ПТЭЭП',
   'сокращение': 'ПЗ-1000В', 'в составе': ''},
  {'название': 'Проверка знаний по промышленной безопасности',
   'вид': 'проверка_знаний', 'периодичность': 12, 'основание': 'РТН',
   'сокращение': '', 'в составе': ''},
]


# Записи «Инструктажей» 2026 года (формат 'done' сервера):
#  101 — инструктаж ОТ-РИ с примечанием, выполнение = 0 (отмечается);
#  102 — ПЗ-1000В без примечания, просрочена;
#  103 — 9-ОГЭ УЖЕ ВЫПОЛНЕНА (проверка «не тускнеет»);
#  104 — ПЗ пункта с ПУСТЫМ сокращением (строка без префикса);
#  105 — тема «вне списка» (нет пункта шаблона)
def T(tid, tab, tip, tema, d, comment, done, late):
    return {'id': tid, 'таб_номер': tab, 'тип': tip, 'тема': tema,
            'дата_начала': d, 'дата_окончания': d,
            'длительность_дней': 1, 'комментарий': comment,
            'дата_проведения': d, 'выполнение': done, 'просрочен': late}


TRAININGS = [
  T(101, '017', 'инструктаж',
    'Повторный инструктаж по рабочим инструкциям',
    '2026-03-15', NOTE_101, 0, 0),
  T(102, '017', 'проверка_знаний',
    'Периодическая проверка знаний в электроустановках до 1000 В',
    '2026-05-20', '', 0, 1),
  T(103, '017', 'инструктаж',
    'Повторный инструктаж по инструкции № 9-ОГЭ',
    '2026-02-10', '', 1, 0),
  T(104, '017', 'проверка_знаний',
    'Проверка знаний по промышленной безопасности',
    '2026-04-05', 'по графику РТН', 0, 0),
  T(105, '017', 'инструктаж',
    'Аварийный внеплановый инструктаж',
    '2026-09-02', 'по предписанию № 4-ОТ', 0, 0),
]
INSTR_ALL = list(TRAININGS)
ENTRIES = []


def E(day, tab, status, source):
    return {'дата': '2026-05-%02d' % day, 'таб_номер': tab,
            'статус': status, 'переработка': 0, 'праздник': 0,
            'источник': source, 'дата_обновления':
            '2026-11-01T08:00:00.000Z', 'замещает': None,
            'инструкция': None, 'комментарий': '', 'часы': None,
            'время_начала': None, 'время_окончания': None}


VACATIONS = []
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
        return {'ok': True, 'data': {'trainings': TRAININGS,
                'instrList': INSTR_LIST, 'instrAll': INSTR_ALL,
                'eventsAll': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': PPE}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.setTrainingDone':
        rid = int(body.get('id', 0) or 0)
        val = int(body.get('выполнение', 0) or 0)
        # сервер Task 554 (srvVer 554): перенос примечаний жив;
        # для 556 достаточно отметить выполнение (без created)
        return {'ok': True, 'data': {'id': rid,
                'выполнение': val, 'просрочен': 0, 'srvVer': '554',
                'autoNote': '', 'created': [], 'updated': [],
                'skipped': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Снимок блока инструктажей КАРТОЧКИ «Работники»: строки записей с
# computed-стилями (отступ/дата) и ГЕОМЕТРИЕЙ (rect-ы: свотч/код/
# имя/кнопки к краям, поле текста растянуто); ВИДИМЫЙ зазор после
# краткого — rect ПЕРВОГО СИМВОЛА .ws-tr-rest (Range): bbox всего
# .ws-tr-rest при переносах длинной темы начинается левее (урок
# первой проверки — фигура объединяет все строки переноса)
INSTR_CARD = """(() => {
    const cards = Array.from(document.querySelectorAll('.ws-wcard'));
    const card = cards.find(c => {
        const h = c.querySelector('.ws-whead-t');
        return h && /Повторные инструктажи/.test(h.textContent || '');
    });
    if (!card) return null;
    const R = el => { const b = el.getBoundingClientRect();
        return { l: +b.left.toFixed(1), r: +b.right.toFixed(1),
                 w: +b.width.toFixed(1) }; };
    const rows = Array.from(
        card.querySelectorAll('.ws-popup-row.ws-popup-event')).map(r => {
        const name = r.querySelector('.ws-popup-name');
        const sh = r.querySelector('.ws-tr-short');
        const rest = r.querySelector('.ws-tr-rest');
        const dt = r.querySelector('.ws-tr-date');
        const chk = r.querySelector('.ws-done-chk');
        const nt = r.querySelector('.ws-tr-note');
        const sw = r.querySelector('.ws-popup-swatch');
        const cd = r.querySelector('.ws-popup-code');
        const ac = r.querySelector('.ws-act-col');
        const rS = getComputedStyle(r);
        const dS = dt ? getComputedStyle(dt) : null;
        let firstChar = null;
        if (rest && rest.firstChild && rest.firstChild.nodeType === 3) {
            const rng = document.createRange();
            rng.setStart(rest.firstChild, 0);
            rng.setEnd(rest.firstChild, 1);
            const fb = rng.getBoundingClientRect();
            firstChar = { l: +fb.left.toFixed(1), r: +fb.right.toFixed(1) };
        }
        return { text: r.textContent.replace(/\\s+/g, ' ').trim(),
                 done: r.classList.contains('ws-row-done'),
                 nameOpacity: name ? getComputedStyle(name).opacity : null,
                 shortMargin: sh ? getComputedStyle(sh).marginRight : null,
                 shortRect: sh ? R(sh) : null,
                 restRect: rest ? R(rest) : null,
                 firstChar: firstChar,
                 date: dt ? { text: dt.textContent.trim(),
                              color: dS.color, weight: dS.fontWeight,
                              size: dS.fontSize } : null,
                 note: nt ? nt.textContent.trim() : null,
                 chkOn: chk ? chk.classList.contains('ws-done-on') : null,
                 geo: { padL: rS.paddingLeft, padR: rS.paddingRight,
                        gap: rS.columnGap,
                        row: R(r), swatch: sw ? R(sw) : null,
                        code: cd ? R(cd) : null,
                        name: name ? R(name) : null,
                        acts: ac ? R(ac) : null } };
    });
    return { rows: rows,
             shorts: card.querySelectorAll('.ws-tr-short').length };})()"""


def instr_card(page):
    return page.evaluate(INSTR_CARD)


def run_flow(page):
    # страница «Работники» уже открыта (кнопка #wsWorkersBtn скрыта
    # на ней) — выбор работника перерисовывает карточку, как в
    # task555-browser-check.py
    page.evaluate("WorkSchedule.selectWorkersTab('017')")
    page.wait_for_timeout(700)
    return instr_card(page)


def click_done(page, date_marker):
    # клик по галочке строки с датой-маркером; возврат — ОБЪЕКТ
    # (примитив true playwright порой отдаёт как None — урок 554)
    return page.evaluate("""(() => {
        const rows = Array.from(
            document.querySelectorAll('.ws-wcard .ws-popup-row.ws-popup-event'));
        const row = rows.find(r =>
            (r.textContent || '').indexOf('%s') !== -1);
        if (!row) return { ok: false, why: 'row' };
        const chk = row.querySelector('.ws-done-chk');
        if (!chk) return { ok: false, why: 'chk' };
        chk.click();
        return { ok: true };})()""" % date_marker)


def near(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


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
        # isolateLocalStorage (kip8test) — ключи с префиксом
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t556');" +
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

        page.select_option('#wsMonthSel', str(M))
        page.select_option('#wsYearSel', str(Y))
        page.wait_for_timeout(2000)

        print('== A: строка 101 — отступ после краткого, дата ярче, геометрия ==')
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(900)
        card = run_flow(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        check('A: отступ после краткого — margin-right 6px (.ws-tr-short)',
              r101 and r101['shortMargin'] == '6px', r101 and r101['shortMargin'])
        vis_gap = (r101 and r101['shortRect'] and r101['firstChar'] and
                   r101['firstChar']['l'] - r101['shortRect']['r'])
        check('A: ВИДИМЫЙ зазор краткое→остальное ≈ 6px (первый символ)',
              near(vis_gap, 6, 1.6), vis_gap)
        check('A: дата 15.03.2026 — span.ws-tr-date в строке',
              r101 and r101['date'] and
              r101['date']['text'] == '15.03.2026', r101 and r101['date'])
        check('A: дата ЯРЧЕ — цвет --text-primary (тёмная тема)',
              r101 and r101['date'] and
              r101['date']['color'] == DATE_DARK, r101 and r101['date'])
        check('A: дата — полужирная 600, размер строки (13px)',
              r101 and r101['date'] and
              r101['date']['weight'] == '600' and
              r101['date']['size'] == '13px', r101 and r101['date'])
        g = (r101 or {}).get('geo') or {}
        check('A: строка колонки — паддинги 6px/4px, gap 4px',
              g.get('padL') == '6px' and g.get('padR') == '4px' and
              g.get('gap') == '4px', g)
        check('A: свотч — у ЛЕВОГО края блока (≈6px, прежде 16px)',
              near((g.get('swatch') or {}).get('l'),
                   (g.get('row') or {}).get('l') + 6, 1.6),
              (g.get('swatch'), g.get('row')))
        check('A: кнопки (галочка/✎/✕) — у ПРАВОГО края (≈4px)',
              near((g.get('row') or {}).get('r'),
                   (g.get('acts') or {}).get('r') + 4, 1.6),
              (g.get('acts'), g.get('row')))
        check('A: поле текста растянуто — имя от кода+4px до колонки кнопок',
              near((g.get('name') or {}).get('l'),
                   (g.get('code') or {}).get('r') + 4, 2.2) and
              near((g.get('acts') or {}).get('l'),
                   (g.get('name') or {}).get('r') + 4, 2.2),
              (g.get('name'), g.get('code'), g.get('acts')))
        check('A: поле текста — заметно шире половины строки',
              (g.get('name') or {}).get('w', 0) >
              (g.get('row') or {}).get('w', 1) * 0.5,
              (g.get('name'), g.get('row')))
        shot(page, '01-workers-017-t556-dark.png')

        print('== B: строка 102 (ПЗ) — та же геометрия, дата яркая ==')
        r102 = next((r for r in rows if 'до 1000 В' in r['text']), None)
        g2 = (r102 or {}).get('geo') or {}
        check('B: паддинги 6px/4px и gap 4px — у всех строк блока',
              g2.get('padL') == '6px' and g2.get('padR') == '4px' and
              g2.get('gap') == '4px', g2)
        check('B: дата 20.05.2026 яркая (--text-primary)',
              r102 and r102['date'] and
              r102['date']['text'] == '20.05.2026' and
              r102['date']['color'] == DATE_DARK, r102 and r102['date'])
        check('B: отступ после краткого ПЗ — 6px',
              r102 and r102['shortMargin'] == '6px',
              r102 and r102['shortMargin'])

        print('== C: выполненная строка 103 — вид жив (не тускнеет) ==')
        r103 = next((r for r in rows if 'инструкции № 9-ОГЭ' in r['text']), None)
        g3 = (r103 or {}).get('geo') or {}
        check('C: .ws-popup-name — opacity 1 (НЕ тускнеет)',
              r103 and r103['nameOpacity'] == '1', r103 and r103['nameOpacity'])
        check('C: отступ 6px и дата яркая — у выполненной тоже',
              r103 and r103['shortMargin'] == '6px' and
              r103['date'] and r103['date']['color'] == DATE_DARK,
              r103 and (r103['shortMargin'], r103['date']))
        check('C: геометрия выполненной строки — та же (6/4/4)',
              g3.get('padL') == '6px' and g3.get('padR') == '4px' and
              g3.get('gap') == '4px', g3)

        print('== D: без префикса — дата ВСЁ РАВНО яркая ==')
        r104 = next((r for r in rows if 'промышленной безопасности' in
                     r['text']), None)
        check('D: пункт с ПУСТЫМ сокращением — БЕЗ .ws-tr-short',
              r104 and 'ws-tr-short' not in json.dumps(r104.get('date', {}))
              and r104['shortMargin'] is None, r104)
        check('D: …но дата — в span.ws-tr-date (яркая)',
              r104 and r104['date'] and
              r104['date']['text'] == '05.04.2026' and
              r104['date']['color'] == DATE_DARK, r104 and r104['date'])
        r105 = next((r for r in rows if 'Аварийный' in r['text']), None)
        check('D: «вне списка» — без префикса, дата яркая, примечание живо',
              r105 and r105['shortMargin'] is None and
              r105['date'] and r105['date']['text'] == '02.09.2026' and
              ' · «по предписанию № 4-ОТ»' in r105['text'],
              r105 and (r105['shortMargin'], r105['date']))

        print('== E: отметка выполнения — вид жив после перерисовки ==')
        clicked = click_done(page, '15.03.2026')
        page.wait_for_timeout(1200)
        check('E: галочка строки 101 нажата',
              bool(clicked) and clicked.get('ok') is True, repr(clicked))
        card = instr_card(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        check('E: галочка 101 стала зелёной',
              r101 and r101['chkOn'] is True, r101 and r101['chkOn'])
        check('E: текст отмеченной строки — opacity 1 (НЕ тускнеет)',
              r101 and r101['nameOpacity'] == '1', r101 and r101['nameOpacity'])
        check('E: отступ 6px и дата яркая — после перерисовки',
              r101 and r101['shortMargin'] == '6px' and
              r101['date'] and r101['date']['color'] == DATE_DARK,
              r101 and (r101['shortMargin'], r101['date']))
        gE = (r101 or {}).get('geo') or {}
        check('E: геометрия строки — прежняя (6px/4px, gap 4px)',
              gE.get('padL') == '6px' and gE.get('padR') == '4px' and
              gE.get('gap') == '4px', gE)
        check('E: полный текст и примечание на месте',
              r101 and 'Повторный инструктаж по рабочим инструкциям' in
              r101['text'] and ' · «' + NOTE_101 + '»' in r101['text'],
              r101 and r101['text'])
        shot(page, '02-workers-017-t556-after-done.png')

        print('== F: светлая тема — дата #141413, та же геометрия ==')
        page.evaluate(
            "localStorage.setItem('kip8test:app-theme','light');" +
            "document.documentElement.setAttribute('data-theme','light')")
        page.wait_for_timeout(600)
        card = run_flow(page)
        rows = (card or {}).get('rows', [])
        r101L = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        check('F: светлая тема — дата ЯРЧЕ (#141413)',
              r101L and r101L['date'] and
              r101L['date']['color'] == DATE_LIGHT,
              r101L and r101L['date'])
        check('F: отступ после краткого — 6px',
              r101L and r101L['shortMargin'] == '6px',
              r101L and r101L['shortMargin'])
        gL = (r101L or {}).get('geo') or {}
        check('F: поля 6px/4px и gap 4px — в светлой теме',
              gL.get('padL') == '6px' and gL.get('padR') == '4px' and
              gL.get('gap') == '4px', gL)
        shot(page, '03-workers-017-t556-light.png')

        print('== G: санитар ==')
        check('G: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()
        server.shutdown()

    print('\nИТОГО: %d/%d (pass/total), FAIL=%d' %
          (PASS, PASS + FAIL, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
