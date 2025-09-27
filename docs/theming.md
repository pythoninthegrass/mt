# Theming and Styling System

## Overview

MT music player implements a comprehensive theming system based on `tkinter.ttk.Style` with JSON-configured color schemes and centralized style management. The system provides consistent visual appearance across all GUI components while supporting multiple theme variants.

## Architecture

### Theme Configuration Flow

```
themes.json → config.py → core/theme.py → GUI Components
     ↓              ↓              ↓              ↓
Theme Definitions → Runtime Config → Style Application → Visual Rendering
```

### Component Integration

The theming system integrates across multiple layers:

1. **Configuration Layer** (`config.py`): Theme loading and validation
2. **Style Layer** (`core/theme.py`): ttk.Style configuration and application  
3. **Component Layer** (`core/gui.py`): Theme-aware component creation
4. **Canvas Layer** (Custom controls): Direct color application for custom widgets

## Theme Definition (`themes.json`)

### Structure

```json
{
  "themes": [
    {
      "theme_name": {
        "type": "dark|light",
        "colors": {
          "primary": "#color_value",
          "secondary": "#color_value",
          ...
        }
      }
    }
  ]
}
```

### Color Palette Standard

Each theme defines a comprehensive color palette:

#### Core Colors

- **`primary`**: Accent color for active states, highlights, and branding
- **`secondary`**: Muted color for inactive states and subtle elements
- **`bg`**: Main background color for panels and containers
- **`fg`**: Primary text and foreground element color
- **`dark`**: Darker shade for depth and shadows
- **`light`**: Lighter shade for highlights and emphasis

#### Interactive States

- **`selectbg`**: Background color for selected items
- **`selectfg`**: Text color for selected items
- **`active`**: Color for active/hover states
- **`border`**: Color for borders and separators

#### Specialized Colors

- **`inputbg`/`inputfg`**: Form input field colors
- **`row_alt`**: Alternating row background in lists/trees
- **`progress_bg`**: Progress bar background
- **`playing_bg`/`playing_fg`**: Currently playing item indication

### Built-in Themes

#### Midnight Theme

```json
{
  "midnight": {
    "type": "dark",
    "colors": {
      "primary": "#0a21f5",     // Blue accent
      "bg": "#000000",          // Pure black background
      "fg": "#ffffff",          // White text
      "selectbg": "#454545",    // Gray selection
      ...
    }
  }
}
```

#### Spotify Theme

```json
{
  "spotify": {
    "type": "dark", 
    "colors": {
      "primary": "#1DB954",     // Spotify green
      "bg": "#0F0F0F",          // Near-black background
      "fg": "#C8C8C8",          // Light gray text
      "active": "#1DB954",      // Green accents
      ...
    }
  }
}
```

#### Metro Teal Theme

```json
{
  "metro-teal": {
    "type": "dark",
    "colors": {
      "primary": "#00b7c3",     // Teal accent
      "bg": "#202020",          // Dark gray background  
      "row_alt": "#242424",     // Subtle row alternation
      "playing_bg": "#00343a",  // Dark teal for playing items
      ...
    }
  }
}
```

## Style Application (`core/theme.py`)

### Setup Function

The `setup_theme(root)` function applies theme configuration:

```python
def setup_theme(root):
    style = ttk.Style()
    
    # Root window configuration
    root.configure(background=THEME_CONFIG['colors']['bg'])
    root.option_add('*Background', THEME_CONFIG['colors']['bg'])
    root.option_add('*Foreground', THEME_CONFIG['colors']['fg'])
```

### Widget Style Configuration

#### Standard ttk Widgets

```python
# Universal widget styling
for widget in ['TFrame', 'TPanedwindow', 'Treeview', 'TButton', 'TLabel']:
    style.configure(widget, 
                   background=THEME_CONFIG['colors']['bg'], 
                   fieldbackground=THEME_CONFIG['colors']['bg'])
```

#### Specialized Button Styles

