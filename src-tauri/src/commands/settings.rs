//! Settings commands using Tauri Store API.
//!
//! Provides persistent key-value storage for user preferences.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value as JsonValue};
use std::collections::HashMap;
use tauri::{AppHandle, Emitter};
use tauri_plugin_store::StoreExt;

/// Settings store filename
const STORE_NAME: &str = "settings.json";

/// Default settings values
fn get_defaults() -> HashMap<&'static str, JsonValue> {
    let mut defaults = HashMap::new();
    defaults.insert("volume", json!(75));
    defaults.insert("shuffle", json!(false));
    defaults.insert("loop_mode", json!("none"));
    defaults.insert("theme", json!("dark"));
    defaults.insert("sidebar_width", json!(250));
    defaults.insert("queue_panel_height", json!(300));
    defaults
}

/// All settings response
#[derive(Debug, Serialize, Deserialize)]
pub struct AllSettingsResponse {
    pub settings: HashMap<String, JsonValue>,
}

/// Single setting response
#[derive(Debug, Serialize, Deserialize)]
pub struct SettingResponse {
    pub key: String,
    pub value: JsonValue,
}

/// Settings update request
#[derive(Debug, Serialize, Deserialize)]
pub struct SettingsUpdateRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub volume: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub shuffle: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub loop_mode: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub theme: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub sidebar_width: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub queue_panel_height: Option<i64>,
}

/// Settings update response
#[derive(Debug, Serialize, Deserialize)]
pub struct SettingsUpdateResponse {
    pub updated: Vec<String>,
}

/// Event payload for settings changes
#[derive(Debug, Clone, Serialize)]
pub struct SettingsChangedPayload {
    pub key: String,
    pub value: JsonValue,
}

/// Get all settings
#[tauri::command]
pub fn settings_get_all(app: AppHandle) -> Result<AllSettingsResponse, String> {
    let store = app
        .store(STORE_NAME)
        .map_err(|e| format!("Failed to open settings store: {}", e))?;

    let defaults = get_defaults();
    let mut settings: HashMap<String, JsonValue> = HashMap::new();

    // Load all settings with defaults
    for (key, default) in defaults {
        let value = store
            .get(key)
            .unwrap_or(default);
        settings.insert(key.to_string(), value);
    }

    // Also include any extra keys that might be in the store
    for key in store.keys() {
        if !settings.contains_key(&key)
            && let Some(value) = store.get(&key) {
                settings.insert(key, value.clone());
            }
    }

    Ok(AllSettingsResponse { settings })
}

/// Get a single setting
#[tauri::command]
pub fn settings_get(app: AppHandle, key: String) -> Result<SettingResponse, String> {
    let store = app
        .store(STORE_NAME)
        .map_err(|e| format!("Failed to open settings store: {}", e))?;

    let defaults = get_defaults();
    let value = store
        .get(&key)
        .or_else(|| defaults.get(key.as_str()).cloned())
        .unwrap_or(JsonValue::Null);

    Ok(SettingResponse { key, value })
}

/// Set a single setting
#[tauri::command]
pub fn settings_set(app: AppHandle, key: String, value: JsonValue) -> Result<SettingResponse, String> {
    let store = app
        .store(STORE_NAME)
        .map_err(|e| format!("Failed to open settings store: {}", e))?;

    store.set(key.clone(), value.clone());
    store.save().map_err(|e| format!("Failed to save settings: {}", e))?;

    // Emit settings changed event
    let _ = app.emit("settings://changed", SettingsChangedPayload {
        key: key.clone(),
        value: value.clone(),
    });

    Ok(SettingResponse { key, value })
}

/// Update multiple settings at once
#[tauri::command]
pub fn settings_update(app: AppHandle, settings: SettingsUpdateRequest) -> Result<SettingsUpdateResponse, String> {
    let store = app
        .store(STORE_NAME)
        .map_err(|e| format!("Failed to open settings store: {}", e))?;

    let mut updated = Vec::new();

    if let Some(volume) = settings.volume {
        // Validate volume range
        let vol = volume.clamp(0, 100);
        store.set("volume".to_string(), json!(vol));
        updated.push("volume".to_string());
        let _ = app.emit("settings://changed", SettingsChangedPayload {
            key: "volume".to_string(),
            value: json!(vol),
        });
    }

    if let Some(shuffle) = settings.shuffle {
        store.set("shuffle".to_string(), json!(shuffle));
        updated.push("shuffle".to_string());
        let _ = app.emit("settings://changed", SettingsChangedPayload {
            key: "shuffle".to_string(),
            value: json!(shuffle),
        });
    }

    if let Some(ref loop_mode) = settings.loop_mode {
        // Validate loop mode
        if ["none", "all", "one"].contains(&loop_mode.as_str()) {
            store.set("loop_mode".to_string(), json!(loop_mode));
            updated.push("loop_mode".to_string());
            let _ = app.emit("settings://changed", SettingsChangedPayload {
                key: "loop_mode".to_string(),
                value: json!(loop_mode),
            });
        }
    }

    if let Some(ref theme) = settings.theme {
        store.set("theme".to_string(), json!(theme));
        updated.push("theme".to_string());
        let _ = app.emit("settings://changed", SettingsChangedPayload {
            key: "theme".to_string(),
            value: json!(theme),
        });
    }

    if let Some(sidebar_width) = settings.sidebar_width {
        // Validate sidebar width range
        let width = sidebar_width.clamp(100, 500);
        store.set("sidebar_width".to_string(), json!(width));
        updated.push("sidebar_width".to_string());
        let _ = app.emit("settings://changed", SettingsChangedPayload {
            key: "sidebar_width".to_string(),
            value: json!(width),
        });
    }

    if let Some(queue_panel_height) = settings.queue_panel_height {
        // Validate queue panel height range
        let height = queue_panel_height.clamp(100, 800);
        store.set("queue_panel_height".to_string(), json!(height));
        updated.push("queue_panel_height".to_string());
        let _ = app.emit("settings://changed", SettingsChangedPayload {
            key: "queue_panel_height".to_string(),
            value: json!(height),
        });
    }

    if !updated.is_empty() {
        store.save().map_err(|e| format!("Failed to save settings: {}", e))?;
    }

    Ok(SettingsUpdateResponse { updated })
}

/// Reset settings to defaults
#[tauri::command]
pub fn settings_reset(app: AppHandle) -> Result<AllSettingsResponse, String> {
    let store = app
        .store(STORE_NAME)
        .map_err(|e| format!("Failed to open settings store: {}", e))?;

    let defaults = get_defaults();
    let mut settings: HashMap<String, JsonValue> = HashMap::new();

    // Clear existing and set defaults
    store.clear();

    for (key, value) in defaults {
        store.set(key.to_string(), value.clone());
        settings.insert(key.to_string(), value.clone());

        let _ = app.emit("settings://changed", SettingsChangedPayload {
            key: key.to_string(),
            value,
        });
    }

    store.save().map_err(|e| format!("Failed to save settings: {}", e))?;

    // Emit reset event
    let _ = app.emit("settings://reset", ());

    Ok(AllSettingsResponse { settings })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_defaults() {
        let defaults = get_defaults();
        assert_eq!(defaults.get("volume"), Some(&json!(75)));
        assert_eq!(defaults.get("shuffle"), Some(&json!(false)));
        assert_eq!(defaults.get("loop_mode"), Some(&json!("none")));
        assert_eq!(defaults.get("theme"), Some(&json!("dark")));
        assert_eq!(defaults.get("sidebar_width"), Some(&json!(250)));
        assert_eq!(defaults.get("queue_panel_height"), Some(&json!(300)));
    }
}
