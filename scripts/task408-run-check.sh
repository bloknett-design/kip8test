#!/bin/bash
# Task 408: запуск локального сервера + браузерной проверки ОДНИМ
# вызовом (урок Task 406: фоновый http.server убивается между
# вызовами Bash). Порт 8909.
cd /home/z/my-project/kip8test
python3 -m http.server 8909 >/dev/null 2>&1 &
SERVER_PID=$!
sleep 1.5
python3 scripts/task408-browser-check.py
RC=$?
kill $SERVER_PID 2>/dev/null
exit $RC
