// tests/test-task371.js
// Task 371: заявка пользователя — «На странице Главная / Инженерные
//   калькуляторы / КИП и А / Датчики температуры, под блоком Таблица
//   значений добавь блок Расчёт произвольных значений, по примеру
//   как в разделе Шкала-сигнал.»
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   A. SRC — панель «Расчёт произвольных значений» в ОБЕИХ ветках
//      calcTempSensor() (ТС: «Сопротивление R(t), Ом»; ТП: «Термо-ЭДС
//      E(t), мВ»), ПОСЛЕ таблицы значений; разметка повторяет
//      scaleCustomCalcPanel («Шкала-сигнал»); рефакторинг: карта типов
//      ТС в одном месте (getRtdSensorMap); функции живого расчёта;
//      диапазоны НСХ; обращение бисекцией; маркеры Task 371.
//   B. VM — живой двусторонний расчёт: Cu50/Pt100/Pt1000/ТП K, B
//      (прямое значение и обратная задача, включая t<0°C с членом C),
//      границы НСХ, тосты «вне диапазона НСХ» с очисткой поля.
//   C. VM (calcTempSensor) — полный рендер: таблица + панель под ней,
//      подписи полей по веткам, повторный «Рассчитать» перерисовывает.
//   D. SW v600 (guard v601).

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');
const { extractFunctions } = require('./extract-functions.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');

// Извлечение исходника function-декларации по имени (баланс фигурных
// скобок; в телах функций скобки в строках/шаблонах сбалансированы)
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

// «1234,56» (с неразрывными пробелами) → 1234.56
function parseRu(s) {
    return parseFloat(String(s).replace(/\u00A0/g, '').replace(',', '.'));
}

