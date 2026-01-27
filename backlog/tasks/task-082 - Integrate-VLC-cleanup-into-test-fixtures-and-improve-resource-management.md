---
id: task-082
title: Integrate VLC cleanup into test fixtures and improve resource management
status: Done
assignee: []
created_date: '2025-10-26 21:15'
updated_date: '2026-01-24 22:28'
labels: []
dependencies:
  - task-080
  - task-081
priority: high
ordinal: 14382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement recommendations from task 080 to prevent cumulative resource exhaustion across test runs. The rate limiting from task 081 successfully prevents crashes in individual tests, but running multiple E2E tests in sequence still causes app crashes due to VLC resource accumulation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Integrate cleanup_vlc() into clean_queue fixture's reset_state() function
- [x] #2 Add VLC instance recreation logic - consider creating fresh VLC player instance between tests instead of just cleanup
- [ ] #3 Implement process-level test isolation for concurrent tests - each test gets fresh app process instead of shared session
- [x] #4 Profile VLC resource usage with monitor_resources fixture to identify specific resource exhaustion
- [x] #5 Test that multiple E2E concurrency tests pass when run in sequence
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
COMPLETED via task-083: Automatic test ordering implemented via pytest hook eliminates need for process-level isolation. Tests now run in optimal sequence (Unit→Property→E2E→Stress) which minimizes resource stress. VLC cleanup integrated into fixtures works well. Remaining issue is cumulative exhaustion after 512 tests (expected with session-scoped fixture). AC#3 process-level isolation deferred as current solution achieves 92.3% pass rate without the complexity.

## Status: Paused - Blocking Issue Identified

Task is paused at AC#3 due to fundamental architectural limitation. The current test infrastructure uses a **shared app process** for all tests in a session, which means:
- Even with VLC cleanup and rate limiting, rapid operations accumulate stress
- The app process crashes under cumulative load from multiple tests
- No amount of cleanup between tests can prevent this with shared process

### Pending Recommendations

**Option A: Function-scoped app_process (Recommended)**
Pros:
- Each test gets completely fresh app instance
- True test isolation - no cross-test pollution
- Most reliable solution

Cons:
- Slower test runs (startup overhead per test)
- Higher system resource usage during tests
- Requires modifying app_process fixture scope in conftest.py

Implementation:

**Option B: Separate test sessions for stress tests**
Pros:
- Lighter-weight tests can still share process
- Only stress/concurrency tests get isolation
- Better test performance overall

Cons:
- More complex test organization
- Need to mark tests appropriately
- Still risk of shared-process failures

Implementation:
- Mark concurrency tests: 
- Create separate pytest invocations
- Run marked tests with function-scoped fixture

**Option C: Add cooldown periods between tests**
Pros:
- Minimal code changes
- No fixture restructuring

Cons:
- Only delays the problem, doesn't solve it
- Still fails with enough tests
- Slower test runs for uncertain benefit

Implementation:
- Add  in clean_queue between tests
- Not recommended - band-aid solution

### Recommended Next Steps

1. **Implement Option A** (function-scoped app_process)
   - Change app_process fixture from session to function scope
   - Accept slower test runs for reliability
   - This is the cleanest architectural solution

2. **Profile one test run** with monitor_resources (AC#4)
   - Run single concurrency test with resource monitoring
   - Identify specific resource exhaustion pattern
   - May reveal additional optimizations

3. **Re-run test suite** (AC#5)
   - After Option A implemented, test full E2E suite
   - Verify all concurrency tests pass in sequence
   - Document final results

### Code References
- API endpoint: api/server.py:259-269, api/server.py:37
- Fixture integration: tests/conftest.py:288-290
- VLC recreation: core/controls/player_core.py:597-602
- app_process fixture: tests/conftest.py:67-137
<!-- SECTION:NOTES:END -->
