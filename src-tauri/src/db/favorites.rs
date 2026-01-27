//! Favorites database operations.
//!
//! Operations for favorited tracks, top played, and recently played.

use rusqlite::{params, Connection};

use crate::db::{DbResult, FavoriteTrack, PaginatedResult, Track};

/// Get favorited tracks with pagination
pub fn get_favorites(
    conn: &Connection,
    limit: i64,
    offset: i64,
) -> DbResult<PaginatedResult<FavoriteTrack>> {
    let total: i64 = conn.query_row("SELECT COUNT(*) FROM favorites", [], |row| row.get(0))?;

    let mut stmt = conn.prepare(
        "SELECT l.id, l.filepath, l.title, l.artist, l.album, l.album_artist,
                l.track_number, l.track_total, l.date, l.duration, l.file_size,
                l.play_count, l.last_played, l.added_date, l.missing, l.last_seen_at,
                l.file_mtime_ns, l.file_inode, l.content_hash, f.timestamp as favorited_date
         FROM favorites f
         JOIN library l ON f.track_id = l.id
         ORDER BY f.timestamp ASC
         LIMIT ? OFFSET ?",
    )?;

    let tracks: Vec<FavoriteTrack> = stmt
        .query_map([limit, offset], |row| {
            Ok(FavoriteTrack {
                track: Track {
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
                },
                favorited_date: row.get("favorited_date")?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(PaginatedResult {
        items: tracks,
        total,
    })
}

/// Get top 25 most played tracks
pub fn get_top_25(conn: &Connection) -> DbResult<Vec<Track>> {
    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns, file_inode, content_hash
         FROM library
         WHERE play_count > 0
         ORDER BY play_count DESC, last_played DESC
         LIMIT 25",
    )?;

    let tracks: Vec<Track> = stmt
        .query_map([], |row| {
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
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(tracks)
}

/// Get tracks played within the last N days
pub fn get_recently_played(conn: &Connection, days: i64, limit: i64) -> DbResult<Vec<Track>> {
    let modifier = format!("-{} days", days);

    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns, file_inode, content_hash
         FROM library
         WHERE last_played IS NOT NULL
           AND last_played >= datetime('now', ?)
         ORDER BY last_played DESC
         LIMIT ?",
    )?;

    let tracks: Vec<Track> = stmt
        .query_map(params![modifier, limit], |row| {
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
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(tracks)
}

/// Get tracks added within the last N days
pub fn get_recently_added(conn: &Connection, days: i64, limit: i64) -> DbResult<Vec<Track>> {
    let modifier = format!("-{} days", days);

    let mut stmt = conn.prepare(
        "SELECT id, filepath, title, artist, album, album_artist,
                track_number, track_total, date, duration, file_size,
                play_count, last_played, added_date, missing, last_seen_at,
                file_mtime_ns, file_inode, content_hash
         FROM library
         WHERE added_date IS NOT NULL
           AND added_date >= datetime('now', ?)
         ORDER BY added_date DESC
         LIMIT ?",
    )?;

    let tracks: Vec<Track> = stmt
        .query_map(params![modifier, limit], |row| {
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
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(tracks)
}

/// Check if a track is favorited
pub fn is_favorite(conn: &Connection, track_id: i64) -> DbResult<(bool, Option<String>)> {
    match conn.query_row(
        "SELECT timestamp FROM favorites WHERE track_id = ?",
        [track_id],
        |row| row.get::<_, String>(0),
    ) {
        Ok(timestamp) => Ok((true, Some(timestamp))),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok((false, None)),
        Err(e) => Err(e.into()),
    }
}

/// Add a track to favorites
pub fn add_favorite(conn: &Connection, track_id: i64) -> DbResult<Option<String>> {
    match conn.execute("INSERT INTO favorites (track_id) VALUES (?)", [track_id]) {
        Ok(_) => {
            let timestamp: String = conn.query_row(
                "SELECT timestamp FROM favorites WHERE track_id = ?",
                [track_id],
                |row| row.get(0),
            )?;
            Ok(Some(timestamp))
        }
        Err(rusqlite::Error::SqliteFailure(err, _))
            if err.code == rusqlite::ErrorCode::ConstraintViolation =>
        {
            Ok(None) // Already favorited
        }
        Err(e) => Err(e.into()),
    }
}

/// Remove a track from favorites
pub fn remove_favorite(conn: &Connection, track_id: i64) -> DbResult<bool> {
    let deleted = conn.execute("DELETE FROM favorites WHERE track_id = ?", [track_id])?;
    Ok(deleted > 0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::{
        library::{add_track, update_play_count},
        schema::{create_tables, run_migrations},
        TrackMetadata,
    };

    fn setup_test_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        create_tables(&conn).unwrap();
        run_migrations(&conn).unwrap();
        conn
    }

    #[test]
    fn test_add_and_remove_favorite() {
        let conn = setup_test_db();

        let metadata = TrackMetadata {
            title: Some("Test".to_string()),
            ..Default::default()
        };
        let id = add_track(&conn, "/music/test.mp3", &metadata).unwrap();

        // Add favorite
        let timestamp = add_favorite(&conn, id).unwrap();
        assert!(timestamp.is_some());

        // Check is favorite
        let (is_fav, _) = is_favorite(&conn, id).unwrap();
        assert!(is_fav);

        // Adding again should return None
        let timestamp = add_favorite(&conn, id).unwrap();
        assert!(timestamp.is_none());

        // Remove favorite
        let removed = remove_favorite(&conn, id).unwrap();
        assert!(removed);

        // Check is not favorite
        let (is_fav, _) = is_favorite(&conn, id).unwrap();
        assert!(!is_fav);
    }

    #[test]
    fn test_get_favorites() {
        let conn = setup_test_db();

        for i in 1..=5 {
            let metadata = TrackMetadata {
                title: Some(format!("Track {}", i)),
                ..Default::default()
            };
            let id = add_track(&conn, &format!("/music/track{}.mp3", i), &metadata).unwrap();
            add_favorite(&conn, id).unwrap();
        }

        let result = get_favorites(&conn, 10, 0).unwrap();
        assert_eq!(result.total, 5);
        assert_eq!(result.items.len(), 5);
    }

    #[test]
    fn test_get_top_25() {
        let conn = setup_test_db();

        for i in 1..=30 {
            let metadata = TrackMetadata {
                title: Some(format!("Track {}", i)),
                ..Default::default()
            };
            let id = add_track(&conn, &format!("/music/track{}.mp3", i), &metadata).unwrap();

            // Increment play count for some tracks
            for _ in 0..i {
                update_play_count(&conn, id).unwrap();
            }
        }

        let top = get_top_25(&conn).unwrap();
        assert_eq!(top.len(), 25);
        assert_eq!(top[0].play_count, 30); // Most played first
    }
}
