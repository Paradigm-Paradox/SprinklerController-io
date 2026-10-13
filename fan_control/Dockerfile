ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    curl \
    jq \
    build-base \
    libffi-dev \
    openssl-dev

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY rootfs/ /
RUN chmod a+x /app/run.sh 2>/dev/null || true

EXPOSE 8095

CMD [ "/app/run.sh" ]
