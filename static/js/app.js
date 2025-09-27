// mt Music Player - HTMX Frontend JavaScript
// Handles client-side interactions, Alpine.js integrations, and HTMX enhancements

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast-enter">
            <div x-data="{ show: true }"
                 x-show="show"
                 x-init="setTimeout(() => show = false, ${duration})"
                 x-transition:enter="transition ease-out duration-300"
                 x-transition:enter-start="opacity-0 translate-x-full"
                 x-transition:enter-end="opacity-100 translate-x-0"
                 x-transition:leave="transition ease-in duration-200"
                 x-transition:leave-start="opacity-100 translate-x-0"
                 x-transition:leave-end="opacity-0 translate-x-full"
                 @click="show = false; setTimeout(() => $el.remove(), 200)"
                 class="bg-gray-900 border border-gray-800 rounded-lg shadow-lg p-4 min-w-[300px] max-w-md cursor-pointer">

                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        ${getToastIcon(type)}
                    </div>
                    <div class="flex-1">
                        <p class="text-sm text-gray-300">${message}</p>
                    </div>
                    <button @click.stop="show = false; setTimeout(() => $el.remove(), 200)"
                            class="flex-shrink-0 p-1 rounded hover:bg-gray-800 transition-colors">
                        <i class="bi bi-x text-gray-400"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    // Auto-remove after animation
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) toast.remove();
    }, duration + 500);
}

function getToastIcon(type) {
    switch (type) {
        case 'success':
            return '<i class="bi bi-check-circle-fill text-green-400 text-xl"></i>';
        case 'error':
            return '<i class="bi bi-x-circle-fill text-red-400 text-xl"></i>';
        case 'warning':
            return '<i class="bi bi-exclamation-triangle-fill text-yellow-400 text-xl"></i>';
        default:
            return '<i class="bi bi-info-circle-fill text-blue-400 text-xl"></i>';
    }
}

// Modal management
function showModal(content, title = '') {
    const modalContainer = document.getElementById('modal-container');
    if (!modalContainer) return;

    const modalHTML = `
        <div class="fixed inset-0 z-50 overflow-y-auto"
             x-data="{ open: true }"
             x-show="open"
             @keydown.escape.window="open = false; $el.remove()">

            <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                 x-show="open"
                 x-transition:enter="ease-out duration-300"
                 x-transition:enter-start="opacity-0"
                 x-transition:enter-end="opacity-100"
                 x-transition:leave="ease-in duration-200"
                 x-transition:leave-start="opacity-100"
                 x-transition:leave-end="opacity-0"
                 @click="open = false; $el.remove()"></div>

            <div class="relative min-h-screen flex items-center justify-center p-4">
                <div class="relative bg-gray-900 rounded-lg shadow-xl border border-gray-800 max-w-lg w-full"
                     x-show="open"
                     x-transition:enter="ease-out duration-300"
                     x-transition:enter-start="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                     x-transition:enter-end="opacity-100 translate-y-0 sm:scale-100"
                     x-transition:leave="ease-in duration-200"
                     x-transition:leave-start="opacity-100 translate-y-0 sm:scale-100"
                     x-transition:leave-end="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
                     @click.stop>

                    ${title ? `
                    <div class="flex items-center justify-between p-4 border-b border-gray-800">
                        <h3 class="text-lg font-semibold">${title}</h3>
                        <button @click="open = false; setTimeout(() => $el.remove(), 200)"
                                class="p-1 rounded hover:bg-gray-800 transition-colors">
                            <i class="bi bi-x-lg text-gray-400"></i>
                        </button>
                    </div>
                    ` : ''}

                    <div class="p-4">
                        ${content}
                    </div>
                </div>
            </div>
        </div>
    `;

    modalContainer.innerHTML = modalHTML;
}

