#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 462: патч index.html + sw.js — доступ к «Плановым мероприятиям»
# через ОТДЕЛЬНОЕ право plan.events в матрице KIP8_Access.
#
# ЗАЯВКА: «Продолжим работу над новым разделом "Плановые мероприятия".
# Во первых необходимо реализовать доступ пользователей к данному
# разделу, в файле KIP8_Access, в таблице matrix нужно добавить новый
# столбец для определения доступа к данному разделу.»
#
# ИЗМЕНЕНИЯ (index.html):
#   1. _KIP_IOS_PAGES: plan-events УДАЛЁН из группы (больше не следует
#      за КИП ИОС автоматически);
#   2. НОВАЯ группа доступа _PLAN_EVENTS_PAGES = ['plan-events'];
#   3. init(): константа PLAN_EVENTS + уровни, где раздел был по
#      Task 460 (ИТР ТОКЕМ / КИП8 pro / КИП ИОС / КИП ИОС+расходомеры)
#      — легаси-карта сохраняет прежнее поведение;
#   4. _applyServerAccess: _drop(_PLAN_EVENTS_PAGES); доступ — по праву
#      plan.events; ПЕРЕХОДНЫЙ фоллбек: матрица получена, но колонки
#      plan.events в ней ещё нет (скрипт RoleMatrixTask462Init не
#      запущен) → прежнее поведение Task 460 (за docs-ios), чтобы никто
#      не потерял доступ до запуска скрипта; found=false → fail-closed;
#   5. flowmeter-ветка: план-эвентс больше не добавляется вместе с
#      docs-ios (Task 462);
#   6. sw.js: kipia-test-v685 → kipia-test-v686 + комментарий.
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
SW = os.path.join(ROOT, 'sw.js')

with io.open(INDEX, encoding='utf-8') as f:
    src = f.read()
with io.open(SW, encoding='utf-8') as f:
    sw = f.read()

REPL = []

# --- 1. _KIP_IOS_PAGES: убрать plan-events + новая группа ---
REPL.append((
"""                         'cable-journal-edit',
                         'cable-journal-add',
                         'cable-journal-view',
                         'plan-114', 'plan-114-view',
                         // Task 460: «Плановые мероприятия» —
                         // статичная страница-таблица (доступ =
                         // «Документация ИОС», отдельного права нет)
                         'plan-events'],""",
"""                         'cable-journal-edit',
                         'cable-journal-add',
                         'cable-journal-view',
                         'plan-114', 'plan-114-view'],
        // Task 462: «Плановые мероприятия» — СВОЯ группа доступа:
        // право plan.events в матрице KIP8_Access (лист matrix; колонка
        // добавляется одноразовым скриптом RoleMatrixTask462Init.gs).
        // До Task 462 (Task 460) страница следовала за «Документацией
        // ИОС» без отдельного права; легаси-карта (матрица недоступна)
        // сохраняет то же поведение — PLAN_EVENTS входит в уровни,
        // где раздел был (ИТР ТОКЕМ / КИП ИОС / ИТР8+ / КИП8 pro).
        _PLAN_EVENTS_PAGES: ['plan-events'],"""))

# --- 2. init(): константа PLAN_EVENTS ---
REPL.append((
"""            const FLOWMETER = this._FLOWMETER_PAGES;
            const CHARTS = this._CHARTS_PAGES;
            const WORK_SCHEDULE = this._WORK_SCHEDULE_PAGES;""",
"""            const FLOWMETER = this._FLOWMETER_PAGES;
            const CHARTS = this._CHARTS_PAGES;
            const WORK_SCHEDULE = this._WORK_SCHEDULE_PAGES;
            const PLAN_EVENTS = this._PLAN_EVENTS_PAGES; // Task 462"""))

# --- 3. Уровни: + PLAN_EVENTS (легаси-карта — прежний доступ) ---
REPL.append((
"""            const LVL_ITR_TOKEM = [].concat(BASE, CALC, ['docs'], KIP_IOS, WHATS_NEW);""",
"""            const LVL_ITR_TOKEM = [].concat(BASE, CALC, ['docs'], KIP_IOS, WHATS_NEW, PLAN_EVENTS);"""))

REPL.append((
"""            // Task 460: вместе с хабом «Документация ИОС» КИП8 pro
            // получает статичную страницу «Плановые мероприятия»
            const LVL_KIP8_PRO = [].concat(BASE, CALC, LIB, SECRET, WHATS_NEW, FLOWMETER, ['docs-ios', 'plan-events']);""",
"""            // Task 460: вместе с хабом «Документация ИОС» КИП8 pro
            // получает статичную страницу «Плановые мероприятия»;
            // Task 462: раздел переведён на отдельное право (PLAN_EVENTS)
            const LVL_KIP8_PRO = [].concat(BASE, CALC, LIB, SECRET, WHATS_NEW, FLOWMETER, PLAN_EVENTS, ['docs-ios']);"""))

