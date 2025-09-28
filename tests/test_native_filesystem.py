#!/usr/bin/env python3
"""Test native file system integration."""

import sys
import threading
import time
import webview
from decouple import config
from server import MTServer
from app.services.filesystem import filesystem_api


def test_native_filesystem():
    """Test the native file system API integration."""
    # Create server instance
    server = MTServer()

    # Start FastAPI server in background thread
    server.start_server()

    # Give server a moment to fully start
    time.sleep(1)

    # Create PyWebView window
    window = webview.create_window(
        title='MT Music Player - Native File System Test',
        url=f'http://{server.host}:{server.port}',
        width=1200,
        height=800,
        resizable=True,
        background_color='#1e1e1e',
    )

    # Set up file system API
    filesystem_api.set_window(window)

    # Expose API methods
    window.expose(filesystem_api.open_file_dialog)
    window.expose(filesystem_api.open_directory_dialog)
    window.expose(filesystem_api.save_file_dialog)
    window.expose(filesystem_api.validate_paths)
    window.expose(filesystem_api.get_path_info)
    window.expose(filesystem_api.list_directory)

    # Create a test API class
    class TestAPI:
        def test_directory_dialog(self):
            """Test opening directory dialog."""
            print("Opening directory dialog...")
            result = filesystem_api.open_directory_dialog("Select a directory to test")
            print(f"Selected directory: {result}")
            return result

        def test_file_dialog(self):
            """Test opening file dialog."""
            print("Opening file dialog...")
            result = filesystem_api.open_file_dialog(file_types=['mp3', 'flac', 'wav'], multiple=True, title="Select audio files")
            print(f"Selected files: {result}")
            return result

        def test_path_validation(self, paths):
            """Test path validation."""
            print(f"Validating paths: {paths}")
            result = filesystem_api.validate_paths(paths)
            print(f"Validation result: {result}")
            return result

    # Expose test API
    test_api = TestAPI()
    window.expose(test_api.test_directory_dialog)
    window.expose(test_api.test_file_dialog)
    window.expose(test_api.test_path_validation)

    print("Native file system test ready. Use browser console to test:")
    print("- pywebview.api.test_directory_dialog()")
    print("- pywebview.api.test_file_dialog()")
    print("- pywebview.api.test_path_validation(['/tmp', '/nonexistent'])")

    # Start PyWebView
    webview.start(debug=True)


if __name__ == '__main__':
    test_native_filesystem()
