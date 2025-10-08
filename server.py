#!/usr/bin/env python3
"""PyWebView + FastAPI server for mt music player."""

import os
import signal
import sys
import threading
import time
import uvicorn
import webview
from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path


class MTServer:
    """Server for mt music player with PyWebView and FastAPI."""
    
    def __init__(self, host=None, port=None):
        self.host = host or config('SERVER_HOST', default='127.0.0.1')
        self.port = int(port or config('SERVER_PORT', default=3000, cast=int))
        
        # Environment configuration
        self.debug = config('DEBUG', default=False, cast=bool)
        self.hot_reload = config('HOT_RELOAD', default=False, cast=bool)
        self.cors_enabled = config('CORS_ENABLED', default=self.debug, cast=bool)
        self.app_title = config('APP_TITLE', default='mt music player')
        
        # Server components
        self.app = self.create_app()
        self.server_thread = None
        self.window = None
        self.observer = None
    
    def create_app(self):
        """Create FastAPI application."""
        app = FastAPI(
            title=self.app_title,
            debug=self.debug
        )
        
        # Add CORS if enabled
        if self.cors_enabled:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        @app.get("/", response_class=HTMLResponse)
        async def root():
            mode = "Development" if self.debug else "Production"
            port = self.port
            
            # Build feature list dynamically
            features = ["✅ PyWebView window active", f"✅ FastAPI server on port {port}"]
            if self.hot_reload:
                features.append("✅ Hot-reload enabled")
            if self.cors_enabled:
                features.append("✅ CORS enabled")
            if self.debug:
                features.append("✅ Debug mode active")
            
            features_html = "\n".join(f"<li>{feature}</li>" for feature in features)
            
            # Auto-reload script only in dev mode with hot reload
            reload_script = ""
            if self.hot_reload:
                reload_script = """
                    // Auto-reload on server restart
                    let lastCheck = Date.now();
                    setInterval(async () => {
                        try {
                            const response = await fetch('/api/health');
                            const data = await response.json();
                            if (data.timestamp && Math.abs(data.timestamp * 1000 - lastCheck) > 5000) {
                                location.reload();
                            }
                        } catch (e) {
                            // Server might be restarting
                        }
                    }, 1000);
                """
            
            return f"""
            <html>
            <head>
                <title>{self.app_title}</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #1e1e1e;
                        color: #e0e0e0;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 20px;
                        border-radius: 10px;
                        margin-bottom: 20px;
                    }}
                    .info {{
                        background: #2a2a2a;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 10px 0;
                    }}
                    .status {{
                        display: inline-block;
                        padding: 5px 10px;
                        background: {'#22c55e' if self.debug else '#3b82f6'};
                        color: white;
                        border-radius: 5px;
                        font-size: 12px;
                        margin-left: 10px;
                    }}
                    code {{
                        background: #3a3a3a;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: 'Monaco', 'Menlo', monospace;
                    }}
                    button {{
                        background: #667eea;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 14px;
                        margin-top: 10px;
                    }}
                    button:hover {{
                        background: #764ba2;
                    }}
                    #result {{
                        margin-top: 10px;
                        padding: 10px;
                        background: #1a1a1a;
                        border-radius: 5px;
                        font-family: monospace;
                    }}
                </style>
                <script>
                    {reload_script}
                    
                    // PyWebView API detection
                    window.addEventListener('pywebviewready', () => {{
                        console.log('PyWebView API ready');
                        if (window.pywebview && window.pywebview.api) {{
                            console.log('Available API:', Object.keys(window.pywebview.api));
                        }}
                    }});
                </script>
            </head>
            <body>
                <div class="header">
                    <h1>{self.app_title}</h1>
                    <p>PyWebView + FastAPI <span class="status">{mode.upper()}</span></p>
                </div>
                
                <div class="info">
                    <h3>Server Status</h3>
                    <ul>
                        {features_html}
                    </ul>
                </div>
                
                <div class="info">
                    <h3>API Test</h3>
                    <p>Test the server API endpoint:</p>
                    <button onclick="testAPI()">Test API</button>
                    <div id="result"></div>
                    <script>
                        async function testAPI() {{
                            const result = document.getElementById('result');
                            try {{
                                const response = await fetch('/api/test');
                                const data = await response.json();
                                result.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                            }} catch (e) {{
                                result.innerHTML = 'Error: ' + e.message;
                            }}
                        }}
                    </script>
                </div>
            </body>
            </html>
            """
        
        @app.get("/api/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "mode": "development" if self.debug else "production"
            }
        
        @app.get("/api/test")
        async def test():
            """Test API endpoint."""
            return {
                "message": "API is working",
                "timestamp": time.time(),
                "server": f"{self.host}:{self.port}",
                "debug": self.debug,
                "environment": "development" if self.debug else "production"
            }
        
        # Mount static files if directory exists
        static_dir = Path("static")
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory="static"), name="static")
        
        return app
    
    def start_server(self):
        """Start FastAPI server in background thread."""
        log_level = "debug" if self.debug else "info"
        
        def run():
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level=log_level
            )
        
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        time.sleep(1)  # Give server time to start
        
        mode = "debug" if self.debug else "production"
        print(f"FastAPI server started on http://{self.host}:{self.port} ({mode} mode)")
    
    def reload_browser(self):
        """Reload the browser window."""
        if self.window:
            self.window.evaluate_js("location.reload()")
            if self.debug:
                print("Browser reloaded")
    
    def setup_file_watcher(self):
        """Setup file watcher for hot-reload in development."""
        if not self.hot_reload:
            return
        
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            print("Warning: watchdog not installed, hot-reload disabled")
            return
        
        class ReloadHandler(FileSystemEventHandler):
            """Handle file changes for hot-reload."""
            
            def __init__(self, callback):
                self.callback = callback
                self.last_reload = time.time()
            
            def on_modified(self, event):
                if event.src_path.endswith(('.py', '.html', '.css', '.js')):
                    # Debounce rapid changes
                    current_time = time.time()
                    if current_time - self.last_reload > 1:
                        self.last_reload = current_time
                        if self.callback:
                            print(f"File changed: {event.src_path}")
                            self.callback()
        
        self.observer = Observer()
        handler = ReloadHandler(self.reload_browser)
        
        # Watch current directory and subdirectories
        watch_path = Path.cwd()
        self.observer.schedule(handler, str(watch_path), recursive=True)
        self.observer.start()
        print(f"Watching {watch_path} for changes...")
    
    def run(self):
        """Run the server with PyWebView."""
        # Start FastAPI server
        self.start_server()
        
        # Create PyWebView window
        window_title = f"{self.app_title} {'[DEBUG]' if self.debug else ''}"
        self.window = webview.create_window(
            title=window_title,
            url=f'http://{self.host}:{self.port}',
            width=1200,
            height=800,
            resizable=True,
            background_color='#1e1e1e',
        )
        
        # Setup file watcher if hot reload is enabled
        if self.hot_reload:
            self.setup_file_watcher()
        
        # Start PyWebView
        mode_text = "debug" if self.debug else "production"
        print(f"Starting PyWebView in {mode_text} mode...")
        webview.start(debug=self.debug)
        
        # Cleanup
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()


def main():
    """Main entry point."""
    server = MTServer()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nShutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()