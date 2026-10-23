#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 546 — Сапёр: (1) анимация переворачивания клетки с глянцевым
бликом + вибрация; (2) архив счёта пользователей по email — лист
«Сапёр» в таблице KIP8_Access (новая страница по заявке) + клиент
(отправка результата партии + блок «Архив партий»).

Патчит index.html (14 патчей) и scripts/Code.gs (2 патча).
Якоря байт-в-байт уникальны в kip8test и kip8 — скрипт работает в
обоих репо: python3 task546-apply.py /home/z/my-project/kip8test

НОВЫЙ файл scripts/MinesweeperArchive.gs — отдельно (Write/cp).
Тесты tests/test-task546.js — отдельно.
"""
import io
import sys

repo = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/kip8test'

PATCHES_INDEX = []
PATCHES_CODE = []


def patch(idx_list, anchor, replacement, label):
    idx_list.append((anchor, replacement, label))


# ============================================================
# index.html — CSS
# ============================================================

# --- 1. Ключевые кадры переворота + блик + перспектива поля ---
patch(PATCHES_INDEX, u"""    .ms-cell-mine-hit {
        background: rgba(199,74,74,0.4);
        border: 1px solid rgba(199,74,74,0.6);
    }
""", u"""    .ms-cell-mine-hit {
        background: rgba(199,74,74,0.4);
        border: 1px solid rgba(199,74,74,0.6);
    }
    /* ===== Task 546: анимация переворачивания клетки (rotateY из
       90°) с глянцевым бликом — диагональная полоса света скользит
       по грани клетки вслед за переворотом ===== */
    .ms-board { perspective: 900px; }
    .ms-cell { overflow: hidden; }
    .ms-cell.ms-cell-flip {
        animation: msCellFlip 0.45s cubic-bezier(0.2, 0.7, 0.3, 1) backwards;
        will-change: transform;
    }
    .ms-cell.ms-cell-flip::after {
        content: '';
        position: absolute; top: -20%; bottom: -20%; left: -75%;
        width: 65%;
        background: linear-gradient(105deg,
            rgba(255,255,255,0) 0%,
            rgba(255,255,255,0.18) 35%,
            rgba(255,255,255,0.55) 50%,
            rgba(255,255,255,0.18) 65%,
            rgba(255,255,255,0) 100%);
        transform: skewX(-18deg) translateX(0);
        animation: msCellShine 0.55s ease-out backwards;
        animation-delay: inherit;   /* волна: блик ждёт свой переворот */
        pointer-events: none;
        border-radius: inherit;
    }
    @keyframes msCellFlip {
        0%   { transform: rotateY(90deg) scale(0.72); opacity: 0.35; }
        60%  { opacity: 1; }
        100% { transform: rotateY(0deg) scale(1); opacity: 1; }
    }
    @keyframes msCellShine {
        0%   { transform: skewX(-18deg) translateX(0); opacity: 0; }
        15%  { opacity: 1; }
        100% { transform: skewX(-18deg) translateX(320%); opacity: 0; }
    }
    /* Меньше движения — без анимации (доступность) */
    @media (prefers-reduced-motion: reduce) {
        .ms-cell.ms-cell-flip { animation: none; }
        .ms-cell.ms-cell-flip::after { animation: none; content: none; }
    }
""", 'CSS: keyframes переворота + блик + perspective + reduced-motion')

# --- 2. Слоты архива партий (проигрыш + дата) ---
patch(PATCHES_INDEX, u"""    .ms-ach-slot.empty { opacity: 0.45; }
""", u"""    .ms-ach-slot.empty { opacity: 0.45; }
    /* Task 546: слот проигранной партии архива + дата в слоте */
    .ms-ach-slot.loss {
        background: rgba(199, 74, 74, 0.08);
        border-color: rgba(199, 74, 74, 0.35);
    }
    .ms-ach-date {
        font-size: 10px; color: var(--text-faint);
        font-variant-numeric: tabular-nums; white-space: nowrap;
        flex-shrink: 0;
    }
    /* Task 546 (браузерная верификация): строка архива — слоты с
       переносом (иконка+сложность / время+дата), чтобы контент не
       вылезал за границы слота при любой ширине; на мобильном —
       3 слота без даты (как строка «Достижений») и короче титул */
    #msSrvRow .ms-ach-slot {
        flex-wrap: wrap;
        align-content: center;
        row-gap: 2px;
        column-gap: 6px;
        padding: 6px 8px;
    }
    #msSrvRow .ms-ach-icon { flex-shrink: 0; }
    #msSrvRow .ms-ach-diff { flex: 1 1 auto; }
    #msSrvRow .ms-ach-time { margin-left: 0; }
    #msSrvRow .ms-ach-date { flex-shrink: 0; }
    @media (max-width: 719px) {
        #msSrvRow .ms-ach-slot:nth-child(n+4) { display: none; }
        #msSrvRow .ms-ach-date { display: none; }
        #msSrvArchive .ms-ach-sub { display: none; }
    }
