#!/usr/bin/env node
// scripts/task506-vlm-check.js — VLM-проверка скриншотов Task 506
// (паттерн task505-vlm-check.js; CLI `z-ai vision`).
// Заявка: печать «Кабельного журнала» по шаблону исходной Google-
// таблицы — без текста «Кабельный журнал отделений…», шапка на
// каждой странице, предпросмотр с разбиением на страницы A4.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task506';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a1-page-seam.png',
     'Это диалог «Предпросмотр печати» раздела «Кабельный журнал» (тёмная тема), прокрученный к СТЫКУ двух страниц A4: альбомная страница занимает всю высоту окна, внизу кадра — нижний край одной страницы, затем тёмный промежуток и верх следующей страницы. Ответь строго по пунктам: (1) В кадре виден нижний край страницы, тёмный промежуток-разделитель и начало СЛЕДУЮЩЕЙ страницы (разбиение на листы)? (2) В начале следующей страницы — ТА ЖЕ двухуровневая шапка таблицы, что и вверху журнала (слева «Обозначение кабеля, провода»… справа пары «По проекту»/«Проложен» с подколонками «Марка»/«Число и сечение жил»/«Длина, м») — шапка ПОВТОРЯЕТСЯ на каждой странице? (3) Подтверди цвет заливки: колонки группы «По проекту» залиты светло-серым фоном, а колонки группы «Проложен» — белым? (4) Есть ли визуальные дефекты (наложение текста, обрезка строк, слипшиеся страницы без разделителя)?'],
    ['b1-page-seam.png',
     'Это диалог «Предпросмотр печати» в светлой теме приложения, прокрученный к стыку двух страниц A4 с таблицей кабельного журнала. Ответь строго по пунктам: (1) Виден стык: нижний край одной страницы, серый промежуток и начало следующей страницы? (2) На следующей странице вверху повторяется двухуровневая шапка таблицы (пары «По проекту»/«Проложен» над тремя подколонками)? (3) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['c1-mobile-preview.png',
     'Это МОБИЛЬНЫЙ (375px) диалог «Предпросмотр печати» кабельного журнала (тёмная тема, на весь экран): мелкий текст сжатых страниц A4 — НОРМА (читаемость ячеек не оценивается). Ответь строго по пунктам: (1) Диалог занимает весь экран? (2) Видно НЕСКОЛЬКО белых страниц-листов, разделённых промежутками (не один сплошной лист)? (3) Кнопки внизу читаемы: «Печать», «Сохранить PDF», «Сохранить Excel», «Отмена»? (4) Есть ли визуальные дефекты (наложение, вылезание за экран, пустой экран)?']
];

const CACHE = path.join(DIR, 'vlm-task506-out.json');
let cache = {};
if (fs.existsSync(CACHE)) cache = JSON.parse(fs.readFileSync(CACHE, 'utf8'));

function score(txt) {
    const t = String(txt).replace(/\*/g, '');
    let ok = true;
    const qs = t.split(/\(\d\)|(?=^\d\.\s)/m).map(x => x.trim()).filter(x => x);
    if (qs.length >= 3) {
        for (const q of qs) {
            const low = q.toLowerCase();
            const isDefectQ = /дефект/i.test(q);
            const negated = /не наблюд|не содержит|отсутств|нет\b|ничего|не замечен|не обнаруж/i.test(low.slice(0, 60));
            const hasYes = /(^|[^а-яё])да[,. ]/i.test(low) ||
                           /да\b/i.test(low.slice(0, 30));
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
    console.log('    ' + String(txt).replace(/\s+/g, ' ').slice(0, 500));
}

fs.writeFileSync(CACHE, JSON.stringify(cache, null, 1));
console.log('\nVLM: %d/%d (fail=%d)', pass, pass + fail, fail);
process.exit(fail ? 1 : 0);
