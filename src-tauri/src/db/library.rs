//! Library database operations.
//!
//! CRUD operations for the music library (tracks table).

use rusqlite::{params, Connection, Row};
use std::collections::{HashMap, HashSet};
use std::path::Path;

use crate::db::{
    DbResult, FileFingerprint, LibrarySortColumn, LibraryStats, PaginatedResult, SortOrder, Track,
    TrackMetadata,
};

/// Map a database row to a Track struct
fn row_to_track(row: &Row) -> rusqlite::Result<Track> {
    Ok(Track {
        id: row.get("id")?,
        filepath: row.get("filepath")?,
        title: row.get("title")?,
        artist: row.get("artist")?,
        album: row.get("album")?,
        album_artist: row.get("album_artist")?,
        track_number: row.get("track_number")?,
        track_total: row.get("track_total")?,
        date: row.get("date")?,
        duration: row.get("duration")?,
        file_size: row.get::<_, Option<i64>>("file_size")?.unwrap_or(0),
        file_mtime_ns: row.get("file_mtime_ns")?,
        added_date: row.get("added_date")?,
        last_played: row.get("last_played")?,
        play_count: row.get::<_, Option<i64>>("play_count")?.unwrap_or(0),
        missing: row.get::<_, Option<i64>>("missing")?.unwrap_or(0) != 0,
        last_seen_at: row.get("last_seen_at")?,
    })
}

/// Library query parameters
#[derive(Debug, Clone, Default)]
pub struct LibraryQuery {
    pub search: Option<String>,
    pub artist: Option<String>,
    pub album: Option<String>,
    pub sort_by: LibrarySortColumn,
    pub sort_order: SortOrder,
    pub limit: i64,
    pub offset: i64,
}

impl LibraryQuery {
    pub fn new() -> Self {
        Self {
            limit: 100,
            ..Default::default()
        }
    }
}

/// Get tracks from the library with filtering and pagination
pub fn get_all_tracks(conn: &Connection, query: &LibraryQuery) -> DbResult<PaginatedResult<Track>> {
    let mut conditions = Vec::new();
    let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

    if let Some(search) = &query.search {
        conditions.push("(title LIKE ? OR artist LIKE ? OR album LIKE ?)");
        let search_term = format!("%{}%", search);
        params_vec.push(Box::new(search_term.clone()));
        params_vec.push(Box::new(search_term.clone()));
        params_vec.push(Box::new(search_term));
    }

    if let Some(artist) = &query.artist {
        conditions.push("artist = ?");
        params_vec.push(Box::new(artist.clone()));
    }

    if let Some(album) = &query.album {
        conditions.push("album = ?");
        params_vec.push(Box::new(album.clone()));
    }

    let where_clause = if conditions.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", conditions.join(" AND "))
    };

    // Get total count
    let count_sql = format!("SELECT COUNT(*) FROM library {}", where_clause);
    let params_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();
    let total: i64 = conn.query_row(&count_sql, params_refs.as_slice(), |row| row.get(0))?;

    // Get tracks
    let sql = format!(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns
         FROM library
         {}
         ORDER BY {} {}
         LIMIT ? OFFSET ?",
        where_clause,
        query.sort_by.as_sql(),
        query.sort_order.as_sql()
    );

    let mut all_params: Vec<&dyn rusqlite::ToSql> = params_refs;
    all_params.push(&query.limit);
    all_params.push(&query.offset);

    let mut stmt = conn.prepare(&sql)?;
    let tracks: Vec<Track> = stmt
        .query_map(all_params.as_slice(), row_to_track)?
        .filter_map(|r| r.ok())
        .collect();

    Ok(PaginatedResult {
        items: tracks,
        total,
    })
}

