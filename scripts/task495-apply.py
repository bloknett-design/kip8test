#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 495 — kip8test: применить правки заявки.

Заявка: «В блоке ввода данных для расчёта таблицы убери поле с типом
датчика, и убери тексты "Тип датчика" и "Шаг расчёта таблицы в
градусах Цельсия", и оформи этот блок так же как блок произвольного
расчёта, только не с эффектом выступа, а наоборот. Сразу вноси
изменения и в kip8.»

ЧТО ДЕЛАЕТ (page-temp-sensor-view, колонка ввода):
  1. HTML: удалены <div class="scale-form-label">Тип датчика</div> и
     чип <div id="tempSensorViewChip" class="ts-view-chip">; удалена
     подсказка «Шаг расчёта таблицы в градусах Цельсия» под полем шага.
  2. HTML: обёртка .scale-form заменена панелью
     <div class="ts-calc-panel ts-calc-inset" id="tempTableFormPanel">
     — как панель произвольного расчёта (Task 494), поля min/max/шаг
     получили класс ts-calc-field (52px/19px/700/белый); кнопка
     «Рассчитать» осталась вне панели.
  3. CSS: новые правила .ts-calc-panel.ts-calc-inset (тёмная + светлая
     тема) — ПРОТИВОПОЛОЖНЫЙ эффект: УГЛУБЛЕНИЕ (рамка 1px
     приглушённая, тёмный фон «колодца» без синего градиента, тени
     ТОЛЬКО внутренние — сверху тёмная, снизу светлая кромка, внешней
     тени НЕТ); мёртвые правила .ts-view-chip/-name/-meta сняты.
  4. JS: openTempSensor больше не заполняет чип (тип датчика виден в
     заголовке страницы).
  5. sw.js: kipia-test-v718 → kipia-test-v719 + комментарий Task 495.
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'
OK = True


def rep(path, pairs):
    global OK
    src = io.open(path, encoding='utf-8').read()
    for old, new, cnt in pairs:
        n = src.count(old)
        if n != cnt:
            print('FAIL %s: фрагмент (ожид. %d, найдено %d):\n%s' %
                  (path, cnt, n, old[:120]))
            OK = False
            continue
        src = src.replace(old, new)
        print('OK   %s: замена x%d (%d симв. → %d симв.)' %
              (path.split('/')[-1], n, len(old), len(new)))
    io.open(path, 'w', encoding='utf-8').write(src)


IDX = ROOT + '/index.html'

# --- 1+2. HTML: блок ввода данных расчёта таблицы -------------------
OLD_HTML = (
    '                    <div class="scale-form">\n'
    '                <div class="scale-form-label">Тип датчика</div>\n'
    '                <div id="tempSensorViewChip" class="ts-view-chip"></div>\n'
    '                <div class="scale-form-label" style="margin-top:12px;">'
    'Диапазон измерения (°C)</div>\n'
    '                <div style="display: flex; gap: 8px; margin-bottom: 12px;'
    ' align-items: stretch;"><input type="text" inputmode="numeric"'
    ' id="temp_sensor_min" class="scale-field" style="flex: 1;'
    ' margin-bottom: 0;" value="0" placeholder="min °C" autocomplete="off"'
    ' enterkeyhint="next"><input type="text" inputmode="numeric"'
    ' id="temp_sensor_max" class="scale-field" style="flex: 1;'
    ' margin-bottom: 0;" value="100" placeholder="max °C" autocomplete="off"'
    ' enterkeyhint="next"></div>\n'
    '                <div class="scale-form-label">Шаг таблицы (°C)</div>\n'
    '                <input type="text" inputmode="numeric"'
    ' id="temp_sensor_step" class="scale-field" value="10" placeholder="10"'
    ' autocomplete="off" enterkeyhint="done"><div'
    ' style="color:rgba(255,255,255,0.25); font-size:10px; margin-top:-6px;'
    ' margin-bottom:8px; padding-left:4px;">Шаг расчёта таблицы в градусах'
    ' Цельсия</div>\n'
    '                            </div>\n'
)

