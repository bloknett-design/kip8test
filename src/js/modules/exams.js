/**
 * @module modules/exams
 * @description Exam tickets system — loading, rendering, navigation, image preview.
 * Extracted from the monolithic src/index.html (lines 8535–9217).
 */

// ============================================================
// Экзаменационные билеты
// ============================================================
let _ticketsData = null;
// Уникальный параметр для cache-busting на одну сессию.
// Меняется при каждой полной перезагрузке страницы, поэтому
// браузер и SW всегда тянут свежий JSON при новом открытии приложения.
const _ticketsCacheBust = 't' + Date.now();
const TICKET_IDS = ['tickets-4', 'tickets-5', 'tickets-6', 'tickets-1000v'];
// Кэш групп билетов для мастер-детали на десктопе
let _ticketGroupsCache = {};
let _ticketSelectedIndex = -1;

async function loadTicketsData(force) {
    // In-memory кэш на одну сессию — чтобы не дёргать сервер
    // при каждом переходе на страницу билетов.
    // force=true — принудительно обновить (например, после обновления SW).
    if (_ticketsData && !force) return _ticketsData;

    // ===== STALE-WHILE-REVALIDATE для JSON =====
    // Сначала пробуем прочитать закэшированный SW ответ (мгновенно).
    // Если есть — используем как initial data и параллельно запускаем
    // фоновое обновление из сети. Это позволяет повторно открывать
    // приложение мгновенно, без ожидания сети.
    if (!force && 'caches' in window) {
        try {
            // SW кэширует JSON по нормализованному ключу (без ?v=...).
            // caches.match() с URL без query найдёт закэшированную запись.
            const cached = await caches.match('data/exam-tickets.json');
            if (cached) {
                _ticketsData = await cached.json();
                _updateTicketBadges();
                // Фоновое обновление (не блокирует return)
                _refreshTicketsInBackground();
                // Запускаем pre-cache картинок (он сам проверит, что уже закэшировано)
                try { precacheTicketImages(); } catch (e) { console.warn('[precache] Ошибка запуска:', e); }
                return _ticketsData;
            }
        } catch (e) {
            console.warn('[tickets] Чтение из SW cache не удалось, fallback на fetch:', e);
        }
    }

    // ===== Обычная загрузка из сети (первый запуск или force) =====
    try {
        const url = 'data/exam-tickets.json?v=' + encodeURIComponent(_ticketsCacheBust);
        const r = await fetch(url);
        if (!r.ok) throw new Error(r.status);
        _ticketsData = await r.json();
        _updateTicketBadges();
        // Фоновый pre-cache картинок для офлайн-просмотра.
        try { precacheTicketImages(); } catch (e) { console.warn('[precache] Ошибка запуска:', e); }
        return _ticketsData;
    } catch (e) {
        console.error('Ошибка загрузки билетов:', e);
        return _ticketsData; // вернуть предыдущие данные, если есть
    }
}

// Обновить бейджи с количеством вопросов на главной странице билетов
function _updateTicketBadges() {
    if (!_ticketsData) return;
    for (const id of TICKET_IDS) {
        const cat = _ticketsData[id];
        if (!cat) continue;
        const badgeId = id.replace('tickets-', 'badge-');
        const badge = document.getElementById(badgeId);
        if (badge) badge.textContent = cat.total + ' вопр.';
    }
}

// Фоновое обновление JSON билетов из сети (stale-while-revalidate).
// Тихо: если сеть недоступна — ничего не делаем, у нас уже есть кэш.
// Если данные изменились — обновляем in-memory кэш и бейджи.
let _bgRefreshInFlight = false;
async function _refreshTicketsInBackground() {
    if (_bgRefreshInFlight) return;
    _bgRefreshInFlight = true;
    try {
        const url = 'data/exam-tickets.json?v=' + encodeURIComponent(_ticketsCacheBust);
        const r = await fetch(url);
        if (!r.ok) return;
        const fresh = await r.json();
        // Сравнить с текущими данными (простое сравнение строк)
        if (_ticketsData && JSON.stringify(fresh) !== JSON.stringify(_ticketsData)) {
            _ticketsData = fresh;
            _updateTicketBadges();
            console.log('[tickets] Данные обновлены в фоне');
            // Если активна страница билетов — перерисовать
            const active = document.querySelector('.page-content.active');
            if (active && active.id && active.id.indexOf('page-tickets-') === 0) {
                renderTickets(active.id.replace('page-', ''), '');
            }
        }
    } catch (e) {
        // Сеть недоступна — тихо игнорируем, у нас уже есть кэш
    } finally {
        _bgRefreshInFlight = false;
    }
}

