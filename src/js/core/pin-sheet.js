/**
 * @module core/pin-sheet
 * @description Pin sheet (bottom sheet) for pin/unpin subsections.
 * Extracted from the monolithic src/index.html (lines 10795–10930).
 */

// Открытие bottom sheet для pin/unpin указанного подраздела.
function openPinSheet(key) {
    const s = window.SUBSECTIONS[key];
    if (!s) return;
    window.currentPinKey = key;
    const pinned = window.isPinned ? window.isPinned(key) : false;
    document.getElementById('pinSheetTitle').textContent = s.label;
    document.getElementById('pinSheetSublabel').textContent = s.sublabel;
    const actionBtn = document.getElementById('pinSheetAction');
    const extraActions = document.getElementById('pinSheetExtraActions');
    if (pinned) {
        // Для закреплённого пункта: показываем кнопки перемещения + красную «Убрать»
        extraActions.style.display = 'flex';
        renderPinSheetExtraActions(key);
        actionBtn.classList.add('is-pinned');
        actionBtn.innerHTML = '<svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>Убрать с главной страницы';
    } else {
        // Для незакреплённого пункта: только синяя «Добавить»
        extraActions.style.display = 'none';
        actionBtn.classList.remove('is-pinned');
        actionBtn.innerHTML = '<svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>Добавить на главную страницу';
    }
    document.getElementById('pinSheetOverlay').classList.add('active');
    document.getElementById('pinSheet').classList.add('active');
    if (navigator.vibrate) navigator.vibrate(15);
}

// Рендеринг кнопок перемещения в bottom sheet.
function renderPinSheetExtraActions(key) {
    const items = window.getPinnedItems ? window.getPinnedItems() : [];
    const idx = items.indexOf(key);
    const isFirst = idx <= 0;
    const isLast = idx === -1 || idx >= items.length - 1;
    const extraActions = document.getElementById('pinSheetExtraActions');
    if (!extraActions) return;
    extraActions.innerHTML =
        '<button type="button" class="pin-sheet-action pin-sheet-action-secondary"' + (isFirst ? ' disabled' : '') + ' onclick="movePinnedItem(\'' + key + '\', -1)">' +
            '<svg viewBox="0 0 24 24"><polyline points="18 15 12 9 6 15"/></svg>Переместить вверх' +
        '</button>' +
        '<button type="button" class="pin-sheet-action pin-sheet-action-secondary"' + (isLast ? ' disabled' : '') + ' onclick="movePinnedItem(\'' + key + '\', 1)">' +
            '<svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>Переместить вниз' +
        '</button>';
}

// Перемещение закреплённого пункта вверх (-1) или вниз (+1).
function movePinnedItem(key, direction) {
    let items = window.getPinnedItems ? window.getPinnedItems() : [];
    const idx = items.indexOf(key);
    if (idx === -1) return;
    const newIdx = idx + direction;
    if (newIdx < 0 || newIdx >= items.length) return;
    const tmp = items[idx];
    items[idx] = items[newIdx];
    items[newIdx] = tmp;
    if (window.setPinnedItems) window.setPinnedItems(items);
    if (window.renderPinnedItems) window.renderPinnedItems();
    renderPinSheetExtraActions(key);
    if (navigator.vibrate) navigator.vibrate(15);
}

// Закрытие bottom sheet.
function closePinSheet() {
    document.getElementById('pinSheetOverlay').classList.remove('active');
    document.getElementById('pinSheet').classList.remove('active');
    if (typeof window.currentPinKey !== 'undefined') window.currentPinKey = null;
}

// Выполнение действия pin/unpin из sheet.
function executePinToggle() {
    if (!window.currentPinKey) return;
    const wasPinned = window.isPinned ? window.isPinned(window.currentPinKey) : false;
    if (window.togglePin) window.togglePin(window.currentPinKey);
    const label = window.SUBSECTIONS && window.SUBSECTIONS[window.currentPinKey] ? window.SUBSECTIONS[window.currentPinKey].label : '';
    if (typeof window.showToast === 'function') {
        window.showToast(wasPinned ? ('«' + label + '» убрано с главной') : ('«' + label + '» добавлено на главную'));
    }
    closePinSheet();
}

export {
    openPinSheet,
    closePinSheet,
    executePinToggle,
    movePinnedItem,
    renderPinSheetExtraActions
};
