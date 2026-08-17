/**
 * @module catalogs/devices
 * @description Devices (КИП ИОС) catalog — data loading, rendering, search,
 * pagination, type filter, sorted/grouped views, detail card, swipe navigation,
 * and «last update» date extraction from the ID=0 record.
 *
 * External dependencies (accessed via `window.*`):
 *   navigateTo, showToast, KipFav, isDesktop, parseLocaleNumber, formatNumber,
 *   devRenderDetailInPanel, openDetailPanel, closeDetailPanel,
 *   gdriveShareToDirect, kipPrompt,
 *   kipIsEmptyProjectNo, kipSplitProjectValues, kipSplitIdValues, kipRenderMultiLinks,
 *   kipIsEmptySbsNo, kipIsEmptySarNo,
 *   kipIsProjectLinkFilterActive, kipClearProjectLinkFilter, kipMatchesProjectFilter,
 *   kipRenderFilterBadge, kipBindFilterBadge,
 *   kipIsSbsLinkFilterActive, kipClearSbsLinkFilter, kipMatchesSbsFilter,
 *   kipRenderSbsFilterBadge, kipBindSbsFilterBadge,
 *   kipIsSarLinkFilterActive, kipClearSarLinkFilter, kipMatchesSarFilter,
 *   kipRenderSarFilterBadge, kipBindSarFilterBadge,
 *   kipProjectLinkFilter, kipSbsLinkFilter, kipSarLinkFilter,
 *   kipRenderSbsRelatedBlock, kipLoadAndUpdateSbsRelated,
 *   projectOpenByProjectNo, lockOpenBySbsNo, regulatorOpenBySarNo,
 *   updateDesktopBreadcrumb
 */

// ===== ПРИБОРЫ (КИП ИОС) =====
let devData = null;            // распарсенный JSON
let devLoaded = false;
let devFilterType = null;       // выбранный тип прибора (null = все)
const DEV_CACHE_KEY = 'kip8test_devices_cache';
const DEV_CACHE_VERSION = 'v1';
const DEV_DEFAULT_LIMIT = 50;   // сколько карточек показывать изначально

// Нормализация строки для поиска (без учёта регистра, лишних пробелов)
function devNorm(s) {
    return (s || '').toString().toLowerCase().replace(/\s+/g, ' ').trim();
}

// Экранирование HTML
function devEsc(s) {
    return (s || '').toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Подсветка совпадений в тексте
function devMark(text, query) {
    const safe = devEsc(text);
    if (!query) return safe;
    const q = devNorm(query);
    if (!q) return safe;
    const qEsc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const normText = (text || '').toString();
    const regex = new RegExp(qEsc, 'gi');
    let result = '';
    let lastIdx = 0;
    let m;
    while ((m = regex.exec(normText)) !== null) {
        const start = m.index;
        const end = start + m[0].length;
        result += devEsc(normText.slice(lastIdx, start));
        result += '<mark>' + devEsc(normText.slice(start, end)) + '</mark>';
        lastIdx = end;
        if (m.index === regex.lastIndex) regex.lastIndex++;
    }
    result += devEsc(normText.slice(lastIdx));
    return result;
}

// Поля для отображения в карточке (порядок = как в карточке)
const DEV_FIELDS = [
    { key: 'Предел измерения', label: 'Предел измерения', group: 1 },
    { key: 'Погрешность', label: 'Погрешность', group: 1 },
    { key: '__period__', label: 'Период ремонта', isCombined: true, group: 1 },
    { key: 'Оборудование', label: 'Оборудование', group: 2 },
    { key: 'Параметр', label: 'Параметр', group: 2 },
    { key: 'Место расположения', label: 'Место расположения', group: 2 },
    { key: 'Производство', label: 'Производство', group: 2 },
    { key: 'Позиция', label: 'Позиция', group: 3 },
    { key: '№ проекта', label: '№ проекта', group: 3 },
    { key: '№ СБС', label: '№ СБС', group: 3 },
    { key: '№ САР', label: '№ САР', group: 3 },
    { key: 'В перечне', label: 'В перечне', group: 3 },
    { key: 'В гр. ППР', label: 'В гр. ППР', group: 3 },
    { key: 'Технические характеристики', label: 'Тех. характеристики', group: 4 },
    { key: 'Примечания', label: 'Примечания', group: 4 },
    { key: 'Замечания', label: 'Замечания', group: 4 },
];

let devImages = {};  // не используется (base64 встроены в devices.json)

// SVG-заставка для приборов без картинки или при загрузке
const DEV_PLACEHOLDER_SVG = 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">' +
    '<rect width="100" height="100" rx="12" fill="rgba(199,150,74,0.06)"/>' +
    '<circle cx="50" cy="50" r="32" fill="none" stroke="rgba(199,150,74,0.35)" stroke-width="2.5"/>' +
    '<text x="50" y="56" text-anchor="middle" font-family="sans-serif" font-size="16" font-weight="700" fill="rgba(199,150,74,0.5)">КИП</text>' +
    '</svg>'
);

// Получить URL картинки для прибора.
// Поддерживаемые форматы поля «Изображение»:
//   1) base64 data URI (data:image/...) — встройка из старых JSON, используется напрямую.
//   2) Google Drive share-ссылка (https://drive.google.com/file/d/ID/view?usp=...)
//      — конвертируется через gdriveShareToDirect() в URL превью
//      (drive.google.com/thumbnail?id=...&sz=w800).
//   3) Прямой HTTPS-URL картинки — используется как есть.
//   4) Пустое значение или неизвестный формат — SVG-заставка «КИП».
function devGetImageUrl(dev) {
    const img = (dev['Изображение'] || '').trim();
    if (!img) return DEV_PLACEHOLDER_SVG;
    if (img.startsWith('data:image/')) return img;
    if (img.startsWith('http://') || img.startsWith('https://')) {
        const gdrive = window.gdriveShareToDirect(img);
        if (gdrive) return gdrive.thumb;
        return img;
    }
    return DEV_PLACEHOLDER_SVG;
}

