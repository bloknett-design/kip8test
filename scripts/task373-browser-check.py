#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 373: browser-check — доработки «Датчиков температуры»:
#   1. десктоп 1280 тёмная: 17 карточек (8 ТС + 9 ТП, есть ТХК (L));
#      табы «Все 17 / Избранные 0»; бейджей ТС/ТП на карточках НЕТ;
#      звёзды на карточках; клик ☆ → ★, счётчик, localStorage
#      kip8_temp_fav_v1; таб «Избранные» — только избранные (пустые
#      группы скрыты), без избранного — заглушка; ТХК (L) → страница
#      датчика: панель «Расчёт произвольных значений» НАД формой
#      выбора диапазона/шага (видна СРАЗУ, до «Рассчитать»), подпись
#      «Термо-ЭДС E(t), мВ»; звезда в шапке; живой расчёт
#      t=100 → 6,862 мВ; «Рассчитать» → таблица БЕЗ панели под ней;
#      справка L — «только в ГОСТ».
#   2. светлая тема: карточки/табы/звёзды читаемы.
#   3. мобайл 375: карточки СТОЛБИКОМ по одной в строке, на всю
#      ширину с отступами ~12px по краям; табы работают.
# + 0 JS-ошибок; скриншот-пруфы (desktop/light/mobile).
import json
import sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8974

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local', 'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'flowmeter.view': True, 'workschedule.view': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    return {'ok': True, 'data': {'ok': True}}

PASS = 0
FAIL = 0
def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok: PASS += 1
    else: FAIL += 1
    print(('  ✓ ' if ok else '  ✗ ') + name + (('  [' + str(extra) + ']') if (extra and not ok) else ''))

