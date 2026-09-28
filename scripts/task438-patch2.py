#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 438, этап 2 — НОВЫЕ функции экспорта: PDF (canvas → JPEG →
# мини-писатель PDF, без библиотек) и Excel (писатель XLSX Task 430
# с динамическими стилями и цветными ячейками кодов); модель
# печатной формы _printModel (чистая, VM-тестируемая); диалог
# предпросмотра: «Сохранить PDF» + «Сохранить Excel» вместо HTML.
# Запуск из корня kip8test после task438-patch.py.
import io

path = 'index.html'
src = io.open(path, encoding='utf-8').read()
n0 = src.count('Task 438')

def rep(old, new, cnt=1, label=''):
    global src
    found = src.count(old)
    assert found == cnt, 'FAIL %s: найдено %d, ожидалось %d' % (label, found, cnt)
    src = src.replace(old, new)

# ============================================================
# 1. ВСТАВКА НОВЫХ МЕТОДОВ на место удалённого _savePrintFile
# ============================================================
INSERT_AFTER = """        // Task 438: сохранение HTML-файла графика УДАЛЕНО (заявка:
        // «вместо html — PDF и Excel»); standalone-HTML остаётся
        // внутренним документом предпросмотра (_buildPrintFileHtml,
        // forFile=true больше не используется)

"""

