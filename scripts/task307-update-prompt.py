# -*- coding: utf-8 -*-
# Обновление системного промта kip8test до post-Task 307
with open('Системный_промт_для_приложения_КИПиА.md') as f:
    lines = f.readlines()

new3 = '''> **Версия документа:** 2026-09-03 (post-Task 307: ВКЛАДКА «СОТРУДНИКИ» УДАЛЕНА, КНОПКА «+ СОТРУДНИК» В ТУЛБАРЕ НАД ШАХМАТКОЙ. Заявка пользователя: «В разделе «График работы» убери вкладку сотрудники, а кнопку «Добавить сотрудника» перемести в бар над шахматкой к остальным кнопкам». КЛИЕНТ index.html — СЕРВЕР WorkSchedule.gs и схема листов НЕ менялись (редеплой Apps Script НЕ нужен, «Сформировать» заново НЕ нужно): 1) СТРАНИЦА «Сотрудники» #page-work-schedule-employees УДАЛЕНА ЦЕЛИКОМ: див + субнав-кнопка + хук navigateTo→initEmployeesPage + записи PAGE_PARENTS/PAGE_LABELS + 'work-schedule-employees' из _WORK_SCHEDULE_PAGES; JS-методы initEmployeesPage/loadEmployees/_renderEmployees удалены (карточки справочника не рендерятся); _loadEmployees ЖИВ — им пользуются loadGrid/инструктажи/отпуска; мёртвый CSS удалён (.ws-emp-card-header, .ws-emp-card .ws-tab-no/.ws-fio/.ws-meta/.ws-tag, .ws-employees-list, [data-theme=light] .ws-emp-card .ws-meta; .ws-trainings-list/.ws-tr-card остаются — инструктажи/отпуска). Справочник по-прежнему виден: строки шахматки, попап ячейки, селекты форм. 2) СУБНАВИГАЦИЯ: 3 полосы × 3 кнопки (Шахматка/Инструктажи/Отпуска) на всех страницах модуля. 3) КНОПКА «+ Сотрудник» (#wsEmpBtn, .ws-addemp-btn) В ТУЛБАРЕ ws-toolbar-main над шахматкой — после селектов месяца/года, ДО «Сформировать» (та видна с margin-left:auto справа): нейтральный стиль в духе селектов (var(--bg-tertiary)+border, font-weight 600), ЕДИНАЯ ВЫСОТА 34px (правило Task 269 расширено), title «Добавить сотрудника»; видимость в init() по _canEdit — КАК У «Сформировать» (Админ и пишущие роли видят, «ИТР8 pro» просмотр — нет); клик → ПРЕЖНИЙ bottom-sheet #wsEmpSheet (openEmployeeForm/submitEmployeeForm без изменений); НОВОЕ: .ws-toolbar-main flex-wrap: wrap — на мобильном ряд с 5 элементами аккуратно складывается в 2 строки (десктоп — nowrap в media); светлая тема кнопки — в тон селектов. 4) submitEmployeeForm после добавления вызывает loadGrid() (НОВАЯ СТРОКА сотрудника в шахматке) вместо удалённого loadEmployees(). ДЕПЛОЙ: ТОЛЬКО фронтенд — GitHub Pages + Ctrl+Shift+R ×1–2 (SW kipia-test-v545→v546, замена в sw.js + 9 тест-файлах); Apps Script НЕ трогать; листы НЕ трогать. Верификация: сьют 1433→1444 passed / 0 failed (НОВЫЕ 12 тестов Task 307 в tests/test-work-schedule.js: страница удалена, субнав 3×3, кнопка в тулбаре до «Сформировать» + hidden + openEmployeeForm, init() видимость, методы удалены (\\b-граница: _loadEmployees жив), submit → loadGrid, хуки/карты/ids отсутствуют, шторка жива, CSS .ws-addemp-btn + flex-wrap + мёртвые стили, SW v546; обновлены: субнав 4→3, активный пункт, страницы, PAGE_LABELS/PARENTS, крошки-симуляция, метки заголовков, Task 255 _posLabel в шахматке, Task 269 высота 34px); task299-mock 76/76; node --check OK; НОВЫЙ scripts/task307-browser-check.py — 22/22 (Playwright 8927, мок fetch: субнав 3 кнопки без «Сотрудники»; «+ Сотрудник» видна Админу в ws-toolbar-main ДО «Сформировать», 34px, title; клик → шторка «Новый сотрудник», поле «Таб. №» пусто и в фокусе; заполнение → «Добавить» → сервер получил addEmployee таб 042 «Сидоров», шторка закрылась, тост «Сотрудник добавлен», listEmployees перезапрошен, НОВАЯ СТРОКА «Сидоров» в шахматке; «Инструктажи»/«Отпуска» живы с 3-кноп. субнавом; navigateTo('work-schedule-employees') не падает; 375px — нет горизонтального скролла, ряд переносится; десктоп 1280px «ИТР8 pro» (просмотр) — кнопка И «Сформировать» скрыты, сетка жива, окошко календаря справа, ряд nowrap; 0 JS-ошибок; скриншоты task307-proof-mobile.png/sheet.png); регресс: task298 29/29, task303 20/20, task304 10/10, task305 20/20, task306 29/29; VLM ×2 (мобильный: кнопка «+ Сотрудник» в баре, субнав 3 кнопки, вкладки «Сотрудники» нет, без переполнения; шторка: заголовок, все 9 полей, «Добавить»/«Отмена», читаемо).)
'''

