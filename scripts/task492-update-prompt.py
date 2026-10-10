#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 492: обновление системного промта kip8test (post-492, БЕЗ
# переноса — команды «перенеси в kip8» в заявке НЕ было; в kip8
# ждут переноса Task 490, 491 И 492 одним инкрементом v515→v516).
# kip8test: кэш v716, формат v716→v717, ожидание 6124/6069,
# факт 6124.
# Имя файла промта ищется через os.listdir (юникод-нормализация
# имени в разных сессиях bash плавает; историческая опечатка —
# «Системный_промт…» с одной «п»).
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

LINE3 = ('> **Версия документа:** 2026-10-10 (post-Task 492: '
         '«ДАТЧИКИ ТЕМПЕРАТУРЫ» — НИЖНИЙ БАР «ВСЕ/ИЗБРАННЫЕ», '
         'ЕДИНЫЙ КРУПНЫЙ ШРИФТ, FEATURED-ВЫСТУП У ИЗБРАННОГО — '
         'заявка: «В разделе датчиков температур кнопки все и '
         'избранные смести вниз и оформи как в разделе расходомеров. '
         'Оформление кнопок верни как прежде но шрифт текста оставь '
         'как есть и сделай такой же на остальных кнопках, и '
         'оформление кнопок добавленных в избранное сделай как сейчас '
         'выделенным»; реализовано ТОЛЬКО в kip8test, переноса в kip8 '
         'НЕ БЫЛО — команды в заявке не было, ждём (в kip8 ждут '
         '490+491+492 одним инкрементом kipia-v515→v516); КЛИЕНТ-'
         'ONLY). СУТЬ: (а) НИЖНИЙ БАР #tsBottomBar (.ts-bottom-bar, '
         'сиблинг #page-temp-sensors как #flowBottomBar) — точная '
         'геометрия flow-bottom-bar: fixed внизу, z-80, grid 1fr 1fr, '
         'var(--bottom-nav-bg) + blur(20px), border-top, safe-area, '
         'разделитель ::before 1px (синий/светл.); показ body:has('
         '#page-temp-sensors.active) { display: grid; }, десктоп '
         '≥1024px — display: none !important (там прежние .ts-tabs '
         'сверху, на мобильном ≤1023px скрыты display:none, .ts-page '
         'padding-bottom 96px); кнопки — стиль flow-tab: 17px/600, '
         'min-height 56px, active только цвет (без фона), счётчик '
         '18px/11px, ≤400px 15px; синхронизация автоматическая — '
         'setTempSensorsTab переключает ВСЕ .ts-tab[data-ts-tab] '
         '(верх+низ), счётчики-дубликаты tsAllCountMob/tsFavCountMob '
         'в renderTempSensorCards при каждом рендере; (б) крупный '
         'шрифт Task 491 (имя 19px/meta 12px, ≤400px 17px) перенесён '
         'в БАЗОВЫЕ правила .ts-card-name/.ts-card-meta мобильного '
         'блока — у ВСЕХ кнопок; правила «.ts-card-feat имя/meta» и '
         '≤400px-feat-строка УДАЛЕНЫ; meta 10.5px на ≤400px удалена '
         '(12px наследуется); (в) renderTempSensorCards: feat=isFav — '
         'класс ts-card-feat (рамка 2px, градиент, эффект выступа, '
         '«утапливание» при :active, светлая тема — CSS Task 491 БЕЗ '
         'изменений, только ≤1023px) вешается на КНОПКИ В ИЗБРАННОМ, '
         'в режиме «Избранные» выделены все показанные; популярные '
         'градуировки 50М/100М/ТХА (K)/ТХК (L) — ПРЕЖНЕЕ оформление '
         '(условия Task 491 удалены), автотаб «Избранного» (Task 491) '
         'и пары каталога — НЕ тронуты. SW kipia-test-v715 → v716 '
         '(логика SW НЕ менялась). ТЕСТЫ kip8test 6124/0 (+27): '
         'НОВЫЙ test-task492.js 27 (SRC: HTML бара ×4 — сиблинг/'
         'кнопки/счётчики/комментарий, CSS бара ×7 — fixed/grid/blur/'
         'safe-area/показ/десктоп-hidden/разделитель/кнопки/счётчик/'
         '≤400px/скрытие ts-tabs+отступ, CSS шрифт+feat ×4, JS ×3 — '
         'feat=isFav/счётчики×2/setTempSensorsTab; VM ×5 — без '
         'избранного 0 feat, избранное ТС+ТП feat ровно на них, '
         '«Избранные» все featured, счётчики Mob, снятие избранного; '
         'SW ×3); АДАПТАЦИИ: 490 (≤400px-строка без feat/meta-10.5), '
         '491 (шапка-ADAPTATION, B: базовые 19/12 вместо feat-правил, '
         'C: feat=isFav + счётчики Mob, E VM: 0 feat без избранного/ '
         'fav=featured, ≤400px-строка); 323 (якорь @media от '
         '.ws-tt-drawer назад — @media ts-bottom-bar стало первым в '
         'файле, regex захватывал width:50% из чужих правил); бамп '
         'task492-bump-sw.py (guards v716→v717 ×146, затем ассерты '
         'v715→v716 ×604, 176 файлов); ОКНА истории sw.js (комментарий '
         '492 ~290 симв. сместил якоря, scripts/task492-windows.py): '
         '461 11600→12400, 472 8500→9300, 473 8200→9000, 474 9000→'
         '9800 и 11600→12400, 480 6000→6800, 481 w700 6000→6800, 482 '
         '6000→6800; каскады 475/481/482/486 синхронизированы. '
         'Browser-check task492-browser-check.py 35/35 (порт 8976): '
         'мобайл 375 тёмная — бар ВИДЕН (grid/fixed/bottom-0/z-80/2 '
         'равные кнопки/счётчики 17:0/прижат к низу/.ts-page 96px), '
         'верхние .ts-tabs скрыты, пары живы; БЕЗ избранного 0 feat, '
         'у ВСЕХ 17px/1px/без тени; клики по кнопкам БАРА; уход со '
         'страницы — бар скрыт; звезда → СРАЗУ feat 2px/тень/градиент '
         '+ счётчик 1; reload → автотаб «Избранные» (кнопка бара '
         'active); «Все» через бар — feat только у избранного; '
         'светлая — палитра света + зазор; десктоп 1280 — бар СКРЫТ, '
         '.ts-tabs ВИДНЫ, feat в DOM при 1px; 0 JS-ошибок. VLM ×4 '
         '(CLI z-ai vision): бар внизу/кнопки равные/верхних нет; '
         'ровно одна карточка выделена («выступает»), звезда, шрифт '
         'одинаковый; светлая читаема; десктоп — переключатель ВВЕРХУ, '
         'бара нет. ПОДВОДНЫЕ КАМНИ: посев localStorage в kip8test — '
         'ТОЛЬКО с префиксом kip8test: (изоляция isolateLocalStorage); '
         'page.click оставляет мышь над карточкой → :hover '
         '(специфичность 0,2,0) перекрывает градиент feat (0,1,0) — '
         'отводить мышь перед computed-проверками; на десктопе с '
         'посеянным избранным автотаб открывает «Избранные» — для '
         'проверки порядка каталога сперва setTempSensorsTab(\'all\').')

