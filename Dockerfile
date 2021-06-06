# syntax = docker/dockerfile:1.2
FROM python:3.9-alpine

# Add Labels for OCI Image Format Specification
LABEL org.opencontainers.image.vendor="Quartx"
LABEL org.opencontainers.image.authors="William Forde"
LABEL org.opencontainers.image.url="https://quartx.ie"
LABEL org.opencontainers.image.licenses="GPL-2.0-only"
LABEL org.opencontainers.image.title="Quartx Call Logger"

# Build Arguments, used to pass in Environment Variables
ARG SENTRY_DSN=""
ARG REG_KEY=""

# Docker Environment Variables
ENV PYTHONUNBUFFERED=1
ENV DOCKERIZED=1
ENV ENVIRONMENT="Deployed"
ENV DATA_LOCATION="/data"
ENV SENTRY_DSN=$SENTRY_DSN
ENV REG_KEY=$REG_KEY

# Entrypoint setup
COPY data/99-serial.rules /etc/udev/rules.d/99-serial.rules
COPY data/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["calllogger"]

# Install as Python Package
COPY . /src
RUN mkdir -p $DATA_LOCATION && \
    apk add --no-cache findmnt py3-psutil && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /src && \
    rm -rf /src && \
    adduser -D -u 1000 -G users runner && \
    mkdir -p $DATA_LOCATION && \
    chown -R runner:users $DATA_LOCATION

# Make all commands run as user runner
USER runner:users
