#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 369: SW-бамп kipia-test-v597 → v598 (index.html менялся — свайп
# кнопки «Проекты» на странице КИП ИОС открывает «Проекты по статусу»:
# свайп-ячейка с подложками, страница page-projects-status, группировка
# по столбцу «Статус проекта», роутинг/доступ/хлебные крошки).
# Порядок замен в tests/ ВАЖЕН (урок Task 361):
# СНАЧАЛА guard-ы «v598 не существует» → v599, ЗАТЕМ ассерты
# v597 → v598. Запуск из корня репо kip8test.
import glob

# 1. sw.js — CACHE_VERSION
sw_path = 'sw.js'
sw = open(sw_path, encoding='utf-8').read()
old = "CACHE_VERSION = 'kipia-test-v597'"
new = "CACHE_VERSION = 'kipia-test-v598'"
assert old in sw, 'sw.js: не найден текущий CACHE_VERSION v597'
assert 'kipia-test-v598' not in sw, 'sw.js: v598 уже был (двойной бамп?)'
sw = sw.replace(old, new)
open(sw_path, 'w', encoding='utf-8').write(sw)
print('sw.js: CACHE_VERSION kipia-test-v597 -> kipia-test-v598')

# 2. tests/*.js — guard v598→v599, затем ассерты v597→v598
changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = open(f, encoding='utf-8').read()
    orig = s
    n_guard = s.count('kipia-test-v598')
    s = s.replace('kipia-test-v598', 'kipia-test-v599')
    n_assert = s.count('kipia-test-v597')
    s = s.replace('kipia-test-v597', 'kipia-test-v598')
    # сообщения guard-ов — под новую цель v599 (косметика)
    s = s.replace('v598 ещё не существует', 'v599 ещё не существует')
    s = s.replace('v597 ещё не существует', 'v599 ещё не существует')
    if s != orig:
        open(f, 'w', encoding='utf-8').write(s)
        changed.append((f, n_assert, n_guard))
print('tests изменено файлов: %d' % len(changed))
for f, a, g in changed:
    print('  %s (ассерты v597→v598: %d, guard v598→v599: %d)' % (f, a, g))

# 3. контроль: v598 в sw.js ровно один
assert sw.count('kipia-test-v598') == 1
print('OK: единственный kipia-test-v598 в sw.js')
