# Test Suite Overview

This directory contains the test suite for the mt music player during its transition from Python/Tkinter to Tauri + Alpine.js.

## Test Organization

```
app/frontend/tests/         # Playwright E2E tests (NEW - Tauri/Alpine.js)
├── playback.spec.js
├── queue.spec.js
├── library.spec.js
├── sidebar.spec.js
├── stores.spec.js
└── fixtures/
    ├── test-data.js
    └── helpers.js

tests/                      # Legacy Python tests
├── test_e2e_*.py          # Legacy Python E2E tests
├── test_unit_*.py         # Legacy Python unit tests
└── test_props_*.py        # Legacy Python property tests
```

## Hybrid Architecture Testing Strategy

During the Tauri migration, the application runs with a hybrid architecture:
- **Frontend**: Tauri + basecoat/Alpine.js (complete)
- **Backend**: Python FastAPI sidecar via PEX (temporary bridge)

### Test Coverage Strategy

1. **Playwright E2E Tests** (`app/frontend/tests/`) - **PRIMARY**
   - Cover all user-facing functionality in the Alpine.js frontend
   - Test Alpine.js store interactions and component behaviors
   - Validate frontend-backend integration through the PEX sidecar
   - **Status**: ✅ Implemented

2. **Python Backend Tests** (`tests/test_*.py`) - **MAINTAINED FOR VALIDATION**
   - Critical Python tests are preserved to validate the PEX sidecar
   - Focus on backend API correctness during the hybrid phase
   - Will be gradually phased out as Rust backend replaces Python sidecar
   - **Status**: ⚠️ Preserved for backend validation

## Preserved Python Tests

The following Python tests remain critical during the hybrid architecture phase:

### Critical Backend Tests (Keep Running in CI)
- `test_unit_backend_database.py` - Database operations via sidecar
- `test_unit_api_client.py` - API client integration
- `test_e2e_playback.py` - Backend playback control validation
- `test_unit_metadata.py` - Audio metadata extraction
- `test_unit_scan.py` - Library scanning functionality

### Tests Superseded by Playwright (Can Be Deprecated)
- Any tests that directly test UI/Tkinter components
- Tests that only validate frontend behavior
- Tests that are now covered by Playwright E2E tests

### Deprecation Strategy
1. **Phase 1** (Current): Run both Playwright and critical Python tests in CI
2. **Phase 2**: As Rust backend features are implemented, remove corresponding Python tests
3. **Phase 3**: Once Python sidecar is fully replaced, remove all Python backend tests

## Running Tests

### Frontend E2E Tests (Playwright)
```bash
# From project root
npm run test:e2e
cd app/frontend && npm run test:e2e

# Interactive UI mode
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug

# Run specific test
cd app/frontend && npx playwright test tests/playback.spec.js
```

### Python Backend Tests
```bash
# All Python tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_unit_backend_database.py -v

# Critical backend tests only
uv run pytest tests/test_unit_backend_database.py tests/test_unit_api_client.py -v
```

## Test Coverage

### Current Coverage

**Playwright E2E Tests:**
- ✅ Playback controls (play/pause, prev/next, progress bar, volume)
- ✅ Queue management (add/remove, shuffle, loop modes, drag-drop)
- ✅ Library operations (search, filter, sort, selection, context menus)
- ✅ Sidebar navigation (sections, collapse/expand, playlists)
- ✅ Alpine.js stores (player, queue, library, ui)
- ✅ Component reactivity and state management

**Python Backend Tests (Preserved):**
- ✅ Database operations and migrations
- ✅ Audio metadata extraction (mutagen)
- ✅ Library scanning and file discovery
- ✅ API endpoint functionality
- ✅ Backend state management

### Coverage Comparison

| Feature Area          | Python Tests | Playwright Tests | Status |
|-----------------------|--------------|------------------|--------|
| Playback Controls     | ✅           | ✅               | Both   |
| Queue Management      | ✅           | ✅               | Both   |
| Library Browsing      | ❌           | ✅               | P only |
| Search/Filter         | ❌           | ✅               | P only |
| UI Interactions       | ❌           | ✅               | P only |
| Alpine.js Stores      | ❌           | ✅               | P only |
| Database Operations   | ✅           | ⚠️               | Py only|
| Audio Metadata        | ✅           | ⚠️               | Py only|
| File Scanning         | ✅           | ⚠️               | Py only|

**Legend:**
- ✅ = Covered
- ❌ = Not covered
- ⚠️ = Partially covered/indirect
- P only = Playwright only
- Py only = Python only
- Both = Covered by both test suites

## CI/CD Integration

Tests run automatically in GitHub Actions (`.github/workflows/test.yml`):

1. **Playwright E2E Tests** - Runs on every push/PR
2. **Python Backend Tests** - Runs critical backend validation tests
3. **Linting** - Deno (frontend) and Ruff (Python backend)
4. **Build Verification** - Frontend build and Rust check

## Contributing

### Adding New Tests

**For frontend features:**
- Add Playwright tests to `app/frontend/tests/`
- Follow existing patterns in `playback.spec.js`, `queue.spec.js`, etc.
- Use helper functions from `app/frontend/tests/fixtures/helpers.js`
- Document test coverage in this README

**For backend features:**
- If testing Python sidecar: Add Python tests to `tests/test_unit_*.py`
- If testing future Rust backend: Add Rust tests to `src-tauri/src/`

### Test Best Practices

1. Use descriptive test names: `should [action] when [condition]`
2. Follow AAA pattern: Arrange, Act, Assert
3. Keep tests focused and independent
4. Use test fixtures for reusable data
5. Wait for Alpine.js to be ready in Playwright tests
6. Mock external dependencies when appropriate

## Future Work

- [ ] Add coverage reporting for Playwright tests
- [ ] Migrate remaining Python E2E tests to Playwright
- [ ] Add visual regression testing
- [ ] Implement Rust backend tests as features are migrated
- [ ] Phase out Python tests as Rust backend replaces sidecar
