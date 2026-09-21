#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 386 — заявка пользователя (3 части, доработка Task 385):
#   1) «Кнопку легенда переименуй словом по проще, к примеру
#      "Обозначения" или как то по другому, и окно должно выезжать
#      в сокращённом виде обозначений, а при нажатии на значок с
#      шевроном - шире и с подробным наименованием кодов, а в
#      мобильной версии переход на отдельную страницу» → кнопка
#      «Обозначения» (ряд 2); шторка ДЕСКТОП выезжает УЗКОЙ (~190px:
#      свотч + код, без наименований), значок-шеврон #wsLgChv на
#      левом крае разворачивает широкую панель (min(400px, 45vw):
#      наименования + пояснения, класс ws-lg-wide, анимация width);
#      МОБИЛЬНЫЙ — отдельная страница #page-ws-legend (паттерн
#      итогов Task 334), оверлей-шторка удалена. Попутно исправлен
#      латентный баг Task 385: замер inner.getBoundingClientRect
#      при свёрнутом слоте ловил flex-сжатие inner до min-content —
#      шторка открывалась урезанной (~186px вместо 400); теперь
#      inner flex:none и ширины ЯВНЫЕ (_legendWidthPx);
#   2) «В шапке столбцов работников переименуй "Работник +" в
#      "Работники" и убери функцию кнопки, просто надпись, кнопка
#      теперь только в баре» → заголовок th — ПРОСТО надпись
#      «Работники» (без ws-emp-head-add/onclick/плюсика; правила
#      CSS кнопки удалены); вход на страницу — только кнопка
#      «Работники» в ряду 1;
#   3) «На странице работники переименуй кнопку "+" в "Добавить
#      работника"» → текстовая кнопка (стиль адаптирован: авто-
#      ширина, 34px высота), пустое состояние переозвучено.
#
# SW-бамп отдельным скриптом: task386-bump-sw.py (v613 → v614).

import sys

INDEX = 'index.html'


def patch(path, repls):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    for name, old, new, cnt in repls:
        found = s.count(old)
        assert found == cnt, (
            '%s: [%s] найдено %d вхождений (ожидалось %d)' % (path, name, found, cnt))
        assert old != new, '%s: [%s] замена пуста' % (path, name)
        s = s.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    print('%s: применено правок: %d' % (path, len(repls)))


repls = []
R = repls.append

# ============================================================
# 1. CSS: шторка «Обозначения» — два вида + шеврон + страница
# ============================================================

# 1a. Комментарий блока + drawer/inner (flex:none, 190px, wide)
R(('CSS: легенда — шапка блока + drawer/inner', '''    /* ============================================================
       Task 385 (заявка, часть 1): ШТОРКА «ЛЕГЕНДА» — окно с
       подробным описанием всех сокращений шахматки табеля, по
       принципу окна итогов учёта: кнопка-переключатель «Легенда»
       в ряду 2 тулбара; ДЕСКТОП — панель выезжает СПРАВА
       (margin-right 0.28s, сетка сжимается, дни прокручиваются
       под ней), МОБАЙЛ — fixed-оверлей ~86vw со скруглением и
       тенью (как итоги, Task 334). Контент — коды дней Т-12/Т-13
       и коды мероприятий из справочника «Коды_статусов» (живые
       цвета ячеек) + обозначения вёрстки. Взаимоисключающая с
       «Итогами учёта» (открытие закрывает другую шторку) */
    .ws-legend-drawer {
        flex: none;
        position: relative;
        width: 0;             /* до первого открытия (панель скрыта) */
        max-width: 45%;
        overflow: hidden;
        display: flex;
        transition: margin-right 0.28s ease;
    }
    .ws-legend-inner {
        width: min(400px, 45vw);  /* фикс-ширина: маржу мерит JS */
        display: flex;
        flex-direction: column;
        min-height: 0;
        background: var(--bg-tertiary, #0e1621);
    }
''', '''    /* ============================================================
       Task 385 → 386 (заявка): ШТОРКА «ОБОЗНАЧЕНИЯ» — окно
       расшифровки сокращений шахматки табеля по принципу окна
       итогов учёта: кнопка-переключатель «Обозначения» (ряд 2);
       ДЕСКТОП — панель выезжает СПРАВА (margin-right 0.28s, сетка
       сжимается, дни прокручиваются под ней). Task 386 — ДВА
       ВИДА: выезжает в СОКРАЩЁННОМ виде (~190px: свотч + код, без
       наименований — .ws-lg-name скрыт), значок-шеврон #wsLgChv
       на левом крае разворачивает ШИРОКУЮ панель (min(400px,
       45vw): наименования кодов + пояснения вёрстки; класс
       .ws-lg-wide на шторке, анимация width 0.28s у drawer и
       inner). inner — flex: none, НЕ сжимается: Task 385 мерил
       getBoundingClientRect при свёрнутом слоте — inner пригибался
       flex-сжатием до min-content (~186px), шторка открывалась
       урезанной; теперь ширины ЯВНЫЕ (_legendWidthPx). МОБАЙЛ —
       ОТДЕЛЬНАЯ СТРАНИЦА #page-ws-legend (как итоги Task 334),
       оверлея-шторки на мобильном больше НЕТ (display: none).
       Контент — коды дней Т-12/Т-13 и коды мероприятий из
       справочника «Коды_статусов» (живые цвета ячеек) +
       обозначения вёрстки (развёрнутый вид). Взаимоисключающая с
       «Итогами учёта» (открытие закрывает другую шторку) */
    .ws-legend-drawer {
        flex: none;
        position: relative;
        width: 0;             /* до первого открытия (панель скрыта) */
        max-width: 45%;
        overflow: hidden;
        display: flex;
        transition: margin-right 0.28s ease, width 0.28s ease;
    }
    .ws-legend-inner {
        flex: none;           /* НЕ сжимается flex-сжатием (Task 386) */
        width: 190px;         /* сокращённый вид: только коды */
        display: flex;
        flex-direction: column;
        min-height: 0;
        background: var(--bg-tertiary, #0e1621);
        transition: width 0.28s ease;
    }
    .ws-legend-drawer.ws-lg-wide .ws-legend-inner {
        width: min(400px, 45vw);  /* развёрнутый вид: с наименованиями */
    }
''', 1))

