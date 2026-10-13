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
 13. Task 458: комментарий ws_auto_dn_keys (упоминает isolateLocalStorage)
 14. IndexedDB: DB_NAME 'kip8-cache-test-v1' -> 'kip8-cache-v1' (+комментарий;
     единственный КОД-изолят — меняется не только текст, но и значение)
 15. Удаляет HTML-комментарии-триггеры синка kip8test-desktop (Task 517/518;
     в kip8 их НЕТ — paths синка kip8 включает tests/**, а в kip8test
     tests-only пуш не попадает в paths, поэтому триггеры пишутся в конец
     index.html и перед переносом вырезаются; правило генерическое —
     триггеры будущих задач вырезаются автоматически)

Обновление Task 519 (устранение хвоста после Task 518): изоляты 13-15
добавлены после дрейфа — Task 458 и IndexedDB не покрывались (assert
'isolateLocalStorage' падал на комментарии 458), триггеры синка 517/518
оставались хвостом. Полный набор сверен диффом kip8test/index.html
(после преобразований) ↔ kip8/index.html: при синхронном контенте
репозиториев дифф должен быть ПУСТ (0 изменённых строк).

Результат: /tmp/kip8_index_transfer.html
Затем печатает контрольные проверки и дифф с текущим kip8.
"""
import re
import subprocess
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
# Замена '\n\n' (а не '\n'): в kip8 на этом месте ДВЕ пустые строки —
# так перенос без новых правок даёт 0 диффа в kip8 (идемпотентность).
html, n_block = pattern.subn('\n\n', html)
if n_block != 1:
    print('ОШИБКА: блок isolateLocalStorage найден %d раз (ожидается 1) — '
          'текст блока дрейфнул, обновить regex шага 1' % n_block)
    sys.exit(1)
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

# --- 8-14. Комментарии-изоляты и код-изоляты (текст kip8test → текст kip8).
# Первое реальное применение скрипта после Task 344 (346 шёл патчем):
# Assert «isolateLocalStorage не остался» падал на комментарии Task 193,
# а 4 комментария-изолята не заменялись вовсе. Task 519 (устранение хвоста
# после прямых патчей Task 518): добавлены изоляты Task 458 (ws_auto_dn_keys)
# и IndexedDB (DB_NAME — единственный код-изолят, меняется значение);
# набор сверен ПОЛНЫМ диффом kip8test↔kip8 post-Task 518 (8 hunks = 6
# прежних + 3 новых, включая триггеры синка — шаг 15).
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
    # Task 458 (добавлено Task 519): ключ ws_auto_dn_keys — упоминает
    # isolateLocalStorage и ронял финальный assert (2 строки → 2 строки)
    ("        // ключ localStorage ws_auto_dn_keys (префикс репозитория\n        // ставит isolateLocalStorage)",
     "        // ключ localStorage ws_auto_dn_keys (в тестовом репо\n        // ключ автоматически получает префикс)",
     1),
    # IndexedDB (добавлено Task 519): имя БД + комментарий (3 строки →
    # 3 строки); ЕДИНСТВЕННЫЙ код-изолят — меняется и var DB_NAME
    ("    // Имя БД kip8test; перенос в kip8 → 'kip8-cache-v1' (маппинг\n    // де-изоляции, как IMAGE_CACHE_VERSION kipia-images-*-v3)\n    var DB_NAME = 'kip8-cache-test-v1';",
     "    // Имя БД kip8 — основной репозиторий (в kip8test — 'kip8-cache-test-v1';\n    // маппинг де-изоляции переносов, как IMAGE_CACHE_VERSION kipia-images-*-v3)\n    var DB_NAME = 'kip8-cache-v1';",
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

# --- 15. HTML-комментарии-триггеры синка kip8test-desktop (Task 517/518) ---
# paths-синк kip8test-desktop срабатывает только на index.html (+
# десктоп-модули), поэтому при правках БЕЗ index.html в конец файла
# пишутся комментарии-триггеры полного синка фикстур. В kip8 таких
# комментариев НЕТ (paths синка kip8 включает tests/**). При переносе
# вырезаем ЛЮБОЙ HTML-комментарий, упоминающий kip8test-desktop, вместе
# с одной следующей пустой строкой (чтобы не оставлять двойных пустых
# строк). (?!--) не даёт пересечь границу соседнего комментария.
trigger_pat = re.compile(
    r'<!--(?:(?!-->)[\s\S])*?kip8test-desktop(?:(?!-->)[\s\S])*?-->\n\n?')
html, n_trig = trigger_pat.subn('', html)
print('[15] HTML-комментариев-триггеров синка kip8test-desktop удалено: %d '
      '(правило генерическое — триггеры будущих задач вырезаются сами; '
      'сейчас это Task 517 и Task 518)' % n_trig)

# --- Контрольные проверки ---
# Оставшиеся упоминания kip8test НЕ обязаны быть нулевыми: часть из
# них ЛЕГИТИМНО живёт в самом kip8 (комментарии «…в kip8test…»,
# «kip8test синхронизирован с этим же URL» — это текст файла kip8).
# Эталонный набор post-Task 519 — 6 строк (сверено диффом, идентичны
# в kip8/index.html):
#   1) CSS /* Task 243: … В kip8test wsTrSheet уже правильно закрыт … */
#   2) // Task 245). Пробы 2026-09-01 (Task 284 в kip8test) подтвердили:
#   3) // (Task 274+) есть. kip8test синхронизирован с этим же URL.
#   4) // проект на kip8 и kip8test):
#   5) // для kip8test/kip8 (как kip8_cj_cache — бэкенд один).
#   6) // Имя БД kip8 — основной репозиторий (в kip8test — 'kip8-cache-test-v1';
# Всё, что СВЕРХ этого набора, — НОВЫЙ изолят: добавить замену в скрипт
# и bump набора ниже.
leftover = [l for l in html.split('\n') if 'kip8test' in l and 'github.com' not in l]
if leftover:
    print('ОСТАВШИЕСЯ упоминания kip8test (%d шт.; эталон post-Task 519 — 6, '
          'сверить с kip8):' % len(leftover))
    for l in leftover:
        print('   ', l.strip()[:120])
else:
    print('[ok] упоминаний kip8test не осталось (кроме github.com URL)')

# Жёсткие ассерты (Task 519): раньше падал только isolateLocalStorage —
# комментарий Task 458 и DB_NAME проходили молча, триггеры синка
# оставались хвостом. Теперь закрываем все четыре класса изолятов.
assert 'isolateLocalStorage' not in html, 'isolateLocalStorage остался!'
assert "'kip8test:'" not in html, "префикс 'kip8test:' остался!"
assert "var DB_NAME = 'kip8-cache-test-v1'" not in html, \
    "DB_NAME 'kip8-cache-test-v1' остался (шаг 14 не применён?)"
assert 'kip8test-desktop' not in html, \
    'упоминание kip8test-desktop осталось (триггер синка — шаг 15?)'

with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

# --- Сравнение с текущим kip8 ---
r = subprocess.run(['diff', DST, '/home/z/my-project/kip8/index.html'],
                   capture_output=True, text=True)
lines = r.stdout.split('\n')
changed = [l for l in lines if l.startswith(('<', '>'))]
print(f'\nDiff с текущим kip8/index.html: {len(changed)} изменённых строк')
if not changed:
    print('[ok] ПОЛНОЕ СОВПАДЕНИЕ: изоляты закрыты полностью, контент '
          'репозиториев синхронен (ожидаемо между переносами).')
else:
    print('(!) Сверить hunks диффа: это переносимый контент (норма при '
          'переносе новой задачи) ИЛИ неизвестный изолят (добавить '
          'замену в скрипт).')
print(f'Строк в файле: {html.count(chr(10)) + 1}')
print(f'Результат: {DST}')
