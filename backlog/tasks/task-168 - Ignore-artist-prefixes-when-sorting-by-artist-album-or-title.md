---
id: task-168
title: 'Ignore artist prefixes when sorting by artist, album, or title'
status: Done
assignee: []
created_date: '2026-01-18 03:30'
updated_date: '2026-01-18 04:01'
labels: []
dependencies: []
priority: medium
ordinal: 382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Music libraries often contain artists with prefixes like "The Beatles", "Le Tigre", "Los Lobos", "A Tribe Called Quest", etc. When sorting alphabetically, these artists are grouped under T, L, or A rather than by their meaningful name. This creates a poor browsing experience as related artists are scattered across different sections.

Users should be able to configure a list of prefixes (articles) to ignore when sorting, so "The Beatles" sorts under "B" and "Los Lobos" sorts under "L". This matches the behavior of professional music management applications like MusicBee and provides a more natural browsing experience for large music collections.

The feature should be configurable in the settings menu under "Sorting/Grouping" > "Ignore words" to allow users to customize the list of prefixes based on their library's language mix (English, Spanish, French, etc.).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Settings menu includes a new 'Sorting/Grouping' section with an 'Ignore words' preference
- [x] #2 Ignore words preference allows users to specify a comma-separated list of prefixes to ignore when sorting
- [x] #3 Default ignore words list includes: 'the, le, la, los, a'
- [x] #4 When ignore words is enabled, sorting by Artist strips matching prefixes (case-insensitive) before sorting
- [x] #5 When ignore words is enabled, sorting by Album strips matching prefixes (case-insensitive) before sorting
- [x] #6 When ignore words is enabled, sorting by Title strips matching prefixes (case-insensitive) before sorting
- [x] #7 Display still shows the full artist/album/title name with prefix - only the sort order changes
- [x] #8 Preference can be toggled on/off without requiring app restart
- [x] #9 Custom ignore words list is persisted across app restarts
- [x] #10 UI follows MusicBee's design pattern: checkbox + text field for ignore words list
<!-- AC:END -->
