/**
 * @module app
 * @description Entry point for kip8test PWA.
 * Imports all modules in the correct initialization order,
 * exports all public functions/objects to `window` so inline HTML
 * onclick handlers still work, and runs initialization.
 *
 * INITIALIZATION ORDER (critical):
 *  1. localStorage isolation — must run FIRST
 *  2. Theme IIFE — apply saved theme early
 *  3. Utility functions — isDesktop, showToast, etc.
 *  4. State module — shared state setters/getters
 *  5. All other modules — navigation, catalogs, calculators, etc.
 *  6. Custom select — refreshCustomSelects/rebuildCustomSelect
 *  7. Scroll audit + adaptive headers — fitPageHeaderTitle
 *  8. Pinch-zoom wraps navigateTo — must run AFTER navigateTo is on window
 *  9. SW registration — service worker
 * 10. Refresh/connection — updateConnectionIndicator
 * 11. Window.onload — KipAuth.bootstrap() + initDesktopSidebar()
 */

// ============================================================
// 1. localStorage isolation (must be first!)
// ============================================================
import './core/local-storage.js';

// ============================================================
// 2. Theme (apply early, before DOM renders)
// ============================================================
import { toggleTheme, updateThemeLabel, updateBuoyImages, updateLogoImage } from './calculators/theme.js';

// ============================================================
// 3. Core utilities (used by everything)
// ============================================================
import {
    isDesktop, isTablet, showToast, kipConfirm, kipPrompt,
    parseLocaleNumber, formatNumber, roundNumber,
    validateField, clearFieldError, hasValidationErrors,
    validateNumericField, validatePositiveField, validateNonNegativeField, validateRangeField
} from './core/utils.js';

// ============================================================
// 4. State module (shared state setters/getters)
// ============================================================
import {
    detailState, groupState,
    setDevDetailId, setLockDetailId, setValveDetailId, setRegulatorDetailId,
    setProjectDetailId, setFlowDetailId, setTicketDetailCatId, setTicketDetailIndex,
    setDevGroupCtx, setLockGroupCtx, setValveGroupCtx, setRegulatorGroupCtx, setProjectGroupCtx,
    getDevDetailId, getLockDetailId, getValveDetailId, getRegulatorDetailId,
    getProjectDetailId, getFlowDetailId, getTicketDetailCatId, getTicketDetailIndex,
    getDevGroupCtx, getLockGroupCtx, getValveGroupCtx, getRegulatorGroupCtx, getProjectGroupCtx,
    resetAllDetailIds, resetAllGroupCtxs
} from './core/state.js';

// ============================================================
// 5. Navigation + Desktop
// ============================================================
import {
    DESKTOP_DETAIL_PAGES, DESKTOP_MASTER_PAGES,
    PAGE_PARENTS, PAGE_LABELS, SUBSECTIONS,
    pageHistory, isNavigating,
    navigateTo, goBack, chevronTap,
    openDetailPanel, closeDetailPanel, swapDetailPanels,
    openLibraryViewer, updateChevronArrows,
    buildBreadcrumbPath, updateDesktopBreadcrumb, updateBottomNavActive
} from './core/navigation.js';

import {
    _auditScrollState
} from './core/scroll-audit.js';
// fitPageHeaderTitle and resetZoomOnLeave are set on window by scroll-audit.js IIFEs

import {
    setDetailBreadcrumb,
    devRenderDetailInPanel, lockRenderDetailInPanel,
    valveRenderDetailInPanel, regulatorRenderDetailInPanel,
    projectRenderDetailInPanel, cableRenderDetailInPanel,
    flowmeterRenderDetailInPanel
} from './core/desktop.js';

// ============================================================
// 6. Sidebar + Pinned + Pin Sheet
// ============================================================
import { toggleSidebar, toggleDesktopSidebar, initDesktopSidebar, toggleSidebarGroup, updateDesktopTopBarTabs } from './core/sidebar.js';
import { getPinnedItems, isPinned, togglePin, renderPinnedItems, wrapSubsectionItems, setPinnedItems } from './core/pinned.js';
import { openPinSheet, closePinSheet, executePinToggle, movePinnedItem, renderPinSheetExtraActions } from './core/pin-sheet.js';