# 1b. Значок-шеврон на левом крае (после светлой темы бортика)
R(('CSS: значок-шеврон ws-lg-chv', '''    [data-theme="light"] .ws-lg-edge {
        background: linear-gradient(180deg, #b7c3d1, #8fa0b4);
    }
    .ws-lg-head {
''', '''    [data-theme="light"] .ws-lg-edge {
        background: linear-gradient(180deg, #b7c3d1, #8fa0b4);
    }
    /* Task 386: значок-ШЕВРОН на левом крае шторки (как #wsTtChv
       итогов, Task 329): узкая шторка — стрелка ВЛЕВО (‹ — «рас-
       крыть панель шире, с наименованиями»), развёрнутая —
       доворачивается на 180° (› — «свернуть к кодам»). Полупроз-
       рачная заливка: слегка просвечивает накрытая ячейка сетки */
    .ws-lg-chv {
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        z-index: 6;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 11px;
        height: 48px;
        padding: 0;
        box-sizing: border-box;
        color: var(--text-secondary, rgba(255,255,255,0.65));
        background: rgba(21, 32, 47, 0.55);
        border: 1px solid var(--card-border, rgba(255,255,255,0.12));
        border-left: none;        /* примыкает к бортику края */
        border-radius: 0 6px 6px 0;
        cursor: pointer;
    }
    .ws-lg-chv:hover {
        color: var(--text-primary, #e0e0e0);
        background: rgba(21, 32, 47, 0.85);
    }
    .ws-lg-chv[aria-pressed="true"] {
        color: #9ec9e8;
        background: rgba(74, 143, 199, 0.35);
        border-color: rgba(74, 143, 199, 0.5);
    }
    .ws-lg-chv:active { opacity: 0.85; }
    .ws-lg-chv[hidden] { display: none; }
    .ws-lg-chv svg { display: block; transition: transform 0.18s ease; }
    .ws-lg-chv[aria-pressed="true"] svg { transform: rotate(180deg); }
    [data-theme="light"] .ws-lg-chv {
        color: #666;
        background: rgba(226, 232, 239, 0.6);
        border-color: rgba(0, 0, 0, 0.14);
    }
    [data-theme="light"] .ws-lg-chv:hover {
        color: #333;
        background: rgba(226, 232, 239, 0.92);
    }
    .ws-lg-head {
''', 1))

# 1c. Наименования/пояснения — только развёрнутый вид
R(('CSS: name/notesec — только широкий вид', '''    .ws-lg-code { font-weight: 700; min-width: 36px; flex: none; }
    .ws-lg-name { font-size: 12.5px; line-height: 1.35; }
    .ws-lg-note {
        font-size: 12px;
        line-height: 1.5;
        padding: 5px 6px;
        opacity: 0.92;
    }
''', '''    .ws-lg-code { font-weight: 700; min-width: 36px; flex: none; }
    /* Task 386: наименования кодов — ТОЛЬКО развёрнутый вид
       (широкая шторка / мобильная страница); узкая шторка — коды */
    .ws-lg-name { font-size: 12.5px; line-height: 1.35; display: none; }
    .ws-legend-drawer.ws-lg-wide .ws-lg-name { display: block; }
    .ws-lg-note {
        font-size: 12px;
        line-height: 1.5;
        padding: 5px 6px;
        opacity: 0.92;
    }
    /* Task 386: блок пояснений вёрстки (.ws-lg-notesec в контенте)
       — только развёрнутый вид; в узкой шторке одни коды */
    .ws-lg-notesec { display: none; }
    .ws-legend-drawer.ws-lg-wide .ws-lg-notesec { display: block; }
''', 1))

# 1d. Мобильный оверлей → страница (шторка гасится) + тело страницы
R(('CSS: мобильный оверлей удалён → display:none + страница', '''    @media (max-width: 1023px) {
        .ws-legend-drawer {
            position: fixed;
            top: 10vh;
            height: 74vh;
            width: min(86vw, 560px);
            right: 0;
            z-index: 75;
            display: flex;
            transform: translateX(100%);
            transition: transform 0.28s ease;
            border-radius: 10px 0 0 10px;
            box-shadow: -10px 0 26px rgba(0, 0, 0, 0.38);
            overflow: hidden;
        }
        .ws-legend-inner {
            width: 100%;
            border-radius: 10px 0 0 10px;
        }
        #page-work-schedule.ws-legend-open .ws-legend-drawer { transform: none; }
    }
''', '''    /* Task 386: мобильного ОВЕРЛЕЯ больше нет — обозначения на
       мобильном открываются ОТДЕЛЬНОЙ СТРАНИЦЕЙ #page-ws-legend
       (как итоги Task 334); десктопная шторка гасится целиком */
    @media (max-width: 1023px) {
        .ws-legend-drawer { display: none; }
    }
    /* Task 386: тело мобильной страницы «Обозначения» — полная
       раскладка (наименования и пояснения всегда видны: узкий
       «кодовый» вид десктопной шторки странице не нужен) */
    .ws-lg-page-body {
        padding: 6px 14px 24px;
        max-width: 560px;
        margin: 0 auto;
    }
    .ws-lg-page-body .ws-lg-name { display: block; }
    .ws-lg-page-body .ws-lg-notesec { display: block; }
''', 1))

# ============================================================
# 2. CSS: страница «Работники» — текстовая кнопка + комментарии
# ============================================================

# 2a. Комментарий блока страницы
R(('CSS: комментарий блока страницы «Работники»', '''    /* ============================================================
       Task 385 (заявка, часть 3): СТРАНИЦА «РАБОТНИКИ» — полные
       карточки (внесение/редактирование профиля, отпусков,
       мероприятий; добавление работника). Переход — кнопка
       «Работники» ряда 1 тулбара и заголовок «Работник +» шапки
       сетки (только редакторам). Карточка .ws-wcard — панель с
       внутренностями попапа шахматки (ws-popup-title/поля/секции
       тех же классов); счётчик сверху; кнопка «+» в шапке
       страницы — шторка создания #wsEmpSheet (openEmployeeForm) */
''', '''    /* ============================================================
       Task 385 → 386 (заявка): СТРАНИЦА «РАБОТНИКИ» — полные
       карточки (внесение/редактирование профиля, отпусков,
       мероприятий; добавление работника). Переход — ТОЛЬКО кнопка
       «Работники» ряда 1 тулбара (редакторам; Task 386: заголовок
       шапки сетки — просто надпись). Карточка .ws-wcard — панель с
       внутренностями попапа шахматки (ws-popup-title/поля/секции
       тех же классов); счётчик сверху; кнопка «Добавить работника»
       в шапке страницы (Task 386: прежде значок «+») — шторка
       создания #wsEmpSheet (openEmployeeForm) */
''', 1))

# 2b. Кнопка «Добавить работника» — текстовая (прежде «+» 34×34)
R(('CSS: ws-workers-add — текстовая кнопка', '''    .ws-workers-add {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.06);
        color: inherit;
        font-size: 20px;
        line-height: 1;
        font-weight: 700;
        cursor: pointer;
        flex: none;
    }
''', '''    /* Task 386 (заявка): «Добавить работника» — ТЕКСТОВАЯ кнопка
       (прежде значок «+» 34×34): та же высота 34px, авто-ширина,
       нейтральный стиль в духе кнопок тулбара */
    .ws-workers-add {
        height: 34px;
        padding: 0 12px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.06);
        color: inherit;
        font-size: 13px;
        line-height: 1;
        font-weight: 600;
        white-space: nowrap;
        cursor: pointer;
        flex: none;
    }
''', 1))

# 2c. Суженный вид шапки: плюсика больше нет (правило удалено)
R(('CSS: narrow — плюсик удалён', '''        /* Task 335 (заявка): шапка «Сотрудник +» в суженном виде —
           «Сотр»: текст меняется span-обменом (data-full/data-s4
           в _renderGrid), плюсик-индикатор добавления скрыт */
        .ws-grid.ws-narrow thead th.ws-emp-col .ws-emp-head-plus {
            display: none;
        }
    }
''', '''        /* Task 335 → 386: шапка «Работники» в суженном виде — «Рабо»:
           текст меняется span-обменом (data-full/data-s4 в
           _renderGrid); плюсика-индикатора больше нет (заголовок —
           надпись, Task 386) */
    }
''', 1))

# 2d. Правила кнопки-заголовка (Task 311/318/330) — удалены
R(('CSS: правила ws-emp-head-add/plus удалены', '''    /* Task 311: заголовок «Сотрудник» — КНОПКА добавления сотрудника
       (кнопка «+ Сотрудник» из тулбара удалена по заявке). Класс
       ws-emp-head-add вешается в _renderGrid только ролям с правом
       правки: плюсик-индикатор акцентом у текста, курсор-палец и
       подсветка при наведении; клик открывает шторку #wsEmpSheet
       (openEmployeeForm — внутри ещё проверка _canEdit). Зрителям —
       обычный заголовок без клика.
       Task 318: подсветка — СПЛОШНОЙ цвет, как у ячеек ФИО под
       шапкой (td.ws-emp-col:hover #15202f/#e2e8ef). Заголовок —
       sticky: прежний ПОЛУПРОЗРАЧНЫЙ rgba-фон на hover делал поле
       прозрачным (сквозь него просвечивало прокручиваемое тело
       таблицы — фон «исчезал»); теперь фон МЕНЯЕТ ЦВЕТ, оставаясь
       непрозрачным. */
    .ws-grid thead th.ws-emp-col.ws-emp-head-add { cursor: pointer; }
    .ws-grid thead th.ws-emp-col.ws-emp-head-add:hover {
        /* Task 330: hover светлее новой сине-серой шапки #1e293b
           (прежде #15202f — был светлее старого фона #0e1621) */
        background: #2a3a4c;
        color: var(--text-primary, #e0e0e0);
    }
    .ws-grid thead th.ws-emp-col .ws-emp-head-plus {
        font-style: normal;
        font-weight: 700;
        color: var(--accent-blue, #4a8fc7);
        margin-left: 6px;
    }
    [data-theme="light"] .ws-grid thead th.ws-emp-col.ws-emp-head-add:hover {
        background: #e2e8ef;
    }
''', '''    /* Task 311 → 385 → 386 (заявка): заголовок «Работники» — ПРОСТО
       надпись: правила кнопки (курсор-палец, hover-подсветка
       Task 318/330, плюсик-индикатор ws-emp-head-plus Task 311)
       УДАЛЕНЫ — переход на страницу «Работники» выполняет только
       кнопка «Работники» в баре (ряд 1). Сужение текста при
       горизонтальной прокрутке — span-обмен data-full/data-s4
       (Task 335) */
''', 1))

# 2e. Комментарий Task 311 у тулбара (упоминание ws-emp-head-add)
R(('CSS: комментарий Task 308/311 у тулбара', '''       Task 311: «+ Сотрудник» из тулбара УБРАНА — её функцию
       выполняет заголовок «Сотрудник» в шапке шахматки
       (.ws-emp-head-add).
''', '''       Task 311: «+ Сотрудник» из тулбара УБРАНА — её функцию
       выполнял заголовок в шапке шахматки (Task 386: заголовок —
       просто надпись «Работники», добавление — кнопкой «Добавить
       работника» на странице «Работники»).
''', 1))

# ============================================================
# 3. HTML: кнопка «Обозначения», шторка с шевроном, страницы
# ============================================================

# 3a. Кнопка ряда 2: «Легенда» → «Обозначения»
R(('HTML: кнопка «Обозначения» в ряду 2', '''                        <!-- Task 385: кнопка-переключатель «Легенда» —
                             окно расшифровки всех сокращений шахматки
                             (справа, по принципу шторки итогов).
                             Видна всем ролям (просмотр); открытие
                             закрывает открытые итоги — окна бара
                             взаимоисключающие -->
                        <button type="button" id="wsLegendBtn" class="ws-totals-btn ws-legend-btn" onclick="WorkSchedule.toggleLegend()" aria-pressed="false">Легенда</button>
''', '''                        <!-- Task 385 → 386 (заявка: «словом
                             попроще»): кнопка-переключатель «Обозна-
                             чения» — окно расшифровки сокращений
                             шахматки (справа, по принципу шторки
                             итогов). Видна всем ролям (просмотр);
                             ДЕСКТОП: выезжает в СОКРАЩЁННОМ виде
                             (коды без наименований), значок-шеврон на
                             крае шторки разворачивает широкую панель
                             с наименованиями (Task 386); МОБАЙЛ:
                             переход на отдельную страницу
                             #page-ws-legend (как «Итоги учёта»,
                             Task 334). Открытие закрывает открытые
                             итоги — окна бара взаимоисключающие -->
                        <button type="button" id="wsLegendBtn" class="ws-totals-btn ws-legend-btn" onclick="WorkSchedule.toggleLegend()" aria-pressed="false">Обозначения</button>
''', 1))

