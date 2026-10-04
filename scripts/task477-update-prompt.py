#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 477: обновление системного промта (post-477) — ЭТАП 3
# ОПТИМИЗАЦИИ: KipPreload — фоновая предзагрузка всех данных ПО
# ПРАВАМ РОЛИ после входа (idle-очередь, паузы ≥1.5 с; статика
# через SWR + серверные копии в KipDB; saveData/2g — пропуск;
# logout — стоп); SW v700→v701; тесты 5586/0.
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-04 (post-Task 476 — ЭТАП 2 ОПТИМИЗАЦИИ по заявке'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-04 (post-Task 477 — ЭТАП 3 ОПТИМИЗАЦИИ по заявке «в принципе должны незаметно подгружаться все данные приложения (только из тех разделов и данных, к которым у пользователя есть доступ согласно его роли)» — завершение этапов 1–2; реализация в kip8test, перенос в kip8 — ПО КОМАНДЕ, партией этапов 1+2+3 одним инкрементом kipia-v509→v510). Состав (КЛИЕНТ-ONLY, Apps Script не тронут): (а) НОВЫЙ модуль KipPreload в index.html (глобальный var, script-блок KipDB): после входа (задержка 4 с от показа UI — KipAuth._schedulePreload, 5 точек входа: verifyOTP, bootstrap быстрый/медленный, офлайн-повтор, фоновая проверка) строит манифест по KipAuth.canAccess (серверная матрица KIP8_Access + легаси-карта — как видимость кнопок UI) и греет кэши ПО ОДНОМУ элементу: статические data/*.json доступных разделов — fetch через SWR (Task 475, прогрев персистентного DATA-кэша тем же путём, что обычное открытие, cache-busting как у разделов — SW нормализует ключ); серверные данные (табель: 7 read-only экшенов → merge-форма кэша Task 314 v1 в KipDB; каб. журнал: getColumns+list(1000) → KipDB-копии колонок+строк; расходомеры: flowmeter.list → {meters,ts}; отметки мероприятий: planEvents.list → merge по годам) — разделы откроются мгновенно даже офлайн при ПЕРВОМ заходе. (б) вежливость: последовательная обработка (один элемент за раз), requestIdleCallback (+fallback setTimeout, timeout 5 с) + пауза ≥1.5 с (GAP_MS) между элементами; Data Saver / 2g / slow-2g (navigator.connection.saveData/effectiveType) — очередь НЕ запускается вовсе; офлайн — пауза, событие online — продолжение; logout — KipPreload.stop() ДО чистки копий (Task 476). (в) границы: только READ-ONLY экшены (каждый гейтится на сервере — клиентская видимость прав не даёт); гость («Общий доступ») и «Запрет» — пустая очередь (калькуляторы без data-файлов); серверные группы — только с токеном; диагностика _state() в консоли (логи [KipPreload]). sw.js kipia-test-v700→v701 + КОМПАКТНЫЙ комментарий Task 477 (~300 симв. — окна истории НЕ расширялись: 474 ~1539<1700, 472 ~1912<2100, 471 ~2461<2700, 461 ~5023<5300; прецедент экономии площади шапки); ЛОГИКИ SW НЕ МЕНЯЛОСЬ (bypass Apps Script / DATA_CACHE / SWR как в Tasks 475/476). Тесты 5586/0 (+34 к 5552): НОВЫЙ test-task477.js ×34 (SW ×5; каркас KipPreload ×8: GAP_MS/IDLE_TIMEOUT, requestIdleCallback+fallback, одноразовость start, stop, online/offline, последовательность — один shift на шаг, _state; VM манифеста ×7: полный доступ 9 json + 4 api с составами, гость — пусто, роль без расходомеров — без flowmeters/fm, без токена — без api, «Запрет» — пусто, saveData/2g/slow-2g блокируют + 4g работает (13 построено/1 в работе), одноразовость; хендлеры read-only ×6: ws 7 экшенов + merge + v1, cj getColumns+list(1000)+обе копии, fm list+{meters,ts}, pe list+merge-годы, статика fetch+SWR; write-экшены отсутствуют — regex-негативы ×11; хуки KipAuth ×4: _schedulePreload 4с+guard, 5 точек вызова, logout stop ДО wipe, guard typeof; границы ×2: DEPLOY-док, окна sw.js без расширения); бамп task477-bump-sw.py: guards v701→v702 (129) ПОСЛЕ ассертов v700→v701 (545), 161 файл, OWN исключён; сверка дистанций якорей в скрипте (окна не менялись); АДАПТАЦИЯ test-task475: окно автоповтора 2400→2800 (_schedulePreload в attempt-успехе +~220 симв. до setInterval). Браузер task477-browser-check.py 43/43 (порт 8992, мок Apps Script + счётчики экшенов + fetch-обёртка в init-script): A — Админ: за ~35 с ФОНОМ прогружены ВСЕ 13 элементов (done=13 fail=0; дашборд активен всё время — пользователь ничего не видел): 9 data/*.json (счётчик fetch) + 11 серверных экшенов (счётчик мока); KipDB заполнен ВСЕМИ 5 копиями ДО первого открытия разделов; SW DATA-кэш прогрет (devices.json); B — logout: started=false, pending=0; C — ГОСТЬ (без токена): 0 запросов данных (кроме легаси pre-cache билетов Task 242 — работает для всех с 2 с, НЕ KipPreload) + 0 серверных экшенов; D — роль «КИП8» (без КИП ИОС/табеля/расходомеров): очередь ровно 2 файла (phonebook+exam-tickets — права секретного+библиотеки), devices.json НЕ запрашивался, серверные экшены разделов = 0; E — saveData: очередь не запущена, 0 запросов; F — 0 JS-ошибок ×4 контекста. DEPLOY-Task477-optimization-stage3-preload-by-role.md (клиент-only, серверных шагов НЕТ, откат — вернуть файлы + поднять версию). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v701` (guard v702), тесты 5586/0; kip8 SW `kipia-v509` (guard v510), тесты 5467/0 — ЭТАПЫ 1+2+3 ЖДУТ ПЕРЕНОСА В kip8 ПО КОМАНДЕ (партией одним инкрементом kipia-v509→v510; маппинг БД kip8-cache-test-v1 → kip8-cache-v1 + версий v699/v700/v701→v510 одним бампом). СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 478 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-476')
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

# (в) «Текущая версия кэша» v700 → v701
old_cache = '> **Текущая версия кэша:** `kipia-test-v700`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v701`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v700` → `kipia-test-v701` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
new_inc = 'Формат: `kipia-test-v701` → `kipia-test-v702` (для kip8test) или `kipia-v510` → `kipia-v511` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5552 → 5586
old_exp = '# Ожидается: 5552 passed, 0 failed (kip8test; в kip8 — 5467 passed, 0 failed)'
new_exp = '# Ожидается: 5586 passed, 0 failed (kip8test; в kip8 — 5467 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# проверки
checks = [
    ('post-Task 477', 1),
    ('kipia-test-v701', None),
    ('KipPreload', None),
    ('5586 passed, 0 failed (kip8test', 1),
    ('СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 478', None),
    ('_schedulePreload', None),
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
print('промт: post-477 записан (кэш v701, тесты 5586/0, следующий 478)')