```python
# Control-specific button styling
style.configure('Controls.TButton',
               background=THEME_CONFIG['colors']['bg'],
               foreground=THEME_CONFIG['colors']['fg'],
               borderwidth=0,
               relief='flat',
               font=BUTTON_STYLE['font'])

# Interactive state mapping
style.map('Controls.TButton',
         foreground=[('active', THEME_CONFIG['colors']['primary'])])
```

#### Treeview Styling

```python
# Main treeview configuration
style.configure('Treeview',
               background=THEME_CONFIG['colors']['bg'],
               foreground=THEME_CONFIG['colors']['fg'],
               fieldbackground=THEME_CONFIG['colors']['bg'])

# Selection and alternating row colors
style.map('Treeview',
         background=[
             ('selected', THEME_CONFIG['colors']['selectbg']),
             ('alternate', THEME_CONFIG['colors']['row_alt'])
         ])
```

#### Scrollbar Styling

```python
# Vertical scrollbar theming
style.configure('Vertical.TScrollbar',
               background=THEME_CONFIG['colors']['bg'],
               troughcolor=THEME_CONFIG['colors']['dark'],
               arrowcolor=THEME_CONFIG['colors']['fg'])
```

### Dynamic Configuration Updates

Theme application updates configuration objects:

```python
# Progress bar color updates
PROGRESS_BAR.update({
    'line_color': THEME_CONFIG['colors']['secondary'],
    'circle_fill': THEME_CONFIG['colors']['primary'],
    'circle_active_fill': THEME_CONFIG['colors']['active'],
})

# Global color dictionary updates
COLORS.update({
    'loop_enabled': THEME_CONFIG['colors']['primary'],
    'loop_disabled': THEME_CONFIG['colors']['secondary'],
})
```

## Configuration Integration (`config.py`)

### Theme Loading

```python
# Load theme configuration from JSON
def load_theme_config():
    with open('themes.json', 'r') as f:
        themes = json.load(f)
    
    # Select active theme (configurable)
    active_theme_name = config('ACTIVE_THEME', default='metro-teal')
    return get_theme_by_name(themes, active_theme_name)

THEME_CONFIG = load_theme_config()
```

### Configuration Constants

Theme-dependent configuration objects:

```python
# Button styling configuration
BUTTON_STYLE = {
    'font': ('SF Pro Display', 14, 'bold'),
    'relief': 'flat',
    'borderwidth': 0,
}

# Progress bar configuration with theme colors
PROGRESS_BAR = {
    'canvas_height': 80,
    'bar_y': 35,
    'circle_radius': 8,
    'line_width': 4,
    # Colors updated by theme system
    'line_color': None,       # Set by setup_theme()
    'circle_fill': None,      # Set by setup_theme()
    'progress_bg': '#404040', # Default fallback
}
```

## GUI Component Integration

### Library and Queue Views

#### Treeview Theme Application

```python
# Automatic theme application via ttk.Style
self.library_tree = ttk.Treeview(...)  # Inherits configured style

# Manual tag configuration for specialized states
self.queue.tag_configure('evenrow', 
                        background=THEME_CONFIG['colors']['bg'])
self.queue.tag_configure('oddrow', 
                        background=THEME_CONFIG['colors']['row_alt'])
```

### Custom Controls

#### Canvas-based Controls

Custom controls (progress bar, volume control) apply theme colors directly:

```python
# Progress line drawing with theme colors
self.canvas.create_line(
    x1, y1, x2, y2,
    fill=THEME_CONFIG['colors']['secondary'],
    width=PROGRESS_BAR['line_width']
)

# Progress position circle
self.canvas.create_oval(
    x1, y1, x2, y2,
    fill=THEME_CONFIG['colors']['primary'],
    outline=THEME_CONFIG['colors']['active']
)
```

#### Interactive State Colors

```python
# Hover effect implementation
def on_enter(event):
    button.configure(fg=THEME_CONFIG['colors']['primary'])

def on_leave(event):
    button.configure(fg=THEME_CONFIG['colors']['fg'])
```

## Platform-Specific Theming

