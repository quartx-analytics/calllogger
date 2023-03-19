# We use full Debian to be able to compile uptime & psutil
FROM python:3.10-bullseye as builder

# Install the package dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements-docker.txt /requirements-docker.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip --disable-pip-version-check install --no-compile -r /requirements-docker.txt

# Install the package itself
COPY pyproject.toml LICENSE README.md /project/
COPY src /project/src/
RUN pip --disable-pip-version-check install --no-cache-dir --no-compile --no-clean --no-deps /project


# Switch to slim Debian for the runtime
FROM python:3.10-slim-bullseye as base

# Add Labels for OCI Image Format Specification
LABEL org.opencontainers.image.vendor="Quartx"
LABEL org.opencontainers.image.authors="William Forde <william@quartx.ie>"

# Build Arguments, used to pass in Environment Variables
ARG SENTRY_DSN=""
ARG REG_KEY=""

# Docker Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOCKERIZED=1
ENV ENVIRONMENT="Dockerized"
ENV DATA_LOCATION="/data"
ENV SENTRY_DSN=$SENTRY_DSN
ENV REG_KEY=$REG_KEY

# Image setup
RUN mkdir -p $DATA_LOCATION && \
    useradd -rm -d /home/runner -s /bin/bash -g users -G dialout -u 999 runner && \
    chown runner:users $DATA_LOCATION
WORKDIR /home/runner

# Copy required scripts
COPY data/99-serial.rules /etc/udev/rules.d/99-serial.rules
COPY data/entrypoint.sh /entrypoint.sh

# Finalize build image
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["calllogger"]
USER runner:users
