FROM python:3.9-alpine

# This environment variable ensures that the python output is
# set straight to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

# Update the base image
RUN apk update

# Install dependencies
COPY ./requirements.txt /
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt
