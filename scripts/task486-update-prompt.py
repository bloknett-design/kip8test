#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 486: обновление системного промта kip8test (post-486, БЕЗ
# переноса — команды «перенеси в kip8» в заявке НЕ было; kip8
# остаётся @019ba8c v513/5940). kip8test: кэш v710, формат
# v710→v711, ожидание 5976/5940, факт 5976/194; строка 3 — только
# kip8test-сторона (kip8 упомянут как «ждёт команды переноса»).
import io
import sys

LINE3 = ('> **Версия документа:** 2026-10-08 (post-Task 486: ТАБЕЛЬ — '
         'ТИХОЕ ОБНОВЛЕНИЕ ДАННЫХ ПРИ ОТКРЫТИИ ПРИЛОЖЕНИЯ — заявка: '
         '«В разделе "Табель учёта рабочего времени", помимо ручного '
         'обновления, сделай тихое обновление данных при открытии '
         'приложения»; реализовано ТОЛЬКО в kip8test @c0d241ee, переноса '
         'в kip8 НЕ БЫЛО — команды в заявке не было, ждём; клиент-only, '
         'Apps Script не тронут). СУТЬ: WorkSchedule.silentRefresh() — '
         'те же 7 read-only экшенов, что «Обновить» и KipPreload'
         '._preloadWs; год/месяц — открытый вид или текущая дата; '
         'свежие данные пишутся в ОБА слоя локальной копии Task 314 '
         '(localStorage + KipDB, merge v1, лимит 12 видов; ДО задачи '
         'KipPreload грел только KipDB, а _restoreCachedView читает LS '
         'ПЕРВЫМ — устаревшая LS-копия побеждала свежий KipDB, оттого '
         'тихое обновление и было нужно); открытый раздел ТИХО '
         'перерисовывается (_restoreFromObj + _renderGrid + чип норм + '
         'штамп, сброс _YEAR_DATA/_VAC_YEARS как loadGrid(true)) — НО не '
         'посреди ручного «Обновить» (_refreshing) и не с открытым '
         'попапом ячейки (#wsCellPopup.active); _PENDING — слой правок '
         'ПОВЕРХ записей, НЕ затирается (семантика «Обновить»); '
         'fetched-вид != открытому — пишется только копия; ТРОТТЛИНГ '
         '5 минут по _silentTs (повторные _schedulePreload от фоновой '
         'проверки сессии не дёргают сеть; пустая копия после logout — '
         'обновление и внутри окна; _wipeLocalServerData сбрасывает '
         'метку); _silentBusy — защита от параллельного запуска; СБОЙ — '
         'ТИХИЙ (console.warn, без тоста/экрана). ЗАПУСК: KipAuth'
         '._schedulePreload (ВСЕ 5 путей старта: вход OTP, быстрый/'
         'медленный bootstrap, возврат связи, фоновая проверка сессии) '
         'тем же таймером 4 с, что KipPreload; права — '
         'canAccess(\'work-schedule\'). КООРДИНАЦИЯ: KipPreload'
         '._preloadWs пропускает свой ws-элемент при свежей метке/'
         'занятости (без дубля сети); тихий сбой silentRefresh (метка не '
         'ставилась) — _preloadWs остаётся ретраем-фолбэком (Task 477 '
         'жив). SW kipia-test-v709 → v710 (логика SW НЕ менялась; кэши '
         'не тронуты). ТЕСТЫ kip8test 5976/0 (+40): НОВЫЙ '
         'test-task486.js (SW/структура метода/хуки KipAuth/координация '
         '_preloadWs VM ×3/VM поведение silentRefresh ×10: живой раздел, '
         'merge чужих видов, троттлинг ×2 (свежая метка + пустая копия '
         'после logout), busy, попап, _refreshing, вид-несовпадение, '
         'тихий сбой, повтор после успеха/адаптации); бамп '
         'task486-bump-sw.py (ассерты v709→v710 ×585 / guards v710→v711 '
         '×144, 170 файлов); ОКНА ИСТОРИИ task486-windows.py: 483/484 '
         '1500→2100, 480 2600→3200, 481 2500/2600/3200→3200/3200/4100, '
         '478/479 3200→4100, 473 5100→5600, 472 5300→5900 + '
         'контекст-471 5900→6500 (ПОРЯДОК ПО УБЫВАНИЮ чисел — уроки '
         '482/484), 471 5900→6500, 461 8500→9100, якоря 474/472/471/461 '
         '→ 5300/5900/6500/9100 + каскады 475/481/482. АДАПТАЦИИ: '
         'WS_CLIENT 500000→600000 в 8 тестах (337/338/341/342/343/360/'
         '361/362 — модуль вырос на ~8.7КБ, onCellClick уехал за '
         'границу); test-task477 срез _schedulePreload 700→1700. '
         'Browser-check task486-browser-check.py 26/26 (порт 8998): A '
         'чистый профиль на дашборде — 7 экшенов сами, копия LS, БЕЗ '
         'тоста, KipPreload.ws не дублирует; B устаревшая копия — '
         'открытие из СВЕЖИХ данных; C раздел открыт ДО обновления — '
         'сетка ТИХО перерисовалась (ОТ→Д), без «Загрузка…»; D ручное '
         '«Обновить» с тостом как прежде; E троттлинг; 0 JS ×3; VLM ×1. '
         'УРОКИ ПРОГОНА: Playwright evaluate — стрелка с ОДНИМ '
         'объектом-аргументом ((day,tab) с одним объектом даёт '
         'day=объект/tab=undefined); ключ кэша в page.evaluate — БЕЗ '
         'префикса kip8test: (обёртка isolateLocalStorage добавит сама; '
         'в init_script — С префиксом, он до обёртки).')

