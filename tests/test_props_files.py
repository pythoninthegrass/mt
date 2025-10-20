"""Property-based tests for file utility functions using Hypothesis.

These tests verify invariants and edge cases that are hard to catch
with example-based tests. They run fast (<1s) with the 'fast' profile.
"""

import pytest
import sys
from hypothesis import given, strategies as st
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.files import normalize_path


class TestNormalizePathProperties:
    """Property-based tests for normalize_path function."""

    @given(st.text(min_size=1, max_size=100))
    def test_normalize_path_idempotent(self, path_str):
        """Test that normalize_path is idempotent (applying twice gives same result)."""
        # Skip paths that would be invalid on the filesystem
        if "\x00" in path_str:
            pytest.skip("Null bytes not allowed in paths")

        try:
            first = normalize_path(path_str)
            second = normalize_path(first)
            assert first == second, "normalize_path should be idempotent"
        except (ValueError, OSError):
            # Some paths may be invalid on the platform - that's OK
            pytest.skip("Invalid path for platform")

    @given(st.text(min_size=1, max_size=50))
    def test_normalize_path_returns_path_object(self, path_str):
        """Test that normalize_path always returns a Path object."""
        if "\x00" in path_str:
            pytest.skip("Null bytes not allowed in paths")

        try:
            result = normalize_path(path_str)
            assert isinstance(result, Path), "Should always return Path object"
        except (ValueError, OSError):
            pytest.skip("Invalid path for platform")

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789/_-.", min_size=1, max_size=50))
    def test_normalize_path_preserves_valid_paths(self, simple_path):
        """Test that normalize_path preserves simple valid paths."""
        result = normalize_path(simple_path)
        # Should not raise exceptions for simple paths
        assert isinstance(result, Path)
        # Should preserve the core path content
        assert simple_path in str(result) or simple_path.strip("/") in str(result)

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789/_-", min_size=1, max_size=30))
    def test_normalize_path_strips_leading_trailing_braces(self, inner_path):
        """Test that normalize_path strips curly braces from start/end."""
        # Add braces to start and/or end
        path_with_braces = f"{{{inner_path}}}"
        result = normalize_path(path_with_braces)
        result_str = str(result)
        # Leading/trailing braces should be stripped
        assert not result_str.startswith("{")
        assert not result_str.endswith("}")
        # Inner path should be preserved
        assert inner_path in result_str or inner_path.strip("/") in result_str

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789/_-", min_size=1, max_size=30))
    def test_normalize_path_strips_leading_trailing_quotes(self, inner_path):
        """Test that normalize_path strips double quotes from start/end."""
        # Add quotes to start and/or end
        path_with_quotes = f'"{inner_path}"'
        result = normalize_path(path_with_quotes)
        result_str = str(result)
        # Leading/trailing quotes should be stripped
        assert not result_str.startswith('"')
        assert not result_str.endswith('"')
        # Inner path should be preserved
        assert inner_path in result_str or inner_path.strip("/") in result_str

    def test_normalize_path_handles_path_object_input(self):
        """Test that Path objects pass through unchanged."""
        # Use a simple example for this specific test
        path_obj = Path("/simple/path")
        result = normalize_path(path_obj)
        assert result == path_obj
        assert result is path_obj  # Should be the same object


class TestPathNormalizationInvariants:
    """Test mathematical invariants of path normalization."""

    @given(st.sampled_from(["/usr/bin", "/tmp", "/home/user", "relative/path", "."]))
    def test_common_paths_normalize_safely(self, common_path):
        """Test that common path patterns normalize without errors."""
        result = normalize_path(common_path)
        assert isinstance(result, Path)
        # Should be able to convert to string
        assert len(str(result)) > 0

    @given(
        st.one_of(
            st.just(""),
            st.text(alphabet=st.characters(blacklist_characters="\x00"), max_size=10).filter(lambda x: x.strip() == ""),
        )
    )
    def test_empty_or_whitespace_paths(self, empty_path):
        """Test behavior with empty or whitespace-only paths."""
        try:
            result = normalize_path(empty_path)
            # If it doesn't raise, should return a Path
            assert isinstance(result, Path)
        except (ValueError, OSError):
            # Empty paths may raise - that's acceptable behavior
            pass

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20))
    def test_simple_ascii_paths(self, simple_name):
        """Test that simple ASCII paths work correctly."""
        result = normalize_path(simple_name)
        assert isinstance(result, Path)
        assert simple_name in str(result)

    @given(st.lists(st.text(alphabet="abc", min_size=1, max_size=5), min_size=1, max_size=5))
    def test_path_with_components(self, components):
        """Test paths constructed from multiple components."""
        path_str = "/".join(components)
        result = normalize_path(path_str)
        assert isinstance(result, Path)
        # All components should appear in the result
        for component in components:
            assert component in str(result)


class TestPathEdgeCases:
    """Test edge cases in path handling."""

    @given(st.integers(min_value=1, max_value=100))
    def test_repeated_normalization(self, n):
        """Test that repeated normalization converges to a stable value."""
        path = "/some/test/path"
        result = normalize_path(path)

        # Apply normalization n times
        for _ in range(n):
            result = normalize_path(result)

        # Should still be the same as the first normalization
        assert result == normalize_path(path)

    @given(st.text(alphabet=" \t", min_size=0, max_size=10))
    def test_whitespace_handling(self, whitespace):
        """Test handling of various whitespace patterns."""
        path_with_ws = f"{whitespace}/path{whitespace}"
        try:
            result = normalize_path(path_with_ws)
            assert isinstance(result, Path)
        except (ValueError, OSError):
            # May fail for pure whitespace paths
            pass

    def test_normalize_path_commutes_with_str_conversion(self):
        """Test that normalize_path and str() operations commute for Path objects."""
        path_obj = Path("/test/path")
        # normalize(path) then str should equal str(path)
        result1 = str(normalize_path(path_obj))
        result2 = str(path_obj)
        assert result1 == result2
