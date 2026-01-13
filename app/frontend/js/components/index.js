/**
 * Component Registry
 * 
 * Registers all Alpine.js components with the Alpine instance.
 * Import this module and call initComponents(Alpine) before Alpine.start().
 */

import { createLibraryBrowser } from './library-browser.js';

/**
 * Initialize all Alpine components
 * @param {object} Alpine - Alpine.js instance
 */
export function initComponents(Alpine) {
  // Register components
  createLibraryBrowser(Alpine);
  
  console.log('[components] All components registered');
}

export default initComponents;
