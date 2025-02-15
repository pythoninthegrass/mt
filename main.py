#!/usr/bin/env python

import importlib
import json
import os
import sqlite3
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
import ttkbootstrap as ttk
import vlc
from config import (
    AUDIO_EXTENSIONS,
    BUTTON_STYLE,
    BUTTON_SYMBOLS,
    COLORS,
    DB_NAME,
    DB_TABLES,
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
from pathlib import Path
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, app_instance):
        self.app_instance = app_instance
        self.last_reload_time = 0
        self.reload_cooldown = 1.0  # seconds
        self.watched_files = {'config.py', 'themes.json', 'main.py'}

    def on_modified(self, event):
        if not RELOAD or event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_reload_time < self.reload_cooldown:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        if file_name in self.watched_files:
            print(f"Detected change in {file_name}, reloading configuration...")
            self.last_reload_time = current_time

            try:
                if file_name == 'main.py':
                    # For main.py changes, we need to restart the entire process
                    if self.app_instance and self.app_instance.window:
                        self.app_instance.window.after(100, self.restart_process)
                else:
                    # For other files, reload config and restart window
                    if 'config' in sys.modules:
                        importlib.reload(sys.modules['config'])
                    if self.app_instance and self.app_instance.window:
                        self.app_instance.window.after(100, self.restart_application)
            except Exception as e:
                print(f"Error reloading configuration: {e}")

    def restart_process(self):
        """Restart the entire Python process"""
        try:
            if self.app_instance and self.app_instance.window:
                self.app_instance.window.destroy()
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            print(f"Error restarting process: {e}")
            sys.exit(1)

    def restart_application(self):
        """Restart just the application window"""
        try:
            if self.app_instance and self.app_instance.window:
                self.app_instance.window.destroy()
                main()
        except Exception as e:
            print(f"Error restarting application: {e}")
            sys.exit(1)


def normalize_path(path_str):
    if isinstance(path_str, Path):
        return path_str

    path_str = path_str.strip('{}').strip('"')

    if sys.platform == 'darwin' and '/Volumes/' in path_str:
        try:
            abs_path = os.path.abspath(path_str)
            real_path = os.path.realpath(abs_path)
            if os.path.exists(real_path):
                return Path(real_path)
        except (OSError, ValueError):
            pass

    return Path(path_str)


def find_audio_files(directory, max_depth=MAX_SCAN_DEPTH):
    found_files = set()
    base_path = normalize_path(directory)

    def scan_directory(path, current_depth):
        if current_depth > max_depth:
            return

        try:
            for item in path.iterdir():
                try:
                    if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS:
                        found_files.add(str(item))
                    elif item.is_dir() and not item.is_symlink():
                        scan_directory(item, current_depth + 1)
                except OSError:
                    continue
        except (PermissionError, OSError):
            pass

    scan_directory(base_path, 1)
    return sorted(found_files)


