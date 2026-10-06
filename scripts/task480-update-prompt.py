#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 480: обновление системного промта (post-480) — смена ссылки на
# Google-таблицу «Перечень КИП ИОС рабочий.xlsx» (новый ID
# 1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee, 31 замена в 15 файлах);
# SW v703→v704; тесты 5733/0; следующий 481.
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-06 (post-Task 479: ППР-ИНДИКАЦИЯ'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-06 (post-Task 480: СМЕНА ССЫЛКИ НА GOOGLE-ТАБЛИЦУ «ПЕРЕЧЕНЬ КИП ИОС РАБОЧИЙ.XLSX». Заявка пользователя: «Поменяй во всех связанных местах и файлах приложения, адрес ссылки на файл "Перечень КИП ИОС рабочий.xlsx" теперь такой https://docs.google.com/spreadsheets/d/1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee/edit?usp=sharing&ouid=110493351905411532775&rtpof=true&sd=true». РЕАЛИЗАЦИЯ (КОНФИГУРАЦИЯ ИСТОЧНИКА ДАННЫХ, клиент-only, Apps Script не тронут, ЗАПИСИ данных не менялись): старый ID 1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy → новый 1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee — 31 замена в 15 файлах: (функциональные — откуда кроны GitHub Actions тянут XLSX) scripts/sync-{devices,lockouts,valves,regulators}.py — DEFAULT_SPREADSHEET_ID + docstring «Источник: …» + env-подсказка (×3 каждый; имена листов _app, env-переменные и механизм export?format=xlsx НЕ менялись) + .github/workflows/sync-*.yml ×4 (URL в комментарии «КАК НАСТРОИТЬ», cron/вызовы не тронуты); (метаданные) data/{devices,lockouts,valves,regulators}.json — source-поле (форма = генерируемой скриптом — после первого крон-синка дифф данных пустой; totals 1291/531/320/268 НЕ менялись); (приложение/доки) index.html ×3 комментария источников («(тот же файл, что и для приборов…)», пояснения «листу "…_app"» живы) + README.md таблица синков ×4 + промт таблица «Источники данных» ×4; worklog.md НЕ трогался — старый ID остаётся в ИСТОРИЧЕСКИХ записях (регламент: историю не переписываем). URL в файлах — чистая форма /edit (параметры usp/ouid/rtpof/sd из ссылки пользователя на экспорт не влияют). СТРУКТУРА НОВОЙ ТАБЛИЦЫ СВЕРЕНА ДО ПРАВКИ (scripts/task480-check-sheet.py — тот же механизм, что синк): валидный xlsx (ZIP PK), все 4 листа _app присутствуют, заголовки идентичны (24/13/24/12 колонок; ID/Наименование/Дата/В гр. ППР/Вид ремонта/Период ремонта/Изображение живы — ППР-индикация Task 478/479 не затронута), строки = текущим данным (1291/531/320/268) — новый файл КОПИЯ старого. sw.js kipia-test-v703→v704 + компактный комментарий ~250 симв. (ЛОГИКА SW НЕ МЕНЯЛАСЬ; IMAGE_CACHE v3/DATA_CACHE v1 НЕ инкрементированы — смена URL не смена структуры, data/*.json обновятся в персистентном DATA-кэше через SWR text-compare); окна истории: комментарий Task 478 отодвинут до ~835 → окна 700→1100 в test-task478.js/test-task479.js (прецедент Task 463/475/479), якоря 461/471/472/474 в прежних окнах 5861/3299/2750/2377 (запасы 101+). Тесты 5733/0 (+60 к 5673): НОВЫЙ tests/test-task480.js ×60 (SW: v704 + guard v705 + комментарий + персистентные кэши; index.html: ровно 3 новых ID, все в комментариях, старого нет, пояснения живы; sync ×4: DEFAULT_SPREADSHEET_ID + docstring + листы/env/export живы; workflows ×4: URL + cron/вызовы; data ×4: source + totals + структура 24 колонок; README/промт: по 4 ID; санитарный скан — старый ID отсутствует в 27 рабочих файлах (worklog/tests исключены: история + негативные ассерты); прочие таблицы проекта НЕ затронуты: каб. журнал 1XsmoyE4…, проекты 1IQq8S4…, расходомеры 1enZSq7K…). Бамп scripts/task480-bump-sw.py: guards v704→v705 (135) ПОСЛЕ ассертов v703→v704 (556), 164 файла, OWN исключён. Браузер scripts/task480-browser-check.py 25/25 (порт 8988, мок Apps Script): приложение открывается (Админ, не логин); SW контролирует после reload, кэш kipia-test-v704 в caches.keys(), v703 нет; DATA-кэш kipia-data-test-v1 хранит devices.json с НОВЫМ ID (старого нет) + total 1291; fetch из страницы: source с новым ID; «КИП ИОС» открывается; «Приборы по производствам»: список отрисован, не «Загрузка…»; карточка ID 1 в десктоп-панели (тёмная + светлая), «Период ремонта» жива; мобильный 375x812 «КИП ИОС»; 0 JS ×3; 4 скриншота; VLM ×1 — дефектов вёрстки нет. DEPLOY-Task480-sheet-url-replace.md (клиент-only, серверных шагов НЕТ; кроны после деплоя пойдут в новую таблицу — ожидается «изменений нет»; откат — вернуть 15 файлов + поднять версию). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v704` (guard v705), тесты 5733/0; kip8 @5da84b8, SW `kipia-v510`, тесты 5592/0 — Tasks 478+479+480 ЖДУТ ПЕРЕНОСА В kip8 ПО КОМАНДЕ (партией одним инкрементом kipia-v510→v511; URL-замена в kip8 — те же 15 файлов, де-изоляция JS-логики не требуется — правка конфигурационная). СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 481 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-479')
    sys.exit(1)

