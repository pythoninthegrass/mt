//! Last.fm integration commands.
//!
//! Provides OAuth authentication, scrobbling, now playing updates, and loved tracks import.

use crate::db::{settings, Database};
use crate::events::LastfmAuthEvent;
use crate::lastfm::{
    AuthCallbackResponse, AuthUrlResponse, DisconnectResponse, LastFmClient, LastfmSettings,
    LastfmSettingsUpdate,
};
use serde_json::json;
use tauri::{AppHandle, Emitter, State};

/// Helper to check if a setting is truthy
fn is_setting_truthy(value: Option<String>) -> bool {
    match value.as_deref() {
        Some("1") | Some("true") | Some("yes") | Some("on") => true,
        _ => false,
    }
}

/// Helper to parse setting as u8
fn parse_threshold(value: Option<String>, default: u8) -> u8 {
    value
        .and_then(|v| v.parse::<u8>().ok())
        .map(|v| v.clamp(25, 100))
        .unwrap_or(default)
}

/// Get Last.fm settings
#[tauri::command]
pub fn lastfm_get_settings(db: State<Database>) -> Result<LastfmSettings, String> {
    let client = LastFmClient::new();

    db.with_conn(|conn| {
        let enabled = is_setting_truthy(settings::get_setting(conn, "lastfm_scrobbling_enabled")?);
        let username = settings::get_setting(conn, "lastfm_username")?;
        let session_key = settings::get_setting(conn, "lastfm_session_key")?;
        let threshold = parse_threshold(
            settings::get_setting(conn, "lastfm_scrobble_threshold")?,
            90,
        );

        Ok(LastfmSettings {
            enabled,
            username,
            authenticated: session_key.is_some(),
            configured: client.is_configured(),
            scrobble_threshold: threshold,
        })
    })
    .map_err(|e| format!("Failed to get Last.fm settings: {}", e))
}

/// Update Last.fm settings
#[tauri::command]
pub fn lastfm_update_settings(
    db: State<Database>,
    settings_update: LastfmSettingsUpdate,
) -> Result<serde_json::Value, String> {
    let mut updated = Vec::new();

    db.with_conn(|conn| {
        if let Some(enabled) = settings_update.enabled {
            settings::set_setting(conn, "lastfm_scrobbling_enabled", &json!(enabled))?;
            updated.push("enabled");
        }

        if let Some(threshold) = settings_update.scrobble_threshold {
            // Clamp to valid range (25-100%)
            let clamped_threshold = threshold.clamp(25, 100);
            settings::set_setting(
                conn,
                "lastfm_scrobble_threshold",
                &json!(clamped_threshold),
            )?;
            updated.push("scrobble_threshold");
        }

        Ok(())
    })
    .map_err(|e: crate::db::DbError| format!("Failed to update Last.fm settings: {}", e))?;

    Ok(json!({ "updated": updated }))
}

// ============================================
// Authentication Commands
// ============================================

/// Get Last.fm authentication URL and token
#[tauri::command]
pub async fn lastfm_get_auth_url(app: AppHandle) -> Result<AuthUrlResponse, String> {
    let client = LastFmClient::new();

    if !client.is_configured() {
        return Err("Last.fm API keys not configured. Set LASTFM_API_KEY and LASTFM_API_SECRET.".to_string());
    }

    let (auth_url, token) = client
        .get_auth_url()
        .await
        .map_err(|e| format!("Failed to get auth URL: {}", e))?;

    // Emit pending event
    app.emit(
        LastfmAuthEvent::EVENT_NAME,
        LastfmAuthEvent::pending(),
    )
    .map_err(|e| format!("Failed to emit event: {}", e))?;

    Ok(AuthUrlResponse { auth_url, token })
}

/// Complete Last.fm authentication with token
#[tauri::command]
pub async fn lastfm_auth_callback(
    app: AppHandle,
    db: State<'_, Database>,
    token: String,
) -> Result<AuthCallbackResponse, String> {
    let client = LastFmClient::new();

    if !client.is_configured() {
        return Err("Last.fm API not configured".to_string());
    }

    // Exchange token for session
    let session = client
        .get_session(&token)
        .await
        .map_err(|e| format!("Authentication failed: {}", e))?;

    let username = session.name.clone();
    let session_key = session.key.clone();

    // Store session data in database
    db.with_conn(|conn| {
        settings::set_setting(conn, "lastfm_session_key", &json!(session_key))?;
        settings::set_setting(conn, "lastfm_username", &json!(username))?;
        settings::set_setting(conn, "lastfm_scrobbling_enabled", &json!(true))?;
        Ok(())
    })
    .map_err(|e: crate::db::DbError| format!("Failed to save session: {}", e))?;

    // Emit authenticated event
    app.emit(
        LastfmAuthEvent::EVENT_NAME,
        LastfmAuthEvent::authenticated(username.clone()),
    )
    .map_err(|e| format!("Failed to emit event: {}", e))?;

    Ok(AuthCallbackResponse {
        status: "success".to_string(),
        username,
        message: format!("Successfully connected as {}", session.name),
    })
}

/// Disconnect from Last.fm
#[tauri::command]
pub fn lastfm_disconnect(
    app: AppHandle,
    db: State<Database>,
) -> Result<DisconnectResponse, String> {
    db.with_conn(|conn| {
        settings::set_setting(conn, "lastfm_session_key", &json!(""))?;
        settings::set_setting(conn, "lastfm_username", &json!(""))?;
        settings::set_setting(conn, "lastfm_scrobbling_enabled", &json!(false))?;
        Ok(())
    })
    .map_err(|e: crate::db::DbError| format!("Failed to disconnect: {}", e))?;

    // Emit disconnected event
    app.emit(
        LastfmAuthEvent::EVENT_NAME,
        LastfmAuthEvent::disconnected(),
    )
    .map_err(|e| format!("Failed to emit event: {}", e))?;

    Ok(DisconnectResponse {
        status: "success".to_string(),
        message: "Disconnected from Last.fm".to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_setting_truthy() {
        assert!(is_setting_truthy(Some("1".to_string())));
        assert!(is_setting_truthy(Some("true".to_string())));
        assert!(is_setting_truthy(Some("yes".to_string())));
        assert!(is_setting_truthy(Some("on".to_string())));
        assert!(!is_setting_truthy(Some("0".to_string())));
        assert!(!is_setting_truthy(Some("false".to_string())));
        assert!(!is_setting_truthy(None));
    }

    #[test]
    fn test_parse_threshold() {
        assert_eq!(parse_threshold(Some("90".to_string()), 90), 90);
        assert_eq!(parse_threshold(Some("50".to_string()), 90), 50);
        // Clamps to 25-100 range
        assert_eq!(parse_threshold(Some("10".to_string()), 90), 25);
        assert_eq!(parse_threshold(Some("150".to_string()), 90), 100);
        // Invalid values use default
        assert_eq!(parse_threshold(Some("invalid".to_string()), 90), 90);
        assert_eq!(parse_threshold(None, 90), 90);
    }
}