async function devLoad() {
    if (devLoaded) return devData;
    try {
        const bust = '?v=' + Date.now();
        const resp = await fetch('data/devices.json' + bust, { cache: 'no-store' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        devData = await resp.json();
        // Сохраняем в localStorage
        try {
            localStorage.setItem('kip8test:' + DEV_CACHE_KEY, JSON.stringify(devData));
        } catch (e) {}
        devLoaded = true;
        return devData;
    } catch (e) {
        console.warn('Devices load from network failed, trying cache:', e);
        try {
            const cached = localStorage.getItem('kip8test:' + DEV_CACHE_KEY);
            if (cached) {
                devData = JSON.parse(cached);
                devLoaded = true;
                console.log('[devices] Используется кэш localStorage (офлайн)');
                return devData;
            }
        } catch (e2) {}
        return null;
    }
}

// Состояние: сколько карточек сейчас показано (для пагинации)
let devVisibleCount = DEV_DEFAULT_LIMIT;

function devRender() {
    const list = document.getElementById('devList');
    const info = document.getElementById('devInfo');
    if (!list || !info) return;

    const query = devNorm((document.getElementById('devSearchInput')?.value || '').trim());

    if (!devLoaded || !devData) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    // Фильтрация
    // Исключаем служебную запись с ID=0 (содержит дату изменения перечня)
    let filtered = devData.devices.filter(d => {
        const id = d['ID'];
        return id !== 0 && id !== '0' && String(id ?? '').trim() !== '0';
    });
    if (query) {
        filtered = filtered.filter(d =>
            DEV_FIELDS.some(f => devNorm(d[f.key] || '').includes(query))
        );
    }

    // Инфо
    info.textContent = '';

    if (filtered.length === 0) {
        list.innerHTML = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        return;
    }

    // Пагинация: показываем только первые devVisibleCount карточек
    const visible = filtered.slice(0, devVisibleCount);
    const remaining = filtered.length - visible.length;

    let html = '<div class="dev-list">';
    for (const dev of visible) {
        const devId = String(dev['ID'] ?? '');
        const name = dev['Наименование'] || '(без названия)';
        const type = dev['Тип'] || '';
        const number = dev['№ прибора'] || '';
        const place = dev['Место установки'] || '';
        const imgUrl = devGetImageUrl(dev);
        const finalImgUrl = imgUrl || DEV_PLACEHOLDER_SVG;

        html += '<div class="dev-card" data-dev-id="' + devEsc(devId) + '">';
        html += '<div class="dev-card-header" onclick="devOpenDetail(\'' + devEsc(devId) + '\')">';
        html += '<div class="dev-card-header-inner">';
        html += '<div class="dev-card-image-wrap">';
        html += '<img class="dev-card-image" src="' + devEsc(finalImgUrl) + '" alt="' + devEsc(name) + '" loading="lazy">';
        html += window.KipFav._cardFavBtnHtml(devId);
        html += '<div class="dev-card-name-overlay">' + devMark(name, query) + '</div>';
        html += '</div>'; // .dev-card-image-wrap
        html += '<div class="dev-card-text">';
        html += '<div class="dev-card-title">' + devMark(name, query) + '</div>';
        let subtitle = '';
        if (type) subtitle += type;
        if (number) subtitle += (subtitle ? ' · №' : '№') + number;
        if (place) subtitle += (subtitle ? ' · ' : '') + place;
        if (subtitle) {
            html += '<div class="dev-card-subtitle">' + devMark(subtitle, query) + '</div>';
        }
        html += '</div>'; // .dev-card-text
        html += '<div class="dev-card-info-block">';
        if (type) {
            html += '<div class="dev-card-info-row">' + devMark(type, query) + '</div>';
        }
        if (number) {
            html += '<div class="dev-card-info-row" style="color:#6aa6e0;font-weight:600;">№ ' + devMark(number, query) + '</div>';
        }
        if (place) {
            html += '<div class="dev-card-info-row">' + devMark(place, query) + '</div>';
        }
        html += '</div>'; // .dev-card-info-block
        html += '</div>'; // .dev-card-header-inner
        html += '</div>'; // .dev-card-header
        html += '</div>'; // .dev-card
    }
    html += '</div>'; // .dev-list
    // Кнопка "Показать ещё"
    if (remaining > 0) {
        html += '<div style="text-align:center; padding:12px;">';
        html += '<button type="button" class="pb-filter-btn" onclick="devShowMore()" style="border-color:rgba(199,150,74,0.35); background:rgba(199,150,74,0.06); color:#c7964a;">';
        html += 'Показать ещё ' + Math.min(50, remaining) + ' (осталось ' + remaining + ')';
        html += '</button>';
        html += '</div>';
    }
    list.innerHTML = html;
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapDevCardsForFavSwipe();
}

function devShowMore() {
    devVisibleCount += 50;
    devRender();
}

function devOpenDetail(devId) {
    if (!devId) return;
    if (navigator.vibrate) navigator.vibrate(15);
    window._devDetailId = devId;
    if (window.isDesktop()) {
        window.devRenderDetailInPanel();
    } else {
        window.navigateTo('device-detail');
    }
}

function devRenderDetail() {
    const devId = window._devDetailId;
    if (!devId || !devLoaded || !devData) return;
    const dev = devData.devices.find(d => String(d['ID'] ?? '') === String(devId));
    if (!dev) return;
    const titleEl = document.getElementById('deviceDetailTitle');
    const content = document.getElementById('deviceDetailContent');
    if (!titleEl || !content) return;
    const name = dev['Наименование'] || '(без названия)';
    titleEl.textContent = name;
    const imgUrl = devGetImageUrl(dev) || DEV_PLACEHOLDER_SVG;
    const type = dev['Тип'] || '';
    const number = dev['№ прибора'] || '';
    const place = dev['Место установки'] || '';
    let html = '<div class="dev-detail-card">';
    // Значок избранного в правом верхнем углу (виден только на десктопе)
    html += '<button type="button" class="dev-detail-fav-btn" onclick="KipFav.toggleFromDetail()" aria-label="Избранное" title="Добавить/убрать из избранного"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button>';
    // Верх: картинка слева (с Типом в нижней части поверх неё) + №/Место справа
    html += '<div class="dev-detail-top">';
    html += '<div class="dev-detail-image-wrap">';
    html += '<img class="dev-detail-image" src="' + devEsc(imgUrl) + '" alt="' + devEsc(name) + '">';
    if (type) {
        html += '<div class="dev-detail-type-overlay">' + devEsc(type) + '</div>';
    }
    html += '</div>'; // .dev-detail-image-wrap
    html += '<div class="dev-detail-meta">';
    if (number) {
        html += '<div class="dev-detail-meta-row">';
        html += '<div class="dev-detail-meta-label">№ прибора</div>';
        html += '<div class="dev-detail-meta-value dev-detail-meta-number">' + devEsc(number) + '</div>';
        html += '</div>';
    }
    if (place) {
        html += '<div class="dev-detail-meta-row">';
        html += '<div class="dev-detail-meta-label">Место установки</div>';
        html += '<div class="dev-detail-meta-value">' + devEsc(place) + '</div>';
        html += '</div>';
    }
    html += '</div>'; // .dev-detail-meta
    html += '</div>'; // .dev-detail-top
    html += '<div class="dev-detail-rows">';
    for (const f of DEV_FIELDS) {
        let val = '';
        if (f.isCombined) {
            const dateRaw = dev['Дата'] || '';
            const vidVal = dev['Вид ремонта'] || '';
            const perVal = dev['Период ремонта'] || '';
            const dateFormatted = dateRaw ? devFormatDate(dateRaw) : '';
            const parts = [dateFormatted, vidVal, perVal].filter(p => p);
            val = parts.join(' ');
        } else {
            val = dev[f.key];
        }
        if (val === undefined || val === null || val === '') continue;
        const cls = f.class ? ' ' + f.class : '';
        const grpCls = f.group ? ' dev-row-group-' + f.group : '';
        html += '<div class="dev-card-row' + grpCls + '">';
        html += '<div class="dev-card-label">' + devEsc(f.label) + '</div>';
        // Для поля «№ проекта» — кликабельная ссылка в карточку проекта
        // (только если значение не пустое/«Нет данных»).
        // Если значение содержит несколько номеров (через ',' или ';'),
        // каждое число становится отдельной кликабельной ссылкой.
        if (f.key === '№ проекта' && !window.kipIsEmptyProjectNo(val)) {
            const parts = window.kipSplitProjectValues(val);
            html += '<div class="dev-card-value' + cls + ' kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'project', devEsc);
            html += '</div>';
        } else if (f.key === '№ СБС' && !window.kipIsEmptySbsNo(val)) {
            const parts = window.kipSplitIdValues(val);
            html += '<div class="dev-card-value' + cls + ' kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'sbs', devEsc);
            html += '</div>';
        } else if (f.key === '№ САР' && !window.kipIsEmptySarNo(val)) {
            const parts = window.kipSplitIdValues(val);
            html += '<div class="dev-card-value' + cls + ' kip-link-group">';
            html += window.kipRenderMultiLinks(parts, 'sar', devEsc);
            html += '</div>';
        } else {
            html += '<div class="dev-card-value' + cls + '">' + devEsc(String(val)) + '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    content.innerHTML = html;
    // Привязка кликов по ссылкам «№ проекта» (безопасно: через data-атрибут)
    content.querySelectorAll('[data-project-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.projectOpenByProjectNo(this.getAttribute('data-project-link'));
        });
    });
    // Привязка кликов по ссылкам «№ СБС» → карточка блокировки
    content.querySelectorAll('[data-sbs-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.lockOpenBySbsNo(this.getAttribute('data-sbs-link'));
        });
    });
    // Привязка кликов по ссылкам «№ САР» → карточка регулятора
    content.querySelectorAll('[data-sar-link]').forEach(function(el) {
        el.addEventListener('click', function() {
            window.regulatorOpenBySarNo(this.getAttribute('data-sar-link'));
        });
    });
    // Обновить значок избранного в хедере
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}



