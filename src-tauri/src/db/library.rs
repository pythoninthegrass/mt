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
        file_inode: row.get("file_inode")?,
        content_hash: row.get("content_hash")?,
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
                file_mtime_ns, file_inode, content_hash
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
                file_mtime_ns, file_inode, content_hash
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
                file_mtime_ns, file_inode, content_hash
         FROM library WHERE filepath = ?",
    )?;

    match stmt.query_row([filepath], row_to_track) {
        Ok(track) => Ok(Some(track)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Check which filepaths already exist in the library
pub fn get_existing_filepaths(
    conn: &Connection,
    filepaths: &[String],
) -> DbResult<HashSet<String>> {
    if filepaths.is_empty() {
        return Ok(HashSet::new());
    }

    let placeholders = filepaths.iter().map(|_| "?").collect::<Vec<_>>().join(",");
    let sql = format!(
        "SELECT filepath FROM library WHERE filepath IN ({})",
        placeholders
    );

    let mut stmt = conn.prepare(&sql)?;
    let params: Vec<&dyn rusqlite::ToSql> = filepaths
        .iter()
        .map(|s| s as &dyn rusqlite::ToSql)
        .collect();

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
          track_number, track_total, date, duration, file_size, file_mtime_ns,
          file_inode, content_hash)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            metadata.file_inode.map(|v| v as i64),
            metadata.content_hash,
        ],
    )?;

    Ok(conn.last_insert_rowid())
}

/// Add multiple tracks in a single transaction
pub fn add_tracks_bulk(conn: &Connection, tracks: &[(String, TrackMetadata)]) -> DbResult<i64> {
    if tracks.is_empty() {
        return Ok(0);
    }

    let mut stmt = conn.prepare(
        "INSERT INTO library
         (filepath, title, artist, album, album_artist,
          track_number, track_total, date, duration, file_size, file_mtime_ns,
          file_inode, content_hash)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            metadata.file_inode.map(|v| v as i64),
            metadata.content_hash,
        ])?;
        count += 1;
    }

    Ok(count)
}

