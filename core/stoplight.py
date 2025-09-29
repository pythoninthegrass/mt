"""
Custom macOS-style stoplight buttons for borderless window.
Provides close, minimize, and maximize functionality with native-looking styling.
"""

import tkinter as tk
from tkinter import ttk


class StoplightButtons:
    """Custom macOS-style stoplight buttons for window control."""

    def __init__(self, parent_window, container, integrated=False):
        self.window = parent_window
        self.container = container
        self.integrated = integrated
        self.is_maximized = False
        self.is_minimized = False
        self.pre_maximize_geometry = None
        
        # macOS stoplight button colors - lighter gray for better visibility
        self.colors = {
            'close': {'normal': '#808080', 'hover': '#ff5f56'},
            'minimize': {'normal': '#808080', 'hover': '#ffbd2e'},
            'maximize': {'normal': '#808080', 'hover': '#27ca3f'},
            'inactive': '#808080'
        }
        
        self.setup_stoplight_buttons()

    def setup_stoplight_buttons(self):
        """Create and position the stoplight buttons."""
        if self.integrated:
            # When integrated, use the existing container directly
            self.stoplight_frame = self.container
        else:
            # Create frame for stoplight buttons
            self.stoplight_frame = tk.Frame(
                self.container,
                bg="#000000",  # Black background to match theme
                height=40  # Match search bar height
            )
            self.stoplight_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
            self.stoplight_frame.pack_propagate(False)

        # Create canvas for circular buttons with proper macOS positioning
        button_size = 14  # Slightly larger for better visibility
        button_spacing = 8  # Tighter spacing like macOS
        left_margin = 12     # Margin from edge
        top_margin = 13  # Centered in 40px height frame (40-14)/2 = 13
        
        self.canvas = tk.Canvas(
            self.stoplight_frame,
            width=left_margin + (button_size + button_spacing) * 3,
            height=40,  # Match search bar height
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, padx=0, pady=0)

        # Close button (starts as lighter gray, turns red on hover)
        self.close_circle = self.canvas.create_oval(
            left_margin, top_margin,
            left_margin + button_size, top_margin + button_size,
            fill=self.colors['close']['normal'],
            outline=""
        )
        
        # Minimize button (starts as lighter gray, turns yellow on hover)
        minimize_x = left_margin + button_size + button_spacing
        self.minimize_circle = self.canvas.create_oval(
            minimize_x, top_margin,
            minimize_x + button_size, top_margin + button_size,
            fill=self.colors['minimize']['normal'],
            outline=""
        )
        
        # Maximize button (starts as lighter gray, turns green on hover)
        maximize_x = left_margin + (button_size + button_spacing) * 2
        self.maximize_circle = self.canvas.create_oval(
            maximize_x, top_margin,
            maximize_x + button_size, top_margin + button_size,
            fill=self.colors['maximize']['normal'],
            outline=""
        )

        # Bind events to canvas
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Motion>", self.handle_motion)
        self.canvas.bind("<Leave>", self.handle_leave)

        # No longer need window event handlers for minimize/restore

        # Make the canvas draggable for window movement (not the frame in integrated mode)
        self.make_draggable()

    def handle_click(self, event):
        """Handle clicks on the canvas to determine which button was clicked."""
        x, y = event.x, event.y
        button_size = 14
        button_spacing = 8
        left_margin = 12
        top_margin = 13  # Updated to match setup
        
        # Check close button
        if (left_margin <= x <= left_margin + button_size and 
            top_margin <= y <= top_margin + button_size):
            self.close_window()
        # Check minimize button
        elif (left_margin + button_size + button_spacing <= x <= left_margin + button_size + button_spacing + button_size and 
              top_margin <= y <= top_margin + button_size):
            self.minimize_window()
        # Check maximize button
        elif (left_margin + (button_size + button_spacing) * 2 <= x <= left_margin + (button_size + button_spacing) * 2 + button_size and 
              top_margin <= y <= top_margin + button_size):
            self.toggle_maximize()

    def handle_motion(self, event):
        """Handle mouse motion for hover effects."""
        x, y = event.x, event.y
        button_size = 14
        button_spacing = 8
        left_margin = 12
        top_margin = 13  # Updated to match setup
        
        # Reset all buttons to normal color first
        self.canvas.itemconfig(self.close_circle, fill=self.colors['close']['normal'])
        self.canvas.itemconfig(self.minimize_circle, fill=self.colors['minimize']['normal'])
        self.canvas.itemconfig(self.maximize_circle, fill=self.colors['maximize']['normal'])
        
        # Check which button is being hovered
        if (left_margin <= x <= left_margin + button_size and 
            top_margin <= y <= top_margin + button_size):
            self.canvas.itemconfig(self.close_circle, fill=self.colors['close']['hover'])
            self.canvas.configure(cursor="hand2")
        elif (left_margin + button_size + button_spacing <= x <= left_margin + button_size + button_spacing + button_size and 
              top_margin <= y <= top_margin + button_size):
            # Minimize is disabled - don't show hover effect or cursor change
            pass
        elif (left_margin + (button_size + button_spacing) * 2 <= x <= left_margin + (button_size + button_spacing) * 2 + button_size and 
              top_margin <= y <= top_margin + button_size):
            self.canvas.itemconfig(self.maximize_circle, fill=self.colors['maximize']['hover'])
            self.canvas.configure(cursor="hand2")
        else:
            self.canvas.configure(cursor="")

    def handle_leave(self, event):
        """Handle mouse leaving the canvas."""
        # Reset all buttons to normal color
        self.canvas.itemconfig(self.close_circle, fill=self.colors['close']['normal'])
        self.canvas.itemconfig(self.minimize_circle, fill=self.colors['minimize']['normal'])
        self.canvas.itemconfig(self.maximize_circle, fill=self.colors['maximize']['normal'])
        self.canvas.configure(cursor="")

    def make_draggable(self):
        """Make the stoplight area draggable to move the window."""
        def start_drag(event):
            # Only start drag if not clicking on a button
            x, y = event.x, event.y
            button_size = 14
            button_spacing = 8
            left_margin = 12
            top_margin = 13
            
            # Check if click is on any button area
            button_areas = [
                (left_margin, top_margin, left_margin + button_size, top_margin + button_size),
                (left_margin + button_size + button_spacing, top_margin, left_margin + button_size + button_spacing + button_size, top_margin + button_size),
                (left_margin + (button_size + button_spacing) * 2, top_margin, left_margin + (button_size + button_spacing) * 2 + button_size, top_margin + button_size)
            ]
            
            for x1, y1, x2, y2 in button_areas:
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return  # Don't start drag if clicking on a button
            
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            self.window_start_x = self.window.winfo_x()
            self.window_start_y = self.window.winfo_y()

        def drag_window(event):
            if hasattr(self, 'drag_start_x'):
                delta_x = event.x_root - self.drag_start_x
                delta_y = event.y_root - self.drag_start_y
                new_x = self.window_start_x + delta_x
                new_y = self.window_start_y + delta_y
                self.window.geometry(f"+{new_x}+{new_y}")

        # Bind drag events to the canvas in integrated mode, or to the frame in standalone mode
        if self.integrated:
            self.canvas.bind("<Button-1>", start_drag, add='+')  # Add to existing bindings
            self.canvas.bind("<B1-Motion>", drag_window)
        else:
            self.stoplight_frame.bind("<Button-1>", start_drag)
            self.stoplight_frame.bind("<B1-Motion>", drag_window)

    def close_window(self, event=None):
        """Handle close button click."""
        # Call the window's close method if it exists, otherwise destroy
        if hasattr(self.window, 'on_window_close'):
            self.window.on_window_close()
        else:
            self.window.destroy()

    def minimize_window(self, event=None):
        """Handle minimize button click - disabled for borderless windows."""
        # Minimize doesn't work properly with overrideredirect(True)
        # The window can't be restored from dock/taskbar
        # For now, minimize is disabled - could implement system tray instead
        pass

    def toggle_maximize(self, event=None):
        """Handle maximize/restore button click."""
        if self.is_maximized:
            # Restore to previous size
            if self.pre_maximize_geometry:
                self.window.geometry(self.pre_maximize_geometry)
                self.window.wm_state('normal')
            self.is_maximized = False
        else:
            # Store current geometry before maximizing
            self.pre_maximize_geometry = self.window.geometry()
            
            # Get screen dimensions
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # On macOS, get the actual usable screen area
            try:
                # Try to get actual screen dimensions using Cocoa
                import Cocoa
                main_screen = Cocoa.NSScreen.mainScreen()
                visible_frame = main_screen.visibleFrame()
                
                # Cocoa uses bottom-left origin, so convert coordinates
                usable_x = int(visible_frame.origin.x)
                usable_y = int(screen_height - visible_frame.origin.y - visible_frame.size.height)
                usable_width = int(visible_frame.size.width)
                usable_height = int(visible_frame.size.height)
                
                # Position window to fill actual usable screen space
                self.window.geometry(f"{usable_width}x{usable_height}+{usable_x}+{usable_y}")
            except ImportError:
                # Fallback: use estimates if Cocoa isn't available
                menu_bar_height = 24
                dock_height = 80
                usable_height = screen_height - menu_bar_height - dock_height
                self.window.geometry(f"{screen_width}x{usable_height}+0+{menu_bar_height}")
            
            self.is_maximized = True

    def restore_window(self):
        """Restore the window from hidden state."""
        if self.is_minimized:
            self.window.deiconify()
            self.is_minimized = False

    def get_title_bar_height(self):
        """Return the height of the stoplight buttons area."""
        return 40