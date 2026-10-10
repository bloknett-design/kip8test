#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 494: browser-check — заявка: «На страницах расчёта датчиков
# температуры убери надписи "Расчёт произвольных значений Введите
# значение в любое поле — другое рассчитается автоматически", а шрифт,
# размер полей ввода в этом блоке сделай больше и ярче, и сам блок
# сделай в стиле эффект выступа (рамка 2px + градиент + тень).»
#   1. МОБАЙЛ 375 тёмная: открыть датчик 50М → страница
#      temp-sensor-view; панель #tempCustomCalcPanel: заголовка
#      «Расчёт произвольных значений» и подсказки «Введите значение…»
#      в DOM НЕТ; рамка 2px, градиент, тень (выступ); поля
#      .ts-calc-field: 19px/700/белый, высота 52px, яркий плейсхолдер;
#      подписи полей на месте; живой расчёт: ввод 55 в «Температура» →
#      второе поле рассчиталось (R(t)).
#   2. ТП (ТХА (K)): то же + подпись «Термо-ЭДС E(t), мВ»
#      подставилась openTempSensor.
#   3. СВЕТЛАЯ тема мобайл: панель — светлая рамка/градиент/мягкая
#      тень; поля — тёмный текст.
#   4. ДЕСКТОП 1280 тёмная: панель стилизована и там (CSS не в media).
# + 0 JS-ошибок; скриншоты в download/kip8test-task494/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8982
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task494')
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
                      body='not found (browser-check t494)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Состояние панели произвольного расчёта
PANEL_JS = r"""(() => {
    const p = document.getElementById('tempCustomCalcPanel');
    if (!p) return {panel: false};
    const st = getComputedStyle(p);
    const t = document.getElementById('tempQueryTemp');
    const v = document.getElementById('tempQueryVal');
    const tst = t ? getComputedStyle(t) : null;
    const vst = v ? getComputedStyle(v) : null;
    return {
        panel: true,
        title: !!p.querySelector('.ts-calc-title'),
        hint: !!p.querySelector('.ts-calc-hint'),
        titleText: p.textContent.indexOf('Расчёт произвольных значений') !== -1,
        hintText: p.textContent.indexOf('Введите значение в любое поле') !== -1,
        borderWidth: st.borderWidth,
        borderColor: st.borderColor,
        boxShadow: st.boxShadow,
        bgImage: st.backgroundImage,
        tempLabel: !!document.getElementById('tempQueryValLabel'),
        valLabelText: (document.getElementById('tempQueryValLabel')||{}).textContent,
        tempLabel2: p.textContent.indexOf('Температура (°C)') !== -1,
        fieldsN: p.querySelectorAll('.ts-calc-field').length,
        tFont: tst ? tst.fontSize : null,
        tWeight: tst ? tst.fontWeight : null,
        tColor: tst ? tst.color : null,
        tHeight: t ? Math.round(t.getBoundingClientRect().height) : null,
        tBorder: tst ? tst.borderColor : null,
        tPlaceholder: (m => m ? m.color : null)(
            (cs => cs ? cs.color : null)({})),
        phColor: (s => s ? s.color : null)(
            (() => { try { return getComputedStyle(t, '::placeholder'); } catch(e){ return null; } })()),
        vFont: vst ? vst.fontSize : null,
        vHeight: v ? Math.round(v.getBoundingClientRect().height) : null,
        tValue: t ? t.value : null,
        vValue: v ? v.value : null
    };
})()"""


