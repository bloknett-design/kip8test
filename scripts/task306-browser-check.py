# -*- coding: utf-8 -*-
# Task 306: browser-check «График работы» — три изменения по заявке:
#   1. Бейдж плановой смены — ТОЛЬКО у «сменных» (дневной 023 в
#      отпуске бейджа НЕ показывает, сменный 017 — показывает);
#   2. ПР (прогул) и * (примечание) — новые коды мероприятий:
#      бейдж «ПР» на сменной ячейке, пунктирный «*» на пустой,
#      событие в тултипе на дне плана отпуска, карточки на странице
#      «Инструктажи» с плашками ПР/*, форма «Новое мероприятие»
#      с 5 типами;
#   3. Кнопки «Обновить» + «Сформировать» объединены: wsCalChip
#      удалён; клик «Сформировать» → диалог → подтверждение
#      запускает И генерацию, И тихое обновление производственного
#      календаря (ProdCalendar.refreshNow(true) — spy).
# Playwright + мок fetch (перехват POST к Apps Script по action).
#
# СТЕНД: 017 «сменный» (шаблон 1: Д/Н/вых×3, старт 31.08.2026):
#   01.09=Н (запись; прогул-мероприятие → бейдж «ПР»),
#   02.09=вых (пусто; примечание-мероприятие → пунктирный «*»),
#   05–16.09=«ОТ» (отпуск; бейджи Д/Н по циклу);
# 023 «дневной» (шаблон 2: Д8×5/вых×2, старт 07.09.2026):
#   22.09 — план отпуска (пусто; прогул-мероприятие → только тултип).
import json, sys, time
from playwright.sync_api import sync_playwright

WS_URL = 'https://script.google.com/macros/s/AKfycbyt2sjbJ8xT5UPKDlYj4q-CV-5pH_Yrv5COrg0PIpp92snpQULUNtJC__pMnQ0h6feNlA/exec'

