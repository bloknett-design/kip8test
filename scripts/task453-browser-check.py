#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 453: browser-check — заявка: «При попытке установки в ручную
# статуса "Выходной, плановый выходной день" появляется сообщение
# "Нельзя очистить авто-запись. Установите статус вручную.", хотя в
# таблице Коды_статусов этот статус есть, и остальные статусы из
# этой таблицы устанавливаются.»
# КОНТЕКСТ (мок-сервер, порт 8974): десктоп 1280 тёмная, Админ:
#   A: приложение + график; ячейка Д8 (авто) Чиркова day-9 видна;
#   B (ЗАЯВКА): клик по авто-ячейке → попап → строка «Выходной,
#      плановый выходной день» (БЕЗ кода-символа, одна) → клик:
#      тост «Выходной поставлен поверх авто-записи…», НЕТ «Нельзя
#      очистить авто-запись», pending {'статус':'.'}, ячейка
#      пустая с рамкой ws-pending, «Сохранить (1)»;
#   C (undo): «Дополнительно…» → «Удалить запись» → правка снята,
#      снова авто Д8, тост «Правка снята — снова авто-запись»;
#   D (шит): select «— выходной —» → «Сохранить» шита → тот же
#      pending '.' (путь расширенной правки);
#   E (сохранение): «Сохранить» тулбара → setManualEntry
#      {'статус':'.', переработка 0, часы null}; после loadGrid
#      ячейка пустая (ручная «.»), «Сохранено записей: 1»;
#   F: ячейка «.» — попап: строка «Выходной» АКТИВНА; шит:
#      «— выходной —» выбран, «Удалить запись» видна, «ручная
#      запись»; полное удаление: «Удаление применено» → Save →
#      deleteEntry → ячейка ПУСТАЯ (без Д8 — запись удалена);
#   G (старый сервер): setManualEntry → unknown_статус «.» →
#      тост-подсказка «обновите WorkSchedule.gs»/«Коды_статусов»;
#   H: зритель (view) — клик открывает ТОЛЬКО окно мероприятий;
#   I: 0 JS-ошибок ×2 контекста; скриншоты download/kip8test-task453/.
import datetime
import json
import os
from urllib.parse import unquote
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

PORT = 8974
TODAY = datetime.date.today()
NOWY = TODAY.year
NOWM = TODAY.month
D = lambda day: '%04d-%02d-%02d' % (NOWY, NOWM, day)
TAB = '0231'          # Чирков В. А., дневной
DAY9 = D(9)           # авто Д8 — целевая ячейка заявки
DAY10 = D(10)         # авто Д8 — сценарий старого сервера
KEY9 = DAY9 + '|' + TAB
KEY10 = DAY10 + '|' + TAB

SHOTS = '/home/z/my-project/download/kip8test-task453'
os.makedirs(SHOTS, exist_ok=True)

EMPLOYEES = [
  {'таб_номер': TAB, 'ФИО': 'Чирков В. А.', 'тип': 'дневной', 'смена': '',
   'шаблон_ротации': 0, 'старт_цикла': '', 'дата_приёма': '2023-05-11',
   'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА 5 разряда', 'группа_допуска': 'IV',
   'комментарий': ''},
]

CODES = [
  {'code': 'Д', 'name': 'День (12-час)', 'color': '#FFE0B2', 'short': 'день 12ч'},
  {'code': 'Д8', 'name': 'День 8-час (7:30–16:30)', 'color': '#FFF9C4',
   'short': 'день 8ч'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1', 'short': 'отпуск'},
  # слот «Выходного» — ПУСТОЙ код, как в листе пользователя
  # (Task 387: точка убрана из листа)
  {'code': '', 'name': 'Выходной, плановый выходной день',
   'color': '#EEF0F2', 'short': 'выходной'},
]

# Стартовые записи: авто Д8 на 9-й и 10-й дни (плановые смены
# дневного персонала после «Сформировать»)
MOCK = {
    'entries': [
        {'дата': DAY9, 'таб_номер': TAB, 'статус': 'Д8',
         'переработка': 0, 'праздник': 0, 'источник': 'авто'},
        {'дата': DAY10, 'таб_номер': TAB, 'статус': 'Д8',
         'переработка': 0, 'праздник': 0, 'источник': 'авто'},
    ],
    'reject_dot': False,   # G: старый сервер без «.»-валидации
    'set_calls': [],       # захваченные setManualEntry payload'ы
    'del_calls': [],       # захваченные deleteEntry payload'ы
}

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
          (('  [' + str(extra)[:250] + ']') if (extra and not ok) else ''))


