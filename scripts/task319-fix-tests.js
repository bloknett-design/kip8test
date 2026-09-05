// Task 319: точечная актуализация двух regex-тестов в test-work-schedule.js
// (рендер <tr> перешёл с trCls-строки на массив trClsParts: ws-group-first
// + ws-hover-row перекрестья). Запуск: node scripts/task319-fix-tests.js
const fs = require('fs');
const f = 'tests/test-work-schedule.js';
let s = fs.readFileSync(f, 'utf8');

const old1 = "const re = /var trCls = \\(empTier === 1 && prevTier === 0\\)[\\s\\S]*?' class=\"ws-group-first\"' : '';[\\s\\S]*?html \\+= '<tr' \\+ trCls \\+ '>';/;";
const new1 = "// Task 319: tr собирается из массива классов (trClsParts:\n" +
    "            // ws-group-first + ws-hover-row перекрестья) — актуализация\n" +
    "            const re = /var trClsParts = \\[\\];[\\s\\S]*?if \\(empTier === 1 && prevTier === 0\\) trClsParts\\.push\\('ws-group-first'\\);[\\s\\S]*?trClsParts\\.join\\(' '\\);/";
const old2 = "const re = /var trCls = \\(empTier === 1 && prevTier === 0\\);";
const new2 = "// Task 319: актуализация под trClsParts\n" +
    "            const re = /if \\(empTier === 1 && prevTier === 0\\) trClsParts\\.push\\('ws-group-first'\\);/";

if (!s.includes(old1)) { console.log('OLD1 NOT FOUND'); process.exit(1); }
s = s.replace(old1, new1);
if (!s.includes(old2)) { console.log('OLD2 NOT FOUND'); process.exit(1); }
s = s.replace(old2, new2);
fs.writeFileSync(f, s);
console.log('OK: 2 regexes updated');
