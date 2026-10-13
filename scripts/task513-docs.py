#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 513 — обновление документации обоих репо (промты + worklog).
По образцу task511-update-prompt.py: пре-ассерты → правка → пост-проверки.
"""
import io
import sys

KT = '/home/z/my-project/kip8test'
K8 = '/home/z/my-project/kip8'
PROMPT = 'Системный_промт_для_приложения_КИПиА.md'

fails = []


def read(p):
    return io.open(p, encoding='utf-8').read()


def write(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def once(src, needle, label):
    c = src.count(needle)
    if c != 1:
        fails.append('%s: найдено %d (ожидалось 1)' % (label, c))
    return c == 1


VER_513 = ('> **Версия документа:** 2026-10-13 (post-Task 513 — УБОРКА МЁРТВОГО КОДА '
           '(заявка: «Подтверждаю уборку» — по аудиту Task 512). УДАЛЕНО из index.html '
           '25 функций + 4 метода (−441 строка): остатки удалённых фич dev*/valve*/lock*/'
           'regulator*/project(s)*; калькуляторы calcErrorGOST/getOimlMpe/'
           'toggleErrorClassFields/validateNonNegativeField; refreshAppData; KipAuth.'
           'getCurrentUser-обёртка (приложение зовёт api напрямую); handleBackButton; '
           'toggleSearch; _fmtDateTime; isTablet; ticketRenderDetailInPanel. Из 7 .gs '
           'удалены 9 функций (−443 строки), гл. обр. ОПАСНЫЙ GAS-дубликат setupTriggers '
           'из Utils.gs (удалял ВСЕ триггеры проекта; канон — Code.gs, только '
           'hourlyCleanup). ВЕРИФИКАЦИЯ аудита: 8 «мёртвых» методов СОХРАНЕНЫ — их '
           'вызывают тесты (аудит не видел строковые литералы: _renderEmpPopup, '
           '_sourceLabel, _state, _vacDays, _vacNetDays, _wsFullFio, KipDB.del, '
           'reloadTotals); setupOtpInputs-IIFE ВОССТАНОВЛЕН (ошибка аудита: IIFE '
           'исполняется сам — обработчики OTP input/paste/Enter). SW v730→v731 '
           '(kip8-зеркало v527→v528); тесты 6489/0 + 6493/0; SMOKE 21/21 оба; '
           'DEPLOY-Task513 — замена 7 .gs в Apps Script (поведение не меняется). '
           'СЛЕДУЮЩАЯ ЗАДАЧА: 514.)\n')

VER_513_K8 = VER_513.replace('SW v730→v731 (kip8-зеркало v527→v528)',
                             'SW v527→v528 (kip8test-зеркало v730→v731)')

VER_512_SHORT = ('> **Версия документа (предыдущая):** 2026-10-12 (post-Task 512 — '
                 'АУДИТ КОДА ПРИЛОЖЕНИЯ: реальных ошибок 0, тесты 6472/0; найдено '
                 'GAS-дубликат setupTriggers (копия Utils.gs удаляет ВСЕ триггеры — '
                 'опасная), ~37 мёртвых функций ≈896 строк, 2 роута без вызовов, '
                 'guarded-остатки id; уборка — кандидат Task 513…)\n')

VER_512_SHORT_K8 = VER_512_SHORT.replace('6472/0', '6476/0')


def update_prompt(repo, ver_new, ver_prev_short, sw_old, sw_new, tests_old, tests_new):
    p = repo + '/' + PROMPT
    src = read(p)
    # 1. новая строка версии — ПЕРВОЙ (перед текущей post-512)
    cur = '> **Версия документа:** 2026-10-12 (post-Task 512'
    once(src, cur, repo + ': строка post-512')
    i = src.find(cur)
    # 2. сжатие старой post-512 → «предыдущая» ≤ 420
    j = src.find('\n', i)
    old_line = src[i:j]
    # удалить ВСЕ старые строки post-512 (текущую) и вставить: новая + сжатая
    src = src[:i] + ver_new + ver_prev_short + src[j + 1:]
    # 3. актуализация версии кэша
    sw_line = '> **Текущая версия кэша:** `%s`' % sw_old
    once(src, sw_line, repo + ': строка версии кэша')
    src = src.replace(sw_line, '> **Текущая версия кэша:** `%s`' % sw_new)
    # 4. актуализация ожидания тестов
    once(src, tests_old, repo + ': строка тестов')
    src = src.replace(tests_old, tests_new)
    write(p, src)
    # пост-проверки
    out = read(p)
    if ver_new not in out:
        fails.append(repo + ': новая строка версии не записана')
    if len(ver_prev_short) > 500:
        fails.append(repo + ': сжатая строка > 500 симв.')
    if sw_new not in out:
        fails.append(repo + ': версия кэша не обновлена')


WL = """
---
Task ID: 513
Agent: main (Super Z)
Task: Заявка: «Подтверждаю уборку» — уборка мёртвого кода по аудиту Task 512
      (передан PAT неограниченного срока на 4 репо: kip8/kip8test/kip8-desktop/
      kip8test-desktop).

