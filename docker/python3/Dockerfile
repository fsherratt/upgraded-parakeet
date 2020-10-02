FROM python:3.8.6-slim

COPY . /app
WORKDIR /app

RUN python3 -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt