#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 463: адаптация СТАРЫХ тестов под легитимные изменения разметки
# (прецедент — task462-adapt-460.py):
#   1. test-task460.js: таблица pe-table получила id="peTable"
#      (Task 463 — делегированный клик по ячейкам месяцев);
#   2. test-task461.js: окно «комментарий Task 461 у версии кэша»
#      700 → 2000 символов — комментарий Task 463 в sw.js (4 строки)
#      отодвинул комментарий Task 461 за границу прежнего окна
#      (расстояние 796 символов); семантика проверки сохранена —
#      «описание изменений задачи в шапке версий».
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 1. test-task460.js ---
P460 = os.path.join(ROOT, 'tests', 'test-task460.js')
with io.open(P460, encoding='utf-8') as f:
    src = f.read()

OLD_TABLE = "assertTrue(page.indexOf('<table class=\"pe-table\">') !== -1, 'таблица pe-table');"
NEW_TABLE = ("assertTrue(page.indexOf('<table class=\"pe-table\" id=\"peTable\">') !== -1, "
             "'таблица pe-table (id добавлен Task 463 — делегированный клик)');")
assert src.count(OLD_TABLE) == 1, 'якорь таблицы в test-task460 не найден'
src = src.replace(OLD_TABLE, NEW_TABLE)
with io.open(P460, 'w', encoding='utf-8') as f:
    f.write(src)
print('test-task460.js: якорь таблицы обновлён (id="peTable")')

# --- 2. test-task461.js ---
P461 = os.path.join(ROOT, 'tests', 'test-task461.js')
with io.open(P461, encoding='utf-8') as f:
    src = f.read()

OLD_WIN = "const above = SW_SRC.slice(Math.max(0, i - 700), i);"
NEW_WIN = ("// Task 463: окно 700 → 2000 — комментарий Task 463 в шапке sw.js\n"
           "        // отодвинул комментарий Task 461 за границу прежнего окна\n"
           "        const above = SW_SRC.slice(Math.max(0, i - 2000), i);")
assert src.count(OLD_WIN) == 1, 'якорь окна в test-task461 не найден'
src = src.replace(OLD_WIN, NEW_WIN)
with io.open(P461, 'w', encoding='utf-8') as f:
    f.write(src)
print('test-task461.js: окно комментария у версии кэша 700 → 2000')
