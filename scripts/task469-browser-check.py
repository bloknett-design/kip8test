#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 469: browser-check — описание раздела «Плановые мероприятия»
# ПЕРЕПИСАНО по заявке: вводный абзац «Периодические работы на
# участке КИП ИОС, выполняемые в начале и в конце каждого месяца.»,
# «Хранение отметок» сокращён («отметки записываются в архив.»),
# пункт «Мобильная версия» удалён (5 → 4 пункта функционала).
# Заявка: «Перепиши описание раздела на "Периодические работы на
# участке КИП ИОС, выполняемые в начале и в конце каждого месяца.
# Функционал: Отметка выполнения…, Хранение отметок…, Правка
# отметки…, Обновление…"».
# ПРОВЕРКИ (мок-сервер, порт 8999):
#   A: широкий вьюпорт 1600 — раскладка Task 468 жива (таблица
#      слева по контенту, окно описания справа до правого края);
#   B: содержание окна — точный текст лида из заявки, 4 пункта
#      (отметка/хранение/правка/обновление), старые фрагменты
#      («Мероприятия_КИП_ИОС», «Пример таблицы…», «Мобильная
#      версия») в тексте окна ОТСУТСТВУЮТ;
#   C: узкий вьюпорт 1100 (< 1200) — описание ПОД таблицей;
#   D: мобильный 375 — Task 464 жив: полоса месяца, один столбец,
#      описание под таблицей; 0 JS-ошибок во всех сценариях.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        '..', 'download', 'kip8test-task469')


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True, 'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'planEvents.list':
        return {'ok': True, 'data': {'marks': []}}
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
          (('  [' + str(extra)[:260] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


# Геометрия раскладки + содержание окна
def layout_geom(page):
    return page.evaluate("""(() => {
        const lay = document.querySelector('#page-plan-events .pe-layout');
        if (!lay) return {open: false};
        const card = lay.querySelector('.pe-card');
        const desc = lay.querySelector('.pe-desc-card');
        const table = lay.querySelector('.pe-table');
        const wrap = lay.querySelector('.pe-grid-wrap');
        const lr = lay.getBoundingClientRect();
        const cr = card ? card.getBoundingClientRect() : null;
        const dr = desc ? desc.getBoundingClientRect() : null;
        const tr = table ? table.getBoundingClientRect() : null;
        const ls = getComputedStyle(lay);
        const names = [...lay.querySelectorAll('td.pe-name')];
        const maxNameH = names.reduce((m, td) => Math.max(m, td.getBoundingClientRect().height), 0);
        const title = desc ? desc.querySelector('.pe-desc-title') : null;
        const sub = desc ? desc.querySelector('.pe-desc-sub') : null;
        const lead = desc ? desc.querySelector('.pe-desc-lead') : null;
        const items = desc ? [...desc.querySelectorAll('.pe-desc-list li')]
                           .map(li => li.textContent.trim()) : [];
        return {open: true, dir: ls.flexDirection,
                layL: +lr.left.toFixed(1), layR: +lr.right.toFixed(1),
                layW: +lr.width.toFixed(1),
                cardL: cr ? +cr.left.toFixed(1) : null,
                cardR: cr ? +cr.right.toFixed(1) : null,
                cardW: cr ? +cr.width.toFixed(1) : null,
                cardH: cr ? +cr.height.toFixed(1) : null,
                descL: dr ? +dr.left.toFixed(1) : null,
                descR: dr ? +dr.right.toFixed(1) : null,
                descW: dr ? +dr.width.toFixed(1) : null,
                descT: dr ? +dr.top.toFixed(1) : null,
                descB: dr ? +dr.bottom.toFixed(1) : null,
                tabW: tr ? +tr.width.toFixed(1) : null,
                tabScrollW: wrap ? wrap.scrollWidth : null,
                tabClientW: wrap ? wrap.clientWidth : null,
                maxNameH: +maxNameH.toFixed(1),
                nameWS: table.querySelector('td.pe-name')
                        ? getComputedStyle(table.querySelector('td.pe-name')).whiteSpace : '',
                title: title ? title.textContent.trim() : '',
                sub: sub ? sub.textContent.trim() : '',
                lead: lead ? lead.textContent.trim() : '',
                items: items,
                docW: document.documentElement.scrollWidth,
                winW: window.innerWidth};})()""")


def open_section(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('plan-events')")
    page.wait_for_timeout(1200)


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t469');" +
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

        # ===== A: широкий вьюпорт 1600 — раскладка Task 468 жива
        print('== A: 1600px — раскладка Task 468 жива (таблица влево, окно справа) ==')
        open_section(page)
        g = layout_geom(page)
        check('раздел открыт, .pe-layout/.pe-card/.pe-desc-card на месте',
              g.get('open') and g.get('cardL') is not None and g.get('descL') is not None, g)
        check('flex-строка на широком экране (row)',
              g.get('dir') == 'row', g)
        check('карточка таблицы прижата ВЛЕВО экрана (±2px)',
              g.get('cardL') is not None and abs(g['cardL'] - g['layL']) <= 2, g)
        check('окно описания СПРАВА от карточки (desc.left >= card.right)',
              g.get('descL') is not None and g['descL'] >= g['cardR'] - 1, g)
        check('карточка обнимает таблицу (cardW - tableW <= 3, БЕЗ растяжения)',
              g.get('cardW') is not None and g.get('tabW') is not None and
              g['cardW'] - g['tabW'] <= 3, g)
        check('правый край окна описания == правому краю раскладки (±2)',
              g.get('descR') is not None and abs(g['descR'] - g['layR']) <= 2, g)
        check('наименования в одну строку (nowrap, maxNameH <= 40)',
              g.get('maxNameH') is not None and g['maxNameH'] <= 40, g)
        check('таблица без горизонтального скролла (scroll <= client + 2)',
              g.get('tabScrollW') is not None and
              g['tabScrollW'] <= g['tabClientW'] + 2, g)
        check('нет горизонтального переполнения страницы',
              g.get('docW') is not None and g['docW'] <= g['winW'] + 1, g)
        shot(page, 'a-desktop-1600.png')

        # ===== B: содержание окна — переписанный текст
        print('== B: окно «Описание раздела» — переписанное содержание ==')
        check('заголовок «Описание раздела»', g.get('title') == 'Описание раздела', g)
        check('вводный абзац — точный текст заявки',
              g.get('lead') == 'Периодические работы на участке КИП ИОС, '
              'выполняемые в начале и в конце каждого месяца.', g.get('lead'))
        check('подзаголовок «Функционал»', g.get('sub') == 'Функционал', g)
        check('ровно ЧЕТЫРЕ пункта функционала (было 5)',
              isinstance(g.get('items'), list) and len(g['items']) == 4,
              [i[:40] for i in (g.get('items') or [])])
        items = g.get('items') or []
        check('пункт 1 «Отметка выполнения» — текст заявки дословно',
              len(items) > 0 and items[0] == 'Отметка выполнения — клик по ячейке '
              'месяца открывает диалог «Отметка выполнения»: укажите дату '
              '(по умолчанию — сегодняшняя) и нажмите «Подтвердить» — в ячейке '
              'появится зелёная галочка.', items[0] if items else None)
        check('пункт 2 «Хранение отметок» — сокращённый текст заявки',
              len(items) > 1 and items[1] == 'Хранение отметок — отметки '
              'записываются в архив.', items[1] if len(items) > 1 else None)
        check('пункт 3 «Правка отметки» — текст заявки дословно',
              len(items) > 2 and items[2] == 'Правка отметки — клик по отмеченной '
              'ячейке открывает диалог «Изменение отметки»: можно сохранить '
              'новую дату или удалить отметку.', items[2] if len(items) > 2 else None)
        check('пункт 4 «Обновление» — текст заявки дословно',
              len(items) > 3 and items[3] == 'Обновление — кнопка «Обновить» '
              'в шапке страницы перезагружает отметки с сервера.',
              items[3] if len(items) > 3 else None)
        txt = ' '.join(items) + ' ' + (g.get('lead') or '')
        for word in ['Мобильная версия', 'Пример таблицы мероприятий',
                     'Мероприятия_КИП_ИОС', 'лист «Архив»',
                     'периодические работы предприятия']:
            check('старый фрагмент убран: «%s»' % word,
                  word not in txt, txt[:120])

        # ===== C: узкий вьюпорт 1100 (< 1200) — описание ПОД таблицей
        print('== C: 1100px (< 1200) — раскладка в колонку ==')
        page.set_viewport_size({'width': 1100, 'height': 900})
        page.wait_for_timeout(500)
        g = layout_geom(page)
        check('раскладка сложилась в колонку (column)',
              g.get('dir') == 'column', g)
        below = page.evaluate("""(() => {
            const lay = document.querySelector('#page-plan-events .pe-layout');
            const card = lay.querySelector('.pe-card');
            const desc = lay.querySelector('.pe-desc-card');
            return desc.getBoundingClientRect().top >= card.getBoundingClientRect().bottom - 1;})()""")
        check('описание ПОД таблицей (desc.top >= card.bottom)', below, g)
        check('окно описания на всю ширину раскладки (±2)',
              g.get('descW') is not None and abs(g['descW'] - g['layW']) <= 2, g)
        check('переписанный лид виден и в колонке',
              g.get('lead') == 'Периодические работы на участке КИП ИОС, '
              'выполняемые в начале и в конце каждого месяца.', g.get('lead'))
        shot(page, 'c-narrow-1100.png')

        # ===== D: мобильный 375 — Task 464 жив
        print('== D: 375px — мобильный вид Task 464 не тронут ==')
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(500)
        m = page.evaluate("""(() => {
            const bar = document.querySelector('#page-plan-events .pe-month-bar');
            const wrap = document.querySelector('#page-plan-events .pe-grid-wrap');
            const table = document.querySelector('#page-plan-events .pe-table');
            const lay = document.querySelector('#page-plan-events .pe-layout');
            const card = lay.querySelector('.pe-card');
            const desc = lay.querySelector('.pe-desc-card');
            const lead = desc.querySelector('.pe-desc-lead');
            const visMonths = [...table.querySelectorAll('td.pe-m')]
                .filter(td => getComputedStyle(td).display !== 'none'
                    && td.getBoundingClientRect().width > 0
                    && td.parentElement.getBoundingClientRect().width > 0).length;
            const monthsSel = document.getElementById('peMonthSel');
            return {barVisible: bar ? getComputedStyle(bar).display !== 'none' : false,
                    tableW: +table.getBoundingClientRect().width.toFixed(1),
                    wrapW: +wrap.getBoundingClientRect().width.toFixed(1),
                    nameWS: getComputedStyle(table.querySelector('td.pe-name')).whiteSpace,
                    visMonths: visMonths,
                    selOptions: monthsSel ? monthsSel.options.length : 0,
                    descBelow: desc.getBoundingClientRect().top >=
                               card.getBoundingClientRect().bottom - 1,
                    lead: lead ? lead.textContent.trim() : '',
                    docW: document.documentElement.scrollWidth,
                    winW: window.innerWidth};})()""")
        check('полоса выбора месяца видна (Task 464)',
              m.get('barVisible'), m)
        check('селектор месяца заполнен (12 опций)',
              m.get('selOptions') == 12, m)
        check('таблица на всю ширину обёртки (±2, Task 464 width: 100%)',
              abs(m.get('tableW', 0) - m.get('wrapW', 1)) <= 2, m)
        check('наименования ПЕРЕНОСЯТСЯ на мобайле (normal)',
              m.get('nameWS') == 'normal', m)
        check('видимые ячейки месяцев: только выбранный месяц (8 строк × 1)',
              m.get('visMonths') == 8, m)
        check('описание ПОД таблицей и на мобайле',
              m.get('descBelow'), m)
        check('переписанный лид виден и на мобайле',
              m.get('lead') == 'Периодические работы на участке КИП ИОС, '
              'выполняемые в начале и в конце каждого месяца.', m.get('lead'))
        check('нет горизонтального переполнения страницы',
              m.get('docW') <= m.get('winW') + 1, m)
        shot(page, 'd-mobile-375.png')

        # ===== светлая тема окна описания (визуальный артефакт)
        page.set_viewport_size({'width': 1600, 'height': 1000})
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(400)
        shot(page, 'e-light-1600.png')
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(200)

        browser.close()
        server.shutdown()

    print('\nИТОГ: %d OK / %d FAIL' % (PASS, FAIL))
    if js_errors:
        print('JS-ОШИБКИ (%d):' % len(js_errors))
        for e in js_errors[:10]:
            print('  ! ' + e[:300])
    else:
        print('JS-ошибок нет (0)')
    raise SystemExit(1 if (FAIL or js_errors) else 0)


if __name__ == '__main__':
    main()
