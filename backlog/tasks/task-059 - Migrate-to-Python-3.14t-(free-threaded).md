---
id: task-059
title: Migrate to Python 3.14t (free-threaded)
status: In Progress
assignee: []
created_date: '2025-10-21 06:58'
updated_date: '2025-10-21 07:02'
labels: []
dependencies: []
ordinal: 500
---

## Description

Incrementally upgrade Python from 3.11 to 3.14t (free-threaded), testing and fixing issues at each version step. This enables true parallelism by removing the Global Interpreter Lock (GIL).

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Upgrade to Python 3.12 and ensure all tests pass
- [ ] #2 Upgrade to Python 3.13 and ensure all tests pass
- [ ] #3 Upgrade to Python 3.14 (standard) and ensure all tests pass
- [ ] #4 Upgrade to Python 3.14t (free-threaded) and ensure all tests pass
- [ ] #5 Verify all functionality works correctly with free-threaded Python
- [ ] #6 Update documentation to reflect Python 3.14t requirement
<!-- AC:END -->


## Implementation Notes

## Upgrade Commands

From Astral's Python 3.14 announcement:
```bash
# Install Python 3.14t
uv python install 3.14t

# Upgrade project to use 3.14t
uv python upgrade 3.14t
```


## Tool Management

Continue using mise for uv management:
```bash
mise use uv
# This manages uv@0.8.8 in .tool-versions (NOT .python-version)
```

## Migration Strategy

1. **3.11 → 3.12**: Update version in mise/uv config, run tests, fix deprecations
2. **3.12 → 3.13**: Update version, test, address any new warnings
3. **3.13 → 3.14**: Update to standard 3.14, verify compatibility
4. **3.14 → 3.14t**: Switch to free-threaded, test for thread-safety issues

## Key Considerations

- **Thread Safety**: Free-threaded Python requires thread-safe code
- **Dependencies**: Verify all dependencies support 3.14t
- **Zig Modules**: Ensure pydust and Zig extensions work with 3.14t
- **VLC Bindings**: Test python-vlc with free-threaded interpreter
- **Performance**: Benchmark before/after for potential gains

## Testing Focus

- Unit tests (fast feedback loop)
- Property-based tests (invariant validation)
- E2E tests (integration validation)
- Manual UI testing with auto-reload
- Zig extension module functionality

## Reference

https://astral.sh/blog/python-3.14#free-threaded-python
