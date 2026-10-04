#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 473: browser-check — Графики КИП ИОС → вкладка «Приборы»,
# график «Количество приборов по графику ППР по месяцам на 2026 год».
# Заявка: «сделай что бы на графике ... отображалось количество
# приборов на каждый месяц на диаграмме, и проверь сама диаграмма
# не отображает зрительно количество приборов по месяцам "К
# Калибровка П Поверка ТО Тех. обслуж."».
# КОНТЕКСТ (мок Apps Script, порт 8998; Electron UA — charts-desktop.js
# грузится ТОЛЬКО в десктопе, Task 147):
#   A: тёмная 1280x900, Админ: «Графики КИП ИОС» открыты, заголовок
#      ППР точный; легенда 3 серии: К и П с «(правая ось)», ТО без;
#   B: подписи: 35 значений над столбцами (12 К + 11 П + 12 ТО) +
#      1 «0» (Май, П) у основания; data-scale: 23 secondary / 12
#      primary; 12 месяцев I–XII; строка «Итого:»;
#   C: ПРАВАЯ ОСЬ .ppr-y-axis-right: метки 50..0; ЛЕВАЯ: 500..0;
#   D: ВИДИМОСТЬ СТОЛБЦОВ (суть заявки): К сентябрь 48 → ~96% высоты
#      строки столбцов, П апрель 15 → ~30%, К январь 13 → ~26%
#      (до правки: 9.6% / 3% / 2.6% — зрительно ноль);
#   E: подписи над самыми высокими столбцами НЕ залезают на шапку
#      карточки (padding-top 16px);
#   F: 0 JS-ошибок; скриншот тёмная;
#   G: светлая тема — правая ось и подписи на месте; скриншот;
#   H: вкладка «Блокировки» — правой оси НЕТ (Кр 98 при ТО 210),
#      24 подписи над столбцами, сводка и топы рендерятся; скриншот.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task473')
os.makedirs(SHOT_DIR, exist_ok=True)

ELECTRON_UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) kip8test-desktop/1.0 Chrome/120.0.0.0 '
               'Safari/537.36 Electron/28.2.0')

PASS = 0
FAIL = 0


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))


def serve():
    os.chdir(REPO)

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

    httpd = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    httpd.serve_forever()


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': 'Админ'}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'Админ', 'found': True,
                        'permissions': {'calc.view': True, 'library.view': True,
                            'kipios.view': True, 'secret.view': True, 'whatsnew.view': True,
                            'charts.view': True, 'flowmeter.view': True,
                            'workschedule.view': True, 'workschedule.edit': True,
                            'admin.panel': True}}}, ensure_ascii=False))
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t473-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t473-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors


def open_charts(page):
    """Загрузка index.html → переход на «Графики КИП ИОС» (только десктоп)."""
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('charts')")
    page.wait_for_timeout(1200)


