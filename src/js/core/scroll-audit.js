/**
 * @module core/scroll-audit
 * @description Scroll audit, adaptive page headers, scroll-hide navbar, pinch-zoom system.
 * Extracted from the monolithic src/index.html (lines 10931–11679).
 */

// ======================== ЗАЩИТНЫЙ АУДИТ ПРОКРУТКИ ========================
// На мобильных scroll-контейнер — html (НЕ body).
// body всегда overflow:visible на мобильном (чтобы не перехватывать свайп).
// Блокировка прокрутки при открытом билете — через CSS html:has(body.ticket-open).
// Этот аудит очищает сиротские состояния и stray инлайн-стили.
function _auditScrollState() {
    // На десктопе — не вмешиваемся (body намеренно overflow:hidden)
    if (window.matchMedia('(min-width: 1024px)').matches) return;

    // Очистить сиротский ticket-open
    if (document.body.classList.contains('ticket-open') &&
        !document.querySelector('.ticket-item.open')) {
        document.body.classList.remove('ticket-open');
        document.body.style.top = '';
        document.body.style.position = '';
        document.body.style.width = '';
        requestAnimationFrame(function() { window.scrollTo(0, (typeof _savedScrollY !== 'undefined' ? _savedScrollY : 0) || 0); });
    }
    // Очистить сиротский ticket-img-viewing
    if (document.body.classList.contains('ticket-img-viewing') &&
        !document.querySelector('.ticket-img-overlay.active')) {
        document.body.classList.remove('ticket-img-viewing');
    }
    // Очистить stray inline overflow:hidden на body
    if (document.body.style.overflow === 'hidden' || document.body.style.overflow === 'hidden auto') {
        document.body.style.overflow = '';
    }
    // На мобильном: html может иметь overflow:hidden только если билет открыт
    if ((document.documentElement.style.overflow === 'hidden' || document.documentElement.style.overflow === 'hidden auto') &&
        !document.body.classList.contains('ticket-open') && !document.body.classList.contains('ticket-img-viewing')) {
        document.documentElement.style.overflow = '';
    }
    // Очистить stray inline position:fixed на body
    if (document.body.style.position === 'fixed') {
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
    }
    // Очистить stray inline height:100% / height:100vh на body и html
    var bh = document.body.style.height;
    if (bh === '100%' || bh === '100vh') {
        document.body.style.height = '';
    }
    var dh = document.documentElement.style.height;
    if (dh === '100%' || dh === '100vh') {
        document.documentElement.style.height = '';
    }
    // Очистить stray inline overflow:hidden на #mainApp и #contentArea
    var mainApp = document.getElementById('mainApp');
    if (mainApp && mainApp.style.overflow === 'hidden') {
        mainApp.style.overflow = '';
    }
    var contentArea = document.getElementById('contentArea');
    if (contentArea && contentArea.style.overflow === 'hidden') {
        contentArea.style.overflow = '';
    }
    if (mainApp) {
        var mh = mainApp.style.height;
        if (mh === '100%' || mh === '100vh') mainApp.style.height = '';
    }
    if (contentArea) {
        var ch = contentArea.style.height;
        if (ch === '100%' || ch === '100vh') contentArea.style.height = '';
    }
}

// Запуск аудита на множестве событий для максимального покрытия
document.addEventListener('visibilitychange', _auditScrollState);
window.addEventListener('focus', _auditScrollState);
document.addEventListener('touchend', _auditScrollState, { passive: true });
document.addEventListener('click', _auditScrollState, { passive: true });
window.addEventListener('popstate', _auditScrollState, { passive: true });

// Периодический аудит на мобильном — раз в 3 секунды
var _scrollAuditTimer = null;
function _startScrollAuditTimer() {
    if (_scrollAuditTimer) clearInterval(_scrollAuditTimer);
    if (!window.matchMedia('(min-width: 1024px)').matches) {
        _scrollAuditTimer = setInterval(_auditScrollState, 3000);
    }
}
_startScrollAuditTimer();
window.matchMedia('(min-width: 1024px)').addEventListener('change', function() {
    _startScrollAuditTimer();
    _auditScrollState();
});

