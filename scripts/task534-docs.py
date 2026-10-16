#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 534 — docs-коммит kip8test (по образцу task533-docs.py):
  1) версионная строка промта: post-Task 534 ЗАМЕНЯЕТ post-Task 533;
  2) ARCHITECTURE.md §2 — счётчики: 6986 тестов / 231 тест-файлов,
     зеркало kip8test-desktop 6971;
  3) worklog.md — запись Task 534 (финализация).
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
T534 = (
    '> **Версия документа:** 2026-10-16 (post-Task 534 — ТАБЕЛЬ: '
    'LCD-ИНФОРМЕР — ПОГОДА: ДВА ПРЯМЫХ КАНАЛА (open-meteo.com → '
    'wttr.in) + подсказка authorizeWeather; КАЛЕНДАРЬ: строки головы '
    'ПО ЛЕВОМУ КРАЮ, подписи «Год»/«Месяц» УБРАНЫ, шрифт месяца '
    'мельче года (заявка: «Погода не работает \"Источники не дали '
    'данных (прямой запрос: Failed to fetch); сервер: '
    'meteoinfo:exception:У вас нет разрешения на вызов функции '
    '\\"UrlFetchApp.fetch\\". Т; open-meteo:exception:…\". В '
    'календаре, кнопки с годом выравняй по левому краю, надписи '
    '\\"Год\\" и \\"Месяц\\" убери, шрифт в кнопках месяца сделай '
    'немного меньше чем в годе.»): (1) ДИАГНОЗ — прямой канал Task '
    '533 в сети пользователя недоступен (Failed to fetch), серверный '
    'резерв падает по «нет разрешения UrlFetchApp» (токен '
    'развёртывания без области script.external_request — авторизовано '
    'до Task 530); (2) КАНАЛ 2 — wttr.in (другой хост): WT_URL '
    'format=j1&lang=ru + _fetchWttr + _parseWttr (lang_ru/EN-слова → '
    'русское явление, cloudcover % → балл 0..10, км/ч → м/с ÷3.6, '
    'гПа → мм ÷1.33322, observation_time UTC AM/PM → местное +7); '
    '_loadWeather цепочкой open-meteo → wttr → сервер; причины сбоев '
    'ОБОИХ прямых каналов в _weatherDiag.direct/.wttr и в статусе '
    '(«(прямой запрос: open-meteo: …; wttr.in: …)»); wttr помечается '
    '«напрямую из браузера»; (3) ПОДСКАЗКА АВТОРИЗАЦИИ — diag с «нет '
    'разрешения|UrlFetchApp» → «запустите authorizeWeather() … и '
    'создайте новую версию развёртывания (DEPLOY-Task534)»; (4) '
    'КАЛЕНДАРЬ — justify-content: flex-start у ОБЕИХ строк (левый '
    'край ‹ = левому краю сетки дней), подписи удалены из разметки '
    'И CSS (.ws-lcd-cal-yearlbl/.ws-lcd-cal-monthlbl), шрифт месяца '
    '12px/15px/12px против года 13px/16px/13px; (5) СЕРВЕР '
    'WorkSchedule.gs — топ-уровневая authorizeWeather() (разовая '
    'авторизация внешних запросов; выбрать в редакторе → Выполнить → '
    'подтвердить доступ → новая версия развёртывания) + diag '
    '60→90 символов; Code.gs и листы НЕ менялись; (6) тесты — НОВЫЙ '
    'test-task534.js ×32 + адаптация test-task533.js/test-task532.js '
    '(подписи убраны, формулировки, wttr-поле) + бамп SW v746→v747 '
    '(895 замен/207 файлов, гварды v748 ПЕРВЫМИ) — итог 6986/0 '
    '(+32); (7) верификация: браузер task534-browser-check.py 35/35 '
    '(подписей в DOM нет; flex-start + геометрия левого края; '
    'шрифты 12/13/15/16/12; навигация жива; ПОГОДА: OM ok → wttr и '
    'сервер НЕ звались; OM сбой → wttr успех, сервер НЕ звался; оба '
    'сбоя → сервер; «нет разрешения» → подсказка authorizeWeather() '
    '+ dnote двух каналов; 1024 светлая; 0 JS-ошибок); '
    'DEPLOY-Task534 (СЕРВЕР: WorkSchedule.gs + authorizeWeather() + '
    'новая версия развёртывания — иначе резерв погоды падает по '
    'разрешению; КЛИЕНТ: Ctrl+Shift+R; kipia-test-v747, Task 534))')

