ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

# Install base system packages & build tools
RUN apk add --no-cache \
    curl \
    jq \
    build-base \
    libffi-dev \
    openssl-dev

# Install Python requirements
WORKDIR /app
COPY rootfs/app/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY rootfs/ /

# Ensure execution permissions for run scripts
RUN chmod a+x /etc/services.d/*/run 2>/dev/null || true
RUN chmod a+x /app/run.sh

EXPOSE 8000

CMD [ "/app/run.sh" ]
