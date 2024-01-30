# dswav

Tool to build dataset for audio model training

Includes a series of helpers for dataset work, such as:

- transcribing audio source into a dataset of segments of text & audio pairs
- combining differnt data sources
- bulk lengthening audio samples
- bulk conversation of mp3s to wav at given sample rate
- building metadata files that can be used for training

Mostly focused around tooling for [StyleTTS2](https://github.com/yl4579/StyleTTS2) datasets, but can also be
used for other kinds of models / libraries such as [coqui](https://github.com/coqui-ai/TTS)

## Usage

```bash
docker run \
  -p 7860:7860 \
  -v ./projects:/app/projects \
  ghcr.io/devidw/dswav:main
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

## Data sources

In order to import other data sources they must follow this structure:

- /your/path/index.json
- /your/path/wavs/[id].wav

```ts
{
    id: string // unique identifier for each sample, should match file name in `./wavs/[id].wav` folder
    content: string // the transcript
    speaker_id?: string // optional when building for multi-speaker, unique on a per voice speaker basis
}[]
```

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