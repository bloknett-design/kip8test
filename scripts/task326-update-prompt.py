# -*- coding: utf-8 -*-
# Обновление системного промта kip8test до post-Task 326
# (BUGFIX: незакрытый </div> страницы «Табель» из Task 323 ломал
#  открытие разделов после табеля и полных карточек расходомеров
#  на десктопе — #detailPanel был вложен в скрытую страницу)
with open('Системный_промт_для_приложения_КИПиА.md', encoding='utf-8') as f:
    lines = f.readlines()

new3 = '''> **Версия документа:** 2026-09-05 (post-Task 326 BUGFIX: «не открывались некоторые разделы и полные карточки расходомеров» — Task 323 потерял ЗАКРЫВАЮЩИЙ </div> страницы #page-work-schedule при перестройке рабочей области в #wsWsBody: ВСЕ разделы после табеля в разметке [«КИП ИОС», «Приборы», «Блокировки», «Задвижки», «Регуляторы», «Проекты», «Кабельный журнал», «План 114», калькуляторы, конвертеры, «Сапёр», «Телефонный справочник», админ-панель, «Библиотека», «Билеты», «Что нового»] и ДЕСКТОПНАЯ ПАНЕЛЬ #detailPanel были ВЛОЖЕНЫ в скрытую [display:none] страницу табеля → клики «не открывали» их; мобильные полные страницы расходомеров идут в разметке РАНЬШЕ табеля и работали; продуктовый kip8 v417 НЕ затронут [баланс 0, баг с kip8test v562]. ФИКС: закрывающий </div> возвращён [после #wsWsBody, перед #page-kip-ios] + комментарий Task 326 (BUGFIX); SW kipia-test-v564→v565. Регресс-тест test-task326.js: стек-парсер <div> с пропуском script/style/комментариев — баланс 0, КАЖДАЯ page-* и #detailPanel — прямые потомки #contentArea, #wsWsBody/#wsGridWrap/#wsTotalsDrawer — внутри табеля. Тесты 1928→1935/0; браузер: 12/12 карточек расходомеров ВИДНЫ [десктоп detail-панель 640×788, мобайл полная страница], 18 разделов active+visible, 0 JS-ошибок; регресс task325 27/27, task323 45/45, task306 29/29; VLM ×3. ДЕПЛОЙ: ТОЛЬКО Pages + Ctrl+Shift+R ×1–2 — Apps Script/листы НЕ трогать. ПЕРЕНОС в kip8: НЕ выполнен — Tasks 315–326 одной партией [k8 v417→v418])
'''

assert lines[2].startswith('> **Версия документа:**')
lines.insert(2, new3 if new3.endswith('\n') else new3 + '\n')
print('Строка 3 вставлена (цепочка версий)')

src = ''.join(lines)

reps = [
    ('> **Текущая версия кэша:** `kipia-test-v564`',
     '> **Текущая версия кэша:** `kipia-test-v565`'),
    ('| `kip8test` | PWA | `kipia-test-v564` |',
     '| `kip8test` | PWA | `kipia-test-v565` |'),
]
for old, new in reps:
    n = src.count(old)
    assert n == 1, (old, n)
    src = src.replace(old, new)
print('Версии кэша обновлены (2 замены)')

# Счётчики тестов
reps2 = [
    ('├── tests/                      # 1928 юнит-тестов (Node.js, 43 файлов): run-all.js, test-role-access.js, и др.',
     '├── tests/                      # 1935 юнит-тестов (Node.js, 44 файла): run-all.js, test-role-access.js, и др.'),
    ('ожидается `1928 passed, 0 failed`', 'ожидается `1935 passed, 0 failed`'),
    ('# Ожидается: 1928 passed, 0 failed', '# Ожидается: 1935 passed, 0 failed'),
]
for old, new in reps2:
    n = src.count(old)
    assert n == 1, (old, n)
    src = src.replace(old, new)
print('Счётчики тестов обновлены (3 замены)')

# Буллет Task 326 — после буллета Task 325
entry = ('\n- **BUGFIX Task 326 — незакрытый </div> «Табеля» ломал открытие разделов и полных карточек расходомеров**: заявка: «Проверь баг, не открываются некоторые разделы и полные карточки расходомеров». ПРИЧИНА: Task 323 (боковая шторка итогов) при перестройке рабочей области в #wsWsBody (сетка + шторка) потерял ОДИН закрывающий </div> страницы #page-work-schedule → в DOM все разделы, идущие в разметке ПОСЛЕ табеля [«КИП ИОС», «Приборы», «Блокировки», «Задвижки», «Регуляторы», «Проекты», «Кабельный журнал», «План 114», калькуляторы/конвертеры, «Сапёр», «Телефонный справочник», админ-панель, «Библиотека», «Билеты», «Что нового»] и ДЕСКТОПНАЯ ПАНЕЛЬ ДЕТАЛЕЙ #detailPanel оказались ВЛОЖЕННЫМИ в скрытую (display:none без .active) страницу табеля: клик по разделу ставил .active, но родитель скрыт → «не открывается»; клик по карточке расходомера на десктопе наполнял #detailPanel (.active, заголовок, показания), но offsetWidth=0 — НЕ ВИДНА; мобильные полные страницы расходомеров (#page-flowmeter-detail) идут в разметке РАНЬШЕ табеля — на телефоне всё работало; баг присутствовал в kip8test v562–v564 (с Task 323), продуктовый kip8 (v417, Tasks ≤314) НЕ затронут — баланс 0. ДИАГНОСТИКА: стек-парсер тегов <div> (пропуск <script>/<style>/комментариев — JS-шаблоны внутри скриптов содержат <div> и сломали бы наивный счёт) → ровно 1 незакрытый div; git-бисекция баланса по коммитам: Task 322 — 0, Task 323 — 1. ФИКС: закрывающий </div> #page-work-schedule возвращён (после закрытия #wsWsBody, перед #page-kip-ios; 8-пробельный отступ уровня страниц) + пояснительный комментарий «Task 326 (BUGFIX)» в HTML; вложенность #wsWsBody/#wsGridWrap/#wsTotalsDrawer внутри табеля СОХРАНЕНА (задумано Task 323); SW kipia-test-v564→v565. Регресс-тест tests/test-task326.js (7): лёгкий стек-парсер parseDivTree (пропуск script/style/комментариев) — 1) баланс <div>/</div> по документу = 0 незакрытых; 2) #detailPanel — ПРЯМОЙ потомок #contentArea; 3) пострадавшие разделы (page-kip-ios/devices-prod/lockouts-prod/valves-prod/regulators-prod/projects-prod/cable-journal-edit/plan-114/calculators/calc-kipa/converter/library-internal/exam-tickets/whats-new/minesweeper/phonebook/admin/work-schedule) — прямые потомки #contentArea; 4) КАЖДАЯ page-* — прямой потомок #contentArea (список из HTML, оффендеры = 0); 5) #wsWsBody — потомок #page-work-schedule, #wsGridWrap и #wsTotalsDrawer — потомки #wsWsBody; 6) порядок разметки (табель раньше #detailPanel) + комментарий Task 326 (BUGFIX); 7) SW v565 + assertFalse v566. Верификация: сьют 1928→1935/0; bug326-repro.py (репродукция: ДО фикса десктоп 12/12 карточек active+len>200 но offsetWidth=0; ПОСЛЕ — 12/12 ВИДНЫ 640×788, мобайл — полные страницы, 0 JS-ошибок); bug326-verify.py 41/41 — 18 разделов active+VISIBLE (десктоп 1280×844 / мобайл 375×N, parent=contentArea), карточки №1/№2/№5/№12 видны, 0 JS-ошибок, пруфы task326-proof-{desktop,mobile}-flow-detail.png + task326-proof-desktop-devices.png; регресс task325-browser-check 27/27 (три ряда/шторка/линии — НЕ задеты), task323-browser-check 45/45, task306-browser-check 29/29; VLM ×3 (десктоп-карточка: панель открыта, «Хозрасчёт №1», 9111 т / 60,460 Гкал, master-detail без дефектов; мобайл: полная карточка с показаниями и хронологией; «Приборы»: список корпусов отрисован). ⚠️ ДЕПЛОЙ: ТОЛЬКО GitHub Pages + Ctrl+Shift+R ×1–2 (SW v564→v565) — Apps Script/листы НЕ трогать (только разметка+SW) — см. scripts/DEPLOY-Task326-fix-dom-nesting.md.')
lines2 = src.split('\n')
insert_at = None
for i, l in enumerate(lines2):
    if l.startswith('- **Табель учёта рабочего времени — ИТОГИ УЧЁТА: колонка сотрудников по самому широкому тексту'):
        # конец буллета Task 325 — следующая строка после него
        insert_at = i + 1
        break
assert insert_at is not None, 'буллет Task 325 не найден'
lines2.insert(insert_at, entry)
src = '\n'.join(lines2)
print('Буллет Task 326 вставлен (после Task 325)')

with open('Системный_промт_для_приложения_КИПиА.md', 'w', encoding='utf-8') as f:
    f.write(src)
print('Файл сохранён')
