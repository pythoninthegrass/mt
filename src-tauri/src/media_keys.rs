use souvlaki::{MediaControlEvent, MediaControls, MediaMetadata, MediaPlayback, MediaPosition, PlatformConfig};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Emitter};

#[derive(Debug, Clone, Default)]
pub struct NowPlayingInfo {
    pub title: Option<String>,
    pub artist: Option<String>,
    pub album: Option<String>,
    pub duration: Option<Duration>,
    pub cover_url: Option<String>,
}

pub struct MediaKeyManager {
    controls: Arc<Mutex<MediaControls>>,
}

impl MediaKeyManager {
    pub fn new(app: AppHandle) -> Result<Self, String> {
        let config = PlatformConfig {
            dbus_name: "mt_music_player",
            display_name: "mt",
            hwnd: None,
        };

        let mut controls = MediaControls::new(config)
            .map_err(|e| format!("Failed to create media controls: {:?}", e))?;

        let app_handle = app.clone();
        controls
            .attach(move |event: MediaControlEvent| {
                println!("Media key event received: {:?}", event);
                let event_name = match event {
                    MediaControlEvent::Play => Some("mediakey://play"),
                    MediaControlEvent::Pause => Some("mediakey://pause"),
                    MediaControlEvent::Toggle => Some("mediakey://toggle"),
                    MediaControlEvent::Next => Some("mediakey://next"),
                    MediaControlEvent::Previous => Some("mediakey://previous"),
                    MediaControlEvent::Stop => Some("mediakey://stop"),
                    _ => None,
                };

                if let Some(name) = event_name {
                    println!("Emitting event: {}", name);
                    let _ = app_handle.emit(name, ());
                }
            })
            .map_err(|e| format!("Failed to attach event handler: {:?}", e))?;

        controls
            .set_metadata(MediaMetadata {
                title: Some("mt"),
                artist: None,
                album: None,
                duration: None,
                cover_url: None,
            })
            .map_err(|e| format!("Failed to set initial metadata: {:?}", e))?;

        controls
            .set_playback(MediaPlayback::Stopped)
            .map_err(|e| format!("Failed to set initial playback state: {:?}", e))?;

        Ok(Self {
            controls: Arc::new(Mutex::new(controls)),
        })
    }

    pub fn set_metadata(&self, info: NowPlayingInfo) -> Result<(), String> {
        let mut controls = self.controls.lock().map_err(|e| e.to_string())?;
        controls
            .set_metadata(MediaMetadata {
                title: info.title.as_deref(),
                artist: info.artist.as_deref(),
                album: info.album.as_deref(),
                duration: info.duration,
                cover_url: info.cover_url.as_deref(),
            })
            .map_err(|e| format!("Failed to set metadata: {:?}", e))
    }

    pub fn set_playing(&self, progress: Option<Duration>) -> Result<(), String> {
        let mut controls = self.controls.lock().map_err(|e| e.to_string())?;
        controls
            .set_playback(MediaPlayback::Playing {
                progress: progress.map(MediaPosition),
            })
            .map_err(|e| format!("Failed to set playing state: {:?}", e))
    }

    pub fn set_paused(&self, progress: Option<Duration>) -> Result<(), String> {
        let mut controls = self.controls.lock().map_err(|e| e.to_string())?;
        controls
            .set_playback(MediaPlayback::Paused {
                progress: progress.map(MediaPosition),
            })
            .map_err(|e| format!("Failed to set paused state: {:?}", e))
    }

    pub fn set_stopped(&self) -> Result<(), String> {
        let mut controls = self.controls.lock().map_err(|e| e.to_string())?;
        controls
            .set_playback(MediaPlayback::Stopped)
            .map_err(|e| format!("Failed to set stopped state: {:?}", e))
    }
}
