---
id: task-124
title: Clean up redundant backend directory structure
status: Done
assignee: []
created_date: '2026-01-14 02:14'
updated_date: '2026-01-18 23:50'
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
- [x] #1 app/backend/ directory removed
- [x] #2 taskfiles/tauri.yml BACKEND_DIR updated to backend/
- [x] #3 Sidecar builds successfully
- [x] #4 Backend runs correctly after cleanup
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Summary

Successfully cleaned up redundant backend directory structure:

### Changes Made

1. **Removed `app/backend/` directory** - This was a redundant wrapper that contained an old FastAPI implementation using `app/core/db`. The actual backend in use is `backend/` with the new modular architecture.

2. **Updated `pyproject.toml`** (line 145):
   - Changed: `packages = ["app/backend", "app/core", "app/utils"]`
   - To: `packages = ["app/core", "app/utils"]`
   - This removes the old backend from the hatch build wheel packages

3. **Updated `deno.jsonc`** (lines 32 and 74):
   - Removed: `"app/backend/**/*.py"` from lint and fmt exclude lists
   - These references are no longer needed since the directory doesn't exist

4. **Verified `taskfiles/tauri.yml`** (line 16):
   - Already correctly configured: `BACKEND_DIR: "{{.ROOT_DIR}}/backend"`
   - No changes needed - it was already pointing to the correct backend

### Testing

- Built PEX sidecar successfully: 23M binary at `src-tauri/bin/main-aarch64-apple-darwin`
- Tested backend health check: Server responded OK on port 8765
- Database migrations ran successfully
- Backend v1.0.0 started without errors

### Result

The project now has a clean structure with only one backend directory (`backend/`) containing the active FastAPI implementation with modular routes and services. The old redundant `app/backend/` wrapper has been removed.
<!-- SECTION:NOTES:END -->