""", 'CSS: слот .loss архива + .ms-ach-date')

# --- 3. Светлая тема: блик ярче + слот проигрыша/дата ---
patch(PATCHES_INDEX, u"""    [data-theme="light"] .ms-ach-slot.win { background: rgba(74,199,113,0.1); border-color: rgba(74,199,113,0.4); }
""", u"""    [data-theme="light"] .ms-ach-slot.win { background: rgba(74,199,113,0.1); border-color: rgba(74,199,113,0.4); }
    [data-theme="light"] .ms-ach-slot.loss { background: rgba(184,58,58,0.07); border-color: rgba(184,58,58,0.32); }
    [data-theme="light"] .ms-ach-date { color: rgba(20,20,19,0.4); }
    /* Task 546: блик по глянцу на светлой теме — контрастнее */
    [data-theme="light"] .ms-cell.ms-cell-flip::after {
        background: linear-gradient(105deg,
            rgba(255,255,255,0) 0%,
            rgba(255,255,255,0.35) 35%,
            rgba(255,255,255,0.85) 50%,
            rgba(255,255,255,0.35) 65%,
            rgba(255,255,255,0) 100%);
    }
""", 'CSS: светлая тема — блик/.loss/.ms-ach-date')

# ============================================================
# index.html — HTML
# ============================================================

# --- 4. Блок «Архив партий» (сервер, по email) ---
patch(PATCHES_INDEX, u"""                    <div class="ms-ach-row" id="msAchRow"></div>
                </div>
                <div class="ms-hint">Нажмите — открыть клетку · Долгое нажатие — поставить флаг</div>
""", u"""                    <div class="ms-ach-row" id="msAchRow"></div>
                </div>
                <!-- Task 546: архив партий на сервере — счёт
                     пользователей по email (лист «Сапёр» в
                     KIP8_Access). Скрыт, пока нет сессии/данных -->
                <div class="ms-achievements" id="msSrvArchive" style="display:none;">
                    <div class="ms-ach-title">Архив партий <span class="ms-ach-sub">· сервер · по вашему email</span><span class="ms-ach-score" id="msSrvStat" style="display:none;"></span></div>
                    <div class="ms-ach-row" id="msSrvRow"></div>
                </div>
                <div class="ms-hint">Нажмите — открыть клетку · Долгое нажатие — поставить флаг</div>
""", 'HTML: блок «Архив партий» (#msSrvArchive)')

# ============================================================
# index.html — JS
# ============================================================

# --- 5. Переменные модуля: серия игры + очередь переворотов ---
patch(PATCHES_INDEX, u"""    let msLongPressTimer = null, msLongPressFired = false;
""", u"""    let msLongPressTimer = null, msLongPressFired = false;
    let msGameId = 0;              // Task 546: серия игры — гвард отложенных оверлеев
    let msFlipCells = null;        // Task 546: клетки хода для анимации переворота
""", 'JS: переменные msGameId/msFlipCells')

# --- 6. msInit: новая серия + сброс очереди ---
patch(PATCHES_INDEX, u"""        msGameOver = false; msFirstClick = true; msSeconds = 0;
""", u"""        msGameOver = false; msFirstClick = true; msSeconds = 0;
        msGameId++;                // Task 546: новая серия — отложенные оверлеи гаснут
        msFlipCells = null;        // Task 546: очередь анимации пуста
""", 'JS: msInit — msGameId++/сброс очереди')

# --- 7. msInit: подтянуть свой архив с сервера ---
patch(PATCHES_INDEX, u"""        msRenderAchievements();  // Task 193: лучшие результаты по времени
""", u"""        msRenderAchievements();  // Task 193: лучшие результаты по времени
        msSrvLoadArchive(false); // Task 546: своя история с сервера (тихо, с троттлингом)
