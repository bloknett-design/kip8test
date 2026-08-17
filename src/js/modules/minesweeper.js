/**
 * @module minesweeper
 * @description Minesweeper game logic and secret tap handler.
 * Extracted from src/index.html (lines ~2749-3051).
 *
 * External dependencies (temporary window bridges):
 *   - navigateTo  (will be imported from core/navigation once available)
 */

// ======================== ИГРА САПЁР ========================
let msCols = 9, msRows = 9, msMines = 10;
let msBoard = [], msRevealed = [], msFlagged = [], msGameOver = false, msFirstClick = true;
let msTimerInterval = null, msSeconds = 0;
let msLongPressTimer = null, msLongPressFired = false;

const msDifficulties = {
    easy: { cols: 9, rows: 9, mines: 10 },
    medium: { cols: 9, rows: 16, mines: 25 },
    hard: { cols: 9, rows: 28, mines: 45 }
};

function msSetDifficulty(diff) {
    const d = msDifficulties[diff];
    if (!d) return;
    msCols = d.cols; msRows = d.rows; msMines = d.mines;
    const sel = document.getElementById('msDiffSelect');
    if (sel) sel.value = diff;
    msInit();
}

function msInit() {
    msBoard = []; msRevealed = []; msFlagged = [];
    msGameOver = false; msFirstClick = true; msSeconds = 0;
    if (msTimerInterval) { clearInterval(msTimerInterval); msTimerInterval = null; }
    document.getElementById('msTimer').textContent = '000';
    document.getElementById('msMineCount').textContent = msMines;
    document.getElementById('msFaceBtn').textContent = '😊';
    document.getElementById('msOverlay').style.display = 'none';

    for (let r = 0; r < msRows; r++) {
        msBoard[r] = []; msRevealed[r] = []; msFlagged[r] = [];
        for (let c = 0; c < msCols; c++) {
            msBoard[r][c] = 0; msRevealed[r][c] = false; msFlagged[r][c] = false;
        }
    }
    msRender();
}

function msPlaceMines(safeR, safeC) {
    let placed = 0;
    while (placed < msMines) {
        let r = Math.floor(Math.random() * msRows);
        let c = Math.floor(Math.random() * msCols);
        if (msBoard[r][c] === -1) continue;
        if (Math.abs(r - safeR) <= 1 && Math.abs(c - safeC) <= 1) continue;
        msBoard[r][c] = -1;
        placed++;
    }
    for (let r = 0; r < msRows; r++) {
        for (let c = 0; c < msCols; c++) {
            if (msBoard[r][c] === -1) continue;
            let count = 0;
            for (let dr = -1; dr <= 1; dr++) {
                for (let dc = -1; dc <= 1; dc++) {
                    let nr = r + dr, nc = c + dc;
                    if (nr >= 0 && nr < msRows && nc >= 0 && nc < msCols && msBoard[nr][nc] === -1) count++;
                }
            }
            msBoard[r][c] = count;
        }
    }
}

function msCalcCellSize() {
    const containerPad = 32;  // ms-container: padding 10px*2 + margin
    const boardPad = window.innerWidth <= 400 ? 8 : 16; // ms-board padding 4px*2 or 8px*2
    const gapSize = window.innerWidth <= 400 ? 1 : 2;
    const scrollSpace = 36;   // scroll-spacer width for touch scrolling
    const availW = window.innerWidth - containerPad - boardPad - scrollSpace;
    const cellSz = Math.floor((availW - (msCols - 1) * gapSize) / msCols);
    return Math.max(cellSz, 20); // minimum 20px for tappability
}

function msRender() {
    let board = document.getElementById('msBoard');
    const cellSize = msCalcCellSize();
    const fontSize = cellSize <= 24 ? 10 : cellSize <= 28 ? 12 : 14;
    const gapSize = window.innerWidth <= 400 ? 1 : 2;
    board.style.gridTemplateColumns = `repeat(${msCols}, ${cellSize}px)`;
    board.style.gap = gapSize + 'px';
    board.innerHTML = '';
    for (let r = 0; r < msRows; r++) {
        for (let c = 0; c < msCols; c++) {
            let cell = document.createElement('div');
            cell.className = 'ms-cell';
            cell.dataset.r = r; cell.dataset.c = c;
            cell.style.width = cellSize + 'px';
            cell.style.height = cellSize + 'px';
            cell.style.fontSize = fontSize + 'px';

            if (msRevealed[r][c]) {
                cell.classList.add('ms-cell-revealed');
                if (msBoard[r][c] === -1) {
                    cell.classList.add(msGameOver ? 'ms-cell-mine-hit' : 'ms-cell-mine');
                    cell.innerHTML = '<span class="ms-mine-icon" style="font-size:' + Math.round(cellSize * 0.55) + 'px">●</span>';
                } else if (msBoard[r][c] > 0) {
                    cell.classList.add('ms-num-' + msBoard[r][c]);
                    cell.textContent = msBoard[r][c];
                }
            } else if (msFlagged[r][c]) {
                cell.classList.add('ms-cell-hidden', 'ms-cell-flagged');
                cell.innerHTML = '<span class="ms-flag-icon" style="font-size:' + Math.round(cellSize * 0.5) + 'px">⚑</span>';
            } else {
                cell.classList.add('ms-cell-hidden');
            }

            // Unified pointer handling for mobile + desktop
            let msCellTouchFired = false;
            let msCellTouchTimer = null;

            cell.addEventListener('touchstart', function(e) {
                msLongPressFired = false;
                msCellTouchFired = true;
                msLongPressTimer = setTimeout(() => {
                    msLongPressFired = true;
                    msToggleFlag(r, c);
                    if (navigator.vibrate) navigator.vibrate(30);
                }, 400);
            }, { passive: true });

            cell.addEventListener('touchend', function(e) {
                if (msLongPressTimer) { clearTimeout(msLongPressTimer); msLongPressTimer = null; }
                if (!msLongPressFired && !msGameOver) {
                    msReveal(r, c);
                }
                e.preventDefault(); // prevent subsequent click event on mobile
            });

            cell.addEventListener('touchmove', function() {
                if (msLongPressTimer) { clearTimeout(msLongPressTimer); msLongPressTimer = null; }
                msCellTouchFired = false;
            }, { passive: true });

            // Mouse click for desktop — skip if touch already handled
            cell.addEventListener('click', function(e) {
                if (msCellTouchFired) { msCellTouchFired = false; return; }
                if (msGameOver) return;
                msReveal(r, c);
            });

            cell.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                if (msGameOver) return;
                msToggleFlag(r, c);
            });

            board.appendChild(cell);
        }
    }
}

