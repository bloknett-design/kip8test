#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 525 browser-check: Библиотека/Электробезопасность — на кнопке
# инструкции СО 153-34.03.603-2003 дополнительная строка статуса
# «Отменена — приказ Минэнерго России от 01.12.2023 № 1105»
# (заявка: «…укажи дополнительную информацию о том, что данная
# инструкция отменена, с названием документа отмены.»):
#  A) ДЕСКТОП тёмная: navigateTo('library-electro') → кнопка СО 153:
#     label + sublabel + строка отмены; цвет вычислен #ef5350;
#     .menu-btn-cancelled на странице РОВНО ОДИН; соседи (ПУЭ,
#     ПТЭЭП, ПОТЭЭ, Дополнительно) — БЕЗ строки; href Google Drive
#     прежний; порядок детей label → sublabel → cancelled;
#  B) ДЕСКТОП светлая: цвет строки #c62828 (канон Task 520);
#  C) МОБАЙЛ тёмная (390×844): строка читаема, не обрезана
#     (scrollWidth ≤ clientWidth + 1), цвет жив;
#  D) 0 JS-ошибок; скриншоты в download/kip8test-task525/.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task525')
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
          (('  [' + str(extra)[:240] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'library.view': True,
                                'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


# Снимок кнопки СО 153 и общих инвариантов страницы
STATE_JS = """(() => {
    const cancelled = document.querySelectorAll('.menu-btn-cancelled');
    const anchors = Array.from(document.querySelectorAll('#page-library-electro a.menu-btn'));
    const so = anchors.find(a => a.textContent.indexOf('СО 153-34.03.603-2003') !== -1);
    const out = {nCancelled: cancelled.length, soExists: !!so};
    if (so) {
        const label = so.querySelector('.menu-btn-label');
        const sub = so.querySelector('.menu-btn-sublabel');
        const c = so.querySelector('.menu-btn-cancelled');
        out.soHref = so.getAttribute('href');
        out.label = label ? label.textContent : '';
        out.sub = sub ? sub.textContent : '';
        out.cancelledText = c ? c.textContent.trim() : '';
        out.cancelledVisible = !!(c && c.offsetParent !== null);
        if (c) {
            const cs = getComputedStyle(c);
            out.color = cs.color;
            out.fontSize = cs.fontSize;
            out.fontWeight = cs.fontWeight;
            out.notClipped = c.scrollWidth <= c.clientWidth + 1;
        }
        out.order = [label, sub, so.querySelector('.menu-btn-cancelled')]
            .filter(Boolean).map(el => Array.prototype.indexOf.call(
                el.parentNode.children, el));
    }
    out.nAnchors = anchors.length;
    out.neighbours = anchors.map(a => {
        const l = a.querySelector('.menu-btn-label');
        return {label: l ? l.textContent : '',
                hasCancelled: !!a.querySelector('.menu-btn-cancelled')};
    });
    return out;})()"""


def page_state(page):
    return page.evaluate(STATE_JS)


def open_page(ctx, browser, theme, viewport):
    page = ctx.new_page()
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('library-electro')")
    page.wait_for_timeout(1200)
    return page


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        errors_all = []

        # ---------- A: десктоп, тёмная тема ----------
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors_all.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t525');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

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
                body=json.dumps(mock_response(action, body)))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        page = open_page(ctx, browser, 'dark', {'width': 1280, 'height': 720})
        st = page_state(page)

        print('A. Десктоп, тёмная тема:')
        check('страница Электробезопасность открыта (кнопки в разделе)',
              st['nAnchors'] >= 4, st)
        check('кнопка СО 153-34.03.603-2003 в DOM', st['soExists'])
        check('label прежний', st.get('label') == 'Инструкция СО 153-34.03.603-2003',
              st.get('label'))
        check('sublabel прежний (средства защиты)',
              st.get('sub', '').startswith('Применение и испытание средств защиты'),
              st.get('sub'))
        check('строка отмены — точный текст',
              st.get('cancelledText') ==
              'Отменена — приказ Минэнерго России от 01.12.2023 № 1105',
              st.get('cancelledText'))
        check('строка отмены ВИДИМА (не display:none)',
              st.get('cancelledVisible') is True)
        check('цвет тёмной темы — #ef5350 (rgb(239, 83, 80))',
              st.get('color') == 'rgb(239, 83, 80)', st.get('color'))
        check('полужирная (600)', st.get('fontWeight') == '600', st.get('fontWeight'))
        check('кегль 13px', st.get('fontSize') == '13px', st.get('fontSize'))
        check('.menu-btn-cancelled на странице РОВНО ОДИН',
              st['nCancelled'] == 1, st['nCancelled'])
        check('href Google Drive сохранён',
              st.get('soHref') ==
              'https://drive.google.com/file/d/1Q8kne-DyfxkkPZp0uxROAm6BC9rPZeq4/view',
              st.get('soHref'))
        check('порядок детей: label → sublabel → cancelled',
              st.get('order') == [0, 1, 2], st.get('order'))
        neigh = {n['label']: n['hasCancelled'] for n in st.get('neighbours', [])}
        check('ПУЭ 6 и 7 — без строки отмены', neigh.get('ПУЭ 6 и 7') is False, neigh)
        check('ПТЭЭП 2003 — без строки отмены', neigh.get('ПТЭЭП 2003') is False, neigh)
        check('ПОТЭЭ 2022 — без строки отмены', neigh.get('ПОТЭЭ 2022') is False, neigh)
        check('Дополнительно — без строки отмены', neigh.get('Дополнительно') is False, neigh)
        shot(page, 'desktop-dark-library-electro.png')
        try:
            box = json.loads(page.evaluate("""(() => {
                const a = Array.from(document.querySelectorAll(
                    '#page-library-electro a.menu-btn')).find(x =>
                    x.textContent.indexOf('СО 153-34.03.603-2003') !== -1);
                if (!a) return '';
                const r = a.getBoundingClientRect();
                return JSON.stringify({x: Math.max(0, r.x - 8),
                    y: Math.max(0, r.y - 8),
                    width: Math.min(r.width + 16, 1272),
                    height: Math.min(r.height + 16, 712)});})()"""))
            if box:
                page.screenshot(
                    path=os.path.join(SHOT_DIR, 'desktop-dark-so153-button.png'),
                    clip=box)
        except Exception as e:
            print('  (клоз-ап не снят: %s)' % e)
        ctx.close()

        # ---------- B: десктоп, светлая тема ----------
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 720})
        page2 = ctx2.new_page()
        page2.on('pageerror', lambda e: errors_all.append(str(e)))
        page2.on('dialog', lambda dg: dg.accept())
        ctx2.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t525');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        ctx2.route('**/exec?**', handle)
        ctx2.route('**script.google.com/**', handle)
        ctx2.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx2.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx2.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        page2 = open_page(ctx2, browser, 'light', {'width': 1280, 'height': 720})
        st2 = page_state(page2)

        print('B. Десктоп, светлая тема:')
        check('строка отмены на месте', st2.get('cancelledText') ==
              'Отменена — приказ Минэнерго России от 01.12.2023 № 1105',
              st2.get('cancelledText'))
        check('цвет светлой темы — #c62828 (rgb(198, 40, 40))',
              st2.get('color') == 'rgb(198, 40, 40)', st2.get('color'))
        shot(page2, 'desktop-light-library-electro.png')
        try:
            box2 = json.loads(page2.evaluate("""(() => {
                const a = Array.from(document.querySelectorAll(
                    '#page-library-electro a.menu-btn')).find(x =>
                    x.textContent.indexOf('СО 153-34.03.603-2003') !== -1);
                if (!a) return '';
                const r = a.getBoundingClientRect();
                return JSON.stringify({x: Math.max(0, r.x - 8),
                    y: Math.max(0, r.y - 8),
                    width: Math.min(r.width + 16, 1272),
                    height: Math.min(r.height + 16, 712)});})()"""))
            if box2:
                page2.screenshot(
                    path=os.path.join(SHOT_DIR, 'desktop-light-so153-button.png'),
                    clip=box2)
        except Exception as e:
            print('  (клоз-ап светлой не снят: %s)' % e)
        ctx2.close()

        # ---------- C: мобайл, тёмная тема ----------
        ctx3 = browser.new_context(viewport={'width': 390, 'height': 844})
        page3 = ctx3.new_page()
        page3.on('pageerror', lambda e: errors_all.append(str(e)))
        page3.on('dialog', lambda dg: dg.accept())
        ctx3.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t525');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        ctx3.route('**/exec?**', handle)
        ctx3.route('**script.google.com/**', handle)
        ctx3.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx3.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx3.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        page3 = open_page(ctx3, browser, 'dark', {'width': 390, 'height': 844})
        st3 = page_state(page3)

        print('C. Мобайл 390×844, тёмная тема:')
        check('строка отмены на мобайле', st3.get('cancelledText') ==
              'Отменена — приказ Минэнерго России от 01.12.2023 № 1105',
              st3.get('cancelledText'))
        check('цвет жив (#ef5350)', st3.get('color') == 'rgb(239, 83, 80)',
              st3.get('color'))
        check('строка не обрезана по ширине',
              st3.get('notClipped') is True,
              {'scrollWidth-clipped': st3.get('notClipped')})
        check('строка видима на мобайле', st3.get('cancelledVisible') is True)
        shot(page3, 'mobile-dark-library-electro.png')
        try:
            box3 = json.loads(page3.evaluate("""(() => {
            const a = Array.from(document.querySelectorAll(
                '#page-library-electro a.menu-btn')).find(x =>
                x.textContent.indexOf('СО 153-34.03.603-2003') !== -1);
            if (!a) return '';
            const r = a.getBoundingClientRect();
            return JSON.stringify({x: Math.max(0, r.x - 4), y: Math.max(0, r.y - 4),
                width: Math.min(r.width + 8, 386), height: Math.min(r.height + 8, 840)});})()"""))
            if box3:
                page3.screenshot(
                    path=os.path.join(SHOT_DIR, 'mobile-dark-so153-button.png'),
                    clip=box3)
        except Exception as e:
            print('  (клоз-ап не снят: %s)' % e)
        ctx3.close()

        browser.close()

    print('D. JS-ошибки:')
    check('0 JS-ошибок во всех сценариях', len(errors_all) == 0, errors_all[:3])

    print('\nИТОГО: %d passed, %d failed' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