// === Фильтр по типу ===
function devUpdateFilterButton() {
    const btn = document.getElementById('devFilterType');
    const label = document.getElementById('devFilterTypeLabel');
    if (!btn || !label) return;
    if (devFilterType) {
        btn.classList.add('active');
        const shortType = devFilterType.length > 20 ? devFilterType.substring(0, 18) + '…' : devFilterType;
        label.textContent = 'Тип: ' + shortType;
    } else {
        btn.classList.remove('active');
        label.textContent = 'Все типы';
    }
}

function devToggleTypeFilter() {
    // Показать список всех уникальных типов — через prompt
    if (!devLoaded || !devData) return;
    const types = [...new Set(devData.devices.map(d => d['Тип'] || '').filter(t => t))];
    types.sort();
    let msg = 'Доступно типов: ' + types.length + '\n\nВведите тип или часть названия.\nДля сброса — оставьте пустым:\n\n';
    // Покажем первые 15 типов для ориентира
    for (let i = 0; i < Math.min(15, types.length); i++) {
        msg += '  ' + types[i] + '\n';
    }
    if (types.length > 15) msg += '  ... и ещё ' + (types.length - 15) + '\n';
    window.kipPrompt(msg, devFilterType || '').then(function(input) {
        if (input === null) return;
        const trimmed = input.trim();
        if (!trimmed) {
            devFilterType = null;
        } else {
            // Точное совпадение или частичное
            const exact = types.find(t => t.toLowerCase() === trimmed.toLowerCase());
            devFilterType = exact || trimmed;
        }
        // Сброс пагинации
        devVisibleCount = DEV_DEFAULT_LIMIT;
        if (navigator.vibrate) navigator.vibrate(25);
        devRender();
    });
}

// Конвертация Excel serial date (число дней с 1899-12-30) в формат DD.MM.YYYY
function devExcelDateToString(serial) {
    if (!serial) return '';
    const num = parseFloat(serial);
    if (isNaN(num)) return '';
    // Excel epoch: 1899-12-30 (с учётом бага 1900 високосного года)
    const ms = Math.round((num - 25569) * 86400 * 1000);  // 25569 = дней между 1899-12-30 и 1970-01-01
    const d = new Date(ms);
    if (isNaN(d.getTime())) return '';
    const dd = String(d.getUTCDate()).padStart(2, '0');
    const mm = String(d.getUTCMonth() + 1).padStart(2, '0');
    const yyyy = d.getUTCFullYear();
    return dd + '.' + mm + '.' + yyyy;
}

// Получить дату последнего изменения перечня из записи с ID=0
// (в столбце "Тип" хранится Excel serial date)
function devFormatDate(dateVal) {
    if (!dateVal) return '';
    // Если это число (Excel serial date)
    const num = parseFloat(dateVal);
    if (!isNaN(num) && num > 30000) {
        return devExcelDateToString(dateVal);
    }
    // Если строка в формате YYYY-MM-DD
    const str = String(dateVal).trim();
    const m = str.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m) {
        return m[3] + '.' + m[2] + '.' + m[1];
    }
    // Если уже в формате DD.MM.YYYY
    if (/^\d{2}\.\d{2}\.\d{4}$/.test(str)) {
        return str;
    }
    return str;
}
function devGetLastUpdateDate() {
    if (!devData || !devData.devices) return '';
    for (const d of devData.devices) {
        const id = d['ID'];
        // ID может быть числом 0 или строкой '0' — проверяем оба
        if (id === 0 || id === '0' || String(id ?? '').trim() === '0') {
            const typeVal = d['Тип'] || '';
            if (typeVal) {
                return devExcelDateToString(typeVal);
            }
        }
    }
    return '';
}

