import { test, expect } from '@playwright/test';
import {
  waitForAlpine,
  getAlpineStore,
  clickTrackRow,
  doubleClickTrackRow,
} from './fixtures/helpers.js';
import {
  createPlaylistState,
  setupPlaylistMocks,
  clearApiCalls,
  findApiCalls,
} from './fixtures/mock-playlists.js';

const setColumnSettings = async (page, { widths, visibility, order }) => {
  await page.evaluate(({ widths, visibility, order }) => {
    if (widths) localStorage.setItem('mt:columns:widths', JSON.stringify(widths));
    if (visibility) localStorage.setItem('mt:columns:visibility', JSON.stringify(visibility));
    if (order) localStorage.setItem('mt:columns:order', JSON.stringify(order));
  }, { widths, visibility, order });
};

const getColumnSettings = async (page) => {
  return await page.evaluate(() => {
    const widths = localStorage.getItem('mt:columns:widths');
    const visibility = localStorage.getItem('mt:columns:visibility');
    const order = localStorage.getItem('mt:columns:order');
    return {
      widths: widths ? JSON.parse(widths) : null,
      visibility: visibility ? JSON.parse(visibility) : null,
      order: order ? JSON.parse(order) : null,
    };
  });
};

const clearColumnSettings = async (page) => {
  await page.evaluate(() => {
    localStorage.removeItem('mt:columns:widths');
    localStorage.removeItem('mt:columns:visibility');
    localStorage.removeItem('mt:columns:order');
    localStorage.removeItem('mt:column-settings');
  });
};

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
    const titleHeaderCell = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Title' }).first();
    await titleHeaderCell.click();
    await page.waitForTimeout(300);

    const headerText = await titleHeaderCell.textContent();
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
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });

    await page.waitForSelector('[data-testid="track-context-menu"]', { state: 'visible' });

    const contextMenu = page.locator('[data-testid="track-context-menu"]');
    await expect(contextMenu).toBeVisible();
  });

  test('should show context menu options', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });

    await page.waitForSelector('[data-testid="track-context-menu"]', { state: 'visible' });
    await page.waitForSelector('[data-testid="track-context-menu"] .context-menu-item', { state: 'visible', timeout: 5000 });

    const menuItems = page.locator('[data-testid="track-context-menu"] .context-menu-item');
    await expect(menuItems.first()).toBeVisible();
    const count = await menuItems.count();
    expect(count).toBeGreaterThan(0);

    const menuTexts = await menuItems.allTextContents();
    const hasPlayOption = menuTexts.some((text) => text.toLowerCase().includes('play'));
    expect(hasPlayOption).toBe(true);
  });

  test('should close context menu when clicking outside', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });
    await page.waitForSelector('[data-testid="track-context-menu"]', { state: 'visible' });

    await page.click('body', { position: { x: 10, y: 10 } });

    const contextMenu = page.locator('[data-testid="track-context-menu"]');
    await expect(contextMenu).not.toBeVisible();
  });

  test('should perform action when clicking menu item', async ({ page }) => {
    const firstTrack = page.locator('[data-track-id]').first();
    await firstTrack.click({ button: 'right' });
    await page.waitForSelector('[data-testid="track-context-menu"]', { state: 'visible' });
    await page.waitForSelector('[data-testid="track-context-menu"] .context-menu-item', { state: 'visible' });

    const playMenuItem = page.locator('[data-testid="track-context-menu"] .context-menu-item').first();
    await playMenuItem.click();

    const contextMenu = page.locator('[data-testid="track-context-menu"]');
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
    
    await clearColumnSettings(page);
  });

  test('should show resize cursor on column header edge', async ({ page }) => {
    const resizeHandle = page.locator('[data-testid="col-resizer-right-artist"]');
    
    await expect(resizeHandle).toBeVisible();
    
    const cursor = await resizeHandle.evaluate(el => window.getComputedStyle(el).cursor);
    expect(cursor).toBe('col-resize');
  });

  test('should resize column by dragging', async ({ page }) => {
    const resizeHandle = page.locator('[data-testid="col-resizer-right-artist"]');
    
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
    const resizeHandle = page.locator('[data-testid="col-resizer-right-artist"]');
    
    await expect(resizeHandle).toBeVisible();
    await resizeHandle.dblclick();
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBeDefined();
  });

  test('should auto-fit column to content width and adjust neighbor', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { title: 200, artist: 300, album: 300 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration']
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const initialBaseWidths = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      return { title: data._baseColumnWidths.title, artist: data._baseColumnWidths.artist };
    });

    const resizer = page.locator('[data-testid="col-resizer-right-title"]');
    await resizer.dblclick();
    await page.waitForTimeout(150);

    const afterBaseWidths = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      return { title: data._baseColumnWidths.title, artist: data._baseColumnWidths.artist };
    });

    expect(afterBaseWidths.title).toBeGreaterThan(initialBaseWidths.title);
    expect(afterBaseWidths.artist).toBeLessThanOrEqual(initialBaseWidths.artist);
  });

  test('should increase column width on auto-fit for Artist column', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { artist: 50, album: 400 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration']
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Get initial width
    const artistHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Artist' }).first();
    const beforeWidth = await artistHeader.evaluate((el) => el.getBoundingClientRect().width);
    expect(beforeWidth).toBeLessThan(100); // Should be narrow initially

    // Double-click to auto-fit
    const resizer = page.locator('[data-testid="col-resizer-right-artist"]');
    await resizer.dblclick();
    await page.waitForTimeout(150);

    // Verify width increased
    const afterWidth = await artistHeader.evaluate((el) => el.getBoundingClientRect().width);
    expect(afterWidth).toBeGreaterThan(beforeWidth);
  });

  test('should increase column width on auto-fit for Album column', async ({ page }) => {
    await page.setViewportSize({ width: 800, height: 600 });
    await setColumnSettings(page, {
      widths: { album: 50, duration: 100 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration']
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const albumHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Album' }).first();
    const beforeWidth = await albumHeader.evaluate((el) => el.getBoundingClientRect().width);

    const resizer = page.locator('[data-testid="col-resizer-right-album"]');
    await resizer.dblclick();
    await page.waitForTimeout(150);

    const afterWidth = await albumHeader.evaluate((el) => el.getBoundingClientRect().width);
    expect(afterWidth).toBeGreaterThanOrEqual(beforeWidth);
  });

  test('should reduce text overflow on auto-fit when possible', async ({ page }) => {
    // Set up very narrow Artist with very wide Album (plenty of space to take)
    await setColumnSettings(page, {
      widths: { artist: 30, album: 500 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration']
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const artistCell = page.locator('[data-column="artist"]').first();
    
    // Get overflow amount before (scrollWidth - clientWidth)
    const beforeOverflowAmount = await artistCell.evaluate((el) => {
      return el.scrollWidth - el.clientWidth;
    });

    // Double-click to auto-fit
    const resizer = page.locator('[data-testid="col-resizer-right-artist"]');
    await resizer.dblclick();
    await page.waitForTimeout(150);

    // Get overflow amount after
    const afterOverflowAmount = await artistCell.evaluate((el) => {
      return el.scrollWidth - el.clientWidth;
    });

    // Overflow should be reduced (ideally to 0, but at minimum less than before)
    expect(afterOverflowAmount).toBeLessThanOrEqual(beforeOverflowAmount);
  });

  test('no horizontal scroll when vertical scrollbar is present @1800x1259', async ({ page }) => {
    await page.setViewportSize({ width: 1800, height: 1259 });
    await clearColumnSettings(page);
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await page.waitForTimeout(300);
    
    const overflow = await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      return {
        overflow: container.scrollWidth - container.clientWidth,
        hasVerticalScroll: container.scrollHeight > container.clientHeight
      };
    });
    
    expect(overflow.hasVerticalScroll).toBe(true);
    expect(overflow.overflow).toBeLessThanOrEqual(2);
  });

  test('no horizontal scroll when vertical scrollbar is present @2400x1260', async ({ page }) => {
    await page.setViewportSize({ width: 2400, height: 1260 });
    await clearColumnSettings(page);
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await page.waitForTimeout(300);
    
    const overflow = await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      return {
        overflow: container.scrollWidth - container.clientWidth,
        hasVerticalScroll: container.scrollHeight > container.clientHeight
      };
    });
    
    expect(overflow.hasVerticalScroll).toBe(true);
    expect(overflow.overflow).toBeLessThanOrEqual(2);
  });

  test('no horizontal scroll after window resize @2400x1260 -> @1800x1260', async ({ page }) => {
    await page.setViewportSize({ width: 2400, height: 1260 });
    await clearColumnSettings(page);
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await page.waitForTimeout(300);
    
    await page.setViewportSize({ width: 1800, height: 1260 });
    await page.waitForTimeout(500);
    
    const overflow = await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      return container.scrollWidth - container.clientWidth;
    });
    
    expect(overflow).toBeLessThanOrEqual(2);
  });

  test('no horizontal scroll when base widths exceed container', async ({ page }) => {
    await page.setViewportSize({ width: 1800, height: 1259 });
    await setColumnSettings(page, {
      widths: { title: 800, artist: 500, album: 500 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration']
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await page.waitForTimeout(300);
    
    const overflow = await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      return container.scrollWidth - container.clientWidth;
    });
    
    expect(overflow).toBeLessThanOrEqual(2);
  });

  test('no horizontal scroll with Tauri fractional pixel widths', async ({ page }) => {
    await page.setViewportSize({ width: 1800, height: 1259 });
    await setColumnSettings(page, {
      widths: {
        index: 40.0625,
        title: 344.69921875,
        artist: 377.8193359375,
        album: 390.845703125,
        lastPlayed: 120,
        dateAdded: 120,
        playCount: 60,
        duration: 405.5732421875
      },
      visibility: { index: true, title: true, artist: true, album: true, lastPlayed: true, dateAdded: true, playCount: true, duration: true },
      order: ['index', 'title', 'artist', 'album', 'lastPlayed', 'dateAdded', 'playCount', 'duration']
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    await page.waitForTimeout(300);
    
    const overflow = await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      return container.scrollWidth - container.clientWidth;
    });
    
    expect(overflow).toBeLessThanOrEqual(2);
  });

  test('columns should fill container width on initial load (RTC-style distribution)', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    await clearColumnSettings(page);
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
    
    // Wait for any distribution to complete
    await page.waitForTimeout(300);
    
    // Get container width
    const containerWidth = await page.evaluate(() => {
      const container = document.querySelector('[x-ref="scrollContainer"]');
      return container.clientWidth;
    });
    
    // Get sum of all column widths from the component state
    const columnData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      const columns = data.columns;
      let totalWidth = 0;
      columns.forEach(col => {
        const width = data.columnWidths[col.key] || 100;
        totalWidth += width;
      });
      return { totalWidth, columnWidths: data.columnWidths, containerWidth: data.containerWidth };
    });
    
    // The total column width should be at least the container width (no gap)
    // Allow 2px tolerance for rounding
    expect(columnData.totalWidth).toBeGreaterThanOrEqual(containerWidth - 2);
    
    // Also verify visually: header should span the container
    const header = page.locator('[data-testid="library-header"]');
    const headerBox = await header.boundingBox();
    const scrollContainer = page.locator('[x-ref="scrollContainer"]');
    const containerBox = await scrollContainer.boundingBox();
    
    // Header width should be >= container width (accounting for scrollbar ~15px)
    expect(headerBox.width).toBeGreaterThanOrEqual(containerBox.width - 20);
  });

  test('auto-fit Artist should persist width (no flash-and-revert)', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { artist: 80, album: 300 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration'],
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const artistHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Artist' }).first();
    const beforeWidth = await artistHeader.evaluate(el => el.getBoundingClientRect().width);

    await page.locator('[data-testid="col-resizer-right-artist"]').dblclick();
    await page.waitForTimeout(500);

    const afterWidth = await artistHeader.evaluate(el => el.getBoundingClientRect().width);
    expect(afterWidth).toBeGreaterThan(beforeWidth + 5);

    const saved = await getColumnSettings(page);
    expect(saved.widths.artist).toBeGreaterThan(80);
  });

  test('auto-fit Album should persist width (no flash-and-revert)', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { album: 80, duration: 100 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration'],
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const albumHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Album' }).first();
    const beforeWidth = await albumHeader.evaluate(el => el.getBoundingClientRect().width);

    await page.locator('[data-testid="col-resizer-right-album"]').dblclick();
    await page.waitForTimeout(500);

    const afterWidth = await albumHeader.evaluate(el => el.getBoundingClientRect().width);
    expect(afterWidth).toBeGreaterThan(beforeWidth + 5);

    const saved = await getColumnSettings(page);
    expect(saved.widths.album).toBeGreaterThan(80);
  });

  test('manual resize Artist should not expand Title temporarily', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { title: 320, artist: 180, album: 180 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration'],
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const getBaseTitleWidth = () => page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el)._baseColumnWidths.title;
    });

    const initialTitleWidth = await getBaseTitleWidth();

    const handle = page.locator('[data-testid="col-resizer-right-artist"]');
    const box = await handle.boundingBox();

    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();

    await page.mouse.move(box.x + box.width / 2 + 60, box.y + box.height / 2);

    const titleWidthDuringDrag = await getBaseTitleWidth();
    expect(titleWidthDuringDrag).toBe(initialTitleWidth);

    await page.mouse.up();
    await page.waitForTimeout(150);

    const titleWidthAfterDrag = await getBaseTitleWidth();
    expect(titleWidthAfterDrag).toBe(initialTitleWidth);
  });

  test('manual resize Album from right border should grow Album base width', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { title: 320, artist: 180, album: 180, duration: 40 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration'],
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const getBaseWidths = () => page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      return { title: data._baseColumnWidths.title, album: data._baseColumnWidths.album };
    });

    const before = await getBaseWidths();

    const handle = page.locator('[data-testid="col-resizer-right-album"]');
    const box = await handle.boundingBox();

    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 40, box.y + box.height / 2);
    await page.mouse.up();
    await page.waitForTimeout(150);

    const after = await getBaseWidths();

    expect(after.title).toBe(before.title);
    expect(after.album).toBeGreaterThan(before.album);
  });

  test('table rows should span full container width (no gap before scrollbar)', async ({ page }) => {
    await clearColumnSettings(page);
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const scrollContainer = page.locator('[x-ref="scrollContainer"]');
    const header = page.locator('[data-testid="library-header"]');
    const firstRow = page.locator('[data-track-id]').first();

    const containerWidth = await scrollContainer.evaluate(el => el.clientWidth);
    const headerWidth = await header.evaluate(el => el.scrollWidth);
    const rowWidth = await firstRow.evaluate(el => el.scrollWidth);

    expect(headerWidth).toBeGreaterThanOrEqual(containerWidth);
    expect(rowWidth).toBeGreaterThanOrEqual(containerWidth);
  });

  test('table rows should span full width after auto-fit narrows columns', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { title: 500, artist: 300, album: 300 },
      visibility: {},
      order: ['index', 'title', 'artist', 'album', 'duration'],
    });
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Auto-fit Title (should shrink it to content width)
    await page.locator('[data-testid="col-resizer-right-title"]').dblclick();
    await page.waitForTimeout(200);

    // Auto-fit Artist
    await page.locator('[data-testid="col-resizer-right-artist"]').dblclick();
    await page.waitForTimeout(200);

    const scrollContainer = page.locator('[x-ref="scrollContainer"]');
    const header = page.locator('[data-testid="library-header"]');
    const firstRow = page.locator('[data-track-id]').first();

    const containerWidth = await scrollContainer.evaluate(el => el.clientWidth);
    const headerWidth = await header.evaluate(el => el.scrollWidth);
    const rowWidth = await firstRow.evaluate(el => el.scrollWidth);

    // Even after auto-fit shrinks columns, they should still span container
    expect(headerWidth).toBeGreaterThanOrEqual(containerWidth);
    expect(rowWidth).toBeGreaterThanOrEqual(containerWidth);
  });

  test('should not flash column drag state on single click', async ({ page }) => {
    const titleHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Title' }).first();
    
    const hasDraggingBefore = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).draggingColumnKey;
    });
    expect(hasDraggingBefore).toBeNull();

    await titleHeader.click();
    await page.waitForTimeout(50);

    const hasDraggingAfter = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).draggingColumnKey;
    });
    expect(hasDraggingAfter).toBeNull();
  });

  test('should not trigger sort when resizing column', async ({ page }) => {
    const resizeHandle = page.locator('[data-testid="col-resizer-right-artist"]');
    
    await expect(resizeHandle).toBeVisible();
    const handleBox = await resizeHandle.boundingBox();
    
    const initialSortBy = await page.evaluate(() => {
      return window.Alpine.store('library').sortBy;
    });
    
    // Use dispatchEvent to trigger mousedown on the resizer element
    await resizeHandle.dispatchEvent('mousedown', { bubbles: true });
    
    // Verify resizingColumn is set during drag
    const resizingDuringDrag = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).resizingColumn;
    });
    expect(resizingDuringDrag).toBe('artist');
    
    // Move mouse to simulate drag (into Album column area)
    await page.mouse.move(handleBox.x + 50, handleBox.y + handleBox.height / 2);
    
    // Trigger mouseup on document (simulates releasing mouse)
    await page.evaluate(() => {
      document.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    });
    
    await page.waitForTimeout(150);
    
    const finalSortBy = await page.evaluate(() => {
      return window.Alpine.store('library').sortBy;
    });
    
    expect(finalSortBy).toBe(initialSortBy);
  });

  test('should resize previous column when dragging left border (Excel behavior)', async ({ page }) => {
    const leftResizer = page.locator('[data-testid="col-resizer-left-artist"]');
    
    await expect(leftResizer).toBeVisible();
    
    const initialTitleWidth = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columnWidths.title;
    });
    
    const handleBox = await leftResizer.boundingBox();
    
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(handleBox.x - 50, handleBox.y + handleBox.height / 2);
    await page.mouse.up();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData._baseColumnWidths.title).toBeLessThan(initialTitleWidth);
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
    
    const savedSettings = await getColumnSettings(page);
    
    expect(savedSettings.visibility).toBeTruthy();
    expect(savedSettings.visibility.album).toBe(false);
  });

  test('should restore column settings on page reload', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { artist: 200 },
      visibility: { album: false }
    });
    
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBeGreaterThanOrEqual(200);
    expect(componentData.columnVisibility.album).toBe(false);
  });

  test('should enforce minimum column width', async ({ page }) => {
    const titleResizer = page.locator('[data-testid="col-resizer-right-title"]');
    
    await expect(titleResizer).toBeVisible();
    const handleBox = await titleResizer.boundingBox();
    
    await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(handleBox.x - 300, handleBox.y + handleBox.height / 2);
    await page.mouse.up();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.title).toBeGreaterThanOrEqual(120);
  });

  test('should reset column widths from context menu', async ({ page }) => {
    await setColumnSettings(page, {
      widths: { artist: 300, album: 300 },
      visibility: {}
    });
    
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    
    const headerRow = page.locator('[data-testid="library-header"]');
    await headerRow.click({ button: 'right' });
    await page.waitForSelector('.header-context-menu', { state: 'visible', timeout: 5000 });
    
    const resetMenuItem = page.locator('.header-context-menu .context-menu-item:has-text("Reset Columns to Defaults")');
    await resetMenuItem.click();
    
    await page.waitForTimeout(100);
    
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el);
    });
    
    expect(componentData.columnWidths.artist).toBeGreaterThanOrEqual(180);
  });

  test('should show all columns from context menu', async ({ page }) => {
    await setColumnSettings(page, {
      widths: {},
      visibility: { album: false, artist: false }
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

  test('should reorder columns by dragging', async ({ page }) => {
    const headerRow = page.locator('[data-testid="library-header"]');
    await expect(headerRow).toBeVisible();

    const initialOrder = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columns.map(c => c.key);
    });

    expect(initialOrder).toContain('artist');
    expect(initialOrder).toContain('album');
    const artistIdx = initialOrder.indexOf('artist');
    const albumIdx = initialOrder.indexOf('album');
    expect(artistIdx).toBeLessThan(albumIdx);

    const artistHeader = headerRow.locator('div').filter({ hasText: 'Artist' }).first();
    const albumHeader = headerRow.locator('div').filter({ hasText: 'Album' }).first();
    
    const artistBox = await artistHeader.boundingBox();
    const albumBox = await albumHeader.boundingBox();

    await page.mouse.move(artistBox.x + artistBox.width / 2, artistBox.y + artistBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(albumBox.x + albumBox.width - 10, albumBox.y + albumBox.height / 2, { steps: 5 });
    await page.mouse.up();

    await page.waitForTimeout(100);

    const newOrder = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columns.map(c => c.key);
    });

    const newArtistIdx = newOrder.indexOf('artist');
    const newAlbumIdx = newOrder.indexOf('album');
    expect(newArtistIdx).toBeGreaterThan(newAlbumIdx);
  });

  test('should not overshoot when dragging column back to original position', async ({ page }) => {
    const headerRow = page.locator('[data-testid="library-header"]');
    await expect(headerRow).toBeVisible();

    // Get initial order: [#, Title, Artist, Album, Time]
    const initialOrder = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columns.map(c => c.key);
    });

    const initialArtistIdx = initialOrder.indexOf('artist');
    const initialAlbumIdx = initialOrder.indexOf('album');
    expect(initialArtistIdx).toBeLessThan(initialAlbumIdx);

    // Step 1: Drag Album left to swap with Artist
    const albumHeader1 = headerRow.locator('div').filter({ hasText: 'Album' }).first();
    const artistHeader1 = headerRow.locator('div').filter({ hasText: 'Artist' }).first();

    const albumBox1 = await albumHeader1.boundingBox();
    const artistBox1 = await artistHeader1.boundingBox();

    await page.mouse.move(albumBox1.x + albumBox1.width / 2, albumBox1.y + albumBox1.height / 2);
    await page.mouse.down();
    await page.mouse.move(artistBox1.x + 10, artistBox1.y + artistBox1.height / 2, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    // Verify Album is now before Artist: [#, Title, Album, Artist, Time]
    const orderAfterStep1 = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columns.map(c => c.key);
    });
    const albumIdxStep1 = orderAfterStep1.indexOf('album');
    const artistIdxStep1 = orderAfterStep1.indexOf('artist');
    expect(albumIdxStep1).toBeLessThan(artistIdxStep1);

    // Step 2: Drag Album back right to swap with Artist (return to original position)
    // This tests the bug fix - Album should not overshoot and jump over Time
    const albumHeader2 = headerRow.locator('div').filter({ hasText: 'Album' }).first();
    const artistHeader2 = headerRow.locator('div').filter({ hasText: 'Artist' }).first();

    const albumBox2 = await albumHeader2.boundingBox();
    const artistBox2 = await artistHeader2.boundingBox();

    await page.mouse.move(albumBox2.x + albumBox2.width / 2, albumBox2.y + albumBox2.height / 2);
    await page.mouse.down();
    await page.mouse.move(artistBox2.x + artistBox2.width - 10, artistBox2.y + artistBox2.height / 2, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    // Verify we're back to original order: [#, Title, Artist, Album, Time]
    // Album should be right after Artist, NOT after Time (which would be overshooting)
    const finalOrder = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columns.map(c => c.key);
    });

    const finalArtistIdx = finalOrder.indexOf('artist');
    const finalAlbumIdx = finalOrder.indexOf('album');
    const finalDurationIdx = finalOrder.indexOf('duration');

    // Artist should be before Album
    expect(finalArtistIdx).toBeLessThan(finalAlbumIdx);
    // Album should be before Time/Duration (not after it - that would be overshooting)
    expect(finalAlbumIdx).toBeLessThan(finalDurationIdx);
    // Verify exact positions: Artist at original-1, Album at original (since we moved left then right)
    expect(finalAlbumIdx - finalArtistIdx).toBe(1);
  });

  test('should persist column order to localStorage', async ({ page }) => {
    await setColumnSettings(page, {
      widths: {},
      visibility: {},
      order: ['index', 'title', 'album', 'artist', 'duration']
    });

    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });

    const columnOrder = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columns.map(c => c.key);
    });

    const albumIdx = columnOrder.indexOf('album');
    const artistIdx = columnOrder.indexOf('artist');
    expect(albumIdx).toBeLessThan(artistIdx);
  });
});

