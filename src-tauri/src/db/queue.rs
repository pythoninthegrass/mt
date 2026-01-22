//! Queue database operations.
//!
//! Operations for the playback queue.

use rusqlite::{params, Connection};

use crate::db::{library::get_track_by_filepath, DbResult, QueueItem, Track};

/// Get all items in the queue with track metadata
pub fn get_queue(conn: &Connection) -> DbResult<Vec<QueueItem>> {
    let mut stmt = conn.prepare(
        "SELECT q.id as queue_id, q.filepath,
                l.id, l.title, l.artist, l.album, l.album_artist,
                l.track_number, l.track_total, l.date, l.duration, l.file_size,
                l.play_count, l.last_played, l.added_date, l.missing, l.last_seen_at,
                l.file_mtime_ns, l.file_inode, l.content_hash
         FROM queue q
         LEFT JOIN library l ON q.filepath = l.filepath
         ORDER BY q.id",
    )?;

    let mut items = Vec::new();
    let mut rows = stmt.query([])?;
    let mut position = 0;

    while let Some(row) = rows.next()? {
        let filepath: String = row.get("filepath")?;
        let track = Track {
            id: row.get::<_, Option<i64>>("id")?.unwrap_or(0),
            filepath: filepath.clone(),
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
        };

        items.push(QueueItem { position, track });
        position += 1;
    }

    Ok(items)
}

/// Add tracks to the queue by track IDs
pub fn add_to_queue(conn: &Connection, track_ids: &[i64], position: Option<i64>) -> DbResult<i64> {
    // Get filepaths for track IDs
    let placeholders = track_ids.iter().map(|_| "?").collect::<Vec<_>>().join(",");
    let sql = format!(
        "SELECT id, filepath FROM library WHERE id IN ({})",
        placeholders
    );

    let mut stmt = conn.prepare(&sql)?;
    let params: Vec<&dyn rusqlite::ToSql> = track_ids
        .iter()
        .map(|id| id as &dyn rusqlite::ToSql)
        .collect();

    let tracks: Vec<(i64, String)> = stmt
        .query_map(params.as_slice(), |row| Ok((row.get(0)?, row.get(1)?)))?
        .filter_map(|r| r.ok())
        .collect();

    let track_map: std::collections::HashMap<i64, String> = tracks.into_iter().collect();

    if let Some(pos) = position {
        // Get current queue
        let mut stmt = conn.prepare("SELECT id, filepath FROM queue ORDER BY id")?;
        let current_queue: Vec<(i64, String)> = stmt
            .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?
            .filter_map(|r| r.ok())
            .collect();

        // Clear and rebuild queue
        conn.execute("DELETE FROM queue", [])?;

        let pos = pos as usize;

        // Insert items before position
        for (_, filepath) in current_queue.iter().take(pos) {
            conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
        }

        // Insert new items
        for track_id in track_ids {
            if let Some(filepath) = track_map.get(track_id) {
                conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
            }
        }

        // Insert items after position
        for (_, filepath) in current_queue.iter().skip(pos) {
            conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
        }
    } else {
        // Append to end
        for track_id in track_ids {
            if let Some(filepath) = track_map.get(track_id) {
                conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
            }
        }
    }

    Ok(track_ids
        .iter()
        .filter(|id| track_map.contains_key(id))
        .count() as i64)
}

/// Add files directly to the queue
pub fn add_files_to_queue(
    conn: &Connection,
    filepaths: &[String],
    position: Option<i64>,
) -> DbResult<(i64, Vec<Track>)> {
    let mut added_tracks = Vec::new();

    for filepath in filepaths {
        // Check if file exists in library
        if let Some(track) = get_track_by_filepath(conn, filepath)? {
            added_tracks.push(track);
        } else {
            // Add to library with minimal metadata
            let filename = std::path::Path::new(filepath)
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("Unknown");
            let title = std::path::Path::new(filename)
                .file_stem()
                .and_then(|n| n.to_str())
                .unwrap_or(filename);

            conn.execute(
                "INSERT INTO library (filepath, title) VALUES (?, ?)",
                params![filepath, title],
            )?;

            if let Some(track) = get_track_by_filepath(conn, filepath)? {
                added_tracks.push(track);
            }
        }
    }

    // Add to queue
    if let Some(pos) = position {
        let mut stmt = conn.prepare("SELECT id, filepath FROM queue ORDER BY id")?;
        let current_queue: Vec<(i64, String)> = stmt
            .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?
            .filter_map(|r| r.ok())
            .collect();

        conn.execute("DELETE FROM queue", [])?;

        let pos = pos as usize;

        for (_, filepath) in current_queue.iter().take(pos) {
            conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
        }

        for track in &added_tracks {
            conn.execute("INSERT INTO queue (filepath) VALUES (?)", [&track.filepath])?;
        }

        for (_, filepath) in current_queue.iter().skip(pos) {
            conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
        }
    } else {
        for track in &added_tracks {
            conn.execute("INSERT INTO queue (filepath) VALUES (?)", [&track.filepath])?;
        }
    }

    Ok((added_tracks.len() as i64, added_tracks))
}

