#!/usr/bin/env node
// scripts/task508-vlm-check.js — VLM-проверка скриншотов Task 508
// (паттерн task505/506-vlm-check.js; CLI `z-ai vision`).
// Заявка: архив журнала — удалённые записи скрыты из списка/печати/
// PDF, видны в Excel; «записей: 4» в предпросмотре (не 6).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task508';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

const shots = [
    ['a2-print-no-archive.png',
     'Это диалог «Предпросмотр печати» раздела «Кабельный журнал» (тёмная тема), внутри — белая страница A4 с таблицей кабельного журнала. Ответь строго по пунктам: (1) В строке подзаголовка (рядом с «Предпросмотр печати») написано «Кабельный журнал — записей: 4» — число записей 4 (НЕ 6)? (2) Таблица отрисована: видна двухуровневая шапка (слева «Обозначение кабеля, провода», пары «По проекту»/«Проложен») и строки данных? (3) Внизу диалога кнопки: «Печать», «Сохранить PDF», «Сохранить Excel», «Отмена»? (4) Есть ли визуальные дефекты (наложение текста, обрезка таблицы, пустой экран)?'],
    ['a3-after-delete.png',
     'Это раздел «Кабельный журнал» приложения (тёмная тема) сразу после удаления записи: список свёрнутых групп отделений с количеством записей. Ответь строго по пунктам: (1) Список не пуст: видны группы-карточки отделений (тёмные блоки со стрелкой, названием и числом записей)? (2) Вверху страницы есть строка поиска и кнопка-иконка принтера? (3) Есть ли визуальные дефекты (наложение, обрезка, пустой экран)?'],
    ['c1-mobile-dialog.png',
     'Это МОБИЛЬНЫЙ (375px) диалог «Предпросмотр печати» кабельного журнала (тёмная тема, на весь экран): мелкий текст сжатых страниц A4 — НОРМА (читаемость ячеек не оценивается). Ответь строго по пунктам: (1) Диалог занимает весь экран? (2) Внизу кнопки читаемы: «Печать», «Сохранить PDF», «Сохранить Excel», «Отмена»? (3) Есть ли визуальные дефекты (наложение, вылезание за экран, пустой экран)?']
];

const CACHE = path.join(DIR, 'vlm-task508-out.json');
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
    if (cache[file]) {
        txt = cache[file];
        console.log('(кэш) ' + file);
    } else {
        try {
            txt = vision(file, prompt);
            cache[file] = txt;
        } catch (e) {
            console.log('FAIL ' + file + ' — ' + String(e).slice(0, 160));
            fail++;
            continue;
        }
    }
    const ok = score(txt);
    console.log('%s %s', ok ? 'OK  ' : 'FAIL', file);
    console.log('     ответ: ' + String(txt).replace(/\s+/g, ' ').slice(0, 220));
    if (ok) pass++; else fail++;
}

fs.writeFileSync(CACHE, JSON.stringify(cache, null, 2));
console.log('\nИТОГ VLM: %d passed, %d failed', pass, fail);
process.exit(fail ? 1 : 0);
