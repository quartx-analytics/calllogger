FROM python:3.9-alpine

# This environment variable ensures that the python output is
# sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Enbed the sentry DSN
ENV SENTRY_DSN https://31a1124e3ac34d2eb30d764211cacfe8@o321896.ingest.sentry.io/1839719
ENV ENVIRONMENT Deployed

# Update the base image
RUN apk update

# Install dependencies
COPY ./requirements.txt /
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt
