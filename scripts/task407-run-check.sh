#!/bin/bash
# Task 407: запуск фонового http-сервера + browser-check одним вызовом
cd /home/z/my-project/kip8test
python3 -m http.server 8908 >/tmp/http8908.log 2>&1 &
SRVPID=$!
sleep 1.5
python3 scripts/task407-browser-check.py
EX=$?
kill $SRVPID 2>/dev/null
exit $EX
