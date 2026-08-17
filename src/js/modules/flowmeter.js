/**
 * @module flowmeter
 * FlowmeterData — расходомеры хозрасчётные + FlowUserView
 * Extracted from src/index.html (lines 18548–19732)
 */

// ===== External dependency bridges =====
var KipAuth     = window.KipAuth;
var KipToast    = window.KipToast;
var showToast   = window.showToast;
var isDesktop   = window.isDesktop;
var navigateTo  = window.navigateTo;
var setDetailBreadcrumb = window.setDetailBreadcrumb;

var FlowUserView = {

    _STORAGE_KEY: 'kip8test:flow_user_view',
    _data: null,  // ленивый кэш: { favs: {id: addedAt}, hidden: {id: hiddenAt}, order: [id,...] }
    _currentFilter: 'all',  // 'all' | 'fav' | 'hidden'

    // SVG-иконка звёздочки
    _STAR_SVG: '<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    _HIDE_SVG: '<svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',

    // ----------------------------------------------------------
    // Хранилище
    // ----------------------------------------------------------
    _load: function() {
        if (this._data !== null) return;
        try {
            var raw = localStorage.getItem(this._STORAGE_KEY);
            this._data = raw ? JSON.parse(raw) : { favs: {}, hidden: {}, order: [] };
        } catch (e) { this._data = { favs: {}, hidden: {}, order: [] }; }
        // Гарантировать структуру
        if (!this._data.favs) this._data.favs = {};
        if (!this._data.hidden) this._data.hidden = {};
        if (!Array.isArray(this._data.order)) this._data.order = [];
    },

    _save: function() {
        try { localStorage.setItem(this._STORAGE_KEY, JSON.stringify(this._data)); } catch (e) {}
    },

    _esc: function(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    },

    // ----------------------------------------------------------
    // Избранное
    // ----------------------------------------------------------
    isFav: function(id) {
        this._load();
        return this._data.favs.hasOwnProperty(String(id));
    },

    toggleFav: function(id) {
        this._load();
        id = String(id);
        if (this._data.favs.hasOwnProperty(id)) {
            delete this._data.favs[id];
            // Убрать из порядка, если есть
            var idx = this._data.order.indexOf(id);
            if (idx !== -1) this._data.order.splice(idx, 1);
        } else {
            this._data.favs[id] = new Date().toISOString();
            // Добавить в конец порядка, если нет
            if (this._data.order.indexOf(id) === -1) {
                this._data.order.push(id);
            }
        }
        this._save();
        this.updateToolbar();
        this.updateDetailFavBtn();
    },

    favCount: function() {
        this._load();
        return Object.keys(this._data.favs).length;
    },

    // ----------------------------------------------------------
    // Скрытые
    // ----------------------------------------------------------
    isHidden: function(id) {
        this._load();
        return this._data.hidden.hasOwnProperty(String(id));
    },

    toggleHidden: function(id) {
        this._load();
        id = String(id);
        if (this._data.hidden.hasOwnProperty(id)) {
            delete this._data.hidden[id];
        } else {
            this._data.hidden[id] = new Date().toISOString();
            // Убрать из избранного при скрытии
            if (this._data.favs.hasOwnProperty(id)) {
                delete this._data.favs[id];
            }
        }
        this._save();
        this.updateToolbar();
    },

    hiddenCount: function() {
        this._load();
        return Object.keys(this._data.hidden).length;
    },

    restoreAll: function() {
        this._load();
        this._data.hidden = {};
        this._save();
        this.updateToolbar();
        if (typeof FlowmeterData !== 'undefined') FlowmeterData.renderList();
    },

    // ----------------------------------------------------------
    // Пользовательский порядок
    // ----------------------------------------------------------
    getOrder: function() {
        this._load();
        return this._data.order.slice();
    },

    setOrder: function(arr) {
        this._load();
        this._data.order = arr.map(String);
        this._save();
    },

    /** Отсортировать массив расходомеров по пользовательскому порядку.
     *  Расходомеры с порядком идут первыми (по индексу), без — в конце по id. */
    sortMeters: function(meters) {
        this._load();
        var order = this._data.order;
        if (!order || order.length === 0) return meters;  // Нет порядка — как есть
        var orderMap = {};
        order.forEach(function(id, i) { orderMap[String(id)] = i; });
        var sorted = meters.slice().sort(function(a, b) {
            var ai = orderMap[String(a.id)];
            var bi = orderMap[String(b.id)];
            if (ai !== undefined && bi !== undefined) return ai - bi;
            if (ai !== undefined) return -1;
            if (bi !== undefined) return 1;
            return a.id - b.id;  // Fallback: по id
        });
        return sorted;
    },

    // ----------------------------------------------------------
    // Фильтр тулбара
    // ----------------------------------------------------------
    setFilter: function(filter) {
        this._currentFilter = filter;
        // Обновить активную кнопку в обоих наборах (нижний бар + хедер)
        var btns = document.querySelectorAll('.flow-filter-btn, .flow-header-filter-btn');
        btns.forEach(function(btn) {
            btn.classList.toggle('active', btn.getAttribute('data-flow-filter') === filter);
        });
        // Перерендерить список
        if (typeof FlowmeterData !== 'undefined') FlowmeterData.renderList();
    },

    // ----------------------------------------------------------
    // UI: нижний бар фильтров
    // ----------------------------------------------------------
    updateToolbar: function() {
        var favC = this.favCount();
        var hidC = this.hiddenCount();
        // Нижний бар (мобильный)
        var favEl = document.getElementById('flowFavCount');
        var hidEl = document.getElementById('flowHiddenCount');
        var restEl = document.getElementById('flowRestoreBtn');
        var restDiv = document.getElementById('flowRestoreDivider');
        if (favEl) favEl.textContent = favC;
        if (hidEl) hidEl.textContent = hidC;
        var show = hidC > 0 ? '' : 'none';
        if (restEl) restEl.style.display = show;
        if (restDiv) restDiv.style.display = show;
        // Хедер (десктоп)
        var hFavEl = document.getElementById('flowHeaderFavCount');
        var hHidEl = document.getElementById('flowHeaderHiddenCount');
        var hRestEl = document.getElementById('flowHeaderRestoreBtn');
        if (hFavEl) hFavEl.textContent = favC;
        if (hHidEl) hHidEl.textContent = hidC;
        if (hRestEl) hRestEl.style.display = show;
        // Breadcrumb bar (десктоп, при открытой detail-панели)
        var bcFavEl = document.getElementById('flowBcFavCount');
        var bcHidEl = document.getElementById('flowBcHiddenCount');
        var bcRestEl = document.getElementById('flowBcRestoreBtn');
        if (bcFavEl) bcFavEl.textContent = favC;
        if (bcHidEl) bcHidEl.textContent = hidC;
        if (bcRestEl) bcRestEl.style.display = show;
    },

    // ----------------------------------------------------------
    // UI: звёздочка в детальной карточке
    // ----------------------------------------------------------
    updateDetailFavBtn: function() {
        var btn = document.getElementById('flowDetailFavBtn');
        if (!btn) return;
        var id = window._flowDetailId;
        btn.classList.toggle('active', id ? this.isFav(id) : false);
    },

    toggleFavFromDetail: function() {
        var id = window._flowDetailId;
        if (!id) return;
        if (navigator.vibrate) navigator.vibrate(10);
        var wasFav = this.isFav(id);
        this.toggleFav(id);
        if (!wasFav) {
            if (typeof showToast === 'function') showToast('Добавлено в избранное');
        } else {
            if (typeof showToast === 'function') showToast('Убрано из избранного');
        }
    },

    // ----------------------------------------------------------
    // Drag-and-drop
    // ----------------------------------------------------------
    _dragState: null,

    initDrag: function() {
        var list = document.getElementById('flowList');
        if (!list) return;

        var self = this;
        var longPressTimer = null;
        var longPressFired = false;
        var startX = 0, startY = 0;
        var dragEl = null, dragWrap = null;

        list.addEventListener('touchstart', function(e) {
            var wrap = e.target.closest('.flow-card-wrap');
            if (!wrap) return;
            var card = wrap.querySelector('.flow-card');
            if (!card) return;

            longPressFired = false;
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            dragWrap = wrap;
            dragEl = card;

            // Долгое зажатие 500 мс → начать перетаскивание
            longPressTimer = setTimeout(function() {
                longPressFired = true;
                card.classList.add('dragging');
                if (navigator.vibrate) navigator.vibrate(30);
                self._dragState = { id: card.getAttribute('data-flow-id'), el: card, wrap: wrap };
            }, 500);
        }, { passive: true });

        list.addEventListener('touchmove', function(e) {
            if (longPressTimer && !longPressFired) {
                var dx = Math.abs(e.touches[0].clientX - startX);
                var dy = Math.abs(e.touches[0].clientY - startY);
                // Если палец ушёл далеко до срабатывания long-press — отменить
                if (dy > 15 || dx > 15) {
                    clearTimeout(longPressTimer);
                    longPressTimer = null;
                }
            }
            if (!longPressFired || !self._dragState) return;

            // Предотвратить прокрутку при перетаскивании
            e.preventDefault();

            // Найти элемент под пальцем
            var touch = e.touches[0];
            var allWraps = list.querySelectorAll('.flow-card-wrap');
            allWraps.forEach(function(w) {
                var c = w.querySelector('.flow-card');
                if (c) c.classList.remove('drag-over');
            });
            var elUnder = document.elementFromPoint(touch.clientX, touch.clientY);
            if (elUnder) {
                var wrapUnder = elUnder.closest('.flow-card-wrap');
                if (wrapUnder && wrapUnder !== self._dragState.wrap) {
                    var cardUnder = wrapUnder.querySelector('.flow-card');
                    if (cardUnder) cardUnder.classList.add('drag-over');
                }
            }
        }, { passive: false });

        list.addEventListener('touchend', function(e) {
            clearTimeout(longPressTimer);
            longPressTimer = null;

            if (!longPressFired || !self._dragState) {
                // Свайп (если не долгое нажатие)
                if (!longPressFired && dragEl) {
                    self._handleSwipe(e, dragWrap, dragEl);
                }
                if (dragEl) dragEl.classList.remove('dragging');
                self._dragState = null;
                longPressFired = false;
                return;
            }

            // Завершить перетаскивание — переставить элемент
            var overCard = list.querySelector('.flow-card.drag-over');
            if (overCard && self._dragState) {
                var fromWrap = self._dragState.wrap;
                var toWrap = overCard.closest('.flow-card-wrap');
                if (toWrap && fromWrap !== toWrap) {
                    // Переставить DOM-элемент
                    if (fromWrap.nextSibling === toWrap) {
                        list.insertBefore(fromWrap, toWrap.nextSibling);
                    } else {
                        list.insertBefore(fromWrap, toWrap);
                    }
                    // Сохранить новый порядок
                    self._saveOrderFromDOM();
                    if (navigator.vibrate) navigator.vibrate(15);
                }
            }

            // Очистить
            list.querySelectorAll('.flow-card').forEach(function(c) {
                c.classList.remove('dragging', 'drag-over');
            });
            self._dragState = null;
            longPressFired = false;
        }, { passive: true });
    },

    /** Сохранить порядок из текущего DOM в localStorage. */
    _saveOrderFromDOM: function() {
        var list = document.getElementById('flowList');
        if (!list) return;
        var ids = [];
        list.querySelectorAll('.flow-card').forEach(function(card) {
            var id = card.getAttribute('data-flow-id');
            if (id) ids.push(String(id));
        });
        this.setOrder(ids);
    },

    // ----------------------------------------------------------
    // Свайп
    // ----------------------------------------------------------
    _swipeState: null,

    _handleSwipe: function(e, wrap, card) {
        // Свайп уже обработан touchmove/touchend ниже
        // Этот метод вызывается из touchend, если не было long-press
    },

    initSwipe: function() {
        var list = document.getElementById('flowList');
        if (!list) return;

        var self = this;
        var startX = 0, startY = 0, currentX = 0;
        var swipeWrap = null, swipeCard = null;
        var swiping = false;
        var THRESHOLD = 60;  // Порог свайпа в px
        var BLOCK_Y = 30;    // Блокировка вертикального скролла

        list.addEventListener('touchstart', function(e) {
            var wrap = e.target.closest('.flow-card-wrap');
            if (!wrap) return;
            // Не начинать свайп по звёздочке
            if (e.target.closest('.flow-card-fav')) return;
            swipeWrap = wrap;
            swipeCard = wrap.querySelector('.flow-card');
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            currentX = startX;
            swiping = false;
        }, { passive: true });

        list.addEventListener('touchmove', function(e) {
            if (!swipeWrap || !swipeCard) return;
            currentX = e.touches[0].clientX;
            var dx = currentX - startX;
            var dy = Math.abs(e.touches[0].clientY - startY);

            if (!swiping && dy > BLOCK_Y) return;  // Вертикальный скролл — не свайп
            if (!swiping && Math.abs(dx) > 10) {
                swiping = true;
            }
            if (!swiping) return;

            e.preventDefault();

            // Визуальная обратная связь: сдвиг карточки
            var maxShift = 80;
            var shift = Math.max(-maxShift, Math.min(maxShift, dx));
            swipeCard.style.transform = 'translateX(' + shift + 'px)';
            swipeCard.style.transition = 'none';

            // Подложка
            swipeWrap.classList.remove('swiping-left', 'swiping-right');
            if (dx > 20) swipeWrap.classList.add('swiping-right');
            else if (dx < -20) swipeWrap.classList.add('swiping-left');
        }, { passive: false });

        list.addEventListener('touchend', function(e) {
            if (!swipeWrap || !swipeCard) { swipeWrap = null; swipeCard = null; return; }

            var dx = currentX - startX;
            var id = swipeCard.getAttribute('data-flow-id');
            var isFav = self.isFav(id);

            // Сбросить визуальное состояние
            swipeCard.style.transform = '';
            swipeCard.style.transition = '';
            swipeWrap.classList.remove('swiping-left', 'swiping-right');

            if (swiping && Math.abs(dx) >= THRESHOLD) {
                if (dx > 0) {
                    // Свайп вправо:
                    // Если не в избранном → добавить в избранное
                    // Если в избранном → убрать из избранного
                    if (!isFav) {
                        self.toggleFav(id);
                        if (typeof showToast === 'function') showToast('Добавлено в избранное');
                    } else {
                        self.toggleFav(id);
                        if (typeof showToast === 'function') showToast('Убрано из избранного');
                    }
                } else {
                    // Свайп влево: скрыть / показать
                    if (!self.isHidden(id)) {
                        self.toggleHidden(id);
                        if (typeof showToast === 'function') showToast('Скрыто', 'Отмена', function() { self.toggleHidden(id); });
                    } else {
                        self.toggleHidden(id);
                        if (typeof showToast === 'function') showToast('Восстановлено');
                    }
                }
                // Перерендерить список после действия
                if (typeof FlowmeterData !== 'undefined') FlowmeterData.renderList();
            }

            swipeWrap = null;
            swipeCard = null;
            swiping = false;
        }, { passive: true });
    }
};

// FlowmeterData — Расходомеры хозрасчётные: накопительные расходы
// Источник: Google Таблица
// ============================================================
var FlowmeterData = {
    _GOOGLE_SHEET_URL: 'https://docs.google.com/spreadsheets/d/1enZSq7K8pwJVzaAI_tbXZtvATqARTxH0lSU4c-wc1eY/edit?usp=sharing',

    // Роли с правом ввода показаний в расходомеры хозрасчётные
    // (по столбцу «Ввод показаний в расходомеры хозрасчётные» из «Карта ролей.xlsx»)
    _INPUT_READINGS_ROLES: ['КИП ИОС дежурный', 'Админ'],
    _canInputReadings: false,

    // Ключи localStorage для кэша данных
    _cacheKey: 'kip8_flow_cache_v1',

    // Флаг: данные загружены с сервера (true) или это fallback
    _loaded: false,

    // 12 позиций хозрасчётных расходомеров
    // Заполняются из data/flowmeters.json (_loadFallback),
    // localStorage (_restoreCache) или сервера (load).
    // Пустой массив до первой загрузки — рендер покажет заглушку.
    _METERS: [],

    // ============================================================
    // API вызовы (по паттерну KipCableJournal)
    // ============================================================
    _api: function(action, payload) {
        var token = KipAuth.getToken();
        if (!token) return Promise.reject(new Error('Нет токена — войдите в аккаунт'));
        return KipAuth.api(action, Object.assign({ token: token }, payload || {}));
    },

    // ============================================================
    // Инициализация: fallback JSONC → кэш localStorage → свежие данные API
    // ============================================================
    // Если пользователь авторизован — НЕ рендерим промежуточные данные
    // (fallback/кэш), чтобы не показывать устаревшие показания.
    // Ждём ответ API и рендерим сразу свежие данные.
    // Если не авторизован — рендерим fallback/кэш (прогрессивный рендер).
    // ============================================================
    init: function() {
        var self = this;
        var token = KipAuth.getToken();
        var silent = !!token; // авторизован → не рендерить промежуточные данные

        // 1. Показать «Загрузка…» (_METERS пустой)
        this.renderList();

        // 2. Тихо заполнить _METERS из localStorage и data/flowmeters.json.
        //    Если silent=true — populate без renderList().
        this._restoreCache(silent);
        this._loadFallback(silent);

        // 3. Загрузить свежие данные с сервера.
        //    load() всегда рендерит по завершении (успех или ошибка).
        this.load();
    },

    // ============================================================
    // Загрузить data/flowmeters.json как начальный fallback
    // (по паттерну cables.json для кабельного журнала)
    // silent=true — заполнить _METERS без рендера (для авторизованных)
    // ============================================================
    _loadFallback: function(silent) {
        var self = this;
        try {
            var bust = '?v=' + Date.now();
            fetch('data/flowmeters.json' + bust, { cache: 'no-store' })
                .then(function(resp) {
                    if (!resp.ok) return null;
                    return resp.json();
                })
                .then(function(data) {
                    if (data && Array.isArray(data.meters) && data.meters.length > 0) {
                        // Не перезаписывать данные, уже загруженные с сервера
                        if (!self._loaded) {
                            self._METERS = data.meters;
                        }
                        if (!silent) self.renderList();
                    }
                })
                .catch(function() { /* ignore — fallback не критичен */ });
        } catch (e) { /* ignore */ }
    },

    // ============================================================
    // Восстановить кэш из localStorage (мгновенный рендер)
    // silent=true — заполнить _METERS без рендера (для авторизованных)
    // ============================================================
    _restoreCache: function(silent) {
        try {
            var json = localStorage.getItem(this._cacheKey);
            if (json) {
                var cached = JSON.parse(json);
                if (cached && Array.isArray(cached.meters)) {
                    if (!this._loaded) {
                        this._METERS = cached.meters;
                        this._loaded = true;
                    }
                    if (!silent) this.renderList();
                }
            }
        } catch (e) { /* ignore parse errors */ }
    },

    // ============================================================
    // Сохранить данные в localStorage
    // ============================================================
    _persistData: function(meters) {
        try {
            localStorage.setItem(this._cacheKey, JSON.stringify({ meters: meters, ts: Date.now() }));
        } catch (e) { /* quota or disabled */ }
    },

    // Форматирование числа с разделителями
    _fmtNum: function(n) {
        if (n === 0) return '0,00';
        var parts = n.toFixed(2).split('.');
        var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '\u00A0');
        return intPart + ',' + parts[1];
    },

    // Форматирование даты M/D/YYYY → ДД.ММ.ГГГГ
    _fmtDate: function(dateStr) {
        try {
            var p = dateStr.split('/');
            var d = (+p[1] < 10 ? '0' : '') + +p[1];
            var m = (+p[0] < 10 ? '0' : '') + +p[0];
            return d + '.' + m + '.' + p[2];
        } catch (e) { return dateStr; }
    },

    // Разница полных дней между двумя датами (формат M/D/YYYY)
    _daysBetween: function(dateStr1, dateStr2) {
        try {
            var p1 = dateStr1.split('/');
            var p2 = dateStr2.split('/');
            var d1 = new Date(+p1[2], +p1[0] - 1, +p1[1]);
            var d2 = new Date(+p2[2], +p2[0] - 1, +p2[1]);
            var diff = Math.round((d2 - d1) / 86400000);
            return (diff >= 0) ? diff : 0;
        } catch (e) { return 0; }
    },

    // ============================================================
    // Загрузить данные из Google Sheets через Apps Script
    // Если нет токена (гостевой режим) — рендерим fallback/кэш
    // Всегда рендерит по завершении (успех или ошибка),
    // чтобы не оставлять «Загрузка…» навсегда.
    // ============================================================
    load: function() {
        var self = this;

        // Если пользователь не авторизован — не трогаем сервер,
        // рендерим fallback/кэш (если они ещё не отрендерены)
        var token = KipAuth.getToken();
        if (!token) {
            this.renderList();
            return;
        }

        this._api('flowmeter.list', {}).then(function(data) {
            if (data && Array.isArray(data.meters)) {
                self._METERS = data.meters;
                self._loaded = true;
                self._persistData(self._METERS);
            }
            self.renderList();
            // Если детальный вид сейчас видим — перерендерить его.
            // Проверяем, что страница/панель реально открыты,
            // иначе при возврате к списку load() снова откроет деталь.
            if (window._flowDetailId) {
                var detailPage = document.getElementById('page-flowmeter-detail');
                var detailPanel = document.getElementById('detailPanel');
                var isDetailVisible = (detailPage && detailPage.classList.contains('active')) ||
                                      (detailPanel && detailPanel.classList.contains('active'));
                if (isDetailVisible) {
                    self.openDetail(window._flowDetailId);
                }
            }
        }).catch(function(err) {
            // При ошибке — рендерим fallback/кэш,
            // чтобы не оставлять «Загрузка…» навсегда.
            console.error('FlowmeterData.load:', err);
            self.renderList();
        });
    },

    // Рендер списка карточек
    renderList: function() {
        var container = document.getElementById('flowList');
        if (!container) return;

        // Сортировка по пользовательскому порядку
        var meters = FlowUserView.sortMeters(this._METERS);

        // Фильтрация по текущему фильтру тулбара
        var filter = FlowUserView._currentFilter;
        var filtered = [];
        for (var i = 0; i < meters.length; i++) {
            var m = meters[i];
            var isFav = FlowUserView.isFav(m.id);
            var isHidden = FlowUserView.isHidden(m.id);
            if (filter === 'fav' && !isFav) continue;
            if (filter === 'hidden' && !isHidden) continue;
            if (filter === 'all' && isHidden) continue;  // В режиме «Все» скрытые не показываются
            filtered.push({ meter: m, isFav: isFav, isHidden: isHidden });
        }

        // Пусто?
        if (filtered.length === 0 && this._METERS.length > 0) {
            var emptyMsg = filter === 'fav' ? 'Нет избранных расходомеров' :
                           filter === 'hidden' ? 'Нет скрытых расходомеров' : '';
            container.innerHTML = '<div class="flow-empty"><div class="flow-empty-text">' + this._esc(emptyMsg) + '</div><div class="flow-empty-hint">Свайп вправо — в избранное, влево — скрыть</div></div>';
            FlowUserView.updateToolbar();
            return;
        }

        var html = '';
        // SVG для подложек свайпа
        var starSvg = '<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>';
        var hideSvg = '<svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';

        for (var i = 0; i < filtered.length; i++) {
            var item = filtered[i];
            var m = item.meter;
            var isFav = item.isFav;
            var isHidden = item.isHidden;
            var consumption = m.curr - m.prev;
            var consStr = this._fmtNum(Math.abs(consumption));
            var tempStr = (m.temp !== null && m.temp !== undefined) ? m.temp.toFixed(1).replace('.', ',') + ' °C' : '—';
            var days = this._daysBetween(m.datePrev, m.dateCurr);
            var daysStr = (days > 0) ? days + ' дн.' : '';

            // Обёртка для свайпа
            html += '<div class="flow-card-wrap' + (isFav ? ' is-fav' : '') + '" data-flow-wrap-id="' + m.id + '">';

            // Подложка свайпа: влево = скрыть, вправо = в избранное (или убрать)
            html += '<div class="flow-swipe-bg flow-swipe-bg-left">' + hideSvg + '<span>Скрыть</span></div>';
            html += '<div class="flow-swipe-bg flow-swipe-bg-right">' + starSvg + '<span>' + (isFav ? 'Убрать' : 'В избранное') + '</span></div>';

            // Карточка
            html += '<div class="flow-card' + (isHidden ? ' flow-hidden' : '') + '" data-flow-id="' + m.id + '" onclick="FlowmeterData.openDetail(' + m.id + ')">';

            // Звёздочка избранного
            html += '<button type="button" class="flow-card-fav' + (isFav ? ' active' : '') + '" onclick="event.stopPropagation(); FlowUserView.toggleFav(' + m.id + '); FlowmeterData.renderList();" aria-label="Избранное">';
            html += '<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>';
            html += '</button>';

            html += '<div class="flow-card-header">';
            html += '<div class="flow-card-hoz">' + this._esc(m.hoz) + '</div>';
            html += '<div class="flow-card-period">' + this._esc(m.period) + '</div>';
            html += '</div>';
            html += '<div class="flow-card-param">' + this._esc(m.param) + '</div>';
            html += '<div class="flow-card-summary">';
            html += '<span class="flow-summary-item"><span class="flow-summary-label">Последние показания</span><span class="flow-summary-val">' + this._fmtNum(m.curr) + ' ' + this._esc(m.unit) + ',<span class="flow-detail-date"> от ' + this._fmtDate(m.dateCurr) + ' г.</span></span></span>';
            if (m.temp !== null && m.temp !== undefined) { html += '<span class="flow-summary-item"><span class="flow-summary-label">T среды</span><span class="flow-summary-val">' + tempStr + '</span></span>'; }
            html += '</div>';
            html += '</div>';  // .flow-card
            html += '</div>';  // .flow-card-wrap
        }
        container.innerHTML = html;

        // Обновить тулбар
        FlowUserView.updateToolbar();

        // Инициализировать drag-and-drop и свайп
        FlowUserView.initDrag();
        FlowUserView.initSwipe();
    },

    // Построить HTML детальной карточки
    _buildDetailHtml: function(m) {
        var consumption = m.curr - m.prev;
        var consStr = this._fmtNum(Math.abs(consumption));
        var tempStr = (m.temp !== null && m.temp !== undefined) ? m.temp.toFixed(1).replace('.', ',') + ' °C' : '—';

        var html = '';
        // Заголовок карточки — param + period внутри одного div с зеброй
        html += '<div class="flow-detail-header"><div class="flow-detail-param">' + this._esc(m.param) + '</div><div class="flow-detail-period">' + this._esc(m.period) + '</div></div>';

        // Предыдущие показания
        html += '<div class="flow-detail-row"><span class="flow-detail-label">Предыдущие показания</span><span class="flow-detail-value">' + this._fmtNum(m.prev) + ' ' + this._esc(m.unit) + ',<span class="flow-detail-date"> от ' + this._fmtDate(m.datePrev) + ' г.</span></span></div>';
        // Последние показания
        html += '<div class="flow-detail-row"><span class="flow-detail-label">Последние показания</span><span class="flow-detail-value flow-detail-curr">' + this._fmtNum(m.curr) + ' ' + this._esc(m.unit) + ',<span class="flow-detail-date"> от ' + this._fmtDate(m.dateCurr) + ' г.</span></span></div>';
        // Расход
        html += '<div class="flow-detail-row flow-detail-highlight"><span class="flow-detail-label">Расход</span><span class="flow-detail-value">' + consStr + ' ' + this._esc(m.unit) + ',<span class="flow-detail-date"> за ' + this._daysBetween(m.datePrev, m.dateCurr) + ' дн.</span></span></div>';

        // Температура среды (только если есть)
        if (m.temp !== null && m.temp !== undefined) {
            html += '<div class="flow-detail-row"><span class="flow-detail-label">Температура среды</span><span class="flow-detail-value">' + tempStr + '</span></div>';
        }

        // Внёс изменения
        if (m.modName || m.modRole) {
            var modParts = [];
            if (m.modRole) modParts.push(this._esc(m.modRole));
            if (m.modName) modParts.push(this._esc(m.modName));
            html += '<div class="flow-detail-row"><span class="flow-detail-label" style="color:#7a8fa6;">Внёс изменения</span><span class="flow-detail-value" style="color:#5b7a96;">' + modParts.join(', ') + '</span></div>';
        }

        // Placeholder для архива (загрузится асинхронно)
        html += '<div id="flowArchiveContainer" class="flow-archive-loading">Загрузка архива…</div>';

        return html;
    },

    // Открыть детальную карточку
    openDetail: function(id) {
        var m = null;
        for (var i = 0; i < this._METERS.length; i++) {
            if (this._METERS[i].id === id) { m = this._METERS[i]; break; }
        }
        if (!m) return;

        window._flowDetailId = id;

        // Обновить звёздочку избранного в хедере
        FlowUserView.updateDetailFavBtn();

        // На десктопе — рендерим в правую панель
        if (isDesktop()) {
            flowmeterRenderDetailInPanel();
            return;
        }

        // На мобильном — полная страница
        var titleEl = document.getElementById('flowDetailTitle');
        if (titleEl) titleEl.textContent = m.hoz;

        var html = this._buildDetailHtml(m);
        var body = document.getElementById('flowDetailBody');
        if (body) body.innerHTML = html;

        // Нижний бар с кнопкой «Ввести показания»
        var bar = document.getElementById('flowDetailBottomBar');
        if (bar) bar.innerHTML = this._renderBottomBar(m);

        // Загрузить архив асинхронно
        this.loadArchive(id, function(records) {
            var container = document.getElementById('flowArchiveContainer');
            if (container) {
                container.className = '';
                container.innerHTML = FlowmeterData._buildArchiveHtml(records, m);
            }
        });

        navigateTo('flowmeter-detail');
    },

    // HTML-экранирование
    _esc: function(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },

    // Вычислить право ввода показаний по текущей роли
    _computeCanInputReadings: function() {
        var role = null;
        try {
            if (typeof KipAuth !== 'undefined' && KipAuth._cachedRole) {
                role = KipAuth._cachedRole;
            }
        } catch (e) { /* ignore */ }
        if (!role) return false;
        // Админ всегда имеет доступ
        if (role === 'Админ') return true;
        return this._INPUT_READINGS_ROLES.indexOf(role) !== -1;
    },

    // Рендер нижнего бара с кнопкой «Ввести показания»
    // Кнопка видна только ролям с _canInputReadings
    _renderBottomBar: function(m) {
        if (!this._canInputReadings) return '';
        var btnSvg = '<svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
        return '<button type="button" class="flow-input-btn" onclick="FlowmeterData.openInput()">' + btnSvg + ' Ввести показания</button>';
    },

    // Открыть sheet ввода новых показаний
    openInput: function() {
        var id = window._flowDetailId;
        var m = null;
        for (var i = 0; i < this._METERS.length; i++) {
            if (this._METERS[i].id === id) { m = this._METERS[i]; break; }
        }
        if (!m) return;

        var titleEl = document.getElementById('flowInputTitle');
        if (titleEl) titleEl.textContent = m.hoz + ' — ввести показания';

        var field = document.getElementById('flowInputField');
        if (field) { field.value = ''; field.placeholder = 'Текущие показания, ' + m.unit; }

        // Температура — предзаполнить текущим значением
        var tempField = document.getElementById('flowInputTemp');
        if (tempField) {
            if (m.temp !== null && m.temp !== undefined) {
                tempField.value = m.temp.toFixed(1).replace('.', ',');
            } else {
                tempField.value = '';
            }
            tempField.placeholder = '— (необязательно)';
        }

        // Дата — предзаполнить сегодняшней датой (YYYY-MM-DD для type="date")
        var dateField = document.getElementById('flowInputDate');
        if (dateField) {
            var now = new Date();
            var yyyy = now.getFullYear();
            var mm = (now.getMonth() + 1 < 10 ? '0' : '') + (now.getMonth() + 1);
            var dd = (now.getDate() < 10 ? '0' : '') + now.getDate();
            dateField.value = yyyy + '-' + mm + '-' + dd;
        }

        document.getElementById('flowInputOverlay').classList.add('active');
        document.getElementById('flowInputSheet').classList.add('active');

        setTimeout(function() { if (field) field.focus(); }, 350);
    },

    // Закрыть sheet ввода
    closeInput: function() {
        // Убрать фокус с полей — закрывает клавиатуру на мобильных
        var field = document.getElementById('flowInputField');
        var tempField = document.getElementById('flowInputTemp');
        var dateField = document.getElementById('flowInputDate');
        if (field) field.blur();
        if (tempField) tempField.blur();
        if (dateField) dateField.blur();

        document.getElementById('flowInputOverlay').classList.remove('active');
        document.getElementById('flowInputSheet').classList.remove('active');
    },

    // Сохранить введённые показания
    submitInput: function() {
        var field = document.getElementById('flowInputField');
        if (!field) return;

        var val = field.value.replace(/\s/g, '').replace(',', '.');
        var num = parseFloat(val);
        if (isNaN(num)) {
            field.style.borderColor = '#e55';
            setTimeout(function() { field.style.borderColor = ''; }, 1500);
            return;
        }

        // Температура (необязательное поле)
        var tempField = document.getElementById('flowInputTemp');
        var tempVal = null;
        if (tempField && tempField.value.trim() !== '') {
            var tempRaw = tempField.value.replace(/\s/g, '').replace(',', '.');
            var tempNum = parseFloat(tempRaw);
            if (!isNaN(tempNum)) {
                tempVal = tempNum;
            }
        }

        // Дата (YYYY-MM-DD → M/D/YYYY внутренний формат)
        var dateField = document.getElementById('flowInputDate');
        var dateStr = null;
        if (dateField && dateField.value) {
            // dateField.value = "YYYY-MM-DD"
            var dp = dateField.value.split('-');
            if (dp.length === 3) {
                dateStr = (+dp[1]) + '/' + (+dp[2]) + '/' + (+dp[0]);
            }
        }
        // Если дата не указана — используем сегодня
        if (!dateStr) {
            var now = new Date();
            dateStr = (now.getMonth() + 1) + '/' + now.getDate() + '/' + now.getFullYear();
        }

        var id = window._flowDetailId;
        var self = this;

        // Оптимистичное обновление UI: сразу обновляем в памяти
        var meter = null;
        for (var i = 0; i < this._METERS.length; i++) {
            if (this._METERS[i].id === id) {
                meter = this._METERS[i];
                meter.prev = meter.curr;
                meter.curr = num;
                meter.datePrev = meter.dateCurr;
                meter.dateCurr = dateStr;
                if (tempVal !== null) {
                    meter.temp = tempVal;
                }
                // Обновляем подпись — текущий пользователь
                try {
                    var curUser = KipAuth._cachedUser || {};
                    meter.modName = curUser.name || curUser.email || '';
                    meter.modRole = curUser.role || '';
                } catch (e) { /* ignore */ }
                break;
            }
        }

        this.closeInput();

        // Перерендерить список и текущую карточку
        this.renderList();
        this.openDetail(id);

        // Отправить обновление на сервер (в Google Sheets через Apps Script)
        if (meter) {
            this._api('flowmeter.updateReading', {
                id: id,
                prev: meter.prev,
                curr: meter.curr,
                datePrev: meter.datePrev,
                dateCurr: meter.dateCurr,
                temp: meter.temp
            }).then(function(res) {
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Показания сохранены');
                }
                // Перезагрузить данные с сервера, чтобы убедиться в синхронизации
                setTimeout(function() { self.load(); }, 200);
            }).catch(function(err) {
                console.error('flowmeter.updateReading:', err);
                if (typeof KipToast !== 'undefined' && KipToast.show) {
                    KipToast.show('Ошибка сохранения: ' + (err.message || 'сеть'));
                }
            });
        }
    },

    // ============================================================
    // АРХИВ ПОКАЗАНИЙ
    // ============================================================

    // Кэш архива в localStorage: key = 'kip8_flow_archive_v1_{meterId}'
    _archiveCacheKey: function(meterId) {
        return 'kip8_flow_archive_v1_' + meterId;
    },

    // Восстановить архив из localStorage
    _restoreArchiveCache: function(meterId) {
        try {
            var json = localStorage.getItem(this._archiveCacheKey(meterId));
            if (json) {
                var cached = JSON.parse(json);
                if (cached && Array.isArray(cached.records)) {
                    return cached.records;
                }
            }
        } catch (e) { /* ignore */ }
        return null;
    },

    // Сохранить архив в localStorage
    _persistArchive: function(meterId, records) {
        try {
            localStorage.setItem(this._archiveCacheKey(meterId),
                JSON.stringify({ records: records, ts: Date.now() }));
        } catch (e) { /* quota or disabled */ }
    },

    // Загрузить архив с сервера
    loadArchive: function(meterId, callback) {
        var self = this;
        var token = KipAuth.getToken();

        // Если нет токена — попробовать кэш
        if (!token) {
            var cached = this._restoreArchiveCache(meterId);
            if (callback) callback(cached || []);
            return;
        }

        this._api('flowmeter.archive', { id: meterId, limit: 200 }).then(function(data) {
            if (data && Array.isArray(data.records)) {
                self._persistArchive(meterId, data.records);
                if (callback) callback(data.records);
            } else {
                if (callback) callback([]);
            }
        }).catch(function(err) {
            console.error('FlowmeterData.loadArchive:', err);
            // Fallback: вернуть кэш
            var cached = self._restoreArchiveCache(meterId);
            if (callback) callback(cached || []);
        });
    },

    // Рендер секции хронологии (таблица + график)
    _buildArchiveHtml: function(records, meter) {
        if (!records || records.length === 0) {
            return '<div class="flow-archive-section">' +
                   '<div class="flow-archive-title">Хронология показаний</div>' +
                   '<div class="flow-archive-empty">Записей ещё нет</div>' +
                   '</div>';
        }

        // Фильтрация по количеству записей: последние 31 (и моб, и десктоп)
        var recLimit = 31;
        var displayRecords = records.length > recLimit ? records.slice(0, recLimit) : records;

        var html = '';
        html += '<div class="flow-archive-section">';
        html += '<div class="flow-archive-title">Хронология показаний</div>';

        // График расхода (вертикальные бары: даты по X, расход по Y)
        html += this._buildArchiveChart(displayRecords, meter);

        // Таблица
        html += '<div class="flow-archive-table-wrap pinch-zoom-target">';
        html += '<table class="flow-archive-table">';
        html += '<thead><tr>';
        html += '<th>Дата</th>';
        html += '<th>Показания</th>';
        html += '<th>Расход</th>';
        if (displayRecords[0] && displayRecords[0].temp !== null && displayRecords[0].temp !== undefined) {
            html += '<th>T</th>';
        }
        html += '<th>Внёс</th>';
        html += '</tr></thead>';
        html += '<tbody>';

        for (var i = 0; i < displayRecords.length; i++) {
            var r = displayRecords[i];
            var consAbs = Math.abs(r.consumption || 0);
            html += '<tr>';
            html += '<td class="flow-archive-date">' + this._fmtDate(r.dateCurr) + '</td>';
            html += '<td class="flow-archive-val">' + this._fmtNum(r.curr) + '</td>';
            html += '<td class="flow-archive-cons">' + this._fmtNum(consAbs) + '</td>';
            // Температура — показываем колонку только если хоть в одной записи есть
            if (displayRecords[0] && displayRecords[0].temp !== null && displayRecords[0].temp !== undefined) {
                var tStr = (r.temp !== null && r.temp !== undefined) ? r.temp.toFixed(1).replace('.', ',') : '—';
                html += '<td class="flow-archive-temp">' + tStr + '</td>';
            }
            var modStr = r.modName || r.modRole || '';
            html += '<td class="flow-archive-mod">' + this._esc(modStr) + '</td>';
            html += '</tr>';
        }

        html += '</tbody></table>';
        html += '</div>'; // .flow-archive-table-wrap
        html += '</div>'; // .flow-archive-section

        return html;
    },

    // График расхода — вертикальные бары (даты по X, расход по Y), зебра, без Y-оси
    _buildArchiveChart: function(records, meter) {
        if (records.length < 2) return '';

        var unit = meter ? meter.unit : (records[0].unit || '');
        var maxCons = 0;
        for (var i = 0; i < records.length; i++) {
            var c = Math.abs(records[i].consumption || 0);
            if (c > maxCons) maxCons = c;
        }
        if (maxCons === 0) return '';

        // Записи от старых к новым (по X слева направо)
        var chartRecords = records.slice(0, 31).reverse();

        var html = '';
        html += '<div class="flow-archive-chart">';
        html += '<div class="flow-archive-chart-title">Расход, ' + this._esc(unit) + '</div>';
        html += '<div class="flow-archive-chart-body">';

        // Область графика (без Y-оси, без сетки)
        html += '<div class="flow-archive-chart-area">';

        // Бары вплотную, зебра через CSS :nth-child(even)
        for (var j = 0; j < chartRecords.length; j++) {
            var r = chartRecords[j];
            var cons = Math.abs(r.consumption || 0);
            var barPct = Math.max(1, (cons / maxCons) * 100);
            html += '<div class="flow-archive-vbar-col">';
            html += '<div class="flow-archive-vbar-tip-zone"><span class="flow-archive-vbar-tip">' + this._fmtNum(cons) + '</span></div>';
            html += '<div class="flow-archive-vbar-bar-zone"><div class="flow-archive-vbar" style="height:' + barPct.toFixed(1) + '%"></div></div>';
            html += '<div class="flow-archive-vbar-xlabel-zone"><span class="flow-archive-vbar-xlabel">' + this._fmtDateShort(r.dateCurr) + '</span></div>';
            html += '</div>';
        }

        html += '</div>'; // .flow-archive-chart-area
        html += '</div>'; // .flow-archive-chart-body
        html += '</div>'; // .flow-archive-chart
        return html;
    },

    // Сокращённая дата: M/D/YYYY → ДД.ММ
    _fmtDateShort: function(dateStr) {
        try {
            var p = dateStr.split('/');
            var d = (+p[1] < 10 ? '0' : '') + +p[1];
            var m = (+p[0] < 10 ? '0' : '') + +p[0];
            return d + '.' + m;
        } catch (e) { return dateStr; }
    }
};

