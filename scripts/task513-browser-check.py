#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 513 — браузерная проверка (Playwright; паттерн task505/506/508).

Заявка: «Проверь код приложения на наличие ошибок и мёртвого кода» +
«Подтверждаю уборку» — после удаления ~419 строк мёртвого кода из
index.html (25 функций + 4 метода) и 443 строк из 7 .gs-файлов.

Проверяется (приложение ДОЛЖНО работать как прежде):
  A) десктоп тёмная: загрузка БЕЗ JS-ошибок (pageerror); дашборд;
     страницы, чьи «остатки» удалены — приборы/арматура/регуляторы/
     замки/проекты/журнал кабелей (карточки из мока) — рендерятся;
  B) РЕГРЕССИЯ OTP (setupOtpInputs-IIFE восстановлен после находки,
     что IIFE самовыполняется): экран входа → шаг 2 → ввод цифры в
     otp1 ПЕРЕВОДИТ фокус на otp2; Backspace на пустом поле
     возвращает фокус; paste «123456» заполняет все 6 полей;
  C) светлая мобильная: загрузка без ошибок.
"""
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

REPO = '/home/z/my-project/kip8test'
PORT = 8995
SHOT_DIR = '/home/z/my-project/download/kip8test-task513'
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0


def check(name, ok, extra=''):
    global PASS, FAIL
    mark = 'OK ' if ok else 'FAIL'
    print('  [%s] %s%s' % (mark, name,
                           (' — %s' % (extra,))[:160] if extra and not ok else ''))
    if ok:
        PASS += 1
    else:
        FAIL += 1


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception:
        pass


# ---------------- мок Apps Script ----------------
COLUMNS = [
    {'key': 'num', 'label': '№ п/п', 'type': 'number', 'readOnly': True},
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
    {'key': 'added_at', 'label': 'Дата добавления', 'type': 'date',
     'readOnly': True},
    {'key': 'department', 'label': 'Отделение, производство',
     'type': 'text'},
    {'key': 'purpose', 'label': 'Назначение кабеля', 'type': 'text'},
    {'key': 'project_no', 'label': '№ проекта', 'type': 'text'},
    # Task 508 — колонки архива (readOnly, сервер пишет)
    {'key': 'last_editor', 'label': 'Последний редактор', 'type': 'text',
     'readOnly': True},
    {'key': 'edited_at', 'label': 'Дата правки', 'type': 'date',
     'readOnly': True},
    {'key': 'archived', 'label': 'Архив', 'type': 'text',
     'readOnly': True},
    {'key': 'archived_by', 'label': 'Кем удалён', 'type': 'text',
     'readOnly': True},
    {'key': 'archived_at', 'label': 'Дата удаления', 'type': 'date',
     'readOnly': True},
]

EDITOR_A = 'Петров Пётр Петрович'
EDITOR_B = 'Тестов Тест Тестович'
EDITOR_C = 'Админов Админ Админович'


def _row(rw, num, des, dep, editor, edited, arch=None):
    r = {'_row': rw, 'num': num, 'designation': des,
         'start': 'ЩК-4, ШУ-%d' % (num % 7 + 1),
         'end': 'КС-%d, отм. %d,0 м.' % (num % 4 + 1, num % 18),
         'section': ['по коробу', 'по лотку', 'фальшпол'][num % 3],
         'mark_project': 'КВБбШЭнг-LS', 'cores_project': '%dх1' % (num + 10),
         'length_project': num * 11, 'mark_actual': 'КВБбШЭнг-LS',
         'cores_actual': '%dх1' % (num + 10), 'length_actual': num * 11,
         'department': dep, 'purpose': 'Контрольный', 'project_no': 'АН-603',
         'added_at': 'Нет данных', 'last_editor': editor,
         'edited_at': edited}
    if arch:
        r['_archived'] = True
        r['archived'] = 'Удалён'
        r['archived_by'] = arch
        r['archived_at'] = '2026-10-%02dT09:30:00.000Z' % (10 + num % 3)
    return r


# 6 записей, ПОРЯДОК ПЕРЕМЕШАН (не № п/п): активные №1/№3/№4/№6,
# архивные №2 («Удалён», Тестов) и №5 («Удалён», Админов)
ROWS = [
    _row(2, 1, '1/7', 'Водоподготовка', EDITOR_A, '2026-10-10T06:00:00'),
    _row(5, 3, '5/2', 'Отделение №2', EDITOR_B, '2026-10-11T06:00:00'),
    _row(3, 2, '2/1', 'Водоподготовка', EDITOR_A, '2026-10-09T06:00:00',
         arch=EDITOR_B),
    _row(6, 4, '4/3', 'МДИ', EDITOR_C, '2026-10-12T06:00:00'),
    _row(7, 5, '5/4', 'МДИ', EDITOR_B, '2026-10-08T06:00:00', arch=EDITOR_C),
    _row(8, 6, '6/5', 'Склад', EDITOR_A, '2026-10-07T06:00:00'),
]


MOCK_HITS = []


def mock_response(action, body):
    MOCK_HITS.append(action)
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1,
                                     'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                                     'permissions': {}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'sendOTP':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'verifyOTP':
        return {'ok': True, 'data': {'ok': True, 'token': 'bc-t513',
                                     'userId': 1, 'role': 'Админ'}}
    if action == 'cableJournal.getColumns':
        return {'ok': True, 'data': {'columns': [
            {'key': 'num', 'label': '№ п/п', 'type': 'number', 'readOnly': True},
            {'key': 'designation', 'label': 'Обозначение', 'type': 'text'},
        ], 'canEdit': True}}
    if action == 'cableJournal.list':
        return {'ok': True, 'data': {'rows': ROWS, 'total': len(ROWS),
                                     'archivedTotal': 0, 'canEdit': True}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def setup_routes(ctx, errors):
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


def attach_error_watch(page, errors, label):
    page.on('pageerror', lambda e: errors.append('%s: pageerror %s' % (label, str(e)[:150])))
    page.on('console', lambda m: errors.append('%s: console.error %s'
             % (label, m.text[:150])) if m.type == 'error' else None)


def seed_ls(theme):
    # с токеном — bootstrap зовёт getCurrentUser (мок «Админ»),
    # страницы приборов/арматуры/журнала доступны по ролям
    return ("try{localStorage.clear()}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t513');" +
            "localStorage.setItem('kip8test:app-theme','" + theme + "');")


OTP_JS = r"""(() => {
    const vis = (el) => el && el.offsetParent !== null;
    return {
        login: document.getElementById('loginScreen').classList.contains('active'),
        step2: document.getElementById('authStep2').classList.contains('active'),
        focus: document.activeElement ? document.activeElement.id : '',
        vals: ['otp1','otp2','otp3','otp4','otp5','otp6'].map(
            id => (document.getElementById(id) || {}).value || ''),
        filled: ['otp1','otp2','otp3','otp4','otp5','otp6'].filter(
            id => document.getElementById(id).classList.contains('filled')).length
    };})"""


def run():
    server = HTTPServer(('127.0.0.1', PORT),
                        lambda *a, **kw: QuietHandler(*a, directory=REPO, **kw))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d/index.html' % PORT

    with sync_playwright() as pw:
        browser = pw.chromium.launch()

        # ---------- A: десктоп, тёмная ----------
        print('A. Десктоп (тёмная тема)')
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        errors = []
        setup_routes(ctx, errors)
        page = ctx.new_page()
        attach_error_watch(page, errors, 'desktop')
        page.goto(base)
        page.add_init_script(seed_ls('dark'))
        page.goto(base)
        page.wait_for_timeout(1200)
        check('загрузка без pageerror', not [e for e in errors if 'pageerror' in e],
              '; '.join(errors[:3]))
        check('сайдбар и тема', page.evaluate(
            "() => document.getElementById('sidebar') !== null && "
            "document.documentElement.getAttribute('data-theme') === 'dark'"))
        shot(page, 'a1-dashboard-dark.png')

        for pg in ('devices', 'valves-prod', 'regulators-prod',
                   'lockouts-prod', 'projects-prod', 'calculators'):
            page.evaluate("navigateTo('%s')" % pg)
            page.wait_for_timeout(350)
            active = page.evaluate(
                "pg => document.getElementById('page-' + pg) && "
                "document.getElementById('page-' + pg).classList.contains('active')", pg)
            check('страница %s активна' % pg, active)
        shot(page, 'a2-valves.png')

        page.evaluate("navigateTo('cable-journal-edit')")
        page.wait_for_timeout(1200)
        cards = page.evaluate(
            "() => document.querySelectorAll('#cjList .cj-item').length")
        # мок task508: 6 строк, 4 активные + 2 архивные «Удалён»
        # (архив не попадает в список — Task 508)
        check('журнал кабелей: 4 активные карточки из мока', cards == 4,
              'карточек %s' % cards)
        shot(page, 'a3-cable-journal.png')
        check('после навигации ошибок JS нет', not [e for e in errors if 'pageerror' in e],
              '; '.join(errors[:3]))

        # ---------- B: OTP-регрессия (IIFE восстановлен) ----------
        print('B. OTP-регрессия (setupOtpInputs-IIFE)')
        MOCK_HITS.clear()
        page.evaluate("KipAuth._showLoginScreen()")
        page.wait_for_timeout(400)
        st = page.evaluate(OTP_JS)
        check('экран входа открыт (шаг 1)', st['login'] and not st['step2'],
              str(st)[:120])
        # Enter в поле email — тоже проводка IIFE (sendOTP)
        page.fill('#authEmail', 'user@test.local')
        page.press('#authEmail', 'Enter')
        page.wait_for_timeout(500)
        check('Enter в email → sendOTP (мок)', 'sendOTP' in MOCK_HITS)
        st = page.evaluate(OTP_JS)
        check('шаг 2 (OTP-поля) виден', st['step2'], str(st)[:120])
        shot(page, 'b1-otp-step2.png')

        page.focus('#otp1')
        page.keyboard.type('5', delay=60)
        page.wait_for_timeout(120)
        st = page.evaluate(OTP_JS)
        check('ввод в otp1 → фокус на otp2', st['focus'] == 'otp2',
              'фокус %s' % st['focus'])
        check('otp1 заполнен и помечен', st['vals'][0] == '5' and st['filled'] == 1,
              str(st))

        page.keyboard.press('Backspace')   # otp2 пуст → фокус вернётся на otp1
        page.keyboard.press('Backspace')   # сотрёт «5» из otp1
        page.wait_for_timeout(120)
        st = page.evaluate(OTP_JS)
        check('Backspace на пустом otp2 → фокус otp1', st['focus'] == 'otp1',
              'фокус %s' % st['focus'])

        # paste «123456» в otp1: IIFE распределяет по 6 полям
        page.evaluate("""() => {
            const inp = document.getElementById('otp1');
            inp.focus();
            const dt = new DataTransfer();
            dt.setData('text', '123456');
            inp.dispatchEvent(new ClipboardEvent('paste', {
                clipboardData: dt, bubbles: true, cancelable: true}));
        }""")
        page.wait_for_timeout(150)
        st = page.evaluate(OTP_JS)
        check('paste «123456» заполнил все 6 полей',
              ''.join(st['vals']) == '123456' and st['filled'] == 6, str(st))
        page.wait_for_timeout(600)   # автопроверка последнего поля (200мс) + ответ
        check('автопроверка после 6-й цифры (verifyOTP в моке)',
              'verifyOTP' in MOCK_HITS)
        shot(page, 'b2-otp-filled.png')
        page.evaluate("KipAuth.cancelLogin ? KipAuth.cancelLogin() : null")
        page.wait_for_timeout(200)
        check('после OTP-сценария ошибок JS нет',
              not [e for e in errors if 'pageerror' in e], '; '.join(errors[:3]))

        # ---------- C: мобильная светлая ----------
        print('C. Мобильная (светлая тема)')
        mctx = browser.new_context(viewport={'width': 390, 'height': 844},
                                   is_mobile=True, has_touch=True)
        merr = []
        setup_routes(mctx, merr)
        mpage = mctx.new_page()
        attach_error_watch(mpage, merr, 'mobile')
        mpage.goto(base)
        mpage.add_init_script(seed_ls('light'))
        mpage.goto(base)
        mpage.wait_for_timeout(1200)
        check('мобильная загрузка без pageerror',
              not [e for e in merr if 'pageerror' in e], '; '.join(merr[:3]))
        check('светлая тема', mpage.evaluate(
            "() => document.documentElement.getAttribute('data-theme') === 'light'"))
        shot(mpage, 'c1-mobile-light.png')

        browser.close()
    server.shutdown()
    print()
    print('ИТОГО: %d OK / %d FAIL' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(run())
