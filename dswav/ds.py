import json
import shutil
import subprocess
from typing import List
import uuid
from dswav.config import Config
from concurrent.futures import ThreadPoolExecutor
import random
import eng_to_ipa as ipa


class Word:
    word: str
    start: float
    end: float

    def __init__(self, word, start, end) -> None:
        self.word = word
        self.start = start
        self.end = end


class Sentence:
    words: List[Word]
    id: str

    def __init__(self, words: List[Word]) -> None:
        self.words = words
        self.id = str(uuid.uuid4())

    @property
    def ipa(self):
        return ipa.convert(self.sentence)

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


def get_sentences(words: List[Word]):
    sentences: List[Sentence] = []
    tmp: Sentence = Sentence([])
    for word in words:
        tmp.words.append(word)
        if (
            word.word == "."
            or word.word.endswith("..")
            or word.word.endswith("?")
            or word.word.endswith("!")
        ) and (
            not tmp.sentence.lower().endswith(" mr.")
            and not tmp.sentence.lower().endswith(" ms.")
        ):
            sentences.append(tmp)
            tmp = Sentence([])
    return sentences


def process(config: Config):
    with open(config.stt_out_path, "r") as file:
        stt_data = json.load(file)

    words = flatten(stt_data["segments"])
    sentences = get_sentences(words)

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

    with open(f"{config.project_path}/ds/metadata.csv", "w") as f:
        csv_content = "\n".join(
            [f"{s.id}|{s.sentence}|{s.sentence}" for s in sentences]
        )
        f.write(csv_content)

    train_list, val_list = split_list(sentences, 0.99)

    with open(f"{config.project_path}/ds/train_list.txt", "w") as f:
        data = "\n".join([f"{line.id}.wav|{line.ipa}" for line in train_list])
        f.write(data)

    with open(f"{config.project_path}/ds/val_list.txt", "w") as f:
        data = "\n".join([f"{line.id}.wav|{line.ipa}" for line in val_list])
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
