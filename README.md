# mt

`mt` is a simple desktop music player designed for large music collections.

![mt](static/cover.png)

## Minimum Requirements

* macOS/Linux
* [Python 3.11+](https://www.python.org/downloads/release/python-31111/)
* [VLC](https://www.videolan.org/vlc/index.html)

## Setup

```bash
# install vlc
## macos
brew install --cask vlc

## TODO: qa ubuntu/wsl
## linux

# create virtual environment
python -m venv .venv

# activate virtual environment
source .venv/bin/activate

# install dependencies
python -m pip install -r requirements.txt

# run the app
python main.py
```

## Development

### Auto-Reload Utility

The `repeater` script provides automatic reloading for Tkinter applications during development, extending tkreload functionality to watch multiple files and directories simultaneously.

#### Installation

```bash
uv sync  # Install all dependencies including watchdog
```

#### Usage

```bash
# Watch main.py and default directories (core/, utils/)
uv run python repeater

# Watch a specific main file
uv run python repeater main.py
```

#### Watched Paths

By default, watches:
- **Main file**: `main.py` (or specified file)
- **core/**: Business logic directory (recursive)
- **utils/**: Utilities directory (recursive)

#### Runtime Commands

- **`h`**: Show help and current status
- **`r`**: Manual restart of the application
- **`a`**: Toggle auto-reload on/off
- **`Ctrl+C`**: Exit the application gracefully

#### Features

- Multi-directory watching
- Content-aware reloading (only when content changes)
- Rich console output with progress indicators
- Cross-platform support (Windows, macOS, Linux)

<!-- TODO: install -->

## TODO

See [TODO.md](TODO.md) for a list of features and improvements.