// ============================================================
// 7. Custom Select
// ============================================================
import { refreshCustomSelects, rebuildCustomSelect } from './core/custom-select.js';

// ============================================================
// 8. Catalogs — Devices
// ============================================================
import {
    devData, devLoaded,
    devInit, devInitEntryButton, devInitSorted,
    devForceRefresh, devRenderSorted, devOpenDetail,
    devRenderDetail, devToggleGroup, devRenderGroup,
    devLoad, devUpdateFilterButton, devToggleTypeFilter,
    devShowMore, devEsc, kipIOSUpdateLastChange
} from './catalogs/devices.js';

// Catalogs — Lockouts
import {
    lockData, lockLoaded,
    lockInitEntryButton, lockInitSorted,
    lockForceRefresh, lockRenderSorted, lockOpenDetail,
    lockRenderDetail, lockToggleGroup, lockRenderGroup
} from './catalogs/lockouts.js';

// Catalogs — Valves
import {
    valveData, valveLoaded,
    valveInitSorted, valveForceRefresh, valveRenderSorted,
    valveToggleGroup, valveRenderGroup,
    valveOpenDetail, valveRenderDetail,
    valveInitEntryButton, valveUpdateEntrySublabel
} from './catalogs/valves.js';

// Catalogs — Regulators
import {
    regulatorData, regulatorLoaded,
    regulatorInitSorted, regulatorForceRefresh, regulatorRenderSorted,
    regulatorToggleGroup, regulatorRenderGroup,
    regulatorOpenDetail, regulatorRenderDetail,
    regulatorInitEntryButton, regulatorUpdateEntrySublabel
} from './catalogs/regulators.js';

// Catalogs — Projects
import {
    projectData, projectLoaded,
    projectsInitEntryButton, projectsUpdateEntrySublabel,
    projectInitSorted,
    projectsRenderSorted, projectOpenDetail, projectOpenByProjectNo,
    projectRenderDetail, projectsToggleGroup, projectsRenderGroup,
    kipIsEmptyProjectNo, kipSplitProjectValues, kipSplitIdValues, kipRenderMultiLinks
} from './catalogs/projects.js';

// Catalogs — Cross-refs (all exported as namespace for Object.assign to window)
import * as crossrefs from './catalogs/crossrefs.js';

// Catalogs — Cable entry + Plan 114 helpers
import { cablesInitEntryButton, cablesUpdateEntrySublabel, plan114OpenView } from './catalogs/cable-entry.js';

// ============================================================
// 9. Modules
// ============================================================
import { KipAuth } from './modules/auth.js';
import { KipFav, KipFavNotes } from './modules/favorites.js';
import { KipCableJournal } from './modules/cable-journal.js';
import { FlowUserView, FlowmeterData } from './modules/flowmeter.js';
import { KipCharts } from './modules/charts.js';
import { KipAdmin } from './modules/admin.js';
import { msInit, msSetDifficulty, msRender, secretTapHandler } from './modules/minesweeper.js';
import {
    pbInit, pbRender,
    pbToggleFavorite, pbEditNote,
    pbToggleSection, pbToggleSubgroup, pbToggleFavFilter,
    pbIsFavorite, pbGetFavoritesCount
} from './modules/phonebook.js';
import {
    _ticketsData, TICKET_IDS,
    loadTicketsData, renderTickets, ticketSelectItem,
    initTicketsPage, toggleTicketItem,
    openTicketImage, closeTicketImage,
    goToTicket, escHtml, gdriveShareToDirect,
    ticketRenderDetailInPanel
} from './modules/exams.js';
import { plan114InitEntryButton, plan114RenderList } from './modules/plan114.js';
import { calcGeoCircle, calcGeoRing, calcGeoCylinder, calcGeoHorizCyl, calcGeoSphere, calcGeoCone } from './modules/geometry.js';
import { showAboutModal, closeAboutModal, whatsNewMarkRead, whatsNewHasUnread, whatsNewUpdateBtnState } from './modules/whats-new.js';

