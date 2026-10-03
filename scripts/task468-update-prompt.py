#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 468: обновление системного промта kip8test (post-Task 468
# ПЕРЕНОС — зеркальная фиксация переноса в kip8).
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-03 (post-Task 467 ПЕРЕНОС'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-03 (post-Task 468 ПЕРЕНОС: Task 468 перенесён из kip8test@68e8fdbc в боевой kip8 ОДНИМ инкрементом SW kipia-v503→v504 — КЛИЕНТ-ONLY, серверных шагов НЕТ (Apps Script не менялся); заявка: «Ширину столбца "Мероприятия" сделай по самому длинному тексту, всю таблицу — влево экрана, а справа от таблицы на всё оставшееся место размести окно с Описанием раздела и его функционала.»): СУТЬ: (1) .pe-table min-width: 100% УДАЛЁН — ширина строго width: max-content (столбец «Мероприятия» по самому длинному наименованию; прежде auto-колонка растягивалась на свободную ширину карточки); (2) НОВЫЙ контейнер .pe-layout (flex-строка, внешний отступ 0 12px перенесён сюда с .pe-card) → карточка таблицы слева (.pe-layout .pe-card { flex: 0 0 auto } — не сжимается, nowrap жив) + НОВОЕ окно описания справа (aside.pe-desc-card { flex: 1 1 280px; border/radius/padding; overflow-y: auto } — забирает всю остаточную ширину): заголовок «Описание раздела» + вводный абзац + «Функционал» (5 пунктов: отметка выполнения, хранение в архиве «Мероприятия_КИП_ИОС», правка отметки, обновление, мобильная версия — фактический функционал Task 460/463/464); (3) @media < 1200px раскладка складывается в колонку — описание ПОД таблицей; мобильный вид Task 464 (≤1023px: полоса месяца, один столбец, width: 100%, перенос наименований) НЕ ТРОНУТ; светлая тема pe-desc-lead/pe-desc-sub. JS отметок (PlanEventsData, диалоги, кнопка «Обновить») НЕ ТРОНУТ. ПЕРЕНОС: scripts/task468-transfer.py в kip8 (де-изоляция ×15, «дифф диффов»: репо-дифф 59 == эталону kip8test@fce2a778↔kip8@83aa340, дифф задач 121 идентичен; .gs не тронуты — синхронны, Code.gs kip8-версия жива); тесты kip8 5285/0 = паритет 5279 + 6 task344 (маппинг v692→v504 (516)/v693→v505 (123)/негатив партии v691→v503 (1: test-task468)/негатив 467 v690→v502 (1)/негативы 466 v689→v501 (2)/v687→v499 (2)/исторические; test-task344 v503→v504; run-all +468); SMOKE task468-smoke-k8.py 14/14 (порт 8997, ключи без префикса: карточка обнимает таблицу cardW-tabW<=3, окно до правого края ±2, 1100px колонка, 375px Task 464 жив: полоса месяца/один столбец/описание под таблицей, 0 JS). ПОДВОДНЫЕ КАМНИ: (а) перенос-скрипт ОДНОРАЗОВЫЙ — повторный прогон вставляет ДУБЛИКАТ require в run-all.js (норма: git checkout -- . и один чистый прогон); (б) комментарий Task 468 (5 строк) в шапке sw.js отодвинул комментарий Task 461 за границу окна 2000 в test-task461.js (расстояние ~2100) — окно расширено до 2500 (паттерн Task 463: 700→2000), фикс пришёл в kip8 с тестами автоматически; (в) test-task468.js: HTML-часть для изоляции pe-desc-card ищется от </head> (простой indexOf(\'<body\') ЛОВИТ подстроку в JS-шаблонах standalone-документов печати — slice слишком рано); ассерты @media 1023px привязаны к правилу .pe-month-bar, а не первому @media в файле (ранние @media других разделов); ruleBlock .pe-table прогоняется через stripComments (комментарий истории упоминает «min-width: 100%»). БАМП: task468-bump-tests.py (guards v692→v693 (123)/ассерты v691→v692 (510), 154 файла) — test-task468.js писался ПОСЛЕ бампа с финальной v692. Тесты kip8test 5279/0 (176 файлов; НОВЫЙ test-task468.js ×21: CSS ×5 (pe-layout flex+gap/отступ перенесён на layout+margin: 0/маркер 468/pe-card flex 0 0 auto/min-width удалён+Task 464 жив (pe-col-name auto, 46px, nowrap)), окно ×4 (pe-desc-card flex 1 1 280px+рамка/типографика 4 правил+grid/светлая тема/@media 1199 колонка), HTML ×4 (структура layout>card+aside/aria-label/содержание заголовок+лид+«Функционал»+5 пунктов/факты 463-464-460), изоляция ×3 (@media 1023px через якорь pe-month-bar/JS PlanEventsData жив/pe-desc-card ровно 1), SW ×3 (v692/v691 нет/комментарий pe-desc-card)). Браузер task468-browser-check.py 31/31 (порт 8999: A 1600 — flex row/карточка слева ±2/desc справа/карточка обнимает таблицу (907=905+2, БЫЛО бы 1576)/desc ≥ 275 до правого края/nowrap maxNameH ≤ 40/без скролла/нет переполнения; B содержание — заголовок/«Функционал»/5 пунктов/ключевые фразы ×5; C 1100 — column, desc под таблицей, desc на всю ширину; D 375 — полоса месяца/12 опций/таблица 100%/перенос normal/8 видимых ячеек месяца/desc под таблицей/нет переполнения; E светлая тема скриншот; 0 JS). VLM ×2 (десктоп: таблица слева по тексту без пустот, окно справа, без дефектов; узкий+мобайл: описание под таблицей, селектор месяца, без наложений). Артефакты download/kip8test-task468/ (×4 png) + download/kip8-task468/ (smoke ×1 png). DEPLOY-Task468-plan-events-layout-desc-window.md (КЛИЕНТ-ONLY — серверных шагов НЕТ; скопирован в kip8). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @68e8fdbc SW `kipia-test-v692` (guard v693), тесты 5279/0; kip8 @f6c0cf5 SW `kipia-v504` (guard v505), тесты 5285/0 (паритет + 6 task344) — Task 468 выкачан в ОБОИХ репо, открытых хвостов нет; десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 469 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-467-ПЕРЕНОС')
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

# (в) «Текущая версия кэша» v691 → v692
old_cache = '> **Текущая версия кэша:** `kipia-test-v691`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v692`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v691` → `kipia-test-v692` (для kip8test) или `kipia-v502` → `kipia-v503` (для kip8)'
new_inc = 'Формат: `kipia-test-v692` → `kipia-test-v693` (для kip8test) или `kipia-v503` → `kipia-v504` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов 5258/5264 → 5279/5285
old_exp = '# Ожидается: 5258 passed, 0 failed (kip8test; в kip8 — 5264 passed, 0 failed)'
new_exp = '# Ожидается: 5279 passed, 0 failed (kip8test; в kip8 — 5285 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# (е) контроль
assert src.count(NEW_LINE3) == 1
assert src.count(PREV_MARK) <= n_prev_before + 1

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('OK: промт kip8test обновлён до post-Task 468 ПЕРЕНОС')
print('  предыдущих строк: %d (было %d)' % (src.count(PREV_MARK), n_prev_before))