function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.innerHTML = '';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Don't trigger shortcuts when typing in inputs
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }

    switch (event.key) {
        case ' ':
            // Spacebar - toggle play/pause
            event.preventDefault();
            htmx.ajax('POST', '/api/player/toggle', { swap: 'none' });
            break;
        case 'ArrowLeft':
            // Left arrow - previous track
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                htmx.ajax('POST', '/api/player/previous', { swap: 'none' });
            }
            break;
        case 'ArrowRight':
            // Right arrow - next track
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                htmx.ajax('POST', '/api/player/next', { swap: 'none' });
            }
            break;
        case 'ArrowUp':
            // Up arrow - increase volume
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                // Volume up logic would go here
            }
            break;
        case 'ArrowDown':
            // Down arrow - decrease volume
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                // Volume down logic would go here
            }
            break;
        case 'm':
        case 'M':
            // M - toggle mute
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                htmx.ajax('POST', '/api/player/mute', { swap: 'none' });
            }
            break;
        case 's':
        case 'S':
            // S - toggle shuffle
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                htmx.ajax('POST', '/api/player/shuffle', { swap: 'none' });
            }
            break;
        case 'r':
        case 'R':
            // R - toggle repeat
            if (event.ctrlKey || event.metaKey) {
                event.preventDefault();
                htmx.ajax('POST', '/api/player/repeat', { swap: 'none' });
            }
            break;
    }
});

// HTMX event handlers
document.addEventListener('DOMContentLoaded', function() {
    // HTMX configuration
    htmx.config.globalViewTransitions = true;
    htmx.config.useTemplateFragments = true;

    // Custom event listeners
    document.body.addEventListener('show-toast', function(event) {
        const { message, type, duration } = event.detail;
        showToast(message, type, duration);
    });

    document.body.addEventListener('show-modal', function(event) {
        const { content, title } = event.detail;
        showModal(content, title);
    });

    document.body.addEventListener('close-modal', function() {
        closeModal();
    });

    // Track selection and drag/drop
    let draggedElement = null;

    document.addEventListener('dragstart', function(event) {
        if (event.target.closest('[draggable="true"]')) {
            draggedElement = event.target.closest('[draggable="true"]');
            draggedElement.classList.add('opacity-50');
        }
    });

    document.addEventListener('dragend', function(event) {
        if (draggedElement) {
            draggedElement.classList.remove('opacity-50');
            draggedElement = null;
        }
    });

    // Progress bar interaction
    document.addEventListener('input', function(event) {
        if (event.target.id === 'progress-bar') {
            const value = event.target.value;
            // Update progress visually
            const progressFill = event.target.nextElementSibling;
            if (progressFill) {
                progressFill.style.width = value + '%';
            }
        }
    });

    // Volume slider interaction
    document.addEventListener('input', function(event) {
        if (event.target.id === 'volume-slider') {
            const value = event.target.value;
            // Update volume visually
            const volumeFill = event.target.nextElementSibling;
            if (volumeFill) {
                volumeFill.style.width = value + '%';
            }
        }
    });
});

// Utility functions
function formatDuration(seconds) {
    if (!seconds || seconds === 0) return '0:00';

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search functionality
const searchInput = document.querySelector('input[name="q"]');
if (searchInput) {
    searchInput.addEventListener('input', debounce(function(event) {
        const query = event.target.value.trim();
        if (query.length > 2) {
            // Trigger search
            htmx.ajax('GET', `/api/search?q=${encodeURIComponent(query)}`, {
                target: '#search-results',
                swap: 'innerHTML'
            });
        } else {
            // Clear results
            const results = document.getElementById('search-results');
            if (results) results.innerHTML = '';
        }
    }, 300));
}

// Theme management
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Update Alpine.js data
    if (window.Alpine && Alpine.store) {
        Alpine.store('theme', theme);
    }
}

// Initialize theme on load
const savedTheme = localStorage.getItem('theme') || 'dark';
setTheme(savedTheme);

// Export functions for global use
window.showToast = showToast;
window.showModal = showModal;
window.closeModal = closeModal;
window.formatDuration = formatDuration;
window.setTheme = setTheme;