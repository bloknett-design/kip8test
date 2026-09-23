#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 396 (заявка, kip8test):
#   (1) «В блоках карт работников, цвет фона чередующихся строк
#       сделай зеброй» — вторая/четвёртая… строка каждого блока
#       (профиль/отпуска/мероприятия/СИЗ) с чередующимся фоном
#       ws-row-alt (только у блоков-окон asBlocks — попап шахматки
#       без зебры; оттенок — как зебра сводной таблицы «Общей»);
#   (2) «В блоке профиля, кнопки правки данных и увольнения
#       оформи в виде компактных кнопок и перемести в верхний
#       правый угол блока, также сделай с кнопками в остальных
#       блоках» — «Правка данных…»/«Уволить…» (профиль) и
#       «+ Отпуск…»/«+ Мероприятие…»/«+ СИЗ…» (свои блоки) —
#       КОМПАКТНЫЕ кнопки .ws-wbtn 26px в шапке .ws-whead-a
#       блока; контракты onclick и классы-маркеры прежние;
#       легаси-строки внизу блока остаются для вида без asBlocks
#       (попап-совместимый путь, гейт withEdit && !asBlocks);
#   (3) «В верхних строках оглавления блоков, шрифт сделай немного
#       больше и ярче, и выдели другим фоном» — шапка-полоса
#       .ws-whead на всю ширину окна (тёмная #1E2B42 / светлая
#       #E4E0D3 — как выделенная шапка сводки .ws-wgen-head
#       Task 390); заголовок ФИО 16px/700/первичный цвет, секции
#       13px/700/первичный (было 12px/600/вторичный).
import io, sys

PATH = 'index.html'
src = io.open(PATH, encoding='utf-8').read()
n0 = src

def rep(old, new, what, count=1):
    global src
    found = src.count(old)
    assert found == count, '%s: найдено %d (ожидалось %d)' % (what, found, count)
    src = src.replace(old, new)
    print('  ✓ %s' % what)

# ============================================================
# 1. JS — _renderWorkerCard: шапки .ws-whead с компактными
#    кнопками (asBlocks), зебра строк, легаси-гейты строк
# ============================================================

# --- 1.1 b1: шапка профиля — полоса .ws-whead + кнопки в углу ---
rep(
"""            // Task 393: карточка собирается ЧЕТЫРЬМЯ блоками — b1
            // профиль+действия, b2 отпуска, b3 мероприятия, b4 СИЗ;
            // склейка/массив — в возврате метода (см. ниже)
            var b1 = '<div class="ws-popup-title">' + this._esc(emp['ФИО']) +
                     ' · таб. №' + this._esc(emp['таб_номер']) + '</div>';
""",
"""            // Task 393: карточка собирается ЧЕТЫРЬМЯ блоками — b1
            // профиль+действия, b2 отпуска, b3 мероприятия, b4 СИЗ;
            // склейка/массив — в возврате метода (см. ниже)
            // Task 396 (заявка): у блоков-окон (asBlocks, страница
            // «Работники») шапка — ВЫДЕЛЕННАЯ ПОЛОСА .ws-whead с
            // КОМПАКТНЫМИ кнопками действий в ВЕРХНЕМ ПРАВОМ углу
            // («Правка данных…» + «Уволить…» — шапка блока профиля;
            // контракты onclick и классы-маркеры прежние). Вид без
            // asBlocks (попап шахматки) — прежний .ws-popup-title,
            // строки действий — внизу блока (гейт ниже)
            var b1Acts = '';
            if (withEdit) {
                b1Acts = '<button type="button" class="ws-wbtn ws-emp-editdata"' +
                         ' title="Правка данных работника: ФИО, режим, должность…"' +
                         ' onclick="WorkSchedule.openEmpEditForm(\\'' +
                         this._esc(String(emp['таб_номер'] || '')) + '\\')">Правка данных…</button>' +
                         '<button type="button" class="ws-wbtn ws-wbtn-danger ws-emp-dismiss"' +
                         ' title="Увольнение: записать дату, убрать из графика"' +
                         ' onclick="WorkSchedule.openDismissForm(\\'' +
                         this._esc(String(emp['таб_номер'] || '')) + '\\')">Уволить…</button>';
            }
            var b1 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t ws-whead-name">' +
                  this._esc(emp['ФИО']) + ' · таб. №' +
                  this._esc(emp['таб_номер']) +
                  '</div><div class="ws-whead-a">' + b1Acts + '</div></div>'
                : '<div class="ws-popup-title">' + this._esc(emp['ФИО']) +
                  ' · таб. №' + this._esc(emp['таб_номер']) + '</div>';
""", 'b1: шапка .ws-whead + кнопки «Правка данных…»/«Уволить…» в углу')

