import Alpine from 'alpinejs';
import { initStores } from './js/stores/index.js';
import './styles.css';

// Make Alpine available globally for debugging
window.Alpine = Alpine;

// Initialize all stores before starting Alpine
initStores(Alpine);

// Start Alpine
Alpine.start();

console.log('[main] Alpine started with stores');
