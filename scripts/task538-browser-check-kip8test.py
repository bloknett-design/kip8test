#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 538 browser-check (kip8): клиентская синхронизация избранного/
# примечаний телефонного справочника с архивом (PhonebookArchive.gs).
# Схема: локальный HTTP-сервер + Playwright, Apps Script (script.google.com)
# перехватывается page.route и мокается по action:
#   getCurrentUser → {role:'КИП8', email, userId} (вход без экрана OTP)
#   getMyAccess    → HTTP 500 (матрица недоступна → легаси-карта прав)
#   phonebook.getMyData → srvVer 537 + избранное (Тихомиров) + примечание
#                          (Чеберяк) из «архива»
#   phonebook.setFavorite/setNote → фиксация вызовов (проверка push)
# Проверяется:
#   A) приложение грузится без JS-ошибок, вход по токену;
#   B) #phonebook: бейдж синхронизации в тулбаре, «Синхронизировано»
#      после pull;
#   C) серверное избранное: звезда Тихомирова залита;
#   D) серверное примечание «Примечание из архива» на карточке Чеберяк;
#   E) тумблер звезды Синякова → debounce 1.5с → phonebook.setFavorite
#      (on=true, entry.name='Синяков…', token);
#   F) примечание через диалог → phonebook.setNote (text, entry);
#   G) тап по бейджу → тост с email;
#   H) светлая тема — бейдж читаем; скриншоты.

import datetime as _dt
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from playwright.sync_api import sync_playwright

PORT = 8996
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task538')
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


# Реальные id из data/phonebook.json (pbMakeId: header|group|subgroup|position|name|phone;
# у записей верхнего уровня group/subgroup = null → header|||position)
HDR = 'ООО ПО «ТОКЕМ»'
ID_TIKH = HDR + '|||Генеральный директор|Тихомиров Андрей Львович|50 01'
ID_CHEB = HDR + '|||Референт|Чеберяк Алена Владимировна|50 70'
ID_SINY = HDR + '|||Директор коммерческий|Синяков Максим Сергеевич|50 12'


def gas_mock(action):
    if action == 'getCurrentUser':
        return 200, {'ok': True, 'data': {'role': 'КИП8',
                                          'email': 'browser@tokem.local',
                                          'userId': 1}}
    if action == 'phonebook.getMyData':
        return 200, {'ok': True, 'data': {'srvVer': '537',
                                          'favorites': {ID_TIKH: True},
                                          'notes': {ID_CHEB: 'Примечание из архива'}}}
    if action == 'phonebook.setFavorite':
        return 200, {'ok': True, 'data': {'id': 'x', 'on': True, 'already': False}}
    if action == 'phonebook.setNote':
        return 200, {'ok': True, 'data': {'id': 'x', 'action': 'created'}}
    # матрица прав/прочие — недоступны (легаси-карта на клиенте)
    return 500, {'ok': False, 'error': 'not_mocked: ' + str(action)}


