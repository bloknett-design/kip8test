#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 509 — ПЕРЕНОС Task 508 («Кабельный журнал» — архив правок/удалений)
из kip8test@3cdfe79d в боевой kip8 ОДНИМ инкрементом kipia-v526→v527.
Метод — как Task 507: index.html КОПИЕЙ из точки kip8test + репо-патчи де-изоляции
(из диффа точки синхронизации kip8test@c9587f8a ↔ kip8@fcf3272 — ТОЛЬКО репо-специфика),
sw.js — свой + комментарий 508 + бамп, серверные эталоны/DEPLOY/тесты — копией с MAP версий.

Сервер (CableJournal.gs в Apps Script) УЖЕ развёрнут пользователем по DEPLOY-Task508
(«заменил содержимое — всё работает»): один деплой на оба приложения, серверных шагов НЕТ.

Фазы:
  1) index.html: копия kip8test@3cdfe79d + env-патч (14 ханков де-изоляции)
  2) sw.js: комментарий Task 508 + kipia-v526→kipia-v527
  3) scripts/CableJournal.gs + scripts/sync-cables.py: копии
  4) DEPLOY-Task508-cable-journal-archive.md: копия + адаптация под kip8
  5) тесты: бамп гардов v527→v528 / ассертов v526→v527, копии test-task508/505 (MAP),
     регистрация run-all.js
  6) контрольные сверки после каждой фазы (0 FAIL = обязательное условие)
