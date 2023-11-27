FROM python:3.11-bullseye

RUN apt-get update && \
    apt-get install ffmpeg espeak -y

# todo, whisper.cpp?
RUN pip install openai-whisper

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-root

COPY . /app/

CMD [ "python", "-m", "dswav" ]
EXPOSE 7860