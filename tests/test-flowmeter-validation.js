// Тесты валидации показаний расходомера (Task 199).
//
// Проверяемые функции: flowValidateReading, _flowParseDate, _flowFmt,
// flowBuildAnomalyModalHtml. Это клиентское UX-зеркало серверной
// ValidationRules.compute.
//
// Покрытие правил (по решению пользователя — 9 правил Фазы 1, без #5 WRONG_METER):
//   • #12 SIGN_NEG        — hard-block (отрицательные значения prev/curr)
//   • #6  DATE_INCONSISTENT — hard-block (dateCurr < datePrev)
//   • #4→JUMP_NEGATIVE    — merged с #10 для не-конденсатных (consumption < 0)
//   • #3/#10 JUMP_HIGH     — consumption > max_cons × 3
//   • #10  JUMP_LOW        — 0 ≤ consumption < min_cons / 10
//   • #7   PERIOD_MISMATCH — daysBetween != expected_days (±tolerance)
//   • #8   TEMP_OUT_OF_RANGE — temp вне [temp_min, temp_max]
//   • #9   GCAL_RATIO     — для расходомеров пара: gcal/consumption вне [min, max]
//   • #11  DUPLICATE      — те же показания, что в последнем архиве,
//                            тем же автором, в течение 5 минут
//
// Стратегия: S1 (soft-confirm на клиенте + модалка) + запись в archive.Q
// (сервер делает независимо, клиент только для UX).

const { test, describe, assertEqual, assertTrue, assertFalse, assertDeepEqual } = require('./test-helpers.js');
const { extractFunctions } = require('./extract-functions.js');
const fns = extractFunctions();

// Эталонный расходомер (как в test-flowmeter-comment.js, плюс allowNegative)
function meter(opts) {
    return Object.assign({
        id: 1,
        hoz: 'Хозрасчёт №1',
        param: 'Расход пара в корпус 114',
        prev: 90.11, curr: 91.11, unit: 'т',
        datePrev: '8/20/2026', dateCurr: '8/20/2026',
        temp: null, gcal: 60.46, period: 'Ежедневно',
        modRole: 'Админ',
        modName: 'duty@plant.local',
        modDisplayName: 'duty@plant.local',
        modTimestamp: '2026-08-20T08:00:00.000Z',
        comment: '',
        allowNegative: ''  // Task 199: 'yes' для конденсатных, '' для остальных
    }, opts || {});
}

// Эталонные правила (как в flowmeter_validation_rules)
function rules(opts) {
    return Object.assign({
        meterId: 1,
        min_cons: 0.5,
        max_cons: 10.0,
        expected_days: 1,
        gcal_ratio_min: 0.40,
        gcal_ratio_max: 0.80,
        temp_min: 100,
        temp_max: 350
    }, opts || {});
}

// Эталонная последняя запись архива
function lastArchive(opts) {
    return Object.assign({
        prev: 90.11,
        curr: 91.11,
        modName: 'duty@plant.local',
        timestamp: new Date(Date.now() - 60000).toISOString()  // 1 минуту назад
    }, opts || {});
}

// Проверить, что в codes есть код (без детализации)
function hasCode(codes, code) {
    return codes.some(function(c) { return c.indexOf(code + ':') === 0 || c === code; });
}

describe('flowValidateReading — нет аномалий (счастливый путь)', () => {
    test('Нормальные показания, расход в норме — codes пустой', () => {
        var m = meter({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local' });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: 200, gcal: 2.4 };
        // lastArchive с разными значениями prev/curr — иначе DUPLICATE сработает
        var result = fns.flowValidateReading(m, p, rules(), lastArchive({ prev: 50.00, curr: 91.11 }));
        assertEqual(result.codes.length, 0);
        assertTrue(!result.hardBlock);
    });
    test('rules = null — пропускаются soft-confirm проверки, только hard-block', () => {
        var m = meter({ prev: 91.11, curr: 95.00, modName: 'x' });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: 1500, gcal: 9999 };
        var result = fns.flowValidateReading(m, p, null, null);
        assertEqual(result.codes.length, 0);
        assertTrue(!result.hardBlock);
    });
});

describe('flowValidateReading — HARD-BLOCK #12 SIGN_NEG', () => {
    test('curr < 0 — hard-block SIGN_NEG', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: -91.11, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertEqual(result.hardBlock.code, 'SIGN_NEG');
        assertTrue(hasCode(result.codes, 'SIGN_NEG'));
    });
    test('prev < 0 — hard-block SIGN_NEG', () => {
        var m = meter();
        var p = { id: 1, prev: -95.50, curr: 91.11, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertEqual(result.hardBlock.code, 'SIGN_NEG');
    });
    test('SIGN_NEG блокирует до проверки дат — codes не содержит DATE_INCONSISTENT', () => {
        var m = meter();
        var p = { id: 1, prev: -95.50, curr: -91.11, datePrev: '8/27/2026', dateCurr: '8/26/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertEqual(result.hardBlock.code, 'SIGN_NEG');
        assertFalse(hasCode(result.codes, 'DATE_INCONSISTENT'));
    });
});

describe('flowValidateReading — HARD-BLOCK #6 DATE_INCONSISTENT', () => {
    test('dateCurr < datePrev — hard-block', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/27/2026', dateCurr: '8/26/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertEqual(result.hardBlock.code, 'DATE_INCONSISTENT');
        assertTrue(hasCode(result.codes, 'DATE_INCONSISTENT'));
    });
    test('dateCurr === datePrev — НЕ hard-block (один день, валидно для «Ежедневно»)', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/26/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertTrue(!result.hardBlock);
    });
});

describe('flowValidateReading — #4→JUMP_NEGATIVE (merged)', () => {
    test('consumption < 0, allowNegative!=="yes" — JUMP_NEGATIVE', () => {
        var m = meter({ allowNegative: '', prev: 95.00, curr: 91.11 });
        var p = { id: 1, prev: 95.00, curr: 91.11, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertTrue(hasCode(result.codes, 'JUMP_NEGATIVE'));
        assertTrue(!result.hardBlock);
    });
    test('consumption < 0, allowNegative==="yes" — НЕ JUMP_NEGATIVE (конденсат)', () => {
        var m = meter({ allowNegative: 'yes', prev: 95.00, curr: 91.11 });
        var p = { id: 1, prev: 95.00, curr: 91.11, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertFalse(hasCode(result.codes, 'JUMP_NEGATIVE'));
    });
    test('consumption = 0 (не отрицательный) — НЕ JUMP_NEGATIVE', () => {
        var m = meter({ allowNegative: '', prev: 91.11, curr: 91.11 });
        var p = { id: 1, prev: 91.11, curr: 91.11, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertFalse(hasCode(result.codes, 'JUMP_NEGATIVE'));
    });
});

describe('flowValidateReading — #3/#10 JUMP_HIGH (×3 от max_cons)', () => {
    test('consumption = max × 4 — JUMP_HIGH', () => {
        var m = meter({ prev: 0, curr: 40.00 });  // max=10, ×4=40
        var p = { id: 1, prev: 0, curr: 40.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 10 }), null);
        assertTrue(hasCode(result.codes, 'JUMP_HIGH'));
    });
    test('consumption = max × 3 (порог) — НЕ JUMP_HIGH (строго больше)', () => {
        var m = meter({ prev: 0, curr: 30.00 });
        var p = { id: 1, prev: 0, curr: 30.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 10 }), null);
        assertFalse(hasCode(result.codes, 'JUMP_HIGH'));
    });
    test('consumption = max × 10 (EXTRA_DIGIT случай) — JUMP_HIGH с большим фактором', () => {
        var m = meter({ prev: 0, curr: 100.00 });
        var p = { id: 1, prev: 0, curr: 100.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 10 }), null);
        assertTrue(hasCode(result.codes, 'JUMP_HIGH'));
        assertTrue(result.codes[0].indexOf('10.00') !== -1 || result.codes[0].indexOf('100.00') !== -1);
    });
    test('max_cons = null — JUMP_HIGH не срабатывает', () => {
        var m = meter({ prev: 0, curr: 1000.00 });
        var p = { id: 1, prev: 0, curr: 1000.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: null }), null);
        assertFalse(hasCode(result.codes, 'JUMP_HIGH'));
    });
});

