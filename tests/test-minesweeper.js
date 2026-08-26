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

const { test, describe, assertEqual, assertTrue } = require('./test-helpers.js');
const { extractFunctions, setMockViewport } = require('./extract-functions.js');
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

// Восстановление дефолтного вьюпорта мока (375) — на случай,
// если другие тестовые файлы будут читать window.innerWidth
describe('Восстановление мок-вьюпорта после тестов Сапёра', () => {
    test('вьюпорт возвращён к 375px', () => {
        setMockViewport(375);
        assertEqual(fns.msCalcCellSize(), 32, 'дефолтное состояние мока восстановлено');
    });
});
