// ============================================================
// Task 457 — заявка: «Сделай отображение этих кодов как ручные,
// в Итоги/Талоны/печать входит» (развитие Task 456: авто-«д»/«н»
// замещения отпуска).
//
// Реализация:
//   • _autoDnEntries(y, m) — ВИРТУАЛЬНЫЕ записи слоя _AUTO_DN
//     (месяц сетки): {дата, таб_номер, статус «д»/«н»,
//     источник «авто»} — только для агрегации отчётов, в
//     «Записи_графика» НЕ пишутся, без часов/переработки;
//   • Итоги учёта (месяц) + печать/PDF/Excel: переработка
//     over/overDays (как у ручных «д»/«н», Task 322 — в явки/
//     часы не попадает), код в печатной сетке (_printCell /
//     _printModel — псевдо-запись с цветом справочника);
//   • Талоны: день явки + 12-часовой талон (получатели слоя —
//     всегда сменные, _overHours = 12);
//   • отображение «как ручные»: рамка ws-manual-dn + метка
//     ws-source-manual (индиго-пунктир ws-auto-dn снят — класс
//     инертный маркер), активная строка «д»/«н» в попапе;
//   • границы: записи не создаются (saveAll/_applyCellStatus
//     слой не трогают), Годовой итог — по серверным записям.
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const INDEX_SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

function extractMethod(src, name) {
    const start = src.indexOf(name + ': function(');
    if (start === -1) return null;
    const braceStart = src.indexOf('{', start);
    let depth = 0;
    for (let i = braceStart; i < src.length; i++) {
        if (src[i] === '{') depth++;
        else if (src[i] === '}') {
            depth--;
            if (depth === 0) return src.slice(start, i + 1);
        }
    }
    return null;
}

function methodText(src, name) {
    const m = extractMethod(src, name);
    if (m === null) throw new Error('метод не найден: ' + name);
    return m;
}

// Срез модуля WorkSchedule (имена методов неуникальны в монолите)
const WS_SRC = INDEX_SRC.slice(INDEX_SRC.indexOf('var WorkSchedule = {'));

// ============================================================
// 1. SRC — метод _autoDnEntries: виртуальные записи слоя
// ============================================================
describe('Task 457 — SRC: _autoDnEntries (виртуальные записи слоя)', () => {

    test('метод существует, комментарий-ссылка на заявку над ним', () => {
        const idx = WS_SRC.indexOf('_autoDnEntries: function(');
        assertTrue(idx !== -1, 'метод _autoDnEntries определён');
        assertTrue(WS_SRC.slice(Math.max(0, idx - 1200), idx)
                       .indexOf('Task 457') !== -1,
            'комментарий-ссылка на заявку Task 457');
    });

    test('фильтр месяца: префикс YYYY-MM-, чужой месяц — пусто', () => {
        const fn = methodText(WS_SRC, '_autoDnEntries');
        assertTrue(fn.indexOf("(m < 10 ? '0' : '') + m") !== -1,
            'двузначный месяц префикса');
        assertTrue(fn.indexOf("indexOf(pref) !== 0") !== -1,
            'ключи вне месяца сетки отбрасываются');
    });

    test('форма записи: статус из плана, источник «авто», БЕЗ часов/переработки', () => {
        const fn = methodText(WS_SRC, '_autoDnEntries');
        assertTrue(fn.indexOf("'статус': plan[k]") !== -1 &&
                   fn.indexOf("'источник': 'авто'") !== -1,
            'синтетическая строка для агрегации');
        assertEqual(fn.indexOf('часы'), -1,
            'поле «часы» слою не нужно (сменным — 12 в _overHours)');
        assertEqual(fn.indexOf('переработка'), -1,
            'флаг переработки (точка) — атрибут записи, у слоя его нет');
    });

    test('_autoDnEntries стоит ПОСЛЕ _autoDnPlan (рядом со слоем)', () => {
        const iPlan = WS_SRC.indexOf('_autoDnPlan: function(');
        const iEnt = WS_SRC.indexOf('_autoDnEntries: function(');
        assertTrue(iPlan !== -1 && iEnt !== -1 && iEnt > iPlan,
            'метод рядом с расчётом слоя');
    });
});

