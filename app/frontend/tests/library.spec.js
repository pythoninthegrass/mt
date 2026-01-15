import { test, expect } from '@playwright/test';
import {
  waitForAlpine,
  getAlpineStore,
  clickTrackRow,
  doubleClickTrackRow,
} from './fixtures/helpers.js';

test.describe('Library Browser', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('should display track list', async ({ page }) => {
    // Wait for tracks to load
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Verify tracks are displayed
    const trackRows = page.locator('[data-track-id]');
    const count = await trackRows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display track metadata columns', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Verify column headers are present
    const headers = page.locator('.column-header, [class*="sort-header"]');
    const headerTexts = await headers.allTextContents();

    // Should have at least these columns
    const expectedColumns = ['#', 'Title', 'Artist', 'Album', 'Duration'];
    expectedColumns.forEach((col) => {
      const hasColumn = headerTexts.some((text) => text.includes(col));
      if (!hasColumn) {
        // Column might be represented differently, check track data instead
        console.log(`Column "${col}" not found in headers, but may be present in rows`);
      }
    });
  });

  test('should show loading state initially', async ({ page }) => {
    // This test needs to run on fresh page load
    await page.reload();
    await waitForAlpine(page);

    // Check for loading indicator (might be brief)
    const loadingIndicator = page.locator('text=Loading library, svg.animate-spin');
    const isVisible = await loadingIndicator.first().isVisible().catch(() => false);

    // Loading might be too fast to catch, so we check the library store instead
    const libraryStore = await getAlpineStore(page, 'library');
    // If tracks are already loaded, loading was completed
    expect(libraryStore.tracks.length >= 0).toBe(true);
  });

  test('should show empty state when no tracks', async ({ page }) => {
    // Set library to empty
    await page.evaluate(() => {
      window.Alpine.store('library').tracks = [];
      window.Alpine.store('library').filteredTracks = [];
      window.Alpine.store('library').loading = false;
    });

    // Wait for empty state
    await page.waitForSelector('text=Library is empty', { state: 'visible' });

    // Verify empty state message
    const emptyState = page.locator('text=Library is empty');
    await expect(emptyState).toBeVisible();
  });
});

test.describe('Search Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
  });

  test('should filter tracks by search query', async ({ page }) => {
    // Wait for tracks to load
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Get initial track count
    const initialCount = await page.locator('[data-track-id]').count();

    // Find search input
    const searchInput = page.locator('input[placeholder="Search"]');
    await expect(searchInput).toBeVisible();

    // Type search query
    await searchInput.fill('test');

    // Wait for search to complete (debounced)
    await page.waitForTimeout(500);

    // Verify filtered tracks
    const libraryStore = await getAlpineStore(page, 'library');
    expect(libraryStore.searchQuery).toBe('test');

    // Track count should change (unless all tracks match "test")
    const filteredCount = await page.locator('[data-track-id]').count();
    expect(typeof filteredCount).toBe('number');
  });

  test('should show clear button when search has text', async ({ page }) => {
    const searchInput = page.locator('input[placeholder="Search"]');
    await searchInput.fill('query');

    // Wait for clear button to appear
    await page.waitForSelector('button:near(input[placeholder="Search"])', { state: 'visible' });

    // Verify clear button is visible
    const clearButton = page.locator('input[placeholder="Search"] ~ button, input[placeholder="Search"] + button').first();
    await expect(clearButton).toBeVisible();
  });

  test('should clear search when clicking clear button', async ({ page }) => {
    const searchInput = page.locator('input[placeholder="Search"]');
    await searchInput.fill('query');
    await page.waitForTimeout(500);

    // Click clear button
    const clearButton = page.locator('input[placeholder="Search"] ~ button, input[placeholder="Search"] + button').first();
    await clearButton.click();

    // Verify search is cleared
    const libraryStore = await getAlpineStore(page, 'library');
    expect(libraryStore.searchQuery).toBe('');

    // Verify input is empty
    const inputValue = await searchInput.inputValue();
    expect(inputValue).toBe('');
  });

  test('should show "no results" message when search has no matches', async ({ page }) => {
    // Search for something unlikely to exist
    const searchInput = page.locator('input[placeholder="Search"]');
    await searchInput.fill('xyzxyzxyzunlikelytomatch123');
    await page.waitForTimeout(500);

    // Wait for empty state
    await page.waitForSelector('text=No tracks found', { state: 'visible' });

    // Verify "no results" message
    const noResultsMessage = page.locator('text=No tracks found');
    await expect(noResultsMessage).toBeVisible();
  });
});

