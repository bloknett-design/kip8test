#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 531 — ожидание CI kip8test + проверка синка в kip8test-desktop
# (паттерн task530-ci-wait.py)
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
    for i in range(70):
        runs = gh('repos', REPO, 'actions', 'runs?per_page=10')
        for r in runs.get('workflow_runs', []):
            if r.get('head_sha') == SHA:
                if r.get('status') != 'completed':
                    time.sleep(12)
                    break
                print('  %s → %s' % ((r.get('name') or '')[:44],
                                     r.get('conclusion')))
                if r.get('conclusion') != 'success':
                    sys.exit('CI RED: ' + (r.get('name') or ''))
                return True
        else:
            time.sleep(12)
    sys.exit('CI runs не появились за 14 минут')


def desktop_sync():
    for i in range(50):
        runs = gh('repos', DESKTOP, 'actions', 'runs?per_page=8')
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
print('== kip8test CI ==')
wait_runs()
print('== kip8test-desktop sync ==')
ok = desktop_sync()
# итоговое число тестов зеркала из его CI-лога
try:
    runs = gh('repos', DESKTOP, 'actions', 'runs?per_page=8')
    for r in runs.get('workflow_runs', []):
        if r.get('name') == 'CI Tests' and r.get('status') == 'completed':
            jobs = gh('repos/%s/actions/runs/%d/jobs' % (DESKTOP, r['id']))
            for j in jobs.get('jobs', []):
                raw = subprocess.check_output(
                    ['curl', '-s', '-L', '-m', '60', '-H',
                     'Authorization: Bearer ' + PAT,
                     'https://api.github.com/repos/%s/actions/jobs/%d/logs'
                     % (DESKTOP, j['id'])]).decode('utf-8', 'replace')
                for line in raw.splitlines():
                    if 'Результат:' in line:
                        print('  зеркало: ' + line.strip()[:120])
            break
except Exception as e:
    print('  (лог зеркала не прочитан: %s)' % e)
sys.exit(0 if ok else 1)
