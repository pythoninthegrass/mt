import importlib
import json
import mutagen
import os
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
import ttkbootstrap as ttk
import vlc
from config import (
    AUDIO_EXTENSIONS,
    BUTTON_STYLE,
    COLORS,
    DB_NAME,
    DEFAULT_LOOP_ENABLED,
    LISTBOX_CONFIG,
    MAX_SCAN_DEPTH,
    PROGRESS_BAR,
    PROGRESS_UPDATE_INTERVAL,
    RELOAD,
    THEME_CONFIG,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from contextlib import suppress
from core.controls import PlayerCore
from core.db import DB_TABLES, MusicDatabase
from core.gui import (
    BUTTON_SYMBOLS,
    LibraryView,
    PlayerControls,
    ProgressBar,
    QueueView,
)
from core.library import LibraryManager
from core.queue import QueueManager
from core.theme import setup_theme
from pathlib import Path
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from utils.files import find_audio_files, normalize_path
from utils.reload import ConfigFileHandler
from watchdog.observers import Observer

# Import AppKit for media key support on macOS
if sys.platform == 'darwin':
    try:
        import Quartz
        from utils.mediakeys import MediaKeyController
        MEDIA_KEY_SUPPORT = True
    except ImportError:
        MEDIA_KEY_SUPPORT = False
else:
    MEDIA_KEY_SUPPORT = False

class MusicPlayer:
    def __init__(self, window):
        self.window = window
        self.window.title(WINDOW_TITLE)
        self.window.geometry(WINDOW_SIZE)
        self.window.minsize(1280, 720)

        # Setup theme and styles first
        setup_theme(self.window)

        # Configure macOS specific appearance
        if sys.platform == 'darwin':
            # Set document style with dark appearance
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.window._w, 'document')
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'appearance', self.window._w, 'dark')
            self.window.createcommand('tk::mac::Quit', self.window.destroy)

        self.reload_enabled = RELOAD

        # Initialize file watcher if enabled
        self.setup_file_watcher()

        # Setup media key support
        if sys.platform == 'darwin' and MEDIA_KEY_SUPPORT:
            self.media_key_controller = MediaKeyController(self.window)

    def setup_components(self):
        """Initialize and setup all components."""
        # Initialize database and managers
        self.db = MusicDatabase(DB_NAME, DB_TABLES)
        self.queue_manager = QueueManager(self.db)
        self.library_manager = LibraryManager(self.db)

        # Create main container
        self.main_container = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        self.main_container.pack(expand=True, fill=tk.BOTH)

        # Create left panel (Library/Playlists)
        self.left_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.left_panel, weight=1)

        # Create right panel (Content)
        self.right_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.right_panel, weight=3)

        # Setup views with callbacks first
        self.setup_views()

        # Initialize player core after views are set up
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view.queue)
        self.player_core.window = self.window  # Set window reference for thread-safe callbacks

        # Create frame for progress bar
        self.progress_frame = ttk.Frame(self.window, height=80)
        self.progress_frame.pack(
            side=tk.BOTTOM,
            fill=tk.X,
            padx=10,
            pady=(0, 20),
        )

        # Setup progress bar with callbacks
        self.progress_bar = ProgressBar(self.window, self.progress_frame, {
            'previous': self.player_core.previous_song,
            'play': self.play_pause,
            'next': self.player_core.next_song,
            'loop': self.player_core.toggle_loop,
            'add': self.add_files_to_library,
            'start_drag': self.start_drag,
            'drag': self.drag,
            'end_drag': self.end_drag,
            'click_progress': self.click_progress,
            'on_resize': self.on_resize,
            'volume_change': self.volume_change,
        }, initial_loop_enabled=self.player_core.loop_enabled)

        # Connect progress bar to player core
        self.player_core.progress_bar = self.progress_bar

        # Start progress update
        self.update_progress()

        # Initialize the volume after a delay to ensure VLC is ready
        self.window.after(1000, lambda: self.player_core.set_volume(80))

        # If media key controller exists, set this instance as the player
        if hasattr(self, 'media_key_controller'):
            self.media_key_controller.set_player(self)

    def setup_views(self):
        """Setup library and queue views with their callbacks."""
        # Setup library view
        self.library_view = LibraryView(self.left_panel, {
            'on_section_select': self.on_section_select,
        })

        # Setup queue view
        self.queue_view = QueueView(self.right_panel, {
            'play_selected': self.play_selected,
            'handle_delete': self.handle_delete,
            'on_song_select': self.on_song_select,
            'handle_drop': self.handle_drop,
        })

    def setup_file_watcher(self):
        """Setup file watcher for development mode."""
        if self.reload_enabled:
            print("Development mode: watching for file changes...")
            self.observer = Observer()
            event_handler = ConfigFileHandler(self)
            self.observer.schedule(event_handler, path='.', recursive=False)
            self.observer.start()
        else:
            self.observer = None

    def play_pause(self):
        """Handle play/pause button click."""
        self.player_core.play_pause()
        self.progress_bar.controls.play_button.configure(
            text=BUTTON_SYMBOLS['pause'] if self.player_core.is_playing else BUTTON_SYMBOLS['play']
        )

    def on_section_select(self, event):
        """Handle library section selection."""
        selected_item = self.library_view.library_tree.selection()[0]
        tags = self.library_view.library_tree.item(selected_item)['tags']

        if not tags:
            return

        tag = tags[0]
        # Clear current view
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)

        if tag == 'music':
            self.load_library()
        elif tag == 'now_playing':
            self.load_queue()

    def load_library(self):
        """Load and display library items."""
        # Clear current view
        for item in self.queue_view.queue.get_children():
            self.queue_view.queue.delete(item)

        rows = self.library_manager.get_library_items()
        if not rows:
            return

        self._populate_queue_view(rows)
        self.refresh_colors()

    def load_queue(self):
        """Load and display queue items."""
        rows = self.queue_manager.get_queue_items()
        if not rows:
            return

        self._populate_queue_view(rows)
        self.refresh_colors()

    def _populate_queue_view(self, rows):
        """Populate queue view with rows of data."""
        for i, (filepath, artist, title, album, track_number, date) in enumerate(rows):
            if os.path.exists(filepath):
                track_display = self._format_track_number(track_number)
                # Use filename as fallback, but if that's empty too, use "Unknown Title"
                title = title or os.path.basename(filepath) or 'Unknown Title'
                artist = artist or 'Unknown Artist'
                year = self._extract_year(date)

                # Apply alternating row tags
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'

                item_id = self.queue_view.queue.insert(
                    '',
                    'end',
                    values=(track_display, title, artist, album or '', year),
                    tags=(row_tag,)
                )

        # Select first item if any were added
        if self.queue_view.queue.get_children():
            first_item = self.queue_view.queue.get_children()[0]
            self.queue_view.queue.selection_set(first_item)
            self.queue_view.queue.see(first_item)

        # Apply playing track highlight if needed
        self.refresh_colors()

    def _format_track_number(self, track_number):
        """Format track number for display."""
        if not track_number:
            return ''
        try:
            track_num = track_number.split('/')[0]
            return f"{int(track_num):02d}"
        except (ValueError, IndexError):
            return ''

    def _extract_year(self, date):
        """Extract year from date string."""
        if not date:
            return ''
        try:
            return date.split('-')[0] if '-' in date else date[:4]
        except Exception:
            return ''

    def add_files_to_library(self):
        """Open file dialog and add selected files to library."""
        home_dir = Path.home()
        music_dir = home_dir / 'Music'
        start_dir = str(music_dir if music_dir.exists() else home_dir)

        if sys.platform == 'darwin':
            try:
                # Try to import AppKit for native macOS file dialog
                from AppKit import NSURL, NSApplication, NSModalResponseOK, NSOpenPanel

                # Create and configure the open panel
                panel = NSOpenPanel.alloc().init()
                panel.setCanChooseFiles_(True)
                panel.setCanChooseDirectories_(True)
                panel.setAllowsMultipleSelection_(True)
                panel.setTitle_("Select Audio Files and Folders")
                panel.setMessage_("Select audio files and/or folders to add to your library")
                panel.setDirectoryURL_(NSURL.fileURLWithPath_(start_dir))

                # Run the panel
                if panel.runModal() == NSModalResponseOK:
                    # Get selected paths
                    paths = [str(url.path()) for url in panel.URLs()]
                    if paths:
                        selected_paths = []
                        for path in paths:
                            path_obj = Path(path)
                            if path_obj.is_dir():
                                mixed_paths = find_audio_files(path_obj)
                                if mixed_paths:
                                    selected_paths.extend([Path(p) for p in mixed_paths])
                            else:
                                selected_paths.append(path_obj)
                        if selected_paths:
                            self.library_manager.add_files_to_library(selected_paths)
                            # Refresh view if needed
                            selected_item = self.library_view.library_tree.selection()
                            if selected_item:
                                tags = self.library_view.library_tree.item(selected_item[0])['tags']
                                if tags and tags[0] == 'music':
                                    self.load_library()
                return
            except ImportError:
                pass  # Fall back to tkinter dialog if AppKit is not available

        # Configure file types for standard dialog
        file_types = []
        for ext in sorted(AUDIO_EXTENSIONS):
            ext = ext.lstrip('.')
            file_types.extend([f'*.{ext}', f'*.{ext.upper()}'])

        # Use standard file dialog as fallback
        paths = filedialog.askopenfilenames(
            title="Select Audio Files",
            initialdir=start_dir,
            filetypes=[("Audio Files", ' '.join(file_types))]
        )

        if paths:
            selected_paths = [Path(p) for p in paths]
            if selected_paths:
                self.library_manager.add_files_to_library(selected_paths)
                # Refresh view if needed
                selected_item = self.library_view.library_tree.selection()
                if selected_item:
                    tags = self.library_view.library_tree.item(selected_item[0])['tags']
                    if tags and tags[0] == 'music':
                        self.load_library()

    def handle_drop(self, event):
        """Handle drag and drop of files."""
        # On macOS, paths are separated by spaces and wrapped in curly braces
        # Example: "{/path/to/first file.mp3} {/path/to/second file.mp3}"
        raw_data = event.data.strip()
        paths = []

        # Extract paths between curly braces
        current = 0
        while current < len(raw_data):
            if raw_data[current] == '{':
                end = raw_data.find('}', current)
                if end != -1:
                    # Extract path without braces and handle quotes
                    path = raw_data[current + 1:end].strip().strip('"')
                    if path:  # Only add non-empty paths
                        paths.append(path)
                    current = end + 1
                else:
                    break
            else:
                current += 1

        if not paths:  # Fallback for non-macOS or different format
            paths = [p.strip('{}').strip('"') for p in event.data.split() if p.strip()]

        print("Parsed paths:", paths)  # Debug output

        # Get current view to determine where to add files
        selected_item = self.library_view.library_tree.selection()
        if selected_item:
            tags = self.library_view.library_tree.item(selected_item[0])['tags']
            if tags:
                if tags[0] == 'music':
                    self.library_manager.add_files_to_library(paths)
                    self.load_library()
                elif tags[0] == 'now_playing':
                    self.library_manager.add_files_to_library(paths)
                    self.queue_manager.process_dropped_files(paths)
                    self.load_queue()

    def play_selected(self, event=None):
        """Play the selected track."""
        selected_items = self.queue_view.queue.selection()
        if not selected_items:
            return "break"

        item_values = self.queue_view.queue.item(selected_items[0])['values']
        if not item_values:
            return "break"

        track_num, title, artist, album, year = item_values
        filepath = self.library_manager.find_file_by_metadata(title, artist, album, track_num)

        if filepath and os.path.exists(filepath):
            self.player_core._play_file(filepath)
            self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['pause'])
            # Refresh colors to highlight the playing track
            self.refresh_colors()

        return "break"

    def handle_delete(self, event):
        """Handle delete key press."""
        selected_items = self.queue_view.queue.selection()
        if not selected_items:
            return

        for item in selected_items:
            values = self.queue_view.queue.item(item)['values']
            if values:
                track_num, title, artist, album, year = values
                self.queue_manager.remove_from_queue(title, artist, album, track_num)
                self.queue_view.queue.delete(item)

        self.refresh_colors()
        return "break"

    def on_song_select(self, event):
        """Handle song selection in queue view."""
        # This method can be used to update UI or track the currently selected song
        pass

    def refresh_colors(self):
        """Update the background colors of all items in the queue view."""
        # Get the currently playing filepath if available
        current_filepath = None
        if hasattr(self, 'player_core') and self.player_core.is_playing:
            # Get the currently playing file path from the media player
            media = self.player_core.media_player.get_media()
            if media:
                current_filepath = media.get_mrl()
                # Convert file:// URL to normal path
                if current_filepath.startswith('file://'):
                    current_filepath = current_filepath[7:]
                # On macOS, decode URL characters
                import urllib.parse
                current_filepath = urllib.parse.unquote(current_filepath)
                print(f"Current playing filepath: {current_filepath}")  # Debug log

        # Configure all the tag styles before applying them
        # Define playing tag - strong teal highlight
        playing_bg = THEME_CONFIG['colors'].get('playing_bg', '#00343a')
        playing_fg = THEME_CONFIG['colors'].get('playing_fg', '#33eeff')
        print(f"Playing colors - bg: {playing_bg}, fg: {playing_fg}")  # Debug log

        # Configure the tag style for the playing track
        self.queue_view.queue.tag_configure(
            'playing',
            background=playing_bg,
            foreground=playing_fg
        )

        # Configure even/odd row tag styles
        self.queue_view.queue.tag_configure('evenrow', background=THEME_CONFIG['colors']['bg'])
        self.queue_view.queue.tag_configure('oddrow', background=THEME_CONFIG['colors'].get('row_alt', '#242424'))

        # Process each row in the queue view
        playing_item_found = False
        for i, item in enumerate(self.queue_view.queue.get_children()):
            values = self.queue_view.queue.item(item, 'values')
            if not values or len(values) < 3:  # Need at least track, title, artist
                continue

            # If we have a current filepath, check if this item corresponds to it
            is_current = False
            if current_filepath:
                track_num, title, artist, album, year = values
                # Find the filepath for this metadata
                item_filepath = self.library_manager.find_file_by_metadata(title, artist, album, track_num)
                # Check if it matches the currently playing file
                if item_filepath and os.path.normpath(item_filepath) == os.path.normpath(current_filepath):
                    is_current = True
                    playing_item_found = True
                    print(f"Found playing item: {title} by {artist}")  # Debug log

            if is_current:
                # This is the currently playing track - highlight with teal
                self.queue_view.queue.item(item, tags=('playing',))
            else:
                # Determine if this is an even or odd row for alternating colors
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.queue_view.queue.item(item, tags=(row_tag,))

        if not playing_item_found and current_filepath:
            print(f"Warning: Could not find item matching filepath: {current_filepath}")  # Debug log

    def update_progress(self):
        """Update progress bar position and time display."""
        if (self.player_core.is_playing and
            self.player_core.media_player.is_playing() and
            not self.progress_bar.dragging and
            (time.time() - self.progress_bar.last_drag_time) > 0.1):

            current = self.player_core.get_current_time()
            duration = self.player_core.get_duration()

            if duration > 0:
                ratio = current / duration
                width = self.progress_bar.canvas.winfo_width()
                x = self.progress_bar.controls_width + (width - self.progress_bar.controls_width - 160) * ratio

                # Update circle position
                self.progress_bar.canvas.coords(
                    self.progress_bar.progress_circle,
                    x - self.progress_bar.circle_radius,
                    self.progress_bar.bar_y - self.progress_bar.circle_radius,
                    x + self.progress_bar.circle_radius,
                    self.progress_bar.bar_y + self.progress_bar.circle_radius,
                )

                # Update progress line coordinates (from start to current position)
                self.progress_bar.canvas.coords(
                    self.progress_bar.progress_line,
                    self.progress_bar.controls_width,
                    self.progress_bar.bar_y,
                    x,
                    self.progress_bar.bar_y,
                )

                # Update time display
                current_time = self._format_time(current / 1000)
                total_time = self._format_time(duration / 1000)
                self.progress_bar.canvas.itemconfig(
                    self.progress_bar.time_text,
                    text=f"{current_time} / {total_time}"
                )

        self.window.after(100, self.update_progress)

    def _format_time(self, seconds):
        """Format time in seconds to MM:SS format."""
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def start_drag(self, event):
        """Start dragging the progress circle."""
        self.progress_bar.dragging = True
        self.progress_bar.last_drag_time = time.time()
        self.player_core.was_playing = self.player_core.is_playing
        if self.player_core.is_playing:
            self.player_core.media_player.pause()
            self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['play'])
            self.player_core.is_playing = False

    def drag(self, event):
        """Handle progress circle drag."""
        if self.progress_bar.dragging:
            controls_width = self.progress_bar.controls_width
            max_width = self.progress_bar.canvas.winfo_width() - 160

            # Constrain x to valid range
            x = max(controls_width, min(event.x, max_width))

            # Update circle position
            circle_radius = self.progress_bar.circle_radius
            bar_y = self.progress_bar.bar_y
            self.progress_bar.canvas.coords(
                self.progress_bar.progress_circle,
                x - circle_radius,
                bar_y - circle_radius,
                x + circle_radius,
                bar_y + circle_radius
            )

            # Update progress line position
            self.progress_bar.canvas.coords(
                self.progress_bar.progress_line,
                controls_width,
                bar_y,
                x,
                bar_y
            )

    def end_drag(self, event):
        """End dragging the progress circle and seek to the position."""
        if self.progress_bar.dragging:
            self.progress_bar.dragging = False

            # Calculate seek ratio
            width = self.progress_bar.canvas.winfo_width() - self.progress_bar.controls_width - 160
            x = min(max(event.x, self.progress_bar.controls_width), self.progress_bar.canvas.winfo_width() - 160)
            ratio = (x - self.progress_bar.controls_width) / width

            # Seek to position
            self.player_core.seek(ratio)

            # Resume playback if it was playing before
            if self.player_core.was_playing:
                self.player_core.media_player.play()
                self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['pause'])
                self.player_core.is_playing = True

    def click_progress(self, event):
        """Handle click on progress bar."""
        # Check if click was near the progress bar and not on a button
        if abs(event.y - self.progress_bar.bar_y) < 10 and not self.progress_bar.dragging:
            self._update_progress_position(event.x)
            # Set position in player
            self._seek_to_position(event.x)

    def _update_progress_position(self, x):
        """Update the position of the progress circle and line."""
        controls_width = self.progress_bar.controls_width
        max_x = self.progress_bar.canvas.winfo_width() - 160

        # Constrain x to valid range
        x = max(controls_width, min(x, max_x))

        # Update circle position
        circle_radius = self.progress_bar.circle_radius
        bar_y = self.progress_bar.bar_y
        self.progress_bar.canvas.coords(
            self.progress_bar.progress_circle,
            x - circle_radius,
            bar_y - circle_radius,
            x + circle_radius,
            bar_y + circle_radius
        )

        # Update progress line position
        self.progress_bar.canvas.coords(
            self.progress_bar.progress_line,
            controls_width,
            bar_y,
            x,
            bar_y
        )

    def _seek_to_position(self, x):
        """Seek to a position in the track based on x coordinate."""
        controls_width = self.progress_bar.controls_width
        width = self.progress_bar.canvas.winfo_width() - controls_width - 160

        # Calculate ratio of position
        ratio = (x - controls_width) / width
        ratio = max(0, min(ratio, 1))  # Constrain to 0-1

        # Update player position
        if self.player_core.media_player.get_length() > 0:
            self.player_core.current_time = int(self.player_core.media_player.get_length() * ratio)
            self.progress_bar.last_drag_time = time.time()
            self.player_core.seek(ratio)

    def on_resize(self, event):
        """Handle window resize."""
        # Calculate positions
        controls_width = self.progress_bar.controls_width
        right_margin = PROGRESS_BAR['right_margin']
        volume_width = self.progress_bar.volume_control_width

        # Calculate where progress line should end (before volume control)
        volume_start_x = event.width - right_margin - volume_width

        # Update line coordinates (end BEFORE volume control)
        self.progress_bar.canvas.coords(
            self.progress_bar.line,
            controls_width,
            self.progress_bar.bar_y,
            volume_start_x - 10,  # Add a small gap before volume control
            self.progress_bar.bar_y,
        )

        # Update time display position
        self.progress_bar.canvas.coords(
            self.progress_bar.time_text,
            event.width - (right_margin / 2),  # Center in right margin
            PROGRESS_BAR['time_label_y'],
        )

        # Reposition volume control
        self.progress_bar.canvas.coords(
            self.progress_bar.volume_window,
            volume_start_x + (volume_width / 2),  # Center the volume control
            self.progress_bar.bar_y,
        )

        # Update progress line if it exists and we're playing
        if hasattr(self.progress_bar, 'progress_line') and self.player_core.is_playing:
            # Ensure progress line doesn't extend beyond where volume control starts
            current_coords = self.progress_bar.canvas.coords(self.progress_bar.progress_line)
            if current_coords and len(current_coords) == 4:
                # Calculate the max x-position where progress line can go
                max_x = volume_start_x - 10

                # Keep progress line within bounds
                if current_coords[2] > max_x:
                    current_coords[2] = max_x

                self.progress_bar.canvas.coords(
                    self.progress_bar.progress_line,
                    current_coords[0],
                    current_coords[1],
                    current_coords[2],
                    current_coords[3]
                )

    def volume_change(self, volume):
        """Handle volume slider changes."""
        print(f"MusicPlayer: Setting volume to {volume}")  # Debug log
        if hasattr(self, 'player_core') and self.player_core:
            try:
                result = self.player_core.set_volume(int(volume))
                print(f"Volume change result: {result}")  # Debug result
            except Exception as e:
                print(f"Error setting volume: {e}")

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()

        if hasattr(self, 'db'):
            self.db.close()
