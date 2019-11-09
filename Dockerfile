FROM python:3.7-alpine3.10

LABEL maintainer="Roxedus"

COPY / /app

RUN python3 -m pip install -r /app/requirements.txt

WORKDIR /app

CMD cp config.json.example config.json && ln -sf /app/data /config && ln -sf config.json /config/config.json && python3 /app/bot.py

VOLUME /config