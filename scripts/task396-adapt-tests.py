#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 396: адаптация существующих тестов под НОВУЮ структуру
# шапок блоков карточки (Task 396: .ws-whead с кнопками в углу —
# заголовки блоков теперь ТЕРНАРНЫЕ asBlocks ? whead : popup-*,
# легаси-ветки сохранены для попапа шахматки).
# Затронут ТОЛЬКО test-task393.js (4 SRC-ассерта «var bX = …»):
# ассерты переписаны на проверку ОБЕИХ веток (whead для панелей +
# прежние классы для попапа). Идемпотентен при повторе.
import io

PATH = 'tests/test-task393.js'
s = io.open(PATH, encoding='utf-8').read()
orig = s
n = 0

def rep(old, new):
    global s, n
    assert s.count(old) == 1, 'не найден (или не уникален): %r' % old[:80]
    s = s.replace(old, new)
    n += 1
    print('  ✓ %s' % new.splitlines()[0][:90])

# b1 — шапка ФИО: Task 396 — asBlocks ? .ws-whead(.ws-whead-name) : .ws-popup-title
rep("""        assertTrue(fn.indexOf("var b1 = '<div class=\\"ws-popup-title\\">'") !== -1,
            'b1 — шапка ФИО · таб. №');""",
"""        assertTrue(fn.indexOf("'<div class=\\"ws-whead\\"><div class=\\"ws-whead-t ws-whead-name\\">'") !== -1,
            'b1 — шапка ФИО · таб. № (Task 396: полоса .ws-whead у блоков-окон)');
        assertTrue(fn.indexOf("'<div class=\\"ws-popup-title\\">'") !== -1,
            'b1 — легаси-ветка попапа: прежний .ws-popup-title');""")

# b2 — отпуска: легаси-ветка .ws-popup-sec жива (без префикса var b2 =)
rep("""        assertTrue(fn.indexOf("var b2 = '<div class=\\"ws-popup-sec\\">Отпуска · '") !== -1,
            'b2 — отпуска года');""",
"""        assertTrue(fn.indexOf("'<div class=\\"ws-popup-sec\\">Отпуска · '") !== -1,
            'b2 — отпуска года (легаси-ветка попапа)');""")

# b3 — мероприятия: легаси-ветка
rep("""        assertTrue(fn.indexOf("var b3 = '<div class=\\"ws-popup-sec\\">Мероприятия · '") !== -1,
            'b3 — мероприятия месяца');""",
"""        assertTrue(fn.indexOf("'<div class=\\"ws-popup-sec\\">Мероприятия · '") !== -1,
            'b3 — мероприятия (легаси-ветка попапа)');""")

# b4 — СИЗ: легаси-ветка
rep("""        assertTrue(fn.indexOf("var b4 = '<div class=\\"ws-popup-sec\\">СИЗ · средства индивидуальной защиты</div>'") !== -1,
            'b4 — СИЗ');""",
"""        assertTrue(fn.indexOf("'<div class=\\"ws-popup-sec\\">СИЗ · средства индивидуальной защиты</div>'") !== -1,
            'b4 — СИЗ (легаси-ветка попапа)');""")

assert s != orig
io.open(PATH, 'w', encoding='utf-8').write(s)
print('test-task393.js: %d ассертов адаптировано' % n)

# ============================================================
# test-task318.js — сегмент ±400 вокруг «ws-emp-dismiss» больше
# НЕ содержит гейт withEdit (Task 396: «Уволить…» — компактная
# кнопка, собирается в b1Acts ЗА гейтом if (withEdit) выше по
# тексту). Ассерт переписан на проверку «гейт РАНЬШЕ кнопки».
# Идемпотентно: уже адаптировано — пропуск.
# ============================================================
PATH2 = 'tests/test-task318.js'
s2 = io.open(PATH2, encoding='utf-8').read()
OLD2 = """        const seg = rp.slice(Math.max(0, i - 400), i + 400);
        assertTrue(seg.indexOf('withEdit') !== -1,
            'только с withEdit (Task 385: страница «Работники», редакторам)');"""
NEW2 = """        const seg = rp.slice(Math.max(0, i - 400), i + 400);
        // Task 396: «Уволить…» — компактная кнопка шапки (b1Acts):
        // гейт withEdit — РАНЬШЕ кнопки по тексту метода
        assertTrue(rp.lastIndexOf('if (withEdit) {', i) !== -1,
            'только с withEdit (кнопка внутри гейта сборки b1Acts)');"""
if s2.count(OLD2) == 1:
    s2 = s2.replace(OLD2, NEW2)
    io.open(PATH2, 'w', encoding='utf-8').write(s2)
    print('test-task318.js: 1 ассерт адаптирован (гейт withEdit до кнопки)')
elif s2.count(NEW2) == 1:
    print('test-task318.js: уже адаптирован (пропуск)')
else:
    raise SystemExit('test-task318.js: якорь не найден')