"""
import subprocess, sys, re, pathlib

KT = pathlib.Path('/home/z/my-project/kip8test')
K8 = pathlib.Path('/home/z/my-project/kip8')
KT_REF = '3cdfe79d'          # точка Task 508 (feat + docs)
SYNC_KT, SYNC_K8 = 'c9587f8a', 'fcf3272'   # точки синхронизации (Task 507/508 зеркало)

fails = []

def git_show(repo, ref, path):
    r = subprocess.run(['git', '-C', str(repo), 'show', f'{ref}:{path}'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'git show {ref}:{path} в {repo} fail: {r.stderr[:200]}')
    return r.stdout

def check(cond, msg):
    print(('  OK  ' if cond else '  FAIL') + '  ' + msg)
    if not cond:
        fails.append(msg)

def replace_once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        check(False, f'{what}: ожидалось 1 вхождение, найдено {n}')
        return text, False
    return text.replace(old, new), True

# ── Фаза 1: index.html ────────────────────────────────────────────────
print('ФАЗА 1: index.html — копия + env-патч')
html_new = git_show(KT, KT_REF, 'index.html')
(K8 / 'index.html').write_text(html_new, encoding='utf-8')

# env-патч из диффа точек синхронизации (kt→k8 направление = де-изоляция)
kt_sync = git_show(KT, SYNC_KT, 'index.html')
k8_sync = git_show(K8, SYNC_K8, 'index.html')
patch = '/tmp/task509-env.patch'
with open(patch, 'w', encoding='utf-8') as f:
    f.write('--- a\n+++ b\n')
    import difflib
    dl = list(difflib.unified_diff(kt_sync.splitlines(True), k8_sync.splitlines(True), n=3))
    f.writelines(dl[2:])  # скинуть свой заголовок, оставить ханки
hunks = sum(1 for l in open(patch, encoding='utf-8') if l.startswith('@@'))
r = subprocess.run(['patch', '--fuzz=1', str(K8 / 'index.html'), patch],
                   capture_output=True, text=True)
check(r.returncode == 0, f'env-патч применён ({hunks} ханков): ' + r.stdout.strip().replace('\n', ' | '))
if r.returncode != 0:
    print(r.stderr[:800]); sys.exit(1)

# сверка: новый kip8/index.html отличается от kip8test@3cdfe79d ТОЛЬКО на env-ханки
after = (K8 / 'index.html').read_text(encoding='utf-8')
env_pairs = sum(1 for l in difflib.unified_diff(html_new.splitlines(), after.splitlines(), n=0)
                if l.startswith('@@'))
check(env_pairs == hunks, f'сверка: дифф нового kip8 ↔ kip8test = {env_pairs} ханков (ожидалось {hunks})')
check('isolateLocalStorage' not in after, 'изоляция localStorage отсутствует (kip8)')
check("DB_NAME = 'kip8-cache-v1'" in after, 'DB_NAME = kip8-cache-v1')
check('PB_FAV_KEY = \'kip8_phonebook_favorites\'' in after, 'phonebook-ключи без kip8test-префикса')
check('_excelModel' in after and '_splitArchived' in after, 'маркеры Task 508 клиента на месте')

# ── Фаза 2: sw.js ─────────────────────────────────────────────────────
print('ФАЗА 2: sw.js — Task 508 комментарий + v526→v527')
sw = (K8 / 'sw.js').read_text(encoding='utf-8')
old_line = "const CACHE_VERSION = 'kipia-v526';"
new_block = ("// Task 508: Кабельный журнал — архив: удалённые записи (_archived) скрыты\n"
             "// из печати/PDF, видны в Excel (блок «Архив»); сервер — CableJournal.gs.\n"
             "const CACHE_VERSION = 'kipia-v527';")
sw, ok = replace_once(sw, old_line, new_block, 'sw.js CACHE_VERSION')
if ok:
    (K8 / 'sw.js').write_text(sw, encoding='utf-8')
check(ok, 'sw.js: kipia-v526→kipia-v527 + комментарий 508')
check("kipia-v526" not in sw, 'sw.js: старой версии v526 больше нет')

# ── Фаза 3: серверные эталоны ─────────────────────────────────────────
print('ФАЗА 3: scripts/CableJournal.gs + scripts/sync-cables.py')
(K8 / 'scripts' / 'CableJournal.gs').write_text(git_show(KT, KT_REF, 'scripts/CableJournal.gs'), encoding='utf-8')
(K8 / 'scripts' / 'sync-cables.py').write_text(git_show(KT, KT_REF, 'scripts/sync-cables.py'), encoding='utf-8')
cj = (K8 / 'scripts' / 'CableJournal.gs').read_text(encoding='utf-8')
sc = (K8 / 'scripts' / 'sync-cables.py').read_text(encoding='utf-8')
check('_ensureArchiveColumns' in cj and '_userName' in cj, 'CableJournal.gs: маркеры Task 508 (архив-колонки, имя)')
check("'Удалён'" in cj, 'CableJournal.gs: причина «Удалён»')
check('skip' in sc and 'Архив' in sc, 'sync-cables.py: пропуск архивных строк в снимок')

# ── Фаза 4: DEPLOY-Task508 → kip8 ─────────────────────────────────────
print('ФАЗА 4: DEPLOY-Task508-cable-journal-archive.md — адаптация под kip8')
dep = git_show(KT, KT_REF, 'DEPLOY-Task508-cable-journal-archive.md')
subs = [
    ('в репозитории kip8test, деплой', 'в репозитории kip8 (перенос Task 509), деплой'),
    ('из репозитория kip8test\n**ЦЕЛИКОМ**', 'из репозитория kip8\n**ЦЕЛИКОМ**'),
    ('### 3. Клиент — GitHub Pages (автоматически)\n\nКоммиты kip8test уже в репозитории: SW `kipia-test-v730` (Ctrl+Shift+R ×1–2).\n**Перенос в kip8 — ПО КОМАНДЕ** (команды в заявке НЕ было; одним инкрементом\n`kipia-v526→v527` + та же замена CableJournal.gs на общем Apps Script уже\nвыполнена шагами 1–2 — сервер один на оба приложения).',
     '### 3. Клиент — GitHub Pages (автоматически)\n\nКоммиты kip8 в репозитории (Task 509): SW `kipia-v527` (Ctrl+Shift+R ×1–2).\nПеренос Task 508 в kip8 ВЫПОЛНЕН одним инкрементом `kipia-v526→v527`;\nсервер CableJournal.gs общий (шаги 1–2 уже выполнены по DEPLOY в kip8test —\nодин деплой Apps Script на оба приложения).'),
    ('(v730 сам\n  не активируется', '(v527 сам\n  не активируется'),
    ('истории git kip8test, commit перед Task 508', 'истории git kip8/kip8test, коммит перед Task 508'),
]
dep_ok = True
for old, new in subs:
    n = dep.count(old)
    if n != 1:
        dep_ok = False
        check(False, f'DEPLOY: подстановка «{old[:40]}…» — {n} вхождений')
    else:
        dep = dep.replace(old, new)
check(dep_ok, 'DEPLOY-Task508: все подстановки kip8test→kip8 применены')
(K8 / 'DEPLOY-Task508-cable-journal-archive.md').write_text(dep, encoding='utf-8')

# ── Фаза 5: тесты ─────────────────────────────────────────────────────
print('ФАЗА 5: тесты — бамп гардов/ассертов + MAP-копии + регистрация')
g_before = a_before = 0
touched = []
for p in sorted((K8 / 'tests').glob('*.js')):
    if p.name in ('test-task508.js',):   # ещё не существует; защита на будущее
        continue
    t = p.read_text(encoding='utf-8')
    t0 = t
    g_before += t.count('kipia-v527')
    t = t.replace('kipia-v527', 'kipia-v528')       # 1) гарды: следующая версия
    a_before += t.count('kipia-v526')
    t = t.replace('kipia-v526', 'kipia-v527')       # 2) ассерты: текущая версия
    if t != t0:
        p.write_text(t, encoding='utf-8')
        touched.append(p.name)
print(f'  бамп: {len(touched)} файлов (гарды v527→v528 ×{g_before}, ассерты v526→v527 ×{a_before})')
check(g_before == 162, f'гарды: {g_before} (ожидалось 162)')
check(a_before == 664, f'ассерты: {a_before} (ожидалось 664)')

# MAP-копии (ПОСЛЕ бампа — как Task 507: новые файлы пишутся сразу в целевые версии)
for name in ('test-task508.js', 'test-task505.js'):
    t = git_show(KT, KT_REF, f'tests/{name}')
    c30, c31 = t.count('kipia-test-v730'), t.count('kipia-test-v731')
    t = t.replace('kipia-test-v730', 'kipia-v527').replace('kipia-test-v731', 'kipia-v528')
    (K8 / 'tests' / name).write_text(t, encoding='utf-8')
    print(f'  MAP {name}: v730→v527 ×{c30}, v731→v528 ×{c31}')
    check(c30 > 0, f'{name}: MAP ассертов применён')

# регистрация run-all.js (после бампа)
ra = (K8 / 'tests' / 'run-all.js').read_text(encoding='utf-8')
anchor = "require('./test-task506.js');"
block = ("require('./test-task506.js');\n"
         "// Task 508: «Кабельный журнал» — архив правок/удалений:\n"
         "// сервер помечает удалённые записи («Удалён», кем, когда;\n"
         "// последний редактор), клиент: печать/PDF без архива,\n"
         "// Excel — с блоком «Архив». SW v527.\n"
         "require('./test-task508.js');")
ra, ok = replace_once(ra, anchor, block, 'run-all.js регистрация')
if ok:
    (K8 / 'tests' / 'run-all.js').write_text(ra, encoding='utf-8')
check(ok, 'run-all.js: test-task508.js зарегистрирован')

print()
if fails:
    print(f'ИТОГ: {len(fails)} FAIL'); [print('  -', f) for f in fails]; sys.exit(1)
print('ИТОГ: перенос файлов завершён, 0 FAIL. Далее: node tests/run-all.js в kip8.')
