import json
import logging
import socket
import time
from config import TEST_TIMEOUT
from typing import Any

# Set up logger for API client
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

        # Circuit breaker state
        self._failure_count = 0
        self._success_count = 0
        self._circuit_open = False
        self._circuit_open_time = None
        self._failure_threshold = 5  # Open circuit after 5 consecutive failures
        self._cooldown_period = 5.0  # Wait 5 seconds before trying again

    def connect(self, timeout: float = 10.0, retry_interval: float | None = None) -> bool:
        """Connect to the API server with retry logic.

        Args:
            timeout: Maximum time to wait for connection (seconds)
            retry_interval: Time between retry attempts (seconds). If None, uses TEST_TIMEOUT.

        Returns:
            True if connection successful, False otherwise
        """
        if retry_interval is None:
            retry_interval = TEST_TIMEOUT
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

    def send(self, action: str, max_retries: int = 3, **params: Any) -> dict[str, Any]:
        """Send a command to the API server with retry logic and exponential backoff.

        The API server closes the connection after each request, so we
        establish a fresh connection for each command.

        Args:
            action: The action to perform (e.g., 'play', 'pause', 'get_status')
            max_retries: Maximum number of retry attempts (default: 3)
            **params: Additional parameters for the action

        Returns:
            Response dictionary from the server

        Raises:
            ConnectionError: If cannot connect to the server after all retries
            ValueError: If server returns invalid JSON
        """
        # Check circuit breaker
        if self._circuit_open:
            # Check if cooldown period has passed
            if time.time() - self._circuit_open_time < self._cooldown_period:
                logger.error(f"Circuit breaker OPEN - rejecting action '{action}' (cooldown: {self._cooldown_period}s)")
                raise ConnectionError(f"Circuit breaker open - server appears to be down. Wait {self._cooldown_period}s.")

            # Try to half-open circuit
            logger.info("Circuit breaker attempting to HALF-OPEN")
            self._circuit_open = False

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # Log attempt
                if attempt > 0:
                    logger.info(f"Retry {attempt}/{max_retries} for action '{action}'")

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

                    # Success - reset circuit breaker
                    self._failure_count = 0
                    self._success_count += 1
                    if self._circuit_open:
                        logger.info("Circuit breaker CLOSED after successful call")
                        self._circuit_open = False

                    return response

                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON response from server: {e}") from e
                except OSError as e:
                    raise ConnectionError(f"Socket error: {e}") from e
                finally:
                    sock.close()

            except (ConnectionError, ValueError) as e:
                last_error = e
                logger.warning(f"Action '{action}' failed (attempt {attempt + 1}/{max_retries + 1}): {e}")

                # Don't retry on ValueError (bad JSON)
                if isinstance(e, ValueError):
                    raise

                # Update circuit breaker
                self._failure_count += 1
                self._success_count = 0

                # Check if we should open the circuit
                if self._failure_count >= self._failure_threshold:
                    self._circuit_open = True
                    self._circuit_open_time = time.time()
                    logger.error(f"Circuit breaker OPENED after {self._failure_count} consecutive failures")

                # If this wasn't the last attempt, wait with exponential backoff
                if attempt < max_retries:
                    backoff = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.debug(f"Waiting {backoff}s before retry...")
                    time.sleep(backoff)

        # All retries exhausted
        logger.error(f"Action '{action}' failed after {max_retries + 1} attempts. Last error: {last_error}")
        raise ConnectionError(f"Failed after {max_retries + 1} attempts: {last_error}") from last_error

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

    def is_healthy(self) -> tuple[bool, str]:
        """Check if the API server is healthy and responding.

        Performs a health check by sending a get_status command.

        Returns:
            Tuple of (is_healthy: bool, message: str)
        """
        try:
            response = self.send('get_status', max_retries=0)
            if response.get('status') == 'success':
                logger.debug("Health check PASSED")
                return True, "API server is healthy"
            else:
                error_msg = f"API server returned error: {response.get('message', 'unknown')}"
                logger.warning(f"Health check FAILED: {error_msg}")
                return False, error_msg
        except ConnectionError as e:
            error_msg = f"Cannot connect to API server: {e}"
            logger.warning(f"Health check FAILED: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during health check: {e}"
            logger.error(f"Health check FAILED: {error_msg}")
            return False, error_msg

    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker state.

        Useful for tests that want to start fresh after a known failure.
        """
        logger.info("Circuit breaker manually RESET")
        self._failure_count = 0
        self._success_count = 0
        self._circuit_open = False
        self._circuit_open_time = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
