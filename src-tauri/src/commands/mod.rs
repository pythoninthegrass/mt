mod audio;
mod playlists;
mod queue;

pub use audio::{
    audio_get_status, audio_get_volume, audio_load, audio_pause, audio_play, audio_seek,
    audio_set_volume, audio_stop, AudioState, PlaybackStatus,
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
