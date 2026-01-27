---
id: task-058
title: Fix context menu highlight to use theme primary color
status: Done
assignee: []
created_date: '2025-10-21 06:27'
updated_date: '2026-01-24 22:28'
labels: []
dependencies: []
ordinal: 44382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The context menu (right-click menu) currently shows blue highlighting instead of using the theme's primary color (cyan for metro-teal theme). Investigation needed: macOS may override tk.Menu activebackground setting with native menu styling. Need to explore alternatives like using ttk.Menu or custom menu implementation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Context menu hover/highlight uses theme primary color
- [ ] #2 Styling works consistently across all themes
<!-- AC:END -->
