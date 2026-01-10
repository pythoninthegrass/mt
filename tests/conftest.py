import gc
import glob
import os
import pytest
import shutil
import subprocess
import sys
import threading
import time
from config import DB_NAME
from contextlib import suppress
from decouple import config
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Hypothesis configuration for property-based testing
from hypothesis import HealthCheck, settings
from tests.helpers.api_client import APIClient

# Register Hypothesis profiles
settings.register_profile("fast", max_examples=50, deadline=None)
settings.register_profile("thorough", max_examples=1000, deadline=None)
settings.load_profile("fast")  # Default to fast profile


def pytest_collection_modifyitems(items):
    """Automatically order tests: unit tests first, then property tests, then E2E tests.

    Individual tests marked with @pytest.mark.order("last") will run at the very end.
    """
    for item in items:
        # Skip if item already has explicit order marker
        if hasattr(item, 'get_closest_marker') and item.get_closest_marker('order'):
            continue

        # Assign order based on test file name
        test_file = str(item.fspath)
        if 'test_unit_' in test_file:
            item.add_marker(pytest.mark.order(1))
        elif 'test_props_' in test_file:
            item.add_marker(pytest.mark.order(2))
        elif 'test_e2e_' in test_file:
            item.add_marker(pytest.mark.order(3))


def setup_macos_environment():
    """Setup TCL/TK environment variables for macOS."""
    env = os.environ.copy()

    if sys.platform == 'darwin':
        # Get TCL/TK paths from environment or use Homebrew defaults
        tcl_library = config('TCL_LIBRARY', default='/opt/homebrew/opt/tcl-tk/lib/tcl8.6')
        tk_library = config('TK_LIBRARY', default='/opt/homebrew/opt/tcl-tk/lib/tk8.6')
        tcl_tk_bin = config('TCL_TK_BIN', default='/opt/homebrew/opt/tcl-tk/bin')

        # Set TCL/TK environment variables
        env['TCL_LIBRARY'] = tcl_library
        env['TK_LIBRARY'] = tk_library

        # Prepend TCL/TK bin to PATH
        env['PATH'] = f"{tcl_tk_bin}:{env.get('PATH', '')}"

    return env


@pytest.fixture(scope="session")
def test_music_files():
    """Provide test music files. Set MT_TEST_MUSIC_DIR env var to override default path."""
    default_music_dir = '/Users/lance/Library/CloudStorage/Dropbox/mt/music'
    music_dir = config('MT_TEST_MUSIC_DIR', default=default_music_dir)

    if not os.path.isdir(music_dir):
        return []

    mp3_files = glob.glob(f"{music_dir}/**/*.mp3", recursive=True)
    m4a_files = glob.glob(f"{music_dir}/**/*.m4a", recursive=True)

    return (mp3_files + m4a_files)[:10]


@pytest.fixture(scope="session")
def app_process():
    """Start the mt application with API server enabled.

    Yields:
        subprocess.Popen: The running application process
    """
    # Use temporary database file for tests (auto-cleanup, no filesystem pollution)
    import sqlite3
    import tempfile

    main_db_path = project_root / DB_NAME

    # Create a temporary file for the test database
    # Using tempfile ensures automatic cleanup and no conflicts
    test_db_fd, test_db_path = tempfile.mkstemp(suffix='.db', prefix='mt_test_')
    os.close(test_db_fd)  # Close the file descriptor, we'll use the path
    test_db_path = Path(test_db_path)

    # Copy main database to test location if it exists
    if main_db_path.exists():
        # Copy entire database
        shutil.copy(main_db_path, test_db_path)

        # Clear the queue table for clean test state
        conn = sqlite3.connect(test_db_path)
        conn.execute("DELETE FROM queue")
        conn.commit()
        conn.close()

    # Set environment variables for testing
    env = setup_macos_environment()
    env['MT_API_SERVER_ENABLED'] = 'true'
    env['MT_API_SERVER_PORT'] = '5555'
    env['MT_RELOAD'] = 'false'  # Disable auto-reload during tests
    env['DB_NAME'] = str(test_db_path)  # Use temporary test database

    # Start the application
    proc = subprocess.Popen(
        ['uv', 'run', 'main.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(project_root)
    )

    # Wait for API server to be ready
    client = APIClient()
    if not client.wait_for_api(timeout=15.0):
        proc.terminate()
        proc.wait()
        raise RuntimeError("API server failed to start within 15 seconds")

    # Clear the queue initially
    try:
        client.send('clear_queue')
    except Exception:
        pass  # Ignore errors during initial clear

    yield proc

    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)

    # Remove temporary test database
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def api_client(app_process):
    """Provide a connected API client for tests.

    Args:
        app_process: The running application process

    Yields:
        APIClient: Connected API client instance
    """
    client = APIClient(host='localhost', port=5555)

    if not client.connect(timeout=5.0):
        raise RuntimeError("Failed to connect to API server")

    yield client

    client.disconnect()


@pytest.fixture(scope='session')
def api_client_session(app_process):
    """Session-scoped API client for setup/teardown operations.

    This client is used for session-level operations like:
    - Capturing original state before tests
    - Restoring original state after all tests

    Args:
        app_process: The running application process

    Yields:
        APIClient: Connected API client instance
    """
    from tests.helpers.api_client import APIClient

    client = APIClient()

    # Wait for server to be ready with retries
    max_retries = 10
    for attempt in range(max_retries):
        try:
            client.connect()
            # Test connection
            response = client.send('get_status')
            if response.get('status') == 'success':
                break
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to connect to API server after {max_retries} attempts") from e
            time.sleep(0.5)

    yield client

    client.disconnect()


