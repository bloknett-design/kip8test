// Тесты расчёта размера клетки «Сапёра» (Task 191):
//   msCalcCellSize — адаптация игрового поля под десктоп.
//
// До Task 191 размер клетки считался от window.innerWidth без
// ограничения сверху: на десктопе 1920px клетка была ~206px и поле
// растягивалось почти на весь экран. После Task 191 на десктопе
// (>= 1024px) клетка ограничена 40px, а touch-спейсер (36px)
// не вычитается из доступной ширины.
//
// Формула: availW = baseW - containerPad(32) - boardPad - scrollSpace;
//          cell = floor((availW - (cols-1)*gap) / cols); cap 40 на десктопе.

const { test, describe, assertEqual, assertTrue, assertFalse } = require('./test-helpers.js');
const { extractFunctions, setMockViewport, clearMockStorage, getMockElement, setMockStorageItem, getMockStorageKeys } = require('./extract-functions.js');
const fns = extractFunctions();

describe('msCalcCellSize — мобильный лейаут (< 1024px, поведение не менялось)', () => {

    test('375px (iPhone SE): 32px', () => {
        setMockViewport(375);
        // boardPad=8, gap=1, scroll=36: (375-32-8-36-8)/9 = 32.33 → 32
        assertEqual(fns.msCalcCellSize(), 32, 'клетка на 375px должна быть 32px');
    });

    test('390px (iPhone 14): 34px', () => {
        setMockViewport(390);
        // (390-32-8-36-8)/9 = 34 → 34
        assertEqual(fns.msCalcCellSize(), 34, 'клетка на 390px должна быть 34px');
    });

    test('768px (планшет, мобильный лейаут): без ограничения', () => {
        setMockViewport(768);
        // boardPad=16, gap=2, scroll=36: (768-32-16-36-16)/9 = 74.2 → 74
        // ограничение 40px НЕ применяется ниже 1024px (Task 191 — только десктоп)
        assertEqual(fns.msCalcCellSize(), 74, 'на планшете мобильное поведение сохранено');
    });

    test('Минимальный размер клетки 20px на очень узком экране', () => {
        setMockViewport(280);
        // (280-32-8-36-8)/9 = 21.7 → 21 — выше минимума
        assertTrue(fns.msCalcCellSize() >= 20, 'клетка не должна быть меньше 20px');
    });
});

describe('msCalcCellSize — десктоп (>= 1024px, Task 191: ограничение 40px)', () => {

    test('1024px: клетка 40px (было ~106px)', () => {
        setMockViewport(1024);
        // boardPad=16, gap=2, scroll=0: (1024-32-16-16)/9 = 106.6 → cap 40
        assertEqual(fns.msCalcCellSize(), 40, 'на десктопе клетка ограничена 40px');
    });

    test('1440px: клетка 40px (было ~148px)', () => {
        setMockViewport(1440);
        assertEqual(fns.msCalcCellSize(), 40, 'на десктопе клетка ограничена 40px');
    });

    test('1920px: клетка 40px (было ~206px)', () => {
        setMockViewport(1920);
        assertEqual(fns.msCalcCellSize(), 40, 'поле не должно растягиваться на весь экран');
    });

    test('2560px (2K): клетка 40px', () => {
        setMockViewport(2560);
        assertEqual(fns.msCalcCellSize(), 40, 'на больших мониторах поле остаётся компактным');
    });

    test('Ширина поля на десктопе укладывается в контейнер 520px', () => {
        setMockViewport(1920);
        const cell = fns.msCalcCellSize();
        // доска = 9 клеток + 8 gap по 2px + padding 8px*2 + border 1px*2
        const boardW = 9 * cell + 8 * 2 + 8 * 2 + 2;
        assertTrue(boardW <= 520, 'поле ' + boardW + 'px должно влезать в контейнер 520px (max-width из Task 191)');
    });

    test('Все сложности (9 колонок) имеют одинаковую ширину поля на десктопе', () => {
        setMockViewport(1920);
        // easy 9x9, medium 9x16, hard 9x28 — все 9 колонок,
        // значит ширина клетки и поля одинакова
        const cell = fns.msCalcCellSize();
        assertEqual(cell, 40, 'ширина клетки не зависит от количества строк');
    });
});

// Task 192: горизонтальные игровые поля на десктопе + счёт достижений
// (три последних результата). На десктопе (>= 1024px) medium/hard
// разворачиваются горизонтально: 9x16 → 16x9, 9x28 → 28x9; на мобильном
// ориентация прежняя — вертикальная. Счёт достижений хранит максимум
// 3 последних результата в localStorage (ключ msRecentResults).

