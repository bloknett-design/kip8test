#!/usr/bin/env node
// scripts/task496-vlm-check.js — VLM-проверка скриншотов Task 496
// (паттерн task495-vlm-check.js; CLI `z-ai vision`).
// Заявка: Enter («Готово») в ППР закрывает клавиатуру, а не
// перескакивает. Клавиатура в статичных кадрах не видна — VLM
// проверяет, что после Enter/ввода панель ППР визуально цела
// (поля, подписи), live-расчёт сработал (значения в полях) и
// дефектов нет.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task496';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a-mobile-dark-after-enter-temp.png',
     'Это скриншот мобильного веб-приложения (тёмная тема, 375px), страница расчёта датчика температуры, сделан СРАЗУ ПОСЛЕ нажатия Enter в поле «Температура (°C)» панели произвольного расчёта. Ответь строго по пунктам: (1) Панель произвольного расчёта с полями «Температура (°C)» и «Сопротивление R(t), Ом» видна и выглядит целой (рамка, подписи, поля на месте)? (2) Есть ли визуальные дефекты (наложения, обрезанные поля, разъехавшаяся вёрстка)? (3) Ниже видна ли вторая панель с полями Диапазон измерения (min/max) и Шаг таблицы?'],
    ['b-mobile-dark-live-calc.png',
     'Это скриншот мобильного веб-приложения (тёмная тема, 375px), страница датчика температуры. В поле «Температура (°C)» панели произвольного расчёта введено 55. Ответь строго по пунктам: (1) В поле «Температура (°C)» видно значение 55? (2) В поле «Сопротивление R(t), Ом» появилось рассчитанное значение (число, НЕ пустое)? (3) Панель выглядит целой, без дефектов вёрстки?'],
    ['c-mobile-dark-tc.png',
     'Это скриншот мобильного веб-приложения (тёмная тема, 375px), страница термопары ТХА (K). В поле «Температура (°C)» введено 300. Ответь строго по пунктам: (1) Заголовок страницы содержит «ТХА (K)» или «термопара»? (2) Панель произвольного расчёта видна: в поле температуры 300, в поле второго значения (мВ) рассчитанное число? (3) Дефектов вёрстки нет?'],
    ['d-mobile-light.png',
     'Это скриншот мобильного веб-приложения (СВЕТЛАЯ тема, 375px), страница датчика температуры. Ответь строго по пунктам: (1) Панель произвольного расчёта (Температура/Сопротивление) читаема: подписи и поля видны на светлом фоне? (2) Панель оформлена как приподнятая карточка (выступ: заметная рамка, лёгкий градиент)? (3) Дефектов вёрстки нет?'],
    ['e-desktop.png',
     'Это скриншот ДЕСКТОПНОЙ версии (1280px, тёмная тема), страница датчика температуры. Ответь строго по пунктам: (1) В левой колонке видна панель произвольного расчёта с полями «Температура (°C)» и «Сопротивление R(t), Ом»? (2) Ниже — панель «Диапазон измерения / Шаг таблицы» и кнопка «Рассчитать»? (3) Дефектов вёрстки нет?']
];

// Ожидание по каждому кадру — оценка «да» на целостность/значения:
//   'intact' — панель цела, значения на месте, дефектов нет.
const EXPECT = {
    'a-mobile-dark-after-enter-temp.png': 'intact',
    'b-mobile-dark-live-calc.png': 'intact',
    'c-mobile-dark-tc.png': 'intact',
    'd-mobile-light.png': 'intact',
    'e-desktop.png': 'intact'
};

// Кэш ответов: повторный прогон не дёргает VLM
const CACHE = path.join(DIR, 'vlm-task496-out.json');
let cache = {};
if (fs.existsSync(CACHE)) cache = JSON.parse(fs.readFileSync(CACHE, 'utf8'));

let pass = 0, fail = 0;
for (const [file, prompt] of shots) {
    if (!fs.existsSync(path.join(DIR, file))) {
        console.log('нет файла ' + file); fail++; continue;
    }
    let txt;
    if (cache[file] !== undefined) {
        txt = cache[file];
        console.log('(из кэша) === ' + file + ' ===');
    } else {
        txt = vision(file, prompt);
        cache[file] = String(txt);
        fs.writeFileSync(CACHE, JSON.stringify(cache, null, 1), 'utf8');
        console.log('=== ' + file + ' ===');
    }
    console.log(String(txt).slice(0, 2400));
    console.log('---');

    // Оценка ПО СМЫСЛУ (урок Task 495: «Да, … нет» — надо понимать
    // отрицание). Построчно: строка-«дефект» — та, где упомянут
    // дефект БЕЗ отрицания («не наблюдается»/«нет»/«без»).
    const s = String(txt).toLowerCase();
    const lines = s.split(/[\n;]+/).filter(x => x.trim());
    let defectClaim = false;
    for (const ln of lines) {
        if (/дефект|наложени|обрез|разъеха|слома|нечитаем|пуст[оы]е?\s+пол/.test(ln) &&
            !/не\s|нет\b|без\s|отсутств|н[её]\s|наблюдается\?\s*нет/.test(ln)) {
            defectClaim = true;
        }
    }
    let ok = false;
    if (EXPECT[file] === 'intact') {
        const yes = (s.match(
            /(?:^|[\s(«"*.—\-])(?:да[,.:;)!\s]|видн\w*|цел\w*|на месте|появил\w*|читаем\w*|корректн\w*)/g
        ) || []).length;
        ok = yes >= 2 && !defectClaim;
    }
    if (ok) { pass++; } else { fail++; }
    console.log((ok ? '  + ' : '  X ') + file + ': ' + EXPECT[file] +
        (defectClaim ? ' [дефект-строка!]' : ''));
}

console.log('ИТОГ VLM Task 496: ' + pass + ' passed, ' + fail + ' failed');
raise_process_exit(pass, fail);

function raise_process_exit(pass, fail) {
    process.exit(fail === 0 ? 0 : 1);
}
