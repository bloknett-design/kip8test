#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 480: browser-check — смена ссылки на Google-таблицу «Перечень
# КИП ИОС рабочий.xlsx» (новый ID 1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee).
# Заявка: «Поменяй во всех связанных местах и файлах приложения,
# адрес ссылки на файл … теперь такой https://docs.google.com/
# spreadsheets/d/1ZKOPBs…/edit?usp=sharing&ouid=…&rtpof=true&sd=true».
# ПРОВЕРЯЕТСЯ (мок Apps Script, порт 8988; приборы — локальный
# data/devices.json):
#   A (десктоп 1280x900, тёмная):
#      A1 приложение открывается, роль Админ применена (не логин);
#      A2 SW контролирует страницу (после reload), версия кэша
#         kipia-test-v704 в caches.keys(), v703 нет;
#      A3 DATA-кэш kipia-data-test-v1 отдаёт ОБНОВЛЁННЫЙ
#         data/devices.json: source содержит новый ID, total 1291;
#      A4 fetch data/devices.json из страницы: новый ID в source;
#      A5 «КИП ИОС» открывается, подразделы отрисованы;
#      A6 «Приборы» (по производствам): список производств не пуст,
#         инфо-строка не «Загрузка…»;
#      A7 карточка прибора ID 1: страница активна, строка «Период
#         ремонта» отрисована (данные живы), заголовок не пуст;
#      A8 0 JS-ошибок; скриншоты (раздел + карточка).
#   B (десктоп, светлая): карточка прибора отрисовывается, 0 JS.
#   C (мобильный 375x812, тёмная): «КИП ИОС» открывается, 0 JS.
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8988
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task480')
os.makedirs(SHOT_DIR, exist_ok=True)

NEW_ID = '1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee'
OLD_ID = '1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy'

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
                      body='not found (t480-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_devices_cache')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t480-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors


def goto_app(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)


# Замер состояния приложения (один evaluate)
STATE_JS = r"""(async function(){
  var out = {};
  out.activePage = (document.querySelector('.page-content.active') || {}).id || '';
  out.loginVisible = !!(document.getElementById('page-login') &&
      document.getElementById('page-login').classList.contains('active'));
  out.swController = !!(navigator.serviceWorker && navigator.serviceWorker.controller);
  try {
    var keys = await caches.keys();
    out.cacheKeys = keys.join(',');
  } catch (e) { out.cacheKeys = 'ERR:' + e.message; }
  try {
    var d = await fetch('data/devices.json', {cache: 'no-store'}).then(function(r){return r.json();});
    out.devSource = d.source || '';
    out.devTotal = d.total_devices;
    out.devFirst = (d.devices && d.devices[0] && d.devices[0]['Наименование']) || '';
  } catch (e) { out.devSource = 'ERR:' + e.message; out.devTotal = -1; }
  return out;
})()"""

# DATA-кэш SW: текст закэшированного devices.json (после reload)
DATA_CACHE_JS = r"""(async function(){
  var out = {};
  try {
    var c = await caches.open('kipia-data-test-v1');
    var r = await c.match('http://localhost:%d/data/devices.json');
    if (!r) { r = await c.match('./data/devices.json'); }
    if (!r) {
      var keys = await c.keys();
      var k = keys.map(function(x){return x.url;}).filter(function(u){return u.indexOf('devices.json') !== -1;})[0];
      if (k) { r = await c.match(k); }
    }
    out.found = !!r;
    if (r) {
      var t = await r.text();
      out.hasNewId = t.indexOf('%s') !== -1;
      out.hasOldId = t.indexOf('%s') !== -1;
      out.total1291 = t.indexOf('"total_devices": 1291') !== -1;
    }
  } catch (e) { out.found = false; out.err = e.message; }
  return out;
})""" % (PORT, NEW_ID, OLD_ID)

# Раздел + список производств + карточка
SECTION_JS = r"""(function(){
  var out = {};
  var kip = document.getElementById('page-kip-ios');
  out.kipActive = !!(kip && kip.classList.contains('active'));
  out.kipVisible = !!(kip && kip.offsetParent !== null);
  out.prodActive = !!(document.getElementById('page-devices-prod') &&
      document.getElementById('page-devices-prod').classList.contains('active'));
  out.prodListLen = (document.getElementById('devProdList') || {children: []}).children.length;
  out.prodInfo = (document.getElementById('devProdInfo') || {}).textContent || '';
  return out;
})()"""

