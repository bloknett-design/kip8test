#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Точная геометрия примыкания рамки LCD к краям бара (дробные px)
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8998
REPO = '/home/z/my-project/kip8test'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for theme, w in [('dark', 1024), ('light', 1280), ('dark', 1280)]:
            ctx = browser.new_context(viewport={'width': w, 'height': 700},
                                      device_scale_factor=1.0)
            ctx.add_init_script(
                "try{localStorage.clear()}catch(e){};" +
                "localStorage.setItem('kip8test:kip8_session_token','bc-t530');" +
                "localStorage.setItem('kip8test:app-theme','" + theme + "');")
            def handle(route, request):
                action = ''
                if 'action=' in request.url:
                    action = unquote(request.url.split('action=')[1].split('&')[0])
                route.fulfill(status=200, content_type='application/json',
                              body=json.dumps({'ok': True, 'data': {'ok': True}}))
            ctx.route('**/exec?**', handle)
            ctx.route('**script.google.com/**', handle)
            page = ctx.new_page()
            page.on('dialog', lambda dg: dg.accept())
            page.goto('http://127.0.0.1:%d/index.html' % PORT)
            page.wait_for_timeout(900)
            page.evaluate("navigateTo('work-schedule')")
            page.wait_for_timeout(1400)
            r = page.evaluate(r"""(() => {
                const wrap = document.getElementById('wsLcdWrap');
                const btn = document.getElementById('wsLcdClock');
                const header = document.querySelector(
                    '#page-work-schedule .page-inline-header');
                const hb = header.getBoundingClientRect();
                const wb = wrap.getBoundingClientRect();
                const bb = btn.getBoundingClientRect();
                const cs = getComputedStyle(header);
                return {
                    headerTop: hb.top, headerBottom: hb.bottom, headerH: hb.height,
                    headerBorderBottom: cs.borderBottomWidth,
                    wrapTop: wb.top, wrapBottom: wb.bottom, wrapH: wb.height,
                    btnTop: bb.top, btnBottom: bb.bottom, btnH: bb.height,
                    gapTop: wb.top - hb.top,
                    gapBottom: hb.bottom - wb.bottom,
                    btnInsideTop: bb.top - wb.top,
                    btnInsideBottom: wb.bottom - bb.bottom,
                    right: wb.right, pageW: window.innerWidth};})""")
            print('%s %dpx: %s' % (theme, w, json.dumps(r, ensure_ascii=False)))
            ctx.close()
        browser.close()
        server.shutdown()

if __name__ == '__main__':
    main()