// ============================================================
// A. SRC — разметка и структура
// ============================================================
describe('Task 371 — SRC: блок «Расчёт произвольных значений»', () => {

    test('Панель в ветке ТС: «Сопротивление R(t), Ом», после таблицы', () => {
        const call = "html+=tempCustomCalcHtml('Сопротивление R(t), Ом','Например: 61,8');";
        assertTrue(INDEX_SRC.indexOf(call) !== -1, 'вызов в ветке ТС есть');
        const ci = INDEX_SRC.indexOf(call);
        const rtdBranch = INDEX_SRC.indexOf("if(type==='rtd'){");
        const tcBranch = INDEX_SRC.indexOf('} else {', rtdBranch);
        assertTrue(ci > rtdBranch && ci < tcBranch, 'вызов внутри ветки ТС');
        // после закрытия таблицы и до записи innerHTML
        const tbl = INDEX_SRC.lastIndexOf('html+=`</tbody></table></div>`;', ci);
        const inner = INDEX_SRC.indexOf('resDiv.innerHTML=html;', ci);
        assertTrue(tbl !== -1 && tbl < ci, 'панель после </tbody></table></div>');
        assertTrue(inner !== -1 && ci < inner, 'панель до resDiv.innerHTML=html');
    });

    test('Панель в ветке ТП: «Термо-ЭДС E(t), мВ», после таблицы', () => {
        const call = "html+=tempCustomCalcHtml('Термо-ЭДС E(t), мВ','Например: 2,2');";
        assertTrue(INDEX_SRC.indexOf(call) !== -1, 'вызов в ветке ТП есть');
        const ci = INDEX_SRC.indexOf(call);
        const tbl = INDEX_SRC.lastIndexOf('html+=`</tbody></table></div>`;', ci);
        const inner = INDEX_SRC.indexOf('resDiv.innerHTML=html;', ci);
        assertTrue(tbl !== -1 && tbl < ci, 'панель после </tbody></table></div>');
        assertTrue(inner !== -1 && ci < inner, 'панель до resDiv.innerHTML=html');
    });

    test('tempCustomCalcHtml: разметка повторяет «Шкала-сигнал»', () => {
        const fn = grabFn('tempCustomCalcHtml');
        assertTrue(fn !== null, 'функция объявлена');
        for (const chunk of [
            'id="tempCustomCalcPanel"',
            'Расчёт произвольных значений',
            'Введите значение в любое поле — другое рассчитается автоматически',
            'id="tempQueryTemp"',
            'id="tempQueryVal"',
            'oninput="tempQueryFromTemp()"',
            'oninput="tempQueryFromValue()"',
            'class="scale-form"',
            'Температура (°C)'
        ]) {
            assertTrue(fn.indexOf(chunk) !== -1, 'содержит: ' + chunk);
        }
    });

    test('Рефакторинг: карта типов ТС ровно в одном месте', () => {
        assertEqual(INDEX_SRC.split('cu50_1428:{r0:50,alpha:0.00428').length - 1, 1,
            'литерал карты один (в getRtdSensorMap)');
        const m = grabFn('calcTempSensor');
        assertTrue(m.indexOf('getRtdSensorMap()') !== -1,
            'calcTempSensor использует getRtdSensorMap()');
        assertTrue(m.indexOf('pt1000_1385:{r0:1000') === -1,
            'дубликата карты в calcTempSensor нет');
    });

    test('Функции живого расчёта и диапазоны НСХ объявлены', () => {
        for (const name of ['getRtdSensorMap', 'tempCustomCalcHtml', 'getTempSensorRange',
                            'tempCalcForwardValue', 'tempCalcInvertValue',
                            'tempQueryFromTemp', 'tempQueryFromValue']) {
            assertTrue(grabFn(name) !== null, 'function ' + name + ' объявлена');
        }
    });

    test('Диапазоны НСХ: Cu −50…200, Pt −200…850, ТП по типам', () => {
        const fn = grabFn('getTempSensorRange');
        assertTrue(fn.indexOf('{min:-50,max:200}') !== -1, 'Cu: −50…200');
        assertTrue(fn.indexOf('{min:-200,max:850}') !== -1, 'Pt: −200…850');
        assertTrue(fn.indexOf('K:[-270,1372]') !== -1, 'K: −270…1372');
        assertTrue(fn.indexOf('B:[0,1820]') !== -1, 'B: 0…1820');
        assertTrue(fn.indexOf('T:[-270,400]') !== -1, 'T: −270…400');
        assertTrue(fn.indexOf('R:[-50,1768]') !== -1, 'R: −50…1768');
    });

    test('Инверсия — бисекция по монотонной НСХ', () => {
        const fn = grabFn('tempCalcInvertValue');
        assertTrue(fn.indexOf('for(let i=0;i<80;i++)') !== -1, 'цикл бисекции');
        assertTrue(fn.indexOf('return null;') !== -1, 'null вне диапазона');
    });

    test('Тосты «вне диапазона НСХ» очищают другое поле', () => {
        const ft = grabFn('tempQueryFromTemp');
        assertTrue(ft.indexOf('Температура вне диапазона НСХ') !== -1, 'тост температуры');
        assertTrue(ft.indexOf("vEl.value='';") !== -1, 'очистка поля значения');
        const fv = grabFn('tempQueryFromValue');
        assertTrue(fv.indexOf('Значение вне диапазона НСХ') !== -1, 'тост значения');
        assertTrue(fv.indexOf("tEl.value='';") !== -1, 'очистка поля температуры');
    });

    test('Пустой ввод очищает парное поле (как в «Шкала-сигнал»)', () => {
        assertTrue(grabFn('tempQueryFromTemp').indexOf("if(isNaN(t)){vEl.value='';return;}") !== -1,
            't→значение: NaN очищает');
        assertTrue(grabFn('tempQueryFromValue').indexOf("if(isNaN(v)){tEl.value='';return;}") !== -1,
            'значение→t: NaN очищает');
    });

    test('Маркеры Task 371 в коде', () => {
        assertTrue((INDEX_SRC.match(/\/\/ Task 371/g) || []).length >= 5,
            'комментарии-маркеры Task 371');
    });
});

// ============================================================
// B+C. VM — функциональные проверки
// ============================================================
const fns = extractFunctions();

// Кастомная VM: свой document (элементы по требованию) + захват тостов
function makeTempVm() {
    const els = {};
    const document = {
        getElementById: id => (els[id] || (els[id] = {
            value: '', style: {}, innerHTML: '', textContent: '',
            scrollIntoView: () => {}
        }))
    };
    const toasts = [];
    const ctx = {
        document,
        showToast: m => toasts.push(String(m)),
        parseLocaleNumber: fns.parseLocaleNumber,
        formatNumber: fns.formatNumber,
        calcCuResistance: fns.calcCuResistance,
        calcRtdResistance: fns.calcRtdResistance,
        calcTcVoltage: fns.calcTcVoltage,
        setTimeout: () => 0
    };
    vm.createContext(ctx);
    const code = ['getRtdSensorMap', 'tempCustomCalcHtml', 'getTempSensorRange',
                  'tempCalcForwardValue', 'tempCalcInvertValue',
                  'tempQueryFromTemp', 'tempQueryFromValue', 'calcTempSensor']
        .map(grabFn).join('\n');
    vm.runInContext(code + '\n;globalThis.__api = {' +
        'getRtdSensorMap, tempCustomCalcHtml, getTempSensorRange, ' +
        'tempCalcForwardValue, tempCalcInvertValue, ' +
        'tempQueryFromTemp, tempQueryFromValue, calcTempSensor};', ctx);
    return { els, toasts, api: ctx.__api };
}

