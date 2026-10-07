// tests/test-task473.js
// Task 473 — заявка пользователя: «В разделе Графики КИП ИОС, на
// вкладке Приборы, сделай что бы на графике "Количество приборов
// по графику ППР по месяцам на 2026 год" отображалось количество
// приборов на каждый месяц на диаграмме, и проверь сама диаграмма
// не отображает зрительно количество приборов по месяцам "К
// Калибровка П Поверка ТО Тех. обслуж.".»
//
// РЕШЕНИЕ (charts-desktop.js — модуль графиков, только десктоп
// Electron; данные ППР не менялись — только отрисовка):
//   (а) КОРЕНЬ «не отображает зрительно»: у .ppr-bars-row было
//       align-items:flex-end — ячейки НЕ растягивались на высоту
//       ряда, height:% столбца разрешался против auto-высоты ячейки
//       и схлопывался в min-height:2px — ВСЕ столбцы всех серий
//       были зрительно невидимы (2px), подтверждено замером в
//       Chromium (браузер-чек: было 2px из 165px). Теперь
//       align-items:stretch — высота ячейки определена, столбцы
//       рисуются по значению; низ столбца прижат align-items:
//       flex-end самой ячейки .ppr-bar-cell;
//   (б) значение над КАЖДЫМ столбцом (порог heightPct > 8 убран —
//       из-за него были видны числа только 14 месяцев из 36) —
//       количество приборов на каждый месяц видно на диаграмме;
//   (в) нулевые месяцы — подпись «0» у основания (.ppr-bar-val-zero);
//   (г) ВСПОМОГАТЕЛЬНАЯ ПРАВАЯ ОСЬ: серии с максимумом <= 25% от
//       общего (К 48, П 15 при ТО 500) масштабируются по правой оси
//       (niceMax(48) = 50) — столбцы зрительно различимы по месяцам;
//       правая ось с метками 50…0; легенда малых серий помечена
//       «(правая ось)»; столбец помечен data-scale primary/secondary;
//   (д) CSS: .ppr-chart-body padding-top 4→16px (запас под подписи),
//       .ppr-bar-cell position:relative (якорь «0»), .ppr-y-axis-right,
//       .ppr-legend-axis;
//   SW: kipia-test-v706.
//   АДАПТАЦИЯ (прецедент Task 463/468/470/471): test-task471.js и
//   test-task472.js — окно шапки версий sw.js 900 → 1020 (комментарий
//   Task 473 отодвинул начало комментария Task 471 до ~986 символов).
//
// Запуск: через tests/run-all.js (require './test-task473.js').

const fs = require('fs');
const path = require('path');
const { test, describe, assertTrue, assertFalse, assertEqual } = require('./test-helpers.js');

const ROOT = path.join(__dirname, '..');
const CHARTS_SRC = fs.readFileSync(path.join(ROOT, 'charts-desktop.js'), 'utf8');
const SW_SRC = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');

// Извлечь метод объекта по имени («name: function(» … парные скобки)
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

// Оживить извлечённый метод (eval объектного литерала — как в test-task464)
function reviveMethod(src, name) {
    const m = extractMethod(src, name);
    if (!m) return null;
    // eslint-disable-next-line no-eval
    return eval('({' + m + '})')[name];
}

// Данные ППР «Приборы» — извлечь из исходника, чтобы тест следовал файлу
function extractPprDevices() {
    const a = CHARTS_SRC.indexOf('_PPR_DEVICES: {');
    const b = CHARTS_SRC.indexOf('_PPR_LOCKOUTS', a);
    assertTrue(a !== -1 && b !== -1, '_PPR_DEVICES найден в charts-desktop.js');
    const block = CHARTS_SRC.slice(a, b);
    const title = block.match(/title:\s*'([^']+)'/);
    const items = [...block.matchAll(/\{ name: '([^']+)', code: '([^']+)', color: '([^']+)', values: \[([^\]]*)\] \}/g)];
    assertTrue(!!title, 'title ППР найден');
    assertEqual(items.length, 3, 'три серии ППР (К/П/ТО)');
    return {
        title: title[1],
        series: items.map(m => ({
            name: m[1], code: m[2], color: m[3],
            values: m[4].split(',').map(v => parseInt(v, 10))
        }))
    };
}

// Хост с живыми методами отрисовки (та же арифметика, что в браузере)
function makeHost() {
    return {
        _renderPPRChart: reviveMethod(CHARTS_SRC, '_renderPPRChart'),
        _niceMax: reviveMethod(CHARTS_SRC, '_niceMax'),
        _escHtml: reviveMethod(CHARTS_SRC, '_escHtml'),
        _MONTHS_ROMAN: ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
    };
}

