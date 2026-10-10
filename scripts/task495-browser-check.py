#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 495: browser-check — заявка: «В блоке ввода данных для расчёта
# таблицы убери поле с типом датчика, и убери тексты "Тип датчика" и
# "Шаг расчёта таблицы в градусах Цельсия", и оформи этот блок так же
# как блок произвольного расчёта, только не с эффектом выступа, а
# наоборот.»
#   1. МОБАЙЛ 375 тёмная, датчик 50М (ТС): на странице датчика НЕТ
#      чипа типа датчика (элемент отсутствует в DOM), НЕТ текстов
#      «Тип датчика» и «Шаг расчёта таблицы в градусах Цельсия»;
#      блок таблицы #tempTableFormPanel: рамка 1px (у ППР 2px),
#      background-image none (у ППР градиент), box-shadow ТОЛЬКО
#      inset (у ППР внешняя + inset); 3 поля .ts-calc-field 19px/52;
#      панель произвольного расчёта НЕ изменилась (2px/градиент/тень);
#      кнопка «Рассчитать» вне панели; клик «Рассчитать» — таблица
#      построена; заголовок страницы по-прежнему с типом датчика.
#   2. ТП (ТХА (K)): та же геометрия панели.
#   3. СВЕТЛАЯ тема: светлая версия углубления (рамка/тени/фон).
#   4. ДЕСКТОП 1280: панель стилизована и там (CSS не в media).
# + 0 JS-ошибок; скриншоты в download/kip8test-task495/.
import json
import os
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8983
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task495')
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
                      body='not found (browser-check t495)')

    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)


# Состояние блока таблицы + ППР + текстов
STATE_JS = r"""(() => {
    const t = document.getElementById('tempTableFormPanel');
    const p = document.getElementById('tempCustomCalcPanel');
    if (!t || !p) return {table: !!t, ppr: !!p};
    const tst = getComputedStyle(t);
    const pst = getComputedStyle(p);
    const inpCol = t.closest('.conv-col-input');
    const btn = inpCol ? inpCol.querySelector('.converter-convert-btn') : null;
    const fields = t.querySelectorAll('.ts-calc-field');
    const fs = fields.length ? getComputedStyle(fields[0]) : null;
    const mn = document.getElementById('temp_sensor_min');
    const mnst = mn ? getComputedStyle(mn) : null;
    return {
        table: true, ppr: true,
        chip: !!document.getElementById('tempSensorViewChip'),
        colText: inpCol ? inpCol.textContent : '',
        tBorderW: tst.borderWidth,
        tBorderC: tst.borderColor,
        tBgImage: tst.backgroundImage,
        tShadow: tst.boxShadow,
        tBgColor: tst.backgroundColor,
        pBorderW: pst.borderWidth,
        pBgImage: pst.backgroundImage,
        pShadow: pst.boxShadow,
        fieldsN: fields.length,
        fFont: fs ? fs.fontSize : null,
        fWeight: fs ? fs.fontWeight : null,
        fHeight: fields[0] ? Math.round(fields[0].getBoundingClientRect().height) : null,
        fColor: fs ? fs.color : null,
        mnFont: mnst ? mnst.fontSize : null,
        mnHeight: mn ? Math.round(mn.getBoundingClientRect().height) : null,
        stepVal: (document.getElementById('temp_sensor_step') || {}).value,
        minVal: (document.getElementById('temp_sensor_min') || {}).value,
        maxVal: (document.getElementById('temp_sensor_max') || {}).value,
        btnOutside: btn ? !t.contains(btn) : null,
        btnText: btn ? btn.textContent.trim() : null,
        title: (document.getElementById('tempSensorViewTitle') || {}).textContent,
        resShown: (r => r ? r.style.display : null)(
            document.getElementById('tempSensorResults')),
        resLen: (r => r ? r.innerHTML.length : 0)(
            document.getElementById('tempSensorResults'))
    };
})()"""


def open_sensor(page, key):
    page.evaluate("openTempSensor('%s')" % key)
    page.wait_for_timeout(500)