# Замеры графика ППР «Приборы» (один evaluate — меньше гонок)
MEASURE_JS = r"""(function(){
  var out = {};
  out.kipCharts = typeof KipCharts !== 'undefined';
  out.pageVisible = (function(){var p=document.getElementById('page-charts');
      return !!p && getComputedStyle(p).display!=='none';})();
  var title = document.querySelector('.ppr-chart-title');
  out.title = title ? title.textContent : '';
  var legend = document.querySelectorAll('.ppr-legend-item');
  out.legend = [];
  for (var i=0;i<legend.length;i++) out.legend.push(legend[i].textContent.replace(/\s+/g,' ').trim());
  out.valLabels = document.querySelectorAll('.ppr-bar-val').length;
  out.zeroLabels = document.querySelectorAll('.ppr-bar-val-zero').length;
  out.zeroText = (function(){var z=document.querySelector('.ppr-bar-val-zero');
      return z?z.textContent:'';})();
  out.secBars = document.querySelectorAll('.ppr-bar[data-scale="secondary"]').length;
  out.priBars = document.querySelectorAll('.ppr-bar[data-scale="primary"]').length;
  out.months = document.querySelectorAll('.ppr-month-label').length;
  out.totals = !!document.querySelector('.ppr-totals-row');
  var right = document.querySelectorAll('.ppr-y-axis-right .ppr-y-label');
  out.rightAxis = [];
  for (var i=0;i<right.length;i++) out.rightAxis.push(right[i].textContent.trim());
  var left = document.querySelectorAll('.ppr-chart-area .ppr-y-axis:not(.ppr-y-axis-right) .ppr-y-label');
  out.leftAxis = [];
  for (var i=0;i<left.length;i++) out.leftAxis.push(left[i].textContent.trim());
  // Высоты столбцов против высоты строки столбцов
  var groups = document.querySelectorAll('.ppr-month-group');
  out.groups = groups.length;
  if (groups.length === 12) {
    var row = groups[0].querySelector('.ppr-bars-row');
    var rowH = row ? row.getBoundingClientRect().height : 0;
    out.rowH = rowH;
    function barH(m, idx){
      var bars = groups[m].querySelectorAll('.ppr-bar');
      return bars[idx] ? bars[idx].getBoundingClientRect().height : -1;
    }
    out.kSep = barH(8, 0);   // К, сентябрь = 48 → 96% от 50
    out.pApr = barH(3, 1);   // П, апрель = 15 → 30% от 50
    out.kJan = barH(0, 0);   // К, январь = 13 → 26% от 50
    out.toMar = barH(2, 2);  // ТО, март = 500 → 100% от 500
    out.mayBars = groups[4].querySelectorAll('.ppr-bar').length; // П=0 → 2 бара
    out.mayZero = (function(){var z=groups[4].querySelector('.ppr-bar-val-zero');
        return z?z.textContent.trim():'';})();
    // Подпись над самым высоким столбцом (ТО, март) не залезает на шапку
    var card = document.querySelector('.ppr-chart-card');
    var header = card ? card.querySelector('.ppr-chart-header') : null;
    var tallest = groups[2].querySelectorAll('.ppr-bar')[2];
    var val = tallest ? tallest.querySelector('.ppr-bar-val') : null;
    if (header && val) {
      out.valTop = val.getBoundingClientRect().top;
      out.headerBottom = header.getBoundingClientRect().bottom;
    }
  }
  return out;
})()"""

