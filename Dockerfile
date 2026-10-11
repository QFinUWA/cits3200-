# G8 research showcase: Flask site + admin, with everything the admin refresh
# needs (Chrome for the Monash/UNSW scrapers) so REFRESH_ENABLED=1 is enough
# to switch it on. See DEPLOY.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_DB_PATH=/app/var/research.db \
    CITS3200_CACHE_DIR=/app/var/cache/scrapers

# Google Chrome stable (amd64 only). base_scrapers/monash.py and unsw.py start
# it through webdriver-manager, which fetches a matching chromedriver at run time.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
 && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends google-chrome-stable \
 && apt-get purge -y gnupg && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# All writable state lives on one volume at /app/var. The code writes to
# repo-relative paths, so those paths become symlinks into it:
#   cache/   HTTP and scraper caches     logs/  refresh logs
#   backups/ database backups            final output/  pipeline outputs
# The committed final output/ is kept as the seed the entrypoint loads from;
# its hash tells the entrypoint whether a deploy brought new data.
RUN useradd --create-home --uid 1000 app \
 && mkdir -p /app/seed /app/var /app/scratch \
 && mv "/app/final output" "/app/seed/final output" \
 && (cd /app/seed && find "final output" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1 > .hash) \
 && rm -rf /app/cache /app/logs /app/backups \
 && ln -s /app/var/cache /app/cache \
 && ln -s /app/var/logs /app/logs \
 && ln -s /app/var/backups /app/backups \
 && ln -s /app/var/final-output "/app/final output" \
 && chmod +x /app/docker-entrypoint.sh \
 && chown app:app /app/var /app/scratch

USER app
EXPOSE 5000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
