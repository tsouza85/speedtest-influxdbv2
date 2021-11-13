# Multistage build setup
FROM debian:bullseye-slim as speedtest-builder

WORKDIR /usr/src/speedtest

ENV PACKAGES="\
    build-essential \
    libcurl4-openssl-dev \
    libxml2-dev \
    libssl-dev \
    cmake \
    git \
    "

RUN \
    apt-get update \
    && apt-get install -y ${PACKAGES} \
    && git clone https://github.com/taganaka/SpeedTest \
    && cd SpeedTest \
    && cmake -DCMAKE_BUILD_TYPE=Release . \
    && make install

FROM python:3.7-slim-bullseye

ARG BUILD_DATE

COPY --from=speedtest-builder /usr/local/bin/SpeedTest /usr/bin/SpeedTest

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg2 \
    libcurl4 \
    libxml2 \
    tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --system speedtest

USER speedtest

WORKDIR /usr/scr/app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY speedtest.py .

COPY run.sh .

CMD ["sh", "run.sh"]
