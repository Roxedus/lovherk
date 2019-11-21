FROM python:3.7-alpine3.10

LABEL maintainer="Roxedus"

COPY / /app

RUN apk add --no-cache --virtual=build-dependencies  --update .build-deps gcc musl-dev

RUN python3 -m pip install -r /app/requirements.txt

RUN apk del build-dependencies

WORKDIR /app

CMD python3 /app/lovherk.py
