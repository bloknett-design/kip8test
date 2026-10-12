#!/usr/bin/env node
// scripts/task504-vlm-check.js — VLM-проверка скриншотов Task 504
// (паттерн task502-vlm-check.js; CLI `z-ai vision`).
// Заявка: в окне «Мероприятия» раздела «Табель учёта рабочего времени»
// даты ВЫПОЛНЕННЫХ мероприятий — ЗЕЛЁНЫЕ, ПРОСРОЧЕННЫХ — КРАСНЫЕ.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const DIR = '/home/z/my-project/download/kip8test-task504';

function vision(file, prompt) {
    const out = execFileSync('z-ai', [
        'vision', '-p', prompt, '-i', path.join(DIR, file)
    ], { encoding: 'utf8', timeout: 120000, stdio: ['ignore', 'pipe', 'pipe'] });
    const m = out.match(/"content":\s*"((?:[^"\\]|\\.)*)"/);
    return m ? JSON.parse('"' + m[1] + '"') : out;
}

// Даты мока (смещения от «сегодня», кламп в месяц — как в
// task504-browser-check.py): 100=И d(-5) зелёная, 102=И d(-4) красная
// (фолбэк), 101=ПЗ d(-3) красная, 104=ОБ d(-2) обычная,
// 105=ПЗ d(-1) зелёная (приоритет), 103=ПЗ d(+5) обычная, СИЗ d(+10)
const _t = new Date();
const _dim = new Date(_t.getFullYear(), _t.getMonth() + 1, 0).getDate();
const _pad = n => (n < 10 ? '0' : '') + n;
const d = off => {
    const dd = Math.max(1, Math.min(_dim, _t.getDate() + off));
    return _pad(dd) + '.' + _pad(_t.getMonth() + 1);
};
const D = { dn5: d(-5), dn4: d(-4), dn3: d(-3), dn2: d(-2),
            dn1: d(-1), dp5: d(5), dp10: d(10) };

const shots = [
    ['t504-panel-dark-x25.png',
     'Это окно «Мероприятия» раздела «Табель учёта рабочего времени» (тёмная тема, увеличено 2.5×): строки «точка · дата · текст». Ответь строго по пунктам: (1) Даты ' + D.dn5 + ' и ' + D.dn1 + ' — ЗЕЛЁНЫЕ? (2) Даты ' + D.dn4 + ' и ' + D.dn3 + ' — КРАСНЫЕ? (3) Дата ' + D.dn2 + ' (строка «Обучение по новой редакции инструкций») и дата ' + D.dp5 + ' (строка «Проверка знаний КИПиА») — обычного СЕРОГО/БЕЛОГО цвета (не зелёные, не красные)? (4) Дата «до ' + D.dp10 + '» в секции «СИЗ» — обычного цвета (не зелёная/не красная)? (5) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['t504-panel-light-x25.png',
     'Это окно «Мероприятия» раздела «Табель учёта рабочего времени» (СВЕТЛАЯ тема, увеличено 2.5×): строки «точка · дата · текст». Ответь строго по пунктам: (1) Дата ' + D.dn5 + ' (строка «Повторный инструктаж по охране труда») — ЗЕЛЁНАЯ? (2) Дата ' + D.dn3 + ' (строка «Проверка знаний до 1000В») — КРАСНАЯ? (3) Даты ' + D.dn2 + ' (обучение) и ' + D.dp5 + ' (будущая проверка знаний КИПиА) — обычного ЧЁРНОГО цвета? (4) Дата «до ' + D.dp10 + '» секции «СИЗ» — обычного цвета? (5) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?'],
    ['c-mobile-dark.png',
     'Это ПОЛНЫЙ скриншот мобильной страницы «Табель учёта рабочего времени» (тёмная тема, 375px), раскрытое окно «Мероприятия». Ответь строго по пунктам: (1) В списке мероприятий есть даты ЗЕЛЁНОГО цвета? (2) Есть даты КРАСНОГО цвета? (3) Текст строк (тема/ФИО) — обычного светлого цвета, читается? (4) Есть ли визуальные дефекты (наложение, обрезка, разъехавшаяся вёрстка)?']
];

const CACHE = path.join(DIR, 'vlm-task504-out.json');
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
