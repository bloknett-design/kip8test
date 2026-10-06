#!/usr/bin/env python3
"""
Task 480: замена ID Google-таблицы «Перечень КИП ИОС рабочий.xlsx»
во всех связанных файлах kip8test.

Старый ID: 1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy
Новый ID:  1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee
(полный URL от пользователя:
 https://docs.google.com/spreadsheets/d/1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee/edit?usp=sharing&ouid=110493351905411532775&rtpof=true&sd=true)

Замена ГОЛОГО ID покрывает все формы: URL в комментариях, docstring,
DEFAULT_SPREADSHEET_ID, source-поля data/*.json, таблицы README и промта.
Worklog (история задач) НЕ трогаем — это исторические записи.
"""
from pathlib import Path

ROOT = Path('/home/z/my-project/kip8test')
OLD_ID = '1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy'
NEW_ID = '1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee'

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

print(f'\nИтого замен: {total} (ожидание: 3+3+3+3+3+3+3+3+1+1+1+1+3+4+4 = 38)')

# Контрольная сверка: старого ID больше нигде нет (кроме worklog — история)
leftovers = []
for rel in FILES:
    if OLD_ID in (ROOT / rel).read_text(encoding='utf-8'):
        leftovers.append(rel)
print(f'Остатки старого ID в обработанных файлах: {leftovers or "нет"}')
