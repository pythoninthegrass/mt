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

<!-- TODO: dev -->
<!-- TODO: install -->

## TODO

See [TODO.md](TODO.md) for a list of features and improvements.