// Вспомогательная функция: HTML вопросов/ответов одного билета
// Используется и в мобильном аккордеоне, и в десктопном detail-panel
function _renderTicketQuestionsHtml(questions, ti) {
    let html = '';
    for (const q of questions) {
        html += '<div class="ticket-q">';
        html += '<div class="ticket-q-num">' + escHtml(getField(q, 'question_number', '\u2116 \u0432\u043e\u043f\u0440\u043e\u0441\u0430')) + '</div>';
        html += '<div class="ticket-q-text">' + escHtml(getField(q, 'question', '\u0412\u043e\u043f\u0440\u043e\u0441')) + '</div>';
        const answer = getField(q, 'answer', '\u041e\u0442\u0432\u0435\u0442');
        const imgSrc = getField(q, 'image_url', 'Image').trim();
        const hasImage = isWorkingUrl(imgSrc);
        const hasAnswer = !!answer;
        html += '<div class="ticket-a-label">Ответ</div>';
        if (hasImage) {
            const imgId = 'timg_' + ti + '_' + (getField(q, 'id', 'ID') || Math.random().toString(36).slice(2,8));
            const gdrive = gdriveShareToDirect(imgSrc);
            let thumbSrc, fullSrc;
            if (gdrive) { thumbSrc = gdrive.thumb; fullSrc = gdrive.full; }
            else { thumbSrc = imgSrc; fullSrc = imgSrc; }
            html += '<div class="ticket-a-img-wrap" id="' + imgId + '_wrap" data-img-src="' + escHtml(fullSrc) + '">';
            html += '<img class="ticket-a-img" id="' + imgId + '" src="' + escHtml(thumbSrc) + '" data-full-src="' + escHtml(fullSrc) + '" alt="Схема" loading="lazy" referrerpolicy="no-referrer" onclick="openTicketImage(this)" onerror="ticketImgFail(\'' + imgId + '\')" onload="ticketImgOk(\'' + imgId + '\')">';
            html += '<a class="ticket-a-imglink" href="' + escHtml(imgSrc) + '" target="_blank" rel="noopener">';
            html += '<svg class="ticket-a-imglink-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';
            html += '<span class="ticket-a-imglink-text">Открыть изображение</span>';
            html += '<svg class="ticket-a-imglink-ext" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>';
            html += '</a></div>';
        }
        if (hasAnswer) {
            html += '<div class="ticket-a-text">' + escHtml(answer) + '</div>';
        } else if (!hasImage) {
            html += '<div class="ticket-a-text" style="color:rgba(255,255,255,0.35);font-style:italic;">Ответ временно отсутствует</div>';
        }
        const ref = getField(q, 'literature_name', '\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u043b\u0438\u0442\u0435\u0440\u0430\u0442\u0443\u0440\u044b');
        const fileUrl = getField(q, 'file_url', '\u0424\u0430\u0439\u043b').trim();
        if (ref) {
            if (isWorkingUrl(fileUrl)) {
                html += '<div class="ticket-ref"><a class="ticket-ref-link" href="' + escHtml(fileUrl) + '" target="_blank" rel="noopener">' + escHtml(ref) + '</a></div>';
            } else {
                html += '<div class="ticket-ref"><span class="ticket-ref-link">' + escHtml(ref) + '</span></div>';
            }
        }
        html += '<div class="ticket-q-divider"><svg viewBox="0 0 400 16" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet"><line x1="0" y1="8" x2="400" y2="8" stroke="currentColor" stroke-width="0.5" opacity="0.45"/><g stroke="currentColor" stroke-width="0.8" fill="none"><rect x="7.11" y="5.5" width="8" height="5" rx="1"/><rect x="29.33" y="5.5" width="8" height="5" rx="1"/><rect x="51.56" y="5.5" width="8" height="5" rx="1"/><rect x="73.78" y="5.5" width="8" height="5" rx="1"/><rect x="96" y="5.5" width="8" height="5" rx="1"/><rect x="118.22" y="5.5" width="8" height="5" rx="1"/><rect x="140.44" y="5.5" width="8" height="5" rx="1"/><rect x="162.67" y="5.5" width="8" height="5" rx="1"/><rect x="184.89" y="5.5" width="8" height="5" rx="1"/><rect x="207.11" y="5.5" width="8" height="5" rx="1"/><rect x="229.33" y="5.5" width="8" height="5" rx="1"/><rect x="251.56" y="5.5" width="8" height="5" rx="1"/><rect x="273.78" y="5.5" width="8" height="5" rx="1"/><rect x="296" y="5.5" width="8" height="5" rx="1"/><rect x="318.22" y="5.5" width="8" height="5" rx="1"/><rect x="340.44" y="5.5" width="8" height="5" rx="1"/><rect x="362.67" y="5.5" width="8" height="5" rx="1"/><rect x="384.89" y="5.5" width="8" height="5" rx="1"/></g></svg></div>';
        html += '</div>';
    }
    return html;
}

