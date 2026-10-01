// ============================================================
// Task 456 — заявка: «Если какой то из работников из сменного
// персонала в отпуске - код статуса "ОТ", то у сменного персонала,
// который не в отпуске, в шахматке также должны автоматически
// расставляться коды статусов "д" ... и "н" ...» — с правилами
// примыкания выходного дня и очерёдности по последнему «д»/«н».
//
// Реализация (полностью КЛИЕНТСКАЯ, производный слой):
//   • _autoDnPlan — расчёт авто-«д»/«н» открытого месяца:
//     потенциальная смена отпускника (_plannedShiftAt: «Д»/«Н»)
//     → выходной день кандидата (плановый выходной цикла, пустая
//     ячейка без записи/правки/плана отпуска) → примыкание
//     (обе стороны выходные, либо выходной + рабочий совпадающий
//     по времени суток) → очерёдность (последний «д»/«н» дальше
//     от даты расстановки — первый);
//   • _AUTO_DN — кэш слоя, пересчитывается каждым _renderGrid;
//   • _renderCell — код «д»/«н» как основной (фон справочника) +
//     пунктирная рамка ws-auto-dn (индиго — отличима от ручных
//     ws-manual-dn и правок ws-pending);
//   • попап ячейки — подсказка «Авто: … (замещение отпуска, в
//     записи не сохранён)»;
//   • слой НЕ пишется в «Записи_графика» и НЕ входит в Итоги
//     учёта/Талоны/печать (записи — источник правды отчётов).
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
// 1. SRC — метод _autoDnPlan: правила заявки
// ============================================================
describe('Task 456 — SRC: _autoDnPlan (правила заявки)', () => {

    test('метод существует, комментарий-ссылка на заявку над ним', () => {
        const idx = WS_SRC.indexOf('_autoDnPlan: function(');
        assertTrue(idx !== -1, 'метод _autoDnPlan определён');
        // комментарий-документация метода длинный (правила заявки
        // целиком) — окно 2600 символов
        assertTrue(WS_SRC.slice(Math.max(0, idx - 2600), idx)
                       .indexOf('Task 456') !== -1,
            'комментарий-ссылка на заявку Task 456');
    });

    test('фильтр: ТОЛЬКО сменный персонал с шаблоном ротации и стартом цикла', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf("!== 'сменный'") !== -1,
            'в расчёте участвуют только сотрудники типа «сменный»');
        assertTrue(fn.indexOf('шаблон_ротации') !== -1 &&
                   fn.indexOf('старт_цикла') !== -1,
            'без шаблона/старта расписание неизвестно');
        assertTrue(fn.indexOf('shifts.length < 2') !== -1,
            'нужен хотя бы отпускник и кандидат');
    });

    test('потенциальная смена отпускника — _plannedShiftAt («Д»/«Н» по циклу)', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf('this._plannedShiftAt(iso, shifts[a])') !== -1,
            'потенциальная смена отпускника — план цикла');
        assertTrue(fn.indexOf("ps === 'Д' || ps === 'Н'") !== -1,
            'только сменные коды «Д»/«Н»');
    });

    test('отпускник — запись семейства отпусков ИЛИ план листа «Отпуска»', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf('_VAC_CODES') !== -1 &&
                   fn.indexOf('_vacationAt') !== -1,
            'день отпуска: _VAC_CODES записи или план _vacationAt (как vacMain Task 305)');
    });

    test('примыкание: обе стороны выходные, ЛИБО выходной + рабочий совпадающий', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf("(cp === 'off' && cn === 'off')") !== -1,
            'случай 1: с обеих сторон выходные');
        assertTrue(fn.indexOf("(cp === 'off' && cn === want)") !== -1 &&
                   fn.indexOf("(cn === 'off' && cp === want)") !== -1,
            'случай 2: выходной с одной стороны, рабочий совпадающий — с другой');
        // время суток: дневные Д/Д8/Д7,2/д ↔ «д», ночные Н/н ↔ «н»
        assertTrue(fn.indexOf("code === 'Д' || code === 'Д8' || code === 'Д7,2' ||") !== -1,
            'дневные смены — одно семейство времени суток');
    });

    test('кандидат — ТОЛЬКО полностью пустая планово-выходная ячейка', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf('recIdx[keyB] || pend[keyB] || plan[keyB]) continue') !== -1,
            'запись/правка/уже назначенный авто — ячейка занята');
        assertTrue(fn.indexOf("dayCat(empB, iso) !== 'off'") !== -1,
            'сам день — плановый выходной (не смена, не до старта цикла)');
    });

    test('очерёдность: последний «д»/«н» ДАЛЬШЕ от даты — первый приоритет', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf('9999') !== -1,
            'нет истории «д»/«н» в месяце — максимальный приоритет');
        assertTrue(fn.indexOf('cands.sort') !== -1 &&
                   fn.indexOf('(y.dist - x.dist)') !== -1,
            'сортировка по убыванию расстояния до последнего «д»/«н»');
        assertTrue(fn.indexOf('lastDn[winTab] = day;') !== -1,
            'назначение обновляет историю — следующий день уходит другому (поочерёдность)');
    });

    test('эффективные записи месяца — записи + правки (_totalsEffectiveEntries)', () => {
        const fn = methodText(WS_SRC, '_autoDnPlan');
        assertTrue(fn.indexOf('this._totalsEffectiveEntries()') !== -1,
            'ручные правки участвуют в примыкании и истории «д»/«н»');
    });
});

