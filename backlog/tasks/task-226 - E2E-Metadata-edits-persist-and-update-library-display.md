---
id: task-226
title: 'E2E: Metadata edits persist and update library display'
status: In Progress
assignee: []
created_date: '2026-01-27 23:37'
updated_date: '2026-01-27 23:49'
labels:
  - e2e
  - library
  - metadata
  - P0
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Validate that saving metadata changes in the editor updates the library list immediately without requiring refresh. User expectation: edits are immediately visible.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Open metadata editor for a track
- [ ] #2 Modify title/artist/album fields
- [ ] #3 Click Save button
- [ ] #4 Assert modal closes
- [ ] #5 Assert library row displays updated metadata values
- [ ] #6 Assert no page reload was required
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Test Location
Add to `app/frontend/tests/library.spec.js` in describe block: `'Metadata Editor @tauri'`

### Test Scenario

```javascript
test('metadata edits should persist and update library display immediately', async ({ page }) => {
  // 1. Setup: Wait for library to load
  await page.waitForSelector('[data-track-id]', { state: 'visible' });
  
  // 2. Get first track's current metadata from library row
  const firstTrackId = await page.locator('[data-track-id]').first().getAttribute('data-track-id');
  const originalTitle = await page.evaluate((id) => {
    const track = window.Alpine.store('library').tracks.find(t => t.id === parseInt(id));
    return track?.title;
  }, firstTrackId);
  
  // 3. Right-click to open context menu
  await page.locator('[data-track-id]').first().click({ button: 'right' });
  await page.waitForSelector('text=Edit Info', { state: 'visible' });
  await page.click('text=Edit Info');
  
  // 4. Wait for metadata modal
  await page.waitForSelector('[data-testid="metadata-modal"]', { state: 'visible', timeout: 5000 });
  
  // 5. Modify title field
  const newTitle = `Test Title ${Date.now()}`;
  const titleInput = page.locator('[data-testid="metadata-title"]');
  await titleInput.clear();
  await titleInput.fill(newTitle);
  
  // 6. Click Save
  const saveButton = page.locator('[data-testid="metadata-save"]');
  await saveButton.click();
  
  // 7. Wait for modal to close
  await page.waitForSelector('[data-testid="metadata-modal"]', { state: 'hidden', timeout: 5000 });
  
  // 8. Verify NO page reload occurred (check a stable element is still present)
  const libraryStillLoaded = await page.locator('[x-data="libraryBrowser"]').isVisible();
  expect(libraryStillLoaded).toBe(true);
  
  // 9. Verify library row displays updated title
  const updatedRowText = await page.locator(`[data-track-id="${firstTrackId}"]`).textContent();
  expect(updatedRowText).toContain(newTitle);
  
  // 10. Verify store was updated
  const storeTitle = await page.evaluate((id) => {
    const track = window.Alpine.store('library').tracks.find(t => t.id === parseInt(id));
    return track?.title;
  }, firstTrackId);
  expect(storeTitle).toBe(newTitle);
});

test('metadata edits for multiple fields should all persist', async ({ page }) => {
  await page.waitForSelector('[data-track-id]', { state: 'visible' });
  
  // Open metadata editor
  await page.locator('[data-track-id]').first().click({ button: 'right' });
  await page.click('text=Edit Info');
  await page.waitForSelector('[data-testid="metadata-modal"]', { state: 'visible', timeout: 5000 });
  
  // Modify multiple fields
  const timestamp = Date.now();
  const updates = {
    title: `Title ${timestamp}`,
    artist: `Artist ${timestamp}`,
    album: `Album ${timestamp}`,
  };
  
  await page.locator('[data-testid="metadata-title"]').clear();
  await page.locator('[data-testid="metadata-title"]').fill(updates.title);
  
  await page.locator('[data-testid="metadata-artist"]').clear();
  await page.locator('[data-testid="metadata-artist"]').fill(updates.artist);
  
  await page.locator('[data-testid="metadata-album"]').clear();
  await page.locator('[data-testid="metadata-album"]').fill(updates.album);
  
  // Save
  await page.locator('[data-testid="metadata-save"]').click();
  await page.waitForSelector('[data-testid="metadata-modal"]', { state: 'hidden', timeout: 5000 });
  
  // Verify all fields updated in library row
  const rowText = await page.locator('[data-track-id]').first().textContent();
  expect(rowText).toContain(updates.title);
  expect(rowText).toContain(updates.artist);
  expect(rowText).toContain(updates.album);
});
```

### Key Selectors
- `[data-testid="metadata-modal"]` - Modal container
- `[data-testid="metadata-title"]` - Title input
- `[data-testid="metadata-artist"]` - Artist input
- `[data-testid="metadata-album"]` - Album input
- `[data-testid="metadata-save"]` - Save button
- `text=Edit Info` - Context menu item to open editor

### Implementation Notes
- Modal is in `app/frontend/js/components/metadata-modal.js`
- Existing tests in library.spec.js (lines 2315+) provide patterns
- Modal uses `x-data="metadataModal"` Alpine component
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Modal is in `app/frontend/js/components/metadata-modal.js`
- Existing tests in library.spec.js (lines 2315+) provide patterns
- Modal uses `x-data="metadataModal"` Alpine component
<!-- SECTION:PLAN:END -->
<!-- SECTION:NOTES:END -->