function countOccurrences(haystack, needle) {
    return haystack.split(needle).length - 1;
}

// ==========================================================================
// 1. _niceMax — красивые максимумы осей (первичная и вспомогательная)
// ==========================================================================
describe('Task 473: _niceMax — масштабы осей', () => {
    const host = makeHost();

    test('niceMax(500) = 500 — ось ТО (первичная)', () => {
        assertEqual(host._niceMax(500), 500);
    });

    test('niceMax(48) = 50 — вспомогательная ось К/П', () => {
        assertEqual(host._niceMax(48), 50);
    });

    test('niceMax(15) = 20', () => {
        assertEqual(host._niceMax(15), 20);
    });

    test('niceMax(210) = 500 — ось блокировок (первичная)', () => {
        assertEqual(host._niceMax(210), 500);
    });

    test('niceMax(0) = 10 — защита от нуля', () => {
        assertEqual(host._niceMax(0), 10);
    });
});

// ==========================================================================
// 2. Функциональный рендер: подписи на каждом месяце + правая ось
// ==========================================================================
describe('Task 473: ППР «Приборы» — рендер HTML', () => {
    const host = makeHost();
    const data = extractPprDevices();
    const html = host._renderPPRChart(data);
    const K = data.series[0], P = data.series[1], TO = data.series[2];

    test('данные ППР не изменились: заголовок', () => {
        assertEqual(data.title, 'Количество приборов по графику ППР по месяцам на 2026 год');
    });

    test('данные ППР не изменились: серии К/П/ТО и значения', () => {
        assertEqual(K.name, 'Калибровка'); assertEqual(K.code, 'К');
        assertEqual(P.name, 'Поверка'); assertEqual(P.code, 'П');
        assertEqual(TO.name, 'Тех. обслуж.'); assertEqual(TO.code, 'ТО');
        assertEqual(K.values.length, 12); assertEqual(P.values.length, 12);
        assertEqual(TO.values.length, 12);
        assertEqual(Math.max.apply(null, K.values), 48);
        assertEqual(Math.max.apply(null, P.values), 15);
        assertEqual(Math.max.apply(null, TO.values), 500);
        // единственный нулевой месяц — Май у Поверки
        const zeros = [];
        for (let m = 0; m < 12; m++)
            for (let s = 0; s < 3; s++)
                if (data.series[s].values[m] === 0) zeros.push([s, m]);
        assertEqual(zeros.length, 1, 'ровно один нулевой месяц (Май, П)');
        assertEqual(zeros[0][0], 1); assertEqual(zeros[0][1], 4);
    });

    test('значение над КАЖДЫМ ненулевым столбцом: 35 подписей (12 К + 11 П + 12 ТО)', () => {
        assertEqual(countOccurrences(html, 'class="ppr-bar-val"'), 35);
    });

    test('старый порог «показывать если heightPct > 8» удалён', () => {
        const fn = extractMethod(CHARTS_SRC, '_renderPPRChart');
        assertTrue(fn.indexOf('heightPct > 8') === -1,
            'условие heightPct > 8 не должно остаться');
    });

    test('нулевой месяц — подпись «0» у основания (.ppr-bar-val-zero)', () => {
        assertEqual(countOccurrences(html, 'class="ppr-bar-val-zero"'), 1);
        assertTrue(html.indexOf('>0</span>') !== -1, 'текст «0» присутствует');
    });

    test('12 групп месяцев с римскими метками I–XII', () => {
        assertEqual(countOccurrences(html, 'class="ppr-month-label"'), 12);
        const romans = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'];
        for (const r of romans) {
            assertTrue(html.indexOf('>' + r + '</div>') !== -1, 'месяц ' + r);
        }
    });

    test('правая вспомогательная ось отрисована (.ppr-y-axis-right)', () => {
        assertEqual(countOccurrences(html, 'ppr-y-axis-right'), 1);
    });

    test('правая ось: метки 50/40/30/20/10 — по одной', () => {
        // левая ось 500…0 сотнями, правая 50…0 десятками
        for (const v of ['50','40','30','20','10']) {
            assertEqual(countOccurrences(html, '>' + v + '</div>'), 1, 'метка ' + v);
        }
    });

    test('левая ось: метки 500/400/300/200/100 — по одной', () => {
        for (const v of ['500','400','300','200','100']) {
            assertEqual(countOccurrences(html, '>' + v + '</div>'), 1, 'метка ' + v);
        }
    });

    test('столбцы малых серий помечены data-scale="secondary" (23 шт: 12 К + 11 П)', () => {
        assertEqual(countOccurrences(html, 'data-scale="secondary"'), 23);
    });

    test('столбцы большой серии помечены data-scale="primary" (12 шт: ТО)', () => {
        assertEqual(countOccurrences(html, 'data-scale="primary"'), 12);
    });

    test('масштаб малых серий по правой оси: К 48 → 96% высоты', () => {
        assertTrue(html.indexOf('height:' + (48 / 50) * 100 + '%') !== -1,
            'height:96% (48 из 50) присутствует');
    });

    test('масштаб малых серий: П 15 → 30% высоты (раньше было 3% — не видно)', () => {
        assertTrue(html.indexOf('height:' + (15 / 50) * 100 + '%') !== -1,
            'height:30% (15 из 50) присутствует');
    });

    test('масштаб большой серии: ТО 500 → 100% высоты (левая ось)', () => {
        assertTrue(html.indexOf('height:' + (500 / 500) * 100 + '%') !== -1,
            'height:100% (500 из 500) присутствует');
    });

    test('масштаб малых серий: К 13 → 26% (раньше 2.6% — не видно)', () => {
        assertTrue(html.indexOf('height:' + (13 / 50) * 100 + '%') !== -1,
            'height:26% (13 из 50) присутствует');
    });

    test('легенда: малые серии помечены «(правая ось)» — 2 подсказки', () => {
        assertEqual(countOccurrences(html, 'class="ppr-legend-axis"'), 2);
        assertTrue(html.indexOf('(правая ось)') !== -1, 'текст подсказки есть');
    });

    test('легенда: полные подписи К Калибровка / П Поверка / ТО Тех. обслуж.', () => {
        assertTrue(html.indexOf('>К</span>') !== -1 && html.indexOf('Калибровка') !== -1);
        assertTrue(html.indexOf('>П</span>') !== -1 && html.indexOf('Поверка') !== -1);
        assertTrue(html.indexOf('>ТО</span>') !== -1 && html.indexOf('Тех. обслуж.') !== -1);
    });

    test('тултип малой серии подсказывает ось: «Калибровка (правая ось): 33»', () => {
        assertTrue(html.indexOf('Калибровка (правая ось): 33') !== -1);
    });

    test('строка итогов «Итого:» по сериям сохранена', () => {
        assertTrue(html.indexOf('Итого:') !== -1);
        const sum = arr => arr.reduce((a, b) => a + b, 0);
        assertTrue(html.indexOf('>' + sum(K.values) + '<') !== -1, 'итог К = ' + sum(K.values));
        assertTrue(html.indexOf('>' + sum(P.values) + '<') !== -1, 'итог П = ' + sum(P.values));
        assertTrue(html.indexOf('>' + sum(TO.values) + '<') !== -1, 'итог ТО = ' + sum(TO.values));
    });
});

