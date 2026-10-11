// tests/test-task501.js
// Task 501: заявка пользователя — «Разделы электротехника и геометрия
//   сделай в таком же стиле. В разделе шкала-сигнал убери текст
//   "Линейная: прямая зависимость · Квадратичная: сигнал ∝ (шкала)² ·
//   Корнеизвлекающая: сигнал ∝ √(шкала)" под полем выбора типа шкалы,
//   а блок расчёта произвольных значений размести над блоком для
//   расчёта шкалы с эффектом выступа. Политру кнопок и блоков в
//   разделе датчиков температур в светлой теме адаптируй под цвета
//   светлой темы.»
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   A. SRC — «Электротехника» (circuit-breaker): 8 блоков → ОДНА
//      панель ts-calc-panel ts-calc-inset (#cbFormPanel), 7
//      разделителей, кнопка вне панели; id cb_power_block/
//      cb_current_block живы (JS-переключатели display), скрытые
//      блоки живы.
//   B. SRC — «Геометрия»: 4 страницы-объединения (#grFormPanel,
//      #gcyFormPanel, #ghFormPanel, #gcoFormPanel) + 2 одиночные
//      (классы на обёртку); кнопки вне панелей; поля живы.
//   C. SRC — «Шкала-сигнал»: текст-подсказка удалён; панель
//      произвольных значений — в колонке ввода НАД панелью шкалы
//      (ts-calc-panel без inset); scaleCustomCalcPanel удалён (HTML+JS);
//      updateScaleQueryUnits определена и вызывается (инит + пресеты +
//      расчёт + oninput единиц).
//   D. SRC — светлая тема: политура ts-элементов — ТЁПЛАЯ палитра
//      (#C6613F/rgba(198,97,63)/rgba(158,78,48)); синих литералов в
//      light-правилах ts-элементов нет; тёмная тема не тронута.
//   E. VM — updateScaleQueryUnits: единицы из полей/селектов;
//      calcScaleSignal не обращается к удалённой обёртке.
//   F. SW kipia-test-v725 + комментарий Task 501 (guard v726).

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');

// Блок страницы по id (баланс div-ов)
function pageBlock(pageId) {
    const i = INDEX_SRC.indexOf('<div id="page-' + pageId + '"');
    if (i === -1) return null;
    let pos = i, depth = 0, started = false;
    while (pos < INDEX_SRC.length) {
        const m = /<\/?div\b/.exec(INDEX_SRC.slice(pos));
        if (!m) break;
        pos = pos + m.index;
        if (INDEX_SRC[pos + 1] === '/') { depth--; } else { depth++; started = true; }
        pos += 4;
        if (started && depth === 0) return INDEX_SRC.slice(i, pos);
    }
    return null;
}

// Колонка ввода conv-3col страницы
function colInput(pageId) {
    const b = pageBlock(pageId);
    if (!b) return null;
    const i1 = b.indexOf('<div class="conv-col conv-col-input">');
    const i2 = b.indexOf('<div class="conv-col conv-col-table">');
    if (i1 === -1 || i2 === -1 || i1 > i2) return null;
    return b.slice(i1, i2);
}

