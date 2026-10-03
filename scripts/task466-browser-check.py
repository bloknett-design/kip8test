#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 466: browser-check — значки окна мероприятий ПОМЕНЯНЫ
# МЕСТАМИ: [печать (27px)][раскрытие (в самом углу)].
# Заявка: «В окне мероприятий поменяй местами значки раскрытия
# окна и печати мероприятий.»
# КОНТЕКСТ (мок-сервер, порт 8999):
#   A: геометрия — окно мероприятий: ПАРА
#      [печать(28px)][раскрытие(3px)], 22×22, зазор 3;
#      окно норм: ОДИН значок раскрытия в 3px (не тронуто);
#      плашки 52/26;
#   B: клик по печати (теперь ЛЕВЫЙ значок) → диалог
#      wsEventsPrevModal открывается, кнопки/лист/инжект на месте;
#   C: клик по раскрытию (теперь в углу) → окно раскрывается
#      (класс ws-bar-open), повторный клик — сворачивается;
#   D: закрытие диалога (Esc) — инжект снят; 0 JS-ошибок.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]

SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'download', 'kip8test-task466')

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
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
ENTRIES = [
  {'id': 1, 'дата': d(-6), 'таб_номер': '017', 'статус': 'Д', 'источник': 'авто'},
]
TRAININGS = [
  {'id': 80, 'тема': 'Повторный инструктаж по охране труда', 'тип': 'инструктаж',
   'дата_начала': d(-12), 'дата_окончания': d(-12), 'таб_номер': '017', 'подразделение': ''},
  {'id': 81, 'тема': 'Обучение по новой редакции инструкций', 'тип': 'обучение',
   'дата_начала': d(-9), 'дата_окончания': d(-7), 'таб_номер': '018', 'подразделение': ''},
  {'id': 82, 'тема': 'Целевой инструктаж при допуске к работам повышенной опасности',
   'тип': 'инструктаж', 'дата_начала': d(-1), 'дата_окончания': d(1),
   'таб_номер': '023', 'подразделение': ''},
  {'id': 83, 'тема': 'Проверка знаний в объёме должностных обязанностей',
   'тип': 'проверка_знаний', 'дата_начала': d(2), 'дата_окончания': d(3),
   'таб_номер': '017', 'подразделение': ''},
]
PPE = [
  {'id': 1, 'таб_номер': '017', 'наименование': 'Каска защитная',
   'дата_выдачи': d(-100), 'дата_окончания': d(4), 'состояние': ''},
]


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
        if body and body.get('month') == M:
            return {'ok': True, 'data': {'entries': ENTRIES}}
        return {'ok': True, 'data': {'entries': []}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8, 'shortdays': 0,
                'holidays': [], 'transfers': []}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


PASS = 0
FAIL = 0


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:220] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def geom(page, idp):
    return page.evaluate("""((id) => {
        const el = document.getElementById(id);
        if (!el) return null;
        const er = el.getBoundingClientRect();
        const btn = el.querySelector('.ws-bar-exp');
        const prn = el.querySelector('.ws-bar-print');
        const br = btn ? btn.getBoundingClientRect() : null;
        const pr = prn ? prn.getBoundingClientRect() : null;
        return {
            hasBtn: !!btn, hasPrint: !!prn,
            btnTop: br ? +(br.top - er.top).toFixed(2) : null,
            btnRight: br ? +(er.right - br.right).toFixed(2) : null,
            btnW: br ? +br.width.toFixed(1) : null,
            btnH: br ? +br.height.toFixed(1) : null,
            prnTop: pr ? +(pr.top - er.top).toFixed(2) : null,
            prnRight: pr ? +(er.right - pr.right).toFixed(2) : null,
            prnW: pr ? +pr.width.toFixed(1) : null,
            prnH: pr ? +pr.height.toFixed(1) : null,
            gap: (br && pr) ? +(br.left - pr.right).toFixed(2) : null,
            expBefore: (br && pr) ? pr.right < br.left : null
        };})""", idp)


