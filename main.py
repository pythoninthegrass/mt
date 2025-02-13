#!/usr/bin/env python

import json
import os
import sqlite3
import sys
import time
import tkinter as tk
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
    THEME_CONFIG,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from pathlib import Path
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD


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
        self.is_playing = False
        self.current_time = 0

        # Initialize database
        self.db_conn = sqlite3.connect(DB_NAME)
        self.db_cursor = self.db_conn.cursor()
        for table_name, create_sql in DB_TABLES.items():
            self.db_cursor.execute(create_sql)
        self.db_conn.commit()

        # Load loop state from settings; default to configured value if unset
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'loop_enabled'")
        result = self.db_cursor.fetchone()
        if result is None:
            self.loop_enabled = DEFAULT_LOOP_ENABLED
            self.db_cursor.execute("INSERT INTO settings (key, value) VALUES ('loop_enabled', '1')")
            self.db_conn.commit()
        else:
            self.loop_enabled = (result[0] == '1')

        # Create progress bar frame
        self.progress_frame = ttk.Frame(self.window, height=PROGRESS_BAR['frame_height'], style='TFrame')
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=PROGRESS_BAR['frame_side_padding'], pady=PROGRESS_BAR['frame_padding'])

        # Create canvas for progress bar
        self.canvas = tk.Canvas(self.progress_frame, height=PROGRESS_BAR['canvas_height'],
                              background=COLORS['alternate_row_colors'][0],
                              highlightthickness=0)
        self.canvas.pack(fill=tk.X, expand=True)

        # Store progress bar configuration
        self.bar_y = PROGRESS_BAR['bar_y']
        self.circle_radius = PROGRESS_BAR['circle_radius']

        # Create progress line and circle
        self.line = self.canvas.create_line(
            10, self.bar_y, self.canvas.winfo_reqwidth()-10, self.bar_y,
            fill=PROGRESS_BAR['line_color'], width=PROGRESS_BAR['line_width']
        )
        self.progress_circle = self.canvas.create_oval(
            10 - self.circle_radius, self.bar_y - self.circle_radius,
            10 + self.circle_radius, self.bar_y + self.circle_radius,
            fill=PROGRESS_BAR['circle_fill'], activefill=PROGRESS_BAR['circle_active_fill']
        )

        # Add time labels
        self.elapsed_text = self.canvas.create_text(
            10, PROGRESS_BAR['time_label_y'], anchor='sw', text="00:00",
            fill=LISTBOX_CONFIG['foreground']
        )
        self.remaining_text = self.canvas.create_text(
            self.canvas.winfo_width()-10, PROGRESS_BAR['time_label_y'],
            anchor='se', text="00:00",
            fill=LISTBOX_CONFIG['foreground']
        )

        # Create queue frame and listbox
        self.queue_frame = ttk.Frame(self.window, style='TFrame')
        self.queue_frame.pack(pady=LISTBOX_CONFIG['padding'], expand=True, fill=tk.BOTH)

        self.scrollbar = ttk.Scrollbar(self.queue_frame, orient=tk.VERTICAL, style='Vertical.TScrollbar')
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.queue = tk.Listbox(
            self.queue_frame,
            width=LISTBOX_CONFIG['width'],
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
        self.queue_frame.bind('<Configure>', lambda e: self.update_scrollbar())

        # Add queue bindings
        self.queue.bind('<Double-Button-1>', self.play_selected)
        self.queue.bind('<Delete>', self.handle_delete)
        self.queue.bind('<BackSpace>', self.handle_delete)

        # Load saved queue
        self.load_queue()

        # Create controls frame
        controls_frame = ttk.Frame(self.window, style='TFrame')
        controls_frame.pack(pady=(0, 5))

        # Create buttons
        self.add_button = ttk.Button(controls_frame, text=BUTTON_SYMBOLS['add'], style='TButton')
        self.add_button.config(command=self.add_to_queue)
        self.add_button.grid(row=0, column=0, padx=8)

        self.prev_button = ttk.Button(controls_frame, text=BUTTON_SYMBOLS['prev'], style='TButton')
        self.prev_button.config(command=self.previous_song)
        self.prev_button.grid(row=0, column=1, padx=8)

        self.play_button = ttk.Button(controls_frame, text=BUTTON_SYMBOLS['play'], style='TButton')
        self.play_button.config(command=self.play_pause)
        self.play_button.grid(row=0, column=2, padx=8)

        self.next_button = ttk.Button(controls_frame, text=BUTTON_SYMBOLS['next'], style='TButton')
        self.next_button.config(command=self.next_song_button)
        self.next_button.grid(row=0, column=3, padx=8)

        initial_color = COLORS['loop_enabled'] if self.loop_enabled else COLORS['loop_disabled']
        self.loop_button = ttk.Button(controls_frame, text=BUTTON_SYMBOLS['loop'], style='TButton')
        self.loop_button.config(command=self.toggle_loop)
        self.loop_button.grid(row=0, column=4, padx=8)

        # Add progress bar bindings
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self.start_drag)
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self.drag)
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self.end_drag)
        self.canvas.bind('<Button-1>', self.click_progress)
        self.canvas.bind('<Configure>', self.on_resize)

        # Initialize dragging state
        self.dragging = False
        self.last_drag_time = 0

        # Add update timer
        self.window.after(PROGRESS_UPDATE_INTERVAL, self.update_progress)

        # Initialize VLC player
        self.player = vlc.Instance()
        self.media_player = self.player.media_player_new()
        self.media_player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.next_song)

        # Initialize drag and drop
        self.setup_drag_drop()

    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        style = ttk.Style()
        style.configure('TButton',
                       foreground=COLORS['loop_enabled'] if self.loop_enabled else COLORS['loop_disabled'])
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
            width = self.canvas.winfo_width() - 20
            x = min(max(event.x, 10), self.canvas.winfo_width() - 10)
            self.canvas.coords(self.progress_circle,
                x - self.circle_radius, self.bar_y - self.circle_radius,
                x + self.circle_radius, self.bar_y + self.circle_radius)
            ratio = (x - 10) / width
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
                x = 10 + (width - 20) * ratio
                self.canvas.coords(self.progress_circle,
                    x - self.circle_radius, self.bar_y - self.circle_radius,
                    x + self.circle_radius, self.bar_y + self.circle_radius)
                if self.was_playing:
                    self.media_player.play()
                    self.play_button.configure(text=BUTTON_SYMBOLS['pause'])
                    self.is_playing = True

    def click_progress(self, event):
        circle_coords = self.canvas.coords(self.progress_circle)
        if circle_coords[0] <= event.x <= circle_coords[2] and circle_coords[1] <= event.y <= circle_coords[3]:
            return
        width = self.canvas.winfo_width() - 20
        x = min(max(event.x, 10), self.canvas.winfo_width() - 10)
        ratio = (x - 10) / width
        if self.media_player.get_length() > 0:
            self.current_time = int(self.media_player.get_length() * ratio)
            self.media_player.set_time(self.current_time)
            self.canvas.coords(self.progress_circle,
                x - self.circle_radius, self.bar_y - self.circle_radius,
                x + self.circle_radius, self.bar_y + self.circle_radius)

    def on_resize(self, event):
        self.canvas.coords(self.line, 10, self.bar_y, event.width-10, self.bar_y)
        self.canvas.coords(self.elapsed_text, 10, PROGRESS_BAR['time_label_y'])
        self.canvas.coords(self.remaining_text, event.width-10, PROGRESS_BAR['time_label_y'])

    def update_progress(self):
        if (self.is_playing and self.media_player.is_playing() and
            not self.dragging and (time.time() - self.last_drag_time) > 0.1):
            current = self.media_player.get_time()
            duration = self.media_player.get_length()

            if duration > 0:
                ratio = current / duration
                width = self.canvas.winfo_width()
                x = 10 + (width - 20) * ratio
                self.canvas.coords(self.progress_circle,
                    x - self.circle_radius, self.bar_y - self.circle_radius,
                    x + self.circle_radius, self.bar_y + self.circle_radius)

                # Compute and update elapsed and remaining times
                elapsed_seconds = current / 1000
                duration_seconds = duration / 1000
                remaining_seconds = duration_seconds - elapsed_seconds
                def format_time(seconds):
                    seconds = int(seconds)
                    sign = "" if seconds >= 0 else "-"
                    seconds = abs(seconds)
                    m = seconds // 60
                    s = seconds % 60
                    return f"{sign}{m:02d}:{s:02d}"
                self.canvas.itemconfig(self.elapsed_text, text=format_time(elapsed_seconds))
                self.canvas.itemconfig(self.remaining_text, text=format_time(remaining_seconds))

        self.window.after(PROGRESS_UPDATE_INTERVAL, self.update_progress)

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

    def next_song(self, event):
        # For automatic next on song end
        self.next_song_button()

    def process_paths(self, paths):
        existing_files = set(self.queue.get(0, tk.END))
        new_files = set()

        for path in paths:
            if not path or path.isspace():
                continue

            normalized_path = normalize_path(path)

            if os.path.exists(str(normalized_path)):
                if os.path.isdir(str(normalized_path)):
                    new_files.update(find_audio_files(normalized_path))
                elif os.path.isfile(str(normalized_path)):
                    new_files.add(str(normalized_path))

        files_to_add = sorted(new_files - existing_files)

        if files_to_add:
            for file_path in files_to_add:
                if os.path.exists(file_path):
                    self.queue.insert(tk.END, file_path)
                    self.db_cursor.execute('INSERT INTO queue (filepath) VALUES (?)',
                                        (file_path,))

            self.db_conn.commit()

            if self.queue.size() == len(files_to_add):
                self.queue.selection_set(0)
                self.queue.activate(0)
            self.refresh_colors()
            self.update_scrollbar()

    def add_to_queue(self):
        # Let user choose between files or directory
        action = filedialog.askdirectory(title="Select Music Directory")

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
            self.process_paths([str(Path(p)) for p in paths])

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
        self.process_paths(paths)

    def __del__(self):
        # Clean up database connection
        if hasattr(self, 'db_conn'):
            self.db_conn.close()


def main():
    # Create custom theme style
    root = TkinterDnD.Tk()
    style = ttk.Style(theme='darkly')  # Start with darkly as base

    # Apply theme colors from config
    style.configure('TButton',
                   background=THEME_CONFIG['colors']['bg'],
                   foreground=THEME_CONFIG['colors']['fg'],
                   bordercolor=THEME_CONFIG['colors']['border'],
                   focuscolor=THEME_CONFIG['colors']['primary'],
                   font=BUTTON_STYLE['font'])

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

    player = MusicPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