# 3b. Комментарий кнопки «Работники» ряда 1 (Task 385 → 386)
R(('HTML: комментарий кнопки «Работники»', '''                    <!-- Task 385: кнопка «Работники» — переход на
                         страницу полных карточек #page-ws-workers
''', '''                    <!-- Task 385 → 386: кнопка «Работники» — переход на
                         страницу полных карточек #page-ws-workers
''', 1))

# 3c. Комментарий Task 311 после кнопки (функция переехала)
R(('HTML: комментарий Task 311 у тулбара', '''                    <!-- Task 311: кнопка «+ Сотрудник» УДАЛЕНА из тулбара
                         (Task 307 приносил её сюда со страницы
                         «Сотрудники»). Её функцию теперь выполняет
                         заголовок колонки «Сотрудник» в шапке сетки:
                         редакторам — клик открывает прежний bottom-sheet
                         #wsEmpSheet (openEmployeeForm, см. _renderGrid:
                         класс ws-emp-head-add + плюсик-индикатор). -->
''', '''                    <!-- Task 311: кнопка «+ Сотрудник» УДАЛЕНА из тулбара
                         (Task 307 приносил её сюда со страницы
                         «Сотрудники»). Task 386: добавление работника —
                         кнопкой «Добавить работника» в шапке страницы
                         «Работники» (заголовок шапки сетки — просто
                         надпись, функции кнопки больше не несёт). -->
''', 1))

# 3d. Шторка: заголовок «Обозначения» + значок-шеврон wsLgChv
R(('HTML: шторка — заголовок + шеврон', '''            <!-- Task 385: ШТОРКА «ЛЕГЕНДА» — окно расшифровки всех
                 сокращений шахматки (кнопка «Легенда» в ряду 2
                 тулбара; принцип — как у шторки итогов: десктоп —
                 выезжает справа, сжимая сетку; мобайл — fixed-оверлей
                 ~86vw). Контент — _renderLegendSheet: коды дней Т-12/Т-13
                 из справочника «Коды_статусов» (живые цвета), коды
                 мероприятий, обозначения вёрстки. Взаимоисключающая
                 с «Итогами учёта» -->
            <div id="wsLegendDrawer" class="ws-legend-drawer">
                <div class="ws-lg-edge" aria-hidden="true"></div>
                <div class="ws-legend-inner">
                    <div class="ws-lg-head">Сокращения в шахматке</div>
                    <div class="ws-lg-body" id="wsLegendBody"></div>
                </div>
            </div>
''', '''            <!-- Task 385 → 386: ШТОРКА «ОБОЗНАЧЕНИЯ» — окно
                 расшифровки сокращений шахматки (кнопка «Обозначения»
                 в ряду 2 тулбара; принцип — как у шторки итогов:
                 десктоп — выезжает справа, сжимая сетку; мобильного
                 оверлея больше НЕТ — страница #page-ws-legend).
                 Task 386: два вида — выезжает УЗКОЙ (коды без
                 наименований), значок-шеврон #wsLgChv на левом крае
                 разворачивает широкую панель с наименованиями и
                 пояснениями (класс ws-lg-wide на шторке). Контент —
                 _renderLegendSheet (_legendHtml): коды дней Т-12/Т-13
                 из справочника «Коды_статусов» (живые цвета), коды
                 мероприятий, обозначения вёрстки. Взаимоисключающая
                 с «Итогами учёта» -->
            <div id="wsLegendDrawer" class="ws-legend-drawer">
                <div class="ws-lg-edge" aria-hidden="true"></div>
                <!-- Task 386: значок-шеврон разворачивает панель ШИРЕ
                     (подробные наименования кодов); свёрнутая шторка —
                     стрелка влево, развёрнутая доворачивается на 180°;
                     виден только при открытой шторке (hidden снимает
                     _setLegend) -->
                <button type="button" id="wsLgChv" class="ws-lg-chv" onclick="WorkSchedule.toggleLegendWide()" hidden aria-pressed="false" aria-label="Показать подробные наименования кодов">
                    <svg width="7" height="12" viewBox="0 0 7 12" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M5.5 1 L1 6 L5.5 11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <div class="ws-legend-inner">
                    <div class="ws-lg-head">Обозначения</div>
                    <div class="ws-lg-body" id="wsLegendBody"></div>
                </div>
            </div>
''', 1))

# 3e. Страница «Работники»: кнопка «Добавить работника» + НОВАЯ
#     мобильная страница «Обозначения» (после workers)
R(('HTML: страница работников + страница «Обозначения»', '''        <!-- ============ Task 385: СТРАНИЦА «РАБОТНИКИ» — полные
             карточки (переход — кнопка «Работники» в ряду 1 тулбара
             табеля и заголовок «Работник +» шапки сетки; только
             редакторам). Карточка каждого работника: профиль,
             отпуска года (✎/✕/«+ Отпуск…»), мероприятия месяца
             (✎/✕/«+ Мероприятие…»), «Правка данных…» (шторка
             #wsEmpSheet, таб. № — readonly PK) и «Уволить…» — всё,
             что до Task 385 жило в карточке шахматки (попап стал
             чисто информационным). Рендер — _renderWorkersPage
             (порядок — как строки шахматки); данные обновляются
             вместе с сеткой (loadGrid(true) → _renderGrid →
             _renderWorkersIfOpen); «+» в шапке — шторка создания
             (openEmployeeForm) -->
        <div id="page-ws-workers" class="page-content">
            <div class="page-inline-header">
                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Работники</div>
                <button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">+</button>
            </div>
            <div id="wsWorkersBody" class="ws-workers-body"></div>
        </div>
''', '''        <!-- ============ Task 385 → 386: СТРАНИЦА «РАБОТНИКИ» —
             полные карточки (переход — ТОЛЬКО кнопка «Работники» в
             ряду 1 тулбара табеля, редакторам; Task 386: заголовок
             шапки сетки — просто надпись). Карточка каждого
             работника: профиль, отпуска года (✎/✕/«+ Отпуск…»),
             мероприятия месяца (✎/✕/«+ Мероприятие…»), «Правка
             данных…» (шторка #wsEmpSheet, таб. № — readonly PK) и
             «Уволить…» — всё, что до Task 385 жило в карточке
             шахматки (попап стал чисто информационным). Рендер —
             _renderWorkersPage (порядок — как строки шахматки);
             данные обновляются вместе с сеткой (loadGrid(true) →
             _renderGrid → _renderWorkersIfOpen); «Добавить
             работника» в шапке (Task 386: прежде значок «+») —
             шторка создания (openEmployeeForm) -->
        <div id="page-ws-workers" class="page-content">
            <div class="page-inline-header">
                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Работники</div>
                <!-- Task 386 (заявка): текстовая кнопка «Добавить
                     работника» (прежде — значок «+») -->
                <button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">Добавить работника</button>
            </div>
            <div id="wsWorkersBody" class="ws-workers-body"></div>
        </div>

        <!-- ============ Task 386 (заявка): МОБИЛЬНАЯ СТРАНИЦА
             «ОБОЗНАЧЕНИЯ» — расшифровка сокращений шахматки. На
             мобильном (≤1023px) кнопка «Обозначения» тулбара табеля
             УХОДИТ на ЭТУ страницу (toggleLegend →
             navigateTo('ws-legend')), а НЕ открывает боковую шторку
             (шторка с двумя видами — десктопное поведение; паттерн
             мобильной страницы итогов Task 334). Шапка — как у
             остальных страниц: ЛИПКИЙ БАР с многострелочным шевроном
             «Назад» и заголовком «Обозначения». Контент — тот же
             _legendHtml (ПОЛНАЯ форма: коды с наименованиями +
             пояснения вёрстки — на странице места хватает, узкий
             «кодовый» вид десктопной шторки не нужен). Закрытие —
             шеврон/системный «назад» (popstate) либо переход на
             любую страницу -->
        <div id="page-ws-legend" class="page-content">
            <div class="page-inline-header"><div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div><div class="page-inline-header-title">Обозначения</div></div>
            <div id="wsLgPageBody" class="ws-lg-page-body"></div>
        </div>
''', 1))

