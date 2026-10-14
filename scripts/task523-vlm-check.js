#!/usr/bin/env node
// scripts/task523-vlm-check.js — VLM-проверка скриншотов Task 523
// (паттерн task522-vlm-check.js; CLI `z-ai vision`).
// Заявка: времена начала/окончания работ д/н сохраняются в колонках
// L/M и отображаются в окне ячейки; «н» = «д» (симметрия).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task523';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a-hover-d-times.png',
     'Это всплывающее окно «Мероприятия в этот день» у ячейки с кодом «д» дневного персонала в разделе «Табель учёта рабочего времени» (тёмная тема). Под строкой «дата · ФИО» секция «Статус дня»: цветной квадратик-свотч, символ «д», длинное описание кода и строка времени работы янтарного/оранжевого цвета. Ответь строго по пунктам: (1) Секция с кодом «д» и описанием видна? (2) Есть янтарная строка вида «Время работы: 07:30–15:12 · 7,7 ч» — с диапазоном времени через тире и часами? (3) Слов «через полночь» в этой строке НЕТ (это дневная смена)? (4) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['b-hover-n-night.png',
     'Это то же окно, но у ячейки с кодом «н» (ночь) дневного персонала. Ответь строго по пунктам: (1) В секции виден код «н» и описание ночной работы? (2) Есть янтарная строка «Время работы: 19:30–07:30 · 12 ч (через полночь)»? (3) Пометка «(через полночь)» присутствует? (4) Есть ли визуальные дефекты?'],
    ['e-form-n-midnight.png',
     'Это малая форма ввода времени работ в попапе ячейки для кода «н»: заголовок «дата · ФИО», строка с кодом «н», два поля времени (Время начала работ / Время окончания работ) в один ряд, янтарная строка «Переработка: 12 ч (через полночь)», кнопки «Готово» и «Назад к кодам». Ответь строго по пунктам: (1) Два поля времени видны в один ряд? (2) В полях стоят значения 19:30 и 07:30 (браузер может показать их как 07:30 PM и 07:30 AM — это те же значения)? (3) Янтарная строка переработки с «(через полночь)» видна? (4) Фокус/подсветка поля ввода (синяя рамка) — НЕ дефект, это нормальное состояние. Есть ли ДРУГИЕ визуальные дефекты?']
];

const results = {};
let pass = 0, fail = 0;
shots.forEach(function(pair) {
    const txt = vision(pair[0], pair[1]);
    results[pair[0]] = txt;
    console.log('=== ' + pair[0] + ' ===');
    console.log(txt.slice(0, 900));
});

function low(f) { return String(results[f] || '').toLowerCase(); }
const checks = [
    ['A: секция «д» + диапазон «07:30–15:12 · 7,7 ч»',
     /07:30\s*[–-]\s*15:12/.test(low('a-hover-d-times.png')) &&
     /7,7|7\.7/.test(low('a-hover-d-times.png'))],
    ['A: янтарная строка времени',
     /янтарн|оранжев/.test(low('a-hover-d-times.png'))],
    ['A: без «через полночь» (день)',
     (function() {
         const a = low('a-hover-d-times.png');
         if (a.indexOf('через полночь') === -1) return true;
         // VLM эхо вопроса: фраза допустима ТОЛЬКО с отрицанием рядом
         const frags = a.match(/через полночь[^.]{0,60}/g) || [];
         return frags.length > 0 && frags.every(function(s) {
             return /(нет|отсутств|не\s|не$)/.test(s);
         });
     })()],
    ['B: «н» с диапазоном 19:30–07:30 и 12 ч',
     /19:30\s*[–-]\s*07:30/.test(low('b-hover-n-night.png')) &&
     /12\s*ч/.test(low('b-hover-n-night.png'))],
    ['B: пометка «через полночь»',
     low('b-hover-n-night.png').indexOf('через полночь') !== -1],
    ['E: форма «н» — два поля 19:30/07:30 + полночь',
     /19:30/.test(low('e-form-n-midnight.png')) &&
     /07:30/.test(low('e-form-n-midnight.png')) &&
     low('e-form-n-midnight.png').indexOf('через полночь') !== -1],
    ['без визуальных дефектов (все кадры)',
     ['a-hover-d-times.png', 'b-hover-n-night.png',
      'e-form-n-midnight.png'].every(function(f) {
         return !/(есть|да)[^.]{0,25}(дефект|наложен|обрезк|разъехал)/i.test(results[f]);
     })]
];
checks.forEach(function(c) {
    console.log((c[1] ? '  + ' : '  X ') + c[0]);
    if (c[1]) { pass++; } else { fail++; }
});
fs.writeFileSync(path.join(DIR, 'vlm-task523-out.json'),
    JSON.stringify(results, null, 2));
console.log();
console.log('ИТОГО VLM: ' + pass + ' passed, ' + fail + ' failed');
if (fail) { process.exit(1); }
