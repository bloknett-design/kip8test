/**
 * @module core/pinned
 * @description Pinned subsections on dashboard — pin/unpin, drag-and-drop reorder, swipe-to-add.
 * Extracted from the monolithic src/index.html (lines 10003–10641).
 */

const PINNED_STORAGE_KEY = 'pinnedSubsections';
let currentPinKey = null; // ключ подраздела, для которого открыт sheet

// Чтение списка закреплённых подразделов из localStorage.
// Возвращает массив ключей (например, ['calc-kipa', 'library']).
function getPinnedItems() {
    try {
        const raw = localStorage.getItem(PINNED_STORAGE_KEY);
        if (!raw) return [];
        const arr = JSON.parse(raw);
        return Array.isArray(arr) ? arr.filter(k => window.SUBSECTIONS[k]) : [];
    } catch (e) { return []; }
}

// Запись списка закреплённых подразделов в localStorage.
function setPinnedItems(arr) {
    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify(arr));
}

// Проверка, закреплён ли указанный подраздел.
function isPinned(key) {
    return getPinnedItems().indexOf(key) !== -1;
}

// Переключение состояния закрепления подраздела.
function togglePin(key) {
    let items = getPinnedItems();
    if (items.indexOf(key) === -1) {
        items.push(key);
    } else {
        items = items.filter(k => k !== key);
    }
    setPinnedItems(items);
    renderPinnedItems();
}

