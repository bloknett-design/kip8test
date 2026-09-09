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

# --- 8-12. Комментарии-изоляты (Task 353: текст kip8test → текст kip8).
# Первое реальное применение скрипта после Task 344 (346 шёл патчем):
# Assert «isolateLocalStorage не остался» падал на комментарии Task 193,
# а 4 комментария-изолята не заменялись вовсе. Ниже — полный набор
# известных изолятов (проверено диффом kip8test↔kip8 до переноса 353).
comment_replacements = [
    # Task 243: sidebar (длинный комментарий)
    ("/* Task 243 (бекпорт из kip8): !important бьёт десктопное правило #sidebar{transform:translateX(-100%)!important} (specificity #sidebar.active (1,1,0) > #sidebar (1,0,0)). В kip8test wsTrSheet уже правильно закрыт, но !important оставлен для надёжности и паритета с kip8 — чтобы при следующем переносе kip8test → kip8 не потерять фикс. */",
     "/* Task 243: !important бьёт десктопное правило #sidebar{transform:translateX(-100%)!important} (specificity #sidebar.active (1,1,0) > #sidebar (1,0,0)) — фикс бага «hamburger не открывает sidebar на 377px viewport». Task 244: корневая причина — wsTrSheet не был закрыт, sidebar оказывался вложенным в него (position:fixed относительно wsTrSheet, имевшего transform). В kip8test wsTrSheet уже правильно закрыт, но !important оставлен для надёжности. */",
     1),
    # Task 243: overlay
    ("/* Task 243 (бекпорт): то же самое для overlay */",
     "/* Task 243: то же самое для overlay */", 1),
    # Task 193: ключи сапёра (2 строки → 2 строки)
    ("    // (в тестовом репо ключ автоматически получает префикс kip8test:\n    // через isolateLocalStorage). При первом запуске победы из старого",
     "    // (kip8 — основной репозиторий, ключи без префикса). При первом\n    // запуске победы из старого",
     1),
    # WEB_APP_URL: шапка-комментарий (6 строк → 5 строк)
    ("        // URL Apps Script Web App.\n        // Task 284: URL развёртывания пользователя (AKfycbyt…) — пробы\n        // 2026-09-01 подтвердили: проект полный (Auth/Sessions/Admin/\n        // CableJournal/Flowmeter/ValidationRules/WorkSchedule) и код\n        // свежий (роутинг отпусков есть). Прежний URL (AKfycbzg…,\n        // Task 202) остался на старом снимке кода — до Task 274.",
     "        // URL Apps Script Web App (развёртывание AKfycbyt…, в kip8 с\n        // Task 245). Пробы 2026-09-01 (Task 284 в kip8test) подтвердили:\n        // проект полный (Auth/Sessions/Admin/CableJournal/Flowmeter/\n        // ValidationRules/WorkSchedule) и код свежий — роутинг отпусков\n        // (Task 274+) есть. kip8test синхронизирован с этим же URL.",
     1),
    # Task 242: усиление обновления SW (перенос строк как в kip8)
    ("        // Task 242 (бекпорт из kip8): усиление обновления SW — вместе с\n        // skipWaiting() в sw.js и reg.update() сразу при загрузке.",
     "        // Task 242: усиление обновления SW — вместе с skipWaiting() в sw.js\n        // и reg.update() сразу при загрузке.",
     1),
]
for old, new, expected in comment_replacements:
    cnt = html.count(old)
    if cnt != expected:
        print('ОШИБКА: комментарий-изолят найден %d раз (ожидается %d):' % (cnt, expected))
        print('   ' + old[:120].replace('\n', '\\n'))
        sys.exit(1)
    html = html.replace(old, new)
    print('[ok] комментарий-изолят #%d заменён (%d зам.)' %
          (comment_replacements.index((old, new, expected)) + 8, cnt))

# --- Контрольные проверки ---
# Оставшиеся упоминания kip8test НЕ обязаны быть нулевыми: часть из
# них ЛЕГИТИМНО живёт в самом kip8 (комментарии «…в kip8test…»,
# «kip8test синхронизирован с этим же URL» — это текст файла kip8).
leftover = [l for l in html.split('\n') if 'kip8test' in l and 'github.com' not in l]
if leftover:
    print('ОСТАВШИЕСЯ упоминания kip8test (сверить с kip8 — могут быть легитимными):')
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
