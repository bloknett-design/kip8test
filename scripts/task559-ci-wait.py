#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 559 — ожидание CI kip8test (Tests + Pages + Sync) и зеркала
kip8test-desktop. Репозитории публичны для API — токен не нужен
(падение 403 rate-limit — перезапуск с GH_PAT в окружении)."""
import json
import os
import sys
import time
import urllib.request

SHA = '103ca85'
# фильтр head_sha в API требует ПОЛНЫЙ sha (короткий даёт 0 прогонов —
# урок Task 559); полный — из git при запуске, фолбэк — константа
import subprocess
try:
    SHA = subprocess.check_output(
        ['git', '-C', '/home/z/my-project/kip8test', 'rev-parse', 'HEAD'],
        text=True).strip()
except Exception:
    pass
T0 = time.time()


def api(url):
    hdrs = {'Accept': 'application/vnd.github+json'}
    pat = os.environ.get('GH_PAT', '')
    if pat:
        hdrs['Authorization'] = 'Bearer ' + pat
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def runs(repo, sha=None):
    url = ('https://api.github.com/repos/bloknett-design/%s/actions/runs'
           '?per_page=15' % repo)
    if sha:
        url += '&head_sha=' + sha
    return api(url)['workflow_runs']


def wait_all(repo, sha, kws, timeout_s=1200):
    while time.time() - T0 < timeout_s:
        try:
            rs = runs(repo, sha)
        except Exception as e:
            print('  (api: %s)' % e)
            time.sleep(20)
            continue
        todo = []
        for kw in kws:
            hits = [r for r in rs if kw.lower() in r['name'].lower()]
            if hits and all(r['status'] == 'completed' for r in hits):
                for r in hits:
                    print('  [%s] %s: %s (%s)' % (repo, r['name'],
                        r['conclusion'], r['id']))
                if any(r['conclusion'] != 'success' for r in hits):
                    return False
            else:
                todo.append(kw)
        if not todo:
            return True
        time.sleep(15)
    print('  [%s] TIMEOUT: %s' % (repo, todo))
    return False


def wait_mirror(timeout_s=1200):
    """Зеркало: ждать НОВЫЙ CI-прогон (создан после старта скрипта)."""
    while time.time() - T0 < timeout_s:
        try:
            rs = [r for r in runs('kip8test-desktop')
                  if 'CI' in r['name'] and r['created_at'] > '2026-11-25T04:15']
            if rs and all(r['status'] == 'completed' for r in rs):
                for r in rs:
                    print('  [kip8test-desktop] %s: %s (%s, head %s)' % (
                        r['name'], r['conclusion'], r['id'],
                        r['head_sha'][:7]))
                return all(r['conclusion'] == 'success' for r in rs)
        except Exception as e:
            print('  (api: %s)' % e)
        time.sleep(20)
    print('  [kip8test-desktop] TIMEOUT')
    return False


ok1 = wait_all('kip8test', SHA, ['CI', 'pages', 'sync'])
print('kip8test (CI+Pages+Sync): %s' % ('ЗЕЛЁНЫЙ' if ok1 else 'КРАСНЫЙ/таймаут'))
if not ok1:
    sys.exit(1)
ok2 = wait_mirror()
print('kip8test-desktop (CI): %s' % ('ЗЕЛЁНЫЙ' if ok2 else 'КРАСНЫЙ/таймаут'))
sys.exit(0 if ok2 else 1)
