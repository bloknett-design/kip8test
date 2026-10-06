#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 479: browser-check — (а) карточка прибора КИП ИОС, строка
# «Период ремонта»: ТРЕТИЙ цвет — оранжево-золотистый, если срок
# просрочен, но месяц срока = ТЕКУЩИЙ календарный месяц; (б) ТАБЛИЧНЫЙ
# ВИД (десктоп-модуль devices-table-desktop.js, Electron UA):
# столбец «Дата» — те же цвета в ячейках.
# КОНТЕКСТ (мок Apps Script, порт 8994; приборы — локальный
# data/devices.json; ОЖИДАНИЯ ДИНАМИЧЕСКИЕ — статус считается тем же
# алгоритмом на дату запуска):
#   D (десктоп 1280x900, тёмная, Electron UA): ID 1 → ok; warn-прибор
#      (ищется динамически, сегодня ID 30 «Датчик-реле давления»,
#      2025-10-01 + 1 год = 2026-10-01 → текущий месяц) → ЗОЛОТИСТЫЙ;
#      ID 16 → bad; ID 81 (ППР=Нет) → обычный; класс ровно на значении
#      строки; fontWeight 600; 0 JS-ошибок; скриншоты;
#   L (десктоп, светлая, Electron UA): light-палитра #a06a00;
#   TAB/TABL (десктоп, тёмная/светлая, Electron UA): «Приборы по
#      производствам» → кнопка «Таблица» → столбец «Дата»: для КАЖДОЙ
#      отрисованной строки класс/цвет ячейки = эталону (Python);
#      поиск по имени warn-прибора гарантирует золотистые строки;
#      скролл к столбцу «Дата» + скриншоты;
#   M (мобильный 375x812, тёмная, БЕЗ Electron): мобильный путь
#      карточки (page-device-detail) + таблица НЕ загружается на
#      мобильном (модуль только десктопа).
import json
import os
import re
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8994
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task479')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# Палитры (index.html + devices-table-desktop.js, Task 478+479)
RGB = {
    ('dark', 'ok'): 'rgb(129, 199, 132)',      # #81c784
    ('dark', 'warn'): 'rgb(224, 160, 48)',     # #e0a030
    ('dark', 'bad'): 'rgb(239, 83, 80)',       # #ef5350
    ('dark', 'normal'): 'rgb(208, 220, 232)',  # #d0dce8 (значение карточки)
    ('dark', 'td_normal'): 'rgb(182, 194, 212)',  # #b6c2d4 (базовая td)
    ('light', 'ok'): 'rgb(46, 125, 50)',       # #2e7d32
    ('light', 'warn'): 'rgb(160, 106, 0)',     # #a06a00
    ('light', 'bad'): 'rgb(198, 40, 40)',      # #c62828
    ('light', 'normal'): 'rgb(26, 26, 26)',    # #1a1a1a
    ('light', 'td_normal'): 'rgb(44, 58, 76)',  # #2c3a4c
}
CLS = {'ok': 'dev-ppr-ok', 'warn': 'dev-ppr-warn', 'bad': 'dev-ppr-bad', 'normal': ''}

ELECTRON_UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) kip8test-desktop/2.1.8 '
               'Chrome/128.0.0.0 Electron/33.0.0 Safari/537.36')


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))


# --- Эталонная логика (= devPprStatusClass после Task 479) ---
def ref_status(dev, today):
    if str(dev.get('В гр. ППР', '')).strip().lower() != 'есть':
        return 'normal'
    vid = str(dev.get('Вид ремонта', '')).strip().upper()
    if vid not in ('ТО', 'К', 'П'):
        return 'normal'
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', str(dev.get('Дата', '')).strip())
    if not m:
        return 'normal'
    per = str(dev.get('Период ремонта', ''))
    pm = re.search(r'(\d+)', per)
    if not pm:
        return 'normal'
    n = int(pm.group(1))
    if n <= 0:
        return 'normal'
    pl = per.lower()
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if 'мес' in pl:
        mo += n
        y += (mo - 1) // 12
        mo = (mo - 1) % 12 + 1
    elif 'год' in pl or 'лет' in pl:
        y += n
    else:
        return 'normal'
    # JS Date переполнение дня: 31-е/29-е числа переполняются в след. месяц
    import calendar
    last = calendar.monthrange(y, mo)[1]
    if d > last:
        mo += 1
        if mo > 12:
            mo = 1
            y += 1
        last = calendar.monthrange(y, mo)[1]
        d = min(d, last)
    due = '%04d-%02d-%02d' % (y, mo, d)
    if due >= today:
        return 'ok'
    if due[:7] == today[:7]:
        return 'warn'
    return 'bad'


