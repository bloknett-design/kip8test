#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 493 — бамп SW-версий в тестах kip8test + адаптация подписи «Табель учёта».

Порядок (по прецеденту task492-bump-sw.py):
  1) guards: kipia-test-v717 → kipia-test-v718 (assertFalse «следующей версии нет»)
  2) asserts: kipia-test-v716 → kipia-test-v717 (assertTrue «текущая версия»)
Порядок важен: сначала v717→v718, потом v716→v717 — иначе v717-ассерты
попали бы под второй проход.

Адаптации подписи (кнопка «Табель учёта рабочего времени» → «Табель учёта»,
затронуты ТОЛЬКО кнопки: статическая на page-docs-ios + реестр SUBSECTIONS):
  - tests/test-task321.js: чанк кнопки + regex реестра
  - tests/test-work-schedule.js: regex реестра (блок Task 267)
Каждая замена с count-ассертом (ровно N вхождений).
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, 'tests')

def replace_in(path, old, new, expected):
    with io.open(path, encoding='utf-8') as f:
        src = f.read()
    n = src.count(old)
    if n != expected:
        print('FAIL %s: %r найдено %d, ожидалось %d' % (os.path.basename(path), old, n, expected))
        return False
    if old == new:
        return True
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(src.replace(old, new))
    print('OK   %s: %d × %s → %s' % (os.path.basename(path), n, old, new))
    return True

ok = True

# --- 1) guards v717 → v718, 2) asserts v716 → v717 (все тесты) ---
total_g, total_a = 0, 0
files = sorted(f for f in os.listdir(TESTS) if f.endswith('.js'))
for fn in files:
    p = os.path.join(TESTS, fn)
    with io.open(p, encoding='utf-8') as f:
        src = f.read()
    g, a = src.count('kipia-test-v717'), src.count('kipia-test-v716')
    total_g += g
    total_a += a
    if g:
        ok = replace_in(p, 'kipia-test-v717', 'kipia-test-v718', g) and ok
for fn in files:
    p = os.path.join(TESTS, fn)
    with io.open(p, encoding='utf-8') as f:
        src = f.read()
    a = src.count('kipia-test-v716')
    if a:
        ok = replace_in(p, 'kipia-test-v716', 'kipia-test-v717', a) and ok
print('GUARDS v717→v718: %d, ASSERTS v716→v717: %d' % (total_g, total_a))

# --- 3) test-task321.js: чанк кнопки workScheduleMenuBtn ---
p = os.path.join(TESTS, 'test-task321.js')
ok = replace_in(
    p,
    """        assertTrue(chunk.indexOf('Табель учёта рабочего времени') !== -1,
            'menu-btn-label — новое имя');""",
    """        // Task 493: кнопка переименована короче — «Табель учёта»
        assertTrue(chunk.indexOf('<div class="menu-btn-label">Табель учёта</div>') !== -1,
            'menu-btn-label — «Табель учёта» (Task 493, короче)');""",
    1) and ok

# --- 4) test-task321.js: regex реестра SUBSECTIONS ---
ok = replace_in(
    p,
    """        assertTrue(/'work-schedule':\\s*\\{ label: 'Табель учёта рабочего времени'/.test(INDEX_SRC),
            'SUBSECTIONS: новая метка (закрепление на главной)');""",
    """        assertTrue(/'work-schedule':\\s*\\{ label: 'Табель учёта'/.test(INDEX_SRC),
            'SUBSECTIONS: метка «Табель учёта» (Task 493 — закрепление на главной)');""",
    1) and ok

# --- 5) test-work-schedule.js: regex реестра (блок Task 267) ---
p = os.path.join(TESTS, 'test-work-schedule.js')
ok = replace_in(
    p,
    """            const re = /'work-schedule':\\s*\\{ label: 'Табель учёта рабочего времени',\\s*sublabel: 'Шахматка сменного и дневного персонала',\\s*target: 'work-schedule',\\s*category: 'docs' \\}/;""",
    """            // Task 493: label короче — «Табель учёта» (кнопка; заголовок
            // страницы/крошки остались полными)
            const re = /'work-schedule':\\s*\\{ label: 'Табель учёта',\\s*sublabel: 'Шахматка сменного и дневного персонала',\\s*target: 'work-schedule',\\s*category: 'docs' \\}/;""",
    1) and ok

print('RESULT: %s' % ('OK' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
