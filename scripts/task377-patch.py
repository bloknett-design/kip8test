#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 377 — kip8test, index.html: две заявки пользователя:
#   1) «В шахматке Табель учёта рабочего времени, выделение текущего
#      дня сделай посильнее» — усиление подсветки столбца «сегодня»:
#      заливки ячеек 0.16→0.30 (тёмная) / 0.10→0.22 (светлая), шапка
#      0.20→0.40 / 0.13→0.26, акцентная полоса 2px ::after под датой,
#      составные правила «сегодня+наведение/выбор» (усиление НЕ гаснет).
#   2) «В светлой теме, разделительные полосы ячеек шахматки такого же
#      цвета, как в тёмной теме» — в тёмной теме полосы рендерятся
#      практически чёрными rgb(9,15,23) (rgba(0,0,0,0.30) ложится на
#      тёмный стол-фон из-за filter-изоляции ячеек Task 319), в светлой
#      тот же rgba давал бледно-серые rgb(167,166,160). Светлой теме —
#      непрозрачные ЦВЕТА ТЁМНОЙ ТЕМЫ: дни rgb(10,15,23), ФИО
#      rgb(64,80,102), шапка rgb(83,96,117).
# Правки по якорям (indexOf + точные фрагменты), каждая проверяется.
import sys, io

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
orig = src
edits = []

def edit(*a):
    # две формы: (anchor, old, new, label) и (old, new, label) —
    # во второй якорь = первые 60 символов самой старой строки
    global src
    if len(a) == 4:
        anchor, old, new, label = a
    else:
        old, new, label = a
        anchor = old[:60]
    i = src.find(anchor)
    if i == -1:
        print('FAIL anchor: ' + label); sys.exit(1)
    j = src.find(old, i)
    if j == -1:
        print('FAIL old: ' + label); sys.exit(1)
    if src.find(old, j + 1) != -1:
        print('FAIL dup: ' + label); sys.exit(1)
    src = src[:j] + new + src[j + len(old):]
    edits.append(label)

# ---------- 1. ТЁМАЯ ТЕМА: усиление «сегодня» ----------

# 1.1 шапка: градиент 0.20 → 0.40 (+ комментарий Task 377)
edit('    /* Task 313: подсветка СЕГОДНЯШНЕЙ даты в шахматке — колонка дня',
     """    .ws-grid thead th.ws-day-col.ws-today-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.20), rgba(74, 143, 199, 0.20));
        color: var(--accent-blue, #4a8fc7);
    }""",
     """    .ws-grid thead th.ws-day-col.ws-today-col {
        /* Task 377 (заявка: «выделение текущего дня — посильнее»):
           градиент 0.20 → 0.40, число — жирнее; + акцентная полоса
           2px ::after под датой (правило ниже) */
        background-image: linear-gradient(rgba(74, 143, 199, 0.40), rgba(74, 143, 199, 0.40));
        color: var(--accent-blue, #4a8fc7);
        font-weight: 700;
    }""",
     '1.1 тёмная шапка today-col 0.40 + bold')

# 1.2 составные правила ШАПКИ «сегодня + наведение/выбор» — после
#     sel-col (иначе поздние ws-hover-col/ws-sel-col гасили бы 0.40 до
#     0.20/0.30); + ::after-полоса 2px (bottom, БЕЗ wgrp-конфликта:
#     у выходных групп box-shadow inset TOP #e57373 — другое свойство)
edit("""    .ws-grid thead th.ws-day-col.ws-sel-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.30), rgba(74, 143, 199, 0.30));
        color: var(--accent-blue, #4a8fc7);
    }""",
     """    .ws-grid thead th.ws-day-col.ws-sel-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.30), rgba(74, 143, 199, 0.30));
        color: var(--accent-blue, #4a8fc7);
    }
    /* Task 377: составные правила ШАПКИ «сегодня + наведение/выбор» —
       усиленный градиент НЕ гаснет при наведении/выборе сегодняшней
       даты (классы ws-hover-col/ws-sel-col ставятся на th в DOM без
       перерисовки; без этих правил поздние равные по специфичности
       правила перекрыли бы 0.40 до 0.20/0.30). Выбранный — чуть
       насыщеннее. */
    .ws-grid thead th.ws-day-col.ws-today-col.ws-hover-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.40), rgba(74, 143, 199, 0.40));
        color: var(--accent-blue, #4a8fc7);
    }
    .ws-grid thead th.ws-day-col.ws-today-col.ws-sel-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.44), rgba(74, 143, 199, 0.44));
        color: var(--accent-blue, #4a8fc7);
    }
    /* Task 377: акцентная ПОЛОСА 2px под сегодняшней датой (внутри
       th, на layout не влияет — высота шапки 37px по-плану Task 256).
       ::after у th ДНЕЙ свободен (::after занят только у
       th.ws-emp-col, Task 336); position:sticky — позиционированный
       предок. Полоса НЕ конфликтует с рамкой выходных ws-wgrp
       (inset box-shadow TOP — другое свойство): «сегодня-выходной»
       несёт и красный верх, и синий низ. */
    .ws-grid thead th.ws-day-col.ws-today-col::after {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 2px;
        background: var(--accent-blue, #4a8fc7);
    }""",
     '1.2 тёмная шапка: составные + ::after полоса')

