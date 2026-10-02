#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 462: адаптация tests/test-task460.js — раздел «права доступа»
# под новую реальность (plan-events — отдельное право plan.events).
import io
import sys

PATH = 'tests/test-task460.js'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

# --- 1. шапка файла: пометка об обновлении Task 462 ---
# (УЖЕ применена частичной правкой MultiEdit — только проверяем)
new1_markers = [
    '[Task 462] доступ переведён на ОТДЕЛЬНОЕ право plan.events',
    'фоллбек пока колонки в матрице нет',
]
for marker in new1_markers:
    if marker not in src:
        print('ОШИБКА: шапка уже должна содержать пометку Task 462: %s' % marker[:50])
        sys.exit(1)

# --- 2. раздел 5: три ассерта под новую реализацию ---
old2 = """// ============================================================
// 5. SRC — доступ (как у «Документации ИОС», без отдельного права)
// ============================================================
describe('Task 460 — SRC: права доступа', () => {

    test('_KIP_IOS_PAGES включает plan-events', () => {
        const idx = INDEX_SRC.indexOf('_KIP_IOS_PAGES:');
        const block = INDEX_SRC.slice(idx, idx + 1200);
        assertTrue(block.indexOf("'plan-events']") !== -1,
            'plan-events в конце массива _KIP_IOS_PAGES');
    });

    test('LVL_KIP8_PRO: вместе с docs-ios (легаси-карта)', () => {
        assertTrue(INDEX_SRC.indexOf("FLOWMETER, ['docs-ios', 'plan-events']);") !== -1,
            'КИП8 pro получает docs-ios + plan-events');
    });

    test('_applyServerAccess: flowmeter.view без КИП ИОС → docs-ios + plan-events', () => {
        assertTrue(INDEX_SRC.indexOf("if (!kipios) _add(['docs-ios', 'plan-events']);") !== -1,
            'серверная матрица: страница идёт вместе с хабом');
    });"""
new2 = """// ============================================================
// 5. SRC — доступ (Task 460: следовал за «Документацией ИОС»;
//    Task 462 перевёл на отдельное право plan.events)
// ============================================================
describe('Task 460 — SRC: права доступа (обновлено Task 462)', () => {

    test('plan-events — своя группа _PLAN_EVENTS_PAGES, НЕ в _KIP_IOS_PAGES', () => {
        assertTrue(INDEX_SRC.indexOf("_PLAN_EVENTS_PAGES: ['plan-events'],") !== -1,
            'группа доступа plan-events (Task 462)');
        const idx = INDEX_SRC.indexOf('_KIP_IOS_PAGES:');
        const end = INDEX_SRC.indexOf('_PLAN_EVENTS_PAGES:');
        const block = INDEX_SRC.slice(idx, end);
        assertTrue(block.indexOf("'plan-events'") === -1,
            'plan-events больше НЕ в массиве _KIP_IOS_PAGES (Task 462)');
    });

    test('LVL_KIP8_PRO: docs-ios + PLAN_EVENTS (легаси-карта)', () => {
        assertTrue(INDEX_SRC.indexOf("FLOWMETER, PLAN_EVENTS, ['docs-ios']);") !== -1,
            'КИП8 pro получает docs-ios + plan-events (через PLAN_EVENTS)');
    });

    test('_applyServerAccess: flowmeter.view без КИП ИОС → только docs-ios', () => {
        assertTrue(INDEX_SRC.indexOf("if (!kipios) _add(['docs-ios']);") !== -1,
            'серверная матрица: хаб отдельно, план-эвентс — по праву plan.events');
    });"""

for name, old in [('раздел 5', old2)]:
    n = src.count(old)
    if n != 1:
        print('ОШИБКА: якорь «%s» найден %d раз' % (name, n))
        sys.exit(1)

src = src.replace(old2, new2)

# проверки после
post = [
    ("_PLAN_EVENTS_PAGES: ['plan-events'],", 'группа в ассерте 460'),
    ("FLOWMETER, PLAN_EVENTS, ['docs-ios']);", 'уровень КИП8 pro'),
    ("if (!kipios) _add(['docs-ios']);", 'flowmeter-ветка'),
    ('Task 462 перевёл на отдельное право plan.events', 'комментарий раздела'),
]
for marker, why in post:
    if marker not in src:
        print('ОШИБКА ПОСЛЕ: нет маркера (%s): %s' % (why, marker[:60]))
        sys.exit(1)
gone = ["['docs-ios', 'plan-events']", '_KIP_IOS_PAGES включает plan-events']
for marker in gone:
    if marker in src:
        print('ОШИБКА ПОСЛЕ: остался старый код: %s' % marker[:60])
        sys.exit(1)

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('test-task460.js: адаптирован под Task 462 (шапка + раздел 5)')
