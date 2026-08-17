/**
 * @module phonebook
 * Телефонный справочник (ООО ПО "ТОКЕМ")
 * Extracted from src/index.html (lines 3053–3675)
 */

// ===== ТЕЛЕФОННЫЙ СПРАВОЧНИК (ООО ПО "ТОКЕМ") =====
let pbData = null;          // распарсенный JSON
let pbFlat = [];            // плоский массив: {section, position, name, phone}
let pbLoaded = false;

// === Избранные контакты и пользовательские примечания ===
// Хранение в localStorage. ID контакта = section + '|' + name + '|' + phone
// (уникален в пределах справочника).
let pbFavorites = {};       // {id: true}
let pbNotes = {};           // {id: "текст примечания"}
let pbFilterFavOnly = false; // показывать только избранные

const PB_FAV_KEY = 'kip8test_phonebook_favorites';
const PB_NOTES_KEY = 'kip8test_phonebook_notes';

function pbMakeId(item) {
    // ID строится из header + group + subgroup + position + name + phone для уникальности.
    return (item.header || '') + '|' + (item.group || '') + '|' + (item.subgroup || '') + '|' +
           (item.position || '') + '|' + (item.name || '') + '|' + (item.phone || '');
}
function pbLoadFavorites() {
    try {
        const raw = localStorage.getItem(PB_FAV_KEY);
        pbFavorites = raw ? JSON.parse(raw) : {};
    } catch (e) { pbFavorites = {}; }
}
function pbSaveFavorites() {
    try { localStorage.setItem(PB_FAV_KEY, JSON.stringify(pbFavorites)); } catch (e) {}
}
function pbLoadNotes() {
    try {
        const raw = localStorage.getItem(PB_NOTES_KEY);
        pbNotes = raw ? JSON.parse(raw) : {};
    } catch (e) { pbNotes = {}; }
}
function pbSaveNotes() {
    try { localStorage.setItem(PB_NOTES_KEY, JSON.stringify(pbNotes)); } catch (e) {}
}
export function pbIsFavorite(id) {
    return pbFavorites[id] === true;
}
function pbGetNote(id) {
    return pbNotes[id] || '';
}
export function pbGetFavoritesCount() {
    return Object.keys(pbFavorites).filter(k => pbFavorites[k] === true).length;
}

// Очистка "фантомных" записей в избранном и примечаниях.
// При изменении структуры pbMakeId (например, при добавлении поля subgroup)
// старые ключи в localStorage больше не соответствуют реальным контактам.
// Эта функция удаляет все записи, ID которых не найден в pbFlat,
// и сохраняет очищенные данные обратно в localStorage.
// Возвращает количество удалённых записей.
function pbCleanupStaleFavorites() {
    if (!pbFlat || pbFlat.length === 0) return { fav: 0, notes: 0 };
    // Построить множество валидных ID
    const validIds = new Set(pbFlat.map(item => pbMakeId(item)));
    let favRemoved = 0;
    let notesRemoved = 0;
    // Очистить pbFavorites
    for (const key of Object.keys(pbFavorites)) {
        if (!validIds.has(key)) {
            delete pbFavorites[key];
            favRemoved++;
        }
    }
    // Очистить pbNotes
    for (const key of Object.keys(pbNotes)) {
        if (!validIds.has(key)) {
            delete pbNotes[key];
            notesRemoved++;
        }
    }
    // Сохранить обратно, если что-то изменилось
    if (favRemoved > 0) pbSaveFavorites();
    if (notesRemoved > 0) pbSaveNotes();
    if (favRemoved > 0 || notesRemoved > 0) {
        console.log('[phonebook] Очистка устаревших записей: избранное −' + favRemoved + ', примечания −' + notesRemoved);
    }
    return { fav: favRemoved, notes: notesRemoved };
}