REPL.append((
"""            const LVL_KIP_IOS = [].concat(BASE, CALC, LIB, KIP_IOS, SECRET, WHATS_NEW);""",
"""            const LVL_KIP_IOS = [].concat(BASE, CALC, LIB, KIP_IOS, SECRET, WHATS_NEW, PLAN_EVENTS);"""))

REPL.append((
"""            const LVL_KIP_IOS_WITH_FLOW = [].concat(BASE, CALC, LIB, KIP_IOS, FLOWMETER, SECRET, WHATS_NEW);""",
"""            const LVL_KIP_IOS_WITH_FLOW = [].concat(BASE, CALC, LIB, KIP_IOS, FLOWMETER, SECRET, WHATS_NEW, PLAN_EVENTS);"""))

# --- 4. _applyServerAccess: шапка-документация прав ---
REPL.append((
"""         *   workschedule.view      → график работы
         * Админ ('*') не трогаем: сервер принудительно даёт админу все""",
"""         *   workschedule.view      → график работы
         *   plan.events            → «Плановые мероприятия» (Task 462;
         *                            пока колонки в матрице нет —
         *                            переходное поведение Task 460)
         * Админ ('*') не трогаем: сервер принудительно даёт админу все"""))

# --- 5. _applyServerAccess: дроп новой группы ---
REPL.append((
"""            _drop(this._FLOWMETER_PAGES);
            _drop(this._WORK_SCHEDULE_PAGES);""",
"""            _drop(this._FLOWMETER_PAGES);
            _drop(this._WORK_SCHEDULE_PAGES);
            _drop(this._PLAN_EVENTS_PAGES); // Task 462"""))

# --- 6. flowmeter-ветка: без plan-events ---
REPL.append((
"""                // Task 460: вместе с хабом идёт статичная страница
                // «Плановые мероприятия» (отдельного права НЕ имеет).
                if (!kipios) _add(['docs-ios', 'plan-events']);""",
"""                // Task 462: «Плановые мероприятия» больше не следует за
                // хабом — отдельное право plan.events (блок ниже).
                if (!kipios) _add(['docs-ios']);"""))

# --- 7. НОВЫЙ блок plan.events (после workschedule) ---
REPL.append((
"""            if (perm('workschedule.view') || perm('workschedule.view.min') ||
                    perm('workschedule.edit')) {
                _add(this._WORK_SCHEDULE_PAGES);
            }
            this.ROLE_ACCESS[role] = list;""",
"""            if (perm('workschedule.view') || perm('workschedule.view.min') ||
                    perm('workschedule.edit')) {
                _add(this._WORK_SCHEDULE_PAGES);
            }
            // Task 462: «Плановые мероприятия» — отдельное право
            // plan.events (колонка matrix; добавляется одноразовым
            // скриптом RoleMatrixTask462Init.gs). Колонка УЖЕ есть в
            // матрице → доступ строго по галочке. Матрица получена
            // (found), но колонки ещё нет (переходный период: клиент
            // обновился раньше таблицы) → прежнее поведение Task 460:
            // раздел следует за «Документацией ИОС» (КИП ИОС /
            // расходомеры), чтобы никто не потерял доступ до запуска
            // скрипта. found=false → не возвращаем (fail-closed).
            if (found && acc && acc.permissions &&
                    Object.prototype.hasOwnProperty.call(acc.permissions, 'plan.events')) {
                if (perm('plan.events')) _add(this._PLAN_EVENTS_PAGES);
            } else if (found) {
                if (kipios || perm('flowmeter.view')) _add(this._PLAN_EVENTS_PAGES);
            }
            this.ROLE_ACCESS[role] = list;"""))

# ============ ПРОВЕРКИ ДО ЗАПИСИ ============
errors = []
for i, (old, new) in enumerate(REPL, 1):
    n = src.count(old)
    if n != 1:
        errors.append('якорь %d найден %d раз (ожидался 1): %s...' %
                      (i, n, old.strip()[:90].replace('\n', ' | ')))
if errors:
    print('ОШИБКИ ЯКОРЕЙ:')
    for e in errors:
        print('  X ' + e)
    sys.exit(1)

for old, new in REPL:
    src = src.replace(old, new)

