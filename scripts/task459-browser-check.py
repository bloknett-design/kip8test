#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 459: browser-check — заявка: «В скачиваемом excel файле
# архива работников, на листе СИЗ, в таблице отсортируй строки по
# алфавиту фамилий в столбце Работник, а в столбце Должность
# оставь наименование должностей без указания разрядов».
# КОНТЕКСТ (мок-сервер, порт 8988): десктоп 1280 тёмная, Админ:
#   A: приложение + график;
#   B: «Работники» → «Общая»: кнопка «Скачать архив»;
#   C: клик → скачивание .xlsx: лист 4 «СИЗ» — строки ПО ФАМИЛИЯМ
#      (Арбузов → Петров → Федосов ×2 → Яковлев; таб. № порядок
#      ДРУГОЙ: 017→377→871→955), внутри группы — по наименованию
#      (Каска < Перчатки); «Должность» БЕЗ разрядов («Слесарь
#      КИПиА 5 разряд» → «Слесарь КИПиА», «Электромонтёр 4
#      разряда» → «Электромонтёр», «Слесарь по КИП и А 5-го
#      разряда» → «Слесарь по КИП и А», римские не задействованы —
#      «Инженер КИПиА» без изменений); слова «разряд» на листе НЕТ;
#      зебра групп; лист 1 «Работники» — справочник КАК ЕСТЬ (с
#      разрядами — заявка лист СИЗ не трогает); тост «…5 СИЗ»;
#   D: мобайл 375 — кнопка, 0 JS-ошибок; скриншоты в
#      download/kip8test-task459/.
import datetime
import io
import json
import os
import re
import zipfile
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8988
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)
NOWY = TODAY.year
D = lambda y, md: '%04d-%s' % (y, md)

# Таб. № порядок ПРОТИВОПОЛОЖЕН алфавиту фамилий: 017 Федосов →
# 377 Яковлев → 871 Петров → 955 Арбузов; алфавит: Арбузов →
# Петров → Федосов → Яковлев
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '377', 'ФИО': 'Яковлев Я. Я.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '',
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '',
   'комментарий': ''},
  {'таб_номер': '871', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '',
   'дата_приёма': '2023-11-05', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр 4 разряда', 'группа_допуска': 'III',
   'комментарий': ''},
  {'таб_номер': '955', 'ФИО': 'Арбузов А. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '',
   'дата_приёма': '2024-06-01', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь по КИП и А 5-го разряда', 'группа_допуска': '',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
]

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

