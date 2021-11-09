# Multistage build setup
FROM debian:buster-slim as speedtest-builder

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

FROM telegraf:latest

USER root

COPY --from=speedtest-builder /usr/local/bin/SpeedTest /usr/bin/SpeedTest

RUN apt-get update && apt-get install -y --no-install-recommends mtr-tiny dnsutils libcurl4 libxml2 && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*; \
    usermod -G video telegraf; \
    chown telegraf:telegraf /etc/telegraf -R; \
    setcap cap_net_raw+ep /usr/bin/telegraf; \
    setcap cap_net_raw+ep /usr/bin/mtr; \
    setcap cap_net_raw+ep /usr/bin/SpeedTest

EXPOSE 8125/udp 8092/udp 8094

USER telegraf

ENTRYPOINT ["/entrypoint.sh"]
CMD ["telegraf"]
