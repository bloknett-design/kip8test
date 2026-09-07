# -*- coding: utf-8 -*-
# Обновление системного промта kip8test до post-Task 334
# («Вид» без значков + липкий блок карточки прибора + мобильный
#  табельный учёт: скрытая подсветка, окна за чипами, итоги —
#  страница «Итоги учёта» с 3 шевронами, сужение фамилий до 4 букв)
with open('Системный_промт_для_приложения_КИПиА.md', encoding='utf-8') as f:
    lines = f.readlines()

new3 = '''> **Версия документа:** 2026-09-07 (post-Task 334: КНОПКА «ВИД» БЕЗ ЗНАЧКОВ + ЛИПКИЙ БЛОК КАРТОЧКИ ПРИБОРА + МОБИЛЬНЫЙ ТАБЕЛЬНЫЙ УЧЁТ [заявка: «Название кнопки "Вид" сделай без значков, просто "Вид". В полной карточке прибора, блок с картинкой и строками "№ прибора" и "Место установки" не должны прокручиваться по вертикали. Необходимо проработать отображение раздела табельного учёта в мобильной версии: кнопка включения перекрёстной подсветки должна быть убрана (её функционал не реализуется в мобильной версии); два окна с мероприятиями и нормами должны быть изначально скрыты; итоги учёта должны открываться на новой странице под названием "Итоги учёта" и с тремя шевронами в верхнем баре, а таблица данных должна быть с фамилиями сотрудников; при прокрутке по горизонтали шахматки табеля учёта и таблицы итогов учёта, столбцы с фамилиями сотрудников должны сужаться до отображения первых четырёх букв фамилий.»]: 1) КНОПКА «ВИД» — БЕЗ ЗНАЧКОВ: из #wsViewBtn УДАЛЕНЫ все три svg-иконки (wsViewIconFull/Shift/Day — «полосы группами») — в кнопке ТОЛЬКО span.ws-view-label «Вид»; _updateViewBtn больше не переключает иконки (aria-label/замок/подсказка #wsViewTip/тосты/цикл — без изменений); CSS-правило .ws-view-btn svg удалено. 2) КАРТОЧКА ПРИБОРА — ВЕРХНИЙ БЛОК ЛИПКИЙ: #page-device-detail .dev-detail-top { position: sticky; top: 56px; z-index: 5; box-shadow } [под липкой шапкой страницы]; #detailPanel .dev-detail-top { position: sticky; top: 0; margin: 0 -16px; padding-left: 16px } [full-bleed скролл-зоны панели — контент не просвечивает по бокам, картинка на прежнем месте]; КРИТИЧНО: мобильное правило #contentArea > .page-content.active { overflow-y: auto } («мобильная защита») ДЕЛАЕТ активную страницу СКРОЛЛ-КОНТЕЙНЕРОМ — sticky .dev-detail-top привязывался к НЕЙ (height:auto — сама не прокручивается) вместо html и НЕ работал; ФИКС: #contentArea > #page-device-detail.page-content.active { overflow: visible } [двух-ID специфичность выше; прокрутка страницы — документом, как у всех]. 3) МОБИЛЬНЫЙ ТАБЕЛЬ: #wsCrossBtn { display: none } в media ≤1023px [подсветка-перекрестье — функционал НАВЕДЕНИЯ, на сенсоре не реализуется; десктоп не тронут]; окна #wsEventsPanel/#wsCalPanel ИЗНАЧАЛЬНО СКРЫТЫ (#page-work-schedule:not(.ws-mob-events-on/-norms-on), только ≤1023px), РАСКРЫВАЮТСЯ чипами .ws-mob-chips («Мероприятия»/«Нормы», toggleMobPanel: классы на странице + aria-pressed чипа; начальное состояние — свёрнуто КАЖДЫЙ раз); чипы — только мобильный display: flex, активный — акцент rgba(74,143,199,...). 4) ИТОГИ УЧЁТА — МОБИЛЬНАЯ СТРАНИЦА #page-ws-totals «Итоги учёта»: НОВАЯ страница с page-inline-header [многострелочный шеврон chevronTap — глубина навигации; путь дашборд → Документация ИОС → Табель → Итоги = РОВНО 3 СТРЕЛКИ, как просил пользователь] + собственные вкладки Месяц/Год (#wsTtPageTabMonth/Year) + тело #wsTtPageBody [класс ws-tt-body: скролл как в шторке; фон = панели #0e1621/#e9e7de; высота 100vh−56−70−safe-area, страница не прокручивается целиком]; toggleTotals на мобиле (matchMedia !min-1024) → navigateTo('ws-totals') БЕЗ шторки [гейт вида действует и на страницу]; навигация: PAGE_PARENTS['ws-totals']='work-schedule', PAGE_LABELS «Итоги учёта», _WORK_SCHEDULE_PAGES=['work-schedule','ws-totals'] [права табеля], хук navigateTo открывает (onTotalsPageOpen: флаг _ttPage + вкладки + _renderTotals + _reapplyEmpNarrow), уход с ws-totals — onTotalsPageClose; РЕНДЕР: _ttBodyEl() отдаёт ТЕЛО СТРАНИЦЫ при открытом _ttPage, иначе тело шторки [все 3 рендера: _renderTotalsMonth/_renderTotalsYear/_renderTotalsYearTable + _rowClass]; гейты: _renderTotals/_renderTotalsIfOpen учитывают _totalsOpen || _ttPage; setTotalsTab синхронизирует вкладки страницы и НЕ делает повторный переход; таблица — мобильные правила ws-tt-emp (фамилии, sticky); закрытие — шеврон/системный «назад». 5) СУЖЕНИЕ ФАМИЛИЙ ДО 4 БУКВ при горизонтальной прокрутке: span.ws-emp-full [сетка] / span.ws-tt-name [итоги: месяц + год + архив] с data-full/data-s4 (_surname4: первые 4 буквы ПЕРВОГО слова ФИО); слушатели scroll (passive, порог 6px) на #wsGridWrap/#wsTtBody/#wsTtPageBody (_attachEmpNarrow, init, однократно): _narrowApply — класс .ws-narrow на ВСЕ таблицы контейнера + обмен textContent span (data-s4 ⇄ data-full); CSS ≤1023px: .ws-grid.ws-narrow th/td.ws-emp-col 76px [таб.номер .ws-tab-no и должность .ws-emp-pos скрыты], .ws-tt-table.ws-narrow th/td.ws-tt-emp 58px [.ws-tt-tabno скрыт]; при возврате scrollLeft→0 — ПОЛНОЕ ФИО; ПЕРЕРИСОВКИ: _reapplyEmpNarrow после _renderGrid/_renderTotalsMonth/_renderTotalsYearTable [сужение переживает смену месяца/«Обновить»/правки]. Верификация: тесты 2055→2087/0 [+32 tests/test-task334.js: HTML кнопки без svg/иконки удалены/CSS-правило svg удалено/VM _updateViewBtn без иконок; sticky мобайл 56px + десктоп top 0/margin -16; #wsCrossBtn none + :not-скрытие окон + чипы HTML/CSS/VM toggleMobPanel; страница итогов HTML/navigateTo-хуки/VM onTotalsPageOpen+_ttBodyEl/гейты/карты/CSS; VM _surname4/_narrowApply/_reapplyEmpNarrow/_attachEmpNarrow; span-обёртки в рендерах; CSS 76px/58px; SW v573]; актуализированы: work-schedule [_WORK_SCHEDULE_PAGES + assertEqual карты ролей ×3], task321 [окно regex 2600→4000 в toggleTotals], task333 [иконки assertFalse + svg-нет], task315/317/328 browser-скрипты [чипы до замеров, colW по видимым детям, кнопка подсветки скрыта]; SW-бамп v572→v573 [sw.js + 33 тест-файла], assertFalse «лишний инкремент» → v574 в 15]; browser scripts/task334-browser-check.py 39/39 (порт 8944; МОБАЙЛ 375 тёмная [«Вид» без svg; подсветка скрыта; окна скрыты, чипы видны, тогглы; прокрутка сетки → ws-narrow + «Иван» + таб.номер скрыт, возврат → полное ФИО; итоги — СТРАНИЦА с «Итоги учёта», ТРИ шеврона, вкладки, шторка НЕ открывалась; месяц: фамилии; год: переполнение + сужение итогов + возврат; шеврон вернул на табель, _ttPage снят; СИНТЕТИЧЕСКАЯ карточка прибора: .dev-detail-top top=56 при скролле]; СВЕТЛАЯ [чипы/страница/фон #e9e7de]; ДЕСКТОП 1280 [подсветка ВИДИМА, окна-трети ВИДНЫ, чипы скрыты, «Вид» без svg, итоги ШТОРКОЙ ws-tt-open, панель прибора sticky top 0]; 0 JS-ошибок ×3); регресс браузером: 333 36/36 [актуализирован: C3 без иконок, мобайл-итоги на СТРАНИЦЕ], 315 33/33 [чип до замеров], 317 49/49 [colW по видимым детям + чипы + кнопки display:none skip], 328 36/36 [O: кнопка подсветки на мобиле СКРЫТА]. ⚠️ ДЕПЛОЙ: ТОЛЬКО GitHub Pages + Ctrl+Shift+R ×1–2 (SW kipia-test-v572→v573) — Apps Script/листы НЕ трогать (только клиент). ПЕРЕНОС в kip8: НЕ выполнен — ждёт проверки пользователем [потом одной партией, k8 v419→v420])
'''

assert lines[2].startswith('> **Версия документа:**')
lines.insert(2, new3 if new3.endswith('\n') else new3 + '\n')
print('Строка 3 вставлена (цепочка версий)')

src = ''.join(lines)

reps = [
    ('> **Текущая версия кэша:** `kipia-test-v572`',
     '> **Текущая версия кэша:** `kipia-test-v573`'),
    ('| `kip8test` | PWA | `kipia-test-v572` |',
     '| `kip8test` | PWA | `kipia-test-v573` |'),
    ('├── tests/                      # 2055 юнит-тестов (Node.js, 50 файлов): run-all.js, test-role-access.js, и др.',
     '├── tests/                      # 2087 юнит-тестов (Node.js, 51 файл): run-all.js, test-role-access.js, и др.'),
    ('ожидается `2055 passed, 0 failed`',
     'ожидается `2087 passed, 0 failed`'),
]
for old, new in reps:
    n = src.count(old)
    assert n == 1, (old, n)
    src = src.replace(old, new)
print('Версии кэша и счётчики обновлены (4 замены)')

# Буллет Task 334 — сразу ПОСЛЕ буллета Task 333
entry = ('\n- **Task 334 — КНОПКА «ВИД» БЕЗ ЗНАЧКОВ + ЛИПКИЙ БЛОК КАРТОЧКИ ПРИБОРА + '
         'МОБИЛЬНЫЙ ТАБЕЛЬНЫЙ УЧЁТ (подсветка скрыта, окна за чипами, итоги — '
         'СТРАНИЦА «Итоги учёта» с 3 шевронами, сужение фамилий до 4 букв)**: заявка: '
         '«Название кнопки "Вид" сделай без значков, просто "Вид". В полной карточке '
         'прибора, блок с картинкой и строками "№ прибора" и "Место установки" не '
         'должны прокручиваться по вертикали. Необходимо проработать отображение '
         'раздела табельного учёта в мобильной версии: кнопка включения перекрёстной '
         'подсветки должна быть убрана (её функционал не реализуется в мобильной '
         'версии); два окна с мероприятиями и нормами должны быть изначально скрыты; '
         'итоги учёта должны открываться на новой странице под названием "Итоги '
         'учёта" и с тремя шевронами в верхнем баре, а таблица данных должна быть с '
         'фамилиями сотрудников; при прокрутке по горизонтали шахматки табеля учёта '
         'и таблицы итогов учёта, столбцы с фамилиями сотрудников должны сужаться до '
         'отображения первых четырёх букв фамилий.» 1) КНОПКА «ВИД»: svg-иконки '
         'wsViewIconFull/Shift/Day УДАЛЕНЫ из #wsViewBtn — ТОЛЬКО текст «Вид» '
         '(span.ws-view-label 13px/600); _updateViewBtn не трогает иконки '
         '(aria-label «Переключение вида табеля: сейчас <вид>», замок '
         'ws-view-locked, подсказка #wsViewTip, тосты cycleView — живы); CSS '
         '.ws-view-btn svg удалён [width auto + паддинги 0 9px — как было]. '
         '2) КАРТОЧКА ПРИБОРА (.dev-detail-top — картинка + «№ прибора» + «Место '
         'установки») НЕ прокручивается по вертикали: МОБАЙЛ — '
         '#page-device-detail .dev-detail-top { position: sticky; top: 56px; '
         'z-index: 5; box-shadow } [липкая шапка страницы 56px; тень отделяет от '
         'прокручиваемого .dev-detail-rows]; ДЕСКТОП-ПАНЕЛЬ — #detailPanel '
         '.dev-detail-top { position: sticky; top: 0; margin: 0 -16px; '
         'padding-left: 16px } [скролл-зона .detail-panel-body padding 16px: '
         'full-bleed по ширине, картинка на прежнем месте, контент не '
         '«просвечивает» по бокам]; ДИАГНОСТИКА (браузер, мок-логин): computed '
         'overflow #page-device-detail = «hidden auto» — правило «мобильной '
         'защиты» #contentArea > .page-content.active { overflow-y: auto } '
         'делает АКТИВНУЮ страницу скролл-контейнером → sticky привязан к ней '
         '(height auto — не прокручивается) вместо html → НЕ работает (замер '
         'top=-844); ФИКС: #contentArea > #page-device-detail.page-content.active '
         '{ overflow: visible } [специфичность 2×ID выше; скролл страницы — '
         'документом html, как у остальных страниц; замер после фикса top=56]. '
         '3) МОБИЛЬНЫЙ ТАБЕЛЬ: #wsCrossBtn { display: none } только ≤1023px '
         '[перекрестье — НАВЕДЕНИЕ курсора, на сенсоре не реализуется; десктоп '
         'без изменений]; окна «Мероприятия»/#wsEventsPanel и «Нормы»/#wsCalPanel '
         'ИЗНАЧАЛЬНО СКРЫТЫ: #page-work-schedule:not(.ws-mob-events-on) '
         '#wsEventsPanel { display: none } (:not(.ws-mob-norms-on) #wsCalPanel), '
         'только ≤1023px; РАСКРЫТИЕ — чипы .ws-mob-chips #wsMobChips («Мероприятия» '
         '#wsChipEvents / «Нормы» #wsChipNorms, только мобайл display: flex): '
         'toggleMobPanel(name) — тоггл класса ws-mob-events-on / ws-mob-norms-on '
         'на #page-work-schedule + aria-pressed чипа (+вибро); начальное '
         'состояние — ВСЕГДА свёрнуто (каждый заход); чипы — стиль кнопок тулбара '
         '(прямые углы, 13px/600), активный — акцент rgba(74,143,199,0.22)/светлая '
         '0.16 + #6aa6e0/#1a4060. 4) ИТОГИ УЧЁТА — МОБИЛЬНАЯ СТРАНИЦА #page-ws-totals '
         '[НЕ шторка]: шапка page-inline-header (шеврон chevronTap — '
         'многострелочный, заголовок «Итоги учёта»; путь дашборд → Документация '
         'ИОС → Табель → Итоги даёт РОВНО 3 СТРЕЛКИ — browser-проверка M15), '
         'вкладки Месяц/Год страницы + тело #wsTtPageBody (класс ws-tt-body: '
         'overflow auto, фон = панели var(--bg-tertiary)/#e9e7de; .ws-tt-page: '
         'flex-колонка высотой calc(100vh − 56px − 70px − env(safe-area))); '
         'toggleTotals: matchMedia !min-1024 → navigateTo(\'ws-totals\') и return '
         '[гейт вида (сменный/дневной — итоги недоступны) действует и для '
         'страницы]; navigateTo: хук открытия (setTimeout 30 → '
         'WorkSchedule.onTotalsPageOpen) + уход с ws-totals → onTotalsPageClose '
         '[флаг _ttPage]; onTotalsPageOpen: _ttPage=true, активная вкладка '
         'страницы, _renderTotals, _reapplyEmpNarrow; РЕНДЕР В СТРАНИЦУ: '
         '_ttBodyEl() — при открытом _ttPage отдаёт #wsTtPageBody, иначе '
         '#wsTtBody [используют _renderTotalsMonth/_renderTotalsYear/'
         '_renderTotalsYearTable (гварды typeof для VM-моков) и _rowClass]; '
         'гейты: _renderTotals/_renderTotalsIfOpen — _totalsOpen || _ttPage; '
         'setTotalsTab — синхронизация вкладок страницы (wsTtPageTabMonth/Year) '
         'и на странице НЕ делает повторный переход; доступ: '
         "_WORK_SCHEDULE_PAGES = ['work-schedule', 'ws-totals'] (права "
         'табеля, серверная матрица workschedule.view), PAGE_PARENTS '
         "['ws-totals']='work-schedule', PAGE_LABELS «Итоги учёта»; закрытие — "
         'шеврон (chevronTap: 1 тап = goBack/popstate → табель, 2 тапа = '
         'главная) или системный «назад»; ДЕСКТОП — шторка как прежде '
         '(ws-tt-open, все синхронизации не тронуты; _fitTtDrawer/_syncTotalsRows/'
         '_applyTtHeadVar гейтятся _totalsOpen/panel.hidden — на странице тихо '
         'пропускают). 5) СУЖЕНИЕ ФАМИЛИЙ ДО 4 БУКВ: рендеры оборачивают ФИО: '
         'сетка — span.ws-emp-full [в .ws-emp-name ПОСЛЕ .ws-tab-no], итоги '
         '(месяц + yearRow года/архива) — span.ws-tt-name [в td.ws-tt-emp после '
         '.ws-tt-tabno], ОБА с data-full/data-s4 (значение — _surname4(ФИО): '
         'первые 4 буквы ПЕРВОГО слова, «Иванов Иван Иванович»→«Иван»); '
         '_attachEmpNarrow (init, однократно, passive): слушатели scroll на '
         '#wsGridWrap/#wsTtBody/#wsTtPageBody; ПОРОГ 6px (субпиксель): '
         '_narrowApply(container, on) — класс .ws-narrow на ВСЕ .ws-grid/'
         '.ws-tt-table контейнера + textContent span ⇄ data-s4/data-full; '
         '_reapplyEmpNarrow (после _renderGrid/_renderTotalsMonth/'
         '_renderTotalsYearTable): если контейнер прокручен (scrollLeft > 6) — '
         'сужение ВОССТАНАВЛИВАЕТСЯ [переживает смену месяца/«Обновить»/правки]; '
         'CSS только ≤1023px: .ws-grid.ws-narrow thead th.ws-emp-col + tbody '
         'td.ws-emp-col { width/min-width: 76px; padding 6px 4px } + скрыты '
         '.ws-tab-no и .ws-emp-pos; .ws-tt-table.ws-narrow th/td.ws-tt-emp '
         '{ width: 58px } + скрыт .ws-tt-tabno [десктоп: сетка overflow-x '
         'hidden, колонки итогов скрыты — правила бездействуют]. Верификация: '
         'тесты 2055→2087/0 [+32 tests/test-task334.js: HTML кнопки (svg нет, '
         'иконки удалены, label жив), CSS (.ws-view-btn svg удалён), VM '
         '_updateViewBtn (без иконок, names/замок живы), sticky мобайл/десктоп '
         '(computed), #wsCrossBtn none, :not-скрытие окон, чипы HTML/CSS/VM '
         '(toggleMobPanel: классы + aria-pressed + повторный тоггл), страница '
         'итогов (HTML шапка/вкладки/тело, хуки navigateTo, карты страниц, '
         'VM onTotalsPageOpen/Close + _ttBodyEl + гейты + вкладки, toggleTotals '
         'мобильная ветка, CSS компоновки), сужение (VM _surname4 ×6, '
         '_narrowApply классы+обмен, _reapplyEmpNarrow порог, _attachEmpNarrow '
         'однократность+passive, span-обёртки в рендерах, CSS 76/58, reapply '
         'вызовы, init), SW v573/v574-guard]; актуализированы под 334: '
         'test-work-schedule [task267/307/308: _WORK_SCHEDULE_PAGES + '
         'assertEqual «’work-schedule’, ’ws-totals’» ×3], test-task321 [окно '
         'regex 2600→4000 в toggleTotals — мобильная ветка удлинила начало], '
         'test-task333 [иконки: assertFalse wsViewIconFull + svg нет]; SW-бамп '
         'v572→v573 [sw.js + 33 тест-файла], assertFalse «лишний инкремент» '
         'v573→v574 в 15]; браузер scripts/task334-browser-check.py 39/39 (порт '
         '8944, 3 контекста: МОБАЙЛ 375 тёмная [M1 «Вид» текст/svg 0; M2 '
         'подсветка none; M3-M5 окна скрыты/чипы flex; M6-M8 тогглы чипов; '
         'M9-M12 сетка: прокрутка → ws-narrow + «Иван» + таб.номер none, '
         'возврат → «Иванов Иван Иванович»; M13-M17 итоги СТРАНИЦЕЙ: «Итоги '
         'учёта», ТРИ шеврона, вкладки, шторка НЕ открывалась; M18-M19 таблица '
         'с фамилиями; M20-M25 год: переполнение, сужение итогов, возврат; M26 '
         'шеврон → табель, _ttPage=false; M27 синтетическая карточка прибора '
         'top=56; M28 0 ошибок], СВЕТЛАЯ [L1-L4], ДЕСКТОП 1280 [D1 подсветка '
         'видима, D2 окна-трети, D3 чипы none, D4 «Вид» без svg, D5 итоги '
         'шторкой ws-tt-open, D6 панель прибора sticky top 0, D7 0 ошибок]); '
         'регресс браузером [актуализированы под 334]: task333 36/36 [C3 — '
         'кнопка шире иконки (порог +10→>), мобайл-итоги теперь на СТРАНИЦЕ: '
         '#wsTtPageBody], task315 33/33 [чип «Мероприятия» перед замерами окон], '
         'task317 49/49 [BAR_JS colW — только ВИДИМЫЕ дети бара (ряд чипов '
         'десктоп скрыт), btns skip display:none, чипы перед мобильными '
         'замерами], task328 36/36 [O: кнопка подсветки на мобиле СКРЫТА]; '
         '0 JS-ошибок везде. ⚠️ ДЕПЛОЙ: ТОЛЬКО GitHub Pages + Ctrl+Shift+R ×1–2 '
         '(SW kipia-test-v572→v573) — Apps Script/листы НЕ трогать (только '
         'клиент). ПЕРЕНОС в kip8: НЕ выполнен — ждёт проверки пользователем '
         '[потом одной партией, k8 v419→v420]. Следующий номер задачи: 335.')
lines2 = src.split('\n')
insert_at = None
for i, l in enumerate(lines2):
    if l.startswith('- **Task 333 —'):
        insert_at = i + 1
        break
assert insert_at is not None, 'буллет Task 333 не найден'
lines2.insert(insert_at, entry)
src = '\n'.join(lines2)
print('Буллет Task 334 вставлен (после Task 333)')

with open('Системный_промт_для_приложения_КИПиА.md', 'w', encoding='utf-8') as f:
    f.write(src)
print('Готово: Системный_промт_для_приложения_КИПиА.md → post-Task 334')
