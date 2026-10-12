#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 508 (kip8test) — «Кабельный журнал»: АРХИВ правок и удалений.

Заявка: «Добавь сохранение в архив журнала кто последний вносил правки
в каждый кабель, по столбцу name в таблице users файла KIP8_Access.
И удалённый кабель так же должен сохраняться с пометкой как архивный
по причине "Удалён", кто удалил, и не должен отображаться в
распечатываемом или сохраняемом в PDF файле, а в excel отображается.»

КЛИЕНТ (index.html):
  1) шапка-комментарий модуля — семантика архива;
  2) состояние: _archivedRows (архивные записи — только для Excel);
  3) _restoreCache/_idbRestore/load — сплит полного снапшота сервера
     (активные/архивные) через новый _splitArchived; кэш persists
     ПОЛНЫЙ список (офлайн-Excel видит удалённые);
  4) НОВЫЕ методы: _rowArchived/_splitArchived (флаги сервера),
     _excelModel (модель Excel: активные + архив, поиск учтён,
     сортировка № п/п), _cjArchiveCols (5 колонок блока «Архив»),
     _cjArchDate (ДД.ММ.ГГГГ);
  5) _saveCjXlsx — строит книгу по _excelModel (фолбэк — модель
     печати);
  6) _buildCjWorkbook — блок «Архив» (K–O: Статус/Кем удалён/Дата
     удаления/Последний редактор/Дата правки) ТОЛЬКО когда в модели
     есть архивные строки; пары шапки — длина группы динамическая
     (len, было 3 жёстко); mergeCells — динамически (7 при архиве,
     6 — без; прежняя структура сохранена дословно);
  7) confirmDelete/submitDelete — честные тексты (архив, «Удалён»).

