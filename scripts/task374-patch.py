#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 374: убрать кнопку «Копировать» над расчётными таблицами в разделе
# «Датчики температуры» (заявка: «убери кнопку "Копировать" над расчётными
# таблицами»). Обе ветки calcTempSensor(): ТС и ТП. Заголовок
# «Таблица значений (шаг X°C)» остаётся (отступ сверху 12px переносится
# на сам заголовок), flex-обёртка и кнопка удаляются.
# Функция copyCalcTable() НЕ трогается — её использует раздел
# весоизмерительных датчиков (wsTableContainer, 3 вызова) и она остаётся
# в файле. Кнопки «Шкала-сигнал» (copyScaleTable) и «Буй» (copyBuoyTable)
# НЕ тронуты — заявка относится к таблицам раздела датчиков температуры.
# Запуск из корня репо kip8test.
import sys

PATH = 'index.html'
html = open(PATH, encoding='utf-8').read()

OLD = ('            html+=`<div style="display:flex; justify-content:space-between;'
       ' align-items:center; margin-top:12px; margin-bottom:0;">'
       '<div class="converter-result-label-title">Таблица значений (шаг ${formatNumber(step)}°C)</div>'
       '<button type="button" class="query-btn" onclick="copyCalcTable(\'tempTableContainer\')"'
       ' style="width:auto; padding:5px 10px; font-size:11px;">'
       '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>'
       '<path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>'
       'Копировать</button></div>`;\n')

NEW = ('            // Task 374: кнопка «Копировать» над таблицей убрана (заявка);\n'
       '            // отступ сверху 12px сохранён на самом заголовке\n'
       '            html+=`<div class="converter-result-label-title" style="margin-top:12px;">'
       'Таблица значений (шаг ${formatNumber(step)}°C)</div>`;\n')

cnt = html.count(OLD)
if cnt != 2:
    print('ОШИБКА: строка с кнопкой найдена %d раз (ожидается 2: ТС и ТП)' % cnt)
    sys.exit(1)
html = html.replace(OLD, NEW)
print('[1] кнопка «Копировать» убрана из заголовков таблиц: 2 места (ТС и ТП)')

# Контроль: в calcTempSensor не осталось вызова copyCalcTable
start = html.index('function calcTempSensor(')
end = html.index('\n    function ', start + 10)
fn = html[start:end]
assert "copyCalcTable('tempTableContainer')" not in fn, 'в calcTempSensor остался вызов copyCalcTable!'
assert '>Копировать</button>' not in fn, 'в calcTempSensor осталась кнопка Копировать!'
print('[2] calcTempSensor: вызовов copyCalcTable и кнопок «Копировать» нет')

# Контроль: функция copyCalcTable осталась в файле (нужна весоизмерительным)
assert html.count('function copyCalcTable(') == 1, 'copyCalcTable должна остаться (1 объявление)'
n_ws = html.count("copyCalcTable(\\'wsTableContainer")
print('[3] copyCalcTable на месте; вызовов wsTableContainer: %d (не тронуты)' % n_ws)
assert n_ws == 3, 'вызовы wsTableContainer (3) не должны меняться'

# Контроль: кнопки других разделов не тронуты
assert html.count('copyScaleTable()') >= 1, 'кнопка Шкала-сигнал на месте'
assert html.count('copyBuoyTable()') >= 1, 'кнопка Буй на месте'
print('[4] кнопки «Шкала-сигнал» и «Буй» не тронуты')

# Контроль: маркеры Task 374
assert html.count('Task 374') >= 2, 'маркеры Task 374'

open(PATH, 'w', encoding='utf-8').write(html)
print('OK: index.html обновлён')
