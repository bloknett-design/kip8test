#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 496 (заявка): «В блоке произвольного расчёта, после ввода
# одного из данных и при нажатии подтверждения на клавиатуре,
# клавиатура должна закрываться, а не перемещаться по следующим
# полям ввода.»
#
# Панель ППР page-temp-sensor-view (#tempCustomCalcPanel):
#   1) поле tempQueryTemp: enterkeyhint="next" → "done" (кнопка
#      «Далее» на мобильной клавиатуре больше НЕ перескакивает в
#      поле значения);
#   2) ОБА поля ППР получают onkeydown="tempQueryEnterBlur(event,this)"
#      — Enter («Готово»/подтверждение) гасится (preventDefault) и
#      снимает фокус (blur) → клавиатура ЗАКРЫВАЕТСЯ (на iOS «done»
#      сам клавиатуру не убирает, на Android — но blur гарантирует);
#   3) JS-хелпер tempQueryEnterBlur перед tempQueryFromTemp;
#   4) комментарий над панелью + Task 496.
# Блок расчёта таблицы (Task 495, tempTableFormPanel min/max/step)
# и остальные страницы — НЕ ТРОГАЕМ (заявка только про ППР).
# sw.js: kipia-test-v719 → v720 + комментарий.
import io

INDEX = '/home/z/my-project/kip8test/index.html'
SW = '/home/z/my-project/kip8test/sw.js'

src = io.open(INDEX, encoding='utf-8').read()

# ---------- 1. Комментарий над панелью ППР (+ Task 496) ----------
OLD_COMMENT = """                         крупнее и ярче (класс ts-calc-field, CSS в <style>). -->
                    <div class="ts-calc-panel" id="tempCustomCalcPanel">"""
NEW_COMMENT = """                         крупнее и ярче (класс ts-calc-field, CSS в <style>).
                         Task 496 (заявка): после ввода значения нажатие
                         кнопки подтверждения («Готово»/Enter) мобильной
                         клавиатуры ЗАКРЫВАЕТ клавиатуру, а не перескакивает
                         на следующее поле: у поля температуры был
                         enterkeyhint="next" (кнопка «Далее» вела в поле
                         значения) — оба поля переведены на
                         enterkeyhint="done" + onkeydown tempQueryEnterBlur
                         (preventDefault + blur). Живой двусторонний расчёт
                         по oninput (Task 371) — без изменений. -->
                    <div class="ts-calc-panel" id="tempCustomCalcPanel">"""
assert src.count(OLD_COMMENT) == 1, 'комментарий ППР: %d' % src.count(OLD_COMMENT)
src = src.replace(OLD_COMMENT, NEW_COMMENT)

# ---------- 2. Поле «Температура (°C)»: next → done + onkeydown ----------
OLD_T = """<input type="text" inputmode="numeric" id="tempQueryTemp" class="scale-field ts-calc-field" placeholder="Например: 55" oninput="tempQueryFromTemp()" autocomplete="off" enterkeyhint="next">"""
NEW_T = """<input type="text" inputmode="numeric" id="tempQueryTemp" class="scale-field ts-calc-field" placeholder="Например: 55" oninput="tempQueryFromTemp()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">"""
assert src.count(OLD_T) == 1, 'поле tempQueryTemp: %d' % src.count(OLD_T)
src = src.replace(OLD_T, NEW_T)

# ---------- 3. Поле значения: + onkeydown ----------
OLD_V = """<input type="text" inputmode="numeric" id="tempQueryVal" class="scale-field ts-calc-field" placeholder="Например: 61,8" oninput="tempQueryFromValue()" autocomplete="off" enterkeyhint="done">"""
NEW_V = """<input type="text" inputmode="numeric" id="tempQueryVal" class="scale-field ts-calc-field" placeholder="Например: 61,8" oninput="tempQueryFromValue()" onkeydown="tempQueryEnterBlur(event,this)" autocomplete="off" enterkeyhint="done">"""
assert src.count(OLD_V) == 1, 'поле tempQueryVal: %d' % src.count(OLD_V)
src = src.replace(OLD_V, NEW_V)

# ---------- 4. JS-хелпер tempQueryEnterBlur (перед tempQueryFromTemp) ----------
OLD_FN = """    // Task 371: живой расчёт «температура → R/E» (ввод в поле температуры)
    function tempQueryFromTemp(){"""