def shadows_only_inset(shadow):
    """все тени в box-shadow — inset (внешней нет)"""
    if not shadow or shadow == 'none':
        return False
    parts = [s.strip() for s in shadow.split('),') if s.strip()]
    ok = True
    for i, part in enumerate(parts):
        p = part + (')' if i < len(parts) - 1 else '')
        if 'inset' not in p:
            ok = False
    return ok


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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t495-a');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        page.evaluate("navigateTo('temp-sensors')")
        page.wait_for_timeout(600)
        open_sensor(page, 'cu50_1428')

        check('A: страница датчика активна',
              page.evaluate(
                  "document.getElementById('page-temp-sensor-view').classList.contains('active')"))
        st = page.evaluate(STATE_JS)
        check('B: чипа типа датчика в DOM НЕТ',
              st['chip'] is False, st)
        check('C: текста «Тип датчика» НЕТ',
              'Тип датчика' not in st['colText'],
              st['colText'][:200])
        check('D: подсказки «Шаг расчёта таблицы…» НЕТ',
              'Шаг расчёта таблицы в градусах Цельсия' not in st['colText'])
        check('E: панель таблицы — рамка 1px (у ППР 2px)',
              st['tBorderW'] == '1px' and st['pBorderW'] == '2px',
              (st['tBorderW'], st['pBorderW']))
        check('F: панель таблицы — БЕЗ градиента (у ППР градиент)',
              st['tBgImage'] == 'none' and
              'linear-gradient' in st['pBgImage'],
              (st['tBgImage'], st['pBgImage'][:60]))
        check('G: панель таблицы — тени ТОЛЬКО inset (углубление)',
              shadows_only_inset(st['tShadow']) and 'inset' in st['tShadow'],
              st['tShadow'][:120])
        check('H: у ППР — внешняя тень выступа осталась',
              '0px 5px 14px' in st['pShadow'].replace('  ', ' ') or
              'rgb' in st['pShadow'].split('inset')[0],
              st['pShadow'][:120])
        check('I: 3 поля ts-calc-field, 19px/52px, тёмный «колодец»',
              st['fieldsN'] == 3 and st['fFont'] == '19px' and
              st['fHeight'] == 52 and
              st['mnFont'] == '19px' and st['mnHeight'] == 52,
              (st['fieldsN'], st['fFont'], st['fHeight'],
               st['mnFont'], st['mnHeight']))
        check('J: поля яркие — 700/белый',
              str(st['fWeight']) == '700' and
              st['fColor'] == 'rgb(255, 255, 255)',
              (st['fWeight'], st['fColor']))
        check('K: кнопка «Рассчитать» ВНЕ панели',
              st['btnOutside'] is True and 'Рассчитать' in str(st['btnText']),
              (st['btnOutside'], st['btnText']))
        check('L: заголовок — тип датчика (как прежде)',
              'термометр сопротивления' in str(st['title']), st['title'])

        # расчёт таблицы через поля новой панели
        check('M: дефолты полей 0/100/10',
              st['minVal'] == '0' and st['maxVal'] == '100' and
              st['stepVal'] == '10', (st['minVal'], st['maxVal'], st['stepVal']))
        page.click('#page-temp-sensor-view .conv-col-input .converter-convert-btn')
        page.wait_for_timeout(700)
        st2 = page.evaluate(STATE_JS)
        check('N: «Рассчитать» — таблица построена',
              st2['resShown'] == 'block' and st2['resLen'] > 500,
              (st2['resShown'], st2['resLen']))
        shot(page, 'a-mobile-dark-rtd.png')
        # доп-кадр: прокрутка к панели таблицы (крупный план углубления)
        page.evaluate(
            "document.getElementById('tempTableFormPanel')"
            ".scrollIntoView({block:'center'})")
        page.wait_for_timeout(400)
        shot(page, 'e-mobile-dark-table-panel.png')

        # ============ 2. ТП — ТХА (K) ================================
        open_sensor(page, 'tc_K')
        st3 = page.evaluate(STATE_JS)
        check('O: ТХА (K) — та же геометрия (1px/без градиента/inset)',
              st3['tBorderW'] == '1px' and st3['tBgImage'] == 'none' and
              shadows_only_inset(st3['tShadow']),
              (st3['tBorderW'], st3['tBgImage'], st3['tShadow'][:60]))
        check('P: ТХА (K) — поля панели таблицы 19px/52px',
              st3['fFont'] == '19px' and st3['fHeight'] == 52 and
              st3['fieldsN'] == 3, (st3['fFont'], st3['fHeight']))
        check('Q: ТХА (K) — заголовок «термопара»',
              'термопара' in str(st3['title']), st3['title'])
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t495-b');" +
            "localStorage.setItem('kip8test:app-theme','light');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu50_1428')
        st4 = page.evaluate(STATE_JS)
        check('R: светлая — рамка 1px синеватая',
              st4['tBorderW'] == '1px' and
              '43, 111, 163' in str(st4['tBorderC']),
              (st4['tBorderW'], st4['tBorderC']))
        check('S: светлая — углубление: тени только inset',
              shadows_only_inset(st4['tShadow']) and
              'inset' in st4['tShadow'], st4['tShadow'][:120])
        check('T: светлая — без градиента, светлый «колодец»',
              st4['tBgImage'] == 'none', st4['tBgImage'][:80])
        check('U: светлая — чипа и текстов по-прежнему НЕТ',
              st4['chip'] is False and
              'Тип датчика' not in st4['colText'])
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
            "localStorage.setItem('kip8test:kip8_session_token','bc-t495-c');" +
            "localStorage.setItem('kip8test:app-theme','dark');")
        page.goto('http://localhost:%d/index.html' % PORT)
        page.wait_for_timeout(2500)
        open_sensor(page, 'cu100_1426')
        st5 = page.evaluate(STATE_JS)
        check('V: десктоп — панель стилизована (1px/inset/19px/52px)',
              st5['tBorderW'] == '1px' and
              shadows_only_inset(st5['tShadow']) and
              st5['fFont'] == '19px' and st5['fHeight'] == 52,
              (st5['tBorderW'], st5['tShadow'][:60], st5['fFont']))
        check('W: десктоп — ППР по-прежнему с выступом (2px)',
              st5['pBorderW'] == '2px', st5['pBorderW'])
        shot(page, 'd-desktop-dark-rtd.png')
        ctx.close()
        browser.close()

        print('JS-ошибок: %d / %d / %d' %
              (len(js_errors), len(js_errors2), len(js_errors3)))
        for e in (js_errors + js_errors2 + js_errors3)[:5]:
            print('  err: %s' % e[:200])
        check('X: 0 JS-ошибок во всех сессиях',
              not js_errors and not js_errors2 and not js_errors3)

    print('\nИТОГ: %d passed, %d failed' % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
