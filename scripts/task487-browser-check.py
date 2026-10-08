#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 487: browser-check — ДВЕ части заявки:
#  A) окно «Мероприятия в этот день» у ячеек табеля — СПРАВОЧНОЕ
#     для ВСЕХ ролей (редактор как зритель): при ховере/клике в
#     строках НЕТ ни одной из трёх кнопок (✓-клик Task 482,
#     ✎ Task 309, ✕ Task 309); состояние выполнения — read-only
#     маркер ws-done-on ws-done-ro (тултип «Выполнено»);
#  B) ДЕСКТОП (≥1024px + мышь): ХОВЕР по ячейке с мероприятием
#     открывает окно БЕЗ клика (без кловера), уход курсора
#     закрывает через grace 350 мс, вход НА окно — держит его,
#     пустая ячейка окно не открывает, открытый КЛИКОМ попап
#     ховером не трогается, Esc закрывает всё;
#  C) узкий десктоп 900×600 (мышь есть, вьюпорт <1024) — ховер
#     НЕ срабатывает (гейт ширины);
#  D) мобильный 375×812 + touch (hover: none) — ховер НЕ
#     срабатывает, КЛИК по ячейке работает как прежде;
#  E) ЗРИТЕЛЬ (min): клик по ячейке — ТОЛЬКО окно мероприятий
#     (окно кодов нет, Task 319 жив), кнопок нет.
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
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task487')
os.makedirs(SHOT_DIR, exist_ok=True)


def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)


def dnum(off):
    return int(d(off).split('-')[2])


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
TRAININGS = [
  # id 100: И ВЫПОЛНЕНО → read-only ✓ в окне
  {'id': 100, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-5), 'дата_окончания': d(-5), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 1, 'просрочен': 0},
  # id 101: ПЗ НЕ выполнено → строка без маркера
  {'id': 101, 'тема': 'Проверка знаний до 1000В', 'тип': 'проверка_знаний',
   'дата_начала': d(-3), 'дата_окончания': d(-3), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 0, 'просрочен': 1},
  # id 103: ОБ (не «Инструктажи») → без маркера вовсе
  {'id': 103, 'тема': 'Обучение по новой редакции инструкций', 'тип': 'обучение',
   'дата_начала': d(-2), 'дата_окончания': d(-2), 'таб_номер': '023',
   'подразделение': ''},
]
PPE = []
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
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


POPUP_STATE_JS = r"""(() => {
    const evp = document.getElementById('wsEventsPopup');
    const pop = document.getElementById('wsCellPopup');
    const closer = document.getElementById('wsPopupCloser');
    const rows = evp ? [...evp.querySelectorAll('.ws-popup-row.ws-popup-event')] : [];
    return {
        active: !!(evp && evp.classList.contains('active')),
        codesActive: !!(pop && pop.classList.contains('active')),
        closerActive: !!(closer && closer.classList.contains('active')),
        sub: evp ? (evp.querySelector('.ws-events-sub') || {}).textContent || '' : '',
        rows: rows.map(r => ({
            code: r.querySelector('.ws-popup-code') ?
                  r.querySelector('.ws-popup-code').textContent.trim() : '',
            chk: r.querySelector('.ws-done-chk') ?
                 r.querySelector('.ws-done-chk').className : null,
            chkTitle: r.querySelector('.ws-done-chk') ?
                      r.querySelector('.ws-done-chk').title : '',
            hasToggle: !!r.querySelector('[onclick*="toggleTrainingDone"]'),
            hasEdit: !!r.querySelector('[title="Редактировать"]'),
            hasDel: !!r.querySelector('[title="Удалить"]')
        }))};})"""

HOVERWIRED_JS = r"""(() => {
    const cells = [...document.querySelectorAll('#wsGridWrap td.ws-cell')];
    return {total: cells.length,
            enter: cells.filter(c => c.getAttribute('onmouseenter') || ''
                .indexOf('onCellHover') !== -1).length,
            leave: cells.filter(c => (c.getAttribute('onmouseleave') || '')
                .indexOf('onCellLeave') !== -1).length};})"""

# пометить ячейку (таб. номер + день) для page.hover — СНИМАЯ
# предыдущие метки (иначе локатор находит СТАРУЮ ячейку)
MARK_JS = r"""(([t, dn]) => {
    document.querySelectorAll('[data-testid="hc"]')
        .forEach(c => c.removeAttribute('data-testid'));
    const emp = document.querySelector('td.ws-emp-col[data-tab="' + t + '"]');
    const td = emp.closest('tr').querySelector('td[data-day="' + dn + '"]');
    td.setAttribute('data-testid', 'hc');
    return !!td;})"""


