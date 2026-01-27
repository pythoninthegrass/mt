"""Favorites management for liked songs functionality."""

from collections.abc import Callable
from core.db import MusicDatabase
from core.logging import log_player_action


class FavoritesManager:
    """Manages favorites/liked songs functionality."""

    def __init__(self, db: MusicDatabase):
        """Initialize FavoritesManager.

        Args:
            db: Database instance for persistence
        """
        self.db = db
        self._on_favorites_changed_callback: Callable[[], None] | None = None

    def set_on_favorites_changed_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when favorites list changes.

        Args:
            callback: Function to call when favorites are added/removed
        """
        self._on_favorites_changed_callback = callback

    def toggle_favorite(self, filepath: str) -> bool:
        """Toggle favorite status for a track.

        Args:
            filepath: Path to the track file

        Returns:
            bool: True if now favorited, False if now unfavorited
        """
        import os
        from core.logging import controls_logger
        from eliot import start_action

        # Get track metadata for logging
        track_metadata = self.db.get_metadata_by_filepath(filepath) if filepath else {}
        track_title = track_metadata.get('title', os.path.basename(filepath) if filepath else 'Unknown')
        track_artist = track_metadata.get('artist', 'Unknown')
        track_display = f"{track_artist} - {track_title}"

        is_favorited = self.db.is_favorite(filepath)

        with start_action(controls_logger, "toggle_favorite_button"):
            if is_favorited:
                # Unfavorite
                success = self.db.remove_favorite(filepath)
                if success:
                    log_player_action(
                        "favorite_button_pressed",
                        trigger_source="gui",
                        filepath=filepath,
                        track=track_display,
                        old_state="favorited",
                        new_state="unfavorited",
                        description=f"Removed from favorites: {track_display}",
                    )
                    self._notify_favorites_changed()
                return False
            else:
                # Favorite
                success = self.db.add_favorite(filepath)
                if success:
                    log_player_action(
                        "favorite_button_pressed",
                        trigger_source="gui",
                        filepath=filepath,
                        track=track_display,
                        old_state="unfavorited",
                        new_state="favorited",
                        description=f"Added to favorites: {track_display}",
                    )
                    self._notify_favorites_changed()
                return True

    def is_favorite(self, filepath: str) -> bool:
        """Check if a track is favorited.

        Args:
            filepath: Path to the track file

        Returns:
            bool: True if track is favorited
        """
        return self.db.is_favorite(filepath)

    def get_liked_songs(self) -> list[tuple]:
        """Get all favorited tracks ordered by favorite timestamp (FIFO).

        Returns:
            list[tuple]: List of (filepath, artist, title, album, track_number, date) tuples
        """
        return self.db.get_liked_songs()

    def _notify_favorites_changed(self) -> None:
        """Notify observers that the favorites list has changed."""
        if self._on_favorites_changed_callback:
            self._on_favorites_changed_callback()
