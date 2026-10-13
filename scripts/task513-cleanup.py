#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 513 — УБОРКА МЁТВОГО КОДА (по аудиту Task 512 + верификация 2026-10-13).

Параметры: python3 task513-cleanup.py <repo_path>

Удаляет (с пре/пост-ассертами):
  index.html — 25 мёртвых функций + 4 мёртвых метода (верифицировано:
    точное имя встречается ровно 1 раз = определение; ссылки из тестов
    и desktop-репо ОТСУТСТВУЮТ; 8 методов из аудита СОХРАНЕНЫ — тесты
    их вызывают: _renderEmpPopup/_sourceLabel/_state/_vacDays/_vacNetDays/
    _wsFullFio/del/reloadTotals).
  scripts/*.gs — 8 мёртвых бэкенд-функций + ОПАСНЫЙ дубликат
    setupTriggers из Utils.gs (удаляет ВСЕ триггеры; канон — Code.gs).
  НЕ трогает: 7 backend test-only функций, 5 frontend test-only функций,
    openLibraryViewer (защитный стаб), роуты, guarded-остатки id.

State-machine: строки/шаблоны/комментарии/regex-эвристика (для
brace-matching). Верификация после: node --check + тесты (вне скрипта).
"""
import io
import os
import re
import sys

# --- цели для index.html: (имя, тип) ---
INDEX_FUNCS = [
    ('calcErrorGOST', 'function'),
    ('devPlural', 'function'),
    ('devScrollToGroup', 'function'),
    ('devShowMoreSorted', 'function'),
    ('devToggleTypeFilter', 'function'),
    ('devUpdateFilterButton', 'function'),
    ('getOimlMpe', 'function'),
    ('isTablet', 'function'),
    ('lockForceRefresh', 'function'),
    ('lockGetLastUpdateDate', 'function'),
    ('lockScrollToGroup', 'function'),
    ('projectGetLastUpdateDate', 'function'),
    ('projectsForceRefresh', 'function'),
    ('projectsScrollToGroup', 'function'),
    ('refreshAppData', 'function'),
    ('regulatorForceRefresh', 'function'),
    ('regulatorGetLastUpdateDate', 'function'),
    ('regulatorScrollToGroup', 'function'),
    ('ticketRenderDetailInPanel', 'function'),
    ('toggleErrorClassFields', 'function'),
    ('validateNonNegativeField', 'function'),
    ('valveForceRefresh', 'function'),
    ('valveGetLastUpdateDate', 'function'),
    ('valveScrollToGroup', 'function'),
    ('_fmtDateTime', 'method'),
    ('getCurrentUser', 'method'),
    ('handleBackButton', 'method'),
    ('toggleSearch', 'method'),
]

# --- цели для scripts/*.gs: (файл, имя) ---
GS_FUNCS = [
    ('RoleMatrixInit.gs', '_colLetter'),
    ('Flowmeter.gs', 'flowmeterCleanupCommentMetadata'),
    ('FlowmeterInit.gs', 'flowmeterFixDates'),
    ('RoleMatrix.gs', 'roleMatrixHasPermission'),
    ('RoleMatrix.gs', 'roleMatrixGetAccessForEmail'),
    ('SessionsDevicePolicy.gs', 'sdpDebug'),
    ('StatusCodesInit.gs', 'statusCodesDeployAll'),
    ('StatusCodesInit.gs', 'statusCodesStatus'),
    ('Utils.gs', 'setupTriggers'),
]

KEYWORDS_BEFORE_REGEX = re.compile(
    r'(return|typeof|instanceof|in|of|new|delete|void|throw|case|do|else|yield)$')

COMMENT_LINE = re.compile(r'^\s*(//|/\*|\*)')


def find_def(text, name, kind):
    """Найти определение. Возвращает (match) или бросает ошибку."""
    if kind == 'function':
        pat = r'^([ \t]*)(async[ \t]+)?function[ \t]+' + re.escape(name) + r'[ \t]*\('
    elif kind == 'method':
        pat = r'^([ \t]*)' + re.escape(name) + r'[ \t]*:[ \t]*function[ \t]*\('
    elif kind == 'iife':
        pat = r'^([ \t]*)\(function[ \t]+' + re.escape(name) + r'[ \t]*\('
    else:
        raise ValueError(kind)
    matches = list(re.finditer(pat, text, re.M))
    if len(matches) != 1:
        raise AssertionError('%s: найдено %d определений (ожидалось 1)'
                             % (name, len(matches)))
    return matches[0]


def match_brace(text, pos):
    """От открывающей { до парной }. String/comment/regex-aware.
    Возвращает индекс парной } или -1."""
    i = pos
    depth = 0
    n = len(text)
    state = 'n'  # n normal, s ', d ", t `, l //, b /*, r regex
    last_nonspace = ''
    while i < n:
        c = text[i]
        if state == 'n':
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i
            elif c == "'":
                state = 's'
            elif c == '"':
                state = 'd'
            elif c == '`':
                state = 't'
            elif c == '/' and text[i:i + 2] == '//':
                state = 'l'
            elif c == '/' and text[i:i + 2] == '/*':
                state = 'b'
            elif c == '/':
                # regex или деление? эвристика по предыдущему значимому символу
                prev = last_nonspace
                is_regex = False
                if prev == '' or prev in '(,=:[!&|?{;':
                    is_regex = True
                elif prev == '}' or prev == ')':
                    # может быть и так и так; проверим слово перед скобкой
                    j = i - 1
                    while j >= 0 and text[j] in ' \t\n\r':
                        j -= 1
                    k = j
                    while k >= 0 and (text[k].isalnum() or text[k] in '_$'):
                        k -= 1
                    word = text[k + 1:j + 1]
                    if word and (KEYWORDS_BEFORE_REGEX.search(word)
                                 or word in ('if', 'while', 'for')):
                        is_regex = True
                if is_regex:
                    state = 'r'
            if not c.isspace():
                last_nonspace = c
        elif state == 's':
            if c == '\\':
                i += 1
            elif c == "'":
                state = 'n'
        elif state == 'd':
            if c == '\\':
                i += 1
            elif c == '"':
                state = 'n'
        elif state == 't':
            if c == '\\':
                i += 1
            elif c == '`':
                state = 'n'
        elif state == 'l':
            if c == '\n':
                state = 'n'
        elif state == 'b':
            if text[i:i + 2] == '*/':
                state = 'n'
                i += 1
        elif state == 'r':
            if c == '\\':
                i += 1
            elif c == '[':
                state = 'R'  # класс символов в regex
            elif c == '/':
                state = 'n'
        elif state == 'R':
            if c == '\\':
                i += 1
            elif c == ']':
                state = 'r'
        i += 1
    return -1


