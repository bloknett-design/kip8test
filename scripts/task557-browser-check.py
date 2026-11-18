#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 557 browser-check: перенос ДАТЫ в строках блока «Повторные
# инструктажи и периодическая проверка знаний» КАРТОЧКИ работника
# (страница «Работники», колонка .ws-wcol-instr) ПОСЛЕ Task
# 555/556. Заявка:
#   «Поменяй местами текст, дату поставь после краткого
#    наименования, а остальной текст под ними.»
# Сценарий (май 2026; работник 017; записи 2026; Список_И_и_ПЗ — 4
# пункта: ОТ-РИ (сокр.), 9-ОГЭ (сокр.), ПЗ-1000В (сокр.), ПЗ-ПБ
# (ПУСТАЯ ячейка E)):
#  A) строка 101 (инструктаж ОТ-РИ, примечание): ДВЕ строки —
#     ПЕРВАЯ: краткое (.ws-tr-short, синий #64B5F6, жирный 700,
#     14px) + дата (span.ws-tr-date ПОСЛЕ краткого, зазор ≈6px
#     margin-right Task 556, top тот же); ВТОРАЯ: остальной текст
#     (.ws-tr-rest display block, top НИЖЕ bottom даты) — полная
#     тема + примечание, БЕЗ даты; дата в строке РОВНО 1 раз;
#     дата ЯРЧЕ (--text-primary rgb(224,224,224), вес 600,
#     13px); геометрия Task 556 жива (паддинги 6px/4px, gap 4px,
#     свотч у левого края, кнопки у правого, имя растянуто);
#  B) строка 102 (ПЗ): краткое КРАСНОЕ #EF5350; та же двухстрочная
#     структура; дата 20.05.2026 яркая; геометрия жива;
#  C) выполненная строка 103: структура/дата живы, текст НЕ
#     тускнеет (opacity 1 — Task 555);
#  D) строки 104 (пункт с ПУСТЫМ сокращением) и 105 («вне
#     списка») — БЕЗ краткого: ОДНА строка (нет .ws-tr-short и
#     .ws-tr-rest), дата — в конце строки, ВСЁ РАВНО яркая;
#  E) отметка галочкой 101 — двухстрочная структура жива после
#     перерисовки, текст не тускнеет;
#  F) светлая тема — дата rgb(20,20,19), краткое #1565C0,
#     структура жива;
#  G) санитар: 0 JS-ошибок; скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8990
Y, M = 2026, 5
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task557')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# Цвета: краткое И синий (555), ПЗ красный (555); дата —
# --text-primary (Task 556): тёмная #e0e0e0, светлая #141413
SHORT_BLUE_DARK = 'rgb(100, 181, 246)'
SHORT_RED_DARK = 'rgb(239, 83, 80)'
SHORT_BLUE_LIGHT = 'rgb(21, 101, 192)'
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
# ячейка ПУСТАЯ (проверка деградации — строка без краткого)
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
#  104 — ПЗ пункта с ПУСТЫМ сокращением (строка без краткого);
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
        # сервер Task 554 (srvVer 554): для 557 достаточно
        # отметить выполнение (структура строки — КЛИЕНТ-Only)
        return {'ok': True, 'data': {'id': rid,
                'выполнение': val, 'просрочен': 0, 'srvVer': '554',
                'autoNote': '', 'created': [], 'updated': [],
                'skipped': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Снимок блока инструктажей КАРТОЧКИ «Работники»: строки записей с
# computed-стилями (краткое/дата/остальной текст) и ВЕРТИКАЛЬНОЙ
# геометрией (rect-ы: первая строка краткое+дата, вторая —
# .ws-tr-rest), плюс прежняя геометрия строки (Task 556)
INSTR_CARD = """(() => {
    const cards = Array.from(document.querySelectorAll('.ws-wcard'));
    const card = cards.find(c => {
        const h = c.querySelector('.ws-whead-t');
        return h && /Повторные инструктажи/.test(h.textContent || '');
    });
    if (!card) return null;
    const R = el => { const b = el.getBoundingClientRect();
        return { l: +b.left.toFixed(1), r: +b.right.toFixed(1),
                 t: +b.top.toFixed(1), b: +b.bottom.toFixed(1),
                 w: +b.width.toFixed(1), h: +b.height.toFixed(1) }; };
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
        const shS = sh ? getComputedStyle(sh) : null;
        const dS = dt ? getComputedStyle(dt) : null;
        const rS2 = rest ? getComputedStyle(rest) : null;
        return { text: r.textContent.replace(/\\s+/g, ' ').trim(),
                 done: r.classList.contains('ws-row-done'),
                 nameOpacity: name ? getComputedStyle(name).opacity : null,
                 short: sh ? { text: sh.textContent.trim(),
                               weight: shS.fontWeight,
                               size: shS.fontSize, color: shS.color,
                               rect: R(sh), margin: shS.marginRight } : null,
                 date: dt ? { text: dt.textContent.trim(),
                              color: dS.color, weight: dS.fontWeight,
                              size: dS.fontSize, rect: R(dt) } : null,
                 rest: rest ? { text: rest.textContent
                                 .replace(/\\s+/g, ' ').trim(),
                                display: rS2.display, size: rS2.fontSize,
                                rect: R(rest) } : null,
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
    # страница «Работники» уже открыта — выбор работника
    # перерисовывает карточку (как в task556-browser-check.py)
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t557');" +
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

        print('== A: строка 101 — дата после краткого, остальное ниже ==')
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(900)
        card = run_flow(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        sh, dt, rest = (r101 or {}).get('short'), (r101 or {}).get('date'), \
                       (r101 or {}).get('rest')
        check('A: краткое ПЕРВЫМ (ОТ-РИ, синий жирный 700/14px)',
              sh and sh['text'] == 'ОТ-РИ' and sh['weight'] == '700' and
              sh['size'] == '14px' and sh['color'] == SHORT_BLUE_DARK, sh)
        check('A: дата ПОСЛЕ краткого — зазор ≈6px (margin Task 556)',
              sh and dt and near(
                  dt['rect']['l'] - sh['rect']['r'], 6, 1.6),
              (sh and sh['rect'], dt and dt['rect']))
        check('A: дата на ПЕРВОЙ строке (top совпадает с кратким)',
              sh and dt and near(dt['rect']['t'], sh['rect']['t'], 3),
              (sh and sh['rect'], dt and dt['rect']))
        check('A: остальной текст ПОД ними (display block, ниже даты)',
              rest and rest['display'] == 'block' and dt and
              rest['rect']['t'] >= dt['rect']['b'] - 2,
              (rest and rest['display'], rest and rest['rect'],
               dt and dt['rect']))
        check('A: остальной текст — полная тема + примечание, БЕЗ даты',
              rest and 'Повторный инструктаж по рабочим инструкциям' in
              rest['text'] and '«' + NOTE_101 + '»' in rest['text'] and
              '15.03.2026' not in rest['text'], rest and rest['text'])
        check('A: дата в строке РОВНО один раз (внизу не повторяется)',
              r101 and r101['text'].count('15.03.2026') == 1,
              r101 and r101['text'])
        check('A: дата ЯРЧЕ --text-primary (тёмная), 600, 13px',
              dt and dt['color'] == DATE_DARK and dt['weight'] == '600' and
              dt['size'] == '13px', dt)
        g = (r101 or {}).get('geo') or {}
        check('A: геометрия 556 жива — паддинги 6px/4px, gap 4px',
              g.get('padL') == '6px' and g.get('padR') == '4px' and
              g.get('gap') == '4px', g)
        check('A: свотч у ЛЕВОГО края, кнопки у ПРАВОГО',
              near((g.get('swatch') or {}).get('l'),
                   (g.get('row') or {}).get('l') + 6, 1.6) and
              near((g.get('row') or {}).get('r'),
                   (g.get('acts') or {}).get('r') + 4, 1.6),
              (g.get('swatch'), g.get('acts'), g.get('row')))
        check('A: поле текста растянуто (имя > половины строки)',
              (g.get('name') or {}).get('w', 0) >
              (g.get('row') or {}).get('w', 1) * 0.5,
              (g.get('name'), g.get('row')))
        shot(page, '01-workers-017-t557-dark.png')

        print('== B: строка 102 (ПЗ) — красное краткое, та же структура ==')
        r102 = next((r for r in rows if 'до 1000 В' in r['text']), None)
        sh2, dt2, rest2 = (r102 or {}).get('short'), (r102 or {}).get('date'), \
                         (r102 or {}).get('rest')
        g2 = (r102 or {}).get('geo') or {}
        check('B: краткое ПЗ — КРАСНОЕ #EF5350 (тёмная)',
              sh2 and sh2['text'] == 'ПЗ-1000В' and
              sh2['color'] == SHORT_RED_DARK, sh2)
        check('B: дата после краткого (зазор ≈6px, первая строка)',
              sh2 and dt2 and near(
                  dt2['rect']['l'] - sh2['rect']['r'], 6, 1.6) and
              near(dt2['rect']['t'], sh2['rect']['t'], 3),
              (sh2 and sh2['rect'], dt2 and dt2['rect']))
        check('B: остальной текст — ниже даты (block)',
              rest2 and rest2['display'] == 'block' and dt2 and
              rest2['rect']['t'] >= dt2['rect']['b'] - 2,
              (rest2 and rest2['rect'], dt2 and dt2['rect']))
        check('B: дата 20.05.2026 яркая',
              dt2 and dt2['text'] == '20.05.2026' and
              dt2['color'] == DATE_DARK, dt2)
        check('B: геометрия — 6px/4px, gap 4px',
              g2.get('padL') == '6px' and g2.get('padR') == '4px' and
              g2.get('gap') == '4px', g2)

        print('== C: выполненная строка 103 — вид жив (не тускнеет) ==')
        r103 = next((r for r in rows if 'инструкции № 9-ОГЭ' in r['text']), None)
        sh3, dt3, rest3 = (r103 or {}).get('short'), (r103 or {}).get('date'), \
                         (r103 or {}).get('rest')
        check('C: .ws-popup-name — opacity 1 (НЕ тускнеет)',
              r103 and r103['nameOpacity'] == '1',
              r103 and r103['nameOpacity'])
        check('C: двухстрочная структура жива (дата после краткого)',
              sh3 and dt3 and rest3 and
              near(dt3['rect']['l'] - sh3['rect']['r'], 6, 1.6) and
              rest3['rect']['t'] >= dt3['rect']['b'] - 2,
              (sh3 and sh3['rect'], dt3 and dt3['rect'],
               rest3 and rest3['rect']))
        check('C: дата яркая и у выполненной',
              dt3 and dt3['color'] == DATE_DARK, dt3)

        print('== D: без краткого — ОДНА строка, дата в конце, яркая ==')
        r104 = next((r for r in rows if 'промышленной безопасности' in
                     r['text']), None)
        check('D: пункт с ПУСТЫМ сокращением — БЕЗ .ws-tr-short/.ws-tr-rest',
              r104 and r104['short'] is None and r104['rest'] is None, r104)
        check('D: …но дата — span.ws-tr-date (яркая, в конце строки)',
              r104 and r104['date'] and
              r104['date']['text'] == '05.04.2026' and
              r104['date']['color'] == DATE_DARK and
              ' · 05.04.2026 · «по графику РТН»' in r104['text'],
              r104 and (r104['date'], r104['text']))
        r105 = next((r for r in rows if 'Аварийный' in r['text']), None)
        check('D: «вне списка» — одна строка, дата яркая, примечание живо',
              r105 and r105['short'] is None and r105['rest'] is None and
              r105['date'] and r105['date']['text'] == '02.09.2026' and
              r105['date']['color'] == DATE_DARK and
              ' · «по предписанию № 4-ОТ»' in r105['text'],
              r105 and (r105['date'], r105['text']))

        print('== E: отметка выполнения — структура жива после перерисовки ==')
        clicked = click_done(page, '15.03.2026')
        page.wait_for_timeout(1200)
        check('E: галочка строки 101 нажата',
              bool(clicked) and clicked.get('ok') is True, repr(clicked))
        card = instr_card(page)
        rows = (card or {}).get('rows', [])
        r101 = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        sh, dt, rest = (r101 or {}).get('short'), (r101 or {}).get('date'), \
                       (r101 or {}).get('rest')
        check('E: галочка 101 стала зелёной',
              r101 and r101['chkOn'] is True, r101 and r101['chkOn'])
        check('E: текст отмеченной строки — opacity 1 (НЕ тускнеет)',
              r101 and r101['nameOpacity'] == '1',
              r101 and r101['nameOpacity'])
        check('E: двухстрочная структура — дата после краткого, ниже rest',
              sh and dt and rest and
              near(dt['rect']['l'] - sh['rect']['r'], 6, 1.6) and
              rest['rect']['t'] >= dt['rect']['b'] - 2,
              (sh and sh['rect'], dt and dt['rect'], rest and rest['rect']))
        check('E: полный текст, примечание и ОДНА дата на месте',
              r101 and 'Повторный инструктаж по рабочим инструкциям' in
              r101['text'] and ' · «' + NOTE_101 + '»' in r101['text'] and
              r101['text'].count('15.03.2026') == 1, r101 and r101['text'])
        gE = (r101 or {}).get('geo') or {}
        check('E: геометрия строки — прежняя (6px/4px, gap 4px)',
              gE.get('padL') == '6px' and gE.get('padR') == '4px' and
              gE.get('gap') == '4px', gE)
        shot(page, '02-workers-017-t557-after-done.png')

        print('== F: светлая тема — дата #141413, краткое #1565C0 ==')
        page.evaluate(
            "localStorage.setItem('kip8test:app-theme','light');" +
            "document.documentElement.setAttribute('data-theme','light')")
        page.wait_for_timeout(600)
        card = run_flow(page)
        rows = (card or {}).get('rows', [])
        r101L = next((r for r in rows if 'рабочим инструкциям' in r['text']), None)
        shL, dtL, restL = (r101L or {}).get('short'), (r101L or {}).get('date'), \
                         (r101L or {}).get('rest')
        check('F: светлая тема — дата ЯРЧЕ (#141413)',
              dtL and dtL['color'] == DATE_LIGHT, dtL)
        check('F: краткое — светлый синий #1565C0',
              shL and shL['color'] == SHORT_BLUE_LIGHT, shL)
        check('F: двухстрочная структура — в светлой теме жива',
              shL and dtL and restL and
              near(dtL['rect']['l'] - shL['rect']['r'], 6, 1.6) and
              restL['rect']['t'] >= dtL['rect']['b'] - 2,
              (shL and shL['rect'], dtL and dtL['rect'],
               restL and restL['rect']))
        gL = (r101L or {}).get('geo') or {}
        check('F: поля 6px/4px и gap 4px — в светлой теме',
              gL.get('padL') == '6px' and gL.get('padR') == '4px' and
              gL.get('gap') == '4px', gL)
        shot(page, '03-workers-017-t557-light.png')

        print('== G: санитар ==')
        check('G: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()
        server.shutdown()

    print('\nИТОГО: %d/%d (pass/total), FAIL=%d' %
          (PASS, PASS + FAIL, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
