---
id: task-160
title: Add @tauri tags and E2E_MODE env var for fast default test runs
status: To Do
assignee: []
created_date: '2026-01-17 01:54'
labels:
  - testing
  - dx
  - playwright
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Speed up E2E test runs by defaulting to WebKit-only and skipping Tauri-dependent tests.

## Problem
Running `task npm:test:e2e` executes all browsers (chromium/webkit/firefox) and includes playback/queue tests that require Tauri IPC/native audio. These tests fail in browser mode, wasting time and producing 105 false failures.

## Solution
1. Tag Tauri-dependent test suites with `@tauri` in their describe block titles
2. Add `E2E_MODE` env var to control test scope:
   - `fast` (default): WebKit only, skip `@tauri` tests
   - `full`: All browsers, skip `@tauri` tests  
   - `tauri`: All browsers, include `@tauri` tests (for future Tauri test harness)

## Files to modify
- `app/frontend/tests/playback.spec.js` - Add `@tauri` to all 3 describe blocks
- `app/frontend/tests/queue.spec.js` - Add `@tauri` to all 7 describe blocks
- `app/frontend/playwright.config.js` - Add grepInvert logic based on E2E_MODE
- `taskfiles/npm.yml` - Update test:e2e task to respect E2E_MODE

## Test suites to tag @tauri
**playback.spec.js:**
- Playback Controls
- Volume Controls
- Playback Parity Tests

**queue.spec.js:**
- Queue Management
- Shuffle and Loop Modes
- Queue Reordering (Drag and Drop)
- Queue View Navigation
- Play Next and Add to Queue (task-158)
- Queue Parity Tests
- Loop Mode Tests (task-146)

## Expected outcome
- `task npm:test:e2e` runs fast (WebKit + browser-safe tests only)
- `E2E_MODE=full task npm:test:e2e` runs all browsers
- `E2E_MODE=tauri task npm:test:e2e` includes Tauri-dependent tests
<!-- SECTION:DESCRIPTION:END -->
