#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 472: обновление системного промта kip8test (post-Task 472
# ПЕРЕНОС — зеркальная фиксация переноса в kip8).
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-03 (post-Task 471 ПЕРЕНОС'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-03 (post-Task 472 ПЕРЕНОС: Task 472 перенесён из kip8test@65c55058 в боевой kip8 ОДНИМ инкрементом SW kipia-v507→v508 — КЛИЕНТ-ONLY, серверных шагов НЕТ); заявка: «При вводе текста работ на следующий месяц больше поля ввода, поле ввода должно динамически расширятся вниз под новые строчки текста. Кликабильные ячейки таблицы мероприятий должны незначительно выделяться зрительно второй рамкой внутри имитирующей выпуклость кнопки. Фон таблицы и окна должны быть не прозрачными, и окно в светлой теме не белым а бежевым цветом, как цвет фона бара, и с толстой рамкой с эффектом выступа.»): СУТЬ (контекст: динамичное окно Task 471 / таблица Task 460/470 / раскладка Task 468 / бежевый бар — --header-bg светлой темы rgba(240,238,230,0.92)): (1) ПОЛЕ ВВОДА РАБОТ «на следующий месяц» — <input type="text"> → <textarea id="peWorkInput" rows="1"> (maxlength 500, aria-label живы) + НОВЫЙ метод PlanWorksData._growInput (height:auto → scrollHeight+2px — компенсация горизонтальных границ при box-sizing:border-box; слушатель input + первичный вызов в _bindView после каждого рендера) — текст длиннее поля переносится на новые строки, поле ДИНАМИЧЕСКИ РАСШИРЯЕТСЯ ВНИЗ; очистка — сжимается к одной строке (CSS min-height 35px); Enter — по-прежнему «Добавить» (делегированный keydown жив, перенос строки НЕ вставляется); CSS: resize:none/overflow:hidden/display:block/line-height 1.4; .pe-works-form — align-items:flex-start (кнопка «Добавить» прижата к первой строке растущего поля); (2) БЕВЕЛ КЛИКАБЕЛЬНЫХ ЯЧЕЕК — группа правил .pe-table td.pe-m / .pe-head-months th / .pe-table th.pe-th-name / .pe-table td.pe-name.pe-name-click: box-shadow inset 1px 1px 0 rgba(255,255,255,0.11) + inset -1px -1px 0 rgba(0,0,0,0.45) (тёмная), светлая — rgba(255,255,255,0.8) + rgba(83,96,117,0.42) (цвет границ таблиц светлой темы) — вторая внутренняя рамка, имитирующая выпуклость кнопки; у выбранного месяца шапки (pe-mo-sel) бевел СЛИТ с полосой снизу (3 inset-тени); строки-группы и некликабельные ячейки — БЕЗ бевела; (3) НЕПРОЗРАЧНЫЕ ФОНЫ — .pe-card/.pe-desc-card: var(--card-bg) → #17212e (сплошной аналог rgba(30,42,56,0.55) над #0e1621, паттерн Task 254); светлая тема: карточка #faf9f6 (аналог rgba(255,255,255,0.65) над #F0EEE6), окно — БЕЖЕВОЕ #f0eee6 (= --header-bg светлой темы rgb(240,238,230), «как цвет фона бара») с ТОЛСТОЙ 3px двухтонной рамкой-выступом (#fffdf7 сверху/слева, #c8c2af снизу/справа) + мягкая тень 2px 3px 6px rgba(20,20,19,0.12). СЕРВЕР: НЕ ТРОНУТ (PlanEvents.gs/PlanWorksInit.gs/Code.gs синхронны — party client-only). ПЕРЕНОС: scripts/task472-transfer.py (де-изоляция ×15, «дифф диффов»: репо-дифф 59 == эталону kip8test@c916884e↔kip8@7f9e20d, дифф задач идентичен); тесты kip8 5399/0 = паритет 5393 + 6 task344 (маппинг v696→v508 (531)/v697→v509 (123)/негатив партии 472 v695→v507 (2: test-task472 — ассерт + строка сообщения, паттерн 471)/негативы 471 v694→v506 (2)/v693→v505 (1)/v692→v504 (1)/v691→v503 (1)/v690→v502 (1)/v689→v501 (2)/исторические; IMAGE_CACHE_VERSION kipia-images-v3; test-task344 v507→v508; run-all +472; дистанция комментария Task 461 в sw.js kip8 = 3325 < 3600 — окно test-task461, запас 275). ПОДВОДНЫЕ КАМНИ: (а) комментарий Task 472 в sw.js kip8test НЕ ДОЛЖЕН вытеснять Task 471 из окна 900 симв. test-task471 — первый вариант комментария (430 симв.) давал дистанцию 909 > 900, сжат до ~260 симв. (дистанция 871); (б) SMOKE kip8: ПЕРЕКЛЮЧЕНИЕ ТЕМЫ — только toggleTheme() БЕЗ reload: init-script playwright при КАЖДОЙ загрузке перезаписывает app-theme на light (в kip8 нет обёртки-префикса kip8test:, в отличие от kip8test, где init-script пишет сырой ключ, а приложение читает префиксированный); (в) SMOKE-замер автороста: перед базовым замером ОЧИЩАТЬ поле (вид next мог остаться открытым с текстом прошлой секции — база 54px вместо 35px ломала порог 1.8×); (г) VLM не видит 1px-бевел и 2-строчный рост на 375px в ПОЛНОМ кадре — подтверждать кропами с zoom x3. БАМП: task472-bump-tests.py (guards v696→v697 (123)/ассерты v695→v696 (527), 156 файлов) — test-task472.js писался ПОСЛЕ бампа с финальной v696. Тесты kip8test 5393/0 (НОВЫЙ test-task472.js ×21: авторост ×6 — в т.ч. VM _growInput (33→35px/120→122px/сжатие)/бевел ×5/фоны ×6/SW ×4). Браузер task472-browser-check.py 37/37 (порт 8999: светлая — окно rgb(240,238,230)=бар/карточка rgb(250,249,246)/рамка 3px #fffdf7-#c8c2af/тень/бевел td.pe-m+th+«Мероприятия»+pe-name-click, группа БЕЗ/textarea rows=1 → рост ≥1.8x → ещё длиннее → очистка → 35px/Enter → planWorks.add/тёмная #17212e оба/авторост в тёмной/375 — Task 464 жив 10 ячеек + окно бежевое + авторост; 0 JS). VLM ×7 (6 скриншотов + 2 кропа x3 — дефектов нет). SMOKE task472-smoke-k8.py 23/23 (порт 8997, ключи без префикса). DEPLOY-Task472-plan-events-input-bevel-beige.md (КЛИЕНТ-ONLY — серверных шагов НЕТ; откат — вернуть index.html+sw.js и поднять версию). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @65c55058 SW `kipia-test-v696` (guard v697), тесты 5393/0; kip8 @e2e7be6 SW `kipia-v508` (guard v509), тесты 5399/0 (паритет + 6 task344) — Task 472 выкачан в ОБОИХ репо, открытых хвостов нет; десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 473 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-471-ПЕРЕНОС')
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

# (в) «Текущая версия кэша» v695 → v696
old_cache = '> **Текущая версия кэша:** `kipia-test-v695`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v696`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v695` → `kipia-test-v696` (для kip8test) или `kipia-v506` → `kipia-v507` (для kip8)'
new_inc = 'Формат: `kipia-test-v696` → `kipia-test-v697` (для kip8test) или `kipia-v507` → `kipia-v508` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов 5372/5378 → 5393/5399
old_exp = '# Ожидается: 5372 passed, 0 failed (kip8test; в kip8 — 5378 passed, 0 failed)'
new_exp = '# Ожидается: 5393 passed, 0 failed (kip8test; в kip8 — 5399 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# (е) контроль
assert src.count(NEW_LINE3) == 1
assert src.count(PREV_MARK) <= n_prev_before + 1

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('OK: промт kip8test обновлён до post-Task 472')
print('  предыдущих строк: %d (было %d)' % (src.count(PREV_MARK), n_prev_before))
