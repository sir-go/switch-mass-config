FROM python:3.10-alpine3.16
WORKDIR /app

RUN apk add --update  \
    gcc  \
    net-snmp-tools  \
    net-snmp-dev  \
    musl-dev  \
    make  \
    findutils

COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

COPY swlib ./swlib
COPY config.py run.py ./

CMD [ "python", "run.py"]