// Recalculate cell sizes on resize/orientation change
window.addEventListener('resize', function() {
    if (document.getElementById('page-minesweeper').classList.contains('active')) {
        msRender();
    }
});

function msReveal(r, c) {
    if (msGameOver || msRevealed[r][c] || msFlagged[r][c]) return;
    if (msFirstClick) {
        msFirstClick = false;
        msPlaceMines(r, c);
        msTimerInterval = setInterval(() => {
            msSeconds++;
            document.getElementById('msTimer').textContent = String(msSeconds).padStart(3, '0');
        }, 1000);
    }
    msRevealed[r][c] = true;
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

function msFloodReveal(r, c) {
    for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
            let nr = r + dr, nc = c + dc;
            if (nr >= 0 && nr < msRows && nc >= 0 && nc < msCols && !msRevealed[nr][nc] && !msFlagged[nr][nc]) {
                msRevealed[nr][nc] = true;
                if (msBoard[nr][nc] === 0) msFloodReveal(nr, nc);
            }
        }
    }
}

function msToggleFlag(r, c) {
    if (msGameOver || msRevealed[r][c]) return;
    msFlagged[r][c] = !msFlagged[r][c];
    let flagCount = msFlagged.flat().filter(Boolean).length;
    document.getElementById('msMineCount').textContent = Math.max(0, msMines - flagCount);
    msRender();
    msCheckWin();
}

function msRevealAllMines() {
    for (let r = 0; r < msRows; r++) {
        for (let c = 0; c < msCols; c++) {
            if (msBoard[r][c] === -1) msRevealed[r][c] = true;
        }
    }
}

function msCheckWin() {
    if (msGameOver) return;
    let hiddenCount = 0;
    for (let r = 0; r < msRows; r++) {
        for (let c = 0; c < msCols; c++) {
            if (!msRevealed[r][c]) hiddenCount++;
        }
    }
    if (hiddenCount === msMines) {
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
}

function msShowOverlay(won) {
    let overlay = document.getElementById('msOverlay');
    let text = document.getElementById('msGameOverText');
    let sub = document.getElementById('msGameOverSub');
    if (won) {
        text.textContent = '🎉 Победа!';
        text.style.color = '#4ac771';
        sub.textContent = 'Время: ' + msSeconds + ' сек';
    } else {
        text.textContent = '💥 Взрыв!';
        text.style.color = '#c74a4a';
        sub.textContent = 'Попробуйте ещё раз';
    }
    overlay.style.display = 'flex';
}

// ===== СЕКРЕТНЫЕ КНОПКИ (САПЁР + ТЕЛЕФОННЫЙ СПРАВОЧНИК) =====
let secretTapCount = 0;
let secretTapTimer = null;
const SECRET_TAP_THRESHOLD = 2;
let secretTouchHandled = false;
const SECRET_BUTTON_IDS = ['minesweeperBtn', 'phonebookBtn'];

function secretTapHandler() {
    secretTapCount++;
    document.querySelector('.header-title').classList.add('hint-pulse');
    setTimeout(() => document.querySelector('.header-title').classList.remove('hint-pulse'), 200);
    clearTimeout(secretTapTimer);
    secretTapTimer = setTimeout(() => { secretTapCount = 0; }, 1500);
    if (secretTapCount >= SECRET_TAP_THRESHOLD) {
        secretTapCount = 0;
        clearTimeout(secretTapTimer);
        // Все секретные кнопки открываются одним жестом (toggle)
        const firstBtn = document.getElementById(SECRET_BUTTON_IDS[0]);
        const willReveal = !firstBtn.classList.contains('revealed');
        SECRET_BUTTON_IDS.forEach(id => {
            const btn = document.getElementById(id);
            if (!btn) return;
            if (willReveal) {
                btn.classList.add('revealed');
            } else {
                btn.classList.remove('revealed');
            }
        });
        if (navigator.vibrate) {
            navigator.vibrate(willReveal ? [50,50,100] : [30,30,30]);
        }
        if (willReveal && firstBtn) {
            firstBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

// Register both touch and click for the header title
(function() {
    let headerEl = document.querySelector('.header-title');
    if (!headerEl) return;
    let touchFired = false;
    headerEl.addEventListener('touchend', function(e) {
        touchFired = true;
        secretTapHandler();
        e.preventDefault();
    });
    headerEl.addEventListener('click', function() {
        if (touchFired) { touchFired = false; return; }
        secretTapHandler();
    });
})();

// ========================
// Public exports
// ========================
export { msInit, msSetDifficulty, msRender, secretTapHandler };
