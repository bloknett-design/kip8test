#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 485: browser-check — Графики КИП ИОС:
#  A) «Блокировки»: серия Кр — «Кап. ремонт» (заявка: не «Кан.»);
#     таблица+диаграмма ППР как в 484;
#  B) «Клапана»: 3 КРУГОВЫЕ диаграммы (по типам / по Ду / футирован-
#     ные), стиль Приборов/Блокировок (белая .ppr-tc-card); НЕТ
#     старого (сводная статистика .chart-stats-grid, Топ-10
#     .chart-bar-row); значения легенды == пересчёту из
#     data/valves.json; «Клапана» (прочие) — строка с 0;
#  C) «Регуляторы»: 3 круговые (производства / устройства /
#     параметры-величины); значения == пересчёту из
#     data/regulators.json; категории параметров — 8 известных;
#  D) SVG-пироги: сектора path/circle, белые разделители, проценты
#     у крупных секторов, легенда со свотчами;
#  E) светлая тема: карточка БЕЛАЯ в обеих темах;
#  F) 0 JS-ошибок; скриншоты.
# КОНТЕКСТ: Electron UA (charts-desktop.js — только десктоп),
# мок Apps Script (Админ), порт 8999.
import json
import os
import re
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task485')
os.makedirs(SHOT_DIR, exist_ok=True)

ELECTRON_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) kip8-desktop/1.0 Chrome/124.0.0.0 '
               'Safari/537.36 Electron/25.3.2')

# --- Эталоны: пересчёт из data/*.json (те же правила, что в модуле) ---
VALVES = json.load(open(os.path.join(REPO, 'data', 'valves.json'),
                        encoding='utf-8'))['valves']
REGS = json.load(open(os.path.join(REPO, 'data', 'regulators.json'),
                      encoding='utf-8'))['regulators']
LOCKOUTS = json.load(open(os.path.join(REPO, 'data', 'lockouts.json'),
                          encoding='utf-8'))['ppr_chart']

TIP = 'Тип, пропускная характеристика'
ZAP = 'Тип запорной части. Материал затвора/ корпуса'
DN = 'DN (мм)'
PAR = 'Параметр'
PROD = 'Производство'
UST = 'Устроиство регулятора или ручного управления'


def valve_types():
    t = {'Отсечные': 0, 'Регулирующие': 0, 'Дисковые затворы': 0, 'Клапана': 0}
    for it in VALVES:
        tip = (it.get(TIP) or '').lower()
        zap = (it.get(ZAP) or '').lower()
        if 'дисков' in zap:
            t['Дисковые затворы'] += 1
        elif 'отс' in tip:
            t['Отсечные'] += 1
        elif 'рег' in tip:
            t['Регулирующие'] += 1
        else:
            t['Клапана'] += 1
    return t


def valve_dn():
    m = {}
    for it in VALVES:
        v = (it.get(DN) or '').strip()
        k = 'Ду не указан' if (not v or v == '?') else ('Ду ' + v)
        m[k] = m.get(k, 0) + 1
    return m


def valve_fut():
    fut = sum(1 for it in VALVES
              if 'футирован' in (it.get(ZAP) or '').lower()
              or 'футерован' in (it.get(ZAP) or '').lower())
    return {'Футированные': fut, 'Не футированные': len(VALVES) - fut}


REG_RULES = [
    ('Температура', re.compile(r'температур|\btic\b', re.I)),
    ('Давление', re.compile(r'давлени|давылен', re.I)),
    ('Уровень', re.compile(r'уровен|уровн', re.I)),
    ('Расход', re.compile(r'расход|\bfirc\b|дозировк', re.I)),
    ('Концентрация', re.compile(r'концентрац', re.I)),
    ('Частота (ЧП)', re.compile(r'частот|чп', re.I)),
    ('Ручное управление', re.compile(r'ручн', re.I)),
]


def reg_params():
    m = {}
    for r in REGS:
        v = r.get(PAR) or ''
        cat = 'Прочие'
        for name, rx in REG_RULES:
            if rx.search(v):
                cat = name
                break
        m[cat] = m.get(cat, 0) + 1
    return m


def count_field(field):
    m = {}
    for r in REGS:
        v = (r.get(field) or '').strip()
        if v:
            m[v] = m.get(v, 0) + 1
    return m


VT = valve_types()
VD = valve_dn()
VF = valve_fut()
RP = reg_params()
RPR = count_field(PROD)
RUS = count_field(UST)
KR_NAME = LOCKOUTS['series'][0]['name']

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
                      body='not found (t485-%s)' % tag)

    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)
    ctx.add_init_script(
        "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
        "try{localStorage.removeItem('kip8test:kip8_session_token')}catch(e){};" +
        "try{if(window.navigator.serviceWorker){navigator.serviceWorker.getRegistrations()" +
        ".then(function(rs){rs.forEach(function(r){r.unregister();});});}}catch(e){};" +
        "localStorage.setItem('kip8test:kip8_session_token','bc-t485-%s');" % tag +
        "localStorage.setItem('kip8test:app-theme','%s');" % theme)
    return js_errors


