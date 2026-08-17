/**
 * @module favorites
 * KipFav — избранное для каталогов КИП ИОС + KipFavNotes — заметки
 */

const KipFav = {

    _STORAGE_KEY: 'kip8_device_fav_v1',
    _ORDER_KEY: 'kip8_fav_order_v1',   // пользовательский порядок (массив ключей)
    _data: null,  // ленивый кэш: { devId: addedAt, ... }

    // ----------------------------------------------------------
    // Хранилище
    // ----------------------------------------------------------

    _load: function() {
        if (this._data !== null) return;
        try {
            const raw = localStorage.getItem(this._STORAGE_KEY);
            this._data = raw ? JSON.parse(raw) : {};
        } catch (e) { this._data = {}; }
    },

    _save: function() {
        try { localStorage.setItem(this._STORAGE_KEY, JSON.stringify(this._data || {})); } catch (e) {}
    },

    _esc: function(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    },

    /** Составной ключ избранного: 'dev:ID' | 'lock:ID' | 'valve:ID' | 'reg:ID'.
     *  Для приборов (type='dev') — просто ID (обратная совместимость). */
    _favKey: function(type, id) {
        if (type === 'dev' || !type) return String(id);
        return type + ':' + String(id);
    },

    /** Разобрать составной ключ: {type, id}. Без префикса → type='dev'. */
    _parseKey: function(favKey) {
        var s = String(favKey);
        var idx = s.indexOf(':');
        if (idx === -1) return { type: 'dev', id: s };
        return { type: s.substring(0, idx), id: s.substring(idx + 1) };
    },

    /** Проверить, в избранном ли элемент (по составному ключу). */
    hasItem: function(favKey) {
        this._load();
        return this._data.hasOwnProperty(favKey);
    },

    /** Проверить, в избранном ли прибор. */
    has: function(devId) {
        this._load();
        return this._data.hasOwnProperty(devId);
    },

    /** Добавить прибор в избранное. */
    add: function(devId) {
        this._load();
        if (!this._data.hasOwnProperty(devId)) {
            this._data[devId] = new Date().toISOString();
            this._save();
            this.updateDashboardButton();
            this.updateHeaderIcon();
        }
    },

    /** Убрать прибор из избранного. */
    remove: function(devId) {
        this._load();
        if (this._data.hasOwnProperty(devId)) {
            delete this._data[devId];
            this._save();
            this.updateDashboardButton();
            this.updateHeaderIcon();
        }
    },

    /** Переключить избранное для прибора. Возвращает true если добавлен, false если убран. */
    toggle: function(devId) {
        if (this.has(devId)) {
            this.remove(devId);
            return false;
        } else {
            this.add(devId);
            return true;
        }
    },

    /** Количество избранных. */
    count: function() {
        this._load();
        return Object.keys(this._data).length;
    },

    /** Все избранные (для списка). Возвращает [{devId, addedAt},...] отсортированные по пользователь/ному порядку, затем по addedAt desc. */
    all: function() {
        this._load();
        const order = this.getOrder();
        const result = [];
        for (const devId in this._data) {
            if (this._data.hasOwnProperty(devId)) {
                result.push({ devId: devId, addedAt: this._data[devId] });
            }
        }
        if (order.length > 0) {
            // Сортировка по пользовательскому порядку
            const orderMap = {};
            order.forEach(function(k, i) { orderMap[k] = i; });
            result.sort(function(a, b) {
                const ai = orderMap[a.devId];
                const bi = orderMap[b.devId];
                // Элементы с порядком идут первыми (по индексу), без порядка — в конце (по addedAt desc)
                if (ai !== undefined && bi !== undefined) return ai - bi;
                if (ai !== undefined) return -1;
                if (bi !== undefined) return 1;
                return (b.addedAt || '').localeCompare(a.addedAt || '');
            });
            // Автоочистка: убрать из порядка ключи, которых больше нет в избранном
            const currentKeys = Object.keys(this._data);
            const cleaned = order.filter(function(k) { return currentKeys.indexOf(k) !== -1; });
            if (cleaned.length !== order.length) this.setOrder(cleaned);
        } else {
            result.sort(function(a, b) { return (b.addedAt || '').localeCompare(a.addedAt || ''); });
        }
        return result;
    },

    /** Получить пользовательский порядок избранных. */
    getOrder: function() {
        try {
            const raw = localStorage.getItem(this._ORDER_KEY);
            if (!raw) return [];
            const arr = JSON.parse(raw);
            return Array.isArray(arr) ? arr : [];
        } catch (e) { return []; }
    },

    /** Сохранить пользовательский порядок избранных. */
    setOrder: function(arr) {
        try { localStorage.setItem(this._ORDER_KEY, JSON.stringify(arr)); } catch (e) {}
    },

    // ----------------------------------------------------------
    // UI: значок в хедере карточки прибора
    // ----------------------------------------------------------

    /** Обновить состояние значка-закладки в хедере (мобильный + десктоп). */
    updateHeaderIcon: function() {
        // Мобильный: значок в page-device-detail хедере
        const btn = document.getElementById('deviceFavBtn');
        if (btn) {
            const devId = window._devDetailId;
            btn.classList.toggle('active', devId ? this.has(devId) : false);
        }
        // Мобильный: значки в хедерах блокировки/клапана/регулятора
        const lockBtn = document.getElementById('lockFavBtn');
        if (lockBtn) {
            const lockId = window._lockDetailId;
            lockBtn.classList.toggle('active', lockId ? this.hasItem(this._favKey('lock', lockId)) : false);
        }
        const valveBtn = document.getElementById('valveFavBtn');
        if (valveBtn) {
            const valveId = window._valveDetailId;
            valveBtn.classList.toggle('active', valveId ? this.hasItem(this._favKey('valve', valveId)) : false);
        }
        const regBtn = document.getElementById('regulatorFavBtn');
        if (regBtn) {
            const regId = window._regulatorDetailId;
            regBtn.classList.toggle('active', regId ? this.hasItem(this._favKey('reg', regId)) : false);
        }
        const projBtn = document.getElementById('projectFavBtn');
        if (projBtn) {
            const projId = window._projectDetailId;
            projBtn.classList.toggle('active', projId ? this.hasItem(this._favKey('proj', projId)) : false);
        }
        // Десктоп: значок в detailPanel хедере
        const dpBtn = document.getElementById('detailPanelFavBtn');
        if (dpBtn) {
            const devId = window._devDetailId;
            // Показываем только если открыт прибор, блокировка, клапан или регулятор
            const isDevDetail = devId && typeof devData !== 'undefined' && devData && devData.devices &&
                devData.devices.find(function(d) { return String(d['ID'] || '') === String(devId); });
            const isLockDetail = !!window._lockDetailId;
            const isValveDetail = !!window._valveDetailId;
            const isRegDetail = !!window._regulatorDetailId;
            const isProjDetail = !!window._projectDetailId;
            const showFav = isDevDetail || isLockDetail || isValveDetail || isRegDetail || isProjDetail;
            dpBtn.style.display = showFav ? '' : 'none';
            // Определяем активность: для приборов — по devId, для lock/valve/reg — по составному ключу
            let isActive = false;
            if (isDevDetail) isActive = this.has(devId);
            else if (isLockDetail) isActive = this.hasItem(this._favKey('lock', window._lockDetailId));
            else if (isValveDetail) isActive = this.hasItem(this._favKey('valve', window._valveDetailId));
            else if (isRegDetail) isActive = this.hasItem(this._favKey('reg', window._regulatorDetailId));
            else if (isProjDetail) isActive = this.hasItem(this._favKey('proj', window._projectDetailId));
            dpBtn.classList.toggle('active', isActive);
            // Сохраняем текущий тип для toggleFromDetailByType
            if (isLockDetail) dpBtn.setAttribute('data-fav-type', 'lock');
            else if (isValveDetail) dpBtn.setAttribute('data-fav-type', 'valve');
            else if (isRegDetail) dpBtn.setAttribute('data-fav-type', 'reg');
            else if (isProjDetail) dpBtn.setAttribute('data-fav-type', 'proj');
            else dpBtn.removeAttribute('data-fav-type');
        }
        // Десктоп: значок внутри карточки (.dev-detail-fav-btn)
        const cardBtn = document.querySelector('.dev-detail-fav-btn');
        if (cardBtn) {
            // Определяем активность по текущему открытому типу
            let isActive = false;
            if (window._devDetailId) isActive = this.has(window._devDetailId);
            else if (window._lockDetailId) isActive = this.hasItem(this._favKey('lock', window._lockDetailId));
            else if (window._valveDetailId) isActive = this.hasItem(this._favKey('valve', window._valveDetailId));
            else if (window._regulatorDetailId) isActive = this.hasItem(this._favKey('reg', window._regulatorDetailId));
            else if (window._projectDetailId) isActive = this.hasItem(this._favKey('proj', window._projectDetailId));
            cardBtn.classList.toggle('active', isActive);
        }
    },

    /** Клик по значку: toggle избранного для текущего прибора. */
    toggleFromDetail: function() {
        const devId = window._devDetailId;
        if (!devId) return;
        if (navigator.vibrate) navigator.vibrate(10);
        const wasAdded = this.toggle(devId);
        if (wasAdded) {
            window.showToast('Добавлено в избранное', 'Открыть', function() { window.navigateTo('device-favorites'); });
        } else {
            window.showToast('Убрано из избранного');
        }
    },

    /** Клик по значку в десктоп-панели: определяет тип (dev/lock/valve/reg) и toggle. */
    toggleFromDetailPanel: function() {
        const dpBtn = document.getElementById('detailPanelFavBtn');
        const favType = dpBtn ? dpBtn.getAttribute('data-fav-type') : null;
        if (favType) {
            this.toggleFromDetailByType(favType);
        } else {
            // Прибор — используем старый метод
            this.toggleFromDetail();
            this.updateHeaderIcon();
        }
    },

    /** Клик по значку: toggle избранного для блокировки/клапана/регулятора/проекта.
     *  type: 'lock' | 'valve' | 'reg' | 'proj'
     *  Определяет ID по window._lockDetailId / _valveDetailId / _regulatorDetailId / _projectDetailId,
     *  строит составной ключ через _favKey(), toggle, обновляет UI. */
    toggleFromDetailByType: function(type) {
        var id;
        if (type === 'lock') id = window._lockDetailId;
        else if (type === 'valve') id = window._valveDetailId;
        else if (type === 'reg') id = window._regulatorDetailId;
        else if (type === 'proj') id = window._projectDetailId;
        if (!id) return;
        if (navigator.vibrate) navigator.vibrate(10);
        const favKey = this._favKey(type, id);
        const wasAdded = this.toggle(favKey);
        if (wasAdded) {
            window.showToast('Добавлено в избранное', 'Открыть', function() { window.navigateTo('device-favorites'); });
        } else {
            window.showToast('Убрано из избранного');
        }
        // Обновить состояние кнопок: в карточке + в заголовке
        this.updateDetailFavBtnByType(type, id);
        this.updateHeaderIcon();
    },

    /** Обновить состояние значка избранного внутри карточки (десктоп).
     *  type: 'lock' | 'valve' | 'reg'  */
    updateDetailFavBtnByType: function(type, id) {
        const cardBtn = document.querySelector('.dev-detail-fav-btn');
        if (!cardBtn) return;
        const favKey = this._favKey(type, id);
        cardBtn.classList.toggle('active', this.hasItem(favKey));
    },

    // ----------------------------------------------------------
    // UI: кнопка «Избранное» на дашборде
    // ----------------------------------------------------------

    updateDashboardButton: function() {
        const n = this.count();
        this._appendFavButton(n);
    },

    /** Добавить/обновить кнопку «Избранное» в pinnedItemsContainer. */
    _appendFavButton: function(n) {
        const container = document.getElementById('pinnedItemsContainer');
        if (!container) return;
        // Удалить старую кнопку если есть
        const existing = document.getElementById('dashboardFavBtn');
        if (existing) {
            const existingCell = existing.closest('.pinned-item-cell') || existing;
            existingCell.remove();
        }

        if (n <= 0) return;  // Нет избранного — не показываем кнопку

        const word = n === 1 ? 'элемент' : (n >= 2 && n <= 4 ? 'элемента' : 'элементов');
        const sublabel = n + ' ' + word + ' в избранном';

        // Если контейнер пуст (нет закреплённых), нужно создать menu-btn-row
        let row = container.querySelector('.menu-btn-row.pinned-items-row');
        if (!row) {
            // Нет закреплённых — создаём отдельный row для избранного
            row = document.createElement('div');
            row.className = 'menu-btn-row pinned-items-row';
            container.appendChild(row);
        }

        const cell = document.createElement('div');
        cell.className = 'pinned-item-cell';
        cell.id = 'dashboardFavBtn';
        cell.innerHTML =
            '<div class="pinned-item-delete-bg pinned-item-delete-left"><svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Убрать</span></div>' +
            '<div class="pinned-item-delete-bg pinned-item-delete-right"><svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Убрать</span></div>' +
            '<div class="menu-btn pinned-item" data-pinned-key="_fav" onclick="window.navigateTo(\'device-favorites\')" style="border-color:rgba(199,150,74,0.35);">' +
                '<div class="menu-btn-text">' +
                    '<div class="menu-btn-label" style="color:#c7964a;">Избранное</div>' +
                    '<div class="menu-btn-sublabel">' + this._esc(sublabel) + '</div>' +
                '</div>' +
                '<i class="menu-btn-arrow" style="color:rgba(199,150,74,0.4);">›</i>' +
            '</div>';
        row.appendChild(cell);
    },

    // ----------------------------------------------------------
    // UI: страница избранного (page-device-favorites)
    // ----------------------------------------------------------

    /** Загрузить данные для всех типов, которые есть в избранном.
     *  Вызывается перед cleanupStale и рендером, чтобы:
     *  - cleanupStale мог корректно определить «мёртвые» ссылки
     *  - карточки отображали имена вместо сырых ID */
    _ensureDataLoaded: async function() {
        this._load();
        const types = new Set();
        for (var favKey in this._data) {
            if (this._data.hasOwnProperty(favKey)) {
                types.add(this._parseKey(favKey).type);
            }
        }
        const loads = [];
        if (types.has('dev') && typeof devLoad === 'function' && !devLoaded) {
            loads.push(devLoad().catch(function(e) { console.warn('[KipFav] devLoad failed:', e); }));
        }
        if (types.has('lock') && typeof lockLoaded !== 'undefined' && !lockLoaded) {
            loads.push(
                fetch('data/lockouts.json?v=' + Date.now(), { cache: 'no-store' })
                    .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                    .then(function(d) { lockData = d; lockLoaded = true; })
                    .catch(function(e) { console.warn('[KipFav] lockouts load failed:', e); })
            );
        }
        if (types.has('valve') && typeof valveLoaded !== 'undefined' && !valveLoaded) {
            loads.push(
                fetch('data/valves.json?v=' + Date.now(), { cache: 'no-store' })
                    .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                    .then(function(d) { valveData = d; valveLoaded = true; })
                    .catch(function(e) { console.warn('[KipFav] valves load failed:', e); })
            );
        }
        if (types.has('reg') && typeof regulatorLoaded !== 'undefined' && !regulatorLoaded) {
            loads.push(
                fetch('data/regulators.json?v=' + Date.now(), { cache: 'no-store' })
                    .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                    .then(function(d) { regulatorData = d; regulatorLoaded = true; })
                    .catch(function(e) { console.warn('[KipFav] regulators load failed:', e); })
            );
        }
        if (types.has('proj') && typeof projectLoaded !== 'undefined' && !projectLoaded) {
            loads.push(
                fetch('data/projects.json?v=' + Date.now(), { cache: 'no-store' })
                    .then(function(r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                    .then(function(d) { projectData = d; projectLoaded = true; })
                    .catch(function(e) { console.warn('[KipFav] projects load failed:', e); })
            );
        }
        if (loads.length > 0) await Promise.all(loads);
    },

    initFavoritesPage: async function() {
        const content = document.getElementById('deviceFavoritesContent');
        if (!content) return;

        // Загрузить данные для всех типов, которые есть в избранном
        await this._ensureDataLoaded();

        // Автоматическая очистка «мёртвых» ссылок
        const staleRemoved = this.cleanupStale();
        if (staleRemoved > 0) {
            KipFavNotes.cleanupStale();
        }

        const favs = this.all();
        let html = '';

        // Обновить элементы в верхнем баре
        var countEl = document.getElementById('favHeaderCount');
        var clearBtn = document.getElementById('favHeaderClearBtn');
        if (favs.length > 0) {
            var word = favs.length === 1 ? 'элемент' : (favs.length >= 2 && favs.length <= 4 ? 'элемента' : 'элементов');
            if (countEl) { countEl.textContent = favs.length + ' ' + word; countEl.style.display = ''; }
            if (clearBtn) { clearBtn.style.display = ''; }
        } else {
            if (countEl) { countEl.style.display = 'none'; }
            if (clearBtn) { clearBtn.style.display = 'none'; }
        }

        if (favs.length === 0) {
            html += '<div class="dev-fav-empty">Список избранного пуст.<br>Нажмите значок закладки на карточке, чтобы добавить в избранное.</div>';
            content.innerHTML = html;
            return;
        }

        // Метки и цвета для типов
        var typeLabels = {
            dev:  { label: 'П', color: '#6aa6e0', name: 'Прибор' },
            lock: { label: 'Б', color: '#b85a7a', name: 'Блокировка' },
            valve:{ label: 'К', color: '#4a8a8c', name: 'Клапан' },
            reg:  { label: 'Р', color: '#7e5ab8', name: 'Регулятор' },
            proj: { label: 'Пр', color: '#c7964a', name: 'Проект' }
        };

        const self = this;
        html += '<div class="dev-list">';
        favs.forEach(function(fav) {
            const favKey = fav.devId; // на самом деле это составной ключ
            const parsed = self._parseKey(favKey);
            const type = parsed.type;
            const itemId = parsed.id;
            const meta = typeLabels[type] || typeLabels.dev;

            let itemName = itemId;
            let itemSub1 = '';
            let itemSub2 = '';
            let itemImgUrl = '';

            // Найти данные элемента
            if (type === 'dev') {
                if (typeof devData !== 'undefined' && devData && devData.devices) {
                    const dev = devData.devices.find(function(d) { return String(d['ID'] || '') === String(itemId); });
                    if (dev) {
                        itemName = dev['Наименование'] || itemId;
                        itemSub1 = dev['Тип'] || '';
                        itemSub2 = dev['Место установки'] || '';
                        const num = dev['№ прибора'] || '';
                        if (num) itemSub1 += (itemSub1 ? ' · №' : '№') + num;
                        if (typeof devGetImageUrl === 'function') itemImgUrl = devGetImageUrl(dev) || '';
                    }
                }
            } else if (type === 'lock') {
                if (typeof lockData !== 'undefined' && lockData && lockData.lockouts) {
                    const item = lockData.lockouts.find(function(d) { return String(d['ID'] || '') === String(itemId); });
                    if (item) {
                        itemName = item['Параметр'] || itemId;
                        itemSub1 = item['Уставка'] || '';
                        itemSub2 = item['Расположение'] || '';
                    }
                }
            } else if (type === 'valve') {
                if (typeof valveData !== 'undefined' && valveData && valveData.valves) {
                    const item = valveData.valves.find(function(d) { return String(d['ID'] || '') === String(itemId); });
                    if (item) {
                        itemName = item['Марка'] || item['Назначение арматуры (параметр)'] || itemId;
                        itemSub1 = item['Тип, пропускная характеристика'] || '';
                        itemSub2 = item['Место расположения'] || '';
                    }
                }
            } else if (type === 'reg') {
                if (typeof regulatorData !== 'undefined' && regulatorData && regulatorData.regulators) {
                    const item = regulatorData.regulators.find(function(d) { return String(d['ID'] || '') === String(itemId); });
                    if (item) {
                        itemName = item['Параметр'] || itemId;
                        itemSub1 = item['Устроиство регулятора или ручного управления'] || '';
                        itemSub2 = item['Производство'] || '';
                    }
                }
            } else if (type === 'proj') {
                if (typeof projectData !== 'undefined' && projectData && projectData.projects) {
                    const item = projectData.projects.find(function(d) { return String(d['ID'] || '') === String(itemId); });
                    if (item) {
                        itemName = item['Наименование проекта'] || itemId;
                        itemSub1 = item['№ проекта'] || '';
                        itemSub2 = item['Статус проекта'] || '';
                    }
                }
            }

            const imgSrc = itemImgUrl || (typeof DEV_PLACEHOLDER_SVG !== 'undefined' ? DEV_PLACEHOLDER_SVG : '');
            const safeKey = self._esc(favKey).replace(/'/g, "\\'");
            const note = KipFavNotes.get(favKey);

            // fav-card-cell — обёртка для свайпа
            html += '<div class="fav-card-cell" data-fav-id="' + self._esc(favKey) + '">';
            html += '<div class="fav-card-delete-bg fav-card-delete-left"><svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Убрать</span></div>';
            html += '<div class="fav-card-delete-bg fav-card-delete-right"><svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Убрать</span></div>';
            // Карточка
            html += '<div class="dev-card fav-card" data-dev-id="' + self._esc(favKey) + '">';
            // Верхняя строка: миниатюра/бейдж слева + данные справа
            html += '<div class="fav-card-top">';
            if (type === 'dev' && imgSrc) {
                html += '<img class="fav-card-img" src="' + self._esc(imgSrc) + '" alt="' + self._esc(itemName) + '" loading="lazy">';
            } else {
                html += '<div class="fav-card-type-badge" style="background:' + meta.color + ';">' + meta.label + '</div>';
            }
            // Текстовый блок
            html += '<div class="fav-card-body" onclick="KipFav.openFromFav(\'' + safeKey + '\')">';
            html += '<div class="dev-card-title">' + self._esc(itemName) + '</div>';
            if (itemSub1) {
                html += '<div class="dev-card-subtitle">' + self._esc(itemSub1) + '</div>';
            }
            if (itemSub2) {
                html += '<div class="dev-card-subtitle">' + self._esc(itemSub2) + '</div>';
            }
            html += '</div>'; // .fav-card-body
            html += '</div>'; // .fav-card-top
            // Заметка
            if (note) {
                html += '<div class="dev-fav-note-row" onclick="event.stopPropagation(); KipFavNotes.prompt(\'' + safeKey + '\')">';
                html += '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>';
                html += '<span class="dev-fav-note-text">' + self._esc(note) + '</span>';
                html += '</div>';
            } else {
                html += '<div class="dev-fav-note-add" onclick="event.stopPropagation(); KipFavNotes.prompt(\'' + safeKey + '\')">+ заметка</div>';
            }
            html += '</div>'; // .dev-card
            html += '</div>'; // .fav-card-cell
        });
        html += '</div>';
        content.innerHTML = html;
        this._attachFavSwipe();
    },

    /** Открыть карточку элемента из избранного по составному ключу. */
    openFromFav: function(favKey) {
        if (!favKey) return;
        var parsed = this._parseKey(favKey);
        var type = parsed.type;
        var itemId = parsed.id;
        if (type === 'dev') {
            window._devDetailId = itemId;
            if (window.isDesktop()) {
                if (typeof devRenderDetailInPanel === 'function') devRenderDetailInPanel();
            } else {
                window.navigateTo('device-detail');
            }
        } else if (type === 'lock') {
            window._lockDetailId = itemId;
            if (window.isDesktop()) {
                if (typeof lockRenderDetailInPanel === 'function') lockRenderDetailInPanel();
            } else {
                window.navigateTo('lockout-detail');
            }
        } else if (type === 'valve') {
            window._valveDetailId = itemId;
            if (window.isDesktop()) {
                if (typeof valveRenderDetailInPanel === 'function') valveRenderDetailInPanel();
            } else {
                window.navigateTo('valve-detail');
            }
        } else if (type === 'reg') {
            window._regulatorDetailId = itemId;
            if (window.isDesktop()) {
                if (typeof regulatorRenderDetailInPanel === 'function') regulatorRenderDetailInPanel();
            } else {
                window.navigateTo('regulator-detail');
            }
        } else if (type === 'proj') {
            window._projectDetailId = itemId;
            if (window.isDesktop()) {
                if (typeof projectRenderDetailInPanel === 'function') projectRenderDetailInPanel();
            } else {
                window.navigateTo('project-detail');
            }
        }
    },

    // ----------------------------------------------------------
    // Свайп для удаления + долгое зажатие для перетаскивания
    // ----------------------------------------------------------
    // По паттерну pinned-item: pointer events, 500 мс long-press → drag,
    // быстрое горизонтальное движение → swipe-to-delete.

    _favInteractState: null,
    _FAV_DRAG_DELAY: 500,        // мс до начала перетаскивания
    _FAV_DRAG_THRESHOLD: 10,     // px — горизонтальное движение больше этого → свайп
    _FAV_IDLE_SCROLL_THRESHOLD: 15, // px — вертикальное смещение в idle, после которого переходим в ручной скролл
    _FAV_SWIPE_RATIO: 0.3,       // доля ширины карточки для порога удаления свайпом

    /** touchmove-перехватчик: запрещает скролл в режиме drag.
     *  Вешается на window с { passive: false } при pointerdown на карточке.
     *  В idle/swipe режиме пропускает событие (скролл разрешён).
     *  В drag режиме вызывает preventDefault() — скролл блокируется. */
    _onFavTouchMove: function(e) {
        var st = KipFav._favInteractState;
        if (st && st.mode === 'drag') {
            e.preventDefault();
        }
    },

    _attachFavSwipe: function() {
        // Переименовали для обратной совместимости — теперь вешает и swipe, и drag
        const cards = document.querySelectorAll('#deviceFavoritesContent .fav-card');
        const self = this;
        cards.forEach(function(card) {
            card.addEventListener('pointerdown', function(e) {
                if (e.button !== undefined && e.button !== 0) return;
                if (e.target.closest('.dev-card-fav-indicator')) return;
                if (e.target.closest('.dev-fav-note-row')) return;
                if (e.target.closest('.dev-fav-note-add')) return;
                const cell = card.closest('.fav-card-cell');
                if (!cell) return;
                e.preventDefault();  // запрещаем нативные действия (скролл, контекстное меню)
                const favId = cell.getAttribute('data-fav-id');
                const rect = card.getBoundingClientRect();
                self._favInteractState = {
                    card: card,
                    cell: cell,
                    favId: favId,
                    startX: e.clientX,
                    startY: e.clientY,
                    width: rect.width,
                    timer: setTimeout(function() { self._startFavDrag(e); }, self._FAV_DRAG_DELAY),
                    mode: 'idle',   // 'idle' | 'swipe' | 'drag' | 'scroll'
                    currentDx: 0,
                    // Drag-поля
                    clone: null,
                    hoverCard: null,
                    grabOffsetX: 0,
                    grabOffsetY: 0,
                    moved: false,
                    // Последняя Y-позиция — для ручного скролла в режиме 'scroll'
                    lastScrollY: e.clientY
                };
                window.addEventListener('pointermove', self._onFavPtrMove);
                window.addEventListener('pointerup', self._onFavPtrUp);
                window.addEventListener('pointercancel', self._onFavPtrUp);
                // touchmove-перехватчик: блокирует скролл в режиме drag
                window.addEventListener('touchmove', self._onFavTouchMove, { passive: false });
            });
        });
    },

    _onFavPtrMove: function(e) {
        const st = KipFav._favInteractState;
        if (!st) return;
        const dx = e.clientX - st.startX;
        const dy = e.clientY - st.startY;

        // Режим ручного скролла — прокручиваем страницу вместо перетаскивания
        if (st.mode === 'scroll') {
            const deltaY = e.clientY - st.lastScrollY;
            if (deltaY !== 0) {
                window.scrollBy(0, -deltaY);
            }
            st.lastScrollY = e.clientY;
            return;
        }

        // Если режим ещё не определён — определяем намерение
        if (st.mode === 'idle') {
            var absDx = Math.abs(dx), absDy = Math.abs(dy);
            // Явно горизонтальное движение → свайп
            if (absDx > KipFav._FAV_DRAG_THRESHOLD && absDx > absDy * 1.3) {
                clearTimeout(st.timer);
                st.mode = 'swipe';
                st.card.classList.add('swipe-active');
                if (navigator.vibrate) navigator.vibrate(5);
            }
            // Явно вертикальное движение (скролл страницы) → переключаемся в режим scroll
            else if (absDy > KipFav._FAV_IDLE_SCROLL_THRESHOLD && absDy > absDx * 1.5) {
                clearTimeout(st.timer);
                st.mode = 'scroll';
                st.lastScrollY = e.clientY;
                if (dy !== 0) {
                    window.scrollBy(0, -dy);
                }
            }
            // Иначе: малое движение (джиттер пальца) — ничего не делаем, таймер drag продолжает идти
            return;
        }

        // Swipe-режим
        if (st.mode === 'swipe') {
            e.preventDefault();
            let effectiveDx = dx;
            if (Math.abs(dx) > st.width) {
                const over = Math.abs(dx) - st.width;
                effectiveDx = Math.sign(dx) * (st.width + over * 0.3);
            }
            st.currentDx = effectiveDx;
            st.card.style.transform = 'translateX(' + effectiveDx + 'px)';
            st.cell.classList.toggle('swiping-left', effectiveDx < 0);
            st.cell.classList.toggle('swiping-right', effectiveDx > 0);
            return;
        }

        // Drag-режим
        if (st.mode === 'drag') {
            e.preventDefault();
            st.moved = true;
            st.clone.style.left = (e.clientX - st.grabOffsetX) + 'px';
            st.clone.style.top = (e.clientY - st.grabOffsetY) + 'px';
            // Находим карточку под курсором (исключая клон)
            st.clone.style.pointerEvents = 'none';
            const target = document.elementFromPoint(e.clientX, e.clientY);
            const newHover = target ? target.closest('#deviceFavoritesContent .fav-card') : null;
            if (newHover !== st.hoverCard) {
                if (st.hoverCard) st.hoverCard.classList.remove('fav-card-drag-over');
                if (newHover && newHover !== st.card) newHover.classList.add('fav-card-drag-over');
                st.hoverCard = newHover;
            }
        }
    },

    _onFavPtrUp: function(e) {
        const st = KipFav._favInteractState;
        if (!st) return;
        clearTimeout(st.timer);

        // Режим ручного скролла — просто очищаем состояние
        if (st.mode === 'scroll') {
            KipFav._cleanupFavInteract();
            return;
        }

        // Swipe-завершение
        if (st.mode === 'swipe') {
            const threshold = st.width * KipFav._FAV_SWIPE_RATIO;
            const shouldDelete = Math.abs(st.currentDx) > threshold;
            if (shouldDelete) {
                const devId = st.cell.getAttribute('data-fav-id');
                const direction = st.currentDx < 0 ? -1 : 1;
                st.card.classList.remove('swipe-active');
                st.card.classList.add('swipe-removing');
                st.card.style.transform = 'translateX(' + (direction * st.width * 1.2) + 'px)';
                if (navigator.vibrate) navigator.vibrate(30);
                const savedCell = st.cell;
                KipFav._favInteractState = null;
                window.removeEventListener('pointermove', KipFav._onFavPtrMove);
                window.removeEventListener('pointerup', KipFav._onFavPtrUp);
                window.removeEventListener('pointercancel', KipFav._onFavPtrUp);
                if (savedCell) savedCell.classList.remove('swiping-left', 'swiping-right');
                setTimeout(function() {
                    KipFav.remove(devId);
                    KipFavNotes.remove(devId);
                    KipFav.initFavoritesPage();
                    window.showToast('Убрано из избранного');
                }, 250);
            } else {
                st.card.classList.remove('swipe-active');
                st.card.style.transform = 'translateX(0)';
                st.cell.classList.remove('swiping-left', 'swiping-right');
                KipFav._cleanupFavInteract();
            }
            return;
        }

        // Drag-завершение
        if (st.mode === 'drag') {
            let didReorder = false;
            if (st.moved && st.hoverCard && st.hoverCard !== st.card) {
                const hoverCell = st.hoverCard.closest('.fav-card-cell');
                if (hoverCell) {
                    const targetFavId = hoverCell.getAttribute('data-fav-id');
                    const order = KipFav.getOrder();
                    // Текущий список ключей в порядке DOM
                    const allKeys = [];
                    document.querySelectorAll('#deviceFavoritesContent .fav-card-cell').forEach(function(c) {
                        allKeys.push(c.getAttribute('data-fav-id'));
                    });
                    const fromIdx = allKeys.indexOf(st.favId);
                    const toIdx = allKeys.indexOf(targetFavId);
                    if (fromIdx !== -1 && toIdx !== -1 && fromIdx !== toIdx) {
                        allKeys.splice(fromIdx, 1);
                        allKeys.splice(toIdx, 0, st.favId);
                        KipFav.setOrder(allKeys);
                        didReorder = true;
                        if (navigator.vibrate) navigator.vibrate(15);
                    }
                }
            }
            KipFav._cleanupFavInteract();
            if (didReorder) {
                KipFav.initFavoritesPage();
            }
            return;
        }

        // Не было ни swipe, ни drag — обычный тап
        KipFav._cleanupFavInteract();
    },

    /** Старт перетаскивания (после долгого зажатия). */
    _startFavDrag: function(e) {
        const st = this._favInteractState;
        if (!st) return;
        st.mode = 'drag';
        const rect = st.card.getBoundingClientRect();
        st.grabOffsetX = st.startX - rect.left;
        st.grabOffsetY = st.startY - rect.top;
        // Клон карточки
        const clone = st.card.cloneNode(true);
        clone.classList.add('fav-card-clone');
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
        st.card.classList.add('fav-card-dragging');
        if (navigator.vibrate) navigator.vibrate(30);
        st.card.style.pointerEvents = 'none';
    },

    _cleanupFavInteract: function() {
        const st = this._favInteractState;
        if (!st) return;
        clearTimeout(st.timer);
        if (st.clone) st.clone.remove();
        if (st.card) {
            st.card.classList.remove('fav-card-dragging');
            st.card.style.pointerEvents = '';
        }
        if (st.hoverCard) st.hoverCard.classList.remove('fav-card-drag-over');
        this._favInteractState = null;
        window.removeEventListener('pointermove', this._onFavPtrMove);
        window.removeEventListener('pointerup', this._onFavPtrUp);
        window.removeEventListener('pointercancel', this._onFavPtrUp);
        window.removeEventListener('touchmove', this._onFavTouchMove);
    },

    // ----------------------------------------------------------
    // Свайп для добавления/удаления из избранного в списке приборов
    // ----------------------------------------------------------

    _devFavSvg: '<svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',

    /** Обернуть карточки приборов в ячейки для свайпа. Вызывать после рендера. */
    wrapDevCardsForFavSwipe: function() {
        var self = this;
        // Находим все .dev-card, которые ещё не обёрнуты
        var cards = document.querySelectorAll('.dev-list > .dev-card:not(.dev-card-fav-wrapped), .pb-section-body > .dev-card:not(.dev-card-fav-wrapped)');
        cards.forEach(function(card) {
            var devId = card.getAttribute('data-dev-id');
            if (!devId) return;
            var favKey = self._favKey('dev', devId);
            var isFav = self.hasItem(favKey);
            var cell = document.createElement('div');
            cell.className = 'dev-card-fav-cell' + (isFav ? ' is-fav' : '');
            cell.setAttribute('data-dev-id', devId);
            cell.setAttribute('data-fav-key', favKey);

            var favLabel = isFav ? 'Убрать' : 'В избранное';
            var bgLeft = document.createElement('div');
            bgLeft.className = 'dev-card-fav-bg dev-card-fav-bg-left';
            bgLeft.innerHTML = self._devFavSvg + '<span>' + favLabel + '</span>';

            var bgRight = document.createElement('div');
            bgRight.className = 'dev-card-fav-bg dev-card-fav-bg-right';
            bgRight.innerHTML = self._devFavSvg + '<span>' + favLabel + '</span>';

            card.parentNode.insertBefore(cell, card);
            cell.appendChild(bgLeft);
            cell.appendChild(bgRight);
            cell.appendChild(card);
            card.classList.add('dev-card-fav-wrapped');
        });
        // Вешаем обработчики
        self._attachKipFavSwipe();
    },

    /** Обернуть карточки (lock/valve/regulator) в ячейки для свайпа в избранное.
     *  @param {string} selector — CSS-селектор карточек (напр. '.lock-card')
     *  @param {string} type — тип избранного: 'lock'|'valve'|'reg'
     *  @param {string} idAttr — data-атрибут с ID (напр. 'data-lock-id') */
    wrapKipCardsForFavSwipe: function(selector, type, idAttr) {
        var self = this;
        var cards = document.querySelectorAll(selector + ':not(.dev-card-fav-wrapped)');
        cards.forEach(function(card) {
            var itemId = card.getAttribute(idAttr);
            if (!itemId) return;
            var favKey = self._favKey(type, itemId);
            var isFav = self.hasItem(favKey);
            var cell = document.createElement('div');
            cell.className = 'dev-card-fav-cell' + (isFav ? ' is-fav' : '');
            cell.setAttribute('data-fav-key', favKey);
            cell.setAttribute(idAttr, itemId);

            var favLabel = isFav ? 'Убрать' : 'В избранное';
            var bgLeft = document.createElement('div');
            bgLeft.className = 'dev-card-fav-bg dev-card-fav-bg-left';
            bgLeft.innerHTML = self._devFavSvg + '<span>' + favLabel + '</span>';

            var bgRight = document.createElement('div');
            bgRight.className = 'dev-card-fav-bg dev-card-fav-bg-right';
            bgRight.innerHTML = self._devFavSvg + '<span>' + favLabel + '</span>';

            card.parentNode.insertBefore(cell, card);
            cell.appendChild(bgLeft);
            cell.appendChild(bgRight);
            cell.appendChild(card);
            card.classList.add('dev-card-fav-wrapped');
        });
        self._attachKipFavSwipe();
    },

    _devFavSwipeState: null,
    _DEV_FAV_SWIPE_RATIO: 0.3,
    _DEV_FAV_SWIPE_THRESHOLD: 10,

    _attachKipFavSwipe: function() {
        var cells = document.querySelectorAll('.dev-card-fav-cell');
        var self = this;
        cells.forEach(function(cell) {
            if (cell._favSwipeBound) return;
            cell._favSwipeBound = true;
            cell.addEventListener('pointerdown', function(e) {
                if (e.button !== undefined && e.button !== 0) return;
                if (e.target.closest('.dev-card-fav-indicator')) return;
                // Найти карточку внутри ячейки (любой тип)
                var card = cell.querySelector('.dev-card, .lock-card, .valve-card, .regulator-card, .project-card');
                if (!card) return;
                var rect = card.getBoundingClientRect();
                self._devFavSwipeState = {
                    card: card,
                    cell: cell,
                    favKey: cell.getAttribute('data-fav-key') || cell.getAttribute('data-dev-id'),
                    startX: e.clientX,
                    startY: e.clientY,
                    width: rect.width,
                    currentDx: 0,
                    mode: 'idle'
                };
                window.addEventListener('pointermove', self._onDevFavPtrMove);
                window.addEventListener('pointerup', self._onDevFavPtrUp);
                window.addEventListener('pointercancel', self._onDevFavPtrUp);
            });
        });
    },

    _onDevFavPtrMove: function(e) {
        var st = KipFav._devFavSwipeState;
        if (!st) return;
        var dx = e.clientX - st.startX;
        var dy = e.clientY - st.startY;

        if (st.mode === 'idle') {
            if (Math.abs(dx) < KipFav._DEV_FAV_SWIPE_THRESHOLD && Math.abs(dy) < KipFav._DEV_FAV_SWIPE_THRESHOLD) return;
            if (Math.abs(dx) > Math.abs(dy) * 1.3) {
                st.mode = 'swipe';
                st.card.classList.add('swipe-active');
                if (navigator.vibrate) navigator.vibrate(5);
            } else {
                KipFav._cleanupDevFavSwipe();
                return;
            }
        }

        e.preventDefault();
        var effectiveDx = dx;
        if (Math.abs(dx) > st.width) {
            var over = Math.abs(dx) - st.width;
            effectiveDx = Math.sign(dx) * (st.width + over * 0.3);
        }
        st.currentDx = effectiveDx;
        st.card.style.transform = 'translateX(' + effectiveDx + 'px)';
        st.cell.classList.toggle('swiping-left', effectiveDx < 0);
        st.cell.classList.toggle('swiping-right', effectiveDx > 0);
    },

    _onDevFavPtrUp: function(e) {
        var st = KipFav._devFavSwipeState;
        if (!st) return;

        if (st.mode !== 'swipe') {
            KipFav._cleanupDevFavSwipe();
            return;
        }

        var threshold = st.width * KipFav._DEV_FAV_SWIPE_RATIO;
        var shouldToggle = Math.abs(st.currentDx) > threshold;

        if (shouldToggle) {
            var favKey = st.favKey;
            var direction = st.currentDx < 0 ? -1 : 1;
            st.card.classList.remove('swipe-active');
            st.card.classList.add('swipe-removing');
            st.card.style.transform = 'translateX(' + (direction * st.width * 1.2) + 'px)';
            if (navigator.vibrate) navigator.vibrate(30);
            var savedCell = st.cell;
            var savedCard = st.card;
            KipFav._devFavSwipeState = null;
            window.removeEventListener('pointermove', KipFav._onDevFavPtrMove);
            window.removeEventListener('pointerup', KipFav._onDevFavPtrUp);
            window.removeEventListener('pointercancel', KipFav._onDevFavPtrUp);
            if (savedCell) savedCell.classList.remove('swiping-left', 'swiping-right');
            setTimeout(function() {
                // Toggle favorite (используем составной ключ)
                var wasAdded = KipFav.toggle(favKey);
                // Обновить значок на карточке напрямую (без полного ререндера)
                if (savedCard) {
                    // Для приборов — значок внутри .dev-card-image-wrap
                    var wrap = savedCard.querySelector('.dev-card-image-wrap');
                    if (wrap) {
                        var existing = wrap.querySelector('.dev-card-fav-indicator');
                        if (wasAdded && !existing) {
                            var span = document.createElement('span');
                            span.className = 'dev-card-fav-indicator';
                            span.setAttribute('aria-label', 'В избранном');
                            span.setAttribute('title', 'В избранном');
                            span.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" stroke="none"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>';
                            var img = wrap.querySelector('.dev-card-image');
                            if (img && img.nextSibling) {
                                wrap.insertBefore(span, img.nextSibling);
                            } else {
                                wrap.appendChild(span);
                            }
                        } else if (!wasAdded && existing) {
                            existing.remove();
                        }
                    }
                    // Для lock/valve/regulator/project — значок в карточке (прямой дочерний или внутри header)
                    var existingIndicator = savedCard.querySelector(':scope > .dev-card-fav-indicator') || savedCard.querySelector('.project-card-header > .dev-card-fav-indicator');
                    if (wasAdded && !existingIndicator) {
                        var span2 = document.createElement('span');
                        span2.className = 'dev-card-fav-indicator';
                        span2.setAttribute('aria-label', 'В избранном');
                        span2.setAttribute('title', 'В избранном');
                        span2.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" stroke="none"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>';
                        savedCard.insertBefore(span2, savedCard.firstChild);
                    } else if (!wasAdded && existingIndicator) {
                        existingIndicator.remove();
                    }
                }
                // Обновить класс ячейки
                if (savedCell) savedCell.classList.toggle('is-fav', wasAdded);
                // Обновить подложку текст
                if (savedCell) {
                    var label = wasAdded ? 'Убрать' : 'В избранное';
                    savedCell.querySelectorAll('.dev-card-fav-bg span').forEach(function(s) { s.textContent = label; });
                }
                // Убрать анимацию
                var c = savedCard;
                if (c) { c.classList.remove('swipe-removing'); c.style.transform = ''; }
                // Тост
                KipFav.updateHeaderIcon();
                KipFav.updateDashboardButton();
                if (wasAdded) {
                    window.showToast('Добавлено в избранное', 'Открыть', function() { window.navigateTo('device-favorites'); });
                } else {
                    window.showToast('Убрано из избранного');
                }
            }, 250);
        } else {
            st.card.classList.remove('swipe-active');
            st.card.style.transform = 'translateX(0)';
            st.cell.classList.remove('swiping-left', 'swiping-right');
            KipFav._cleanupDevFavSwipe();
        }
    },

    _cleanupDevFavSwipe: function() {
        window.removeEventListener('pointermove', KipFav._onDevFavPtrMove);
        window.removeEventListener('pointerup', KipFav._onDevFavPtrUp);
        window.removeEventListener('pointercancel', KipFav._onDevFavPtrUp);
        KipFav._devFavSwipeState = null;
    },

    // ----------------------------------------------------------
    // Очистка «мёртвых» ссылок
    // ----------------------------------------------------------

    /** Удалить из избранного приборы, которых больше нет в devData.
     *  Возвращает количество удалённых. */
    cleanupStale: function() {
        this._load();
        var removed = 0;
        var liveDevIds = (typeof devData !== 'undefined' && devData && devData.devices)
            ? new Set(devData.devices.map(function(d) { return String(d['ID'] || ''); }))
            : null;
        var liveLockIds = (typeof lockData !== 'undefined' && lockData && lockData.lockouts)
            ? new Set(lockData.lockouts.map(function(d) { return String(d['ID'] || ''); }))
            : null;
        var liveValveIds = (typeof valveData !== 'undefined' && valveData && valveData.valves)
            ? new Set(valveData.valves.map(function(d) { return String(d['ID'] || ''); }))
            : null;
        var liveRegIds = (typeof regulatorData !== 'undefined' && regulatorData && regulatorData.regulators)
            ? new Set(regulatorData.regulators.map(function(d) { return String(d['ID'] || ''); }))
            : null;
        var liveProjIds = (typeof projectData !== 'undefined' && projectData && projectData.projects)
            ? new Set(projectData.projects.map(function(d) { return String(d['ID'] || ''); }))
            : null;
        for (var favKey in this._data) {
            if (!this._data.hasOwnProperty(favKey)) continue;
            var parsed = this._parseKey(favKey);
            var live = null;
            var knownType = true;
            if (parsed.type === 'dev') live = liveDevIds;
            else if (parsed.type === 'lock') live = liveLockIds;
            else if (parsed.type === 'valve') live = liveValveIds;
            else if (parsed.type === 'reg') live = liveRegIds;
            else if (parsed.type === 'proj') live = liveProjIds;
            else knownType = false;
            // Удаляем только если данные загружены (live !== null) и ID не найден,
            // либо если тип неизвестен (knownType = false).
            // Если данные не загружены (live === null) — пропускаем,
            // чтобы не удалить избранное при первом открытии до загрузки данных.
            if (!knownType || (live !== null && !live.has(parsed.id))) {
                delete this._data[favKey];
                removed++;
            }
        }
        if (removed > 0) {
            this._save();
            this.updateDashboardButton();
            this.updateHeaderIcon();
        }
        return removed;
    },

    // ----------------------------------------------------------
    // Очистить всё избранное
    // ----------------------------------------------------------

    /** Удалить все избранные приборы. */
    clearAll: function() {
        if (this.count() === 0) return;
        var self = this;
        window.kipConfirm('Удалить всё из избранного?', { danger: true }).then(function(ok) {
            if (!ok) return;
            self._load();
            self._data = {};
            self._save();
            KipFavNotes.clearAll();
            self.updateDashboardButton();
            self.updateHeaderIcon();
            self.initFavoritesPage();
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Избранное очищено');
            } else {
                window.showToast('Избранное очищено');
            }
        });
    },

    // ----------------------------------------------------------
    // UI: информационный значок избранного на карточке в списке
    // ----------------------------------------------------------

    /** Toggle избранное из карточки в списке. favKey — составной ключ. */
    toggleFromCard: function(favKey, ev) {
        if (ev) { ev.stopPropagation(); ev.preventDefault(); }
        if (!favKey) return;
        if (navigator.vibrate) navigator.vibrate(10);
        const wasAdded = this.toggle(favKey);
        // Обновить значок на карточке напрямую (без полного ререндера)
        if (ev && ev.target) {
            var cardEl = ev.target.closest('.dev-card, .lock-card, .valve-card, .regulator-card, .project-card');
            if (cardEl) {
                // Найти контейнер для индикатора — для project-card он внутри .project-card-header
                var wrap = cardEl.querySelector('.dev-card-image-wrap') || cardEl.querySelector('.project-card-header') || cardEl;
                var existing = wrap.querySelector('.dev-card-fav-indicator');
                if (wasAdded && !existing) {
                    var span = document.createElement('span');
                    span.className = 'dev-card-fav-indicator';
                    span.setAttribute('aria-label', 'В избранном');
                    span.setAttribute('title', 'В избранном');
                    span.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" stroke="none"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>';
                    wrap.appendChild(span);
                } else if (!wasAdded && existing) {
                    existing.remove();
                    // Также убрать значок заметки
                    var noteIcon = wrap.querySelector('.dev-card-fav-note-icon');
                    if (noteIcon) noteIcon.remove();
                }
                // Обновить десктопную кнопку-закладку на карточке
                var favBtn = cardEl.querySelector('.project-card-fav-btn');
                if (favBtn) favBtn.classList.toggle('active', wasAdded);
            }
        }
        // Также обновить значок в хедере и дашборд
        this.updateHeaderIcon();
        this.updateDashboardButton();
        if (wasAdded) {
            window.showToast('Добавлено в избранное', 'Открыть', function() { window.navigateTo('device-favorites'); });
        } else {
            window.showToast('Убрано из избранного');
        }
    },

    /** Сгенерировать HTML значков избранного и заметки для карточки в списке.
     *  @param {string} itemId — ID элемента
     *  @param {string} [type='dev'] — тип: 'dev'|'lock'|'valve'|'reg'|'proj' */
    /** HTML информационных значков (поверх карточки).
     *  Закладка — показывается только если элемент в избранном.
     *  Значок заметки — показывается рядом с закладкой, если есть заметка.
     *  Если не в избранном — возвращается пустая строка. */
    _cardFavBtnHtml: function(itemId, type) {
        var favKey = this._favKey(type || 'dev', itemId);
        var isActive = this.hasItem(favKey);
        if (!isActive) return '';
        var html = '<span class="dev-card-fav-indicator" aria-label="В избранном" title="В избранном">' +
               '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" stroke="none"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></span>';
        // Значок заметки (карандаш) — если есть заметка к этому элементу
        if (typeof KipFavNotes !== 'undefined' && KipFavNotes.get(favKey)) {
            html += '<span class="dev-card-fav-note-icon" aria-label="Есть заметка" title="Есть заметка">' +
                    '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></span>';
        }
        return html;
    },

    /** Кликабельная кнопка избранного на карточке (только десктоп).
     *  Показывается всегда — позволяет добавить/убрать из избранного.
     *  На мобильных скрыта через CSS media query. */
    _cardFavToggleHtml: function(itemId, type) {
        var favKey = this._favKey(type || 'dev', itemId);
        var isActive = this.hasItem(favKey);
        var cls = 'project-card-fav-btn' + (isActive ? ' active' : '');
        var safeKey = favKey.replace(/'/g, "\\'");
        return '<button type="button" class="' + cls + '" onclick="KipFav.toggleFromCard(\'' + safeKey + '\', event)" aria-label="Избранное" title="Добавить/убрать из избранного">' +
               '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>';
    }
};

// ============================================================
// KipFavNotes — Заметки к избранным приборам (localStorage)
// ============================================================
// Позволяет добавлять короткую текстовую заметку к прибору
// в разделе избранного (например, «проверить калибровку»).
// Структура: { "devId1": "текст заметки", ... }
// ============================================================

const KipFavNotes = {

    _STORAGE_KEY: 'kip8_device_fav_notes_v1',
    _data: null,

    _load: function() {
        if (this._data !== null) return;
        try {
            const raw = localStorage.getItem(this._STORAGE_KEY);
            this._data = raw ? JSON.parse(raw) : {};
        } catch (e) { this._data = {}; }
    },

    _save: function() {
        try { localStorage.setItem(this._STORAGE_KEY, JSON.stringify(this._data || {})); } catch (e) {}
    },

    /** Получить заметку для прибора (или пустую строку). */
    get: function(devId) {
        this._load();
        return this._data[devId] || '';
    },

    /** Установить заметку для прибора. Пустая строка = удалить. */
    set: function(devId, text) {
        this._load();
        text = String(text || '').trim();
        if (text) {
            this._data[devId] = text;
        } else {
            delete this._data[devId];
        }
        this._save();
    },

    /** Удалить заметку для прибора. */
    remove: function(devId) {
        this._load();
        if (this._data.hasOwnProperty(devId)) {
            delete this._data[devId];
            this._save();
        }
    },

    /** Показать диалог ввода заметки для прибора. */
    prompt: function(devId) {
        if (!devId) return;
        const current = this.get(devId);
        const self = this;
        window.kipPrompt('Заметка к прибору:', current).then(function(result) {
            // null = отмена; пустая строка = удалить заметку
            if (result === null) return;
            self.set(devId, result);
            // Обновить отображение заметки на странице избранного
            KipFav.initFavoritesPage();
        });
    },

    /** Очистить все заметки (при очистке избранного). */
    clearAll: function() {
        this._data = {};
        this._save();
    },

    /** Удалить заметки для элементов, которых нет в KipFav. */
    cleanupStale: function() {
        this._load();
        const favKeys = new Set(Object.keys(KipFav._data || {}));
        let removed = 0;
        for (const noteKey in this._data) {
            if (this._data.hasOwnProperty(noteKey) && !favKeys.has(noteKey)) {
                delete this._data[noteKey];
                removed++;
            }
        }
        if (removed > 0) this._save();
        return removed;
    }
};

export { KipFav, KipFavNotes };
export default KipFav;
