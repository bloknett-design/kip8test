#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 546 browser-check (kip8test): Сапёр — (1) анимация
# переворачивания клетки с бликом по глянцу + вибрация; (2) архив
# счёта по email — блок «Архив партий» (сервер minesweeper.*).
# Схема: локальный HTTP + Playwright; Apps Script мокается
# page.route (вход по токену, роль КИП8 — есть secret.view);
# navigator.vibrate подменён init-скриптом (счёт вызовов).
#
# A) МОБИЛЬНЫЙ 390×844: поле 81 клетка; тап → переворот
#    (.ms-cell-flip, animationName msCellFlip, блик ::after
#    msCellShine + linear-gradient, волна задержек, наследование
#    delay на ::after); вибрация 12; взрыв: вибрация [80,60,120],
#    оверлей ЗАДЕРЖАН (750 мс), recordResult уходит; победа:
#    [40,40,40,40,100], оверлей 650 мс, флаги на мины; архив:
#    блок видим, 5 слотов (3 данных: ✓/✗/даты), статистика.
# B) БЕЗ серверного модуля (500): блок архива скрыт, взрыв не
#    роняет страницу, 0 JS-ошибок (тихая деградация).
# C) REDUCED MOTION: анимации выключены (animation: none).
# D) ДЕСКТОП 1280×800: клик-переворот, блик, архив, светлая тема
#    (блик 0.85, слот .loss), 0 JS-ошибок.

import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

from playwright.sync_api import sync_playwright

PORT = 8996
REPO = '/home/z/my-project/kip8test'
SHOT_DIR = '/home/z/my-project/download/kip8test-task546'
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


ARCHIVE_DATA = {
    'srvVer': '546',
    'rows': [
        {'id': 3, 'ts': '2026-10-22T09:00:00', 'won': False, 'diff': 'hard',
         'field': '9x28', 'time': 130, 'mines': 45},
        {'id': 2, 'ts': '2026-10-21T09:00:00', 'won': True, 'diff': 'medium',
         'field': '9x16', 'time': 61, 'mines': 25},
        {'id': 1, 'ts': '2026-10-20T09:00:00', 'won': True, 'diff': 'easy',
         'field': '9x9', 'time': 24, 'mines': 10}
    ],
    'stats': {'total': 3, 'wins': 2, 'losses': 1,
              'best': {'easy': 24, 'medium': 61}}
}


def gas_mock(action, no_minesweeper=False):
    if action == 'getCurrentUser':
        return 200, {'ok': True, 'data': {'role': 'КИП8',
                                          'email': 'browser@tokem.local',
                                          'userId': 1}}
    if no_minesweeper and action.startswith('minesweeper.'):
        return 500, {'ok': False, 'error': 'not_mocked'}
    if action == 'minesweeper.getMyArchive':
        return 200, {'ok': True, 'data': ARCHIVE_DATA}
    if action == 'minesweeper.recordResult':
        return 200, {'ok': True, 'data': {'id': 4, 'saved': True}}
    return 500, {'ok': False, 'error': 'not_mocked: ' + str(action)}


VIB_STUB = """
window.__vibes = [];
try {
  navigator.vibrate = function (p) { window.__vibes.push(p); return true; };
} catch (e) {}
"""


def make_page(browser, w, h, mobile, errors, no_minesweeper=False,
              reduced=False):
    ctx = browser.new_context(viewport={'width': w, 'height': h},
                              is_mobile=mobile, has_touch=mobile,
                              color_scheme='dark',
                              reduced_motion=('reduce' if reduced else 'no-preference'))
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
        status, body = gas_mock(action, no_minesweeper)
        route.fulfill(status=status, content_type='application/json',
                      body=json.dumps(body, ensure_ascii=False))

    page.route('**/macros/s/**', route_gas)
    page.add_init_script(
        "try { localStorage.setItem('kip8test:kip8_session_token', 'browser-test-token');"
        " localStorage.setItem('app-theme', 'dark'); } catch (e) {}")   # тёмная — детерминированно (дефолт 'light' следует за color-scheme)
    page.add_init_script(VIB_STUB)
    return ctx, page


def open_sweeper(page):
    page.goto('http://127.0.0.1:%d/' % PORT)
    page.wait_for_timeout(1500)
    page.wait_for_function("typeof KipAuth !== 'undefined' && KipAuth._cachedRole",
                           timeout=10000)
    page.evaluate("navigateTo('minesweeper')")
    page.wait_for_function("document.getElementById('msBoard') && "
                           "document.getElementById('msBoard').children.length > 0",
                           timeout=10000)
    page.wait_for_timeout(800)


def find_mine():
    return ("() => { for (let r = 0; r < msRows; r++) { for (let c = 0; c < msCols; c++)"
            " { if (msBoard[r][c] === -1) return [r, c]; } } return null; }")


