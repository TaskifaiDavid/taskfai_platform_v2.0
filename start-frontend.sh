#!/bin/bash
# Start TaskifAI Frontend

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "❌ Node modules not found. Run ./start-local.sh first"
    exit 1
fi

echo "🎨 Starting TaskifAI Frontend on port 5173..."
npm run dev