# --- 1.2 зебра полей профиля (счётчик РЕНДЕРЯЩИХСЯ строк) ---
rep(
"""            for (var fi = 0; fi < fields.length; fi++) {
""",
"""            // Task 396 (заявка): ЗЕБРА — чередующийся фон вторых
            // строк блока (класс ws-row-alt — только asBlocks;
            // попап шахматки без зебры)
            var fRow = 0;
            for (var fi = 0; fi < fields.length; fi++) {
""", 'b1: счётчик строк зебры fRow')

rep(
"""                b1 += '<div class="ws-emp-field"><span class="ws-emp-k">' +
                      this._esc(fields[fi][0]) + '</span><span class="ws-emp-v">' +
                      this._esc(fields[fi][1]) + '</span></div>';
            }
""",
"""                b1 += '<div class="ws-emp-field' +
                      ((asBlocks && fRow % 2 === 1) ? ' ws-row-alt' : '') +
                      '"><span class="ws-emp-k">' +
                      this._esc(fields[fi][0]) + '</span><span class="ws-emp-v">' +
                      this._esc(fields[fi][1]) + '</span></div>';
                fRow++;
            }
""", 'b1: поля профиля — класс зебры')

# --- 1.3 легаси-строки b1 — только без asBlocks (совместимость) ---
rep(
"""            if (withEdit) {
                b1 += '<div class="ws-popup-row ws-popup-more ws-emp-editdata"' +
""",
"""            if (withEdit && !asBlocks) {
                b1 += '<div class="ws-popup-row ws-popup-more ws-emp-editdata"' +
""", 'b1: легаси-строка «Правка данных…» — гейт !asBlocks')

rep(
"""            if (withEdit) {
                b1 += '<div class="ws-popup-row ws-popup-more ws-emp-dismiss"' +
""",
"""            if (withEdit && !asBlocks) {
                b1 += '<div class="ws-popup-row ws-popup-more ws-emp-dismiss"' +
""", 'b1: легаси-строка «Уволить…» — гейт !asBlocks')

# --- 1.4 b2: шапка отпусков + кнопка «+ Отпуск…» в углу ---
rep(
"""            var b2 = '<div class="ws-popup-sec">Отпуска · ' + this._year + '</div>';
""",
"""            // Task 396: шапка блока отпусков — полоса .ws-whead,
            // кнопка «+ Отпуск…» — КОМПАКТНАЯ, в правом углу шапки
            // (asBlocks); легаси-вид попапа — прежняя секция
            // .ws-popup-sec, строка добавления — внизу блока
            var b2 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Отпуска · ' +
                  this._year + '</div><div class="ws-whead-a">' +
                  (withEdit ? '<button type="button" class="ws-wbtn ws-emp-addvac"' +
                  ' title="Добавить период отпуска этому работнику"' +
                  ' onclick="WorkSchedule.onEmpAddVacation(\\'' +
                  this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Отпуск…</button>' : '') +
                  '</div></div>'
                : '<div class="ws-popup-sec">Отпуска · ' + this._year + '</div>';
""", 'b2: шапка .ws-whead + кнопка «+ Отпуск…» в углу')

# --- 1.5 зебра строк отпусков ---
rep(
"""                    b2 += '<div class="ws-emp-field"><span class="ws-emp-k">Часть ' +
""",
"""                    b2 += '<div class="ws-emp-field' +
                          ((asBlocks && vk % 2 === 1) ? ' ws-row-alt' : '') +
                          '"><span class="ws-emp-k">Часть ' +
""", 'b2: строки отпусков — класс зебры')

