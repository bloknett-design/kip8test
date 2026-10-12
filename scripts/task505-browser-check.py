#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 505: browser-check — заявка:
#   «В разделе "Кабельный журнал" добавь кнопку печати, компактную
#    со значком принтера, и с диалоговым окном предпросмотра и
#    сохранения в PDF или Excel, по примеру как в разделе "Табель
#    учёта рабочего времени".»
# Проверяется страница #page-cable-journal-edit (мок Apps Script:
# cableJournal.getColumns + cableJournal.list):
#   A) ДЕСКТОП 1280x720, тёмная: кнопка #cjPrintBtn — компактная
#      32×32 со значком принтера, видна, левее поиска; клик →
#      диалог #cjPrintPrevModal (wspprev-*) с iframe-предпросмотром
#      (таблица журнала, шапка «По проекту»/«Проложен», строки
#      отделений), кнопки «Печать»/«Сохранить PDF»/«Сохранить
#      Excel»/«Отмена» + «A4 · альбомная»; СКАЧИВАНИЕ PDF
#      (Кабельный_журнал_*.pdf, >1 КБ, %PDF-магия) и Excel
#      (*.xlsx, PK-магия) + тосты; Esc закрывает (со снятием
#      инжект-стиля); фильтр поиска — подзаголовок «из N»;
#      0 JS-ошибок;
#   B) ДЕСКТОП, светлая: кнопка и диалог на месте (computed-цвета);
#   C) МОБАЙЛ 375x812, тёмная: кнопка в шапке, диалог на весь
#      экран (media 640px), контент предпросмотра жив;
#   D) скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8985
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task505')
os.makedirs(SHOT_DIR, exist_ok=True)

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
          (('  [' + str(extra)[:300] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=True)
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


# ---- мок данных кабельного журнала (структура как в cables.json) ----
COLUMNS = [
    {'key': 'designation', 'label': 'Обозначение кабеля, провода', 'type': 'text'},
    {'key': 'start', 'label': 'Начало трассы', 'type': 'text'},
    {'key': 'end', 'label': 'Конец трассы', 'type': 'text'},
    {'key': 'section', 'label': 'Участок трассы кабеля, провода', 'type': 'text'},
    {'key': 'mark_project', 'label': 'Марка (по проекту)', 'type': 'text'},
    {'key': 'cores_project', 'label': 'Число и сечение жил (по проекту)', 'type': 'text'},
    {'key': 'length_project', 'label': 'Длина, м (по проекту)', 'type': 'number'},
    {'key': 'mark_actual', 'label': 'Марка (проложен)', 'type': 'text'},
    {'key': 'cores_actual', 'label': 'Число и сечение жил (проложен)', 'type': 'text'},
    {'key': 'length_actual', 'label': 'Длина, м (проложен)', 'type': 'number'},
    {'key': 'added_at', 'label': 'Дата добавления', 'type': 'text'},
    {'key': 'department', 'label': 'Отделение, производство', 'type': 'text'},
    {'key': 'purpose', 'label': 'Назначение кабеля', 'type': 'text'},
    {'key': 'project_no', 'label': '№ проекта', 'type': 'text'},
]

ROWS = [
    {'_row': 2, 'num': 1, 'designation': '1/7', 'start': 'ЩК-4, ШУ-1',
     'end': 'ЭЩ №4', 'section': 'по коробу',
     'mark_project': 'КВБбШЭнг-LS', 'cores_project': '14х1',
     'length_project': 60, 'mark_actual': 'КВБбШЭнг-LS',
     'cores_actual': '19х1', 'length_actual': 90,
     'department': 'Водоподготовка', 'purpose': 'Контрольный',
     'project_no': 'АН-603', 'added_at': 'Нет данных'},
    {'_row': 3, 'num': 2, 'designation': '2/1', 'start': 'ЩК-4, ШУ-1',
     'end': 'КС-1, отм. 0,0 м., оси 1-2/А-Б', 'section': 'по коробу',
     'mark_project': 'КВБбШЭнг-LS', 'cores_project': '27х1',
     'length_project': 43, 'mark_actual': 'КВБбШЭнг-LS',
     'cores_actual': '27х1', 'length_actual': 43.5,
     'department': 'Водоподготовка', 'purpose': 'Контрольный',
     'project_no': 'АН-603', 'added_at': 'Нет данных'},
    {'_row': 5, 'num': 3, 'designation': '5/2', 'start': 'ЩСУ-2',
     'end': 'Н-1', 'section': 'по лотку',
     'mark_project': 'КГ', 'cores_project': '3х2,5',
     'length_project': 12, 'mark_actual': 'КГ', 'cores_actual': '3х2,5',
     'length_actual': 12, 'department': 'Отделение №2',
     'purpose': 'Силовой', 'project_no': 'АН-603', 'added_at': 'Нет данных'},
]


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'cableJournal.getColumns':
        return {'ok': True, 'data': {'columns': COLUMNS, 'canEdit': True}}
    if action == 'cableJournal.list':
        return {'ok': True, 'data': {'rows': ROWS, 'total': len(ROWS),
                                     'canEdit': True}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t505');" +
            "localStorage.setItem('kip8test:app-theme','" + theme + "');")


# состояние страницы для проверок (в осн. документе)
STATE_JS = r"""(() => {
    const btn = document.getElementById('cjPrintBtn');
    const dlg = document.getElementById('cjPrintPrevModal');
    const st = document.getElementById('cjPrintStyle');
    const out = {
        btnExists: !!btn,
        btnVisible: !!btn && btn.offsetParent !== null,
        btnW: btn ? btn.getBoundingClientRect().width : 0,
        btnH: btn ? btn.getBoundingClientRect().height : 0,
        dlg: !!dlg,
        styleInjected: !!st,
        cards: document.querySelectorAll('#cjList .cj-item').length,
        groups: document.querySelectorAll('#cjList .cj-group').length
    };
    if (dlg) {
        const f = dlg.querySelector('.wspprev-frame');
        out.frame = !!f;
        out.sub = (dlg.querySelector('.wspprev-sub') || {}).textContent || '';
        out.hint = (dlg.querySelector('.wspprev-hint') || {}).textContent || '';
        out.btns = [...dlg.querySelectorAll('.wspprev-btn')].map(
            b => b.textContent.trim());
    }
    return out;})"""


# содержимое iframe предпросмотра
FRAME_JS = r"""(() => {
    const f = document.querySelector('#cjPrintPrevModal .wspprev-frame');
    if (!f) return {missing: true};
    try {
        const d = f.contentDocument;
        if (!d) return {noDoc: true};
        const sheet = d.getElementById('wsPrintSheet');
        return {
            title: (d.querySelector('.cjpr-title') || {}).textContent || '',
            sub: (d.querySelector('.cjpr-sub') || {}).textContent || '',
            thRows: d.querySelectorAll('.cjpr-table thead tr').length,
            rowspan: d.querySelectorAll('.cjpr-table th[rowspan="2"]').length,
            colspan: d.querySelectorAll('.cjpr-table th[colspan="3"]').length,
            grpRows: d.querySelectorAll('tr.cjpr-grp').length,
            dataRows: d.querySelectorAll('tr.cjpr-odd, tr.cjpr-even').length,
            firstDes: ((d.querySelector('tr.cjpr-odd td.cjpr-c-des') || {})
                       .textContent || ''),
            landscape: (d.documentElement.innerHTML
                        .indexOf('A4 landscape') !== -1)
        };
    } catch (e) { return {err: String(e)}; }})"""


def collect_errors(page, errors):
    page.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))
    page.on('console', lambda m: errors.append('console: ' + m.text)
            if m.type == 'error' else None)


