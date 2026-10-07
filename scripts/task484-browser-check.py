#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 484: browser-check — Графики КИП ИОС → вкладка «Блокировки»:
#  A) ТАБЛИЦА «как в Excel» (= вид «Приборы», Task 483): шапка «Вид
#     обслуживания» (2×2) + титул «Количество БЛОКИРОВОК по графику
#     ППР по месяцам на 2026 год»; месяцы I–XII (пастели: I/V/IX/XII
#     #FFB9B9, VI-VIII #FFDB69, прочие белые); бейджи Кр/ТО
#     (#8DB4E2/#C3D69B — Кр в ветке accent1, как «К» приборов);
#     строки с оттенками (#DBEEF4/#EBF1DE); 24 значения ==
#     data/lockouts.json ppr_chart;
#  B) ДИАГРАММА: 12 групп по 2 столбца (Кр #4F81BD однотонный, ТО —
#     горизонтальная штриховка), 24 подписи над столбцами (нулей в
#     текущих данных нет), высоты пропорциональны (макс ТО 205);
#  C) ВЫРАВНИВАНИЕ: центр группы == центр колонки месяца (±3px);
#  D) ЛОГИКА: числа == ppr_chart (снимок lockouts.json; счётчик =
#     метка месяца == Кр/ТО И «Наличие в перечне и в ППР» = «Есть»);
#     итоги Кр 503 / ТО 1509 (без фильтра было бы 531/1593);
#  E) ФОЛБЭК: lockouts.json БЕЗ ppr_chart → сообщение про
#     блокировки (перехват fetch);
#  F) светлая тема: карточка БЕЛАЯ в обеих темах;
#  G) «УБРАНО ВСЁ ЛИШНЕЕ»: старый график ППР (.ppr-chart-card),
#     сводная статистика (.chart-stats-grid) и Топ-10 (.chart-bar-row)
#     на вкладке «Блокировки» НЕ рендерятся.
# КОНТЕКСТ: Electron UA (модуль charts-desktop.js — только десктоп),
# мок Apps Script (Админ), порт 8995, 0 JS-ошибок, скриншоты.
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8995
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task484')
os.makedirs(SHOT_DIR, exist_ok=True)

ELECTRON_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) kip8-desktop/1.0 Chrome/124.0.0.0 '
               'Safari/537.36 Electron/25.3.2')

# Эталонные данные — из data/lockouts.json (тот же файл, что отдаёт сервер)
with open(os.path.join(REPO, 'data', 'lockouts.json'), encoding='utf-8') as f:
    PPR = json.load(f)['ppr_chart']
