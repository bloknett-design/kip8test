#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 394: адаптация тестов под изменения заявки:
#   • карточка работника: блок мероприятий — «Мероприятия · ГОД»
#     (было «· Сентябрь 2026»), пустое состояние — «нет мероприятий
#     за год» (было «в месяце») — test-task393.js / test-task309.js;
# Заодно точечная правка наименования теста (косметика).
import glob

EDITS = [
    ('tests/test-task393.js', [
        # VM: заголовок блока мероприятий теперь ГОД (2 вхождения:
        # строка-попап и страница-панели)
        ("        const i3 = html.indexOf('Мероприятия · Сентябрь 2026');\n",
         "        const i3 = html.indexOf('Мероприятия · 2026');\n", 2),
        # VM: блок 3 — заголовок/пустое состояние
        ("    test('блок 3 — мероприятия месяца', () => {",
         "    test('блок 3 — мероприятия года (Task 394)', () => {", 1),
        ("        assertTrue(b.indexOf('Мероприятия · Сентябрь 2026') !== -1, 'заголовок блока (месяц/год)');\n"
         "        assertTrue(b.indexOf('нет мероприятий в месяце') !== -1, 'пустое состояние');\n",
         "        assertTrue(b.indexOf('Мероприятия · 2026') !== -1, 'заголовок блока (год, Task 394)');\n"
         "        assertTrue(b.indexOf('нет мероприятий за год') !== -1, 'пустое состояние (год)');\n", 1),
    ]),
    ('tests/test-task309.js', [
        ("        assertTrue(rp.indexOf('нет мероприятий в месяце') !== -1,\n"
         "            'пустое состояние секции мероприятий');\n",
         "        assertTrue(rp.indexOf('нет мероприятий за год') !== -1,\n"
         "            'пустое состояние секции мероприятий (Task 394: год)');\n", 1),
    ]),
]

total = 0
for fname, reps in EDITS:
    s = open(fname, encoding='utf-8').read()
    for old, new, cnt in reps:
        n = s.count(old)
        if n != cnt:
            print('%s: ЯКОРЬ НЕ НАЙДЕН (%d раз): %r' % (fname, n, old[:70]))
            raise SystemExit(1)
        s = s.replace(old, new)
        total += 1
    open(fname, 'w', encoding='utf-8').write(s)
    print('%s: %d правок' % (fname, len(reps)))
print('Всего правок: %d' % total)