def parse_ru(s):
    s = str(s).replace('\u00a0', '').replace(',', '.')
    try: return float(s)
    except Exception: return None

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ================= Контекст 1: десктоп 1280, тёмная =================
    ctx = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t373)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    ctx.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t373-a');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("document.title==='КИПиА'"))

    # --- страница выбора: карточки ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(800)
    check('B: страница «Датчики температуры» активна',
          page.evaluate("document.getElementById('page-temp-sensors').classList.contains('active')"))
    check('C: карточек ТС = 8',
          page.evaluate("document.querySelectorAll('#tsRtdCards .ts-card').length") == 8,
          page.evaluate("document.querySelectorAll('#tsRtdCards .ts-card').length"))
    check('D: карточек ТП = 9 (добавлена ТХК (L))',
          page.evaluate("document.querySelectorAll('#tsTcCards .ts-card').length") == 9,
          page.evaluate("document.querySelectorAll('#tsTcCards .ts-card').length"))
    check('E: карточка ТХК (L) с электродами и диапазоном',
          page.evaluate("""(function(){
            var cards = document.querySelectorAll('#tsTcCards .ts-card');
            for (var i=0;i<cards.length;i++){
              var t = cards[i].textContent;
              if (t.indexOf('ТХК (L)') !== -1){
                return t.indexOf('хромель-копель') !== -1 && t.indexOf('−200…800') !== -1;
              }
            }
            return false;
          })()"""))
    check('F: бейджей ТС/ТП на карточках НЕТ',
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card-badge').length") == 0,
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card-badge').length"))
    check('G: бейджи остались в заголовках групп (ТС/ТП)',
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-group-badge').length") == 2)
    check('H: табы «Все / Избранные» со счётчиками 17 / 0',
          page.evaluate("document.getElementById('tsAllCount').textContent") == '17' and
          page.evaluate("document.getElementById('tsFavCount').textContent") == '0')
    check('I: звёздочка на каждой карточке (17)',
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card-fav-btn').length") == 17,
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card-fav-btn').length"))

    # --- избранное: звезда на карточке Pt100 ---
    page.click("#tsRtdCards .ts-card:has-text('Pt100 (IEC)') .ts-card-fav-btn")
    page.wait_for_timeout(400)
    check('J: после клика ☆ → ★, счётчик «Избранные 1»',
          page.evaluate("""(function(){
            var cards = document.querySelectorAll('#tsRtdCards .ts-card');
            for (var i=0;i<cards.length;i++){
              if (cards[i].textContent.indexOf('Pt100 (IEC)') !== -1){
                var b = cards[i].querySelector('.ts-card-fav-btn');
                return b ? b.textContent : null;
              }
            }
            return null;
          })()""") == '★' and
          page.evaluate("document.getElementById('tsFavCount').textContent") == '1',
          page.evaluate("document.getElementById('tsFavCount').textContent"))
    check('K: localStorage kip8_temp_fav_v1 с ключом pt100_1385',
          page.evaluate("""(function(){
            var raw = localStorage.getItem('kip8_temp_fav_v1');
            return !!raw && raw.indexOf('pt100_1385') !== -1;
          })()"""))

    # --- таб «Избранные»: только избранные, пустые группы скрыты ---
    page.click(".ts-tab[data-ts-tab='fav']")
    page.wait_for_timeout(400)
    check('L: в «Избранных» 1 карточка (Pt100)',
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card').length") == 1,
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card').length"))
    check('M: заголовок группы ТП скрыт (ТП нет в избранном)',
          page.evaluate("document.getElementById('tsTcGroupTitle').style.display") == 'none' and
          page.evaluate("document.getElementById('tsRtdGroupTitle').style.display") != 'none')

    # --- добавить ТХК (L) в избранное из его карточки ---
    page.click(".ts-tab[data-ts-tab='all']")
    page.wait_for_timeout(300)
    page.click("#tsTcCards .ts-card:has-text('ТХК (L)') .ts-card-fav-btn")
    page.wait_for_timeout(300)
    check('N: счётчик «Избранные 2»',
          page.evaluate("document.getElementById('tsFavCount').textContent") == '2',
          page.evaluate("document.getElementById('tsFavCount').textContent"))
    page.click(".ts-tab[data-ts-tab='fav']")
    page.wait_for_timeout(400)
    check('O: в «Избранных» 2 карточки (Pt100 + ТХК L), обе группы видны',
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card').length") == 2 and
          page.evaluate("document.getElementById('tsRtdGroupTitle').style.display") != 'none' and
          page.evaluate("document.getElementById('tsTcGroupTitle').style.display") != 'none',
          page.evaluate("document.querySelectorAll('#page-temp-sensors .ts-card').length"))

    # --- убрать всё → заглушка «Нет избранных датчиков» ---
    page.click("#tsRtdCards .ts-card:has-text('Pt100 (IEC)') .ts-card-fav-btn")
    page.wait_for_timeout(200)
    page.click("#tsTcCards .ts-card:has-text('ТХК (L)') .ts-card-fav-btn")
    page.wait_for_timeout(400)
    check('P: заглушка «Нет избранных датчиков» + группы скрыты',
          page.evaluate("document.getElementById('tsRtdCards').textContent.indexOf('Нет избранных датчиков') !== -1") and
          page.evaluate("document.getElementById('tsRtdGroupTitle').style.display") == 'none' and
          page.evaluate("document.getElementById('tsTcGroupTitle').style.display") == 'none')

    # --- страница датчика ТХК (L) ---
    page.click(".ts-tab[data-ts-tab='all']")
    page.wait_for_timeout(300)
    page.click("#tsTcCards .ts-card:has-text('ТХК (L)')")
    page.wait_for_timeout(600)
    check('Q: перешли на страницу ТХК (L)',
          page.evaluate("document.getElementById('page-temp-sensor-view').classList.contains('active')") and
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent").strip().endswith('ТХК (L)'),
          page.evaluate("document.getElementById('tempSensorViewTitle').textContent"))
    check('R: панель «Расчёт произвольных значений» НАД формой выбора (DOM-порядок)',
          page.evaluate("""(function(){
            var panel = document.getElementById('tempCustomCalcPanel');
            var range = document.getElementById('temp_sensor_min');
            if (!panel || !range) return false;
            // панель — предыдущий сосед формы (или выше по документу)
            return panel.compareDocumentPosition(range) & Node.DOCUMENT_POSITION_FOLLOWING;
          })()"""))
    check('S: панель видна СРАЗУ (до «Рассчитать»)',
          page.evaluate("""(function(){
            var panel = document.getElementById('tempCustomCalcPanel');
            var st = getComputedStyle(panel);
            return st.display !== 'none' && panel.offsetHeight > 40;
          })()"""))
    check('T: подпись второго поля — «Термо-ЭДС E(t), мВ»',
          page.evaluate("document.getElementById('tempQueryValLabel').textContent.trim()") == 'Термо-ЭДС E(t), мВ',
          page.evaluate("document.getElementById('tempQueryValLabel').textContent"))
    check('U: чип без бейджа ТС/ТП',
          page.evaluate("document.querySelectorAll('#tempSensorViewChip .ts-card-badge').length") == 0 and
          page.evaluate("document.getElementById('tempSensorViewChip').textContent.indexOf('ТХК (L)') !== -1"))
    check('V: звезда в шапке страницы датчика (☆)',
          page.evaluate("document.getElementById('tempSensorFavBtn').textContent") == '☆')

    # --- звезда в шапке: добавление и синхронизация ---
    page.click("#tempSensorFavBtn")
    page.wait_for_timeout(300)
    check('W: звезда в шапке → ★, датчик в избранном',
          page.evaluate("document.getElementById('tempSensorFavBtn').textContent") == '★' and
          page.evaluate("(function(){var r=localStorage.getItem('kip8_temp_fav_v1');return !!r&&r.indexOf('tc_L')!==-1;})()"))

    # --- живой расчёт t=100 → 6,862 мВ ---
    page.fill("#tempQueryTemp", "100")
    page.wait_for_timeout(500)
    val100 = parse_ru(page.evaluate("document.getElementById('tempQueryVal').value"))
    check('X: живой расчёт E(100) ≈ 6,862 мВ', val100 is not None and abs(val100 - 6.862) < 0.005, val100)
    # обратно: E=14,56 → t≈200
    page.fill("#tempQueryVal", "14,56")
    page.wait_for_timeout(500)
    t200 = parse_ru(page.evaluate("document.getElementById('tempQueryTemp').value"))
    check('Y: инверсия E=14,56 → t ≈ 200 °C', t200 is not None and abs(t200 - 200) < 0.5, t200)

    # --- «Рассчитать»: таблица есть, панели под ней НЕТ ---
    page.fill("#temp_sensor_min", "0")
    page.fill("#temp_sensor_max", "200")
    page.fill("#temp_sensor_step", "100")
    page.click("#page-temp-sensor-view .converter-convert-btn")
    page.wait_for_timeout(700)
    check('Z: таблица E(t) построена (E(200) ≈ 14,56 мВ)',
          page.evaluate("""(function(){
            var t = document.getElementById('tempSensorResults').textContent;
            return t.indexOf('ТХК (L)') !== -1 && t.indexOf('14,56') !== -1;
          })()"""))
    check('AA: панели «Расчёт произвольных значений» в результатах НЕТ',
          page.evaluate("document.getElementById('tempSensorResults').querySelectorAll('#tempCustomCalcPanel').length") == 0 and
          page.evaluate("document.getElementById('tempSensorResults').textContent.indexOf('Расчёт произвольных значений')") == -1)
    check('AB: справка ТХК (L) — «только в ГОСТ», без полиномов НИСТ',
          page.evaluate("""(function(){
            var h = document.getElementById('tempSensorInfoBody').textContent;
            return h.indexOf('только в ГОСТ') !== -1 && h.indexOf('SRD 60') === -1;
          })()"""))

    # --- обратно в список: звезда ТХК (L) на карточке ★ (синхронизация) ---
    page.evaluate("navigateTo('temp-sensors')")
    page.wait_for_timeout(600)
    check('AC: на карточке ТХК (L) звезда ★ (синхронизация со страницей датчика)',
          page.evaluate("""(function(){
            var cards = document.querySelectorAll('#tsTcCards .ts-card');
            for (var i=0;i<cards.length;i++){
              if (cards[i].textContent.indexOf('ТХК (L)') !== -1){
                var b = cards[i].querySelector('.ts-card-fav-btn');
                return b ? b.textContent : null;
              }
            }
            return null;
          })()""") == '★')
    check('AD: счётчик «Избранные 1»',
          page.evaluate("document.getElementById('tsFavCount').textContent") == '1',
          page.evaluate("document.getElementById('tsFavCount').textContent"))

    page.screenshot(path='scripts/task373-proof-desktop.png', full_page=False)
    check('AE: десктоп — 0 JS-ошибок', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ================= Контекст 2: светлая тема =================
    ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    page2.on('dialog', lambda d: d.accept())
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)
    ctx2.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t373-b');" +
        "localStorage.setItem('kip8test:app-theme','light');")
    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('temp-sensors')")
    page2.wait_for_timeout(800)
    check('AF: светлая — карточки и табы читаемы (цвет текста карточки тёмный)',
          page2.evaluate("""(function(){
            var name = document.querySelector('#tsRtdCards .ts-card .ts-card-name');
            var rgb = getComputedStyle(name).color;
            return rgb.indexOf('255') === -1;  // не белый на светлом
          })()"""))
    page2.click("#tsRtdCards .ts-card:has-text('Pt100 (IEC)') .ts-card-fav-btn")
    page2.wait_for_timeout(300)
    check('AG: светлая — активная звезда читаема (не белая)',
          page2.evaluate("""(function(){
            var cards = document.querySelectorAll('#tsRtdCards .ts-card');
            for (var i=0;i<cards.length;i++){
              if (cards[i].textContent.indexOf('Pt100 (IEC)') !== -1){
                var b = cards[i].querySelector('.ts-card-fav-btn.active');
                if (!b) return false;
                return getComputedStyle(b).color.indexOf('255, 255, 255') === -1;
              }
            }
            return false;
          })()"""))
    page2.screenshot(path='scripts/task373-proof-light.png', full_page=False)
    check('AH: светлая — 0 JS-ошибок', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()

    # ================= Контекст 3: мобайл 375 =================
    ctx3 = browser.new_context(viewport={'width': 375, 'height': 720}, is_mobile=True, has_touch=True)
    page3 = ctx3.new_page()
    js_errors3 = []
    page3.on('pageerror', lambda e: js_errors3.append(str(e)))
    page3.on('dialog', lambda d: d.accept())
    ctx3.route('**/exec?**', handle)
    ctx3.route('**script.google.com/**', handle)
    ctx3.route('**raw.githubusercontent.com/**', block_external)
    ctx3.route('**calendar.legalic.ru/**', block_external)
    ctx3.add_init_script(
        "localStorage.setItem('kip8test:kip8_session_token','bc-t373-c');" +
        "localStorage.setItem('kip8test:app-theme','dark');")
    page3.goto('http://localhost:%d/index.html' % PORT)
    page3.wait_for_timeout(2500)
    page3.evaluate("navigateTo('temp-sensors')")
    page3.wait_for_timeout(800)
    # карточки столбиком: одна колонка
    grid_cols = page3.evaluate("""(function(){
            var g = getComputedStyle(document.getElementById('tsRtdCards'));
            return g.gridTemplateColumns;
          })()""")
    n_tracks = len([c for c in grid_cols.split() if c.replace('.', '').replace('-', '').isdigit()]) if grid_cols != 'none' else 0
    check('AI: мобайл — сетка ОДНА колонка (столбиком)',
          grid_cols != 'none' and n_tracks <= 1, grid_cols)
    # карточка на всю ширину строки с небольшими отступами по краям
    geom = page3.evaluate("""(function(){
            var page = document.querySelector('#page-temp-sensors .ts-page');
            var card = document.querySelector('#tsRtdCards .ts-card');
            var rect = card.getBoundingClientRect();
            return { left: rect.left, right: window.innerWidth - rect.right,
                     width: rect.width, vw: window.innerWidth,
                     pad: getComputedStyle(page).paddingLeft };
          })()""")
    check('AJ: мобайл — карточка на всю строку (отступы ≤ 20px по краям)',
          geom['left'] <= 20 and geom['right'] <= 20 and geom['width'] >= geom['vw'] - 44,
          geom)
    check('AK: мобайл — отступ .ts-page = 12px', geom['pad'] == '12px', geom['pad'])
    # все карточки в один столбик: у каждой ширина ≈ одинаковая (полная)
    widths = page3.evaluate("""(function(){
            var cards = document.querySelectorAll('#page-temp-sensors .ts-card');
            var out = [];
            for (var i=0;i<cards.length;i++) out.push(Math.round(cards[i].getBoundingClientRect().width));
            return out;
          })()""")
    check('AL: мобайл — все 17 карточек полной ширины (разброс ≤ 2px)',
          len(widths) == 17 and max(widths) - min(widths) <= 2, (len(widths), min(widths), max(widths)))
    page3.screenshot(path='scripts/task373-proof-mobile-cards.png', full_page=False)
    # табы работают на мобильном
    page3.click(".ts-tab[data-ts-tab='fav']")
    page3.wait_for_timeout(400)
    check('AM: мобайл — таб «Избранные» работает (заглушка)',
          page3.evaluate("document.getElementById('tsRtdCards').textContent.indexOf('Нет избранных датчиков') !== -1"))
    page3.click(".ts-tab[data-ts-tab='all']")
    page3.wait_for_timeout(300)
    # страница датчика: панель над формой, живой расчёт
    page3.click("#tsTcCards .ts-card:has-text('ТХК (L)')")
    page3.wait_for_timeout(600)
    check('AN: мобайл — панель расчёта над формой выбора',
          page3.evaluate("""(function(){
            var panel = document.getElementById('tempCustomCalcPanel');
            var range = document.getElementById('temp_sensor_min');
            return !!panel && !!range && (panel.compareDocumentPosition(range) & Node.DOCUMENT_POSITION_FOLLOWING);
          })()"""))
    page3.fill("#tempQueryTemp", "100")
    page3.wait_for_timeout(500)
    val_m = parse_ru(page3.evaluate("document.getElementById('tempQueryVal').value"))
    check('AO: мобайл — живой расчёт E(100) ≈ 6,862', val_m is not None and abs(val_m - 6.862) < 0.005, val_m)
    page3.screenshot(path='scripts/task373-proof-mobile.png', full_page=False)
    check('AP: мобайл — 0 JS-ошибок', len(js_errors3) == 0, js_errors3[:3])
    ctx3.close()

    browser.close()

print('')
print('ИТОГО: %d passed, %d failed (из %d)' % (PASS, FAIL, PASS + FAIL))
sys.exit(0 if FAIL == 0 else 1)