// ==========================================================================
// A. ЭЛЕКТРОТЕХНИКА — объединение в одну панель
// ==========================================================================
describe('Task 501 A: электротехника (circuit-breaker) — одна панель', () => {
    test('circuit-breaker: ОДНА панель ts-calc-inset #cbFormPanel', () => {
        const col1 = colInput('circuit-breaker');
        assertTrue(col1 !== null, 'колонка ввода найдена');
        assertTrue(
            col1.indexOf('class="ts-calc-panel ts-calc-inset" id="cbFormPanel"') !== -1,
            'панель #cbFormPanel с классами колодца');
        assertEqual(col1.split('class="scale-form"').length - 1, 0,
            'обёрток .scale-form в col1 нет');
        assertEqual(col1.split('ts-calc-inset').length - 1, 1,
            'панель-«колодец» в col1 ровно одна');
    });

    test('circuit-breaker: 8 групп → 7 разделителей', () => {
        const col1 = colInput('circuit-breaker');
        // разделитель — КЛАСС label (не атрибут): CSS-селектор срабатывает
        assertEqual(col1.split('class="scale-form-label ts-calc-sep"').length - 1, 7,
            'разделителей групп: ' +
            (col1.split('class="scale-form-label ts-calc-sep"').length - 1));
    });

    test('circuit-breaker: кнопка ВНЕ панели (после неё)', () => {
        const col1 = colInput('circuit-breaker');
        const iPanel = col1.indexOf('id="cbFormPanel"');
        const iBtn = col1.indexOf('class="converter-convert-btn"');
        assertTrue(iBtn !== -1 && iPanel < iBtn, 'кнопка после панели');
        // панель закрывается до кнопки (баланс div на срезе)
        const iOpen = col1.lastIndexOf('<div', iPanel);
        const seg = col1.slice(iOpen, iBtn);
        assertEqual((seg.match(/<div\b/g) || []).length,
                    (seg.match(/<\/div>/g) || []).length,
                    'панель закрыта до кнопки');
    });

    test('circuit-breaker: JS-переключатели групп живы', () => {
        const col1 = colInput('circuit-breaker');
        ['cb_power_block', 'cb_current_block', 'cb_custom_voltage_block',
         'cb_custom_cosphi_block', 'cb_custom_cable', 'cb_supply_type',
         'cb_load_type', 'cb_consumer_type', 'cb_line_type', 'cb_curve',
         'cb_device_count', 'cb_power', 'cb_current', 'cb_custom_voltage',
         'cb_custom_cosphi', 'cb_inrush_factor', 'cb_cable_section',
         'cb_cable_material'].forEach((id) => {
            assertTrue(col1.indexOf('id="' + id + '"') !== -1,
                'элемент #' + id + ' на месте');
        });
        // JS-тумблеры display живы
        assertTrue(INDEX_SRC.indexOf(
            "document.getElementById('cb_power_block').style.display") !== -1,
            'тумблер cb_power_block жив');
        assertTrue(INDEX_SRC.indexOf(
            "document.getElementById('cb_current_block').style.display") !== -1,
            'тумблер cb_current_block жив');
        // изначально скрытая группа тока — скрыта и теперь
        const i = col1.indexOf('id="cb_current_block"');
        assertTrue(col1.slice(i, i + 120).indexOf('display:none') !== -1,
            'группа тока изначально скрыта');
    });
});

