#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 494: обновление системного промта kip8test (post-494, перенос
# в kip8 выполняется СРАЗУ по команде из заявки «Сразу вноси изменения
# и в kip8» — зеркальная отметка появится в записи переноса kip8).
# kip8test: кэш v718, формат v718→v719, ожидание 6146/6138, факт 6146.
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

LINE3 = ('> **Версия документа:** 2026-10-10 (post-Task 494: '
         '«ДАТЧИКИ ТЕМПЕРАТУРЫ» — ПАНЕЛЬ ПРОИЗВОЛЬНОГО РАСЧЁТА БЕЗ '
         'ЗАГОЛОВКА/ПОДСКАЗКИ, ЭФФЕКТ ВЫСТУПА, ПОЛЯ КРУПНЕЕ И ЯРЧЕ — '
         'заявка: «На страницах расчёта датчиков температуры убери '
         'надписи "Расчёт произвольных значений Введите значение в '
         'любое поле — другое рассчитается автоматически", а шрифт, '
         'размер полей ввода в этом блоке сделай больше и ярче, и сам '
         'блок сделай в стиле эффект выступа (рамка 2px + градиент + '
         'тень). Сразу вноси изменения и в kip8»; перенос в kip8 '
         'выполняется СРАЗУ (команда в заявке), одним инкрементом '
         'kipia-v517→v518; КЛИЕНТ-ONLY). СУТЬ: панель '
         '#tempCustomCalcPanel (.ts-calc-panel, Task 371/373 — '
         'статичная НАД формой выбора на page-temp-sensor-view, '
         'единая для ТС и ТП): (а) УДАЛЕНЫ div.ts-calc-title '
         '(«Расчёт произвольных значений») и div.ts-calc-hint '
         '(«Введите значение в любое поле…»), CSS-правила сняты; '
         '(б) блок — эффект ВЫСТУПА по образцу featured Task 492: '
         'border 2px rgba(74,143,199,0.85) + градиент '
         'linear-gradient(180deg, 0.2→0.05) ПОВЕРХ background-color '
         'var(--card-bg) (раздельные свойства, НЕ shorthand) + тень '
         '0 5px 14px / inset 0 1px 0 / inset 0 -3px; светлая — рамка '
         '43,111,163, тень 21,54,83 0.22; (в) поля (оба, класс '
         'ts-calc-field) — 52px/19px/700/#ffffff, рамка 0.45, '
         'плейсхолдер 0.4, :focus рамка 0.85+свечение; светлая — '
         '#141413 на белом 0.75; подписи .scale-form-label в панели '
         'ярче (0.6/12px); (г) ПОДВОДНЫЙ КАМЕНЬ: мобильные @media '
         '(max-width: 480px/400px) ужимают .form-field/.scale-field '
         'до 14/13px и 40/38px ПОЗЖЕ основного правила (каскад, '
         'равная специфичность) — override-ы .ts-calc-field { '
         'padding: 10px 14px; font-size: 19px; height: 52px; } '
         'ПОСЛЕ общих правил в ОБОИХ media-блоках; (д) подписи полей '
         'под тип датчика (openTempSensor: Сопротивление R(t), Ом ↔ '
         'Термо-ЭДС E(t), мВ) и живой расчёт — НЕ менялись. SW '
         'kipia-test-v717 → v718 (логика SW НЕ менялась). ТЕСТЫ '
         'kip8test 6146/0 (+12): НОВЫЙ test-task494.js 12 (SRC-HTML '
         '×4, SRC-CSS ×5 — в т.ч. media-override ×2 по вхождениям '
         '(первый @media-400px в файле НЕ наш — вхождений много!), '
         'VM ×1, SW ×2); АДАПТАЦИИ: 371 (список панели минус '
         'заголовок/подсказка + два НЕ-ассерта), 373 (подсказка → '
         'НЕ-ассерт); бамп task494-bump-sw.py (OWN исключён): guards '
         'v718→v719 ×147, затем ассерты v717→v718 ×610; ОКНА истории '
         'sw.js (scripts/task494-windows.py): якорь 472 ~9105 — окно '
         '9100→9400 в 476/477/478/479/481/482. Browser-check '
         'task494-browser-check.py 20/20 (порт 8982): мобайл 375 '
         'тёмная 50М — заголовка/подсказки НЕТ, 2px/градиент/inset-'
         'тень, поля 19px/52px/700/белый, живой расчёт t=55→R(t) '
         '61,77; ТП tc_K (КАМЕНЬ: ключ ТП в каталоге \'tc_\'+буква, '
         'НЕ буква) — подпись Термо-ЭДС, t=300→E(t) 12,2086; светлая '
         '— рамка 43,111,163/мягкая тень; десктоп — стилизовано (CSS '
         'вне media); 0 JS ×3. VLM ×4: все — заголовка НЕТ, панель '
         'приподнятая, поля крупные (КАМЕНЬ VLM-скрипта: модель '
         'цитирует фразу вопроса в ответе «Нет, …» — оценка по '
         'пункту (1) «^нет», НЕ по вхождению фразы).')

CUR_T = '> **Версия документа:** 2026-10-10 (post-Task 493 ПЕРЕНОС-зеркало:'
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
    print('%s: строка 3 обновлена (post-494)' % path)


# --- kip8test ---
FEAT = sys.argv[1] if len(sys.argv) > 1 else '<feat494>'
update(PT, CUR_T,
       ' ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @' + FEAT + ', SW `kipia-test-v718` '
       '(guard v719), тесты 6146/0; kip8 @296a0bb, SW `kipia-v517` '
       '(guard v518), тесты 6138/0 — Task 494 переносится в kip8 СРАЗУ '
       'по команде из заявки одним инкрементом kipia-v517→v518 '
       '(см. зеркальную запись в worklog kip8); десктопы — '
       'CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 495.')

src = io.open(PT, encoding='utf-8').read()
repsT = [
    ('> **Текущая версия кэша:** `kipia-test-v717`',
     '> **Текущая версия кэша:** `kipia-test-v718`'),
    ('Формат: `kipia-test-v717` → `kipia-test-v718` (для kip8test) или '
     '`kipia-v516` → `kipia-v517` (для kip8)',
     'Формат: `kipia-test-v718` → `kipia-test-v719` (для kip8test) или '
     '`kipia-v517` → `kipia-v518` (для kip8)'),
    ('# Ожидается: 6134 passed, 0 failed (kip8test; в kip8 — 6138 passed, '
     '0 failed — Task 493 ПЕРЕНЕСЁН в kip8 одним инкрементом '
     'kipia-v516→v517)',
     '# Ожидается: 6146 passed, 0 failed (kip8test; в kip8 — 6138 passed, '
     '0 failed +12 после переноса Task 494 = 6150, одним инкрементом '
     'kipia-v517→v518)'),
    ('(`tests/`, 6134 тестов, 201 тест-файл, `node tests/run-all.js`)',
     '(`tests/`, 6146 тестов, 202 тест-файла, `node tests/run-all.js`)'),
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