# ============ ПРОВЕРКИ ПОСЛЕ ПАТЧА ============
POST_MUST = [
    ("_PLAN_EVENTS_PAGES: ['plan-events'],", 'новая группа доступа'),
    ("const PLAN_EVENTS = this._PLAN_EVENTS_PAGES; // Task 462", 'константа уровня'),
    ("WHATS_NEW, PLAN_EVENTS);", 'LVL_ITR_TOKEM с PLAN_EVENTS'),
    ("FLOWMETER, PLAN_EVENTS, ['docs-ios']);", 'LVL_KIP8_PRO: PLAN_EVENTS + docs-ios'),
    ("SECRET, WHATS_NEW, PLAN_EVENTS);", 'LVL_KIP_IOS / WITH_FLOW с PLAN_EVENTS'),
    ("_drop(this._PLAN_EVENTS_PAGES); // Task 462", 'дроп группы в _applyServerAccess'),
    ("if (!kipios) _add(['docs-ios']);", 'flowmeter-ветка без plan-events'),
    ("Object.prototype.hasOwnProperty.call(acc.permissions, 'plan.events')",
     'переходный детектор колонки'),
    ("if (perm('plan.events')) _add(this._PLAN_EVENTS_PAGES);",
     'доступ по праву plan.events'),
    ("if (kipios || perm('flowmeter.view')) _add(this._PLAN_EVENTS_PAGES);",
     'переходный фоллбек Task 460'),
    ("RoleMatrixTask462Init.gs", 'упоминание init-скрипта'),
]
POST_ABSENT = [
    ("'plan-114', 'plan-114-view',\n                         // Task 460",
     'старый комментарий Task 460 в _KIP_IOS_PAGES'),
    ("['docs-ios', 'plan-events']", 'старая flowmeter-ветка'),
    ("доступ =\n                         // «Документация ИОС», отдельного права нет",
     'старый комментарий «отдельного права нет»'),
]

post_errors = []
for marker, why in POST_MUST:
    if marker not in src:
        post_errors.append('НЕТ маркера (%s): %s' % (why, marker[:80]))
for marker, why in POST_ABSENT:
    if marker in src:
        post_errors.append('ОСТАЛСЯ старый код (%s): %s' % (why, marker[:80].replace('\n', ' | ')))
# plan-events не должен остаться в МАССИВЕ _KIP_IOS_PAGES (срез —
# только до определения новой группы _PLAN_EVENTS_PAGES)
kidx = src.index('_KIP_IOS_PAGES:')
kend = src.index('_PLAN_EVENTS_PAGES:')
kblock = src[kidx:kend]
if "'plan-events'" in kblock:
    post_errors.append("plan-events остался в массиве _KIP_IOS_PAGES")
# уровни: ровно 4 вхождения PLAN_EVENTS в concat-строках
n_lvl = src.count(", PLAN_EVENTS);") + src.count(", PLAN_EVENTS, ")
if n_lvl < 4:
    post_errors.append('уровней с PLAN_EVENTS меньше 4: %d' % n_lvl)
if post_errors:
    print('ОШИБКИ ПОСЛЕ ПАТЧА:')
    for e in post_errors:
        print('  X ' + e)
    sys.exit(1)

with io.open(INDEX, 'w', encoding='utf-8') as f:
    f.write(src)
print('index.html: %d блоков заменено, проверки пройдены' % len(REPL))

# ============ sw.js ============
SW_OLD_COMMENT = """// Task 461: форма СИЗ (раздел «Работники») — подсказки наименований
// datalist #wsPpeNameList ДИНАМИЧЕСКИ из листа «СИЗ» (уникальные
// «наименование_СИЗ» без повторов, _fillPpeNameOptions); статичный
// набор 8 позиций — запасной при пустом листе."""
SW_NEW_COMMENT = SW_OLD_COMMENT + """
// Task 462: «Плановые мероприятия» — ОТДЕЛЬНОЕ право plan.events
// в матрице KIP8_Access (колонку добавляет RoleMatrixTask462Init.gs);
// до появления колонки — прежнее поведение (за «Документацией ИОС»)."""
assert sw.count(SW_OLD_COMMENT) == 1, 'якорь комментария Task 461 в sw.js не найден'
sw = sw.replace(SW_OLD_COMMENT, SW_NEW_COMMENT)
assert sw.count("const CACHE_VERSION = 'kipia-test-v685';") == 1, 'нет v685 в sw.js'
sw = sw.replace("const CACHE_VERSION = 'kipia-test-v685';",
                "const CACHE_VERSION = 'kipia-test-v686';")
assert sw.count("const CACHE_VERSION = 'kipia-test-v686';") == 1
assert 'kipia-test-v685' not in sw, 'v685 осталась в sw.js'
assert 'Task 462' in sw and 'plan.events' in sw

with io.open(SW, 'w', encoding='utf-8') as f:
    f.write(sw)
print('sw.js: kipia-test-v685 -> kipia-test-v686 + комментарий Task 462')
