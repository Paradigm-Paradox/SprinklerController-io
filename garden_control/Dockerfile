ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

# Install runtime and build dependencies
RUN apk add --no-cache \
    curl \
    jq \
    sqlite \
    build-base \
    libffi-dev \
    openssl-dev

WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY run.sh /app/run.sh
COPY app /app/app

RUN chmod a+x /app/run.sh

EXPOSE 8099

CMD [ "/app/run.sh" ]
