#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 535 — ожидание синка kip8test→desktop и CI десктопа.
Шаги: (1) в kip8test появляется completed sync-workflow на SHA пуша;
(2) в kip8test-desktop приходит bot-коммит; (3) его CI зелёный.
Токен — из окружения GH_PAT (в файлах НЕ хранится)."""
import json
import os
import sys
import time
import urllib.request

PAT = os.environ.get('GH_PAT', '')
SRC_SHA = sys.argv[1]           # SHA feat-коммита в kip8test
HDRS = {'Authorization': 'Bearer ' + PAT,
        'Accept': 'application/vnd.github+json'}
if not PAT:
    print('GH_PAT не задан — выход')
    sys.exit(2)


def api(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def runs(repo, sha=None):
    url = ('https://api.github.com/repos/bloknett-design/%s/actions/runs'
           '?per_page=30' % repo)
    if sha:
        url += '&head_sha=' + sha
    try:
        return api(url)['workflow_runs']
    except Exception:
        return []


def wait_kw(repo, sha, name_kw, timeout_s=900):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        for r in runs(repo, sha):
            if name_kw in r['name']:
                if r['status'] != 'completed':
                    time.sleep(15)
                    break
                print('%s @ %s: %s' % (r['name'], r['head_sha'][:8],
                                       r['conclusion']))
                return r['conclusion'] == 'success'
        else:
            time.sleep(15)
    print('%s @ %s: TIMEOUT' % (name_kw, sha[:8]))
    return False


# 1) sync-воркфлоу на нашем SHA в kip8test
ok_sync = wait_kw('kip8test', SRC_SHA, 'sync')

# 2) bot-коммит в kip8test-desktop
bot_sha = None
t0 = time.time()
while time.time() - t0 < 600 and not bot_sha:
    try:
        commits = api('https://api.github.com/repos/bloknett-design/'
                      'kip8test-desktop/commits?per_page=5')
        for c in commits:
            msg = c['commit']['message'].lower()
            if 'sync' in msg and SRC_SHA[:8] in c['commit']['message'].lower():
                bot_sha = c['sha']
                print('bot-коммит kip8test-desktop: %s — %s'
                      % (bot_sha[:8], c['commit']['message'].split('\n')[0][:90]))
                break
    except Exception as e:
        print('  (повтор: %s)' % e)
    if not bot_sha:
        time.sleep(20)

if not bot_sha:
    print('bot-коммит НЕ найден за 10 мин')
    sys.exit(1)

# 3) CI десктопа на bot-коммите
ok_ci = wait_kw('kip8test-desktop', bot_sha, 'CI')
ok_build = wait_kw('kip8test-desktop', bot_sha, 'Build')
print('sync: %s | desktop CI: %s | desktop Build: %s'
      % (ok_sync, ok_ci, ok_build))
sys.exit(0 if (ok_sync and ok_ci and ok_build) else 1)
