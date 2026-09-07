#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [simulation|home_assistant]" >&2
  exit 2
fi

if [[ $# -eq 1 ]]; then
  case "$1" in
    simulation|home_assistant)
      export CONTROL_BACKEND="$1"
      ;;
    *)
      echo "Unknown backend: $1" >&2
      echo "Usage: $0 [simulation|home_assistant]" >&2
      exit 2
      ;;
  esac
fi

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
