#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 378 — kip8test, index.html. Заявки пользователя:
#   1) «Фон пустых ячеек сделай #FFFFFF» + «в ячейках итогов учёта,
#      там где нуль, сделать просто пустыми» + «разделительные полосы
#      ячеект сделай как в основной шахматке» — рестайлинг таблиц
#      итогов учёта (шторка + мобильная страница): ячейки значений —
#      непрозрачный #FFFFFF (светлая) / светлые цвета шахматки дней
#      #eef0f2+brightness(0.88) и тёмный текст #141413 (тёмная, Task
#      319-принцип), зебра строк УБРАТА, нули → пустые ячейки, линии —
#      цвета шахматки (значения rgba(0,0,0,0.30)/rgb(10,15,23), шапка
#      сталь rgba(140,158,188,0.55)/rgb(83,96,117), «Сотрудник»
#      rgba(105,130,160,0.55)/rgb(64,80,102)).
#   2) «При включённом подсвечивании перекрестья — подсвечивание строк
#      при наведении на ячейку с фамилией сотрудника и на ячейки итогов
#      учёта; подсветку перекрестья — такой же яркости, как подсветку
#      текущего дня» — сетка: делегирование ловит и td.ws-emp-col
#      (строка без столбца); НОВЫЕ слушатели на телах итогов
#      (#wsTtBody/#wsTtPageBody, архив мимо); яркость: строка/столбец
#      0.30/0.22 (= «сегодня»), пересечение 0.34/0.26, шапка
#      0.40/0.26 (= «сегодня»), строка шторки 0.30/0.22.
#   3) «В окнах мероприятий и норм бара убери боковую полосу
#      прокрутки (останется свайп/колесо/клавиши ↑↓), вместо неё —
#      значок полного раскрытия в правом нижнем углу, со смещением
#      нижней части окна вниз по количеству текста; значок меняет
#      контрастность, когда не активен» — scrollbar-width:none +
#      ::-webkit-scrollbar display:none (как Task 331), tabindex="0"
#      (клавиатурный скролл), значок .ws-bar-exp (шеврон, opacity 0.45
#      не активен / 1 при наведении-фокусе-раскрытии), JS
#      _barExpSync/_barExpToggle/_barExpSyncAll: клик — высота
#      scrollHeight, повторный — 95px.
# Правки по якорям (уникальность проверяется), каждая с меткой.
import sys, io

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
orig = src
edits = []

def edit(old, new, label):
    global src
    i = src.find(old)
    if i == -1:
        print('FAIL not found: ' + label); sys.exit(1)
    if src.find(old, i + 1) != -1:
        print('FAIL dup: ' + label); sys.exit(1)
    src = src[:i] + new + src[i + len(old):]
    edits.append(label)

# ============================================================
# ЧАСТЬ 1. ИТОГИ УЧЁТА: линии/фоны как в шахматке, зебра — прочь
# ============================================================

# 1.1 базовые линии th/td: цвет ячеек дней сетки (Task 355/377)
edit("""    .ws-tt-table th,
    .ws-tt-table td {
        padding: 4px 8px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        /* Task 325: тонкая вертикальная линия между ячейками */
        border-right: 1px solid rgba(255,255,255,0.07);""",
     """    .ws-tt-table th,
    .ws-tt-table td {
        padding: 4px 8px;
        /* Task 378 (заявка: «разделительные полосы ячеек — как в
           основной шахматке»): базовый цвет линий — ЯЧЕЕК ДНЕЙ сетки
           (Task 355/377): тёмная rgba(0,0,0,0.30); шапке и колонке
           «Сотрудник» — свои стале-синие (правила Task 378 ниже) */
        border-bottom: 1px solid rgba(0, 0, 0, 0.30);
        border-right: 1px solid rgba(0, 0, 0, 0.30);""",
     '1.1 базовые линии итогов rgba(0,0,0,0.30)')