function setForm(vm, type, rtd, tc) {
    vm.els['temp_sensor_type'] = { value: type, style: {} };
    vm.els['temp_rtd_type'] = { value: rtd, style: {} };
    vm.els['temp_tc_type'] = { value: tc, style: {} };
    vm.els['tempQueryTemp'] = { value: '', style: {} };
    vm.els['tempQueryVal'] = { value: '', style: {} };
}

describe('Task 371 — VM: живой расчёт ТС (температура ↔ сопротивление)', () => {

    test('Cu50 (α=0,00428): t=55 → R=61,77 Ом; и обратно', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '55';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '61,77', 'R(55) для Cu50');
        vmw.els['tempQueryVal'].value = '61,77';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        assertEqual(vmw.els['tempQueryTemp'].value, '55', 'обратная задача — точный 55');
    });

    test('Cu50: границы НСХ −50…200 → 39,3 / 92,8 Ом', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '-50';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '39,3', 'R(−50)');
        vmw.els['tempQueryTemp'].value = '200';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '92,8', 'R(200)');
    });

    test('Cu50: t=250 вне НСХ → тост + поле очищено', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '250';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '', 'поле значения очищено');
        assertTrue(vmw.toasts.length === 1 &&
            vmw.toasts[0].indexOf('Температура вне диапазона НСХ') !== -1 &&
            vmw.toasts[0].indexOf('-50') !== -1 && vmw.toasts[0].indexOf('200') !== -1,
            'тост с границами: ' + (vmw.toasts[0] || '—'));
    });

    test('Cu50: R=10 Ом ниже НСХ → тост «Значение вне диапазона» + очистка', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryVal'].value = '10';
        vmw.api.tempQueryFromValue();
        assertEqual(vmw.els['tempQueryTemp'].value, '', 'поле температуры очищено');
        assertTrue(vmw.toasts.length === 1 &&
            vmw.toasts[0].indexOf('Значение вне диапазона НСХ') !== -1 &&
            vmw.toasts[0].indexOf('Ом') !== -1,
            'тост с единицей Ом');
    });

    test('Pt100 (IEC): t=55 → 121,32; t=100 → 138,51 (сверка с IEC 60751)', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'pt100_1385', 'K');
        vmw.els['tempQueryTemp'].value = '55';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '121,32', 'R(55) Pt100');
        vmw.els['tempQueryTemp'].value = '100';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '138,51', 'R(100) Pt100');
    });

    test('Pt100: t=−50 (член C) → 80,3063 Ом; обратная задача → −50', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'pt100_1385', 'K');
        vmw.els['tempQueryTemp'].value = '-50';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '80,3063', 'R(−50) с членом C');
        vmw.els['tempQueryVal'].value = '80,3063';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        assertEqual(vmw.els['tempQueryTemp'].value, '-50', 'инверсия ниже 0°C — бисекция');
    });

    test('Pt1000 (IEC): t=100 → 1385,05 Ом (R₀=1000)', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'pt1000_1385', 'K');
        vmw.els['tempQueryTemp'].value = '100';
        vmw.api.tempQueryFromTemp();
        const r = parseRu(vmw.els['tempQueryVal'].value);
        assertTrue(Math.abs(r - 1385.055) < 0.01, 'R(100) Pt1000 ≈ 1385,05, получено ' + r);
    });

    test('Pt100: t=−300 вне НСХ → тост', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'pt100_1385', 'K');
        vmw.els['tempQueryTemp'].value = '-300';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '', 'очищено');
        assertTrue(vmw.toasts.length === 1, 'тост показан');
    });

    test('Пустое поле температуры очищает поле значения', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['tempQueryVal'].value = '61,77';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '', 'NaN → очистка парного поля');
        assertEqual(vmw.toasts.length, 0, 'без тоста');
    });
});

