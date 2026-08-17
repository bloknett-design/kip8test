/**
 * @module core/desktop
 * @description Desktop detail-in-panel rendering functions and breadcrumb setter.
 * Extracted from the monolithic src/index.html (lines 11679–11967 + flowmeterRenderDetailInPanel at 19682).
 */

// ============================================================
// ДЕСКТОП: RenderDetail-InPanel — рендер в detail-panel
// ============================================================

// Устанавливает breadcrumbs в заголовке detail-панели.
function setDetailBreadcrumb(pageType, itemName, groupName, groupNavPage) {
    const bar = document.getElementById('detailBreadcrumbContent');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (!bar) return;

    // Строим иерархический путь по дереву PAGE_PARENTS
    const fullPath = window.buildBreadcrumbPath(pageType);
    const path = fullPath.slice(0, -1);

    let html = '<span class="breadcrumb-link" onclick="navigateTo(\'dashboard\', false)">Главная</span>';

    for (let i = 0; i < path.length; i++) {
        const pageId = path[i];
        const label = window.PAGE_LABELS[pageId] || pageId;
        html += '<span class="breadcrumb-sep"> / </span>';
        html += '<span class="breadcrumb-link" onclick="closeDetailPanel(); navigateTo(\'' + pageId + '\', false)">' + label + '</span>';
    }

    if (groupName) {
        html += '<span class="breadcrumb-sep"> / </span>';
        if (groupNavPage) {
            html += '<span class="breadcrumb-link" onclick="closeDetailPanel(); navigateTo(\'' + groupNavPage + '\', false)">' + groupName + '</span>';
        } else {
            html += '<span class="breadcrumb-current">' + groupName + '</span>';
        }
    }

    if (itemName) {
        html += '<span class="breadcrumb-sep"> / </span>';
        html += '<span class="breadcrumb-current">' + itemName + '</span>';
    }

    bar.innerHTML = html;
    if (bcBar) bcBar.classList.add('active');
}

function devRenderDetailInPanel() {
    const devId = window._devDetailId;
    if (!devId || typeof window.devLoaded === 'undefined' || !window.devLoaded || typeof window.devData === 'undefined' || !window.devData) return;
    const dev = window.devData.devices.find(d => String(d['ID'] ?? '') === String(devId));
    if (!dev) return;
    const bodyEl = document.getElementById('detailPanelBody');
    const origContent = document.getElementById('deviceDetailContent');
    if (!bodyEl || !origContent) return;
    const name = dev['Наименование'] || '(без названия)';
    origContent.id = 'deviceDetailContent_orig';
    bodyEl.id = 'deviceDetailContent';
    window.devRenderDetail();
    bodyEl.id = 'detailPanelBody';
    origContent.id = 'deviceDetailContent';
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    document.querySelectorAll('.dev-card.detail-highlight, .lock-card.detail-highlight, .valve-card.detail-highlight, .regulator-card.detail-highlight, .project-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
    const activeCard = document.querySelector('.dev-card[data-dev-id="' + devId + '"]');
    if (activeCard) {
        activeCard.classList.add('detail-highlight');
        activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const devGroupCtx = window._devGroupCtx || {};
    const devGroupName = devGroupCtx.group || '';
    setDetailBreadcrumb('device-detail', name, devGroupName, 'dev-group');
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

function lockRenderDetailInPanel() {
    const lockId = window._lockDetailId;
    if (!lockId) return;
    const origContent = document.getElementById('lockoutDetailContent');
    const origTitle = document.getElementById('lockoutDetailTitle');
    const bodyEl = document.getElementById('detailPanelBody');
    if (!origContent || !bodyEl) return;
    origContent.id = 'lockoutDetailContent_orig';
    bodyEl.id = 'lockoutDetailContent';
    window.lockRenderDetail();
    bodyEl.id = 'detailPanelBody';
    origContent.id = 'lockoutDetailContent';
    const title = origTitle ? origTitle.textContent : 'Блокировка';
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    document.querySelectorAll('.lock-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
    const activeLockCard = document.querySelector('.lock-card[data-lock-id="' + lockId + '"]');
    if (activeLockCard) {
        activeLockCard.classList.add('detail-highlight');
        activeLockCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const lockGroupCtx = window._lockGroupCtx || {};
    const lockGroupName = lockGroupCtx.group || '';
    setDetailBreadcrumb('lockout-detail', title, lockGroupName, 'lock-group');
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

function valveRenderDetailInPanel() {
    const valveId = window._valveDetailId;
    if (!valveId) return;
    const origContent = document.getElementById('valveDetailContent');
    const origTitle = document.getElementById('valveDetailTitle');
    const bodyEl = document.getElementById('detailPanelBody');
    if (!origContent || !bodyEl) return;
    origContent.id = 'valveDetailContent_orig';
    bodyEl.id = 'valveDetailContent';
    window.valveRenderDetail();
    bodyEl.id = 'detailPanelBody';
    origContent.id = 'valveDetailContent';
    const title = origTitle ? origTitle.textContent : 'Клапан';
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    document.querySelectorAll('.valve-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
    const activeValveCard = document.querySelector('.valve-card[data-valve-id="' + valveId + '"]');
    if (activeValveCard) {
        activeValveCard.classList.add('detail-highlight');
        activeValveCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const valveGroupCtx = window._valveGroupCtx || {};
    const valveGroupName = valveGroupCtx.group || '';
    setDetailBreadcrumb('valve-detail', title, valveGroupName, 'valve-group');
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

function regulatorRenderDetailInPanel() {
    const regulatorId = window._regulatorDetailId;
    if (!regulatorId) return;
    const origContent = document.getElementById('regulatorDetailContent');
    const origTitle = document.getElementById('regulatorDetailTitle');
    const bodyEl = document.getElementById('detailPanelBody');
    if (!origContent || !bodyEl) return;
    origContent.id = 'regulatorDetailContent_orig';
    bodyEl.id = 'regulatorDetailContent';
    window.regulatorRenderDetail();
    bodyEl.id = 'detailPanelBody';
    origContent.id = 'regulatorDetailContent';
    const title = origTitle ? origTitle.textContent : 'Регулятор';
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    document.querySelectorAll('.regulator-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
    const activeRegCard = document.querySelector('.regulator-card[data-regulator-id="' + regulatorId + '"]');
    if (activeRegCard) {
        activeRegCard.classList.add('detail-highlight');
        activeRegCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const regulatorGroupCtx = window._regulatorGroupCtx || {};
    const regulatorGroupName = regulatorGroupCtx.group || '';
    setDetailBreadcrumb('regulator-detail', title, regulatorGroupName, 'regulator-group');
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

function projectRenderDetailInPanel() {
    const projectId = window._projectDetailId;
    if (!projectId) return;
    const origContent = document.getElementById('projectDetailContent');
    const origTitle = document.getElementById('projectDetailTitle');
    const bodyEl = document.getElementById('detailPanelBody');
    if (!origContent || !bodyEl) return;
    origContent.id = 'projectDetailContent_orig';
    bodyEl.id = 'projectDetailContent';
    window.projectRenderDetail();
    bodyEl.id = 'detailPanelBody';
    origContent.id = 'projectDetailContent';
    const title = origTitle ? origTitle.textContent : 'Проект';
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    document.querySelectorAll('.project-card.detail-highlight').forEach(el => el.classList.remove('detail-highlight'));
    const activeProjCard = document.querySelector('.project-card[data-project-id="' + projectId + '"]');
    if (activeProjCard) {
        activeProjCard.classList.add('detail-highlight');
        activeProjCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const projectGroupCtx = window._projectGroupCtx || {};
    const projectGroupName = projectGroupCtx.group || '';
    setDetailBreadcrumb('project-detail', title, projectGroupName, 'project-group');
    if (typeof window.KipFav !== 'undefined') window.KipFav.updateHeaderIcon();
}

function cableRenderDetailInPanel() {
    if (typeof window.KipCableJournal === 'undefined' || !window.KipCableJournal._viewing) return;
    const row = window.KipCableJournal._viewing;
    const columns = window.KipCableJournal._columns || [];
    const bodyEl = document.getElementById('detailPanelBody');
    if (!bodyEl) return;
    const cableTitle = row.designation || ('Запись №' + (row.num || '?'));
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
    let html = '<div class="dev-detail-card">';
    html += '<div class="ticket-detail-title" style="margin-bottom:14px;">' + (typeof window.devEsc === 'function' ? window.devEsc(cableTitle) : cableTitle) + '</div>';
    for (const f of order) {
        const col = columns.find(function(c) { return c.key === f.key; });
        if (!col) continue;
        const val = row[f.key];
        const raw = (val === null || val === undefined || val === '') ? '' : String(val);
        if (raw === '' || raw === 'Нет данных') continue;
        let valStr = raw;
        if (f.key === 'length_project' || f.key === 'length_actual') {
            valStr = raw + ' м';
        } else if (f.key === 'added_at') {
            valStr = window.KipCableJournal._formatDate(raw);
        }
        const grpCls = f.group ? ' cj-view-group-' + f.group : '';
        html += '<div class="dev-card-row' + grpCls + '">';
        html += '<div class="dev-card-label">' + (typeof window.devEsc === 'function' ? window.devEsc(col.label) : col.label) + '</div>';
        html += '<div class="dev-card-value">' + (typeof window.devEsc === 'function' ? window.devEsc(valStr) : valStr) + '</div>';
        html += '</div>';
    }
    html += '</div>';
    bodyEl.innerHTML = html;
    const footerEl = document.getElementById('detailPanelFooter');
    if (footerEl) {
        if (window.KipCableJournal._canEdit) {
            footerEl.innerHTML =
                '<button type="button" class="detail-footer-btn detail-footer-btn-edit" onclick="KipCableJournal.openEdit()">Править</button>';
        } else {
            footerEl.innerHTML = '';
        }
    }
    const panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');
    const bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');
    setDetailBreadcrumb('cable-journal-view', cableTitle, '', '');
}

function flowmeterRenderDetailInPanel() {
    var flowId = window._flowDetailId;
    if (!flowId) return;
    var m = null;
    for (var i = 0; i < window.FlowmeterData._METERS.length; i++) {
        if (window.FlowmeterData._METERS[i].id === flowId) { m = window.FlowmeterData._METERS[i]; break; }
    }
    if (!m) return;

    var bodyEl = document.getElementById('detailPanelBody');
    if (!bodyEl) return;

    bodyEl.innerHTML = window.FlowmeterData._buildDetailHtml(m);

    var footerEl = document.getElementById('detailPanelFooter');
    if (footerEl) footerEl.innerHTML = window.FlowmeterData._renderBottomBar(m);

    window.FlowmeterData.loadArchive(flowId, function(records) {
        var container = document.getElementById('flowArchiveContainer');
        if (container) {
            container.className = '';
            container.innerHTML = window.FlowmeterData._buildArchiveHtml(records, m);
        }
    });

    var panel = document.getElementById('detailPanel');
    if (panel) panel.classList.add('active');

    var bcBar = document.getElementById('detailBreadcrumbBar');
    if (bcBar) bcBar.classList.add('active');

    document.querySelectorAll('.flow-card.detail-highlight').forEach(function(el) { el.classList.remove('detail-highlight'); });
    var activeCard = document.querySelector('.flow-card[data-flow-id="' + flowId + '"]');
    if (activeCard) {
        activeCard.classList.add('detail-highlight');
        activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    setDetailBreadcrumb('flowmeter-detail', m.hoz, null, null);

    var titleEl = document.getElementById('detailPanelTitle');
    if (titleEl) titleEl.textContent = m.hoz;
}


export {
    setDetailBreadcrumb,
    devRenderDetailInPanel,
    lockRenderDetailInPanel,
    valveRenderDetailInPanel,
    regulatorRenderDetailInPanel,
    projectRenderDetailInPanel,
    cableRenderDetailInPanel,
    flowmeterRenderDetailInPanel
};