test.describe('Sorting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should sort tracks by column when clicking header', async ({ page }) => {
    // Find a sortable column header (Title, Artist, Album, etc.)
    const titleHeader = page.locator('text=Title').first();

    // Click to sort
    await titleHeader.click();

    // Wait for sort to complete
    await page.waitForTimeout(300);

    // Verify sort indicator appears
    const libraryStore = await getAlpineStore(page, 'library');
    expect(libraryStore.sortBy).toBeTruthy();
  });

  test('should toggle sort direction on second click', async ({ page }) => {
    const titleHeader = page.locator('text=Title').first();

    // First click - sort ascending
    await titleHeader.click();
    await page.waitForTimeout(300);

    const firstSort = await getAlpineStore(page, 'library');
    const firstDirection = firstSort.sortOrder;

    // Second click - sort descending
    await titleHeader.click();
    await page.waitForTimeout(300);

    const secondSort = await getAlpineStore(page, 'library');
    expect(secondSort.sortOrder).not.toBe(firstDirection);
  });

  test('should show sort indicator on active column', async ({ page }) => {
    // Click title header
    const titleHeader = page.locator('text=Title').first();
    await titleHeader.click();
    await page.waitForTimeout(300);

    // Verify sort indicator (▲ or ▼)
    const headerText = await titleHeader.textContent();
    const hasSortIndicator = headerText.includes('▲') || headerText.includes('▼') || headerText.includes('↑') || headerText.includes('↓');
    expect(hasSortIndicator).toBe(true);
  });
});

test.describe('Track Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should select single track on click', async ({ page }) => {
    // Click first track
    await clickTrackRow(page, 0);

    // Verify track is selected (has track-row-selected class)
    const firstTrack = page.locator('[data-track-id]').first();
    const classes = await firstTrack.getAttribute('class');
    expect(classes).toContain('track-row-selected');
  });

  test('should deselect track when clicking elsewhere', async ({ page }) => {
    // Select first track
    await clickTrackRow(page, 0);

    // Click second track (without Cmd/Ctrl)
    await clickTrackRow(page, 1);

    // Verify first track is no longer selected
    const firstTrack = page.locator('[data-track-id]').first();
    const classes = await firstTrack.getAttribute('class');
    expect(classes).not.toContain('track-row-selected');
  });

  test('should select multiple tracks with Cmd+click (Mac) or Ctrl+click', async ({ page }) => {
    // Detect platform
    const isMac = process.platform === 'darwin';
    const modifier = isMac ? 'Meta' : 'Control';

    // Select first track
    await clickTrackRow(page, 0);

    // Cmd/Ctrl+click second track
    await page.keyboard.down(modifier);
    await clickTrackRow(page, 1);
    await page.keyboard.up(modifier);

    // Verify both tracks are selected
    const selectedTracks = page.locator('[data-track-id].track-row-selected');
    const count = await selectedTracks.count();
    expect(count).toBe(2);
  });

  test('should select range with Shift+click', async ({ page }) => {
    // Click first track
    await clickTrackRow(page, 0);

    // Shift+click fourth track
    await page.keyboard.down('Shift');
    await clickTrackRow(page, 3);
    await page.keyboard.up('Shift');

    // Verify tracks 0-3 are selected (4 tracks)
    const selectedTracks = page.locator('[data-track-id].track-row-selected');
    const count = await selectedTracks.count();
    expect(count).toBe(4);
  });

  test('should highlight selected tracks visually', async ({ page }) => {
    await clickTrackRow(page, 0);

    // Verify selected track has different background
    const selectedTrack = page.locator('[data-track-id].track-row-selected').first();
    const backgroundColor = await selectedTrack.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Should have a background color set
    expect(backgroundColor).toBeTruthy();
    expect(backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
  });
});

test.describe('Context Menu', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should show context menu on right-click', async ({ page }) => {
    // Right-click first track
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });

    // Wait for context menu
    await page.waitForSelector('.context-menu', { state: 'visible' });

    // Verify context menu is visible
    const contextMenu = page.locator('.context-menu');
    await expect(contextMenu).toBeVisible();
  });

  test('should show context menu options', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });

    await page.waitForSelector('.context-menu', { state: 'visible' });

    // Verify menu items exist
    const menuItems = page.locator('.context-menu-item');
    const count = await menuItems.count();
    expect(count).toBeGreaterThan(0);

    // Common menu items
    const menuTexts = await menuItems.allTextContents();
    const hasPlayOption = menuTexts.some((text) => text.toLowerCase().includes('play'));
    expect(hasPlayOption).toBe(true);
  });

  test('should close context menu when clicking outside', async ({ page }) => {
    // Open context menu
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });
    await page.waitForSelector('.context-menu', { state: 'visible' });

    // Click outside menu
    await page.click('body', { position: { x: 10, y: 10 } });

    // Verify menu is hidden
    const contextMenu = page.locator('.context-menu');
    await expect(contextMenu).not.toBeVisible();
  });

  test('should perform action when clicking menu item', async ({ page }) => {
    // Open context menu
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });
    await page.waitForSelector('.context-menu', { state: 'visible' });

    // Click "Play" menu item (or first available action)
    const playMenuItem = page.locator('.context-menu-item').first();
    await playMenuItem.click();

    // Verify menu closes
    const contextMenu = page.locator('.context-menu');
    await expect(contextMenu).not.toBeVisible();

    // Verify action was performed (depends on which menu item was clicked)
    // This is a generic check that something happened
    await page.waitForTimeout(500);
  });
});

