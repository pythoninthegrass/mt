---
id: task-098
title: 'P3: Package Python backend as PEX sidecar'
status: To Do
assignee: []
created_date: '2026-01-12 04:07'
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
Build the Python backend as a PEX file for Tauri sidecar distribution.

**Build script:**
```bash
#!/bin/bash
# build_pex.sh

# Detect platform
ARCH=$(uname -m)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

if [ "$OS" = "darwin" ]; then
    TARGET="$ARCH-apple-darwin"
elif [ "$OS" = "linux" ]; then
    TARGET="$ARCH-unknown-linux-gnu"
fi

pex backend/ \
    -r backend/requirements.txt \
    -o src-tauri/binaries/mt-backend-$TARGET \
    -m backend.main:run \
    --python-shebang="/usr/bin/env python3"
```

**Tauri configuration:**
```json
// tauri.conf.json
{
  "bundle": {
    "externalBin": ["binaries/mt-backend"]
  }
}
```

**Sidecar launch in Rust:**
- Spawn PEX with dynamic port
- Wait for "SERVER_READY" on stdout
- Store port for frontend API calls
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 PEX builds successfully for macOS (arm64 and x86_64)
- [ ] #2 PEX runs standalone and serves API
- [ ] #3 Tauri can spawn PEX as sidecar
- [ ] #4 Sidecar readiness detection works
- [ ] #5 Dynamic port allocation works
<!-- AC:END -->
