#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "lyricsgenius>=3.7.2",
#     "python-decouple>=3.8",
# ]
# [tool.uv]
# exclude-newer = "2025-10-31T00:00:00Z"
# ///

# pyright: reportMissingImports=false

"""
Lyrics fetching utility using Genius API.

Usage as script:
    ./utils/lyrics.py "Song Title" "Artist Name" [--album "Album Name"]

Usage as module:
    from utils.lyrics import fetch_lyrics
    result = fetch_lyrics("Song Title", "Artist Name", "Album Name")

Returns JSON structure:
    {
        "title": str,
        "artist": str,
        "lyrics": str,
        "url": str,
        "found": bool
    }

Note:
    Dependencies get cached in `uv cache dir`
    e.g., ~/Library/Caches/uv/environments-v2/hello-8969d74899f61209
"""

import json
import lyricsgenius
import sys
from pathlib import Path
from typing import Optional


def get_genius_client() -> lyricsgenius.Genius:
    """Get configured Genius API client.

    Returns:
        Configured Genius client instance
    """
    # Get an environment variable using decouple
    env_file = Path.cwd() / '.env'
    if env_file.exists():
        from decouple import Config, RepositoryEnv
        config = Config(RepositoryEnv(env_file))
        token = config("GENIUS_TOKEN")
    else:
        from decouple import config
        token = config("GENIUS_TOKEN")

    genius = lyricsgenius.Genius(token)
    genius.verbose = False                          # Turn off status messages for cleaner output
    genius.remove_section_headers = True            # Remove section headers (e.g. [Chorus]) from lyrics
    genius.skip_non_songs = False                   # Include hits thought to be non-songs
    genius.excluded_terms = ["(Remix)", "(Live)"]   # Exclude songs with these words in their title

    return genius


def fetch_lyrics(title: str, artist: str, album: str | None = None) -> dict:
    """Fetch lyrics for a song from Genius API.

    Args:
        title: Song title
        artist: Artist name
        album: Album name (optional, used for better matching)

    Returns:
        Dictionary with keys:
            - title: Song title from Genius
            - artist: Artist name from Genius
            - lyrics: Song lyrics text
            - url: Genius URL
            - found: Boolean indicating if lyrics were found
    """
    try:
        genius = get_genius_client()
        song = genius.search_song(title, artist)

        if song:
            return {
                "title": song.title,
                "artist": song.artist,
                "lyrics": song.lyrics,
                "url": song.url,
                "found": True
            }
        else:
            return {
                "title": title,
                "artist": artist,
                "lyrics": "",
                "url": "",
                "found": False
            }
    except Exception as e:
        print(f"Error fetching lyrics: {e}", file=sys.stderr)
        return {
            "title": title,
            "artist": artist,
            "lyrics": "",
            "url": "",
            "found": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Command-line interface
    if len(sys.argv) < 3:
        print("Usage: ./utils/lyrics.py 'Song Title' 'Artist Name' [--album 'Album Name']")
        sys.exit(1)

    title = sys.argv[1]
    artist = sys.argv[2]
    album = None

    # Parse optional album argument
    if len(sys.argv) > 3 and sys.argv[3] == "--album" and len(sys.argv) > 4:
        album = sys.argv[4]

    result = fetch_lyrics(title, artist, album)
    print(json.dumps(result, indent=2))