# 1.2 светлая тема: линии rgb(10,15,23) + НОВЫЙ блок Task 378
#     (шапка-сталь, ФИО-сталь, ячейки значений #FFFFFF/#eef0f2,
#      цветные колонки в тёмной — палитра светлой)
edit("""    [data-theme="light"] .ws-tt-table th,
    [data-theme="light"] .ws-tt-table td {
        border-bottom-color: rgba(0, 0, 0, 0.08);
        border-right-color: rgba(0, 0, 0, 0.08);
    }""",
     """    [data-theme="light"] .ws-tt-table th,
    [data-theme="light"] .ws-tt-table td {
        /* Task 378: непрозрачный цвет линий дней шахматки (Task 377) */
        border-bottom-color: rgb(10, 15, 23);
        border-right-color: rgb(10, 15, 23);
    }
    /* Task 378 (заявка: «фон пустых ячеек — #FFFFFF; в ячейках итогов
       учёта, где нуль — просто пусто; разделительные полосы — как в
       основной шахматке»): ячейки ЗНАЧЕНИЙ таблиц итогов — непрозрачные
       и СВЕТЛЫЕ, как поле дней шахматки: светлая тема — #FFFFFF
       (заявка), тёмная — светлые цвета шахматки дней Task 319
       (#eef0f2 под фильтром brightness(0.88), текст тёмный #141413).
       ЗЕБРА строк (Task 322, ниже) УБРАТА — непрозрачные ячейки её не
       просвечивают (зебра КОЛОНКИ ФИО сетки остаётся — своя фича).
       Линии: значения — цвет дней сетки (базовое правило выше),
       шапка — сталь как шапка сетки, «Сотрудник» — сталь как ФИО
       сетки. Колонки «Часы»/«Переработка» в тёмной теме — палитра
       светлой (ячейки-то светлые) */
    .ws-tt-table thead th {
        border-bottom-color: rgba(140, 158, 188, 0.55);
        border-right-color: rgba(140, 158, 188, 0.55);
    }
    .ws-tt-table tbody td.ws-tt-emp {
        border-bottom-color: rgba(105, 130, 160, 0.55);
        border-right-color: rgba(105, 130, 160, 0.55);
    }
    [data-theme="light"] .ws-tt-table thead th {
        border-bottom-color: rgb(83, 96, 117);
        border-right-color: rgb(83, 96, 117);
    }
    [data-theme="light"] .ws-tt-table tbody td.ws-tt-emp {
        border-bottom-color: rgb(64, 80, 102);
        border-right-color: rgb(64, 80, 102);
    }
    [data-theme="light"] .ws-tt-table tbody td.ws-tt-num {
        background: #FFFFFF;
    }
    [data-theme="dark"] .ws-tt-table tbody td.ws-tt-num {
        background: #eef0f2;
        color: #141413;
        filter: brightness(0.88);
    }
    [data-theme="dark"] .ws-tt-table td.ws-tt-hours { color: #1d7a37; }
    [data-theme="dark"] .ws-tt-table td.ws-tt-over { color: #a06a13; }""",
     '1.2 светлые линии rgb(10,15,23) + блок Task 378 (фоны/шапка/ФИО)')

# 1.3 зебра строк итогов — УДАЛЕНА (ячейки непрозрачные)
edit("""    /* Task 322 (заявка): ЗЕБРА строк таблицы итогов — чётные строки
       заметно светлее фона панели (визуальное чередование как у
       табеля Т-12; сила 9% — подобрана по VLM-проверке Task 322);
       итоговая строка красится своей заливкой (правило ниже, её
       td имеют собственный фон — зебра их не трогает) */
    .ws-tt-table tbody tr:nth-child(even) {
        background: rgba(255, 255, 255, 0.09);
    }
    [data-theme="light"] .ws-tt-table tbody tr:nth-child(even) {
        background: rgba(0, 0, 0, 0.07);
    }
""",
     """    /* Task 378 (заявка: «фон пустых ячеек #FFFFFF … как в основной
       шахматке»): ЗЕБРА строк таблицы итогов (Task 322) УДАЛЕНА —
       ячейки значений стали НЕПРОЗРАЧНЫМИ (#FFFFFF / #eef0f2×0.88,
       правила Task 378 выше) и полосы зебры больше не просвечивают;
       поле итогов — чистое белое с линиями шахматки, как заявлено */
""",
     '1.3 зебра строк итогов удалена')