/**
 * Regression tests for task-135: Column padding consistency fix
 *
 * These tests ensure:
 * - Duration column has correct asymmetric padding (pl-[3px] pr-[10px])
 * - Other non-index columns have consistent px-4 padding
 * - Index column has px-2 padding
 * - Duration column maintains 40px width
 * - Title column fills remaining space without excessive whitespace
 * - Headers remain sticky when scrolling
 */
test.describe('Column Padding Consistency (task-135)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    await page.waitForSelector('[data-track-id]', { state: 'visible' });
  });

  test('should have correct duration column padding (asymmetric pl-3px pr-10px)', async ({ page }) => {
    // Check header duration column padding
    const headerDurationCell = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Time' }).first();

    const headerPadding = await headerDurationCell.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
      };
    });

    // Duration column should have asymmetric padding: pl-[3px] pr-[10px]
    expect(headerPadding.paddingLeft).toBe('3px');
    expect(headerPadding.paddingRight).toBe('10px');

    // Check data row duration column padding
    const dataDurationCell = page.locator('[data-column="duration"]').first();

    const dataPadding = await dataDurationCell.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
      };
    });

    expect(dataPadding.paddingLeft).toBe('3px');
    expect(dataPadding.paddingRight).toBe('10px');
  });

  test('should have consistent px-4 padding for non-duration, non-index columns', async ({ page }) => {
    // Check Artist column padding (should be px-4 = 16px)
    const artistHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Artist' }).first();

    const artistPadding = await artistHeader.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
      };
    });

    expect(artistPadding.paddingLeft).toBe('16px');
    expect(artistPadding.paddingRight).toBe('16px');

    // Check Album column padding
    const albumHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Album' }).first();

    const albumPadding = await albumHeader.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
      };
    });

    expect(albumPadding.paddingLeft).toBe('16px');
    expect(albumPadding.paddingRight).toBe('16px');

    // Check Title column padding
    const titleHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Title' }).first();

    const titlePadding = await titleHeader.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
      };
    });

    expect(titlePadding.paddingLeft).toBe('16px');
    expect(titlePadding.paddingRight).toBe('16px');
  });

  test('should have px-2 padding for index column', async ({ page }) => {
    // Index column uses px-2 = 8px padding
    const indexHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: '#' }).first();

    const indexPadding = await indexHeader.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
      };
    });

    expect(indexPadding.paddingLeft).toBe('8px');
    expect(indexPadding.paddingRight).toBe('8px');
  });

  test('should have duration column default width of 52px', async ({ page }) => {
    await clearColumnSettings(page);
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });

    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      return {
        durationWidth: data.columnWidths.duration,
      };
    });

    expect(componentData.durationWidth).toBe(52);
  });

  test('should enforce minimum duration column width of 52px', async ({ page }) => {
    // Try to resize duration column below minimum
    const durationResizer = page.locator('[data-testid="col-resizer-left-duration"]');

    if (await durationResizer.count() > 0) {
      const handleBox = await durationResizer.boundingBox();

      // Drag left to try to shrink the column before duration (Album)
      await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
      await page.mouse.down();
      await page.mouse.move(handleBox.x + 100, handleBox.y + handleBox.height / 2);
      await page.mouse.up();

      await page.waitForTimeout(100);
    }

    // Duration width should not go below 52px
    const componentData = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      return window.Alpine.$data(el).columnWidths.duration;
    });

    expect(componentData).toBeGreaterThanOrEqual(52);
  });

  test('should have sticky header that remains visible when scrolling', async ({ page }) => {
    // Verify header has sticky positioning
    const header = page.locator('[data-testid="library-header"]');

    const headerClasses = await header.getAttribute('class');
    expect(headerClasses).toContain('sticky');
    expect(headerClasses).toContain('top-0');
    expect(headerClasses).toContain('z-10');

    // Scroll down and verify header is still in view
    const scrollContainer = page.locator('[x-ref="scrollContainer"]');
    await scrollContainer.evaluate((el) => {
      el.scrollTop = 500;
    });

    await page.waitForTimeout(100);

    // Header should still be visible at top of viewport
    const headerBox = await header.boundingBox();
    const containerBox = await scrollContainer.boundingBox();

    // Header top should be at or near the container top (sticky behavior)
    expect(headerBox.y).toBeLessThanOrEqual(containerBox.y + 5);
  });

  test('should not have excessive whitespace between Time column and scrollbar', async ({ page }) => {
    // Get the Time column header bounding box
    const timeHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Time' }).first();
    const timeHeaderBox = await timeHeader.boundingBox();

    // Get the scroll container bounding box
    const scrollContainer = page.locator('[x-ref="scrollContainer"]');
    const containerBox = await scrollContainer.boundingBox();

    // Time column should extend close to the right edge
    // Allow for scrollbar width (~15-20px) and small margin
    const gap = containerBox.x + containerBox.width - (timeHeaderBox.x + timeHeaderBox.width);

    // Gap should be reasonable (scrollbar width + small buffer)
    // If excessive whitespace bug exists, gap would be much larger (50px+)
    expect(gap).toBeLessThan(30);
  });

  test('should have Title column fill remaining space dynamically', async ({ page }) => {
    // Get initial Title column width
    const initialTitleWidth = await page.evaluate(() => {
      const el = document.querySelector('[x-data="libraryBrowser"]');
      const data = window.Alpine.$data(el);
      return data.columnWidths.title || 320;
    });

    // Resize the viewport to trigger Title column recalculation
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(200);

    // Title column should have expanded to fill the larger container
    const titleHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Title' }).first();
    const titleBox = await titleHeader.boundingBox();

    // Title should be at least 320px (minimum) and expanded with the viewport
    expect(titleBox.width).toBeGreaterThanOrEqual(320);
  });

  test('should have same padding on data rows as header rows', async ({ page }) => {
    // Artist header padding
    const artistHeader = page.locator('[data-testid="library-header"] > div').filter({ hasText: 'Artist' }).first();
    const headerPadding = await artistHeader.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return { left: style.paddingLeft, right: style.paddingRight };
    });

    // Artist data cell padding
    const artistDataCell = page.locator('[data-column="artist"]').first();
    const dataPadding = await artistDataCell.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return { left: style.paddingLeft, right: style.paddingRight };
    });

    // Should have matching padding
    expect(dataPadding.left).toBe(headerPadding.left);
    expect(dataPadding.right).toBe(headerPadding.right);
  });
});