""", 'JS: msInit — msSrvLoadArchive')

# --- 8. Чистые функции: задержка волны, вибрация, снимки поля ---
patch(PATCHES_INDEX, u"""    function msRender() {
""", u"""    // Task 546: задержка каскада переворотов — клетка у эпицентра
    // хода переворачивается сразу, дальние — с отступом по
    // расстоянию (волна от клика/взрыва). Чистая функция (тесты).
    function msFlipDelay(r, c, originR, originC) {
        if (typeof originR !== 'number' || typeof originC !== 'number') return 0;
        const dist = Math.max(Math.abs(r - originR), Math.abs(c - originC));
        return Math.min(dist * 35, 385);
    }

    // Task 546: вибрация — безопасная обёртка (iOS Safari не
    // поддерживает navigator.vibrate — там просто без отклика)
    function msVibrate(pattern) {
        try {
            if (typeof navigator !== 'undefined' && navigator.vibrate) {
                navigator.vibrate(pattern);
            }
        } catch (e) { /* нет вибро — не критично */ }
    }

    // Task 546: снимок «открытости» поля до хода — для разницы
    // «до → после» (ново-открытые клетки играют переворот)
    function msSnapshotRevealed() {
        const snap = [];
        for (let r = 0; r < msRows; r++) snap.push(msRevealed[r].slice());
        return snap;
    }

    // Task 546: разница «до → после» — очередь клеток переворота
    // (клик + автораскрытие пустых + мины при взрыве), с эпицентром
    // для волны задержек. Очередь живёт ДО ближайшего msRender.
    function msQueueFlips(before, originR, originC) {
        const flips = [];
        for (let r = 0; r < msRows; r++) {
            for (let c = 0; c < msCols; c++) {
                if (!before[r][c] && msRevealed[r][c]) flips.push({ r: r, c: c });
            }
        }
        if (flips.length) msFlipCells = { cells: flips, or: originR, oc: originC };
    }

    // Task 546: отложенный финал партии — волна переворотов
    // успевает отыграть, потом флаги на мины (победа) и оверлей.
    // Гвард по msGameId: пользователь успел нажать «новая игра» —
    // отмена (оверлей не выскочит поверх свежего поля).
    function msDelayedOverlay(won, delayMs) {
        const gameId = msGameId;
        setTimeout(function () {
            if (msGameId !== gameId || !msGameOver) return;
            if (won) {
                for (let r = 0; r < msRows; r++) {
                    for (let c = 0; c < msCols; c++) {
                        if (msBoard[r][c] === -1) msFlagged[r][c] = true;
                    }
                }
                document.getElementById('msMineCount').textContent = '0';
                msRender();
            }
            msShowOverlay(won);
        }, delayMs);
    }

    function msRender() {
""", 'JS: чистые функции волны/вибрации/очереди/отложенного финала')

# --- 9. msRender: класс переворота + задержка волны ---
patch(PATCHES_INDEX, u"""                } else if (msFlagged[r][c]) {
                    cell.classList.add('ms-cell-hidden', 'ms-cell-flagged');
                    cell.innerHTML = '<span class="ms-flag-icon" style="font-size:' + Math.round(cellSize * 0.5) + 'px">⚑</span>';
                } else {
                    cell.classList.add('ms-cell-hidden');
                }
""", u"""                } else if (msFlagged[r][c]) {
                    cell.classList.add('ms-cell-hidden', 'ms-cell-flagged');
                    cell.innerHTML = '<span class="ms-flag-icon" style="font-size:' + Math.round(cellSize * 0.5) + 'px">⚑</span>';
                } else {
                    cell.classList.add('ms-cell-hidden');
                }

                // Task 546: клетка открылась ЭТИМ ходом — анимация
                // переворота с бликом; задержка — волна от эпицентра
                if (msFlipCells) {
                    for (let i = 0; i < msFlipCells.cells.length; i++) {
                        const fc = msFlipCells.cells[i];
                        if (fc.r === r && fc.c === c) {
                            cell.classList.add('ms-cell-flip');
                            cell.style.animationDelay = msFlipDelay(r, c, msFlipCells.or, msFlipCells.oc) + 'ms';
                            break;
                        }
                    }
                }
""", 'JS: msRender — класс .ms-cell-flip + animationDelay волны')

# --- 10. msRender: очередь отыграна этим рендером ---
patch(PATCHES_INDEX, u"""                board.appendChild(cell);
            }
        }
    }