NEW_HTML = (
    '                    <!-- Task 495: блок ввода данных для расчёта таблицы —\n'
    '                         поле «Тип датчика» (чип tempSensorViewChip) и'
    ' тексты\n'
    '                         «Тип датчика» / «Шаг расчёта таблицы в градусах\n'
    '                         Цельсия» УДАЛЕНЫ по заявке; блок оформлен как'
    ' панель\n'
    '                         произвольного расчёта (Task 494: контейнер\n'
    '                         ts-calc-panel, поля ts-calc-field), но с'
    ' эффектом\n'
    '                         УГЛУБЛЕНИЯ, а не выступа — модификатор\n'
    '                         ts-calc-inset: приглушённая рамка 1px, тёмный\n'
    '                         «колодец» без синего градиента, тени только\n'
    '                         внутренние. Обёртка .scale-form снята; кнопка\n'
    '                         «Рассчитать» осталась вне панели. -->\n'
    '                    <div class="ts-calc-panel ts-calc-inset"'
    ' id="tempTableFormPanel">\n'
    '                <div class="scale-form-label">Диапазон измерения (°C)</div>\n'
    '                <div style="display: flex; gap: 8px; margin-bottom: 12px;'
    ' align-items: stretch;"><input type="text" inputmode="numeric"'
    ' id="temp_sensor_min" class="scale-field ts-calc-field" style="flex: 1;'
    ' margin-bottom: 0;" value="0" placeholder="min °C" autocomplete="off"'
    ' enterkeyhint="next"><input type="text" inputmode="numeric"'
    ' id="temp_sensor_max" class="scale-field ts-calc-field" style="flex: 1;'
    ' margin-bottom: 0;" value="100" placeholder="max °C" autocomplete="off"'
    ' enterkeyhint="next"></div>\n'
    '                <div class="scale-form-label">Шаг таблицы (°C)</div>\n'
    '                <input type="text" inputmode="numeric"'
    ' id="temp_sensor_step" class="scale-field ts-calc-field" value="10"'
    ' placeholder="10" autocomplete="off" enterkeyhint="done">\n'
    '                    </div>\n'
)

# --- 3a. CSS: правила углубления (после светлой focus-правила полей) --
ANCHOR_CSS = (
    '    [data-theme="light"] .ts-calc-field:focus { border-color:'
    ' rgba(43, 111, 163, 0.9); box-shadow: 0 0 0 3px rgba(74, 143, 199,'
    ' 0.15); background: rgba(255, 255, 255, 0.9); }\n'
)

NEW_CSS = ANCHOR_CSS + (
    '    /* Task 495: блок ввода данных расчёта ТАБЛИЦЫ (диапазон + шаг,\n'
    '       #tempTableFormPanel) — оформлен как панель произвольного\n'
    '       расчёта (тот же контейнер .ts-calc-panel и поля .ts-calc-field),\n'
    '       но с ПРОТИВОПОЛОЖНЫМ эффектом: УГЛУБЛЕНИЕ вместо выступа.\n'
    '       Рамка 1px приглушённая (у выступа — яркая 2px), фон — тёмный\n'
    '       «колодец» без синего градиента, тени ТОЛЬКО внутренние (сверху\n'
    '       тёмная — глубина, снизу светлая кромка), внешней тени НЕТ —\n'
    '       блок «втоплен» в страницу, тогда как панель произвольного\n'
    '       расчёта над ним выступает. */\n'
    '    .ts-calc-panel.ts-calc-inset { background-color: rgba(13, 17, 23,'
    ' 0.55); background-image: none; border: 1px solid rgba(74, 143, 199,'
    ' 0.32); box-shadow: inset 0 3px 10px rgba(0, 0, 0, 0.5), inset 0 -1px 0'
    ' rgba(255, 255, 255, 0.06); }\n'
    '    [data-theme="light"] .ts-calc-panel.ts-calc-inset {'
    ' background-color: rgba(21, 54, 83, 0.08); background-image: none;'
    ' border-color: rgba(43, 111, 163, 0.35); box-shadow: inset 0 2px 8px'
    ' rgba(21, 54, 83, 0.18), inset 0 -1px 0 rgba(255, 255, 255, 0.7); }\n'
)