CODES = [
  {'code':'Д','name':'День, плановая дневная 12-часовая смена (7:30–19:30)','color':'#FFE082'},
  {'code':'Д8','name':'День, плановая дневная 8-часовая смена (7:30–16:30)','color':'#FFF9C4'},
  {'code':'Д7,2','name':'День, плановая дневная 7,2-часовая смена (пятница/предпраздничный)','color':'#FFF9C4'},
  {'code':'Н','name':'Ночь, плановая ночная 12-часовая смена (19:30–7:30)','color':'#B0BEC5'},
  {'code':'д','name':'День, работа в выходные и праздничные дни','color':'#FFD54F'},
  {'code':'н','name':'Ночь, работа в выходные и праздничные дни','color':'#78909C'},
  {'code':'ОТ','name':'Отпуск, ежегодный основной оплачиваемый','color':'#ECEFF1'},
  {'code':'У','name':'Учебный отпуск','color':'#80CBC4'},
  {'code':'ОВ','name':'Отгул (оплачиваемый)','color':'#C5E1A5'},
  {'code':'Б','name':'Больничный','color':'#F8BBD0'},
  {'code':'ПР','name':'Прогул','color':'#EF5350'},
  {'code':'И','name':'Инструктаж, повторные по охране труда и промбезопасности','color':'#B3E5FC'},
  {'code':'ОБ','name':'Обучение, по охране труда и промышленной безопасности','color':'#D1C4E9'},
  {'code':'ПЗ','name':'Проверка знаний, до 1000В, на допуск к самостоятельной работе','color':'#FFCDD2'},
  {'code':'*','name':'Примечание (с комментарием)','color':'#FFAB91'},
  {'code':'.','name':'Плановый выходной день','color':'#CFD8DC'}
]
EMPLOYEES = [
  {'таб_номер':'017','ФИО':'Иванов И. И.','тип':'сменный','смена':1,'шаблон_ротации':1,'старт_цикла':'2026-08-31','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА смена №1','комментарий':''},
  {'таб_номер':'023','ФИО':'Петров П. П.','тип':'дневной','смена':'','шаблон_ротации':2,'старт_цикла':'2026-09-07','дата_приёма':'','дата_увольнения':'','в_архиве':0,'должность':'Слесарь КИПиА дневной','комментарий':''}
]
PATTERNS = [
  {'id':1,'name':'Сменный 5-дневный','cycle':5,'description':'','days':[{'day':1,'status':'Д'},{'day':2,'status':'Н'},{'day':3,'status':''},{'day':4,'status':''},{'day':5,'status':''}]},
  {'id':2,'name':'Дневной 5/2','cycle':7,'description':'','days':[{'day':1,'status':'Д8'},{'day':2,'status':'Д8'},{'day':3,'status':'Д8'},{'day':4,'status':'Д8'},{'day':5,'status':'Д8'},{'day':6,'status':''},{'day':7,'status':''}]}
]
ENTRIES = [
  # 017: 01.09 — смена «Н» (прогул-мероприятие = бейдж «ПР» рядом)
  {'дата':'2026-09-01','таб_номер':'017','статус':'Н','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-08-31T10:00:00Z','замещает':None,'инструкция':1,'комментарий':''},
  # 017: отпуск 05–16.09 — бейджи плановых смен по циклу (Task 305)
  {'дата':'2026-09-05','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  {'дата':'2026-09-06','таб_номер':'017','статус':'ОТ','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''},
  # 023: обычная смена (контроль)
  {'дата':'2026-09-14','таб_номер':'023','статус':'Д8','переработка':0,'праздник':0,'источник':'авто','дата_обновления':'2026-09-01T10:00:00Z','замещает':None,'инструкция':None,'комментарий':''}
]
TRAININGS = [
  # Task 306: новые типы мероприятий
  {'id':1,'таб_номер':'017','тип':'прогул','тема':'Не явился на смену, акт №3','дата_начала':'2026-09-01','дата_окончания':'2026-09-01','длительность_дней':1,'комментарий':''},
  {'id':2,'таб_номер':'017','тип':'примечание','тема':'Смена перенесена по приказу №145','дата_начала':'2026-09-02','дата_окончания':'2026-09-02','длительность_дней':1,'комментарий':'по приказу'},
  {'id':3,'таб_номер':'023','тип':'прогул','тема':'Прогул в отпуске не показываем бейджем','дата_начала':'2026-09-22','дата_окончания':'2026-09-22','длительность_дней':1,'комментарий':''}
]
VACATIONS = [
  {'id':1,'таб_номер':'017','часть':2,'дата_начала':'2026-09-05','дата_окончания':'2026-09-16','комментарий':''},
  {'id':2,'таб_номер':'023','часть':1,'дата_начала':'2026-09-21','дата_окончания':'2026-09-25','комментарий':''}
]

GEN_STATE = {'calls': 0, 'gen': 5, 'updated': 0, 'removed': 0, 'vacDays': 2}

def mock_response(action):
    if action == 'getCurrentUser':
        return {'ok':True,'data':{'userId':1,'email':'admin@test.local','role':'Админ'}}
    if action == 'getMyAccess':
        return {'ok':True,'data':{'role':'Админ','perms':{'admin.panel':True,'workschedule.view':True,'workschedule.edit':True,'flowmeter.view':True,'flowmeter.input':True}}}
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
    if action == 'workSchedule.generateMonth':
        GEN_STATE['calls'] += 1
        return {'ok':True,'data':{'generated':GEN_STATE['gen'],'updated':GEN_STATE['updated'],
                                   'removed':GEN_STATE['removed'],'vacationDays':GEN_STATE['vacDays'],
                                   'vacationsFound':2,'vacationError':None,
                                   'trainingDays':1,'eventGenerated':0,'eventRestored':0,
                                   'eventRemoved':0,'perEmployee':{},'monthStart':'2026-09-01',
                                   'daysInMonth':30,'warnings':[]}}
    return {'ok':False,'error':'unknown action ' + str(action)}

results = []
def check(name, cond, extra=''):
    results.append((name, bool(cond), extra))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(extra)) if (extra and not cond) else ''))

