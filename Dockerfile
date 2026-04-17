FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
        libpango-1.0-0 libcairo2 libasound2 libxshmfence1 && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir . && \
    playwright install chromium --with-deps

COPY src/ src/

RUN mkdir -p /app/data

ENV SA_DATA_DIR=/app/data \
    SA_DB_URL=sqlite:////app/data/shopping.db \
    SA_OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    SA_SCRAPER_HEADLESS=true \
    SA_MAX_DAILY_SEARCHES=10

EXPOSE 8000

VOLUME ["/app/data"]

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
