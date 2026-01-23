---
id: task-133
title: Convert test suite to cover Alpine.js frontend with Playwright MCP
status: Done
assignee:
  - Claude
created_date: '2026-01-14 19:30'
updated_date: '2026-01-15 03:11'
labels:
  - testing
  - playwright
  - frontend
  - alpine.js
  - tauri-migration
  - e2e
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The current test suite (35 Python pytest files) tests the legacy Python backend API directly, but doesn't cover the new Alpine.js frontend interactions in the Tauri migration. This task converts and supplements the existing test suite to:

1. Cover Alpine.js component interactions, stores (queue, player, library, ui), and reactive behaviors
2. Use Playwright MCP for a smaller, focused integration and E2E test suite
3. Maintain coverage of critical user workflows during the hybrid architecture phase (Python PEX sidecar + Tauri frontend)

**Context:** The application is in a transitional hybrid architecture:
- Frontend: Tauri + basecoat/Alpine.js (complete)
- Backend: Python FastAPI sidecar via PEX (temporary bridge)
- Current tests: 35 Python files (test_e2e_*.py, test_unit_*.py, test_props_*.py) testing Python API
- Target: Playwright tests covering Alpine.js UI + backend integration

**Value:** Ensures the migrated frontend works correctly, prevents regressions, and provides confidence during the incremental Rust backend migration.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Playwright test infrastructure is configured (playwright.config.js, test directory structure, npm scripts)
- [x] #2 Core user workflows have Playwright E2E coverage: play/pause, queue operations, track navigation, shuffle/loop modes
- [x] #3 Alpine.js store interactions are testable (queue, player, library, ui stores)
- [x] #4 Alpine.js component behaviors are tested (player-controls, library-browser, now-playing-view, sidebar)
- [x] #5 Playwright MCP integration is documented for interactive testing during development
- [x] #6 Test suite runs in CI/CD pipeline alongside existing Python tests
- [x] #7 Critical Python backend tests are preserved for PEX sidecar validation during hybrid phase
- [x] #8 Test coverage report shows equivalent or better coverage compared to legacy Python tests for covered workflows
- [x] #9 AGENTS.md is updated with Playwright test execution examples and best practices
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Phase 1: Playwright Infrastructure Setup
1. Install Playwright dependencies (@playwright/test)
2. Create playwright.config.js with Tauri app testing configuration
3. Set up test directory structure (tests/e2e/)
4. Add npm scripts for test execution

### Phase 2: Core E2E Test Implementation
5. Implement playback tests (play/pause, prev/next, progress bar)
6. Implement queue tests (add/remove, shuffle, loop, drag-drop)
7. Implement library tests (search, filter, sort, selection, context menu)
8. Implement sidebar tests (navigation, collapse, playlists)

### Phase 3: Alpine.js Store Testing
9. Implement store interaction tests using page.evaluate() to access Alpine stores

### Phase 4: Component Behavior Testing
10. Test player-controls, library-browser, now-playing-view, sidebar components

### Phase 5: Test Fixtures and Utilities
11. Create test fixtures (mock tracks, playlists)
12. Create test utilities (Alpine.js helpers, interaction helpers)

### Phase 6: Documentation and CI/CD
13. Document Playwright MCP usage in AGENTS.md
14. Update AGENTS.md with test execution examples and best practices
15. Set up CI/CD integration (GitHub Actions)

### Phase 7: Coverage and Validation
16. Generate and analyze coverage reports
17. Document preserved Python tests for PEX sidecar validation

### Key Files
- playwright.config.js (new)
- app/frontend/package.json (update)
- tests/e2e/*.spec.js (new)
- AGENTS.md (update)
- .github/workflows/test.yml (new)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Created playback.spec.js with comprehensive E2E tests covering play/pause, track navigation, progress bar, volume controls, and favorite status.

Created queue.spec.js with tests for queue management, shuffle/loop modes, drag-and-drop reordering, and queue navigation.

Created library.spec.js with tests for search, sorting, track selection, context menus, and section navigation.

Created sidebar.spec.js with tests for sidebar navigation, collapse/expand, search input, playlists section, and responsiveness.

Created stores.spec.js with comprehensive tests for all Alpine.js stores (player, queue, library, ui) and store reactivity.

Created GitHub Actions CI/CD workflow (test.yml) with parallel jobs for Playwright tests, Python tests, linting, and build verification.

Created tests/README.md documenting the test suite organization, Python test preservation strategy, coverage comparison, and CI/CD integration. All critical Python backend tests are identified and will be preserved during the hybrid architecture phase.

Added Taskfile.yml abstractions for Playwright test commands: test:e2e, test:e2e:ui, test:e2e:debug, test:e2e:headed, test:e2e:report, and test:all for running both Python and E2E tests.
<!-- SECTION:NOTES:END -->
