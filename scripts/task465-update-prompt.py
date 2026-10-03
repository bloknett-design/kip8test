#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 465: обновление системного промта kip8test (post-Task 465
# ПЕРЕНОС — зеркальная фиксация переноса в kip8).
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-02 (post-Task 463-464 ПЕРЕНОС'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-03 (post-Task 465 ПЕРЕНОС: Task 465 перенесён из kip8test@fe34a7b1 в боевой kip8 ОДНИМ инкрементом SW kipia-v500→v501 — КЛИЕНТ-ONLY, серверных шагов НЕТ (Apps Script не менялся); заявка: «В разделе Табель учёта рабочего времени, в окнах мероприятий и норм, значки "развернуть окно" сместить на расстояние от краёв окон на 3px сверху и справа. В окне мероприятий, справа от значка раскрытия окна сделай новый значок с иконкой принтера, форма кнопки квадратная и размером как кнопка раскрытия окна, при нажатии на эту кнопку должно появляться диалоговое окно печати и сохранения в форматах файлов, так же как в окне кнопки печати графика, с предпросмотром списка мероприятий, для дальнейшей печати или сохранения в файл списка мероприятий на текущий месяц.»): КЛИЕНТ (index.html): значки .ws-bar-exp — top/right 5px→2px (2px CSS + 1px рамка окна = 3px от ВНЕШНЕГО края, в ОБОИХ окнах бара табеля); ПРИЧИНА асимметрии найдена — правило Task 381 «склейка строк» .ws-events-panel > * + * { margin-top: 3px } задевало и absolute-значок окна мероприятий (висел на 3px НИЖЕ, чем в окне норм — 9px против 6px от края) — сброс .ws-events-panel > .ws-bar-exp, > .ws-bar-print { margin-top: 0 }; в окне мероприятий раскрытие сдвинуто ВЛЕВО (#wsEventsPanel .ws-bar-exp { right: 27px }), у угла ПАРА [раскрытие][печать]: НОВЫЙ .ws-bar-print (квадрат 22×22, стиль пары, Material-иконка принтера как у wsPrintBtn), создаёт _barExpSync только для el.id === \'wsEventsPanel\', клик → WorkSchedule.printEventsList(); прикол translateY(scrollTop) — на ОБОИХ значках; плашка окна мероприятий padding-right 26→52px (нормы — 26px). ПЕЧАТЬ СПИСКА: printEventsList (guard _viewLevel===null; пустой месяц → тост «Нет мероприятий для печати — месяц пуст») → лист #wsPrintSheet.wsev-sheet + инжект #wsEventsPrintStyle (@page A4 portrait 12mm 10mm + _EVENTS_PRINT_CSS — приём талонов Task 447, один CSS для инжекта/iframe/печати) → диалог _openEventsPreview (id wsEventsPrevModal, wspprev-*: «Предпросмотр печати / Мероприятия — Месяц год г.», iframe standalone КНИЖНЫЙ лист 190мм (_buildEventsFileHtml), кнопки «Печать»/«Сохранить PDF»/«Сохранить Excel»/«Отмена» + «A4 · книжная», Esc/затемнение/✕/Отмена, фолбэк window.print); _closeEventsPreview снимает инжект; ДИАЛОГИ ПЕЧАТИ ВЗАИМОИСКЛЮЧАЮЩИЕ: график ↔ талоны ↔ список мероприятий. МОДЕЛЬ _eventsListModel (чистая): выборка окна «Мероприятия» — пересекающие ОТКРЫТЫЙ месяц (сорт: дата начала → таб. номер) + СИЗ истекающие в месяце («До износа» нет), БЕЗ фильтра выбранного дня (печать полного месяца), min — записи мастеров скрыты (Task 399), name — короткое (Task 416) + цвет кода, fio отдельно; _buildEventsPrintHtml: шапка + таблица №/Даты/Мероприятие/Работник (точки цвета, № 9мм/Даты 24мм/Работник 44мм, table-header-group, page-break-inside avoid) + секция СИЗ (пустая не пишется), пусто — заглушка. ГЕНЕРАТОРЫ: _eventsPdfLayout (595×842pt, поля 28, шапка 44 первая, заголовки таблиц 16 на каждой странице, перенос по словам ~4.6pt/симв — приём графика, сквозная нумерация evFirst/ppe.first, caption 24) + _eventsPdfPaintPage (canvas×2, JPEG 0.92) поверх _buildPdfDocument/_wsDataUrlBytes/_wsDownload → «Мероприятия_‹Месяц›_‹год›.pdf»; _buildEventsWorkbook (лист «Мероприятия», _eventsSheetXml БЕЗ pane, _eventsStylesXml 4 шрифта/8 стилей, поверх _wsXlsZip/_wsXlsBytes/_wsXlsColName/_wsXlsEsc) → «…​.xlsx». ПЕРЕНОС: scripts/task465-transfer.py в kip8 (де-изоляция ×15, «дифф диффов»: репо-дифф 59 == эталону kip8test@44c09ee6↔kip8@8653f0c, дифф задач 1147 идентичен; .gs не тронуты — синхронны); тесты kip8 5238/0 = паритет 5232 + 6 task344 (маппинг v689→v501 (507)/v690→v502 (123)/негатив партии v688→v500 (1)/v687→v499 (2)/исторические); test-task344 v500→v501; SMOKE task465-smoke-k8.py 9/9 (порт 8997, ключи без префикса). ПОДВОДНЫЕ КАМНИ: (а) ruleBlock(\'.ws-bar-print {\') ловит ПЕРВОЕ вхождение — правило сброса маржи «.ws-events-panel > .ws-bar-print {» стоит РАНЬШЕ основного — в тестах искать \'.ws-bar-print {\\n\' (с переносом); (б) assertEqual(actual, expected) — ПЕРВЫЙ аргумент actual (в assertEqual(0, evFirst) «expected 38, got 0» означает evFirst=38); (в) VM-хост одного метода: new Function(\'return ({\' + src + \'\\n});\') — С ФИГУРНЫМИ СКОБКАМИ и ЗАПЯТЫМИ при join нескольких методов; (г) standalone-запуск test-taskNNN.js НЕ исполняет тесты (runAll зовёт run-all) — прогонять через node -e require+h.runAll() или run-all; (д) окно WS_CLIENT в test-task340.js 500000→560000 — блок печати ~36КБ сдвинул _renderEmpPopup/_renderWorkerCard; (е) смена уровня доступа в браузер-чеке — кэш kip8_my_access в localStorage переживает refreshData (перезагрузка страницы с новым кэшем). Тесты 5232/0 (174 файла; НОВЫЙ test-task465.js ×43: CSS ×5/_barExpSync ×3/печать ×8/диалог ×5/генераторы ×4/VM модель ×5/VM HTML ×3/VM PDF ×4/VM книга ×5/SW ×3; адаптация 378/381/388 (2px/52px/tNow) + 340 (окно 560КБ); бамп v688→v689 ассерты (149)/v689→v690 guards (109)). Браузер task465-browser-check.py 38/38 (порт 8999: A геометрия 3px обоих окон + пара + плашки 52/26; B диалог (кнопки/лист/инжект/iframe 5+1+СИЗ); C закрытия; D скачивания PDF/Excel; E взаимоисключение; F пустой месяц тост; G мобайл 375; H min мастера скрыты; 0 JS). VLM ×3 (диалог/пара значков/мобайл; «обрезанная колонка» опровергнута замером scrollW==clientW). DEPLOY-Task465-timesheet-bar-icons-print-events-list.md (КЛИЕНТ-ONLY — серверных шагов НЕТ). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @fe34a7b1 SW `kipia-test-v689` (guard v690), тесты 5232/0; kip8 SW `kipia-v501` (guard v502), тесты 5238/0 (паритет + 6 task344) — Task 465 выкачан в ОБОИХ репо, открытых хвостов нет; десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 466 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-463-464-ПЕРЕНОС')
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

# (в) «Текущая версия кэша» v688 → v689
old_cache = '> **Текущая версия кэша:** `kipia-test-v688`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v689`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v688` → `kipia-test-v689` (для kip8test) или `kipia-v499` → `kipia-v500` (для kip8)'
new_inc = 'Формат: `kipia-test-v689` → `kipia-test-v690` (для kip8test) или `kipia-v500` → `kipia-v501` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов 5189/5195 → 5232/5238
old_exp = '# Ожидается: 5189 passed, 0 failed (kip8test; в kip8 — 5195 passed, 0 failed)'
new_exp = '# Ожидается: 5232 passed, 0 failed (kip8test; в kip8 — 5238 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# (е) контроль: строка 3 одна, счётчик «предыдущих» не вырос
# (в файле ДВЕ группы prev-строк: активная цепочка после строки 3
# и застывший исторический снимок ниже — логика task464: удаляется
# последняя строка снимка при общем счётчике > 2, паритет поведения)
assert src.count(NEW_LINE3) == 1
assert src.count(PREV_MARK) <= n_prev_before + 1

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('OK: промт kip8test обновлён до post-Task 465 ПЕРЕНОС')
print('  предыдущих строк: %d (было %d)' % (src.count(PREV_MARK), n_prev_before))