""", u"""                board.appendChild(cell);
            }
        }

        // Task 546: очередь переворотов отыграна этим рендером —
        // следующий рендер (флаг, ресайз) анимацию не повторяет
        msFlipCells = null;
    }
""", 'JS: msRender — сброс очереди в конце')

# --- 11. msReveal: перевороты, вибрация, отложенный оверлей ---
patch(PATCHES_INDEX, u"""        msRevealed[r][c] = true;
        if (msBoard[r][c] === -1) {
            msGameOver = true;
            msRevealAllMines();
            document.getElementById('msFaceBtn').textContent = '😵';
            if (msTimerInterval) { clearInterval(msTimerInterval); msTimerInterval = null; }
            msShowOverlay(false);
        } else if (msBoard[r][c] === 0) {
            msFloodReveal(r, c);
        }
        msRender();
        msCheckWin();
    }
""", u"""        // Task 546: снимок поля до хода — ново-открытые клетки
        // (клик + автораскрытие + мины при взрыве) переворачиваются
        const flipsBefore = msSnapshotRevealed();
        msRevealed[r][c] = true;
        if (msBoard[r][c] === -1) {
            msGameOver = true;
            msRevealAllMines();
            document.getElementById('msFaceBtn').textContent = '😵';
            if (msTimerInterval) { clearInterval(msTimerInterval); msTimerInterval = null; }
            // Task 546: взрыв — особая вибрация; оверлей с отступом,
            // чтобы отыграла волна переворотов всех мин от эпицентра
            msVibrate([80, 60, 120]);
            msDelayedOverlay(false, 750);
        } else {
            // Task 546: лёгкая вибрация-отклик на переворот клетки
            msVibrate(12);
            if (msBoard[r][c] === 0) msFloodReveal(r, c);
        }
        msQueueFlips(flipsBefore, r, c);
        msRender();
        msCheckWin();
    }
""", 'JS: msReveal — снимок/вибрация/отложенный оверлей взрыва')

# --- 12. msCheckWin: финал победы — после волны переворотов ---
patch(PATCHES_INDEX, u"""        if (hiddenCount === msMines) {
            msGameOver = true;
            document.getElementById('msFaceBtn').textContent = '😎';
            if (msTimerInterval) { clearInterval(msTimerInterval); msTimerInterval = null; }
            // Auto-flag all mines
            for (let r = 0; r < msRows; r++) {
                for (let c = 0; c < msCols; c++) {
                    if (msBoard[r][c] === -1) msFlagged[r][c] = true;
                }
            }
            document.getElementById('msMineCount').textContent = '0';
            msRender();
            msShowOverlay(true);
        }
""", u"""        if (hiddenCount === msMines) {
            msGameOver = true;
            document.getElementById('msFaceBtn').textContent = '😎';
            if (msTimerInterval) { clearInterval(msTimerInterval); msTimerInterval = null; }
            // Task 546: флаги на мины + оверлей — с отступом: волна
            // переворотов последних открытых клеток успевает
            // отыграть. Вибрация победы — сразу
            msVibrate([40, 40, 40, 40, 100]);
            msDelayedOverlay(true, 650);
        }
""", 'JS: msCheckWin — отложенный финал победы + вибрация')

# --- 13. msShowOverlay: отправка результата в серверный архив ---
patch(PATCHES_INDEX, u"""        overlay.style.display = 'flex';
        // Task 193: фиксируем победу в счёте лучших результатов
        msRecordResult(won, msSeconds, msCurrentDiff);
        msRenderAchievements();
    }
""", u"""        overlay.style.display = 'flex';
        // Task 193: фиксируем победу в счёте лучших результатов
        msRecordResult(won, msSeconds, msCurrentDiff);
        msRenderAchievements();
        // Task 546: архив на сервере (лист «Сапёр» в KIP8_Access) —
        // тихая отправка результата партии по email пользователя
        msSrvSendResult(won);
    }
