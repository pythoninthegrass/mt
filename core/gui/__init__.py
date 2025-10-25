"""GUI components for the MT music player.

This module provides all GUI-related classes and components organized by responsibility:
- player_controls: Playback and utility control buttons
- progress_status: Progress bar and status bar display
- library_search: Library tree view and search bar
- queue_view: Queue/library content display with context menu
- music_player: Main player window coordinator

All classes are re-exported at the package level for backwards compatibility.
"""

from core.gui.library_search import LibraryView, SearchBar
from core.gui.music_player import MusicPlayer
from core.gui.player_controls import PlayerControls
from core.gui.progress_status import ProgressBar, StatusBar
from core.gui.queue_view import QueueView

__all__ = [
    'LibraryView',
    'MusicPlayer',
    'PlayerControls',
    'ProgressBar',
    'QueueView',
    'SearchBar',
    'StatusBar',
]