# 1.4 подсветка строки шторки — яркость «сегодня» (0.30/0.22)
edit("""    /* Task 333 (заявка): ПЕРЕКРЁСТНАЯ ПОДСВЕТКА распространяется и на
       СТРОКИ ШТОРКИ — класс ws-hover-row на <tr> таблицы итогов
       ставит _rowClass (вместе со строкой сетки, тот же индекс).
       Заливка — тот же приём inset-«шторки», что у сетки (Task 319):
       мягкий тинт поверх зебры и фона sticky-колонки «Сотрудник»;
       тёмная 0.10 / светлая 0.06 — как строка сетки */
    .ws-tt-table tbody tr.ws-hover-row td {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.10);
    }
    [data-theme="light"] .ws-tt-table tbody tr.ws-hover-row td {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.06);
    }""",
     """    /* Task 333 (заявка): ПЕРЕКРЁСТНАЯ ПОДСВЕТКА распространяется и на
       СТРОКИ ШТОРКИ — класс ws-hover-row на <tr> таблицы итогов
       ставит _rowClass (вместе со строкой сетки, тот же индекс).
       Заливка — тот же приём inset-«шторки», что у сетки (Task 319),
       поверх непрозрачных ячеек Task 378; Task 378 (заявка: «подсветку
       перекрестья — такой же яркости, как подсветку текущего дня»):
       тёмная 0.10 → 0.30 / светлая 0.06 → 0.22 — уровень «сегодня» */
    .ws-tt-table tbody tr.ws-hover-row td {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }
    [data-theme="light"] .ws-tt-table tbody tr.ws-hover-row td {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }""",
     '1.4 строка шторки 0.30/0.22 (= сегодня)')

# ============================================================
# ЧАСТЬ 2. ПЕРЕКРЕСТЬЕ = ЯРКОСТЬ «СЕГОДНЯ» (тёмная тема)
# ============================================================

edit("""    .ws-grid tbody td.ws-cell.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.16);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-hover {
        /* Task 378 (заявка: «подсветку перекрестья — такой же яркости,
           как подсветку текущего дня»): 0.16 → 0.30 (= «сегодня») */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }""",
     '2.1 тёмная: столбец наведения 0.30')

edit("""    .ws-grid tbody td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.16),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.2 тёмная: столбец+manual 0.30')

edit("""    .ws-grid tbody td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-sel {
        /* Task 378: выбранный день — 0.24 → 0.30 (паритет с наведением
           и «сегодня»; пересечения — насыщеннее, правила ниже) */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }""",
     '2.3 тёмная: выбранный столбец 0.30')

edit("""    .ws-grid tbody td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.4 тёмная: выбранный+manual 0.30')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.10);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell {
        /* Task 378: строка перекрестья 0.10 → 0.30 (= «сегодня») */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }""",
     '2.5 тёмная: строка перекрестья 0.30')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.10),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.6 тёмная: строка+manual 0.30')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        /* Task 377: 0.20 → 0.32 — «сегодня» сильнее строки */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.32);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        /* Task 377 → 378: «сегодня» в строке — 0.32 → 0.34 (строка
           теперь 0.30; пересечение чуть насыщеннее) */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }""",
     '2.7 тёмная: строка+сегодня 0.34')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.32),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.8 тёмная: строка+сегодня+manual 0.34')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover {
        /* Task 378: пересечение строки и столбца — 0.24 → 0.34 */
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }""",
     '2.9 тёмная: пересечение 0.34')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.10 тёмная: пересечение+manual 0.34')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }""",
     '2.11 тёмная: строка+выбор 0.34')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.12 тёмная: строка+выбор+manual 0.34')

edit("""    .ws-grid tbody td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }""",
     '2.13 тёмная: сегодня+наведение 0.34')

edit("""    .ws-grid tbody td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.14 тёмная: сегодня+наведение+manual 0.34')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.36);
    }""",
     '2.15 тёмная: строка+сегодня+наведение 0.36')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.34),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.36),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '2.16 тёмная: строка+сегодня+наведение+manual 0.36')

edit("""    .ws-grid tbody tr.ws-hover-row td.ws-emp-col {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.10);
    }""",
     """    .ws-grid tbody tr.ws-hover-row td.ws-emp-col {
        box-shadow: inset 0 0 0 999px rgba(74, 143, 199, 0.30);
    }""",
     '2.17 тёмная: ФИО-ячейка строки 0.30')

edit("""    .ws-grid thead th.ws-day-col.ws-hover-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.20), rgba(74, 143, 199, 0.20));
        color: var(--accent-blue, #4a8fc7);
    }""",
     """    .ws-grid thead th.ws-day-col.ws-hover-col {
        /* Task 378: дата под курсором — 0.20 → 0.40 (= «сегодня»
           Task 377): перекрестье той же яркости, что текущий день */
        background-image: linear-gradient(rgba(74, 143, 199, 0.40), rgba(74, 143, 199, 0.40));
        color: var(--accent-blue, #4a8fc7);
    }""",
     '2.18 тёмная: шапка hover-col 0.40')

edit("""    .ws-grid thead th.ws-day-col.ws-sel-col {
        background-image: linear-gradient(rgba(74, 143, 199, 0.30), rgba(74, 143, 199, 0.30));
        color: var(--accent-blue, #4a8fc7);
    }""",
     """    .ws-grid thead th.ws-day-col.ws-sel-col {
        /* Task 378: выбранная дата — 0.30 → 0.40 (паритет с наведением
           и «сегодня»; составное «сегодня+выбор» — 0.44, как прежде) */
        background-image: linear-gradient(rgba(74, 143, 199, 0.40), rgba(74, 143, 199, 0.40));
        color: var(--accent-blue, #4a8fc7);
    }""",
     '2.19 тёмная: шапка sel-col 0.40')

# ============================================================
# ЧАСТЬ 3. ПЕРЕКРЕСТЬЕ = «СЕГОДНЯ» (светлая тема)
# ============================================================

edit("""    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.10);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-hover {
        /* Task 378: 0.10 → 0.22 (= «сегодня» светлой темы) */
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }""",
     '3.1 светлая: столбец наведения 0.22')

edit("""    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.10),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.2 светлая: столбец+manual 0.22')

edit("""    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.15);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }""",
     '3.3 светлая: выбранный столбец 0.22')

edit("""    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.15),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.4 светлая: выбранный+manual 0.22')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.06);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell {
        /* Task 378: строка перекрестья 0.06 → 0.22 (= «сегодня») */
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }""",
     '3.5 светлая: строка перекрестья 0.22')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.06),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.6 светлая: строка+manual 0.22')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        /* Task 377: 0.14 → 0.24 — «сегодня» сильнее строки */
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.24);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today {
        /* Task 377 → 378: 0.24 → 0.26 (строка теперь 0.22) */
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }""",
     '3.7 светлая: строка+сегодня 0.26')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.24),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.8 светлая: строка+сегодня+manual 0.26')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.16);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }""",
     '3.9 светлая: пересечение 0.26')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.16),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.10 светлая: пересечение+manual 0.26')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.15);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }""",
     '3.11 светлая: строка+выбор 0.26')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.15),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-sel.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.12 светлая: строка+выбор+manual 0.26')

edit("""    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }""",
     '3.13 светлая: сегодня+наведение 0.26')

