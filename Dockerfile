FROM python:3.11-slim-bullseye
ARG BUILD_NAME
LABEL build=${BUILD_NAME}

ENV TZ="Europe/Prague"

RUN \
    apt-get update &&\
    apt-get install -y --no-install-recommends tini && \
    apt-get install -y curl &&\
    pip install -U pip &&\
    pip install poetry &&\
    poetry config virtualenvs.create true &&\
    poetry config virtualenvs.in-project true

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN touch README.md
RUN poetry install

COPY . .

# install current project
RUN poetry install

USER nobody

ENTRYPOINT ["tini", "--"]