// ============================================================
// 10. Calculators
// ============================================================
import {
    convertUnits, convertTemp, calcScaleSignal,
    showConverterTable, showTempTable,
    calcPressureError, calcLevelError, calcFlowmeterError,
    calcErrorGOST,
    calcGenericNumber, calcGenericUnderline, calcGenericCircle, calcGenericFraction
} from './calculators/converters.js';
import {
    calcRtdError, calcTcError, calcScaleError,
    updateRtdTypeOptions, updateRtdClassOptions,
    updateTcRanges, toggleScaleTypeFields
} from './calculators/rtd-tc.js';
import { calcTempSensor, updateTempSensorOptions, calcRtdResistance, calcCuResistance, calcTcVoltage } from './calculators/electro.js';
import {
    calculateBuoyCalibration, calcBuoyancyMass,
    copyBuoyTable, copyScaleTable, copyCalcTable,
    selectCalibMethod, setCalibMethodOnForm, updateBuoyCalcTitle,
    getSignalRangeAndUnit,
    setLiquidDensity, updateBuoySignalUnit, clearBuoyCustomFields,
    calcBuoyFromLevel, calcBuoyFromMass, calcBuoyFromSignal
} from './calculators/buoy.js';
import {
    calcOrificeDp, calcOrificeFlow, calcOrificeDiameter, calcOrificeQuick,
    updateOqMediumDefaults, updateOpForm, updateOpDpForm, updateOpFlowForm
} from './calculators/orifice.js';
import { calcCircuitBreaker, updateCbForm, updateCbCosPhi, updateCbCableTable } from './calculators/circuit-breaker.js';
import { calcErrorKit, addKitDevice, removeKitDevice, updateKitLimitMsg } from './calculators/error-kit.js';

// ============================================================
// 11. Refresh + Connection
// ============================================================
import {
    refreshAppData, forceFullRefresh, forceDesktopRefresh,
    updateConnectionIndicator, showCloudBriefly,
    checkRealConnection, periodicConnectionCheck
} from './core/refresh.js';

// ============================================================
// 12. SW Registration (self-executing on import)
// ============================================================
import './core/sw-register.js';


// ============================================
// WINDOW EXPORTS — for inline onclick handlers
// and inter-module communication via window.*
// ============================================

// --- Objects / Classes ---
window.KipAuth       = KipAuth;
window.KipFav        = KipFav;
window.KipFavNotes   = KipFavNotes;
window.KipCableJournal = KipCableJournal;
window.FlowUserView  = FlowUserView;
window.FlowmeterData = FlowmeterData;
window.KipCharts     = KipCharts;
window.KipAdmin      = KipAdmin;

// --- Navigation ---
window.navigateTo      = navigateTo;
window.goBack         = goBack;
window.chevronTap     = chevronTap;
window.openDetailPanel  = openDetailPanel;
window.closeDetailPanel = closeDetailPanel;
window.swapDetailPanels = swapDetailPanels;
window.openLibraryViewer   = openLibraryViewer;
window.updateChevronArrows = updateChevronArrows;
window.buildBreadcrumbPath = buildBreadcrumbPath;
window.updateDesktopBreadcrumb = updateDesktopBreadcrumb;
window.updateBottomNavActive = updateBottomNavActive;
window.PAGE_PARENTS   = PAGE_PARENTS;
window.PAGE_LABELS    = PAGE_LABELS;
window.SUBSECTIONS    = SUBSECTIONS;
window.pageHistory    = pageHistory;
window.isNavigating   = isNavigating;
window.DESKTOP_DETAIL_PAGES = DESKTOP_DETAIL_PAGES;
window.DESKTOP_MASTER_PAGES = DESKTOP_MASTER_PAGES;

