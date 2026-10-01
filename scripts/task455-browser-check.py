#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 455: browser-check — заявка: «В разделе талоны, данные
# формирования отчёта должны быть в зависимости от того, на какой
# месяц открыта шахматка табеля».
# КОНТЕКСТ (мок-сервер, порт 8978): десктоп 1280 светлая, Админ
# (edit); 3 работника, записи ДВУХ месяцев (текущий и прошлый):
#   A: приложение + график ТЕКУЩЕГО месяца; wsMonthSel = текущий;
#   B: «Талоны» на текущей сетке — шапка «— <текущий месяц> <год>
#      г.», значения/чипы по записям ТЕКУЩЕГО месяца; listEntries
#      сверх начальной загрузки НЕ вызывался (кэш/подтяжка
#      удалены — записи живые);
#   C (ЗАЯВКА): назад в табель → селект месяца → ПРОШЛЫЙ месяц →
#      «Талоны»: шапка «— <прошлый месяц> <год> г.», подзаголовок
#      «за месяц, открытый в шахматке табеля», значения/чипы по
#      записям ПРОШЛОГО месяца (Чирков t8=3, Федосов t12=2,
#      Петров t8=1; 12ч=2/8ч=4), «Дней явки» 3/2/1;
#   D: предпросмотр печати — шапка «— <прошлый> <год> г.» и
#      форма «за <прошлый> <год> г.» (iframe srcdoc), закрытие;
#   E: «Обновить данные» — listEntries(year=прошлый, month=прошлый)
#      + тост «Данные графика обновлены», отчёт прежний;
#   F: правка талонов поверх месяца сетки (3→5: чип 8ч=6, Правок:
#      1, «Сбросить правки» видна) и сброс (чип 8ч=4);
#   G: зритель (view) — кнопка «Талоны» скрыта, прямой URL
#      ws-talons → редирект в табель;
#   H: мобайл 375 — сетка на прошлом месяце (evaluate), шапка
#      «Талонов» — прошлый месяц, значения те же;
#   I: 0 JS-ошибок ×2 контекста; скриншоты download/kip8test-task455/.
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8978
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
# прошлый месяц (с переходом года)
PM = NOWM - 1 if NOWM > 1 else 12
PMY = NOWY if NOWM > 1 else NOWY - 1
MD = lambda y, m, d: '%04d-%02d-%02d' % (y, m, d)
MONTHS = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
          'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
CUR_NAME = '%s %d г.' % (MONTHS[NOWM - 1], NOWY)
PM_NAME = '%s %d г.' % (MONTHS[PM - 1], PMY)

TAB_CH = '0231'   # Чирков, дневной
TAB_FD = '0871'   # Федосов, сменный
TAB_PT = '0512'   # Петров, дневной

SHOTS = '/home/z/my-project/download/kip8test-task455'
os.makedirs(SHOTS, exist_ok=True)

