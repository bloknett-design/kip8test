#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 476: обновление системного промта (post-476) — ЭТАП 2
# ОПТИМИЗАЦИИ: KipDB (IndexedDB) — кэш СЕРВЕРНЫХ данных (табель/
# каб. журнал/расходомеры/отметки мероприятий) рядом с localStorage
# (квота ~5 МБ больше не режет локальные копии); storage.persist()
# после входа; чистка копий при logout; SW v699→v700; тесты 5552/0.
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-04 (post-Task 475 — ЭТАП 1 ОПТИМИЗАЦИИ по заявке'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-04 (post-Task 476 — ЭТАП 2 ОПТИМИЗАЦИИ по заявке «ранее подгруженные данные должны сохраняться в памяти устройства для моментального доступа к ним» — для СЕРВЕРНЫХ данных Apps Script, которые SW не кэширует (bypass); реализация в kip8test, перенос в kip8 — ПО КОМАНДЕ, одним инкрементом kipia-v509→v510). Состав (КЛИЕНТ-ONLY, Apps Script не тронут): (а) НОВЫЙ модуль KipDB в index.html (глобальный var, отдельный script): мини-обёртка IndexedDB (БД kip8-cache-test-v1, store kv, промисы get/set/del/keys/clear, тихие ошибки, guard «typeof KipDB» везде — модуль необязателен; перенос в kip8 → имя kip8-cache-v1) — надёжный ёмкий слой локальных копий серверных данных: квота localStorage (~5 МБ, синхронный) больше не может ТИХО потерять копии разделов. (б) WorkSchedule (Task 314): _cacheWrite пишет в ОБА слоя (KipDB.set + localStorage — прежний синхронный слой жив, тесты Task 314 зелёные); разбор объекта кэша вынесен в _restoreFromObj (общий для слоёв, формат v1 не менялся; АДАПТАЦИЯ тестов 314/412/440/407/408 — ассерты разбора переехали на _restoreFromObj, VM-хосты подгружают его); _idbRestoreView — асинхронный добор из KipDB ДО сети (промах localStorage: квота/чистка) + миграция LS→KipDB (одноразово сама собой); init и loadGrid зовут KipDB-ветку до сетевого пути (сетевой путь вложен в .then(idbTry), this.→self. внутри — адаптация текстовых ассертов 274/305/308/317/387/392 + окно test-vacation-shift 2600→3600); force («Обновить») кэш НЕ читает — только сеть, как прежде. (в) KipCableJournal: _persistData/_persistColumns — оба слоя (единый снапшот, одинаковое ts); _idbRestore (LS-промах → KipDB: колонки+строки → рендер, затем фоновое обновление как обычно) + миграция. (г) FlowmeterData: _persistData — оба слоя; _idbRestore(silent) по образцу _restoreCache + миграция. (д) PlanEventsData: локальная копия отметок ВПЕРВЫЕ (_marksCacheKey kip8_pe_marks_v1, формат {v:1,years:{год:{marks,ts}}}; _cacheMarks после успешного planEvents.list; _restoreMarksCache ДО loadMarks в init — раздел открывается с галочками мгновенно при любой связи, merge по годам не затирает соседние годы). (е) KipAuth: _requestPersistentStorage (navigator.storage.persist, идемпотентно через _persistAsked; 5 точек вызова — verifyOTP, bootstrap быстрый/медленный, офлайн-повтор, фоновая проверка) + _wipeLocalServerData при LOGOUT (ручной выход — устройство могут передать; LS-ключи копий kip8_ws_cache_v1/kip8_cj_cache_v1/kip8_cj_cols_v1/kip8_flow_cache_v1 + KipDB.clear() целиком; автоистечение сессии handleSessionExpired НЕ чистит — тот же пользователь вернётся; статические публичные data/*.json SW-кэша и настройки интерфейса НЕ трогаются). sw.js kipia-test-v699→v700 + комментарий Task 476 (~7 строк; ЛОГИКИ SW НЕ МЕНЯЛОСЬ — кэш статический, bypass Apps Script/ DATA_CACHE/SWR как в Task 475). Тесты 5552/0 (+49 к 5503): НОВЫЙ test-task476.js ×49 (SW-версия/шапка ×5, KipDB модуль ×5 + VM roundtrip на фейковом indexedDB ×4, persist/wipe ×6, WorkSchedule ×7 (вкл. VM _cacheWrite без KipDB — деградация тихая), CableJournal ×4, FlowmeterData ×3, PlanEvents ×7 (вкл. VM _cacheMarks/_restoreMarksCache roundtrip + нет копии → false), границы ×4, окна истории ×4); бамп task476-bump-sw.py: guards v700→v701 (127) ПОСЛЕ ассертов v699→v700 (542), 160 файлов, OWN исключён; окна истории sw.js (комментарий Task 476 ~490 симв. отодвинул якоря): 461 4600→5300, 471 2100→2700, 472 1500→2100 и 2100→2700, 474 1100→1700 + дистанции 2100→2700/4600→5300 (адаптация test-task475 окон на новые литералы). Браузер task476-browser-check.py 27/27 (порт 8993, мок Apps Script): A — «График работы» грузится с сервера, копия в ДВА слоя (LS жив + KipDB kip8_ws_cache_v1 с текущим видом/сотрудниками), storage.persist запрошен; F — расходомеры: KipDB-копия + LS-копия; B — LS-копия УДАЛЕНА + Apps Script недоступен (route.abort) + офлайн → сетка поднята МГНОВЕННО из KipDB (0.42 с, без экрана ошибки) — квота больше не режет копии; C — отметки мероприятий: онлайн пишутся в kip8_pe_marks_v1 (годы), офлайн восстановлены (галочки pe-m-done на месте, 0.37 с); D — logout: KipDB ПОЛНОСТЬЮ пуст, LS-копии стёрты, настройки (тема) не тронуты; E — 0 JS-ошибок. DEPLOY-Task476-optimization-stage2-idb-server-cache.md (клиент-only, серверных шагов НЕТ, откат — вернуть файлы + поднять версию). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v700` (guard v701), тесты 5552/0; kip8 SW `kipia-v509` (guard v510), тесты 5467/0 — ЭТАПЫ 1+2 ЖДУТ ПЕРЕНОСА В kip8 ПО КОМАНДЕ (партией одним инкрементом kipia-v509→v510; маппинг БД kip8-cache-test-v1 → kip8-cache-v1). СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 477 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-475')
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

# (в) «Текущая версия кэша» v699 → v700
old_cache = '> **Текущая версия кэша:** `kipia-test-v699`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v700`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v699` → `kipia-test-v700` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
new_inc = 'Формат: `kipia-test-v700` → `kipia-test-v701` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5503 → 5552
old_exp = '# Ожидается: 5503 passed, 0 failed (kip8test; в kip8 — 5467 passed, 0 failed)'
new_exp = '# Ожидается: 5552 passed, 0 failed (kip8test; в kip8 — 5467 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# проверки
checks = [
    ('post-Task 476', 1),
    ('kipia-test-v700', None),
    ('kip8-cache-test-v1', None),
    ('5552 passed, 0 failed (kip8test', 1),
    ('СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 477', None),
    ('KipDB', None),
    ('_wipeLocalServerData', None),
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
print('промт: post-476 записан (кэш v700, тесты 5552/0, следующий 477)')
