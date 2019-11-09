FROM python:3.7-alpine3.10

LABEL maintainer="Roxedus"

COPY / /app

RUN python3 -m pip install -r /app/requirements.txt

WORKDIR /app

CMD python3 /app/lovherk.py