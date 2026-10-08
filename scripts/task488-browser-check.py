#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 488: browser-check — ДВЕ части заявки:
#  A) окно «Мероприятия в этот день»: заявка «кнопка отметки
#     осталась» — МАРКЕР-квадрат ws-done-chk УДАЛЁН (у выполненной
#     записи «И» НЕТ зелёного квадрата ✓ даже read-only): строка =
#     свотч + код + название; регресс Task 487 — кнопок
#     (✓-клик/✎/✕) по-прежнему нет; КЛИК по ячейке открывает окно
#     кодов + окно мероприятий; подстрока «дата · ФИО» жива;
#  B) десктоп-ховер (регресс 487): окно открывается БЕЗ клика,
#     строка «И» (выполнено=1) — БЕЗ маркера;
#  C) «Печать» (график) → предпросмотр → «Сохранить Excel»:
#     файл *.xlsx скачивается; валидация: zip валиден,
#     [Content_Types].xml — ПЕРВОЙ записью, docProps/core.xml +
#     docProps/app.xml в пакете, workbook.xml содержит bookViews,
#     дни 1–31 шапки — ЧИСЛАМИ (<v>N</v>, не текст), НЕТ
#     sheetProtection/workbookProtection (файл редактируемый);
#  D) «Работники» → «Скачать архив»: файл скачивается; валидация:
#     12 частей zip, CT первой, docProps, bookViews, листы без
#     защит.
# КОНТЕКСТ: мок Apps Script (порт 8999), 0 JS-ошибок, скриншоты.
import calendar
import datetime
import json
import os
import zipfile
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task488')
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


# --- Данные мока (как Task 487) ---
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
  # id 100: И ВЫПОЛНЕНО → в окне (Task 488) маркера БОЛЬШЕ НЕТ
  {'id': 100, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-5), 'дата_окончания': d(-5), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 1, 'просрочен': 0},
  # id 101: ПЗ НЕ выполнено → строка без маркера
  {'id': 101, 'тема': 'Проверка знаний до 1000В', 'тип': 'проверка_знаний',
   'дата_начала': d(-3), 'дата_окончания': d(-3), 'таб_номер': '017',
   'подразделение': '', 'выполнение': 0, 'просрочен': 1},
]
PPE = []
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


POPUP_STATE_JS = r"""(() => {
    const evp = document.getElementById('wsEventsPopup');
    const pop = document.getElementById('wsCellPopup');
    const rows = evp ? [...evp.querySelectorAll('.ws-popup-row.ws-popup-event')] : [];
    return {
        active: !!(evp && evp.classList.contains('active')),
        codesActive: !!(pop && pop.classList.contains('active')),
        sub: evp ? (evp.querySelector('.ws-events-sub') || {}).textContent || '' : '',
        rows: rows.map(r => ({
            code: r.querySelector('.ws-popup-code') ?
                  r.querySelector('.ws-popup-code').textContent.trim() : '',
            name: r.querySelector('.ws-popup-name') ?
                  r.querySelector('.ws-popup-name').textContent.trim() : '',
            hasChk: !!r.querySelector('.ws-done-chk'),
            anyChk: r.innerHTML.indexOf('ws-done-chk') !== -1,
            hasToggle: !!r.querySelector('[onclick*="toggleTrainingDone"]'),
            hasEdit: !!r.querySelector('[title="Редактировать"]'),
            hasDel: !!r.querySelector('[title="Удалить"]'),
            swatch: !!r.querySelector('.ws-popup-swatch')
        }))};})"""

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
    # Task 486: тихое обновление (4 с от старта) — дождаться
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t488');" +
            "localStorage.setItem('kip8test:app-theme','dark');")