# ============================================================
# 4. Регистрация страницы ws-legend: хук + карты + доступ
# ============================================================

# 4a. navigateTo-хук
R(('JS: хук navigateTo ws-legend', '''        // Task 385: страница «Работники» — рендер полных карточек
        // после активации (прямой заход по URL/возврат на страницу)
        if (page === 'ws-workers') {
            setTimeout(() => { if (typeof WorkSchedule !== 'undefined' && WorkSchedule.onWorkersPageOpen) WorkSchedule.onWorkersPageOpen(); }, 30);
        }
''', '''        // Task 385: страница «Работники» — рендер полных карточек
        // после активации (прямой заход по URL/возврат на страницу)
        if (page === 'ws-workers') {
            setTimeout(() => { if (typeof WorkSchedule !== 'undefined' && WorkSchedule.onWorkersPageOpen) WorkSchedule.onWorkersPageOpen(); }, 30);
        }
        // Task 386: мобильная страница «Обозначения» — рендер
        // расшифровки кодов после активации (паттерн ws-workers)
        if (page === 'ws-legend') {
            setTimeout(() => { if (typeof WorkSchedule !== 'undefined' && WorkSchedule.onLegendPageOpen) WorkSchedule.onLegendPageOpen(); }, 30);
        }
''', 1))

# 4b. PAGE_PARENTS
R(('JS: PAGE_PARENTS + ws-legend', '''        // Task 385: страница «Работники» — дочь табеля (полные
        // карточки; крошки: … / Табель учёта рабочего времени /
        // Работники)
        'ws-workers':               'work-schedule',
''', '''        // Task 385: страница «Работники» — дочь табеля (полные
        // карточки; крошки: … / Табель учёта рабочего времени /
        // Работники)
        'ws-workers':               'work-schedule',
        // Task 386: мобильная страница «Обозначения» — дочь табеля
        // (крошки: … / Табель учёта рабочего времени / Обозначения)
        'ws-legend':                'work-schedule',
''', 1))

# 4c. PAGE_LABELS
R(('JS: PAGE_LABELS + ws-legend', '''        // Task 385: страница полных карточек работников
        'ws-workers':               'Работники',
''', '''        // Task 385: страница полных карточек работников
        'ws-workers':               'Работники',
        // Task 386: мобильная страница расшифровки сокращений
        'ws-legend':                'Обозначения',
''', 1))

# 4d. _WORK_SCHEDULE_PAGES
R(('JS: _WORK_SCHEDULE_PAGES + ws-legend', '''        // Task 334: + мобильная страница итогов учёта (те же права,
        // что у табеля — доступ наследуют все роли с workschedule.view)
        // Task 385: + страница «Работники» (полные карточки; кнопки
        // правки внутри — только редакторам workschedule.edit)
        _WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers'],
''', '''        // Task 334: + мобильная страница итогов учёта (те же права,
        // что у табеля — доступ наследуют все роли с workschedule.view)
        // Task 385: + страница «Работники» (полные карточки; кнопки
        // правки внутри — только редакторам workschedule.edit)
        // Task 386: + мобильная страница «Обозначения» (расшифровка
        // кодов шахматки — доступ как у табеля, всем уровням)
        _WORK_SCHEDULE_PAGES: ['work-schedule', 'ws-totals', 'ws-workers', 'ws-legend'],
''', 1))

# ============================================================
# 5. JS: механика шторки (ширины/шеврон/страница) + контент
# ============================================================

# 5a. Esc-комментарий
R(('JS: комментарий Esc', '''                    // Task 385: Esc закрывает и шторку «Легенда»
''', '''                    // Task 385 → 386: Esc закрывает и шторку
                    // «Обозначения» (десктоп; на мобильном — страница)
''', 1))

# 5b. _setLegend + новые _legendWidthPx/toggleLegendWide/_applyLegendWide
R(('JS: _setLegend + широкие методы', '''        // Task 385: ШТОРКА «ЛЕГЕНДА» — открытие/закрытие. Десктоп:
        // панель #wsLegendDrawer едет справа margin-right'ом (как
        // итоги: замер фикс-ширины inner → старт за краем → 0);
        // мобайл: transform-оверлей (класс ws-legend-open на
        // странице). Открытие закрывает итоги (взаимоисключающие
        // окна бара); закрытие — повторный клик/Esc
        _setLegend: function(open) {
            this._legendOpen = !!open;
            var btn = document.getElementById('wsLegendBtn');
            if (btn && btn.setAttribute) {
                btn.setAttribute('aria-pressed', open ? 'true' : 'false');
            }
            var page = document.getElementById('page-work-schedule');
            if (page && page.classList) {
                if (open) page.classList.add('ws-legend-open');
                else page.classList.remove('ws-legend-open');
            }
            if (open) this._renderLegendSheet();
            var drawer = document.getElementById('wsLegendDrawer');
            if (!drawer) return;
            var desktop = (typeof window !== 'undefined' && window.matchMedia
                && window.matchMedia('(min-width: 1024px)').matches);
            if (desktop) {
                // ширина = фикс-ширина inner (не зависит от нулевой
                // ширины свёрнутого drawer); открытие: старт за
                // правым краем, синхронный reflow, анимация к 0
                var inner = drawer.querySelector
                    ? drawer.querySelector('.ws-legend-inner') : null;
                var w = (inner && inner.getBoundingClientRect)
                    ? Math.ceil(inner.getBoundingClientRect().width) : 0;
                if (open) {
                    drawer.style.width = w + 'px';
                    drawer.style.marginRight = (-w) + 'px';
                    void drawer.offsetWidth;
                    drawer.style.marginRight = '0px';
                } else {
                    // уезжает за край анимацией (ширина остаётся —
                    // контент под overflow:hidden, flex-слот = 0)
                    drawer.style.marginRight = (-w) + 'px';
                }
                this._fitGrid();
            } else {
                drawer.style.width = '';
                drawer.style.marginRight = '';
            }
        },
''', '''        // Task 385 → 386: ШТОРКА «ОБОЗНАЧЕНИЯ» — открытие/закрытие
        // (ДЕСКТОП: мобильного оверлея больше нет — страница
        // ws-legend). Панель #wsLegendDrawer едет справа
        // margin-right'ом (как итоги: старт за краем → 0); Task 386:
        // ширина слота — ЯВНАЯ (_legendWidthPx: узкий вид 190px /
        // широкий min(400px, 45vw) по _legendWide; прежний замер
        // inner.getBoundingClientRect при свёрнутом слоте ловил
        // flex-сжатие inner до min-content ~186px — шторка
        // открывалась урезанной). Значок-шеврон #wsLgChv показы-
        // вается вместе со шторкой (hidden); класс ws-lg-wide
        // (широкий вид) применяет _applyLegendWide. Открытие
        // закрывает итоги (взаимоисключающие окна бара); закрытие —
        // повторный клик/Esc
        _setLegend: function(open) {
            this._legendOpen = !!open;
            var btn = document.getElementById('wsLegendBtn');
            if (btn && btn.setAttribute) {
                btn.setAttribute('aria-pressed', open ? 'true' : 'false');
            }
            var chv = document.getElementById('wsLgChv');
            if (chv) chv.hidden = !open;
            if (open) this._renderLegendSheet();
            var drawer = document.getElementById('wsLegendDrawer');
            if (!drawer) return;
            var desktop = (typeof window !== 'undefined' && window.matchMedia
                && window.matchMedia('(min-width: 1024px)').matches);
            if (desktop) {
                // класс вида (узкий/широкий) + слот-ширина — до
                // margin-механики; затем: старт за правым краем,
                // синхронный reflow, анимация к 0 (как итоги)
                if (open) this._applyLegendWide();
                var w = this._legendWidthPx();
                if (open) {
                    drawer.style.marginRight = (-w) + 'px';
                    void drawer.offsetWidth;
                    drawer.style.marginRight = '0px';
                } else {
                    // уезжает за край анимацией (ширина остаётся —
                    // контент под overflow:hidden, flex-слот = 0)
                    drawer.style.marginRight = (-w) + 'px';
                }
                this._fitGrid();
            } else {
                drawer.style.width = '';
                drawer.style.marginRight = '';
            }
        },

        // Task 386: целевая фикс-ширина шторки «Обозначения»:
        // узкий вид (коды без наименований) — 190px; широкий
        // (наименования + пояснения) — min(400px, 45vw); согласо-
        // вано с CSS-правилом .ws-legend-drawer.ws-lg-wide inner
        _legendWidthPx: function() {
            var vw = (typeof window !== 'undefined' && window.innerWidth)
                ? window.innerWidth : 1280;
            return this._legendWide
                ? Math.max(190, Math.min(400, Math.floor(vw * 0.45)))
                : 190;
        },

        // Task 386 (заявка): значок-ШЕВРОН на левом крае шторки —
        // развернуть панель ШИРЕ с подробными наименованиями кодов
        // (повторный клик — назад, к одним кодам). Гейт _legendOpen:
        // по скрытому (за краем) значку кликнуть нельзя, но метод
        // публичный — защита и от программных вызовов
        toggleLegendWide: function() {
            if (!this._legendOpen) return;
            this._legendWide = !this._legendWide;
            this._applyLegendWide();
        },

        // применение вида шторки: класс ws-lg-wide (CSS: ширина
        // inner, показ .ws-lg-name/.ws-lg-notesec), aria-состояние
        // значка-шеврона, слот-ширина drawer (анимация width 0.28s
        // — transition на drawer и inner), перегонка сетки
        _applyLegendWide: function() {
            var drawer = document.getElementById('wsLegendDrawer');
            var btn = document.getElementById('wsLgChv');
            if (btn && btn.setAttribute) {
                btn.setAttribute('aria-pressed', this._legendWide ? 'true' : 'false');
                btn.setAttribute('aria-label', this._legendWide
                    ? 'Только коды (свернуть наименования)'
                    : 'Показать подробные наименования кодов');
            }
            if (!drawer) return;
            if (drawer.classList) {
                if (this._legendWide) drawer.classList.add('ws-lg-wide');
                else drawer.classList.remove('ws-lg-wide');
            }
            drawer.style.width = this._legendWidthPx() + 'px';
            this._fitGrid();
        },
''', 1))

