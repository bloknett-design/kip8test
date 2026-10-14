#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 523 browser-check: Табель — времена начала/окончания работ
# д/н дневного персонала СОХРАНЯЮТСЯ (колонки L/M «Записи_графика»,
# часы K пересчитываются из пары) и ОТОБРАЖАЮТСЯ; «н» = «д» (заявка):
#  A) ХОВЕР день-«д» с парой 07:30–15:12 (7,2 ч) → секция «Статус
#     дня» с «Время работы: 07:30–15:12 · 7,2 ч»;
#  B) ХОВЕР день-«н» с ночной парой 19:30–07:30 (12 ч) → «Время
#     работы: 19:30–07:30 · 12 ч (через полночь)» — СИММЕТРИЯ «н»;
#  C) ХОВЕР день-«д» БЕЗ пары (легаси Task 322, только часы) →
#     «Время работы: 7,2 ч» (регресс Task 522);
#  D) КЛИК пустой → «д» → форма 07:30–15:30/«8 ч» → 08:00–15:12 →
#     живой расчёт 7,2 → Готово → _PENDING {часы 7,2; пара};
#  E) КЛИК пустой → «н» → форма 19:30–03:30/«8 ч (через полночь)» →
#     19:30–07:30 → 12 ч → Готово → _PENDING {часы 12; пара} — «н»;
#  F) КЛИК ячейки С парой → «д» → префилл ТОЧНО 07:30–15:12
#     (раунд-трип, не через округление часов);
#  G) «Сохранить» → payload setManualEntry несёт время_начала/
#     время_окончания/часы (д И н);
#  H) ХОВЕР сменный «д» — тишина (не тронуто);
#  I) 0 JS-ошибок; скриншоты в download/kip8test-task523/.
import calendar
import datetime
import json
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

PORT = 8999
TODAY = datetime.date.today()
Y, M = TODAY.year, TODAY.month
DIM = calendar.monthrange(Y, M)[1]
D1 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 11)))   # день-«д» с парой
D2 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 12)))   # день-«н» ночная пара
D3 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 13)))   # день-«д» легаси
D4 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 14)))   # сменный «д»
D5 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 15)))   # пустая → ввод «д»
D6 = '%04d-%02d-%02d' % (Y, M, max(1, min(DIM, 16)))   # пустая → ввод «н»
DAY1, DAY2, DAY3, DAY4, DAY5, DAY6 = 11, 12, 13, 14, 15, 16
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(os.path.dirname(REPO), 'download', 'kip8test-task523')
os.makedirs(SHOT_DIR, exist_ok=True)

PASS = 0
FAIL = 0
SAVED = []   # перехваченные payload setManualEntry


def check(name, cond, extra=''):
    global PASS, FAIL
    ok = bool(cond)
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(('  + ' if ok else '  X ') + name +
          (('  [' + str(extra)[:240] + ']') if (extra and not ok) else ''))


def shot(page, name):
    try:
        page.screenshot(path=os.path.join(SHOT_DIR, name))
    except Exception as e:
        print('  (скриншот %s не сохранён: %s)' % (name, e))


DN_NAME = ('День, плановая продолжительность работы в выходные и '
           'нерабочие праздничные дни, для сменного персонала дневная '
           '12-часовая смена (с 7:30 до 19:30), для дневного персонала — '
           'с указанием продолжительности (в часах) в комментарии')
NN_NAME = ('Ночь, плановая продолжительность работы в выходные и '
           'нерабочие праздничные дни, для сменного персонала ночная '
           '12-часовая смена (с 19:30 до 7:30), для дневного персонала — '
           'с указанием продолжительности (в часах) в комментарии')

