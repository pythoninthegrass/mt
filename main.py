#!/usr/bin/env python

import os
import sqlite3
import time
import tkinter as tk
import vlc
from tkinter import filedialog


class MusicPlayer:
    def load_queue(self):
        self.db_cursor.execute('SELECT filepath FROM queue ORDER BY id')
        for (filepath,) in self.db_cursor.fetchall():
            if os.path.exists(filepath):  # Only add if file still exists
                self.queue.insert(tk.END, filepath)
        if self.queue.size() > 0:
            self.queue.selection_set(0)
            self.queue.activate(0)

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
        self.window.geometry("640x480")
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

        # Create progress bar frame with increased height
        self.progress_frame = tk.Frame(self.window, height=100)
        self.progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(10, 20))

        # Create canvas for progress bar with increased height
        self.canvas = tk.Canvas(self.progress_frame, height=80)
        self.canvas.pack(fill=tk.X)

        # Create progress line and circle - centered at y=20
        self.line = self.canvas.create_line(10, 20, self.canvas.winfo_reqwidth()-10, 20, fill='gray', width=2)
        self.progress_circle = self.canvas.create_oval(5, 15, 20, 30, fill='blue', activefill='lightblue')

        # Add time labels below the line
        self.elapsed_text = self.canvas.create_text(10, 65, anchor='sw', text="00:00")
        self.remaining_text = self.canvas.create_text(self.canvas.winfo_width()-10, 65, anchor='se', text="00:00")

        # Create the queue with adjusted padding
        self.queue = tk.Listbox(self.window, width=50, selectmode=tk.EXTENDED)
        self.queue.pack(pady=10, expand=True, fill=tk.BOTH)

        # Add double-click binding
        self.queue.bind('<Double-Button-1>', self.play_selected)

        # Load saved queue
        self.load_queue()

        # Add keyboard bindings for delete/backspace
        self.queue.bind('<Delete>', self.handle_delete)
        self.queue.bind('<BackSpace>', self.handle_delete)

        # Create the controls frame with more padding and a border
        controls_frame = tk.Frame(self.window)
        controls_frame.pack(pady=20)

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
            self.canvas.coords(self.progress_circle, x-7.5, 15, x+7.5, 30)
            ratio = (x - 10) / width
            if self.media_player.get_length() > 0:
                self.current_time = int(self.media_player.get_length() * ratio)
                self.last_drag_time = time.time()

    def end_drag(self, event):
        if self.dragging:
            self.dragging = False
            if self.media_player.get_length() > 0:
                self.media_player.set_time(self.current_time)
                # Update progress circle based on current_time immediately
                duration = self.media_player.get_length()
                ratio = self.current_time / duration if duration > 0 else 0
                width = self.canvas.winfo_width()
                x = 10 + (width - 20) * ratio
                self.canvas.coords(self.progress_circle, x-7.5, 15, x+7.5, 30)
                # Resume playback manually if it was playing before dragging
                if self.was_playing:
                    self.media_player.play()
                    self.play_button.config(text="⏸")
                    self.is_playing = True

    def click_progress(self, event):
        # Ignore if the click is on the progress circle (handled by drag)
        circle_coords = self.canvas.coords(self.progress_circle)
        if circle_coords[0] <= event.x <= circle_coords[2] and circle_coords[1] <= event.y <= circle_coords[3]:
            return
        width = self.canvas.winfo_width() - 20
        x = min(max(event.x, 10), self.canvas.winfo_width() - 10)
        ratio = (x - 10) / width
        if self.media_player.get_length() > 0:
            self.current_time = int(self.media_player.get_length() * ratio)
            self.media_player.set_time(self.current_time)
            # Update progress circle position immediately
            self.canvas.coords(self.progress_circle, x-7.5, 15, x+7.5, 30)

    def on_resize(self, event):
        self.canvas.coords(self.line, 10, 20, event.width-10, 20)
        # Update positions of time labels
        self.canvas.coords(self.elapsed_text, 10, 65)
        self.canvas.coords(self.remaining_text, event.width-10, 65)

    def update_progress(self):
        if self.is_playing and self.media_player.is_playing():
            # Only update position if not dragging and enough time has passed since last drag
            if not self.dragging and (time.time() - self.last_drag_time) > 0.1:
                current = self.media_player.get_time()
                duration = self.media_player.get_length()

                if duration > 0:
                    ratio = current / duration
                    width = self.canvas.winfo_width()
                    x = 10 + (width - 20) * ratio
                    self.canvas.coords(self.progress_circle, x-7.5, 15, x+7.5, 30)

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

    def add_to_queue(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[
                (
                    "Audio Files",
                    """
                    *.m4a *.mp3 *.wav *.ogg *.wma *.flac *.aac *.ac3
                    *.dts *.mpc *.ape *.ra *.mid *.midi *.mod *.3gp
                    *.aif *.aiff *.wv *.tta *.m4b *.m4r *.mp1 *.mp2
                    """
                )
            ]
        )

        if file_paths:
            for file_path in file_paths:
                self.queue.insert(tk.END, file_path)
                self.db_cursor.execute('INSERT INTO queue (filepath) VALUES (?)', (file_path,))
            self.db_conn.commit()
            # Select first song if queue was empty
            if self.queue.size() == len(file_paths):
                self.queue.selection_set(0)
                self.queue.activate(0)

    def remove_song(self):
        selected_indices = self.queue.curselection()
        # Delete items in reverse order to avoid index shifting problems
        for index in sorted(selected_indices, reverse=True):
            filepath = self.queue.get(index)
            self.queue.delete(index)
            self.db_cursor.execute('DELETE FROM queue WHERE filepath = ?', (filepath,))
        self.db_conn.commit()

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

    def __del__(self):
        # Clean up database connection
        if hasattr(self, 'db_conn'):
            self.db_conn.close()


def main():
    window = tk.Tk()
    music_player = MusicPlayer(window)
    window.mainloop()


if __name__ == "__main__":
    main()