SW: kipia-test-v729 → kipia-test-v730 (+ комментарий Task 508).
sync-cables.py: архивные строки (колонка «Архив» непустая) НЕ
попадают в data/cables.json (снимок активного журнала).
"""
import io
import sys

ROOT = '/home/z/my-project/kip8test'
INDEX = ROOT + '/index.html'
SW = ROOT + '/sw.js'
SYNC = ROOT + '/scripts/sync-cables.py'

fails = []


def patch(path, old, new, label, expect=1):
    src = io.open(path, encoding='utf-8').read()
    n = src.count(old)
    if n != expect:
        fails.append('%s: якорь ×%d (ожидалось %d)' % (label, n, expect))
        print('FAIL %s: ×%d' % (label, n))
        return
    src = src.replace(old, new, 1)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('OK   %s' % label)


# ============================================================
# 1. Шапка-комментарий модуля
# ============================================================
patch(INDEX,
"""    // Доступ: чтение — всем авторизованным, добавление/правка/удаление — Админ, ИТР ИОС, КИП ИОС pro.
    // ============================================================
    const KipCableJournal = {""",
"""    // Доступ: чтение — всем авторизованным, добавление/правка/удаление — Админ, ИТР ИОС, КИП ИОС pro.
    // Task 508 — АРХИВ ЖУРНАЛА (сервер CableJournal.gs Task 508):
    //   удалённые записи помечаются флагом _archived (колонка «Архив»
    //   листа = «Удалён»); активные — список/печать/PDF, архивные —
    //   только Excel-экспорт (_excelModel + блок «Архив» книги).
    //   «Последний редактор»/«Дата правки» (P/Q листа) — кто последний
    //   вносил правки (name из users KIP8_Access).
    // ============================================================
    const KipCableJournal = {""",
'1. шапка-комментарий модуля')

# ============================================================
# 2. Состояние: _archivedRows
# ============================================================
patch(INDEX,
"""        _editingRow: null,  // запись в режиме правки (мобильная форма) или null""",
"""        _editingRow: null,  // запись в режиме правки (мобильная форма) или null
        _archivedRows: null,  // Task 508: архивные записи (удалённые) — только для Excel-экспорта""",
'2. состояние _archivedRows')

# ============================================================
# 3a. _restoreCache: сплит кэша
# ============================================================
patch(INDEX,
"""                if (dataJson) {
                    const cached = JSON.parse(dataJson);
                    if (cached && Array.isArray(cached.rows)) {
                        this._rows = cached.rows;
                        this._total = cached.total || cached.rows.length;
                        this._render();
                    }
                }""",
"""                if (dataJson) {
                    const cached = JSON.parse(dataJson);
                    if (cached && Array.isArray(cached.rows)) {
                        // Task 508: кэш — полный снапшот (активные +
                        // архивные); архивные — только в Excel-экспорт
                        const split = this._splitArchived(cached.rows);
                        this._rows = split.active;
                        this._archivedRows = split.archived;
                        this._total = cached.total || split.active.length;
                        this._render();
                    }
                }""",
'3a. _restoreCache сплит')

# ============================================================
# 3b. _idbRestore: сплит кэша
# ============================================================
patch(INDEX,
"""                if (cached && Array.isArray(cached.rows)) {
                    if (!(self._rows && self._rows.length > 0)) {
                        self._rows = cached.rows;
                        self._total = cached.total || cached.rows.length;
                        self._allRows = self._rows.slice();
                        self._render();
                    }
                    return;
                }""",
"""                if (cached && Array.isArray(cached.rows)) {
                    if (!(self._rows && self._rows.length > 0)) {
                        // Task 508: полный снапшот (с архивом) — активные
                        // в список, архивные для Excel-экспорта
                        const split = self._splitArchived(cached.rows);
                        self._rows = split.active;
                        self._archivedRows = split.archived;
                        self._total = cached.total || split.active.length;
                        self._allRows = self._rows.slice();
                        self._render();
                    }
                    return;
                }""",
'3b. _idbRestore сплит')

# ============================================================
# 3c. load: сплит + полный кэш
# ============================================================
patch(INDEX,
"""            }).then(function(data) {
                self._rows = data.rows || [];
                self._total = data.total || 0;
                self._canEdit = !!data.canEdit;
                document.getElementById('cjAddBtn').style.display = self._canEdit ? '' : 'none';
                self._persistData(self._rows, self._total);""",
"""            }).then(function(data) {
                // Task 508: сервер помечает архивные записи (удалённые,
                // причина «Удалён») флагом _archived — активные идут в
                // список/печать/PDF, архивные только в Excel-экспорт
                const split = self._splitArchived(data.rows || []);
                self._rows = split.active;
                self._archivedRows = split.archived;
                self._total = data.total || split.active.length;
                self._canEdit = !!data.canEdit;
                document.getElementById('cjAddBtn').style.display = self._canEdit ? '' : 'none';
                // Кэш — ПОЛНЫЙ снапшот (активные + архив): офлайн-Excel
                // тоже видит удалённые записи
                self._persistData(data.rows || [], self._total);""",
'3c. load сплит + полный кэш')

# ============================================================
# 4a. НОВЫЕ методы _rowArchived/_splitArchived (перед toggleSearch)
# ============================================================
patch(INDEX,
"""        // ============================================================
        // Toggle компактного поиска в шапке.""",
"""        // ============================================================
        // Task 508: строка архивная? Сервер (CableJournal.gs Task 508)
        // помечает удалённые записи колонкой «Архив» (причина
        // «Удалён») и флагом _archived. До обновления сервера строк с
        // пометкой нет — поведение прежнее.
        // ============================================================
        _rowArchived: function(row) {
            if (!row) return false;
            if (row._archived === true) return true;
            if (row.archived === true) return true;
            if (typeof row.archived === 'string' &&
                    row.archived.trim() !== '') return true;
            return false;
        },

        // Task 508: полный список сервера → активные + архивные.
        // Активные — обычный конвейер (список, поиск, печать, PDF);
        // архивные — только Excel-экспорт (заявка: удалённый кабель
        // «в excel отображается», в печать/PDF не попадает).
        _splitArchived: function(rows) {
            var active = [], archived = [];
            if (Array.isArray(rows)) {
                for (var i = 0; i < rows.length; i++) {
                    if (this._rowArchived(rows[i])) archived.push(rows[i]);
                    else active.push(rows[i]);
                }
            }
            return { active: active, archived: archived };
        },

        // ============================================================
        // Toggle компактного поиска в шапке.""",
'4a. методы _rowArchived/_splitArchived')

# ============================================================
# 4b. НОВЫЙ метод _excelModel (перед комментарием колонок шаблона)
# ============================================================
patch(INDEX,
"""        // Task 506: колонки печатной таблицы — РОВНО как в шаблоне""",
"""        // ============================================================
        // Task 508: модель ДЛЯ EXCEL — активные строки + архивные
        // (заявка: «а в excel отображается»): печать/PDF строятся по
        // _printModel (только активные), Excel — по этой модели.
        // Поиск (Task 152) применяется и к архиву; сортировка — та
        // же «как в исходном файле» (№ п/п). archived — сколько
        // архивных строк в модели: по этому числу _buildCjWorkbook
        // добавляет блок колонок «Архив» (Статус/Кем удалён/Дата
        // удаления/Последний редактор/Дата правки).
        // ============================================================
        _excelModel: function() {
            var self = this;
            var active = (this._rows || []).slice();
            var arch = (this._archivedRows || []).slice();
            var q = '';
            try {
                var inp = document.getElementById('cjSearchInput');
                q = ((inp && inp.value) || '').trim();
            } catch (e) { q = ''; }
            if (q && arch.length && typeof kipSearchFilter === 'function') {
                arch = kipSearchFilter(arch, q, function (row) {
                    return [
                        row.department, row.designation, row.start, row.end,
                        row.mark, row.mark_actual, row.cores, row.cores_actual,
                        row.length, row.length_actual, row.notes
                    ].join(' ');
                });
            }
            var all = active.concat(arch);
            // сортировка «как в исходном файле» — № п/п (приём
            // _printModel: строки без номера — в конце, сортировка
            // стабильна)
            var numOf = function(row) {
                var n = row && row.num;
                if (typeof n === 'number' && isFinite(n)) return n;
                if (typeof n === 'string' && n.trim() &&
                        isFinite(parseFloat(n))) {
                    return parseFloat(n);
                }
                return null;
            };
            all.sort(function(a, b) {
                var va = numOf(a), vb = numOf(b);
                if (va === null && vb === null) return 0;
                if (va === null) return 1;
                if (vb === null) return -1;
                return va - vb;
            });
            var cols = this._cjPrintCols();
            var out = all.map(function(row) {
                var cells = {};
                cols.forEach(function(c) {
                    cells[c.key] = self._cjCellVal(row, c.key);
                });
                return { cells: cells, src: row };
            });
            var archShown = 0;
            out.forEach(function(r) {
                if (self._rowArchived(r.src)) archShown++;
            });
            return {
                rows: out,
                total: out.length,
                totalAll: out.length,
                filtered: false,
                archived: archShown
            };
        },

        // Task 506: колонки печатной таблицы — РОВНО как в шаблоне""",
'4b. метод _excelModel')

# ============================================================
# 4c. НОВЫЕ методы _cjArchiveCols/_cjArchDate (перед _cjFmtNum)
# ============================================================
patch(INDEX,
"""        // Task 505: число → строка с запятой (60 → «60», 43.5 → «43,5»)
        // Task 505: число → строка с запятой (60 → «60», 43.5 → «43,5»)
        _cjFmtNum: function(v) {""",
"""        // Task 508: колонки блока «Архив» в Excel-экспорте — статус
        // («Удалён»), кем/когда удалён, последний редактор/дата
        // правки. Добавляются к 10 колонкам шаблона ТОЛЬКО когда в
        // модели есть архивные строки (заявка: удалённые кабели — в
        // Excel, не в печать/PDF). w — pt-эквивалент для симметрии с
        // _cjPrintCols (в Excel ширины блока — из xlW книги).
        _cjArchiveCols: function() {
            return [
                { key: 'archived',     label: 'Статус',             w: 57, align: 'ctr', head: 'Архив' },
                { key: 'archived_by',  label: 'Кем удалён',         w: 78, align: 'left', head: 'Архив' },
                { key: 'archived_at',  label: 'Дата удаления',      w: 57, align: 'ctr', head: 'Архив' },
                { key: 'last_editor',  label: 'Последний редактор', w: 86, align: 'left', head: 'Архив' },
                { key: 'edited_at',    label: 'Дата правки',        w: 57, align: 'ctr', head: 'Архив' }
            ];
        },

        // Task 508: дата архива (ISO/строка) → «ДД.ММ.ГГГГ» для ячеек
        // Excel; не-дата — как есть (пустая — '')
        _cjArchDate: function(v) {
            if (v === null || v === undefined || v === '') return '';
            if (typeof v === 'number' && isFinite(v)) {
                return this._cjFmtNum(v);
            }
            var d = new Date(v);
            if (isNaN(d.getTime())) return String(v);
            var p2 = function(n) { return (n < 10 ? '0' : '') + n; };
            return p2(d.getDate()) + '.' + p2(d.getMonth() + 1) + '.' +
                   d.getFullYear();
        },

        // Task 505: число → строка с запятой (60 → «60», 43.5 → «43,5»)
        // Task 505: число → строка с запятой (60 → «60», 43.5 → «43,5»)
        _cjFmtNum: function(v) {""",
'4c. методы _cjArchiveCols/_cjArchDate')

# ============================================================
# 5. _saveCjXlsx: модель с архивом
# ============================================================
patch(INDEX,
"""            var wb = null;
            try {
                wb = this._buildCjWorkbook(model);
            } catch (e) { wb = null; }""",
"""            var wb = null;
            try {
                // Task 508: Excel — модель с АРХИВОМ (удалённые записи
                // отображаются, с блоком колонок «Архив»); фолбэк при
                // ошибке — прежняя модель печати
                wb = this._buildCjWorkbook(this._excelModel());
            } catch (e) {
                try { wb = this._buildCjWorkbook(model); } catch (e2) { wb = null; }
            }""",
'5. _saveCjXlsx модель с архивом')

# ============================================================
# 6a. _buildCjWorkbook: шапка метода (self/allCols/xlW)
# ============================================================
patch(INDEX,
"""        _buildCjWorkbook: function(model) {
            var esc = WorkSchedule._wsXlsEsc;
            var colName = WorkSchedule._wsXlsColName;
            var cols = this._cjPrintCols();
            // ширины колонок шаблона (Excel-юниты)
            var xlW = [17, 19.71, 21, 18.71, 17, 16.71,
                       11.43, 17, 16.71, 9.43];""",
"""        _buildCjWorkbook: function(model) {
            var self = this;
            var esc = WorkSchedule._wsXlsEsc;
            var colName = WorkSchedule._wsXlsColName;
            var cols = this._cjPrintCols();
            // Task 508: блок «Архив» — только когда в модели есть
            // архивные строки (Excel показывает удалённые кабели;
            // печать/PDF — нет)
            var archCols = (model.archived && model.archived > 0)
                ? this._cjArchiveCols() : [];
            var allCols = cols.concat(archCols);
            // ширины колонок шаблона (Excel-юниты)
            var xlW = [17, 19.71, 21, 18.71, 17, 16.71,
                       11.43, 17, 16.71, 9.43];
            if (archCols.length) {
                // Task 508: ширины блока «Архив» (K–O)
                xlW = xlW.concat([12, 16, 12, 16.5, 12]);
            }""",
'6a. _buildCjWorkbook шапка')

# ============================================================
# 6b. _buildCjWorkbook: шапка листа — allCols + пары с len
# ============================================================
patch(INDEX,
"""            var r1 = [], r2 = [];
            var i, ci;
            for (i = 0; i < cols.length; i++) {
                if (!cols[i].rowspan) break;
                r1.push(cellXml(1, i + 1, cols[i].label, 1, false));
                r2.push(cellXml(2, i + 1, '', 1, false));
            }
            var pairs = [];
            for (i = 0; i < cols.length; i++) {
                if (cols[i].rowspan) continue;
                if (!pairs.length ||
                        pairs[pairs.length - 1].head !== cols[i].head) {
                    pairs.push({ head: cols[i].head, at: i });
                }
            }
            pairs.forEach(function(p) {
                var c1 = p.at + 1;
                var c2 = Math.min(p.at + 3, cols.length);
                r1.push(cellXml(1, c1, p.head, 1, false));
                for (ci = c1 + 1; ci <= c2; ci++) {
                    r1.push(cellXml(1, ci, '', 1, false));
                }
                for (ci = c1; ci <= c2; ci++) {
                    r2.push(cellXml(2, ci, cols[ci - 1].label,
                                    1, false));
                }
            });""",
"""            var r1 = [], r2 = [];
            var i, ci;
            for (i = 0; i < allCols.length; i++) {
                if (!allCols[i].rowspan) break;
                r1.push(cellXml(1, i + 1, allCols[i].label, 1, false));
                r2.push(cellXml(2, i + 1, '', 1, false));
            }
            var pairs = [];
            for (i = 0; i < allCols.length; i++) {
                if (allCols[i].rowspan) continue;
                if (!pairs.length ||
                        pairs[pairs.length - 1].head !== allCols[i].head) {
                    pairs.push({ head: allCols[i].head, at: i, len: 1 });
                } else {
                    // Task 508: пара может быть длиннее 3 («Архив» — 5)
                    pairs[pairs.length - 1].len++;
                }
            }
            pairs.forEach(function(p) {
                var c1 = p.at + 1;
                var c2 = Math.min(p.at + p.len, allCols.length);
                r1.push(cellXml(1, c1, p.head, 1, false));
                for (ci = c1 + 1; ci <= c2; ci++) {
                    r1.push(cellXml(1, ci, '', 1, false));
                }
                for (ci = c1; ci <= c2; ci++) {
                    r2.push(cellXml(2, ci, allCols[ci - 1].label,
                                    1, false));
                }
            });""",
'6b. _buildCjWorkbook шапка allCols+len')

# ============================================================
# 6c. _buildCjWorkbook: строки данных — allCols + даты архива
# ============================================================
patch(INDEX,
"""                    var cs = [];
                    cols.forEach(function(c, ci) {
                        var raw = rw.src ? rw.src[c.key] : '';
                        var v = '', num = false;
                        if (raw !== null && raw !== undefined) {""",
"""                    var cs = [];
                    allCols.forEach(function(c, ci) {
                        var raw = rw.src ? rw.src[c.key] : '';
                        var v = '', num = false;
                        if (c.key === 'archived_at' ||
                                c.key === 'edited_at') {
                            // Task 508: даты архива — «ДД.ММ.ГГГГ»
                            v = self._cjArchDate(raw);
                        } else if (raw !== null && raw !== undefined) {""",
'6c. _buildCjWorkbook данные allCols')

# ============================================================
# 6d. _buildCjWorkbook: mergeCells динамически
# ============================================================
patch(INDEX,
"""            var colXml = '';
            xlW.forEach(function(w, ci) {
                colXml += '<col min="' + (ci + 1) + '" max="' +
                          (ci + 1) + '" width="' + w +
                          '" customWidth="1"/>';
            });
            var sheet =""",
"""            var colXml = '';
            xlW.forEach(function(w, ci) {
                colXml += '<col min="' + (ci + 1) + '" max="' +
                          (ci + 1) + '" width="' + w +
                          '" customWidth="1"/>';
            });
            // Task 508: объединения шапки — динамически: одиночные
            // (A1:A2…D1:D2) + пары «По проекту»/«Проложен» (+ блок
            // «Архив» K1:O1, когда архивные строки есть)
            var mergesXml = '';
            var merges = [];
            for (i = 0; i < allCols.length; i++) {
                if (allCols[i].rowspan) {
                    var ref = colName(i) + '1:' + colName(i) + '2';
                    merges.push(ref);
                    mergesXml += '<mergeCell ref="' + ref + '"/>';
                }
            }
            pairs.forEach(function(p) {
                var pref = colName(p.at) + '1:' +
                           colName(p.at + p.len - 1) + '1';
                merges.push(pref);
                mergesXml += '<mergeCell ref="' + pref + '"/>';
            });
            var sheet =""",
'6d. _buildCjWorkbook merges подготовка')

patch(INDEX,
"""                '<sheetData>' + rowsXml.join('') + '</sheetData>' +
                '<mergeCells count="6">' +
                '<mergeCell ref="A1:A2"/><mergeCell ref="B1:B2"/>' +
                '<mergeCell ref="C1:C2"/><mergeCell ref="D1:D2"/>' +
                '<mergeCell ref="E1:G1"/><mergeCell ref="H1:J1"/>' +
                '</mergeCells>' +""",
"""                '<sheetData>' + rowsXml.join('') + '</sheetData>' +
                '<mergeCells count="' + merges.length + '">' +
                mergesXml +
                '</mergeCells>' +""",
'6e. _buildCjWorkbook merges XML')

# ============================================================
# 7a. confirmDelete: честный текст
# ============================================================
patch(INDEX,
"""            const msg = 'Удалить кабель «' + designation + '»?\\nЭто действие нельзя отменить.';""",
"""            // Task 508: запись остаётся в архиве журнала (колонки
            // «Архив»/«Кем удалён»/«Дата удаления» листа) — честно
            // предупреждаем, что она сохранится с пометкой «Удалён»
            const msg = 'Удалить кабель «' + designation + '»?\\nЗапись останется в архиве журнала с пометкой «Удалён».';""",
'7a. confirmDelete текст')

# ============================================================
# 7b. submitDelete: тост
# ============================================================
patch(INDEX,
"""                    KipToast.show('Запись удалена');""",
"""                    KipToast.show('Запись удалена — в архиве журнала');""",
'7b. submitDelete тост')

# ============================================================
# 8. sw.js: версия + комментарий
# ============================================================
patch(SW,
"""const CACHE_VERSION = 'kipia-test-v729';""",
"""// Task 508: Кабельный журнал — архив правок/удалений (клиент):
// _archived-строки скрыты из списка/печати/PDF, видны в Excel-экспорте
// (блок «Архив»: статус/кем удалён/когда/последний редактор). Сервер —
// CableJournal.gs Task 508 (деплой Apps Script по инструкции).
const CACHE_VERSION = 'kipia-test-v730';""",
'8. sw.js версия v730')

# ============================================================
# 9. sync-cables.py: архивные строки не попадают в cables.json
# ============================================================
patch(SYNC,
"""        # Пропускаем строки без № п/п и без Обозначения кабеля, провода
        id_val = record.get('№ п/п', '')""",
"""        # Task 508: архивные записи (удалённые кабели, колонка «Архив»
        # непустая) в снимок data/cables.json НЕ попадают — это снимок
        # АКТИВНОГО журнала (счётчик на кнопке входа, офлайн-данные);
        # сами записи остаются в Google-таблице и в Excel-экспорте.
        arch_val = record.get('Архив', '')
        if isinstance(arch_val, str) and arch_val.strip():
            skipped += 1
            continue

        # Пропускаем строки без № п/п и без Обозначения кабеля, провода
        id_val = record.get('№ п/п', '')""",
'9. sync-cables.py скип архива')

print()
if fails:
    print('ПРОВАЛЕНО: %d' % len(fails))
    for f in fails:
        print(' - ' + f)
    sys.exit(1)
print('ВСЕ ПАТЧИ ПРИМЕНЕНЫ')