Work Log:
- Старт: kip8test @c3b185c8 (v730, 6472/0), kip8 @dc30cfb (v527, 6476/0). Теги
  pre-task513 + v730-post512 / v527-post512 — запушены в оба репо (откат:
  git show pre-task513:<путь>). PAT обновлён (/home/z/.kip_pat).
- ВЕРИФИКАЦИЯ АУДИТА до удаления (desktop-репо склонированы: kip8test-desktop/
  kip8-desktop — index.html автосинхронизируется GitHub Action sync-to-desktop.yml,
  тесты там расходятся с основными): 25 функций — 0 ссылок где-либо (чисто);
  из 12 «мёртвых» методов 8 СОХРАНЕНЫ — тесты их вызывают/ассертят строковыми
  литералами, которых граф вызовов аудита не видел: _renderEmpPopup (assert
  «жив (обёртка для тестов)»), _sourceLabel (PC._sourceLabel), _state, _vacDays,
  _vacNetDays, _wsFullFio, KipDB.del (kdb.del), reloadTotals (host.reloadTotals).
  КАМЕНЬ: аудит метод-ссылок .имя не сканировал строковые литералы тестов.
- УДАЛЕНО kip8test index.html 66066→65625 (−441): 25 функций + 4 метода
  (_fmtDateTime, KipAuth.getCurrentUser-обёртка, handleBackButton, toggleSearch);
  7 .gs −443 строки: _colLetter, flowmeterCleanupCommentMetadata, flowmeterFixDates,
  roleMatrixHasPermission, roleMatrixGetAccessForEmail, sdpDebug, statusCodesDeployAll,
  statusCodesStatus + ОПАСНЫЙ setupTriggers из Utils.gs (канон Code.gs); правки
  устаревших комментариев (шапки RoleMatrix/StatusCodesInit/SessionsDevicePolicy/
  Utils ×2; осиротевший заголовок «ДИАГНОСТИКА» в хвосте SessionsDevicePolicy.gs).
- КАМЕНЬ-ОТКАТ: setupOtpInputs (IIFE) удалён как «мёртвый», но IIFE ИСПОЛНЯЕТСЯ
  сам (input/keydown/paste на otp1–otp6, Enter на authEmail/createUserEmail) —
  автопереход OTP сломался бы. ВОССТАНОВЛЕН из git-тега; browser-check B
  (цифра в otp1 → фокус otp2; Backspace; paste «123456» → 6 полей; Enter в email →
  sendOTP) — пруф. Урок: «мёртвость» IIFE определяется потребителями его
  side-эффектов, не вызовами.
- КАМЕНЬ (восстановление): end-скан `rstrip() == '})();'` не учитывает ПРОБЕЛЫ
  СЛЕВА — первая вставка взяла 397 строк вместо 70 и поглотила следующий раздел
  (двойной якорь «Запуск авторизации»); вылечено вырезанием по второму вхождению
  якоря + brace-matching-границы. КАМЕНЬ (диагностика): bash-вывод «съедает»
  последовательность [m (SGR-подобная) — строка stats.byEmail[mail] ВЫГЛЯДЕЛА
  сломанной («byEmailail]»), файл был корректен; проверка символов — python
  repr/od. КАМЕНЬ (аудит): «дубликат p» StatusCodesInit.gs:670/677 — ЛОЖНЫЙ
  (вложенные локальные хелперы _scTimestamp/_scIsoDate, не глобальный override).
- SW v730→v731; бамп: гарды v731→v732 ×162 строк / ассерты v730→v731 (828 замен,
  191 файл); test-task513.js (+17 тестов: отсутствие удалённых имён через
  \\b-регэксп — getOimlMpe ≠ живой getOimlMpeR60!; живость тест-используемых
  методов; IIFE-гвард; канон setupTriggers ×1 в Code.gs; SW-ассерты) → 6489/0.
- SMOKE scripts/task513-browser-check.py 21/21 (порт 8995: boot без pageerror;
  страницы devices/valves-prod/regulators-prod/lockouts-prod/projects-prod/
  calculators активны; журнал кабелей — 4 активные карточки мока (архив не в
  списке); OTP-регрессия; мобильная светлая). Скриншоты download/kip8test-task513/.
- ЗЕРКАЛО kip8: тот же task513-cleanup.py (имя-ориентированный, без привязки к
  строкам) — index.html 66054→65611 (−443), те же 7 .gs; SW v527→v528; бамп
  v528→v529/v527→v528 (830 замен, 193 файла); test-task513.js (зеркало, kipia-v52x)
  → 6493/0; SMOKE task513-browser-check-k8.py 21/21 (порт 8997, ключи LS без
  префикса kip8test:). Папка DEPLOY: kip8 — та же 7 файлов, см. свой экземпляр.
