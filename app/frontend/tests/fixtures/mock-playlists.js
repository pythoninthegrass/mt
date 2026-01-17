/**
 * Mock Playlists API for Playwright tests
 * 
 * Provides route handlers that simulate the backend playlist API.
 * State is shared across tests within a describe block when using
 * setupPlaylistMocks() in beforeAll/beforeEach.
 */

/**
 * Create a fresh playlist mock state
 * @returns {Object} Mutable state object for playlists
 */
export function createPlaylistState() {
  return {
    playlists: [
      { id: 1, name: 'Test Playlist 1', position: 0, created_at: '2026-01-15T00:00:00Z' },
      { id: 2, name: 'Test Playlist 2', position: 1, created_at: '2026-01-15T01:00:00Z' },
      { id: 3, name: 'Test Playlist 3', position: 2, created_at: '2026-01-15T02:00:00Z' },
    ],
    playlistTracks: {
      1: [
        { position: 0, added_at: '2026-01-15T00:00:00Z', track: { id: 101, title: 'Track A', artist: 'Artist A', album: 'Album A', duration: 180, filepath: '/music/track-a.mp3' } },
        { position: 1, added_at: '2026-01-15T00:01:00Z', track: { id: 102, title: 'Track B', artist: 'Artist B', album: 'Album B', duration: 200, filepath: '/music/track-b.mp3' } },
      ],
      2: [
        { position: 0, added_at: '2026-01-15T01:00:00Z', track: { id: 103, title: 'Track C', artist: 'Artist C', album: 'Album C', duration: 220, filepath: '/music/track-c.mp3' } },
      ],
      3: [],
    },
    nextPlaylistId: 4,
    // Track API calls for assertions
    apiCalls: [],
  };
}

/**
 * Setup playlist API mocks on a Playwright page
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {Object} state - Mutable state from createPlaylistState()
 */
