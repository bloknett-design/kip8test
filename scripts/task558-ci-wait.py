#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 558 — ожидание CI kip8test (+ Pages + Sync). Токен — из окружения
GH_PAT (секрет в файлах репозитория НЕ хранится — push protection).
"""
import json
import os
import sys
import time
import urllib.request

PAT = os.environ.get('GH_PAT', '')
SHA = sys.argv[1] if len(sys.argv) > 1 else '9bd1d4f4'
REPO = sys.argv[2] if len(sys.argv) > 2 else 'kip8test'
HDRS = {'Authorization': 'Bearer ' + PAT,
        'Accept': 'application/vnd.github+json'}
if not PAT:
    print('GH_PAT не задан — выход')
    sys.exit(2)


def runs():
    url = ('https://api.github.com/repos/bloknett-design/%s/actions/runs'
           '?head_sha=%s&per_page=30' % (REPO, SHA))
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['workflow_runs']


def wait(name_kw, timeout_s=900):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        seen = False
        for r in runs():
            if name_kw.lower() in r['name'].lower():
                seen = True
                if r['status'] != 'completed':
                    break
                print('%s: %s' % (r['name'], r['conclusion']))
                return r['conclusion'] == 'success'
        time.sleep(15)
    print('%s: TIMEOUT' % name_kw)
    return False


def wait_all(name_kw, timeout_s=900):
    """Ждать ВСЕ прогоны с name_kw (CI, Pages, Sync) — все success."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        rs = [r for r in runs() if name_kw.lower() in r['name'].lower()]
        if rs and all(r['status'] == 'completed' for r in rs):
            for r in rs:
                print('%s: %s' % (r['name'], r['conclusion']))
            return all(r['conclusion'] == 'success' for r in rs)
        time.sleep(15)
    print('%s: TIMEOUT' % name_kw)
    return False


ok = wait_all('CI', 900)
print('CI kip8test: %s' % ('ЗЕЛЁНЫЙ' if ok else 'КРАСНЫЙ/таймаут'))
sys.exit(0 if ok else 1)