// ============================================================
// 2. SRC — подключение слоя: сетка, ячейка, попап, CSS, поле
// ============================================================
describe('Task 456 — SRC: рендер сетки/ячейки/попап + CSS', () => {

    test('_renderGrid пересчитывает слой на КАЖДЫЙ рендер', () => {
        const fn = methodText(WS_SRC, '_renderGrid');
        assertTrue(fn.indexOf('this._AUTO_DN = this._autoDnPlan();') !== -1,
            'правки ячеек (onPopupStatus → _renderGrid) сразу меняют план');
    });

    test('поле _AUTO_DN объявлено в состоянии модуля', () => {
        assertTrue(WS_SRC.indexOf('_AUTO_DN: {},') !== -1,
            'кэш производного слоя в состоянии WorkSchedule');
    });

    test('_renderCell: авто-код — основной контент + фон справочника + рамка', () => {
        const fn = methodText(WS_SRC, '_renderCell');
        assertTrue(fn.indexOf("classes.push('ws-auto-dn');") !== -1,
            'класс ws-auto-dn на ячейке авто-кода');
        assertTrue(fn.indexOf("(showMainCode ? (status || autoDn) :") !== -1,
            'код «д»/«н» выводится в центре пустой ячейки');
        assertTrue(fn.indexOf('(this._AUTO_DN || {})') !== -1,
            'план читается из _AUTO_DN с защитой от undefined');
        assertTrue(fn.indexOf('!status && !isPending') !== -1,
            'записи/правки слой не перекрывает');
    });

    test('попап ячейки: подсказка об авто-коде (в записи не сохранён)', () => {
        const fn = methodText(WS_SRC, '_renderCellPopup');
        assertTrue(fn.indexOf('ws-popup-auto') !== -1,
            'строка-подсказка .ws-popup-auto');
        assertTrue(fn.indexOf('замещение отпуска') !== -1 &&
                   fn.indexOf('в записи не сохранён') !== -1,
            'текст поясняет природу авто-кода');
    });

    test('CSS: рамка авто ws-auto-dn (индиго-пунктир) + строка попапа', () => {
        assertTrue(INDEX_SRC.indexOf('.ws-grid tbody td.ws-cell.ws-auto-dn {') !== -1,
            'правило .ws-auto-dn');
        assertTrue(INDEX_SRC.indexOf('.ws-grid tbody td.ws-cell.ws-auto-dn {\n' +
                     '        outline: 2px dashed rgba(121, 134, 203, 0.95);') !== -1,
            'пунктирная рамка индиго — отличима от ws-pending/ws-vac-plan');
        assertTrue(INDEX_SRC.indexOf('.ws-popup-auto {') !== -1,
            'правило .ws-popup-auto');
    });
});

// ============================================================
// 3. SRC — изоляция слоя: НЕ записи, НЕ Итоги, НЕ Талоны, НЕ печать
// ============================================================
describe('Task 456 — SRC: производный слой НЕ входит в отчёты/печать', () => {

    test('_printCell (печать шахматки) слой не показывает', () => {
        const fn = methodText(WS_SRC, '_printCell');
        assertEqual(fn.indexOf('_AUTO_DN'), -1,
            'печать — по записям (прецедент Task 442: экранные слои в печати не показываются)');
        assertEqual(fn.indexOf('ws-auto-dn'), -1,
            'рамка авто — только экранный признак');
    });

    test('_totalsAgg (Итоги учёта) авто-«д»/«н» не считает', () => {
        const fn = methodText(WS_SRC, '_totalsAgg');
        assertEqual(fn.indexOf('_AUTO_DN'), -1,
            'переработка — только по записям (Task 322)');
    });

    test('_talonsRows (Талоны) авто-«д»/«н» не учитывает', () => {
        const fn = methodText(WS_SRC, '_talonsRows');
        assertEqual(fn.indexOf('_AUTO_DN'), -1,
            'талоны — по записям сетки (Task 447–455)');
    });
});

// ============================================================
// 4. SRC — SW
// ============================================================
describe('Task 456 — SRC: SW kipia-test-v680', () => {
    test('CACHE_VERSION = kipia-test-v680, прежней v679 нет', () => {
        assertTrue(SW_SRC.indexOf("'kipia-test-v680'") !== -1,
            'новая версия SW v680');
        assertEqual(SW_SRC.indexOf("'kipia-test-v679'"), -1,
            'старой версии v679 не осталось');
        assertTrue(SW_SRC.indexOf('Task 456') !== -1,
            'комментарий истории Task 456');
    });
});

