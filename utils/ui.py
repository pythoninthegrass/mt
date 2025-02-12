import time
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from config import BUTTON_STYLE
from tkinterdnd2 import DND_FILES
from utils.files import find_audio_files


class ProgressBar:
    def __init__(self, parent, height=60):
        self.frame = tk.Frame(parent, height=height)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 20))

        self.canvas = tk.Canvas(self.frame, height=50)
        self.canvas.pack(fill=tk.X, expand=True)

        self.bar_y = 20
        self.circle_radius = 6

        self.line = self.canvas.create_line(
            10, self.bar_y,
            self.canvas.winfo_reqwidth()-10, self.bar_y,
            fill='gray', width=2
        )

        self.progress_circle = self.canvas.create_oval(
            10 - self.circle_radius, self.bar_y - self.circle_radius,
            10 + self.circle_radius, self.bar_y + self.circle_radius,
            fill='blue', activefill='lightblue'
        )

        self.elapsed_text = self.canvas.create_text(10, 45, anchor='sw', text="00:00")
        self.remaining_text = self.canvas.create_text(
            self.canvas.winfo_width()-10, 45, anchor='se', text="00:00"
        )

        self.dragging = False
        self.last_drag_time = 0

        self._bind_events()

    def _bind_events(self):
        self.canvas.tag_bind(self.progress_circle, '<Button-1>', self._start_drag)
        self.canvas.tag_bind(self.progress_circle, '<B1-Motion>', self._drag)
        self.canvas.tag_bind(self.progress_circle, '<ButtonRelease-1>', self._end_drag)
        self.canvas.bind('<Button-1>', self._click_progress)
        self.canvas.bind('<Configure>', self._on_resize)

    def _start_drag(self, event):
        self.dragging = True
        if self.on_drag_start:
            self.on_drag_start()

    def _drag(self, event):
        if self.dragging:
            width = self.canvas.winfo_width() - 20
            x = min(max(event.x, 10), self.canvas.winfo_width() - 10)
            self._update_circle_position(x)
            if self.on_drag:
                ratio = (x - 10) / width
                self.on_drag(ratio)
            self.last_drag_time = time.time()

    def _end_drag(self, event):
        if self.dragging:
            self.dragging = False
            if self.on_drag_end:
                self.on_drag_end()

    def _click_progress(self, event):
        circle_coords = self.canvas.coords(self.progress_circle)
        if circle_coords[0] <= event.x <= circle_coords[2] and \
           circle_coords[1] <= event.y <= circle_coords[3]:
            return

        width = self.canvas.winfo_width() - 20
        x = min(max(event.x, 10), self.canvas.winfo_width() - 10)
        ratio = (x - 10) / width
        if self.on_progress_click:
            self.on_progress_click(ratio)

    def _on_resize(self, event):
        self.canvas.coords(self.line, 10, self.bar_y, event.width-10, self.bar_y)
        self.canvas.coords(self.elapsed_text, 10, 45)
        self.canvas.coords(self.remaining_text, event.width-10, 45)

    def _update_circle_position(self, x):
        self.canvas.coords(
            self.progress_circle,
            x - self.circle_radius, self.bar_y - self.circle_radius,
            x + self.circle_radius, self.bar_y + self.circle_radius
        )

    def update_progress(self, ratio, elapsed_time, remaining_time):
        if not self.dragging and (time.time() - self.last_drag_time) > 0.1:
            width = self.canvas.winfo_width()
            x = 10 + (width - 20) * ratio
            self._update_circle_position(x)
            self._update_time_display(elapsed_time, remaining_time)

    def _update_time_display(self, elapsed_seconds, remaining_seconds):
        def format_time(seconds):
            seconds = int(seconds)
            sign = "" if seconds >= 0 else "-"
            seconds = abs(seconds)
            m = seconds // 60
            s = seconds % 60
            return f"{sign}{m:02d}:{s:02d}"

        self.canvas.itemconfig(self.elapsed_text, text=format_time(elapsed_seconds))
        self.canvas.itemconfig(self.remaining_text, text=format_time(remaining_seconds))


class QueueList(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()
        self.on_drop = None
        self.pack(pady=(0, 15), expand=True, fill=tk.BOTH)

    def setup_ui(self):
        # Create and pack scrollbar first
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create listbox with scrollbar attached
        self.listbox = tk.Listbox(
            self,
            width=50,
            selectmode=tk.EXTENDED,
            yscrollcommand=self._on_scroll,
            selectbackground='lightblue',
            activestyle='none'
        )

        # Pack listbox and configure scrollbar
        self.listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.listbox.yview)

        # Bind events to ensure colors stay updated
        self.listbox.bind('<Configure>', lambda e: self.refresh_colors())
        self.bind('<Configure>', lambda e: self.refresh_colors())

    def setup_dnd(self):
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', lambda e: self.on_drop(e) if self.on_drop else None)

    def _on_scroll(self, *args):
        self.scrollbar.set(*args)
        self._update_scrollbar()
        self.refresh_colors()

    def _update_scrollbar(self):
        try:
            # Get the total size of all items
            total_size = self.listbox.size()
            if total_size == 0:
                self.scrollbar.pack_forget()
                return

            # Get first visible item's bbox to calculate item height
            first_bbox = self.listbox.bbox(0)
            if not first_bbox:
                return

            item_height = first_bbox[3]  # Height of single item
            total_height = item_height * total_size
            visible_height = self.listbox.winfo_height()

            if total_height > visible_height:
                self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            else:
                self.scrollbar.pack_forget()

        except (tk.TclError, AttributeError):
            # Handle potential errors during widget initialization
            pass
        self.refresh_colors()

    def refresh_colors(self):
        """Update the background colors of all items in the queue"""
        for i in range(self.listbox.size()):
            bg_color = '#f0f0f0' if i % 2 else 'white'
            self.listbox.itemconfigure(i, background=bg_color)


class ControlPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_controls()

    def setup_controls(self):
        self.add_button = tk.Button(self, text="+", **BUTTON_STYLE)
        self.prev_button = tk.Button(self, text="⏮", **BUTTON_STYLE)
        self.play_button = tk.Button(self, text="⏯", **BUTTON_STYLE)
        self.next_button = tk.Button(self, text="⏭", **BUTTON_STYLE)
        self.loop_button = tk.Button(self, text="⟳", **BUTTON_STYLE)

        buttons = [self.add_button, self.prev_button, self.play_button,
                  self.next_button, self.loop_button]

        for i, button in enumerate(buttons):
            button.grid(row=0, column=i, padx=8)


def show_file_dialog():
    action = filedialog.askdirectory(title="Select Music Directory")

    if action:
        path_obj = Path(action)
        if path_obj.is_dir():
            return find_audio_files(path_obj)

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

    return [str(Path(p)) for p in paths] if paths else []
