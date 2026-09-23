#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 398 (kip8test): заявка «Почему в роли КИП ИОС видна кнопка
# "Работники" в разделе Табель учёта рабочего времени, хотя доступа
# и перехода по ней нет?»
#
# ДИАГНОЗ (зонд task398-diagnose*.py, порт 9019):
#   · роль «КИП ИОС» в матрице имеет workschedule.view.min (ограниченный
#     просмотр табеля): раздел доступен, JS-гейт Task 395 КОРРЕКТНО
#     ставит #wsWorkersBtn hidden=true (min ≠ edit/view);
#   · НО CSS-правило .ws-refresh-btn { display: inline-flex } (тулбар
#     табеля) ПЕРЕБИВАЕТ браузерный UA-стиль [hidden] { display: none }:
#     авторский CSS ВСЕГДА сильнее UA-стилей, атрибут «не работает» —
#     кнопка ОСТАЁТСЯ на экране (замер: rect 107×30 при hidden=true);
#   · клик молча отсекается openWorkersPage (lvl='min' → ранний выход):
#     ни перехода, ни экрана «Нет доступа» — точный симптом заявки.
#   · Полный DOM-скан (дашборд + табель, роль КИП ИОС): протекает ТОЛЬКО
#     #wsWorkersBtn; у прочих скрытых кнопок (Итоги/Сформировать/
#     Сохранить/Отменить/вкладки) авторских display-правил нет — hidden
#     работает. #wsPrintBtn/#wsViewBtn того же класса .ws-refresh-btn
#     протекают лишь в НЕДОСТИЖИМОМ состоянии (null — сам раздел скрыт).
#
# ФИКС: ОДНО универсальное CSS-правило в начале <style>:
#     [hidden] { display: none !important; }
#   восстанавливает семантику атрибута hidden ПО ВСЕМУ приложению
#   (какая бы display ни задавал авторский CSS); JS не трогаем —
#   показ всегда снятием атрибута (el.hidden = false), как и сделано.
#   Побочно закрывает и #wsPrintBtn/#wsViewBtn в граничных состояниях,
#   и любые будущие случаи (Task 397 «кнопка видна ⟺ переход возможен»).
# Только index.html (серверных шагов НЕТ).

REPLS = [

# ---------- CSS: универсальное правило [hidden] в начале <style> ----------
(
"""<style>
    :root {""",
"""<style>
    /* Task 398 (заявка: «почему в роли КИП ИОС видна кнопка "Работники"
       в разделе Табель, хотя доступа и перехода по ней нет?»): атрибут
       hidden БЫЛ бессильным против авторских display-правил — UA-стиль
       [hidden]{display:none} проигрывает ЛЮБОМУ авторскому правилу
       с display (пример: .ws-refresh-btn{display:inline-flex} — кнопка
       «Работники» #wsWorkersBtn: JS-гейт Task 395 ставит hidden=true
       уровням null/min, но кнопка ОСТАВАЛАСЬ на экране (107×30), клик
       молча отсекался openWorkersPage). Правило с !important ниже
       ВОССТАНАВЛИВАЕТ семантику hidden по всему приложению: элемент
       с атрибутом НЕ отображается, какой бы display ни задавал CSS.
       Показ элемента — всегда снятием атрибута (el.hidden=false),
       как и делает весь JS приложения. */
    [hidden] { display: none !important; }

    :root {"""
),
]

if __name__ == '__main__':
    path = 'index.html'
    s = open(path, encoding='utf-8').read()
    for i, (old, new) in enumerate(REPLS, 1):
        n = s.count(old)
        assert n == 1, 'REPL %d: найдено %d вхождений (ожидалось 1)' % (i, n)
        s = s.replace(old, new)
        print('REPL %2d: OK (%d симв.)' % (i, len(new)))
    open(path, 'w', encoding='utf-8').write(s)
    print('task398-patch: применено %d правок к index.html' % len(REPLS))
