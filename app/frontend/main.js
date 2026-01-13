import Alpine from 'alpinejs';
import { initStores } from './js/stores/index.js';
import { initComponents } from './js/components/index.js';
import './styles.css';

// Make Alpine available globally for debugging
window.Alpine = Alpine;

// Initialize stores and components before starting Alpine
initStores(Alpine);
initComponents(Alpine);

// Start Alpine
Alpine.start();

console.log('[main] Alpine started with stores and components');