// Обновить строку "Последние изменения: <дата>" в родительском разделе КИП ИОС.
// Дата берётся из строки с ID=0, столбца "Тип" таблицы Приборы (devices.json),
// как реализовано в подразделе Приборы (devGetLastUpdateDate()).
// Вызывается при каждом переходе на страницу kip-ios.
async function kipIOSUpdateLastChange() {
    const span = document.getElementById('kip-ios-last-update');
    if (!span) return;
    let dateStr = '';
    // Принудительно тянем свежий devices.json с cache-bust —
    // devLoad() кэширует devData в памяти и не обновляет его,
    // поэтому без прямого fetch дата «Последние изменения»
    // (хранимая в строке ID=0, столбце «Тип» листа «Приборы_app»
    // как Excel serial date) никогда не обновится в текущей сессии.
    try {
        const bust = '?v=' + Date.now();
        const resp = await fetch('data/devices.json' + bust, { cache: 'no-store' });
        if (resp.ok) {
            const fresh = await resp.json();
            if (fresh && Array.isArray(fresh.devices)) {
                // Найти строку с ID=0 (дата последнего изменения перечня)
                const row0 = fresh.devices.find(d => {
                    const id = d['ID'];
                    return id === 0 || id === '0' || String(id ?? '').trim() === '0';
                });
                if (row0 && row0['Тип']) {
                    dateStr = (typeof devExcelDateToString === 'function')
                        ? devExcelDateToString(row0['Тип'])
                        : '';
                }
                // Обновляем кэш в памяти и localStorage, чтобы
                // другие разделы (Приборы и т.д.) тоже видели свежие данные.
                if (typeof devData !== 'undefined') {
                    devData = fresh;
                    devLoaded = true;
                    try {
                        localStorage.setItem('kip8test:' + DEV_CACHE_KEY, JSON.stringify(fresh));
                    } catch (eLS) {}
                }
            }
        }
    } catch (e) {
        // Офлайн / ошибка сети — fallback на кэшированный devLoad()
        if (typeof devLoad === 'function') {
            try { await devLoad(); } catch (e2) {}
        }
        if (typeof devGetLastUpdateDate === 'function') {
            dateStr = devGetLastUpdateDate();
        }
    }
    span.textContent = dateStr || '—';
}

function devPlural(n, forms) {
    const n10 = n % 10;
    const n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 10 || n100 >= 20)) return forms[1];
    return forms[2];
}

function devInit() {
    devLoaded = false;
    devData = null;
    devVisibleCount = DEV_DEFAULT_LIMIT;
    devLoad().then(() => devRender());
}

// ===== Кнопка Приборы на странице КИП ИОС: swipe с подложками + tap =====
// Паттерн как swipe-to-add на подразделах: карточка сдвигается,
// под ней видна цветная подложка с надписью сортировки.
// tap → по производствам, swipe ← (влево) → по типу, swipe → (вправо) → по наименованию
const DEV_SWIPE_THRESHOLD = 12;    // px до определения направления
const DEV_SWIPE_NAV_RATIO = 0.3;   // доля ширины для перехода
let devSwipeState = null;           // { el, cell, startX, startY, width, currentDx, active, moved }

function devInitEntryButton() {
    const btn = document.getElementById('devicesEntryBtn');
    if (!btn || btn.dataset.initialized) return;
    btn.dataset.initialized = '1';

    btn.addEventListener('pointerdown', onDevSwipePointerDown);
    // Тап без свайпа → по производствам
    btn.addEventListener('click', function() {
        if (devSwipeMoved) return;
        if (navigator.vibrate) navigator.vibrate(15);
        window.navigateTo('devices-prod');
    });
}

function onDevSwipePointerDown(e) {
    if (e.button !== undefined && e.button !== 0) return;
    const el = e.currentTarget;
    const cell = document.getElementById('devSwipeCell');
    if (!el || !cell) return;
    const rect = el.getBoundingClientRect();
    devSwipeState = {
        el: el,
        cell: cell,
        startX: e.clientX,
        startY: e.clientY,
        width: rect.width,
        currentDx: 0,
        active: false,
        moved: false
    };
    window.addEventListener('pointermove', onDevSwipePointerMove);
    window.addEventListener('pointerup', onDevSwipePointerUp);
    window.addEventListener('pointercancel', onDevSwipePointerUp);
}

function onDevSwipePointerMove(e) {
    if (!devSwipeState) return;
    const st = devSwipeState;
    const dx = e.clientX - st.startX;
    const dy = e.clientY - st.startY;
    if (!st.active) {
        if (Math.abs(dx) > DEV_SWIPE_THRESHOLD || Math.abs(dy) > DEV_SWIPE_THRESHOLD) {
            if (Math.abs(dx) > Math.abs(dy) * 1.5) {
                st.active = true;
                st.el.classList.add('swipe-active');
                st.el.style.pointerEvents = 'none';
                if (navigator.vibrate) navigator.vibrate(10);
            } else {
                // Вертикальное — скролл, отменяем
                cleanupDevSwipe();
                return;
            }
        } else {
            return;
        }
    }
    e.preventDefault();
    // Обновляем позицию карточки
    let effectiveDx = dx;
    if (Math.abs(dx) > st.width) {
        const overshoot = Math.abs(dx) - st.width;
        effectiveDx = Math.sign(dx) * (st.width + overshoot * 0.3);
    }
    st.currentDx = effectiveDx;
    st.el.style.transform = 'translateX(' + effectiveDx + 'px)';
    // Показываем подложку с противоположной стороны
    st.cell.classList.toggle('swiping-left',  effectiveDx < 0);
    st.cell.classList.toggle('swiping-right', effectiveDx > 0);
}