// ==========================================================================
// B. ГЕОМЕТРИЯ — панели на 6 страницах
// ==========================================================================
describe('Task 501 B: геометрия — единый стиль панелей', () => {
    const MERGED = [
        // (pageId, panelId, полей-блоков было, разделителей, поля)
        ['geo-ring', 'grFormPanel', 2, 1, ['gr_d_outer', 'gr_d_inner']],
        ['geo-cylinder', 'gcyFormPanel', 2, 1, ['gcy_diameter', 'gcy_height']],
        ['geo-horiz', 'ghFormPanel', 3, 2, ['gh_length', 'gh_diameter', 'gh_level']],
        ['geo-cone', 'gcoFormPanel', 2, 1, ['gco_diameter', 'gco_height']],
    ];

    MERGED.forEach(([pageId, panelId, nBlocks, nSeps, fields]) => {
        test(pageId + ': ОДНА панель, ' + (nBlocks - 1) + ' разделит., поля живы', () => {
            const b = pageBlock(pageId);
            assertTrue(b !== null, 'страница найдена');
            assertTrue(
                b.indexOf('class="ts-calc-panel ts-calc-inset" id="' + panelId + '"') !== -1,
                'панель #' + panelId + ' с классами колодца');
            assertEqual(
                b.split('class="scale-form-label ts-calc-sep"').length - 1, nSeps,
                'разделителей: ' +
                (b.split('class="scale-form-label ts-calc-sep"').length - 1));
            // обёрток больше нет, кнопка после панели
            const iPanel = b.indexOf('id="' + panelId + '"');
            const iBtn = b.indexOf('class="converter-convert-btn');
            assertTrue(iBtn > iPanel, 'кнопка после панели');
            const iOpen = b.lastIndexOf('<div', iPanel);
            const seg = b.slice(iOpen, iBtn);
            assertEqual((seg.match(/<div\b/g) || []).length,
                        (seg.match(/<\/div>/g) || []).length,
                        'панель закрыта до кнопки');
            fields.forEach((id) => {
                assertTrue(b.indexOf('id="' + id + '"') !== -1,
                    'поле #' + id + ' живо');
            });
        });
    });

    ['geo-circle', 'geo-sphere'].forEach((pageId) => {
        test(pageId + ': обёртка с классами панели', () => {
            const b = pageBlock(pageId);
            assertTrue(b !== null, 'страница найдена');
            assertTrue(
                b.indexOf('class="scale-form ts-calc-panel ts-calc-inset"') !== -1,
                'блок получил классы панели (как конвертер Task 500)');
            const iBtn = b.indexOf('class="converter-convert-btn');
            assertTrue(iBtn !== -1, 'кнопка на месте');
        });
    });

    test('геометрия: живые функции расчёта', () => {
        ['calcGeoCircle', 'calcGeoRing', 'calcGeoCylinder',
         'calcGeoHorizCyl', 'calcGeoSphere', 'calcGeoCone'].forEach((fn) => {
            assertTrue(INDEX_SRC.indexOf('function ' + fn + '(') !== -1,
                'функция ' + fn + ' жива');
        });
    });
});

// ==========================================================================
// C. ШКАЛА-СИГНАЛ — подсказка удалена, панель ППР над панелью шкалы
// ==========================================================================
describe('Task 501 C: шкала-сигнал', () => {
    test('текст-подсказка под типом шкалы удалён', () => {
        assertFalse(INDEX_SRC.indexOf(
            'Линейная: прямая зависимость · Квадратичная: сигнал ∝ (шкала)²') !== -1,
            'подсказка удалена из index.html');
        assertFalse(INDEX_SRC.indexOf('Корнеизвлекающая: сигнал ∝ √(шкала)') !== -1,
            'второй фрагмент подсказки удалён');
        // выбор типа шкалы жив
        const col1 = colInput('scale-signal');
        assertTrue(col1.indexOf('id="scaleType"') !== -1, 'селект типа шкалы жив');
        assertTrue(col1.indexOf('Корнеизвлекающая') !== -1,
            'опция «Корнеизвлекающая» в селекте жива');
    });

    test('панель произвольных значений — НАД панелью расчёта шкалы', () => {
        const col1 = colInput('scale-signal');
        const iQ = col1.indexOf('id="scaleQueryPanel"');
        const iF = col1.indexOf('id="scaleFormPanel"');
        assertTrue(iQ !== -1 && iF !== -1 && iQ < iF,
            'ППР выше панели шкалы');
        assertTrue(col1.indexOf('class="ts-calc-panel" id="scaleQueryPanel"') !== -1,
            'ППР — ts-calc-panel БЕЗ inset (эффект выступа)');
        assertTrue(col1.indexOf('ts-calc-inset" id="scaleQueryPanel"') === -1,
            'НЕ колодец');
        // поля и подсказка панели живы
        const seg = col1.slice(iQ, iQ + 2400);
        ['queryScaleVal', 'querySigVal', 'scaleQueryUnit',
         'scaleQuerySigUnit'].forEach((id) => {
            assertTrue(seg.indexOf('id="' + id + '"') !== -1, '#' + id + ' жив');
        });
        assertTrue(seg.indexOf('queryFromScaleLive()') !== -1, 'живой расчёт жив');
        // кнопка «Рассчитать» — после ОБОИХ панелей
        const iBtn = col1.indexOf('class="scale-calc-btn"');
        assertTrue(iBtn > iF, 'кнопка после панелей');
    });

    test('scaleCustomCalcPanel удалён (HTML и JS)', () => {
        assertFalse(INDEX_SRC.indexOf('scaleCustomCalcPanel') !== -1,
            'упоминаний scaleCustomCalcPanel нет нигде');
        // расчёт по-прежнему показывает результаты и чистит поля ППР
        const fn = INDEX_SRC.slice(
            INDEX_SRC.indexOf('function calcScaleSignal()'),
            INDEX_SRC.indexOf('function queryFromScaleLive()'));
        assertTrue(fn.indexOf("scaleResultsArea').style.display='block'") !== -1,
            'показ результатов жив');
        assertTrue(fn.indexOf('queryScaleVal').value=''.length > 0 ||
                   fn.indexOf("document.getElementById('queryScaleVal').value=''") !== -1,
            'очистка полей ППР жива');
    });

    test('updateScaleQueryUnits: функция + вызовы + oninput', () => {
        assertTrue(INDEX_SRC.indexOf('function updateScaleQueryUnits()') !== -1,
            'функция определена');
        assertEqual(INDEX_SRC.split('updateScaleQueryUnits(').length - 1, 7,
            'вхождений (1 def + 4 вызова + 2 oninput): ' +
            (INDEX_SRC.split('updateScaleQueryUnits(').length - 1));
        // инит при загрузке
        const fnI = INDEX_SRC.indexOf('function updateScaleQueryUnits()');
        const seg = INDEX_SRC.slice(fnI, fnI + 900);
        assertTrue(seg.indexOf('updateScaleQueryUnits();') !== -1,
            'инит-вызов сразу после определения');
        // поля своих единиц обновляют подписи
        const iSu = INDEX_SRC.indexOf('id="scaleUnitName"');
        assertTrue(INDEX_SRC.slice(iSu - 200, iSu + 200).indexOf(
            'oninput="updateScaleQueryUnits()"') !== -1,
            'oninput у scaleUnitName');
        const iSgu = INDEX_SRC.indexOf('id="sigUnitCustom"');
        assertTrue(INDEX_SRC.slice(iSgu - 200, iSgu + 200).indexOf(
            'oninput="updateScaleQueryUnits()"') !== -1,
            'oninput у sigUnitCustom');
    });
});

// ==========================================================================
// D. СВЕТЛАЯ ТЕМА — тёплая политура ts-элементов
// ==========================================================================
describe('Task 501 D: светлая тема — тёплая палитра политры', () => {
    test('панель-выступ: рамка/градиент/тени — терракотовые', () => {
        const rule = INDEX_SRC.indexOf('[data-theme="light"] .ts-calc-panel {');
        const seg = INDEX_SRC.slice(rule, INDEX_SRC.indexOf('}', rule) + 1);
        assertTrue(seg.indexOf('rgba(198, 97, 63, 0.55)') !== -1,
            'рамка терракотовая');
        assertTrue(seg.indexOf('rgba(198, 97, 63, 0.13)') !== -1,
            'градиент тёплый');
        assertTrue(seg.indexOf('rgba(158, 78, 48, 0.22)') !== -1,
            'тень тёплая');
        assertFalse(seg.indexOf('43, 111, 163') !== -1, 'синей рамки нет');
        assertFalse(seg.indexOf('21, 54, 83') !== -1, 'синих теней нет');
    });

    test('колодец: фон/рамка — тёплые', () => {
        const rule = INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-calc-panel.ts-calc-inset {');
        const seg = INDEX_SRC.slice(rule, INDEX_SRC.indexOf('}', rule) + 1);
        assertTrue(seg.indexOf('rgba(198, 97, 63, 0.05)') !== -1, 'фон тёплый');
        assertTrue(seg.indexOf('rgba(198, 97, 63, 0.22)') !== -1, 'рамка тёплая');
        assertFalse(seg.indexOf('21, 54, 83') !== -1, 'синего фона нет');
    });

    test('фокус полей/селектов в панелях — терракотовое кольцо', () => {
        const i = INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-calc-field:focus {');
        const seg = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
        assertTrue(seg.indexOf('rgba(198, 97, 63, 0.65)') !== -1,
            'фокус ts-calc-field терракотовый');
        const i2 = INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-calc-panel input.scale-field:focus');
        const seg2 = INDEX_SRC.slice(i2, INDEX_SRC.indexOf('background: rgba(255, 255, 255, 0.92);', i2));
        assertTrue(seg2.indexOf('rgba(198, 97, 63, 0.65)') !== -1,
            'фокус полей в панелях терракотовый');
        const i3 = INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-calc-panel .cs-trigger:focus');
        const seg3 = INDEX_SRC.slice(i3, INDEX_SRC.indexOf('}', i3) + 200);
        assertTrue(seg3.indexOf('rgba(198, 97, 63, 0.65)') !== -1,
            'фокус cs-trigger терракотовый');
    });

    test('каталог: табы/звёзды/featured/бар — терракотовые', () => {
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-card-fav-btn.active { color: #C6613F;') !== -1,
            'звёздочка активная #C6613F');
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-tab.active {') !== -1 &&
            INDEX_SRC.indexOf('background: rgba(198, 97, 63, 0.12); color: #C6613F; }') !== -1,
            'активный таб терракотовый');
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-tab.active .ts-tab-count { background: #C6613F;') !== -1,
            'счётчик активного таба терракотовый');
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] #tempSensorFavBtn.active { color: #C6613F; }') !== -1,
            'звёздочка шапки терракотовая');
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] #tsBottomBar .ts-tab.active { color: #C6613F; }') !== -1,
            'таб нижнего бара терракотовый');
        const i = INDEX_SRC.indexOf('[data-theme="light"] .ts-card-feat {');
        const seg = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
        assertTrue(seg.indexOf('rgba(198, 97, 63, 0.55)') !== -1,
            'featured-карточка тёплая');
    });

    test('новые light-правила: контур табов, hover карточек, заглушка', () => {
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-tabs { border-color: rgba(20, 20, 19, 0.15); }') !== -1,
            'контур табов нейтральный');
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-empty-fav-hint .star { color: #C6613F; }') !== -1,
            'звёздочка заглушки терракотовая');
        assertTrue(INDEX_SRC.indexOf(
            '[data-theme="light"] .ts-empty-fav-icon { color: rgba(198, 97, 63, 0.4); }') !== -1,
            'иконка заглушки терракотовая');
    });

    test('синих литералов в light-правилах ts-элементов НЕТ', () => {
        const lines = INDEX_SRC.split('\n');
        const bad = lines.filter((line) =>
            line.indexOf('[data-theme="light"]') !== -1 &&
            (line.indexOf('.ts-') !== -1 || line.indexOf('tsBottomBar') !== -1 ||
             line.indexOf('tempSensorFav') !== -1) &&
            (line.indexOf('43, 111, 163') !== -1 || line.indexOf('2b6fa3') !== -1 ||
             line.indexOf('rgba(74, 143, 199') !== -1 ||
             line.indexOf('21, 54, 83') !== -1));
        assertEqual(bad.length, 0,
            'синие light-литералы: ' + (bad.length ? bad[0].trim().slice(0, 80) : 'нет'));
    });

    test('тёмная тема НЕ тронута (синий — акцент тёмной)', () => {
        assertTrue(INDEX_SRC.indexOf(
            '.ts-calc-panel { padding: 16px;') !== -1, 'базовая панель жива');
        assertTrue(INDEX_SRC.indexOf(
            'rgba(74, 143, 199, 0.85); border-radius: 14px; margin: 8px 0 12px;') !== -1,
            'синяя рамка 2px тёмной темы жива');
        assertTrue(INDEX_SRC.indexOf(
            '.ts-tab.active { background: rgba(74, 143, 199, 0.15); color: #4a8fc7; }') !== -1,
            'тёмные табы живы');
        assertTrue(INDEX_SRC.indexOf(
            '.ts-card-fav-btn.active { color: #4a8fc7;') !== -1,
            'тёмная звёздочка жива');
    });
});

