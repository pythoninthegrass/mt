"""Unit tests for APIClient error handling and retry logic."""

import pytest
import time
from tests.helpers.api_client import APIClient
from unittest.mock import MagicMock, Mock, patch


def test_api_client_retry_logic():
    """Test that APIClient retries on connection failure."""
    client = APIClient()

    # Mock socket to fail twice then succeed
    call_count = 0

    def mock_socket_factory(*args, **kwargs):
        nonlocal call_count
        mock_sock = MagicMock()

        if call_count < 2:
            # First two attempts fail
            call_count += 1
            mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        else:
            # Third attempt succeeds
            call_count += 1
            mock_sock.connect.return_value = None
            mock_sock.send.return_value = None
            mock_sock.recv.side_effect = [b'{"status": "success"}', b'']

        return mock_sock

    with patch('socket.socket', side_effect=mock_socket_factory):
        result = client.send('get_status')
        assert result['status'] == 'success'
        assert call_count == 3  # Should have tried 3 times


def test_api_client_exponential_backoff():
    """Test that retry delays use exponential backoff."""
    client = APIClient()
    delays = []

    original_sleep = time.sleep

    def mock_sleep(duration):
        delays.append(duration)
        original_sleep(0.01)  # Actually sleep a tiny bit to avoid busy loop

    with patch('socket.socket') as mock_socket_cls:
        # Make all attempts fail
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_cls.return_value = mock_sock

        with patch('time.sleep', side_effect=mock_sleep), pytest.raises(ConnectionError):
            client.send('test_action', max_retries=3)

    # Should have 3 delays: 0.5s, 1s, 2s (exponential backoff)
    assert len(delays) == 3
    assert delays[0] == 0.5
    assert delays[1] == 1.0
    assert delays[2] == 2.0


def test_api_client_circuit_breaker():
    """Test that circuit breaker opens after consecutive failures."""
    client = APIClient()
    client._failure_threshold = 3  # Lower threshold for testing

    with patch('socket.socket') as mock_socket_cls:
        # Make all attempts fail
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_cls.return_value = mock_sock

        # First 3 failures should open the circuit
        for i in range(3):
            with pytest.raises(ConnectionError):
                client.send('test_action', max_retries=0)

        # Circuit should now be open
        assert client._circuit_open is True
        assert client._failure_count == 3

        # Next call should fail immediately due to open circuit
        with pytest.raises(ConnectionError, match="Circuit breaker open"):
            client.send('test_action', max_retries=0)


def test_api_client_circuit_breaker_reset():
    """Test that circuit breaker resets on successful call."""
    client = APIClient()
    client._failure_threshold = 2

    with patch('socket.socket') as mock_socket_cls:
        # First 2 calls fail
        mock_sock_fail = MagicMock()
        mock_sock_fail.connect.side_effect = ConnectionRefusedError("Connection refused")

        # Third call succeeds
        mock_sock_success = MagicMock()
        mock_sock_success.connect.return_value = None
        mock_sock_success.send.return_value = None
        mock_sock_success.recv.side_effect = [b'{"status": "success"}', b'']

        mock_socket_cls.side_effect = [mock_sock_fail, mock_sock_fail, mock_sock_success]

        # First two failures
        with pytest.raises(ConnectionError):
            client.send('test1', max_retries=0)
        with pytest.raises(ConnectionError):
            client.send('test2', max_retries=0)

        # Circuit should be open
        assert client._circuit_open is True

        # Wait for cooldown (mock time)
        with patch('time.time') as mock_time:
            mock_time.side_effect = [
                client._circuit_open_time + client._cooldown_period + 1,  # Past cooldown
                client._circuit_open_time + client._cooldown_period + 1,
            ]

            # This should succeed and close the circuit
            result = client.send('test3', max_retries=0)
            assert result['status'] == 'success'
            assert client._circuit_open is False
            assert client._failure_count == 0


def test_api_client_health_check():
    """Test is_healthy() method."""
    client = APIClient()

    with patch('socket.socket') as mock_socket_cls:
        # Successful health check
        mock_sock = MagicMock()
        mock_sock.connect.return_value = None
        mock_sock.send.return_value = None
        mock_sock.recv.side_effect = [b'{"status": "success", "data": {}}', b'']
        mock_socket_cls.return_value = mock_sock

        is_healthy, message = client.is_healthy()
        assert is_healthy is True
        assert "healthy" in message.lower()


def test_api_client_health_check_failure():
    """Test is_healthy() detects connection failure."""
    client = APIClient()

    with patch('socket.socket') as mock_socket_cls:
        # Failed health check
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_socket_cls.return_value = mock_sock

        is_healthy, message = client.is_healthy()
        assert is_healthy is False
        assert "connect" in message.lower()


def test_api_client_manual_circuit_reset():
    """Test manual circuit breaker reset."""
    client = APIClient()

    # Manually trigger circuit breaker
    client._circuit_open = True
    client._failure_count = 10
    client._circuit_open_time = time.time()

    # Reset
    client.reset_circuit_breaker()

    assert client._circuit_open is False
    assert client._failure_count == 0
    assert client._circuit_open_time is None


def test_api_client_no_retry_on_json_error():
    """Test that JSON decode errors don't trigger retries."""
    client = APIClient()

    with patch('socket.socket') as mock_socket_cls:
        mock_sock = MagicMock()
        mock_sock.connect.return_value = None
        mock_sock.send.return_value = None
        # Return invalid JSON
        mock_sock.recv.side_effect = [b'invalid json', b'']
        mock_socket_cls.return_value = mock_sock

        # Should raise ValueError immediately, not retry
        with pytest.raises(ValueError, match="Invalid JSON"):
            client.send('test_action', max_retries=3)

        # Should only have tried once (no retries for JSON errors)
        assert mock_socket_cls.call_count == 1
