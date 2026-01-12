---
id: task-090
title: 'P1: Create tauri-migration worktree'
status: Done
assignee: []
created_date: '2026-01-12 04:06'
updated_date: '2026-01-12 04:32'
labels:
  - infrastructure
  - phase-1
milestone: Tauri Migration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Use worktrunk to create a dedicated git worktree for the Tauri migration.

```bash
wt switch --create tauri-migration --base=main
```

This isolates migration work from the existing Tkinter codebase, enabling a hard-cut approach.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Worktree created at ../mt-tauri-migration (or similar)
- [x] #2 Branch tauri-migration exists and tracks main
- [x] #3 Can switch between worktrees with `wt switch`
<!-- AC:END -->
