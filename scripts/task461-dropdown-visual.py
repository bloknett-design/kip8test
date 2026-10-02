#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 461: попытка визуально раскрыть нативный datalist в headless
# Chromium (заполнить «ка» + ArrowDown) — если панель не рендерится
# (известное ограничение headless), подтверждаем программно.
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8956
TODAY_ISO = '2026-10-02'

EMPLOYEES = [
  {'таб_номер': '0871', 'ФИО': 'Федосов А. В.', 'тип': 'сменный', 'смена': 1,
   'шаблон_ротации': 1, 'старт_цикла': TODAY_ISO, 'дата_приёма': '2024-03-15',
   'дата_увольнения': '', 'в_архиве': 0, 'должность': 'Слесарь КИПиА',
   'группа_допуска': 'IV', 'комментарий': ''},
]
CODES = [
  {'code': 'Д8', 'name': 'День 8-час', 'color': '#FFF9C4', 'short': 'день'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2', 'short': 'выходной'},
]
PPE = [
  {'id': 11, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Каска защитная',
   'дата_выдачи': '2026-08-17', 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': '2028-08-17', 'примечание': ''},
  {'id': 12, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Каска защитная',
   'дата_выдачи': '2026-06-01', 'дата_изготовления': '',
   'срок_годности': '2 года', 'дата_окончания': '2028-06-01', 'примечание': ''},
  {'id': 13, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Ботинки',
   'дата_выдачи': '2026-02-11', 'дата_изготовления': '',
   'срок_годности': '1 год', 'дата_окончания': '2027-02-11', 'примечание': ''},
  {'id': 14, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Каска защитная',
   'дата_выдачи': '2025-03-10', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
  {'id': 15, 'таб_номер': '0871', 'работник': 'Федосов А. В.',
   'должность': 'Слесарь КИПиА', 'наименование': 'Очки закрытые',
   'дата_выдачи': '2026-04-14', 'дата_изготовления': '',
   'срок_годности': 'До износа', 'дата_окончания': 'До износа',
   'примечание': ''},
]


def api_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'u@t.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': []}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': [], 'instrList': [],
                                     'instrAll': [], 'eventsAll': []}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': [dict(r) for r in PPE]}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': []}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}" +
            "catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t461d');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            url = request.url
            action = ''
            if 'action=' in url:
                action = unquote(url.split('action=')[1].split('&')[0])
            pd_ = request.post_data
            body = {}
            if pd_:
                try:
                    body = json.loads(pd_)
                except Exception:
                    body = {}
            return route.fulfill(status=200,
                content_type='application/json; charset=utf-8',
                body=json.dumps(api_response(action, body),
                                ensure_ascii=False))
        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**',
                  lambda r: r.fulfill(status=404, body='x'))
        ctx.route('**calendar.legalic.ru/**',
                  lambda r: r.fulfill(status=404, body='x'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        page.click('#wsWorkersBtn')
        page.wait_for_timeout(900)
        page.click('button[title="Федосов А. В."]')
        page.wait_for_timeout(900)
        page.click('.ws-emp-addppe')
        page.wait_for_timeout(900)
        # программная проверка: options в DOM
        vals = page.evaluate("""(function(){
            var dl = document.getElementById('wsPpeNameList');
            var o = dl ? dl.querySelectorAll('option') : [];
            var v = [];
            for (var i=0;i<o.length;i++) v.push(o[i].value);
            return v;
        })()""")
        print('datalist options:', vals)
        # попытка раскрыть нативную панель: клик по полю + ввод + стрелки
        page.click('#wsPpeName')
        page.fill('#wsPpeName', 'Кас')
        page.keyboard.press('ArrowDown')
        page.wait_for_timeout(900)
        page.screenshot(
            path='/home/z/my-project/download/kip8test-task461/'
                 '07-datalist-dropdown-arrow.png')
        print('JS errors:', errors)
        browser.close()


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
        main()
    finally:
        server.shutdown()
