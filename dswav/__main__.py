import gradio as gr
import os
import subprocess
from dswav.config import Config
from dswav.ds import process, add_silence_if_needed


def build_handler(project_name, input_path, lang, multi_sentence_share, merges: str):
    config = Config(
        project_name=project_name,
        input_path=input_path,
        lang=lang,
        multi_sentence_share=multi_sentence_share,
        merges=list(map(lambda x: x.strip(), merges.split("\n"))),
    )

    if not os.path.exists(config.project_path):
        os.mkdir(config.project_path)

    if not os.path.exists(f"{config.project_path}/ds"):
        os.mkdir(f"{config.project_path}/ds")

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

    process(config)

    return "done"


def fix_audio_handler(project_name):
    add_silence_if_needed(f"./projects/{project_name}/ds/wavs")


if __name__ == "__main__":
    DEV = os.environ.get("USER") == "devidw"

    with gr.Blocks(title="dswav") as ui:
        project_name = gr.Textbox(
            label="Project Name",
            value="example" if not DEV else "allison_1h",
        )
        with gr.Tab("builder"):
            input_path = gr.Textbox(
                label="Input Audio File Path",
                value="./projects/example/audio.mp3"
                if not DEV
                else "/Users/devidw/Desktop/allison_1h.wav",
            )
            lang = gr.Textbox(
                label="Input Audio Language Code",
                value="en",
            )
            multi_sentence_share = gr.Number(
                label="Percentage of dataset examples with multiple sentences",
                value=10,
            )
            merges = gr.TextArea(
                label="""
                        List of paths to folders with contents of /index.json [{id: string, content: string}]
                        and /wavs/{id}.wav that will be merged with dataset
                        One path per line
                        All those are ensured to go into train_list and won't be used when sampling val_list (1%)
                        """,
                value="" if not DEV else "/Users/devidw/Desktop/allison_voice 2",
            )
            button = gr.Button("Process")
            output = gr.Textbox(label="Output")
            button.click(
                build_handler,
                inputs=[
                    project_name,
                    input_path,
                    lang,
                    multi_sentence_share,
                    merges,
                ],
                outputs=[output],
            )
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
    ui.launch(server_name="0.0.0.0")
