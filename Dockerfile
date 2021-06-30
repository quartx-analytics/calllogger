# syntax = docker/dockerfile:1.2
FROM python:3.9-slim-buster

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

# Image setup
RUN mkdir -p $DATA_LOCATION && \
    useradd --no-log-init -r -g users runner && \
    chown runner:users $DATA_LOCATION && \
    python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package data
COPY data/99-serial.rules /etc/udev/rules.d/99-serial.rules
COPY data/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["calllogger"]
COPY . /src

# Now we can install the package in the virtual env
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /src --use-feature=in-tree-build && \
    rm -rf /src

# Best to run the program as a normal user
USER runner:users