// ============================================================
// 2. SRC — включение в отчёты и печать
// ============================================================
describe('Task 457 — SRC: Итоги/Талоны/печать включают слой', () => {

    test('Итоги месяца и печать: concat виртуальных записей (гвард typeof)', () => {
        const tm = methodText(WS_SRC, '_renderTotalsMonth');
        assertTrue(tm.indexOf('entries.concat(') !== -1 &&
                   tm.indexOf('this._autoDnEntries(this._year, this._month)') !== -1,
            'Итоги: эффективные записи + слой');
        assertTrue(tm.indexOf("typeof this._autoDnEntries === 'function'") !== -1,
            'гвард — старые VM-харнессы без метода не падают');
        const pg = methodText(WS_SRC, 'printGrid');
        assertTrue(pg.indexOf('this._autoDnEntries(this._year, this._month)') !== -1,
            'печать: тот же agg — колонка «Перераб./дни», PDF/Excel');
    });

    test('Талоны: _talonsRows подмешивает слой месяца отчёта', () => {
        const fn = methodText(WS_SRC, '_talonsRows');
        assertTrue(fn.indexOf('eff.concat(this._autoDnEntries(mi.y, mi.m))') !== -1,
            'агрегация талонов: месяц — как у записей сетки (Task 455)');
    });

    test('печать сетки: _printCell — псевдо-запись авто-кода', () => {
        const fn = methodText(WS_SRC, '_printCell');
        assertTrue(fn.indexOf("if (!entry) {") !== -1 &&
                   fn.indexOf("entry = { 'статус': autoDn };") !== -1,
            'пустой ячейке с авто-кодом — псевдо-запись (код + фон справочника)');
        assertTrue(fn.indexOf("(this._AUTO_DN || {})") !== -1,
            'защита от undefined — печать работает и без слоя');
    });

    test('PDF/Excel: _printModel — код слоя в ячейках модели', () => {
        const fn = methodText(WS_SRC, '_printModel');
        assertTrue(fn.indexOf('(this._AUTO_DN || {})[key]') !== -1,
            'пустая ячейка с авто-кодом получает статус и цвет справочника');
        assertTrue(fn.indexOf('if (!status) {') !== -1,
            'слой не перекрывает записи/правки (только пустые ячейки)');
    });

    test('граница: записи НЕ создаются — saveAll/_applyCellStatus чисты', () => {
        const sa = methodText(WS_SRC, 'saveAll');
        assertEqual(sa.indexOf('_autoDnEntries'), -1,
            '«Сохранить» не отправляет слой на сервер');
        const ac = methodText(WS_SRC, '_applyCellStatus');
        assertEqual(ac.indexOf('_autoDnEntries'), -1,
            'правки ячеек — с записями/_PENDING, слой только читается');
        const ap = methodText(WS_SRC, '_autoDnPlan');
        assertEqual(ap.indexOf('_autoDnEntries'), -1,
            'расчёт слоя не зависит от собственных виртуальных записей (нет рекурсии)');
    });
});

// ============================================================
// 3. SRC — SW
// ============================================================
describe('Task 457 — SRC: SW kipia-test-v681', () => {
    test('CACHE_VERSION = kipia-test-v681, прежней v680 нет', () => {
        assertTrue(SW_SRC.indexOf("'kipia-test-v681'") !== -1,
            'новая версия SW v681');
        assertEqual(SW_SRC.indexOf("'kipia-test-v680'"), -1,
            'старой версии v680 не осталось');
        assertTrue(SW_SRC.indexOf('Task 457') !== -1,
            'комментарий истории Task 457');
    });
});

// ============================================================
// 4. VM — _autoDnEntries: карта слоя → записи
// ============================================================
describe('Task 457 — VM: _autoDnEntries', () => {

    const MAP = {
        '2026-10-03|02': 'д',
        '2026-10-08|02': 'н',
        '2026-09-15|02': 'д',   // чужой месяц (сентябрь)
        '2026-11-02|03': 'н'    // чужой месяц (ноябрь)
    };

    function host(map) {
        return new Function('return ({' +
            methodText(WS_SRC, '_autoDnEntries') + ',' +
            '_AUTO_DN: ' + JSON.stringify(map) + ',' +
            '});')();
    }

    test('записи только месяца сетки, поля синтетической строки', () => {
        const out = host(MAP)._autoDnEntries(2026, 10);
        assertEqual(out.length, 2, 'октябрьских записей — 2');
        for (const r of out) {
            assertEqual(r['источник'], 'авто', 'источник — авто');
            assertTrue(r['дата'].indexOf('2026-10-') === 0, 'дата октября');
            assertTrue(r['статус'] === 'д' || r['статус'] === 'н',
                'статус — код слоя');
        }
        assertEqual(out[0]['дата'], '2026-10-03', 'дата из ключа');
        assertEqual(out[0]['таб_номер'], '02', 'таб. номер из ключа');
        assertEqual(out[0]['статус'], 'д', 'статус из карты слоя');
    });

    test('фильтр месяца: сентябрь/ноябрь — свои записи, пустой месяц — []', () => {
        assertEqual(host(MAP)._autoDnEntries(2026, 9).length, 1,
            'сентябрь: 1 запись');
        assertEqual(host(MAP)._autoDnEntries(2026, 11).length, 1,
            'ноябрь: 1 запись');
        assertEqual(host(MAP)._autoDnEntries(2026, 12).length, 0,
            'декабря в слое нет');
    });

    test('защита: _AUTO_DN undefined/пустая карта/повреждённый ключ', () => {
        assertEqual(new Function('return ({' +
            methodText(WS_SRC, '_autoDnEntries') + '});')()
            ._autoDnEntries(2026, 10).length, 0,
            'undefined-карта (до первого _renderGrid) — пусто');
        assertEqual(host({})._autoDnEntries(2026, 10).length, 0,
            'пустой слой — пусто');
        assertEqual(host({ 'битый-ключ': 'д' })._autoDnEntries(2026, 10).length, 0,
            'ключ без «|» пропускается');
    });
});