/// Remove a track from the queue by position
pub fn remove_from_queue(conn: &Connection, position: i64) -> DbResult<bool> {
    let mut stmt = conn.prepare("SELECT id FROM queue ORDER BY id")?;
    let items: Vec<i64> = stmt
        .query_map([], |row| row.get(0))?
        .filter_map(|r| r.ok())
        .collect();

    if position < 0 || position as usize >= items.len() {
        return Ok(false);
    }

    let queue_id = items[position as usize];
    let deleted = conn.execute("DELETE FROM queue WHERE id = ?", [queue_id])?;
    Ok(deleted > 0)
}

/// Clear the entire queue
pub fn clear_queue(conn: &Connection) -> DbResult<()> {
    conn.execute("DELETE FROM queue", [])?;
    Ok(())
}

/// Reorder tracks in the queue
pub fn reorder_queue(conn: &Connection, from_position: i64, to_position: i64) -> DbResult<bool> {
    let mut stmt = conn.prepare("SELECT id, filepath FROM queue ORDER BY id")?;
    let items: Vec<(i64, String)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?
        .filter_map(|r| r.ok())
        .collect();

    let from = from_position as usize;
    let to = to_position as usize;

    if from >= items.len() || to >= items.len() {
        return Ok(false);
    }

    // Reorder in memory
    let mut filepaths: Vec<String> = items.into_iter().map(|(_, fp)| fp).collect();
    let item = filepaths.remove(from);
    filepaths.insert(to, item);

    // Rebuild queue
    conn.execute("DELETE FROM queue", [])?;
    for filepath in filepaths {
        conn.execute("INSERT INTO queue (filepath) VALUES (?)", [filepath])?;
    }

    Ok(true)
}

/// Get the number of items in the queue
pub fn get_queue_length(conn: &Connection) -> DbResult<i64> {
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM queue", [], |row| row.get(0))?;
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::{
        library::add_track,
        schema::{create_tables, run_migrations},
        TrackMetadata,
    };

    fn setup_test_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        create_tables(&conn).unwrap();
        run_migrations(&conn).unwrap();
        conn
    }

    fn add_test_tracks(conn: &Connection, count: i32) -> Vec<i64> {
        (1..=count)
            .map(|i| {
                let metadata = TrackMetadata {
                    title: Some(format!("Track {}", i)),
                    ..Default::default()
                };
                add_track(conn, &format!("/music/track{}.mp3", i), &metadata).unwrap()
            })
            .collect()
    }

    #[test]
    fn test_add_to_queue() {
        let conn = setup_test_db();
        let track_ids = add_test_tracks(&conn, 3);

        let added = add_to_queue(&conn, &track_ids, None).unwrap();
        assert_eq!(added, 3);

        let queue = get_queue(&conn).unwrap();
        assert_eq!(queue.len(), 3);
        assert_eq!(queue[0].position, 0);
        assert_eq!(queue[1].position, 1);
        assert_eq!(queue[2].position, 2);
    }

    #[test]
    fn test_add_to_queue_at_position() {
        let conn = setup_test_db();
        let track_ids = add_test_tracks(&conn, 5);

        // Add first 3 tracks
        add_to_queue(&conn, &track_ids[0..3], None).unwrap();

        // Add remaining 2 at position 1
        add_to_queue(&conn, &track_ids[3..5], Some(1)).unwrap();

        let queue = get_queue(&conn).unwrap();
        assert_eq!(queue.len(), 5);

        // Order should be: track1, track4, track5, track2, track3
        assert_eq!(queue[0].track.title, Some("Track 1".to_string()));
        assert_eq!(queue[1].track.title, Some("Track 4".to_string()));
        assert_eq!(queue[2].track.title, Some("Track 5".to_string()));
    }

    #[test]
    fn test_remove_from_queue() {
        let conn = setup_test_db();
        let track_ids = add_test_tracks(&conn, 3);
        add_to_queue(&conn, &track_ids, None).unwrap();

        let removed = remove_from_queue(&conn, 1).unwrap();
        assert!(removed);

        let queue = get_queue(&conn).unwrap();
        assert_eq!(queue.len(), 2);
    }

    #[test]
    fn test_reorder_queue() {
        let conn = setup_test_db();
        let track_ids = add_test_tracks(&conn, 3);
        add_to_queue(&conn, &track_ids, None).unwrap();

        // Move track at position 2 to position 0
        let success = reorder_queue(&conn, 2, 0).unwrap();
        assert!(success);

        let queue = get_queue(&conn).unwrap();
        assert_eq!(queue[0].track.title, Some("Track 3".to_string()));
        assert_eq!(queue[1].track.title, Some("Track 1".to_string()));
        assert_eq!(queue[2].track.title, Some("Track 2".to_string()));
    }

    #[test]
    fn test_clear_queue() {
        let conn = setup_test_db();
        let track_ids = add_test_tracks(&conn, 3);
        add_to_queue(&conn, &track_ids, None).unwrap();

        clear_queue(&conn).unwrap();

        let length = get_queue_length(&conn).unwrap();
        assert_eq!(length, 0);
    }
}
