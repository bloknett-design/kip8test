#!/usr/bin/env node
// scripts/task554-vlm-check.js — VLM-проверка скриншотов Task 554
// (паттерн task553-vlm-check.js; CLI `z-ai vision`).
// Заявка: «при отметке галочкой о выполнении и автоматическом
// формировании списка на следующий год, примечания так же должны
// переноситься» — созданные записи с новым сроком несут примечание
// отмеченной записи (тёмная тема, карточка работника).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task554';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const NOTE_CARRY = 'Это страница «Работники» раздела «Табель учёта рабочего времени» (тёмная тема), карточка работника Иванова, блок «Повторные инструктажи и периодическая проверка знаний · 2026». Пользователь отметил галочкой выполнение инструктажа 15.03.2026 (примечание «протокол № 12, ведёт Иванов А.А.»), и система автоматически создала записи с новыми сроками. Ответь строго по пунктам: (1) Строка «Повторный инструктаж по рабочим инструкциям ОТ · 15.03.2026» оканчивается примечанием «протокол № 12, ведёт Иванов А.А.» в кавычках-ёлочках? (2) Есть строка «Повторный инструктаж по инструкции № 9-ОГЭ · 15.06.2026» и она ТОЖЕ несёт примечание «протокол № 12, ведёт Иванов А.А.»? (3) Есть строка «Повторный инструктаж по рабочим инструкциям ОТ · 15.09.2026» и она ТОЖЕ несёт то же примечание? (4) Примечания набраны курсивом и чуть тусклее основного текста? (5) Строка «Периодическая проверка знаний … · 20.05.2026» — без галочки-отметки выполнения? (6) Вёрстка аккуратная: ничего не наложено и не обрезано?';

const TOAST_OLD = 'Это тот же экран приложения КИПиА (тёмная тема): внизу/сверху виден тост-уведомление с текстом про отметку выполнения и предупреждением «Сервер Apps Script старой версии — замените WorkSchedule.gs и создайте новую версию развёртывания». Ответь строго по пунктам: (1) Тост виден? (2) В тексте есть слова «старой версии»? (3) Есть подсказка «замените WorkSchedule.gs»? (4) Тост читаем, не обрезан?';

const shots = [
    ['01-workers-017-note-carry-dark.png', NOTE_CARRY],
    ['02-toast-old-server.png', TOAST_OLD]
];

const results = {};
shots.forEach(function(pair) {
    const txt = vision(pair[0], pair[1]);
    results[pair[0]] = txt;
    console.log('=== ' + pair[0] + ' ===');
    console.log(txt.slice(0, 800));
});

function low(f) { return String(results[f] || '').toLowerCase(); }
const checks = [
    ['A: исходная строка 15.03 — примечание в ёлочках',
     low('01-workers-017-note-carry-dark.png').indexOf('протокол № 12') !== -1],
    ['A: созданный 9-ОГЭ 15.06 — примечание ПЕРЕНЕСЕНО',
     /9-ОГЭ[^.]{0,200}15\.06|15\.06[^.]{0,200}9-ОГЭ/i.test(
         low('01-workers-017-note-carry-dark.png')) &&
     (low('01-workers-017-note-carry-dark.png').match(/протокол № 12/g) || []).length >= 2],
    ['A: созданный общий 15.09 — примечание ПЕРЕНЕСЕНО',
     low('01-workers-017-note-carry-dark.png').indexOf('15.09.2026') !== -1 &&
     (low('01-workers-017-note-carry-dark.png').match(/протокол № 12/g) || []).length >= 3],
    ['A: примечания — курсив/тише текста',
     /курсив/.test(low('01-workers-017-note-carry-dark.png'))],
    ['B: тост — «старой версии» + «замените WorkSchedule.gs»',
     low('02-toast-old-server.png').indexOf('старой версии') !== -1 &&
     low('02-toast-old-server.png').indexOf('workschedule') !== -1],
    ['санитар: affirmed нет визуальных дефектов',
     shots.every(function(p) {
         return !/(есть|присутствуют?)[^.]{0,40}(дефект|наложен|обрезк|перекрыв)/i.test(
             results[p[0]] || '');
     })]
];

let pass = 0, fail = 0;
checks.forEach(function(c) {
    const ok = !!c[1];
    console.log((ok ? '  + ' : '  X ') + c[0]);
    ok ? pass++ : fail++;
});

fs.writeFileSync(path.join(DIR, 'vlm-task554-out.json'),
    JSON.stringify(results, null, 2), 'utf8');
console.log('\nИТОГО VLM: ' + pass + '/' + (pass + fail) + ', FAIL=' + fail);
process.exit(fail ? 1 : 0);