function renderTickets(catId, filter) {
    const container = document.getElementById('tickets-container-' + catId);
    if (!container || !_ticketsData) return;
    const cat = _ticketsData[catId];
    if (!cat) { container.innerHTML = '<div class="ticket-empty">Данные не найдены</div>'; return; }

    // Группировка по номеру билета
    const groups = {};
    for (const row of cat.rows) {
        const key = getField(row, 'ticket_number', '\u2116 \u0431\u0438\u043b\u0435\u0442\u0430') || 'Билет';
        if (!groups[key]) groups[key] = [];
        groups[key].push(row);
    }

    // Кэшируем группы для мастер-детали
    _ticketGroupsCache[catId] = groups;
    const ticketKeys = Object.keys(groups);
    const lowerFilter = (filter || '').toLowerCase();

    // === Десктоп: компактный список (мастер-деталь) ===
    if (window.isDesktop()) {
        let html = '<div class="ticket-master-list">';
        for (let ti = 0; ti < ticketKeys.length; ti++) {
            const ticketNum = ticketKeys[ti];
            const questions = groups[ticketNum];
            let filtered = questions;
            if (lowerFilter) {
                filtered = questions.filter(q =>
                    getField(q, 'question', '\u0412\u043e\u043f\u0440\u043e\u0441').toLowerCase().includes(lowerFilter) ||
                    getField(q, 'answer', '\u041e\u0442\u0432\u0435\u0442').toLowerCase().includes(lowerFilter) ||
                    getField(q, 'question_number', '\u2116 \u0432\u043e\u043f\u0440\u043e\u0441\u0430').toLowerCase().includes(lowerFilter)
                );
                if (filtered.length === 0) continue;
            }
            html += '<div class="ticket-list-item" data-ticket-index="' + ti + '" onclick="ticketSelectItem(\'' + catId + '\',' + ti + ')">';
            html += '<span class="ticket-list-item-num">' + escHtml(ticketNum) + '</span>';
            html += '<span class="ticket-list-item-count">' + filtered.length + ' вопр.</span>';
            html += '</div>';
        }
        html += '</div>';
        container.innerHTML = html || '<div class="ticket-empty">Ничего не найдено</div>';
        // Если был выбран билет — восстановить подсветку
        if (_ticketSelectedIndex >= 0) {
            const sel = container.querySelector('.ticket-list-item[data-ticket-index="' + _ticketSelectedIndex + '"]');
            if (sel) sel.classList.add('detail-highlight');
        }
        return;
    }

    // === Мобильный: аккордеон (прежнее поведение) ===
    let html = '';
    for (let ti = 0; ti < ticketKeys.length; ti++) {
        const ticketNum = ticketKeys[ti];
        const questions = groups[ticketNum];
        let filtered = questions;
        if (lowerFilter) {
            filtered = questions.filter(q =>
                getField(q, 'question', '\u0412\u043e\u043f\u0440\u043e\u0441').toLowerCase().includes(lowerFilter) ||
                getField(q, 'answer', '\u041e\u0442\u0432\u0435\u0442').toLowerCase().includes(lowerFilter) ||
                getField(q, 'question_number', '\u2116 \u0432\u043e\u043f\u0440\u043e\u0441\u0430').toLowerCase().includes(lowerFilter)
            );
            if (filtered.length === 0) continue;
        }

        html += '<div class="ticket-item" data-ticket-index="' + ti + '">';
        html += '<div class="ticket-item-header" onclick="toggleTicketItem(this.parentElement)">';
        html += '<span class="ticket-item-num">' + ticketNum + '</span>';
        html += '<span style="display:flex;align-items:center;gap:8px;"><span class="ticket-item-count">' + filtered.length + ' вопр.</span>';
        html += '<svg class="ticket-item-chevron" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg></span>';
        html += '</div>';
        html += '<div class="ticket-item-body">';
        html += _renderTicketQuestionsHtml(filtered, ti);
        html += '</div>'; // конец ticket-item-body

        // Навигация между билетами
        const hasPrev = ti > 0;
        const hasNext = ti < ticketKeys.length - 1;
        if (hasPrev || hasNext) {
            html += '<div class="ticket-nav-bar">';
            if (hasPrev) {
                const prevTitle = ticketKeys[ti - 1];
                html += '<div class="ticket-nav-btn ticket-nav-prev" onclick="goToTicket(' + (ti - 1) + ')">';
                html += '<svg class="ticket-nav-chevron" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>';
                html += '<div><div class="ticket-next-label">Предыдущий</div><div class="ticket-next-title">' + escHtml(prevTitle) + '</div></div>';
                html += '</div>';
            }
            if (hasNext) {
                const nextTitle = ticketKeys[ti + 1];
                html += '<div class="ticket-nav-btn ticket-nav-next" onclick="goToTicket(' + (ti + 1) + ')">';
                html += '<div><div class="ticket-next-label">Следующий</div><div class="ticket-next-title">' + escHtml(nextTitle) + '</div></div>';
                html += '<svg class="ticket-nav-chevron" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>';
                html += '</div>';
            }
            html += '</div>';
        }
        html += '</div>'; // конец ticket-item
    }

    container.innerHTML = html || '<div class="ticket-empty">Ничего не найдено</div>';

    // Таймауты для превью картинок
    if (html) {
        const imgs = container.querySelectorAll('.ticket-a-img');
        imgs.forEach(function(img) {
            if (img.complete && img.naturalWidth > 0) return;
            if (img.closest('.ticket-a-img-wrap').classList.contains('img-failed')) return;
            setTimeout(function() {
                if (!img.complete || img.naturalWidth === 0) {
                    ticketImgFail(img.id);
                }
            }, 8000);
        });
    }
}