NEW_METHODS = """        // Task 438: сохранение HTML-файла графика УДАЛЕНО (заявка:
        // «вместо html — PDF и Excel»); standalone-HTML остаётся
        // внутренним документом предпросмотра (_buildPrintFileHtml,
        // forFile=true больше не используется)

        // ============================================================
        // Task 438: ЭКСПОРТ ПЕЧАТНОЙ ФОРМЫ В PDF И EXCEL — полностью
        // клиентский, без внешних библиотек (PWA работает офлайн).
        // PDF: модель → раскладка страниц A4-альбом (чистый
        // _printPdfLayout) → отрисовка canvas ×2 (браузер,
        // _printPdfPaintPage) → JPEG → сборка PDF-документа
        // (_buildPdfDocument, DCTDecode passthrough — JPEG из
        // canvas вставляется в PDF как есть). Excel: та же модель →
        // строки листа с цветными ячейками кодов (динамические
        // стили) → писатель XLSX Task 430 (_wsXlsZip/_wsXlsBytes/
        // _wsXlsCrc32). Состав повторяет печатный лист: шапка из
        // двух строк (Task 438), сетка Работник/дни/Дни/Перераб.
        // (без «Часов», переработка — только дни), мероприятия
        // месяца, перечень кодов в СОКРАЩЁННОМ виде
        // ============================================================

        // Task 438: МОДЕЛЬ печатной формы (чистая, без DOM — для
        // VM-тестов). Логика повторяет _buildPrintHtml/_printCell
        // (Tasks 341/360/361/362): дни месяца с выходными/празд-
        // никами/«*» сокращённых; строки печатаемого вида с
        // ЭФФЕКТИВНЫМИ записями (запись + локальная правка,
        // __delete — пустая ячейка); цвет/текст основного кода,
        // пунктирный план отпуска, точка переработки, бейджи
        // мероприятий; построчные итоги «Дни»/«Перераб.» (только
        // дни — Task 438); события месяца (Task 360/362 — записи
        // листа «Инструктажи», пересекающие месяц, в видах
        // «сменный»/«дневной» — только печатаемые строки) и
        // перечень используемых кодов в сокращённом виде
        _printModel: function(viewEmps, agg) {
            var dows = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'];
            var daysInMonth = new Date(this._year, this._month, 0).getDate();
            var days = [];
            for (var d = 1; d <= daysInMonth; d++) {
                var dt = new Date(this._year, this._month - 1, d);
                var dInfo = (typeof ProdCalendar !== 'undefined' &&
                             ProdCalendar.dayInfo)
                    ? ProdCalendar.dayInfo(this._year, this._month, d) : null;
                days.push({
                    d: d, dow: dows[dt.getDay()],
                    off: dInfo ? dInfo.off
                        : (dt.getDay() === 0 || dt.getDay() === 6),
                    feast: dInfo ? !!dInfo.holiday : false,
                    short: dInfo ? !!dInfo.short : false
                });
            }
            // строки: эффективные ячейки + бейджи + итоги
            var entryIdx = this._buildEntryIndex();
            var pend = this._PENDING || {};
            var rows = [];
            var usedCodes = {};
            for (var ri = 0; ri < viewEmps.length; ri++) {
                var emp = viewEmps[ri];
                var cells = [];
                for (var day = 1; day <= daysInMonth; day++) {
                    var ddt = new Date(this._year, this._month - 1, day);
                    var isoDate = this._isoDate(ddt);
                    var key = isoDate + '|' + emp['таб_номер'];
                    var entry = entryIdx[key] || null;
                    var pending = pend[key] || null;
                    var eff = entry;
                    if (pending) {
                        if (pending.__delete) {
                            eff = null;
                        } else {
                            eff = Object.assign({}, entry || {}, pending,
                                                 { 'источник': 'руч' });
                        }
                    }
                    var status = eff ? eff.статус : '';
                    var isDot = (status === '.');
                    var isEvSt = !!status &&
                        this._EVENT_CODES.indexOf(status) !== -1;
                    var meta = (status && !isDot && !isEvSt)
                        ? (this._statusMeta(status) || {}) : {};
                    var evs = (typeof this._eventsAt === 'function')
                        ? (this._eventsAt(isoDate, emp['таб_номер']) || [])
                        : [];
                    if (isEvSt) {
                        var covered = false;
                        for (var ei = 0; ei < evs.length; ei++) {
                            if (evs[ei].code === status) { covered = true; break; }
                        }
                        if (!covered) {
                            evs = evs.concat([{ code: status, training: null }]);
                        }
                    }
                    var badges = [];
                    for (var bi = 0; bi < evs.length; bi++) {
                        var bMeta = this._statusMeta(evs[bi].code) || {};
                        badges.push({ code: evs[bi].code,
                                      color: bMeta.color || '' });
                    }
                    cells.push({
                        status: (!isDot && !isEvSt) ? status : '',
                        color: meta.color || '',
                        overtime: !!(eff && eff.переработка === 1),
                        vac: !status
                            ? !!this._vacationAt(isoDate, emp['таб_номер'])
                            : false,
                        events: badges
                    });
                    if (eff && eff.статус) usedCodes[eff.статус] = true;
                }
                var a = (agg && agg.byTab)
                    ? agg.byTab[String(emp['таб_номер'] || '')] : null;
                rows.push({
                    fio: String(emp['ФИО'] || ''),
                    pos: String(this._posLabel(emp) || ''),
                    tab: String(emp['таб_номер'] || ''),
                    cells: cells,
                    inAgg: !!a,
                    work: a ? a.work : null,
                    overDays: a ? (a.overDays || 0) : null
                });
            }
            var events = this._printEventsData(viewEmps);
            return {
                year: this._year, month: this._month, view: this._view,
                days: days, rows: rows, usedCodes: usedCodes,
                events: events,
                codes: this._printCodesData(usedCodes, events)
            };
        },

        // Task 438: список мероприятий месяца для PDF/Excel — та же
        // выборка, что в печати (Task 360: записи листа
        // «Инструктажи», пересекающие месяц; Task 362: в видах
        // «сменный»/«дневной» — только сотрудники печатаемых строк;
        // Task 416: короткое название из «Список_И_и_ПЗ»)
        _printEventsData: function(viewEmps) {
            var mStart = this._year + '-' + (this._month < 10 ? '0' : '') +
                         this._month + '-01';
            var mEnd = this._year + '-' + (this._month < 10 ? '0' : '') +
                       this._month + '-' +
                       new Date(this._year, this._month, 0).getDate();
            var viewTabs = {};
            for (var vi = 0; vi < viewEmps.length; vi++) {
                viewTabs[viewEmps[vi]['таб_номер']] = true;
            }
            var evByView = (this._view === 'shift' || this._view === 'day');
            var trs = this._TRAININGS || [];
            var evList = [];
            for (var ti = 0; ti < trs.length; ti++) {
                var tr = trs[ti];
                var trS = tr['дата_начала'];
                if (!trS) continue;
                var trE = tr['дата_окончания'] || trS;
                if (trE < mStart || trS > mEnd) continue;
                if (evByView && !viewTabs[tr['таб_номер']]) continue;
                evList.push(tr);
            }
            evList.sort(function(a, b) {
                return String(a['дата_начала'])
                    .localeCompare(String(b['дата_начала'])) ||
                       String(a['таб_номер'])
                    .localeCompare(String(b['таб_номер']));
            });
            var fioIdx = {};
            var evEmps = this._EMPLOYEES || [];
            for (var fi = 0; fi < evEmps.length; fi++) {
                fioIdx[evEmps[fi]['таб_номер']] = evEmps[fi]['ФИО'];
            }
            var out = [];
            for (var ki = 0; ki < evList.length; ki++) {
                var ev = evList[ki];
                var code = (typeof this._trainingCodeOf === 'function')
                    ? this._trainingCodeOf(ev['тип']) : '';
                var meta = code ? (this._statusMeta(code) || {}) : {};
                var fio = fioIdx[ev['таб_номер']] ||
                          ('таб. №' + ev['таб_номер']);
                var evS = String(ev['дата_начала']);
                var evE = String(ev['дата_окончания'] || ev['дата_начала']);
                var range;
                if (evS === evE) {
                    range = evS.slice(8) + '.' + evS.slice(5, 7);
                } else if (evS.slice(0, 7) === evE.slice(0, 7)) {
                    range = evS.slice(8) + '–' + evE.slice(8) + '.' +
                            evE.slice(5, 7);
                } else {
                    range = evS.slice(8) + '.' + evS.slice(5, 7) + '–' +
                            evE.slice(8) + '.' + evE.slice(5, 7);
                }
                var text = (code ? code + ' · ' : '') +
                    (this._instrShortOf(ev['тема']) || meta.name || '—') +
                    ' · ' + fio;
                out.push({ range: range, text: text, code: code,
                           color: meta.color || '' });
            }
            return out;
        },

        // Task 438: перечень кодов месяца для PDF/Excel — порядок
        // справочника _STATUS_CODES (как в печати), «.» — слот
        // «Выходной», обозначение — СОКРАЩЁННОЕ (short, Task 388;
        // у кодов вне канона short нет — фолбэк name); легаси-коды
        // месяца вне справочника — в конец без цвета (только код).
        // Коды мероприятий (Task 362) тоже попадают в перечень
        _printCodesData: function(usedCodes, events) {
            var used = {};
            for (var k in usedCodes) {
                if (Object.prototype.hasOwnProperty.call(usedCodes, k)) {
                    used[k] = true;
                }
            }
            for (var i = 0; i < (events || []).length; i++) {
                if (events[i].code) used[events[i].code] = true;
            }
            var codes = this._STATUS_CODES || [];
            var out = [];
            for (var ci = 0; ci < codes.length; ci++) {
                if (!used[codes[ci].code] &&
                    !(codes[ci].code === '' && used['.'])) continue;
                out.push({ code: codes[ci].code,
                           label: codes[ci].short || codes[ci].name || '',
                           color: codes[ci].color || '' });
            }
            var legacy = [];
            for (var lk in used) {
                if (!Object.prototype.hasOwnProperty.call(used, lk)) continue;
                var known = false;
                for (var cj = 0; cj < codes.length; cj++) {
                    if (codes[cj].code === lk) { known = true; break; }
                }
                if (!known) legacy.push(lk);
            }
            legacy.sort();
            for (var li = 0; li < legacy.length; li++) {
                out.push({ code: legacy[li], label: '', color: '' });
            }
            return out;
        },

        // Task 438: РАСКЛАДКА СТРАНИЦ PDF (чистая, без DOM —
        // VM-тесты). A4 альбомная 842×595 pt, поля 8 мм ≈ 23 pt.
        // Страницы: [шапка (только первая) +] лента дней + строки
        // сотрудников (граница — только по строкам, лента
        // повторяется на каждой странице с таблицей); мероприятия
        // и коды — на последней странице под таблицей, если
        // влезают, иначе отдельными страницами (события режутся
        // по высоте, коды — всегда одной страницей)
        _printPdfLayout: function(model, opts) {
            opts = opts || {};
            var W = opts.W || 842, H = opts.H || 595, M = opts.M || 23;
            var headH = opts.headH || 34;
            var dayHeadH = opts.dayHeadH || 24;
            var rowH = opts.rowH || 22;
            var secH = opts.secH || 18;
            var evRowH = opts.evRowH || 13;
            var codeRowH = opts.codeRowH || 14;
            var gapH = opts.gapH || 8;
            var contentH = H - 2 * M;
            var evList = (model.events || []).length
                ? model.events : [{ placeholder: true }];
            var codeRows = Math.max(1,
                Math.ceil((model.codes || []).length / 2));
            var evH = secH + evList.length * evRowH + gapH;
            var cdH = secH + codeRows * codeRowH;

            var pages = [];
            var rows = model.rows || [];
            var i = 0;
            while (i < rows.length) {
                var first = (pages.length === 0);
                var avail = contentH - (first ? headH + gapH : 0) - dayHeadH;
                var n = Math.max(1, Math.floor(avail / rowH));
                var chunk = rows.slice(i, i + n);
                i += chunk.length;
                var used = dayHeadH + chunk.length * rowH + gapH;
                if (i >= rows.length && used + evH + cdH <= contentH) {
                    // последняя страница таблицы: мероприятия и коды
                    // помещаются под ней
                    pages.push({ first: first, rows: chunk,
                                 events: model.events || [],
                                 codes: model.codes || [] });
                    return { pages: pages, W: W, H: H, M: M, headH: headH,
                             dayHeadH: dayHeadH, rowH: rowH, secH: secH,
                             evRowH: evRowH, codeRowH: codeRowH, gapH: gapH };
                }
                pages.push({ first: first, rows: chunk,
                             events: null, codes: null });
            }
            // мероприятия (+ коды, если влезут) — отдельными
            // страницами; пустой месяц — строка-заглушка (как в
            // печати: «нет мероприятий в этом месяце»)
            var evCap = Math.max(1,
                Math.floor((contentH - secH) / evRowH));
            var ei = 0;
            var codesPlaced = false;
            while (ei < evList.length) {
                var take = Math.min(evCap, evList.length - ei);
                var evChunk = evList.slice(ei, ei + take);
                ei += take;
                var withCodes = (ei >= evList.length) &&
                                (secH + take * evRowH + gapH + cdH <= contentH);
                if (withCodes) codesPlaced = true;
                pages.push({ first: false, rows: [], events: evChunk,
                             codes: withCodes ? (model.codes || []) : null });
            }
            if (!codesPlaced) {
                pages.push({ first: false, rows: [], events: null,
                             codes: model.codes || [] });
            }
            return { pages: pages, W: W, H: H, M: M, headH: headH,
                     dayHeadH: dayHeadH, rowH: rowH, secH: secH,
                     evRowH: evRowH, codeRowH: codeRowH, gapH: gapH };
        },

        // Task 438: СБОРКА PDF-ДОКУМЕНТА (чистая, VM-тесты).
        // jpegs: [{bytes: Uint8Array (JPEG), w: px, h: px}] — по
        // одному на страницу; каждая страница — растровый XObject
        // (DCTDecode: JPEG из canvas.toDataURL вставляется как
        // есть, без перекодирования). Структура: 1 Catalog,
        // 2 Pages, далее на страницу — Page / Image / Contents
        // (номера 3+3i / 4+3i / 5+3i), xref + trailer. Смещения —
        // в БАЙТАХ (бинарные вставки JPEG учтены)
        _buildPdfDocument: function(jpegs, W, H) {
            W = Math.round(W || 842);
            H = Math.round(H || 595);
            var parts = [];
            var offset = 0;
            var offs = [];
            var self = this;
            var push = function(s) {
                var b = self._wsXlsBytes(s);
                parts.push(b);
                offset += b.length;
            };
            var pushBin = function(b) {
                parts.push(b);
                offset += b.length;
            };
            var n = (jpegs || []).length;
            var kids = [];
            for (var k = 0; k < n; k++) kids.push((3 + 3 * k) + ' 0 R');
            push('%PDF-1.4\\n');
            offs[1] = offset;
            push('1 0 obj\\n<< /Type /Catalog /Pages 2 0 R >>\\nendobj\\n');
            offs[2] = offset;
            push('2 0 obj\\n<< /Type /Pages /Kids [' + kids.join(' ') +
                 '] /Count ' + n + ' >>\\nendobj\\n');
            for (var p = 0; p < n; p++) {
                var pg = 3 + 3 * p, im = 4 + 3 * p, cn = 5 + 3 * p;
                var jp = jpegs[p];
                offs[pg] = offset;
                push(pg + ' 0 obj\\n<< /Type /Page /Parent 2 0 R ' +
                     '/MediaBox [0 0 ' + W + ' ' + H + '] ' +
                     '/Resources << /ProcSet [/PDF /ImageC] ' +
                     '/XObject << /Im' + p + ' ' + im + ' 0 R >> >> ' +
                     '/Contents ' + cn + ' 0 R >>\\nendobj\\n');
                offs[im] = offset;
                push(im + ' 0 obj\\n<< /Type /XObject /Subtype /Image ' +
                     '/Width ' + jp.w + ' /Height ' + jp.h +
                     ' /ColorSpace /DeviceRGB /BitsPerComponent 8 ' +
                     '/Filter /DCTDecode /Length ' + jp.bytes.length +
                     ' >>\\nstream\\n');
                pushBin(jp.bytes);
                push('\\nendstream\\nendobj\\n');
                var cont = 'q\\n' + W + ' 0 0 ' + H + ' 0 0 cm\\n/Im' +
                           p + ' Do\\nQ\\n';
                offs[cn] = offset;
                push(cn + ' 0 obj\\n<< /Length ' + cont.length +
                     ' >>\\nstream\\n' + cont + 'endstream\\nendobj\\n');
            }
            var total = 3 + 3 * n;
            var xrefPos = offset;
            var xref = 'xref\\n0 ' + total + '\\n0000000000 65535 f \\n';
            for (var o = 1; o < total; o++) {
                xref += ('0000000000' + (offs[o] || 0)).slice(-10) +
                        ' 00000 n \\n';
            }
            push(xref);
            push('trailer\\n<< /Size ' + total + ' /Root 1 0 R ' +
                 '>>\\nstartxref\\n' + xrefPos + '\\n%%EOF');
            var out = new Uint8Array(offset);
            var pos = 0;
            for (var q = 0; q < parts.length; q++) {
                out.set(parts[q], pos);
                pos += parts[q].length;
            }
            return out;
        },

        // Task 438: data-URL (JPEG из canvas) → байты; вне браузера
        // (нет atob) — пустой массив (страница пропускается)
        _wsDataUrlBytes: function(u) {
            var b64 = String(u || '').split(',')[1] || '';
            if (!b64 || typeof atob !== 'function') {
                return new Uint8Array(0);
            }
            var bin = atob(b64);
            var out = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) {
                out[i] = bin.charCodeAt(i) & 0xff;
            }
            return out;
        },

        // Task 438: ОТРИСОВКА СТРАНИЦЫ PDF на canvas (браузер; в
        // VM-тестах не вызывается — раскладку строит чистый
        // _printPdfLayout). Координаты — pt (842×595), canvas ×2
        // для чёткости текста; итог — JPEG {bytes, w, h} или null
        _printPdfPaintPage: function(lay, model, pi) {
            if (typeof document === 'undefined' ||
                !document.createElement) return null;
            var page = lay.pages[pi];
            if (!page) return null;
            var cnv = document.createElement('canvas');
            if (!cnv || !cnv.getContext) return null;
            var scale = 2;
            cnv.width = lay.W * scale;
            cnv.height = lay.H * scale;
            var ctx = cnv.getContext('2d');
            if (!ctx || !ctx.fillText) return null;
            try { ctx.scale(scale, scale); } catch (e) { return null; }
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, lay.W, lay.H);

            var M = lay.M;
            var CW = lay.W - 2 * M;
            var x0 = M;
            var y = M;
            var monthsNom = ['январь','февраль','март','апрель','май',
                             'июнь','июль','август','сентябрь','октябрь',
                             'ноябрь','декабрь'];
            var viewLabels = { full: 'полный', shift: 'сменный',
                               day: 'дневной' };
            var nDays = model.days.length;
            var totW1 = 26, totW2 = 38;

            // ширина колонки работника — по самому длинному ФИО
            var empW = 96;
            try {
                var maxW = 0;
                ctx.font = '700 9px Arial';
                for (var wi = 0; wi < model.rows.length; wi++) {
                    maxW = Math.max(maxW,
                        ctx.measureText(model.rows[wi].fio || '').width);
                }
                empW = Math.max(70, Math.min(150, maxW + 10));
            } catch (e2) { empW = 96; }
            var dayW = (CW - empW - totW1 - totW2) / nDays;

            // шапка листа — только на первой странице
            if (page.first) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 16px Arial';
                ctx.fillText('ГРАФИК РАБОТЫ', x0, y + 14);
                ctx.fillStyle = '#3c4650';
                ctx.font = '600 10.5px Arial';
                ctx.fillText(monthsNom[model.month - 1] + ' ' + model.year +
                             ' г. · вид табеля: ' +
                             (viewLabels[model.view] || 'полный'),
                             x0, y + 29);
                y += lay.headH + lay.gapH;
            }

            var gridLine = function(x, yy, w, h) {
                ctx.strokeStyle = '#c9d1d9';
                ctx.lineWidth = 0.5;
                ctx.strokeRect(x, yy, w, h);
            };

            // лента дней (повторяется на каждой странице таблицы)
            var drawDayHead = function(yTop) {
                ctx.fillStyle = '#eef1f4';
                ctx.fillRect(x0, yTop, empW, lay.dayHeadH);
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 8px Arial';
                ctx.fillText('Работник', x0 + 3, yTop + 14);
                for (var dd = 0; dd < nDays; dd++) {
                    var day = model.days[dd];
                    var dx = x0 + empW + dd * dayW;
                    if (day.off) {
                        ctx.fillStyle = '#dfe5e9';
                        ctx.fillRect(dx, yTop, dayW, lay.dayHeadH);
                    }
                    ctx.textAlign = 'center';
                    ctx.fillStyle = day.feast ? '#b02a2a' : '#1b1f24';
                    ctx.font = '700 7px Arial';
                    ctx.fillText(String(day.d) + (day.short ? '*' : ''),
                                 dx + dayW / 2, yTop + 9);
                    ctx.fillStyle = '#54606a';
                    ctx.font = '5.5px Arial';
                    ctx.fillText(day.dow, dx + dayW / 2, yTop + 17);
                    ctx.textAlign = 'left';
                    gridLine(dx, yTop, dayW, lay.dayHeadH);
                }
                var tx1 = x0 + empW + nDays * dayW;
                ctx.fillStyle = '#eef1f4';
                ctx.fillRect(tx1, yTop, totW1, lay.dayHeadH);
                ctx.fillRect(tx1 + totW1, yTop, totW2, lay.dayHeadH);
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 8px Arial';
                ctx.fillText('Дни', tx1 + 6, yTop + 14);
                ctx.fillText('Перераб.', tx1 + totW1 + 4, yTop + 9);
                ctx.fillStyle = '#54606a';
                ctx.font = '5.5px Arial';
                ctx.fillText('дни', tx1 + totW1 + 4, yTop + 17);
                gridLine(x0, yTop, empW, lay.dayHeadH);
                gridLine(tx1, yTop, totW1, lay.dayHeadH);
                gridLine(tx1 + totW1, yTop, totW2, lay.dayHeadH);
            };

            // строки сотрудников
            if (page.rows.length) {
                drawDayHead(y);
                y += lay.dayHeadH;
                for (var rr = 0; rr < page.rows.length; rr++) {
                    var row = page.rows[rr];
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '700 8px Arial';
                    ctx.fillText(row.fio, x0 + 3, y + 10);
                    if (row.pos) {
                        ctx.fillStyle = '#54606a';
                        ctx.font = '6.5px Arial';
                        ctx.fillText(row.pos, x0 + 3, y + 18);
                    }
                    for (var cc = 0; cc < row.cells.length; cc++) {
                        var cell = row.cells[cc];
                        var dx = x0 + empW + cc * dayW;
                        var dyy = model.days[cc];
                        if (cell.status && cell.color) {
                            ctx.fillStyle = cell.color;
                            ctx.fillRect(dx, y, dayW, lay.rowH);
                        } else if (!cell.status && !cell.vac && dyy.off) {
                            ctx.fillStyle = '#e2e8ec';
                            ctx.fillRect(dx, y, dayW, lay.rowH);
                        }
                        if (cell.vac) {
                            ctx.strokeStyle = '#8aa4b8';
                            ctx.lineWidth = 0.8;
                            try {
                                ctx.setLineDash([2, 1.6]);
                                ctx.strokeRect(dx + 1, y + 1,
                                               dayW - 2, lay.rowH - 2);
                                ctx.setLineDash([]);
                            } catch (e3) {
                                ctx.strokeRect(dx + 1, y + 1,
                                               dayW - 2, lay.rowH - 2);
                            }
                        }
                        if (cell.status) {
                            ctx.fillStyle = '#1b1f24';
                            ctx.font = '700 6.5px Arial';
                            ctx.textAlign = 'center';
                            ctx.fillText(cell.status, dx + dayW / 2,
                                         y + lay.rowH / 2 + 2);
                            ctx.textAlign = 'left';
                        }
                        if (cell.overtime) {
                            ctx.fillStyle = '#d32f2f';
                            ctx.beginPath();
                            ctx.arc(dx + dayW - 2.5, y + 3.2, 1.4,
                                    0, Math.PI * 2);
                            ctx.fill();
                        }
                        // бейджи мероприятий — правый нижний угол
                        for (var bb = 0; bb < cell.events.length && bb < 3; bb++) {
                            var bw = 3.4;
                            var bx = dx + dayW - 2 - bw -
                                     bb * (bw + 0.8);
                            ctx.fillStyle = cell.events[bb].color ||
                                            '#3a3a3a';
                            ctx.fillRect(bx, y + lay.rowH - 2 - bw,
                                         bw, bw);
                        }
                        gridLine(dx, y, dayW, lay.rowH);
                    }
                    var tx = x0 + empW + nDays * dayW;
                    gridLine(x0, y, empW, lay.rowH);
                    gridLine(tx, y, totW1, lay.rowH);
                    gridLine(tx + totW1, y, totW2, lay.rowH);
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '700 8px Arial';
                    if (row.inAgg) {
                        ctx.fillText(String(row.work), tx + 6, y + 14);
                        ctx.fillText(row.overDays
                                     ? String(row.overDays) : '—',
                                     tx + totW1 + 6, y + 14);
                    }
                    y += lay.rowH;
                }
                y += lay.gapH;
            }

            // мероприятия (заголовок — как в печати: счётчик месяца)
            if (page.events) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Мероприятия · ' +
                             monthsNom[model.month - 1] + ' ' + model.year +
                             (model.events.length
                                 ? ' · ' + model.events.length : ''),
                             x0, y + 8);
                y += lay.secH;
                var evs = page.events.length ? page.events
                    : [{ range: '', color: '',
                         text: 'нет мероприятий в этом месяце' }];
                for (var ee = 0; ee < evs.length; ee++) {
                    var ex = x0;
                    if (evs[ee].color) {
                        ctx.fillStyle = evs[ee].color;
                        ctx.beginPath();
                        ctx.arc(ex + 2.4, y + 4, 2.2, 0, Math.PI * 2);
                        ctx.fill();
                    }
                    ex += 7;
                    if (evs[ee].range) {
                        ctx.fillStyle = '#1b1f24';
                        ctx.font = '700 8px Arial';
                        ctx.fillText(evs[ee].range, ex, y + 7);
                        ex += ctx.measureText(evs[ee].range).width + 6;
                    }
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '8px Arial';
                    ctx.fillText(evs[ee].text, ex, y + 7);
                    y += lay.evRowH;
                }
                y += lay.gapH;
            }

            // коды — две колонки (как в печати, Task 434)
            if (page.codes) {
                ctx.fillStyle = '#1b1f24';
                ctx.font = '700 9px Arial';
                ctx.fillText('Коды:', x0, y + 8);
                y += lay.secH;
                var colW2 = CW / 2;
                var perCol = Math.max(1,
                    Math.ceil(page.codes.length / 2));
                for (var lc = 0; lc < page.codes.length; lc++) {
                    var lx = x0 + (lc < perCol ? 0 : colW2);
                    var ly = y + (lc % perCol) * lay.codeRowH;
                    var code = page.codes[lc];
                    if (code.color) {
                        ctx.fillStyle = code.color;
                        ctx.fillRect(lx, ly + 1, 4.5, 4.5);
                    }
                    ctx.fillStyle = '#1b1f24';
                    ctx.font = '8px Arial';
                    ctx.fillText(code.code
                        ? (code.label
                           ? code.code + ' — ' + code.label : code.code)
                        : (code.label || ''),
                        lx + 7, ly + 5.5);
                }
            }

            var dataUrl;
            try {
                dataUrl = cnv.toDataURL('image/jpeg', 0.92);
            } catch (e4) { return null; }
            var bytes = this._wsDataUrlBytes(dataUrl);
            if (!bytes.length) return null;
            return { bytes: bytes, w: cnv.width, h: cnv.height };
        },

        // Task 438: «Сохранить PDF» диалога предпросмотра — модель
        // → раскладка → отрисовка страниц → PDF в загрузки; имя —
        // «График_работы_‹Месяц›_‹год›.pdf»
        _savePrintPdf: function(viewEmps, agg) {
            var months = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                          'Июль','Август','Сентябрь','Октябрь','Ноябрь',
                          'Декабрь'];
            var mIdx = Math.min(Math.max(parseInt(this._month, 10) || 1, 1), 12);
            var name = 'График_работы_' + months[mIdx - 1] + '_' +
                       this._year + '.pdf';
            var ok = false;
            try {
                var model = this._printModel(viewEmps, agg);
                var lay = this._printPdfLayout(model);
                var jpegs = [];
                for (var p = 0; p < lay.pages.length; p++) {
                    var jp = this._printPdfPaintPage(lay, model, p);
                    if (jp) jpegs.push(jp);
                }
                if (!jpegs.length) throw new Error('нет страниц');
                var bytes = this._buildPdfDocument(jpegs, lay.W, lay.H);
                ok = this._wsDownload(bytes, 'application/pdf', name);
            } catch (e) { ok = false; }
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show(ok
                    ? ('График сохранён — файл «' + name + '»')
                    : 'Не удалось сохранить PDF графика');
            }
        },

        // Task 438: ДИНАМИЧЕСКИЕ стили листа табеля Excel:
        // 0 — обычный, 1 — шапка (жирный белый на синем),
        // 2 — заголовок листа (жирный 14), 3 — подстрока шапки
        // (серый), 4 — ячейка сетки (рамка), 5 — ячейка сетки
        // жирная (ФИО/итоги), 6 — день недели (серый 9, центр,
        // рамка), 7+k — заливка цвета кода k + рамка + центр
        _wsTabelStylesXml: function(colors) {
            colors = colors || [];
            var f = '', fl = '', xf = '';
            f += '<font><sz val="11"/><color rgb="FF1B1F24"/><name val="Arial"/></font>';
            f += '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>';
            f += '<font><b/><sz val="14"/><color rgb="FF1B1F24"/><name val="Arial"/></font>';
            f += '<font><sz val="11"/><color rgb="FF5C6670"/><name val="Arial"/></font>';
            f += '<font><sz val="9"/><color rgb="FF5C6670"/><name val="Arial"/></font>';
            f += '<font><b/><sz val="11"/><color rgb="FF1B1F24"/><name val="Arial"/></font>';
            fl += '<fill><patternFill patternType="none"/></fill>';
            fl += '<fill><patternFill patternType="gray125"/></fill>';
            fl += '<fill><patternFill patternType="solid">' +
                  '<fgColor rgb="FF4472C4"/><bgColor indexed="64"/>' +
                  '</patternFill></fill>';
            for (var i = 0; i < colors.length; i++) {
                fl += '<fill><patternFill patternType="solid">' +
                      '<fgColor rgb="FF' + colors[i] + '"/>' +
                      '<bgColor indexed="64"/></patternFill></fill>';
            }
            xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>';
            xf += '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>';
            xf += '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>';
            xf += '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>';
            xf += '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>';
            xf += '<xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>';
            xf += '<xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1">' +
                  '<alignment horizontal="center"/></xf>';
            for (var k = 0; k < colors.length; k++) {
                xf += '<xf numFmtId="0" fontId="0" fillId="' + (3 + k) +
                      '" borderId="1" xfId="0" applyFill="1" ' +
                      'applyBorder="1" applyAlignment="1">' +
                      '<alignment horizontal="center"/></xf>';
            }
            return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
                '<fonts count="' + 6 + '">' + f + '</fonts>' +
                '<fills count="' + (3 + colors.length) + '">' + fl + '</fills>' +
                '<borders count="2">' +
                '<border><left/><right/><top/><bottom/><diagonal/></border>' +
                '<border>' +
                '<left style="thin"><color rgb="FFB9C2CC"/></left>' +
                '<right style="thin"><color rgb="FFB9C2CC"/></right>' +
                '<top style="thin"><color rgb="FFB9C2CC"/></top>' +
                '<bottom style="thin"><color rgb="FFB9C2CC"/></bottom>' +
                '<diagonal/></border></borders>' +
                '<cellStyleXfs count="1">' +
                '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>' +
                '</cellStyleXfs>' +
                '<cellXfs count="' + (7 + colors.length) + '">' + xf +
                '</cellXfs>' +
                '<cellStyles count="1">' +
                '<cellStyle name="Normal" xfId="0" builtinId="0"/>' +
                '</cellStyles></styleSheet>';
        },

        // Task 438: строки листа «Табель» для Excel (чистая, для
        // VM-тестов): шапка из двух строк (Task 438), сетка
        // Работник/дни/Дни/Перераб. (без «Часов», переработка —
        // только дни), цветные ячейки кодов, мероприятия месяца и
        // коды в сокращённом виде (по два в ряд)
        _wsTabelRows: function(model, colorIdx) {
            var viewLabels = { full: 'полный', shift: 'сменный',
                               day: 'дневной' };
            var monthsNom = ['январь','февраль','март','апрель','май',
                             'июнь','июль','август','сентябрь','октябрь',
                             'ноябрь','декабрь'];
            var rows = [];
            rows.push([{ v: 'График работы', s: 2 }]);
            rows.push([{ v: monthsNom[model.month - 1] + ' ' + model.year +
                         ' г. · вид табеля: ' +
                         (viewLabels[model.view] || 'полный'), s: 3 }]);
            rows.push([]);
            var head = [{ v: 'Работник', s: 1 }];
            var dows = [{ v: '', s: 6 }];
            for (var d = 0; d < model.days.length; d++) {
                head.push({ v: String(model.days[d].d) +
                            (model.days[d].short ? '*' : ''), s: 1 });
                dows.push({ v: model.days[d].dow, s: 6 });
            }
            head.push({ v: 'Дни', s: 1 });
            head.push({ v: 'Перераб.', s: 1 });
            dows.push({ v: '', s: 6 });
            dows.push({ v: '', s: 6 });
            rows.push(head);
            rows.push(dows);
            for (var r = 0; r < model.rows.length; r++) {
                var row = model.rows[r];
                var line = [{ v: row.fio, s: 5 }];
                for (var c = 0; c < row.cells.length; c++) {
                    var cell = row.cells[c];
                    var st = 4;
                    if (cell.status && cell.color) {
                        var col = String(cell.color).replace('#', '')
                                    .toUpperCase();
                        if (colorIdx[col] !== undefined) {
                            st = 7 + colorIdx[col];
                        }
                    }
                    line.push({ v: cell.status || '', s: st });
                }
                line.push({ v: row.inAgg ? row.work : '', s: 5 });
                line.push({ v: row.inAgg
                            ? (row.overDays ? row.overDays : '—') : '',
                            s: 5 });
                rows.push(line);
            }
            rows.push([]);
            rows.push([{ v: 'Мероприятия · ' +
                         monthsNom[model.month - 1] + ' ' + model.year +
                         (model.events.length
                             ? ' · ' + model.events.length : ''), s: 1 }]);
            if (model.events.length) {
                for (var e = 0; e < model.events.length; e++) {
                    rows.push([{ v: model.events[e].range, s: 5 },
                               { v: model.events[e].text, s: 0 }]);
                }
            } else {
                rows.push([{ v: 'нет мероприятий в этом месяце', s: 0 }]);
            }
            rows.push([]);
            rows.push([{ v: 'Коды:', s: 1 }]);
            for (var k = 0; k < model.codes.length; k += 2) {
                var pair = [];
                for (var kk = k; kk < k + 2 && kk < model.codes.length; kk++) {
                    var cd = model.codes[kk];
                    pair.push({ v: cd.code
                        ? (cd.label ? cd.code + ' — ' + cd.label : cd.code)
                        : (cd.label || ''), s: 0 });
                }
                rows.push(pair);
            }
            return rows;
        },

        // Task 438: XML листа «Табель»: ячейки — {v, s} (v —
        // строка/число, s — индекс стиля из _wsTabelStylesXml);
        // ПУСТЫЕ ячейки сетки тоже пишутся (с рамкой — сетка
        // видна), закрепление: столбец A + строки шапки/дней
        _wsTabelSheetXml: function(rows, opts) {
            opts = opts || {};
            var maxCol = 1;
            for (var i = 0; i < (rows || []).length; i++) {
                if (rows[i].length > maxCol) maxCol = rows[i].length;
            }
            var x = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
                '<dimension ref="A1:' + this._wsXlsColName(maxCol - 1) +
                Math.max(rows ? rows.length : 0, 1) + '"/>' +
                '<sheetViews><sheetView workbookViewId="0"' +
                (opts.active ? ' tabSelected="1"' : '') + '>' +
                '<pane xSplit="1" ySplit="' + (opts.freezeY || 5) +
                '" topLeftCell="B' + ((opts.freezeY || 5) + 1) +
                '" activePane="bottomRight" state="frozen"/>' +
                '</sheetView></sheetViews>';
            if (opts.widths && opts.widths.length) {
                x += '<cols>';
                for (var w = 0; w < opts.widths.length; w++) {
                    x += '<col min="' + (w + 1) + '" max="' + (w + 1) +
                         '" width="' + opts.widths[w] + '" customWidth="1"/>';
                }
                x += '</cols>';
            }
            x += '<sheetData>';
            for (var r = 0; r < (rows || []).length; r++) {
                var row = rows[r];
                if (!row.length) {
                    x += '<row r="' + (r + 1) + '"/>';
                    continue;
                }
                x += '<row r="' + (r + 1) + '">';
                for (var c = 0; c < row.length; c++) {
                    var cell = row[c] || {};
                    var ref = this._wsXlsColName(c) + (r + 1);
                    var st = (cell.s === undefined || cell.s === null)
                        ? '' : ' s="' + cell.s + '"';
                    var v = cell.v;
                    if (v === null || v === undefined) v = '';
                    if (typeof v === 'number' && isFinite(v)) {
                        x += '<c r="' + ref + '"' + st + '><v>' + v +
                             '</v></c>';
                    } else if (String(v) === '') {
                        x += '<c r="' + ref + '"' + st + '/>';
                    } else {
                        x += '<c r="' + ref + '" t="inlineStr"' + st +
                             '><is><t>' + this._wsXlsEsc(String(v)) +
                             '</t></is></c>';
                    }
                }
                x += '</row>';
            }
            x += '</sheetData></worksheet>';
            return x;
        },

        // Task 438: КНИГА .xlsx «Табель» (чистая — те же помощники
        // Task 430: _wsXlsZip/_wsXlsBytes; имя — «График_работы_
        // ‹Месяц›_‹год›.xlsx»); цвета кодов → динамические стили
        _buildTabelWorkbook: function(viewEmps, agg) {
            var model = this._printModel(viewEmps, agg);
            var colors = [];
            var colorIdx = {};
            for (var c = 0; c < model.codes.length; c++) {
                var col = String(model.codes[c].color || '')
                    .replace('#', '').toUpperCase();
                if (!col || colorIdx[col] !== undefined) continue;
                colorIdx[col] = colors.length;
                colors.push(col);
            }
            // ячейки сетки могут нести цвет кода, которого нет в
            // легенде (легаси без цвета — пустой, не бывает), но на
            // всякий случай индексируем и их
            for (var r = 0; r < model.rows.length; r++) {
                var cells = model.rows[r].cells;
                for (var k = 0; k < cells.length; k++) {
                    var cc = String(cells[k].color || '')
                        .replace('#', '').toUpperCase();
                    if (!cc || colorIdx[cc] !== undefined) continue;
                    colorIdx[cc] = colors.length;
                    colors.push(cc);
                }
            }
            var rows = this._wsTabelRows(model, colorIdx);
            var widths = [30];
            for (var d = 0; d < model.days.length; d++) widths.push(3.8);
            widths.push(6, 9.5);
            var files = [];
            var ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
                '<Default Extension="xml" ContentType="application/xml"/>' +
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
                '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' +
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
                '</Types>';
            files.push({ name: '[Content_Types].xml',
                         data: this._wsXlsBytes(ct) });
            files.push({
                name: '_rels/.rels',
                data: this._wsXlsBytes(
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"' +
                    ' Target="xl/workbook.xml"/></Relationships>')
            });
            files.push({
                name: 'xl/workbook.xml',
                data: this._wsXlsBytes(
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"' +
                    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
                    '<sheets><sheet name="Табель" sheetId="1" r:id="rId1"/>' +
                    '</sheets></workbook>')
            });
            files.push({
                name: 'xl/_rels/workbook.xml.rels',
                data: this._wsXlsBytes(
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"' +
                    ' Target="worksheets/sheet1.xml"/>' +
                    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"' +
                    ' Target="styles.xml"/></Relationships>')
            });
            files.push({
                name: 'xl/worksheets/sheet1.xml',
                data: this._wsXlsBytes(this._wsTabelSheetXml(rows, {
                    widths: widths, freezeY: 5, active: true }))
            });
            files.push({ name: 'xl/styles.xml',
                         data: this._wsXlsBytes(this._wsTabelStylesXml(colors)) });
            var months = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                          'Июль','Август','Сентябрь','Октябрь','Ноябрь',
                          'Декабрь'];
            var mIdx = Math.min(Math.max(parseInt(this._month, 10) || 1, 1), 12);
            return {
                name: 'График_работы_' + months[mIdx - 1] + '_' +
                      this._year + '.xlsx',
                bytes: this._wsXlsZip(files),
                counts: {
                    rows: model.rows.length,
                    events: model.events.length,
                    codes: model.codes.length,
                    colors: colors.length
                }
            };
        },

        // Task 438: «Сохранить Excel» диалога предпросмотра — книга
        // «Табель» (.xlsx) в загрузки браузера
        _savePrintXlsx: function(viewEmps, agg) {
            var wb = null;
            try {
                wb = this._buildTabelWorkbook(viewEmps, agg);
            } catch (e) { wb = null; }
            var ok = wb
                ? this._wsDownload(
                      wb.bytes,
                      'application/vnd.openxmlformats-officedocument.' +
                      'spreadsheetml.sheet', wb.name)
                : false;
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show(ok
                    ? ('График сохранён — файл «' + wb.name + '»')
                    : 'Не удалось сохранить Excel графика');
            }
        },

"""