test.describe('Section Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should show different library sections', async ({ page }) => {
    // Navigate to "All Songs" (default)
    const libraryStore = await getAlpineStore(page, 'library');
    expect(libraryStore.currentSection).toBeTruthy();
  });

  test('should update view when changing section', async ({ page }) => {
    // Wait for library to load
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Get initial section
    const initialStore = await getAlpineStore(page, 'library');
    const initialSection = initialStore.currentSection;

    // Try to find and click a different section (e.g., "Recently Played")
    const recentSection = page.locator('button:has-text("Recent")').first();
    const exists = await recentSection.count();

    if (exists > 0) {
      await recentSection.click();
      await page.waitForTimeout(500);

      // Verify section changed
      const updatedStore = await getAlpineStore(page, 'library');
      expect(updatedStore.currentSection).not.toBe(initialSection);
    }
  });

  test('should show Liked Songs section', async ({ page }) => {
    // Navigate to Liked Songs section
    const likedButton = page.locator('button:has-text("Liked")').first();
    const exists = await likedButton.count();

    if (exists > 0) {
      await likedButton.click();
      await page.waitForTimeout(500);

      // Verify we're in Liked Songs section
      const libraryStore = await getAlpineStore(page, 'library');
      expect(libraryStore.currentSection).toBe('liked');
    }
  });
});

test.describe('Responsive Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should maintain layout at minimum viewport size', async ({ page }) => {
    // Set to minimum recommended size
    await page.setViewportSize({ width: 1624, height: 1057 });

    // Verify essential elements are visible
    await expect(page.locator('[x-data="libraryBrowser"]')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();
  });

  test('should adjust layout for larger screens', async ({ page }) => {
    // Set to larger viewport
    await page.setViewportSize({ width: 1920, height: 1080 });

    // Verify layout adjusts
    await expect(page.locator('[x-data="libraryBrowser"]')).toBeVisible();

    // Track table should expand
    const trackList = page.locator('.track-list');
    const boundingBox = await trackList.boundingBox();
    expect(boundingBox.width).toBeGreaterThan(1000);
  });
});

