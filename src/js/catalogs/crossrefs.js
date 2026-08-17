/**
 * @module catalogs/crossrefs
 * @description Cross-reference logic: project/SBS/SAR link filters, related-block
 * rendering, filter badges, and navigation helpers.  Data from devices/lockouts/
 * valves/regulators/projects modules is accessed via window.* bridges.
 * Lines ~7239–8260 of the original index.html.
 */

// ===== Обратные ссылки: фильтр списка раздела КИП ИОС по «№ проекта» =====
// Глобальное состояние фильтра. Когда не null — соответствующий
// *RenderSorted фильтрует записи по полю «№ проекта» (только полное
// совпадение номеров). В шапке списка показывается бейдж с возможностью
// сброса.
//
// Структура:
//   { projectNo: '551-115-008-АТХ-2', section: 'devices' }
// section — одно из: 'devices' | 'lockouts' | 'valves' | 'regulators' | 'cables'
let kipProjectLinkFilter = null;

// Установить фильтр и открыть страницу раздела КИП ИОС.
// section — идентификатор раздела; page — целевая страница (по умолчанию '*-prod').
function kipSetProjectLinkFilter(section, projectNo) {
    if (!section || projectNo == null) return;
    const raw = String(projectNo).trim();
    if (!raw || window.kipIsEmptyProjectNo(raw)) {
        if (navigator.vibrate) navigator.vibrate(10);
        alert('№ проекта не указан.');
        return;
    }
    // Карта section → страница по умолчанию. Если раздел неизвестен — молча выйти.
    const pages = {
        devices: 'devices-prod',
        lockouts: 'lockouts-prod',
        valves: 'valves-prod',
        regulators: 'regulators-prod',
    };
    const target = pages[section];
    if (!target) return;
    if (navigator.vibrate) navigator.vibrate(15);
    // Взаимное исключение: фильтр по «№ проекта», «№ СБС» и «№ САР» не могут
    // быть активны одновременно для одного раздела — сбросить остальные.
    if (kipSbsLinkFilter && kipSbsLinkFilter.section === section) {
        kipSbsLinkFilter = null;
    }
    if (typeof kipSarLinkFilter !== 'undefined' && kipSarLinkFilter && kipSarLinkFilter.section === section) {
        kipSarLinkFilter = null;
    }
    kipProjectLinkFilter = { projectNo: raw, section: section };
    // Сбросить поисковый запрос (если инпут уже существует)
    // Очистить поисковые запросы на ВСЕХ вкладках сортировки целевого раздела.
    // Для devices — это 3 вкладки (prod/type/name); для остальных — одна.
    const inputIds = {
        devices:    ['devProdSearchInput', 'devTypeSearchInput', 'devNameSearchInput'],
        lockouts:   ['lockProdSearchInput'],
        valves:     ['valveProdSearchInput'],
        regulators: ['regulatorProdSearchInput'],
    }[section] || [];
    for (const iid of inputIds) {
        const inp = document.getElementById(iid);
        if (inp) inp.value = '';
    }
    window.navigateTo(target);
}

// Сбросить активный фильтр (если он относится к данному раздела).
// Если section не передан — сбросить любой.
function kipClearProjectLinkFilter(section) {
    if (!kipProjectLinkFilter) return;
    if (!section || kipProjectLinkFilter.section === section) {
        kipProjectLinkFilter = null;
        if (navigator.vibrate) navigator.vibrate(8);
    }
}

// Проверить, активен ли фильтр для данного раздела.
function kipIsProjectLinkFilterActive(section) {
    return !!(kipProjectLinkFilter && kipProjectLinkFilter.section === section);
}

// Проверить, проходит ли запись фильтр по «№ проекта».
// Используется в *RenderSorted. Соответствие — только по полному
// совпадению номеров (после нормализации регистра/пробелов/ё→е).
function kipMatchesProjectFilter(item, section) {
    if (!kipProjectLinkFilter || kipProjectLinkFilter.section !== section) return true;
    const raw = kipProjectLinkFilter.projectNo;
    if (!raw) return true;
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');
    const r = norm(raw);
    const v = norm(item['№ проекта']);
    if (!v) return false;
    // Полное совпадение номеров
    return v === r;
}

// Рендер бейджа активного фильтра в шапке списка раздела.
// Возвращает HTML-строку (пустую, если фильтр не активен).
function kipRenderFilterBadge(section) {
    if (!kipIsProjectLinkFilterActive(section)) return '';
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const no = kipProjectLinkFilter.projectNo;
    return '<div class="kip-filter-badge" data-filter-badge="' + esc(section) + '">' +
           '<span class="kip-filter-badge-label">Проект:</span>' +
           '<span class="kip-filter-badge-value">' + esc(no) + '</span>' +
           '<button class="kip-filter-badge-clear" data-filter-clear="' + esc(section) + '" aria-label="Сбросить фильтр">✕</button>' +
           '</div>';
}

