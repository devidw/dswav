# dswav

Tool to build dataset for audio model training

Takes single audio input file 

Transcribes it using whisper and splits into sentences, chunks audio using ffmpeg into samples

And builds metadata files that can be used for training

## Usage

```bash
git clone https://github.com/devidw/dswav
cd dswav

make docker_build

make docker_run
```

## TTS, LJSpeech

https://tts.readthedocs.io/en/latest/formatting_your_dataset.html

Supports output in LJSpeech dataset format (`metadata.csv`, `wavs/`) that can be used in the `TTS` py pkg to train models such as xtts2

## StyleTTS2

https://github.com/yl4579/StyleTTS2

Also supports output format for StyleTTS2

- `train_list.txt` 99 %
- `val_list.txt` 1 %
- `wavs/`

## Development

- need ffmpeg, espeak, whipser

```bash
git clone https://github.com/devidw/dswav
cd dswav

poetry install

make dev
```

## notes

- currently splitting based on sentences and not silence, which sometimes still keeps artifacts at the end, should
  rather detect silence to have clean examples