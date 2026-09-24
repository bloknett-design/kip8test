#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 408 — адаптация (часть 2): вставка методов года в VM-хосты
# после _renderWorkerCard (фикс экранирования '\\n' первого варианта).
import glob
import re
import io

host_re = re.compile(
    r"^([ \t]*)methodText\(INDEX_SRC, '_renderWorkerCard'\) \+ ',\\n' \+[ \t]*\n",
    re.M)

changed = []
for f in sorted(glob.glob('tests/*.js')):
    s = io.open(f, encoding='utf-8').read()
    m = host_re.search(s)
    if not m:
        continue
    indent = m.group(1)
    add = (indent + "methodText(INDEX_SRC, '_wtabYearOf') + ',\\n' +\n" +
           indent + "methodText(INDEX_SRC, '_wtabYearMin') + ',\\n' +\n" +
           indent + "methodText(INDEX_SRC, '_wtabYearNav') + ',\\n' +\n" +
           indent + "methodText(INDEX_SRC, '_wtabYearRecords') + ',\\n' +\n")
    s2 = host_re.sub(lambda mm: mm.group(0) + add, s, count=1)
    if s2 != s:
        io.open(f, 'w', encoding='utf-8').write(s2)
        changed.append(f)
print('хосты дополнены: %d файлов' % len(changed))
for f in changed:
    print('  ' + f)

# контроль: срез _renderWorkerCard больше не ссылается на trYStart
for f in sorted(glob.glob('tests/*.js')):
    s = io.open(f, encoding='utf-8').read()
    if 'trYStart' in s and 'test-task394' not in f:
        print('ВНИМАНИЕ: %s ещё содержит trYStart' % f)
