#!/usr/bin/env python

import os
import tkinter as tk
import ttkbootstrap as ttk
from core.player import MusicPlayer
from core.theme import setup_theme
from tkinterdnd2 import TkinterDnD


def main():
    try:
        # Create custom theme style
        root = TkinterDnD.Tk()

        # Set application icon
        icon = tk.PhotoImage(file='mt.png')
        root.wm_iconphoto(False, icon)

        # Setup theme and styles
        setup_theme(root)

        global player_instance
        player_instance = MusicPlayer(root)
        player_instance.setup_components()
        root.mainloop()
    except Exception as e:
        print(f"Error in main: {e}")
        if 'root' in locals():
            root.destroy()
        exit(1)


if __name__ == "__main__":
    player_instance = None
    main()