// Pinch-to-zoom для таблицы архива — используется универсальная система
// (класс pinch-zoom-target назначается при генерации HTML в _buildArchiveHtml)

// flowmeterRenderDetailInPanel — рендер детальной карточки расходомера
// в правую панель (#detailPanel) на десктопе
function flowmeterRenderDetailInPanel() {
    var flowId = window._flowDetailId;
    if (!flowId) return;
    var m = null;
    for (var i = 0; i < FlowmeterData._METERS.length; i++) {
        if (FlowmeterData._METERS[i].id === flowId) { m = FlowmeterData._METERS[i]; break; }
    }
    if (!m) return;

    var bodyEl = document.getElementById('detailPanelBody');
    if (!bodyEl) return;

    // Рендерим HTML в панель
    bodyEl.innerHTML = FlowmeterData._buildDetailHtml(m);

    // Кнопка ввода показаний — в нижний бар detail-panel-footer
    var footerEl = document.getElementById('detailPanelFooter');
    if (footerEl) footerEl.innerHTML = FlowmeterData._renderBottomBar(m);

    // Загрузить архив асинхронно
    FlowmeterData.loadArchive(flowId, function(records) {
        var container = document.getElementById('flowArchiveContainer');
        if (container) {
            container.className = '';
            container.innerHTML = FlowmeterData._buildArchiveHtml(records, m);
        }
    });

    // Открываем панель
    var panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');

    // Показываем полноэкранную строку breadcrumbs
    var bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');

    // Подсветка активной карточки в списке слева
    document.querySelectorAll('.flow-card.detail-highlight').forEach(function(el) { el.classList.remove('detail-highlight'); });
    var activeCard = document.querySelector('.flow-card[data-flow-id="' + flowId + '"]');
    if (activeCard) {
        activeCard.classList.add('detail-highlight');
        activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Breadcrumbs в заголовке detail-панели
    setDetailBreadcrumb('flowmeter-detail', m.hoz, null, null);

    // Обновляем заголовок панели
    var titleEl = document.getElementById('detailPanelTitle');
    if (titleEl) titleEl.textContent = m.hoz;
}

// ===== Window bridges (for inline HTML event handlers) =====
window.FlowUserView = FlowUserView;
window.FlowmeterData = FlowmeterData;
window.flowmeterRenderDetailInPanel = flowmeterRenderDetailInPanel;

export { FlowUserView, FlowmeterData, flowmeterRenderDetailInPanel };
