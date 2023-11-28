import gradio as gr
import os
import subprocess
from dswav.config import Config
from dswav.ds import transcribe, add_silence_if_needed, combine_many, build_ds


def transcribe_handler(project_name, input_path, lang):
    config = Config(
        project_name=project_name,
        input_path=input_path,
        lang=lang,
    )
    transcribe(config)
    print("done")


def fix_audio_handler(project_name):
    add_silence_if_needed(project_name)
    print("done")


def merge_handler(project_name: str, merges: str):
    paths = list(map(lambda x: x.strip(), merges.split("\n")))
    combine_many(project_name, paths)
    print("done")


def setup_handler(project_name: str):
    if not os.path.exists(f"./projects/{project_name}"):
        os.mkdir(f"./projects/{project_name}")

    if not os.path.exists(f"./projects/{project_name}/ds"):
        os.mkdir(f"./projects/{project_name}/ds")

    if not os.path.exists(f"./projects/{project_name}/ds/wavs"):
        os.mkdir(f"./projects/{project_name}/ds/wavs")

    print("done")


def build_handler(project_name: str):
    build_ds(project_name)
    print("done")


if __name__ == "__main__":
    DEV = os.environ.get("USER") == "devidw"
    CONFIG = {}

    if DEV:
        with open("./config.json", "r") as f:
            import json

            CONFIG = json.loads(f.read())

    with gr.Blocks(title="dswav") as ui:
        project_name = gr.Textbox(
            label="Project Name",
            value="example" if not DEV else CONFIG["project_name"],
        )
        button = gr.Button()
        button.click(setup_handler, inputs=[project_name])

        with gr.Tab("build"):
            button = gr.Button()
            button.click(build_handler, inputs=[project_name])

        with gr.Tab("combine"):
            merges = gr.TextArea(
                label="""
                        List of paths to folders with contents of /index.json [{id: string, content: string}]
                        and /wavs/{id}.wav that will be merged with dataset
                        One path per line
                        """,
                value="" if not DEV else CONFIG["merges"],
            )
            button = gr.Button()
            button.click(merge_handler, inputs=[project_name, merges])

        with gr.Tab("fix audio length"):
            gr.Markdown(
                """
            > The fix is very simple though: Remove short <1s audiofiles or merge them into longer files with merged
            transcripts. Ensure that max_len is at least 100.

            https://github.com/yl4579/StyleTTS2/discussions/81
            """
            )
            button = gr.Button()
            button.click(fix_audio_handler, inputs=[project_name])

        with gr.Tab("transcribe"):
            input_path = gr.Textbox(
                label="Input Audio File Path",
                value="./projects/example/audio.mp3"
                if not DEV
                else CONFIG["audio_input"],
            )
            lang = gr.Textbox(
                label="Input Audio Language Code",
                value="en",
            )
            button = gr.Button("Process")
            button.click(
                transcribe_handler,
                inputs=[
                    project_name,
                    input_path,
                    lang,
                ],
            )

    ui.launch(server_name="0.0.0.0")
