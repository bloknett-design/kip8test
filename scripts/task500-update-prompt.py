#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 500: обновление системного промта kip8test (post-500, перенос
# в kip8 НЕ выполнялся — команды в заявке не было; ждём «перенеси»).
# kip8test: кэш v724, формат v724→v725, ожидание 6320/6258, факт 6320.
import io
import os
import sys
import unicodedata

PT = None
for f in os.listdir('.'):
    if f.endswith('.md'):
        if unicodedata.normalize('NFC', f).startswith('Системный_промт'):
            PT = f
            break
assert PT, 'файл системного промта не найден'

LINE3 = ('> **Версия документа:** 2026-10-11 (post-Task 500 — «КИП И А»: '
         'ЕДИНЫЙ СТИЛЬ ПАНЕЛЕЙ ВВОДА ВСЕХ РАЗДЕЛОВ + ОБЪЕДИНЕНИЕ БЛОКОВ '
         'В «ШКАЛА-СИГНАЛ»/«БУЙКОВЫЙ УРОВНЕМЕР»/«СУЖАЮЩЕЕ УСТРОЙСТВО» — '
         'заявка: «Примени стиль отображения для всех разделов КИП и А, '
         'в разделах шкала-сигнал, буйковый уровнемер и сужающее '
         'устройство объедини блоки с полями ввода в один блок.»; '
         'реализовано ТОЛЬКО в kip8test, переноса в kip8 НЕ БЫЛО — '
         'команды в заявке не было, ждём (в kip8 ждёт Task 500 одним '
         'инкрементом kipia-v523→v524); КЛИЕНТ-ONLY). СУТЬ (стиль — по '
         'образцу «Датчиков температуры», Tasks 494-499): (1) ОБЪЕДИНЕНИЕ '
         'блоков ввода в ОДНУ панель ts-calc-panel ts-calc-inset '
         '(«колодец»): scale-signal 3 блока → #scaleFormPanel, '
         'buoy-calc 4 → #buoyFormPanel, orifice-quick 5 / orifice-dp 7 / '
         'orifice-flow 7 / orifice-diameter 7 → #orifice…FormPanel; '
         'обёртки .scale-form в col-input сняты (содержимое — поля, '
         'селекты, скрытые JS-переключатели scaleCustomRange / '
         'op_*_gas_params — дословно; кнопки расчёта ВНЕ панелей; '
         'бывшие группы разделены линией ts-calc-sep — border-top 1px '
         'rgba(74,143,199,0.3), отступы 14px, светлая 0.35); (2) СТИЛЬ '
         'без объединения: конвертер 8 страниц — converter-form + классы '
         'панелей; погрешность 11 страниц — scale-form + классы '
         '(error-scale все 7 с сохранением id/inline; error-kit '
         'kit-dev-form-динамика НЕ тронута); (3) панели «Расчёт '
         'произвольных значений» scale-signal/buoy — #scaleQueryPanel/'
         '#buoyQueryPanel ts-calc-panel БЕЗ inset (ВЫСТУП, как ППР); '
         '(4) ПОЛЯ в панелях — крупный вид 52/19/700 селекторами по '
         'тегам .ts-calc-panel input/select.scale-field|.form-field '
         '(спан-бейджи единиц НЕ тронуты) + КАСТОМНЫЕ СЕЛЕКТЫ: нативные '
         'select скрыты cs-wrapper — видимый .cs-trigger в панелях '
         'стилизован тем же видом (иначе мелкие 42/14 рядом с полями), '
         '.cs-wrapper margin-bottom 14px; (5) отступ панелей в col-input '
         '8px 0 12px (сильнее нуля Task 179). ПОДВОДНЫЕ КАМЕНИ: '
         'HTML-комментарии панелей НЕ должны содержать литералы '
         'ts-calc-inset/ts-calc-sep/scale-form (счётные ассерты — урок '
         '499); кавычки [data-theme="light"] в bash-heredoc теряются — '
         'правки CSS через Edit/скрипт-файл, не через -c; dict PLANS в '
         'windows-скриптах НЕ терпит дублей ключей (поздняя запись '
         'затирает раннюю — 3 итерации окон); Chromium нормализует '
         'box-shadow (inset в КОНЦЕ каждой тени, цвет впереди) и '
         'резолвит localhost в IPv6 (127.0.0.1 в URL); querySelector '
         '.conv-col-input без скоупа активной страницы ловит ЧУЖУЮ '
         'колонку. SW kipia-test-v723 → v724. ТЕСТЫ kip8test 6320/0 '
         '(+66): НОВЫЙ test-task500.js (SRC: панели/разделители/кнопки/'
         'поля/скрытые блоки, query-панели, классы 19 страниц, CSS '
         'включая cs-trigger, div-баланс, SW v724+комментарий); окна '
         'истории sw.js — 58 литералов (461 14000→15000, 473 '
         '10600→11500, 478/479/481/482 8900→9600/8300→9100/7800→8800, '
         '483-488/493-497/499, dist-формы 474/476/477/478/479/481/482 '
         '10400→11200/10800→12000/11200→12400/14000→15000) + '
         'синхро-литералы «окон ЧУЖИХ тестов» (475 §9, 481, 482, 486); '
         'бамп ассерты v723→v724 ×638 / гарды v724→v725 ×155 (184 '
         'файла). Browser-check task500-browser-check.py 56/56 (порт '
         '8986): мобайл 375 тёмная/светлая + десктоп 1280 — ОДНА панель '
         'в col-input, «колодец» 1px/inset-тени, поля и cs-trigger '
         '52/19/700, разделители, живой расчёт шкала-сигнал/буйка/'
         'диафрагмы, переключатели «Своё значение»/«Газ» ЧЕРЕЗ UI '
         'кастомного дропдауна (клик триггера → опция), регрессия '
         'temp-sensor-view; 0 JS ×3. VLM ×11 (full_page-кадры высоких '
         'панелей; разделители 0.3 заметны; кнопки ниже кадра — вопрос '
         'из промпта снят). DEPLOY-Task500-kipa-uniform-panel-style.md.')

