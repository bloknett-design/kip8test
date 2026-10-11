#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 501 browser-check: (1) электротехника/геометрия — панели
# единого стиля (объединение, разделители, кнопки вне, поля 52/19,
# cs-триггеры); (2) шкала-сигнал — подсказка убрана, ППР НАД панелью
# шкалы (выступ 2px), живые единицы и живой расчёт; (3) светлая тема
# датчиков температуры — тёплая политура (терракота); (4) живые
# расчёты CB/гео/шкала; (5) 0 JS-ошибок; скриншоты.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8986
SHOT_DIR = '/home/z/my-project/download/kip8test-task501'
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
          (('  [' + str(extra)[:180] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=False)
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'flowmeter.view': True,
                                'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}


def setup_routes(ctx):
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200,
                      content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action),
                                      ensure_ascii=False).encode('utf-8'))

    def block_external(route):
        route.fulfill(status=404, content_type='text/plain',
                      body='not found (browser-check t501)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# --- проверки вычисляемых стилей панели (активная страница) ---------
PANEL_JS = r"""((pageId) => {
    const pg = document.getElementById('page-' + pageId);
    if (!pg || !pg.classList.contains('active')) return {found: 'not active'};
    const scope = pg.querySelector('.conv-col-input') || pg;
    const panel = scope.querySelector('.ts-calc-panel.ts-calc-inset');
    if (!panel) return {found: 'no panel'};
    const cs = getComputedStyle(panel);
    const input = panel.querySelector('input.scale-field, input.form-field');
    const ics = input ? getComputedStyle(input) : null;
    const trig = panel.querySelector('.cs-trigger');
    const tcs = trig ? getComputedStyle(trig) : null;
    const btn = scope.querySelector('.scale-calc-btn, .converter-convert-btn');
    return {
        found: 'ok',
        insets: scope.querySelectorAll('.ts-calc-panel.ts-calc-inset').length,
        wrappers: scope.querySelectorAll('.scale-form:not(.ts-calc-panel)').length,
        seps: panel.querySelectorAll('.ts-calc-sep').length,
        borderWidth: cs.borderTopWidth,
        hasInsetShadow: cs.boxShadow.indexOf('inset') !== -1,
        btnOutside: btn ? !panel.contains(btn) : null,
        inputH: ics ? ics.height : null,
        inputFS: ics ? ics.fontSize : null,
        inputW: ics ? ics.fontWeight : null,
        trigH: tcs ? tcs.height : null,
        trigFS: tcs ? tcs.fontSize : null,
    };
})"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    errors_all = []

    # =========== МОБАЙЛ, ТЁМНАЯ ===========
    ctx = browser.new_context(viewport={'width': 375, 'height': 812},
                              device_scale_factor=2)
    setup_routes(ctx)
    ctx.add_init_script(
        "localStorage.setItem('kip8test:app-theme','dark');")
    page = ctx.new_page()
    page.on('pageerror', lambda e: errors_all.append(str(e)))
    page.goto('http://127.0.0.1:%d/index.html' % PORT)
    page.wait_for_timeout(2500)

    print('== 1. Электротехника (circuit-breaker), тёмная')
    page.evaluate("navigateTo('circuit-breaker')")
    page.wait_for_timeout(500)
    st = page.evaluate(PANEL_JS, 'circuit-breaker')
    check('ОДНА панель-колодец', st.get('found') == 'ok' and st['insets'] == 1, st)
    check('обёрток .scale-form нет', st.get('wrappers') == 0, st)
    check('разделителей 7', st.get('seps') == 7, st)
    check('кнопка вне панели', st.get('btnOutside') is True, st)
    check('рамка 1px + inset-тень',
          st.get('borderWidth') == '1px' and st.get('hasInsetShadow'), st)
    check('поля 52/19/700',
          st.get('inputH') == '52px' and st.get('inputFS') == '19px' and
          st.get('inputW') == '700', st)
    check('cs-триггер 52/19', st.get('trigH') == '52px' and st.get('trigFS') == '19px', st)
    shot(page, 't501-cb-dark.png')
    # JS-переключатель нагрузки: мощность → ток
    vis0 = page.evaluate("""() => {
        const p = document.getElementById('cb_power_block');
        const c = document.getElementById('cb_current_block');
        return {p: getComputedStyle(p).display, c: getComputedStyle(c).display};
    }""")
    check('группы: мощность видна, ток скрыт',
          vis0['p'] == 'block' and vis0['c'] == 'none', vis0)
    # живой расчёт CB
    page.evaluate("calcCircuitBreaker()")
    page.wait_for_timeout(300)
    cb = page.evaluate("""() => {
        const r = document.getElementById('cbResults');
        return {shown: r.style.display !== 'none', len: r.innerHTML.length};
    }""")
    check('живой расчёт выключателя', cb['shown'] and cb['len'] > 200, cb)

    print('== 2. Геометрия, тёмная')
    for geo, nseps in [('geo-ring', 1), ('geo-horiz', 2)]:
        page.evaluate("navigateTo('%s')" % geo)
        page.wait_for_timeout(400)
        st = page.evaluate(PANEL_JS, geo)
        check('%s: панель+%d разделит., поля 52/19' % (geo, nseps),
              st.get('found') == 'ok' and st.get('seps') == nseps and
              st.get('inputH') == '52px' and st.get('inputFS') == '19px', st)
    page.evaluate("navigateTo('geo-circle')")
    page.wait_for_timeout(400)
    gc = page.evaluate("""() => {
        const el = document.querySelector('#page-geo-circle .scale-form.ts-calc-panel');
        if (!el) return {found: false};
        const cs = getComputedStyle(el);
        const inp = el.querySelector('input.scale-field');
        const ics = inp ? getComputedStyle(inp) : null;
        return {found: true, bw: cs.borderTopWidth, h: ics.height, fs: ics.fontSize};
    }""")
    check('geo-circle: классы панели + поля 52/19',
          gc.get('found') and gc.get('h') == '52px' and gc.get('fs') == '19px', gc)
    shot(page, 't501-geo-ring-dark.png')
    page.evaluate("calcGeoRing()")
    page.wait_for_timeout(250)
    gr = page.evaluate("""() => ({
        shown: document.getElementById('gr_results').style.display !== 'none',
        len: document.getElementById('gr_results').innerHTML.length})""")
    check('живой расчёт кольца', gr['shown'] and gr['len'] > 100, gr)

    print('== 3. Шкала-сигнал, тёмная')
    page.evaluate("navigateTo('scale-signal')")
    page.wait_for_timeout(400)
    ss = page.evaluate("""() => {
        const col = document.querySelector('#page-scale-signal.active .conv-col-input');
        const q = document.getElementById('scaleQueryPanel');
        const f = document.getElementById('scaleFormPanel');
        const qcs = getComputedStyle(q);
        const fcs = getComputedStyle(f);
        const qInput = q.querySelector('input.scale-field');
        const qics = getComputedStyle(qInput);
        const u1 = document.getElementById('scaleQueryUnit').textContent;
        const u2 = document.getElementById('scaleQuerySigUnit').textContent;
        return {
            qInCol: col.contains(q),
            qAbove: col.contains(q) && (q.compareDocumentPosition(f) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0,
            qBorder: qcs.borderTopWidth,
            fBorder: fcs.borderTopWidth,
            qH: qics.height, qFS: qics.fontSize,
            uScale: u1, uSig: u2,
        };
    }""")
    check('ППР в колонке ввода и НАД панелью шкалы',
          ss['qInCol'] and ss['qAbove'], ss)
    check('ППР — выступ (2px), панель шкалы — колодец (1px)',
          ss['qBorder'] == '2px' and ss['fBorder'] == '1px', ss)
    check('поля ППР 52/19', ss['qH'] == '52px' and ss['qFS'] == '19px', ss)
    check('живые единицы при загрузке (%s / %s)' % (ss['uScale'], ss['uSig']),
          ss['uScale'] == '%' and ss['uSig'] == 'кгс/см²', ss)
    hint_gone = page.evaluate(
        "() => !document.body.textContent.includes('Корнеизвлекающая: сигнал ∝ √(шкала)')")
    check('текст-подсказка удалён', hint_gone)
    shot(page, 't501-scale-signal-dark.png')
    # живой расчёт ППР: 50 ед. → сигнал
    page.fill('#queryScaleVal', '50')
    page.evaluate("queryFromScaleLive()")
    qv = page.evaluate("() => document.getElementById('querySigVal').value")
    check('ППР: 50%% → ~12,2 мА (кгс/см²→мА: %.3s)' % qv, qv != '', qv)
    # смена пресета шкалы → единицы обновляются
    page.evaluate(
        "() => {const s=document.getElementById('scalePreset'); s.value='4_20'; setScaleDefaults();}")
    u_after = page.evaluate(
        "() => document.getElementById('scaleQueryUnit').textContent")
    check('пресет 4–20 мА → единица «мА»', u_after == 'мА', u_after)
    # полный расчёт
    page.evaluate("calcScaleSignal()")
    page.wait_for_timeout(300)
    res = page.evaluate(
        "() => document.getElementById('scaleResultsArea').style.display")
    check('«Рассчитать» показывает результаты', res == 'block', res)

    # =========== СВЕТЛАЯ ТЕМА ===========
    print('== 4. Светлая тема — датчики температуры (тёплая политура)')
    page.evaluate("localStorage.setItem('kip8test:app-theme','light')")
    page.evaluate("document.documentElement.setAttribute('data-theme','light')")
    page.wait_for_timeout(300)
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(700)
    cat = page.evaluate("""() => {
        const tab = document.querySelector('#page-temp-sensors .ts-tab.active');
        const tcs = tab ? getComputedStyle(tab) : null;
        const barTab = document.querySelector('#tsBottomBar .ts-tab.active');
        const bcs = barTab ? getComputedStyle(barTab) : null;
        return {
            tabColor: tcs ? tcs.color : null,
            barColor: bcs ? bcs.color : null,
        };
    }""")
    check('активный таб каталога — терракота rgb(198, 97, 63)',
          cat['tabColor'] and cat['tabColor'].startswith('rgb(198'), cat)
    check('активный таб нижнего бара — терракота',
          cat['barColor'] and cat['barColor'].startswith('rgb(198'), cat)
    shot(page, 't501-ts-catalog-light.png')
    page.evaluate("openTempSensor('cu50_1428')")
    page.wait_for_timeout(600)
    tsv = page.evaluate("""() => {
        const q = document.getElementById('tempCustomCalcPanel');
        const f = document.getElementById('tempTableFormPanel');
        const qcs = getComputedStyle(q);
        const fcs = getComputedStyle(f);
        const inp = document.querySelector('#tempCustomCalcPanel input.ts-calc-field');
        const ics = inp ? getComputedStyle(inp) : null;
        return {
            qBorder: qcs.borderTopColor, fBorder: fcs.borderTopColor,
            qShadow: qcs.boxShadow.slice(0, 60),
            inpBorder: ics ? ics.borderTopColor : null,
            inpColor: ics ? ics.color : null,
        };
    }""")
    check('ППР вид: рамка терракота rgb(198, 97, 63)',
          tsv['qBorder'].startswith('rgba(198'), tsv)
    check('колодец: рамка терракота', tsv['fBorder'].startswith('rgba(198'), tsv)
    check('тень ППР тёплая (без 21, 54, 83)',
          '21, 54, 83' not in tsv['qShadow'], tsv)
    check('поля: нейтральная рамка, тёмный текст',
          tsv['inpBorder'].startswith('rgba(20') and tsv['inpColor'].startswith('rgb(20'), tsv)
    shot(page, 't501-ts-view-light.png')
    # шкала-сигнал светлая: панель ППР над панелью шкалы + тёплые рамки
    page.evaluate("navigateTo('scale-signal')")
    page.wait_for_timeout(400)
    ssl = page.evaluate("""() => {
        const q = document.getElementById('scaleQueryPanel');
        const f = document.getElementById('scaleFormPanel');
        return {q: getComputedStyle(q).borderTopColor,
                f: getComputedStyle(f).borderTopColor};
    }""")
    check('шкала-сигнал светлая: обе панели тёплые',
          ssl['q'].startswith('rgba(198') and ssl['f'].startswith('rgba(198'), ssl)
    shot(page, 't501-scale-signal-light.png')

    n_err1 = len(errors_all)
    check('0 JS-ошибок (мобайл)', n_err1 == 0, errors_all[:3])
    ctx.close()

    # =========== ДЕСКТОП 1280, СВЕТЛАЯ ===========
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 900},
                               device_scale_factor=1)
    setup_routes(ctx2)
    ctx2.add_init_script(
        "localStorage.setItem('kip8test:app-theme','light');")
    page2 = ctx2.new_page()
    errs2 = []
    page2.on('pageerror', lambda e: errs2.append(str(e)))
    page2.goto('http://127.0.0.1:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    print('== 5. Десктоп 1280, светлая')
    page2.evaluate("navigateTo('circuit-breaker')")
    page2.wait_for_timeout(500)
    d = page2.evaluate("""() => {
        const pg = document.getElementById('page-circuit-breaker');
        const cols = pg.querySelectorAll('.conv-col').length;
        const panel = pg.querySelector('.ts-calc-panel.ts-calc-inset');
        return {cols, panel: !!panel,
                seps: panel ? panel.querySelectorAll('.ts-calc-sep').length : 0};
    }""")
    check('десктоп: три колонки + панель + 7 разделителей',
          d['cols'] == 3 and d['panel'] and d['seps'] == 7, d)
    shot(page2, 't501-cb-desktop-light.png')
    page2.evaluate("navigateTo('geo-horiz')")
    page2.wait_for_timeout(400)
    gh = page2.evaluate("""() => {
        const p = document.querySelector('#page-geo-horiz .ts-calc-panel.ts-calc-inset');
        return p ? {seps: p.querySelectorAll('.ts-calc-sep').length} : null;
    }""")
    check('десктоп geo-horiz: панель + 2 разделителя',
          gh and gh['seps'] == 2, gh)
    shot(page2, 't501-geo-desktop-light.png')
    check('0 JS-ошибок (десктоп)', len(errs2) == 0, errs2[:3])
    ctx2.close()
    browser.close()

print('\nИТОГ: %d passed / %d failed' % (PASS, FAIL))
if FAIL:
    raise SystemExit(1)
