#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 390: адаптация ЖИВЫХ тестов под новую реальность (заявка):
#   - test-task385.js: HOST_METHODS += _isMasterKipia (шапка «Общей»
#     вкладки теперь считает мастеров по должности);
#   - test-task388.js: VM-харнесс += _isMasterKipia; _plural-мок
#     заменён на РЕАЛЬНОЕ склонение (forms[0] ломал новые строки
#     «N мастеров; N дневных; N сменных»); счётчик «3 » → категории;
#     «сменных — 2/дневных — 1» сноски → категории в шапке + сноска
#     удалена; «10 день» → «10 дней» (реальное склонение);
#   - test-task389.js: VM-харнесс += _isMasterKipia; формулировки
#     шапки (штат/текущий момент) — по заявке Task 390; CSS-ассерты
#     ярлыков (тёплые светлые цвета тёмной темы).

def patch(path, repls):
    s = open(path, encoding='utf-8').read()
    applied = 0
    for i, (old, new) in enumerate(repls, 1):
        n = s.count(old)
        if n == 0 and new in s:
            print('%s REPL %d: уже применён' % (path, i))
            continue
        assert n == 1, '%s REPL %d: найдено %d вхождений' % (path, i, n)
        s = s.replace(old, new)
        applied += 1
    open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d правок' % (path, applied))


# ---------- test-task385.js ----------
patch('tests/test-task385.js', [
(
"""        '_vacSplitDays', '_parseIsoLocal',
    ];""",
"""        '_vacSplitDays', '_parseIsoLocal',
        // Task 390: подсчёт мастеров в шапке «Общей» вкладки
        '_isMasterKipia',
    ];"""
),
# склонение счётчика: работник → категории (Task 390)
(
"""        const gen = methodText(INDEX_SRC, '_renderWorkersGeneral');
        assertTrue(gen.indexOf("['работник', 'работника', 'работников']") !== -1,
            'склонение счётчика (в «Общей»)');""",
"""        const gen = methodText(INDEX_SRC, '_renderWorkersGeneral');
        // Task 390: счётчик — категории с собственными склонениями
        assertTrue(gen.indexOf("['мастер', 'мастера', 'мастеров']") !== -1,
            'склонения счётчика категорий (в «Общей»; Task 390)');"""
),
])


# ---------- test-task388.js ----------
patch('tests/test-task388.js', [
# харнесс: реальный метод _isMasterKipia
(
"""        const host = new Function('document', 'return ({' +
            methodText(INDEX_SRC, '_renderWorkersPage') + ',\\n' +
            methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\\n' +
            methodText(INDEX_SRC, 'selectWorkersTab') + ',\\n' +""",
"""        const host = new Function('document', 'return ({' +
            methodText(INDEX_SRC, '_renderWorkersPage') + ',\\n' +
            methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\\n' +
            methodText(INDEX_SRC, 'selectWorkersTab') + ',\\n' +
            // Task 390: шапка «Общей» вкладки считает мастеров
            methodText(INDEX_SRC, '_isMasterKipia') + ',\\n' +"""
),
# харнесс: реальное склонение (мок forms[0] ломает строки Task 390)
(
"""            '_plural: function(n, forms) { return forms[0]; },' +""",
"""            '_plural: ' + pluralRu + ',' +"""
),
# вставка pluralRu перед VM-блоком
(
"""describe('Task 388 — VM: страница «Работники» — вкладки', () => {""",
"""// Русские склонения (Task 390: харнесс использует РЕАЛЬНОЕ
// правило — строки шапки «Общей» вкладки со склонениями категорий)
function pluralRu(n, forms) {
    return forms[(n % 10 === 1 && n % 100 !== 11) ? 0 :
        (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) ? 1 : 2];
}

describe('Task 388 — VM: страница «Работники» — вкладки', () => {"""
),
# счётчик «3 » → категории (Task 390)
(
"""        assertTrue(body.indexOf('3 ') !== -1, 'трое работников в счётчике');""",
"""        // Task 390: счётчик — по категориям (мастера/дневные/сменные)
        assertTrue(body.indexOf('0 мастеров; 1 дневной; 2 сменных') !== -1,
            'шапка: 0 мастеров; 1 дневной; 2 сменных');"""
),
# сноска «Сводка…» → категории в шапке + сноска удалена
(
"""        // примечание со счётчиком типов
        assertTrue(html.indexOf('сменных — 2') !== -1 &&
                   html.indexOf('дневных — 1') !== -1,
            'примечание: сменных 2, дневных 1');""",
"""        // Task 390: счётчик категорий — в ШАПКЕ (сноска удалена)
        assertTrue(html.indexOf('0 мастеров; 1 дневной; 2 сменных') !== -1,
            'шапка: 0 мастеров; 1 дневной; 2 сменных');
        assertTrue(html.indexOf('ws-wgen-note') === -1,
            'сноска-примечание удалена (Task 390)');"""
),
# реальное склонение: «10 день» → «10 дней»
(
"""        assertTrue(ivanovRow.indexOf('>10 день<') !== -1 ||
                   ivanovRow.indexOf('10 день') !== -1,
            'отпуск Иванова — 10 (дней)');""",
"""        assertTrue(ivanovRow.indexOf('10 дней') !== -1,
            'отпуск Иванова — 10 (дней, реальное склонение)');"""
),
])


