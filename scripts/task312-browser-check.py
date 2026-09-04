# -*- coding: utf-8 -*-
# Task 312: browser-check «График работы» — заявка пользователя:
#   1) убрать кнопку «+ Отпуск» из бара над шахматкой, функционал —
#      новой строкой «+ Отпуск…» в блок отпусков карточки сотрудника
#      (клик по полю ФИО) с префиллом сотрудника в шторке;
#   2) в попапе ячейки убрать коды мероприятий (И/ОБ/ПЗ/ПР/*) из
#      списка основных статусов — они добавляются «+ Мероприятие…»
#      и живут бейджами-«иконками» в ячейках;
#   3) убрать строку «— выходной —» (кода «—» нет в «Коды_статусов»);
#   4) цвет «.» — белый #FAF9F5 (мок листа имитирует замену в таблице;
#      fallback клиента синхронизирован в Task 312).
# Task 313 (актуализация регресса): секция «Мероприятия в этот день»
# переехала из окна кодов в ОТДЕЛЬНОЕ окно #wsEventsPopup над ним —
# проверки D6/E2 смотрят событие в новом окне, в окне кодов секции
# больше нет. Playwright + мок fetch (Apps Script по action; внешние
# источники производственного календаря закрыты 404 — фолбэки).
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8937

