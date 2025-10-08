#!/bin/bash
# Start TaskifAI Celery Worker

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./start-local.sh first"
    exit 1
fi

echo "🔄 Starting TaskifAI Celery Worker..."
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
