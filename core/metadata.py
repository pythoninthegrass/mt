import customtkinter as ctk
import tkinter as tk
from mutagen import File, MutagenError
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4


class MetadataEditor(ctk.CTkToplevel):
    def __init__(self, parent, file_paths, on_save_callback, navigation_callback=None, has_prev=False, has_next=False):
        super().__init__(parent)
        # Support both single file and multiple files
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        self.file_paths = file_paths
        self.file_path = file_paths[0]  # For compatibility
        self.on_save_callback = on_save_callback
        self.navigation_callback = navigation_callback
        self.has_prev = has_prev
        self.has_next = has_next
        self.is_batch = len(file_paths) > 1

        if self.is_batch:
            self.title(f"Edit Tag - {len(file_paths)} files")
        else:
            self.title(f"Edit Tag - {file_paths[0].split('/')[-1]}")
        self.geometry("450x600")

        # Load all audio files for batch editing
        self.audio_files = []
        for fp in self.file_paths:
            audio = self.load_metadata_from_path(fp)
            if audio:
                self.audio_files.append((fp, audio))

        if not self.audio_files:
            self.destroy()
            return

        self.audio = self.audio_files[0][1]  # For compatibility

        self.entries = {}
        self.create_widgets()
        self.populate_fields()

    def load_metadata(self):
        """Load metadata from the first file (for compatibility)."""
        return self.load_metadata_from_path(self.file_path)

    def load_metadata_from_path(self, file_path):
        """Load metadata from a specific file path."""
        try:
            audio = File(file_path)
            if audio is None:
                return None
            return audio
        except Exception as e:
            print(f"Error loading metadata from {file_path}: {e}")
            return None

    def get_tag_value(self, key):
        """Get tag value handling different formats."""
        if isinstance(self.audio, MP4):
            mp4_key_map = {
                "title": "\xa9nam",
                "artist": "\xa9ART",
                "album": "\xa9alb",
                "genre": "\xa9gen",
                "year": "\xa9day",
                "album_artist": "aART",
                "composer": "\xa9wrt",
                "track_number": "trkn",
                "disc_number": "disk",
                "comment": "\xa9cmt",
            }
            mp4_key = mp4_key_map.get(key)
            if mp4_key and mp4_key in self.audio:
                value = self.audio[mp4_key]
                if isinstance(value, list) and value:
                    val = value[0]
                    # Handle track/disc number tuples (track, total)
                    if isinstance(val, tuple):
                        return f"{val[0]}/{val[1]}" if val[1] > 0 else str(val[0])
                    # Handle year field - extract just the year from ISO date strings
                    if key == "year" and isinstance(val, str):
                        # Extract year from formats like "2012-02-10T08:00:00Z" or "2012"
                        return val.split('-')[0] if '-' in val else val
                    return str(val)
            return ""
        elif isinstance(self.audio, FLAC):
            # FLAC uses VorbisComment - simple string key/value pairs
            vorbis_key_map = {
                "title": "title",
                "artist": "artist",
                "album": "album",
                "genre": "genre",
                "year": "date",  # VorbisComment uses 'date' not 'year'
                "album_artist": "albumartist",
                "composer": "composer",
                "track_number": "tracknumber",
                "disc_number": "discnumber",
                "comment": "comment",
            }
            vorbis_key = vorbis_key_map.get(key)
            if vorbis_key and vorbis_key in self.audio:
                value = self.audio[vorbis_key]
                if isinstance(value, list) and value:
                    return str(value[0])
                return str(value)
            return ""
        else:
            # ID3 tags (MP3, etc.)
            easy_key_map = {
                "title": "TIT2",
                "artist": "TPE1",
                "album": "TALB",
                "genre": "TCON",
                "year": "TDRC",
                "album_artist": "TPE2",
                "composer": "TCOM",
                "track_number": "TRCK",
                "disc_number": "TPOS",
                "comment": "COMM::eng",
            }
            tag_key = easy_key_map.get(key)
            if tag_key and tag_key in self.audio:
                value = self.audio[tag_key]
                if hasattr(value, 'text'):
                    return str(value.text[0]) if value.text else ""
                elif isinstance(value, list) and value:
                    return str(value[0])
                return str(value)
            return ""

    def set_tag_value(self, key, value):
        """Set tag value handling different formats."""
        if isinstance(self.audio, MP4):
            mp4_key_map = {
                "title": "\xa9nam",
                "artist": "\xa9ART",
                "album": "\xa9alb",
                "genre": "\xa9gen",
                "year": "\xa9day",
                "album_artist": "aART",
                "composer": "\xa9wrt",
                "track_number": "trkn",
                "disc_number": "disk",
                "comment": "\xa9cmt",
            }
            mp4_key = mp4_key_map.get(key)
            if mp4_key:
                if value:
                    if key in ("track_number", "disc_number"):
                        try:
                            parts = value.split('/')
                            track_num = int(parts[0])
                            total = int(parts[1]) if len(parts) > 1 else 0
                            self.audio[mp4_key] = [(track_num, total)]
                        except (ValueError, IndexError):
                            try:
                                self.audio[mp4_key] = [(int(value), 0)]
                            except ValueError:
                                pass
                    else:
                        self.audio[mp4_key] = [value]
                elif mp4_key in self.audio:
                    del self.audio[mp4_key]
        elif isinstance(self.audio, FLAC):
            # FLAC uses VorbisComment - simple string key/value pairs
            vorbis_key_map = {
                "title": "title",
                "artist": "artist",
                "album": "album",
                "genre": "genre",
                "year": "date",  # VorbisComment uses 'date' not 'year'
                "album_artist": "albumartist",
                "composer": "composer",
                "track_number": "tracknumber",
                "disc_number": "discnumber",
                "comment": "comment",
            }
            vorbis_key = vorbis_key_map.get(key)
            if vorbis_key:
                if value:
                    self.audio[vorbis_key] = value
                elif vorbis_key in self.audio:
                    del self.audio[vorbis_key]
        else:
            # ID3 tags (MP3, etc.)
            from mutagen.id3 import COMM, TALB, TCOM, TCON, TDRC, TIT2, TPE1, TPE2, TPOS, TRCK

            tag_class_map = {
                "title": TIT2,
                "artist": TPE1,
                "album": TALB,
                "genre": TCON,
                "year": TDRC,
                "album_artist": TPE2,
                "composer": TCOM,
                "track_number": TRCK,
                "disc_number": TPOS,
            }
            if key == "comment":
                if value:
                    self.audio["COMM::eng"] = COMM(encoding=3, lang='eng', desc='', text=value)
                elif "COMM::eng" in self.audio:
                    del self.audio["COMM::eng"]
            else:
                tag_class = tag_class_map.get(key)
                if tag_class:
                    tag_key = tag_class.__name__
                    if value:
                        self.audio[tag_key] = tag_class(encoding=3, text=value)
                    elif tag_key in self.audio:
                        del self.audio[tag_key]

    def create_widgets(self):
        from config import THEME_CONFIG
        
        frame = ctk.CTkFrame(self)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Configure grid column to expand
        frame.grid_columnconfigure(1, weight=1)

        # Editable fields
        fields = [
            "Title",
            "Artist",
            "Album",
            "Genre",
            "Year",
            "Album Artist",
            "Composer",
            "Track #",
            "Disc #",
            "Comment",
        ]

        for i, field in enumerate(fields):
            label = ctk.CTkLabel(frame, text=field)
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            entry = ctk.CTkEntry(frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.entries[field.lower().replace(" ", "_").replace("#", "number")] = entry

        # Add read-only File Name field at the bottom (after all editable fields)
        file_label = ctk.CTkLabel(frame, text="File Name")
        file_label.grid(row=len(fields), column=0, padx=5, pady=5, sticky="w")

        file_entry = ctk.CTkEntry(frame, text_color="#888888")
        file_entry.grid(row=len(fields), column=1, padx=5, pady=5, sticky="ew")

        # Show appropriate text based on mode
        if self.is_batch:
            file_entry.insert(0, f"<{len(self.file_paths)} files selected>")
        else:
            file_entry.insert(0, self.file_path)

        # Make it read-only by preventing modifications while allowing cursor movement
        def readonly_keypress(event):
            # Allow navigation keys
            if event.keysym in ('Left', 'Right', 'Home', 'End', 'Up', 'Down'):
                return None  # Allow these keys
            # Allow selection keys
            if event.state & 0x0001 and event.keysym in ('Left', 'Right', 'Home', 'End', 'a', 'A'):
                return None  # Allow Shift+navigation and Ctrl/Cmd+A
            # Block all other keys (typing, delete, backspace, etc.)
            return "break"

        file_entry.bind("<Key>", readonly_keypress)
        self.entries["file_name"] = file_entry

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(padx=10, pady=10, fill="x")

        # Get theme colors
        primary_color = THEME_CONFIG['colors']['primary']

        # Navigation buttons on the left
        if self.navigation_callback:
            prev_button = ctk.CTkButton(
                button_frame,
                text="←",
                command=lambda: self.navigate_track(-1),
                width=40,
                fg_color=primary_color,
                hover_color=primary_color,
                text_color="#ffffff",
                state="normal" if self.has_prev else "disabled"
            )
            prev_button.pack(side="left", padx=5)

            next_button = ctk.CTkButton(
                button_frame,
                text="→",
                command=lambda: self.navigate_track(1),
                width=40,
                fg_color=primary_color,
                hover_color=primary_color,
                text_color="#ffffff",
                state="normal" if self.has_next else "disabled"
            )
            next_button.pack(side="left", padx=5)

        # Action buttons on the right
        apply_button = ctk.CTkButton(
            button_frame,
            text="Apply",
            command=self.save_metadata,
            fg_color=primary_color,
            hover_color=primary_color,
            text_color="#ffffff"
        )
        apply_button.pack(side="right", padx=5)

        close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            fg_color=primary_color,
            hover_color=primary_color,
            text_color="#ffffff"
        )
        close_button.pack(side="right", padx=5)

    def populate_fields(self):
        field_map = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "genre": "genre",
            "year": "year",
            "album_artist": "album_artist",
            "composer": "composer",
            "track_number": "track_number",
            "disc_number": "disc_number",
            "comment": "comment",
        }

        if self.is_batch:
            # For batch editing, check if values are shared across all files
            for field, key in field_map.items():
                values = []
                for filepath, audio in self.audio_files:
                    # Temporarily set self.audio to get the value
                    self.audio = audio
                    value = self.get_tag_value(key)
                    values.append(value)

                # Check if all values are the same
                unique_values = set(values)
                if len(unique_values) == 1 and values[0]:
                    # All files have the same value - show it
                    self.entries[field].delete(0, tk.END)
                    self.entries[field].insert(0, values[0])
                else:
                    # Different values or empty - show placeholder
                    self.entries[field].delete(0, tk.END)
                    # Store placeholder state
                    if not hasattr(self, '_placeholders'):
                        self._placeholders = {}
                    self._placeholders[field] = True

                    # Configure placeholder appearance
                    self.entries[field].configure(text_color="#666666")
                    placeholder_text = "<Multiple values>" if any(values) else ""
                    self.entries[field].insert(0, placeholder_text)

                    # Bind events to clear placeholder on focus/type
                    self.entries[field].bind("<FocusIn>", lambda e, f=field: self._clear_placeholder(f))
                    self.entries[field].bind("<Key>", lambda e, f=field: self._on_key_with_placeholder(e, f))

            # Restore self.audio
            self.audio = self.audio_files[0][1]
        else:
            # Single file editing
            for field, key in field_map.items():
                value = self.get_tag_value(key)
                if value:
                    self.entries[field].delete(0, tk.END)
                    self.entries[field].insert(0, value)

    def _clear_placeholder(self, field):
        """Clear placeholder text when field receives focus."""
        if hasattr(self, '_placeholders') and self._placeholders.get(field):
            self.entries[field].delete(0, tk.END)
            self.entries[field].configure(text_color="#FFFFFF")
            self._placeholders[field] = False

    def _on_key_with_placeholder(self, event, field):
        """Handle key press when placeholder is shown."""
        if hasattr(self, '_placeholders') and self._placeholders.get(field):
            self._clear_placeholder(field)

    def save_metadata(self):
        field_map = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "genre": "genre",
            "year": "year",
            "album_artist": "album_artist",
            "composer": "composer",
            "track_number": "track_number",
            "disc_number": "disc_number",
            "comment": "comment",
        }

        if self.is_batch:
            # Batch editing: apply changes to all files
            for filepath, audio in self.audio_files:
                # Temporarily set self.audio to this file's audio object
                self.audio = audio
                
                # Apply all field values (skip placeholders)
                for field, key in field_map.items():
                    value = self.entries[field].get().strip()
                    # Skip if this field still has placeholder text
                    if hasattr(self, '_placeholders') and self._placeholders.get(field):
                        continue
                    self.set_tag_value(key, value)
                
                try:
                    self.audio.save()
                    if self.on_save_callback:
                        self.on_save_callback(filepath)
                except Exception as e:
                    print(f"Error saving metadata for {filepath}: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            # Single file editing
            for field, key in field_map.items():
                value = self.entries[field].get().strip()
                self.set_tag_value(key, value)

            try:
                self.audio.save()
                if self.on_save_callback:
                    self.on_save_callback(self.file_path)
            except Exception as e:
                print(f"Error saving metadata: {e}")
                import traceback
                traceback.print_exc()

        self.destroy()

    def navigate_track(self, direction):
        """Navigate to previous (-1) or next (1) track."""
        if self.navigation_callback:
            # Get new file path from callback
            new_file_path, has_prev, has_next = self.navigation_callback(self.file_path, direction)
            if new_file_path:
                # Update current file path
                self.file_path = new_file_path
                self.has_prev = has_prev
                self.has_next = has_next

                # Reload metadata
                self.audio = self.load_metadata()
                if self.audio:
                    # Update window title
                    self.title(f"Edit Tag - {self.file_path.split('/')[-1]}")

                    # Clear and repopulate all fields
                    for entry in self.entries.values():
                        if entry.cget("state") != "disabled":  # Skip disabled fields
                            entry.delete(0, tk.END)

                    # Update file name field
                    self.entries["file_name"].configure(state="normal")
                    self.entries["file_name"].delete(0, tk.END)
                    self.entries["file_name"].insert(0, self.file_path)
                    self.entries["file_name"].configure(state="readonly")

                    # Populate metadata fields
                    self.populate_fields()

                    # Update navigation button states
                    self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update navigation button states based on has_prev/has_next."""
        # Find the navigation buttons in button_frame
        for widget in self.children.values():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton):
                        if child.cget("text") == "←":
                            child.configure(state="normal" if self.has_prev else "disabled")
                        elif child.cget("text") == "→":
                            child.configure(state="normal" if self.has_next else "disabled")
