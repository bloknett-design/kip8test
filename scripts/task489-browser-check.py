#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 489: browser-check — заявка «Сотрудники»: ФИО → фамилия/
# имя/отчество (полные данные) + «дата_рождения» перед
# «комментарием»:
#  A) ШАХМАТКА: строки сотрудников — КАК ПРЕЖДЕ КРАТКОЕ ФИО
#     («Хадасевич А. С.»; полное НЕ показывается);
#  B) «Работники»: сводка «Общая» — краткое; КАРТОЧКА работника
#     (клик по табу-фамилии): шапка блока профиля — ПОЛНОЕ ФИО
#     («Хадасевич Александр Сергеевич · таб. № 2741»), «Дата
#     рождения» — ПОСЛЕДНЯЯ строка списка профиля (дд.мм.гггг);
#     легаси-работник (без ФИО_полное/даты) — краткое, без строки;
#  C) «Правка данных…»: шторка — поля Фамилия/Имя/Отчество/Дата
#     рождения, префилл ЧАСТЯМИ записи;
#  D) «Добавить работника»: поля живы, единое поле ФИО удалено;
#  E) «Скачать архив»: xlsx — лист «Работники» колонка ФИО =
#     ПОЛНОЕ имя (легаси — краткое), лист «Отпуска» — краткое;
#     zip валиден, CT первой, docProps, 12 частей, защит нет.
# КОНТЕКСТ: мок Apps Script (порт 8999), 0 JS-ошибок, скриншоты.
import calendar
import datetime
import json
import os
import re
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
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task489')
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