function onDevSwipePointerUp(e) {
    if (!devSwipeState) return;
    const st = devSwipeState;
    const threshold = st.width * DEV_SWIPE_NAV_RATIO;
    const shouldNav = st.active && Math.abs(st.currentDx) > threshold;
    const isLeft = st.currentDx < 0;

    if (shouldNav) {
        if (navigator.vibrate) navigator.vibrate(20);
        // Карточка уезжает за край
        st.el.classList.remove('swipe-active');
        st.el.style.transition = 'transform 0.2s ease-out, opacity 0.2s ease-out';
        st.el.style.transform = 'translateX(' + (isLeft ? '-100%' : '100%') + ')';
        st.el.style.opacity = '0';
        const targetPage = isLeft ? 'devices-type' : 'devices-name';
        setTimeout(function() {
            window.navigateTo(targetPage);
            // Сброс после перехода
            setTimeout(function() {
                st.el.style.transition = '';
                st.el.style.opacity = '';
                st.el.style.transform = '';
                st.el.style.pointerEvents = '';
                st.cell.classList.remove('swiping-left', 'swiping-right');
            }, 100);
        }, 200);
        devSwipeState = null;
        window.removeEventListener('pointermove', onDevSwipePointerMove);
        window.removeEventListener('pointerup', onDevSwipePointerUp);
        window.removeEventListener('pointercancel', onDevSwipePointerUp);
    } else {
        // Возвращаем карточку на место (с анимацией)
        st.el.classList.remove('swipe-active');
        st.el.style.transform = '';
        st.el.style.pointerEvents = '';
        st.cell.classList.remove('swiping-left', 'swiping-right');
        st.moved = st.active;
        cleanupDevSwipe();
    }
}

function cleanupDevSwipe() {
    if (!devSwipeState) return;
    const st = devSwipeState;
    st.el.classList.remove('swipe-active');
    st.el.style.pointerEvents = '';
    st.el.style.transform = '';
    if (st.cell) {
        st.cell.classList.remove('swiping-left', 'swiping-right');
    }
    // Если был активный свайп — блокируем следующий click
    if (st.active) {
        devSwipeMoved = true;
        setTimeout(function() { devSwipeMoved = false; }, 300);
    }
    devSwipeState = null;
    window.removeEventListener('pointermove', onDevSwipePointerMove);
    window.removeEventListener('pointerup', onDevSwipePointerUp);
    window.removeEventListener('pointercancel', onDevSwipePointerUp);
}
let devSwipeMoved = false;

// ===== Рендер приборов с сортировкой =====
// mode: 'type' — по типу, 'name' — по наименованию, 'prod' — по производствам
let devSortedVisibleCount = {};
let devGroupExpanded = {};  // { 'type|Группа': true, ... } — раскрытые группы в сортировке

