#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 443: точечная проверка мобильной шторки — не обрезана ли
# строка авто-даты (wsPpeExpiryInfo) и подсказка (ws-vac-form-hint)
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8946
TODAY = datetime.date.today()
TODAY_ISO = '%04d-%02d-%02d' % (TODAY.year, TODAY.month, TODAY.day)

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO,
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряд', 'группа_допуска': 'IV',
   'комментарий': ''},
]


def api_response(action):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'u@t.l', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    return {'ok': True, 'data': {'ok': True}}


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
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={'width': 375, 'height': 812})
            page = ctx.new_page()
            page.on('dialog', lambda d: d.accept())
            ctx.add_init_script(
                "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
                "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
                "localStorage.setItem('kip8test:kip8_session_token','t443m2');" +
                "localStorage.setItem('kip8test:app-theme','dark');")

            def handle(route, request):
                url = request.url
                action = ''
                if 'action=' in url:
                    action = unquote(url.split('action=')[1].split('&')[0])
                return route.fulfill(
                    status=200, content_type='application/json; charset=utf-8',
                    body=json.dumps(api_response(action), ensure_ascii=False))
            ctx.route('**/exec?**', handle)
            ctx.route('**script.google.com/**', handle)
            ctx.route('**raw.githubusercontent.com/**',
                      lambda r: r.fulfill(status=404, body='x'))
            ctx.route('**calendar.legalic.ru/**',
                      lambda r: r.fulfill(status=404, body='x'))

            page.goto('http://localhost:%d/index.html' % PORT)
            page.wait_for_timeout(2500)
            page.evaluate("navigateTo('work-schedule')")
            page.wait_for_timeout(2000)
            page.click('#wsWorkersBtn')
            page.wait_for_timeout(800)
            page.click('button[title="Федосов А. В."]')
            page.wait_for_timeout(800)
            page.click('.ws-emp-addppe')
            page.wait_for_timeout(700)
            page.fill('#wsPpeManufactured', '2025-01-15')
            page.select_option('#wsPpeTerm', '2 года')
            page.wait_for_timeout(400)
            m = page.evaluate("""(function(){
                var out = {};
                var ids = ['wsPpeExpiryInfo', 'wsPpeManufactured', 'wsPpeIssued', 'wsPpeTerm'];
                for (var i = 0; i < ids.length; i++) {
                    var el = document.getElementById(ids[i]);
                    if (!el) continue;
                    var r = el.getBoundingClientRect();
                    out[ids[i]] = {
                        txt: (el.textContent || '').slice(0, 120),
                        left: Math.round(r.left), right: Math.round(r.right),
                        top: Math.round(r.top), bottom: Math.round(r.bottom),
                        w: Math.round(r.width),
                        clipR: r.right > 375, clipL: r.left < 0,
                        overflowX: el.scrollWidth > el.clientWidth + 1
                    };
                }
                var hint = document.querySelector('#wsPpeSheet .ws-vac-form-hint');
                if (hint) {
                    var hr = hint.getBoundingClientRect();
                    out['hint'] = { clipR: hr.right > 375,
                                    overflowX: hint.scrollWidth > hint.clientWidth + 1,
                                    right: Math.round(hr.right) };
                }
                return out;
            })()""")
            print(json.dumps(m, ensure_ascii=False, indent=1))
            browser.close()
    finally:
        server.shutdown()
