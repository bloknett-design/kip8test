#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 463: обновление системного промта (post-463).
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-02 (post-Task 460-462 ПЕРЕНОС'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-02 (post-Task 463; заявка: «Продолжим работу над новым разделом "Плановые мероприятия". Суть раздела в том, чтобы ежемесячно отмечать выполнение перечисленных в таблице мероприятий, с функцией архива в новом файле... Отметки делает пользователь в таблице плана мероприятий путём нажатия на ячейку напротив мероприятия за выбранный месяц, при этом, после подтверждения данного действия, в ячейке вместо тусклого крестика появляется значок галочки зелёного цвета, и эта информация, с указанием наименования мероприятия и даты его выполнения, сохраняется в архив файла Мероприятия_КИП_ИОС»): раздел «Плановые мероприятия» (таблица Task 460, право plan.events Task 462) стал ИНТЕРАКТИВНЫМ. КЛИЕНТ: НОВЫЙ модуль PlanEventsData (перед WorkSchedule) — init при открытии страницы (тусклые SVG-крестики в 96 ячейках + loadMarks), делегированный клик на #peTable, _confirmDialog на базе kip-dialog (наименование + месяц + input type=date «дата выполнения», по умолчанию сегодня), planEvents.mark → ЗЕЛЁНАЯ SVG-галочка (polyline #43a047/#2e7d32, title «Выполнено dd.mm.yyyy») вместо крестика; отмеченная ячейка → тост «Уже отмечено» (mark повторно НЕ шлётся); busy-блокировка; ошибки — тост, ячейка остаётся крестиком; кнопка «Обновить» #peRefreshBtn в шапке (⟳ + pe-refreshing) + подсказка .pe-hint; наименования читаются из DOM (.pe-name) — один источник истины; год плана YEAR=2026. СЕРВЕР: НОВЫЙ scripts/PlanEvents.gs (planEvents.list — отметки года; planEvents.mark — ИДЕМПОТЕНТНО: запись (год, месяц, мероприятие) уже есть → already:true без дубля; валидация год/месяц/мероприятие/дата; аудит PLAN_EVENTS_MARK; доступ plan.events через rmRequirePerm, нет гейта → fail-closed) + 2 case в Code.gs + НОВЫЙ одноразовый идемпотентный scripts/PlanEventsInit.gs (planEventsDeploy — лист «Архив» в файле Мероприятия_КИП_ИОС ID 1uX8Bz6B…: 7 колонок id/дата_выполнения/мероприятие/год/месяц/email/время_отметки, даты текстом \'@\' — паттерн Task 304). АРХИВ — файл Мероприятия_КИП_ИОС (новый, от пользователя): каждая отметка = строка листа «Архив» (наименование + дата выполнения + кто/когда); ручные правки листа поддерживаются (даты текстом и Date, битые строки молча пропускаются). ПОДВОДНЫЕ КАМНИ: (а) закрывающие div диалога ОДНИМ литералом \'</div></div>\' — иначе тест Task 269 ловит конец блока ws-cp-cols; (б) CSS-комментарий НЕ должен содержать литерал \'.pe-row:nth-child(even) td\' — тест 460 ищет ПЕРВОЕ вхождение правила; (в) page.evaluate Playwright — функция БЕЗ IIFE-хвоста (), один аргумент-массив. Тесты 5154/0 (172 файла; НОВЫЙ test-task463.js ×47: SRC ×38 (HTML/CSS/модуль ×12/PlanEvents.gs ×8/init-скрипт ×5/Code.gs ×2/SW ×3) + VM ×9 (ключи/даты-локаль/индекс-дубли); адаптация test-task460 (id=peTable) + test-task461 (окно комментария 700→2000); бамп v687→v688 guards/v686→v687 ассерты, 147 файлов 621 замена). Браузер task463-browser-check.py 42/42 (порт 8995, STATEFUL-мок: A — 2 отметки с сервера, 94 крестика + 2 галочки, title с датой, клик по отмеченной → тост «Уже отмечено» без mark, клик по пустой → диалог (наименование+месяц+дата=сегодня) → Отмена; B — подтверждение → mark payload {token, year:2026, month, event, date} → зелёная галочка + title + тост + повторное открытие с сервера; C — already:true идемпотентность; D — ошибка сервера → ячейка остаётся крестиком; E — старый сервер Unknown action → тихая автозагрузка; F — «Обновить» + мобайл 375 светлая; 0 JS ×6). VLM ×4 (тусклые крестики/зелёные галочки/подсказка/кнопка; галочка явно выделяется; мобильная декабрьская после скролла). DEPLOY-Task463-plan-events-marks-archive.md (ШАГИ СЕРВЕРА: PlanEvents.gs + 2 case в Code.gs + New version развёртывания + planEventsDeploy; порядок любой — тихая деградация). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @6f5b4bed SW `kipia-test-v687` (guard v688), тесты 5154/0; kip8 @11617e1, SW `kipia-v499` (guard v500), тесты 5113/0 — Task 463 ВЫЖИДАЕТ ПЕРЕНОСА В kip8 (инкремент kipia-v499→v500; СЕРВЕР ОБЩИЙ — вставить PlanEvents.gs + case в Apps Script ОДИН раз, init-скрипт уже нужен для общего листа «Арххив»); десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 464 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-460-462 ПЕРЕНОС')
    sys.exit(1)

