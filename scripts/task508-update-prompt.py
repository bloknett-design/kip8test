#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 508 — обновление репо-документации kip8test:
  1) Системный_промт_для_приложения_КИПиА.md — строка версии
     post-Task 508 (полная замена строки 3);
  2) worklog.md — запись Task 508 (append в конец).
"""

import io

ROOT = '/home/z/my-project/kip8test/'

VERSION_LINE = (
    '> **Версия документа:** 2026-10-12 (post-Task 508 — «КАБЕЛЬНЫЙ ЖУРНАЛ»: '
    'АРХИВ ПРАВОК И УДАЛЕНИЙ — заявка: «Добавь сохранение в архив журнала кто '
    'последний вносил правки в каждый кабель, по столбцу name в таблице users '
    'файла KIP8_Access. И удалённый кабель так же должен сохраняться с пометкой '
    'как архивный по причине "Удалён", кто удалил, и не должен отображаться в '
    'распечатываемом или сохраняемом в PDF файле, а в excel отображается.» — '
    'ПЕРЕНОСА в kip8 НЕ БЫЛО: команды в заявке НЕТ (в kip8 ждёт Task 508 одним '
    'инкрементом kipia-v526→v527); КЛИЕНТ + СЕРВЕР). АРХИТЕКТУРА: лист журнала '
    'получает колонки P–T («Последний редактор»/«Дата правки»/«Архив» (причина '
    '«Удалён»)/«Кем удалён»/«Дата удаления») — создаются САМИ при первом '
    'обращении (_ensureArchiveColumns: insertColumnsAfter до 20 + заголовки '
    'P1:T1 только в ПУСТЫЕ ячейки — идемпотентно, init-скрипт не нужен; '
    'вызывается из _openSheet). СЕРВЕР scripts/CableJournal.gs (файл-эталон в '
    'репо — НОВЫЙ, ранее модуль жил только в Apps Script; ЭТО ПОЛНАЯ ЗАМЕНА '
    'файла в проекте по DEPLOY-Task508 + New version): SCHEMA +5 readOnly '
    'колонок; _userName(user) — name из users KIP8_Access, фолбэк email; '
    'appendRow/updateRow пишут P/Q; deleteRow БЕЗ sheet.deleteRow — R=«Удалён», '
    'S=кто, T=когда, ответ {ok, num, archived: true}; _rowToObject ставит '
    '_archived (колонка R непустая); list отдаёт ВСЕ строки (клиент решает), '
    'total=активные + archivedTotal; getFilters архивные пропускает '
    '(values[i][17]); аудиты прежних кодов с именами. КЛИЕНТ index.html '
    '(scripts/task508-apply.py, 18 патчей, 0 FAIL): шапка-комментарий модуля; '
    'состояние _archivedRows; load/_restoreCache/_idbRestore сплитят полный '
    'снапшот (_splitArchived/_rowArchived: флаг _archived | archived===true | '
    'строка «Архив» непустая) — активные в прежний конвейер (список/поиск/'
    'печать/PDF), архивные только в Excel; кэш persists ПОЛНЫЙ список (офлайн-'
    'Excel видит удалённые); НОВЫЕ методы: _excelModel (активные _rows УЖЕ '
    'поиск-отфильтрованы + архив kipSearchFilter тем же запросом, сортировка '
    '№ п/п, archived-счётчик), _cjArchiveCols (блок K–O: Статус/Кем удалён/'
    'Дата удаления/Последний редактор/Дата правки), _cjArchDate (ДД.ММ.ГГГГ); '
    '_saveCjXlsx — книга по _excelModel (фолбэк на модель печати); '
    '_buildCjWorkbook — блок «Архив» ТОЛЬКО при model.archived>0 (без архива '
    'книга ПОСЛОВНО Task 506): пары шапки len-динамические (было 3 жёстко), '
    'mergeCells динамически (7 с K1:O1 / 6 без), ширины K–O 12/16/12/16.5/12, '
    'даты архива «ДД.ММ.ГГГГ», self-замыкание; confirmDelete/submitDelete — '
    'честные тексты («Запись останется в архиве журнала с пометкой «Удалён»», '
    'тост «Запись удалена — в архиве журнала»). ПЕЧАТЬ/PDF НЕ тронуты '
    '(_printModel по this._rows — архив туда не попадает). sync-cables.py: '
    'архивные строки (колонка «Архив» непустая) в data/cables.json НЕ попадают '
    '(снимок активного журнала — счётчик кнопки входа). SW kipia-test-v729 → '
    'v730 (+комментарий ~160 симв. — ПЕРВЫЙ коммент был 4 строки/330 симв. и '
    'ВЫТЕСНЯЛ якоря истории: сокращён до 2 строк; окна истории '
    'task508-windows.py: 461 16300→17000 (@16317), 471 13700→14400 (@13755), '
    '483 9300→10500 (@9814), 500 2200→2800 (@2568 — ЗАМЕР по «// Task N:», '
    'мин-дистанция по подстроке «Task N» ловила ЧУЖУЮ ссылку в комментарии '
    '501!); КАСКАД task508-sync-literals.py: §9-475 (16300→17000, '
    '13700→14400), 481 (×2), 486 («\'i - 16300\'»→«\'i - 17000\'») — окно 472 '
    '13700 НЕ менялось; бамп task508-bump-sw.py: гарды v730→v731 ×134 ПОСЛЕ '
    'ассертов v729→v730 ×690, 190 файлов, test-task508 исключён; регистрация '
    'run-all ПОСЛЕ бампа). ТЕСТЫ 6472/0 (= 6445 + 27 test-task508.js: VM '
    'флаги/сплит (старый сервер — все активные), SRC проводка load/кэшей, VM '
    '_excelModel (сортировка/поиск-стаб kipSearchFilter через параметры '
    'Function(' + "'document', 'kipSearchFilter'" + '!), VM _buildCjWorkbook '
    '(блок «Архив»: K1:O1/7 объединений/«Удалён»/кем/дата ДД.ММ.ГГГГ/редактор/'
    'ширины/Print_Titles жив; БЕЗ архива — ПОСЛОВНО Task 506: 6 объединений, '
    'нет K1:O1/N-колонки), VM _cjArchDate (TZ-безопасно — локальная строка '
    'без Z!), SRC печать/PDF не знают архив, SRC тексты удаления, СЕРВЕР '
    'CableJournal.gs ×8 (SCHEMA P–T readOnly, _userName, appendRow P/Q, '
    'updateRow 16/17, deleteRow НЕ deleteRow-вызов — только упоминание в '
    'КОММЕНТАРИИ (КАМЕНЬ: assertFalse ловил пояснение «// Task 508: НЕ '
    'sheet.deleteRow(row)» — считать ВХОЖДЕНИЯ), _rowToObject/_archived, '
    'list archivedTotal, getFilters [17], _ensureArchiveColumns), sync-скип, '
    'SW v730; АДАПТАЦИЯ test-task505.js: литерал mergeCell ушёл из исходника '
    '(динамические объединения) — ассерт на colName-генерацию + mergesXml). '
    'Browser-check task508-browser-check.py 40/40 (порт 8994, мок Apps '
    'Script — 6 строк: 4 активные + 2 архивные «Удалён», порядок перемешан; '
    'getColumns 20 колонок; deleteRow СОСТОЯТЕЛЬНЫЙ — помечает архивом): '
    'список 4 карточки/4 группы; _printModel 4 (архив НЕ печатается); '
    '_excelModel 6/archived 2; диалог «записей: 4» + лист/предпросмотр 4 '
    'строки; PDF структурно; Excel openpyxl: 7 объединений K1:O1, K2–O2 '
    'подколонки, r4=архив (K4 «Удалён»/L4 кем/M4 12.10.2026), r7=архив №5, '
    'N3/O3 редактор активной, 2 архивных/6 строк, Print_Titles/A3 живы; '
    'e2e-удаление: submitDelete → тост «в архиве журнала», карточек 3, печать '
    '3, Excel 6/архив 3; светлая «записей: 3»; мобайл на весь экран; 0 JS ×3 '
    '(КАМЕНЬ: «Failed to load resource: 429» — lh3/drive-миниатюры KipPreload '
    'по IP-рейт-лимиту Google — СЕТЕВОЙ шум, НЕ JS-ошибка: фильтр в '
    'collect_errors; КАМЕНЬ: KipCableJournal — const-лексическая binding, '
    'window.KipCableJournal === undefined — в evaluate по имени). VLM ×3/3 '
    'task508-vlm-check.js (записей: 4 в подзаголовке, список после удаления '
    'жив, мобайл). DEPLOY-Task508-cable-journal-archive.md (СЕРВЕР: полная '
    'замена CableJournal.gs + New version; НЕТ init-скрипта — колонки '
    'самосоздаются; откат с возвратом листа). ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test — '
    'Task 508 выкачан, SW `kipia-test-v730` (guard v731), тесты 6472/0; kip8 '
    '— Task 507 (v526, 6449/0), Task 508 в kip8 ОТСУТСТВУЕТ (перенос по '
    'команде одним инкрементом kipia-v526→v527); сервер Apps Script общий — '
    'до шагов DEPLOY-Task508 оба приложения работают со «старым» сервером '
    '(клиент обратной совместим: строк с пометкой нет — поведение прежнее). '
    'СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 509.'
)

WORKLOG_ENTRY = '''
---
Task ID: 508
Agent: main (Super Z)
Task: Заявка (PAT от 24.08.2026, бессрочный): «Добавь сохранение в архив журнала кто последний вносил правки в каждый кабель, по столбцу name в таблице users файла KIP8_Access. И удалённый кабель так же должен сохраняться с пометкой как архивный по причине "Удалён", кто удалил, и не должен отображаться в распечатываемом или сохраняемом в PDF файле, а в excel отображается.» (kip8test; переноса в kip8 в заявке НЕТ — по команде).

Work Log:
- Старт: kip8test @c9587f8a (Task 507 зеркало, v729, 6445/0 — ОБА репо синхронны), PAT жив. Пользователь передал ИСХОДНИК CableJournal.gs (модуль Apps Script, в репо его НЕ было) — стал базой файла-эталона.
- СЕРВЕР scripts/CableJournal.gs — НОВЫЙ файл-эталон в репо (полная замена в Apps Script по DEPLOY): SCHEMA +5 readOnly колонок P–T; _ensureArchiveColumns (insertColumnsAfter до 20 колонок + заголовки P1:T1 ТОЛЬКО в пустые ячейки; вызов из _openSheet — идемпотентно, init-скрипт не нужен); _userName (name из users KIP8_Access, фолбэк email); appendRow/updateRow пишут «Последний редактор»/«Дата правки» (P/Q); deleteRow БЕЗ физического удаления — R=«Удалён», S=кем, T=когда, ответ archived: true; _rowToObject ставит _archived; list — все строки + total=активные + archivedTotal; getFilters пропускает архивные.
- КЛИЕНТ (scripts/task508-apply.py, 18 патчей, 0 FAIL; синтаксис — task508-syntax.py node --check): сплит полного списка в load/_restoreCache/_idbRestore (_splitArchived/_rowArchived — совместимо со старым сервером); кэш persists ПОЛНЫЙ снапшот (офлайн-Excel видит архив); _excelModel (поиск к архиву тем же запросом; сортировка № п/п; счётчик archived); _cjArchiveCols (K–O) + _cjArchDate (ДД.ММ.ГГГГ); _saveCjXlsx по _excelModel с фолбэком; _buildCjWorkbook — блок «Архив» при model.archived>0, пары len-динамические, mergeCells динамические (7/6), даты архива форматируются; confirmDelete/submitDelete — тексты про архив. Печать/PDF НЕ тронуты (архив в _rows не попадает).
- sync-cables.py: архивные строки (колонка «Архив» непустая) в data/cables.json не попадают (снимок АКТИВНОГО журнала; сами записи — в Google-листе и Excel-экспорте).
- sw.js v729→v730 + комментарий (~160 симв. — первый вариант 4 строки вытеснял якоря истории). Бамп task508-bump-sw.py: гарды v730→v731 ×134 ПОСЛЕ ассертов v729→v730 ×690 (190 файлов; test-task508 исключён); регистрация run-all ПОСЛЕ бампа.
- Окна истории task508-windows.py: 461 16300→17000 (@16317), 471 13700→14400 (@13755), 483 9300→10500 (@9814), 500 2200→2800 (@2568). КАМЕНЬ замера: мин-дистанция по подстроке «Task N» ловила ЧУЖУЮ ссылку в комментарии Task 501 — мерить по «// Task N:». КАСКАД task508-sync-literals.py: §9-475 (16300→17000, 13700→14400), 481 ×2, 486 («'i - 16300'»→«'i - 17000'»); окно 472 НЕ менялось (13700 жив).
- Тесты 6472/0 (= 6445 + 27 test-task508.js; АДАПТАЦИЯ test-task505.js — литерал «mergeCell ref="A1:A2"» ушёл из исходника в динамическую сборку: ассерт на colName-генерацию+mergesXml; УРОК assertEqual(CJ-файл): пояснение «// Task 508: НЕ sheet.deleteRow(row)» содержит вызов-строку — assertFalse падал; УРОК: _excelModel-поиск в VM — _rows УЖЕ отфильтрован приложением, в хосте передавать _rows:[]; УРОК TZ: _cjArchDate-тест на локальной строке без Z).
- Browser-check task508-browser-check.py 40/40 (порт 8994; мок: 6 строк = 4 активные + 2 архивные, порядок перемешан; getColumns 20 колонок; deleteRow СОСТОЯТЕЛЬНЫЙ — помечает архивную): список без архива (4 карточки); _printModel 4 / _excelModel 6 (архив меж активных по № п/п); диалог «записей: 4»; Excel openpyxl: K1:O1 (7 объединений), подколонки K2–O2, архивная r4: K4 «Удалён»/L4 кем/M4 «12.10.2026», r7 архив №5, N3/O3 редактор активной, 2 архивных из 6 строк, Print_Titles/A3 живы; e2e-удаление: тост «в архиве журнала», карточек 3, печать 3/Excel 6 (архивная добавлена моком); светлая/мобайл; 0 JS ×3 (429 lh3/drive — сетевой шум, фильтруется; KipCableJournal — const, НЕ window). VLM ×3/3 (записей: 4; список после удаления; мобайл-диалог).
- DEPLOY-Task508-cable-journal-archive.md (СЕРВЕР: полная замена CableJournal.gs + New version — один деплой на оба приложения; init НЕ нужен; откат — версиями Apps Script + снять пометку «Удалён» вручную). Коммиты: feat (index/sw/sync/tests/scripts) + docs (DEPLOY/worklog/промт).

Stage Summary:
- Task 508 ВЫКАЧАН в kip8test: SW kipia-test-v730 (guard v731), тесты 6472/0, browser-check 40/40, VLM ×3/3. Архив журнала: сервер CableJournal.gs фиксирует последнего редактора (name из users KIP8_Access) в P/Q каждой правки; удаление помечает строку архивной (R «Удалён»/S кем/T когда) БЕЗ физического удаления; клиент: список/печать/PDF — только активные, Excel — с блоком «Архив» (K–O); кэш — полный снапшот; sync-cables — снимок активного журнала. Колонки P–T создаются сами (DEPLOY: замена файла + New version).
- ПЕРЕНОС в kip8 — ПО КОМАНДЕ (одним инкрементом kipia-v526→v527; сервер уже общий после DEPLOY — в kip8 только клиент). СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 509.
'''

# 1) строка версии промта
PROMPT = ROOT + 'Системный_промт_для_приложения_КИПиА.md'
src = io.open(PROMPT, encoding='utf-8').read()
lines = src.split('\n')
idx = -1
for i, ln in enumerate(lines):
    if ln.startswith('> **Версия документа:**'):
        idx = i
        break
assert idx != -1, 'строка версии не найдена'
lines[idx] = VERSION_LINE
io.open(PROMPT, 'w', encoding='utf-8').write('\n'.join(lines))
print('промт: строка версии %d заменена (post-Task 508)' % (idx + 1))

# 2) worklog — append
WL = ROOT + 'worklog.md'
wl = io.open(WL, encoding='utf-8').read()
if 'Task ID: 508' in wl:
    print('worklog: запись Task 508 уже есть')
else:
    wl = wl.rstrip('\n') + '\n' + WORKLOG_ENTRY
    io.open(WL, 'w', encoding='utf-8').write(wl)
    print('worklog: запись Task 508 добавлена')