""", 'JS: msShowOverlay — msSrvSendResult')

# --- 14. Клиент серверного архива (отправка/чтение/рендер) ---
patch(PATCHES_INDEX, u"""    // ===== СЕКРЕТНАЯ КНОПКА (САПЁР) =====
""", u"""    // ===== Task 546: АРХИВ ПАРТИЙ НА СЕРВЕРЕ (KIP8_Access, лист
    // «Сапёр») — счёт пользователей по email =====
    // Отправка: конец партии (msShowOverlay) →
    // minesweeper.recordResult (fire-and-forget, тихие ошибки).
    // Чтение: msInit → minesweeper.getMyArchive (троттлинг 60 с,
    // кэш localStorage — оффлайн показывает последний ответ).
    // Тихая деградация: нет токена / сервер ещё без модуля (старый
    // Apps Script отвечает Unknown action) / сеть — блок «Архив
    // партий» скрыт, игра не задаётся ожиданиями. Локальный счёт
    // (Task 193) от сервера не зависит.
    const MS_SRV_CACHE_KEY = 'msSrvArchiveCache';
    const MS_SRV_FETCH_TS_KEY = 'msSrvArchiveFetchTs';
    const MS_SRV_TTL = 60000;   // троттлинг запроса истории: 60 с

    // Чистая функция (тесты): пора ли обновлять архив с сервера?
    function msSrvThrottled(lastFetchTs, now) {
        if (typeof lastFetchTs !== 'number' || isNaN(lastFetchTs) ||
            typeof now !== 'number' || isNaN(now)) return true;
        return now - lastFetchTs >= MS_SRV_TTL;
    }

    // Отправить результат партии на сервер (fire-and-forget).
    // Успех → сразу подтянуть историю (своя новая партия в архиве).
    function msSrvSendResult(won) {
        try {
            if (typeof KipAuth === 'undefined' || !KipAuth) return;
            const token = KipAuth.getToken();
            if (!token) return;   // без сессии — только локальный счёт
            KipAuth.api('minesweeper.recordResult', {
                token: token,
                won: !!won,
                time: msSeconds | 0,
                diff: msCurrentDiff,
                cols: msCols,
                rows: msRows,
                mines: msMines
            }).then(function () {
                try { localStorage.setItem(MS_SRV_FETCH_TS_KEY, '0'); } catch (e) {}
                msSrvLoadArchive(true);
            }).catch(function () { /* тихо: партия уже окончена */ });
        } catch (e) { /* тихо */ }
    }

    // Загрузить свою историю с сервера (троттлинг + кэш оффлайна)
    function msSrvLoadArchive(force) {
        try {
            const block = document.getElementById('msSrvArchive');
            if (!block) return;
            if (typeof KipAuth === 'undefined' || !KipAuth) return;
            const token = KipAuth.getToken();
            if (!token) { block.style.display = 'none'; return; }
            let lastTs = 0;
            try {
                lastTs = parseInt(localStorage.getItem(MS_SRV_FETCH_TS_KEY) || '0', 10) || 0;
            } catch (e) {}
            if (!force && !msSrvThrottled(lastTs, Date.now())) {
                msSrvRenderCached();
                return;
            }
            try { localStorage.setItem(MS_SRV_FETCH_TS_KEY, String(Date.now())); } catch (e) {}
            KipAuth.api('minesweeper.getMyArchive', { token: token })
                .then(function (data) {
                    try { localStorage.setItem(MS_SRV_CACHE_KEY, JSON.stringify(data)); } catch (e) {}
                    msSrvRenderArchive(data);
                })
                .catch(function () { msSrvRenderCached(); });
        } catch (e) { /* тихо */ }
    }

    // Отрисовать архив из кэша (оффлайн / троттлинг / сбой сети)
    function msSrvRenderCached() {
        try {
            const raw = localStorage.getItem(MS_SRV_CACHE_KEY);
            if (raw) msSrvRenderArchive(JSON.parse(raw));
        } catch (e) { /* тихо */ }
    }

    // Чистая функция (тесты): HTML строки архива — 5 слотов.
    // rows: [{won, diff, time, ts}] (новые — первыми). Дата —
    // число (мс) ИЛИ ISO-строка; пустые слоты приглушены.
    function msRenderArchiveRow(rows) {
        const MAX = 5;
        const list = Array.isArray(rows) ? rows.slice(0, MAX) : [];
        let html = '';
        for (let i = 0; i < MAX; i++) {
            const r = list[i];
            if (r) {
                const t = r.ts ? new Date(r.ts) : null;
                const ok = t && !isNaN(t.getTime());
                const dateTxt = ok
                    ? String(t.getDate()).padStart(2, '0') + '.' + String(t.getMonth() + 1).padStart(2, '0')
                    : '—';
                html += '<div class="ms-ach-slot ' + (r.won ? 'win' : 'loss') + '">' +
                    '<span class="ms-ach-icon">' + (r.won ? '✓' : '✗') + '</span>' +
                    '<span class="ms-ach-diff">' + msDiffLabel(r.diff) + '</span>' +
                    '<span class="ms-ach-time">' + (typeof r.time === 'number' ? r.time : '—') + ' с</span>' +
                    '<span class="ms-ach-date">' + dateTxt + '</span></div>';
            } else {
                html += '<div class="ms-ach-slot empty"><span class="ms-ach-icon">·</span>' +
                    '<span class="ms-ach-diff">—</span><span class="ms-ach-time">—</span>' +
                    '<span class="ms-ach-date">—</span></div>';
            }
        }
        return html;
    }

    // Отрисовать блок архива из ответа сервера {rows, stats}
    function msSrvRenderArchive(data) {
        const block = document.getElementById('msSrvArchive');
        if (!block) return;
        const row = document.getElementById('msSrvRow');
        if (!row) return;
        const stat = document.getElementById('msSrvStat');
        if (!data || typeof data !== 'object') { block.style.display = 'none'; return; }
        const rows = Array.isArray(data.rows) ? data.rows : [];
        const stats = data.stats || {};
        if (!rows.length && !stats.total) { block.style.display = 'none'; return; }
        block.style.display = '';
        row.innerHTML = msRenderArchiveRow(rows);
        if (stat) {
            const wins = stats.wins || 0;
            const total = stats.total || (wins + (stats.losses || 0));
            stat.textContent = total + ' партий · ' + wins + ' побед';
            stat.style.display = '';
        }
    }

    // ===== СЕКРЕТНАЯ КНОПКА (САПЁР) =====
