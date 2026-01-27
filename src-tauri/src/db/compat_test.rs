//! Backward compatibility test for existing databases.
//!
//! This test verifies that the Rust database layer can read databases
//! created by the Python backend.
//!
//! Note: These tests must run sequentially (not in parallel) because they
//! share the same database file. Use: cargo test compat_test -- --test-threads=1

#[cfg(test)]
mod tests {
    use crate::db::{Database, favorites, library, library::LibraryQuery, playlists, settings};
    use std::path::Path;
    use std::sync::Mutex;

    const TEST_DB_PATH: &str = "/Users/lance/git/mt/mt.db";

    // Mutex to ensure tests run sequentially
    static TEST_LOCK: Mutex<()> = Mutex::new(());

    fn skip_if_no_db() -> bool {
        !Path::new(TEST_DB_PATH).exists()
    }

    #[test]
    fn test_open_existing_database() {
        let _lock = TEST_LOCK.lock().unwrap();
        if skip_if_no_db() {
            println!("Skipping: test database not found at {}", TEST_DB_PATH);
            return;
        }

        let db = Database::new(TEST_DB_PATH).expect("Failed to open existing database");
        let conn = db.conn().expect("Failed to get connection");

        // Verify we can query the database
        let stats = library::get_library_stats(&conn).expect("Failed to get stats");
        println!("Library stats: {:?}", stats);
        assert!(stats.total_tracks > 0, "Expected tracks in library");
    }

    #[test]
    fn test_read_existing_tracks() {
        let _lock = TEST_LOCK.lock().unwrap();
        if skip_if_no_db() {
            return;
        }

        let db = Database::new(TEST_DB_PATH).expect("Failed to open database");
        let conn = db.conn().expect("Failed to get connection");

        let query = LibraryQuery {
            limit: 10,
            ..Default::default()
        };

        let result = library::get_all_tracks(&conn, &query).expect("Failed to get tracks");
        println!("Found {} tracks (showing first {})", result.total, result.items.len());

        for track in &result.items {
            println!("  - {} by {:?}", track.title.as_deref().unwrap_or("Unknown"), track.artist);
        }

        assert!(!result.items.is_empty(), "Expected some tracks");
    }

    #[test]
    fn test_read_existing_playlists() {
        let _lock = TEST_LOCK.lock().unwrap();
        if skip_if_no_db() {
            return;
        }

        let db = Database::new(TEST_DB_PATH).expect("Failed to open database");
        let conn = db.conn().expect("Failed to get connection");

        let playlist_list = playlists::get_playlists(&conn).expect("Failed to get playlists");
        println!("Found {} playlists", playlist_list.len());

        for playlist in &playlist_list {
            println!("  - {} ({} tracks)", playlist.name, playlist.track_count);
        }
    }

    #[test]
    fn test_read_existing_favorites() {
        let _lock = TEST_LOCK.lock().unwrap();
        if skip_if_no_db() {
            return;
        }

        let db = Database::new(TEST_DB_PATH).expect("Failed to open database");
        let conn = db.conn().expect("Failed to get connection");

        let result = favorites::get_favorites(&conn, 100, 0).expect("Failed to get favorites");
        println!("Found {} favorites", result.total);

        for fav in &result.items {
            println!("  - {} by {:?}", fav.track.title.as_deref().unwrap_or("Unknown"), fav.track.artist);
        }
    }

    #[test]
    fn test_read_existing_settings() {
        let _lock = TEST_LOCK.lock().unwrap();
        if skip_if_no_db() {
            return;
        }

        let db = Database::new(TEST_DB_PATH).expect("Failed to open database");
        let conn = db.conn().expect("Failed to get connection");

        let all_settings = settings::get_all_settings(&conn).expect("Failed to get settings");
        println!("Settings: {:?}", all_settings);

        // Verify defaults are applied
        assert!(all_settings.contains_key("volume"));
    }

    #[test]
    fn test_schema_compatibility() {
        let _lock = TEST_LOCK.lock().unwrap();
        if skip_if_no_db() {
            return;
        }

        let db = Database::new(TEST_DB_PATH).expect("Failed to open database");
        let conn = db.conn().expect("Failed to get connection");

        // Check that all expected columns exist in library table
        let mut stmt = conn.prepare("PRAGMA table_info(library)").unwrap();
        let columns: Vec<String> = stmt
            .query_map([], |row| row.get::<_, String>(1))
            .unwrap()
            .filter_map(|r| r.ok())
            .collect();

        let expected_columns = [
            "id", "filepath", "title", "artist", "album", "album_artist",
            "track_number", "track_total", "date", "duration", "file_size",
            "added_date", "last_played", "play_count",
        ];

        for col in &expected_columns {
            assert!(
                columns.contains(&col.to_string()),
                "Missing column: {}",
                col
            );
        }

        println!("All {} expected columns found in library table", expected_columns.len());
    }
}
