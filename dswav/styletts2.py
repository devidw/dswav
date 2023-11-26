import nltk
from nltk.tokenize import word_tokenize
import phonemizer

nltk.download("punkt")

global_phonemizer = phonemizer.backend.EspeakBackend(
    language="en-us",
    preserve_punctuation=True,
    with_stress=True,
)


def text_to_phonemes(text):
    text = text.strip()
    ps = global_phonemizer.phonemize([text])
    ps = word_tokenize(ps[0])
    ps = " ".join(ps)
    return ps
