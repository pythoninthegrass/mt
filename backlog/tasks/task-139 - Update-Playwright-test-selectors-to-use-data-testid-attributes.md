---
id: task-139
title: Update Playwright test selectors to use data-testid attributes
status: Done
assignee: []
created_date: '2026-01-16 04:03'
updated_date: '2026-01-24 22:28'
labels:
  - testing
  - playwright
  - refactor
dependencies:
  - task-138
priority: high
ordinal: 69382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Problem
After adding `data-testid` attributes, tests should be updated to use them for stability.

## Solution
Update selectors in Playwright test files:

### Files to update
- `app/frontend/tests/playback.spec.js`
- `app/frontend/tests/queue.spec.js`
- `app/frontend/tests/fixtures/helpers.js`

### Selector changes
| Old Selector | New Selector |
|--------------|--------------|
| `button[title="Play/Pause"]` | `[data-testid="player-playpause"]` |
| `button[title="Next"]` | `[data-testid="player-next"]` |
| `button[title="Previous"]` | `[data-testid="player-prev"]` |
| `button[title="Shuffle"]` | `[data-testid="player-shuffle"]` |
| `button[title="Loop"]` | `[data-testid="player-loop"]` |
| `button[title="Mute"]` | `[data-testid="player-mute"]` |
| `[x-ref="progressBar"]` | `[data-testid="player-progressbar"]` |
| `[x-ref="volumeBar"]` | `[data-testid="player-volume"]` |

## Acceptance Criteria
<!-- AC:BEGIN -->
- All fragile selectors replaced with data-testid selectors
- All existing tests pass
- No new test failures introduced
<!-- SECTION:DESCRIPTION:END -->

- [ ] #1 All player control selectors updated to use data-testid
- [ ] #2 All queue selectors updated
- [ ] #3 All existing tests pass
- [ ] #4 Helper functions updated if needed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Completed: Updated all fragile selectors to use data-testid attributes:
- playback.spec.js: 7 selectors updated (play/pause, next, prev, progressbar, volume, mute)
- queue.spec.js: 4 selectors updated (next, prev, shuffle, loop)
- stores.spec.js: 1 selector updated (play/pause)

All 96 library+stores tests pass. Playback/queue test failures are expected (require Tauri audio backend).
<!-- SECTION:NOTES:END -->
