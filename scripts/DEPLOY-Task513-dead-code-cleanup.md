# DEPLOY — Task 513 (УБОРКА МЁРТВОГО КОДА) + Task 514 (ПРОВЕРКА ФАКТИЧЕСКОГО Apps Script)

> **Заявки:** «Проверь код приложения на наличие ошибок и мёртвого кода» (Task 512, аудит),
> «Подтверждаю уборку» (Task 513), выгрузка всех .gs из Apps Script в docx (Task 514).
> **Task 514:** пользователь передал ВСЕ файлы фактического Apps Script (17 .gs, 12 818 строк)
> — сверены с git-эталонами. План замены УТОЧНЁН: 7 файлов → **6 замен + удаление Admin.gs**.
> **Характер изменений:** удаления мёртвого кода (513) + подтягивание пропущенных обновлений
> (Task 376, Task 340, Admin-блок). Деплой стал чуть больше, чем предполагал Task 513, — но
> всё равно безопасен: каждый файл сверен с фактическим состоянием.

## Фактическое состояние Apps Script (тест kip8test) — итог сверки Task 514

**Совпадают с эталоном байт-в-байт (11) — НЕ трогать:** Code.gs, Auth.gs, Sessions.gs,
FlowmeterArchive.gs, ValidationRules.gs, WorkSchedule.gs, VacationsInit.gs, RoleMatrix.gs,
SessionsDevicePolicy.gs, PPEInit.gs, PlanEvents.gs.

**Отсутствуют в Apps Script (8, одноразовые init/diagnose — норма, НЕ разворачивать):**
FlowmeterInit.gs, StatusCodesInit.gs, PlanEventsInit.gs, PlanWorksInit.gs, TabNumbersFix.gs,
VacationsDiagnose.gs, RoleMatrixTask340Init.gs, RoleMatrixTask462Init.gs.

**Дрейф (нужна замена):**

| Файл в Apps Script | Фактическое состояние | Чего не хватает |
|---|---|---|
| `Utils.gs` | 775 строк = pre-513, НО без Admin-блока в конце | встроенного Admin (в репо с Task 347 живёт в Utils.gs) |
| `Admin.gs` — ЛИШНИЙ файл | 337 строк = Admin-блок Utils pre-513 | в репо файла НЕТ: контент встроен в Utils.gs |
| `Flowmeter.gs` | точно коммит Task 359 (2026-09-10) | Task 376: честный `archive_write_failed` (показания не теряются) |
| `RoleMatrixGate.gs` | точно коммит Task 319 (2026-09-05) | Task 340: право `workschedule.view.min` — ФУНКЦИОНАЛЬНЫЙ дрейф |
| `RoleMatrixInit.gs` | pre-513 + пользовательские правки опечаток | опечатки (создаёт/хелпер) приняты в репо в Task 514 |
| `CableJournal.gs` | = Task 508, минус 2 пустые строки | только косметика — можно не трогать |

## ⚠️ Триггеры: фактическая безопасность (уточнение Task 514)

Опасная копия `setupTriggers` (удаляет ВСЕ триггеры) в фактическом проекте живёт в
**Admin.gs**, а НЕ в Utils.gs (Utils.gs пользователя её не содержит — репо-эталон
расходился с реальностью). Алфавитный порядок загрузки GAS: **Admin.gs < Code.gs** —
позже загружаемый **Code.gs перекрывает** опасную копию: запуск `setupTriggers()` из
редактора сейчас идёт по КАНОНИЧЕСКОЙ ветке (фильтр только hourlyCleanup).
**Runtime сейчас безопасен, но мина остаётся в Admin.gs.**
Замена Utils.gs (Admin-блок встроен, без setupTriggers) + удаление Admin.gs убирает
мину полностью: единственный `setupTriggers` — канон в Code.gs.

## Уточнённый план замены

Заменить содержимое файлов в редакторе Apps Script на версии из репозитория `kip8test`
(`scripts/*.gs`, HEAD = Task 513 + опечатки Task 514):

| # | Файл | Действие | Что изменится |
|---|------|----------|---------------|
| 1 | `Utils.gs` | ЗАМЕНИТЬ | к существующему коду НЕ меняется; в конце файла добавится Admin-блок (339 строк; опасного setupTriggers в версии НЕТ) |
| 2 | `Admin.gs` | **УДАЛИТЬ ФАЙЛ** (правый клик → Delete) | контент теперь в Utils.gs; его `setupTriggers` — опасный дубликат |
| 3 | `Flowmeter.gs` | ЗАМЕНИТЬ | Task 376: при неудаче записи архива — честный `archive_write_failed`, строка ОСТАЁТСЯ в outbox клиента; плюс уборка 513 (−96 строк мёртвого кода) |
| 4 | `RoleMatrixGate.gs` | ЗАМЕНИТЬ | Task 340: право `workschedule.view.min` (ограниченный просмотр графика) — сейчас шлюз это право не распознаёт |
| 5 | `RoleMatrix.gs` | ЗАМЕНИТЬ | уборка 513: −`roleMatrixHasPermission`, −`roleMatrixGetAccessForEmail` (superseded RoleMatrixGate) |
| 6 | `RoleMatrixInit.gs` | ЗАМЕНИТЬ | уборка 513: −`_colLetter`; правки опечаток пользователя (создаёт/хелпер) в версии УЧТЕНЫ |
| 7 | `SessionsDevicePolicy.gs` | ЗАМЕНИТЬ | уборка 513: −`sdpDebug` |
| — | `CableJournal.gs` | по желанию | идентичен репо, кроме 2 пустых строк |
| — | `FlowmeterInit.gs`, `StatusCodesInit.gs` | ПРОПУСТИТЬ | в Apps Script отсутствуют (одноразовые) |

`Code.gs` НЕ трогать — канон `setupTriggers` жив там.

## Шаги

1. Открыть проект Apps Script (тестовый — kip8test).
2. Файлы 1, 3–7: открыть → выделить всё → вставить версию из репозитория → Ctrl+S.
3. Файл 2: удалить `Admin.gs` целиком (правый клик по файлу → Delete).
4. Сверка: `setupTriggers` в списке функций ОДИН раз (Code.gs); исчезли `sdpDebug`,
   `roleMatrixHasPermission`, `roleMatrixGetAccessForEmail`, `flowmeterCleanupCommentMetadata`,
   `flowmeterFixDates`, `_colLetter`, `statusCodesDeployAll`; `listUsers`/`updateRole`/…
   (Admin-объект) видны как методы из Utils.gs.
5. Проверить приложение: вход/OTP, журнал кабелей, расходомеры (ввод показаний),
   расписание, ограниченный просмотр графика (роль с workschedule.view.min).
6. Триггеры: меню Triggers — `hourlyCleanup` (Every 1 hour) на месте; НЕ запускать
   `setupTriggers` без необходимости (запуск безопасен — канон теперь один).
7. Журнал выполнения (Ctrl+Enter) — без новых ошибок.

## Для ПРОДА (kip8)

Состояние прод-проекта Apps Script в Task 514 НЕ проверялось (вероятно, в прод Utils.gs
уже содержит Admin-блок — репо-версия Utils синхронизирована с прод при Task 347).
Перед зеркальным деплоем собрать такую же выгрузку всех .gs из прод-проекта и сверить.

## Откаты

- До уборки 513: `git show pre-task513:scripts/<файл>.gs`
- Текущие версии Apps Script: `git show 2097d1e7:scripts/Flowmeter.gs`,
  `git show 51bdde92:scripts/RoleMatrixGate.gs`
- Admin.gs целиком: последний блок `git show pre-task513:scripts/Utils.gs`