// ============================================================
// 5. VM — Итоги: переработка over/overDays, явки/часы не тронуты
// ============================================================
describe('Task 457 — VM: Итоги учёта с виртуальными записями', () => {

    const CODES = [
        { code: 'Д', name: 'День (12-час)', color: '#c8e6c9' },
        { code: 'д', name: 'День в вых./праздник', color: '#dcecc9' },
        { code: 'н', name: 'Ночь в вых./праздник', color: '#cfd8f5' }
    ];

    function aggHost(opts) {
        opts = opts || {};
        return new Function('return ({' +
            methodText(WS_SRC, '_totalsEffectiveEntries') + ',' +
            methodText(WS_SRC, '_autoDnEntries') + ',' +
            methodText(WS_SRC, '_totalsZero') + ',' +
            methodText(WS_SRC, '_totalsAgg') + ',' +
            methodText(WS_SRC, '_codeHours') + ',' +
            methodText(WS_SRC, '_statusMeta') + ',' +
            methodText(WS_SRC, '_empTypeMap') + ',' +
            methodText(WS_SRC, '_overHours') + ',' +
            '_EMPLOYEES: ' + JSON.stringify(opts.emps || [{
                'таб_номер': '02', 'ФИО': 'Белов Б. Б.', 'тип': 'сменный' }]) + ',' +
            '_ENTRIES: ' + JSON.stringify(opts.entries || [
                { 'дата': '2026-10-06', 'таб_номер': '02', 'статус': 'Д', 'источник': 'авто' },
                { 'дата': '2026-10-07', 'таб_номер': '02', 'статус': 'Н', 'источник': 'авто' },
                { 'дата': '2026-10-14', 'таб_номер': '02', 'статус': 'Д', 'источник': 'авто' }]) + ',' +
            '_PENDING: ' + JSON.stringify(opts.pending || {}) + ',' +
            '_AUTO_DN: ' + JSON.stringify(opts.autoDn !== undefined ? opts.autoDn
                : { '2026-10-03|02': 'д', '2026-10-19|02': 'н' }) + ',' +
            '_STATUS_CODES: ' + JSON.stringify(CODES) + ',' +
            '});')();
    }

    // паттерн _renderTotalsMonth/printGrid: записи + слой
    function aggWith(h) {
        return h._totalsAgg(
            h._totalsEffectiveEntries()
                .concat(h._autoDnEntries(2026, 10)),
            h._empTypeMap(h._EMPLOYEES));
    }

    test('слой = ПЕРЕРАБОТКА: over/overDays растут, явки/часы НЕ тронуты', () => {
        const h = aggHost({});
        const before = h._totalsAgg(h._totalsEffectiveEntries(),
                                    h._empTypeMap(h._EMPLOYEES)).byTab['02'];
        const after = aggWith(h).byTab['02'];
        assertEqual(before.work, 3, 'без слоя: 3 явки');
        assertEqual(before.over, 0, 'без слоя: переработки нет');
        assertEqual(after.work, 3, 'явки НЕ изменились (д/н — не явка, Task 322)');
        assertEqual(after.hours, before.hours, 'часы явок НЕ изменились');
        assertEqual(after.overDays, 2, '2 дня переработки — виртуальные д/н');
        assertEqual(after.over, 24, 'сменному 12 ч × 2 = 24 ч');
        assertEqual(after.total, before.total + 2, 'total — все дни табеля');
    });

    test('ручной «д» и авто «н» — один счётчик (суммирование)', () => {
        const h = aggHost({
            entries: [{ 'дата': '2026-10-05', 'таб_номер': '02',
                        'статус': 'д', 'источник': 'руч', 'часы': null }],
            autoDn: { '2026-10-20|02': 'н' }
        });
        const a = aggWith(h).byTab['02'];
        assertEqual(a.overDays, 2, 'ручной «д» + авто «н» = 2 дня');
        assertEqual(a.over, 24, '12 + 12 = 24 ч');
        assertEqual(a.work, 0, 'явок нет');
    });

    test('auto «д» НЕ добавляет явок в сравнении с пустым слоем', () => {
        const h = aggHost({ autoDn: {} });
        const a = aggWith(h).byTab['02'];
        assertEqual(a.work, 3, 'слой пуст — только записи');
        assertEqual(a.overDays, 0, 'переработки нет');
    });
});

