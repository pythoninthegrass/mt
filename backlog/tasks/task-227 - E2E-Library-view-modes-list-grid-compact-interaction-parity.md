---
id: task-227
title: 'E2E: Library view modes (list/grid/compact) interaction parity'
status: In Progress
assignee: []
created_date: '2026-01-27 23:37'
updated_date: '2026-01-27 23:49'
labels:
  - e2e
  - library
  - ui
  - P0
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Validate that track selection, context menus, and play actions work consistently across all library view modes (list, grid, compact).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Switch to grid view mode
- [ ] #2 Select track and verify selection state
- [ ] #3 Right-click and verify context menu appears
- [ ] #4 Double-click track and verify playback starts
- [ ] #5 Repeat for compact view mode
- [ ] #6 Repeat for list view mode
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Implementation Plan

### Test Location
Add new describe block to `app/frontend/tests/library.spec.js`: `'Library View Mode Parity @tauri'`

### Test Scenarios

```javascript
test.describe('Library View Mode Parity @tauri', () => {
  const viewModes = ['list', 'grid', 'compact'];
  
  for (const mode of viewModes) {
    test.describe(`${mode} view`, () => {
      test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await waitForAlpine(page);
        await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
        
        // Set view mode
        await page.evaluate((viewMode) => {
          window.Alpine.store('ui').libraryViewMode = viewMode;
        }, mode);
        await page.waitForTimeout(200);
      });
      
      test('should allow track selection via click', async ({ page }) => {
        await page.waitForSelector('[data-track-id]', { state: 'visible' });
        
        // Click first track
        await page.locator('[data-track-id]').first().click();
        
        // Verify selection state
        const isSelected = await page.evaluate(() => {
          const library = window.Alpine.store('library');
          return library.selectedTrackIds?.size > 0 || library.selectedTracks?.length > 0;
        });
        expect(isSelected).toBe(true);
      });
      
      test('should show context menu on right-click', async ({ page }) => {
        await page.waitForSelector('[data-track-id]', { state: 'visible' });
        
        // Right-click first track
        await page.locator('[data-track-id]').first().click({ button: 'right' });
        
        // Verify context menu appears with expected options
        await page.waitForSelector('text=Play', { state: 'visible', timeout: 3000 });
        await page.waitForSelector('text=Add to Queue', { state: 'visible', timeout: 3000 });
        await page.waitForSelector('text=Edit Info', { state: 'visible', timeout: 3000 });
        
        // Dismiss menu
        await page.keyboard.press('Escape');
      });
      
      test('should start playback on double-click', async ({ page }) => {
        await page.waitForSelector('[data-track-id]', { state: 'visible' });
        
        // Verify not playing initially
        const initialPlaying = await page.evaluate(() => 
          window.Alpine.store('player').isPlaying
        );
        expect(initialPlaying).toBe(false);
        
        // Double-click first track
        await page.locator('[data-track-id]').first().dblclick();
        
        // Wait for playback to start
        await waitForPlaying(page);
        
        // Verify playing
        const nowPlaying = await page.evaluate(() => 
          window.Alpine.store('player').isPlaying
        );
        expect(nowPlaying).toBe(true);
        
        // Verify current track is set
        const currentTrack = await page.evaluate(() => 
          window.Alpine.store('player').currentTrack
        );
        expect(currentTrack).not.toBeNull();
        expect(currentTrack.id).toBeTruthy();
      });
      
      test('should support multi-select with Shift+click', async ({ page }) => {
        await page.waitForSelector('[data-track-id]', { state: 'visible' });
        
        // Ensure enough tracks
        const trackCount = await page.locator('[data-track-id]').count();
        if (trackCount < 3) {
          test.skip('Need at least 3 tracks for multi-select test');
          return;
        }
        
        // Click first track
        await page.locator('[data-track-id]').first().click();
        
        // Shift+click third track
        await page.keyboard.down('Shift');
        await page.locator('[data-track-id]').nth(2).click();
        await page.keyboard.up('Shift');
        
        // Verify 3 tracks selected
        const selectedCount = await page.evaluate(() => {
          const library = window.Alpine.store('library');
          return library.selectedTrackIds?.size || library.selectedTracks?.length || 0;
        });
        expect(selectedCount).toBeGreaterThanOrEqual(3);
      });
    });
  }
});
```

### Key Implementation Details
- Uses parameterized tests to run same suite for each view mode
- View modes are: `list`, `grid`, `compact`
- Set via `window.Alpine.store('ui').libraryViewMode`
- All modes should support: click select, right-click context menu, double-click play, multi-select

### Selectors
- `window.Alpine.store('ui').libraryViewMode` - Set/get current view mode
- `[data-track-id]` - Track elements in any view mode
- Context menu items: `text=Play`, `text=Add to Queue`, `text=Edit Info`

### View Mode Storage
- Stored in ui store: `libraryViewMode: 'list' | 'grid' | 'compact'`
- Persisted via `window.settings.set('ui:libraryViewMode', value)`
<!-- SECTION:PLAN:END -->
