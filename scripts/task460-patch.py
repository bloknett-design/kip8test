#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 460 — патч kip8test: раздел «Плановые мероприятия» в «Документации ИОС».

Заявка: «Теперь необходимо создать новый раздел "Плановые мероприятия" в
разделе Документация ИОС. На странице нового раздела необходимо разместить
информацию в виде таблицы по образцу приложенному в файле»
(«Пример таблицы мероприятий.xlsx»).

Состав (всё КЛИЕНТСКОЕ, index.html + sw.js):
  1. CSS-блок pe-* (тёмная + светлая темы, зебра строк, скролл-обёртка);
  2. Кнопка planEventsMenuBtn на page-docs-ios (после «Табеля»);
  3. Страница page-plan-events: таблица образца — «Мероприятия» (rowspan 2)
     + «2026 год» (colspan 12) + 12 месяцев (опечатка образца «Феф.»
     исправлена на «Фев.»), группы «В начале месяца» (3 строки) /
     «В конце месяца» (5 строк), ячейки месяцев ПУСТЫЕ (как в образце);
  4. PAGE_PARENTS + PAGE_LABELS (крошки «Главная / Документация /
     Документация ИОС / Плановые мероприятия»);
  5. SUBSECTIONS (закрепление на главной, категория docs);
  6. Доступ: _KIP_IOS_PAGES + LVL_KIP8_PRO + _applyServerAccess
     (flowmeter.view без КИП ИОС) — как у страницы «Документация ИОС»;
  7. Пункт сайдбара в группе «Документация ИОС»;
  8. sw.js kipia-test-v683 → v684 + комментарий.

Метод: якорные замены с assert count==1 (паттерн taskNNN-patch.py);
при любой неудаче —_ABORT до записи файлов (дерево не портится).
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'
INDEX = ROOT + '/index.html'
SW = ROOT + '/sw.js'


def rep(text, old, new, label):
    """Замена с жёсткой проверкой единственности вхождения."""
    n = text.count(old)
    assert n == 1, 'ЯКОРЬ %s: найдено %d вхождений (нужно 1)' % (label, n)
    return text.replace(old, new, 1)


# ============================================================
# Данные таблицы (образец «Пример таблицы мероприятий.xlsx»)
# ============================================================
MONTHS = ['Янв.', 'Фев.', 'Мар.', 'Апр.', 'Май', 'Июн.',
          'Июл.', 'Авг.', 'Сен.', 'Окт.', 'Ноя', 'Дек.']
GROUPS = [
    ('В начале месяца', [
        'Проверка электроинструмента (приспособлений)',
        'Проверка СИЗ в электроустановках',
        'Проверка огнетушителей',
    ]),
    ('В конце месяца', [
        'График смен на следующий месяц',
        'Отчёт по талонам',
        'Выписка из ППР на следующий месяц',
        'Журнал учёта электрооборудования',
        'Отчёт по графику ППР',
    ]),
]

M_TDS = ''.join('<td class="pe-m"></td>' for _ in MONTHS)


def build_rows():
    out = []
    for gname, acts in GROUPS:
        out.append('                                <tr class="pe-group"><td colspan="13">%s</td></tr>' % gname)
        for a in acts:
            out.append('                                <tr class="pe-row">')
            out.append('                                    <td class="pe-name">%s</td>' % a)
            out.append('                                    ' + M_TDS)
            out.append('                                </tr>')
    return '\n'.join(out)


MONTH_THS = ''.join('<th>%s</th>' % m for m in MONTHS)

# ============================================================
# Чтение
# ============================================================
with io.open(INDEX, 'r', encoding='utf-8') as f:
    src = f.read()
with io.open(SW, 'r', encoding='utf-8') as f:
    sw = f.read()

# ============================================================
# 1. CSS-блок pe-* (перед </style>, после plan-114)
# ============================================================
CSS_ANCHOR = """        #plan114ImgContainer.plan114-rotated #plan114Img {
            transform: rotate(-90deg);
            transform-origin: top left;
            max-width: none;
        }
    }

</style>"""