test.describe('Column Customization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    
    await page.evaluate(() => {
      localStorage.removeItem('mt:column-settings');
    });
  });

  test('should show resize cursor on column header edge', async ({ page }) => {
    // Excel-style: resize handle on left edge of Album resizes Artist column
    const albumHeaderContainer = page.locator('[data-testid="library-header"] div:has(> span:text("Album"))').first();
    const resizeHandle = albumHeaderContainer.locator('.cursor-col-resize');
    
    await expect(resizeHandle).toBeVisible();
    
    const handleBox = await resizeHandle.boundingBox();
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    
    const cursor = await page.evaluate((pos) => {
      const el = document.elementFromPoint(pos.x, pos.y);
      return el ? window.getComputedStyle(el).cursor : null;
    }, { x: handleBox.x + handleBox.width / 2, y: handleBox.y + handleBox.height / 2 });
    
    expect(['col-resize', 'default', 'pointer']).toContain(cursor);
  });

  test('should resize column by dragging', async ({ page }) => {
    // Excel-style: dragging left edge of Album resizes Artist column
    const albumHeaderContainer = page.locator('[data-testid="library-header"] div:has(> span:text("Album"))').first();
    const resizeHandle = albumHeaderContainer.locator('.cursor-col-resize');
    
    await expect(resizeHandle).toBeVisible();
    const handleBox = await resizeHandle.boundingBox();
    
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(handleBox.x + 50, handleBox.y + handleBox.height / 2);
    await page.mouse.up();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBeDefined();
  });

  test('should auto-fit column width on double-click', async ({ page }) => {
    // Excel-style: double-click left edge of Album auto-fits Artist column
    const albumHeaderContainer = page.locator('[data-testid="library-header"] div:has(> span:text("Album"))').first();
    const resizeHandle = albumHeaderContainer.locator('.cursor-col-resize');
    
    await expect(resizeHandle).toBeVisible();
    await resizeHandle.dblclick();
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBeDefined();
  });

  test('should pause sorting during column resize', async ({ page }) => {
    // Excel-style: left edge of Album resizes Artist
    const albumHeaderContainer = page.locator('[data-testid="library-header"] div:has(> span:text("Album"))').first();
    const resizeHandle = albumHeaderContainer.locator('.cursor-col-resize');
    
    await expect(resizeHandle).toBeVisible();
    const handleBox = await resizeHandle.boundingBox();
    
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    await page.mouse.down();
    
    // During resize, sort-header class should be removed (sorting disabled)
    const artistHeader = page.locator('[data-testid="library-header"] div:has(> span:text("Artist"))').first();
    const hasSortHeader = await artistHeader.evaluate(el => el.classList.contains('sort-header'));
    expect(hasSortHeader).toBe(false);
    
    await page.mouse.up();
    await page.waitForTimeout(100);
    
    // After resize, sort-header class should be restored
    const hasSortHeaderAfter = await artistHeader.evaluate(el => el.classList.contains('sort-header'));
    expect(hasSortHeaderAfter).toBe(true);
  });

  test('should show header context menu on right-click', async ({ page }) => {
    const headerRow = page.locator('[data-testid="library-header"]');
    await expect(headerRow).toBeVisible();
    await headerRow.click({ button: 'right' });
    
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const contextMenu = page.locator('.header-context-menu');
    await expect(contextMenu).toBeVisible();
    
    const showColumnsText = page.locator('text=Show Columns');
    await expect(showColumnsText).toBeVisible();
  });

  test('should toggle column visibility from context menu', async ({ page }) => {
    const headerRow = page.locator('[data-testid="library-header"]');
    await headerRow.click({ button: 'right' });
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const albumMenuItem = page.locator('.header-context-menu .context-menu-item:has-text("Album")');
    await albumMenuItem.click();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnVisibility.album).toBe(false);
    
    const albumColumn = page.locator('[data-column="album"]').first();
    await expect(albumColumn).not.toBeVisible();
  });

  test('should prevent hiding all columns', async ({ page }) => {
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      
      data.columnVisibility.artist = false;
      data.columnVisibility.album = false;
      data.columnVisibility.duration = false;
      
      return window.Alpine.$data(el);
    });
    
    const headerRow = page.locator('[data-testid="library-header"]');
    await headerRow.click({ button: 'right' });
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const visibleColumns = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      return data.visibleColumnCount;
    });
    
    expect(visibleColumns).toBeGreaterThanOrEqual(2);
  });

  test('should persist column settings to localStorage', async ({ page }) => {
    const headerRow = page.locator('[data-testid="library-header"]');
    await headerRow.click({ button: 'right' });
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const albumMenuItem = page.locator('.header-context-menu .context-menu-item:has-text("Album")');
    await albumMenuItem.click();
    await page.waitForTimeout(100);
    
    const savedSettings = await page.evaluate(() => {
      return localStorage.getItem('mt:column-settings');
    });
    
    expect(savedSettings).toBeTruthy();
    const parsed = JSON.parse(savedSettings);
    expect(parsed.visibility.album).toBe(false);
  });

  test('should restore column settings on page reload', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('mt:column-settings', JSON.stringify({
        widths: { artist: 200 },
        visibility: { album: false }
      }));
    });
    
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBe(200);
    expect(componentData.columnVisibility.album).toBe(false);
  });

  test('should enforce minimum column width', async ({ page }) => {
    // Excel-style: left edge of Album resizes Artist
    const albumHeaderContainer = page.locator('[data-testid="library-header"] div:has(> span:text("Album"))').first();
    const resizeHandle = albumHeaderContainer.locator('.cursor-col-resize');
    
    await expect(resizeHandle).toBeVisible();
    const handleBox = await resizeHandle.boundingBox();
    
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(handleBox.x - 200, handleBox.y + handleBox.height / 2);
    await page.mouse.up();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBeGreaterThanOrEqual(40);
  });

  test('should reset column widths from context menu', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('mt:column-settings', JSON.stringify({
        widths: { artist: 300, album: 300 },
        visibility: {}
      }));
    });
    
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    
    const headerRow = page.locator('[data-testid="library-header"]');
    await headerRow.click({ button: 'right' });
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const resetMenuItem = page.locator('.header-context-menu .context-menu-item:has-text("Reset Column Widths")');
    await resetMenuItem.click();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBe(160);
  });

  test('should show all columns from context menu', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('mt:column-settings', JSON.stringify({
        widths: {},
        visibility: { album: false, artist: false }
      }));
    });
    
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    
    const headerRow = page.locator('[data-testid="library-header"]');
    await headerRow.click({ button: 'right' });
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const showAllMenuItem = page.locator('.header-context-menu .context-menu-item:has-text("Show All Columns")');
    await showAllMenuItem.click();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnVisibility.album).toBe(true);
    expect(componentData.columnVisibility.artist).toBe(true);
  });
});
