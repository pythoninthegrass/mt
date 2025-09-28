/**
 * PyWebView File System API Integration
 *
 * Provides a JavaScript interface to PyWebView's native file system capabilities.
 * This module handles communication with the Python FileSystemAPI and provides
 * promise-based methods for file operations.
 */

class FileSystemAPI {
    constructor() {
        this._checkAvailability();
    }

    /**
     * Check if the PyWebView API is available
     */
    _checkAvailability() {
        if (typeof window.pywebview === 'undefined' || !window.pywebview.api) {
            console.warn('PyWebView API not available. File system operations will not work.');
            this.available = false;
        } else {
            this.available = true;
        }
    }

    /**
     * Open a native file selection dialog
     *
     * @param {Object} options - Dialog options
     * @param {Array<string>} options.fileTypes - Array of file extensions (e.g., ['mp3', 'flac'])
     * @param {boolean} options.multiple - Allow multiple file selection
     * @param {string} options.title - Dialog title
     * @returns {Promise<Array<string>>} Promise resolving to array of selected file paths
     */
    async openFileDialog(options = {}) {
        if (!this.available) {
            throw new Error('PyWebView API not available');
        }

        const { fileTypes = [], multiple = false, title = 'Select Files' } = options;

        try {
            const result = await window.pywebview.api.open_file_dialog(fileTypes, multiple, title);
            return result || [];
        } catch (error) {
            console.error('Error opening file dialog:', error);
            throw error;
        }
    }

    /**
     * Open a native directory selection dialog
     *
     * @param {string} title - Dialog title
     * @returns {Promise<string|null>} Promise resolving to selected directory path or null
     */
    async openDirectoryDialog(title = 'Select Directory') {
        if (!this.available) {
            throw new Error('PyWebView API not available');
        }

        try {
            const result = await window.pywebview.api.open_directory_dialog(title);
            return result;
        } catch (error) {
            console.error('Error opening directory dialog:', error);
            throw error;
        }
    }

    /**
     * Open a native file save dialog
     *
     * @param {Object} options - Dialog options
     * @param {string} options.defaultFilename - Default filename to suggest
     * @param {Array<string>} options.fileTypes - Array of file extensions
     * @param {string} options.title - Dialog title
     * @returns {Promise<string|null>} Promise resolving to selected file path or null
     */
    async openSaveDialog(options = {}) {
        if (!this.available) {
            throw new Error('PyWebView API not available');
        }

        const { defaultFilename = '', fileTypes = [], title = 'Save File' } = options;

        try {
            const result = await window.pywebview.api.save_file_dialog(defaultFilename, fileTypes, title);
            return result;
        } catch (error) {
            console.error('Error opening save dialog:', error);
            throw error;
        }
    }

    /**
     * Validate file/directory paths
     *
     * @param {Array<string>} paths - Array of paths to validate
     * @returns {Promise<Object>} Promise resolving to validation results
     */
    async validatePaths(paths) {
        if (!this.available) {
            throw new Error('PyWebView API not available');
        }

        if (!Array.isArray(paths)) {
            paths = [paths];
        }

        try {
            const result = await window.pywebview.api.validate_paths(paths);
            return result;
        } catch (error) {
            console.error('Error validating paths:', error);
            throw error;
        }
    }

    /**
     * Get information about a file or directory path
     *
     * @param {string} path - Path to analyze
     * @returns {Promise<Object|null>} Promise resolving to path information or null
     */
    async getPathInfo(path) {
        if (!this.available) {
            throw new Error('PyWebView API not available');
        }

        try {
            const result = await window.pywebview.api.get_path_info(path);
            return result;
        } catch (error) {
            console.error('Error getting path info:', error);
            throw error;
        }
    }

    /**
     * List contents of a directory
     *
     * @param {string} path - Directory path to list
     * @param {Object} options - Listing options
     * @param {boolean} options.recursive - List subdirectories recursively
     * @param {number} options.maxDepth - Maximum recursion depth
     * @returns {Promise<Object>} Promise resolving to directory listing
     */
    async listDirectory(path, options = {}) {
        if (!this.available) {
            throw new Error('PyWebView API not available');
        }

        const { recursive = false, maxDepth = 3 } = options;

        try {
            const result = await window.pywebview.api.list_directory(path, recursive, maxDepth);
            return result;
        } catch (error) {
            console.error('Error listing directory:', error);
            throw error;
        }
    }

    /**
     * Check if the file system API is available
     *
     * @returns {boolean} True if API is available
     */
    isAvailable() {
        return this.available;
    }
}

// Create global instance
const filesystemAPI = new FileSystemAPI();

// Export for use in other modules
window.FileSystemAPI = filesystemAPI;

// Convenience functions for direct use
window.openFileDialog = (options) => filesystemAPI.openFileDialog(options);
window.openDirectoryDialog = (title) => filesystemAPI.openDirectoryDialog(title);
window.openSaveDialog = (options) => filesystemAPI.openSaveDialog(options);
window.validatePaths = (paths) => filesystemAPI.validatePaths(paths);
window.getPathInfo = (path) => filesystemAPI.getPathInfo(path);
window.listDirectory = (path, options) => filesystemAPI.listDirectory(path, options);