# 1.3 ячейки «сегодня»: 0.16 → 0.30 (+ manual)
edit("""    /* Task 313: подсветка СЕГОДНЯШНЕЙ даты — ячейки столбца дня.""",
     """    .ws-grid tbody td.ws-cell.ws-today {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.16);
    }
    .ws-grid tbody td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.16),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-today {
        /* Task 377: 0.16 → 0.30 — выделение заметнее */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }
    .ws-grid tbody td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '1.3 тёмные ячейки сегодня 0.30')

# 1.4 строка наведения + «сегодня»: 0.20 → 0.32 (+ manual)
edit(
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.20);
    }
    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.20),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        /* Task 377: 0.20 → 0.32 — «сегодня» сильнее строки */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.32);
    }
    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.32),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '1.4 тёмная строка+сегодня 0.32')

# 1.5 НОВЫЕ составные правила ТЕЛА «сегодня + hover/sel» — после
#     блока row+sel+manual (последний в серии перекрестья)
edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    /* Task 377 (заявка: «выделение текущего дня — посильнее»):
       составные правила «сегодня + наведение/выбор СТОЛБЦА» —
       усиленная заливка НЕ гаснет, когда курсор над сегодняшней
       датой в шапке или столбец выбран кликом (_dayHover/_daySelect
       ставят ws-hover/ws-sel на td в DOM БЕЗ перерисовки; поздние
       равные правила ws-hover/ws-sel перекрывали бы box-shadow
       «сегодня», возвращая бледный уровень). Сегодня — не ниже
       0.30; выбор столбца — чуть насыщеннее (0.34/0.36); в строке
       наведения — 0.34/0.36. Принцип составных теней — Task 313/316. */
    .ws-grid tbody td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }
    .ws-grid tbody td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    .ws-grid tbody td.ws-cell.ws-today.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }
    .ws-grid tbody td.ws-cell.ws-today.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }
    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.36);
    }
    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.36),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '1.5 тёмное тело: составные сегодня+hover/sel')

# ---------- 2. СВЕТЛАЯ ТЕМА: усиление «сегодня» ----------

# 2.1 шапка: 0.13 → 0.26 (+ bold)
edit("""    /* Task 313: светлая тема — подсветка сегодняшней даты (шапка +
       ячейки столбца): тон мягче тёмной темы (белый фон «громче»
       показывает наложение), число — тёмно-синим акцентом */""",
     """    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-today-col {
        background-image: linear-gradient(rgba(42, 93, 143, 0.13), rgba(42, 93, 143, 0.13));
        color: #2a5d8f;
    }""",
     """    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-today-col {
        /* Task 377: 0.13 → 0.26 — выделение заметнее */
        background-image: linear-gradient(rgba(42, 93, 143, 0.26), rgba(42, 93, 143, 0.26));
        color: #2a5d8f;
        font-weight: 700;
    }""",
     '2.1 светлая шапка today-col 0.26')

# 2.2 ячейки: 0.10 → 0.22 (+ manual)
edit(
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.10);
    }
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.10),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today {
        /* Task 377: 0.10 → 0.22 — выделение заметнее */
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.2 светлые ячейки сегодня 0.22')

# 2.3 строка + «сегодня»: 0.14 → 0.24 (+ manual)
edit("""    /* Task 319: светлая тема — перекрестье СТРОКИ (класс ws-hover-row""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.14);
    }
    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.14),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        /* Task 377: 0.14 → 0.24 — «сегодня» сильнее строки */
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.24);
    }
    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.3 светлая строка+сегодня 0.24')

# 2.4 НОВЫЕ составные правила светлой темы — после row+sel+manual;
#     + полоса ::after в цвет светлого акцента; + составные шапки
edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.15),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.15),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    /* Task 377: светлая тема — составные «сегодня + наведение/выбор
       столбца» (не гаснет при ws-hover/ws-sel на td) и составные
       правила ШАПКИ (градиент 0.26 держится при hover/sel даты);
       полоса ::after под датой — тёмно-синий акцент светлой темы */
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }
    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }
    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.28);
    }
    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.28),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }
    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-today-col.ws-hover-col {
        background-image: linear-gradient(rgba(42, 93, 143, 0.26), rgba(42, 93, 143, 0.26));
        color: #2a5d8f;
    }
    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-today-col.ws-sel-col {
        background-image: linear-gradient(rgba(42, 93, 143, 0.30), rgba(42, 93, 143, 0.30));
        color: #2a5d8f;
    }
    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-today-col::after {
        background: #2a5d8f;
    }""",
     '2.4 светлая: составные + полоса')

# ---------- 3. СВЕТЛАЯ ТЕМА: полосы ячеек = цвет тёмной темы ----------

# 3.1 дни — непрозрачный rgb(10,15,23) (= тёмная тема: rgba(0,0,0,0.30)
#     над тёмным стол-фоном); ставим ПОСЛЕ тёмной пары правил и ДО
#     красной рамки-группы ws-wgrp (равная специфичность (0,3,2) —
#     красные 2px побеждают порядком, как у тёмной)
edit("""    [data-theme="dark"] .ws-grid tbody td {
        border-color: rgba(105, 130, 160, 0.55);
    }""",
     """    [data-theme="dark"] .ws-grid tbody td {
        border-color: rgba(105, 130, 160, 0.55);
    }
    /* Task 377 (заявка: «в светлой теме разделительные полосы ячеек
       шахматки такого же цвета, как в тёмной теме»): в ТЁМНОЙ теме
       полосы между ячейками рендерятся практически ЧЁРНЫМИ —
       rgba(0,0,0,0.30) ложится на тёмный стол-фон (filter-изоляция
       ячеек Task 319 не пускает их светлый фон под collapsed-границу)
       → rgb(9,15,23); в СВЕТЛОЙ теме тот же rgba(0,0,0,0.30) ложился
       на СВЕТЛЫЙ фон ячеек → бледно-серые rgb(167,166,160) полосы.
       Светлой теме — непрозрачный цвет тёмной темы rgb(10,15,23):
       результат одинаков в обеих темах независимо от подложки.
       Специфичность (0,3,2) = тёмной паре; правило стоит ДО красной
       рамки-группы ws-wgrp (Task 363) — красные 2px выходных
       ПОБЕЖДАЮТ порядком, как в тёмной теме. */
    [data-theme="light"] .ws-grid tbody td.ws-cell {
        border-color: rgb(10, 15, 23);
    }""",
     '3.1 светлые дни rgb(10,15,23)')

# 3.2 ФИО/прочие td — rgb(64,80,102) (= тёмная: rgba(105,130,160,0.55)
#     над тёмным фоном); правим ПРАВИЛО Task 355 на месте (оно позже
#     по файлу — (0,2,2) не трогает красную рамку (0,3,2))
edit("""    /* Task 355 (заявка: «разделительные линии оставить тонкими, но
       сделать поярче (чернее)»): цвет линий ячеек шахматки 8% → 30%
       чёрного — тонкие 1px, но отчётливо видны на фоне пустых #eef0f2
       и пастельного розового выходных. Красные стыки Task 255 и
       2px-разделители групп/ФИО специфичностью выше — не затронуты */
    [data-theme="light"] .ws-grid tbody td {
        border-color: rgba(0, 0, 0, 0.30);
    }""",
     """    /* Task 377 (заявка: «в светлой теме полосы — такого же цвета,
       как в тёмной теме»): правило Task 355 (30% чёрного) перекрашено
       в НЕПРОЗРАЧНЫЙ стале-синий rgb(64,80,102) — тот же цвет, каким
       колонка ФИО видна в ТЁМНОЙ теме (rgba(105,130,160,0.55) над
       тёмным фоном). Горизонтальный разделитель строк непрерывен по
       всей ширине: дни — rgb(10,15,23) (правило выше специфичнее),
       ФИО — rgb(64,80,102) — в точности как в тёмной теме.
       Специфичность (0,2,2): красная рамка ws-wgrp (0,3,2) и
       2px-разделители групп/ФИО выше — не затронуты */
    [data-theme="light"] .ws-grid tbody td {
        border-color: rgb(64, 80, 102);
    }""",
     '3.2 светлые ФИО rgb(64,80,102)')

# 3.3 шапка — rgb(83,96,117) (= тёмная: rgba(140,158,188,0.55) над
#     #1e293b); вертикали между днями продолжают полосы тела
edit("""    /* Task 355 (заявка: «так же в шапке шахматки, в днях месяца»):
       светлая тема — линии шапки 30% чёрного, как у ячеек тела
       шахматки (прежде — только нижняя линия 12% чёрного) */
    [data-theme="light"] .ws-grid thead th {
        background: #bfcad5;
        color: #333;
        border-color: rgba(0, 0, 0, 0.30);
    }""",
     """    /* Task 377 (заявка: «в светлой теме полосы — такого же цвета,
       как в тёмной теме»): линии шапки — непрозрачный стале-голубой
       rgb(83,96,117) = цвет тёмной темы (rgba(140,158,188,0.55) над
       сине-серой шапкой #1e293b). Вертикали между днями шапки —
       продолжение полос тела шахматки. Task 355 красил 30% чёрного */
    [data-theme="light"] .ws-grid thead th {
        background: #bfcad5;
        color: #333;
        border-color: rgb(83, 96, 117);
    }""",
     '3.3 светлая шапка rgb(83,96,117)')

io.open(PATH, 'w', encoding='utf-8').write(src)
print('OK: %d правок, %d байт → %d байт' % (len(edits), len(orig), len(src)))
for e in edits:
    print('  ✓ ' + e)