def open_sensor(page, key):
    page.evaluate("openTempSensor('%s')" % key)
    page.wait_for_timeout(500)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ============ 1. МОБАЙЛ 375, тёмная, датчик 50М (ТС) ===========
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t494-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(600)
        open_sensor(page, 'cu50_1428')

        check('A: страница датчика активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensor-view').classList.contains('active')"))
        st = page.evaluate(PANEL_JS)
        check('B: панель есть; заголовка/подсказки в DOM НЕТ',
              st['panel'] and not st['title'] and not st['hint'] and
              not st['titleText'] and not st['hintText'], st)
        check('C: панель — рамка 2px (эффект выступа)',
              st['borderWidth'] == '2px', (st['borderWidth'],
                                           st['borderColor']))
        check('D: панель — градиент фона', st['bgImage'] != 'none' and
              'linear-gradient' in st['bgImage'], st['bgImage'][:80])
        check('E: панель — тень выступа (внешняя + inset)',
              st['boxShadow'] != 'none' and 'inset' in st['boxShadow'],
              st['boxShadow'][:80])
        check('F: поля — ровно 2, подписи на месте (Температура/R(t))',
              st['fieldsN'] == 2 and st['tempLabel2'] and
              st['valLabelText'] == 'Сопротивление R(t), Ом', st)
        check('G: поля крупнее — шрифт 19px, высота 52px',
              st['tFont'] == '19px' and st['tHeight'] == 52 and
              st['vFont'] == '19px' and st['vHeight'] == 52,
              (st['tFont'], st['tHeight'], st['vFont'], st['vHeight']))
        check('H: поля ярче — 700/белый текст',
              str(st['tWeight']) == '700' and st['tColor'] == 'rgb(255, 255, 255)',
              (st['tWeight'], st['tColor']))
        check('I: рамка поля яркая (не общий card-border)',
              '74, 143, 199' in str(st['tBorder']), st['tBorder'])

        # живой расчёт: ввод 55 → R(t) рассчиталось
        page.fill('#tempQueryTemp', '55')
        page.wait_for_timeout(400)
        st2 = page.evaluate(PANEL_JS)
        check('J: живой расчёт жив — t=55 → R(t) рассчитано',
              st2['vValue'] not in (None, '') and
              float(st2['vValue'].replace(',', '.')) > 61,
              (st2['tValue'], st2['vValue']))
        shot(page, 'a-mobile-dark-rtd.png')

        # ============ 2. ТП — ТХА (K) ================================
        open_sensor(page, 'tc_K')
        st3 = page.evaluate(PANEL_JS)
        check('K: ТХА (K) — подпись «Термо-ЭДС E(t), мВ» подставилась',
              st3['valLabelText'] == 'Термо-ЭДС E(t), мВ', st3['valLabelText'])
        check('L: панель ТП — та же геометрия (2px/19px/52px)',
              st3['borderWidth'] == '2px' and st3['tFont'] == '19px' and
              st3['tHeight'] == 52, (st3['borderWidth'], st3['tFont']))
        page.fill('#tempQueryTemp', '300')
        page.wait_for_timeout(400)
        st4 = page.evaluate(PANEL_JS)
        check('M: живой расчёт ТП — t=300 → E(t) рассчитано',
              st4['vValue'] not in (None, '') and
              float(st4['vValue'].replace(',', '.')) > 10,
              (st4['tValue'], st4['vValue']))
        shot(page, 'b-mobile-dark-tc.png')
        ctx.close()

        # ============ 3. СВЕТЛАЯ тема мобайл ==========================
        ctx = browser.new_context(viewport={'width': 375, 'height': 720},
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        js_errors2 = []
        page.on('pageerror', lambda e: js_errors2.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t494-b');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu50_1428')
        st5 = page.evaluate(PANEL_JS)
        check('N: светлая — рамка 2px синяя',
              st5['borderWidth'] == '2px' and
              '43, 111, 163' in str(st5['borderColor']),
              (st5['borderWidth'], st5['borderColor']))
        check('O: светлая — поля тёмный текст, крупный шрифт',
              st5['tColor'] == 'rgb(20, 20, 19)' and
              st5['tFont'] == '19px', (st5['tColor'], st5['tFont']))
        check('P: светлая — мягкая тень (без 0.42-черноты)',
              st5['boxShadow'] != 'none' and
              'rgba(21, 54, 83, 0.22)' in st5['boxShadow'],
              st5['boxShadow'][:80])
        check('Q: светлая — заголовка/подсказки НЕТ',
              not st5['titleText'] and not st5['hintText'], st5)
        shot(page, 'c-mobile-light-rtd.png')
        ctx.close()

        # ============ 4. ДЕСКТОП 1280 тёмная ==========================
        ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = ctx.new_page()
        js_errors3 = []
        page.on('pageerror', lambda e: js_errors3.append(str(e)))
        page.on('dialog', lambda d: d.accept())
        setup_routes(ctx)
        ctx.add_init_script(
            "localStorage.setItem('kip8test:kip8_session_token','bc-t494-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu100_1426')
        st6 = page.evaluate(PANEL_JS)
        check('R: десктоп — панель стилизована (2px/градиент/тень/19px)',
              st6['borderWidth'] == '2px' and
              'linear-gradient' in st6['bgImage'] and
              'inset' in st6['boxShadow'] and st6['tFont'] == '19px',
              (st6['borderWidth'], st6['bgImage'][:40],
               st6['boxShadow'][:40], st6['tFont']))
        check('S: десктоп — заголовка/подсказки НЕТ',
              not st6['titleText'] and not st6['hintText'], st6)
        shot(page, 'd-desktop-dark-rtd.png')
        ctx.close()
        browser.close()

        print('JS-ошибок: %d / %d / %d' %
              (len(js_errors), len(js_errors2), len(js_errors3)))
        for e in (js_errors + js_errors2 + js_errors3)[:5]:
            print('  err: %s' % e[:200])
        check('T: 0 JS-ошибок во всех сессиях',
              not js_errors and not js_errors2 and not js_errors3)

    print('\nИТОГ: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
