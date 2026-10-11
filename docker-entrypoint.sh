#!/bin/sh
# Container start: make sure the database on the volume matches the data this
# image was built with, then start the web server.
#
# The rule: a deploy whose committed `final output/` differs from the one the
# volume was last loaded from rebuilds the database from it. That replaces any
# admin edits (the same as running load.py by hand), so the old database is
# backed up first. Any other restart keeps the database as it is.
set -eu

VAR=/app/var
DB="${APP_DB_PATH:-$VAR/research.db}"
SEED="/app/seed/final output"

mkdir -p "$VAR/cache" "$VAR/logs" "$VAR/backups" "$VAR/final-output"

seed_hash=$(cat /app/seed/.hash)
loaded_hash=$(cat "$VAR/.seed-hash" 2>/dev/null || true)

if [ ! -f "$DB" ] || [ "$seed_hash" != "$loaded_hash" ]; then
    if [ -f "$DB" ]; then
        backup="$VAR/backups/research-predeploy-$(date -u +%Y%m%dT%H%M%SZ).db"
        cp -p "$DB" "$backup"
        echo "entrypoint: new committed data; backed up the database to $backup"
    else
        echo "entrypoint: no database yet; building it"
    fi

    rm -rf "$VAR/final-output.new"
    cp -a "$SEED" "$VAR/final-output.new"
    rm -rf "$VAR/final-output"
    mv "$VAR/final-output.new" "$VAR/final-output"

    # Build beside the live file, then swap, so a failed load never leaves the
    # site on a half-built database.
    staging="$DB.deploy-staging"
    rm -f "$staging"
    RESEARCH_DB_PATH="$staging" python load.py
    mv -f "$staging" "$DB"
    echo "$seed_hash" > "$VAR/.seed-hash"
    echo "entrypoint: database rebuilt from the committed final output/"
else
    echo "entrypoint: committed data unchanged; keeping the existing database"
fi

# One worker: the admin refresh's progress lives in this process's memory, so
# a second worker would report a different state. Threads serve concurrency.
exec gunicorn --workers 1 --threads 8 --timeout 120 \
    --bind 0.0.0.0:5000 --access-logfile - app:app
