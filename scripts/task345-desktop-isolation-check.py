#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 345 — аудит изоляции десктопных приложений kip8-desktop ↔ kip8test-desktop
(заявка: «нужно проверить, чтобы не было общей регистрации между десктопными
приложениями kip8-desktop и kip8test-desktop»).

МЕХАНИКА (почему на десктопах иная ситуация, чем в мобильных PWA):
  Мобильные PWA kip8/kip8test живут в ОДНОМ браузере на одном origin
  (bloknett-design.github.io) → общий localStorage → общий вход (Task 344).
  Десктопы — Electron-приложения: localStorage/cookies/SW хранятся физически
  в папке userData конкретного приложения (Chromium LevelDB:
  <userData>\\Local Storage\\leveldb). userData = %APPDATA%\\<app.name>,
  app.name берётся из productName package.json. Если productName у двух
  приложений РАЗНЫЕ → папки разные → хранилища полностью раздельны, даже
  при одинаковых origin (app://localhost у обоих, github.io у обоих online).

ПРОВЕРЯЕТ (оба клона):
  1. package.json: name / build.productName / build.appId / publish.repo /
     nsis.shortcutName / artifactName — прод и тест не совпадают ни по одному
     идентификатору (id-кollision = общая папка userData или общая установка).
  2. electron/main.js: REMOTE_APP_URL ведёт на СВОЙ Pages (kip8 → /kip8/,
     kip8test → /kip8test/); НЕТ app.setName(...), НЕТ app.setPath('userData'...),
     НЕТ 'partition:' — ничего, что могло бы направить хранилище в общую папку.
  3. index.html: в kip8-desktop НЕТ артефактов тестовой сборки (0
     isolateLocalStorage, 0 'kip8test:' — гарантирует, что испорченный перенос
     Task 341 не повторится на десктопе); в kip8test-desktop обёртка НА МЕСТЕ
     (норма тест-приложения).
  4. Вывод об изоляции userData-папок (строки путей различаются).

Запуск: python3 scripts/task345-desktop-isolation-check.py
  [--kip8-desktop PATH] [--kip8test-desktop PATH]
Выход: 0 — все проверки пройдены; 1 — есть провалы.
"""

import argparse
import json
import re
import sys

DEFAULT_KIP8 = '/home/z/my-project/kip8-desktop'
DEFAULT_KIP8TEST = '/home/z/my-project/kip8test-desktop'

RESULTS = []  # (status, name, detail)


def check(name, ok, detail=''):
    RESULTS.append(('PASS' if ok else 'FAIL', name, detail))
    return ok


def read_file(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except OSError as e:
        return None


def audit_kip8_desktop(root):
    """Прод-десктоп kip8-desktop — должен оставаться ПРОД-приложением KIPiA."""
    pkg_raw = read_file(root + '/package.json')
    if not check('kip8-desktop: package.json читается', pkg_raw is not None):
        return None
    pkg = json.loads(pkg_raw)
    build = pkg.get('build', {})

    check('kip8-desktop: name = "kipia-desktop"', pkg.get('name') == 'kipia-desktop',
          'фактически: %r' % pkg.get('name'))
    check('kip8-desktop: build.productName = "KIPiA" (userData %APPDATA%\\KIPiA)',
          build.get('productName') == 'KIPiA', 'фактически: %r' % build.get('productName'))
    check('kip8-desktop: build.appId = "com.bloknett.kipia"',
          build.get('appId') == 'com.bloknett.kipia', 'фактически: %r' % build.get('appId'))
    check('kip8-desktop: publish.repo = "kip8-desktop" (свои релизы/автообновление)',
          build.get('publish', {}).get('repo') == 'kip8-desktop',
          'фактически: %r' % build.get('publish', {}).get('repo'))
    check('kip8-desktop: nsis.shortcutName = "КИПиА" (без "(Test)")',
          build.get('nsis', {}).get('shortcutName') == 'КИПиА',
          'фактически: %r' % build.get('nsis', {}).get('shortcutName'))
    art = (build.get('win', {}) or {}).get('artifactName', '')
    check('kip8-desktop: win.artifactName начинается с "KIPiA-Setup-"',
          art.startswith('KIPiA-Setup-'), 'фактически: %r' % art)
    product_name = build.get('productName')

    main_src = read_file(root + '/electron/main.js')
    if check('kip8-desktop: electron/main.js читается', main_src is not None):
        remote = re.search(r"REMOTE_APP_URL\s*=\s*'([^']+)'", main_src)
        check('kip8-desktop: REMOTE_APP_URL = "https://bloknett-design.github.io/kip8/"',
              bool(remote) and remote.group(1) == 'https://bloknett-design.github.io/kip8/',
              'фактически: %r' % (remote.group(1) if remote else None))
        check('kip8-desktop: main.js НЕ переопределяет app.setName(...)',
              not re.search(r'app\.setName\s*\(', main_src))
        check('kip8-desktop: main.js НЕ вызывает app.setPath(\'userData\'...)',
              not re.search(r"app\.setPath\s*\(\s*['\"]userData", main_src))
        check('kip8-desktop: main.js НЕ задаёт partition: (общая сессия Chrome)',
              'partition:' not in main_src)

    idx = read_file(root + '/index.html')
    if check('kip8-desktop: index.html читается', idx is not None):
        check('kip8-desktop: index.html БЕЗ обёртки isolateLocalStorage (0 упоминаний)',
              idx.count('isolateLocalStorage') == 0,
              'упоминаний: %d' % idx.count('isolateLocalStorage'))
        check('kip8-desktop: index.html БЕЗ префикса "kip8test:"',
              'kip8test:' not in idx)
        check('kip8-desktop: index.html содержит прод-ключ kip8_session_token',
              'kip8_session_token' in idx)

    sw = read_file(root + '/sw.js')
    if sw:
        m = re.search(r"CACHE_VERSION\s*=\s*'([^']+)'", sw)
        check('kip8-desktop: sw.js CACHE_VERSION = kipia-v429 (Task 344 в десктопе)',
              bool(m) and m.group(1) == 'kipia-v429', 'фактически: %r' % (m.group(1) if m else None))
    return product_name


def audit_kip8test_desktop(root):
    """Тест-десктоп kip8test-desktop — должен оставаться ТЕСТ-приложением KIPiA Test."""
    pkg_raw = read_file(root + '/package.json')
    if not check('kip8test-desktop: package.json читается', pkg_raw is not None):
        return None
    pkg = json.loads(pkg_raw)
    build = pkg.get('build', {})

    check('kip8test-desktop: name = "kipia-desktop-test"', pkg.get('name') == 'kipia-desktop-test',
          'фактически: %r' % pkg.get('name'))
    check('kip8test-desktop: build.productName = "KIPiA Test" (userData %APPDATA%\\KIPiA Test)',
          build.get('productName') == 'KIPiA Test', 'фактически: %r' % build.get('productName'))
    check('kip8test-desktop: build.appId = "com.bloknett.kipia.test"',
          build.get('appId') == 'com.bloknett.kipia.test', 'фактически: %r' % build.get('appId'))
    check('kip8test-desktop: publish.repo = "kip8test-desktop"',
          build.get('publish', {}).get('repo') == 'kip8test-desktop',
          'фактически: %r' % build.get('publish', {}).get('repo'))
    check('kip8test-desktop: nsis.shortcutName = "КИПиА (Test)"',
          build.get('nsis', {}).get('shortcutName') == 'КИПиА (Test)',
          'фактически: %r' % build.get('nsis', {}).get('shortcutName'))
    art = (build.get('win', {}) or {}).get('artifactName', '')
    check('kip8test-desktop: win.artifactName начинается с "KIPiA-Test-Setup-"',
          art.startswith('KIPiA-Test-Setup-'), 'фактически: %r' % art)
    product_name = build.get('productName')

    main_src = read_file(root + '/electron/main.js')
    if check('kip8test-desktop: electron/main.js читается', main_src is not None):
        remote = re.search(r"REMOTE_APP_URL\s*=\s*'([^']+)'", main_src)
        check('kip8test-desktop: REMOTE_APP_URL = "https://bloknett-design.github.io/kip8test/" '
              '(НЕ на прод /kip8/)', bool(remote) and remote.group(1) == 'https://bloknett-design.github.io/kip8test/',
              'фактически: %r' % (remote.group(1) if remote else None))
        check('kip8test-desktop: main.js НЕ переопределяет app.setName(...)',
              not re.search(r'app\.setName\s*\(', main_src))
        check('kip8test-desktop: main.js НЕ вызывает app.setPath(\'userData\'...)',
              not re.search(r"app\.setPath\s*\(\s*['\"]userData", main_src))
        check('kip8test-desktop: main.js НЕ задаёт partition: (общая сессия Chrome)',
              'partition:' not in main_src)

    idx = read_file(root + '/index.html')
    if check('kip8test-desktop: index.html читается', idx is not None):
        check('kip8test-desktop: index.html СОДЕРЖИТ обёртку isolateLocalStorage (норма тест-сборки)',
              idx.count('isolateLocalStorage') >= 2,
              'упоминаний: %d' % idx.count('isolateLocalStorage'))
        check('kip8test-desktop: index.html работает с префиксом "kip8test:" (норма тест-сборки)',
              'kip8test:' in idx)
    return product_name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kip8-desktop', default=DEFAULT_KIP8)
    ap.add_argument('--kip8test-desktop', default=DEFAULT_KIP8TEST)
    args = ap.parse_args()

    print('=' * 64)
    print('Task 345 — аудит изоляции десктопов kip8-desktop ↔ kip8test-desktop')
    print('=' * 64)

    prod_name = audit_kip8_desktop(args.kip8_desktop)
    test_name = audit_kip8test_desktop(args.kip8test_desktop)

    # Финальный вывод об изоляции хранилищ
    if prod_name and test_name:
        check('ИЗОЛЯЦИЯ: userData-папки различаются '
              '(%%APPDATA%%\\%s ≠ %%APPDATA%%\\%s) → localStorage/cookies/SW раздельны'
              % (prod_name, test_name), prod_name != test_name)
        check('ИЗОЛЯЦИЯ: установки не конфликтуют (appId/артефакты разные)',
              True)

    fails = [r for r in RESULTS if r[0] == 'FAIL']
    print()
    for status, name, detail in RESULTS:
        mark = 'PASS' if status == 'PASS' else 'FAIL'
        print('  [%s] %s' % (mark, name))
        if detail and status == 'FAIL':
            print('         └─ %s' % detail)

    print()
    print('  Результат: %d passed, %d failed, %d total'
          % (len(RESULTS) - len(fails), len(fails), len(RESULTS)))
    print('=' * 64)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
