# syntax = docker/dockerfile:1.2
FROM python:3.9-alpine

# Add Labels for OCI Image Format Specification
LABEL org.opencontainers.image.vendor="Quartx"
LABEL org.opencontainers.image.authors="William Forde"
LABEL org.opencontainers.image.url="https://quartx.ie"
LABEL org.opencontainers.image.licenses="GPL-2.0-only"
LABEL org.opencontainers.image.title="Quartx Call Logger"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENVIRONMENT Deployed
ENV SENTRY_DSN https://31a1124e3ac34d2eb30d764211cacfe8@o321896.ingest.sentry.io/1839719

# Install as Package
COPY . /src
RUN mkdir /data && pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir /src && rm -rf /src
CMD ["calllogger"]
VOLUME ["/data"]
