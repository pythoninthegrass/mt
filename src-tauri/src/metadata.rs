use lofty::config::WriteOptions;
use lofty::prelude::*;
use lofty::probe::Probe;
use lofty::tag::Tag;
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Serialize, Deserialize)]
pub struct TrackMetadata {
    pub path: String,
    pub title: Option<String>,
    pub artist: Option<String>,
    pub album: Option<String>,
    pub album_artist: Option<String>,
    pub track_number: Option<u32>,
    pub track_total: Option<u32>,
    pub disc_number: Option<u32>,
    pub disc_total: Option<u32>,
    pub year: Option<u32>,
    pub genre: Option<String>,
    pub duration_ms: Option<u64>,
    pub format: Option<String>,
    pub bitrate: Option<u32>,
    pub sample_rate: Option<u32>,
    pub channels: Option<u8>,
}

#[derive(Debug, Deserialize)]
pub struct MetadataUpdate {
    pub path: String,
    pub title: Option<String>,
    pub artist: Option<String>,
    pub album: Option<String>,
    pub album_artist: Option<String>,
    pub track_number: Option<u32>,
    pub track_total: Option<u32>,
    pub disc_number: Option<u32>,
    pub disc_total: Option<u32>,
    pub year: Option<u32>,
    pub genre: Option<String>,
}

#[tauri::command]
pub fn get_track_metadata(path: String) -> Result<TrackMetadata, String> {
    let file_path = Path::new(&path);
    
    if !file_path.exists() {
        return Err(format!("File not found: {}", path));
    }

    let tagged_file = Probe::open(file_path)
        .map_err(|e| format!("Failed to open file: {}", e))?
        .read()
        .map_err(|e| format!("Failed to read file: {}", e))?;

    let tag = tagged_file.primary_tag().or_else(|| tagged_file.first_tag());
    let properties = tagged_file.properties();

    let format = match tagged_file.file_type() {
        lofty::file::FileType::Aac => "AAC",
        lofty::file::FileType::Aiff => "AIFF",
        lofty::file::FileType::Ape => "APE",
        lofty::file::FileType::Flac => "FLAC",
        lofty::file::FileType::Mpeg => "MP3",
        lofty::file::FileType::Mp4 => "M4A",
        lofty::file::FileType::Mpc => "MPC",
        lofty::file::FileType::Opus => "Opus",
        lofty::file::FileType::Vorbis => "Ogg Vorbis",
        lofty::file::FileType::Speex => "Speex",
        lofty::file::FileType::Wav => "WAV",
        lofty::file::FileType::WavPack => "WavPack",
        _ => "Unknown",
    };

    let (title, artist, album, album_artist, track_number, track_total, disc_number, disc_total, year, genre) =
        if let Some(tag) = tag {
            (
                tag.title().map(|s| s.to_string()),
                tag.artist().map(|s| s.to_string()),
                tag.album().map(|s| s.to_string()),
                tag.get_string(&ItemKey::AlbumArtist).map(|s| s.to_string()),
                tag.track(),
                tag.track_total(),
                tag.disk(),
                tag.disk_total(),
                tag.year(),
                tag.genre().map(|s| s.to_string()),
            )
        } else {
            (None, None, None, None, None, None, None, None, None, None)
        };

    Ok(TrackMetadata {
        path,
        title,
        artist,
        album,
        album_artist,
        track_number,
        track_total,
        disc_number,
        disc_total,
        year,
        genre,
        duration_ms: Some(properties.duration().as_millis() as u64),
        format: Some(format.to_string()),
        bitrate: properties.audio_bitrate(),
        sample_rate: properties.sample_rate(),
        channels: properties.channels(),
    })
}

#[tauri::command]
pub fn save_track_metadata(update: MetadataUpdate) -> Result<TrackMetadata, String> {
    let file_path = Path::new(&update.path);
    
    if !file_path.exists() {
        return Err(format!("File not found: {}", update.path));
    }

    let mut tagged_file = Probe::open(file_path)
        .map_err(|e| format!("Failed to open file: {}", e))?
        .read()
        .map_err(|e| format!("Failed to read file: {}", e))?;

    let tag = match tagged_file.primary_tag_mut() {
        Some(primary_tag) => primary_tag,
        None => {
            if let Some(first_tag) = tagged_file.first_tag_mut() {
                first_tag
            } else {
                let tag_type = tagged_file.primary_tag_type();
                tagged_file.insert_tag(Tag::new(tag_type));
                tagged_file.primary_tag_mut().unwrap()
            }
        }
    };

    if let Some(title) = &update.title {
        tag.set_title(title.clone());
    }
    if let Some(artist) = &update.artist {
        tag.set_artist(artist.clone());
    }
    if let Some(album) = &update.album {
        tag.set_album(album.clone());
    }
    if let Some(album_artist) = &update.album_artist {
        tag.insert(lofty::tag::TagItem::new(
            ItemKey::AlbumArtist,
            lofty::tag::ItemValue::Text(album_artist.clone()),
        ));
    }
    if let Some(track) = update.track_number {
        tag.set_track(track);
    }
    if let Some(total) = update.track_total {
        tag.set_track_total(total);
    }
    if let Some(disc) = update.disc_number {
        tag.set_disk(disc);
    }
    if let Some(total) = update.disc_total {
        tag.set_disk_total(total);
    }
    if let Some(year) = update.year {
        tag.set_year(year);
    }
    if let Some(genre) = &update.genre {
        tag.set_genre(genre.clone());
    }

    tag.save_to_path(&update.path, WriteOptions::default())
        .map_err(|e| format!("Failed to save metadata: {}", e))?;

    get_track_metadata(update.path)
}