// --- Sidebar ---
window.toggleSidebar       = toggleSidebar;
window.toggleDesktopSidebar = toggleDesktopSidebar;
window.toggleSidebarGroup  = toggleSidebarGroup;
window.initDesktopSidebar  = initDesktopSidebar;
window.updateDesktopTopBarTabs = updateDesktopTopBarTabs;

// --- Pin Sheet ---
window.openPinSheet   = openPinSheet;
window.closePinSheet  = closePinSheet;
window.executePinToggle = executePinToggle;
window.movePinnedItem = movePinnedItem;

// --- Pinned ---
window.getPinnedItems   = getPinnedItems;
window.isPinned         = isPinned;
window.togglePin        = togglePin;
window.renderPinnedItems = renderPinnedItems;
window.wrapSubsectionItems = wrapSubsectionItems;
window.setPinnedItems   = setPinnedItems;

// --- Core utilities ---
window.isDesktop        = isDesktop;
window.isTablet         = isTablet;
window.showToast        = showToast;
window.kipConfirm       = kipConfirm;
window.kipPrompt        = kipPrompt;
window.parseLocaleNumber = parseLocaleNumber;
window.formatNumber     = formatNumber;
window.roundNumber      = roundNumber;
window.validateField    = validateField;
window.clearFieldError  = clearFieldError;
window.hasValidationErrors = hasValidationErrors;
window.validateNumericField   = validateNumericField;
window.validatePositiveField  = validatePositiveField;
window.validateNonNegativeField = validateNonNegativeField;
window.validateRangeField     = validateRangeField;

// --- Theme ---
window.toggleTheme    = toggleTheme;
window.updateThemeLabel = updateThemeLabel;
window.updateBuoyImages = updateBuoyImages;
window.updateLogoImage  = updateLogoImage;

// --- State ---
window.detailState = detailState;
window.groupState  = groupState;
window.setDevDetailId       = setDevDetailId;
window.setLockDetailId      = setLockDetailId;
window.setValveDetailId     = setValveDetailId;
window.setRegulatorDetailId = setRegulatorDetailId;
window.setProjectDetailId   = setProjectDetailId;
window.setFlowDetailId      = setFlowDetailId;
window.setTicketDetailCatId = setTicketDetailCatId;
window.setTicketDetailIndex = setTicketDetailIndex;
window.setDevGroupCtx       = setDevGroupCtx;
window.setLockGroupCtx      = setLockGroupCtx;
window.setValveGroupCtx     = setValveGroupCtx;
window.setRegulatorGroupCtx = setRegulatorGroupCtx;
window.setProjectGroupCtx   = setProjectGroupCtx;
window.getDevDetailId       = getDevDetailId;
window.getLockDetailId      = getLockDetailId;
window.getValveDetailId     = getValveDetailId;
window.getRegulatorDetailId = getRegulatorDetailId;
window.getProjectDetailId   = getProjectDetailId;
window.getFlowDetailId      = getFlowDetailId;
window.getTicketDetailCatId = getTicketDetailCatId;
window.getTicketDetailIndex = getTicketDetailIndex;
window.getDevGroupCtx       = getDevGroupCtx;
window.getLockGroupCtx      = getLockGroupCtx;
window.getValveGroupCtx     = getValveGroupCtx;
window.getRegulatorGroupCtx = getRegulatorGroupCtx;
window.getProjectGroupCtx   = getProjectGroupCtx;
window.resetAllDetailIds    = resetAllDetailIds;
window.resetAllGroupCtxs    = resetAllGroupCtxs;