// ======================== СКРЫТИЕ NAV-BAR И СЖАТИЕ ЗАГОЛОВКА ПРИ ПРОКРУТКЕ ========================
(function() {
    let lastScrollY = 0;
    let ticking = false;
    let cooldown = false;
    const COOLDOWN_MS = 150;
    const HIDE_THRESHOLD = 80;
    const RESTORE_RATIO = 0.10;

    function onScroll() {
        if (ticking || cooldown) return;
        ticking = true;
        requestAnimationFrame(function() {
            ticking = false;
            let active = document.querySelector('.page-content.active');
            if (!active || active.id === 'page-dashboard') return;

            let scrollY = window.scrollY || window.pageYOffset;
            let docHeight = document.documentElement.scrollHeight;
            let winHeight = window.innerHeight;
            let isScrolled = active.classList.contains('scrolled');

            if (docHeight <= winHeight + 10) {
                if (isScrolled) {
                    active.classList.remove('scrolled');
                }
                lastScrollY = scrollY;
                return;
            }

            let restoreThreshold = docHeight * RESTORE_RATIO;

            if (!isScrolled && scrollY > lastScrollY && scrollY > HIDE_THRESHOLD) {
                active.classList.add('scrolled');
                let newScrollY = window.scrollY || window.pageYOffset;
                lastScrollY = newScrollY;
                cooldown = true;
                setTimeout(function() { cooldown = false; }, COOLDOWN_MS);
                if (typeof window.fitPageHeaderTitle === 'function') {
                    requestAnimationFrame(window.fitPageHeaderTitle);
                }
            } else if (isScrolled && scrollY < lastScrollY && scrollY <= restoreThreshold) {
                let hasOpenTicket = active.querySelector('.ticket-item.open');
                if (!hasOpenTicket) {
                    active.classList.remove('scrolled');
                    let newScrollY = window.scrollY || window.pageYOffset;
                    lastScrollY = newScrollY;
                    cooldown = true;
                    setTimeout(function() { cooldown = false; }, COOLDOWN_MS);
                    if (typeof window.fitPageHeaderTitle === 'function') {
                        requestAnimationFrame(window.fitPageHeaderTitle);
                    }
                } else {
                    lastScrollY = scrollY;
                }
            } else {
                lastScrollY = scrollY;
            }
        });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
})();

// ======================== АДАПТИВНЫЕ ЗАГОЛОВКИ СТРАНИЦ ========================
(function() {
    const FIT_MIN_FONT = 12;
    const FIT_STEP = 1;
    const FIT_LINE_GAP = 6;

    function _fitOneHeader(header) {
        if (!header) return;
        const title = header.querySelector('.page-inline-header-title');
        if (!title) return;
        if (!header.offsetParent) return;

        title.style.fontSize = '';
        title.style.whiteSpace = '';
        title.style.overflow = '';
        title.style.lineHeight = '';
        header.style.height = '';
        header.style.minHeight = '';

        const titleStyle = getComputedStyle(title);
        const headerStyle = getComputedStyle(header);
        const baseFontSize = parseFloat(titleStyle.fontSize);
        const baseHeight = parseFloat(headerStyle.height);
        if (!isFinite(baseFontSize) || !isFinite(baseHeight)) return;

        title.style.whiteSpace = 'nowrap';
        title.style.overflow = 'hidden';

        const fitsAtBase = title.scrollWidth <= title.clientWidth;

        if (fitsAtBase) {
            title.style.whiteSpace = '';
            title.style.overflow = '';
            return;
        }

        let fontSize = baseFontSize;
        while (fontSize > FIT_MIN_FONT) {
            fontSize -= FIT_STEP;
            title.style.fontSize = fontSize + 'px';
            if (title.scrollWidth <= title.clientWidth) {
                title.style.whiteSpace = '';
                title.style.overflow = '';
                return;
            }
        }

        title.style.whiteSpace = 'normal';
        title.style.overflow = 'hidden';
        title.style.lineHeight = '1.2';

        void title.offsetHeight;

        const titleHeight = title.scrollHeight;
        const titlePadTop = parseFloat(titleStyle.paddingTop) || 0;
        const titlePadBottom = parseFloat(titleStyle.paddingBottom) || 0;
        const requiredTitleHeight = titleHeight + titlePadTop + titlePadBottom;

        const newHeight = Math.max(baseHeight, requiredTitleHeight + FIT_LINE_GAP);
        header.style.height = newHeight + 'px';
        header.style.minHeight = newHeight + 'px';
    }

    function fitPageHeaderTitle() {
        const active = document.querySelector('.page-content.active');
        if (!active) return;
        const header = active.querySelector('.page-inline-header');
        if (!header) return;
        _fitOneHeader(header);
    }

    // Экспортируем в глобальную область для вызова из navigateTo и scroll-handler.
    window.fitPageHeaderTitle = fitPageHeaderTitle;

    let _fitResizeTimer = null;
    function _onFitResize() {
        clearTimeout(_fitResizeTimer);
        _fitResizeTimer = setTimeout(fitPageHeaderTitle, 80);
    }
    window.addEventListener('resize', _onFitResize);
    window.addEventListener('orientationchange', function() {
        setTimeout(fitPageHeaderTitle, 250);
    });
    window.addEventListener('load', function() {
        setTimeout(fitPageHeaderTitle, 200);
    });
})();

// ======================== МАСШТАБИРОВАНИЕ ТЕКСТА ЩИПКОМ ========================
(function() {
    const MIN_SCALE = 1.0;
    const MAX_SCALE = 2.5;
    let pageScales = {};
    let refBlockScales = new WeakMap();

    function applyScale(scale) {
        let active = document.querySelector('.page-content.active');
        if (!active) return;
        let targets = active.querySelectorAll('.pinch-zoom-target');
        targets.forEach(function(el) {
            if (el.classList.contains('ref-info-block')) return;
            let isTicketBody = el.classList.contains('ticket-item-body');
            if (scale > 1.0) {
                if (!el._pzOrigWidth) {
                    el._pzOrigWidth = el.getBoundingClientRect().width;
                }
                el.classList.add('zoomed');
                el.style.zoom = scale;
                if (!isTicketBody) {
                    el.style.width = Math.round(el._pzOrigWidth / scale) + 'px';
                }
            } else {
                el.classList.remove('zoomed');
                el.style.zoom = '';
                if (!isTicketBody) {
                    el.style.width = '';
                }
                el._pzOrigWidth = null;
            }
        });
        pageScales[active.id] = scale;
    }

    function applyRefBlockScale(block, scale) {
        let pageContent = block.closest('.page-content');
        let pageWidth = pageContent ? pageContent.clientWidth : window.innerWidth;
        if (scale > 1.0) {
            if (!block._pzOrigMarginLeft) {
                block._pzOrigMarginLeft = block.style.marginLeft || '';
                block._pzOrigMarginRight = block.style.marginRight || '';
                block._pzOrigMargin = block.classList.contains('scale-form') ? '8px 16px' : '';
            }
            block.classList.add('zoomed');
            block.style.zoom = scale;
            block.style.marginLeft = '0';
            block.style.marginRight = '0';
            block.style.width = Math.round(pageWidth / scale) + 'px';
        } else {
            block.classList.remove('zoomed');
            block.style.zoom = '';
            block.style.width = '';
            if (block._pzOrigMargin) {
                block.style.margin = block._pzOrigMargin;
            } else {
                block.style.marginLeft = block._pzOrigMarginLeft || '';
                block.style.marginRight = block._pzOrigMarginRight || '';
            }
            block._pzOrigMarginLeft = null;
            block._pzOrigMarginRight = null;
            block._pzOrigMargin = null;
        }
        refBlockScales.set(block, scale);
    }

    function resetZoomOnLeave() {
        let active = document.querySelector('.page-content.active');
        if (!active) return;
        let scale = pageScales[active.id];
        if (scale && scale !== 1.0) {
            active.querySelectorAll('.pinch-zoom-target').forEach(function(el) {
                el.style.zoom = '';
                el.style.width = '';
                el._pzOrigWidth = null;
                el.classList.remove('zoomed');
            });
            delete pageScales[active.id];
        }
        active.querySelectorAll('.ref-info-block').forEach(function(el) {
            el.style.zoom = '';
            el.style.width = '';
            if (el._pzOrigMargin) {
                el.style.margin = el._pzOrigMargin;
            } else {
                el.style.marginLeft = '';
                el.style.marginRight = '';
            }
            el._pzOrigMarginLeft = null;
            el._pzOrigMarginRight = null;
            el._pzOrigMargin = null;
            el.classList.remove('zoomed');
            refBlockScales.delete(el);
        });
    }

    function isInZoomZone(el) {
        let current = el;
        while (current) {
            if (current.classList && (current.classList.contains('pinch-zoom-target') || current.classList.contains('ref-info-block'))) return true;
            if (current.classList && current.classList.contains('page-content')) return false;
            current = current.parentElement;
        }
        return false;
    }

    function findRefInfoBlock(el) {
        let current = el;
        while (current) {
            if (current.classList && current.classList.contains('ref-info-block')) return current;
            if (current.classList && current.classList.contains('page-content')) return null;
            current = current.parentElement;
        }
        return null;
    }

    let initialDistance = 0;
    let initialScale = 1.0;
    let isPinching = false;
    let pinchTarget = null;
    let pinchRefBlock = null;

    function getDistance(touch1, touch2) {
        let dx = touch1.clientX - touch2.clientX;
        let dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    document.addEventListener('touchstart', function(e) {
        if (e.touches.length === 2) {
            let inZone1 = isInZoomZone(e.touches[0].target);
            let inZone2 = isInZoomZone(e.touches[1].target);
            if (inZone1 || inZone2) {
                isPinching = true;
                initialDistance = getDistance(e.touches[0], e.touches[1]);
                e.preventDefault();

                let refBlock1 = findRefInfoBlock(e.touches[0].target);
                let refBlock2 = findRefInfoBlock(e.touches[1].target);
                if (refBlock1 && refBlock1 === refBlock2) {
                    pinchTarget = 'ref-block';
                    pinchRefBlock = refBlock1;
                    initialScale = refBlockScales.has(refBlock1) ? refBlockScales.get(refBlock1) : 1.0;
                } else {
                    pinchTarget = 'page';
                    pinchRefBlock = null;
                    let active = document.querySelector('.page-content.active');
                    initialScale = (active && pageScales[active.id]) ? pageScales[active.id] : 1.0;
                }
            }
        }
    }, { passive: false });

    document.addEventListener('touchmove', function(e) {
        if (!isPinching || e.touches.length !== 2) return;
        e.preventDefault();
        let currentDistance = getDistance(e.touches[0], e.touches[1]);
        let ratio = currentDistance / initialDistance;
        let newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, initialScale * ratio));
        if (pinchTarget === 'ref-block' && pinchRefBlock) {
            applyRefBlockScale(pinchRefBlock, newScale);
        } else {
            applyScale(newScale);
        }
    }, { passive: false });

    document.addEventListener('touchend', function(e) {
        if (isPinching && e.touches.length < 2) {
            isPinching = false;
            pinchTarget = null;
            pinchRefBlock = null;
        }
    });

    // iOS Safari gesture events
    document.addEventListener('gesturestart', function(e) {
        if (!isInZoomZone(e.target)) return;
        e.preventDefault();
        isPinching = true;

        let refBlock = findRefInfoBlock(e.target);
        if (refBlock) {
            pinchTarget = 'ref-block';
            pinchRefBlock = refBlock;
            initialScale = refBlockScales.has(refBlock) ? refBlockScales.get(refBlock) : 1.0;
        } else {
            pinchTarget = 'page';
            pinchRefBlock = null;
            let active = document.querySelector('.page-content.active');
            initialScale = (active && pageScales[active.id]) ? pageScales[active.id] : 1.0;
        }
    }, { passive: false });

    document.addEventListener('gesturechange', function(e) {
        if (!isPinching) return;
        e.preventDefault();
        let newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, initialScale * e.scale));
        if (pinchTarget === 'ref-block' && pinchRefBlock) {
            applyRefBlockScale(pinchRefBlock, newScale);
        } else {
            applyScale(newScale);
        }
    }, { passive: false });

    document.addEventListener('gestureend', function() {
        isPinching = false;
        pinchTarget = null;
        pinchRefBlock = null;
    });

    // Экспортируем resetZoomOnLeave в глобальную область для использования
    // в app.js (pinch-zoom wrapper around navigateTo).
    window.resetZoomOnLeave = resetZoomOnLeave;

    // NOTE: The pinch-zoom navigateTo wrapper is applied in app.js
    // AFTER navigateTo is placed on window. This module runs before
    // that, so the wrapper here would capture undefined. Removed.

    // Назначить класс pinch-zoom-target нужным элементам
    function assignPinchZoomTargets() {
        document.querySelectorAll('[id^="conv-"][id$="-table"]').forEach(function(el) {
            if (el.classList.contains('pinch-zoom-target')) return;
            let tableWrapper = el.querySelector('div[style*="overflow-x"]');
            if (tableWrapper && tableWrapper.querySelector('table')) {
                if (!tableWrapper.classList.contains('pinch-zoom-target')) {
                    tableWrapper.classList.add('pinch-zoom-target');
                }
            } else if (el.querySelector('table')) {
                el.classList.add('pinch-zoom-target');
            }
        });

        document.querySelectorAll('#scaleTableContainer, #buoyTableContainer, #wsTableContainer, #tempTableContainer').forEach(function(el) {
            if (!el.classList.contains('pinch-zoom-target')) el.classList.add('pinch-zoom-target');
        });

        document.querySelectorAll('.converter-result-group').forEach(function(el) {
            if (el.classList.contains('pinch-zoom-target')) return;
            if (el.querySelector('.pinch-zoom-target')) return;
            if (el.querySelector('table')) {
                let tableWrapper = el.querySelector('div[style*="overflow-x"]');
                if (tableWrapper && tableWrapper.querySelector('table')) {
                    if (!tableWrapper.classList.contains('pinch-zoom-target')) {
                        tableWrapper.classList.add('pinch-zoom-target');
                    }
                } else {
                    el.classList.add('pinch-zoom-target');
                }
            }
        });

        document.querySelectorAll('.page-content div[style]').forEach(function(div) {
            if (div.classList.contains('ref-info-block')) return;
            if (div.querySelector('.ref-info-block')) return;
            if (div.style.background && div.querySelector('span')) {
                let spans = div.querySelectorAll('span');
                for (let s of spans) {
                    if (s.textContent && s.textContent.trim() === 'Справочная информация') {
                        div.classList.add('ref-info-block');
                        break;
                    }
                }
            }
        });
        document.querySelectorAll('.page-content .scale-form').forEach(function(div) {
            if (div.classList.contains('ref-info-block')) return;
            let headerDiv = div.querySelector('div[style*="font-size:13px"]');
            if (headerDiv && headerDiv.textContent && headerDiv.textContent.trim() === 'Справочная информация') {
                div.classList.add('ref-info-block');
            }
        });

        document.querySelectorAll('.ticket-item-body').forEach(function(el) {
            if (!el.classList.contains('pinch-zoom-target')) el.classList.add('pinch-zoom-target');
        });

        document.querySelectorAll('.page-content table').forEach(function(table) {
            let parent = table.closest('.pinch-zoom-target');
            if (parent) return;
            let refParent = table.closest('.ref-info-block');
            if (refParent) return;
            let wrapper = table.parentElement;
            while (wrapper && !wrapper.classList.contains('page-content')) {
                if (wrapper.style && wrapper.style.overflowX === 'auto') {
                    if (!wrapper.classList.contains('pinch-zoom-target')) {
                        wrapper.classList.add('pinch-zoom-target');
                    }
                    return;
                }
                wrapper = wrapper.parentElement;
            }
            if (!table.classList.contains('pinch-zoom-target')) {
                table.classList.add('pinch-zoom-target');
            }
        });

        document.querySelectorAll('.ref-info-block').forEach(function(block) {
            if (block.dataset.refCollapsibleInit) return;
            let header = null;
            let content = null;
            let children = block.children;
            for (let i = 0; i < children.length; i++) {
                let child = children[i];
                if (child.tagName !== 'DIV') continue;
                if (!header) {
                    let span = child.querySelector('span');
                    if (span && span.textContent && span.textContent.trim() === 'Справочная информация') {
                        header = child;
                        continue;
                    }
                }
                if (header && !content) {
                    content = child;
                    break;
                }
            }
            if (!header || !content) return;
            block.dataset.refCollapsibleInit = 'true';
            block.classList.add('ref-info-collapsible', 'ref-info-collapsed');
            header.classList.add('ref-info-header');
            content.classList.add('ref-info-content');
            if (!header.querySelector('.ref-info-chevron')) {
                let chevron = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                chevron.setAttribute('class', 'ref-info-chevron');
                chevron.setAttribute('viewBox', '0 0 24 24');
                chevron.setAttribute('fill', 'none');
                let poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
                poly.setAttribute('points', '6 9 12 15 18 9');
                chevron.appendChild(poly);
                header.appendChild(chevron);
            }
            header.addEventListener('click', function(e) {
                e.stopPropagation();
                block.classList.toggle('ref-info-collapsed');
                if (navigator.vibrate) navigator.vibrate(15);
            });
        });
    }

    let assignTimeout = null;
    function scheduleAssignPinchZoomTargets() {
        if (assignTimeout) return;
        assignTimeout = setTimeout(function() {
            assignTimeout = null;
            assignPinchZoomTargets();
        }, 300);
    }

    function initPinchZoomTargets() {
        assignPinchZoomTargets();
        let observer = new MutationObserver(function(mutations) {
            for (let m of mutations) {
                if (m.addedNodes.length) {
                    for (let node of m.addedNodes) {
                        if (node.nodeType === 1) {
                            scheduleAssignPinchZoomTargets();
                            return;
                        }
                    }
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPinchZoomTargets);
    } else {
        initPinchZoomTargets();
    }
})();

// ============================================================
// Exports
// ============================================================
export {
    _auditScrollState,
    _scrollAuditTimer,
    _startScrollAuditTimer
};