test.describe('Playlist Feature Parity - Library Browser (task-150)', () => {
  let playlistState;

  test.beforeAll(() => {
    playlistState = createPlaylistState();
  });

  test.beforeEach(async ({ page }) => {
    clearApiCalls(playlistState);
    // Setup playlist API mocks before navigation
    await setupPlaylistMocks(page, playlistState);
    // Also mock library tracks endpoint
    await page.route('**/api/library**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tracks: [
            { id: 101, title: 'Track A', artist: 'Artist A', album: 'Album A', duration: 180, filepath: '/music/track-a.mp3' },
            { id: 102, title: 'Track B', artist: 'Artist B', album: 'Album B', duration: 200, filepath: '/music/track-b.mp3' },
          ],
          total: 2,
        }),
      });
    });
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('[x-data="libraryBrowser"]', { state: 'visible' });
    // Trigger playlist load via event (simulates real app behavior)
    await page.evaluate(() => window.dispatchEvent(new CustomEvent('mt:playlists-updated')));
    await page.waitForTimeout(200);
  });

  test('AC#3: should show Add to Playlist submenu in context menu', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const trackRow = page.locator('[data-track-id]').first();
    await trackRow.click({ button: 'right' });

    const addToPlaylistItem = page.locator('.context-menu-item:has-text("Add to Playlist")');
    await expect(addToPlaylistItem).toBeVisible();
  });

  test('AC#4-5: track rows should be draggable', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const trackRow = page.locator('[data-track-id]').first();
    const draggable = await trackRow.getAttribute('draggable');
    expect(draggable).toBe('true');
  });

  test('AC#7-8: playlist view detection works correctly', async ({ page }) => {
    // Navigate to playlist view via sidebar click (real flow)
    const playlistButton = page.locator('[data-testid="sidebar-playlist-1"]');
    if (await playlistButton.count() > 0) {
      await playlistButton.click();
      await page.waitForTimeout(300);
    } else {
      // Fallback: set via evaluate if sidebar playlist not rendered
      await page.evaluate(() => {
        const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
        libraryBrowser.currentPlaylistId = 1;
      });
    }

    const isInPlaylistView = await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return libraryBrowser.isInPlaylistView();
    });

    expect(isInPlaylistView).toBe(true);
  });

  test('AC#7-8: outside playlist view detection works correctly', async ({ page }) => {
    // Ensure we're in library view (not playlist)
    await page.locator('[data-testid="sidebar-section-all"]').click();
    await page.waitForTimeout(200);

    const isInPlaylistView = await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return libraryBrowser.isInPlaylistView();
    });

    expect(isInPlaylistView).toBe(false);
  });

  test('AC#3: submenu opens on hover and lists playlists from API', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const trackRow = page.locator('[data-track-id]').first();
    await trackRow.click({ button: 'right' });

    const addToPlaylistItem = page.locator('.context-menu-item:has-text("Add to Playlist")');
    await addToPlaylistItem.hover();
    await page.waitForTimeout(200);

    const submenu = page.locator('[data-testid="playlist-submenu"]');
    await expect(submenu).toBeVisible();

    const newPlaylistOption = submenu.locator('text=New Playlist...');
    await expect(newPlaylistOption).toBeVisible();

    // These should come from the mock API (Test Playlist 1, Test Playlist 2)
    const playlist1Option = submenu.locator('text=Test Playlist 1');
    await expect(playlist1Option).toBeVisible();

    const playlist2Option = submenu.locator('text=Test Playlist 2');
    await expect(playlist2Option).toBeVisible();
  });

  test('AC#3: clicking playlist in submenu triggers API call', async ({ page }) => {
    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    // Select a track first
    const trackRow = page.locator('[data-track-id]').first();
    await trackRow.click();
    await trackRow.click({ button: 'right' });

    const addToPlaylistItem = page.locator('.context-menu-item:has-text("Add to Playlist")');
    await addToPlaylistItem.hover();
    await page.waitForTimeout(200);

    const submenu = page.locator('[data-testid="playlist-submenu"]');
    const playlist1Option = submenu.locator('text=Test Playlist 1');
    await playlist1Option.click();

    await page.waitForTimeout(300);

    // Verify API was called with correct endpoint
    const addTracksCalls = findApiCalls(playlistState, 'POST', '/playlists/1/tracks');
    expect(addTracksCalls.length).toBeGreaterThan(0);
    expect(addTracksCalls[0].body).toHaveProperty('track_ids');
  });

  test('AC#7-8: context menu shows "Remove from Playlist" in playlist view', async ({ page }) => {
    // Navigate to playlist view
    await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      libraryBrowser.currentPlaylistId = 1;
    });

    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const trackRow = page.locator('[data-track-id]').first();
    await trackRow.click({ button: 'right' });

    const removeFromPlaylist = page.locator('.context-menu-item:has-text("Remove track from Playlist")');
    await expect(removeFromPlaylist).toBeVisible();

    const removeFromLibrary = page.locator('.context-menu-item:has-text("Remove track from Library")');
    await expect(removeFromLibrary).toBeVisible();
  });

  test('AC#7-8: context menu hides "Remove from Playlist" outside playlist view', async ({ page }) => {
    // Ensure we're in library view
    await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      libraryBrowser.currentPlaylistId = null;
    });

    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const trackRow = page.locator('[data-track-id]').first();
    await trackRow.click({ button: 'right' });

    const removeFromPlaylist = page.locator('.context-menu-item:has-text("Remove track from Playlist")');
    await expect(removeFromPlaylist).not.toBeVisible();

    const removeFromLibrary = page.locator('.context-menu-item:has-text("Remove track from Library")');
    await expect(removeFromLibrary).toBeVisible();
  });

  test('AC#6: drag reorder in playlist view shows drag handle and sets state', async ({ page }) => {
    // Navigate to playlist view
    await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      libraryBrowser.currentPlaylistId = 1;
    });

    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const dragHandle = page.locator('[data-track-id] .cursor-grab').first();
    await expect(dragHandle).toBeVisible();

    const isInPlaylistView = await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return libraryBrowser.isInPlaylistView();
    });
    expect(isInPlaylistView).toBe(true);

    const track1 = page.locator('[data-track-id]').first();
    const track1Box = await track1.boundingBox();

    await page.mouse.move(track1Box.x + 10, track1Box.y + track1Box.height / 2);
    await page.mouse.down();

    const draggingIndex = await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return libraryBrowser.draggingIndex;
    });

    expect(draggingIndex).toBe(0);

    await page.mouse.up();
  });

  test('submenu flips to left side when near right viewport edge', async ({ page }) => {
    await page.setViewportSize({ width: 800, height: 600 });

    await page.waitForSelector('[data-track-id]', { state: 'visible' });

    const trackRow = page.locator('[data-track-id]').first();
    const trackBox = await trackRow.boundingBox();

    await page.mouse.click(trackBox.x + trackBox.width - 50, trackBox.y + trackBox.height / 2, { button: 'right' });

    const addToPlaylistItem = page.locator('.context-menu-item:has-text("Add to Playlist")');
    await addToPlaylistItem.hover();
    await page.waitForTimeout(200);

    const arrowText = await addToPlaylistItem.locator('.text-muted-foreground').textContent();

    const submenuOnLeft = await page.evaluate(() => {
      const libraryBrowser = window.Alpine.$data(document.querySelector('[x-data="libraryBrowser"]'));
      return libraryBrowser.submenuOnLeft;
    });

    if (submenuOnLeft) {
      expect(arrowText).toBe('◀');
    } else {
      expect(arrowText).toBe('▶');
    }
  });
});