// --- Desktop detail-in-panel ---
window.setDetailBreadcrumb       = setDetailBreadcrumb;
window.devRenderDetailInPanel    = devRenderDetailInPanel;
window.lockRenderDetailInPanel   = lockRenderDetailInPanel;
window.valveRenderDetailInPanel  = valveRenderDetailInPanel;
window.regulatorRenderDetailInPanel = regulatorRenderDetailInPanel;
window.projectRenderDetailInPanel   = projectRenderDetailInPanel;
window.cableRenderDetailInPanel     = cableRenderDetailInPanel;
window.flowmeterRenderDetailInPanel = flowmeterRenderDetailInPanel;

// --- Scroll audit ---
// fitPageHeaderTitle and _auditScrollState
// fitPageHeaderTitle is already set on window by scroll-audit.js IIFE
window._auditScrollState = _auditScrollState;

// --- Custom Select ---
// refreshCustomSelects and rebuildCustomSelect are already set on window
// by custom-select.js IIFE, but we also export them for ES import usage.
window.refreshCustomSelects = refreshCustomSelects;
window.rebuildCustomSelect  = rebuildCustomSelect;

// --- Devices catalog ---
window.devData             = devData;
window.devLoaded           = devLoaded;
window.devInit             = devInit;
window.devInitEntryButton  = devInitEntryButton;
window.devInitSorted       = devInitSorted;
window.devForceRefresh     = devForceRefresh;
window.devRenderSorted     = devRenderSorted;
window.devOpenDetail       = devOpenDetail;
window.devRenderDetail     = devRenderDetail;
window.devToggleGroup      = devToggleGroup;
window.devRenderGroup      = devRenderGroup;
window.devLoad             = devLoad;
window.devUpdateFilterButton = devUpdateFilterButton;
window.devToggleTypeFilter = devToggleTypeFilter;
window.devShowMore         = devShowMore;
window.devEsc              = devEsc;
window.kipIOSUpdateLastChange = kipIOSUpdateLastChange;

// --- Lockouts catalog ---
window.lockData            = lockData;
window.lockLoaded          = lockLoaded;
window.lockInitEntryButton = lockInitEntryButton;
window.lockInitSorted      = lockInitSorted;
window.lockForceRefresh    = lockForceRefresh;
window.lockRenderSorted    = lockRenderSorted;
window.lockOpenDetail      = lockOpenDetail;
window.lockRenderDetail    = lockRenderDetail;
window.lockToggleGroup     = lockToggleGroup;
window.lockRenderGroup     = lockRenderGroup;

// --- Valves catalog ---
window.valveData              = valveData;
window.valveLoaded            = valveLoaded;
window.valveInitSorted        = valveInitSorted;
window.valveForceRefresh      = valveForceRefresh;
window.valveRenderSorted      = valveRenderSorted;
window.valveToggleGroup       = valveToggleGroup;
window.valveRenderGroup       = valveRenderGroup;
window.valveOpenDetail        = valveOpenDetail;
window.valveRenderDetail      = valveRenderDetail;
window.valveInitEntryButton   = valveInitEntryButton;
window.valveUpdateEntrySublabel = valveUpdateEntrySublabel;

// --- Regulators catalog ---
window.regulatorData              = regulatorData;
window.regulatorLoaded            = regulatorLoaded;
window.regulatorInitSorted        = regulatorInitSorted;
window.regulatorForceRefresh      = regulatorForceRefresh;
window.regulatorRenderSorted      = regulatorRenderSorted;
window.regulatorToggleGroup       = regulatorToggleGroup;
window.regulatorRenderGroup       = regulatorRenderGroup;
window.regulatorOpenDetail        = regulatorOpenDetail;
window.regulatorRenderDetail      = regulatorRenderDetail;
window.regulatorInitEntryButton   = regulatorInitEntryButton;
window.regulatorUpdateEntrySublabel = regulatorUpdateEntrySublabel;