# Снимок вкладки «Клапана»/«Регуляторы» (карточки-пироги)
PIES_JS = r"""(() => {
    const cards = [...document.querySelectorAll('#chartsContent .ppr-tc-card')];
    const bg = el => { const c = getComputedStyle(el).backgroundColor;
                       const m = c.match(/rgba?\(([^)]+)\)/); return m ? m[1] : c; };
    return cards.map(card => ({
        title: (card.querySelector('.pc-title') || {}).textContent || '',
        cardBg: bg(card),
        svg: !!card.querySelector('svg.pc-svg'),
        paths: card.querySelectorAll('svg.pc-svg path').length,
        circles: card.querySelectorAll('svg.pc-svg circle').length,
        sliceLbls: card.querySelectorAll('.pc-slice-lbl').length,
        legend: [...card.querySelectorAll('.pc-li')].map(li => ({
            name: (li.querySelector('.pc-name') || {}).textContent || '',
            cnt: (li.querySelector('.pc-cnt') || {}).textContent || '',
            pct: (li.querySelector('.pc-pct') || {}).textContent || '',
            swatchBg: bg(li.querySelector('.pc-swatch'))
        }))
    }));
})()"""

GONE_JS = r"""(() => ({
    oldChart: !!document.querySelector('.ppr-chart-card'),
    statsGrid: !!document.querySelector('.chart-stats-grid'),
    top10: !!document.querySelector('.chart-bar-row'),
    oldCardCss: !!document.querySelector('.chart-card'),
    tabActive: (document.querySelector('.charts-tab-active') || {})
               .getAttribute('data-chart-tab') || ''
}))()"""


def open_tab(page, tab):
    page.evaluate("navigateTo('charts')")
    page.wait_for_timeout(900)
    page.evaluate("KipCharts.switchTab('%s')" % tab)
    page.wait_for_timeout(1600)


