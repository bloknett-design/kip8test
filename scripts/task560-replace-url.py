#!/usr/bin/env python3
"""
Task 560: замена ID Google-таблицы «Перечень КИП ИОС рабочий.xlsx»
во всех связанных файлах kip8test (по образцу task480-replace-url.py).

Старый ID: 1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee (Task 480)
Новый ID:  14l0ac4zGwOblvuH8kRkwwdOymAVXD5op
(полный URL от пользователя:
 https://docs.google.com/spreadsheets/d/14l0ac4zGwOblvuH8kRkwwdOymAVXD5op/edit?usp=sharing&ouid=110493351905411532775&rtpof=true&sd=true)

Замена ГОЛОГО ID покрывает все формы: URL в комментариях, docstring,
DEFAULT_SPREADSHEET_ID, source-поля data/*.json, таблицы README и промта.
Worklog (история задач), DEPLOY-Task480 и одноразовые скрипты task480-*
НЕ трогаем — это исторические записи. sw.js (комментарий Task 480) и
tests/run-all.js (комментарий Task 480) правятся ОТДЕЛЬНО — с пометкой
«обновлён Task 560», слепая замена там не подходит.
"""
from pathlib import Path

ROOT = Path('/home/z/my-project/kip8test')
OLD_ID = '1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee'
NEW_ID = '14l0ac4zGwOblvuH8kRkwwdOymAVXD5op'

FILES = [
    '.github/workflows/sync-devices.yml',
    '.github/workflows/sync-lockouts.yml',
    '.github/workflows/sync-regulators.yml',
    '.github/workflows/sync-valves.yml',
    'scripts/sync-devices.py',
    'scripts/sync-lockouts.py',
    'scripts/sync-regulators.py',
    'scripts/sync-valves.py',
    'data/devices.json',
    'data/lockouts.json',
    'data/regulators.json',
    'data/valves.json',
    'index.html',
    'README.md',
    'Системный_промт_для_приложения_КИПиА.md',
]

total = 0
for rel in FILES:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    n = text.count(OLD_ID)
    if n == 0:
        print(f'!! {rel}: старый ID НЕ найден (проверить!)')
        continue
    p.write_text(text.replace(OLD_ID, NEW_ID), encoding='utf-8')
    print(f'OK {rel}: {n} замен')
    total += n

print(f'\nИтого замен: {total} (ожидание: 3+3+3+3+3+3+3+3+1+1+1+1+3+4+4 = 31)')

# Контрольная сверка: старого ID больше нигде нет (кроме worklog — история)
leftovers = []
for rel in FILES:
    if OLD_ID in (ROOT / rel).read_text(encoding='utf-8'):
        leftovers.append(rel)
print(f'Остатки старого ID в обработанных файлах: {leftovers or "нет"}')
