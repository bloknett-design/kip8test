#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 539 pre-study: скриншоты телефонного справочника — мобайл
# (390px) и десктоп (1440px), тёмная тема, вход по токену через мок
# Apps Script (как task538-browser-check). Цель — увидеть текущую
# раскладку ДО правок: где разделы/содержание на десктопе.

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from playwright.sync_api import sync_playwright

REPO = '/home/z/my-project/kip8test'
SHOT = '/home/z/my-project/download/kip8test-task539'
os.makedirs(SHOT, exist_ok=True)
PORT = 8995


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/exec'):
            body = json.dumps({
                'ok': True,
                'data': {
                    'userId': 'u1', 'email': 'bloknet@bk.ru',
                    'role': 'КИП8', 'name': 'Тест'
                }
            }).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
            return
        p = self.path.split('?')[0]
        if p == '/':
            p = '/index.html'
        fp = os.path.join(REPO, p.lstrip('/'))
        if not os.path.isfile(fp):
            self.send_response(404)
            self.end_headers()
            return
        ext = os.path.splitext(p)[1]
        mime = {'.html': 'text/html', '.js': 'text/javascript',
                '.css': 'text/css', '.json': 'application/json',
                '.png': 'image/png', '.svg': 'image/svg+xml',
                '.webmanifest': 'application/manifest+json'}.get(ext,
                                                                'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.end_headers()
        with open(fp, 'rb') as f:
            self.wfile.write(f.read())

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        self.rfile.read(n)
        body = json.dumps({'ok': False, 'error': 'no_session'}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


srv = HTTPServer(('127.0.0.1', PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for label, w, h in [('mobile', 390, 844), ('desktop', 1440, 900)]:
        ctx = browser.new_context(viewport={'width': w, 'height': h},
                                  is_mobile=(label == 'mobile'),
                                  has_touch=(label == 'mobile'))
        page = ctx.new_page()
        # мок Apps Script
        page.route('**/macros/s/**', lambda route: route.fulfill(
            status=200,
            content_type='application/json',
            body=json.dumps({'ok': True, 'data': {
                'userId': 'u1', 'email': 'bloknet@bk.ru',
                'role': 'КИП8', 'name': 'Тест'}})
        ))
        page.goto(f'http://127.0.0.1:{PORT}/')
        page.evaluate("localStorage.setItem('kip8test_session_token','test-token')")
        page.goto(f'http://127.0.0.1:{PORT}/#phonebook')
        page.wait_for_timeout(2500)
        # дождаться рендера справочника
        try:
            page.wait_for_selector('#pbList .pb-section', timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(800)
        page.screenshot(path=f'{SHOT}/study-{label}-phonebook.png',
                        full_page=False)
        if label == 'desktop':
            # раскрыть первую секцию (клик по заголовку)
            try:
                page.click('#pbList .pb-section-title')
                page.wait_for_timeout(900)
                page.screenshot(path=f'{SHOT}/study-desktop-expanded.png',
                                full_page=False)
            except Exception as e:
                print('expand click fail:', e)
        print(label, 'title:', page.title())
        errs = []
        page.on('pageerror', lambda e: errs.append(str(e)))
        ctx.close()
    browser.close()

srv.shutdown()
print('DONE ->', SHOT)
