# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY octopus_agile_tracker /app/octopus_agile_tracker

USER nobody
ENTRYPOINT ["python", "-m", "octopus_agile_tracker.main"]

