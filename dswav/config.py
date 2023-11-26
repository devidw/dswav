import os


class Config:
    project_name: str
    input_path: str
    lang: str
    multi_sentence_share: float

    def __init__(self, project_name, input_path, lang, multi_sentence_share) -> None:
        self.project_name = project_name
        self.input_path = input_path
        self.lang = lang
        self.multi_sentence_share = multi_sentence_share

    def to_dict(self):
        return {
            "project_name": self.project_name,
            "input_path": self.input_path,
            "lang": self.lang,
            "multi_sentence_share": self.multi_sentence_share,
        }

    @property
    def project_path(self):
        relative_path = f"./projects/{self.project_name}"
        return os.path.abspath(relative_path)

    @property
    def stt_out_path(self):
        basename = os.path.basename(self.input_path)
        # Change the extension to .json
        json_basename = os.path.splitext(basename)[0] + ".json"
        return os.path.join(self.project_path, json_basename)
