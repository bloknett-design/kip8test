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

// Эталонный recentAllMeters для WRONG_METER тестов (Task 200, Фаза 2)
function recentAll(opts) {
    // По умолчанию — массив из 2 других счётчиков с разными расходами
    return [
        { meterId: 2, hoz: 'Хозрасчёт №2', prev: 1000, curr: 1250, consumption: 250, modName: 'a@p', timestamp: new Date().toISOString() },
        { meterId: 4, hoz: 'Хозрасчёт №4', prev: 500, curr: 520, consumption: 20, modName: 'b@p', timestamp: new Date().toISOString() }
    ].concat(opts || []);
}

describe('flowValidateReading — #5 WRONG_METER (Task 200, Фаза 2)', () => {
    test('recentAllMeters = null → WRONG_METER не срабатывает (graceful)', () => {
        var m = meter({ prev: 0, curr: 50.00 });
        var p = { id: 1, prev: 0, curr: 50.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 100 }), null, null);
        assertFalse(hasCode(result.codes, 'WRONG_METER'));
    });

    test('recentAllMeters = [] (пустой массив) → WRONG_METER не срабатывает', () => {
        var m = meter({ prev: 0, curr: 50.00 });
        var p = { id: 1, prev: 0, curr: 50.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 100 }), null, []);
        assertFalse(hasCode(result.codes, 'WRONG_METER'));
    });

    test('Уровень 1 (exact-match): расход совпадает с другим счётчиком → WRONG_METER', () => {
        var m = meter({ id: 1, prev: 0, curr: 250.00 });
        var p = { id: 1, prev: 0, curr: 250.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // meterId=2 имеет consumption=250 в recentAll — точное совпадение
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000 }), null, recentAll());
        assertTrue(hasCode(result.codes, 'WRONG_METER'));
        // detail должен ссылаться на meterId=2
        var wmCode = result.codes.find(function(c) { return c.indexOf('WRONG_METER') === 0; });
        assertTrue(wmCode.indexOf('id=2') !== -1);
        assertTrue(wmCode.indexOf('Хозрасчёт №2') !== -1);
    });

    test('Уровень 1: расход чуть отличается (больше 0.01) → WRONG_METER не срабатывает', () => {
        var m = meter({ id: 1, prev: 0, curr: 250.05 });
        var p = { id: 1, prev: 0, curr: 250.05, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // meterId=2 consumption=250, наш 250.05, разница 0.05 > 0.01
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000 }), null, recentAll());
        assertFalse(hasCode(result.codes, 'WRONG_METER'));
    });

    test('Уровень 3 (swap): пара (prev, curr) совпадает с другим счётчиком → WRONG_METER', () => {
        // meterId=2 в recentAll имеет prev=1000, curr=1250. Вводим их в meterId=1.
        var m = meter({ id: 1, prev: 1000, curr: 1250, modName: 'c@p' });
        var p = { id: 1, prev: 1000, curr: 1250, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // consumption = 250 — совпадает с meterId=2 consumption. Поэтому сработает
        // уровень 1 раньше уровня 3 — оба дают WRONG_METER, это OK.
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000 }), null, recentAll());
        assertTrue(hasCode(result.codes, 'WRONG_METER'));
        var wmCode = result.codes.find(function(c) { return c.indexOf('WRONG_METER') === 0; });
        assertTrue(wmCode.indexOf('id=2') !== -1);
    });

    test('Уровень 3: пара (prev, curr) совпадает, но расход НЕ совпадает — swap', () => {
        // meterId=2 в recentAll: prev=1000, curr=1250, consumption=250.
        // Конструируем так, чтобы пара совпадала, но расход не был = 250.
        // Это возможно только если prev/curr — не числа (например, мы ввели 1000/1250
        // как чужую пару). consumption в этом случае = 250 (1250-1000), что совпадёт
        // с meterId=2 — уровень 1 сработает раньше. Чтобы проверить только swap,
        // надо чтобы consumption у meterId=2 был НЕ 250.
        var m = meter({ id: 1, prev: 1000, curr: 1250, modName: 'c@p' });
        var p = { id: 1, prev: 1000, curr: 1250, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // Подменяем consumption meterId=2 на 999 (чтобы уровень 1 не сработал)
        var customRecent = [
            { meterId: 2, hoz: 'Хозрасчёт №2', prev: 1000, curr: 1250, consumption: 999, modName: 'a@p', timestamp: new Date().toISOString() }
        ];
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000 }), null, customRecent);
        assertTrue(hasCode(result.codes, 'WRONG_METER'));
        var wmCode = result.codes.find(function(c) { return c.indexOf('WRONG_METER') === 0; });
        assertTrue(wmCode.indexOf('пара') !== -1);  // detail про «пара (prev=..., curr=...)»
    });

    test('Свой собственный meterId исключается — совпадение с собой не считается', () => {
        // meterId=1 в recentAll имеет consumption=250, наш расход=250.
        // Но это наш же счётчик — WRONG_METER не должен сработать.
        var m = meter({ id: 1, prev: 0, curr: 250.00 });
        var p = { id: 1, prev: 0, curr: 250.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        var recentWithSelf = recentAll([
            { meterId: 1, hoz: 'Хозрасчёт №1', prev: 0, curr: 250, consumption: 250, modName: 'd@p', timestamp: new Date().toISOString() }
        ]);
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000 }), null, recentWithSelf);
        // meterId=2 всё ещё совпадает (consumption=250), поэтому WRONG_METER сработает на meterId=2
        assertTrue(hasCode(result.codes, 'WRONG_METER'));
        // detail должен ссылаться на meterId=2, НЕ на meterId=1
        var wmCode = result.codes.find(function(c) { return c.indexOf('WRONG_METER') === 0; });
        assertTrue(wmCode.indexOf('id=2') !== -1);
        assertTrue(wmCode.indexOf('id=1') === -1);
    });

    test('consumption < MIN_CONSUMPTION (1.0) → WRONG_METER пропускается', () => {
        var m = meter({ id: 1, prev: 100, curr: 100.5 });  // расход 0.5
        var p = { id: 1, prev: 100, curr: 100.5, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // meterId=4 consumption=20, не совпадает. Но даже если бы совпало (0.5),
        // расход < 1.0 — WRONG_METER пропускается.
        var customRecent = [
            { meterId: 4, hoz: 'Хозрасчёт №4', prev: 100, curr: 100.5, consumption: 0.5, modName: 'b@p', timestamp: new Date().toISOString() }
        ];
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000, min_cons: 0 }), null, customRecent);
        assertFalse(hasCode(result.codes, 'WRONG_METER'));
    });

    test('Несколько счётчиков в recentAll, один совпадает — break, один WRONG_METER код', () => {
        var m = meter({ id: 1, prev: 0, curr: 250.00 });
        var p = { id: 1, prev: 0, curr: 250.00, datePrev: '8/26/2026', dateCurr: '8/27/2026' };
        // meterId=2 совпадает (consumption=250), meterId=4 нет (consumption=20)
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 1000 }), null, recentAll());
        var wmCount = result.codes.filter(function(c) { return c.indexOf('WRONG_METER') === 0; }).length;
        assertEqual(wmCount, 1);
    });

    test('WRONG_METER + другая аномалия — оба в codes', () => {
        var m = meter({ id: 1, prev: 0, curr: 250.00 });
        var p = { id: 1, prev: 0, curr: 250.00, datePrev: '8/20/2026', dateCurr: '8/27/2026' };
        // JUMP_HIGH (250 > 30 = 10×3), PERIOD_MISMATCH (7 дн vs 1), WRONG_METER (consumption=250 = meterId=2)
        var result = fns.flowValidateReading(m, p, rules({ max_cons: 10, expected_days: 1 }), null, recentAll());
        assertTrue(hasCode(result.codes, 'JUMP_HIGH'));
        assertTrue(hasCode(result.codes, 'PERIOD_MISMATCH'));
        assertTrue(hasCode(result.codes, 'WRONG_METER'));
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

// Task 222: проверка, что flowBuildAnomalyModalHtml использует
// дружелюбное описание из FlowmeterData._anomalyHelp, если оно есть.
// Поскольку FlowmeterData объявлен внутри sandbox extract-functions
// и не экспортируется, проверяем source-text инварианты в index.html.
describe('Task 222: flowBuildAnomalyModalHtml — дружелюбные описания (source-text)', () => {
    const fs = require('fs');
    const path = require('path');
    const idxSrc = fs.readFileSync(path.resolve(__dirname, '..', 'index.html'), 'utf-8');

    test('FlowmeterData имеет поле _anomalyHelp (инициализировано как {})', () => {
        assertTrue(idxSrc.indexOf('_anomalyHelp: {}') !== -1);
    });
    test('flowBuildAnomalyModalHtml читает FlowmeterData._anomalyHelp', () => {
        // Ищем паттерн обращения к карте описаний внутри функции
        var idx = idxSrc.indexOf('function flowBuildAnomalyModalHtml');
        assertTrue(idx !== -1);
        var snippet = idxSrc.substring(idx, idx + 1500);
        assertTrue(snippet.indexOf('FlowmeterData._anomalyHelp') !== -1);
        assertTrue(snippet.indexOf('helpMap[code]') !== -1);
        assertTrue(snippet.indexOf('|| detail') !== -1);
    });
    test('_buildArchiveHtml использует _anomalyHelp для столбца «⚠ Замечания»', () => {
        // Ищем паттерн внутри _buildArchiveHtml
        var idx = idxSrc.indexOf('_buildArchiveHtml: function');
        assertTrue(idx !== -1);
        var snippet = idxSrc.substring(idx, idx + 12000);
        assertTrue(snippet.indexOf('this._anomalyHelp') !== -1);
        assertTrue(snippet.indexOf('friendly') !== -1);
        assertTrue(snippet.indexOf('displayText') !== -1);
    });
    test('loadArchive сохраняет anomalyHelp из ответа сервера', () => {
        var idx = idxSrc.indexOf("'flowmeter.archive',");
        assertTrue(idx !== -1);
        var snippet = idxSrc.substring(idx, idx + 800);
        assertTrue(snippet.indexOf('data.anomalyHelp') !== -1);
        assertTrue(snippet.indexOf('self._anomalyHelp') !== -1);
    });
});

// Task 222: проверка, что серверный файл ValidationRules.gs содержит
// нужные структуры (HELP_SHEET_NAME, DEFAULT_HELP, getHelpMap, listHelp,
// flowmeterInitValidationHelp) и что DEFAULT_HELP содержит все 10 кодов.
describe('Task 222: ValidationRules.gs — структуры для help-таблицы', () => {
    const fs = require('fs');
    const path = require('path');
    const vrPath = path.resolve(__dirname, '..', 'scripts', 'ValidationRules.gs');
    const src = fs.readFileSync(vrPath, 'utf-8');

    test('HELP_SHEET_NAME = flowmeter_validation_help', () => {
        assertTrue(src.indexOf("HELP_SHEET_NAME: 'flowmeter_validation_help'") !== -1);
    });
    test('DEFAULT_HELP содержит все 10 кодов', () => {
        var codes = ['SIGN_NEG', 'DATE_INCONSISTENT', 'JUMP_NEGATIVE', 'JUMP_HIGH',
                     'JUMP_LOW', 'PERIOD_MISMATCH', 'TEMP_OUT_OF_RANGE', 'GCAL_RATIO',
                     'DUPLICATE', 'WRONG_METER'];
        for (var i = 0; i < codes.length; i++) {
            assertTrue(src.indexOf(codes[i] + ':') !== -1,
                       'DEFAULT_HELP должен содержать код ' + codes[i]);
        }
    });
    test('Метод getHelpMap определён', () => {
        assertTrue(src.indexOf('getHelpMap: function') !== -1);
    });
    test('Метод listHelp определён (для эндпоинта flowmeter.getValidationHelp)', () => {
        assertTrue(src.indexOf('listHelp: function') !== -1);
    });
    test('Функция flowmeterInitValidationHelp определена', () => {
        assertTrue(src.indexOf('function flowmeterInitValidationHelp') !== -1);
    });
});

// Task 222: проверка, что Code.gs регистрирует новый эндпоинт
// flowmeter.getValidationHelp, а FlowmeterArchive.gs возвращает anomalyHelp.
describe('Task 222: регистрация эндпоинта и anomalyHelp в архиве', () => {
    const fs = require('fs');
    const path = require('path');
    const codeSrc = fs.readFileSync(path.resolve(__dirname, '..', 'scripts', 'Code.gs'), 'utf-8');
    const archSrc = fs.readFileSync(path.resolve(__dirname, '..', 'scripts', 'FlowmeterArchive.gs'), 'utf-8');

    test('Code.gs: case flowmeter.getValidationHelp → ValidationRules.listHelp', () => {
        assertTrue(codeSrc.indexOf("'flowmeter.getValidationHelp'") !== -1);
        assertTrue(codeSrc.indexOf('ValidationRules.listHelp') !== -1);
    });
    test('FlowmeterArchive.gs: listArchive возвращает anomalyHelp', () => {
        assertTrue(archSrc.indexOf('anomalyHelp') !== -1);
        assertTrue(archSrc.indexOf('ValidationRules.getHelpMap') !== -1);
    });
});

// Task 223 + 224: график в архиве расходомера строится из показаний (r.curr),
// а не из вычисленного расхода (r.consumption); высота баров нормализуется
// по диапазону [min..max]: bar = (curr − min) / (max − min) × 100.
// Тесты — source-text на index.html (без мутации sandbox-объектов).
describe('Task 223+224+228: график архива — условный источник + нормализация', () => {
    const fs = require('fs');
    const path = require('path');
    const idxPath = path.resolve(__dirname, '..', 'index.html');
    const src = fs.readFileSync(idxPath, 'utf-8');

    function chartBody() {
        var fnIdx = src.indexOf('_buildArchiveChart: function');
        if (fnIdx === -1) return '';
        var fnEnd = src.indexOf('return html;', fnIdx);
        return src.substring(fnIdx, fnEnd === -1 ? src.length : fnEnd);
    }

    // Task 228: условный выбор источника данных
    test('Определяется dailyMode через _isDailyMode(meter)', () => {
        var body = chartBody();
        assertTrue(body.indexOf('_isDailyMode') !== -1,
                   'Должен вызываться _isDailyMode(meter) для определения источника');
    });

    test('Функция pickValue использует r.curr для dailyMode', () => {
        var body = chartBody();
        assertTrue(body.indexOf('pickValue') !== -1,
                   'Должна быть функция pickValue для выбора источника');
        // Для dailyMode → r.curr
        assertTrue(body.indexOf('r.curr') !== -1,
                   'pickValue должен использовать r.curr для dailyMode');
    });

    test('Функция pickValue использует r.consumption для НЕ-dailyMode (Task 228)', () => {
        var body = chartBody();
        // Для не-dailyMode → r.consumption
        assertTrue(body.indexOf('r.consumption') !== -1,
                   'pickValue должен использовать r.consumption для не-dailyMode (Task 228)');
    });

    test('Заголовок: «Показания» для dailyMode, «Расход» для остальных', () => {
        var body = chartBody();
        // chartTitle = dailyMode ? 'Показания' : 'Расход'
        assertTrue(body.indexOf("'Показания'") !== -1,
                   'Должна быть строка «Показания» для dailyMode');
        assertTrue(body.indexOf("'Расход'") !== -1,
                   'Должна быть строка «Расход» для не-dailyMode');
        // Тернарный оператор
        assertTrue(body.indexOf("chartTitle = dailyMode") !== -1 ||
                   body.indexOf("dailyMode ? 'Показания' : 'Расход'") !== -1,
                   'Должен быть тернарный выбор заголовка по dailyMode');
    });

    // Task 224: нормализация по диапазону
    test('Вычисляется minVal (минимум значений)', () => {
        var body = chartBody();
        assertTrue(body.indexOf('minVal') !== -1,
                   'Должна быть переменная minVal');
        assertTrue(body.indexOf('Infinity') !== -1,
                   'minVal должен инициализироваться Infinity');
    });

    test('Вычисляется maxVal (максимум значений)', () => {
        var body = chartBody();
        assertTrue(body.indexOf('maxVal') !== -1,
                   'Должна быть переменная maxVal');
    });

    test('Формула нормализации: (val − minVal) / range × 100', () => {
        var body = chartBody();
        assertTrue(body.indexOf('(val - minVal)') !== -1,
                   'Должна быть формула (val − minVal)');
        assertTrue(body.indexOf('/ range') !== -1,
                   'Должно быть деление на range (max − min)');
        assertTrue(body.indexOf('* 100') !== -1,
                   'Должно быть умножение на 100');
    });

    test('Защита от деления на ноль (плоский случай max === min)', () => {
        var body = chartBody();
        assertTrue(body.indexOf('range === 0') !== -1 || body.indexOf('flat') !== -1,
                   'Должна быть защита от деления на ноль (range === 0 / flat)');
    });

    test('Минимальная высота бара 5% (Math.max(5, ...)) — Task 226', () => {
        var body = chartBody();
        assertTrue(body.indexOf('Math.max(5') !== -1,
                   'Должен быть Math.max(5, ...) для минимальной высоты 5% (Task 226)');
        assertTrue(body.indexOf('Math.max(1') === -1,
                   'Старый Math.max(1, ...) должен быть убран');
    });

    test('Старый код (curr / maxReading × 100 без min) убран', () => {
        var body = chartBody();
        assertTrue(body.indexOf('(curr / maxReading) * 100') === -1,
                   'Старая формула (curr / maxReading) × 100 должна быть убрана');
    });
});

// Task 231 (историческая заметка): в этой ревизии SW был поднят до v495.
// Актуальная версия — v496 (Task 232, см. ниже). Текущий SW-тест живёт в
// блоке «Task 232: SW версия v496» — он проверяет и наличие v496, и
// отсутствие v495. Отдельный блок Task 231 убран, чтобы не падал при
// следующих bump-ах.

// Task 230: горизонтальный скролл таблицы хронологии работает сразу (без pinch-zoom).
// Причина бага: .pinch-zoom-target имеет touch-action: pan-y (только вертикаль),
// и лишь после добавления класса .zoomed (через pinch-zoom) становится pan-x pan-y.
// Решение: для таблицы хронологии добавлено специфичное правило
// .flow-archive-table-wrap.pinch-zoom-target { touch-action: pan-x pan-y }.
describe('Task 230: горизонтальный скролл таблицы хронологии без pinch-zoom', () => {
    const fs = require('fs');
    const path = require('path');
    const idxPath = path.resolve(__dirname, '..', 'index.html');
    const src = fs.readFileSync(idxPath, 'utf-8');

    test('Добавлено правило .flow-archive-table-wrap.pinch-zoom-target', () => {
        assertTrue(src.indexOf('.flow-archive-table-wrap.pinch-zoom-target') !== -1,
                   'Должно быть CSS-правило .flow-archive-table-wrap.pinch-zoom-target');
    });

    test('touch-action: pan-x pan-y для таблицы хронологии', () => {
        // Находим блок правила
        var ruleIdx = src.indexOf('.flow-archive-table-wrap.pinch-zoom-target');
        assertTrue(ruleIdx !== -1);
        var ruleEnd = src.indexOf('}', ruleIdx);
        var ruleText = src.substring(ruleIdx, ruleEnd === -1 ? src.length : ruleEnd);
        assertTrue(ruleText.indexOf('touch-action: pan-x pan-y') !== -1,
                   'touch-action должен быть pan-x pan-y');
    });

    test('Старое touch-action: pan-y у .pinch-zoom-target сохранено (для других элементов)', () => {
        // Базовое правило .pinch-zoom-target не трогаем — оно нужно для билетов и др.
        // Ищем именно базовое правило (с переносом строки перед, чтобы не поймать
        // .flow-archive-table-wrap.pinch-zoom-target).
        var needle = '\n    .pinch-zoom-target {\n        touch-action: pan-y;';
        assertTrue(src.indexOf(needle) !== -1,
                   'Базовое .pinch-zoom-target должно остаться с touch-action: pan-y');
    });
});

// Task 225: реорганизация строки «Последние показания» в детальной карточке.
// Убраны отдельные строки «Температура среды» и «Гигакалории пара» — их
// значения перенесены под основные показания. Дата «за дата г.» —
// отдельной строкой под названием «Последние показания».
describe('Task 225: реорганизация строки «Последние показания»', () => {
    const fs = require('fs');
    const path = require('path');
    const idxPath = path.resolve(__dirname, '..', 'index.html');
    const src = fs.readFileSync(idxPath, 'utf-8');

    // Находим _buildDetailHtml
    function detailBody() {
        var fnIdx = src.indexOf('_buildDetailHtml: function');
        if (fnIdx === -1) return '';
        // Конец функции — следующая закрывающая } на уровне метода
        var fnEnd = src.indexOf('\n        },', fnIdx);
        return src.substring(fnIdx, fnEnd === -1 ? src.length : fnEnd);
    }

    test('Отдельная строка «Температура среды» убрана', () => {
        var body = detailBody();
        // Не должно быть HTML-строки с label «Температура среды»
        assertTrue(body.indexOf('>Температура среды<') === -1,
                   'Строка «Температура среды» должна быть убрана');
    });

    test('Отдельная строка «Гигакалории пара» убрана', () => {
        var body = detailBody();
        assertTrue(body.indexOf('>Гигакалории пара<') === -1,
                   'Строка «Гигакалории пара» должна быть убрана');
    });

    test('Значение температуры перенесено в flow-detail-sub (под осн. значением)', () => {
        var body = detailBody();
        // tempStr всё ещё формируется в buildDetailHtml
        assertTrue(body.indexOf('m.temp.toFixed(1)') !== -1,
                   'Должно быть вычисление tempStr');
        // И оборачивается в flow-detail-sub
        assertTrue(body.indexOf('flow-detail-value flow-detail-sub') !== -1 ||
                   body.indexOf('flow-detail-sub') !== -1,
                   'Подзначения должны иметь класс flow-detail-sub');
    });

    test('Значение гигакалорий перенесено в flow-detail-sub', () => {
        var body = detailBody();
        // gcalStr формируется ранее (строка ~31793)
        assertTrue(body.indexOf('gcalStr') !== -1,
                   'Должно использоваться gcalStr');
        // И оборачивается в flow-detail-sub
        assertTrue(body.indexOf('flow-detail-sub') !== -1,
                   'Подзначения должны иметь класс flow-detail-sub');
    });

    test('Дата «за дата г.» — под-элемент label, одна строка (Task 227+229)', () => {
        var body = detailBody();
        // Task 227: дата в row-head (не отдельной строкой под названием)
        // Task 229: дата — под-элемент .flow-detail-label (одна общая строка)
        assertTrue(body.indexOf('flow-detail-date-inline') !== -1,
                   'Дата должна иметь класс-маркер flow-detail-date-inline');
        // Проверяем, что lastReadingLabel идёт ВНУТРИ span.flow-detail-label
        // (это единственный span с этим классом в карточке), а date-inline
        // идёт сразу после lastReadingLabel (с тем же родителем — span.label).
        // Находим подстроку «flow-detail-label» — после неё в радиусе 200
        // символов должно быть «flow-detail-date-inline» (т.е. date-элемент
        // является под-элементом label, а не отдельным span в row-head).
        var labelIdx = body.indexOf('flow-detail-label');
        assertTrue(labelIdx !== -1, 'flow-detail-label должен быть в коде');
        var snippet = body.substring(labelIdx, Math.min(body.length, labelIdx + 300));
        assertTrue(snippet.indexOf('flow-detail-date-inline') !== -1,
                   'Дата должна идти внутри span.flow-detail-label (одна общая строка с названием)');
        // Старый формат (<div class="flow-detail-date">за ...</div> как отдельная
        // строка под row-head) должен быть убран
        assertTrue(body.indexOf('<div class="flow-detail-date">за ') === -1,
                   'Старая дата-как-блок должна быть убрана (Task 227)');
    });

    test('Значение показаний не содержит встроенную дату «за ...»', () => {
        var body = detailBody();
        // Старый формат — значение показаний имело встроенную дату через запятую:
        //   ... ' + this._esc(m.unit) + ',<span class="flow-detail-date"> за ' + this._fmtDate(m.dateCurr) + ' г.</span> ...
        // После Task 225 дата перенесена выше (отдельной строкой), а в значении
        // показаний её быть не должно.
        // Проверяем: в подстроке, где формируется flow-detail-curr, нет
        // ",<span class=\"flow-detail-date\"> за ".
        var currIdx = body.indexOf('flow-detail-curr');
        assertTrue(currIdx !== -1, 'flow-detail-curr должен быть в коде');
        // Ищем следующий фрагмент ',<span class="flow-detail-date"> за '
        // в радиусе 200 символов от flow-detail-curr (тело строки значения).
        var snippet = body.substring(currIdx, Math.min(body.length, currIdx + 400));
        assertTrue(snippet.indexOf(',<span class="flow-detail-date"> за ') === -1,
                   'Значение показаний не должно содержать встроенную дату «за ...»');
        // И должно закрываться </div> без продолжения даты
        // (найдём первую закрывающую > после curr)
        assertTrue(snippet.indexOf(' ' + '</div>') !== -1 || snippet.indexOf('</div>') !== -1,
                   'Значение показаний должно закрываться </div>');
    });

    test('Добавлен класс flow-detail-row-last для строки «Последние показания»', () => {
        var body = detailBody();
        assertTrue(body.indexOf('flow-detail-row-last') !== -1,
                   'Должен быть класс-маркер flow-detail-row-last');
    });

    test('CSS-класс .flow-detail-sub определён', () => {
        assertTrue(src.indexOf('.flow-detail-sub') !== -1,
                   'CSS .flow-detail-sub должен быть определён');
    });
});

// Task 231: реорганизация сводной карточки расходомера в списке.
// В каждой карточке хозрасчётного расходомера:
//   1) «Последние показания» и дата «за дата г.» — в одной строке (дата — под-элемент label,
//      как в детальной карточке Task 229);
//   2) лейблы «Гкал» и «T среды» убраны — значения (с собственными единицами °C и Гкал)
//      показаны под основным значением как sub-текст.
describe('Task 231: карточка расходомера — label+дата в одну строку, лейблы Гкал/T среды убраны', () => {
    const fs = require('fs');
    const path = require('path');
    const idxPath = path.resolve(__dirname, '..', 'index.html');
    const src = fs.readFileSync(idxPath, 'utf-8');

    // Извлекаем тело метода renderList (где формируется HTML карточек)
    function renderListBody() {
        var fnIdx = src.indexOf('renderList: function');
        if (fnIdx === -1) return '';
        var fnEnd = src.indexOf('\n        },', fnIdx);
        return src.substring(fnIdx, fnEnd === -1 ? src.length : fnEnd);
    }

    test('Лейбл «T среды» убран из карточки списка', () => {
        var body = renderListBody();
        // Не должно быть HTML-строки с label «T среды» внутри renderList
        assertTrue(body.indexOf('>T среды<') === -1,
                   'Лейбл «T среды» должен быть убран из карточки списка');
    });

    test('Лейбл «Гкал» убран из карточки списка', () => {
        var body = renderListBody();
        assertTrue(body.indexOf('>Гкал<') === -1,
                   'Лейбл «Гкал» должен быть убран из карточки списка');
    });

    test('Дата — под-элемент label «Последние показания» (одна строка)', () => {
        var body = renderListBody();
        // Дата должна иметь класс-маркер flow-summary-date-inline
        assertTrue(body.indexOf('flow-summary-date-inline') !== -1,
                   'Дата должна иметь класс flow-summary-date-inline');
        // Проверяем: в радиусе 300 символов после flow-summary-label должен быть
        // flow-summary-date-inline (т.е. дата — под-элемент label)
        var labelIdx = body.indexOf('flow-summary-label');
        assertTrue(labelIdx !== -1, 'flow-summary-label должен быть в коде');
        var snippet = body.substring(labelIdx, Math.min(body.length, labelIdx + 300));
        assertTrue(snippet.indexOf('flow-summary-date-inline') !== -1,
                   'Дата должна идти внутри span.flow-summary-label (одна строка с названием)');
    });

    test('Старый формат даты через запятую в значении убран', () => {
        var body = renderListBody();
        // Старый формат: ',<span class="flow-detail-date"> за ' + ... + ' г.'
        // не должен встречаться в карточке списка
        assertTrue(body.indexOf(',<span class="flow-detail-date"> за ') === -1,
                   'Старый формат даты через запятую в значении должен быть убран');
    });

    test('Sub-значения temp/gcal показаны под основным значением без лейблов', () => {
        var body = renderListBody();
        // Должен быть класс flow-summary-sub для sub-значений
        assertTrue(body.indexOf('flow-summary-sub') !== -1,
                   'Должен быть класс flow-summary-sub для sub-значений temp/gcal');
        // Значения tempStr/gcalStr всё ещё формируются и используются
        assertTrue(body.indexOf('tempStr') !== -1, 'tempStr должен использоваться');
        assertTrue(body.indexOf('gcalStr') !== -1, 'gcalStr должен использоваться');
        // Проверяем что subParts содержит tempStr/gcalStr (через join)
        assertTrue(body.indexOf('subParts.push(tempStr)') !== -1 ||
                   body.indexOf('subParts.push(') !== -1,
                   'temp/gcal должны добавляться в subParts');
        assertTrue(body.indexOf('.join(') !== -1,
                   'Sub-значения должны объединяться через join');
    });

    test('Старые отдельные summary-items для T среды и Гкал убраны', () => {
        var body = renderListBody();
        // Раньше было: html += '<span class="flow-summary-item"><span class="flow-summary-label">T среды</span>...
        // Теперь этого быть не должно
        assertTrue(body.indexOf('flow-summary-label">T среды') === -1,
                   'Отдельный summary-item с T среды должен быть убран');
        assertTrue(body.indexOf('flow-summary-label">Гкал') === -1,
                   'Отдельный summary-item с Гкал должен быть убран');
    });

    test('CSS-класс .flow-summary-date-inline определён', () => {
        assertTrue(src.indexOf('.flow-summary-label .flow-summary-date-inline') !== -1,
                   'CSS .flow-summary-label .flow-summary-date-inline должен быть определён');
    });

    test('CSS-класс .flow-summary-sub определён', () => {
        assertTrue(src.indexOf('.flow-summary-sub') !== -1,
                   'CSS .flow-summary-sub должен быть определён');
    });
});

// Task 232: внесённый комментарий сразу отображается в архивных записях.
// Архитектура:
//   • setComment пишет в meters.O (активный комментарий счётчика)
//   • archive.P заполняется только при смене автора показаний в updateReading
//   • для той же автора archive.P пустой → самая свежая запись в архиве
//     показывает r.comment = '' хотя комментарий есть в meters.O
// Решение: в _buildArchiveHtml для i===0 (новейшая запись) если r.comment пуст,
// берём m.comment (через flowCommentText — с поддержкой локального fallback).
// Доп.: в submitComment success добавлен немедленный рендер архива из кэша,
// чтобы комментарий отобразился без ожидания network round-trip в loadArchive.
describe('Task 232: комментарий сразу отображается в архивных записях', () => {
    const fs = require('fs');
    const path = require('path');
    const idxPath = path.resolve(__dirname, '..', 'index.html');
    const src = fs.readFileSync(idxPath, 'utf-8');

    // Извлекаем тело метода _buildArchiveHtml
    function archiveBody() {
        var fnIdx = src.indexOf('_buildArchiveHtml: function');
        if (fnIdx === -1) return '';
        var fnEnd = src.indexOf('\n        },', fnIdx);
        return src.substring(fnIdx, fnEnd === -1 ? src.length : fnEnd);
    }

    // Извлекаем тело submitComment
    function submitBody() {
        var fnIdx = src.indexOf('submitComment: function');
        if (fnIdx === -1) return '';
        var fnEnd = src.indexOf('\n        },', fnIdx);
        return src.substring(fnIdx, fnEnd === -1 ? src.length : fnEnd);
    }

    test('В _buildArchiveHtml есть проверка i === 0 + flowCommentText fallback', () => {
        var body = archiveBody();
        // Проверка i === 0 в контексте comment cell
        assertTrue(body.indexOf('i === 0') !== -1,
                   'Должна быть проверка i === 0 для новейшей записи');
        // Вызов flowCommentText(meter, ...) для получения активного комментария
        assertTrue(body.indexOf('flowCommentText(meter') !== -1,
                   'Должен быть вызов flowCommentText(meter, ...) для fallback');
    });

    test('Старая логика «r.comment → cmtStr или —» сохранена для старых записей', () => {
        var body = archiveBody();
        // Должна остаться проверка r.comment из archive.P (для старых записей)
        assertTrue(body.indexOf('r.comment') !== -1,
                   'r.comment должен использоваться (для старых записей)');
        // И должна быть явная защита: если !cmtStr, брать liveCmt
        assertTrue(body.indexOf('if (!cmtStr && i === 0') !== -1 ||
                   body.indexOf('!cmtStr && i === 0') !== -1,
                   'Должна быть защита: для i===0 при пустом r.comment брать активный');
    });

    test('Если у записи есть archive.P (r.comment) — он приоритетнее активного', () => {
        var body = archiveBody();
        // Порядок: сначала r.comment, потом fallback. Проверяем что r.comment первый
        var idxRcomment = body.indexOf('var cmtStr = (r.comment');
        assertTrue(idxRcomment !== -1,
                   'Должна быть инициализация cmtStr из r.comment');
        var idxFallback = body.indexOf('if (!cmtStr && i === 0');
        assertTrue(idxFallback !== -1, 'Должен быть fallback для i===0');
        assertTrue(idxFallback > idxRcomment,
                   'Fallback должен идти ПОСЛЕ инициализации из r.comment');
    });

    test('submitComment вызывает немедленный рендер архива из кэша', () => {
        var body = submitBody();
        // В success-handler должен быть вызов _restoreArchiveCache + _buildArchiveHtml
        assertTrue(body.indexOf('_restoreArchiveCache') !== -1,
                   'submitComment должен вызывать _restoreArchiveCache для кэш-рендера');
        assertTrue(body.indexOf('flowArchiveContainer') !== -1,
                   'submitComment должен обращаться к #flowArchiveContainer');
        assertTrue(body.indexOf('_buildArchiveHtml') !== -1,
                   'submitComment должен вызвать _buildArchiveHtml с кэшем');
    });

    test('Кэш-рендер обёрнут в try/catch (не ломает основной flow)', () => {
        var body = submitBody();
        // Поиск try { ... } catch ... вокруг _restoreArchiveCache
        var idx = body.indexOf('_restoreArchiveCache');
        assertTrue(idx !== -1);
        // Должен быть try перед этим вызовом (в радиусе 200 символов)
        var before = body.substring(Math.max(0, idx - 200), idx);
        assertTrue(before.indexOf('try') !== -1,
                   'Кэш-рендер должен быть в try-блоке (не ломает основной flow)');
    });

    test('Локальный fallback-путь в submitComment тоже имеет кэш-рендер', () => {
        var body = submitBody();
        // Должен быть второй блок _restoreArchiveCache в fallback-ветке (Unknown action)
        var firstIdx = body.indexOf('_restoreArchiveCache');
        var secondIdx = body.indexOf('_restoreArchiveCache', firstIdx + 1);
        assertTrue(secondIdx !== -1,
                   'Должно быть два вызова _restoreArchiveCache: основной + fallback');
    });
});

// Task 232: SW обновлён до v496
describe('Task 232: SW версия v496', () => {
    const fs = require('fs');
    const path = require('path');
    const swPath = path.resolve(__dirname, '..', 'sw.js');
    const sw = fs.readFileSync(swPath, 'utf-8');

    test('CACHE_VERSION = kipia-test-v496', () => {
        assertTrue(sw.indexOf("kipia-test-v496") !== -1);
    });
    test('Старая версия v495 убрана', () => {
        assertTrue(sw.indexOf("kipia-test-v495") === -1,
                   'Старая v495 не должна остаться в sw.js');
    });
});