rep(INSERT_AFTER, NEW_METHODS, 1, 'вставка новых методов')

# ============================================================
# 2. ДИАЛОГ: подпись «Сохранить в файл» → PDF/Excel
# ============================================================
rep("""        // масштаб под окно; низ — «Печать» (window.print() ОСНОВНОГО
        // документа: @media print скрывает всё кроме #wsPrintSheet —
        // диалог тоже, поэтому его можно не закрывать), «Сохранить
        // в файл» (standalone-HTML в загрузки), «Отмена». Esc и
        // клик по затемнению закрывают. Возвращает true при успехе;
        // false — без DOM (фолбэк printGrid: печать сразу)
        _openPrintPreview: function(printHtml) {""",
"""        // (как в экранной сетке, Task 314); кнопки — «Печать»
        // (window.print() ОСНОВНОГО документа: @media print
        // скрывает всё кроме #wsPrintSheet — диалог тоже, поэтому
        // его можно не закрывать), «Сохранить PDF» и
        // «Сохранить Excel» (Task 438: клиентские генераторы вместо
        // standalone-HTML), «Отмена». Esc и клик по затемнению
        // закрывают. Возвращает true при успехе; false — без DOM
        // (фолбэк printGrid: печать сразу). ctx (Task 438) —
        // {viewEmps, agg} из printGrid для кнопок выгрузки
        _openPrintPreview: function(printHtml, ctx) {""",
    1, 'подпись _openPrintPreview')

rep("""            var foot = document.createElement('div');
            foot.className = 'wspprev-foot';
            foot.innerHTML =
                '<button type="button" class="wspprev-btn wspprev-print">' +
                '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V6z" fill="currentColor"/></svg>' +
                'Печать</button>' +
                '<button type="button" class="wspprev-btn wspprev-save">' +
                '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" fill="currentColor"/></svg>' +
                'Сохранить в файл</button>' +
                '<button type="button" class="wspprev-btn ' +
                'wspprev-cancel">Отмена</button>' +
                '<span class="wspprev-hint">A4 · альбомная</span>';""",
"""            var foot = document.createElement('div');
            foot.className = 'wspprev-foot';
            // Task 438: вместо одной кнопки «Сохранить в файл»
            // (standalone-HTML) — ДВЕ: «Сохранить PDF» и «Сохранить
            // Excel» (клиентские генераторы, без библиотек)
            foot.innerHTML =
                '<button type="button" class="wspprev-btn wspprev-print">' +
                '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V6z" fill="currentColor"/></svg>' +
                'Печать</button>' +
                '<button type="button" class="wspprev-btn wspprev-pdf">' +
                '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6H6zm7 7V3.5L18.5 9H13z" fill="currentColor"/></svg>' +
                'Сохранить PDF</button>' +
                '<button type="button" class="wspprev-btn wspprev-xlsx">' +
                '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 19H5v-2h4v2zm0-4H5v-2h4v2zm0-4H5V9h4v2zm10 8h-4v-2h4v2zm0-4h-4v-2h4v2zm0-4h-4V9h4v2z" fill="currentColor"/></svg>' +
                'Сохранить Excel</button>' +
                '<button type="button" class="wspprev-btn ' +
                'wspprev-cancel">Отмена</button>' +
                '<span class="wspprev-hint">A4 · альбомная</span>';""",
    1, 'кнопки диалога')