// Нормализация строки для сравнения (lowercase, без лишних пробелов)
function pbNorm(s) {
    return (s || '').toString().toLowerCase().replace(/\s+/g, ' ').trim();
}
// Экранирование HTML
function pbEsc(s) {
    return (s || '').toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
// Подсветка совпадения: обёртывает все вхождения query в <mark>
function pbMark(text, query) {
    const safe = pbEsc(text);
    if (!query) return safe;
    const q = pbNorm(query);
    if (!q) return safe;
    // Экранируем query для RegExp
    const qEsc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // Сравниваем по нормализованной строке, но сохраняем оригинальный регистр
    const normText = (text || '').toString();
    const regex = new RegExp(qEsc, 'gi');
    let result = '';
    let lastIdx = 0;
    let m;
    while ((m = regex.exec(normText)) !== null) {
        const start = m.index;
        const end = start + m[0].length;
        // Экранируем кусок до совпадения
        result += pbEsc(normText.slice(lastIdx, start));
        // Совпадение — в <mark>
        result += '<mark>' + pbEsc(normText.slice(start, end)) + '</mark>';
        lastIdx = end;
        // Защита от зацикливания при пустом match
        if (m.index === regex.lastIndex) regex.lastIndex++;
    }
    result += pbEsc(normText.slice(lastIdx));
    return result;
}

// Версия кэша phonebook в localStorage. При изменении структуры данных —
// инкрементировать, чтобы старый кэш автоматически сбросился.
const PB_CACHE_VERSION = 'v3-header-group-subgroup';

async function pbLoad() {
    if (pbLoaded) return pbData;
    try {
        // Сначала пытаемся загрузить свежие данные из сети (NetworkFirst).
        // Cache-busting: ?v=timestamp обходит HTTP-кэш и SW Cache.
        // cache: 'no-store' — гарантированно не используем HTTP-кэш браузера.
        const bust = '?v=' + Date.now();
        const resp = await fetch('data/phonebook.json' + bust, { cache: 'no-store' });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        pbData = await resp.json();
        // Сохраняем в localStorage как резервный кэш для офлайна
        try {
            localStorage.setItem('kip8test_phonebook_cache', JSON.stringify(pbData));
        } catch (e) {}
        pbFlatten();
        pbLoaded = true;
        return pbData;
    } catch (e) {
        console.warn('Phonebook load from network failed, trying cache:', e);
        // Офлайн — берём из localStorage
        try {
            const cached = localStorage.getItem('kip8test_phonebook_cache');
            if (cached) {
                pbData = JSON.parse(cached);
                pbFlatten();
                pbLoaded = true;
                console.log('[phonebook] Используется кэш localStorage (офлайн)');
                return pbData;
            }
        } catch (e2) {}
        return null;
    }
}

function pbFlatten() {
    pbFlat = [];
    if (!pbData || !pbData.sections) return;
    for (const header of Object.keys(pbData.sections)) {
        for (const item of pbData.sections[header]) {
            pbFlat.push({
                header: header,
                group: item.group || null,
                subgroup: item.subgroup || null,
                position: item.position || '',
                name: item.name || '',
                phone: item.phone || '',
            });
        }
    }
}

export function pbRender() {
    const list = document.getElementById('pbList');
    const info = document.getElementById('pbInfo');
    if (!list || !info) return;

    const query = pbNorm((document.getElementById('pbSearchInput')?.value || '').trim());

    // Обновить счётчик на кнопке фильтра
    pbUpdateFilterButton();

    if (!pbLoaded) {
        list.innerHTML = '';
        info.textContent = 'Загрузка…';
        return;
    }

    // Фильтрация: по поиску + по избранным (если включён фильтр)
    let filtered = pbFlat.slice();
    if (pbFilterFavOnly) {
        filtered = filtered.filter(item => pbIsFavorite(pbMakeId(item)));
    }
    if (query) {
        filtered = filtered.filter(item =>
            pbNorm(item.name).includes(query) ||
            pbNorm(item.position).includes(query) ||
            pbNorm(item.phone).includes(query) ||
            pbNorm(item.header).includes(query) ||
            (item.group && pbNorm(item.group).includes(query)) ||
            (item.subgroup && pbNorm(item.subgroup).includes(query))
        );
    }

    // Группировка по header'ам (верхний уровень) с сохранением порядка
    const groupedByHeader = {};
    for (const item of filtered) {
        if (!groupedByHeader[item.header]) groupedByHeader[item.header] = [];
        groupedByHeader[item.header].push(item);
    }

    // Инфо
    let infoParts = [];
    const headerCount = Object.keys(groupedByHeader).length;
    if (pbFilterFavOnly) {
        infoParts.push('Избранные: ' + filtered.length + ' ' + pbPlural(filtered.length, ['запись', 'записи', 'записей']));
    } else if (query) {
        infoParts.push('Найдено: ' + filtered.length + ' ' + pbPlural(filtered.length, ['запись', 'записи', 'записей']) +
                       ' в ' + headerCount + ' ' + pbPlural(headerCount, ['организации', 'организациях', 'организациях']));
    } else {
        infoParts.push('Всего: ' + pbFlat.length + ' ' + pbPlural(pbFlat.length, ['запись', 'записи', 'записей']) +
                       ' · ' + Object.keys(pbData.sections).length + ' организаций');
        const favCount = pbGetFavoritesCount();
        if (favCount > 0) {
            infoParts.push(' · избранное: ' + favCount);
        } else {
            infoParts.push(' · тапните по организации или отделу, чтобы раскрыть');
        }
    }
    info.textContent = infoParts.join('');

    // Режим: есть поисковый запрос ИЛИ фильтр избранных → все секции раскрыты
    const forceExpand = query || pbFilterFavOnly;
    if (forceExpand) {
        list.classList.add('searching');
    } else {
        list.classList.remove('searching');
    }

    // Рендер
    if (filtered.length === 0) {
        if (pbFilterFavOnly && !query) {
            list.innerHTML = '<div class="pb-empty">Нет избранных контактов.<br>Нажмите на ★ рядом с контактом, чтобы добавить его сюда.</div>';
        } else {
            list.innerHTML = '<div class="pb-empty">Ничего не найдено.<br>Попробуйте изменить запрос.</div>';
        }
        return;
    }

    let html = '';
    for (const header of Object.keys(pbData.sections)) {
        if (!groupedByHeader[header] || groupedByHeader[header].length === 0) continue;
        const items = groupedByHeader[header];
        const count = items.length;

        // В режиме поиска/фильтра — секция раскрыта. Иначе — сохраняем состояние.
        const isExpanded = forceExpand ? true : (pbExpandedSections[header] === true);
        html += '<div class="pb-section' + (isExpanded ? ' expanded' : '') + '" data-section="' + pbEsc(header) + '">';
        html += '<div class="pb-section-title" onclick="pbToggleSection(this)">';
        html += '<span class="pb-section-title-text">' + pbMark(header, query) + '</span>';
        html += '<span class="pb-section-title-count">' + count + '</span>';
        html += '<span class="pb-section-arrow"></span>';
        html += '</div>';
        html += '<div class="pb-section-body">';

        // Внутри секции — группировка по group (второй уровень) с сохранением порядка
        const groupedByGroup = {};
        const groupOrder = [];
        for (const item of items) {
            const g = item.group || null;
            if (!(g in groupedByGroup)) {
                groupedByGroup[g] = [];
                groupOrder.push(g);
            }
            groupedByGroup[g].push(item);
        }
        // Сортируем группы по алфавиту (null — в конце)
        groupOrder.sort((a, b) => {
            if (a === null) return 1;
            if (b === null) return -1;
            const va = a.toString().toLowerCase();
            const vb = b.toString().toLowerCase();
            if (va < vb) return -1;
            if (va > vb) return 1;
            return 0;
        });

        // Показываем подзаголовки групп, если есть хотя бы одна именованная группа
        const hasAnyNamedGroup = groupOrder.some(g => g !== null);
        const showGroupHeaders = groupOrder.length > 1 || hasAnyNamedGroup;

        // Глобальный счётчик карточек для зебра-фона
        let cardIndex = 0;

        for (const g of groupOrder) {
            if (showGroupHeaders) {
                const groupLabel = g === null ? 'Без группы' : g;
                const groupCount = groupedByGroup[g].length;
                // Сворачиваемая подгруппа: data-subgroup = header + '|' + group
                const subgroupKey = header + '|' + (g === null ? '' : g);
                const sgExpanded = forceExpand ? true : (pbExpandedSubgroups[subgroupKey] === true);
                html += '<div class="pb-subgroup' + (sgExpanded ? ' expanded' : '') + '" data-subgroup="' + pbEsc(subgroupKey) + '">';
                html += '<div class="pb-subgroup-title" onclick="pbToggleSubgroup(this)">';
                html += '<span class="pb-subgroup-title-text">' + pbMark(groupLabel, query) + '</span>';
                html += '<span class="pb-subgroup-count">' + groupCount + '</span>';
                html += '<span class="pb-subgroup-arrow"></span>';
                html += '</div>';
                html += '<div class="pb-subgroup-body">';
            }

            // Внутри группы — группировка по subgroup (третий уровень)
            const groupedBySubgroup = {};
            const subgroupOrder = [];
            for (const item of groupedByGroup[g]) {
                const sg = item.subgroup || null;
                if (!(sg in groupedBySubgroup)) {
                    groupedBySubgroup[sg] = [];
                    subgroupOrder.push(sg);
                }
                groupedBySubgroup[sg].push(item);
            }

            const hasAnySubgroup = subgroupOrder.some(sg => sg !== null);
            const showSubgroupHeaders = subgroupOrder.length > 1 || hasAnySubgroup;

            for (const sg of subgroupOrder) {
                if (showSubgroupHeaders && sg !== null) {
                    const sgCount = groupedBySubgroup[sg].length;
                    html += '<div class="pb-subsubgroup">';
                    html += '<div class="pb-subsubgroup-title">' + pbMark(sg, query) +
                            '<span class="pb-subsubgroup-count">' + sgCount + '</span></div>';
                    html += '<div class="pb-subsubgroup-body">';
                }
                for (const item of groupedBySubgroup[sg]) {
                    const id = pbMakeId(item);
                    const isFav = pbIsFavorite(id);
                    const note = pbGetNote(id);
                    // Зебра: чётная/нечётная карточка
                    const zebraClass = (cardIndex % 2 === 0) ? ' pb-card-even' : ' pb-card-odd';
                    cardIndex++;
                    html += '<div class="pb-card' + zebraClass + '" data-id="' + pbEsc(id) + '">';
                    html += '<div class="pb-card-top">';
                    html += '<div class="pb-card-top-text">';
                    if (item.name) {
                        html += '<div class="pb-card-name">' + pbMark(item.name, query) + '</div>';
                    }
                    if (item.position) {
                        html += '<div class="pb-card-pos">' + pbMark(item.position, query) + '</div>';
                    }
                    if (item.phone) {
                        html += '<div class="pb-card-phone">' + pbMark(item.phone, query) + '</div>';
                    }
                    html += '</div>'; // .pb-card-top-text
                    // Кнопка-звёздочка
                    html += '<button type="button" class="pb-fav-btn' + (isFav ? ' fav-active' : '') + '" ' +
                            'aria-label="' + (isFav ? 'Убрать из избранного' : 'Добавить в избранное') + '" ' +
                            'onclick="pbToggleFavorite(this, event)">' +
                            '<svg viewBox="0 0 24 24" fill="' + (isFav ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>' +
                            '</button>';
                    html += '</div>'; // .pb-card-top
                    // Примечание (если есть) — с кнопкой редактирования
                    if (note) {
                        html += '<div class="pb-note">' + pbEsc(note) +
                                '<button type="button" class="pb-note-edit" aria-label="Редактировать примечание" onclick="pbEditNote(this)">' +
                                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>' +
                                '</button></div>';
                    } else {
                        html += '<button type="button" class="pb-note-add" onclick="pbEditNote(this)">' +
                                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>' +
                                'добавить примечание</button>';
                    }
                    html += '</div>'; // .pb-card
                }
                if (showSubgroupHeaders && sg !== null) {
                    html += '</div>'; // .pb-subsubgroup-body
                    html += '</div>'; // .pb-subsubgroup
                }
            }

            if (showGroupHeaders) {
                html += '</div>'; // .pb-subgroup-body
                html += '</div>'; // .pb-subgroup
            }
        }
        html += '</div>'; // .pb-section-body
        html += '</div>'; // .pb-section
    }
    list.innerHTML = html;
}

// Обновить состояние кнопки "Только избранные" и счётчик
function pbUpdateFilterButton() {
    const btn = document.getElementById('pbFilterFav');
    const label = document.getElementById('pbFilterFavLabel');
    if (!btn || !label) return;
    if (pbFilterFavOnly) {
        btn.classList.add('active');
    } else {
        btn.classList.remove('active');
    }
    const count = pbGetFavoritesCount();
    label.textContent = 'Избранные' + (count > 0 ? ': ' + count : '');
}

// Переключить фильтр "только избранные"
export function pbToggleFavFilter() {
    pbFilterFavOnly = !pbFilterFavOnly;
    if (navigator.vibrate) navigator.vibrate(25);
    // Сбросить раскрытые секции — в режиме фильтра они раскрываются автоматически
    pbExpandedSections = {};
    pbRender();
}

// Переключить избранное у контакта
export function pbToggleFavorite(btnEl, ev) {
    if (ev) { ev.stopPropagation(); ev.preventDefault(); }
    const card = btnEl.closest('.pb-card');
    if (!card) return;
    const id = card.getAttribute('data-id');
    if (!id) return;
    if (pbIsFavorite(id)) {
        delete pbFavorites[id];
        btnEl.classList.remove('fav-active');
        btnEl.setAttribute('aria-label', 'Добавить в избранное');
        // Убрать заливку звёздочки
        const svg = btnEl.querySelector('svg path');
        if (svg) svg.setAttribute('fill', 'none');
        if (navigator.vibrate) navigator.vibrate(20);
    } else {
        pbFavorites[id] = true;
        btnEl.classList.add('fav-active');
        btnEl.setAttribute('aria-label', 'Убрать из избранного');
        const svg = btnEl.querySelector('svg path');
        if (svg) svg.setAttribute('fill', 'currentColor');
        if (navigator.vibrate) navigator.vibrate([20, 30, 40]);
    }
    pbSaveFavorites();
    // Если включён фильтр избранных — пере-рендер (карточка может исчезнуть)
    if (pbFilterFavOnly) {
        pbRender();
    } else {
        pbUpdateFilterButton();
        // Обновить инфо-строку (там показывается счётчик избранного)
        pbRender();
    }
}

// Редактировать примечание (через prompt)
export function pbEditNote(btnEl) {
    const card = btnEl.closest('.pb-card');
    if (!card) return;
    const id = card.getAttribute('data-id');
    if (!id) return;
    const currentNote = pbGetNote(id);
    const newName = card.querySelector('.pb-card-name')?.textContent || 'этот контакт';
    const promptText = 'Примечание для: ' + newName + '\n\n(оставьте пустым, чтобы удалить)';
    window.kipPrompt(promptText, currentNote).then(function(newNote) {
        // null = отмена
        if (newNote === null) return;
        const trimmed = newNote.trim();
        if (trimmed) {
            pbNotes[id] = trimmed;
        } else {
            delete pbNotes[id];
        }
        pbSaveNotes();
        if (navigator.vibrate) navigator.vibrate(25);
        // Пере-рендер карточки (или всего списка — проще)
        pbRender();
    });
}

// Состояние раскрытых секций в обычном режиме (без поиска).
// Хранит {sectionName: true}. При открытии новой — предыдущая закрывается.
let pbExpandedSections = {};

// Вспомогательная функция: прокрутить элемент к верхней части экрана,
// учитывая высоту sticky-блока поиска (чтобы заголовок не перекрывался).
function pbScrollToTop(el) {
    if (!el) return;
    const searchWrap = document.querySelector('.pb-search-wrap');
    const stickyHeight = searchWrap ? searchWrap.getBoundingClientRect().height : 0;
    const rect = el.getBoundingClientRect();
    // Текущая позиция прокрутки + смещение элемента от верха viewport - высота sticky - маленький отступ
    const targetY = window.scrollY + rect.top - stickyHeight - 8;
    window.scrollTo({ top: Math.max(0, targetY), behavior: 'auto' });
}

// Отложенная прокрутка с корректировкой после завершения анимации.
// Анимация max-height длится ~400ms. Если прокрутить слишком рано,
// позиция "уплывёт", потому что контент ещё растёт.
// Стратегия:
//   1. Мгновенная прокрутка через 2 кадра (requestAnimationFrame × 2) —
//      убирает резкий скачок, позиция примерно правильная.
//   2. Повторная корректировка через 450ms — после завершения анимации,
//      когда финальная высота стабильна.
function pbScrollToTopDelayed(el) {
    if (!el) return;
    // 1-я прокрутка: быстро, чтобы убрать скачок
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            pbScrollToTop(el);
        });
    });
    // 2-я прокрутка: после завершения анимации max-height (0.4s = 400ms)
    setTimeout(() => {
        pbScrollToTop(el);
    }, 450);
}

