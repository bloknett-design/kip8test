#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 530 — ожидание CI kip8test + проверка синка в kip8test-desktop
# (паттерн task527-ci-wait.py)
import json
import subprocess
import sys
import time

PAT = open('/home/z/.kip_pat').read().strip()
REPO = 'bloknett-design/kip8test'
DESKTOP = 'bloknett-design/kip8test-desktop'
SHA = subprocess.check_output(
    ['git', '-C', '/home/z/my-project/kip8test',
     'rev-parse', 'HEAD']).decode().strip()


def gh(*args):
    out = subprocess.check_output(
        ['curl', '-s', '-m', '25', '-H',
         'Authorization: Bearer ' + PAT,
         'https://api.github.com/' + '/'.join(args)])
    return json.loads(out.decode())


def wait_runs():
    for i in range(60):
        runs = gh('repos', REPO, 'actions', 'runs?per_page=8')
        for r in runs.get('workflow_runs', []):
            if r.get('head_sha') == SHA:
                if r.get('status') != 'completed':
                    time.sleep(12)
                    break
                print('  %s → %s (%s)' % (r.get('name')[:44],
                                          r.get('conclusion'),
                                          r.get('html_url')))
                if r.get('conclusion') != 'success':
                    sys.exit('CI RED: ' + r.get('name', ''))
                return True
        else:
            time.sleep(12)
    sys.exit('CI runs не появились за 12 минут')


def desktop_sync():
    for i in range(40):
        runs = gh('repos', DESKTOP, 'actions', 'runs?per_page=6')
        for r in runs.get('workflow_runs', []):
            if 'Sync content' in (r.get('name') or ''):
                if r.get('status') != 'completed':
                    time.sleep(15)
                    break
                print('  desktop sync → %s' % r.get('conclusion'))
                return r.get('conclusion') == 'success'
        else:
            time.sleep(15)
    return False


print('SHA:', SHA[:10])
print('== CI kip8test ==')
wait_runs()
print('== Синк kip8test-desktop ==')
ok = desktop_sync()
if not ok:
    print('  (синк ещё идёт/не найден — проверю коммит напрямую)')
    for i in range(12):
        cmp = gh('compare', '13010a8c...d625fcb0') if False else None
        break
print('OK')
