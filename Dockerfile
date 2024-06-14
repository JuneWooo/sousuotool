
FROM amd64/python:3.10

WORKDIR /app
COPY . /app


RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt 

RUN playwright install chromium

RUN playwright install-deps
