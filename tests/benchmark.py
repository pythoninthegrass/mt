#!/usr/bin/env python

import sys
from core._scan import benchmark_directory, count_audio_files

music_dir = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/shares/Music"

avg_time_ms = benchmark_directory(music_dir, 3)
avg_time_sec = avg_time_ms / 1000

total_files = count_audio_files(music_dir)

print(f"Total audio files: {total_files}")  # Total audio files: 11079
print(f"Average scan time: {avg_time_sec:.3f} seconds")  # Average scan time: 85.015 seconds