// ============================================================
// 6. VM — Талоны: день явки + 12-часовой талон
// ============================================================
describe('Task 457 — VM: Талоны с виртуальными записями', () => {

    const CODES = [
        { code: 'Д', name: 'День (12-час)', color: '#c8e6c9' },
        { code: 'д', name: 'День в вых./праздник', color: '#dcecc9' },
        { code: 'н', name: 'Ночь в вых./праздник', color: '#cfd8f5' }
    ];

    function talonsHost(autoDn, entries) {
        return new Function('return ({' +
            methodText(WS_SRC, '_autoDnEntries') + ',' +
            methodText(WS_SRC, '_talonsAgg') + ',' +
            methodText(WS_SRC, '_overHours') + ',' +
            methodText(WS_SRC, '_codeHours') + ',' +
            methodText(WS_SRC, '_statusMeta') + ',' +
            methodText(WS_SRC, '_empTypeMap') + ',' +
            '_EMPLOYEES: [{ "таб_номер": "02", "ФИО": "Белов Б. Б.", "тип": "сменный" }],' +
            '_ENTRIES: ' + JSON.stringify(entries || []) + ',' +
            '_AUTO_DN: ' + JSON.stringify(autoDn || {}) + ',' +
            '_STATUS_CODES: ' + JSON.stringify(CODES) + ',' +
            '});')();
    }

    test('авто «д»/«н»: дни явки и 12-часовые талоны (сменный)', () => {
        const h = talonsHost({ '2026-10-03|02': 'д', '2026-10-08|02': 'н' },
            [{ 'дата': '2026-10-06', 'таб_номер': '02', 'статус': 'Д' }]);
        // паттерн _talonsRows: eff + слой
        const eff = h._ENTRIES.concat(h._autoDnEntries(2026, 10));
        const a = h._talonsAgg(eff, h._empTypeMap(h._EMPLOYEES)).byTab['02'];
        assertEqual(a.days, 3, '2 смены Д + 2 виртуальных д/н = 3 дня явки');
        assertEqual(a.t12, 3, '12-часовые талоны: Д + д + н');
        assertEqual(a.t8, 0, '8-часовых нет');
    });

    test('пустой слой — талоны только по записям', () => {
        const h = talonsHost({}, [{ 'дата': '2026-10-06', 'таб_номер': '02', 'статус': 'Д8' }]);
        const eff = h._ENTRIES.concat(h._autoDnEntries(2026, 10));
        const a = h._talonsAgg(eff, h._empTypeMap(h._EMPLOYEES)).byTab['02'];
        assertEqual(a.days, 1, 'запись одна');
        assertEqual(a.t8, 1, 'Д8 — 8-часовой талон');
    });
});

