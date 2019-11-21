FROM python:3.7-alpine3.10

LABEL maintainer="Roxedus"

COPY / /app

RUN apt-get update %% apt-get install -y gcc && rm -rf /tmp/* /var/lib/apt/lists/* /var/tmp/*

RUN python3 -m pip install -r /app/requirements.txt

WORKDIR /app

CMD python3 /app/lovherk.py