def validate_xlsx(path, expect_parts=None):
    """Валидация «простого редактируемого» xlsx: zip, CT первым,
    docProps, bookViews, числа дней, отсутствие защит."""
    res = {}
    try:
        z = zipfile.ZipFile(path)
        res['zip_ok'] = z.testzip() is None
        names = z.namelist()
        res['ct_first'] = names[0] == '[Content_Types].xml'
        res['docprops'] = ('docProps/core.xml' in names and
                           'docProps/app.xml' in names)
        wbxml = z.read('xl/workbook.xml').decode('utf-8')
        res['bookviews'] = '<bookViews>' in wbxml
        res['no_wb_protect'] = 'workbookProtection' not in wbxml
        res['no_sheet_protect'] = True
        for n in names:
            if 'worksheets' in n:
                sh = z.read(n).decode('utf-8')
                if 'sheetProtection' in sh:
                    res['no_sheet_protect'] = False
        if 'xl/worksheets/sheet1.xml' in names:
            sh1 = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
            import re
            # дни шапки — числа (не inlineStr)
            res['days_numeric'] = bool(re.search(
                r'<c r="B4"[^>]*><v>1</v></c>', sh1)) or bool(
                re.search(r'<c r="B4"[^>]*><v>\d+</v></c>', sh1))
            res['days_not_text'] = not re.search(
                r't="inlineStr"[^>]*><is><t>\d+</t></is>', sh1)
        if expect_parts:
            res['parts'] = len(names)
            res['parts_ok'] = len(names) == expect_parts
        # XML каждой части парсится
        import xml.etree.ElementTree as ET
        res['xml_ok'] = True
        for n in names:
            try:
                ET.fromstring(z.read(n))
            except Exception:
                res['xml_ok'] = False
    except Exception as e:
        res['zip_ok'] = False
        res['err'] = str(e)
    return res


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A: ДЕСКТОП 1280x720, edit — КЛИК: маркера НЕТ ==')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720},
                                  accept_downloads=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(seed_ls())
        setup_routes(ctx)
        open_grid(page)

        # A1: КЛИК по ячейке И (выполнение=1) — окно БЕЗ маркера
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.click('[data-testid="hc"]')
        page.wait_for_timeout(350)
        ps1 = page.evaluate(POPUP_STATE_JS)
        check('клик: окно мероприятий открылось', ps1['active'], ps1)
        check('клик: окно кодов тоже открылось (редактор)',
              ps1['codesActive'], ps1)
        r_i = [r for r in ps1['rows'] if r['code'] == 'И']
        check('СТРОКА И (выполнено=1): МАРКЕРА НЕТ (заявка «кнопка '
              'отметки осталась»)', r_i and not r_i[0]['hasChk'] and
              not r_i[0]['anyChk'], ps1)
        check('строка И: НИКАКИХ кнопок (✓-клик/✎/✕, регресс 487)',
              r_i and not r_i[0]['hasToggle'] and not r_i[0]['hasEdit'] and
              not r_i[0]['hasDel'], ps1)
        check('строка И: свотч + код + название живы',
              r_i and r_i[0]['swatch'] and r_i[0]['name'] != '', ps1)
        check('подстрока «дата · ФИО» жива',
              ps1['sub'].find('Иванов') != -1 and ps1['sub'].find('.') != -1,
              ps1)
        shot(page, 'a-click-popup-instr-done-no-marker.png')
        page.keyboard.press('Escape')
        page.wait_for_timeout(250)

        # A2: КЛИК по ПЗ (не выполнено) — тоже чисто текстовая строка
        page.evaluate(MARK_JS, ['017', dnum(-3)])
        page.click('[data-testid="hc"]')
        page.wait_for_timeout(350)
        ps2 = page.evaluate(POPUP_STATE_JS)
        r_pz = [r for r in ps2['rows'] if r['code'] == 'ПЗ']
        check('строка ПЗ: маркера НЕТ и кнопок НЕТ',
              r_pz and not r_pz[0]['hasChk'] and not r_pz[0]['hasToggle'] and
              not r_pz[0]['hasEdit'] and not r_pz[0]['hasDel'], ps2)
        page.keyboard.press('Escape')
        page.wait_for_timeout(600)

        # A3: ХОВЕР по И (выполнено) — окно без маркера (регресс 487)
        page.evaluate(MARK_JS, ['017', dnum(-5)])
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        ps3 = page.evaluate(POPUP_STATE_JS)
        check('ховер: окно открылось БЕЗ клика (регресс 487)',
              ps3['active'] and not ps3['codesActive'], ps3)
        r_i3 = [r for r in ps3['rows'] if r['code'] == 'И']
        check('ховер: строка И — маркера НЕТ (Task 488)',
              r_i3 and not r_i3[0]['hasChk'] and not r_i3[0]['anyChk'], ps3)
        shot(page, 'b-hover-popup-no-marker.png')
        page.mouse.move(10, 300)
        page.wait_for_timeout(600)

        # ==============================================================
        print('== B: «Печать» → предпросмотр → «Сохранить Excel» ==')
        # кнопка «Печать» в тулбаре табеля (id=wsPrintBtn)
        try:
            page.click('#wsPrintBtn', timeout=6000)
            page.wait_for_timeout(1400)
            xlsx_btn = page.locator('.wspprev-xlsx')
            check('диалог предпросмотра: кнопка «Сохранить Excel» видна',
                  xlsx_btn.count() > 0)
            shot(page, 'c-print-preview-dialog.png')
            with page.expect_download(timeout=15000) as dl_info:
                xlsx_btn.first.click()
            dl = dl_info.value
            path = os.path.join(SHOT_DIR, 'dl-tabel.xlsx')
            dl.save_as(path)
            check('файл скачался с именем *.xlsx',
                  dl.suggested_filename.endswith('.xlsx'),
                  dl.suggested_filename)
            res = validate_xlsx(path)
            check('график: zip валиден', res.get('zip_ok'), res)
            check('график: [Content_Types].xml — ПЕРВОЙ записью',
                  res.get('ct_first'), res)
            check('график: docProps (core+app) в пакете',
                  res.get('docprops'), res)
            check('график: bookViews в workbook.xml', res.get('bookviews'), res)
            check('график: дни 1–31 шапки — ЧИСЛАМИ',
                  res.get('days_numeric') and res.get('days_not_text'), res)
            check('график: защит НЕТ (лист/книга правятся)',
                  res.get('no_sheet_protect') and res.get('no_wb_protect'), res)
            check('график: XML всех частей парсится', res.get('xml_ok'), res)
        except Exception as e:
            check('график: скачивание Excel', False, str(e))
        try:
            page.keyboard.press('Escape')
            page.wait_for_timeout(300)
        except Exception:
            pass

        # ==============================================================
        print('== C: «Работники» → «Скачать архив» ==')
        try:
            # кнопка «Работники» в тулбаре (право edit есть)
            page.click('#wsWorkersBtn', timeout=6000)
            page.wait_for_timeout(1600)
            btn = page.locator('#wsWorkersArchiveBtn')
            check('страница работников: кнопка «Скачать архив» видна',
                  btn.count() > 0)
            shot(page, 'd-workers-archive-btn.png')
            with page.expect_download(timeout=15000) as dl_info2:
                btn.first.click()
            dl2 = dl_info2.value
            path2 = os.path.join(SHOT_DIR, 'dl-archive.xlsx')
            dl2.save_as(path2)
            check('архив скачался с именем *.xlsx',
                  dl2.suggested_filename.endswith('.xlsx'),
                  dl2.suggested_filename)
            res2 = validate_xlsx(path2, expect_parts=12)
            check('архив: zip валиден', res2.get('zip_ok'), res2)
            check('архив: CT — ПЕРВОЙ записью (прежде листы шли первыми)',
                  res2.get('ct_first'), res2)
            check('архив: docProps (core+app)', res2.get('docprops'), res2)
            check('архив: bookViews', res2.get('bookviews'), res2)
            check('архив: 12 частей (5 листов + 7 служебных)',
                  res2.get('parts_ok'), res2)
            check('архив: защит листов НЕТ', res2.get('no_sheet_protect'), res2)
            check('архив: XML всех частей парсится', res2.get('xml_ok'), res2)
        except Exception as e:
            check('архив: скачивание', False, str(e))

        check('JS-ошибок нет (A–C)', len(js_errors) == 0, js_errors[:5])
        ctx.close()
        browser.close()

    print('\nИТОГ: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
