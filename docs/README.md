# MT Music Player Documentation

This directory contains comprehensive documentation for the MT music player project.

## Documentation Structure

- [**Python Architecture**](python-architecture.md) - Core Python modules and their interactions
- [**Zig Modules**](zig-modules.md) - High-performance Zig extensions and FFI integration
- [**GUI Implementation**](tkinter-gui.md) - Tkinter-based user interface design and components
- [**Theming System**](theming.md) - Theme configuration, styling, and visual customization
- [**VLC Integration**](vlc-integration.md) - Audio playback engine integration and media controls
- [**API Server**](api.md) - Programmatic control interface for LLMs and automation
- [**Custom Playlists**](custom-playlists.md) - Implementation plan for user-created playlists
- [**Current Status**](status.md) - Implementation progress, outstanding tasks, and known issues
- [**Web Migration Guide**](web-migration.md) - Strategy for porting to FastAPI/Flask web application
- [**Tauri Architecture**](tauri-architecture.md) - Target architecture for Tauri migration (Rust audio, Python sidecar, Alpine.js frontend)

## Quick Start

For immediate understanding of the codebase:

1. Start with [Python Architecture](python-architecture.md) for overall system design
2. Review [Current Status](status.md) for what's implemented and what's planned
3. Check [VLC Integration](vlc-integration.md) for audio playback details

## Development Context

This documentation is generated from analysis of:

- Source code in `core/`, `src/`, `utils/` directories
- Configuration files (`config.py`, `themes.json`, `pyproject.toml`)
- Task management (`backlog/`, `TODO.md`)
- Development guidance (`AGENTS.md`)
- Test specifications (`tests/`)

Each document provides both current implementation details and future development considerations.
