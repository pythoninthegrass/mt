#!/usr/bin/env python

import flet as ft
import os
import random
import sys
import time
import traceback
from collections.abc import Callable
from config import (
    ALPHABET_ROW,
    APP_NAME,
    BUTTON_SYMBOLS,
    COLORS,
    COLUMNS,
    DEFAULT_THEME,
    MUSIC_EXTENSIONS,
    THEME_CONFIG,
    VERSION,
)
from dataclasses import dataclass
from enum import Enum
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
    ListTile,
    ListView,
    MainAxisAlignment,
    NavigationBar,
    NavigationRail,
    Page,
    ProgressBar,
    Row,
    Slider,
    Stack,
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
from typing import Any, Optional, Union


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
            # Instead of actually scanning, we'll create tracks based on mutagen data examples
            sample_tracks = [
                Track(
                    id="1",
                    title="Strobe",
                    artist="Evan Duffy",
                    album="Strobe - Single",
                    path="/Music/01 Strobe.m4a",
                    duration=469,  # 468.95 seconds from mutagen
                    year="2012",
                    genre="Dance",
                    track_number=1
                ),
                Track(
                    id="2",
                    title="Raise Your Weapon",
                    artist="deadmau5",
                    album="4x4=12",
                    path="/Music/09 - Raise Your Weapon.mp3",
                    duration=496,  # 495.64 seconds from mutagen
                    year="2010",
                    genre="Electronic",
                    track_number=9
                ),
                Track(
                    id="3",
                    title="Strobe",
                    artist="Deadmau5",
                    album="For Lack Of A Better Name",
                    path="/Music/10 Strobe.mp3",
                    duration=637,  # 637.05 seconds from mutagen
                    year="2009",
                    genre="Tech House",
                    track_number=10
                ),
                Track(
                    id="4",
                    title="Beautiful Life",
                    artist="Gui Boratto",
                    album="Chromophobia - kompakt.rcrdlb.com",
                    path="/Music/Beautiful Life.mp3",
                    duration=511,  # 510.96 seconds from mutagen
                    year="",  # Not provided in the mutagen data
                    genre="Electronica/Dance",
                    track_number=0  # Not provided in the mutagen data
                )
            ]

            # Add all sample tracks to the library
            for track in sample_tracks:
                self.add_track(track)

            print(f"Added {len(sample_tracks)} tracks to the library")
        except Exception as e:
            print(f"Error scanning directory: {e}")
            traceback.print_exc()


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

        # Add a window event handler to detect resize events
        def handle_window_event(e):
            # Process resize events only if we have a resize handler
            if (hasattr(e, 'data') and e.data == 'resize' and
                hasattr(self, 'page') and hasattr(self.page, 'on_resize')):
                try:
                    self.page.on_resize(e)
                except Exception as ex:
                    print(f"Error handling window resize: {ex}")

        # Register the window event handler
        self.page.on_window_event = handle_window_event

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
        alphabet = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # Add # back to the alphabet
        alphabet_buttons = []
        for letter in alphabet:
            alphabet_buttons.append(
                ft.TextButton(
                    letter,
                    on_click=lambda e, l=letter: self.filter_by_letter(l),
                    style=ft.ButtonStyle(
                        color=colors.get('fg'),
                        padding=0,  # Minimal padding around the text
                    ),
                    width=ALPHABET_ROW['button_width'],
                    height=ALPHABET_ROW['button_height'],
                )
            )

        # Create the alphabet row with center alignment
        alphabet_row = ft.Row(
            alphabet_buttons,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=ALPHABET_ROW['use_wrap'],
            spacing=ALPHABET_ROW['button_spacing'],
        )

        # Get breakpoint settings from configuration
        minimum_width_breakpoint = ALPHABET_ROW['min_breakpoint']
        fixed_alphabet_width = ALPHABET_ROW['fixed_width']
        scale_factor = ALPHABET_ROW['scale_factor']

        # Configure horizontal position based on config
        left_position = ALPHABET_ROW['initial_x']

        # Create a simple container for the alphabet row
        alphabet_container = ft.Container(
            content=alphabet_row,
            bgcolor=colors.get('bg'),
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.get('border'))),
            padding=ft.padding.only(
                top=ALPHABET_ROW['padding_top'],
                bottom=ALPHABET_ROW['padding_bottom']
            ),
            alignment=ft.alignment.center,
            width=fixed_alphabet_width,  # Initial width
            height=ALPHABET_ROW['height'],
        )

        # If initial_x is set, position the container
        if left_position is not None:
            alphabet_container.left = left_position

        # Store reference for resize handling
        self.alphabet_container = alphabet_container

        # Add a page resize handler for responsive behavior
        def on_page_resize(e):
            try:
                # Get window width from page
                window_width = self.page.window.width

                # Only adjust width below the breakpoint, keep centered above
                if window_width < minimum_width_breakpoint:
                    # When below the breakpoint, adjust width proportionally
                    new_width = window_width * scale_factor
                    self.alphabet_container.width = new_width

                    # Update position if initial_x is set
                    if ALPHABET_ROW['initial_x'] is not None:
                        # Recalculate position based on new width if needed
                        # Otherwise, it stays at initial_x
                        pass
                else:
                    # Above breakpoint - fixed width
                    self.alphabet_container.width = fixed_alphabet_width

                    # Reset position if initial_x is set
                    if ALPHABET_ROW['initial_x'] is not None:
                        self.alphabet_container.left = ALPHABET_ROW['initial_x']

                # Update the UI
                self.page.update()
            except Exception as ex:
                print(f"Error in resize handler: {ex}")

        # Register the resize handler
        self.page.on_resize = on_page_resize

        # Create table headers
        headers = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text(
                            col["name"], color=colors.get('fg'), weight=ft.FontWeight.BOLD
                        ),
                        width=col["width"],
                        padding=ft.padding.only(left=10),
                    ) for col in COLUMNS
                ],
                spacing=0,
            ),
            bgcolor=colors.get('bg'),
            height=40,
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.get('border'))),
        )

        # Create tracks list
        track_rows = []
        for i, track in enumerate(self.library.tracks):
            bg_color = colors.get('row_alt') if i % 2 == 1 else colors.get('bg')

            # Build row cells based on COLUMNS configuration
            row_cells = []
            for col in COLUMNS:
                cell_content = ""
                if col["id"] == "number":
                    cell_content = str(i + 1)
                elif col["id"] == "title":
                    cell_content = track.title
                elif col["id"] == "artist":
                    cell_content = track.artist
                elif col["id"] == "album":
                    cell_content = track.album
                elif col["id"] == "year":
                    cell_content = track.year
                elif col["id"] == "duration":
                    cell_content = track.duration_str

                row_cells.append(
                    ft.Container(
                        content=ft.Text(cell_content, color=colors.get('fg')),
                        width=col["width"],
                        padding=ft.padding.only(left=10),
                    )
                )

            track_row = ft.Container(
                content=ft.Row(
                    row_cells,
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
        )

        # Create a simple column layout with the alphabet row at the top
        main_content = ft.Column(
            [
                # Alphabet row at the top
                alphabet_container,

                # Divider to separate alphabet row from content
                ft.Divider(height=1, color=colors.get('border')),

                # Main content
                ft.Container(
                    content=ft.Column(
                        [
                            headers,
                            track_list,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                    bgcolor=colors.get('bg'),
                    padding=0,
                ),
            ],
            spacing=0,
            expand=True,
        )

        # Trigger initial sizing
        # Use a default fixed width for alphabet container if above breakpoint
        if self.page.window.width >= ALPHABET_ROW['min_breakpoint']:
            alphabet_container.width = ALPHABET_ROW['fixed_width']
        else:
            alphabet_container.width = self.page.window.width * ALPHABET_ROW['scale_factor']

        # Apply initial x position if specified
        if ALPHABET_ROW['initial_x'] is not None:
            alphabet_container.left = ALPHABET_ROW['initial_x']

        # Debug output
        print(f"Initial alphabet row setup: width={alphabet_container.width}, " +
              f"x={ALPHABET_ROW['initial_x'] if ALPHABET_ROW['initial_x'] is not None else 'centered'}")

        return ft.Container(
            content=main_content,
            expand=True,
            bgcolor=colors.get('bg'),
            padding=0,
        )

    def build_player_controls(self):
        colors = THEME_CONFIG.get('colors', {})

        # Debug output to check player state
        print(f"Player state: current_track={self.player.current_track}, is_playing={self.player.is_playing}")

        # Track info text - empty string if no track is playing
        track_title = ""
        if self.player.current_track:
            track_title = f"{self.player.current_track.artist} - {self.player.current_track.title}"

        # Track info text
        track_info = ft.Text(
            track_title,
            color=colors.get('fg'),
            size=14,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )

        # Time display
        current_time = "0:00"
        total_time = "0:00"
        if self.player.current_track:
            current_time = self.format_time(self.player.position)
            total_time = self.player.current_track.duration_str

        time_display = ft.Text(
            f"{current_time} / {total_time}",
            color=colors.get('fg'),
            size=14,
        )

        # Control buttons
        previous_button = ft.IconButton(
            icon=ft.Icons.SKIP_PREVIOUS,
            icon_color=colors.get('fg'),
            icon_size=35,
            padding=0,
            tooltip="Previous",
            on_click=lambda _: self.player.previous(),
        )

        play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW if not self.player.is_playing else ft.Icons.PAUSE,
            icon_color=colors.get('fg'),
            icon_size=35,
            padding=0,
            tooltip="Play/Pause",
            on_click=lambda _: self.toggle_play(),
        )

        next_button = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT,
            icon_color=colors.get('fg'),
            icon_size=35,
            padding=0,
            tooltip="Next",
            on_click=lambda _: self.player.next(),
        )

        # Progress slider
        progress_slider = ft.Slider(
            min=0,
            max=100,
            value=0,
            on_change=lambda e: self.player.set_position(int(e.data) if e.data is not None else 0),
            expand=True,
            active_color=colors.get('primary'),
            inactive_color=colors.get('progress_bg', colors.get('secondary')),
            thumb_color=colors.get('primary'),
            height=16,
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
            value=int(self.player.volume * 100),
            width=110,
            on_change=lambda e: self.player.set_volume(float(e.data) / 100 if e.data is not None else self.player.volume),
            active_color=colors.get('primary'),
            inactive_color=colors.get('progress_bg', colors.get('secondary')),
            thumb_color=colors.get('primary'),
            height=16,
        )

        # Width values for controls to ensure consistent spacing
        playback_controls_width = 135
        volume_controls_width = 135

        # Create a layout with track info and progress slider in separate rows
        return ft.Container(
            content=ft.Column(
                [
                    # Top row: Track info and time display
                    ft.Container(
                        content=ft.Row(
                            [
                                # Left section: empty space matching playback controls width + padding
                                ft.Container(width=playback_controls_width + 10),

                                # Track info (expand to fill middle space)
                                track_info,

                                # Right aligned time display
                                time_display,

                                # Right section: empty space matching volume controls width
                                ft.Container(width=volume_controls_width),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.only(bottom=5),
                    ),

                    # Bottom row: Controls and progress slider
                    ft.Row(
                        [
                            # Left section: Playback controls with fixed width
                            ft.Container(
                                content=ft.Row(
                                    [previous_button, play_button, next_button],
                                    spacing=0,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                width=playback_controls_width,
                            ),

                            # Middle: Progress slider (expands to fill space)
                            progress_slider,

                            # Right section: Volume controls with fixed width
                            ft.Container(
                                content=ft.Row(
                                    [volume_icon, volume_slider],
                                    spacing=0,
                                    alignment=ft.MainAxisAlignment.END,
                                ),
                                width=volume_controls_width,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=120,
            width=float('inf'),
            bgcolor=colors.get('bg_dark', colors.get('dark', colors.get('bg'))),
            padding=ft.padding.all(20),
            border=ft.border.only(top=ft.border.BorderSide(1, colors.get('border'))),
        )

    def format_time(self, seconds):
        """Format seconds into mm:ss format"""
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02d}"

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
        # Set initial window properties
        page.title = APP_NAME
        page.theme_mode = "dark" if THEME_CONFIG.get('type') == 'dark' else "light"
        page.padding = 0
        page.spacing = 0
        page.window.width = 1700
        page.window.height = 1080
        page.window.min_width = 1700
        page.window.min_height = 1080
        page.update()

        # Create app instance after initial window setup
        app = MusicApp(page)

    try:
        ft.app(target=app_page)
    except Exception as e:
        print(f"Error in main: {e}")
        exit(1)


if __name__ == "__main__":
    main()
