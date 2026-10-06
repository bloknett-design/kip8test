#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 478: browser-check — раздел «КИП ИОС», подробная карточка
# прибора, строка «Период ремонта». Заявка: текст в строке с датой
# периода ремонта окрашивать в зелёный/красный по условиям ППР
# (в гр. ППР + вид ТО/К/П + срок не просрочен — зелёный;
# просрочен — красный; остальные — обычный цвет).
# КОНТЕКСТ (мок Apps Script, порт 8989; приборы — локальный
# data/devices.json; ОЖИДАНИЯ ДИНАМИЧЕСКИЕ — статус считается тем
# же алгоритмом на дату запуска, проверка не зависит от «сегодня»):
#   D (десктоп 1280x900, тёмная): ID 1 (К, 6 лет, ППР=Есть) →
#      ok/bad по дате; ID 16 (ТО, 3 мес, ППР=Есть) → ok/bad;
#      ID 81 (К, 2 года, ППР=Нет) → ВСЕГДА обычный; класс ровно
#      на значении строки, метка и прочие строки не окрашены;
#      fontWeight 600; 0 JS-ошибок; скриншоты;
#   L (десктоп, светлая): цвета light-палитры #2e7d32/#c62828;
#   M (мобильный 375x812, тёмная): та же тройка приборов через
#      мобильный путь (page-device-detail).
import json
import os
import re
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8989
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task478')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0

# Палитры (index.html, Task 478)
RGB = {
    ('dark', 'ok'): 'rgb(129, 199, 132)',    # #81c784
    ('dark', 'bad'): 'rgb(239, 83, 80)',     # #ef5350
    ('dark', 'normal'): 'rgb(208, 220, 232)',  # #d0dce8 (обычное значение)
    ('light', 'ok'): 'rgb(46, 125, 50)',     # #2e7d32
    ('light', 'bad'): 'rgb(198, 40, 40)',    # #c62828
    ('light', 'normal'): 'rgb(26, 26, 26)',  # #1a1a1a
}
CLS = {'ok': 'dev-ppr-ok', 'bad': 'dev-ppr-bad', 'normal': ''}


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))


# --- Эталонная логика (= devPprStatusClass) для динамических ожиданий ---
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
    return 'bad' if due < today else 'ok'


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
                body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t478-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_devices_cache')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t478-%s');" % tag +
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
    } else if (/dev-ppr-(ok|bad)/.test(val.className)) {
      out.coloredOthers++;
    }
  }
  // первая ПРОЧАЯ строка (не «Период ремонта») — обычный цвет (контроль
  // не-окрашивания прочих строк; «Позиция» бывает пуста и не рендерится)
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
          else ('dev-ppr-ok' not in p['className'] and 'dev-ppr-bad' not in p['className']),
          p['className'])
    check('%s-%s: computed color = %s' % (tag, dev_id, RGB[(theme, st)]),
          p['color'] == RGB[(theme, st)], p['color'])
    if st in ('ok', 'bad'):
        check('%s-%s: полужирный 600 (статус читается сразу)' % (tag, dev_id),
              p['fontWeight'] == '600', p['fontWeight'])
    check('%s-%s: метка «Период ремонта» НЕ окрашена' % (tag, dev_id),
          p['labelColor'] != p['color'], (p['labelColor'], p['color']))
    check('%s-%s: строка видима' % (tag, dev_id), p['visible'])
    check('%s-%s: прочие строки не окрашены (окрашена ровно одна)' % (tag, dev_id),
          m['coloredOthers'] == 0, m['coloredOthers'])
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
    # Тройка приборов: 1 (ППР=Есть, К, 6 лет), 16 (ППР=Есть, ТО, 3 мес),
    # 81 (ППР=Нет — всегда обычный)
    for did in ('1', '16', '81'):
        d = dev_info(did, devices)
        print('  ID %s: %s | %s %s | ППР=%s → %s' % (
            did, d['Наименование'][:30], d['Дата'], d['Период ремонта'],
            d['В гр. ППР'], ref_status(d, today)))

    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280x900, тёмная =================
    print('=== Контекст 1: десктоп 1280x900, тёмная ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'dark')
    open_device_detail(page)
    check('D1: панель деталей открыта (десктоп)',
          page.evaluate(MEASURE_JS)['panelActive'])

    check_device(page, 'dark', '1', devices, today, 'D')
    page.screenshot(path=os.path.join(SHOT_DIR, '01-period-ok-dark.png'))
    print('  скриншот: 01-period-ok-dark.png (ID 1)')

    page.evaluate("devOpenDetail('16')")
    page.wait_for_timeout(600)
    check_device(page, 'dark', '16', devices, today, 'D')
    page.screenshot(path=os.path.join(SHOT_DIR, '02-period-bad-dark.png'))
    print('  скриншот: 02-period-bad-dark.png (ID 16)')

    page.evaluate("devOpenDetail('81')")
    page.wait_for_timeout(600)
    m81 = check_device(page, 'dark', '81', devices, today, 'D')
    # первая прочая строка — обычного цвета (не наследует окраску)
    if m81:
        check('D-81: прочая строка (не «Период ремонта») обычного цвета',
              m81['firstOtherColor'] == RGB[('dark', 'normal')], m81['firstOtherColor'])
    page.screenshot(path=os.path.join(SHOT_DIR, '03-period-normal-dark.png'))
    print('  скриншот: 03-period-normal-dark.png (ID 81, ППР=Нет)')

    check('D2: 0 JS-ошибок (десктоп, тёмная)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: десктоп 1280x900, светлая =================
    print('=== Контекст 2: десктоп 1280x900, светлая ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'light')
    open_device_detail(page)
    page.evaluate("devOpenDetail('1')")
    page.wait_for_timeout(600)
    check_device(page, 'light', '1', devices, today, 'L')
    page.evaluate("devOpenDetail('16')")
    page.wait_for_timeout(600)
    check_device(page, 'light', '16', devices, today, 'L')
    page.screenshot(path=os.path.join(SHOT_DIR, '04-period-light.png'))
    print('  скриншот: 04-period-light.png (ID 16 + ID 1)')
    check('L1: 0 JS-ошибок (десктоп, светлая)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 3: мобильный 375x812, тёмная =================
    print('=== Контекст 3: мобильный 375x812, тёмная ===')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mob')
    open_device_detail(page)
    m = page.evaluate(MEASURE_JS)
    check('M1: страница деталей прибора открыта (мобильный путь)',
          m['pageVisible'])

    check_device(page, 'dark', '1', devices, today, 'M')
    page.evaluate("devOpenDetail('16')")
    page.wait_for_timeout(600)
    check_device(page, 'dark', '16', devices, today, 'M')
    page.screenshot(path=os.path.join(SHOT_DIR, '05-period-bad-mobile.png'))
    print('  скриншот: 05-period-bad-mobile.png (ID 16)')
    page.evaluate("devOpenDetail('81')")
    page.wait_for_timeout(600)
    check_device(page, 'dark', '81', devices, today, 'M')
    check('M2: 0 JS-ошибок (мобильный)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d ✓ / %d ✗' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
