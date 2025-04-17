FROM python:3.9-slim

WORKDIR /app

# Copy requirements from script dir (used as build context)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# This image expects to be run with a command (CMD not needed)

