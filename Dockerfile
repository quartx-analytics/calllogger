# syntax=docker/dockerfile:1.0.0-experimental
FROM python:3.9-alpine

# Add Labels for OCI Image Format Specification
LABEL maintainer="willforde@quartx.ie"
LABEL org.opencontainers.image.vendor="Quartx"
LABEL org.opencontainers.image.authors="William Forde"
LABEL org.opencontainers.image.url="https://quartx.ie"
LABEL org.opencontainers.image.licenses="GPL-2.0-only"
LABEL org.opencontainers.image.title="Quartx Call Logger"

# This environment variable ensures that the python output is
# sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Update the base image
RUN apk update

# Add secrets & Environment Variables
RUN --mount=type=secret,id=sentry_dsn cat /run/secrets/sentry_dsn
ENV ENVIRONMENT Deployed

# Install dependencies
COPY ./requirements.txt /
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt
