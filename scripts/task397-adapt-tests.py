#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 397: адаптация существующих тестов под ОБЩЕЕ ПРАВИЛО
# (кнопка раздела без доступа не отображается).
#
# test-role-access.js:
#   · формула видимости кнопки «Документация» нижнего бара — композит
#     docs|library|kip-ios упрощён до docs (Task 397: library влечёт
#     docs — одна группа _LIBRARY_PAGES; kip-ios без library/restricted
#     не открывает page-docs — кнопка вела на «Нет доступа»);
#   · + НОВЫЕ проверки «Инженерные калькуляторы» нижнего бара
#     (прежде «видна всегда» — теперь по доступу) и целого бара
#     (обе кнопки скрыты → бар скрыт).
import io

PATH = 'tests/test-role-access.js'
src = io.open(PATH, encoding='utf-8').read()
n0 = src

def rep(old, new, what, count=1):
    global src
    found = src.count(old)
    assert found == count, '%s: найдено %d (ожидалось %d)' % (what, found, count)
    src = src.replace(old, new)
    print('  ✓ %s' % what)

# --- 1. Формула «Документации»: композит → docs (Task 397) ---
rep(
"""    test('Кнопка «Документация» видна ролям с доступом к docs/library/kip-ios', function () {
        // Формула из _applyRoleToUI: isAll || docs || library || kip-ios
        ROLES.forEach(function (role) {
            const allowed = Kip.ROLE_ACCESS[role] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const expectVisible = isAll
                || allowed.indexOf('docs') !== -1
                || allowed.indexOf('library') !== -1
                || allowed.indexOf('kip-ios') !== -1;
""",
"""    test('Кнопка «Документация» видна ролям с доступом к docs', function () {
        // Task 397 (общее правило): формула из _applyRoleToUI —
        // isAll || docs (композит docs|library|kip-ios упрощён:
        // library влечёт docs — одна группа; kip-ios без library
        // не открывает page-docs — кнопка вела на «Нет доступа»).
        ROLES.forEach(function (role) {
            const allowed = Kip.ROLE_ACCESS[role] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const expectVisible = isAll
                || allowed.indexOf('docs') !== -1;
""", 'формула «Документации» — композит упрощён до docs (ROLES)')

rep(
"""            const allowed = Kip.ROLE_ACCESS[pair[0]] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const actual = isAll
                || allowed.indexOf('docs') !== -1
                || allowed.indexOf('library') !== -1
                || allowed.indexOf('kip-ios') !== -1;
            assertEqual(actual, pair[1],
                'роль «' + pair[0] + '»: кнопка «Документация» нижнего бара');
        });
    });
});
""",
"""            const allowed = Kip.ROLE_ACCESS[pair[0]] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const actual = isAll
                || allowed.indexOf('docs') !== -1;
            assertEqual(actual, pair[1],
                'роль «' + pair[0] + '»: кнопка «Документация» нижнего бара');
        });
    });

    // Task 397 (общее правило): «Инженерные калькуляторы» нижнего
    // бара — прежде «видна всегда», теперь видна ⟺ доступ к разделу.
    test('Кнопка «Инженерные калькуляторы» нижнего бара видна ролям с calculators', function () {
        [['Запрет', false], ['Общий доступ', true], ['ИТР ТОКЕМ', true], ['КИП8', true],
         ['КИП ИОС', true], ['Админ', true]].forEach(function (pair) {
            const allowed = Kip.ROLE_ACCESS[pair[0]] || [];
            const isAll = allowed.indexOf('*') !== -1;
            const actual = isAll || allowed.indexOf('calculators') !== -1;
            assertEqual(actual, pair[1],
                'роль «' + pair[0] + '»: кнопка «Инженерные калькуляторы» нижнего бара');
        });
    });

    test('Нижний бар скрыт целиком, если обе кнопки недоступны («Запрет»)', function () {
        const allowed = Kip.ROLE_ACCESS['Запрет'] || [];
        const isAll = allowed.indexOf('*') !== -1;
        const calcVisible = isAll || allowed.indexOf('calculators') !== -1;
        const docsVisible = isAll || allowed.indexOf('docs') !== -1;
        assertEqual(calcVisible || docsVisible, false,
            '«Запрет»: обе кнопки бара скрыты — бар скрыт целиком');
    });
});
""", 'формула «Документации» (матрица) + калькуляторы + бар целиком')

assert src != n0, 'файл не изменился'
io.open(PATH, 'w', encoding='utf-8').write(src)
print('OK: tests/test-role-access.js адаптирован (2 правки)')
