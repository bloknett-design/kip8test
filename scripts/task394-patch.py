#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 394 — заявка (3 части):
#   (1) десктоп: блок отпусков — СПРАВА от блока профиля, блок СИЗ —
#       ПОД ним, все четыре блока — РАВНОМЕРНО по горизонтали на
#       весь экран (сетка 2×2, обёртка .ws-wgrid2);
#   (2) в картах работников мероприятия — на ВЕСЬ ГОД (не месяц);
#   (3) в окне мероприятий месяца табеля — та же информация по
#       ОТПУСКАМ (частично попадающие на два месяца — в окнах ОБЕИХ
#       месяцев) и по СИЗ (срок годности истекает в месяце).
# Все правки — только index.html (сервер listTrainings уже умеет
# годовой охват без month: «если month не указан — все мероприятия
# года»; Apps Script не трогается).
import sys

path = 'index.html'
src = open(path, encoding='utf-8').read()

REPLS = []
def rep(old, new, cnt=1):
    REPLS.append((old, new, cnt))

# --- R1: CSS — .ws-workers-body без капа 1020px (на весь экран) ---
rep(
"""    .ws-workers-body {
        padding: 10px 12px 24px;
        max-width: 1020px;   /* Task 388: вкладки слева + карточка справа */
""",
"""    .ws-workers-body {
        padding: 10px 12px 24px;
        /* Task 394 (заявка): четыре блока карточки — РАВНОМЕРНО по
           горизонтали НА ВЕСЬ ЭКРАН: кап 1020px (Task 388) снят */
"""
)

# --- R2: CSS — сетка 2×2 на десктопе (≥1024px) ---
rep(
"""    /* Task 393: в теле вкладки карточка — ЧЕТЫРЕ блока-окна: зазор
       между ними — margin-bottom, у последнего — 0 */
    .ws-wtab-body .ws-wcard { margin-bottom: 12px; }
    .ws-wtab-body .ws-wcard:last-child { margin-bottom: 0; }
""",
"""    /* Task 393: в теле вкладки карточка — ЧЕТЫРЕ блока-окна: зазор
       между ними — margin-bottom, у последнего — 0 (мобильный стек;
       на десктопе зазор задаёт сетка Task 394 ниже) */
    .ws-wtab-body .ws-wcard { margin-bottom: 12px; }
    .ws-wtab-body .ws-wcard:last-child { margin-bottom: 0; }
    /* Task 394 (заявка): ДЕСКТОП (≥1024px) — четыре блока карточки
       СЕТКОЙ 2×2, РАВНЫЕ колонки НА ВСЮ ШИРИНУ окна вкладок:
       профиль — слева сверху, ОТПУСКА — СПРАВА от профиля,
       МЕРОПРИЯТИЯ — под профилем, СИЗ — ПОД ОТПУСКАМИ (порядок
       блоков b1–b4 раскладывается сеткой сам). Обёртка .ws-wgrid2 —
       _renderWorkersPage (только вкладка работника; «Общая» — без
       сетки). Окна НЕ тянутся по высоте чужих строк (align-items:
       start); зазор — gap 12px, margin-bottom обнулён (базовые
       правила Task 393 остаются для мобильного стека ≤1023px) */
    @media (min-width: 1024px) {
        .ws-wgrid2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            align-items: start;
        }
        .ws-wgrid2 .ws-wcard { margin-bottom: 0; }
    }
"""
)

# --- R3: CSS — плашки/точки секций «Отпуска» и «СИЗ» окна мероприятий ---
rep(
"""    [data-theme="light"] .ws-ep-cap {
        background: rgba(76, 199, 113, 0.16);
        /* Task 330 (заявка): ВЕСЬ текст окон бара — ЧЁРНЫЙ в светлой
           теме (прежде — приглушённые цветные/серые: зелёный/синий/
           красный/серый — на светлом фоне читались слабо) */
        color: #000;
    }
""",
"""    [data-theme="light"] .ws-ep-cap {
        background: rgba(76, 199, 113, 0.16);
        /* Task 330 (заявка): ВЕСЬ текст окон бара — ЧЁРНЫЙ в светлой
           теме (прежде — приглушённые цветные/серые: зелёный/синий/
           красный/серый — на светлом фоне читались слабо) */
        color: #000;
    }
    /* Task 394 (заявка): окно «Мероприятия» месяца — СЕКЦИИ «Отпуска»
       и «СИЗ» (заполняет _renderMonthEventsPanel): заголовки — те же
       плашки .ws-ep-cap своих цветов (мероприятия — зелёная, как
       прежде; отпуска — серо-синяя, СИЗ — янтарная). Точки строк —
       фиксированные читаемые тона для ОБОИХ тем: цвет «ОТ» #ECEFF1
       (фон клеток плана отпуска) слишком светел для точки 8×8 — в
       светлой теме почти невидим; точка отпуска — нейтральный
       #90a4ae, точка СИЗ — янтарная #f0a830 */
    .ws-ep-cap-vac {
        background: rgba(144, 164, 174, 0.22);
        color: #b0bec5;
    }
    .ws-ep-cap-ppe {
        background: rgba(240, 168, 48, 0.2);
        color: #f0a830;
    }
    [data-theme="light"] .ws-ep-cap-vac,
    [data-theme="light"] .ws-ep-cap-ppe {
        /* Task 330: весь текст окон бара — ЧЁРНЫЙ в светлой теме */
        color: #000;
    }
    .ws-ep-dot-vac { background: #90a4ae; }
    .ws-ep-dot-ppe { background: #f0a830; }
"""
)