// Обработчик клика по заголовку секции (аккордеон).
export function pbToggleSection(titleEl) {
    const list = document.getElementById('pbList');
    // В режиме поиска секции не сворачиваются (все раскрыты автоматически)
    if (list && list.classList.contains('searching')) return;

    const section = titleEl.closest('.pb-section');
    if (!section) return;
    const secName = section.getAttribute('data-section');
    if (!secName) return;

    const isExpanded = section.classList.contains('expanded');

    if (isExpanded) {
        // Закрыть текущую
        section.classList.remove('expanded');
        delete pbExpandedSections[secName];
        if (navigator.vibrate) navigator.vibrate(20);
    } else {
        // Закрыть ВСЕ остальные (аккордеон — только одна открытая)
        list.querySelectorAll('.pb-section.expanded').forEach(s => {
            s.classList.remove('expanded');
            const name = s.getAttribute('data-section');
            if (name) delete pbExpandedSections[name];
        });
        // Раскрыть текущую
        section.classList.add('expanded');
        pbExpandedSections[secName] = true;
        if (navigator.vibrate) navigator.vibrate(30);
        // Прокрутить заголовок секции к верхней части экрана.
        // Используем отложенную прокрутку с корректировкой после анимации.
        pbScrollToTopDelayed(section);
    }
}

