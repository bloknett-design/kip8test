/**
 * @module plan114
 * @description Plan 114 — building floor plans viewer for Kip IOS.
 * Includes registry of plans, entry button init, list rendering, and
 * the plan viewer with image loading from Google Drive.
 * Extracted from src/index.html (lines ~8308-8506).
 *
 * External dependencies (temporary window bridges):
 *   - navigateTo  (will be imported from core/navigation once available)
 */

const navigateTo = window.navigateTo;

// ===== Кнопка «План корпуса 114» на странице КИП И ОС + список планов + просмотр =====
// Реестр 6 планов помещений корпуса 114.
// driveId — ID файла Google Drive (из share-ссылки /file/d/ID/view).
// Картинка грузится напрямую через lh3.googleusercontent.com/d/ID=w10000
// (Google отдаёт исходное изображение как image/png, без OAuth).
// Service Worker кэширует эти запросы через IMAGE_CACHE_NAME
// (stale-while-revalidate) — после первой загрузки планы доступны офлайн.
// Оригинал открывается в новой вкладке через /file/d/ID/view.
const PLAN114_ITEMS = [
    { id: 'shk1-cpu', title: 'ЩК-1 (ЦПУ)', driveId: '1NbS0JUWCbLVuKz39XIT2J8adJ5VeP8yQ' },
    { id: 'shk2-rpa', title: 'ЩК-2 (РПА)', driveId: '1Ycdn-HFdu15AOA73W7ctV-oEKr4n02zn' },
    { id: 'otm-00',   title: 'Отм. 0.0 м', driveId: '1yE1gCe47Jc3qjQKkXFRfKKfQ1TCcWlrp' },
    { id: 'otm-06',   title: 'Отм. 6.0 м', driveId: '1WBH6oF1k6TjCCc9nOnoS9Sy-gI2BRSQL' },
    { id: 'otm-12',   title: 'Отм. 12.0 м', driveId: '1p73Aswuyho87yuxz8zriaO8NlLQH5oMp' },
    { id: 'otm-18',   title: 'Отм. 18.0 м', driveId: '1L-CehKcYKT-W9VOzkV0obqfT0FzuVIsY' }
];

// Инициализация кнопки входа «План корпуса 114» на странице КИП ИОС
function plan114InitEntryButton() {
    const btn = document.getElementById('plan114EntryBtn');
    if (!btn || btn.dataset.initialized) return;
    btn.dataset.initialized = '1';
    btn.addEventListener('click', function() {
        if (navigator.vibrate) navigator.vibrate(15);
        navigateTo('plan-114');
    });
}

// Рендер списка планов на странице page-plan-114.
// Вызывается один раз при первом открытии страницы (флаг plan114ListRendered).
let plan114ListRendered = false;
function plan114RenderList() {
    if (plan114ListRendered) return;
    const list = document.getElementById('plan114List');
    if (!list) return;
    // Сине-стальная палитра раздела (см. Системный_промт...md, «Цветовая палитра КИП ИОС»)
    const borderColor = 'rgba(120,140,170,0.35)';
    const labelColor = '#7896b0';
    const arrowColor = 'rgba(120,140,170,0.4)';
    list.innerHTML = PLAN114_ITEMS.map(function(item) {
        // Без подзаголовка — только название пункта (как выбрал пользователь)
        return '<div class="menu-btn" style="border-color:' + borderColor + ';" onclick="plan114OpenView(\'' + item.id + '\')">' +
            '<div class="menu-btn-text">' +
            '<div class="menu-btn-label" style="color:' + labelColor + ';">' + item.title + '</div>' +
            '</div>' +
            '<i class="menu-btn-arrow" style="color:' + arrowColor + ';">›</i>' +
            '</div>';
    }).join('');
    plan114ListRendered = true;
}

// Открытие страницы просмотра плана по id из PLAN114_ITEMS.
// Шаги:
//   1. Сменить страницу на page-plan-114-view через navigateTo().
//   2. Обновить заголовок страницы и ссылку «Открыть оригинал».
//   3. Показать индикатор «Загрузка…», скрыть старую картинку и ошибку.
//   4. Предзагрузить картинку через new Image() (чтобы избежать «дребезга» при смене src).
//      URL = https://lh3.googleusercontent.com/d/ID=w10000 — Google отдаёт
//      исходный PNG напрямую, без OAuth и без iframe.
//   5. Отобразить картинку, скрыть индикатор.
//   6. При ошибке — показать блок plan114Error.
async function plan114OpenView(id) {
    const item = PLAN114_ITEMS.find(function(x) { return x.id === id; });
    if (!item) return;
    if (navigator.vibrate) navigator.vibrate(15);

    navigateTo('plan-114-view');

    // Обновить заголовок страницы
    const titleEl = document.getElementById('plan114ViewTitle');
    if (titleEl) titleEl.textContent = item.title;

    // Обновить ссылку «Открыть оригинал» — ведёт на страницу файла Google Drive
    const origLink = document.getElementById('plan114OrigLink');
    if (origLink) {
        origLink.href = 'https://drive.google.com/file/d/' + encodeURIComponent(item.driveId) + '/view';
        origLink.textContent = 'Открыть оригинал на Google Drive';
        origLink.style.display = 'none'; // покажем после успешной загрузки
    }

    // Сбросить состояние UI
    const loadingEl = document.getElementById('plan114Loading');
    const imgEl = document.getElementById('plan114Img');
    const errorEl = document.getElementById('plan114Error');
    if (loadingEl) loadingEl.style.display = '';
    if (imgEl) {
        imgEl.style.display = 'none';
        imgEl.removeAttribute('src');
        imgEl.style.transform = '';
        imgEl.style.transformOrigin = '';
        imgEl.style.width = '';
        imgEl.style.height = '';
        imgEl.style.maxWidth = '100%';
    }
    if (errorEl) errorEl.style.display = 'none';
    // Сбросить стили поворота контейнера
    const containerEl = document.getElementById('plan114ImgContainer');
    if (containerEl) {
        containerEl.classList.remove('plan114-rotated');
        containerEl.style.height = '';
        const spacer = containerEl.querySelector('.plan114-rotate-spacer');
        if (spacer) spacer.remove();
    }

    try {
        // Прямой URL картинки Google Drive.
        // w10000 — запросить изображение шириной до 10000px (по сути, оригинал).
        // lh3.googleusercontent.com отдаёт image/png без CORS-ограничений для <img>.
        const imgUrl = 'https://lh3.googleusercontent.com/d/' + encodeURIComponent(item.driveId) + '=w10000';

        // Предзагрузить картинку (await onload) — избегаем «дребезга» при смене src.
        // Прерывание через 30 сек на случай зависания.
        await new Promise(function(resolve, reject) {
            const img = new Image();
            img.referrerPolicy = 'no-referrer';
            const timer = setTimeout(function() { reject(new Error('Image load timeout')); }, 30000);
            img.onload = function() { clearTimeout(timer); resolve(); };
            img.onerror = function() { clearTimeout(timer); reject(new Error('Image load failed')); };
            img.src = imgUrl;
        });

        // Отобразить картинку
        if (imgEl) {
            imgEl.src = imgUrl;
            imgEl.alt = item.title;
            imgEl.setAttribute('data-plan-id', item.id);
            imgEl.style.display = '';
        }
        if (loadingEl) loadingEl.style.display = 'none';
        if (origLink) origLink.style.display = ''; // показать кнопку «Открыть оригинал»

        // На десктопе: для планов отм-00/06/12/18 повернуть картинку влево
        // и сделать контейнер горизонтально прокручиваемым.
        const rotatedPlans = ['otm-00', 'otm-06', 'otm-12', 'otm-18'];
        const containerEl = document.getElementById('plan114ImgContainer');
        if (rotatedPlans.indexOf(item.id) !== -1 && containerEl && window.matchMedia('(min-width: 1024px)').matches) {
            // Дождаться, когда imgEl узнает свои naturalWidth/naturalHeight
            requestAnimationFrame(function() {
                const nw = imgEl.naturalWidth || 1;
                const nh = imgEl.naturalHeight || 1;
                // Доступная высота: вычитаем desktopTopBar (56px),
                // page-inline-header (56px) и запас на скроллбар (~12px).
                const availH = window.innerHeight - 56 - 56 - 12;
                // Масштаб: вписать по высоте (после поворота высота = nw)
                const scale = availH / nw;
                const renderedH = Math.round(nw * scale);  // высота после поворота
                const renderedW = Math.round(nh * scale);  // ширина после поворота
                // Установить размеры img до поворота:
                //   width = renderedH (после rotate станет высотой)
                //   height = renderedW (после rotate станет шириной, но layout не меняется)
                imgEl.style.width = renderedH + 'px';
                imgEl.style.height = renderedW + 'px';
                imgEl.style.maxWidth = 'none';
                // transform-origin: top left → после rotate(-90deg)
                // картинка визуально уходит вверх от верхней левой точки.
                // translateX(-renderedH) в доповоротной системе → после rotate(-90deg)
                // даёт сдвиг вниз на renderedH в экранных координатах,
                // выравнивая верхний край картинки с верхом контейнера.
                imgEl.style.transform = 'rotate(-90deg) translateX(' + (-renderedH) + 'px)';
                imgEl.style.transformOrigin = 'top left';
                // Контейнер: прокрутка по горизонтали, высота = renderedH
                // Явно убрать padding (inline-стиль padding:12px перебивает CSS-правило).
                containerEl.classList.add('plan114-rotated');
                containerEl.style.padding = '0';
                containerEl.style.height = renderedH + 'px';
                containerEl.style.minWidth = '0';
                // Чтобы контейнер знал реальную ширину прокручиваемого контента,
                // создаём невидимый spacer шириной renderedW
                let spacer = containerEl.querySelector('.plan114-rotate-spacer');
                if (!spacer) {
                    spacer = document.createElement('div');
                    spacer.className = 'plan114-rotate-spacer';
                    spacer.style.cssText = 'display:block;height:0;pointer-events:none;';
                    containerEl.appendChild(spacer);
                }
                spacer.style.width = renderedW + 'px';
            });
        } else if (containerEl) {
            // Не отм-план или мобильный — сбросить стили поворота
            containerEl.classList.remove('plan114-rotated');
            containerEl.style.padding = '12px';
            containerEl.style.height = '';
            imgEl.style.transform = '';
            imgEl.style.transformOrigin = '';
            imgEl.style.width = '';
            imgEl.style.height = '';
            imgEl.style.maxWidth = '100%';
            const spacer = containerEl.querySelector('.plan114-rotate-spacer');
            if (spacer) spacer.remove();
        }
    } catch (err) {
        // Офлайн или ошибка загрузки — показать ошибку
        if (loadingEl) loadingEl.style.display = 'none';
        if (imgEl) imgEl.style.display = 'none';
        if (origLink) origLink.style.display = '';
        if (errorEl) errorEl.style.display = '';
        console.warn('[plan114] Не удалось загрузить план:', item.id, err && err.message);
    }
}

// ========================
// Public exports
// ========================
export { plan114InitEntryButton, plan114RenderList, PLAN114_ITEMS };
