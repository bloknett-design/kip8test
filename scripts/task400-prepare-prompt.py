# -*- coding: utf-8 -*-
"""Task 400 — подготовка «Системного промта» kip8test к переходу в новый чат.

Синхронизация post-Task 399: новая шапка-версия 2026-09-23 + сводка партии 384–399,
актуализация метрик (строки/страницы/тесты/SW/позиции модулей), файлы/эндпоинты Apps Script
(PPEInit.gs + CRUD СИЗ, Task 392), общее правило кнопок Task 397 в секции _applyRoleToUI.
Строгое якорное сопоставление: любой несовпавший якорь — ошибка, файл не пишется.
"""
import io, sys

PATH = '/home/z/my-project/kip8test/Системный_промт_для_приложения_КИПиА.md'

NEW_HEADER = (
    "> **Версия документа:** 2026-09-23 (post-Task 399: задачи 384–399 выполнены, проверены и "
    "В ПРОДЕ ОБОИХ репо; документация синхронизирована при подготовке к ПЕРЕХОДУ В НОВЫЙ ЧАТ. "
    "ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @95ad62d, SW `kipia-test-v627` (guard v628), тесты 3726/0 "
    "(112 файлов), index.html ~52.2 тыс. строк; боевой kip8 @51daa9e, SW `kipia-v475` (guard v476), "
    "тесты 3732/0 (113 файлов); десктопы kip8-desktop/kip8test-desktop — CI-автосинк при пуше "
    "index.html. Следующий номер задачи: 400 (в обоих репо). СВОДКА ПАРТИИ 384–399: [Task 384 — "
    "карточка сотрудника табеля — ЦЕНТР ПРАВКИ по отдельности: «Правка данных…» (updateEmployee, "
    "таб. № readonly), ✎/✕ отпусков (updateVacation/deleteVacation), «+ Мероприятие…» (✎/✕ Task 309 "
    "живы); серверные шаги задеплоены пользователем. Task 385 — страница «Работники»: полные карточки "
    "CRUD + кнопка в баре, карточка шахматки read-only, «работник» во всех строках, шторка «Легенда». "
    "Task 386 — «Обозначения»: кнопка + шторка двух видов (краткий 230px / развёрнутый 500px) + "
    "мобильная страница, «Добавить работника». Task 387 — панель до 500px, КАНОН справочника кодов "
    "(порядок + полные наименования, нормализация на клиенте; серверная часть опциональна — "
    "getStatusCodes + StatusCodesInit.gs). Task 388 — сплошные миниатюры с цветом кода, краткие "
    "обозначения, итоги в сменном/дневном виде, значок полного раскрытия в правом верхнем углу, "
    "вкладки «Работников» столбиком слева. Task 389 — прошедшие мероприятия = общий фон окна "
    "мероприятий; кнопка и численность работников (авто + штат) на «Общей» вкладке; сплошные фоны "
    "ярлыков/окон. Task 390 — «Общая» вкладка: строки «Работников по штату» и «на текущий момент» "
    "ПО КАТЕГОРИЯМ (мастера по должности «Мастер КИПиА» (_isMasterKipia), дневные/сменные по типу, "
    "мастер исключается из сменных/дневных), шапка выделена фоном, ярлыки примыкают к окну, тёмная "
    "тема — тёплые ярлыки. Task 391 — формулировки В СКОБКАХ с ведущим итогом-суммой, шрифт крупнее "
    "(14px/600), кнопка «Добавить работника» акцентная (синий тёмная / оранжевый светлая). Task 392 — "
    "раздел «СИЗ»: лист «СИЗ» таблицы табель_КИП_ИОС, секция СИЗ в карточке работника (правка/"
    "добавление/удаление), шторка с АВТО-датой окончания (выдача + срок, кламп месяца), серверные "
    "CRUD listPpe/addPpe/updatePpe/deletePpe + PPEInit.gs (задеплоено пользователем). Task 393 — "
    "карточка работника «Работников»: ЧЕТЫРЕ блока-окна (профиль с действиями / отпуска / "
    "мероприятия / СИЗ) + шрифт крупнее (15/14/12px). Task 394 — карточки: десктоп сеткой 2×2 на весь "
    "экран; мероприятия НА ВЕСЬ ГОД (listTrainings без month); окно мероприятий месяца — секции "
    "«Отпуска» (частично на два месяца — в ОБОИХ) и «СИЗ» (срок истекает в месяце). Task 395 — кнопка "
    "«Работники» тулбара табеля скрыта уровням null (нет доступа) и min (workschedule.view.min); "
    "блоки карточек фон светлее окна + рамки 2px с «выступающим вверх бордюрчиком»; десктоп — две "
    "колонки (СИЗ верхняя правая). Task 396 — ЗЕБРА чередующихся строк 4 блоков карточки, КОМПАКТНЫЕ "
    "кнопки 26px в ВЕРХНЕМ ПРАВОМ углу шапок блоков, оглавления блоков полосой .ws-whead с другим "
    "фоном (ФИО 16px/700). Task 397 — ОБЩЕЕ ПРАВИЛО ВСЕГО ПРИЛОЖЕНИЯ: кнопка раздела без доступа НЕ "
    "отображается — универсальный проход в _applyRoleToUI (любой элемент с onclick=navigateTo виден "
    "⟺ canAccess; крошки-исключение) + карта JS_NAV_TARGETS (8 JS-кнопок) + «Инженерные "
    "калькуляторы» нижнего бара по доступу + композит docs|library|kip-ios упрощён до docs + нижний "
    "бар скрыт целиком без видимых кнопок. Task 398 — фикс CSS: [hidden]{display:none!important} в "
    "начале <style> — семантика атрибута восстановлена ПО ВСЕМУ приложению (авторский "
    ".ws-refresh-btn{display:inline-flex} перебивал UA-стиль [hidden]{display:none}: кнопка "
    "«Работники» рендерилась при hidden=true, клик молча отсекался гейтом уровня). Task 399 — окно "
    "мероприятий табеля синхронизировано с сеткой по мастерам: уровень min (нет доступа к информации "
    "мастеров) НЕ видит в окне НИ мероприятий, НИ отпусков, НИ СИЗ мастеров (тот же _isMasterKipia, "
    "что у фильтра сетки; индекс таб. номеров по ПОЛНОМУ _EMPLOYEES; записи вне справочника "
    "показываются; счётчики/пустые состояния пересчитаны; режим выбранного дня — тоже; edit/view — "
    "окно полное)]. РАБОЧИЙ ЦИКЛ (не менять): заявка → kip8test (патч-скрипт scripts/taskNNN-patch.py "
    "+ SW-бамп taskNNN-bump-sw.py + тесты tests/test-taskNNN.js + браузер-чек taskNNN-browser-check.py "
    "на порту 89XX + DEPLOY-TaskNNN-*.md + worklog) → приёмка пользователем → перенос в kip8 "
    "(taskNNN-transfer: побайтовая проверка диффа, маппинг версий SW, браузер-чек БЕЗ префикса "
    "localStorage) → пуш (PAT в /home/z/.kip_pat, ПОСЛЕ пуша сброс URL) → CI "
    "(Tests/Sync-to-desktop/Pages). ОТКРЫТЫЕ СЕРВЕРНЫЕ ДЕЙСТВИЯ (Apps Script, вручную пользователем; "
    "клиент работает и без них): Task 375 — FlowmeterArchive.gs («окно 1 часа» анти-дублей); Task 376 "
    "— FlowmeterArchive.gs И Flowmeter.gs (ретраи архива + честный archive_write_failed); статус у "
    "пользователя. Задеплоены пользователем подтверждённо: Task 384 (Code.gs 2 case + WorkSchedule.gs "
    "updateEmployee/updateVacation), Task 392 (PPE CRUD + PPEInit.gs), Task 366 (дедуп архива). ПАТ: у "
    "пользователя (бессрочный; переотправлялся после отката песочницы — урок Task 396) — в новом чате "
    "запрашивать заново, ПЕРЕД записью в /home/z/.kip_pat проверять API /user (урок Task 365: "
    "ls-remote публичных репо всегда 200).)"
)

