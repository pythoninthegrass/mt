#!/usr/bin/env python

import os
import sqlite3
import sys
import time
import tkinter as tk
import vlc
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

def find_audio_files(directory, max_depth=5):
    AUDIO_EXTENSIONS = {
        '.m4a', '.mp3', '.wav', '.ogg', '.wma', '.flac', '.aac',
        '.ac3', '.dts', '.mpc', '.ape', '.ra', '.mid', '.midi',
        '.mod', '.3gp', '.aif', '.aiff', '.wv', '.tta', '.m4b',
        '.m4r', '.mp1', '.mp2'
    }

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
    def load_queue(self):
        self.db_cursor.execute('SELECT filepath FROM queue ORDER BY id')
        for (filepath,) in self.db_cursor.fetchall():
            if os.path.exists(filepath):  # Only add if file still exists
                self.queue.insert(tk.END, filepath)
        if self.queue.size() > 0:
            self.queue.selection_set(0)
            self.queue.activate(0)
        self.refresh_colors()

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
            self.play_button.config(text="⏸")  # Unicode pause symbol
            self.is_playing = True
        else:
            self.current_time = self.media_player.get_time()
            self.media_player.pause()
            self.play_button.config(text="⏯")  # Unicode play/pause symbol
            self.is_playing = False

    def __init__(self, window):
        self.window = window
        self.window.title("mt")
        self.window.geometry("640x720")
        self.is_playing = False
        self.current_time = 0

        # Initialize database
        self.db_conn = sqlite3.connect('mt.db')
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS queue
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             filepath TEXT NOT NULL)
        ''')
        # Create settings table for persistent state
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self.db_conn.commit()

        # Load loop state from settings; default to True if unset
        self.db_cursor.execute("SELECT value FROM settings WHERE key = 'loop_enabled'")
        result = self.db_cursor.fetchone()
        if result is None:
            self.loop_enabled = True
            self.db_cursor.execute("INSERT INTO settings (key, value) VALUES ('loop_enabled', '1')")
            self.db_conn.commit()
        else:
            self.loop_enabled = (result[0] == '1')

        # Create progress bar frame with increased height and adjusted padding
        self.progress_frame = tk.Frame(self.window, height=60)
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 20))

        # Create canvas for progress bar
        self.canvas = tk.Canvas(self.progress_frame, height=50)  # Increased height from 40 to 50
        self.canvas.pack(fill=tk.X, expand=True)

        # Calculate vertical center
        self.bar_y = 20  # Vertical center of the canvas
        self.circle_radius = 6  # Define circle radius as instance variable

        # Create progress line and circle
        self.line = self.canvas.create_line(10, self.bar_y, self.canvas.winfo_reqwidth()-10, self.bar_y, fill='gray', width=2)
        self.progress_circle = self.canvas.create_oval(
            10 - self.circle_radius, self.bar_y - self.circle_radius,
            10 + self.circle_radius, self.bar_y + self.circle_radius,
            fill='blue', activefill='lightblue'
        )

        # Add time labels below the line
        self.elapsed_text = self.canvas.create_text(10, 45, anchor='sw', text="00:00")  # Changed y from 35 to 45
        self.remaining_text = self.canvas.create_text(self.canvas.winfo_width()-10, 45, anchor='se', text="00:00")  # Changed y from 35 to 45

        # Create the queue with no top padding
        self.queue = tk.Listbox(self.window, width=50, selectmode=tk.EXTENDED)
        self.queue.pack(pady=(0, 15), expand=True, fill=tk.BOTH)

        # Configure colors for the listbox
        self.queue.configure(selectbackground='lightblue', activestyle='none')

        # Add double-click binding
        self.queue.bind('<Double-Button-1>', self.play_selected)

        # Load saved queue
        self.load_queue()

        # Add keyboard bindings for delete/backspace
        self.queue.bind('<Delete>', self.handle_delete)
        self.queue.bind('<BackSpace>', self.handle_delete)

        # Create the controls frame with adjusted padding
        controls_frame = tk.Frame(self.window)
        controls_frame.pack(pady=(0, 5))

        # Common button style configuration
        button_config = {
            'width': 5,
            'height': 2,
            'font': ('TkDefaultFont', 18, 'bold'),
            'padx': 8,
            'pady': 5,
        }

        # Create buttons with new configuration
        self.add_button = tk.Button(controls_frame, text="+", **button_config)
        self.add_button.config(command=self.add_to_queue)
        self.add_button.grid(row=0, column=0, padx=8)

        self.prev_button = tk.Button(controls_frame, text="⏮", **button_config)
        self.prev_button.config(command=self.previous_song)
        self.prev_button.grid(row=0, column=1, padx=8)

        self.play_button = tk.Button(controls_frame, text="⏯", **button_config)
        self.play_button.config(command=self.play_pause)
        self.play_button.grid(row=0, column=2, padx=8)

        self.next_button = tk.Button(controls_frame, text="⏭", **button_config)
        self.next_button.config(command=self.next_song_button)
        self.next_button.grid(row=0, column=3, padx=8)

        initial_color = "green" if self.loop_enabled else "black"
        self.loop_button = tk.Button(controls_frame, text="⟳", fg=initial_color, **button_config)
        self.loop_button.config(command=self.toggle_loop)
        self.loop_button.grid(row=0, column=4, padx=8)

        # Add mouse bindings for drag functionality
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self.start_drag)
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self.drag)
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self.end_drag)
        # Bind click on anywhere in the timeline to reposition playhead
        self.canvas.bind('<Button-1>', self.click_progress)

        # Bind canvas resize event
        self.canvas.bind('<Configure>', self.on_resize)

        # Dragging state
        self.dragging = False
        self.last_drag_time = 0

        # Add update timer
        self.window.after(100, self.update_progress)

        # Create the vlc player instance
        self.player = vlc.Instance()
        self.media_player = self.player.media_player_new()

        # Set the end event
        the_event = vlc.EventType.MediaPlayerEndReached
        self.media_player.event_manager().event_attach(the_event, self.next_song)

        # Initialize drag and drop
        self.setup_drag_drop()

    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        # Update button fg based on loop_enabled state
        self.loop_button.config(text="⟳", fg="green" if self.loop_enabled else "black")
        # Update loop state in the settings table for persistence
        self.db_cursor.execute("UPDATE settings SET value = ? WHERE key = ?", ('1' if self.loop_enabled else '0', 'loop_enabled'))
        self.db_conn.commit()

    def start_drag(self, event):
        self.dragging = True
        self.was_playing = self.is_playing
        # Pause manually instead of toggling play_pause
        if self.is_playing:
            self.media_player.pause()
            self.play_button.config(text="⏯")
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
                    self.play_button.config(text="⏸")
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
        self.canvas.coords(self.elapsed_text, 10, 45)  # Changed y from 35 to 45
        self.canvas.coords(self.remaining_text, event.width-10, 45)  # Changed y from 35 to 45

    def update_progress(self):
        if self.is_playing and self.media_player.is_playing():
            if not self.dragging and (time.time() - self.last_drag_time) > 0.1:
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

        self.window.after(100, self.update_progress)

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
                self.play_button.config(text="⏯")  # Use Unicode play/pause symbol
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
            self.play_button.config(text="⏸")

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
            self.play_button.config(text="⏸")

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
            self.play_button.config(text="⏸")
        return "break"  # Prevent default double-click behavior

    def refresh_colors(self):
        """Update the background colors of all items in the queue"""
        for i in range(self.queue.size()):
            bg_color = '#f0f0f0' if i % 2 else 'white'
            self.queue.itemconfigure(i, background=bg_color)

    def setup_drag_drop(self):
        self.queue.drop_target_register('DND_Files')
        self.queue.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        raw_paths = event.data

        if sys.platform == 'darwin':
            if '/Volumes/' in raw_paths:
                potential_paths = raw_paths.split('\n')

                if len(potential_paths) == 1:
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
                else:
                    paths = potential_paths
            else:
                paths = raw_paths.split()
        else:
            paths = raw_paths.split()

        paths = [p.strip('{}').strip('"') for p in paths if p.strip()]
        self.process_paths(paths)

    def __del__(self):
        # Clean up database connection
        if hasattr(self, 'db_conn'):
            self.db_conn.close()


def main():
    root = TkinterDnD.Tk()
    player = MusicPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