CSS_BLOCK = """        #plan114ImgContainer.plan114-rotated #plan114Img {
            transform: rotate(-90deg);
            transform-origin: top left;
            max-width: none;
        }
    }

    /* ====== Task 460: «Плановые мероприятия» — таблица образца ======
       «Мероприятия × 12 месяцев» (файл «Пример таблицы мероприятий.xlsx»):
       полная сетка рамок, стальная шапка (как у шахматки табеля,
       Task 330), группы-строки «В начале/В конце месяца», зебра строк
       (ориентир при горизонтальной прокрутке на мобайле). Всё на
       теме-переменных — тёмная/светлая темы без дублирования правил. */
    .pe-body {
        padding: 12px 4px 8px;
    }
    /* Карточка-обёртка: рамка + радиус срезает углы таблицы */
    .pe-card {
        margin: 0 12px;
        border: 1px solid var(--card-border, rgba(74, 143, 199, 0.25));
        border-radius: 12px;
        background: var(--card-bg, rgba(30, 42, 56, 0.55));
        overflow: hidden;
    }
    /* Широкая сетка (наименование + 12 месяцев) на узких экранах
       прокручивается горизонтально (паттерн .ws-grid-wrap) */
    .pe-grid-wrap {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;      /* Firefox */
        -ms-overflow-style: none;   /* старый Edge / IE */
    }
    .pe-grid-wrap::-webkit-scrollbar {
        width: 0;
        height: 0;
        display: none;
    }
    .pe-table {
        border-collapse: collapse;
        font-size: 13px;
        color: var(--text-primary, #e0e0e0);
        width: max-content;
        min-width: 100%;
    }
    /* Пропорции образца: колонка наименований широкая (49,7 Excel),
       месяцы — одинаковые узкие (8,9) */
    .pe-col-name { width: 300px; }
    .pe-col-month { width: 46px; }
    .pe-table th, .pe-table td {
        border: 1px solid rgba(140, 158, 188, 0.35);
    }
    .pe-table thead th {
        background: #1e293b;
        color: var(--text-secondary, rgba(255, 255, 255, 0.55));
        font-weight: 600;
        text-align: center;
        padding: 7px 4px;
        line-height: 15px;
    }
    .pe-th-name {
        text-align: left;
        padding: 7px 12px;
        font-size: 14px;
        color: var(--text-primary, #e0e0e0);
    }
    .pe-th-year { font-size: 14px; }
    .pe-head-months th { font-size: 12px; }
    /* Строка-группа («В начале месяца» / «В конце месяца») — жирная,
       с фоном шапки таблиц (в образце — жирный текст 14pt) */
    .pe-group td {
        background: var(--table-head-bg, rgba(22, 27, 34, 0.7));
        color: var(--text-primary, #e0e0e0);
        font-weight: 700;
        font-size: 14px;
        text-align: left;
        padding: 8px 12px;
        letter-spacing: 0.2px;
    }
    .pe-name {
        text-align: left;
        padding: 9px 12px;
    }
    /* Пустая ячейка месяца (разметка периодичности в образец
       не входит) — высота как у строки с текстом */
    .pe-m { height: 36px; }
    /* Зебра строк — ориентир «чья это строка» при горизонтальной
       прокрутке (мобайл); цвета — тема-переменные таблиц */
    .pe-row:nth-child(even) td {
        background: var(--table-row-bg, rgba(13, 17, 23, 0.4));
    }
    .pe-row:nth-child(odd) td {
        background: var(--table-row-alt-bg, rgba(22, 27, 34, 0.4));
    }
    /* Светлая тема — как у сетки шахматки (Task 330/355) */
    [data-theme="light"] .pe-table th,
    [data-theme="light"] .pe-table td {
        border-color: rgb(83, 96, 117);
    }
    [data-theme="light"] .pe-table thead th {
        background: #bfcad5;
        color: #333;
    }
    [data-theme="light"] .pe-th-name {
        color: #333;
    }

</style>"""

src = rep(src, CSS_ANCHOR, CSS_BLOCK, 'CSS-блок перед </style>')

# ============================================================
# 2. Кнопка на page-docs-ios (после «Табеля»)
# ============================================================
BTN_ANCHOR = """                    <div id="workScheduleMenuBtn" class="menu-btn" onclick="navigateTo('work-schedule')" style="cursor: pointer;"><div class="menu-btn-text"><div class="menu-btn-label">Табель учёта рабочего времени</div><div class="menu-btn-sublabel">Шахматка сменного и дневного персонала</div></div><svg class="menu-btn-arrow" viewBox="0 0 24 24" style="width: 18px; height: 18px; stroke: rgba(255,255,255,0.12); fill: none; stroke-width: 2; stroke-linecap: round;"><polyline points="9 18 15 12 9 6"/></svg></div>
                </div>"""

