#!/bin/bash

IN_DIR=$1
OUT_DIR=$2
SR=$3


# Loop through each MP3 file in the directory
for file in "$IN_DIR"/*.mp3; do
    # Skip if not a file
    [ -f "$file" ] || continue

    # Construct the WAV filename
    base_name=$(basename "$file" .mp3)

    # Convert MP3 to WAV using FFmpeg
    ffmpeg -i "$file" -ar $SR "$OUT_DIR/$base_name.wav"
done
