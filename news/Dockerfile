# syntax=docker/dockerfile:1
FROM python:3.8-slim AS worker

MAINTAINER Nikolay Beloglazov "nickolai.beloglazov@gmail.com"

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .