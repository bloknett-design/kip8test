// tests/test-task498.js
// Task 498: заявка пользователя — «в разделе датчиков температур
//   посмотри ещё раз пределы измерения для датчиков температуры в
//   приложении и скорректируй если есть неточности. затем укажи эти
//   пределы в градусах по цельсию и в единицах измерения в полях
//   ввода произвольного расчёта. на страницах расчёта температур, в
//   баре с названием страницы указывай только тип датчиков, например
//   "50М (Cu50) α = 0,00428 °C⁻¹", и размер шрифта сделай больше.»
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   A. SRC — формула pt1391 приведена к таблице А.2 ГОСТ 6651-2009
//      (A=3,969e-3, B=−5,841e-7, ниже 0 °C член C=−4,330e-12;
//      строки формул в getRtdSensorMap обновлены); диапазоны каталога
//      НЕ менялись (сверены с ГОСТ 6651-2009 / ГОСТ Р 8.585-2001);
//      заголовок openTempSensor — только тип датчика; подсказки
//      пределов в полях ППР (HTML div.ts-calc-range + заполнение);
//      CSS .ts-calc-range + #tempSensorViewTitle (21px/17px scrolled).
//   B. fns/VM — calcRtdResistance pt1391 по эталонам таблицы А.2
//      (−200→17,24; −150→38,79; −100→59,64; −50→80,00; 70→127,50;
//      850→395,16 для 100П); pt1385 НЕ изменилась (18,52/80,31/390,48);
//      монотонность и непрерывность в 0.
//   C. VM — openTempSensor: заголовки «50М (Cu50) α = 0,00428 °C⁻¹»
//      (и 0,00426 / 100П 0,00391 / Pt100 0,00385), ТП — только имя;
//      подсказки пределов: «−50…200 °C» + «39,3…92,8 Ом» (Cu),
//      «−200…850 °C» + «17,2444…395,16 Ом» (100П), мВ у ТП;
//      живой пересчёт с новой формулой (59,64 → ≈−100).
//   D. SW kipia-test-v722 (guard v723).

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertEqual, assertTrue, assertFalse, assertApprox } = require('./test-helpers.js');
const { extractFunctions } = require('./extract-functions.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');
const fns = extractFunctions();

// Извлечение исходника function-декларации по имени (баланс скобок)
function grabFn(name) {
    const start = INDEX_SRC.indexOf('function ' + name + '(');
    if (start === -1) return null;
    const braceStart = INDEX_SRC.indexOf('{', start);
    let depth = 0;
    for (let i = braceStart; i < INDEX_SRC.length; i++) {
        if (INDEX_SRC[i] === '{') depth++;
        else if (INDEX_SRC[i] === '}') {
            depth--;
            if (depth === 0) return INDEX_SRC.slice(start, i + 1);
        }
    }
    return null;
}

// Чанк панели ППР: от id="tempCustomCalcPanel" до конца панели
// (баланс div-ов от открывающего тега панели)
function panelChunk() {
    const i = INDEX_SRC.indexOf('id="tempCustomCalcPanel"');
    if (i === -1) return null;
    let pos = INDEX_SRC.lastIndexOf('<div', i);
    let depth = 0, started = false;
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

// ================================ A. SRC ================================

describe('Task 498 — SRC: формула pt1391 по таблице А.2 ГОСТ 6651-2009', () => {

    test('calcRtdResistance: коэффициенты 3,969e-3 / −5,841e-7 / −4,330e-12', () => {
        const fn = grabFn('calcRtdResistance');
        assertTrue(fn !== null, 'функция есть');
        assertTrue(fn.indexOf('3.969e-3') !== -1, 'A = 3,969·10⁻³');
        assertTrue(fn.indexOf('-5.841e-7') !== -1, 'B = −5,841·10⁻⁷');
        assertTrue(fn.indexOf('-4.330e-12') !== -1, 'C = −4,330·10⁻¹²');
        assertFalse(fn.indexOf('3.96847e-3') !== -1, 'старое значение A убрано');
        assertFalse(fn.indexOf('-5.84e-7') !== -1, 'старое округление B убрано');
    });

    test('calcRtdResistance: ниже 0 °C — член C·(t−100)·t³ у pt1391', () => {
        const fn = grabFn('calcRtdResistance');
        // обе ветки pt1391 различаются (раньше были одинаковыми)
        const i1391 = fn.indexOf("nsc==='pt1391'");
        const seg = fn.slice(i1391, fn.indexOf('return r0;', i1391 + 100));
        const branch = fn.slice(i1391, fn.indexOf('}', fn.indexOf("nsc==='pt1385'")) > 0 ? fn.length : fn.length);
        assertTrue(fn.indexOf('C*(t-100)*t*t*t', fn.indexOf("nsc==='pt1391'") - 200) !== -1 ||
                   fn.indexOf('C*(t-100)*t*t*t', i1391) !== -1,
            'член C есть в ветке pt1391');
        // ровно ДВЕ ветки с C-членом (pt1385 и pt1391)
        assertEqual(fn.split('C*(t-100)*t*t*t').length - 1, 2,
            'C-член в обеих платиновых ветках (pt1385 + pt1391)');
    });

    test('getRtdSensorMap: строки формул pt1391 обновлены (×2)', () => {
        const fn = grabFn('getRtdSensorMap');
        assertTrue(fn !== null, 'функция есть');
        assertEqual(fn.split('A=3,969·10⁻³').length - 1, 2, 'A в 50П и 100П');
        assertEqual(fn.split('B=−5,841·10⁻⁷').length - 1, 2, 'B в 50П и 100П');
        assertEqual(fn.split('C=−4,330·10⁻¹²').length - 1, 2, 'C в 50П и 100П');
        assertTrue(fn.indexOf('C(t−100)t³') !== -1, 'формула с C-членом');
        assertFalse(fn.indexOf('A=3,96847·10⁻³') !== -1, 'старая строка формулы убрана');
        assertFalse(fn.indexOf('B=−5,84·10⁻⁷') !== -1, 'старое округление в строке убрано');
    });

    test('Каталог: пределы НСХ НЕ менялись (сверка подтвердила)', () => {
        const fn = grabFn('getTempSensorCatalog');
        assertTrue(fn !== null, 'функция есть');
        assertTrue(fn.indexOf('range:isCu?{min:-50,max:200}:{min:-200,max:850}') !== -1,
            'Cu −50…+200 (ГОСТ 6651-2009, приложение Б), Pt −200…+850 (А.1/А.2)');
        assertTrue(fn.indexOf('K:{mat:\'хромель-алюмель\',r:[-270,1372]}') !== -1, 'K: −270…1372');
        assertTrue(fn.indexOf('L:{mat:\'хромель-копель\',r:[-200,800]}') !== -1, 'L: −200…800');
        assertTrue(fn.indexOf('B:{mat:\'платинородий-платинородий\',r:[0,1820]}') !== -1, 'B: 0…1820');
        // комментарий сверки — НАД функцией (в INDEX_SRC, вне grabFn)
        const iCat = INDEX_SRC.indexOf('function getTempSensorCatalog(');
        assertTrue(INDEX_SRC.slice(Math.max(0, iCat - 1200), iCat).indexOf('пределы НСХ каталога СВЕРЕНЫ') !== -1,
            'комментарий сверки Task 498 перед каталогом');
    });
});

describe('Task 498 — SRC: заголовок и подсказки пределов', () => {

    test('openTempSensor: заголовок — только тип датчика', () => {
        const fn = grabFn('openTempSensor');
        assertTrue(fn !== null, 'функция есть');
        // старое присваивание «имя + пояснение» удалено из КОДА
        // (в комментариях пояснения упомянуты как убранные)
        assertFalse(fn.indexOf('title.textContent=sel.name+') !== -1,
            'старое присваивание заголовка убрано');
        assertTrue(fn.indexOf('title.textContent=t498') !== -1,
            'новое присваивание через t498');
        assertTrue(fn.indexOf('°C⁻¹') !== -1, 'α с единицей °C⁻¹ (для ТС)');
        assertTrue(fn.indexOf('α = ') !== -1, 'конструкция «α = …»');
    });

    test('openTempSensor: заполняет подсказки пределов обоих полей', () => {
        const fn = grabFn('openTempSensor');
        assertTrue(fn.indexOf("tempQueryTempRange") !== -1, 'элемент пределов °C');
        assertTrue(fn.indexOf("tempQueryValRange") !== -1, 'элемент пределов Ом/мВ');
        assertTrue(fn.indexOf('tempCalcForwardValue(rng498.min)') !== -1,
            'значения на границах — через НСХ (единый источник)');
        assertTrue(fn.indexOf('getTempSensorRange()') !== -1, 'границы — из каталога');
        assertTrue(fn.indexOf("'Ом':'мВ'") !== -1, 'единица по типу датчика');
    });

    test('HTML: подсказки под обоими полями ППР (порядок)', () => {
        const p = panelChunk();
        assertTrue(p !== null, 'панель ППР найдена');
        assertEqual(p.split('class="ts-calc-range"').length - 1, 2,
            'ровно ДВА div-подсказки (без учёта комментария)');
        const iT = p.indexOf('id="tempQueryTemp"');
        const iTR = p.indexOf('id="tempQueryTempRange"');
        const iL = p.indexOf('id="tempQueryValLabel"');
        const iV = p.indexOf('id="tempQueryVal"');
        const iVR = p.indexOf('id="tempQueryValRange"');
        assertTrue(iT !== -1 && iTR !== -1 && iL !== -1 && iV !== -1 && iVR !== -1,
            'все элементы панели на месте');
        assertTrue(iT < iTR && iTR < iL, 'подсказка °C — ПОД полем температуры');
        assertTrue(iV < iVR, 'подсказка Ом/мВ — ПОД полем значения');
        // инварианты Task 494/496 не задеты
        assertEqual(p.split('class="scale-field ts-calc-field"').length - 1, 2,
            'оба поля остались ts-calc-field (Task 494)');
        assertEqual(p.split('onkeydown="tempQueryEnterBlur(event,this)"').length - 1, 2,
            'Enter-закрытие клавиатуры живо (Task 496)');
    });

    test('CSS: #tempSensorViewTitle крупнее (21px / 17px scrolled)', () => {
        assertTrue(INDEX_SRC.indexOf('#tempSensorViewTitle { font-size: 21px; }') !== -1,
            'базовый размер 21px (было 18px)');
        assertTrue(INDEX_SRC.indexOf('.page-content.scrolled #tempSensorViewTitle { font-size: 17px; }') !== -1,
            'scrolled 17px (было 15px)');
        // правки не трогают общий класс заголовков: базовое правило —
        // ровно ОДНО (правило scrolled — отдельный селектор)
        assertEqual(INDEX_SRC.split('#tempSensorViewTitle { font-size: 21px; }').length - 1, 1,
            'правило только для страницы датчика температуры');
    });

    test('CSS: .ts-calc-range — стиль подсказок (тёмная + светлая)', () => {
        assertTrue(INDEX_SRC.indexOf('.ts-calc-range { font-size: 11px;') !== -1,
            'базовое правило .ts-calc-range');
        assertTrue(INDEX_SRC.indexOf('.ts-calc-panel .ts-calc-range:last-child { margin-bottom: 0; }') !== -1,
            'нижний отступ последней подсказки убран');
        assertTrue(INDEX_SRC.indexOf('[data-theme="light"] .ts-calc-range') !== -1,
            'светлая тема');
    });

    test('Десктоп: последний сегмент крошек — тип датчика с α (как в баре)', () => {
        // хук navigateTo: updateDesktopBreadcrumb(null, l498), где
        // l498 = имя + α (ТС) / имя (ТП) — та же форма, что в заголовке
        assertTrue(INDEX_SRC.indexOf('updateDesktopBreadcrumb(null, l498)') !== -1,
            'крошки используют l498 (Task 498)');
        const iHook = INDEX_SRC.indexOf("if (page === 'temp-sensor-view' && tempSensorKey)");
        const seg = INDEX_SRC.slice(iHook, iHook + 1400);
        assertTrue(seg.indexOf('l498 = s372.name') !== -1 &&
                   seg.indexOf('°C⁻¹') !== -1 &&
                   seg.indexOf("0,00391") !== -1 && seg.indexOf("0,00385") !== -1,
            'в хуке — та же форма «имя + α», что в openTempSensor');
    });
});

// ============================ B. fns: pt1391 ============================

describe('Task 498 — calcRtdResistance: 100П по таблице А.2 ГОСТ 6651-2009', () => {

    // Эталоны — таблица А.2 ГОСТ 6651-2009 (R₀ = 100 Ом, α = 0,00391):
    // −200 → 17,24; −150 → 38,79; −100 → 59,64; −50 → 80,00; 70 → 127,50;
    // 100 → 139,11; 850 → 395,16. Совпадение в 2 знаках после запятой.
    test('100П: отрицательные температуры (раньше без члена C)', () => {
        assertApprox(fns.calcRtdResistance(-200, 100, 'pt1391'), 17.24, 0.005, 'R(−200) = 17,24');
        assertApprox(fns.calcRtdResistance(-150, 100, 'pt1391'), 38.79, 0.005, 'R(−150) = 38,79');
        assertApprox(fns.calcRtdResistance(-100, 100, 'pt1391'), 59.64, 0.005, 'R(−100) = 59,64');
        assertApprox(fns.calcRtdResistance(-50, 100, 'pt1391'), 80.00, 0.005, 'R(−50) = 80,00');
    });

    test('100П: положительные температуры', () => {
        assertApprox(fns.calcRtdResistance(0, 100, 'pt1391'), 100.00, 0.005, 'R(0) = 100,00');
        assertApprox(fns.calcRtdResistance(70, 100, 'pt1391'), 127.50, 0.005, 'R(70) = 127,50');
        assertApprox(fns.calcRtdResistance(100, 100, 'pt1391'), 139.11, 0.005, 'R(100) = 139,11');
        assertApprox(fns.calcRtdResistance(850, 100, 'pt1391'), 395.16, 0.005, 'R(850) = 395,16');
    });

    test('50П: R(−100) = 29,82 (половина от 100П)', () => {
        assertApprox(fns.calcRtdResistance(-100, 50, 'pt1391'), 29.82, 0.005, 'R(−100) 50П');
        assertApprox(fns.calcRtdResistance(-200, 50, 'pt1391'), 8.62, 0.005, 'R(−200) 50П');
    });

    test('100П: монотонность и непрерывность в 0 °C', () => {
        let prev = -1;
        for (let t = -200; t <= 850; t += 25) {
            const r = fns.calcRtdResistance(t, 100, 'pt1391');
            assertTrue(r > prev, 'R монотонно растёт при t=' + t);
            prev = r;
        }
        // C-член обнуляется при t=0: ветки стыкуются без скачка
        const eps = Math.abs(
            fns.calcRtdResistance(0, 100, 'pt1391') -
            (100 * (1 + 3.969e-3 * 0 - 5.841e-7 * 0)));
        assertTrue(eps < 1e-9, 'стык веток при 0 °C непрерывен');
    });

    test('pt1385 (IEC) НЕ изменилась: 18,52 / 80,31 / 390,48', () => {
        assertApprox(fns.calcRtdResistance(-200, 100, 'pt1385'), 18.52, 0.005, 'R(−200) Pt100');
        assertApprox(fns.calcRtdResistance(-50, 100, 'pt1385'), 80.31, 0.005, 'R(−50) Pt100');
        assertApprox(fns.calcRtdResistance(850, 100, 'pt1385'), 390.48, 0.005, 'R(850) Pt100');
    });
});

// ======================= C. VM: заголовок и пределы =======================

// VM-харнесс по образцу test-task372.js (openTempSensor + зависимости)
function makeVm() {
    const els = {};
    const mkEl = () => ({
        value: '', style: {}, innerHTML: '', textContent: '',
        placeholder: '',
        scrollIntoView: () => {}, children: [],
        _attrs: {},
        setAttribute(k, v) { this._attrs[k] = String(v); },
        getAttribute(k) { return (k in this._attrs) ? this._attrs[k] : null; },
    });
    const document = {
        getElementById: id => (els[id] || (els[id] = mkEl())),
        querySelectorAll: () => []
    };
    const toasts = [];
    const nav = [];
    const store = {};
    const ctx = {
        document,
        localStorage: {
            getItem: k => (k in store ? store[k] : null),
            setItem: (k, v) => { store[k] = String(v); },
            removeItem: k => { delete store[k]; }
        },
        showToast: m => toasts.push(String(m)),
        parseLocaleNumber: fns.parseLocaleNumber,
        formatNumber: fns.formatNumber,
        calcCuResistance: fns.calcCuResistance,
        calcRtdResistance: fns.calcRtdResistance,
        calcTcVoltage: fns.calcTcVoltage,
        setTimeout: () => 0,
        navigator: {},
        navigateTo: p => nav.push(p)
    };
    vm.createContext(ctx);
    const code = ['getRtdSensorMap', 'getTcSensorMap', 'getTempSensorCatalog',
                  'tempSensorFindByKey', 'renderTempSensorCards', 'setTempSensorsTab',
                  'toggleTempSensorFav', 'toggleTempSensorFavFromView',
                  'updateTempSensorFavBtn', 'openTempSensor',
                  'tempSensorInfoHtml', 'getTempSensorRange',
                  'tempCalcForwardValue', 'tempCalcInvertValue',
                  'tempQueryFromTemp', 'tempQueryFromValue', 'calcTempSensor']
        .map(grabFn).join('\n');
    const tempFavStart = INDEX_SRC.indexOf('var TempFav={');
    const tempFavBrace = INDEX_SRC.indexOf('{', tempFavStart);
    let tfDepth = 0, tfEnd = -1;
    for (let i = tempFavBrace; i < INDEX_SRC.length; i++) {
        if (INDEX_SRC[i] === '{') tfDepth++;
        else if (INDEX_SRC[i] === '}') { tfDepth--; if (tfDepth === 0) { tfEnd = i + 2; break; } }
    }
    const tempFavSrc = INDEX_SRC.slice(tempFavStart, tfEnd);
    vm.runInContext('var tempSensorKey=null; var tempSensorsTab=\'all\';\n' + tempFavSrc + '\n' + code + '\n;globalThis.__api = {' +
        'getTempSensorCatalog, openTempSensor, tempSensorInfoHtml, TempFav, ' +
        'getTempSensorRange, tempCalcForwardValue, tempCalcInvertValue, ' +
        'tempQueryFromTemp, tempQueryFromValue, calcTempSensor, ' +
        'setSensor: function(k){ tempSensorKey = k; }};', ctx);
    return { els, toasts, nav, api: ctx.__api };
}

describe('Task 498 — VM: заголовок — только тип датчика', () => {

    test('50М (Cu50): «50М (Cu50) α = 0,00428 °C⁻¹» (как в заявке)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent,
            '50М (Cu50) α = 0,00428 °C⁻¹', 'заголовок ТС с α = 0,00428');
    });

    test('50М (Cu50) α = 0,00426: α различает одинаковые градуировки', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1426');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent,
            '50М (Cu50) α = 0,00426 °C⁻¹', 'заголовок с α = 0,00426');
    });

    test('Платина: 100П → 0,00391; Pt100 (IEC) → 0,00385; Pt1000', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent,
            '100П (Pt100) α = 0,00391 °C⁻¹', 'заголовок 100П');
        vmw.api.openTempSensor('pt100_1385');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent,
            'Pt100 (IEC) α = 0,00385 °C⁻¹', 'заголовок Pt100 (IEC)');
        vmw.api.openTempSensor('pt1000_1385');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent,
            'Pt1000 (IEC) α = 0,00385 °C⁻¹', 'заголовок Pt1000');
    });

    test('Термопары: только наименование, без α', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_K');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent, 'ТХА (K)', 'заголовок ТХА (K)');
        vmw.api.openTempSensor('tc_B');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent, 'ТПР (B)', 'заголовок ТПР (B)');
        vmw.api.openTempSensor('tc_L');
        assertEqual(vmw.els['tempSensorViewTitle'].textContent, 'ТХК (L)', 'заголовок ТХК (L)');
    });

    test('Инварианты openTempSensor живы: дефолты, сброс, переход', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.nav[vmw.nav.length - 1], 'temp-sensor-view', 'переход');
        assertEqual(vmw.els['temp_sensor_min'].value, '0', 'min = 0');
        assertEqual(vmw.els['temp_sensor_max'].value, '100', 'max = 100');
        assertEqual(vmw.els['tempQueryValLabel'].textContent, 'Сопротивление R(t), Ом',
            'подпись второго поля (Task 373)');
        assertEqual(vmw.els['tempQueryTemp'].value, '', 'поле температуры очищено');
        assertEqual(vmw.els['tempQueryVal'].value, '', 'поле значения очищено');
    });
});

