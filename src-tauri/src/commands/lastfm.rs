//! Last.fm integration commands.
//!
//! Provides OAuth authentication, scrobbling, now playing updates, and loved tracks import.

use crate::db::{settings, Database};
use crate::lastfm::{LastFmClient, LastfmSettings, LastfmSettingsUpdate};
use serde_json::json;
use tauri::State;

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