def remove_block(path, text, name, kind):
    """Удалить блок определения + прилегающие комментарии.
    Возвращает (new_text, удалённые_строки)."""
    m = find_def(text, name, kind)
    # первый { после начала определения
    brace = text.find('{', m.start())
    close = match_brace(text, brace)
    if close < 0:
        raise AssertionError('%s: парная } не найдена' % name)
    end = close
    # метод: захватить хвостовую запятую
    if kind == 'method':
        rest = text[end + 1:]
        mm = re.match(r'\s*,', rest)
        if mm:
            end += 1 + mm.end()
    # iife: захватить )()  или )();
    if kind == 'iife':
        rest = text[end + 1:]
        mm = re.match(r'\s*\)\s*\(\s*\)\s*;?', rest)
        if mm:
            end += 1 + mm.end()
        else:
            raise AssertionError('%s: IIFE-хвост не найден' % name)

    # границы строк
    start_line = text.count('\n', 0, m.start())
    end_line = text.count('\n', 0, end)
    lines = text.split('\n')

    # walk-back по комментариям над определением
    first = start_line
    while first - 1 >= 0 and COMMENT_LINE.match(lines[first - 1]):
        first -= 1

    # если строка над комментариями пустая и над НЕЙ тоже пустая —
    # съесть одну (чтобы не осталось 2+ пустых)
    ate_blank = False
    if first - 1 >= 0 and lines[first - 1].strip() == '':
        if first - 2 >= 0 and lines[first - 2].strip() == '':
            first -= 1
            ate_blank = True
        elif first - 2 < 0:
            first -= 1
            ate_blank = True

    removed = lines[first:end_line + 1]
    new_lines = lines[:first] + lines[end_line + 1:]

    # пост-чистка: не допускать 2+ подряд пустых в месте склейки
    j = first - 1
    while j >= 0 and j < len(new_lines):
        if new_lines[j].strip() == '' and j + 1 < len(new_lines) \
                and new_lines[j + 1].strip() == '':
            del new_lines[j + 1]
        else:
            break

    return '\n'.join(new_lines), len(removed), (first + 1, end_line + 1)


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else '/home/z/my-project/kip8test'
    idx_path = os.path.join(repo, 'index.html')
    text = io.open(idx_path, encoding='utf-8').read()
    orig_lines = text.count('\n') + 1
    total_removed = 0
    report = []

    print('=== index.html: %d целей ===' % len(INDEX_FUNCS))
    for name, kind in INDEX_FUNCS:
        # пре-ассерт: имя встречается ровно 1 раз (для getCurrentUser —
        # ровно 1 раз ШАБЛОН определения; другие вхождения — api/комменты)
        if name == 'getCurrentUser':
            cnt = len(re.findall(r'^\s*getCurrentUser\s*:\s*function', text, re.M))
        else:
            cnt = len(re.findall(r'\b' + re.escape(name) + r'\b', text))
        if cnt != 1:
            raise SystemExit('ПРЕ-АССЕРТ ПРОВАЛЕН: %s — %d вхождений' % (name, cnt))
        text, n, span = remove_block(idx_path, text, name, kind)
        total_removed += n
        report.append('%-28s %-8s строк %3d (%d-%d)' % (name, kind, n, span[0], span[1]))
        print('  ok: %-28s −%d строк' % (name, n))

    io.open(idx_path, 'w', encoding='utf-8').write(text)

    # пост-ассерты
    for name, kind in INDEX_FUNCS:
        if name == 'getCurrentUser':
            if re.search(r'^\s*getCurrentUser\s*:\s*function', text, re.M):
                raise SystemExit('ПОСТ-АССЕРТ: определение getCurrentUser живо')
        elif re.search(r'\b' + re.escape(name) + r'\b', text):
            raise SystemExit('ПОСТ-АССЕРТ: %s ещё в файле' % name)

    print('index.html: %d → %d строк (−%d)' % (orig_lines, text.count('\n') + 1, total_removed))

    # ---------- .gs файлы ----------
    print('=== scripts/*.gs: %d целей ===' % len(GS_FUNCS))
    gs_total = 0
    for fname, name in GS_FUNCS:
        path = os.path.join(repo, 'scripts', fname)
        src = io.open(path, encoding='utf-8').read()
        cnt = len(re.findall(r'\b' + re.escape(name) + r'\b', src))
        # пре-ассерт: определение ровно 1; прочие вхождения — только комменты
        defs = len(re.findall(r'^function\s+' + re.escape(name) + r'\s*\(', src, re.M))
        if defs != 1:
            raise SystemExit('ПРЕ-АССЕРТ %s/%s: определений %d' % (fname, name, defs))
        src, n, span = remove_block(path, src, name, 'function')
        io.open(path, 'w', encoding='utf-8').write(src)
        gs_total += n
        print('  ok: %s/%s −%d строк (%d-%d)' % (fname, name, n, span[0], span[1]))

    # ---------- точечные правки устаревших комментариев ----------
    print('=== правки устаревших комментариев ===')

    def edit(path, old, new, label):
        src = io.open(path, encoding='utf-8').read()
        c = src.count(old)
        if c != 1:
            raise SystemExit('КОММЕНТ-ПРАВКА «%s»: найдено %d (ожидалось 1)' % (label, c))
        io.open(path, 'w', encoding='utf-8').write(src.replace(old, new))
        print('  ok: %s' % label)

    # осиротевший заголовок «ДИАГНОСТИКА» (единственной функцией был sdpDebug)
    sdp = os.path.join(repo, 'scripts', 'SessionsDevicePolicy.gs')
    src_sdp = io.open(sdp, encoding='utf-8').read()
    orphan = ('\n// ==========================================================================\n'
              '// ДИАГНОСТИКА\n'
              '// ==========================================================================\n')
    if src_sdp.endswith(orphan):
        io.open(sdp, 'w', encoding='utf-8').write(src_sdp[:-len(orphan)] + '\n')
        print('  ok: SessionsDevicePolicy.gs — осиротевший заголовок ДИАГНОСТИКА')

    rm = os.path.join(repo, 'scripts', 'RoleMatrix.gs')
    edit(rm,
         ' *   roleMatrixHasPermission(roleName, permId) → true/false\n'
         ' *   roleMatrixGetAccessForEmail(email)\n'
         ' *     → как getAccess + email/userFound (роль из листа users)\n',
         '',
         'RoleMatrix.gs: шапка — список публичных функций')
    edit(rm,
         ' *   var acc = roleMatrixGetAccessForEmail(user.email);\n'
         ' *   if (!roleMatrixHasPermission(acc.role, \'kipios.view\')) { … }\n',
         ' *   var acc = roleMatrixGetAccess(userRole);\n',
         'RoleMatrix.gs: пример использования')

    sci = os.path.join(repo, 'scripts', 'StatusCodesInit.gs')
    edit(sci,
         '//   statusCodesDeployAll()       — рекомендованный порядок: Шаг 1\n'
         '//                                  (замена листа) + Шаг 2 (миграция\n'
         '//                                  «О»→«ОТ»). Запустить ОДИН раз —\n'
         '//                                  и деплой листов Task 298 готов.\n',
         '',
         'StatusCodesInit.gs: шапка — deployAll')
    edit(sci,
         '//   statusCodesStatus()          — диагностика: что сейчас в листе,\n'
         '//                                  отличия от эталона, сколько «О»\n'
         '//                                  осталось в «Записи_графика»,\n'
         '//                                  состояние шаблона 2, список\n'
         '//                                  резервных листов. Ничего не меняет.\n',
         '',
         'StatusCodesInit.gs: шапка — status')
    edit(sci,
         '//     остальные листы таблицы не читаются и не пишутся\n'
         '//     (statusCodesStatus читает ещё «Записи_графика»/«Дни_цикла»\n'
         '//     для диагностики — только чтение).\n',
         '//     остальные листы таблицы не читаются и не пишутся.\n',
         'StatusCodesInit.gs: БЕЗОПАСНОСТЬ')

    sdp = os.path.join(repo, 'scripts', 'SessionsDevicePolicy.gs')
    edit(sdp,
         ' *   sdpDebug()                             → диагностика в редакторе\n',
         '',
         'SessionsDevicePolicy.gs: шапка — sdpDebug')

    ut = os.path.join(repo, 'scripts', 'Utils.gs')
    edit(ut,
         'Ручные запуски из редактора (sdpDebug, init-скрипты)',
         'Ручные запуски из редактора (init-скрипты)',
         'Utils.gs: beginExecution — sdpDebug')
    edit(ut,
         ' * встроенные Admin.gs и setupTriggers) + новая функция.\n',
         ' * встроенные Admin.gs; ОПАСНАЯ копия функции настройки триггеров\n'
         ' * удалена в Task 513 — канон живёт в Code.gs) + новая функция.\n',
         'Utils.gs: историческая справка — без имени дубликата')

    # ---------- пост-ассерты .gs ----------
    print('=== пост-ассерты .gs ===')
    for fname, name in GS_FUNCS:
        src = io.open(os.path.join(repo, 'scripts', fname), encoding='utf-8').read()
        hits = [l for l in src.split('\n') if re.search(r'\b' + re.escape(name) + r'\b', l)]
        if hits:
            raise SystemExit('ПОСТ-АССЕРТ ПРОВАЛЕН: %s в %s: %s' % (name, fname, hits[:2]))
    # канон setupTriggers жив в Code.gs
    code = io.open(os.path.join(repo, 'scripts', 'Code.gs'), encoding='utf-8').read()
    if not re.search(r'^function\s+setupTriggers\s*\(', code, re.M):
        raise SystemExit('КАНОН setupTriggers не найден в Code.gs')
    print('  все чисты; канон setupTriggers жив в Code.gs')

    print()
    print('ИТОГО: index.html −%d строк, .gs −%d строк' % (total_removed, gs_total))
    print('ДЕТАЛИЗАЦИЯ:')
    for r in report:
        print('  ' + r)


if __name__ == '__main__':
    main()
