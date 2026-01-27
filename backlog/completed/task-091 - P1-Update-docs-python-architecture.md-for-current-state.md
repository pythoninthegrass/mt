---
id: task-091
title: 'P1: Update docs/python-architecture.md for current state'
status: Done
assignee: []
created_date: '2026-01-12 04:06'
updated_date: '2026-01-24 22:28'
labels:
  - documentation
  - phase-1
milestone: Tauri Migration
dependencies: []
priority: high
ordinal: 97382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix inaccuracies in the architecture doc to reflect the actual codebase structure:

**Corrections needed:**
- Central orchestrator is `core/player/__init__.py` (package), not `core/player.py`
- DB layer is `core/db/` package facade, not single-file
- GUI is `core/gui/` package; `core/gui/music_player.py` is legacy stub
- Add API server architecture section (`api/server.py`)
- Document manager composition pattern (PlayerUIManager, PlayerWindowManager, etc.)
- Document Zig performance extension (`src/scan.zig`)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Central orchestrator section updated to reference core/player/ package
- [x] #2 Data layer section updated to reference core/db/ package
- [x] #3 API server section added with command surface and threading model
- [x] #4 Manager composition pattern documented
- [x] #5 Zig extension documented
<!-- AC:END -->
