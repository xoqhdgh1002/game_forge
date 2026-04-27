#!/usr/bin/env bash
# Game Forge 실행 스크립트
# vera venv를 사용하여 PYTHONPATH 충돌 없이 실행
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="/home/taebh/vera/.venv/bin/python3.14"

PYTHONPATH="" exec "$VENV_PYTHON" "$SCRIPT_DIR/forge.py" "$@"
