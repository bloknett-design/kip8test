#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 539 browser-check (kip8test): табы «Все / Избранное» телефонного
# справочника — МОБИЛЬНЫЙ нижний бар #pbBottomBar (по образцу
# расходомеров/датчиков) + ДЕСКТОПНЫЕ табы #pbDesktopTabs в тулбаре
# (видимы на ОБОИХ «экранах»: «разделы» свёрнуты / «содержание»
# раскрыто — тулбар sticky).
# Схема: локальный HTTP-сервер + Playwright, Apps Script мокается
# page.route (вход по токену; серверное избранное — Тихомиров).
# A) мобайл: бар fixed внизу, 2 таба, старой кнопки нет, фильтрация
#    работает, счётчики, светлaя тема, 0 JS-ошибок;
# B) десктоп: бар скрыт, табы в тулбаре, видимость при свёрнутых
#    разделах и при раскрытой организации (скролл), фильтрация.

import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from playwright.sync_api import sync_playwright

PORT = 8997
REPO = '/home/z/my-project/kip8test'
SHOT_DIR = '/home/z/my-project/download/kip8test-task539'
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
ID_TIKH = HDR + '|||Генеральный директор|Тихомиров Андрей Львович|50 01'
ID_CHEB = HDR + '|||Референт|Чеберяк Алена Владимировна|50 70'


def gas_mock(action):
    if action == 'getCurrentUser':
        return 200, {'ok': True, 'data': {'role': 'КИП8',
                                          'email': 'browser@tokem.local',
                                          'userId': 1}}
    if action == 'phonebook.getMyData':
        return 200, {'ok': True, 'data': {'srvVer': '537',
                                          'favorites': {ID_TIKH: True},
                                          'notes': {}}}
    if action in ('phonebook.setFavorite', 'phonebook.setNote'):
        return 200, {'ok': True, 'data': {'id': 'x'}}
    return 500, {'ok': False, 'error': 'not_mocked: ' + str(action)}


def make_page(browser, w, h, mobile, errors):
    ctx = browser.new_context(viewport={'width': w, 'height': h},
                              is_mobile=mobile, has_touch=mobile)
    page = ctx.new_page()
    page.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))

    def route_gas(route):
        url = route.request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
        try:
            from urllib.parse import unquote
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


