#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 536 browser-check: серверная погода УДАЛЕНА. Заявка: «Через
# сервер погода не загружается, работает только через wttr.in
# (напрямую из браузера), поэтому убери из кода WorkSchedule.gs не
# рабочие строки кода связанные с погодой.»
#  A) ПОГОДА ЧЕРЕЗ WTTR: open-meteo падает (503) → wttr.in отвечает
#     («-2°», Пасмурно) — экран показывает погоду, diag: канал wttr,
#     источник «wttr.in (напрямую из браузера)»; сервер Apps Script
#     (action=workSchedule.getWeather) НЕ звался ВООБЩЕ.
#  B) ОБА ПРЯМЫХ КАНАЛА ПАЛИ: экран «--», панель настроек — статус
#     «Прямые запросы open-meteo/wttr.in не прошли (прямой запрос:
#     open-meteo: http_503; wttr.in: http_502). Повтор — по
#     расписанию или кнопкой ниже»; НЕТ подсказок authorizeWeather/
#     appsscript.json/oauthScopes; сервер НЕ звался и здесь.
#  C) КЛИЕНТ: в исходнике страницы нет вызова
#     KipAuth.api('workSchedule.getWeather') (по toString метода
#     _loadWeather и по всему index.html); календарь жив (быстрая
#     регрессия Task 535: высоты контролов ровные).
#  D) 1024 светлая тема — попапы в пределах вьюпорта; 0 JS-ошибок.
import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task536')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

OM_CALLS = []
WT_CALLS = []
SERVER_W_CALLS = []


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


# --- Данные мока (как в task534/535) ---
CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': '2026-10-01',
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
_T = _dt.date.today()
_ISO = lambda d: d.strftime('%Y-%m-%d')
TRAININGS = [
  {'id': 101, 'таб_номер': '017', 'тип': 'инструктаж',
   'тема': 'Охрана труда', 'дата_начала': _ISO(_T),
   'дата_окончания': _ISO(_T), 'длительность_дней': 1, 'комментарий': ''},
]
VACATIONS = [
  {'id': 1, 'таб_номер': '017', 'дата_начала': _ISO(_T - _dt.timedelta(days=3)),
   'дата_окончания': _ISO(_T + _dt.timedelta(days=11)),
   'часть': 1, 'комментарий': ''},
]

# ответ wttr.in (format=j1&lang=ru — РЕАЛЬНЫЙ формат, Кемерово):
# −2°C, пасмурно, облака 100%
WTTR_JSON = json.dumps({
    'current_condition': [{
        'temp_C': '-2', 'FeelsLikeC': '-6', 'cloudcover': '100',
        'humidity': '83', 'observation_time': '01:51 AM',
        'pressure': '1035', 'weatherDesc': [{'value': 'Overcast '}],
        'lang_ru': [{'value': 'Пасмурно'}],
        'winddirDegree': '253', 'windspeedKmph': '11'
    }]
}, ensure_ascii=False)


def mock_response(action):
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
                'instrList': [], 'instrAll': TRAININGS, 'eventsAll': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': VACATIONS}}
    # getWeather УДАЛЕН (Task 536): если бы клиент позвал — счётчик
    # SERVER_W_CALLS зафиксирует вызов, а ответ будет ошибкой
    if action == 'workSchedule.getWeather':
        return {'ok': False, 'error': 'unknown_action'}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# --- JS-побы ---

