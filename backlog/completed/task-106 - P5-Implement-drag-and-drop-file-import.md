---
id: task-106
title: 'P5: Implement drag-and-drop file import'
status: Done
assignee: []
created_date: '2026-01-12 04:09'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - backend
  - phase-5
milestone: Tauri Migration
dependencies:
  - task-097
  - task-102
priority: medium
ordinal: 83382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable drag-and-drop of audio files and folders into the app.

**Frontend (WebView):**
```javascript
// Handle drag events on drop zone
document.addEventListener('dragover', (e) => {
    e.preventDefault();
    // Show drop indicator
});

document.addEventListener('drop', async (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const paths = files.map(f => f.path);
    
    // Send to backend for processing
    await fetch(`${backendUrl}/api/library/scan`, {
        method: 'POST',
        body: JSON.stringify({ paths })
    });
});
```

**Backend handling:**
- Accept array of file/folder paths
- Recursively scan folders for audio files
- Extract metadata and add to library
- Emit progress events via WebSocket

**UX considerations:**
- Visual feedback during drag (highlight drop zone)
- Progress indicator during scan
- Toast notification when complete
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Can drag files onto app window
- [x] #2 Can drag folders onto app window
- [x] #3 Visual feedback during drag
- [x] #4 Progress shown during scan
- [x] #5 Library updates after scan completes
<!-- AC:END -->
