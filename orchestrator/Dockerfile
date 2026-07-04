# BimaSarathi orchestrator — FastAPI + Browser Use + cloakbrowser stealth Chromium.
# Runs headless in a container. Memory-heavy: budget ~1GB per concurrent agent.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/root \
    BROWSER_HEADLESS=true \
    REAL_CONCURRENCY=2

# System libraries Chromium needs to run headless (Debian bookworm).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates wget fonts-liberation \
      libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxext6 \
      libxfixes3 libxrandr2 libgbm1 libxcb1 libpango-1.0-0 libcairo2 libasound2 \
      libglib2.0-0 libx11-6 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt browser-use>=0.13 cloakbrowser>=0.4

# Bake the patched stealth Chromium into the image (avoids a slow first-request download).
RUN python -m cloakbrowser install

COPY . .

# Railway provides $PORT; bind uvicorn to it.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
