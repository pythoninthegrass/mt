import sys
import vlc
from config import WINDOW_SIZE, WINDOW_TITLE
from core.queue import QueueManager
from pathlib import Path
from utils.files import find_audio_files, normalize_path
from utils.ui import ControlPanel, ProgressBar, QueueList, show_file_dialog


class MusicPlayer:
    def __init__(self, window):
        self.window = window
        self.window.title(WINDOW_TITLE)
        self.window.geometry(WINDOW_SIZE)

        # UI Components
        self.progress_bar = ProgressBar(window)
        self.queue_list = QueueList(window)
        self.controls = ControlPanel(window)
        self.queue_list.pack(pady=(0, 15), expand=True, fill='both')
        self.controls.pack(pady=(0, 5))

        # State
        self.is_playing = False
        self.current_time = 0
        self.loop_enabled = True

        # VLC setup
        self.player = vlc.Instance()
        self.media_player = self.player.media_player_new()

        # Setup queue manager
        self.queue_manager = QueueManager(self.queue_list.listbox)
        self.queue_manager.load_queue()

        # Initialize UI state
        self.setup_callbacks()
        self.setup_events()
        self.update_progress_timer()

    def setup_callbacks(self):
        # Progress bar callbacks
        self.progress_bar.on_drag_start = self.handle_progress_drag_start
        self.progress_bar.on_drag = self.handle_progress_drag
        self.progress_bar.on_drag_end = self.handle_progress_drag_end
        self.progress_bar.on_progress_click = self.handle_progress_click

        # Control panel callbacks
        self.controls.add_button.config(command=self.add_to_queue)
        self.controls.prev_button.config(command=self.previous_song)
        self.controls.play_button.config(command=self.play_pause)
        self.controls.next_button.config(command=self.next_song_button)
        self.controls.loop_button.config(command=self.toggle_loop)

        # Queue list callbacks
        self.queue_list.listbox.bind('<Double-Button-1>', self.play_selected)
        self.queue_list.listbox.bind('<Delete>', self.handle_delete)
        self.queue_list.listbox.bind('<BackSpace>', self.handle_delete)

    def setup_events(self):
        # VLC event handler for song end
        event_type = vlc.EventType.MediaPlayerEndReached
        self.media_player.event_manager().event_attach(event_type, self.next_song)

        # Setup drag and drop
        self.queue_list.setup_dnd()
        self.queue_list.on_drop = self.handle_drop  # Connect the handler directly

    def update_progress_timer(self):
        if self.is_playing and self.media_player.is_playing():
            current = self.media_player.get_time()
            duration = self.media_player.get_length()

            if duration > 0:
                ratio = current / duration
                elapsed_seconds = current / 1000
                duration_seconds = duration / 1000
                remaining_seconds = duration_seconds - elapsed_seconds

                self.progress_bar.update_progress(ratio, elapsed_seconds, remaining_seconds)

        self.window.after(100, self.update_progress_timer)

    def handle_progress_drag_start(self):
        self.was_playing = self.is_playing
        if self.is_playing:
            self.media_player.pause()
            self.controls.play_button.config(text="⏯")
            self.is_playing = False

    def handle_progress_drag(self, ratio):
        if self.media_player.get_length() > 0:
            self.current_time = int(self.media_player.get_length() * ratio)

    def handle_progress_drag_end(self):
        if self.media_player.get_length() > 0:
            self.media_player.set_time(self.current_time)
            if self.was_playing:
                self.media_player.play()
                self.controls.play_button.config(text="⏸")
                self.is_playing = True

    def handle_progress_click(self, ratio):
        if self.media_player.get_length() > 0:
            self.current_time = int(self.media_player.get_length() * ratio)
            self.media_player.set_time(self.current_time)

    def play_pause(self):
        if not self.is_playing:
            if self.media_player.get_media() is not None:
                self.media_player.play()
            else:
                if self.queue_list.listbox.size() == 0:
                    return
                selected_song = self.queue_list.listbox.get('active')
                media = self.player.media_new(selected_song)
                self.media_player.set_media(media)
                if self.current_time > 0:
                    self.media_player.play()
                    self.media_player.set_time(self.current_time)
                else:
                    self.media_player.play()
            self.controls.play_button.config(text="⏸")
            self.is_playing = True
        else:
            self.current_time = self.media_player.get_time()
            self.media_player.pause()
            self.controls.play_button.config(text="⏯")
            self.is_playing = False

    def add_to_queue(self):
        paths = show_file_dialog()
        if paths:
            self.process_paths(paths)

    def process_paths(self, paths):
        existing_files = set(self.queue_list.listbox.get(0, 'end'))
        new_files = set()

        for path in paths:
            if not path or path.isspace():
                continue

            path_obj = normalize_path(path)
            if path_obj.exists():
                if path_obj.is_file():
                    new_files.add(str(path_obj))
                else:
                    new_files.update(find_audio_files(path_obj))

        files_to_add = sorted(new_files - existing_files)
        if files_to_add:
            for filepath in files_to_add:
                self.queue_list.listbox.insert('end', filepath)
                self.queue_manager.db_cursor.execute(
                    'INSERT INTO queue (filepath) VALUES (?)', (filepath,)
                )
            self.queue_manager.db_conn.commit()

            if self.queue_list.listbox.size() == len(files_to_add):
                self.queue_list.listbox.selection_set(0)
                self.queue_list.listbox.activate(0)
            self.queue_list.refresh_colors()

    def next_song_button(self, event=None):
        if self.queue_list.listbox.size() > 0:
            current = self.queue_list.listbox.curselection()
            current_index = current[0] if current else -1

            if current_index == -1:
                next_index = 0
            elif not self.loop_enabled and current_index == self.queue_list.listbox.size() - 1:
                self.media_player.stop()
                self.is_playing = False
                self.controls.play_button.config(text="⏯")
                self.current_time = 0
                return
            else:
                next_index = (current_index + 1) % self.queue_list.listbox.size()

            self.play_index(next_index)

    def previous_song(self):
        if self.queue_list.listbox.size() > 0:
            current = self.queue_list.listbox.curselection()
            current_index = current[0] if current else 0
            prev_index = (current_index - 1) % self.queue_list.listbox.size()
            self.play_index(prev_index)

    def play_index(self, index):
        self.queue_list.listbox.selection_clear(0, 'end')
        self.queue_list.listbox.activate(index)
        self.queue_list.listbox.selection_set(index)
        self.queue_list.listbox.see(index)

        selected_song = self.queue_list.listbox.get(index)
        media = self.player.media_new(selected_song)
        self.media_player.set_media(media)
        self.media_player.play()
        self.current_time = 0
        self.is_playing = True
        self.controls.play_button.config(text="⏸")

    def play_selected(self, event):
        if self.queue_list.listbox.size() > 0:
            clicked_index = self.queue_list.listbox.nearest(event.y)
            self.play_index(clicked_index)
        return "break"

    def toggle_loop(self):
        self.loop_enabled = not self.loop_enabled
        self.controls.loop_button.config(
            text="⟳",
            fg="green" if self.loop_enabled else "black"
        )

    def handle_delete(self, event):
        selected = self.queue_list.listbox.curselection()
        for index in reversed(selected):
            filepath = self.queue_list.listbox.get(index)
            self.queue_list.listbox.delete(index)
            self.queue_manager.db_cursor.execute(
                'DELETE FROM queue WHERE filepath = ?', (filepath,)
            )
        self.queue_manager.db_conn.commit()
        self.queue_list.refresh_colors()
        return "break"

    def handle_drop(self, event):
        raw_paths = event.data
        paths = []

        if sys.platform == 'darwin' and '/Volumes/' in raw_paths:
            if '\n' in raw_paths:
                paths = raw_paths.split('\n')
            else:
                parts = raw_paths.split()
                current_path = []
                for part in parts:
                    if part.startswith('/') or part.startswith('/Volumes'):
                        if current_path:
                            paths.append(' '.join(current_path))
                            current_path = []
                        current_path.append(part)
                    else:
                        current_path.append(part)
                if current_path:
                    paths.append(' '.join(current_path))
        else:
            paths = raw_paths.split()

        paths = [p.strip('{}').strip('"') for p in paths if p.strip()]
        self.process_paths(paths)

    def next_song(self, event):
        self.next_song_button()

    def __del__(self):
        if hasattr(self, 'queue_manager'):
            self.queue_manager.db_conn.close()