# СИЗ: 5 записей, работник Яковлева — через ФОЛБЭК ФИО (поле пусто);
# у Федосова ДВЕ записи (проверка группы подряд + вторичной
# сортировки по наименованию: «Каска защитная» < «Перчатки»)
PPE_STATE = [
  {'id': 11, 'таб_номер': '017', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд',
   'наименование': 'Перчатки',
   'дата_выдачи': D(NOWY, '02-10'), 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
  {'id': 12, 'таб_номер': '017', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд',
   'наименование': 'Каска защитная',
   'дата_выдачи': D(NOWY, '01-15'), 'дата_изготовления': D(NOWY - 2, '03-01'),
   'срок_годности': '2 года', 'дата_окончания': D(NOWY, '03-01'),
   'примечание': ''},
  {'id': 13, 'таб_номер': '377', 'работник': '',
   'должность': 'Инженер КИПиА',
   'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
  {'id': 14, 'таб_номер': '871', 'работник': 'Петров П. П.',
   'должность': 'Электромонтёр 4 разряда',
   'наименование': 'Ботинки',
   'дата_выдачи': D(NOWY, '03-20'), 'дата_изготовления': '',
   'срок_годности': '1,5 года', 'дата_окончания': D(NOWY + 1, '09-20'),
   'примечание': ''},
  {'id': 15, 'таб_номер': '955', 'работник': 'Арбузов А. А.',
   'должность': 'Слесарь по КИП и А 5-го разряда',
   'наименование': 'Куртка утеплённая',
   'дата_выдачи': D(NOWY, '04-05'), 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': D(NOWY + 2, '04-05'),
   'примечание': 'До износа'},
]

VAC_BY_YEAR = {
    NOWY: [
        {'id': 42, 'таб_номер': '871', 'часть': 1,
         'дата_начала': D(NOWY, '06-01'), 'дата_окончания': D(NOWY, '06-10'),
         'дней': 10, 'комментарий': ''},
    ],
}

API_CALLS = []

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/kip8test-task459'
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
            out.append({'дата': iso_, 'таб_номер': '017', 'статус': 'Д8',
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
            'trainings': [], 'instrList': [], 'instrAll': [],
            'eventsAll': []}}
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


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t459-%s');" % tag +
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
                      body='not found (t459-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def sheet_rows(xml):
    """Строки листа: [[тексты ячеек по порядку], …] — пустые
    пропущенные ячейки не рвут порядок непустых колонок A/B."""
    rows = []
    for rm in re.finditer(r'<row r="(\d+)">(.*?)</row>', xml, re.S):
        texts = re.findall(r'<t[^>]*>([^<]*)</t>', rm.group(2))
        rows.append(texts)
    return rows


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ =====
        print('=== Контекст: десктоп тёмная — «Общая» + архив ===')
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
        g = page.evaluate("""(function(){
            var btn = document.getElementById('wsWorkersArchiveBtn');
            return {btn: !!btn, btnText: btn ? btn.textContent.trim() : ''};
        })""")
        check('B1: кнопка «Скачать архив» на вкладке «Общая»',
              g['btn'] and g['btnText'] == 'Скачать архив',
              (g['btn'], g['btnText']))
        page.screenshot(path=SHOTS + '/01-general-tab.png')

        # ---------- C: скачивание архива ----------
        with page.expect_download(timeout=8000) as dl_info:
            page.click('#wsWorkersArchiveBtn')
        dl = dl_info.value
        fname = dl.suggested_filename
        fpath = SHOTS + '/downloaded-' + fname
        dl.save_as(fpath)
        check('C1: скачан .xlsx с датой в имени',
              re.match(r'^Архив_по_работникам_\d{4}-\d{2}-\d{2}\.xlsx$',
                       fname) is not None, fname)

        with open(fpath, 'rb') as f:
            data = f.read()
        zf = zipfile.ZipFile(io.BytesIO(data))
        names = zf.namelist()
        check('C2: ZIP из 10 частей (5 листов + 5 служебных)',
              len(names) == 10, names)
        wbxml = zf.read('xl/workbook.xml').decode('utf-8')
        order = [m for m in re.findall(r'name="([^"]+)"', wbxml)]
        sheet_names = [n for n in order if n in
                       ('Работники', 'Отпуска', 'Инструктажи', 'СИЗ',
                        'Мероприятия')]
        check('C3: workbook.xml — 5 листов по порядку',
              sheet_names == ['Работники', 'Отпуска', 'Инструктажи', 'СИЗ',
                              'Мероприятия'], sheet_names)

        s1 = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
        s4 = zf.read('xl/worksheets/sheet4.xml').decode('utf-8')
        rows4 = sheet_rows(s4)

        # шапка листа СИЗ
        check('C4: шапка листа «СИЗ» прежняя (8 колонок)',
              rows4 and rows4[0] == ['Работник', 'Должность', 'Наименование',
                                     'Дата выдачи', 'Дата изготовления',
                                     'Срок годности', 'Дата окончания',
                                     'Примечание'],
              rows4[0] if rows4 else 'нет строк')
        check('C5: 5 строк данных СИЗ', len(rows4) == 6,
              len(rows4))

        # ЗАЯВКА 1: сортировка по АЛФАВИТУ ФАМИЛИЙ (не по таб. №)
        workers = [r[0] for r in rows4[1:]]
        check('C6: строки по фамилиям: Арбузов → Петров → Федосов ×2 → Яковлев',
              workers == ['Арбузов А. А.', 'Петров П. П.',
                          'Федосов А. В.', 'Федосов А. В.',
                          'Яковлев Я. Я.'], workers)
        # внутри группы Федосова — по наименованию (Каска < Перчатки)
        fed_names = [r[2] for r in rows4[1:] if r[0] == 'Федосов А. В.']
        check('C7: внутри группы Федосова — по наименованию '
              '(Каска защитная < Перчатки)',
              fed_names == ['Каска защитная', 'Перчатки'], fed_names)

        # ЗАЯВКА 2: должности БЕЗ разрядов
        positions = [r[1] for r in rows4[1:]]
        check('C8: «Должность» без разрядов — точные значения',
              positions == ['Слесарь по КИП и А', 'Электромонтёр',
                            'Слесарь КИПиА', 'Слесарь КИПиА',
                            'Инженер КИПиА'], positions)
        check('C9: слова «разряд» на листе «СИЗ» НЕТ',
              'разряд' not in s4,
              [t for t in re.findall(r'<t[^>]*>([^<]*)</t>', s4)
               if 'разряд' in t])
        # Яковлев — через фолбэк ФИО (поле «работник» пусто в моке)
        check('C10: пустое поле «работник» — ФИО из справочника (Яковлев)',
              rows4[5][0] == 'Яковлев Я. Я.', rows4[5])

        # зебра: группа Федосова — ОДНОЙ полосой (строки 4-5: s="2")
        check('C11: зебра групп: Арбузов (стр.2) без заливки, Петров (стр.3) '
              's="2", Федосов ×2 (стр.4-5) без, Яковлев (стр.6) s="2"',
              '<c r="A2" t="inlineStr">' in s4 and
              '<c r="A3" t="inlineStr" s="2">' in s4 and
              '<c r="A4" t="inlineStr">' in s4 and
              '<c r="A5" t="inlineStr">' in s4 and
              '<c r="A6" t="inlineStr" s="2">' in s4)

        # регресс: справочник «Работники» — должности КАК ЕСТЬ (с разрядами)
        check('C12: лист «Работники» — справочник не тронут '
              '(должности с разрядами как есть)',
              'Слесарь КИПиА 5 разряд' in s1 and
              'Электромонтёр 4 разряда' in s1 and
              'Слесарь по КИП и А 5-го разряда' in s1)

        page.wait_for_timeout(600)
        toast = page.evaluate(
            "document.getElementById('toastMessage') ? " +
            "document.getElementById('toastMessage').textContent : ''")
        check('C13: тост «Архив скачан — …: 4 работника, … 5 СИЗ…»',
              toast.startswith('Архив скачан') and
              '4 работника' in toast and '5 СИЗ' in toast, toast)
        page.screenshot(path=SHOTS + '/02-archive-toast.png')
        check('C14: 0 JS-ошибок (десктоп)', js_errors == [], js_errors[:3])
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
        g2 = page2.evaluate("""(function(){
            var btn = document.getElementById('wsWorkersArchiveBtn');
            return {btn: !!btn, btnText: btn ? btn.textContent.trim() : ''};
        })""")
        check('D1: мобайл — кнопка «Скачать архив» видна',
              g2['btn'] and g2['btnText'] == 'Скачать архив', g2['btnText'])
        page2.screenshot(path=SHOTS + '/03-mobile-general.png')
        check('D2: 0 JS-ошибок (мобайл)', js_errors2 == [], js_errors2[:3])
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