DETAIL_JS = r"""(function(){
  var out = {};
  // десктоп: карточка в боковой панели #detailPanel (Task 334);
  // мобайл: страница #page-device-detail — рендер общий (devRenderDetail)
  var panel = document.getElementById('detailPanel');
  out.panelActive = !!(panel && panel.classList.contains('active'));
  out.panelVisible = !!(panel && panel.offsetParent !== null);
  var pg = document.getElementById('page-device-detail');
  out.pageActive = !!(pg && pg.classList.contains('active'));
  out.pageVisible = !!(pg && pg.offsetParent !== null);
  out.title = (document.getElementById('deviceDetailTitle') || {}).textContent || '';
  out.rows = document.querySelectorAll('.dev-card-row').length;
  out.periodRow = null;
  var rows = document.querySelectorAll('.dev-card-row');
  for (var i = 0; i < rows.length; i++) {
    var lbl = rows[i].querySelector('.dev-card-label');
    if (lbl && lbl.textContent.trim() === 'Период ремонта') {
      out.periodRow = (rows[i].querySelector('.dev-card-value') || {}).textContent || '';
    }
  }
  return out;
})()"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ===== A. Десктоп 1280x900, тёмная =====
        print('A. Десктоп 1280x900, тёмная тема')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        errs = attach(page, ctx, 'dark', 'A')

        goto_app(page)
        st = page.evaluate(STATE_JS)
        check('A1: приложение открылось (не экран входа)', not st.get('loginVisible'),
              st)
        check('A4: data/devices.json — source с НОВЫМ ID',
              NEW_ID in (st.get('devSource') or ''), st.get('devSource'))
        check('A4: старый ID в source отсутствует',
              OLD_ID not in (st.get('devSource') or ''), st.get('devSource'))
        check('A4: total_devices = 1291 (данные не менялись)',
              st.get('devTotal') == 1291, st.get('devTotal'))

        # reload → SW контролирует страницу
        page.reload()
        page.wait_for_timeout(2500)
        st2 = page.evaluate(STATE_JS)
        check('A2: SW контролирует страницу', st2.get('swController'))
        check('A2: кэш kipia-test-v704 в caches.keys()',
              'kipia-test-v704' in (st2.get('cacheKeys') or ''),
              st2.get('cacheKeys'))
        check('A2: прежнего кэша kipia-test-v703 нет',
              'kipia-test-v703' not in (st2.get('cacheKeys') or ''),
              st2.get('cacheKeys'))
        check('A2: персистентный DATA-кэш kipia-data-test-v1 жив',
              'kipia-data-test-v1' in (st2.get('cacheKeys') or ''),
              st2.get('cacheKeys'))
        dc = page.evaluate(DATA_CACHE_JS)
        check('A3: DATA-кэш хранит devices.json', dc.get('found'), dc)
        check('A3: в DATA-кэше НОВЫЙ ID (source обновлён)', dc.get('hasNewId'), dc)
        check('A3: в DATA-кэше нет старого ID', not dc.get('hasOldId'), dc)
        check('A3: total_devices 1291 в DATA-кэше', dc.get('total1291'), dc)

        page.evaluate("navigateTo('kip-ios')")
        page.wait_for_timeout(1200)
        sec = page.evaluate(SECTION_JS)
        check('A5: «КИП ИОС» открылся (страница активна/видима)',
              sec.get('kipActive') and sec.get('kipVisible'), sec)

        page.evaluate("navigateTo('devices-prod')")
        page.wait_for_timeout(1500)
        sec2 = page.evaluate(SECTION_JS)
        check('A6: страница «Приборы по производствам» активна',
              sec2.get('prodActive'), sec2)
        check('A6: список производств отрисован (> 0)',
              sec2.get('prodListLen', 0) > 0, sec2)
        check('A6: инфо-строка не «Загрузка…»',
              'Загрузка' not in (sec2.get('prodInfo') or ''), sec2.get('prodInfo'))

        page.evaluate("devOpenDetail('1')")
        page.wait_for_timeout(800)
        det = page.evaluate(DETAIL_JS)
        check('A7: карточка в десктоп-панели активна/видима',
              det.get('panelActive') and det.get('panelVisible'), det)
        check('A7: заголовок карточки не пуст', bool(det.get('title')), det.get('title'))
        check('A7: строки карточки отрисованы (> 5)', det.get('rows', 0) > 5, det.get('rows'))
        check('A7: строка «Период ремонта» жива (данные ППР)',
              det.get('periodRow') is not None, det.get('periodRow'))

        check('A8: 0 JS-ошибок (тёмная)', len(errs) == 0, errs[:3])
        page.screenshot(path=os.path.join(SHOT_DIR, '01-kip-ios-dark.png'))
        page.evaluate("navigateTo('kip-ios')")
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(SHOT_DIR, '02-device-detail-dark.png'),
                        full_page=False)
        ctx.close()

        # ===== B. Десктоп, светлая (быстрая) =====
        print('B. Десктоп 1280x900, светлая тема')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        errs = attach(page, ctx, 'light', 'B')
        goto_app(page)
        page.evaluate("navigateTo('kip-ios')")
        page.wait_for_timeout(1000)
        page.evaluate("devOpenDetail('1')")
        page.wait_for_timeout(800)
        det = page.evaluate(DETAIL_JS)
        check('B1: карточка в десктоп-панели (светлая)',
              det.get('panelActive') and det.get('rows', 0) > 5, det)
        check('B2: 0 JS-ошибок (светлая)', len(errs) == 0, errs[:3])
        page.screenshot(path=os.path.join(SHOT_DIR, '03-device-detail-light.png'))
        ctx.close()

        # ===== C. Мобильный 375x812, тёмная (быстрая) =====
        print('C. Мобильный 375x812, тёмная тема')
        ctx = browser.new_context(viewport={'width': 375, 'height': 812},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        errs = attach(page, ctx, 'dark', 'C')
        goto_app(page)
        page.evaluate("navigateTo('kip-ios')")
        page.wait_for_timeout(1000)
        sec = page.evaluate(SECTION_JS)
        check('C1: «КИП ИОС» открывается на мобильном',
              sec.get('kipActive') and sec.get('kipVisible'), sec)
        check('C2: 0 JS-ошибок (мобильный)', len(errs) == 0, errs[:3])
        page.screenshot(path=os.path.join(SHOT_DIR, '04-kip-ios-mobile.png'))
        ctx.close()

        browser.close()

    print('\nИтог: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    time.sleep(0.5)
    code = main()
    raise SystemExit(code)