CUR_T = '> **Версия документа:** 2026-10-07 (post-Task 485 ПЕРЕНОС:'
PREV_MARK = '> **Версия документа (предыдущая):**'


def update(path, cur_mark, tail):
    src = io.open(path, encoding='utf-8').read()
    if cur_mark not in src:
        print('ОШИБКА: не найдена строка версии в %s' % path)
        sys.exit(1)

    # (а) удалить самую старую «предыдущую» (ПОСЛЕДНЯЯ по позиции)
    if src.count(PREV_MARK) > 2:
        iprev = src.rindex(PREV_MARK)
        iprev_end = src.index('\n', iprev)
        src = src[:iprev] + src[iprev_end + 1:]

    i3 = src.index(cur_mark)
    i3end = src.index('\n', i3)
    old_line3 = src[i3:i3end]
    new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
    src = src[:i3] + LINE3 + tail + '\n' + new_prev + src[i3end:]
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: строка 3 обновлена (post-486)' % path)


# --- kip8test ---
PT = '/home/z/my-project/kip8test/Системный_промт_для_приложения_КИПиА.md'
update(PT, CUR_T,
       ' ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @c0d241ee, SW `kipia-test-v710` '
       '(guard v711), тесты 5976/0; kip8 @019ba8c, SW `kipia-v513` '
       '(guard v514), тесты 5940/0 — Task 486 в kip8 ОТСУТСТВУЕТ '
       '(перенос ПО КОМАНДЕ пользователя); десктопы — CI-автосинк. '
       'СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 487.')

src = io.open(PT, encoding='utf-8').read()
repsT = [
    ('> **Текущая версия кэша:** `kipia-test-v709`',
     '> **Текущая версия кэша:** `kipia-test-v710`'),
    ('Формат: `kipia-test-v709` → `kipia-test-v710` (для kip8test) или '
     '`kipia-v513` → `kipia-v514` (для kip8)',
     'Формат: `kipia-test-v710` → `kipia-test-v711` (для kip8test) или '
     '`kipia-v513` → `kipia-v514` (для kip8)'),
    ('# Ожидается: 5936 passed, 0 failed (kip8test; в kip8 — 5940 passed, 0 failed)',
     '# Ожидается: 5976 passed, 0 failed (kip8test; в kip8 — 5940 passed, 0 failed — Task 486 НЕ переносился)'),
    ('(`tests/`, 5936 тестов, 193 тест-файлов, `node tests/run-all.js`)',
     '(`tests/`, 5976 тестов, 194 тест-файла, `node tests/run-all.js`)'),
]
for old, new in repsT:
    assert src.count(old) == 1, 'T: %r ×%d' % (old[:60], src.count(old))
    src = src.replace(old, new)
io.open(PT, 'w', encoding='utf-8').write(src)
print('T: кэш v710, формат v710→v711, ожидание 5976/5940, факт 5976/194')

print('OK: промт kip8test обновлён (post-Task 486, без переноса)')