- DEPLOY-Task513-dead-code-cleanup.md: замена 7 .gs в Apps Script (обе копии
  проекта — тест и прод; чистые удаления, поведение не меняется; после замены
  setupTriggers из редактора выполняется ТОЛЬКО канон Code.gs).

Stage Summary:
- Уборка выполнена зеркально: index.html −441/−443 строк, 7 .gs −443 строки в
  каждом репо; опасный GAS-дубликат setupTriggers устранён (Utils.gs), канон —
  Code.gs; ошибки аудита исправлены ДО продакшена (8 методов живы — тесты;
  IIFE setupOtpInputs восстановлен); SW kipia-test-v731 / kipia-v528; тесты
  6489/0 + 6493/0; SMOKE 21/21 оба. DEPLOY-Task513 — замена 7 .gs (не срочно,
  рекомендовано). СЛЕДУЮЩАЯ ЗАДАЧА: 514.
"""

WL_K8 = """
---
Task ID: 513
Agent: main (Super Z)
Task: Заявка: «Подтверждаю уборку» — ЗЕРКАЛО kip8test (уборка мёртвого кода по
      аудиту Task 512; PAT передан на 4 репо).

Work Log:
- Из kip8test (Task 513): те же удаления имя-ориентированным скриптом
  task513-cleanup.py — index.html 66054→65611 (−443: 25 функций + 4 метода),
  7 .gs −443 строки (8 функций + опасный setupTriggers из Utils.gs; канон
  Code.gs не тронут) + правки устаревших комментариев; setupOtpInputs-IIFE
  восстановлен из git pre-task513 (IIFE исполняется сам — обработчики OTP).
- SW v527→v528; бамп: гарды v528→v529 / ассерты v527→v528 (830 замен, 193
  файла); test-task513.js (зеркало, kipia-v52x, +17) → 6493/0.
- SMOKE scripts/task513-browser-check-k8.py 21/21 (порт 8997, ключи LS без
  префикса; страницы приборов/арматуры/журнал 4 карточки/OTP-регрессия/
  мобильная светлая). DEPLOY-Task513 — замена тех же 7 .gs в ПРОД Apps Script.

Stage Summary:
- Зеркало уборки: −443 строки index.html, −443 строки 7 .gs; дубликат
  setupTriggers устранён (канон Code.gs); SW kipia-v528; тесты 6493/0
  (kip8test — v731, 6489/0); SMOKE 21/21. DEPLOY-Task513 — замена 7 .gs
  (поведение не меняется). СЛЕДУЮЩАЯ ЗАДАЧА: 514.
"""

update_prompt(KT, VER_513, VER_512_SHORT,
              'kipia-test-v730', 'kipia-test-v731',
              '# Ожидается: 6472 passed, 0 failed (kip8test; в kip8 — 6476 passed, '
              '0 failed — Task 508 ПЕРЕНЕСЁН (Task 509, kipia-v526→v527); оба репо '
              'синхронны)',
              '# Ожидается: 6489 passed, 0 failed (kip8test; в kip8 — 6493 passed, '
              '0 failed — Task 513 уборка зеркальная; оба репо синхронны)')

update_prompt(K8, VER_513_K8, VER_512_SHORT_K8,
              'kipia-v527', 'kipia-v528',
              '# Ожидается: 6476 passed, 0 failed (kip8; в kip8test — 6472 passed, '
              '0 failed — Task 508 перенесён (Task 509), оба репо синхронны)',
              '# Ожидается: 6493 passed, 0 failed (kip8; в kip8test — 6489 passed, '
              '0 failed — Task 513 уборка зеркальная; оба репо синхронны)')

# worklog-записи
write(KT + '/worklog.md', read(KT + '/worklog.md').rstrip('\n') + '\n' + WL)
write(K8 + '/worklog.md', read(K8 + '/worklog.md').rstrip('\n') + '\n' + WL_K8)

# зеркальный DEPLOY в kip8
dep = read(KT + '/scripts/DEPLOY-Task513-dead-code-cleanup.md')
dep = dep.replace('репозитория `kip8test`', 'репозитория `kip8`')
dep = dep.replace('`scripts/*.gs`, коммит Task 513', '`scripts/*.gs`, коммит Task 513 (зеркало kip8test)')
dep = dep.replace('(тестовый — для kip8test)', '(боевой — ПРОД kip8)')
dep = dep.replace('тесты 6489/0, SMOKE 21/21', 'тесты 6493/0, SMOKE 21/21')
dep = dep.replace('клиентские проверки: тесты 6493/0, SMOKE 21/21',
                  'клиентские проверки: тесты 6489/0, SMOKE 21/21')
dep = dep.replace('те же 7 файлов из репозитория `kip8` (зеркальные, коммит Task 513)',
                  'те же 7 файлов — уже из репозитория `kip8test` (зеркальные, коммит Task 513)')
write(K8 + '/scripts/DEPLOY-Task513-dead-code-cleanup.md', dep)

if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('ДОКУМЕНТАЦИЯ ОБНОВЛЕНА: промты + worklog обоих репо + DEPLOY-зеркало kip8')
