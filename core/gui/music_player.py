import tkinter as tk
from core.controls import PlayerCore

class MusicPlayer:
    def __init__(self, window: tk.Tk, theme_manager):
        self.window = window
        self.theme_manager = theme_manager
        self.setup_components()

    def setup_components(self):
        # Create player core first
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks


