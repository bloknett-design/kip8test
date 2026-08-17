/**
 * @module charts
 * KipCharts — графики и статистика по каталогам КИП ИОС
 * Extracted from src/index.html (lines 19736–20173)
 */

// ===== External dependency bridges =====
var navigateTo = window.navigateTo;

// KipCharts — Графики и статистика КИП ИОС
// ============================================================
const KipCharts = {

    _currentTab: 'devices',   // активная вкладка
    _cache: {},               // кэш загруженных данных {devices: [...], lockouts: [...], ...}

    // Месяцы года (римские)
    _MONTHS_ROMAN: ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII'],

    // Данные ППР на текущий год (2026) — Приборы
    // 3 серии: Калибровка (K), Поверка (П), Тех.обслуж. (ТО)
    // Источник: «Перечень КИП ИОС рабочий.xlsx» → лист «Диаграмма приборов»
    // Формулы: COUNTIF(Приборы[<месяц>], <код вида обслуживания>)
    _PPR_DEVICES: {
        title: 'Количество приборов по графику ППР по месяцам на 2026 год',
        series: [
            { name: 'Калибровка', code: 'К', color: '#4a90d9', values: [13, 33, 30, 45, 24, 28, 33, 34, 48, 16, 34, 35] },
            { name: 'Поверка', code: 'П', color: '#e07040', values: [12, 12, 4, 15, 0, 4, 6, 10, 4, 6, 1, 12] },
            { name: 'Тех. обслуж.', code: 'ТО', color: '#5ab870', values: [353, 354, 500, 320, 374, 496, 333, 353, 481, 358, 362, 485] }
        ]
    },

    // Данные ППР на текущий год (2026) — Блокировки (Схемы)
    // 2 серии: Кан.ремонт (Кр), Тех.обслуж. (ТО)
    _PPR_LOCKOUTS: {
        title: 'График ППР — Схемы на 2026 год',
        series: [
            { name: 'Кан. ремонт', code: 'Кр', color: '#4a90d9', values: [58, 49, 26, 31, 13, 38, 33, 34, 74, 23, 49, 98] },
            { name: 'Тех. обслуж.', code: 'ТО', color: '#5ab870', values: [87, 96, 210, 114, 132, 198, 112, 111, 162, 122, 96, 138] }
        ]
    },

    // Конфигурация разделов
    _SECTIONS: {
        devices: {
            jsonFile: 'data/devices.json',
            arrayKey: 'devices',
            groupField: 'Наименование',
            prodField: 'Место установки',
            typeField: 'Тип',
            label: 'Приборы',
            color: '#4a8fc7',
            colorLight: 'rgba(74,143,199,0.35)'
        },
        lockouts: {
            jsonFile: 'data/lockouts.json',
            arrayKey: 'lockouts',
            groupField: 'Параметр',
            prodField: 'Производство',
            label: 'Блокировки',
            color: '#b85a7a',
            colorLight: 'rgba(184,90,122,0.35)'
        },
        valves: {
            jsonFile: 'data/valves.json',
            arrayKey: 'valves',
            groupField: 'Тип, пропускная характеристика',
            prodField: 'Производство',
            label: 'Клапана',
            color: '#4a8a8c',
            colorLight: 'rgba(74,138,140,0.35)'
        },
        regulators: {
            jsonFile: 'data/regulators.json',
            arrayKey: 'regulators',
            groupField: 'Параметр',
            prodField: 'Производство',
            label: 'Регуляторы',
            color: '#7e5ab8',
            colorLight: 'rgba(126,90,184,0.35)'
        }
    },

    // Переключение вкладки
    switchTab: function(tab) {
        if (!this._SECTIONS[tab]) return;
        this._currentTab = tab;
        // Обновить UI вкладок
        var tabs = document.querySelectorAll('.charts-tab');
        for (var i = 0; i < tabs.length; i++) {
            var t = tabs[i];
            if (t.getAttribute('data-chart-tab') === tab) {
                t.classList.add('charts-tab-active');
            } else {
                t.classList.remove('charts-tab-active');
            }
        }
        this._renderTab(tab);
    },

    // Загрузка данных раздела
    _loadData: function(section, callback) {
        if (this._cache[section]) {
            callback(this._cache[section]);
            return;
        }
        var sec = this._SECTIONS[section];
        var ts = Date.now();
        fetch(sec.jsonFile + '?v=' + ts, {cache: 'no-store'})
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var items = data[sec.arrayKey] || [];
                KipCharts._cache[section] = items;
                callback(items);
            })
            .catch(function() {
                // Fallback — показать пустой массив
                KipCharts._cache[section] = [];
                callback([]);
            });
    },

    // Рендер вкладки
    _renderTab: function(tab) {
        var container = document.getElementById('chartsContent');
        if (!container) return;

        // Для вкладки Приборы — диаграмма ППР не зависит от JSON-данных
        if (tab === 'devices') {
            this._renderContent(tab, []);
            return;
        }

        container.innerHTML = '<div class="charts-loading">Загрузка…</div>';
        this._loadData(tab, function(items) {
            KipCharts._renderContent(tab, items);
        });
    },

    // Основной рендер контента
    _renderContent: function(tab, items) {
        var container = document.getElementById('chartsContent');
        if (!container) return;

        var sec = this._SECTIONS[tab];
        var html = '';

        // Для вкладки Приборы — только диаграмма ППР (как в Excel)
        if (tab === 'devices') {
            html += this._renderPPRChart(this._PPR_DEVICES);
            container.innerHTML = html;
            return;
        }

        // 0. График ППР (если есть для данного раздела)
        if (tab === 'lockouts') {
            html += this._renderPPRChart(this._PPR_LOCKOUTS);
        }

        // 1. Сводная статистика
        var totalItems = items.length;
        var groupField = sec.groupField;
        var prodField = sec.prodField;

        // Группировка по groupField
        var groups = {};
        var prods = {};
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            var gVal = (item[groupField] || '').toString().trim();
            if (gVal) groups[gVal] = (groups[gVal] || 0) + 1;
            var pVal = (item[prodField] || '').toString().trim();
            if (pVal) prods[pVal] = (prods[pVal] || 0) + 1;
        }
        var groupCount = Object.keys(groups).length;
        var prodCount = Object.keys(prods).length;

        // Для приборов — ещё по типу
        var typeCount = 0;
        if (sec.typeField) {
            var types = {};
            for (var i = 0; i < items.length; i++) {
                var tVal = (items[i][sec.typeField] || '').toString().trim();
                if (tVal) types[tVal] = (types[tVal] || 0) + 1;
            }
            typeCount = Object.keys(types).length;
        }

        // Сводная сетка
        html += '<div class="chart-stats-grid">';
        html += '<div class="chart-stat-card"><div class="chart-stat-value">' + totalItems + '</div><div class="chart-stat-label">Всего ' + sec.label.toLowerCase() + '</div></div>';
        html += '<div class="chart-stat-card"><div class="chart-stat-value">' + prodCount + '</div><div class="chart-stat-label">Производств</div></div>';
        html += '<div class="chart-stat-card"><div class="chart-stat-value">' + groupCount + '</div><div class="chart-stat-label">Уникальных ' + this._groupLabel(tab) + '</div></div>';
        if (sec.typeField) {
            html += '<div class="chart-stat-card"><div class="chart-stat-value">' + typeCount + '</div><div class="chart-stat-label">Уникальных типов</div></div>';
        } else {
            html += '<div class="chart-stat-card"><div class="chart-stat-value">' + this._avgPerProd(items, prodField) + '</div><div class="chart-stat-label">Среднее на пр-во</div></div>';
        }
        html += '</div>';

        // 2. График: Топ-10 по groupField
        var sortedGroups = Object.keys(groups).map(function(k) { return {name: k, count: groups[k]}; });
        sortedGroups.sort(function(a, b) { return b.count - a.count; });
        html += this._renderBarChart(
            'Топ-10 по ' + this._groupLabel(tab),
            sortedGroups.slice(0, 10),
            sec.color
        );

        // 3. График: Топ-10 производств
        var sortedProds = Object.keys(prods).map(function(k) { return {name: k, count: prods[k]}; });
        sortedProds.sort(function(a, b) { return b.count - a.count; });
        html += this._renderBarChart(
            'Топ-10 производств',
            sortedProds.slice(0, 10),
            sec.color
        );

        // 4. Для приборов — ещё и по типу
        if (sec.typeField) {
            var types = {};
            for (var i = 0; i < items.length; i++) {
                var tVal = (items[i][sec.typeField] || '').toString().trim();
                if (tVal) types[tVal] = (types[tVal] || 0) + 1;
            }
            var sortedTypes = Object.keys(types).map(function(k) { return {name: k, count: types[k]}; });
            sortedTypes.sort(function(a, b) { return b.count - a.count; });
            html += this._renderBarChart(
                'Топ-10 типов приборов',
                sortedTypes.slice(0, 10),
                sec.color
            );
        }

        container.innerHTML = html;
    },

    // ============================================================
    // Рендер графика ППР — группированная вертикальная гистограмма
    // (как в Excel: clustered column chart с легендой и итогами)
    // ============================================================
    _renderPPRChart: function(pprData) {
        var series = pprData.series;
        var numSeries = series.length;
        var numMonths = 12;

        // Найти максимальное значение для масштаба оси Y
        var maxVal = 0;
        for (var s = 0; s < numSeries; s++) {
            for (var m = 0; m < numMonths; m++) {
                if (series[s].values[m] > maxVal) maxVal = series[s].values[m];
            }
        }
        if (maxVal === 0) maxVal = 1;

        // Округлить maxVal вверх до красивого числа
        var niceMax = this._niceMax(maxVal);

        // Ось Y: 5 делений
        var ySteps = 5;
        var yStepVal = niceMax / ySteps;

        var html = '<div class="chart-card ppr-chart-card">';
        html += '<div class="ppr-chart-header">';
        html += '<div class="ppr-chart-title">' + this._escHtml(pprData.title) + '</div>';
        // Легенда
        html += '<div class="ppr-legend">';
        for (var s = 0; s < numSeries; s++) {
            html += '<div class="ppr-legend-item">';
            html += '<span class="ppr-legend-dot" style="background:' + series[s].color + ';"></span>';
            html += '<span class="ppr-legend-code">' + this._escHtml(series[s].code) + '</span>';
            html += '<span class="ppr-legend-name">' + this._escHtml(series[s].name) + '</span>';
            html += '</div>';
        }
        html += '</div>';
        html += '</div>';

        // Тело графика
        html += '<div class="ppr-chart-body">';

        // Оси + область графика
        html += '<div class="ppr-chart-area">';

        // Ось Y (метки слева)
        html += '<div class="ppr-y-axis">';
        for (var i = ySteps; i >= 0; i--) {
            var yVal = Math.round(yStepVal * i);
            html += '<div class="ppr-y-label">' + yVal + '</div>';
        }
        html += '</div>';

        // Сетка + столбцы
        html += '<div class="ppr-chart-grid">';

        // Горизонтальные линии сетки
        for (var i = 0; i <= ySteps; i++) {
            var bottomPct = (i / ySteps) * 100;
            html += '<div class="ppr-grid-line" style="bottom:' + bottomPct + '%;"></div>';
        }

        // Группы столбцов по месяцам
        for (var m = 0; m < numMonths; m++) {
            html += '<div class="ppr-month-group">';

            // Столбцы серий
            html += '<div class="ppr-bars-row">';
            for (var s = 0; s < numSeries; s++) {
                var val = series[s].values[m];
                var heightPct = (val / niceMax) * 100;
                html += '<div class="ppr-bar-cell">';
                if (val > 0) {
                    html += '<div class="ppr-bar" style="height:' + heightPct + '%;background:' + series[s].color + ';" title="' + this._escHtml(series[s].name) + ': ' + val + '">';
                    // Значение над столбцом (показываем если достаточно высокий)
                    if (heightPct > 8) {
                        html += '<span class="ppr-bar-val">' + val + '</span>';
                    }
                    html += '</div>';
                }
                html += '</div>';
            }
            html += '</div>';

            // Метка месяца
            html += '<div class="ppr-month-label">' + this._MONTHS_ROMAN[m] + '</div>';
            html += '</div>';
        }

        html += '</div>'; // .ppr-chart-grid
        html += '</div>'; // .ppr-chart-area

        // Строка итогов (сумма по каждой серии)
        html += '<div class="ppr-totals-row">';
        html += '<div class="ppr-totals-label">Итого:</div>';
        for (var s = 0; s < numSeries; s++) {
            var total = 0;
            for (var m = 0; m < numMonths; m++) total += series[s].values[m];
            html += '<div class="ppr-totals-item">';
            html += '<span class="ppr-legend-dot" style="background:' + series[s].color + ';"></span>';
            html += '<span class="ppr-legend-code">' + this._escHtml(series[s].code) + '</span>';
            html += '<span class="ppr-totals-value">' + total + '</span>';
            html += '</div>';
        }
        html += '</div>';

        html += '</div>'; // .ppr-chart-body
        html += '</div>'; // .chart-card

        return html;
    },

    // Красивое округление максимума для оси Y
    _niceMax: function(val) {
        if (val <= 0) return 10;
        var mag = Math.pow(10, Math.floor(Math.log10(val)));
        var norm = val / mag;
        var nice;
        if (norm <= 1) nice = 1;
        else if (norm <= 2) nice = 2;
        else if (norm <= 5) nice = 5;
        else nice = 10;
        return nice * mag;
    },

    // Название группировки для заголовка
    _groupLabel: function(tab) {
        switch (tab) {
            case 'devices': return 'наименований';
            case 'lockouts': return 'параметров';
            case 'valves': return 'типов клапанов';
            case 'regulators': return 'параметров';
            default: return 'групп';
        }
    },

    // Среднее количество на производство
    _avgPerProd: function(items, prodField) {
        var prods = {};
        for (var i = 0; i < items.length; i++) {
            var p = (items[i][prodField] || '').toString().trim();
            if (p) prods[p] = (prods[p] || 0) + 1;
        }
        var keys = Object.keys(prods);
        if (keys.length === 0) return '0';
        var sum = 0;
        for (var i = 0; i < keys.length; i++) sum += prods[keys[i]];
        return (sum / keys.length).toFixed(1);
    },

    // Рендер горизонтальной столбчатой диаграммы
    _renderBarChart: function(title, data, color) {
        if (!data || data.length === 0) return '';
        var maxVal = data[0].count;
        if (maxVal === 0) maxVal = 1;

        var html = '<div class="chart-card">';
        html += '<div class="chart-card-title">' + this._escHtml(title) + '</div>';
        html += '<div class="chart-card-body">';

        for (var i = 0; i < data.length; i++) {
            var d = data[i];
            var pct = Math.round((d.count / maxVal) * 100);
            html += '<div class="chart-bar-row">';
            html += '<div class="chart-bar-label" title="' + this._escHtml(d.name) + '">' + this._escHtml(d.name) + '</div>';
            html += '<div class="chart-bar-track"><div class="chart-bar-fill" style="width:' + pct + '%;background:' + color + ';"></div></div>';
            html += '<div class="chart-bar-value">' + d.count + '</div>';
            html += '</div>';
        }

        html += '</div></div>';
        return html;
    },

    // HTML-экранирование
    _escHtml: function(str) {
        if (str === null || str === undefined) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },

    // Инициализация кнопки входа (вызывается при загрузке КИП ИОС)
    initEntryButton: function() {
        var btn = document.getElementById('chartsEntryBtn');
        if (!btn) return;
        btn.onclick = function() { navigateTo('charts'); };
    },

    // Обновление подзаголовка кнопки
    updateEntrySublabel: function() {
        var btn = document.getElementById('chartsEntryBtn');
        if (!btn) return;
        var sub = btn.querySelector('.menu-btn-sublabel');
        if (!sub) return;
        // Показать общее количество записей во всех 4 разделах
        var total = 0;
        var sections = ['devices', 'lockouts', 'valves', 'regulators'];
        for (var i = 0; i < sections.length; i++) {
            if (this._cache[sections[i]]) {
                total += this._cache[sections[i]].length;
            }
        }
        if (total > 0) {
            sub.textContent = total + ' записей КИП ИОС';
        }
    },

    // Открытие страницы (вызывается из navigateTo)
    onPageOpen: function() {
        this.switchTab(this._currentTab);
    }
};

// ===== Window bridge (for inline HTML event handlers) =====
window.KipCharts = KipCharts;

export { KipCharts };
export default KipCharts;
