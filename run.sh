
---

## `run.sh`
```bash
#!/usr/bin/env bash
# run.sh — convenience startup script for Unix-like systems
# - Creates a venv if missing
# - Installs backend requirements
# - Starts backend (uvicorn on port 8000)
# - Serves frontend folder on port 3000 with python's simple http server
#
# Usage: chmod +x run.sh && ./run.sh
# NOTE: This script backgrounds the servers for convenience and prints PIDs.
# Press Ctrl+C to stop; the script attempts to kill started processes on exit.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

echo "Project root: $PROJECT_ROOT"
echo "Backend dir: $BACKEND_DIR"
echo "Frontend dir: $FRONTEND_DIR"

# 1) create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating python virtual environment at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# 2) activate and install requirements
echo "Activating venv and installing backend requirements..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "$BACKEND_DIR/requirements.txt"

# 3) load .env if present (export vars)
if [ -f "$PROJECT_ROOT/.env" ]; then
  echo "Loading environment variables from .env"
  # export every VAR=VALUE line (ignore comments)
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.env"
  set +a
fi

# 4) Start backend with uvicorn
echo "Starting backend (uvicorn) on ${BACKEND_HOST}:${BACKEND_PORT} ..."
# run in background
uvicorn backend.app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload &
UVICORN_PID=$!
echo "uvicorn PID: $UVICORN_PID"

# 5) serve frontend
echo "Serving frontend at http://localhost:${FRONTEND_PORT} ..."
# change to frontend dir and start http.server
(
  cd "$FRONTEND_DIR"
  python3 -m http.server "$FRONTEND_PORT" &
  HTTP_PID=$!
  echo "http.server PID: $HTTP_PID"
  # wait in subshell so we can trap signals in parent
  wait $HTTP_PID
) &

# record background PIDs (uvicorn already started above)
FRONTEND_PID=$!

# trap to kill children on exit
cleanup() {
  echo "Stopping servers..."
  if ps -p $UVICORN_PID > /dev/null 2>&1; then
    kill $UVICORN_PID || true
  fi
  # attempt kill any python http.server processes started (best-effort)
  pkill -f "python3 -m http.server $FRONTEND_PORT" || true
  exit 0
}
trap cleanup INT TERM

echo ""
echo "----------"
echo "Backend: http://localhost:${BACKEND_PORT}"
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo ""
echo "To stop: press Ctrl+C"
echo "----------"

# wait forever so script stays alive and trap works
wait
