#!/usr/bin/env node
// scripts/task522-vlm-check.js — VLM-проверка скриншотов Task 522
// (паттерн task521-vlm-check.js; CLI `z-ai vision`).
// Заявка: окно ячейки Табеля — секция «Статус дня» для «д»/«н»
// дневного персонала: справка по коду + «Время работы: N ч».
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task522';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a-hover-dn-info.png',
     'Это всплывающее окно «Мероприятия в этот день» у ячейки с кодом «д» дневного персонала в разделе «Табель учёта рабочего времени» (тёмная тема). Под заголовком и строкой «дата · ФИО» должна быть секция «Статус дня»: цветной квадратик-свотч, символ «д» и ДЛИННОЕ описание кода (переносится на несколько строк), ниже строка времени работы янтарного/оранжевого цвета. Ответь строго по пунктам: (1) Секция со свотчем, кодом «д» и длинным описанием кода видна? (2) Есть строка «Время работы: 7,2 ч» ОРАНЖЕВОГО/ЯНТАРНОГО цвета? (3) Ниже есть курсивная строка «нет мероприятий»? (4) Длинный текст описания читаем, переносится строками, не обрезан? (5) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['c-hover-dn-event.png',
     'Это то же окно, но у ячейки «д» с мероприятием. Ответь строго по пунктам: (1) Секция «Статус дня» (свотч + «д» + описание + «Время работы: 8 ч») видна СВЕРХУ? (2) Ниже её есть строка мероприятия «Повторный инструктаж по охране труда» со своим цветным квадратиком? (3) Есть ли визуальные дефекты?'],
    ['h-click-viewer.png',
     'Это окно «Мероприятия в этот день» после КЛИКА зрителя (без права правки) по ячейке «д» дневного персонала. Ответь строго по пунктам: (1) Окно со списком КОДОВ для выбора (многострочный список кодов-статусов) НЕ показывается — видно только справочное окно с секцией «Статус дня» и «нет мероприятий»? (2) Строка «Время работы: 7,2 ч» янтарного цвета видна? (3) Есть ли визуальные дефекты?']
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
    ['A: секция с кодом «д» и описанием',
     low('a-hover-dn-info.png').indexOf('д') !== -1 &&
     /описан|секци/.test(low('a-hover-dn-info.png'))],
    ['A: янтарная строка «Время работы: 7,2 ч»',
     /время работы[^.]{0,15}7,2/.test(low('a-hover-dn-info.png')) &&
     /янтарн|оранжев/.test(low('a-hover-dn-info.png'))],
    ['A: «нет мероприятий» + читаемый перенос',
     low('a-hover-dn-info.png').indexOf('нет мероприятий') !== -1 &&
     !/(?<!не )(обрезан|не читается)/.test(low('a-hover-dn-info.png'))],
    ['C: секция сверху + мероприятие снизу',
     /повторный инструктаж|инструктаж по охране/.test(low('c-hover-dn-event.png')) &&
     low('c-hover-dn-event.png').indexOf('время работы') !== -1],
    ['H: зритель — только справочное окно (без списка кодов)',
     low('h-click-viewer.png').indexOf('время работы') !== -1 &&
     (/не показыва|только справочн|только окно/.test(low('h-click-viewer.png')))],
    ['без визуальных дефектов (все кадры)',
     ['a-hover-dn-info.png', 'c-hover-dn-event.png', 'h-click-viewer.png'].every(function(f) {
         return !/(есть|да)[^.]{0,25}(дефект|наложен|обрезк|разъехал)/i.test(results[f]);
     })]
];
checks.forEach(function(c) {
    console.log((c[1] ? '  + ' : '  X ') + c[0]);
    if (c[1]) { pass++; } else { fail++; }
});
fs.writeFileSync(path.join(DIR, 'vlm-task522-out.json'),
    JSON.stringify(results, null, 2));
console.log();
console.log('ИТОГО VLM: ' + pass + ' passed, ' + fail + ' failed');
if (fail) { process.exit(1); }