# --- R4: JS — _loadTrainings на ВЕСЬ ГОД (без month) ---
rep(
"""        _loadTrainings: function() {
            var self = this;
            return this._api('workSchedule.listTrainings', { year: this._year, month: this._month })
                .then(function(data) {
                    self._TRAININGS = data.trainings || [];
                });
        },
""",
"""        // Task 394 (заявка): мероприятия грузятся на ВЕСЬ ГОД
        // шахматки — month НЕ указан (сервер listTrainings без
        // месяца отдаёт все записи, ПЕРЕСЕКАЮЩИЕ год): карточки
        // работников показывают мероприятия ЗА ГОД, а окно
        // мероприятий месяца, печать и бейджи ячеек фильтруют
        // список сами (месяц/даты). Локальная копия (Task 314),
        // записанная прежними версиями с месячным срезом, после
        // «Обновить» перезаписывается годовым списком
        _loadTrainings: function() {
            var self = this;
            return this._api('workSchedule.listTrainings', { year: this._year })
                .then(function(data) {
                    self._TRAININGS = data.trainings || [];
                });
        },
"""
)

# --- R5: JS — карточка: monthNames больше не нужен (заголовок — ГОД) ---
rep(
"""            var monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];

            // Task 393: карточка собирается ЧЕТЫРЬМЯ блоками — b1
""",
"""            // Task 394: monthNames карточке больше не нужен —
            // заголовок блока мероприятий теперь ГОД, не месяц

            // Task 393: карточка собирается ЧЕТЫРЬМЯ блоками — b1
"""
)

# --- R6: JS — карточка: секция 3 — мероприятия ГОДА ---
rep(
"""            // --- Секция 3: мероприятия месяца (бывшая вкладка
            //     «Инструктажи»; _TRAININGS загружены listTrainings
            //     для года/месяца шахматки) ---
            var trs = [];
            for (var ti = 0; ti < (this._TRAININGS || []).length; ti++) {
                if (this._TRAININGS[ti]['таб_номер'] === tabNo) {
                    trs.push(this._TRAININGS[ti]);
                }
            }
            trs.sort(function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            });
            var b3 = '<div class="ws-popup-sec">Мероприятия · ' +
                     monthNames[this._month - 1] + ' ' + this._year + '</div>';
            if (!trs.length) {
                b3 += '<div class="ws-emp-empty">нет мероприятий в месяце</div>';
""",
"""            // --- Секция 3: мероприятия ГОДА (бывшая вкладка
            //     «Инструктажи»; Task 394 — заявка: в карточках
            //     работников мероприятия указываются НА ВЕСЬ ГОД).
            //     _TRAININGS — ГОДОВОЙ список (listTrainings без
            //     месяца); сверка пересечения с годом шахматки —
            //     защита от смешанных/устаревших данных (кэш
            //     прежних версий мог лежать месячным срезом) ---
            var trs = [];
            var trYStart = this._year + '-01-01', trYEnd = this._year + '-12-31';
            for (var ti = 0; ti < (this._TRAININGS || []).length; ti++) {
                var tRec = this._TRAININGS[ti];
                if (tRec['таб_номер'] !== tabNo) continue;
                var tS = String(tRec['дата_начала'] || '');
                if (!tS) continue;
                var tE = String(tRec['дата_окончания'] || tS);
                if (tE < trYStart || tS > trYEnd) continue;
                trs.push(tRec);
            }
            trs.sort(function(a, b) {
                return String(a.дата_начала).localeCompare(String(b.дата_начала));
            });
            var b3 = '<div class="ws-popup-sec">Мероприятия · ' +
                     this._year + '</div>';
            if (!trs.length) {
                b3 += '<div class="ws-emp-empty">нет мероприятий за год</div>';
"""
)

