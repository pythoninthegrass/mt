"""Scrollable frame widget for Now Playing view."""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget using Canvas.

    Attributes:
        scrollable_frame: The inner frame that contains the content
        canvas: The canvas widget that enables scrolling
        scrollbar: The vertical scrollbar
    """

    def __init__(self, parent, *args, **kwargs):
        """Initialize the scrollable frame.

        Args:
            parent: Parent widget
            *args: Additional positional arguments for Frame
            **kwargs: Additional keyword arguments for Frame
        """
        super().__init__(parent, *args, **kwargs)

        # Create canvas with scrollbar
        self.canvas = tk.Canvas(self, bg='#202020', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Bind frame resize to update scroll region
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create window in canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Enable mouse wheel scrolling on canvas
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)

        # Bind canvas resize to update frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update frame width.

        Args:
            event: Configure event
        """
        # Update the width of the frame to match canvas width
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_enter(self, event):
        """Bind mouse wheel when mouse enters canvas area.

        Args:
            event: Enter event
        """
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_leave(self, event):
        """Unbind mouse wheel when mouse leaves canvas area.

        Args:
            event: Leave event
        """
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _bind_children_mousewheel(self, event=None):
        """No longer needed - keeping for compatibility."""
        pass

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling.

        Args:
            event: Mouse wheel event
        """
        # Different platforms report scroll differently
        if hasattr(event, 'num'):
            if event.num == 4:  # Linux scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                self.canvas.yview_scroll(1, "units")
        elif hasattr(event, 'delta'):  # Windows/macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_to_widget(self, widget):
        """Scroll to make a specific widget visible.

        Args:
            widget: Widget to scroll to
        """
        # Get widget position relative to canvas
        try:
            widget.update_idletasks()
            x, y, width, height = self.canvas.bbox(self.canvas_frame)
            widget_y = widget.winfo_y()

            # Calculate scroll position to center widget
            canvas_height = self.canvas.winfo_height()
            scroll_pos = (widget_y - canvas_height / 2) / height

            self.canvas.yview_moveto(max(0, min(1, scroll_pos)))
        except tk.TclError:
            # Widget might not be visible yet
            pass

    def destroy(self):
        """Clean up bindings before destroying."""
        # Unbind global mouse wheel events
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
        super().destroy()