# 5c. toggleLegend: мобильная ветка — страница ws-legend
R(('JS: toggleLegend — мобильная страница', '''        toggleLegend: function() {
            // взаимоисключающие окна бара: открытые итоги
            // закрываются ПОЛНЫМ путём toggleTotals (он снимет и
            // классы, и маржу; сам toggleTotals легенду не зовёт —
            // рекурсии нет)
            if (this._totalsOpen) this.toggleTotals();
            this._setLegend(!this._legendOpen);
        },
''', '''        toggleLegend: function() {
            // взаимоисключающие окна бара: открытые итоги
            // закрываются ПОЛНЫМ путём toggleTotals (он снимет и
            // классы, и маржу; сам toggleTotals легенду не зовёт —
            // рекурсии нет)
            if (this._totalsOpen) this.toggleTotals();
            // Task 386 (заявка): на МОБИЛЬНОМ обозначения откры-
            // ваются ОТДЕЛЬНОЙ СТРАНИЦЕЙ #page-ws-legend («Обозна-
            // чения», шапка с многострелочным шевроном), НЕ
            // шторкой — паттерн мобильных итогов Task 334. Повтор-
            // ный тап кнопки на странице табеля невозможен (кнопка
            // на другой странице); «закрытие» — шеврон/системный
            // «назад». Доступа-гейта нет: обозначения — всем
            if (typeof window !== 'undefined' && window.matchMedia
                    && !window.matchMedia('(min-width: 1024px)').matches) {
                if (typeof navigateTo === 'function') navigateTo('ws-legend');
                return;
            }
            this._setLegend(!this._legendOpen);
        },
''', 1))

# 5d. Контент: _legendHtml + шторка + страница (пояснения в notesec)
R(('JS: _legendHtml/_renderLegendSheet/onLegendPageOpen', '''        // Task 385: контент шторки «Легенда» — все сокращения
        // шахматки: коды дней Т-12/Т-13 и коды мероприятий из
        // справочника «Коды_статусов» (живые цвета ячеек — свотчи),
        // затем — обозначения вёрстки (бейдж плановой смены,
        // «сегодня», рамки выходных, праздники в отпусках)
        _renderLegendSheet: function() {
            var body = document.getElementById('wsLegendBody');
            if (!body) return;
            var html = '';
            var codes = this._STATUS_CODES || [];
            var evSet = {};
            for (var k = 0; k < (this._EVENT_CODES || []).length; k++) {
                evSet[this._EVENT_CODES[k]] = true;
            }
            var dayHtml = '', evHtml = '';
            for (var i = 0; i < codes.length; i++) {
                var c = codes[i];
                var row = '<div class="ws-lg-item"><span class="ws-lg-swatch" style="background:' +
                          this._esc(String(c.color || '#3a3a3a')) + '"></span><span class="ws-lg-code">' +
                          this._esc(String(c.code || '')) + '</span><span class="ws-lg-name">' +
                          this._esc(String(c.name || '')) + '</span></div>';
                if (evSet[String(c.code)]) evHtml += row;
                else dayHtml += row;
            }
            html += '<div class="ws-lg-sec">Коды дней (Т-12/Т-13)</div>';
            html += dayHtml ||
                '<div class="ws-lg-note">Справочник кодов ещё не загружен — нажмите «Обновить».</div>';
            html += '<div class="ws-lg-sec">Коды мероприятий</div>';
            html += evHtml ||
                '<div class="ws-lg-note">Справочник кодов ещё не загружен — нажмите «Обновить».</div>';
            html += '<div class="ws-lg-note">Код мероприятия ставится в угол ячейки ПОВЕРХ плановой смены (Д/Н); ручная правка дня сильнее.</div>';
            html += '<div class="ws-lg-sec">Обозначения в шахматке</div>';
            html += '<div class="ws-lg-note">Бейдж «Д»/«Н» в правом нижнем углу ячейки отпуска — плановая смена по циклу (только у сменных работников).</div>';
            html += '<div class="ws-lg-note">Подсветка числа и столбца — сегодняшняя дата.</div>';
            html += '<div class="ws-lg-note">Рамка 2px вокруг группы ячеек — выходные и праздники; «*» у числа (24*) — сокращённый предпраздничный день.</div>';
            html += '<div class="ws-lg-note">В отпусках: «12 дней (−2 праздн.)» — вычтены праздники (ст. 120 ТК РФ); годовой лимит — 42 дня (ст. 125 ТК РФ, до 3 частей).</div>';
            html += '<div class="ws-lg-note">Зебра строк — чередование фона по работникам; перекрестье — подсветка строки и столбца при наведении (кнопка в ряду 3).</div>';
            body.innerHTML = html;
        },
''', '''        // Task 385 → 386: контент шторки/страницы «Обозначения» —
        // все сокращения шахматки: коды дней Т-12/Т-13 и коды
        // мероприятий из справочника «Коды_статусов» (живые цвета
        // ячеек — свотчи), затем — обозначения вёрстки (бейдж
        // плановой смены, «сегодня», рамки выходных, праздники в
        // отпусках). Наименования (.ws-lg-name) и пояснения
        // (.ws-lg-notesec) показываются CSS только в РАЗВЁРНУТОМ
        // виде (класс ws-lg-wide на шторке / мобильная страница);
        // узкая шторка — одни коды
        _legendHtml: function() {
            var html = '';
            var codes = this._STATUS_CODES || [];
            var evSet = {};
            for (var k = 0; k < (this._EVENT_CODES || []).length; k++) {
                evSet[this._EVENT_CODES[k]] = true;
            }
            var dayHtml = '', evHtml = '';
            for (var i = 0; i < codes.length; i++) {
                var c = codes[i];
                var row = '<div class="ws-lg-item"><span class="ws-lg-swatch" style="background:' +
                          this._esc(String(c.color || '#3a3a3a')) + '"></span><span class="ws-lg-code">' +
                          this._esc(String(c.code || '')) + '</span><span class="ws-lg-name">' +
                          this._esc(String(c.name || '')) + '</span></div>';
                if (evSet[String(c.code)]) evHtml += row;
                else dayHtml += row;
            }
            html += '<div class="ws-lg-sec">Коды дней (Т-12/Т-13)</div>';
            html += dayHtml ||
                '<div class="ws-lg-note">Справочник кодов ещё не загружен — нажмите «Обновить».</div>';
            html += '<div class="ws-lg-sec">Коды мероприятий</div>';
            html += evHtml ||
                '<div class="ws-lg-note">Справочник кодов ещё не загружен — нажмите «Обновить».</div>';
            // Task 386: пояснения — в свёртываемом блоке .ws-lg-notesec
            // (узкая шторка прячет его целиком — остаются коды)
            html += '<div class="ws-lg-notesec">';
            html += '<div class="ws-lg-note">Код мероприятия ставится в угол ячейки ПОВЕРХ плановой смены (Д/Н); ручная правка дня сильнее.</div>';
            html += '<div class="ws-lg-sec">Обозначения в шахматке</div>';
            html += '<div class="ws-lg-note">Бейдж «Д»/«Н» в правом нижнем углу ячейки отпуска — плановая смена по циклу (только у сменных работников).</div>';
            html += '<div class="ws-lg-note">Подсветка числа и столбца — сегодняшняя дата.</div>';
            html += '<div class="ws-lg-note">Рамка 2px вокруг группы ячеек — выходные и праздники; «*» у числа (24*) — сокращённый предпраздничный день.</div>';
            html += '<div class="ws-lg-note">В отпусках: «12 дней (−2 праздн.)» — вычтены праздники (ст. 120 ТК РФ); годовой лимит — 42 дня (ст. 125 ТК РФ, до 3 частей).</div>';
            html += '<div class="ws-lg-note">Зебра строк — чередование фона по работникам; перекрестье — подсветка строки и столбца при наведении (кнопка в ряду 3).</div>';
            html += '</div>';
            return html;
        },

        // шторка (десктоп): тело #wsLegendBody
        _renderLegendSheet: function() {
            var body = document.getElementById('wsLegendBody');
            if (!body) return;
            body.innerHTML = this._legendHtml();
        },

        // Task 386: мобильная страница «Обозначения» — полный
        // контент (наименования и пояснения всегда видны: CSS
        // .ws-lg-page-body переопределяет скрытия узкой шторки);
        // хук navigateTo('ws-legend') / прямой заход по URL
        onLegendPageOpen: function() {
            var body = document.getElementById('wsLgPageBody');
            if (!body) return;
            body.innerHTML = this._legendHtml();
        },
''', 1))

