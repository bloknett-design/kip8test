#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 467: диагностика — почему при сужении вьюпорта k остаётся 1.
import datetime, json, threading, os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import calendar

PORT = 8998
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]

def d(off):
    dd = max(1, min(DIM, TODAY.day + off))
    return '%04d-%02d-%02d' % (Y, M, dd)

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE082'},
  {'code': 'Н', 'name': 'Ночь (12-час)', 'color': '#B0BEC5'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
ENTRIES = [{'id': 1, 'дата': d(-6), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'}]
TRAININGS = [
  {'id': 80, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-12), 'дата_окончания': d(-12), 'таб_номер': '017', 'подразделение': ''},
]
PPE = []

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': PPE}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES if body and body.get('month') == M else []}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def probe(page, tag):
    r = page.evaluate("""(() => {
        const ov = document.getElementById('wsEventsPrevModal');
        if (!ov) return {open: false};
        const dlg = ov.querySelector('.wspprev-dialog');
        const body = ov.querySelector('.wspprev-body');
        const paper = ov.querySelector('.wspprev-paper');
        const frame = ov.querySelector('.wspprev-frame');
        const dr = dlg.getBoundingClientRect();
        const br = body.getBoundingClientRect();
        const pr = paper.getBoundingClientRect();
        return {open: true, vw: window.innerWidth,
                dlgW: +dr.width.toFixed(1), bodyCW: body.clientWidth,
                paperW: +pr.width.toFixed(1), paperL: +pr.left.toFixed(1),
                tr: frame.style.transform || '(none)',
                sw: getComputedStyle(frame).width};})()""")
    print(tag, json.dumps(r, ensure_ascii=False))

def main():
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = ctx.new_page()
        page.on('dialog', lambda dlg: dlg.accept())
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','probe467');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        def handle(route, request):
            url = request.url
            action = ''
            if 'action=' in url:
                action = unquote(url.split('action=')[1].split('&')[0])
            body = {}
            if request.post_data:
                try: body = json.loads(request.post_data)
                except Exception: body = {}
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                                 body=json.dumps(mock_response(action, body), ensure_ascii=False))
        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1500)
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(1200)
        probe(page, 'A@1600:')
        page.set_viewport_size({'width': 800, 'height': 700})
        page.wait_for_timeout(900)
        probe(page, 'B@800: ')
        # принудительный вызов fit
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        page.wait_for_timeout(300)
        probe(page, 'C@800+resize-dispatch:')
        browser.close()
    server.shutdown()

if __name__ == '__main__':
    main()
