#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 401 (kip8test): заявка «В десктопной версии приложения, в
# разделе Табель учёта рабочего времени, окно итогов учёта за год
# должно раскрываться полностью закрывая собой шахматку табеля,
# вплотную примыкая к правому краю столбца с фамилиями работников,
# и в шапке окна итогов учёта за год, под числами должно быть
# пояснение данных в ячейках "дней/часов", и три крайних правых
# столбца (дней, часов, перераб. (дни)) выделить фоном немного
# другого оттенка от остальных ячеек со столбцами месяцев, и
# разделить их вертикальной линией таблицы такой же как с левого
# края окна итогов учёта за год».
#
# ЧЕТЫРЕ изменения (только index.html, серверных шагов НЕТ):
#   1) ДЕСКТОП, вкладка «Год»: шторка итогов РАСКРЫВАЕТСЯ НА ВСЮ
#      ШИРИНУ рабочей области правее колонки ФИО шахматки —
#      _fitTtDrawer в годовом режиме ставит ширину =
#      #wsWsBody.clientWidth − --ws-emp-w (натуральная ширина
#      колонки ФИО; на десктопе сужения ФИО не бывает — _narrowApply
#      гасит его при ≥1024px). Класс ws-tt-yearfull на странице:
#      снимает кап 60% (.ws-tt-drawer), растягивает таблицу года на
#      100% ширины шторки (#wsTotalsPanel), прячет полосу-
#      разделитель ФИО сетки (::after, Task 333 — иначе у края
#      окна ДВЕ линии 2px+2px; единственная линия .ws-tt-edge) и
#      гасит ползунок прокрутки закрытой шторкой шахматки (мертвый
#      UI). Ресайз окна — пересчёт (ResizeObserver/fallback в
#      _attachFitResize). «Месяц»/закрытие — класс снят, прежняя
#      ширина по столбцам таблицы.
#   2) ШАПКА годовой таблицы — ПОДСТРОКА-пояснение «дней/часов»
#      (th.ws-tt-sub, colspan=12, под месяцами «янв…дек»: ячейки
#      месяцев вида «11/132» = слева дни, справа часы); шапка стала
#      двухстрочной — «Работник» и три итоговых th — rowspan="2";
#      у ОБОИХ таблиц (главная + архив).
#   3) ТРИ ИТОГОВЫХ СТОЛБЦА (Дней/Часов/Перераб. (дни)) — классы
#      ws-tt-sum (th+td): фон немного другого оттенка (шапка —
#      светлее стали #243048 тёмная / чуть темнее #b4c1cd светлая;
#      ячейки — полупрозрачная тонировка поверх зебры).
#   4) РАЗДЕЛИТЕЛЬ между месяцами и итоговыми столбцами — 2px
#      сплошная слева от «Дней» (ws-tt-sum-edge на th+td), та же
#      линия, что левый край окна итогов .ws-tt-edge: #4a8fc7
#      тёмная / #6e8ba4 светлая.

