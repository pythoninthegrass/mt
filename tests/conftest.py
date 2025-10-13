import glob
import os
import pytest
import shutil
import subprocess
import sys
import time
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
    """Provide paths to test music files from Dropbox directory.

    Returns:
        List of paths to MP3/M4A files for testing
    """
    music_dir = '/Users/lance/Library/CloudStorage/Dropbox/mt/music'

    # Find MP3 and M4A files
    mp3_files = glob.glob(f"{music_dir}/**/*.mp3", recursive=True)
    m4a_files = glob.glob(f"{music_dir}/**/*.m4a", recursive=True)

    all_files = mp3_files + m4a_files

    # Return first 10 files for testing
    return all_files[:10]


@pytest.fixture(scope="session")
def app_process():
    """Start the mt application with API server enabled.

    Yields:
        subprocess.Popen: The running application process
    """
    # Use a test database to avoid polluting the main one
    db_path = project_root / "mt.db"
    test_db_path = project_root / "mt_test.db"
    backup_path = project_root / "mt.db.backup"

    # Backup the main database
    if db_path.exists():
        shutil.copy(db_path, backup_path)

    # Create test database by copying main database and clearing queue
    if test_db_path.exists():
        test_db_path.unlink()

    if db_path.exists():
        import sqlite3

        # Copy entire database
        shutil.copy(db_path, test_db_path)

        # Clear the queue table
        conn = sqlite3.connect(test_db_path)
        conn.execute("DELETE FROM queue")
        conn.commit()
        conn.close()

    # Set environment variables for testing
    env = setup_macos_environment()
    env['MT_API_SERVER_ENABLED'] = 'true'
    env['MT_API_SERVER_PORT'] = '5555'
    env['MT_RELOAD'] = 'false'  # Disable auto-reload during tests
    env['DB_NAME'] = 'mt_test.db'  # Use test database

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

    # Remove test database
    if test_db_path.exists():
        test_db_path.unlink()

    # Restore the main database backup
    if backup_path.exists():
        shutil.move(backup_path, db_path)


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


@pytest.fixture
def clean_queue(api_client):
    """Clear the queue and reset application state before and after each test.

    Resets the following stateful variables to ensure test isolation:
    - Queue content (cleared)
    - VLC media player state (stopped if playing, media cleared)
    - Current view (reset to 'queue')
    - Loop state (disabled)
    - Shuffle state (disabled)
    - Volume (set to 80%)

    Args:
        api_client: Connected API client
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

            # Disable loop if enabled
            if status_data.get('loop_enabled', False):
                with suppress(Exception):
                    api_client.send('toggle_loop')

            # Disable shuffle if enabled
            if status_data.get('shuffle_enabled', False):
                with suppress(Exception):
                    api_client.send('toggle_shuffle')

        # Reset view to 'queue' (now_playing view)
        with suppress(Exception):
            api_client.send('switch_view', view='queue')

        # Set volume to consistent level (80%)
        with suppress(Exception):
            api_client.send('set_volume', volume=80)

    # Reset state before test
    reset_state()

    yield

    # Reset state after test
    reset_state()