describe('Task 371 — VM: живой расчёт ТП (температура ↔ термо-ЭДС)', () => {

    test('ТХА (K): t=400 → 16,3971 мВ; обратная задача → 400', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '400';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '16,3971', 'E(400) по полиному приложения');
        vmw.els['tempQueryVal'].value = '16,3971';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        const t = parseRu(vmw.els['tempQueryTemp'].value);
        assertTrue(Math.abs(t - 400) < 0.01, 'инверсия ≈ 400, получено ' + t);
    });

    test('ТХА (K): t=−100 → −3,5536 мВ; обратно → −99,999', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '-100';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '-3,5536', 'E(−100), ветка t<0');
        vmw.els['tempQueryVal'].value = '-3,5536';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        const t = parseRu(vmw.els['tempQueryTemp'].value);
        assertTrue(Math.abs(t - (-100)) < 0.01, 'инверсия ≈ −100, получено ' + t);
    });

    test('ТПР (B): t=1000 → 4,8343 мВ; обратно → 1000', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'B');
        vmw.els['tempQueryTemp'].value = '1000';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '4,8343', 'E(1000) тип B');
        vmw.els['tempQueryVal'].value = '4,8343';
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        const t = parseRu(vmw.els['tempQueryTemp'].value);
        assertTrue(Math.abs(t - 1000) < 0.01, 'инверсия ≈ 1000, получено ' + t);
    });

    test('ТМК (T): t=−100 → ≈ −3,378 мВ; обратная задача', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'T');
        vmw.els['tempQueryTemp'].value = '-100';
        vmw.api.tempQueryFromTemp();
        const e = parseRu(vmw.els['tempQueryVal'].value);
        assertTrue(Math.abs(e - (-3.3787)) < 0.002, 'E(−100) тип T ≈ −3,379, получено ' + e);
        vmw.els['tempQueryVal'].value = vmw.els['tempQueryVal'].value;
        vmw.els['tempQueryTemp'].value = '';
        vmw.api.tempQueryFromValue();
        const t = parseRu(vmw.els['tempQueryTemp'].value);
        assertTrue(Math.abs(t - (-100)) < 0.01, 'инверсия ≈ −100, получено ' + t);
    });

    test('K: E=100 мВ выше НСХ (макс 54,8864) → тост с «мВ» + очистка', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'K');
        vmw.els['tempQueryVal'].value = '100';
        vmw.api.tempQueryFromValue();
        assertEqual(vmw.els['tempQueryTemp'].value, '', 'поле температуры очищено');
        assertTrue(vmw.toasts.length === 1 &&
            vmw.toasts[0].indexOf('Значение вне диапазона НСХ') !== -1 &&
            vmw.toasts[0].indexOf('мВ') !== -1,
            'тост с единицей мВ: ' + (vmw.toasts[0] || '—'));
    });

    test('K: t=1373 вне НСХ (макс 1372) → тост', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'K');
        vmw.els['tempQueryTemp'].value = '1373';
        vmw.api.tempQueryFromTemp();
        assertEqual(vmw.els['tempQueryVal'].value, '', 'очищено');
        assertTrue(vmw.toasts.length === 1, 'тост показан');
    });

    test('getTempSensorRange: границы по типам', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu100_1426', 'K');
        assertEqual(JSON.stringify(vmw.api.getTempSensorRange()), '{"min":-50,"max":200}', 'Cu');
        setForm(vmw, 'rtd', 'pt50_1391', 'K');
        assertEqual(JSON.stringify(vmw.api.getTempSensorRange()), '{"min":-200,"max":850}', 'Pt');
        setForm(vmw, 'tc', 'cu50_1428', 'J');
        assertEqual(JSON.stringify(vmw.api.getTempSensorRange()), '{"min":-210,"max":1200}', 'J');
        setForm(vmw, 'tc', 'cu50_1428', 'B');
        assertEqual(JSON.stringify(vmw.api.getTempSensorRange()), '{"min":0,"max":1820}', 'B');
        setForm(vmw, 'tc', 'cu50_1428', 'R');
        assertEqual(JSON.stringify(vmw.api.getTempSensorRange()), '{"min":-50,"max":1768}', 'R');
    });

    test('tempCustomCalcHtml: подписи и примеры подставляются', () => {
        const vmw = makeTempVm();
        const rtd = vmw.api.tempCustomCalcHtml('Сопротивление R(t), Ом', 'Например: 61,8');
        assertTrue(rtd.indexOf('Сопротивление R(t), Ом') !== -1, 'подпись ТС');
        assertTrue(rtd.indexOf('Например: 61,8') !== -1, 'пример ТС');
        const tc = vmw.api.tempCustomCalcHtml('Термо-ЭДС E(t), мВ', 'Например: 2,2');
        assertTrue(tc.indexOf('Термо-ЭДС E(t), мВ') !== -1, 'подпись ТП');
        assertTrue(tc.indexOf('Например: 2,2') !== -1, 'пример ТП');
        assertTrue(tc.indexOf('Например: 55') !== -1, 'пример температуры общий');
    });
});

describe('Task 371 — VM: calcTempSensor рендерит панель под таблицей', () => {

    test('Ветка ТС: таблица → панель «Расчёт произвольных значений»', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'rtd', 'cu50_1428', 'K');
        vmw.els['temp_sensor_min'] = { value: '0', style: {} };
        vmw.els['temp_sensor_max'] = { value: '100', style: {} };
        vmw.els['temp_sensor_step'] = { value: '10', style: {} };
        vmw.api.calcTempSensor();
        const html = vmw.els['tempSensorResults'].innerHTML;
        assertTrue(html.indexOf('tempTableContainer') !== -1, 'таблица есть');
        const iTbl = html.indexOf('id="tempTableContainer"');
        const iPanel = html.indexOf('id="tempCustomCalcPanel"');
        assertTrue(iPanel !== -1, 'панель есть');
        assertTrue(iTbl < iPanel, 'панель ПОД таблицей');
        assertTrue(html.indexOf('Расчёт произвольных значений') !== -1, 'заголовок блока');
        assertTrue(html.indexOf('Сопротивление R(t), Ом') !== -1, 'подпись поля ТС');
        assertTrue(html.indexOf('id="tempQueryTemp"') !== -1 &&
            html.indexOf('id="tempQueryVal"') !== -1, 'поля ввода');
        assertTrue(html.indexOf('R(t), Ом') !== -1 && html.indexOf('E(t), мВ') === -1,
            'ветка ТС — без подписи ТП');
    });

    test('Ветка ТП: подпись «Термо-ЭДС E(t), мВ»', () => {
        const vmw = makeTempVm();
        setForm(vmw, 'tc', 'cu50_1428', 'K');
        vmw.els['temp_sensor_min'] = { value: '0', style: {} };
        vmw.els['temp_sensor_max'] = { value: '100', style: {} };
        vmw.els['temp_sensor_step'] = { value: '10', style: {} };
        vmw.api.calcTempSensor();
        const html = vmw.els['tempSensorResults'].innerHTML;
        assertTrue(html.indexOf('Термо-ЭДС E(t), мВ') !== -1, 'подпись поля ТП');
        assertTrue(html.indexOf('Сопротивление R(t), Ом') === -1, 'без подписи ТС');
        const iTbl = html.indexOf('id="tempTableContainer"');
        const iPanel = html.indexOf('id="tempCustomCalcPanel"');
        assertTrue(iTbl !== -1 && iPanel !== -1 && iTbl < iPanel, 'панель под таблицей');
    });

    test('Панель появляется только после «Рассчитать» (до — пусто)', () => {
        // #tempSensorResults стартует пустым (display:none в разметке),
        // панель генерируется вместе с результатами — как в «Шкала-сигнал»
        const i = INDEX_SRC.indexOf('id="tempSensorResults"');
        const chunk = INDEX_SRC.slice(i, i + 200);
        assertTrue(chunk.indexOf('tempCustomCalcPanel') === -1,
            'в статичной разметке панели нет — только в генерируемой');
    });
});

// ============================================================
// D. SW v600 (guard v601)
// ============================================================
describe('Task 371 — SW: версия кэша kipia-test-v600', () => {

    test('CACHE_VERSION = kipia-test-v600', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v600'") !== -1,
            'SW бампнут до v600');
    });

    test('Guard: v601 ещё не существует', () => {
        assertTrue(SW_SRC.indexOf('kipia-test-v601') === -1,
            'v601 не должен существовать (следующий бамп)');
    });
});
