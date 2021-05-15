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
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT="Deployed"
ENV DATA_LOCATION="/data"
ENV SENTRY_DSN=$SENTRY_DSN
ENV REG_KEY=$REG_KEY

# Install as Python Package
COPY . /src
RUN mkdir -p $DATA_LOCATION && pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir /src && rm -rf /src
CMD ["calllogger"]
VOLUME [$DATA_LOCATION]
