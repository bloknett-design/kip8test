#!/usr/bin/env node
// scripts/task505-vlm-check.js — VLM-проверка скриншотов Task 505
// (паттерн task504-vlm-check.js; CLI `z-ai vision`).
// Заявка: в разделе «Кабельный журнал» кнопка печати (компактная,
// значок принтера) с диалогом предпросмотра и сохранением в PDF/Excel.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task505';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a1-page.png',
     'Это страница «Кабельный журнал» приложения (тёмная тема): группы записей (по умолчанию СВЁРНУТЫ — видны только заголовки групп с количеством записей), вверху строка-шапка с заголовком и кнопками справа. Ответь строго по пунктам: (1) В шапке СПРАВА видны ТРИ компактные квадратные кнопки: «+» (добавить), иконка поиска (лупа) и иконка ПРИНТЕРА? (2) Кнопка с иконкой принтера — квадратная, примерно как «+» по размеру (не растянута, не огромная)? (3) В списке видны свёрнутые группы «Водоподготовка» (2 записи) и «Отделение №2» (1 запись)? (4) Есть ли визуальные дефекты (наложение кнопок, обрезка заголовка, разъехавшаяся вёрстка)?'],
    ['a2-dialog.png',
     'Это диалог «Предпросмотр печати» раздела «Кабельный журнал» (тёмная тема): белый лист-предпросмотр таблицы журнала и ряд кнопок внизу. Ответь строго по пунктам: (1) Заголовок диалога — «Предпросмотр печати», подзаголовок упоминает «Кабельный журнал»? (2) На листе таблица с шапкой: колонки «№», «Обозначение», «Начало трассы», «Конец трассы», «Участок», «Назначение» и пары «По проекту» / «Проложен» над подколонками «Марка», «Жилы», «Длина, м»? (3) В таблице есть СЕРЫЕ строки-подзаголовки отделений «Водоподготовка» и «Отделение №2»? (4) Внизу диалога есть кнопки «Печать», «Сохранить PDF», «Сохранить Excel», «Отмена» и подсказка «A4 · альбомная»? (5) Таблица читается, зебра-строки чередуются, есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['c1-mobile-dialog.png',
     'Это МОБИЛЬНЫЙ (375px) диалог «Предпросмотр печати» раздела «Кабельный журнал» (тёмная тема, на весь экран): БЕЛЫЙ лист — это СЖАТЫЙ до ширины экрана альбомный лист A4 (мелкий текст на нём — НОРМА для предпросмотра, читаемость ячеек не оценивается). Ответь строго по пунктам: (1) Диалог занимает весь экран? (2) Белый лист с таблицей (шапка с колонками, строки, серые строки-подзаголовки отделений) виден целиком, не обрезан? (3) Кнопки внизу читаемы: «Печать», «Сохранить PDF», «Сохранить Excel», «Отмена»? (4) Есть ли визуальные дефекты (наложение, вылезание за экран, пустой лист)?']
];

const CACHE = path.join(DIR, 'vlm-task505-out.json');
let cache = {};
if (fs.existsSync(CACHE)) cache = JSON.parse(fs.readFileSync(CACHE, 'utf8'));

function score(txt) {
    const t = String(txt);
    let ok = true;
    const qs = t.split(/\(\d\)|(?=^\d\.\s)/m).map(x => x.trim()).filter(x => x);
    if (qs.length >= 3) {
        for (const q of qs) {
            const low = q.toLowerCase();
            const isDefectQ = /дефект/i.test(q);
            const negated = /не наблюд|не содержит|отсутств|нет\b|ничего|не замечен|не обнаруж/i.test(low.slice(0, 60));
            const lowClean = low.replace(/\*/g, '');
            const hasYes = /(^|[^а-яё])да[,. ]/i.test(lowClean) ||
                           /да\b/i.test(lowClean.slice(0, 30));
            if (isDefectQ) {
                if (negated && !/есть .*дефект|обнаружен дефект/i.test(low)) { /* ок */ }
                else if (/^да[,.]?\s*(есть|видны?|обнаруж)/i.test(low.trim())) { ok = false; }
            } else {
                if (!hasYes && /(^|[^а-яё])(нет|не видн|неверно|отсутств)/i.test(low)) { ok = false; }
            }
        }
    } else {
        if (/(есть|видны?|присутству)\D{0,40}дефект/i.test(t)) ok = false;
    }
    return ok;
}

let pass = 0, fail = 0;
for (const [file, prompt] of shots) {
    let txt;
    const ck = cache[file];
    if (ck && ck.prompt === prompt) {
        txt = ck.answer;
        console.log('[кэш] ' + file);
    } else {
        try {
            txt = vision(file, prompt);
        } catch (e) {
            console.log('X ' + file + ': ' + String(e).slice(0, 200));
            fail++;
            continue;
        }
        cache[file] = { prompt, answer: txt };
    }
    const ok = score(txt);
    if (ok) pass++; else fail++;
    console.log((ok ? '+ ' : 'X ') + file);
    console.log('    ' + String(txt).replace(/\s+/g, ' ').slice(0, 400));
}

fs.writeFileSync(CACHE, JSON.stringify(cache, null, 2));
console.log('\nVLM ИТОГ: ' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
