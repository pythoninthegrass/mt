import Alpine from 'alpinejs';
import { initStores } from './js/stores/index.js';
import { initComponents } from './js/components/index.js';
import { setApiBase } from './js/api.js';
import './styles.css';

window.Alpine = Alpine;

initStores(Alpine);
initComponents(Alpine);

window.handleFileDrop = async function(event) {
  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;
  
  const paths = Array.from(files).map(f => f.path).filter(Boolean);
  if (paths.length === 0) return;
  
  try {
    const result = await Alpine.store('library').scan(paths);
    const ui = Alpine.store('ui');
    if (result.added > 0) {
      ui.toast(`Added ${result.added} track${result.added === 1 ? '' : 's'} to library`, 'success');
    } else if (result.skipped > 0) {
      ui.toast(`All ${result.skipped} track${result.skipped === 1 ? '' : 's'} already in library`, 'info');
    }
  } catch (error) {
    console.error('Failed to process dropped files:', error);
    Alpine.store('ui').toast('Failed to add files', 'error');
  }
};

async function initBackendUrl() {
  try {
    if (window.__TAURI__) {
      const { invoke } = window.__TAURI__.core;
      const url = await invoke('get_backend_url');
      setApiBase(url + '/api');
      console.log('[main] Backend URL:', url);
    }
  } catch (error) {
    console.warn('[main] Failed to get backend URL, using default:', error);
  }
}

initBackendUrl().then(() => {
  Alpine.start();
  console.log('[main] Alpine started with stores and components');
});
