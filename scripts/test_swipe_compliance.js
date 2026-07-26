// Полная проверка соответствия свайпов, группировок и заголовков требованиям пользователя
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/z/my-project/kip8test/data/valves.json', 'utf8'));
const valves = data.valves || [];

const html = fs.readFileSync('/home/z/my-project/kip8test/index.html', 'utf8');

console.log('═══════════════════════════════════════════════════════════════');
console.log('  ПРОВЕРКА: СВАЙПЫ, ГРУППИРОВКИ, ЗАГОЛОВКИ, ПОДГРУППЫ');
console.log('═══════════════════════════════════════════════════════════════\n');

let allOk = true;
function check(name, ok, detail) {
    console.log('  ' + (ok ? '✓' : '✗') + ' ' + name + (detail ? ': ' + detail : ''));
    if (!ok) allOk = false;
}

// 1. Заголовки страниц valves-type/name/prod — должны быть «Клапана по …» (ед.ч.)
console.log('▌ 1. Заголовки родительских страниц (должны быть «Клапана по …»)');
const titleType = (html.match(/page-valves-type[\s\S]*?page-inline-header-title">([^<]+)</) || [])[1];
const titleName = (html.match(/page-valves-name[\s\S]*?page-inline-header-title">([^<]+)</) || [])[1];
const titleProd = (html.match(/page-valves-prod[\s\S]*?page-inline-header-title">([^<]+)</) || [])[1];
check('Заголовок page-valves-type', titleType === 'Клапана по типу', titleType);
check('Заголовок page-valves-name', titleName === 'Клапана по DN', titleName);
check('Заголовок page-valves-prod', titleProd === 'Клапана по производствам', titleProd);
console.log('');

// 2. Свайпы: ← → valves-type, → → valves-name
console.log('▌ 2. JS-логика свайпов (для клапанов)');
const valveSection = (html.match(/function valveInitEntryButton[\s\S]*?function cleanupValveSwipe[\s\S]*?\n    \}/) || [''])[0];
const swipeMatch = valveSection.match(/const targetPage = isLeft \? '([^']+)' : '([^']+)'/);
check('Свайп ← (справа налево) → valves-type', swipeMatch[1] === 'valves-type', swipeMatch[1]);
check('Свайп → (слева направо) → valves-name', swipeMatch[2] === 'valves-name', swipeMatch[2]);
console.log('');

// 3. Группировка на родительских страницах (valveRenderSorted)
console.log('▌ 3. Группировка на родительских страницах (valveRenderSorted)');
const fnSorted = (html.match(/function valveRenderSorted\(mode\) \{[\s\S]*?\n    \}/) || [''])[0];
const typeBranch = fnSorted.match(/if \(mode === 'type'\) \{\s*groupKey = '([^']+)';\s*sortKey = '([^']+)';\s*\}/);
const nameBranch = fnSorted.match(/else if \(mode === 'name'\) \{\s*groupKey = '([^']+)';\s*sortKey = '([^']+)';\s*numericGroup = true;\s*\}/);
check('mode=type: groupKey=«Тип, пропускная характеристика»', typeBranch[1] === 'Тип, пропускная характеристика', typeBranch[1]);
check('mode=type: sortKey=«Тип запорной части…»', typeBranch[2] === 'Тип запорной части. Материал затвора/ корпуса', typeBranch[2]);
check('mode=name: groupKey=«DN (мм)»', nameBranch[1] === 'DN (мм)', nameBranch[1]);
check('mode=name: sortKey=«Тип запорной части…»', nameBranch[2] === 'Тип запорной части. Материал затвора/ корпуса', nameBranch[2]);
console.log('');

// 4. Страница группы (valveRenderGroup): заголовок и подгруппы
console.log('▌ 4. Страница группы (valveRenderGroup)');
const fnGroup = (html.match(/function valveRenderGroup\(\) \{[\s\S]*?\n    \}/) || [''])[0];

// 4a. Динамический заголовок для mode='name' → «DN {group} (мм)»
const titleNameLogic = fnGroup.match(/if \(mode === 'name'\) \{\s*pageTitle = group \? \('DN ' \+ group \+ ' \(мм\)'\) : 'Клапана';/);
check('mode=name: заголовок «DN {значение} (мм)»', !!titleNameLogic, titleNameLogic ? 'OK' : 'НЕ НАЙДЕНО');

// 4b. Подгруппировка по sortKey (статичные, всегда раскрытые)
const hasStaticSubgroups = fnGroup.includes('pb-section valve-group valve-subgroup static');
check('Подгруппы по «Тип запорной части» (класс .static)', hasStaticSubgroups, hasStaticSubgroups ? 'OK' : 'НЕ НАЙДЕНО');

// 4c. Подгруппы используют sortKey в качестве поля подгруппировки
const subgroupLoop = fnGroup.match(/const sg = item\[sortKey\] \|\| '\(без подгруппы\)'/);
check('Подгруппировка идёт по sortKey', !!subgroupLoop, subgroupLoop ? 'OK' : 'НЕ НАЙДЕНО');

// 4d. Для mode='prod' тоже используется sortKey = «Тип запорной части…»
const prodBranch = fnGroup.match(/else \{\s*groupKey = 'Производство';\s*sortKey = 'Тип запорной части\. Материал затвора\/ корпуса';\s*\}/);
check('mode=prod: подгруппы по «Тип запорной части…»', !!prodBranch, prodBranch ? 'OK' : 'НЕ НАЙДЕНО');
console.log('');

// 5. Симуляция: для DN 50 — какие подгруппы будут на странице группы?
console.log('▌ 5. Симуляция для группы DN 50 (mode=name)');
const dn50Items = valves.filter(v => String(v['DN (мм)'] || '') === '50');
console.log('  Клапанов DN 50:', dn50Items.length);
const dn50Subgroups = {};
for (const v of dn50Items) {
    const sg = v['Тип запорной части. Материал затвора/ корпуса'] || '(без подгруппы)';
    if (!dn50Subgroups[sg]) dn50Subgroups[sg] = 0;
    dn50Subgroups[sg]++;
}
console.log('  Подгрупп по «Тип запорной части»:', Object.keys(dn50Subgroups).length);
Object.entries(dn50Subgroups).forEach(([sg, n]) => {
    console.log('    • ' + sg + ' — ' + n + ' шт.');
});
console.log('  Ожидаемый заголовок страницы: «DN 50 (мм)»');
console.log('');

// 6. CSS для статичных подгрупп существует
console.log('▌ 6. CSS для статичных подгрупп (.pb-section.static)');
const cssStatic = html.includes('.pb-section.static .pb-section-body') &&
                  html.includes('.pb-section.static .pb-section-arrow');
check('CSS-правила для .pb-section.static присутствуют', cssStatic);
console.log('');

// 7. Версия SW
console.log('▌ 7. Версия Service Worker');
const swContent = fs.readFileSync('/home/z/my-project/kip8test/sw.js', 'utf8');
const swVer = (swContent.match(/CACHE_VERSION = '([^']+)'/) || [])[1];
check('SW версия актуальна (≥ v189)', swVer && parseInt(swVer.match(/v(\d+)/)[1]) >= 189, swVer);
console.log('');

console.log('═══════════════════════════════════════════════════════════════');
console.log(allOk ? '  ✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ' : '  ✗ ЕСТЬ НЕСООТВЕТСТВИЯ');
console.log('═══════════════════════════════════════════════════════════════');
process.exit(allOk ? 0 : 1);
