ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install runtime utilities
RUN apk add --no-cache \
    curl \
    jq

# Install Python requirements
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app /app/app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099

CMD [ "/run.sh" ]
