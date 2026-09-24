#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Task 404: element-screenshot окна мероприятий (для VLM-пруфа)
import sys, json, datetime
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

src = open('/home/z/my-project/kip8test/scripts/task404-browser-check.py', encoding='utf-8').read()
head = src.split('with sync_playwright() as p:')[0]
ns = {}
exec(head, ns)

PORT = 8905
with sync_playwright() as p:
    browser = p.chromium.launch()
    ns['ADMIN'] = False
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    ns['attach'](page, ctx, 'dark', 'vlm-ev')
    page.goto('http://localhost:%d/index.html' % PORT)
    page.wait_for_timeout(2500)
    page.evaluate("navigateTo('work-schedule')")
    page.wait_for_timeout(2500)
    el = page.query_selector('#wsEventsPanel')
    if el:
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        el.screenshot(path='/home/z/my-project/kip8test/task404-proof-events-window.png')
        print('saved: task404-proof-events-window.png')
    else:
        print('wsEventsPanel NOT FOUND')
        sys.exit(1)
    browser.close()