### macOS Integration

```python
# macOS dark appearance support
if sys.platform == 'darwin':
    self.window.tk.call('::tk::unsupported::MacWindowStyle', 
                       'appearance', self.window._w, 'dark')
```

### Font Configuration

Platform-appropriate font selection:

```python
# macOS system fonts
BUTTON_STYLE['font'] = ('SF Pro Display', 14, 'bold')

# Cross-platform fallbacks
FONT_CONFIG = {
    'default': ('Helvetica', 12),
    'bold': ('Helvetica', 12, 'bold'),
    'small': ('Helvetica', 10),
}
```

## Runtime Theme Management

### Theme Switching

Future implementation for runtime theme changes:

```python
def change_theme(theme_name):
    # Load new theme configuration
    new_theme = load_theme_by_name(theme_name)
    
    # Update global configuration
    global THEME_CONFIG
    THEME_CONFIG = new_theme
    
    # Reapply theme to existing widgets
    setup_theme(root_window)
    
    # Refresh custom canvas elements
    refresh_custom_controls()
```

### Hot Reload Support

Development-time theme reloading:

```python
# File watcher for themes.json changes
def on_theme_file_change():
    reload_theme_configuration()
    apply_theme_to_all_widgets()
    redraw_custom_elements()
```

## Custom Widget Theming

### Progress Control Theming

```python
class ProgressControl:
    def apply_theme(self):
        # Update line colors
        self.canvas.itemconfig(self.line, 
                              fill=THEME_CONFIG['colors']['secondary'])
        self.canvas.itemconfig(self.progress_line, 
                              fill=THEME_CONFIG['colors']['primary'])
        
        # Update circle colors
        self.canvas.itemconfig(self.progress_circle,
                              fill=THEME_CONFIG['colors']['primary'],
                              outline=THEME_CONFIG['colors']['active'])
```

### Volume Control Theming

```python
class VolumeControl:
    def setup_volume_control(self):
        # Icon color based on volume state
        icon_color = (THEME_CONFIG['colors']['secondary'] 
                     if self.volume == 0 
                     else THEME_CONFIG['colors']['fg'])
        
        # Slider background/foreground
        bg_color = THEME_CONFIG['colors']['dark']
        fg_color = THEME_CONFIG['colors']['primary']
```

## Theming Best Practices

### Color Consistency

1. **Use Semantic Colors**: Reference colors by semantic meaning (primary, secondary) rather than specific values
2. **State Indication**: Consistent color usage for interactive states across components
3. **Accessibility**: Ensure sufficient contrast ratios for text readability
4. **Platform Integration**: Respect platform-specific appearance preferences

### Performance Considerations

1. **Single Theme Application**: Apply theme once during application startup
2. **Minimal Redraws**: Only update changed elements during theme switches
3. **Cached Color Values**: Store frequently-used colors in variables
4. **Efficient Canvas Updates**: Batch canvas item configuration changes

### Maintenance Guidelines

1. **Centralized Color Definitions**: All colors defined in themes.json
2. **Consistent Naming**: Standardized color property names across themes
3. **Documentation**: Comments explaining color usage and relationships
4. **Validation**: Theme validation to ensure all required colors are defined

## Future Enhancements

### Planned Features

1. **Light Theme Support**: Additional light-mode color schemes
2. **User Theme Creation**: Interface for custom theme creation
3. **Theme Import/Export**: Sharing themes between installations
4. **Automatic Dark Mode**: System appearance detection and switching
5. **Component-Specific Themes**: Per-component color overrides
6. **Animation Support**: Smooth theme transition animations

### Technical Improvements

1. **CSS-like Styling**: More sophisticated style cascade system
2. **Theme Inheritance**: Base themes with variant overrides
3. **Conditional Styling**: Platform or state-dependent style rules
4. **Performance Optimization**: Reduced memory footprint for theme data
5. **Live Preview**: Real-time theme editing with immediate feedback

This theming system provides a solid foundation for visual customization while maintaining consistency and performance across the application's user interface.
