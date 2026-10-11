#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 502 browser-check: (1) шкала-сигнал — панель шкалы (тип шкалы)
# ВВЕРХУ, ППР под ней, кнопка после обеих; подсказка ППР удалена;
# Enter в полях ППР гасит клавиатуру (blur, НЕ следующий input);
# (2) палитра ts-элементов СНЯТА — нейтральные рамки/табы/звёзды в
# обеих темах, «Рассчитать» — прежний акцент; (3) буйковый уровнемер —
# подсказка НЕ удалялась (границы заявки); (4) живые расчёты; (5) 0 JS.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8986
SHOT_DIR = '/home/z/my-project/download/kip8test-task502'
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


def shot(page, name, full=False):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name), full_page=full)
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
                      body='not found (browser-check t502)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# --- шкала-сигнал: порядок/подсказка/Enter/единицы -------------------
SCALE_JS = r"""(() => {
    const col = document.querySelector('#page-scale-signal.active .conv-col-input');
    const q = document.getElementById('scaleQueryPanel');
    const f = document.getElementById('scaleFormPanel');
    const btn = document.querySelector('#page-scale-signal.active .scale-calc-btn');
    const qcs = getComputedStyle(q);
    const fcs = getComputedStyle(f);
    const qInp = q.querySelector('input.scale-field');
    const qics = getComputedStyle(qInp);
    const hint = q.textContent.indexOf('рассчитается автоматически') !== -1;
    return {
        colOk: !!col && col.contains(f) && col.contains(q) && col.contains(btn),
        formFirst: col.compareDocumentPosition(q) & Node.DOCUMENT_POSITION_FOLLOWING,
        btnLast: f.compareDocumentPosition(btn) & Node.DOCUMENT_POSITION_FOLLOWING &&
                 q.compareDocumentPosition(btn) & Node.DOCUMENT_POSITION_FOLLOWING,
        startsWithType: f.textContent.indexOf('Тип шкалы') !== -1,
        hint,
        qBorderW: qcs.borderTopWidth, fBorderW: fcs.borderTopWidth,
        qH: qics.height, qFS: qics.fontSize,
        qKeydown: qInp.getAttribute('onkeydown') || '',
        qEkh: qInp.getAttribute('enterkeyhint') || '',
    };
})()"""