REPLS = [

# ---------- 1. CSS: класс ws-tt-yearfull — полная ширина «Года» ----------
(
"""        .ws-tt-drawer {
            flex: none;
            display: flex;
            position: relative;   /* якорь бортика/кнопки левого края */
            width: 0;             /* до первого открытия (панель скрыта) */
            max-width: 60%;       /* кап: длинные таблицы — прокруткой */
            overflow: hidden;     /* клип мгновенных пререндеров ширины */
            transition: margin-right 0.28s ease;
        }
    }
""",
"""        .ws-tt-drawer {
            flex: none;
            display: flex;
            position: relative;   /* якорь бортика/кнопки левого края */
            width: 0;             /* до первого открытия (панель скрыта) */
            max-width: 60%;       /* кап: длинные таблицы — прокруткой */
            overflow: hidden;     /* клип мгновенных пререндеров ширины */
            transition: margin-right 0.28s ease;
        }
    }
    /* Task 401 (заявка): вкладка «Год» — шторка итогов РАСКРЫВАЕТСЯ
       НА ВСЮ ШИРИНУ рабочей области ПРАВЕЕ столбца ФИО шахматки,
       полностью закрывая собой дни (ширину ставит JS _fitTtDrawer:
       #wsWsBody − --ws-emp-w; класс ws-tt-yearfull на странице —
       ставит/снимает тот же _fitTtDrawer):
       · кап 60% снят — шторке разрешена полная ширина;
       · таблица года — width: 100% (растягивается по шторке; колонка
         ФИО не растёт — авто-раскладка делит меж месяцев/итогов;
         мобильная СТРАНИЦА итогов и прямой заход по #hash не
         тронуты — селектор только #wsTotalsPanel шторки).
       Правила скрытия полосы ФИО сетки (::after) и ползунка
       шахматки — НИЖЕ базовых правил ::after (Task 333/336),
       в блоке Task 401 рядом с ними */
    @media (min-width: 1024px) {
        #page-work-schedule.ws-tt-yearfull .ws-tt-drawer {
            max-width: none;
        }
        #page-work-schedule.ws-tt-yearfull #wsTotalsPanel .ws-tt-table.ws-tt-year {
            width: 100%;
        }
    }
"""
),

# ---------- 1b. CSS: скрытие полосы ФИО и ползунка — ПОСЛЕ базовых ::after ----------
(
"""    [data-theme="light"] .ws-grid thead th.ws-emp-col::after,
    [data-theme="light"] .ws-grid tbody td.ws-emp-col::after {
        background: #6e8ba4;
    }
    .ws-grid {
""",
"""    [data-theme="light"] .ws-grid thead th.ws-emp-col::after,
    [data-theme="light"] .ws-grid tbody td.ws-emp-col::after {
        background: #6e8ba4;
    }
    /* Task 401 (заявка): полная ширина «Года» — правила стоят ЗДЕСЬ,
       ПОСЛЕ базовых ::after-полос ФИО сетки (Task 333/336), чтобы
       первое вхождение селектора оставалось базовым:
       · полоса-разделитель ФИО шахматки СКРЫТА — у левого края окна
         итогов остаётся ЕДИНСТВЕННАЯ линия .ws-tt-edge (шторка
         примыкает вплотную — иначе на стыке ДВЕ линии 2px + 2px);
       · ползунок прокрутки шахматки (.ws-grid-hbar) погашен — дни
         полностью закрыты шторкой, скроллить нечего (мертвый UI);
         12px-зона остаётся — бордюры сетки и шторки на одном
         уровне (Task 331) */
    @media (min-width: 1024px) {
        #page-work-schedule.ws-tt-yearfull .ws-grid thead th.ws-emp-col::after,
        #page-work-schedule.ws-tt-yearfull .ws-grid tbody td.ws-emp-col::after {
            display: none;
        }
        #page-work-schedule.ws-tt-yearfull .ws-grid-hbar.on {
            background: none;
            border-radius: 0;
        }
        #page-work-schedule.ws-tt-yearfull .ws-grid-hbar .ws-hbar-thumb {
            display: none !important;
        }
    }
    .ws-grid {
"""
),

# ---------- 2. CSS: подстрока шапки + итоговые столбцы ----------
(
"""    /* годовая таблица — прежний вид: заголовки-месяцы одной строкой;
       Task 331 (заявка): текст — по центру (как ячейки значений) */
    .ws-tt-table.ws-tt-year th {
        white-space: nowrap;
        overflow-wrap: normal;
        word-break: normal;
        hyphens: manual;
        text-align: center;
    }
""",
"""    /* годовая таблица — прежний вид: заголовки-месяцы одной строкой;
       Task 331 (заявка): текст — по центру (как ячейки значений) */
    .ws-tt-table.ws-tt-year th {
        white-space: nowrap;
        overflow-wrap: normal;
        word-break: normal;
        hyphens: manual;
        text-align: center;
    }
    /* Task 401 (заявка): ПОДСТРОКА шапки годовой таблицы — пояснение
       формата данных в ячейках месяцев «дней/часов» (ячейка вида
       «11/132»: слева ДНИ, справа ЧАСЫ); одна на все 12 месяцев
       (colspan=12), под месяцами шапки. Компактная — высота auto
       (не 38px базовой шапки), приглушённый цвет */
    .ws-tt-table.ws-tt-year th.ws-tt-sub {
        height: auto;
        padding: 1px 4px 3px;
        font-size: 10px;
        font-weight: 600;
        line-height: 1.2;
        color: var(--text-secondary, rgba(255, 255, 255, 0.5));
    }
    [data-theme="light"] .ws-tt-table.ws-tt-year th.ws-tt-sub {
        color: #5b6774;
    }
    /* Task 401 (заявка): ТРИ ИТОГОВЫХ СТОЛБЦА (Дней/Часов/Перераб.
       (дни)) — фон НЕМНОГО ДРУГОГО ОТТЕНКА от столбцов месяцев:
       шапка — светлее стальной (тёмная #243048 против #1e293b) /
       чуть темнее (светлая #b4c1cd против #bfcad5); ячейки —
       полупрозрачная тонировка ПОВЕРХ зебры строк (зебра видна);
       слева от блока — РАЗДЕЛИТЕЛЬ 2px, та же линия, что левый
       край окна итогов .ws-tt-edge (#4a8fc7 тёмная / #6e8ba4
       светлая; в border-collapse стык 2px побеждает 1px границы
       «дек» — линия непрерывна, включая подстроку шапки) */
    .ws-tt-table.ws-tt-year th.ws-tt-sum {
        background: #243048;
    }
    [data-theme="light"] .ws-tt-table.ws-tt-year th.ws-tt-sum {
        background: #b4c1cd;
    }
    .ws-tt-table.ws-tt-year td.ws-tt-sum {
        background: rgba(255, 255, 255, 0.05);
    }
    [data-theme="light"] .ws-tt-table.ws-tt-year td.ws-tt-sum {
        background: rgba(0, 0, 0, 0.05);
    }
    .ws-tt-table.ws-tt-year th.ws-tt-sum-edge,
    .ws-tt-table.ws-tt-year td.ws-tt-sum-edge {
        border-left: 2px solid #4a8fc7;
    }
    [data-theme="light"] .ws-tt-table.ws-tt-year th.ws-tt-sum-edge,
    [data-theme="light"] .ws-tt-table.ws-tt-year td.ws-tt-sum-edge {
        border-left-color: #6e8ba4;
    }
"""
),

# ---------- 3. JS: _fitTtDrawer — полный режим «Года» ----------
(
"""            var body = document.getElementById('wsTtBody');
            var table = body ? body.querySelector('.ws-tt-table') : null;
            var w = table ? Math.ceil(table.getBoundingClientRect().width) : 0;
            if (!w) w = 240;   // пустое/загрузочное состояние — минимум
            drawer.style.width = w + 'px';
        },
""",
"""            // Task 401 (заявка): вкладка «Год» — шторка РАСКРЫВАЕТСЯ
            // НА ВСЮ ШИРИНУ рабочей области правее столбца ФИО
            // шахматки, ПОЛНОСТЬЮ закрывая собой дни. Ширина =
            // #wsWsBody.clientWidth − --ws-emp-w (натуральная ширина
            // колонки ФИО по тексту — её мерит _measureEmpCol; на
            // десктопе сужения ФИО не бывает: _narrowApply гасит
            // его при ≥1024px, поэтому --ws-emp-nw здесь не нужна).
            // Класс ws-tt-yearfull на странице: снимает кап 60%,
            // растягивает таблицу года на 100% шторки, прячет
            // полосу ФИО сетки (у края окна — ЕДИНСТВЕННАЯ линия
            // .ws-tt-edge) и гасит ползунок шахматки (дни закрыты).
            // «Месяц»/закрытие — класс снят, ширина по столбцам
            // таблицы (прежнее поведение Task 329)
            var full = false;
            var page = document.getElementById('page-work-schedule');
            if (this._totalsTab === 'year' && !this._ttPage && page) {
                var wBody = document.getElementById('wsWsBody');
                var empW = 180;   // фолбэк ширины ФИО (как в CSS)
                if (window.getComputedStyle) {
                    try {
                        var ev = parseFloat(window.getComputedStyle(page)
                                    .getPropertyValue('--ws-emp-w'));
                        if (ev > 0) empW = ev;
                    } catch (e) {}
                }
                if (wBody && wBody.clientWidth) {
                    var wFull = Math.floor(wBody.clientWidth - empW);
                    if (wFull < 240) wFull = 240;   // минимум (как пустое состояние)
                    drawer.style.width = wFull + 'px';
                    full = true;
                }
            }
            if (page && page.classList) {
                if (full && page.classList.add) {
                    page.classList.add('ws-tt-yearfull');
                } else if (!full && page.classList.remove) {
                    page.classList.remove('ws-tt-yearfull');
                }
            }
            if (full) return;
            var body = document.getElementById('wsTtBody');
            var table = body ? body.querySelector('.ws-tt-table') : null;
            var w = table ? Math.ceil(table.getBoundingClientRect().width) : 0;
            if (!w) w = 240;   // пустое/загрузочное состояние — минимум
            drawer.style.width = w + 'px';
        },
"""
),

# ---------- 4. JS: _ttCloseCleanup — снять ws-tt-yearfull ----------
(
"""            var page = document.getElementById('page-work-schedule');
            if (page && page.classList && page.classList.remove) {
                page.classList.remove('ws-tt-gridwide');
            }
""",
"""            var page = document.getElementById('page-work-schedule');
            if (page && page.classList && page.classList.remove) {
                page.classList.remove('ws-tt-gridwide');
                // Task 401: полноширинный «Год» закрыт — класс снять
                // (полоса ФИО сетки и ползунок возвращаются)
                page.classList.remove('ws-tt-yearfull');
            }
"""
),

# ---------- 5. JS: _attachFitResize — пересчёт при ресайзе ----------
(
"""            if (wrap && typeof ResizeObserver !== 'undefined') {
                this._fitObserver = new ResizeObserver(function() {
                    self._fitGrid();
                });
                this._fitObserver.observe(wrap);
            } else if (wrap) {
                // запасной вариант для старых браузеров без ResizeObserver
                window.addEventListener('resize', function() {
                    self._fitGrid();
                });
            }
""",
"""            if (wrap && typeof ResizeObserver !== 'undefined') {
                this._fitObserver = new ResizeObserver(function() {
                    self._fitGrid();
                    // Task 401 (заявка): годовая шторка «на всю ширину» —
                    // при изменении размера окна/области ширина
                    // пересчитывается (иначе шахматка выглядывает
                    // из-под закрывающего её окна). Сходится: повторный
                    // вызов с теми же входными не меняет ширину —
                    // ResizeObserver больше не срабатывает
                    if (self._totalsOpen && self._totalsTab === 'year'
                            && !self._ttPage
                            && typeof self._fitTtDrawer === 'function') {
                        try { self._fitTtDrawer(); } catch (e) {}
                    }
                });
                this._fitObserver.observe(wrap);
            } else if (wrap) {
                // запасной вариант для старых браузеров без ResizeObserver
                window.addEventListener('resize', function() {
                    self._fitGrid();
                    // Task 401: годовая шторка — пересчёт и на ресайзе
                    if (self._totalsOpen && self._totalsTab === 'year'
                            && !self._ttPage
                            && typeof self._fitTtDrawer === 'function') {
                        try { self._fitTtDrawer(); } catch (e) {}
                    }
                });
            }
"""
),

# ---------- 6. JS: yearRow — классы итоговых ячеек ----------
(
"""                out += '<td class="ws-tt-num">' + (sumWork || '—') + '</td>' +
                        '<td class="ws-tt-num ws-tt-hours">' +
                        (sumHours ? self._fmtTotalsNum(sumHours) : '—') + '</td>' +
                        '<td class="ws-tt-num ws-tt-over" title="часов переработки: ' +
                            self._fmtTotalsNum(sumOver) + ' (коды д/н)">' +
                        (sumOverDays || '—') + '</td></tr>';
""",
"""                // Task 401 (заявка): три итоговых столбца — классы
                // ws-tt-sum (фон другого оттенка) + ws-tt-sum-edge
                // («Дней»: разделитель 2px слева — как левый край
                // окна итогов)
                out += '<td class="ws-tt-num ws-tt-sum ws-tt-sum-edge">' +
                        (sumWork || '—') + '</td>' +
                        '<td class="ws-tt-num ws-tt-hours ws-tt-sum">' +
                        (sumHours ? self._fmtTotalsNum(sumHours) : '—') + '</td>' +
                        '<td class="ws-tt-num ws-tt-over ws-tt-sum" title="часов переработки: ' +
                            self._fmtTotalsNum(sumOver) + ' (коды д/н)">' +
                        (sumOverDays || '—') + '</td></tr>';
"""
),

# ---------- 7. JS: шапка ГЛАВНОЙ таблицы года — двухстрочная ----------
(
"""            var html = '';
            if (employees.length) {
                html = '<table class="ws-tt-table ws-tt-year">' +
                    // Task 335: «Сотрудник» → «Сотр» при сужении
                    '<thead><tr><th class="ws-tt-emp"><span class="ws-tt-emp-head" data-full="Работник" data-s4="Рабо">Работник</span></th>';
                for (var h = 1; h <= 12; h++) {
                    html += '<th>' + monthsAbbr[h - 1] + '</th>';
                }
                html += '<th>Дней</th><th>Часов</th>' +
                    '<th title="дни переработки за год — коды д/н">Перераб. (дни)</th>' +
                    '</tr></thead><tbody>';
""",
"""            var html = '';
            if (employees.length) {
                html = '<table class="ws-tt-table ws-tt-year">' +
                    // Task 335: «Сотрудник» → «Сотр» при сужении;
                    // Task 401: rowspan="2" — шапка ДВУХСТРОЧНАЯ
                    // (подстрока «дней/часов» под месяцами)
                    '<thead><tr><th class="ws-tt-emp" rowspan="2"><span class="ws-tt-emp-head" data-full="Работник" data-s4="Рабо">Работник</span></th>';
                for (var h = 1; h <= 12; h++) {
                    html += '<th>' + monthsAbbr[h - 1] + '</th>';
                }
                // Task 401 (заявка): итоговые столбцы — rowspan="2"
                // (шапка двухстрочная) + классы ws-tt-sum (фон) и
                // ws-tt-sum-edge («Дней»: разделитель 2px слева)
                html += '<th class="ws-tt-sum ws-tt-sum-edge" rowspan="2">Дней</th>' +
                    '<th class="ws-tt-sum" rowspan="2">Часов</th>' +
                    '<th class="ws-tt-sum" rowspan="2" title="дни переработки за год — коды д/н">Перераб. (дни)</th>' +
                    // Task 401 (заявка): ПОДСТРОКА-пояснение формата
                    // ячеек месяцев «дней/часов» («11/132»: слева дни,
                    // справа часы) — под месяцами шапки
                    '</tr><tr><th class="ws-tt-sub" colspan="12">дней/часов</th></tr>' +
                    '</thead><tbody>';
"""
),

# ---------- 8. JS: шапка таблицы АРХИВА — двухстрочная ----------
(
"""            if (archived.length) {
                html += '<div class="ws-tt-arch-cap">Архив</div>' +
                    '<table class="ws-tt-table ws-tt-year ws-tt-arch">' +
                    // Task 335: «Сотрудник» → «Сотр» при сужении
                    '<thead><tr><th class="ws-tt-emp"><span class="ws-tt-emp-head" data-full="Работник" data-s4="Рабо">Работник</span></th>';
                for (var h2 = 1; h2 <= 12; h2++) {
                    html += '<th>' + monthsAbbr[h2 - 1] + '</th>';
                }
                html += '<th>Дней</th><th>Часов</th>' +
                    '<th title="дни переработки за год — коды д/н">Перераб. (дни)</th>' +
                    '</tr></thead><tbody>';
""",
"""            if (archived.length) {
                html += '<div class="ws-tt-arch-cap">Архив</div>' +
                    '<table class="ws-tt-table ws-tt-year ws-tt-arch">' +
                    // Task 335: «Сотрудник» → «Сотр» при сужении;
                    // Task 401: rowspan="2" + подстрока «дней/часов» —
                    // шапка двухстрочная, как у главной (Task 401)
                    '<thead><tr><th class="ws-tt-emp" rowspan="2"><span class="ws-tt-emp-head" data-full="Работник" data-s4="Рабо">Работник</span></th>';
                for (var h2 = 1; h2 <= 12; h2++) {
                    html += '<th>' + monthsAbbr[h2 - 1] + '</th>';
                }
                html += '<th class="ws-tt-sum ws-tt-sum-edge" rowspan="2">Дней</th>' +
                    '<th class="ws-tt-sum" rowspan="2">Часов</th>' +
                    '<th class="ws-tt-sum" rowspan="2" title="дни переработки за год — коды д/н">Перераб. (дни)</th>' +
                    '</tr><tr><th class="ws-tt-sub" colspan="12">дней/часов</th></tr>' +
                    '</thead><tbody>';
"""
),
]

if __name__ == '__main__':
    path = 'index.html'
    s = open(path, encoding='utf-8').read()
    for i, (old, new) in enumerate(REPLS, 1):
        n = s.count(old)
        assert n == 1, 'REPL %d: найдено %d вхождений (ожидалось 1)' % (i, n)
        s = s.replace(old, new)
        print('REPL %d: OK (%d симв.)' % (i, len(new)))
    open(path, 'w', encoding='utf-8').write(s)
    print('task401-patch: применено %d правок к index.html' % len(REPLS))
