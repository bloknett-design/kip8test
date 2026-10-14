#!/usr/bin/env node
// scripts/task521-vlm-check.js — VLM-проверка скриншотов Task 521
// (паттерн task504-vlm-check.js; CLI `z-ai vision`).
// Заявка: малая форма д/н Табеля — два поля «Время начала/окончания
// работ», часы переработки считаются автоматически (янтарная строка).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task521';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a-form-prefill.png',
     'Это попап малой формы выбора кода «д» (день в выходной) у дневного персонала в разделе «Табель учёта рабочего времени» (тёмная тема): заголовок с датой и ФИО, строка кода со свотчем, ниже форма. Ответь строго по пунктам: (1) В форме есть ДВА поля ввода времени, РЯДОМ (в один ряд): «Время начала работ» со значением 07:30 и «Время окончания работ» со значением 15:30? (2) Под полями есть строка «Переработка: 8 ч» ОРАНЖЕВОГО/ЯНТАРНОГО цвета? (3) Есть кнопки «Готово» и «Назад к кодам»? (4) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['d-overnight.png',
     'Это та же форма после ввода времени 20:00 и 04:00. Ответь строго по пунктам: (1) Поле «Время начала работ» показывает 20:00, «Время окончания работ» — 04:00? (2) Строка расчёта — «Переработка: 8 ч (через полночь)» янтарного цвета? (3) Есть ли визуальные дефекты?'],
    ['e-error-toast.png',
     'Это форма с одинаковым временем 08:00 и 08:00. Ответь строго по пунктам: (1) Показан тост/уведомление с текстом про совпадение времени начала и окончания? (2) Форма осталась открытой (два поля времени видны)? (3) Есть ли визуальные дефекты?']
];

const results = {};
let pass = 0, fail = 0;
shots.forEach(function(pair) {
    const txt = vision(pair[0], pair[1]);
    results[pair[0]] = txt;
    console.log('=== ' + pair[0] + ' ===');
    console.log(txt.slice(0, 900));
});

function hasNo(txt, words) {
    const t = String(txt).toLowerCase();
    return words.every(function(w) { return t.indexOf(w) !== -1; });
}
const checks = [
    ['префилл: два поля в ряд 07:30/15:30',
     hasNo(results['a-form-prefill.png'], ['время начала', 'время окончания']) &&
     /07:30/.test(results['a-form-prefill.png']) &&
     /15:30/.test(results['a-form-prefill.png'])],
    ['янтарная строка «Переработка: 8 ч»',
     /переработка[^.]{0,20}8/i.test(String(results['a-form-prefill.png']).toLowerCase()) &&
     /янтарн|оранжев/.test(String(results['a-form-prefill.png']).toLowerCase())],
    ['полночь: 20:00/04:00 + «через полночь»',
     /20:00/.test(results['d-overnight.png']) &&
     /04:00/.test(results['d-overnight.png']) &&
     String(results['d-overnight.png']).toLowerCase().indexOf('через полночь') !== -1],
    ['тост об ошибке виден',
     String(results['e-error-toast.png']).toLowerCase().indexOf('совпад') !== -1 ||
     String(results['e-error-toast.png']).toLowerCase().indexOf('время') !== -1],
    ['без визуальных дефектов (все кадры)',
     ['a-form-prefill.png', 'd-overnight.png', 'e-error-toast.png'].every(function(f) {
         return !/(есть|да)[^.]{0,20}(дефект|наложен|обрезк)/i.test(results[f]);
     })]
];
checks.forEach(function(c) {
    console.log((c[1] ? '  + ' : '  X ') + c[0]);
    if (c[1]) { pass++; } else { fail++; }
});
fs.writeFileSync(path.join(DIR, 'vlm-task521-out.json'),
    JSON.stringify(results, null, 2));
console.log();
console.log('ИТОГО VLM: ' + pass + ' passed, ' + fail + ' failed');
if (fail) { process.exit(1); }