// Привязка обработчика к кнопке ✕ в бейдже.
// Вызывается после list.innerHTML = html в каждом *RenderSorted.
function kipBindFilterBadge(container, section, renderFn) {
    if (!container) return;
    const badge = container.querySelector('[data-filter-badge="' + section + '"]');
    if (!badge) return;
    const clear = badge.querySelector('[data-filter-clear]');
    if (clear) {
        clear.addEventListener('click', function(e) {
            e.stopPropagation();
            kipClearProjectLinkFilter(section);
            // Сбросить поисковые запросы на всех вкладках сортировки раздела
            const inputIds = {
                devices:    ['devProdSearchInput', 'devTypeSearchInput', 'devNameSearchInput'],
                lockouts:   ['lockProdSearchInput'],
                valves:     ['valveProdSearchInput'],
                regulators: ['regulatorProdSearchInput'],
            }[section] || [];
            for (const iid of inputIds) {
                const inp = document.getElementById(iid);
                if (inp) inp.value = '';
            }
            if (typeof renderFn === 'function') renderFn('prod');
        });
    }
}

// ===== Прямая навигация: клик по «№ СБС» в карточке прибора/клапана/регулятора =====
// Вспомогательная функция: считается ли значение «№ СБС» пустым/незаполненным.
// Для таких значений ссылка не рендерится в *RenderDetail, а в lockOpenBySbsNo
// показывается короткое сообщение вместо поиска.
// Возвращает true для: пусто, «Нет данных», «нет», «-», «—», «–», «н/д», «n/a».
function kipIsEmptySbsNo(val) {
    if (val == null) return true;
    const s = String(val).trim().toLowerCase().replace(/[ё]/g, 'е');
    if (!s) return true;
    const empties = ['нет данных', 'нет', '-', '—', '–', '—', 'н/д', 'n/a', 'na', 'null', 'undefined', 'нет сведений', 'нет сбс'];
    return empties.indexOf(s) !== -1;
}

// Открыть карточку блокировки по значению «№ СБС».
// Сначала пытаемся найти точное совпадение в lockData.lockouts по полю «№ СБС»,
// в fallback — по частичному совпадению. Если ничего не найдено — alert.
// При необходимости догружает lockouts.json.
async function lockOpenBySbsNo(sbsNo) {
    if (sbsNo == null) return;
    const raw = String(sbsNo).trim();
    if (!raw) return;
    if (kipIsEmptySbsNo(raw)) {
        if (navigator.vibrate) navigator.vibrate(10);
        alert('№ СБС не указан.');
        return;
    }
    if (navigator.vibrate) navigator.vibrate(15);

    // Догрузить lockouts.json, если ещё не загружен
    if (!window.lockLoaded || !window.lockData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/lockouts.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            window.lockData = await resp.json();
            window.lockLoaded = true;
            localStorage.setItem('lockoutsLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('lockOpenBySbsNo: ошибка загрузки lockouts.json:', e);
            alert('Не удалось загрузить данные блокировок. Проверьте соединение.');
            return;
        }
    }

    // Нормализация: нижний регистр, ё→е, схлопывание пробелов.
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');

    const items = window.lockData.lockouts || [];
    const r = norm(raw);

    // 1) Точное совпадение по «№ СБС»
    const exact = items.find(d => norm(d['№ СБС']) === r);
    if (exact && exact['ID'] != null && exact['ID'] !== '') {
        window.lockOpenDetail(exact['ID']);
        return;
    }

    // 2) Не найдено точное совпадение — показать сообщение.
    //    Частичное совпадение отключено: разные СБС могут содержать
    //    одинаковые подстроки (например, «123» и «1234» — разные СБС),
    //    поэтому соответствие определяется только по полному совпадению.
    alert('Блокировка с № СБС «' + raw + '» не найдена в базе блокировок.');
}

// ===== Обратные ссылки: фильтр списка раздела КИП ИОС по «№ СБС» =====
// Глобальное состояние фильтра. Когда не null — соответствующий
// *RenderSorted фильтрует записи по полю «№ СБС» (только полное совпадение
// номеров). В шапке списка показывается бейдж с возможностью сброса.
//
// Структура:
//   { sbsNo: 'СБС-123', section: 'devices' }
// section — одно из: 'devices' | 'valves' | 'regulators'
let kipSbsLinkFilter = null;

// Установить фильтр по «№ СБС» и открыть страницу раздела КИП ИОС.
function kipSetSbsLinkFilter(section, sbsNo) {
    if (!section || sbsNo == null) return;
    const raw = String(sbsNo).trim();
    if (!raw || kipIsEmptySbsNo(raw)) {
        if (navigator.vibrate) navigator.vibrate(10);
        alert('№ СБС не указан.');
        return;
    }
    const pages = {
        devices: 'devices-prod',
        valves: 'valves-prod',
        regulators: 'regulators-prod',
    };
    const target = pages[section];
    if (!target) return;
    if (navigator.vibrate) navigator.vibrate(15);
    // Взаимное исключение: фильтр по «№ СБС», «№ проекта» и «№ САР» не могут
    // быть активны одновременно для одного раздела — сбросить остальные.
    if (kipProjectLinkFilter && kipProjectLinkFilter.section === section) {
        kipProjectLinkFilter = null;
    }
    if (typeof kipSarLinkFilter !== 'undefined' && kipSarLinkFilter && kipSarLinkFilter.section === section) {
        kipSarLinkFilter = null;
    }
    kipSbsLinkFilter = { sbsNo: raw, section: section };
    const inputIds = {
        devices:    ['devProdSearchInput', 'devTypeSearchInput', 'devNameSearchInput'],
        valves:     ['valveProdSearchInput'],
        regulators: ['regulatorProdSearchInput'],
    }[section] || [];
    for (const iid of inputIds) {
        const inp = document.getElementById(iid);
        if (inp) inp.value = '';
    }
    window.navigateTo(target);
}