// --- Projects catalog ---
window.projectData              = projectData;
window.projectLoaded            = projectLoaded;
window.projectsInitEntryButton  = projectsInitEntryButton;
window.projectsUpdateEntrySublabel = projectsUpdateEntrySublabel;
window.projectInitSorted        = projectInitSorted;
window.projectsRenderSorted     = projectsRenderSorted;
window.projectOpenDetail        = projectOpenDetail;
window.projectOpenByProjectNo   = projectOpenByProjectNo;
window.projectRenderDetail      = projectRenderDetail;
window.projectsToggleGroup      = projectsToggleGroup;
window.projectsRenderGroup      = projectsRenderGroup;
window.kipIsEmptyProjectNo      = kipIsEmptyProjectNo;
window.kipSplitProjectValues    = kipSplitProjectValues;
window.kipSplitIdValues         = kipSplitIdValues;
window.kipRenderMultiLinks      = kipRenderMultiLinks;

// --- Cable entry ---
window.cablesInitEntryButton    = cablesInitEntryButton;
window.cablesUpdateEntrySublabel = cablesUpdateEntrySublabel;
window.plan114OpenView          = plan114OpenView;

// --- Cross-refs (all exported functions) ---
Object.assign(window, crossrefs);

// --- Exams / Tickets ---
window._ticketsData    = _ticketsData;
window.TICKET_IDS     = TICKET_IDS;
window.loadTicketsData = loadTicketsData;
window.renderTickets   = renderTickets;
window.ticketSelectItem = ticketSelectItem;
window.initTicketsPage = initTicketsPage;
window.toggleTicketItem = toggleTicketItem;
window.openTicketImage = openTicketImage;
window.closeTicketImage = closeTicketImage;
window.goToTicket      = goToTicket;
window.escHtml         = escHtml;
window.gdriveShareToDirect = gdriveShareToDirect;
window.ticketRenderDetailInPanel = ticketRenderDetailInPanel;

// --- Phonebook ---
window.pbInit           = pbInit;
window.pbRender         = pbRender;
window.pbToggleFavorite = pbToggleFavorite;
window.pbEditNote       = pbEditNote;
window.pbToggleSection  = pbToggleSection;
window.pbToggleSubgroup = pbToggleSubgroup;
window.pbToggleFavFilter = pbToggleFavFilter;
window.pbIsFavorite     = pbIsFavorite;
window.pbGetFavoritesCount = pbGetFavoritesCount;

// --- Minesweeper ---
window.msInit          = msInit;
window.msSetDifficulty = msSetDifficulty;
window.msRender        = msRender;
window.secretTapHandler = secretTapHandler;

// --- Plan 114 ---
window.plan114InitEntryButton = plan114InitEntryButton;
window.plan114RenderList      = plan114RenderList;

// --- Geometry ---
window.calcGeoCircle    = calcGeoCircle;
window.calcGeoRing      = calcGeoRing;
window.calcGeoCylinder  = calcGeoCylinder;
window.calcGeoHorizCyl  = calcGeoHorizCyl;
window.calcGeoSphere    = calcGeoSphere;
window.calcGeoCone      = calcGeoCone;

// --- What's New ---
window.showAboutModal       = showAboutModal;
window.closeAboutModal      = closeAboutModal;
window.whatsNewMarkRead     = whatsNewMarkRead;
window.whatsNewHasUnread    = whatsNewHasUnread;
window.whatsNewUpdateBtnState = whatsNewUpdateBtnState;

// --- Converters ---
window.convertUnits      = convertUnits;
window.convertTemp       = convertTemp;
window.calcScaleSignal   = calcScaleSignal;
window.showConverterTable = showConverterTable;
window.showTempTable     = showTempTable;
window.calcPressureError = calcPressureError;
window.calcLevelError    = calcLevelError;
window.calcFlowmeterError = calcFlowmeterError;
window.calcErrorGOST     = calcErrorGOST;
window.calcGenericNumber   = calcGenericNumber;
window.calcGenericUnderline = calcGenericUnderline;
window.calcGenericCircle   = calcGenericCircle;
window.calcGenericFraction = calcGenericFraction;