CUR_T = '> **Версия документа:** 2026-10-10 (post-Task 491:'
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
    print('%s: строка 3 обновлена (post-492)' % path)


# --- kip8test ---
FEAT = sys.argv[1] if len(sys.argv) > 1 else '<feat492>'
update(PT, CUR_T,
       ' ТЕКУЩЕЕ СОСТОЯНИЕ: kip8test @' + FEAT + ', SW `kipia-test-v716` '
       '(guard v717), тесты 6124/0; kip8 @ddd7878 (авто-коммиты Google '
       'Sheets поверх), SW `kipia-v515` (guard v516), тесты 6069/0 — '
       'Tasks 490, 491 И 492 в kip8 ОТСУТСТВУЮТ (перенос ПО КОМАНДЕ '
       'пользователя одним инкрементом kipia-v515→v516); десктопы — '
       'CI-автосинк. СЛЕДУЮЩИЙ НОМЕР ЗАДАЧИ: 493.')

src = io.open(PT, encoding='utf-8').read()
repsT = [
    ('> **Текущая версия кэша:** `kipia-test-v715`',
     '> **Текущая версия кэша:** `kipia-test-v716`'),
    ('Формат: `kipia-test-v715` → `kipia-test-v716` (для kip8test) или '
     '`kipia-v515` → `kipia-v516` (для kip8)',
     'Формат: `kipia-test-v716` → `kipia-test-v717` (для kip8test) или '
     '`kipia-v515` → `kipia-v516` (для kip8)'),
    ('# Ожидается: 6097 passed, 0 failed (kip8test; в kip8 — 6069 passed, '
     '0 failed — Tasks 490/491 НЕ переносились)',
     '# Ожидается: 6124 passed, 0 failed (kip8test; в kip8 — 6069 passed, '
     '0 failed — Tasks 490/491/492 НЕ переносились)'),
    ('(`tests/`, 6097 тестов, 199 тест-файлов, `node tests/run-all.js`)',
     '(`tests/`, 6124 тестов, 200 тест-файлов, `node tests/run-all.js`)'),
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
