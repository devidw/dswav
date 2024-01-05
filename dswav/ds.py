import json
import shutil
import subprocess
from typing import Dict, List, Optional
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
from nltk.tokenize import word_tokenize
import random


# MAX_LEN = 512
MAX_LEN = 400
SILENCE_EOS = " …"
SILENCE_LENGTH_MS = 100
# DS_SIZE_LIMIT = 17
DS_SIZE_LIMIT = None


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
            list(
                map(
                    lambda x: Sentence(
                        x["id"],
                        x["content"],
                        [],
                        speaker_id=x["speaker_id"],
                    ),
                    index,
                )
            )
        )
        # copy_files(f"{merge}/wavs", f"./projects/{project_name}/ds/wavs")
    write_sentences(project_name, sentences)


def build_ds(project_name: str, add_ending_silence: bool):
    sentences: List[Sentence] = read_sentences(project_name)

    if DS_SIZE_LIMIT:
        random.shuffle(sentences)
        sentences = sentences[:DS_SIZE_LIMIT]

    SPEAKER_IDS: Dict[str, int] = {}

    for sentence in sentences:
        if sentence.speaker_id in SPEAKER_IDS:
            continue
        SPEAKER_IDS[sentence.speaker_id] = len(SPEAKER_IDS.keys()) + 1

    print(SPEAKER_IDS)

    # with open(f"./projects/{project_name}/ds/metadata.csv", "w") as f:
    #     csv_content = "\n".join(
    #         [f"{s.id}|{s.sentence}|{s.sentence}" for s in sentences]
    #     )
    #     f.write(csv_content)

    def get_phonemes(sentence: Sentence):
        try:
            the_text = (
                sentence.sentence
                if not add_ending_silence
                else f"{sentence.sentence}{SILENCE_EOS}"
            )
            if the_text == "":
                return None
            # token_count = len(word_tokenize(the_text))
            # if token_count > MAX_LEN:
            #     return None
            if len(the_text) > MAX_LEN:
                return None
            return text_to_phonemes(the_text)
        except:
            return None

    l0 = len(sentences)
    lines = list(
        filter(
            lambda x: x["content"] != None,
            map(
                lambda x: {
                    "sentence": x,
                    "id": x.id,
                    "content": get_phonemes(x),
                    "speaker_id": SPEAKER_IDS[x.speaker_id],
                },
                sentences,
            ),
        )
    )
    l1 = len(lines)
    print(
        f"{l0-l1} samples dropped due to being too long or too short, <=0 or >{MAX_LEN}"
    )

    train_list, val_list = split_list(lines, 0.99)

    with open(f"./projects/{project_name}/debug.json", "w") as f:
        json.dump(
            list(
                map(
                    lambda x: {
                        **x,
                        "sentence": x["sentence"].content,
                    },
                    lines,
                )
            ),
            f,
            indent=4,
            ensure_ascii=False,
        )

    with open(f"./projects/{project_name}/ds/train_list.txt", "w") as f:
        data = "\n".join(
            [
                f"{line['id']}.wav|{line['content']}|{line['speaker_id']}"
                for line in train_list
            ]
        )
        f.write(data)

    with open(f"./projects/{project_name}/ds/val_list.txt", "w") as f:
        data = "\n".join(
            [
                f"{line['id']}.wav|{line['content']}|{line['speaker_id']}"
                for line in val_list
            ]
        )
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