// ============================================================
// 5. VM — харнесс _autoDnPlan
// ============================================================
// Октябрь 2026. Три сменных, старт циклов 2026-09-01:
//   01 Отпускников: цикл 4 «Д Н В В»  → смены Д/Н: 3,4,7,8,11,12,
//      15,16,19,20,23,24,27,28,31 октября;
//   02 Белов и 03 Чернов: цикл 8 «В В В Д Н В В В» → рабочие
//      6,7,14,15,22,23,30,31; выходные — остальные (в т.ч. все
//      дни потенциальных смен отпускника, кроме 7/8… по фазе).
// Отпуск 01: весь октябрь (план листа «Отпуска»).
// Ожидание (ручной прогон правил заявки):
//   02: 3«д» 8«н» 12«н» 19«д» 24«н» 28«н»   — 6 назначений
//   03: 4«н» 11«д» 16«н» 20«н» 27«д»        — 5 назначений
//   (поочерёдность: 02→03→02→03→…; дни 7,15,23,31 — у 02/03
//    рабочая смена, кандидат нет; 5,13,21,29 — смена «Н»
//    отпускника на рабочих «Н» днях 02/03 — не выходной)
// ============================================================
describe('Task 456 — VM: _autoDnPlan (базовый сценарий)', () => {

    const PAT_A = { id: 'pa', cycle: 4, days: [
        { day: 1, status: 'Д' }, { day: 2, status: 'Н' },
        { day: 3, status: '' }, { day: 4, status: '' } ] };
    const PAT_BC = { id: 'pbc', cycle: 8, days: [
        { day: 1, status: '' }, { day: 2, status: '' },
        { day: 3, status: '' }, { day: 4, status: 'Д' },
        { day: 5, status: 'Н' }, { day: 6, status: '' },
        { day: 7, status: '' }, { day: 8, status: '' } ] };

    const EMPS = [
        { 'таб_номер': '01', 'ФИО': 'Отпускников О. О.', 'тип': 'сменный',
          'шаблон_ротации': 'pa', 'старт_цикла': '2026-09-01' },
        { 'таб_номер': '02', 'ФИО': 'Белов Б. Б.', 'тип': 'сменный',
          'шаблон_ротации': 'pbc', 'старт_цикла': '2026-09-01' },
        { 'таб_номер': '03', 'ФИО': 'Чернов Ч. Ч.', 'тип': 'сменный',
          'шаблон_ротации': 'pbc', 'старт_цикла': '2026-09-01' }
    ];

    function planHost(opts) {
        opts = opts || {};
        return new Function('return ({' +
            methodText(WS_SRC, '_autoDnPlan') + ',\n' +
            methodText(WS_SRC, '_plannedShiftAt') + ',\n' +
            methodText(WS_SRC, '_totalsEffectiveEntries') + ',\n' +
            methodText(WS_SRC, '_vacationAt') + ',\n' +
            methodText(WS_SRC, '_parseIsoLocal') + ',\n' +
            methodText(WS_SRC, '_isoDate') + ',\n' +
            '_EMPLOYEES: ' + JSON.stringify(opts.employees || EMPS) + ',' +
            '_ENTRIES: ' + JSON.stringify(opts.entries || []) + ',' +
            '_PENDING: ' + JSON.stringify(opts.pending || {}) + ',' +
            '_VACATIONS: ' + JSON.stringify(opts.vacations !== undefined
                ? opts.vacations
                : [{ 'таб_номер': '01', 'дата_начала': '2026-10-01',
                     'дата_окончания': '2026-10-31' }]) + ',' +
            '_VAC_CODES: ' + JSON.stringify(['ОТ', 'У']) + ',' +
            '_PATTERNS: ' + JSON.stringify(opts.patterns || [PAT_A, PAT_BC]) + ',' +
            '_year: 2026, _month: 10,' +
            '});')();
    }

    test('полный месяц: карта назначений совпадает с ручным прогоном заявки', () => {
        const h = planHost({});
        const plan = h._autoDnPlan();
        const expect = {
            // 02 Белов
            '2026-10-03|02': 'д', '2026-10-08|02': 'н',
            '2026-10-12|02': 'н', '2026-10-19|02': 'д',
            '2026-10-24|02': 'н', '2026-10-28|02': 'н',
            // 03 Чернов
            '2026-10-04|03': 'н', '2026-10-11|03': 'д',
            '2026-10-16|03': 'н', '2026-10-20|03': 'н',
            '2026-10-27|03': 'д'
        };
        assertEqual(Object.keys(plan).length, 11,
            'ровно 11 назначений (лишних нет)');
        for (const k of Object.keys(expect)) {
            assertEqual(plan[k], expect[k], 'день ' + k + ' → «' + expect[k] + '»');
        }
        for (const k of Object.keys(plan)) {
            assertTrue(Object.prototype.hasOwnProperty.call(expect, k),
                'неожиданное назначение: ' + k + ' → ' + plan[k]);
        }
    });

    test('тип смены отпускника задаёт код: «Д»→«д», «Н»→«н»', () => {
        const h = planHost({});
        const plan = h._autoDnPlan();
        assertEqual(plan['2026-10-03|02'], 'д',
            'день 3: потенциальная смена отпускника «Д» → код «д»');
        assertEqual(plan['2026-10-04|03'], 'н',
            'день 4: потенциальная смена «Н» → код «н»');
    });

    test('примыкание: сосед-«Н» не даёт дневную, сосед-«Д» не даёт ночную', () => {
        const h = planHost({});
        const plan = h._autoDnPlan();
        // день 4: у 02 сосед-авто «д» (дневная) → «н» НЕ ставится 02
        assertEqual(plan['2026-10-04|02'], undefined,
            'после «д» ночная смена 02 не ставится (время суток не совпадает)');
        // день 12: у 03 сосед-авто «д» → «н» 03 не ставится (взял 02)
        assertEqual(plan['2026-10-12|03'], undefined,
            'сосед-«дневная» блокирует ночную для 03');
    });

    test('рабочий день кандидата — НЕ выходной: авто не ставится', () => {
        const h = planHost({});
        const plan = h._autoDnPlan();
        // 7/8 октября: смена «Д»/«Н» отпускника, но у 02 и 03 это
        // собственные смены (Н 7-го, Д 6-го…): 7-е — рабочие «Н»
        assertEqual(plan['2026-10-07|02'], undefined,
            'день 7: у 02/03 рабочая ночная — авто-кода нет');
        assertEqual(plan['2026-10-07|03'], undefined,
            'день 7: и у 03 рабочая — авто-кода нет');
    });

    test('поочерёдность: 02→03→02→… — назначивший получает низший приоритет', () => {
        const h = planHost({});
        const plan = h._autoDnPlan();
        // день 3 взял 02 (первый по списку, оба без истории);
        // день 11: dist 02 = 11-8 = 3 < dist 03 = 11-4 = 7 → 03
        assertEqual(plan['2026-10-03|02'], 'д', 'день 3 — первый кандидат 02');
        assertEqual(plan['2026-10-11|03'], 'д', 'день 11 — очередь 03');
        assertEqual(plan['2026-10-19|02'], 'д', 'день 19 — снова 02 (дальше от его «н»)');
    });

    test('примыкание «выходной + рабочая совпадающая»: «н» после блока «Н»', () => {
        const h = planHost({});
        const plan = h._autoDnPlan();
        // день 8: у 02 сосед 7-го — рабочая «Н» (совпадает с «Н»
        // отпускника по времени суток), 9-е — выходной → «н» 02
        assertEqual(plan['2026-10-08|02'], 'н',
            'выходной между рабочей «Н» и выходным — «н» ставится');
    });

    test('отпуск ПЛАНОМ (лист «Отпуска», записи нет) — слой работает', () => {
        const h = planHost({});  // vacations по умолчанию — план 01
        const plan = h._autoDnPlan();
        assertEqual(plan['2026-10-03|02'], 'д',
            'несформированный месяц: план отпуска + циклы достаточно');
    });
});