// Экранирование HTML (защита от XSS при рендере пользовательских данных).
// Использует существующую функцию escHtml, если она есть.
function pinEscHtml(s) {
    if (typeof window.escHtml === 'function') return window.escHtml(String(s));
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// Рендеринг контейнера закреплённых подразделов на дашборде.
// Вызывается при загрузке и после каждого pin/unpin.
function renderPinnedItems() {
    const container = document.getElementById('pinnedItemsContainer');
    if (!container) return;
    const items = getPinnedItems();
    if (items.length === 0) {
        container.innerHTML =
            '<div class="pinned-empty-hint">' +
            'Закрепите часто используемые разделы — они появятся здесь. ' +
            'Нажмите <svg class="pin-empty-icon" viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg> на любом разделе или подразделе и выберите <b>«Добавить на главную»</b>, ' +
            'или сделайте свайп влево/вправо по пункту — появится зелёная подложка <b>«Добавить»</b>.' +
            '</div>';
        // Даже если нет закреплённых, добавляем кнопку «Избранное» если есть избранное
        if (typeof window.KipFav !== 'undefined') window.KipFav.updateDashboardButton();
        return;
    }
    let html = '<div class="menu-btn-row pinned-items-row">';
    items.forEach(key => {
        const s = window.SUBSECTIONS[key];
        if (!s) return;
        const isDocs = s.category === 'docs';
        const borderColor = isDocs ? 'border-color:rgba(199,150,74,0.35);' : '';
        const labelColor  = isDocs ? 'color:#c7964a;' : '';
        const arrowColor  = isDocs ? 'color:rgba(199,150,74,0.4);' : '';
        html +=
            '<div class="pinned-item-cell">' +
                '<div class="pinned-item-delete-bg pinned-item-delete-left"><svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Убрать</span></div>' +
                '<div class="pinned-item-delete-bg pinned-item-delete-right"><svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Убрать</span></div>' +
                '<div class="menu-btn pinned-item" data-pinned-key="' + key + '" onclick="navigateTo(\'' + s.target + '\')" style="' + borderColor + '">' +
                    '<div class="menu-btn-text">' +
                        '<div class="menu-btn-label" style="' + labelColor + '">' + pinEscHtml(s.label) + '</div>' +
                        '<div class="menu-btn-sublabel">' + pinEscHtml(s.sublabel) + '</div>' +
                    '</div>' +
                    '<button type="button" class="menu-btn-overflow" aria-label="Действия" onclick="event.stopPropagation(); openPinSheet(\'' + key + '\')">' +
                        '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>' +
                    '</button>' +
                    '<i class="menu-btn-arrow" style="' + arrowColor + '">›</i>' +
                '</div>' +
            '</div>';
    });
    html += '</div>';
    container.innerHTML = html;
    // После рендера вешаем обработчики long-press + drag-and-drop на каждую карточку.
    attachPinnedDragHandlers();
    // Добавить кнопку «Избранное» (если есть избранное)
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateDashboardButton();
}

// ============================================================
// ПЕРЕТАСКИВАНИЕ ЗАКРЕПЛЁННЫХ ПУНКТОВ (long-press + drag)
// ============================================================
const PINNED_DRAG_DELAY = 500;       // мс долгого зажатия до начала перетаскивания
const PINNED_DRAG_THRESHOLD = 10;    // px — горизонтальное движение больше этого → свайп
const PINNED_IDLE_SCROLL_THRESHOLD = 15; // px — вертикальное смещение в idle
const PINNED_SWIPE_DELETE_RATIO = 0.3; // доля ширины карточки для удаления свайпом
let pinnedDragState = null;          // { el, key, startX, startY, timer, clone, hoverEl, mode, width, currentDx, lastScrollY }

function attachPinnedDragHandlers() {
    const items = document.querySelectorAll('#pinnedItemsContainer .pinned-item');
    items.forEach(el => {
        el.addEventListener('pointerdown', onPinnedPointerDown);
    });
}

function onPinnedPointerDown(e) {
    if (e.target.closest('.menu-btn-overflow')) return;
    if (e.button !== undefined && e.button !== 0) return;
    const el = e.currentTarget;
    const key = el.getAttribute('data-pinned-key');
    if (!key) return;
    e.preventDefault();
    const rect = el.getBoundingClientRect();
    pinnedDragState = {
        el: el,
        cell: el.closest('.pinned-item-cell'),
        key: key,
        startX: e.clientX,
        startY: e.clientY,
        timer: setTimeout(() => startPinnedDrag(e), PINNED_DRAG_DELAY),
        clone: null,
        hoverEl: null,
        grabOffsetX: 0,
        grabOffsetY: 0,
        moved: false,
        mode: 'idle',
        width: rect.width,
        currentDx: 0,
        lastScrollY: e.clientY
    };
    window.addEventListener('pointermove', onPinnedPointerMove);
    window.addEventListener('pointerup', onPinnedPointerUp);
    window.addEventListener('pointercancel', onPinnedPointerUp);
    window.addEventListener('touchmove', onPinnedTouchMove, { passive: false });
}

function onPinnedTouchMove(e) {
    if (pinnedDragState && pinnedDragState.mode === 'drag') {
        e.preventDefault();
    }
}

function onPinnedPointerMove(e) {
    if (!pinnedDragState) return;
    const st = pinnedDragState;
    const dx = e.clientX - st.startX;
    const dy = e.clientY - st.startY;
    if (st.mode === 'scroll') {
        const deltaY = e.clientY - st.lastScrollY;
        if (deltaY !== 0) {
            window.scrollBy(0, -deltaY);
        }
        st.lastScrollY = e.clientY;
        return;
    }
    if (!st.clone && st.mode !== 'swipe') {
        var absDx = Math.abs(dx), absDy = Math.abs(dy);
        if (absDx > PINNED_DRAG_THRESHOLD && absDx > absDy * 1.5) {
            clearTimeout(st.timer);
            startPinnedSwipe();
        }
        else if (absDy > PINNED_IDLE_SCROLL_THRESHOLD && absDy > absDx * 1.5) {
            clearTimeout(st.timer);
            st.mode = 'scroll';
            st.lastScrollY = e.clientY;
            if (dy !== 0) {
                window.scrollBy(0, -dy);
            }
        }
        return;
    }
    if (st.mode === 'swipe') {
        e.preventDefault();
        updatePinnedSwipe(dx);
        return;
    }
    e.preventDefault();
    st.moved = true;
    st.clone.style.left = (e.clientX - st.grabOffsetX) + 'px';
    st.clone.style.top = (e.clientY - st.grabOffsetY) + 'px';
    st.clone.style.pointerEvents = 'none';
    const target = document.elementFromPoint(e.clientX, e.clientY);
    const newHover = target ? target.closest('#pinnedItemsContainer .pinned-item') : null;
    if (newHover !== st.hoverEl) {
        if (st.hoverEl) st.hoverEl.classList.remove('pinned-item-drag-over');
        if (newHover && newHover !== st.el) newHover.classList.add('pinned-item-drag-over');
        st.hoverEl = newHover;
    }
}

function startPinnedSwipe() {
    const st = pinnedDragState;
    if (!st) return;
    st.mode = 'swipe';
    st.el.classList.add('swipe-active');
    st.el.style.pointerEvents = 'none';
    if (navigator.vibrate) navigator.vibrate(10);
}

function updatePinnedSwipe(dx) {
    const st = pinnedDragState;
    if (!st) return;
    let effectiveDx = dx;
    if (Math.abs(dx) > st.width) {
        const overshoot = Math.abs(dx) - st.width;
        effectiveDx = Math.sign(dx) * (st.width + overshoot * 0.3);
    }
    st.currentDx = effectiveDx;
    st.el.style.transform = 'translateX(' + effectiveDx + 'px)';
    if (st.cell) {
        st.cell.classList.toggle('swiping-left',  effectiveDx < 0);
        st.cell.classList.toggle('swiping-right', effectiveDx > 0);
    }
}

function onPinnedPointerUp(e) {
    if (!pinnedDragState) return;
    const st = pinnedDragState;
    clearTimeout(st.timer);
    if (st.mode === 'scroll') {
        cleanupPinnedDrag();
        return;
    }
    if (st.mode === 'swipe') {
        endPinnedSwipe();
        return;
    }
    if (!st.clone) {
        cleanupPinnedDrag();
        return;
    }
    let didReorder = false;
    if (st.moved && st.hoverEl && st.hoverEl !== st.el) {
        const items = getPinnedItems();
        const fromIdx = items.indexOf(st.key);
        const toIdx = items.indexOf(st.hoverEl.getAttribute('data-pinned-key'));
        if (fromIdx !== -1 && toIdx !== -1 && fromIdx !== toIdx) {
            items.splice(fromIdx, 1);
            items.splice(toIdx, 0, st.key);
            setPinnedItems(items);
            didReorder = true;
            if (navigator.vibrate) navigator.vibrate(15);
        }
    }
    cleanupPinnedDrag();
    if (didReorder) {
        renderPinnedItems();
    }
}

function endPinnedSwipe() {
    const st = pinnedDragState;
    if (!st) return;
    const threshold = st.width * PINNED_SWIPE_DELETE_RATIO;
    const shouldDelete = Math.abs(st.currentDx) > threshold;
    if (shouldDelete) {
        const direction = st.currentDx < 0 ? -1 : 1;
        st.el.classList.remove('swipe-active');
        st.el.classList.add('swipe-removing');
        st.el.style.transform = 'translateX(' + (direction * st.width * 1.2) + 'px)';
        if (navigator.vibrate) navigator.vibrate(30);
        setTimeout(() => {
            togglePin(st.key);
            if (typeof window.showToast === 'function') {
                const label = window.SUBSECTIONS[st.key] ? window.SUBSECTIONS[st.key].label : '';
                window.showToast('«' + label + '» убрано с главной');
            }
        }, 250);
        const savedCell = st.cell;
        pinnedDragState = null;
        window.removeEventListener('pointermove', onPinnedPointerMove);
        window.removeEventListener('pointerup', onPinnedPointerUp);
        window.removeEventListener('pointercancel', onPinnedPointerUp);
        if (savedCell) {
            savedCell.classList.remove('swiping-left', 'swiping-right');
        }
    } else {
        st.el.classList.remove('swipe-active');
        st.el.style.transform = '';
        if (st.cell) {
            st.cell.classList.remove('swiping-left', 'swiping-right');
        }
        cleanupPinnedDrag();
    }
}

function startPinnedDrag(e) {
    const st = pinnedDragState;
    if (!st) return;
    const rect = st.el.getBoundingClientRect();
    st.grabOffsetX = st.startX - rect.left;
    st.grabOffsetY = st.startY - rect.top;
    const clone = st.el.cloneNode(true);
    clone.classList.add('pinned-item-clone');
    clone.style.position = 'fixed';
    clone.style.left = rect.left + 'px';
    clone.style.top = rect.top + 'px';
    clone.style.width = rect.width + 'px';
    clone.style.height = rect.height + 'px';
    clone.style.zIndex = '9999';
    clone.style.pointerEvents = 'none';
    clone.style.margin = '0';
    document.body.appendChild(clone);
    st.clone = clone;
    st.el.classList.add('pinned-item-dragging');
    if (navigator.vibrate) navigator.vibrate(30);
    st.el.style.pointerEvents = 'none';
}

function cleanupPinnedDrag() {
    if (!pinnedDragState) return;
    const st = pinnedDragState;
    clearTimeout(st.timer);
    if (st.clone) {
        st.clone.remove();
    }
    if (st.el) {
        st.el.classList.remove('pinned-item-dragging');
        st.el.style.pointerEvents = '';
    }
    if (st.hoverEl) {
        st.hoverEl.classList.remove('pinned-item-drag-over');
    }
    pinnedDragState = null;
    window.removeEventListener('pointermove', onPinnedPointerMove);
    window.removeEventListener('pointerup', onPinnedPointerUp);
    window.removeEventListener('pointercancel', onPinnedPointerUp);
    window.removeEventListener('touchmove', onPinnedTouchMove);
}

// ============================================================
// SWIPE-TO-ADD для подразделов на страницах меню
// ============================================================
const SUBSECTION_SWIPE_ADD_RATIO = 0.3;
const SUBSECTION_SWIPE_THRESHOLD = 10;
let subsectionSwipeState = null;

function wrapSubsectionItems(pageId) {
    const page = document.getElementById(pageId);
    if (!page) return;
    const buttons = page.querySelectorAll('.menu-btn[onclick^="navigateTo("]');
    buttons.forEach(btn => {
        if (btn.closest('.subsection-cell')) return;
        if (btn.hasAttribute('data-pinned-key')) return;
        if (btn.classList.contains('menu-btn-placeholder')) return;
        if (btn.id === 'minesweeperBtn') return;
        const onclickAttr = btn.getAttribute('onclick') || '';
        const match = onclickAttr.match(/navigateTo\(['"]([^'"]+)['"]\)/);
        if (!match) return;
        const key = match[1];
        if (!window.SUBSECTIONS[key]) return;

        const cell = document.createElement('div');
        cell.className = 'subsection-cell';
        cell.setAttribute('data-subsection-key', key);

        const plusSvg = '<svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
        const leftBg = document.createElement('div');
        leftBg.className = 'subsection-add-bg subsection-add-left';
        leftBg.innerHTML = plusSvg + '<span>Добавить</span>';
        const rightBg = document.createElement('div');
        rightBg.className = 'subsection-add-bg subsection-add-right';
        rightBg.innerHTML = plusSvg + '<span>Добавить</span>';

        btn.parentNode.insertBefore(cell, btn);
        cell.appendChild(leftBg);
        cell.appendChild(rightBg);
        cell.appendChild(btn);

        btn.addEventListener('pointerdown', onSubsectionPointerDown);
    });
}

function onSubsectionPointerDown(e) {
    if (e.target.closest('.menu-btn-overflow')) return;
    if (e.button !== undefined && e.button !== 0) return;
    const el = e.currentTarget;
    const cell = el.closest('.subsection-cell');
    if (!cell) return;
    const key = cell.getAttribute('data-subsection-key');
    if (!key) return;
    if (isPinned(key)) return;
    const rect = el.getBoundingClientRect();
    subsectionSwipeState = {
        el: el,
        cell: cell,
        key: key,
        startX: e.clientX,
        startY: e.clientY,
        width: rect.width,
        currentDx: 0,
        active: false
    };
    window.addEventListener('pointermove', onSubsectionPointerMove);
    window.addEventListener('pointerup', onSubsectionPointerUp);
    window.addEventListener('pointercancel', onSubsectionPointerUp);
}

function onSubsectionPointerMove(e) {
    if (!subsectionSwipeState) return;
    const st = subsectionSwipeState;
    const dx = e.clientX - st.startX;
    const dy = e.clientY - st.startY;
    if (!st.active) {
        if (Math.abs(dx) > SUBSECTION_SWIPE_THRESHOLD || Math.abs(dy) > SUBSECTION_SWIPE_THRESHOLD) {
            if (Math.abs(dx) > Math.abs(dy) * 1.5) {
                st.active = true;
                st.el.classList.add('swipe-active');
                st.el.style.pointerEvents = 'none';
                if (navigator.vibrate) navigator.vibrate(10);
            } else {
                cleanupSubsectionSwipe();
                return;
            }
        } else {
            return;
        }
    }
    e.preventDefault();
    updateSubsectionSwipe(dx);
}

function updateSubsectionSwipe(dx) {
    const st = subsectionSwipeState;
    if (!st) return;
    let effectiveDx = dx;
    if (Math.abs(dx) > st.width) {
        const overshoot = Math.abs(dx) - st.width;
        effectiveDx = Math.sign(dx) * (st.width + overshoot * 0.3);
    }
    st.currentDx = effectiveDx;
    st.el.style.transform = 'translateX(' + effectiveDx + 'px)';
    if (st.cell) {
        st.cell.classList.toggle('swiping-left',  effectiveDx < 0);
        st.cell.classList.toggle('swiping-right', effectiveDx > 0);
    }
}

function onSubsectionPointerUp(e) {
    if (!subsectionSwipeState) return;
    endSubsectionSwipe();
}

function endSubsectionSwipe() {
    const st = subsectionSwipeState;
    if (!st) return;
    const threshold = st.width * SUBSECTION_SWIPE_ADD_RATIO;
    const shouldAdd = Math.abs(st.currentDx) > threshold;
    if (shouldAdd && !isPinned(st.key)) {
        if (navigator.vibrate) navigator.vibrate(30);
        const key = st.key;
        togglePin(key);
        if (typeof window.showToast === 'function') {
            const label = window.SUBSECTIONS[key] ? window.SUBSECTIONS[key].label : '';
            window.showToast('«' + label + '» добавлено на главную');
        }
        st.el.classList.remove('swipe-active');
        st.el.style.transform = '';
        if (st.cell) {
            st.cell.classList.remove('swiping-left', 'swiping-right');
        }
        cleanupSubsectionSwipe();
    } else {
        st.el.classList.remove('swipe-active');
        st.el.style.transform = '';
        if (st.cell) {
            st.cell.classList.remove('swiping-left', 'swiping-right');
        }
        cleanupSubsectionSwipe();
    }
}

function cleanupSubsectionSwipe() {
    if (!subsectionSwipeState) return;
    const st = subsectionSwipeState;
    if (st.el) {
        st.el.classList.remove('swipe-active');
        st.el.style.pointerEvents = '';
        st.el.style.transform = '';
    }
    if (st.cell) {
        st.cell.classList.remove('swiping-left', 'swiping-right');
    }
    subsectionSwipeState = null;
    window.removeEventListener('pointermove', onSubsectionPointerMove);
    window.removeEventListener('pointerup', onSubsectionPointerUp);
    window.removeEventListener('pointercancel', onSubsectionPointerUp);
}

// ============================================================
// Exports
// ============================================================
export {
    PINNED_STORAGE_KEY,
    PINNED_DRAG_DELAY,
    PINNED_DRAG_THRESHOLD,
    SUBSECTION_SWIPE_ADD_RATIO,
    SUBSECTION_SWIPE_THRESHOLD,
    pinnedDragState,
    subsectionSwipeState,
    currentPinKey,
    getPinnedItems,
    isPinned,
    togglePin,
    renderPinnedItems,
    wrapSubsectionItems,
    setPinnedItems
};
