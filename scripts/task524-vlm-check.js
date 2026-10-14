#!/usr/bin/env node
// scripts/task524-vlm-check.js — VLM-проверка скриншотов Task 524
// (паттерн task522/523-vlm-check.js; CLI `z-ai vision`).
// Заявка: в описаниях кодов «д»/«н» убран хвост «в комментарии».
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task524';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a-hover-dn-new-wording.png',
     'Это всплывающее окно «Мероприятия в этот день» у ячейки с кодом «д» дневного персонала в разделе «Табель учёта рабочего времени» (тёмная тема). Под строкой «дата · ФИО» секция «Статус дня»: цветной квадратик-свотч, символ «д», длинное описание кода (несколько строк) и янтарная строка времени работы. Ответь строго по пунктам: (1) Секция с кодом «д» и описанием видна? (2) Процитируй ДОСЛОВНО, буква в букву, последние 6 слов описания кода. (3) Есть янтарная строка «Время работы: 7,2 ч»? (4) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['b-hover-nn-new-wording.png',
     'Это то же окно, но у ячейки с кодом «н» (ночь в выходной) дневного персонала. Ответь строго по пунктам: (1) В секции виден код «н» и описание ночной работы? (2) Описание оканчивается частью про дневной персонал: процитируй её ЦЕЛИКОМ, ДОСЛОВНО — от слов «для дневного персонала» до САМОГО КОНЦА описания. (3) Процитируй ДОСЛОВНО янтарную строку времени работы (диапазон и часы). (4) Есть ли визуальные дефекты?'],
    ['d-legend-panel.png',
     'Это панель «Обозначения» (расшифровка кодов табеля) справа от сетки шахматки, тёмная тема, РАЗВЁРНУТЫЙ (широкий) вид: у каждого кода — ПОЛНОЕ название вместо краткой подписи. Нужна секция «Коды дней (Т-12/Т-13)» со строками кодов Д8/Д7,2/Д/Н/д/н — НЕ секция мероприятий. Ответь строго по пунктам: (1) Секция «Коды дней (Т-12/Т-13)» со строками кодов «д» и «н» видна? (2) Процитируй ДОСЛОВНО, буква в букву, последние 8 слов ПОЛНОГО описания у строки «д». (3) То же — последние 8 слов описания у строки «н». (4) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?']
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

// «в комментарии» в ответе допустимо ТОЛЬКО с отрицанием рядом
// (VLM эхо вопроса/цитата «слов нет») — урок Task 523
function noCommentPhrase(f) {
    const a = low(f);
    if (a.indexOf('в комментарии') === -1) return true;
    const frags = a.match(/в комментарии[^.]{0,80}/g) || [];
    return frags.length > 0 && frags.every(function(s) {
        return /(нет|отсутств|не\s|не$|заканчивается на)/.test(s);
    });
}

const checks = [
    ['A: секция «д» видна, описание читаемо',
     /секц|описан/.test(low('a-hover-dn-new-wording.png'))],
    ['A: описание оканчивается «(в часах)» — без «в комментарии»',
     /часах|часов/.test(low('a-hover-dn-new-wording.png')) &&
     /продолжительност/.test(low('a-hover-dn-new-wording.png')) &&
     noCommentPhrase('a-hover-dn-new-wording.png')],
    ['A: янтарная строка «Время работы: 7,2 ч»',
     /время работы/.test(low('a-hover-dn-new-wording.png')) &&
     /7,2|7\.2/.test(low('a-hover-dn-new-wording.png'))],
    ['B: секция «н» + ночная пара и полночь',
     (low('b-hover-nn-new-wording.png').indexOf('через полночь') !== -1 ||
      /19:30/.test(low('b-hover-nn-new-wording.png'))) &&
     /12\s*ч|12 часов/.test(low('b-hover-nn-new-wording.png'))],
    ['B: описание «н» оканчивается «(в часах)» — без «в комментарии»',
     /часах|часов/.test(low('b-hover-nn-new-wording.png')) &&
     /продолжительност/.test(low('b-hover-nn-new-wording.png')) &&
     noCommentPhrase('b-hover-nn-new-wording.png')],
    ['D: панель — секция «Коды дней (Т-12/Т-13)» со строками д/н',
     /т-12|коды дней|д8/.test(low('d-legend-panel.png'))],
    ['D: описания в панели оканчиваются «(в часах)» — без «в комментарии»',
     /часах|часов/.test(low('d-legend-panel.png')) &&
     /продолжительност/.test(low('d-legend-panel.png')) &&
     noCommentPhrase('d-legend-panel.png')],
    ['без визуальных дефектов (все кадры)',
     ['a-hover-dn-new-wording.png', 'b-hover-nn-new-wording.png',
      'd-legend-panel.png'].every(function(f) {
         return !/(есть|да)[^.]{0,25}(дефект|наложен|обрезк|разъехал)/i.test(results[f]);
     })]
];
checks.forEach(function(c) {
    console.log((c[1] ? '  + ' : '  X ') + c[0]);
    if (c[1]) { pass++; } else { fail++; }
});
fs.writeFileSync(path.join(DIR, 'vlm-task524-out.json'),
    JSON.stringify(results, null, 2));
console.log();
console.log('ИТОГО VLM: ' + pass + ' passed, ' + fail + ' failed');
if (fail) { process.exit(1); }
