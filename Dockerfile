FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends gcc python3-dev libssl-dev curl vim && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip install --upgrade pip setuptools>=70.0.0 wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip show sqlalchemy || (echo "sqlalchemy installation failed" && exit 1)

# Install Playwright browsers
RUN pip install playwright && \
    playwright install --with-deps

COPY . .
RUN groupadd -r appgroup && \
    useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
