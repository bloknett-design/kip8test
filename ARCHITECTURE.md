# ARCHITECTURE.md — архитектура приложения «КИПиА» (репозиторий kip8test)

> Извлечено из `Системный_промт_для_приложения_КИПиА.md` (Task 510, 2026-10-12, п.7 —
> «отдельный ARCHITECTURE.md» из оптимизации системных файлов). Обновлять при изменении
> архитектуры. Правила работы/регламенты — в системном промте; история задач — worklog.md
> (полные записи — неделя) и git (полная, тег `pre-task510`); деплой-инструкции недели —
> `DEPLOY-Task*.md`; одноразовые и старые файлы — только в git-истории.

## 1. Общая схема (репозитории, сервер, данные)

- **4 репозитория GitHub** (владелец `bloknett-design`): `kip8test` (тестовое PWA) и `kip8`
  (боевое PWA) — код приложений; `kip8test-desktop` / `kip8-desktop` — Electron-обёртки,
  тянут из PWA-репо полный набор (Task 517): `index.html`, десктоп-модули, `sw.js`,
  `scripts/*.gs` + `scripts/sync-*.py`, `tests/*.js` + `tests/README.md`, `data/*.json`,
  `images/*.png`, системный промт — зеркало держит фикстуры CI (`node tests/run-all.js`)
  актуальными; гварды окружения в `tests/test-task480.js` пропускают workflow/README-ассерты,
  которых в зеркале нет, в `tests/test-task518.js` — ассерт аудит-скрипта (6491/6525 тестов). Синк чистит `scripts/DEPLOY-*.md` (и артефакты
  Task 345: build.mjs/vite.config.mjs/bun.lock — kip8test-desktop). Триггеры
  `sync-to-desktop.yml` (Task 517: НЕ менять): kip8 — push в index.html/sw.js/
  scripts/*.gs/tests/десктоп-модули (авто); kip8test — push в index.html/десктоп-модули
  (полный набор протягивается этим же пушем) + workflow_dispatch.
- Разработка ведётся в kip8test; перенос в kip8 — копией `index.html` + env-патч
  (снятие `isolateLocalStorage()`, префиксы кэшей/путей) одним инкрементом `CACHE_VERSION`
  (детали регламента переноса — в системном промте, «Перенос в kip8»).
- **Сервер** — Google Apps Script Web App, физически НЕ в репозиториях (эталоны `.gs` —
  `scripts/`): auth Email+OTP, матрица прав KIP8_Access, кабельный журнал, расходомеры,
  график работы/табель, план-мероприятия.
- **Данные** — Google Sheets (мастер-источники) → Python `sync-*.py` → `data/*.json` →
  GitHub Pages (офлайн через SW). Двусторонние данные — через Apps Script (§6).
- Публикация: GitHub Pages — автоматически из `main`; APK — Bubblewrap (только kip8);
  десктоп — electron-builder по тегу `v*`.

## 2. Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Frontend | Vanilla JavaScript (ES6+), без фреймворков; весь код в одном `index.html` (~56.4 тыс. строк, ~3.2 MB) |
| Стили | CSS3 в `<style>` внутри `index.html`, CSS-переменные для тем (dark/light) |
| Архитектура | SPA, 95 страниц (`page-*`), шевроны ‹‹ для навигации |
| Офлайн-режим | Service Worker (`sw.js`) — NetworkFirst для `data/*.json` + App Shell + cache-busting |
| Auth | Apps Script Web App (Email+OTP, session token, heartbeat 5 мин) |
| Хранение | `localStorage` — сессионные ключи `kip8_*` без префикса (общие между kip8/kip8test); настройки с префиксом `kip8test:` (только в kip8test) |
| Тесты | Node.js + кастомный фреймворк (`tests/`, 7429 тестов, 244 тест-файла, `node tests/run-all.js` — раннер сам поднимает лимит кучи до 2560МБ (Task 542: суит ~2ГБ live); зеркало CI: kip8test-desktop 7369 → 7414 (прогноз Task 547: +45 тестов; 7282 + 87 из них — +68 Task 546 и +19 Task 545, доехавших одним синком: Task 545 index.html не менял) — синк при смене index.html/sw.js (гварды окружения Tasks 517+518)) |
| Сборка APK | Bubblewrap CLI + Android SDK + JDK 17 (только в `kip8`) |
| CI | GitHub Actions (1 CI + 7 sync workflows, cron ежедневно) |
| Деплой | GitHub Pages (автоматически при `git push` в `main`); для десктопа — через тег `v*` |
| Синхронизация данных | Python 3.12 + `openpyxl` + `requests`, Google Sheets xlsx-экспорт |
| Backend (auth/admin/cable/flowmeter) | Google Apps Script (JavaScript-диалект, Web App с `doGet`/`doPost`) |
| Десктоп | Electron + electron-builder + electron-updater |


## 3. Apps Script — серверная часть (не в репозитории)

Код Apps Script (`Code.gs`, `Auth.gs`, `Sessions.gs`, `SessionsDevicePolicy.gs`, `Utils.gs`, `Flowmeter.gs`, `FlowmeterArchive.gs`, `FlowmeterInit.gs`, `WorkSchedule.gs`, `ValidationRules.gs`, `VacationsInit.gs`/`VacationsDiagnose.gs`, `RoleMatrix.gs`, `RoleMatrixGate.gs`, `PlanEvents.gs` (Task 463: план-мероприятия — отметки/архив), `PlanEventsInit.gs` (одноразовый init листа «Архив» файла Мероприятия_КИП_ИОС), `RoleMatrixInit.gs` (одноразовый init матрицы), `RoleMatrixTask340Init.gs` (одноразовый init уровней view.min), `StatusCodesInit.gs` (одноразовая замена листа «Коды_статусов», Task 299), `TabNumbersFix.gs` (разовая починка таб_№), `PPEInit.gs` (одноразовый init листа «СИЗ», Task 392), `PhonebookArchive.gs` (Task 537: архив пользовательских данных телефонного справочника — избранное/примечания, email-bound, файл «Телефонный справочник — Архив пользователей» создаётся phonebookArchiveInit() или лениво), `MinesweeperArchive.gs` (Task 546: архив счёта «Сапёра» по email — НОВАЯ СТРАНИЦА «Сапёр» в самом файле KIP8_Access, создаётся minesweeperArchiveInit() или лениво; append-only журнал партий, чтение только своих записей)) **физически не находится** в репозиториях. Он редактируется напрямую в Google Apps Script Web App (script.google.com). В репозиториях хранится только URL `WEB_APP_URL` (в `index.html`, ~строка 33 040, `KipAuth.WEB_APP_URL` — с Task 284 указывает на развёртывание AKfycbyt…/exec, которым управляет пользователь), а серверные `.gs` файлы — в `scripts/` как справочные копии.

**Серверные эндпоинты (общий список):**

| Действие | Описание |
|----------|----------|
| `sendOTP` | Отправка 6-значного OTP-кода на email. Создаёт pending-запись с TTL ~10 мин. |
| `verifyOTP` | Проверка OTP → при успехе создаёт сессию (token, userId, expiresAt). |
| `getCurrentUser` | По token возвращает `{userId, email, role}` — для bootstrap и heartbeat. |
| `heartbeat` | Продление сессии (сброс `expiresAt`). Вызывается каждые 5 минут. |
| `logout` | Инвалидация token. |
| `getMyAccess` | Карта прав текущего пользователя по матрице KIP8_Access (Task 295, rmGetMyAccess; `no_session` по конвенции doPost). |
| `cableJournal.list` / `.getColumns` / `.getFilters` / `.appendRow` | CRUD кабельного журнала. |
| `adminListUsers` / `adminCreateUser` / `adminUpdateRole` / `adminResetLogin` / `adminListSessions` / `adminListLogs` | Админ-функции (гейт `admin.panel` — только Админ). |
| `flowmeter.list` / `.updateReading` / `.updatePeriodReading` / `.archive` / `.setComment` / `.getValidationRules` / `.getRecentAllMeters` | Просмотр / ввод показаний (за сутки и за период — Task 286) / архив / комментарии / правила валидации расходомеров. |
| `workSchedule.*` | График работы/табель: шахматка / сотрудники / инструктажи / отпуска / СИЗ — `listEntries`/`listEmployees`/`listTrainings`/`listVacations`/`listPpe` (СИЗ, Task 392)/`generateMonth`/`getPatterns`/`getStatusCodes`/`addEmployee`/`updateEmployee` (Task 384)/`dismissEmployee`/`addTraining`/`deleteTraining`/`addVacation`/`updateVacation` (Task 384)/`deleteVacation`/`addPpe`/`updatePpe`/`deletePpe` (Task 392)/`setManualEntry`/`deleteEntry` — Tasks 201-399; гейт `workschedule.view`/`workschedule.view.min`/`workschedule.edit`. |
| `planEvents.list` / `planEvents.mark` / `planEvents.update` / `planEvents.unmark` | «Плановые мероприятия»: отметки года / отметка выполнения (идемпотентно, Task 463) / правка даты / снятие отметки (Task 464; архив файла Мероприятия_КИП_ИОС, лист «Архив»). |
| `phonebook.*` (Task 537) | Телефонный справочник — архив пользовательских данных: `getMyData` (свои избранные + примечания), `setFavorite` (добавить/убрать, идемпотентно), `setNote` (создать/обновить/удалить). Файл «Телефонный справочник — Архив пользователей» (листы «Избранное»/«Примечания»/«Служебное», создаётся `phonebookArchiveInit()` или лениво), каждая строка привязана к email — видно/меняется только своё; мягкое удаление (история сохраняется); гейт `secret.view` (сервер не менялся; Task 543: КЛИЕНТСКИЙ доступ к разделу — `li
| `minesweeper.*` (Task 546) | Сапёр — архив счёта пользователей по email: `recordResult` (зафиксировать партию: won/time/diff/поле/мины — валидация, отклонения не обрезаются), `getMyArchive` (свои последние 50 партий + stats/best по сложностям). Лист «Сапёр» В ФАЙЛЕ KIP8_Access (новая страница по заявке; строки 1–2 титул/описание, 3 — заголовки: id/дата/email/имя/результат/сложность/поле/время_сек/мины), email — из сессии (подделка чужого счёта невозможна), append-only; гейт `secret.view` (как у страницы «Сапёр» на клиенте); клиент — fire-and-forget + тихая деградация (нет сессии/модуля/сети — локальный счёт Task 193), блок «Архив партий» на странице. |brary.view`, серверный гейт архива остался `secret.view` — у ролей с library.view без secret.view страница работает, архив-синк уходит в локальный режим); расширение архива — новыми листами (версия структуры в «Служебном»). |


## 4. Структура PWA-репозитория

| Путь | Назначение |
|------|-----------|
| `index.html` | Весь код приложения (SPA, страницы `page-*`) |
| `sw.js` | Service Worker (кэш-версии `kipia[-test]-v*`, images) |
| `manifest.json` | PWA-манифест (пути `/kip8/` или `/kip8test/`) |
| `data/*.json` | Снимки Google Sheets для офлайна |
| `images/` | Ассеты приложения (иконки, логотип, схемы — НЕ удалять) |
| `tests/` | Node-тесты (`node tests/run-all.js`) |
| `scripts/*.gs` | Эталоны серверного кода Apps Script |
| `scripts/sync-*.py` | Выгрузка Google Sheets → data/*.json |
| `DEPLOY-Task*.md` | Деплой-инструкции текущей недели (старше — в git) |
| `.github/workflows/` | CI + 7 sync-воркфлоу (cron) |
| `Системный_промт_…КИПиА.md` | Системный промт (правила, регламенты, сводки) |
| `worklog.md` | Журнал задач (ротация: неделя + сводка, Task 510) |
| `ARCHITECTURE.md` | Этот файл |

## 5. Ключевые архитектурные решения

### Service Worker (`sw.js`)
- `CACHE_VERSION` (например, `kipia-test-v655`) + `IMAGE_CACHE_VERSION`
- Стратегия: **NetworkFirst** для `data/*.json` (с cache-busting через `?_t=timestamp`), CacheFirst для App Shell
- При изменении любых файлов приложения — **обязательно** инкрементировать `CACHE_VERSION`, иначе пользователи увидят старую версию

### Навигация — шевроны ‹‹
- 1 тап по шеврону = назад (`goBack()`)
- 2 тапа в течение 0.5 с = на главную (`navigateTo('dashboard')`)

### Изоляция localStorage (только в kip8test)
- Обёртка `isolateLocalStorage()` применяет префикс `kip8test:` ко всем ключам, **кроме** `kip8_*` и `kip8_flow_*` (они общие с kip8 для совместного входа)
- При переносе из kip8test в kip8 этот блок **УДАЛЯЕТСЯ** (см. `scripts/prepare-kip8-transfer.py`)
- В kip8, kip8-desktop, kip8test-desktop этого блока **НЕТ** (десктопы тянут `index.html` из PWA-репозиториев)

### Кэширование данных (ВАЖНО!)
- Все `data/*.json` кэшируются SW. При их изменении — инкрементировать `CACHE_VERSION`
- Динамические данные (кабельный журнал, расходомеры) — через Apps Script, без кэширования SW

### Кросс-ссылки между разделами (фильтр по № проекта)
- Кнопка «Проекты» в карточках открывает `projects-prod?project=N` — фильтрует список по номеру проекта
- Реализовано через URL-параметры + `URLSearchParams`

### Цветовая палитра КИП ИОС
- Приборы: `#b85a7a` (медно-розовый)
- Блокировки: `#b85a7a` (та же палитра)
- Клапана: `#4a8a8c` (бирюзовый)
- Регуляторы: `#7e5ab8` (аметистовый)
- Проекты: `#b08048` (медно-янтарный)
- Кабельный журнал: `#8aa070` (оливково-зелёный)
- План корпуса 114: `#7896b0` (сине-стальной)

### Тёмная и светлая темы
- CSS-переменные в `:root` + `:root[data-theme="dark"]`
- Тема хранится в `kip8test:theme` (в kip8 — без префикса, `theme`)
- Переключатель в sidebar внизу

### Sidebar — структура
- Группы: «КИП и А» (калькуляторы), «Электротехника», «Геометрия», «Экзаменационные билеты», «Библиотека КИП и А», «КИП ИОС», «Расходомеры», «Админ-панель» (только Админ), «Что нового»
- Атрибут `data-requires="library"` / `"kip-ios"` на группах — для группового скрытия при отсутствии доступа
- Внизу: email + роль + кнопка «Выйти» (или «Гость» + «Войти в аккаунт»)


## 6. Синхронизация данных

### Общая схема

```
Google Sheets (xlsx-экспорт по публичной ссылке)
        ↓ Python sync-*.py (cron в GitHub Actions)
data/*.json (в репозитории, кэшируются SW)
        ↓
PWA читает data/*.json при загрузке (NetworkFirst)
```

Телефонный справочник (Task 542): источник — Google-таблица
пользователя (плоские 3 колонки: Должность | Ф.И.О. | № тел.) —
https://docs.google.com/spreadsheets/d/1rFbDn-jNRSoELTnsiaKjNvatSqIhVvbS/edit
(ссылка обновлена Task 545),
`scripts/sync-phonebook.py` пересобирает `data/phonebook.json`;
правила разбора — в docstring скрипта (A-only строка = заголовок:
«ООО…» → организация, иначе подразделение; DEFAULT_HEADER =
ООО ПО «ТОКЕМ» стабилизирует ID избранного; подгрупп = null).
Доступ (Task 543): раздел не секретный — право `library.view`
(«Билеты» + «Библиотека КИП и А»), кнопка в «Документации».
```

### Расписание cron (kip8 + kip8test)

kip8 работает на 2 ч раньше kip8test, чтобы не дублировать запросы к Google Sheets:

| Workflow | kip8 (UTC / Нск) | kip8test (UTC / Нск) |
|----------|------|------|
| sync-cables | 01:00 / 08:00 | 03:00 / 10:00 |
| sync-lockouts | 01:10 / 08:10 | 03:10 / 10:10 |
| sync-valves | 01:20 / 08:20 | 03:20 / 10:20 |
| sync-regulators | 01:30 / 08:30 | 03:30 / 10:30 |
| sync-projects | 01:40 / 08:40 | 03:40 / 10:40 |
| sync-phonebook | 01:50 / 08:50 | 03:50 / 10:50 |
| sync-devices | 04:00 / 11:00 | 06:00 / 13:00 |
| update-exam-tickets | 04:10 / 11:10 | 06:10 / 13:10 |

### Двусторонняя синхронизация «клиент ↔ Apps Script ↔ Google Sheets» (паттерн)

Используется для кабельного журнала и расходомеров хозрасчётных:

1. **Google Sheets** — таблица с данными (доступ «у кого есть ссылка» для чтения)
2. **Apps Script — X.gs** — серверный модуль: `list()`, `update*()`, `_requireRead()`, `_requireEdit()`, `audit()`
3. **Apps Script — Code.gs** — роутинг в `doPost()` по action (`x.list`, `x.update*`)
4. **scripts/X.gs** — справочная копия в репозитории (НЕ исполняется)
5. **scripts/sync-x.py** — Python-скрипт для офлайн-fallback (экспорт xlsx → JSON)
6. **data/x.json** — статический fallback для PWA
7. **XData модуль в `index.html`** — клиент: `init()`, `load()`, `renderList()`, `openDetail()`, `submitInput()`, `_canEdit()`

**Серверные готчи:**

- **Даты:** Apps Script получает Date objects через `new Date(year, month-1, day)` (месяцы 0-indexed!). Читать даты нужно через `_sheetToClientDate()` — преобразует Date в M/D/YYYY format. В Excel-форматах используется `datetime_to_serial()` — конвертация Excel-дат в числовые значения.
- **Content-Type:** `text/plain;charset=utf-8` — НЕ `application/json` (см. раздел auth)
- **Авторизация:** `_requireRead()` / `_requireEdit()` — проверка роли по `READ_ROLES` / `INPUT_ROLES`. Методы возвращают `{ok, ...}` — **без throw**.
- **Аудит:** `Utils.audit(user.email, 'X_ACTION', '', '', message)` для каждой операции записи.
- **Оптимистичное обновление UI:** клиент обновляет UI сразу, потом ждёт ответа сервера. При ошибке — откат.

### Чеклист: добавление нового раздела с двусторонней синхронизацией

1. Google Sheets: создать лист, раздать доступ «у кого есть ссылка»
2. Apps Script — X.gs: скопировать шаблон из `Flowmeter.gs`, заменить `SPREADSHEET_ID`, `SHEET_NAME`, `READ_ROLES`, `INPUT_ROLES`, реализовать `list()` / `update*()`. Даты — всегда Date objects.
3. Apps Script — Code.gs: добавить маршруты в `doPost()`
4. Apps Script — Deploy: создать новую версию веб-приложения
5. scripts/X.gs: сохранить справочную копию
6. scripts/sync-x.py: создать Python-скрипт
7. data/x.json: запустить sync, проверить результат
8. index.html — XData: реализовать клиентский модуль
9. index.html — навигация: добавить `XData.init()` в обработчик перехода на страницу
10. sw.js: добавить `'./data/x.json'` в `ASSETS`, инкрементировать `CACHE_VERSION`

