#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 535 — ожидание CI kip8test (+ Pages). Токен — из окружения
GH_PAT (секрет в файлах репозитория НЕ хранится — push protection).
"""
import json
import os
import sys
import time
import urllib.request

PAT = os.environ.get('GH_PAT', '')
SHA = sys.argv[1] if len(sys.argv) > 1 else 'f4536289429f7e4ff116b43505be75625e9a2443'
REPO = sys.argv[2] if len(sys.argv) > 2 else 'kip8test'
HDRS = {'Authorization': 'Bearer ' + PAT,
        'Accept': 'application/vnd.github+json'}
if not PAT:
    print('GH_PAT не задан — выход')
    sys.exit(2)


def runs():
    url = ('https://api.github.com/repos/bloknett-design/%s/actions/runs'
           '?head_sha=%s&per_page=20' % (REPO, SHA))
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['workflow_runs']


def wait(name_kw, timeout_s=600):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        for r in runs():
            if name_kw in r['name']:
                if r['status'] != 'completed':
                    time.sleep(15)
                    break
                print('%s: %s' % (r['name'], r['conclusion']))
                return r['conclusion'] == 'success'
        else:
            time.sleep(15)
    print('%s: TIMEOUT' % name_kw)
    return False


ok_ci = wait('CI Tests')
ok_pages = wait('pages')
print('CI Tests: %s | Pages: %s' % (ok_ci, ok_pages))
sys.exit(0 if (ok_ci and ok_pages) else 1)