def fmt_date_ru(iso):
    y, m, d = iso.split('-')
    return '%s.%s.%s' % (d, m, y)


def serve():
    os.chdir(REPO)

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

    httpd = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    httpd.serve_forever()


def attach(page, ctx, theme, tag, electron=False):
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
                body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t479-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_devices_cache')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:devTableMode')}catch(e){};" +
        "try{localStorage.removeItem('devTableMode')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t479-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors


def open_device_detail(page):
    """index.html → «КИП ИОС» → карточка прибора (devOpenDetail)."""
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1200)
    page.evaluate("devOpenDetail('1')")
    page.wait_for_timeout(800)


# Замер строки «Период ремонта» в карточке прибора (один evaluate)
MEASURE_JS = r"""(function(){
  var out = {};
  var panel = document.getElementById('detailPanel');
  out.panelActive = panel && panel.classList.contains('active');
  var pg = document.getElementById('page-device-detail');
  out.pageVisible = !!pg && pg.classList.contains('active');
  var rows = document.querySelectorAll('.dev-card-row');
  out.rowsTotal = rows.length;
  out.period = null;
  out.coloredOthers = 0;
  for (var i = 0; i < rows.length; i++) {
    var lbl = rows[i].querySelector('.dev-card-label');
    var val = rows[i].querySelector('.dev-card-value');
    if (!lbl || !val) continue;
    if (lbl.textContent.trim() === 'Период ремонта') {
      var cs = getComputedStyle(val);
      var lcs = getComputedStyle(lbl);
      out.period = {
        text: val.textContent.trim(),
        className: val.className,
        color: cs.color,
        fontWeight: cs.fontWeight,
        visible: val.offsetParent !== null,
        labelColor: lcs.color,
        labelText: lbl.textContent.trim()
      };
    } else if (/dev-ppr-(ok|bad|warn)/.test(val.className)) {
      out.coloredOthers++;
    }
  }
  var firstOtherColor = null;
  for (var j = 0; j < rows.length; j++) {
    var l2 = rows[j].querySelector('.dev-card-label');
    if (l2 && l2.textContent.trim() !== 'Период ремонта') {
      firstOtherColor = getComputedStyle(rows[j].querySelector('.dev-card-value')).color;
      break;
    }
  }
  out.firstOtherColor = firstOtherColor;
  out.title = (document.getElementById('deviceDetailTitle') || {}).textContent || '';
  return out;
})()"""