describe('msEffectiveDims — ориентация поля (Task 192)', () => {

    test('мобильный 375px: поля вертикальные, как раньше', () => {
        setMockViewport(375);
        assertEqual(JSON.stringify(fns.msEffectiveDims('easy')),
            JSON.stringify({ cols: 9, rows: 9, mines: 10 }), 'easy 9x9 без изменений');
        assertEqual(JSON.stringify(fns.msEffectiveDims('medium')),
            JSON.stringify({ cols: 9, rows: 16, mines: 25 }), 'medium вертикальный 9x16');
        assertEqual(JSON.stringify(fns.msEffectiveDims('hard')),
            JSON.stringify({ cols: 9, rows: 28, mines: 45 }), 'hard вертикальный 9x28');
    });

    test('десктоп 1440px: medium/hard развёрнуты горизонтально', () => {
        setMockViewport(1440);
        assertEqual(JSON.stringify(fns.msEffectiveDims('easy')),
            JSON.stringify({ cols: 9, rows: 9, mines: 10 }), 'easy остаётся квадратом');
        assertEqual(JSON.stringify(fns.msEffectiveDims('medium')),
            JSON.stringify({ cols: 16, rows: 9, mines: 25 }), 'medium горизонтальный 16x9');
        assertEqual(JSON.stringify(fns.msEffectiveDims('hard')),
            JSON.stringify({ cols: 28, rows: 9, mines: 45 }), 'hard горизонтальный 28x9');
    });

    test('граница 1024px: уже десктоп — горизонтальная ориентация', () => {
        setMockViewport(1024);
        assertEqual(JSON.stringify(fns.msEffectiveDims('medium')),
            JSON.stringify({ cols: 16, rows: 9, mines: 25 }), 'на 1024px поле горизонтальное');
    });

    test('неизвестная сложность → fallback на easy', () => {
        setMockViewport(1920);
        assertEqual(JSON.stringify(fns.msEffectiveDims('нет такой')),
            JSON.stringify({ cols: 9, rows: 9, mines: 10 }), 'fallback на easy 9x9');
    });
});

describe('msDiffLabel — подписи сложностей в селекторе (Task 192)', () => {

    test('мобильный: 9x9 / 9x16 / 9x28', () => {
        setMockViewport(375);
        assertEqual(fns.msDiffLabel('easy'), '9x9', 'подпись easy на мобильном');
        assertEqual(fns.msDiffLabel('medium'), '9x16', 'подпись medium на мобильном');
        assertEqual(fns.msDiffLabel('hard'), '9x28', 'подпись hard на мобильном');
    });

    test('десктоп: 9x9 / 16x9 / 28x9 — ширина впереди', () => {
        setMockViewport(1920);
        assertEqual(fns.msDiffLabel('easy'), '9x9', 'подпись easy на десктопе');
        assertEqual(fns.msDiffLabel('medium'), '16x9', 'подпись medium на десктопе');
        assertEqual(fns.msDiffLabel('hard'), '28x9', 'подпись hard на десктопе');
    });

    test('неизвестная сложность → пустая подпись', () => {
        setMockViewport(1920);
        assertEqual(fns.msDiffLabel('unknown'), '', 'неизвестная сложность даёт пустую строку');
    });
});

describe('msCalcCellSize(cols) — горизонтальное поле на десктопе (Task 192)', () => {

    test('1920px, 28 колонок (hard 28x9): клетка 40px', () => {
        setMockViewport(1920);
        // (1920-32-16-54)/28 = 64.9 → cap 40
        assertEqual(fns.msCalcCellSize(28), 40, 'горизонтальное поле не растягивается на весь экран');
    });

    test('1440px, 28 колонок: клетка 40px', () => {
        setMockViewport(1440);
        assertEqual(fns.msCalcCellSize(28), 40, 'клетка ограничена 40px');
    });

    test('1024px, 28 колонок: клетка 32px, поле влезает без прокрутки', () => {
        setMockViewport(1024);
        // (1024-32-16-54)/28 = 32.9 → 32
        const cell = fns.msCalcCellSize(28);
        assertEqual(cell, 32, 'клетка на минимальном десктопе');
        // доска = 28 клеток + 27 gap по 2px + padding 8px*2 + border 1px*2
        const boardW = 28 * cell + 27 * 2 + 8 * 2 + 2;
        assertTrue(boardW <= 1024 - 32, 'поле ' + boardW + 'px влезает в страницу 1024px без прокрутки');
    });

    test('1024px, 16 колонок (medium 16x9): клетка 40px', () => {
        setMockViewport(1024);
        // (1024-32-16-30)/16 = 59.1 → cap 40
        assertEqual(fns.msCalcCellSize(16), 40, 'medium на минимальном десктопе — клетка 40px');
    });

    test('без аргумента — использует активные msCols (обратная совместимость)', () => {
        setMockViewport(1920);
        assertEqual(fns.msCalcCellSize(), fns.msCalcCellSize(9), 'вызов без аргумента эквивалентен 9 колонкам');
    });
});