# ---------- test-task389.js ----------
patch('tests/test-task389.js', [
# харнесс: реальный метод _isMasterKipia
(
"""    const host = new Function('document', 'return ({' +
        methodText(INDEX_SRC, '_renderWorkersPage') + ',\\n' +
        methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\\n' +
        methodText(INDEX_SRC, 'selectWorkersTab') + ',\\n' +""",
"""    const host = new Function('document', 'return ({' +
        methodText(INDEX_SRC, '_renderWorkersPage') + ',\\n' +
        methodText(INDEX_SRC, '_renderWorkersGeneral') + ',\\n' +
        methodText(INDEX_SRC, 'selectWorkersTab') + ',\\n' +
        // Task 390: шапка «Общей» вкладки считает мастеров
        methodText(INDEX_SRC, '_isMasterKipia') + ',\\n' +"""
),
# SRC: формулировка текущего момента (Task 390)
(
"""    test('«На текущий момент: N …» — АВТОМАТИЧЕСКИЙ ПОДСЧЁТ', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersGeneral'));
        assertTrue(fn.indexOf('На текущий момент: ') !== -1,
            'формулировка «На текущий момент:»');
        assertTrue(fn.indexOf('list.length') !== -1,
            'число — list.length (живой список, автоподсчёт)');
        assertTrue(fn.indexOf("['работник', 'работника', 'работников']") !== -1,
            'склонение через _plural');
        assertTrue(fn.indexOf('(автоматический подсчёт).') !== -1,
            'пометка «(автоматический подсчёт)»');
    });""",
"""    test('«Работников на текущий момент: …» — АВТОПОДСЧЁТ ПО КАТЕГОРИЯМ (Task 390)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersGeneral'));
        assertTrue(fn.indexOf('Работников на текущий момент: ') !== -1,
            'формулировка «Работников на текущий момент:» (Task 390)');
        assertTrue(fn.indexOf('this._isMasterKipia(cEmp)') !== -1,
            'мастера — по должности «Мастер КИПиА» (_isMasterKipia)');
        assertTrue(fn.indexOf("['мастер', 'мастера', 'мастеров']") !== -1 &&
                   fn.indexOf("['дневной', 'дневных', 'дневных']") !== -1 &&
                   fn.indexOf("['сменный', 'сменных', 'сменных']") !== -1,
            'склонения категорий через _plural');
        assertTrue(fn.indexOf('На текущий момент:') === -1 &&
                   fn.indexOf('(автоматический подсчёт)') === -1,
            'старые формулировки удалены');
    });"""
),
# SRC: формулировка штата (Task 390)
(
"""    test('«По штату: 14, из которых 2 мастера, 5 сменных и 7 дневных»', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersGeneral'));
        assertTrue(fn.indexOf('По штату: 14, из которых') !== -1,
            'константа штата: 14');
        assertTrue(fn.indexOf('2 мастера, 5 сменных и 7 дневных.') !== -1,
            'структура: 2 мастера / 5 сменных / 7 дневных');
        assertTrue(fn.indexOf('ws-wgen-staff') !== -1,
            'класс строки штата');
        assertTrue(fn.indexOf('ws-wgen-info') !== -1,
            'инфо-блок шапки сводки');
        assertTrue(fn.indexOf('ws-workers-count') !== -1,
            'счётчик — прежний класс (стили живы)');
    });""",
"""    test('«Работников по штату 14: 2 мастера; 7 дневных; 5 сменных.» (Task 390)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_renderWorkersGeneral'));
        assertTrue(fn.indexOf('Работников по штату 14: ') !== -1,
            'константа штата: 14 (Task 390)');
        assertTrue(fn.indexOf('2 мастера; 7 дневных; 5 сменных.') !== -1,
            'структура: 2 мастера / 7 дневных / 5 сменных');
        assertTrue(fn.indexOf('ws-wgen-staff') !== -1,
            'класс строки штата');
        assertTrue(fn.indexOf('ws-wgen-info') !== -1,
            'инфо-блок шапки сводки');
        assertTrue(fn.indexOf('ws-workers-count') !== -1,
            'счётчик — прежний класс (стили живы)');
        assertTrue(fn.indexOf('По штату: 14, из которых') === -1,
            'старая формулировка удалена');
    });"""
),
# SRC: CSS неактивного ярлыка — тёплый светлый (Task 390)
(
"""    test('.ws-wtab: СПЛОШНОЙ фон неактивного ярлыка', () => {
        const b = ruleBlock('.ws-wtab {');
        assertTrue(b !== null, 'правило живо');
        assertTrue(b.indexOf('background: var(--bg-primary, #1a2233);') !== -1,
            'тёмная: сплошной var(--bg-primary) — НЕ rgba-тинт');
        assertFalse(/background:\\s*rgba\\(/.test(b),
            'в правиле .ws-wtab нет полупрозрачных фонов');
    });""",
"""    test('.ws-wtab: СПЛОШНОЙ фон неактивного ярлыка', () => {
        const b = ruleBlock('.ws-wtab {');
        assertTrue(b !== null, 'правило живо');
        assertTrue(b.indexOf('background: #4B4E46;') !== -1,
            'тёмная (Task 390): тёплый #4B4E46 — светлее фона страницы, ближе к светлой теме');
        assertFalse(/background:\\s*rgba\\(/.test(b),
            'в правиле .ws-wtab нет полупрозрачных фонов');
    });"""
),
# SRC: CSS hover (Task 390)
(
"""    test('.ws-wtab:hover: сплошной светлее', () => {
        const b = ruleBlock('.ws-wtab:hover {');
        assertTrue(b !== null && b.indexOf('background: #243048;') !== -1,
            'тёмная: сплошной #243048');
    });""",
"""    test('.ws-wtab:hover: сплошной светлее', () => {
        const b = ruleBlock('.ws-wtab:hover {');
        assertTrue(b !== null && b.indexOf('background: #575A50;') !== -1,
            'тёмная (Task 390): тёплый #575A50');
    });"""
),
# VM: тексты шапки (редактор)
(
"""        assertTrue(body.indexOf('На текущий момент: 3 работника (автоматический подсчёт).') !== -1,
            'автоподсчёт: «На текущий момент: 3 работника (автоматический подсчёт).»');
        assertTrue(body.indexOf('По штату: 14, из которых 2 мастера, 5 сменных и 7 дневных.') !== -1,
            'штат: 14 = 2 мастера + 5 сменных + 7 дневных');""",
"""        assertTrue(body.indexOf('Работников на текущий момент: 0 мастеров; 1 дневной; 2 сменных.') !== -1,
            'автоподсчёт (Task 390): 0 мастеров; 1 дневной; 2 сменных');
        assertTrue(body.indexOf('Работников по штату 14: 2 мастера; 7 дневных; 5 сменных.') !== -1,
            'штат: 14 = 2 мастера + 7 дневных + 5 сменных');"""
),
# VM: тексты шапки (зритель)
(
"""        assertTrue(body.indexOf('На текущий момент: 3 работника') !== -1 &&
                   body.indexOf('По штату: 14') !== -1,
            'информация доступна всем');""",
"""        assertTrue(body.indexOf('Работников на текущий момент:') !== -1 &&
                   body.indexOf('Работников по штату 14') !== -1,
            'информация доступна всем');"""
),
# VM: пустой список
(
"""        assertTrue(body.indexOf('На текущий момент: 0 работников (автоматический подсчёт).') !== -1,
            'автоподсчёт нуля');""",
"""        assertTrue(body.indexOf('Работников на текущий момент: 0 мастеров; 0 дневных; 0 сменных.') !== -1,
            'автоподсчёт нуля (Task 390)');"""
),
# VM: прямой вызов с 2 работниками
(
"""        assertTrue(html.indexOf('На текущий момент: 2 работника (автоматический подсчёт).') !== -1,
            'число = длине переданного списка (2 работника)');""",
"""        assertTrue(html.indexOf('Работников на текущий момент: 0 мастеров; 1 дневной; 1 сменный.') !== -1,
            'категории переданного списка: 0 мастеров; 1 дневной; 1 сменный (Task 390)');"""
),
])

print('task390-adapt-tests: готово')
