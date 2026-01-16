import { test, expect } from '@playwright/test';
import {
  waitForAlpine,
  getAlpineStore,
} from './fixtures/helpers.js';

test.describe('Sidebar Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
  });

  test('should display sidebar sections', async ({ page }) => {
    // Wait for sidebar to be visible
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });

    // Verify sidebar contains library sections
    const librarySections = page.locator('aside button');
    const count = await librarySections.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should navigate between sections', async ({ page }) => {
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });

    // Get initial section
    const libraryStore = await getAlpineStore(page, 'library');
    const initialSection = libraryStore.currentSection;

    // Find and click a different section
    const sections = page.locator('aside button');
    const count = await sections.count();

    if (count > 1) {
      // Click second section
      await sections.nth(1).click();
      await page.waitForTimeout(500);

      // Verify section changed
      const updatedStore = await getAlpineStore(page, 'library');
      expect(updatedStore.currentSection).not.toBe(initialSection);
    }
  });

  test('should highlight active section', async ({ page }) => {
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });

    // Click first section
    const firstSection = page.locator('aside button').first();
    await firstSection.click();
    await page.waitForTimeout(300);

    // Verify section is highlighted (has bg-primary or similar class)
    const classes = await firstSection.getAttribute('class');
    expect(classes).toContain('bg-primary');
  });

  test('should show section icons', async ({ page }) => {
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });

    // Verify sections have icons (SVG elements)
    const sectionIcons = page.locator('aside button svg');
    const count = await sectionIcons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show section labels when expanded', async ({ page }) => {
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });

    // Ensure sidebar is expanded
    const sidebarStore = await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      if (sidebar.isCollapsed) {
        sidebar.toggleCollapse();
      }
      return sidebar;
    });

    // Verify section labels are visible
    const sectionLabels = page.locator('aside button span');
    const count = await sectionLabels.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Sidebar Collapse/Expand', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });
  });

  test('should collapse sidebar when clicking collapse button', async ({ page }) => {
    // Ensure sidebar starts expanded
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.isCollapsed = false;
    });

    // Get initial width
    const sidebar = page.locator('aside[x-data="sidebar"]');
    const initialBox = await sidebar.boundingBox();

    // Click collapse button
    const collapseButton = page.locator('aside button[title*="Collapse"], aside button[title*="Expand"]').last();
    await collapseButton.click();

    // Wait for transition
    await page.waitForTimeout(300);

    // Verify sidebar width changed
    const collapsedBox = await sidebar.boundingBox();
    expect(collapsedBox.width).toBeLessThan(initialBox.width);
  });

  test('should expand sidebar when clicking expand button', async ({ page }) => {
    // Collapse sidebar first
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.isCollapsed = true;
    });

    await page.waitForTimeout(300);

    // Get collapsed width
    const sidebar = page.locator('aside[x-data="sidebar"]');
    const collapsedBox = await sidebar.boundingBox();

    // Click expand button
    const expandButton = page.locator('aside button[title*="Expand"], aside button[title*="Collapse"]').last();
    await expandButton.click();

    // Wait for transition
    await page.waitForTimeout(300);

    // Verify sidebar width increased
    const expandedBox = await sidebar.boundingBox();
    expect(expandedBox.width).toBeGreaterThan(collapsedBox.width);
  });

  test('should hide section labels when collapsed', async ({ page }) => {
    // Collapse sidebar
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.isCollapsed = true;
    });

    await page.waitForTimeout(300);

    // Verify labels are hidden
    const sectionLabels = page.locator('aside button span:not([x-show="isCollapsed"])');
    const visible = await sectionLabels.first().isVisible().catch(() => false);
    expect(visible).toBe(false);
  });

  test('should show only icons when collapsed', async ({ page }) => {
    // Collapse sidebar
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.isCollapsed = true;
    });

    await page.waitForTimeout(300);

    // Verify icons are still visible
    const icons = page.locator('aside button svg');
    const firstIcon = await icons.first().isVisible();
    expect(firstIcon).toBe(true);
  });

  test('should persist collapse state', async ({ page }) => {
    // Toggle collapse
    const collapseButton = page.locator('aside button').last();
    await collapseButton.click();
    await page.waitForTimeout(300);

    // Get collapsed state
    const isCollapsedBefore = await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      return sidebar.isCollapsed;
    });

    // Reload page
    await page.reload();
    await waitForAlpine(page);
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });
    await page.waitForTimeout(500);

    // Verify state is persisted (localStorage)
    const isCollapsedAfter = await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      return sidebar.isCollapsed;
    });

    expect(isCollapsedAfter).toBe(isCollapsedBefore);
  });
});

