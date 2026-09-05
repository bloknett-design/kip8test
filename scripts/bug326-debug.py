# -*- coding: utf-8 -*-
# Debug: почему #detailPanel не видим на десктопе при клике на карточку
# расходомера (active + контент есть, но offsetWidth=0).
import json
from playwright.sync_api import sync_playwright

PORT = 8945
BASE = 'http://127.0.0.1:%d/index.html' % PORT
FALLBACK = json.load(open('/home/z/my-project/kip8test/data/flowmeters.json', encoding='utf-8'))
METERS = FALLBACK['meters']

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'role': 'Админ', 'email': 'qa@local.test', 'userId': 1}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'found': True, 'role': 'Админ', 'permissions': {
            'calc.view': True, 'library.view': True, 'kipios.view': True,
            'kipios.restricted': True, 'secret.view': True, 'whatsnew.view': True,
            'charts.view': True, 'flowmeter.view': True, 'flowmeter.input': True,
            'workschedule.view': True}}}
    if action == 'flowmeter.list':
        return {'ok': True, 'data': {'meters': METERS}}
    if action == 'flowmeter.archive':
        return {'ok': True, 'data': {'records': []}}
    if action == 'flowmeter.getValidationRules':
        return {'ok': True, 'data': {'rules': []}}
    return {'ok': False, 'error': 'unknown action ' + str(action)}

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            from urllib.parse import unquote
            action = unquote(url.split('action=')[1].split('&')[0])
        resp = mock_response(action, None)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(resp, ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    page = ctx.new_page()
    page.on('pageerror', lambda e: print('PAGEERROR:', e))
    page.on('console', lambda m: print('CONSOLE[%s]:' % m.type, m.text[:200]) if m.type in ('error', 'warning') else None)
    page.goto(BASE)
    page.evaluate("localStorage.setItem('kip8_session_token','dbg326')")
    page.evaluate("localStorage.setItem('kip8_cached_role','Админ')")
    page.evaluate("localStorage.setItem('kip8_cached_email','qa@local.test')")
    page.reload()
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('flowmeter-data')")
    page.wait_for_timeout(1500)
    page.evaluate("document.querySelector('#flowList .flow-card .flow-card-header').click()")
    page.wait_for_timeout(600)

    info = page.evaluate('''(() => {
        const p = document.getElementById('detailPanel');
        const cs = getComputedStyle(p);
        const chain = [];
        let el = p;
        while (el && el !== document.documentElement) {
            const s = getComputedStyle(el);
            chain.push(el.tagName + '#' + (el.id || '') + '.' + (el.className || '') +
                       ' | display=' + s.display + ' vis=' + s.visibility +
                       ' opacity=' + s.opacity + ' | w=' + el.offsetWidth + ' h=' + el.offsetHeight +
                       ' | rect=' + JSON.stringify(el.getBoundingClientRect()));
            el = el.parentElement;
        }
        const bodyHas = {
            contentArea: document.getElementById('contentArea') ? document.getElementById('contentArea').className : 'none',
            mainApp: document.getElementById('mainApp') ? document.getElementById('mainApp').className : 'none',
            bodyClass: document.body.className,
            desktopClass: document.documentElement.className,
            isDesktop: (typeof isDesktop === 'function') ? isDesktop() : 'n/a',
        };
        return {panelClass: p.className, display: cs.display, position: cs.position,
                width: cs.width, height: cs.height, visibility: cs.visibility,
                rect: JSON.stringify(p.getBoundingClientRect()), chain, bodyHas};
    })()''')
    print('PANEL class:', info['panelClass'])
    print('PANEL computed: display=%s position=%s width=%s height=%s vis=%s' % (
        info['display'], info['position'], info['width'], info['height'], info['visibility']))
    print('PANEL rect:', info['rect'])
    print('BODY/HAS:', json.dumps(info['bodyHas'], ensure_ascii=False))
    print('--- ANCESTOR CHAIN ---')
    for c in info['chain']:
        print(' ', c)
    page.screenshot(path='/tmp/bug326-desktop-panel.png')
    browser.close()