def open_grid(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1800)
    # Task 486: ТИХОЕ обновление (таймер 4 с от старта приложения)
    # перерисовывает открытый раздел — ждём его ЗАВЕРШЕНИЯ, чтобы
    # сетка была стабильна во время ховер-сценариев (иначе грид
    # перерисуется посреди теста: data-testid сотрётся, mouseleave
    # на старом td не придёт)
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


def seed_ls(edit=True):
    return ("try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t487');" +
            "localStorage.setItem('kip8test:app-theme','dark');")


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A: ДЕСКТОП 1280x720, edit, тёмная — ХОВЕР ==')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(seed_ls())
        setup_routes(ctx)
        open_grid(page)

        wired = page.evaluate(HOVERWIRED_JS)
        check('все ячейки несут onmouseenter/onmouseleave',
              wired['total'] > 50 and wired['enter'] == wired['total'] and
              wired['leave'] == wired['total'], wired)

        # A1: ховер по ячейке И (выполнено) — окно БЕЗ клика
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        ps1 = page.evaluate(POPUP_STATE_JS)
        check('ховер: окно «Мероприятия» открылось БЕЗ клика', ps1['active'], ps1)
        check('ховер: кловер НЕ активен (закрытие — уход курсора)',
              not ps1['closerActive'] and not ps1['codesActive'], ps1)
        r_i = [r for r in ps1['rows'] if r['code'] == 'И']
        check('строка И: read-only маркер ws-done-on ws-done-ro',
              r_i and r_i[0]['chk'] and 'ws-done-ro' in r_i[0]['chk'] and
              'ws-done-on' in r_i[0]['chk'], ps1)
        check('строка И: тултип «Выполнено»', r_i and
              r_i[0]['chkTitle'] == 'Выполнено', ps1)
        check('строка И: НИКАКИХ кнопок (✓-клик/✎/✕)',
              r_i and not r_i[0]['hasToggle'] and not r_i[0]['hasEdit'] and
              not r_i[0]['hasDel'], ps1)
        check('подстрока «дата · ФИО» жива (дд.мм.гггг)',
              ps1['sub'].find('Иванов') != -1 and ps1['sub'].find('.') != -1, ps1)
        shot(page, 'a-hover-popup-instr-done.png')

        # A2: уход курсора → закрытие по grace-таймеру
        page.mouse.move(10, 300)
        page.wait_for_timeout(600)
        ps2 = page.evaluate(POPUP_STATE_JS)
        check('уход курсора: окно закрылось (grace 350 мс)', not ps2['active'], ps2)

        # A3: курсор идёт НА окно — оно остаётся открыто
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        box = page.evaluate("""(() => {
            const b = document.getElementById('wsEventsPopup')
                .getBoundingClientRect();
            return {x: b.x, y: b.y, w: b.width, h: b.height};})()""")
        # путь: прочитать длинную тему — мышка на середину окна
        page.mouse.move(box['x'] + box['w'] / 2, box['y'] + box['h'] / 2,
                        steps=12)
        page.wait_for_timeout(600)
        ps3 = page.evaluate(POPUP_STATE_JS)
        check('курсор НА окне: окно остаётся открытым', ps3['active'], ps3)
        # уход с окна — закрылось
        page.mouse.move(10, 10)
        page.wait_for_timeout(500)
        ps3b = page.evaluate(POPUP_STATE_JS)
        check('уход с окна: окно закрылось', not ps3b['active'], ps3b)

        # A4: ховер по ПЗ (не выполнено) — строка без маркера, без кнопок
        page.evaluate(MARK_JS, ['017', dnum(-3)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        ps4 = page.evaluate(POPUP_STATE_JS)
        r_pz = [r for r in ps4['rows'] if r['code'] == 'ПЗ']
        check('ПЗ не выполнено: маркера НЕТ, кнопок НЕТ',
              r_pz and r_pz[0]['chk'] is None and not r_pz[0]['hasEdit'] and
              not r_pz[0]['hasToggle'] and not r_pz[0]['hasDel'], ps4)
        page.mouse.move(10, 300)
        page.wait_for_timeout(600)

        # A5: пустая ячейка — окно НЕ открывается
        page.evaluate(MARK_JS, ['023', dnum(6)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        ps5 = page.evaluate(POPUP_STATE_JS)
        check('пустая ячейка: ховер окно НЕ открывает', not ps5['active'], ps5)

        # A6: КЛИК по ячейке (редактор) — окно кодов + мероприятий,
        # ховер больше НЕ вмешивается, Esc закрывает всё
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.click('[data-testid="hc"]')
        page.wait_for_timeout(350)
        ps6 = page.evaluate(POPUP_STATE_JS)
        check('клик: окно кодов И окно мероприятий открыты',
              ps6['codesActive'] and ps6['active'], ps6)
        check('клик: кловер активен (кликовый режим)', ps6['closerActive'], ps6)
        r_i2 = [r for r in ps6['rows'] if r['code'] == 'И']
        check('клик-окно: кнопок тоже НЕТ (справочное)',
              r_i2 and not r_i2[0]['hasEdit'] and not r_i2[0]['hasDel'] and
              not r_i2[0]['hasToggle'], ps6)
        shot(page, 'a6-click-popup-both-windows.png')
        # ховер по ДРУГОЙ ячейке не должен ничего менять. Кловер
        # (оверлей) при живом клик-попапе перехватывает реальные
        # события — реальная мышь до ячеек НЕ ДОХОДИТ; вторая
        # линия защиты — гвард _popupCell: проверяем СИНТЕТИЧЕСКИМ
        # mouseenter (как в сценариях B/C), окно не должно меняться
        page.evaluate("""(() => {
            const emp = document.querySelector(
                'td.ws-emp-col[data-tab="023"]');
            const td = emp.closest('tr')
                .querySelector('td[data-day="%d"]');
            td.dispatchEvent(new MouseEvent('mouseenter'));})()"""
                     % dnum(-2))
        page.wait_for_timeout(400)
        ps6b = page.evaluate(POPUP_STATE_JS)
        check('открытый кликом попап: ховер НЕ вмешивается',
              ps6b['codesActive'] and ps6b['active'] and
              ps6b['closerActive'] and
              ps6b['sub'].find('Иванов') != -1 and
              any(r['code'] == 'И' for r in ps6b['rows']), ps6b)
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)
        ps6c = page.evaluate(POPUP_STATE_JS)
        check('Esc: оба окна закрылись', not ps6c['active'] and
              not ps6c['codesActive'], ps6c)
        # анти-дребезг: Esc-закрытие гейтит ховер 400 мс (браузер
        # переотправляет mouseenter при скрытии кловера — мышь стоит
        # на ячейке); уводим курсор и возвращаем ПОСЛЕ кулдауна —
        # окно открывается заново (реальный ховер жив)
        page.mouse.move(10, 300)
        page.wait_for_timeout(450)  # кулдаун истёк
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        ps6d = page.evaluate(POPUP_STATE_JS)
        check('после кулдауна ховер снова открывает окно',
              ps6d['active'] and not ps6d['codesActive'], ps6d)
        page.mouse.move(10, 300)
        page.wait_for_timeout(600)

        # A7: ОБ (не «Инструктажи») — ховер окно, строки без маркера
        page.evaluate(MARK_JS, ['023', dnum(-2)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        ps7 = page.evaluate(POPUP_STATE_JS)
        r_ob = [r for r in ps7['rows'] if r['code'] == 'ОБ']
        check('ОБ: окно открылось, маркера и кнопок нет',
              ps7['active'] and r_ob and r_ob[0]['chk'] is None and
              not r_ob[0]['hasEdit'], ps7)
        page.mouse.move(10, 300)
        page.wait_for_timeout(600)

        check('JS-ошибок нет (десктоп, edit)', not js_errors, js_errors[:4])
        ctx.close()

        # ==============================================================
        print('== B: УЗКИЙ десктоп 900x600 (мышь есть, вьюпорт <1024) ==')
        ctx = browser.new_context(viewport={'width': 900, 'height': 600})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(seed_ls())
        setup_routes(ctx)
        open_grid(page)
        # синтетический mouseenter на ячейке с И — окно НЕ открывается
        page.evaluate("""(() => {
            const emp = document.querySelector('td.ws-emp-col[data-tab="017"]');
            const td = emp.closest('tr')
                .querySelector('td[data-day="%d"]');
            td.dispatchEvent(new MouseEvent('mouseenter'));})()""" % dnum(-5))
        page.wait_for_timeout(400)
        psb = page.evaluate(POPUP_STATE_JS)
        check('вьюпорт <1024: ховер НЕ срабатывает (гейт ширины)',
              not psb['active'], psb)
        # медиа-выражения контекста — для протокола
        mm = page.evaluate("""(() => ({
            desktop: matchMedia('(min-width: 1024px)').matches,
            hover: matchMedia('(hover: hover)').matches,
            fine: matchMedia('(pointer: fine)').matches}))()""")
        check('контекст B: мышь есть, десктопа нет',
              mm['hover'] and mm['fine'] and not mm['desktop'], mm)
        check('JS-ошибок нет (узкий десктоп)', not js_errors, js_errors[:4])
        ctx.close()

        # ==============================================================
        print('== C: МОБИЛ 375x812 + touch — ховера нет, клик жив ==')
        ctx = browser.new_context(viewport={'width': 375, 'height': 812},
                                  has_touch=True, is_mobile=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(seed_ls())
        setup_routes(ctx)
        open_grid(page)
        page.evaluate("""(() => {
            const emp = document.querySelector('td.ws-emp-col[data-tab="017"]');
            const td = emp.closest('tr')
                .querySelector('td[data-day="%d"]');
            td.dispatchEvent(new MouseEvent('mouseenter'));})()""" % dnum(-5))
        page.wait_for_timeout(400)
        psc = page.evaluate(POPUP_STATE_JS)
        check('тач: ховер НЕ срабатывает (гейт hover:hover)',
              not psc['active'], psc)
        mm = page.evaluate("""(() => ({
            desktop: matchMedia('(min-width: 1024px)').matches,
            hover: matchMedia('(hover: hover)').matches}))()""")
        check('контекст C: ни десктопа, ни ховера', not mm['desktop'] and
              not mm['hover'], mm)
        # клик по ячейке с И работает как прежде (зритель-попап не нужен,
        # edit): открывается окно кодов + мероприятий
        page.evaluate("""(([t, dn]) => {
            const emp = document.querySelector('td.ws-emp-col[data-tab="' + t + '"]');
            const td = emp.closest('tr')
                .querySelector('td[data-day="' + dn + '"]');
            td.click();})""", ['017', dnum(-5)])
        page.wait_for_timeout(400)
        psd = page.evaluate(POPUP_STATE_JS)
        check('тач: КЛИК по ячейке работает (окна открыты)',
              psd['active'], psd)
        r_ic = [r for r in psd['rows'] if r['code'] == 'И']
        check('тач: в клик-окне кнопок нет (справочное)',
              r_ic and not r_ic[0]['hasEdit'] and not r_ic[0]['hasToggle'], psd)
        shot(page, 'c-mobile-click-popup.png')
        page.keyboard.press('Escape')
        check('JS-ошибок нет (мобил)', not js_errors, js_errors[:4])
        ctx.close()

        # ==============================================================
        print('== D: ЗРИТЕЛЬ (min): клик — только окно мероприятий ==')
        MODE['level'] = 'min'
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(seed_ls())
        setup_routes(ctx)
        open_grid(page)
        # ховер зрителю тоже доступен (справочное окно)
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        pse = page.evaluate(POPUP_STATE_JS)
        check('зритель: ховер открывает справочное окно', pse['active'], pse)
        check('зритель: окно кодов НЕ открывается',
              not pse['codesActive'], pse)
        r_iv = [r for r in pse['rows'] if r['code'] == 'И']
        check('зритель: read-only маркер, кнопок нет',
              r_iv and 'ws-done-ro' in (r_iv[0]['chk'] or '') and
              not r_iv[0]['hasToggle'] and not r_iv[0]['hasEdit'], pse)
        page.mouse.move(10, 300)
        page.wait_for_timeout(600)
        # клик зрителя — только окно мероприятий (Task 319 жив)
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.click('[data-testid="hc"]')
        page.wait_for_timeout(350)
        psf = page.evaluate(POPUP_STATE_JS)
        check('зритель, клик: ТОЛЬКО окно мероприятий (без кодов)',
              psf['active'] and not psf['codesActive'], psf)
        check('зритель, клик: кловер активен', psf['closerActive'], psf)
        shot(page, 'd-viewer-click-popup.png')
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)
        check('зритель: Esc закрыл окно',
              not page.evaluate(POPUP_STATE_JS)['active'])
        check('JS-ошибок нет (зритель)', not js_errors, js_errors[:4])
        ctx.close()
        MODE['level'] = 'edit'

    print('\n===== ИТОГ: %d OK, %d FAIL =====' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