with sync_playwright() as p:
    # Статический сервер репозитория (index.html + charts-desktop.js + data/*.json)
    threading.Thread(target=serve, daemon=True).start()
    import time
    time.sleep(0.5)

    browser = p.chromium.launch()

    # ================= Контекст 1: тёмная тема, «Приборы» =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                               user_agent=ELECTRON_UA)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'dark')
    open_charts(page)
    m = page.evaluate(MEASURE_JS)

    check('A1: KipCharts загружен (Electron UA)', m['kipCharts'])
    check('A2: страница «Графики КИП ИОС» видна', m['pageVisible'])
    check('A3: заголовок ППР точный',
          m['title'] == 'Количество приборов по графику ППР по месяцам на 2026 год', m['title'])
    check('A4: легенда — 3 серии', len(m['legend']) == 3, m['legend'])
    check('A5: К «Калибровка» помечена «(правая ось)»',
          'Калибровка' in m['legend'][0] and '(правая ось)' in m['legend'][0], m['legend'][0])
    check('A6: П «Поверка» помечена «(правая ось)»',
          'Поверка' in m['legend'][1] and '(правая ось)' in m['legend'][1], m['legend'][1])
    check('A7: ТО «Тех. обслуж.» без пометки правой оси',
          'Тех. обслуж.' in m['legend'][2] and '(правая ось)' not in m['legend'][2], m['legend'][2])

    check('B1: 35 подписей значений над столбцами (12 К + 11 П + 12 ТО)',
          m['valLabels'] == 35, m['valLabels'])
    check('B2: один «0» у основания (Май, Поверка)', m['zeroLabels'] == 1 and m['zeroText'] == '0',
          (m['zeroLabels'], m['zeroText']))
    check('B3: data-scale: 23 secondary / 12 primary',
          m['secBars'] == 23 and m['priBars'] == 12, (m['secBars'], m['priBars']))
    check('B4: 12 месяцев', m['months'] == 12 and m['groups'] == 12, (m['months'], m['groups']))
    check('B5: строка «Итого:» на месте', m['totals'])
    check('B6: в Мае 2 столбца (П = 0) и подпись «0»',
          m['mayBars'] == 2 and m['mayZero'] == '0', (m['mayBars'], m['mayZero']))

    check('C1: ПРАВАЯ ось с метками 50..0',
          m['rightAxis'] == ['50', '40', '30', '20', '10', '0'], m['rightAxis'])
    check('C2: ЛЕВАЯ ось с метками 500..0',
          m['leftAxis'] == ['500', '400', '300', '200', '100', '0'], m['leftAxis'])

    # D: зрительная различимость — суть заявки
    rowH = m.get('rowH', 0)
    check('D1: столбец К 48 (сентябрь) — %d%% высоты (>55%%)' % round(m['kSep'] / rowH * 100),
          m['kSep'] > 0.55 * rowH, (m['kSep'], rowH))
    check('D2: столбец П 15 (апрель) — %d%% высоты (>22%%)' % round(m['pApr'] / rowH * 100),
          m['pApr'] > 0.22 * rowH, (m['pApr'], rowH))
    check('D3: столбец К 13 (январь) — %d%% высоты (>15%%)' % round(m['kJan'] / rowH * 100),
          m['kJan'] > 0.15 * rowH, (m['kJan'], rowH))
    check('D4: столбец ТО 500 (март) — %d%% высоты (>80%%)' % round(m['toMar'] / rowH * 100),
          m['toMar'] > 0.8 * rowH, (m['toMar'], rowH))

    # E: подписи не залезают на шапку
    check('E1: подпись высокого столбца ниже шапки карточки',
          m['valTop'] >= m['headerBottom'] - 1, (m.get('valTop'), m.get('headerBottom')))

    check('F1: 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path=os.path.join(SHOT_DIR, '01-devices-dark.png'), full_page=False)
    print('    скриншот: 01-devices-dark.png')

    # ================= Контекст 2: светлая тема =================
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900},
                               user_agent=ELECTRON_UA)
    page2 = ctx2.new_page()
    js_errors2 = attach(page2, ctx2, 'light', 'light')
    open_charts(page2)
    m2 = page2.evaluate(MEASURE_JS)

    check('G1: светлая — заголовок ППР на месте', m2['title'].startswith('Количество приборов'))
    check('G2: светлая — правая ось с метками 50..0',
          m2['rightAxis'] == ['50', '40', '30', '20', '10', '0'], m2['rightAxis'])
    check('G3: светлая — 35 подписей + 1 «0»',
          m2['valLabels'] == 35 and m2['zeroLabels'] == 1, (m2['valLabels'], m2['zeroLabels']))
    rowH2 = m2.get('rowH', 0)
    check('G4: светлая — К 48 виден (%d%%), П 15 виден (%d%%)' % (
          round(m2['kSep'] / rowH2 * 100), round(m2['pApr'] / rowH2 * 100)),
          m2['kSep'] > 0.55 * rowH2 and m2['pApr'] > 0.22 * rowH2, (m2['kSep'], m2['pApr'], rowH2))
    check('G5: светлая — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    page2.screenshot(path=os.path.join(SHOT_DIR, '02-devices-light.png'), full_page=False)
    print('    скриншот: 02-devices-light.png')

    # ================= Контекст 3: вкладка «Блокировки» (регресс) =========
    page.evaluate("KipCharts.switchTab('lockouts')")
    page.wait_for_timeout(1500)
    m3 = page.evaluate("""(function(){
      var out = {};
      var titles = document.querySelectorAll('.ppr-chart-title');
      out.lockTitle = titles.length ? titles[0].textContent : '';
      out.rightAxis = document.querySelectorAll('.ppr-y-axis-right').length;
      out.axisHints = document.querySelectorAll('.ppr-legend-axis').length;
      out.valLabels = document.querySelectorAll('.ppr-bar-val').length;
      out.stats = document.querySelectorAll('.chart-stat-card').length;
      out.tops = document.querySelectorAll('.chart-card').length;
      return out;
    })()""")
    check('H1: график «График ППР — Схемы на 2026 год» отрисован',
          m3['lockTitle'] == 'График ППР — Схемы на 2026 год', m3['lockTitle'])
    check('H2: правой оси НЕТ (Кр 98 > 25% от ТО 210)', m3['rightAxis'] == 0, m3['rightAxis'])
    check('H3: подсказок «(правая ось)» нет', m3['axisHints'] == 0, m3['axisHints'])
    check('H4: 24 подписи над столбцами (12 Кр + 12 ТО)', m3['valLabels'] == 24, m3['valLabels'])
    check('H5: сводка и топы рендерятся (карточек >= 3)', m3['tops'] >= 3 and m3['stats'] >= 2,
          (m3['tops'], m3['stats']))
    check('H6: 0 JS-ошибок после вкладки «Блокировки»', len(js_errors) == 0, js_errors[:3])
    page.screenshot(path=os.path.join(SHOT_DIR, '03-lockouts-dark.png'), full_page=False)
    print('    скриншот: 03-lockouts-dark.png')

    ctx.close()
    ctx2.close()
    browser.close()

print('========================================')
print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
import sys
sys.exit(0 if FAIL == 0 else 1)
