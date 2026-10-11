#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 500: browser-check — заявка: «Примени стиль отображения для
# всех разделов КИП и А, в разделах шкала-сигнал, буйковый уровнемер
# и сужающее устройство объедини блоки с полями ввода в один блок.»
#   1. МОБАЙЛ 375 тёмная — ОБЪЕДИНЕНИЕ (6 страниц): в col-input ОДНА
#      панель-«колодец» (border 1px, box-shadow inset, фон-«колодец»),
#      обёрток .scale-form нет, кнопка вне панели; ПОЛЯ 52/19/700/
#      белый; КАСТОМНЫЕ селекты (найденные как .cs-trigger — нативный
#      select скрыт cs-wrapper'ом) — тот же крупный вид 52/19/700;
#      разделители групп (border-top 1px, margin-top 14px).
#   2. ЖИВЫЕ ПЕРЕКЛЮЧАТЕЛИ (через UI кастомного дропдауна: клик
#      триггера → клик опции): scalePreset→custom (scaleCustomRange),
#      buoy_signal_type→custom (customSignalRange), orifice-flow
#      среда→газ (op_flow_gas_params); живой расчёт scale-signal
#      («Рассчитать» → таблица) и панель произвольных значений
#      (scaleQueryPanel: border 2px — ВЫСТУП, поля 52/19).
#   3. СТИЛЬ без объединения: conv-pressure (converter-form) и
#      error-pressure (scale-form) — «колодец», поля 52/19, подпись
#      form-label 12px, триггер селекта 52/19.
#   4. РЕГРЕССИЯ temp-sensor-view: панель таблицы как была (495).
#   5. СВЕТЛАЯ тема: панель светлая, поля тёмный текст (rgb(20,20,19)).
#   6. ДЕСКТОП 1280: три колонки, панель одна, поля 52/19/700.
# + 0 JS-ошибок; скриншоты в download/kip8test-task500/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8986
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task500')
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
          (('  [' + str(extra)[:200] + ']') if (extra and not ok) else ''))


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
                      body='not found (browser-check t500)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Состояние объединённой панели АКТИВНОЙ страницы
PANEL_JS = r"""((panelSel) => {
    // только АКТИВНАЯ страница (querySelector без скоупа ловит первую
    // попавшуюся col-input другой страницы — урок отладки t500)
    const pg = document.querySelector('.page-content.active');
    const col = pg ? pg.querySelector('.conv-col-input') : null;
    const panel = col ? col.querySelector(panelSel) : null;
    if (!panel) return {found: false};
    const cs = getComputedStyle(panel);
    const input = panel.querySelector('input.scale-field, input.form-field');
    const ics = input ? getComputedStyle(input) : null;
    const trig = panel.querySelector('.cs-trigger');
    const tcs = trig ? getComputedStyle(trig) : null;
    const sep = panel.querySelector('.ts-calc-sep');
    const scs2 = sep ? getComputedStyle(sep) : null;
    const btn = col.querySelector('.scale-calc-btn, .converter-convert-btn');
    return {
        found: true,
        insetPanels: col.querySelectorAll('.ts-calc-panel.ts-calc-inset').length,
        formWrappers: col.querySelectorAll('.scale-form').length,
        borderWidth: cs.borderTopWidth,
        shadow: cs.boxShadow,
        hasInsetShadow: cs.boxShadow.indexOf('inset') !== -1,
        bg: cs.backgroundColor,
        bgImage: cs.backgroundImage,
        inputH: ics ? ics.height : null,
        inputFS: ics ? ics.fontSize : null,
        inputW: ics ? ics.fontWeight : null,
        inputColor: ics ? ics.color : null,
        trigH: tcs ? tcs.height : null,
        trigFS: tcs ? tcs.fontSize : null,
        trigW: tcs ? tcs.fontWeight : null,
        trigColor: tcs ? tcs.color : null,
        sepBT: scs2 ? scs2.borderTopWidth : 'нет',
        sepMT: scs2 ? scs2.marginTop : 'нет',
        btnAfter: btn ? ((panel.compareDocumentPosition(btn) &
                 Node.DOCUMENT_POSITION_FOLLOWING) !== 0) : null
    };
})('%s')"""


def panel_state(page, panel_sel):
    return page.evaluate(PANEL_JS % panel_sel)


def go(page, nav):
    page.evaluate("navigateTo('%s')" % nav)
    page.wait_for_timeout(900)


