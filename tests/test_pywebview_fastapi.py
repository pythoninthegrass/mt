#!/usr/bin/env python3
"""Integrated PyWebView + FastAPI example."""

import sys
import threading
import time
import webview
from decouple import config
from test_fastapi_server import app, start_server


def main():
    """Run PyWebView with FastAPI backend."""
    # Get server configuration
    host = config('SERVER_HOST', default='127.0.0.1')
    port = config('SERVER_PORT', default=3000, cast=int)
    
    # Start FastAPI server in background thread
    print("Starting FastAPI server...")
    server_thread = start_server()  # Uses config defaults
    
    # Give server a moment to fully start
    time.sleep(1)
    
    # Create PyWebView window pointing to FastAPI server
    print("Creating PyWebView window...")
    window = webview.create_window(
        title='MT Music Player - PyWebView + FastAPI',
        url=f'http://{host}:{port}',
        width=1200,
        height=800,
        resizable=True,
        background_color='#1e1e1e',
    )
    
    # Add API bridge for Python-JavaScript communication
    class Api:
        def get_system_info(self):
            """Example API method callable from JavaScript."""
            return {
                "platform": sys.platform,
                "python_version": sys.version,
                "message": "Called from JavaScript!"
            }
        
        def test_method(self, value):
            """Test method that receives and returns data."""
            print(f"Received from JS: {value}")
            return f"Echo from Python: {value}"
    
    # Expose API to JavaScript
    api = Api()
    window.expose(api.get_system_info)
    window.expose(api.test_method)
    
    # Start PyWebView
    print("Starting PyWebView...")
    webview.start(debug=True)


if __name__ == '__main__':
    main()