# погода: экранный буфер + diag
WX_JS = r"""(() => {
    const WsL = window.WsLcdClock;
    if (!WsL) return {missing: true};
    const g = WsL._grid;
    const lit = (r, a, b) => { let n = 0;
        for (let c = a; c <= b; c++) n += (g[r][c] ? 1 : 0); return n; };
    let wxFirst = -1, wxLast = -1;
    if (g) for (let c = 170; c <= 204; c++)
        for (let r = 5; r <= 12; r++)
            if (g[r][c]) { if (wxFirst < 0) wxFirst = c; wxLast = c; break; }
    return {
        tempTxt: WsL._weather ? WsL._weather.tempTxt : null,
        icon: WsL._weather ? WsL._weather.icon : null,
        diagOk: WsL._weatherDiag ? WsL._weatherDiag.ok : null,
        via: WsL._weatherDiag ? WsL._weatherDiag.via : null,
        source: WsL._weatherDiag ? WsL._weatherDiag.source : null,
        obs: WsL._weatherDiag ? WsL._weatherDiag.obs : null,
        why: WsL._weatherDiag ? (WsL._weatherDiag.why || null) : null,
        direct: WsL._weatherDiag ? (WsL._weatherDiag.direct || null) : null,
        wttr: WsL._weatherDiag ? (WsL._weatherDiag.wttr || null) : null,
        wxFirst: wxFirst, wxLast: wxLast,
        loadSrc: WsL._loadWeather.toString()
    };})"""

# панель настроек: строка статуса погоды
WSTAT_JS = r"""(() => {
    const el = document.getElementById('wsLcdSet');
    if (!el || el.hidden) return {missing: true};
    const st = el.querySelector('.ws-lcd-set-wstat');
    return {hidden: el.hidden, wstat: st ? st.textContent.trim() : null,
            cls: st ? st.className : null,
            html: el.innerHTML};})"""

