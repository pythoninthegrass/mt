---
id: task-031.02
title: Integrate native file dialogs with library scanning
status: To Do
assignee: []
created_date: '2025-09-27 21:51'
labels:
  - integration
  - scanning
  - ui
dependencies:
  - task-031.01
parent_task_id: task-031
---

## Description

Connect PyWebView file dialogs with the existing LibraryManager to enable seamless library scanning from user-selected directories

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Directory selection dialog triggers library scan automatically
- [ ] #2 File selection dialog adds individual files to library
- [ ] #3 Scanning progress is reported to the UI
- [ ] #4 File validation prevents non-audio files from being processed
- [ ] #5 Integration maintains existing metadata extraction functionality
<!-- AC:END -->
