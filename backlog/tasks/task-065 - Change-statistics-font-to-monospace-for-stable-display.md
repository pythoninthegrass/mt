---
id: task-065
title: Change statistics font to monospace for stable display
status: In Progress
assignee: []
created_date: '2025-10-22 01:59'
updated_date: '2025-10-22 03:08'
labels: []
dependencies: []
priority: low
ordinal: 2000
---

## Description

Statistics display should use monospace font (like the time display in progress.py) to prevent horizontal text movement when numbers change. Currently statistics jump around as values update.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Use the same monospace font pattern from progress.py:24-35 (SF Mono → Menlo → TkFixedFont fallback)
- [ ] #2 Apply monospace font to all statistics displays (play count, track count, etc.)
- [ ] #3 Ensure numbers and labels align properly and don't cause horizontal shifting
- [ ] #4 Test with changing statistics values to verify stable display
- [ ] #5 Consider applying to any other UI areas that display changing numeric values
<!-- AC:END -->
