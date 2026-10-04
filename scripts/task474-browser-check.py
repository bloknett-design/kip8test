#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 474: browser-check — раздел «КИП ИОС», подробная карточка
# прибора. Заявка: «В разделе КИП ИОС, в подробной карточке прибора
# размер текста типа прибора, расположенного перед картинкой
# прибора, сделай в полтора раза больше. И текст "№ прибора" и
# "Место установки" смести немного ниже от верхней границы
# карточки.»
# КОНТЕКСТ (мок Apps Script, порт 8995; приборы грузятся из локального
# data/devices.json — ID 1 «Счетчик воды турбинный», Тип «"Пульсар" ТХ»):
#   D (десктоп 1280x900, тёмная): панель деталей открыта; Тип на
#      картинке — computed font-size 18px (было 12px, ровно ×1.5);
#      оверлей Типа в пределах картинки, у её нижней грани;
#      «№ прибора» смещён от верха карточки на ~12px (было ~2px);
#      «Место установки» ниже «№ прибора»; значок избранного виден;
#      0 JS-ошибок; скриншот;
#   L (десктоп, светлая): те же замеры (размер/смещение в светлой
#      теме не переопределяются); скриншот;
#   M (мобильный 375x812, тёмная): страница device-detail; Тип 18px;
#      смещение меты ~12px; 0 JS-ошибок; скриншот.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8995
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task474')
os.makedirs(SHOT_DIR, exist_ok=True)

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
                body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t474-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_devices_cache')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t474-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors


def open_device_detail(page):
    """index.html → «КИП ИОС» → карточка прибора ID 1 (devOpenDetail)."""
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('kip-ios')")
    page.wait_for_timeout(1200)
    page.evaluate("devOpenDetail('1')")
    page.wait_for_timeout(800)


# Замеры карточки прибора (один evaluate — меньше гонок)
MEASURE_JS = r"""(function(){
  var out = {};
  var panel = document.getElementById('detailPanel');
  out.panelActive = panel && panel.classList.contains('active');
  var pg = document.getElementById('page-device-detail');
  out.pageVisible = !!pg && getComputedStyle(pg).display !== 'none'
      && pg.classList.contains('active');
  var overlay = document.querySelector('.dev-detail-type-overlay');
  out.overlayExists = !!overlay;
  if (overlay) {
    out.overlayText = overlay.textContent.trim();
    out.overlayFont = getComputedStyle(overlay).fontSize;
    out.overlayWeight = getComputedStyle(overlay).fontWeight;
    var wrap = document.querySelector('.dev-detail-image-wrap');
    var wr = wrap.getBoundingClientRect();
    var ov = overlay.getBoundingClientRect();
    out.overlayInWrap = ov.left >= wr.left - 1 && ov.right <= wr.right + 1
        && ov.top >= wr.top - 1 && ov.bottom <= wr.bottom + 1;
    out.overlayAtBottom = Math.abs(ov.bottom - wr.bottom) < 2;
  }
  var top = document.querySelector('.dev-detail-top');
  out.topExists = !!top;
  if (top) {
    var tr = top.getBoundingClientRect();
    var labels = document.querySelectorAll('.dev-detail-meta-label');
    out.labels = [];
    for (var i = 0; i < labels.length; i++)
      out.labels.push(labels[i].textContent.trim());
    if (labels.length) {
      out.label1Shift = labels[0].getBoundingClientRect().top - tr.top;
      out.label1Text = labels[0].textContent.trim();
    }
    if (labels.length > 1) {
      out.label2Shift = labels[1].getBoundingClientRect().top - tr.top;
      out.label2Text = labels[1].textContent.trim();
    }
  }
  var meta = document.querySelector('.dev-detail-meta');
  if (meta) out.metaPaddingTop = getComputedStyle(meta).paddingTop;
  var fav = document.querySelector('.dev-detail-fav-btn');
  out.favVisible = !!fav && getComputedStyle(fav).display !== 'none';
  out.cardCount = document.querySelectorAll('.dev-detail-card').length;
  return out;
})()"""