# --- Enter в поле ППР: blur, НЕ переход на следующее поле ------------
ENTER_JS = r"""(() => {
    const inp = document.getElementById('queryScaleVal');
    const sig = document.getElementById('querySigVal');
    inp.focus();
    const wasFocused = document.activeElement === inp;
    const ev = new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13,
                                             bubbles: true, cancelable: true});
    inp.dispatchEvent(ev);
    const ae = document.activeElement;
    return {
        wasFocused,
        blurred: ae !== inp,
        notNext: ae !== sig,
        aeTag: ae === document.body ? 'body' : (ae.id || ae.tagName),
        defPrevented: ev.defaultPrevented,
    };
})()"""

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

    print('== 1. Шкала-сигнал, тёмная: swap + подсказка + Enter')
    page.evaluate("navigateTo('scale-signal')")
    page.wait_for_timeout(500)
    st = page.evaluate(SCALE_JS)
    check('панель шкалы (тип шкалы) — ВВЕРХУ, ППР под ней',
          st['colOk'] and st['formFirst'] and st['btnLast'], st)
    check('панель шкалы открывается группой «Тип шкалы»',
          st.get('startsWithType'), st)
    check('текст-подсказка ППР удалён', not st.get('hint'), st)
    check('ППР — выступ 2px, панель шкалы — колодец 1px',
          st['qBorderW'] == '2px' and st['fBorderW'] == '1px', st)
    check('поля ППР 52/19', st['qH'] == '52px' and st['qFS'] == '19px', st)
    check('Enter-обработчик на поле (scaleQueryEnterBlur)',
          'scaleQueryEnterBlur' in st['qKeydown'] and
          st['qEkh'] == 'done', st)
    ent = page.evaluate(ENTER_JS)
    check('Enter гасит клавиатуру: blur (active=%s)' % ent['aeTag'],
          ent['wasFocused'] and ent['blurred'] and ent['notNext'], ent)
    check('Enter: перехода на следующее поле НЕТ + default предотвращён',
          ent['notNext'] and ent['defPrevented'], ent)
    shot(page, 't502-scale-signal-dark.png', full=True)
    # живой расчёт ППР: 50 ед. → сигнал (пресет 0-100%/0,2-1,0 кгс/см²)
    page.fill('#queryScaleVal', '50')
    page.evaluate("queryFromScaleLive()")
    qv = page.evaluate("() => document.getElementById('querySigVal').value")
    check('ППР: 50%% → сигнал рассчитан (%s)' % qv[:7], qv != '', qv)
    # смена пресета → живые единицы
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

    print('== 2. Тёмная тема — нейтральная палитра ts-элементов')
    pal = page.evaluate("""() => {
        const q = document.getElementById('scaleQueryPanel');
        const f = document.getElementById('scaleFormPanel');
        const btn = document.querySelector('#page-scale-signal.active .scale-calc-btn');
        return {
            qBorder: getComputedStyle(q).borderTopColor,
            fBorder: getComputedStyle(f).borderTopColor,
            qShadow: getComputedStyle(q).boxShadow.slice(0, 80),
            btnBg: getComputedStyle(btn).backgroundImage.slice(0, 60),
        };
    }""")
    check('ППР тёмная: нейтральная белая рамка',
          pal['qBorder'].startswith('rgba(255, 255, 255'), pal)
    check('колодец тёмная: нейтральная рамка',
          pal['fBorder'].startswith('rgba(255, 255, 255'), pal)
    check('тень ППР без синевы (74, 143, 199)',
          '74, 143, 199' not in pal['qShadow'], pal)
    check('«Рассчитать» — прежний синий градиент (границы заявки)',
          '37, 99, 235' in pal['btnBg'] or '2563eb' in pal['btnBg'], pal)

    print('== 3. Буйковый уровнемер: подсказка НЕ удалялась (границы)')
    page.evaluate("navigateTo('buoy-calc')")
    page.wait_for_timeout(500)
    buoy = page.evaluate("""() => {
        const q = document.getElementById('buoyQueryPanel');
        const hint = q ? q.textContent.indexOf(
            'Введите значение в любое поле — два других рассчитаются автоматически') !== -1 : false;
        const keydowns = q ? q.querySelectorAll('input[onkeydown]') : [];
        return {hint, kd: keydowns.length};
    }""")
    check('подсказка буйка на месте', buoy['hint'], buoy)
    check('Enter-обработчик НЕ навешан на буйок (заявка — шкала-сигнал)',
          buoy['kd'] == 0, buoy)

    # =========== СВЕТЛАЯ ТЕМА ===========
    print('== 4. Светлая тема — нейтральная палитра')
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
        const star = document.querySelector('#page-temp-sensors .ts-card-fav-btn');
        const scs = star ? getComputedStyle(star) : null;
        return {
            tabColor: tcs ? tcs.color : null,
            barColor: bcs ? bcs.color : null,
            starColor: scs ? scs.color : null,
        };
    }""")
    check('активный таб каталога — нейтральный rgb(20, 20, 19)',
          cat['tabColor'] and cat['tabColor'].startswith('rgb(20'), cat)
    check('активный таб нижнего бара — нейтральный',
          cat['barColor'] and cat['barColor'].startswith('rgb(20'), cat)
    check('звёздочка — нейтральная (не терракота/синий)',
          cat['starColor'] and (cat['starColor'].startswith('rgb(20') or
                                cat['starColor'].startswith('rgba(20')), cat)
    shot(page, 't502-ts-catalog-light.png')
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
        };
    }""")
    check('ППР вида: нейтральная рамка rgba(20, 20, 19',
          tsv['qBorder'].startswith('rgba(20, 20, 19'), tsv)
    check('колодец вида: нейтральная рамка',
          tsv['fBorder'].startswith('rgba(20, 20, 19'), tsv)
    check('тень ППР без терракоты (198, 97, 63 / 158, 78, 48)',
          '198, 97, 63' not in tsv['qShadow'] and
          '158, 78, 48' not in tsv['qShadow'], tsv)
    check('поля: нейтральная рамка',
          tsv['inpBorder'].startswith('rgba(20, 20, 19'), tsv)
    shot(page, 't502-ts-view-light.png', full=True)
    # шкала-сигнал светлая: swap сохранён, панели нейтральные
    page.evaluate("navigateTo('scale-signal')")
    page.wait_for_timeout(400)
    stl = page.evaluate(SCALE_JS)
    check('светлая: swap и подсказка (инварианты)',
          stl['colOk'] and stl['formFirst'] and stl['btnLast'] and
          not stl['hint'], stl)
    ssl = page.evaluate("""() => {
        const q = document.getElementById('scaleQueryPanel');
        const f = document.getElementById('scaleFormPanel');
        const btn = document.querySelector('#page-scale-signal.active .scale-calc-btn');
        const bcs = getComputedStyle(btn);
        return {q: getComputedStyle(q).borderTopColor,
                f: getComputedStyle(f).borderTopColor,
                btnBg: bcs.backgroundImage.slice(0, 60)};
    }""")
    check('шкала-сигнал светлая: панели нейтральные',
          ssl['q'].startswith('rgba(20, 20, 19') and
          ssl['f'].startswith('rgba(20, 20, 19'), ssl)
    check('«Рассчитать» светлой — прежний терракотовый градиент',
          '198, 97, 63' in ssl['btnBg'] or 'C6613F' in ssl['btnBg'], ssl)
    shot(page, 't502-scale-signal-light.png', full=True)
    # Enter в светлой — тоже гасит клавиатуру
    entl = page.evaluate(ENTER_JS)
    check('светлая: Enter гасит клавиатуру', entl['blurred'] and entl['notNext'], entl)

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
    page2.evaluate("navigateTo('scale-signal')")
    page2.wait_for_timeout(500)
    d = page2.evaluate(SCALE_JS)
    check('десктоп: swap/подсказка/Enter-атрибуты (инварианты)',
          d['colOk'] and d['formFirst'] and d['btnLast'] and
          not d['hint'] and 'scaleQueryEnterBlur' in d['qKeydown'], d)
    shot(page2, 't502-scale-signal-desktop-light.png', full=True)
    page2.evaluate("navigateTo('temp-sensors')")
    page2.wait_for_timeout(600)
    dts = page2.evaluate("""() => {
        const tab = document.querySelector('#page-temp-sensors .ts-tab.active');
        return tab ? {color: getComputedStyle(tab).color} : null;
    }""")
    check('десктоп: активный таб каталога нейтральный',
          dts and dts['color'].startswith('rgb(20'), dts)
    shot(page2, 't502-ts-catalog-desktop-light.png')
    check('0 JS-ошибок (десктоп)', len(errs2) == 0, errs2[:3])
    ctx2.close()
    browser.close()

print('\nИТОГ: %d passed / %d failed' % (PASS, FAIL))
if FAIL:
    raise SystemExit(1)
