---
id: task-190
title: Remove Python backend and PEX sidecar (Phase 5)
status: In Progress
assignee: []
created_date: '2026-01-21 17:39'
updated_date: '2026-01-21 18:32'
labels:
  - rust
  - migration
  - cleanup
  - phase-5
  - optimization
dependencies:
  - task-173
  - task-180
  - task-181
  - task-182
  - task-183
  - task-184
  - task-185
  - task-186
  - task-187
  - task-188
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Final cleanup phase: Remove Python FastAPI backend, PEX build system, and all Python dependencies. Optimize Rust implementation and update documentation.

**Scope**:

**Code Removal**:
- Delete entire `backend/` directory (Python FastAPI code)
- Delete `backend/` symlink or reference in project root
- Remove PEX build taskfile (`taskfiles/pex.yml`)
- Remove sidecar management code (`src-tauri/src/sidecar.rs`)
- Update `tauri.conf.json` - remove `externalBin` configuration
- Remove Python from `pyproject.toml`
- Remove Python from `.tool-versions` and `mise` configuration
- Remove mutagen and other Python music libraries
- Clean up any Python-specific CI/CD configurations

**Build System Updates**:
- Update main `Taskfile.yml` to remove PEX tasks
- Remove `task pex:build` dependencies from Tauri build
- Update `task tauri:dev` to not start sidecar
- Update `task tauri:build` to not bundle sidecar
- Simplify build pipeline (no more multi-architecture PEX builds)

**Documentation Updates**:
- Update README.md to reflect Rust-only backend
- Update CLAUDE.md/AGENTS.md architecture overview
- Remove PEX sidecar documentation
- Update development setup instructions
- Update build instructions
- Document new Rust backend architecture

**Performance Optimization**:
- Profile Rust backend for hot paths
- Optimize database query performance
- Optimize metadata extraction performance
- Reduce memory allocations where possible
- Benchmark against Python baseline

**Final Verification**:
- Run full E2E test suite
- Test on all target platforms (macOS, Linux, Windows)
- Verify all features working without Python
- Check application startup time
- Verify memory usage improvements
- Test library scanning performance

**Documentation to Update**:
- `README.md`
- `CLAUDE.md` / `AGENTS.md`
- `docs/fastapi-to-rust-migration-analysis.md` (mark as completed)
- Development guides
- Build guides
- Architecture diagrams

**Estimated Effort**: 1 week
**Deliverable**: Python-free codebase with Rust-only backend
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Python backend code deleted
- [ ] #2 PEX build system removed
- [ ] #3 Python dependencies removed from project
- [ ] #4 Build system updated and simplified
- [ ] #5 Documentation updated
- [ ] #6 Performance benchmarks completed
- [ ] #7 E2E tests passing on all platforms
- [ ] #8 Application fully functional without Python
- [ ] #9 Startup time improved
- [ ] #10 Memory usage reduced
<!-- AC:END -->
