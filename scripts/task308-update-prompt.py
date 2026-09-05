# -*- coding: utf-8 -*-
# Обновление системного промта kip8test до post-Task 308
with open('Системный_промт_для_приложения_КИПиА.md') as f:
    lines = f.readlines()

new3 = '''> **Версия документа:** 2026-09-04 (post-Task 308: ВКЛАДКИ «ИНСТРУКТАЖИ» И «ОТПУСКА» УДАЛЕНЫ, КНОПКА «+ ОТПУСК» В ТУЛБАРЕ НАД ШАХМАТКОЙ. Заявка пользователя: «Убери вкладки "Инструктажи" и "Отпуска", а кнопку "Добавить отпуск" перемести в бар над шахматкой к остальным кнопкам». КЛИЕНТ index.html — СЕРВЕР WorkSchedule.gs и схема листов НЕ менялись (редеплой Apps Script НЕ нужен, «Сформировать» заново НЕ нужно): 1) СТРАНИЦЫ «Инструктажи» #page-work-schedule-trainings и «Отпуска» #page-work-schedule-vacations УДАЛЕНЫ ЦЕЛИКОМ (дивы + внутренности wsTrainingsList/wsAddTrainingBar/wsVacYearSel/wsVacSummary/wsVacationsList/wsAddVacationBar + хуки navigateTo→initTrainingsPage/initVacationsPage + записи PAGE_PARENTS/PAGE_LABELS + обе страницы из _WORK_SCHEDULE_PAGES → ['work-schedule']); МОДУЛЬ ОДНОСТРАНИЧНЫЙ (только шахматка), СУБНАВИГАЦИЯ .ws-subnav УДАЛЕНА ЦЕЛИКОМ (все 3 полосы: после Task 307 их было 3×3 Шахматка/Инструктажи/Отпуска). 2) JS: страничные методы initTrainingsPage/loadTrainings/_renderTrainings/initVacationsPage/onVacYearChange/loadVacations/_renderVacations удалены; ЖИВЫ: _loadTrainings/_loadVacations (Promise.all в loadGrid — бейджи мероприятий И/ОБ/ПЗ/ПР/* и план «ОТ» в ячейках), _trainingCodeOf/_eventsAt/_statusMeta, openTrainingForm/closeTrainingForm/submitTrainingForm (вход — «+ Мероприятие…» в попапе ячейки, Task 303, шторка #wsTrSheet), openVacationForm/closeVacationForm/onVacEmployeeChange/onVacDatesChange/submitVacationForm (шторка #wsVacSheet), deleteTraining/deleteVacation/_doDeleteVacation (API-методы, серверные эндпоинты не менялись), хелперы _vacDays/_vacDaysInYear/_vacationAt/_fmtDateRu/_plural. НОВОЕ в _loadVacations: заполняет и _VACATIONS (сетка), и _VAC_PAGE + _vacYear = _year (шторка «+ Отпуск»: номер свободной части в onVacEmployeeChange и проверка пересечений в submitVacationForm; год плана = год шахматки — селект года удалён вместе со страницей). 3) КНОПКА «+ Отпуск» (#wsVacBtn, .ws-addvac-btn) В ТУЛБАРЕ ws-toolbar-main: ПОРЯДОК РЯДА селекты → «+ Сотрудник» (Task 307) → «+ Отпуск» → «Сформировать»; стиль — ОБЩЕЕ ПРАВИЛО с .ws-addemp-btn (нейтральный var(--bg-tertiary)+border, font-weight 600, :active opacity .85, светлая тема в тон селектов, ЕДИНАЯ ВЫСОТА 34px — правило Task 269 расширено); title «Добавить период отпуска»; видимость в init() по _canEdit КАК У «Сформировать»/«+ Сотрудник» (Админ и пишущие роли видят, «ИТР8 pro» просмотр — нет); клик → ПРЕЖНИЙ bottom-sheet #wsVacSheet (openVacationForm); 4) submitVacationForm после добавления вызывает loadGrid() (план «ОТ» в пустых ячейках подтягивается сразу, как новая строка у «+ Сотрудника» в Task 307) + тост «Отпуск добавлен. Нажмите «Сформировать» в шахматке — дни отметятся кодом «О»»; 5) МЁРТВЫЙ CSS удалён: .ws-trainings-list, .ws-tr-card* (+ .ws-tr-type* цветные плашки типов — цвета ПР/* остаются в справочнике «Коды_статусов», попап ячейки берёт их из _statusMeta), .ws-tr-title/.ws-tr-meta/.ws-tr-warn/.ws-tr-delete-btn, .ws-add-bar/.ws-add-btn (нижние плавающие бары), .ws-subnav/.ws-subnav-btn (+hover/active, светлая тема), .ws-vac-toolbar/.ws-vac-summary, .ws-vac-card*/.ws-vac-badge.p1/p2/p3 (светлая тема тоже); ЖИВЫ .ws-vac-form-info/.ws-vac-form-hint (строка дней и подсказка ст. 125 ТК РФ в шторке #wsVacSheet). ДЕПЛОЙ: ТОЛЬКО фронтенд — GitHub Pages + Ctrl+Shift+R ×1–2 (SW kipia-test-v546→v547, замена в sw.js + 9 тест-файлах); Apps Script НЕ трогать; листы НЕ трогать; удаление периодов отпусков из интерфейса временно недоступно (кнопки «Удалить» были на карточках удалённой страницы) — метод deleteVacation жив, удаление через Apps Script/лист; старые ссылки #work-schedule-trainings/-vacations открывают пустой экран без ошибки (navigateTo на несуществующую страницу — вернуться шевроном). Верификация: сьют 1444→1457 passed / 0 failed (+13 тестов Task 308 в tests/test-work-schedule.js; обновлены Task 249/267/269/274/307-блоки и тест-файлы test-task306.js/test-vacations-feedback.js/test-vacations-generate.js — \b-границы loadTrainings/loadVacations: _load*-загрузчики живы); node --check OK; НОВЫЙ scripts/task308-browser-check.py — 21/21 (Playwright 8929, мок fetch: субнавигации НЕТ (0 полос/0 кнопок), страниц trainings/vacations НЕТ; «+ Отпуск» видна Админу в ws-toolbar-main между «+ Сотрудник» и «Сформировать», 34px, title; клик → шторка «Новый отпуск», селект сотрудников заполнен, «Период: 14 кал. дн.»; заполнение (Петров, часть 1, 20.09–1.10) → сервер получил addVacation с правильным payload, шторка закрылась, тост «Отпуск добавлен», listVacations перезапрошен, ячейка Петрова 22.09 — ПЛАН «ОТ» с классом ws-vac-plan и тултипом «часть 1»; регресс Task 303: попап ячейки с «Мероприятия в этот день» + «+ Мероприятие…» → шторка с префиллом 017/10.09; navigateTo на удалённые страницы не падает; 375px — нет горизонтального скролла; десктоп 1280px «ИТР8 pro» — кнопка скрыта (паритет с «+ Сотрудник»/«Сформировать»), сетка жива, окошко календаря справа, ряд nowrap; 0 JS-ошибок; скриншоты task308-proof-mobile.png/sheet.png/toolbar.png); регресс: task298 29/29, task303 20/20, task304 10/10 (актуализирован: страница «Инструктажи» удалена, ⚠-предупреждения — в тосте «Сформировать»), task305 20/20, task306 29/29 (актуализирован: свотчи ПР #EF5350 и * #FFAB91 в попапе ячейки — цвета справочника живы), task307 22/22 (актуализирован: субнав 0, «+ Отпуск» в тулбаре); VLM ×2 (мобильный: кнопки «+ Сотрудник»/«+ Отпуск» в баре, полосы вкладок нет, без переполнения страницы; шторка: заголовок, все поля, «Период: 14 кал. дн.», подсказка ст. 125 ТК РФ, «Добавить»/«Отмена», читаемо).)
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
    ('> **Текущая версия кэша:** `kipia-test-v546`', '> **Текущая версия кэша:** `kipia-test-v547`'),
    ('| `kip8test` | PWA | `kipia-test-v546` |', '| `kip8test` | PWA | `kipia-test-v547` |'),
    ('| Архитектура | SPA, 92 страницы (`page-*`), шевроны', '| Архитектура | SPA, 90 страниц (`page-*`), шевроны'),
    ('# 92 страницы (page-*), включая:', '# 90 страниц (page-*), включая:'),
]
for old, new in reps:
    n = src.count(old)
    assert n == 1, (old, n)
    src = src.replace(old, new)
print('Счётчики обновлены (4 замены)')

# Аннотация Task 274 (субнавигация): Task 308 удалил полосу целиком
old274 = 'Субнавигация модуля** (.ws-subnav — Task 307: вкладка «Сотрудники» УДАЛЕНА, 3 страницы: Шахматка/Инструктажи/Отпуска; исторически Task 274 делал 4: Шахматка/Сотрудники/Инструктажи/Отпуска'
new274 = 'Субнавигация модуля** (.ws-subnav — Task 308: УДАЛЕНА ЦЕЛИКОМ, модуль одностраничный; Task 307 убрал «Сотрудников», 308 — «Инструктажи»/«Отпуска»; исторически Task 274 делал 4 полосы: Шахматка/Сотрудники/Инструктажи/Отпуска'
assert old274 in src
src = src.replace(old274, new274)
print('Аннотация Task 274 обновлена')

# Аннотация Task 274 (страница «Отпуска» удалена)
old274b = '4) **Страница «Отпуска»** (#page-work-schedule-vacations): селект года'
new274b = '4) **Страница «Отпуска»** (#page-work-schedule-vacations; Task 308: УДАЛЕНА — добавление периода кнопкой «+ Отпуск» в тулбаре над шахматкой, шторка #wsVacSheet жива; год плана = год шахматки): селект года'
assert old274b in src
src = src.replace(old274b, new274b)
print('Аннотация Task 274 (страница) обновлена')

# Аннотация к записи Task 307 (субнавигация 3×3 больше не существует)
old307 = 'Субнавигация — 3 полосы × 3 кнопки (Шахматка/Инструктажи/Отпуска). Кнопка «+ Сотрудник»'
new307 = 'Субнавигация — 3 полосы × 3 кнопки (Шахматка/Инструктажи/Отпуска; Task 308: полосы больше НЕТ — вкладки «Инструктажи»/«Отпуска» удалены, модуль одностраничный). Кнопка «+ Сотрудник»'
assert old307 in src
src = src.replace(old307, new307)
print('Аннотация Task 307 обновлена')

entry = ('\n- **График работы — вкладки «Инструктажи»/«Отпуска» удалены, кнопка «+ Отпуск» в тулбаре (Task 308)**: '
         'по заявке пользователя страницы #page-work-schedule-trainings и #page-work-schedule-vacations удалены целиком (дивы/внутренности/хуки navigateTo/PAGE_PARENTS/PAGE_LABELS/_WORK_SCHEDULE_PAGES → [\'work-schedule\']; JS initTrainingsPage+loadTrainings+_renderTrainings и initVacationsPage+onVacYearChange+loadVacations+_renderVacations; мёртвый CSS .ws-subnav*/.ws-tr-card*/.ws-tr-type*/.ws-add-bar/.ws-add-btn/.ws-vac-card*/.ws-vac-badge*/.ws-vac-toolbar/.ws-vac-summary). '
         'МОДУЛЬ ОДНОСТРАНИЧНЫЙ: субнавигации нет. Что живо: _loadTrainings/_loadVacations (бейджи и план «ОТ» в ячейках), шторка #wsTrSheet — «+ Мероприятие…» в попапе ячейки (Task 303), шторка #wsVacSheet — НОВАЯ кнопка «+ Отпуск» (#wsVacBtn .ws-addvac-btn) в ws-toolbar-main между «+ Сотрудник» (Task 307) и «Сформировать» (общий стиль .ws-addemp-btn: нейтральный, 34px, светлая тема; видимость по _canEdit в init()); '
         '_loadVacations заполняет и _VAC_PAGE/_vacYear (номер свободной части + проверка пересечений в шторке; год плана = год шахматки); submitVacationForm → loadGrid() (план «ОТ» в пустых ячейках) + тост про «Сформировать»; deleteTraining/deleteVacation живы как API-методы (сервер не менялся; интерфейсного удаления периодов временно нет — было на карточках удалённой страницы). '
         'Сервер WorkSchedule.gs/листы НЕ менялись. Верификация: сьют 1444→1457/0 (+13 Task 308), task308-browser-check 21/21, регресс 298/303/304/305/306/307 (304/306/307 актуализированы под новую реальность), VLM ×2. SW v546→v547. '
         'ДЕПЛОЙ: только GitHub Pages + Ctrl+Shift+R — см. scripts/DEPLOY-Task308-subnav-trainings-vacations.md')
lines2 = src.split('\n')
insert_at = None
for i, l in enumerate(lines2):
    if l.startswith('- **График работы — вкладка «Сотрудники» удалена'):
        j = i + 1
        while j < len(lines2) and lines2[j].startswith('  '):
            j += 1
        insert_at = j
        break
assert insert_at is not None, 'точка вставки (после записи Task 307) не найдена'
lines2.insert(insert_at, entry)
src = '\n'.join(lines2)
print('Запись Task 308 добавлена (после строки %d)' % insert_at)

with open('Системный_промт_для_приложения_КИПиА.md', 'w') as f:
    f.write(src)
print('Промт записан:', len(src), 'символов')