class MusicPlayer:
    def update_scrollbar(self):
        # Get the total height of all items
        total_height = self.queue.size() * self.queue.bbox(0)[3] if self.queue.size() > 0 else 0
        # Get the visible height of the listbox
        visible_height = self.queue.winfo_height()

        # Show/hide scrollbar based on content
        if total_height > visible_height:
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.scrollbar.pack_forget()

    def load_queue(self):
        self.db_cursor.execute('SELECT filepath FROM queue ORDER BY id')
        for (filepath,) in self.db_cursor.fetchall():
            if os.path.exists(filepath):  # Only add if file still exists
                self.queue.insert(tk.END, filepath)
        if self.queue.size() > 0:
            self.queue.selection_set(0)
            self.queue.activate(0)
        self.refresh_colors()
        self.update_scrollbar()

    def play_pause(self):
        if not self.is_playing:
            # If media is already loaded (paused), resume playback.
            if self.media_player.get_media() is not None:
                self.media_player.play()
            else:
                # If queue is empty, do nothing.
                if self.queue.size() == 0:
                    return
                selected_song = self.queue.get(tk.ACTIVE)
                media = self.player.media_new(selected_song)
                self.media_player.set_media(media)
                if self.current_time > 0:
                    self.media_player.play()
                    self.media_player.set_time(self.current_time)
                else:
                    self.media_player.play()
            self.play_button.configure(text=BUTTON_SYMBOLS['pause'])
            self.is_playing = True
        else:
            self.current_time = self.media_player.get_time()
            self.media_player.pause()
            self.play_button.configure(text=BUTTON_SYMBOLS['play'])
            self.is_playing = False

    def __init__(self, window):
        self.window = window
        self.window.title(WINDOW_TITLE)
        self.window.geometry(WINDOW_SIZE)
        # Force the window to open at the specified size and prevent smaller sizes
        self.window.minsize(1280, 720)
        self.is_playing = False
        self.current_time = 0

        # Initialize file watcher only if RELOAD is enabled
        if RELOAD:
            print("Development mode: watching for file changes...")
            self.observer = Observer()
            event_handler = ConfigFileHandler(self)
            self.observer.schedule(event_handler, path='.', recursive=False)
            self.observer.start()
        else:
            self.observer = None

        # Initialize database
        self.db_conn = sqlite3.connect(DB_NAME)
        self.db_cursor = self.db_conn.cursor()
        for table_name, create_sql in DB_TABLES.items():
            self.db_cursor.execute(create_sql)
        self.db_conn.commit()

        # Load loop state from settings
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'loop_enabled'")
        result = self.db_cursor.fetchone()
        if result is None:
            self.loop_enabled = DEFAULT_LOOP_ENABLED
            self.db_cursor.execute("INSERT INTO settings (key, value) VALUES ('loop_enabled', '1')")
            self.db_conn.commit()
        else:
            self.loop_enabled = (result[0] == '1')

        # Create main container
        self.main_container = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        self.main_container.pack(expand=True, fill=tk.BOTH)

        # Create left panel (Library/Playlists)
        self.left_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.left_panel, weight=1)

        # Create right panel (Content)
        self.right_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.right_panel, weight=3)

        # Setup left panel sections
        self.setup_left_panel()

        # Setup right panel (initially empty)
        self.setup_right_panel()

        # Initialize VLC player
        self.player = vlc.Instance()
        self.media_player = self.player.media_player_new()
        self.media_player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.next_song)

        # Add progress bar and controls at bottom
        self.setup_progress_bar()

    def setup_left_panel(self):
        # Create treeview for library/playlists
        self.library_tree = ttk.Treeview(self.left_panel, show='tree', selectmode='browse')
        self.library_tree.pack(expand=True, fill=tk.BOTH)

        # Library section
        library_id = self.library_tree.insert('', 'end', text='Library', open=True)
        self.library_tree.insert(library_id, 'end', text='Music', tags=('music',))
        self.library_tree.insert(library_id, 'end', text='Now Playing', tags=('now_playing',))

        # Playlists section
        playlists_id = self.library_tree.insert('', 'end', text='Playlists', open=True)
        self.library_tree.insert(playlists_id, 'end', text='Recently Added', tags=('recent_added',))
        self.library_tree.insert(playlists_id, 'end', text='Recently Played', tags=('recent_played',))
        self.library_tree.insert(playlists_id, 'end', text='Top 25 Most Played', tags=('top_played',))

        # Calculate the width needed for the longest item
        items = [
            'Library', 'Music', 'Now Playing',
            'Playlists', 'Recently Added', 'Recently Played', 'Top 25 Most Played'
        ]

        # Get the font from the Treeview style
        style = ttk.Style()
        font_str = style.lookup('Treeview', 'font')
        if not font_str:  # If no font specified in style, use default
            font_str = 'TkDefaultFont'
        font = tkfont.nametofont(font_str)

        # Calculate max width including all necessary padding
        text_width = max(font.measure(text) for text in items)
        indent_width = 10                           # Width for each level of indentation
        icon_width = 10                             # Width for tree icons
        max_indent_level = 2                        # Maximum indentation level in our tree
        side_padding = 0                            # Reduced from 80 to move divider left

        # Total width calculation
        total_width = (
            text_width +                            # Actual text width
            (indent_width * max_indent_level) +     # Indentation for nested items
            icon_width +                            # Space for tree icons
            side_padding                            # Extra padding for visual comfort
        )

        # Add extra width to match the manual position
        pane_width = total_width + 40  # Reduced from 60 to move divider left

        # Configure the left panel width and prevent it from being too small
        self.left_panel.configure(width=pane_width)
        self.left_panel.pack_propagate(False)  # Prevent the frame from shrinking

        # Force the sash (divider) position after a short delay to ensure the window is fully created
        self.window.after(100, lambda: self.main_container.sashpos(0, pane_width))

        # Bind selection event
        self.library_tree.bind('<<TreeviewSelect>>', self.on_section_select)

    def setup_right_panel(self):
        # Create queue frame and listbox (similar to original queue setup)
        self.queue_frame = ttk.Frame(self.right_panel)
        self.queue_frame.pack(expand=True, fill=tk.BOTH)

        self.scrollbar = ttk.Scrollbar(self.queue_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.queue = tk.Listbox(
            self.queue_frame,
            selectmode=LISTBOX_CONFIG['selectmode'],
            yscrollcommand=self.scrollbar.set,
            background=LISTBOX_CONFIG['background'],
            foreground=LISTBOX_CONFIG['foreground'],
            selectbackground=LISTBOX_CONFIG['selectbackground'],
            selectforeground=LISTBOX_CONFIG['selectforeground'],
            activestyle=LISTBOX_CONFIG['activestyle'],
            borderwidth=0,
            highlightthickness=0
        )
        self.queue.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.queue.yview)

        # Add queue bindings
        self.queue.bind('<Double-Button-1>', self.play_selected)
        self.queue.bind('<Delete>', self.handle_delete)
        self.queue.bind('<BackSpace>', self.handle_delete)

        # Setup drag and drop
        self.setup_drag_drop()

    def on_section_select(self, event):
        selected_item = self.library_tree.selection()[0]
        tags = self.library_tree.item(selected_item)['tags']

        if not tags:
            return

        tag = tags[0]
        self.queue.delete(0, tk.END)  # Clear current view

        if tag == 'music':
            # Load full library
            self.load_library()
        elif tag == 'now_playing':
            # Load current queue
            self.load_queue()
        elif tag in ('recent_added', 'recent_played', 'top_played'):
            # These will be implemented later
            pass

    def load_library(self):
        # Load all known music files from database
        self.db_cursor.execute('SELECT DISTINCT filepath FROM library ORDER BY filepath')
        for (filepath,) in self.db_cursor.fetchall():
            if os.path.exists(filepath):
                self.queue.insert(tk.END, filepath)
        self.refresh_colors()

    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        # Update the loop button style based on state
        style = ttk.Style()
        style.configure('Loop.Controls.TButton',
            foreground=THEME_CONFIG['colors']['primary'] if self.loop_enabled else THEME_CONFIG['colors']['fg']
        )
        self.db_cursor.execute(
            "UPDATE settings SET value = ? WHERE key = ?",
            ('1' if self.loop_enabled else '0', 'loop_enabled')
        )
        self.db_conn.commit()

    def start_drag(self, event):
        self.dragging = True
        self.was_playing = self.is_playing
        # Pause manually instead of toggling play_pause
        if self.is_playing:
            self.media_player.pause()
            self.play_button.configure(text=BUTTON_SYMBOLS['play'])
            self.is_playing = False

    def drag(self, event):
        if self.dragging:
            # Only allow dragging within the valid progress bar area
            x = min(max(event.x, self.controls_width),
                    self.canvas.winfo_width() - 160)

            # Update circle position
            self.canvas.coords(self.progress_circle,
                x - self.circle_radius, self.bar_y - self.circle_radius,
                x + self.circle_radius, self.bar_y + self.circle_radius)

            # Calculate new time based on position
            width = self.canvas.winfo_width() - self.controls_width - 160
            ratio = (x - self.controls_width) / width
            if self.media_player.get_length() > 0:
                self.current_time = int(self.media_player.get_length() * ratio)
                self.last_drag_time = time.time()

    def end_drag(self, event):
        if self.dragging:
            self.dragging = False
            if self.media_player.get_length() > 0:
                self.media_player.set_time(self.current_time)
                duration = self.media_player.get_length()
                ratio = self.current_time / duration if duration > 0 else 0
                width = self.canvas.winfo_width()
                x = self.controls_width + (width - self.controls_width - 160) * ratio
                self.canvas.coords(self.progress_circle,
                    x - self.circle_radius, self.bar_y - self.circle_radius,
                    x + self.circle_radius, self.bar_y + self.circle_radius)
                if self.was_playing:
                    self.media_player.play()
                    self.play_button.configure(text=BUTTON_SYMBOLS['pause'])
                    self.is_playing = True

    def click_progress(self, event):
        # Only process clicks within the valid progress bar area
        if event.x < self.controls_width or event.x > self.canvas.winfo_width() - 10:
            return

        # Calculate the new position
        width = self.canvas.winfo_width() - self.controls_width - 160
        ratio = (event.x - self.controls_width) / width

        if self.media_player.get_length() > 0:
            self.current_time = int(self.media_player.get_length() * ratio)
            self.media_player.set_time(self.current_time)
            # Update circle position
            self.canvas.coords(self.progress_circle,
                event.x - self.circle_radius, self.bar_y - self.circle_radius,
                event.x + self.circle_radius, self.bar_y + self.circle_radius)

    def on_resize(self, event):
        # Update progress bar line
        self.canvas.coords(self.line,
            self.controls_width, self.bar_y,
            event.width-160, self.bar_y)
        # Update time text position
        self.canvas.coords(self.time_text,
            event.width-160, PROGRESS_BAR['time_label_y'])
        # Update utility controls position
        for widget in self.canvas.find_withtag('utility_frame'):
            self.canvas.coords(widget, event.width-150, PROGRESS_BAR['controls_y']-15)

    def update_progress(self):
        if (self.is_playing and self.media_player.is_playing() and
            not self.dragging and (time.time() - self.last_drag_time) > 0.1):
            current = self.media_player.get_time()
            duration = self.media_player.get_length()

            if duration > 0:
                ratio = current / duration
                width = self.canvas.winfo_width()
                x = self.controls_width + (width - self.controls_width - 160) * ratio
                self.canvas.coords(self.progress_circle,
                    x - self.circle_radius, self.bar_y - self.circle_radius,
                    x + self.circle_radius, self.bar_y + self.circle_radius)

                # Update time display with current/total format
                def format_time(seconds):
                    seconds = int(seconds)
                    m = seconds // 60
                    s = seconds % 60
                    return f"{m:02d}:{s:02d}"

                current_time = format_time(current / 1000)
                total_time = format_time(duration / 1000)
                self.canvas.itemconfig(self.time_text, text=f"{current_time} / {total_time}")

        self.window.after(PROGRESS_UPDATE_INTERVAL, self.update_progress)

    def next_song(self, event=None):
        # For automatic next on song end and manual next
        self.next_song_button()

    def next_song_button(self, event=None):
        if self.queue.size() > 0:
            current = self.queue.curselection()
            current_index = current[0] if current else -1
            # If nothing is selected, default to first song.
            if current_index == -1:
                next_index = 0
            # If loop is disabled and on the last song, then stop playback.
            elif not self.loop_enabled and current_index == self.queue.size() - 1:
                self.media_player.stop()
                self.is_playing = False
                self.play_button.configure(text=BUTTON_SYMBOLS['play'])
                self.current_time = 0
                return
            else:
                next_index = current_index + 1 if current_index + 1 < self.queue.size() else 0
            self.queue.selection_clear(0, tk.END)
            self.queue.activate(next_index)
            self.queue.selection_set(next_index)
            self.queue.see(next_index)
            selected_song = self.queue.get(next_index)
            media = self.player.media_new(selected_song)
            self.media_player.set_media(media)
            self.media_player.play()
            self.current_time = 0
            self.is_playing = True
            self.play_button.configure(text=BUTTON_SYMBOLS['pause'])

    def previous_song(self):
        if self.queue.size() > 0:
            # Get current selection or default to 0
            current = self.queue.curselection()
            current_index = current[0] if current else 0
            prev_index = (current_index - 1) % self.queue.size()

            self.queue.selection_clear(0, tk.END)
            self.queue.activate(prev_index)
            self.queue.selection_set(prev_index)
            self.queue.see(prev_index)

            # Directly play the previous song
            selected_song = self.queue.get(prev_index)
            media = self.player.media_new(selected_song)
            self.media_player.set_media(media)
            self.media_player.play()
            self.current_time = 0
            self.is_playing = True
            self.play_button.configure(text=BUTTON_SYMBOLS['pause'])

    def process_paths(self, paths):
        existing_files = set()
        # Get existing files from library
        self.db_cursor.execute('SELECT filepath FROM library')
        for (filepath,) in self.db_cursor.fetchall():
            existing_files.add(filepath)

        new_files = set()

        for path in paths:
            if not path or path.isspace():
                continue

            normalized_path = normalize_path(path)

            try:
                if normalized_path.exists():
                    if normalized_path.is_dir():
                        new_files.update(find_audio_files(normalized_path))
                    elif normalized_path.is_file():
                        new_files.add(str(normalized_path))
            except (OSError, PermissionError):
                continue

        files_to_add = sorted(new_files - existing_files)

        if files_to_add:
            for file_path in files_to_add:
                path_obj = Path(file_path)
                if path_obj.exists():
                    # Add to library instead of queue
                    self.db_cursor.execute(
                        'INSERT INTO library (filepath) VALUES (?)',
                        (str(file_path),)
                    )

            self.db_conn.commit()

            # If we're currently viewing the Music library, update the view
            selected_item = self.library_tree.selection()
            if selected_item:
                tags = self.library_tree.item(selected_item[0])['tags']
                if tags and tags[0] == 'music':
                    self.load_library()

    def add_to_queue(self):
        # Get selected items from the current view
        selected_indices = self.queue.curselection()
        if not selected_indices:
            return

        # Get the filepaths of selected items
        selected_files = [self.queue.get(idx) for idx in selected_indices]

        # Add selected files to queue
        for filepath in selected_files:
            self.db_cursor.execute('INSERT INTO queue (filepath) VALUES (?)', (filepath,))
        self.db_conn.commit()

        # If we're viewing Now Playing, refresh the view
        selected_item = self.library_tree.selection()
        if selected_item:
            tags = self.library_tree.item(selected_item[0])['tags']
            if tags and tags[0] == 'now_playing':
                self.load_queue()

    def add_files_to_library(self):
        # Get user's home directory using pathlib
        home_dir = Path.home()

        # Let user choose between files or directory
        action = filedialog.askdirectory(
            title="Select Music Directory",
            initialdir=str(home_dir)
        )

        if action:
            path_obj = Path(action)
            if path_obj.is_dir():
                mixed_paths = find_audio_files(path_obj)
                if mixed_paths:
                    self.process_paths(mixed_paths)
                return

        # If directory selection was cancelled, show file selection dialog
        paths = filedialog.askopenfilenames(
            title="Select Audio Files",
            initialdir=str(home_dir),
            filetypes=[
                (
                    "Audio Files",
                    "*.m4a *.mp3 *.wav *.ogg *.wma *.flac *.aac *.ac3 "
                    "*.dts *.mpc *.ape *.ra *.mid *.midi *.mod *.3gp "
                    "*.aif *.aiff *.wv *.tta *.m4b *.m4r *.mp1 *.mp2"
                )
            ]
        )

        if paths:
            self.process_paths([Path(p) for p in paths])

    def remove_song(self):
        selected_indices = self.queue.curselection()
        # Delete items in reverse order to avoid index shifting problems
        for index in sorted(selected_indices, reverse=True):
            filepath = self.queue.get(index)
            self.queue.delete(index)
            self.db_cursor.execute('DELETE FROM queue WHERE filepath = ?', (filepath,))
        self.db_conn.commit()
        self.refresh_colors()
        self.update_scrollbar()

    def handle_delete(self, event):
        self.remove_song()
        return "break"  # Prevents the default behavior

    def play_selected(self, event=None):
        if self.queue.size() > 0:
            # Clear any existing selection first
            self.queue.selection_clear(0, tk.END)
            # Get the clicked index
            clicked_index = self.queue.nearest(event.y)
            self.queue.selection_set(clicked_index)
            self.queue.activate(clicked_index)
            selected_song = self.queue.get(clicked_index)

            # Check if we're in the Music library view
            selected_item = self.library_tree.selection()
            if selected_item:
                tags = self.library_tree.item(selected_item[0])['tags']
                if tags and tags[0] == 'music':
                    # Add to queue if playing from library
                    self.db_cursor.execute('INSERT INTO queue (filepath) VALUES (?)', (selected_song,))
                    self.db_conn.commit()

            media = self.player.media_new(selected_song)
            self.media_player.set_media(media)
            self.media_player.play()
            self.current_time = 0
            self.is_playing = True
            self.play_button.configure(text=BUTTON_SYMBOLS['pause'])
        return "break"  # Prevent default double-click behavior

    def refresh_colors(self):
        """Update the background colors of all items in the queue"""
        for i in range(self.queue.size()):
            bg_color = COLORS['alternate_row_colors'][i % 2]
            self.queue.itemconfigure(i, background=bg_color)

    def setup_drag_drop(self):
        self.queue.drop_target_register('DND_Files')
        self.queue.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        raw_paths = event.data

        match (sys.platform, '/Volumes/' in raw_paths):
            case ('darwin', True):
                potential_paths = raw_paths.split('\n')
                match len(potential_paths):
                    case 1:
                        parts = raw_paths.split()
                        reconstructed_path = []
                        current_path = []

                        for part in parts:
                            if part.startswith('/') or part.startswith('/Volumes'):
                                if current_path:
                                    reconstructed_path.append(' '.join(current_path))
                                    current_path = []
                                current_path.append(part)
                            else:
                                current_path.append(part)

                        if current_path:
                            reconstructed_path.append(' '.join(current_path))

                        paths = reconstructed_path
                    case _:
                        paths = potential_paths
            case _:
                paths = raw_paths.split()

        paths = [p.strip('{}').strip('"') for p in paths if p.strip()]

        # Get current view to determine where to add files
        selected_item = self.library_tree.selection()
        if selected_item:
            tags = self.library_tree.item(selected_item[0])['tags']
            if tags:
                if tags[0] == 'music':
                    # Add to library
                    self.process_paths(paths)
                elif tags[0] == 'now_playing':
                    # Add to queue - first ensure files are in library
                    self.process_paths(paths)
                    # Then add to queue
                    for path in paths:
                        normalized_path = str(normalize_path(path))
                        if os.path.exists(normalized_path):
                            self.db_cursor.execute('INSERT INTO queue (filepath) VALUES (?)', (normalized_path,))
                    self.db_conn.commit()
                    self.load_queue()

    def setup_progress_bar(self):
        # Create frame for progress bar
        self.progress_frame = ttk.Frame(self.window, height=PROGRESS_BAR['frame_height'])
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=PROGRESS_BAR['frame_side_padding'],
                               pady=PROGRESS_BAR['frame_padding'])

        # Create canvas for custom progress bar
        self.canvas = tk.Canvas(
            self.progress_frame,
            height=PROGRESS_BAR['canvas_height'],
            background=THEME_CONFIG['colors']['bg'],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X)

        # Setup playback controls on the left
        self.setup_playback_controls()

        # Create time labels
        self.time_text = self.canvas.create_text(
            self.canvas.winfo_width()-160, PROGRESS_BAR['time_label_y'],
            text="00:00 / 00:00",
            fill=THEME_CONFIG['colors']['fg'],
            anchor=tk.E
        )

        # Create progress bar line - start after the control buttons
        self.bar_y = PROGRESS_BAR['bar_y']
        self.line = self.canvas.create_line(
            self.controls_width, self.bar_y,
            self.canvas.winfo_width()-160, self.bar_y,
            fill=PROGRESS_BAR['line_color'],
            width=PROGRESS_BAR['line_width']
        )

        # Create progress circle at start position
        self.circle_radius = PROGRESS_BAR['circle_radius']
        self.progress_circle = self.canvas.create_oval(
            self.controls_width - self.circle_radius, self.bar_y - self.circle_radius,
            self.controls_width + self.circle_radius, self.bar_y + self.circle_radius,
            fill=PROGRESS_BAR['circle_fill'],
            outline=""
        )

        # Setup utility controls on the right
        self.setup_utility_controls()

        # Bind events
        self.dragging = False
        self.last_drag_time = 0
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self.start_drag)
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self.drag)
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self.end_drag)
        self.canvas.bind('<Button-1>', self.click_progress)
        self.canvas.bind('<Configure>', self.on_resize)

        # Start progress update
        self.update_progress()

    def setup_playback_controls(self):
        # Create buttons frame within canvas for playback controls (prev, play, next)
        button_frame = ttk.Frame(self.canvas)
        button_frame.place(x=10, y=PROGRESS_BAR['controls_y']-15)

        for i, (action, symbol) in enumerate([
            ('previous', BUTTON_SYMBOLS['prev']),
            ('play', BUTTON_SYMBOLS['play']),
            ('next', BUTTON_SYMBOLS['next'])
        ]):
            button = ttk.Button(
                button_frame,
                text=symbol,
                style='Controls.TButton',
                command=getattr(self, f"{action}_song" if action != 'play' else 'play_pause'),
                width=3
            )
            button.pack(side=tk.LEFT, padx=2)

            if action == 'play':
                self.play_button = button

        # Update the button frame after all buttons are packed to get its true width
        button_frame.update()
        # Store the width for progress bar calculations
        self.controls_width = button_frame.winfo_width() + 20

    def setup_utility_controls(self):
        # Create buttons frame within canvas for utility controls (loop, add)
        utility_frame = ttk.Frame(self.canvas)
        utility_frame.place(x=self.canvas.winfo_width()-150, y=PROGRESS_BAR['controls_y']-15)

        for action, symbol in [
            ('loop', BUTTON_SYMBOLS['loop']),
            ('add', BUTTON_SYMBOLS['add'])
        ]:
            button = ttk.Button(
                utility_frame,
                text=symbol,
                style='Loop.Controls.TButton' if action == 'loop' else 'Controls.TButton',
                command=getattr(self, "toggle_loop" if action == 'loop' else 'add_files_to_library'),
                width=3
            )
            button.pack(side=tk.LEFT, padx=2)

            if action == 'loop':
                self.loop_button = button

    def __del__(self):
        # Stop the file watcher if it exists
        if hasattr(self, 'observer') and self.observer:
            self.observer.stop()
            self.observer.join()

        # Clean up database connection
        if hasattr(self, 'db_conn'):
            self.db_conn.close()


