---
id: task-206
title: Fix log export soft lock and add .log file extension
status: Done
assignee: []
created_date: '2026-01-25 22:10'
updated_date: '2026-01-25 22:16'
labels:
  - bug
  - backend
  - ui-responsiveness
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
When users export logs, the application soft locks with a spinning beach ball cursor, making the app unresponsive. Additionally, the exported file should use a `.log` extension instead of the current extension for better file type recognition.

**Current Behavior:**
- Exporting logs causes the app to become unresponsive with a beach ball cursor
- Exported file doesn't have a `.log` extension

**Expected Behavior:**
- Log export should be non-blocking and keep the UI responsive
- Exported file should have a `.log` extension
- User should receive feedback when export is complete

**User Value:**
Users can export logs for troubleshooting without freezing the application, and the exported files will be properly recognized as log files by the system.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Log export operation does not block the UI thread
- [x] #2 App remains responsive during log export with no beach ball cursor
- [x] #3 Exported log file has a .log extension
- [x] #4 User receives confirmation when export completes successfully
- [x] #5 Export errors are handled gracefully with user-friendly messages
- [x] #6 Playwright E2E test verifies log export doesn't freeze the UI
- [x] #7 Playwright E2E test verifies exported file has correct .log extension
<!-- AC:END -->