// ==========================================================================
// E. VM — updateScaleQueryUnits
// ==========================================================================
describe('Task 501 E: VM — живые единицы панели ППР шкала-сигнал', () => {
    function makeCtx() {
        const els = {};
        const mk = (id, props) => {
            els[id] = Object.assign({
                style: {}, textContent: '', innerText: '', value: '',
                innerHTML: '', display: '', scrollTop: 0,
            }, props);
            return els[id];
        };
        mk('scaleUnitName', { value: '°C' });
        mk('sigType', { value: '4_20' });
        mk('scaleQueryUnit', {});
        mk('scaleQuerySigUnit', {});
        const document = {
            getElementById: (id) => els[id] || null,
            querySelector: () => null,
            querySelectorAll: () => [],
        };
        const ctx = {
            document,
            Math, isNaN, parseFloat, parseInt, String, Number, Array, Object,
            console: { log: () => {} },
            setTimeout: () => {},
        };
        vm.createContext(ctx);
        return { ctx, els };
    }

    function grabFn(name) {
        const start = INDEX_SRC.indexOf('function ' + name + '(');
        if (start === -1) return null;
        const brace = INDEX_SRC.indexOf('{', start);
        let depth = 0;
        for (let i = brace; i < INDEX_SRC.length; i++) {
            if (INDEX_SRC[i] === '{') depth++;
            else if (INDEX_SRC[i] === '}') {
                depth--;
                if (depth === 0) return INDEX_SRC.slice(start, i + 1);
            }
        }
        return null;
    }

    test('updateScaleQueryUnits: единицы из полей и селекта сигнала', () => {
        const fn = grabFn('updateScaleQueryUnits');
        assertTrue(fn !== null, 'функция извлечена');
        const { ctx, els } = makeCtx();
        const fnSig = grabFn('getSignalRangeAndUnit');
        assertTrue(fnSig !== null, 'getSignalRangeAndUnit извлечена');
        vm.runInContext(fnSig + '\n' + fn + '\n;updateScaleQueryUnits();', ctx);
        assertEqual(els.scaleQueryUnit.textContent, '°C', 'единица шкалы из поля');
        assertEqual(els.scaleQuerySigUnit.textContent, 'мА',
            'единица сигнала 4-20 мА');
        // смена типа сигнала → смена единицы
        els.sigType.value = '0_10V';
        vm.runInContext('updateScaleQueryUnits();', ctx);
        assertEqual(els.scaleQuerySigUnit.textContent, 'В', '0-10 В → «В»');
        // пустая единица шкалы → «ед.»
        els.scaleUnitName.value = '';
        vm.runInContext('updateScaleQueryUnits();', ctx);
        assertEqual(els.scaleQueryUnit.textContent, 'ед.', 'пусто → «ед.»');
    });

    test('calcScaleSignal: обращений к удалённой обёртке нет', () => {
        const fn = grabFn('calcScaleSignal');
        assertTrue(fn !== null, 'функция извлечена');
        assertFalse(fn.indexOf('scaleCustomCalcPanel') !== -1,
            'scaleCustomCalcPanel не упоминается');
        assertTrue(fn.indexOf('updateScaleQueryUnits') !== -1,
            'единицы обновляются живой функцией');
    });
});

// ==========================================================================
// F. SW — версия и комментарий
// ==========================================================================
describe('Task 501 F: Service Worker', () => {
    test("sw.js: CACHE_VERSION = 'kipia-test-v725'", () => {
        assertTrue(
            SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v725';") !== -1,
            'версия v725');
        assertFalse(SW_SRC.indexOf('kipia-test-v726') !== -1,
            'v726 ещё не выпущена');
    });

    test('sw.js: комментарий Task 501 в шапке версий', () => {
        const i = SW_SRC.indexOf('const CACHE_VERSION');
        const head = SW_SRC.slice(Math.max(0, i - 1200), i);
        assertTrue(head.indexOf('Task 501') !== -1, 'маркер Task 501');
        assertTrue(head.indexOf('Электротехника') !== -1,
            'упоминание разделов заявки');
    });
});