# --- Данные мока: НОВАЯ раскладка (части + ФИО_полное +
#     дата_рождения) + ОДНА легаси-запись (без частей) ---
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
  {'code': 'И', 'name': 'Инструктаж', 'color': '#B3E5FC'},
  {'code': 'ОБ', 'name': 'Обучение', 'color': '#D1C4E9'},
  {'code': 'ПЗ', 'name': 'Проверка знаний', 'color': '#FFCDD2'},
]
EMPLOYEES = [
  # новый формат: краткое ФИО + ПОЛНОЕ + части + дата рождения
  {'таб_номер': '2741', 'ФИО': 'Хадасевич А. С.',
   'ФИО_полное': 'Хадасевич Александр Сергеевич',
   'фамилия': 'Хадасевич', 'имя': 'Александр', 'отчество': 'Сергеевич',
   'тип': 'сменный', 'смена': 1, 'шаблон_ротации': 1,
   'старт_цикла': '%04d-%02d-01' % (Y, M), 'дата_приёма': '2014-09-01',
   'дата_рождения': '1985-03-15', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  # легаси-запись (кэш старого сервера): только краткое ФИО
  {'таб_номер': '0292', 'ФИО': 'Чикризов Ю.',
   'тип': 'сменный', 'смена': 3, 'шаблон_ротации': 1,
   'старт_цикла': '%04d-%02d-02' % (Y, M), 'дата_приёма': '2020-08-03',
   'в_архиве': 0, 'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
ENTRIES = [
  {'id': 1, 'дата': d(-6), 'таб_номер': '2741', 'статус': 'Д',
   'источник': 'авто'},
]
TRAININGS = []
PPE = []
VACATIONS = [
  {'id': 21, 'таб_номер': '2741', 'часть': 1,
   'дата_начала': '%04d-%02d-05' % (Y, M),
   'дата_окончания': '%04d-%02d-14' % (Y, M),
   'дней': 10, 'комментарий': ''},
]


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
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


CARD_JS = r"""(() => {
    const body = document.getElementById('wsWorkersBody');
    // блок 1 (профиль) — ПЕРВАЯ карточка-окно .ws-wcard
    const card = body ? body.querySelector('.ws-wcard') : null;
    const head = card ? card.querySelector('.ws-whead-name') : null;
    const fields = card ? [...card.querySelectorAll('.ws-emp-field')] : [];
    const last = fields.length ? fields[fields.length - 1] : null;
    return {
        head: head ? head.textContent.trim() : '',
        fields: fields.map(f => ({
            k: f.querySelector('.ws-emp-k') ?
               f.querySelector('.ws-emp-k').textContent.trim() : '',
            v: f.querySelector('.ws-emp-v') ?
               f.querySelector('.ws-emp-v').textContent.trim() : ''
        })),
        lastK: last && last.querySelector('.ws-emp-k') ?
               last.querySelector('.ws-emp-k').textContent.trim() : ''
    };})"""

SUMMARY_JS = r"""(() => {
    const t = document.querySelector('.ws-wgen-table');
    if (!t) return {rows: 0, fio: []};
    return {
        rows: t.querySelectorAll('tbody tr').length,
        fio: [...t.querySelectorAll('tbody tr td.ws-wgen-fio')]
            .map(td => td.textContent.trim())
    };})"""

GRID_JS = r"""(() => {
    const cells = [...document.querySelectorAll('td.ws-emp-col')];
    return cells.map(c => c.textContent.trim().slice(0, 60));
})"""

FORM_JS = r"""(() => {
    const g = id => { const e = document.getElementById(id);
        return e ? {live: true, value: e.value} : {live: false, value: ''}; };
    return {
        fam: g('wsEmpFam'), name: g('wsEmpName'), patr: g('wsEmpPatr'),
        birth: g('wsEmpBirth'), fio: g('wsEmpFio'),
        sheet: !!document.getElementById('wsEmpSheet')
    };})"""


def validate_xlsx(path):
    res = {}
    try:
        zf = zipfile.ZipFile(path)
        names = zf.namelist()
        res['zip_ok'] = True
        res['parts'] = len(names)
        res['parts_ok'] = (len(names) == 12)
        res['ct_first'] = (names[0] == '[Content_Types].xml')
        res['docprops'] = ('docProps/core.xml' in names and
                           'docProps/app.xml' in names)
        wb = zf.read('xl/workbook.xml').decode('utf-8')
        res['bookviews'] = ('<bookViews>' in wb)
        res['no_sheet_protect'] = all(
            'sheetProtection' not in zf.read(n).decode('utf-8', 'ignore')
            for n in names if n.startswith('xl/worksheets/'))
        # карта листов: имя → файл
        rels = zf.read('xl/_rels/workbook.xml.rels').decode('utf-8')
        rmap = dict(re.findall(
            r'Id="(rId\d+)"[^>]*Target="(worksheets/[^"]+)"', rels))
        sheets = {}
        for m in re.finditer(
                r'<sheet[^>]*name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
            sheets[m.group(1)] = 'xl/' + rmap.get(m.group(2), '')
        res['sheets'] = sheets
        res['xml_ok'] = True
        for n in names:
            if n.endswith('.xml'):
                re.compile(r'<[\w:]').search(zf.read(n).decode('utf-8',
                                                                'ignore'))
    except Exception as e:
        res['error'] = str(e)
    return res


def sheet_text(path, sheet_file):
    zf = zipfile.ZipFile(path)
    xml = zf.read(sheet_file).decode('utf-8')
    return ''.join(re.findall(r'<t[^>]*>([^<]*)</t>', xml))


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


def seed_ls():
    # сессия в localStorage (как 488): логин есть, кэш чистый
    return ("try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t489');" +
            "localStorage.setItem('kip8test:app-theme','dark');")


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print('Task 489 browser-check (порт %d): Сотрудники — ФИО → части'
          ' + дата рождения' % PORT)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1600, 'height': 900},
                                  accept_downloads=True)
        ctx.add_init_script(seed_ls())
        setup_routes(ctx)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))

        # ==============================================================
        print('== A: шахматка — «в других местах сокращённо» ==')
        open_grid(page)
        try:
            emp_cells = page.evaluate(GRID_JS)
            check('шахматка: строки сотрудников есть',
                  len(emp_cells) >= 2, emp_cells)
            check('шахматка: Хадасевич — КРАТКОЕ «Хадасевич А. С.»',
                  any('Хадасевич А. С.' in c for c in emp_cells), emp_cells)
            check('шахматка: ПОЛНОЕ имя НЕ показывается',
                  not any('Александр Сергеевич' in c for c in emp_cells))
            check('шахматка: легаси-запись — краткое «Чикризов Ю.»',
                  any('Чикризов Ю.' in c for c in emp_cells))
            shot(page, 'a-grid-short-fio.png')
        except Exception as e:
            check('шахматка: строки сотрудников', False, str(e))

        # ==============================================================
        print('== B: «Работники» — карточка (полное ФИО + дата рождения) ==')
        try:
            page.click('#wsWorkersBtn', timeout=6000)
            page.wait_for_timeout(1600)
            # сводка «Общая» — КРАТКОЕ
            summ = page.evaluate(SUMMARY_JS)
            check('сводка «Общая»: строки есть', summ.get('rows', 0) >= 2,
                  summ)
            check('сводка «Общая»: ФИО — КРАТКОЕ',
                  'Хадасевич А. С.' in summ.get('fio', []) and
                  'Чикризов Ю.' in summ.get('fio', []), summ)
            check('сводка «Общая»: полное НЕ показывается',
                  'Хадасевич Александр Сергеевич' not in
                  summ.get('fio', []))

            # карточка: клик по табу-фамилии (title = краткое ФИО)
            page.click('button[title="Хадасевич А. С."]', timeout=6000)
            page.wait_for_timeout(1200)
            card = page.evaluate(CARD_JS)
            check('карточка: шапка профиля — ПОЛНОЕ ФИО',
                  card.get('head') ==
                  'Хадасевич Александр Сергеевич · таб. №2741',
                  card.get('head'))
            check('карточка: краткое ФИО в шапке НЕ печатается',
                  'Хадасевич А. С.' not in card.get('head', ''))
            fields = card.get('fields', [])
            keys = [f['k'] for f in fields]
            check('карточка: «Дата рождения» — ПОСЛЕДНЯЯ строка профиля',
                  keys and keys[-1] == 'Дата рождения', keys)
            birth = [f for f in fields if f['k'] == 'Дата рождения']
            check('карточка: дата рождения дд.мм.гггг (15.03.1985)',
                  birth and birth[0]['v'] == '15.03.1985', fields)
            shot(page, 'b-card-full-fio-birth.png')

            # легаси-работник: краткое ФИО, строки даты нет
            page.click('button[title="Чикризов Ю."]', timeout=6000)
            page.wait_for_timeout(1200)
            card2 = page.evaluate(CARD_JS)
            check('легаси-карточка: шапка — краткое ФИО (фолбэк)',
                  card2.get('head') == 'Чикризов Ю. · таб. №0292',
                  card2.get('head'))
            keys2 = [f['k'] for f in card2.get('fields', [])]
            check('легаси-карточка: строки «Дата рождения» НЕТ',
                  'Дата рождения' not in keys2, keys2)
            shot(page, 'b-card-legacy-short.png')
        except Exception as e:
            check('«Работники»: карточка', False, str(e))

        # ==============================================================
        print('== C: «Правка данных…» — форма частями ==')
        try:
            page.click('button[title="Хадасевич А. С."]', timeout=6000)
            page.wait_for_timeout(1000)
            page.click('.ws-emp-editdata', timeout=6000)
            page.wait_for_timeout(900)
            form = page.evaluate(FORM_JS)
            check('форма: поля Фамилия/Имя/Отчество живы',
                  form.get('fam', {}).get('live') and
                  form.get('name', {}).get('live') and
                  form.get('patr', {}).get('live'), form)
            check('форма: поле «Дата рождения» живо',
                  form.get('birth', {}).get('live'), form)
            check('форма: единое поле ФИО УДАЛЕНО',
                  not form.get('fio', {}).get('live'), form)
            check('форма: префилл фамилии = «Хадасевич»',
                  form.get('fam', {}).get('value') == 'Хадасевич', form)
            check('форма: префилл имени = «Александр»',
                  form.get('name', {}).get('value') == 'Александр', form)
            check('форма: префилл отчества = «Сергеевич»',
                  form.get('patr', {}).get('value') == 'Сергеевич', form)
            check('форма: префилл даты рождения = 1985-03-15',
                  form.get('birth', {}).get('value') == '1985-03-15', form)
            shot(page, 'c-edit-form-parts.png')
            page.evaluate("WorkSchedule.closeEmployeeForm()")
            page.wait_for_timeout(500)
        except Exception as e:
            check('«Правка данных…»: форма', False, str(e))

        # ==============================================================
        print('== D: «Добавить работника» — поля живы ==')
        try:
            page.click('button.ws-wtab-general', timeout=6000)
            page.wait_for_timeout(700)
            page.click('#wsWorkersAddBtn', timeout=6000)
            page.wait_for_timeout(900)
            form = page.evaluate(FORM_JS)
            check('добавление: ТРИ поля имени живы и ПУСТЫ',
                  form.get('fam', {}).get('live') and
                  form.get('fam', {}).get('value') == '' and
                  form.get('name', {}).get('value') == '' and
                  form.get('patr', {}).get('value') == '', form)
            check('добавление: поле «Дата рождения» живо и пусто',
                  form.get('birth', {}).get('live') and
                  form.get('birth', {}).get('value') == '', form)
            shot(page, 'd-add-form.png')
            page.evaluate("WorkSchedule.closeEmployeeForm()")
            page.wait_for_timeout(500)
        except Exception as e:
            check('«Добавить работника»', False, str(e))

        # ==============================================================
        print('== E: «Скачать архив» — лист «Работники»: полное ФИО ==')
        try:
            page.click('button.ws-wtab-general', timeout=6000)
            page.wait_for_timeout(700)
            btn = page.locator('#wsWorkersArchiveBtn')
            check('страница работников: кнопка «Скачать архив» видна',
                  btn.count() > 0)
            with page.expect_download(timeout=15000) as dl_info:
                btn.first.click()
            dl = dl_info.value
            path = os.path.join(SHOT_DIR, 'dl-archive.xlsx')
            dl.save_as(path)
            check('архив скачался с именем *.xlsx',
                  dl.suggested_filename.endswith('.xlsx'),
                  dl.suggested_filename)
            res = validate_xlsx(path)
            check('архив: zip валиден', res.get('zip_ok'), res)
            check('архив: CT — ПЕРВОЙ записью', res.get('ct_first'), res)
            check('архив: docProps (core+app)', res.get('docprops'), res)
            check('архив: bookViews', res.get('bookviews'), res)
            check('архив: 12 частей', res.get('parts_ok'), res)
            check('архив: защит листов НЕТ', res.get('no_sheet_protect'),
                  res)
            sheets = res.get('sheets', {})
            check('архив: лист «Работники» в книге', 'Работники' in sheets,
                  sheets)
            wtxt = sheet_text(path, sheets.get('Работники', ''))
            check('лист «Работники»: колонка ФИО — ПОЛНОЕ имя',
                  'Хадасевич Александр Сергеевич' in wtxt, wtxt[:200])
            check('лист «Работники»: краткое ФИО НЕ выгружается',
                  'Хадасевич А. С.' not in wtxt)
            check('лист «Работники»: легаси-запись — как прежде краткое',
                  'Чикризов Ю.' in wtxt)
            vtxt = sheet_text(path, sheets.get('Отпуска', ''))
            check('лист «Отпуска»: КРАТКОЕ ФИО (как прежде)',
                  'Хадасевич А. С.' in vtxt, vtxt[:200])
            check('лист «Отпуска»: полное НЕ выгружается',
                  'Александр Сергеевич' not in vtxt)
            shot(page, 'e-workers-page.png')
        except Exception as e:
            check('архив: скачивание', False, str(e))

        check('JS-ошибок нет (A–E)', len(js_errors) == 0, js_errors[:5])
        ctx.close()
        browser.close()

    print('\nИТОГ: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
