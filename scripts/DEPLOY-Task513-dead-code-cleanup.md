# DEPLOY — Task 513 (УБОРКА МЁРТВОГО КОДА) + Task 514/515 (ПРОВЕРКА ФАКТИЧЕСКОГО Apps Script)

> **Заявки:** аудит кода (Task 512), «Подтверждаю уборку» (Task 513), docx-выгрузка
> всех .gs (Task 514), повторная выгрузка + «нет файла Admin.gs» (Task 515 — КОРРЕКЦИЯ).
> **Task 515 (коррекция разбора 514):** «Admin.gs» из отчёта 514 — это ВНУТРЕННЯЯ
> шапка-комментарий блока Admin, встроенного в КОНЕЦ Utils.gs (так задумано с Task 347:
> «Встроен в Utils.gs для удобства»), а НЕ отдельный файл. Отдельного файла Admin.gs
> в Apps Script НЕТ — удалять нечего. Итоговый план: **6 замен, удалений НЕТ.**
> Вывод 514 «runtime безопасен» ОТМЕНЁН — см. секцию «Триггеры» (мина АКТИВНА).

## Фактическое состояние Apps Script (тест kip8test) — итог сверки Task 514/515

**16 файлов (все — из репо; лишних НЕТ, «в Apps есть, в репо нет» = пусто).**
Совпадают с эталоном — НЕ трогать (10): Code.gs, Auth.gs, Sessions.gs,
FlowmeterArchive.gs, ValidationRules.gs, WorkSchedule.gs, VacationsInit.gs, PPEInit.gs,
PlanEvents.gs + CableJournal.gs (единственное расхождение — 2 пустые строки, косметика,
можно не трогать).

**Отсутствуют в Apps Script (8, одноразовые init/diagnose — норма, НЕ разворачивать):**
FlowmeterInit.gs, StatusCodesInit.gs, PlanEventsInit.gs, PlanWorksInit.gs, TabNumbersFix.gs,
VacationsDiagnose.gs, RoleMatrixTask340Init.gs, RoleMatrixTask462Init.gs.

**Заменить (6):**

| Файл | Фактическое состояние (apps) | Замена на HEAD изменит |
|---|---|---|
| `Utils.gs` | 1113 строк ≈ pre-513 (−1 пустая строка); Admin-блок ВСТРОЕН в конец файла (строки ~778–1112, шапка «Admin.gs — …Встроен в Utils.gs…») | −ОПАСНЫЙ дубликат `setupTriggers` (удалял ВСЕ триггеры) и мёртвый `_colLetter`; **Admin-объект ОСТАЁТСЯ** (живой — роутится из Code.gs); −21/+4 строк |
| `Flowmeter.gs` | точно Task 359 (10.09) | Task 376: честный `archive_write_failed` (показания НЕ теряются при сбое записи архива) + уборка 513; −99/+22 строк |
| `RoleMatrixGate.gs` | точно Task 319 (05.09) | Task 340: право `workschedule.view.min` (ограниченный просмотр графика) — ФУНКЦИОНАЛЬНЫЙ дрейф; −3/+7 строк |
| `RoleMatrix.gs` | = pre-513 байт-в-байт | уборка 513: −`roleMatrixHasPermission`, −`roleMatrixGetAccessForEmail` (superseded RoleMatrixGate); −64/+1 строк |
| `RoleMatrixInit.gs` | = pre-513 + правки опечаток пользователя | опечатки (создаёт/хелпер) в версии УЧТЕНЫ (Task 514); уборка 513; −11 строк |
| `SessionsDevicePolicy.gs` | = pre-513 байт-в-байт | уборка 513: −`sdpDebug`; −41 строка |

## ⚠️ Триггеры: КОРРЕКЦИЯ вывода Task 514

