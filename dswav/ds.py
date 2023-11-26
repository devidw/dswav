import json
import shutil
import subprocess
from typing import List
import uuid
from dswav.config import Config
from concurrent.futures import ThreadPoolExecutor
import random
from dswav.styletts2 import text_to_phonemes
import os


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
    id: str

    def __init__(self, words: List[Word]) -> None:
        self.words = words
        self.id = str(uuid.uuid4())

    def to_dict(self):
        return {
            "id": self.id,
            "words": [word.to_dict() for word in self.words],
            "phonemes": self.phonemes,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "sentence": self.sentence,
        }

    @property
    def phonemes(self):
        return text_to_phonemes(self.sentence)

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
        return "".join(map(lambda x: x.word, self.words)).strip()


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
        tmp: Sentence = Sentence([])
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
                tmp = Sentence([])
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
        sentence = Sentence(words)
        sentence.id = single["id"]
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

    if not os.path.exists(f"{config.project_path}/ds/wavs"):
        os.mkdir(f"{config.project_path}/ds/wavs")

        with ThreadPoolExecutor(max_workers=32) as executor:
            futures = []
            for sentence in sentences:
                futures.append(
                    executor.submit(process_sentence, str(sentence.id), sentence)
                )
            for future in futures:
                future.result()

    with open(f"{config.project_path}/ds/metadata.csv", "w") as f:
        csv_content = "\n".join(
            [f"{s.id}|{s.sentence}|{s.sentence}" for s in sentences]
        )
        f.write(csv_content)

    train_list, val_list = split_list(sentences, 0.99)

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


def split_list(input_list, percentage):
    """
    Splits a list into two parts with the given percentage.

    :param input_list: The list to be split.
    :param percentage: The percentage of the first list (between 0 and 1).
    :return: Two lists.
    """
    if not 0 <= percentage <= 1:
        raise ValueError("Percentage must be between 0 and 1")

    list_length = len(input_list)
    split_index = int(list_length * percentage)

    random.shuffle(input_list)
    return input_list[:split_index], input_list[split_index:]