promt = read(P_PROMT)
lines = promt.split('\n')
assert 'post-Task 533' in lines[2], 'строка 3 не post-Task 533!'
lines[2] = T534
write(P_PROMT, '\n'.join(lines))
print('промт: строка версии заменена post-Task 533 → post-Task 534')

# ---------- 2. ARCHITECTURE.md §2 ----------
arch = read(P_ARCH)
old = ('`tests/`, 6954 теста, 230 тест-файлов, `node tests/run-all.js`; '
       'зеркало CI: kip8test-desktop 6939')
new = ('`tests/`, 6986 тестов, 231 тест-файлов, `node tests/run-all.js`; '
       'зеркало CI: kip8test-desktop 6971')
assert old in arch, 'не найден счётчик ARCHITECTURE.md'
arch = arch.replace(old, new, 1)
write(P_ARCH, arch)
print('ARCHITECTURE.md: 6954/230/6939 → 6986/231/6971')

# ---------- 3. worklog.md ----------
WLOG = (
    '\n---\n'
    'Task ID: 534 (финализация)\n'
    'Agent: main (Super Z)\n'
    'Task: Заявка Task 534: погода — «Источники не дали данных '
    '(прямой запрос: Failed to fetch); сервер: …нет разрешения на '
    'вызов функции UrlFetchApp.fetch…» (второй прямой канал wttr.in '
    '+ подсказка authorizeWeather); календарь — год по левому краю, '
    'подписи «Год»/«Месяц» убрать, шрифт месяца меньше года.\n'
    '\n'
    'Work Log:\n'
    '- Диагноз по тексту ошибки: api.open-meteo.com в сети '
    'пользователя недоступен (Failed to fetch) — единственный '
    'прямой канал Task 533 не работал; серверный резерв падает по '
    '«нет разрешения UrlFetchApp» — развёртывание авторизовано ДО '
    'Task 530, области script.external_request в токене нет.\n'
    '- Погода: КАНАЛ 2 wttr.in (другой хост; WT_URL '
    'format=j1&lang=ru, CORS открыт, без ключа) + _fetchWttr + '
    'клиентский _parseWttr (lang_ru либо EN-ключевые слова → '
    'русское явление; cloudcover % → балл 0..10; км/ч → м/с; гПа → '
    'мм рт.ст.; observation_time UTC AM/PM → местное +7); '
    '_loadWeather цепочкой open-meteo → wttr.in → сервер; '
    '_weatherDiag.direct/.wttr хранят причины ОБЕИХ прямых '
    'каналов, статус панели выводит «(прямой запрос: '
    'open-meteo: …; wttr.in: …)»; _weatherOk: wttr — «напрямую из '
    'браузера».\n'
    '- Подсказка авторизации: diag сервера с «нет '
    'разрешения|UrlFetchApp» → статус добавляет «запустите '
    'authorizeWeather() в редакторе Apps Script и создайте новую '
    'версию развёртывания (DEPLOY-Task534)» — точное лекарство от '
    'ошибки из заявки.\n'
    '- Календарь (заявка): строки ГОДА и МЕСЯЦА — '
    'justify-content: flex-start (левый край ‹ = левому краю '
    'сетки дней); подписи «Год»/«Месяц» удалены из _renderCal и '
    'CSS (.ws-lcd-cal-yearlbl/.ws-lcd-cal-monthlbl); шрифт строки '
    'месяца мельче года (селект 12px < 13px; стрелки 15px < 16px; '
    '«Сегодня» 12px < 13px); навигация не менялась.\n'
    '- Сервер WorkSchedule.gs: топ-уровневая authorizeWeather() '
    '(разовая авторизация внешних запросов: выбрать в списке '
    'функций → Выполнить → подтвердить доступ → новая версия '
    'развёртывания; пробует open-meteo + meteoinfo.ru, результат в '
    'Logger; повторный запуск безопасен) + diag-исключения 60→90 '
    'символов; Code.gs и листы НЕ менялись.\n'
    '- Тесты: НОВЫЙ test-task534.js ×32 (SRC: WT_URL/парсер/'
    'fetch/порядок каналов/подсказка/календарь/CSS/сервер; VM: '
    'парсер полный+lang_ru+EN+cloudcover+AM/PM+мусор; цепочка: '
    'успех OM → wttr НЕ звался / сбой OM → wttr — сервер НЕ звался '
    '/ оба сбой → сервер успех/empty; панель: успех wttr, dnote '
    'два канала, подсказка только при «нет разрешения»; календарь: '
    'подписей нет/порядок/4 стрелки/12 опций/«Сегодня»; SW v747 + '
    'гвард v748) + адаптация test-task533.js (подписи, '
    'формулировки, wttr-поле) и test-task532.js (подпись «Год») + '
    'бамп SW v746→v747 (895 замен/207 файлов, гварды v748 '
    'первыми) — 6986/0 (+32).\n'
    '- Верификация: браузер task534-browser-check.py 35/35 (обе '
    'темы, DPR 2/1: подписей в DOM нет; flex-start + геометрия '
    'левого края обеих строк; шрифты 12/13/15/16/12px; навигация '
    'жива; ПОГОДА: OM ok → wttr/сервер НЕ звались; OM сбой → '
    'wttr.in успех («wttr.in (напрямую из браузера)», −2°, сервер '
    'НЕ звался); оба сбой → сервер −12° «(через Apps Script)»; '
    'diag «нет разрешения» → подсказка authorizeWeather() + dnote '
    '«open-meteo: http_503; wttr.in: http_502»; 1024 светлая; 0 '
    'JS-ошибок).\n'
    '- Пуши и зеркала: kip8test 6ec1b01d (feat) → CI Tests + '
    'Pages + синк 2f5d691 → kip8test-desktop CI 6971/0 + Build '
    'success.\n'
    '- Docs: DEPLOY-Task534-lcd-weather-two-channels-auth-hint.md '
    '(СЕРВЕР: обновить WorkSchedule.gs → выполнить authorizeWeather() '
    '→ новая версия развёртывания; КЛИЕНТ: Ctrl+Shift+R), промт '
    'post-Task 534, ARCHITECTURE.md §2 (6986/231 + зеркало 6971), '
    'эта запись; локальный scripts/: task534-bump-sw.py, '
    'task534-browser-check.py, task534-ci-wait.py.\n'
    '\n'
    'Stage Summary:\n'
    '- Task 534 в kip8test ЗАКРЫТ: репо ЗЕЛЁНОЕ (6986/0), Pages '
    'обновлён, десктоп-зеркало синкнуто (2f5d691, 6971/0 + Build). '
    'Из заявки выполнено ВСЁ: (1) погода — второй прямой канал '
    'wttr.in (open-meteo → wttr → сервер) + подсказка '
    'authorizeWeather для серверного резерва; (2) календарь — '
    'левый край, без подписей, месяц мельче. Пользователю: '
    'WorkSchedule.gs в Apps Script + authorizeWeather() + новая '
    'версия развёртывания (см. DEPLOY-Task534), иначе резерв '
    'погоды падает по разрешению. SW: kipia-test-v747. Хвостов '
    'НЕТ. СЛЕДУЮЩАЯ ЗАДАЧА: перенос в kip8 (Task 534-mirror).\n')

wlog = read(P_WLOG)
wlog += WLOG
write(P_WLOG, wlog)
print('worklog.md: запись Task 534 добавлена')
print('OK — docs готовы к коммиту')