EMPLOYEES = [
  {'таб_номер': TAB_CH, 'ФИО': 'Чирков В. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2023-05-11',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
  {'таб_номер': TAB_FD, 'ФИО': 'Федосов А. С.', 'тип': 'сменный', 'смена': 3,
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2022-02-01',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Электромонтёр 4 разряда', 'группа_допуска': 'III',
   'комментарий': ''},
  {'таб_номер': TAB_PT, 'ФИО': 'Петров Б. Н.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2024-06-03',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Мастер КИПиА 6 разряда', 'группа_допуска': 'V',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE0B2', 'short': 'день 12ч'},
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#C5E1F5', 'short': 'ночь'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
]


def E(date, tab, st):
    return {'дата': date, 'таб_номер': tab, 'статус': st,
            'переработка': 0, 'праздник': 0, 'источник': 'авто'}


# записи ДВУХ месяцев: отчёт следует за сеткой, а не за календарём
ENTRIES = {
    (NOWY, NOWM): [
        E(MD(NOWY, NOWM, 1), TAB_CH, 'Д8'),
        E(MD(NOWY, NOWM, 2), TAB_CH, 'Д8'),          # Чирков: t8=2
        E(MD(NOWY, NOWM, 1), TAB_FD, 'Д'),           # Федосов: t12=1
    ],
    (PMY, PM): [
        E(MD(PMY, PM, 1), TAB_CH, 'Д8'),
        E(MD(PMY, PM, 2), TAB_CH, 'Д8'),
        E(MD(PMY, PM, 3), TAB_CH, 'Д8'),             # Чирков: t8=3
        E(MD(PMY, PM, 4), TAB_FD, 'Д'),
        E(MD(PMY, PM, 5), TAB_FD, 'Н'),              # Федосов: t12=2
        E(MD(PMY, PM, 6), TAB_PT, 'Д8'),             # Петров: t8=1
    ],
}

MOCK = {'list_entries_calls': []}

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
          (('  [' + str(extra)[:250] + ']') if (extra and not ok) else ''))


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
        return {'ok': True, 'data': {'patterns': []}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': [], 'instrList': [],
                'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        y = int(body.get('year') or NOWY)
        m = int(body.get('month') or NOWM)
        MOCK['list_entries_calls'].append({'year': y, 'month': m})
        return {'ok': True, 'data': {'entries':
                [dict(e) for e in ENTRIES.get((y, m), [])]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length).decode('utf-8', 'replace') \
            if length else ''
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {}
        action = ''
        if 'action=' in self.path:
            action = unquote(self.path.split('action=')[1].split('&')[0])
        resp = api_response(action, body)
        out = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type',
                         'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def attach(page, ctx, theme, tag, editor=True):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t455-%s');" % tag +
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
                      body='not found (t455-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


def hook_toasts(page):
    page.evaluate(
        "window.__toasts=[];"
        "KipToast.show=(function(o){return function(m){"
        "window.__toasts.push(String(m)); try{o(m);}catch(e){}};"
        "})(KipToast.show);")


def toasts(page):
    return page.evaluate("window.__toasts || []")


def report_state(page):
    return page.evaluate(
        "(function(){var t=document.querySelector('.wst-title');"
        "var s=document.querySelector('.wst-sub');"
        "function val(tab,cat){var i=document.querySelector("
        "'input.wst-count[data-tab=\"'+tab+'\"][data-cat=\"'+cat+'\"]');"
        "return i?i.value:null;}"
        "function chip(id){var e=document.getElementById(id);"
        "return e?e.textContent:null;}"
        "var days={};document.querySelectorAll('.wst-table tbody tr').forEach("
        "function(tr){var f=tr.querySelector('.wst-fio');"
        "var d=tr.querySelector('.wst-c-days');"
        "if(f&&d)days[f.textContent.trim()]=d.textContent.trim();});"
        "return {title:t?t.textContent:'',sub:s?s.textContent.slice(0,140):'',"
        "ch8:val('" + TAB_CH + "','t8'),ch12:val('" + TAB_CH + "','t12'),"
        "fd8:val('" + TAB_FD + "','t8'),fd12:val('" + TAB_FD + "','t12'),"
        "pt8:val('" + TAB_PT + "','t8'),pt12:val('" + TAB_PT + "','t12'),"
        "t12:chip('wstTotalT12Chip'),t8:chip('wstTotalT8Chip'),"
        "edits:chip('wstEditCount'),days:days};})()")


def entry_calls():
    return list(MOCK['list_entries_calls'])


def main():
    srv = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 светлая, Админ (edit) =====
        print('=== Контекст: десктоп светлая — месяц отчёта = месяцу шахматки ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'light', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        hook_toasts(page)

        check('A1: приложение загрузилось, график открыт',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))
        msel = page.evaluate("(function(){var s=document.getElementById(" +
                             "'wsMonthSel');return s?parseInt(s.value,10):"
                             "null;})()")
        check('A2: сетка на ТЕКУЩЕМ месяце (%d)' % NOWM, msel == NOWM, msel)

        # ---------- B: Талоны на текущей сетке ----------
        print('--- B: «Талоны» — сетка на текущем месяце ---')
        before = len(entry_calls())
        page.click('#wsTalonsBtn')
        page.wait_for_timeout(900)
        rs = report_state(page)
        check('B1: шапка — ТЕКУЩИЙ месяц «%s»' % CUR_NAME,
              rs['title'].endswith(CUR_NAME), rs['title'])
        check('B2: подзаголовок — «за месяц, открытый в шахматке табеля»',
              'за месяц, открытый в шахматке табеля' in rs['sub'], rs['sub'])
        check('B3: Чирков t8=2 (записи текущего месяца)',
              rs['ch8'] == '2' and rs['ch12'] == '0', rs)
        check('B4: Федосов t12=1 (текущий месяц)', rs['fd12'] == '1', rs)
        check('B5: Петров 0 явок — строка есть, t8=0', rs['pt8'] == '0', rs)
        check('B6: чипы 12ч=1 / 8ч=2 (текущий месяц)',
              rs['t12'] == '1' and rs['t8'] == '2', rs)
        check('B7: listEntries НЕ вызывался при открытии (записи живые)',
              len(entry_calls()) == before,
              [before, len(entry_calls())])
        page.screenshot(path=SHOTS + '/01-talons-current-month.png',
                        full_page=True)

        # ---------- C: ЗАЯВКА — сетка на прошлом месяце ----------
        print('--- C: заявка — смена месяца шахматки → отчёт следует ---')
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1200)
        if NOWM == 1:
            page.select_option('#wsYearSel', str(PMY))
            page.wait_for_timeout(1500)
        page.select_option('#wsMonthSel', str(PM))
        page.wait_for_timeout(2000)
        msel = page.evaluate("(function(){var s=document.getElementById(" +
                             "'wsMonthSel');return s?parseInt(s.value,10):"
                             "null;})()")
        check('C1: сетка перешла на прошлый месяц (%d)' % PM, msel == PM, msel)
        last = entry_calls()[-1] if entry_calls() else None
        check('C2: сетка запросила записи прошлого месяца',
              last and last['month'] == PM, last)
        page.click('#wsTalonsBtn')
        page.wait_for_timeout(900)
        rs = report_state(page)
        check('C3: шапка — ПРОШЛЫЙ месяц «%s»' % PM_NAME,
              rs['title'].endswith(PM_NAME), rs['title'])
        check('C4: Чирков t8=3 (записи прошлого месяца)',
              rs['ch8'] == '3' and rs['ch12'] == '0', rs)
        check('C5: Федосов t12=2 (Д+Н прошлого месяца)',
              rs['fd12'] == '2' and rs['fd8'] == '0', rs)
        check('C6: Петров t8=1', rs['pt8'] == '1', rs)
        check('C7: чипы 12ч=2 / 8ч=4 (прошлый месяц)',
              rs['t12'] == '2' and rs['t8'] == '4', rs)
        check('C8: «Дней явки» по прошлому месяцу (Чирков 3 / Федосов 2)',
              rs['days'].get('Чирков В. А.') == '3' and
              rs['days'].get('Федосов А. С.') == '2', rs['days'])
        page.screenshot(path=SHOTS + '/02-talons-prev-month.png',
                        full_page=True)

        # ---------- D: предпросмотр печати ----------
        print('--- D: предпросмотр печати — месяц сетки в форме ---')
        page.click('.wst-print-btn')
        page.wait_for_timeout(1500)
        prev = page.evaluate(
            "(function(){var m=document.getElementById("
            "'wsTalonsPrevModal');if(!m) return null;"
            "var h=m.querySelector('.wspprev-sub');"
            "var f=m.querySelector('iframe.wspprev-frame');"
            "return {head:h?h.textContent:'',srcdoc:f?f.srcdoc:''};})()")
        check('D1: диалог открыт', bool(prev))
        check('D2: шапка диалога — прошлый месяц «%s»' % PM_NAME,
              bool(prev) and prev['head'].endswith(PM_NAME),
              prev and prev['head'])
        check('D3: форма (srcdoc) — «за %s»' % PM_NAME,
              bool(prev) and ('за ' + PM_NAME) in prev['srcdoc'],
              prev and prev['srcdoc'][:200])
        check('D4: текущий месяц в форме НЕ упомянут',
              bool(prev) and ('за ' + CUR_NAME) not in prev['srcdoc'])
        page.screenshot(path=SHOTS + '/03-print-preview-prev-month.png')
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        check('D5: закрытие снимает предпросмотр',
              not page.evaluate(
                  "(function(){var m=document.getElementById("
                  "'wsTalonsPrevModal');return !!m;})()"))

        # ---------- E: «Обновить данные» ----------
        print('--- E: «Обновить данные» — refreshData сетки ---')
        before = len(entry_calls())
        page.click('.wst-actions button.wst-btn:not(.wst-print-btn):not('
                   '#wstResetBtn)')
        page.wait_for_timeout(2000)
        calls = entry_calls()[before:]
        check('E1: listEntries перечитал МЕСЯЦ СЕТКИ (%d)' % PM,
              any(c['month'] == PM for c in calls), calls)
        t = toasts(page)
        check('E2: тост «Данные графика обновлены»',
              any('Данные графика обновлены' in x for x in t), t)
        rs = report_state(page)
        check('E3: отчёт прежний — прошлый месяц, значения на месте',
              rs['title'].endswith(PM_NAME) and rs['ch8'] == '3', rs['title'])

        # ---------- F: правка талонов поверх месяца сетки ----------
        print('--- F: правка/сброс талонов ---')
        inp = page.locator('input.wst-count[data-tab="%s"][data-cat="t8"]'
                           % TAB_CH)
        inp.fill('5')
        page.wait_for_timeout(500)
        rs = report_state(page)
        check('F1: правка 3→5 — чип 8ч=6, Правок: 1',
              rs['t8'] == '6' and rs['edits'] == '1', rs)
        rst = page.evaluate(
            "(function(){var b=document.getElementById('wstResetBtn');"
            "return b&&!b.hidden;})()")
        check('F2: «Сбросить правки» видна', rst)
        page.screenshot(path=SHOTS + '/04-edit-over-prev-month.png')
        page.click('#wstResetBtn')
        page.wait_for_timeout(700)
        rs = report_state(page)
        t = toasts(page)
        check('F3: сброс — чип 8ч=4, тост «Правки сброшены»',
              rs['t8'] == '4' and
              any('Правки сброшены' in x for x in t), rs)

        check('I1: 0 JS-ошибок (десктоп)', not js_errors, js_errors[:3])
        ctx.close()

        # ===== G: зритель (view) =====
        print('=== Контекст: зритель (view) — гейты ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'viewer', editor=False)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2000)
        btn = page2.evaluate(
            "(function(){var b=document.getElementById('wsTalonsBtn');"
            "return b?b.hidden:null;})()")
        check('G1: кнопка «Талоны» скрыта у зрителя', btn is True, btn)
        page2.evaluate("navigateTo('ws-talons')")
        page2.wait_for_timeout(900)
        cur = page2.evaluate(
            "(function(){var el=document.querySelector("
            "'.page-content.active');return el?el.id:'';})()")
        check('G2: прямой URL ws-talons → редирект в табель',
              cur == 'page-work-schedule', cur)
        check('I2: 0 JS-ошибок (зритель)', not js_errors2, js_errors2[:3])
        page2.screenshot(path=SHOTS + '/05-viewer-redirect.png')
        ctx2.close()

        # ===== H: мобайл 375 =====
        print('=== Контекст: мобайл 375 — месяц сетки ===')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 812})
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'light', 'mobile')
        page3.goto('http://localhost:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2000)
        # смена месяца сетки напрямую (селект в мобайл-раскладке скрыт)
        page3.evaluate("WorkSchedule._month=%d;WorkSchedule._year=%d;"
                       "WorkSchedule.loadGrid()" % (PM, PMY))
        page3.wait_for_timeout(2000)
        page3.click('#wsTalonsBtn')
        page3.wait_for_timeout(900)
        rs3 = report_state(page3)
        check('H1: шапка — прошлый месяц «%s»' % PM_NAME,
              rs3['title'].endswith(PM_NAME), rs3['title'])
        check('H2: значения прошлого месяца (Чирков t8=3 / Федосов t12=2)',
              rs3['ch8'] == '3' and rs3['fd12'] == '2', rs3)
        check('H3: 0 JS-ошибок (мобайл)', not js_errors3, js_errors3[:3])
        page3.screenshot(path=SHOTS + '/06-mobile-prev-month.png',
                         full_page=True)
        ctx3.close()

        browser.close()

    print('=' * 60)
    print('ИТОГ Task 455 browser-check: %d OK, %d FAIL' % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == '__main__':
    raise SystemExit(main())