n_prev_before = src.count(PREV_MARK)

# индексы текущей строки 3
i3 = src.index(CUR_MARK)
i3end = src.index('\n', i3)
old_line3 = src[i3:i3end]

# (а) удалить САМУЮ СТАРУЮ строку «предыдущая» (последняя в цепочке —
# post-449; храним 2 предыдущие версии: post-462 и post-460-462 ПЕРЕНОС)
if src.count(PREV_MARK) > 2:
    iprev = src.rindex(PREV_MARK)
    iprev_end = src.index('\n', iprev)
    src = src[:iprev] + src[iprev_end + 1:]

# (б) строка 3 → новая версия + «предыдущая» из старой строки 3
new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
src = src[:i3] + NEW_LINE3 + '\n' + new_prev + src[i3end:]

# (в) «Текущая версия кэша» v686 → v687
old_cache = '> **Текущая версия кэша:** `kipia-test-v686`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v687`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v686` → `kipia-test-v687` (для kip8test) или `kipia-v499` → `kipia-v500` (для kip8)'
new_inc = 'Формат: `kipia-test-v687` → `kipia-test-v688` (для kip8test) или `kipia-v499` → `kipia-v500` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5107 → 5154
old_exp = '# Ожидается: 5107 passed, 0 failed (kip8test; в kip8 — 5113 passed, 0 failed)'
new_exp = '# Ожидается: 5154 passed, 0 failed (kip8test; в kip8 — 5113 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)
old_exp2 = 'ожидается `5107 passed, 0 failed` (для kip8test; в kip8 — `5113 passed, 0 failed`)'
new_exp2 = 'ожидается `5154 passed, 0 failed` (для kip8test; в kip8 — `5113 passed, 0 failed`)'
if old_exp2 in src:
    src = src.replace(old_exp2, new_exp2, 1)

# (е) Серверные эндпоинты: + planEvents.* (после workSchedule)
old_ep = '| `workSchedule.*` | График работы/табель: шахматка / сотрудники / инструктажи / отпуска / СИЗ — `listEntries`/`listEmployees`/`listTrainings`/`listVacations`/`listPpe` (СИЗ, Task 392)/`generateMonth`/`getPatterns`/`getStatusCodes`/`addEmployee`/`updateEmployee` (Task 384)/`dismissEmployee`/`addTraining`/`deleteTraining`/`addVacation`/'
new_ep = old_ep + '\n| `planEvents.list` / `planEvents.mark` | «Плановые мероприятия»: отметки года / отметка выполнения (идемпотентно, Task 463; архив файла Мероприятия_КИП_ИОС, лист «Архив»). |'
if old_ep not in src:
    print('ОШИБКА: не найдена строка эндпоинтов workSchedule')
    sys.exit(1)
src = src.replace(old_ep, new_ep, 1)

# (ж) Источники данных: + файл Мероприятия_КИП_ИОС (после матрицы прав)
old_ds = '| **МАТРИЦА ПРАВ** (Task 293-296) | листы matrix/permissions/roles — галочки = права (13 прав × 12 ролей) | `1TmmNZLUArWH38F6NX0gMGar8LMNMQomm_FaGZv9osyk` |'
new_ds = old_ds + '\n| **Мероприятия_КИП_ИОС** (Task 463) | лист «Архив» — отметки выполнения «Плановых мероприятий» (id, дата_выполнения, мероприятие, год, месяц, email, время_отметки) | `1uX8Bz6FBS9HniZfWQnHeeyccTwwjwyvpPFWyFkIclCs` |'
if old_ds not in src:
    print('ОШИБКА: не найдена строка матрицы прав в источниках данных')
    sys.exit(1)
src = src.replace(old_ds, new_ds, 1)

# (з) список файлов Apps Script: + PlanEvents.gs / PlanEventsInit.gs
old_gs = '`RoleMatrixInit.gs` (одноразовый init матрицы), `RoleMatrixTask340Init.gs` (одноразовый init уровней view.min),'
new_gs = '`PlanEvents.gs` (Task 463: план-мероприятия — отметки/архив), `PlanEventsInit.gs` (одноразовый init листа «Архив» файла Мероприятия_КИП_ИОС), `RoleMatrixInit.gs` (одноразовый init матрицы), `RoleMatrixTask340Init.gs` (одноразовый init уровней view.min),'
if old_gs not in src:
    print('ОШИБКА: не найден список файлов Apps Script')
    sys.exit(1)
src = src.replace(old_gs, new_gs, 1)

# проверки
checks = [
    ('post-Task 463', 1),
    ('Версия документа (предыдущая):** 2026-10-02 (post-Task 460-462 ПЕРЕНОС', 1),
    ('5154 passed, 0 failed (kip8test', 1),
    ('kipia-test-v687', None),
    ('planEvents.mark` | «Плановые мероприятия»', 1),
    ('Мероприятия_КИП_ИОС** (Task 463)', 1),
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
print('промт: post-463 записан (кэш v687, тесты 5154/0, эндпоинты/источники/Apps Script-файлы)')
