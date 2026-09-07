# -*- coding: utf-8 -*-
# Task 336 probe-3: десктоп карточка (реальный рендер) + пиксельный
# анализ стыка «Сотрудник +» | первый день в шапке сетки.
import json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8944
Y, M = datetime.date.today().year, datetime.date.today().month

DEVICES = [
  {'ID':'100','Наименование':'Термометр сопротивления ТСП-100П','Тип':'КИПиА','№ прибора':'ТСП-001','Место установки':'Цех №1, трубопровод пара','Раздел':'Тепло','Заводской №':'Z-100','Дата поверки':'2026-05-01','Замечания':'','Ед. изм.':'°C','Диапазон':'0…150','Класс точности':'B','Год выпуска':'2023','Изготовитель':'Элемер','Схема':'','Примечание':''},
]
CODES = [{'code':'Д','name':'День','color':'#FFE082'},{'code':'Н','name':'Ночь','color':'#B0BEC5'}]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов Иван Иванович','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
]

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','found':True,'permissions':{'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'kip.view':True,'kip.edit':True}}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'getDevices':
        return {'ok':True,'data':{'devices':DEVICES}}
    return {'ok':True,'data':{'ok':True}}

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- десктоп: реальный рендер карточки ----------
    ctx = browser.new_context(viewport={'width':1440,'height':900})
    page = ctx.new_page()
    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = unquote(url.split('action=')[1].split('&')[0])
        pd = request.post_data
        body = None
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=json.dumps(mock_response(action, body), ensure_ascii=False).encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(status=404, body='x'))
    ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(status=404, body='x'))
    page.goto('http://localhost:%d/index.html' % PORT, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('kip8_session_token','probe-t336-d3')")
    page.evaluate("localStorage.setItem('app-theme','dark')")
    page.reload(); page.wait_for_timeout(2500)

    page.evaluate("navigateTo('kip-ios')"); page.wait_for_timeout(1500)
    page.evaluate("devOpenDetail('100')"); page.wait_for_timeout(1200)
    d = page.evaluate("""(function(){
        var panel = document.getElementById('detailPanel');
        var body = document.getElementById('detailPanelBody');
        var bar = document.getElementById('detailBreadcrumbBar');
        var top = body ? body.querySelector('.dev-detail-top') : null;
        if (!body || !top) return {err:'no els'};
        var brb = bar.getBoundingClientRect(), tb = top.getBoundingClientRect();
        var bb = body.getBoundingClientRect(), pb = panel.getBoundingClientRect();
        var res = { barBottom: brb.bottom, panelTop: pb.top, bodyTop: bb.top, topTop: tb.top,
                    gapBar: tb.top - brb.bottom, gapBody: tb.top - bb.top,
                    mt: getComputedStyle(top).marginTop,
                    bodyPaddingTop: getComputedStyle(body).paddingTop };
        body.scrollTop = 500;
        res.gapScrolled = top.getBoundingClientRect().top - brb.bottom;
        body.scrollTop = 0;
        return res;
    })()""")
    print('D-CARD real render:', json.dumps(d, ensure_ascii=False))
    page.screenshot(path='scripts/task336-probe-d-card.png')
    ctx.close()
    browser.close()
print('DONE')