# --- R7: JS — _renderWorkersPage: обёртка .ws-wgrid2 ---
rep(
"""                contentHtml = this._renderWorkerCardPanels(empTabNo, withEdit);
            }
""",
"""                // Task 394 (заявка): четыре блока-окна — в обёртке
                // .ws-wgrid2: десктоп ≥1024px — СЕТКА 2×2 на всю
                // ширину (профиль слева сверху / отпуска справа от
                // профиля / мероприятия под профилем / СИЗ под
                // отпусками); мобайл — прежний вертикальный стек
                // (обёртка без правил сетки)
                contentHtml = '<div class="ws-wgrid2">' +
                    this._renderWorkerCardPanels(empTabNo, withEdit) + '</div>';
            }
"""
)

# --- R8: JS — _renderWorkersGeneral: комментарий (мероприятия ГОДА) ---
rep(
"""        // работы (тип/смена), должность, дата приёма, отпуск года
        // («чистые» дни — праздники ст. 120 ТК РФ вычтены) и число
        // мероприятий месяца шахматки.
""",
"""        // работы (тип/смена), должность, дата приёма, отпуск года
        // («чистые» дни — праздники ст. 120 ТК РФ вычтены) и число
        // мероприятий ГОДА (Task 394: годовой список listTrainings).
"""
)

# --- R9: JS — _renderWorkersGeneral: monthNames не нужен ---
rep(
"""        _renderWorkersGeneral: function(list) {
            var monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                              'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
            // Task 390: подсчёт по категориям ДО шапки — мастера по
""",
"""        _renderWorkersGeneral: function(list) {
            // Task 394: monthNames не нужен — колонка мероприятий
            // теперь «Мероприятия · ГОД» (не месяц шахматки)
            // Task 390: подсчёт по категориям ДО шапки — мастера по
"""
)

# --- R10: JS — _renderWorkersGeneral: колонка «Мероприятия · ГОД» ---
rep(
"""                    '<th>Отпуск · ' + this._year + '</th>' +
                    '<th>Мероприятия · ' + monthNames[this._month - 1] + '</th>' +
""",
"""                    '<th>Отпуск · ' + this._year + '</th>' +
                    '<th>Мероприятия · ' + this._year + '</th>' +
"""
)