describe('flowValidateReading — #10 JUMP_LOW (0 ≤ cons < min/10)', () => {
    test('consumption = 0.04 (min=0.5 → min/10=0.05) — JUMP_LOW', () => {
        var m = meter({ prev: 90.00, curr: 90.04 });
        var p = { id: 1, prev: 90.00, curr: 90.04, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ min_cons: 0.5 }), null);
        assertTrue(hasCode(result.codes, 'JUMP_LOW'));
    });
    test('consumption = 0.06 (выше порога min/10=0.05) — НЕ JUMP_LOW', () => {
        var m = meter({ prev: 90.00, curr: 90.06 });
        var p = { id: 1, prev: 90.00, curr: 90.06, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ min_cons: 0.5 }), null);
        assertFalse(hasCode(result.codes, 'JUMP_LOW'));
    });
    test('consumption < 0 (отрицательный) — НЕ JUMP_LOW (только JUMP_NEGATIVE)', () => {
        var m = meter({ allowNegative: '', prev: 95.00, curr: 90.00 });
        var p = { id: 1, prev: 95.00, curr: 90.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ min_cons: 0.5 }), null);
        assertFalse(hasCode(result.codes, 'JUMP_LOW'));
    });
});

describe('flowValidateReading — #7 PERIOD_MISMATCH', () => {
    test('expected_days=1, фактических 5 — PERIOD_MISMATCH', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/22/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ expected_days: 1 }), null);
        assertTrue(hasCode(result.codes, 'PERIOD_MISMATCH'));
    });
    test('expected_days=1, фактических 1 — НЕ PERIOD_MISMATCH', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ expected_days: 1 }), null);
        assertFalse(hasCode(result.codes, 'PERIOD_MISMATCH'));
    });
    test('expected_days=1, фактических 2 — НЕ PERIOD_MISMATCH (допуск ±1)', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/25/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ expected_days: 1 }), null);
        assertFalse(hasCode(result.codes, 'PERIOD_MISMATCH'));
    });
    test('expected_days=30 (месячный), фактических 35 — ПЕРИОД_MISMATCH', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '7/23/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ expected_days: 30 }), null);
        assertTrue(hasCode(result.codes, 'PERIOD_MISMATCH'));
    });
});

describe('flowValidateReading — #8 TEMP_OUT_OF_RANGE', () => {
    test('temp=400 (>350) — TEMP_OUT_OF_RANGE', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: 400 };
        var result = fns.flowValidateReading(m, p, rules({ temp_min: 100, temp_max: 350 }), null);
        assertTrue(hasCode(result.codes, 'TEMP_OUT_OF_RANGE'));
    });
    test('temp=50 (<100) — TEMP_OUT_OF_RANGE', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: 50 };
        var result = fns.flowValidateReading(m, p, rules({ temp_min: 100, temp_max: 350 }), null);
        assertTrue(hasCode(result.codes, 'TEMP_OUT_OF_RANGE'));
    });
    test('temp=200 (в диапазоне) — НЕ TEMP_OUT_OF_RANGE', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: 200 };
        var result = fns.flowValidateReading(m, p, rules({ temp_min: 100, temp_max: 350 }), null);
        assertFalse(hasCode(result.codes, 'TEMP_OUT_OF_RANGE'));
    });
    test('temp=null — пропускается проверка', () => {
        var m = meter();
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: null };
        var result = fns.flowValidateReading(m, p, rules({ temp_min: 100, temp_max: 350 }), null);
        assertFalse(hasCode(result.codes, 'TEMP_OUT_OF_RANGE'));
    });
});

