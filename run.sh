#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================="
echo "           🚀 Starting Minute AI Dashboard"
echo "  AI-Powered Meeting Transcripts to Jira Action Items"
echo "=========================================================="

# Activate virtualenv if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Ensure frontend build is up to date
if [ ! -d "frontend/dist" ]; then
    echo "📦 Building modern frontend bundle..."
    cd frontend && npm install && npm run build && cd ..
fi

echo "✨ Server starting on http://localhost:8000"
echo "   - Modern Minimalist Light UI: http://localhost:8000"
echo "   - REST API & Health: http://localhost:8000/health"
echo "   - Interactive API Docs: http://localhost:8000/docs"
echo "=========================================================="

exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
