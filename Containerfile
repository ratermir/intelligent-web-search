FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/app \
    APP_HOME=/app \
    XDG_CACHE_HOME=/home/app/.cache \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Systémové balíčky potřebné pro Playwright/Chromium a běh aplikace
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    dumb-init \
    git \
    wget \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libxshmfence1 \
    libglu1-mesa \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Neprivilegovaný uživatel a skupina
RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app --shell /usr/sbin/nologin app \
    && mkdir -p /app /data /tmp/app /home/app/.cache /ms-playwright \
    && chown -R app:app /app /data /tmp/app /home/app /ms-playwright

# Nejprve requirements kvůli cache vrstvě
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && python -m playwright install chromium

# Až potom zbytek projektu
COPY . /app
RUN chown -R app:app /app

USER app

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python", "-m", "app.mcp_server"]
