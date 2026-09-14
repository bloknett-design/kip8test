// tests/test-task367.js
// Task 367: расходомеры — заявка пользователя:
//   «По баннеру недоставленных показаний, упростим ещё, убери
//    появление баннера вовсе, но сделай цвет шрифта значений в списке
//    карточек расходомеров желто-оранжевым когда возникает такая
//    ситуация, и после успешной передачи данных на сервер, снова
//    зелёным. Кстати к расходомерам еженедельным и месячным тоже
//    примени правило изменения цвета на красный, только не по суткам
//    а по календарным недели и месяцу.»
//
// ЧТО ПРОВЕРЯЕТСЯ:
//   A. SRC — баннер удалён полностью; вместо него жёлто-оранжевый
//      цвет ЗНАЧЕНИЙ карточек (.flow-summary-val-pending, приоритет
//      над красным); перерендеры после _outboxAdd (день/период) и
//      в finish() флаша; _isOverdue — регэкспы периодов.
//   B. VM — _isOverdue: недельные по КАЛЕНДАРНОЙ неделе пн–вс,
//      месячные по месяцу (Task 357 подтверждён + закреплён);
//      сокращения («Еженед.», «Ежемес.») и «N раз в неделю/месяц»
//      попадают в свою ветку (раньше считались суточными);
//      суточная логика (6:00, Task 365) не сломана.
//   C. SW v596 (guard v597).

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');

const INDEX_SRC = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(__dirname, '..', 'sw.js'), 'utf8');

// ============================================================
// Извлечение методов из FlowmeterData (балансировка скобок)
// ============================================================
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