// Сбросить активный СБС-фильтр (если он относится к данному разделу).
function kipClearSbsLinkFilter(section) {
    if (!kipSbsLinkFilter) return;
    if (!section || kipSbsLinkFilter.section === section) {
        kipSbsLinkFilter = null;
        if (navigator.vibrate) navigator.vibrate(8);
    }
}

// Проверить, активен ли СБС-фильтр для данного раздела.
function kipIsSbsLinkFilterActive(section) {
    return !!(kipSbsLinkFilter && kipSbsLinkFilter.section === section);
}

// Проверить, проходит ли запись СБС-фильтр. Соответствие — только
// по полному совпадению номеров (после нормализации).
function kipMatchesSbsFilter(item, section) {
    if (!kipSbsLinkFilter || kipSbsLinkFilter.section !== section) return true;
    const raw = kipSbsLinkFilter.sbsNo;
    if (!raw) return true;
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');
    const r = norm(raw);
    const v = norm(item['№ СБС']);
    if (!v) return false;
    // Полное совпадение номеров
    return v === r;
}

// Рендер бейджа активного СБС-фильтра в шапке списка раздела.
// Возвращает HTML-строку (пустую, если фильтр не активен).
// Использует тот же CSS-класс .kip-filter-badge, что и проектный,
// но data-атрибут data-sbs-filter-badge отличает бейджи.
function kipRenderSbsFilterBadge(section) {
    if (!kipIsSbsLinkFilterActive(section)) return '';
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const no = kipSbsLinkFilter.sbsNo;
    return '<div class="kip-filter-badge" data-sbs-filter-badge="' + esc(section) + '">' +
           '<span class="kip-filter-badge-label">СБС:</span>' +
           '<span class="kip-filter-badge-value">' + esc(no) + '</span>' +
           '<button class="kip-filter-badge-clear" data-sbs-filter-clear="' + esc(section) + '" aria-label="Сбросить фильтр">✕</button>' +
           '</div>';
}

// Привязка обработчика к кнопке ✕ в бейдже СБС-фильтра.
function kipBindSbsFilterBadge(container, section, renderFn) {
    if (!container) return;
    const badge = container.querySelector('[data-sbs-filter-badge="' + section + '"]');
    if (!badge) return;
    const clear = badge.querySelector('[data-sbs-filter-clear]');
    if (clear) {
        clear.addEventListener('click', function(e) {
            e.stopPropagation();
            kipClearSbsLinkFilter(section);
            const inputIds = {
                devices:    ['devProdSearchInput', 'devTypeSearchInput', 'devNameSearchInput'],
                valves:     ['valveProdSearchInput'],
                regulators: ['regulatorProdSearchInput'],
            }[section] || [];
            for (const iid of inputIds) {
                const inp = document.getElementById(iid);
                if (inp) inp.value = '';
            }
            if (typeof renderFn === 'function') renderFn('prod');
        });
    }
}

// ===== Обратные ссылки: блок «Связанные записи» в карточке блокировки =====
// Конфигурация разделов для отображения обратных ссылок по «№ СБС».
// В карточке блокировки показываем связанные:
//   - Приборы (devices) — имеют поле «№ СБС»
//   - Клапаны (valves) — имеют поле «№ СБС»
//   - Регуляторы (regulators) — имеют поле «№ СБС»
// Блокировки, кабели — не показываем (в блокировках это собственный ID,
// в кабелях поля «№ СБС» нет).
const KIP_SBS_RELATED_SECTIONS = [
    { label: 'Приборы',    section: 'devices',    icon: 'П', color: '#6aa6e0' },
    { label: 'Клапаны',    section: 'valves',     icon: 'К', color: '#4a8a8c' },
    { label: 'Регуляторы', section: 'regulators', icon: 'Р', color: '#7e5ab8' },
];

// Подсчитать количество связанных записей для данного «№ СБС».
// Использует ту же логику совпадения, что и kipMatchesSbsFilter
// (только полное совпадение номеров).
function kipCountRelatedBySbs(section, items, sbsNo) {
    if (!items || !items.length) return 0;
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');
    const r = norm(sbsNo);
    if (!r) return 0;
    let count = 0;
    for (const it of items) {
        const v = norm(it['№ СБС']);
        if (!v) continue;
        // Полное совпадение номеров
        if (v === r) count++;
    }
    return count;
}

