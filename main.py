#!/usr/bin/env python

import flet as ft
import os
import traceback
from config import (
    APP_NAME,
    THEME_CONFIG,
    VERSION,
    WINDOW_SIZE,
)
from core.db import MusicDatabase
from core.ui.app import MusicApp
from typing import Optional
from utils.common import format_time

_db_instance = None


def get_db_instance() -> MusicDatabase | None:
    global _db_instance
    return _db_instance


def set_db_instance(db: MusicDatabase) -> None:
    global _db_instance
    _db_instance = db


def safe_path_join(*args) -> str:
    return os.path.join(*args)


def main(page: ft.Page):
    """Main application entry point that receives the page object directly."""
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
        finally:
            # Ensure window is destroyed even if an exception occurs during cleanup
            if e.data == "close":
                page.window.destroy()

    # Register window event handler
    page.on_window_event = on_window_event


if __name__ == "__main__":
    try:
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            assets_dir="assets" if os.path.exists("assets") else None,
        )
    except Exception as e:
        print(f"Error in main: {e}")
        exit(1)