CODES = [
  {'code': 'Д', 'name': 'День, плановая 12-часовая смена', 'color': '#FFE082'},
  {'code': 'д', 'name': DN_NAME, 'color': '#FFD54F'},
  {'code': 'н', 'name': NN_NAME, 'color': '#78909C'},
  {'code': 'ОТ', 'name': 'Отпуск', 'color': '#ECEFF1'},
  {'code': '', 'name': 'Выходной', 'color': '#EEF0F2'},
]
EMPLOYEES = [
  {'таб_номер': '017', 'ФИО': 'Иванов Иван Иванович', 'тип': 'сменный',
   'смена': 1, 'шаблон_ротации': 1, 'старт_цикла': '%04d-%02d-01' % (Y, M),
   'дата_приёма': '2024-03-15', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
  {'таб_номер': '023', 'ФИО': 'Петров Пётр Петрович', 'тип': 'дневной',
   'смена': '', 'шаблон_ротации': 2, 'старт_цикла': '%04d-%02d-07' % (Y, M),
   'дата_приёма': '2025-01-20', 'дата_увольнения': '', 'в_архиве': 0,
   'должность': 'Слесарь КИПиА', 'комментарий': ''},
]
PATTERNS = [
  {'id': 1, 'name': 'Сменный сутки/двое', 'cycle': 4, 'description': '',
   'days': [{'day': 1, 'status': 'Д'}, {'day': 2, 'status': 'Н'},
            {'day': 3, 'status': ''}, {'day': 4, 'status': ''}]},
]
# записи месяца: K часы + L/M времена (новый сервер listEntries)
ENTRIES = [
  {'дата': D1, 'таб_номер': '023', 'статус': 'д', 'часы': 7.7,
   'время_начала': '07:30', 'время_окончания': '15:12',
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
  {'дата': D2, 'таб_номер': '023', 'статус': 'н', 'часы': 12,
   'время_начала': '19:30', 'время_окончания': '07:30',
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
  {'дата': D3, 'таб_номер': '023', 'статус': 'д', 'часы': 7.2,
   'переработка': 1, 'праздник': 0, 'источник': 'руч',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
  {'дата': D4, 'таб_номер': '017', 'статус': 'д', 'часы': None,
   'переработка': 1, 'праздник': 0, 'источник': 'авто',
   'дата_обновления': None, 'замещает': None, 'инструкция': None,
   'комментарий': ''},
]
TRAININGS = []


def mock_response(action, body):
    if action == 'getCurrentUser':
        return {'ok': True, 'data': {'userId': 1, 'email': 'user@test.local',
                                     'role': 'Админ'}}
    if action == 'getMyAccess':
        return {'ok': True, 'data': {'role': 'Админ', 'found': True,
                'permissions': {'workschedule.view': True,
                                'workschedule.edit': True}}}
    if action == 'heartbeat':
        return {'ok': True, 'data': {'ok': True}}
    if action == 'workSchedule.getStatusCodes':
        return {'ok': True, 'data': {'codes': CODES}}
    if action == 'workSchedule.listEmployees':
        return {'ok': True, 'data': {'employees': EMPLOYEES}}
    if action == 'workSchedule.getPatterns':
        return {'ok': True, 'data': {'patterns': PATTERNS}}
    if action == 'workSchedule.listTrainings':
        return {'ok': True, 'data': {'trainings': TRAININGS}}
    if action == 'workSchedule.listPpe':
        return {'ok': True, 'data': {'ppe': []}}
    if action == 'workSchedule.listEntries':
        return {'ok': True, 'data': {'entries': ENTRIES}}
    if action == 'workSchedule.listVacations':
        return {'ok': True, 'data': {'vacations': []}}
    if action == 'workSchedule.setManualEntry':
        SAVED.append(body)
        return {'ok': True, 'data': {'ok': True, 'часы': body.get('часы'),
                'время_начала': body.get('время_начала'),
                'время_окончания': body.get('время_окончания')}}
    return {'ok': True, 'data': {'ok': True}}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


MARK_JS = r"""(([t, dn]) => {
    document.querySelectorAll('[data-testid="hc"]')
        .forEach(c => c.removeAttribute('data-testid'));
    const emp = document.querySelector('td.ws-emp-col[data-tab="' + t + '"]');
    const td = emp.closest('tr').querySelector('td[data-day="' + dn + '"]');
    td.setAttribute('data-testid', 'hc');
    return !!td;})"""


def mark_cell(page, tab, day):
    return page.evaluate(MARK_JS, [tab, str(day)])


def close_hover_window(page):
    try:
        page.hover('#wsGridWrap thead th', timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(700)


def events_popup_state(page):
    return page.evaluate("""(() => {
        const w = document.getElementById('wsEventsPopup');
        const codes = document.getElementById('wsCellPopup');
        return {
            win: !!(w && w.classList.contains('active')),
            html: w ? w.innerHTML : '',
            codesWin: !!(codes && codes.classList.contains('active'))};})()""")


def click_cell(page, tab, day):
    page.evaluate("""((p) => {
        const empCell = document.querySelector(
            'td.ws-emp-col[data-tab="' + p.tab + '"]');
        const td = empCell.closest('tr')
            .querySelector('td[data-day="' + p.day + '"]');
        td.dispatchEvent(new MouseEvent('click',
            {bubbles: true, cancelable: true}));})""",
        {'tab': tab, 'day': str(day)})


def click_code_row(page, code):
    return page.evaluate("""((c) => {
        const rows = document.querySelectorAll('#wsCellPopup .ws-popup-row');
        for (let i = 0; i < rows.length; i++) {
            const codeEl = rows[i].querySelector('.ws-popup-code');
            if (codeEl && codeEl.textContent.trim() === c) {
                rows[i].dispatchEvent(new MouseEvent('click',
                    {bubbles: true, cancelable: true}));
                return true;
            }
        }
        return false;})""", code)


def form_state(page):
    return page.evaluate("""(() => {
        const s = document.getElementById('wsDnStart');
        const e = document.getElementById('wsDnEnd');
        const c = document.getElementById('wsDnCalc');
        return {start: s ? s.value : null,
                end: e ? e.value : null,
                calc: c ? c.textContent.trim() : null,
                form: !!document.querySelector('#wsCellPopup .ws-dn-form')};})""")


def pending(page):
    return page.evaluate("""(() => {
        const p = window.WorkSchedule && WorkSchedule._PENDING || {};
        const out = {};
        Object.keys(p).forEach(function(k) { out[k] = p[k]; });
        return out;})""")


def open_grid(page):
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    page.wait_for_timeout(2500)


def main():
    os.chdir(REPO)
    server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = ctx.new_page()
        js_errors = []
        page.on('pageerror', lambda e: js_errors.append(str(e)))
        page.on('dialog', lambda dg: dg.accept())
        ctx.add_init_script(
            "try{localStorage.removeItem('kip8test:kip8_ws_cache_v1')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_my_access')}catch(e){};" +
            "try{localStorage.removeItem('kip8test:kip8_cached_role')}catch(e){};" +
            "localStorage.setItem('kip8test:kip8_session_token','bc-t523');" +
            "localStorage.setItem('kip8test:app-theme','dark');")

        def handle(route, request):
            action = ''
            if 'action=' in request.url:
                action = unquote(request.url.split('action=')[1].split('&')[0])
            body = {}
            if request.post_data:
                try:
                    body = json.loads(request.post_data)
                except Exception:
                    body = {}
            return route.fulfill(status=200,
                content_type='application/json; charset=utf-8',
                body=json.dumps(mock_response(action, body), ensure_ascii=False))

        ctx.route('**/exec?**', handle)
        ctx.route('**script.google.com/**', handle)
        ctx.route('**raw.githubusercontent.com/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**calendar.legalic.ru/**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))
        ctx.route('**isdayoff.ru**', lambda r: r.fulfill(
            status=404, content_type='text/plain', body='nf'))

        open_grid(page)

        # ===== A: ховер день-«д» с парой 07:30–15:12 =====
        print('== A: ховер день-«д» (пара 07:30–15:12, 7,2 ч) ==')
        check('A: ячейка помечена', mark_cell(page, '023', DAY1))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('A: окно открылось ховером', st['win'], st)
        check('A: секция «Статус дня»', 'ws-dn-info' in st['html'])
        check('A: «Время работы: 07:30–15:12 · 7,7 ч» (L/M + K)',
              'Время работы: 07:30–15:12 · 7,7 ч' in st['html'], st['html'][:300])
        check('A: БЕЗ пометки полночи (день)',
              'через полночь' not in st['html'])
        shot(page, 'a-hover-d-times.png')
        close_hover_window(page)

        # ===== B: ховер день-«н» ночная пара (СИММЕТРИЯ) =====
        print('== B: ховер день-«н» (ночь 19:30–07:30, 12 ч) ==')
        check('B: ячейка помечена', mark_cell(page, '023', DAY2))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('B: окно открылось', st['win'])
        check('B: код «н» в секции', 'ws-dn-info-code">н<' in st['html'])
        check('B: «Время работы: 19:30–07:30 · 12 ч (через полночь)»',
              'Время работы: 19:30–07:30 · 12 ч (через полночь)' in st['html'],
              st['html'][:300])
        shot(page, 'b-hover-n-night.png')
        close_hover_window(page)

        # ===== C: ховер день-«д» легаси (только часы) =====
        print('== C: ховер день-«д» без времён (легаси Task 322) ==')
        check('C: ячейка помечена', mark_cell(page, '023', DAY3))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('C: окно открылось', st['win'])
        check('C: «Время работы: 7,2 ч» (регресс Task 522)',
              'Время работы: 7,2 ч' in st['html'], st['html'][:300])
        shot(page, 'c-hover-d-legacy.png')
        close_hover_window(page)

        # ===== D: ввод «д» в пустую ячейку =====
        print('== D: ввод «д» 08:00–15:12 в пустую ячейку ==')
        check('D: ячейка помечена', mark_cell(page, '023', DAY5))
        click_cell(page, '023', DAY5)
        page.wait_for_timeout(300)
        check('D: код «д» выбран', click_code_row(page, 'д'))
        page.wait_for_timeout(300)
        fs = form_state(page)
        check('D: форма открылась', fs['form'], fs)
        check('D: префилл 07:30–15:30 (дефолт)',
              fs['start'] == '07:30' and fs['end'] == '15:30', fs)
        check('D: начальный расчёт «8 ч» (из пары)',
              fs['calc'] == 'Переработка: 8 ч', fs['calc'])
        page.fill('#wsDnStart', '08:00')
        page.fill('#wsDnEnd', '15:12')
        page.wait_for_timeout(200)
        fs = form_state(page)
        check('D: живой расчёт «7,2 ч»', fs['calc'] == 'Переработка: 7,2 ч',
              fs['calc'])
        shot(page, 'd-form-d-live.png')
        page.click('#wsCellPopup .ws-dn-ok')
        page.wait_for_timeout(300)
        pend = pending(page)
        pd = pend.get(D5 + '|023')
        check('D: _PENDING часы 7,2', pd and pd.get('часы') == 7.2, pd)
        check('D: _PENDING время_начала 08:00',
              pd and pd.get('время_начала') == '08:00', pd)
        check('D: _PENDING время_окончания 15:12',
              pd and pd.get('время_окончания') == '15:12', pd)

        # ===== E: ввод «н» в пустую ячейку (СИММЕТРИЯ) =====
        print('== E: ввод «н» 19:30–07:30 в пустую ячейку ==')
        check('E: ячейка помечена', mark_cell(page, '023', DAY6))
        click_cell(page, '023', DAY6)
        page.wait_for_timeout(300)
        check('E: код «н» выбран', click_code_row(page, 'н'))
        page.wait_for_timeout(300)
        fs = form_state(page)
        check('E: форма открылась', fs['form'], fs)
        check('E: префилл 19:30–03:30 (ночь)',
              fs['start'] == '19:30' and fs['end'] == '03:30', fs)
        check('E: начальный расчёт «8 ч (через полночь)» — из пары',
              fs['calc'] == 'Переработка: 8 ч (через полночь)', fs['calc'])
        page.fill('#wsDnEnd', '07:30')
        page.wait_for_timeout(200)
        fs = form_state(page)
        check('E: живой расчёт «12 ч (через полночь)»',
              fs['calc'] == 'Переработка: 12 ч (через полночь)', fs['calc'])
        shot(page, 'e-form-n-midnight.png')
        page.click('#wsCellPopup .ws-dn-ok')
        page.wait_for_timeout(300)
        pend = pending(page)
        pn = pend.get(D6 + '|023')
        check('E: _PENDING часы 12', pn and pn.get('часы') == 12, pn)
        check('E: _PENDING время_начала 19:30',
              pn and pn.get('время_начала') == '19:30', pn)
        check('E: _PENDING время_окончания 07:30',
              pn and pn.get('время_окончания') == '07:30', pn)

        # ===== F: раунд-трип — префилл из сохранённой пары =====
        print('== F: клик ячейки с парой → префилл 07:30–15:12 ==')
        check('F: ячейка помечена', mark_cell(page, '023', DAY1))
        click_cell(page, '023', DAY1)
        page.wait_for_timeout(300)
        check('F: код «д» выбран', click_code_row(page, 'д'))
        page.wait_for_timeout(300)
        fs = form_state(page)
        check('F: префилл ТОЧНО 07:30–15:12 (не 07:30–14:42 из 7,2 ч)',
              fs['start'] == '07:30' and fs['end'] == '15:12', fs)
        check('F: расчёт из пары «7,7 ч»', fs['calc'] == 'Переработка: 7,7 ч',
              fs['calc'])
        shot(page, 'f-roundtrip-prefill.png')
        # закрыть форму без применения (Назад) — F проверяет только префилл
        page.click('#wsCellPopup .ws-dn-back')
        page.wait_for_timeout(200)
        page.mouse.click(10, 10)
        page.wait_for_timeout(400)

        # ===== G: «Сохранить» → payload с временами =====
        print('== G: Сохранить → payload setManualEntry ==')
        before = len(SAVED)
        page.click('#wsSaveBtn')
        page.wait_for_timeout(1500)
        news = SAVED[before:]
        gd = [b for b in news if b.get('date') == D5]
        gn = [b for b in news if b.get('date') == D6]
        check('G: два запроса (д + н)', len(news) == 2, news)
        check('G: «д» payload: часы 7,2 + времена',
              gd and gd[0].get('часы') == 7.2 and
              gd[0].get('время_начала') == '08:00' and
              gd[0].get('время_окончания') == '15:12', gd)
        check('G: «н» payload: часы 12 + времена',
              gn and gn[0].get('часы') == 12 and
              gn[0].get('время_начала') == '19:30' and
              gn[0].get('время_окончания') == '07:30', gn)
        shot(page, 'g-saved-toast.png')

        # ===== H: сменный — тишина =====
        print('== H: ховер сменный «д» — тишина ==')
        check('H: ячейка помечена', mark_cell(page, '017', DAY4))
        page.hover('[data-testid="hc"]')
        page.wait_for_timeout(300)
        st = events_popup_state(page)
        check('H: окно НЕ открылось', not st['win'], st)
        close_hover_window(page)

        # ===== I: JS-ошибки =====
        check('I: 0 JS-ошибок', not js_errors, js_errors[:3])

        browser.close()

    print()
    print('ИТОГ: %d/%d (failed %d)' % (PASS, PASS + FAIL, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