# --- 3b. CSS: снять мёртвые правила чипа -----------------------------
OLD_CHIP_CSS = (
    '    /* Task 372: чип выбранного датчика на странице датчика */\n'
    '    .ts-view-chip { display: flex; align-items: center; flex-wrap:'
    ' wrap; gap: 8px; min-height: 44px; padding: 9px 12px; background:'
    ' var(--card-bg); border: 1px solid var(--card-border); border-radius:'
    ' 10px; }\n'
    '    .ts-view-chip-name { font-size: 15px; font-weight: 700; color:'
    ' var(--text-primary); }\n'
    '    .ts-view-chip-meta { font-size: 11px; color: var(--conv-info-text);'
    ' line-height: 1.35; }\n'
)

NEW_CHIP_CSS = (
    '    /* Task 372: чип выбранного датчика — Task 495: чип\n'
    '       tempSensorViewChip и текст «Тип датчика» удалены из блока\n'
    '       ввода (тип датчика показывает заголовок страницы); правила\n'
    '       .ts-view-chip/-name/-meta сняты как неиспользуемые. */\n'
)

# --- 4. JS: openTempSensor без чипа ----------------------------------
OLD_JS = (
    "        let chip=document.getElementById('tempSensorViewChip');\n"
    '        // Task 373: бейдж ТС/ТП убран из чипа — только имя и параметры\n'
    "        if(chip){chip.innerHTML='<span class=\"ts-view-chip-name\">'"
    "+sel.name+'</span><span class=\"ts-view-chip-meta\">'+sel.meta"
    "+'</span>';}\n"
)

NEW_JS = (
    '        // Task 495: чип «Тип датчика» (tempSensorViewChip) удалён из\n'
    '        // блока ввода — тип датчика виден в заголовке страницы\n'
)

rep(IDX, [
    (OLD_HTML, NEW_HTML, 1),
    (ANCHOR_CSS, NEW_CSS, 1),
    (OLD_CHIP_CSS, NEW_CHIP_CSS, 1),
    (OLD_JS, NEW_JS, 1),
])

# --- 5. sw.js: версия + комментарий -----------------------------------
SW = ROOT + '/sw.js'
OLD_SW = (
    "// Task 494: «Датчики температуры» — панель произвольного расчёта\n"
    "// (tempCustomCalcPanel) без заголовка/подсказки, эффект выступа\n"
    "// (рамка 2px + градиент + тень), поля крупнее и ярче. Клиент-only.\n"
    "const CACHE_VERSION = 'kipia-test-v718';"
)
NEW_SW = (
    "// Task 494: «Датчики температуры» — панель произвольного расчёта\n"
    "// (tempCustomCalcPanel) без заголовка/подсказки, эффект выступа\n"
    "// (рамка 2px + градиент + тень), поля крупнее и ярче. Клиент-only.\n"
    "// Task 495: «Датчики температуры» — блок ввода данных расчёта\n"
    "// таблицы: поле «Тип датчика» (чип) и тексты «Тип датчика» / «Шаг\n"
    "// расчёта таблицы в градусах Цельсия» удалены; блок оформлен как\n"
    "// панель произвольного расчёта, но с эффектом УГЛУБЛЕНИЯ\n"
    "// (ts-calc-inset). Клиент-only.\n"
    "const CACHE_VERSION = 'kipia-test-v719';"
)
rep(SW, [(OLD_SW, NEW_SW, 1)])

# --- Контроли ---------------------------------------------------------
idx = io.open(IDX, encoding='utf-8').read()
for gone in ['Тип датчика', 'Шаг расчёта таблицы в градусах Цельсия',
             'tempSensorViewChip', 'ts-view-chip']:
    if idx.count(gone):
        print('FAIL: в index.html осталось %r x%d' % (gone, idx.count(gone)))
        OK = False
    else:
        print('Контроль: %r отсутствует в index.html' % gone)
for must in ['ts-calc-inset', 'tempTableFormPanel',
             'class="ts-calc-panel ts-calc-inset"']:
    if not idx.count(must):
        print('FAIL: в index.html нет %r' % must)
        OK = False

print('RESULT: %s' % ('OK' if OK else 'FAIL'))
sys.exit(0 if OK else 1)
