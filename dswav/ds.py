import json
import shutil
import subprocess
from typing import List, Optional
from dswav.config import Config
from concurrent.futures import ThreadPoolExecutor
import os
from dswav.utils import copy_files, split_list
from pydub import AudioSegment
from dswav.sentence import (
    Sentence,
    compute_sentences,
    flatten,
    read_sentences,
    write_sentences,
    read_sentences,
)
from dswav.styletts2 import text_to_phonemes


SILENCE_EOS = " …"
SILENCE_LENGTH_MS = 100


def add_silence_if_needed(project_name: str):
    for filename in os.listdir(f"./projects/{project_name}/ds/wavs"):
        if filename.endswith(".wav"):
            file_path = os.path.join(f"./projects/{project_name}/ds/wavs", filename)
            audio = AudioSegment.from_wav(file_path)

            if len(audio) < 1000:  # Audio length less than 1000 ms (1 second)
                silence = AudioSegment.silent(duration=1000 - len(audio) + 1)
                new_audio = audio + silence
                new_audio.export(file_path, format="wav")  # Overwrite original file
                print(f"done {file_path}")


def add_silence(project_name: str):
    for filename in os.listdir(f"./projects/{project_name}/ds/wavs"):
        if not filename.endswith(".wav"):
            continue
        file_path = os.path.join(f"./projects/{project_name}/ds/wavs", filename)
        audio = AudioSegment.from_wav(file_path)
        silence = AudioSegment.silent(duration=SILENCE_LENGTH_MS)
        new_audio = audio + silence
        new_audio.export(file_path, format="wav")
        print(f"done {file_path}")


def combine_many(project_name: str, merges: List[str]):
    sentences: List[Sentence] = []
    for merge in merges:
        with open(f"{merge}/index.json", "r") as f:
            index = json.loads(f.read())
        sentences.extend(
            list(map(lambda x: Sentence(x["id"], x["content"], []), index))
        )
        copy_files(f"{merge}/wavs", f"./projects/{project_name}/ds/wavs")
    write_sentences(project_name, sentences)


def build_ds(project_name: str, add_ending_silence: bool):
    sentences: List[Sentence] = read_sentences(project_name)

    train_list, val_list = split_list(sentences, 0.99)

    with open(f"./projects/{project_name}/ds/metadata.csv", "w") as f:
        csv_content = "\n".join(
            [f"{s.id}|{s.sentence}|{s.sentence}" for s in sentences]
        )
        f.write(csv_content)

    def get_phonemes(sentence: Sentence):
        return text_to_phonemes(
            sentence.sentence
            if not add_ending_silence
            else f"{sentence.sentence}{SILENCE_EOS}"
        )

    with open(f"./projects/{project_name}/ds/train_list.txt", "w") as f:
        data = "\n".join(
            [f"{line.id}.wav|{get_phonemes(line)}|0" for line in train_list]
        )
        f.write(data)

    with open(f"./projects/{project_name}/ds/val_list.txt", "w") as f:
        data = "\n".join([f"{line.id}.wav|{get_phonemes(line)}|0" for line in val_list])
        f.write(data)

    shutil.make_archive(
        f"./projects/{project_name}/ds",
        "zip",
        f"./projects/{project_name}/ds",
    )


def transcribe(config: Config):
    """ """

    if not os.path.exists(config.stt_out_path):
        subprocess.run(
            [
                "make",
                "stt",
                f"FILE={config.input_path}",
                f"OUT_DIR={config.project_path}",
                f"LANG={config.lang}",
            ]
        )

    with open(config.stt_out_path, "r") as file:
        stt_data = json.load(file)

    words = flatten(stt_data["segments"])
    sentences = compute_sentences(words)
    write_sentences(config.project_name, sentences)

    def process_sentence(filename: str, sentence: Sentence):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                config.input_path,
                "-ss",
                str(sentence.start),
                "-t",
                str(sentence.duration),
                "-acodec",
                "copy",
                f"{config.project_path}/ds/wavs/{filename}.wav",
            ],
        )

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = []
        for sentence in sentences:
            futures.append(
                executor.submit(process_sentence, str(sentence.id), sentence)
            )
        for future in futures:
            future.result()