rep("""            var printBtn = foot.querySelector('.wspprev-print');
            var saveBtn = foot.querySelector('.wspprev-save');
            var cancelBtn = foot.querySelector('.wspprev-cancel');""",
"""            var printBtn = foot.querySelector('.wspprev-print');
            var pdfBtn = foot.querySelector('.wspprev-pdf');
            var xlsxBtn = foot.querySelector('.wspprev-xlsx');
            var cancelBtn = foot.querySelector('.wspprev-cancel');
            // Task 438: данные для выгрузок — из контекста
            // printGrid; вызов без контекста (старые тесты) —
            // кнопки просто ничего не сохраняют
            var ctxEmps = (ctx && ctx.viewEmps) || [];
            var ctxAgg = ctx ? ctx.agg : null;""",
    1, 'селекторы кнопок диалога')

rep("""            if (saveBtn && saveBtn.addEventListener) {
                saveBtn.addEventListener('click', function() {
                    self._savePrintFile(printHtml);
                });
            }""",
"""            if (pdfBtn && pdfBtn.addEventListener) {
                pdfBtn.addEventListener('click', function() {
                    self._savePrintPdf(ctxEmps, ctxAgg);
                });
            }
            if (xlsxBtn && xlsxBtn.addEventListener) {
                xlsxBtn.addEventListener('click', function() {
                    self._savePrintXlsx(ctxEmps, ctxAgg);
                });
            }""",
    1, 'обработчики кнопок PDF/Excel')

