"""Unit tests for watched folders backend functionality."""

import pytest
import tempfile
from backend.services.database import DatabaseService
from pathlib import Path


@pytest.fixture
def backend_db():
    """Create a backend database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = DatabaseService(db_path)
    yield db

    db_path.unlink(missing_ok=True)


@pytest.fixture
def temp_music_dir():
    """Create a temporary directory for testing watched folders."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestWatchedFoldersDatabaseOperations:
    def test_add_watched_folder(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )

        assert folder is not None
        assert folder["path"] == str(temp_music_dir)
        assert folder["mode"] == "continuous"
        assert folder["cadence_minutes"] == 10
        assert folder["enabled"] == 1

    def test_add_watched_folder_with_defaults(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="startup",
            cadence_minutes=None,
            enabled=True,
        )

        assert folder is not None
        assert folder["mode"] == "startup"
        assert folder["cadence_minutes"] is None

    def test_get_watched_folder_by_id(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=15,
            enabled=True,
        )

        folder = backend_db.get_watched_folder(created["id"])

        assert folder is not None
        assert folder["id"] == created["id"]
        assert folder["path"] == str(temp_music_dir)

    def test_get_watched_folder_not_found(self, backend_db):
        folder = backend_db.get_watched_folder(99999)
        assert folder is None

    def test_list_watched_folders_empty(self, backend_db):
        folders = backend_db.get_watched_folders()
        assert isinstance(folders, list)
        assert len(folders) == 0

    def test_list_watched_folders_multiple(self, backend_db):
        with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
            backend_db.add_watched_folder(path=dir1, mode="startup", cadence_minutes=None, enabled=True)
            backend_db.add_watched_folder(path=dir2, mode="continuous", cadence_minutes=5, enabled=False)

            folders = backend_db.get_watched_folders()

            assert len(folders) == 2
            paths = [f["path"] for f in folders]
            assert dir1 in paths
            assert dir2 in paths

    def test_update_watched_folder_mode(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="startup",
            cadence_minutes=None,
            enabled=True,
        )

        updated = backend_db.update_watched_folder(
            folder_id=created["id"],
            mode="continuous",
            cadence_minutes=20,
            enabled=None,
        )

        assert updated["mode"] == "continuous"
        assert updated["cadence_minutes"] == 20
        assert updated["enabled"] == 1

    def test_update_watched_folder_enabled(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )

        updated = backend_db.update_watched_folder(
            folder_id=created["id"],
            mode=None,
            cadence_minutes=None,
            enabled=False,
        )

        assert updated["enabled"] == 0
        assert updated["mode"] == "continuous"
        assert updated["cadence_minutes"] == 10

    def test_update_watched_folder_partial(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )

        updated = backend_db.update_watched_folder(
            folder_id=created["id"],
            mode=None,
            cadence_minutes=30,
            enabled=None,
        )

        assert updated["cadence_minutes"] == 30
        assert updated["mode"] == "continuous"
        assert updated["enabled"] == 1

    def test_remove_watched_folder(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )

        result = backend_db.remove_watched_folder(created["id"])
        assert result is True

        folder = backend_db.get_watched_folder(created["id"])
        assert folder is None

    def test_remove_watched_folder_not_found(self, backend_db):
        result = backend_db.remove_watched_folder(99999)
        assert result is False

    def test_get_enabled_watched_folders(self, backend_db):
        with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2, tempfile.TemporaryDirectory() as dir3:
            backend_db.add_watched_folder(path=dir1, mode="startup", cadence_minutes=None, enabled=True)
            backend_db.add_watched_folder(path=dir2, mode="continuous", cadence_minutes=5, enabled=False)
            backend_db.add_watched_folder(path=dir3, mode="continuous", cadence_minutes=10, enabled=True)

            enabled = backend_db.get_enabled_watched_folders()

            assert len(enabled) == 2
            paths = [f["path"] for f in enabled]
            assert dir1 in paths
            assert dir3 in paths
            assert dir2 not in paths

    def test_update_watched_folder_last_scanned(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )

        assert created.get("last_scanned_at") is None

        result = backend_db.update_watched_folder_last_scanned(created["id"])
        assert result is True

        folder = backend_db.get_watched_folder(created["id"])
        assert folder["last_scanned_at"] is not None


class TestWatchedFoldersModeValidation:
    def test_startup_mode_no_cadence(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="startup",
            cadence_minutes=None,
            enabled=True,
        )

        assert folder["mode"] == "startup"
        assert folder["cadence_minutes"] is None

    def test_continuous_mode_with_cadence(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=15,
            enabled=True,
        )

        assert folder["mode"] == "continuous"
        assert folder["cadence_minutes"] == 15

    def test_cadence_minimum_value(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=1,
            enabled=True,
        )

        assert folder["cadence_minutes"] == 1

    def test_cadence_maximum_value(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=1440,
            enabled=True,
        )

        assert folder["cadence_minutes"] == 1440


class TestWatchedFoldersTimestamps:
    def test_created_at_timestamp(self, backend_db, temp_music_dir):
        folder = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )

        assert "created_at" in folder
        assert folder["created_at"] is not None

    def test_updated_at_on_update(self, backend_db, temp_music_dir):
        import time

        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="startup",
            cadence_minutes=None,
            enabled=True,
        )
        original_updated = created.get("updated_at")

        time.sleep(0.1)

        updated = backend_db.update_watched_folder(
            folder_id=created["id"],
            mode="continuous",
            cadence_minutes=5,
            enabled=None,
        )

        if original_updated is not None:
            assert updated["updated_at"] >= original_updated


class TestWatchedFoldersMultipleOperations:
    def test_add_remove_readd_folder(self, backend_db, temp_music_dir):
        folder1 = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="continuous",
            cadence_minutes=10,
            enabled=True,
        )
        folder1_id = folder1["id"]

        backend_db.remove_watched_folder(folder1_id)

        folder2 = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="startup",
            cadence_minutes=None,
            enabled=True,
        )

        assert folder2["id"] != folder1_id
        assert folder2["mode"] == "startup"

    def test_update_multiple_fields_atomically(self, backend_db, temp_music_dir):
        created = backend_db.add_watched_folder(
            path=str(temp_music_dir),
            mode="startup",
            cadence_minutes=None,
            enabled=True,
        )

        updated = backend_db.update_watched_folder(
            folder_id=created["id"],
            mode="continuous",
            cadence_minutes=30,
            enabled=False,
        )

        assert updated["mode"] == "continuous"
        assert updated["cadence_minutes"] == 30
        assert updated["enabled"] == 0