# Цвет «.» = #FAF9F5 — целевое состояние листа «Коды_статусов»
# (пользователь меняет в таблице сам; клиент и fallback синхронны)
CODES = [
  {'code':'Д','name':'День (12-час)','color':'#FFE082'},
  {'code':'Д8','name':'День 8-час','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь (12-час)','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'н','name':'Ночь в вых./праздник','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск ежегодный основной','color':'#ECEFF1'},
  {'code':'И','name':'Инструктаж','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний','color':'#FFCDD2'},
  {'code':'.','name':'Плановый выходной день','color':'#FAF9F5'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'2025-01-20','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
# 02.06 Д (смена + бейдж И), 05.06 «.» (белый плановый выходной),
# 03.06 у Петрова «И» основным (день события без смены — generateMonth)
ENTRIES = [
  {'id':1,'дата':'2026-06-02','таб_номер':'017','статус':'Д','источник':'авто'},
  {'id':2,'дата':'2026-06-05','таб_номер':'017','статус':'.','источник':'авто'},
  {'id':3,'дата':'2026-06-03','таб_номер':'023','статус':'И','источник':'авто'},
  {'id':4,'дата':'2026-06-08','таб_номер':'023','статус':'Д8','источник':'авто'}
]
TRAININGS = [
  {'id':101,'таб_номер':'017','тип':'инструктаж','тема':'ОТ и ПБ','дата_начала':'2026-06-02','дата_окончания':'2026-06-02'},
  {'id':102,'таб_номер':'023','тип':'инструктаж','тема':'ОТ и ПБ','дата_начала':'2026-06-03','дата_окончания':'2026-06-03'},
  {'id':103,'таб_номер':'023','тип':'обучение','тема':'КИПиА','дата_начала':'2026-06-10','дата_окончания':'2026-06-10'}
]
# Иванов: май, часть 1 — «+ Отпуск…» префилл предложит часть 2
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':1,'дата_начала':'2026-05-01','дата_окончания':'2026-05-14','комментарий':'май'}
]

STATE = {'role': 'Админ'}

def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'user@test.local','role':STATE['role']}}
    if action == 'getMyAccess':
        admin = STATE['role'] == 'Админ'
        perms = {'workschedule.view':True, 'workschedule.edit':admin,
                 'flowmeter.view':True, 'flowmeter.input':admin}
        if admin: perms['admin.panel'] = True
        return {'ok':True,'data':{'role':STATE['role'],'found':True,'permissions':perms}}
    if action == 'heartbeat':
        return {'ok':True,'data':{'ok':True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok':True,'data':{'codes':CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok':True,'data':{'employees':EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok':True,'data':{'patterns':PATTERNS}}
    if action == 'workSchedule.listEntries':
        return {'ok':True,'data':{'entries':ENTRIES}}
    if action == 'workSchedule.listTrainings':
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def goto_june(page):
    page.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '6';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page.wait_for_timeout(2500)

# клик по ячейке (дата+таб) — через координаты центра ячейки
def click_cell(page, iso, tab):
    page.evaluate("""(function(a){
        var iso = a[0], tab = a[1];
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'"+iso+"'") !== -1 && oc.indexOf("'"+tab+"'") !== -1) {
                var r = tds[i].getBoundingClientRect();
                window.__cellXY = [r.left + r.width/2, r.top + r.height/2];
                window.__cellEl = tds[i];
                return;
            }
        }
    })""", [iso, tab])
    xy = page.evaluate("window.__cellXY || [600, 300]")
    page.mouse.click(xy[0], xy[1])
    page.wait_for_timeout(500)

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- Контекст 1: десктоп 1280px, Админ ----------
    ctx = browser.new_context(viewport={'width':1280,'height':800})
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
            action = unquote(action)
        body = None
        pd = request.post_data
        if pd:
            try: body = json.loads(pd)
            except Exception: body = None
        resp = mock_response(action, body)
        s = json.dumps(resp, ensure_ascii=False)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=s.encode('utf-8'))
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)
    def block_external(route):
        route.fulfill(status=404, content_type='text/plain', body='not found (browser-check t312)')
    ctx.route('**raw.githubusercontent.com/**', block_external)
    ctx.route('**calendar.legalic.ru/**', block_external)

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t312')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    goto_june(page)
    check('B: шахматка июнь 2026 отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. Тулбар: «+ Отпуск» УДАЛЕНА, «Сформировать»/«Сохранить» живы
    tb = page.evaluate("""(function(){
        return { vacBtn: !!document.getElementById('wsVacBtn'),
                 genBtn: !!document.getElementById('wsGenerateBtn'),
                 saveBtn: !!document.getElementById('wsSaveBtn'),
                 calPanel: !!document.getElementById('wsCalPanel') };
    })()""")
    check('C: кнопка «+ Отпуск» (#wsVacBtn) УДАЛЕНА из бара; «Сформировать»/«Сохранить»/календарь живы',
          (not tb['vacBtn']) and tb['genBtn'] and tb['saveBtn'] and tb['calPanel'], tb)
    page.screenshot(path='scripts/task312-proof-toolbar.png', full_page=False)

    # D. Попап ячейки 02.06 Иванов (Д + бейдж И): без «выходного» и мероприятий
    click_cell(page, '2026-06-02', '017')
    pop = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        var txt = cp ? cp.textContent : '';
        var evTxt = evp ? evp.textContent : '';
        var rows = cp ? cp.querySelectorAll('.ws-popup-row') : [];
        var mainCodes = [];
        for (var i=0;i<rows.length;i++) {
            if (rows[i].className.indexOf('ws-popup-event') !== -1) continue;
            if (rows[i].className.indexOf('ws-popup-more') !== -1) continue;
            var code = rows[i].querySelector('.ws-popup-code');
            if (code) mainCodes.push(code.textContent);
        }
        var rowNames = [];
        for (var j=0;j<rows.length;j++) {
            if (rows[j].className.indexOf('ws-popup-event') !== -1) continue;
            if (rows[j].className.indexOf('ws-popup-more') !== -1) continue;
            var nm = rows[j].querySelector('.ws-popup-name');
            if (nm) rowNames.push(nm.textContent);
        }
        var active = cp ? cp.querySelector('.ws-popup-row.ws-popup-active') : null;
        return { open: cp ? cp.classList.contains('active') : false,
                 txt: txt,
                 mainCodes: mainCodes,
                 rowNames: rowNames,
                 activeCode: active ? (active.querySelector('.ws-popup-code')||{}).textContent : null,
                 hasWeekendRow: txt.indexOf('выходной') !== -1,
                 hasEventsSecInCodes: txt.indexOf('Мероприятия в этот день') !== -1,
                 evOpen: evp ? evp.classList.contains('active') : false,
                 evTitle: evTxt.indexOf('Мероприятия в этот день') !== -1,
                 evHasTr: evTxt.indexOf('ОТ и ПБ') !== -1,
                 hasAddEvent: txt.indexOf('+ Мероприятие…') !== -1,
                 hasMore: txt.indexOf('Дополнительно…') !== -1 };
    })()""")
    check('D: попап ячейки открылся', pop['open'])
    check('D2: строки «— выходной —» НЕТ (кода «—» нет в таблице кодов)',
          '—' not in pop['mainCodes'] and 'выходной' not in pop['rowNames'], pop['mainCodes'])
    check('D3: коды мероприятий (И/ОБ/ПЗ) НЕ в списке основных статусов',
          all(c not in pop['mainCodes'] for c in ['И','ОБ','ПЗ','ПР','*']), pop['mainCodes'])
    check('D4: основные коды — только статусы из листа (Д/Д8/Н/д/н/ОТ/·)',
          pop['mainCodes'] and pop['mainCodes'][0] == 'Д' and '.' in pop['mainCodes'], pop['mainCodes'])
    check('D5: текущий статус «Д» подсвечен', pop['activeCode'] == 'Д', pop['activeCode'])
    check('D6: Task 313 — окно «Мероприятия в этот день» НАД окном кодов (Иванов, 02.06)',
          pop['evOpen'] and pop['evTitle'] and pop['evHasTr'] and
          (not pop['hasEventsSecInCodes']),
          {'evOpen': pop['evOpen'], 'evTitle': pop['evTitle'], 'evHasTr': pop['evHasTr'],
           'secInCodes': pop['hasEventsSecInCodes']})
    check('D7: «+ Мероприятие…» и «Дополнительно…» живы',
          pop['hasAddEvent'] and pop['hasMore'])
    page.screenshot(path='scripts/task312-proof-cell-popup.png', full_page=False)

    # D8. «Дополнительно…» — select без кодов мероприятий, «— выходной —» жив
    page.evaluate("WorkSchedule.onPopupMore()")
    page.wait_for_timeout(500)
    sheet = page.evaluate("""(function(){
        var sel = document.getElementById('wsCellStatus');
        var opts = [];
        if (sel) for (var i=0;i<sel.options.length;i++) opts.push(sel.options[i].value);
        return { open: document.getElementById('wsCellSheet').classList.contains('active'),
                 opts: opts };
    })()""")
    check('D8: шит «Дополнительно…»: select жив, «— выходной —» есть, мероприятий НЕТ',
          sheet['open'] and '' in sheet['opts'] and
          all(o not in ['И','ОБ','ПЗ','*'] for o in sheet['opts']) and 'ПР' not in sheet['opts'], sheet)
    page.evaluate("WorkSchedule.closeCellForm()")
    page.wait_for_timeout(300)

    # E. Попап ячейки 03.06 Петров (основной статус «И» — день события)
    click_cell(page, '2026-06-03', '023')
    popE = page.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        var txt = cp ? cp.textContent : '';
        var evTxt = evp ? evp.textContent : '';
        var active = cp ? cp.querySelector('.ws-popup-row.ws-popup-active') : null;
        var rows = cp ? cp.querySelectorAll('.ws-popup-row:not(.ws-popup-event):not(.ws-popup-more)') : [];
        var codes = [];
        for (var i=0;i<rows.length;i++) {
            var c = rows[i].querySelector('.ws-popup-code');
            if (c) codes.push(c.textContent);
        }
        return { open: cp ? cp.classList.contains('active') : false,
                 active: !!active,
                 codes: codes,
                 evOpen: evp ? evp.classList.contains('active') : false,
                 evTitle: evTxt.indexOf('Мероприятия в этот день') !== -1,
                 hasTr: evTxt.indexOf('ОТ и ПБ') !== -1 };
    })()""")
    check('E: ячейка «И» (день события): попап открыт, И НЕ в списке основных',
          popE['open'] and 'И' not in popE['codes'], popE['codes'])
    check('E2: активной строки нет (код-мероприятие отфильтрован), событие — в окне мероприятий (Task 313)',
          (not popE['active']) and popE['evOpen'] and popE['evTitle'] and popE['hasTr'], popE)
    page.screenshot(path='scripts/task312-proof-event-day.png', full_page=False)

    # E3. «Дополнительно…» на ячейке «И»: текущее значение-мероприятие живо
    page.evaluate("WorkSchedule.onPopupMore()")
    page.wait_for_timeout(500)
    selE = page.evaluate("""(function(){
        var sel = document.getElementById('wsCellStatus');
        return { value: sel ? sel.value : null,
                 hasEvOpt: sel ? Array.prototype.some.call(sel.options, function(o){return o.value==='И';}) : false };
    })()""")
    check('E3: шит на ячейке «И»: текущее значение остаётся опцией (не теряется)',
          selE['value'] == 'И' and selE['hasEvOpt'], selE)
    page.evaluate("WorkSchedule.closeCellForm()")
    page.wait_for_timeout(300)
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)

    # F. Ячейка «.» (05.06) — белый фон как у пустых ячеек
    dotCell = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-06-05'") !== -1 && oc.indexOf("'017'") !== -1) {
                var cs = getComputedStyle(tds[i]);
                return { text: tds[i].textContent.trim().replace(/[\\u200b]/g,''),
                         bg: cs.backgroundColor };
            }
        }
        return null;
    })()""")
    # rgb(250, 249, 245) = #FAF9F5
    check('F: ячейка «.» — белый фон #FAF9F5 (rgb(250,249,245)), код в ячейке',
          dotCell is not None and dotCell['bg'] == 'rgb(250, 249, 245)' and dotCell['text'].find('.') != -1, dotCell)

    # G. Карточка Иванов: строка «+ Отпуск…» в блоке отпусков
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(600)
    card = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var txt = pp ? pp.textContent : '';
        var addVac = pp ? pp.querySelector('.ws-emp-addvac') : null;
        var iVacSec = txt.indexOf('Отпуска · 2026');
        var iAdd = txt.indexOf('+ Отпуск…');
        var iTrSec = txt.indexOf('Мероприятия · ');
        return { open: pp ? pp.classList.contains('active') : false,
                 addVac: !!addVac,
                 cls: addVac ? addVac.className : '',
                 txt: txt,
                 iVacSec: iVacSec, iAdd: iAdd, iTrSec: iTrSec,
                 hasVac: txt.indexOf('01.05.2026 — 14.05.2026') !== -1 };
    })()""")
    check('G: карточка открылась; «+ Отпуск…» в блоке отпусков (между «Отпуска» и «Мероприятия»)',
          card['open'] and card['addVac'] and card['iVacSec'] != -1 and
          card['iAdd'] != -1 and card['iTrSec'] != -1 and
          card['iVacSec'] < card['iAdd'] and card['iAdd'] < card['iTrSec'], card['txt'][:200])
    check('G2: строка — стиль действия (ws-popup-row ws-popup-more ws-emp-addvac)',
          'ws-popup-row' in card['cls'] and 'ws-popup-more' in card['cls'] and 'ws-emp-addvac' in card['cls'], card['cls'])
    check('G3: период отпуска в карточке жив (май, 14 дней)',
          card['hasVac'], card['txt'][:300])
    page.screenshot(path='scripts/task312-proof-emp-card.png', full_page=False)

    # H. Клик «+ Отпуск…» → карточка закрыта, шторка с ПРЕФИЛЛОМ Иванова
    page.click('#wsEmpPopup .ws-emp-addvac')
    page.wait_for_timeout(700)
    vac = page.evaluate("""(function(){
        var sh = document.getElementById('wsVacSheet');
        var pp = document.getElementById('wsEmpPopup');
        var emp = document.getElementById('wsVacTabNo');
        var part = document.getElementById('wsVacPart');
        var year = document.getElementById('wsVacYearInfo');
        return { sheetOpen: sh ? sh.classList.contains('active') : false,
                 cardClosed: pp ? !pp.classList.contains('active') : true,
                 emp: emp ? emp.value : null,
                 part: part ? part.value : null,
                 yearInfo: year ? year.textContent : '' };
    })()""")
    check('H: «+ Отпуск…»: карточка закрылась, шторка «Новый отпуск» открылась',
          vac['sheetOpen'] and vac['cardClosed'])
    check('H2: ПРЕФИЛЛ — выбран Иванов (таб. 017), часть 2 (май = часть 1)',
          vac['emp'] == '017' and vac['part'] == '2', vac)
    # май 1–14: 14 кал. − праздники 01.05/09.05 (ст. 112) = 12 чистых;
    # дефолтный период формы (сегодня+13) добавляется к счётчику
    check('H3: строка лимита года посчитана для Иванова (12 дн. чистых + период)',
          vac['yearInfo'].find('12 из 42') != -1, vac['yearInfo'])
    page.screenshot(path='scripts/task312-proof-vac-sheet.png', full_page=False)

    # H4. Отмена шторки
    page.evaluate("WorkSchedule.closeVacationForm()")
    page.wait_for_timeout(300)
    check('H4: шторка закрылась (отмена)',
          page.evaluate("!document.getElementById('wsVacSheet').classList.contains('active')"))

    # I. JS-ошибок нет
    check('I: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ---------- Контекст 2: мобильный 375px, Админ ----------
    ctxm = browser.new_context(viewport={'width':375,'height':720}, has_touch=True)
    pagem = ctxm.new_page()
    js_errors_m = []
    pagem.on('pageerror', lambda e: js_errors_m.append(str(e)))
    ctxm.route('**/exec?**', handle)
    ctxm.route('**script.google.com/**', handle)
    ctxm.route('**raw.githubusercontent.com/**', block_external)
    ctxm.route('**calendar.legalic.ru/**', block_external)

    pagem.goto('http://localhost:%d/index.html' % PORT)
    pagem.evaluate("localStorage.setItem('kip8_session_token','browser-check-t312-m')")
    pagem.reload()
    pagem.wait_for_timeout(2500)
    pagem.evaluate("navigateTo('work-schedule')")
    pagem.wait_for_timeout(1500)
    goto_june(pagem)

    # тулбар без «+ Отпуск»
    mobTb = pagem.evaluate("!document.getElementById('wsVacBtn')")
    check('K: 375px — кнопки «+ Отпуск» в тулбаре нет', mobTb)

    # тап по ячейке ФИО — карточка со строкой «+ Отпуск…»
    pagem.tap('td.ws-emp-col[data-tab="017"]')
    pagem.wait_for_timeout(600)
    mob = pagem.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        return { open: pp ? pp.classList.contains('active') : false,
                 addVac: !!pp.querySelector('.ws-emp-addvac') };
    })()""")
    check('K2: 375px — карточка по тапу, строка «+ Отпуск…» есть',
          mob['open'] and mob['addVac'], mob)
    pagem.tap('#wsEmpPopup .ws-emp-addvac')
    pagem.wait_for_timeout(700)
    mob2 = pagem.evaluate("""(function(){
        var sh = document.getElementById('wsVacSheet');
        var emp = document.getElementById('wsVacTabNo');
        return { open: sh ? sh.classList.contains('active') : false,
                 emp: emp ? emp.value : null };
    })()""")
    check('K3: 375px — тап «+ Отпуск…» открывает шторку с префиллом (017)',
          mob2['open'] and mob2['emp'] == '017', mob2)
    check('L: 375px — JS-ошибок нет', len(js_errors_m) == 0, js_errors_m[:3])
    ctxm.close()

    # ---------- Контекст 3: десктоп, «ИТР8 pro» (просмотр) ----------
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)
    ctx2.route('**raw.githubusercontent.com/**', block_external)
    ctx2.route('**calendar.legalic.ru/**', block_external)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t312-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1500)
    goto_june(page2)

    # карточка зрителю — БЕЗ строки «+ Отпуск…» (и без кнопки в тулбаре)
    page2.click('td.ws-emp-col[data-tab="017"]')
    page2.wait_for_timeout(600)
    ro = page2.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        return { open: pp ? pp.classList.contains('active') : false,
                 addVac: pp ? !!pp.querySelector('.ws-emp-addvac') : false,
                 txt: pp ? pp.textContent : '' };
    })()""")
    check('M: «ИТР8 pro» — карточка открыта, строки «+ Отпуск…» НЕТ (просмотр)',
          ro['open'] and (not ro['addVac']), ro['txt'][:200])
    check('M2: «ИТР8 pro» — периоды отпусков в карточке видны',
          ro['txt'].find('01.05.2026 — 14.05.2026') != -1, ro['txt'][:200])
    # зритель кликает ячейку — тост «нет прав», попап не открывается
    click_cell(page2, '2026-06-02', '017')
    ro2 = page2.evaluate("""(function(){
        var cp = document.getElementById('wsCellPopup');
        var evp = document.getElementById('wsEventsPopup');
        return { open: cp ? cp.classList.contains('active') : false,
                 evOpen: evp ? evp.classList.contains('active') : false };
    })()""")
    check('M3: «ИТР8 pro» — клик по ячейке попап НЕ открывает (нет прав; оба окна)',
          ro2['open'] is False and ro2['evOpen'] is False, ro2)
    check('N: JS-ошибок нет (просмотр)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task312-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
