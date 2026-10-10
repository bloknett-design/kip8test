#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 496 — правка 2: глобальный обработчик Enter/Next (стр. ~31636
# «Обработчик Enter/Next на клавиатуре — логичный переход между
# полями и расчёт») ПЕРЕСКАКИВАЕТ фокус после нашего blur: событие
# всплывает до document, handler видит e.target=input ППР и ставит
# фокус в СЛЕДУЮЩЕЕ поле (tempQueryVal / temp_sensor_min).
# Фикс: tempQueryEnterBlur + e.stopPropagation() — ППР-поля
# выходят из глобального перескока (Enter = закрыть клавиатуру).
# Глобальный handler и остальные блоки — НЕ ТРОГАЕМ (граница заявки).
import io

INDEX = '/home/z/my-project/kip8test/index.html'

src = io.open(INDEX, encoding='utf-8').read()

# ---------- 1. JS-функция: + stopPropagation ----------
OLD_FN = """    // Task 496 (заявка): в блоке произвольного расчёта кнопка подтверждения
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
    }"""
NEW_FN = """    // Task 496 (заявка): в блоке произвольного расчёта кнопка подтверждения
    // («Готово»/Enter) мобильной клавиатуры ЗАКРЫВАЕТ клавиатуру, а не
    // перескакивает на следующее поле: у поля температуры был
    // enterkeyhint="next" (кнопка «Далее» вела в поле значения) — оба поля
    // переведены на enterkeyhint="done", Enter гасится и снимает фокус
    // (preventDefault + blur: клавиатура закрывается и на iOS, где «done»
    // сам по себе клавиатуру не убирает, и на Android). ВАЖНО:
    // stopPropagation — ППР-поля выходят из ГЛОБАЛЬНОГО обработчика
    // Enter/Next («логичный переход между полями», document keydown):
    // без него после blur событие всплывает, глобальный handler ставит
    // фокус в следующее поле и клавиатура не закрывается. Глобальный
    // переход в остальных блоках — без изменений. Живой двусторонний
    // расчёт по oninput (Task 371) не меняется.
    function tempQueryEnterBlur(e, el){
        if(!e){return;}
        if(e.key==='Enter'||e.keyCode===13){
            e.preventDefault();
            if(e.stopPropagation){e.stopPropagation();}
            if(el&&typeof el.blur==='function'){el.blur();}
        }
    }"""
assert src.count(OLD_FN) == 1, 'функция: %d' % src.count(OLD_FN)
src = src.replace(OLD_FN, NEW_FN)

# ---------- 2. Комментарий над панелью: + stopPropagation ----------
OLD_C = """                         enterkeyhint="done" + onkeydown tempQueryEnterBlur
                         (preventDefault + blur). Живой двусторонний расчёт
                         по oninput (Task 371) — без изменений. -->"""
NEW_C = """                         enterkeyhint="done" + onkeydown tempQueryEnterBlur
                         (preventDefault + stopPropagation + blur — выход из
                         глобального Enter-перехода между полями). Живой
                         двусторонний расчёт по oninput (Task 371) — без
                         изменений. -->"""
assert src.count(OLD_C) == 1, 'комментарий ППР: %d' % src.count(OLD_C)
src = src.replace(OLD_C, NEW_C)

io.open(INDEX, 'w', encoding='utf-8').write(src)
print('index.html: tempQueryEnterBlur + stopPropagation (функция + комментарий) — ок')

# ---------- Контроль ----------
chk = io.open(INDEX, encoding='utf-8').read()
fn = chk[chk.find('function tempQueryEnterBlur'):chk.find('function tempQueryFromTemp')]
assert 'stopPropagation' in fn, 'stopPropagation в функции'
assert fn.count('e.stopPropagation') == 2  # guard + вызов
# глобальный handler не тронут
glob = chk[chk.find('// Обработчик Enter/Next на клавиатуре'):chk.find('// Обработчик Enter/Next на клавиатуре') + 1200]
assert "fields[idx + 1].focus();" in glob, 'глобальный переход жив (граница заявки)'
assert 'tempQuery' not in glob, 'глобальный handler не знает про ППР'
print('Контроль: stopPropagation в хелпере; глобальный Enter-переход жив '
      '(остальные блоки не тронуты). Всё ок.')
