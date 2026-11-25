#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 559 browser-check (kip8test): вкладка «Избранное» телефонного
# справочника на ДЕСКТОПЕ — ДВА ОКНА, как «Все» (заявка: «группы в
# одном окне, а телефоны при выборе группы во втором окне»).
# Схема: локальный HTTP-сервер + Playwright, Apps Script мокается
# page.route (вход по токену; серверное избранное — 3 контакта:
# Тихомиров А. и Филиппов в ООО ПО «ТОКЕМ» (Без группы / ПФО),
# Тихомиров В. в ООО НПО "ТОКЕМ" (Без группы)).
# ДЕСКТОП: старт на «Избранном» (по клику таба) — дерево ТОЛЬКО по
#   избранным (2 организации, счётчики 2/1/1; ЧОО/СибИмпорт/ТД скрыты,
#   карточек в левом окне нет); клик по ПФО — правое окно с 1 карточкой
#   Филиппова, подсветка строки, крошки; клик по организации — 2
#   избранного блоками подразделений; снятие ★ Филиппова — карточка
#   уходит из окна НА МЕСТЕ (окно открыто), строка ПФО исчезает из
#   дерева; снятие ★ последнего в организации — окно закрывается,
#   организация исчезает; поиск — инлайн-результаты, очистка — дерево;
#   «Все» — прежнее полное дерево (5 организаций, свёрнуты кроме
#   ТОКЕМ — Task 542); ✕ закрывает окно; светлая тема; 0 JS-ошибок.
# МОБАЙЛ: «Избранное» — прежний инлайн-список карточек (3), «Все» —
#   аккордеон 5 секций; 0 JS-ошибок.

import json
import os
import re
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

PORT = 8994
REPO = '/home/z/my-project/kip8test'
SHOT_DIR = '/home/z/my-project/download/kip8test-task559'
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0
SERVER_CALLS = []


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
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def serve():
    os.chdir(REPO)
    httpd = HTTPServer(('127.0.0.1', PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


HDR = 'ООО ПО «ТОКЕМ»'
HDR2 = 'ООО НПО "ТОКЕМ"'
ID_TIKH = HDR + '|||Генеральный директор|Тихомиров Андрей Львович|50 01'
ID_PHIL = HDR + '|Планово-финансовый отдел (ПФО)||Начальник|Филиппов Алексей Владимирович|51 18'
ID_TIKH2 = HDR2 + '|||Ген. директор|Тихомиров Владимир Андреевич|50 03'


def gas_mock(action):
    if action == 'getCurrentUser':
        return 200, {'ok': True, 'data': {'role': 'КИП8',
                                          'email': 'browser@tokem.local',
                                          'userId': 1}}
    if action == 'phonebook.getMyData':
        return 200, {'ok': True, 'data': {'srvVer': '537',
                                          'favorites': {ID_TIKH: True,
                                                        ID_PHIL: True,
                                                        ID_TIKH2: True},
                                          'notes': {}}}
    if action in ('phonebook.setFavorite', 'phonebook.setNote'):
        return 200, {'ok': True, 'data': {'id': 'x'}}
    return 500, {'ok': False, 'error': 'not_mocked: ' + str(action)}


def make_page(browser, w, h, mobile, errors):
    # Task 540 урок: SW-скрипт не перехватывается page.route — блокируем
    ctx = browser.new_context(viewport={'width': w, 'height': h},
                              is_mobile=mobile, has_touch=mobile,
                              service_workers='block')
    page = ctx.new_page()
    page.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))

    def route_gas(route):
        url = route.request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
        try:
            action = unquote(action)
        except Exception:
            pass
        SERVER_CALLS.append(action)
        status, body = gas_mock(action)
        route.fulfill(status=status, content_type='application/json',
                      body=json.dumps(body, ensure_ascii=False))

    page.route('**/macros/s/**', route_gas)
    page.add_init_script(
        "try { localStorage.setItem('kip8test:kip8_session_token', 'browser-test-token'); } catch (e) {}")
    return ctx, page


def open_phonebook(page):
    page.goto('http://127.0.0.1:%d/' % PORT)
    page.wait_for_timeout(1500)
    page.wait_for_function("typeof KipAuth !== 'undefined' && KipAuth._cachedRole",
                           timeout=10000)
    page.evaluate("navigateTo('phonebook')")
    page.wait_for_function("document.getElementById('pbList') && "
                           "document.getElementById('pbList').children.length > 0",
                           timeout=10000)
    page.wait_for_timeout(1200)


def set_search(page, text):
    page.evaluate(
        "var el = document.getElementById('pbSearchInput');"
        "el.value = '%s'; el.dispatchEvent(new Event('input', {bubbles: true}));" % text)
    page.wait_for_timeout(400)