REPLACEMENTS = [
    # --- шапка-версия (строка 3): полная замена строки, начинающейся со старого префикса ---
    ("__HEADER__", None),  # маркер: обрабатывается отдельно по префиксу строки

    # --- метрики: технологический стек + структура проекта ---
    ("весь код в одном `index.html` (~49.7 тыс. строк, ~3.1 MB)",
     "весь код в одном `index.html` (~52.2 тыс. строк, ~3.2 MB)"),
    ("# Весь HTML + CSS + JS (single-file, ~49.7 тыс. строк, ~3.1 MB)",
     "# Весь HTML + CSS + JS (single-file, ~52.2 тыс. строк, ~3.2 MB)"),
    ("SPA, 93 страницы (`page-*`), шевроны ‹‹ для навигации",
     "SPA, 95 страниц (`page-*`), шевроны ‹‹ для навигации"),
    ("(`tests/`, 3288 тестов, 94 тест-файла, `node tests/run-all.js`)",
     "(`tests/`, 3726 тестов, 112 тест-файлов, `node tests/run-all.js`)"),
    ("# 93 страницы (page-*), включая:",
     "# 95 страниц (page-*), включая:"),

    # --- позиции модулей в структуре проекта ---
    ("Модуль KipAuth (Email+OTP + серверная карта прав, ~строка 32 108)",
     "Модуль KipAuth (Email+OTP + серверная карта прав, ~строка 33 033)"),
    ("Модуль KipCableJournal (редактирование кабелей, ~строка 35 116)",
     "Модуль KipCableJournal (редактирование кабелей, ~строка 36 115)"),
    ("Модуль KipFav (избранное, ~строка 33 758) — v2.0.0",
     "Модуль KipFav (избранное, ~строка 34 757) — v2.0.0"),
    ("Модуль FlowmeterData + FlowFav (расходомеры, ~строка 36 982)",
     "Модуль FlowmeterData + FlowFav (расходомеры, ~строка 37 981)"),
    ("Модуль WorkSchedule (график работы/табель, ~строка 40 242)",
     "Модуль WorkSchedule (график работы/табель, ~строка 41 247)"),

    # --- Service Worker пример версии ---
    ("`CACHE_VERSION` (например, `kipia-test-v611`) + `IMAGE_CACHE_VERSION`",
     "`CACHE_VERSION` (например, `kipia-test-v627`) + `IMAGE_CACHE_VERSION`"),

    # --- правила работы: ожидания тестов + формат бампа ---
    ("ожидается `3288 passed, 0 failed` (для kip8test; в kip8 — `3294 passed, 0 failed`)",
     "ожидается `3726 passed, 0 failed` (для kip8test; в kip8 — `3732 passed, 0 failed`)"),
    ("Формат: `kipia-test-v611` → `kipia-test-v612` (для kip8test) или `kipia-v459` → `kipia-v460` (для kip8)",
     "Формат: `kipia-test-v627` → `kipia-test-v628` (для kip8test) или `kipia-v475` → `kipia-v476` (для kip8)"),

    # --- инструкция для новых чатов ---
    ("# Ожидается: 3288 passed, 0 failed (kip8test; в kip8 — 3294 passed, 0 failed)",
     "# Ожидается: 3726 passed, 0 failed (kip8test; в kip8 — 3732 passed, 0 failed)"),
    ("❌ Заново читать весь `index.html` (~49.7 тыс. строк)",
     "❌ Заново читать весь `index.html` (~52.2 тыс. строк)"),

    # --- полезные команды: ожидание страниц ---
    ("# Подсчёт страниц в index.html\ngrep -c 'id=\"page-' index.html\n# ожидается: 93",
     "# Подсчёт страниц в index.html\ngrep -c 'id=\"page-' index.html\n# ожидается: 95"),

    # --- Apps Script: состав файлов (справочные копии scripts/*.gs) ---
    ("Код Apps Script (`Code.gs`, `Utils.gs`, `CableJournal.gs`, `Flowmeter.gs`, `FlowmeterArchive.gs`, "
     "`WorkSchedule.gs`, `ValidationRules.gs`, `VacationsInit.gs`/`VacationsDiagnose.gs`, `RoleMatrix.gs`, "
     "`RoleMatrixGate.gs`, `RoleMatrixInit.gs` (одноразовый init матрицы), `StatusCodesInit.gs` "
     "(одноразовая замена листа «Коды_статусов», Task 299))",
     "Код Apps Script (`Code.gs`, `Auth.gs`, `Sessions.gs`, `SessionsDevicePolicy.gs`, `Utils.gs`, "
     "`Flowmeter.gs`, `FlowmeterArchive.gs`, `FlowmeterInit.gs`, `WorkSchedule.gs`, `ValidationRules.gs`, "
     "`VacationsInit.gs`/`VacationsDiagnose.gs`, `RoleMatrix.gs`, `RoleMatrixGate.gs`, "
     "`RoleMatrixInit.gs` (одноразовый init матрицы), `RoleMatrixTask340Init.gs` (одноразовый init "
     "уровней view.min), `StatusCodesInit.gs` (одноразовая замена листа «Коды_статусов», Task 299), "
     "`TabNumbersFix.gs` (разовая починка таб_№), `PPEInit.gs` (одноразовый init листа «СИЗ», Task 392))"),

    # --- Apps Script: строка WEB_APP_URL ---
    ("(в `index.html`, ~строка 28 144, `KipAuth.WEB_APP_URL`",
     "(в `index.html`, ~строка 33 040, `KipAuth.WEB_APP_URL`"),

    # --- Apps Script: эндпоинты workSchedule (карточка-центр правки + СИЗ) ---
    ("| `workSchedule.*` | График работы: шахматка / сотрудники / инструктажи / отпуска "
     "(`listEntries`/`listEmployees`/`listTrainings`/`listVacations`/`generateMonth`/`addTraining`/`addVacation` "
     "/ … — Tasks 201-275; гейт `workschedule.view`/`workschedule.edit`). |",
     "| `workSchedule.*` | График работы/табель: шахматка / сотрудники / инструктажи / отпуска / СИЗ — "
     "`listEntries`/`listEmployees`/`listTrainings`/`listVacations`/`listPpe` (СИЗ, Task 392)/`generateMonth`/"
     "`getPatterns`/`getStatusCodes`/`addEmployee`/`updateEmployee` (Task 384)/`dismissEmployee`/"
     "`addTraining`/`deleteTraining`/`addVacation`/`updateVacation` (Task 384)/`deleteVacation`/"
     "`addPpe`/`updatePpe`/`deletePpe` (Task 392)/`setManualEntry`/`deleteEntry` — Tasks 201-399; гейт "
     "`workschedule.view`/`workschedule.view.min`/`workschedule.edit`. |"),

    # --- Защита _applyRoleToUI: ОБЩЕЕ ПРАВИЛО Task 397 ---
    ("4. **Админ-страницы** — двойная защита: CSS + JS-проверка при `navigateTo()`",
     "4. **Админ-страницы** — двойная защита: CSS + JS-проверка при `navigateTo()`\n"
     "5. **ОБЩЕЕ ПРАВИЛО (Task 397):** любой элемент с `onclick=\"navigateTo('…')\"` виден ⟺ "
     "`canAccess(page)` (хлебные крошки — исключение); карта `JS_NAV_TARGETS` покрывает 8 кнопок с "
     "`addEventListener`-навигацией; «Инженерные калькуляторы» нижнего бара — по `calc.view`; "
     "нижний бар скрыт целиком, если видимых кнопок нет; симметрично при смене роли\n"
     "6. **Семантика `hidden` (Task 398):** CSS-правило `[hidden]{display:none!important}` в начале "
     "`<style>` — атрибут `hidden` ВСЕГДА прячет элемент, даже если авторский CSS задаёт `display` "
     "(показ — только снятием атрибута)"),
]

