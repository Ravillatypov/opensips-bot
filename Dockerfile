FROM python:3.8-alpine

WORKDIR /code
CMD ["python", "main.py"]
VOLUME /data

RUN apk add --update --no-cache postgresql-libs

COPY requirements.txt /requirements.txt
RUN apk add --update --no-cache --virtual .tmp-build-deps \
        build-base python3-dev libffi-dev coreutils openssl-dev && \
    pip install --no-cache-dir -U pip cryptography && \
    pip install --no-cache-dir --no-use-pep517 -r /requirements.txt && \
    apk del .tmp-build-deps

COPY . /code
