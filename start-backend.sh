#!/bin/bash
# Start TaskifAI Backend API

cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./start-local.sh first"
    exit 1
fi

echo "🚀 Starting TaskifAI Backend API on port 8000..."
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
