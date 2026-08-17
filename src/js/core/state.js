/**
 * @module core/state
 * @description Shared mutable state for inter-module communication.
 * Replaces scattered `window._*` globals with a centralized, typed store.
 *
 * Each property has a convenience setter that also writes to `window._*`
 * for backward compatibility with code that hasn't been migrated yet.
 *
 * Extracted from src/index.html — the window._*DetailId and
 * window._*GroupCtx globals used across devices, lockouts, valves,
 * regulators, projects, flowmeters, and exam-tickets modules.
 */

// ============================================================
// Detail IDs — which item is currently shown in the detail panel
// ============================================================

export const detailState = {
    /** @type {string|null} Device detail ID */       devDetailId: null,
    /** @type {string|null} Lockout detail ID */      lockDetailId: null,
    /** @type {string|null} Valve detail ID */        valveDetailId: null,
    /** @type {string|null} Regulator detail ID */    regulatorDetailId: null,
    /** @type {string|null} Project detail ID */      projectDetailId: null,
    /** @type {string|null} Flowmeter detail ID */    flowDetailId: null,
    /** @type {string|null} Exam ticket category ID */ ticketDetailCatId: null,
    /** @type {number|null} Exam ticket index */      ticketDetailIndex: null,
};

// ============================================================
// Group contexts — which group is currently expanded in the sidebar
// ============================================================

export const groupState = {
    /** @type {{mode:string, group:object}|null} */ devGroupCtx: null,
    /** @type {{mode:string, group:object}|null} */ lockGroupCtx: null,
    /** @type {{mode:string, group:object}|null} */ valveGroupCtx: null,
    /** @type {{mode:string, group:object}|null} */ regulatorGroupCtx: null,
    /** @type {{mode:string, group:object}|null} */ projectGroupCtx: null,
};

// ============================================================
// Convenience setters — update both the state object and
// the window._* global for backward compatibility
// ============================================================

export function setDevDetailId(id)       { detailState.devDetailId = id;       window._devDetailId = id; }
export function setLockDetailId(id)      { detailState.lockDetailId = id;     window._lockDetailId = id; }
export function setValveDetailId(id)     { detailState.valveDetailId = id;    window._valveDetailId = id; }
export function setRegulatorDetailId(id) { detailState.regulatorDetailId = id; window._regulatorDetailId = id; }
export function setProjectDetailId(id)   { detailState.projectDetailId = id;  window._projectDetailId = id; }
export function setFlowDetailId(id)      { detailState.flowDetailId = id;     window._flowDetailId = id; }
export function setTicketDetailCatId(id) { detailState.ticketDetailCatId = id; window._ticketDetailCatId = id; }
export function setTicketDetailIndex(i)  { detailState.ticketDetailIndex = i;  window._ticketDetailIndex = i; }

export function setDevGroupCtx(ctx)       { groupState.devGroupCtx = ctx;       window._devGroupCtx = ctx; }
export function setLockGroupCtx(ctx)      { groupState.lockGroupCtx = ctx;      window._lockGroupCtx = ctx; }
export function setValveGroupCtx(ctx)     { groupState.valveGroupCtx = ctx;     window._valveGroupCtx = ctx; }
export function setRegulatorGroupCtx(ctx) { groupState.regulatorGroupCtx = ctx; window._regulatorGroupCtx = ctx; }
export function setProjectGroupCtx(ctx)   { groupState.projectGroupCtx = ctx;   window._projectGroupCtx = ctx; }

// ============================================================
// Convenience getters — read from state (fallback to window._*)
// ============================================================

export function getDevDetailId()       { return detailState.devDetailId       ?? window._devDetailId; }
export function getLockDetailId()      { return detailState.lockDetailId      ?? window._lockDetailId; }
export function getValveDetailId()     { return detailState.valveDetailId     ?? window._valveDetailId; }
export function getRegulatorDetailId() { return detailState.regulatorDetailId ?? window._regulatorDetailId; }
export function getProjectDetailId()   { return detailState.projectDetailId   ?? window._projectDetailId; }
export function getFlowDetailId()      { return detailState.flowDetailId      ?? window._flowDetailId; }
export function getTicketDetailCatId() { return detailState.ticketDetailCatId ?? window._ticketDetailCatId; }
export function getTicketDetailIndex() { return detailState.ticketDetailIndex ?? window._ticketDetailIndex; }

export function getDevGroupCtx()       { return groupState.devGroupCtx       ?? window._devGroupCtx; }
export function getLockGroupCtx()      { return groupState.lockGroupCtx      ?? window._lockGroupCtx; }
export function getValveGroupCtx()     { return groupState.valveGroupCtx     ?? window._valveGroupCtx; }
export function getRegulatorGroupCtx() { return groupState.regulatorGroupCtx ?? window._regulatorGroupCtx; }
export function getProjectGroupCtx()   { return groupState.projectGroupCtx   ?? window._projectGroupCtx; }

// ============================================================
// Reset all state (useful when navigating away from a detail panel)
// ============================================================

export function resetAllDetailIds() {
    setDevDetailId(null);
    setLockDetailId(null);
    setValveDetailId(null);
    setRegulatorDetailId(null);
    setProjectDetailId(null);
    setFlowDetailId(null);
    setTicketDetailCatId(null);
    setTicketDetailIndex(null);
}

export function resetAllGroupCtxs() {
    setDevGroupCtx(null);
    setLockGroupCtx(null);
    setValveGroupCtx(null);
    setRegulatorGroupCtx(null);
    setProjectGroupCtx(null);
}
