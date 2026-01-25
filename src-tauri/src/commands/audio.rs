use crate::audio::{AudioEngine, PlaybackState, TrackInfo};
use serde::{Deserialize, Serialize};
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread;
use std::time::Duration;
use tauri::{AppHandle, Emitter, Manager, State};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlaybackStatus {
    pub position_ms: u64,
    pub duration_ms: u64,
    pub state: PlaybackState,
    pub volume: f32,
    pub track: Option<TrackInfo>,
}

enum AudioCommand {
    Load(String, Option<i64>, Sender<Result<TrackInfo, String>>),  // Add track_id
    Play(Sender<Result<(), String>>),
    Pause(Sender<Result<(), String>>),
    Stop(Sender<Result<(), String>>),
    Seek(u64, Sender<Result<(), String>>),
    SetVolume(f32, Sender<Result<(), String>>),
    GetVolume(Sender<f32>),
    GetStatus(Sender<PlaybackStatus>),
}

struct PlayCountState {
    track_id: Option<i64>,
    threshold_reached: bool,
}

struct ScrobbleState {
    track_id: Option<i64>,
    threshold_reached: bool,
    threshold_percent: f64,
}

pub struct AudioState {
    sender: Sender<AudioCommand>,
}

impl AudioState {
    pub fn new(app: AppHandle) -> Self {
        let (tx, rx) = mpsc::channel::<AudioCommand>();

        thread::spawn(move || {
            audio_thread(rx, app);
        });

        Self { sender: tx }
    }

    fn send_command(&self, cmd: AudioCommand) {
        let _ = self.sender.send(cmd);
    }
}

fn audio_thread(rx: Receiver<AudioCommand>, app: AppHandle) {
    let mut engine = match AudioEngine::new() {
        Ok(e) => e,
        Err(e) => {
            eprintln!("Failed to create audio engine: {}", e);
            return;
        }
    };

    let mut last_finished = false;
    let mut last_emit = std::time::Instant::now();
    let mut play_count_state = PlayCountState {
        track_id: None,
        threshold_reached: false,
    };
    let mut scrobble_state = ScrobbleState {
        track_id: None,
        threshold_reached: false,
        threshold_percent: 0.9, // Default 90%
    };

    loop {
        match rx.recv_timeout(Duration::from_millis(100)) {
            Ok(cmd) => match cmd {
                AudioCommand::Load(path, track_id, reply) => {
                    let result = engine.load(&path).map_err(|e| e.to_string());

                    // Reset play count state for new track
                    play_count_state.track_id = track_id;
                    play_count_state.threshold_reached = false;

                    // Reset scrobble state for new track
                    scrobble_state.track_id = track_id;
                    scrobble_state.threshold_reached = false;

                    last_finished = false;

                    let _ = reply.send(result);
                }
                AudioCommand::Play(reply) => {
                    let result = engine.play().map_err(|e| e.to_string());
                    let _ = reply.send(result);
                }
                AudioCommand::Pause(reply) => {
                    let result = engine.pause().map_err(|e| e.to_string());
                    let _ = reply.send(result);
                }
                AudioCommand::Stop(reply) => {
                    engine.stop();
                    let _ = reply.send(Ok(()));
                }
                AudioCommand::Seek(pos, reply) => {
                    let result = engine.seek(pos).map_err(|e| e.to_string());
                    let _ = reply.send(result);
                }
                AudioCommand::SetVolume(vol, reply) => {
                    engine.set_volume(vol);
                    let _ = reply.send(Ok(()));
                }
                AudioCommand::GetVolume(reply) => {
                    let _ = reply.send(engine.get_volume());
                }
                AudioCommand::GetStatus(reply) => {
                    let progress = engine.get_progress();
                    let track = engine.get_current_track().cloned();
                    let status = PlaybackStatus {
                        position_ms: progress.position_ms,
                        duration_ms: progress.duration_ms,
                        state: progress.state,
                        volume: engine.get_volume(),
                        track,
                    };
                    let _ = reply.send(status);
                }
            },
            Err(mpsc::RecvTimeoutError::Timeout) => {}
            Err(mpsc::RecvTimeoutError::Disconnected) => break,
        }

        let is_playing = engine.get_state() == PlaybackState::Playing;
        let is_finished = engine.is_finished();

        if is_playing && last_emit.elapsed() >= Duration::from_millis(250) {
            let progress = engine.get_progress();
            let _ = app.emit("audio://progress", &progress);
            last_emit = std::time::Instant::now();

            // Check play count threshold (75%)
            if !play_count_state.threshold_reached
               && progress.duration_ms > 0
               && play_count_state.track_id.is_some() {
                let ratio = progress.position_ms as f64 / progress.duration_ms as f64;

                if ratio >= 0.75 {
                    if let Some(track_id) = play_count_state.track_id {
                        // Spawn async task to avoid blocking audio thread
                        let app_handle = app.clone();
                        std::thread::spawn(move || {
                            use crate::db::Database;
                            use crate::db::library;

                            let db = app_handle.state::<Database>();
                            if let Ok(conn) = db.conn() {
                                let _ = library::update_play_count(&conn, track_id);
                                println!("[audio] Play count updated for track_id={}", track_id);
                            }
                        });
                        play_count_state.threshold_reached = true;
                    }
                }
            }

            // Check scrobble threshold (90% default, configurable)
            if !scrobble_state.threshold_reached
               && progress.duration_ms > 0
               && scrobble_state.track_id.is_some() {
                let ratio = progress.position_ms as f64 / progress.duration_ms as f64;

                if ratio >= scrobble_state.threshold_percent {
                    if let Some(track_id) = scrobble_state.track_id {
                        // Spawn async task to avoid blocking audio thread
                        let app_handle = app.clone();
                        std::thread::spawn(move || {
                            use crate::commands::lastfm;
                            use crate::db::Database;

                            let db = app_handle.state::<Database>();
                            if let Ok(conn) = db.conn() {
                                // Queue scrobble from audio thread
                                match lastfm::scrobble_from_audio_thread(&app_handle, &conn, track_id) {
                                    Ok(_) => println!("[audio] Scrobble queued for track_id={}", track_id),
                                    Err(e) => eprintln!("[audio] Failed to queue scrobble: {}", e),
                                }
                            }
                        });
                        scrobble_state.threshold_reached = true;
                    }
                }
            }
        }

        if is_finished && !last_finished {
            let _ = app.emit("audio://track-ended", ());
        }
        last_finished = is_finished;
    }
}