# календарь: высоты контролов (регрессия Task 535)
CAL_JS = r"""(() => {
    const cal = document.getElementById('wsLcdCal');
    if (!cal || cal.hidden) return {missing: true};
    const yearRow = cal.querySelector('.ws-lcd-cal-year');
    const monthRow = cal.querySelector('.ws-lcd-cal-month');
    const ysel = yearRow ? yearRow.querySelector('select') : null;
    const msel = monthRow ? monthRow.querySelector('select') : null;
    const ynavs = yearRow ? yearRow.querySelectorAll('.ws-lcd-cal-nav') : [];
    const mnavs = monthRow ? monthRow.querySelectorAll('.ws-lcd-cal-nav') : [];
    const todayBtn = monthRow ? monthRow.querySelector('.ws-lcd-cal-today') : null;
    const h = el => el ? Math.round(el.getBoundingClientRect().height * 10) / 10 : null;
    return {yselH: h(ysel), mselH: h(msel),
            ynavH: h(ynavs[0]), mnavH: h(mnavs[0]), todayH: h(todayBtn)};})"""


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        def make_ctx(theme, w, h, dpr=1.0, om='ok', wttr='ok'):
            ctx = browser.new_context(viewport={'width': w, 'height': h},
                                      device_scale_factor=dpr)
            ctx.add_init_script(
                "try{localStorage.clear()}catch(e){};" +
                "localStorage.setItem('kip8test:kip8_session_token','bc-t536');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")

            def om_handle(route):
                OM_CALLS.append(1)
                if om == 'ok':
                    route.fulfill(status=200,
                                  content_type='application/json; charset=utf-8',
                                  body=json.dumps({
                                      'latitude': 55.36, 'longitude': 86.02,
                                      'current': {
                                          'time': '2026-10-16T07:00',
                                          'temperature_2m': -1.6,
                                          'weather_code': 3,
                                          'wind_speed_10m': 2.55,
                                          'wind_direction_10m': 271,
                                          'surface_pressure': 1018.1,
                                          'relative_humidity_2m': 73}}))
                else:
                    route.fulfill(status=int(om), content_type='text/plain',
                                  body='om down')

            def wt_handle(route):
                WT_CALLS.append(1)
                if wttr == 'ok':
                    route.fulfill(status=200,
                                  content_type='text/plain; charset=utf-8',
                                  body=WTTR_JSON)
                else:
                    route.fulfill(status=int(wttr), content_type='text/plain',
                                  body='wttr down')

            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
                if action == 'workSchedule.getWeather':
                    SERVER_W_CALLS.append(1)
                route.fulfill(status=200,
                              content_type='application/json; charset=utf-8',
                              body=json.dumps(mock_response(action),
                                              ensure_ascii=False))
            ctx.route('**api.open-meteo.com/**', om_handle)
            ctx.route('**wttr.in/**', wt_handle)
            ctx.route('**/exec?**', handle)
            ctx.route('**script.google.com/**', handle)
            ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
                status=404, content_type='text/plain', body='nf'))
            return ctx

        # ==============================================================
        print('== A: ПОГОДА ЧЕРЕЗ WTTR.IN — сервер Apps Script не звался ==')
        ctx = make_ctx('dark', 1280, 720, dpr=2.0, om='503', wttr='ok')
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(1200)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)

        wx = page.evaluate(WX_JS)
        check('A: open-meteo падал (503), wttr.in ответил',
              len(OM_CALLS) >= 1 and len(WT_CALLS) >= 1,
              (len(OM_CALLS), len(WT_CALLS)))
        check('A: погода пришла через wttr («-2°», иконка cloud)',
              wx.get('tempTxt') == '-2°' and wx.get('icon') == 'cloud', wx)
        check('A: канал — wttr, источник «wttr.in (напрямую из браузера)»',
              wx.get('diagOk') is True and wx.get('via') == 'wttr' and
              wx.get('source') == 'wttr.in (напрямую из браузера)', wx)
        check('A: наблюдение 08:51 (UTC 01:51 → Кемерово +7)',
              wx.get('obs') == '08:51', wx)
        check('A: блок погоды на экране (177..203 — геометрия Task 535 жива)',
              wx.get('wxFirst') == 177 and wx.get('wxLast') == 203, wx)
        check('A: сервер Apps Script НЕ звался (getWeather удалён)',
              len(SERVER_W_CALLS) == 0, SERVER_W_CALLS)
        check('A: в исходнике _loadWeather НЕТ вызова workSchedule.getWeather',
              'workSchedule.getWeather' not in (wx.get('loadSrc') or ''), None)

        # панель настроек: статус успеха
        page.click('#wsLcdGear')
        page.wait_for_timeout(300)
        ws = page.evaluate(WSTAT_JS)
        check('A: панель — «Есть данные: -2° — wttr.in (напрямую...)»',
              ws.get('wstat') == 'Есть данные: -2° — wttr.in ' +
                     '(напрямую из браузера) (набл. 08:51)', ws)
        shot(page, '01-settings-wttr-ok.png')
        page.keyboard.press('Escape')

        # фото строки LCD (погода через wttr)
        try:
            lcd = page.locator('#wsLcdClock')
            lcd.screenshot(path=os.path.join(SHOT_DIR, '00-lcd-wttr.png'))
            check('A: скриншот строки LCD (wttr) сохранён', True)
        except Exception as e:
            check('A: скриншот строки LCD (wttr) сохранён', False, str(e))

        # календарь жив (регрессия Task 535: высоты ровные)
        page.click('#wsLcdClock')
        page.wait_for_timeout(300)
        cy = page.evaluate(CAL_JS)
        hs = [cy.get('yselH'), cy.get('mselH'), cy.get('ynavH'),
              cy.get('mnavH'), cy.get('todayH')]
        check('A: календарь жив — высоты ровные (разброс ≤ 1px): %s' % hs,
              all(h is not None for h in hs) and max(hs) - min(hs) <= 1.0, cy)
        shot(page, '02-calendar-dark.png')
        page.keyboard.press('Escape')
        check('A: 0 JS-ошибок (тёмная)', len(js_errors) == 0, js_errors)

        # ==============================================================
        print('== B: ОБА КАНАЛА ПАЛИ — статус без сервера, «--» ==')
        ctx2 = make_ctx('dark', 1280, 720, dpr=1.0, om='503', wttr='502')
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(1200)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)

        wx2 = page.evaluate(WX_JS) if False else page2.evaluate(WX_JS)
        check('B: экран — тихий прочерк «--»',
              wx2.get('tempTxt') is None or wx2.get('tempTxt') == '--', wx2)
        check('B: diag — не ok, why=network, оба канала видны',
              wx2.get('diagOk') is False and wx2.get('why') == 'network' and
              wx2.get('direct') == 'http_503' and wx2.get('wttr') == 'http_502',
              wx2)

        page2.click('#wsLcdGear')
        page2.wait_for_timeout(300)
        ws2 = page2.evaluate(WSTAT_JS)
        wstat = ws2.get('wstat') or ''
        check('B: статус — «Прямые запросы open-meteo/wttr.in не прошли…»',
              wstat.startswith('Прямые запросы open-meteo/wttr.in не прошли'),
              ws2)
        check('B: dnote с причинами обоих каналов (503/502)',
              '(прямой запрос: open-meteo: http_503; wttr.in: http_502)' in wstat,
              ws2)
        check('B: обещание повтора', 'Повтор — по расписанию или кнопкой ниже' in wstat,
              ws2)
        html = ws2.get('html') or ''
        check('B: НЕТ подсказок authorizeWeather/appsscript.json/oauthScopes',
              'authorizeWeather' not in html and 'appsscript.json' not in html and
              'oauthScopes' not in html, None)
        check('B: варнинг-стиль статуса', 'warn' in (ws2.get('cls') or ''), ws2)
        shot(page2, '03-settings-both-fail.png')
        page2.keyboard.press('Escape')
        check('B: сервер Apps Script НЕ звался и здесь',
              len(SERVER_W_CALLS) == 0, SERVER_W_CALLS)
        check('B: 0 JS-ошибок', len(js_errors2) == 0, js_errors2)

        # ==============================================================
        print('== C: 1024 светлая — попапы в порядке, 0 ошибок ==')
        ctx3 = make_ctx('light', 1024, 700, dpr=1.0, om='503', wttr='ok')
        page3 = ctx3.new_page()
        js_errors3 = []
        page3.on('pageerror', lambda e: js_errors3.append(str(e)))
        page3.on('dialog', lambda dg: dg.accept())
        page3.goto('http://127.0.0.1:%d/index.html' % PORT)
        page3.wait_for_timeout(1200)
        page3.evaluate("navigateTo('work-schedule')")
        page3.wait_for_timeout(2500)
        # страховка от редкого плавающего «элемент не виден» (тема/
        # раскладка применяются асинхронно): до 3 попыток клика
        clicked = False
        for _ in range(3):
            try:
                page3.click('#wsLcdClock', timeout=8000)
                clicked = True
                break
            except Exception:
                probe = page3.evaluate("""(() => {
                    const el = document.getElementById('wsLcdClock');
                    if (!el) return {missing: true};
                    const r = el.getBoundingClientRect();
                    return {w: Math.round(r.width), h: Math.round(r.height),
                            off: el.offsetParent === null,
                            hidden: !!el.closest('[hidden]'),
                            page: (document.querySelector(
                                '.nav-item.active, .nav-btn.active') || {})
                                .textContent || ''};
                })()""")
                print('    (клик не удался, состояние: %s)' % probe)
                page3.wait_for_timeout(800)
        check('C: календарь открыт (клик по окну)', clicked)
        page3.wait_for_timeout(300)
        pop = page3.evaluate("""(() => {
            const cal = document.getElementById('wsLcdCal');
            const c = cal.getBoundingClientRect();
            return {inside: c.left >= 0 && c.right <= innerWidth};})""")
        check('C: календарь в пределах вьюпорта 1024',
              pop.get('inside'), pop)
        shot(page3, '04-light-1024.png')
        check('C: 0 JS-ошибок (светлая)', len(js_errors3) == 0, js_errors3)

        # контроль: страница не содержит клиентского вызова эндпоинта
        src = open(os.path.join(REPO, 'index.html'), encoding='utf-8').read()
        check('C: index.html БЕЗ вызова KipAuth.api(\'workSchedule.getWeather\')',
              "KipAuth.api('workSchedule.getWeather'" not in src, None)
        check('C: index.html БЕЗ упоминаний authorizeWeather',
              'authorizeWeather' not in src, None)

        browser.close()

    print('\nИТОГО: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