def main():
    try:
        # Create custom theme style
        root = TkinterDnD.Tk()

        # Set application icon
        icon = tk.PhotoImage(file='mt.png')
        root.wm_iconphoto(False, icon)

        style = ttk.Style(theme='darkly')  # Start with darkly as base

        # Apply theme colors from config
        style.configure('TButton',
                       background=THEME_CONFIG['colors']['bg'],
                       foreground=THEME_CONFIG['colors']['fg'],
                       borderwidth=0,
                       relief='flat',
                       focuscolor='',           # Remove focus border
                       highlightthickness=0,    # Remove highlight border
                       font=BUTTON_STYLE['font'])

        # Configure specific styles for control buttons
        style.configure('Controls.TButton',
                       background=THEME_CONFIG['colors']['bg'],
                       foreground=THEME_CONFIG['colors']['fg'],
                       borderwidth=0,
                       relief='flat',
                       focuscolor='',           # Remove focus border
                       highlightthickness=0,    # Remove highlight border
                       font=BUTTON_STYLE['font'],
                       padding=BUTTON_STYLE['padding'])

        style.configure('Loop.Controls.TButton',
                       background=THEME_CONFIG['colors']['bg'],
                       foreground=THEME_CONFIG['colors']['fg'],
                       borderwidth=0,
                       relief='flat',
                       focuscolor='',           # Remove focus border
                       highlightthickness=0,    # Remove highlight border
                       font=BUTTON_STYLE['font'],
                       padding=BUTTON_STYLE['padding'])

        style.map('Controls.TButton',
                 background=[('active', THEME_CONFIG['colors']['bg'])],
                 foreground=[('active', THEME_CONFIG['colors']['primary'])])

        style.map('Loop.Controls.TButton',
                 background=[('active', THEME_CONFIG['colors']['bg'])],
                 foreground=[('active', THEME_CONFIG['colors']['primary'])])

        style.configure('TFrame', background=THEME_CONFIG['colors']['bg'])
        style.configure('TLabel', background=THEME_CONFIG['colors']['bg'], foreground=THEME_CONFIG['colors']['fg'])
        style.configure('Vertical.TScrollbar',
                       background=THEME_CONFIG['colors']['bg'],
                       troughcolor=THEME_CONFIG['colors']['dark'],
                       arrowcolor=THEME_CONFIG['colors']['fg'])

        # Update progress bar colors
        PROGRESS_BAR.update({
            'line_color': THEME_CONFIG['colors']['secondary'],
            'circle_fill': THEME_CONFIG['colors']['primary'],
            'circle_active_fill': THEME_CONFIG['colors']['active']
        })

        # Update listbox colors
        LISTBOX_CONFIG.update({
            'selectbackground': THEME_CONFIG['colors']['selectbg'],
            'selectforeground': THEME_CONFIG['colors']['selectfg'],
            'background': THEME_CONFIG['colors']['bg'],
            'foreground': THEME_CONFIG['colors']['fg']
        })

        # Update colors
        COLORS.update({
            'loop_enabled': THEME_CONFIG['colors']['primary'],
            'loop_disabled': THEME_CONFIG['colors']['secondary'],
            'alternate_row_colors': [THEME_CONFIG['colors']['bg'], THEME_CONFIG['colors']['selectbg']]
        })

        global player_instance
        player_instance = MusicPlayer(root)
        root.mainloop()
    except Exception as e:
        print(f"Error in main: {e}")
        if 'root' in locals():
            root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    player_instance = None
    main()
