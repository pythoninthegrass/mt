---
id: task-221
title: Remove continue-on-error from CI rust-tests job
status: Done
assignee: []
created_date: '2026-01-27 22:33'
updated_date: '2026-01-27 22:36'
labels:
  - ci
  - coverage
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
The rust-tests CI job has `continue-on-error: true` which allows coverage failures to pass silently. This defeats the purpose of having coverage thresholds.

## Context
- Coverage threshold is 50%
- Currently failures don't block PRs
- Regressions can slip through unnoticed

## Implementation
Remove or set to false:
```yaml
continue-on-error: false  # or remove the line entirely
```

## Dependencies
This should be done AFTER:
1. task-209 improvements are merged
2. Tarpaulin exclusions are configured
3. Coverage reliably passes 50% threshold

Otherwise CI will fail on every PR.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 continue-on-error removed from rust-tests job
- [ ] #2 CI fails when coverage drops below 50%
- [ ] #3 Coverage threshold enforced on PRs
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Completed 2026-01-27

Removed `continue-on-error: true` from the rust-tests job in `.github/workflows/test.yml`.

With the tarpaulin exclusions (task-220), coverage is now 54.07% which exceeds the 50% threshold, so the job will pass without the error workaround.
<!-- SECTION:NOTES:END -->
