# -*- coding: utf-8 -*-
# Task 326 — верификация после фикса: разделы не просто .active,
# но и ВИДИМЫ (offsetWidth/offsetHeight > 0) на десктопе и мобиле,
# полные карточки расходомеров видны, скриншоты-пруфы.
import json
from playwright.sync_api import sync_playwright

PORT = 8945
BASE = 'http://127.0.0.1:%d/index.html' % PORT
FALLBACK = json.load(open('/home/z/my-project/kip8test/data/flowmeters.json', encoding='utf-8'))
METERS = FALLBACK['meters']

def mock_response(action, body):
    if action == 'getCurrentUser': return {'ok': True, 'data': {'role': 'Админ', 'email': 'qa@local.test', 'userId': 1}}
    if action == 'heartbeat': return {'ok': True, 'data': {'ok': True}}
    if action == 'getMyAccess': return {'ok': True, 'data': {'found': True, 'role': 'Админ', 'permissions': {
        'calc.view': True, 'library.view': True, 'kipios.view': True, 'kipios.restricted': True,
        'secret.view': True, 'whatsnew.view': True, 'charts.view': True, 'flowmeter.view': True,
        'flowmeter.input': True, 'workschedule.view': True}}}
    if action == 'flowmeter.list': return {'ok': True, 'data': {'meters': METERS}}
    if action == 'flowmeter.archive': return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.getValidationRules': return {'ok': True, 'data': {'rules': []}}
    if action == 'cableJournal.getColumns': return {'ok': True, 'data': {'columns': [], 'canEdit': True}}
    if action == 'workSchedule.getCodes': return {'ok': True, 'data': {'codes': []}}
    if action == 'workSchedule.getEmployees': return {'ok': True, 'data': {'employees': []}}
    if action == 'workSchedule.getPatterns': return {'ok': True, 'data': {'patterns': []}}
    if action == 'workSchedule.listEntries': return {'ok': True, 'data': {'entries': []}}
    return {'ok': False, 'error': 'unknown action ' + str(action)}

SECTIONS = ['kip-ios', 'devices-prod', 'lockouts-prod', 'valves-prod', 'regulators-prod',
            'projects-prod', 'cable-journal-edit', 'calculators', 'calc-kipa', 'converter',
            'library-internal', 'exam-tickets', 'whats-new', 'phonebook', 'admin',
            'work-schedule', 'flowmeter-data', 'dashboard']

def setup_routes(ctx):
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            from urllib.parse import unquote
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

fails = []
def check(label, ok, detail=''):
    print(('  OK  ' if ok else ' FAIL ') + label + ((' — ' + detail) if detail else ''))
    if not ok: fails.append(label + ' ' + detail)

def run_ctx(browser, vw, vh, is_mob, label, shot_prefix):
    ctx = browser.new_context(viewport={'width': vw, 'height': vh}, is_mobile=is_mob, has_touch=is_mob)
    setup_routes(ctx)
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '#dashboard')
    page.evaluate("localStorage.setItem('kip8_session_token','v326')")
    page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
    page.evaluate("localStorage.setItem('kip8_cached_email','qa@local.test')")
    page.reload()
    page.wait_for_timeout(2500)
    print('== Разделы ВИДИМОСТЬ (%s) ==' % label)
    for sec in SECTIONS:
        page.evaluate("navigateTo('%s')" % sec)
        page.wait_for_timeout(420)
        st = page.evaluate('''(() => {
            const el = document.getElementById('page-%s');
            if (!el) return {exists: false};
            const r = el.getBoundingClientRect();
            return {exists: true, active: el.classList.contains('active'),
                    w: r.width, h: r.height,
                    visible: el.offsetWidth > 50 && el.offsetHeight > 50,
                    parent: el.parentElement.id};
        })()''' % sec)
        ok = st.get('exists') and st.get('active') and st.get('visible')
        check('%s: %s' % (label, sec), ok, 'active=%s visible=%s %sx%s parent=%s' % (
            st.get('active'), st.get('visible'), int(st.get('w') or 0), int(st.get('h') or 0), st.get('parent')))
    print('== Полные карточки расходомеров (%s) ==' % label)
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1100)
    for mid in (1, 2, 5, 12):
        sel = "#flowList .flow-card[data-flow-id='%d'] .flow-card-header" % mid
        page.evaluate('document.querySelector("%s").click()' % sel)
        page.wait_for_timeout(380)
        if not is_mob:
            st = page.evaluate('''(() => {
                const p = document.getElementById('detailPanel');
                const r = p.getBoundingClientRect();
                return {active: p.classList.contains('active'), w: r.width, h: r.height, visible: p.offsetWidth > 50};
            })()''')
            check('%s: полная карточка расходомера №%d (detail-панель)' % (label, mid),
                  st['active'] and st['visible'],
                  'active=%s visible=%s %dx%d' % (st['active'], st['visible'], int(st['w']), int(st['h'])))
            if mid == 1:
                page.screenshot(path='/tmp/task326-proof-%s-flow-detail.png' % shot_prefix)
            page.evaluate("closeDetailPanel()")
        else:
            st = page.evaluate('''(() => {
                const p = document.getElementById('page-flowmeter-detail');
                return {active: p.classList.contains('active'), visible: p.offsetWidth > 50 && p.offsetHeight > 50};
            })()''')
            check('%s: полная карточка расходомера №%d (страница)' % (label, mid),
                  st['active'] and st['visible'], 'active=%s visible=%s' % (st['active'], st['visible']))
            if mid == 1:
                page.screenshot(path='/tmp/task326-proof-%s-flow-detail.png' % shot_prefix)
            page.evaluate("navigateTo('flowmeter-data')")
        page.wait_for_timeout(250)
    # скрин раздела приборов (пострадавший в баге)
    page.evaluate("navigateTo('devices-prod')")
    page.wait_for_timeout(800)
    page.screenshot(path='/tmp/task326-proof-%s-devices.png' % shot_prefix)
    check('%s: 0 JS-ошибок' % label, len(errors) == 0, '; '.join(errors[:3]))
    ctx.close()

with sync_playwright() as p:
    browser = p.chromium.launch()
    run_ctx(browser, 1280, 900, False, 'desktop', 'desktop')
    run_ctx(browser, 375, 812, True, 'mobile', 'mobile')
    browser.close()

print('\nИТОГО: %d провалов' % len(fails))
for f in fails: print('  FAIL:', f)