with sync_playwright() as p:
    # Статический сервер репозитория (index.html + data/devices.json)
    threading.Thread(target=serve, daemon=True).start()
    import time
    time.sleep(0.5)

    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280x900, тёмная =================
    print('=== Контекст 1: десктоп 1280x900, тёмная ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'dark')
    open_device_detail(page)
    m = page.evaluate(MEASURE_JS)

    check('D1: панель деталей открыта (devOpenDetail на десктопе)',
          m['panelActive'], m)
    check('D2: Тип прибора на карточке — «"Пульсар" ТХ»',
          m['overlayText'] == '"Пульсар" ТХ', m.get('overlayText'))
    check('D3: размер текста Типа = 18px (в полтора раза больше 12px)',
          m['overlayFont'] == '18px', m.get('overlayFont'))
    check('D4: 18 = 12 × 1.5 — ровно в полтора раза',
          18 == 12 * 1.5)
    check('D5: оверлей Типа — в пределах картинки («перед картинкой»)',
          m['overlayInWrap'], m)
    check('D6: оверлей Типа у нижней грани картинки (как было, Task 334)',
          m['overlayAtBottom'], m)
    check('D7: «№ прибора» смещён ниже от верхней границы карточки (~12px)',
          10 <= m.get('label1Shift', -1) <= 15,
          m.get('label1Shift'))
    check('D8: «Место установки» — ниже «№ прибора»',
          m.get('label2Shift', -1) > m.get('label1Shift', -1),
          (m.get('label1Shift'), m.get('label2Shift')))
    check('D9: подписи ровно по одной («№ прибора» + «Место установки»)',
          m['labels'] == ['№ прибора', 'Место установки'], m['labels'])
    check('D10: padding-top мета-блока = 12px (было 2px)',
          m.get('metaPaddingTop') == '12px', m.get('metaPaddingTop'))
    check('D11: значок избранного в правом верхнем углу виден (десктоп)',
          m['favVisible'], m)
    check('D12: карточка на панели одна', m['cardCount'] == 1, m['cardCount'])
    check('D13: 0 JS-ошибок (десктоп, тёмная)', len(js_errors) == 0,
          js_errors[:3])
    page.screenshot(path=os.path.join(SHOT_DIR, '01-device-detail-dark.png'))
    print('  скриншот: 01-device-detail-dark.png')
    ctx.close()

    # ================= Контекст 2: десктоп 1280x900, светлая =================
    print('=== Контекст 2: десктоп 1280x900, светлая ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'light', 'light')
    open_device_detail(page)
    m = page.evaluate(MEASURE_JS)

    check('L1: светлая тема — размер Типа тот же 18px',
          m['overlayFont'] == '18px', m.get('overlayFont'))
    check('L2: светлая тема — «№ прибора» смещён (~12px)',
          10 <= m.get('label1Shift', -1) <= 15, m.get('label1Shift'))
    check('L3: светлая тема — подписи на месте',
          m['labels'] == ['№ прибора', 'Место установки'], m['labels'])
    check('L4: 0 JS-ошибок (десктоп, светлая)', len(js_errors) == 0,
          js_errors[:3])
    page.screenshot(path=os.path.join(SHOT_DIR, '02-device-detail-light.png'))
    print('  скриншот: 02-device-detail-light.png')
    ctx.close()

    # ================= Контекст 3: мобильный 375x812, тёмная =================
    print('=== Контекст 3: мобильный 375x812, тёмная ===')
    ctx = browser.new_context(viewport={'width': 375, 'height': 812})
    page = ctx.new_page()
    js_errors = attach(page, ctx, 'dark', 'mob')
    open_device_detail(page)
    m = page.evaluate(MEASURE_JS)

    check('M1: страница деталей прибора открыта (мобильный путь)',
          m['pageVisible'], m)
    check('M2: мобильный — размер Типа 18px',
          m['overlayFont'] == '18px', m.get('overlayFont'))
    check('M3: мобильный — «№ прибора» смещён (~12px)',
          10 <= m.get('label1Shift', -1) <= 15, m.get('label1Shift'))
    check('M4: мобильный — подписи на месте',
          m['labels'] == ['№ прибора', 'Место установки'], m['labels'])
    check('M5: 0 JS-ошибок (мобильный)', len(js_errors) == 0,
          js_errors[:3])
    page.screenshot(path=os.path.join(SHOT_DIR, '03-device-detail-mobile.png'))
    print('  скриншот: 03-device-detail-mobile.png')
    ctx.close()

    browser.close()

print()
print('ИТОГО: %d ✓ / %d ✗' % (PASS, FAIL))
import sys
sys.exit(1 if FAIL else 0)
