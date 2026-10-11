#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 501: обновление системного промта kip8test (post-501; перенос
# в kip8 ВЫПОЛНЕН командой заявки — оба репо синхронны).
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

LINE3 = ('> **Версия документа:** 2026-10-11 (post-Task 501 — '
         '«ЭЛЕКТРОТЕХНИКА»/«ГЕОМЕТРИЯ» В ЕДИНОМ СТИЛЕ ПАНЕЛЕЙ + '
         '«ШКАЛА-СИГНАЛ»: ПОДСКАЗКА УБРАНА, БЛОК ПРОИЗВОЛЬНЫХ ЗНАЧЕНИЙ '
         'НАД ПАНЕЛЬЮ ШКАЛЫ + ТЁПЛАЯ СВЕТЛАЯ ТЕМА ДАТЧИКОВ ТЕМПЕРАТУРЫ '
         '— заявка: «Разделы электротехника и геометрия сделай в таком '
         'же стиле. В разделе шкала-сигнал убери текст "Линейная: '
         'прямая зависимость · Квадратичная: сигнал ∝ (шкала)² · '
         'Корнеизвлекающая: сигнал ∝ √(шкала)" под полем выбора типа '
         'шкалы, а блок расчёта произвольных значений размести над '
         'блоком для расчёта шкалы с эффектом выступа. Политру кнопок '
         'и блоков в разделе датчиков температур в светлой теме '
         'адаптируй под цвета светлой темы. И сразу перенеси все '
         'изменения в kip8.»; выкачан в kip8test @a01352ef (v725, '
         '6346/0 = 6320+26, browser-check 32/32 (порт 8986) + VLM ×10) '
         'и ПЕРЕНЕСЁН вместе с Task 500 в боевой kip8 @cd457ac ОДНИМ '
         'инкрементом SW kipia-v523→v524 (команда «сразу перенеси» в '
         'заявке; тесты kip8 6350/0, SMOKE 26/26 + VLM ×4; регламент '
         '441); КЛИЕНТ-ONLY. СОСТАВ: (1) ЭЛЕКТРОТЕХНИКА: 8 блоков → '
         'ОДНА панель #cbFormPanel (ts-calc-panel ts-calc-inset, стиль '
         'Task 500), 7 разделителей, кнопка вне; id cb_power_block/'
         'cb_current_block — на внутренних обёртках (JS-тумблеры); '
         '(2) ГЕОМЕТРИЯ: кольцо/цилиндр верт./горизонт./конус → '
         '#grFormPanel/#gcyFormPanel/#ghFormPanel/#gcoFormPanel, круг/'
         'сфера — классы одиночным блокам; (3) ШКАЛА-СИГНАЛ: подсказка '
         'удалена, #scaleQueryPanel — НАД #scaleFormPanel (выступ, '
         'как ППР датчиков температуры), #scaleCustomCalcPanel удалён, '
         'updateScaleQueryUnits — живые единицы; (4) СВЕТЛАЯ ТЕМА '
         'датчиков температуры — политура ТЁПЛАЯ (акцент светлой темы '
         '#C6613F/rgba(198,97,63), тени #9E4E30, нейтральные рамки '
         'полей): панели/фокус/cs-триггеры/табы/звёзды/featured/'
         'разделители — общая тёплая палитра для всех панелей стиля '
         'Task 500; тёмная не тронута. УРОКИ: разделитель — КЛАСС '
         'label, НЕ атрибут (строчные счётные ассерты зелёные при '
         'битом CSS — тестировать class="…ts-calc-sep"); ТЕМА в '
         'Playwright — localStorage kip8test:app-theme ДО загрузки '
         '(html data-theme=light по умолчанию — «тёмные» кадры '
         'снимались светлыми); VLM-скорер — markdown-звёздочки '
         'сносить до проверки «да»; вопросы БЕЗ инверсии (правильный '
         '«нет» карался); full_page-кадры; перенос index.html копией '
         'с репо-патчем (диф = только localStorage-ключи). '
         'SW kipia-test-v724 → v725. ТЕСТЫ 6346/0 (+26 test-task501.js: '
         'A CB, B гео ×6, C шкала-сигнал, D тёплая светлая тема, E VM '
         'updateScaleQueryUnits, F SW v725; адаптации 491/492/494/495 '
         'light-литералы + 471/472/500 окна; бамп ассерты v724→v725 '
         '×641 / гарды v725→v726 ×156). Browser-check 32/32. VLM ×10. '
         'DEPLOY-Task501-electro-geo-uniform-style.md.')

CUR_T = '> **Версия документа:** 2026-10-11 (post-Task 500 —'

src = io.open(PT, encoding='utf-8').read()
i3 = src.index('> **Версия документа:**')
i3end = src.index('\n', i3)
old_line3 = src[i3:i3end]
PREV_MARK = '> **Версия документа (предыдущая):**'
if src.count(PREV_MARK) > 2:
    iprev = src.rindex(PREV_MARK)
    iprev_end = src.index('\n', iprev)
    src = src[:iprev] + src[iprev_end + 1:]
new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
src = src[:i3] + LINE3 + '\n' + new_prev + src[i3end:]
io.open(PT, 'w', encoding='utf-8').write(src)
print('%s: строка 3 обновлена (post-501)' % PT)

src = io.open(PT, encoding='utf-8').read()
repsT = [
    ('> **Текущая версия кэша:** `kipia-test-v724`',
     '> **Текущая версия кэша:** `kipia-test-v725`'),
    ('Формат: `kipia-test-v725` → `kipia-test-v726` (для kip8test) или '
     '`kipia-v524` → `kipia-v525` (для kip8)',
     'Формат: `kipia-test-v725` → `kipia-test-v726` (для kip8test) или '
     '`kipia-v525` → `kipia-v526` (для kip8)'),
    ('`kipia-v524` → `kipia-v525` (для kip8)',
     '`kipia-v525` → `kipia-v526` (для kip8)'),
    ('# Ожидается: 6320 passed, 0 failed (kip8test; в kip8 — 6258 passed, '
     '0 failed — Task 500 НЕ перенесён, ждёт команды; после переноса '
     'kip8 = 6324 одним инкрементом kipia-v523→v524)',
     '# Ожидается: 6346 passed, 0 failed (kip8test; в kip8 — 6350 '
     'passed, 0 failed — Tasks 500+501 ПЕРЕНЕСЕНЫ одним инкрементом '
     'kipia-v523→v524, оба репо синхронны)'),
    ('(`tests/`, 6320 тестов, 203 тест-файла, `node tests/run-all.js`)',
     '(`tests/`, 6346 тестов, 204 тест-файла, `node tests/run-all.js`)'),
]
n = 0
for old, new in repsT:
    if old in src:
        src = src.replace(old, new, 1)
        n += 1
    else:
        print('  [MISS] %r' % old[:60])
# строка состояния — теперь оба синхронны
i = src.find('ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @')
if i != -1:
    j = src.find('\n', i)
    new_state = ('ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @a01352ef, SW '
                 '`kipia-test-v725` (guard v726), тесты 6346/0; kip8 '
                 '@cd457ac, SW `kipia-v524` (guard v525), тесты '
                 '6350/0 — ОБА репо синхронны (Tasks 500+501 в обоих); '
                 'десктопы — CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 502.')
    src = src[:i] + new_state + src[j:]
    n += 1
io.open(PT, 'w', encoding='utf-8').write(src)
print('kip8test: скаляры обновлены (%d)' % n)
