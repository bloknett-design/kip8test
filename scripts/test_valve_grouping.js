// Симуляция valveRenderSorted для проверки группировки и сортировки
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/home/z/my-project/kip8test/data/valves.json', 'utf8'));
const valves = data.valves || [];

function simulate(mode) {
    let sortKey, groupKey, numericGroup = false;
    if (mode === 'type') {
        groupKey = 'Тип, пропускная характеристика';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
    } else if (mode === 'name') {
        groupKey = 'DN (мм)';
        sortKey = 'Тип запорной части. Материал затвора/ корпуса';
        numericGroup = true;
    } else {
        sortKey = 'Производство';
        groupKey = 'Производство';
    }

    let filtered = valves.slice();
    filtered.sort((a, b) => {
        const va = (a[sortKey] || '').toString();
        const vb = (b[sortKey] || '').toString();
        const la = va.toLowerCase(), lb = vb.toLowerCase();
        if (la < lb) return -1;
        if (la > lb) return 1;
        const ma = (a['Марка'] || '').toString().toLowerCase();
        const mb = (b['Марка'] || '').toString().toLowerCase();
        return ma.localeCompare(mb);
    });

    const groups = {};
    const groupOrder = [];
    for (const d of filtered) {
        const g = d[groupKey] || '(без группы)';
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(d);
    }
    if (numericGroup) {
        groupOrder.sort((a, b) => {
            if (a === '(без группы)' && b === '(без группы)') return 0;
            if (a === '(без группы)') return 1;
            if (b === '(без группы)') return -1;
            const na = parseFloat(a.replace(',', '.'));
            const nb = parseFloat(b.replace(',', '.'));
            if (isNaN(na) && isNaN(nb)) return a.toLowerCase().localeCompare(b.toLowerCase());
            if (isNaN(na)) return 1;
            if (isNaN(nb)) return -1;
            if (na !== nb) return na - nb;
            return 0;
        });
    }

    console.log('\n=== mode =', mode, '===');
    console.log('groupKey:', groupKey);
    console.log('sortKey (внутри группы):', sortKey);
    console.log('Количество групп:', groupOrder.length);
    console.log('Порядок групп (первые 10):');
    groupOrder.slice(0, 10).forEach((g, i) => {
        console.log('  ' + (i+1) + '. [' + g + '] — ' + groups[g].length + ' шт.');
    });
    // Покажем сортировку внутри первой группы
    if (groupOrder.length > 0) {
        const firstGroup = groupOrder[0];
        const items = groups[firstGroup].slice(0, 5);
        console.log('Первые 5 элементов в группе [' + firstGroup + ']:');
        items.forEach((it, i) => {
            console.log('  ' + (i+1) + '. Марка="' + (it['Марка'] || '') + '" | ' +
                sortKey + '="' + (it[sortKey] || '') + '" | ' +
                groupKey + '="' + (it[groupKey] || '') + '"');
        });
    }
}

simulate('type');
simulate('name');
simulate('prod');
