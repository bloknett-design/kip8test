#!/usr/bin/env node
// Task 495: диагностика окон истории sw.js после вставки комментария
// (~287 симв. перед CACHE_VERSION). Для каждого якоря считаем
// дистанцию до CACHE_VERSION (iConst) / v-строки (iVstr).
const fs = require('fs');
const SW = fs.readFileSync('/home/z/my-project/kip8test/sw.js', 'utf8');

const iConst = SW.indexOf("const CACHE_VERSION = 'kipia-test-v719';");
const iVstr = SW.indexOf('kipia-test-v719');
console.log('iConst =', iConst, ' iVstr =', iVstr);

function lastAnchors(i, marks) {
    for (const m of marks) {
        const pos = SW.lastIndexOf(m, i);
        console.log('  %-14s дистанция %d', m, i - pos);
    }
}

console.log('\n== Маркеры комментариев задач (от iConst) ==');
lastAnchors(iConst, [
    'Task 461', 'Task 471', 'Task 472', 'Task 473', 'Task 474',
    'Task 476', 'Task 477', 'Task 478', 'Task 479', 'Task 480',
    'Task 481', 'Task 482', 'Task 483', 'Task 484', 'Task 485',
    'Task 486', 'Task 488', 'Task 490', 'Task 491', 'Task 492',
    'Task 493', 'Task 494', 'Task 495'
]);

console.log('\n== Спец-якоря контента (от iConst) ==');
lastAnchors(iConst, [
    'Период ремонта', 'ЗЕЛЁНЫЙ', 'КРАСНЫЙ', 'оранжево-золотистый',
    'dev-ppr-warn', 'столбце «Дата»', '_barExpMaxH', 'рамка зелёная',
    'галочка отметки', 'Работы на месяц', 'перенос-метка',
    'kipia-v514'
]);

console.log('\n== От iVstr (тесты 471/472 используют v-строку) ==');
lastAnchors(iVstr, ['Task 471', 'Task 472', 'Работы на месяц']);