def main():
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t466');" +
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
            resp = mock_response(action, body)
            return route.fulfill(status=200,
                                 content_type='application/json; charset=utf-8',
                                 body=json.dumps(resp, ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(1600)

        print('== A: геометрия — значки ПОМЕНЯНЫ МЕСТАМИ ==')
        ev = geom(page, 'wsEventsPanel')
        cal = geom(page, 'wsCalPanel')
        check('окно мероприятий: пара значков (раскрытие + печать)',
              ev and ev['hasBtn'] and ev['hasPrint'], ev)
        check('РАСКРЫТИЕ — в самом углу: 3px сверху и справа',
              ev and ev['btnTop'] == 3 and ev['btnRight'] == 3, ev)
        check('ПЕЧАТЬ — сдвинута ВЛЕВО: 3px сверху, 28px справа',
              ev and ev['prnTop'] == 3 and ev['prnRight'] == 28, ev)
        check('печать СЛЕВА от раскрытия (expBefore)',
              ev and ev['expBefore'] is True, ev)
        check('обе кнопки 22×22 (размеры не менялись)',
              ev and ev['btnW'] == 22 and ev['btnH'] == 22 and
              ev['prnW'] == 22 and ev['prnH'] == 22, ev)
        check('зазор между значками 3px',
              ev and ev['gap'] == 3, ev)
        check('окно норм: ОДИН значок (печати нет, не тронуто)',
              cal and cal['hasBtn'] and not cal['hasPrint'], cal)
        check('окно норм: 3px сверху и справа',
              cal and cal['btnTop'] == 3 and cal['btnRight'] == 3, cal)
        caps = page.evaluate("""(() => {
            const a = document.querySelector('#wsEventsPanel .ws-ep-cap');
            const b = document.querySelector('#wsCalPanel .ws-cp-cap');
            return {ev: a ? getComputedStyle(a).paddingRight : null,
                    cal: b ? getComputedStyle(b).paddingRight : null};})()""")
        check('плашки-заголовки не прячутся: 52px/26px',
              caps['ev'] == '52px' and caps['cal'] == '26px', caps)
        shot(page, 'a-swapped-icons.png')

        print('== B: клик по печати (ЛЕВЫЙ значок) — диалог ==')
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(1100)
        st = page.evaluate("""(() => {
            const ov = document.getElementById('wsEventsPrevModal');
            if (!ov) return {open: false};
            const t = ov.querySelector('.wspprev-title');
            const s = ov.querySelector('.wspprev-sub');
            const btns = [...ov.querySelectorAll('.wspprev-btn')].map(b => b.textContent.trim());
            const sheet = document.getElementById('wsPrintSheet');
            return {open: true,
                    title: t ? t.textContent.trim() : '',
                    sub: s ? s.textContent.trim() : '',
                    btns: btns,
                    sheetClass: sheet ? sheet.className : null,
                    inj: !!document.getElementById('wsEventsPrintStyle')};})()""")
        check('диалог открыт (wsEventsPrevModal)', st['open'], st)
        check('заголовок «Предпросмотр печати»', st['title'] == 'Предпросмотр печати', st)
        check('кнопки: Печать / Сохранить PDF / Сохранить Excel / Отмена',
              st['btns'] == ['Печать', 'Сохранить PDF', 'Сохранить Excel', 'Отмена'], st)
        check('лист #wsPrintSheet.wsev-sheet + инжект книжной @page',
              st['sheetClass'] == 'wsev-sheet' and st['inj'], st)
        shot(page, 'b-dialog-from-left-icon.png')

        print('== C: раскрытие (теперь в углу) работает ==')
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        page.click('#wsEventsPanel .ws-bar-exp')
        page.wait_for_timeout(600)
        opened = page.evaluate("""(() => {
            const el = document.getElementById('wsEventsPanel');
            return {open: el.classList.contains('ws-bar-open'),
                    h: el.getBoundingClientRect().height};})()""")
        check('клик по раскрытию — окно раскрылось (ws-bar-open)',
              opened['open'] and opened['h'] > 100, opened)
        shot(page, 'c-expanded-from-corner.png')
        page.click('#wsEventsPanel .ws-bar-exp')
        page.wait_for_timeout(600)

        print('== D: закрытие диалога, чистота ==')
        page.click('#wsEventsPanel .ws-bar-print')
        page.wait_for_timeout(800)
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        st2 = page.evaluate("""(() => ({
            dlg: !!document.getElementById('wsEventsPrevModal'),
            inj: !!document.getElementById('wsEventsPrintStyle')}))()""")
        check('Esc: диалог закрыт, инжект снят',
              (not st2['dlg']) and (not st2['inj']), st2)
        check('0 JS-ошибок на странице', len(js_errors) == 0, js_errors)

        browser.close()
    server.shutdown()
    print('\nИТОГ Task 466 browser-check: %d OK / %d FAIL' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
