#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 506: пересъёмка ДЕСКТОП-скриншотов предпросмотра с высоким
# вьюпортом 1280×2000 — в кадр попадают НЕСКОЛЬКО страниц A4
# (в 720px помещалась только первая; функциональность уже
# подтверждена browser-check 46/46 — это кадр для VLM).
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8983
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download',
                        'kip8test-task506')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


COLUMNS = [
    {'key': 'designation', 'label': 'Обозначение кабеля, провода',
     'type': 'text'},
    {'key': 'start', 'label': 'Начало трассы', 'type': 'text'},
    {'key': 'end', 'label': 'Конец трассы', 'type': 'text'},
    {'key': 'section', 'label': 'Участок трассы кабеля, провода',
     'type': 'text'},
    {'key': 'mark_project', 'label': 'Марка (по проекту)', 'type': 'text'},
    {'key': 'cores_project',
     'label': 'Число и сечение жил (по проекту)', 'type': 'text'},
    {'key': 'length_project', 'label': 'Длина, м (по проекту)',
     'type': 'number'},
    {'key': 'mark_actual', 'label': 'Марка (проложен)', 'type': 'text'},
    {'key': 'cores_actual',
     'label': 'Число и сечение жил (проложен)', 'type': 'text'},
    {'key': 'length_actual', 'label': 'Длина, м (проложен)',
     'type': 'number'},
    {'key': 'added_at', 'label': 'Дата добавления', 'type': 'text'},
    {'key': 'department', 'label': 'Отделение, производство',
     'type': 'text'},
    {'key': 'purpose', 'label': 'Назначение кабеля', 'type': 'text'},
    {'key': 'project_no', 'label': '№ проекта', 'type': 'text'},
]

ROWS = []
for i in range(1, 31):
    dep = ['Водоподготовка', 'МДИ', 'КИП и А', 'Склад'][i % 4]
    ROWS.append({
        '_row': i + 1, 'num': i,
        'designation': '%d/%d' % (i, i % 9 + 1) if i > 3 else
                       ['1/7', '2/1', '5/2'][i - 1],
        'start': 'ЩК-4, ШУ-%d' % (i % 7 + 1),
        'end': 'КС-%d, отм. %d,0 м., оси %d-%d/А-Б' %
               (i % 4 + 1, i % 18, i % 10 + 1, i % 10 + 2),
        'section': ['по коробу', 'по лотку', 'фальшпол', 'труба'][i % 4],
        'mark_project': 'КВБбШЭнг-LS', 'cores_project': '%dх1' % (i % 20 + 2),
        'length_project': (i * 7) % 180 + 5,
        'mark_actual': 'КВБбШЭнг-LS', 'cores_actual': '%dх1' % (i % 20 + 2),
        'length_actual': (i * 7) % 180 + 5,
        'department': dep, 'purpose': 'Контрольный',
        'project_no': 'АН-603', 'added_at': 'Нет данных'})


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'u@t.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                                     'permissions': {}}}
    if action == 'cableJournal.getColumns':
        return {'ok': True, 'data': {'columns': COLUMNS, 'canEdit': True}}
    if action == 'cableJournal.list':
        return {'ok': True, 'data': {'rows': ROWS, 'total': len(ROWS),
                                     'canEdit': True}}
    return {'ok': True, 'data': {'ok': True}}


def setup_routes(ctx):
    def handle(route, request):
        action = ''
        if 'action=' in request.url:
            action = unquote(request.url.split('action=')[1].split('&')[0])
        body = {}
        if request.post_data:
            try:
                body = json.loads(request.post_data)
            except Exception:
                body = {}
        return route.fulfill(status=200,
            content_type='application/json; charset=utf-8',
            body=json.dumps(mock_response(action, body), ensure_ascii=False))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
        status=404, content_type='text/plain', body='nf'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
        status=404, content_type='text/plain', body='nf'))
    ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
        status=404, content_type='text/plain', body='nf'))


def seed_ls(theme):
    return ("try{localStorage.clear()}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t506');" +
            "localStorage.setItem('kip8test:app-theme','" + theme + "');")


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for theme, name in [('dark', 'a1-page-seam.png'),
                            ('light', 'b1-page-seam.png')]:
            ctx = browser.new_context(viewport={'width': 1280,
                                                'height': 940})
            ctx.add_init_script(seed_ls(theme))
            setup_routes(ctx)
            page = ctx.new_page()
            page.goto('http://localhost:%d/index.html' % PORT)
            page.wait_for_timeout(2500)
            page.evaluate("navigateTo('cable-journal-edit')")
            page.wait_for_timeout(1800)
            page.click('#cjPrintBtn')
            page.wait_for_timeout(1500)
            pages = page.evaluate(
                "() => document.querySelectorAll("
                "'#cjPrintPrevModal iframe').length && "
                "(document.querySelector('#cjPrintPrevModal .wspprev-frame')"
                ".contentDocument.querySelectorAll('.cjpr-page').length)")
            print('%s: страниц в предпросмотре = %s' % (theme, pages))
            # прокрутка к СТЫКУ страниц: низ стр.1 + промежуток +
            # верх стр.2 (шапка повторяется)
            page.evaluate(
                "() => { const b = document.querySelector("
                "'#cjPrintPrevModal .wspprev-body');"
                " b.scrollTop = 700; }")
            page.wait_for_timeout(300)
            page.screenshot(
                path=os.path.join(SHOT_DIR, name), full_page=False)
            ctx.close()
        browser.close()
    print('OK — переснято в 1280×2000')


if __name__ == '__main__':
    main()
