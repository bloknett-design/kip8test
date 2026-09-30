#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 452: browser-check — заявка: «В разделе талоны, дни
# переработки должны учитываться при учёте количества дней явки и
# соответственно количества выданных талонов. Есть замечание по
# учёту талонов, у Чиркова в сентябре 2026 года стоят шесть 12
# часовых смен, а в отчёте они не учлись, в отличии от итогов
# учёта в табеле сдесь необходимо разделятьрабочие дни по
# талонам, 7,2 и 8 это 8 часовые талоны, 12 это 12 часовые
# талоны.»
# КОНТЕКСТ (мок-сервер, порт 8972): десктоп 1280 тёмная, Админ:
#   A: приложение + график; кнопка «Талоны» видна;
#   B: «Талоны»: чипы 12ч=11 (Чирков 8 + Федосов 3) / 8ч=6
#      (Чирков 3 + Петров 3); Чирков (ДНЕВНОЙ!) — ДВЕ категории
#      авто: t12=8 (6×Д + 2×д по 12 ч) и t8=3 (3×Д8), дней=11
#      (переработка в днях явки); Федосов (сменный) t12=3/t8=0;
#      Петров t8=3 (2×Д8 + д 8 ч, дней 3); сортировка по алфавиту;
#      Итого с ПУСТОЙ ячейкой дней; подсказка про переработку;
#   C: предпросмотр печати: Чирков ДВАЖДЫ (авто, без правок),
#      96 ч (8×12) + 24 ч (3×8), ИТОГО 11/6 (шт.), подписи;
#      PDF-эквивалент = 1 страница A4 (pypdf);
#   D: правка t12 Чиркова 8→10: чипы 13/6, бейдж +2, сброс →
#      8, тост «по дням месяца»;
#   E: зритель (view без edit): кнопка скрыта, прямой заход —
#      редирект в табель;
#   F: мобайл 375: страница + правка t8 Петрова 3→4 → чип 8ч=7;
#   G: 0 JS-ошибок ×3 контекста; скриншоты в download/kip8test-task452/.
import datetime
import json
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8972
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
D = lambda day: '%04d-%02d-%02d' % (NOWY, NOWM, day)

SHOTS = '/home/z/my-project/download/kip8test-task452'
os.makedirs(SHOTS, exist_ok=True)

# Работники: Чирков — ДНЕВНОЙ с 12-часовыми днями (замечание
# пользователя); Федосов — сменный; Петров — дневной с
# переработкой 8 ч; Яковлев — без записей (fallback)
EMPLOYEES = [
  {'таб_номер': '0231', 'ФИО': 'Чирков В. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2023-05-11',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': D(1), 'дата_приёма': '2024-03-15',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': '0955', 'ФИО': 'Петров П. П.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2023-11-05',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр 4 разряда', 'группа_допуска': 'III',
   'комментарий': ''},
  {'таб_номер': '0377', 'ФИО': 'Яковлев Я. Я.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2025-01-20',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Инженер КИПиА', 'группа_допуска': '',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE0B2', 'short': 'день 12ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5', 'short': 'ночь 12ч'},
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'д', 'name': 'Переработка день', 'color': '#FFCDD2',
   'short': 'перер. день'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
]

# Смена Чиркова (текущий месяц): 6× Д + 2× д(12 ч) + 3× Д8 —
# 11 дней явки (переработка учтена), t12=8, t8=3
ENTRIES = []
for i in range(1, 7):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0231', 'статус': 'Д',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
for i in (7, 8):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0231', 'статус': 'д',
                    'переработка': 1, 'праздник': 1, 'источник': 'руч',
                    'часы': 12})
for i in (9, 10, 11):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0231', 'статус': 'Д8',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
# Федосов (сменный): 3× Н → t12=3
for i in (1, 2, 3):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0871', 'статус': 'Н',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
# Петров (дневной): 2× Д8 + 1× д(8 ч) → t8=3, дней 3
for i in (2, 3):
    ENTRIES.append({'дата': D(i), 'таб_номер': '0955', 'статус': 'Д8',
                    'переработка': 0, 'праздник': 0, 'источник': 'авто'})
ENTRIES.append({'дата': D(7), 'таб_номер': '0955', 'статус': 'д',
                'переработка': 1, 'праздник': 1, 'источник': 'руч',
                'часы': 8})

PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]

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
          (('  [' + str(extra)[:230] + ']') if (extra and not ok) else ''))


def api_response(action, body, editor=True):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': editor,
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
        return {'ok': True, 'data': {'trainings': [], 'instrList': [],
                'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in ENTRIES]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def attach(page, ctx, theme, tag, editor=True):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t452-%s');" % tag +
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
        resp = api_response(action, body, editor=editor)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t452-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


TALONS_JS = """(function(){
    var body = document.getElementById('wsTalonsBody');
    if (!body) return null;
    var sub = body.querySelector('.wst-sub');
    var chips = {};
    body.querySelectorAll('.wst-chip').forEach(function(ch){
        var t = ch.textContent.replace(/\\s+/g,' ').trim();
        var m = t.match(/^([^:]+):\\s*(.+)$/);
        if (m) chips[m[1]] = m[2];
    });
    var table = body.querySelector('.wst-table');
    var rows = [];
    if (table) {
        table.querySelectorAll('tbody tr').forEach(function(tr){
            var tds = tr.querySelectorAll('td');
            var ins = tr.querySelectorAll('input[data-cat]');
            var byCat = {};
            ins.forEach(function(inp){
                byCat[inp.getAttribute('data-cat')] = {
                    val: inp.value, auto: inp.getAttribute('data-auto')};
            });
            rows.push({fio: tds[2].textContent.trim(),
                       pos: tds[3].textContent.trim(),
                       days: tds[4].textContent.trim(),
                       cats: byCat});
        });
    }
    var foot = table ? table.querySelectorAll('tfoot td') : [];
    var footVals = [];
    foot.forEach(function(td){ footVals.push(td.textContent.trim()); });
    return {sub: sub ? sub.textContent : '', chips: chips, rows: rows,
            foot: footVals};
})"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ (edit) =====
        print('=== Контекст: десктоп тёмная — Талоны по дням + переработка ===')
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
        btn = page.evaluate("(function(){var b = document.getElementById(" +
                            "'wsTalonsBtn'); return b ? " +
                            "{v: !b.hidden && b.offsetParent !== null," +
                            " t: b.textContent.trim()} : null;})()")
        check('A2: кнопка «Талоны» видна (edit)', bool(btn and btn['v']),
              btn)

        # ---------- B: страница «Талоны» ----------
        page.click('#wsTalonsBtn')
        page.wait_for_timeout(1500)
        g = page.evaluate(TALONS_JS)
        check('B1: страница отрендерена', bool(g and g['rows']))
        if g:
            check('B2: чип 12ч = 11 (Чирков 8 + Федосов 3)',
                  g['chips'].get('12 ч. талонов') == '11', g['chips'])
            check('B3: чип 8ч = 6 (Чирков 3 + Петров 3)',
                  g['chips'].get('8 ч. талонов') == '6', g['chips'])
            check('B4: НЕТ чипа общего итога дней',
                  all('Дней' not in k for k in g['chips']), g['chips'])
            names = [r['fio'] for r in g['rows']]
            check('B5: сортировка по алфавиту (П→Ф→Ч→Я): Петров→Федосов→Чирков→Яковлев',
                  names == ['Петров П. П.', 'Федосов А. В.',
                            'Чирков В. А.', 'Яковлев Я. Я.'], names)
            # алфавит: П < Ф < Ч — Чирков ТРЕТИЙ (дневной с 12-ч днями)
            chir = g['rows'][2]
            check('B6: Чирков (ДНЕВНОЙ) — ДВЕ категории авто: t12=8 (6×Д + 2×д 12ч)',
                  chir['cats'].get('t12', {}).get('val') == '8' and
                  chir['cats'].get('t12', {}).get('auto') == '8',
                  chir['cats'])
            check('B7: Чирков t8=3 (3×Д8, авто)',
                  chir['cats'].get('t8', {}).get('val') == '3' and
                  chir['cats'].get('t8', {}).get('auto') == '3', chir['cats'])
            check('B8: Чирков дней явки = 11 — ПЕРЕРАБОТКА (2× д) учтена',
                  chir['days'] == '11', chir['days'])
            fed = g['rows'][1]
            check('B9: Федосов (сменный) t12=3 (3×Н), t8=0',
                  fed['cats'].get('t12', {}).get('val') == '3' and
                  fed['cats'].get('t8', {}).get('val') == '0', fed['cats'])
            petr = g['rows'][0]
            check('B10: Петров t8=3 (2×Д8 + д 8ч), t12=0',
                  petr['cats'].get('t8', {}).get('val') == '3' and
                  petr['cats'].get('t12', {}).get('val') == '0', petr['cats'])
            check('B11: Петров дней = 3 (переработка 8 ч — день явки)',
                  petr['days'] == '3', petr['days'])
            yak = g['rows'][3]
            check('B12: Яковлев без записей — 0/0',
                  yak['cats'].get('t12', {}).get('val') == '0' and
                  yak['cats'].get('t8', {}).get('val') == '0' and
                  yak['days'] == '0', yak)
            check('B13: Итого: дни ПУСТЫ, 12ч=11, 8ч=6',
                  g['foot'] == ['Итого', '', '11', '6'], g['foot'])
            check('B14: подсказка — дни переработки учитываются',
                  'дни переработки (д/н) учитываются' in g['sub'], g['sub'][:120])
            check('B15: подсказка — классификация 7,2/8 и 12',
                  '7,2/8 ч — 8 ч. талон' in g['sub'] and
                  '12 ч — 12 ч. талон' in g['sub'], g['sub'][:160])
        page.screenshot(path=SHOTS + '/01-talons-page.png')

        # ---------- C: предпросмотр печати ----------
        page.click('.wst-print-btn')
        page.wait_for_timeout(1500)
        prev = page.evaluate("""(function(){
            var ov = document.getElementById('wsTalonsPrevModal');
            if (!ov) return null;
            var fr = ov.querySelector('iframe');
            return {srcdoc: fr ? fr.srcdoc : ''};
        })()""")
        check('C1: предпросмотр открыт', bool(prev and prev['srcdoc']))
        if prev:
            sd = prev['srcdoc']
            n_chir = sd.count('Чирков В. А.')
            check('C2: Чирков в отчёте ДВАЖДЫ — авто по дням, БЕЗ правок',
                  n_chir == 2, n_chir)
            i12 = sd.find('>12 часовые<')
            i8 = sd.find('>8 часовые<')
            i1 = sd.find('Чирков В. А.')
            i2 = sd.find('Чирков В. А.', i1 + 1)
            check('C3: первое вхождение — в «12 часовых», второе — в «8»',
                  i12 != -1 and i8 != -1 and i1 > i12 and i1 < i8 and i2 > i8,
                  (i12, i1, i8, i2))
            check('C4: часы Чиркова 96 (8×12) и 24 (3×8)',
                  '>96</td>' in sd and '>24</td>' in sd,
                  ('96' in sd, '24' in sd))
            check('C5: должность Чиркова — «Слесарь по КИП и А» (без разряда)',
                  'Слесарь по КИП и А</td>' in sd and 'разряда' not in sd)
            check('C6: ИТОГО 12 часовые = 11, 8 часовые = 6 (шт.)',
                  re.search(r'ИТОГО: 12 часовые</td><td class="wst-t-val">11</td>', sd)
                  is not None and
                  re.search(r'8 часовые</td><td class="wst-t-val">6</td>', sd)
                  is not None)
            check('C7: подписи формы на месте',
                  all(s in sd for s in ['Игушов Н.В.', 'Котельникова И.А.',
                                        'Фензель В.П.', '(ф.и.о.)']))
            # PDF-эквивалент: srcdoc → chromium pdf → pypdf = 1 страница
            with open(SHOTS + '/_standalone.html', 'w',
                      encoding='utf-8') as f:
                f.write(sd)
            pg = ctx.new_page()
            pg.goto('http://localhost:%d/_standalone.html' % PORT)
            pg.emulate_media(media='print')
            pg.pdf(path=SHOTS + '/talons-a4.pdf', format='A4',
                   margin={'top': '12mm', 'bottom': '12mm',
                           'left': '10mm', 'right': '10mm'})
            pg.close()
            try:
                import pypdf
                n_pages = len(pypdf.PdfReader(SHOTS + '/talons-a4.pdf').pages)
            except Exception as e:
                n_pages = 'pypdf error: %s' % e
            check('C8: PDF-эквивалент = РОВНО 1 страница A4',
                  n_pages == 1, n_pages)
            page.screenshot(path=SHOTS + '/02-preview.png')
            page.click('.wspprev-cancel')
            page.wait_for_timeout(400)

        # ---------- D: правка t12 Чиркова + сброс ----------
        page.evaluate("""(function(){
            var body = document.getElementById('wsTalonsBody');
            var inp = body.querySelector('input[data-tab="0231"][data-cat="t12"]');
            inp.value = '10';
            inp.dispatchEvent(new Event('input', {bubbles: true}));
        })()""")
        page.wait_for_timeout(400)
        g2 = page.evaluate(TALONS_JS)
        check('D1: правка t12=10 — чип 12ч = 13',
              g2['chips'].get('12 ч. талонов') == '13', g2['chips'])
        check('D2: чип 8ч не тронут (6)', g2['chips'].get('8 ч. талонов') == '6')
        badge = page.evaluate("""(function(){
            var body = document.getElementById('wsTalonsBody');
            var inp = body.querySelector('input[data-tab="0231"][data-cat="t12"]');
            var b = inp.parentNode.querySelector('.wst-diff');
            return {t: b.textContent.trim(), hidden: b.hidden};
        })()""")
        check('D3: бейдж разницы +2 (к авто 8)', badge['t'] == '+2' and
              not badge['hidden'], badge)
        page.screenshot(path=SHOTS + '/03-edited.png')
        page.click('#wstResetBtn')
        page.wait_for_timeout(800)
        g3 = page.evaluate(TALONS_JS)
        check('D4: сброс — авто 12ч = 11 снова',
              g3['chips'].get('12 ч. талонов') == '11', g3['chips'])
        check('D5: Чирков t12 = 8 после сброса',
              g3['rows'][2]['cats'].get('t12', {}).get('val') == '8',
              g3['rows'][2]['cats'])
        check('G1: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors[:3])
        ctx.close()

        # ===== E: зритель (view без edit) =====
        print('=== Контекст: зритель — гейты ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js2 = attach(page2, ctx2, 'dark', 'viewer', editor=False)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2000)
        btn2 = page2.evaluate("(function(){var b = document.getElementById(" +
                              "'wsTalonsBtn'); return !b ? null : " +
                              "(b.offsetParent !== null);})()")
        check('E1: зрителю кнопка «Талоны» СКРЫТА', btn2 is False or btn2 is None,
              btn2)
        page2.evaluate("navigateTo('ws-talons')")
        page2.wait_for_timeout(800)
        active = page2.evaluate("(function(){var p = document.getElementById(" +
                                "'page-ws-talons'); return p ? " +
                                "p.classList.contains('active') : false;})()")
        check('E2: прямой URL — редирект, страница не активна', active is False)
        check('G2: 0 JS-ошибок (зритель)', len(js2) == 0, js2[:3])
        ctx2.close()

        # ===== F: мобайл 375 =====
        print('=== Контекст: мобайл 375 — правка t8 Петрова ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 812})
        page3 = ctx3.new_page()
        js3 = attach(page3, ctx3, 'light', 'mobile')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2000)
        page3.evaluate("WorkSchedule.openTalonsPage()")
        page3.wait_for_timeout(1200)
        g4 = page3.evaluate(TALONS_JS)
        check('F1: мобайл — страница отрендерена, чипы 11/6',
              g4 and g4['chips'].get('12 ч. талонов') == '11' and
              g4['chips'].get('8 ч. талонов') == '6', g4['chips'] if g4 else None)
        page3.evaluate("""(function(){
            var body = document.getElementById('wsTalonsBody');
            var inp = body.querySelector('input[data-tab="0955"][data-cat="t8"]');
            inp.value = '4';
            inp.dispatchEvent(new Event('input', {bubbles: true}));
        })()""")
        page3.wait_for_timeout(400)
        g5 = page3.evaluate(TALONS_JS)
        check('F2: правка t8 Петрова 3→4 — чип 8ч = 7',
              g5['chips'].get('8 ч. талонов') == '7', g5['chips'])
        page3.screenshot(path=SHOTS + '/04-mobile.png')
        check('G3: 0 JS-ошибок (мобайл)', len(js3) == 0, js3[:3])
        ctx3.close()

        browser.close()
    print('\n=== Итог: %d/%d (пас/фал) ===' % (PASS, PASS + FAIL))
    return 0 if FAIL == 0 else 1


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    import threading
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        code = main()
    finally:
        server.shutdown()
    raise SystemExit(code)
