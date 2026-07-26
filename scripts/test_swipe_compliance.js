// Проверка свайпов, группировок, заголовков и подгрупп
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

// 1. Заголовки родительских страниц
console.log('▌ 1. Заголовки родительских страниц (должны быть «Клапана по …»)');
const titleType = (html.match(/page-valves-type[\s\S]*?page-inline-header-title">([^<]+)</) || [])[1];
const titleName = (html.match(/page-valves-name[\s\S]*?page-inline-header-title">([^<]+)</) || [])[1];
const titleProd = (html.match(/page-valves-prod[\s\S]*?page-inline-header-title">([^<]+)</) || [])[1];
check('Заголовок page-valves-type', titleType === 'Клапана по типу', titleType);
check('Заголовок page-valves-name', titleName === 'Клапана по DN', titleName);
check('Заголовок page-valves-prod', titleProd === 'Клапана по производствам', titleProd);
console.log('');

// 2. Свайпы
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
check('mode=name: groupKey=«DN (мм)»', nameBranch[1] === 'DN (мм)', nameBranch[1]);
console.log('');

// 4. Страница группы (valveRenderGroup): заголовок и подгруппы
console.log('▌ 4. Страница группы (valveRenderGroup)');
const fnGroup = (html.match(/function valveRenderGroup\(\) \{[\s\S]*?\n    \}/) || [''])[0];

// 4a. Динамический заголовок для mode='name' → «DN {group} (мм)»
const titleNameLogic = fnGroup.match(/if \(mode === 'name'\) \{\s*pageTitle = group \? \('DN ' \+ group \+ ' \(мм\)'\) : 'Клапана';/);
check('mode=name: заголовок «DN {значение} (мм)»', !!titleNameLogic);

// 4b. Подгруппировка для каждого режима
const prodBranch = fnGroup.match(/else \{\s*\/\/ mode === 'prod'\s*groupKey = 'Производство';\s*subgroupKey = 'DN \(мм\)';\s*sortKey = 'Тип запорной части\. Материал затвора\/ корпуса';\s*numericSubgroups = true;\s*\}/);
check('mode=prod: subgroupKey=«DN (мм)», numericSubgroups=true', !!prodBranch);

const typeSubgroup = fnGroup.match(/if \(mode === 'type'\) \{\s*groupKey = 'Тип, пропускная характеристика';\s*subgroupKey = 'Тип запорной части\. Материал затвора\/ корпуса';/);
check('mode=type: subgroupKey=«Тип запорной части…»', !!typeSubgroup);

const nameSubgroup = fnGroup.match(/else if \(mode === 'name'\) \{\s*groupKey = 'DN \(мм\)';\s*subgroupKey = 'Тип запорной части\. Материал затвора\/ корпуса';/);
check('mode=name: subgroupKey=«Тип запорной части…»', !!nameSubgroup);

// 4c. Подгруппы используют subgroupKey в цикле
const subgroupLoop = fnGroup.match(/const sgRaw = item\[subgroupKey\] \|\| '\(без подгруппы\)'/);
check('Цикл подгруппировки использует subgroupKey', !!subgroupLoop);

// 4d. Заголовок подгруппы для numericSubgroups = «DN {значение}»
const sgLabelLogic = fnGroup.match(/const sgLabel = \(numericSubgroups && sg !== '\(без подгруппы\)'\)\s*\? 'DN ' \+ sg\s*: sg;/);
check('Заголовок числовой подгруппы = «DN {значение}»', !!sgLabelLogic);

// 4e. CSS .pb-section.static присутствует
check('CSS .pb-section.static присутствует',
    html.includes('.pb-section.static .pb-section-body') &&
    html.includes('.pb-section.static .pb-section-arrow'));
console.log('');

// 5. Симуляция для режима prod — какие будут подгруппы для производства?
console.log('▌ 5. Симуляция для режима prod (группировка по производствам, подгруппы по DN)');
const prodGroups = {};
for (const v of valves) {
    const p = v['Производство'] || '(без группы)';
    if (!prodGroups[p]) prodGroups[p] = [];
    prodGroups[p].push(v);
}
// Берём первое производство с большим количеством клапанов
const firstProd = Object.entries(prodGroups).find(([_, items]) => items.length > 5);
if (firstProd) {
    const [prodName, prodItems] = firstProd;
    console.log('  Производство:', prodName, '(' + prodItems.length + ' клапанов)');
    const dnSubgroups = {};
    for (const v of prodItems) {
        const dn = v['DN (мм)'] || '(без подгруппы)';
        if (!dnSubgroups[dn]) dnSubgroups[dn] = 0;
        dnSubgroups[dn]++;
    }
    // Числовая сортировка DN
    const sortedDns = Object.keys(dnSubgroups).sort((a, b) => {
        if (a === '(без подгруппы)') return 1;
        if (b === '(без подгруппы)') return -1;
        const na = parseFloat(a.replace(',', '.'));
        const nb = parseFloat(b.replace(',', '.'));
        if (isNaN(na) && isNaN(nb)) return a.localeCompare(b);
        if (isNaN(na)) return 1;
        if (isNaN(nb)) return -1;
        return na - nb;
    });
    console.log('  Подгруппы по DN (' + sortedDns.length + ' шт.):');
    sortedDns.slice(0, 8).forEach(dn => {
        console.log('    • DN ' + dn + ' — ' + dnSubgroups[dn] + ' шт.');
    });
    if (sortedDns.length > 8) console.log('    ... и ещё ' + (sortedDns.length - 8) + ' подгрупп');
}
console.log('');

// 6. Версия SW
console.log('▌ 6. Версия Service Worker');
const swContent = fs.readFileSync('/home/z/my-project/kip8test/sw.js', 'utf8');
const swVer = (swContent.match(/CACHE_VERSION = '([^']+)'/) || [])[1];
check('SW версия актуальна (≥ v190)', swVer && parseInt(swVer.match(/v(\d+)/)[1]) >= 190, swVer);
console.log('');

console.log('═══════════════════════════════════════════════════════════════');
console.log(allOk ? '  ✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ' : '  ✗ ЕСТЬ НЕСООТВЕТСТВИЯ');
console.log('═══════════════════════════════════════════════════════════════');
process.exit(allOk ? 0 : 1);
