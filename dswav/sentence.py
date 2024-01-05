import json
from typing import List, Optional
import random
from dswav.styletts2 import text_to_phonemes


MULTI_SENTENCE_SHARE = 10


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
    _id: Optional[str] = None
    words: List[Word]
    content: str = ""
    speaker_id: str = ""

    def __init__(
        self,
        id: Optional[str],
        content: str,
        words: List[Word],
        speaker_id: str,
    ) -> None:
        self._id = id if id else None
        self.words = words
        self.content = content
        self.speaker_id = speaker_id

    def to_dict(self):
        return {
            "id": self.id,
            "speaker_id": self.speaker_id,
            "content": self.content,
            "words": [word.to_dict() for word in self.words],
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
            return self.content.strip()
        else:
            print(self.to_dict())
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


def read_sentences(project_name: str):
    sentences: List[Sentence] = []

    with open(f"./projects/{project_name}/sentences.json", "r") as f:
        raw = json.loads(f.read())

    for single in raw:
        words = list(
            map(
                lambda x: Word(x["word"], x["start"], x["end"]),
                single["words"],
            )
        )
        sentence = Sentence(
            single["id"],
            single["content"],
            words,
            speaker_id=single["speaker_id"],
        )
        sentences.append(sentence)

    return sentences


def write_sentences(project_name: str, sentences: List[Sentence]):
    with open(f"./projects/{project_name}/sentences.json", "w") as f:
        f.write(
            json.dumps(
                list(map(lambda x: x.to_dict(), sentences)),
                indent=4,
            )
        )


def compute_sentences(words: List[Word]):
    """ """
    sentences: List[Sentence] = []
    tmp: Sentence = Sentence(None, "", [], "")
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
                        MULTI_SENTENCE_SHARE,
                        100.0 - MULTI_SENTENCE_SHARE,
                    ],
                    k=1,
                )[0]
            ):
                is_multi = True
                continue

            sentences.append(tmp)
            tmp = Sentence(None, "", [], "")
            is_multi = False

    return sentences