// ==========================================================================
// 3. Регресс: ППР «Блокировки» — обе серии крупные, правой оси быть НЕ должно
// ==========================================================================
describe('Task 473: ППР «Блокировки» — без вспомогательной оси', () => {
    const host = makeHost();
    const html = host._renderPPRChart({
        title: 'График ППР — Схемы на 2026 год',
        series: [
            { name: 'Кан. ремонт', code: 'Кр', color: '#4a90d9', values: [58, 49, 26, 31, 13, 38, 33, 34, 74, 23, 49, 98] },
            { name: 'Тех. обслуж.', code: 'ТО', color: '#5ab870', values: [87, 96, 210, 114, 132, 198, 112, 111, 162, 122, 96, 138] }
        ]
    });

    test('правой оси нет (Кр 98 > 25% от ТО 210)', () => {
        assertEqual(countOccurrences(html, 'ppr-y-axis-right'), 0);
    });

    test('подсказок «(правая ось)» в легенде нет', () => {
        assertEqual(countOccurrences(html, 'class="ppr-legend-axis"'), 0);
    });

    test('единая шкала 0–500: Кр 98 → 19.6%, ТО 210 → 42%', () => {
        assertTrue(html.indexOf('height:' + (98 / 500) * 100 + '%') !== -1, 'Кр 98 из 500');
        assertTrue(html.indexOf('height:' + (210 / 500) * 100 + '%') !== -1, 'ТО 210 из 500');
    });

    test('значения над всеми 24 столбцами (12 Кр + 12 ТО)', () => {
        assertEqual(countOccurrences(html, 'class="ppr-bar-val"'), 24);
    });
});

