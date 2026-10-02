#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 464: обновление системного промта (post-464).
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-02 (post-Task 463; заявка'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-02 (post-Task 464; заявка: «Сделал скрипты, создалась новый лист Архив создал, отметки мероприятий работают. Краткую инструкцию над таблицей "Нажмите на ячейку месяца, чтобы отметить выполнение мероприятия — отметка с датой сохраняется в архив файла Мероприятия_КИП_ИОС" убери. Ширину столбца с мероприятиями сделай по тексту в нём. В диалоговом окне подтверждения отметки, кнопку "Отмена" подкрась немного в красный, а кнопку "Отметить" переименуй в "Подтвердить". После выполнения отметки сделай возможность отредактировать дату и отменить выполнение отметки. В мобильной версии, для компактности, оставляй только столбец с мероприятиями и текущий месяц, с возможностью выбора месяца. И перенеси изменения в боевой kip8.»): ПОЛИРОВКА раздела «Плановые мероприятия» (Task 463 ПОДТВЕРЖДЁН пользователем: серверные шаги выполнены, лист «Архив» создан, отметки работают). КЛИЕНТ (index.html): подсказка .pe-hint/peHint УДАЛЕНА; ширина колонки мероприятий ПО ТЕКСТУ (.pe-col-name width:auto + .pe-name/.pe-th-name white-space:nowrap — по самому длинному наименованию); диалог подтверждения: кнопка «Подтвердить» (была «Отметить»), «Отмена» СЛЕГКА КРАСНАЯ (.pe-dialog .kip-dialog-cancel.pe-cancel-red, rgba(220,80,80,.14)/#d98484 + светлая тема); НОВОЕ — клик по ОТМЕЧЕННОЙ ячейке → _editDialog «Изменение отметки» (подпись «мероприятие — месяц год (выполнено дд.мм.гггг)», input date prefilled, кнопки [Отмена][Удалить отметку — .pe-unmark-btn КРАСНАЯ][Сохранить дату]) → _saveDate (planEvents.update: {token, year, month, event, date}, busy, _setCell + title + тост «Дата отметки обновлена») или _unmarkCell (planEvents.unmark: payload БЕЗ date, удаление из _marks/_byKey, _setCell(td, null) + тост «Отметка снята»); ошибки сети/сервера → тост «Не удалось сохранить дату/снять отметку…» (not_found → подсказка «Нажмите Обновить»), данные не трогаются; МОБАЙЛ (<= 1023px): полоса .pe-month-bar + select#peMonthSel (опции из MONTHS, по умолчанию ТЕКУЩИЙ месяц; на десктопе display:none) + _tagColumns (классы pe-mo-1..12 на th/td — разметку 96 ячеек НЕ трогаем) + _applyMonth (класс pe-mo-off всем, кроме выбранного); CSS media: .pe-table .pe-mo-off{display:none}, .pe-table{width:100%}, .pe-name/.pe-th-name{white-space:normal} (десктопный nowrap 352+46px НЕ ВЛЕЗАЛ в 375px) и ОБЯЗАТЕЛЬНО .pe-table col.pe-col-month{width:0} (col span=12 width:46px резервировал пустые слоты скрытых месяцев — «пустой столбец» у правого края, нашёл VLM). СЕРВЕР: PlanEvents.gs + planEvents.update (валидация как mark; правка колонок B дата_выполнения + G время_отметки у ВСЕХ строк ключа; записи нет → not_found) + planEvents.unmark (deleteRow всех строк ключа С КОНЦА — индексы не съезжают; идемпотентно: removed:false без ошибки) + SRV_VER \'464\' + 2 case в Code.gs (шапка \'PlanEvents (Task 463/464)\'). ПОДВОДНЫЕ КАМНИ: (а) первый @media (max-width: 1023px) в index.html ЧУЖОЙ (др. секция) — тесты ищут сами правила (.pe-mo-off) как якорь; (б) версии в ручных правках тестов 463/464 писать ДО бампа: скрипт task464-bump-tests.py сдвигает v688→v689 (guards) и v687→v688 (ассерты) — вписанный руками v688 «уезжает» в v689; (в) super().end_headers() в мок-сервере браузерных чеков (SimpleHTTPRequestHandler.end_headers() без self падает). Тесты 5189/0 (173 файла; НОВЫЙ test-task464.js ×41: SRC HTML ×4 / CSS ×6 / модуль ×9 / PlanEvents.gs ×9 / Code.gs ×2 / SW ×3 + run-all; адаптация test-task463.js (peHint «удалена», «Подтвердить»+pe-cancel-red, _cellClick→_editDialog, шапка Code.gs префикс-поиск, SW v688) + test-task460.js (width:auto+nowrap вместо 300px); бамп v688→v689 guards (129)/v687→v688 ассерты (500), 149 файлов). Браузер task464-browser-check.py 57/57 (порт 8996, STATEFUL-мок с update/unmark: A — подсказки нет/селектор скрыт/nowrap/диалог [Отмена pe-cancel-red][Подтвердить]/отмена/mark→галочка; B — правка даты (payload, title 20.03.2026, тост «Дата отметки обновлена»); C — снятие (unmark БЕЗ date, крестик, тост «Отметка снята», stateful повторное открытие); D — ошибки сервера (sheet_not_found + not_found, данные не тронуты, busy снят); E — already:true; F — мобайл 375 светлая: селектор = текущий месяц, шапка ТОЛЬКО одного месяца, 8 ячеек, выбор «Декабрь» переключает столбец, отметка в декабре, таблица ВЛЕЗАЕТ (scroll<=client) и месяц — крайний столбец (нет пустого); G — «Обновить»; 0 JS ×7). VLM ×4 (диалог: [Отмена красноватая][Подтвердить синяя], подсказки нет; «Изменение отметки»: 3 кнопки, «Удалить отметку» красная, дата prefilled; мобайл октябрь: селектор + 1 столбец, всё влезло; месяц — ПОСЛЕДНИЙ столбец, пустого справа НЕТ). DEPLOY-Task464-plan-events-polish-edit-unmark-mobile.md (ШАГИ СЕРВЕРА: обновить PlanEvents.gs ЦЕЛИКОМ + 2 case в Code.gs + New version развёртывания; лист «Архив»/PlanEventsInit.gs НЕ нужны — созданы Task 463; порядок любой — до обновления сервера правка/снятие дают тост об ошибке, ничего не ломается). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v688` (guard v689), тесты 5189/0; kip8 @11617e1, SW `kipia-v499` (guard v500), тесты 5113/0 — партия 463+464 ВЫЖИДАЕТ ПЕРЕНОСА В kip8 ОДНИМ инкрементом kipia-v499→v500 (команда дана в заявке 464; Apps Script уже развёрнут по 463 — для 464 обновить PlanEvents.gs + case); десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 465 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-463')
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

