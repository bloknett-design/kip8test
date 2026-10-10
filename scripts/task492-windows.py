#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 492: окна истории sw.js — комментарий Task 492 (~290 симв. перед
# CACHE_VERSION) отодвинул все якоря на ~286 симв.; расширены окна
# тестов 461/472/473/474/480/481/482 + каскад литералов в
# test-task475/test-task486/test-task482 (якорь = CACHE_VERSION v716).
# Замеры дистанций (post-492): 461@11841, 471@9279, 472@8730,
# 473@8469, 480@6221, 481@5977 — новые окна с запасом 500+.
import io

def patch(path, old, new, count=1):
    s = io.open(path, encoding='utf-8').read()
    n = s.count(old)
    assert n == count, '%s: %r найден %d раз (ожидалось %d)' % (path, old[:40], n, count)
    s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8').write(s)
    print('  OK %s: %s' % (path, new[:70].replace('\n', ' ')))

NOTE = ('        // Task 492: комментарий (~290 симв.) отодвинул якорь — '
        'окно расширено\n')

# --- 1) test-task461: окно 11600 → 12400 (якорь 461@11841) ---
patch('tests/test-task461.js',
      "        const above = SW_SRC.slice(Math.max(0, i - 11600), i);",
      "        // Task 492: комментарий нижнего бара датчиков (~290 симв.)\n"
      "        // отодвинул якорь Task 461 до ~11841 — окно 11600 → 12400.\n"
      "        const above = SW_SRC.slice(Math.max(0, i - 12400), i);")

# --- 2) test-task472: окно 8500 → 9300 (якорь 472@8730) ---
patch('tests/test-task472.js',
      "        const ctx = SW_SRC.slice(Math.max(0, i - 8500), i);",
      "        // Task 492: комментарий (~290 симв.) отодвинул якорь Task 472\n"
      "        // до ~8730 — окно 8500 → 9300.\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 9300), i);")

# --- 3) test-task473: окно 8200 → 9000 (якорь 473@8469) ---
patch('tests/test-task473.js',
      "        const ctx = SW_SRC.slice(Math.max(0, i - 8200), i);",
      "        // Task 492: комментарий (~290 симв.) отодвинул якорь Task 473\n"
      "        // до ~8469 — окно 8200 → 9000.\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 9000), i);")

# --- 4) test-task474: якоря 471/461 — 9000 → 9800, 11600 → 12400 ---
patch('tests/test-task474.js',
      "        assertTrue(i471 !== -1 && (i - i471) < 9000,",
      "        // Task 492: якорь 471@9279 — окно 9000 → 9800.\n"
      "        assertTrue(i471 !== -1 && (i - i471) < 9800,")
patch('tests/test-task474.js',
      "        assertTrue(i461 !== -1 && (i - i461) < 11600,",
      "        // Task 492: якорь 461@11841 — окно 11600 → 12400.\n"
      "        assertTrue(i461 !== -1 && (i - i461) < 12400,")

# --- 5) test-task480: окно 6000 → 6800 (якорь 480@6221) ---
patch('tests/test-task480.js',
      "        const ctx = SW_SRC.slice(Math.max(0, i - 6000), i);",
      "        // Task 492: комментарий (~290 симв.) отодвинул якорь Task 480\n"
      "        // до ~6221 — окно 6000 → 6800.\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 6800), i);")

# --- 6) test-task481: w700 6000 → 6800 (якорь 480@6221 в w700) ---
patch('tests/test-task481.js',
      "        const w700 = SW_SRC.slice(Math.max(0, i - 6000), i);",
      "        // Task 492: комментарий (~290 симв.) — якорь 480@6221;\n"
      "        // окно w700 6000 → 6800 (w1400 7300 хватает: 479@6235)\n"
      "        const w700 = SW_SRC.slice(Math.max(0, i - 6800), i);")

# --- 7) test-task481 §«окна ЧУЖИХ»: литералы 461/472 ---
patch('tests/test-task481.js',
      "        assertTrue(s461.indexOf('i - 11600') !== -1, 'test-task461: окно 9100');",
      "        assertTrue(s461.indexOf('i - 12400') !== -1, 'test-task461: окно 12400 (Task 492)');")
patch('tests/test-task481.js',
      "        assertTrue(s472.indexOf('i - 8500') !== -1, 'test-task472: окно 5900');",
      "        assertTrue(s472.indexOf('i - 9300') !== -1, 'test-task472: окно 9300 (Task 492)');")

# --- 8) test-task482: окно 6000 → 6800 (якорь 480@6221) ---
patch('tests/test-task482.js',
      "        const ctx = SW_SRC.slice(Math.max(0, i - 6000), i);\n"
      "        assertTrue(ctx.indexOf('Task 481') !== -1, 'Task 481 в окне');",
      "        // Task 492: комментарий (~290 симв.) отодвинул якорь 480\n"
      "        // до ~6221 — окно 6000 → 6800 (481@5977 внутри)\n"
      "        const ctx = SW_SRC.slice(Math.max(0, i - 6800), i);\n"
      "        assertTrue(ctx.indexOf('Task 481') !== -1, 'Task 481 в окне');")

# --- 9) test-task482 §литералы: s480 'i - 6000' → 'i - 6800' ---
patch('tests/test-task482.js',
      "        assertTrue(s480.indexOf('i - 6000') !== -1, 'test-task480: окно 6000 (Task 490)');",
      "        assertTrue(s480.indexOf('i - 6800') !== -1, 'test-task480: окно 6800 (Task 492)');")

# --- 10) test-task475 §9: литералы 461/472 (s = содержимое их тестов) ---
patch('tests/test-task475.js',
      "        assertTrue(s.indexOf('i - 11600') !== -1, 'окно расширено до 9100');",
      "        assertTrue(s.indexOf('i - 12400') !== -1, 'окно 12400 (Task 492)');")
patch('tests/test-task475.js',
      "        assertTrue(s.indexOf('i - 8500') !== -1, 'окно Task 472: 5900');",
      "        assertTrue(s.indexOf('i - 9300') !== -1, 'окно Task 472: 9300 (Task 492)');")

# --- 11) test-task486 §литералы: s475 'i - 11600' → 'i - 12400' ---
patch('tests/test-task486.js',
      "        assertTrue(s475.indexOf(\"'i - 11600'\") !== -1, 'каскад 475: 461 → 9100');",
      "        assertTrue(s475.indexOf(\"'i - 12400'\") !== -1, 'каскад 475: 461 → 12400 (Task 492)');")

print('OK: все окна истории Task 492 расширены (каскад синхронизирован)')