describe('Task 498 — VM: пределы в полях ввода произвольного расчёта', () => {

    test('Cu50 (0,00428): «−50…200 °C» + «39,3…92,8 Ом»', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '−50…200 °C',
            'пределы температуры в °C (минус — типографский)');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '39,3…92,8 Ом',
            'пределы сопротивления в Ом');
    });

    test('Cu50 (0,00426) и Cu100: значения от α и R₀', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1426');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '39,35…92,6 Ом',
            'Cu50 α = 0,00426');
        vmw.api.openTempSensor('cu100_1428');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '78,6…185,6 Ом',
            'Cu100 α = 0,00428 (R₀ = 100)');
    });

    test('100П: «−200…850 °C» + «17,2444…395,16 Ом» (новая формула!)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '−200…850 °C',
            'пределы Pt');
        // 17,2444 (а не 18,29 — старая формула без члена C) — А.2 ГОСТ
        assertEqual(vmw.els['tempQueryValRange'].textContent, '17,2444…395,16 Ом',
            'пределы 100П по НСХ с C-членом');
    });

    test('Pt100 (IEC): «18,5201…390,48 Ом» (ветка не менялась)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1385');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '18,5201…390,48 Ом',
            'пределы Pt100 (IEC)');
    });

    test('ТХА (K): °C + мВ; минус — типографский', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_K');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '−270…1372 °C',
            'пределы K в °C');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '−6,4577…54,8864 мВ',
            'пределы термо-ЭДС в мВ');
    });

    test('ТПР (B): нижний предел 0 → «0…13,8203 мВ»', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('tc_B');
        assertEqual(vmw.els['tempQueryTempRange'].textContent, '0…1820 °C',
            'пределы B в °C');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '0…13,8203 мВ',
            'пределы B в мВ (E(0) = 0)');
    });

    test('Смена датчика обновляет подсказки', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('cu50_1428');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '39,3…92,8 Ом', 'до смены');
        vmw.api.openTempSensor('pt100_1391');
        assertEqual(vmw.els['tempQueryValRange'].textContent, '17,2444…395,16 Ом', 'после смены');
        assertEqual(vmw.els['tempQueryValLabel'].textContent, 'Сопротивление R(t), Ом',
            'подпись для ТС');
        vmw.api.openTempSensor('tc_L');
        assertEqual(vmw.els['tempQueryValLabel'].textContent, 'Термо-ЭДС E(t), мВ',
            'подпись для ТП');
    });

    test('Живой пересчёт с новой формулой: 59,64 Ом → ≈ −100 °C (100П)', () => {
        const vmw = makeVm();
        vmw.api.openTempSensor('pt100_1391');
        vmw.els['tempQueryVal'].value = '59,64';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        const t = parseFloat(vmw.els['tempQueryTemp'].value.replace(',', '.'));
        assertTrue(isFinite(t) && Math.abs(t - (-100)) < 0.05,
            'инверсия бисекцией по НСХ с C-членом, получено ' + t);
    });
});

// ================================ D. SW ================================

describe('Task 498 — SW', () => {

    test('SW: CACHE_VERSION = kipia-test-v722, один инкремент', () => {
        assertTrue(SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v722';") !== -1,
            'CACHE_VERSION = kipia-test-v722');
    });

    test('SW: guard-версия kipia-test-v723 НЕ выпущена', () => {
        const i = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v722';");
        assertTrue(i !== -1, 'строка версии есть');
        assertFalse(SW_SRC.indexOf('kipia-test-v723') !== -1,
            'v723 в sw.js нет (guard для следующей задачи)');
    });

    test('SW: комментарий Task 498 в истории', () => {
        const i = SW_SRC.indexOf('Task 498: «Датчики температуры»');
        assertTrue(i !== -1, 'маркер Task 498 есть');
        const ver = SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v722';");
        assertTrue(i < ver, 'комментарий над версией (в блоке истории)');
    });
});
