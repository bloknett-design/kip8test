#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 466: обновление системного промта kip8test (post-Task 466
# ПЕРЕНОС — зеркальная фиксация переноса в kip8).
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-03 (post-Task 465 ПЕРЕНОС'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-03 (post-Task 466 ПЕРЕНОС: Task 466 перенесён из kip8test@986db19b в боевой kip8 ОДНИМ инкрементом SW kipia-v501→v502 — КЛИЕНТ-ONLY, серверных шагов НЕТ (Apps Script не менялся); заявка: «В окне мероприятий поменяй местами значки раскрытия окна и печати мероприятий.»): КЛИЕНТ (index.html): CSS-only свап — правило #wsEventsPanel .ws-bar-exp { right: 27px } (Task 465) УДАЛЕНО (раскрытие возвращается в самый угол на базовые 2px CSS + 1px рамка окна = 3px от ВНЕШНЕГО края, как в окне норм), вместо него #wsEventsPanel .ws-bar-print { right: 27px } — печать теперь СЛЕВА (пара [печать][раскрытие], зазор 3px, 22+3+22+2px от правой грани); JS-логика НЕ ТРОНУТА (оба значка absolute внутри скроллера с общим приколом translateY(scrollTop) — порядок задаётся только CSS): размеры 22×22, _barExpSync создаёт печать только для wsEventsPanel, клик → printEventsList, диалог «Печать/Сохранить PDF/Сохранить Excel/Отмена» с предпросмотром книжного A4, сброс margin-top, плашки 52/26px, окно норм — всё живо; обновлены комментарии CSS ×3 + JS ×2 (маркеры Task 466, «печать СЛЕВА от раскрытия»); sw.js: kipia-test-v689→v690 + комментарий Task 466 (строка Task 465 «справа от раскрытия» → «слева»). ПЕРЕНОС: scripts/task466-transfer.py в kip8 (де-изоляция ×15, «дифф диффов»: репо-дифф 59 == эталону kip8test@b7504f2f↔kip8@097d9ac, дифф задач 33 идентичен; .gs не тронуты — синхронны, Code.gs kip8-версия жива); тесты kip8 5250/0 = паритет 5244 + 6 task344 (маппинг v690→v502 (510)/v691→v503 (123)/негативы партии v689→v501 (2: test-task465 + test-task466)/v687→v499 (2)/исторические; test-task344 v501→v502; run-all +466); SMOKE task466-smoke-k8.py 8/8 (порт 8997, ключи без префикса). ПОДВОДНЫЕ КАМНИ: (а) перенос-скрипт ОДНОРАЗОВЫЙ — повторный прогон на применённом состоянии падает на якорях v501/«справа» (норма: git checkout -- . и один прогон); первый прогон упал на сверхстрогом ассерте «слева от раскрытия == 2» (в kip8 фраза 1 — комментарий Task 466 говорит «печать слева (27px)» без литеральной фразы) — ассерт исправлен на == 1 + негатив «справа нет», состояние откачено, прогон начисто exit 0 (98 OK); (б) бамп-скрипт task466-bump-tests.py (guards v690→v691 (123)/ассерты v689→v690 (507), 150 файлов) — test-task466.js писать ПОСЛЕ бампа с финальной версией v690, иначе v690-ассерты «уедут» в v691. Тесты kip8test 5244/0 (174 файла; НОВЫЙ test-task466.js ×12: CSS свап ×6 (печать 27px/старое правило раскрытия УБРАНО + база 2px/ровно одно #wsEventsPanel-переопределение/база печати 2px+22×22/margin-reset жив/52px+26px), JS не тронут ×3 (_barExpSync по id + printEventsList/прикол обоих/маркеры Task 466), SW ×3 (v690/v689 нет/комментарий); адаптация test-task465.js — позиционный тест «печать 27px, раскрытие в углу» + шапка «слева (Task 466)» + выправлены устаревшие тексты SW-сообщений). Браузер task466-browser-check.py 16/16 (порт 8999: A геометрия свапа — раскрытие 3/3 в углу, печать 3/28 слева, expBefore, 22×22, зазор 3, окно норм 3/3 один значок, плашки 52/26; B клик по печати (ЛЕВЫЙ) — диалог wsEventsPrevModal (заголовок, 4 кнопки, wsev-sheet, инжект); C раскрытие (в углу) — ws-bar-open; D Esc + инжект снят; 0 JS). VLM ×1 (a-swapped-icons.png: «левее — значок принтера», «у самого правого края — шеврон»). Артефакты download/kip8test-task466/ (×3 png). DEPLOY-Task466-timesheet-bar-icons-swapped.md (КЛИЕНТ-ONLY — серверных шагов НЕТ; скопирован в kip8). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @986db19b SW `kipia-test-v690` (guard v691), тесты 5244/0; kip8 @867d4df SW `kipia-v502` (guard v503), тесты 5250/0 (паритет + 6 task344) — Task 466 выкачан в ОБОИХ репо, открытых хвостов нет; десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 467 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-465-ПЕРЕНОС')
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

# (в) «Текущая версия кэша» v689 → v690
old_cache = '> **Текущая версия кэша:** `kipia-test-v689`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v690`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v689` → `kipia-test-v690` (для kip8test) или `kipia-v500` → `kipia-v501` (для kip8)'
new_inc = 'Формат: `kipia-test-v690` → `kipia-test-v691` (для kip8test) или `kipia-v501` → `kipia-v502` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов 5232/5238 → 5244/5250
old_exp = '# Ожидается: 5232 passed, 0 failed (kip8test; в kip8 — 5238 passed, 0 failed)'
new_exp = '# Ожидается: 5244 passed, 0 failed (kip8test; в kip8 — 5250 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# (е) контроль
assert src.count(NEW_LINE3) == 1
assert src.count(PREV_MARK) <= n_prev_before + 1

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('OK: промт kip8test обновлён до post-Task 466 ПЕРЕНОС')
print('  предыдущих строк: %d (было %d)' % (src.count(PREV_MARK), n_prev_before))
