# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

ARG ENERGY_TRACKER_VERSION="unknown"
ENV PYTHONUNBUFFERED=1
ENV ENERGY_TRACKER_VERSION=${ENERGY_TRACKER_VERSION}
WORKDIR /app

COPY octopus_agile_tracker /app/octopus_agile_tracker

USER nobody
ENTRYPOINT ["python", "-m", "octopus_agile_tracker.main"]
