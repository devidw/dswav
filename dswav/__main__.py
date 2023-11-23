import gradio as gr
import os
import subprocess
from dswav.config import Config
from dswav.ds import process


def handler(project_name, input_path, lang):
    config = Config(
        project_name=project_name,
        input_path=input_path,
        lang=lang,
    )

    if not os.path.exists(config.project_path):
        os.mkdir(config.project_path)

    if not os.path.exists(f"{config.project_path}/ds"):
        os.mkdir(f"{config.project_path}/ds")

    if not os.path.exists(f"{config.project_path}/ds/wavs"):
        os.mkdir(f"{config.project_path}/ds/wavs")

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


if __name__ == "__main__":
    with gr.Blocks(title="dswav") as ui:
        project_name = gr.Textbox(
            label="Project Name",
            value="example",
        )
        input_path = gr.Textbox(
            label="Input Audio File Path",
            value="./projects/example/audio.mp3",
        )
        lang = gr.Textbox(
            label="Input Audio Language Code",
            value="en",
        )
        button = gr.Button("Process")
        output = gr.Textbox(label="Output")
        button.click(handler, inputs=[project_name, input_path, lang], outputs=[output])
    ui.launch()