def main():
    httpd = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= ДЕСКТОП (1440×900) =================
        print('== ДЕСКТОП 1440×900 ==')
        errors = []
        ctx, page = make_page(browser, 1440, 900, False, errors)
        open_phonebook(page)

        # Синхронизация: серверное избранное (3) подъехало и в счётчики
        page.wait_for_function(
            "document.getElementById('pbFavCountDesk') && "
            "document.getElementById('pbFavCountDesk').textContent === '3'",
            timeout=10000)
        check('D1. нет JS-ошибок при старте', len(errors) == 0, errors[:3])
        check('D2. счётчики: «Все» = 230, «Избранное» = 3 (сервер)',
              page.locator('#pbAllCountDesk').inner_text() == '230' and
              page.locator('#pbFavCountDesk').inner_text() == '3')

        # Вкладка «Избранное» — ДВА ОКНА: дерево по избранным
        page.locator('#pbDesktopTabs .pb-tab[data-pb-tab="fav"]').click()
        page.wait_for_timeout(600)
        org_rows = page.locator('#pbList .pb-master-org-row')
        check('D3. дерево: 2 организации с избранным', org_rows.count() == 2,
              org_rows.count())
        list_html = page.evaluate("document.getElementById('pbList').innerHTML")
        check('D4. организации без избранного скрыты (ЧОО/СибИмпорт/ТД)',
              'Дежурная часть' not in list_html and 'СибИмпорт' not in list_html
              and 'ООО ТД' not in list_html)
        check('D5. карточек в левом окне НЕТ (они в правом)',
              page.locator('#pbList .pb-card').count() == 0)
        check('D6. клики строк — pbFavMasterOpen (индексы)',
              'pbFavMasterOpen(' in list_html)
        tokem = page.locator('#pbList .pb-master-org-row', has_text=re.compile('ООО ПО «ТОКЕМ»'))
        check('D7. счётчик ООО ПО «ТОКЕМ» = 2 избранного',
              '<span class="pb-master-count">2</span>' in (tokem.first.inner_html() if tokem.count() else ''))
        pfo = page.locator('#pbList .pb-master-row', has_text=re.compile('Планово-финансовый'))
        check('D8. строка ПФО с счётчиком 1', pfo.count() == 1 and
              '<span class="pb-master-count">1</span>' in pfo.first.inner_html())
        shot(page, '01-desktop-fav-tree.png')

        # Клик по подразделению ПФО → правое окно с избранными
        pfo.first.click()
        page.wait_for_timeout(600)
        panel_active = page.evaluate(
            "document.getElementById('detailPanel').classList.contains('active')")
        cards = page.locator('#detailPanelBody .pb-card')
        check('D9. правое окно открыто', panel_active)
        check('D10. в окне 1 карточка — Филиппов (только избранные группы)',
              cards.count() == 1 and 'Филиппов' in cards.first.inner_text(),
              cards.count())
        check('D11. выбранная строка подсвечена',
              'selected' in (pfo.first.get_attribute('class') or ''))
        bc = page.evaluate("document.getElementById('detailBreadcrumbContent').innerHTML")
        check('D12. крошки: организация + ПФО, сегмент — pbFavMasterOpen',
              'ООО ПО «ТОКЕМ»' in bc and 'Планово-финансовый' in bc and
              'pbFavMasterOpen(0)' in bc, bc[:200])
        shot(page, '02-desktop-fav-group-panel.png')

        # Клик по организации → все избранные организации блоками
        page.locator('#pbList .pb-master-org-row', has_text=re.compile('ООО ПО «ТОКЕМ»')).first.click()
        page.wait_for_timeout(600)
        cards2 = page.locator('#detailPanelBody .pb-card')
        gtitles = page.locator('#detailPanelBody .pb-detail-group-title')
        check('D13. вся организация: 2 избранного (Тихомиров + Филиппов)',
              cards2.count() == 2, cards2.count())
        check('D14. блоки по подразделениям (Без группы + ПФО)',
              gtitles.count() == 2,
              [gtitles.nth(i).inner_text() for i in range(min(3, gtitles.count()))])
        shot(page, '03-desktop-fav-org-panel.png')

        # Снятие ★ у Филиппова: карточка уходит из окна НА МЕСТЕ
        page.locator('#detailPanelBody .pb-card', has_text=re.compile('Филиппов')) \
            .locator('.pb-fav-btn').click()
        page.wait_for_timeout(700)
        check('D15. карточка Филиппова ушла из окна (без переоткрытия)',
              page.locator('#detailPanelBody .pb-card').count() == 1 and
              page.evaluate("document.getElementById('detailPanel').classList.contains('active')"))
        check('D16. строка ПФО исчезла из дерева, счётчик организации = 1',
              page.locator('#pbList .pb-master-row', has_text=re.compile('Планово-финансовый')).count() == 0 and
              '<span class="pb-master-count">1</span>' in
              page.locator('#pbList .pb-master-org-row', has_text=re.compile('ООО ПО «ТОКЕМ»')).first.inner_html())
        check('D17. счётчик таба «Избранное» = 2',
              page.locator('#pbFavCountDesk').inner_text() == '2')
        shot(page, '04-desktop-fav-after-unstar.png')

        # Последний избранного организации: окно закрывается, организация исчезает
        page.locator('#pbList .pb-master-row', has_text=re.compile('Без группы')).first.click()
        page.wait_for_timeout(600)
        check('D18. «Без группы» ТОКЕМ: 1 карточка Тихомирова',
              page.locator('#detailPanelBody .pb-card').count() == 1 and
              'Тихомиров Андрей' in page.locator('#detailPanelBody .pb-card').first.inner_text())
        page.locator('#detailPanelBody .pb-card .pb-fav-btn').first.click()
        page.wait_for_timeout(800)
        check('D19. последний ★ снят — правое окно ЗАКРЫТО',
              not page.evaluate("document.getElementById('detailPanel').classList.contains('active')"))
        check('D20. организация исчезла из дерева (осталась только НПО)',
              page.locator('#pbList .pb-master-org-row').count() == 1 and
              'НПО' in page.locator('#pbList .pb-master-org-row').first.inner_text())
        check('D21. счётчик таба «Избранное» = 1',
              page.locator('#pbFavCountDesk').inner_text() == '1')
        shot(page, '05-desktop-fav-org-empty-closed.png')

        # Поиск на «Избранном» — инлайн-результаты (не дерево)
        set_search(page, 'Владимир')
        check('D22. поиск: инлайн-карточка Тихомирова В.',
              page.locator('#pbList .pb-card').count() == 1 and
              'Тихомиров Владимир' in page.locator('#pbList .pb-card').first.inner_text() and
              'pb-master' not in page.evaluate("document.getElementById('pbList').innerHTML"))
        set_search(page, '')
        check('D23. очистка поиска — дерево вернулось',
              page.locator('#pbList .pb-master-org-row').count() == 1)
        shot(page, '06-desktop-fav-search-restored.png')

        # Вкладка «Все» — прежнее полное дерево (регрессия Tasks 540-542)
        page.locator('#pbDesktopTabs .pb-tab[data-pb-tab="all"]').click()
        page.wait_for_timeout(600)
        check('D24. «Все»: 5 организаций, карточек в левом окне нет',
              page.locator('#pbList .pb-master-org-row').count() == 5 and
              page.locator('#pbList .pb-card').count() == 0)
        check('D25. «Все»: свёрнуты все, кроме ТОКЕМ (Task 542)',
              page.locator('#pbList .pb-master-org.collapsed').count() == 4)

        # Правое окно «Все» живо + ✕ закрывает
        page.locator('#pbList .pb-master-row').first.click()
        page.wait_for_timeout(500)
        check('D26. «Все»: клик по подразделению — правое окно с контактами',
              page.evaluate("document.getElementById('detailPanel').classList.contains('active')") and
              page.locator('#detailPanelBody .pb-card').count() > 0)
        page.locator('.detail-breadcrumb-close').click()
        page.wait_for_timeout(500)
        check('D27. ✕ закрыл окно, выбор сброшен',
              not page.evaluate("document.getElementById('detailPanel').classList.contains('active')") and
              page.locator('#pbList .selected').count() == 0)
        shot(page, '07-desktop-all-tree.png')

        # Светлая тема
        page.evaluate("document.documentElement.setAttribute('data-theme','light')")
        page.locator('#pbDesktopTabs .pb-tab[data-pb-tab="fav"]').click()
        page.wait_for_timeout(600)
        shot(page, '08-desktop-fav-light.png')
        check('D28. нет JS-ошибок (десктоп, весь сценарий)', len(errors) == 0, errors[:5])
        ctx.close()

        # ================= МОБИЛЬНЫЙ (390×844) =================
        print('== МОБИЛЬНЫЙ 390×844 ==')
        errors_m = []
        ctx_m, page_m = make_page(browser, 390, 844, True, errors_m)
        open_phonebook(page_m)
        page_m.wait_for_function(
            "document.getElementById('pbFavCountMob') && "
            "document.getElementById('pbFavCountMob').textContent === '3'",
            timeout=10000)

        page_m.locator('#pbBottomBar .pb-tab[data-pb-tab="fav"]').click()
        page_m.wait_for_timeout(600)
        cards_m = page_m.locator('#pbList .pb-card')
        check('M1. мобильное «Избранное» — инлайн-карточки (3, не дерево)',
              cards_m.count() == 3 and
              'pb-master' not in page_m.evaluate("document.getElementById('pbList').innerHTML"),
              cards_m.count())
        shot(page_m, '09-mobile-fav.png')

        page_m.locator('#pbBottomBar .pb-tab[data-pb-tab="all"]').click()
        page_m.wait_for_timeout(600)
        check('M2. мобильное «Все» — аккордеон 5 секций',
              page_m.locator('#pbList .pb-section').count() == 5)
        check('M3. нет JS-ошибок (мобайл)', len(errors_m) == 0, errors_m[:5])
        shot(page_m, '10-mobile-all.png')
        ctx_m.close()
        browser.close()
    httpd.shutdown()

    print()
    print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
