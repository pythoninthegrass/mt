---
id: task-055
title: Integrate Hypothesis property-based testing
status: Done
assignee: []
created_date: '2025-10-13 02:15'
updated_date: '2025-10-13 02:34'
labels: []
dependencies: []
---

## Description

Add Hypothesis property-based tests to complement existing unit and E2E tests. Create test_props_*.py files that validate invariants and properties of core components (PlayerCore, QueueManager, utilities). Update documentation to explain when and how to use property tests.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Create tests/test_props_player_core.py with volume clamping, seek position, and toggle idempotency tests
- [x] #2 Create tests/test_props_queue_manager.py with shuffle preservation and queue operation tests
- [x] #3 Create tests/test_props_utils.py with utility function property tests
- [x] #4 Update tests/conftest.py with Hypothesis profile configuration (fast and thorough profiles)
- [x] #5 Update docs/testing.md with property testing section including when to use, examples, and running instructions
- [x] #6 Update AGENTS.md Development Workflow section with property test running commands
- [x] #7 All property tests pass with pytest tests/test_props_*.py -v -p no:pydust
<!-- AC:END -->