# Замер табличного вида: столбец «Дата» + ppr-классы ячеек
TABLE_JS = r"""(function(){
  var out = {};
  var wrap = document.querySelector('#page-devices-prod .dev-table-wrap');
  out.wrap = !!wrap;
  var btn = document.getElementById('devTableToggleBtn');
  out.btn = !!btn;
  out.btnActive = !!(btn && btn.classList.contains('active'));
  var group = document.getElementById('devTableHeaderGroup');
  out.groupActive = !!(group && group.classList.contains('table-active'));
  var table = wrap ? wrap.querySelector('table.dev-table') : null;
  out.table = !!table;
  if (!table) return out;
  var ths = table.querySelectorAll('thead th');
  var dateIdx = -1;
  for (var i = 0; i < ths.length; i++) {
    // заголовок = label + иконки сортировки/фильтра — ищем по
    // data-sort-key (или по началу текста)
    var k = ths[i].getAttribute('data-sort-key');
    if (k === 'Дата' || (ths[i].textContent || '').trim().indexOf('Дата') === 0) {
      dateIdx = i; break;
    }
  }
  out.dateIdx = dateIdx;
  out.cols = ths.length;
  var rows = table.querySelectorAll('tbody tr.dev-table-row');
  out.rowsRendered = rows.length;
  out.rows = [];
  for (var r = 0; r < rows.length; r++) {
    var tr = rows[r];
    var tds = tr.querySelectorAll('td');
    var rec = { id: tr.getAttribute('data-dev-id'), cells: tds.length, pprTds: [] };
    for (var c = 0; c < tds.length; c++) {
      var cn = tds[c].className || '';
      var m = cn.match(/dev-ppr-(ok|warn|bad)/);
      if (m) {
        var cs = getComputedStyle(tds[c]);
        rec.pprTds.push({ idx: c, cls: m[1], text: (tds[c].textContent || '').trim(),
                          color: cs.color, fontWeight: cs.fontWeight });
      }
    }
    if (dateIdx >= 0 && tds[dateIdx]) {
      rec.dateText = (tds[dateIdx].textContent || '').trim();
      rec.dateColor = getComputedStyle(tds[dateIdx]).color;
      rec.dateLeft = tds[dateIdx].offsetLeft;
    }
    out.rows.push(rec);
  }
  var si = document.getElementById('devProdSearchInput');
  out.searchValue = si ? si.value : null;
  out.count = (document.getElementById('devTableCount') || {}).textContent || '';
  return out;
})()"""


def dev_info(dev_id, devices):
    for d in devices:
        if str(d['ID']) == str(dev_id):
            return d
    return None


def expected_text(dev):
    parts = [fmt_date_ru(dev['Дата']), dev['Вид ремонта'], dev['Период ремонта']]
    return ' '.join(p for p in parts if p)


def check_device(page, theme, dev_id, devices, today, tag):
    m = page.evaluate(MEASURE_JS)
    dev = dev_info(dev_id, devices)
    st = ref_status(dev, today)
    p = m.get('period')
    check('%s-%s: строка «Период ремонта» отрисована' % (tag, dev_id),
          p is not None, m)
    if not p:
        return
    check('%s-%s: текст строки = «%s»' % (tag, dev_id, expected_text(dev)),
          p['text'] == expected_text(dev), p['text'])
    check('%s-%s: статус %s — класс %s' % (tag, dev_id, st, CLS[st] or 'обычный'),
          (CLS[st] in p['className'].split(' ')) if CLS[st]
          else ('dev-ppr-ok' not in p['className'] and 'dev-ppr-bad' not in p['className']
                and 'dev-ppr-warn' not in p['className']),
          p['className'])
    check('%s-%s: computed color = %s' % (tag, dev_id, RGB[(theme, st)]),
          p['color'] == RGB[(theme, st)], p['color'])
    if st in ('ok', 'warn', 'bad'):
        check('%s-%s: полужирный 600 (статус читается сразу)' % (tag, dev_id),
              p['fontWeight'] == '600', p['fontWeight'])
    check('%s-%s: метка «Период ремонта» НЕ окрашена' % (tag, dev_id),
          p['labelColor'] != p['color'], (p['labelColor'], p['color']))
    check('%s-%s: строка видима' % (tag, dev_id), p['visible'])
    check('%s-%s: прочие строки не окрашены (окрашена ровно одна)' % (tag, dev_id),
          m['coloredOthers'] == 0, m['coloredOthers'])
    return m


