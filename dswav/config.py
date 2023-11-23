import os


class Config:
    project_name: str
    input_path: str
    lang: str

    def __init__(self, project_name, input_path, lang) -> None:
        self.project_name = project_name
        self.input_path = input_path
        self.lang = lang

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
