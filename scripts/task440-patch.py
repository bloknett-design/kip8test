#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 440 — патч index.html (kip8test), 3 части:
1) зазор 10px между мероприятиями и кодами во всех ТРЁХ представлениях
   печати (HTML gap 6mm→10px; PDF colGap 12→7.5pt [10 CSS-px = 7.5 pt];
   Excel — отступ indent="1" (~7px, ближайшее достижимое: колонки D
   общие с сеткой дней) у кодов в колонке D);
2) баг › в «Повторных инструктажах…» (fam 1): верх навигации — по
   ЗАПИСЯМ раздела (новый _wtabYearMax), не только текущий/год табеля;
3) блок «Отпуска» (fam 2, НОВОЕ хранилище _wtabYearVac): навигация
   ‹год› по записям серверной таблицы «Отпуска» — пул _VAC_YEARS
   (ленивая подгрузка соседних годов _vacYearEnsure, окно ±3 года),
   «Мероприятия» (fam 0) — тот же фикс максимума.
"""
import io, sys

PATH = '/home/z/my-project/kip8test/index.html'
src = io.open(PATH, encoding='utf-8').read()
orig = src
n = [0]

def rep(old, new, what):
    global src
    cnt = src.count(old)
    assert cnt == 1, 'FAIL [%s]: найдено %d вхождений (ожидалось 1)' % (what, cnt)
    src = src.replace(old, new)
    n[0] += 1
    print('OK  %02d) %s' % (n[0], what))

# ----------------------------------------------------------------------
# ЧАСТЬ 1.1 — HTML печать: зазор ряда wsp-bottom 6mm → 10px
# ----------------------------------------------------------------------
rep("""               мероприятий»): нижняя секция — ГИБКИЙ РЯД: список
               мероприятий слева (растягивается на остаток), блок
               кодов — справа фиксированной ширины, зазор 6mm */
            display: flex;
            align-items: flex-start;
            gap: 6mm;
        }""",
    """               мероприятий»): нижняя секция — ГИБКИЙ РЯД: список
               мероприятий слева (растягивается на остаток), блок
               кодов — справа фиксированной ширины. Task 440 (заявка:
               «коды справа от мероприятий на расстоянии друг от
               друга 10px»): зазор между блоками — РОВНО 10px (прежде
               6mm ≈ 23px) */
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }""",
    'CSS печать: gap 10px в .wsp-bottom')

# ----------------------------------------------------------------------
# ЧАСТЬ 1.2 — PDF: colGap 12 → 7.5 pt (10 CSS-px = 7.5 pt)
# ----------------------------------------------------------------------
rep("""            // Task 439: коды — СПРАВА от мероприятий: ширина
            // правой зоны кодов и зазор между блоками
            var codeW = opts.codeW || 235;
            var colGap = opts.colGap || 12;""",
    """            // Task 439: коды — СПРАВА от мероприятий: ширина
            // правой зоны кодов и зазор между блоками. Task 440
            // (заявка: «на расстоянии друг от друга 10px»): зазор
            // 12pt → 7.5pt — РОВНО 10 CSS-px (1px = 0.75pt), как в
            // печатной HTML-форме (gap: 10px)
            var codeW = opts.codeW || 235;
            var colGap = opts.colGap || 7.5;""",
    'PDF _printPdfLayout: colGap 7.5pt')

rep("""            var codeW = lay.codeW || 235;
            var colGap = lay.colGap || 12;""",
    """            var codeW = lay.codeW || 235;
            // Task 440: зазор мероприятий↔коды — 7.5pt (= 10px)
            var colGap = lay.colGap || 7.5;""",
    'PDF _printPdfPaintPage: colGap 7.5pt')

# ----------------------------------------------------------------------
# ЧАСТЬ 1.3 — Excel: отступ indent="1" у кодов (D), +2 базовых стиля
# ----------------------------------------------------------------------
rep("""            xf += '<xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment horizontal="center"/></xf>';
            for (var k = 0; k < colors.length; k++) {""",
    """            xf += '<xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment horizontal="center"/></xf>';
            // Task 440 (заявка: «коды справа от мероприятий на
            // расстоянии друг от друга 10px»): Excel-эквивалент
            // зазора — ОТСТУП indent="1" (~7px = ширина символа
            // Arial 11) у ячеек КОДОВ в колонке D: текст мероприятий
            // (A/B) переполнением через пустую C обрезается у левой
            // кромки D, а текст кодов начинается на ~7px ПРАВЕЕ
            // кромки — видимый зазор между блоками (10px точно
            // недостижимы: колонка-разделитель C общая с сеткой дней
            // табеля, сузить её нельзя). Стиль 7 — строка кода,
            // стиль 8 — заголовок «Коды:» (шапка как s=1 + отступ)
            xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">' +
                  '<alignment horizontal="left" indent="1"/></xf>';
            xf += '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1">' +
                  '<alignment horizontal="left" indent="1"/></xf>';
            for (var k = 0; k < colors.length; k++) {""",
    'Excel styles: +2 стиля с indent="1" (код-строка s7, «Коды:» s8)')

rep("""                '<cellXfs count="' + (7 + colors.length) + '">' + xf +""",
    """                '<cellXfs count="' + (9 + colors.length) + '">' + xf +""",
    'Excel styles: cellXfs count 9 + colors')

# сетка: цветные ячейки теперь 9 + idx (стили 7/8 заняты кодами)
rep("""                        if (colorIdx[col] !== undefined) {
                            st = 7 + colorIdx[col];
                        }""",
    """                        // Task 440: база цветных стилей 9 (7/8 —
                        // коды с indent)
                        if (colorIdx[col] !== undefined) {
                            st = 9 + colorIdx[col];
                        }""",
    'Excel rows: цветные ячейки стили 9+idx')

# нижняя секция: «Коды:» s:1 → s:8, строки кодов s:0 → s:7
rep("""            rows.push([{ v: 'Мероприятия · ' +
                         monthsNom[model.month - 1] + ' ' + model.year +
                         (model.events.length
                             ? ' · ' + model.events.length : ''), s: 1 },
                       null, null, { v: 'Коды:', s: 1 }]);""",
    """            rows.push([{ v: 'Мероприятия · ' +
                         monthsNom[model.month - 1] + ' ' + model.year +
                         (model.events.length
                             ? ' · ' + model.events.length : ''), s: 1 },
                       null, null, { v: 'Коды:', s: 8 }]);""",
    'Excel rows: «Коды:» — стиль 8 (шапка + indent)')

rep("""                rows.push([bev ? { v: bev.a || '', s: bev.as } : null,
                           bev && bev.b ? { v: bev.b, s: bev.bs } : null,
                           null,
                           codeLines[b] !== undefined
                               ? { v: codeLines[b], s: 0 } : null]);""",
    """                rows.push([bev ? { v: bev.a || '', s: bev.as } : null,
                           bev && bev.b ? { v: bev.b, s: bev.bs } : null,
                           null,
                           codeLines[b] !== undefined
                               ? { v: codeLines[b], s: 7 } : null]);""",
    'Excel rows: строки кодов — стиль 7 (indent)')

# ----------------------------------------------------------------------
# ЧАСТЬ 2 — _wtabYearMax: верх навигации по ЗАПИСЯМ раздела
# ЧАСТЬ 3 — fam 2 «Отпуска»: _vacYearRange + пул _VAC_YEARS
# ----------------------------------------------------------------------

# _wtabYearOf: fam 2 → _wtabYearVac
rep("""        // Task 435: fam 1 — год блока «Повторные инструктажи…»
        // (хранилище _wtabYearInstr), fam 0/не задан — год блока
        // «Мероприятия» (хранилище _wtabYear, прежнее поведение)
        _wtabYearOf: function(tabNo, fam) {
            var store = (fam === 1) ? this._wtabYearInstr : this._wtabYear;""",
    """        // Task 435: fam 1 — год блока «Повторные инструктажи…»
        // (хранилище _wtabYearInstr), fam 0/не задан — год блока
        // «Мероприятия» (хранилище _wtabYear, прежнее поведение).
        // Task 440: fam 2 — год блока «Отпуска» (хранилище
        // _wtabYearVac) — третий независимый год карточки
        _wtabYearOf: function(tabNo, fam) {
            var store = (fam === 1) ? this._wtabYearInstr
                       : (fam === 2) ? this._wtabYearVac : this._wtabYear;""",
    '_wtabYearOf: fam 2 → _wtabYearVac')

# _wtabYearMin: ветка fam 2 (по пулу отпусков) — вставка ДО famFilter
rep("""        _wtabYearMin: function(tabNo, fam) {
            tabNo = String(tabNo);
            var famFilter = (fam === 0 || fam === 1);""",
    """        _wtabYearMin: function(tabNo, fam) {
            tabNo = String(tabNo);
            // Task 440: fam 2 — блок «Отпуска»: нижняя граница по
            // годам пула _VAC_YEARS с записями работника (сервер
            // listVacations отдаёт план по ОДНОМУ году — пул
            // собирается соседними годами, _vacYearEnsure)
            if (fam === 2) {
                var vr = this._vacYearRange(tabNo);
                return vr ? vr.min
                    : (this._year || new Date().getFullYear());
            }
            var famFilter = (fam === 0 || fam === 1);""",
    '_wtabYearMin: ветка fam 2 (пул отпусков)')

# НОВЫЕ методы _vacYearRange + _wtabYearMax — после _wtabYearMin
rep("""            return min || (this._year || new Date().getFullYear());
        },

        // стрелка ‹/› — смена года работника и перерисовка страницы""",
    """            return min || (this._year || new Date().getFullYear());
        },

        // Task 440: годы с записями ОТПУСКОВ работника в пуле
        // _VAC_YEARS (listVacations по одному году — пул собирает
        // соседние годы лениво, _vacYearEnsure): {min, max} или null,
        // если записей работника в известных годах нет. Пересечение
        // года и периода — _vacDaysInYear (период через границу года
        // попадает в оба года, как на сервере)
        _vacYearRange: function(tabNo) {
            tabNo = String(tabNo);
            var pool = this._VAC_YEARS || {};
            var min = null, max = null;
            for (var vy in pool) {
                if (!pool.hasOwnProperty(vy)) continue;
                var y = parseInt(vy, 10);
                if (!y) continue;
                var arr = pool[vy] || [];
                for (var i = 0; i < arr.length; i++) {
                    if (String(arr[i]['таб_номер']) !== tabNo) continue;
                    if (this._vacDaysInYear(arr[i], y) <= 0) continue;
                    if (min === null || y < min) min = y;
                    if (max === null || y > max) max = y;
                }
            }
            return (min === null) ? null : { min: min, max: max };
        },

        // Task 440 (заявка: «не активна кнопка просмотра следующего
        // года, если в таблице Инструктажи … есть записи на следующий
        // год, а на предыдущий год при наличии записей активна»):
        // ВЕРХНЯЯ граница навигации — по ЗАПИСАМ раздела (симметрично
        // нижней _wtabYearMin): самый поздний год записи работника;
        // учитывает и дата_окончания — период 27.12.2026–15.01.2027
        // открывает и следующий год. fam 0/1 — instrAll/eventsAll/
        // trainings с фильтром СВОЕГО раздела (как _wtabYearMin),
        // fam 2 — пул отпусков _vacYearRange, fam не задан — все
        // записи; нет записей — null (звавший подставляет текущий и
        // год табеля)
        _wtabYearMax: function(tabNo, fam) {
            tabNo = String(tabNo);
            if (fam === 2) {
                var vr2 = this._vacYearRange(tabNo);
                return vr2 ? vr2.max : null;
            }
            var famFilter = (fam === 0 || fam === 1);
            var wantInstr = (fam === 1);
            var max = null;
            var pools = [this._INSTR_ALL, this._EVENTS_ALL,
                         this._TRAININGS];
            for (var p = 0; p < pools.length; p++) {
                var arr = pools[p] || [];
                for (var i = 0; i < arr.length; i++) {
                    if (String(arr[i]['таб_номер']) !== tabNo) continue;
                    if (famFilter &&
                        (this._isInstrType(arr[i].тип) !== wantInstr)) continue;
                    var sM = String(arr[i].дата_начала || '');
                    var eM = String(arr[i].дата_окончания || sM);
                    var yS = sM.length >= 4
                        ? parseInt(sM.slice(0, 4), 10) : 0;
                    var yE = eM.length >= 4
                        ? parseInt(eM.slice(0, 4), 10) : 0;
                    var y = Math.max(yS || 0, yE || 0);
                    if (y && (max === null || y > max)) max = y;
                }
            }
            return max;
        },

        // стрелка ‹/› — смена года работника и перерисовка страницы""",
    'НОВЫЕ методы _vacYearRange + _wtabYearMax')

# _wtabYearShift: store fam 2 + max по записям
rep("""            var y = this._wtabYearOf(tabNo, fam) + (delta || 0);
            var min = this._wtabYearMin(tabNo, fam);
            var max = Math.max(now, this._year || now);
            if (y < min) y = min;
            if (y > max) y = max;
            var store = (fam === 1) ? '_wtabYearInstr' : '_wtabYear';""",
    """            var y = this._wtabYearOf(tabNo, fam) + (delta || 0);
            var min = this._wtabYearMin(tabNo, fam);
            // Task 440: верх — и по ЗАПИСЯМ раздела (кнопка › активна,
            // когда есть записи следующего года — заявка «не активна
            // кнопка просмотра следующего года…»)
            var max = Math.max(now, this._year || now,
                               this._wtabYearMax(tabNo, fam) || 0);
            if (y < min) y = min;
            if (y > max) y = max;
            var store = (fam === 1) ? '_wtabYearInstr'
                       : (fam === 2) ? '_wtabYearVac' : '_wtabYear';""",
    '_wtabYearShift: fam 2 + max по записям')

# _wtabYearNav: max по записям + famArg fam 2
rep("""        _wtabYearNav: function(tabNo, year, fam) {
            var min = this._wtabYearMin(tabNo, fam);
            var now = new Date().getFullYear();
            var max = Math.max(now, this._year || now);
            var famArg = (fam === 1) ? ', 1' : '';""",
    """        _wtabYearNav: function(tabNo, year, fam) {
            var min = this._wtabYearMin(tabNo, fam);
            var now = new Date().getFullYear();
            // Task 440: правая стрелка активна и при записях
            // СЛЕДУЮЩЕГО года (верх — по записям раздела), не только
            // до текущего/года табеля
            var max = Math.max(now, this._year || now,
                               this._wtabYearMax(tabNo, fam) || 0);
            var famArg = (fam === 1 || fam === 2) ? ', ' + fam : '';""",
    '_wtabYearNav: max по записям + famArg 2')

# хранилище _wtabYearVac (объявление свойств)
rep("""        // Task 408: выбранный ГОД блоков карточки по работникам
        // (стрелки ‹год›; не выбран — год шахматки). Task 435: годы
        // блоков РАЗДЕЛЬНЫЕ — «Мероприятия» (_wtabYear, fam 0) и
        // «Повторные инструктажи…» (_wtabYearInstr, fam 1) не
        // влияют друг на друга
        _wtabYear: {},
        _wtabYearInstr: {},""",
    """        // Task 408: выбранный ГОД блоков карточки по работникам
        // (стрелки ‹год›; не выбран — год шахматки). Task 435: годы
        // блоков РАЗДЕЛЬНЫЕ — «Мероприятия» (_wtabYear, fam 0) и
        // «Повторные инструктажи…» (_wtabYearInstr, fam 1) не
        // влияют друг на друга. Task 440: + «Отпуска» (fam 2,
        // _wtabYearVac) — третий независимый год (заявка: «такой же
        // функционал просмотра предыдущего или следующего годов … в
        // блоках Отпуска и Мероприятия»)
        _wtabYear: {},
        _wtabYearInstr: {},
        _wtabYearVac: {},""",
    'свойство _wtabYearVac')

# свойство _VAC_YEARS рядом с _VACATIONS
rep("""        _VACATIONS: [],
        _VAC_PAGE: [],
        _vacYear: null,""",
    """        _VACATIONS: [],
        _VAC_PAGE: [],
        _vacYear: null,
        // Task 440: ПУЛ отпусков ПО ГОДАМ — {год: [записи]} для
        // навигации ‹год› блока «Отпуска» карточки: год шахматки
        // свежий (обновляет _loadVacations), соседние годы — лениво
        // (_vacYearEnsure, окно ±3 года), живут в локальной копии
        // (_cacheWrite/_restoreCachedView); CRUD/«Обновить» сбрасывают
        _VAC_YEARS: {},""",
    'свойство _VAC_YEARS')

# ----------------------------------------------------------------------
# ЧАСТЬ 3 — карточка: блок «Отпуска» с навигацией fam 2
# ----------------------------------------------------------------------
rep("""            // --- Секция 2: отпуска года шахматки (бывшая вкладка
            //     «Отпуска»; _VACATIONS уже отфильтрованы по году
            //     сервером listVacations, дополнительно сверяем
            //     пересечение с годом — период 29.12–11.01 попадает
            //     в оба, дни года считает _vacDaysInYear) ---
            var vacs = [];
            for (var vi = 0; vi < (this._VACATIONS || []).length; vi++) {
                var v = this._VACATIONS[vi];
                if (v['таб_номер'] !== tabNo) continue;
                if (this._vacDaysInYear(v, this._year) <= 0) continue;
                vacs.push(v);
            }""",
    """            // --- Секция 2: отпуска года шахматки (бывшая вкладка
            //     «Отпуска»; _VACATIONS уже отфильтрованы по году
            //     сервером listVacations, дополнительно сверяем
            //     пересечение с годом — период 29.12–11.01 попадает
            //     в оба, дни года считает _vacDaysInYear).
            //     Task 440 (заявка: «такой же функционал просмотра
            //     предыдущего или следующего годов … в блоках Отпуска
            //     и Мероприятия»): у блока — СВОИ стрелки ‹год› (fam 2,
            //     хранилище _wtabYearVac): год просмотра не зависит от
            //     шахматки и соседних блоков; записи — пул годов
            //     _VAC_YEARS (год шахматки — свежий _VACATIONS,
            //     соседние годы — listVacations по году, лениво,
            //     _vacYearEnsure); попап ячейки — по-прежнему год
            //     шахматки, без навигатора ---
            var wYearVac = asBlocks ? this._wtabYearOf(tabNo, 2)
                                    : this._year;
            var vacPoolYear = ((this._VAC_YEARS || {})[wYearVac]) ||
                (wYearVac === this._year ? (this._VACATIONS || []) : []);
            var vacs = [];
            for (var vi = 0; vi < vacPoolYear.length; vi++) {
                var v = vacPoolYear[vi];
                if (v['таб_номер'] !== tabNo) continue;
                if (this._vacDaysInYear(v, wYearVac) <= 0) continue;
                vacs.push(v);
            }""",
    'карточка: пул отпусков по wYearVac')

rep("""            var b2 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Отпуска · ' +
                  this._year + '</div><div class="ws-whead-a">' +""",
    """            var b2 = asBlocks
                ? '<div class="ws-whead"><div class="ws-whead-t">Отпуска · ' +
                  wYearVac + this._wtabYearNav(tabNo, wYearVac, 2) +
                  '</div><div class="ws-whead-a">' +""",
    'карточка: шапка «Отпуска · год» + навигатор fam 2')

# ----------------------------------------------------------------------
# ЧАСТЬ 3 — пул: _loadVacations сеет текущий год + _vacYearEnsure
# ----------------------------------------------------------------------
rep("""        _loadVacations: function() {
            var self = this;
            return this._api('workSchedule.listVacations', { year: this._year })
                .then(function(data) {
                    self._VACATIONS = data.vacations || [];
                    self._VAC_PAGE = self._VACATIONS;
                    self._vacYear = self._year;
                })
                .catch(function() {
                    self._VACATIONS = [];
                    self._VAC_PAGE = [];
                });
        },""",
    """        _loadVacations: function() {
            var self = this;
            return this._api('workSchedule.listVacations', { year: this._year })
                .then(function(data) {
                    self._VACATIONS = data.vacations || [];
                    self._VAC_PAGE = self._VACATIONS;
                    self._vacYear = self._year;
                    // Task 440: год шахматки в пуле годов — всегда
                    // свежий (соседние годы — лениво, _vacYearEnsure)
                    if (!self._VAC_YEARS) self._VAC_YEARS = {};
                    self._VAC_YEARS[self._year] = self._VACATIONS;
                })
                .catch(function() {
                    self._VACATIONS = [];
                    self._VAC_PAGE = [];
                    if (!self._VAC_YEARS) self._VAC_YEARS = {};
                    self._VAC_YEARS[self._year] = [];
                });
        },

        // Task 440: ленивая подгрузка СОСЕДНИХ годов отпусков для
        // навигации ‹год› блока «Отпуска» (сервер listVacations отдаёт
        // план ТОЛЬКО по одному году): недостающие годы тянутся
        // ПАРАЛЛЕЛЬНО и складываются в пул _VAC_YEARS; год уже в пуле
        // или уже качается — пропускается (повторный рендер не
        // зацикливается); ошибка года = «известно пусто» (стрелки по
        // факту, без спама повторными запросами). Возврат —
        // Promise<boolean>: подтянулись ли НОВЫЕ годы (звавший может
        // перерисовать страницу «Работники» — стрелки по записям)
        _vacYearEnsure: function(years) {
            var self = this;
            if (!this._VAC_YEARS) this._VAC_YEARS = {};
            if (!this._VAC_FETCHING) this._VAC_FETCHING = {};
            var need = [];
            for (var i = 0; i < (years || []).length; i++) {
                var y = parseInt(years[i], 10);
                if (!y || y < 1900 || y > 2999) continue;
                if (this._VAC_YEARS[y] || this._VAC_FETCHING[y]) continue;
                if (!this._api) continue;
                need.push(y);
            }
            if (!need.length) return Promise.resolve(false);
            var got = false;
            var jobs = [];
            for (var j = 0; j < need.length; j++) {
                (function(year) {
                    self._VAC_FETCHING[year] = true;
                    jobs.push(self._api('workSchedule.listVacations',
                                        { year: year })
                        .then(function(data) {
                            self._VAC_YEARS[year] =
                                (data && data.vacations) || [];
                            got = true;
                        })
                        .catch(function() {
                            self._VAC_YEARS[year] = [];
                            got = true;
                        })
                        .then(function() {
                            delete self._VAC_FETCHING[year];
                        }));
                })(need[j]);
            }
            return Promise.all(jobs).then(function() { return got; });
        },""",
    '_loadVacations: посев пула + НОВЫЙ _vacYearEnsure')

# loadGrid(force): сброс пула соседних годов
rep("""            // Task 321: принудительное обновление («Обновить»,
            // увольнение/сотрудник/генерация) — годовой кэш итогов
            // устарел: сбрасываем, вкладка «Год» перезагрузится при
            // следующем показе
            if (force) this._YEAR_DATA = null;""",
    """            // Task 321: принудительное обновление («Обновить»,
            // увольнение/сотрудник/генерация) — годовой кэш итогов
            // устарел: сбрасываем, вкладка «Год» перезагрузится при
            // следующем показе
            if (force) {
                this._YEAR_DATA = null;
                // Task 440: соседние годы пула отпусков могли
                // измениться (CRUD отпусков / «Обновить») — сброс;
                // подтянутся заново при следующем рендере страницы
                // «Работники» (_vacYearEnsure)
                this._VAC_YEARS = {};
            }""",
    'loadGrid(force): сброс пула _VAC_YEARS')

# _restoreCachedView: посев пула всеми годами локальной копии
rep("""            this._VACATIONS = vacs;
            this._VAC_PAGE = vacs;
            this._vacYear = this._year;""",
    """            this._VACATIONS = vacs;
            this._VAC_PAGE = vacs;
            this._vacYear = this._year;
            // Task 440: пул годов отпусков — ВСЕ годы локальной копии
            // (соседние годы прошлых сессий сразу дают правильные
            // стрелки ‹› блока «Отпуска» без сети)
            this._VAC_YEARS = {};
            var cVac = c.vacations || {};
            for (var cvy in cVac) {
                if (cVac.hasOwnProperty(cvy) && Array.isArray(cVac[cvy])) {
                    this._VAC_YEARS[parseInt(cvy, 10)] = cVac[cvy];
                }
            }""",
    '_restoreCachedView: посев пула из кэша')

# _cacheWrite: соседние годы пула — в локальную копию
rep("""                if (!c.vacations || typeof c.vacations !== 'object') c.vacations = {};
                c.vacations[String(this._year)] = this._VACATIONS;""",
    """                if (!c.vacations || typeof c.vacations !== 'object') c.vacations = {};
                c.vacations[String(this._year)] = this._VACATIONS;
                // Task 440: соседние годы пула отпусков (навигация
                // блока «Отпуска») — тоже в локальную копию
                var poolW = this._VAC_YEARS || {};
                for (var py in poolW) {
                    if (poolW.hasOwnProperty(py) && poolW[py]) {
                        c.vacations[py] = poolW[py];
                    }
                }""",
    '_cacheWrite: пул годов в кэш')

# _renderWorkersPage: хук ленивой подгрузки окна годов
rep("""            if (!found) { tab = 'general'; this._workersTab = 'general'; }

            // ярлыки-вкладки: «Общая» + работники по фамильно""",
    """            if (!found) { tab = 'general'; this._workersTab = 'general'; }

            // Task 440: навигация ‹год› блока «Отпуска» — границы
            // стрелок по записям серверной таблицы «Отпуска»: сервер
            // отдаёт план по одному году — при показе КАРТОЧКИ лениво
            // подтягиваем окно [год табеля ±3] и соседей выбранного
            // года работника; подтянулись новые годы — перерисовка
            // (стрелки по факту записей; повторный проход найдёт все
            // годы в пуле — цикла нет)
            if (tab !== 'general' && this._api &&
                typeof this._wtabYearOf === 'function' &&
                typeof this._vacYearEnsure === 'function') {
                var vacNeed = [];
                for (var vy2 = this._year - 3; vy2 <= this._year + 3; vy2++) {
                    vacNeed.push(vy2);
                }
                var navVacY = this._wtabYearOf(tab, 2);
                vacNeed.push(navVacY - 1, navVacY + 1);
                var selfVac = this;
                this._vacYearEnsure(vacNeed).then(function(got) {
                    if (got) selfVac._renderWorkersPage();
                });
            }

            // ярлыки-вкладки: «Общая» + работники по фамильно""",
    '_renderWorkersPage: хук _vacYearEnsure (окно ±3 года)')

io.open(PATH, 'w', encoding='utf-8').write(src)
print('\nГОТОВО: %d замен, файл %d → %d строк' % (n[0], orig.count('\n') + 1, src.count('\n') + 1))
