# syntax = docker/dockerfile:1.2.1
FROM python:3.9-alpine

# Add Labels for OCI Image Format Specification
LABEL org.opencontainers.image.vendor="Quartx"
LABEL org.opencontainers.image.authors="William Forde"
LABEL org.opencontainers.image.url="https://quartx.ie"
LABEL org.opencontainers.image.licenses="GPL-2.0-only"
LABEL org.opencontainers.image.title="Quartx Call Logger"

# This environment variable ensures that the python output is
# sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Add secrets & Environment Variables
RUN --mount=type=secret,id=sentry_dsn
ENV ENVIRONMENT Deployed

# Install as Package
COPY . /src
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir /src && rm -rf /src
CMD ["calllogger"]