# --- 1.6 легаси-строка «+ Отпуск…» — только без asBlocks ---
rep(
"""            if (withEdit) {
                b2 += '<div class="ws-popup-row ws-popup-more ws-emp-addvac"' +
""",
"""            if (withEdit && !asBlocks) {
                b2 += '<div class="ws-popup-row ws-popup-more ws-emp-addvac"' +
""", 'b2: легаси-строка «+ Отпуск…» — гейт !asBlocks')

# --- 1.7 b3: шапка мероприятий + кнопка «+ Мероприятие…» ---
# (формат легаси-ветки с прежним отступом продолжения — ассерт
#  test-task394 «Мероприятия · ' +\n…this._year + '</div>'»)
rep(
"""            var b3 = '<div class="ws-popup-sec">Мероприятия · ' +
                     this._year + '</div>';
""",
"""            // Task 396: шапка блока мероприятий — полоса .ws-whead,
            // кнопка «+ Мероприятие…» — КОМПАКТНАЯ, в правом углу
            var b3 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Мероприятия · ' +
                  this._year + '</div><div class="ws-whead-a">' +
                  (withEdit ? '<button type="button" class="ws-wbtn ws-emp-addtr"' +
                  ' title="Добавить мероприятие этому работнику"' +
                  ' onclick="WorkSchedule.onEmpAddTraining(\\'' +
                  this._esc(String(emp['таб_номер'] || '')) + '\\')">+ Мероприятие…</button>' : '') +
                  '</div></div>'
                : '<div class="ws-popup-sec">Мероприятия · ' +
                     this._year + '</div>';
""", 'b3: шапка .ws-whead + кнопка «+ Мероприятие…» в углу')

# --- 1.8 зебра строк мероприятий ---
rep(
"""                    b3 += '<div class="ws-popup-row ws-popup-event">' +
""",
"""                    b3 += '<div class="ws-popup-row ws-popup-event' +
                          ((asBlocks && tk % 2 === 1) ? ' ws-row-alt' : '') + '">' +
""", 'b3: строки мероприятий — класс зебры')

# --- 1.9 легаси-строка «+ Мероприятие…» — только без asBlocks ---
rep(
"""            if (withEdit) {
                b3 += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
""",
"""            if (withEdit && !asBlocks) {
                b3 += '<div class="ws-popup-row ws-popup-more ws-emp-addtr"' +
""", 'b3: легаси-строка «+ Мероприятие…» — гейт !asBlocks')

# --- 1.10 b4: шапка СИЗ + кнопка «+ СИЗ…» ---
rep(
"""            var b4 = '<div class="ws-popup-sec">СИЗ · средства индивидуальной защиты</div>';
""",
"""            // Task 396: шапка блока СИЗ — полоса .ws-whead,
            // кнопка «+ СИЗ…» — КОМПАКТНАЯ, в правом углу шапки
            var b4 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">СИЗ · средства индивидуальной защиты</div><div class="ws-whead-a">' +
                  (withEdit ? '<button type="button" class="ws-wbtn ws-emp-addppe"' +
                  ' title="Добавить СИЗ этому работнику"' +
                  ' onclick="WorkSchedule.onEmpAddPpe(\\'' +
                  this._esc(String(emp['таб_номер'] || '')) + '\\')">+ СИЗ…</button>' : '') +
                  '</div></div>'
                : '<div class="ws-popup-sec">СИЗ · средства индивидуальной защиты</div>';
""", 'b4: шапка .ws-whead + кнопка «+ СИЗ…» в углу')

# --- 1.11 зебра записей СИЗ ---
rep(
"""                    b4 += '<div class="ws-ppe-item">' +
""",
"""                    b4 += '<div class="ws-ppe-item' +
                          ((asBlocks && pk % 2 === 1) ? ' ws-row-alt' : '') + '">' +
""", 'b4: записи СИЗ — класс зебры')