Опасная копия `setupTriggers` (сначала удаляет ВСЕ триггеры без разбора, потом создаёт
hourlyCleanup) живёт в конце Utils.gs (внутри встроенного Admin-блока). Порядок загрузки
файлов GAS — алфавитный: **Code.gs < Utils.gs → копия из Utils.gs ПЕРЕКРЫВАЕТ канон
Code.gs: запуск `setupTriggers()` из редактора сейчас выполняет ОПАСНУЮ ветку.**
Сегодня фактического ущерба нет: триггер в проекте один (hourlyCleanup; других
`newTrigger` во всём коде нет), а опасная версия его же и пересоздаёт. Но мина
ВЗВЕДЕНА: любой будущий триггер будет молча удалён запуском `setupTriggers()`.
**Замена Utils.gs (позиция 1) обезвреживает:** единственный `setupTriggers` останется
в Code.gs — канон, удаляющий только дубликаты hourlyCleanup.

## План замены

Заменить содержимое файлов в редакторе Apps Script на версии из репозитория `kip8test`
(`scripts/*.gs`, HEAD = Task 513 + правки опечаток Task 514):

| # | Файл | Действие |
|---|------|----------|
| 1 | `Utils.gs` | ЗАМЕНИТЬ (выделить всё → вставить версию HEAD → Ctrl+S) |
| 2 | `Flowmeter.gs` | ЗАМЕНИТЬ |
| 3 | `RoleMatrixGate.gs` | ЗАМЕНИТЬ |
| 4 | `RoleMatrix.gs` | ЗАМЕНИТЬ |
| 5 | `RoleMatrixInit.gs` | ЗАМЕНИТЬ |
| 6 | `SessionsDevicePolicy.gs` | ЗАМЕНИТЬ |
| — | `CableJournal.gs` | по желанию (только 2 пустые строки) |
| — | `FlowmeterInit.gs`, `StatusCodesInit.gs` и др. | ПРОПУСТИТЬ (в Apps Script отсутствуют — одноразовые) |

`Code.gs` НЕ трогать — канон `setupTriggers` жив там. **Файлы НЕ удалять: лишних нет.**

## Шаги

1. Открыть проект Apps Script (тестовый — kip8test).
2. Файлы 1–6: открыть → выделить всё → вставить версию из репозитория → Ctrl+S.
3. Сверка: `setupTriggers` в списке функций ОДИН раз (Code.gs); исчезли `sdpDebug`,
   `roleMatrixHasPermission`, `roleMatrixGetAccessForEmail`,
   `flowmeterCleanupCommentMetadata`, `flowmeterFixDates`, `_colLetter`,
   `statusCodesDeployAll`; `listUsers`/`updateRole`/… (Admin-объект) видны как методы
   Utils.gs — КАК И РАНЬШЕ (блок был и остаётся встроенным).
4. Проверить приложение: вход/OTP, журнал кабелей, расходомеры (ввод показаний),
   расписание, ограниченный просмотр графика (роль с workschedule.view.min).
5. Триггеры: меню Triggers — `hourlyCleanup` (Every 1 hour) на месте; НЕ запускать
   `setupTriggers()` без необходимости (после замены Utils.gs запуск безопасен —
   канон один, но и нужды нет: триггер уже стоит).
6. Журнал выполнения (Ctrl+Enter) — без новых ошибок.

## Для ПРОДА (kip8)

Состояние прод-проекта Apps Script в Task 514/515 НЕ проверялось. УРОК Task 515:
внутренние шапки-комментарии «X.gs —» внутри .gs НЕ являются границами файлов — при
сверке прода Utils.gs сверять ЦЕЛИКОМ. Возможны два варианта, оба лечатся одинаково:
(а) Admin-блок встроен в Utils.gs (как в тесте) → тогда опасная копия `setupTriggers`
ПЕРЕКРЫВАЕТ канон (Utils > Code) — замена Utils.gs обязательна;
(б) отдельный файл Admin.gs существует → Admin < Code, канон побеждает, но файл всё
равно удалить (контент встроен в Utils.gs HEAD). Перед зеркальным деплоем собрать
выгрузку всех .gs из прод-проекта и сверить (~15 минут).

## Откаты

- До уборки 513: `git show pre-task513:scripts/<файл>.gs` (тег в обоих репо)
- Текущие версии теста (докаталог): `git show 2097d1e7:scripts/Flowmeter.gs`,
  `git show 51bdde92:scripts/RoleMatrixGate.gs`; Utils/RoleMatrix/RoleMatrixInit/
  SessionsDevicePolicy текущего теста ≈ `pre-task513` (−1..2 пустые строки, опечатки
  RoleMatrixInit уже в HEAD)