NEW_FN = """    // Task 496 (заявка): в блоке произвольного расчёта кнопка подтверждения
    // («Готово»/Enter) мобильной клавиатуры ЗАКРЫВАЕТ клавиатуру, а не
    // перескакивает на следующее поле: у поля температуры был
    // enterkeyhint="next" (кнопка «Далее» вела в поле значения) — оба поля
    // переведены на enterkeyhint="done", Enter гасится и снимает фокус
    // (preventDefault + blur: клавиатура закрывается и на iOS, где «done»
    // сам по себе клавиатуру не убирает, и на Android). Живой
    // двусторонний расчёт по oninput (Task 371) не меняется.
    function tempQueryEnterBlur(e, el){
        if(!e){return;}
        if(e.key==='Enter'||e.keyCode===13){
            e.preventDefault();
            if(el&&typeof el.blur==='function'){el.blur();}
        }
    }
    // Task 371: живой расчёт «температура → R/E» (ввод в поле температуры)
    function tempQueryFromTemp(){"""
assert src.count(OLD_FN) == 1, 'tempQueryFromTemp: %d' % src.count(OLD_FN)
src = src.replace(OLD_FN, NEW_FN)

io.open(INDEX, 'w', encoding='utf-8').write(src)
print('index.html: 4 правки (комментарий, 2 поля, JS-хелпер) — ок')

# ---------- 5. sw.js: v719 → v720 + комментарий ----------
sw = io.open(SW, encoding='utf-8').read()

OLD_SW = """// Task 495: «Датчики температуры» — блок ввода данных расчёта
// таблицы: поле типа датчика (чип) с подписью и подсказка про шаг
// пересчёта удалены; блок оформлен как панель произвольного
// расчёта, но с эффектом УГЛУБЛЕНИЯ (ts-calc-inset). Клиент-only.
const CACHE_VERSION = 'kipia-test-v719';"""
NEW_SW = """// Task 495: «Датчики температуры» — блок ввода данных расчёта
// таблицы: поле типа датчика (чип) с подписью и подсказка про шаг
// пересчёта удалены; блок оформлен как панель произвольного
// расчёта, но с эффектом УГЛУБЛЕНИЯ (ts-calc-inset). Клиент-only.
// Task 496: «Датчики температуры» — панель произвольного расчёта:
// кнопка подтверждения («Готово»/Enter) мобильной клавиатуры
// закрывает клавиатуру (enterkeyhint done + tempQueryEnterBlur),
// а не перескакивает на следующее поле. Клиент-only.
const CACHE_VERSION = 'kipia-test-v720';"""
assert sw.count(OLD_SW) == 1, 'sw.js Task 495 блок: %d' % sw.count(OLD_SW)
sw = sw.replace(OLD_SW, NEW_SW)

io.open(SW, 'w', encoding='utf-8').write(sw)
print('sw.js: kipia-test-v719 → v720 + комментарий Task 496 — ок')

# ---------- Контроль ----------
chk = io.open(INDEX, encoding='utf-8').read()
ppr = chk[chk.indexOf if False else 0:]
i = chk.find('<div class="ts-calc-panel" id="tempCustomCalcPanel">')
j = chk.find('id="tempTableFormPanel"')
ppr_block = chk[i:j]
assert 'enterkeyhint="next"' not in ppr_block, 'в ППР остался next!'
assert ppr_block.count('tempQueryEnterBlur(event,this)') == 2
assert ppr_block.count('enterkeyhint="done"') == 2
tbl_i = chk.find('<div class="ts-calc-panel ts-calc-inset" id="tempTableFormPanel">')
tbl_j = chk.find('converter-convert-btn', tbl_i)
tbl_block = chk[tbl_i:tbl_j]
assert tbl_block.count('enterkeyhint="next"') == 2, \
    'поля min/max блока таблицы должны остаться next (заявка только ППР)'
assert 'tempQueryEnterBlur' not in tbl_block, 'блок таблицы не трогаем!'
assert 'function tempQueryEnterBlur(e, el){' in chk
assert chk.count('function tempQueryEnterBlur') == 1
assert "const CACHE_VERSION = 'kipia-test-v720'" in sw
assert 'kipia-test-v719' not in sw
print('Контроль: ППР done×2 + onkeydown×2; блок таблицы next×2 НЕ тронут; '
      'SW v720. Всё ок.')
