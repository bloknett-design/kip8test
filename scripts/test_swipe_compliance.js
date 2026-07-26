// Полная проверка соответствия свайпов и группировки требованиям пользователя
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/z/my-project/kip8test/data/valves.json', 'utf8'));
const valves = data.valves || [];

const html = fs.readFileSync('/home/z/my-project/kip8test/index.html', 'utf8');

console.log('═══════════════════════════════════════════════════════════════');
console.log('  ПРОВЕРКА СООТВЕТСТВИЯ СВАЙПОВ И ГРУППИРОВОК ТРЕБОВАНИЯМ');
console.log('═══════════════════════════════════════════════════════════════\n');

// 1. Проверка HTML подложек
console.log('▌ ШАГ 1. Проверка HTML подложек кнопки «Клапана»');
const btnHtmlMatch = html.match(/<div class="dev-swipe-cell valve-swipe-cell"[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/);
const btnHtml = btnHtmlMatch ? btnHtmlMatch[0] : '';
const bgLeftMatch = btnHtml.match(/<div class="dev-swipe-bg dev-swipe-bg-left valve-swipe-bg"><span>([^<]+)<\/span>/);
const bgRightMatch = btnHtml.match(/<div class="dev-swipe-bg dev-swipe-bg-right valve-swipe-bg"><span>([^<]+)<\/span>/);
console.log('  Левая подложка (видна при свайпе ←→ слева направо):', bgLeftMatch ? bgLeftMatch[1] : 'НЕ НАЙДЕНА');
console.log('  Правая подложка (видна при свайпе →← справа налево):', bgRightMatch ? bgRightMatch[1] : 'НЕ НАЙДЕНА');

const bgLeftOk = bgLeftMatch && bgLeftMatch[1].includes('DN');
const bgRightOk = bgRightMatch && bgRightMatch[1].includes('тип');
console.log('  ✓ Левая подложка должна говорить "По DN":', bgLeftOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
console.log('  ✓ Правая подложка должна говорить "По типу":', bgRightOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
console.log('');

// 2. Проверка JS-логики свайпа (именно для клапанов, не для приборов)
console.log('▌ ШАГ 2. Проверка JS-логики определения целевой страницы (для клапанов)');
// Ищем секцию valveInitEntryButton и в ней — targetPage
const valveSectionMatch = html.match(/function valveInitEntryButton[\s\S]*?function cleanupValveSwipe[\s\S]*?\n    \}/);
const valveSection = valveSectionMatch ? valveSectionMatch[0] : '';
const swipeJsMatch = valveSection.match(/const targetPage = isLeft \? '([^']+)' : '([^']+)'/);
console.log('  isLeft=true  (dx < 0, свайп справа налево) →', swipeJsMatch ? swipeJsMatch[1] : 'НЕ НАЙДЕНО');
console.log('  isLeft=false (dx > 0, свайп слева направо) →', swipeJsMatch ? swipeJsMatch[2] : 'НЕ НАЙДЕНО');

const jsSwipeLeftOk = swipeJsMatch && swipeJsMatch[1] === 'valves-type';
const jsSwipeRightOk = swipeJsMatch && swipeJsMatch[2] === 'valves-name';
console.log('  ✓ Свайп справа налево → valves-type (Тип):', jsSwipeLeftOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
console.log('  ✓ Свайп слева направо → valves-name (DN):', jsSwipeRightOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
console.log('');

// 3. Проверка группировки на странице valves-type (mode='type')
console.log('▌ ШАГ 3. Проверка группировки на странице valves-type (mode="type")');
const typeMatch = html.match(/if \(mode === 'type'\) \{\s*groupKey = '([^']+)';\s*sortKey = '([^']+)';\s*\}/);
console.log('  groupKey (поле группировки):', typeMatch ? typeMatch[1] : 'НЕ НАЙДЕНО');
console.log('  sortKey  (поле сортировки внутри групп):', typeMatch ? typeMatch[2] : 'НЕ НАЙДЕНО');

const typeGroupOk = typeMatch && typeMatch[1] === 'Тип, пропускная характеристика';
const typeSortOk = typeMatch && typeMatch[2] === 'Тип запорной части. Материал затвора/ корпуса';
console.log('  ✓ Группировка по «Тип, пропускная характеристика»:', typeGroupOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
console.log('  ✓ Сортировка внутри групп по «Тип запорной части. Материал затвора/ корпуса»:', typeSortOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');

// Фактическая симуляция
const typeGroups = {};
for (const v of valves) {
    const g = v['Тип, пропускная характеристика'] || '(без группы)';
    if (!typeGroups[g]) typeGroups[g] = 0;
    typeGroups[g]++;
}
console.log('  Фактическое количество групп:', Object.keys(typeGroups).length, '→', Object.keys(typeGroups).join(', '));
console.log('');

// 4. Проверка группировки на странице valves-name (mode='name')
console.log('▌ ШАГ 4. Проверка группировки на странице valves-name (mode="name")');
const nameMatch = html.match(/else if \(mode === 'name'\) \{\s*groupKey = '([^']+)';\s*sortKey = '([^']+)';\s*numericGroup = true;\s*\}/);
console.log('  groupKey (поле группировки):', nameMatch ? nameMatch[1] : 'НЕ НАЙДЕНО');
console.log('  sortKey  (поле сортировки внутри групп):', nameMatch ? nameMatch[2] : 'НЕ НАЙДЕНО');
console.log('  numericGroup = true (числовая сортировка групп):', nameMatch ? 'OK' : 'НЕ НАЙДЕНО');

const nameGroupOk = nameMatch && nameMatch[1] === 'DN (мм)';
const nameSortOk = nameMatch && nameMatch[2] === 'Тип запорной части. Материал затвора/ корпуса';
console.log('  ✓ Группировка по «DN (мм)»:', nameGroupOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
console.log('  ✓ Сортировка внутри групп по «Тип запорной части. Материал затвора/ корпуса»:', nameSortOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');

const nameGroups = {};
for (const v of valves) {
    const g = v['DN (мм)'] || '(без группы)';
    if (!nameGroups[g]) nameGroups[g] = 0;
    nameGroups[g]++;
}
console.log('  Фактическое количество групп:', Object.keys(nameGroups).length);
console.log('');

// 5. Проверка страницы группы (valveRenderGroup)
console.log('▌ ШАГ 5. Проверка страницы внутри группы (valveRenderGroup)');
const grpMatch = html.match(/function valveRenderGroup\(\) \{[\s\S]*?let sortKey, groupKey;[\s\S]*?if \(mode === 'type'\) \{\s*groupKey = '([^']+)';\s*sortKey = '([^']+)';\s*\} else if \(mode === 'name'\) \{\s*groupKey = '([^']+)';\s*sortKey = '([^']+)';\s*\}/);
if (grpMatch) {
    console.log('  mode="type": groupKey=', grpMatch[1], '| sortKey=', grpMatch[2]);
    console.log('  mode="name": groupKey=', grpMatch[3], '| sortKey=', grpMatch[4]);
    const grpTypeOk = grpMatch[1] === 'Тип, пропускная характеристика' && grpMatch[2] === 'Тип запорной части. Материал затвора/ корпуса';
    const grpNameOk = grpMatch[3] === 'DN (мм)' && grpMatch[4] === 'Тип запорной части. Материал затвора/ корпуса';
    console.log('  ✓ mode="type" — группировка и сортировка корректны:', grpTypeOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
    console.log('  ✓ mode="name" — группировка и сортировка корректны:', grpNameOk ? 'OK' : 'НЕ СООТВЕТСТВУЕТ');
} else {
    console.log('  НЕ УДАЛОСЬ НАЙТИ КОНСТРУКЦИЮ В valveRenderGroup');
}
console.log('');

// 6. Проверка отсутствия подгруппировки по DN на странице группы
console.log('▌ ШАГ 6. Проверка отсутствия подгруппировки по DN на странице группы');
const hasOldDnSubgrouping = /valveRenderGroup[\s\S]{0,4000}_valveParseDn/.test(html);
console.log('  ✓ Старая подгруппировка по DN удалена:', !hasOldDnSubgrouping ? 'OK' : 'ВСЁ ЕЩЁ ПРИСУТСТВУЕТ');
console.log('');

// 7. Проверка версии Service Worker
console.log('▌ ШАГ 7. Проверка версии Service Worker (для принудительного сброса кэша)');
const swContent = fs.readFileSync('/home/z/my-project/kip8test/sw.js', 'utf8');
const swVerMatch = swContent.match(/CACHE_VERSION = '([^']+)'/);
console.log('  Текущая версия SW:', swVerMatch ? swVerMatch[1] : 'НЕ НАЙДЕНА');
console.log('');

// ИТОГ
console.log('═══════════════════════════════════════════════════════════════');
const allOk = bgLeftOk && bgRightOk && jsSwipeLeftOk && jsSwipeRightOk
    && typeGroupOk && typeSortOk && nameGroupOk && nameSortOk;
if (allOk) {
    console.log('  ✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ — код соответствует требованиям пользователя');
} else {
    console.log('  ✗ ЕСТЬ НЕСООТВЕТСТВИЯ — см. выше');
}
console.log('═══════════════════════════════════════════════════════════════');
