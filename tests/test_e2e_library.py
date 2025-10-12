"""End-to-end tests for library operations via API."""

import pytest
import time


def test_get_library(api_client):
    """Test getting library contents."""
    response = api_client.send('get_library')
    assert response['status'] == 'success', "Failed to get library"
    assert 'data' in response, "Response should include data"
    assert 'count' in response, "Response should include count"
    assert 'total' in response, "Response should include total"

    # Verify structure of returned items
    if response['count'] > 0:
        first_item = response['data'][0]
        assert 'index' in first_item, "Item should have index"
        assert 'track' in first_item, "Item should have track number"
        assert 'title' in first_item, "Item should have title"
        assert 'artist' in first_item, "Item should have artist"
        assert 'album' in first_item, "Item should have album"


def test_select_library_item(api_client):
    """Test selecting an item in the library view."""
    # Get library to find valid index
    library = api_client.send('get_library')
    assert library['status'] == 'success', "Failed to get library"

    if library['count'] > 0:
        # Select first item
        response = api_client.send('select_library_item', index=0)
        assert response['status'] == 'success', "Failed to select library item"


def test_select_library_item_invalid_index(api_client):
    """Test selecting with invalid index returns error."""
    response = api_client.send('select_library_item', index=99999)
    assert response['status'] == 'error', "Should return error for invalid index"
    assert 'out of range' in response.get('message', '').lower(), "Error should mention range"


def test_search_tracks(api_client, clean_queue):
    """Test searching for tracks in the library."""
    # Search for a common term (like "the")
    response = api_client.send('search', query='the')
    assert response['status'] == 'success', "Failed to perform search"
    assert response['query'] == 'the', "Should report the search query"

    # The search should filter the library view
    # We can't directly verify the results, but the command should succeed


def test_search_with_specific_term(api_client, clean_queue):
    """Test searching with a specific artist or title."""
    # Search for "deadmau5" (we know this artist is in the test music)
    response = api_client.send('search', query='deadmau5')
    assert response['status'] == 'success', "Failed to search for deadmau5"


def test_search_empty_query(api_client, clean_queue):
    """Test search with empty query."""
    response = api_client.send('search', query='')
    assert response['status'] == 'success', "Empty search should succeed"


def test_clear_search(api_client, clean_queue):
    """Test clearing search filter."""
    # First perform a search
    api_client.send('search', query='test')

    # Then clear the search
    response = api_client.send('clear_search')
    assert response['status'] == 'success', "Failed to clear search"


def test_switch_to_library_view(api_client):
    """Test switching to library view."""
    response = api_client.send('switch_view', view='library')
    assert response['status'] == 'success', "Failed to switch to library view"
    assert response['view'] == 'Library', "Should report Library view"


def test_library_limit_100_items(api_client):
    """Test that library returns maximum 100 items for performance."""
    response = api_client.send('get_library')
    assert response['status'] == 'success', "Failed to get library"

    # Library should limit to 100 items even if total is higher
    assert response['count'] <= 100, "Should return at most 100 items"

    # If there are more items, total should be higher than count
    if response['total'] > 100:
        assert response['count'] == 100, "Should return exactly 100 items when total exceeds 100"
