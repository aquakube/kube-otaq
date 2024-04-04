FROM python:3.11-bullseye

RUN apt update --fix-missing && \
    apt install -o Acquire::BrokenProxy="true" \
    -o Acquire::http::No-Cache="true" \
    -o Acquire::http::Pipeline-Depth="0" \
    -y sudo nmap arping iputils-ping ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY . /usr/src/app

WORKDIR /usr/src/app/src

RUN pip install --upgrade pip

RUN pip install pipenv

RUN pipenv lock && pipenv install --system --deploy

ENTRYPOINT ["/bin/bash", "-l", "-c"]