describe('flowValidateReading — #9 GCAL_RATIO', () => {
    test('gcal/consumption=0.95 (>0.80) — GCAL_RATIO', () => {
        var m = meter({ prev: 0, curr: 100.00 });
        var p = { id: 1, prev: 0, curr: 100.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', gcal: 95.0 };
        var result = fns.flowValidateReading(m, p, rules({ gcal_ratio_min: 0.40, gcal_ratio_max: 0.80 }), null);
        assertTrue(hasCode(result.codes, 'GCAL_RATIO'));
    });
    test('gcal/consumption=0.30 (<0.40) — GCAL_RATIO', () => {
        var m = meter({ prev: 0, curr: 100.00 });
        var p = { id: 1, prev: 0, curr: 100.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', gcal: 30.0 };
        var result = fns.flowValidateReading(m, p, rules({ gcal_ratio_min: 0.40, gcal_ratio_max: 0.80 }), null);
        assertTrue(hasCode(result.codes, 'GCAL_RATIO'));
    });
    test('gcal/consumption=0.60 (в диапазоне) — НЕ GCAL_RATIO', () => {
        var m = meter({ prev: 0, curr: 100.00 });
        var p = { id: 1, prev: 0, curr: 100.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', gcal: 60.0 };
        var result = fns.flowValidateReading(m, p, rules({ gcal_ratio_min: 0.40, gcal_ratio_max: 0.80 }), null);
        assertFalse(hasCode(result.codes, 'GCAL_RATIO'));
    });
    test('consumption=0 (деление на 0) — НЕ GCAL_RATIO', () => {
        var m = meter({ prev: 91.11, curr: 91.11 });
        var p = { id: 1, prev: 91.11, curr: 91.11, datePrev: '8/26/2026', dateCurr: '8/27/2026', gcal: 60.0 };
        var result = fns.flowValidateReading(m, p, rules({ gcal_ratio_min: 0.40, gcal_ratio_max: 0.80 }), null);
        assertFalse(hasCode(result.codes, 'GCAL_RATIO'));
    });
    test('gcal=null — НЕ GCAL_RATIO', () => {
        var m = meter({ prev: 0, curr: 100.00 });
        var p = { id: 1, prev: 0, curr: 100.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', gcal: null };
        var result = fns.flowValidateReading(m, p, rules({ gcal_ratio_min: 0.40, gcal_ratio_max: 0.80 }), null);
        assertFalse(hasCode(result.codes, 'GCAL_RATIO'));
    });
});

describe('flowValidateReading — #11 DUPLICATE', () => {
    test('Те же prev/curr, тот же автор, < 5 минут — DUPLICATE', () => {
        var m = meter({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local' });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var la = lastArchive({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local', timestamp: new Date(Date.now() - 60000).toISOString() });
        var result = fns.flowValidateReading(m, p, rules(), la);
        assertTrue(hasCode(result.codes, 'DUPLICATE'));
    });
    test('Те же prev/curr, но другой автор — НЕ DUPLICATE', () => {
        var m = meter({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local' });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var la = lastArchive({ prev: 91.11, curr: 95.00, modName: 'admin@plant.local', timestamp: new Date(Date.now() - 60000).toISOString() });
        var result = fns.flowValidateReading(m, p, rules(), la);
        assertFalse(hasCode(result.codes, 'DUPLICATE'));
    });
    test('Те же prev/curr, тот же автор, > 5 минут — НЕ DUPLICATE', () => {
        var m = meter({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local' });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var la = lastArchive({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local', timestamp: new Date(Date.now() - 600000).toISOString() });  // 10 минут
        var result = fns.flowValidateReading(m, p, rules(), la);
        assertFalse(hasCode(result.codes, 'DUPLICATE'));
    });
    test('Разные prev/curr — НЕ DUPLICATE', () => {
        var m = meter({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local' });
        var p = { id: 1, prev: 91.11, curr: 95.50, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var la = lastArchive({ prev: 91.11, curr: 95.00, modName: 'duty@plant.local', timestamp: new Date(Date.now() - 60000).toISOString() });
        var result = fns.flowValidateReading(m, p, rules(), la);
        assertFalse(hasCode(result.codes, 'DUPLICATE'));
    });
    test('lastArchive=null — НЕ DUPLICATE', () => {
        var m = meter({ prev: 91.11, curr: 95.00 });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules(), null);
        assertFalse(hasCode(result.codes, 'DUPLICATE'));
    });
});

describe('flowValidateReading — несколько правил сразу', () => {
    test('JUMP_HIGH + PERIOD_MISMATCH вместе — оба в codes', () => {
        var m = meter({ prev: 0, curr: 50.00 });
        var p = { id: 1, prev: 0, curr: 50.00, datePrev: '8/20/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 10, expected_days: 1 }), null);
        assertTrue(hasCode(result.codes, 'JUMP_HIGH'));
        assertTrue(hasCode(result.codes, 'PERIOD_MISMATCH'));
    });
    test('TEMP_OUT_OF_RANGE + GCAL_RATIO вместе — оба в codes', () => {
        var m = meter({ prev: 0, curr: 100.00 });
        var p = { id: 1, prev: 0, curr: 100.00, datePrev: '8/26/2026', dateCurr: '8/27/2026', temp: 500, gcal: 95.0 };
        var result = fns.flowValidateReading(m, p, rules({ temp_min: 100, temp_max: 350, gcal_ratio_min: 0.40, gcal_ratio_max: 0.80 }), null);
        assertTrue(hasCode(result.codes, 'TEMP_OUT_OF_RANGE'));
        assertTrue(hasCode(result.codes, 'GCAL_RATIO'));
    });
});

describe('flowValidateReading — detail-строка (формат «CODE: detail; ...»)', () => {
    test('codes.length > 0 → detail = join «; »', () => {
        var m = meter({ prev: 0, curr: 50.00 });
        var p = { id: 1, prev: 0, curr: 50.00, datePrev: '8/20/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 10, expected_days: 1 }), null);
        assertTrue(result.detail.indexOf(';') !== -1 || result.codes.length === 1);
        assertTrue(result.detail.indexOf('JUMP_HIGH') !== -1);
    });
    test('codes.length === 0 → detail = пустая строка', () => {
        var m = meter({ prev: 91.11, curr: 95.00 });
        var p = { id: 1, prev: 91.11, curr: 95.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // lastArchive с другими prev/curr — иначе DUPLICATE
        var result = fns.flowValidateReading(m, p, rules(), lastArchive({ prev: 50.00, curr: 91.11 }));
        assertEqual(result.detail, '');
    });
});

describe('_flowParseDate — парсинг дат разных форматов', () => {
    test('M/D/YYYY → Date', () => {
        var d = fns._flowParseDate('8/27/2026');
        assertTrue(d instanceof Date);
        assertEqual(d.getFullYear(), 2026);
        assertEqual(d.getMonth(), 7);  // август = 7 (0-indexed)
        assertEqual(d.getDate(), 27);
    });
    test('YYYY-MM-DD → Date', () => {
        var d = fns._flowParseDate('2026-08-27');
        assertTrue(d instanceof Date);
        assertEqual(d.getFullYear(), 2026);
        assertEqual(d.getMonth(), 7);
        assertEqual(d.getDate(), 27);
    });
    test('DD.MM.YYYY → Date', () => {
        var d = fns._flowParseDate('27.08.2026');
        assertTrue(d instanceof Date);
        assertEqual(d.getFullYear(), 2026);
        assertEqual(d.getMonth(), 7);
        assertEqual(d.getDate(), 27);
    });
    test('Пустая строка → null', () => {
        var d = fns._flowParseDate('');
        assertEqual(d, null);
    });
    test('Невалидный формат → null', () => {
        var d = fns._flowParseDate('hello');
        assertEqual(d, null);
    });
});

describe('_flowFmt — форматирование чисел', () => {
    test('Число 3.14159 → "3.14"', () => {
        assertEqual(fns._flowFmt(3.14159), '3.14');
    });
    test('Число 0 → "0.00"', () => {
        assertEqual(fns._flowFmt(0), '0.00');
    });
    test('NaN → "NaN"', () => {
        assertEqual(fns._flowFmt(NaN), 'NaN');
    });
    test('Не число (строка) → исходная строка', () => {
        assertEqual(fns._flowFmt('hello'), 'hello');
    });
});

describe('flowBuildAnomalyModalHtml — построение модалки', () => {
    test('Пустой массив codes → нет <li>, но модалка рендерится', () => {
        var html = fns.flowBuildAnomalyModalHtml(meter(), []);
        assertTrue(html.indexOf('flow-anomaly-modal') !== -1);
        assertTrue(html.indexOf('flow-anomaly-item') === -1);
    });
    test('Один код с деталью → <li> с кодом и деталью', () => {
        var html = fns.flowBuildAnomalyModalHtml(meter(), ['JUMP_HIGH: расход 50.00 > max×3=30.00']);
        assertTrue(html.indexOf('flow-anomaly-item') !== -1);
        assertTrue(html.indexOf('JUMP_HIGH') !== -1);
        assertTrue(html.indexOf('расход 50.00') !== -1);
    });
    test('Код без двоеточия — весь текст как код, detail пустой', () => {
        var html = fns.flowBuildAnomalyModalHtml(meter(), ['SIGN_NEG']);
        assertTrue(html.indexOf('flow-anomaly-item') !== -1);
        assertTrue(html.indexOf('SIGN_NEG') !== -1);
    });
    test('Несколько кодов — несколько <li>', () => {
        var codes = ['JUMP_HIGH: расход 50', 'PERIOD_MISMATCH: 5 дн'];
        var html = fns.flowBuildAnomalyModalHtml(meter(), codes);
        var liCount = (html.match(/flow-anomaly-item/g) || []).length;
        assertEqual(liCount, 2);
    });
    test('HTML-символы в detail экранируются (XSS)', () => {
        var html = fns.flowBuildAnomalyModalHtml(meter(), ['JUMP_HIGH: <script>alert(1)</script>']);
        assertTrue(html.indexOf('<script>') === -1);
        assertTrue(html.indexOf('&lt;script&gt;') !== -1);
    });
    test('Meter с hoz и param — попадают в шапку модалки', () => {
        var m = meter({ hoz: 'Хозрасчёт №1', param: 'Расход пара в корпус 114' });
        var html = fns.flowBuildAnomalyModalHtml(m, ['JUMP_HIGH: test']);
        assertTrue(html.indexOf('Хозрасчёт №1') !== -1);
        assertTrue(html.indexOf('Расход пара в корпус 114') !== -1);
    });
    test('Meter null — шапка модалки пустая (не падает)', () => {
        var html = fns.flowBuildAnomalyModalHtml(null, ['JUMP_HIGH: test']);
        assertTrue(html.indexOf('flow-anomaly-modal-meter') !== -1);
    });
    test('Кнопки «Отменить» и «Сохранить с пометкой» присутствуют', () => {
        var html = fns.flowBuildAnomalyModalHtml(meter(), ['JUMP_HIGH: test']);
        assertTrue(html.indexOf('Отменить') !== -1);
        assertTrue(html.indexOf('Сохранить с пометкой') !== -1);
        assertTrue(html.indexOf('flow-anomaly-cancel') !== -1);
        assertTrue(html.indexOf('flow-anomaly-confirm') !== -1);
    });
});