// ============================================================
// A. SRC — клиент
// ============================================================
describe('Task 367 — SRC: баннер убран, значения жёлто-оранжевые', () => {

    test('Баннера нет: класс, CSS, хелпер, вызовы — всё удалено', () => {
        assertTrue(INDEX_SRC.indexOf('flow-outbox-banner') === -1,
            'класс/блок баннера удалён');
        assertTrue(INDEX_SRC.indexOf('_outboxBannerText: function') === -1,
            'определение _outboxBannerText удалено');
        assertTrue(INDEX_SRC.indexOf('this._outboxBannerText(') === -1,
            'вызовы _outboxBannerText удалены');
        assertTrue(INDEX_SRC.indexOf('не отправлены — отправятся на сервер') === -1,
            'текст баннера не рендерится');
    });

    test('CSS: .flow-summary-val-pending — жёлто-оранжевый, обе темы', () => {
        const i = INDEX_SRC.indexOf('.flow-summary-val.flow-summary-val-pending {');
        assertTrue(i !== -1, 'CSS-правило pending есть');
        const css = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
        assertEqual(css.trim(), '.flow-summary-val.flow-summary-val-pending {\n        color: #f5a623;\n    }',
            'тёмная тема — жёлто-оранжевый #f5a623, только цвет');
        const l = INDEX_SRC.indexOf('[data-theme="light"] .flow-summary-val.flow-summary-val-pending');
        assertTrue(l !== -1, 'светлая тема есть');
        assertTrue(INDEX_SRC.slice(l, INDEX_SRC.indexOf('}', l) + 1).indexOf('#c96e00') !== -1,
            'светлая тема — тёмно-янтарный #c96e00');
    });

    test('CSS: pending НЕ меняет размер/вес шрифта (только цвет)', () => {
        const i = INDEX_SRC.indexOf('.flow-summary-val.flow-summary-val-pending {');
        const css = INDEX_SRC.slice(i, INDEX_SRC.indexOf('}', i) + 1);
        assertTrue(css.indexOf('font-size') === -1 && css.indexOf('font-weight') === -1,
            'размер/вес не тронуты (в отличие от красного due 18px/800)');
    });

    test('renderList: pendingIds собирается из outbox (id строкой, пустые пропущены)', () => {
        const rl = extractMethod(INDEX_SRC, 'renderList');
        assertTrue(rl.indexOf('var pendingIds = {};') !== -1, 'инициализация множества');
        assertTrue(rl.indexOf('this._outboxLoad()') !== -1, 'чтение outbox');
        assertTrue(rl.indexOf('pendingIds[String(pid)] = true;') !== -1,
            'id нормализуется String() (число/строка — один расходомер)');
        assertTrue(rl.indexOf("pid !== undefined && pid !== null && pid !== ''") !== -1,
            'записи без id пропускаются');
    });

    test('renderList: приоритет — pending РАНЬШЕ красного due', () => {
        const rl = extractMethod(INDEX_SRC, 'renderList');
        const pend = rl.indexOf("if (pendingIds[String(m.id)]) valCls += ' flow-summary-val-pending';");
        const due = rl.indexOf("else if (this._isOverdue(m, null)) valCls += ' flow-summary-val-due';");
        assertTrue(pend !== -1 && due !== -1, 'обе ветки классов на месте');
        assertTrue(pend < due, 'недоставленное (жёлто-оранжевый) важнее «пора вводить»');
    });

    test('Перерендер: renderList после _outboxAdd в обеих ветках ввода', () => {
        // суточный ввод: _outboxAdd({kind:'day'...}) → renderList
        const day = extractMethod(INDEX_SRC, 'submitInput');
        const addDay = day.indexOf("kind: 'day',");
        const rlDay = day.indexOf('this.renderList();', addDay);
        assertTrue(addDay !== -1 && rlDay !== -1,
            'суточный ввод: renderList после записи в outbox');
        // ввод за период: _outboxAdd({kind:'period'...}) → renderList
        const per = extractMethod(INDEX_SRC, '_submitPeriodEntry');
        const addPer = per.indexOf("kind: 'period',");
        const rlPer = per.indexOf('this.renderList();', addPer);
        assertTrue(addPer !== -1 && rlPer !== -1,
            'ввод за период: renderList после записи в outbox');
    });

    test('Перерендер: _flushOutbox.finish() обновляет цвета после доставки', () => {
        const m = extractMethod(INDEX_SRC, '_flushOutbox');
        const fin = m.indexOf('var finish = function(sent) {');
        const rl = m.indexOf('self.renderList();', fin);
        assertTrue(fin !== -1 && rl !== -1,
            'доставка/дедуп-вычистка → renderList (жёлто-оранжевый → зелёный)');
    });

    test('_isOverdue: регэкспы распознавания периодов', () => {
        const m = extractMethod(INDEX_SRC, '_isOverdue');
        assertTrue(m.indexOf('/недел|еженед/.test(period)') !== -1,
            'недельная ветка: недел|еженед');
        assertTrue(m.indexOf('/месяц|месяч|ежемес/.test(period)') !== -1,
            'месячная ветка: месяц|месяч|ежемес');
    });

    test('Доставка success → load(): путь возврата зелёного (не сломан)', () => {
        const m = extractMethod(INDEX_SRC, '_sendUpdateReading');
        assertTrue(m.indexOf('self._outboxRemove(outboxCid);') !== -1,
            'успех — запись из outbox удалена');
        assertTrue(m.indexOf('self.load();') !== -1,
            'load() перезагружает список (renderList с обычными цветами)');
    });
});

// ============================================================
// B. VM — _isOverdue: календарная неделя/месяц (Task 357 + 367)
// ============================================================
let Mixin = null;
try {
    const parts = ['_isOverdue', '_parseMdy', '_dayKey', '_mondayOf']
        .map(n => extractMethod(INDEX_SRC, n)).filter(Boolean);
    if (parts.length === 4) {
        const ctx = {};
        vm.createContext(ctx);
        vm.runInContext('var Mixin = { ' + parts.join(',') + ' };', ctx);
        Mixin = ctx.Mixin;
    }
} catch (e) { /* ниже упадут с причиной */ }

describe('Task 367 — VM: методы извлечены', () => {
    test('Mixin собран (4 метода FlowmeterData)', () => {
        assertTrue(Mixin !== null && typeof Mixin._isOverdue === 'function',
            '_isOverdue извлечён из index.html');
    });
});

