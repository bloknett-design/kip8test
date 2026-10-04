#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 473: обновление системного промта (post-473) — график ППР
# «Приборы»: корневой фикс зрительной невидимости столбцов
# (align-items:flex-end → stretch) + значения над каждым столбцом +
# вспомогательная правая ось для К/П; SW v696→v697; тесты 5436/0.
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-03 (post-Task 472 ПЕРЕНОС: Task 472 перенесён'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-04 (post-Task 473; заявка: «В разделе Графики КИП ИОС, на вкладке Приборы, сделай что бы на графике "Количество приборов по графику ППР по месяцам на 2026 год" отображалось количество приборов на каждый месяц на диаграмме, и проверь сама диаграмма не отображает зрительно количество приборов по месяцам "К Калибровка П Поверка ТО Тех. обслуж."»): график ППР «Приборы» — ТОЛЬКО отрисовка, charts-desktop.js (модуль графиков Task 147, грузится только в десктопе Electron по User-Agent; данные _PPR_DEVICES не менялись). КОРЕНЬ «не отображает зрительно»: .ppr-bars-row имел align-items:flex-end → ячейки .ppr-bar-cell сжимались по контенту, height:% столбца разрешался против auto-высоты ячейки и схлопывался в min-height:2px — ВСЕ столбцы ВСЕХ серий были зрительно невидимы (2px из 165px, подтверждено замером Chromium на коде ДО правки) → align-items:stretch (низ столбца прижат flex-end самой ячейки .ppr-bar-cell). ПЛЮС: (а) значение над КАЖДЫМ столбцом — порог heightPct>8 УБРАН (числа видны были только у 14 из 36 месяцев: 12 ТО + 2 К; у П — ни одного), нулевые месяцы — подпись «0» у основания (.ppr-bar-val-zero, якорь .ppr-bar-cell position:relative); (б) ВСПОМОГАТЕЛЬНАЯ ПРАВАЯ ОСЬ: серии с максимумом <= 25% от общего (SECONDARY_SHARE=0.25; К 48 и П 15 при ТО 500) масштабируются по правой оси (niceMax(48)=50, метки 50…0, .ppr-y-axis-right) — столбцы малых серий зрительно различимы по месяцам; data-scale primary/secondary; легенда малых серий «(правая ось)» (.ppr-legend-axis) и тултипы; (в) CSS: .ppr-chart-body padding-top 4→16px (запас под подписи над 100%-столбцами). РЕГРЕСС «Блокировки» (Кр 98 при ТО 210 — обе крупные): правой оси НЕТ, единая шкала 0–500, 24 подписи. SW kipia-test-v696→v697 + сжатый комментарий Task 473 (2 строки; якорь «ВСЕГДА на одном уровне»). Тесты 5436/0 (+43 к 5393): НОВЫЙ test-task473.js ×43 (_niceMax ×5 / рендер HTML ×19 / «Блокировки» ×4 / CSS ×8 / шапка+SW ×7; данные ППР извлекаются из файла регексом; методы оживляются eval); АДАПТАЦИЯ test-task471+test-task472 — окно шапки версий sw.js 900→1020 (комментарий Task 473 отодвинул Task 471 до ~986 симв.; прецедент — окно test-task461 700→…→3600); бамп ассертов v696→v697 (533 в 157 файлах) + guards v697→v698 (123 в 109) — task473-bump-sw.py, OWN исключён. Браузер task473-browser-check.py 32/32 (порт 8998, Electron UA + мок Apps Script: тёмная/светлая/«Блокировки»; высоты К-48=96%, П-15=30%, К-13=26%, ТО-500=100% ряда; 0 JS ×3). VLM ×4 (включая ЗУМ-КРОП ×2.5: все 36 значений прочитаны и совпали с данными серий). DEPLOY НЕ ТРЕБУЕТСЯ (статический ассет — SW-бамп; десктопы — CI-автосинк). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v697` (guard v698), тесты 5436/0; kip8 SW `kipia-v508` (guard v509), тесты 5399/0 — Task 473 ОЖИДАЕТ ПЕРЕНОСА В kip8 одним инкрементом kipia-v508→v509 (регламент Task 441; команды «перенеси» в заявке НЕ БЫЛО — ждём подтверждения пользователя на тестовом стенде); десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 474 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-472')
    sys.exit(1)

n_prev_before = src.count(PREV_MARK)

i3 = src.index(CUR_MARK)
i3end = src.index('\n', i3)
old_line3 = src[i3:i3end]

# (а) удалить самую старую строку «предыдущая» (храним 2 последних)
if src.count(PREV_MARK) > 2:
    iprev = src.rindex(PREV_MARK)
    iprev_end = src.index('\n', iprev)
    src = src[:iprev] + src[iprev_end + 1:]

# (б) строка 3 → новая версия + «предыдущая» из старой строки 3
new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
src = src[:i3] + NEW_LINE3 + '\n' + new_prev + src[i3end:]

# (в) «Текущая версия кэша» v696 → v697
old_cache = '> **Текущая версия кэша:** `kipia-test-v696`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v697`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v696` → `kipia-test-v697` (для kip8test) или `kipia-v507` → `kipia-v508` (для kip8)'
new_inc = 'Формат: `kipia-test-v697` → `kipia-test-v698` (для kip8test) или `kipia-v508` → `kipia-v509` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5393 → 5436
old_exp = '# Ожидается: 5393 passed, 0 failed (kip8test; в kip8 — 5399 passed, 0 failed)'
new_exp = '# Ожидается: 5436 passed, 0 failed (kip8test; в kip8 — 5399 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# проверки
checks = [
    ('post-Task 473', 1),
    ('Версия документа (предыдущая):** 2026-10-03 (post-Task 472 ПЕРЕНОС: Task 472 перенесён', 1),
    ('5436 passed, 0 failed (kip8test', 1),
    ('kipia-test-v697', None),
    ('СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 474', 1),
    ('align-items:stretch', None),
]
for marker, cnt in checks:
    c = src.count(marker)
    if cnt is not None and c != cnt:
        print('ОШИБКА: маркер %r найден %d раз (ожидалось %s)' % (marker[:60], c, cnt))
        sys.exit(1)
    if cnt is None and c == 0:
        print('ОШИБКА: маркер не найден: %r' % marker[:60])
        sys.exit(1)
if src.count(PREV_MARK) != n_prev_before:
    print('ОШИБКА: длина цепочки «предыдущих» изменилась (%d → %d)' %
          (n_prev_before, src.count(PREV_MARK)))
    sys.exit(1)

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('промт: post-473 записан (кэш v697, тесты 5436/0, следующий 474)')
