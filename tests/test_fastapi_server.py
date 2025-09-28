#!/usr/bin/env python3
"""FastAPI server setup for PyWebView integration."""

import threading
import time
import uvicorn
from contextlib import asynccontextmanager
from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Global server instance
server = None
server_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI app lifecycle."""
    print("FastAPI server starting up...")
    yield
    print("FastAPI server shutting down...")


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint serving HTML."""
    return """
    <html>
    <head>
        <title>FastAPI + PyWebView</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
            h1 { margin: 0 0 1rem 0; font-size: 2.5rem; }
            p { margin: 0.5rem 0; font-size: 1.2rem; }
            .status { 
                padding: 0.5rem 1rem;
                background: rgba(34, 197, 94, 0.2);
                border: 2px solid #22c55e;
                border-radius: 5px;
                margin-top: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>FastAPI Server Running!</h1>
            <p>Successfully serving content from FastAPI</p>
            <div class="status">Server: localhost:3000</div>
        </div>
    </body>
    </html>
    """


@app.get("/api/test")
async def test_api():
    """Test API endpoint."""
    return {"message": "FastAPI is working!", "timestamp": time.time()}


def start_server(host=None, port=None):
    """Start the FastAPI server in a background thread."""
    global server, server_thread
    
    host = host or config('SERVER_HOST', default='127.0.0.1')
    port = int(port or config('SERVER_PORT', default=3000, cast=int))
    
    def run_server():
        uvicorn.run(app, host=host, port=port, log_level="info")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(1)
    print(f"FastAPI server started on http://{host}:{port}")
    return server_thread


def stop_server():
    """Stop the FastAPI server."""
    global server_thread
    if server_thread:
        # Note: Proper shutdown requires more complex handling with uvicorn
        print("Server shutdown requested")


if __name__ == "__main__":
    # Test the server standalone
    host = config('SERVER_HOST', default='127.0.0.1')
    port = config('SERVER_PORT', default=3000, cast=int)
    print(f"Starting FastAPI server standalone on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, reload=True)