def check_table(page, theme, devices, today, tag, shot_name, require=None):
    m = page.evaluate(TABLE_JS)
    check('%s: табличный вид включён (wrap + table)' % tag,
          m['wrap'] and m['table'], m)
    check('%s: кнопка «Таблица» активна + группа table-active' % tag,
          m['btn'] and m['btnActive'] and m['groupActive'])
    check('%s: столбец «Дата» найден в шапке' % tag, m['dateIdx'] >= 0, m['dateIdx'])
    check('%s: строки отрисованы (виртуальное окно)' % tag, m['rowsRendered'] > 0,
          m['rowsRendered'])
    if not m['rows']:
        return m
    counts = {'ok': 0, 'warn': 0, 'bad': 0, 'normal': 0}
    bad_rows = []
    for rec in m['rows']:
        dev = dev_info(rec['id'], devices)
        if dev is None:
            bad_rows.append(('нет прибора', rec['id']))
            continue
        st = ref_status(dev, today)
        counts[st] += 1
        if st == 'normal':
            if rec['pprTds']:
                bad_rows.append(('лишний класс у обычного', rec['id'], rec['pprTds']))
            else:
                # ячейка даты обычного прибора — базовый цвет td
                if rec.get('dateColor') != RGB[(theme, 'td_normal')]:
                    bad_rows.append(('обычный: цвет даты', rec['id'],
                                     rec.get('dateColor'), RGB[(theme, 'td_normal')]))
        else:
            if len(rec['pprTds']) != 1:
                bad_rows.append(('не один ppr-td', rec['id'], rec['pprTds']))
                continue
            td = rec['pprTds'][0]
            if td['idx'] != m['dateIdx']:
                bad_rows.append(('класс не в столбце «Дата»', rec['id'], td['idx']))
            if td['cls'] != st:
                bad_rows.append(('класс != эталону', rec['id'], td['cls'], st))
            if td['text'] != str(dev.get('Дата', '')):
                bad_rows.append(('текст != дате прибора', rec['id'], td['text']))
            if td['color'] != RGB[(theme, st)]:
                bad_rows.append(('цвет', rec['id'], td['color'], RGB[(theme, st)]))
            if td['fontWeight'] != '600':
                bad_rows.append(('жирность', rec['id'], td['fontWeight']))
    check('%s: КАЖДАЯ отрисованная строка совпадает с эталоном (класс/цвет/текст)'
          % tag, not bad_rows, bad_rows[:4])
    check('%s: статусная палитра представлена (ok=%d, warn=%d, bad=%d, обычный=%d)'
          % (tag, counts['ok'], counts['warn'], counts['bad'], counts['normal']),
          counts['ok'] > 0 and counts['normal'] >= 0)
    if require:
        check('%s: строки со статусом «%s» есть в отрисовке (%d)'
              % (tag, require, counts[require]), counts[require] > 0, counts)
    # скролл к столбцу «Дата» — для скриншота
    page.evaluate(
        "(function(){var w=document.querySelector('#page-devices-prod .dev-table-wrap');"
        "if(w){w.scrollLeft=Math.max(0,(%d-150));}})()" % (m['rows'][0].get('dateLeft') or 3000))
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(SHOT_DIR, shot_name))
    print('  скриншот: %s (ok=%d warn=%d bad=%d обычный=%d)' % (
        shot_name, counts['ok'], counts['warn'], counts['bad'], counts['normal']))
    return m