BTN_NEW = """                    <div id="workScheduleMenuBtn" class="menu-btn" onclick="navigateTo('work-schedule')" style="cursor: pointer;"><div class="menu-btn-text"><div class="menu-btn-label">Табель учёта рабочего времени</div><div class="menu-btn-sublabel">Шахматка сменного и дневного персонала</div></div><svg class="menu-btn-arrow" viewBox="0 0 24 24" style="width: 18px; height: 18px; stroke: rgba(255,255,255,0.12); fill: none; stroke-width: 2; stroke-linecap: round;"><polyline points="9 18 15 12 9 6"/></svg></div>
                    <!-- Task 460: «Плановые мероприятия» — статичная
                         страница-таблица периодических работ по образцу
                         «Пример таблицы мероприятий.xlsx»; отдельного
                         права НЕ имеет — кнопку видят все, кто видит
                         сам раздел «Документация ИОС». -->
                    <div id="planEventsMenuBtn" class="menu-btn" onclick="navigateTo('plan-events')" style="cursor: pointer;"><div class="menu-btn-text"><div class="menu-btn-label">Плановые мероприятия</div><div class="menu-btn-sublabel">Периодические работы по месяцам года</div></div><svg class="menu-btn-arrow" viewBox="0 0 24 24" style="width: 18px; height: 18px; stroke: rgba(255,255,255,0.12); fill: none; stroke-width: 2; stroke-linecap: round;"><polyline points="9 18 15 12 9 6"/></svg></div>
                </div>"""

src = rep(src, BTN_ANCHOR, BTN_NEW, 'кнопка на page-docs-ios')

# ============================================================
# 3. Страница page-plan-events (после page-docs-ios)
# ============================================================
PAGE_ANCHOR = """        <!-- ======================== РАСХОДОМЕРЫ ХОЗРАСЧЁТНЫЕ — список записей ======================== -->"""

PAGE_NEW = """        <!-- ======================== ПЛАНОВЫЕ МЕРОПРИЯТИЯ ======================== -->
        <!-- Task 460: заявка — «создать новый раздел "Плановые мероприятия"
             в разделе Документация ИОС. На странице нового раздела необходимо
             разместить информацию в виде таблицы по образцу, приложенному
             в файле». Таблица по образцу «Пример таблицы мероприятий.xlsx»:
             шапка «Мероприятия» (на 2 строки) + «2026 год» (на 12 колонок
             месяцев), группы «В начале месяца» (3 мероприятия) и «В конце
             месяца» (5 мероприятий), ячейки месяцев ПУСТЫЕ — разметка
             периодичности в образец не входит. Опечатка образца «Феф.»
             исправлена на «Фев.». Страница СТАТИЧНАЯ (справочная):
             серверных запросов НЕТ, работает офлайн; доступ — как у
             страницы «Документация ИОС» (без отдельного права). -->
        <div id="page-plan-events" class="page-content">
            <div class="page-inline-header">
                <div class="page-inline-header-chevron" onclick="chevronTap()" aria-label="Назад / Главная"></div>
                <div class="page-inline-header-title">Плановые мероприятия</div>
            </div>
            <div class="pe-body">
                <div class="pe-card">
                    <div class="pe-grid-wrap">
                        <table class="pe-table">
                            <colgroup>
                                <col class="pe-col-name">
                                <col class="pe-col-month" span="12">
                            </colgroup>
                            <thead>
                                <tr class="pe-head-top">
                                    <th class="pe-th-name" rowspan="2">Мероприятия</th>
                                    <th class="pe-th-year" colspan="12">2026 год</th>
                                </tr>
                                <tr class="pe-head-months">
                                    """ + MONTH_THS + """
                                </tr>
                            </thead>
                            <tbody>
""" + build_rows() + """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- ======================== РАСХОДОМЕРЫ ХОЗРАСЧЁТНЫЕ — список записей ======================== -->"""

src = rep(src, PAGE_ANCHOR, PAGE_NEW, 'страница page-plan-events')

# ============================================================
# 4. PAGE_PARENTS
# ============================================================
src = rep(src,
          "        'work-schedule':            'docs-ios',",
          "        'work-schedule':            'docs-ios',\n"
          "        // Task 460: «Плановые мероприятия» — подраздел\n"
          "        // «Документации ИОС» (крошки: «Главная / Документация /\n"
          "        // Документация ИОС / Плановые мероприятия»)\n"
          "        'plan-events':              'docs-ios',",
          'PAGE_PARENTS')