assert lines[2].startswith('> **Версия документа:**')
lines.insert(2, new3 if new3.endswith('\n') else new3 + '\n')
prev = [i for i, l in enumerate(lines[:30]) if l.startswith('> **Версия документа (предыдущая):**')]
while len(prev) > 12:
    del lines[prev[-1]]
    prev = [i for i, l in enumerate(lines[:30]) if l.startswith('> **Версия документа (предыдущая):**')]
print('Строка 3 вставлена; цепочка «предыдущих»:', len(prev))

src = ''.join(lines)

reps = [
    ('> **Текущая версия кэша:** `kipia-test-v540`', '> **Текущая версия кэша:** `kipia-test-v546`'),
    ('| `kip8test` | PWA | `kipia-test-v540` |', '| `kip8test` | PWA | `kipia-test-v546` |'),
    ('| `kip8` | PWA + APK | `kipia-v410` |', '| `kip8` | PWA + APK | `kipia-v411` |'),
    ('| Архитектура | SPA, 93 страницы (`page-*`), шевроны', '| Архитектура | SPA, 92 страницы (`page-*`), шевроны'),
    ('# 93 страницы (page-*), включая:', '# 92 страницы (page-*), включая:'),
]
for old, new in reps:
    n = src.count(old)
    assert n == 1, (old, n)
    src = src.replace(old, new)
print('Счётчики обновлены (5 замен)')

old274 = 'Субнавигация модуля** (.ws-subnav на всех 4 страницах: Шахматка/Сотрудники/Инструктажи/Отпуска'
new274 = 'Субнавигация модуля** (.ws-subnav — Task 307: вкладка «Сотрудники» УДАЛЕНА, 3 страницы: Шахматка/Инструктажи/Отпуска; исторически Task 274 делал 4: Шахматка/Сотрудники/Инструктажи/Отпуска'
assert old274 in src
src = src.replace(old274, new274)
print('Аннотация Task 274 добавлена')

entry = ('\n- **График работы — вкладка «Сотрудники» удалена, кнопка «+ Сотрудник» в тулбаре (Task 307)**: '
         'по заявке пользователя страница #page-work-schedule-employees удалена целиком (див/субнав/хук navigateTo/PAGE_PARENTS/PAGE_LABELS/_WORK_SCHEDULE_PAGES; JS initEmployeesPage+loadEmployees+_renderEmployees; мёртвый CSS .ws-emp-card*). '
         'Субнавигация — 3 полосы × 3 кнопки (Шахматка/Инструктажи/Отпуска). Кнопка «+ Сотрудник» (#wsEmpBtn .ws-addemp-btn) — в ws-toolbar-main над шахматкой (после селектов, до «Сформировать»), нейтральный стиль селектов, 34px, '
         'видимость по _canEdit как у «Сформировать», клик → прежний bottom-sheet #wsEmpSheet, submit → loadGrid() (новая строка в сетке). .ws-toolbar-main flex-wrap: wrap для мобильного. '
         'Сервер WorkSchedule.gs/листы НЕ менялись. Верификация: сьют 1444/0 (+12 Task 307 в test-work-schedule.js), task307-browser-check 22/22, регресс 298/303/304/305/306, VLM ×2. SW v545→v546. '
         'ДЕПЛОЙ: только GitHub Pages + Ctrl+Shift+R — см. scripts/DEPLOY-Task307-subnav-employees.md')
lines2 = src.split('\n')
insert_at = None
for i, l in enumerate(lines2):
    if l.startswith('- **Шахматка — визуальная разметка'):
        j = i + 1
        while j < len(lines2) and lines2[j].startswith('  '):
            j += 1
        insert_at = j
        break
assert insert_at is not None, 'точка вставки не найдена'
lines2.insert(insert_at, entry)
src = '\n'.join(lines2)
print('Запись Task 307 добавлена (после строки %d)' % insert_at)

with open('Системный_промт_для_приложения_КИПиА.md', 'w') as f:
    f.write(src)
print('Промт записан:', len(src), 'символов')