test.describe('Search Input', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });
  });

  test('should show search input in sidebar', async ({ page }) => {
    // Verify search input exists
    const searchInput = page.locator('aside input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible();
  });

  test('should update library search when typing', async ({ page }) => {
    const searchInput = page.locator('aside input[placeholder*="Search"]');
    await searchInput.fill('test query');

    // Wait for debounce
    await page.waitForTimeout(500);

    // Verify library search is updated
    const libraryStore = await getAlpineStore(page, 'library');
    expect(libraryStore.searchQuery).toBe('test query');
  });

  test('should show clear button when search has value', async ({ page }) => {
    const searchInput = page.locator('aside input[placeholder*="Search"]');
    await searchInput.fill('query');

    // Verify clear button appears
    const clearButton = page.locator('aside button:near(input[placeholder*="Search"])');
    await expect(clearButton.first()).toBeVisible();
  });

  test('should clear search when clicking clear button', async ({ page }) => {
    const searchInput = page.locator('aside input[placeholder*="Search"]');
    await searchInput.fill('query');
    await page.waitForTimeout(500);

    // Click clear button
    const clearButton = page.locator('aside input[placeholder*="Search"] ~ button').first();
    await clearButton.click();

    // Verify search is cleared
    const value = await searchInput.inputValue();
    expect(value).toBe('');
  });

  test('should hide search input when sidebar is collapsed', async ({ page }) => {
    // Ensure sidebar is expanded first
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.isCollapsed = false;
    });

    // Verify search is visible
    let searchInput = page.locator('aside input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible();

    // Collapse sidebar
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.isCollapsed = true;
    });

    await page.waitForTimeout(300);

    // Verify search is hidden
    searchInput = page.locator('aside input[placeholder*="Search"]');
    const visible = await searchInput.isVisible().catch(() => false);
    expect(visible).toBe(false);
  });
});

