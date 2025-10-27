---
id: task-087
title: 'Fix remaining test failures: property tests and flaky smoke test'
status: In Progress
assignee: []
created_date: '2025-10-27 05:48'
updated_date: '2025-10-27 05:48'
labels: []
dependencies: []
priority: medium
ordinal: 1500
---

## Description

Two categories of test failures remain after test suite optimization: (1) 5 property tests fail because real VLC returns -1 for time/duration operations with mock media objects (test_seek_position_stays_in_bounds, test_seek_position_proportional_to_duration, test_get_current_time_non_negative, test_get_duration_non_negative, test_get_duration_matches_media_length); (2) test_next_previous_navigation in smoke suite intermittently fails with 'Track should have changed' - timing-sensitive test that passes in isolation but can fail when run with other tests.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Investigate why real VLC returns -1 for mock media operations (check if MockMedia needs additional attributes/methods)
- [ ] #2 Either fix MockMedia to work with real VLC, or mark property tests to skip when real VLC is loaded
- [ ] #3 Add retry logic or increased wait times to test_next_previous_navigation to handle timing variability
- [ ] #4 Verify all fast tests pass consistently: pytest -m 'not slow' should show 473 passed, 0 failed
<!-- AC:END -->
