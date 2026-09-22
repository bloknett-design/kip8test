#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 390 (kip8test): заявка (4 части), доработка «Общей» вкладки
# страницы «Работники»:
#   (1) убрать «Сводка по всем работникам: сменных — N, дневных — N.
#       Полная карточка каждого работника — на его вкладке.»;
#   (2) переделать численность на ДВЕ строки:
#       «Работников по штату 14: 2 мастера; 7 дневных; 5 сменных.»
#       (константа) и ниже строчкой «Работников на текущий момент:
#       (N) мастера; (N) дневных; (N) сменных.» — АВТОМАТИЧЕСКИЙ
#       ПОДСЧЁТ ПО КАТЕГОРИЯМ (мастера — по должности «Мастер КИПиА»
#       через _isMasterKipia, как фильтр шахматки; дневные/сменные —
#       по типу, БЕЗ мастеров: категории не пересекаются, как в
#       штате 2+7+5);
#   (3) ВЫДЕЛИТЬ фон шапки с этими надписями и кнопкой «Добавить
#       работника» (.ws-wgen-head — сплошной фон + рамка + отступы,
#       обе темы);
#   (4) ярлыки ПРИМЫКАЮТ к окну вкладок (padding-right колонки
#       убран — было 10px щели; активный ярлык пристыкован
#       margin-right:-1px);
#   (5) тёмная тема: ярлыки СВЕТЛЕЕ и ДРУГИМ по цвету — ТЁПЛЫЙ тон
#       ближе к светлой теме (#4B4E46/#575A50/#63665B), чтобы НЕ
#       сливались с общим фоном страницы #1a2233; светлая тема без
#       изменений (#E4E0D3/#DBD6C8/var(--bg-tertiary)).
# Только index.html (серверных шагов НЕТ).