def main():
    httpd = serve()
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1024, 'height': 768})
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))

        def route_gas(route):
            url = route.request.url
            action = ''
            if 'action=' in url:
                action = url.split('action=')[1].split('&')[0]
            try:
                action = __import__('urllib.parse', fromlist=['parse']).unquote(action)
            except Exception:
                pass
            SERVER_CALLS.append(action)
            status, body = gas_mock(action)
            route.fulfill(status=status, content_type='application/json',
                          body=json.dumps(body, ensure_ascii=False))

        # Apps Script — мок; всё прочее (index/data/images) — локальный сервер
        page.route('**/macros/s/**', route_gas)

        # Токен в localStorage ДО загрузки приложения (вход без OTP)
        page.add_init_script(
            "try { localStorage.setItem('kip8test:kip8_session_token', 'browser-test-token'); } catch (e) {}")

        page.goto('http://127.0.0.1:%d/' % PORT)
        page.wait_for_timeout(1500)

        # A) вход и загрузка
        check('A1. getCurrentUser замокан и вызван', 'getCurrentUser' in SERVER_CALLS,
              SERVER_CALLS[:6])
        check('A2. нет JS-ошибок при старте', len(errors) == 0, errors[:3])

        # Хэш-навигация на старте опережает асинхронную авторизацию, а
        # первая активация SW (clients.claim) перезагружает страницу —
        # ждём роль на пережившей перезагрузку странице и открываем
        # справочник программно
        page.wait_for_function("typeof KipAuth !== 'undefined' && KipAuth._cachedRole",
                               timeout=10000)
        page.evaluate("navigateTo('phonebook')")
        page.wait_for_function("document.getElementById('pbList') && "
                               "document.getElementById('pbList').children.length > 0",
                               timeout=10000)
        page.wait_for_timeout(1500)

        # B) бейдж синхронизации
        badge = page.locator('#pbSyncBadge')
        check('B1. бейдж pbSyncBadge в тулбаре', badge.count() == 1)
        check('B2. getMyData вызван при открытии раздела',
              'phonebook.getMyData' in SERVER_CALLS, SERVER_CALLS)
        label = page.locator('#pbSyncBadgeLabel').inner_text()
        check('B3. бейдж «Синхронизировано» после pull', label == 'Синхронизировано', label)
        badge_cls = badge.get_attribute('class') or ''
        check('B4. класс sync-ok', 'sync-ok' in badge_cls, badge_cls)

        # C) серверное избранное. Карточки ищем по ТОЧНОМУ data-id (в
        # справочнике 5 Тихомировых!); записи верхнего уровня лежат в
        # подгруппе «Без группы» — раскрыть секцию и подгруппу
        page.locator('.pb-section-title', has_text='ООО ПО «ТОКЕМ»').first.click()
        page.wait_for_timeout(500)
        page.locator('.pb-subgroup-title', has_text='Без группы').first.click()
        page.wait_for_timeout(700)
        tik_card = page.locator('[data-id="%s"]' % ID_TIKH)
        check('C1. карточка Тихомирова (по data-id) в DOM', tik_card.count() == 1)
        star_on = tik_card.locator('.pb-fav-btn.fav-active').count() > 0
        check('C2. звезда серверного избранного залита', star_on)

        # D) серверное примечание на карточке Чеберяк (по data-id)
        cheb = page.locator('[data-id="%s"]' % ID_CHEB)
        note_txt = cheb.locator('.pb-note').first.inner_text() if cheb.count() else ''
        check('D1. серверное примечание видно', 'Примечание из архива' in note_txt, note_txt)

        shot(page, '01-phonebook-sync-ok-dark.png')

        # E) тумблер звезды Синякова → push setFavorite
        before = SERVER_CALLS.count('phonebook.setFavorite')
        siny = page.locator('[data-id="%s"]' % ID_SINY)
        siny.locator('.pb-fav-btn').click()
        page.wait_for_timeout(2600)   # debounce 1.5с + запас
        after = SERVER_CALLS.count('phonebook.setFavorite')
        check('E1. setFavorite уходит после тумблера (debounce 1.5с)', after == before + 1,
              'до=%d после=%d' % (before, after))
        badge_txt = page.locator('#pbSyncBadgeLabel').inner_text()
        check('E2. бейдж снова «Синхронизировано» после push', badge_txt == 'Синхронизировано',
              badge_txt)

        # F) примечание через диалог → push setNote
        before_n = SERVER_CALLS.count('phonebook.setNote')
        siny2 = page.locator('[data-id="%s"]' % ID_SINY)
        siny2.locator('.pb-note-add').click()
        page.wait_for_timeout(400)
        page.fill('.kip-dialog-input', 'Заметка из браузера')
        page.click('.kip-dialog-ok')
        page.wait_for_timeout(2600)
        after_n = SERVER_CALLS.count('phonebook.setNote')
        check('F1. setNote уходит после сохранения примечания', after_n == before_n + 1,
              'до=%d после=%d' % (before_n, after_n))
        note2 = page.locator('[data-id="%s"]' % ID_SINY).locator('.pb-note')
        check('F2. примечание отрисовано на карточке',
              note2.count() > 0 and 'Заметка из браузера' in note2.first.inner_text())

        # G) тап по бейджу → тост с email
        page.click('#pbSyncBadge')
        page.wait_for_timeout(300)
        toast = page.locator('#toastMessage').inner_text()
        check('G1. тост-детализация с email', 'browser@tokem.local' in toast, toast)

        # H) светлая тема — бейдж читаем
        page.evaluate("document.documentElement.setAttribute('data-theme','light')")
        page.wait_for_timeout(300)
        shot(page, '02-phonebook-sync-light.png')
        badge_vis = page.locator('#pbSyncBadge').is_visible()
        check('H1. бейдж видим в светлой теме', badge_vis)

        check('Z. JS-ошибок нет за всю сессию', len(errors) == 0, errors[:5])
        browser.close()
    httpd.shutdown()

    print('\nИтог: %d/%d (пройдено/всего), время %s' %
          (PASS, PASS + FAIL, _dt.datetime.now().strftime('%H:%M:%S')))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
