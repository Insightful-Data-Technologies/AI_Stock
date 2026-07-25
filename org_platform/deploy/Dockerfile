FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ORG_DATA_DIR=/data \
    PORT=8080 \
    GOOGLE_CLOUD_PROJECT=gen-lang-client-0386540117

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY org_platform/requirements.txt /app/org_platform/requirements.txt
RUN pip install --no-cache-dir -r /app/org_platform/requirements.txt

COPY org_platform /app/org_platform

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/api/health || exit 1

CMD ["sh", "-c", "uvicorn org_platform.api.app:app --host 0.0.0.0 --port ${PORT}"]