# ============================================================
# 5. PAGE_LABELS
# ============================================================
src = rep(src,
          "        'flowmeter-detail': 'Расходомер',",
          "        'flowmeter-detail': 'Расходомер',\n"
          "        'plan-events':      'Плановые мероприятия',",
          'PAGE_LABELS')

# ============================================================
# 6. SUBSECTIONS
# ============================================================
src = rep(src,
          "        'work-schedule':  { label: 'Табель учёта рабочего времени', sublabel: 'Шахматка сменного и дневного персонала',          target: 'work-schedule',  category: 'docs' },",
          "        'work-schedule':  { label: 'Табель учёта рабочего времени', sublabel: 'Шахматка сменного и дневного персонала',          target: 'work-schedule',  category: 'docs' },\n"
          "        // Task 460: «Плановые мероприятия» — можно закрепить на\n"
          "        // главной (кнопка на странице «Документация ИОС»)\n"
          "        'plan-events':    { label: 'Плановые мероприятия',       sublabel: 'Периодические работы по месяцам года',            target: 'plan-events',    category: 'docs' },",
          'SUBSECTIONS')

# ============================================================
# 7. _KIP_IOS_PAGES
# ============================================================
src = rep(src,
          "                         'plan-114', 'plan-114-view'],",
          "                         'plan-114', 'plan-114-view',\n"
          "                         // Task 460: «Плановые мероприятия» —\n"
          "                         // статичная страница-таблица (доступ =\n"
          "                         // «Документация ИОС», отдельного права нет)\n"
          "                         'plan-events'],",
          '_KIP_IOS_PAGES')

# ============================================================
# 8. LVL_KIP8_PRO (легаси-карта)
# ============================================================
src = rep(src,
          "            const LVL_KIP8_PRO = [].concat(BASE, CALC, LIB, SECRET, WHATS_NEW, FLOWMETER, ['docs-ios']);",
          "            // Task 460: вместе с хабом «Документация ИОС» КИП8 pro\n"
          "            // получает статичную страницу «Плановые мероприятия»\n"
          "            const LVL_KIP8_PRO = [].concat(BASE, CALC, LIB, SECRET, WHATS_NEW, FLOWMETER, ['docs-ios', 'plan-events']);",
          'LVL_KIP8_PRO')

# ============================================================
# 9. _applyServerAccess (серверная матрица прав)
# ============================================================
src = rep(src,
          "                // «Документация ИОС» — вход к расходомерам для ролей без\n"
          "                // доступа к КИП ИОС (КИП8 pro, Task 117); ролям с КИП ИОС\n"
          "                // docs-ios уже добавлен через _KIP_IOS_PAGES.\n"
          "                if (!kipios) _add(['docs-ios']);",
          "                // «Документация ИОС» — вход к расходомерам для ролей без\n"
          "                // доступа к КИП ИОС (КИП8 pro, Task 117); ролям с КИП ИОС\n"
          "                // docs-ios уже добавлен через _KIP_IOS_PAGES.\n"
          "                // Task 460: вместе с хабом идёт статичная страница\n"
          "                // «Плановые мероприятия» (отдельного права НЕ имеет).\n"
          "                if (!kipios) _add(['docs-ios', 'plan-events']);",
          '_applyServerAccess')

# ============================================================
# 10. Сайдбар — пункт группы «Документация ИОС»
# ============================================================
SIDEBAR_ANCHOR = """        <div class="sidebar-item sidebar-item-extra" id="sidebarWorkScheduleBtn" onclick="navigateTo('work-schedule'); toggleSidebar();" style="display:none;">
            <span style="color:rgba(200,112,72,0.9);">Табель учёта рабочего времени</span>
        </div>
        </div>"""

SIDEBAR_NEW = """        <div class="sidebar-item sidebar-item-extra" id="sidebarWorkScheduleBtn" onclick="navigateTo('work-schedule'); toggleSidebar();" style="display:none;">
            <span style="color:rgba(200,112,72,0.9);">Табель учёта рабочего времени</span>
        </div>
        <!-- Task 460: «Плановые мероприятия» — пункт группы «Документация
             ИОС»; видимость — общая логика _applyRoleToUI по navigateTo-
             целевой странице (виден всем ролям с доступом к разделу),
             счётчик группы пересчитывается динамически. -->
        <div class="sidebar-item sidebar-item-extra" onclick="navigateTo('plan-events'); toggleSidebar();">
            <span style="color:rgba(200,112,72,0.9);">Плановые мероприятия</span>
        </div>
        </div>"""

