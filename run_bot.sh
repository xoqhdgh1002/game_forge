#!/usr/bin/env bash
# Game Forge Bot 실행 스크립트
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="/home/taebh/vera/.venv/bin/python3.14"

PYTHONPATH="" exec "$VENV_PYTHON" "$SCRIPT_DIR/bot.py" "$@"