// Клик по билету в десктопном списке — открыть detail-panel
function ticketSelectItem(catId, ti) {
    _ticketSelectedIndex = ti;
    const groups = _ticketGroupsCache[catId];
    if (!groups) return;
    const ticketKeys = Object.keys(groups);
    if (ti < 0 || ti >= ticketKeys.length) return;
    const ticketNum = ticketKeys[ti];
    const questions = groups[ticketNum];

    // Подсветка в списке
    const container = document.getElementById('tickets-container-' + catId);
    if (container) {
        container.querySelectorAll('.ticket-list-item.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
        const sel = container.querySelector('.ticket-list-item[data-ticket-index="' + ti + '"]');
        if (sel) { sel.classList.add('detail-highlight'); sel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
    }

    // Рендер в detail-panel
    const bodyEl = document.getElementById('detailPanelBody');
    if (!bodyEl) return;
    let html = '<div class="ticket-detail-card">';
    html += '<div class="ticket-detail-title">' + escHtml(ticketNum) + '</div>';
    html += _renderTicketQuestionsHtml(questions, ti);
    // Навигация между билетами
    const hasPrev = ti > 0;
    const hasNext = ti < ticketKeys.length - 1;
    if (hasPrev || hasNext) {
        html += '<div class="ticket-detail-nav">';
        if (hasPrev) {
            html += '<div class="ticket-detail-nav-btn" onclick="ticketSelectItem(\'' + catId + '\',' + (ti - 1) + ')" style="justify-content:flex-start;gap:10px;border-right:1px solid var(--card-border);">';
            html += '<svg class="ticket-nav-chevron" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>';
            html += '<div><div class="ticket-next-label">Предыдущий</div><div class="ticket-next-title">' + escHtml(ticketKeys[ti - 1]) + '</div></div>';
            html += '</div>';
        }
        if (hasNext) {
            html += '<div class="ticket-detail-nav-btn" onclick="ticketSelectItem(\'' + catId + '\',' + (ti + 1) + ')" style="justify-content:flex-end;gap:10px;text-align:right;">';
            html += '<div><div class="ticket-next-label">Следующий</div><div class="ticket-next-title">' + escHtml(ticketKeys[ti + 1]) + '</div></div>';
            html += '<svg class="ticket-nav-chevron" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>';
            html += '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    bodyEl.innerHTML = html;

    // Открыть панель
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');

    // Breadcrumbs
    const pageNames = { 'tickets-1000v': 'Билеты до 1000 В', 'tickets-4': 'Билеты на 4 разряд', 'tickets-5': 'Билеты на 5 разряд', 'tickets-6': 'Билеты на 6 разряд' };
    const catName = pageNames[catId] || 'Билеты';
    if (typeof window.setDetailBreadcrumb === 'function') {
        window.setDetailBreadcrumb('ticket-detail', ticketNum, catName, catId);
    }

    // Таймауты для картинок в detail-панели
    const imgs = bodyEl.querySelectorAll('.ticket-a-img');
    imgs.forEach(function(img) {
        if (img.complete && img.naturalWidth > 0) return;
        setTimeout(function() { if (!img.complete || img.naturalWidth === 0) ticketImgFail(img.id); }, 8000);
    });

    // Прокрутить панель наверх
    bodyEl.scrollTop = 0;
}

// Рендер билета в detail-panel при навигации (для десктопа)
function ticketRenderDetailInPanel() {
    const catId = window._ticketDetailCatId;
    const ti = window._ticketDetailIndex || 0;
    if (!catId) return;
    ticketSelectItem(catId, ti);
}

// Картика загрузилась успешно — убрать таймаут, оставить <img> видимым
function ticketImgOk(imgId) {
    const img = document.getElementById(imgId);
    if (!img) return;
    const wrap = img.closest('.ticket-a-img-wrap');
    if (wrap) wrap.classList.remove('img-failed');
}

// Картика не загрузилась (onerror или таймаут) — показать fallback-карточку
function ticketImgFail(imgId) {
    const img = document.getElementById(imgId);
    if (!img) return;
    const wrap = img.closest('.ticket-a-img-wrap');
    if (wrap) wrap.classList.add('img-failed');
}

// Полноэкранный просмотр картинки билета
function openTicketImage(imgEl) {
    // Создать overlay для полноэкранного просмотра
    let overlay = document.getElementById('ticket-img-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'ticket-img-overlay';
        overlay.className = 'ticket-img-overlay';
        // Клик по фону (но не по картинке) — закрывает overlay
        overlay.setAttribute('onclick', 'if(event.target===this)closeTicketImage()');
        overlay.innerHTML = '<div class="ticket-img-overlay-close" onclick="closeTicketImage()">&times;</div><div class="ticket-img-overlay-content"><img id="ticket-img-overlay-full" src="" alt="" referrerpolicy="no-referrer" onclick="event.stopPropagation()"></div><div class="ticket-img-overlay-hint">Нажмите × или свайпните вниз, чтобы закрыть</div>';
        document.body.appendChild(overlay);
        // Жесты для закрытия на мобильных — свайп вниз
        let startY = 0, currentY = 0, swiping = false;
        overlay.addEventListener('touchstart', function(e) {
            if (e.touches.length === 1) {
                startY = e.touches[0].clientY;
                swiping = true;
            }
        }, { passive: true });
        overlay.addEventListener('touchmove', function(e) {
            if (swiping && e.touches.length === 1) {
                currentY = e.touches[0].clientY;
                const dy = currentY - startY;
                if (dy > 0) {
                    overlay.style.background = 'rgba(0,0,0,' + Math.max(0.4, 0.92 - dy / 500) + ')';
                }
            }
        }, { passive: true });
        overlay.addEventListener('touchend', function(e) {
            if (swiping) {
                const dy = currentY - startY;
                if (dy > 80) {
                    closeTicketImage();
                }
                overlay.style.background = '';
            }
            swiping = false;
            startY = currentY = 0;
        }, { passive: true });
    }
    const fullImg = document.getElementById('ticket-img-overlay-full');
    // Используем полный размер если есть data-full-src (Google Drive full-res),
    // иначе тот же src что и у превью.
    const fullSrc = imgEl.getAttribute('data-full-src') || imgEl.src;
    fullImg.src = fullSrc;
    overlay.classList.add('active');
    document.body.classList.add('ticket-img-viewing');
}

function closeTicketImage() {
    const overlay = document.getElementById('ticket-img-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
    document.body.classList.remove('ticket-img-viewing');
}

// Закрытие overlay картинки по клавише Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeTicketImage();
});

function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// Утилита для чтения поля билета с обратной совместимостью.
// В JSON данные могут храниться под новыми латинскими именами
// (ticket_number, question, answer, image_url, ...) или под
// старыми русскими (№ билета, Вопрос, Ответ, Image, ...).
// Эта функция сначала ищет новое имя, при отсутствии — старое.
// Позволяет плавно мигрировать на новую схему имён.
function getField(obj, newName, oldName) {
    if (!obj) return '';
    if (obj[newName] !== undefined) return obj[newName] || '';
    if (oldName && obj[oldName] !== undefined) return obj[oldName] || '';
    return '';
}

// Проверка, что значение ячейки является рабочей ссылкой.
// ЕДИНЫЙ ПРИНЦИП: картинки в билетах загружаются ТОЛЬКО по URL
// из столбца Image Excel-таблицы (http:// или https://).
// Поддерживаемые источники:
//   - Google Drive share-ссылка (конвертируется в прямой URL через
//     gdriveShareToDirect() ниже).
//   - Прямая HTTPS-ссылка на PNG/JPG/WebP.
// Локальные пути (images/..., library/...), относительные пути
// и пустые ячейки НЕ считаются рабочей ссылкой — картинка просто
// не вставляется. Это гарантирует, что все картинки в билетах
// управляются исключительно содержимым столбца Image в Excel.
function isWorkingUrl(s) {
    if (!s) return false;
    const str = String(s).trim();
    if (!str) return false;
    return /^https?:\/\/[^\s\/]+(\/\S*)?$/i.test(str);
}

// Конвертация Google Drive share-ссылки в прямые URL картинки.
// Google Drive share-ссылка: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
// Возвращает { fileId, thumb, full, share } или null, если ссылка не Google Drive.
//   thumb — уменьшенная копия для превью (drive.google.com/thumbnail?id=...&sz=w800)
//   full  — полный размер через lh3.googleusercontent.com/d/FILE_ID
//   share — оригинальная share-ссылка (для fallback в новую вкладку)
// Для публичных файлов (Anyone with the link) оба URL отдают PNG/JPG напрямую.
function gdriveShareToDirect(shareUrl) {
    if (!shareUrl) return null;
    const str = String(shareUrl).trim();
    if (!/drive\.google\.com/i.test(str)) return null;
    let fileId = null;
    let m = str.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
    if (m) fileId = m[1];
    if (!fileId) {
        m = str.match(/[?&]id=([a-zA-Z0-9_-]+)/);
        if (m) fileId = m[1];
    }
    if (!fileId) return null;
    return {
        fileId: fileId,
        thumb: 'https://drive.google.com/thumbnail?id=' + fileId + '&sz=w800',
        full: 'https://lh3.googleusercontent.com/d/' + fileId,
        share: str
    };
}

// === Фоновый pre-cache картинок билетов для офлайн-просмотра ===
// После загрузки exam-tickets.json фоном, через requestIdleCallback, скачиваем
// все картинки билетов (превью + полный размер). SW перехватывает эти запросы
// (ветка 2 в sw.js) и кэширует opaque responses. После этого картинки доступны
// офлайн без необходимости открывать каждый билет вручную.
//
// Параметры:
//   - параллельность = 3 (чтобы не перегружать сеть и не блокировать UI)
//   - запросы с mode:'no-cors' (как у <img>) → opaque responses, кэшируются SW
//   - запускается через requestIdleCallback, чтобы не мешать основной работе
//   - ошибки игнорируются — это фоновая задача, не блокирующая UI
let _precacheStarted = false;
function precacheTicketImages() {
    if (_precacheStarted) return; // защита от повторного запуска
    if (!('caches' in window) || !navigator.serviceWorker) return; // нет поддержки SW
    if (!_ticketsData) return;
    _precacheStarted = true;

    // Собираем уникальные URL картинок из всех 4 категорий билетов
    const urls = new Set();
    for (const catId of TICKET_IDS) {
        const cat = _ticketsData[catId];
        if (!cat || !Array.isArray(cat.rows)) continue;
        for (const row of cat.rows) {
            const imgUrl = (getField(row, 'image_url', 'Image') || '').trim();
            if (!isWorkingUrl(imgUrl)) continue;
            const gdrive = gdriveShareToDirect(imgUrl);
            if (gdrive) {
                urls.add(gdrive.thumb);  // превью
                urls.add(gdrive.full);   // полный размер
            } else {
                // Прямой HTTPS-URL картинки — кэшируем как есть.
                urls.add(imgUrl);
            }
        }
    }
    if (urls.size === 0) {
        console.log('[precache] Нет картинок для кэширования');
        return;
    }
    console.log('[precache] Запланирована загрузка ' + urls.size + ' картинок для офлайна');

    // Очередь с параллельностью 3
    const queue = Array.from(urls);
    let idx = 0;
    let inFlight = 0;
    let done = 0;
    let failed = 0;

    function scheduleNext() {
        // Запускаем следующий запрос через requestIdleCallback
        if ('requestIdleCallback' in window) {
            requestIdleCallback(fetchNext);
        } else {
            setTimeout(fetchNext, 50);
        }
    }

    function fetchNext() {
        if (idx >= queue.length) {
            if (inFlight === 0) {
                console.log('[precache] Завершено: ' + done + ' OK, ' + failed + ' ошибок из ' + queue.length);
            }
            return;
        }
        const url = queue[idx++];
        inFlight++;
        // mode:'no-cors' — как у <img>. SW получит opaque response и закэширует.
        // cache:'no-store' — не используем HTTP-кэш браузера, только SW Cache API.
        fetch(url, { mode: 'no-cors', cache: 'no-store' })
            .then(() => { done++; })
            .catch(() => { failed++; })
            .finally(() => {
                inFlight--;
                if (idx < queue.length) {
                    scheduleNext(); // запустить следующий (заполняет освободившийся слот)
                } else if (inFlight === 0) {
                    console.log('[precache] Завершено: ' + done + ' OK, ' + failed + ' ошибок из ' + queue.length);
                }
            });
    }

    // Старт: запускаем 3 параллельных запроса (или меньше, если картинок меньше)
    const initialBatch = Math.min(3, queue.length);
    for (let i = 0; i < initialBatch; i++) {
        if ('requestIdleCallback' in window) {
            requestIdleCallback(fetchNext);
        } else {
            setTimeout(fetchNext, 100 + i * 50);
        }
    }
}

// Запомненная позиция прокрутки для восстановления при закрытии билета
let _savedScrollY = 0;

// Запомненное состояние scrolled для корректного восстановления
let _wasPageScrolled = false;

function toggleTicketItem(el) {
    const wasOpen = el.classList.contains('open');
    // Закрыть все открытые билеты в этом контейнере
    el.parentElement.querySelectorAll('.ticket-item.open').forEach(item => {
        item.classList.remove('open');
        item.querySelector('.ticket-item-body').scrollTop = 0;
    });
    const page = el.closest('.page-content');

    // Если кликнутый не был открыт — открыть
    if (!wasOpen) {
        el.classList.add('open');
        // Заблокировать прокрутку страницы
        _savedScrollY = window.scrollY || window.pageYOffset;
        // Запомнить, была ли страница уже в состоянии scrolled
        _wasPageScrolled = page ? page.classList.contains('scrolled') : false;
        document.body.classList.add('ticket-open');
        // На десктопе: position:fixed + top для iOS scroll-lock паттерна
        // На мобильном: CSS через html:has(body.ticket-open) блокирует прокрутку на html
        // body остаётся overflow:visible (не создаёт scroll-контейнер)
        if (window.isDesktop()) {
            document.body.style.top = '-' + _savedScrollY + 'px';
        }
        // Скрыть nav-bar и сжать заголовок страницы (как при прокрутке вниз)
        if (page && !page.classList.contains('scrolled')) {
            page.classList.add('scrolled');
        }
    } else {
        // Билет закрыт — разблокировать прокрутку страницы
        document.body.classList.remove('ticket-open');
        if (window.isDesktop()) {
            document.body.style.top = '';
        }
        requestAnimationFrame(function() { window.scrollTo(0, _savedScrollY || 0); });
        // Вернуть nav-bar и заголовок в исходное состояние только если мы сами добавили scrolled
        if (page && page.classList.contains('scrolled') && !_wasPageScrolled) {
            page.classList.remove('scrolled');
        }
    }
}

// Переход к другому билету (по индексу)
function goToTicket(nextIndex) {
    // Сначала находим текущий открытый билет и его контейнер
    const current = document.querySelector('.ticket-item.open');
    if (!current) return;
    const container = current.closest('.ticket-list');
    if (!container) return;
    // Закрыть текущий билет (без снятия блокировки body)
    current.classList.remove('open');
    const currentBody = current.querySelector('.ticket-item-body');
    if (currentBody) currentBody.scrollTop = 0;
    // Открыть следующий билет
    const next = container.querySelector('.ticket-item[data-ticket-index="' + nextIndex + '"]');
    if (next) {
        next.classList.add('open');
        // Прокрутить тело билета наверх
        const body = next.querySelector('.ticket-item-body');
        if (body) body.scrollTop = 0;
    } else {
        // Следующий билет не найден — разблокировать страницу
        document.body.classList.remove('ticket-open');
        document.body.style.top = '';
        requestAnimationFrame(function() { window.scrollTo(0, _savedScrollY || 0); });
        const page = container.closest('.page-content');
        if (page && page.classList.contains('scrolled')) {
            page.classList.remove('scrolled');
        }
    }
}

async function initTicketsPage(catId) {
    const container = document.getElementById('tickets-container-' + catId);
    if (!container) return;
    // Закрыть все открытые билеты (на случай повторного входа на страницу)
    document.querySelectorAll('.ticket-item.open').forEach(item => {
        item.classList.remove('open');
        const body = item.querySelector('.ticket-item-body');
        if (body) body.scrollTop = 0;
    });
    // Снять блокировку прокрутки, если осталась от предыдущего билета
    if (document.body.classList.contains('ticket-open')) {
        document.body.classList.remove('ticket-open');
        document.body.style.top = '';
        requestAnimationFrame(function() { window.scrollTo(0, _savedScrollY || 0); });
    }
    if (document.body.classList.contains('ticket-img-viewing')) {
        closeTicketImage();
    }
    // Десктоп: сбросить состояние мастер-детали и закрыть detail-panel
    _ticketSelectedIndex = -1;
    if (window.isDesktop()) window.closeDetailPanel();
    container.innerHTML = '<div class="ticket-loading">Загрузка…</div>';
    const data = await loadTicketsData();
    if (data) {
        renderTickets(catId, '');
    } else {
        container.innerHTML = '<div class="ticket-empty">Не удалось загрузить данные</div>';
    }
}

// ============================================================
// Exports
// ============================================================
export {
    _ticketsData,
    _ticketGroupsCache,
    _ticketSelectedIndex,
    _bgRefreshInFlight,
    _precacheStarted,
    _ticketsCacheBust,
    TICKET_IDS,
    _savedScrollY,
    _wasPageScrolled,
    loadTicketsData,
    renderTickets,
    ticketSelectItem,
    initTicketsPage,
    toggleTicketItem,
    openTicketImage,
    closeTicketImage,
    ticketRenderDetailInPanel,
    ticketImgOk,
    ticketImgFail,
    goToTicket,
    escHtml,
    getField,
    isWorkingUrl,
    gdriveShareToDirect,
    precacheTicketImages
};