REPLS = [

# ---------- 1-2: JS — подсчёт по категориям + новые строки шапки ----------
(
"""        // Task 389 (заявка): в шапке сводки — ЧИСЛЕННОСТЬ: «на
        // текущий момент N …» (N — АВТОМАТИЧЕСКИЙ ПОДСЧЁТ по живому
        // списку, склонение _plural) и «по штату 14, из которых
        // 2 мастера, 5 сменных и 7 дневных» (штат — константа);
        // кнопка «Добавить работника» ПЕРЕНЕСЕНА сюда из шапки
        // страницы (id wsWorkersAddBtn сохранён; только у
        // редакторов — _canEdit)
        _renderWorkersGeneral: function(list) {
            var monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
            var shiftN = 0, dayN = 0;
            var addBtn = this._canEdit
                ? '<button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">Добавить работника</button>'
                : '';
            var html = '<div class="ws-wgen-head"><div class="ws-wgen-info">' +
                       '<span class="ws-workers-count">На текущий момент: ' +
                       list.length + ' ' +
                       this._plural(list.length, ['работник', 'работника', 'работников']) +
                       ' (автоматический подсчёт).</span>' +
                       '<span class="ws-wgen-staff">По штату: 14, из которых ' +
                       '2 мастера, 5 сменных и 7 дневных.</span>' +
                       '</div>' + addBtn + '</div>';""",
"""        // Task 389 (заявка): кнопка «Добавить работника» ПЕРЕНЕСЕНА
        // сюда из шапки страницы (id wsWorkersAddBtn сохранён;
        // только у редакторов — _canEdit).
        // Task 390 (заявка): шапка — ДВЕ строки: «Работников по
        // штату 14: 2 мастера; 7 дневных; 5 сменных.» (константа) и
        // НИЖЕ строчкой «Работников на текущий момент: …» —
        // АВТОМАТИЧЕСКИЙ ПОДСЧЁТ ПО КАТЕГОРИЯМ: мастера — по
        // должности «Мастер КИПиА» (_isMasterKipia, как фильтр
        // шахматки минимального вида), дневные/сменные — по типу
        // БЕЗ мастеров (категории не пересекаются — как структура
        // штата 2+7+5); сноска «Сводка по всем работникам…»
        // УДАЛЕНА; фон шапки ВЫДЕЛЕН (.ws-wgen-head)
        _renderWorkersGeneral: function(list) {
            var monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
            // Task 390: подсчёт по категориям ДО шапки — мастера по
            // должности исключаются из сменных/дневных (штат:
            // 2 мастера + 7 дневных + 5 сменных = 14, без пересечений)
            var masterN = 0, shiftN = 0, dayN = 0;
            for (var ci = 0; ci < list.length; ci++) {
                var cEmp = list[ci];
                var cTip = String(cEmp['тип'] || '').trim();
                if (this._isMasterKipia(cEmp)) masterN++;
                else if (cTip === 'сменный') shiftN++;
                else if (cTip === 'дневной') dayN++;
            }
            var addBtn = this._canEdit
                ? '<button type="button" id="wsWorkersAddBtn" class="ws-workers-add" onclick="WorkSchedule.openEmployeeForm()" aria-label="Добавить работника">Добавить работника</button>'
                : '';
            var html = '<div class="ws-wgen-head"><div class="ws-wgen-info">' +
                       '<span class="ws-wgen-staff">Работников по штату 14: ' +
                       '2 мастера; 7 дневных; 5 сменных.</span>' +
                       '<span class="ws-workers-count">Работников на текущий момент: ' +
                       masterN + ' ' + this._plural(masterN, ['мастер', 'мастера', 'мастеров']) + '; ' +
                       dayN + ' ' + this._plural(dayN, ['дневной', 'дневных', 'дневных']) + '; ' +
                       shiftN + ' ' + this._plural(shiftN, ['сменный', 'сменных', 'сменных']) +
                       '.</span>' +
                       '</div>' + addBtn + '</div>';"""
),

# ---------- 1-2: JS — таблица: счётчики из цикла убраны ----------
(
"""                var emp = list[i];
                var tip = String(emp['тип'] || '').trim();
                var smena = parseInt(emp['смена'], 10);
                if (tip === 'сменный') shiftN++;
                else if (tip === 'дневной') dayN++;
                var tipVal = tip === 'сменный'""",
"""                var emp = list[i];
                var tip = String(emp['тип'] || '').trim();
                var smena = parseInt(emp['смена'], 10);
                var tipVal = tip === 'сменный'"""
),

# ---------- 1: JS — сноска «Сводка по всем работникам…» удалена ----------
(
"""            html += '</tbody></table>';
            html += '<div class="ws-wgen-note">Сводка по всем работникам: сменных — ' +
                    shiftN + ', дневных — ' + dayN + '. Полная карточка каждого ' +
                    'работника — на его вкладке.</div>';
            return html;""",
"""            html += '</tbody></table>';
            // Task 390: сноска «Сводка по всем работникам…» удалена
            // (заявка) — категории теперь в шапке сводки
            return html;"""
),

# ---------- 4: CSS — колонка ярлыков ПРИМЫКАЕТ к окну вкладок ----------
(
"""    .ws-wtabs {
        flex: none;
        width: 236px;
        display: flex;
        flex-direction: column;
        gap: 3px;
        padding-right: 10px;
    }""",
"""    .ws-wtabs {
        flex: none;
        width: 236px;
        display: flex;
        flex-direction: column;
        gap: 3px;
        /* Task 390 (заявка: «ярлыки должны примыкать к окну
           вкладок»): правый отступ колонки УБРАН (была щель между
           ярлыками и окном вкладок); активный ярлык пристыкован
           к окну (margin-right: -1px, правая рамка прозрачна) */
    }"""
),

# ---------- 5: CSS — комментарий-обоснование ярлыков ----------
(
"""    /* Task 388 (заявка): ярлыки-вкладки СТОЛБИКОМ СЛЕВА (браузерный
       вид): активный ярлык подсвечен и «пристыкован» к телу
       (margin-right:-1px, правая рамка прозрачна); тело — карточка
       выбранного работника / сводная таблица «Общей» вкладки.
       Task 389 (заявка: «фон ярлыков и окон вкладок сделай не
       прозрачным»): ярлыки — СПЛОШНОЙ цвет (были rgba-тинты —
       фоновая сетка-«миллиметровка» страницы просвечивала):
       неактивный — var(--bg-primary) / #E4E0D3 (тёмная/светлая),
       hover — сплошной светлее; активный — как ОКНО вкладки
       (var(--bg-tertiary), «пристыкован»). Окна вкладок: «Общая» —
       панель .ws-wgen (сплошной var(--bg-tertiary)), работник —
       .ws-wcard (уже сплошной) */""",
"""    /* Task 388 (заявка): ярлыки-вкладки СТОЛБИКОМ СЛЕВА (браузерный
       вид): активный ярлык подсвечен и «пристыкован» к телу
       (margin-right:-1px, правая рамка прозрачна); тело — карточка
       выбранного работника / сводная таблица «Общей» вкладки.
       Task 389 (заявка: «фон ярлыков и окон вкладок сделай не
       прозрачным»): ярлыки — СПЛОШНОЙ цвет; окна вкладок: «Общая» —
       панель .ws-wgen (сплошной var(--bg-tertiary)), работник —
       .ws-wcard (уже сплошной).
       Task 390 (заявка: в тёмной теме ярлыки СВЕТЛЕЕ и ДРУГИМ по
       цвету — ближе к светлой теме, чтобы НЕ сливались с общим
       фоном страницы #1a2233): тёмная тема — ТЁПЛЫЙ тон (как
       светлые #E4E0D3/#DBD6C8, затемнённый): неактивный #4B4E46,
       hover #575A50, активный #63665B (светлее неактивного — как
       активные вкладки браузеров); светлая тема — БЕЗ ИЗМЕНЕНИЙ
       (#E4E0D3/#DBD6C8/var(--bg-tertiary)) */"""
),

# ---------- 5: CSS — неактивный ярлык (тёмная) ----------
(
"""    .ws-wtab {
        display: block;
        text-align: left;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 3px solid transparent;
        border-radius: 8px 0 0 8px;
        background: var(--bg-primary, #1a2233);   /* Task 389: сплошной */
        color: var(--text-secondary, rgba(255,255,255,0.65));
        padding: 8px 10px;
        font-size: 12.5px;
        line-height: 1.3;
        cursor: pointer;
        overflow-wrap: break-word;
    }""",
"""    .ws-wtab {
        display: block;
        text-align: left;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 3px solid transparent;
        border-radius: 8px 0 0 8px;
        /* Task 390: СВЕТЛЕЕ фона страницы (#1a2233) и ТЁПЛЫЙ тон
           (ближе к светлой теме — не сливается с общим фоном) */
        background: #4B4E46;
        color: rgba(255, 255, 255, 0.78);
        padding: 8px 10px;
        font-size: 12.5px;
        line-height: 1.3;
        cursor: pointer;
        overflow-wrap: break-word;
    }"""
),

# ---------- 5: CSS — hover (тёмная) ----------
(
"""    .ws-wtab:hover {
        /* Task 389: сплошной, светлее неактивного var(--bg-primary) */
        background: #243048;
        color: var(--text-primary, #e0e0e0);
    }""",
"""    .ws-wtab:hover {
        /* Task 390: тёплый, светлее неактивного */
        background: #575A50;
        color: var(--text-primary, #e0e0e0);
    }"""
),

# ---------- 5: CSS — активный ярлык (тёмная) ----------
(
"""    .ws-wtab.active {
        background: var(--bg-tertiary, #0e1621);
        border-color: rgba(255, 255, 255, 0.14);
        border-left-color: var(--accent-blue, #4a8fc7);
        border-right-color: transparent;
        color: var(--text-primary, #e0e0e0);
        font-weight: 600;
        margin-right: -1px;
    }""",
"""    .ws-wtab.active {
        /* Task 390: активный — САМЫЙ светлый тёплый (как активные
           вкладки браузеров), «пристыкован» к окну вкладки */
        background: #63665B;
        border-color: rgba(255, 255, 255, 0.14);
        border-left-color: var(--accent-blue, #4a8fc7);
        border-right-color: transparent;
        color: var(--text-primary, #e0e0e0);
        font-weight: 600;
        margin-right: -1px;
    }"""
),

# ---------- 3: CSS — ВЫДЕЛЕННАЯ шапка сводки (тёмная) ----------
(
"""    .ws-wgen-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 6px 12px;
        margin: 2px 2px 10px;
    }""",
"""    .ws-wgen-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 6px 12px;
        /* Task 390 (заявка): шапка ВЫДЕЛЕНА фоном — строки
           «Работников по штату…» / «Работников на текущий момент…»
           + кнопка «Добавить работника» */
        background: #1E2B42;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 8px;
        padding: 10px 12px;
        margin: 0 0 12px;
    }"""
),

# ---------- 3: CSS — светлая выделенная шапка (ПОСЛЕ базового
# правила .ws-wgen-head — важно для ruleBlock-поиска первого
# вхождения «.ws-wgen-head {»; якорь = хвост REPL 9) ----------
(
"""        background: #1E2B42;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 8px;
        padding: 10px 12px;
        margin: 0 0 12px;
    }
""",
"""        background: #1E2B42;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 8px;
        padding: 10px 12px;
        margin: 0 0 12px;
    }
    [data-theme="light"] .ws-wgen-head {
        /* Task 390: выделенная шапка — тёплый тон ярлыков светлой
           темы, темнее панели окна */
        background: #E4E0D3;
        border-color: rgba(0,0,0,0.14);
    }
"""
),

# ---------- 1: CSS — мёртвое правило .ws-wgen-note удалено ----------
(
"""    .ws-wgen-note {
        font-size: 12px;
        opacity: 0.8;
        padding: 10px 2px 0;
    }
    [data-theme="light"] .ws-wgen-table th { border-bottom-color: rgba(0,0,0,0.2); }""",
"""    /* Task 390: правило сноски сводки внизу таблицы удалено вместе
       с самой сноской (заявка) — категории теперь в шапке сводки */
    [data-theme="light"] .ws-wgen-table th { border-bottom-color: rgba(0,0,0,0.2); }"""
),
]

if __name__ == '__main__':
    path = 'index.html'
    s = open(path, encoding='utf-8').read()
    for i, (old, new) in enumerate(REPLS, 1):
        n = s.count(old)
        assert n == 1, 'REPL %d: найдено %d вхождений (ожидалось 1)' % (i, n)
        s = s.replace(old, new)
        print('REPL %2d: OK (%d симв.)' % (i, len(new)))
    open(path, 'w', encoding='utf-8').write(s)
    print('task390-patch: применено %d правок к index.html' % len(REPLS))
