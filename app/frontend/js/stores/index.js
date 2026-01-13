/**
 * Store Registry
 * 
 * Registers all Alpine.js stores with the Alpine instance.
 * Import this module and call initStores(Alpine) before Alpine.start().
 */

import { createPlayerStore } from './player.js';
import { createQueueStore } from './queue.js';
import { createLibraryStore } from './library.js';
import { createUIStore } from './ui.js';

/**
 * Initialize all Alpine stores
 * @param {object} Alpine - Alpine.js instance
 */
export function initStores(Alpine) {
  // Register stores in dependency order
  // UI store first (no dependencies)
  createUIStore(Alpine);
  
  // Library store (no store dependencies, uses API)
  createLibraryStore(Alpine);
  
  // Queue store (may reference library)
  createQueueStore(Alpine);
  
  // Player store (may reference queue)
  createPlayerStore(Alpine);
  
  console.log('[stores] All stores registered');
}

export default initStores;
