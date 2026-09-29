#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 445: browser-check — заявка: «В разделе работников во вкладке
# Общая: в колонке Группа допуска справа от группы добавь отображение
# даты, так же как в блоке профиля работника. Колонки
# Отпуск/Мероприятия/Инструктажи убери. Кнопку "Сохранить архив"
# переименуй в "Скачать архив". Переделай структуру скачиваемого
# архива: Лист "Работники" (профили), Лист "Отпуска" (предыдущий и
# текущий годы), Лист "Инструктажи" (предыдущий, текущий и следующий
# годы), Лист "СИЗ", Лист "Мероприятия" (текущий год)».
# КОНТЕКСТ (мок-сервер, порт 8950): десктоп 1280 тёмная, Админ:
#   A: приложение + график;
#   B: «Работники» → «Общая»: 6 колонок (без Отпуск/Мероприятия/
#      Инструктажи), «Группа допуска» = «IV от 15.03.ГГГГ» (дата
#      последней проверки до 1000 В, как в профиле), «III» без даты,
#      «—» без группы; кнопка «Скачать архив»;
#   C: клик «Скачать архив»: скачивание .xlsx (10 частей ZIP),
#      workbook.xml — 5 листов по порядку; лист 1 Работники (3);
#      лист 2 Отпуска — прошлый+текущий годы; лист 3 Инструктажи —
#      prev/cur/next, без глубокой старой; лист 4 СИЗ (все + «До
#      износа»); лист 5 Мероприятия — только текущий год;
#      listVacations дёрган для прошлого года (ленивая подтяжка);
#      тост «Архив скачан — …»;
#   D: мобайл 375 — сводка + кнопка, 0 JS-ошибок;
#   E: 0 JS-ошибок ×2 контекста; скриншоты в download/screenshots-task445/.
import datetime
import io
import json
import os
import re
import zipfile
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8950
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)
NOWY = TODAY.year
D = lambda y, md: '%04d-%s' % (y, md)

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0955', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '',
   'дата_приёма': '2023-11-05', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр', 'группа_допуска': 'III',
   'комментарий': ''},
  {'таб_номер': '0377', 'ФИО': 'Яковлев Я. Я.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '',
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

# Инструктажи/проверки знаний: i700 — выполненная «до 1000 В» (дата
# для колонки «Группа допуска»); диапазон листа «Инструктажи» —
# prev/cur/next; i703 (позапрошлый год) — НЕ должен попасть
INSTR_ALL = [
    {'id': 700, 'таб_номер': '0871', 'тип': 'проверка_знаний',
     'тема': 'Проверка знаний электроустановок до 1000 В',
     'дата_начала': D(NOWY, '03-15'), 'дата_окончания': D(NOWY, '03-15'),
     'длительность_дней': 1, 'комментарий': '',
     'дата_проведения': D(NOWY, '03-15'), 'выполнение': 1, 'просрочен': 0},
    {'id': 701, 'таб_номер': '0871', 'тип': 'инструктаж',
     'тема': 'Повторный инструктаж по охране труда',
     'дата_начала': D(NOWY - 1, '06-10'), 'дата_окончания': D(NOWY - 1, '06-10'),
     'длительность_дней': 1, 'комментарий': '',
     'дата_проведения': D(NOWY - 1, '06-10'), 'выполнение': 1, 'просрочен': 0},
    {'id': 702, 'таб_номер': '0955', 'тип': 'инструктаж',
     'тема': 'Повторный инструктаж по пожарной безопасности',
     'дата_начала': D(NOWY + 1, '03-02'), 'дата_окончания': D(NOWY + 1, '03-02'),
     'длительность_дней': 1, 'комментарий': 'план',
     'дата_проведения': D(NOWY + 1, '03-02'), 'выполнение': 0, 'просрочен': 0},
    {'id': 703, 'таб_номер': '0955', 'тип': 'инструктаж',
     'тема': 'Очень старый инструктаж',
     'дата_начала': D(NOWY - 2, '01-15'), 'дата_окончания': D(NOWY - 2, '01-15'),
     'длительность_дней': 1, 'комментарий': '',
     'дата_проведения': D(NOWY - 2, '01-15'), 'выполнение': 1, 'просрочен': 1},
]
INSTR_LIST = [
  {'название': 'Повторный инструктаж по охране труда', 'вид': 'инструктаж',
   'периодичность': 6, 'основание': '', 'сокращение': 'Инстр. ОТ'},
]

# Мероприятия: e1 — текущий год (в листе), e2 — прошлый (НЕ в листе),
# e3 — период через границу прошлого/текущего (в листе)
EVENTS_ALL = [
    {'id': 801, 'таб_номер': '0871', 'тип': 'обучение',
     'тема': 'Курс по АСУ ТП',
     'дата_начала': D(NOWY, '09-03'), 'дата_окончания': D(NOWY, '09-05'),
     'длительность_дней': 3, 'комментарий': 'центр'},
    {'id': 802, 'таб_номер': '0955', 'тип': 'прогул',
     'тема': 'Прогул',
     'дата_начала': D(NOWY - 1, '05-05'), 'дата_окончания': D(NOWY - 1, '05-05'),
     'длительность_дней': 1, 'комментарий': ''},
    {'id': 803, 'таб_номер': '0377', 'тип': 'обучение',
     'тема': 'Обучение через границу года',
     'дата_начала': D(NOWY - 1, '12-29'), 'дата_окончания': D(NOWY, '01-05'),
     'длительность_дней': 8, 'комментарий': ''},
]

# Отпуска ПО ГОДАМ (сервер отдаёт план одного года)
VAC_BY_YEAR = {
    NOWY - 1: [
        {'id': 41, 'таб_номер': '0871', 'часть': 1,
         'дата_начала': D(NOWY - 1, '07-01'), 'дата_окончания': D(NOWY - 1, '07-14'),
         'дней': 14, 'комментарий': 'лето ' + str(NOWY - 1)},
    ],
    NOWY: [
        {'id': 42, 'таб_номер': '0955', 'часть': 1,
         'дата_начала': D(NOWY, '06-01'), 'дата_окончания': D(NOWY, '06-10'),
         'дней': 10, 'комментарий': ''},
    ],
}

PPE_STATE = [
  {'id': 11, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд',
   'наименование': 'Фильтрующая коробка противогаза',
   'дата_выдачи': D(NOWY, '08-17'), 'дата_изготовления': D(NOWY - 2, '01-15'),
   'срок_годности': '2 года', 'дата_окончания': D(NOWY, '01-15'),
   'примечание': 'банка №2'},
  {'id': 12, 'таб_номер': '0955', 'работник': 'Петров П. П.',
   'должность': 'Электромонтёр', 'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
]
API_CALLS = []   # [{action, body}]

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task445'
os.makedirs(SHOTS, exist_ok=True)


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def fresh_entries():
    out = []
    dim = (datetime.date(TODAY.year, TODAY.month % 12 + 1, 1) -
           datetime.timedelta(days=1)).day
    for day in range(1, dim + 1):
        iso_ = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, day)
        if day <= 5:
            out.append({'дата': iso_, 'таб_номер': '0871', 'статус': 'Д8',
                        'переработка': 0, 'праздник': 0, 'источник': 'авто'})
    return out


ENTRIES = fresh_entries()


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': True,
                                'flowmeter.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {
            'trainings': [], 'instrList': [dict(x) for x in INSTR_LIST],
            'instrAll': [dict(r) for r in INSTR_ALL],
            'eventsAll': [dict(r) for r in EVENTS_ALL]}}
    if action == 'workSchedule.listVacations':
        year = body.get('year')
        year = int(year) if year else None
        vacs = VAC_BY_YEAR.get(year, []) if year else []
        return {'ok': True, 'data': {'vacations': [dict(v) for v in vacs]}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': [dict(r) for r in PPE_STATE]}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in ENTRIES]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def vac_calls():
    return [c for c in API_CALLS if c['action'] == 'workSchedule.listVacations']


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t445-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        if body is None:
            body = {}
        if action.startswith('workSchedule.'):
            API_CALLS.append({'action': action, 'body': body})
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t445-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


GENERAL_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    var table = body ? body.querySelector('.ws-wgen-table') : null;
    var ths = table ? table.querySelectorAll('thead th') : [];
    var heads = [];
    for (var i = 0; i < ths.length; i++) heads.push(ths[i].textContent.trim());
    var btn = document.getElementById('wsWorkersArchiveBtn');
    var rows = table ? table.querySelectorAll('tbody tr') : [];
    var cells = [];
    for (var r = 0; r < rows.length; r++) {
        var tds = rows[r].querySelectorAll('td');
        var row = [];
        for (var c = 0; c < tds.length; c++) row.push(tds[c].textContent.trim());
        cells.push(row);
    }
    return {
        table: !!table, heads: heads, nRows: rows.length, cells: cells,
        btn: !!btn, btnText: btn ? btn.textContent.trim() : '',
        btnTitle: btn ? (btn.getAttribute('title') || '') : ''
    };
})"""


def xlsx_texts(zpath):
    """Разбор скачанного xlsx: {имя части: текст}; + данные листов."""
    with open(zpath, 'rb') as f:
        data = f.read()
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = zf.namelist()
    sheets = {}
    for n in names:
        if re.match(r'xl/worksheets/sheet\d+\.xml$', n):
            xml = zf.read(n).decode('utf-8')
            texts = re.findall(r'<t[^>]*>([^<]*)</t>', xml)
            sheets[n] = texts
    return names, sheets, zf.read('xl/workbook.xml').decode('utf-8')


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ =====
        print('=== Контекст: десктоп тёмная — вкладка «Общая» + архив ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                                  accept_downloads=True)
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось, график открыт',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))

        # ---------- B: «Общая» вкладка ----------
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(1200)
        g = page.evaluate(GENERAL_JS)
        check('B1: сводная таблица на «Общей»', g['table'] and g['nRows'] == 3,
              (g['table'], g['nRows']))
        check('B2: РОВНО 6 колонок — Таб/ФИО/Режим/Должность/Группа/Приём',
              g['heads'] == ['Таб. №', 'ФИО', 'Режим работы', 'Должность',
                             'Группа допуска', 'Дата приёма'], g['heads'])
        check('B3: колонок Отпуск/Мероприятия/Инструктажи НЕТ',
              all('Отпуск' not in h and 'Мероприятия' not in h and
                  'Инструктажи' not in h for h in g['heads']), g['heads'])
        fed = next((r for r in g['cells'] if 'Федосов' in r[1]), [])
        petr = next((r for r in g['cells'] if 'Петров' in r[1]), [])
        yak = next((r for r in g['cells'] if 'Яковлев' in r[1]), [])
        check('B4: Федосов — «IV от 15.03.%d» (дата проверки до 1000 В справа)'
              % NOWY, fed[4] == 'IV от 15.03.%d' % NOWY, fed)
        check('B5: Петров — только «III» (нет выполненной проверки)',
              petr[4] == 'III', petr)
        check('B6: Яковлев — «—» (нет группы)', yak[4] == '—', yak)
        check('B7: кнопка «Скачать архив» (не «Сохранить»)',
              g['btn'] and g['btnText'] == 'Скачать архив',
              (g['btn'], g['btnText']))
        check('B8: title кнопки перечисляет листы',
              'Отпуска' in g['btnTitle'] and 'СИЗ' in g['btnTitle'] and
              'Мероприятия' in g['btnTitle'], g['btnTitle'])
        page.screenshot(path=SHOTS + '/01-general-table.png')

        # ---------- C: скачивание архива ----------
        n_vac_before = len(vac_calls())
        with page.expect_download(timeout=8000) as dl_info:
            page.click('#wsWorkersArchiveBtn')
        dl = dl_info.value
        fname = dl.suggested_filename
        fpath = SHOTS + '/downloaded-' + fname
        dl.save_as(fpath)
        check('C1: скачан .xlsx с датой в имени',
              re.match(r'^Архив_по_работникам_\d{4}-\d{2}-\d{2}\.xlsx$',
                       fname) is not None, fname)
        names, sheets, wbxml = xlsx_texts(fpath)
        check('C2: ZIP из 10 частей (5 листов + 5 служебных)',
              len(names) == 10, names)
        order = [m for m in re.findall(r'name="([^"]+)"', wbxml)]
        sheet_names = [n for n in order if n in
                       ('Работники', 'Отпуска', 'Инструктажи', 'СИЗ',
                        'Мероприятия')]
        check('C3: workbook.xml — 5 листов по порядку',
              sheet_names == ['Работники', 'Отпуска', 'Инструктажи', 'СИЗ',
                              'Мероприятия'], sheet_names)
        s1 = sheets.get('xl/worksheets/sheet1.xml', [])
        s2 = sheets.get('xl/worksheets/sheet2.xml', [])
        s3 = sheets.get('xl/worksheets/sheet3.xml', [])
        s4 = sheets.get('xl/worksheets/sheet4.xml', [])
        s5 = sheets.get('xl/worksheets/sheet5.xml', [])
        check('C4: лист «Работники» — справочник 3 работников',
              'Федосов А. В.' in s1 and 'Петров П. П.' in s1 and
              'Яковлев Я. Я.' in s1, s1[:12])
        check('C5: лист «Отпуска» — шапка + прошлый и текущий годы',
              any('Часть' in t for t in s2) and
              ('01.07.%d' % (NOWY - 1)) in s2 and
              ('01.06.%d' % NOWY) in s2, s2[:16])
        check('C6: лист «Инструктажи» — prev/cur/next, БЕЗ позапрошлого',
              ('10.06.%d' % (NOWY - 1)) in s3 and
              ('15.03.%d' % NOWY) in s3 and
              ('02.03.%d' % (NOWY + 1)) in s3 and
              ('15.01.%d' % (NOWY - 2)) not in s3, s3[:16])
        check('C7: лист «СИЗ» — все записи, «До износа» без форматирования',
              'Фильтрующая коробка противогаза' in s4 and
              'До износа' in s4 and 'Очки закрытые' in s4, s4[:16])
        check('C8: лист «Мероприятия» — только текущий год',
              ('03.09.%d' % NOWY) in s5 and ('05.09.%d' % NOWY) in s5 and
              ('29.12.%d' % (NOWY - 1)) in s5 and
              ('05.05.%d' % (NOWY - 1)) not in s5, s5[:16])
        page.wait_for_timeout(600)
        toast = page.evaluate(
            "document.getElementById('toastMessage') ? " +
            "document.getElementById('toastMessage').textContent : ''")
        check('C9: тост «Архив скачан — …: 3 работника, 2 отпуска, …»',
              toast.startswith('Архив скачан') and
              '3 работника' in toast and '2 отпуска' in toast and
              '2 СИЗ' in toast and '2 мероприятия' in toast, toast)
        vac_years = [c['body'].get('year') for c in vac_calls()]
        check('C10: отпуска прошлого года подтянуты лениво '
              '(listVacations year=%d после клика)' % (NOWY - 1),
              len(vac_calls()) == n_vac_before + 1 and
              str(NOWY - 1) in [str(y) for y in vac_years], vac_years)
        page.screenshot(path=SHOTS + '/02-archive-toast.png')
        check('C11: 0 JS-ошибок (десктоп)', js_errors == [], js_errors[:3])
        ctx.close()

        # ===== мобайл 375 =====
        print('=== Контекст: мобайл 375 — «Общая» + кнопка ===')
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 812},
                                   accept_downloads=True)
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'dark', 'mobile')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        page2.click('#wsWorkersBtn')
        page2.wait_for_timeout(1200)
        g2 = page2.evaluate(GENERAL_JS)
        check('D1: мобайл — сводная таблица (6 колонок)',
              g2['table'] and len(g2['heads']) == 6, g2['heads'])
        check('D2: мобайл — «IV от 15.03.%d» в колонке группы' % NOWY,
              any(r[4] == 'IV от 15.03.%d' % NOWY for r in g2['cells']),
              [r[4] for r in g2['cells']])
        check('D3: мобайл — кнопка «Скачать архив» видна',
              g2['btn'] and g2['btnText'] == 'Скачать архив', g2['btnText'])
        # Task 445: скролл-обёртка — таблица ШИРЕ вьюпорта, свайп
        # открывает колонки «Группа допуска»/«Дата приёма»
        sc = page2.evaluate("""(function(){
            var w = document.querySelector('.ws-wgen-tscroll');
            if (!w) return {exists: false};
            var styles = getComputedStyle(w);
            return {exists: true, ox: styles.overflowX,
                    sw: w.scrollWidth, cw: w.clientWidth,
                    canScroll: w.scrollWidth > w.clientWidth};
        })""")
        check('D4: мобайл — таблица в скролл-обёртке (overflow-x auto)',
              sc.get('exists') and sc.get('ox') == 'auto', sc)
        check('D5: мобайл — свайп доступен (таблица шире контейнера)',
              sc.get('canScroll'), sc)
        page2.evaluate("""(function(){
            var w = document.querySelector('.ws-wgen-tscroll');
            w.scrollLeft = 9999;
        })""")
        page2.wait_for_timeout(400)
        g3 = page2.evaluate(GENERAL_JS)
        fed2 = next((r for r in g3['cells'] if 'Федосов' in r[1]), [])
        check('D6: мобайл — после свайпа видна «IV от 15.03.%d»' % NOWY,
              fed2 and fed2[4] == 'IV от 15.03.%d' % NOWY, fed2)
        page2.screenshot(path=SHOTS + '/03-mobile-general.png')
        check('D7: 0 JS-ошибок (мобайл)', js_errors2 == [], js_errors2[:3])
        ctx2.close()
        browser.close()

    print('\n===== ИТОГ: %d OK / %d FAIL =====' % (PASS, FAIL))
    return 1 if FAIL else 0


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
