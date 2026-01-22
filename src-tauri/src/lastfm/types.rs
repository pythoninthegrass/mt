use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Last.fm settings response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LastfmSettings {
    pub enabled: bool,
    pub username: Option<String>,
    pub authenticated: bool,
    pub configured: bool,
    pub scrobble_threshold: u8,
}

/// Request to update Last.fm settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LastfmSettingsUpdate {
    pub enabled: Option<bool>,
    pub scrobble_threshold: Option<u8>,
}

/// Response from updating settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LastfmSettingsUpdateResponse {
    pub updated: Vec<String>,
}

/// Authentication URL response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthUrlResponse {
    pub auth_url: String,
    pub token: String,
}

/// Authentication callback response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthCallbackResponse {
    pub status: String,
    pub username: String,
    pub message: String,
}

/// Disconnect response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisconnectResponse {
    pub status: String,
    pub message: String,
}

/// Now playing request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NowPlayingRequest {
    pub artist: String,
    pub track: String,
    pub album: Option<String>,
    pub duration: u32,
}

/// Scrobble request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrobbleRequest {
    pub artist: String,
    pub track: String,
    pub album: Option<String>,
    pub timestamp: i64,
    pub duration: u32,
    pub played_time: u32,
}

/// Scrobble response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrobbleResponse {
    pub status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

/// Queue status response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueStatusResponse {
    pub queued_scrobbles: usize,
}

/// Queue retry response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueRetryResponse {
    pub status: String,
    pub remaining_queued: usize,
}

/// Import loved tracks response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportLovedTracksResponse {
    pub status: String,
    pub total_loved_tracks: usize,
    pub imported_count: usize,
    pub message: String,
}

/// Last.fm API token response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenResponse {
    pub token: String,
}

/// Last.fm API session response (from auth.getSession)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionResponse {
    pub session: SessionInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionInfo {
    pub name: String,
    pub key: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub subscriber: Option<u8>,
}

/// Last.fm API error response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: u32,
    pub message: String,
}

/// Loved tracks response from Last.fm API
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LovedTracksResponse {
    pub lovedtracks: LovedTracksContainer,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LovedTracksContainer {
    pub track: Vec<LovedTrack>,
    #[serde(rename = "@attr")]
    pub attr: Option<LovedTracksAttr>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LovedTracksAttr {
    pub user: String,
    #[serde(rename = "totalPages")]
    pub total_pages: String,
    pub page: String,
    #[serde(rename = "perPage")]
    pub per_page: String,
    pub total: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LovedTrack {
    pub name: String,
    pub artist: ArtistInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ArtistInfo {
    Simple(String),
    Detailed { name: String },
}

impl ArtistInfo {
    pub fn name(&self) -> &str {
        match self {
            ArtistInfo::Simple(name) => name,
            ArtistInfo::Detailed { name } => name,
        }
    }
}

/// Scrobble response from Last.fm API
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrobbleApiResponse {
    pub scrobbles: ScrobblesContainer,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrobblesContainer {
    #[serde(rename = "@attr")]
    pub attr: ScrobblesAttr,
    pub scrobble: Option<HashMap<String, serde_json::Value>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrobblesAttr {
    pub accepted: u32,
    pub ignored: u32,
}

/// Now playing response from Last.fm API
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NowPlayingApiResponse {
    pub nowplaying: HashMap<String, serde_json::Value>,
}
