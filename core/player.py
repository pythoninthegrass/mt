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
    setup_theme,
)
from core.library import LibraryManager
from core.queue import QueueManager
from pathlib import Path
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from utils.files import find_audio_files, normalize_path
from utils.reload import ConfigFileHandler
from watchdog.observers import Observer


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

        # Setup views with callbacks
        self.setup_views()

        # Initialize player core first
        self.player_core = PlayerCore(self.db, self.queue_manager, self.queue_view.queue)

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
        }, initial_loop_enabled=self.player_core.loop_enabled)

        # Connect progress bar to player core
        self.player_core.progress_bar = self.progress_bar

        # Start progress update
        self.update_progress()

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

    def load_queue(self):
        """Load and display queue items."""
        rows = self.queue_manager.get_queue_items()
        if not rows:
            return

        self._populate_queue_view(rows)

    def _populate_queue_view(self, rows):
        """Populate queue view with rows of data."""
        for filepath, artist, title, album, track_number, date in rows:
            if os.path.exists(filepath):
                track_display = self._format_track_number(track_number)
                # Use filename as fallback, but if that's empty too, use "Unknown Title"
                title = title or os.path.basename(filepath) or 'Unknown Title'
                artist = artist or 'Unknown Artist'
                year = self._extract_year(date)

                self.queue_view.queue.insert(
                    '',
                    'end',
                    values=(track_display, title, artist, album or '', year),
                )

        # Select first item if any were added
        if self.queue_view.queue.get_children():
            first_item = self.queue_view.queue.get_children()[0]
            self.queue_view.queue.selection_set(first_item)
            self.queue_view.queue.see(first_item)

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
        for i, item in enumerate(self.queue_view.queue.get_children()):
            bg_color = COLORS['alternate_row_colors'][i % 2]
            self.queue_view.queue.tag_configure(f'row_{i}', background=bg_color)
            self.queue_view.queue.item(item, tags=(f'row_{i}',))

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
        """Handle start of progress bar drag."""
        self.progress_bar.dragging = True
        self.player_core.was_playing = self.player_core.is_playing
        if self.player_core.is_playing:
            self.player_core.media_player.pause()
            self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['play'])
            self.player_core.is_playing = False

    def drag(self, event):
        """Handle progress bar drag."""
        if self.progress_bar.dragging:
            x = min(
                max(event.x, self.progress_bar.controls_width),
                self.progress_bar.canvas.winfo_width() - 160
            )
            self._update_progress_position(x)

    def end_drag(self, event):
        """Handle end of progress bar drag."""
        if self.progress_bar.dragging:
            self.progress_bar.dragging = False
            if self.player_core.media_player.get_length() > 0:
                self.player_core.seek(self.player_core.current_time / self.player_core.get_duration())
                if self.player_core.was_playing:
                    self.player_core.media_player.play()
                    self.progress_bar.controls.play_button.configure(text=BUTTON_SYMBOLS['pause'])
                    self.player_core.is_playing = True

    def click_progress(self, event):
        """Handle progress bar click."""
        if event.x < self.progress_bar.controls_width or event.x > self.progress_bar.canvas.winfo_width() - 10:
            return
        self._update_progress_position(event.x)
        self.player_core.seek(self.player_core.current_time / self.player_core.get_duration())

    def _update_progress_position(self, x):
        """Update progress bar position based on x coordinate."""
        width = self.progress_bar.canvas.winfo_width() - self.progress_bar.controls_width - 160
        ratio = (x - self.progress_bar.controls_width) / width
        if self.player_core.media_player.get_length() > 0:
            self.player_core.current_time = int(self.player_core.media_player.get_length() * ratio)
            self.progress_bar.last_drag_time = time.time()
            self.progress_bar.canvas.coords(
                self.progress_bar.progress_circle,
                x - self.progress_bar.circle_radius,
                self.progress_bar.bar_y - self.progress_bar.circle_radius,
                x + self.progress_bar.circle_radius,
                self.progress_bar.bar_y + self.progress_bar.circle_radius,
            )

    def on_resize(self, event):
        """Handle window resize."""
        self.progress_bar.canvas.coords(
            self.progress_bar.line,
            self.progress_bar.controls_width,
            self.progress_bar.bar_y,
            event.width - 160,
            self.progress_bar.bar_y,
        )
        self.progress_bar.canvas.coords(
            self.progress_bar.time_text,
            event.width - 160,
            15,
        )

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()

        if hasattr(self, 'db'):
            self.db.close()