// ============================================================
// 6. VM — отпуск ЗАПИСЯМИ «ОТ»/«У» (сформированный месяц)
// ============================================================
describe('Task 456 — VM: отпуск записями «ОТ» и «У»', () => {

    const PAT_A = { id: 'pa', cycle: 4, days: [
        { day: 1, status: 'Д' }, { day: 2, status: 'Н' },
        { day: 3, status: '' }, { day: 4, status: '' } ] };
    const PAT_BC = { id: 'pbc', cycle: 8, days: [
        { day: 1, status: '' }, { day: 2, status: '' },
        { day: 3, status: '' }, { day: 4, status: 'Д' },
        { day: 5, status: 'Н' }, { day: 6, status: '' },
        { day: 7, status: '' }, { day: 8, status: '' } ] };
    const EMPS = [
        { 'таб_номер': '01', 'ФИО': 'Отпускников О. О.', 'тип': 'сменный',
          'шаблон_ротации': 'pa', 'старт_цикла': '2026-09-01' },
        { 'таб_номер': '02', 'ФИО': 'Белов Б. Б.', 'тип': 'сменный',
          'шаблон_ротации': 'pbc', 'старт_цикла': '2026-09-01' },
        { 'таб_номер': '03', 'ФИО': 'Чернов Ч. Ч.', 'тип': 'сменный',
          'шаблон_ротации': 'pbc', 'старт_цикла': '2026-09-01' }
    ];

    function host(entries) {
        return new Function('return ({' +
            methodText(WS_SRC, '_autoDnPlan') + ',\n' +
            methodText(WS_SRC, '_plannedShiftAt') + ',\n' +
            methodText(WS_SRC, '_totalsEffectiveEntries') + ',\n' +
            methodText(WS_SRC, '_vacationAt') + ',\n' +
            methodText(WS_SRC, '_parseIsoLocal') + ',\n' +
            methodText(WS_SRC, '_isoDate') + ',\n' +
            '_EMPLOYEES: ' + JSON.stringify(EMPS) + ',' +
            '_ENTRIES: ' + JSON.stringify(entries) + ',' +
            '_PENDING: {},' +
            '_VACATIONS: [],' +
            '_VAC_CODES: ' + JSON.stringify(['ОТ', 'У']) + ',' +
            '_PATTERNS: ' + JSON.stringify([PAT_A, PAT_BC]) + ',' +
            '_year: 2026, _month: 10,' +
            '});')();
    }

    test('записи «ОТ» (дни 3/4/8) — те же назначения, что и планом', () => {
        const h = host([
            { 'дата': '2026-10-03', 'таб_номер': '01', 'статус': 'ОТ', 'источник': 'авто' },
            { 'дата': '2026-10-04', 'таб_номер': '01', 'статус': 'ОТ', 'источник': 'авто' },
            { 'дата': '2026-10-08', 'таб_номер': '01', 'статус': 'ОТ', 'источник': 'авто' }
        ]);
        const plan = h._autoDnPlan();
        assertEqual(plan['2026-10-03|02'], 'д', 'день 3: «ОТ» записью — 02');
        assertEqual(plan['2026-10-04|03'], 'н', 'день 4: «ОТ» записью — 03');
        assertEqual(plan['2026-10-08|02'], 'н', 'день 8: очерёдность 02 (5 > 4)');
        assertEqual(plan['2026-10-08|03'], undefined, 'день 8: 03 не дублирует');
    });

    test('«У» (учебный отпуск) — тоже отпуск для слоя', () => {
        const h = host([
            { 'дата': '2026-10-03', 'таб_номер': '01', 'статус': 'У', 'источник': 'авто' }
        ]);
        const plan = h._autoDnPlan();
        assertEqual(plan['2026-10-03|02'], 'д',
            'семейство _VAC_CODES (ОТ/У) — как vacMain Task 305');
    });
});

// ============================================================
// 7. VM — соседи: «до старта цикла» и «день отсутствия» блокируют
// ============================================================
describe('Task 456 — VM: соседи-блокеры примыкания', () => {

    const PAT_A = { id: 'p2a', cycle: 2, days: [
        { day: 1, status: 'Д' }, { day: 2, status: '' } ] };
    const PAT_B = { id: 'p2b', cycle: 4, days: [
        { day: 1, status: '' }, { day: 2, status: '' },
        { day: 3, status: '' }, { day: 4, status: 'Д' } ] };
    const EMPS = [
        { 'таб_номер': '01', 'ФИО': 'Отпускников О. О.', 'тип': 'сменный',
          'шаблон_ротации': 'p2a', 'старт_цикла': '2026-10-01' },
        { 'таб_номер': '02', 'ФИО': 'Белов Б. Б.', 'тип': 'сменный',
          'шаблон_ротации': 'p2b', 'старт_цикла': '2026-10-05' }
    ];

    function host(entries) {
        return new Function('return ({' +
            methodText(WS_SRC, '_autoDnPlan') + ',\n' +
            methodText(WS_SRC, '_plannedShiftAt') + ',\n' +
            methodText(WS_SRC, '_totalsEffectiveEntries') + ',\n' +
            methodText(WS_SRC, '_vacationAt') + ',\n' +
            methodText(WS_SRC, '_parseIsoLocal') + ',\n' +
            methodText(WS_SRC, '_isoDate') + ',\n' +
            '_EMPLOYEES: ' + JSON.stringify(EMPS) + ',' +
            '_ENTRIES: ' + JSON.stringify(entries || []) + ',' +
            '_PENDING: {},' +
            '_VACATIONS: ' + JSON.stringify([
                { 'таб_номер': '01', 'дата_начала': '2026-10-01',
                  'дата_окончания': '2026-10-31' }]) + ',' +
            '_VAC_CODES: ' + JSON.stringify(['ОТ', 'У']) + ',' +
            '_PATTERNS: ' + JSON.stringify([PAT_A, PAT_B]) + ',' +
            '_year: 2026, _month: 10,' +
            '});')();
    }

    test('сосед ДО старта цикла — не выходной: назначения нет', () => {
        const plan = host()._autoDnPlan();
        // 5 октября: выходной 02, смена «Д» отпускника, но 4-е —
        // до старта цикла 02 (старт 5-го) — данных нет, блок
        assertEqual(plan['2026-10-05|02'], undefined,
            'день до старта цикла не считается выходным соседом');
    });

    test('сосед-отсутствие («Б») блокирует, смена после него — работает', () => {
        const plan = host([
            { 'дата': '2026-10-06', 'таб_номер': '02', 'статус': 'Б',
              'источник': 'авто' }
        ])._autoDnPlan();
        // 7-е: сосед 6-го — «Б» (не выходной и не рабочий) → блок
        assertEqual(plan['2026-10-07|02'], undefined,
            'день отсутствия соседом не бывает — правило не выполнено');
        // 9-е: сосед 8-го — рабочая «Д» (совпадает по времени), 10-е выходной
        assertEqual(plan['2026-10-09|02'], 'д',
            '«выходной + рабочая совпадающая» — назначение есть');
    });
});

