#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 389: адаптация тестов под новые реалии (5 файлов):
#   test-task380.js — .ws-ep-past теперь transparent (общий фон
#     окна, заявка Task 389), а не «светлее окна»;
#   test-task381.js — регресс-тинты: прошедшие transparent,
#     текущие/будущие rgba НЕ тронуты;
#   test-task385.js — кнопка «Добавить работника» ПЕРЕНЕСЕНА из
#     шапки страницы #page-ws-workers на «Общую» вкладку;
#   test-task386.js — пустое состояние: новый текст подсказки
#     (кнопка на «Общей» вкладке, не в шапке);
#   test-task388.js — имя регресс-теста кнопки (место — «Общая»
#     вкладка; ассерты те же — id/текст живут в _renderWorkersGeneral).

def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: адаптировано правок: %d' % (path, len(repls)))


# ---------- test-task380.js ----------
patch('tests/test-task380.js', [
    ('прошедшие тёмная — transparent', """    test('.ws-ep-past: СВЕТЛЫЙ фон (тёмная тема)', () => {
        const re = /\\.ws-ep-item\\.ws-ep-past \\{[^}]*background:\\s*rgba\\(255, 255, 255, 0\\.12\\);[^}]*\\}/;
        assertTrue(re.test(INDEX_SRC),
            'прошедшие: rgba(255,255,255,0.12) — СВЕТЛЕЕ окна #0e1621');
    });
""", """    test('.ws-ep-past: ПРОЗРАЧНЫЙ — общий фон окна (Task 389)', () => {
        const re = /\\.ws-ep-item\\.ws-ep-past \\{[^}]*background:\\s*transparent;[^}]*\\}/;
        assertTrue(re.test(INDEX_SRC),
            'прошедшие: transparent — виден ОБЩИЙ ФОН окна var(--bg-tertiary), как выше оглавления (Task 389)');
    });
""", 1),
    ('прошедшие светлая — transparent', """    test('светлая тема: .ws-ep-past СВЕТЛЫЙ', () => {
        const re = /\\[data-theme="light"\\] \\.ws-ep-item\\.ws-ep-past \\{[^}]*background:\\s*rgba\\(255, 255, 255, 0\\.55\\);[^}]*\\}/;
        assertTrue(re.test(INDEX_SRC),
            'светлая тема: прошедшие rgba(255,255,255,0.55) — светлее окна');
    });
""", """    test('светлая тема: .ws-ep-past ПРОЗРАЧНЫЙ (Task 389)', () => {
        const re = /\\[data-theme="light"\\] \\.ws-ep-item\\.ws-ep-past \\{[^}]*background:\\s*transparent;[^}]*\\}/;
        assertTrue(re.test(INDEX_SRC),
            'светлая тема: прошедшие transparent — общий фон окна (Task 389)');
    });
""", 1),
])

# ---------- test-task381.js ----------
patch('tests/test-task381.js', [
    ('регресс-тинты: прошедшие transparent', """    test('регресс: тинты Task 380 не тронуты', () => {
        assertTrue(/\\.ws-ep-item\\.ws-ep-past \\{[^}]*rgba\\(255, 255, 255, 0\\.12\\)/.test(INDEX_SRC),
            'прошедшие тёмная — 0.12');
        assertTrue(/\\[data-theme="light"\\] \\.ws-ep-item \\{[^}]*rgba\\(0, 0, 0, 0\\.12\\)/.test(INDEX_SRC),
            'текущие светлая — 0.12');
        assertTrue(/\\[data-theme="light"\\] \\.ws-ep-item\\.ws-ep-past \\{[^}]*rgba\\(255, 255, 255, 0\\.55\\)/.test(INDEX_SRC),
            'прошедшие светлая — 0.55');
    });
""", """    test('регресс: тинты Task 380 — текущие/будущие живы; прошедшие — Task 389 transparent', () => {
        assertTrue(/\\.ws-ep-item\\.ws-ep-past \\{[^}]*background:\\s*transparent;/.test(INDEX_SRC),
            'прошедшие тёмная — transparent (Task 389: общий фон окна)');
        assertTrue(/\\[data-theme="light"\\] \\.ws-ep-item \\{[^}]*rgba\\(0, 0, 0, 0\\.12\\)/.test(INDEX_SRC),
            'текущие светлая — 0.12');
        assertTrue(/\\[data-theme="light"\\] \\.ws-ep-item\\.ws-ep-past \\{[^}]*background:\\s*transparent;/.test(INDEX_SRC),
            'прошедшие светлая — transparent (Task 389)');
    });
""", 1),
])