# (в) «Текущая версия кэша» v687 → v688
old_cache = '> **Текущая версия кэша:** `kipia-test-v687`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v688`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v687` → `kipia-test-v688` (для kip8test) или `kipia-v499` → `kipia-v500` (для kip8)'
new_inc = 'Формат: `kipia-test-v688` → `kipia-test-v689` (для kip8test) или `kipia-v499` → `kipia-v500` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5154 → 5189
old_exp = '# Ожидается: 5154 passed, 0 failed (kip8test; в kip8 — 5113 passed, 0 failed)'
new_exp = '# Ожидается: 5189 passed, 0 failed (kip8test; в kip8 — 5113 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)
old_exp2 = 'ожидается `5154 passed, 0 failed` (для kip8test; в kip8 — `5113 passed, 0 failed`)'
new_exp2 = 'ожидается `5189 passed, 0 failed` (для kip8test; в kip8 — `5113 passed, 0 failed`)'
if old_exp2 in src:
    src = src.replace(old_exp2, new_exp2, 1)

# (е) эндпоинт план-мероприятий: + update/unmark (Task 464)
old_ep = '| `planEvents.list` / `planEvents.mark` | «Плановые мероприятия»: отметки года / отметка выполнения (идемпотентно, Task 463; архив файла Мероприятия_КИП_ИОС, лист «Архив»). |'
new_ep = '| `planEvents.list` / `planEvents.mark` / `planEvents.update` / `planEvents.unmark` | «Плановые мероприятия»: отметки года / отметка выполнения (идемпотентно, Task 463) / правка даты / снятие отметки (Task 464; архив файла Мероприятия_КИП_ИОС, лист «Архив»). |'
if old_ep not in src:
    print('ОШИБКА: не найдена строка эндпоинта planEvents')
    sys.exit(1)
src = src.replace(old_ep, new_ep, 1)

# проверки
checks = [
    ('post-Task 464', 1),
    ('Версия документа (предыдущая):** 2026-10-02 (post-Task 463; заявка', 1),
    ('5189 passed, 0 failed (kip8test', 1),
    ('kipia-test-v688', None),
    ('planEvents.update` / `planEvents.unmark`', 1),
    ('col.pe-col-month{width:0}', None),
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
print('промт: post-464 записан (кэш v688, тесты 5189/0, эндпоинт update/unmark)')