#[tauri::command]
pub fn audio_load(path: String, track_id: Option<i64>, state: State<AudioState>) -> Result<TrackInfo, String> {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::Load(path, track_id, tx));
    rx.recv().map_err(|_| "Channel closed".to_string())?
}

#[tauri::command]
pub fn audio_play(state: State<AudioState>) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::Play(tx));
    rx.recv().map_err(|_| "Channel closed".to_string())?
}

#[tauri::command]
pub fn audio_pause(state: State<AudioState>) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::Pause(tx));
    rx.recv().map_err(|_| "Channel closed".to_string())?
}

#[tauri::command]
pub fn audio_stop(state: State<AudioState>) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::Stop(tx));
    rx.recv().map_err(|_| "Channel closed".to_string())?
}

#[tauri::command]
pub fn audio_seek(position_ms: u64, state: State<AudioState>) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::Seek(position_ms, tx));
    rx.recv().map_err(|_| "Channel closed".to_string())?
}

#[tauri::command]
pub fn audio_set_volume(volume: f32, state: State<AudioState>) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::SetVolume(volume, tx));
    rx.recv().map_err(|_| "Channel closed".to_string())?
}

#[tauri::command]
pub fn audio_get_volume(state: State<AudioState>) -> f32 {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::GetVolume(tx));
    rx.recv().unwrap_or(1.0)
}

#[tauri::command]
pub fn audio_get_status(state: State<AudioState>) -> PlaybackStatus {
    let (tx, rx) = mpsc::channel();
    state.send_command(AudioCommand::GetStatus(tx));
    rx.recv().unwrap_or(PlaybackStatus {
        position_ms: 0,
        duration_ms: 0,
        state: PlaybackState::Stopped,
        volume: 1.0,
        track: None,
    })
}