describe('Task 367 — VM: еженедельные — красный по КАЛЕНДАРНОЙ неделе', () => {

    test('Данные этой недели (ср 9/9, сейчас чт 9/10) — ЗЕЛЁНЫЙ', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 10, 12, 0)),
            'та же неделя пн–вс');
    });

    test('Данные прошлой недели (ср 9/9, сейчас пн 9/14) — КРАСНЫЙ', () => {
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/9/2026' }, new Date(2026, 8, 14, 12, 0)),
            'неделя данных прошла');
    });

    test('Граница: вс 23:59 — ещё зелёный, пн 00:00 — уже красный', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/7/2026' }, new Date(2026, 8, 13, 23, 59)),
            'воскресенье — та же неделя');
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: '9/13/2026' }, new Date(2026, 8, 14, 0, 30)),
            'понедельник новой недели');
    });

    test('Сокращение «Еженед.» — недельная ветка (не суточная)', () => {
        assertFalse(Mixin._isOverdue({ period: 'Еженед.', dateCurr: '9/9/2026' }, new Date(2026, 8, 10, 12, 0)),
            'та же неделя — зелёный');
        assertTrue(Mixin._isOverdue({ period: 'Еженед.', dateCurr: '9/9/2026' }, new Date(2026, 8, 14, 12, 0)),
            'прошлая неделя — красный');
    });

    test('«1 раз в неделю» — недельная ветка', () => {
        assertTrue(Mixin._isOverdue({ period: '1 раз в неделю', dateCurr: '9/9/2026' }, new Date(2026, 8, 14, 12, 0)),
            'прошлая неделя — красный');
    });

    test('Нет данных — красный (недельный)', () => {
        assertTrue(Mixin._isOverdue({ period: 'Еженедельно', dateCurr: null }, new Date(2026, 8, 10, 12, 0)),
            'данных нет — пора вводить');
    });
});

describe('Task 367 — VM: ежемесячные — красный по КАЛЕНДАРНОМУ месяцу', () => {

    test('Данные этого месяца — ЗЕЛЁНЫЙ', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '9/5/2026' }, new Date(2026, 8, 16, 10, 0)),
            'тот же месяц');
    });

    test('Данные прошлого месяца — КРАСНЫЙ', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '8/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            'месяц данных прошёл');
    });

    test('Граница: 30 сент 23:59 — зелёный, 1 окт 00:00 — красный', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '9/1/2026' }, new Date(2026, 8, 30, 23, 59)),
            'ещё сентябрь');
        assertTrue(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '9/30/2026' }, new Date(2026, 9, 1, 0, 30)),
            'наступил октябрь');
    });

    test('Годовой переход: данные дек 2026, сейчас янв 2027 — красный', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежемесячно', dateCurr: '12/15/2026' }, new Date(2027, 0, 10, 10, 0)),
            'месяц прошёл через границу года');
    });

    test('Сокращение «Ежемес.» и «раз в месяц» — месячная ветка', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежемес.', dateCurr: '8/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            '«Ежемес.» — прошлый месяц красный');
        assertTrue(Mixin._isOverdue({ period: 'раз в месяц', dateCurr: '8/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            '«раз в месяц» — прошлый месяц красный');
        assertFalse(Mixin._isOverdue({ period: 'раз в месяц', dateCurr: '9/20/2026' }, new Date(2026, 8, 16, 10, 0)),
            '«раз в месяц» — тот же месяц зелёный');
    });
});

describe('Task 367 — VM: суточная логика (Task 365) не сломана', () => {

    test('Вчерашние данные сегодня в 7:00 — зелёный', () => {
        assertFalse(Mixin._isOverdue({ period: 'Ежедневно', dateCurr: '9/13/2026' }, new Date(2026, 8, 14, 7, 0)),
            'красный с 6:00 НОВЫХ суток за сутками данных');
    });

    test('Позавчерашние данные сегодня в 7:00 — красный', () => {
        assertTrue(Mixin._isOverdue({ period: 'Ежедневно', dateCurr: '9/12/2026' }, new Date(2026, 8, 14, 7, 0)),
            'данные старше предыдущих суток цикла');
    });

    test('Неизвестный период — суточная ветка (как раньше)', () => {
        assertTrue(Mixin._isOverdue({ period: '', dateCurr: '9/12/2026' }, new Date(2026, 8, 14, 7, 0)),
            'пустой период — суточные правила');
    });
});

// ============================================================
// C. SW
// ============================================================
describe('Task 367 — SW кэш', () => {

    test('SW: CACHE_VERSION = kipia-test-v596', () => {
        assertTrue(SW_SRC.indexOf("CACHE_VERSION = 'kipia-test-v596'") !== -1,
            'версия кэша поднята до v596');
    });

    test('SW: нет v595 (старая) и нет v597 (двойной бамп)', () => {
        assertTrue(SW_SRC.indexOf('kipia-test-v595') === -1, 'старая версия не осталась');
        assertTrue(SW_SRC.indexOf('kipia-test-v597') === -1, 'двойного бампа не было');
    });
});
