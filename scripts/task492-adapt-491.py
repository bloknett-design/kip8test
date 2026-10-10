#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 492: адаптация test-task491.js — VM-секция (feat=избранное).
# Edit-tool не сматчил old_str из-за экранирования кавычек в regex
# (class="ts-card[ "]), поэтому правка применена побайтово-точным
# Python-скриптом (префиксная сверка уже выполнена: old в файле есть).
import io

P = 'tests/test-task491.js'
s = io.open(P, encoding='utf-8').read()

old_vm = """// D/E. VM — рендер карточек с featured-классом
// ============================================================
describe('Task 491 — VM: featured-класс на популярных кнопках', () => {

    test('4 ТС с ts-card-feat (обе 50М, обе 100М), 4 ТС без', () => {
        const vmw = makeVm491();
        vmw.api.renderTempSensorCards();
        const rtd = vmw.els['tsRtdCards'].innerHTML;
        assertEqual((rtd.match(/class="ts-card ts-card-feat"/g) || []).length, 4, '4 featured ТС');
        assertEqual((rtd.match(/class="ts-card"/g) || []).length, 4, '4 обычных ТС (Pt)');
        assertEqual((rtd.match(/class="ts-card[ "]/g) || []).length, 8, 'всего 8 ТС');
    });

    test('2 ТП с ts-card-feat (ТХА (K), ТХК (L)), 7 ТП без', () => {
        const vmw = makeVm491();
        vmw.api.renderTempSensorCards();
        const tc = vmw.els['tsTcCards'].innerHTML;
        assertEqual((tc.match(/class="ts-card ts-card-tc ts-card-feat"/g) || []).length, 2, '2 featured ТП');
        assertEqual((tc.match(/class="ts-card ts-card-tc"/g) || []).length, 7, '7 обычных ТП');
    });
"""

new_vm = """// D/E. VM — рендер карточек с featured-классом
// ============================================================
describe('Task 491 — VM: featured-класс (Task 492: на избранном)', () => {

    test('Без избранного: 0 featured ТС, все 8 обычные (Task 492)', () => {
        const vmw = makeVm491();
        vmw.api.renderTempSensorCards();
        const rtd = vmw.els['tsRtdCards'].innerHTML;
        assertEqual((rtd.match(/class="ts-card ts-card-feat"/g) || []).length, 0, '0 featured ТС (feat=избранное)');
        assertEqual((rtd.match(/class="ts-card"/g) || []).length, 8, 'все 8 ТС обычные');
        assertFalse(rtd.indexOf('ts-card-feat') !== -1,
            'популярные 50М/100М больше НЕ featured (Task 492)');
    });

    test('Без избранного: 0 featured ТП, все 9 обычные (Task 492)', () => {
        const vmw = makeVm491();
        vmw.api.renderTempSensorCards();
        const tc = vmw.els['tsTcCards'].innerHTML;
        assertEqual((tc.match(/class="ts-card ts-card-tc ts-card-feat"/g) || []).length, 0, '0 featured ТП');
        assertEqual((tc.match(/class="ts-card ts-card-tc"/g) || []).length, 9, 'все 9 ТП обычные');
        assertFalse(tc.indexOf('ts-card-feat') !== -1,
            'ТХА (K)/ТХК (L) больше НЕ featured (Task 492)');
    });
"""

old_fav = """    test('Избранные: featured-класс сохраняется у 50М, у обычных его нет', () => {
        const vmw = makeVm491();
        vmw.api.TempFav.add('cu50_1426');
        vmw.api.TempFav.add('tc_J');
        vmw.api.setTempSensorsTab('fav');
        vmw.api.renderTempSensorCards();
        const rtd = vmw.els['tsRtdCards'].innerHTML;
        const tc = vmw.els['tsTcCards'].innerHTML;
        assertEqual((rtd.match(/class="ts-card ts-card-feat"/g) || []).length, 1, '1 ТС — featured 50М');
        assertTrue(rtd.indexOf("openTempSensor('cu50_1426')") !== -1, 'карточка 50М (0,00426)');
        assertEqual((tc.match(/class="ts-card ts-card-tc"/g) || []).length, 1, '1 ТП (ТЖК J)');
        assertFalse(tc.indexOf('ts-card-feat') !== -1, 'у ТЖК (J) featured нет');
        vmw.api.setTempSensorsTab('all');
    });
});"""

new_fav = """    test('Избранные: featured-класс у избранного (Task 492)', () => {
        const vmw = makeVm491();
        vmw.api.TempFav.add('cu50_1426');
        vmw.api.TempFav.add('tc_J');
        vmw.api.setTempSensorsTab('fav');
        vmw.api.renderTempSensorCards();
        const rtd = vmw.els['tsRtdCards'].innerHTML;
        const tc = vmw.els['tsTcCards'].innerHTML;
        assertEqual((rtd.match(/class="ts-card ts-card-feat"/g) || []).length, 1, '1 ТС — featured 50М (в избранном)');
        assertTrue(rtd.indexOf("openTempSensor('cu50_1426')") !== -1, 'карточка 50М (0,00426)');
        // Task 492: ТЖК (J) — В избранном → featured (не как в Task 491)
        assertEqual((tc.match(/class="ts-card ts-card-tc ts-card-feat"/g) || []).length, 1, '1 ТП — featured ТЖК (J)');
        assertTrue(tc.indexOf("openTempSensor('tc_J')") !== -1, 'карточка ТЖК (J) в «Избранных»');
        vmw.api.setTempSensorsTab('all');
    });

    test('Вкладка «Все» с избранным: featured только у избранного', () => {
        const vmw = makeVm491();
        vmw.api.TempFav.add('pt1000_1385');
        vmw.api.setTempSensorsTab('all');
        vmw.api.renderTempSensorCards();
        const rtd = vmw.els['tsRtdCards'].innerHTML;
        assertEqual((rtd.match(/class="ts-card ts-card-feat"/g) || []).length, 1, 'только Pt1000 — featured');
        assertTrue(rtd.indexOf("openTempSensor('pt1000_1385')") !== -1, 'карточка Pt1000');
        const tc = vmw.els['tsTcCards'].innerHTML;
        assertFalse(tc.indexOf('ts-card-feat') !== -1, 'в ТП избранного нет');
        vmw.api.setTempSensorsTab('all');
    });
});"""

for tag, old, new in [('VM', old_vm, new_vm), ('FAV', old_fav, new_fav)]:
    assert old in s, 'old_str %s не найден' % tag
    assert s.count(old) == 1, 'old_str %s не уникален' % tag
    s = s.replace(old, new)
    print('OK: %s заменён' % tag)

io.open(P, 'w', encoding='utf-8').write(s)
print('test-task491.js: адаптация Task 492 (VM/FAV) применена')
