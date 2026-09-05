# -*- coding: utf-8 -*-
# Task 309: browser-check «График работы» — заявка пользователя:
#   1) НАВЕДЕНИЕ курсора или КЛИК на поле сотрудника (слева от
#      шахматки) открывают окно с данными из убранных вкладок
#      (Task 307/308): профиль «Сотрудники», отпуска «Отпуска»,
#      мероприятия «Инструктажи»;
#   2) правка/удаление мероприятий, добавляемых в ячейки: кнопки ✎/✕
#      в попапе ячейки («Мероприятия в этот день») и в карточке
#      сотрудника; правка = шторка «Правка мероприятия» с префиллом,
#      сохранение = addTraining(новые значения) + deleteTraining(старый
#      id) — сервер не менялся;
#   3) ручные коды «д»/«н» — рамка по краям ячейки (ws-manual-dn,
#      inset 2px, как у миниатюры-свотча попапа).
# Playwright + мок fetch (перехват POST к Apps Script по action).
import json, sys
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8930

CODES = [
  {'code':'Д','name':'День','color':'#FFE082'},
  {'code':'Д8','name':'День 8ч','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь','color':'#B0BEC5'},
  {'code':'д','name':'День в вых./праздник','color':'#FFD54F'},
  {'code':'н','name':'Ночь в вых./праздник','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск','color':'#ECEFF1'},
  {'code':'.','name':'Плановый выходной','color':'#CFD8DC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'2024-03-15','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':'ответственный за КИПиА цеха №2'},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный сутки/двое','cycle':4,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  {'дата':'2026-09-01','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-14','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
TRAININGS = [
  {'id':1,'таб_номер':'017','тип':'инструктаж','тема':'Повторный по охране труда','дата_начала':'2026-09-10','дата_окончания':'2026-09-10','длительность_дней':1,'комментарий':''}
]
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':2,'дата_начала':'2026-09-05','дата_окончания':'2026-09-16','комментарий':'по графику'}
]

STATE = {'role': 'Админ', 'add_calls': [], 'del_calls': [], 'list_tr_calls': 0}

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
        STATE['list_tr_calls'] += 1
        return {'ok':True,'data':{'trainings':TRAININGS}}
    if action == 'workSchedule.listVacations':
        return {'ok':True,'data':{'vacations':VACATIONS}}
    if action == 'workSchedule.addTraining':
        STATE['add_calls'].append(body or {})
        new_id = max([t['id'] for t in TRAININGS]) + 1 if TRAININGS else 1
        b = body or {}
        TRAININGS.append({'id':new_id,
                          'таб_номер':b.get('таб_номер',''),
                          'тип':b.get('тип',''),
                          'тема':b.get('тема',''),
                          'дата_начала':b.get('дата_начала',''),
                          'дата_окончания':b.get('дата_окончания','') or b.get('дата_начала',''),
                          'длительность_дней':b.get('длительность_дней',1),
                          'комментарий':b.get('комментарий','')})
        return {'ok':True,'data':{'id':new_id}}
    if action == 'workSchedule.deleteTraining':
        STATE['del_calls'].append(body or {})
        tid = (body or {}).get('id')
        for i, t in enumerate(TRAININGS):
            if t['id'] == tid:
                del TRAININGS[i]
                return {'ok':True,'data':{'id':tid}}
        return {'ok':False,'error':'not_found'}
    if action == 'workSchedule.addVacation':
        return {'ok':True,'data':{'added':True}}
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def toast_text(page):
    return page.evaluate("(function(){var t=document.querySelector('#toast');return t? (t.textContent||'') : '';})()")

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- Контекст 1: десктоп 1280px, Админ (hover-устройство) ----------
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

    page.goto('http://localhost:%d/index.html' % PORT)
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t309')")
    page.reload()
    page.wait_for_timeout(2500)
    check('A: страница загрузилась', page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # B. График работы + сентябрь 2026
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1500)
    page.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '9';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page.wait_for_timeout(2500)
    check('B: шахматка отрисована', page.evaluate("document.querySelector('#wsGridWrap table')") is not None)

    # C. (Task 311) HOVER на поле сотрудника — карточка НЕ открывается;
    #     данные убранных вкладок проверяются КЛИКОМ (единственный триггер)
    page.hover('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(900)   # больше таймера hover 350 мс + запас
    nohover = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        return { active: pp ? pp.classList.contains('active') : false,
                 empty: pp ? !pp.textContent : true };
    })()""")
    check('C: Task 311 — наведение НЕ открывает карточку (hover-режим удалён)',
          (not nohover['active']) and nohover['empty'], nohover)
    page.mouse.move(640, 400)
    page.wait_for_timeout(300)

    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(500)
    card = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var h = pp ? pp.innerHTML : '';
        var closer = document.getElementById('wsEmpPopupCloser');
        return { active: pp ? pp.classList.contains('active') : false,
                 closerActive: closer ? closer.classList.contains('active') : false,
                 title: (pp ? (pp.querySelector('.ws-popup-title')||{}).textContent : ''),
                 hasProf: h.indexOf('>Сотрудник<') === -1,
                 hasType: h.indexOf('сменный, смена №1') !== -1,
                 hasPos: h.indexOf('Слесарь КИПиА') !== -1,
                 hasPat: h.indexOf('Сменный сутки/двое') === -1,
                 hasHire: h.indexOf('15.03.2024') !== -1,
                 hasComment: h.indexOf('ответственный за КИПиА') !== -1,
                 hasVacSec: h.indexOf('Отпуска · 2026') !== -1,
                 hasVacPart: h.indexOf('Часть 2') !== -1 && h.indexOf('05.09.2026 — 16.09.2026') !== -1,
                 hasVacTotal: h.indexOf('Итого в году: 12') === -1,
                 hasTrSec: h.indexOf('Мероприятия · Сентябрь 2026') !== -1,
                 hasTrTheme: h.indexOf('Повторный по охране труда') !== -1,
                 hasEdit: h.indexOf('editTraining(') !== -1,
                 hasDel: h.indexOf('deleteTraining(') !== -1 };
    })()""")
    check('C0: клик открыл карточку (прикреплённый режим: кловер активен)',
          card['active'] and card['closerActive'], card)
    check('C2: шапка «Иванов И. И. · таб. №017» + профиль (тип, должность, приём, комментарий; Task 311: без строки «Сотрудник» и «Шаблон ротации»)',
          card['title'] == 'Иванов И. И. · таб. №017' and card['hasProf'] and card['hasType'] and
          card['hasPos'] and card['hasPat'] and card['hasHire'] and card['hasComment'], card)
    check('C3: секция «Отпуска · 2026»: часть 2, 05.09–16.09 (Task 311: итога года НЕТ)',
          card['hasVacSec'] and card['hasVacPart'] and card['hasVacTotal'], card)
    check('C4: секция «Мероприятия · Сентябрь 2026»: тема + кнопки ✎/✕ (Админ)',
          card['hasTrSec'] and card['hasTrTheme'] and card['hasEdit'] and card['hasDel'], card)
    page.screenshot(path='scripts/task309-proof-click-card.png', full_page=False)
    page.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    page.wait_for_timeout(300)

    # D. КЛИК по полю сотрудника → прикреплённый режим (кловер active)
    page.click('td.ws-emp-col[data-tab="023"]')
    page.wait_for_timeout(400)
    pinned = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var closer = document.getElementById('wsEmpPopupCloser');
        return { active: pp.classList.contains('active'),
                 pinned: WorkSchedule._empPinned,
                 closerActive: closer.classList.contains('active'),
                 title: (pp.querySelector('.ws-popup-title')||{}).textContent,
                 emptyTr: pp.textContent.indexOf('нет мероприятий в месяце') !== -1 };
    })()""")
    check('D: клик — прикреплённый режим (кловер active, _empPinned), карточка Петрова',
          pinned['active'] and pinned['pinned'] and pinned['closerActive'] and
          pinned['title'] == 'Петров П. П. · таб. №023', pinned)
    # D2: клик по кловеру закрывает (клик в угол — центр кловера
    # перекрыт самой карточкой, так и задумано: клик внутри попапа
    # не закрывает его)
    page.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    page.wait_for_timeout(300)
    closed2 = page.evaluate("!document.getElementById('wsEmpPopup').classList.contains('active')")
    check('D2: клик по фону-кловеру закрыл карточку', closed2)

    # E. Попап ячейки с мероприятием: кнопки ✎/✕ в окне «Мероприятия в
    #    этот день» (Task 313: окно НАД окном кодов, секция переехала)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-10'") !== -1 && oc.indexOf("'017'") !== -1) { tds[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(700)
    pop = page.evaluate("""(function(){
        var popup = document.getElementById('wsCellPopup');
        var ev = document.getElementById('wsEventsPopup');
        var h = ev ? ev.innerHTML : '';
        return { active: popup ? popup.classList.contains('active') : false,
                 evOpen: ev ? ev.classList.contains('active') : false,
                 hasSec: h.indexOf('Мероприятия в этот день') !== -1,
                 hasTheme: h.indexOf('Повторный по охране труда') !== -1,
                 hasEdit: h.indexOf('editTraining(1)') !== -1,
                 hasDel: h.indexOf('deleteTraining(1)') !== -1 };
    })()""")
    check('E: окно «Мероприятия в этот день»: секция с темой и кнопками ✎/✕ (id=1)',
          pop['active'] and pop['evOpen'] and pop['hasSec'] and pop['hasTheme'] and pop['hasEdit'] and pop['hasDel'], pop)

    # F. ✎ в окне мероприятий → шторка «Правка мероприятия» с префиллом
    page.click('#wsEventsPopup .ws-popup-act:not(.ws-popup-act-del)')
    page.wait_for_timeout(700)
    trs = page.evaluate("""(function(){
        var sh = document.getElementById('wsTrSheet');
        return { active: sh ? sh.classList.contains('active') : false,
                 title: (document.getElementById('wsTrSheetTitle')||{}).textContent,
                 btn: (document.getElementById('wsTrSubmitBtn')||{}).textContent,
                 tab: (document.getElementById('wsTrTabNo')||{}).value,
                 type: (document.getElementById('wsTrType')||{}).value,
                 tema: (document.getElementById('wsTrTitle')||{}).value,
                 start: (document.getElementById('wsTrStart')||{}).value,
                 end: (document.getElementById('wsTrEnd')||{}).value,
                 cellPopupClosed: !document.getElementById('wsCellPopup').classList.contains('active'),
                 evPopupClosed: !document.getElementById('wsEventsPopup').classList.contains('active') };
    })()""")
    check('F: шторка «Правка мероприятия», кнопка «Сохранить», префилл записи',
          trs['active'] and trs['title'] == 'Правка мероприятия' and trs['btn'] == 'Сохранить' and
          trs['tab'] == '017' and trs['type'] == 'инструктаж' and
          trs['tema'] == 'Повторный по охране труда' and
          trs['start'] == '2026-09-10' and trs['end'] == '2026-09-10' and
          trs['cellPopupClosed'] and trs['evPopupClosed'], trs)
    page.screenshot(path='scripts/task309-proof-edit-sheet.png', full_page=False)

    # G. Сохранение правки (новая тема) → add + delete на сервере, тост, перезагрузка
    page.fill('#wsTrTitle', 'Повторный инструктаж по ОТ (обновлён)')
    tr_before = STATE['list_tr_calls']
    page.click('#wsTrSubmitBtn')
    page.wait_for_timeout(2500)
    add = STATE['add_calls'][0] if STATE['add_calls'] else {}
    delc = STATE['del_calls'][0] if STATE['del_calls'] else {}
    t = toast_text(page)
    sheet_closed = page.evaluate("!document.getElementById('wsTrSheet').classList.contains('active')")
    check('G: сервер получил addTraining (новые значения) и deleteTraining (старый id=1)',
          len(STATE['add_calls']) == 1 and len(STATE['del_calls']) == 1 and
          add.get('тема') == 'Повторный инструктаж по ОТ (обновлён)' and
          add.get('таб_номер') == '017' and add.get('тип') == 'инструктаж' and
          delc.get('id') == 1, (add, delc))
    check('G2: шторка закрыта, тост «Мероприятие обновлено», сетка перезагружена (listTrainings)',
          sheet_closed and 'Мероприятие обновлено' in t and
          STATE['list_tr_calls'] > tr_before, (t[:120], tr_before, STATE['list_tr_calls']))

    # G3. Карточка показывает обновлённое мероприятие (id=2, новая тема)
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(500)
    upd = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        return { active: pp.classList.contains('active'),
                 newTheme: pp.textContent.indexOf('Повторный инструктаж по ОТ (обновлён)') !== -1,
                 oldGone: pp.textContent.indexOf('Повторный по охране труда') === -1 };
    })()""")
    check('G3: карточка показывает обновлённую тему (старой нет)', upd['active'] and upd['newTheme'] and upd['oldGone'], upd)

    # H. Удаление: ✕ в карточке → kipConfirm → deleteTraining
    page.click('#wsEmpPopup .ws-popup-act-del')
    page.wait_for_timeout(500)
    dlg = page.evaluate("""(function(){
        var ov = document.getElementById('kipDialogOverlay');
        return { active: ov ? ov.classList.contains('active') : false,
                 text: ov ? ov.textContent : '',
                 cardClosed: !document.getElementById('wsEmpPopup').classList.contains('active') };
    })()""")
    check('H: диалог подтверждения открыт («Удалить мероприятие»), карточка закрыта',
          dlg['active'] and 'Удалить мероприятие' in dlg['text'] and dlg['cardClosed'], dlg)
    page.click('.kip-dialog-ok')
    page.wait_for_timeout(2000)
    t2 = toast_text(page)
    # карточка была закрыта deleteTraining до диалога — открываем заново
    # (клик по полю сотрудника) и проверяем пустое состояние секции
    page.click('td.ws-emp-col[data-tab="017"]')
    page.wait_for_timeout(700)
    gone = page.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        return { active: pp.classList.contains('active'),
                 empty: pp.textContent.indexOf('нет мероприятий в месяце') !== -1 };
    })()""")
    check('H2: подтверждено — deleteTraining(id=2), тост «Мероприятие удалено», секция пуста',
          len(STATE['del_calls']) == 2 and STATE['del_calls'][1].get('id') == 2 and
          'Мероприятие удалено' in t2 and gone['active'] and gone['empty'],
          (STATE['del_calls'], t2[:120]))
    page.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    page.wait_for_timeout(300)

    # I. Ручной код «д»: попап статуса → выбор «д» → рамка ws-manual-dn
    # (суббота 12.09.2026, Петров — пустая ячейка выходного дня)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-12'") !== -1 && oc.indexOf("'023'") !== -1) { tds[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(700)
    has_d = page.evaluate("""(function(){
        return document.getElementById('wsCellPopup').innerHTML.indexOf('onPopupStatus(\\'д\\')') !== -1;
    })()""")
    check('I: попап статуса ячейки 12.09 (Петров) содержит код «д»', has_d)
    page.evaluate("WorkSchedule.onPopupStatus('д')")
    page.wait_for_timeout(400)
    # Task 322: дневной персонал — сначала МАЛАЯ ФОРМА ЧАСОВ
    # (переработка по указанным часам); применяем 8 ч
    page.evaluate("(function(){ var i = document.getElementById('wsDnHours'); if (i) i.value = '8'; })()")
    page.evaluate("(function(){ var b = document.querySelector('#wsCellPopup .ws-dn-ok'); if (b) b.click(); })()")
    page.wait_for_timeout(900)
    frame = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-12'") !== -1 && oc.indexOf("'023'") !== -1) {
                var cs = getComputedStyle(tds[i]);
                // Task 310: рамка — псевдоэлемент ::before (border 1px
                // + border-radius 3px, как у свотча миниатюры), а не
                // box-shadow (было inset 2px в Task 309)
                var bf = getComputedStyle(tds[i], '::before');
                return { cls: tds[i].className, text: tds[i].textContent.trim(),
                         shadow: cs.boxShadow,
                         bfContent: bf.content,
                         bfBorderTop: bf.borderTopWidth,
                         bfBorderStyle: bf.borderTopStyle,
                         bfRadius: bf.borderTopLeftRadius,
                         bfPointerEvents: bf.pointerEvents };
            }
        }
        return null;
    })()""")
    check('I2: ячейка получила «д» с классом ws-manual-dn и рамкой ::before 1px + radius',
          frame is not None and 'ws-manual-dn' in frame['cls'] and
          frame['text'] == 'д' and frame['bfContent'] != 'none' and
          frame['bfBorderTop'] == '1px' and frame['bfBorderStyle'] == 'solid' and
          frame['bfRadius'] == '3px' and frame['bfPointerEvents'] == 'none', frame)

    # I3. Плановая «Н» Иванова 01.09 (авто) — БЕЗ рамки (только ручные д/н)
    auto = page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-01'") !== -1 && oc.indexOf("'017'") !== -1) {
                return { cls: tds[i].className };
            }
        }
        return null;
    })()""")
    check('I3: авто-код БЕЗ рамки (ws-manual-dn нет на плановых ячейках)',
          auto is not None and 'ws-manual-dn' not in auto['cls'], auto)
    page.screenshot(path='scripts/task309-proof-manual-dn.png', full_page=False)

    # J. JS-ошибок нет
    check('J: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])
    ctx.close()

    # ---------- Контекст 2: мобильный 375px, Админ (клик, без hover) ----------
    ctxm = browser.new_context(viewport={'width':375,'height':720}, has_touch=True)
    pagem = ctxm.new_page()
    js_errors_m = []
    pagem.on('pageerror', lambda e: js_errors_m.append(str(e)))
    def handle_m(route, request):
        handle(route, request)
    ctxm.route('**/exec?**', handle)
    ctxm.route('**script.google.com/**', handle)

    pagem.goto('http://localhost:%d/index.html' % PORT)
    pagem.evaluate("localStorage.setItem('kip8_session_token','browser-check-t309-m')")
    pagem.reload()
    pagem.wait_for_timeout(2500)
    pagem.evaluate("navigateTo('work-schedule')")
    pagem.wait_for_timeout(1500)
    pagem.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '9';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    pagem.wait_for_timeout(2500)
    # тап по полю сотрудника — карточка в пределах вьюпорта
    pagem.click('td.ws-emp-col[data-tab="017"]')
    pagem.wait_for_timeout(600)
    mob = pagem.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var r = pp.getBoundingClientRect();
        return { active: pp.classList.contains('active'),
                 inView: r.left >= 0 && r.right <= window.innerWidth && r.top >= 0,
                 w: Math.round(r.width),
                 hasSections: pp.textContent.indexOf('Отпуска · 2026') !== -1 &&
                              pp.textContent.indexOf('Мероприятия · ') !== -1 };
    })()""")
    check('K: 375px — тап открыл карточку, попап в пределах экрана',
          mob['active'] and mob['inView'] and mob['hasSections'], mob)
    pagem.click('#wsEmpPopupCloser', position={'x': 10, 'y': 10})
    pagem.wait_for_timeout(300)
    check('K2: 375px — закрытие по кловеру',
          pagem.evaluate("!document.getElementById('wsEmpPopup').classList.contains('active')"))
    ovf = pagem.evaluate("""(function(){
        var de = document.documentElement;
        return { scrollW: de.scrollWidth, clientW: de.clientWidth };
    })()""")
    check('K3: 375px — нет горизонтального переполнения',
          ovf['scrollW'] <= ovf['clientW'] + 2, ovf)
    pagem.screenshot(path='scripts/task309-proof-mobile.png', full_page=False)
    check('L: мобильный — JS-ошибок нет', len(js_errors_m) == 0, js_errors_m[:3])
    ctxm.close()

    # ---------- Контекст 3: десктоп 1280px, «ИТР8 pro» (просмотр) ----------
    STATE['role'] = 'ИТР8 pro'
    ctx2 = browser.new_context(viewport={'width':1280,'height':800})
    page2 = ctx2.new_page()
    js_errors2 = []
    page2.on('pageerror', lambda e: js_errors2.append(str(e)))
    ctx2.route('**/exec?**', handle)
    ctx2.route('**script.google.com/**', handle)

    page2.goto('http://localhost:%d/index.html' % PORT)
    page2.evaluate("localStorage.setItem('kip8_session_token','browser-check-t309-ro')")
    page2.reload()
    page2.wait_for_timeout(2500)
    page2.evaluate("navigateTo('work-schedule')")
    page2.wait_for_timeout(1500)
    page2.evaluate("""(function(){
        var m = document.getElementById('wsMonthSel');
        var y = document.getElementById('wsYearSel');
        if (m) m.value = '9';
        if (y) y.value = '2026';
        WorkSchedule.onMonthChange();
    })()""")
    page2.wait_for_timeout(2500)
    # (вернули мероприятие для просмотра — id 3)
    page2.click('td.ws-emp-col[data-tab="017"]')
    page2.wait_for_timeout(600)
    ro = page.evaluate if False else page2.evaluate("""(function(){
        var pp = document.getElementById('wsEmpPopup');
        var h = pp ? pp.innerHTML : '';
        return { active: pp ? pp.classList.contains('active') : false,
                 hasInfo: h.indexOf('Отпуска · 2026') !== -1 || h.indexOf('Тип') !== -1,
                 hasEdit: h.indexOf('editTraining(') !== -1,
                 hasDel: h.indexOf('deleteTraining(') !== -1,
                 canEdit: WorkSchedule._canEdit };
    })()""")
    check('M: «ИТР8 pro» — клик открывает карточку (справка; Task 311: hover нет), кнопок ✎/✕ НЕТ',
          ro['active'] and ro['hasInfo'] and not ro['hasEdit'] and not ro['hasDel'] and
          ro['canEdit'] is False, ro)
    check('N: JS-ошибок нет (просмотр, 0 pageerror)', len(js_errors2) == 0, js_errors2[:3])
    ctx2.close()
    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task309-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