def main():
    httpd = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ================= A. МОБИЛЬНЫЙ 390×844 =================
        print('== A. МОБИЛЬНЫЙ 390×844 (с серверным архивом) ==')
        errors = []
        ctx, page = make_page(browser, 390, 844, True, errors)
        open_sweeper(page)

        check('A1. нет JS-ошибок при старте', len(errors) == 0, errors[:3])
        cells = page.locator('#msBoard .ms-cell')
        check('A2. поле 9x9 = 81 клетка', cells.count() == 81, cells.count())

        # --- тап по клетке: переворот + блик + вибрация ---
        page.tap('#msBoard .ms-cell')           # клетка (0,0) — эпицентр
        page.wait_for_timeout(120)
        info = page.evaluate(
            "() => { const flips = [...document.querySelectorAll('.ms-cell.ms-cell-flip')];"
            " const first = flips[0];"
            " const cs = first ? getComputedStyle(first) : null;"
            " const after = first ? getComputedStyle(first, '::after') : null;"
            " let maxDelay = 0, originDelay = null, originDelayStr = null;"
            " flips.forEach(f => { const csf = getComputedStyle(f);"
            "   const d = parseFloat(csf.animationDelay) || 0;"
            "   if (d > maxDelay) maxDelay = d;"
            "   if (f.dataset.r === '0' && f.dataset.c === '0') { originDelay = d; originDelayStr = csf.animationDelay; } });"
            " return { flips: flips.length, revealed: document.querySelectorAll('.ms-cell-revealed').length,"
            "  animName: cs ? cs.animationName : null, animDur: cs ? cs.animationDuration : null,"
            "  shineName: after ? after.animationName : null,"
            "  shineBg: after ? after.backgroundImage : '',"
            "  shineDelay: after ? after.animationDelay : null,"
            "  originDelayStr: originDelayStr,"
            "  maxDelay: maxDelay, originDelay: originDelay,"
            "  perspective: getComputedStyle(document.getElementById('msBoard')).perspective }; }")
        check('A3. ново-открытые клетки получили класс переворота',
              info['flips'] >= 1 and info['revealed'] >= 1, info)
        check('A4. анимация клетки — msCellFlip 0.45s',
              info['animName'] == 'msCellFlip' and info['animDur'] == '0.45s', info)
        check('A5. блик по глянцу: ::after msCellShine + линейный градиент',
              info['shineName'] == 'msCellShine' and
              'linear-gradient' in info['shineBg'] and
              'rgba(255, 255, 255, 0.55)' in info['shineBg'], info)
        check('A6. блик ждёт свой переворот: delay наследуется (::after == клетке)',
              info['shineDelay'] == info['originDelayStr'],
              {'shine': info['shineDelay'], 'cell': info['originDelayStr']})
        check('A7. волна задержек: эпицентр 0с, дальние > 0',
              info['originDelay'] == 0 and info['maxDelay'] > 0,
              {'origin': info['originDelay'], 'max': info['maxDelay']})
        check('A8. перспектива поля включена (900px)',
              info['perspective'] == '900px', info['perspective'])
        vibes = page.evaluate("() => window.__vibes")
        check('A9. вибрация отклика клетки — 12 мс', 12 in vibes, vibes[:5])
        shot(page, '01-mobile-flip-wave-dark.png')
        page.wait_for_timeout(700)   # дождаться конца волны

        # --- блок «Архив партий» (мок getMyArchive) ---
        arch = page.evaluate(
            "() => { const b = document.getElementById('msSrvArchive');"
            " const row = document.getElementById('msSrvRow');"
            " return { display: b ? getComputedStyle(b).display : 'none',"
            "  slots: row ? row.children.length : 0,"
            "  wins: row ? row.querySelectorAll('.ms-ach-slot.win').length : 0,"
            "  losses: row ? row.querySelectorAll('.ms-ach-slot.loss').length : 0,"
            "  empty: row ? row.querySelectorAll('.ms-ach-slot.empty').length : 0,"
            "  stat: (document.getElementById('msSrvStat') || {}).textContent || '' }; }")
        check('A10. блок «Архив партий» видим', arch['display'] != 'none', arch)
        check('A11. строка архива — 5 слотов (3 данных + 2 пустых)',
              arch['slots'] == 5 and arch['empty'] == 2, arch)
        check('A12. слоты побед/поражений: 2 ✓ / 1 ✗',
              arch['wins'] == 2 and arch['losses'] == 1, arch)
        check('A13. статистика «3 партий · 2 побед»',
              '3' in arch['stat'] and '2' in arch['stat'] and
              'партий' in arch['stat'] and 'побед' in arch['stat'], arch['stat'])
        dates = page.evaluate(
            "() => [...document.querySelectorAll('#msSrvRow .ms-ach-date')].map(e => e.textContent)")
        check('A14. даты в слотах архива', any(d and d != '—' for d in dates), dates)
        shot(page, '02-mobile-archive-block.png')

        # --- взрыв: вибрация [80,60,120], оверлей ЗАДЕРЖАН ---
        mine = page.evaluate(find_mine())
        check('A15. мина на поле найдена', mine is not None, mine)
        page.evaluate("([r, c]) => msReveal(r, c)", mine)
        page.wait_for_timeout(150)
        early = page.evaluate(
            "() => ({ overlay: getComputedStyle(document.getElementById('msOverlay')).display,"
            "  flips: document.querySelectorAll('.ms-cell.ms-cell-flip').length,"
            "  face: document.getElementById('msFaceBtn').textContent })")
        check('A16. взрыв: оверлей ещё СКРЫТ (волна мин отыгрывает)',
              early['overlay'] == 'none', early)
        check('A17. мины в очереди переворота (от эпицентра взрыва)',
              early['flips'] >= 10, early['flips'])
        check('A18. лицо — 💥😵 после взрыва', early['face'] == '😵', early['face'])
        vibes2 = page.evaluate("() => window.__vibes")
        check('A19. вибрация взрыва [80,60,120]',
              [80, 60, 120] in vibes2, vibes2[-3:])
        page.wait_for_timeout(900)   # 750 мс задержка оверлея
        late = page.evaluate(
            "() => ({ overlay: getComputedStyle(document.getElementById('msOverlay')).display,"
            "  text: document.getElementById('msGameOverText').textContent })")
        check('A20. оверлей взрыва появился после волны (750 мс)',
              late['overlay'] == 'flex' and 'Взрыв' in late['text'], late)
        shot(page, '03-mobile-explosion-overlay.png')
        check('A21. recordResult ушёл на сервер (поражение)',
              SERVER_CALLS.count('minesweeper.recordResult') >= 1,
              SERVER_CALLS)

        # --- победа: [40,40,40,40,100], оверлей 650 мс, авто-флаги ---
        # (сначала msReveal — только ПЕРВЫЙ клик расставляет мины; поле
        # после msInit пустое, без мин «вскрыть всё» не даст победы)
        page.evaluate(
            "() => { msInit(); msReveal(4, 4);"
            " for (let r = 0; r < msRows; r++)"
            " { for (let c = 0; c < msCols; c++) { if (msBoard[r][c] !== -1)"
            " msRevealed[r][c] = true; } } msCheckWin(); return true; }")
        page.wait_for_timeout(150)
        win_early = page.evaluate(
            "() => getComputedStyle(document.getElementById('msOverlay')).display")
        check('A22. победа: оверлей задержан (650 мс)', win_early == 'none', win_early)
        page.wait_for_timeout(800)
        win = page.evaluate(
            "() => ({ overlay: getComputedStyle(document.getElementById('msOverlay')).display,"
            "  text: document.getElementById('msGameOverText').textContent,"
            "  flags: document.querySelectorAll('.ms-cell-flagged').length })")
        check('A23. оверлей победы после волны',
              win['overlay'] == 'flex' and 'Победа' in win['text'], win)
        check('A24. авто-флаги на все мины (10)', win['flags'] == 10, win['flags'])
        vibes3 = page.evaluate("() => window.__vibes")
        check('A25. вибрация победы [40,40,40,40,100]',
              [40, 40, 40, 40, 100] in vibes3, vibes3[-2:])
        check('A26. победа тоже ушла в архив',
              SERVER_CALLS.count('minesweeper.recordResult') >= 2, SERVER_CALLS)
        shot(page, '04-mobile-win-overlay.png')
        check('A27. весь мобильный сценарий — 0 JS-ошибок',
              len(errors) == 0, errors[:5])
        ctx.close()

        # ================= B. БЕЗ СЕРВЕРНОГО МОДУЛЯ =================
        print('== B. МОБИЛЬНЫЙ — сервер без minesweeper.* (500) ==')
        errors_b = []
        SERVER_CALLS.clear()
        ctx_b, page_b = make_page(browser, 390, 844, True, errors_b,
                                  no_minesweeper=True)
        open_sweeper(page_b)
        page_b.wait_for_timeout(800)
        arch_b = page_b.evaluate(
            "() => getComputedStyle(document.getElementById('msSrvArchive')).display")
        check('B1. блок архива скрыт (модуля нет — тихо)', arch_b == 'none', arch_b)
        page_b.evaluate("() => msReveal(4, 4)")   # старт партии: мины расставлены
        page_b.wait_for_timeout(100)
        mine_b = page_b.evaluate(
            "() => { for (let r = 0; r < msRows; r++) { for (let c = 0; c < msCols; c++)"
            " { if (msBoard[r][c] === -1) return [r, c]; } } return null; }")
        page_b.evaluate("([r, c]) => msReveal(r, c)", mine_b)
        page_b.wait_for_timeout(900)
        ov_b = page_b.evaluate(
            "() => getComputedStyle(document.getElementById('msOverlay')).display")
        check('B2. игра жива: взрыв отработал, оверлей есть', ov_b == 'flex', ov_b)
        check('B3. запись в архив молча не удалась — игра не упала',
              len(errors_b) == 0, errors_b[:5])
        shot(page_b, '05-mobile-no-server-module.png')
        ctx_b.close()

        # ================= C. REDUCED MOTION =================
        print('== C. МОБИЛЬНЫЙ — prefers-reduced-motion ==')
        errors_c = []
        ctx_c, page_c = make_page(browser, 390, 844, True, errors_c, reduced=True)
        open_sweeper(page_c)
        page_c.tap('#msBoard .ms-cell')
        page_c.wait_for_timeout(150)
        rm = page_c.evaluate(
            "() => { const f = document.querySelector('.ms-cell.ms-cell-flip');"
            " if (!f) return { present: false };"
            " return { present: true,"
            "  anim: getComputedStyle(f).animationName,"
            "  shine: getComputedStyle(f, '::after').animationName,"
            "  content: getComputedStyle(f, '::after').content }; }")
        check('C1. клетка открылась (класс есть)', rm['present'], rm)
        check('C2. анимация переворота ОТКЛЮЧЕНА', rm['anim'] == 'none', rm)
        check('C3. блик отключён (animation none / content none)',
              rm['shine'] == 'none' or rm['content'] == 'none', rm)
        check('C4. reduced-motion — 0 JS-ошибок', len(errors_c) == 0, errors_c[:3])
        ctx_c.close()

        # ================= D. ДЕСКТОП 1280×800 =================
        print('== D. ДЕСКТОП 1280×800 (мышь + светлая тема) ==')
        errors_d = []
        ctx_d, page_d = make_page(browser, 1280, 800, False, errors_d)
        open_sweeper(page_d)
        check('D1. десктоп: нет JS-ошибок', len(errors_d) == 0, errors_d[:3])
        page_d.click('#msBoard .ms-cell')
        page_d.wait_for_timeout(120)
        flip_d = page_d.evaluate(
            "() => { const f = document.querySelector('.ms-cell.ms-cell-flip');"
            " if (!f) return null;"
            " const a = getComputedStyle(f, '::after');"
            " return { anim: getComputedStyle(f).animationName,"
            "  shine: a.animationName, bg: a.backgroundImage }; }")
        check('D2. клик мышью — переворот с бликом',
              flip_d and flip_d['anim'] == 'msCellFlip' and
              flip_d['shine'] == 'msCellShine' and
              'linear-gradient' in flip_d['bg'], flip_d)
        arch_d = page_d.evaluate(
            "() => ({ display: getComputedStyle(document.getElementById('msSrvArchive')).display,"
            "  slots: document.getElementById('msSrvRow').children.length })")
        check('D3. десктоп: блок архива видим, 5 слотов',
              arch_d['display'] != 'none' and arch_d['slots'] == 5, arch_d)
        shot(page_d, '06-desktop-dark.png')

        # светлая тема: вскрыть ещё НЕ открытую клетку — новые флипы
        page_d.evaluate("document.documentElement.setAttribute('data-theme','light')")
        page_d.wait_for_timeout(300)
        light = page_d.evaluate(
            "() => { const b = document.getElementById('msBoard');"
            " for (let r = 0; r < msRows; r++) { for (let c = 0; c < msCols; c++) {"
            "   if (!msRevealed[r][c] && msBoard[r][c] !== -1) { msReveal(r, c); break; } } }"
            " const f = b.querySelector('.ms-cell.ms-cell-flip');"
            " const loss = document.querySelector('#msSrvRow .ms-ach-slot.loss');"
            " return f ? { bg: getComputedStyle(f, '::after').backgroundImage,"
            "  lossBg: loss ? getComputedStyle(loss).backgroundColor : '' } : null; }")
        page_d.wait_for_timeout(400)
        check('D4. светлая тема: блик задан (контрастнее)',
              light and 'rgba(255, 255, 255, 0.85)' in light['bg'], light)
        check('D5. светлая тема: слот поражения окрашен',
              light and 'rgba(184, 58, 58' in light['lossBg'], light)
        shot(page_d, '07-desktop-light.png')
        check('D6. десктоп весь — 0 JS-ошибок', len(errors_d) == 0, errors_d[:5])
        ctx_d.close()

    httpd.shutdown()
    print()
    print('ИТОГО: %d OK, %d FAIL' % (PASS, FAIL))
    raise SystemExit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
