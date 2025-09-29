#!/usr/bin/env python

import customtkinter as ctk
import eliot
import os
import tkinter as tk
from core.logging import app_logger, log_error, setup_logging
from core.player import MusicPlayer
from core.theme import setup_theme
from eliot import log_message, start_action, write_traceback
from tkinter import ttk
from tkinterdnd2 import TkinterDnD


def main():
    with start_action(app_logger, "application_startup"):
        try:
            log_message(message_type="application_init", message="Starting mt music player")

            # Set CustomTkinter appearance mode and theme
            ctk.set_appearance_mode("dark")  # "dark" or "light"
            ctk.set_default_color_theme("blue")  # "blue", "dark-blue", "green"

            # Create custom theme style with CustomTkinter
            root = TkinterDnD.Tk()
            log_message(message_type="ui_init", component="main_window", message="Created main CustomTkinter window")

            # Set application icon
            icon = tk.PhotoImage(file='mt.png')
            root.wm_iconphoto(False, icon)
            log_message(message_type="ui_init", component="icon", message="Set application icon")

            # Setup theme and styles
            setup_theme(root)
            log_message(message_type="ui_init", component="theme", message="Theme setup completed")

            global player_instance
            player_instance = MusicPlayer(root)
            log_message(message_type="player_init", message="MusicPlayer instance created")

            player_instance.setup_components()
            log_message(message_type="player_init", message="Player components setup completed")

            log_message(message_type="application_ready", message="Application startup completed, entering main loop")

            root.mainloop()

        except Exception as e:
            write_traceback()
            log_message(
                message_type="error_occurred",
                error_message=str(e),
                error_type=type(e).__name__,
                context="application_startup",
            )
            print(f"Error in main: {e}")
            if 'root' in locals():
                root.destroy()
            exit(1)


if __name__ == "__main__":
    main()