""", 'JS: клиент серверного архива (send/load/render)')

# ============================================================
# scripts/Code.gs — маршруты + индекс модулей
# ============================================================

# --- 15. Индекс модулей в шапке ---
patch(PATCHES_CODE, u""" *     PhonebookArchive.setNote(payload)     → {ok, data/error}
 * ============================================================
 */
""", u""" *     PhonebookArchive.setNote(payload)     → {ok, data/error}
 *   MinesweeperArchive (Task 546) — «Сапёр»: архив счёта
 *     пользователей по email — лист «Сапёр» в таблице
 *     KIP8_Access (новая страница по заявке):
 *     MinesweeperArchive.recordResult(payload) → {ok, data/error}
 *     MinesweeperArchive.getMyArchive(payload) → {ok, data/error}
 * ============================================================
 */
""", 'Code.gs: индекс модулей — MinesweeperArchive')

# --- 16. Маршруты ---
patch(PATCHES_CODE, u"""      case 'phonebook.setNote':
        return _json(PhonebookArchive.setNote(payload));

      default:
""", u"""      case 'phonebook.setNote':
        return _json(PhonebookArchive.setNote(payload));

      // MinesweeperArchive.gs (Task 546) — архив счёта «Сапёра»
      // по email: лист «Сапёр» в таблице KIP8_Access. Запись
      // партии + своя история. Гейт secret.view (как у страницы
      // «Сапёр» на клиенте), проверка внутри модуля
      case 'minesweeper.recordResult':
        return _json(MinesweeperArchive.recordResult(payload));

      case 'minesweeper.getMyArchive':
        return _json(MinesweeperArchive.getMyArchive(payload));

      default:
""", 'Code.gs: маршруты minesweeper.recordResult/getMyArchive')


def apply_file(path, patches, kind):
    src = io.open(path, encoding='utf-8').read()
    ok = 0
    for anchor, repl, label in patches:
        if repl != anchor and repl in src:
            print('SKIP [%s] %s: патч уже применён' % (kind, label))
            ok += 1
            continue
        n = src.count(anchor)
        if n != 1:
            print('FAIL [%s] %s: якорь найден %d раз (ожидался 1)' % (kind, label, n))
            sys.exit(1)
        src = src.replace(anchor, repl, 1)
        ok += 1
        print('  OK  %s' % label)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: применено %d патчей' % (path, ok))


print('=== Task 546 apply: %s ===' % repo)
apply_file(repo + '/index.html', PATCHES_INDEX, 'index.html')
apply_file(repo + '/scripts/Code.gs', PATCHES_CODE, 'Code.gs')
print('ГОТОВО')