CUR_T = '> **Версия документа:** 2026-10-11 (post-Task 499 — «ДАТЧИКИ ТЕМПЕРАТУРЫ»'
PREV_MARK = '> **Версия документа (предыдущая):**'


def update(path, cur_mark, tail):
    src = io.open(path, encoding='utf-8').read()
    if cur_mark not in src:
        print('ОШИБКА: не найдена строка версии в %s' % path)
        sys.exit(1)

    # (а) удалить самую старую «предыдущую» (ПОСЛЕДНЯЯ по позиции)
    if src.count(PREV_MARK) > 2:
        iprev = src.rindex(PREV_MARK)
        iprev_end = src.index('\n', iprev)
        src = src[:iprev] + src[iprev_end + 1:]

    i3 = src.index(cur_mark)
    i3end = src.index('\n', i3)
    old_line3 = src[i3:i3end]
    new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
    src = src[:i3] + LINE3 + tail + '\n' + new_prev + src[i3end:]
    io.open(path, 'w', encoding='utf-8').write(src)
    print('%s: строка 3 обновлена (post-500)' % path)


FEAT = sys.argv[1] if len(sys.argv) > 1 else '<feat500>'
update(PT, CUR_T,
       ' ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @' + FEAT + ', SW `kipia-test-v724` '
       '(guard v725), тесты 6320/0; kip8 @9ceb354, SW `kipia-v523` '
       '(guard v524), тесты 6258/0 — Task 500 ЖДЁТ ПЕРЕНОСА в kip8 ПО '
       'КОМАНДЕ (одним инкрементом kipia-v523→v524, маппинг '
       'kipia-test-v724→v524 / v725→v525, окна kip8-геометрии); '
       'десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 501.')

src = io.open(PT, encoding='utf-8').read()
repsT = [
    ('> **Текущая версия кэша:** `kipia-test-v723`',
     '> **Текущая версия кэша:** `kipia-test-v724`'),
    ('Формат: `kipia-test-v723` → `kipia-test-v724` (для kip8test) или '
     '`kipia-v523` → `kipia-v524` (для kip8)',
     'Формат: `kipia-test-v724` → `kipia-test-v725` (для kip8test) или '
     '`kipia-v524` → `kipia-v525` (для kip8)'),
    ('# Ожидается: 6198 passed, 0 failed (kip8test; в kip8 — 6202 passed, '
     '0 failed — Task 497 ПЕРЕНЕСЁН одним инкрементом kipia-v520→v521)',
     '# Ожидается: 6320 passed, 0 failed (kip8test; в kip8 — 6258 passed, '
     '0 failed — Task 500 НЕ перенесён, ждёт команды; после переноса '
     'kip8 = 6324 одним инкрементом kipia-v523→v524)'),
    ('(`tests/`, 6146 тестов, 202 тест-файла, `node tests/run-all.js`)',
     '(`tests/`, 6320 тестов, 203 тест-файла, `node tests/run-all.js`)'),
]
n = 0
for old, new in repsT:
    if old in src:
        src = src.replace(old, new, 1)
        n += 1
    else:
        print('  [MISS] %r' % old[:60])
io.open(PT, 'w', encoding='utf-8').write(src)
print('kip8test: скаляры обновлены (%d/%d)' % (n, len(repsT)))
