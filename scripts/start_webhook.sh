#!/bin/sh
set -e  # langsung berhenti kalau ada error

echo "[Webhook] 🚀 Starting Uvicorn listener..."

exec python -m uvicorn common.webhook.trakteer_listener:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --log-level info \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --access-log
