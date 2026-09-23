#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 395 — адаптация тестов под новую семантику:
#   (1) кнопка «Работники» видна уровням edit/view (НЕ отображается
#       для null — нет доступа — и min — ограниченный просмотр);
#   (2) десктоп-раскладка карточки — ДВЕ колонки (лево: профиль →
#       отпуска → мероприятия; право: СИЗ сверху) вместо сетки 2×2;
#   (3) зритель (view) теперь ПУСКАЕТСЯ на страницу «Работники»
#       (read-only), min/null — нет.
# Затронуты: test-task311.js (двойная защита), test-task385.js
# (SRC-гейт + _onRoleUpdate + VM), test-task394.js (CSS сетки).
import sys

def patch(path, repls):
    src = open(path, encoding='utf-8').read()
    fail = 0
    applied = 0
    for old, new, cnt in repls:
        n = src.count(old)
        if n != cnt:
            # уже применено (повторный запуск) — не ошибка
            if src.count(new) == cnt:
                applied += 1
                continue
            print('ANCHOR FAIL в %s (%d из %d):\n---\n%s\n---' % (path, n, cnt, old[:160]))
            fail += 1
            continue
        src = src.replace(old, new, cnt)
        applied += 1
    if fail:
        return False
    open(path, 'w', encoding='utf-8').write(src)
    print('OK: %s — %d правок' % (path, applied))
    return True

ok = True

# --- test-task311.js: двойная защита openWorkersPage ---
ok &= patch('tests/test-task311.js', [(
"""        // двойная защита: openWorkersPage сам проверяет право записи
        const owp = fnBody(INDEX_SRC, 'openWorkersPage: function');
        assertTrue(owp.indexOf('if (!this._canEdit) return;') !== -1,
            'openWorkersPage проверяет право записи (зритель — мимо)');
""",
"""        // двойная защита (Task 395): openWorkersPage пускает edit/view
        const owp = fnBody(INDEX_SRC, 'openWorkersPage: function');
        assertTrue(owp.indexOf("if (lvl !== 'edit' && lvl !== 'view') return;") !== -1,
            'openWorkersPage пускает edit/view (Task 395: null/min — мимо)');
""", 1
)])

# --- test-task385.js: SRC-гейт, _onRoleUpdate, VM ---
ok &= patch('tests/test-task385.js', [
(
"""    test('openWorkersPage — гейт + navigateTo + рендер', () => {
        const fn = methodText(INDEX_SRC, 'openWorkersPage');
        assertTrue(fn.indexOf('if (!this._canEdit) return;') !== -1,
            'двойная защита права записи');
""",
"""    test('openWorkersPage — гейт + navigateTo + рендер', () => {
        const fn = methodText(INDEX_SRC, 'openWorkersPage');
        assertTrue(fn.indexOf("if (lvl !== 'edit' && lvl !== 'view') return;") !== -1,
            'Task 395: гейт edit/view (null/min — мимо; зритель — пускается)');
""", 1
),
(
"""    test('_onRoleUpdate — кнопка «Работники» по _canEdit', () => {
        const i = INDEX_SRC.indexOf("_onRoleUpdate: function");
        const chunk = INDEX_SRC.slice(i, i + 2000);
        assertTrue(chunk.indexOf("wsWorkersBtn") !== -1 &&
                   chunk.indexOf('workersBtn.hidden = !newCanEdit') !== -1,
            'видимость кнопки — только редакторам (как «Сформировать»)');
    });
""",
"""    test('_onRoleUpdate — кнопка «Работники»: скрыта для null/min (Task 395)', () => {
        const i = INDEX_SRC.indexOf("_onRoleUpdate: function");
        const chunk = INDEX_SRC.slice(i, i + 2000);
        assertTrue(chunk.indexOf("wsWorkersBtn") !== -1 &&
                   chunk.indexOf("(newLevel === null || newLevel === 'min')") !== -1,
            'Task 395: кнопка НЕ отображается без прав (null) и при ограниченном просмотре (min)');
    });
""", 1
),
(
"""        // зритель — мимо
        const h2 = makeHost();
        h2.WSM._canEdit = false;
        h2.WSM.openWorkersPage();
        assertEqual(JSON.stringify(h2.nav()), JSON.stringify([]),
            'без права записи перехода нет');
""",
"""        // Task 395: ЗРИТЕЛЬ (view) — теперь пускается (кнопка видна
        // уровням edit/view; страница — read-only, без кнопок правки)
        const h2 = makeHost();
        h2.WSM._canEdit = false;
        h2.WSM.openWorkersPage();
        assertEqual(JSON.stringify(h2.nav()), JSON.stringify(['ws-workers']),
            'Task 395: зритель (view) переходит на страницу');
        // min (ограниченный просмотр) и null (нет доступа) — мимо
        const h3 = makeHost();
        h3.WSM._viewLevel = 'min';
        h3.WSM.openWorkersPage();
        assertEqual(JSON.stringify(h3.nav()), JSON.stringify([]),
            'Task 395: min — перехода нет (кнопка скрыта)');
        const h4 = makeHost();
        h4.WSM._viewLevel = null;
        h4.WSM.openWorkersPage();
        assertEqual(JSON.stringify(h4.nav()), JSON.stringify([]),
            'Task 395: null (нет доступа) — перехода нет');
""", 1
)])

# --- test-task394.js: CSS сетки 2×2 → колонки Task 395 ---
ok &= patch('tests/test-task394.js', [(
"""    test('десктоп ≥1024px — .ws-wgrid2: grid 2×2, gap 12, start', () => {
        const re = /@media \\(min-width: 1024px\\) \\{\\s*\\.ws-wgrid2 \\{[^}]*?display: grid;[^}]*?grid-template-columns: 1fr 1fr;[^}]*?gap: 12px;[^}]*?align-items: start;\\s*\\}\\s*\\.ws-wgrid2 \\.ws-wcard \\{ margin-bottom: 0; \\}/;
        assertTrue(re.test(INDEX_SRC),
            'сетка 2×2 равными колонками, зазор 12px, окна не тянутся');
    });
""",
"""    test('десктоп ≥1024px — .ws-wgrid2: ДВЕ колонки flex (Task 395)', () => {
        const re = /@media \\(min-width: 1024px\\) \\{\\s*\\.ws-wgrid2 \\{[^}]*?display: flex;[^}]*?gap: 12px;[^}]*?align-items: flex-start;\\s*\\}\\s*\\.ws-wgrid2 \\.ws-wcol \\{[^}]*?flex: 1 1 0;[^}]*?min-width: 0;[^}]*?margin-bottom: 0;\\s*\\}/;
        assertTrue(re.test(INDEX_SRC),
            'Task 395: две равные flex-колонки; правая (СИЗ) сверху — не тянется');
    });
""", 1
)])

sys.exit(0 if ok else 1)
