// scripts/task518-audit.js — Task 518: аудит FP-остатков обратных расчётов
// «Инженерные калькуляторы».
//
// ЗАЯВКА: 50М (Cu50) α = 0,00428 — при вводе 50 Ом в поле сопротивления
// поле температуры показывает −1,2970e−14 вместо 0 °C. Причина:
// tempCalcInvertValue() обращает НСХ бисекцией, а прямая функция f(t)
// квантована шагом округления double (~1e-16 отн.): в полосе |t| ~ 1e-14
// вычисленная f(t) округляется ровно к R₀, и бисекция сходится к краю
// этой полосы, а не к точному нулю. formatNumber() при |n| < 1e-5
// переключается на научную запись — остаток становится видимым.
//
// АУДИТ (все live-калькуляторы с обратным расчётом):
//   1. Датчики температуры: 8 ТС + 9 ТП — инверсия номиналов (R₀ / E(0))
//      и round-trip номинальных точек.
//   2. Шкала-сигнал: queryFromSignalLive / queryFromScaleLive на концах
//      диапазона и нулевом перепаде биполярной шкалы.
//   3. Буйковый уровнемер: номиналы панели (анализ + smoke-проба).
//
// Скрипт двусторонний: до фикса (v731) — 56 находок (все ТС/ТП
// номиналы); после фикса Task 518 — 0. Критерии: 'exact0' — мусор
// любого масштаба у номинала; 'approx' — |остаток| >= 1e-9 или
// научная запись в видимом выводе.

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = path.resolve(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');

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

// VM с мок-DOM; prologue выполняется в том же контексте (там можно
// объявлять var-глобалы и расширять __api сеттерами).
function makeVm(fnNames, prologue) {
    const els = {};
    const document = {
        getElementById: id => (els[id] || (els[id] = {
            value: '', style: {}, innerHTML: '', textContent: '',
            scrollIntoView: () => {}, children: []
        }))
    };
    const ctx = { document, console, showToast: () => {}, setTimeout: () => 0 };
    vm.createContext(ctx);
    vm.runInContext(
        (prologue || '') + '\n' + fnNames.map(grabFn).filter(Boolean).join('\n') +
        '\n;globalThis.__api = {' + fnNames.join(', ') + '};',
        ctx);
    return { els, ctx, api: ctx.__api };
}

// Доступ к мок-элементу с ленивым созданием (как в браузере getElementById)
function el(vm, id) {
    vm.ctx.document.getElementById(id);
    return vm.els[id];
}

const findings = [];
// expect: 'exact0' — номинал должен быть РОВНО 0 (мусор вида 1e-14 —
// находка); 'approx' — round-trip, допуск 1e-9 (видимая часть
// laundered форматом toFixed — флаг только при реальной ошибке);
// число — ожидаемое значение (шкала-сигнал: концы диапазона)
function report(area, probe, raw, fmt, expect) {
    let bad = false;
    if (expect === 'exact0') {
        bad = (typeof raw === 'number' && raw !== 0) ||
              (typeof fmt === 'string' && /e-\d+/.test(fmt));
    } else if (typeof expect === 'number') {
        bad = (typeof raw !== 'number') ||
              Math.abs(raw - expect) >= 1e-9 ||
              (typeof fmt === 'string' && /e-\d+/.test(fmt));
    } else {
        bad = (typeof raw === 'number' && Math.abs(raw) >= 1e-9) ||
              (typeof fmt === 'string' && /e-\d+/.test(fmt) &&
               Math.abs(raw !== null ? raw : 0) < 1e-5);
    }
    findings.push({ area, probe, raw, fmt, bad });
    return bad;
}

console.log('=== TASK 518: АУДИТ FP-ОСТАТКОВ ОБРАТНЫХ РАСЧЁТОВ ===\n');

// ---------------------------------------------------------------
// 1. Датчики температуры (temp-sensor-view)
// ---------------------------------------------------------------
const tempVm = makeVm(
    ['getRtdSensorMap', 'getTcSensorMap', 'getTempSensorCatalog',
     'tempSensorFindByKey', 'getTempSensorRange', 'tempCalcForwardValue',
     'tempCalcInvertValue', 'tempQueryFromTemp', 'tempQueryFromValue',
     'calcCuResistance', 'calcRtdResistance', 'calcTcVoltage',
     'formatNumber', 'parseLocaleNumber'],
    'var tempSensorKey=null;' +
    '\nglobalThis.__setSensor = function(k){ tempSensorKey = k; };'
);
vm.runInContext('globalThis.__api.__setSensor = globalThis.__setSensor;', tempVm.ctx);
const A = tempVm.api;
const setSensor = k => A.__setSensor(k);
const rtdMap = A.getRtdSensorMap();

// --- СЦЕНАРИЙ ПОЛЬЗОВАТЕЛЯ (Cu50, R=50 Ом) ---
A.__setSensor('cu50_1428');
el(tempVm, 'tempQueryVal').value = '50';
el(tempVm, 'tempQueryTemp').value = '';
A.tempQueryFromValue();
console.log('[ЗАЯВКА] Cu50: ввод "50" Ом -> поле температуры: "' +
    el(tempVm, 'tempQueryTemp').value + '"');
console.log('[ЗАЯВКА] Cu50: tempCalcInvertValue(50) = ' +
    A.tempCalcInvertValue(50) + '\n');

// --- ТС: инверсия R0 + round-trip ---
console.log('--- Термосопротивления ---');
for (const k of ['cu50_1428', 'cu50_1426', 'cu100_1428', 'cu100_1426',
                 'pt50_1391', 'pt100_1391', 'pt100_1385', 'pt1000_1385']) {
    A.__setSensor(k);
    const sd = rtdMap[k];
    const tInv = A.tempCalcInvertValue(sd.r0);
    const bad1 = report('ТС ' + k, 'invert(R0=' + sd.r0 + ' Ом) -> ожидался 0',
        tInv, A.formatNumber(tInv), 'exact0');
    const rng = A.getTempSensorRange();
    for (const tt of [100, 50, 25, -50, -100, -180]
            .filter(x => x >= rng.min && x <= rng.max)) {
        const R = A.tempCalcForwardValue(tt);
        const t2 = A.tempCalcInvertValue(R);
        report('ТС ' + k, 'round-trip t=' + tt + ' (R=' + R.toFixed(4) + ') остаток',
            t2 - tt, A.formatNumber(t2), 'approx');
    }
    console.log('  ' + k + ': invert(R0) = ' + tInv + ' -> "' +
        A.formatNumber(tInv) + '"' + (bad1 ? '   <<< НАХОДКА' : ''));
}

// --- ТП: E(0), инверсия 0 мВ, round-trip ---
console.log('\n--- Термопары ---');
for (const k of ['K', 'L', 'J', 'T', 'E', 'N', 'R', 'S', 'B']) {
    A.__setSensor('tc_' + k);
    const rng = A.getTempSensorRange();
    const e0 = A.tempCalcForwardValue(0);
    report('ТП ' + k, 'forward(0): E(0), ожидался 0', e0, A.formatNumber(e0), 'exact0');
    const tInv = A.tempCalcInvertValue(0);
    report('ТП ' + k, 'invert(E=0 мВ) -> ожидался 0', tInv, A.formatNumber(tInv), 'exact0');
    for (const tt of [100, 500, -50].filter(x => x >= rng.min && x <= rng.max)) {
        const E = A.tempCalcForwardValue(tt);
        const t2 = A.tempCalcInvertValue(E);
        report('ТП ' + k, 'round-trip t=' + tt + ' остаток', t2 - tt,
            A.formatNumber(t2), 'approx');
    }
    console.log('  ТП ' + k + ': E(0)=' + e0 + ' ("' + A.formatNumber(e0) +
        '"), invert(0)=' + tInv + ' -> "' + A.formatNumber(tInv) + '"');
}

// ---------------------------------------------------------------
// 2. Шкала-сигнал (scale-signal)
// ---------------------------------------------------------------
console.log('\n--- Шкала-сигнал ---');
const scaleVm = makeVm(
    ['queryFromScaleLive', 'queryFromSignalLive', 'getSignalRangeAndUnit',
     'formatNumber', 'parseLocaleNumber'], '');
const S = scaleVm.api;
function setScaleFields(smin, smax, gmin, gmax, type) {
    const f = id => el(scaleVm, id);
    f('scaleMin').value = String(smin);
    f('scaleMax').value = String(smax);
    f('sigMin').value = String(gmin);
    f('sigMax').value = String(gmax);
    f('scaleType').value = type || 'linear';
    f('scaleUnitName').value = 'ед.';
    f('sigType').value = '4_20';
    f('queryScaleVal').value = '';
    f('querySigVal').value = '';
}
function probeSigToVal(label, smin, smax, gmin, gmax, q, type, expected) {
    setScaleFields(smin, smax, gmin, gmax, type);
    el(scaleVm, 'querySigVal').value = String(q);
    S.queryFromSignalLive();
    const fmt = el(scaleVm, 'queryScaleVal').value;
    const raw = parseFloat(String(fmt).replace(/\u00A0/g, '').replace(',', '.'));
    report('Шкала-сигнал', label + ': сигнал=' + q + ' -> значение', raw, fmt,
        typeof expected === 'number' ? expected : 'approx');
    console.log('  ' + label + ': сигнал ' + q + ' -> "' + fmt + '"');
}
probeSigToVal('0-100 ед / 4-20 мА, линейная', 0, 100, 4, 20, 4, null, 0);
probeSigToVal('0-100 ед / 4-20 мА, линейная', 0, 100, 4, 20, 20, null, 100);
probeSigToVal('биполярная -50..50 / 4-20 мА', -50, 50, 4, 20, 12, null, 0);
probeSigToVal('биполярная -7,3..12,7 / 4-20 мА', -7.3, 12.7, 4, 20, 9.84, null, 0);
probeSigToVal('0-100 ед / 4-20 мА, sqrt', 0, 100, 4, 20, 4, 'sqrt', 0);
probeSigToVal('0-100 ед / 4-20 мА, квадратичная', 0, 100, 4, 20, 20, 'quadratic', 100);
setScaleFields(0, 100, 4, 20, 'linear');
el(scaleVm, 'queryScaleVal').value = '0';
S.queryFromScaleLive();
console.log('  шкала 0 -> сигнал "' + el(scaleVm, 'querySigVal').value + '"');
setScaleFields(-50, 50, 4, 20, 'linear');
el(scaleVm, 'queryScaleVal').value = '0';
S.queryFromScaleLive();
console.log('  биполярная шкала 0 -> сигнал "' + el(scaleVm, 'querySigVal').value + '"');

// ---------------------------------------------------------------
// 3. Буйковый уровнемер (buoy-calc): smoke-проба номиналов
// ---------------------------------------------------------------
console.log('\n--- Буй (панель произвольных значений) ---');
const buoyVm = makeVm(
    ['calcBuoyFromLevel', 'calcBuoyFromMass', 'calcBuoyFromSignal',
     'calcBuoyVolume', 'calcBuoyancyMass', 'calculateBuoySignalValue',
     'getBuoySignalRangeAndUnit', 'formatBuoyNumber', 'parseLocaleNumber',
     'calculateSignalValue', 'getSignalRangeAndUnit'],
    'var lastBuoyParams=null;');
vm.runInContext(
    'lastBuoyParams={d:40,l:300,w:1.2,rho:1000,m_s:0.05,st:"4_20",method:"with_buoy"};' +
    'globalThis.__api.__params = lastBuoyParams;', buoyVm.ctx);
const B = buoyVm.api;
el(buoyVm, 'buoyCustomSignal').value = '4';
B.calcBuoyFromSignal();
console.log('  сигнал 4 мА -> уровень "' + el(buoyVm, 'buoyCustomLevel').value + '"');
report('Буй', 'сигнал 4 мА -> уровень %, ожидался 0',
    parseFloat(el(buoyVm, 'buoyCustomLevel').value.replace(',', '.')),
    el(buoyVm, 'buoyCustomLevel').value, 'exact0');
el(buoyVm, 'buoyCustomLevel').value = '0';
el(buoyVm, 'buoyCustomMass').value = '';
el(buoyVm, 'buoyCustomSignal').value = '';
B.calcBuoyFromLevel();
console.log('  уровень 0 % -> сигнал "' + el(buoyVm, 'buoyCustomSignal').value + '"');

// ---------------------------------------------------------------
// Сводка
// ---------------------------------------------------------------
const bad = findings.filter(f => f.bad);
console.log('\n=== СВОДКА ===');
console.log('Проверок: ' + findings.length + '; находок класса заявки: ' + bad.length);
for (const f of bad) {
    console.log('  [!] ' + f.area + ' :: ' + f.probe + ' -> raw=' + f.raw +
        ' fmt="' + f.fmt + '"');
}
process.exit(bad.length > 0 ? 1 : 0);
