"""API client for communicating with mt music player API server."""

import json
import socket
import time
from typing import Any


class APIClient:
    """Client for sending commands to the mt API server."""

    def __init__(self, host: str = 'localhost', port: int = 5555):
        """Initialize the API client.

        Args:
            host: API server host (default: localhost)
            port: API server port (default: 5555)
        """
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None

    def connect(self, timeout: float = 10.0, retry_interval: float = 0.5) -> bool:
        """Connect to the API server with retry logic.

        Args:
            timeout: Maximum time to wait for connection (seconds)
            retry_interval: Time between retry attempts (seconds)

        Returns:
            True if connection successful, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                self.socket.connect((self.host, self.port))
                return True
            except (ConnectionRefusedError, OSError):
                if self.socket:
                    self.socket.close()
                    self.socket = None
                time.sleep(retry_interval)

        return False

    def disconnect(self):
        """Close the connection to the API server."""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            finally:
                self.socket = None

    def send(self, action: str, **params: Any) -> dict[str, Any]:
        """Send a command to the API server.

        The API server closes the connection after each request, so we
        establish a fresh connection for each command.

        Args:
            action: The action to perform (e.g., 'play', 'pause', 'get_status')
            **params: Additional parameters for the action

        Returns:
            Response dictionary from the server

        Raises:
            ConnectionError: If cannot connect to the server
            ValueError: If server returns invalid JSON
        """
        # Create fresh connection for this request
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)

        try:
            sock.connect((self.host, self.port))
        except (ConnectionRefusedError, OSError) as e:
            sock.close()
            raise ConnectionError(f"Failed to connect to API server: {e}") from e

        # Build command
        command = {'action': action, **params}
        command_json = json.dumps(command)

        try:
            # Send command
            sock.send(command_json.encode('utf-8'))

            # Receive response - read until connection closes or we get full JSON
            data_parts = []
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                data_parts.append(chunk)

            if not data_parts:
                raise ConnectionError("Server closed connection before responding")

            data = b''.join(data_parts).decode('utf-8')

            # Parse response
            response = json.loads(data)
            return response

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from server: {e}") from e
        except OSError as e:
            raise ConnectionError(f"Socket error: {e}") from e
        finally:
            sock.close()

    def send_and_reconnect(self, action: str, **params: Any) -> dict[str, Any]:
        """Send a command, reconnecting if necessary.

        This is useful for tests where the connection might be dropped.

        Args:
            action: The action to perform
            **params: Additional parameters for the action

        Returns:
            Response dictionary from the server
        """
        try:
            return self.send(action, **params)
        except (ConnectionError, OSError):
            # Try to reconnect and send again
            self.disconnect()
            if self.connect():
                return self.send(action, **params)
            raise ConnectionError("Failed to reconnect to API server") from None

    def wait_for_api(self, timeout: float = 10.0) -> bool:
        """Wait for the API server to be ready.

        Args:
            timeout: Maximum time to wait (seconds)

        Returns:
            True if API is ready, False otherwise
        """
        return self.connect(timeout=timeout)

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