src = rep(src, SIDEBAR_ANCHOR, SIDEBAR_NEW, 'сайдбар-пункт')

# ============================================================
# 11. sw.js: v683 → v684 + комментарий
# ============================================================
sw = rep(sw,
         "// Task 459: архив .xlsx работников — лист «СИЗ»: строки по\n"
         "// АЛФАВИТУ ФАМИЛИЙ колонки «Работник» (прежде — по таб. №),\n"
         "// «Должность» — БЕЗ разрядов (_ppePosNoGrade).",
         "// Task 459: архив .xlsx работников — лист «СИЗ»: строки по\n"
         "// АЛФАВИТУ ФАМИЛИЙ колонки «Работник» (прежде — по таб. №),\n"
         "// «Должность» — БЕЗ разрядов (_ppePosNoGrade).\n"
         "// Task 460: НОВЫЙ раздел «Плановые мероприятия» в «Документации\n"
         "// ИОС» — статичная таблица «Мероприятия × 12 месяцев 2026 года»\n"
         "// по образцу («В начале/В конце месяца», ячейки месяцев пустые);\n"
         "// доступ — как у раздела, серверных шагов нет.",
         'комментарий Task 460 в sw.js')

sw = rep(sw,
         "const CACHE_VERSION = 'kipia-test-v683';",
         "const CACHE_VERSION = 'kipia-test-v684';",
         'SW kipia-test-v683 → v684')

# ============================================================
# Проверки результата (до записи)
# ============================================================
checks = [
    ('страница page-plan-events', src.count('id="page-plan-events"') == 1),
    ('кнопка planEventsMenuBtn', src.count('id="planEventsMenuBtn"') == 1),
    ('CSS .pe-table', src.count('.pe-table {') == 1),
    ('шапка «2026 год» colspan 12', src.count('colspan="12">2026 год<') == 1),
    ('«Мероприятия» rowspan 2', src.count('rowspan="2">Мероприятия<') == 1),
    ('группа «В начале месяца»', src.count('<tr class="pe-group"><td colspan="13">В начале месяца</td></tr>') == 1),
    ('группа «В конце месяца»', src.count('<tr class="pe-group"><td colspan="13">В конце месяца</td></tr>') == 1),
    ('8 мероприятий', src.count('<td class="pe-name">') == 8),
    ('96 пустых ячеек месяцев', src.count('<td class="pe-m"></td>') == 96),
    ('месяц «Фев.» (опечатки «Феф.» в th нет)', src.count('<th>Фев.</th>') == 1 and src.count('<th>Феф.</th>') == 0),
    ('PAGE_PARENTS', src.count("'plan-events':              'docs-ios',") == 1),
    ('PAGE_LABELS', src.count("'plan-events':      'Плановые мероприятия',") == 1),
    ('SUBSECTIONS', src.count("target: 'plan-events',    category: 'docs' }") == 1),
    ('LVL_KIP8_PRO', src.count("FLOWMETER, ['docs-ios', 'plan-events']);") == 1),
    ('_applyServerAccess', src.count("if (!kipios) _add(['docs-ios', 'plan-events']);") == 1),
    ('сайдбар-пункт', src.count("navigateTo('plan-events'); toggleSidebar();") == 1),
    ('SW v684', sw.count("kipia-test-v684") == 1),
    ('SW старой v683 нет', sw.count("kipia-test-v683") == 0),
]
# отдельная проверка _KIP_IOS_PAGES (конец массива)
checks.append(('_KIP_IOS_PAGES plan-events', src.count("'plan-114', 'plan-114-view',") == 1 and src.count("'plan-events'],") == 1))

bad = [name for name, ok in checks if ok is not True]
if bad:
    print('ОТКАТ: не пройдены проверки: %s' % '; '.join(str(b) for b in bad))
    print('DEBUG: <th>Фев.</th>=%d  Феф.=%d  96td=%d' % (
        src.count('<th>Фев.</th>'), src.count('Феф.'),
        src.count('<td class="pe-m"></td>')))
    sys.exit(1)

# ============================================================
# Запись
# ============================================================
with io.open(INDEX, 'w', encoding='utf-8') as f:
    f.write(src)
with io.open(SW, 'w', encoding='utf-8') as f:
    f.write(sw)

print('OK: index.html (11 замен) + sw.js (v683 → v684), проверок пройдено: %d' % sum(1 for _, ok in checks if ok))