// ==========================================================================
// 4. CSS модуля: запас под подписи, якорь «0», стили правой оси
// ==========================================================================
describe('Task 473: CSS графиков', () => {

    test('КОРЕНЬ «не отображает зрительно»: .ppr-bars-row align-items:stretch', () => {
        // Было align-items:flex-end — ячейки не растягивались на высоту
        // ряда, height:% столбца разрешался против auto-высоты ячейки и
        // схлопывался в min-height:2px: ВСЕ столбцы всех серий были
        // зрительно невидимы (замер Chromium: 2px из 165px) — это и
        // значила фраза заявки «сама диаграмма не отображает зрительно
        // количество приборов по месяцам».
        const m = CHARTS_SRC.match(/\.ppr-bars-row \{[^}]*\}/);
        assertTrue(!!m && /align-items:\s*stretch/.test(m[0]),
            'ячейки растянуты на всю высоту ряда — высота столбца определена');
        assertTrue(!!m && !/align-items:\s*flex-end/.test(m[0]),
            'align-items:flex-end убран из .ppr-bars-row');
    });

    test('низ столбца прижат ячейкой (.ppr-bar-cell align-items:flex-end)', () => {
        const m = CHARTS_SRC.match(/\.ppr-bar-cell \{[^}]*\}/);
        assertTrue(!!m && /align-items:\s*flex-end/.test(m[0]),
            'столбец прижат к основанию ячейки');
    });
    test('запас под подписи: .ppr-chart-body padding-top 16px', () => {
        assertTrue(CHARTS_SRC.indexOf('padding: 16px 14px 12px;') !== -1,
            'было 4px — подписи над высокими столбцами упирались в шапку');
    });

    test('.ppr-bar-cell position:relative — якорь подписи «0»', () => {
        const m = CHARTS_SRC.match(/\.ppr-bar-cell \{[^}]*\}/);
        assertTrue(!!m && /position:\s*relative/.test(m[0]), 'правило с position:relative');
    });

    test('стиль подписи нуля .ppr-bar-val-zero у основания', () => {
        const m = CHARTS_SRC.match(/\.ppr-bar-val-zero \{[^}]*\}/);
        assertTrue(!!m && /bottom:\s*1px/.test(m[0]), 'привязка к основанию');
    });

    test('стиль правой оси .ppr-y-axis-right (отступ слева, метки слева)', () => {
        const m = CHARTS_SRC.match(/\.ppr-y-axis-right \{[^}]*\}/);
        assertTrue(!!m && /padding-left:\s*6px/.test(m[0]), 'правило есть');
        assertTrue(CHARTS_SRC.indexOf('.ppr-y-axis-right .ppr-y-label') !== -1,
            'выравнивание меток правой оси');
    });

    test('стиль подсказки легенды .ppr-legend-axis', () => {
        const m = CHARTS_SRC.match(/\.ppr-legend-axis \{[^}]*\}/);
        assertTrue(!!m, 'правило есть');
    });

    test('минимальная высота столбца сохранена (min-height: 2px)', () => {
        assertTrue(CHARTS_SRC.indexOf('min-height: 2px;') !== -1);
    });
});

// ==========================================================================
// 5. Заголовок модуля и Service Worker
// ==========================================================================
describe('Task 473: шапка charts-desktop.js и SW', () => {

    test('шапка charts-desktop.js описывает Task 473', () => {
        assertTrue(CHARTS_SRC.indexOf('Task 473') !== -1, 'маркер задачи');
        assertTrue(CHARTS_SRC.indexOf('ВСПОМОГА') !== -1 || CHARTS_SRC.indexOf('правая ось') !== -1,
            'упоминание вспомогательной оси');
    });

    test('модуль по-прежнему только десктоп (заголовок Electron)', () => {
        assertTrue(CHARTS_SRC.indexOf('ТОЛЬКО десктопного приложения') !== -1,
            ' назначение модуля не изменилось');
    });

    test('CACHE_VERSION = kipia-test-v706', () => {
        assertTrue(SW_SRC.indexOf("const CACHE_VERSION = 'kipia-test-v706';") !== -1,
            'текущая версия v689');
    });

    test('v688 в sw.js отсутствует', () => {
        assertTrue(SW_SRC.indexOf('kipia-test-v696') === -1,
            'версии до Task 473 нет');
    });

    test('v690 в sw.js отсутствует (лишний инкремент не сделан)', () => {
        assertTrue(SW_SRC.indexOf('kipia-test-v707') === -1,
            'версия после Task 473 не существует');
    });

    test('комментарий Task 473 о составе правок в sw.js', () => {
        assertTrue(SW_SRC.indexOf('Task 473') !== -1, 'маркер задачи');
        assertTrue(SW_SRC.indexOf('правая ось') !== -1 || SW_SRC.indexOf('ППР') !== -1,
            'упоминание графика ППР');
    });

    test('charts-desktop.js в ASSETS сервис-воркера (обновление кэша)', () => {
        assertTrue(SW_SRC.indexOf('./charts-desktop.js') !== -1,
            'файл графика перекешируется при бампе');
    });
});

console.log('test-task473: все describes зарегистрированы');
