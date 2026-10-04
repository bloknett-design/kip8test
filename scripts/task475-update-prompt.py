#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 475: обновление системного промта (post-475) — ЭТАП 1
# ОПТИМИЗАЦИИ: SWR-мгновенное открытие (навигация + данные +
# ассеты), персистентный DATA-кэш kipia-data-test-v1, офлайн-ветка
# входа (гостевой режим + автоповтор), сжатие logo/logo_black/Launch
# (−3,4 МБ); SW v698→v699; тесты 5503/0.
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-04 (post-Task 473-474 ПЕРЕНОС: партия Tasks 473+474 перенесена'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-04 (post-Task 475 — ЭТАП 1 ОПТИМИЗАЦИИ по заявке: «Нужно проработать оптимизацию работы приложения, основные требования — моментальное открытие приложения при отсутствии или медленной связи, ранее подгруженные данные должны сохраняться в памяти устройства для моментального доступа к ним, а загрузка должна быть фоновой (незаметной для пользователя)»; реализация в kip8test, перенос в kip8 — ПО КОМАНДЕ, одним инкрементом kipia-v509→v510). Состав (КЛИЕНТ-ONLY, Apps Script не тронут): (а) sw.js — STALE-WHILE-REVALIDATE: навигация (App Shell) и ВСЕ локальные ассеты отдаются ИЗ КЭША СРАЗУ (сеть не ждём), свежие версии догружаются ФОНОМ; механизм обновления прежний (бамп CACHE_VERSION → install → skipWaiting → activate → controllerchange → перезагрузка). (б) data/*.json — SWR + ПЕРСИСТЕНТНЫЙ DATA_CACHE_NAME (kipia-data-test-v1, НЕ зависит от CACHE_VERSION — как кэш картинок): данные переживают обновления приложения, разделы открываются мгновенно при любой связи; фоновая ревалидация сравнивает тексты (клон cachedForCompare ДО отдачи ответа), при ИЗМЕНЕНИИ — кэш обновляется + вкладкам DATA_REFRESHED с path; fallback на precache из CACHE_NAME; Background Sync (exam-tickets) пишет в тот же кэш; activate держит в DATA-кэше только /data/*.json; bypass Apps Script НЕ тронут (авторизация/heartbeat всегда в сеть). (в) index.html — слушатель DATA_REFRESHED сбрасывает in-memory кэши разделов (resetSectionDataCache: devices/lockouts/valves/regulators/projects/cables/phonebook/exam-tickets) — свежая версия при следующем открытии раздела, БЕЗ перерисовки под пользователем; офлайн-ветка входа: токен есть, кэша роли нет, сети нет → ГОСТЕВОЙ режим (не экран входа) + тост + АВТПОВТОР getCurrentUser (интервал 60 с + событие online + первая попытка через 5 с; _startOfflineTokenRetry/_stopOfflineTokenRetry; verifyOTP останавливает; session_expired — штатный выход через handleSessionExpired). (г) images: logo.png и logo_black.png 2048→256px RGB (по 1450→45 КБ, отображение в шапке 36×36, VLM: артефактов нет) + добавлены в ASSETS; Launch.png 996→363 КБ (256-цветная палитра, фон сайдбара под 50–70% оверлеем); суммарная экономия ~3,4 МБ; иконки манифеста НЕ тронуты. SW kipia-test-v698→v699 + комментарий Task 475 (~9 строк). Тесты 5503/0 (+42 к 5461): НОВЫЙ test-task475.js ×42 (SW ×19: версия/шапка, DATA-кэш/гигиена, SWR-ветки навигации/данных/ассетов, bypass Apps Script до SWR-веток, notifyDataChanged, refreshTicketsData; вход ×10: гостевой режим/тост/60с+online+5с/стоп/verifyOTP/handleSessionExpired/поля состояния; слушатель ×4: resetSectionDataCache/все справочники/без перерисовки; изображения ×5: 256×256/45 КБ/Launch 363 КБ/экономия ≥3 МБ/иконки не тронуты); бамп ассертов v698→v699 (540) + guards v699→v700 (125) — task475-bump-sw.py, 159 файлов, OWN исключён; окна истории версий sw.js (прецедент Task 471/473/474): test-task461 3800→4600 (Task 461 ~4300), test-task471 + test-task472 (Task 471) 1300→2100 (~1738), test-task472 (Task 472) 900→1500 (~1189), test-task474 600→1100 (~816) + дистанции в test-task474 1300→2100/3800→4600. Браузер task475-browser-check.py 28/28 (порт 8994, мок Apps Script: полный офлайн — reload 0.36 с, «Приборы» из кэша устройства без сети; медленная сеть CDP 4 с + 50 Кбит/с, эмуляция проверена замером 4.10 с — открытие 0.34 с; офлайн-вход — гостевой режим + тост + автоповтор; возврат связи — роль Админ применена, повтор остановлен, тост «Связь восстановлена»; SWR — изменение data/devices.json на диске поймано фоном (консоль Task475), следующий заход — свежие данные с маркером; 0 JS-ошибок). VLM ×4 (офлайн-приборы/гостевой режим/восстановление входа + сравнение сжатых картинок). DEPLOY-Task475-optimization-stage1-swr-offline.md (клиент-only, серверных шагов НЕТ). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v699` (guard v700), тесты 5503/0; kip8 SW `kipia-v509` (guard v510), тесты 5467/0 — ЭТАП 1 ЖДЁТ ПЕРЕНОСА В kip8 ПО КОМАНДЕ (одним инкрементом kipia-v509→v510; ЭТАПЫ 2–3 оптимизации — IndexedDB-кэш/предзагрузка по правам роли, Web Worker/минификация — по отдельным заявкам). СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 476 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-473-474-ПЕРЕНОС')
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

# (в) «Текущая версия кэша» v698 → v699
old_cache = '> **Текущая версия кэша:** `kipia-test-v698`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v699`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v698` → `kipia-test-v699` (для kip8test) или `kipia-v509` → `kipia-v510` (для kip8)'
new_inc = 'Формат: `kipia-test-v699` → `kipia-test-v700` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5461 → 5503
old_exp = '# Ожидается: 5461 passed, 0 failed (kip8test; в kip8 — 5467 passed, 0 failed)'
new_exp = '# Ожидается: 5503 passed, 0 failed (kip8test; в kip8 — 5467 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# проверки
checks = [
    ('post-Task 475', 1),
    ('Версия документа (предыдущая):** 2026-10-04 (post-Task 473-474 ПЕРЕНОС', 1),
    ('5503 passed, 0 failed (kip8test', 1),
    ('kipia-test-v699', None),
    ('kipia-data-test-v1', None),
    ('СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 476', None),
    ('resetSectionDataCache', None),
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
print('промт: post-475 записан (кэш v699, тесты 5503/0, следующий 476)')