// Состояние раскрытых подгрупп (второй уровень) в обычном режиме.
// Ключ = header + '|' + group. Аккордеон: только одна открытая в пределах секции.
let pbExpandedSubgroups = {};

// Обработчик клика по заголовку подгруппы (второй уровень, аккордеон).
export function pbToggleSubgroup(titleEl) {
    const list = document.getElementById('pbList');
    // В режиме поиска подгруппы не сворачиваются (все раскрыты автоматически)
    if (list && list.classList.contains('searching')) return;

    const subgroup = titleEl.closest('.pb-subgroup');
    if (!subgroup) return;
    const sgKey = subgroup.getAttribute('data-subgroup');
    if (!sgKey) return;

    // Найти родительскую секцию, чтобы закрыть другие подгруппы только в её пределах
    const section = subgroup.closest('.pb-section');
    if (!section) return;

    const isExpanded = subgroup.classList.contains('expanded');

    if (isExpanded) {
        // Закрыть текущую
        subgroup.classList.remove('expanded');
        delete pbExpandedSubgroups[sgKey];
        if (navigator.vibrate) navigator.vibrate(15);
    } else {
        // Аккордеон: закрыть ВСЕ остальные подгруппы ВНУТРИ этой же секции
        section.querySelectorAll('.pb-subgroup.expanded').forEach(s => {
            s.classList.remove('expanded');
            const k = s.getAttribute('data-subgroup');
            if (k) delete pbExpandedSubgroups[k];
        });
        // Раскрыть текущую
        subgroup.classList.add('expanded');
        pbExpandedSubgroups[sgKey] = true;
        if (navigator.vibrate) navigator.vibrate(25);
        // Прокрутить заголовок подгруппы к верхней части экрана.
        // Используем отложенную прокрутку с корректировкой после анимации.
        pbScrollToTopDelayed(subgroup);
    }
}

// Простая функция плюарализации для русского языка
function pbPlural(n, forms) {
    const n10 = n % 10;
    const n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 10 || n100 >= 20)) return forms[1];
    return forms[2];
}

// Инициализация при первом открытии страницы контактов
export function pbInit() {
    // Загрузить избранное и примечания из localStorage (всегда)
    pbLoadFavorites();
    pbLoadNotes();
    // Всегда перезагружаем данные из сети (cache-busting в pbLoad),
    // чтобы увидеть изменения из таблицы Google Sheets.
    // Очистка устаревших избранного будет выполнена после загрузки.
    pbLoaded = false;
    pbData = null;
    pbFlat = [];
    pbLoad().then(() => {
        // После загрузки данных — очистить устаревшие записи (старые ID
        // от предыдущих версий pbMakeId, которые больше не валидны)
        pbCleanupStaleFavorites();
        pbRender();
    });
}