def main():
    httpd = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= МОБИЛЬНЫЙ (390×844) =================
        print('== МОБИЛЬНЫЙ 390×844 ==')
        errors = []
        ctx, page = make_page(browser, 390, 844, True, errors)
        open_phonebook(page)

        check('M1. нет JS-ошибок при старте', len(errors) == 0, errors[:3])

        bar = page.locator('#pbBottomBar')
        check('M2. нижний бар #pbBottomBar в DOM', bar.count() == 1)
        disp = page.evaluate("getComputedStyle(document.getElementById('pbBottomBar')).display")
        check('M3. бар отображается (display: grid)', disp == 'grid', disp)
        pos = page.evaluate("getComputedStyle(document.getElementById('pbBottomBar')).position")
        check('M4. бар фиксирован снизу (position: fixed)', pos == 'fixed', pos)
        rect = bar.bounding_box()
        check('M5. бар прижат к низу вьюпорта',
              rect and abs(rect['y'] + rect['height'] - 844) < 2, rect)

        tabs = bar.locator('.pb-tab')
        check('M6. в баре 2 таба', tabs.count() == 2, tabs.count())
        labels = [tabs.nth(i).inner_text().strip() for i in range(2)]
        check('M7. надписи «Все» и «Избранное»',
              'Все' in labels[0] and 'Избранное' in labels[1], labels)
        fav_active = bar.locator('.pb-tab[data-pb-tab="fav"]').get_attribute('class') or ''
        check('M8. активен таб «Все» (не «Избранное»)', 'active' not in fav_active, fav_active)

        check('M9. старая кнопка #pbFilterFav удалена',
              page.locator('#pbFilterFav').count() == 0)
        desk_disp = page.evaluate("getComputedStyle(document.getElementById('pbDesktopTabs')).display")
        check('M10. десктоп-табы скрыты на мобиле (display: none)', desk_disp == 'none', desk_disp)

        # счётчики
        all_cnt = page.locator('#pbAllCountMob').inner_text()
        fav_cnt = page.locator('#pbFavCountMob').inner_text()
        check('M11. счётчик «Все» = 236', all_cnt == '236', all_cnt)
        check('M12. счётчик «Избранное» = 1 (Тихомиров с сервера)', fav_cnt == '1', fav_cnt)

        # фильтрация: таб «Избранное»
        page.locator('#pbBottomBar .pb-tab[data-pb-tab="fav"]').click()
        page.wait_for_timeout(600)
        info = page.locator('#pbInfo').inner_text()
        check('M13. инфо: «Избранные: 1»', 'Избранные: 1' in info, info)
        cards = page.locator('.pb-card')
        check('M14. в режиме избранного — 1 карточка', cards.count() == 1, cards.count())
        name1 = cards.first.locator('.pb-card-name').inner_text() if cards.count() else ''
        check('M15. карточка — Тихомиров (серверное избранное)', 'Тихомиров' in name1, name1)
        fav_cls = bar.locator('.pb-tab[data-pb-tab="fav"]').get_attribute('class') or ''
        check('M16. таб «Избранное» стал активным', 'active' in fav_cls, fav_cls)
        shot(page, '01-mobile-fav-tab-dark.png')

        # назад на «Все»
        page.locator('#pbBottomBar .pb-tab[data-pb-tab="all"]').click()
        page.wait_for_timeout(600)
        info2 = page.locator('#pbInfo').inner_text()
        check('M17. возврат на «Все»: инфо «Всего: 236»', 'Всего: 236' in info2, info2)
        check('M18. таб «Все» снова активен',
              'active' in (bar.locator('.pb-tab[data-pb-tab="all"]').get_attribute('class') or ''))

        # отступ списка — бар не накрывает карточки
        pb_pad = page.evaluate(
            "getComputedStyle(document.querySelector('.pb-list')).paddingBottom")
        check('M19. отступ списка снизу ≥96px (бар не накрывает)',
              pb_pad.rstrip('px').isdigit() and int(pb_pad.rstrip('px')) >= 96, pb_pad)

        # светлая тема
        page.evaluate("document.documentElement.setAttribute('data-theme','light')")
        page.wait_for_timeout(400)
        shot(page, '02-mobile-fav-tab-light.png')
        light_col = page.evaluate(
            "getComputedStyle(document.querySelector('#pbBottomBar .pb-tab.active')).color")
        check('M20. светлая тема: активный таб тёмный (читаем)',
              'rgb(20, 20, 19)' in light_col, light_col)
        ctx.close()

        # ================= ДЕСКТОП (1440×900) =================
        print('== ДЕСКТОП 1440×900 ==')
        errors2 = []
        ctx2, page2 = make_page(browser, 1440, 900, False, errors2)
        open_phonebook(page2)

        check('D1. нет JS-ошибок (десктоп)', len(errors2) == 0, errors2[:3])
        bar_disp = page2.evaluate(
            "getComputedStyle(document.getElementById('pbBottomBar')).display")
        check('D2. мобильный бар скрыт на десктопе', bar_disp == 'none', bar_disp)

        dtabs = page2.locator('#pbDesktopTabs')
        check('D3. десктоп-табы #pbDesktopTabs в DOM', dtabs.count() == 1)
        dt_disp = page2.evaluate(
            "getComputedStyle(document.getElementById('pbDesktopTabs')).display")
        check('D4. табы отображаются (display: flex)', dt_disp == 'flex', dt_disp)

        # ЭКРАН 1 «разделы»: organizations свёрнуты, табы видимы
        box = dtabs.bounding_box()
        check('D5. ЭКРАН «разделы»: табы в вьюпорте (тулбар сверху)',
              box and box['y'] >= 0 and box['y'] < 300 and box['x'] >= 0, box)
        d_all = page2.locator('#pbAllCountDesk').inner_text()
        d_fav = page2.locator('#pbFavCountDesk').inner_text()
        check('D6. счётчики десктопа (Все=236, Избранное=1)',
              d_all == '236' and d_fav == '1', (d_all, d_fav))
        shot(page2, '03-desktop-sections-screen.png')

        # ЭКРАН 2 «содержание»: раскрыть организацию, проскроллить
        page2.locator('.pb-section-title').first.click()
        page2.wait_for_timeout(500)
        page2.locator('.pb-subgroup-title').first.click()
        page2.wait_for_timeout(700)
        page2.evaluate("document.querySelector('.pb-list').scrollIntoView({block:'end'})")
        page2.wait_for_timeout(400)
        box2 = dtabs.bounding_box()
        check('D7. ЭКРАН «содержание»: табы всё ещё видны (sticky)',
              box2 and box2['y'] >= 0 and box2['y'] < 300, box2)
        check('D8. контакты раскрыты (содержание видно)',
              page2.locator('.pb-card').count() > 0,
              page2.locator('.pb-card').count())
        shot(page2, '04-desktop-content-screen.png')

        # фильтрация на десктопе
        page2.locator('#pbDesktopTabs .pb-tab[data-pb-tab="fav"]').click()
        page2.wait_for_timeout(600)
        info_d = page2.locator('#pbInfo').inner_text()
        check('D9. десктоп: таб «Избранное» фильтрует («Избранные: 1»)',
              'Избранные: 1' in info_d, info_d)
        check('D10. карточка Тихомирова единственная',
              page2.locator('.pb-card').count() == 1,
              page2.locator('.pb-card').count())
        fav_cls_d = dtabs.locator('.pb-tab[data-pb-tab="fav"]').get_attribute('class') or ''
        check('D11. таб «Избранное» активен на десктопе', 'active' in fav_cls_d, fav_cls_d)

        page2.locator('#pbDesktopTabs .pb-tab[data-pb-tab="all"]').click()
        page2.wait_for_timeout(600)
        check('D12. возврат на «Все» (десктоп)',
              'Всего: 236' in page2.locator('#pbInfo').inner_text())

        # светлая тема десктопа
        page2.evaluate("document.documentElement.setAttribute('data-theme','light')")
        page2.wait_for_timeout(400)
        shot(page2, '05-desktop-light.png')
        ctx2.close()
        browser.close()
    httpd.shutdown()

    print()
    print('ИТОГО: %d passed, %d failed' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
