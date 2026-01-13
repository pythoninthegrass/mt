/**
 * Component Registry
 * 
 * Registers all Alpine.js components with the Alpine instance.
 * Import this module and call initComponents(Alpine) before Alpine.start().
 */

import { createLibraryBrowser } from './library-browser.js';
import { createPlayerControls } from './player-controls.js';
import { createSidebar } from './sidebar.js';

/**
 * Initialize all Alpine components
 * @param {object} Alpine - Alpine.js instance
 */
export function initComponents(Alpine) {
  createLibraryBrowser(Alpine);
  createPlayerControls(Alpine);
  createSidebar(Alpine);
  
  console.log('[components] All components registered');
}

export default initComponents;
