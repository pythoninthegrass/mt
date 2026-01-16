---
id: task-124
title: Clean up redundant backend directory structure
status: In Progress
assignee: []
created_date: '2026-01-14 02:14'
updated_date: '2026-01-16 22:22'
labels:
  - cleanup
  - backend
  - tech-debt
dependencies: []
priority: low
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
There are two backend directories that should be consolidated:

- `backend/` - The actual FastAPI backend with routes, services, models
- `app/backend/` - A thin wrapper that just imports from `backend/`

The `app/backend/` directory is redundant and was likely created during initial Tauri migration scaffolding. It only contains a `main.py` that imports and runs `backend.main:app`.

**Cleanup tasks:**
1. Remove `app/backend/` directory
2. Update `taskfiles/tauri.yml` to point `BACKEND_DIR` to `backend/` instead of `app/backend/`
3. Update any other references to `app/backend/`
4. Verify sidecar build still works after changes
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 app/backend/ directory removed
- [ ] #2 taskfiles/tauri.yml BACKEND_DIR updated to backend/
- [ ] #3 Sidecar builds successfully
- [ ] #4 Backend runs correctly after cleanup
<!-- AC:END -->
