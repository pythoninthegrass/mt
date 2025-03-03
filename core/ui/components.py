#!/usr/bin/env python

import flet as ft
import threading
import time
import traceback
from collections.abc import Callable
from config import (
    ALPHABET_ROW,
    COLUMNS,
    THEME_CONFIG,
)
from core.models import Track
from flet import (
    Column,
    Container,
    Icon,
    ListTile,
    MainAxisAlignment,
    Row,
    Text,
    TextThemeStyle,
    padding,
)
from typing import Any
from utils.common import format_time


class MusicAppComponents:
    """
    UI component builder methods for the music player application.

    This class provides methods to build various UI components
    used in the music player interface.
    """

    @staticmethod
    def build_sidebar(app):
        """
        Build the sidebar containing library and playlist navigation.

        Args:
            app: Reference to the MusicApp instance

        Returns:
            Container: The sidebar container
        """
        colors = THEME_CONFIG.get('colors', {})

        # Library section
        library_items = [
            Container(height=10),
            Container(
                content=Text(
                    "Library",
                    theme_style=TextThemeStyle.LABEL_LARGE,
                    color=colors.get('fg'),
                ),
                padding=padding.only(left=15, top=1, bottom=1),
            ),
            # Now add the actual library items
            ListTile(
                leading=Icon(ft.Icons.LIBRARY_MUSIC, color=colors.get('primary')),
                title=Text("Music", color=colors.get('fg')),
                selected=True,
                selected_color=colors.get('primary'),
                on_click=lambda _: app.switch_view("library"),
                height=40,
            ),
            ListTile(
                leading=Icon(ft.Icons.PLAY_CIRCLE, color=colors.get('fg')),
                title=Text("Now Playing", color=colors.get('fg')),
                on_click=lambda _: app.switch_view("now_playing"),
                height=40,
            ),
        ]

        # Playlist section
        playlist_items = []
        default_playlists = ["Recently Added", "Recently Played", "Top 25 Most Played"]
        if not hasattr(app.library, 'playlists') or not app.library.playlists:
            app.library.playlists = default_playlists

        for playlist_name in app.library.playlists:
            playlist_items.append(
                ListTile(
                    leading=Icon(ft.Icons.PLAYLIST_PLAY, color=colors.get('fg')),
                    title=Text(playlist_name, color=colors.get('fg')),
                    on_click=lambda _, name=playlist_name: app.switch_view(
                        "playlist", name
                    ),
                    height=40,
                )
            )

        sidebar = Container(
            content=Column(
                [
                    # Direct content without extra padding
                    Column(library_items, spacing=0),
                    Container(
                        content=Column(
                            [
                                Container(
                                    content=Text(
                                        "Playlists",
                                        theme_style=TextThemeStyle.LABEL_LARGE,
                                        color=colors.get('fg'),
                                    ),
                                    padding=padding.only(left=15, top=5, bottom=5),
                                ),
                                *playlist_items,
                            ],
                            spacing=0,
                        )
                    ),
                    # Add an expanding container to push everything to the top
                    Container(expand=True),
                ],
                spacing=0,
                alignment=MainAxisAlignment.START,  # Align to top
                expand=True,
            ),
            width=250,
            expand=False,
            bgcolor=colors.get('bg'),
            padding=0,
            border=ft.border.only(right=ft.border.BorderSide(1, colors.get('border'))),
        )

        return sidebar

    @staticmethod
    def build_player_controls(app):
        """
        Build the player controls UI component.

        Args:
            app: Reference to the MusicApp instance

        Returns:
            Container: The player controls container
        """
        colors = THEME_CONFIG.get('colors', {})

        # Debug output to check player state
        print(
            f"Player state: current_track={app.player.current_track}, is_playing={app.player.player_core.is_playing}"
        )

        # Track info text - empty string if no track is playing
        track_title = ""
        if app.player.current_track:
            track_title = f"{app.player.current_track.artist} - {app.player.current_track.title}"

        # Track info text
        track_info = Text(
            track_title,
            color=colors.get('fg'),
            size=14,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )

        # Time display
        current_time = "0:00"
        total_time = "0:00"
        if app.player.current_track:
            current_time = format_time(
                app.player.player_core.get_current_time() // 1000
            )
            total_time = app.player.current_track.duration_str

        time_display = Text(
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
            on_click=lambda _: app.previous_track(),
        )

        play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW
            if not app.player.player_core.is_playing
            else ft.Icons.PAUSE,
            icon_color=colors.get('fg'),
            icon_size=35,
            padding=0,
            tooltip="Play/Pause",
            on_click=lambda _: app.toggle_play(),
        )

        next_button = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT,
            icon_color=colors.get('fg'),
            icon_size=35,
            padding=0,
            tooltip="Next",
            on_click=lambda _: app.next_track(),
        )

        # Progress slider
        progress_slider = ft.Slider(
            min=0,
            max=100,
            value=0,
            on_change=lambda e: app.set_position_threaded(
                int(e.data) if e.data is not None else 0
            ),
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

        # Fix the initialization of the volume slider value
        # Ensure the volume value is clamped between 0 and 100
        volume_value = max(0, min(100, int(app.player.player_core.get_volume())))

        volume_slider = ft.Slider(
            min=0,
            max=100,
            value=volume_value,  # Use the clamped value
            width=110,
            on_change=lambda e: app.set_volume_threaded(
                float(e.data) / 100 if e.data is not None else 0.7
            ),
            active_color=colors.get('primary'),
            inactive_color=colors.get('progress_bg', colors.get('secondary')),
            thumb_color=colors.get('primary'),
            height=16,
        )

        # Width values for controls to ensure consistent spacing
        playback_controls_width = 135
        volume_controls_width = 135

        # Create a layout with track info and progress slider in separate rows
        player_controls = Container(
            content=Column(
                [
                    # Top row: Track info and time display
                    Container(
                        content=Row(
                            [
                                # Left section: empty space matching playback controls width + padding
                                Container(width=playback_controls_width + 10),
                                # Track info (expand to fill middle space)
                                track_info,
                                # Right aligned time display
                                time_display,
                                # Right section: empty space matching volume controls width
                                Container(width=volume_controls_width),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=padding.only(bottom=5),
                    ),
                    # Bottom row: Controls and progress slider
                    Row(
                        [
                            # Left section: Playback controls with fixed width
                            Container(
                                content=Row(
                                    [previous_button, play_button, next_button],
                                    spacing=0,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                width=playback_controls_width,
                            ),
                            # Middle: Progress slider (expands to fill space)
                            progress_slider,
                            # Right section: Volume controls with fixed width
                            Container(
                                content=Row(
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
            padding=padding.all(20),
            border=ft.border.only(top=ft.border.BorderSide(1, colors.get('border'))),
        )

        # Store references for direct access
        app._track_info = track_info
        app._time_display = time_display
        app._play_button = play_button
        app._progress_slider = progress_slider

        return player_controls

    @staticmethod
    def build_alphabet_row(app):
        """
        Build the alphabet filtering row.

        Args:
            app: Reference to the MusicApp instance

        Returns:
            Container: The alphabet row container
        """
        colors = THEME_CONFIG.get('colors', {})
        alphabet = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # Add # to the alphabet
        alphabet_buttons = []

        for letter in alphabet:
            alphabet_buttons.append(
                ft.TextButton(
                    letter,
                    on_click=lambda e, l=letter: app.filter_by_letter(l),
                    style=ft.ButtonStyle(
                        color=colors.get('fg'),
                        padding=0,  # Minimal padding around the text
                    ),
                    width=ALPHABET_ROW['button_width'],
                    height=ALPHABET_ROW['button_height'],
                )
            )

        # Create the alphabet row with center alignment
        alphabet_row = Row(
            alphabet_buttons,
            alignment=MainAxisAlignment.CENTER,
            wrap=ALPHABET_ROW['use_wrap'],
            spacing=ALPHABET_ROW['button_spacing'],
        )

        # Configure horizontal position based on config
        left_position = ALPHABET_ROW['initial_x']

        # Create a simple container for the alphabet row
        alphabet_container = Container(
            content=alphabet_row,
            bgcolor=colors.get('bg'),
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.get('border'))),
            padding=padding.only(
                top=ALPHABET_ROW['padding_top'], bottom=ALPHABET_ROW['padding_bottom']
            ),
            alignment=ft.alignment.center,
            width=ALPHABET_ROW['fixed_width'],  # Initial width
            height=ALPHABET_ROW['height'],
        )

        # If initial_x is set, position the container
        if left_position is not None:
            alphabet_container.left = left_position

        return alphabet_container