def main():
    server = HTTPServer(('127.0.0.1', PORT), lambda *a, **k: None)
    server.server_close()
    threading.Thread(target=serve, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ==============================================================
        print('== A: БЛОКИРОВКИ — «Кап. ремонт» (тёмная тема) ==')
        ctx = browser.new_context(viewport={'width': 1400, 'height': 900},
                                  user_agent=ELECTRON_UA)
        page = ctx.new_page()
        js_errors = attach(page, ctx, 'dark', 'main')
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_tab(page, 'lockouts')

        check('вкладка «Блокировки» активна',
              page.evaluate("((document.querySelector('.charts-tab-active')||{}).getAttribute('data-chart-tab')==='lockouts')"))
        body = page.evaluate("document.getElementById('chartsContent').textContent")
        check('серия Кр называется «Кап. ремонт»', 'Кап. ремонт' in body)
        check('опечатки «Кан.» больше нет', 'Кан.' not in body)
        check('таблица ППР жива (титул)',
              'Количество БЛОКИРОВОК по графику ППР' in body)
        check('24 значения Кр/ТО', page.evaluate(
            "document.querySelectorAll('.ppr-tc-v').length") == 24)
        check('прогрев: строка «Вид обслуживания»', 'Вид обслуживания' in body)
        shot(page, 'lockouts-kap-remont.png')

        # ==============================================================
        print('== B: КЛАПАНА — круговые (тёмная тема) ==')
        open_tab(page, 'valves')
        check('вкладка «Клапана» активна',
              page.evaluate("((document.querySelector('.charts-tab-active')||{}).getAttribute('data-chart-tab')==='valves')"))
        g = page.evaluate(GONE_JS)
        check('СТАРОГО НЕТ: сводная статистика', not g['statsGrid'])
        check('СТАРОГО НЕТ: Топ-10 бары', not g['top10'])
        check('СТАРОГО НЕТ: старый график ППР', not g['oldChart'])
        check('СТАРОГО НЕТ: класс .chart-card', not g['oldCardCss'])

        pies = page.evaluate(PIES_JS)
        check('три карточки-пирога', len(pies) == 3, len(pies))
        titles = [c['title'] for c in pies]
        check('титул 1: по типам', 'Количество КЛАПАНОВ по типам' in titles)
        check('титул 2: по Ду', 'Количество КЛАПАНОВ по Ду' in titles)
        check('титул 3: футированные', 'Количество футированных КЛАПАНОВ' in titles)

        # карточка 1 — типы
        c1 = pies[0]
        check('пирог 1: SVG + сектора', c1['svg'] and c1['paths'] == 3,
              (c1['paths'], c1['circles']))
        legend1 = {r['name']: int(r['cnt']) for r in c1['legend']}
        check('типы: Отсечные == %d' % VT['Отсечные'], legend1.get('Отсечные') == VT['Отсечные'])
        check('типы: Регулирующие == %d' % VT['Регулирующие'],
              legend1.get('Регулирующие') == VT['Регулирующие'])
        check('типы: Дисковые затворы == %d' % VT['Дисковые затворы'],
              legend1.get('Дисковые затворы') == VT['Дисковые затворы'])
        check('типы: Клапана == %d (строка при 0)' % VT['Клапана'],
              legend1.get('Клапана') == VT['Клапана'] and 'Клапана' in legend1)
        check('типы: сумма == 320', sum(legend1.values()) == len(VALVES))
        check('карточка белая (документная)',
              c1['cardBg'].startswith('255, 255, 255'), c1['cardBg'])

        # карточка 2 — Ду
        c2 = pies[1]
        legend2 = {r['name']: int(r['cnt']) for r in c2['legend']}
        check('Ду: легенда == уникальным значениям (%d)' % len(VD),
              len(legend2) == len(VD))
        check('Ду: значения совпадают с пересчётом', legend2 == VD,
              {k: (legend2.get(k), VD.get(k)) for k in VD})
        check('Ду: подписи у крупных секторов', c2['sliceLbls'] >= 3, c2['sliceLbls'])

        # карточка 3 — футированные
        c3 = pies[2]
        legend3 = {r['name']: int(r['cnt']) for r in c3['legend']}
        check('футированные: %d/%d' % (VF['Футированные'], VF['Не футированные']),
              legend3 == VF)
        check('футированные: 2 сектора', c3['paths'] == 2)
        shot(page, 'valves-pies-dark.png')

        # ==============================================================
        print('== C: РЕГУЛЯТОРЫ — круговые (тёмная тема) ==')
        open_tab(page, 'regulators')
        g = page.evaluate(GONE_JS)
        check('СТАРОГО НЕТ и здесь', not g['statsGrid'] and not g['top10'])
        pies = page.evaluate(PIES_JS)
        check('три карточки-пирога', len(pies) == 3, len(pies))
        titles = [c['title'] for c in pies]
        check('титул 1: производства', 'Количество РЕГУЛЯТОРОВ по производствам' in titles)
        check('титул 2: устройства',
              'Количество РЕГУЛЯТОРОВ по устройствам (регулятора или ручного управления)' in titles)
        check('титул 3: параметры',
              'Количество РЕГУЛЯТОРОВ по параметрам (регулируемой величине)' in titles)

        legendP = {r['name']: int(r['cnt']) for r in pies[0]['legend']}
        check('производства: %d строк, значения == пересчёту' % len(RPR),
              legendP == RPR,
              {k: (legendP.get(k), RPR.get(k)) for k in list(RPR)[:5]})
        legendU = {r['name']: int(r['cnt']) for r in pies[1]['legend']}
        check('устройства: %d строк, значения == пересчёту' % len(RUS),
              legendU == RUS)
        legendA = {r['name']: int(r['cnt']) for r in pies[2]['legend']}
        check('параметры: значения == пересчёту', legendA == RP,
              {k: (legendA.get(k), RP.get(k)) for k in RP})
        check('параметры: сумма == 268', sum(legendA.values()) == len(REGS))
        rows = [r['name'] for r in pies[2]['legend']]
        check('параметры: «Прочие» — последняя строка', rows[-1] == 'Прочие')
        shot(page, 'regulators-pies-dark.png')

        check('JS-ошибок нет (тёмная)', not js_errors, js_errors[:3])
        ctx.close()

        # ==============================================================
        print('== D: СВЕТЛАЯ ТЕМА — карточки белые ==')
        ctx2 = browser.new_context(viewport={'width': 1400, 'height': 900},
                                   user_agent=ELECTRON_UA)
        page2 = ctx2.new_page()
        js_errors2 = attach(page2, ctx2, 'light', 'light')
        page2.goto('http://localhost:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        open_tab(page2, 'valves')
        pies = page2.evaluate(PIES_JS)
        check('клапана: карточка белая в светлой теме',
              all(c['cardBg'].startswith('255, 255, 255') for c in pies),
              [c['cardBg'] for c in pies])
        shot(page2, 'valves-pies-light.png')
        open_tab(page2, 'regulators')
        pies = page2.evaluate(PIES_JS)
        check('регуляторы: карточки белые в светлой теме',
              all(c['cardBg'].startswith('255, 255, 255') for c in pies))
        shot(page2, 'regulators-pies-light.png')
        check('JS-ошибок нет (светлая)', not js_errors2, js_errors2[:3])
        ctx2.close()

        browser.close()

    print('\n===== ИТОГО: %d passed / %d failed =====' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