# (а) удалить самую старую строку «предыдущая» (ПОСЛЕДНЯЯ по позиции —
# подводный камень из Task 475-477: rindex, не первая)
if src.count(PREV_MARK) > 2:
    iprev = src.rindex(PREV_MARK)
    iprev_end = src.index('\n', iprev)
    src = src[:iprev] + src[iprev_end + 1:]

i3 = src.index(CUR_MARK)
i3end = src.index('\n', i3)
old_line3 = src[i3:i3end]

# (б) строка 3 → новая версия + «предыдущая» из старой строки 3
new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
src = src[:i3] + NEW_LINE3 + '\n' + new_prev + src[i3end:]

# (в) «Текущая версия кэша» v703 → v704
old_cache = '> **Текущая версия кэша:** `kipia-test-v703`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v704`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии (kip8 ждёт партию
# 478+479+480 одним инкрементом v510→v511 — сторона kip8 не меняется)
old_inc = 'Формат: `kipia-test-v703` → `kipia-test-v704` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
new_inc = 'Формат: `kipia-test-v704` → `kipia-test-v705` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5673 → 5733 (kip8 не менялся — 5592)
old_exp = '# Ожидается: 5673 passed, 0 failed (kip8test; в kip8 — 5592 passed, 0 failed)'
new_exp = '# Ожидается: 5733 passed, 0 failed (kip8test; в kip8 — 5592 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# (е) факт-строка «Тесты» в таблице раздела: 5673/187 → 5733/188
old_cnt = '(`tests/`, 5673 теста, 187 тест-файлов, `node tests/run-all.js`)'
new_cnt = '(`tests/`, 5733 теста, 188 тест-файлов, `node tests/run-all.js`)'
if old_cnt not in src:
    print('ОШИБКА: не найдена факт-строка тестов в таблице')
    sys.exit(1)
src = src.replace(old_cnt, new_cnt, 1)

# проверки
checks = [
    ('post-Task 480', 1),
    ('kipia-test-v704', None),
    ('1ZKOPBsD9x4wdlC5rDjz09UypD86G0Cee', None),  # таблица источников ×4 + строка 3
    ('5733 passed, 0 failed (kip8test', 1),
    ('СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 481', 1),
    ('post-Task 479', 1),      # строка 4 (предыдущая)
    ('1eUUwwulUvKUGWTgQ__XP-y7z1aEkt5Wy', 1),  # строка 3 (заявка: старый ID); таблица источников уже заменена на новый
    ('5861/3299/2750/2377', 1),
    ('5733 теста, 188 тест-файлов', 1),
]
for marker, cnt in checks:
    c = src.count(marker)
    if cnt is not None and c != cnt:
        print('ОШИБКА: маркер %r найден %d раз (ожидалось %s)' % (marker[:60], c, cnt))
        sys.exit(1)
    if cnt is None and c == 0:
        print('ОШИБКА: маркер не найден: %r' % marker[:60])
        sys.exit(1)

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)

print('OK: промт обновлён post-Task 480 (SW v704, тесты 5733/0, следующий 481)')