function devRenderSorted(mode) {
    const ids = {
        type: { list: 'devTypeList', info: 'devTypeInfo', search: 'devTypeSearchInput', page: 'page-devices-type' },
        name: { list: 'devNameList', info: 'devNameInfo', search: 'devNameSearchInput', page: 'page-devices-name' },
        prod: { list: 'devProdList', info: 'devProdInfo', search: 'devProdSearchInput', page: 'page-devices-prod' },
    };
    const id = ids[mode];
    if (!id) return;
    const list = document.getElementById(id.list);
    const info = document.getElementById(id.info);
    if (!list || !info) return;

    if (!devLoaded || !devData) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    const query = devNorm((document.getElementById(id.search)?.value || '').trim());

    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по проекту
    if (query && window.kipIsProjectLinkFilterActive('devices')) {
        window.kipClearProjectLinkFilter('devices');
    }
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по «№ СБС»
    if (query && window.kipIsSbsLinkFilterActive('devices')) {
        window.kipClearSbsLinkFilter('devices');
    }
    // Если пользователь вручную ввёл поисковый запрос — сбросить фильтр по «№ САР»
    if (query && window.kipIsSarLinkFilterActive('devices')) {
        window.kipClearSarLinkFilter('devices');
    }
    // Если активен любой фильтр (проект/СБС/САР) — принудительно очистить
    // поисковые запросы на остальных вкладках сортировки, чтобы при переключении
    // вкладок фильтр не сбрасывался из-за «висящего» поискового запроса.
    if (window.kipIsProjectLinkFilterActive('devices') || window.kipIsSbsLinkFilterActive('devices') || window.kipIsSarLinkFilterActive('devices')) {
        const otherInputs = mode === 'prod'
            ? ['devTypeSearchInput', 'devNameSearchInput']
            : mode === 'type'
                ? ['devProdSearchInput', 'devNameSearchInput']
                : ['devProdSearchInput', 'devTypeSearchInput'];
        for (const iid of otherInputs) {
            const o = document.getElementById(iid);
            if (o && o.value) o.value = '';
        }
    }

    // Исключаем ID=0
    let filtered = devData.devices.filter(d => {
        const idv = d['ID'];
        return idv !== 0 && idv !== '0' && String(idv ?? '').trim() !== '0';
    });

    // Сортировка. Главная цель — обеспечить корректный порядок внутри
    // подгруппы (которая формируется ниже). Поэтому сортируем по полю
    // подгруппировки: для prod — по Наименованию, для name/type — по
    // Производству. Внутри подгруппы приборы получатся отсортированными
    // по Наименованию (как вторичная сортировка не делается, но это
    // приемлемо: одинаковые значения subgroupFieldKey уже рядом).
    const sortKey = mode === 'type' ? 'Тип' : mode === 'name' ? 'Наименование' : 'Производство';
    // Внутренняя сортировка для правильной группировки внутри основной группы.
    // Для prod — по Наименованию (нужно для подгруппировки), для name/type —
    // по Производству (также для подгруппировки). Дополнительно делаем
    // вторичную сортировку по «Наименованию», чтобы внутри подгруппы приборы
    // шли в алфавитном порядке.
    const subgroupFieldKeyForSort = mode === 'prod' ? 'Наименование' : 'Производство';
    filtered.sort((a, b) => {
        const va = (a[subgroupFieldKeyForSort] || '').toString().toLowerCase();
        const vb = (b[subgroupFieldKeyForSort] || '').toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        // Вторичная сортировка — по Наименованию внутри подгруппы.
        const na = (a['Наименование'] || '').toString().toLowerCase();
        const nb = (b['Наименование'] || '').toString().toLowerCase();
        if (na < nb) return -1;
        if (na > nb) return 1;
        return 0;
    });
    // Фильтр по «№ проекта» (из карточки проекта)
    if (window.kipIsProjectLinkFilterActive('devices')) {
        filtered = filtered.filter(d => window.kipMatchesProjectFilter(d, 'devices'));
    }
    // Фильтр по «№ СБС» (из карточки блокировки)
    if (window.kipIsSbsLinkFilterActive('devices')) {
        filtered = filtered.filter(d => window.kipMatchesSbsFilter(d, 'devices'));
    }
    // Фильтр по «№ САР» (из карточки регулятора)
    if (window.kipIsSarLinkFilterActive('devices')) {
        filtered = filtered.filter(d => window.kipMatchesSarFilter(d, 'devices'));
    }

    // Поиск
    if (query) {
        filtered = filtered.filter(d =>
            DEV_FIELDS.some(f => devNorm(d[f.key] || '').includes(query)) ||
            devNorm(d['Тип'] || '').includes(query) ||
            devNorm(d['№ прибора'] || '').includes(query) ||
            devNorm(d['Место установки'] || '').includes(query) ||
            devNorm(d['Наименование'] || '').includes(query)
        );
    }

    // Группировка. Для вкладки «по производству» группируем по полю
    // «Производство» (как и раньше), а внутри — подгруппировка по
    // «Наименованию». Для вкладок «по типу» и «по наименованию» —
    // основная группировка по выбранному полю (Тип / Наименование),
    // внутри — подгруппировка по производствам. Клик по заголовку
    // основной группы открывает отдельную страницу (dev-group) с
    // приборами этой группы, сгруппированными по производствам.
    const groupFieldKey = mode === 'type' ? 'Тип' : mode === 'name' ? 'Наименование' : 'Производство';
    // Подгруппировка: для prod — по Наименованию, для name/type — по Производству.
    const subgroupFieldKey = mode === 'prod' ? 'Наименование' : 'Производство';
    const groups = {};
    const groupOrder = [];
    for (const d of filtered) {
        const g = d[groupFieldKey] || '(без группы)';
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(d);
    }
    // Сортируем основные группы по алфавиту
    groupOrder.sort((a, b) => {
        const va = a.toString().toLowerCase();
        const vb = b.toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    // Инфо
    info.textContent = '';

    if (filtered.length === 0) {
        let emptyHtml = '';
        if (window.kipIsProjectLinkFilterActive('devices')) {
            emptyHtml += window.kipRenderFilterBadge('devices');
            emptyHtml += '<div class="pb-empty">По проекту №«' + devEsc(window.kipProjectLinkFilter.projectNo) + '» приборов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (window.kipIsSbsLinkFilterActive('devices')) {
            emptyHtml += window.kipRenderSbsFilterBadge('devices');
            emptyHtml += '<div class="pb-empty">По СБС №«' + devEsc(window.kipSbsLinkFilter.sbsNo) + '» приборов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (window.kipIsSarLinkFilterActive('devices')) {
            emptyHtml += window.kipRenderSarFilterBadge('devices');
            emptyHtml += '<div class="pb-empty">По САР №«' + devEsc(window.kipSarLinkFilter.sarNo) + '» приборов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        }
        list.innerHTML = emptyHtml;
        window.kipBindFilterBadge(list, 'devices', devRenderSorted);
        window.kipBindSbsFilterBadge(list, 'devices', devRenderSorted);
        window.kipBindSarFilterBadge(list, 'devices', devRenderSorted);
        return;
    }

    // Пагинация

    let html = '';
    // Бейдж активного фильтра по проекту (вверху списка)
    if (window.kipIsProjectLinkFilterActive('devices')) {
        html += window.kipRenderFilterBadge('devices');
    }
    // Бейдж активного фильтра по «№ СБС» (вверху списка)
    if (window.kipIsSbsLinkFilterActive('devices')) {
        html += window.kipRenderSbsFilterBadge('devices');
    }
    // Бейдж активного фильтра по «№ САР» (вверху списка)
    if (window.kipIsSarLinkFilterActive('devices')) {
        html += window.kipRenderSarFilterBadge('devices');
    }
    html += '<div class="dev-sorted-list' + (query ? ' searching' : '') + '">';

    for (const g of groupOrder) {
        const items = groups[g];
        const groupKey = mode + '|' + g;
        const isGroupExpanded = query ? true : (devGroupExpanded[groupKey] === true);

        // Групповой заголовок (сворачиваемый)
        html += '<div class="pb-section dev-group' + (isGroupExpanded ? ' expanded' : '') + '" data-group="' + devEsc(g) + '" data-mode="' + mode + '">';
        html += '<div class="pb-section-title dev-group-title" onclick="devToggleGroup(this)">';
        html += '<span class="pb-section-title-text">' + devMark(g, query) + '</span>';
        html += '<span class="pb-section-title-count">' + items.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';

        // Внутри основной группы всегда делаем подгруппировку:
        // - для mode='prod'   — по «Наименованию»
        // - для mode='name'   — по «Производству»
        // - для mode='type'   — по «Производству»
        // Заголовок подгруппы = значение subgroupFieldKey. Если это
        // «Наименование» — имя прибора дублирует заголовок подгруппы, и
        // в карточке его можно не показывать. Если это «Производство» —
        // имя прибора показываем в карточке как обычно.
        const hideNameInCard = (subgroupFieldKey === 'Наименование');
        const subgroups = {};
        const subgroupOrder = [];
        for (const dev of items) {
            const sg = dev[subgroupFieldKey] || (subgroupFieldKey === 'Наименование' ? '(без названия)' : '(без группы)');
            if (!subgroups[sg]) { subgroups[sg] = []; subgroupOrder.push(sg); }
            subgroups[sg].push(dev);
        }
        // Сортируем подгруппы алфавитно (по тексту)
        subgroupOrder.sort((a, b) => {
            const va = a.toString().toLowerCase();
            const vb = b.toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            return 0;
        });
        for (const sg of subgroupOrder) {
            const sgItems = subgroups[sg];
            html += '<div class="pb-section dev-group dev-subgroup static">';
            html += '<div class="pb-section-title">';
            html += '<span class="pb-section-title-text">' + devMark(sg, query) + '</span>';
            html += '<span class="pb-section-title-count">' + sgItems.length + '</span>';
            html += '<span class="pb-section-arrow"></span>';
            html += '</div>';
            html += '<div class="pb-section-body">';
            for (const dev of sgItems) {
                const devId = String(dev['ID'] ?? '');
                const name = dev['Наименование'] || '(без названия)';
                const type = dev['Тип'] || '';
                const number = dev['№ прибора'] || '';
                const place = dev['Место установки'] || '';
                const imgUrl = devGetImageUrl(dev);

                html += '<div class="dev-card" data-dev-id="' + devEsc(devId) + '" data-mode="' + mode + '">';
                html += '<div class="dev-card-header" onclick="devOpenDetail(\'' + devEsc(devId) + '\')">';
                html += '<div class="dev-card-header-inner">';
                html += '<div class="dev-card-image-wrap">';
                html += '<img class="dev-card-image" src="' + devEsc(imgUrl) + '" alt="' + devEsc(name) + '" loading="lazy">';
                html += window.KipFav._cardFavBtnHtml(devId);
                // Если имя прибора уже в заголовке подгруппы — overlay не нужен.
                if (!hideNameInCard) {
                    html += '<div class="dev-card-name-overlay">' + devMark(name, query) + '</div>';
                }
                html += '</div>';
                html += '<div class="dev-card-text">';
                // Имя показываем в карточке только если оно не дублирует заголовок подгруппы.
                if (!hideNameInCard) {
                    html += '<div class="dev-card-title">' + devMark(name, query) + '</div>';
                }
                let subtitle = '';
                if (type) subtitle += type;
                if (number) subtitle += (subtitle ? ' · №' : '№') + number;
                if (place) subtitle += (subtitle ? ' · ' : '') + place;
                if (subtitle) html += '<div class="dev-card-subtitle">' + devMark(subtitle, query) + '</div>';
                html += '</div>';
                html += '<div class="dev-card-info-block">';
                if (type) html += '<div class="dev-card-info-row">' + devMark(type, query) + '</div>';
                if (number) html += '<div class="dev-card-info-row" style="color:#6aa6e0;font-weight:600;">№ ' + devMark(number, query) + '</div>';
                if (place) html += '<div class="dev-card-info-row">' + devMark(place, query) + '</div>';
                html += '</div>';
                html += '</div>'; // header-inner
                html += '</div>'; // header
                html += '</div>'; // card
            }
            html += '</div>'; // pb-section-body (subgroup)
            html += '</div>'; // pb-section (subgroup)
        }
        html += '</div>'; // section-body
        html += '</div>'; // section

    }
    html += '</div>'; // dev-sorted-list


    list.innerHTML = html;
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapDevCardsForFavSwipe();
    // Привязка обработчика к кнопке ✕ в бейдже фильтра
    window.kipBindFilterBadge(list, 'devices', devRenderSorted);
    window.kipBindSbsFilterBadge(list, 'devices', devRenderSorted);
    window.kipBindSarFilterBadge(list, 'devices', devRenderSorted);
}


function devToggleGroup(titleEl) {
    const section = titleEl.closest('.pb-section');
    if (!section) return;
    const mode = section.getAttribute('data-mode') || 'type';
    const group = section.getAttribute('data-group');
    if (!group) return;
    if (navigator.vibrate) navigator.vibrate(25);
    window._devGroupCtx = { mode: mode, group: group };
    window.navigateTo('dev-group');
}

// Рендер отдельной страницы со списком приборов в выбранной группе
function devRenderGroup() {
    const ctx = window._devGroupCtx || {};
    const mode = ctx.mode || 'type';
    const group = ctx.group || '';
    const list = document.getElementById('devGroupList');
    const titleEl = document.getElementById('devGroupTitle');
    if (!list) return;
    if (titleEl) titleEl.textContent = group || 'Приборы';
    // На десктопе: заменить заголовок на полные хлебные крошки
    if (window.isDesktop()) window.updateDesktopBreadcrumb(null, group || 'Приборы');

    if (!devLoaded || !devData) {
        list.innerHTML = '<div class="pb-empty">Загрузка…</div>';
        return;
    }

    const sortKey = mode === 'type' ? 'Тип' : mode === 'name' ? 'Наименование' : 'Производство';
    // Группа определяется по полю, по которому шла основная группировка
    // на родительской странице (Тип / Наименование / Производство).
    // Клик по заголовку группы открывает эту страницу.
    const groupFieldKey = mode === 'type' ? 'Тип' : mode === 'name' ? 'Наименование' : 'Производство';
    // На странице группы — подгруппировка по другому полю:
    // для prod — по Наименованию, для name/type — по Производству.
    const subgroupFieldKey = mode === 'prod' ? 'Наименование' : 'Производство';
    // Фильтруем приборы: ID != 0 и принадлежат выбранной группе
    let items = devData.devices.filter(d => {
        const idv = d['ID'];
        if (idv === 0 || idv === '0' || String(idv ?? '').trim() === '0') return false;
        const g = d[groupFieldKey] || '(без группы)';
        return g === group;
    });
    // Применить активный фильтр (проект / СБС / САР), если он установлен.
    // Без этого при клике на группу из отфильтрованного списка будет показан
    // весь список приборов этой группы, а не только относящиеся к проекту.
    const hasFilter = window.kipIsProjectLinkFilterActive('devices')
        || window.kipIsSbsLinkFilterActive('devices')
        || window.kipIsSarLinkFilterActive('devices');
    if (hasFilter) {
        items = items.filter(d =>
            window.kipMatchesProjectFilter(d, 'devices')
            && window.kipMatchesSbsFilter(d, 'devices')
            && window.kipMatchesSarFilter(d, 'devices')
        );
    }
    items.sort((a, b) => {
        const va = (a['Наименование'] || '').toString().toLowerCase();
        const vb = (b['Наименование'] || '').toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    if (items.length === 0) {
        let emptyHtml = '';
        if (window.kipIsProjectLinkFilterActive('devices')) {
            emptyHtml += window.kipRenderFilterBadge('devices');
            emptyHtml += '<div class="pb-empty">В группе «' + devEsc(group) + '» по проекту №«' + devEsc(window.kipProjectLinkFilter.projectNo) + '» приборов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (window.kipIsSbsLinkFilterActive('devices')) {
            emptyHtml += window.kipRenderSbsFilterBadge('devices');
            emptyHtml += '<div class="pb-empty">В группе «' + devEsc(group) + '» по СБС №«' + devEsc(window.kipSbsLinkFilter.sbsNo) + '» приборов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else if (window.kipIsSarLinkFilterActive('devices')) {
            emptyHtml += window.kipRenderSarFilterBadge('devices');
            emptyHtml += '<div class="pb-empty">В группе «' + devEsc(group) + '» по САР №«' + devEsc(window.kipSarLinkFilter.sarNo) + '» приборов не найдено.<br>Нажмите ✕ в бейдже, чтобы сбросить фильтр.</div>';
        } else {
            emptyHtml = '<div class="pb-empty">В группе нет приборов.</div>';
        }
        list.innerHTML = emptyHtml;
        window.kipBindFilterBadge(list, 'devices', function() { devRenderGroup(); });
        window.kipBindSbsFilterBadge(list, 'devices', function() { devRenderGroup(); });
        window.kipBindSarFilterBadge(list, 'devices', function() { devRenderGroup(); });
        return;
    }

    // Сгруппировать приборы по subgroupFieldKey — раскрытая группа без сворачивания.
    // - mode='prod'  → subgroupFieldKey = 'Наименование' (как раньше)
    // - mode='name'  → subgroupFieldKey = 'Производство'
    // - mode='type'  → subgroupFieldKey = 'Производство'
    const hideNameInCard = (subgroupFieldKey === 'Наименование');
    const groups = {};
    const groupOrder = [];
    for (const dev of items) {
        const g = dev[subgroupFieldKey] || (subgroupFieldKey === 'Наименование' ? '(без названия)' : '(без группы)');
        if (!groups[g]) { groups[g] = []; groupOrder.push(g); }
        groups[g].push(dev);
    }
    // Алфавитный порядок групп
    groupOrder.sort((a, b) => {
        const va = a.toString().toLowerCase();
        const vb = b.toString().toLowerCase();
        if (va < vb) return -1;
        if (va > vb) return 1;
        return 0;
    });

    let html = '';
    // Бейдж активного фильтра (проект / СБС / САР) вверху страницы группы
    if (window.kipIsProjectLinkFilterActive('devices')) {
        html += window.kipRenderFilterBadge('devices');
    } else if (window.kipIsSbsLinkFilterActive('devices')) {
        html += window.kipRenderSbsFilterBadge('devices');
    } else if (window.kipIsSarLinkFilterActive('devices')) {
        html += window.kipRenderSarFilterBadge('devices');
    }
    html += '<div class="dev-sorted-list">';
    for (const g of groupOrder) {
        const gItems = groups[g];
        html += '<div class="pb-section dev-group dev-subgroup static">';
        html += '<div class="pb-section-title">';
        html += '<span class="pb-section-title-text">' + devEsc(g) + '</span>';
        html += '<span class="pb-section-title-count">' + gItems.length + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';
        for (const dev of gItems) {
            const devId = String(dev['ID'] ?? '');
            const name = dev['Наименование'] || '(без названия)';
            const type = dev['Тип'] || '';
            const number = dev['№ прибора'] || '';
            const place = dev['Место установки'] || '';
            const imgUrl = devGetImageUrl(dev);

            html += '<div class="dev-card" data-dev-id="' + devEsc(devId) + '" data-mode="' + mode + '">';
            html += '<div class="dev-card-header" onclick="devOpenDetail(\'' + devEsc(devId) + '\')">';
            html += '<div class="dev-card-header-inner">';
            html += '<div class="dev-card-image-wrap">';
            html += '<img class="dev-card-image" src="' + devEsc(imgUrl) + '" alt="' + devEsc(name) + '" loading="lazy">';
            html += window.KipFav._cardFavBtnHtml(devId);
            // Если имя уже в заголовке подгруппы (mode='prod') — overlay не нужен.
            if (!hideNameInCard) {
                html += '<div class="dev-card-name-overlay">' + devEsc(name) + '</div>';
            }
            html += '</div>';
            html += '<div class="dev-card-text">';
            // Имя показываем в карточке только если оно не дублирует заголовок подгруппы.
            if (!hideNameInCard) {
                html += '<div class="dev-card-title">' + devEsc(name) + '</div>';
            }
            let subtitle = '';
            if (type) subtitle += type;
            if (number) subtitle += (subtitle ? ' · №' : '№') + number;
            if (place) subtitle += (subtitle ? ' · ' : '') + place;
            if (subtitle) html += '<div class="dev-card-subtitle">' + devEsc(subtitle) + '</div>';
            html += '</div>';
            html += '<div class="dev-card-info-block">';
            if (type) html += '<div class="dev-card-info-row">' + devEsc(type) + '</div>';
            if (number) html += '<div class="dev-card-info-row" style="color:#6aa6e0;font-weight:600;">№ ' + devEsc(number) + '</div>';
            if (place) html += '<div class="dev-card-info-row">' + devEsc(place) + '</div>';
            html += '</div>';
            html += '</div>'; // header-inner
            html += '</div>'; // header
            html += '</div>'; // card
        }
        html += '</div>'; // pb-section-body
        html += '</div>'; // pb-section
    }
    html += '</div>';
    list.innerHTML = html;
    if (typeof window.KipFav !== 'undefined') window.KipFav.wrapDevCardsForFavSwipe();
    // Привязка обработчиков к кнопкам ✕ в бейджах фильтра
    window.kipBindFilterBadge(list, 'devices', function() { devRenderGroup(); });
    window.kipBindSbsFilterBadge(list, 'devices', function() { devRenderGroup(); });
    window.kipBindSarFilterBadge(list, 'devices', function() { devRenderGroup(); });
}

function devScrollToGroup(el) {
    if (!el) return;
    const mode = el.getAttribute('data-mode') || 'type';
    const ph = document.querySelector('#page-devices-' + mode + ' .page-inline-header');
    const stickyHeight = ph ? ph.offsetHeight : 56;
    const rect = el.getBoundingClientRect();
    const targetY = window.scrollY + rect.top - stickyHeight - 8;
    window.scrollTo({ top: Math.max(0, targetY), behavior: 'auto' });
}

function devShowMoreSorted(mode) {
    if (!devSortedVisibleCount[mode]) devSortedVisibleCount[mode] = 50;
    devSortedVisibleCount[mode] += 50;
    devRenderSorted(mode);
}

function devInitSorted(mode) {
    if (!devLoaded) {
        devLoad().then(() => devRenderSorted(mode));
    } else {
        devRenderSorted(mode);
    }
}

function devForceRefresh(mode) {
    devData = null;
    devLoaded = false;
    devInitSorted(mode);
    if (navigator.vibrate) navigator.vibrate(40);
}

// ===== Exports =====
export {
    devData,
    devLoaded,
    devInit,
    devInitEntryButton,
    devInitSorted,
    devForceRefresh,
    devRenderSorted,
    devOpenDetail,
    devRenderDetail,
    devToggleGroup,
    devRenderGroup,
    devLoad,
    devUpdateFilterButton,
    devToggleTypeFilter,
    devShowMore,
    devEsc,
    kipIOSUpdateLastChange
};
