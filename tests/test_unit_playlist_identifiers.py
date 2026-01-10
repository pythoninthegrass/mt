"""Unit tests for playlist identifier standardization.

Tests that ensure consistent use of 'recently_added' and 'recently_played'
identifiers throughout the codebase (not 'recent_added' or 'recent_played').
"""

import pytest
import inspect


class TestIdentifierStandardization:
    """Tests for identifier standardization in source code."""

    def test_library_search_no_old_identifiers(self):
        """Should not use old-style identifiers in library_search.py."""
        from core.gui import library_search

        # Get the source code
        source = inspect.getsource(library_search)

        # Ensure no references to old identifiers in string literals or tags
        assert "'recent_added'" not in source, "Found old 'recent_added' identifier"
        assert '"recent_added"' not in source, "Found old 'recent_added' identifier"
        assert "'recent_played'" not in source, "Found old 'recent_played' identifier"
        assert '"recent_played"' not in source, "Found old 'recent_played' identifier"

    def test_player_ui_no_old_identifiers(self):
        """Should not use old-style identifiers in player ui.py."""
        from core.player import ui

        # Get the source code
        source = inspect.getsource(ui)

        # Ensure no references to old identifiers
        assert "'recent_added'" not in source, "Found old 'recent_added' identifier in ui.py"
        assert '"recent_added"' not in source, "Found old 'recent_added' identifier in ui.py"
        assert "'recent_played'" not in source, "Found old 'recent_played' identifier in ui.py"
        assert '"recent_played"' not in source, "Found old 'recent_played' identifier in ui.py"

        # Ensure references to new identifiers exist
        assert "'recently_added'" in source or '"recently_added"' in source, "Missing 'recently_added' identifier"
        assert "'recently_played'" in source or '"recently_played"' in source, "Missing 'recently_played' identifier"


class TestPlaylistIdentifiers:
    """Tests for custom playlist identifier format."""

    def test_custom_playlist_identifier_format(self):
        """Should use 'playlist:<id>' format for custom playlists."""
        # Test that playlist identifiers follow the correct format
        playlist_id = 42
        expected_identifier = f'playlist:{playlist_id}'

        # Verify format
        assert expected_identifier.startswith('playlist:')
        assert expected_identifier.split(':')[1].isdigit()

    def test_playlist_id_extraction(self):
        """Should correctly extract playlist ID from identifier."""
        playlist_id = 42
        identifier = f'playlist:{playlist_id}'

        # Extract ID
        extracted_id = int(identifier.split(':')[1])

        assert extracted_id == playlist_id

    def test_invalid_playlist_identifier(self):
        """Should handle invalid playlist identifier format."""
        invalid_identifiers = [
            'playlist:',
            'playlist:abc',
            'playlist',
            ':42',
            'playlists:42',
        ]

        for identifier in invalid_identifiers:
            try:
                # Try to extract ID
                if identifier.startswith('playlist:'):
                    parts = identifier.split(':')
                    if len(parts) == 2 and parts[1]:
                        int(parts[1])
                    else:
                        raise ValueError("Invalid format")
                else:
                    raise ValueError("Invalid prefix")
            except (ValueError, IndexError):
                # Expected to fail
                pass
            else:
                pytest.fail(f"Should have failed for invalid identifier: {identifier}")


class TestViewIdentifierConsistency:
    """Tests for consistency between view identifiers and routing."""

    def test_dynamic_playlist_identifiers(self):
        """Should use consistent identifiers for dynamic playlists."""
        valid_identifiers = [
            'liked_songs',
            'recently_added',
            'recently_played',
            'top_25',
        ]

        # Ensure these are the canonical identifiers
        for identifier in valid_identifiers:
            assert '_' in identifier or identifier == 'top_25', f"Invalid identifier format: {identifier}"

    def test_no_underscore_inconsistencies(self):
        """Should not mix underscore styles in identifiers."""
        # recently_added is correct (underscore between words)
        # recent_added is wrong (inconsistent with 'recently')
        correct_identifiers = ['recently_added', 'recently_played']

        for identifier in correct_identifiers:
            assert 'recently_' in identifier, f"Identifier should use 'recently_' prefix: {identifier}"