/// Update multiple tracks in a single transaction
pub fn update_tracks_bulk(conn: &Connection, tracks: &[(String, TrackMetadata)]) -> DbResult<i64> {
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
    let params: Vec<&dyn rusqlite::ToSql> = filepaths
        .iter()
        .map(|s| s as &dyn rusqlite::ToSql)
        .collect();

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
    let total_tracks: i64 = conn.query_row("SELECT COUNT(*) FROM library", [], |row| row.get(0))?;

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
    let updated = conn.execute(
        "UPDATE library SET missing = 1 WHERE filepath = ?",
        [filepath],
    )?;
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
                file_mtime_ns, file_inode, content_hash
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

pub fn find_missing_track_by_inode(conn: &Connection, inode: u64) -> DbResult<Option<Track>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns, file_inode, content_hash
         FROM library WHERE file_inode = ? AND missing = 1 LIMIT 1",
    )?;

    match stmt.query_row([inode as i64], row_to_track) {
        Ok(track) => Ok(Some(track)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

pub fn find_missing_track_by_content_hash(
    conn: &Connection,
    content_hash: &str,
) -> DbResult<Option<Track>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns, file_inode, content_hash
         FROM library WHERE content_hash = ? AND missing = 1 LIMIT 1",
    )?;

    match stmt.query_row([content_hash], row_to_track) {
        Ok(track) => Ok(Some(track)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

pub fn reconcile_moved_track(
    conn: &Connection,
    track_id: i64,
    new_filepath: &str,
    new_inode: Option<u64>,
) -> DbResult<Option<Track>> {
    conn.execute(
        "UPDATE library SET
            filepath = ?,
            file_inode = ?,
            missing = 0,
            last_seen_at = strftime('%s','now')
         WHERE id = ?",
        params![new_filepath, new_inode.map(|v| v as i64), track_id],
    )?;

    get_track_by_id(conn, track_id)
}

/// Track info for fingerprint backfill (minimal struct to reduce memory)
#[derive(Debug)]
pub struct TrackForBackfill {
    pub id: i64,
    pub filepath: String,
}

/// Get tracks that need fingerprint backfill (missing inode or content_hash)
pub fn get_tracks_needing_fingerprints(conn: &Connection) -> DbResult<Vec<TrackForBackfill>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath FROM library
         WHERE (file_inode IS NULL OR content_hash IS NULL) AND missing = 0",
    )?;

    let tracks: Vec<TrackForBackfill> = stmt
        .query_map([], |row| {
            Ok(TrackForBackfill {
                id: row.get(0)?,
                filepath: row.get(1)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(tracks)
}

/// Update a track's fingerprint (inode and content_hash)
pub fn update_track_fingerprints(
    conn: &Connection,
    track_id: i64,
    inode: Option<u64>,
    content_hash: Option<&str>,
) -> DbResult<bool> {
    let updated = conn.execute(
        "UPDATE library SET file_inode = ?, content_hash = ? WHERE id = ?",
        params![inode.map(|v| v as i64), content_hash, track_id],
    )?;
    Ok(updated > 0)
}

/// Duplicate track info for merge decisions
#[derive(Debug)]
pub struct DuplicateCandidate {
    pub id: i64,
    pub filepath: String,
    pub missing: bool,
    pub play_count: i64,
    pub added_date: Option<String>,
}

/// Find duplicate tracks by inode (tracks with same inode)
pub fn find_duplicates_by_inode(conn: &Connection) -> DbResult<Vec<Vec<DuplicateCandidate>>> {
    // Find inodes that appear more than once
    let mut stmt = conn.prepare(
        "SELECT file_inode FROM library
         WHERE file_inode IS NOT NULL
         GROUP BY file_inode
         HAVING COUNT(*) > 1",
    )?;

    let duplicate_inodes: Vec<i64> = stmt
        .query_map([], |row| row.get(0))?
        .filter_map(|r| r.ok())
        .collect();

    let mut result = Vec::new();

    for inode in duplicate_inodes {
        let mut stmt = conn.prepare(
            "SELECT id, filepath, missing, play_count, added_date
             FROM library WHERE file_inode = ?
             ORDER BY missing ASC, added_date ASC",
        )?;

        let candidates: Vec<DuplicateCandidate> = stmt
            .query_map([inode], |row| {
                Ok(DuplicateCandidate {
                    id: row.get(0)?,
                    filepath: row.get(1)?,
                    missing: row.get::<_, Option<i64>>(2)?.unwrap_or(0) != 0,
                    play_count: row.get::<_, Option<i64>>(3)?.unwrap_or(0),
                    added_date: row.get(4)?,
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        if candidates.len() > 1 {
            result.push(candidates);
        }
    }

    Ok(result)
}

/// Find duplicate tracks by content_hash (tracks with same hash)
pub fn find_duplicates_by_content_hash(
    conn: &Connection,
) -> DbResult<Vec<Vec<DuplicateCandidate>>> {
    // Find content hashes that appear more than once
    let mut stmt = conn.prepare(
        "SELECT content_hash FROM library
         WHERE content_hash IS NOT NULL
         GROUP BY content_hash
         HAVING COUNT(*) > 1",
    )?;

    let duplicate_hashes: Vec<String> = stmt
        .query_map([], |row| row.get(0))?
        .filter_map(|r| r.ok())
        .collect();

    let mut result = Vec::new();

    for hash in duplicate_hashes {
        let mut stmt = conn.prepare(
            "SELECT id, filepath, missing, play_count, added_date
             FROM library WHERE content_hash = ?
             ORDER BY missing ASC, added_date ASC",
        )?;

        let candidates: Vec<DuplicateCandidate> = stmt
            .query_map([&hash], |row| {
                Ok(DuplicateCandidate {
                    id: row.get(0)?,
                    filepath: row.get(1)?,
                    missing: row.get::<_, Option<i64>>(2)?.unwrap_or(0) != 0,
                    play_count: row.get::<_, Option<i64>>(3)?.unwrap_or(0),
                    added_date: row.get(4)?,
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        if candidates.len() > 1 {
            result.push(candidates);
        }
    }

    Ok(result)
}

/// Merge duplicate tracks: transfer metadata from source to target, then delete source
/// Preserves: play_count (summed), favorites, playlist memberships
pub fn merge_duplicate_tracks(conn: &Connection, keep_id: i64, delete_id: i64) -> DbResult<bool> {
    // Sum play counts
    conn.execute(
        "UPDATE library SET play_count = play_count + (
            SELECT COALESCE(play_count, 0) FROM library WHERE id = ?
        ) WHERE id = ?",
        params![delete_id, keep_id],
    )?;

    // Transfer favorites (ignore if already exists)
    conn.execute(
        "INSERT OR IGNORE INTO favorites (track_id, added_at)
         SELECT ?, added_at FROM favorites WHERE track_id = ?",
        params![keep_id, delete_id],
    )?;

    // Transfer playlist items (update track_id, ignore if duplicate position)
    conn.execute(
        "UPDATE OR IGNORE playlist_items SET track_id = ? WHERE track_id = ?",
        params![keep_id, delete_id],
    )?;

    // Delete remaining playlist items for the duplicate
    conn.execute("DELETE FROM playlist_items WHERE track_id = ?", [delete_id])?;

    // Delete favorites for the duplicate
    conn.execute("DELETE FROM favorites WHERE track_id = ?", [delete_id])?;

    // Delete the duplicate track
    let deleted = conn.execute("DELETE FROM library WHERE id = ?", [delete_id])?;

    Ok(deleted > 0)
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

    // ===== Move Detection Tests (TDD) =====

    #[test]
    fn test_find_missing_track_by_inode() {
        let conn = setup_test_db();

        // Add a track with an inode
        let metadata = TrackMetadata {
            title: Some("Moved Song".to_string()),
            artist: Some("Test Artist".to_string()),
            file_inode: Some(12345),
            ..Default::default()
        };
        let original_id = add_track(&conn, "/music/old/song.mp3", &metadata).unwrap();

        // Mark track as missing (simulating file disappearance)
        mark_track_missing_by_filepath(&conn, "/music/old/song.mp3").unwrap();

        // Should find the missing track by inode
        let found = find_missing_track_by_inode(&conn, 12345).unwrap();
        assert!(found.is_some(), "Should find missing track by inode");
        let found_track = found.unwrap();
        assert_eq!(found_track.id, original_id);
        assert_eq!(found_track.title, Some("Moved Song".to_string()));
        assert!(found_track.missing, "Track should be marked as missing");
    }

    #[test]
    fn test_find_missing_track_by_inode_not_missing() {
        let conn = setup_test_db();

        // Add a track with an inode (NOT missing)
        let metadata = TrackMetadata {
            title: Some("Present Song".to_string()),
            file_inode: Some(99999),
            ..Default::default()
        };
        add_track(&conn, "/music/present.mp3", &metadata).unwrap();

        // Should NOT find the track because it's not missing
        let found = find_missing_track_by_inode(&conn, 99999).unwrap();
        assert!(found.is_none(), "Should not find non-missing track");
    }

    #[test]
    fn test_find_missing_track_by_content_hash() {
        let conn = setup_test_db();

        // Add a track with a content hash
        let metadata = TrackMetadata {
            title: Some("Cross-Volume Song".to_string()),
            artist: Some("Hash Artist".to_string()),
            content_hash: Some("sha256:abc123def456".to_string()),
            file_inode: Some(11111), // Different inode won't match after cross-volume move
            ..Default::default()
        };
        let original_id = add_track(&conn, "/volume1/music/song.mp3", &metadata).unwrap();

        // Mark as missing
        mark_track_missing_by_filepath(&conn, "/volume1/music/song.mp3").unwrap();

        // Should find by content hash (fallback when inode doesn't match)
        let found = find_missing_track_by_content_hash(&conn, "sha256:abc123def456").unwrap();
        assert!(found.is_some(), "Should find missing track by content hash");
        let found_track = found.unwrap();
        assert_eq!(found_track.id, original_id);
        assert_eq!(found_track.title, Some("Cross-Volume Song".to_string()));
    }

    #[test]
    fn test_reconcile_moved_track_updates_filepath_preserves_metadata() {
        let conn = setup_test_db();

        // Add a track with play count and other metadata
        let metadata = TrackMetadata {
            title: Some("Favorite Song".to_string()),
            artist: Some("Beloved Artist".to_string()),
            file_inode: Some(77777),
            ..Default::default()
        };
        let original_id = add_track(&conn, "/music/old/favorite.mp3", &metadata).unwrap();

        // Simulate user played the track multiple times
        update_play_count(&conn, original_id).unwrap();
        update_play_count(&conn, original_id).unwrap();
        update_play_count(&conn, original_id).unwrap();

        // Mark as missing (file moved)
        mark_track_missing_by_filepath(&conn, "/music/old/favorite.mp3").unwrap();

        // Reconcile: update filepath to new location, clear missing flag, update inode
        let new_inode = 88888u64;
        let reconciled = reconcile_moved_track(
            &conn,
            original_id,
            "/music/new/favorite.mp3",
            Some(new_inode),
        )
        .unwrap();

        assert!(reconciled.is_some(), "Should return reconciled track");
        let track = reconciled.unwrap();

        // Verify filepath updated
        assert_eq!(track.filepath, "/music/new/favorite.mp3");

        // Verify metadata preserved
        assert_eq!(track.id, original_id, "ID should be preserved");
        assert_eq!(track.title, Some("Favorite Song".to_string()));
        assert_eq!(track.artist, Some("Beloved Artist".to_string()));
        assert_eq!(track.play_count, 3, "Play count should be preserved");

        // Verify no longer missing
        assert!(!track.missing, "Track should no longer be missing");

        // Verify inode updated
        assert_eq!(track.file_inode, Some(new_inode as i64));

        // Verify old path no longer exists
        let old_path = get_track_by_filepath(&conn, "/music/old/favorite.mp3").unwrap();
        assert!(old_path.is_none(), "Old path should not exist");

        // Verify new path works
        let new_path = get_track_by_filepath(&conn, "/music/new/favorite.mp3").unwrap();
        assert!(new_path.is_some(), "New path should exist");
    }

    #[test]
    fn test_move_detection_prioritizes_inode_over_hash() {
        let conn = setup_test_db();

        // Two tracks with same content hash but different inodes
        let metadata1 = TrackMetadata {
            title: Some("Original".to_string()),
            file_inode: Some(11111),
            content_hash: Some("sha256:samehash".to_string()),
            ..Default::default()
        };
        let metadata2 = TrackMetadata {
            title: Some("Duplicate".to_string()),
            file_inode: Some(22222),
            content_hash: Some("sha256:samehash".to_string()),
            ..Default::default()
        };

        let id1 = add_track(&conn, "/music/original.mp3", &metadata1).unwrap();
        let _id2 = add_track(&conn, "/music/duplicate.mp3", &metadata2).unwrap();

        // Mark first as missing
        mark_track_missing_by_filepath(&conn, "/music/original.mp3").unwrap();

        // Inode match should return the correct track
        let found_by_inode = find_missing_track_by_inode(&conn, 11111).unwrap();
        assert!(found_by_inode.is_some());
        assert_eq!(found_by_inode.unwrap().id, id1);
    }

    #[test]
    fn test_full_move_detection_cycle_no_duplicates() {
        let conn = setup_test_db();

        let original_metadata = TrackMetadata {
            title: Some("My Favorite Song".to_string()),
            artist: Some("Artist Name".to_string()),
            album: Some("Album Name".to_string()),
            file_inode: Some(12345),
            content_hash: Some("sha256:abc123def456".to_string()),
            ..Default::default()
        };
        let original_id = add_track(&conn, "/music/old/song.mp3", &original_metadata).unwrap();

        let original_count: i64 = conn
            .query_row("SELECT COUNT(*) FROM library", [], |row| row.get(0))
            .unwrap();
        assert_eq!(original_count, 1);

        mark_track_missing_by_filepath(&conn, "/music/old/song.mp3").unwrap();

        let missing_track = get_track_by_id(&conn, original_id).unwrap().unwrap();
        assert!(missing_track.missing);

        let reconciled =
            reconcile_moved_track(&conn, original_id, "/music/new/song.mp3", Some(12345)).unwrap();
        assert!(reconciled.is_some());

        let final_count: i64 = conn
            .query_row("SELECT COUNT(*) FROM library", [], |row| row.get(0))
            .unwrap();
        assert_eq!(final_count, 1);

        let updated_track = get_track_by_id(&conn, original_id).unwrap().unwrap();
        assert_eq!(updated_track.filepath, "/music/new/song.mp3");
        assert!(!updated_track.missing);
        assert_eq!(updated_track.title, Some("My Favorite Song".to_string()));
        assert_eq!(updated_track.artist, Some("Artist Name".to_string()));
    }

    #[test]
    fn test_content_hash_fallback_when_inode_differs() {
        let conn = setup_test_db();

        let original_metadata = TrackMetadata {
            title: Some("Cross Volume Song".to_string()),
            file_inode: Some(11111),
            content_hash: Some("sha256:uniquehash123".to_string()),
            ..Default::default()
        };
        let original_id = add_track(&conn, "/volume1/song.mp3", &original_metadata).unwrap();

        mark_track_missing_by_filepath(&conn, "/volume1/song.mp3").unwrap();

        let by_inode = find_missing_track_by_inode(&conn, 99999).unwrap();
        assert!(by_inode.is_none());

        let by_hash = find_missing_track_by_content_hash(&conn, "sha256:uniquehash123").unwrap();
        assert!(by_hash.is_some());
        assert_eq!(by_hash.as_ref().unwrap().id, original_id);

        let reconciled =
            reconcile_moved_track(&conn, original_id, "/volume2/song.mp3", Some(99999)).unwrap();
        assert!(reconciled.is_some());

        let final_count: i64 = conn
            .query_row("SELECT COUNT(*) FROM library", [], |row| row.get(0))
            .unwrap();
        assert_eq!(final_count, 1);

        let updated = get_track_by_id(&conn, original_id).unwrap().unwrap();
        assert_eq!(updated.filepath, "/volume2/song.mp3");
        assert_eq!(updated.file_inode, Some(99999));
        assert!(!updated.missing);
    }
}