// --- RTD / TC ---
window.calcRtdError           = calcRtdError;
window.calcTcError            = calcTcError;
window.calcScaleError         = calcScaleError;
window.updateRtdTypeOptions   = updateRtdTypeOptions;
window.updateRtdClassOptions  = updateRtdClassOptions;
window.updateTcRanges         = updateTcRanges;
window.toggleScaleTypeFields  = toggleScaleTypeFields;

// --- Electro / Temp Sensors ---
window.calcTempSensor         = calcTempSensor;
window.updateTempSensorOptions = updateTempSensorOptions;
window.calcRtdResistance      = calcRtdResistance;
window.calcCuResistance       = calcCuResistance;
window.calcTcVoltage          = calcTcVoltage;

// --- Buoy ---
window.calculateBuoyCalibration = calculateBuoyCalibration;
window.calcBuoyancyMass        = calcBuoyancyMass;
window.copyBuoyTable           = copyBuoyTable;
window.copyScaleTable          = copyScaleTable;
window.copyCalcTable           = copyCalcTable;
window.selectCalibMethod       = selectCalibMethod;
window.setCalibMethodOnForm     = setCalibMethodOnForm;
window.updateBuoyCalcTitle     = updateBuoyCalcTitle;
window.getSignalRangeAndUnit    = getSignalRangeAndUnit;
window.setLiquidDensity        = setLiquidDensity;
window.updateBuoySignalUnit    = updateBuoySignalUnit;
window.clearBuoyCustomFields   = clearBuoyCustomFields;
window.calcBuoyFromLevel       = calcBuoyFromLevel;
window.calcBuoyFromMass        = calcBuoyFromMass;
window.calcBuoyFromSignal      = calcBuoyFromSignal;

// --- Orifice ---
window.calcOrificeDp        = calcOrificeDp;
window.calcOrificeFlow     = calcOrificeFlow;
window.calcOrificeDiameter = calcOrificeDiameter;
window.calcOrificeQuick    = calcOrificeQuick;
window.updateOqMediumDefaults = updateOqMediumDefaults;
window.updateOpForm        = updateOpForm;
window.updateOpDpForm      = updateOpDpForm;
window.updateOpFlowForm    = updateOpFlowForm;

// --- Circuit Breaker ---
window.calcCircuitBreaker = calcCircuitBreaker;
window.updateCbForm      = updateCbForm;
window.updateCbCosPhi    = updateCbCosPhi;
window.updateCbCableTable = updateCbCableTable;

// --- Error Kit ---
window.calcErrorKit    = calcErrorKit;
window.addKitDevice    = addKitDevice;
window.removeKitDevice = removeKitDevice;
window.updateKitLimitMsg = updateKitLimitMsg;

// --- Refresh / Connection ---
window.refreshAppData          = refreshAppData;
window.forceFullRefresh        = forceFullRefresh;
window.forceDesktopRefresh     = forceDesktopRefresh;
window.updateConnectionIndicator = updateConnectionIndicator;
window.showCloudBriefly        = showCloudBriefly;
window.checkRealConnection     = checkRealConnection;
window.periodicConnectionCheck = periodicConnectionCheck;


// ============================================
// PINCH-ZOOM WRAPPER
// Must run AFTER navigateTo is on window.
// Wraps navigateTo so that pinch-zoom is reset
// when navigating away from a page.
// ============================================
if (typeof window.resetZoomOnLeave === 'function') {
    let _origNavigateTo = window.navigateTo;
    window.navigateTo = function(page, addToHistory) {
        window.resetZoomOnLeave();
        return _origNavigateTo.call(this, page, addToHistory);
    };
}


// ============================================
// BOOTSTRAP / INITIALIZATION
// ============================================
window.addEventListener('load', function() {
    // KipAuth.bootstrap() with a small delay to let DOM settle
    setTimeout(function() {
        if (typeof KipAuth !== 'undefined' && KipAuth.bootstrap) {
            KipAuth.bootstrap();
        }
    }, 100);

    // Desktop sidebar initialization
    if (typeof initDesktopSidebar === 'function') {
        initDesktopSidebar();
    }
});