# --- 1.12 легаси-строка «+ СИЗ…» — только без asBlocks ---
rep(
"""            if (withEdit) {
                b4 += '<div class="ws-popup-row ws-popup-more ws-emp-addppe"' +
""",
"""            if (withEdit && !asBlocks) {
                b4 += '<div class="ws-popup-row ws-popup-more ws-emp-addppe"' +
""", 'b4: легаси-строка «+ СИЗ…» — гейт !asBlocks')

# ============================================================
# 2. CSS — зебра (паддинги строк), шапка .ws-whead,
#    компактные кнопки .ws-wbtn
# ============================================================

# --- 2.1 строки — боковой паддинг под полосы-«пилюли» зебры ---
rep(
"""    .ws-wcard .ws-emp-field {
        font-size: 14px;
        padding: 4px 0;
    }
""",
"""    .ws-wcard .ws-emp-field {
        font-size: 14px;
        /* Task 396: боковой паддинг — полосы-«пилюли» ЗЕБРЫ строк */
        padding: 4px 10px;
    }
""", 'CSS: .ws-wcard .ws-emp-field — паддинг 4px 10px')

rep(
"""    .ws-wcard .ws-popup-row {
        font-size: 14px;
        padding: 8px 0;
    }
""",
"""    .ws-wcard .ws-popup-row {
        font-size: 14px;
        /* Task 396: боковой паддинг — полосы-«пилюли» ЗЕБРЫ строк */
        padding: 8px 10px;
    }
""", 'CSS: .ws-wcard .ws-popup-row — паддинг 8px 10px')

rep(
"""    .ws-wcard .ws-ppe-item {
        font-size: 14px;
        padding: 6px 0;
    }
""",
"""    .ws-wcard .ws-ppe-item {
        font-size: 14px;
        /* Task 396: боковой паддинг — полосы-«пилюли» ЗЕБРЫ строк */
        padding: 6px 10px;
    }
""", 'CSS: .ws-wcard .ws-ppe-item — паддинг 6px 10px')

# --- 2.2 пустые строки «нет …» — тот же отступ, что строки зебры ---
rep(
"""    .ws-wcard .ws-emp-empty {
        font-size: 13px;
        padding: 4px 0 6px;
    }
""",
"""    .ws-wcard .ws-emp-empty {
        font-size: 13px;
        /* Task 396: отступ — вровень с текстом строк зебры */
        padding: 4px 10px 6px;
    }
""", 'CSS: .ws-wcard .ws-emp-empty — паддинг вровень со строками')

