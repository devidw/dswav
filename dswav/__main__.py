import gradio as gr
import os
import subprocess
from dswav.config import Config
from dswav.ds import (
    transcribe,
    add_silence_if_needed,
    combine_many,
    build_ds,
    add_silence,
)


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


def add_ending_silence_handler(project_name):
    add_silence(project_name)
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


def build_handler(project_name: str, add_silent_endings: bool):
    build_ds(project_name, add_silent_endings)
    print("done")


def convert_mp3_to_wav_handler(sample_rate, input_path, output_path):
    subprocess.run(
        [
            "./scripts/mp3-to-wav.sh",
            input_path,
            output_path,
            sample_rate,
        ]
    )
    print("done")


def upload_handler(project_name: str, scp_cmd: str):
    args = scp_cmd.replace("%", f"./projects/{project_name}/ds.zip").split(" ")
    print(args)
    subprocess.run(args)


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
            add_silent_endings = gr.Checkbox(
                label="add eos sequence ' …' to text, to avoid artifacts at the end by teaching to end in silence, need to inference with eos: ' …' - requires to use `add ending silences` tool before to have actual silence endings in audio samples"
            )
            button = gr.Button()
            button.click(build_handler, inputs=[project_name, add_silent_endings])

        with gr.Tab("upload"):
            gr.Markdown(
                """
                Use "%" for the local source path of the build ds.zip file
                """
            )
            scp_cmd = gr.Textbox(
                label="cmd", value="" if not DEV else CONFIG["scp_cmd"]
            )
            button = gr.Button()
            button.click(upload_handler, inputs=[project_name, scp_cmd])

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

        with gr.Tab("add ending silences"):
            gr.Markdown(
                """
            https://github.com/yl4579/StyleTTS2/discussions/81#discussioncomment-7736076
            """
            )
            button = gr.Button()
            button.click(add_ending_silence_handler, inputs=[project_name])

        with gr.Tab("mp3 to wav @ sr"):
            sr = gr.Textbox(label="Sample Rate", value="22050")
            input_path = gr.Textbox(label="input mp3s path")
            output_path = gr.Textbox(label="output wavs path")
            button = gr.Button()
            button.click(
                convert_mp3_to_wav_handler, inputs=[sr, input_path, output_path]
            )

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
