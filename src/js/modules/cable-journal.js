/**
 * @module cable-journal
 * KipCableJournal — кабельный журнал (CRUD через Apps Script)
 */
const KipCableJournal = {

    _columns: null,    // схема колонок
    _rows: [],          // текущие загруженные записи
    _total: 0,
    _canEdit: false,
    _searchTimer: null,
    _viewing: null,     // текущая просматриваемая запись ({_row: N, ...}) или null
    _editingRow: null,  // запись в режиме правки (мобильная форма) или null
    _cacheKey: 'kip8_cj_cache_v1',  // localStorage-ключ для кэша списка
    _cacheColsKey: 'kip8_cj_cols_v1',  // localStorage-ключ для кэша колонок

    // ============================================================
    // API вызовы
    // ============================================================
    _api: function(action, payload) {
        const token = window.KipAuth.getToken();
        if (!token) return Promise.reject(new Error('Нет токена — войдите в аккаунт'));
        // Используем KipAuth.api() — он корректно обрабатывает
        // Content-Type: text/plain (без CORS-preflight), ошибки сети,
        // и возвращает уже data.data (не весь объект ответа).
        return window.KipAuth.api(action, Object.assign({ token: token }, payload || {}));
    },

    // ============================================================
    // Вычислить canEdit: проверить роль пользователя vs editRoles.
    // Используется как fallback, если серверный эндпоинт (например,
    // getColumns в старой версии CableJournal.gs) не вернул canEdit
    // — иначе _canEdit сбросится в false и Админ не сможет добавить запись.
    // ============================================================
    _computeCanEdit: function(editRoles) {
        if (!Array.isArray(editRoles) || editRoles.length === 0) return false;
        let role = null;
        try {
            if (typeof window.KipAuth !== 'undefined' && window.KipAuth._cachedRole) {
                role = window.KipAuth._cachedRole;
            }
        } catch (e) { /* ignore */ }
        if (!role) return false;
        return editRoles.indexOf(role) !== -1;
    },

    // ============================================================
    // Инициализация страницы
    // ============================================================
    init: function() {
        // Кнопка "Добавить" видна только если canEdit
        const self = this;
        // 1. Мгновенно восстановить кэш колонок и данных — чтобы
        //    пользователь не смотрел на "Загрузка…" при каждом открытии.
        this._restoreCache();
        // 2. Фоново подгрузить свежую схему + данные.
        this._api('cableJournal.getColumns', {}).catch(e => { console.error('getColumns:', e); return null; })
            .then(function(columnsRes) {
                if (columnsRes) {
                    self._columns = columnsRes.columns;
                    self._persistColumns(columnsRes);
                    if (typeof columnsRes.canEdit === 'boolean') {
                        self._canEdit = columnsRes.canEdit;
                    } else if (columnsRes.editRoles) {
                        self._canEdit = self._computeCanEdit(columnsRes.editRoles);
                    }
                    document.getElementById('cjAddBtn').style.display = self._canEdit ? '' : 'none';
                }
                self.load();
            }).catch(function(err) {
                document.getElementById('cjList').innerHTML =
                    '<div style="padding:32px;text-align:center;color:var(--text-secondary,rgba(255,255,255,0.5));font-size:13px;">Ошибка: ' +
                    self._esc(err.message) + '</div>';
            });
    },

    // ============================================================
    // Восстановить кэш из localStorage (мгновенный рендер).
    // ============================================================
    _restoreCache: function() {
        try {
            const colsJson = localStorage.getItem(this._cacheColsKey);
            if (colsJson && !this._columns) {
                const colsRes = JSON.parse(colsJson);
                if (colsRes && colsRes.columns) {
                    this._columns = colsRes.columns;
                    if (typeof colsRes.canEdit === 'boolean') {
                        this._canEdit = colsRes.canEdit;
                    } else if (colsRes.editRoles) {
                        this._canEdit = this._computeCanEdit(colsRes.editRoles);
                    }
                    const btn = document.getElementById('cjAddBtn');
                    if (btn) btn.style.display = this._canEdit ? '' : 'none';
                }
            }
        } catch (e) { /* ignore parse errors */ }
        try {
            const dataJson = localStorage.getItem(this._cacheKey);
            if (dataJson) {
                const cached = JSON.parse(dataJson);
                if (cached && Array.isArray(cached.rows)) {
                    this._rows = cached.rows;
                    this._total = cached.total || cached.rows.length;
                    this._render();
                }
            }
        } catch (e) { /* ignore */ }
    },

    // ============================================================
    // Сохранить колонки в localStorage.
    // ============================================================
    _persistColumns: function(colsRes) {
        try {
            localStorage.setItem(this._cacheColsKey, JSON.stringify(colsRes));
        } catch (e) { /* quota or disabled */ }
    },

    // ============================================================
    // Сохранить данные в localStorage.
    // ============================================================
    _persistData: function(rows, total) {
        try {
            localStorage.setItem(this._cacheKey, JSON.stringify({ rows: rows, total: total, ts: Date.now() }));
        } catch (e) { /* quota or disabled */ }
    },

    // ============================================================
    // Загрузить список записей
    // (все записи на одной странице — пагинация убрана, Task 56)
    // Если уже есть кэш — рендерим его немедленно и тихо обновляем
    // в фоне (Task 58 — кэш в памяти приложения).
    // ============================================================
    load: function() {
        const self = this;
        const search = (document.getElementById('cjSearchInput').value || '').trim();

        // Если есть кэш и это не поисковый запрос — рендерим сразу.
        const hasCache = this._rows && this._rows.length > 0;
        const isSearch = !!search;
        if (!hasCache && !isSearch) {
            document.getElementById('cjList').innerHTML =
                '<div style="padding:32px;text-align:center;color:var(--text-secondary,rgba(255,255,255,0.5));font-size:13px;">Загрузка…</div>';
        } else if (isSearch) {
            // При поиске показываем loading (результаты могут отличаться от кэша)
            document.getElementById('cjList').innerHTML =
                '<div style="padding:32px;text-align:center;color:var(--text-secondary,rgba(255,255,255,0.5));font-size:13px;">Поиск…</div>';
        }

        this._api('cableJournal.list', {
            options: {
                search: search,
                limit: 1000  // максимум на стороне сервера (см. CableJournal.gs)
            }
        }).then(function(data) {
            self._rows = data.rows || [];
            self._total = data.total || 0;
            self._canEdit = !!data.canEdit;
            document.getElementById('cjAddBtn').style.display = self._canEdit ? '' : 'none';
            // Сохраняем в кэш только полный список (без поискового фильтра),
            // чтобы при следующем открытии пользователь видел все записи.
            if (!isSearch) {
                self._persistData(self._rows, self._total);
            }
            self._render();
        }).catch(function(err) {
            // При ошибке — если кэш есть, оставляем его; иначе показываем ошибку.
            if (!hasCache) {
                document.getElementById('cjList').innerHTML =
                    '<div style="padding:32px;text-align:center;color:var(--text-secondary,rgba(255,255,255,0.5));font-size:13px;">Ошибка: ' +
                    self._esc(err.message) + '</div>';
            }
        });
    },

    // ============================================================
    // Отрисовать список
    // (все записи на одной странице, группы свёрнуты по умолчанию — Task 56)
    // ============================================================
    _render: function() {
        const list = document.getElementById('cjList');

        if (this._rows.length === 0) {
            list.innerHTML = '<div style="padding:32px;text-align:center;color:var(--text-secondary,rgba(255,255,255,0.5));font-size:13px;">Записей нет</div>';
            return;
        }

        // ============================================================
        // Сгруппировать строки по "Отделение, производство".
        // Порядок групп — как встречаются в данных (сервер уже
        // отсортировал по отделению в list, но на всякий случай
        // сохраняем порядок первого вхождения).
        // ============================================================
        const groupOrder = [];
        const groups = {};
        this._rows.forEach(function(row) {
            // пустое отделение → '(без отделения)' для читаемости
            const g = (row.department && String(row.department).trim()) || '(без отделения)';
            if (!groups[g]) {
                groups[g] = [];
                groupOrder.push(g);
            }
            groups[g].push(row);
        });

        // Сортируем группы по алфавиту
        groupOrder.sort((a, b) => {
            const va = a.toString().toLowerCase();
            const vb = b.toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            return 0;
        });

        const self = this;
        let html = '';
        groupOrder.forEach(function(g) {
            const items = groups[g];
            // Каждая группа — отдельный сворачиваемый блок.
            // data-collapsed="true" — свёрнута по умолчанию (Task 56).
            // Клик по шапке toggle'ит состояние; CSS скрывает body и
            // поворачивает caret.
            html += '<div class="cj-group" data-collapsed="true">';
            html += '  <div class="cj-group-header" onclick="KipCableJournal.toggleGroup(this)">';
            html += '    <span class="cj-group-caret" aria-hidden="true">▼</span>';
            html += '    <span class="cj-group-header-title">' + self._esc(g) + '</span>';
            html += '    <span class="cj-group-header-count">' + items.length + ' ' +
                self._plural(items.length, ['запись', 'записи', 'записей']) + '</span>';
            html += '  </div>';
            html += '  <div class="cj-group-body">';

            // Карточки: только обозначение, трасса, проложен
            // (Task 55 — упрощённый preview).
            items.forEach(function(row) {
                const designation = self._esc(row.designation || '(без обозначения)');
                const start = self._esc(row.start || '');
                const end = self._esc(row.end || '');
                const markActual = self._esc(row.mark_actual || '');
                const coresActual = self._esc(row.cores_actual || '');
                const lengthActual = row.length_actual != null ? row.length_actual : '';

                html += '<div class="cj-item" onclick="KipCableJournal.openView(' + row._row + ')">';
                html += '  <div class="cj-item-header">';
                html += '    <span class="cj-item-designation">' + designation + '</span>';
                html += '  </div>';
                html += '  <div class="cj-item-meta">';
                if (start || end) {
                    html += '  <div class="cj-item-meta-row"><span class="cj-item-meta-label">трасса:</span> ' +
                        start + (start && end ? ' → ' : '') + end + '</div>';
                }
                if (markActual || coresActual || lengthActual) {
                    html += '  <div class="cj-item-meta-row"><span class="cj-item-meta-label">проложен:</span> ' +
                        markActual +
                        (coresActual ? ' · ' + coresActual : '') +
                        (lengthActual !== '' ? ' · ' + lengthActual + ' м' : '') +
                        '</div>';
                }
                html += '  </div>';
                html += '</div>';
            });

            html += '  </div>';  // .cj-group-body
            html += '</div>';    // .cj-group
        });
        list.innerHTML = html;
    },

    // ============================================================
    // Свернуть/развернуть группу карточек.
    // headerEl — элемент .cj-group-header, по которому кликнули.
    // Переключает data-collapsed у родительского .cj-group;
    // CSS скрывает .cj-group-body и поворачивает caret.
    //
    // Аккордеон (Task 58): при разворачивании текущей группы —
    // все остальные открытые группы сворачиваются. Только одна
    // группа может быть открыта одновременно.
    // ============================================================
    toggleGroup: function(headerEl) {
        const groupEl = headerEl ? headerEl.parentElement : null;
        if (!groupEl || !groupEl.classList.contains('cj-group')) return;
        const willCollapse = groupEl.getAttribute('data-collapsed') === 'true' ? false : true;
        // Если собираемся открыть (willCollapse=false) — закрыть все остальные.
        if (!willCollapse) {
            const list = document.getElementById('cjList');
            if (list) {
                const others = list.querySelectorAll('.cj-group[data-collapsed="false"]');
                for (let i = 0; i < others.length; i++) {
                    if (others[i] !== groupEl) {
                        others[i].setAttribute('data-collapsed', 'true');
                    }
                }
            }
        }
        groupEl.setAttribute('data-collapsed', willCollapse ? 'true' : 'false');
    },

    // Русская плюрализация для счётчика в шапке группы
    _plural: function(n, forms) {
        const m = n % 100;
        const m1 = m % 10;
        if (m >= 5 && m <= 20) return forms[2];
        if (m1 === 1) return forms[0];
        if (m1 >= 2 && m1 <= 4) return forms[1];
        return forms[2];
    },

    // ============================================================
    // Поиск с debounce
    // ============================================================
    handleSearchInput: function() {
        const self = this;
        if (this._searchTimer) clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(function() {
            self.load();
        }, 350);
    },

    // ============================================================
    // Toggle компактного поиска в шапке.
    // Кнопка-иконка переключает видимость поля ввода.
    // При раскрытии — фокус на поле; при скрытии — очистка + reload.
    // ============================================================
    toggleSearch: function() {
        const input = document.getElementById('cjSearchInput');
        const btn = document.getElementById('cjSearchToggleBtn');
        if (!input || !btn) return;
        const isOpen = input.classList.contains('search-open');
        if (isOpen) {
            // Закрыть
            input.classList.remove('search-open');
            input.removeAttribute('open');
            btn.classList.remove('active');
            if (input.value) {
                input.value = '';
                this.load();
            }
        } else {
            // Открыть
            input.classList.add('search-open');
            input.setAttribute('open', '');
            btn.classList.add('active');
            setTimeout(function() { try { input.focus(); } catch (e) {} }, 30);
        }
    },

    // ============================================================
    // Открыть страницу просмотра записи (read-only).
    // Редактирование и удаление сохранённых записей в приложении
    // запрещены (Task 57) — клик по карточке ведёт на отдельную
    // страницу page-cable-journal-view, где поля показаны как текст.
    // ============================================================
    openView: function(rowNum) {
        const row = this._rows.find(function(r) { return r._row === rowNum; });
        if (!row) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Запись не найдена');
            }
            return;
        }
        this._viewing = row;
        window.navigateTo('cable-journal-view');
    },

    // ============================================================
    // Инициализация страницы просмотра (вызывается из navigateTo)
    // ============================================================
    initViewPage: function() {
        const self = this;
        const fieldsEl = document.getElementById('cjViewFields');
        const titleEl = document.getElementById('cjViewTitle');

        // Если запись не выбрана — показываем ошибку
        if (!this._viewing) {
            if (fieldsEl) fieldsEl.innerHTML = '<div class="admin-empty">Запись не выбрана. Вернитесь к списку.</div>';
            if (titleEl) titleEl.textContent = 'Запись';
            return;
        }

        const row = this._viewing;

        // Заголовок — обозначение кабеля (или № записи как fallback)
        if (titleEl) {
            titleEl.textContent = row.designation || ('Запись №' + (row.num || '?'));
        }

        // Если колонки ещё не загружены — подтянем их
        if (!this._columns) {
            if (fieldsEl) fieldsEl.innerHTML = '<div class="admin-empty">Загрузка полей…</div>';
            this._api('cableJournal.getColumns', {}).then(function(res) {
                if (res && res.columns) self._columns = res.columns;
                self._renderViewPage();
            }).catch(function(err) {
                if (fieldsEl) fieldsEl.innerHTML = '<div class="admin-empty">Ошибка загрузки полей: ' + (err.message || err) + '</div>';
            });
        } else {
            this._renderViewPage();
        }
    },

    // ============================================================
    // Отрисовать поля страницы просмотра (read-only текст)
    // ============================================================
    _renderViewPage: function() {
        const self = this;
        const fieldsEl = document.getElementById('cjViewFields');
        if (!fieldsEl || !this._viewing) return;

        // Порядок полей — как в Google Sheets. Группа — для чередующегося
        // фона строки (как в карточке блокировки: lock-row-group-N).
        const order = [
            { key: 'designation',   group: 1 },
            { key: 'start',         group: 1 },
            { key: 'end',           group: 1 },
            { key: 'section',       group: 1 },
            { key: 'mark_project',  group: 2 },
            { key: 'cores_project', group: 2 },
            { key: 'length_project',group: 2 },
            { key: 'mark_actual',   group: 3 },
            { key: 'cores_actual',  group: 3 },
            { key: 'length_actual', group: 3 },
            { key: 'department',    group: 4 },
            { key: 'purpose',       group: 4 },
            { key: 'project_no',    group: 4 },
            { key: 'added_at',      group: 4 }
        ];

        // Карточка в стиле «строки во всю ширину, без подложки»:
        // .cj-view-fields > .cj-view-row.cj-view-group-N
        //   > .cj-view-label + .cj-view-value
        // Пустые поля пропускаются (как в lockRenderDetail).
        let rowsHtml = '';
        order.forEach(function(item) {
            rowsHtml += self._renderViewField(item.key, item.group);
        });
        // Кнопки правки/удаления — в нижний бар (cjViewBottomBar)
        const bottomBar = document.getElementById('cjViewBottomBar');
        if (bottomBar) {
            if (this._canEdit) {
                bottomBar.innerHTML =
                    '<button type="button" class="cj-view-bottom-bar-btn cj-view-bottom-bar-btn-edit" onclick="KipCableJournal.openEdit()">Править</button>';
            } else {
                bottomBar.innerHTML = '';
            }
        }
        fieldsEl.innerHTML = rowsHtml;
    },

    // ============================================================
    // Сгенерировать одну строку карточки просмотра (label + значение)
    // ============================================================
    _renderViewField: function(key, group) {
        const col = this._columns.find(function(c) { return c.key === key; });
        if (!col) return '';
        const val = this._viewing ? this._viewing[key] : '';
        const raw = (val === null || val === undefined || val === '') ? '' : String(val);
        // Пустые поля пропускаем — карточка показывает только заполненные
        // данные. Также пропускаем текстовые заглушки «Нет данных»,
        // которые Google Sheets хранит в колонке «Дата добавления».
        if (raw === '' || raw === 'Нет данных') return '';
        // Длина — добавляем единицу измерения; дата — форматируем локально.
        let valHtml = this._esc(raw);
        if (key === 'length_project' || key === 'length_actual') {
            valHtml = this._esc(raw) + ' м';
        } else if (key === 'added_at') {
            valHtml = this._esc(this._formatDate(raw));
        }
        const grpCls = group ? ' cj-view-group-' + group : '';
        let html = '<div class="cj-view-row' + grpCls + '">';
        html += '<div class="cj-view-label">' + this._esc(col.label) + '</div>';
        html += '<div class="cj-view-value">' + valHtml + '</div>';
        html += '</div>';
        return html;
    },

    // ============================================================
    // Открыть страницу добавления записи
    // ============================================================
    openAdd: function() {
        if (!this._canEdit) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('У вас нет прав на добавление записей');
            }
            return;
        }
        // Сбросить режим правки — мы открываем форму добавления,
        // а не правки существующей записи. Без этого _editingRow
        // мог остаться от предыдущего openEdit() и initAddPage
        // отрендерил бы форму с данными правки вместо пустых полей.
        this._editingRow = null;
        window.navigateTo('cable-journal-add');
    },

    // ============================================================
    // Инициализация страницы добавления (вызывается из navigateTo)
    // Кэш: если колонки уже загружены (в init/_restoreCache) — мгновенно
    // рендерим форму, а фоном тихо обновляем options из сервера.
    // ============================================================
    initAddPage: function() {
        const self = this;
        const fieldsEl = document.getElementById('cjAddFields');
        const errEl = document.getElementById('cjAddError');
        const submitBtn = document.getElementById('cjAddSubmitBtn');
        const isEditing = !!this._editingRow;

        // Сбросить состояние
        if (errEl) errEl.classList.remove('show');
        if (submitBtn) {
            submitBtn.disabled = false;
            if (isEditing) {
                submitBtn.textContent = 'Сохранить';
                submitBtn.setAttribute('onclick', 'KipCableJournal.submitEditMobile()');
            } else {
                submitBtn.textContent = 'Добавить запись';
                submitBtn.setAttribute('onclick', 'KipCableJournal.submitAdd()');
            }
        }
        // Обновить заголовок страницы
        const titleEl = document.querySelector('#page-cable-journal-add .page-inline-header-title');
        if (titleEl) {
            titleEl.textContent = isEditing ? 'Правка записи' : 'Новая запись';
        }

        // Проверка прав (на случай если пользователь открыл URL напрямую)
        if (!this._canEdit) {
            if (fieldsEl) fieldsEl.innerHTML = '<div class="admin-empty">У вас нет прав на добавление записей</div>';
            if (submitBtn) submitBtn.disabled = true;
            return;
        }

        // 1. Если колонки уже есть в памяти — мгновенно рендерим форму
        //    из кэша, без показа «Загрузка полей…».
        if (this._columns && this._columns.length) {
            this._renderAddPage();
        } else {
            // Попытаться восстановить из localStorage (на случай если
            // пользователь зашёл сразу на страницу добавления без
            // посещения списка).
            this._restoreColumnsOnly();
            if (this._columns && this._columns.length) {
                this._renderAddPage();
            } else if (fieldsEl) {
                fieldsEl.innerHTML = '<div class="admin-empty">Загрузка полей…</div>';
            }
        }

        // 2. Фоном подгрузить свежие options (data validation могла
        //    измениться в Google Sheets). Если ответ отличается —
        //    перерисуем форму. Если ответ совпадает или сеть недоступна —
        //    пользователь работает с кэшем.
        this._api('cableJournal.getColumns', {}).then(function(res) {
            if (!res || !res.columns) return;
            // canEdit: сначала доверяем серверу; если сервер не вернул
            // поле (старая версия CableJournal.gs) — вычисляем из
            // editRoles и кэшированной роли пользователя.
            if (typeof res.canEdit === 'boolean') {
                self._canEdit = res.canEdit;
            } else if (res.editRoles) {
                self._canEdit = self._computeCanEdit(res.editRoles);
            }
            if (!self._canEdit) {
                if (fieldsEl) fieldsEl.innerHTML = '<div class="admin-empty">У вас нет прав на добавление записей</div>';
                if (submitBtn) submitBtn.disabled = true;
                return;
            }
            self._columns = res.columns;
            self._persistColumns(res);
            self._renderAddPage();
        }).catch(function(err) {
            // Если сеть недоступна, но кэш есть — пользователь продолжает
            // работать с кэшированной схемой. Если кэша нет — показываем ошибку.
            if (!self._columns || !self._columns.length) {
                if (fieldsEl) fieldsEl.innerHTML = '<div class="admin-empty">Ошибка загрузки полей: ' + (err.message || err) + '</div>';
            }
        });
    },

    // ============================================================
    // Восстановить только колонки из localStorage (без данных).
    // Используется на странице добавления, если пользователь зашёл
    // туда напрямую без посещения списка.
    // ============================================================
    _restoreColumnsOnly: function() {
        if (this._columns && this._columns.length) return;
        try {
            const colsJson = localStorage.getItem(this._cacheColsKey);
            if (colsJson) {
                const colsRes = JSON.parse(colsJson);
                if (colsRes && colsRes.columns) {
                    this._columns = colsRes.columns;
                    if (typeof colsRes.canEdit === 'boolean') {
                        this._canEdit = colsRes.canEdit;
                    } else if (colsRes.editRoles) {
                        this._canEdit = this._computeCanEdit(colsRes.editRoles);
                    }
                }
            }
        } catch (e) { /* ignore */ }
    },

    // ============================================================
    // Отрисовать поля страницы добавления
    // ============================================================
    _renderAddPage: function() {
        const self = this;
        const fieldsEl = document.getElementById('cjAddFields');
        if (!fieldsEl) return;

        const isEditing = !!this._editingRow;
        const editRow = this._editingRow;

        // Порядок полей — как в Google Sheets (без num — он авто-генерится
        // сервером в appendRow). added_at теперь в форме: поле type=date
        // с дефолтом «сегодня», сервер принимает значение или ставит now().
        const order = [
            'designation',
            'start',
            'end',
            'section',
            'mark_project',
            'cores_project',
            'length_project',
            'mark_actual',
            'cores_actual',
            'length_actual',
            'department',
            'purpose',
            'project_no',
            'added_at'
        ];

        let html = '';
        if (isEditing) {
            // Режим правки: рендерим поля с текущими значениями
            order.forEach(function(key) {
                const val = editRow ? editRow[key] : undefined;
                html += self._renderEditField(key, val);
            });
        } else {
            order.forEach(function(key) {
                html += self._renderField(key);
            });
        }
        fieldsEl.innerHTML = html;

        // Кнопки Сохранить / Отмена — в нижний бар (cjAddBottomBar)
        const addBar = document.getElementById('cjAddBottomBar');
        if (addBar) {
            if (isEditing) {
                addBar.innerHTML =
                    '<button type="button" id="cjAddSubmitBtn" class="cj-add-bottom-bar-btn cj-add-bottom-bar-btn-save" onclick="KipCableJournal.submitEdit()">Сохранить</button>' +
                    '<div class="cj-add-bottom-bar-divider"></div>' +
                    '<button type="button" class="cj-add-bottom-bar-btn cj-add-bottom-bar-btn-cancel" onclick="KipCableJournal.cancelEdit()">Отмена</button>' +
                    '<div class="cj-add-bottom-bar-divider"></div>' +
                    '<button type="button" class="cj-add-bottom-bar-btn cj-view-bottom-bar-btn-delete" onclick="KipCableJournal.confirmDelete()">Удалить</button>';
            } else {
                addBar.innerHTML =
                    '<button type="button" id="cjAddSubmitBtn" class="cj-add-bottom-bar-btn cj-add-bottom-bar-btn-save" onclick="KipCableJournal.submitAdd()">Добавить запись</button>' +
                    '<div class="cj-add-bottom-bar-divider"></div>' +
                    '<button type="button" class="cj-add-bottom-bar-btn cj-add-bottom-bar-btn-cancel" onclick="KipCableJournal.cancelAddOrEdit()">Отмена</button>';
            }
        }

        if (!isEditing) {
            // Восстановить черновик из localStorage (если он был).
            self._restoreDraft();
        }

        // Сохранять черновик при каждом изменении поля.
        const inputs = fieldsEl.querySelectorAll('[data-key]');
        for (let i = 0; i < inputs.length; i++) {
            inputs[i].addEventListener('input', function() { self._saveDraft(); });
            inputs[i].addEventListener('change', function() { self._saveDraft(); });
        }

        // Auto-resize для textarea: высота подстраивается под содержимое.
        // Пустая textarea остаётся узкой (1 строка), при вводе — растёт.
        const textareas = fieldsEl.querySelectorAll('textarea.cj-autoresize');
        for (let i = 0; i < textareas.length; i++) {
            const ta = textareas[i];
            const resize = function() {
                ta.style.height = 'auto';
                ta.style.height = (ta.scrollHeight) + 'px';
            };
            ta.addEventListener('input', resize);
            // Первичная подгонка под восстановленный черновик.
            resize();
        }
    },

    // ============================================================
    // Кэш черновика формы добавления (введённые значения).
    // Позволяет не потерять данные при случайном уходе со страницы
    // и сразу показать заполненные поля при возврате.
    // ============================================================
    _draftKey: 'kip8_cj_draft_v1',
    _saveDraft: function() {
        try {
            const data = {};
            const inputs = document.querySelectorAll('#cjAddFields [data-key]');
            for (let i = 0; i < inputs.length; i++) {
                const k = inputs[i].getAttribute('data-key');
                if (k) data[k] = inputs[i].value;
            }
            localStorage.setItem(this._draftKey, JSON.stringify(data));
        } catch (e) { /* ignore */ }
    },
    _restoreDraft: function() {
        try {
            const json = localStorage.getItem(this._draftKey);
            if (!json) return;
            const data = JSON.parse(json);
            if (!data || typeof data !== 'object') return;
            const inputs = document.querySelectorAll('#cjAddFields [data-key]');
            for (let i = 0; i < inputs.length; i++) {
                const k = inputs[i].getAttribute('data-key');
                if (k && data[k] !== undefined && data[k] !== null) {
                    inputs[i].value = data[k];
                }
            }
        } catch (e) { /* ignore */ }
    },
    _clearDraft: function() {
        try { localStorage.removeItem(this._draftKey); } catch (e) { /* ignore */ }
    },

    // ============================================================
    // Сохранить новую запись со страницы добавления
    // ============================================================
    submitAdd: function() {
        const self = this;
        const errEl = document.getElementById('cjAddError');
        const saveBtn = document.getElementById('cjAddSubmitBtn');
        if (errEl) errEl.classList.remove('show');

        if (!this._canEdit) {
            if (errEl) { errEl.textContent = 'У вас нет прав на добавление'; errEl.classList.add('show'); }
            return;
        }

        // Собрать данные из полей
        const data = {};
        const inputs = document.querySelectorAll('#cjAddFields [data-key]');
        for (let i = 0; i < inputs.length; i++) {
            const inp = inputs[i];
            const key = inp.getAttribute('data-key');
            const col = this._columns.find(function(c) { return c.key === key; });
            // added_at помечен как readOnly в SCHEMA, но в форме добавления
            // это поле type=date (с дефолтом «сегодня»). Разрешаем передачу.
            if (!col || (col.readOnly && key !== 'added_at')) continue;
            let v = inp.value.trim();
            if (col.type === 'number' && v !== '') {
                const n = parseFloat(v.replace(',', '.'));
                v = isNaN(n) ? v : n;
            }
            data[key] = v;
        }

        saveBtn.disabled = true;
        saveBtn.textContent = 'Добавление…';

        this._api('cableJournal.appendRow', { data: data }).then(function(res) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Запись добавлена (№' + res.num + ')');
            }
            saveBtn.disabled = false;
            saveBtn.textContent = 'Добавить запись';
            // Очистить черновик (успешное добавление — данные больше не нужны).
            self._clearDraft();
            // Вернуться к списку и обновить
            window.navigateTo('cable-journal-edit');
            setTimeout(function() {
                if (typeof KipCableJournal !== 'undefined') KipCableJournal.load();
            }, 80);
        }).catch(function(err) {
            if (errEl) {
                errEl.textContent = err.message || err;
                errEl.classList.add('show');
            }
            saveBtn.disabled = false;
            saveBtn.textContent = 'Добавить запись';
        });
    },

    // ============================================================
    // Открыть форму правки записи (мобильная — переход на cable-journal-add
    // с предзаполнением; десктоп — рендер формы в detail-panel)
    // ============================================================
    openEdit: function() {
        if (!this._canEdit || !this._viewing) return;
        // Сохраняем редактируемую запись в отдельный флаг
        this._editingRow = this._viewing;
        if (window.isDesktop()) {
            this._renderEditInDetailPanel();
        } else {
            // Мобильная: перейти на страницу добавления, но в режиме правки
            window.navigateTo('cable-journal-add');
        }
    },

    // ============================================================
    // Рендер формы правки в десктопной detail-panel
    // ============================================================
    _renderEditInDetailPanel: function() {
        const self = this;
        const row = this._editingRow;
        if (!row || !this._columns) return;
        const bodyEl = document.getElementById('detailPanelBody');
        if (!bodyEl) return;

        const cableTitle = row.designation || ('Запись №' + (row.num || '?'));
        let html = '<div class="dev-detail-card">';
        html += '<div class="ticket-detail-title" style="margin-bottom:14px;">Правка: ' + this._esc(cableTitle) + '</div>';
        html += '<div class="cj-add-fields" style="padding:0;">';

        const order = [
            'designation','start','end','section',
            'mark_project','cores_project','length_project',
            'mark_actual','cores_actual','length_actual',
            'department','purpose','project_no','added_at'
        ];
        for (const key of order) {
            html += this._renderEditField(key, row[key]);
        }
        html += '</div>';  // close .cj-add-fields
        html += '<div id="cjEditError" class="cj-edit-error"></div>';
        html += '</div>'; // close .dev-detail-card
        bodyEl.innerHTML = html;
        // Кнопки Сохранить / Отмена — в нижний бар detail-panel
        const footerEl = document.getElementById('detailPanelFooter');
        if (footerEl) {
            footerEl.innerHTML =
                '<button type="button" id="cjEditSubmitBtn" class="detail-footer-btn detail-footer-btn-edit" onclick="KipCableJournal.submitEdit()">Сохранить</button>' +
                '<div class="detail-footer-divider"></div>' +
                '<button type="button" class="detail-footer-btn" style="color:var(--text-secondary,rgba(255,255,255,0.65));" onclick="KipCableJournal.cancelEdit()">Отмена</button>' +
                '<div class="detail-footer-divider"></div>' +
                '<button type="button" class="detail-footer-btn detail-footer-btn-delete" onclick="KipCableJournal.confirmDelete()">Удалить</button>';
        }
    },

    // ============================================================
    // Рендер одного поля формы правки (аналог _renderField, но с текущим значением)
    // ============================================================
    _renderEditField: function(key, currentVal) {
        const col = this._columns.find(function(c) { return c.key === key; });
        if (!col) return '';
        if (key === 'num') return ''; // № п/п — серверный, не редактируется
        const id = 'cjEditField_' + key;
        const hasOptions = Array.isArray(col.options) && col.options.length > 0;
        const isSelectOnly = this._selectOnlyKeys.indexOf(key) !== -1;
        const val = (currentVal !== null && currentVal !== undefined) ? String(currentVal) : '';

        let html = '<div class="cj-field-group">';
        html += '<label class="cj-field-label" for="' + id + '">' + this._esc(col.label) + '</label>';

        if (isSelectOnly && hasOptions) {
            html += '<select id="' + id + '" data-key="' + key + '" class="cj-field-select">';
            html += '<option value="">—</option>';
            for (const opt of col.options) {
                const sel = (String(opt) === val) ? ' selected' : '';
                html += '<option value="' + this._esc(String(opt)) + '"' + sel + '>' + this._esc(String(opt)) + '</option>';
            }
            html += '</select>';
        } else if (col.type === 'number') {
            html += '<input type="number" id="' + id + '" data-key="' + key + '" class="cj-field-input" value="' + this._esc(val) + '" inputmode="decimal">';
        } else if (col.type === 'date') {
            html += '<input type="date" id="' + id + '" data-key="' + key + '" class="cj-field-input" value="' + this._esc(val) + '">';
        } else if (hasOptions && !isSelectOnly) {
            // combo: input + datalist
            html += '<input type="text" id="' + id + '" data-key="' + key + '" class="cj-field-combo" value="' + this._esc(val) + '" list="' + id + '_dl">';
            html += '<datalist id="' + id + '_dl">';
            for (const opt of col.options) {
                html += '<option value="' + this._esc(String(opt)) + '">';
            }
            html += '</datalist>';
        } else if (key === 'designation' || key === 'start' || key === 'end') {
            html += '<textarea id="' + id + '" data-key="' + key + '" class="cj-field-textarea" rows="1">' + this._esc(val) + '</textarea>';
        } else {
            html += '<input type="text" id="' + id + '" data-key="' + key + '" class="cj-field-input" value="' + this._esc(val) + '">';
        }

        html += '</div>';
        return html;
    },

    // ============================================================
    // Сохранить правку записи
    // ============================================================
    submitEdit: function() {
        const self = this;
        const errEl = document.getElementById('cjEditError');
        const saveBtn = document.getElementById('cjEditSubmitBtn');
        if (!this._canEdit || !this._editingRow) {
            if (errEl) { errEl.textContent = 'Нет прав на редактирование'; errEl.classList.add('show'); }
            return;
        }
        if (errEl) errEl.classList.remove('show');

        // Собрать данные из полей
        const data = {};
        const container = window.isDesktop()
            ? document.getElementById('detailPanelBody')
            : document.getElementById('cjAddFields');
        if (!container) return;
        const inputs = container.querySelectorAll('[data-key]');
        for (let i = 0; i < inputs.length; i++) {
            const inp = inputs[i];
            const key = inp.getAttribute('data-key');
            const col = this._columns.find(function(c) { return c.key === key; });
            if (!col || (col.readOnly && key !== 'added_at')) continue;
            let v = inp.value.trim();
            if (col.type === 'number' && v !== '') {
                const n = parseFloat(v.replace(',', '.'));
                v = isNaN(n) ? v : n;
            }
            data[key] = v;
        }

        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Сохранение…'; }

        const rowNum = this._editingRow._row;
        this._api('cableJournal.updateRow', { row: rowNum, data: data }).then(function(res) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Запись обновлена');
            }
            self._editingRow = null;
            // Обновить _viewing обновлёнными данными
            if (self._viewing && self._viewing._row === rowNum) {
                Object.assign(self._viewing, data);
            }
            if (window.isDesktop()) {
                // Перерисовать карточку в detail-panel
                window.cableRenderDetailInPanel();
            } else {
                window.navigateTo('cable-journal-view');
                setTimeout(function() { KipCableJournal.initViewPage(); }, 50);
            }
            // Обновить список
            setTimeout(function() { KipCableJournal.load(); }, 100);
        }).catch(function(err) {
            if (errEl) { errEl.textContent = err.message || err; errEl.classList.add('show'); }
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Сохранить'; }
        });
    },

    // ============================================================
    // Отмена правки — вернуться к просмотру
    // ============================================================
    cancelEdit: function() {
        this._editingRow = null;
        if (window.isDesktop()) {
            window.cableRenderDetailInPanel();
        } else {
            window.navigateTo('cable-journal-view');
            setTimeout(function() { KipCableJournal.initViewPage(); }, 50);
        }
    },

    // ============================================================
    // Отмена на мобильной странице добавления/правки
    // ============================================================
    cancelAddOrEdit: function() {
        if (this._editingRow) {
            this._editingRow = null;
            window.navigateTo('cable-journal-view');
            setTimeout(function() { KipCableJournal.initViewPage(); }, 50);
        } else {
            window.navigateTo('cable-journal-edit');
        }
    },

    // ============================================================
    // Подтверждение удаления записи
    // ============================================================
    confirmDelete: function() {
        if (!this._canEdit || !this._viewing) return;
        const designation = this._viewing.designation || ('Запись №' + (this._viewing.num || '?'));
        const msg = 'Удалить кабель «' + designation + '»?\nЭто действие нельзя отменить.';
        window.kipConfirm(msg, { danger: true }).then(function(ok) {
            if (ok) {
                this.submitDelete();
            }
        }.bind(this));
    },

    // ============================================================
    // Удалить запись
    // ============================================================
    submitDelete: function() {
        const self = this;
        if (!this._canEdit || !this._viewing) return;
        const rowNum = this._viewing._row;
        this._api('cableJournal.deleteRow', { row: rowNum }).then(function(res) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Запись удалена');
            }
            self._viewing = null;
            if (window.isDesktop()) {
                window.closeDetailPanel();
            }
            // Вернуться к списку и обновить
            window.navigateTo('cable-journal-edit');
            setTimeout(function() { KipCableJournal.load(); }, 100);
        }).catch(function(err) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Ошибка удаления: ' + (err.message || err));
            }
        });
    },

    // ============================================================
    // Сохранить правку записи (мобильная версия — форма на cable-journal-add)
    // ============================================================
    submitEditMobile: function() {
        const self = this;
        const errEl = document.getElementById('cjAddError');
        const saveBtn = document.getElementById('cjAddSubmitBtn');
        if (!this._canEdit || !this._editingRow) {
            if (errEl) { errEl.textContent = 'Нет прав на редактирование'; errEl.classList.add('show'); }
            return;
        }
        if (errEl) errEl.classList.remove('show');

        // Собрать данные из полей
        const data = {};
        const inputs = document.querySelectorAll('#cjAddFields [data-key]');
        for (let i = 0; i < inputs.length; i++) {
            const inp = inputs[i];
            const key = inp.getAttribute('data-key');
            const col = this._columns.find(function(c) { return c.key === key; });
            if (!col || (col.readOnly && key !== 'added_at')) continue;
            let v = inp.value.trim();
            if (col.type === 'number' && v !== '') {
                const n = parseFloat(v.replace(',', '.'));
                v = isNaN(n) ? v : n;
            }
            data[key] = v;
        }

        if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Сохранение…'; }

        const rowNum = this._editingRow._row;
        this._api('cableJournal.updateRow', { row: rowNum, data: data }).then(function(res) {
            if (typeof KipToast !== 'undefined' && KipToast.show) {
                KipToast.show('Запись обновлена');
            }
            self._editingRow = null;
            // Обновить _viewing обновлёнными данными
            if (self._viewing && self._viewing._row === rowNum) {
                Object.assign(self._viewing, data);
            }
            // Вернуться к просмотру
            window.navigateTo('cable-journal-view');
            setTimeout(function() { KipCableJournal.initViewPage(); }, 50);
            // Обновить список
            setTimeout(function() { KipCableJournal.load(); }, 100);
        }).catch(function(err) {
            if (errEl) { errEl.textContent = err.message || err; errEl.classList.add('show'); }
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Сохранить'; }
        });
    },
    // Поля, где ввод своего значения ЗАПРЕЩЁН — только выбор из списка.
    // Пользователь явно попросил оставить их обычными <select>:
    //   section    → «Участок трассы»
    //   department → «Отделение, производство»
    //   purpose    → «Назначение кабеля»
    // Остальные поля с options — гибрид (input + datalist): можно
    // выбрать из списка или ввести своё значение.
    _selectOnlyKeys: ['section', 'department', 'purpose'],

    _renderField: function(key, opts) {
        const self = this;
        const col = this._columns.find(function(c) { return c.key === key; });
        if (!col) return '';
        const id = 'cjAddField_' + key;
        const hasOptions = Array.isArray(col.options) && col.options.length > 0;
        const isSelectOnly = this._selectOnlyKeys.indexOf(key) !== -1;

        let html = '<div class="cj-field-group">';
        html += '<label class="cj-field-label" for="' + id + '">' + this._esc(col.label) + '</label>';

        if (key === 'added_at') {
            // Поле даты добавления: type=date с дефолтом «сегодня».
            // Сервер в appendRow использует это значение, если передано;
            // если поле пустое — сервер ставит текущую дату/время.
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            const todayStr = yyyy + '-' + mm + '-' + dd;
            html += '<input id="' + id + '" type="date" class="cj-field-input cj-field-date" data-key="' + key + '" value="' + todayStr + '">';
        } else if (hasOptions && isSelectOnly) {
            // Поле с выпадающим списком БЕЗ возможности ввести своё
            // значение: data validation Google Sheets или fallback
            // (уникальные значения из данных).
            html += '<select id="' + id + '" class="cj-field-input cj-field-select" data-key="' + key + '">';
            html += '<option value="">- выберите -</option>';
            col.options.forEach(function(v) {
                const sv = String(v);
                html += '<option value="' + self._esc(sv) + '">' + self._esc(sv) + '</option>';
            });
            html += '</select>';
        } else if (hasOptions) {
            // Гибридное поле: <input list> + <datalist>. Можно выбрать
            // из списка существующих значений или ввести своё. Применяется
            // ко всем полям с options, кроме явно запрещённых
            // (section / department / purpose).
            const listId = 'cjAddDatalist_' + key;
            html += '<input id="' + id + '" type="text" class="cj-field-input cj-field-combo" list="' + listId + '" data-key="' + key + '" placeholder="выберите или введите" autocomplete="off">';
            html += '<datalist id="' + listId + '">';
            col.options.forEach(function(v) {
                const sv = String(v);
                html += '<option value="' + self._esc(sv) + '"></option>';
            });
            html += '</datalist>';
        } else {
            // Длинные текстовые поля — textarea с auto-resize
            // (расширяется под содержимое через JS-обработчик input).
            const useTextarea = ['start', 'end', 'section', 'designation'].indexOf(key) !== -1;
            if (useTextarea) {
                html += '<textarea id="' + id + '" class="cj-field-textarea cj-autoresize" data-key="' + key + '" rows="1"></textarea>';
            } else {
                const type = col.type === 'number' ? 'number' : 'text';
                html += '<input id="' + id + '" type="' + type + '" class="cj-field-input" data-key="' + key + '" value="">';
            }
        }
        html += '</div>';
        return html;
    },

    // ============================================================
    // Утилиты
    // ============================================================
    _esc: function(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    _formatDate: function(s) {
        if (!s) return '';
        // Если значение — не дата (например, текст "Нет данных"),
        // new Date() вернёт Invalid Date. Возвращаем оригинальную строку.
        const d = new Date(s);
        if (isNaN(d.getTime())) return String(s);
        try {
            return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        } catch (e) { return s; }
    }
};

export { KipCableJournal };
export default KipCableJournal;