/// Get a single track by ID
pub fn get_track_by_id(conn: &Connection, track_id: i64) -> DbResult<Option<Track>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns
         FROM library WHERE id = ?",
    )?;

    match stmt.query_row([track_id], row_to_track) {
        Ok(track) => Ok(Some(track)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Get a track by filepath
pub fn get_track_by_filepath(conn: &Connection, filepath: &str) -> DbResult<Option<Track>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns
         FROM library WHERE filepath = ?",
    )?;

    match stmt.query_row([filepath], row_to_track) {
        Ok(track) => Ok(Some(track)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Check which filepaths already exist in the library
pub fn get_existing_filepaths(conn: &Connection, filepaths: &[String]) -> DbResult<HashSet<String>> {
    if filepaths.is_empty() {
        return Ok(HashSet::new());
    }

    let placeholders = filepaths.iter().map(|_| "?").collect::<Vec<_>>().join(",");
    let sql = format!(
        "SELECT filepath FROM library WHERE filepath IN ({})",
        placeholders
    );

    let mut stmt = conn.prepare(&sql)?;
    let params: Vec<&dyn rusqlite::ToSql> = filepaths.iter().map(|s| s as &dyn rusqlite::ToSql).collect();

    let existing: HashSet<String> = stmt
        .query_map(params.as_slice(), |row| row.get::<_, String>(0))?
        .filter_map(|r| r.ok())
        .collect();

    Ok(existing)
}

/// Get fingerprints for all tracks (filepath, mtime, size)
pub fn get_all_fingerprints(conn: &Connection) -> DbResult<HashMap<String, FileFingerprint>> {
    let mut stmt = conn.prepare("SELECT filepath, file_mtime_ns, file_size FROM library")?;

    let fingerprints: HashMap<String, FileFingerprint> = stmt
        .query_map([], |row| {
            Ok(FileFingerprint {
                filepath: row.get(0)?,
                file_mtime_ns: row.get(1)?,
                file_size: row.get::<_, Option<i64>>(2)?.unwrap_or(0),
            })
        })?
        .filter_map(|r| r.ok())
        .map(|fp| (fp.filepath.clone(), fp))
        .collect();

    Ok(fingerprints)
}

/// Add a track to the library
pub fn add_track(conn: &Connection, filepath: &str, metadata: &TrackMetadata) -> DbResult<i64> {
    conn.execute(
        "INSERT INTO library
         (filepath, title, artist, album, album_artist,
          track_number, track_total, date, duration, file_size, file_mtime_ns)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        params![
            filepath,
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.album_artist,
            metadata.track_number,
            metadata.track_total,
            metadata.date,
            metadata.duration,
            metadata.file_size.unwrap_or(0),
            metadata.file_mtime_ns,
        ],
    )?;

    Ok(conn.last_insert_rowid())
}

/// Add multiple tracks in a single transaction
pub fn add_tracks_bulk(
    conn: &Connection,
    tracks: &[(String, TrackMetadata)],
) -> DbResult<i64> {
    if tracks.is_empty() {
        return Ok(0);
    }

    let mut stmt = conn.prepare(
        "INSERT INTO library
         (filepath, title, artist, album, album_artist,
          track_number, track_total, date, duration, file_size, file_mtime_ns)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    )?;

    let mut count = 0;
    for (filepath, metadata) in tracks {
        stmt.execute(params![
            filepath,
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.album_artist,
            metadata.track_number,
            metadata.track_total,
            metadata.date,
            metadata.duration,
            metadata.file_size.unwrap_or(0),
            metadata.file_mtime_ns,
        ])?;
        count += 1;
    }

    Ok(count)
}

/// Update multiple tracks in a single transaction
pub fn update_tracks_bulk(
    conn: &Connection,
    tracks: &[(String, TrackMetadata)],
) -> DbResult<i64> {
    if tracks.is_empty() {
        return Ok(0);
    }

    let mut stmt = conn.prepare(
        "UPDATE library SET
            title = ?,
            artist = ?,
            album = ?,
            album_artist = ?,
            track_number = ?,
            track_total = ?,
            date = ?,
            duration = ?,
            file_size = ?,
            file_mtime_ns = ?
         WHERE filepath = ?",
    )?;

    let mut count = 0;
    for (filepath, metadata) in tracks {
        let rows = stmt.execute(params![
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.album_artist,
            metadata.track_number,
            metadata.track_total,
            metadata.date,
            metadata.duration,
            metadata.file_size.unwrap_or(0),
            metadata.file_mtime_ns,
            filepath,
        ])?;
        count += rows as i64;
    }

    Ok(count)
}

/// Delete multiple tracks by filepath
pub fn delete_tracks_bulk(conn: &Connection, filepaths: &[String]) -> DbResult<i64> {
    if filepaths.is_empty() {
        return Ok(0);
    }

    let placeholders = filepaths.iter().map(|_| "?").collect::<Vec<_>>().join(",");
    let params: Vec<&dyn rusqlite::ToSql> = filepaths.iter().map(|s| s as &dyn rusqlite::ToSql).collect();

    // Delete from favorites first
    let sql = format!(
        "DELETE FROM favorites
         WHERE track_id IN (SELECT id FROM library WHERE filepath IN ({}))",
        placeholders
    );
    conn.execute(&sql, params.as_slice())?;

    // Delete from playlist_items
    let sql = format!(
        "DELETE FROM playlist_items
         WHERE track_id IN (SELECT id FROM library WHERE filepath IN ({}))",
        placeholders
    );
    conn.execute(&sql, params.as_slice())?;

    // Delete tracks
    let sql = format!("DELETE FROM library WHERE filepath IN ({})", placeholders);
    let deleted = conn.execute(&sql, params.as_slice())?;

    Ok(deleted as i64)
}

/// Delete a track by ID
pub fn delete_track(conn: &Connection, track_id: i64) -> DbResult<bool> {
    conn.execute("DELETE FROM favorites WHERE track_id = ?", [track_id])?;
    conn.execute("DELETE FROM playlist_items WHERE track_id = ?", [track_id])?;
    let deleted = conn.execute("DELETE FROM library WHERE id = ?", [track_id])?;
    Ok(deleted > 0)
}

/// Update track metadata by ID
pub fn update_track_metadata(
    conn: &Connection,
    track_id: i64,
    metadata: &TrackMetadata,
) -> DbResult<bool> {
    let updated = conn.execute(
        "UPDATE library SET
            title = ?,
            artist = ?,
            album = ?,
            album_artist = ?,
            track_number = ?,
            track_total = ?,
            date = ?,
            duration = ?,
            file_size = ?,
            file_mtime_ns = ?
         WHERE id = ?",
        params![
            metadata.title,
            metadata.artist,
            metadata.album,
            metadata.album_artist,
            metadata.track_number,
            metadata.track_total,
            metadata.date,
            metadata.duration,
            metadata.file_size.unwrap_or(0),
            metadata.file_mtime_ns,
            track_id,
        ],
    )?;

    Ok(updated > 0)
}

/// Increment play count for a track
pub fn update_play_count(conn: &Connection, track_id: i64) -> DbResult<Option<Track>> {
    conn.execute(
        "UPDATE library SET
            play_count = play_count + 1,
            last_played = CURRENT_TIMESTAMP
         WHERE id = ?",
        [track_id],
    )?;

    get_track_by_id(conn, track_id)
}

/// Get library statistics
pub fn get_library_stats(conn: &Connection) -> DbResult<LibraryStats> {
    let total_tracks: i64 =
        conn.query_row("SELECT COUNT(*) FROM library", [], |row| row.get(0))?;

    // Duration is stored as REAL, so read as f64 and convert
    let total_duration: i64 = conn.query_row(
        "SELECT COALESCE(SUM(duration), 0) FROM library",
        [],
        |row| row.get::<_, f64>(0).map(|v| v as i64),
    )?;

    let total_size: i64 = conn.query_row(
        "SELECT COALESCE(SUM(file_size), 0) FROM library",
        [],
        |row| row.get(0),
    )?;

    let total_artists: i64 = conn.query_row(
        "SELECT COUNT(DISTINCT artist) FROM library WHERE artist IS NOT NULL",
        [],
        |row| row.get(0),
    )?;

    let total_albums: i64 = conn.query_row(
        "SELECT COUNT(DISTINCT album) FROM library WHERE album IS NOT NULL",
        [],
        |row| row.get(0),
    )?;

    Ok(LibraryStats {
        total_tracks,
        total_duration,
        total_size,
        total_artists,
        total_albums,
    })
}

/// Update file sizes for tracks with file_size = 0
pub fn update_file_sizes(conn: &Connection) -> DbResult<i64> {
    let mut stmt =
        conn.prepare("SELECT id, filepath FROM library WHERE file_size = 0 OR file_size IS NULL")?;

    let tracks: Vec<(i64, String)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?
        .filter_map(|r| r.ok())
        .collect();

    let mut updated = 0;
    for (id, filepath) in tracks {
        if let Ok(metadata) = std::fs::metadata(&filepath) {
            let size = metadata.len() as i64;
            conn.execute("UPDATE library SET file_size = ? WHERE id = ?", [size, id])?;
            updated += 1;
        }
    }

    Ok(updated)
}

/// Mark a track as missing by ID
pub fn mark_track_missing(conn: &Connection, track_id: i64) -> DbResult<bool> {
    let updated = conn.execute("UPDATE library SET missing = 1 WHERE id = ?", [track_id])?;
    Ok(updated > 0)
}

/// Mark a track as missing by filepath
pub fn mark_track_missing_by_filepath(conn: &Connection, filepath: &str) -> DbResult<bool> {
    let updated = conn.execute("UPDATE library SET missing = 1 WHERE filepath = ?", [filepath])?;
    Ok(updated > 0)
}

/// Mark a track as present
pub fn mark_track_present(conn: &Connection, track_id: i64) -> DbResult<bool> {
    let updated = conn.execute(
        "UPDATE library SET missing = 0, last_seen_at = strftime('%s','now') WHERE id = ?",
        [track_id],
    )?;
    Ok(updated > 0)
}

/// Update track filepath
pub fn update_track_filepath(conn: &Connection, track_id: i64, new_path: &str) -> DbResult<bool> {
    let updated = conn.execute(
        "UPDATE library SET filepath = ?, missing = 0, last_seen_at = strftime('%s','now') WHERE id = ?",
        params![new_path, track_id],
    )?;
    Ok(updated > 0)
}

/// Get all missing tracks
pub fn get_missing_tracks(conn: &Connection) -> DbResult<Vec<Track>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns
         FROM library WHERE missing = 1 ORDER BY title ASC",
    )?;

    let tracks: Vec<Track> = stmt
        .query_map([], row_to_track)?
        .filter_map(|r| r.ok())
        .collect();

    Ok(tracks)
}

/// Check and update track status based on file existence
pub fn check_and_update_track_status(conn: &Connection, track_id: i64) -> DbResult<Option<Track>> {
    let track = get_track_by_id(conn, track_id)?;

    if let Some(ref t) = track {
        let exists = Path::new(&t.filepath).exists();
        if exists && t.missing {
            mark_track_present(conn, track_id)?;
        } else if !exists && !t.missing {
            mark_track_missing(conn, track_id)?;
        }
    }

    get_track_by_id(conn, track_id)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::schema::{create_tables, run_migrations};

    fn setup_test_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        create_tables(&conn).unwrap();
        run_migrations(&conn).unwrap();
        conn
    }

    #[test]
    fn test_add_and_get_track() {
        let conn = setup_test_db();

        let metadata = TrackMetadata {
            title: Some("Test Song".to_string()),
            artist: Some("Test Artist".to_string()),
            album: Some("Test Album".to_string()),
            duration: Some(180.5),
            ..Default::default()
        };

        let id = add_track(&conn, "/music/test.mp3", &metadata).unwrap();
        assert!(id > 0);

        let track = get_track_by_id(&conn, id).unwrap().unwrap();
        assert_eq!(track.title, Some("Test Song".to_string()));
        assert_eq!(track.artist, Some("Test Artist".to_string()));
    }

    #[test]
    fn test_get_track_by_filepath() {
        let conn = setup_test_db();

        let metadata = TrackMetadata {
            title: Some("Test Song".to_string()),
            ..Default::default()
        };

        add_track(&conn, "/music/test.mp3", &metadata).unwrap();

        let track = get_track_by_filepath(&conn, "/music/test.mp3")
            .unwrap()
            .unwrap();
        assert_eq!(track.title, Some("Test Song".to_string()));

        let not_found = get_track_by_filepath(&conn, "/music/nonexistent.mp3").unwrap();
        assert!(not_found.is_none());
    }

    #[test]
    fn test_bulk_operations() {
        let conn = setup_test_db();

        let tracks: Vec<(String, TrackMetadata)> = (1..=5)
            .map(|i| {
                (
                    format!("/music/track{}.mp3", i),
                    TrackMetadata {
                        title: Some(format!("Track {}", i)),
                        artist: Some("Test Artist".to_string()),
                        ..Default::default()
                    },
                )
            })
            .collect();

        let added = add_tracks_bulk(&conn, &tracks).unwrap();
        assert_eq!(added, 5);

        let stats = get_library_stats(&conn).unwrap();
        assert_eq!(stats.total_tracks, 5);
    }

    #[test]
    fn test_update_play_count() {
        let conn = setup_test_db();

        let metadata = TrackMetadata {
            title: Some("Test".to_string()),
            ..Default::default()
        };
        let id = add_track(&conn, "/music/test.mp3", &metadata).unwrap();

        let track = update_play_count(&conn, id).unwrap().unwrap();
        assert_eq!(track.play_count, 1);
        assert!(track.last_played.is_some());

        let track = update_play_count(&conn, id).unwrap().unwrap();
        assert_eq!(track.play_count, 2);
    }

    #[test]
    fn test_library_query() {
        let conn = setup_test_db();

        for i in 1..=20 {
            let metadata = TrackMetadata {
                title: Some(format!("Track {}", i)),
                artist: Some(if i <= 10 {
                    "Artist A".to_string()
                } else {
                    "Artist B".to_string()
                }),
                ..Default::default()
            };
            add_track(&conn, &format!("/music/track{}.mp3", i), &metadata).unwrap();
        }

        // Test pagination
        let query = LibraryQuery {
            limit: 5,
            offset: 0,
            ..Default::default()
        };
        let result = get_all_tracks(&conn, &query).unwrap();
        assert_eq!(result.items.len(), 5);
        assert_eq!(result.total, 20);

        // Test artist filter
        let query = LibraryQuery {
            artist: Some("Artist A".to_string()),
            limit: 100,
            ..Default::default()
        };
        let result = get_all_tracks(&conn, &query).unwrap();
        assert_eq!(result.total, 10);
    }
}