def toast_text(page):
    return page.evaluate("(function(){var t=document.querySelector('#toast');return t? (t.textContent||'') : '';})()")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={'width':375,'height':720})  # мобильный
    page = ctx.new_page()
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(str(e)))

    def handle(route, request):
        url = request.url
        action = ''
        if 'action=' in url:
            action = url.split('action=')[1].split('&')[0]
        try:
            from urllib.parse import unquote
            action = unquote(action)
        except Exception:
            pass
        body = json.dumps(mock_response(action), ensure_ascii=False)
        route.fulfill(status=200, content_type='application/json; charset=utf-8',
                      body=body.encode('utf-8') if isinstance(body, str) else body)
    ctx.route('**/exec?**', handle)
    ctx.route('**script.google.com/**', handle)

    page.goto('http://localhost:8925/index.html')
    page.evaluate("localStorage.setItem('kip8_session_token','browser-check-t306')")
    page.reload()
    page.wait_for_timeout(2500)

    # A. Страница загрузилась
    check('A: страница загрузилась, дашборд активен',
          page.evaluate("!!document.querySelector('#page-dashboard') && document.title==='КИПиА'"))

    # B. Переход на График работы + сентябрь 2026
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

    # C. Task 306-1: бейдж плановой смены — только у «сменных»
    shift_info = page.evaluate("""(function(){
        var out = { ivan05: null, petr22: null, total: 0 };
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (!tds.length) continue;
            if (tds[0].textContent.indexOf('Иванов') !== -1 && tds[5]) {
                var b = tds[5].querySelector('.ws-ev-badge.ws-ev-shift');
                out.ivan05 = { text: tds[5].textContent.trim(), badge: b ? b.textContent : null };
            }
            if (tds[0].textContent.indexOf('Петров') !== -1 && tds[22]) {
                var b2 = tds[22].querySelector('.ws-ev-badge');
                out.petr22 = { text: tds[22].textContent.trim(), plan: tds[22].classList.contains('ws-vac-plan'),
                               badges: tds[22].querySelectorAll('.ws-ev-badge').length,
                               shift: tds[22].querySelectorAll('.ws-ev-shift').length,
                               ev: b2 ? {text: b2.textContent.trim(),
                                         dashed: b2.classList.contains('ws-ev-pending')} : null };
            }
        }
        out.total = document.querySelectorAll('.ws-ev-badge.ws-ev-shift').length;
        return out;
    })()""")
    check('C: 017 (сменный) 05.09 — «ОТ» + бейдж «Д»',
          shift_info and shift_info['ivan05'] and
          shift_info['ivan05']['text'].startswith('ОТ') and shift_info['ivan05']['badge'] == 'Д',
          shift_info)
    check('C2: 023 (дневной) 22.09 — план «ОТ», бейджа СМЕНЫ нет (фильтр empIsShift жив); Task 314 — событие «ПР» пунктирным бейджем',
          shift_info and shift_info['petr22'] and shift_info['petr22']['plan'] and
          shift_info['petr22']['shift'] == 0 and
          shift_info['petr22']['ev'] and shift_info['petr22']['ev']['text'] == 'ПР' and
          shift_info['petr22']['ev']['dashed'], shift_info)
    check('C3: бейджей плановой смены в сетке = 6 (только 017: 05/10/15=Д, 06/11/16=Н)',
          shift_info and shift_info['total'] == 6, shift_info)

    # D. Task 306-2: бейдж «ПР» на сменной ячейке (прогул-мероприятие)
    pr = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[1]){
                var td = tds[1];
                var b = td.querySelector('.ws-ev-badge:not(.ws-ev-shift)');
                return { text: td.textContent.trim(), badge: b ? b.textContent : null,
                         bg: b ? getComputedStyle(b).backgroundColor : null,
                         dashed: b ? b.classList.contains('ws-ev-pending') : null,
                         title: td.getAttribute('title') || '' };
            }
        }
        return null;
    })()""")
    check('D: 01.09 — смена «Н» + бейдж мероприятия «ПР»',
          pr and pr['text'].startswith('Н') and pr['badge'] == 'ПР', pr)
    check('D2: бейдж «ПР» сплошной, цвет справочника #EF5350',
          pr and pr['bg'] == 'rgb(239, 83, 80)' and not pr['dashed'], pr)
    # Task 311: тултипы с ячеек убраны — событие-прогул видно бейджем
    # «ПР» в ячейке и в секции мероприятий попапа клика
    check('D3: Task 311 — тултип мероприятия убран (title пуст), бейдж «ПР» жив',
          pr and pr['title'] == '' and pr['badge'] == 'ПР', pr['title'][:200] if pr else '')

    # E. Task 306-2: пунктирный бейдж «*» на пустой ячейке (примечание)
    star = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Иванов') !== -1 && tds[2]){
                var td = tds[2];
                var b = td.querySelector('.ws-ev-badge');
                return { text: td.textContent.trim(), badge: b ? b.textContent : null,
                         dashed: b ? b.classList.contains('ws-ev-pending') : null,
                         title: td.getAttribute('title') || '' };
            }
        }
        return null;
    })()""")
    check('E: 02.09 — пустая ячейка + пунктирный бейдж «*»',
          star and star['badge'] == '*' and star['dashed'], star)
    # Task 311: тултип подсказки убран — пунктирный бейдж остаётся
    check('E2: Task 311 — тултип «заполнится кодом…» убран (title пуст), пунктир жив',
          star and star['title'] == '' and star['dashed'], star['title'][:200] if star else '')

    # Скриншот сетки: бейдж «ПР» на «Н», пунктирный «*», бейджи Д/Н под «ОТ»
    page.screenshot(path='scripts/task306-proof-grid.png', full_page=False)

    # F. Событие на дне плана отпуска — Task 314: событие-прогул
    #    теперь ВИДНО пунктирным бейджем «ПР» (заявка: «мероприятия —
    #    маленькими бейджами-«иконками»»; раньше — только тултип,
    #    Task 311 тултипы убрал — событие жило лишь в попапе/карточке)
    check('F: 22.09 (023) — событие-прогул: пунктирный бейдж «ПР» на дне плана (Task 314)',
          shift_info and shift_info['petr22'] and
          shift_info['petr22']['ev'] and shift_info['petr22']['ev']['text'] == 'ПР' and
          shift_info['petr22']['ev']['dashed'],
          'см. C2')
    tip22 = page.evaluate("""(function(){
        var rows = document.querySelectorAll('#wsGridWrap tbody tr');
        for (var r=0;r<rows.length;r++){
            var tds = rows[r].querySelectorAll('td');
            if (tds.length && tds[0].textContent.indexOf('Петров') !== -1 && tds[22]){
                return { title: tds[22].getAttribute('title') || '' };
            }
        }
        return null;
    })()""")
    # Task 311: тултип убран — план показывает класс ws-vac-plan и код «ОТ»
    check('F2: Task 311 — тултип 22.09 убран (title пуст), план «ОТ» в ячейке жив',
          tip22 and tip22['title'] == '',
          tip22['title'][:250] if tip22 else '')

    # G. Страница «Инструктажи» УДАЛЕНА (Task 308) — карточек с плашками
    #    ПР/* больше нет; цвета новых типов по-прежнему видны пользователю:
    #    бейдж в ячейке (D2: #EF5350) и свотч в попапе ячейки (справочник
    #    «Коды_статусов» → _statusMeta)
    page.evaluate("navigateTo('work-schedule-trainings')")
    page.wait_for_timeout(1000)
    gone = page.evaluate("""(function(){
        var act = document.querySelector('.page-content.active');
        return { page: !!document.getElementById('page-work-schedule-trainings'),
                 cards: document.querySelectorAll('.ws-tr-card').length,
                 plaques: document.querySelectorAll('.ws-tr-type').length,
                 active: act ? act.id : '' };
    })()""")
    check('G: страница «Инструктажи» удалена (Task 308) — карточек/плашек нет',
          not gone['page'] and gone['cards'] == 0 and gone['plaques'] == 0, gone)

    # G2/G3: свотчи ПР и * в окне «Мероприятия в этот день» (Task 313:
    #     окно НАД окном кодов) — цвета справочника
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1200)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-01'") !== -1 && oc.indexOf("'017'") !== -1) { tds[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(600)
    pr_pop = page.evaluate("""(function(){
        var popup = document.getElementById('wsEventsPopup');
        var rows = popup ? popup.querySelectorAll('.ws-popup-row') : [];
        for (var i=0;i<rows.length;i++){
            var code = rows[i].querySelector('.ws-popup-code');
            if (code && code.textContent.trim() === 'ПР') {
                var sw = rows[i].querySelector('.ws-popup-swatch');
                return { code: 'ПР', bg: sw ? getComputedStyle(sw).backgroundColor : '' };
            }
        }
        return null;
    })()""")
    check('G2: окно мероприятий — строка «ПР» со свотчем #EF5350 (справочник жив)',
          pr_pop and pr_pop['bg'] == 'rgb(239, 83, 80)', pr_pop)
    page.evaluate("""(function(){
        var closer = document.querySelector('.ws-popup-closer');
        if (closer) closer.click();
    })()""")
    page.wait_for_timeout(400)
    page.evaluate("""(function(){
        var tds = document.querySelectorAll('#wsGridWrap td.ws-cell');
        for (var i=0;i<tds.length;i++){
            var oc = tds[i].getAttribute('onclick') || '';
            if (oc.indexOf("'2026-09-02'") !== -1 && oc.indexOf("'017'") !== -1) { tds[i].click(); return; }
        }
    })()""")
    page.wait_for_timeout(600)
    star_pop = page.evaluate("""(function(){
        var popup = document.getElementById('wsEventsPopup');
        var rows = popup ? popup.querySelectorAll('.ws-popup-row') : [];
        for (var i=0;i<rows.length;i++){
            var code = rows[i].querySelector('.ws-popup-code');
            if (code && code.textContent.trim() === '*') {
                var sw = rows[i].querySelector('.ws-popup-swatch');
                return { code: '*', bg: sw ? getComputedStyle(sw).backgroundColor : '' };
            }
        }
        return null;
    })()""")
    check('G3: окно мероприятий — строка «*» со свотчем #FFAB91 (справочник жив)',
          star_pop and star_pop['bg'] == 'rgb(255, 171, 145)', star_pop)
    page.evaluate("""(function(){
        var closer = document.querySelector('.ws-popup-closer');
        if (closer) closer.click();
    })()""")
    page.wait_for_timeout(300)
    page.screenshot(path='scripts/task306-proof-trainings.png', full_page=False)

    # H. Форма «Новое мероприятие»: 5 типов
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(1200)
    page.evaluate("WorkSchedule.openTrainingForm()")
    page.wait_for_timeout(600)
    form = page.evaluate("""(function(){
        var sel = document.getElementById('wsTrType');
        if (!sel) return null;
        var vals = [];
        for (var i=0;i<sel.options.length;i++) vals.push(sel.options[i].value);
        return { open: document.getElementById('wsTrSheet').classList.contains('active'), options: vals };
    })()""")
    check('H: форма «Новое мероприятие» открыта, 5 типов',
          form and form['open'] and form['options'] ==
          ['инструктаж','обучение','проверка_знаний','прогул','примечание'], form)
    page.evaluate("WorkSchedule.closeTrainingForm()")
    page.wait_for_timeout(400)

    # I. Task 306-3: тулбар — одна кнопка «Сформировать»
    # Task 315/317: кнопки разнесены по рядам КОЛОНКИ кнопок
    # (.ws-toolbar-main): ряд 1 (.ws-toolbar-row) — «Обновить»;
    # ряд 2 (.ws-actions-row) — «Сохранить» (при правках);
    # ряд 3 (.ws-generate-row) — «Сформировать»
    toolbar = page.evaluate("""(function(){
        var bar = document.querySelector('.ws-toolbar-row');
        var gen = document.getElementById('wsGenerateBtn');
        var genRow = document.getElementById('wsGenerateRow');
        var cal = document.getElementById('wsCalChip');
        var labels = [];
        if (bar) bar.querySelectorAll('button').forEach(function(b){
            labels.push((b.id || '?') + ':' + b.textContent.trim());
        });
        return { calChip: !!cal, genBtn: gen ? !gen.hidden : false,
                 genText: gen ? gen.textContent.trim() : '',
                 genRowShown: genRow ? !genRow.hidden : false,
                 buttons: labels };
    })()""")
    check('I: кнопки «Обновить» (wsCalChip) НЕТ, «Сформировать» видна',
          toolbar and not toolbar['calChip'] and toolbar['genBtn'] and
          toolbar['genText'] == 'Сформировать', toolbar)
    check('I2: Task 314/315/317 — «Обновить» в ряду 1; «Сформировать» — в ряду 3 (.ws-generate-row)',
          toolbar and any('wsRefreshBtn:Обновить' in b for b in toolbar['buttons']) and
          toolbar['genRowShown'] and toolbar['genText'] == 'Сформировать' and
          not any('wsGenerateBtn' in b for b in toolbar['buttons']), toolbar)

    # J. Клик «Сформировать» → диалог → «Текущий месяц» → генерация +
    #    тихое обновление календаря (spy)
    page.evaluate("""(function(){
        window.__refreshSpy = [];
        var orig = ProdCalendar.refreshNow;
        ProdCalendar.refreshNow = function(silent){
            window.__refreshSpy.push(silent === true);
            return orig.apply(ProdCalendar, arguments);
        };
    })()""")
    page.click('#wsGenerateBtn')
    page.wait_for_timeout(700)
    dialog = page.evaluate("""(function(){
        var alt = document.querySelector('.kip-dialog-alt');
        var ok = document.querySelector('.kip-dialog-ok');
        var ttl = document.querySelector('.kip-dialog-title');
        return { title: ttl ? ttl.textContent : '', hasAlt: !!alt,
                 altText: alt ? alt.textContent : '', okText: ok ? ok.textContent : '' };
    })()""")
    check('J: открыт диалог «Формирование шахматки» с выбором периода',
          dialog and dialog['title'] == 'Формирование шахматки' and
          dialog['okText'] == 'Весь год' and dialog['hasAlt'], dialog)
    page.click('.kip-dialog-alt')
    page.wait_for_timeout(1500)
    spy = page.evaluate("window.__refreshSpy")
    check('J2: подтверждение запустило ТИХОЕ обновление календаря (silent=true)',
          spy == [True], spy)
    check('J3: серверный generateMonth вызван (месяц)',
          GEN_STATE['calls'] == 1, GEN_STATE['calls'])
    t_month = toast_text(page)
    check('J4: тост «Сентябрь 2026: сформировано …»', 'сформировано' in t_month, t_month[:150])
    btn_back = page.evaluate("(function(){var b=document.getElementById('wsGenerateBtn');return b? {t:b.textContent.trim(), d:b.disabled}:{}})()")
    check('J5: кнопка вернулась в «Сформировать»', btn_back and btn_back['t'] == 'Сформировать' and not btn_back['d'], btn_back)

    # K. «Сформировать» → «Весь год» → 12 вызовов + второе обновление
    page.click('#wsGenerateBtn')
    page.wait_for_timeout(700)
    page.click('.kip-dialog-ok')
    page.wait_for_timeout(4000)
    spy2 = page.evaluate("window.__refreshSpy")
    check('K: год — 12 вызовов generateMonth (итого 13)',
          GEN_STATE['calls'] == 13, GEN_STATE['calls'])
    check('K2: тихое обновление календаря — второй вызов (итого 2)',
          spy2 == [True, True], spy2)
    t_year = toast_text(page)
    check('K3: тост «Год 2026: …»', ('Год 2026' in t_year), t_year[:150])
    btn_back2 = page.evaluate("(function(){var b=document.getElementById('wsGenerateBtn');return b? {t:b.textContent.trim(), d:b.disabled}:{}})()")
    check('K4: кнопка вернулась в «Сформировать» (после года)',
          btn_back2 and btn_back2['t'] == 'Сформировать' and not btn_back2['d'], btn_back2)

    # L. Окошко производственного календаря живо (без кнопки «Обновить»)
    panel = page.evaluate("(function(){var el=document.getElementById('wsCalPanel');return el? {hidden: el.hidden, text: el.textContent.slice(0,80)} : null;})()")
    check('L: окошко календаря (нормы) в тулбаре живо', panel and not panel['hidden'] and ('Норма' in panel['text']), panel)

    # Скриншот тулбара с одной кнопкой
    page.screenshot(path='scripts/task306-proof-toolbar.png', full_page=False)

    # M. JS-ошибок нет
    check('M: JS-ошибок нет (0 pageerror)', len(js_errors) == 0, js_errors[:3])

    browser.close()

passed = sum(1 for r in results if r[1])
failed = len(results) - passed
print('\n==========================================')
print('task306-browser-check: %d passed / %d failed' % (passed, failed))
print('==========================================')
sys.exit(1 if failed else 0)
