#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 474: обновление системного промта (post-474) — карточка
# прибора КИП ИОС: текст Типа ×1.5 (12→18px) + «№ прибора»/
# «Место установки» ниже от верха карточки; SW v697→v698;
# тесты 5461/0.
import io
import sys

PATH = 'Системный_промт_для_приложения_КИПиА.md'
with io.open(PATH, encoding='utf-8') as f:
    src = f.read()

CUR_MARK = '> **Версия документа:** 2026-10-04 (post-Task 473; заявка: «В разделе Графики КИП ИОС'
PREV_MARK = '> **Версия документа (предыдущая):**'

NEW_LINE3 = '> **Версия документа:** 2026-10-04 (post-Task 474; заявка: «В разделе КИП ИОС, в подробной карточке прибора размер текста типа прибора, расположенного перед картинкой прибора, сделай в полтора раза больше. И текст "№ прибора" и "Место установки" смести немного ниже от верхней границы карточки. Перенеси изменения в боевой kip8.»): подробная карточка прибора (devRenderDetail — рендер один для десктоп-панели #detailPanel и мобильной #page-device-detail) — ТОЛЬКО CSS, index.html. (а) ТЕКСТ ТИПА ПРИБОРА — оверлей .dev-detail-type-overlay в нижней части картинки, поверх неё («перед картинкой прибора», Task 334): font-size 12px → 18px — РОВНО в полтора раза (12 × 1.5 = 18); вес 600/переносы не тронуты; светлая тема размер не переопределяет. (б) «№ прибора» и «Место установки» — блок .dev-detail-meta справа от картинки: padding-top 2px → 12px — оба блока смещены немного ниже от верхней границы карточки; десктопное правило #detailPanel .dev-detail-meta задаёт только padding-left/right 14px — смещение действует и в панели. Структура карточки/липкий верх (Task 334/335/336) НЕ менялись. SW kipia-test-v697→v698 + сжатый комментарий Task 474 (3 строки; якорь «ВСЕГДА на одном уровне»). Тесты 5461/0 (+25 к 5436): НОВЫЙ test-task474.js ×25 (Тип ×1.5 ×7: 18px, отсутствие 12px, светлая не переопределяет; мета-блок ×6: 12px, десктоп не сбрасывает padding-top; структура карточки ×6: порядок блоков/условие if (type)/метки; SW ×6: v698 + негатив v697 + guard v699 + окна якорей); бамп ассертов v697→v698 (533) + guards v698→v699 (123) — task474-bump-sw.py, 158 файлов, OWN исключён; окна истории версий sw.js (прецедент Task 471/473): test-task461 3600→3800 (Task 461 ~3719), test-task471 + test-task472 (контекст Task 471) 1020→1300 (~1157). Браузер task474-browser-check.py 22/22 (порт 8995, мок Apps Script, прибор ID 1 «Счетчик воды турбинный» Тип «"Пульсар" ТХ»: computed font-size 18px ×3 контекста, label1Shift ~12px, оверлей в пределах картинки у нижней грани, значок избранного виден, 0 JS ×3). VLM ×3 (тёмная/светлая/мобайл 375: Тип крупный и читаемый, подписи с отступом, дефектов нет). DEPLOY НЕ ТРЕБУЕТСЯ (статический ассет — SW-бамп; десктопы — CI-автосинк). ПЕРЕНОС В kip8: заявка СОДЕРЖИТ команду «Перенеси изменения в боевой kip8» — ПАРТИЯ Tasks 473+474 одним инкрементом kipia-v508→v509 (473 ждал переноса по команде — команда получена в заявке 474; регламент Task 441); перенос выполняется следующим шагом этой сессии. ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test SW `kipia-test-v698` (guard v699), тесты 5461/0; kip8 SW `kipia-v508` (guard v509), тесты 5399/0 — ДО переноса партии. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 475 (в обоих репо).'

if CUR_MARK not in src:
    print('ОШИБКА: не найдена строка версии post-473')
    sys.exit(1)

n_prev_before = src.count(PREV_MARK)

i3 = src.index(CUR_MARK)
i3end = src.index('\n', i3)
old_line3 = src[i3:i3end]

# (а) удалить самую старую строку «предыдущая» (храним 2 последних)
if src.count(PREV_MARK) > 2:
    iprev = src.rindex(PREV_MARK)
    iprev_end = src.index('\n', iprev)
    src = src[:iprev] + src[iprev_end + 1:]

# (б) строка 3 → новая версия + «предыдущая» из старой строки 3
new_prev = PREV_MARK + ' ' + old_line3[len('> **Версия документа:** '):]
src = src[:i3] + NEW_LINE3 + '\n' + new_prev + src[i3end:]

# (в) «Текущая версия кэша» v697 → v698
old_cache = '> **Текущая версия кэша:** `kipia-test-v697`'
new_cache = '> **Текущая версия кэша:** `kipia-test-v698`'
if old_cache not in src:
    print('ОШИБКА: не найдена строка текущей версии кэша')
    sys.exit(1)
src = src.replace(old_cache, new_cache, 1)

# (г) строка «Инкрементируй» — следующие версии
old_inc = 'Формат: `kipia-test-v697` → `kipia-test-v698` (для kip8test) или `kipia-v508` → `kipia-v509` (для kip8)'
new_inc = 'Формат: `kipia-test-v698` → `kipia-test-v699` (для kip8test) или `kipia-v509` → `kipia-v510` (для kip8)'
if old_inc not in src:
    print('ОШИБКА: не найдена строка «Инкрементируй»')
    sys.exit(1)
src = src.replace(old_inc, new_inc, 1)

# (д) ожидание тестов kip8test 5436 → 5461
old_exp = '# Ожидается: 5436 passed, 0 failed (kip8test; в kip8 — 5399 passed, 0 failed)'
new_exp = '# Ожидается: 5461 passed, 0 failed (kip8test; в kip8 — 5399 passed, 0 failed)'
if old_exp not in src:
    print('ОШИБКА: не найдена строка ожидания тестов')
    sys.exit(1)
src = src.replace(old_exp, new_exp, 1)

# проверки
checks = [
    ('post-Task 474', 1),
    ('Версия документа (предыдущая):** 2026-10-04 (post-Task 473; заявка: «В разделе Графики КИП ИОС', 1),
    ('5461 passed, 0 failed (kip8test', 1),
    ('kipia-test-v698', None),
    ('СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 475', 1),
    ('padding-top 2px → 12px', None),
]
for marker, cnt in checks:
    c = src.count(marker)
    if cnt is not None and c != cnt:
        print('ОШИБКА: маркер %r найден %d раз (ожидалось %s)' % (marker[:60], c, cnt))
        sys.exit(1)
    if cnt is None and c == 0:
        print('ОШИБКА: маркер не найден: %r' % marker[:60])
        sys.exit(1)
if src.count(PREV_MARK) != n_prev_before:
    print('ОШИБКА: длина цепочки «предыдущих» изменилась (%d → %d)' %
          (n_prev_before, src.count(PREV_MARK)))
    sys.exit(1)

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(src)
print('промт: post-474 записан (кэш v698, тесты 5461/0, следующий 475)')