// Сгенерировать HTML-строку блока «Связанные записи» для карточки блокировки.
// Сразу рендерит строки с пометкой «загрузка…», после загрузки данных
// вызывающий код должен перерисовать блок (вызвать kipUpdateSbsRelatedBlock).
function kipRenderSbsRelatedBlock(sbsNo) {
    if (!sbsNo || kipIsEmptySbsNo(sbsNo)) return '';
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    let html = '<div class="kip-related-section" id="kipSbsRelatedSection">';
    html += '<div class="kip-related-title">Связанные записи</div>';
    html += '<div class="kip-related-grid">';
    for (const cfg of KIP_SBS_RELATED_SECTIONS) {
        html += '<div class="kip-related-row is-loading" data-sbs-related-section="' + esc(cfg.section) + '">';
        html += '<div class="kip-related-row-icon" style="background:' + esc(cfg.color) + ';">' + esc(cfg.icon) + '</div>';
        html += '<div class="kip-related-row-text">';
        html += '<div class="kip-related-row-label">' + esc(cfg.label) + '</div>';
        html += '<div class="kip-related-row-count">Загрузка…</div>';
        html += '</div>';
        html += '<div class="kip-related-row-arrow">›</div>';
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    return html;
}

// Обновить счётчики в блоке «Связанные записи» карточки блокировки.
function kipUpdateSbsRelatedBlock(sbsNo, section) {
    const root = document.getElementById('kipSbsRelatedSection');
    if (!root) return;
    const targets = section
        ? [section]
        : KIP_SBS_RELATED_SECTIONS.map(c => c.section);
    for (const sec of targets) {
        const row = root.querySelector('[data-sbs-related-section="' + sec + '"]');
        if (!row) continue;
        const countEl = row.querySelector('.kip-related-row-count');
        if (!countEl) continue;
        const items = kipGetSectionItems(sec);
        if (!items) continue;
        const count = kipCountRelatedBySbs(sec, items, sbsNo);
        const forms = {
            devices:    ['прибор', 'прибора', 'приборов'],
            valves:     ['клапан', 'клапана', 'клапанов'],
            regulators: ['регулятор', 'регулятора', 'регуляторов'],
        }[sec] || ['запись', 'записи', 'записей'];
        const plural = kipRelatedPlural(count, forms);
        countEl.textContent = count + ' ' + plural;
        if (count === 0) {
            row.classList.remove('is-loading');
            row.classList.add('is-empty');
            countEl.textContent = 'Нет связанных ' + forms[2];
        } else {
            row.classList.remove('is-loading', 'is-empty');
        }
    }
}

// Асинхронно загрузить все недостающие разделы и обновить счётчики.
// Вызывается из lockRenderDetail после установки HTML.
async function kipLoadAndUpdateSbsRelated(sbsNo) {
    if (!sbsNo || kipIsEmptySbsNo(sbsNo)) return;
    const promises = KIP_SBS_RELATED_SECTIONS.map(c => c.section).map(sec => kipLoadSectionData(sec));
    await Promise.all(promises);
    kipUpdateSbsRelatedBlock(sbsNo, null);
    const root = document.getElementById('kipSbsRelatedSection');
    if (!root) return;
    const rows = root.querySelectorAll('.kip-related-row');
    rows.forEach(function(row) {
        const sec = row.getAttribute('data-sbs-related-section');
        if (row.classList.contains('is-empty')) return;
        row.addEventListener('click', function() {
            kipSetSbsLinkFilter(sec, sbsNo);
        });
    });
}

// ===== Прямая навигация: клик по «№ САР» (приборы) / «№ САРиРУ» (клапаны) =====
// Вспомогательная функция: считается ли значение «№ САР» / «№ САРиРУ» пустым.
// Для таких значений ссылка не рендерится в *RenderDetail, а в
// regulatorOpenBySarNo показывается короткое сообщение вместо поиска.
// Возвращает true для: пусто, «Нет данных», «нет», «-», «—», «–», «н/д»,
// «n/a», «na», «null», «undefined», «нет сведений», «нет сар», «нет сариру».
function kipIsEmptySarNo(val) {
    if (val == null) return true;
    const s = String(val).trim().toLowerCase().replace(/[ё]/g, 'е');
    if (!s) return true;
    const empties = ['нет данных', 'нет', '-', '—', '–', '—', 'н/д', 'n/a', 'na', 'null', 'undefined', 'нет сведений', 'нет сар', 'нет сариру', 'нет сар/ру'];
    return empties.indexOf(s) !== -1;
}

// Возвращает имя поля «№ САР» для раздела:
//   devices  → «№ САР»
//   valves   → «№ САРиРУ»
//   regulators → «№ САРиРУ»
function kipSarFieldKey(section) {
    return section === 'devices' ? '№ САР' : '№ САРиРУ';
}

// Открыть карточку регулятора по значению «№ САР» / «№ САРиРУ».
// Сначала пытаемся найти точное совпадение в regulatorData.regulators
// по полю «№ САРиРУ», в fallback — по частичному совпадению.
// Если ничего не найдено — alert. При необходимости догружает regulators.json.
async function regulatorOpenBySarNo(sarNo) {
    if (sarNo == null) return;
    const raw = String(sarNo).trim();
    if (!raw) return;
    if (kipIsEmptySarNo(raw)) {
        if (navigator.vibrate) navigator.vibrate(10);
        alert('№ САР не указан.');
        return;
    }
    if (navigator.vibrate) navigator.vibrate(15);

    // Догрузить regulators.json, если ещё не загружен
    if (!window.regulatorLoaded || !window.regulatorData) {
        try {
            const bust = '?v=' + Date.now();
            const resp = await fetch('data/regulators.json' + bust, { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            window.regulatorData = await resp.json();
            window.regulatorLoaded = true;
            localStorage.setItem('regulatorsLastUpdate', new Date().toISOString());
        } catch (e) {
            console.error('regulatorOpenBySarNo: ошибка загрузки regulators.json:', e);
            alert('Не удалось загрузить данные регуляторов. Проверьте соединение.');
            return;
        }
    }

    // Нормализация: нижний регистр, ё→е, схлопывание пробелов.
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');

    const items = window.regulatorData.regulators || [];
    const r = norm(raw);
    const fieldKey = '№ САРиРУ';

    // 1) Точное совпадение по «№ САРиРУ»
    const exact = items.find(d => norm(d[fieldKey]) === r);
    if (exact && exact['ID'] != null && exact['ID'] !== '') {
        window.regulatorOpenDetail(exact['ID']);
        return;
    }

    // 2) Не найдено точное совпадение — показать сообщение.
    //    Частичное совпадение отключено: разные САР могут содержать
    //    одинаковые подстроки (например, «11405» и «11405(1)» — разные САР),
    //    поэтому соответствие определяется только по полному совпадению.
    alert('Регулятор с № САР «' + raw + '» не найден в базе регуляторов.');
}

// ===== Обратные ссылки: фильтр списка раздела КИП ИОС по «№ САР» / «№ САРиРУ» =====
// Глобальное состояние фильтра. Когда не null — соответствующий
// *RenderSorted фильтрует записи по полю «№ САР» (devices) или «№ САРиРУ»
// (valves) — только по полному совпадению номеров. В шапке списка
// показывается бейдж с возможностью сброса.
//
// Структура:
//   { sarNo: '11405', section: 'devices' }
// section — одно из: 'devices' | 'valves'
let kipSarLinkFilter = null;

// Установить фильтр по «№ САР» и открыть страницу раздела КИП ИОС.
function kipSetSarLinkFilter(section, sarNo) {
    if (!section || sarNo == null) return;
    const raw = String(sarNo).trim();
    if (!raw || kipIsEmptySarNo(raw)) {
        if (navigator.vibrate) navigator.vibrate(10);
        alert('№ САР не указан.');
        return;
    }
    const pages = {
        devices: 'devices-prod',
        valves: 'valves-prod',
    };
    const target = pages[section];
    if (!target) return;
    if (navigator.vibrate) navigator.vibrate(15);
    // Взаимное исключение: фильтр по «№ САР», «№ проекта» и «№ СБС» не могут
    // быть активны одновременно для одного раздела — сбросить остальные.
    if (kipProjectLinkFilter && kipProjectLinkFilter.section === section) {
        kipProjectLinkFilter = null;
    }
    if (kipSbsLinkFilter && kipSbsLinkFilter.section === section) {
        kipSbsLinkFilter = null;
    }
    kipSarLinkFilter = { sarNo: raw, section: section };
    const inputIds = {
        devices:    ['devProdSearchInput', 'devTypeSearchInput', 'devNameSearchInput'],
        valves:     ['valveProdSearchInput'],
    }[section] || [];
    for (const iid of inputIds) {
        const inp = document.getElementById(iid);
        if (inp) inp.value = '';
    }
    window.navigateTo(target);
}

// Сбросить активный САР-фильтр (если он относится к данному разделу).
function kipClearSarLinkFilter(section) {
    if (!kipSarLinkFilter) return;
    if (!section || kipSarLinkFilter.section === section) {
        kipSarLinkFilter = null;
        if (navigator.vibrate) navigator.vibrate(8);
    }
}

// Проверить, активен ли САР-фильтр для данного раздела.
function kipIsSarLinkFilterActive(section) {
    return !!(kipSarLinkFilter && kipSarLinkFilter.section === section);
}

// Проверить, проходит ли запись САР-фильтр.
// Для devices — сравнение по полю «№ САР»;
// для valves — по полю «№ САРиРУ».
// Соответствие — только по полному совпадению номеров (после нормализации).
function kipMatchesSarFilter(item, section) {
    if (!kipSarLinkFilter || kipSarLinkFilter.section !== section) return true;
    const raw = kipSarLinkFilter.sarNo;
    if (!raw) return true;
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');
    const r = norm(raw);
    const v = norm(item[kipSarFieldKey(section)]);
    if (!v) return false;
    // Полное совпадение номеров
    return v === r;
}

// Рендер бейджа активного САР-фильтра в шапке списка раздела.
// Возвращает HTML-строку (пустую, если фильтр не активен).
// Использует тот же CSS-класс .kip-filter-badge, что и проектный/СБС,
// но data-атрибут data-sar-filter-badge отличает бейджи.
function kipRenderSarFilterBadge(section) {
    if (!kipIsSarLinkFilterActive(section)) return '';
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const no = kipSarLinkFilter.sarNo;
    return '<div class="kip-filter-badge" data-sar-filter-badge="' + esc(section) + '">' +
           '<span class="kip-filter-badge-label">САР:</span>' +
           '<span class="kip-filter-badge-value">' + esc(no) + '</span>' +
           '<button class="kip-filter-badge-clear" data-sar-filter-clear="' + esc(section) + '" aria-label="Сбросить фильтр">✕</button>' +
           '</div>';
}

// Привязка обработчика к кнопке ✕ в бейдже САР-фильтра.
function kipBindSarFilterBadge(container, section, renderFn) {
    if (!container) return;
    const badge = container.querySelector('[data-sar-filter-badge="' + section + '"]');
    if (!badge) return;
    const clear = badge.querySelector('[data-sar-filter-clear]');
    if (clear) {
        clear.addEventListener('click', function(e) {
            e.stopPropagation();
            kipClearSarLinkFilter(section);
            const inputIds = {
                devices:    ['devProdSearchInput', 'devTypeSearchInput', 'devNameSearchInput'],
                valves:     ['valveProdSearchInput'],
            }[section] || [];
            for (const iid of inputIds) {
                const inp = document.getElementById(iid);
                if (inp) inp.value = '';
            }
            if (typeof renderFn === 'function') renderFn('prod');
        });
    }
}

// ===== Обратные ссылки: блок «Связанные записи» в карточке регулятора =====
// Конфигурация разделов для отображения обратных ссылок по «№ САР» / «№ САРиРУ».
// В карточке регулятора показываем связанные:
//   - Приборы (devices) — имеют поле «№ САР»
//   - Клапаны (valves) — имеют поле «№ САРиРУ»
// Регуляторы не показываем (это их собственный ID), блокировки/кабели
// не показываем (у них нет поля «№ САР» / «№ САРиРУ»).
const KIP_SAR_RELATED_SECTIONS = [
    { label: 'Приборы', section: 'devices', icon: 'П', color: '#6aa6e0' },
    { label: 'Клапаны', section: 'valves',  icon: 'К', color: '#4a8a8c' },
];

// Подсчитать количество связанных записей для данного «№ САР».
// Использует ту же логику совпадения, что и kipMatchesSarFilter
// (только полное совпадение номеров).
function kipCountRelatedBySar(section, items, sarNo) {
    if (!items || !items.length) return 0;
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');
    const r = norm(sarNo);
    if (!r) return 0;
    const fieldKey = kipSarFieldKey(section);
    let count = 0;
    for (const it of items) {
        const v = norm(it[fieldKey]);
        if (!v) continue;
        // Полное совпадение номеров
        if (v === r) count++;
    }
    return count;
}

// Сгенерировать HTML-строку блока «Связанные записи» для карточки регулятора.
// Сразу рендерит строки с пометкой «загрузка…», после загрузки данных
// вызывающий код должен перерисовать блок (вызвать kipUpdateSarRelatedBlock).
function kipRenderSarRelatedBlock(sarNo) {
    if (!sarNo || kipIsEmptySarNo(sarNo)) return '';
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    let html = '<div class="kip-related-section" id="kipSarRelatedSection">';
    html += '<div class="kip-related-title">Связанные записи</div>';
    html += '<div class="kip-related-grid">';
    for (const cfg of KIP_SAR_RELATED_SECTIONS) {
        html += '<div class="kip-related-row is-loading" data-sar-related-section="' + esc(cfg.section) + '">';
        html += '<div class="kip-related-row-icon" style="background:' + esc(cfg.color) + ';">' + esc(cfg.icon) + '</div>';
        html += '<div class="kip-related-row-text">';
        html += '<div class="kip-related-row-label">' + esc(cfg.label) + '</div>';
        html += '<div class="kip-related-row-count">Загрузка…</div>';
        html += '</div>';
        html += '<div class="kip-related-row-arrow">›</div>';
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    return html;
}

// Обновить счётчики в блоке «Связанные записи» карточки регулятора.
function kipUpdateSarRelatedBlock(sarNo, section) {
    const root = document.getElementById('kipSarRelatedSection');
    if (!root) return;
    const targets = section
        ? [section]
        : KIP_SAR_RELATED_SECTIONS.map(c => c.section);
    for (const sec of targets) {
        const row = root.querySelector('[data-sar-related-section="' + sec + '"]');
        if (!row) continue;
        const countEl = row.querySelector('.kip-related-row-count');
        if (!countEl) continue;
        const items = kipGetSectionItems(sec);
        if (!items) continue;
        const count = kipCountRelatedBySar(sec, items, sarNo);
        const forms = {
            devices: ['прибор', 'прибора', 'приборов'],
            valves:  ['клапан', 'клапана', 'клапанов'],
        }[sec] || ['запись', 'записи', 'записей'];
        const plural = kipRelatedPlural(count, forms);
        countEl.textContent = count + ' ' + plural;
        if (count === 0) {
            row.classList.remove('is-loading');
            row.classList.add('is-empty');
            countEl.textContent = 'Нет связанных ' + forms[2];
        } else {
            row.classList.remove('is-loading', 'is-empty');
        }
    }
}

// Асинхронно загрузить все недостающие разделы и обновить счётчики.
// Вызывается из regulatorRenderDetail после установки HTML.
async function kipLoadAndUpdateSarRelated(sarNo) {
    if (!sarNo || kipIsEmptySarNo(sarNo)) return;
    const promises = KIP_SAR_RELATED_SECTIONS.map(c => c.section).map(sec => kipLoadSectionData(sec));
    await Promise.all(promises);
    kipUpdateSarRelatedBlock(sarNo, null);
    const root = document.getElementById('kipSarRelatedSection');
    if (!root) return;
    const rows = root.querySelectorAll('.kip-related-row');
    rows.forEach(function(row) {
        const sec = row.getAttribute('data-sar-related-section');
        if (row.classList.contains('is-empty')) return;
        row.addEventListener('click', function() {
            kipSetSarLinkFilter(sec, sarNo);
        });
    });
}

// ===== Обратные ссылки: блок «Связанные записи» в карточке проекта =====
// Конфигурация разделов для отображения обратных ссылок.
// label — название раздела в карточке проекта;
// section — идентификатор для kipProjectLinkFilter;
// itemsKey — ключ в JSON, где лежит массив записей (devices/lockouts/...);
// loadedFlag — имя глобальной переменной-флага (строкой не получится,
//   поэтому используем явные проверки в kipSectionLoaded/kipGetSectionItems);
// icon — буква для иконки; color — цвет иконки (RGB-строка).
const KIP_RELATED_SECTIONS = [
    { label: 'Приборы',         section: 'devices',    icon: 'П', color: '#6aa6e0' },
    { label: 'Блокировки',      section: 'lockouts',   icon: 'Б', color: '#b85a7a' },
    { label: 'Клапаны',         section: 'valves',     icon: 'К', color: '#4a8a8c' },
    { label: 'Регуляторы',      section: 'regulators', icon: 'Р', color: '#7e5ab8' },
];

// Проверить, загружены ли данные раздела.
function kipSectionLoaded(section) {
    switch (section) {
        case 'devices':    return !!(typeof window.devLoaded !== 'undefined' && window.devLoaded && window.devData);
        case 'lockouts':   return !!(typeof window.lockLoaded !== 'undefined' && window.lockLoaded && window.lockData);
        case 'valves':     return !!(typeof window.valveLoaded !== 'undefined' && window.valveLoaded && window.valveData);
        case 'regulators': return !!(typeof window.regulatorLoaded !== 'undefined' && window.regulatorLoaded && window.regulatorData);
    }
    return false;
}

// Получить массив записей раздела (или null, если не загружен).
function kipGetSectionItems(section) {
    switch (section) {
        case 'devices':    return window.devData && window.devData.devices ? window.devData.devices : null;
        case 'lockouts':   return window.lockData && window.lockData.lockouts ? window.lockData.lockouts : null;
        case 'valves':     return window.valveData && window.valveData.valves ? window.valveData.valves : null;
        case 'regulators': return window.regulatorData && window.regulatorData.regulators ? window.regulatorData.regulators : null;
    }
    return null;
}

// Загрузить данные раздела (если ещё не загружены). Возвращает Promise.
// Использует те же глобальные переменные и тот же формат fetch, что и
// соответствующий *InitSorted — без дублирования логики парсинга.
async function kipLoadSectionData(section) {
    if (kipSectionLoaded(section)) return true;
    const url = 'data/' + (
        section === 'devices' ? 'devices.json' :
        section === 'lockouts' ? 'lockouts.json' :
        section === 'valves' ? 'valves.json' :
        section === 'regulators' ? 'regulators.json' : null
    );
    if (!url) return false;
    try {
        const bust = '?v=' + Date.now();
        const resp = await fetch(url + bust, { cache: 'no-store' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        switch (section) {
            case 'devices':
                window.devData = data; window.devLoaded = true;
                localStorage.setItem('devicesLastUpdate', new Date().toISOString());
                break;
            case 'lockouts':
                window.lockData = data; window.lockLoaded = true;
                localStorage.setItem('lockoutsLastUpdate', new Date().toISOString());
                break;
            case 'valves':
                window.valveData = data; window.valveLoaded = true;
                localStorage.setItem('valvesLastUpdate', new Date().toISOString());
                break;
            case 'regulators':
                window.regulatorData = data; window.regulatorLoaded = true;
                localStorage.setItem('regulatorsLastUpdate', new Date().toISOString());
                break;
        }
        return true;
    } catch (e) {
        console.error('kipLoadSectionData(' + section + ') error:', e);
        return false;
    }
}

// Подсчитать количество связанных записей для данного «№ проекта».
// Использует ту же логику совпадения, что и kipMatchesProjectFilter
// (только полное совпадение номеров).
function kipCountRelated(section, items, projectNo) {
    if (!items || !items.length) return 0;
    const norm = (s) => String(s == null ? '' : s)
        .trim().toLowerCase().replace(/[ё]/g, 'е').replace(/\s+/g, ' ');
    const r = norm(projectNo);
    if (!r) return 0;
    let count = 0;
    for (const it of items) {
        const v = norm(it['№ проекта']);
        if (!v) continue;
        // Полное совпадение номеров
        if (v === r) count++;
    }
    return count;
}

// Сгенерировать HTML-строку блока «Связанные записи» для карточки проекта.
// Сразу рендерит строки с пометкой «загрузка…», после загрузки данных
// вызывающий код должен перерисовать блок (вызвать kipUpdateRelatedBlock).
function kipRenderRelatedBlock(projectNo) {
    if (!projectNo || window.kipIsEmptyProjectNo(projectNo)) return '';
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    let html = '<div class="kip-related-section" id="kipRelatedSection">';
    html += '<div class="kip-related-title">Связанные записи</div>';
    html += '<div class="kip-related-grid">';
    for (const cfg of KIP_RELATED_SECTIONS) {
        html += '<div class="kip-related-row is-loading" data-related-section="' + esc(cfg.section) + '">';
        html += '<div class="kip-related-row-icon" style="background:' + esc(cfg.color) + ';">' + esc(cfg.icon) + '</div>';
        html += '<div class="kip-related-row-text">';
        html += '<div class="kip-related-row-label">' + esc(cfg.label) + '</div>';
        html += '<div class="kip-related-row-count">Загрузка…</div>';
        html += '</div>';
        html += '<div class="kip-related-row-arrow">›</div>';
        html += '</div>';
    }
    html += '</div>';
    html += '</div>';
    return html;
}

// Обновить счётчики в блоке «Связанные записи».
// section — какой раздел обновить (или null для всех).
// projectNo — № проекта для фильтрации.
function kipUpdateRelatedBlock(projectNo, section) {
    const root = document.getElementById('kipRelatedSection');
    if (!root) return;
    const esc = (s) => String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const targets = section
        ? [section]
        : KIP_RELATED_SECTIONS.map(c => c.section);
    for (const sec of targets) {
        const row = root.querySelector('[data-related-section="' + sec + '"]');
        if (!row) continue;
        const countEl = row.querySelector('.kip-related-row-count');
        if (!countEl) continue;
        const items = kipGetSectionItems(sec);
        const cfg = KIP_RELATED_SECTIONS.find(c => c.section === sec);
        if (!items) {
            // Данные ещё не загружены — оставляем «Загрузка…»
            continue;
        }
        // Если данные есть, но пустой массив — тоже считаем = 0
        const count = kipCountRelated(sec, items, projectNo);
        // Плюрализация
        const forms = {
            devices:    ['прибор', 'прибора', 'приборов'],
            lockouts:   ['блокировка', 'блокировки', 'блокировок'],
            valves:     ['клапан', 'клапана', 'клапанов'],
            regulators: ['регулятор', 'регулятора', 'регуляторов'],
        }[sec] || ['запись', 'записи', 'записей'];
        const plural = kipRelatedPlural(count, forms);
        countEl.textContent = count + ' ' + plural;
        if (count === 0) {
            row.classList.remove('is-loading');
            row.classList.add('is-empty');
            countEl.textContent = 'Нет связанных ' + forms[2];
        } else {
            row.classList.remove('is-loading', 'is-empty');
        }
    }
}

// Русская плюрализация для счётчиков в блоке связанных записей.
function kipRelatedPlural(n, forms) {
    const m = n % 100;
    const m1 = m % 10;
    if (m >= 5 && m <= 20) return forms[2];
    if (m1 === 1) return forms[0];
    if (m1 >= 2 && m1 <= 4) return forms[1];
    return forms[2];
}

// Асинхронно загрузить все недостающие разделы и обновить счётчики.
// Вызывается из projectRenderDetail после установки HTML.
async function kipLoadAndUpdateRelated(projectNo) {
    if (!projectNo || window.kipIsEmptyProjectNo(projectNo)) return;
    // Загружаем разделы параллельно
    const promises = KIP_RELATED_SECTIONS.map(c => c.section).map(sec => kipLoadSectionData(sec));
    await Promise.all(promises);
    // После загрузки обновляем счётчики
    kipUpdateRelatedBlock(projectNo, null);
    // Привязываем обработчики кликов на строки (теперь они кликабельны)
    const root = document.getElementById('kipRelatedSection');
    if (!root) return;
    const rows = root.querySelectorAll('.kip-related-row');
    rows.forEach(function(row) {
        const sec = row.getAttribute('data-related-section');
        // Не привязывать, если 0 связанных
        if (row.classList.contains('is-empty')) return;
        row.addEventListener('click', function() {
            kipSetProjectLinkFilter(sec, projectNo);
        });
    });
}

// ===== Exports =====
export {
    // Filter state
    kipProjectLinkFilter,
    kipSbsLinkFilter,
    kipSarLinkFilter,
    // Constants
    KIP_SBS_RELATED_SECTIONS,
    KIP_SAR_RELATED_SECTIONS,
    KIP_RELATED_SECTIONS,
    // Project filter functions
    kipSetProjectLinkFilter,
    kipClearProjectLinkFilter,
    kipIsProjectLinkFilterActive,
    kipMatchesProjectFilter,
    kipRenderFilterBadge,
    kipBindFilterBadge,
    // SBS filter functions
    kipIsEmptySbsNo,
    kipSetSbsLinkFilter,
    kipClearSbsLinkFilter,
    kipIsSbsLinkFilterActive,
    kipMatchesSbsFilter,
    kipRenderSbsFilterBadge,
    kipBindSbsFilterBadge,
    // SBS related-block functions
    kipCountRelatedBySbs,
    kipRenderSbsRelatedBlock,
    kipUpdateSbsRelatedBlock,
    kipLoadAndUpdateSbsRelated,
    lockOpenBySbsNo,
    // SAR filter functions
    kipIsEmptySarNo,
    kipSarFieldKey,
    kipSetSarLinkFilter,
    kipClearSarLinkFilter,
    kipIsSarLinkFilterActive,
    kipMatchesSarFilter,
    kipRenderSarFilterBadge,
    kipBindSarFilterBadge,
    // SAR related-block functions
    kipCountRelatedBySar,
    kipRenderSarRelatedBlock,
    kipUpdateSarRelatedBlock,
    kipLoadAndUpdateSarRelated,
    regulatorOpenBySarNo,
    // Project related-block functions
    kipSectionLoaded,
    kipGetSectionItems,
    kipLoadSectionData,
    kipCountRelated,
    kipRenderRelatedBlock,
    kipUpdateRelatedBlock,
    kipRelatedPlural,
    kipLoadAndUpdateRelated,
};
