# -*- coding: utf-8 -*-
# Task 336 probe-4: почему margin-top:-16 не даёт эффекта в десктоп-
# панели — структура и геометрия body/card/top + эксперимент.
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
DEVICES = [
  {'ID':'100','Наименование':'Термометр ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'kip.view':True,'kip.edit':True,'workschedule.view':True}}}
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':1440,'height':900})
    page = ctx.new_page()
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, None), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, body='x'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, body='x'))
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','probe-t336-d4')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload(); page.wait_for_timeout(2500)

    page.evaluate("navigateTo('kip-ios')"); page.wait_for_timeout(1500)
    page.evaluate("devOpenDetail('100')"); page.wait_for_timeout(1200)
    d = page.evaluate("""(function(){
        var body = document.getElementById('detailPanelBody');
        var card = body.querySelector('.dev-detail-card');
        var top = body.querySelector('.dev-detail-top');
        var fav = body.querySelector('.dev-detail-fav-btn');
        var bb = body.getBoundingClientRect(), cb = card.getBoundingClientRect(),
            tb = top.getBoundingClientRect(), fb = fav ? fav.getBoundingClientRect() : null;
        var cs = getComputedStyle(top), ccs = getComputedStyle(card);
        var out = {
            bodyTop: bb.top, cardTop: cb.top, topTop: tb.top, favTop: fb ? fb.top : null,
            topMarginTop: cs.marginTop, topPos: cs.position, topDisplay: cs.display,
            cardMarginTop: ccs.marginTop, cardPaddingTop: ccs.paddingTop,
            cardPos: ccs.position, cardOverflow: ccs.overflow,
            topFirstChildText: null,
            htmlStart: body.innerHTML.substring(0, 120)
        };
        // эксперимент: заменить margin-top на transform
        top.style.marginTop = '0px';
        top.style.transform = 'translateY(-16px)';
        out.afterTransform = top.getBoundingClientRect().top - bb.top;
        top.style.transform = '';
        top.style.marginTop = '-16px';
        // эксперимент 2: margin на CARD, не на top
        top.style.marginTop = '0px';
        card.style.marginTop = '-16px';
        out.afterCardMargin = top.getBoundingClientRect().top - bb.top;
        card.style.marginTop = '';
        // эксперимент 3: padding-top компенсация на body
        var bcs = getComputedStyle(body);
        out.bodyPaddingTop = bcs.paddingTop;
        return out;
    })()""")
    print(json.dumps(d, ensure_ascii=False, indent=1))
    ctx.close(); browser.close()
print('DONE')
