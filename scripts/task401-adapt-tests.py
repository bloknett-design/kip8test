#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 401 — адаптация старых тестов под НОВУЮ разметку шапки
# годовой таблицы итогов (Task 401: шапка ДВУХСТРОЧНАЯ — подстрока
# «дней/часов» под месяцами, «Работник»/итоговые th — rowspan="2",
# итоговые th/td — классы ws-tt-sum/ws-tt-sum-edge).
# Затронуты (жёсткие ассерты на прежние строки):
#   · tests/test-task321.js — <th class="ws-tt-emp">…, <tr>-счёт 4→6,
#     <th>Днев</th>/<th>Часов</th>/<th title=…>Перераб. (дни)</th>;
#   · tests/test-task323.js — <tr>-счёт 4→6 (шапка+подстрока ×2);
#   · tests/test-task333.js — regex <th class="ws-tt-emp"><span … ×2
#     (rowspan добавлен).
import sys

def patch(path, repls):
    src = open(path, encoding='utf-8').read()
    fail = 0
    applied = 0
    for old, new, cnt in repls:
        n = src.count(old)
        if n != cnt:
            # уже применено (повторный запуск) — не ошибка
            if src.count(new) == cnt:
                applied += 1
                continue
            print('ANCHOR FAIL в %s (%d из %d):\n---\n%s\n---' % (path, n, cnt, old[:200]))
            fail += 1
            continue
        src = src.replace(old, new, cnt)
        applied += 1
    if fail:
        return False
    open(path, 'w', encoding='utf-8').write(src)
    print('OK: %s — %d правок' % (path, applied))
    return True

ok = True

# --- test-task321.js: шапка года (rowspan, <tr>-счёт, итоговые th) ---
ok &= patch('tests/test-task321.js', [
(
"""        assertTrue(h.indexOf('<th class="ws-tt-emp"><span class="ws-tt-emp-head"') !== -1 &&
            h.indexOf('data-full="Работник"') !== -1,
            'главная таблица: шапка с «Работником» (Task 333, мобайл; Task 385: работник)');""",
"""        assertTrue(h.indexOf('<th class="ws-tt-emp" rowspan="2"><span class="ws-tt-emp-head"') !== -1 &&
            h.indexOf('data-full="Работник"') !== -1,
            'главная таблица: шапка с «Работником» (Task 333, мобайл; Task 385: работник; Task 401: rowspan=2)');""", 1
),
(
"""        assertEqual((h.match(/<tr>/g) || []).length, 4,
            '4 <tr>: шапка+Иванов (главная) + шапка+Сидоров (архив)');
        assertTrue(h.indexOf('<th>Дней</th>') !== -1 && h.indexOf('<th>Часов</th>') !== -1,
            'годовые суммы: колонки Дней/Часов');
        assertTrue(h.indexOf('<th title="дни переработки за год — коды д/н">Перераб. (дни)</th>') !== -1,
            'Task 322 → 329 → 331: годовая колонка Перераб. (дни, тултип)');""",
"""        assertEqual((h.match(/<tr>/g) || []).length, 6,
            '6 <tr>: шапка+подстрока+Иванов (главная) + шапка+подстрока+Сидоров (архив) — Task 401');
        assertTrue(h.indexOf('<th class="ws-tt-sum ws-tt-sum-edge" rowspan="2">Дней</th>') !== -1 &&
            h.indexOf('<th class="ws-tt-sum" rowspan="2">Часов</th>') !== -1,
            'годовые суммы: колонки Дней/Часов (Task 401: rowspan=2 + итоговый фон)');
        assertTrue(h.indexOf('<th class="ws-tt-sum" rowspan="2" title="дни переработки за год — коды д/н">Перераб. (дни)</th>') !== -1,
            'Task 322 → 329 → 331: годовая колонка Перераб. (дни, тултип; Task 401: класс+rowspan)');""", 1
),
])

# --- test-task323.js: <tr>-счёт года (шапки стали двухстрочными) ---
ok &= patch('tests/test-task323.js', [
(
"""        assertEqual((h.match(/<tr>/g) || []).length, 4,
            '4 <tr>: шапка+Петров (главная) + шапка+Сидоров (архив)');""",
"""        assertEqual((h.match(/<tr>/g) || []).length, 6,
            '6 <tr>: шапка+подстрока+Петров (главная) + шапка+подстрока+Сидоров (архив) — Task 401');""", 1
),
])

# --- test-task333.js: «Работник» th — rowspan="2" (regex ×2) ---
ok &= patch('tests/test-task333.js', [
(
"""        assertTrue((h.match(/<th class="ws-tt-emp"><span class="ws-tt-emp-head"/g) || []).length === 2,
            'шапки «Сотрудник» — у главной (мобайл) и у архива');""",
"""        assertTrue((h.match(/<th class="ws-tt-emp" rowspan="2"><span class="ws-tt-emp-head"/g) || []).length === 2,
            'шапки «Сотрудник» — у главной (мобайл) и у архива (Task 401: rowspan=2 — шапка двухстрочная)');""", 1
),
])

sys.exit(0 if ok else 1)