describe('Счёт достижений — хранение трёх последних результатов (Task 192)', () => {

    test('Пустой счёт: msLoadResults() возвращает []', () => {
        clearMockStorage();
        assertEqual(fns.msLoadResults().length, 0, 'до первой игры счёт пуст');
    });

    test('Запись победы: won=true, время и сложность сохранены', () => {
        clearMockStorage();
        const res = fns.msRecordResult(true, 45, 'easy');
        assertEqual(res.length, 1, 'после первой партии — один результат');
        assertTrue(res[0].won, 'победа зафиксирована');
        assertEqual(res[0].time, 45, 'время партии сохранено');
        assertEqual(res[0].diff, 'easy', 'сложность сохранена');
    });

    test('Хранятся только три последних: 4-я партия вытесняет 1-ю', () => {
        clearMockStorage();
        fns.msRecordResult(true, 10, 'easy');
        fns.msRecordResult(false, 20, 'medium');
        fns.msRecordResult(true, 30, 'hard');
        fns.msRecordResult(false, 40, 'easy');
        const res = fns.msLoadResults();
        assertEqual(res.length, 3, 'в счёте не больше трёх результатов');
        assertEqual(res[0].time, 20, 'самый старый результат вытеснен');
        assertEqual(res[2].time, 40, 'новейший результат — последний');
    });

    test('Поражение фиксируется со временем взрыва', () => {
        clearMockStorage();
        fns.msRecordResult(false, 7, 'medium');
        const res = fns.msLoadResults();
        assertFalse(res[0].won, 'взрыв зафиксирован как поражение');
        assertEqual(res[0].time, 7, 'время до взрыва сохранено');
    });

    test('Мусор в хранилище не ломает счёт (возврат к пустому)', () => {
        clearMockStorage();
        // пишем валидные данные, чтобы узнать фактический ключ
        // (обёртка isolateLocalStorage добавляет префикс к 'msRecentResults')
        fns.msSaveResults([{ won: true, time: 1, diff: 'easy', ts: 1 }]);
        const keys = getMockStorageKeys();
        assertEqual(keys.length, 1, 'в хранилище один ключ счёта');
        // заменяем содержимое на мусор — чтение не должно падать
        setMockStorageItem(keys[0], '{{{не json');
        assertEqual(fns.msLoadResults().length, 0, 'повреждённое хранилище → пустой счёт без исключений');
    });

    test('msRenderAchievements: 3 слота — победа, поражение, пусто + счёт 1/2', () => {
        clearMockStorage();
        setMockViewport(1920); // десктопные подписи 16x9
        fns.msRecordResult(true, 45, 'easy');
        fns.msRecordResult(false, 12, 'medium');
        fns.msRenderAchievements();
        const row = getMockElement('msAchRow');
        assertTrue(row !== null, 'мок-элемент msAchRow создан');
        assertTrue(row.innerHTML.indexOf('ms-ach-slot win') !== -1, 'слот победы отрендерен');
        assertTrue(row.innerHTML.indexOf('ms-ach-slot loss') !== -1, 'слот поражения отрендерен');
        assertTrue(row.innerHTML.indexOf('ms-ach-slot empty') !== -1, 'пустой слот отрендерен');
        assertTrue(row.innerHTML.indexOf('16x9') !== -1, 'подпись сложности в текущей ориентации');
        const score = getMockElement('msAchScore');
        assertEqual(score.textContent, '1/2', 'бейдж счёта: 1 победа из 2 партий');
    });

    test('msRenderAchievements: пустой счёт — 3 пустых слота, бейдж скрыт', () => {
        clearMockStorage();
        fns.msRenderAchievements();
        const row = getMockElement('msAchRow');
        assertEqual(row.innerHTML.split('ms-ach-slot empty').length - 1, 3, 'три пустых слота');
        const score = getMockElement('msAchScore');
        assertEqual(score.style.display, 'none', 'бейдж счёта скрыт без партий');
    });
});

// Восстановление дефолтного вьюпорта мока (375) — на случай,
// если другие тестовые файлы будут читать window.innerWidth
describe('Восстановление мок-вьюпорта после тестов Сапёра', () => {
    test('вьюпорт возвращён к 375px', () => {
        setMockViewport(375);
        clearMockStorage(); // Task 192: чистое хранилище для следующих файлов
        assertEqual(fns.msCalcCellSize(), 32, 'дефолтное состояние мока восстановлено');
    });
});
