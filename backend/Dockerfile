FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "psycopg[binary]>=3.1"

COPY . .

EXPOSE 8000

# Migrate, seed reference data (idempotent), then serve.
# Proxy headers are trusted so absolute URLs (e.g. uploaded video links) and the
# scheme/host reflect the public domain served by the reverse proxy in front.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]