import Alpine from 'alpinejs';
import persist from '@alpinejs/persist';
import { initStores } from './js/stores/index.js';
import { initComponents } from './js/components/index.js';
import { setApiBase } from './js/api.js';
import './styles.css';

// Register Alpine plugins
Alpine.plugin(persist);

window.Alpine = Alpine;

window.handleFileDrop = async function(event) {
  console.log('[main] Browser drop event (Tauri handles via native events)');
};

async function initTauriDragDrop() {
  if (!window.__TAURI__) {
    console.log('[main] No Tauri environment detected');
    return;
  }
  
  console.log('[main] Tauri object keys:', Object.keys(window.__TAURI__));
  
  try {
    const { getCurrentWebview } = window.__TAURI__.webview;
    
    await getCurrentWebview().onDragDropEvent(async (event) => {
      console.log('[main] Drag-drop event:', event);
      const { type, paths, position } = event.payload;
      
      if (type === 'over') {
        console.log('[main] Drag over:', position);
      } else if (type === 'drop') {
        console.log('[main] Files dropped:', paths);
        
        if (paths && paths.length > 0) {
          try {
            const result = await Alpine.store('library').scan(paths);
            const ui = Alpine.store('ui');
            if (result.added > 0) {
              ui.toast(`Added ${result.added} track${result.added === 1 ? '' : 's'} to library`, 'success');
            } else if (result.skipped > 0) {
              ui.toast(`All ${result.skipped} track${result.skipped === 1 ? '' : 's'} already in library`, 'info');
            } else {
              ui.toast('No audio files found', 'info');
            }
          } catch (error) {
            console.error('[main] Failed to process dropped files:', error);
            Alpine.store('ui').toast('Failed to add files', 'error');
          }
        }
      } else if (type === 'cancel') {
        console.log('[main] Drag cancelled');
      }
    });
    
    console.log('[main] Tauri drag-drop listener initialized');
  } catch (error) {
    console.error('[main] Failed to initialize Tauri drag-drop:', error);
  }
}

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

window.testDialog = async function() {
  console.log('[test] Testing dialog...');
  console.log('[test] window.__TAURI__:', window.__TAURI__ ? Object.keys(window.__TAURI__) : 'undefined');
  console.log('[test] window.__TAURI__.dialog:', window.__TAURI__?.dialog);
  
  if (window.__TAURI__?.dialog?.open) {
    try {
      const result = await window.__TAURI__.dialog.open({ directory: true, multiple: true });
      console.log('[test] Dialog result:', result);
    } catch (e) {
      console.error('[test] Dialog error:', e);
    }
  } else {
    console.error('[test] dialog.open not available');
  }
};

// Initialize backend URL first, then register stores and start Alpine
initBackendUrl().then(() => {
  initStores(Alpine);
  initComponents(Alpine);
  initTauriDragDrop();
  Alpine.start();
  console.log('[main] Alpine started with stores and components');
  console.log('[main] Test dialog with: testDialog()');
});
