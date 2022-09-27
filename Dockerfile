# syntax=docker/dockerfile:1

FROM python:3.10.7-slim

WORKDIR /app

COPY source .

RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

CMD ["python3.10","minecraft-discord-bots.py"]
  