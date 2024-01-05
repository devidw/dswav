#!/bin/bash

IN_DIR=$1
OUT_DIR=$2
SR=$3

export OUT_DIR SR  # Export these variables so they're available to subshells

find "$IN_DIR" -name '*.mp3' | parallel -I% --max-args 1 ffmpeg -i % -ar $SR "$OUT_DIR/{/.}.wav"