# ============================================================
# 3. CSS кнопок: .wspprev-save → .wspprev-pdf/.wspprev-xlsx
# ============================================================
rep("""    .wspprev-save,
    .wspprev-cancel {""",
"""    .wspprev-pdf,
    .wspprev-xlsx,
    .wspprev-cancel {""", 1, 'CSS кнопок 1')

rep("""    .wspprev-save:hover,
    .wspprev-cancel:hover { background: rgba(255, 255, 255, 0.07); }""",
"""    .wspprev-pdf:hover,
    .wspprev-xlsx:hover,
    .wspprev-cancel:hover { background: rgba(255, 255, 255, 0.07); }""",
    1, 'CSS кнопок 2')

# ============================================================
# 4. Комментарий кнопки «Печать» в тулбаре (упоминание Часов)
# ============================================================
rep("""                         справочника, колонки «Дни»/«Часы» — те же
                         счётчики, что во вкладке «Итоги учёта», и
                         легенда кодов) и вызывает window.print().""",
"""                         справочника, колонки «Дни»/«Перераб.» —
                         те же счётчики, что во вкладке «Итоги
                         учёта» (Task 438: часы убраны, в
                         «Перераб.» — только дни), и легенда кодов)
                         и вызывает window.print().""",
    1, 'комментарий wsPrintBtn')

io.open(path, 'w', encoding='utf-8').write(src)
print('index.html: этап 2 (PDF/Excel/диалог/CSS) — OK, вставок Task 438: %d' % (src.count('Task 438') - n0))