SERIES = {s['code']: s['values'] for s in PPR['series']}
NAMES = {s['code']: s['name'] for s in PPR['series']}

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
          (('  [' + str(extra)[:200] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def serve():
    os.chdir(REPO)

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

    httpd = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    httpd.serve_forever()


def attach(page, ctx, theme, tag):
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        if action == 'getCurrentUser':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                        'role': 'Админ'}}, ensure_ascii=False))
        if action == 'getMyAccess':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'role': 'Админ', 'found': True,
                        'permissions': {'kipios.view': True, 'charts.view': True,
                            'workschedule.view': True}}}, ensure_ascii=False))
        if action == 'heartbeat':
            return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))
        return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                             body=json.dumps({'ok': True, 'data': {'ok': True}}, ensure_ascii=False))

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (t484-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "try{if(window.navigator.serviceWorker){navigator.serviceWorker.getRegistrations()" +
        ".then(function(rs){rs.forEach(function(r){r.unregister();});});}}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t484-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors


# --- Снимок DOM для проверок (одним evaluate) ---
SNAPSHOT_JS = r"""(() => {
    const card = document.querySelector('.ppr-tc-card');
    if (!card) return {error: 'карточка не найдена'};
    const q = s => [...card.querySelectorAll(s)];
    const bg = el => {
        const c = getComputedStyle(el).backgroundColor;
        const m = c.match(/rgba?\(([^)]+)\)/);
        return m ? m[1] : c;
    };
    const months = q('.ppr-tc-m');
    const names = q('.ppr-tc-name');
    const badges = q('.ppr-tc-badge');
    const vals = q('.ppr-tc-v');
    // порядок значений: Кр, ТО по 12 подряд (CSS-сетка)
    const groups = q('.ppr-tc-g');
    return {
        title: (card.querySelector('.ppr-tc-title') || {}).textContent || '',
        vo: (card.querySelector('.ppr-tc-vo') || {}).textContent || '',
        months: months.map(m => ({t: m.textContent.trim(), bg: bg(m),
                                  x: m.getBoundingClientRect().x,
                                  w: m.getBoundingClientRect().width})),
        rows: names.map((n, i) => ({
            name: n.textContent.trim(), bg: bg(n),
            badge: badges[i] ? {t: badges[i].textContent.trim(), bg: bg(badges[i])} : null,
            values: vals.slice(i * 12, i * 12 + 12).map(v => v.textContent.trim()),
            valsBg: bg(vals[i * 12])
        })),
        groups: groups.map(g => {
            const r = g.getBoundingClientRect();
            const bcells = [...g.querySelectorAll('.ppr-tc-bcell')];
            return {x: r.x, w: r.width,
                    bcells: bcells.map(bc => {
                        const bar = bc.querySelector('.ppr-tc-bar');
                        if (!bar) return {zero: true};
                        const br = bar.getBoundingClientRect();
                        return {h: br.height,
                                bg: getComputedStyle(bar).backgroundColor,
                                img: getComputedStyle(bar).backgroundImage,
                                val: bar.querySelector('.ppr-tc-val') ?
                                     bar.querySelector('.ppr-tc-val').textContent.trim() : null};
                    })};
        }),
        cardBg: bg(card),
        valLabels: q('.ppr-tc-val').length,
        zeroLabels: q('.ppr-tc-val-zero').length,
        solidBars: q('.ppr-tc-bar:not(.ppr-tc-hatch)').length,
        hatchBars: q('.ppr-tc-bar.ppr-tc-hatch').length,
        note: card.querySelector('.ppr-tc-empty-note') ?
              card.querySelector('.ppr-tc-empty-note').textContent.trim() : null
    };
})()"""

GONE_JS = r"""(() => ({
    oldChart: !!document.querySelector('.ppr-chart-card'),
    statsGrid: !!document.querySelector('.chart-stats-grid'),
    top10: !!document.querySelector('.chart-bar-row'),
    tabActive: (document.querySelector('.charts-tab-active') || {})
               .getAttribute('data-chart-tab') || ''
}))()"""


def open_lockouts(ctx, page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('charts')")
    page.wait_for_timeout(1500)
    page.evaluate("KipCharts.switchTab('lockouts')")
    page.wait_for_timeout(2500)


def main():
    server = HTTPServer(('127.0.0.1', PORT), lambda *a, **k: None)
    server.server_close()  # заглушка; настоящий — ниже
    threading.Thread(target=serve, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A-D+G: ДЕСКТОП 1400x900, Electron UA, тёмная тема ==')
        ctx = browser.new_context(viewport={'width': 1400, 'height': 900},
                                  user_agent=ELECTRON_UA)
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'main')
        open_lockouts(ctx, page)

        check('вкладка «Блокировки» активна',
              page.evaluate("(() => {const t=document.querySelector('.charts-tab-active');"
                            "return !!t && t.getAttribute('data-chart-tab')==='lockouts';})()"))
        check('loading сменился контентом (не «Загрузка…»)',
              'Загрузка' not in (page.evaluate(
                  "document.getElementById('chartsContent').textContent") or ''))

        snap = page.evaluate(SNAPSHOT_JS)
        check('карточка отрисована', 'error' not in snap, snap.get('error'))

        # --- G. «Убрано всё лишнее» (заявка) ---
        gone = page.evaluate(GONE_JS)
        check('G: старый график ППР (.ppr-chart-card) НЕ рендерится',
              not gone['oldChart'])
        check('G: сводная статистика (.chart-stats-grid) НЕ рендерится',
              not gone['statsGrid'])
        check('G: Топ-10 (.chart-bar-row) НЕ рендерится',
              not gone['top10'])

        # --- A. Таблица ---
        check('титул: «Количество БЛОКИРОВОК по графику ППР по месяцам на 2026 год»',
              snap['title'].strip() == 'Количество БЛОКИРОВОК по графику ППР по месяцам на 2026 год',
              repr(snap['title']))
        check('шапка «Вид обслуживания»', snap['vo'].strip() == 'Вид обслуживания',
              repr(snap['vo']))
        ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
        check('месяцы I–XII в шапке',
              [m['t'] for m in snap['months']] == ROMANS,
              [m['t'] for m in snap['months']])

        PINK = '255, 185, 185'
        GOLD = '255, 219, 105'
        WHITE = '255, 255, 255'
        pink_idx = [0, 4, 8, 11]
        gold_idx = [5, 6, 7]
        check('пастели: I/V/IX/XII розовые #FFB9B9',
              all(snap['months'][i]['bg'] == PINK for i in pink_idx),
              [(ROMANS[i], snap['months'][i]['bg']) for i in pink_idx])
        check('пастели: VI/VII/VIII золотые #FFDB69',
              all(snap['months'][i]['bg'] == GOLD for i in gold_idx),
              [(ROMANS[i], snap['months'][i]['bg']) for i in gold_idx])
        check('пастели: II/III/IV/X/XI белые',
              all(snap['months'][i]['bg'] == WHITE for i in range(12)
                  if i not in pink_idx + gold_idx))

        check('2 строки: Кан. ремонт / Тех. обслуж.',
              [r['name'] for r in snap['rows']] == [NAMES['Кр'], NAMES['ТО']],
              [r['name'] for r in snap['rows']])
        BADGE = {'Кр': ('141, 180, 226'), 'ТО': ('195, 214, 155')}
        ROWBG = {'Кр': '219, 238, 244', 'ТО': '235, 241, 222'}
        for i, code in enumerate(['Кр', 'ТО']):
            check('бейдж %s: код + цвет accent' % code,
                  snap['rows'][i]['badge'] and
                  snap['rows'][i]['badge']['t'] == code and
                  snap['rows'][i]['badge']['bg'] == BADGE[code],
                  snap['rows'][i]['badge'])
            check('оттенок строки %s: %s' % (code, ROWBG[code]),
                  snap['rows'][i]['bg'] == ROWBG[code] and
                  snap['rows'][i]['valsBg'] == ROWBG[code],
                  (snap['rows'][i]['bg'], snap['rows'][i]['valsBg']))

        # --- D. Логика: значения == ppr_chart (снимок lockouts.json) ---
        for i, code in enumerate(['Кр', 'ТО']):
            expected = [str(v) for v in SERIES[code]]
            check('значения строки %s == ppr_chart (%s…)' % (code, expected[:3]),
                  snap['rows'][i]['values'] == expected,
                  (snap['rows'][i]['values'], expected))

        # контроль ключевых чисел логики (снимок Task 484):
        # фильтр «Наличие в перечне и в ППР» = «Есть»: Кр 503, ТО 1509
        # (без фильтра было бы 531/1593; старые заШитые _PPR_LOCKOUTS
        # — Кр 526/ТО 1578 — не соответствовали ничему)
        tot = {c: sum(SERIES[c]) for c in ('Кр', 'ТО')}
        check('логика «Есть»-фильтра: итоги Кр 503 / ТО 1509',
              tot == {'Кр': 503, 'ТО': 1509}, tot)

        # --- B. Диаграмма ---
        check('12 групп столбцов', len(snap['groups']) == 12)
        check('24 столбца: 12 однотонных Кр + 12 штрихованных ТО',
              snap['solidBars'] == 12 and snap['hatchBars'] == 12,
              (snap['solidBars'], snap['hatchBars']))
        check('24 подписи значений над столбцами (нулей нет)',
              snap['valLabels'] == 24 and snap['zeroLabels'] == 0,
              (snap['valLabels'], snap['zeroLabels']))

        BLUE = 'rgb(79, 129, 189)'
        kr_bars = [g['bcells'][0] for g in snap['groups']]
        to_bars = [g['bcells'][1] for g in snap['groups']]
        check('цвета столбцов: Кр #4F81BD (все 12, accent1)',
              all('bg' in b and b['bg'] == BLUE for b in kr_bars),
              [b.get('bg') for b in kr_bars[:3]])
        check('штриховка ТО: repeating-linear-gradient (все 12)',
              all('img' in b and 'repeating-linear-gradient' in b['img'] for b in to_bars),
              [b.get('img', '')[:60] for b in to_bars[:2]])

        # высоты: максимум ТО = 205 (III) → самая высокая; пропорции
        to3 = to_bars[2]  # месяц III
        max_h = max(b['h'] for g in snap['groups'] for b in g['bcells'] if 'h' in b)
        check('масштаб: столбец ТО/III (макс 205) — самый высокий',
              to3['h'] == max_h, (to3['h'], max_h))
        ratio_ok = all(
            'h' in to_bars[m] and
            abs(to_bars[m]['h'] / to3['h'] - SERIES['ТО'][m] / 205.0) < 0.02
            for m in range(12))
        check('пропорции высот ТО ≈ значение/макс (все 12, ±2%)', ratio_ok)

        # подписи == значения
        labels_ok = all(
            'val' in kr_bars[m] and kr_bars[m]['val'] == str(SERIES['Кр'][m])
            for m in range(12)) and all(
            'val' in to_bars[m] and to_bars[m]['val'] == str(SERIES['ТО'][m])
            for m in range(12))
        check('подписи над столбцами == значениям ppr_chart', labels_ok)

        # --- C. Выравнивание: группы под колонками месяцев ---
        for i in (0, 3, 5, 8, 11):
            mx = snap['months'][i]['x'] + snap['months'][i]['w'] / 2
            gx = snap['groups'][i]['x'] + snap['groups'][i]['w'] / 2
            check('выравнивание %s: центр группы == центр колонки (±3px)' % ROMANS[i],
                  abs(mx - gx) <= 3, (mx, gx))

        check('карточка БЕЛАЯ в тёмной теме (документ-вид)',
              snap['cardBg'] == '255, 255, 255', snap['cardBg'])

        shot(page, 'a-desk-dark-full.png')
        card = page.query_selector('.ppr-tc-card')
        if card:
            card.screenshot(path=os.path.join(SHOT_DIR, 'a-desk-dark-card.png'))

        check('0 JS-ошибок (тёмная)', not js_errors, js_errors[:3])
        ctx.close()

        # ==============================================================
        print('== F: СВЕТЛАЯ тема (быстрая проверка) ==')
        ctx2 = browser.new_context(viewport={'width': 1400, 'height': 900},
                                   user_agent=ELECTRON_UA, color_scheme='light')
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'light')
        open_lockouts(ctx2, page2)
        snap2 = page2.evaluate(SNAPSHOT_JS)
        check('светлая: карточка отрисована', 'error' not in snap2)
        check('светлая: карточка ТАК ЖЕ белая (Excel-вид в обеих темах)',
              snap2.get('cardBg') == '255, 255, 255', snap2.get('cardBg'))
        check('светлая: значения те же (2 серии × 12)',
              len(snap2['rows']) == 2 and all(len(r['values']) == 12 for r in snap2['rows']))
        check('светлая: пастели месяцев те же',
              all(snap2['months'][i]['bg'] == PINK for i in pink_idx) and
              all(snap2['months'][i]['bg'] == GOLD for i in gold_idx))
        shot(page2, 'f-desk-light-full.png')
        check('0 JS-ошибок (светлая)', not js_errors2, js_errors2[:3])
        ctx2.close()

        # ==============================================================
        print('== E: ФОЛБЭК — lockouts.json без ppr_chart ==')
        ctx3 = browser.new_context(viewport={'width': 1400, 'height': 900},
                                   user_agent=ELECTRON_UA)
        page3 = ctx3.new_page()
        js_errors3 = attach(page3, ctx3, 'dark', 'fb')

        def strip_ppr(route, request):
            if 'data/lockouts.json' in request.url:
                data = json.loads(open(os.path.join(REPO, 'data', 'lockouts.json'),
                                       encoding='utf-8').read())
                data.pop('ppr_chart', None)
                return route.fulfill(status=200, content_type='application/json; charset=utf-8',
                                     body=json.dumps(data, ensure_ascii=False))
            return route.continue_()

        ctx3.route('**/data/lockouts.json*', strip_ppr)
        open_lockouts(ctx3, page3)
        snap3 = page3.evaluate(SNAPSHOT_JS)
        check('фолбэк: карточка-таблица НЕ отрисована',
              'error' in snap3 or not snap3.get('rows'))
        note = page3.evaluate(
            "((document.querySelector('.ppr-tc-empty-note')||{}).textContent||'').trim()")
        check('фолбэк: сообщение про блокировки и синхронизацию',
              'Данные графика ППР' in note and 'блокировкам' in note
              and 'синхронизация' in note, repr(note))
        shot(page3, 'e-fallback.png')
        check('0 JS-ошибок (фолбэк)', not js_errors3, js_errors3[:3])
        ctx3.close()

        browser.close()

    print('\n════ ИТОГ: %d passed, %d failed ════' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
