# DEPLOY — Task 513 (УБОРКА МЁРТВОГО КОДА) + Task 514/515 (ПРОВЕРКА ФАКТИЧЕСКОГО Apps Script)

> ## ✅ СТАТУС: ТЕСТ ЗАДЕПЛОЕН И ВЕРИФИЦИРОВАН (Task 516, 2026-10-13)
>
> Пользователь заменил все 6 файлов и создал НОВУЮ ВЕРСИЮ РАЗВЁРТЫВАНИЯ
> (Deploy → New version). Контрольная docx-выгрузка (12 613 строк = 12 818 − 205)
> сверена с HEAD kip8test построчно:
> - **16/16 файлов функционально ИДЕНТИЧНЫ HEAD** (сверка без пустых строк);
>   14/16 — байт-в-байт (включая все 6 заменённых);
>   Utils.gs −1 пустая строка (~526, docx-артефакт), CableJournal −2 пустые
>   (известный дрейф 514/515, косметика) — поведение не затрагивается.
> - **Мины обезврежены:** `setupTriggers` — ровно ОДНО определение (Code.gs);
>   `hourlyCleanup` newTrigger — один (Code.gs); `sdpDebug`, `_colLetter`,
>   `roleMatrixHasPermission`, `roleMatrixGetAccessForEmail`,
>   `flowmeterCleanupCommentMetadata`, `flowmeterFixDates`,
>   `statusCodesDeployAll` — все ОТСУТСТВУЮТ.
> - **Admin-объект цел** (Utils.gs): `_requireAdmin`, `listUsers`, `updateRole`,
>   `resetLogin`, `deleteUser`, `createUser`, `listSessions`, `listLogs`.
> - Инвентарь функций всех 16 файлов = HEAD; порядок файлов прежний; арифметика
>   сдвигов сходится: −205 = Utils −18, Flowmeter −77, RoleMatrixInit −11,
>   RoleMatrix −63, RoleMatrixGate +4, SessionsDevicePolicy −41.
> - Скрипты сверки: `scripts/task516-verify.py`, `task516-final.py`
>   (артефакты `tmp/task516-verify/`); уроки парсинга: docx-строки начинаются
>   с NBSP (`\xa0* Name.gs —`), 7 файлов используют шапки `// Name.gs —`
>   вместо JSDoc, внутренние шапки ≠ границы файлов.
> - Осталось (runtime, вручную): проверить триггер hourlyCleanup в меню Triggers,
>   дымовой тест приложения (вход/OTP, журнал кабелей, расходомеры, график,
>   workschedule.view.min), журнал выполнения (Ctrl+Enter).
> - **КОРРЕКЦИЯ (продолжение Task 516): Apps Script проект ОДИН на все версии
>   приложения** — отдельного Apps Script для kip8/kip8test НЕТ (WEB_APP_URL
>   идентичен в обоих index.html). Верификация выше покрыла ЕДИНСТВЕННЫЙ сервер:
>   серверная часть Task 513 развёрнута для ВСЕХ версий; отдельный прод-деплой
>   не требуется (плановая задача 517 ОТМЕНЕНА; см. «Для ПРОДА» ниже).

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

## Для ПРОДА (kip8) — СНЯТО (неактуально, продолжение Task 516)

**Уточнение пользователя: «Проект Apps Script один на все версии приложения,
отдельного Apps Script для kip8 или наоборот kip8test нет».** Подтверждено кодом:
WEB_APP_URL идентичен в обоих репо (AKfycbyt2…: kip8test/index.html:35456 =
kip8/index.html:35442). Фронты отличаются только клиентом (GitHub Pages), сервер
и Google-таблицы общие. Сверка Task 516 (16/16 = HEAD) покрыла единственный
Apps Script — отдельный «прод-деплой» и «прод-выгрузка» НЕ ТРЕБУЮТСЯ.
Секция ниже оставлена как историческая справка (из ложной посылки двух
Apps Script-проектов) и НЕ требует исполнения.

~~Состояние прод-проекта Apps Script в Task 514/515 НЕ проверялось.~~ УРОК Task 515:
внутренние шапки-комментарии «X.gs —» внутри .gs НЕ являются границами файлов —
при ЛЮБОЙ будущей сверке выгрузок Utils.gs сверять ЦЕЛИКОМ. Возможны были два
варианта (оба снимаются одной заменой Utils.gs, что уже сделано):
(а) Admin-блок встроен в Utils.gs (как в проверенном проекте) → опасная копия
`setupTriggers` ПЕРЕКРЫВАЕТ канон (Utils > Code);
(б) отдельный файл Admin.gs существует → Admin < Code, канон побеждает, но файл
удалять (контент встроен в Utils.gs HEAD).

## Откаты

- До уборки 513: `git show pre-task513:scripts/<файл>.gs` (тег в обоих репо)
- Текущие версии теста (докаталог): `git show 2097d1e7:scripts/Flowmeter.gs`,
  `git show 51bdde92:scripts/RoleMatrixGate.gs`; Utils/RoleMatrix/RoleMatrixInit/
  SessionsDevicePolicy текущего теста ≈ `pre-task513` (−1..2 пустые строки, опечатки
  RoleMatrixInit уже в HEAD)
