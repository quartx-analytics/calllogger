FROM python:3.9-alpine

# This environment variable ensures that the python output is
# sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Enbed the sentry DSN
ARG SENTRY_DSN=""
ENV SENTRY_DSN $SENTRY_DSN
ENV ENVIRONMENT Deployed

# Update the base image
RUN apk update

# Install dependencies
COPY ./requirements.txt /
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt
