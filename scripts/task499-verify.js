// Task 499: экспресс-проверка значений после применения (kip8test)
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { extractFunctions } = require('../tests/extract-functions.js');
const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const fns = extractFunctions();

function grabFn(name) {
    const start = INDEX_SRC.indexOf('function ' + name + '(');
    if (start === -1) return null;
    const braceStart = INDEX_SRC.indexOf('{', start);
    let depth = 0;
    for (let i = braceStart; i < INDEX_SRC.length; i++) {
        if (INDEX_SRC[i] === '{') depth++;
        else if (INDEX_SRC[i] === '}') { depth--; if (depth === 0) return INDEX_SRC.slice(start, i + 1); }
    }
    return null;
}

console.log('=== calcCuResistance: ГОСТ 5.2.3 (α=0,00428), эталоны А.3 (R₀=100) ===');
[[-180, 20.53], [-170, 25.10], [-120, 47.65], [-100, 56.54], [-50, 78.46], [0, 100.00], [200, 185.60]].forEach(([t, ref]) => {
    const r = fns.calcCuResistance(t, 100, 0.00428);
    console.log('t=' + t + ' → ' + r.toFixed(4) + ' (эталон ' + ref + ') ' + (Math.abs(r - ref) < 0.01 ? 'OK' : 'FAIL'));
});
console.log('=== α=0,00426 — линейная при любой t ===');
console.log('t=-50, R0=50 → ' + fns.calcCuResistance(-50, 50, 0.00426).toFixed(4) + ' (эталон 39.35)');
console.log('=== формат ===');
[[10.264210], [20.52842], [39.2275], [-6.4577], [54.8864], [13.8203], [92.8], [185.6]].forEach(([v]) => console.log(v + ' → «' + fns.formatNumber(v).replace(/-/g, '−') + '»'));

// --- VM: openTempSensor → плейсхолдеры ---
const els = {};
const mkEl = () => ({ value: '', style: {}, innerHTML: '', textContent: '', placeholder: '', scrollIntoView: () => {}, children: [], _attrs: {}, setAttribute(k, v) { this._attrs[k] = String(v); }, getAttribute(k) { return (k in this._attrs) ? this._attrs[k] : null; } });
const document = { getElementById: id => (els[id] || (els[id] = mkEl())), querySelectorAll: () => [] };
const toasts = [], nav = [], store = {};
const vctx = {
    document, localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } },
    showToast: m => toasts.push(String(m)),
    parseLocaleNumber: fns.parseLocaleNumber, formatNumber: fns.formatNumber,
    calcCuResistance: fns.calcCuResistance, calcRtdResistance: fns.calcRtdResistance, calcTcVoltage: fns.calcTcVoltage,
    setTimeout: () => 0, navigator: {}, navigateTo: p => nav.push(p)
};
vm.createContext(vctx);
const code = ['getRtdSensorMap', 'getTcSensorMap', 'getTempSensorCatalog',
              'tempSensorFindByKey', 'renderTempSensorCards', 'setTempSensorsTab',
              'toggleTempSensorFav', 'toggleTempSensorFavFromView',
              'updateTempSensorFavBtn', 'openTempSensor',
              'tempSensorInfoHtml', 'getTempSensorRange',
              'tempCalcForwardValue', 'tempCalcInvertValue',
              'tempQueryFromTemp', 'tempQueryFromValue', 'calcTempSensor']
    .map(grabFn).join('\n');
// TempFav — копия блока из test-task498.js
const tempFavStart = INDEX_SRC.indexOf('var TempFav={');
const tempFavBrace = INDEX_SRC.indexOf('{', tempFavStart);
let tfDepth = 0, tfEnd = -1;
for (let i = tempFavBrace; i < INDEX_SRC.length; i++) {
    if (INDEX_SRC[i] === '{') tfDepth++;
    else if (INDEX_SRC[i] === '}') { tfDepth--; if (tfDepth === 0) { tfEnd = i + 2; break; } }
}
const tempFavSrc = INDEX_SRC.slice(tempFavStart, tfEnd);
vm.runInContext('var tempSensorKey=null; var tempSensorsTab=\'all\';\n' + tempFavSrc + '\n' + code +
    '\n;globalThis.__api = { openTempSensor, getTempSensorRange, tempQueryFromTemp, getTempSensorCatalog };', vctx);
const api = vctx.__api;

console.log('=== плейсхолдеры полей ППР по датчикам ===');
['cu50_1428', 'cu100_1428', 'cu50_1426', 'cu100_1426', 'pt100_1391', 'pt100_1385', 'tc_K', 'tc_L', 'tc_B'].forEach(k => {
    api.openTempSensor(k);
    console.log(k + ': temp=«' + els['tempQueryTemp'].placeholder + '» val=«' + els['tempQueryVal'].placeholder + '»');
});

console.log('=== диапазоны каталога ===');
api.getTempSensorCatalog().forEach(s => { if (s.kind === 'rtd') console.log(s.key + ' ' + s.range.min + '…' + s.range.max); });

console.log('=== живой расчёт tempQueryFromTemp (cu50_1428) ===');
api.openTempSensor('cu50_1428');
els['tempQueryTemp'].value = '-50';
api.tempQueryFromTemp();
console.log('R(−50) = «' + els['tempQueryVal'].value + '» (ожидание 39,2275)');
els['tempQueryTemp'].value = '-180';
api.tempQueryFromTemp();
console.log('R(−180) = «' + els['tempQueryVal'].value + '» (ожидание 10,2642)');
els['tempQueryTemp'].value = '-190';
api.tempQueryFromTemp();
console.log('R(−190) → тост: «' + toasts[toasts.length - 1] + '»');
