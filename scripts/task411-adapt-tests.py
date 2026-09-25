#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 411 — адаптация существующих тестов под новую форму:

1) test-work-events.js — префилл сотрудника: список фамилий убран,
   работник отображается статичной строкой (Task 411).
2) test-task410.js — _applyTrFormMode: ширина «Таб. №» больше НЕ
   переключается (работник — статичная строка во всю ширину в обоих
   режимах); убраны flex-ассерты SRC и VM.
"""
import io

REPO = '/home/z/my-project/kip8test'


def replace_once(path, old, new, tag):
    with io.open(path, encoding='utf-8') as f:
        s = f.read()
    n = s.count(old)
    assert n == 1, '%s: ожидается 1 вхождение, найдено %d' % (tag, n)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(s.replace(old, new, 1))
    print('OK  %s' % tag)


def main():
    # --- 1. test-work-events.js: статичная строка работника ---
    replace_once(
        REPO + '/tests/test-work-events.js',
        """        assertTrue(INDEX_SRC.indexOf('if (prefillTab) empSel.value = String(prefillTab);') !== -1,
            'сотрудник вписывается в форму');""",
        """        // Task 411: список фамилий убран — работник карточки входа
        // отображается статичной строкой «ФИО · таб. №»
        assertTrue(INDEX_SRC.indexOf("empDiv.textContent = emp['ФИО'] + ' · таб. №' + emp['таб_номер'];") !== -1,
            'сотрудник карточки — статичная строка формы (Task 411)');""",
        '1. work-events: статичная строка работника')

    # --- 2. test-task410.js: SRC-ассерт ширины ---
    replace_once(
        REPO + '/tests/test-task410.js',
        """    test('_applyTrFormMode: скрытие «Тип», ширина «Таб. №», ярлык', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_applyTrFormMode'));
        assertTrue(fn.indexOf("typeGroup.style.display = instr ? 'none' : '';") !== -1,
            'группа «Тип» скрыта в instr-режиме');
        assertTrue(fn.indexOf("tabGroup.style.flex = instr ? '1 1 100%' : '0 0 35%';") !== -1,
            '«Таб. №» — во всю ширину в instr-режиме');
        assertTrue(fn.indexOf("'Инструктаж / проверка знаний'") !== -1 &&
                   fn.indexOf(": 'Тема'") !== -1,
            'ярлык темы переключается по режиму');
    });""",
        """    test('_applyTrFormMode: скрытие «Тип» + ярлык (Task 411: работник — статичная строка)', () => {
        const fn = stripComments(methodText(INDEX_SRC, '_applyTrFormMode'));
        assertTrue(fn.indexOf("typeGroup.style.display = instr ? 'none' : '';") !== -1,
            'группа «Тип» скрыта в instr-режиме');
        assertTrue(fn.indexOf('tabGroup.style.flex') === -1,
            'ширина работника не переключается (Task 411 — статичная строка)');
        assertTrue(fn.indexOf("'Инструктаж / проверка знаний'") !== -1 &&
                   fn.indexOf(": 'Тема'") !== -1,
            'ярлык темы переключается по режиму');
    });""",
        '2. task410: SRC-ассерт ширины')

    # --- 3. test-task410.js: VM instr-тест ---
    replace_once(
        REPO + '/tests/test-task410.js',
        """    test('instr: «Тип» скрыт, «Таб. №» во всю ширину, ярлык темы', () => {
        const c = modeHost(true);
        c.host._applyTrFormMode();
        assertEqual(c.els.wsTrTypeGroup.style.display, 'none',
            'группа «Тип» скрыта');
        assertEqual(c.els.wsTrTabGroup.style.flex, '1 1 100%',
            '«Таб. №» во всю ширину');
        assertEqual(c.els.wsTrTitleLabel.textContent,
            'Инструктаж / проверка знаний', 'ярлык темы instr-режима');
    });""",
        """    test('instr: «Тип» скрыт, ярлык темы (Task 411: работник — статично)', () => {
        const c = modeHost(true);
        c.host._applyTrFormMode();
        assertEqual(c.els.wsTrTypeGroup.style.display, 'none',
            'группа «Тип» скрыта');
        assertEqual(c.els.wsTrTitleLabel.textContent,
            'Инструктаж / проверка знаний', 'ярлык темы instr-режима');
    });""",
        '3. task410: VM instr-тест')

    # --- 4. test-task410.js: VM event-тест ---
    replace_once(
        REPO + '/tests/test-task410.js',
        """    test('event: прежний вид формы', () => {
        const c = modeHost(false);
        c.host._applyTrFormMode();
        assertEqual(c.els.wsTrTypeGroup.style.display, '',
            'группа «Тип» видна');
        assertEqual(c.els.wsTrTabGroup.style.flex, '0 0 35%',
            'ширина «Таб. №» прежняя');
        assertEqual(c.els.wsTrTitleLabel.textContent, 'Тема',
            'ярлык «Тема»');
    });""",
        """    test('event: прежний вид формы', () => {
        const c = modeHost(false);
        c.host._applyTrFormMode();
        assertEqual(c.els.wsTrTypeGroup.style.display, '',
            'группа «Тип» видна');
        assertEqual(c.els.wsTrTitleLabel.textContent, 'Тема',
            'ярлык «Тема»');
    });""",
        '4. task410: VM event-тест')

    print('Адаптация тестов завершена')


if __name__ == '__main__':
    main()
