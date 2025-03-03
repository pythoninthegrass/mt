#!/usr/bin/env python

import flet as ft
import os
import random
import sys
import time
from config import APP_NAME, DEFAULT_THEME, MUSIC_EXTENSIONS, THEME_CONFIG
from dataclasses import dataclass
from flet import (
    AppBar,
    ButtonStyle,
    Card,
    Colors,
    Column,
    Container,
    CrossAxisAlignment,
    Divider,
    ElevatedButton,
    FloatingActionButton,
    Icon,
    IconButton,
    Icons,
    ListView,
    MainAxisAlignment,
    NavigationBar,
    NavigationRail,
    Page,
    ProgressBar,
    Row,
    Slider,
    Tab,
    Tabs,
    Text,
    TextAlign,
    TextButton,
    TextField,
    TextThemeStyle,
    Theme,
    VerticalAlignment,
    alignment,
    app,
    border_radius,
    colors,
    icons,
    margin,
    padding,
)
from pathlib import Path
from typing import Any


# Data structures
@dataclass
class Track:
    id: str
    title: str
    artist: str
    album: str
    path: str
    duration: int = 0
    year: str = ""
    genre: str = ""
    track_number: int = 0

    @property
    def duration_str(self) -> str:
        minutes, seconds = divmod(self.duration, 60)
        return f"{minutes}:{seconds:02d}"


class MusicLibrary:
    def __init__(self):
        self.tracks: list[Track] = []
        self.playlists: dict[str, list[Track]] = {
            "Recently Added": [],
            "Recently Played": [],
            "Top 25 Most Played": [],
        }

    def add_track(self, track: Track):
        self.tracks.append(track)

    def get_tracks(self) -> list[Track]:
        return self.tracks

    def scan_directory(self, directory: str):
        """Scan a directory for music files"""
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in MUSIC_EXTENSIONS):
                        file_path = os.path.join(root, file)
                        # In a real implementation, we would use a library like mutagen
                        # to extract metadata. For now, we'll create dummy data.
                        track_id = str(len(self.tracks) + 1)
                        filename = os.path.basename(file_path)
                        title = os.path.splitext(filename)[0]

                        # Create dummy data for demonstration
                        artists = [
                            "Beirut",
                            "deadmau5",
                            "Gui Boratto",
                            "The Flying Club Cup",
                            "Gallipoli",
                        ]
                        albums = [
                            "4x4=12",
                            "For Lack Of A Better Name",
                            "Chromophobia",
                            "The Flying Club Cup",
                        ]
                        years = [str(year) for year in range(2007, 2021)]
                        genres = ["Indie", "Electronic", "Folk", "Rock", "Jazz"]

                        track = Track(
                            id=track_id,
                            title=title,
                            artist=random.choice(artists),
                            album=random.choice(albums),
                            path=file_path,
                            duration=random.randint(120, 360),
                            year=random.choice(years),
                            genre=random.choice(genres),
                            track_number=random.randint(1, 12),
                        )
                        self.add_track(track)

                        # Add to recently added
                        if len(self.playlists["Recently Added"]) < 25:
                            self.playlists["Recently Added"].append(track)
        except Exception as e:
            print(f"Error scanning directory: {e}")


class Player:
    def __init__(self):
        self.current_track: Track | None = None
        self.is_playing = False
        self.position = 0
        self.volume = 0.5

    def play(self, track: Track | None = None):
        if track:
            self.current_track = track
        if self.current_track:
            self.is_playing = True
            # In a real implementation, we would use a library like pygame to play the music file
            print(f"Playing: {self.current_track.title}")

    def pause(self):
        self.is_playing = False
        print("Paused")

    def stop(self):
        self.is_playing = False
        self.position = 0
        print("Stopped")

    def next(self):
        # In a real implementation, we would get the next track
        # from the current playlist
        print("Next track")

    def previous(self):
        # In a real implementation, we would get the previous track
        # from the current playlist
        print("Previous track")

    def set_position(self, position: int):
        self.position = position

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))


class MusicApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.library = MusicLibrary()
        self.player = Player()
        self.current_view = "library"
        self.selected_tracks: list[Track] = []

        # Configure page
        self.page.title = APP_NAME
        self.page.theme_mode = "dark" if THEME_CONFIG.get('type') == 'dark' else "light"
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window_width = 1700
        self.page.window_height = 1080
        self.page.window_min_width = 1000
        self.page.window_min_height = 600
        # Remove window_maximized to ensure dimensions are respected

        # Apply theme colors to the page
        colors = THEME_CONFIG.get('colors', {})
        self.page.bgcolor = colors.get('bg')
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=colors.get('primary'),
                secondary=colors.get('secondary'),
                background=colors.get('bg'),
                surface=colors.get('bg'),
                on_primary=colors.get('fg'),
                on_secondary=colors.get('fg'),
                on_background=colors.get('fg'),
                on_surface=colors.get('fg'),
            )
        )

        # Create some sample data
        sample_dir = os.path.expanduser("~/Music")
        if os.path.exists(sample_dir):
            self.library.scan_directory(sample_dir)

        # If no tracks were found, create some dummy tracks
        if not self.library.tracks:
            for i in range(1, 21):
                track = Track(
                    id=str(i),
                    title=f"Track {i}",
                    artist="Artist" if i % 3 != 0 else "Various Artists",
                    album=f"Album {i // 4 + 1}",
                    path=f"/path/to/track_{i}.mp3",
                    duration=random.randint(120, 360),
                    year=str(random.randint(2000, 2023)),
                    genre=random.choice(["Rock", "Pop", "Electronic", "Indie", "Folk"]),
                    track_number=i % 12 + 1,
                )
                self.library.add_track(track)

                # Add to recently added
                if i <= 15:
                    self.library.playlists["Recently Added"].append(track)

                # Add to recently played
                if i % 2 == 0 and i <= 10:
                    self.library.playlists["Recently Played"].append(track)

                # Add to top 25
                if i % 3 == 0 or i < 5:
                    self.library.playlists["Top 25 Most Played"].append(track)

        # Build the UI
        self.build_layout()
        self.page.update()

    def build(self):
        # This method is now just a wrapper for backward compatibility
        self.build_layout()
        self.page.update()

    def build_layout(self):
        # Sidebar for library and playlists
        sidebar = self.build_sidebar()

        # Main content area
        main_content = self.build_main_content()

        # Player controls at bottom
        player_controls = self.build_player_controls()

        colors = THEME_CONFIG.get('colors', {})

        # Create full layout
        layout = ft.Column(
            [
                ft.Row(
                    [
                        sidebar,
                        ft.VerticalDivider(width=1, color=colors.get('border')),
                        main_content,
                    ],
                    expand=True,
                    spacing=0,
                ),
                ft.Divider(height=1, color=colors.get('border')),
                player_controls,
            ],
            spacing=0,
            expand=True,
        )

        self.page.add(layout)

    def build_sidebar(self):
        colors = THEME_CONFIG.get('colors', {})

        # Library section
        library_items = [
            ft.Container(height=10),
            ft.Container(
                content=ft.Text(
                    "Library",
                    theme_style=ft.TextThemeStyle.LABEL_LARGE,
                    color=colors.get('fg'),
                ),
                padding=ft.padding.only(left=15, top=1, bottom=1),
            ),
            # Now add the actual library items
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LIBRARY_MUSIC, color=colors.get('primary')),
                title=ft.Text("Music", color=colors.get('fg')),
                selected=True,
                selected_color=colors.get('primary'),
                on_click=lambda _: self.switch_view("library"),
                height=40,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PLAY_CIRCLE, color=colors.get('fg')),
                title=ft.Text("Now Playing", color=colors.get('fg')),
                on_click=lambda _: self.switch_view("now_playing"),
                height=40,
            ),
        ]

        # Playlist section
        playlist_items = []
        default_playlists = ["Recently Added", "Recently Played", "Top 25 Most Played"]
        if not hasattr(self.library, 'playlists') or not self.library.playlists:
            self.library.playlists = default_playlists

        for playlist_name in self.library.playlists:
            playlist_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PLAYLIST_PLAY, color=colors.get('fg')),
                    title=ft.Text(playlist_name, color=colors.get('fg')),
                    on_click=lambda _, name=playlist_name: self.switch_view(
                        "playlist", name
                    ),
                    height=40,
                )
            )

        sidebar = ft.Container(
            content=ft.Column(
                [
                    # Direct content without extra padding
                    ft.Column(library_items, spacing=0),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        "Playlists",
                                        theme_style=ft.TextThemeStyle.LABEL_LARGE,
                                        color=colors.get('fg'),
                                    ),
                                    padding=ft.padding.only(left=15, top=5, bottom=5),
                                ),
                                *playlist_items,
                            ],
                            spacing=0,
                        )
                    ),
                    # Add an expanding container to push everything to the top
                    ft.Container(expand=True),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START, # Align to top
                expand=True,
            ),
            width=250,
            expand=False,
            bgcolor=colors.get('bg'),
            padding=0,
            border=ft.border.only(right=ft.border.BorderSide(1, colors.get('border'))),
        )

        return sidebar


    def build_main_content(self):
        # Alphabet filter row
        colors = THEME_CONFIG.get('colors', {})

        alphabet_row = ft.Row(
            [
                ft.TextButton(
                    text=char,
                    on_click=lambda _, c=char: self.filter_by_letter(c),
                    style=ft.ButtonStyle(
                        color=colors.get('fg'),
                        padding=0,
                    ),
                    height=32,
                    width=30,
                )
                for char in "#ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ],
            scroll=ft.ScrollMode.AUTO,
            wrap=False,
        )

        # Container with reduced padding
        alphabet_container = ft.Container(
            content=alphabet_row,
            padding=ft.padding.only(left=5, right=5),
            alignment=ft.alignment.center,
        )

        # Table headers
        headers = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(
                            "#", color=colors.get('fg'), weight=ft.FontWeight.BOLD
                        ),
                        width=60,
                        padding=ft.padding.only(left=10),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Title", color=colors.get('fg'), weight=ft.FontWeight.BOLD
                        ),
                        width=300,
                        padding=ft.padding.only(left=10),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Artist", color=colors.get('fg'), weight=ft.FontWeight.BOLD
                        ),
                        width=200,
                        padding=ft.padding.only(left=10),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Album", color=colors.get('fg'), weight=ft.FontWeight.BOLD
                        ),
                        width=300,
                        padding=ft.padding.only(left=10),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Year", color=colors.get('fg'), weight=ft.FontWeight.BOLD
                        ),
                        width=100,
                        padding=ft.padding.only(left=10),
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Duration",
                            color=colors.get('fg'),
                            weight=ft.FontWeight.BOLD,
                        ),
                        width=100,
                        padding=ft.padding.only(left=10),
                    ),
                ],
                spacing=0,
            ),
            height=40,
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.get('border'))),
            bgcolor=colors.get('bg'),
        )

        # Create tracks list
        track_rows = []
        for i, track in enumerate(self.library.tracks):
            bg_color = colors.get('row_alt') if i % 2 == 1 else colors.get('bg')

            track_row = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(str(i + 1), color=colors.get('fg')),
                            width=60,
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(track.title, color=colors.get('fg')),
                            width=300,
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(track.artist, color=colors.get('fg')),
                            width=200,
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(track.album, color=colors.get('fg')),
                            width=300,
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(track.year, color=colors.get('fg')),
                            width=100,
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(track.duration_str, color=colors.get('fg')),
                            width=100,
                            padding=ft.padding.only(left=10),
                        ),
                    ],
                    spacing=0,
                ),
                height=40,
                bgcolor=bg_color,
                on_click=lambda _, t=track: self.select_track(t),
            )
            track_rows.append(track_row)

        track_list = ft.Column(
            track_rows,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        main_content = ft.Container(
            content=ft.Column(
                [
                    alphabet_container,
                    ft.Divider(height=1, color=colors.get('border')),
                    headers,
                    track_list,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=colors.get('bg'),
            padding=0,
        )

        return main_content

    def build_player_controls(self):
        # Build player controls row
        colors = THEME_CONFIG.get('colors', {})

        previous_button = ft.IconButton(
            icon=ft.Icons.SKIP_PREVIOUS,
            icon_color=colors.get('fg'),
            icon_size=30,
            tooltip="Previous",
            on_click=lambda _: self.player.previous(),
        )

        play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW if not self.player.is_playing else ft.Icons.PAUSE,
            icon_color=colors.get('primary'),
            icon_size=40,
            tooltip="Play/Pause",
            on_click=lambda _: self.toggle_play(),
        )

        next_button = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT,
            icon_color=colors.get('fg'),
            icon_size=30,
            tooltip="Next",
            on_click=lambda _: self.player.next(),
        )

        # Current time / duration
        current_time = ft.Text("0:00", color=colors.get('fg'), size=14)
        duration = ft.Text("0:00", color=colors.get('fg'), size=14)

        # Progress slider
        progress_slider = ft.Slider(
            min=0,
            max=100,
            value=0,
            on_change=lambda e: self.player.set_position(int(e.data)),
            expand=True,
            active_color=colors.get('primary'),
            inactive_color=colors.get('progress_bg', colors.get('secondary')),
            thumb_color=colors.get('primary'),
            height=20,
        )

        # Volume control
        volume_icon = ft.IconButton(
            icon=ft.Icons.VOLUME_UP,
            icon_color=colors.get('fg'),
            icon_size=20,
            tooltip="Volume",
        )

        volume_slider = ft.Slider(
            min=0,
            max=100,
            value=100,
            width=100,
            on_change=lambda e: self.player.set_volume(float(e.data) / 100),
            active_color=colors.get('primary'),
            inactive_color=colors.get('progress_bg', colors.get('secondary')),
            thumb_color=colors.get('primary'),
            height=20,
        )

        # TODO: move above the top-lefthand side of the progress line
        # * Don't show anything if no track is selected
        # now_playing_info = ft.Text("No track selected", size=14, color=colors.get('fg'))

        # Create a darker background for player controls
        player_bg = colors.get('dark', colors.get('bg'))
        if player_bg == colors.get('bg'):
            # If no dark variant, darken the background slightly
            # Using hex color manipulation instead of with_opacity
            bg_color = colors.get('bg') or "#202020"
            # Make it slightly darker by reducing RGB values by 10%
            if bg_color.startswith('#'):
                # Parse hex color
                r = int(bg_color[1:3], 16)
                g = int(bg_color[3:5], 16)
                b = int(bg_color[5:7], 16)
                # Darken
                r = max(0, int(r * 0.9))
                g = max(0, int(g * 0.9))
                b = max(0, int(b * 0.9))
                # Convert back to hex
                player_bg = f"#{r:02x}{g:02x}{b:02x}"

        player_controls = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [current_time, progress_slider, duration],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            # TODO: reimplement
                            # now_playing_info,
                            ft.Row(
                                [previous_button, play_button, next_button],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [volume_icon, volume_slider],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=0,
            ),
            height=80,
            bgcolor=player_bg,
            border=ft.border.only(top=ft.border.BorderSide(1, colors.get('border'))),
            padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
        )

        return player_controls

    def toggle_play(self):
        if self.player.is_playing:
            self.player.pause()
        else:
            self.player.play()
        # Update the play/pause button icon
        self.page.update()

    def select_track(self, track: Track):
        colors = THEME_CONFIG.get('colors', {})
        self.player.play(track)
        self.page.update()

        # In a real implementation, we would highlight the selected track
        print(f"Selected track: {track.title}")

    def switch_view(self, view_name: str, data: Any = None):
        self.current_view = view_name
        # Update UI to show the selected view
        # In a real implementation, we would rebuild the main content
        # For now, we'll just print the change
        print(f"Switching to view: {view_name}, data: {data}")

    def filter_by_letter(self, letter: str):
        # In a real implementation, we would filter the tracks by letter
        print(f"Filtering by letter: {letter}")


def main():
    def app_page(page: ft.Page):
        app = MusicApp(page)

    try:
        ft.app(target=app_page)
    except Exception as e:
        print(f"Error in main: {e}")
        exit(1)


if __name__ == "__main__":
    main()