def open_cj(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('cable-journal-edit')")
    page.wait_for_timeout(1800)


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ======== A. ДЕСКТОП, тёмная тема ========
        print('A) ДЕСКТОП 1280x720, тёмная — кнопка + диалог + выгрузки')
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720},
                                  accept_downloads=True)
        ctx.add_init_script(seed_ls('dark'))
        setup_routes(ctx)
        page = ctx.new_page()
        errors = []
        collect_errors(page, errors)
        open_cj(page)

        st = page.evaluate(STATE_JS)
        check('список журнала отрисован (3 карточки, 2 группы)',
              st['cards'] == 3 and st['groups'] == 2, st)
        check('кнопка #cjPrintBtn существует и видна',
              st['btnExists'] and st['btnVisible'])
        check('кнопка компактная 32×32',
              abs(st['btnW'] - 32) < 1.5 and abs(st['btnH'] - 32) < 1.5,
              (st['btnW'], st['btnH']))
        # значок принтера: svg с path внутри кнопки
        has_prn = page.evaluate(
            "() => !!document.querySelector('#cjPrintBtn svg path')")
        check('значок принтера (svg path) в кнопке', has_prn)
        shot(page, 'a1-page.png')

        # клик → диалог
        page.click('#cjPrintBtn')
        page.wait_for_timeout(900)
        st = page.evaluate(STATE_JS)
        check('диалог #cjPrintPrevModal открыт (wspprev-*)', st['dlg'])
        check('инжект-стиль cjPrintStyle в <head>', st['styleInjected'])
        check('кнопки диалога: Печать/PDF/Excel/Отмена',
              st.get('btns') == ['Печать', 'Сохранить PDF',
                                 'Сохранить Excel', 'Отмена'], st.get('btns'))
        check('подсказка «A4 · альбомная»', 'альбомная' in st.get('hint', ''))
        check('подзаголовок диалога с составом',
              'отделений: 2' in st.get('sub', '') and
              'записей: 3' in st.get('sub', ''), st.get('sub'))
        fr = page.evaluate(FRAME_JS)
        check('iframe: заголовок «Кабельный журнал» (капс)',
              fr.get('title', '').replace(' ', '').upper() ==
              'КАБЕЛЬНЫЙЖУРНАЛ', fr)
        check('iframe: двухуровневая шапка (2 строки, rowspan 6 / colspan 2)',
              fr.get('thRows') == 2 and fr.get('rowspan') == 6 and
              fr.get('colspan') == 2, fr)
        check('iframe: 2 строки отделений + 3 строки данных',
              fr.get('grpRows') == 2 and fr.get('dataRows') == 3, fr)
        check('iframe: обозначение первой строки (1/7)',
              fr.get('firstDes') == '1/7', fr)
        check('iframe: альбомная @page', fr.get('landscape'))
        shot(page, 'a2-dialog.png')

        # выгрузка PDF
        try:
            with page.expect_download(timeout=30000) as dl:
                page.click('#cjPrintPrevModal .wspprev-pdf')
            d = dl.value
            path = d.path()
            size = os.path.getsize(path)
            with open(path, 'rb') as f:
                magic = f.read(4)
            check('PDF скачан: имя + магия %PDF + размер',
                  d.suggested_filename.startswith('Кабельный_журнал_') and
                  d.suggested_filename.endswith('.pdf') and
                  magic == b'%PDF' and size > 1024,
                  (d.suggested_filename, magic, size))
        except Exception as e:
            check('PDF скачан', False, str(e)[:200])
        page.wait_for_timeout(600)
        toast_pdf = page.evaluate(
            "() => (document.querySelector('.toast, #toast, .kip-toast') || "
            "{}).textContent || ''")
        # выгрузка Excel
        try:
            with page.expect_download(timeout=30000) as dl:
                page.click('#cjPrintPrevModal .wspprev-xlsx')
            d = dl.value
            path = d.path()
            size = os.path.getsize(path)
            with open(path, 'rb') as f:
                magic = f.read(2)
            check('Excel скачан: имя + PK-магия + размер',
                  d.suggested_filename.startswith('Кабельный_журнал_') and
                  d.suggested_filename.endswith('.xlsx') and
                  magic == b'PK' and size > 1024,
                  (d.suggested_filename, magic, size))
        except Exception as e:
            check('Excel скачан', False, str(e)[:200])
        page.wait_for_timeout(600)

        # фильтр: «из N» в подзаголовке (печатается отфильтрованное)
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        page.evaluate("() => { const i = document.getElementById('cjSearchInput');"
                      " i.value = 'Водоподготовка';"
                      " KipCableJournal._applyClientSearch(); }")
        page.wait_for_timeout(400)
        page.click('#cjPrintBtn')
        page.wait_for_timeout(900)
        st = page.evaluate(STATE_JS)
        check('фильтр: подзаголовок «записей: 2 из 3»',
              'записей: 2 из 3' in st.get('sub', ''), st.get('sub'))
        fr = page.evaluate(FRAME_JS)
        check('фильтр: в предпросмотре 2 записи одного отделения',
              fr.get('grpRows') == 1 and fr.get('dataRows') == 2, fr)
        shot(page, 'a3-filtered.png')

        # Esc закрывает + снимает стиль
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        st = page.evaluate(STATE_JS)
        check('Esc закрыл диалог и снял инжект-стиль',
              not st['dlg'] and not st['styleInjected'], st)

        check('0 JS-ошибок (тёмная, все шаги)', len(errors) == 0,
              errors[:4])
        ctx.close()

        # ======== B. ДЕСКТОП, светлая тема ========
        print('B) ДЕСКТОП, светлая — кнопка и диалог')
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 720})
        ctx2.add_init_script(seed_ls('light'))
        setup_routes(ctx2)
        page2 = ctx2.new_page()
        errors2 = []
        collect_errors(page2, errors2)
        open_cj(page2)
        st2 = page.evaluate if False else page2.evaluate(STATE_JS)
        check('светлая: кнопка видна, компактная',
              st2['btnExists'] and st2['btnVisible'] and
              abs(st2['btnW'] - 32) < 1.5, st2)
        col = page2.evaluate(
            "() => getComputedStyle(document.getElementById('cjPrintBtn')).color")
        check('светлая: цвет кнопки тёмный (не белый-на-белом)',
              col not in ('rgb(255, 255, 255)',), col)
        page2.click('#cjPrintBtn')
        page2.wait_for_timeout(900)
        st2 = page2.evaluate(STATE_JS)
        check('светлая: диалог открыт с предпросмотром', st2['dlg'])
        fr2 = page2.evaluate(FRAME_JS)
        check('светлая: таблица в iframe отрисована',
              fr2.get('dataRows') == 3, fr2)
        shot(page2, 'b1-light-dialog.png')
        page2.keyboard.press('Escape')
        page2.wait_for_timeout(300)
        check('0 JS-ошибок (светлая)', len(errors2) == 0, errors2[:4])
        ctx2.close()

        # ======== C. МОБАЙЛ 375x812, тёмная ========
        print('C) МОБАЙЛ 375x812, тёмная — кнопка + диалог на весь экран')
        ctx3 = browser.new_context(viewport={'width': 375, 'height': 812},
                                   device_scale_factor=2,
                                   accept_downloads=True)
        ctx3.add_init_script(seed_ls('dark'))
        setup_routes(ctx3)
        page3 = ctx3.new_page()
        errors3 = []
        collect_errors(page3, errors3)
        open_cj(page3)
        st3 = page3.evaluate(STATE_JS)
        check('мобайл: кнопка в шапке видна, 32×32',
              st3['btnExists'] and st3['btnVisible'] and
              abs(st3['btnW'] - 32) < 1.5, st3)
        page3.click('#cjPrintBtn')
        page3.wait_for_timeout(900)
        mst = page3.evaluate(
            r"""(() => {
                const dlg = document.querySelector('#cjPrintPrevModal .wspprev-dialog');
                if (!dlg) return {dlg: false};
                const r = dlg.getBoundingClientRect();
                return {dlg: true, w: r.width, h: r.height,
                        vw: window.innerWidth, vh: window.innerHeight};})()""")
        check('мобайл: диалог на весь экран (100vw × 100dvh)',
              mst.get('dlg') and abs(mst['w'] - 375) < 2 and
              mst['h'] >= 700, mst)
        fr3 = page3.evaluate(FRAME_JS)
        check('мобайл: предпросмотр жив (таблица)',
              fr3.get('dataRows') == 3, fr3)
        shot(page3, 'c1-mobile-dialog.png')
        # выгрузка на мобайле тоже работает
        try:
            with page3.expect_download(timeout=30000) as dl:
                page3.click('#cjPrintPrevModal .wspprev-pdf')
            d = dl.value
            check('мобайл: PDF скачивается',
                  d.suggested_filename.endswith('.pdf'),
                  d.suggested_filename)
        except Exception as e:
            check('мобайл: PDF скачивается', False, str(e)[:200])
        check('0 JS-ошибок (мобайл)', len(errors3) == 0, errors3[:4])
        ctx3.close()

        browser.close()

    server.shutdown()
    print()
    print('ИТОГ: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
