# HTMX Base Templates

This directory contains the foundational HTMX templates and partials for the mt music player web interface, designed to match the MusicBee-inspired UI.

## Structure

```
templates/
├── base/
│   └── base.html              # Main application layout with three-panel design
├── components/
│   ├── navbar.html            # Top navigation bar with search and user menu
│   ├── sidebar.html           # Left sidebar with library navigation and playlists
│   ├── player-controls.html   # Bottom player controls with progress and volume
│   └── queue.html             # Right panel queue management
├── pages/
│   └── library.html           # Library view page extending base template
└── partials/
    ├── modal.html             # Reusable modal dialog template
    ├── toast.html             # Toast notification template
    └── track-item.html        # Individual track item component
```

## Features

### Three-Panel Layout
- **Left Sidebar**: Library navigation, playlists, and library statistics
- **Center Panel**: Main content area with HTMX-powered dynamic loading
- **Right Panel**: Queue management with drag-and-drop reordering

### UI Components
- **Navigation**: Responsive navbar with search, theme toggle, and user menu
- **Player Controls**: Full-featured audio controls with progress bar and volume
- **Queue Management**: Interactive queue with drag-and-drop, history, and suggestions
- **Modals**: Flexible modal system for dialogs and forms
- **Toast Notifications**: Non-intrusive notification system

### Design System
- **Basecoat UI**: Custom design system with dark theme
- **Tailwind CSS**: Utility-first CSS framework
- **Inter Font**: Modern, readable typography
- **Bootstrap Icons**: Consistent iconography

### HTMX Integration
- **Dynamic Content Loading**: Seamless page updates without full reloads
- **WebSocket Support**: Real-time updates via Server-Sent Events
- **Form Handling**: Progressive enhancement with HTMX
- **Loading States**: Built-in loading indicators and transitions

### Alpine.js Enhancements
- **Reactive UI**: State management for interactive components
- **Transitions**: Smooth animations and micro-interactions
- **Keyboard Shortcuts**: Global keyboard navigation
- **Drag & Drop**: Native drag-and-drop for queue management

## Dependencies

### Frontend
- **HTMX 1.9.10**: For dynamic content and interactions
- **Alpine.js 3.13.5**: For reactive UI components
- **Tailwind CSS**: For styling and layout
- **Inter Font**: For typography
- **Bootstrap Icons**: For icons

### Backend Requirements
The templates expect the following backend endpoints:

#### Player API
- `POST /api/player/toggle` - Toggle play/pause
- `POST /api/player/next` - Next track
- `POST /api/player/previous` - Previous track
- `POST /api/player/seek` - Seek to position
- `POST /api/player/volume` - Set volume
- `POST /api/player/mute` - Toggle mute
- `POST /api/player/shuffle` - Toggle shuffle
- `POST /api/player/repeat` - Cycle repeat mode

#### Queue API
- `GET /api/queue/tracks` - Get queue tracks
- `POST /api/queue/add/{track_id}` - Add track to queue
- `POST /api/queue/reorder` - Reorder queue items
- `POST /api/queue/clear` - Clear queue
- `POST /api/queue/shuffle` - Shuffle queue

#### Library API
- `GET /api/library/tracks` - Get library tracks
- `GET /api/library/stats` - Get library statistics
- `POST /api/library/scan` - Scan for new music

#### Search API
- `GET /api/search?q={query}` - Search tracks

## Template Filters

Custom Jinja2 filters are provided in `filters.py`:

- `format_duration(seconds)` - Format seconds to MM:SS
- `format_file_size(bytes)` - Format bytes to human readable
- `pluralize(count, singular, plural)` - Pluralize words

## Usage

### Extending Base Template

```html
{% extends "base/base.html" %}

{% block title %}Page Title - mt music player{% endblock %}

{% block content %}
<!-- Your page content here -->
{% endblock %}
```

### Including Partials

```html
{% include "partials/modal.html" %}
{% include "components/navbar.html" %}
```

### HTMX Patterns

```html
<!-- Dynamic content loading -->
<div hx-get="/api/data" hx-trigger="load" hx-swap="innerHTML">
  Loading...
</div>

<!-- Form submission -->
<form hx-post="/api/submit" hx-swap="innerHTML" hx-target="#result">
  <input name="query" type="search">
  <button type="submit">Search</button>
</form>

<!-- Click actions -->
<button hx-post="/api/action" hx-swap="none">
  Perform Action
</button>
```

## Customization

### Theme Variables
CSS custom properties are defined in `static/css/main.css`:

```css
:root {
  --bg-primary: #030712;
  --bg-secondary: #111827;
  --text-primary: #f3f4f6;
  --accent-blue: #3b82f6;
  /* ... */
}
```

### Responsive Design
Templates include responsive breakpoints:
- Mobile: < 640px
- Tablet: 640px - 768px
- Desktop: > 768px

### Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Screen reader friendly
- Focus management in modals

## Development

### File Organization
- Keep templates modular and reusable
- Use consistent naming conventions
- Document template variables and blocks
- Include loading states for dynamic content

### Performance
- Minimize CSS and JavaScript bundle size
- Use HTMX for efficient content updates
- Implement lazy loading for large lists
- Cache static assets appropriately

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires modern browser features like CSS Grid, Flexbox, and ES6 modules.