export async function setupPlaylistMocks(page, state) {
  // GET /api/playlists - list all playlists
  await page.route('**/api/playlists', async (route, request) => {
    if (request.method() === 'GET') {
      state.apiCalls.push({ method: 'GET', url: '/api/playlists' });
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(state.playlists),
      });
    } else if (request.method() === 'POST') {
      // POST /api/playlists - create playlist
      const body = request.postDataJSON();
      state.apiCalls.push({ method: 'POST', url: '/api/playlists', body });
      const newPlaylist = {
        id: state.nextPlaylistId++,
        name: body.name,
        position: state.playlists.length,
        created_at: new Date().toISOString(),
      };
      state.playlists.push(newPlaylist);
      state.playlistTracks[newPlaylist.id] = [];
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newPlaylist),
      });
    } else {
      await route.continue();
    }
  });

  // GET /api/playlists/generate-name - generate unique name
  await page.route('**/api/playlists/generate-name*', async (route, request) => {
    const url = new URL(request.url());
    const base = url.searchParams.get('base') || 'New playlist';
    state.apiCalls.push({ method: 'GET', url: '/api/playlists/generate-name', base });
    
    // Generate unique name
    let name = base;
    let suffix = 2;
    const existingNames = new Set(state.playlists.map(p => p.name));
    while (existingNames.has(name)) {
      name = `${base} (${suffix})`;
      suffix++;
    }
    
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ name }),
    });
  });

  // GET/PUT/DELETE /api/playlists/:id
  await page.route(/\/api\/playlists\/(\d+)$/, async (route, request) => {
    const match = request.url().match(/\/api\/playlists\/(\d+)$/);
    const playlistId = parseInt(match[1], 10);
    const method = request.method();
    
    if (method === 'GET') {
      state.apiCalls.push({ method: 'GET', url: `/api/playlists/${playlistId}` });
      const playlist = state.playlists.find(p => p.id === playlistId);
      if (!playlist) {
        await route.fulfill({ status: 404, body: JSON.stringify({ error: 'Not found' }) });
        return;
      }
      const tracks = state.playlistTracks[playlistId] || [];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...playlist, tracks }),
      });
    } else if (method === 'PUT') {
      // Rename playlist
      const body = request.postDataJSON();
      state.apiCalls.push({ method: 'PUT', url: `/api/playlists/${playlistId}`, body });
      const playlist = state.playlists.find(p => p.id === playlistId);
      if (playlist) {
        playlist.name = body.name;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(playlist),
      });
    } else if (method === 'DELETE') {
      state.apiCalls.push({ method: 'DELETE', url: `/api/playlists/${playlistId}` });
      state.playlists = state.playlists.filter(p => p.id !== playlistId);
      delete state.playlistTracks[playlistId];
      await route.fulfill({ status: 204 });
    } else {
      await route.continue();
    }
  });

  // POST /api/playlists/:id/tracks - add tracks to playlist
  await page.route(/\/api\/playlists\/(\d+)\/tracks$/, async (route, request) => {
    if (request.method() !== 'POST') {
      await route.continue();
      return;
    }
    const match = request.url().match(/\/api\/playlists\/(\d+)\/tracks$/);
    const playlistId = parseInt(match[1], 10);
    const body = request.postDataJSON();
    state.apiCalls.push({ method: 'POST', url: `/api/playlists/${playlistId}/tracks`, body });
    
    const tracks = state.playlistTracks[playlistId] || [];
    const existingTrackIds = new Set(tracks.map(t => t.track.id));
    let added = 0;
    let skipped = 0;
    
    for (const trackId of body.track_ids) {
      if (existingTrackIds.has(trackId)) {
        skipped++;
      } else {
        tracks.push({
          position: tracks.length,
          added_at: new Date().toISOString(),
          track: { id: trackId, title: `Track ${trackId}`, artist: `Artist ${trackId}`, album: `Album ${trackId}`, duration: 180 },
        });
        added++;
      }
    }
    state.playlistTracks[playlistId] = tracks;
    
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ added, skipped }),
    });
  });

  // DELETE /api/playlists/:id/tracks/:position - remove track from playlist
  await page.route(/\/api\/playlists\/(\d+)\/tracks\/(\d+)$/, async (route, request) => {
    if (request.method() !== 'DELETE') {
      await route.continue();
      return;
    }
    const match = request.url().match(/\/api\/playlists\/(\d+)\/tracks\/(\d+)$/);
    const playlistId = parseInt(match[1], 10);
    const position = parseInt(match[2], 10);
    state.apiCalls.push({ method: 'DELETE', url: `/api/playlists/${playlistId}/tracks/${position}` });
    
    const tracks = state.playlistTracks[playlistId] || [];
    if (position >= 0 && position < tracks.length) {
      tracks.splice(position, 1);
      // Re-index positions
      tracks.forEach((t, i) => { t.position = i; });
    }
    state.playlistTracks[playlistId] = tracks;
    
    await route.fulfill({ status: 204 });
  });

  // POST /api/playlists/:id/tracks/reorder - reorder tracks in playlist
  await page.route(/\/api\/playlists\/(\d+)\/tracks\/reorder$/, async (route, request) => {
    if (request.method() !== 'POST') {
      await route.continue();
      return;
    }
    const match = request.url().match(/\/api\/playlists\/(\d+)\/tracks\/reorder$/);
    const playlistId = parseInt(match[1], 10);
    const body = request.postDataJSON();
    state.apiCalls.push({ method: 'POST', url: `/api/playlists/${playlistId}/tracks/reorder`, body });
    
    const tracks = state.playlistTracks[playlistId] || [];
    const { from_position, to_position } = body;
    if (from_position >= 0 && from_position < tracks.length && to_position >= 0 && to_position < tracks.length) {
      const [moved] = tracks.splice(from_position, 1);
      tracks.splice(to_position, 0, moved);
      tracks.forEach((t, i) => { t.position = i; });
    }
    state.playlistTracks[playlistId] = tracks;
    
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true }),
    });
  });

  // POST /api/playlists/reorder - reorder playlists in sidebar
  await page.route('**/api/playlists/reorder', async (route, request) => {
    if (request.method() !== 'POST') {
      await route.continue();
      return;
    }
    const body = request.postDataJSON();
    state.apiCalls.push({ method: 'POST', url: '/api/playlists/reorder', body });
    
    const { from_position, to_position } = body;
    if (from_position >= 0 && from_position < state.playlists.length && to_position >= 0 && to_position < state.playlists.length) {
      const [moved] = state.playlists.splice(from_position, 1);
      state.playlists.splice(to_position, 0, moved);
      state.playlists.forEach((p, i) => { p.position = i; });
    }
    
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true }),
    });
  });
}

/**
 * Helper to clear API call history (useful between tests)
 * @param {Object} state - State from createPlaylistState()
 */
export function clearApiCalls(state) {
  state.apiCalls = [];
}

/**
 * Helper to find API calls matching criteria
 * @param {Object} state - State from createPlaylistState()
 * @param {string} method - HTTP method
 * @param {string|RegExp} urlPattern - URL pattern to match
 * @returns {Array} Matching API calls
 */
export function findApiCalls(state, method, urlPattern) {
  return state.apiCalls.filter(call => {
    if (call.method !== method) return false;
    if (typeof urlPattern === 'string') {
      return call.url.includes(urlPattern);
    }
    return urlPattern.test(call.url);
  });
}
