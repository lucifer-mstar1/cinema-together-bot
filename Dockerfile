FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD sh -c 'export WEBHOOK_BASE_URL="https://${RENDER_EXTERNAL_HOSTNAME}" && alembic upgrade head && uvicorn app.webhook_server:app --host 0.0.0.0 --port ${PORT:-10000}'
