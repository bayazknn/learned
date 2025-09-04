#!/bin/bash
source backend/venv/bin/activate

# Create a new process group
set -m

cleanup() {
    echo ""
    echo "Stopping all processes..."
    
    # Kill the entire process group
    kill -TERM -$$ 2>/dev/null
    sleep 2
    kill -KILL -$$ 2>/dev/null
    
    # Backup cleanup
    pkill -9 -f "celery.*worker" 2>/dev/null
    pkill -9 -f "watchmedo" 2>/dev/null
    pkill -9 -f "uvicorn" 2>/dev/null
    pkill -9 -f "npm run dev" 2>/dev/null
    pkill -9 -f "node.*next" 2>/dev/null
    
    echo "All processes stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Celery worker with auto-restart..."
celery -A backend.tasks.background.app worker --loglevel=info --concurrency=1 &

sleep 3
echo "Starting FastAPI server..."
uvicorn backend.main:app \
  --reload-dir backend \
  --reload-exclude '*.pyc' \
  --reload-exclude '*/__pycache__/*' \
  --reload-exclude '*.txt' \
  --reload-exclude '*.md' \
  --reload-exclude '*.ipynb' \
  --reload-exclude 'test*' \
  --reload &

sleep 5
echo "Starting Next.js..."
cd yt-learn && npm run dev &

echo ""
echo "All services started. Press Ctrl+C to stop all processes."
echo ""

wait