with sync_playwright() as p:
    # Статический сервер репозитория (index.html + data/devices.json)
    threading.Thread(target=serve, daemon=True).start()
    time.sleep(0.5)

    # Дата «сегодня» (драйвер и браузер в одном часовом поясе)
    today = time.strftime('%Y-%m-%d')
    devices = json.load(open(os.path.join(REPO, 'data', 'devices.json'),
                             encoding='utf-8'))['devices']
    print('«Сегодня» браузера: %s (ожидания динамические)' % today)

    # warn-прибор ищется ДИНАМИЧЕСКИ на дату запуска (ядро заявки 479)
    warn_dev = None
    for d in devices:
        if isinstance(d.get('ID'), int) and d.get('Наименование') and \
           str(d.get('Дата', '')).startswith('20') and ref_status(d, today) == 'warn':
            warn_dev = d
            break
    check('данные: warn-прибор найден на сегодня', warn_dev is not None,
          'нет приборов со сроком в текущем месяце')
    warn_id = str(warn_dev['ID']) if warn_dev else '30'
    warn_name = warn_dev['Наименование'] if warn_dev else 'Датчик-реле давления'
    if warn_dev:
        print('  warn-прибор: ID %s | %s | %s %s | ППР=%s → срок на текущий месяц' % (
            warn_id, warn_name[:34], warn_dev['Дата'], warn_dev['Период ремонта'],
            warn_dev['В гр. ППР']))
    for did in ('1', '16', '81'):
        d = dev_info(did, devices)
        print('  ID %s: %s | %s %s | ППР=%s → %s' % (
            did, d['Наименование'][:30], d['Дата'], d['Период ремонта'],
            d['В гр. ППР'], ref_status(d, today)))

    browser = p.chromium.launch()

    # ============ Контекст 1: десктоп 1280x900, тёмная, Electron UA ============
    print('=== Контекст 1: десктоп 1280x900, тёмная, Electron UA (карточка) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                              user_agent=ELECTRON_UA)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'dark')
    open_device_detail(page)
    check('D1: панель деталей открыта (десктоп)',
          page.evaluate(MEASURE_JS)['panelActive'])

    check_device(page, 'dark', '1', devices, today, 'D')
    page.screenshot(path=os.path.join(SHOT_DIR, '01-period-ok-dark.png'))
    print('  скриншот: 01-period-ok-dark.png (ID 1)')

    page.evaluate("devOpenDetail('%s')" % warn_id)
    page.wait_for_timeout(600)
    check_device(page, 'dark', warn_id, devices, today, 'D')
    page.screenshot(path=os.path.join(SHOT_DIR, '02-period-warn-dark.png'))
    print('  скриншот: 02-period-warn-dark.png (ID %s — ЗОЛОТИСТЫЙ, текущий месяц)' % warn_id)

    page.evaluate("devOpenDetail('16')")
    page.wait_for_timeout(600)
    check_device(page, 'dark', '16', devices, today, 'D')
    page.screenshot(path=os.path.join(SHOT_DIR, '03-period-bad-dark.png'))
    print('  скриншот: 03-period-bad-dark.png (ID 16 — КРАСНЫЙ, прошлые месяцы)')

    page.evaluate("devOpenDetail('81')")
    page.wait_for_timeout(600)
    m81 = check_device(page, 'dark', '81', devices, today, 'D')
    if m81:
        check('D-81: прочая строка обычного цвета (не наследует окраску)',
              m81['firstOtherColor'] == RGB[('dark', 'normal')], m81['firstOtherColor'])
    page.screenshot(path=os.path.join(SHOT_DIR, '04-period-normal-dark.png'))
    print('  скриншот: 04-period-normal-dark.png (ID 81, ППР=Нет)')

    check('D2: 0 JS-ошибок (десктоп, тёмная, Electron)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 2: десктоп, светлая, Electron UA ============
    print('=== Контекст 2: десктоп 1280x900, светлая, Electron UA (карточка) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                              user_agent=ELECTRON_UA)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'light')
    open_device_detail(page)
    page.evaluate("devOpenDetail('%s')" % warn_id)
    page.wait_for_timeout(600)
    check_device(page, 'light', warn_id, devices, today, 'L')
    page.evaluate("devOpenDetail('1')")
    page.wait_for_timeout(600)
    check_device(page, 'light', '1', devices, today, 'L')
    page.screenshot(path=os.path.join(SHOT_DIR, '05-period-light.png'))
    print('  скриншот: 05-period-light.png (ID %s золотистый + ID 1 зелёный)' % warn_id)
    check('L1: 0 JS-ошибок (десктоп, светлая)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 3: десктоп, тёмная, Electron — ТАБЛИЦА ============
    print('=== Контекст 3: десктоп, тёмная, Electron UA (табличный вид) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                              user_agent=ELECTRON_UA)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'tab')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('devices-prod')")
    page.wait_for_timeout(1200)
    # модуль десктопа загрузился (Electron UA) — ждём кнопку «Таблица»
    for _ in range(40):
        if page.evaluate("!!document.getElementById('devTableToggleBtn')"):
            break
        page.wait_for_timeout(250)
    check('TAB0: модуль таблицы загружен (кнопка «Таблица» в шапке)',
          page.evaluate("!!document.getElementById('devTableToggleBtn')"))
    page.click('#devTableToggleBtn')
    page.wait_for_timeout(900)

    check_table(page, 'dark', devices, today, 'TAB', '06-table-dates-dark.png')

    # поиск по имени warn-прибора → гарантированные золотистые строки
    page.evaluate(
        "(function(){var el=document.getElementById('devProdSearchInput');"
        "el.value=%s;el.dispatchEvent(new Event('input'));})()" % json.dumps(warn_name))
    page.wait_for_timeout(900)
    m = check_table(page, 'dark', devices, today, 'TAB-S', '07-table-warn-dark.png', require='warn')
    check('TAB-S: поиск отфильтровал строки (в окне > 0)', m and m['rowsRendered'] > 0,
          m['rowsRendered'] if m else None)

    # поиск красного прибора (Мутномер, ID 16 — просрочен давно)
    page.evaluate(
        "(function(){var el=document.getElementById('devProdSearchInput');"
        "el.value='Мутномер';el.dispatchEvent(new Event('input'));})()")
    page.wait_for_timeout(900)
    check_table(page, 'dark', devices, today, 'TAB-B', '07b-table-bad-dark.png', require='bad')

    # поиск обычного прибора (ППР=Нет — ячейка даты без класса)
    page.evaluate(
        "(function(){var el=document.getElementById('devProdSearchInput');"
        "el.value='Регистратор безбумажный';el.dispatchEvent(new Event('input'));})()")
    page.wait_for_timeout(900)
    check_table(page, 'dark', devices, today, 'TAB-N', '07c-table-normal-dark.png', require='normal')

    # сброс поиска — возврат к полному списку
    page.evaluate(
        "(function(){var el=document.getElementById('devProdSearchInput');"
        "el.value='';el.dispatchEvent(new Event('input'));})()")
    page.wait_for_timeout(600)
    check('TAB2: 0 JS-ошибок (таблица, тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 4: десктоп, светлая, Electron — ТАБЛИЦА ============
    print('=== Контекст 4: десктоп 1280x900, светлая, Electron UA (табличный вид) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900},
                              user_agent=ELECTRON_UA)
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'tabl')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('devices-prod')")
    page.wait_for_timeout(1200)
    for _ in range(40):
        if page.evaluate("!!document.getElementById('devTableToggleBtn')"):
            break
        page.wait_for_timeout(250)
    page.click('#devTableToggleBtn')
    page.wait_for_timeout(900)
    page.evaluate(
        "(function(){var el=document.getElementById('devProdSearchInput');"
        "el.value=%s;el.dispatchEvent(new Event('input'));})()" % json.dumps(warn_name))
    page.wait_for_timeout(900)
    check_table(page, 'light', devices, today, 'TABL', '08-table-warn-light.png', require='warn')
    check('TABL2: 0 JS-ошибок (таблица, светлая)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ============ Контекст 5: мобильный 375x812, тёмная, БЕЗ Electron ============
    print('=== Контекст 5: мобильный 375x812, тёмная (без Electron) ===')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mob')
    open_device_detail(page)
    m = page.evaluate(MEASURE_JS)
    check('M1: страница деталей прибора открыта (мобильный путь)',
          m['pageVisible'])

    check_device(page, 'dark', '1', devices, today, 'M')
    page.evaluate("devOpenDetail('%s')" % warn_id)
    page.wait_for_timeout(600)
    check_device(page, 'dark', warn_id, devices, today, 'M')
    page.screenshot(path=os.path.join(SHOT_DIR, '09-period-warn-mobile.png'))
    print('  скриншот: 09-period-warn-mobile.png (ID %s — золотистый)' % warn_id)
    page.evaluate("devOpenDetail('16')")
    page.wait_for_timeout(600)
    check_device(page, 'dark', '16', devices, today, 'M')
    # модуль таблицы — ТОЛЬКО десктоп: на мобильном кнопки/таблицы нет
    page.evaluate("navigateTo('devices-prod')")
    page.wait_for_timeout(900)
    check('M2: таблица НЕ загружается на мобильном (модуль только десктопа)',
          page.evaluate("!(document.getElementById('devTableToggleBtn') || "
                        "document.querySelector('#page-devices-prod .dev-table-wrap'))"))
    check('M3: 0 JS-ошибок (мобильный)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d ✓ / %d ✗' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