test.describe('Playlists Section', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);
    await page.waitForSelector('aside[x-data="sidebar"]', { state: 'visible' });
  });

  test('should show playlists section header', async ({ page }) => {
    // Verify playlists header exists
    const playlistsHeader = page.locator('aside:has-text("Playlists")');
    await expect(playlistsHeader).toBeVisible();
  });

  test('should show create playlist button', async ({ page }) => {
    // Verify create button exists (+ icon)
    const createButton = page.locator('aside button[title*="Playlist"]');
    const count = await createButton.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should show empty state when no playlists', async ({ page }) => {
    // Set playlists to empty
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [];
    });

    await page.waitForTimeout(300);

    // Verify empty message
    const emptyMessage = page.locator('aside:has-text("No playlists")');
    await expect(emptyMessage).toBeVisible();
  });

  test('should list playlists when available', async ({ page }) => {
    // Add mock playlists
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [
        { id: 'playlist-1', name: 'Test Playlist 1' },
        { id: 'playlist-2', name: 'Test Playlist 2' },
      ];
    });

    await page.waitForTimeout(300);

    // Verify playlists are displayed
    const playlistItems = page.locator('aside button:has-text("Test Playlist")');
    const count = await playlistItems.count();
    expect(count).toBe(2);
  });

  test('should highlight active playlist', async ({ page }) => {
    // Add mock playlists
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [
        { id: 'playlist-1', name: 'Test Playlist 1' },
      ];
      sidebar.activeSection = 'playlist-1';
    });

    await page.waitForTimeout(300);

    // Find playlist button
    const playlistButton = page.locator('aside button:has-text("Test Playlist 1")');

    // Verify it's highlighted
    const classes = await playlistButton.getAttribute('class');
    expect(classes).toContain('bg-primary');
  });

  test('should navigate to playlist when clicked', async ({ page }) => {
    // Add mock playlists
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [
        { id: 'playlist-1', name: 'Test Playlist 1' },
      ];
    });

    await page.waitForTimeout(300);

    // Click playlist
    const playlistButton = page.locator('aside button:has-text("Test Playlist 1")');
    await playlistButton.click();

    await page.waitForTimeout(300);

    // Verify navigation occurred
    const sidebarData = await page.evaluate(() => {
      return window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
    });

    expect(sidebarData.activeSection).toBe('playlist-1');
  });

  test('should show context menu on right-click (task-147)', async ({ page }) => {
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [
        { id: 'playlist-1', playlistId: 1, name: 'Test Playlist' },
      ];
    });

    await page.waitForTimeout(300);

    const playlistButton = page.locator('aside button:has-text("Test Playlist")');
    await playlistButton.click({ button: 'right' });

    await page.waitForTimeout(200);

    const contextMenu = page.locator('[data-testid="playlist-context-menu"]');
    await expect(contextMenu).toBeVisible();

    const renameOption = page.locator('[data-testid="playlist-rename"]');
    await expect(renameOption).toBeVisible();

    const deleteOption = page.locator('[data-testid="playlist-delete"]');
    await expect(deleteOption).toBeVisible();
  });

  test('should hide context menu when clicking away (task-147)', async ({ page }) => {
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [
        { id: 'playlist-1', playlistId: 1, name: 'Test Playlist' },
      ];
    });

    await page.waitForTimeout(300);

    const playlistButton = page.locator('aside button:has-text("Test Playlist")');
    await playlistButton.click({ button: 'right' });

    await page.waitForTimeout(200);

    const contextMenu = page.locator('[data-testid="playlist-context-menu"]');
    await expect(contextMenu).toBeVisible();

    await page.click('main');
    await page.waitForTimeout(200);

    await expect(contextMenu).not.toBeVisible();
  });

  test('should hide context menu on escape key (task-147)', async ({ page }) => {
    await page.evaluate(() => {
      const sidebar = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sidebar.playlists = [
        { id: 'playlist-1', playlistId: 1, name: 'Test Playlist' },
      ];
    });

    await page.waitForTimeout(300);

    const playlistButton = page.locator('aside button:has-text("Test Playlist")');
    await playlistButton.click({ button: 'right' });

    await page.waitForTimeout(200);

    const contextMenu = page.locator('[data-testid="playlist-context-menu"]');
    await expect(contextMenu).toBeVisible();

    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    await expect(contextMenu).not.toBeVisible();
  });
});

test.describe('Sidebar Responsiveness', () => {
  test('should adjust sidebar width based on collapse state', async ({ page }) => {
    await page.goto('/');
    await waitForAlpine(page);

    const sidebar = page.locator('aside[x-data="sidebar"]');

    // Expanded state
    await page.evaluate(() => {
      const sb = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sb.isCollapsed = false;
    });
    await page.waitForTimeout(300);

    const expandedWidth = (await sidebar.boundingBox()).width;

    // Collapsed state
    await page.evaluate(() => {
      const sb = window.Alpine.$data(document.querySelector('aside[x-data="sidebar"]'));
      sb.isCollapsed = true;
    });
    await page.waitForTimeout(300);

    const collapsedWidth = (await sidebar.boundingBox()).width;

    expect(collapsedWidth).toBeLessThan(expandedWidth);
    expect(collapsedWidth).toBeLessThan(100); // Should be narrow when collapsed
  });
});
