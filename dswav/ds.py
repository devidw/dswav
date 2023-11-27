import json
import shutil
import subprocess
from typing import List, Optional
import uuid
from dswav.config import Config
from concurrent.futures import ThreadPoolExecutor
import random
from dswav.styletts2 import text_to_phonemes
import os
from dswav.utils import copy_files, split_list
from pydub import AudioSegment


class Word:
    word: str
    start: float
    end: float

    def __init__(self, word, start, end) -> None:
        self.word = word
        self.start = start
        self.end = end

    def to_dict(self):
        return {
            "word": self.word,
            "start": self.start,
            "end": self.end,
        }


class Sentence:
    words: List[Word]
    content: str = ""
    _id: Optional[str] = None

    def __init__(self, id: Optional[str], content: str, words: List[Word]) -> None:
        self._id = id if id else None
        self.content = content
        self.words = words

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "words": [word.to_dict() for word in self.words],
            "phonemes": self.phonemes,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "sentence": self.sentence,
        }

    @property
    def id(self):
        if self._id:
            return self._id
        return f"{self.start}-{self.end}"

    @property
    def start(self):
        return self.words[0].start

    @property
    def end(self):
        return self.words[-1].end

    @property
    def duration(self):
        return self.end - self.start

    @property
    def sentence(self):
        if len(self.words) > 0 and len(self.content) == 0:
            return "".join(map(lambda x: x.word, self.words)).strip()
        elif len(self.words) == 0 and len(self.content) > 0:
            return self.content
        else:
            raise Exception("bad sentence has content and words should only have one")

    @property
    def phonemes(self):
        return text_to_phonemes(self.sentence)


def flatten(segments):
    words: List[Word] = []
    for segment in segments:
        for word in segment["words"]:
            words.append(
                Word(
                    word["word"],
                    word["start"],
                    word["end"],
                )
            )
    return words


def process(config: Config):
    """ """

    def get_sentences(words: List[Word]):
        """ """
        sentences: List[Sentence] = []
        tmp: Sentence = Sentence(None, "", [])
        is_multi = False

        for word in words:
            tmp.words.append(word)
            if (
                tmp.duration >= 1
                and (
                    word.word == "."
                    or word.word.endswith("..")
                    or word.word.endswith("?")
                    or word.word.endswith("!")
                )
                and (
                    not tmp.sentence.lower().endswith(" mr.")
                    and not tmp.sentence.lower().endswith(" ms.")
                )
            ):
                if (
                    not is_multi
                    and random.choices(
                        population=[True, False],
                        weights=[
                            config.multi_sentence_share,
                            100.0 - config.multi_sentence_share,
                        ],
                        k=1,
                    )[0]
                ):
                    is_multi = True
                    continue

                sentences.append(tmp)
                tmp = Sentence(None, "", [])
                is_multi = False

        return sentences

    with open(config.stt_out_path, "r") as file:
        stt_data = json.load(file)

    if not os.path.exists(f"{config.project_path}/sentences.json"):
        words = flatten(stt_data["segments"])
        sentences = get_sentences(words)

        with open(f"{config.project_path}/sentences.json", "w") as f:
            f.write(
                json.dumps(
                    list(map(lambda x: x.to_dict(), sentences)),
                    indent=4,
                )
            )

    with open(f"{config.project_path}/sentences.json", "r") as f:
        raw = json.loads(f.read())

    sentences: List[Sentence] = []

    for single in raw:
        words = list(
            map(lambda x: Word(x["word"], x["start"], x["end"]), single["words"])
        )
        sentence = Sentence(None, "", words)
        sentences.append(sentence)

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

    # if not os.path.exists(f"{config.project_path}/ds/wavs"):
    #     os.mkdir(f"{config.project_path}/ds/wavs")

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = []
        for sentence in sentences:
            futures.append(
                executor.submit(process_sentence, str(sentence.id), sentence)
            )
        for future in futures:
            future.result()

    train_list, val_list = split_list(sentences, 0.99)

    merge_sentences = add_merges(config)

    train_list.extend(merge_sentences)

    with open(f"{config.project_path}/ds/metadata.csv", "w") as f:
        csv_content = "\n".join(
            [f"{s.id}|{s.sentence}|{s.sentence}" for s in sentences + merge_sentences]
        )
        f.write(csv_content)

    with open(f"{config.project_path}/ds/train_list.txt", "w") as f:
        data = "\n".join([f"{line.id}.wav|{line.phonemes}|0" for line in train_list])
        f.write(data)

    with open(f"{config.project_path}/ds/val_list.txt", "w") as f:
        data = "\n".join([f"{line.id}.wav|{line.phonemes}|0" for line in val_list])
        f.write(data)

    shutil.make_archive(
        f"{config.project_path}/{config.project_name}",
        "zip",
        f"{config.project_path}/ds",
    )


def add_merges(config: Config):
    sentences: List[Sentence] = []
    for merge in config.merges:
        with open(f"{merge}/index.json", "r") as f:
            index = json.loads(f.read())
        sentences.extend(
            list(map(lambda x: Sentence(x["id"], x["content"], []), index))
        )
        copy_files(f"{merge}/wavs", f"{config.project_path}/ds/wavs")
    return sentences


def add_silence_if_needed(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".wav"):
            file_path = os.path.join(folder_path, filename)
            audio = AudioSegment.from_wav(file_path)

            if len(audio) < 1000:  # Audio length less than 1000 ms (1 second)
                silence = AudioSegment.silent(duration=1000 - len(audio))
                new_audio = audio + silence
                new_audio.export(file_path, format="wav")  # Overwrite original file
                print(f"done {file_path}")
