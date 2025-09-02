# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# copy code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
CMD ["uvicorn", "src.serve.main:app", "--host", "0.0.0.0", "--port", "8000"]