# --- 2.3 НОВЫЕ правила: шапка .ws-whead + кнопки .ws-wbtn + зебра ---
rep(
"""    .ws-wcard .ws-popup-act {
        width: 26px;
        height: 26px;
        font-size: 13px;
    }
""",
"""    .ws-wcard .ws-popup-act {
        width: 26px;
        height: 26px;
        font-size: 13px;
    }
    /* Task 396 (заявка): ШАПКА-«ОГЛАВЛЕНИЕ» блока-окна .ws-whead —
       полоса НА ВСЮ ШИРИНУ окна (отрицательные поля гасят паддинг
       панели 14px 16px 12px, свой паддинг 9px 16px; скругление
       верхних углов 8px — внутренний радиус панели 10−2px рамки).
       Фон — ДРУГОЙ, как выделенная шапка сводки «Общей» вкладки
       (.ws-wgen-head, Task 390): тёмная #1E2B42, светлая #E4E0D3.
       Заголовок — ШРИФТ КРУПНЕЕ и ЯРЧЕ (Task 393: было 15px/600
       вторичный у ФИО и 12px/600 вторичный у секций): ФИО —
       16px/700/первичный цвет (ws-whead-name, без капса), секции
       — 13px/700/первичный (капс сохранён). Справа — компактные
       кнопки действий (ws-whead-a; margin-left:auto — при узком
       экране переносятся ниже, оставаясь ПРАВЕЕ). Попап шахматки
       — прежние .ws-popup-title/.ws-popup-sec (НЕ в .ws-wcard) */
    .ws-wcard .ws-whead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 6px 10px;
        margin: -14px -16px 10px;
        padding: 9px 16px;
        background: #1E2B42;
        border-bottom: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 8px 8px 0 0;
    }
    [data-theme="light"] .ws-wcard .ws-whead {
        background: #E4E0D3;
        border-bottom-color: rgba(0, 0, 0, 0.14);
    }
    .ws-wcard .ws-whead-t {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        color: var(--text-primary, #e0e0e0);
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .ws-wcard .ws-whead-t.ws-whead-name {
        /* ФИО · таб. № — крупнее секций, без капса */
        font-size: 16px;
        letter-spacing: 0.2px;
        text-transform: none;
    }
    .ws-wcard .ws-whead-a {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-left: auto;
        flex: none;
    }
    /* Task 396 (заявка): КОМПАКТНЫЕ кнопки действий шапки — стиль
       сайта (как «Добавить работника», Task 391): тёмная — СИНИЙ
       var(--accent-blue) #4a8fc7, светлая — ОРАНЖЕВЫЙ #C6613F,
       текст белый, hover/active — фильтром яркости. «Уволить…» —
       опасное действие КРАСНЫМ (#ef5350 / #c62828 — как ✕
       удалений). Контракты классов-маркеров (ws-emp-editdata/
       ws-emp-dismiss/ws-emp-addvac/ws-emp-addtr/ws-emp-addppe)
       и onclick — прежние */
    .ws-wbtn {
        height: 26px;
        padding: 0 11px;
        border-radius: 7px;
        border: 1px solid transparent;
        background: var(--accent-blue, #4a8fc7);
        color: #fff;
        font-size: 12px;
        line-height: 1;
        font-weight: 600;
        white-space: nowrap;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        -webkit-tap-highlight-color: transparent;
        user-select: none;
        flex: none;
    }
    .ws-wbtn:hover { filter: brightness(1.12); }
    .ws-wbtn:active { filter: brightness(0.9); }
    .ws-wbtn.ws-wbtn-danger { background: #ef5350; }
    [data-theme="light"] .ws-wbtn.ws-wbtn-danger { background: #c62828; }
    /* Task 396 (заявка): ЗЕБРА строк — чередующийся фон вторых
       строк каждого блока (класс ws-row-alt ставит
       _renderWorkerCard при asBlocks; попап шахматки — БЕЗ зебры).
       Оттенок — как зебра сводной таблицы «Общей» вкладки
       (Task 388); строки — «пилюли» со скруглением 6px */
    .ws-wcard .ws-emp-field,
    .ws-wcard .ws-popup-row,
    .ws-wcard .ws-ppe-item {
        border-radius: 6px;
    }
    .ws-wcard .ws-emp-field.ws-row-alt,
    .ws-wcard .ws-popup-row.ws-row-alt,
    .ws-wcard .ws-ppe-item.ws-row-alt {
        background: rgba(255, 255, 255, 0.045);
    }
    [data-theme="light"] .ws-wcard .ws-emp-field.ws-row-alt,
    [data-theme="light"] .ws-wcard .ws-popup-row.ws-row-alt,
    [data-theme="light"] .ws-wcard .ws-ppe-item.ws-row-alt {
        background: rgba(0, 0, 0, 0.05);
    }
""", 'CSS: НОВЫЕ правила .ws-whead/.ws-whead-t/.ws-whead-a/.ws-wbtn/зебра')

# ============================================================
# Контроль
# ============================================================
assert src != n0, 'файл не изменился'
assert src.count('ws-whead') >= 12, 'ws-whead: правило/разметка на месте'
assert src.count('ws-row-alt') >= 8, 'ws-row-alt: зебра на месте'
assert src.count('ws-wbtn') >= 6, 'ws-wbtn: кнопки на месте'
assert src.count("if (withEdit && !asBlocks) {") == 5, 'легаси-гейты строк ×5'
io.open(PATH, 'w', encoding='utf-8').write(src)
print('index.html: Task 396 применён (%d правок)' % 15)