def main():
    with io.open(PATH, encoding='utf-8') as f:
        text = f.read()

    errors = []
    # 1) шапка: заменить строку, начинающуюся со старого префикса версии
    lines = text.split('\n')
    header_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith('> **Версия документа:** 2026-09-18 (post-Task 382'):
            header_idx = i
            break
    if header_idx is None:
        errors.append('HEADER: строка "> **Версия документа:** 2026-09-18 (post-Task 382…" не найдена')
    else:
        lines[header_idx] = NEW_HEADER
        text = '\n'.join(lines)

    # 2) точечные замены
    for old, new in [(o, n) for (o, n) in REPLACEMENTS if o != '__HEADER__']:
        if old not in text:
            errors.append('ANCHOR NOT FOUND: %s' % old[:90].replace('\n', '\\n'))
            continue
        if text.count(old) != 1:
            errors.append('ANCHOR NOT UNIQUE (%d): %s' % (text.count(old), old[:90].replace('\n', '\\n')))
            continue
        text = text.replace(old, new)

    if errors:
        print('ОШИБКИ ЯКОРЕЙ (%d):' % len(errors))
        for e in errors:
            print('  - ' + e)
        sys.exit(1)

    with io.open(PATH, 'w', encoding='utf-8') as f:
        f.write(text)
    print('OK: Системный промт kip8test синхронизирован к post-Task 399 (версия 2026-09-23).')
    print('Замен: шапка (полная строка) + %d точечных.' % (len(REPLACEMENTS) - 1))

if __name__ == '__main__':
    main()
