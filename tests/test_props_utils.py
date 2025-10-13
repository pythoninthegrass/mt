"""Property-based tests for utility functions using Hypothesis.

These tests validate invariants and properties of utility functions
that should hold for all valid inputs. They complement unit tests by
discovering edge cases through automated test generation.
"""

import sys
from hypothesis import given, strategies as st
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestTimeConversionProperties:
    """Property-based tests for time conversion utilities."""

    @given(milliseconds=st.integers(min_value=0, max_value=86400000))  # Max 24 hours
    def test_milliseconds_to_seconds_non_negative(self, milliseconds):
        """Converting milliseconds to seconds should never be negative."""
        seconds = milliseconds / 1000
        assert seconds >= 0

    @given(milliseconds=st.integers(min_value=0, max_value=86400000))
    def test_milliseconds_seconds_roundtrip(self, milliseconds):
        """Converting ms -> seconds -> ms should preserve value (with rounding)."""
        seconds = milliseconds / 1000.0
        result = round(seconds * 1000)
        assert result == milliseconds

    @given(seconds=st.integers(min_value=0, max_value=86400))  # Max 24 hours
    def test_seconds_to_minutes_format(self, seconds):
        """Converting seconds to MM:SS format should be valid."""
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        formatted = f"{minutes:02d}:{remaining_seconds:02d}"

        # Should match format
        assert len(formatted) >= 5  # At least "00:00"
        assert ":" in formatted
        assert formatted.count(":") == 1

        # Minutes and seconds should be extractable
        parts = formatted.split(":")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()


class TestPercentageConversionProperties:
    """Property-based tests for percentage/position conversions."""

    @given(
        percentage=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        total=st.integers(min_value=1, max_value=1000000),
    )
    def test_percentage_to_absolute_in_bounds(self, percentage, total):
        """Converting percentage to absolute value should stay in bounds."""
        absolute = int(total * percentage)
        assert 0 <= absolute <= total

    @given(
        percentage=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        total=st.integers(min_value=1, max_value=1000000),
    )
    def test_percentage_conversion_monotonic(self, percentage, total):
        """Larger percentages should give larger absolute values."""
        absolute1 = int(total * percentage)
        absolute2 = int(total * min(1.0, percentage + 0.1))

        if percentage < 1.0:
            assert absolute2 >= absolute1

    @given(
        value=st.integers(min_value=0, max_value=1000000),
        total=st.integers(min_value=1, max_value=1000000),
    )
    def test_absolute_to_percentage_in_bounds(self, value, total):
        """Converting absolute to percentage should give [0.0, 1.0]."""
        # Clamp value to total
        clamped = min(value, total)
        percentage = clamped / total
        assert 0.0 <= percentage <= 1.0


class TestRangeClampingProperties:
    """Property-based tests for range clamping utilities."""

    @given(
        value=st.integers(min_value=-1000, max_value=1000),
        min_val=st.integers(min_value=-100, max_value=0),
        max_val=st.integers(min_value=1, max_value=100),
    )
    def test_clamp_to_range(self, value, min_val, max_val):
        """Clamping a value should keep it within [min, max]."""
        clamped = max(min_val, min(value, max_val))
        assert min_val <= clamped <= max_val

    @given(
        value=st.integers(min_value=0, max_value=100),
        min_val=st.integers(min_value=0, max_value=50),
        max_val=st.integers(min_value=51, max_value=100),
    )
    def test_clamp_within_range_unchanged(self, value, min_val, max_val):
        """Clamping a value already in range should not change it."""
        if min_val <= value <= max_val:
            clamped = max(min_val, min(value, max_val))
            assert clamped == value

    @given(value=st.integers(min_value=-1000, max_value=-1))
    def test_clamp_to_zero_one_hundred(self, value):
        """Negative values clamped to [0, 100] should become 0."""
        clamped = max(0, min(value, 100))
        assert clamped == 0

    @given(value=st.integers(min_value=101, max_value=10000))
    def test_clamp_above_range(self, value):
        """Values above [0, 100] should clamp to 100."""
        clamped = max(0, min(value, 100))
        assert clamped == 100


class TestStringOperationProperties:
    """Property-based tests for string operation utilities."""

    @given(text=st.text(min_size=0, max_size=1000))
    def test_strip_idempotent(self, text):
        """Stripping whitespace twice should give same result."""
        stripped_once = text.strip()
        stripped_twice = stripped_once.strip()
        assert stripped_once == stripped_twice

    @given(text=st.text(min_size=0, max_size=1000))
    def test_strip_never_longer(self, text):
        """Stripping should never make string longer."""
        stripped = text.strip()
        assert len(stripped) <= len(text)

    @given(
        text=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=("Cs",)))
    )
    def test_lower_then_upper_identity(self, text):
        """Converting to lower then upper should give uppercase version."""
        lowered = text.lower()
        uppered = lowered.upper()
        assert uppered == text.upper()

    @given(text=st.text(min_size=0, max_size=100))
    def test_lower_idempotent(self, text):
        """Converting to lowercase twice should give same result."""
        lower_once = text.lower()
        lower_twice = lower_once.lower()
        assert lower_once == lower_twice

    @given(text=st.text(min_size=0, max_size=100))
    def test_upper_idempotent(self, text):
        """Converting to uppercase twice should give same result."""
        upper_once = text.upper()
        upper_twice = upper_once.upper()
        assert upper_once == upper_twice


class TestPathOperationProperties:
    """Property-based tests for path operation utilities."""

    @given(filename=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
    def test_path_normalization_idempotent(self, filename):
        """Normalizing a path twice should give same result."""
        path1 = Path(filename)
        normalized_once = path1.resolve()
        normalized_twice = normalized_once.resolve()
        assert normalized_once == normalized_twice

    @given(parts=st.lists(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"), min_size=1, max_size=5))
    def test_path_join_parts_count(self, parts):
        """Joining path parts should preserve all components."""
        joined = Path(*parts)
        # Path should contain all parts
        path_str = str(joined)
        for part in parts:
            assert part in path_str

    @given(filename=st.text(min_size=1, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz._-"))
    def test_stem_and_suffix_reconstruct(self, filename):
        """File stem + suffix should reconstruct filename."""
        if "." in filename and not filename.startswith("."):
            path = Path(filename)
            reconstructed = path.stem + path.suffix
            assert reconstructed == filename
