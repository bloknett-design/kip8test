#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare-kip8-transfer.py — подготовка переноса index.html из kip8test в kip8.

Выполняет обратную изоляцию:
  1. Удаляет блок isolateLocalStorage() (комментарий + IIFE)
  2. 'kip8test_devices_cache'      -> 'kip8_devices_cache'
  3. "'kip8test:' + DEV_CACHE_KEY"  -> "DEV_CACHE_KEY" (3 места)
  4. 'kip8test_phonebook_favorites' -> 'kip8_phonebook_favorites'
  5. 'kip8test_phonebook_notes'     -> 'kip8_phonebook_notes'
  6. 'kip8test_phonebook_cache'     -> 'kip8_phonebook_cache' (2 места)
  7. '/kip8test/#exam-tickets'      -> '/kip8/#exam-tickets' (комментарий)

Результат: /tmp/kip8_index_transfer.html
Затем печатает контрольные проверки.
"""
import re
import sys

SRC = '/home/z/my-project/kip8test/index.html'
DST = '/tmp/kip8_index_transfer.html'

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# --- 1. Удаление блока isolateLocalStorage (комментарий + IIFE) ---
pattern = re.compile(
    r'\n    // ===== ТЕСТОВЫЙ РЕПОЗИТОРИЙ kip8test: изоляция localStorage =====\n'
    r'    // localStorage общий для всего origin \(bloknett-design\.github\.io\)\.\n'
    r'    // Чтобы настройки \(тема, метод калибровки буя\) из тестового репозитория\n'
    r'    // не влияли на основной репозиторий kip8, добавляем префикс ко всем ключам\.\n'
    r'    // В основном репозитории kip8 этот блок ОТСУТСТВУЕТ — там ключи без префикса\.\n'
    r'    \(function isolateLocalStorage\(\) \{\n'
    r'        const PREFIX = \'kip8test:\';\n'
    r'        const origGetItem = localStorage\.getItem\.bind\(localStorage\);\n'
    r'        const origSetItem = localStorage\.setItem\.bind\(localStorage\);\n'
    r'        const origRemoveItem = localStorage\.removeItem\.bind\(localStorage\);\n'
    r'        localStorage\.getItem = function\(key\) \{ return origGetItem\(PREFIX \+ key\); \};\n'
    r'        localStorage\.setItem = function\(key, value\) \{ return origSetItem\(PREFIX \+ key, value\); \};\n'
    r'        localStorage\.removeItem = function\(key\) \{ return origRemoveItem\(PREFIX \+ key\); \};\n'
    r'    \}\)\(\);\n'
)
html, n_block = pattern.subn('\n', html)
print(f'[1] isolateLocalStorage блок удалён: {n_block} (ожидается 1)')

# --- 2-7. Замены префиксов ---
replacements = [
    ("'kip8test_devices_cache'", "'kip8_devices_cache'", 1),
    ("'kip8test:' + DEV_CACHE_KEY", "DEV_CACHE_KEY", 3),
    ("'kip8test_phonebook_favorites'", "'kip8_phonebook_favorites'", 1),
    ("'kip8test_phonebook_notes'", "'kip8_phonebook_notes'", 1),
    ("'kip8test_phonebook_cache'", "'kip8_phonebook_cache'", 2),
    ("/kip8test/#exam-tickets", "/kip8/#exam-tickets", 1),
]
for old, new, expected in replacements:
    cnt = html.count(old)
    if cnt != expected:
        print(f'ОШИБКА: "{old}" найден {cnt} раз (ожидается {expected})')
        sys.exit(1)
    html = html.replace(old, new)
    print(f'[ok] "{old}" -> "{new}" ({cnt} зам.)')

# --- Контрольные проверки ---
leftover = [l for l in html.split('\n') if 'kip8test' in l and 'github.com' not in l]
if leftover:
    print('ОСТАВШИЕСЯ упоминания kip8test (не URL):')
    for l in leftover:
        print('   ', l.strip()[:120])
else:
    print('[ok] упоминаний kip8test не осталось (кроме github.com URL)')
assert 'isolateLocalStorage' not in html, 'isolateLocalStorage остался!'

with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

# --- Сравнение с текущим kip8 ---
import subprocess
r = subprocess.run(['diff', DST, '/home/z/my-project/kip8/index.html'],
                   capture_output=True, text=True)
lines = r.stdout.split('\n')
changed = [l for l in lines if l.startswith(('<', '>'))]
print(f'\nDiff с текущим kip8/index.html: {len(changed)} изменённых строк')
print(f'Строк в файле: {html.count(chr(10)) + 1}')
print(f'Результат: {DST}')
