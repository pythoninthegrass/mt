---
id: task-098
title: 'P3: Package Python backend as PEX sidecar'
status: Done
assignee: []
created_date: '2026-01-12 04:07'
updated_date: '2026-01-13 07:59'
labels:
  - python
  - packaging
  - phase-3
milestone: Tauri Migration
dependencies:
  - task-097
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Build the Python backend as a PEX SCIE (self-contained executable) for Tauri sidecar distribution using the `task pex:*` workflow.

**Build Commands:**
```bash
# Check dependencies
task pex:check-deps

# Build for Apple Silicon (arm64)
task pex:build:arm64

# Build for Intel (x86_64)
task pex:build:x64

# Build for current architecture
task pex:build
```

**Output Locations:**
- `src-tauri/bin/main-aarch64-apple-darwin` (Apple Silicon)
- `src-tauri/bin/main-x86_64-apple-darwin` (Intel)

**Runtime Configuration (Environment Variables):**
- `MT_API_HOST`: API server host (default: `127.0.0.1`)
- `MT_API_PORT`: API server port (default: `8765`)
- `MT_DB_PATH`: SQLite database path (default: `./mt.db`)

**Test Sidecar:**
```bash
# Run standalone test
task pex:test

# Or manually:
MT_API_PORT=8765 ./src-tauri/bin/main-aarch64-apple-darwin
curl http://127.0.0.1:8765/api/health
```

**Tauri Configuration:**
```json
// tauri.conf.json
{
  "bundle": {
    "externalBin": ["bin/main"]
  }
}
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `task pex:build:arm64` builds successfully
- [x] #2 `task pex:build:x64` builds successfully (or documents cross-compile limitation)
- [x] #3 PEX runs standalone: `MT_API_PORT=8765 ./src-tauri/bin/main-aarch64-apple-darwin`
- [x] #4 Health endpoint responds: `curl http://127.0.0.1:8765/api/health`
- [x] #5 Environment variables configure runtime behavior
<!-- AC:END -->
