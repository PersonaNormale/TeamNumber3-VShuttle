#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

cleanup() {
  echo "\nStopping services..."
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

command -v python3 >/dev/null 2>&1 || {
  echo "python3 not found" >&2
  exit 1
}
command -v npm >/dev/null 2>&1 || {
  echo "npm not found" >&2
  exit 1
}

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  echo "Creating backend virtualenv..."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

# shellcheck source=/dev/null
source "$BACKEND_DIR/.venv/bin/activate"
pip install -q -r "$BACKEND_DIR/requirements.txt"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "Starting backend on http://127.0.0.1:${BACKEND_PORT}"
(
  cd "$BACKEND_DIR"
  uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

sleep 2
if ! curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null; then
  echo "Backend health check failed" >&2
  exit 1
fi

echo "Starting frontend on http://127.0.0.1:${FRONTEND_PORT}"
(
  cd "$FRONTEND_DIR"
  npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo "\n✅ Full stack running"
echo "- Frontend: http://127.0.0.1:${FRONTEND_PORT}"
echo "- Backend:  http://127.0.0.1:${BACKEND_PORT}"
echo "Press Ctrl+C to stop both services."

wait "$FRONTEND_PID"
