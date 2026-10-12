#!/usr/bin/env node
// Task 505: проверка JS-синтаксиса всех <script>-блоков index.html
// (приём извлечения: регексп script-блоков без внешних src)
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');
const SRC = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');

const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
let m, n = 0, bad = 0;
while ((m = re.exec(SRC)) !== null) {
    n++;
    const code = m[1];
    if (!code.trim()) continue;
    try {
        new Function(code);
    } catch (e) {
        bad++;
        // приблизительная строка внутри блока
        const pos = m.index;
        const line = SRC.slice(0, pos).split('\n').length;
        console.log('  X script #' + n + ' (html line ~' + line + '): ' + e.message);
    }
}
console.log((bad ? 'FAIL: ' + bad : 'OK: 0') + ' / ' + n + ' inline script blocks');
process.exit(bad ? 1 : 0);