# ============================================================
# 6. Шапка сетки: «Работники» — просто надпись
# ============================================================

R(('JS: _renderGrid — заголовок «Работники» (надпись)', '''            var html = '<table class="ws-grid"><thead><tr>';
            // Task 311 → 385: заголовок «Работник» — КНОПКА ПЕРЕХОДА
            // на страницу полных карточек «Работники» (Task 385:
            // внесение/правка данных переехали туда — карточка
            // шахматки стала чисто информационной): редакторам —
            // плюсик-индикатор, курсор-палец и подсветка наведения
            // (класс ws-emp-head-add), клик открывает страницу
            // (openWorkersPage); зрителям — обычный заголовок без
            // клика. Двойная защита: класс/onclick вешаются по
            // _canEdit, а сам openWorkersPage ещё раз проверяет право
            // записи. До Task 385 здесь открывалась шторка создания
            // #wsEmpSheet (Task 311) — теперь шторка открывается
            // кнопкой «+» на странице «Работники»
            var empHeadAdd = this._canEdit ? ' ws-emp-head-add' : '';
            // Task 335 (заявка): «Работник +» в суженном виде —
            // «Рабо»: текст в span с data-full/data-s4 — тот же
            // span-обмен, что у ФИО (_narrowApply); плюсик-индикатор
            // скрывается CSS (.ws-grid.ws-narrow .ws-emp-head-plus)
            html += '<th class="ws-emp-col' + empHeadAdd + '"' +
                    (this._canEdit
                        ? ' onclick="WorkSchedule.openWorkersPage()"'
                        : '') +
                    '><span class="ws-emp-head-txt" data-full="Работник" data-s4="Рабо">Работник</span>' +
                    (this._canEdit ? '<i class="ws-emp-head-plus">+</i>' : '') +
                    '</th>';
''', '''            var html = '<table class="ws-grid"><thead><tr>';
            // Task 311 → 385 → 386 (заявка): заголовок столбца —
            // ПРОСТО надпись «Работники» (без функции кнопки:
            // переход на страницу полных карточек выполняет ТОЛЬКО
            // кнопка «Работники» в баре, ряд 1). Прежде (Task 385)
            // заголовок был кнопкой перехода с плюсиком-индикатором
            // (класс ws-emp-head-add, клик openWorkersPage по
            // _canEdit); Task 311 — кнопкой создания (openEmployee-
            // Form). Сужение при горизонтальной прокрутке — прежний
            // span-обмен data-full/data-s4 («Работники» → «Рабо»,
            // Task 335, _narrowApply)
            html += '<th class="ws-emp-col">' +
                    '<span class="ws-emp-head-txt" data-full="Работники" data-s4="Рабо">Работники</span>' +
                    '</th>';
''', 1))

# ============================================================
# 7. Комментарии и мелкие строки вокруг
# ============================================================

# 7a. Комментарий wsEmpPopup (упоминание «Работник +»)
R(('JS: комментарий wsEmpPopup', '''     внесение/редактирование переехало на страницу «Работники»
     (кнопка тулбара / заголовок «Работник +»); шахматка на месяц
''', '''     внесение/редактирование переехало на страницу «Работники»
     (кнопка тулбара — единственный вход, Task 386); шахматка на месяц
''', 1))

# 7b. Комментарий openWorkersPage
R(('JS: комментарий openWorkersPage', '''        // Task 385: СТРАНИЦА «РАБОТНИКИ» — переход (кнопка тулбара
        // «Работники» в ряду 1 / заголовок «Работник +» шапки сетки).
        // Гейт _canEdit — двойная защита (кнопки видны только
        // редакторам); страница — полные карточки всех активных
        // работников с внесением/редактированием данных
''', '''        // Task 385 → 386: СТРАНИЦА «РАБОТНИКИ» — переход (кнопка
        // тулбара «Работники» в ряду 1 — ЕДИНСТВЕННЫЙ вход: Task 386
        // снял функцию кнопки с заголовка шапки сетки). Гейт
        // _canEdit — двойная защита (кнопка видна только
        // редакторам); страница — полные карточки всех активных
        // работников с внесением/редактированием данных
''', 1))

# 7c. Пустое состояние страницы «Работники»
R(('JS: пустое состояние — «Добавить работника»', '''            if (!this._EMPLOYEES || !this._EMPLOYEES.length) {
                body.innerHTML = '<div class="ws-tt-empty">Нет активных работников. ' +
                                 'Добавьте их кнопкой «+» в шапке страницы.</div>';
                return;
            }
''', '''            if (!this._EMPLOYEES || !this._EMPLOYEES.length) {
                body.innerHTML = '<div class="ws-tt-empty">Нет активных работников. ' +
                                 'Добавьте первого кнопкой «Добавить работника» в шапке страницы.</div>';
                return;
            }
''', 1))

if __name__ == '__main__':
    patch(INDEX, repls)
    print('Task 386: патч применён — «Обозначения» (кнопка/два вида/'
          'мобильная страница), шапка «Работники» (надпись),'
          ' «Добавить работника»')
