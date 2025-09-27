#!/usr/bin/env python3
"""Basic PyWebView window test to verify installation."""

import webview


def main():
    """Create a basic PyWebView window to test the installation."""
    # Create a simple window with HTML content
    window = webview.create_window(
        title='PyWebView Test',
        html='''
        <html>
        <head>
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
                h1 {
                    margin: 0 0 1rem 0;
                    font-size: 2.5rem;
                }
                p {
                    margin: 0.5rem 0;
                    font-size: 1.2rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>PyWebView Test Successful!</h1>
                <p>The PyWebView environment is properly configured.</p>
                <p>Press Ctrl+C in terminal to exit.</p>
            </div>
        </body>
        </html>
        ''',
        width=800,
        height=600,
        resizable=True
    )
    
    # Start the GUI loop
    webview.start()


if __name__ == '__main__':
    main()