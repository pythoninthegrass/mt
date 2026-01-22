mod audio;
mod favorites;
mod playlists;
mod queue;
mod settings;

pub use audio::{
    audio_get_status, audio_get_volume, audio_load, audio_pause, audio_play, audio_seek,
    audio_set_volume, audio_stop, AudioState, PlaybackStatus,
};

pub use favorites::{
    favorites_add, favorites_check, favorites_get, favorites_get_recently_added,
    favorites_get_recently_played, favorites_get_top25, favorites_remove,
};

pub use playlists::{
    playlist_add_tracks, playlist_create, playlist_delete, playlist_generate_name, playlist_get,
    playlist_list, playlist_remove_track, playlist_reorder_tracks, playlist_update,
    playlists_reorder,
};

pub use queue::{
    queue_add, queue_add_files, queue_clear, queue_get, queue_remove, queue_reorder,
    queue_shuffle,
};

pub use settings::{
    settings_get, settings_get_all, settings_reset, settings_set, settings_update,
};