edit("""    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.14 светлая: сегодня+наведение+manual 0.26')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.28);
    }""",
     '3.15 светлая: строка+сегодня+наведение 0.28')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.26),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-cell.ws-today.ws-hover.ws-source-manual {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.28),
                    inset 0 0 0 1.5px rgba(255,255,255,0.5);
    }""",
     '3.16 светлая: строка+сегодня+наведение+manual 0.28')

edit("""    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-emp-col {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.06);
    }""",
     """    [data-theme="light"] .ws-grid tbody tr.ws-hover-row td.ws-emp-col {
        box-shadow: inset 0 0 0 999px rgba(42, 93, 143, 0.22);
    }""",
     '3.17 светлая: ФИО-ячейка строки 0.22')

edit("""    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-hover-col {
        background-image: linear-gradient(rgba(42, 93, 143, 0.13), rgba(42, 93, 143, 0.13));
        color: #2a5d8f;
    }""",
     """    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-hover-col {
        /* Task 378: дата под курсором — 0.13 → 0.26 (= «сегодня») */
        background-image: linear-gradient(rgba(42, 93, 143, 0.26), rgba(42, 93, 143, 0.26));
        color: #2a5d8f;
    }""",
     '3.18 светлая: шапка hover-col 0.26')

edit("""    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-sel-col {
        background-image: linear-gradient(rgba(42, 93, 143, 0.20), rgba(42, 93, 143, 0.20));
        color: #2a5d8f;
    }""",
     """    [data-theme="light"] .ws-grid thead th.ws-day-col.ws-sel-col {
        background-image: linear-gradient(rgba(42, 93, 143, 0.26), rgba(42, 93, 143, 0.26));
        color: #2a5d8f;
    }""",
     '3.19 светлая: шапка sel-col 0.26')

# ============================================================
# ЧАСТЬ 4. ОКНА БАРА: без полосы прокрутки + значок раскрытия (CSS)
# ============================================================

edit("""    .ws-events-panel[hidden] { display: none; }""",
     """    .ws-events-panel[hidden] { display: none; }
    /* Task 378 (заявка): боковая ПОЛОСА ПРОКРУТКИ окон «Мероприятия»
       и «Нормы» бара УБРАТА (приём Task 331 — оба движка): скролл
       остаётся КОЛЕСОМ/СВАЙПОМ/КЛАВИШАМИ ↑↓ (окна фокусируемы —
       tabindex в разметке). ВМЕСТО полосы — ЗНАЧОК полного раскрытия
       .ws-bar-exp в правом нижнем углу (создаёт/обновляет
       _barExpSync): клик раскрывает окно на ВЕСЬ текст — низ
       смещается вниз по количеству текста (инлайновая высота =
       scrollHeight, плавный transition), повторный клик возвращает
       95px. Значок НЕ активен (окно свёрнуто) — приглушён
       контрастом (opacity 0.45); наведение/фокус/раскрытие — полная
       контрастность; шеврон ПОВОРАЧИВАЕТСЯ на 180°. Виден значок
       только когда текст НЕ влезает (или окно уже раскрыто) */
    .ws-events-panel {
        position: relative;          /* якорь значка .ws-bar-exp */
        transition: height 0.18s ease;
        scrollbar-width: none;       /* Firefox: полоса скрыта */
        -ms-overflow-style: none;    /* IE/legacy Edge */
    }
    .ws-cal-panel {
        position: relative;
        transition: height 0.18s ease;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .ws-events-panel::-webkit-scrollbar,
    .ws-cal-panel::-webkit-scrollbar {
        width: 0;
        height: 0;
        display: none;               /* Chromium: полоса скрыта */
    }
    .ws-events-panel:focus-visible,
    .ws-cal-panel:focus-visible {
        outline: 1px solid rgba(74, 143, 199, 0.55);
        outline-offset: -1px;
    }
    .ws-bar-exp {
        position: absolute;
        right: 5px;
        bottom: 5px;
        z-index: 2;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        padding: 0;
        border: 1px solid rgba(127, 127, 127, 0.45);
        border-radius: 3px;
        background: rgba(127, 127, 127, 0.25);
        color: var(--text-primary, #e0e0e0);
        cursor: pointer;
        /* НЕ активен (свёрнуто) — приглушён контрастом (заявка) */
        opacity: 0.45;
        transition: opacity 0.15s ease;
    }
    .ws-bar-exp:hover,
    .ws-bar-exp:focus-visible { opacity: 1; }
    .ws-bar-exp.on { opacity: 1; }   /* раскрыто — контрастно */
    .ws-bar-exp svg {
        width: 13px;
        height: 13px;
        transition: transform 0.18s ease;
    }
    .ws-bar-exp.on svg { transform: rotate(180deg); }
    [data-theme="light"] .ws-bar-exp { color: #222; }""",
     '4.1 окна бара: скрытие полосы + значок .ws-bar-exp (CSS)')

# 4.2-4.3 tabindex — клавиатурный скролл колёсика заменителя
edit("""                <div id="wsEventsPanel" class="ws-events-panel" hidden></div>""",
     """                <!-- Task 378: tabindex — окно фокусируемо, скролл
                     стрелками ↑↓ клавиатуры (полоса прокрутки убрана
                     CSS; значок раскрытия добавляет _barExpSync) -->
                <div id="wsEventsPanel" class="ws-events-panel" hidden tabindex="0"></div>""",
     '4.2 tabindex окна мероприятий')

edit("""                <div id="wsCalPanel" class="ws-cal-panel" hidden></div>""",
     """                <!-- Task 378: tabindex — клавиатурный скролл ↑↓ -->
                <div id="wsCalPanel" class="ws-cal-panel" hidden tabindex="0"></div>""",
     '4.3 tabindex окна норм')

# ============================================================
# ЧАСТЬ 5. JS: нули → пустые ячейки (месячная таблица итогов)
# ============================================================

edit("""                    var v = (col.key === 'over') ? a.overDays : a[col.key];
                    var txt = (col.key === 'hours')
                        ? this._fmtTotalsNum(v)
                        : String(v);""",
     """                    var v = (col.key === 'over') ? a.overDays : a[col.key];
                    // Task 378 (заявка: «в ячейках итогов учёта, где
                    // нуль — просто пусто»): ноль (и отформатированные
                    // «0» часы) — ПУСТАЯ ячейка; ненулевые — как прежде
                    var txt = v
                        ? ((col.key === 'hours')
                            ? this._fmtTotalsNum(v)
                            : String(v))
                        : '';""",
     '5.1 нули итогов → пустые ячейки')

# ============================================================
# ЧАСТЬ 6. JS: перекрестье — ФИО и ячейки итогов
# ============================================================

edit("""            var gridWrapEl = document.getElementById('wsGridWrap');
            if (gridWrapEl && gridWrapEl.addEventListener) {
                gridWrapEl.addEventListener('mouseover', function(e) {
                    var td = null;
                    try {
                        if (e.target && e.target.closest) {
                            td = e.target.closest('td.ws-cell');
                        }
                    } catch (err) {}
                    if (!td) return;
                    if (self._crossOn === false) return;   // Task 328
                    var day = parseInt(td.getAttribute('data-day'), 10);
                    var tr = (td.closest ? td.closest('tr') : null);
                    var ri = tr ? tr.sectionRowIndex : -1;
                    if (isNaN(day) || ri < 0) return;
                    self._cellHover(ri, day);
                });
                gridWrapEl.addEventListener('mouseout', function(e) {
                    var td = null;
                    try {
                        if (e.target && e.target.closest) {
                            td = e.target.closest('td.ws-cell');
                        }
                    } catch (err) {}
                    if (!td) return;
                    var to = e.relatedTarget;
                    if (to && to.closest && to.closest('td.ws-cell')) return;
                    self._cellHover(null);
                });
            }""",
     """            var gridWrapEl = document.getElementById('wsGridWrap');
            if (gridWrapEl && gridWrapEl.addEventListener) {
                gridWrapEl.addEventListener('mouseover', function(e) {
                    var td = null;
                    try {
                        if (e.target && e.target.closest) {
                            // Task 378 (заявка): наведение на ячейку
                            // ФИО сотрудника ТОЖЕ подсвечивает СТРОКУ —
                            // ловим и td.ws-emp-col (день не определён:
                            // _dayHover(null) снимает подсветку столбца)
                            td = e.target.closest('td.ws-cell, td.ws-emp-col');
                        }
                    } catch (err) {}
                    if (!td) return;
                    if (self._crossOn === false) return;   // Task 328
                    var isDayCell = td.classList.contains('ws-cell');
                    var day = isDayCell ? parseInt(td.getAttribute('data-day'), 10) : null;
                    var tr = (td.closest ? td.closest('tr') : null);
                    var ri = tr ? tr.sectionRowIndex : -1;
                    if (ri < 0 || (isDayCell && isNaN(day))) return;
                    self._cellHover(ri, day);
                });
                gridWrapEl.addEventListener('mouseout', function(e) {
                    var td = null;
                    try {
                        if (e.target && e.target.closest) {
                            td = e.target.closest('td.ws-cell, td.ws-emp-col');
                        }
                    } catch (err) {}
                    if (!td) return;
                    var to = e.relatedTarget;
                    if (to && to.closest && to.closest('td.ws-cell, td.ws-emp-col')) return;
                    self._cellHover(null);
                });
            }

            // Task 378 (заявка: «подсвечивание строк при наведении на
            // ячейки итогов учёта»): таблицы шторки и мобильной
            // страницы идут по строкам сетки (Task 333) — наведение
            // на их ячейки подсвечивает СТРОКУ (_rowHover красит и
            // сетку, и итоги); АРХИВНАЯ таблица года (.ws-tt-arch)
            // пропускается — её строки не соответствуют строкам сетки.
            // Гейт перекрестья тот же (_crossOn); уход с ячеек —
            // _rowHover(null)
            var ttBodies = [document.getElementById('wsTtBody'),
                            document.getElementById('wsTtPageBody')];
            for (var tb = 0; tb < ttBodies.length; tb++) {
                (function(ttBody) {
                    if (!ttBody || !ttBody.addEventListener) return;
                    ttBody.addEventListener('mouseover', function(e) {
                        if (self._crossOn === false) return;
                        var td = null;
                        try {
                            if (e.target && e.target.closest) {
                                td = e.target.closest('tbody td');
                            }
                        } catch (err) {}
                        if (!td) return;
                        var table = (td.closest ? td.closest('table') : null);
                        if (table && table.classList
                                && table.classList.contains('ws-tt-arch')) return;
                        var tr = (td.closest ? td.closest('tr') : null);
                        var ri = tr ? tr.sectionRowIndex : -1;
                        if (ri < 0) return;
                        self._rowHover(ri);
                    });
                    ttBody.addEventListener('mouseout', function(e) {
                        var td = null;
                        try {
                            if (e.target && e.target.closest) {
                                td = e.target.closest('tbody td');
                            }
                        } catch (err) {}
                        if (!td) return;
                        var to = e.relatedTarget;
                        if (to && to.closest && to.closest('tbody td')) return;
                        self._rowHover(null);
                    });
                })(ttBodies[tb]);
            }""",
     '6.1 делегирование: ФИО + ячейки итогов (слушатели)')

# ============================================================
# ЧАСТЬ 7. JS: значок раскрытия окон бара (_barExp*)
# ============================================================

edit("""        _renderMonthEventsPanel: function() {
            var el = document.getElementById('wsEventsPanel');
            if (!el) return;""",
     """        // ============================================================
        // Task 378 (заявка): ЗНАЧОК ПОЛНОГО РАСКРЫТИЯ окон бара
        // («Мероприятия»/«Нормы»). Нативная полоса прокрутки окон
        // УБРАНА (CSS: scrollbar-width:none + ::-webkit-scrollbar
        // display:none — скролл остаётся колесом/свайпом/клавишами ↑↓,
        // окна фокусируемы tabindex). ВМЕСТО полосы — значок-шеврон
        // в правом нижнем углу: клик раскрывает окно на ВЕСЬ текст
        // (низ смещается вниз по количеству текста — инлайновая
        // высота = scrollHeight), повторный клик возвращает 95px.
        // Значок виден, только когда текст НЕ влезает (или окно уже
        // раскрыто); НЕ активен — приглушён контрастом (CSS opacity
        // 0.45), наведение/фокус/раскрытие — полная контрастность.
        // Рендеры окон заменяют innerHTML ЦЕЛИКОМ — значок (пере)-
        // создаётся после каждого рендера; раскрытое состояние — класс
        // ws-bar-open на самом окне (переживает перерисовки), высота
        // пересчитывается под НОВЫЙ объём текста
        // ============================================================
        _barExpSync: function(el) {
            if (!el) return;
            var btn = el.querySelector('.ws-bar-exp');
            if (!btn) {
                btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'ws-bar-exp';
                btn.setAttribute('aria-label', 'Раскрыть окно целиком');
                btn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';
                var self = this;
                btn.onclick = function() { self._barExpToggle(el); };
                el.appendChild(btn);
            }
            var open = el.classList.contains('ws-bar-open');
            // 97 = компактная высота окон 95px (CSS) + допуск 2px:
            // scrollHeight не зависит от текущей (анимируемой) высоты
            var need = el.scrollHeight > 97;
            if (open && !need) {
                // текст перестал переполняться (смена месяца/дня) —
                // свернуть, значок спрятать
                el.classList.remove('ws-bar-open');
                el.style.height = '';
                open = false;
            } else if (open) {
                // остаёмся раскрытыми — низ окна следует за НОВЫМ
                // объёмом текста (замер после перерисовки)
                el.style.height = el.scrollHeight + 'px';
            }
            btn.classList.toggle('on', open);
            btn.style.display = (need || open) ? '' : 'none';
        },

        // Task 378: клик по значку — раскрыть/свернуть окно бара
        _barExpToggle: function(el) {
            if (!el) return;
            var open = el.classList.contains('ws-bar-open');
            if (open) {
                el.classList.remove('ws-bar-open');
                el.style.height = '';
            } else {
                el.classList.add('ws-bar-open');
                el.style.height = el.scrollHeight + 'px';
            }
            this._barExpSync(el);
        },

        // Task 378: пересчёт обоих окон бара (мероприятия + нормы)
        _barExpSyncAll: function() {
            this._barExpSync(document.getElementById('wsEventsPanel'));
            this._barExpSync(document.getElementById('wsCalPanel'));
        },

        _renderMonthEventsPanel: function() {
            var el = document.getElementById('wsEventsPanel');
            if (!el) return;""",
     '7.1 методы _barExpSync/_barExpToggle/_barExpSyncAll')

# 7.2 вызов после рендера окна мероприятий
edit("""                        '<span class="ws-ep-text">' + this._esc(text) + '</span></span>';
            }
            el.innerHTML = html;
            el.hidden = false;
        },""",
     """                        '<span class="ws-ep-text">' + this._esc(text) + '</span></span>';
            }
            el.innerHTML = html;
            el.hidden = false;
            // Task 378: значок раскрытия — (пере)создать/пересчитать
            // (innerHTML окна заменился целиком)
            this._barExpSync(el);
        },""",
     '7.2 _barExpSync после рендера мероприятий')

# 7.3 вызов после рендера окна норм (ProdCalendar.renderPanel)
edit("""            html += '<span class="ws-cp-legend">* — сокращённый предпраздничный день (−1 час)</span>' +
                    '</div>';

            el.innerHTML = html;
            el.hidden = false;
        },""",
     """            html += '<span class="ws-cp-legend">* — сокращённый предпраздничный день (−1 час)</span>' +
                    '</div>';

            el.innerHTML = html;
            el.hidden = false;
            // Task 378: значок раскрытия окна норм — (пере)создать
            // (метод WorkSchedule: у календаря своей копии нет)
            if (typeof WorkSchedule !== 'undefined'
                    && WorkSchedule._barExpSync) {
                WorkSchedule._barExpSync(el);
            }
        },""",
     '7.3 _barExpSync после рендера норм')

# 7.4 мобильные чипы: окно ПОКАЗАНО — пересчёт значка
edit("""            if (on && typeof navigator !== 'undefined' && navigator.vibrate) {
                navigator.vibrate(10);
            }
        },

        // Открытие мобильной СТРАНИЦЫ «Итоги учёта» (вызов из navigateTo""",
     """            if (on && typeof navigator !== 'undefined' && navigator.vibrate) {
                navigator.vibrate(10);
            }
            // Task 378: окно ПОКАЗАНО чипом — пересчёт значка раскрытия
            // (скрытое окно меряется нулём, состояние могло устареть)
            if (this._barExpSyncAll) this._barExpSyncAll();
        },

        // Открытие мобильной СТРАНИЦЫ «Итоги учёта» (вызов из navigateTo""",
     '7.4 toggleMobPanel → _barExpSyncAll')

# 7.5 ресайз окна — перенос текста окон бара меняется
edit("""                window.addEventListener('resize', function() {
                    self._fitGrid();
                });
            }""",
     """                window.addEventListener('resize', function() {
                    self._fitGrid();
                });
            }
            // Task 378: перенос текста окон бара зависит от ширины окна
            // — пересчёт значков раскрытия при ресайзе (наблюдатель
            // сетки не видит переразмещений текста внутри окон)
            window.addEventListener('resize', function() {
                try { self._barExpSyncAll(); } catch (e) {}
            });""",
     '7.5 ресайз → _barExpSyncAll')

# 7.6 поздняя загрузка шрифта — повторный замер + пересчёт значков
edit("""                document.fonts.ready.then(function() {
                    try { self._measureEmpCol(); } catch (e) {}
                    // Task 336: суженная ширина (по сокращённому тексту)
                    // — тот же повторный замер после загрузки шрифта
                    try { if (self._measureEmpNarrowW) self._measureEmpNarrowW(); } catch (e) {}
                });""",
     """                document.fonts.ready.then(function() {
                    try { self._measureEmpCol(); } catch (e) {}
                    // Task 336: суженная ширина (по сокращённому тексту)
                    // — тот же повторный замер после загрузки шрифта
                    try { if (self._measureEmpNarrowW) self._measureEmpNarrowW(); } catch (e) {}
                    // Task 378: шрифт меняет перенос текста окон бара —
                    // пересчёт значков раскрытия
                    try { if (self._barExpSyncAll) self._barExpSyncAll(); } catch (e) {}
                });""",
     '7.6 fonts.ready → _barExpSyncAll')

io.open(PATH, 'w', encoding='utf-8').write(src)
print('OK: %d правок, %d байт → %d байт' % (len(edits), len(orig), len(src)))
for e in edits:
    print('  ✓ ' + e)
