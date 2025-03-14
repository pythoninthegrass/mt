#!/usr/bin/env python

import flet as ft
import traceback
from config import (
    APP_NAME,
    THEME_CONFIG,
    VERSION,
    WINDOW_SIZE,
)
from core.ui.app import MusicApp
from utils.common import format_time


def app_page(page: ft.Page):
    """Set up the application page and handle window events.

    Args:
        page: The Flet page object to configure.
    """
    # Set initial window properties
    page.title = APP_NAME
    page.theme_mode = "dark" if THEME_CONFIG.get('type') == 'dark' else "light"
    page.padding = 0
    page.spacing = 0
    page.window.width = WINDOW_SIZE["width"]
    page.window.height = WINDOW_SIZE["height"]
    page.window.min_width = WINDOW_SIZE["min_width"]
    page.window.min_height = WINDOW_SIZE["min_height"]
    page.update()

    # Create app instance after initial window setup
    app = MusicApp(page)

    # Add window event handler to properly clean up resources
    def on_window_event(e):
        try:
            if e.data == "close":
                print("Window close event received")

                # Set shutdown flag immediately
                if hasattr(app, '_is_shutting_down'):
                    app._is_shutting_down = True

                # Use the dedicated cleanup method to ensure all resources are released
                if hasattr(app, 'cleanup'):
                    app.cleanup()
                else:
                    print("Warning: app has no cleanup method")
                    # Fallback cleanup
                    try:
                        if app.player and app.player.player_core:
                            app.player.player_core.stop()
                            app.player.player_core.media_player.release()
                            app.player.player_core.player.release()
                        if app.player and hasattr(app.player, 'db'):
                            app.player.db.close()
                    except Exception as err:
                        print(f"Error in fallback cleanup: {err}")
            # Also handle resize events
            elif e.data == "resize" and hasattr(app, 'page') and hasattr(app.page, 'on_resize'):
                try:
                    # Call on_resize directly
                    app.page.on_resize(e)
                except Exception as ex:
                    print(f"Error handling window resize: {ex}")
        except Exception as e:
            print(f"Error in window event handler: {e}")
            traceback.print_exc()

    # Register window event handler
    page.on_window_event = on_window_event


def main():
    """Run the application."""
    try:
        ft.app(target=app_page)
    except Exception as e:
        print(f"Error in main: {e}")
        exit(1)


if __name__ == "__main__":
    main()