# --- R11: JS — _renderMonthEventsPanel: секции «Отпуска» и «СИЗ» ---
rep(
"""                html += '<span class="ws-ep-item' + pastCls + '">' +
                        '<i class="ws-ep-dot" style="background:' + (meta.color || '#3a3a3a') + ';"></i>' +
                        '<b class="ws-ep-date">' + this._esc(range) + '</b>' +
                        '<span class="ws-ep-text">' + this._esc(text) + '</span></span>';
            }
            el.innerHTML = html;
""",
"""                html += '<span class="ws-ep-item' + pastCls + '">' +
                        '<i class="ws-ep-dot" style="background:' + (meta.color || '#3a3a3a') + ';"></i>' +
                        '<b class="ws-ep-date">' + this._esc(range) + '</b>' +
                        '<span class="ws-ep-text">' + this._esc(text) + '</span></span>';
            }
            // Task 394 (заявка): в окне мероприятий месяца — ТАК ЖЕ
            // ОТПУСКА и СИЗ. Отпуска — периоды листа «Отпуска»,
            // ПЕРЕСЕКАЮЩИЕ открытый месяц (частично попадающие на
            // два месяца показываются в окнах ОБЕИХ месяцев — фильтр
            // пересечения тот же, что у мероприятий); выбранный день
            // (Task 316) — только накрывающие день. СИЗ — записи, чей
            // срок годности ИСТЕКАЕТ в этом месяце (дата_окончания
            // внутри месяца; «До износа»/без даты — не показываются);
            // в режиме дня — истекающие ровно в выбранный день.
            // ПУСТЫЕ секции скрыты (окно не шумит зря); заголовки —
            // те же плашки со счётчиком, строки — формат «точка ·
            // даты · текст»; ПРОШЕДШИЕ (дата раньше «сегодня») —
            // прозрачный фон .ws-ep-past (Tasks 380/389)
            var vacList = [];
            var vacsAll = this._VACATIONS || [];
            for (var vI = 0; vI < vacsAll.length; vI++) {
                var vRec = vacsAll[vI];
                var vS = vRec['дата_начала'];
                if (!vS) continue;
                var vE = vRec['дата_окончания'] || vS;
                if (vE < mStart || vS > mEnd) continue;
                if (selIso && (vS > selIso || vE < selIso)) continue;
                vacList.push(vRec);
            }
            vacList.sort(function(a, b) {
                return String(a['дата_начала']).localeCompare(String(b['дата_начала'])) ||
                       String(a['таб_номер']).localeCompare(String(b['таб_номер']));
            });
            if (vacList.length) {
                html += '<span class="ws-cp-cap ws-ep-cap ws-ep-cap-vac">Отпуска · ' +
                        (selIso ? this._esc(fmtDay(selIso))
                                : this._esc(monthsNom[m - 1]) + ' ' + y) +
                        ' · ' + vacList.length + '</span>';
                for (var vk = 0; vk < vacList.length; vk++) {
                    var vac = vacList[vk];
                    var vFio = fioIdx[vac['таб_номер']] || ('таб. №' + vac['таб_номер']);
                    var vRange = fmtRange(vac['дата_начала'], vac['дата_окончания']);
                    var vEndIso = String(vac['дата_окончания'] || vac['дата_начала'] || '');
                    var vPast = (vEndIso && vEndIso < todayIso) ? ' ws-ep-past' : '';
                    html += '<span class="ws-ep-item' + vPast + '">' +
                            '<i class="ws-ep-dot ws-ep-dot-vac"></i>' +
                            '<b class="ws-ep-date">' + this._esc(vRange) + '</b>' +
                            '<span class="ws-ep-text">' +
                            this._esc('Отпуск · ' + vFio) + '</span></span>';
                }
            }
            var ppeList = [];
            var ppeAll = this._PPE || [];
            for (var pzI = 0; pzI < ppeAll.length; pzI++) {
                var pRec = ppeAll[pzI];
                var pExpIso = String(pRec['дата_окончания'] || '').trim();
                if (!pExpIso || pExpIso === 'До износа') continue;
                if (pExpIso < mStart || pExpIso > mEnd) continue;
                if (selIso && pExpIso !== selIso) continue;
                ppeList.push(pRec);
            }
            ppeList.sort(function(a, b) {
                return String(a['дата_окончания']).localeCompare(String(b['дата_окончания'])) ||
                       String(a['таб_номер']).localeCompare(String(b['таб_номер']));
            });
            if (ppeList.length) {
                html += '<span class="ws-cp-cap ws-ep-cap ws-ep-cap-ppe">СИЗ · ' +
                        (selIso ? this._esc(fmtDay(selIso))
                                : this._esc(monthsNom[m - 1]) + ' ' + y) +
                        ' · ' + ppeList.length + '</span>';
                for (var pk2 = 0; pk2 < ppeList.length; pk2++) {
                    var ppz = ppeList[pk2];
                    var pFio = fioIdx[ppz['таб_номер']] || ('таб. №' + ppz['таб_номер']);
                    var pPast = (String(ppz['дата_окончания'] || '') < todayIso)
                        ? ' ws-ep-past' : '';
                    html += '<span class="ws-ep-item' + pPast + '">' +
                            '<i class="ws-ep-dot ws-ep-dot-ppe"></i>' +
                            '<b class="ws-ep-date">до ' +
                            this._esc(fmtDay(ppz['дата_окончания'])) + '</b>' +
                            '<span class="ws-ep-text">' +
                            this._esc('СИЗ · ' + String(ppz['наименование'] || '') +
                                      ' · ' + pFio) + '</span></span>';
                }
            }
            el.innerHTML = html;
"""
)

ok = 0
for i, (old, new, cnt) in enumerate(REPLS, 1):
    n = src.count(old)
    if n != cnt:
        print('R%d: ЯКОРЬ НЕ НАЙДЕН (%d раз, ожидалось %d): %r' % (i, n, cnt, old[:70]))
        sys.exit(1)
    src = src.replace(old, new)
    ok += 1

open(path, 'w', encoding='utf-8').write(src)
print('Task 394: применено правок %d (index.html)' % ok)

# Контроль: ключевые маркеры новой версии
checks = [
    ("listTrainings', { year: this._year }", 1),
    ('ws-wgrid2', 3),           # CSS-правила + JS-обёртка (минимум)
    ("Мероприятия · ' +\n                     this._year + '</div>'", 1),
    ('нет мероприятий за год', 1),
    ('ws-ep-cap-vac', 3),       # CSS ×2 + JS
    ('ws-ep-cap-ppe', 3),
    ('ws-ep-dot-vac', 2),
    ('ws-ep-dot-ppe', 2),
]
for marker, minimum in checks:
    if src.count(marker) < minimum:
        print('КОНТРОЛЬ ПРОВАЛЕН: маркер %r (%d < %d)' % (marker, src.count(marker), minimum))
        sys.exit(1)
print('Контроль маркеров: ок')