# ---------- test-task385.js ----------
patch('tests/test-task385.js', [
    ('кнопка НЕ в шапке страницы (Task 389)', """        assertTrue(chunk.indexOf('id="wsWorkersAddBtn"') !== -1, 'кнопка добавления в шапке');
        assertTrue(chunk.indexOf('WorkSchedule.openEmployeeForm()') !== -1,
            'кнопка → шторка создания (openEmployeeForm)');
        assertTrue(chunk.indexOf('>Добавить работника</button>') !== -1,
            'текст «Добавить работника» (Task 386: прежде значок «+»)');
        assertTrue(chunk.indexOf('id="wsWorkersBody"') !== -1, 'тело #wsWorkersBody');
        assertTrue(chunk.indexOf('aria-label="Добавить работника"') !== -1,
            'aria-подпись кнопки');
""", """        // Task 389: кнопка «Добавить работника» ПЕРЕНЕСЕНА из шапки
        // страницы на «Общую» вкладку (рендерит _renderWorkersGeneral)
        assertTrue(chunk.indexOf('id="wsWorkersAddBtn"') === -1,
            'кнопки добавления в шапке страницы НЕТ (Task 389)');
        assertTrue(INDEX_SRC.indexOf('WorkSchedule.openEmployeeForm()') !== -1,
            'кнопка → шторка создания (openEmployeeForm)');
        assertTrue(INDEX_SRC.indexOf('>Добавить работника</button>') !== -1,
            'текст «Добавить работника» (Task 386: прежде значок «+»)');
        assertTrue(chunk.indexOf('id="wsWorkersBody"') !== -1, 'тело #wsWorkersBody');
        assertTrue(INDEX_SRC.indexOf('aria-label="Добавить работника"') !== -1,
            'aria-подпись кнопки');
""", 1),
])

# ---------- test-task386.js ----------
patch('tests/test-task386.js', [
    ('пустое состояние — новый текст (кнопка на «Общей» вкладке)', """    test('SRC: пустое состояние — «Добавить работника»', () => {
        assertTrue(INDEX_SRC.indexOf(
            'Добавьте первого кнопкой «Добавить работника» в шапке страницы.') !== -1,
            'подсказка озвучивает новую кнопку');
        assertTrue(INDEX_SRC.indexOf('Добавьте их кнопкой «+» в шапке страницы.') === -1,
            'старая подсказка про «+» убрана');
    });
""", """    test('SRC: пустое состояние — «Добавить работника»', () => {
        // Task 389: подсказка переозвучена — кнопка на «Общей» вкладке
        assertTrue(INDEX_SRC.indexOf(
            'Нет активных работников — добавьте первого кнопкой «Добавить работника».') !== -1,
            'подсказка озвучивает кнопку «Общей» вкладки');
        assertTrue(INDEX_SRC.indexOf(
            'Добавьте первого кнопкой «Добавить работника» в шапке страницы.') === -1,
            'старая подсказка про шапку страницы убрана (Task 389)');
        assertTrue(INDEX_SRC.indexOf('Добавьте их кнопкой «+» в шапке страницы.') === -1,
            'старая подсказка про «+» убрана');
    });
""", 1),
])

# ---------- test-task388.js ----------
patch('tests/test-task388.js', [
    ('имя регресса кнопки — «Общая» вкладка (Task 389)', """    test('HTML: кнопка «Добавить работника» в шапке жива (регресс 386)', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsWorkersAddBtn"') !== -1 &&
                   INDEX_SRC.indexOf('>Добавить работника</button>') !== -1,
            'кнопка добавления на месте');
    });
""", """    test('HTML: кнопка «Добавить работника» жива (регресс 386; Task 389 — на «Общей» вкладке)', () => {
        assertTrue(INDEX_SRC.indexOf('id="wsWorkersAddBtn"') !== -1 &&
                   INDEX_SRC.indexOf('>Добавить работника</button>') !== -1,
            'кнопка добавления на месте (рендер _renderWorkersGeneral)');
    });
""", 1),
])

print('Task 389: адаптация тестов завершена.')
