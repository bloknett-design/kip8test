#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task527-ci-wait.py — ожидание CI-ранов Task 527 (kip8test затем kip8).
Использование: python3 task527-ci-wait.py <repo> <sha> [timeout_sec]
"""
import json
import sys
import time
import urllib.request

PAT = open('/home/z/.kip_pat').read().strip()
repo, sha = sys.argv[1], sys.argv[2]
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 600


def api(url):
    req = urllib.request.Request(
        url, headers={'Authorization': 'token ' + PAT,
                      'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def runs():
    return api('https://api.github.com/repos/bloknett-design/%s/actions/runs?head_sha=%s&per_page=20' % (repo, sha))['workflow_runs']


t0 = time.time()
seen = {}
while time.time() - t0 < timeout:
    rs = runs()
    for r in rs:
        seen[r['name']] = (r['status'], r['conclusion'])
    done = all(s == 'completed' for s, _ in seen.values()) and seen
    line = ' | '.join('%s: %s/%s' % (n, s, c or '-') for n, (s, c) in sorted(seen.items()))
    print('[%3ds] %s' % (int(time.time() - t0), line[:300]), flush=True)
    if done:
        ok = all(c in ('success', 'skipped') for _, c in seen.values())
        print('\nИТОГ %s @%s: %s' % (repo, sha[:8], 'SUCCESS' if ok else 'FAILURE'))
        sys.exit(0 if ok else 1)
    time.sleep(15)
print('\nТАЙМАУТ %s @%s' % (repo, sha[:8]))
sys.exit(2)
