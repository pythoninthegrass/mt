---
id: task-065
title: Change statistics font to monospace for stable display
status: Done
assignee: []
created_date: '2025-10-22 01:59'
updated_date: '2025-10-24 03:50'
labels: []
dependencies: []
priority: low
ordinal: 500
---

## Description

Statistics display should use monospace font (like the time display in progress.py) to prevent horizontal text movement when numbers change. Currently statistics jump around as values update.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Use the same monospace font pattern from progress.py:24-35 (SF Mono → Menlo → TkFixedFont fallback)
- [x] #2 Apply monospace font to all statistics displays (play count, track count, etc.)
- [x] #3 Ensure numbers and labels align properly and don't cause horizontal shifting
- [x] #4 Test with changing statistics values to verify stable display
- [x] #5 Consider applying to any other UI areas that display changing numeric values
<!-- AC:END -->


## Implementation Notes

Applied monospace font (SF Mono) to status bar statistics display to prevent horizontal text jumping when numbers change. Also applied to progress bar time display. Updated duration format from 'd hh:mm' to 'd h m' and reduced spacing between metrics by 25%.