@pytest.fixture(scope='session')
def original_volume(api_client_session):
    """Capture and restore original volume level across entire test session.

    This session-scoped fixture:
    - Captures the volume level before any tests run
    - Restores it after all tests complete

    This ensures the user's volume preference is preserved after running tests.
    """
    # Capture original volume before any tests run
    original_vol = 80  # Default fallback
    try:
        status_response = api_client_session.send('get_status')
        if status_response.get('status') == 'success':
            original_vol = status_response.get('data', {}).get('volume', 80)
    except Exception:
        pass

    yield original_vol

    # Restore original volume after all tests complete
    try:
        api_client_session.send('set_volume', volume=original_vol)
    except Exception:
        pass


@pytest.fixture
def clean_queue(api_client, original_volume):
    """Clear the queue and reset application state before and after each test.

    Resets the following stateful variables to ensure test isolation:
    - Queue content (cleared)
    - VLC media player state (stopped if playing, media cleared)
    - Search query (cleared)
    - Current view (reset to 'queue')
    - Loop state (disabled)
    - Shuffle state (disabled)
    - Volume (set to 80% during tests)

    Note: Original volume is restored after all tests via the original_volume fixture.

    Args:
        api_client: Connected API client
        original_volume: Session fixture that captures and restores volume
    """

    def reset_state():
        """Reset all application state variables."""
        # Clear queue first (this is critical)
        clear_response = api_client.send('clear_queue')
        assert clear_response['status'] == 'success', f"Failed to clear queue: {clear_response}"

        # Verify queue is actually empty
        queue_check = api_client.send('get_queue')
        assert queue_check['count'] == 0, f"Queue not empty after clear: {queue_check['count']} items"

        # Get current state to check what needs resetting
        status_response = api_client.send('get_status')
        status_ok = status_response.get('status') == 'success'

        if status_ok:
            status_data = status_response.get('data', {})

            # Stop playback if something is currently playing (resets VLC state)
            if status_data.get('is_playing', False):
                with suppress(Exception):
                    api_client.send('stop')

            # Disable loop and repeat-one (may need multiple toggles for three-state cycle)
            # Keep toggling until both loop and repeat_one are False
            max_attempts = 5  # Safety limit
            for _ in range(max_attempts):
                if not status_data.get('loop_enabled', False) and not status_data.get('repeat_one', False):
                    break
                with suppress(Exception):
                    api_client.send('toggle_loop')
                # Re-check status
                status_response = api_client.send('get_status')
                status_data = status_response.get('data', {})

            # Disable shuffle if enabled
            if status_data.get('shuffle_enabled', False):
                with suppress(Exception):
                    api_client.send('toggle_shuffle')

        # Clear any active search
        with suppress(Exception):
            api_client.send('clear_search')

        # Reset view to 'queue' (now_playing view)
        with suppress(Exception):
            api_client.send('switch_view', view='queue')

        # Set volume to consistent level for tests (80%)
        with suppress(Exception):
            api_client.send('set_volume', volume=80)

    # Reset state before test
    reset_state()

    yield

    # Reset state after test
    reset_state()


@pytest.fixture(scope="function", autouse=False)
def monitor_resources(request):
    """Monitor system resources before and after each test.

    Tracks:
    - Thread count
    - Memory usage (if psutil available)
    - File descriptors (if psutil available on Unix)

    Usage: Add to test function parameters to enable monitoring for that test.
    """
    test_name = request.node.name

    # Get initial resource counts
    threads_before = threading.active_count()
    thread_names_before = [t.name for t in threading.enumerate()]

    try:
        import psutil

        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        try:
            fds_before = process.num_fds() if hasattr(process, 'num_fds') else None
        except Exception:
            fds_before = None
    except ImportError:
        memory_before = None
        fds_before = None

    print(f"\n[RESOURCES BEFORE {test_name}]")
    print(f"  Threads: {threads_before}")
    print(f"  Thread names: {thread_names_before}")
    if memory_before:
        print(f"  Memory: {memory_before:.1f} MB")
    if fds_before:
        print(f"  File descriptors: {fds_before}")

    yield

    # Get final resource counts
    threads_after = threading.active_count()
    thread_names_after = [t.name for t in threading.enumerate()]

    try:
        import psutil

        process = psutil.Process()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        try:
            fds_after = process.num_fds() if hasattr(process, 'num_fds') else None
        except Exception:
            fds_after = None
    except ImportError:
        memory_after = None
        fds_after = None

    print(f"\n[RESOURCES AFTER {test_name}]")
    print(f"  Threads: {threads_after} (delta: {threads_after - threads_before:+d})")
    print(f"  Thread names: {thread_names_after}")
    if memory_after:
        memory_delta = memory_after - memory_before
        print(f"  Memory: {memory_after:.1f} MB (delta: {memory_delta:+.1f} MB)")
    if fds_after and fds_before:
        fd_delta = fds_after - fds_before
        print(f"  File descriptors: {fds_after} (delta: {fd_delta:+d})")

    # Warn if resources increased significantly
    if threads_after > threads_before:
        print(f"  ⚠️  WARNING: {threads_after - threads_before} thread(s) leaked!")
    if memory_after and memory_before and (memory_after - memory_before) > 50:
        print(f"  ⚠️  WARNING: Memory increased by {memory_after - memory_before:.1f} MB!")
    if fds_after and fds_before and fds_after > fds_before:
        print(f"  ⚠️  WARNING: {fds_after - fds_before} file descriptor(s) leaked!")
