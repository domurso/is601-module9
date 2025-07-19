FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
   PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
   apt-get upgrade -y && \
   apt-get install -y --no-install-recommends gcc python3-dev libssl-dev && \
   rm -rf /var/lib/apt/lists/* && \
   python -m pip install --upgrade pip setuptools>=70.0.0 wheel && \
   groupadd -r appgroup && \
   useradd -r -g appgroup appuser && \
   mkdir -p /app/coverage/html /app/.pytest_cache && \
   chown -R appuser:appgroup /app/coverage /app/.pytest_cache && \
   chmod -R u+rw /app/coverage /app/.pytest_cache

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
   playwright install --with-deps

COPY . .

USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
   CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
