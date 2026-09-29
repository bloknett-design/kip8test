#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 444: browser-check — заявка: «В картах работников, в блоке
# СИЗ, шрифт наименования СИЗ сделай не ярким, а текст с датами и
# сроками наоборот сделай нормальным ярким и лучше читаемым, дату
# окончания "до дд.мм.гггг" сделай больше размером и цвет шрифта
# зелёным - если дата окончания не просрочена и оранжевым или ближе
# к красному цвету - если дата окончания просрочена».
# КОНТЕКСТ (мок-сервер, порт 8948):
#   A: десктоп 1280 ТЁМНАЯ — карточка «Работники»:
#      имя СИЗ — приглушённое (secondary, вес 500), мета — ЯРКАЯ
#      (primary #e0e0e0, 13px), «до …» — 1.15em (≈15px)/700 +
#      ЗЕЛЁНЫЙ #81c784 (действует) / ОРАНЖЕВО-КРАСНЫЙ #ff7043
#      (просрочена); «До износа» — без выделения; граница — дата
#      ровно «сегодня» ещё действует (зелёный);
#   B: десктоп СВЕТЛАЯ — имя #777, мета #333, ok #2e7d32,
#      bad #e64a19;
#   C: мобайл 375 — блок СИЗ жив, «до …» в границах экрана;
#   D: 0 JS-ошибок; скриншоты в download/screenshots-task444/.
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8948
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)
TODAY_RU = '%02d.%02d.%04d' % (TODAY.day, TODAY.month, TODAY.year)

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
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

# СИЗ (Task 444): 1) коробка — срок ДЕЙСТВУЕТ (зелёный);
# 2) каска — действует (зелёный); 3) очки — «До износа» (без
# выделения); 4) перчатки — ПРОСРОЧЕНА (оранжево-красный);
# 5) респиратор — граница «до сегодня» (ещё действует → зелёный)
PPE_STATE = [
  {'id': 11, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд',
   'наименование': 'Фильтрующая коробка противогаза',
   'дата_выдачи': '2026-08-17', 'дата_изготовления': '2025-01-15',
   'срок_годности': '2 года', 'дата_окончания': '2027-01-15',
   'примечание': 'банка №2'},
  {'id': 12, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Каска защитная',
   'дата_выдачи': '2026-08-17', 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': '2028-08-17',
   'примечание': ''},
  {'id': 13, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Очки закрытые',
   'дата_выдачи': '', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
  {'id': 14, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Перчатки резиновые',
   'дата_выдачи': '2023-06-01', 'дата_изготовления': '',
   'срок_годности': '1 год', 'дата_окончания': '2024-06-01',
   'примечание': 'просрочено'},
  {'id': 15, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА 5 разряд', 'наименование': 'Респиратор',
   'дата_выдачи': '2025-09-29', 'дата_изготовления': '',
   'срок_годности': '1 год', 'дата_окончания': TODAY_ISO,
   'примечание': 'граница: до сегодня'},
]

PASS = 0
FAIL = 0
SHOTS = '/home/z/my-project/download/screenshots-task444'
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
            'trainings': [], 'instrList': [],
            'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
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
        "localStorage.setItem('kip8test:kip8_session_token','bc-t444-%s');" % tag +
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
        resp = api_response(action, body)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t444-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


# computed-снимок блока СИЗ: имя/мета/«до …» — цвет, размер, вес
CARD_STYLES_JS = """(function(){
    var body = document.getElementById('wsWorkersBody');
    var items = body ? body.querySelectorAll('.ws-ppe-item') : [];
    function info(el) {
        if (!el) return null;
        var cs = getComputedStyle(el);
        return { color: cs.color, fs: cs.fontSize, fw: cs.fontWeight,
                 text: (el.textContent || '').slice(0, 80) };
    }
    var out = [];
    for (var i = 0; i < items.length; i++) {
        var it = items[i];
        var nm = it.querySelector('.ws-ppe-name');
        var mt = it.querySelector('.ws-ppe-meta');
        var ex = it.querySelector('.ws-ppe-exp');
        out.push({ name: info(nm), meta: info(mt), exp: info(ex),
                   nameTxt: nm ? nm.textContent : '' });
    }
    return { n: items.length,
             sec: (body.textContent || '').indexOf(
                 'СИЗ · средства индивидуальной защиты') !== -1,
             rows: out };
})"""


def open_card(page):
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.click('#wsWorkersBtn')
    page.wait_for_timeout(1000)
    page.click('button[title="Федосов А. В."]')
    page.wait_for_timeout(900)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== A: десктоп 1280 ТЁМНАЯ =====
        print('=== Контекст A: десктоп тёмная — стили блока СИЗ ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        check('A1: приложение загрузилось, график открыт',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(1000)
        page.click('button[title="Федосов А. В."]')
        page.wait_for_timeout(900)
        c = page.evaluate(CARD_STYLES_JS)
        check('A2: секция СИЗ в карточке, 5 записей',
              c['sec'] and c['n'] == 5, (c['sec'], c['n']))

        r1, r3, r4, r5 = (c['rows'][0], c['rows'][2], c['rows'][3], c['rows'][4])
        # имя — ПРИГЛУШЁННОЕ (secondary тёмной темы, вес 500)
        check('A3: имя СИЗ — приглушённый secondary '
              'rgba(255,255,255,0.55), вес 500 (прежде primary/600)',
              r1['name']['color'] == 'rgba(255, 255, 255, 0.55)' and
              r1['name']['fw'] == '500',
              (r1['name']['color'], r1['name']['fw']))
        # мета — ЯРКАЯ (primary #e0e0e0, 13px в карточке)
        check('A4: мета (даты/сроки) — ЯРКИЙ primary rgb(224,224,224), 13px '
              '(прежде secondary/10.5-12.5px)',
              r1['meta']['color'] == 'rgb(224, 224, 224)' and
              r1['meta']['fs'] == '13px',
              (r1['meta']['color'], r1['meta']['fs']))
        # «до …» ДЕЙСТВУЕТ — зелёный, крупнее, жирный
        ok_px = round(13 * 1.15, 2)
        check('A5: «до 15.01.2027» (действует) — ЗЕЛЁНЫЙ rgb(129,199,132), '
              'крупнее меты (≈%.2fpx), вес 700' % ok_px,
              r1['exp'] is not None and
              r1['exp']['color'] == 'rgb(129, 199, 132)' and
              abs(float(r1['exp']['fs'].replace('px', '')) - ok_px) < 0.3 and
              r1['exp']['fw'] == '700',
              r1['exp'])
        check('A6: «до 17.08.2028» каски (действует) — тоже зелёный',
              c['rows'][1]['exp'] is not None and
              c['rows'][1]['exp']['color'] == 'rgb(129, 199, 132)',
              c['rows'][1]['exp'])
        # «до …» ПРОСРОЧЕНА — оранжево-красный
        check('A7: «до 01.06.2024» перчаток (ПРОСРОЧЕНА) — '
              'ОРАНЖЕВО-КРАСНЫЙ rgb(255,112,67)',
              r4['exp'] is not None and
              r4['exp']['color'] == 'rgb(255, 112, 67)' and
              r4['exp']['fw'] == '700',
              r4['exp'])
        # граница: «до сегодня» — ещё действует (зелёный)
        check('A8: граница — «до %s» (ровно сегодня) — ЕЩЁ ДЕЙСТВУЕТ, '
              'зелёный' % TODAY_RU,
              r5['exp'] is not None and
              r5['exp']['color'] == 'rgb(129, 199, 132)',
              r5['exp'])
        # «До износа» — БЕЗ выделения
        check('A9: очки «До износа» — БЕЗ span-выделения (обычная мета)',
              r3['exp'] is None and 'До износа' in r3['meta']['text'],
              r3['meta'])
        # тексты мет на месте (регресс 392/443)
        check('A10: мета коробки: выдано → изгот. → срок → до → примечание',
              all(x in r1['meta']['text'] for x in
                  ['выдано 17.08.2026', 'изгот. 15.01.2025',
                   'срок 2 года', 'до 15.01.2027', 'банка №2']),
              r1['meta']['text'])
        check('A11: инверсия — имя ТУСКЛЕЕ меты (secondary < primary), '
              '«до» — самый яркий элемент строки',
              r1['name']['color'] != r1['meta']['color'] and
              r1['exp']['fw'] == '700' and r1['name']['fw'] == '500')
        page.screenshot(path=SHOTS + '/01-dark-card-ppe.png')
        check('A12: 0 JS-ошибок (десктоп тёмная)', js_errors == [],
              js_errors[:3])
        ctx.close()

        # ===== B: десктоп СВЕТЛАЯ =====
        print('=== Контекст B: десктоп светлая — палитра light ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'light')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        open_card(page2)
        l = page2.evaluate(CARD_STYLES_JS)
        l1, l4 = l['rows'][0], l['rows'][3]
        check('B1: светлая — имя приглушённое rgb(119,119,119) (#777)',
              l1['name']['color'] == 'rgb(119, 119, 119)',
              l1['name']['color'])
        check('B2: светлая — мета яркая rgb(51,51,51) (#333)',
              l1['meta']['color'] == 'rgb(51, 51, 51)',
              l1['meta']['color'])
        check('B3: светлая — действует rgb(46,125,50) (#2e7d32)',
              l1['exp'] is not None and
              l1['exp']['color'] == 'rgb(46, 125, 50)',
              l1['exp'])
        check('B4: светлая — просрочена rgb(230,74,25) (#e64a19)',
              l4['exp'] is not None and
              l4['exp']['color'] == 'rgb(230, 74, 25)',
              l4['exp'])
        page2.screenshot(path=SHOTS + '/02-light-card-ppe.png')
        check('B5: 0 JS-ошибок (светлая)', js_errors2 == [], js_errors2[:3])
        ctx2.close()

        # ===== C: мобайл 375 =====
        print('=== Контекст C: мобайл 375 — блок СИЗ ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 812})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'dark', 'mobile')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        open_card(page3)
        m = page3.evaluate("""(function(){
            var body = document.getElementById('wsWorkersBody');
            var txt = body ? (body.textContent || '') : '';
            var items = body ? body.querySelectorAll('.ws-ppe-item') : [];
            var exps = body ? body.querySelectorAll('.ws-ppe-exp') : [];
            var clipped = [];
            for (var i = 0; i < exps.length; i++) {
                var r = exps[i].getBoundingClientRect();
                if (r.right > 376 || r.left < -1)
                    clipped.push(Math.round(r.right));
            }
            var sec = body ? (body.querySelector('.ws-whead-t') &&
                body.textContent.indexOf('СИЗ') !== -1) : false;
            return { sec: !!sec, n: items.length, expN: exps.length,
                     clipped: clipped,
                     ok: txt.indexOf('до 15.01.2027') !== -1,
                     bad: txt.indexOf('до 01.06.2024') !== -1 };
        })()""")
        check('C1: мобайл — секция СИЗ жива, 5 записей',
              m['sec'] and m['n'] == 5, m)
        check('C2: мобайл — 4 выделенные даты (3 действует + 1 просрочена)',
              m['expN'] == 4, m['expN'])
        check('C3: мобайл — «до …» НЕ обрезана (в границах 375px)',
              m['clipped'] == [], m['clipped'])
        check('C4: мобайл — зелёная и оранжево-красная даты видны текстом',
              m['ok'] and m['bad'], m)
        page3.screenshot(path=SHOTS + '/03-mobile-card-ppe.png')
        check('C5: 0 JS-ошибок (мобайл)', js_errors3 == [], js_errors3[:3])
        ctx3.close()
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
