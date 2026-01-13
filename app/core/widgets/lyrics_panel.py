"""Lyrics display panel widget."""

import tkinter as tk
from tkinter import ttk


class LyricsPanel(tk.Frame):
    """Scrollable lyrics display panel.

    Displays song lyrics with title/artist header and handles loading/empty states.

    Attributes:
        title_label: Label showing song title
        artist_label: Label showing artist name
        lyrics_text: Scrolled text widget for lyrics content
        loading_label: Label shown during loading
        not_found_label: Label shown when lyrics not available
    """

    def __init__(self, parent):
        """Initialize lyrics panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, bg='#000000', relief=tk.FLAT, borderwidth=0)

        # Setup UI
        self.setup_ui()

        # Show empty state initially
        self.show_empty_state()

    def setup_ui(self):
        """Setup the UI components."""
        # Single text widget for lyrics ONLY (no header, no scrollbar)
        self.lyrics_text = tk.Text(
            self,
            wrap=tk.WORD,
            font=('Helvetica', 13),
            bg='#000000',
            fg='#CCCCCC',
            insertbackground='#CCCCCC',
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,  # Remove focus highlight border
            padx=20,
            pady=15,
            state=tk.DISABLED,  # Read-only by default
            cursor='arrow',  # Not editable
        )
        self.lyrics_text.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

        # Bind mouse wheel for scrolling (no visible scrollbar)
        self.lyrics_text.bind('<MouseWheel>', self._on_mousewheel)
        self.lyrics_text.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.lyrics_text.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        # Loading state label
        self.loading_label = tk.Label(
            self,
            text="Loading lyrics...",
            font=('Helvetica', 14),
            fg='#888888',
            bg='#000000',
            justify=tk.CENTER
        )

        # Not found state label
        self.not_found_label = tk.Label(
            self,
            text="Lyrics not available",
            font=('Helvetica', 14),
            fg='#888888',
            bg='#000000',
            justify=tk.CENTER
        )

    def show_lyrics(self, title: str, artist: str, lyrics: str):
        """Display ONLY lyrics text - no title, no artist.

        Args:
            title: Song title (not displayed)
            artist: Artist name (not displayed)
            lyrics: Lyrics text
        """
        # Hide state labels
        self.loading_label.pack_forget()
        self.not_found_label.pack_forget()

        # Show lyrics text widget
        self.lyrics_text.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

        # Update lyrics text - ONLY lyrics, nothing else
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete('1.0', tk.END)
        self.lyrics_text.insert('1.0', lyrics)
        self.lyrics_text.config(state=tk.DISABLED)

        # Scroll to top
        self.lyrics_text.see('1.0')

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling without visible scrollbar."""
        if event.num == 4 or event.delta > 0:
            # Scroll up
            self.lyrics_text.yview_scroll(-1, 'units')
        elif event.num == 5 or event.delta < 0:
            # Scroll down
            self.lyrics_text.yview_scroll(1, 'units')
        return 'break'  # Prevent event propagation

    def show_loading(self):
        """Show loading state."""
        # Hide other widgets
        self.lyrics_text.pack_forget()
        self.not_found_label.pack_forget()

        # Show loading label
        self.loading_label.pack(expand=True, fill=tk.BOTH)

    def show_not_found(self, title: str = "", artist: str = ""):
        """Show not found state.

        Args:
            title: Song title (ignored, kept for compatibility)
            artist: Artist name (ignored, kept for compatibility)
        """
        # Hide other widgets
        self.lyrics_text.pack_forget()
        self.loading_label.pack_forget()

        # Show not found label
        self.not_found_label.pack(expand=True, fill=tk.BOTH)

    def show_empty_state(self):
        """Show empty state (no track selected)."""
        # Hide all widgets
        self.lyrics_text.pack_forget()
        self.loading_label.pack_forget()
        self.not_found_label.pack_forget()

        # Empty state - nothing shown

    def clear(self):
        """Clear all content and show empty state."""
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete('1.0', tk.END)
        self.lyrics_text.config(state=tk.DISABLED)
        self.show_empty_state()
