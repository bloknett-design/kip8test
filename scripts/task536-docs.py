#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 536 — docs-коммит kip8test (по образцу task535-docs.py):
  1) версионная строка промта: post-Task 536 ЗАМЕНЯЕТ post-Task 535;
  2) ARCHITECTURE.md §2 — счётчики: 7028 тестов / 233 тест-файлов,
     зеркало kip8test-desktop 7013;
  3) worklog.md — запись Task 536 (финализация).
Коммит делает обёртка (bash). Скрипт — артефакт коммита.
"""
import io

P_PROMT = 'Системный_промт_для_приложения_КИПиА.md'
P_ARCH = 'ARCHITECTURE.md'
P_WLOG = 'worklog.md'


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


# ---------- 1. Версионная строка промта ----------
T536 = (
    '> **Версия документа:** 2026-10-16 (post-Task 536 — ТАБЕЛЬ: '
    'СЕРВЕРНАЯ ПОГОДА УДАЛЕНА (заявка: «Через сервер погода не '
    'загружается, работает только через wttr.in (напрямую из '
    'браузера), поэтому убери из кода WorkSchedule.gs не рабочие '
    'строки кода связанные с погодой»): (1) WorkSchedule.gs −290 '
    'строк — getWeather (кэш 30 мин/UA-заголовки/diag) + парсеры '
    '_parseMeteoinfo/_parseOpenMeteo + топ-уровневая authorizeWeather '
    '— серверным запросам UrlFetchApp не хватало области '
    'script.external_request, авторизация не выдана; заметки Task 536 '
    'на местах удаления; шапка-индекс эндпоинтов без getWeather; '
    '_getProdCal/legalic НЕ тронут (НЕ погода); (2) Code.gs: роутинг '
    'case workSchedule.getWeather УДАЛЁН; (3) КЛИЕНТ: '
    '_loadWeather — двухканальная цепочка open-meteo → wttr.in БЕЗ '
    'серверного резерва (сбой обоих → why:network с причинами '
    'direct+wttr), _weatherOk — без ветки server, _renderSettings — '
    'единая ветка сбоя «Прямые запросы open-meteo/wttr.in не прошли '
    '(…) Повтор — по расписанию или кнопкой ниже» (устойчива к любому '
    'diag), подсказки authorizeWeather/appsscript.json/oauthScopes '
    'УДАЛЕНЫ; (4) тесты — НОВЫЙ test-task536.js ×27 + адаптация '
    'test-task530/532/533/534/535.js (fetch-моки вместо KipAuth; '
    'серверные describe → ассерты удаления; панель без подсказок '
    'сервера) + бамп SW v748→v749 (907 замен/209 файлов, гварды v750 '
    'ПЕРВЫМИ) — итог 7028/0 (+10); (5) верификация: браузер '
    'task536-browser-check.py 25/25 (обе темы: OM 503 → wttr «-2°» '
    'облака, сервер НЕ звался; оба пали → «--» + статус без подсказок; '
    'календарь 30px жив; 1024 светлая; 0 JS-ошибок; страховка клика от '
    'плавающего «не виден»); УРОКИ: ассерты «строки нет» — в КОДОВОЙ '
    'форме (заметки-комментарии легитимно упоминают имена удалённых '
    'функций и wttr.in); DEPLOY-Task536 (КЛИЕНТ: Ctrl+Shift+R — само; '
    'СЕРВЕР опционален: чистка мёртвого кода — свежие WorkSchedule.gs '
    '+ Code.gs + New version, authorizeWeather больше НЕ запускать; '
    'kipia-test-v749, Task 536))')

promt = read(P_PROMT)
lines = promt.split('\n')
assert 'post-Task 535' in lines[2], 'строка 3 не post-Task 535!'
lines[2] = T536
write(P_PROMT, '\n'.join(lines))
print('промт: строка версии заменена post-Task 535 → post-Task 536')

# ---------- 2. ARCHITECTURE.md §2 ----------
arch = read(P_ARCH)
old = ('`tests/`, 7018 тестов, 232 тест-файлов, `node tests/run-all.js`; '
       'зеркало CI: kip8test-desktop 7003')
new = ('`tests/`, 7028 тестов, 233 тест-файлов, `node tests/run-all.js`; '
       'зеркало CI: kip8test-desktop 7013')
assert old in arch, 'не найден счётчик ARCHITECTURE.md'
arch = arch.replace(old, new, 1)
write(P_ARCH, arch)
print('ARCHITECTURE.md: 7018/232/7003 → 7028/233/7013')

# ---------- 3. worklog.md ----------
WLOG = (
    '\n---\n'
    'Task ID: 536 (финализация)\n'
    'Agent: main (Super Z)\n'
    'Task: Заявка Task 536: «Через сервер погода не загружается, '
    'работает только через wttr.in (напрямую из браузера), поэтому '
    'убери из кода WorkSchedule.gs не рабочие строки кода связанные '
    'с погодой».\n'
    '\n'
    'Work Log:\n'
    '- СЕРВЕР WorkSchedule.gs −290 строк (scripts/'
    'task536-remove-server-weather.py, якорный хирургический скрипт '
    'с контролем ГONE/KEPT): эндпоинт getWeather + _parseMeteoinfo + '
    '_parseOpenMeteo + authorizeWeather() с инструкцией; заметки '
    '«Task 536 — СЕРВЕРНАЯ ПОГОДА УДАЛЕНА» на обоих местах; '
    '_getProdCal/legalic НЕ тронут (заявка была про погоду; замер: '
    'ws_prodcal_ на месте).\n'
    '- Code.gs: роутинг case workSchedule.getWeather → заметка '
    'Task 536 (в обоих репо — точечно, репо дрейфанули).\n'
    '- КЛИЕНТ index.html: _loadWeather — OM → wttr, серверный резерв '
    'УДАЛЁН (canServer/KipAuth.api/why:no-endpoint/why:server); '
    '_weatherOk — без ветки via:server; _renderSettings — единая '
    'ветка сбоя для ЛЮБОГО не-ok diag («Прямые запросы '
    'open-meteo/wttr.in не прошли» + dnote + «Повтор — по расписанию '
    'или кнопкой ниже»); подсказки authorizeWeather/appsscript.json/'
    'oauthScopes удалены из панели; комментарии-заметки Task 536 '
    '(шапка LCD/OM_URL/секция погоды/start()).\n'
    '- Тесты: НОВЫЙ test-task536.js ×27 (SRC СЕРВЕР/КЛИЕНТ + VM '
    'цепочка/панель + SW) + адаптация 530/532/533/534/535.js: '
    'погодные VM-тесты переведены с kipAuth-моков на fetch-моки '
    '(routeFetch), серверные describe → ассерты удаления, фикстуры '
    'meteoinfo/wsSandbox/noCache убраны, статусы панели — без '
    'подсказок сервера; бамп SW v748→v749 (907 замен/209 файлов, '
    'гварды v750 первыми) — итог 7028/0 (+10).\n'
    '- Верификация: браузер task536-browser-check.py 25/25 (обе '
    'темы, DPR 2/1: OM 503 → wttr.in «-2°» иконка cloud, канал wttr '
    '«(напрямую из браузера)» набл. 08:51, блок 177..203 (геометрия '
    '535 жива), сервер Apps Script НЕ звался; оба пали → «--» + '
    'why:network + http_503/http_502 в dnote; календарь 30px; 1024 '
    'светлая; 0 JS-ошибок). УРОК: ассерты «строки нет» писать в '
    'КОДОВОЙ форме — заметки Task 536 легитимно упоминают имена '
    'удалённых функций (wttr.in тоже: «entries.push» ⊃ «tries.push» '
    '— ложное срабатывание).\n'
    '- Пуши и зеркала: kip8test bc37e572 (feat) → CI Tests + Pages + '
    'синк → kip8test-desktop bot 828d5e29d3 → CI 7013/0 + Build '
    'success.\n'
    '- Docs: DEPLOY-Task536-server-weather-removed.md (КЛИЕНТ: '
    'Ctrl+Shift+R — само; СЕРВЕР опционален — чистка мёртвого кода: '
    'свежие WorkSchedule.gs + Code.gs + New version; authorizeWeather '
    'больше НЕ запускать), промт post-Task 536, ARCHITECTURE.md §2 '
    '(7028/233 + зеркало 7013), эта запись; локальный scripts/: '
    'task536-remove-server-weather.py, task536-bump-sw.py, '
    'task536-browser-check.py, task536-ci-wait.py.\n'
    '\n'
    'Stage Summary:\n'
    '- Task 536 в kip8test ЗАКРЫТ: репо ЗЕЛЁНОЕ (7028/0), Pages '
    'обновлён, десктоп-зеркало синкнуто (828d5e29d3, 7013/0 + Build). '
    'Из заявки выполнено ВСЁ: нерабочие строки погоды убраны из '
    'WorkSchedule.gs (−290 строк) и Code.gs (роутинг); клиент — '
    'только прямые каналы open-meteo → wttr.in (у пользователя '
    'работает wttr.in). SW: kipia-test-v749. Хвостов НЕТ. '
    'СЛЕДУЮЩАЯ ЗАДАЧА: перенос в kip8 (Task 536-mirror).\n')

wlog = read(P_WLOG)
wlog += WLOG
write(P_WLOG, wlog)
print('worklog.md: запись Task 536 добавлена')
print('OK — docs готовы к коммиту')