// ============================================================
// 7. VM — печать: _printCell и _printModel с авто-кодом
// ============================================================
describe('Task 457 — VM: печать сетки (_printCell/_printModel)', () => {

    const CODES = [
        { code: 'Д', name: 'День (12-час)', color: '#c8e6c9' },
        { code: 'д', name: 'День в вых./праздник', color: '#dcecc9' },
        { code: 'н', name: 'Ночь в вых./праздник', color: '#cfd8f5' }
    ];
    const EMP = { 'таб_номер': '02', 'ФИО': 'Белов Б. Б.', 'тип': 'сменный' };

    function printHost(autoDn) {
        return new Function('return ({' +
            methodText(WS_SRC, '_printCell') + ',' +
            methodText(WS_SRC, '_statusMeta') + ',' +
            methodText(WS_SRC, '_vacationAt') + ',' +
            methodText(WS_SRC, '_calDayOff') + ',' +
            methodText(WS_SRC, '_esc') + ',' +
            '_EVENT_CODES: [],' +
            '_STATUS_CODES: ' + JSON.stringify(CODES) + ',' +
            '_AUTO_DN: ' + JSON.stringify(autoDn || {}) + ',' +
            '_VACATIONS: [],' +
            '_year: 2026, _month: 10,' +
            '});')();
    }

    test('_printCell: авто-код — как запись (код + фон, без точки/vac)', () => {
        const h = printHost({ '2026-10-03|02': 'д' });
        const td = h._printCell(3, '2026-10-03', EMP, null, false);
        assertTrue(td.indexOf('>д<') !== -1, 'код «д» в ячейке печати');
        assertTrue(td.indexOf('background:#dcecc9') !== -1,
            'фон — цвет справочника «д»');
        assertEqual(td.indexOf('wsp-over'), -1, 'точки переработки нет (не запись)');
        assertEqual(td.indexOf('wsp-vac'), -1, 'плана отпуска нет');
    });

    test('_printCell: запись поверх — авто не вмешивается', () => {
        const h = printHost({ '2026-10-03|02': 'д' });
        const td = h._printCell(3, '2026-10-03', EMP,
            { 'статус': 'Д', 'источник': 'авто' }, false);
        assertTrue(td.indexOf('>Д<') !== -1, 'код записи');
        assertEqual(td.indexOf('>д<'), -1, 'слой перекрыт записью');
    });

    test('_printCell: без слоя пустая ячейка остаётся пустой', () => {
        const h = printHost({});
        const td = h._printCell(3, '2026-10-03', EMP, null, false);
        assertEqual(td.indexOf('>д<'), -1, 'кода нет');
        assertEqual(td.indexOf('background:'), -1, 'фона нет');
        // слой персонален: авто другого работника ячейку не занимает
        const h2 = printHost({ '2026-10-03|03': 'д' });
        assertEqual(h2._printCell(3, '2026-10-03', EMP, null, false)
            .indexOf('>д<'), -1,
            'авто чужого таб. номера не показывается');
    });

    test('_printModel: авто-код в ячейках PDF/Excel + итоги строки', () => {
        const h = new Function('return ({' +
            methodText(WS_SRC, '_printModel') + ',' +
            methodText(WS_SRC, '_buildEntryIndex') + ',' +
            methodText(WS_SRC, '_autoDnEntries') + ',' +
            methodText(WS_SRC, '_totalsZero') + ',' +
            methodText(WS_SRC, '_totalsAgg') + ',' +
            methodText(WS_SRC, '_codeHours') + ',' +
            methodText(WS_SRC, '_statusMeta') + ',' +
            methodText(WS_SRC, '_empTypeMap') + ',' +
            methodText(WS_SRC, '_overHours') + ',' +
            methodText(WS_SRC, '_vacationAt') + ',' +
            methodText(WS_SRC, '_empTipLine') + ',' +
            methodText(WS_SRC, '_isoDate') + ',' +
            '_printEventsData: function() { return []; },' +
            '_EVENT_CODES: [],' +
            '_STATUS_CODES: ' + JSON.stringify(CODES) + ',' +
            '_EMPLOYEES: [' + JSON.stringify(EMP) + '],' +
            '_ENTRIES: [{ "дата": "2026-10-06", "таб_номер": "02", "статус": "Д", "источник": "авто" }],' +
            '_PENDING: {},' +
            '_AUTO_DN: { "2026-10-03|02": "д" },' +
            '_VACATIONS: [],' +
            '_view: "full",' +
            '_year: 2026, _month: 10,' +
            '});')();
        // agg — паттерн printGrid: записи + слой
        const agg = h._totalsAgg(
            [{ 'дата': '2026-10-06', 'таб_номер': '02', 'статус': 'Д', 'источник': 'авто' }]
                .concat(h._autoDnEntries(2026, 10)),
            h._empTypeMap(h._EMPLOYEES));
        const model = h._printModel([EMP], agg);
        assertEqual(model.rows.length, 1, 'строка работника');
        const day3 = model.rows[0].cells[2];   // 3 октября
        assertEqual(day3.status, 'д', 'авто-код в ячейке модели');
        assertEqual(day3.color, '#dcecc9', 'цвет справочника «д»');
        assertFalse(day3.overtime, 'точки переработки нет');
        assertFalse(day3.vac, 'это не план отпуска');
        const day6 = model.rows[0].cells[5];   // 6 октября — запись
        assertEqual(day6.status, 'Д', 'запись на месте');
        const day4 = model.rows[0].cells[3];   // 4 октября — пусто
        assertEqual(day4.status, '', 'без записи и слоя — пусто');
        assertEqual(model.rows[0].work, 1, 'явка — запись Д');
        assertEqual(model.rows[0].overDays, 1, '«Перераб./дни» — виртуальный «д»');
    });
});