// ============================================================
// 8. VM — очерёдность: ручной «д»/«н» и правки ячеек
// ============================================================
describe('Task 456 — VM: приоритет/правки', () => {

    const PAT_A = { id: 'pa', cycle: 4, days: [
        { day: 1, status: 'Д' }, { day: 2, status: 'Н' },
        { day: 3, status: '' }, { day: 4, status: '' } ] };
    const PAT_BC = { id: 'pbc', cycle: 8, days: [
        { day: 1, status: '' }, { day: 2, status: '' },
        { day: 3, status: '' }, { day: 4, status: 'Д' },
        { day: 5, status: 'Н' }, { day: 6, status: '' },
        { day: 7, status: '' }, { day: 8, status: '' } ] };
    const EMPS = [
        { 'таб_номер': '01', 'ФИО': 'Отпускников О. О.', 'тип': 'сменный',
          'шаблон_ротации': 'pa', 'старт_цикла': '2026-09-01' },
        { 'таб_номер': '02', 'ФИО': 'Белов Б. Б.', 'тип': 'сменный',
          'шаблон_ротации': 'pbc', 'старт_цикла': '2026-09-01' },
        { 'таб_номер': '03', 'ФИО': 'Чернов Ч. Ч.', 'тип': 'сменный',
          'шаблон_ротации': 'pbc', 'старт_цикла': '2026-09-01' }
    ];

    function host(opts) {
        opts = opts || {};
        return new Function('return ({' +
            methodText(WS_SRC, '_autoDnPlan') + ',\n' +
            methodText(WS_SRC, '_plannedShiftAt') + ',\n' +
            methodText(WS_SRC, '_totalsEffectiveEntries') + ',\n' +
            methodText(WS_SRC, '_vacationAt') + ',\n' +
            methodText(WS_SRC, '_parseIsoLocal') + ',\n' +
            methodText(WS_SRC, '_isoDate') + ',\n' +
            '_EMPLOYEES: ' + JSON.stringify(opts.employees || EMPS) + ',' +
            '_ENTRIES: ' + JSON.stringify(opts.entries || []) + ',' +
            '_PENDING: ' + JSON.stringify(opts.pending || {}) + ',' +
            '_VACATIONS: ' + JSON.stringify([
                { 'таб_номер': '01', 'дата_начала': '2026-10-01',
                  'дата_окончания': '2026-10-31' }]) + ',' +
            '_VAC_CODES: ' + JSON.stringify(['ОТ', 'У']) + ',' +
            '_PATTERNS: ' + JSON.stringify(opts.patterns || [PAT_A, PAT_BC]) + ',' +
            '_year: 2026, _month: 10,' +
            '});')();
    }

    test('ручная запись «д» понижает приоритет: день 3 уходит 03', () => {
        const h = host({
            entries: [{ 'дата': '2026-10-02', 'таб_номер': '02',
                        'статус': 'д', 'источник': 'руч' }]
        });
        const plan = h._autoDnPlan();
        assertEqual(plan['2026-10-03|03'], 'д',
            'последний «д» 02 — 2-го (ближе) → назначение 03');
        assertEqual(plan['2026-10-03|02'], undefined,
            '02 в этот день авто-код не получает');
        assertEqual(plan['2026-10-04|02'], 'н',
            'день 4: 03 занят соседом-«д», 02 подходит (вых + вых)');
    });

    test('локальная правка ячейки исключает кандидата (день 3 → 03)', () => {
        const h = host({
            pending: { '2026-10-03|02': { 'статус': 'Д' } }
        });
        const plan = h._autoDnPlan();
        assertEqual(plan['2026-10-03|02'], undefined,
            'правка пользователя поверх — авто не ставится');
        assertEqual(plan['2026-10-03|03'], 'д',
            'очередь переходит к 03');
        // день 4: у обоих сосед-«д» → «н» никому
        assertEqual(plan['2026-10-04|02'], undefined,
            'день 4: сосед 02 — правка «Д» (дневная) → «н» 02 нет');
        assertEqual(plan['2026-10-04|03'], undefined,
            'день 4: сосед 03 — его же авто «д» → «н» 03 нет');
    });

    test('несменные/без шаблона/одиночный сменный — план пуст', () => {
        // кандидаты — дневные: некому замещать
        const dayEmps = EMPS.map(function(e, i) {
            return Object.assign({}, e, { 'тип': (i === 0 ? 'сменный' : 'дневной') });
        });
        assertEqual(Object.keys(host({ employees: dayEmps })._autoDnPlan()).length, 0,
            'дневной персонал кандидатом не бывает');
        // отпускник — дневной: потенциальной смены нет
        const vacDayEmps = EMPS.map(function(e, i) {
            return Object.assign({}, e, { 'тип': (i === 0 ? 'дневной' : 'сменный') });
        });
        assertEqual(Object.keys(host({ employees: vacDayEmps })._autoDnPlan()).length, 0,
            'дневной отпускник смен не создаёт');
        // одиночный сменный
        assertEqual(Object.keys(host({ employees: [EMPS[0]] })._autoDnPlan()).length, 0,
            'один сменный — некого замещать');
        // у кандидатов нет шаблона
        const noPat = [
            EMPS[0],
            Object.assign({}, EMPS[1], { 'шаблон_ротации': null }),
            Object.assign({}, EMPS[2], { 'шаблон_ротации': null })
        ];
        assertEqual(Object.keys(host({ employees: noPat })._autoDnPlan()).length, 0,
            'без шаблона ротации расписание неизвестно');
    });
});