def pick_option(page, select_id, value):
    """Выбор опции через UI кастомного селекта: клик по триггеру
    #select_id-обёртки → клик по видимой опции дропдауна."""
    page.evaluate(
        "(() => { const s = document.getElementById('%s');"
        " s.closest('.cs-wrapper').querySelector('.cs-trigger').click(); })()"
        % select_id)
    page.wait_for_timeout(350)
    page.click('.cs-dropdown.cs-show .cs-option[data-value="%s"]' % value)
    page.wait_for_timeout(350)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ============ 1. МОБАЙЛ 375, тёмная ============
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t500-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://127.0.0.1:%d/index.html' % PORT)
        page.wait_for_timeout(2500)

        # --- 1a. Шкала-сигнал (объединение 3 блоков) ---
        go(page, 'scale-signal')
        st = panel_state(page, '#scaleFormPanel')
        check('1a-1: панель #scaleFormPanel найдена (активная страница)',
              st.get('found'))
        check('1a-2: в col-input ОДНА панель-«колодец»',
              st.get('insetPanels') == 1, st.get('insetPanels'))
        check('1a-3: обёрток .scale-form в col-input НЕТ',
              st.get('formWrappers') == 0, st.get('formWrappers'))
        check('1a-4: «колодец»: рамка 1px (не 2px выступа)',
              st.get('borderWidth') == '1px', st.get('borderWidth'))
        n_insets = len([x for x in str(st.get('shadow', '')).split(',') if x.strip()]
                       ) if st.get('shadow') else 0
        # Chromium нормализует: каждая из 2 теней заканчивается «inset»
        shadow_str = str(st.get('shadow', ''))
        n_inset_kw = shadow_str.count('inset')
        check('1a-5: тень ТОЛЬКО внутренняя (2 inset, внешней нет)',
              st.get('hasInsetShadow') and n_inset_kw == 2, st.get('shadow'))
        check('1a-6: фон-«колодец» тёмный без градиента',
              st.get('bg') == 'rgba(13, 17, 23, 0.55)' and
              st.get('bgImage') == 'none', (st.get('bg'), st.get('bgImage')))
        check('1a-7: поле в панели: 52px/19px/700/белый',
              st.get('inputH') == '52px' and st.get('inputFS') == '19px' and
              st.get('inputW') == '700' and
              st.get('inputColor') == 'rgb(255, 255, 255)',
              (st.get('inputH'), st.get('inputFS'), st.get('inputW'),
               st.get('inputColor')))
        check('1a-8: селект (cs-trigger): 52px/19px/700/белый',
              st.get('trigH') == '52px' and st.get('trigFS') == '19px' and
              st.get('trigW') == '700' and
              st.get('trigColor') == 'rgb(255, 255, 255)',
              (st.get('trigH'), st.get('trigFS'), st.get('trigW'),
               st.get('trigColor')))
        check('1a-9: разделитель групп: линия 1px, отступ 14px',
              st.get('sepBT') == '1px' and st.get('sepMT') == '14px',
              (st.get('sepBT'), st.get('sepMT')))
        check('1a-10: кнопка «Рассчитать» после панели',
              st.get('btnAfter') is True, st.get('btnAfter'))
        n_sep = page.evaluate(
            "document.querySelectorAll('#scaleFormPanel .ts-calc-sep').length")
        check('1a-11: разделителей 2 (бывшие 3 блока)', n_sep == 2, n_sep)
        shot(page, 'a1-scale-signal-dark.png')

        # --- живой расчёт + панель произвольных значений ---
        page.click('.scale-calc-btn')
        page.wait_for_timeout(700)
        res = page.evaluate("(() => { const a = document.getElementById("
                            "'scaleResultsArea'); const t = document."
                            "getElementById('scaleTableContainer');"
                            "return {vis: a && a.style.display !== 'none',"
                            "rows: t ? t.querySelectorAll('tr').length : 0}; })()")
        check('1a-12: живой расчёт: результаты + таблица (строк > 0)',
              res['vis'] and res['rows'] > 0, res)
        qp = page.evaluate("(() => { const q = document.getElementById("
                           "'scaleQueryPanel'); if (!q) return {found: false};"
                           "const cs = getComputedStyle(q);"
                           "const f = q.querySelector('input.scale-field');"
                           "const fc = f ? getComputedStyle(f) : null;"
                           "return {found: true, bw: cs.borderTopWidth,"
                           "inset: q.classList.contains('ts-calc-inset'),"
                           "h: fc ? fc.height : null,"
                           "fs: fc ? fc.fontSize : null}; })()")
        check('1a-13: панель произвольных значений — ВЫСТУП (рамка 2px)',
              qp.get('found') and qp.get('bw') == '2px' and
              qp.get('inset') is False, (qp.get('bw'), qp.get('inset')))
        check('1a-14: поля панели произвольных значений: 52px/19px',
              qp.get('h') == '52px' and qp.get('fs') == '19px',
              (qp.get('h'), qp.get('fs')))
        shot(page, 'a2-scale-signal-query-dark.png')

        # --- переключатели через UI кастомного селекта ---
        pick_option(page, 'scalePreset', 'custom')
        vis = page.evaluate("(() => { const d = document.getElementById("
                            "'scaleCustomRange'); return d && "
                            "d.style.display !== 'none'; })()")
        check('1a-15: scalePreset→«Своё»: диапазон шкалы раскрыт', vis)
        pick_option(page, 'sigType', 'custom')
        vis2 = page.evaluate("(() => { const d = document.getElementById("
                             "'sigCustomRange'); return d && d.offsetParent "
                             "!== null; })()")
        check('1a-16: sigType→«Своё»: диапазон сигнала раскрыт', vis2)
        shot(page, 'a3-scale-signal-custom-dark.png')

        # --- 1b. Буйковый уровнемер (объединение 4 блоков) ---
        go(page, 'buoy-select')
        page.wait_for_timeout(300)
        go(page, 'buoy-calc')
        st = panel_state(page, '#buoyFormPanel')
        check('1b-1: панель #buoyFormPanel найдена', st.get('found'))
        check('1b-2: ОДНА панель-«колодец», обёрток нет',
              st.get('insetPanels') == 1 and st.get('formWrappers') == 0,
              (st.get('insetPanels'), st.get('formWrappers')))
        check('1b-3: «колодец»: рамка 1px, inset-тень',
              st.get('borderWidth') == '1px' and st.get('hasInsetShadow'),
              (st.get('borderWidth'), str(st.get('shadow'))[:40]))
        check('1b-4: поля 52/19/700, триггер селекта 52/19/700',
              st.get('inputH') == '52px' and st.get('inputFS') == '19px' and
              st.get('trigH') == '52px' and st.get('trigFS') == '19px',
              (st.get('inputH'), st.get('inputFS'), st.get('trigH'),
               st.get('trigFS')))
        n_sep = page.evaluate(
            "document.querySelectorAll('#buoyFormPanel .ts-calc-sep').length")
        check('1b-5: разделителей 3 (бывшие 4 блока)', n_sep == 3, n_sep)
        shot(page, 'b1-buoy-calc-dark.png')
        # переключатель сигнала → custom (через UI)
        pick_option(page, 'buoy_signal_type', 'custom')
        vis = page.evaluate("(() => { const d = document.getElementById("
                            "'customSignalRange'); return d && "
                            "d.style.display !== 'none'; })()")
        check('1b-6: buoy_signal_type→«Своё»: диапазон раскрыт', vis)
        # вернуть стандартный сигнал (custom с пустыми min/max не
        # проходит валидацию — таблица не строится)
        pick_option(page, 'buoy_signal_type', '0_2_1_0_kgf_cm2')
        page.wait_for_timeout(200)
        # живой расчёт калибровки
        page.evaluate("selectCalibMethod('with_buoy')")
        page.wait_for_timeout(300)
        page.click('.page-content.active .conv-col-input .converter-convert-btn')
        page.wait_for_timeout(700)
        rows = page.evaluate(
            "document.querySelectorAll('#buoyTableContainer tr').length")
        check('1b-7: живой расчёт: таблица калибровки построена', rows > 0, rows)
        shot(page, 'b2-buoy-calc-results-dark.png')

        # --- 1c. Сужающее устройство: 4 страницы (5/7/7/7 блоков → 1) ---
        ORIFICE = [('orifice-quick', '#orificeQuickFormPanel', 4),
                   ('orifice-dp', '#orificeDpFormPanel', 6),
                   ('orifice-flow', '#orificeFlowFormPanel', 6),
                   ('orifice-diameter', '#orificeDiameterFormPanel', 6)]
        for nav, sel, n_sep_exp in ORIFICE:
            go(page, nav)
            st = panel_state(page, sel)
            check('%s-1: панель найдена, ОДНА, обёрток нет' % nav,
                  st.get('found') and st.get('insetPanels') == 1 and
                  st.get('formWrappers') == 0,
                  (st.get('found'), st.get('insetPanels'),
                   st.get('formWrappers')))
            check('%s-2: «колодец» 1px/inset/фон-колодец' % nav,
                  st.get('borderWidth') == '1px' and st.get('hasInsetShadow')
                  and st.get('bgImage') == 'none',
                  (st.get('borderWidth'), st.get('bg'), st.get('bgImage')))
            check('%s-3: поля 52/19/700, селект-триггер 52/19' % nav,
                  st.get('inputH') == '52px' and st.get('inputFS') == '19px'
                  and st.get('trigFS') == '19px',
                  (st.get('inputH'), st.get('inputFS'), st.get('trigFS')))
            n_sep = page.evaluate(
                "document.querySelectorAll('%s .ts-calc-sep').length" % sel)
            check('%s-4: разделителей %d' % (nav, n_sep_exp),
                  n_sep == n_sep_exp, n_sep)
        shot(page, 'c1-orifice-quick-dark.png')
        go(page, 'orifice-diameter')
        shot(page, 'c2-orifice-diameter-dark.png')

        # переключатель среды orifice-flow → газ (через UI)
        go(page, 'orifice-flow')
        pick_option(page, 'op_flow_medium_type', 'gas')
        vis = page.evaluate("(() => { const d = document.getElementById("
                            "'op_flow_gas_params'); return d && "
                            "d.style.display !== 'none'; })()")
        check('1c-5: orifice-flow среда→«Газ»: параметры газа раскрыты', vis)
        # живой расчёт orifice-quick
        go(page, 'orifice-quick')
        page.click('.page-content.active .conv-col-input .converter-convert-btn')
        page.wait_for_timeout(700)
        vis = page.evaluate("(() => { const r = document.getElementById("
                            "'oq_results'); return r && r.style.display !== "
                            "'none' && r.innerHTML.length > 100; })()")
        check('1c-6: живой расчёт: быстрая диафрагма посчиталась', vis)

        # --- 1d. Стиль без объединения: conv-pressure + error-pressure ---
        go(page, 'conv-pressure')
        st = page.evaluate(r"""(() => {
            const pg = document.querySelector('.page-content.active');
            const col = pg ? pg.querySelector('.conv-col-input') : null;
            const f = col ? col.querySelector('.converter-form') : null;
            if (!f) return {found: false};
            const cs = getComputedStyle(f);
            const fld = f.querySelector('input.form-field');
            const fc = fld ? getComputedStyle(fld) : null;
            const lbl = f.querySelector('.form-label');
            const lc = lbl ? getComputedStyle(lbl) : null;
            return {found: true, bw: cs.borderTopWidth,
                    inset: cs.boxShadow.indexOf('inset') !== -1,
                    h: fc ? fc.height : null, fs: fc ? fc.fontSize : null,
                    w: fc ? fc.fontWeight : null, lblFS: lc ? lc.fontSize : null};
        })()""")
        check('1d-1: conv-pressure: форма-«колодец» (1px, inset-тень)',
              st.get('found') and st.get('bw') == '1px' and st.get('inset'),
              (st.get('bw'), str(st.get('inset'))[:40]))
        check('1d-2: conv-pressure: поле 52/19/700', st.get('h') == '52px'
              and st.get('fs') == '19px' and st.get('w') == '700',
              (st.get('h'), st.get('fs'), st.get('w')))
        check('1d-3: conv-pressure: подпись form-label 12px',
              st.get('lblFS') == '12px', st.get('lblFS'))
        shot(page, 'd1-conv-pressure-dark.png')

        go(page, 'error-pressure')
        st = page.evaluate(r"""(() => {
            const pg = document.querySelector('.page-content.active');
            const col = pg ? pg.querySelector('.conv-col-input') : null;
            const f = col ? col.querySelector('.scale-form') : null;
            if (!f) return {found: false};
            const cs = getComputedStyle(f);
            const trig = f.querySelector('.cs-trigger');
            const tc = trig ? getComputedStyle(trig) : null;
            return {found: true, bw: cs.borderTopWidth,
                    inset: cs.boxShadow.indexOf('inset') !== -1,
                    trigH: tc ? tc.height : null,
                    trigFS: tc ? tc.fontSize : null,
                    n: col.querySelectorAll('.scale-form.ts-calc-inset').length};
        })()""")
        check('1d-4: error-pressure: блок-«колодец», селект-триггер 52/19',
              st.get('found') and st.get('bw') == '1px' and st.get('inset')
              and st.get('trigH') == '52px' and st.get('trigFS') == '19px',
              (st.get('bw'), st.get('trigH'), st.get('trigFS')))
        shot(page, 'd2-error-pressure-dark.png')

        # --- 1e. РЕГРЕССИЯ temp-sensor-view (эталон 495) ---
        go(page, 'temp-sensors')
        page.evaluate("openTempSensor('cu50_1428')")
        page.wait_for_timeout(700)
        st = page.evaluate(r"""(() => {
            const p = document.getElementById('tempTableFormPanel');
            const f = document.getElementById('temp_sensor_step');
            const cs = p ? getComputedStyle(p) : null;
            const fc = f ? getComputedStyle(f) : null;
            return {bw: cs ? cs.borderTopWidth : null,
                    h: fc ? fc.height : null, fs: fc ? fc.fontSize : null};
        })()""")
        check('1e-1: temp-sensor-view: панель таблицы как была (1px, 52/19)',
              st.get('bw') == '1px' and st.get('h') == '52px' and
              st.get('fs') == '19px', st)
        shot(page, 'e1-temp-sensor-view-dark.png')

        check('1-0JS: мобильная сессия без JS-ошибок', len(js_errors) == 0,
              js_errors[:3])
        ctx.close()

        # ============ 2. СВЕТЛАЯ тема (мобайл) ============
        ctx2 = browser.new_context(viewport={'width': 375, 'height': 720},
                                   is_mobile=True, has_touch=True)
        page2 = ctx2.new_page()
        js_errors2 = []
        page2.on('pageerror', lambda e: js_errors2.append(str(e)))
        page2.on('dialog', lambda d: d.accept())
        setup_routes(ctx2)
        ctx2.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t500-b');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page2.goto('http://127.0.0.1:%d/index.html' % PORT)
        page2.wait_for_timeout(2500)
        go(page2, 'scale-signal')
        st = panel_state(page2, '#scaleFormPanel')
        check('2-1: светлая: панель светлая, рамка 1px',
              st.get('found') and st.get('borderWidth') == '1px' and
              st.get('bg') == 'rgba(21, 54, 83, 0.08)',
              (st.get('bg'), st.get('borderWidth')))
        check('2-2: светлая: поля тёмный текст (rgb(20,20,19))',
              st.get('inputColor') == 'rgb(20, 20, 19)',
              st.get('inputColor'))
        check('2-3: светлая: триггер селекта тоже светлый/тёмный текст',
              st.get('trigColor') == 'rgb(20, 20, 19)', st.get('trigColor'))
        sep_c = page2.evaluate("(() => { const s = document.querySelector("
                               "'#scaleFormPanel .ts-calc-sep'); return s ? "
                               "getComputedStyle(s).borderTopColor : null; })()")
        check('2-4: светлая: линия-разделитель есть', sep_c is not None, sep_c)
        shot(page2, 'f1-scale-signal-light.png')
        check('2-0JS: светлая сессия без JS-ошибок', len(js_errors2) == 0,
              js_errors2[:3])
        ctx2.close()

        # ============ 3. ДЕСКТОП 1280 ============
        ctx3 = browser.new_context(viewport={'width': 1280, 'height': 800})
        page3 = ctx3.new_page()
        js_errors3 = []
        page3.on('pageerror', lambda e: js_errors3.append(str(e)))
        page3.on('dialog', lambda d: d.accept())
        setup_routes(ctx3)
        ctx3.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t500-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page3.goto('http://127.0.0.1:%d/index.html' % PORT)
        page3.wait_for_timeout(2500)
        go(page3, 'scale-signal')
        st = panel_state(page3, '#scaleFormPanel')
        cols = page3.evaluate("document.querySelectorAll("
                              "'#page-scale-signal .conv-col').length")
        check('3-1: десктоп: 3 колонки, панель одна, обёрток нет',
              cols == 3 and st.get('insetPanels') == 1 and
              st.get('formWrappers') == 0,
              (cols, st.get('insetPanels'), st.get('formWrappers')))
        check('3-2: десктоп: поля 52/19/700 (стиль един на всех экранах)',
              st.get('inputH') == '52px' and st.get('inputFS') == '19px' and
              st.get('inputW') == '700',
              (st.get('inputH'), st.get('inputFS'), st.get('inputW')))
        shot(page3, 'g1-scale-signal-desktop.png')
        go(page3, 'orifice-diameter')
        st = panel_state(page3, '#orificeDiameterFormPanel')
        check('3-3: десктоп orifice-diameter: панель одна',
              st.get('found') and st.get('insetPanels') == 1,
              st.get('insetPanels'))
        shot(page3, 'g2-orifice-diameter-desktop.png')
        check('3-0JS: десктоп-сессия без JS-ошибок', len(js_errors3) == 0,
              js_errors3[:3])
        ctx3.close()

        browser.close()

    print('\nИТОГ Task 500 browser-check: %d OK, %d FAIL' % (PASS, FAIL))
    if FAIL:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