def api_response(action, body, editor=True):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'calc.view': True, 'library.view': True,
                                'kipios.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': editor,
                                'flowmeter.view': True}}}
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
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': [dict(e) for e in MOCK['entries']]}}
    if action == 'prodCalendar.getMonth':
        return {'ok': True, 'data': {'workdays': 22, 'weekends': 8,
                'shortdays': 0, 'holidays': [], 'transfers': []}}
    # --- мутирующие вызовы (запоминаем + применяем) ---
    if action == 'workSchedule.setManualEntry':
        MOCK['set_calls'].append(dict(body))
        st = String = str(body.get('статус', ''))
        if st == '.' and MOCK['reject_dot']:
            # старый Apps Script: «.» нет в колонке A листа
            return {'ok': False, 'error': 'unknown_статус: .'}
        key = str(body.get('date', '')) + '|' + str(body.get('таб_номер', ''))
        found = None
        for e in MOCK['entries']:
            if e['дата'] + '|' + e['таб_номер'] == key:
                found = e
                break
        rec = {'дата': str(body.get('date', '')),
               'таб_номер': str(body.get('таб_номер', '')),
               'статус': st, 'переработка': int(body.get('переработка') or 0),
               'праздник': 0, 'источник': 'руч',
               'замещает': body.get('замещает') or None,
               'комментарий': body.get('комментарий') or '',
               'часы': body.get('часы') if body.get('часы') else None}
        if found:
            found.update(rec)
        else:
            MOCK['entries'].append(rec)
        return {'ok': True, 'data': {'date': rec['дата'],
                'таб_номер': rec['таб_номер'], 'статус': st}}
    if action == 'workSchedule.deleteEntry':
        MOCK['del_calls'].append(dict(body))
        key = str(body.get('date', '')) + '|' + str(body.get('таб_номер', ''))
        MOCK['entries'] = [e for e in MOCK['entries']
                           if e['дата'] + '|' + e['таб_номер'] != key]
        return {'ok': True, 'data': {'date': body.get('date'),
                'таб_номер': body.get('таб_номер')}}
    return {'ok': True, 'data': {'ok': True}}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length).decode('utf-8', 'replace') \
            if length else ''
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            body = {}
        url = self.path
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        resp = api_response(action, body)
        out = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type',
                         'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def attach(page, ctx, theme, tag, editor=True):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda dlg: dlg.accept())
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t453-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd_ = request.post_data
        body = None
        if pd_:
            try:
                body = json.loads(pd_)
            except Exception:
                body = None
        if body is None:
            body = {}
        resp = api_response(action, body, editor=editor)
        return route.fulfill(status=200,
                             content_type='application/json; charset=utf-8',
                             body=json.dumps(resp, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t453-%s)' % tag)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    return js_errors


CELL9 = "td.ws-cell[onclick*=\"%s\"][onclick*=\"'%s'\"]" % (DAY9, TAB)
CELL10 = "td.ws-cell[onclick*=\"%s\"][onclick*=\"'%s'\"]" % (DAY10, TAB)
VYH_ROW = ".ws-cell-popup .ws-popup-row[onclick*=\"onPopupStatus('')\"]"
MORE_ROW = ".ws-cell-popup .ws-popup-row.ws-popup-more"


def cell_state(page, sel):
    return page.evaluate(
        "(function(){var el=document.querySelector(%s);"
        "if(!el) return null;"
        "return {txt: el.textContent.replace(/\\s+/g,' ').trim(),"
        " pend: el.classList.contains('ws-pending'),"
        " dot: el.classList.contains('ws-dot-code'),"
        " empty: el.classList.contains('ws-status-empty'),"
        " manual: el.classList.contains('ws-source-manual')};})()"
        % json.dumps(sel))


def toasts(page):
    return page.evaluate("window.__toasts || []")


def hook_toasts(page):
    page.evaluate(
        "window.__toasts=[];"
        "KipToast.show=(function(o){return function(m){"
        "window.__toasts.push(String(m)); try{o(m);}catch(e){}};"
        "})(KipToast.show);")


def pending_of(page, key):
    return page.evaluate(
        "(function(){var p=WorkSchedule._PENDING['%s'];"
        "return p?JSON.parse(JSON.stringify(p)):null;})()" % key)


def main():
    srv = HTTPServer(('127.0.0.1', PORT), Handler)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ===== десктоп 1280 тёмная, Админ (edit) =====
        print('=== Контекст: десктоп тёмная — «Выходной» поверх авто ===')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'desktop')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('work-schedule')")
        page.wait_for_timeout(2500)
        hook_toasts(page)

        check('A1: приложение загрузилось, график открыт',
              page.evaluate("(function(){return !!document.querySelector(" +
              "'.ws-grid');})()"))
        st0 = cell_state(page, CELL9)
        check('A2: целевая ячейка — авто Д8 (код виден)', bool(st0) and
              st0['txt'] == 'Д8' and not st0['pend'], st0)

        # ---------- B: ЗАЯВКА — «Выходной» поверх авто ----------
        print('--- B: заявка — ручная установка «Выходного» ---')
        page.click(CELL9)
        page.wait_for_timeout(400)
        check('B1: попап кодов открыт',
              page.evaluate("(function(){var p=document.getElementById(" +
              "'wsCellPopup');return p&&p.classList.contains('active');})()"))
        vyh = page.evaluate(
            "(function(){var rows=document.querySelectorAll(%s);"
            "var r=rows.length?rows[0]:null;"
            "if(!r) return null;"
            "var code=r.querySelector('.ws-popup-code');"
            "return {n: rows.length,"
            " name: r.querySelector('.ws-popup-name').textContent.trim(),"
            " code: code?code.textContent.trim():'',"
            " dot: !!r.querySelector('.ws-swatch-dot')};})()"
            % json.dumps(VYH_ROW))
        check('B2: строка «Выходной, плановый выходной день» — ОДНА',
              bool(vyh) and vyh['n'] == 1, vyh)
        check('B3: без кода-символа, свотч «точки» (канон Task 387)',
              bool(vyh) and vyh['code'] == '' and vyh['dot'], vyh)
        page.click(VYH_ROW)
        page.wait_for_timeout(600)
        t = toasts(page)
        check('B4: тост «Выходной поставлен поверх авто-записи…»',
              any('Выходной поставлен поверх авто-записи' in x for x in t), t)
        check('B5: НЕТ тоста «Нельзя очистить авто-запись»',
              not any('Нельзя очистить авто-запись' in x for x in t), t)
        p = pending_of(page, KEY9)
        check('B6: pending = ручная запись «.» с чистыми полями',
              bool(p) and p.get('статус') == '.' and
              p.get('переработка') == 0 and p.get('замещает') is None and
              p.get('часы') is None and p.get('комментарий') == '', p)
        st1 = cell_state(page, CELL9)
        check('B7: ячейка ПУСТАЯ (Д8 убран) с рамкой несохранённого',
              bool(st1) and st1['txt'] == '' and st1['pend'] and
              st1['dot'] and st1['empty'], st1)
        save = page.evaluate("(function(){var b=document.getElementById(" +
                             "'wsSaveBtn');return b?{h:b.hidden," +
                             "t:b.textContent}:null;})()")
        check('B8: кнопка «Сохранить (1)» видна',
              bool(save) and not save['h'] and save['t'] == 'Сохранить (1)',
              save)
        page.screenshot(path=SHOTS + '/b-vyhodnoy-pending.png')

        # ---------- C: undo — «Удалить запись» снимает правку ----------
        print('--- C: undo — удаление правки поверх авто ---')
        page.click(CELL9)
        page.wait_for_timeout(400)
        page.evaluate("(function(){var m=document.querySelectorAll(\"%s\");"
                      "for(var i=0;i<m.length;i++){"
                      "if(m[i].textContent.indexOf('Дополнительно')!==-1){"
                      "m[i].click();break;}}})()" % MORE_ROW)
        page.wait_for_timeout(700)
        sheet_open = page.evaluate(
            "(function(){var s=document.getElementById('wsCellSheet');"
            "return s&&s.classList.contains('active');})()")
        del_vis = page.evaluate(
            "(function(){var b=document.getElementById('wsCellDelete');"
            "return b&&getComputedStyle(b).display!=='none';})()")
        info = page.evaluate(
            "(function(){return document.getElementById('wsCellInfo')"
            ".textContent;})()")
        check('C1: шит открыт, «Удалить запись» видна (эфф. «руч»)',
              sheet_open and del_vis, {'sheet': sheet_open, 'del': del_vis})
        check('C2: инфо — «ручная запись · НЕ СОХРАНЕНО»',
              'ручная запись' in info and 'НЕ СОХРАНЕНО' in info, info)
        page.click('#wsCellDelete')
        page.wait_for_timeout(500)
        t = toasts(page)
        check('C3: тост «Правка снята — снова авто-запись»',
              any('Правка снята — снова авто-запись' in x for x in t), t)
        check('C4: pending снят', pending_of(page, KEY9) is None)
        st2 = cell_state(page, CELL9)
        check('C5: ячейка вернулась к авто Д8 (без рамки)',
              bool(st2) and st2['txt'] == 'Д8' and not st2['pend'], st2)
        save = page.evaluate("(function(){var b=document.getElementById(" +
                             "'wsSaveBtn');return b?b.hidden:true;})()")
        check('C6: «Сохранить» скрыта (правок нет)', save is True)
        page.screenshot(path=SHOTS + '/c-undo-avto-back.png')

        # ---------- D: шит «Дополнительно…» — тот же фикс ----------
        print('--- D: путь шита — «— выходной —» ---')
        page.click(CELL9)
        page.wait_for_timeout(400)
        page.evaluate("(function(){var m=document.querySelectorAll(\"%s\");"
                      "for(var i=0;i<m.length;i++){"
                      "if(m[i].textContent.indexOf('Дополнительно')!==-1){"
                      "m[i].click();break;}}})()" % MORE_ROW)
        page.wait_for_timeout(700)
        page.select_option('#wsCellStatus', '')
        page.click("button[onclick='WorkSchedule.submitCellForm()']")
        page.wait_for_timeout(500)
        t = toasts(page)
        check('D1: тост «Применено…» (без ошибки авто-записи)',
              any('Применено' in x for x in t) and
              not any('Нельзя очистить авто-запись' in x for x in t), t)
        p = pending_of(page, KEY9)
        check('D2: pending «.» — путь шита даёт ту же запись',
              bool(p) and p.get('статус') == '.', p)

        # ---------- E: сохранение на сервер ----------
        print('--- E: «Сохранить» → setManualEntry «.» ---')
        page.click('#wsSaveBtn')
        page.wait_for_timeout(1800)
        calls = [c for c in MOCK['set_calls']
                 if c.get('статус') == '.' and c.get('date') == DAY9]
        check('E1: setManualEntry вызван со статусом «.»',
              len(calls) == 1, MOCK['set_calls'])
        if calls:
            c = calls[0]
            check('E2: чистые поля (переработка 0, часы null, без замещения)',
                  str(c.get('переработка')) in ('0', 'None') and
                  not c.get('замещает') and not c.get('часы'), c)
        t = toasts(page)
        check('E3: тост «Сохранено записей: 1»',
              any('Сохранено записей: 1' in x for x in t), t)
        st3 = cell_state(page, CELL9)
        check('E4: после сохранения ячейка ПУСТАЯ (ручная «.»), без рамки',
              bool(st3) and st3['txt'] == '' and not st3['pend'] and
              st3['dot'] and st3['manual'], st3)
        check('E5: pending пуст (всё отправлено)',
              pending_of(page, KEY9) is None)
        page.screenshot(path=SHOTS + '/e-saved-dot.png')

        # ---------- F: «.»-ячейка — активность + полное удаление ----------
        print('--- F: запись «.» в попапе/шите + удаление ---')
        page.click(CELL9)
        page.wait_for_timeout(400)
        act = page.evaluate(
            "(function(){var r=document.querySelector(%s);"
            "return r?r.classList.contains('ws-popup-active'):null;})()"
            % json.dumps(VYH_ROW))
        check('F1: в попапе строка «Выходной» АКТИВНА', act is True, act)
        page.evaluate("(function(){var m=document.querySelectorAll(\"%s\");"
                      "for(var i=0;i<m.length;i++){"
                      "if(m[i].textContent.indexOf('Дополнительно')!==-1){"
                      "m[i].click();break;}}})()" % MORE_ROW)
        page.wait_for_timeout(700)
        sel_val = page.evaluate(
            "(function(){return document.getElementById('wsCellInfo')"
            ".textContent + ' | ' + document.getElementById('wsCellStatus')"
            ".selectedOptions[0].text;})()")
        check('F2: шит: «— выходной —» выбран, запись «ручная»',
              'ручная запись' in sel_val and 'выходной' in sel_val.lower(),
              sel_val)
        page.click('#wsCellDelete')
        page.wait_for_timeout(500)
        t = toasts(page)
        check('F3: «Удаление применено…» (ручная «.» удаляется)',
              any('Удаление применено' in x for x in t), t)
        page.click('#wsSaveBtn')
        page.wait_for_timeout(1500)
        deld = [c for c in MOCK['del_calls'] if c.get('date') == DAY9]
        check('E4→F4: deleteEntry вызван для дня 9',
              len(deld) == 1, MOCK['del_calls'])
        st4 = cell_state(page, CELL9)
        check('F5: ячейка ПУСТАЯ без «.»-маркера (запись удалена)',
              bool(st4) and st4['txt'] == '' and not st4['dot'] and
              not st4['pend'], st4)
        page.screenshot(path=SHOTS + '/f-deleted-empty.png')

        # ---------- G: старый сервер отклоняет «.» ----------
        print('--- G: старый сервер — unknown_статус «.» ---')
        MOCK['reject_dot'] = True
        page.click(CELL10)
        page.wait_for_timeout(400)
        page.click(VYH_ROW)
        page.wait_for_timeout(500)
        page.click('#wsSaveBtn')
        page.wait_for_timeout(1500)
        t = toasts(page)
        check('G1: тост-подсказка про WorkSchedule.gs и «Коды_статусов»',
              any('не принят сервером' in x and
                  'WorkSchedule.gs' in x and
                  'Коды_статусов' in x for x in t), t)
        p10 = pending_of(page, KEY10)
        check('G2: правка «.» НЕ потеряна (осталась в pending)',
              bool(p10) and p10.get('статус') == '.', p10)
        page.screenshot(path=SHOTS + '/g-old-server-hint.png')

        check('I1: 0 JS-ошибок (десктоп)', len(js_errors) == 0, js_errors)
        ctx.close()

        # ===== зритель (view без edit) =====
        print('=== Контекст: зритель — окно мероприятий без правки ===')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900})
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'dark', 'viewer', editor=False)
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        page2.evaluate("navigateTo('work-schedule')")
        page2.wait_for_timeout(2500)
        page2.click(CELL9)
        page2.wait_for_timeout(500)
        gates = page2.evaluate(
            "(function(){var e=document.getElementById('wsEventsPopup');"
            "var c=document.getElementById('wsCellPopup');"
            "return {ev: e&&e.classList.contains('active'),"
            " codes: c&&c.classList.contains('active')};})()")
        check('H1: зрителю — ТОЛЬКО окно мероприятий (коды не открыты)',
              gates['ev'] is True and gates['codes'] is False, gates)
        check('I2: 0 JS-ошибок (зритель)', len(js_errors2) == 0, js_errors2)
        page2.screenshot(path=SHOTS + '/h-viewer.png')
        ctx2.close()
        browser.close()

    srv.shutdown()
    print('=' * 60)
    print('БРАУЗЕР TASK 453: %d/%d (порт %d)' % (PASS, PASS + FAIL, PORT))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    os.chdir('/home/z/my-project/kip8test')
    main()
