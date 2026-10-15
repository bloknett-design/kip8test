#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 529 — docs-коммиты (КИПИА-конвейер, по образцу Task 528):
  1) версионная строка промта: post-Task 529 ПРЕДШЕСТВУЕТ, post-Task
     528 демонирован в хвост (оба репо);
  2) ARCHITECTURE.md §2 — счётчики тестов + зеркала + число файлов;
  3) worklog.md — записи финализации ×2 (kip8test + kip8).
Файлы правятся, коммиты делает обёртка (bash).
"""
import io


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


T529 = ('post-Task 529 — ТАБЕЛЬ: LCD-ОКНО «ПЕЙДЖЕР» В БАРЕ КРОШЕК — '
        'ВРЕМЯ, ДАТА, КАЛЕНДАРЬ ПО МЕСЯЦАМ, СООБЩЕНИЯ В ДВЕ СТРОКИ '
        '(заявка: «В десктопной версии, в разделе Табель учёта рабочего '
        'времени, в баре с хлебными крошками, справа сделай окно с '
        'рамками и эффектом вдавливания с показаниями текущего времени '
        'и датой, с возможностью открытия календаря по месяцам. Сделай '
        'в стиле как на приложенном фото, только из квадратных сегментов '
        'в поле окна с разрешением к примеру 10х60 или лучше выбери сам '
        'оптимальное разрешение пикселей экрана с заделом что на этом '
        'экране могут выводиться сообщения в две строки (по типу как '
        'раньше было на пейджерах).»; фото — настольная метеостанция: '
        'серо-зелёный ЖК, тёмные символы, чёрный корпус, 2 строки): (1) '
        'HTML — #wsLcdWrap (кнопка #wsLcdClock + canvas #wsLcdCanvas '
        '96×17 + #wsLcdCal hidden) в page-inline-header Табеля ПОСЛЕ '
        'заголовка, aria-haspopup/expanded/label; (2) CSS — ТОЛЬКО '
        '≥1024px (базовый display:none, мобильный бар не тронут), '
        'margin-left:auto справа; ВДАВЛИВАНИЕ — inset-тени корпуса '
        '(бортик-блик + тень низа) и экрана («колодец»), бордеры, '
        'скругления; экран width: calc(40px * 96 / 17) — пропорция '
        'матрицы, image-rendering: pixelated; ТЕМЫ через --ws-lcd-bg/'
        'seg/ghost/glow: светлая — серо-зелёный ЖК #ccd6c5 + тёмные '
        'символы #232e38 + чёрный корпус #2a2f35 (КАК НА ФОТО), тёмная '
        '— «подсветка» #93e6a4 + glow (canvas shadow); календарь '
        '.ws-lcd-cal — absolute под окном, z-index 9460 (выше info-окон '
        'ws-* 9450), [hidden], светлая тема; (3) JS — модуль WsLcdClock: '
        'матрица COLS=96/ROWS=17 — ВЫБРАНО ВМЕСТО 10×60 ИЗ ЗАЯВКИ: '
        '«задел» на 2 строки требует 7+1+7=15 строк шрифта 5×7 (+запас), '
        '96 колонок = ровно 16 символов/строка (пейджерная ёмкость); '
        'шрифты FONT5 5×7 (полная кириллица 32 + латиница 26 + цифры + '
        'знаки) и FONTBIG 6×9 (цифры + двоеточие); компоновка КАК НА '
        'ФОТО: крупное ЧЧ:ММ (двоеточие мигает по чётности секунды), '
        'дата ДД.ММ.ГГГГ справа в верхней зоне (как число месяца у '
        '«PM»), полное название дня недели + секунды — нижняя строка '
        '(как WEDNESDAY), разделительный ряд 9; draw() — canvas в '
        'device-px (DPR), ПРИЗРАЧНЫЕ ячейки всей матрицы («выключенные» '
        'сегменты-призраки как на настоящем ЖК) + включённые (в тёмной '
        'теме свечение), цвета из CSS при каждой отрисовке (MutationObserver '
        'по data-theme — мгновенная перерисовка при смене темы); тик '
        '500 мс с детектом смены секунды; start/stop по хуку navigateTo '
        '(паттерн ws-totals: таймер живёт ТОЛЬКО на открытой странице); '
        'КАЛЕНДАРЬ: _renderCal (42 ячейки, соседние месяцы dim, выходные '
        'wknd тёплым, сегодня today), _calNav ‹ ›, _calToday «Сегодня», '
        '_calPick — клик по дате открывает ЭТОТ месяц в табеле (селекты '
        'месяца/года + WorkSchedule.onMonthChange + добавление '
        'недостающего года в селект), закрытие Esc/клик-вне/после '
        'выбора; «ЗАДЕЛ» ПО ЗАЯВКЕ: showMessage(line1, line2, ms) + '
        'событие window ws-lcd-message (detail: {line1, line2, ms}) — '
        'сообщения в ДВЕ строки по 16 символов, длинный текст '
        'листается «страницами» по 2 строки (PAGE_MS 3,5 с), '
        'авто-возврат к часам; (4) перенос prepare-kip8-transfer.py '
        '(дифф 763 строки = ровно контент Task 529: CSS 185 + HTML 17 '
        '+ хук 6 + JS 555) + task529-transfer-tests.py (rindex-урок '
        '527); тесты test-task529 ×39 НОВЫЙ (5 слоёв: SRC HTML — виджет '
        'в баре после заголовка, canvas 96×17, aria, календарь hidden; '
        'SRC CSS — display:none <1024px, flex+margin-left:auto ≥1024px, '
        'inset-тени вдавливания, calc(40px*96/17), pixelated, --ws-lcd-*, '
        'light-оверрайды, absolute/z-9460/[hidden]; SRC JS — COLS/ROWS, '
        'валидация ВСЕХ глифов (7 строк × 5 бит / 9 × 6 бит), _DAYS, хук '
        'start/stop, showMessage + слушатель, календарные методы; VM — '
        '«1» ряда 0 кол 3..4, дата col 37, «Ч» ЧЕТВЕРГ ряда 10, ряд 9 '
        'пуст, мигание двоеточия чёт/нечет, счётчик сегментов 200..600, '
        'две строки 1..7/9..15 + одна по центру ряда 5, _splitPages '
        '(перенос ≤16, сверхдлинное слово кусками, пустой → []), '
        'showMessage until, _tick возврат/листание, draw 96×17+фон и '
        'device-px 600×106, скрытый canvas не рисует, _calPick селекты '
        '+ onMonthChange; SW) + бамп SW v741→v742 / v538→v539; УРОК '
        'БАМПА (kip8test): слепая замена v741→v742 задела 144 гварда '
        '«следующей версии нет» (143 падения) — фикс task529-fix-guards.py '
        '(assertFalse/===−1 → v743, 30 ассертов присутствия не тронуты) '
        '+ вручную 3 гварда CACHE_VERSION-паттерна (task432/433/434); в '
        'kip8 перенос шёл в правильном порядке (гварды v539→v540 '
        'ПЕРВЫМИ) — 6800/0 с первого прогона; (5) верификация: браузер '
        'scripts/task529-browser-check.py 35/35 (моки auth/API как '
        'task486; тёмная DPR=2: окно справа 245,9px, canvas 452 device-px, '
        'матрица >2 цветов, кадр живой за 1,2 с (двоеточие/секунды), '
        'зоны верх 246/низ 144 сегментов; календарь: 42 ячейки, сегодня, '
        '‹›/«Сегодня», клик по дню 15 → селект месяца + сетка, Esc/вне; '
        'сообщение ПРОВЕРКА/СВЯЗИ в 2 строки + авто-возврат; уход со '
        'страницы — таймер стоп; светлая: фон #ccd6c5, календарь '
        '#fbf8f0; мобайл 390×844 и 1000×700 — окно СКРЫТО; 0 JS-ошибок) '
        '+ VLM по скриншотам download/kip8test-task529/ (тёмная ×2 — '
        '«чёткая точечная матрица из квадратных ячеек, сетка различима, '
        'пересечений нет»; календари — «идеально»; сообщение — «читается '
        'идеально»; светлая ×4 — «слипание»/«обрезка года» ОПРОВЕРГНУТЫ '
        'пиксельным анализом: 777 тёмных пикселей в правой зоне, 3 '
        'пустые колонцы между зонами — глиф «6» без правой стойки, не '
        'клип); DEPLOY-Task529 (ТОЛЬКО КЛИЕНТ: .gs, листы Google Sheets '
        'и деплой веб-приложения НЕ менялись); SW kipia-test-v742 / '
        'kipia-v539; все 4 репо ЗЕЛЁНЫЕ: kip8test 6800/0 → kip8test-desktop '
        '6785/0 (+39), kip8 6800/0 → kip8-desktop 6815/0 (+39; обе '
        'сборки success)')


def bump_prompt(path, old_head):
    s = read(path)
    assert s.count(old_head) == 1, 'версионная строка не найдена: ' + path
    s = s.replace(old_head,
                  '> **Версия документа:** 2026-10-15 (' + T529 +
                  '. Post-Task 528 — ')
    write(path, s)
    print('[ok] промт: ' + path)


def bump_arch(path, old_tests, new_tests, old_files, new_files,
              old_mirror, new_mirror):
    s = read(path)
    old = ('`tests/`, %s тестов, %s тест-файлов, `node tests/run-all.js`; '
           'зеркало CI: %s' % (old_tests, old_files, old_mirror))
    i = s.index(old)
    seg = s[i:i + 400]
    seg = seg.replace(old_tests, new_tests, 1).replace(old_files, new_files, 1)
    seg = seg.replace(old_mirror, new_mirror, 1)
    s = s[:i] + seg + s[i + 400:]
    assert new_tests in s and new_mirror in s, 'ARCHITECTURE не обновлён: ' + path
    write(path, s)
    print('[ok] ARCHITECTURE: %s → %s тестов, зеркало %s → %s' %
          (path, new_tests, old_mirror, new_mirror))


# kip8test
bump_prompt('/home/z/my-project/kip8test/Системный_промт_для_приложения_КИПиА.md',
            '> **Версия документа:** 2026-10-15 (post-Task 528 — ')
bump_arch('/home/z/my-project/kip8test/ARCHITECTURE.md',
          '6761', '6800', '225', '226',
          'kip8test-desktop 6746', 'kip8test-desktop 6785')

# kip8
bump_prompt('/home/z/my-project/kip8/Системный_промт_для_приложения_КИПиА.md',
            '> **Версия документа:** 2026-10-15 (post-Task 528 — ')
bump_arch('/home/z/my-project/kip8/ARCHITECTURE.md',
          '6761', '6800', '226', '227',
          'kip8-desktop 6776', 'kip8-desktop 6815')

# worklog-записи финализации
for repo, counts, push_line in [
    ('kip8test',
     'kip8test 6800/0 → kip8test-desktop 6785/0 (+39)',
     '- Пуш e0395abc → CI Tests 6800/0 + Pages + синк (bot 173d977c) → '
     'kip8test-desktop 6785/0 + Build success.\n'),
    ('kip8',
     'kip8 6800/0 → kip8-desktop 6815/0 (+39)',
     '- Пуш 300b950 → CI Tests 6800/0 + Pages + Build + синк (bot '
     '25f48fe7) → kip8-desktop 6815/0 + Build success (перенос '
     'prepare-kip8-transfer.py дифф 763 строки + task529-transfer-tests.py '
     'с rindex-уроком 527).\n')]:
    p = '/home/z/my-project/%s/worklog.md' % repo
    entry = ('\n---\nTask ID: 529 (финализация)\nAgent: main (Super Z)\n'
             'Task: Пуш/CI/синк/docs Task 529.\n\nWork Log:\n' + push_line +
             '- Docs: версионная строка промта post-Task 529 (демоция '
             'post-Task 528), ARCHITECTURE.md §2, эта запись.\n\n'
             'Stage Summary:\n- Task 529 ПОЛНОСТЬЮ ЗАКРЫТ: %s; обе '
             'сборки success. Правка ТОЛЬКО КЛИЕНТ — Apps Script, листы '
             'Google Sheets и деплой НЕ менялись: клиенты получат LCD-окно '
             'часов/календаря по обычному циклу SW (kipia-test-v742 / '
             'kipia-v539). Открытых хвостов НЕТ. СЛЕДУЮЩАЯ ЗАДАЧА: задачи '
             'пользователя.\n' % counts)
    with io.open(p, 'a', encoding='utf-8') as f:
        f.write(entry)
    print('[ok] worklog: ' + p)

print('OK — docs готовы к коммитам.')
