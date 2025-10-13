---
id: task-034
title: Swap unicode buttons with custom icon buttons from static/
status: Done
assignee: []
created_date: '2025-10-09 03:28'
updated_date: '2025-10-09 04:49'
labels: []
dependencies: []
---

## Description

Replace current unicode symbol buttons with PNG icon buttons from the custom tkinter builder Spotify demo. Icons are located in static/ directory and need to be renamed to remove baseline prefix, color notation, and DPI suffixes before integration.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Rename all PNG icons in static/ to remove 'baseline_' prefix, '(255, 255, 255)' color notation, and '18dp_1x' DPI suffix (e.g., baseline_play_arrow_(255, 255, 255)_18dp_1x.png → play_arrow.png)
- [x] #2 Update config.py BUTTON_SYMBOLS to reference icon file paths instead of unicode symbols
- [x] #3 Modify PlayerControls class in core/gui.py to use PhotoImage/PIL for icon buttons instead of text-based Label widgets
- [x] #4 Ensure all playback controls (play/pause, previous, next) use icon buttons
- [x] #5 Ensure all utility controls (add, loop, shuffle) use icon buttons
- [x] #6 Update volume control icon to use volume_up.png instead of unicode emoji
- [x] #7 Maintain hover effects (color change or opacity) for icon buttons
- [x] #8 Ensure play/pause button can toggle between play_arrow.png and pause icon (if available)
- [x] #9 Test that all buttons are clickable and properly positioned after icon replacement
- [x] #10 Verify icons scale appropriately with window resize events
- [x] #11 Add any missing dependencies (PIL/Pillow) to pyproject.toml if needed
<!-- AC:END -->

## Implementation Notes

Successfully replaced unicode buttons with PNG icon buttons from static/. All playback and utility controls now use icons with hover effects. Fixed TCL/TK environment setup in repeater.py and resolved PIL/ImageTk compatibility issue with Homebrew Tcl/Tk using BytesIO workaround.
