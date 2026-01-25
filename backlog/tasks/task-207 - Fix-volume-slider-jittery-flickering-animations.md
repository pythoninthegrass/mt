---
id: task-207
title: Fix volume slider jittery/flickering animations
status: In Progress
assignee: []
created_date: '2026-01-25 22:10'
updated_date: '2026-01-25 22:11'
labels:
  - bug
  - frontend
  - ui-polish
  - alpine
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The volume slider has jittery or flickering animations when adjusting the volume. This should be smooth like the progress bar slider.

**Current Behavior:**
- Volume slider exhibits jittery or flickering visual behavior during adjustment
- Animation is not smooth compared to the progress bar slider

**Expected Behavior:**
- Volume slider should have smooth animations like the progress bar
- No visual flickering or jittering during volume adjustments
- Consistent animation behavior across both sliders

**User Value:**
Users get a polished, professional UI experience with smooth slider interactions that don't cause visual distractions or perceived performance issues.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Volume slider animations are smooth without jittering or flickering
- [ ] #2 Volume slider animation behavior matches progress bar slider smoothness
- [ ] #3 No visual artifacts during volume adjustments
- [ ] #4 Volume changes respond promptly to user input without lag
- [ ] #5 Playwright E2E test verifies smooth volume slider interaction
- [ ] #6 Visual regression test captures slider behavior for comparison
<!-- AC:END -->
